"""SQLAlchemy declarative base.

Domain models arrive in later milestones. Alembic's ``target_metadata`` points
here so autogeneration keeps working as modules are added.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
