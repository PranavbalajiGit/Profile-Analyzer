"""Shared helper for admin write operations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.identity.models import Role, UserRole


def assign_role(
    session: Session,
    *,
    college_id,
    user_id,
    role_code: str,
    granted_by=None,
) -> None:
    role = session.query(Role).filter(Role.code == role_code).one_or_none()
    if role is None:
        raise NotFoundError(f"Role {role_code} is not configured.")

    existing = (
        session.query(UserRole)
        .filter(
            UserRole.college_id == college_id,
            UserRole.user_id == user_id,
            UserRole.role_id == role.id,
            UserRole.revoked_at.is_(None),
        )
        .one_or_none()
    )
    if existing is not None:
        return

    session.add(
        UserRole(
            college_id=college_id,
            user_id=user_id,
            role_id=role.id,
            granted_by=granted_by,
        )
    )
