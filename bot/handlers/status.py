"""Status and management command handlers."""

import os
import re

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
    
    session = await db.get_session(telegram_id)
    stats = await db.get_recording_stats(telegram_id)
    total_sentences = await db.get_sentence_count(telegram_id)
    
    # Build status message
    lines = [
        t(lang, "status_header"),
        t(lang, "status_user", username=user['username']),
        t(lang, "status_user_id", user_id=user['cv_user_id']),
        t(lang, "status_email", email=user['email']),
    ]
    
    if session:
        lang_name = config.supported_languages.get(session['language'], session['language'])
        lines.append(t(lang, "status_language", language=lang_name))
        lines.append(t(lang, "status_sentences", count=total_sentences))
        lines.append("")
        lines.append(t(lang, "status_progress_header"))
        
        # Calculate remaining (not recorded or skipped yet)
        remaining = total_sentences - stats['total']
        lines.append(t(lang, "status_progress_remaining", remaining=remaining))
        lines.append(t(lang, "status_progress_pending", pending=stats['pending']))
        lines.append(t(lang, "status_progress_uploaded", uploaded=stats['uploaded']))
        lines.append(t(lang, "status_progress_skipped", skipped=stats['skipped']))
        if stats['failed'] > 0:
            lines.append(t(lang, "status_progress_failed", failed=stats['failed']))
        
        if stats['pending'] > 0:
            lines.append(t(lang, "status_upload_hint"))
        if remaining > 0:
            lines.append(t(lang, "status_remaining_hint"))
    else:
        lines.append(t(lang, "status_no_session"))
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def sentences_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show sentences for the current session.
    
    Usage:
        /sentences - show all sentences with status
        /sentences left - show only unrecorded sentences
    """
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    session = await db.get_session(telegram_id)
    if not session:
        await update.message.reply_text(t(lang, "sentences_no_session"))
        return
    
    sentences = await db.get_all_sentences(telegram_id)
    if not sentences:
        await update.message.reply_text(t(lang, "sentences_none"))
        return
    
    # Check for filter argument
    args = update.message.text.split()[1:]  # Remove /sentences
    show_only_left = args and args[0].lower() in ("left", "remaining", "todo")
    
    # Get recording status for each sentence
    recording_status = {}
    for s in sentences:
        recording = await db.get_recording(telegram_id, s["sentence_number"])
        if recording:
            recording_status[s["sentence_number"]] = recording["status"]
    
    # Filter sentences if requested (exclude any with recording status)
    if show_only_left:
        sentences = [s for s in sentences if recording_status.get(s["sentence_number"]) is None]
        if not sentences:
            await update.message.reply_text(t(lang, "sentences_all_done"))
            return
        header = t(lang, "sentences_left_header", count=len(sentences))
    else:
        header = t(lang, "sentences_header", count=len(sentences))
    
    # Send header
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
    
    session = await db.get_session(telegram_id)
    if not session:
        await update.message.reply_text(t(lang, "upload_no_session"))
        return
    
    # Get pending and failed recordings
    pending = await db.get_pending_recordings(telegram_id)
    failed = await db.get_failed_recordings(telegram_id)
    all_recordings = pending + failed
    
    if not all_recordings:
        await update.message.reply_text(t(lang, "upload_nothing"))
        return
    
    await update.message.reply_text(
        t(lang, "upload_starting", count=len(all_recordings))
    )
    
    # Use admin credentials
    api_client = _get_api_client(config)
    
    success_count = 0
    fail_count = 0
    
    try:
        for rec in all_recordings:
            try:
                # Download audio from Telegram
                audio_file = await context.bot.get_file(rec["file_id"])
                audio_bytes = await audio_file.download_as_bytearray()
                
                # Upload to Common Voice
                await api_client.upload_audio(
                    audio_data=bytes(audio_bytes),
                    user_id=user["cv_user_id"],
                    dataset_code=session["language"],
                    text_id=rec["text_id"],
                    text=rec["text"],
                    text_hash=rec["hash"],
                )
                
                await db.update_recording_status(
                    telegram_id, rec["sentence_number"], "uploaded"
                )
                
                # Mark sentence as seen so it won't be assigned again (save text for dashboard)
                await db.mark_sentence_uploaded(telegram_id, session["language"], rec["text_id"], rec["text"])
                
                success_count += 1
                
            except CVAPIError as e:
                await db.update_recording_status(
                    telegram_id, 
                    rec["sentence_number"], 
                    "failed",
                    error_message=str(e.detail or e.message)
                )
                fail_count += 1
            except Exception as e:
                await db.update_recording_status(
                    telegram_id,
                    rec["sentence_number"],
                    "failed",
                    error_message=str(e)
                )
                fail_count += 1
    finally:
        await api_client.close()
    
    # Send summary
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
    
    session = await db.get_session(telegram_id)
    if not session:
        await update.message.reply_text(t(lang, "skip_no_session"))
        return
    
    total_sentences = await db.get_sentence_count(telegram_id)
    if total_sentences == 0:
        await update.message.reply_text(t(lang, "skip_no_sentences"))
        return
    
    # Get arguments (sentence numbers)
    args = update.message.text.split()[1:]  # Remove /skip
    if not args:
        await update.message.reply_text(
            t(lang, "skip_usage", total=total_sentences),
            parse_mode="Markdown",
        )
        return
    
    # Parse sentence numbers
    numbers = parse_sentence_numbers(" ".join(args), total_sentences)
    if not numbers:
        await update.message.reply_text(
            t(lang, "skip_invalid", total=total_sentences)
        )
        return
    
    # Skip each sentence (mark as skipped so it won't be assigned again)
    skipped = []
    for num in numbers:
        sentence = await db.get_sentence(telegram_id, num)
        if sentence:
            await db.mark_sentence_skipped(telegram_id, session["language"], sentence["text_id"])
            await db.mark_recording_skipped(telegram_id, num)
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
    
    # Check if already logged out
    if not user.get("cv_token"):
        await update.message.reply_text(t(lang, "logout_already_logged_out"))
        return
    
    # Check for pending uploads
    stats = await db.get_recording_stats(telegram_id)
    if stats["pending"] > 0:
        # Use context to track confirmation
        if not context.user_data.get("logout_confirmed"):
            await update.message.reply_text(
                t(lang, "logout_pending_warning", count=stats['pending'])
            )
            context.user_data["logout_confirmed"] = True
            return
    
    # Clear session but keep user record
    await db.logout_user(telegram_id)
    
    # Clear context
    context.user_data.clear()
    
    await update.message.reply_text(t(lang, "logout_success"))


async def resend_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resend unrecorded sentences as individual messages for offline recording."""
    import asyncio
    
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    session = await db.get_session(telegram_id)
    if not session:
        await update.message.reply_text(t(lang, "resend_no_session"))
        return
    
    sentences = await db.get_all_sentences(telegram_id)
    if not sentences:
        await update.message.reply_text(t(lang, "resend_no_sentences"))
        return
    
    # Filter to only unrecorded sentences
    remaining = []
    for s in sentences:
        recording = await db.get_recording(telegram_id, s["sentence_number"])
        if not recording:
            remaining.append(s)
    
    if not remaining:
        await update.message.reply_text(t(lang, "resend_all_done"))
        return
    
    await update.message.reply_text(
        t(lang, "resend_starting", count=len(remaining))
    )
    
    # Send each unrecorded sentence as individual message
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


# Register handlers (priority 40-59: other commands)
handler(priority=40)(CommandHandler("status", status_command))
handler(priority=41)(CommandHandler("sentences", sentences_command))
handler(priority=42)(CommandHandler("upload", upload_command))
handler(priority=43)(CommandHandler("skip", skip_command))
handler(priority=45)(CommandHandler("resend", resend_command))
handler(priority=46)(CommandHandler("logout", logout_command))
