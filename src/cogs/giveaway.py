from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set

import discord
from discord import app_commands
from discord.ext import commands, tasks

from ..utils.database import Database

logger = logging.getLogger("bot.giveaway")


class GiveawayView(discord.ui.View):
    def __init__(self, prize: str, end_time: datetime, giveaway_cog, custom_id: str):
        super().__init__(timeout=None)  # Persistent view
        self.entries: Set[int] = set()
        self.prize = prize
        # Normalize end_time to UTC-aware to keep timestamp rendering correct across hosts
        if end_time.tzinfo is None:
            self.end_time = end_time.replace(tzinfo=timezone.utc)
        else:
            self.end_time = end_time.astimezone(timezone.utc)
        self.message: Optional[discord.Message] = None
        self.giveaway_cog = giveaway_cog
        self.custom_id = custom_id
        self.is_ended = False

    @discord.ui.button(label="Enter Giveaway", style=discord.ButtonStyle.success, emoji="🎉", custom_id="giveaway_enter")
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.is_ended:
            await interaction.response.send_message("This giveaway has ended!", ephemeral=True)
            return
            
        if interaction.user.id in self.entries:
            await interaction.response.send_message("You're already entered!", ephemeral=True)
            return
        
        self.entries.add(interaction.user.id)
        await interaction.response.send_message("You're entered!", ephemeral=True)
        
        # Save to database
        await self.giveaway_cog.save_giveaway_to_db(self)
        
        # Update the embed with new entry count
        await self.update_embed()
            
    # Build the giveaway embed with current data.
    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎉 Giveaway!",
            description=f"**Prize:** {self.prize}\n\nClick the button below to enter!",
            color=discord.Color.gold(),
        )

        # Add entry count
        embed.add_field(
            name="👥 Entries",
            value=str(len(self.entries)),
            inline=True,
        )

        # Use Discord timestamps so the client renders a live countdown (no periodic edits needed)
        end_ts = int(self.end_time.timestamp())
        embed.add_field(
            name="⏰ Ends",
            value=f"<t:{end_ts}:F> • <t:{end_ts}:R>",
            inline=False,
        )

        embed.add_field(
            name="📌 Status",
            value="Ended" if self.is_ended else "Open",
            inline=True,
        )

        embed.set_footer(text=f"Giveaway ID: {self.custom_id}")
        return embed
      
    # Update the giveaway message with current data.
    async def update_embed(self):
        if not self.message:
            return
        
        embed = self._build_embed()
        try:
            # Re-fetch message to get fresh reference that can be edited
            try:
                fresh_message = await self.message.channel.fetch_message(self.message.id)
                self.message = fresh_message
            except discord.NotFound:
                logger.warning(f"Giveaway message {self.custom_id} was deleted")
                self.message = None
                return
            except discord.Forbidden:
                logger.error(f"No permission to fetch message for giveaway {self.custom_id}")
                return
            
            # Edit the freshly fetched message
            await self.message.edit(embed=embed)
            
        except discord.Forbidden as e:
            logger.error(f"No permission to edit giveaway message {self.custom_id}: {e}")
        except discord.HTTPException as e:
            logger.error(f"Failed to update giveaway embed {self.custom_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error updating giveaway {self.custom_id}: {e}")


class GiveawayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        from pathlib import Path
        self.bot = bot
        self.db = Database()
        self.active_giveaways: dict[str, GiveawayView] = {}
        self.giveaway_update_task.start()
        self.database_cleanup_task.start()
        self.bot.loop.create_task(self._restore_giveaways())
        logger.info("GiveawayCog initialized")

    def cog_unload(self):
        logger.info("Unloading GiveawayCog...")
        self.giveaway_update_task.cancel()
        self.database_cleanup_task.cancel()
    
    async def cog_app_command_error(self, interaction: discord.Interaction, error: Exception):
        # Handle errors in app commands
        logger.error(f"Error in giveaway command: {error}", exc_info=True)
        
        error_message = f"❌ An error occurred: {str(error)}"
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)
        except:
            logger.error("Failed to send error message to user")
    
    async def _restore_giveaways(self):
        # Restore giveaways from database on startup
        await self.bot.wait_until_ready()
        await self.db.initialize()
        
        giveaways_data = await self.db.load_giveaways()
        logger.info(f"Restoring {len(giveaways_data)} giveaways from database")
        
        for data in giveaways_data:
            try:
                # Fetch the message
                channel = self.bot.get_channel(data["channel_id"])
                if not channel:
                    logger.warning(f"Channel {data['channel_id']} not found for giveaway {data['custom_id']}")
                    continue
                
                try:
                    message = await channel.fetch_message(data["message_id"])
                except discord.NotFound:
                    logger.warning(f"Message {data['message_id']} not found, deleting giveaway {data['custom_id']}")
                    await self.db.delete_giveaway(data["custom_id"])
                    continue
                
                # Recreate the view
                view = GiveawayView(
                    prize=data["prize"],
                    end_time=data["end_time"],
                    giveaway_cog=self,
                    custom_id=data["custom_id"]
                )
                view.entries = data["entries"]
                view.message = message
                view.is_ended = data["is_ended"]
                
                # Re-attach the view to the message
                self.bot.add_view(view, message_id=message.id)
                self.active_giveaways[data["custom_id"]] = view
                
                logger.info(f"Restored giveaway {data['custom_id']} with {len(view.entries)} entries")
            except Exception as e:
                logger.error(f"Failed to restore giveaway {data.get('custom_id', 'unknown')}: {e}")
    
    async def save_giveaway_to_db(self, view: GiveawayView):
        # Save a giveaway to the database
        if not view.message:
            return
        
        await self.db.save_giveaway(
            custom_id=view.custom_id,
            prize=view.prize,
            end_time=view.end_time,
            channel_id=view.message.channel.id,
            message_id=view.message.id,
            entries=view.entries,
            is_ended=view.is_ended
        )
    
    @tasks.loop(seconds=5)
    async def giveaway_update_task(self):
        # Background task to end giveaways once their end_time has passed.
        # We intentionally do NOT edit giveaway messages on a timer; Discord clients can render
        # countdowns using <t:...:R> without any API traffic.
        now = datetime.now(timezone.utc)
        ended_giveaways = []

        for custom_id, view in list(self.active_giveaways.items()):
            try:
                # Skip if no valid message reference
                if not view.message:
                    logger.warning(f"Skipping giveaway {custom_id}: no message reference")
                    continue

                if now >= view.end_time and not view.is_ended:
                    # Giveaway has ended
                    view.is_ended = True
                    ended_giveaways.append((custom_id, view))
            except OSError as e:
                # Network errors (DNS, connection issues)
                logger.warning(f"Network error checking giveaway {custom_id}: {e}. Will retry next cycle.")
            except Exception as e:
                logger.error(f"Error checking giveaway {custom_id}: {e}")
        
        # Process ended giveaways
        for custom_id, view in ended_giveaways:
            try:
                await self._end_giveaway(view)
                del self.active_giveaways[custom_id]
                await self.db.delete_giveaway(custom_id)
            except Exception as e:
                logger.error(f"Error ending giveaway {custom_id}: {e}")
    
    @giveaway_update_task.before_loop
    async def before_giveaway_update(self):
        await self.bot.wait_until_ready()
    
    @giveaway_update_task.error
    async def giveaway_update_task_error(self, error: Exception):
        # Handle task-level errors to prevent task from stopping
        logger.error(f"Giveaway update task encountered an error: {error}", exc_info=True)
        # Task will automatically restart
    
    @tasks.loop(hours=24)
    async def database_cleanup_task(self):
        # Clean up old giveaway entries from database (60+ days old)
        try:
            deleted = await self.db.cleanup_old_entries(days=60)
            if deleted > 0:
                logger.info(f"Database cleanup: removed {deleted} old entries")
        except Exception as e:
            logger.error(f"Database cleanup task failed: {e}")
    
    @database_cleanup_task.before_loop
    async def before_database_cleanup(self):
        await self.bot.wait_until_ready()
    
    async def _end_giveaway(self, view: GiveawayView):
        # End a giveaway and announce the winner
        try:
            # Final update to show "Ended" status
            await view.update_embed()
            
            if not view.message:
                logger.error("Cannot end giveaway: no message reference")
                return
            
            # Determine winner
            if not view.entries:
                await view.message.reply("🎉 Giveaway ended! No entries, so no winner.")
                return
            
            winner_id = random.choice(list(view.entries))
            guild = view.message.guild
            winner = guild.get_member(winner_id) if guild else None
            
            if winner:
                await view.message.reply(
                    f"🎉 **Giveaway ended!**\n\nCongratulations {winner.mention}! You won: **{view.prize}**"
                )
            else:
                await view.message.reply("🎉 Giveaway ended! Winner left the server or cannot be found.")
        except Exception as e:
            logger.error(f"Error ending giveaway: {e}")
    
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.command(name="giveaway_start", description="Start a giveaway (admin only)")
    @app_commands.describe(duration_minutes="Duration in minutes", prize="Description of the prize")
    async def giveaway_start(self, interaction: discord.Interaction, duration_minutes: int, prize: str):
        try:
            if duration_minutes <= 0:
                await interaction.response.send_message("❌ Duration must be positive.", ephemeral=True)
                return

            # Calculate end time (store as UTC-aware for correct timestamp rendering)
            end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
            
            # Create unique ID for this giveaway
            custom_id = f"giveaway_{interaction.id}"
            
            logger.info(f"Creating giveaway: {prize} (duration: {duration_minutes}m, ID: {custom_id})")
            
            view = GiveawayView(prize, end_time, self, custom_id)
            embed = view._build_embed()
            
            await interaction.response.send_message(
                embed=embed,
                view=view,
            )
            
            # Store message reference and register view
            view.message = await interaction.original_response()
            self.active_giveaways[custom_id] = view
            
            # Save to database
            await self.save_giveaway_to_db(view)
            
            logger.info(f"✅ Giveaway '{prize}' started successfully (ID: {custom_id})")
        except Exception as e:
            logger.error(f"Failed to start giveaway: {e}", exc_info=True)
            raise

async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCog(bot))