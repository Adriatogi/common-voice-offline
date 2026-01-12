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
    
    # Check if already logged in
    user = await db.get_user(update.effective_user.id)
    if user:
        await update.message.reply_text(
            f"You're already logged in as **{user['username']}**!\n\n"
            f"Use /logout to log out first, or /setup to continue.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Let's get you set up with Common Voice!\n\n"
        "Please enter your **email address**:\n\n"
        "(This will be used to identify your contributions)\n\n"
        "Type /cancel to abort.",
        parse_mode="Markdown",
    )
    return EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive email address."""
    email = update.message.text.strip().lower()
    
    # Basic email validation
    if "@" not in email or "." not in email:
        await update.message.reply_text(
            "That doesn't look like a valid email. Please try again:"
        )
        return EMAIL
    
    context.user_data["temp_email"] = email
    
    await update.message.reply_text(
        "Great! Now please enter a **username** for Common Voice:\n\n"
        "(This will be visible in the dataset)",
        parse_mode="Markdown",
    )
    return USERNAME


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive username and complete registration."""
    config: Config = context.bot_data["config"]
    db: Database = context.bot_data["db"]
    
    username = update.message.text.strip()
    
    if not username or len(username) < 2:
        await update.message.reply_text(
            "Username must be at least 2 characters. Please try again:"
        )
        return USERNAME
    
    email = context.user_data.get("temp_email")
    
    await update.message.reply_text("Creating your Common Voice profile...")
    
    # Create user in Common Voice using admin credentials
    api_client = _get_api_client(config)
    try:
        user_info = await api_client.create_user(email, username)
        cv_user_id = user_info.get("userId")
        
        if not cv_user_id:
            raise CVAPIError("No userId returned from API")
        
    except CVAPIError as e:
        await update.message.reply_text(
            f"❌ Failed to create user: {e.detail or e.message}\n\n"
            "Use /login to try again."
        )
        return ConversationHandler.END
    finally:
        await api_client.close()
    
    # Save to database (no credentials stored - using admin token)
    await db.save_user(
        telegram_id=update.effective_user.id,
        email=email,
        username=username,
        cv_user_id=cv_user_id,
    )
    
    # Clear temporary data
    context.user_data.pop("temp_email", None)
    
    await update.message.reply_text(
        f"✅ **Registration successful!**\n\n"
        f"Welcome, {username}!\n"
        f"Your Common Voice User ID: `{cv_user_id}`\n\n"
        f"Next step: Use /setup to select your language and download sentences.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    context.user_data.pop("temp_email", None)
    
    await update.message.reply_text(
        "Login cancelled. Use /login to try again.",
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
    )
)
