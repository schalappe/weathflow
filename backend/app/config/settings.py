"""Application settings using Pydantic Settings for environment variable management."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Attributes
    ----------
    anthropic_api_key : SecretStr
        Anthropic API key for Claude categorization.
    database_url : str
        SQLite database URL.
    backend_port : int
        Port for the FastAPI server.
    frontend_url : str
        Frontend URL for CORS configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    anthropic_api_key: SecretStr
    anthropic_base_url: str | None = None
    anthropic_model: str = "claude-opus-4-5-20251101"
    anthropic_thinking_enabled: bool = False
    anthropic_thinking_budget: int = 10000
    database_url: str = f"sqlite:///{Path(__file__).parent.parent.parent.parent / 'data' / 'moneymap.db'}"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns
    -------
    Settings
        Application configuration singleton.
    """
    return Settings()
