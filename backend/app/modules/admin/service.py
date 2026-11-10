"""Institution administration services (FR-06, FR-09, FR-10, FR-59)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.audit import service as audit
from app.modules.auth.identity import Identity
from app.modules.auth.service import normalize_email, set_password
from app.modules.identity.models import College, User, UserSession
from app.modules.identity.roles import assign_role
from app.modules.identity.schemas import (
    AssignmentCreate,
    BatchCreate,
    BatchOut,
    CollegeCreate,
    CollegeOut,
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
    MentorCreate,
    MentorOut,
)
from app.modules.institution.models import (
    Batch,
    Department,
    Mentor,
    MentorBatchAssignment,
)

ROLE_STUDENT = "STUDENT"
ROLE_MENTOR = "MENTOR"


def _audit(
    session: Session,
    identity: Identity,
    *,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    details: dict | None = None,
) -> None:
    audit.record(
        session,
        college_id=identity.college_id,
        actor_user_id=identity.user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )


# --- Colleges (platform super administration) -------------------------------


def list_colleges(session: Session, identity: Identity) -> list[CollegeOut]:
    if not identity.has_role("SUPER_ADMIN"):
        raise PermissionDeniedError()
    from app.core.tenant import apply_system

    apply_system(session)
    rows = session.scalars(select(College).order_by(College.name)).all()
    return [CollegeOut.model_validate(row) for row in rows]


def create_college(
    session: Session, identity: Identity, payload: CollegeCreate
) -> CollegeOut:
    if not identity.has_role("SUPER_ADMIN"):
        raise PermissionDeniedError()

    from app.core.tenant import apply_system, apply_tenant

    apply_system(session)
    college = College(
        name=payload.name.strip(),
        short_code=payload.short_code.strip().upper(),
        domain=payload.domain.strip().lower() if payload.domain else None,
        timezone=payload.timezone,
        status="ACTIVE",
    )
    try:
        with session.begin_nested():
            session.add(college)
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("A college with that short code or domain already exists.") from exc

    apply_tenant(session, college.id)
    audit.record(
        session,
        college_id=college.id,
        actor_user_id=None,
        action="college.created",
        entity_type="college",
        entity_id=college.id,
        details={"short_code": college.short_code, "by_user_id": str(identity.user_id)},
    )
    session.commit()
    return CollegeOut.model_validate(college)


# --- Departments -------------------------------------------------------------


def list_departments(session: Session, identity: Identity) -> list[DepartmentOut]:
    rows = session.scalars(
        select(Department)
        .where(Department.college_id == identity.college_id, Department.deleted_at.is_(None))
        .order_by(Department.code)
    ).all()
    return [DepartmentOut.model_validate(row) for row in rows]


def create_department(
    session: Session, identity: Identity, payload: DepartmentCreate
) -> DepartmentOut:
    department = Department(
        college_id=identity.college_id,
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
        status="ACTIVE",
    )
    try:
        with session.begin_nested():
            session.add(department)
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("A department with that code already exists.") from exc

    _audit(
        session,
        identity,
        action="department.created",
        entity_type="department",
        entity_id=department.id,
        details={"code": department.code},
    )
    session.commit()
    return DepartmentOut.model_validate(department)


def update_department(
    session: Session,
    identity: Identity,
    department_id: UUID,
    payload: DepartmentUpdate,
) -> DepartmentOut:
    department = session.scalar(
        select(Department).where(
            Department.id == department_id,
            Department.college_id == identity.college_id,
            Department.deleted_at.is_(None),
        )
    )
    if department is None:
        raise NotFoundError("Department not found.")
    if payload.name is not None:
        department.name = payload.name.strip()
    if payload.status is not None:
        department.status = payload.status
    _audit(
        session,
        identity,
        action="department.updated",
        entity_type="department",
        entity_id=department.id,
        details=payload.model_dump(exclude_none=True),
    )
    session.commit()
    return DepartmentOut.model_validate(department)


# --- Batches -----------------------------------------------------------------


def _get_department(session: Session, college_id: UUID, department_id: UUID) -> Department:
    department = session.scalar(
        select(Department).where(
            Department.id == department_id,
            Department.college_id == college_id,
            Department.deleted_at.is_(None),
        )
    )
    if department is None:
        raise NotFoundError("Department not found.")
    return department


def list_batches(
    session: Session, identity: Identity, department_id: UUID | None = None
) -> list[BatchOut]:
    statement = select(Batch).where(
        Batch.college_id == identity.college_id, Batch.deleted_at.is_(None)
    )
    if department_id is not None:
        statement = statement.where(Batch.department_id == department_id)
    rows = session.scalars(statement.order_by(Batch.start_year, Batch.name)).all()
    return [BatchOut.model_validate(row) for row in rows]


def create_batch(session: Session, identity: Identity, payload: BatchCreate) -> BatchOut:
    _get_department(session, identity.college_id, payload.department_id)
    if payload.end_year < payload.start_year:
        raise ConflictError("end_year must be greater than or equal to start_year.")

    batch = Batch(
        college_id=identity.college_id,
        department_id=payload.department_id,
        name=payload.name.strip(),
        start_year=payload.start_year,
        end_year=payload.end_year,
        status="ACTIVE",
    )
    try:
        with session.begin_nested():
            session.add(batch)
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("A batch with that name already exists in the department.") from exc

    _audit(
        session,
        identity,
        action="batch.created",
        entity_type="batch",
        entity_id=batch.id,
        details={"name": batch.name, "start_year": batch.start_year, "end_year": batch.end_year},
    )
    session.commit()
    return BatchOut.model_validate(batch)


# --- Mentors and assignments -------------------------------------------------


def list_mentors(session: Session, identity: Identity) -> list[MentorOut]:
    rows = session.execute(
        select(Mentor, User)
        .join(User, User.id == Mentor.user_id)
        .where(Mentor.college_id == identity.college_id, Mentor.deleted_at.is_(None))
        .order_by(User.display_name)
    ).all()
    return [
        MentorOut(
            id=mentor.id,
            user_id=mentor.user_id,
            email=user.institutional_email,
            display_name=user.display_name,
            employee_code=mentor.employee_code,
            department_id=mentor.department_id,
            status=mentor.status,
        )
        for mentor, user in rows
    ]


def create_mentor(
    session: Session, identity: Identity, payload: MentorCreate
) -> MentorOut:
    email = normalize_email(payload.email)
    existing = session.scalar(
        select(User).where(
            User.college_id == identity.college_id,
            func.lower(User.institutional_email) == email,
        )
    )
    if existing is not None:
        raise ConflictError("A user with that institutional email already exists.")
    if payload.department_id is not None:
        _get_department(session, identity.college_id, payload.department_id)

    user = User(
        college_id=identity.college_id,
        institutional_email=email,
        display_name=payload.display_name.strip(),
        status="ACTIVE" if payload.temporary_password else "INVITED",
    )
    mentor = Mentor(
        college_id=identity.college_id,
        employee_code=payload.employee_code.strip(),
        department_id=payload.department_id,
        status="ACTIVE",
    )

    try:
        with session.begin_nested():
            session.add(user)
            session.flush()
            if payload.temporary_password:
                set_password(session, user, payload.temporary_password)
            mentor.user_id = user.id
            session.add(mentor)
            session.flush()
            assign_role(
                session,
                college_id=identity.college_id,
                user_id=user.id,
                role_code=ROLE_MENTOR,
                granted_by=identity.user_id,
            )
    except IntegrityError as exc:
        raise ConflictError("That employee code or email is already in use.") from exc

    _audit(
        session,
        identity,
        action="mentor.created",
        entity_type="mentor",
        entity_id=mentor.id,
        details={"email": email, "employee_code": mentor.employee_code},
    )
    session.commit()
    return MentorOut(
        id=mentor.id,
        user_id=user.id,
        email=user.institutional_email,
        display_name=user.display_name,
        employee_code=mentor.employee_code,
        department_id=mentor.department_id,
        status=mentor.status,
    )


def assign_mentor(
    session: Session, identity: Identity, payload: AssignmentCreate
) -> MentorBatchAssignment:
    mentor = session.scalar(
        select(Mentor).where(
            Mentor.id == payload.mentor_id,
            Mentor.college_id == identity.college_id,
            Mentor.deleted_at.is_(None),
        )
    )
    if mentor is None:
        raise NotFoundError("Mentor not found.")
    batch = session.scalar(
        select(Batch).where(
            Batch.id == payload.batch_id,
            Batch.college_id == identity.college_id,
            Batch.deleted_at.is_(None),
        )
    )
    if batch is None:
        raise NotFoundError("Batch not found.")

    existing = session.scalar(
        select(MentorBatchAssignment).where(
            MentorBatchAssignment.college_id == identity.college_id,
            MentorBatchAssignment.mentor_id == mentor.id,
            MentorBatchAssignment.batch_id == batch.id,
            MentorBatchAssignment.revoked_at.is_(None),
        )
    )
    if existing is not None:
        raise ConflictError("The mentor is already assigned to that batch.")

    assignment = MentorBatchAssignment(
        college_id=identity.college_id,
        mentor_id=mentor.id,
        batch_id=batch.id,
        assigned_by=identity.user_id,
    )
    try:
        with session.begin_nested():
            session.add(assignment)
            session.flush()
    except IntegrityError as exc:
        raise ConflictError("The mentor is already assigned to that batch.") from exc

    _audit(
        session,
        identity,
        action="mentor.assigned",
        entity_type="mentor_batch_assignment",
        entity_id=assignment.id,
        details={"mentor_id": str(mentor.id), "batch_id": str(batch.id)},
    )
    session.commit()
    return assignment


# --- Users and audit ---------------------------------------------------------


def update_user_status(
    session: Session, identity: Identity, user_id: UUID, status: str
) -> None:
    user = session.scalar(
        select(User).where(
            User.id == user_id,
            User.college_id == identity.college_id,
            User.deleted_at.is_(None),
        )
    )
    if user is None:
        raise NotFoundError("User not found.")
    if user.id == identity.user_id and status != "ACTIVE":
        raise ConflictError("You cannot deactivate your own account.")

    previous = user.status
    user.status = status
    if status != "ACTIVE":
        session.execute(
            update(UserSession)
            .where(
                UserSession.college_id == identity.college_id,
                UserSession.user_id == user.id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )

    _audit(
        session,
        identity,
        action="user.status_changed",
        entity_type="user",
        entity_id=user.id,
        details={"from": previous, "to": status},
    )
    session.commit()


def list_audit_logs(
    session: Session, identity: Identity, page: int, page_size: int
) -> list:
    from app.modules.audit.models import AuditLog

    return list(
        session.scalars(
            select(AuditLog)
            .where(AuditLog.college_id == identity.college_id)
            .order_by(AuditLog.occurred_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )


def count_audit_logs(session: Session, identity: Identity) -> int:
    from app.modules.audit.models import AuditLog

    return int(
        session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.college_id == identity.college_id)
        )
        or 0
    )
