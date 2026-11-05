"""Application settings.

All configuration comes from environment variables (see ``.env.example``).
Defaults are development-only values and are rejected in production.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_APP_DB_CREDENTIAL = "profile_app:profile_app"
DEFAULT_OWNER_DB_CREDENTIAL = "profile_owner:profile_owner"

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Profile Analyzer"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # The API/worker connect as the restricted role; migrations use the owner role.
    database_url: str = (
        "postgresql+psycopg://profile_app:profile_app@localhost:5433/profile_analyzer"
    )
    migration_database_url: str = (
        "postgresql+psycopg://profile_owner:profile_owner@localhost:5433/profile_analyzer"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_connect_timeout_seconds: int = 5

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    log_level: str = "INFO"
    log_json: bool = True

    cors_origins: list[str] = []

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, value: str) -> str:
        level = value.upper()
        if level not in VALID_LOG_LEVELS:
            raise ValueError(f"log_level must be one of {sorted(VALID_LOG_LEVELS)}")
        return level

    @field_validator("database_url", "migration_database_url")
    @classmethod
    def _require_postgres_driver(cls, value: str) -> str:
        if not value.startswith(("postgresql+psycopg://", "postgresql+psycopg2://")):
            raise ValueError("database URLs must use the postgresql+psycopg driver")
        return value

    @model_validator(mode="after")
    def _validate_production(self) -> Settings:
        if self.environment != "production":
            return self

        if self.debug:
            raise ValueError("debug must be disabled in production")
        if DEFAULT_APP_DB_CREDENTIAL in self.database_url:
            raise ValueError("the default application database credentials are not allowed")
        if DEFAULT_OWNER_DB_CREDENTIAL in self.migration_database_url:
            raise ValueError("the default migration database credentials are not allowed")
        return self

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend_url(self) -> str:
        return self.celery_result_backend or self.redis_url

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
