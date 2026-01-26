"""Internationalization module for the bot."""

from bot.i18n.translations import TRANSLATIONS

# Default language
DEFAULT_LANG = "es"

# Supported bot interface languages (not the same as Common Voice languages)
BOT_LANGUAGES = {
    "en": "English",
    "es": "Español",
}


def get_all_skip_words() -> set[str]:
    """Get all skip words from all languages (for reply detection)."""
    return {
        TRANSLATIONS[lang].get("skip_word", "skip").lower()
        for lang in TRANSLATIONS
    }


def t(lang: str, key: str, **kwargs) -> str:
    """
    Get translated string for the given language and key.
    
    Args:
        lang: Language code (e.g., 'en', 'es')
        key: Translation key (e.g., 'welcome', 'login_prompt')
        **kwargs: Format arguments for the string
        
    Returns:
        Translated string, or English fallback if not found
    """
    # Get translations for the language, fall back to English
    lang_translations = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANG])
    
    # Get the specific string, fall back to English
    text = lang_translations.get(key)
    if text is None:
        text = TRANSLATIONS[DEFAULT_LANG].get(key, f"[Missing: {key}]")
    
    # Apply format arguments if any
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass  # Return unformatted if args don't match
    
    return text
