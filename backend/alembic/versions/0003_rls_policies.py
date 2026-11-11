"""Row-level security policies and runtime role grants (M2).

Revision ID: 0003_rls_policies
Revises: 0002_identity_institution
Create Date: 2026-11-09

Every tenant-owned table is fail-closed: without ``app.current_college_id`` the
policy matches no rows. ``colleges`` additionally honours the narrow
``app.is_system`` flag used only for provisioning and login resolution.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003_rls_policies"
down_revision: str | None = "0002_identity_institution"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES = (
    "users",
    "user_sessions",
    "user_roles",
    "departments",
    "batches",
    "students",
    "mentors",
    "mentor_batch_assignments",
    "audit_logs",
)

TENANT_PREDICATE = (
    "college_id = nullif(current_setting('app.current_college_id', true), '')::uuid"
)

COLLEGE_PREDICATE = (
    "(id = nullif(current_setting('app.current_college_id', true), '')::uuid "
    "OR current_setting('app.is_system', true) = 'true')"
)


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
              USING ({TENANT_PREDICATE})
              WITH CHECK ({TENANT_PREDICATE})
            """
        )

    op.execute("ALTER TABLE colleges ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE colleges FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY colleges_tenant_isolation ON colleges
          USING ({COLLEGE_PREDICATE})
          WITH CHECK ({COLLEGE_PREDICATE})
        """
    )

    # Grants are explicit so a fresh database does not depend on init scripts.
    # The role is created by the deployment/Compose bootstrap.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'profile_app') THEN
                EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON '
                    || 'users, user_sessions, user_roles, departments, batches, '
                    || 'students, mentors, mentor_batch_assignments TO profile_app';
                EXECUTE 'GRANT SELECT, INSERT ON audit_logs TO profile_app';
                EXECUTE 'GRANT SELECT ON roles TO profile_app';
                EXECUTE 'GRANT SELECT, INSERT, UPDATE ON colleges TO profile_app';
                EXECUTE 'REVOKE UPDATE, DELETE, TRUNCATE ON audit_logs FROM profile_app';
                EXECUTE 'REVOKE UPDATE, DELETE, TRUNCATE ON roles FROM profile_app';
                EXECUTE 'REVOKE DELETE, TRUNCATE ON colleges FROM profile_app';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'profile_app') THEN
                EXECUTE 'REVOKE ALL ON users, user_sessions, user_roles, departments, '
                    || 'batches, students, mentors, mentor_batch_assignments, '
                    || 'audit_logs, roles, colleges FROM profile_app';
            END IF;
        END
        $$;
        """
    )
    op.execute("DROP POLICY IF EXISTS colleges_tenant_isolation ON colleges")
    op.execute("ALTER TABLE colleges DISABLE ROW LEVEL SECURITY")
    for table in reversed(TENANT_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
