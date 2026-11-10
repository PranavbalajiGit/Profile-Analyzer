"""Unit tests for the role catalogue and authorization helpers."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.exceptions import PermissionDeniedError
from app.core.permissions import (
    RoleCode,
    has_any_role,
    is_admin,
    is_college_wide,
    require_roles,
)
from app.modules.auth.identity import Identity
from app.modules.identity.models import College, User


def make_identity(*roles: str) -> Identity:
    college_id = uuid4()
    return Identity(
        user=User(
            id=uuid4(),
            college_id=college_id,
            institutional_email="person@example.edu",
            display_name="Test Person",
            status="ACTIVE",
        ),
        college=College(id=college_id, name="Test College", short_code="TEST"),
        roles=frozenset(roles),
        session_id=uuid4(),
    )


def test_role_membership_helpers() -> None:
    admin = make_identity(RoleCode.COLLEGE_ADMIN)
    mentor = make_identity(RoleCode.MENTOR)
    super_admin = make_identity(RoleCode.SUPER_ADMIN)

    assert has_any_role(admin, {RoleCode.COLLEGE_ADMIN}) is True
    assert has_any_role(mentor, {RoleCode.COLLEGE_ADMIN}) is False
    assert is_admin(admin) is True
    assert is_admin(super_admin) is True
    assert is_admin(mentor) is False
    assert is_college_wide(make_identity(RoleCode.PLACEMENT_COORDINATOR)) is True
    assert is_college_wide(mentor) is False


def test_require_roles_allows_any_listed_role() -> None:
    dependency = require_roles(RoleCode.COLLEGE_ADMIN, RoleCode.SUPER_ADMIN)
    admin = make_identity(RoleCode.COLLEGE_ADMIN)

    assert dependency(admin) is admin


def test_require_roles_denies_unlisted_roles() -> None:
    dependency = require_roles(RoleCode.COLLEGE_ADMIN)
    student = make_identity(RoleCode.STUDENT)

    with pytest.raises(PermissionDeniedError):
        dependency(student)
