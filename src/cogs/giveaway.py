from __future__ import annotations
import asyncio
import random
from typing import List, Set, Optional

import discord
from discord import app_commands
from discord.ext import commands


class GiveawayView(discord.ui.View):
    def __init__(self, *, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.entries: Set[int] = set()

    @discord.ui.button(label="Enter Giveaway", style=discord.ButtonStyle.success)
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.entries.add(interaction.user.id)
        await interaction.response.send_message("You're entered!", ephemeral=True)


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

        view = GiveawayView(timeout=duration_minutes * 60)
        await interaction.response.send_message(
            f"Giveaway started for: {prize}\nClick the button below to enter! Ends in {duration_minutes} minutes.",
            view=view,
        )

        # Wait for the giveaway duration
        await asyncio.sleep(duration_minutes * 60)

        # Determine winner
        if not view.entries:
            await interaction.followup.send("No entries. Giveaway cancelled.")
            return

        winner_id = random.choice(list(view.entries))
        winner = interaction.guild.get_member(winner_id) if interaction.guild else None
        if winner:
            await interaction.followup.send(f"Congratulations {winner.mention}! You won: {prize}")
        else:
            await interaction.followup.send("Winner left the server or cannot be found.")
