"""Database engine and session management.

The engine is created lazily from the settings of the running app, which keeps
the test suite and the CLI scripts from sharing a hard-coded connection.
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings

_engine: Engine | None = None
_engine_url: str | None = None


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine, _engine_url

    resolved = settings or get_settings()
    if _engine is not None and _engine_url == resolved.database_url:
        return _engine

    if _engine is not None:
        _engine.dispose()

    connect_args: dict[str, object] = {}
    if resolved.database_url.startswith("postgresql"):
        connect_args["connect_timeout"] = resolved.database_connect_timeout_seconds

    _engine = create_engine(
        resolved.database_url,
        pool_pre_ping=True,
        pool_size=resolved.database_pool_size,
        max_overflow=resolved.database_max_overflow,
        connect_args=connect_args,
    )
    _engine_url = resolved.database_url
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(settings),
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )


def get_db(request: Request) -> Iterator[Session]:
    """FastAPI dependency yielding a session bound to the app settings.

    Transaction boundaries belong to the calling service, not to the
    dependency, so tenant-scoped ``SET LOCAL`` stays in the same transaction as
    the queries it protects.
    """
    settings = getattr(request.app.state, "settings", None) or get_settings()
    session = get_session_factory(settings)()
    try:
        yield session
    finally:
        session.close()


def check_database(settings: Settings | None = None) -> bool:
    """Return True when the configured database answers a trivial query."""
    try:
        with get_engine(settings).connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - readiness must never raise
        return False
