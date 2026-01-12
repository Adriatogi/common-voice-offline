"""Status and management command handlers."""

import os

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.config import Config
from bot.database.db import Database
from bot.services.cv_api import CVAPIClient, CVAPIError
from bot.handlers.registry import handler


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
    user = await db.get_user(telegram_id)
    
    if not user:
        await update.message.reply_text(
            "You're not registered. Use /login to get started."
        )
        return
    
    session = await db.get_session(telegram_id)
    stats = await db.get_recording_stats(telegram_id)
    total_sentences = await db.get_sentence_count(telegram_id)
    
    # Build status message
    lines = [
        "📊 **Your Status**\n",
        f"👤 User: {user['username']}",
        f"📧 Email: {user['email']}",
    ]
    
    if session:
        lang_name = config.supported_languages.get(session['language'], session['language'])
        lines.append(f"🌍 Language: {lang_name}")
        lines.append(f"📝 Sentences: {total_sentences}")
        lines.append("")
        lines.append("**Recording Progress:**")
        lines.append(f"• Total recorded: {stats['total']}/{total_sentences}")
        lines.append(f"• Pending upload: {stats['pending']}")
        lines.append(f"• Uploaded: {stats['uploaded']}")
        lines.append(f"• Failed: {stats['failed']}")
        
        if stats['pending'] > 0:
            lines.append("\n💡 Use /upload to upload pending recordings.")
    else:
        lines.append("\n⚠️ No active session. Use /setup to select a language.")
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def sentences_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all sentences for the current session."""
    db: Database = context.bot_data["db"]
    
    telegram_id = update.effective_user.id
    
    session = await db.get_session(telegram_id)
    if not session:
        await update.message.reply_text(
            "No active session. Use /setup to download sentences."
        )
        return
    
    sentences = await db.get_all_sentences(telegram_id)
    if not sentences:
        await update.message.reply_text(
            "No sentences downloaded. Use /setup to download sentences."
        )
        return
    
    # Get recording status for each sentence
    stats = {}
    for s in sentences:
        recording = await db.get_recording(telegram_id, s["sentence_number"])
        if recording:
            stats[s["sentence_number"]] = recording["status"]
    
    # Send sentences in batches
    await update.message.reply_text(
        f"📝 **Your {len(sentences)} Sentences**\n"
        f"Legend: ⬜ Not recorded • 🟡 Pending • ✅ Uploaded • ❌ Failed\n",
        parse_mode="Markdown",
    )
    
    batch_size = 10
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i + batch_size]
        lines = []
        for s in batch:
            num = s["sentence_number"]
            status = stats.get(num)
            if status == "uploaded":
                emoji = "✅"
            elif status == "pending":
                emoji = "🟡"
            elif status == "failed":
                emoji = "❌"
            else:
                emoji = "⬜"
            lines.append(f"{emoji} **#{num}** {s['text']}")
        
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")


async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger upload of pending recordings."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    
    telegram_id = update.effective_user.id
    
    user = await db.get_user(telegram_id)
    if not user:
        await update.message.reply_text(
            "You're not registered. Use /login to get started."
        )
        return
    
    session = await db.get_session(telegram_id)
    if not session:
        await update.message.reply_text(
            "No active session. Use /setup to get started."
        )
        return
    
    # Get pending and failed recordings
    pending = await db.get_pending_recordings(telegram_id)
    failed = await db.get_failed_recordings(telegram_id)
    all_recordings = pending + failed
    
    if not all_recordings:
        await update.message.reply_text(
            "No recordings to upload! Record some sentences first."
        )
        return
    
    await update.message.reply_text(
        f"📤 Uploading {len(all_recordings)} recordings..."
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
            f"✅ Successfully uploaded {success_count} recordings to Common Voice!"
        )
    else:
        await update.message.reply_text(
            f"📤 Upload complete:\n"
            f"• ✅ Uploaded: {success_count}\n"
            f"• ❌ Failed: {fail_count}\n\n"
            f"Use /status to see details. Failed recordings can be retried with /upload."
        )


async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log out and clear all user data."""
    db: Database = context.bot_data["db"]
    
    telegram_id = update.effective_user.id
    user = await db.get_user(telegram_id)
    
    if not user:
        await update.message.reply_text(
            "You're not registered."
        )
        return
    
    # Check for pending uploads
    stats = await db.get_recording_stats(telegram_id)
    if stats["pending"] > 0:
        await update.message.reply_text(
            f"⚠️ You have {stats['pending']} recordings pending upload!\n\n"
            f"Use /upload first to upload them, or send /logout again to confirm."
        )
        
        # Use context to track confirmation
        if context.user_data.get("logout_confirmed"):
            pass  # Continue with logout
        else:
            context.user_data["logout_confirmed"] = True
            return
    
    # Clear all user data
    await db.delete_user(telegram_id)
    
    # Clear context
    context.user_data.clear()
    
    await update.message.reply_text(
        "✅ You have been logged out.\n\n"
        "Your local data has been cleared.\n"
        "Use /login to register again."
    )


# Register handlers (priority 40-59: other commands)
handler(priority=40)(CommandHandler("status", status_command))
handler(priority=41)(CommandHandler("sentences", sentences_command))
handler(priority=42)(CommandHandler("upload", upload_command))
handler(priority=43)(CommandHandler("logout", logout_command))
