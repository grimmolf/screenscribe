"""Configuration management for screenscribe."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration class for screenscribe."""
    
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # API Keys
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        
        # Whisper Configuration
        self.whisper_cache_dir: Path = Path(
            os.getenv("WHISPER_CACHE_DIR", "~/.cache/whisper")
        ).expanduser()
        
        # LiteLLM Configuration
        self.litellm_log_level: str = os.getenv("LITELLM_LOG_LEVEL", "INFO")
        
        # Prompts Configuration
        self.prompts_dir: Optional[Path] = None
        if os.getenv("SCREENSCRIBE_PROMPTS_DIR"):
            self.prompts_dir = Path(os.getenv("SCREENSCRIBE_PROMPTS_DIR")).expanduser()
        
        # Ensure cache directory exists
        self.whisper_cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ['WHISPER_CACHE_DIR'] = str(self.whisper_cache_dir)
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.openai_api_key and not self.anthropic_api_key:
            errors.append(
                "No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY"
            )
        
        return errors


# Global config instance
config = Config()