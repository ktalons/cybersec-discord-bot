# Database module for persistent storage of giveaways and rosters
# Uses SQLite with aiosqlite for async operations
import aiosqlite
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger("bot.database")

# Default database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "bot.db"


class Database:
    # Async SQLite database wrapper for bot persistence
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        # Create tables if they don't exist
        async with aiosqlite.connect(self.db_path) as db:
            # Giveaways table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS giveaways (
                    custom_id TEXT PRIMARY KEY,
                    prize TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    entries TEXT NOT NULL,
                    is_ended INTEGER DEFAULT 0
                )
            """)
            
            # Rosters table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS rosters (
                    custom_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    date_time TEXT NOT NULL,
                    description TEXT NOT NULL,
                    roster_limit INTEGER,
                    thumbnail TEXT,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    participants TEXT NOT NULL
                )
            """)
            
            await db.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    # === GIVEAWAY OPERATIONS ===
    
    async def save_giveaway(
        self,
        custom_id: str,
        prize: str,
        end_time: datetime,
        channel_id: int,
        message_id: int,
        entries: set,
        is_ended: bool = False
    ):
        # Save or update a giveaway
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO giveaways 
                    (custom_id, prize, end_time, channel_id, message_id, entries, is_ended)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    custom_id,
                    prize,
                    end_time.isoformat(),
                    channel_id,
                    message_id,
                    json.dumps(list(entries)),
                    1 if is_ended else 0
                ))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to save giveaway {custom_id}: {e}")
    
    async def load_giveaways(self) -> List[Dict[str, Any]]:
        # Load all active giveaways
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM giveaways WHERE is_ended = 0"
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [
                        {
                            "custom_id": row["custom_id"],
                            "prize": row["prize"],
                            "end_time": datetime.fromisoformat(row["end_time"]),
                            "channel_id": row["channel_id"],
                            "message_id": row["message_id"],
                            "entries": set(json.loads(row["entries"])),
                            "is_ended": bool(row["is_ended"])
                        }
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"Failed to load giveaways: {e}")
            return []
    
    async def delete_giveaway(self, custom_id: str):
        # Delete a giveaway from the database
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM giveaways WHERE custom_id = ?", (custom_id,))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to delete giveaway {custom_id}: {e}")
    
    # === ROSTER OPERATIONS ===
    
    async def save_roster(
        self,
        custom_id: str,
        title: str,
        date_time: str,
        description: str,
        channel_id: int,
        message_id: int,
        participants: Dict[int, tuple[str, str]],
        roster_limit: Optional[int] = None,
        thumbnail: Optional[str] = None
    ):
        # Save or update a roster
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Convert participants dict to JSON-serializable format
                participants_data = {
                    str(user_id): {"username": username, "skill_level": skill}
                    for user_id, (username, skill) in participants.items()
                }
                
                await db.execute("""
                    INSERT OR REPLACE INTO rosters 
                    (custom_id, title, date_time, description, roster_limit, thumbnail,
                     channel_id, message_id, participants)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    custom_id,
                    title,
                    date_time,
                    description,
                    roster_limit,
                    thumbnail,
                    channel_id,
                    message_id,
                    json.dumps(participants_data)
                ))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to save roster {custom_id}: {e}")
    
    async def load_rosters(self) -> List[Dict[str, Any]]:
        # Load all active rosters
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM rosters") as cursor:
                    rows = await cursor.fetchall()
                    result = []
                    for row in rows:
                        # Convert participants back to dict format
                        participants_data = json.loads(row["participants"])
                        participants = {
                            int(user_id): (data["username"], data["skill_level"])
                            for user_id, data in participants_data.items()
                        }
                        
                        result.append({
                            "custom_id": row["custom_id"],
                            "title": row["title"],
                            "date_time": row["date_time"],
                            "description": row["description"],
                            "roster_limit": row["roster_limit"],
                            "thumbnail": row["thumbnail"],
                            "channel_id": row["channel_id"],
                            "message_id": row["message_id"],
                            "participants": participants
                        })
                    return result
        except Exception as e:
            logger.error(f"Failed to load rosters: {e}")
            return []
    
    async def delete_roster(self, custom_id: str):
        # Delete a roster from the database
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM rosters WHERE custom_id = ?", (custom_id,))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to delete roster {custom_id}: {e}")
