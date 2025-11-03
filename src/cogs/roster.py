from __future__ import annotations
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

from ..utils.database import Database

logger = logging.getLogger("bot.roster")


class SkillLevel:
    ROOKIE = "🐣 Rookie"
    INTERMEDIATE = "🌵 Intermediate"
    VETERAN = "🥷 Veteran"

# Modal to collect roster configuration from admin
class RosterConfigModal(discord.ui.Modal, title="Configure CTF Roster"):
    
    roster_title = discord.ui.TextInput(
        label="Roster Title",
        placeholder="e.g., picoCTF 2024 Team Roster",
        required=True,
        max_length=100,
    )
    
    roster_datetime = discord.ui.TextInput(
        label="Date & Time",
        placeholder="e.g., April 15, 2024 at 6:00 PM MST",
        required=True,
        max_length=100,
    )
    
    roster_description = discord.ui.TextInput(
        label="Description",
        placeholder="Describe the CTF event...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500,
    )
    
    roster_limit = discord.ui.TextInput(
        label="Roster Limit (optional)",
        placeholder="Leave blank for unlimited",
        required=False,
        max_length=3,
    )
    
    thumbnail_url = discord.ui.TextInput(
        label="Thumbnail URL (optional)",
        placeholder="https://example.com/image.png",
        required=False,
        max_length=200,
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        # Parse limit
        limit = None
        if self.roster_limit.value.strip():
            try:
                limit = int(self.roster_limit.value.strip())
                if limit <= 0:
                    await interaction.response.send_message("Roster limit must be positive!", ephemeral=True)
                    return
            except ValueError:
                await interaction.response.send_message("Invalid roster limit! Must be a number.", ephemeral=True)
                return
        
        # Store config in the view
        self.view.title = self.roster_title.value
        self.view.date_time = self.roster_datetime.value
        self.view.description = self.roster_description.value
        self.view.limit = limit
        self.view.thumbnail = self.thumbnail_url.value.strip() or None
        
        # Create the roster embed and post it
        await self.view.post_roster(interaction)


class SkillSelectView(discord.ui.View):
    
    def __init__(self, roster_view: RosterMainView, user: discord.Member):
        super().__init__(timeout=180)  # 3 minute timeout
        self.roster_view = roster_view
        self.user = user
        self.selected_skill: Optional[str] = None
    
    @discord.ui.button(label="Rookie", style=discord.ButtonStyle.success, emoji="🐣")
    async def rookie_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not your registration!", ephemeral=True)
            return
        await self.finalize_registration(interaction, SkillLevel.ROOKIE)
    
    @discord.ui.button(label="Intermediate", style=discord.ButtonStyle.primary, emoji="🌵")
    async def intermediate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not your registration!", ephemeral=True)
            return
        await self.finalize_registration(interaction, SkillLevel.INTERMEDIATE)
    
    @discord.ui.button(label="Veteran", style=discord.ButtonStyle.danger, emoji="🥷")
    async def veteran_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not your registration!", ephemeral=True)
            return
        await self.finalize_registration(interaction, SkillLevel.VETERAN)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not your registration!", ephemeral=True)
            return
        await interaction.response.edit_message(
            content="❌ Registration cancelled.",
            view=None,
            embed=None,
        )
        self.stop()

    # register user with skill level
    async def finalize_registration(self, interaction: discord.Interaction, skill_level: str):
        success = await self.roster_view.add_participant(self.user, skill_level)
        
        if success:
            await interaction.response.edit_message(
                content=f"✅ You've been registered as **{skill_level}**!",
                view=None,
                embed=None,
            )
            # Update the roster display
            await self.roster_view.update_roster_display()
        else:
            await interaction.response.edit_message(
                content="❌ Registration failed. The roster may be full.",
                view=None,
                embed=None,
            )
        
        self.stop()


class RosterMainView(discord.ui.View):
    
    def __init__(self, cog: RosterCog, custom_id: str):
        super().__init__(timeout=None)  # Persistent view
        self.cog = cog
        self.custom_id = custom_id
        
        # Roster configuration
        self.title: str = ""
        self.date_time: str = ""
        self.description: str = ""
        self.limit: Optional[int] = None
        self.thumbnail: Optional[str] = None
        
        # Participants: user_id -> (username, skill_level)
        self.participants: Dict[int, tuple[str, str]] = {}
        
        # Message reference for updating
        self.roster_message: Optional[discord.Message] = None
        self.channel_id: Optional[int] = None
        self.message_id: Optional[int] = None
        
        # Rate limit tracking
        self._last_update: float = 0
        self._update_cooldown: float = 3.0  # 3 seconds between updates
    
    @discord.ui.button(label="I'm Interested!", style=discord.ButtonStyle.primary, emoji="✋", custom_id="roster_interested")
    async def interested_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        # Check if roster is full
        if self.limit and len(self.participants) >= self.limit:
            await interaction.response.send_message(
                "❌ Sorry, the roster is full!",
                ephemeral=True,
            )
            return
        
        # Check if already registered
        if interaction.user.id in self.participants:
            await interaction.response.send_message(
                "You're already registered! Use the **Remove Me** button to unregister.",
                ephemeral=True,
            )
            return
        
        # Show skill selection
        skill_view = SkillSelectView(self, interaction.user)
        
        embed = discord.Embed(
            title="Select Your CTF Skill Level",
            description=(
                "Please select the option that best describes your experience:\n\n"
                "🐣 **Rookie**: New to CTFs or limited experience\n"
                "🌵 **Intermediate**: Some CTF experience, familiar with basics\n"
                "🥷 **Veteran**: Extensive CTF experience, advanced skills"
            ),
            color=discord.Color.blue(),
        )
        
        await interaction.response.send_message(
            embed=embed,
            view=skill_view,
            ephemeral=True,
        )
    
    # Handle when a user wants to remove themselves from the roster.
    @discord.ui.button(label="Remove Me", style=discord.ButtonStyle.danger, emoji="❎", custom_id="roster_remove")
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        if interaction.user.id not in self.participants:
            await interaction.response.send_message(
                "You're not registered on this roster.",
                ephemeral=True,
            )
            return
        
        # Remove the user
        del self.participants[interaction.user.id]
        await interaction.response.send_message(
            "✅ You've been removed from the roster.",
            ephemeral=True,
        )
        
        # Save to database
        await self.cog.save_roster_to_db(self)
        
        # Update the roster display
        await self.update_roster_display()

    # adds member, returns true
    async def add_participant(self, user: discord.Member, skill_level: str) -> bool:
        
        # Double-check limit
        if self.limit and len(self.participants) >= self.limit:
            return False
        
        self.participants[user.id] = (user.display_name, skill_level)
        
        # Save to database
        await self.cog.save_roster_to_db(self)
        
        return True

    # initial roster post
    async def post_roster(self, interaction: discord.Interaction):
        try:
            embed = self._build_embed()
            
            await interaction.response.send_message(
                content="📋 **CTF Roster Created!**",
                embed=embed,
                view=self,
            )
            
            # Store message reference
            self.roster_message = await interaction.original_response()
            self.channel_id = interaction.channel_id
            self.message_id = self.roster_message.id
            
            # Register this view with the cog
            self.cog.active_rosters[self.custom_id] = self
            
            # Save to database
            await self.cog.save_roster_to_db(self)
            
            logger.info(f"✅ Roster '{self.title}' created successfully (ID: {self.custom_id})")
        except Exception as e:
            logger.error(f"Failed to post roster: {e}", exc_info=True)
            raise

    # Updates the roster embed with current participants
    async def update_roster_display(self, force: bool = False):
        import time
        import asyncio
        
        # Rate limit check
        now = time.time()
        if not force and (now - self._last_update) < self._update_cooldown:
            logger.debug(f"Skipping roster update for {self.custom_id} - rate limited")
            return
        
        if not self.roster_message:
            # Try to recover message reference if we have IDs
            if self.channel_id and self.message_id:
                try:
                    channel = self.cog.bot.get_channel(self.channel_id)
                    if channel:
                        self.roster_message = await channel.fetch_message(self.message_id)
                        logger.info(f"Recovered roster message reference for {self.custom_id}")
                except Exception as e:
                    logger.error(f"Failed to recover roster message: {e}")
                    return
            else:
                logger.warning(f"Cannot update roster {self.custom_id}: no message reference")
                return
        
        embed = self._build_embed()
        
        try:
            # Edit the message directly
            await self.roster_message.edit(embed=embed)
            self._last_update = now
        except discord.NotFound:
            logger.warning(f"Roster message {self.custom_id} was deleted")
            self.roster_message = None
        except discord.Forbidden as e:
            logger.error(f"No permission to edit roster message {self.custom_id}: {e}")
        except discord.HTTPException as e:
            # Handle rate limits with exponential backoff
            if e.status == 429:
                retry_after = e.response.headers.get('Retry-After', 5)
                logger.warning(f"Rate limited on roster {self.custom_id}. Retry after {retry_after}s")
                # Don't retry here - let the next interaction handle it
                return
            elif e.status == 401 or "Webhook" in str(e):
                logger.error(f"Invalid message reference for roster {self.custom_id}, will try to recover")
                self.roster_message = None
            else:
                logger.error(f"Failed to update roster embed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error updating roster {self.custom_id}: {e}")

    # builds roster with admin entered data
    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description=self.description,
            color=discord.Color.purple(),
            timestamp=datetime.utcnow(),
        )
        
        # Add date/time field
        embed.add_field(
            name="📅 Date & Time",
            value=self.date_time,
            inline=False,
        )
        
        # Add participant count
        count_text = f"{len(self.participants)}"
        if self.limit:
            count_text += f" / {self.limit}"
        embed.add_field(
            name="👥 Participants",
            value=count_text,
            inline=False,
        )
        
        # Group participants by skill level
        rookies = []
        intermediates = []
        veterans = []
        
        for user_id, (username, skill_level) in self.participants.items():
            if skill_level == SkillLevel.ROOKIE:
                rookies.append(username)
            elif skill_level == SkillLevel.INTERMEDIATE:
                intermediates.append(username)
            elif skill_level == SkillLevel.VETERAN:
                veterans.append(username)
        
        # Add participant lists by skill level
        if veterans:
            embed.add_field(
                name=f"{SkillLevel.VETERAN} ({len(veterans)})",
                value="\n".join(f"• {name}" for name in veterans),
                inline=True,
            )
        
        if intermediates:
            embed.add_field(
                name=f"{SkillLevel.INTERMEDIATE} ({len(intermediates)})",
                value="\n".join(f"• {name}" for name in intermediates),
                inline=True,
            )
        
        if rookies:
            embed.add_field(
                name=f"{SkillLevel.ROOKIE} ({len(rookies)})",
                value="\n".join(f"• {name}" for name in rookies),
                inline=True,
            )
        
        if not self.participants:
            embed.add_field(
                name="Status",
                value="*No participants yet. Be the first to join!*",
                inline=False,
            )
        
        # Add thumbnail if provided
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        
        embed.set_footer(text="Click 'I'm Interested!' to join")
        
        return embed

# CTF roster cog
class RosterCog(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        from pathlib import Path
        self.bot = bot
        self.db = Database()
        self.active_rosters: Dict[str, RosterMainView] = {}
        self.roster_refresh_task.start()
        self.bot.loop.create_task(self._restore_rosters())
        logger.info("RosterCog initialized")
    
    def cog_unload(self):
        logger.info("Unloading RosterCog...")
        self.roster_refresh_task.cancel()
    
    async def cog_app_command_error(self, interaction: discord.Interaction, error: Exception):
        # Handle errors in app commands
        logger.error(f"Error in roster command: {error}", exc_info=True)
        
        error_message = f"❌ An error occurred: {str(error)}"
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)
        except:
            logger.error("Failed to send error message to user")
    
    async def _restore_rosters(self):
        # Restore rosters from database on startup
        await self.bot.wait_until_ready()
        await self.db.initialize()
        
        rosters_data = await self.db.load_rosters()
        logger.info(f"Restoring {len(rosters_data)} rosters from database")
        
        for data in rosters_data:
            try:
                # Fetch the message
                channel = self.bot.get_channel(data["channel_id"])
                if not channel:
                    logger.warning(f"Channel {data['channel_id']} not found for roster {data['custom_id']}")
                    continue
                
                try:
                    message = await channel.fetch_message(data["message_id"])
                except discord.NotFound:
                    logger.warning(f"Message {data['message_id']} not found, deleting roster {data['custom_id']}")
                    await self.db.delete_roster(data["custom_id"])
                    continue
                
                # Recreate the view
                view = RosterMainView(self, data["custom_id"])
                view.title = data["title"]
                view.date_time = data["date_time"]
                view.description = data["description"]
                view.limit = data["roster_limit"]
                view.thumbnail = data["thumbnail"]
                view.participants = data["participants"]
                view.roster_message = message
                view.channel_id = data["channel_id"]
                view.message_id = data["message_id"]
                
                # Re-attach the view to the message
                self.bot.add_view(view, message_id=message.id)
                self.active_rosters[data["custom_id"]] = view
                
                logger.info(f"Restored roster {data['custom_id']} with {len(view.participants)} participants")
            except Exception as e:
                logger.error(f"Failed to restore roster {data.get('custom_id', 'unknown')}: {e}")
    
    async def save_roster_to_db(self, view: RosterMainView):
        # Save a roster to the database
        if not view.roster_message:
            return
        
        await self.db.save_roster(
            custom_id=view.custom_id,
            title=view.title,
            date_time=view.date_time,
            description=view.description,
            channel_id=view.channel_id,
            message_id=view.message_id,
            participants=view.participants,
            roster_limit=view.limit,
            thumbnail=view.thumbnail
        )
    
    @tasks.loop(hours=1)
    async def roster_refresh_task(self):
        # Background task to validate rosters periodically (not refresh messages)
        # This only checks if messages still exist, doesn't update them
        logger.info(f"Running roster validation check for {len(self.active_rosters)} rosters")
        
        for custom_id, view in list(self.active_rosters.items()):
            try:
                # Only verify message existence, don't fetch/update
                if view.channel_id and view.message_id:
                    channel = self.bot.get_channel(view.channel_id)
                    if not channel:
                        logger.warning(f"Channel missing for roster {custom_id}, removing from active rosters")
                        del self.active_rosters[custom_id]
                        continue
                    
                    # Light check - only verify if message was deleted
                    # Don't fetch message unless necessary
                    if not view.roster_message:
                        try:
                            message = await channel.fetch_message(view.message_id)
                            view.roster_message = message
                            logger.info(f"Recovered message reference for roster {custom_id}")
                        except discord.NotFound:
                            logger.warning(f"Roster message {custom_id} was deleted, removing from active rosters")
                            await self.db.delete_roster(custom_id)
                            del self.active_rosters[custom_id]
                        except discord.HTTPException as e:
                            if e.status != 429:  # Ignore rate limits here
                                logger.error(f"Error validating roster {custom_id}: {e}")
                        except OSError as e:
                            logger.warning(f"Network error validating roster {custom_id}: {e}")
            except Exception as e:
                logger.error(f"Error in roster validation for {custom_id}: {e}")
        
        logger.info(f"Roster validation complete. {len(self.active_rosters)} active rosters")
    
    @roster_refresh_task.error
    async def roster_refresh_task_error(self, error: Exception):
        # Handle task-level errors to prevent task from stopping
        logger.error(f"Roster validation task encountered an error: {error}", exc_info=True)
    
    @roster_refresh_task.before_loop
    async def before_roster_refresh(self):
        await self.bot.wait_until_ready()
    
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.command(name="roster_start", description="Create a new CTF roster (admin only)")
    async def roster_start(self, interaction: discord.Interaction):
        try:
            # Create unique ID for this roster
            custom_id = f"roster_{interaction.id}"
            
            logger.info(f"Creating roster (ID: {custom_id}) by {interaction.user}")
            
            # Create the main view for this roster
            roster_view = RosterMainView(self, custom_id)
            
            # Show configuration modal
            modal = RosterConfigModal()
            modal.view = roster_view  # Pass the view to the modal
            
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(f"Failed to start roster: {e}", exc_info=True)
            raise
    
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.command(name="roster_delete", description="Delete a roster (admin only)")
    @app_commands.describe(message_id="The message ID of the roster to delete")
    async def roster_delete(self, interaction: discord.Interaction, message_id: str):
        # Delete a roster by message ID
        try:
            msg_id = int(message_id)
            
            # Find the roster
            roster_to_delete = None
            for custom_id, view in self.active_rosters.items():
                if view.message_id == msg_id:
                    roster_to_delete = (custom_id, view)
                    break
            
            if not roster_to_delete:
                await interaction.response.send_message(
                    "❌ Roster not found. Make sure the message ID is correct.",
                    ephemeral=True
                )
                return
            
            custom_id, view = roster_to_delete
            
            # Delete from database
            await self.db.delete_roster(custom_id)
            
            # Remove from active rosters
            del self.active_rosters[custom_id]
            
            # Try to delete the message
            if view.roster_message:
                try:
                    await view.roster_message.delete()
                except discord.HTTPException:
                    pass
            
            await interaction.response.send_message(
                f"✅ Roster deleted successfully.",
                ephemeral=True
            )
            logger.info(f"Deleted roster {custom_id}")
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid message ID. Please provide a valid number.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(RosterCog(bot))
