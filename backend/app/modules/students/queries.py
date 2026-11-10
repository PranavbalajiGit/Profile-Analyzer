"""SQLAlchemy query helpers scoped to the current identity."""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.auth.identity import Identity
from app.modules.identity.models import User
from app.modules.institution.models import (
    Batch,
    Department,
    Mentor,
    MentorBatchAssignment,
    Student,
)


def tenant_students(identity: Identity) -> Select:
    return (
        select(Student, User, Department.name, Batch.name)
        .join(User, User.id == Student.user_id)
        .join(Department, Department.id == Student.department_id)
        .join(Batch, Batch.id == Student.batch_id)
        .where(Student.college_id == identity.college_id)
    )


def mentor_batch_ids(session: Session, identity: Identity) -> list:
    mentor = session.scalar(
        select(Mentor).where(
            Mentor.college_id == identity.college_id,
            Mentor.user_id == identity.user_id,
            Mentor.deleted_at.is_(None),
        )
    )
    if mentor is None:
        return []
    return list(
        session.scalars(
            select(MentorBatchAssignment.batch_id).where(
                MentorBatchAssignment.college_id == identity.college_id,
                MentorBatchAssignment.mentor_id == mentor.id,
                MentorBatchAssignment.revoked_at.is_(None),
            )
        ).all()
    )


def count_of(session: Session, statement: Select) -> int:
    subquery = statement.order_by(None).subquery()
    return int(session.scalar(select(func.count()).select_from(subquery)) or 0)
