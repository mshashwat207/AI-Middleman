import sys
import os
from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


def _get_or_generate_key() -> str:
    key = os.environ.get("ENCRYPTION_KEY", "")
    if key:
        return key
    generated = Fernet.generate_key().decode()
    print(
        f"WARNING: No ENCRYPTION_KEY found. Generated a temporary key for this session: {generated}\n"
        "Add it to your .env file to persist token mappings across restarts.",
        file=sys.stderr,
    )
    return generated


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./middleman.db"
    ENCRYPTION_KEY: str = ""

    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"

    DEFAULT_LLM_PROVIDER: str = "gemini"

    @property
    def DEFAULT_MODEL(self) -> str:
        return {
            "groq": self.GROQ_MODEL,
            "gemini": self.GEMINI_MODEL,
            "openai": self.OPENAI_MODEL,
            "anthropic": self.ANTHROPIC_MODEL,
            "mock": "mock",
        }.get(self.DEFAULT_LLM_PROVIDER, self.GEMINI_MODEL)

    ALLOWED_PROVIDERS: List[str] = ["mock", "groq", "gemini", "openai", "anthropic"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    TOKEN_TTL_MINUTES: int = 30
    PII_CONFIDENCE_THRESHOLD: float = 0.65
    MAX_PROMPT_LENGTH: int = 32000
    ENABLE_REHYDRATION: bool = True
    BLOCK_HIGH_RISK_PROMPTS: bool = True
    LLM_TIMEOUT_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


_raw = Settings()

if not _raw.ENCRYPTION_KEY:
    _resolved_key = _get_or_generate_key()
else:
    _resolved_key = _raw.ENCRYPTION_KEY

if _raw.APP_ENV == "production" and not os.environ.get("ENCRYPTION_KEY"):
    print("FATAL: ENCRYPTION_KEY must be set explicitly in production.", file=sys.stderr)
    sys.exit(1)


class _ResolvedSettings(Settings):
    ENCRYPTION_KEY: str = _resolved_key


settings = _ResolvedSettings()
