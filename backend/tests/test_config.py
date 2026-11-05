from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_safe_development_defaults() -> None:
    settings = Settings(_env_file=None, environment="development")

    assert settings.app_name == "Profile Analyzer"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.log_level == "INFO"
    assert settings.broker_url == settings.redis_url
    assert settings.result_backend_url == settings.redis_url


def test_log_level_is_normalized_and_validated() -> None:
    assert Settings(_env_file=None, environment="test", log_level="debug").log_level == "DEBUG"

    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="test", log_level="verbose")


def test_non_postgres_database_url_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="test", database_url="sqlite:///local.db")


def test_production_rejects_debug() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            environment="production",
            debug=True,
            database_url="postgresql+psycopg://svc:strong@db.internal:5432/app",
            migration_database_url="postgresql+psycopg://owner:strong@db.internal:5432/app",
        )


def test_production_rejects_default_credentials() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production")


def test_production_accepts_hardened_settings() -> None:
    settings = Settings(
        _env_file=None,
        environment="production",
        debug=False,
        database_url="postgresql+psycopg://svc:strong@db.internal:5432/app",
        migration_database_url="postgresql+psycopg://owner:strong@db.internal:5432/app",
        log_json=True,
    )

    assert settings.is_production is True
