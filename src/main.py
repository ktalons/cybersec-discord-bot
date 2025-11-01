import asyncio
import logging
import sys
from typing import Optional
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

from .config import load_config, Config

# Configure logging with timestamps and better formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
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
        # Load all cogs with error handling
        logger.info("========================================")
        logger.info("Starting bot setup...")
        logger.info("========================================")
        
        # Load cogs with individual error handling
        cogs = [
            ("verification", "VerificationCog"),
            ("giveaway", "GiveawayCog"),
            ("calendar", "CalendarCog"),
            ("ctftime", "CTFTimeCog"),
            ("roster", "RosterCog"),
        ]
        
        loaded = 0
        failed = 0
        
        for module_name, cog_name in cogs:
            try:
                logger.info(f"Loading cog: {cog_name}...")
                # Use importlib for proper relative imports
                from importlib import import_module
                module = import_module(f".cogs.{module_name}", package="src")
                cog_class = getattr(module, cog_name)
                await self.add_cog(cog_class(self))
                logger.info(f"✅ Successfully loaded {cog_name}")
                loaded += 1
            except Exception as e:
                logger.error(f"❌ Failed to load {cog_name}: {e}", exc_info=True)
                failed += 1
        
        logger.info(f"Cog loading complete: {loaded} loaded, {failed} failed")

        # Admin-only command to force sync
        @app_commands.default_permissions(manage_guild=True)
        @self.tree.command(name="sync", description="Force sync application commands in this guild (admin only)")
        async def sync_cmd(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                if interaction.guild:
                    # Copy global commands to guild and sync
                    self.tree.copy_global_to(guild=interaction.guild)
                    synced = await self.tree.sync(guild=interaction.guild)
                    await interaction.followup.send(f"✅ Synced {len(synced)} command(s) to this guild.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ This command must be used in a server.", ephemeral=True)
            except Exception as e:
                logger.error(f"Sync command failed: {e}")
                await interaction.followup.send(f"❌ Sync failed: {e}", ephemeral=True)

    async def on_ready(self):
        # Called when the bot is ready and connected
        logger.info("========================================")
        logger.info(f"✅ Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        logger.info("========================================")
        
        # List guilds
        for guild in self.guilds:
            logger.info(f"  - {guild.name} (ID: {guild.id}, Members: {guild.member_count})")
        
        # Command sync
        logger.info("Starting command sync...")
        try:
            if self.config.guild_ids:
                logger.info(f"Guild-specific sync for {len(self.config.guild_ids)} guild(s)")
                for gid in self.config.guild_ids:
                    try:
                        guild = discord.Object(id=gid)
                        self.tree.copy_global_to(guild=guild)
                        synced = await self.tree.sync(guild=guild)
                        logger.info(f"✅ Synced {len(synced)} command(s) to guild {gid}")
                    except Exception as e:
                        logger.error(f"❌ Failed to sync guild {gid}: {e}")
            else:
                logger.info("Performing global command sync (may take up to 1 hour)...")
                synced = await self.tree.sync()
                logger.info(f"✅ Globally synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"❌ Command sync failed: {e}", exc_info=True)
        
        logger.info("========================================")
        logger.info("🚀 Bot is ready and operational!")
        logger.info("========================================")
    
    async def on_error(self, event_method: str, *args, **kwargs):
        # Global error handler for events
        logger.error(f"Error in event '{event_method}'", exc_info=True)
    
    async def on_command_error(self, ctx, error):
        # Handle command errors
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        logger.error(f"Command error in {ctx.command}: {error}", exc_info=True)
    
    async def on_guild_join(self, guild: discord.Guild):
        # Log when bot joins a new guild
        logger.info(f"🎉 Joined new guild: {guild.name} (ID: {guild.id}, Members: {guild.member_count})")
    
    async def on_guild_remove(self, guild: discord.Guild):
        # Log when bot leaves a guild
        logger.warning(f"👋 Removed from guild: {guild.name} (ID: {guild.id})")


def main():
    # Main entry point with error handling
    logger.info("========================================")
    logger.info("Cybersecurity Discord Bot Starting...")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("========================================")
    
    try:
        logger.info("Loading configuration...")
        config = load_config()
        
        if not config.token:
            logger.error("❌ DISCORD_TOKEN is not set in .env file")
            raise SystemExit("DISCORD_TOKEN is not set. Add it to your .env file.")
        
        logger.info("✅ Configuration loaded successfully")
        
        if config.guild_ids:
            logger.info(f"Guild IDs configured: {config.guild_ids}")
        else:
            logger.info("No guild IDs configured - will use global sync")
        
        logger.info("Initializing bot...")
        bot = CybersecBot(config)
        
        logger.info("Connecting to Discord...")
        bot.run(config.token, log_handler=None)  # We handle logging ourselves
        
    except KeyboardInterrupt:
        logger.info("\n👋 Bot shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
