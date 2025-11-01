# Logging and Error Handling

## Overview
The bot now has comprehensive error handling and status logging throughout all operations.

## Log Format
```
2025-11-01 02:30:15 | INFO     | bot | 🚀 Bot is ready and operational!
```

Format: `timestamp | level | logger_name | message`

## Startup Logging

### What You'll See on Startup:
```
========================================
Cybersecurity Discord Bot Starting...
Start time: 2025-11-01 02:30:15
========================================
Loading configuration...
✅ Configuration loaded successfully
Guild IDs configured: [123456789]
Initializing bot...
Connecting to Discord...
========================================
Starting bot setup...
========================================
Loading cog: VerificationCog...
✅ Successfully loaded VerificationCog
Loading cog: GiveawayCog...
GiveawayCog initialized
✅ Successfully loaded GiveawayCog
...
Cog loading complete: 5 loaded, 0 failed
========================================
✅ Bot logged in as BotName (ID: 123456789)
Connected to 2 guild(s)
========================================
  - Guild Name 1 (ID: 123456789, Members: 150)
  - Guild Name 2 (ID: 987654321, Members: 200)
Starting command sync...
Guild-specific sync for 1 guild(s)
✅ Synced 8 command(s) to guild 123456789
========================================
🚀 Bot is ready and operational!
========================================
```

## Runtime Logging

### Giveaways
- Creating giveaway: `Creating giveaway: Prize Name (duration: 60m, ID: giveaway_123)`
- Successful creation: `✅ Giveaway 'Prize Name' started successfully (ID: giveaway_123)`
- Restoring from DB: `Restoring 2 giveaways from database`
- Entry added: Automatically saved to database
- Giveaway ended: Cleanup and winner selection logged

### Rosters
- Creating roster: `Creating roster (ID: roster_123) by User#1234`
- Successful creation: `✅ Roster 'Event Name' created successfully (ID: roster_123)`
- Restoring from DB: `Restoring 3 rosters from database`
- Participant changes: Database saves logged
- Refresh task: Message validation every 2 minutes

### Command Sync
- Per-guild sync: `✅ Synced 8 command(s) to guild 123456789`
- Global sync: `✅ Globally synced 8 command(s)`
- Failures: `❌ Failed to sync guild 123456789: [error details]`

### Guild Events
- Bot joins server: `🎉 Joined new guild: Server Name (ID: 123456789, Members: 100)`
- Bot removed: `👋 Removed from guild: Server Name (ID: 123456789)`

## Error Handling

### Cog-Level Error Handling
Each cog has a `cog_app_command_error` handler that:
1. Logs the full error with stack trace
2. Sends user-friendly error message to Discord
3. Handles both response and followup scenarios

### Global Error Handling
- Event errors: Caught and logged with full context
- Command errors: Logged with command name and details
- Fatal errors: Logged at CRITICAL level with full trace

### Database Errors
All database operations have try-except blocks:
- Save failures: Logged but don't crash the bot
- Load failures: Return empty list, bot continues
- Delete failures: Logged as warnings

### Message Recovery
When message references become invalid:
1. Log the issue: `Invalid message reference for roster roster_123, will try to recover`
2. Attempt to fetch using stored channel/message IDs
3. If successful: `Recovered roster message reference for roster_123`
4. If failed: Skip update, log warning

## Log Levels

- **INFO**: Normal operations, status updates, successful actions
- **WARNING**: Recoverable issues, missing optional data
- **ERROR**: Failed operations that don't crash the bot
- **CRITICAL**: Fatal errors that cause bot shutdown

## Debugging Tips

### Check Cog Loading
Look for:
```
✅ Successfully loaded GiveawayCog
❌ Failed to load CalendarCog: [error]
```

### Check Command Sync
Look for:
```
✅ Synced 8 command(s) to guild 123456789
```
If commands don't appear, check for sync errors.

### Check Database Restoration
Look for:
```
Restoring 2 giveaways from database
✅ Restored giveaway giveaway_123 with 5 entries
```

### Check for Webhook Errors
Should no longer see:
```
❌ ERROR:bot.giveaway:Failed to update giveaway embed: 401 Unauthorized
```

If you do, the message reference recovery will kick in.

## Monitoring Production

### Key Log Patterns to Monitor:

**Healthy Operation:**
```
✅ Successfully loaded [cog]
✅ Synced [n] command(s)
🚀 Bot is ready and operational!
```

**Warning Signs:**
```
❌ Failed to load [cog]
❌ Failed to sync guild
Failed to recover roster message
Invalid message reference
```

**Critical Issues:**
```
❌ Fatal error: [error]
Error in event '[event_name]'
Command error in [command]
```

### Docker Logs
View logs in Docker:
```bash
docker logs cybersec-bot -f --tail 100
```

### Log Filtering
```bash
# Only errors
docker logs cybersec-bot 2>&1 | grep "ERROR\|CRITICAL"

# Only giveaways
docker logs cybersec-bot 2>&1 | grep "giveaway"

# Only rosters
docker logs cybersec-bot 2>&1 | grep "roster"
```

## Graceful Shutdown
When stopping the bot (Ctrl+C or SIGTERM):
```
👋 Bot shutdown requested by user
Unloading GiveawayCog...
Unloading RosterCog...
```

## Error Messages to Users
When something goes wrong, users see:
```
❌ An error occurred: [brief description]
```

Full details are logged for admins to review.
