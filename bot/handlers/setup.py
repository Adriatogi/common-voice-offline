"""Setup conversation handler for language selection and sentence fetching."""

import os
import asyncio
import logging

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

logger = logging.getLogger(__name__)

# Conversation states
LANGUAGE, AGE, GENDER, SENTENCE_COUNT = range(4)

# Age range options (API value -> translation key)
AGE_OPTIONS = [
    ("teens", "age_teens"),
    ("twenties", "age_twenties"),
    ("thirties", "age_thirties"),
    ("forties", "age_forties"),
    ("fifties", "age_fifties"),
    ("sixties", "age_sixties"),
    ("seventies", "age_seventies"),
    ("eighties", "age_eighties"),
    ("nineties", "age_nineties"),
]

# Gender options (API value -> translation key)
GENDER_OPTIONS = [
    ("male_masculine", "gender_male"),
    ("female_feminine", "gender_female"),
    ("'non-binary'", "gender_non_binary"),  # API requires quotes
    ("do_not_wish_to_say", "gender_prefer_not"),
]


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
    
    # Show age selection keyboard
    keyboard = [[t(lang, key)] for _, key in AGE_OPTIONS]
    keyboard.append([t(lang, "setup_skip")])
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        t(lang, "setup_select_age"),
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return AGE


async def receive_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive age selection."""
    db: Database = context.bot_data["db"]
    lang = await db.get_bot_language(update.effective_user.id)
    
    text = update.message.text.strip()
    
    # Check if user skipped
    if text == t(lang, "setup_skip"):
        context.user_data["setup_age"] = None
    else:
        # Find matching age option
        selected_age = None
        for api_value, key in AGE_OPTIONS:
            if text == t(lang, key):
                selected_age = api_value
                break
        
        if selected_age is None:
            # Invalid selection, show keyboard again
            keyboard = [[t(lang, key)] for _, key in AGE_OPTIONS]
            keyboard.append([t(lang, "setup_skip")])
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(
                t(lang, "setup_select_age"),
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
            return AGE
        
        context.user_data["setup_age"] = selected_age
    
    # Show gender selection keyboard
    keyboard = [[t(lang, key)] for _, key in GENDER_OPTIONS]
    keyboard.append([t(lang, "setup_skip")])
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        t(lang, "setup_select_gender"),
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return GENDER


async def receive_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive gender selection."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    lang = await db.get_bot_language(update.effective_user.id)
    
    text = update.message.text.strip()
    
    # Check if user skipped
    if text == t(lang, "setup_skip"):
        context.user_data["setup_gender"] = None
    else:
        # Find matching gender option
        selected_gender = None
        for api_value, key in GENDER_OPTIONS:
            if text == t(lang, key):
                selected_gender = api_value
                break
        
        if selected_gender is None:
            # Invalid selection, show keyboard again
            keyboard = [[t(lang, key)] for _, key in GENDER_OPTIONS]
            keyboard.append([t(lang, "setup_skip")])
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(
                t(lang, "setup_select_gender"),
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
            return GENDER
        
        context.user_data["setup_gender"] = selected_gender
    
    # Show sentence count selection
    selected_code = context.user_data.get("setup_language")
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
    
    # Get user's CV ID
    user = await db.get_user(telegram_id)
    cv_user_id = user["cv_user_id"]
    
    await update.message.reply_text(
        t(lang, "setup_fetching", count=count, language=cv_language_name),
        reply_markup=ReplyKeyboardRemove(),
    )
    
    # Get previously seen sentences to avoid duplicates
    seen_ids = await db.get_seen_sentence_ids(cv_user_id, cv_language)
    
    # Fetch sentences from API using admin credentials
    api_client = _get_api_client(config)
    try:
        sentences = await api_client.get_sentences(
            cv_language, 
            limit=count, 
            exclude_ids=seen_ids,
        )
        
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
    
    # Save demographics (non-critical - don't fail setup if this errors)
    setup_age = context.user_data.get("setup_age")
    setup_gender = context.user_data.get("setup_gender")
    try:
        await db.update_user_demographics(telegram_id, setup_age, setup_gender)
    except Exception as e:
        logger.warning(f"Failed to save demographics for {telegram_id}: {e}")
    
    # Set current language and save sentences
    await db.set_current_language(telegram_id, cv_language)
    await db.save_sentences(cv_user_id, cv_language, sentences)
    
    # Clear setup data
    context.user_data.pop("setup_language", None)
    context.user_data.pop("setup_age", None)
    context.user_data.pop("setup_gender", None)
    
    # Send sentences to user
    await update.message.reply_text(
        t(lang, "setup_complete", count=len(sentences)),
        parse_mode="Markdown",
    )
    
    # Send each sentence as individual message (so user can reply to it offline)
    for i, sentence in enumerate(sentences, start=1):
        await update.message.reply_text(
            f"**#{i}** {sentence['text']}",
            parse_mode="Markdown",
        )
        # Small delay to avoid Telegram rate limits
        await asyncio.sleep(0.1)
    
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
    context.user_data.pop("setup_age", None)
    context.user_data.pop("setup_gender", None)
    
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
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_gender)],
            SENTENCE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_sentence_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
)
