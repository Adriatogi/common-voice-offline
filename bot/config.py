"""Configuration management for the bot."""

from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


# Base paths (module-level, not config)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Load .env once at module import
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Config:
    """Application configuration (settings that affect behavior)."""
    
    # Common Voice API
    cv_api_base_url: str
    token_expiry_buffer_seconds: int
    
    # Languages
    supported_languages: dict[str, str]
    
    # Sentence limits
    max_sentences: int
    default_sentences: int


def load_config() -> Config:
    """Load configuration from config.yaml."""
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    
    # Load config.yaml
    with open(PROJECT_ROOT / "config.yaml") as f:
        yaml_config = yaml.safe_load(f)
    
    return Config(
        cv_api_base_url=yaml_config["cv_api"]["base_url"],
        token_expiry_buffer_seconds=yaml_config["cv_api"]["token_expiry_buffer_seconds"],
        supported_languages=yaml_config["languages"],
        max_sentences=yaml_config["sentences"]["max"],
        default_sentences=yaml_config["sentences"]["default"],
    )
