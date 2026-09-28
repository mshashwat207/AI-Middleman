from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./middleman.db"
    
    # Needs to be a valid Fernet key (32 url-safe base64-encoded bytes)
    # We will provide a default for local dev, but warn in production
    ENCRYPTION_KEY: str = "tU7z8Q0xG8H_3c1-Xg7M_gJ9wL6j_3K0xY4gM8b-V9g="
    
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    DEFAULT_LLM_PROVIDER: str = "mock"
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    ALLOWED_PROVIDERS: List[str] = ["mock", "openai", "gemini", "anthropic"]
    
    TOKEN_TTL_MINUTES: int = 30
    PII_CONFIDENCE_THRESHOLD: float = 0.70
    MAX_PROMPT_LENGTH: int = 10000
    ENABLE_REHYDRATION: bool = True
    BLOCK_HIGH_RISK_PROMPTS: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
