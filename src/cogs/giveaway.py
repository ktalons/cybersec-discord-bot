from __future__ import annotations
import asyncio
import random
import logging
from typing import List, Set, Optional
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

logger = logging.getLogger("bot.giveaway")


class GiveawayView(discord.ui.View):
    def __init__(self, prize: str, end_time: datetime, giveaway_cog, custom_id: str):
        super().__init__(timeout=None)  # Persistent view
        self.entries: Set[int] = set()
        self.prize = prize
        self.end_time = end_time
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
        
        # Calculate time remaining
        now = datetime.utcnow()
        if now < self.end_time:
            remaining = self.end_time - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                time_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"
            
            embed.add_field(
                name="⏰ Time Remaining",
                value=time_str,
                inline=True,
            )
        else:
            embed.add_field(
                name="⏰ Status",
                value="Ended",
                inline=True,
            )
        
        embed.set_footer(text=f"Ends at {self.end_time.strftime('%I:%M:%S %p UTC')}")
        
        return embed
      
    # Update the giveaway message with current data.
    async def update_embed(self):
        if not self.message:
            return
        
        embed = self._build_embed()
        try:
            await self.message.edit(embed=embed)
        except discord.HTTPException as e:
            logger.error(f"Failed to update giveaway embed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error updating giveaway: {e}")


class GiveawayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_giveaways: dict[str, GiveawayView] = {}
        self.giveaway_update_task.start()

    def cog_unload(self):
        self.giveaway_update_task.cancel()
    
    @tasks.loop(seconds=5)
    async def giveaway_update_task(self):
        """Background task to update all active giveaways every 5 seconds."""
        now = datetime.utcnow()
        ended_giveaways = []
        
        for custom_id, view in list(self.active_giveaways.items()):
            if now >= view.end_time and not view.is_ended:
                # Giveaway has ended
                view.is_ended = True
                ended_giveaways.append((custom_id, view))
            elif not view.is_ended:
                # Update countdown
                await view.update_embed()
        
        # Process ended giveaways
        for custom_id, view in ended_giveaways:
            await self._end_giveaway(view)
            del self.active_giveaways[custom_id]
    
    @giveaway_update_task.before_loop
    async def before_giveaway_update(self):
        await self.bot.wait_until_ready()
    
    async def _end_giveaway(self, view: GiveawayView):
        """End a giveaway and announce the winner."""
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
        if duration_minutes <= 0:
            await interaction.response.send_message("Duration must be positive.", ephemeral=True)
            return

        # Calculate end time
        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        # Create unique ID for this giveaway
        custom_id = f"giveaway_{interaction.id}"
        
        view = GiveawayView(prize, end_time, self, custom_id)
        embed = view._build_embed()
        
        await interaction.response.send_message(
            embed=embed,
            view=view,
        )
        
        # Store message reference and register view
        view.message = await interaction.original_response()
        self.active_giveaways[custom_id] = view
        
        logger.info(f"Started giveaway '{prize}' for {duration_minutes} minutes")

async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCog(bot))