"""Status and management command handlers."""

import os
import re
import asyncio

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.config import Config
from bot.database.db import Database
from bot.services.cv_api import CVAPIClient, CVAPIError
from bot.i18n import t
from bot.handlers.registry import handler


def parse_sentence_numbers(text: str, max_num: int) -> list[int]:
    """Parse sentence numbers from text like '1,3,5' or '1-5' or '1 3 5'."""
    numbers = set()
    
    # Handle ranges like "1-5"
    for match in re.finditer(r'(\d+)-(\d+)', text):
        start, end = int(match.group(1)), int(match.group(2))
        for n in range(start, min(end + 1, max_num + 1)):
            if 1 <= n <= max_num:
                numbers.add(n)
    
    # Handle individual numbers
    for match in re.finditer(r'\b(\d+)\b', re.sub(r'\d+-\d+', '', text)):
        n = int(match.group(1))
        if 1 <= n <= max_num:
            numbers.add(n)
    
    return sorted(numbers)


def _get_api_client(config: Config) -> CVAPIClient:
    """Create API client with admin credentials from environment."""
    client_id = os.getenv("CV_CLIENT_ID")
    client_secret = os.getenv("CV_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("CV_CLIENT_ID and CV_CLIENT_SECRET must be set in .env")
    
    return CVAPIClient(
        client_id=client_id,
        client_secret=client_secret,
        base_url=config.cv_api_base_url,
        token_expiry_buffer_seconds=config.token_expiry_buffer_seconds,
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current status and recording progress."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    user = await db.get_user(telegram_id)
    
    if not user:
        await update.message.reply_text(t(lang, "status_not_registered"))
        return
    
    # Check if logged out
    if not user.get("cv_token"):
        await update.message.reply_text(t(lang, "status_logged_out"), parse_mode="Markdown")
        return
    
    cv_user_id = user["cv_user_id"]
    current_language = user.get("current_language")
    
    # Get stats if user has a current language
    if current_language:
        stats = await db.get_recording_stats(cv_user_id, current_language)
    else:
        stats = {"total": 0, "active": 0, "uploaded": 0, "skipped": 0, "pending": 0, "failed": 0}
    
    # Build status message
    lines = [
        t(lang, "status_header"),
        t(lang, "status_user", username=user['username']),
        t(lang, "status_user_id", user_id=cv_user_id),
        t(lang, "status_email", email=user['email']),
    ]
    
    if current_language:
        lang_name = config.supported_languages.get(current_language, current_language)
        lines.append(t(lang, "status_language", language=lang_name))
        lines.append(t(lang, "status_sentences", count=stats['total']))
        lines.append("")
        lines.append(t(lang, "status_progress_header", language=lang_name))
        
        lines.append(t(lang, "status_progress_remaining", remaining=stats['active']))
        lines.append(t(lang, "status_progress_pending", pending=stats['pending']))
        lines.append(t(lang, "status_progress_uploaded", uploaded=stats['uploaded']))
        lines.append(t(lang, "status_progress_skipped", skipped=stats['skipped']))
        if stats['failed'] > 0:
            lines.append(t(lang, "status_progress_failed", failed=stats['failed']))
        
        if stats['pending'] > 0:
            lines.append(t(lang, "status_upload_hint"))
        if stats['active'] > 0:
            lines.append(t(lang, "status_remaining_hint"))
    else:
        lines.append(t(lang, "status_no_session"))
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def sentences_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show sentences for the current session."""
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    user = await db.get_user(telegram_id)
    if not user or not user.get("current_language"):
        await update.message.reply_text(t(lang, "sentences_no_session"))
        return
    
    cv_user_id = user["cv_user_id"]
    current_language = user["current_language"]
    
    # Get all active sentences with their recording status
    sentence_data = await db.get_all_recordings_with_sentences(cv_user_id, current_language)
    if not sentence_data:
        # Check if there are any sentences at all (uploaded/skipped)
        total = await db.get_sentence_count(cv_user_id, current_language)
        if total > 0:
            await update.message.reply_text(t(lang, "sentences_all_done"))
        else:
            await update.message.reply_text(t(lang, "sentences_none"))
        return
    
    # Check for filter argument
    args = update.message.text.split()[1:]
    show_only_left = args and args[0].lower() in ("left", "remaining", "todo")
    
    # Build recording status map
    recording_status = {}
    sentences = []
    for item in sentence_data:
        sentences.append(item)
        if item["recording"]:
            recording_status[item["sentence_number"]] = item["recording"]["status"]
    
    # Filter sentences if requested
    if show_only_left:
        sentences = [s for s in sentences if recording_status.get(s["sentence_number"]) is None]
        if not sentences:
            await update.message.reply_text(t(lang, "sentences_all_done"))
            return
        header = t(lang, "sentences_left_header", count=len(sentences))
    else:
        header = t(lang, "sentences_header", count=len(sentences))
    
    await update.message.reply_text(header, parse_mode="Markdown")
    
    # Send sentences in batches
    batch_size = 10
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i + batch_size]
        lines = []
        for s in batch:
            num = s["sentence_number"]
            status = recording_status.get(num)
            if status == "uploaded":
                emoji = "✅"
            elif status == "pending":
                emoji = "🟡"
            elif status == "failed":
                emoji = "❌"
            elif status == "skipped":
                emoji = "⏭️"
            else:
                emoji = "⬜"
            lines.append(f"{emoji} **#{num}** {s['text']}")
        
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")


async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger upload of pending recordings."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    user = await db.get_user(telegram_id)
    if not user:
        await update.message.reply_text(t(lang, "upload_not_registered"))
        return
    
    if not user.get("current_language"):
        await update.message.reply_text(t(lang, "upload_no_session"))
        return
    
    cv_user_id = user["cv_user_id"]
    current_language = user["current_language"]
    
    # Get pending and failed recordings
    pending = await db.get_pending_recordings(cv_user_id, current_language)
    failed = await db.get_failed_recordings(cv_user_id, current_language)
    all_recordings = pending + failed
    
    if not all_recordings:
        await update.message.reply_text(t(lang, "upload_nothing"))
        return
    
    await update.message.reply_text(
        t(lang, "upload_starting", count=len(all_recordings))
    )
    
    api_client = _get_api_client(config)
    
    success_count = 0
    fail_count = 0
    
    try:
        for rec in all_recordings:
            try:
                audio_file = await context.bot.get_file(rec["file_id"])
                audio_bytes = await audio_file.download_as_bytearray()
                
                await api_client.upload_audio(
                    audio_data=bytes(audio_bytes),
                    user_id=cv_user_id,
                    dataset_code=current_language,
                    text_id=rec["text_id"],
                    text=rec["text"],
                    text_hash=rec["hash"],
                )
                
                await db.update_recording_status(rec["sentence_id"], "uploaded")
                await db.mark_sentence_uploaded(rec["sentence_id"])
                
                success_count += 1
                
            except CVAPIError as e:
                await db.update_recording_status(
                    rec["sentence_id"], 
                    "failed",
                    error_message=str(e.detail or e.message)
                )
                fail_count += 1
            except Exception as e:
                await db.update_recording_status(
                    rec["sentence_id"],
                    "failed",
                    error_message=str(e)
                )
                fail_count += 1
    finally:
        await api_client.close()
    
    if fail_count == 0:
        await update.message.reply_text(
            t(lang, "upload_success", count=success_count)
        )
    else:
        await update.message.reply_text(
            t(lang, "upload_partial", success=success_count, failed=fail_count)
        )


async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Skip sentences so they won't be assigned again."""
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    user = await db.get_user(telegram_id)
    if not user or not user.get("current_language"):
        await update.message.reply_text(t(lang, "skip_no_session"))
        return
    
    cv_user_id = user["cv_user_id"]
    current_language = user["current_language"]
    
    total_sentences = await db.get_sentence_count(cv_user_id, current_language)
    if total_sentences == 0:
        await update.message.reply_text(t(lang, "skip_no_sentences"))
        return
    
    args = update.message.text.split()[1:]
    if not args:
        await update.message.reply_text(
            t(lang, "skip_usage", total=total_sentences),
            parse_mode="Markdown",
        )
        return
    
    numbers = parse_sentence_numbers(" ".join(args), total_sentences)
    if not numbers:
        await update.message.reply_text(
            t(lang, "skip_invalid", total=total_sentences)
        )
        return
    
    skipped = []
    for num in numbers:
        sentence = await db.get_sentence_by_number(cv_user_id, current_language, num)
        if sentence:
            await db.mark_sentence_skipped(sentence["id"])
            skipped.append(num)
    
    if skipped:
        await update.message.reply_text(
            t(lang, "skip_success", numbers=", ".join(f"#{n}" for n in skipped))
        )
    else:
        await update.message.reply_text(t(lang, "skip_none_found"))


async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log out and clear session data (keeps user record for history)."""
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    user = await db.get_user(telegram_id)
    
    if not user:
        await update.message.reply_text(t(lang, "logout_not_registered"))
        return
    
    if not user.get("cv_token"):
        await update.message.reply_text(t(lang, "logout_already_logged_out"))
        return
    
    # Check for pending uploads
    cv_user_id = user["cv_user_id"]
    current_language = user.get("current_language")
    
    if current_language:
        stats = await db.get_recording_stats(cv_user_id, current_language)
        if stats["pending"] > 0:
            if not context.user_data.get("logout_confirmed"):
                await update.message.reply_text(
                    t(lang, "logout_pending_warning", count=stats['pending'])
                )
                context.user_data["logout_confirmed"] = True
                return
    
    await db.logout_user(telegram_id, cv_user_id)
    context.user_data.clear()
    
    await update.message.reply_text(t(lang, "logout_success"))


async def resend_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resend unrecorded sentences as individual messages for offline recording."""
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    user = await db.get_user(telegram_id)
    if not user or not user.get("current_language"):
        await update.message.reply_text(t(lang, "resend_no_session"))
        return
    
    cv_user_id = user["cv_user_id"]
    current_language = user["current_language"]
    
    sentence_data = await db.get_all_recordings_with_sentences(cv_user_id, current_language)
    if not sentence_data:
        await update.message.reply_text(t(lang, "resend_no_sentences"))
        return
    
    remaining = [s for s in sentence_data if not s["recording"]]
    
    if not remaining:
        await update.message.reply_text(t(lang, "resend_all_done"))
        return
    
    await update.message.reply_text(
        t(lang, "resend_starting", count=len(remaining))
    )
    
    for s in remaining:
        await update.message.reply_text(
            f"**#{s['sentence_number']}** {s['text']}",
            parse_mode="Markdown",
        )
        await asyncio.sleep(0.1)
    
    await update.message.reply_text(
        t(lang, "resend_done"),
        parse_mode="Markdown",
    )


# Register handlers
handler(priority=40)(CommandHandler("status", status_command))
handler(priority=41)(CommandHandler("sentences", sentences_command))
handler(priority=42)(CommandHandler("upload", upload_command))
handler(priority=43)(CommandHandler("skip", skip_command))
handler(priority=45)(CommandHandler("resend", resend_command))
handler(priority=46)(CommandHandler("logout", logout_command))
