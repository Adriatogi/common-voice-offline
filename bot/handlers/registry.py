"""Handler registry for auto-discovery."""

from telegram.ext import Application, BaseHandler

# Global registry with priority ordering
_handlers: list[tuple[int, BaseHandler]] = []


def handler(priority: int = 50):
    """Decorator to register a handler.
    
    Args:
        priority: Lower numbers run first. Suggested ranges:
            - 0-19: Core commands (start, help)
            - 20-39: Conversations (login, setup)
            - 40-59: Other commands (status, upload)
            - 60-79: Message handlers (recording)
    """
    def decorator(h: BaseHandler) -> BaseHandler:
        _handlers.append((priority, h))
        return h
    return decorator


def register_all(application: Application) -> None:
    """Register all discovered handlers with the application."""
    # Sort by priority (lower first)
    for _, h in sorted(_handlers, key=lambda x: x[0]):
        application.add_handler(h)

