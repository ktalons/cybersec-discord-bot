# 🐳 Docker Deployment Guide

Complete guide for deploying the Cybersec Discord Bot using Docker and Docker Compose.

---

## Why Docker?

✅ **Consistent environment** - Same setup everywhere  
✅ **Easy updates** - `docker-compose pull && docker-compose up -d`  
✅ **Isolated dependencies** - No conflicts with host system  
✅ **Simple rollback** - Tag and revert to previous versions  
✅ **Production-ready** - Auto-restart, log management

---

## Quick Start

### 1. Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- Discord bot token with **Server Members Intent** enabled
- Gmail App Password (for email verification)

### 2. Setup

```bash
# Clone repository
git clone https://github.com/ktalons/cybersec-discord-bot.git
cd cybersec-discord-bot

# Configure environment
cp .env.example .env
nano .env  # Edit with your values

# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f bot
```

---

## Volume Persistence

### ⚠️ Critical: Database Persistence

The bot stores giveaways and rosters in a SQLite database. **Without a persistent volume, your data will be lost on restart.**

### Default Configuration (Good for Development)

The default `docker-compose.yml` doesn't include volume mapping. The database will be created inside the container at `/app/data/bot.db` but **will be lost** when the container is removed.

### Recommended: Add Persistent Volume

Update your `docker-compose.yml`:

```yaml
services:
  bot:
    build: .
    image: cybersec-discord-bot:latest
    container_name: cybersec-bot
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./data:/app/data  # ← Add this line
```

This maps `./data` on your host to `/app/data` in the container.

### Configure Database Path

Add to your `.env` file:

```env
DATABASE_PATH=/app/data/bot.db
```

### Create Data Directory

```bash
# Create directory with proper permissions
mkdir -p data
chmod 755 data

# If running Docker as non-root (recommended)
# Make sure the appuser (UID 10001) can write to it
sudo chown 10001:10001 data

# Or make it world-writable (less secure but simpler)
chmod 777 data
```

---

## Complete docker-compose.yml Example

```yaml
services:
  bot:
    build: .
    image: cybersec-discord-bot:latest
    container_name: cybersec-bot
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      # Database persistence
      - ./data:/app/data
      
      # Optional: Mount custom config
      # - ./custom-config.env:/app/.env:ro
    
    # Optional: Resource limits
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          memory: 256M
    
    # Optional: Logging configuration
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Environment Variables

### Required

```env
DISCORD_TOKEN=your_bot_token_here
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
```

### Database Configuration

```env
# Default: /app/data/bot.db (recommended for Docker)
DATABASE_PATH=/app/data/bot.db
```

If you don't set this, it defaults to `./data/bot.db` relative to the project root, which may not work correctly in Docker.

### Optional Features

```env
VERIFY_DOMAIN=arizona.edu
VERIFY_ROLE_ID=123456789
GUILD_IDS=123456789,987654321        # Instant command sync
CALENDAR_ICS_URL=https://calendar.google.com/calendar/ical/...
CALENDAR_CHANNEL_ID=123456789
CTF_CHANNEL_ID=123456789
CTFTIME_EVENTS_WINDOW_DAYS=7
```

---

## Common Commands

### Start the Bot

```bash
docker-compose up -d
```

### View Logs

```bash
# Follow all logs
docker-compose logs -f bot

# Last 100 lines
docker-compose logs --tail 100 bot

# Search for errors
docker-compose logs bot | grep -i error
```

### Restart the Bot

```bash
docker-compose restart bot
```

### Update and Restart

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Stop the Bot

```bash
docker-compose down
```

### Access Container Shell

```bash
docker-compose exec bot bash
```

### View Database

```bash
# From host
sqlite3 data/bot.db "SELECT * FROM giveaways;"

# From container
docker-compose exec bot sqlite3 /app/data/bot.db "SELECT * FROM giveaways;"
```

---

## Troubleshooting

### Database Permission Issues

**Symptom:** Logs show `Permission denied: '/app/data'` and fallback to `/tmp`

**Solution:**

```bash
# Option 1: Fix permissions
mkdir -p data
sudo chown 10001:10001 data

# Option 2: Make directory writable
chmod 777 data

# Option 3: Run container as root (not recommended)
# Add to docker-compose.yml under 'bot':
user: "0:0"
```

### Database in /tmp Warning

If you see:

```
⚠️  WARNING: Falling back to temporary directory for database
⚠️  WARNING: Database will be lost on container restart!
```

This means the bot couldn't write to `/app/data`. See solutions above.

### Data Lost After Restart

**Cause:** No volume mounted

**Solution:** Add volume mapping to `docker-compose.yml`:

```yaml
volumes:
  - ./data:/app/data
```

### Container Won't Start

```bash
# Check logs
docker-compose logs bot

# Common issues:
# - Missing DISCORD_TOKEN in .env
# - Invalid .env format
# - Port conflicts (shouldn't happen with this bot)
```

### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Clean up unused images/containers
docker system prune -a

# Check database size
du -h data/bot.db
```

---

## Production Deployment

### Server Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Clone repository
git clone https://github.com/ktalons/cybersec-discord-bot.git
cd cybersec-discord-bot

# Setup environment
cp .env.example .env
nano .env  # Add your tokens

# Create data directory
mkdir -p data
chmod 755 data
sudo chown 10001:10001 data
```

### Deploy

```bash
docker-compose up -d
```

### Monitor

```bash
# Watch logs
docker-compose logs -f bot

# Check status
docker-compose ps

# Check resource usage
docker stats cybersec-bot
```

### Auto-start on Boot

Docker Compose already configures `restart: unless-stopped`, so the container will auto-start on server reboot.

### Backup Database

```bash
# Manual backup
cp data/bot.db data/bot.db.backup.$(date +%Y%m%d)

# Automated daily backup (add to crontab)
0 2 * * * cd /path/to/bot && cp data/bot.db data/backups/bot.db.$(date +\%Y\%m\%d)
```

### Updates

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Verify startup
docker-compose logs -f bot
```

---

## Security Best Practices

### ✅ Do's

- ✅ Use `.env` file for secrets (never commit it)
- ✅ Enable Docker's user namespacing
- ✅ Keep base images updated: `docker-compose build --pull`
- ✅ Use resource limits (see complete example above)
- ✅ Regular backups of `data/bot.db`
- ✅ Monitor logs for security issues

### ❌ Don'ts

- ❌ Don't run as root unless necessary
- ❌ Don't expose unnecessary ports
- ❌ Don't commit `.env` file to version control
- ❌ Don't use `latest` tag in production (tag specific versions)
- ❌ Don't skip regular updates

---

## Database Persistence Deep Dive

### Why Persistence Matters

The bot stores:
- **Giveaway entries** - User IDs, prizes, end times
- **Roster participants** - CTF team members, skill levels
- **Message IDs** - For button interactions after restart

Without persistence:
- ❌ Active giveaways lose all entries
- ❌ Roster buttons stop working
- ❌ Users must re-enter after bot restart

### Temporary Directory Fallback

The bot includes a fallback to `/tmp` if it can't write to the configured database path. This prevents startup failure but:

⚠️ **Risks:**
- Data lost on container restart
- `/tmp` may have limited space
- Not suitable for production

✅ **Benefits:**
- Bot starts even with permission issues
- Allows testing without proper setup
- Clear warnings in logs

### Production Setup

For production, **always use a persistent volume**:

```yaml
volumes:
  - ./data:/app/data
```

And set in `.env`:

```env
DATABASE_PATH=/app/data/bot.db
```

---

## Advanced Configuration

### Multiple Bots

Run multiple instances for different servers:

```bash
# Bot 1
cd cybersec-bot-server1
docker-compose -p bot1 up -d

# Bot 2
cd cybersec-bot-server2
docker-compose -p bot2 up -d
```

### Custom Dockerfile

For specific Python versions or additional dependencies:

```dockerfile
FROM python:3.12-slim
# ... rest of Dockerfile
```

### Health Checks

Add to `docker-compose.yml`:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

## Getting Help

### Check Logs First

```bash
docker-compose logs bot | tail -100
```

Look for:
- ✅ `Bot is ready and operational!`
- ❌ `ERROR` or `CRITICAL` messages
- ⚠️ `WARNING: Falling back to temporary directory`

### Common Log Messages

| Message | Meaning | Action |
|---------|---------|--------|
| `Database directory ensured` | ✅ Working correctly | None |
| `Failed to create database directory` | ❌ Permission issue | Fix data/ permissions |
| `Using temporary database location` | ⚠️ Fallback active | Add volume mount |
| `Bot is ready and operational!` | ✅ Startup successful | None |

### More Resources

- **[README.md](../README.md)** - Quick start and features
- **[DEPLOY.md](DEPLOY.md)** - General deployment guide
- **[LOGGING.md](LOGGING.md)** - Log interpretation
- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - Technical details

---

**Questions?** Open an issue on [GitHub](https://github.com/ktalons/cybersec-discord-bot/issues)
