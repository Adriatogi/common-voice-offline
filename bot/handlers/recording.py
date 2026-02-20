"""Voice recording handlers."""

import os
import re

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.config import Config
from bot.database.db import Database
from bot.services.cv_api import CVAPIClient, CVAPIError
from bot.i18n import t, get_all_skip_words
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
    lang = await db.get_bot_language(telegram_id)
    
    # Check if user is registered
    user = await db.get_user(telegram_id)
    if not user:
        await update.message.reply_text(t(lang, "record_not_registered"))
        return
    
    # Check if user has an active session (current language set)
    current_language = user.get("current_language")
    if not current_language:
        await update.message.reply_text(t(lang, "record_no_session"))
        return
    
    cv_user_id = user["cv_user_id"]
    
    # Try to find sentence number from caption or reply-to
    sentence_number = None
    
    # 1. Check caption on the voice/audio message (e.g., "#6" or just "6")
    caption = update.message.caption or ""
    match = SENTENCE_PATTERN.search(caption)
    if not match and caption.strip().isdigit():
        sentence_number = int(caption.strip())
    elif match:
        sentence_number = int(match.group(1))
    
    # 2. Check if replying to a message with sentence number
    if not sentence_number and update.message.reply_to_message:
        reply_text = update.message.reply_to_message.text or ""
        match = SENTENCE_PATTERN.search(reply_text)
        if match:
            sentence_number = int(match.group(1))
    
    if not sentence_number:
        await update.message.reply_text(
            t(lang, "record_specify_sentence"),
            parse_mode="Markdown",
        )
        return
    
    # Verify sentence exists
    sentence = await db.get_sentence_by_number(cv_user_id, current_language, sentence_number)
    if not sentence:
        total = await db.get_sentence_count(cv_user_id, current_language)
        await update.message.reply_text(
            t(lang, "record_not_found", number=sentence_number, total=total)
        )
        return
    
    # Save the recording file_id (support both voice notes and audio files)
    voice = update.message.voice or update.message.audio
    await db.save_recording(sentence["id"], voice.file_id)
    
    # Get stats
    stats = await db.get_recording_stats(cv_user_id, current_language)
    total_sentences = await db.get_sentence_count(cv_user_id, current_language)
    
    await update.message.reply_text(
        t(lang, "record_success",
          number=sentence_number,
          recorded=stats['total'],
          total=total_sentences,
          pending=stats['pending'],
          uploaded=stats['uploaded'])
    )
    
    # Attempt immediate upload if online
    await attempt_upload(update, context, user, sentence, lang)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages that might contain sentence references or skip commands."""
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    text = update.message.text.strip().lower()
    
    # Check if user is replying with a skip word to a sentence message
    if text in get_all_skip_words() and update.message.reply_to_message:
        reply_text = update.message.reply_to_message.text or ""
        match = SENTENCE_PATTERN.search(reply_text)
        if match:
            sentence_number = int(match.group(1))
            await skip_sentence(update, context, telegram_id, sentence_number, lang)
            return
    
    # Check for sentence number pattern
    match = SENTENCE_PATTERN.match(update.message.text.strip())
    if not match:
        # Not a sentence reference - remind user to use commands
        await update.message.reply_text(
            t(lang, "unknown_message"),
            parse_mode="Markdown",
        )
        return
    
    sentence_number = int(match.group(1))
    
    # Check if user has a session
    user = await db.get_user(telegram_id)
    if not user or not user.get("current_language"):
        await update.message.reply_text(t(lang, "record_no_session"))
        return
    
    cv_user_id = user["cv_user_id"]
    current_language = user["current_language"]
    
    # Get the sentence
    sentence = await db.get_sentence_by_number(cv_user_id, current_language, sentence_number)
    if not sentence:
        total = await db.get_sentence_count(cv_user_id, current_language)
        if total == 0:
            await update.message.reply_text(t(lang, "record_no_sentences"))
        else:
            await update.message.reply_text(
                t(lang, "record_not_found", number=sentence_number, total=total)
            )
        return
    
    # Show the sentence - user should reply to this message with voice recording
    await update.message.reply_text(
        t(lang, "record_prompt", number=sentence_number, text=sentence['text']),
        parse_mode="Markdown",
    )


async def skip_sentence(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegram_id: int,
    sentence_number: int,
    lang: str,
) -> None:
    """Skip a single sentence."""
    db: Database = context.bot_data["db"]
    
    # Check if user has a session
    user = await db.get_user(telegram_id)
    if not user or not user.get("current_language"):
        await update.message.reply_text(t(lang, "record_no_session"))
        return
    
    cv_user_id = user["cv_user_id"]
    current_language = user["current_language"]
    
    # Get the sentence
    sentence = await db.get_sentence_by_number(cv_user_id, current_language, sentence_number)
    if not sentence:
        total = await db.get_sentence_count(cv_user_id, current_language)
        await update.message.reply_text(
            t(lang, "record_not_found", number=sentence_number, total=total)
        )
        return
    
    # Mark as skipped
    await db.mark_sentence_skipped(sentence["id"])
    
    await update.message.reply_text(
        t(lang, "skip_success", numbers=f"#{sentence_number}")
    )


async def attempt_upload(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    user: dict,
    sentence: dict,
    lang: str,
) -> None:
    """Attempt to upload a recording immediately."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    
    cv_user_id = user["cv_user_id"]
    current_language = user["current_language"]
    sentence_id = sentence["id"]
    
    # Get recording
    recording = await db.get_recording(sentence_id)
    if not recording:
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
                user_id=cv_user_id,
                dataset_code=current_language,
                text_id=sentence["text_id"],
                text=sentence["text"],
                text_hash=sentence["hash"],
                age=user.get("age"),
                gender=user.get("gender"),
            )
            
            # Mark as uploaded
            await db.update_recording_status(sentence_id, "uploaded")
            await db.mark_sentence_uploaded(sentence_id)
            
            await update.message.reply_text(
                t(lang, "record_uploaded", number=sentence["sentence_number"])
            )
        finally:
            await api_client.close()
            
    except CVAPIError as e:
        await db.update_recording_status(
            sentence_id, "failed", error_message=str(e.detail or e.message)
        )
    except Exception:
        # Network error, keep as pending
        pass


async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unrecognized commands."""
    db: Database = context.bot_data["db"]
    lang = await db.get_bot_language(update.effective_user.id)
    
    await update.message.reply_text(t(lang, "unknown_command"))


# Register handlers
handler(priority=60)(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_message))
handler(priority=61)(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
handler(priority=99)(MessageHandler(filters.COMMAND, handle_unknown_command))
