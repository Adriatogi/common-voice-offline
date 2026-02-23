"""Main entry point for the Common Voice Offline Telegram Bot."""

import logging
import os

from telegram.ext import Application, PicklePersistence

from bot.config import load_config, DATA_DIR
from bot.database.db import Database
from bot.handlers import register_all


# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Load configuration at module level
_config = None


def get_config():
    """Get or load configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


async def post_init(application: Application) -> None:
    """Initialize services after application starts."""
    logger.info("Initializing services...")
    
    # Load config (persistence may have cleared bot_data)
    config = get_config()
    application.bot_data["config"] = config
    
    # Initialize database (Supabase)
    db = Database()
    await db.init()
    application.bot_data["db"] = db
    
    logger.info("Services initialized.")


def main() -> None:
    """Run the bot."""
    logger.info("Starting Common Voice Offline Bot...")
    
    # Load configuration early to validate
    config = get_config()
    
    # Use --dev flag to run with the dev bot token for local testing
    dev_mode = "--dev" in os.sys.argv
    if dev_mode:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN_DEV")
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN_DEV must be set in .env when using --dev")
        logger.info("Running in DEV mode")
    else:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Validate CV credentials are set
    if not os.getenv("CV_CLIENT_ID") or not os.getenv("CV_CLIENT_SECRET"):
        raise ValueError("CV_CLIENT_ID and CV_CLIENT_SECRET environment variables are required")
    
    # Validate Supabase credentials are set
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
    
    # Create persistence for conversation state
    persistence = PicklePersistence(filepath=str(DATA_DIR / "bot_persistence.pickle"))
    
    # Build application
    application = (
        Application.builder()
        .token(bot_token)
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )
    
    # Auto-register all handlers (discovered via decorators)
    register_all(application)
    
    # Start the bot
    logger.info("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
