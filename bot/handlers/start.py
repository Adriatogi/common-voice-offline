"""Start and help command handlers."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.database.db import Database
from bot.i18n import t
from bot.handlers.registry import handler


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    db: Database = context.bot_data["db"]
    lang = await db.get_bot_language(update.effective_user.id)
    
    await update.message.reply_text(
        t(lang, "welcome"),
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    db: Database = context.bot_data["db"]
    lang = await db.get_bot_language(update.effective_user.id)
    
    await update.message.reply_text(
        t(lang, "welcome"),
        parse_mode="Markdown",
    )


# Register handlers (priority 0-19: core commands)
handler(priority=0)(CommandHandler("start", start_command))
handler(priority=1)(CommandHandler("help", help_command))
