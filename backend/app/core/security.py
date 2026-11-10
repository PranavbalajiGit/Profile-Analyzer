"""Password hashing, opaque sessions and signed tokens (FR-01, FR-08).

Passwords use Argon2id. Session cookies carry a signed JWT whose ``sid`` maps to
a server-side ``user_sessions`` row, so sessions are revocable even though the
cookie is self-contained.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import Settings

SESSION_AUDIENCE = "profile-analyzer-session"
OIDC_STATE_AUDIENCE = "profile-analyzer-oidc-state"

PASSWORD_MIN_LENGTH = 12
_PASSWORD_UPPER = re.compile(r"[A-Z]")
_PASSWORD_LOWER = re.compile(r"[a-z]")
_PASSWORD_DIGIT = re.compile(r"[0-9]")

_hasher = PasswordHasher()


class InvalidTokenError(Exception):
    """Raised when a signed token cannot be trusted."""


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    if not password_hash:
        return False
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def validate_password_strength(password: str) -> list[str]:
    """Return human-readable policy violations (empty when acceptable)."""
    problems: list[str] = []
    if len(password) < PASSWORD_MIN_LENGTH:
        problems.append(f"must be at least {PASSWORD_MIN_LENGTH} characters")
    if not _PASSWORD_UPPER.search(password):
        problems.append("must contain an uppercase letter")
    if not _PASSWORD_LOWER.search(password):
        problems.append("must contain a lowercase letter")
    if not _PASSWORD_DIGIT.search(password):
        problems.append("must contain a digit")
    return problems


def hash_token(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8")).digest()


def encode_token(
    claims: dict[str, Any],
    settings: Settings,
    *,
    audience: str,
    ttl: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload = {
        **claims,
        "iss": settings.jwt_issuer,
        "aud": audience,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(
    token: str,
    settings: Settings,
    *,
    audience: str,
) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
    except jwt.PyJWTError as exc:  # pragma: no cover - message varies by version
        raise InvalidTokenError("token cannot be verified") from exc


def create_session_token(
    *,
    user_id: UUID,
    college_id: UUID,
    session_id: UUID,
    settings: Settings,
) -> str:
    return encode_token(
        {
            "sub": str(user_id),
            "col": str(college_id),
            "sid": str(session_id),
            "jti": str(uuid4()),
        },
        settings,
        audience=SESSION_AUDIENCE,
        ttl=timedelta(minutes=settings.session_ttl_minutes),
    )


def create_oidc_state(*, college_id: UUID, nonce: str, settings: Settings) -> str:
    return encode_token(
        {"col": str(college_id), "nonce": nonce},
        settings,
        audience=OIDC_STATE_AUDIENCE,
        ttl=timedelta(minutes=10),
    )


def read_oidc_state(state: str, settings: Settings) -> dict[str, Any]:
    return decode_token(state, settings, audience=OIDC_STATE_AUDIENCE)
