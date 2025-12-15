"""
Configuration management for ContextDiff API.

Uses Pydantic Settings to load and validate environment variables.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        OPENAI_API_KEY: OpenAI API key for LLM operations.
        OPENAI_MODEL: Model to use for semantic analysis (default: gpt-4o-mini).
        OPENAI_TEMPERATURE: Temperature setting for LLM (default: 0.1 for consistency).
        OPENAI_MAX_TOKENS: Maximum tokens for LLM response (default: 4000).
        API_TITLE: FastAPI application title.
        API_VERSION: API version string.
        API_DESCRIPTION: API description for documentation.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"  # Balanced speed/quality
    PREMIUM_LLM_MODEL: str = "gpt-4o"  # Best quality for premium
    OPENAI_MODEL: str = "gpt-4o-mini"  # Deprecated, use DEFAULT_LLM_MODEL
    OPENAI_TEMPERATURE: float = 0.0  # Deterministic for speed
    OPENAI_MAX_TOKENS: int = 1500  # Prevent truncation, prompt enforces brevity
    OPENAI_TIMEOUT: int = 25  # Fast timeout
    
    # Cost Protection
    MAX_TOTAL_CHARS: int = 15000  # Maximum combined text length
    SHORT_CIRCUIT_THRESHOLD: float = 0.96  # More aggressive skip (96% similarity)
    
    # API Configuration
    API_TITLE: str = "ContextDiff API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Semantic text difference analysis using AI"
    
    # Security
    API_SECRET: Optional[str] = None  # Secret for RapidAPI authentication
    
    # CORS (Optional - for production you'd configure this properly)
    ALLOW_ORIGINS: list[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Monitoring Configuration
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1  # 10% of transactions
    
    def validate_settings(self) -> None:
        """
        Validate critical settings.
        
        Raises:
            ValueError: If critical settings are missing or invalid.
        """
        if not self.OPENAI_API_KEY or self.OPENAI_API_KEY == "your_openai_api_key_here":
            raise ValueError("OPENAI_API_KEY must be set in environment or .env file")


# Global settings instance
settings = Settings()
