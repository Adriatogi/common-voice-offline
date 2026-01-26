"""Supabase database operations for the bot."""

import os
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)


class Database:
    """Supabase database operations."""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        self.client: Client = create_client(url, key)
    
    async def init(self) -> None:
        """Initialize database connection. Tables are managed via Supabase SQL Editor."""
        logger.info("Database initialized (Supabase)")

    def _now(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    # ==========================================
    # User operations
    # ==========================================

    async def save_user(
        self,
        telegram_id: int,
        cv_user_id: str,
        email: str,
        username: str,
        bot_language: str = "en",
    ) -> None:
        """Save or update user."""
        now = self._now()
        data = {
            "telegram_id": telegram_id,
            "cv_user_id": cv_user_id,
            "email": email,
            "username": username,
            "bot_language": bot_language,
            "created_at": now,
            "updated_at": now,
        }
        await asyncio.to_thread(
            lambda: self.client.table("users").upsert(data, on_conflict="telegram_id").execute()
        )

    async def get_user(self, telegram_id: int) -> Optional[dict]:
        """Get user by telegram ID."""
        result = await asyncio.to_thread(
            lambda: self.client.table("users").select("*").eq("telegram_id", telegram_id).execute()
        )
        return result.data[0] if result.data else None

    async def delete_user(self, telegram_id: int) -> None:
        """Delete user and all associated data (cascades via foreign keys)."""
        # Delete from tables without cascade first
        await asyncio.to_thread(
            lambda: self.client.table("user_preferences").delete().eq("telegram_id", telegram_id).execute()
        )
        # Delete user (cascades to sessions, sentences, recordings, seen_sentences)
        await asyncio.to_thread(
            lambda: self.client.table("users").delete().eq("telegram_id", telegram_id).execute()
        )

    # ==========================================
    # Bot language operations
    # ==========================================

    async def get_bot_language(self, telegram_id: int) -> str:
        """Get bot interface language for a user."""
        # First check if user is registered
        result = await asyncio.to_thread(
            lambda: self.client.table("users").select("bot_language").eq("telegram_id", telegram_id).execute()
        )
        if result.data:
            return result.data[0]["bot_language"]
        
        # Check preferences table for non-registered users
        result = await asyncio.to_thread(
            lambda: self.client.table("user_preferences").select("bot_language").eq("telegram_id", telegram_id).execute()
        )
        if result.data:
            return result.data[0]["bot_language"]
        
        return "en"  # Default to English

    async def set_bot_language(self, telegram_id: int, language: str) -> None:
        """Set bot interface language for a user."""
        now = self._now()
        
        # Check if user is registered
        user = await self.get_user(telegram_id)
        
        if user:
            await asyncio.to_thread(
                lambda: self.client.table("users").update({
                    "bot_language": language,
                    "updated_at": now
                }).eq("telegram_id", telegram_id).execute()
            )
        else:
            # Store in preferences table for non-registered users
            data = {
                "telegram_id": telegram_id,
                "bot_language": language,
                "updated_at": now,
            }
            await asyncio.to_thread(
                lambda: self.client.table("user_preferences").upsert(data, on_conflict="telegram_id").execute()
            )

    # ==========================================
    # Session operations
    # ==========================================

    async def save_session(self, telegram_id: int, language: str) -> None:
        """Save or update session."""
        now = self._now()
        data = {
            "telegram_id": telegram_id,
            "language": language,
            "created_at": now,
        }
        await asyncio.to_thread(
            lambda: self.client.table("sessions").upsert(data, on_conflict="telegram_id").execute()
        )

    async def get_session(self, telegram_id: int) -> Optional[dict]:
        """Get session by telegram ID."""
        result = await asyncio.to_thread(
            lambda: self.client.table("sessions").select("*").eq("telegram_id", telegram_id).execute()
        )
        return result.data[0] if result.data else None

    async def delete_session(self, telegram_id: int) -> None:
        """Delete session and associated sentences/recordings."""
        await asyncio.to_thread(
            lambda: self.client.table("recordings").delete().eq("telegram_id", telegram_id).execute()
        )
        await asyncio.to_thread(
            lambda: self.client.table("sentences").delete().eq("telegram_id", telegram_id).execute()
        )
        await asyncio.to_thread(
            lambda: self.client.table("sessions").delete().eq("telegram_id", telegram_id).execute()
        )

    # ==========================================
    # Sentence operations
    # ==========================================

    async def save_sentences(self, telegram_id: int, language: str, sentences: list[dict]) -> None:
        """Save sentences for a user. Clears existing sentences and recordings first."""
        now = self._now()
        
        # Clear existing sentences and recordings (new session = fresh start)
        await asyncio.to_thread(
            lambda: self.client.table("recordings").delete().eq("telegram_id", telegram_id).execute()
        )
        await asyncio.to_thread(
            lambda: self.client.table("sentences").delete().eq("telegram_id", telegram_id).execute()
        )
        
        # Insert new sentences
        data = [
            {
                "telegram_id": telegram_id,
                "sentence_number": i,
                "text_id": sentence["id"],
                "text": sentence["text"],
                "hash": sentence["hash"],
                "created_at": now,
            }
            for i, sentence in enumerate(sentences, start=1)
        ]
        if data:
            await asyncio.to_thread(
                lambda: self.client.table("sentences").insert(data).execute()
            )

    async def get_sentence(self, telegram_id: int, sentence_number: int) -> Optional[dict]:
        """Get a specific sentence by number."""
        result = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("*")
                .eq("telegram_id", telegram_id)
                .eq("sentence_number", sentence_number)
                .execute()
        )
        return result.data[0] if result.data else None

    async def get_all_sentences(self, telegram_id: int) -> list[dict]:
        """Get all sentences for a user."""
        result = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("*")
                .eq("telegram_id", telegram_id)
                .order("sentence_number")
                .execute()
        )
        return result.data

    async def get_sentence_count(self, telegram_id: int) -> int:
        """Get count of sentences for a user."""
        result = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("id", count="exact")
                .eq("telegram_id", telegram_id)
                .execute()
        )
        return result.count or 0

    async def get_seen_sentence_ids(self, telegram_id: int, language: str) -> set[str]:
        """Get all sentence IDs this user has uploaded for a language."""
        result = await asyncio.to_thread(
            lambda: self.client.table("seen_sentences")
                .select("sentence_id")
                .eq("telegram_id", telegram_id)
                .eq("language", language)
                .execute()
        )
        return {row["sentence_id"] for row in result.data}

    async def mark_sentence_uploaded(self, telegram_id: int, language: str, sentence_id: str) -> None:
        """Mark a sentence as uploaded (seen) so it won't be assigned again."""
        now = self._now()
        data = {
            "telegram_id": telegram_id,
            "language": language,
            "sentence_id": sentence_id,
            "created_at": now,
        }
        # Use upsert with on_conflict to handle duplicates
        await asyncio.to_thread(
            lambda: self.client.table("seen_sentences")
                .upsert(data, on_conflict="telegram_id,language,sentence_id")
                .execute()
        )

    # ==========================================
    # Recording operations
    # ==========================================

    async def save_recording(
        self, telegram_id: int, sentence_number: int, file_id: str
    ) -> None:
        """Save a recording file_id."""
        now = self._now()
        data = {
            "telegram_id": telegram_id,
            "sentence_number": sentence_number,
            "file_id": file_id,
            "status": "pending",
            "created_at": now,
        }
        await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .upsert(data, on_conflict="telegram_id,sentence_number")
                .execute()
        )

    async def mark_recording_skipped(self, telegram_id: int, sentence_number: int) -> None:
        """Mark a sentence as skipped (no recording needed)."""
        now = self._now()
        data = {
            "telegram_id": telegram_id,
            "sentence_number": sentence_number,
            "file_id": "",
            "status": "skipped",
            "created_at": now,
        }
        await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .upsert(data, on_conflict="telegram_id,sentence_number")
                .execute()
        )

    async def get_recording(self, telegram_id: int, sentence_number: int) -> Optional[dict]:
        """Get a specific recording."""
        result = await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .select("*")
                .eq("telegram_id", telegram_id)
                .eq("sentence_number", sentence_number)
                .execute()
        )
        return result.data[0] if result.data else None

    async def get_pending_recordings(self, telegram_id: int) -> list[dict]:
        """Get all pending recordings for a user with sentence data."""
        # Get pending recordings
        recordings = await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .select("*")
                .eq("telegram_id", telegram_id)
                .eq("status", "pending")
                .order("sentence_number")
                .execute()
        )
        
        if not recordings.data:
            return []
        
        # Get associated sentences
        sentence_numbers = [r["sentence_number"] for r in recordings.data]
        sentences = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("*")
                .eq("telegram_id", telegram_id)
                .in_("sentence_number", sentence_numbers)
                .execute()
        )
        
        # Merge data
        sentence_map = {s["sentence_number"]: s for s in sentences.data}
        result = []
        for r in recordings.data:
            s = sentence_map.get(r["sentence_number"], {})
            result.append({
                **r,
                "text_id": s.get("text_id"),
                "text": s.get("text"),
                "hash": s.get("hash"),
            })
        return result

    async def update_recording_status(
        self,
        telegram_id: int,
        sentence_number: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Update recording status."""
        now = self._now()
        data = {"status": status}
        
        if status == "uploaded":
            data["error_message"] = None
            data["uploaded_at"] = now
        else:
            data["error_message"] = error_message
        
        await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .update(data)
                .eq("telegram_id", telegram_id)
                .eq("sentence_number", sentence_number)
                .execute()
        )

    async def get_recording_stats(self, telegram_id: int) -> dict:
        """Get recording statistics for a user."""
        result = await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .select("status")
                .eq("telegram_id", telegram_id)
                .execute()
        )
        
        stats = {"total": 0, "pending": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        for row in result.data:
            status = row["status"]
            if status in stats:
                stats[status] += 1
            stats["total"] += 1
        
        return stats

    async def get_failed_recordings(self, telegram_id: int) -> list[dict]:
        """Get all failed recordings for a user with sentence data."""
        # Get failed recordings
        recordings = await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .select("*")
                .eq("telegram_id", telegram_id)
                .eq("status", "failed")
                .order("sentence_number")
                .execute()
        )
        
        if not recordings.data:
            return []
        
        # Get associated sentences
        sentence_numbers = [r["sentence_number"] for r in recordings.data]
        sentences = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("*")
                .eq("telegram_id", telegram_id)
                .in_("sentence_number", sentence_numbers)
                .execute()
        )
        
        # Merge data
        sentence_map = {s["sentence_number"]: s for s in sentences.data}
        result = []
        for r in recordings.data:
            s = sentence_map.get(r["sentence_number"], {})
            result.append({
                **r,
                "text_id": s.get("text_id"),
                "text": s.get("text"),
                "hash": s.get("hash"),
            })
        return result
