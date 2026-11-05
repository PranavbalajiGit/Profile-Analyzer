"""Tenant binding helpers.

Tenant identity always comes from the authenticated context — never from a
request body, query parameter, or header supplied by the client (README §8).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.context import (
    TenantContextError,
    get_tenant_id,
    require_tenant_id,
    reset_tenant_id,
    set_tenant_id,
)

__all__ = [
    "TenantContextError",
    "apply_tenant",
    "get_tenant_id",
    "require_tenant_id",
    "tenant_scope",
]

SET_TENANT_SQL = text("SELECT set_config('app.current_college_id', :college_id, true)")


@contextmanager
def tenant_scope(college_id: UUID) -> Iterator[UUID]:
    """Bind a tenant for the duration of a block."""
    token = set_tenant_id(college_id)
    try:
        yield college_id
    finally:
        reset_tenant_id(token)


def apply_tenant(session: Session, college_id: UUID | None = None) -> UUID:
    """Set the transaction-local tenant used by PostgreSQL RLS policies.

    ``set_config(..., is_local => true)`` is scoped to the current transaction,
    so this must be called inside the same transaction as the queries it
    protects. Callers must never pass a client-supplied tenant ID.
    """
    resolved = college_id or require_tenant_id()
    session.execute(SET_TENANT_SQL, {"college_id": str(resolved)})
    return resolved
