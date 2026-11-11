"""Import all models so Alembic sees complete metadata."""

from __future__ import annotations

from app.modules.audit.models import AuditLog
from app.modules.identity.models import (
    College,
    Role,
    User,
    UserRole,
    UserSession,
)
from app.modules.institution.models import (
    Batch,
    Department,
    Mentor,
    MentorBatchAssignment,
    Student,
)

__all__ = [
    "AuditLog",
    "Batch",
    "College",
    "Department",
    "Mentor",
    "MentorBatchAssignment",
    "Role",
    "Student",
    "User",
    "UserRole",
    "UserSession",
]
