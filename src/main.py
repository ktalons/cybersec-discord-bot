import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

from .config import load_config, Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")


class CybersecBot(commands.Bot):
    def __init__(self, config: Config):
        intents = discord.Intents.default()
        intents.messages = True
        intents.guilds = True
        intents.members = True  # Required for role assignment

        super().__init__(command_prefix="!", intents=intents)
        self.config = config

    async def setup_hook(self) -> None:
        # Load cogs
        from .cogs.verification import VerificationCog
        from .cogs.giveaway import GiveawayCog
        from .cogs.calendar import CalendarCog
        from .cogs.ctftime import CTFTimeCog
        from .cogs.roster import RosterCog

        await self.add_cog(VerificationCog(self))
        await self.add_cog(GiveawayCog(self))
        await self.add_cog(CalendarCog(self))
        await self.add_cog(CTFTimeCog(self))
        await self.add_cog(RosterCog(self))

        # Admin-only command to force sync
        @app_commands.default_permissions(manage_guild=True)
        @self.tree.command(name="sync", description="Force sync application commands in this guild (admin only)")
        async def sync_cmd(interaction: discord.Interaction):
            await interaction.response.defer(empheral=True)
            try:
                if interaction.guild:
                    await self.tree.sync(guild=interaction.guild)
                    await interaction.response.send_message("Commands synced for this guild.", ephemeral=True)
                    #Sync
                    self.tree.copy_global_to(guild=interaction.guild)
                    synced = await self.tree.sync(guild=interaction.guild)
                    await interaction.response.send_message(f"Synced {len(synced)} command(s) to this guild.", ephemeral=True)
                else:
                    await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Sync failed: {e}", ephemeral=True)

    async def on_ready(self):
        # Per-guild sync for fast availability, or global fallback
        try:
            if self.config.guild_ids:
                for gid in self.config.guild_ids:
                    guild = discord.Object(id=gid)
                    await self.tree.sync(guild=guild)
                logger.info(f"Synced commands for {len(self.config.guild_ids)} guild(s)")
                #Sync
                for gid in self.config.guild_ids:
                    guild = discord.Object(id=gid)
                    self.tree.copy_global_to(guild=guild)
                    synced = await self.tree.sync(guild=guild)
                    logger.info(f"Synced {len(synced)} command(s) to guild {gid}")
            else:
                synced = await self.tree.sync()
                logger.info(f"Globally synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
        logger.info(f"Logged in as {self.user}")


def main():
    config = load_config()
    if not config.token:
        raise SystemExit("DISCORD_TOKEN is not set. Add it to your .env file.")

    bot = CybersecBot(config)
    bot.run(config.token)


if __name__ == "__main__":
    main()
