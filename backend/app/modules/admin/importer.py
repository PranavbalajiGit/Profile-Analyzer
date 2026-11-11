"""CSV/Excel student provisioning (FR-06, FR-10).

Import runs inside one tenant transaction. Each row is a SAVEPOINT so a bad row
is reported without discarding valid rows. Client-supplied tenant IDs are never
read; the tenant comes from the authenticated identity.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.modules.admin.service import ROLE_STUDENT
from app.modules.audit import service as audit
from app.modules.auth.identity import Identity
from app.modules.auth.service import normalize_email, set_password
from app.modules.identity.models import User
from app.modules.identity.roles import assign_role
from app.modules.identity.schemas import ImportResult, ImportRowError
from app.modules.institution.models import Batch, Department, Student

REQUIRED_COLUMNS = (
    "register_number",
    "display_name",
    "institutional_email",
    "department_code",
    "batch_name",
)
OPTIONAL_COLUMNS = ("admission_year", "current_year", "temporary_password")
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xlsm"}


def _normalize_header(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _parse_csv(content: bytes) -> list[dict[str, str]]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [
        {_normalize_header(key): str(value or "").strip() for key, value in row.items()}
        for row in reader
    ]


def _parse_excel(content: bytes) -> list[dict[str, str]]:
    workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    sheet = workbook[workbook.sheetnames[0]]
    rows = sheet.iter_rows(values_only=True)
    try:
        header = [_normalize_header(cell) for cell in next(rows)]
    except StopIteration:
        return []
    parsed: list[dict[str, str]] = []
    for values in rows:
        parsed.append(
            {
                header[index]: ("" if value is None else str(value).strip())
                for index, value in enumerate(values)
                if index < len(header) and header[index]
            }
        )
    return parsed


def parse_upload(filename: str, content: bytes) -> list[dict[str, str]]:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise AppError(
            "Upload a .csv, .xlsx or .xlsm file.",
            code="unsupported_file",
            status_code=400,
        )
    if not content:
        raise AppError("The uploaded file is empty.", code="empty_file", status_code=400)

    rows = _parse_csv(content) if suffix == ".csv" else _parse_excel(content)
    if not rows:
        raise AppError("The uploaded file has no data rows.", code="empty_file", status_code=400)

    missing = [column for column in REQUIRED_COLUMNS if column not in rows[0]]
    if missing:
        raise AppError(
            "Missing required columns: " + ", ".join(missing),
            code="invalid_columns",
            status_code=400,
        )
    return rows


def _optional_year(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("must be a whole number") from exc


def import_students(
    session: Session,
    identity: Identity,
    rows: list[dict[str, str]],
) -> ImportResult:
    departments = {
        row.code.upper(): row
        for row in session.scalars(
            select(Department).where(
                Department.college_id == identity.college_id,
                Department.deleted_at.is_(None),
            )
        ).all()
    }
    batches = {
        (row.department_id, row.name.strip().lower()): row
        for row in session.scalars(
            select(Batch).where(
                Batch.college_id == identity.college_id,
                Batch.deleted_at.is_(None),
            )
        ).all()
    }
    existing_registers = {
        value.lower()
        for value in session.scalars(
            select(Student.register_number).where(Student.college_id == identity.college_id)
        ).all()
    }
    existing_emails = {
        value.lower()
        for value in session.scalars(
            select(User.institutional_email).where(User.college_id == identity.college_id)
        ).all()
    }

    errors: list[ImportRowError] = []
    created = 0
    skipped = 0

    for index, row in enumerate(rows, start=2):
        register_number = (row.get("register_number") or "").strip()
        display_name = (row.get("display_name") or "").strip()
        email = normalize_email(row.get("institutional_email") or "")
        department_code = (row.get("department_code") or "").strip().upper()
        batch_name = (row.get("batch_name") or "").strip()

        missing = [
            name
            for name, value in (
                ("register_number", register_number),
                ("display_name", display_name),
                ("institutional_email", email),
                ("department_code", department_code),
                ("batch_name", batch_name),
            )
            if not value
        ]
        if missing:
            errors.append(ImportRowError(row=index, message="missing " + ", ".join(missing)))
            continue

        if not EMAIL_PATTERN.match(email):
            errors.append(ImportRowError(row=index, message="invalid institutional_email"))
            continue

        department = departments.get(department_code)
        if department is None:
            errors.append(
                ImportRowError(row=index, message=f"unknown department_code {department_code}")
            )
            continue

        batch = batches.get((department.id, batch_name.lower()))
        if batch is None:
            errors.append(
                ImportRowError(
                    row=index,
                    message=f"unknown batch_name {batch_name} for {department_code}",
                )
            )
            continue

        if register_number.lower() in existing_registers:
            skipped += 1
            continue
        if email in existing_emails:
            errors.append(
                ImportRowError(row=index, message="institutional_email already exists")
            )
            continue

        try:
            admission_year = _optional_year(row.get("admission_year") or "")
            current_year = _optional_year(row.get("current_year") or "")
        except ValueError as exc:
            errors.append(ImportRowError(row=index, message=str(exc)))
            continue

        try:
            with session.begin_nested():
                user = User(
                    college_id=identity.college_id,
                    institutional_email=email,
                    display_name=display_name,
                    status="ACTIVE",
                )
                session.add(user)
                session.flush()

                temporary_password = row.get("temporary_password") or ""
                if temporary_password:
                    set_password(session, user, temporary_password)

                student = Student(
                    college_id=identity.college_id,
                    user_id=user.id,
                    register_number=register_number,
                    department_id=department.id,
                    batch_id=batch.id,
                    admission_year=admission_year,
                    current_year=current_year,
                    status="ACTIVE",
                )
                session.add(student)
                session.flush()

                assign_role(
                    session,
                    college_id=identity.college_id,
                    user_id=user.id,
                    role_code=ROLE_STUDENT,
                    granted_by=identity.user_id,
                )
        except IntegrityError:
            errors.append(
                ImportRowError(row=index, message="duplicate register number or email")
            )
            continue
        except AppError as exc:
            errors.append(ImportRowError(row=index, message=exc.message))
            continue

        existing_registers.add(register_number.lower())
        existing_emails.add(email)
        created += 1

    audit.record(
        session,
        college_id=identity.college_id,
        actor_user_id=identity.user_id,
        action="students.imported",
        entity_type="student_import",
        entity_id=None,
        details={"created": created, "skipped": skipped, "failed": len(errors)},
    )
    session.commit()

    return ImportResult(
        created=created,
        skipped=skipped,
        failed=len(errors),
        errors=errors,
    )
