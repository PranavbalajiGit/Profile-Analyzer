"""Role catalogue and authorization helpers (FR-04, FR-21)."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Annotated

from fastapi import Depends

from app.core.exceptions import PermissionDeniedError
from app.modules.auth.dependencies import get_current_identity
from app.modules.auth.identity import Identity

CurrentIdentity = Annotated[Identity, Depends(get_current_identity)]


class RoleCode(StrEnum):
    STUDENT = "STUDENT"
    MENTOR = "MENTOR"
    PLACEMENT_COORDINATOR = "PLACEMENT_COORDINATOR"
    COLLEGE_ADMIN = "COLLEGE_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


ALL_ROLES: tuple[RoleCode, ...] = tuple(RoleCode)

COLLEGE_WIDE_ROLES = frozenset(
    {RoleCode.PLACEMENT_COORDINATOR, RoleCode.COLLEGE_ADMIN, RoleCode.SUPER_ADMIN}
)
ADMIN_ROLES = frozenset({RoleCode.COLLEGE_ADMIN, RoleCode.SUPER_ADMIN})


def has_any_role(
    identity: Identity,
    roles: frozenset[RoleCode] | set[RoleCode] | tuple[RoleCode, ...],
) -> bool:
    return bool(identity.roles.intersection({role.value for role in roles}))


def is_college_wide(identity: Identity) -> bool:
    return has_any_role(identity, COLLEGE_WIDE_ROLES)


def is_admin(identity: Identity) -> bool:
    return has_any_role(identity, ADMIN_ROLES)


def require_roles(*roles: RoleCode) -> Callable[..., Identity]:
    """Dependency factory enforcing at least one of the given roles."""

    allowed = frozenset(role.value for role in roles)

    def dependency(identity: CurrentIdentity) -> Identity:
        if not identity.roles.intersection(allowed):
            raise PermissionDeniedError()
        return identity

    return dependency


require_admin = require_roles(RoleCode.COLLEGE_ADMIN, RoleCode.SUPER_ADMIN)
require_super_admin = require_roles(RoleCode.SUPER_ADMIN)
