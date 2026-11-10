"""Authenticated identity attached to a request."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.identity.models import College, User


@dataclass(slots=True)
class Identity:
    user: User
    college: College
    roles: frozenset[str]
    session_id: UUID

    @property
    def user_id(self) -> UUID:
        return self.user.id

    @property
    def college_id(self) -> UUID:
        return self.college.id

    def has_role(self, *codes: str) -> bool:
        return bool(self.roles.intersection(codes))
