"""Database initialization and migrations."""

import aiosqlite
import os
from pathlib import Path
from database.models import (
    CREATE_PLAYERS_TABLE,
    CREATE_ATTEMPTS_TABLE,
    CREATE_TONGUE_TWISTERS_TABLE,
    CREATE_SESSIONS_TABLE,
    CREATE_DAILY_CHALLENGES_TABLE,
    CREATE_DAILY_CHALLENGE_ATTEMPTS_TABLE,
    CREATE_ACHIEVEMENTS_TABLE,
    CREATE_PLAYER_ACHIEVEMENTS_TABLE,
    CREATE_DUELS_TABLE,
    CREATE_TOURNAMENTS_TABLE,
    CREATE_INDEXES
)
from data.tongue_twisters import TWISTERS
from dotenv import load_dotenv

load_dotenv()


async def initialize_database():
    """Initialize database with all tables and seed data."""
    db_path = os.getenv("DATABASE_PATH", "./data/twister.db")
    
    # Create data directory if it doesn't exist
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(db_path) as db:
        # Create all tables
        await db.execute(CREATE_PLAYERS_TABLE)
        await db.execute(CREATE_ATTEMPTS_TABLE)
        await db.execute(CREATE_TONGUE_TWISTERS_TABLE)
        await db.execute(CREATE_SESSIONS_TABLE)
        await db.execute(CREATE_DAILY_CHALLENGES_TABLE)
        await db.execute(CREATE_DAILY_CHALLENGE_ATTEMPTS_TABLE)
        await db.execute(CREATE_ACHIEVEMENTS_TABLE)
        await db.execute(CREATE_PLAYER_ACHIEVEMENTS_TABLE)
        await db.execute(CREATE_DUELS_TABLE)
        await db.execute(CREATE_TOURNAMENTS_TABLE)
        
        # Create indexes
        for index_sql in CREATE_INDEXES:
            await db.execute(index_sql)
        
        # Seed tongue twisters if not already present
        for twister in TWISTERS:
            await db.execute(
                """
                INSERT OR IGNORE INTO tongue_twisters 
                (twister_id, text, difficulty, word_count, focus_sounds, is_official)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    twister['id'],
                    twister['text'],
                    twister['difficulty'],
                    twister['word_count'],
                    twister['focus_sounds'],
                    True
                )
            )
        
        # Seed achievements
        achievements = [
            ('perfect_score', 'Perfect Score', 'Achieve 100% accuracy', '💯'),
            ('speed_demon', 'Speed Demon', 'Complete a twister in under 2 seconds', '⚡'),
            ('persistent', 'Persistent', 'Complete 100 attempts', '🔥'),
            ('master', 'Master', 'Beat all insane difficulty twisters', '👑'),
            ('champion', 'Champion', 'Reach #1 on the leaderboard', '🏆'),
        ]
        
        for achievement_id, name, description, icon in achievements:
            await db.execute(
                """
                INSERT OR IGNORE INTO achievements (achievement_id, name, description, icon)
                VALUES (?, ?, ?, ?)
                """,
                (achievement_id, name, description, icon)
            )
        
        await db.commit()
        print(f"Database initialized at {db_path}")

