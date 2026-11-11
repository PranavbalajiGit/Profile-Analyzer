"""Create deterministic synthetic development data.

Run from the ``backend`` directory after ``alembic upgrade head``::

    python scripts/seed_dev.py

The script is idempotent per college (identified by ``short_code``) and uses the
schema-owner connection so it can provision tenants deliberately. It never
contains real student data and must never be pointed at production.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.core.tenant import apply_system, apply_tenant  # noqa: E402
from app.database.session import get_engine  # noqa: E402
from app.modules.identity.models import College, Role, User, UserRole  # noqa: E402
from app.modules.institution.models import (  # noqa: E402
    Batch,
    Department,
    Mentor,
    MentorBatchAssignment,
    Student,
)

DEV_PASSWORD = "DevPassw0rd!2026"

DEPARTMENTS = (
    ("CSE", "Computer Science and Engineering"),
    ("ECE", "Electronics and Communication Engineering"),
    ("ME", "Mechanical Engineering"),
)

BATCHES = (
    ("2023-2027", 2023, 2027),
    ("2024-2028", 2024, 2028),
)

COLLEGES = (
    {
        "short_code": "NFIT",
        "name": "Northfield Institute of Technology",
        "domain": "northfield.example.edu",
        "timezone": "Asia/Kolkata",
    },
    {
        "short_code": "WCET",
        "name": "Westmere College of Engineering and Technology",
        "domain": "westmere.example.edu",
        "timezone": "Asia/Kolkata",
    },
)


def _role(session: Session, code: str) -> Role:
    role = session.scalar(select(Role).where(Role.code == code))
    if role is None:
        raise SystemExit(f"Role {code} is missing; run 'alembic upgrade head' first.")
    return role


def _add_user(
    session: Session,
    *,
    college: College,
    email: str,
    display_name: str,
    roles: tuple[str, ...],
    password: str = DEV_PASSWORD,
) -> User:
    user = User(
        college_id=college.id,
        institutional_email=email,
        display_name=display_name,
        password_hash=hash_password(password),
        status="ACTIVE",
    )
    session.add(user)
    session.flush()
    for code in roles:
        session.add(
            UserRole(
                college_id=college.id,
                user_id=user.id,
                role_id=_role(session, code).id,
                granted_by=None,
            )
        )
    return user


def _seed_college(session: Session, spec: dict[str, str]) -> bool:
    existing = session.scalar(
        select(College).where(College.short_code == spec["short_code"])
    )
    if existing is not None:
        print(f"  {spec['short_code']}: already seeded, skipping")
        return False

    apply_system(session)
    college = College(
        name=spec["name"],
        short_code=spec["short_code"],
        domain=spec["domain"],
        timezone=spec["timezone"],
        status="ACTIVE",
    )
    session.add(college)
    session.flush()
    apply_tenant(session, college.id)

    prefix = spec["short_code"].lower()
    departments: dict[str, Department] = {}
    for code, name in DEPARTMENTS:
        department = Department(
            college_id=college.id, code=code, name=name, status="ACTIVE"
        )
        session.add(department)
        departments[code] = department
    session.flush()

    batches: dict[tuple[str, str], Batch] = {}
    for department_code, department in departments.items():
        for name, start_year, end_year in BATCHES:
            batch = Batch(
                college_id=college.id,
                department_id=department.id,
                name=name,
                start_year=start_year,
                end_year=end_year,
                status="ACTIVE",
            )
            session.add(batch)
            batches[(department_code, name)] = batch
    session.flush()

    admin = _add_user(
        session,
        college=college,
        email=f"admin@{prefix}.example.edu",
        display_name=f"{spec['short_code']} College Admin",
        roles=("COLLEGE_ADMIN",),
    )
    _add_user(
        session,
        college=college,
        email=f"placement@{prefix}.example.edu",
        display_name=f"{spec['short_code']} Placement Coordinator",
        roles=("PLACEMENT_COORDINATOR",),
    )

    mentor_specs = (
        ("mentor.cse", "CSE", "CSE Mentor", "CSE", "2023-2027"),
        ("mentor.ece", "ECE", "ECE Mentor", "ECE", "2023-2027"),
    )
    for local_part, department_code, display_name, assigned_department, batch_name in mentor_specs:
        user = _add_user(
            session,
            college=college,
            email=f"{local_part}@{prefix}.example.edu",
            display_name=display_name,
            roles=("MENTOR",),
        )
        mentor = Mentor(
            college_id=college.id,
            user_id=user.id,
            employee_code=f"{spec['short_code']}-{department_code}-M01",
            department_id=departments[assigned_department].id,
            status="ACTIVE",
        )
        session.add(mentor)
        session.flush()
        session.add(
            MentorBatchAssignment(
                college_id=college.id,
                mentor_id=mentor.id,
                batch_id=batches[(assigned_department, batch_name)].id,
                assigned_by=admin.id,
            )
        )

    student_specs = (
        ("student1", "CSE", "2023-2027", "Aarav Synthetic"),
        ("student2", "CSE", "2024-2028", "Bhavna Synthetic"),
        ("student3", "ECE", "2023-2027", "Chirag Synthetic"),
    )
    for local_part, department_code, batch_name, display_name in student_specs:
        user = _add_user(
            session,
            college=college,
            email=f"{local_part}@{prefix}.example.edu",
            display_name=display_name,
            roles=("STUDENT",),
        )
        session.add(
            Student(
                college_id=college.id,
                user_id=user.id,
                register_number=f"{spec['short_code']}-{department_code}-{local_part[-1].zfill(3)}",
                department_id=departments[department_code].id,
                batch_id=batches[(department_code, batch_name)].id,
                admission_year=int(batch_name.split("-")[0]),
                current_year=3,
                status="ACTIVE",
            )
        )

    session.commit()
    print(f"  {spec['short_code']}: seeded")
    return True


def _seed_platform_admin(session: Session, college: College) -> None:
    """Give the development database a platform super administrator.

    The role is attached to a home college because every user row is
    tenant-scoped. It is created outside the per-college early return so it is
    also added when the colleges already exist.
    """

    email = "superadmin@platform.example.edu"
    apply_system(session)
    existing = session.scalar(select(User.id).where(User.institutional_email == email))
    if existing is not None:
        print("  platform super admin: already seeded, skipping")
        return

    apply_tenant(session, college.id)
    _add_user(
        session,
        college=college,
        email=email,
        display_name="Platform Super Admin",
        roles=("SUPER_ADMIN",),
    )
    session.commit()
    print("  platform super admin: seeded")


def main() -> int:
    settings = get_settings()
    if settings.is_production:
        raise SystemExit("Refusing to seed production data.")

    engine = get_engine(
        settings.model_copy(update={"database_url": settings.migration_database_url})
    )
    print(f"Seeding synthetic data into {settings.migration_database_url}")
    with Session(engine) as session:
        created = 0
        for spec in COLLEGES:
            if _seed_college(session, spec):
                created += 1

        nfit = session.scalar(select(College).where(College.short_code == "NFIT"))
        if nfit is not None:
            _seed_platform_admin(session, nfit)

    print()
    print(f"Colleges created: {created}")
    print(f"Development password for every seeded account: {DEV_PASSWORD}")
    print("Accounts (per college, replace <code> with nfit or wcet):")
    print("  admin@<code>.example.edu       COLLEGE_ADMIN")
    print("  placement@<code>.example.edu   PLACEMENT_COORDINATOR")
    print("  mentor.cse@<code>.example.edu  MENTOR (CSE 2023-2027)")
    print("  mentor.ece@<code>.example.edu  MENTOR (ECE 2023-2027)")
    print("  student1..3@<code>.example.edu STUDENT")
    print("Platform (sign in with institution code NFIT):")
    print("  superadmin@platform.example.edu SUPER_ADMIN")
    print()
    print("Sign in with the institution code NFIT or WCET.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
