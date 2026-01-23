"""Language selection handler."""

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.database.db import Database
from bot.i18n import t, BOT_LANGUAGES
from bot.handlers.registry import handler


# Conversation state
SELECTING = 0


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the language selection conversation."""
    # Create keyboard with language options
    keyboard = [[f"{name} ({code})"] for code, name in BOT_LANGUAGES.items()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "🌐 Choose your language / Elige tu idioma:",
        reply_markup=reply_markup,
    )
    return SELECTING


async def receive_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive language selection."""
    db: Database = context.bot_data["db"]
    
    text = update.message.text.strip().lower()
    telegram_id = update.effective_user.id
    
    # Extract language code from selection
    selected_code = None
    for code, name in BOT_LANGUAGES.items():
        if code in text or name.lower() in text:
            selected_code = code
            break
    
    if not selected_code:
        keyboard = [[f"{name} ({code})"] for code, name in BOT_LANGUAGES.items()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "Please select a valid language / Por favor selecciona un idioma válido:",
            reply_markup=reply_markup,
        )
        return SELECTING
    
    # Save language preference
    await db.set_bot_language(telegram_id, selected_code)
    
    await update.message.reply_text(
        t(selected_code, "language_changed"),
        reply_markup=ReplyKeyboardRemove(),
    )
    
    # Show help in the new language
    await update.message.reply_text(
        t(selected_code, "welcome"),
        parse_mode="Markdown",
    )
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    db: Database = context.bot_data["db"]
    lang = await db.get_bot_language(update.effective_user.id)
    
    await update.message.reply_text(
        t(lang, "language_current"),
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# Register handler (priority 2: core commands)
handler(priority=2)(
    ConversationHandler(
        entry_points=[CommandHandler("language", language_command)],
        states={
            SELECTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_language)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
)
