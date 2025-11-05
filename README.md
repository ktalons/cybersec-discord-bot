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

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 **Email Verification** | Gate server access with domain-based email verification |
| 👥 **CTF Rosters** | Create team rosters with skill levels (Rookie/Intermediate/Veteran) |
| 🎉 **Giveaways** | Interactive raffles with live countdown and entry tracking |
|| 📅 **Calendar Integration** | Auto-post events and 60‑minute reminders from Google Calendar (ICS) |
| 🚩 **CTFtime Events** | Announce upcoming CTF competitions |
| 💾 **Database Persistence** | SQLite storage - survives restarts, supports multi-day events |
| 📊 **Enhanced Logging** | Comprehensive status updates and error tracking |


## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Discord bot token
  - Enable **Server Members Intent** in Bot settings
- Gmail account with [App Password](https://support.google.com/accounts/answer/185833)

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

# Create data directory for persistence
mkdir -p data

# Run
docker-compose up -d

# View logs
docker-compose logs -f bot
```

> 📘 **For detailed Docker setup, volume persistence, and troubleshooting, see [docs/DOCKER.md](docs/DOCKER.md)**

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
- ⏰ **Every minute** - Calendar reminders (T‑60m before start)
- ⏰ **Every 2 hours** - CTFtime event checks
- ⏰ **Daily** - Database cleanup (removes entries 60+ days old)

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[DOCKER.md](docs/DOCKER.md)** | Complete Docker deployment guide with volume persistence |
| **[DEPLOY.md](docs/DEPLOY.md)** | General deployment instructions and checklist |
| **[IMPROVEMENTS.md](docs/IMPROVEMENTS.md)** | Feature overview and technical details |
| **[LOGGING.md](docs/LOGGING.md)** | Log format guide and debugging tips |
| **[DATABASE_CLEANUP.md](docs/DATABASE_CLEANUP.md)** | Database maintenance and cleanup information |
| **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** | How to contribute to this project |
| **[CODE_OF_CONDUCT.md](docs/CODE_OF_CONDUCT.md)** | Community standards |

## 🔧 Troubleshooting

<details>
<summary><b>Commands not appearing in Discord?</b></summary>

- Set `GUILD_IDS` in `.env` for instant sync
- Run `/sync` command
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
- For Docker: ensure volume is mounted (see [docs/DOCKER.md](docs/DOCKER.md))
- Review logs for specific error messages
- See [docs/LOGGING.md](docs/LOGGING.md) for log interpretation
</details>

<details>
<summary><b>Database in /tmp warning?</b></summary>

- Bot is using temporary storage - data will be lost on restart
- Fix: Create `data/` directory with proper permissions
- Docker: Add volume mount to `docker-compose.yml` (see [docs/DOCKER.md](docs/DOCKER.md))
- Set `DATABASE_PATH` in `.env` if using custom location
</details>

<details>
<summary><b>Calendar reminders not posting?</b></summary>

- Ensure `CALENDAR_ICS_URL` is publicly accessible and `CALENDAR_CHANNEL_ID` is set
- Event must not be all‑day and should be at least 60 minutes in the future
- ICS should include correct timezone (TZID) if not UTC
- Check logs for: `Posted 60‑minute reminder`
</details>

> 💡 For more help, check [docs/LOGGING.md](docs/LOGGING.md) for common error patterns.

## 🤝 Contributing

Contributions are welcome! Please read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the terms in [LICENSE](LICENSE).

---

<p align="center">
  Vibed with ❤️ for cybersecurity communities<br>
  <a href="https://github.com/ktalons/cybersec-discord-bot/issues">Report Bug</a> •
  <a href="https://github.com/ktalons/cybersec-discord-bot/issues">Request Feature</a>
</p>
