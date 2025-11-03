# Deployment Guide

## Summary of Changes

✅ **Database persistence** - SQLite storage for giveaways/rosters  
✅ **Multi-day support** - Giveaways and rosters survive restarts  
✅ **Network resilience** - Survives temporary DNS/connection failures  
✅ **Fixed webhook errors** - No more 401 errors after 15 minutes  
✅ **Comprehensive logging** - Detailed status updates and error tracking  
✅ **Error handling** - Graceful failure recovery with automatic retries  
✅ **Database cleanup** - Automatic cleanup of old entries (60+ days)  
✅ **Fixed /sync command** - Now works correctly  
✅ **New admin commands** - `/roster_delete`

## Ubuntu Server Deployment

### Option 1: Docker (Recommended)

1. **SSH to your server:**
   ```bash
   ssh user@your-server
   ```

2. **Navigate to bot directory:**
   ```bash
   cd /path/to/cybersec-discord-bot
   ```

3. **Pull changes:**
   ```bash
   git pull
   ```

4. **Rebuild and restart container:**
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

5. **View logs:**
   ```bash
   docker logs cybersec-bot -f --tail 100
   ```

### Option 2: Direct Python

1. **Pull changes:**
   ```bash
   cd /path/to/bot
   git pull
   ```

2. **Update dependencies:**
   ```bash
   .venv/bin/pip install -r requirements.txt
   ```

3. **Restart bot service:**
   ```bash
   # If using systemd
   sudo systemctl restart cybersec-bot
   
   # If using screen/tmux
   # Stop the old session and start new one
   .venv/bin/python src/main.py
   ```

4. **Check logs:**
   ```bash
   # Systemd
   journalctl -u cybersec-bot -f
   
   # Or check log file if configured
   tail -f /path/to/bot.log
   ```

## Post-Deployment Checklist

### 1. Verify Startup
Look for these in logs:
- ✅ `Bot logged in as [name]`
- ✅ `Successfully loaded [5 cogs]`
- ✅ `Synced [n] command(s)`
- ✅ `Bot is ready and operational!`

### 2. Test Database
```bash
# Check database was created
ls -lh data/bot.db
```

### 3. Test Commands
In Discord:
- ✅ `/giveaway_start` - Create a test giveaway
- ✅ `/roster_start` - Create a test roster
- ✅ `/sync` - Should work without errors

### 4. Test Persistence
1. Create a giveaway/roster
2. Restart the bot
3. Verify buttons still work
4. Check logs for "Restoring X giveaways from database"

### 5. Monitor for Errors
Watch logs for the first 10-15 minutes:
```bash
docker logs cybersec-bot -f 2>&1 | grep "ERROR\|CRITICAL\|❌"
```

**Expected behavior:**
- ✅ No webhook token errors (401)
- ✅ No task crashes from network errors
- ✅ Giveaways/rosters restore successfully
- ✅ Database cleanup task scheduled

## Rollback Plan

If something goes wrong:

1. **Stop the bot:**
   ```bash
   docker-compose down
   # or
   sudo systemctl stop cybersec-bot
   ```

2. **Rollback code:**
   ```bash
   git log --oneline  # Find previous commit
   git checkout <commit-hash>
   ```

3. **Restart:**
   ```bash
   docker-compose up -d
   # or
   sudo systemctl start cybersec-bot
   ```

4. **Report issue:**
   Save logs and error messages for debugging.


## Maintenance

### Backup Database
```bash
# Local copy
cp data/bot.db data/bot.db.backup

# Download from server
scp user@server:/path/to/bot/data/bot.db ./bot-backup-$(date +%Y%m%d).db
```

### Clean Up Old Rosters
Use `/roster_delete <message_id>` to remove old rosters manually.

Giveaways auto-delete when they end.

### Log Rotation
If using Docker, logs will grow. Consider log rotation:
```bash
# View log size
docker logs cybersec-bot 2>&1 | wc -l

# Clear logs
docker-compose down
docker-compose up -d
```

## Need Help?

Check these files:
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Feature details
- [LOGGING.md](LOGGING.md) - Log interpretation guide
- [../README.md](../README.md) - Original setup instructions


Enjoy your improved bot! 🎉
