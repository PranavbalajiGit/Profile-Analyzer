"""Authentication service: password login, sessions and identity resolution."""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppError, LockedError, UnauthorizedError
from app.core.security import (
    SESSION_AUDIENCE,
    InvalidTokenError,
    create_session_token,
    decode_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    validate_password_strength,
    verify_password,
)
from app.core.tenant import apply_system, apply_tenant
from app.modules.auth.identity import Identity
from app.modules.auth.schemas import MeResponse
from app.modules.identity.models import College, Role, User, UserRole, UserSession

INACTIVE_USER_STATUSES = {"SUSPENDED", "DEACTIVATED", "GRADUATED", "INVITED"}


@dataclass(slots=True)
class LoginResult:
    identity: Identity
    token: str


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_ip(value: str | None) -> str | None:
    """Return a valid IP address string, or None.

    ASGI servers and test clients may report non-IP peers; the audit column is
    ``inet``, so anything unparseable is discarded rather than failing login.
    """
    if not value:
        return None
    try:
        return str(ip_address(value))
    except ValueError:
        return None


def get_college_by_code(session: Session, college_code: str) -> College | None:
    """Resolve a college by short code.

    Callers must already be in system context (``apply_system``); this is the
    narrow allow-listed lookup used before a tenant is known.
    """
    normalized = college_code.strip().upper()
    return session.scalar(
        select(College).where(
            func.upper(College.short_code) == normalized,
            College.status == "ACTIVE",
            College.deleted_at.is_(None),
        )
    )


def load_role_codes(session: Session, user: User) -> frozenset[str]:
    rows = session.scalars(
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user.id,
            UserRole.college_id == user.college_id,
            UserRole.revoked_at.is_(None),
        )
    ).all()
    return frozenset(rows)


def create_session_for_user(
    session: Session,
    settings: Settings,
    user: User,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[str, UserSession]:
    now = datetime.now(UTC)
    session_id = uuid4()
    token = create_session_token(
        user_id=user.id,
        college_id=user.college_id,
        session_id=session_id,
        settings=settings,
    )
    row = UserSession(
        id=session_id,
        college_id=user.college_id,
        user_id=user.id,
        token_hash=hash_token(token),
        issued_at=now,
        expires_at=now + timedelta(minutes=settings.session_ttl_minutes),
        ip_address=normalize_ip(ip_address),
        user_agent=(user_agent or "")[:512] or None,
    )
    session.add(row)
    session.flush()
    return token, row


def authenticate_password(
    session: Session,
    settings: Settings,
    *,
    college_code: str,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> LoginResult:
    apply_system(session)
    college = get_college_by_code(session, college_code)
    if college is None:
        raise UnauthorizedError("Invalid credentials.")

    apply_tenant(session, college.id)
    user = session.scalar(
        select(User).where(
            User.college_id == college.id,
            func.lower(User.institutional_email) == normalize_email(email),
            User.deleted_at.is_(None),
        )
    )
    if user is None or user.status in INACTIVE_USER_STATUSES:
        raise UnauthorizedError("Invalid credentials.")

    now = datetime.now(UTC)
    if user.locked_until is not None and user.locked_until > now:
        raise LockedError()

    if not verify_password(user.password_hash, password):
        user.failed_login_count += 1
        if user.failed_login_count >= settings.login_max_failures:
            user.failed_login_count = 0
            user.locked_until = now + timedelta(minutes=settings.login_lockout_minutes)
        session.commit()
        raise UnauthorizedError("Invalid credentials.")

    if user.password_hash and password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now

    token, row = create_session_for_user(
        session, settings, user, ip_address=ip_address, user_agent=user_agent
    )
    roles = load_role_codes(session, user)
    session.commit()

    return LoginResult(
        identity=Identity(
            user=user, college=college, roles=roles, session_id=row.id
        ),
        token=token,
    )


def resolve_identity(
    session: Session,
    settings: Settings,
    token: str,
) -> Identity | None:
    """Resolve a cookie token to an identity, or return None.

    The tenant comes from the *verified* token claim, never from request input.
    """
    try:
        claims = decode_token(token, settings, audience=SESSION_AUDIENCE)
        college_id = UUID(str(claims["col"]))
        user_id = UUID(str(claims["sub"]))
        session_id = UUID(str(claims["sid"]))
    except (InvalidTokenError, KeyError, ValueError):
        return None

    apply_tenant(session, college_id)
    row = session.get(UserSession, session_id)
    if (
        row is None
        or row.college_id != college_id
        or row.user_id != user_id
        or row.revoked_at is not None
        or row.expires_at <= datetime.now(UTC)
        or not hmac.compare_digest(row.token_hash, hash_token(token))
    ):
        return None

    user = session.get(User, user_id)
    if (
        user is None
        or user.college_id != college_id
        or user.status != "ACTIVE"
        or user.deleted_at is not None
    ):
        return None

    college = session.get(College, college_id)
    if college is None or college.status != "ACTIVE" or college.deleted_at is not None:
        return None

    return Identity(
        user=user,
        college=college,
        roles=load_role_codes(session, user),
        session_id=session_id,
    )


def revoke_session(session: Session, settings: Settings, token: str) -> None:
    try:
        claims = decode_token(token, settings, audience=SESSION_AUDIENCE)
        college_id = UUID(str(claims["col"]))
        session_id = UUID(str(claims["sid"]))
    except (InvalidTokenError, KeyError, ValueError):
        return

    apply_tenant(session, college_id)
    row = session.get(UserSession, session_id)
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)
        session.commit()


def serialize_me(identity: Identity) -> MeResponse:
    return MeResponse(
        user_id=identity.user.id,
        college_id=identity.college.id,
        college_name=identity.college.name,
        college_code=identity.college.short_code,
        email=identity.user.institutional_email,
        display_name=identity.user.display_name,
        status=identity.user.status,
        roles=sorted(identity.roles),
    )


def set_password(
    session: Session,
    user: User,
    password: str,
) -> None:
    problems = validate_password_strength(password)
    if problems:
        raise AppError(
            "Password does not meet the policy: " + "; ".join(problems),
            code="weak_password",
            status_code=400,
        )
    user.password_hash = hash_password(password)
    session.add(user)
