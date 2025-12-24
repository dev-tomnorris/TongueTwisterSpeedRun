"""Database operations manager."""

import aiosqlite
import os
import uuid
from typing import Optional, List, Dict
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()


class DatabaseManager:
    """Manages all database operations."""
    
    def __init__(self):
        self.db_path = os.getenv("DATABASE_PATH", "./data/twister.db")
    
    async def _get_connection(self) -> aiosqlite.Connection:
        """Get database connection."""
        return await aiosqlite.connect(self.db_path)
    
    # Player operations
    async def get_or_create_player(self, user_id: str, username: str) -> Dict:
        """Get or create a player record."""
        async with self._get_connection() as db:
            # Try to get existing player
            async with db.execute(
                "SELECT * FROM players WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'user_id': row[0],
                        'username': row[1],
                        'total_attempts': row[2],
                        'successful_attempts': row[3],
                        'total_score': row[4],
                        'best_score': row[5],
                        'best_score_twister_id': row[6],
                        'fastest_time': row[7],
                        'created_at': row[8],
                        'last_played': row[9],
                    }
            
            # Create new player
            await db.execute(
                """
                INSERT INTO players (user_id, username, last_played)
                VALUES (?, ?, ?)
                """,
                (user_id, username, datetime.utcnow())
            )
            await db.commit()
            
            # Return new player
            return await self.get_or_create_player(user_id, username)
    
    async def update_player_stats(
        self,
        user_id: str,
        accuracy: float,
        time_seconds: float,
        score: int,
        twister_id: int,
        is_successful: bool
    ):
        """Update player statistics after an attempt."""
        async with self._get_connection() as db:
            # Update player stats
            await db.execute(
                """
                UPDATE players
                SET total_attempts = total_attempts + 1,
                    successful_attempts = successful_attempts + ?,
                    total_score = total_score + ?,
                    best_score = MAX(best_score, ?),
                    fastest_time = CASE
                        WHEN fastest_time IS NULL OR ? < fastest_time THEN ?
                        ELSE fastest_time
                    END,
                    last_played = ?
                WHERE user_id = ?
                """,
                (
                    1 if is_successful else 0,
                    score,
                    score,
                    time_seconds,
                    time_seconds,
                    datetime.utcnow(),
                    user_id
                )
            )
            
            # Update best_score_twister_id if this is a new best
            await db.execute(
                """
                UPDATE players
                SET best_score_twister_id = ?
                WHERE user_id = ? AND best_score = ?
                """,
                (twister_id, user_id, score)
            )
            
            await db.commit()
    
    async def get_player_stats(self, user_id: str) -> Optional[Dict]:
        """Get comprehensive player statistics."""
        async with self._get_connection() as db:
            async with db.execute(
                """
                SELECT * FROM players WHERE user_id = ?
                """,
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                # Get attempts by difficulty
                async with db.execute(
                    """
                    SELECT difficulty, 
                           COUNT(*) as attempts,
                           AVG(accuracy) as avg_accuracy,
                           MAX(score) as best_score
                    FROM attempts
                    WHERE user_id = ?
                    GROUP BY difficulty
                    """,
                    (user_id,)
                ) as cursor2:
                    difficulty_stats = {}
                    async for row2 in cursor2:
                        difficulty_stats[row2[0]] = {
                            'attempts': row2[1],
                            'avg_accuracy': row2[2] or 0.0,
                            'best_score': row2[3] or 0
                        }
                
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'total_attempts': row[2],
                    'successful_attempts': row[3],
                    'total_score': row[4],
                    'best_score': row[5],
                    'best_score_twister_id': row[6],
                    'fastest_time': row[7],
                    'created_at': row[8],
                    'last_played': row[9],
                    'difficulty_stats': difficulty_stats
                }
    
    # Attempt operations
    async def save_attempt(
        self,
        user_id: str,
        twister_id: int,
        spoken_text: str,
        accuracy: float,
        time_seconds: float,
        score: int,
        difficulty: str,
        session_type: str,
        session_id: Optional[str] = None
    ) -> str:
        """Save an attempt to the database."""
        attempt_id = str(uuid.uuid4())
        
        async with self._get_connection() as db:
            await db.execute(
                """
                INSERT INTO attempts 
                (attempt_id, user_id, twister_id, spoken_text, accuracy, 
                 time_seconds, score, difficulty, session_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id, user_id, twister_id, spoken_text,
                    accuracy, time_seconds, score, difficulty, session_type
                )
            )
            
            # Update twister stats
            await db.execute(
                """
                UPDATE tongue_twisters
                SET times_attempted = times_attempted + 1,
                    average_accuracy = (
                        SELECT AVG(accuracy) 
                        FROM attempts 
                        WHERE twister_id = ?
                    )
                WHERE twister_id = ?
                """,
                (twister_id, twister_id)
            )
            
            await db.commit()
        
        return attempt_id
    
    # Session operations
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        server_id: str,
        channel_id: str,
        session_type: str
    ):
        """Create a new session record."""
        async with self._get_connection() as db:
            await db.execute(
                """
                INSERT INTO sessions 
                (session_id, user_id, server_id, channel_id, session_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, user_id, server_id, channel_id, session_type)
            )
            await db.commit()
    
    async def end_session(
        self,
        session_id: str,
        total_attempts: int,
        total_score: int
    ):
        """End a session and update stats."""
        async with self._get_connection() as db:
            await db.execute(
                """
                UPDATE sessions
                SET ended_at = ?,
                    total_attempts = ?,
                    total_score = ?
                WHERE session_id = ?
                """,
                (datetime.utcnow(), total_attempts, total_score, session_id)
            )
            await db.commit()
    
    # Leaderboard operations
    async def get_leaderboard(
        self,
        scope: str = 'server',
        server_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 15
    ) -> List[Dict]:
        """Get leaderboard rankings."""
        async with self._get_connection() as db:
            if difficulty:
                # Leaderboard by difficulty
                query = """
                    SELECT 
                        p.user_id,
                        p.username,
                        SUM(a.score) as total_score,
                        COUNT(*) as attempts,
                        ROUND(AVG(a.accuracy), 1) as avg_accuracy,
                        MAX(a.score) as best_score
                    FROM players p
                    INNER JOIN attempts a ON p.user_id = a.user_id
                    WHERE a.difficulty = ?
                """
                params = [difficulty]
                
                if scope == 'server' and server_id:
                    query += " AND EXISTS (SELECT 1 FROM sessions s WHERE s.user_id = p.user_id AND s.server_id = ?)"
                    params.append(server_id)
                
                query += """
                    GROUP BY p.user_id, p.username
                    ORDER BY total_score DESC
                    LIMIT ?
                """
                params.append(limit)
            else:
                # Overall leaderboard
                query = """
                    SELECT 
                        user_id,
                        username,
                        total_score,
                        total_attempts,
                        ROUND(CAST(successful_attempts AS REAL) / total_attempts * 100, 1) as success_rate,
                        best_score
                    FROM players
                    WHERE total_attempts > 0
                """
                params = []
                
                if scope == 'server' and server_id:
                    query += " AND EXISTS (SELECT 1 FROM sessions s WHERE s.user_id = players.user_id AND s.server_id = ?)"
                    params.append(server_id)
                
                query += " ORDER BY total_score DESC LIMIT ?"
                params.append(limit)
            
            async with db.execute(query, params) as cursor:
                results = []
                async for row in cursor:
                    if difficulty:
                        results.append({
                            'user_id': row[0],
                            'username': row[1],
                            'total_score': row[2],
                            'attempts': row[3],
                            'avg_accuracy': row[4],
                            'best_score': row[5]
                        })
                    else:
                        results.append({
                            'user_id': row[0],
                            'username': row[1],
                            'total_score': row[2],
                            'attempts': row[3],
                            'success_rate': row[4],
                            'best_score': row[5]
                        })
                
                return results
    
    async def get_player_rank(
        self,
        user_id: str,
        scope: str = 'server',
        server_id: Optional[str] = None
    ) -> Optional[int]:
        """Get a player's rank on the leaderboard."""
        leaderboard = await self.get_leaderboard(scope, server_id, limit=1000)
        for i, entry in enumerate(leaderboard, 1):
            if entry['user_id'] == user_id:
                return i
        return None


# Global database manager instance
db_manager = DatabaseManager()

