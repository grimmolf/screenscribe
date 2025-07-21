"""Enhanced configuration management for screenscribe with global settings."""

import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class LLMEndpoint:
    """Configuration for an LLM endpoint."""
    name: str
    provider: str  # openai, anthropic, custom
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    enabled: bool = True


@dataclass 
class ScreenscribeConfig:
    """Complete screenscribe configuration."""
    # API Configuration
    llm_endpoints: List[LLMEndpoint]
    default_llm_endpoint: str
    
    # Transcription Configuration
    whisper_cache_dir: str
    default_whisper_model: str
    default_whisper_backend: str
    
    # Processing Configuration
    default_sampling_mode: str
    default_interval_seconds: float
    default_scene_threshold: float
    default_output_format: str
    
    # Directory Configuration
    global_prompts_dir: str
    output_base_dir: str
    
    # YouTube Configuration
    prefer_youtube_transcripts: bool
    yt_dlp_format: str
    
    # Update Configuration
    auto_check_updates: bool
    github_repo: str
    
    @classmethod
    def default(cls) -> 'ScreenscribeConfig':
        """Create default configuration."""
        config_dir = get_config_dir()
        return cls(
            llm_endpoints=[
                LLMEndpoint(
                    name="openai",
                    provider="openai",
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model="gpt-4o"
                ),
                LLMEndpoint(
                    name="anthropic", 
                    provider="anthropic",
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                    model="claude-3-5-sonnet-20241022"
                )
            ],
            default_llm_endpoint="openai",
            whisper_cache_dir=str(Path.home() / ".cache" / "whisper"),
            default_whisper_model="medium",
            default_whisper_backend="auto",
            default_sampling_mode="interval",
            default_interval_seconds=45.0,
            default_scene_threshold=0.3,
            default_output_format="markdown",
            global_prompts_dir=str(config_dir / "prompts"),
            output_base_dir=str(Path.home() / "screenscribe_outputs"),
            prefer_youtube_transcripts=True,
            yt_dlp_format="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            auto_check_updates=True,
            github_repo="grimmolf/screenscribe"
        )


def get_config_dir() -> Path:
    """Get the screenscribe configuration directory."""
    if os.name == 'nt':  # Windows
        config_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming')) / 'screenscribe'
    else:  # Unix-like (Linux, macOS)
        config_dir = Path.home() / '.config' / 'screenscribe'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.json"


def load_config() -> ScreenscribeConfig:
    """Load configuration from file or create default."""
    config_file = get_config_file()
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Convert endpoint dicts to LLMEndpoint objects
            endpoints = [LLMEndpoint(**ep) for ep in data.get('llm_endpoints', [])]
            data['llm_endpoints'] = endpoints
            
            config = ScreenscribeConfig(**data)
            logger.info(f"Loaded configuration from {config_file}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config from {config_file}: {e}")
            logger.info("Using default configuration")
            return ScreenscribeConfig.default()
    else:
        logger.info(f"No config file found at {config_file}, creating default")
        config = ScreenscribeConfig.default()
        save_config(config)
        return config


def save_config(config: ScreenscribeConfig) -> None:
    """Save configuration to file."""
    config_file = get_config_file()
    
    try:
        # Convert to dict for JSON serialization
        data = asdict(config)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved configuration to {config_file}")
        
    except Exception as e:
        logger.error(f"Error saving config to {config_file}: {e}")


def setup_global_directories(config: ScreenscribeConfig) -> None:
    """Set up global directories and copy default prompts if needed."""
    # Create prompts directory
    prompts_dir = Path(config.global_prompts_dir)
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output directory
    output_dir = Path(config.output_base_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy default prompts if they don't exist
    default_prompts = [
        ("synthesis.md", get_default_synthesis_prompt()),
        ("trading.md", get_default_trading_prompt())
    ]
    
    for prompt_name, prompt_content in default_prompts:
        prompt_file = prompts_dir / prompt_name
        if not prompt_file.exists():
            try:
                prompt_file.write_text(prompt_content, encoding='utf-8')
                logger.info(f"Created default prompt: {prompt_file}")
            except Exception as e:
                logger.error(f"Error creating prompt file {prompt_file}: {e}")


def get_default_synthesis_prompt() -> str:
    """Get the default synthesis prompt content."""
    return """You are analyzing a video frame with its corresponding audio transcript to extract key information and insights.

Focus on identifying:
1. Main visual elements and their significance
2. Text content and important information displayed  
3. Context clues about the subject matter
4. Actionable insights or key takeaways
5. How visual and audio content complement each other

Frame timestamp: {timestamp_str}
Transcript context: "{transcript_text}"

Provide JSON response:
{{
  "summary": "Brief synthesis of the main content being presented",
  "visual_description": "Detailed description of what is shown in the frame",
  "key_points": ["specific insight 1", "important concept 2", "actionable takeaway 3"]
}}

Focus on educational value and actionable insights rather than generic descriptions."""


def get_default_trading_prompt() -> str:
    """Get the default trading-specific prompt content."""
    return """You are analyzing a trading/financial education video frame to extract market analysis and trading insights.

Focus on identifying:
1. **Chart Patterns & Price Action** - trends, reversals, support/resistance, magnitude of moves
2. **Technical Indicators** - moving averages, oscillators, fibonacci, volume analysis
3. **Market Structure** - highs/lows, liquidity zones, imbalances, premium/discount areas
4. **Trade Setups** - entries, exits, risk management, stop placements
5. **Educational Concepts** - smart money concepts, fair value gaps, market mechanics
6. **Trading Terminology** - handles, ticks, basis points, specific market language

Frame timestamp: {timestamp_str}  
Transcript context: "{transcript_text}"

Provide JSON response:
{{
  "summary": "Key trading concept, market setup, or educational point being discussed",
  "visual_description": "Detailed description of charts, indicators, price levels, or trading platform elements",
  "key_points": ["specific trading insight", "technical analysis detail", "market concept"]
}}

Focus on actionable trading insights and specific market analysis rather than generic descriptions."""


class EnhancedConfig:
    """Enhanced configuration manager with global settings and validation."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self.config = load_config()
        
        # Setup directories
        setup_global_directories(self.config)
        
        # Legacy compatibility properties
        self._setup_legacy_properties()
    
    def _setup_legacy_properties(self):
        """Set up legacy properties for backward compatibility."""
        # API Keys (look for endpoint with key or fall back to env vars)
        self.openai_api_key = self._get_api_key("openai") or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = self._get_api_key("anthropic") or os.getenv("ANTHROPIC_API_KEY")
        
        # Directories
        self.whisper_cache_dir = Path(self.config.whisper_cache_dir).expanduser()
        self.prompts_dir = Path(self.config.global_prompts_dir) if self.config.global_prompts_dir else None
        
        # Ensure whisper cache directory exists
        self.whisper_cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ['WHISPER_CACHE_DIR'] = str(self.whisper_cache_dir)
    
    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        for endpoint in self.config.llm_endpoints:
            if endpoint.provider == provider and endpoint.api_key:
                return endpoint.api_key
        return None
    
    def get_llm_endpoint(self, name: Optional[str] = None) -> Optional[LLMEndpoint]:
        """Get LLM endpoint by name or default."""
        target_name = name or self.config.default_llm_endpoint
        
        for endpoint in self.config.llm_endpoints:
            if endpoint.name == target_name and endpoint.enabled:
                return endpoint
        
        # Fallback to first enabled endpoint
        for endpoint in self.config.llm_endpoints:
            if endpoint.enabled:
                return endpoint
                
        return None
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Check that at least one LLM endpoint has an API key
        has_valid_key = False
        for endpoint in self.config.llm_endpoints:
            if endpoint.enabled and endpoint.api_key:
                has_valid_key = True
                break
        
        if not has_valid_key:
            errors.append(
                "No valid API keys found. Please configure at least one LLM endpoint with an API key."
            )
        
        # Validate directories exist
        if not Path(self.config.global_prompts_dir).exists():
            errors.append(f"Global prompts directory does not exist: {self.config.global_prompts_dir}")
        
        return errors
    
    def save(self) -> None:
        """Save current configuration to file."""
        save_config(self.config)


# Global enhanced config instance
enhanced_config = EnhancedConfig()

# Legacy compatibility
config = enhanced_config