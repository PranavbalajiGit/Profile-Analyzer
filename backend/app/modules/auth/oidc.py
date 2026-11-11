"""Provider-agnostic OIDC adapter (FR-01, FR-02).

The adapter discovers endpoints from the issuer, performs the authorization
code exchange, verifies the ID token signature/issuer/audience/expiry, and maps
a verified identity to an already-provisioned user.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx
import jwt
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import ServiceUnavailableError, UnauthorizedError
from app.core.security import create_oidc_state, read_oidc_state
from app.core.tenant import apply_system, apply_tenant
from app.modules.auth.service import get_college_by_code
from app.modules.identity.models import User

DISCOVERY_TIMEOUT_SECONDS = 10


class OidcError(Exception):
    """Raised when the identity provider response cannot be trusted."""


@dataclass(slots=True)
class OidcStart:
    authorization_url: str
    state: str


def _require_config(settings: Settings) -> None:
    if not settings.oidc_enabled:
        raise ServiceUnavailableError("Institutional OIDC login is not configured.")
    if not settings.oidc_issuer or not settings.oidc_client_id:
        raise ServiceUnavailableError("Institutional OIDC login is not configured.")


def discover(settings: Settings) -> dict[str, Any]:
    _require_config(settings)
    issuer = settings.oidc_issuer.rstrip("/")
    try:
        response = httpx.get(
            f"{issuer}/.well-known/openid-configuration",
            timeout=DISCOVERY_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        document = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OidcError("OIDC discovery failed") from exc

    for key in ("authorization_endpoint", "token_endpoint", "jwks_uri", "issuer"):
        if not document.get(key):
            raise OidcError(f"OIDC discovery document is missing {key}")
    return document


def start_login(session: Session, settings: Settings, college_code: str) -> OidcStart:
    _require_config(settings)

    apply_system(session)
    college = get_college_by_code(session, college_code)
    if college is None:
        raise UnauthorizedError("Unknown institution.")

    document = discover(settings)
    nonce = secrets.token_urlsafe(24)
    state = create_oidc_state(college_id=college.id, nonce=nonce, settings=settings)
    params = {
        "client_id": settings.oidc_client_id,
        "response_type": "code",
        "scope": settings.oidc_scopes,
        "redirect_uri": settings.oidc_redirect_uri,
        "state": state,
        "nonce": nonce,
    }
    separator = "&" if "?" in document["authorization_endpoint"] else "?"
    return OidcStart(
        authorization_url=f"{document['authorization_endpoint']}{separator}{urlencode(params)}",
        state=state,
    )


def read_state(settings: Settings, state: str) -> UUID:
    try:
        claims = read_oidc_state(state, settings)
        return UUID(str(claims["col"]))
    except Exception as exc:  # noqa: BLE001 - any state problem is untrusted input
        raise OidcError("Invalid OIDC state") from exc


def exchange_code(settings: Settings, code: str) -> dict[str, Any]:
    _require_config(settings)
    document = discover(settings)
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.oidc_redirect_uri,
        "client_id": settings.oidc_client_id,
    }
    if settings.oidc_client_secret:
        data["client_secret"] = settings.oidc_client_secret

    try:
        response = httpx.post(
            document["token_endpoint"], data=data, timeout=DISCOVERY_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        tokens = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OidcError("OIDC code exchange failed") from exc

    if not tokens.get("id_token"):
        raise OidcError("OIDC response did not include an ID token")
    return tokens


def validate_id_token(settings: Settings, id_token: str) -> dict[str, Any]:
    _require_config(settings)
    document = discover(settings)
    try:
        signing_key = jwt.PyJWKClient(document["jwks_uri"]).get_signing_key_from_jwt(
            id_token
        )
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256", "RS384", "RS512", "ES256", "ES384"],
            audience=settings.oidc_client_id,
            issuer=document.get("issuer", settings.oidc_issuer),
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
    except jwt.PyJWTError as exc:
        raise OidcError("OIDC ID token cannot be verified") from exc
    return claims


def map_verified_identity(
    session: Session,
    *,
    college_id: UUID,
    claims: dict[str, Any],
) -> User:
    """Map a verified ID token to a provisioned user in the given tenant.

    Unknown identities are rejected; the adapter never auto-provisions (FR-03).
    """
    apply_tenant(session, college_id)

    issuer = claims.get("iss")
    subject = claims.get("sub")
    if not issuer or not subject:
        raise OidcError("OIDC claims are missing issuer or subject")

    user = session.scalar(
        select(User).where(
            User.oidc_issuer == issuer,
            User.oidc_subject == subject,
            User.deleted_at.is_(None),
        )
    )
    if user is not None:
        if user.college_id != college_id or user.status != "ACTIVE":
            raise UnauthorizedError("This identity is not active for this institution.")
        return user

    email = claims.get("email")
    if not email:
        raise UnauthorizedError("Your institution has not provisioned this identity.")
    if claims.get("email_verified") is False:
        raise UnauthorizedError("The identity provider has not verified this email.")

    user = session.scalar(
        select(User).where(
            User.college_id == college_id,
            func.lower(User.institutional_email) == str(email).strip().lower(),
            User.deleted_at.is_(None),
        )
    )
    if user is None or user.status != "ACTIVE":
        raise UnauthorizedError("Your institution has not provisioned this identity.")

    user.oidc_issuer = issuer
    user.oidc_subject = subject
    session.flush()
    return user
