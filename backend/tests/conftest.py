"""Shared test configuration."""

from __future__ import annotations

import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_JSON", "false")

# Integration tests run only when a disposable PostgreSQL database is provided.
# Setting these here (before app modules import settings) keeps the test process
# pointed at the test database for the whole session.
_TEST_APP_URL = os.environ.get("TEST_DATABASE_URL")
_TEST_OWNER_URL = os.environ.get("TEST_MIGRATION_DATABASE_URL")

if _TEST_APP_URL and _TEST_OWNER_URL:
    os.environ["DATABASE_URL"] = _TEST_APP_URL
    os.environ["MIGRATION_DATABASE_URL"] = _TEST_OWNER_URL
    os.environ.setdefault("JWT_SECRET", "test-session-signing-secret-that-is-long")
