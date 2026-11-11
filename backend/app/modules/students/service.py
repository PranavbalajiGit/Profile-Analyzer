"""Student self-service and authorized listing."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.permissions import is_college_wide
from app.core.tenant import apply_tenant
from app.modules.audit import service as audit
from app.modules.auth.identity import Identity
from app.modules.identity.models import User
from app.modules.identity.schemas import StudentOut, StudentUpdate
from app.modules.institution.models import Department, Student
from app.modules.students.queries import (
    count_of,
    mentor_batch_ids,
    tenant_students,
)


def _to_out(row) -> StudentOut:
    student, user, department_name, batch_name = row
    return StudentOut(
        id=student.id,
        user_id=student.user_id,
        register_number=student.register_number,
        display_name=user.display_name,
        email=user.institutional_email,
        department_id=student.department_id,
        department_name=department_name,
        batch_id=student.batch_id,
        batch_name=batch_name,
        admission_year=student.admission_year,
        current_year=student.current_year,
        status=student.status,
    )


def list_students(
    session: Session,
    identity: Identity,
    *,
    page: int,
    page_size: int,
    department_id: UUID | None = None,
    batch_id: UUID | None = None,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[StudentOut], int]:
    statement = tenant_students(identity)

    if not is_college_wide(identity):
        allowed_batches = mentor_batch_ids(session, identity)
        if not allowed_batches:
            return [], 0
        statement = statement.where(Student.batch_id.in_(allowed_batches))

    if department_id is not None:
        statement = statement.where(Student.department_id == department_id)
    if batch_id is not None:
        statement = statement.where(Student.batch_id == batch_id)
    if status:
        statement = statement.where(Student.status == status.upper())
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            User.display_name.ilike(term) | Student.register_number.ilike(term)
        )

    total = count_of(session, statement)
    rows = session.execute(
        statement.order_by(Student.register_number)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [_to_out(row) for row in rows], total


def get_my_student(session: Session, identity: Identity) -> StudentOut:
    row = session.execute(
        tenant_students(identity).where(Student.user_id == identity.user_id)
    ).first()
    if row is None:
        raise NotFoundError("No student record is linked to this account.")
    return _to_out(row)


def update_me(
    session: Session, identity: Identity, payload: StudentUpdate
) -> StudentOut:
    student = session.scalar(
        select(Student).where(
            Student.college_id == identity.college_id,
            Student.user_id == identity.user_id,
            Student.deleted_at.is_(None),
        )
    )
    if student is None:
        raise NotFoundError("No student record is linked to this account.")

    if payload.display_name is not None:
        identity.user.display_name = payload.display_name.strip()
    if payload.current_year is not None:
        student.current_year = payload.current_year

    audit.record(
        session,
        college_id=identity.college_id,
        actor_user_id=identity.user_id,
        action="student.self_updated",
        entity_type="student",
        entity_id=student.id,
        details=payload.model_dump(exclude_none=True),
    )
    session.commit()
    # The commit ended the transaction that carried the RLS ``SET LOCAL``.
    apply_tenant(session, identity.college_id)
    return get_my_student(session, identity)


def department_names(session: Session, identity: Identity) -> dict[UUID, str]:
    return {
        row.id: row.name
        for row in session.scalars(
            select(Department).where(Department.college_id == identity.college_id)
        ).all()
    }
