# Bot Improvements - Persistent Storage

## Overview
Added SQLite database persistence to giveaways and rosters so they survive bot restarts and can run for extended periods (days/weeks).

## Changes Made

### 1. New Database Module (`src/utils/database.py`)
- Async SQLite wrapper using `aiosqlite`
- Tables for giveaways and rosters
- Handles saving, loading, and deleting data
- Stores entries/participants as JSON

### 2. Giveaway Improvements (`src/cogs/giveaway.py`)
**Features:**
- ✅ Giveaways persist across bot restarts
- ✅ Automatically restores active giveaways on startup
- ✅ Re-attaches button views to existing messages
- ✅ Saves entries to database on each new entry
- ✅ Cleans up database when giveaway ends
- ✅ Improved error handling for missing messages/channels

**How it works:**
- When a giveaway is created, it's saved to the database
- On bot restart, the cog fetches all active giveaways from the database
- Recreates views and re-attaches them to the original Discord messages
- Countdown and winner selection continue as normal

### 3. Roster Improvements (`src/cogs/roster.py`)
**Features:**
- ✅ Rosters persist across bot restarts
- ✅ Automatically restores active rosters on startup
- ✅ Re-attaches button views to existing messages
- ✅ Saves participant data to database on add/remove
- ✅ New `/roster_delete` admin command to remove rosters
- ✅ Improved error handling for webhook token errors
- ✅ Message reference recovery mechanism

**How it works:**
- When a roster is created, it's saved to the database
- On bot restart, the cog fetches all rosters from the database
- Recreates views and re-attaches them to the original Discord messages
- Participants can continue joining/leaving as normal

### 4. Requirements Update
Added `aiosqlite>=0.19.0` to requirements.txt

## Installation

1. Update dependencies:
```bash
.venv/bin/pip install -r requirements.txt
```

2. The database will be created automatically at `data/bot.db` on first run

## New Admin Commands

- `/roster_delete <message_id>` - Delete a roster by its message ID

## Database Location

The SQLite database is stored at: `data/bot.db`

This file is created automatically on first run. You can back it up to preserve giveaway/roster data.

## Error Handling Improvements

1. **Webhook Token Errors**: Fixed the 401 errors that occurred after bot restarts
2. **Message Recovery**: Both cogs now attempt to recover message references using stored IDs
3. **Cleanup**: Automatically removes database entries for deleted messages
4. **Logging**: Better logging for debugging startup restoration and errors

## Testing Recommendations

1. Create a test giveaway with a short duration (e.g., 5 minutes)
2. Create a test roster
3. Restart the bot
4. Verify that:
   - Giveaway buttons still work
   - Roster buttons still work
   - Countdown continues
   - New entries/participants are saved

## Notes

- Giveaways and rosters now support **multi-day or multi-week durations**
- The bot will maintain state even through restarts, deployments, or crashes
- Database is lightweight (SQLite) and requires no external services
- All data is stored locally in the `data/` directory
