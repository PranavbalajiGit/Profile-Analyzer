"""Identity and institution schema (M2).

Revision ID: 0002_identity_institution
Revises: 0001_baseline
Create Date: 2026-11-09

Creates the tenant-owned institution tables with composite foreign keys so a
row can never reference another tenant's row (FR-12). RLS policies and role
grants are added separately in ``0003_rls_policies``.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_identity_institution"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLLEGE_STATUSES = "'ACTIVE', 'SUSPENDED', 'PROVISIONING'"
USER_STATUSES = "'INVITED', 'ACTIVE', 'SUSPENDED', 'GRADUATED', 'DEACTIVATED'"
RECORD_STATUSES = "'ACTIVE', 'INACTIVE'"
STUDENT_STATUSES = "'ACTIVE', 'GRADUATED', 'SUSPENDED', 'INACTIVE'"

ROLE_IDS = {
    "STUDENT": uuid.UUID("00000000-0000-4000-8000-000000000001"),
    "MENTOR": uuid.UUID("00000000-0000-4000-8000-000000000002"),
    "PLACEMENT_COORDINATOR": uuid.UUID("00000000-0000-4000-8000-000000000003"),
    "COLLEGE_ADMIN": uuid.UUID("00000000-0000-4000-8000-000000000004"),
    "SUPER_ADMIN": uuid.UUID("00000000-0000-4000-8000-000000000005"),
}


def upgrade() -> None:
    op.create_table(
        "colleges",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("short_code", sa.String(32), nullable=False),
        sa.Column("domain", sa.String(255)),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column("timezone", sa.String(64), server_default="Asia/Kolkata", nullable=False),
        sa.Column(
            "settings", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_colleges"),
        sa.UniqueConstraint("short_code", name="uq_colleges_short_code"),
        sa.UniqueConstraint("domain", name="uq_colleges_domain"),
        sa.CheckConstraint(f"status IN ({COLLEGE_STATUSES})", name="ck_colleges_status"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_assignable", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("college_id", sa.Uuid(), nullable=False),
        sa.Column("institutional_email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.Text()),
        sa.Column("oidc_issuer", sa.Text()),
        sa.Column("oidc_subject", sa.Text()),
        sa.Column("status", sa.String(20), server_default="INVITED", nullable=False),
        sa.Column("failed_login_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.ForeignKeyConstraint(["college_id"], ["colleges.id"], name="fk_users_college"),
        sa.UniqueConstraint("id", "college_id", name="uq_users_id_college"),
        sa.CheckConstraint(f"status IN ({USER_STATUSES})", name="ck_users_status"),
        sa.CheckConstraint("failed_login_count >= 0", name="ck_users_failed_login_count"),
    )
    op.create_index(
        "uq_users_email",
        "users",
        ["college_id", sa.text("lower(institutional_email)")],
        unique=True,
    )
    op.create_index(
        "uq_users_oidc_identity",
        "users",
        ["oidc_issuer", "oidc_subject"],
        unique=True,
        postgresql_where=sa.text("oidc_issuer IS NOT NULL AND oidc_subject IS NOT NULL"),
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("college_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(), nullable=False),
        sa.Column(
            "issued_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("ip_address", postgresql.INET()),
        sa.Column("user_agent", sa.Text()),
        sa.PrimaryKeyConstraint("id", name="pk_user_sessions"),
        sa.ForeignKeyConstraint(
            ["college_id"], ["colleges.id"], name="fk_user_sessions_college"
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_user_sessions_user",
        ),
        sa.UniqueConstraint("id", "college_id", name="uq_user_sessions_id_college"),
        sa.UniqueConstraint("token_hash", name="uq_user_sessions_token_hash"),
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("college_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("granted_by", sa.Uuid()),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_user_roles"),
        sa.ForeignKeyConstraint(
            ["user_id", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_user_roles_user",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_user_roles_granted_by",
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name="fk_user_roles_role"),
        sa.UniqueConstraint("id", "college_id", name="uq_user_roles_id_college"),
    )
    op.create_index(
        "uq_user_roles_active",
        "user_roles",
        ["college_id", "user_id", "role_id"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    op.create_table(
        "departments",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("college_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_departments"),
        sa.ForeignKeyConstraint(
            ["college_id"], ["colleges.id"], name="fk_departments_college"
        ),
        sa.UniqueConstraint("college_id", "code", name="uq_departments_code"),
        sa.UniqueConstraint("id", "college_id", name="uq_departments_id_college"),
        sa.CheckConstraint(f"status IN ({RECORD_STATUSES})", name="ck_departments_status"),
    )

    op.create_table(
        "batches",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("college_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=False),
        sa.Column("end_year", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_batches"),
        sa.ForeignKeyConstraint(["college_id"], ["colleges.id"], name="fk_batches_college"),
        sa.ForeignKeyConstraint(
            ["department_id", "college_id"],
            ["departments.id", "departments.college_id"],
            name="fk_batches_department",
        ),
        sa.UniqueConstraint(
            "college_id", "department_id", "name", name="uq_batches_name"
        ),
        sa.UniqueConstraint("id", "college_id", name="uq_batches_id_college"),
        sa.CheckConstraint("end_year >= start_year", name="ck_batches_year_range"),
        sa.CheckConstraint(f"status IN ({RECORD_STATUSES})", name="ck_batches_status"),
    )

    op.create_table(
        "students",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("college_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("register_number", sa.String(64), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("admission_year", sa.Integer()),
        sa.Column("current_year", sa.Integer()),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column("profile_completeness", sa.Numeric(5, 2)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_students"),
        sa.ForeignKeyConstraint(["college_id"], ["colleges.id"], name="fk_students_college"),
        sa.ForeignKeyConstraint(
            ["user_id", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_students_user",
        ),
        sa.ForeignKeyConstraint(
            ["department_id", "college_id"],
            ["departments.id", "departments.college_id"],
            name="fk_students_department",
        ),
        sa.ForeignKeyConstraint(
            ["batch_id", "college_id"],
            ["batches.id", "batches.college_id"],
            name="fk_students_batch",
        ),
        sa.UniqueConstraint("college_id", "user_id", name="uq_students_user"),
        sa.UniqueConstraint("id", "college_id", name="uq_students_id_college"),
        sa.CheckConstraint(f"status IN ({STUDENT_STATUSES})", name="ck_students_status"),
    )
    op.create_index(
        "uq_students_register",
        "students",
        ["college_id", sa.text("lower(register_number)")],
        unique=True,
    )
    op.create_index(
        "ix_students_scope", "students", ["college_id", "department_id", "batch_id"]
    )
    op.create_index("ix_students_status", "students", ["college_id", "status"])

    op.create_table(
        "mentors",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("college_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("employee_code", sa.String(64), nullable=False),
        sa.Column("department_id", sa.Uuid()),
        sa.Column("status", sa.String(20), server_default="ACTIVE", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_mentors"),
        sa.ForeignKeyConstraint(["college_id"], ["colleges.id"], name="fk_mentors_college"),
        sa.ForeignKeyConstraint(
            ["user_id", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_mentors_user",
        ),
        sa.ForeignKeyConstraint(
            ["department_id", "college_id"],
            ["departments.id", "departments.college_id"],
            name="fk_mentors_department",
        ),
        sa.UniqueConstraint("college_id", "employee_code", name="uq_mentors_employee"),
        sa.UniqueConstraint("college_id", "user_id", name="uq_mentors_user"),
        sa.UniqueConstraint("id", "college_id", name="uq_mentors_id_college"),
        sa.CheckConstraint(f"status IN ({RECORD_STATUSES})", name="ck_mentors_status"),
    )

    op.create_table(
        "mentor_batch_assignments",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("college_id", sa.Uuid(), nullable=False),
        sa.Column("mentor_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_by", sa.Uuid()),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_by", sa.Uuid()),
        sa.PrimaryKeyConstraint("id", name="pk_mentor_batch_assignments"),
        sa.ForeignKeyConstraint(
            ["college_id"],
            ["colleges.id"],
            name="fk_mentor_batch_assignments_college",
        ),
        sa.ForeignKeyConstraint(
            ["mentor_id", "college_id"],
            ["mentors.id", "mentors.college_id"],
            name="fk_mentor_batch_assignments_mentor",
        ),
        sa.ForeignKeyConstraint(
            ["batch_id", "college_id"],
            ["batches.id", "batches.college_id"],
            name="fk_mentor_batch_assignments_batch",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_mentor_batch_assignments_assigned_by",
        ),
        sa.ForeignKeyConstraint(
            ["revoked_by", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_mentor_batch_assignments_revoked_by",
        ),
        sa.UniqueConstraint(
            "id", "college_id", name="uq_mentor_batch_assignments_id_college"
        ),
    )
    op.create_index(
        "uq_mentor_batch_assignments_active",
        "mentor_batch_assignments",
        ["college_id", "mentor_id", "batch_id"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("college_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid()),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Uuid()),
        sa.Column(
            "details", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("request_id", sa.String(128)),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
        sa.ForeignKeyConstraint(
            ["college_id"], ["colleges.id"], name="fk_audit_logs_college"
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_audit_logs_actor",
        ),
    )
    op.create_index(
        "ix_audit_logs_college_time",
        "audit_logs",
        ["college_id", sa.text("occurred_at DESC")],
    )

    role_table = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_assignable", sa.Boolean()),
    )
    op.bulk_insert(
        role_table,
        [
            {
                "id": ROLE_IDS["STUDENT"],
                "code": "STUDENT",
                "name": "Student",
                "description": "Own profile and performance.",
                "is_assignable": True,
            },
            {
                "id": ROLE_IDS["MENTOR"],
                "code": "MENTOR",
                "name": "Mentor",
                "description": "Reviews profiles in assigned batches.",
                "is_assignable": True,
            },
            {
                "id": ROLE_IDS["PLACEMENT_COORDINATOR"],
                "code": "PLACEMENT_COORDINATOR",
                "name": "Placement Coordinator",
                "description": "College-wide rankings and shortlists.",
                "is_assignable": True,
            },
            {
                "id": ROLE_IDS["COLLEGE_ADMIN"],
                "code": "COLLEGE_ADMIN",
                "name": "College Administrator",
                "description": "Manages institution records.",
                "is_assignable": True,
            },
            {
                "id": ROLE_IDS["SUPER_ADMIN"],
                "code": "SUPER_ADMIN",
                "name": "Platform Super Administrator",
                "description": "Provisions college tenants.",
                "is_assignable": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_college_time", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(
        "uq_mentor_batch_assignments_active", table_name="mentor_batch_assignments"
    )
    op.drop_table("mentor_batch_assignments")
    op.drop_table("mentors")
    op.drop_index("ix_students_status", table_name="students")
    op.drop_index("ix_students_scope", table_name="students")
    op.drop_index("uq_students_register", table_name="students")
    op.drop_table("students")
    op.drop_table("batches")
    op.drop_table("departments")
    op.drop_index("uq_user_roles_active", table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_table("user_sessions")
    op.drop_index("uq_users_oidc_identity", table_name="users")
    op.drop_index("uq_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("colleges")
