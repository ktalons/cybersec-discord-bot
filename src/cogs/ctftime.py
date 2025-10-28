from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Set, List

import aiohttp
import discord
from discord.ext import commands, tasks

from ..config import Config


API_URL = "https://ctftime.org/api/v1/events/"


class CTFTimeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config  # type: ignore[attr-defined]
        self.posted_ids: Set[int] = set()
        self._loop.start()

    def cog_unload(self):
        self._loop.cancel()

    @tasks.loop(hours=2)
    async def _loop(self):
        if not self.config.ctf_channel_id:
            return
        channel = self.bot.get_channel(self.config.ctf_channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return

        now = datetime.now(timezone.utc)
        finish = now + timedelta(days=self.config.ctftime_window_days)
        params = {
            "limit": 25,
            "start": int(now.timestamp()),
            "finish": int(finish.timestamp()),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        return
                    data = await resp.json()
        except Exception:
            return

        # data is a list of events
        for ev in data:
            ev_id = int(ev.get("id")) if ev.get("id") is not None else None
            name = ev.get("title") or "(No Title)"
            url = ev.get("url") or ev.get("ctftime_url")
            ctftime_start = ev.get("start")

            if ev_id is None or not ctftime_start:
                continue

            # ctftime returns start in ISO8601; parse naive by slicing
            try:
                start_dt = datetime.fromisoformat(ctftime_start.replace("Z", "+00:00"))
            except Exception:
                continue

            if ev_id in self.posted_ids:
                continue

            embed = discord.Embed(title=name, description="Upcoming CTF", color=0x3498db)
            embed.add_field(name="Starts", value=f"<t:{int(start_dt.timestamp())}:F>")
            if url:
                embed.add_field(name="More info", value=url, inline=False)
            await channel.send(embed=embed)
            self.posted_ids.add(ev_id)

    @_loop.before_loop
    async def _before(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(CTFTimeCog(bot))