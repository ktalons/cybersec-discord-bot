import os
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


def _get_list(name: str) -> Optional[List[int]]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    out: List[int] = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part))
        except ValueError:
            pass
    return out or None


@dataclass
class Config:
    token: str
    verify_domain: str
    verify_role_name: Optional[str]
    verify_role_id: Optional[int]
    gmail_user: Optional[str]
    gmail_app_password: Optional[str]
    guild_ids: Optional[List[int]]
    calendar_ics_url: Optional[str]
    calendar_channel_id: Optional[int]
    ctf_channel_id: Optional[int]
    ctftime_window_days: int


def load_config() -> Config:
    return Config(
        token=os.getenv("DISCORD_TOKEN", "").strip(),
        verify_domain=os.getenv("VERIFY_DOMAIN", "arizona.edu").strip(),
        verify_role_name=os.getenv("VERIFY_ROLE_NAME", "Member").strip() or None,
        verify_role_id=int(os.getenv("VERIFY_ROLE_ID", "0")) or None,
        gmail_user=os.getenv("GMAIL_USER", "").strip() or None,
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", "").strip() or None,
        guild_ids=_get_list("GUILD_IDS"),
        calendar_ics_url=os.getenv("CALENDAR_ICS_URL", "").strip() or None,
        calendar_channel_id=int(os.getenv("CALENDAR_CHANNEL_ID", "0")) or None,
        ctf_channel_id=int(os.getenv("CTF_CHANNEL_ID", "0")) or None,
        ctftime_window_days=int(os.getenv("CTFTIME_EVENTS_WINDOW_DAYS", "7")),
    )
