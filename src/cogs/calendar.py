from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Set, Optional

import aiohttp
import discord
from discord.ext import commands, tasks

from ..config import Config


class CalendarCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config  # type: ignore[attr-defined]
        self.posted_ids: Set[str] = set()
        self._run_loop.start()

    def cog_unload(self):
        self._run_loop.cancel()

    @tasks.loop(hours=1)
    async def _run_loop(self):
        if not (self.config.calendar_ics_url and self.config.calendar_channel_id):
            return
        channel = self.bot.get_channel(self.config.calendar_channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.config.calendar_ics_url, timeout=30) as resp:
                    if resp.status != 200:
                        return
                    ics_text = await resp.text()
        except Exception:
            return

        # Minimal ICS parsing to find upcoming events (next 24 hours)
        now = datetime.now(timezone.utc)
        soon = now + timedelta(hours=24)
        # Very light parsing: split by BEGIN:VEVENT ... END:VEVENT
        for block in ics_text.split("BEGIN:VEVENT"):
            if "END:VEVENT" not in block:
                continue
            uid = _ical_get(block, "UID") or _ical_get(block, "X-WR-RELCALID") or None
            dtstart = _ical_get(block, "DTSTART")
            summary = _ical_get(block, "SUMMARY") or "(No Title)"
            url = _ical_get(block, "URL")

            if not dtstart:
                continue
            try:
                event_dt = _parse_ics_datetime(dtstart)
            except Exception:
                continue

            if not (now <= event_dt <= soon):
                continue

            key = f"{uid or summary}-{event_dt.isoformat()}"
            if key in self.posted_ids:
                continue
            self.posted_ids.add(key)

            embed = discord.Embed(title=summary, description="Upcoming calendar event", color=0x2ecc71)
            embed.add_field(name="Starts", value=f"<t:{int(event_dt.timestamp())}:F>")
            if url:
                embed.add_field(name="More info", value=url, inline=False)
            await channel.send(embed=embed)

    @_run_loop.before_loop
    async def _before_loop(self):
        await self.bot.wait_until_ready()


def _ical_get(block: str, key: str) -> Optional[str]:
    # Find lines like KEY:VALUE (no unfolding/encoding handling for simplicity)
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(key + ":"):
            return line.split(":", 1)[1].strip()
        if line.startswith(key + ";"):
            # Handle params like DTSTART;TZID=...
            return line.split(":", 1)[1].strip()
    return None


def _parse_ics_datetime(value: str) -> datetime:
    # Handle forms like 20250101T120000Z or 20250101T120000
    value = value.strip()
    if value.endswith("Z"):
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    return dt

async def setup(bot: commands.Bot):
    await bot.add_cog(CalendarCog(bot))
