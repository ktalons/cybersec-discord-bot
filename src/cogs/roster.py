from __future__ import annotations
import asyncio
from typing import Dict, Optional, List
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands


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
    
    def __init__(self, cog: RosterCog):
        super().__init__(timeout=None)  # Persistent view
        self.cog = cog
        
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
        
        # Update the roster display
        await self.update_roster_display()

    # adds member, returns true
    async def add_participant(self, user: discord.Member, skill_level: str) -> bool:
        
        # Double-check limit
        if self.limit and len(self.participants) >= self.limit:
            return False
        
        self.participants[user.id] = (user.display_name, skill_level)
        return True

    # initial roster post
    async def post_roster(self, interaction: discord.Interaction):
        embed = self._build_embed()
        
        await interaction.response.send_message(
            content="📋 **CTF Roster Created!**",
            embed=embed,
            view=self,
        )
        
        # Store message reference
        self.roster_message = await interaction.original_response()

    # Updates the roster embed with current participants
    async def update_roster_display(self):
        if not self.roster_message:
            return
        
        embed = self._build_embed()
        
        try:
            await self.roster_message.edit(embed=embed)
        except discord.HTTPException:
            pass  # Message might have been deleted

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
        self.bot = bot
    
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.command(name="roster_start", description="Create a new CTF roster (admin only)")
    async def roster_start(self, interaction: discord.Interaction):
        
        # Create the main view for this roster
        roster_view = RosterMainView(self)
        
        # Show configuration modal
        modal = RosterConfigModal()
        modal.view = roster_view  # Pass the view to the modal
        
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot):
    await bot.add_cog(RosterCog(bot))
