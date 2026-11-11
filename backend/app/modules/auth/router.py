"""Authentication endpoints (FR-01, FR-02, FR-08)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import ServiceUnavailableError
from app.database.session import get_db
from app.modules.auth import oidc, service
from app.modules.auth.dependencies import get_current_identity
from app.modules.auth.identity import Identity
from app.modules.auth.schemas import (
    AuthConfigResponse,
    LoginRequest,
    MeResponse,
    OidcStartResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentIdentity = Annotated[Identity, Depends(get_current_identity)]


def _set_session_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


@router.get("/config", response_model=AuthConfigResponse)
def auth_config(request: Request) -> AuthConfigResponse:
    """Expose non-sensitive login options so the UI can render them."""
    return AuthConfigResponse(oidc_enabled=request.app.state.settings.oidc_enabled)


@router.post("/login", response_model=MeResponse)
def password_login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> MeResponse:
    settings = request.app.state.settings
    result = service.authenticate_password(
        db,
        settings,
        college_code=payload.college_code,
        email=payload.email,
        password=payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _set_session_cookie(response, settings, result.token)
    return service.serialize_me(result.identity)


@router.get("/oidc/start", response_model=OidcStartResponse)
def oidc_start(
    request: Request,
    college_code: Annotated[str, Query(min_length=1, max_length=32)],
    db: DbSession,
) -> OidcStartResponse:
    settings = request.app.state.settings
    started = oidc.start_login(db, settings, college_code)
    return OidcStartResponse(authorization_url=started.authorization_url)


@router.get("/callback")
def oidc_callback(
    request: Request,
    code: Annotated[str, Query(min_length=1)],
    state: Annotated[str, Query(min_length=1)],
    db: DbSession,
) -> RedirectResponse:
    settings = request.app.state.settings
    if not settings.oidc_enabled:
        raise ServiceUnavailableError("Institutional OIDC login is not configured.")

    college_id = oidc.read_state(settings, state)
    tokens = oidc.exchange_code(settings, code)
    claims = oidc.validate_id_token(settings, tokens["id_token"])

    user = oidc.map_verified_identity(db, college_id=college_id, claims=claims)
    token, _ = service.create_session_for_user(
        db,
        settings,
        user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()

    response = RedirectResponse(url=settings.frontend_base_url, status_code=303)
    _set_session_cookie(response, settings, token)
    return response


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db: DbSession,
) -> Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        service.revoke_session(db, settings, token)
    _clear_session_cookie(response, settings)
    response.status_code = 204
    return response


@router.get("/me", response_model=MeResponse)
def me(identity: CurrentIdentity) -> MeResponse:
    return service.serialize_me(identity)
