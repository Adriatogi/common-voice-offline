"""Setup conversation handler for language selection and sentence fetching."""

import os

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.config import Config
from bot.database.db import Database
from bot.services.cv_api import CVAPIClient, CVAPIError
from bot.i18n import t
from bot.handlers.registry import handler


# Conversation states
LANGUAGE, SENTENCE_COUNT = range(2)


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


async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the setup conversation."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    user = await db.get_user(telegram_id)
    if not user:
        await update.message.reply_text(t(lang, "setup_not_registered"))
        return ConversationHandler.END

    # Create keyboard with Common Voice language options (not bot interface languages)
    keyboard = [[f"{name} ({code})"] for code, name in config.supported_languages.items()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        t(lang, "setup_select_language"),
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return LANGUAGE


async def receive_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive language selection."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    lang = await db.get_bot_language(update.effective_user.id)
    
    text = update.message.text.strip()
    
    # Extract language code from selection
    selected_code = None
    for code, name in config.supported_languages.items():
        if code in text.lower() or name.lower() in text.lower():
            selected_code = code
            break
    
    if not selected_code:
        keyboard = [[f"{name} ({code})"] for code, name in config.supported_languages.items()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            t(lang, "setup_invalid_language"),
            reply_markup=reply_markup,
        )
        return LANGUAGE
    
    context.user_data["setup_language"] = selected_code
    
    # Create keyboard with sentence count options
    counts = ["10", "25", "50", "100"]
    keyboard = [[c for c in counts]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        t(lang, "setup_select_count", 
          language=config.supported_languages[selected_code],
          max=config.max_sentences),
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return SENTENCE_COUNT


async def receive_sentence_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive sentence count and fetch sentences."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    text = update.message.text.strip()
    
    try:
        count = int(text)
        if count < 1 or count > config.max_sentences:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            t(lang, "setup_invalid_count", max=config.max_sentences)
        )
        return SENTENCE_COUNT
    
    cv_language = context.user_data.get("setup_language")
    cv_language_name = config.supported_languages[cv_language]
    
    await update.message.reply_text(
        t(lang, "setup_fetching", count=count, language=cv_language_name),
        reply_markup=ReplyKeyboardRemove(),
    )
    
    # Fetch sentences from API using admin credentials
    api_client = _get_api_client(config)
    try:
        sentences = await api_client.get_sentences(cv_language, limit=count)
        
        if not sentences:
            await update.message.reply_text(
                t(lang, "setup_no_sentences", language=cv_language_name)
            )
            return ConversationHandler.END
        
    except CVAPIError as e:
        await update.message.reply_text(
            t(lang, "setup_fetch_failed", error=e.detail or e.message)
        )
        return ConversationHandler.END
    finally:
        await api_client.close()
    
    # Save session and sentences
    await db.save_session(telegram_id, cv_language)
    await db.save_sentences(telegram_id, sentences)
    
    # Clear setup data
    context.user_data.pop("setup_language", None)
    
    # Send sentences to user
    await update.message.reply_text(
        t(lang, "setup_complete", count=len(sentences)),
        parse_mode="Markdown",
    )
    
    # Send sentences in batches to avoid flooding
    batch_size = 10
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i + batch_size]
        message_lines = []
        for j, sentence in enumerate(batch, start=i + 1):
            message_lines.append(f"**#{j}** {sentence['text']}")
        
        await update.message.reply_text(
            "\n\n".join(message_lines),
            parse_mode="Markdown",
        )
    
    await update.message.reply_text(
        t(lang, "setup_all_sent"),
        parse_mode="Markdown",
    )
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    db: Database = context.bot_data["db"]
    lang = await db.get_bot_language(update.effective_user.id)
    
    context.user_data.pop("setup_language", None)
    
    await update.message.reply_text(
        t(lang, "setup_cancelled"),
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# Register handler (priority 20-39: conversations)
handler(priority=21)(
    ConversationHandler(
        entry_points=[CommandHandler("setup", setup_command)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_language)],
            SENTENCE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_sentence_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
)
