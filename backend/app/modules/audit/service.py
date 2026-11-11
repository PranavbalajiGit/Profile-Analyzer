"""Audit recording (append-only)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.context import get_request_id
from app.modules.audit.models import AuditLog


def record(
    session: Session,
    *,
    college_id: UUID,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    """Add an audit row to the current transaction.

    The caller commits; audit rows share the transaction of the action they
    describe so a failed action never leaves a misleading entry.
    """
    entry = AuditLog(
        college_id=college_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
        request_id=get_request_id(),
    )
    session.add(entry)
    return entry
