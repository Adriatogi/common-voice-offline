"""Start and help command handlers."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.config import Config
from bot.handlers.registry import handler


def _get_welcome_message(config: Config) -> str:
    """Generate welcome message with supported languages."""
    languages = "\n".join(
        f"• {name} ({code})" for code, name in config.supported_languages.items()
    )
    
    return f"""
Welcome to the Common Voice Offline Bot! 🎙️

This bot helps you contribute voice recordings to Mozilla Common Voice, even when you're in areas with limited connectivity.

**How it works:**
1. `/login` - Register with your email and username
2. `/setup` - Select your language and download sentences
3. Go offline and record your voice messages
4. When back online, your recordings are uploaded automatically

**Available Commands:**
/login - Register for Common Voice
/setup - Select language and download sentences
/sentences - View your assigned sentences
/status - Check your recording progress
/upload - Manually trigger upload of pending recordings
/logout - Clear your session
/help - Show this help message

**Supported Languages:**
{languages}

Ready to start? Use /login to begin!
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    config: Config = context.bot_data["config"]
    await update.message.reply_text(
        _get_welcome_message(config),
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    config: Config = context.bot_data["config"]
    await update.message.reply_text(
        _get_welcome_message(config),
        parse_mode="Markdown",
    )


# Register handlers (priority 0-19: core commands)
handler(priority=0)(CommandHandler("start", start_command))
handler(priority=1)(CommandHandler("help", help_command))
