"""Identity and institution models (M2).

Every tenant-owned table carries ``college_id``, exposes ``unique (id,
college_id)`` so children can use composite foreign keys, and is protected by
RLS in migration ``0003``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

COLLEGE_STATUSES = ("ACTIVE", "SUSPENDED", "PROVISIONING")
USER_STATUSES = ("INVITED", "ACTIVE", "SUSPENDED", "GRADUATED", "DEACTIVATED")
RECORD_STATUSES = ("ACTIVE", "INACTIVE")
STUDENT_STATUSES = ("ACTIVE", "GRADUATED", "SUSPENDED", "INACTIVE")

DEFAULT_COLLEGE_TIMEZONE = "Asia/Kolkata"


def _in_list(column: str, values: tuple[str, ...]) -> str:
    joined = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({joined})"


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class College(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Global tenant registry. RLS exposes only the caller's own row."""

    __tablename__ = "colleges"
    __table_args__ = (
        UniqueConstraint("short_code", name="uq_colleges_short_code"),
        UniqueConstraint("domain", name="uq_colleges_domain"),
        CheckConstraint(_in_list("status", COLLEGE_STATUSES), name="status"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_code: Mapped[str] = mapped_column(String(32), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default=DEFAULT_COLLEGE_TIMEZONE
    )
    settings: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Role(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Global role catalogue; not tenant-owned."""

    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("code", name="uq_roles_code"),)

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_assignable: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("id", "college_id", name="uq_users_id_college"),
        Index(
            "uq_users_email",
            "college_id",
            text("lower(institutional_email)"),
            unique=True,
        ),
        Index(
            "uq_users_oidc_identity",
            "oidc_issuer",
            "oidc_subject",
            unique=True,
            postgresql_where=text(
                "oidc_issuer IS NOT NULL AND oidc_subject IS NOT NULL"
            ),
        ),
        CheckConstraint(_in_list("status", USER_STATUSES), name="status"),
        CheckConstraint("failed_login_count >= 0", name="failed_login_count"),
    )

    college_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("colleges.id", name="fk_users_college"),
        nullable=False,
    )
    institutional_email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text)
    oidc_issuer: Mapped[str | None] = mapped_column(Text)
    oidc_subject: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="INVITED")
    failed_login_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        UniqueConstraint("id", "college_id", name="uq_user_sessions_id_college"),
        UniqueConstraint("token_hash", name="uq_user_sessions_token_hash"),
        ForeignKeyConstraint(
            ["user_id", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_user_sessions_user",
        ),
    )

    college_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    token_hash: Mapped[bytes] = mapped_column(nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)


class UserRole(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("id", "college_id", name="uq_user_roles_id_college"),
        Index(
            "uq_user_roles_active",
            "college_id",
            "user_id",
            "role_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
        ForeignKeyConstraint(
            ["user_id", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_user_roles_user",
        ),
        ForeignKeyConstraint(
            ["granted_by", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_user_roles_granted_by",
        ),
        ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_user_roles_role",
        ),
    )

    college_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
