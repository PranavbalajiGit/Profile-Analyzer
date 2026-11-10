"""Departments, batches, students, mentors and batch assignments."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.modules.identity.models import (
    RECORD_STATUSES,
    STUDENT_STATUSES,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    _in_list,
)


class Department(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("college_id", "code", name="uq_departments_code"),
        UniqueConstraint("id", "college_id", name="uq_departments_id_college"),
        CheckConstraint(_in_list("status", RECORD_STATUSES), name="status"),
    )

    college_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("colleges.id", name="fk_departments_college"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Batch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "batches"
    __table_args__ = (
        UniqueConstraint(
            "college_id", "department_id", "name", name="uq_batches_name"
        ),
        UniqueConstraint("id", "college_id", name="uq_batches_id_college"),
        ForeignKeyConstraint(
            ["department_id", "college_id"],
            ["departments.id", "departments.college_id"],
            name="fk_batches_department",
        ),
        CheckConstraint("end_year >= start_year", name="year_range"),
        CheckConstraint(_in_list("status", RECORD_STATUSES), name="status"),
    )

    college_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("colleges.id", name="fk_batches_college"),
        nullable=False,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Student(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("college_id", "user_id", name="uq_students_user"),
        UniqueConstraint("id", "college_id", name="uq_students_id_college"),
        Index(
            "uq_students_register",
            "college_id",
            text("lower(register_number)"),
            unique=True,
        ),
        Index("ix_students_scope", "college_id", "department_id", "batch_id"),
        Index("ix_students_status", "college_id", "status"),
        ForeignKeyConstraint(
            ["user_id", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_students_user",
        ),
        ForeignKeyConstraint(
            ["department_id", "college_id"],
            ["departments.id", "departments.college_id"],
            name="fk_students_department",
        ),
        ForeignKeyConstraint(
            ["batch_id", "college_id"],
            ["batches.id", "batches.college_id"],
            name="fk_students_batch",
        ),
        CheckConstraint(_in_list("status", STUDENT_STATUSES), name="status"),
    )

    college_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("colleges.id", name="fk_students_college"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    register_number: Mapped[str] = mapped_column(String(64), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    admission_year: Mapped[int | None] = mapped_column(Integer)
    current_year: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    profile_completeness: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Mentor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "mentors"
    __table_args__ = (
        UniqueConstraint("college_id", "employee_code", name="uq_mentors_employee"),
        UniqueConstraint("college_id", "user_id", name="uq_mentors_user"),
        UniqueConstraint("id", "college_id", name="uq_mentors_id_college"),
        ForeignKeyConstraint(
            ["user_id", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_mentors_user",
        ),
        ForeignKeyConstraint(
            ["department_id", "college_id"],
            ["departments.id", "departments.college_id"],
            name="fk_mentors_department",
        ),
        CheckConstraint(_in_list("status", RECORD_STATUSES), name="status"),
    )

    college_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("colleges.id", name="fk_mentors_college"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    employee_code: Mapped[str] = mapped_column(String(64), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MentorBatchAssignment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "mentor_batch_assignments"
    __table_args__ = (
        UniqueConstraint(
            "id", "college_id", name="uq_mentor_batch_assignments_id_college"
        ),
        Index(
            "uq_mentor_batch_assignments_active",
            "college_id",
            "mentor_id",
            "batch_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
        ForeignKeyConstraint(
            ["mentor_id", "college_id"],
            ["mentors.id", "mentors.college_id"],
            name="fk_mentor_batch_assignments_mentor",
        ),
        ForeignKeyConstraint(
            ["batch_id", "college_id"],
            ["batches.id", "batches.college_id"],
            name="fk_mentor_batch_assignments_batch",
        ),
        ForeignKeyConstraint(
            ["assigned_by", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_mentor_batch_assignments_assigned_by",
        ),
        ForeignKeyConstraint(
            ["revoked_by", "college_id"],
            ["users.id", "users.college_id"],
            name="fk_mentor_batch_assignments_revoked_by",
        ),
    )

    college_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("colleges.id", name="fk_mentor_batch_assignments_college"),
        nullable=False,
    )
    mentor_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
