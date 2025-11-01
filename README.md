# 🛡️ Cybersec Discord Bot

A feature-rich Discord bot built for cybersecurity clubs and CTF communities.

**Key Features:** Email verification • CTF Rosters • Giveaways • Calendar Integration • CTFtime Events

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

## 📋 Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Commands](#commands)
- [Documentation](#documentation)
- [Contributing](#contributing)

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 **Email Verification** | Gate server access with domain-based email verification |
| 👥 **CTF Rosters** | Create team rosters with skill levels (Rookie/Intermediate/Veteran) |
| 🎉 **Giveaways** | Interactive raffles with live countdown and entry tracking |
| 📅 **Calendar Integration** | Auto-post events from Google Calendar (ICS) |
| 🚩 **CTFtime Events** | Announce upcoming CTF competitions |
| 💾 **Database Persistence** | SQLite storage - survives restarts, supports multi-day events |
| 📊 **Enhanced Logging** | Comprehensive status updates and error tracking |


## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Discord bot token ([Create one here](https://discord.com/developers/applications))
  - Enable **Server Members Intent** in Bot settings
- Gmail account with [App Password](https://support.google.com/accounts/answer/185833) (for verification emails)

### Installation

<details>
<summary><b>Option 1: Python (Local)</b></summary>

```bash
# Clone and setup
git clone https://github.com/ktalons/cybersec-discord-bot.git
cd cybersec-discord-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your values

# Run
.venv/bin/python -m src.main
```
</details>

<details>
<summary><b>Option 2: Docker Compose (Recommended)</b></summary>

```bash
# Setup
cp .env.example .env
# Edit .env with your values

# Run
docker-compose up -d

# View logs
docker-compose logs -f
```
</details>

## ⚙️ Configuration

### Required Environment Variables
```env
DISCORD_TOKEN=your_bot_token_here
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

### Optional Variables
```env
VERIFY_DOMAIN=arizona.edu          # Email domain for verification
VERIFY_ROLE_ID=123456789           # Role ID to assign after verification
GUILD_IDS=123,456                  # Instant command sync (comma-separated)
CALENDAR_ICS_URL=https://...       # Google Calendar public ICS URL
CALENDAR_CHANNEL_ID=123456789      # Channel for calendar posts
CTF_CHANNEL_ID=123456789           # Channel for CTFtime posts
CTFTIME_EVENTS_WINDOW_DAYS=7       # Days ahead for CTF events
```

> 💡 **Tip:** Set `GUILD_IDS` for instant slash command availability. Without it, global sync takes up to 1 hour.

## 🤖 Commands

### User Commands
- `/verify` - Request email verification code
- `/submit_code` - Submit verification code
- Roster buttons - Join/leave CTF teams
- Giveaway buttons - Enter/track raffles

### Admin Commands
| Command | Description |
|---------|-------------|
| `/roster_start` | Create interactive CTF team roster |
| `/roster_delete` | Remove a roster by message ID |
| `/giveaway_start` | Launch a timed giveaway raffle |
| `/sync` | Force slash command sync |

### Background Tasks
- ⏰ **Hourly** - Calendar event checks
- ⏰ **Every 2 hours** - CTFtime event checks
- ⏰ **Daily** - Database cleanup (removes entries 60+ days old)

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[IMPROVEMENTS.md](IMPROVEMENTS.md)** | Feature overview and technical details |
| **[LOGGING.md](LOGGING.md)** | Log format guide and debugging tips |
| **[DEPLOY.md](DEPLOY.md)** | Deployment instructions and checklist |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | How to contribute to this project |
| **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** | Community standards |

## 🔧 Troubleshooting

<details>
<summary><b>Commands not appearing in Discord?</b></summary>

- Set `GUILD_IDS` in `.env` for instant sync
- Run `/sync` command (requires Manage Server permission)
- Wait up to 1 hour for global sync
- Check bot has application commands scope in invite URL
</details>

<details>
<summary><b>Email verification not working?</b></summary>

- Use Gmail App Password, not regular password
- Enable "Less secure app access" if needed
- Check `GMAIL_USER` and `GMAIL_APP_PASSWORD` are set correctly
</details>

<details>
<summary><b>Bot crashes on restart?</b></summary>

- Check `data/` directory exists and is writable
- Review logs for specific error messages
- See [LOGGING.md](LOGGING.md) for log interpretation
</details>

> 💡 For more help, check [LOGGING.md](LOGGING.md) for common error patterns.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the terms in [LICENSE](LICENSE).

---

<p align="center">
  Made with ❤️ for cybersecurity communities<br>
  <a href="https://github.com/ktalons/cybersec-discord-bot/issues">Report Bug</a> •
  <a href="https://github.com/ktalons/cybersec-discord-bot/issues">Request Feature</a>
</p>
