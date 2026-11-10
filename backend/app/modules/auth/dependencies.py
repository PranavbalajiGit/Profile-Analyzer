"""Authentication dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.database.session import get_db
from app.modules.auth.identity import Identity
from app.modules.auth.service import resolve_identity

DbSession = Annotated[Session, Depends(get_db)]


def get_current_identity(
    request: Request,
    db: DbSession,
) -> Identity:
    settings = request.app.state.settings
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise UnauthorizedError()

    identity = resolve_identity(db, settings, token)
    if identity is None:
        raise UnauthorizedError()

    request.state.identity = identity
    return identity
