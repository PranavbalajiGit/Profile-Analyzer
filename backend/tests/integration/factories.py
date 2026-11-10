"""Factories for synthetic integration-test records (no real student data)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.identity.models import College, Role, User, UserRole
from app.modules.institution.models import (
    Batch,
    Department,
    Mentor,
    MentorBatchAssignment,
    Student,
)

TEST_PASSWORD = "DevPassw0rd!2026"


def make_college(
    session: Session,
    *,
    short_code: str,
    name: str | None = None,
    domain: str | None = None,
) -> College:
    college = College(
        name=name or f"{short_code} Institute",
        short_code=short_code,
        domain=domain or f"{short_code.lower()}.example.edu",
        status="ACTIVE",
    )
    session.add(college)
    session.flush()
    return college


def make_department(session: Session, college: College, code: str) -> Department:
    department = Department(
        college_id=college.id,
        code=code,
        name=f"{code} Department",
        status="ACTIVE",
    )
    session.add(department)
    session.flush()
    return department


def make_batch(
    session: Session,
    college: College,
    department: Department,
    *,
    name: str,
    start_year: int,
    end_year: int,
) -> Batch:
    batch = Batch(
        college_id=college.id,
        department_id=department.id,
        name=name,
        start_year=start_year,
        end_year=end_year,
        status="ACTIVE",
    )
    session.add(batch)
    session.flush()
    return batch


def _role(session: Session, code: str) -> Role:
    role = session.scalar(select(Role).where(Role.code == code))
    if role is None:
        raise AssertionError(f"Role {code} was not seeded by the migration")
    return role


def make_user(
    session: Session,
    college: College,
    *,
    email: str,
    roles: tuple[str, ...],
    display_name: str = "Synthetic Person",
    password: str | None = TEST_PASSWORD,
    status: str = "ACTIVE",
) -> User:
    user = User(
        college_id=college.id,
        institutional_email=email,
        display_name=display_name,
        password_hash=hash_password(password) if password else None,
        status=status,
    )
    session.add(user)
    session.flush()
    for code in roles:
        session.add(
            UserRole(
                college_id=college.id,
                user_id=user.id,
                role_id=_role(session, code).id,
            )
        )
    session.flush()
    return user


def make_student(
    session: Session,
    college: College,
    department: Department,
    batch: Batch,
    *,
    email: str,
    register_number: str,
) -> tuple[User, Student]:
    user = make_user(session, college, email=email, roles=("STUDENT",))
    student = Student(
        college_id=college.id,
        user_id=user.id,
        register_number=register_number,
        department_id=department.id,
        batch_id=batch.id,
        admission_year=batch.start_year,
        current_year=3,
        status="ACTIVE",
    )
    session.add(student)
    session.flush()
    return user, student


def make_mentor(
    session: Session,
    college: College,
    department: Department,
    *,
    email: str,
    employee_code: str,
    batches: tuple[Batch, ...] = (),
) -> tuple[User, Mentor]:
    user = make_user(session, college, email=email, roles=("MENTOR",))
    mentor = Mentor(
        college_id=college.id,
        user_id=user.id,
        employee_code=employee_code,
        department_id=department.id,
        status="ACTIVE",
    )
    session.add(mentor)
    session.flush()
    for batch in batches:
        session.add(
            MentorBatchAssignment(
                college_id=college.id,
                mentor_id=mentor.id,
                batch_id=batch.id,
            )
        )
    session.flush()
    return user, mentor
