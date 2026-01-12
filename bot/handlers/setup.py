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
    
    user = await db.get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text(
            "You need to register first! Use /login to get started."
        )
        return ConversationHandler.END

    # Create keyboard with language options
    keyboard = [[f"{name} ({code})"] for code, name in config.supported_languages.items()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Let's set up your recording session!\n\n"
        "Please select your **language**:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return LANGUAGE


async def receive_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive language selection."""
    config: Config = context.bot_data["config"]
    
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
            "Please select a valid language from the options:",
            reply_markup=reply_markup,
        )
        return LANGUAGE
    
    context.user_data["setup_language"] = selected_code
    
    # Create keyboard with sentence count options
    counts = ["10", "25", "50", "100"]
    keyboard = [[c for c in counts]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Great! You selected **{config.supported_languages[selected_code]}**.\n\n"
        f"How many sentences would you like to download? (max {config.max_sentences})",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return SENTENCE_COUNT


async def receive_sentence_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive sentence count and fetch sentences."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    
    text = update.message.text.strip()
    
    try:
        count = int(text)
        if count < 1 or count > config.max_sentences:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            f"Please enter a number between 1 and {config.max_sentences}:"
        )
        return SENTENCE_COUNT
    
    language = context.user_data.get("setup_language")
    telegram_id = update.effective_user.id
    
    await update.message.reply_text(
        f"Fetching {count} sentences in {config.supported_languages[language]}...",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    # Fetch sentences from API using admin credentials
    api_client = _get_api_client(config)
    try:
        sentences = await api_client.get_sentences(language, limit=count)
        
        if not sentences:
            await update.message.reply_text(
                f"❌ No sentences available for {config.supported_languages[language]}.\n\n"
                "This language may not be fully supported yet. Try another language with /setup."
            )
            return ConversationHandler.END
        
    except CVAPIError as e:
        await update.message.reply_text(
            f"❌ Failed to fetch sentences: {e.detail or e.message}\n\n"
            "Use /setup to try again."
        )
        return ConversationHandler.END
    finally:
        await api_client.close()
    
    # Save session and sentences
    await db.save_session(telegram_id, language)
    await db.save_sentences(telegram_id, sentences)
    
    # Clear setup data
    context.user_data.pop("setup_language", None)
    
    # Send sentences to user
    await update.message.reply_text(
        f"✅ **Downloaded {len(sentences)} sentences!**\n\n"
        f"I'll send them below. When you're offline, record voice messages in this format:\n"
        f"`#1` followed by your voice recording\n\n"
        f"The sentences will stay in your chat history so you can see them offline.",
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
        "📝 **All sentences sent!**\n\n"
        "To record:\n"
        "1. Type `#1` (or any sentence number)\n"
        "2. Send a voice message reading that sentence\n\n"
        "Your recordings will be uploaded automatically when you're online.\n"
        "Use /status to check your progress.",
        parse_mode="Markdown",
    )
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    context.user_data.pop("setup_language", None)
    
    await update.message.reply_text(
        "Setup cancelled. Use /setup to try again.",
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
