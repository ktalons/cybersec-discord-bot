# Cybersec Discord Bot

A modern Discord bot tailored for cybersecurity clubs and communities.

- Email-based member verification (e.g., @arizona.edu)
- Giveaways and simple utilities
- Google Calendar (ICS) polling and announcements
- CTFtime upcoming events announcements

<p>
  <a href="https://github.com/ktalons/cybersec-discord-bot/actions/workflows/ci.yml">
    <img alt="CI" src="https://github.com/ktalons/cybersec-discord-bot/actions/workflows/ci.yml/badge.svg" />
  </a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" />
  <img alt="discord.py" src="https://img.shields.io/badge/discord.py-2.4%2B-5865F2?logo=discord&logoColor=white" />
  <a href="https://github.com/ktalons/cybersec-discord-bot/commits">
    <img alt="Last commit" src="https://img.shields.io/github/last-commit/ktalons/cybersec-discord-bot?logo=github" />
  </a>
  <a href="https://github.com/ktalons/cybersec-discord-bot/issues">
    <img alt="Issues" src="https://img.shields.io/github/issues/ktalons/cybersec-discord-bot?logo=github" />
  </a>
</p>

---

## Table of contents
- Features
- Demo
- Quick start
- Docker
- Configuration
- Usage
- Commands (placeholders)
- Permissions and intents
- Troubleshooting
- Development
- License

## Features
- Email-based verification workflow to gate access to your server
- Giveaway utility for quick raffles
- Calendar announcements from a public Google Calendar (ICS)
- CTFtime upcoming events announcements with a configurable window

## Demo
> Placeholder: Add a screenshot or GIF demonstrating verification or announcements.
>
> Suggested paths:
> - `docs/demo.gif`
> - `docs/screenshot.png`
>
> Example embed (update the path once added):
>
> ![Demo](docs/demo.gif)

## Quick start

Prerequisites:
- Python 3.10+
- A Discord application and bot token (enable "Server Members Intent")
- A Gmail account with an App Password for sending verification emails

Install and run:

```bash
# Create a virtual environment and install dependencies
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and fill in values (see Configuration below)

# Start the bot
python -m src.main
```

## Docker
Build and run the bot using Docker. Provide configuration via environment variables or an env file.

```bash
# Build the image
docker build -t cybersec-discord-bot .

# Run with an env file (recommended)
# Ensure your .env contains DISCORD_TOKEN and other configuration
docker run --rm \
  --name cybersec-bot \
  --env-file .env \
  cybersec-discord-bot

# Alternatively, pass individual variables
# (replace values or use your shell's exported vars)
# docker run --rm \
#   -e DISCORD_TOKEN="$DISCORD_TOKEN" \
#   -e VERIFY_DOMAIN=arizona.edu \
#   cybersec-discord-bot
```

## Configuration
Copy .env.example to .env and set the following variables:

- DISCORD_TOKEN: Your bot token
- VERIFY_DOMAIN: Allowed email domain (default: arizona.edu)
- VERIFY_ROLE_NAME: Role name to grant on verification (optional)
- VERIFY_ROLE_ID: Role ID to grant on verification (preferred if set)
- GMAIL_USER: Gmail address used to send verification codes
- GMAIL_APP_PASSWORD: Gmail App Password (not your normal password)
- GUILD_IDS: Optional comma-separated guild IDs for instant per-guild slash command sync
- CALENDAR_ICS_URL: Public Google Calendar ICS URL
- CALENDAR_CHANNEL_ID: Channel ID to post calendar events
- CTF_CHANNEL_ID: Channel ID to post CTFtime events
- CTFTIME_EVENTS_WINDOW_DAYS: Days ahead to look for CTFtime events (default: 7)

Notes on slash command sync:
- If GUILD_IDS is provided, slash commands are synced per-guild for instant availability
- If not provided, global sync can take up to an hour
- Admins can run /sync in a server to force a re-sync

## Usage
- Start the bot: `python -m src.main` or via Docker as shown above
- Invite the bot to your server with permissions to manage roles and send messages in target channels
- Configure dedicated channels for calendar and CTFtime announcements via the respective channel IDs

## Commands (placeholders)
> Placeholder: Document slash commands for each cog here once finalized.
>
> Suggested structure:
> - Verification
>   - `/verify` — Initiate email verification flow (details TBD)
> - Giveaway
>   - `/giveaway start` — Start a giveaway (details TBD)
> - Calendar
>   - `/calendar subscribe` — Subscribe a channel to calendar updates (details TBD)
> - CTFtime
>   - `/ctf upcoming` — Show upcoming events (details TBD)

## Permissions and intents
- Required Discord intents: Server Members (for role assignment), Guilds, and Messages
- The bot must have permission to manage roles (for verification) and send messages in target channels

## Troubleshooting
- If slash commands are missing, set GUILD_IDS or run /sync (requires Manage Server)
- Ensure Gmail uses an App Password and that less secure access is not required
- Double-check channel and role IDs are correct and the bot has sufficient permissions

## Development
- Linting/formatting is not enforced in CI; you can add your preferred tools (e.g., ruff, black) locally
- CI currently compiles sources (`python -m compileall -q src`) to catch syntax errors

## License
No license file has been provided yet. Consider adding a LICENSE (e.g., MIT, Apache-2.0) so others know how they can use this project.
