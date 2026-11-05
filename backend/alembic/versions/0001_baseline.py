"""Baseline: required PostgreSQL extensions.

No domain tables yet. Domain migrations are added milestone by milestone, and
RLS policies are added in their own reviewable migration.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-11-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")


def downgrade() -> None:
    # Extensions are shared database objects; never drop them in a downgrade.
    pass
