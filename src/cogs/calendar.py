from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Set, Optional, Dict
from zoneinfo import ZoneInfo

import aiohttp
import discord
from discord.ext import commands, tasks

from ..config import Config

logger = logging.getLogger("bot.calendar")


class CalendarCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config  # type: ignore[attr-defined]
        # Track sent 60‑minute reminders
        self.posted_reminders: Set[str] = set()
        self._run_loop.start()

    def cog_unload(self):
        self._run_loop.cancel()

    # Check every minute to reliably hit the 60‑minute reminder window
    @tasks.loop(minutes=1)
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
                        logger.warning(f"Calendar fetch failed: HTTP {resp.status}")
                        return
                    ics_text = await resp.text()
        except Exception as e:
            logger.warning(f"Calendar fetch error: {e}")
            return

        # Unfold folded lines per RFC5545, then iterate events
        ics_text = _unfold_ics(ics_text)
        now = datetime.now(timezone.utc)
        reminder_offset = timedelta(minutes=60)
        window = timedelta(minutes=2)  # ±2 minutes around the target

        for block in ics_text.split("BEGIN:VEVENT"):
            if "END:VEVENT" not in block:
                continue

            try:
                event = _parse_event_block(block)
            except Exception as e:
                logger.debug(f"Skip event parse error: {e}")
                continue
            if not event:
                continue

            start = event["start"]  # timezone‑aware UTC datetime
            uid = event.get("uid") or event.get("summary") or "unknown"

            # Fire exactly once around T-60 minutes
            delta = (start - now)
            if abs(delta - reminder_offset) <= window:
                key = f"{uid}-{start.isoformat()}-60m"
                if key in self.posted_reminders:
                    continue
                self.posted_reminders.add(key)

                embed = _build_calendar_embed(event)
                try:
                    await channel.send(embed=embed)
                    logger.info(f"Posted 60‑minute reminder for event: {event.get('summary','(No Title)')}")
                except Exception as e:
                    logger.error(f"Failed to send calendar reminder: {e}")

    @_run_loop.before_loop
    async def _before_loop(self):
        await self.bot.wait_until_ready()


def _unfold_ics(text: str) -> str:
    # Join lines that start with a space or tab with the previous line
    out: list[str] = []
    for line in text.splitlines():
        if line.startswith(" ") or line.startswith("\t"):
            if out:
                out[-1] += line[1:]
            else:
                out.append(line.lstrip())
        else:
            out.append(line)
    return "\n".join(out)


def _parse_event_block(block: str) -> Optional[Dict[str, object]]:
    # Extract fields with simple param support (TZID, VALUE)
    summary: Optional[str] = None
    uid: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    start: Optional[datetime] = None

    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()
        elif line.startswith("UID:"):
            uid = line.split(":", 1)[1].strip()
        elif line.startswith("LOCATION:"):
            location = line.split(":", 1)[1].strip()
        elif line.startswith("DESCRIPTION:"):
            description = line.split(":", 1)[1].strip().replace("\\n", "\n")
        elif line.startswith("URL:"):
            url = line.split(":", 1)[1].strip()
        elif line.startswith("DTSTART"):
            # DTSTART[:|;params]:value
            try:
                left, value = line.split(":", 1)
            except ValueError:
                continue
            tzid: Optional[str] = None
            all_day = False
            if ";" in left:
                for part in left.split(";")[1:]:
                    if part.startswith("TZID="):
                        tzid = part.split("=", 1)[1]
                    elif part.startswith("VALUE=") and part.endswith("DATE"):
                        all_day = True
            # Skip all‑day events for reminders
            if all_day:
                continue
            start = _parse_ics_datetime_with_tz(value.strip(), tzid)

    if start is None:
        return None

    return {
        "summary": summary or "(No Title)",
        "uid": uid,
        "location": location,
        "description": description,
        "url": url,
        "start": start,
    }


def _parse_ics_datetime_with_tz(value: str, tzid: Optional[str]) -> datetime:
    # Supports forms like 20250101T170000Z or 20250101T170000 with TZID
    value = value.strip()
    if value.endswith("Z"):
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return dt
    # Naive local time with TZID
    dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
    if tzid:
        try:
            tz = ZoneInfo(tzid)
        except Exception:
            tz = timezone.utc
        return dt.replace(tzinfo=tz).astimezone(timezone.utc)
    # Assume UTC if no TZID
    return dt.replace(tzinfo=timezone.utc)


def _build_calendar_embed(event: Dict[str, object]) -> discord.Embed:
    start: datetime = event["start"]  # type: ignore[index]
    title: str = str(event.get("summary", "(No Title)"))
    location: Optional[str] = event.get("location")  # type: ignore[assignment]
    description: Optional[str] = event.get("description")  # type: ignore[assignment]
    url: Optional[str] = event.get("url")  # type: ignore[assignment]

    embed = discord.Embed(
        title="Cyber Saguaros Calendar Event",
        color=discord.Color.green(),
    )
    embed.add_field(name="Event", value=title, inline=False)
    ts = int(start.timestamp())
    embed.add_field(name="Date & Time", value=f"<t:{ts}:F> • <t:{ts}:R>", inline=False)
    if location:
        embed.add_field(name="Location", value=str(location)[:1024], inline=False)
    if description:
        embed.add_field(name="Description", value=str(description)[:1024], inline=False)
    if url:
        embed.add_field(name="Link", value=str(url), inline=False)
    return embed


async def setup(bot: commands.Bot):
    await bot.add_cog(CalendarCog(bot))
