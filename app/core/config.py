"""Application configuration management."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


def _default_sqlite_url() -> str:
    """Build the default SQLite connection URL stored in the project root."""

    database_file = Path(__file__).resolve().parents[2] / "skate_spots.db"
    return f"sqlite:///{database_file}"


class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables."""

    database_url: str = Field(default_factory=_default_sqlite_url, alias="DATABASE_URL")
    secret_key: str = Field(
        default="change-this-secret-key-in-production-use-strong-random-value",
        alias="SECRET_KEY",
    )
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )
    log_json: bool = Field(default=False, alias="LOG_JSON")

    model_config = {
        "env_prefix": "SKATE_SPOTS_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()
