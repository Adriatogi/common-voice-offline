"""SQLite database operations for the bot."""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)


# Schema definition: table -> list of (column_name, column_definition)
# Used for both initial creation and migrations
SCHEMA = {
    "users": [
        ("telegram_id", "INTEGER PRIMARY KEY"),
        ("cv_user_id", "TEXT NOT NULL"),
        ("email", "TEXT NOT NULL"),
        ("username", "TEXT NOT NULL"),
        ("bot_language", "TEXT NOT NULL DEFAULT 'en'"),
        ("created_at", "TEXT NOT NULL"),
        ("updated_at", "TEXT NOT NULL"),
    ],
    "sessions": [
        ("telegram_id", "INTEGER PRIMARY KEY"),
        ("language", "TEXT NOT NULL"),
        ("created_at", "TEXT NOT NULL"),
    ],
    "sentences": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("telegram_id", "INTEGER NOT NULL"),
        ("sentence_number", "INTEGER NOT NULL"),
        ("text_id", "TEXT NOT NULL"),
        ("text", "TEXT NOT NULL"),
        ("hash", "TEXT NOT NULL"),
        ("created_at", "TEXT NOT NULL"),
    ],
    "recordings": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("telegram_id", "INTEGER NOT NULL"),
        ("sentence_number", "INTEGER NOT NULL"),
        ("file_id", "TEXT NOT NULL"),
        ("status", "TEXT NOT NULL DEFAULT 'pending'"),
        ("error_message", "TEXT"),
        ("created_at", "TEXT NOT NULL"),
        ("uploaded_at", "TEXT"),
    ],
    "user_preferences": [
        ("telegram_id", "INTEGER PRIMARY KEY"),
        ("bot_language", "TEXT NOT NULL DEFAULT 'en'"),
        ("updated_at", "TEXT NOT NULL"),
    ],
    "seen_sentences": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("telegram_id", "INTEGER NOT NULL"),
        ("language", "TEXT NOT NULL"),
        ("sentence_id", "TEXT NOT NULL"),
        ("created_at", "TEXT NOT NULL"),
    ],
}


class Database:
    """Async SQLite database operations."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    async def _get_existing_columns(self, db, table_name: str) -> set[str]:
        """Get set of existing column names for a table."""
        async with db.execute(f"PRAGMA table_info({table_name})") as cursor:
            rows = await cursor.fetchall()
            return {row[1] for row in rows}  # row[1] is column name
    
    async def _table_exists(self, db, table_name: str) -> bool:
        """Check if a table exists."""
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        ) as cursor:
            return await cursor.fetchone() is not None
    
    async def _migrate_table(self, db, table_name: str, columns: list[tuple[str, str]]) -> None:
        """Add any missing columns to an existing table."""
        existing = await self._get_existing_columns(db, table_name)
        
        for col_name, col_def in columns:
            if col_name not in existing:
                # SQLite ADD COLUMN syntax is limited - can't add NOT NULL without default
                # So we strip NOT NULL if there's no DEFAULT
                safe_def = col_def
                if "NOT NULL" in col_def and "DEFAULT" not in col_def:
                    safe_def = col_def.replace("NOT NULL", "").strip()
                
                sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {safe_def}"
                logger.info(f"Migrating: {sql}")
                await db.execute(sql)
    
    async def init(self) -> None:
        """Initialize the database schema, migrating if needed."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            if not await self._table_exists(db, "users"):
                await db.execute("""
                    CREATE TABLE users (
                        telegram_id INTEGER PRIMARY KEY,
                        cv_user_id TEXT NOT NULL,
                        email TEXT NOT NULL,
                        username TEXT NOT NULL,
                        bot_language TEXT NOT NULL DEFAULT 'en',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                logger.info("Created table: users")
            else:
                await self._migrate_table(db, "users", SCHEMA["users"])

            # Sessions table
            if not await self._table_exists(db, "sessions"):
                await db.execute("""
                    CREATE TABLE sessions (
                        telegram_id INTEGER PRIMARY KEY,
                        language TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                    )
                """)
                logger.info("Created table: sessions")
            else:
                await self._migrate_table(db, "sessions", SCHEMA["sessions"])

            # Sentences table
            if not await self._table_exists(db, "sentences"):
                await db.execute("""
                    CREATE TABLE sentences (
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
                logger.info("Created table: sentences")
            else:
                await self._migrate_table(db, "sentences", SCHEMA["sentences"])

            # Recordings table
            if not await self._table_exists(db, "recordings"):
                await db.execute("""
                    CREATE TABLE recordings (
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
                logger.info("Created table: recordings")
            else:
                await self._migrate_table(db, "recordings", SCHEMA["recordings"])
            
            # User preferences table
            if not await self._table_exists(db, "user_preferences"):
                await db.execute("""
                    CREATE TABLE user_preferences (
                        telegram_id INTEGER PRIMARY KEY,
                        bot_language TEXT NOT NULL DEFAULT 'en',
                        updated_at TEXT NOT NULL
                    )
                """)
                logger.info("Created table: user_preferences")
            else:
                await self._migrate_table(db, "user_preferences", SCHEMA["user_preferences"])

            # Seen sentences table (tracks all sentences ever assigned to avoid duplicates)
            if not await self._table_exists(db, "seen_sentences"):
                await db.execute("""
                    CREATE TABLE seen_sentences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER NOT NULL,
                        language TEXT NOT NULL,
                        sentence_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (telegram_id) REFERENCES users (telegram_id),
                        UNIQUE (telegram_id, language, sentence_id)
                    )
                """)
                logger.info("Created table: seen_sentences")
            else:
                await self._migrate_table(db, "seen_sentences", SCHEMA["seen_sentences"])

            await db.commit()

    # User operations

    async def save_user(
        self,
        telegram_id: int,
        cv_user_id: str,
        email: str,
        username: str,
        bot_language: str = "en",
    ) -> None:
        """Save or update user."""
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (telegram_id, cv_user_id, email, username, bot_language, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    cv_user_id = excluded.cv_user_id,
                    email = excluded.email,
                    username = excluded.username,
                    bot_language = excluded.bot_language,
                    updated_at = excluded.updated_at
            """, (telegram_id, cv_user_id, email, username, bot_language, now, now))
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
            await db.execute("DELETE FROM seen_sentences WHERE telegram_id = ?", (telegram_id,))
            await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            await db.execute("DELETE FROM user_preferences WHERE telegram_id = ?", (telegram_id,))
            await db.commit()

    # Bot language operations

    async def get_bot_language(self, telegram_id: int) -> str:
        """Get bot interface language for a user."""
        async with aiosqlite.connect(self.db_path) as db:
            # First check if user is registered
            async with db.execute(
                "SELECT bot_language FROM users WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
            
            # Check preferences table for non-registered users
            async with db.execute(
                "SELECT bot_language FROM user_preferences WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
        
        return "en"  # Default to English

    async def set_bot_language(self, telegram_id: int, language: str) -> None:
        """Set bot interface language for a user."""
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            # Check if user is registered
            async with db.execute(
                "SELECT telegram_id FROM users WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                is_registered = await cursor.fetchone() is not None
            
            if is_registered:
                await db.execute(
                    "UPDATE users SET bot_language = ?, updated_at = ? WHERE telegram_id = ?",
                    (language, now, telegram_id)
                )
            else:
                # Store in preferences table for non-registered users
                await db.execute("""
                    INSERT INTO user_preferences (telegram_id, bot_language, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT (telegram_id) DO UPDATE SET
                        bot_language = excluded.bot_language,
                        updated_at = excluded.updated_at
                """, (telegram_id, language, now))
            
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

    async def save_sentences(self, telegram_id: int, language: str, sentences: list[dict]) -> None:
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
                """, (telegram_id, i, sentence["id"], sentence["text"], sentence["hash"], now))
            
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

    async def get_seen_sentence_ids(self, telegram_id: int, language: str) -> set[str]:
        """Get all sentence IDs this user has uploaded for a language."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT sentence_id FROM seen_sentences WHERE telegram_id = ? AND language = ?",
                (telegram_id, language)
            ) as cursor:
                rows = await cursor.fetchall()
                return {row[0] for row in rows}

    async def mark_sentence_uploaded(self, telegram_id: int, language: str, sentence_id: str) -> None:
        """Mark a sentence as uploaded (seen) so it won't be assigned again."""
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO seen_sentences (telegram_id, language, sentence_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (telegram_id, language, sentence_id, now))
            await db.commit()

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

    async def mark_recording_skipped(self, telegram_id: int, sentence_number: int) -> None:
        """Mark a sentence as skipped (no recording needed)."""
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO recordings (telegram_id, sentence_number, file_id, status, created_at)
                VALUES (?, ?, '', 'skipped', ?)
                ON CONFLICT (telegram_id, sentence_number) DO UPDATE SET
                    status = 'skipped',
                    error_message = NULL,
                    created_at = excluded.created_at
            """, (telegram_id, sentence_number, now))
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
            stats = {"total": 0, "pending": 0, "uploaded": 0, "failed": 0, "skipped": 0}
            
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
