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
- Quick start
- Docker
- Configuration
- Usage
- Commands
- Permissions and intents
- Troubleshooting
- Development
- Contributing & License

## Features
- **Email verification** — Email-based verification workflow to gate access to your server
- **CTF roster management** — Create team rosters with skill level tracking (Rookie, Intermediate, Veteran)
- **Giveaways** — Interactive raffles with real-time countdown timer and entry count
- **Calendar announcements** — Automatic posts from a public Google Calendar (ICS)
- **CTFtime integration** — Upcoming CTF events announcements with a configurable window


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

### Docker Compose
Use Docker Compose for a simple, repeatable local run with logs.

```bash
# Build and start in the background
docker compose up -d

# Tail logs
docker compose logs -f

# Stop and remove the container
docker compose down
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

## Commands

### Verification
- `/verify` — Request a verification code via email
- `/submit_code` — Submit your verification code to gain access

### Roster Management (Admin only)
- `/roster_start` — Create a new CTF team roster with interactive sign-ups
  - Configure title, date/time, description, participant limit, and thumbnail
  - Members select skill level: 🐣 Rookie, 🌵 Intermediate, 🥷 Veteran
  - Real-time roster updates as users join or remove themselves

### Giveaways (Admin only)
- `/giveaway_start` — Start a giveaway with live countdown timer
  - Displays real-time entry count and time remaining
  - Prevents duplicate entries
  - Automatically selects a winner when time expires

### Utility (Admin only)
- `/sync` — Force sync slash commands in the current server

### Background Tasks
- **Calendar announcements** — Hourly check for events in the next 24 hours
- **CTFtime announcements** — Bi-hourly check for upcoming CTF events

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

## Contributing & License

We welcome contributions! Please review the following:

- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Guidelines for contributing to this project
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** — Community standards and behavior expectations
- **[LICENSE](LICENSE)** — Project license terms
