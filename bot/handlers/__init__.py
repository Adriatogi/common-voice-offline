"""Handler modules - import all to trigger registration."""

# Import all handler modules to register them via decorators
from bot.handlers import start, login, setup, status, recording  # noqa: F401

# Re-export registry for convenience
from bot.handlers.registry import register_all  # noqa: F401
