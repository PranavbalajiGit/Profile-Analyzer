"""Request-scoped context values (request ID, tenant)."""

from __future__ import annotations

from contextvars import ContextVar, Token
from uuid import UUID

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(value: str) -> Token[str | None]:
    return _request_id.set(value)


def reset_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)


_tenant_id: ContextVar[UUID | None] = ContextVar("tenant_id", default=None)


class TenantContextError(RuntimeError):
    """Raised when an operation requires a tenant but none is bound."""


def get_tenant_id() -> UUID | None:
    return _tenant_id.get()


def set_tenant_id(college_id: UUID) -> Token[UUID | None]:
    if not isinstance(college_id, UUID):
        raise TypeError("college_id must be a UUID")
    return _tenant_id.set(college_id)


def reset_tenant_id(token: Token[UUID | None]) -> None:
    _tenant_id.reset(token)


def require_tenant_id() -> UUID:
    college_id = _tenant_id.get()
    if college_id is None:
        raise TenantContextError(
            "No tenant is bound to the current context. "
            "Resolve the tenant from the authenticated identity before querying."
        )
    return college_id
