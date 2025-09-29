from __future__ import annotations
import asyncio
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple, Optional

import discord
from discord import app_commands
from discord.ext import commands

from ..config import Config
from ..utils.emailer import send_email_smtp_ssl


@dataclass
class Pending:
    email: str
    code: str
    expires_at: datetime


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config  # type: ignore[attr-defined]
        self.pending: Dict[int, Pending] = {}
        self._cleanup_task = self.bot.loop.create_task(self._cleanup_loop())

    def cog_unload(self):
        self._cleanup_task.cancel()

    async def _cleanup_loop(self):
        try:
            while True:
                now = datetime.now(timezone.utc)
                to_delete = [uid for uid, p in self.pending.items() if p.expires_at <= now]
                for uid in to_delete:
                    del self.pending[uid]
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    def _generate_code(self) -> str:
        return str(random.randint(100000, 999999))

    def _valid_email(self, email: str) -> bool:
        return email.lower().endswith(f"@{self.config.verify_domain}")

    def _make_email_body(self, code: str) -> str:
        return (
            f"Your one-time verification code is: {code}\n\n"
            f"This code expires in 10 minutes."
        )

    async def _assign_role(self, member: discord.Member) -> bool:
        guild = member.guild
        role: Optional[discord.Role] = None
        if self.config.verify_role_id:
            role = guild.get_role(self.config.verify_role_id)
        if not role and self.config.verify_role_name:
            role = discord.utils.get(guild.roles, name=self.config.verify_role_name)
        if not role:
            return False
        try:
            await member.add_roles(role, reason="User verified via email code")
            return True
        except discord.Forbidden:
            return False

    @app_commands.command(name="verify", description="Start university email verification")
    @app_commands.describe(email=f"Your @{'arizona.edu'} email address")
    async def verify(self, interaction: discord.Interaction, email: str):
        if not self._valid_email(email):
            await interaction.response.send_message(
                f"That doesn't look like a valid @{self.config.verify_domain} email.", ephemeral=True
            )
            return

        if not (self.config.gmail_user and self.config.gmail_app_password):
            await interaction.response.send_message(
                "Email is not configured on the bot. Contact an admin.", ephemeral=True
            )
            return

        code = self._generate_code()
        sent = send_email_smtp_ssl(
            host="smtp.gmail.com",
            port=465,
            user=self.config.gmail_user,
            app_password=self.config.gmail_app_password,
            to_email=email,
            subject="Your Discord Verification Code",
            body=self._make_email_body(code),
        )

        if not sent:
            await interaction.response.send_message(
                "Failed to send email. Try again later.", ephemeral=True
            )
            return

        self.pending[interaction.user.id] = Pending(
            email=email, code=code, expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        await interaction.response.send_message(
            "Check your email! Then use /submit_code <yourcode> to complete verification.",
            ephemeral=True,
        )

    @app_commands.command(name="submit_code", description="Submit the verification code from your email")
    @app_commands.describe(code="The 6-digit verification code sent to your email")
    async def submit_code(self, interaction: discord.Interaction, code: str):
        data = self.pending.get(interaction.user.id)
        if not data:
            await interaction.response.send_message(
                "You haven’t started verification. Use /verify first.", ephemeral=True
            )
            return

        now = datetime.now(timezone.utc)
        if data.expires_at <= now:
            del self.pending[interaction.user.id]
            await interaction.response.send_message(
                "Your code has expired. Please run /verify again.", ephemeral=True
            )
            return

        if code.strip() != data.code:
            await interaction.response.send_message("Incorrect code. Try again.", ephemeral=True)
            return

        if not interaction.guild:
            await interaction.response.send_message(
                "This must be used in a server, not in DMs.", ephemeral=True
            )
            return

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            await interaction.response.send_message("Could not find your member record.", ephemeral=True)
            return

        ok = await self._assign_role(member)
        if ok:
            del self.pending[interaction.user.id]
            await interaction.response.send_message(
                f"You are now verified!", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Could not assign the verification role. Contact an admin.", ephemeral=True
            )
