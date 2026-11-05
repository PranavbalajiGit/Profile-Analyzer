from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.context import (
    TenantContextError,
    get_tenant_id,
    require_tenant_id,
    set_tenant_id,
)
from app.core.tenant import SET_TENANT_SQL, apply_tenant, tenant_scope


def test_tenant_scope_binds_and_resets() -> None:
    college_id = uuid4()

    assert get_tenant_id() is None
    with tenant_scope(college_id):
        assert get_tenant_id() == college_id
        assert require_tenant_id() == college_id

    assert get_tenant_id() is None


def test_require_tenant_raises_without_context() -> None:
    with pytest.raises(TenantContextError):
        require_tenant_id()


def test_set_tenant_rejects_non_uuid() -> None:
    with pytest.raises(TypeError):
        set_tenant_id("not-a-uuid")  # type: ignore[arg-type]


class RecordingSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str]]] = []

    def execute(self, statement, params):  # type: ignore[no-untyped-def]
        self.calls.append((str(statement), dict(params)))


def test_apply_tenant_uses_transaction_local_setting() -> None:
    college_id = uuid4()
    session = RecordingSession()

    applied = apply_tenant(session, college_id)  # type: ignore[arg-type]

    assert applied == college_id
    assert str(SET_TENANT_SQL) == (
        "SELECT set_config('app.current_college_id', :college_id, true)"
    )
    assert session.calls == [(str(SET_TENANT_SQL), {"college_id": str(college_id)})]


def test_apply_tenant_requires_context_when_omitted() -> None:
    session = RecordingSession()

    with pytest.raises(TenantContextError):
        apply_tenant(session)  # type: ignore[arg-type]
