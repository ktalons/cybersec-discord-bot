# Cybersecurity Discord Bot

A Discord bot for your cybersecurity club, featuring:
- Email-based verification for @arizona.edu addresses
- Giveaway utility
- Google Calendar (ICS) polling and announcements
- CTFtime upcoming events announcements

## Prerequisites
- Python 3.10+
- A Discord application and bot token (with the "Server Members Intent" enabled)
- A Gmail account with an App Password (recommended) for sending verification emails

## Quick start
1) Create a virtualenv and install dependencies

   macOS/Linux:
   - python3 -m venv .venv
   - .venv/bin/pip install -r requirements.txt

2) Configure environment
   - Copy .env.example to .env and fill in values
   - Make sure to use a Gmail App Password instead of your account password

3) Run the bot
   - .venv/bin/python src/main.py

## Environment variables (.env)
- DISCORD_TOKEN=your_discord_bot_token
- VERIFY_DOMAIN=arizona.edu
- VERIFY_ROLE_NAME=Member
- VERIFY_ROLE_ID=        # optional, preferred over name if provided
- GMAIL_USER=you@example.com
- GMAIL_APP_PASSWORD=app_password_here
- GUILD_IDS=             # optional: comma-separated guild IDs for fast per-guild slash command sync
- CALENDAR_ICS_URL=      # optional: Google Calendar public ICS URL
- CALENDAR_CHANNEL_ID=   # numeric channel ID to post calendar events
- CTF_CHANNEL_ID=        # numeric channel ID to post CTFtime events
- CTFTIME_EVENTS_WINDOW_DAYS=7

## Notes on slash command sync
- If GUILD_IDS is provided, slash commands are synced per-guild for instant availability.
- If not, global sync may take up to an hour to propagate everywhere.
- Use /sync (server admin only) to force re-sync in a guild if needed.

## Permissions
- The bot requires permissions to manage roles (for verification) and send messages to the target channels
- Ensure the "Server Members Intent" and "Message Content Intent" are enabled in the Developer Portal as appropriate

## Security
- Never commit your .env file
- Use Gmail App Passwords, not your main account password
