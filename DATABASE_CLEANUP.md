# Database Cleanup

## Overview
Automatic database cleanup to prevent storage bloat from old giveaway entries.

## How It Works

### Cleanup Schedule
- **Frequency:** Every 24 hours
- **Retention:** 60 days
- **Target:** Ended giveaways only

### What Gets Cleaned
✅ **Removed:**
- Giveaway entries that ended more than 60 days ago
- Only affects completed/ended giveaways

❌ **Not Removed:**
- Active giveaways (regardless of age)
- Roster entries (manual cleanup with `/roster_delete`)
- Any giveaway that hasn't ended yet

### Technical Details

**Location:** `src/utils/database.py`
```python
async def cleanup_old_entries(self, days: int = 60):
    # Deletes giveaways where is_ended = 1 AND end_time < 60 days ago
```

**Task:** `src/cogs/giveaway.py`
```python
@tasks.loop(hours=24)
async def database_cleanup_task(self):
    # Runs daily cleanup
```

### Monitoring

Check logs for cleanup activity:
```bash
# Look for cleanup messages
docker logs cybersec-bot | grep "cleanup"

# Expected output when entries are removed:
# INFO | bot.database | Cleaned up 5 old giveaway(s) from database
# INFO | bot.giveaway | Database cleanup: removed 5 old entries
```

No output means no old entries to clean (which is normal).

### Manual Cleanup

If you need to clean up rosters manually:
1. Get the roster message ID (right-click message → Copy ID)
2. Run: `/roster_delete <message_id>`

### Storage Benefits

- Prevents unlimited database growth
- Keeps `data/bot.db` file size reasonable
- Maintains performance over long-term operation
- Historical data is preserved for 60 days

### Adjusting Retention Period

To change the 60-day retention:

1. Edit `src/cogs/giveaway.py`:
```python
deleted = await self.db.cleanup_old_entries(days=90)  # Change to 90 days
```

2. Restart the bot

### Backup Recommendation

Before major cleanups, backup the database:
```bash
cp data/bot.db data/bot.db.backup-$(date +%Y%m%d)
```

### FAQ

**Q: Will this delete active giveaways?**  
A: No, only giveaways that have already ended.

**Q: What about giveaways that lasted more than 60 days?**  
A: They're kept until 60 days **after** they end.

**Q: Can I disable cleanup?**  
A: Yes, comment out `self.database_cleanup_task.start()` in `src/cogs/giveaway.py`.

**Q: How much space does this save?**  
A: Depends on usage. Each giveaway entry is ~1KB. With 100 giveaways/year, you save ~100KB/year of bloat.

**Q: Is cleanup logged?**  
A: Yes, cleanup activity is logged at INFO level.
