from __future__ import annotations
import asyncio
import random
from typing import List, Set, Optional
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands


class GiveawayView(discord.ui.View):
    def __init__(self, prize: str, end_time: datetime, *, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.entries: Set[int] = set()
        self.prize = prize
        self.end_time = end_time
        self.message: Optional[discord.Message] = None

    @discord.ui.button(label="Enter Giveaway", style=discord.ButtonStyle.success, emoji="🎉")
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.entries:
            await interaction.response.send_message("You're already entered!", ephemeral=True)
            return
        
        self.entries.add(interaction.user.id)
        await interaction.response.send_message("You're entered!", ephemeral=True)
        
        # Update the embed with new entry count
        if self.message:
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
        except discord.HTTPException:
            pass


class GiveawayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.command(name="giveaway_start", description="Start a giveaway (admin only)")
    @app_commands.describe(duration_minutes="Duration in minutes", prize="Description of the prize")
    async def giveaway_start(self, interaction: discord.Interaction, duration_minutes: int, prize: str):
        if duration_minutes <= 0:
            await interaction.response.send_message("Duration must be positive.", ephemeral=True)
            return

        # Calculate end time
        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        view = GiveawayView(prize, end_time, timeout=duration_minutes * 60)
        embed = view._build_embed()
        
        await interaction.response.send_message(
            embed=embed,
            view=view,
        )
        
        # Store message reference for updates
        view.message = await interaction.original_response()
        
        # Update countdown every 5 seconds
        update_interval = 5  # seconds
        total_duration = duration_minutes * 60
        elapsed = 0
        
        while elapsed < total_duration:
            await asyncio.sleep(update_interval)
            elapsed += update_interval
            await view.update_embed()
        
        # Final update
        await view.update_embed()

        # Determine winner
        if not view.entries:
            await interaction.followup.send("🎉 Giveaway ended! No entries, so no winner.")
            return

        winner_id = random.choice(list(view.entries))
        winner = interaction.guild.get_member(winner_id) if interaction.guild else None
        if winner:
            await interaction.followup.send(f"🎉 **Giveaway ended!**\n\nCongratulations {winner.mention}! You won: **{prize}**")
        else:
            await interaction.followup.send("🎉 Giveaway ended! Winner left the server or cannot be found.")

async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCog(bot))