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
        bot_language: str = "es",
    ) -> None:
        """Save or update user and mark as logged in."""
        now = self._now()
        data = {
            "telegram_id": telegram_id,
            "cv_user_id": cv_user_id,
            "email": email,
            "username": username,
            "cv_token": "active",  # Marker to indicate logged in
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

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username (for checking availability)."""
        result = await asyncio.to_thread(
            lambda: self.client.table("users").select("cv_user_id, username").eq("username", username).execute()
        )
        return result.data[0] if result.data else None

    async def delete_user(self, telegram_id: int) -> None:
        """Delete user and all associated data."""
        await asyncio.to_thread(
            lambda: self.client.table("user_preferences").delete().eq("telegram_id", telegram_id).execute()
        )
        await asyncio.to_thread(
            lambda: self.client.table("users").delete().eq("telegram_id", telegram_id).execute()
        )

    async def logout_user(self, telegram_id: int, cv_user_id: str) -> None:
        """Log out user by clearing token, current language, and active sentences."""
        now = self._now()
        
        # Clear all active sentences for this user
        await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .delete()
                .eq("cv_user_id", cv_user_id)
                .eq("status", "active")
                .execute()
        )
        
        # Clear user session
        await asyncio.to_thread(
            lambda: self.client.table("users").update({
                "cv_token": None,
                "current_language": None,
                "updated_at": now,
            }).eq("telegram_id", telegram_id).execute()
        )

    async def set_current_language(self, telegram_id: int, language: str) -> None:
        """Set the current recording language for a user."""
        now = self._now()
        await asyncio.to_thread(
            lambda: self.client.table("users").update({
                "current_language": language,
                "updated_at": now,
            }).eq("telegram_id", telegram_id).execute()
        )

    async def update_user_demographics(
        self,
        telegram_id: int,
        age: Optional[str],
        gender: Optional[str],
    ) -> None:
        """Update user's demographic info (age and gender)."""
        now = self._now()
        await asyncio.to_thread(
            lambda: self.client.table("users").update({
                "age": age,
                "gender": gender,
                "updated_at": now,
            }).eq("telegram_id", telegram_id).execute()
        )

    # ==========================================
    # Bot language operations
    # ==========================================

    async def get_bot_language(self, telegram_id: int) -> str:
        """Get bot interface language for a user."""
        result = await asyncio.to_thread(
            lambda: self.client.table("users").select("bot_language").eq("telegram_id", telegram_id).execute()
        )
        if result.data:
            return result.data[0]["bot_language"]
        
        result = await asyncio.to_thread(
            lambda: self.client.table("user_preferences").select("bot_language").eq("telegram_id", telegram_id).execute()
        )
        if result.data:
            return result.data[0]["bot_language"]
        
        return "es"  # Default to Spanish

    async def set_bot_language(self, telegram_id: int, language: str) -> None:
        """Set bot interface language for a user."""
        now = self._now()
        
        user = await self.get_user(telegram_id)
        
        if user:
            await asyncio.to_thread(
                lambda: self.client.table("users").update({
                    "bot_language": language,
                    "updated_at": now
                }).eq("telegram_id", telegram_id).execute()
            )
        else:
            data = {
                "telegram_id": telegram_id,
                "bot_language": language,
                "updated_at": now,
            }
            await asyncio.to_thread(
                lambda: self.client.table("user_preferences").upsert(data, on_conflict="telegram_id").execute()
            )

    # ==========================================
    # Sentence operations
    # ==========================================

    async def save_sentences(self, cv_user_id: str, language: str, sentences: list[dict]) -> list[dict]:
        """Save new sentences. Deletes ALL old active sentences first (across all languages)."""
        now = self._now()
        
        # Delete ALL active sentences for this user (starting fresh session)
        await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .delete()
                .eq("cv_user_id", cv_user_id)
                .eq("status", "active")
                .execute()
        )
        
        # Insert new sentences
        data = [
            {
                "cv_user_id": cv_user_id,
                "language": language,
                "sentence_number": i,
                "text_id": sentence["id"],
                "text": sentence["text"],
                "hash": sentence["hash"],
                "status": "active",
                "created_at": now,
            }
            for i, sentence in enumerate(sentences, start=1)
        ]
        if data:
            result = await asyncio.to_thread(
                lambda: self.client.table("sentences").insert(data).execute()
            )
            return result.data
        return []

    async def get_sentence_by_number(self, cv_user_id: str, language: str, sentence_number: int) -> Optional[dict]:
        """Get an active sentence by number."""
        result = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("*")
                .eq("cv_user_id", cv_user_id)
                .eq("language", language)
                .eq("sentence_number", sentence_number)
                .eq("status", "active")
                .execute()
        )
        return result.data[0] if result.data else None

    async def get_sentence_by_id(self, sentence_id: int) -> Optional[dict]:
        """Get a sentence by its ID."""
        result = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("*")
                .eq("id", sentence_id)
                .execute()
        )
        return result.data[0] if result.data else None

    async def get_all_sentences(self, cv_user_id: str, language: str) -> list[dict]:
        """Get all active sentences for a CV user in a language."""
        result = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("*")
                .eq("cv_user_id", cv_user_id)
                .eq("language", language)
                .eq("status", "active")
                .order("sentence_number")
                .execute()
        )
        return result.data

    async def get_sentence_count(self, cv_user_id: str, language: str, status: str = None) -> int:
        """Get count of sentences. If status is None, count all sentences."""
        query = self.client.table("sentences") \
            .select("id", count="exact") \
            .eq("cv_user_id", cv_user_id) \
            .eq("language", language)
        
        if status:
            query = query.eq("status", status)
        
        result = await asyncio.to_thread(lambda: query.execute())
        return result.count or 0

    async def get_seen_sentence_ids(self, cv_user_id: str, language: str) -> set[str]:
        """Get sentence IDs that have been uploaded or skipped (for deduplication)."""
        result = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("text_id")
                .eq("cv_user_id", cv_user_id)
                .eq("language", language)
                .in_("status", ["uploaded", "skipped"])
                .execute()
        )
        return {row["text_id"] for row in result.data}

    async def mark_sentence_uploaded(self, sentence_id: int) -> None:
        """Mark a sentence as uploaded."""
        await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .update({"status": "uploaded"})
                .eq("id", sentence_id)
                .execute()
        )

    async def mark_sentence_skipped(self, sentence_id: int) -> None:
        """Mark a sentence as skipped."""
        await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .update({"status": "skipped"})
                .eq("id", sentence_id)
                .execute()
        )

    # ==========================================
    # Recording operations
    # ==========================================

    async def save_recording(self, sentence_id: int, file_id: str) -> None:
        """Save a recording for a sentence."""
        now = self._now()
        data = {
            "sentence_id": sentence_id,
            "file_id": file_id,
            "status": "pending",
            "created_at": now,
        }
        await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .upsert(data, on_conflict="sentence_id")
                .execute()
        )

    async def get_recording(self, sentence_id: int) -> Optional[dict]:
        """Get recording for a sentence."""
        result = await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .select("*")
                .eq("sentence_id", sentence_id)
                .execute()
        )
        return result.data[0] if result.data else None

    async def get_pending_recordings(self, cv_user_id: str, language: str) -> list[dict]:
        """Get all pending recordings for active sentences."""
        sentences = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("*")
                .eq("cv_user_id", cv_user_id)
                .eq("language", language)
                .eq("status", "active")
                .order("sentence_number")
                .execute()
        )
        
        if not sentences.data:
            return []
        
        sentence_ids = [s["id"] for s in sentences.data]
        recordings = await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .select("*")
                .in_("sentence_id", sentence_ids)
                .eq("status", "pending")
                .execute()
        )
        
        recording_map = {r["sentence_id"]: r for r in recordings.data}
        result = []
        for s in sentences.data:
            r = recording_map.get(s["id"])
            if r:
                result.append({
                    **r,
                    "sentence_number": s["sentence_number"],
                    "text_id": s["text_id"],
                    "text": s["text"],
                    "hash": s["hash"],
                })
        return result

    async def get_failed_recordings(self, cv_user_id: str, language: str) -> list[dict]:
        """Get all failed recordings for active sentences."""
        sentences = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("*")
                .eq("cv_user_id", cv_user_id)
                .eq("language", language)
                .eq("status", "active")
                .order("sentence_number")
                .execute()
        )
        
        if not sentences.data:
            return []
        
        sentence_ids = [s["id"] for s in sentences.data]
        recordings = await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .select("*")
                .in_("sentence_id", sentence_ids)
                .eq("status", "failed")
                .execute()
        )
        
        recording_map = {r["sentence_id"]: r for r in recordings.data}
        result = []
        for s in sentences.data:
            r = recording_map.get(s["id"])
            if r:
                result.append({
                    **r,
                    "sentence_number": s["sentence_number"],
                    "text_id": s["text_id"],
                    "text": s["text"],
                    "hash": s["hash"],
                })
        return result

    async def update_recording_status(
        self,
        sentence_id: int,
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
                .eq("sentence_id", sentence_id)
                .execute()
        )

    async def get_recording_stats(self, cv_user_id: str, language: str) -> dict:
        """Get comprehensive stats for all sentences in this language."""
        # Get all sentences grouped by status
        sentences = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("id, status")
                .eq("cv_user_id", cv_user_id)
                .eq("language", language)
                .execute()
        )
        
        stats = {
            "total": len(sentences.data),
            "active": 0,      # Sentences waiting to be recorded
            "uploaded": 0,    # Sentences successfully uploaded
            "skipped": 0,     # Sentences skipped by user
            "pending": 0,     # Recordings waiting to upload
            "failed": 0,      # Recordings that failed
        }
        
        if not sentences.data:
            return stats
        
        # Count by sentence status
        active_ids = []
        for s in sentences.data:
            if s["status"] == "active":
                stats["active"] += 1
                active_ids.append(s["id"])
            elif s["status"] == "uploaded":
                stats["uploaded"] += 1
            elif s["status"] == "skipped":
                stats["skipped"] += 1
        
        # Get pending/failed recordings for active sentences
        if active_ids:
            recordings = await asyncio.to_thread(
                lambda: self.client.table("recordings")
                    .select("status")
                    .in_("sentence_id", active_ids)
                    .execute()
            )
            
            for row in recordings.data:
                if row["status"] == "pending":
                    stats["pending"] += 1
                elif row["status"] == "failed":
                    stats["failed"] += 1
        
        return stats

    async def get_all_recordings_with_sentences(self, cv_user_id: str, language: str) -> list[dict]:
        """Get all active sentences with their recording status."""
        sentences = await asyncio.to_thread(
            lambda: self.client.table("sentences")
                .select("*")
                .eq("cv_user_id", cv_user_id)
                .eq("language", language)
                .eq("status", "active")
                .order("sentence_number")
                .execute()
        )
        
        if not sentences.data:
            return []
        
        sentence_ids = [s["id"] for s in sentences.data]
        recordings = await asyncio.to_thread(
            lambda: self.client.table("recordings")
                .select("*")
                .in_("sentence_id", sentence_ids)
                .execute()
        )
        
        recording_map = {r["sentence_id"]: r for r in recordings.data}
        result = []
        for s in sentences.data:
            r = recording_map.get(s["id"])
            result.append({
                "sentence_id": s["id"],
                "sentence_number": s["sentence_number"],
                "text_id": s["text_id"],
                "text": s["text"],
                "hash": s["hash"],
                "recording": r,
            })
        return result
