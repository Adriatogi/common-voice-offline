"""Voice recording handlers."""

import os
import re

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.config import Config
from bot.database.db import Database
from bot.services.cv_api import CVAPIClient, CVAPIError
from bot.handlers.registry import handler


# Pattern to match sentence references like "#1", "#25", etc.
SENTENCE_PATTERN = re.compile(r"#(\d+)")


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


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages."""
    db: Database = context.bot_data["db"]
    
    telegram_id = update.effective_user.id
    
    # Check if user is registered
    user = await db.get_user(telegram_id)
    if not user:
        await update.message.reply_text(
            "Please register first with /login before recording."
        )
        return
    
    # Check if user has an active session
    session = await db.get_session(telegram_id)
    if not session:
        await update.message.reply_text(
            "Please set up your session first with /setup."
        )
        return
    
    # Check if there's a pending sentence number
    sentence_number = context.user_data.get("pending_sentence_number")
    
    if not sentence_number:
        # Check reply-to message for sentence number
        if update.message.reply_to_message:
            reply_text = update.message.reply_to_message.text or ""
            match = SENTENCE_PATTERN.search(reply_text)
            if match:
                sentence_number = int(match.group(1))
    
    if not sentence_number:
        await update.message.reply_text(
            "Please specify which sentence you're recording!\n\n"
            "Send a message like `#5` first, then your voice recording.",
            parse_mode="Markdown",
        )
        return
    
    # Verify sentence exists
    sentence = await db.get_sentence(telegram_id, sentence_number)
    if not sentence:
        total = await db.get_sentence_count(telegram_id)
        await update.message.reply_text(
            f"Sentence #{sentence_number} not found. You have sentences #1-#{total}."
        )
        context.user_data.pop("pending_sentence_number", None)
        return
    
    # Save the recording file_id
    voice = update.message.voice
    await db.save_recording(telegram_id, sentence_number, voice.file_id)
    
    # Clear pending sentence
    context.user_data.pop("pending_sentence_number", None)
    
    # Get stats
    stats = await db.get_recording_stats(telegram_id)
    total_sentences = await db.get_sentence_count(telegram_id)
    
    await update.message.reply_text(
        f"✅ Recorded #{sentence_number}!\n"
        f"📊 Progress: {stats['total']}/{total_sentences} sentences recorded\n"
        f"📤 {stats['pending']} pending upload • ✓ {stats['uploaded']} uploaded"
    )
    
    # Attempt immediate upload if online
    await attempt_upload(update, context, telegram_id, sentence_number)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages that might contain sentence references."""
    db: Database = context.bot_data["db"]
    
    text = update.message.text.strip()
    
    # Check for sentence number pattern
    match = SENTENCE_PATTERN.match(text)
    if not match:
        return  # Not a sentence reference, ignore
    
    telegram_id = update.effective_user.id
    sentence_number = int(match.group(1))
    
    # Check if user has a session
    session = await db.get_session(telegram_id)
    if not session:
        await update.message.reply_text(
            "Please set up your session first with /setup."
        )
        return
    
    # Get the sentence
    sentence = await db.get_sentence(telegram_id, sentence_number)
    if not sentence:
        total = await db.get_sentence_count(telegram_id)
        if total == 0:
            await update.message.reply_text(
                "You don't have any sentences. Use /setup to download some."
            )
        else:
            await update.message.reply_text(
                f"Sentence #{sentence_number} not found. You have sentences #1-#{total}."
            )
        return
    
    # Store pending sentence number
    context.user_data["pending_sentence_number"] = sentence_number
    
    # Show the sentence and prompt for recording
    await update.message.reply_text(
        f"**#{sentence_number}**\n{sentence['text']}\n\n"
        f"🎤 Send a voice message now to record this sentence.",
        parse_mode="Markdown",
    )


async def attempt_upload(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    telegram_id: int, 
    sentence_number: int
) -> None:
    """Attempt to upload a recording immediately."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    
    # Get recording and sentence
    recording = await db.get_recording(telegram_id, sentence_number)
    sentence = await db.get_sentence(telegram_id, sentence_number)
    session = await db.get_session(telegram_id)
    user = await db.get_user(telegram_id)
    
    if not all([recording, sentence, session, user]):
        return
    
    try:
        # Download audio from Telegram
        audio_file = await context.bot.get_file(recording["file_id"])
        audio_bytes = await audio_file.download_as_bytearray()
        
        # Upload to Common Voice using admin credentials
        api_client = _get_api_client(config)
        try:
            await api_client.upload_audio(
                audio_data=bytes(audio_bytes),
                user_id=user["cv_user_id"],
                dataset_code=session["language"],
                text_id=sentence["text_id"],
                text=sentence["text"],
                text_hash=sentence["hash"],
            )
            
            # Mark as uploaded
            await db.update_recording_status(telegram_id, sentence_number, "uploaded")
            
            await update.message.reply_text(
                f"☁️ #{sentence_number} uploaded to Common Voice!"
            )
        finally:
            await api_client.close()
            
    except CVAPIError as e:
        # Keep as pending for later retry
        await db.update_recording_status(
            telegram_id, sentence_number, "failed", error_message=str(e.detail or e.message)
        )
    except Exception:
        # Network error, keep as pending
        pass


# Register handlers (priority 60-79: message handlers - must be last)
handler(priority=60)(MessageHandler(filters.VOICE, handle_voice_message))
handler(priority=61)(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
