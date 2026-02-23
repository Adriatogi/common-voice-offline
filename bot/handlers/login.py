"""Login conversation handler."""

import os

from telegram import Update, ReplyKeyboardRemove
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
EMAIL, USERNAME = range(2)


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


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the login conversation."""
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)
    
    # Check if already logged in (has token)
    user = await db.get_user(telegram_id)
    if user and user.get("cv_token"):
        await update.message.reply_text(
            t(lang, "already_logged_in", username=user['username']),
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        t(lang, "login_start"),
        parse_mode="Markdown",
    )
    return EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive email address."""
    db: Database = context.bot_data["db"]
    lang = await db.get_bot_language(update.effective_user.id)
    
    email = update.message.text.strip().lower()
    
    # Basic email validation
    if "@" not in email or "." not in email:
        await update.message.reply_text(t(lang, "login_invalid_email"))
        return EMAIL
    
    context.user_data["temp_email"] = email
    
    await update.message.reply_text(
        t(lang, "login_enter_username"),
        parse_mode="Markdown",
    )
    return USERNAME


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive username and complete registration or re-login.

    Three cases:
    1. Username doesn't exist       → create new CV account
    2. Username exists, email match  → re-login (claim the account)
    3. Username exists, email mismatch → reject ("taken")
    """
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    telegram_id = update.effective_user.id
    lang = await db.get_bot_language(telegram_id)

    username = update.message.text.strip().lower()

    if not username or len(username) < 2:
        await update.message.reply_text(t(lang, "login_invalid_username"))
        return USERNAME

    email = context.user_data.get("temp_email")
    existing_account = await db.get_user_by_username(username)

    if existing_account:
        # Username already exists — verify ownership via email
        if existing_account["email"] != email:
            await update.message.reply_text(t(lang, "login_username_taken"))
            return USERNAME

        # Email matches — re-login / claim this account
        cv_user_id = existing_account["cv_user_id"]

        await update.message.reply_text(t(lang, "login_logging_in"))

        # If a different telegram_id holds this username, free the row first
        if existing_account["telegram_id"] != telegram_id:
            await db.release_username(username)

        await db.save_user(
            telegram_id=telegram_id,
            email=email,
            username=username,
            cv_user_id=cv_user_id,
            bot_language=lang,
        )

        context.user_data.pop("temp_email", None)
        await update.message.reply_text(
            t(lang, "login_welcome_back", username=username, cv_user_id=cv_user_id),
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    # Username doesn't exist — create a new CV account
    await update.message.reply_text(t(lang, "login_creating"))

    api_client = _get_api_client(config)
    try:
        user_info = await api_client.create_user(email, username)
        cv_user_id = user_info.get("userId")

        if not cv_user_id:
            raise CVAPIError("No userId returned from API")

    except CVAPIError as e:
        await update.message.reply_text(
            t(lang, "login_failed", error=e.detail or e.message)
        )
        return ConversationHandler.END
    finally:
        await api_client.close()

    await db.save_user(
        telegram_id=telegram_id,
        email=email,
        username=username,
        cv_user_id=cv_user_id,
        bot_language=lang,
    )

    context.user_data.pop("temp_email", None)
    await update.message.reply_text(
        t(lang, "login_success", username=username, cv_user_id=cv_user_id),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    db: Database = context.bot_data["db"]
    lang = await db.get_bot_language(update.effective_user.id)
    
    context.user_data.pop("temp_email", None)
    
    await update.message.reply_text(
        t(lang, "login_cancelled"),
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# Register handler (priority 20-39: conversations)
handler(priority=20)(
    ConversationHandler(
        entry_points=[CommandHandler("login", login_command)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
)
