"""SQLite database operations for the bot."""

from pathlib import Path
from datetime import datetime
from typing import Optional

import aiosqlite


class Database:
    """Async SQLite database operations."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    async def init(self) -> None:
        """Initialize the database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table - stores user info (no credentials - using admin token)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    cv_user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Sessions table - stores active language selection
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    telegram_id INTEGER PRIMARY KEY,
                    language TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
            """)

            # Sentences table - stores downloaded sentences
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sentences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    sentence_number INTEGER NOT NULL,
                    text_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id),
                    UNIQUE (telegram_id, sentence_number)
                )
            """)

            # Recordings table - stores file_id references
            await db.execute("""
                CREATE TABLE IF NOT EXISTS recordings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    sentence_number INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    uploaded_at TEXT,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id),
                    UNIQUE (telegram_id, sentence_number)
                )
            """)

            await db.commit()

    # User operations

    async def save_user(
        self,
        telegram_id: int,
        cv_user_id: str,
        email: str,
        username: str,
    ) -> None:
        """Save or update user."""
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (telegram_id, cv_user_id, email, username, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    cv_user_id = excluded.cv_user_id,
                    email = excluded.email,
                    username = excluded.username,
                    updated_at = excluded.updated_at
            """, (telegram_id, cv_user_id, email, username, now, now))
            await db.commit()

    async def get_user(self, telegram_id: int) -> Optional[dict]:
        """Get user by telegram ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def delete_user(self, telegram_id: int) -> None:
        """Delete user and all associated data."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM recordings WHERE telegram_id = ?", (telegram_id,))
            await db.execute("DELETE FROM sentences WHERE telegram_id = ?", (telegram_id,))
            await db.execute("DELETE FROM sessions WHERE telegram_id = ?", (telegram_id,))
            await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            await db.commit()

    # Session operations

    async def save_session(self, telegram_id: int, language: str) -> None:
        """Save or update session."""
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO sessions (telegram_id, language, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    language = excluded.language,
                    created_at = excluded.created_at
            """, (telegram_id, language, now))
            await db.commit()

    async def get_session(self, telegram_id: int) -> Optional[dict]:
        """Get session by telegram ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM sessions WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def delete_session(self, telegram_id: int) -> None:
        """Delete session and associated sentences/recordings."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM recordings WHERE telegram_id = ?", (telegram_id,))
            await db.execute("DELETE FROM sentences WHERE telegram_id = ?", (telegram_id,))
            await db.execute("DELETE FROM sessions WHERE telegram_id = ?", (telegram_id,))
            await db.commit()

    # Sentence operations

    async def save_sentences(self, telegram_id: int, sentences: list[dict]) -> None:
        """Save sentences for a user. Clears existing sentences first."""
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            # Clear existing sentences
            await db.execute("DELETE FROM sentences WHERE telegram_id = ?", (telegram_id,))
            
            # Insert new sentences
            for i, sentence in enumerate(sentences, start=1):
                await db.execute("""
                    INSERT INTO sentences (telegram_id, sentence_number, text_id, text, hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (telegram_id, i, sentence["textId"], sentence["text"], sentence["hash"], now))
            
            await db.commit()

    async def get_sentence(self, telegram_id: int, sentence_number: int) -> Optional[dict]:
        """Get a specific sentence by number."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM sentences 
                WHERE telegram_id = ? AND sentence_number = ?
            """, (telegram_id, sentence_number)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_sentences(self, telegram_id: int) -> list[dict]:
        """Get all sentences for a user."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM sentences 
                WHERE telegram_id = ? 
                ORDER BY sentence_number
            """, (telegram_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_sentence_count(self, telegram_id: int) -> int:
        """Get count of sentences for a user."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM sentences WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # Recording operations

    async def save_recording(
        self, telegram_id: int, sentence_number: int, file_id: str
    ) -> None:
        """Save a recording file_id."""
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO recordings (telegram_id, sentence_number, file_id, status, created_at)
                VALUES (?, ?, ?, 'pending', ?)
                ON CONFLICT (telegram_id, sentence_number) DO UPDATE SET
                    file_id = excluded.file_id,
                    status = 'pending',
                    error_message = NULL,
                    created_at = excluded.created_at,
                    uploaded_at = NULL
            """, (telegram_id, sentence_number, file_id, now))
            await db.commit()

    async def get_recording(self, telegram_id: int, sentence_number: int) -> Optional[dict]:
        """Get a specific recording."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM recordings 
                WHERE telegram_id = ? AND sentence_number = ?
            """, (telegram_id, sentence_number)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_pending_recordings(self, telegram_id: int) -> list[dict]:
        """Get all pending recordings for a user."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT r.*, s.text_id, s.text, s.hash
                FROM recordings r
                JOIN sentences s ON r.telegram_id = s.telegram_id 
                    AND r.sentence_number = s.sentence_number
                WHERE r.telegram_id = ? AND r.status = 'pending'
                ORDER BY r.sentence_number
            """, (telegram_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def update_recording_status(
        self,
        telegram_id: int,
        sentence_number: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Update recording status."""
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            if status == "uploaded":
                await db.execute("""
                    UPDATE recordings 
                    SET status = ?, error_message = NULL, uploaded_at = ?
                    WHERE telegram_id = ? AND sentence_number = ?
                """, (status, now, telegram_id, sentence_number))
            else:
                await db.execute("""
                    UPDATE recordings 
                    SET status = ?, error_message = ?
                    WHERE telegram_id = ? AND sentence_number = ?
                """, (status, error_message, telegram_id, sentence_number))
            await db.commit()

    async def get_recording_stats(self, telegram_id: int) -> dict:
        """Get recording statistics for a user."""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {"total": 0, "pending": 0, "uploaded": 0, "failed": 0}
            
            async with db.execute("""
                SELECT status, COUNT(*) as count 
                FROM recordings 
                WHERE telegram_id = ? 
                GROUP BY status
            """, (telegram_id,)) as cursor:
                async for row in cursor:
                    status, count = row
                    stats[status] = count
                    stats["total"] += count
            
            return stats

    async def get_failed_recordings(self, telegram_id: int) -> list[dict]:
        """Get all failed recordings for a user (for retry)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT r.*, s.text_id, s.text, s.hash
                FROM recordings r
                JOIN sentences s ON r.telegram_id = s.telegram_id 
                    AND r.sentence_number = s.sentence_number
                WHERE r.telegram_id = ? AND r.status = 'failed'
                ORDER BY r.sentence_number
            """, (telegram_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
