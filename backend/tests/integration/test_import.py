"""Integration tests for CSV/Excel student import (FR-06, FR-10)."""

from __future__ import annotations

import io

from openpyxl import Workbook

from tests.integration.conftest import World


def csv_upload(rows: str) -> dict[str, tuple[str, bytes, str]]:
    return {"file": ("students.csv", rows.encode("utf-8"), "text/csv")}


HEADER = (
    "register_number,display_name,institutional_email,"
    "department_code,batch_name,admission_year,current_year,temporary_password\n"
)


def test_import_creates_valid_rows_and_reports_problems(login, world: World) -> None:
    admin_client = login("TENA", world.a.admin_email)
    body = HEADER + (
        "TENA-NEW-001,New Student,newstudent@tena.example.edu,CSE,2023-2027,2023,3,"
        "DevPassw0rd!2026\n"
        "TENA-NEW-002,Bad Department,baddept@tena.example.edu,ZZZ,2023-2027,,,\n"
        "TENA-CSE-001,Duplicate Register,dupregister@tena.example.edu,CSE,2023-2027,,,\n"
        "TENA-NEW-003,Duplicate Email,student2023@tena.example.edu,CSE,2023-2027,,,\n"
    )

    response = admin_client.post(
        "/api/v1/admin/students/import", files=csv_upload(body)
    )

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["created"] == 1
    assert result["failed"] == 2
    assert result["skipped"] == 1
    messages = " ".join(error["message"] for error in result["errors"])
    assert "unknown department_code ZZZ" in messages
    assert "already exists" in messages

    new_student = login("TENA", "newstudent@tena.example.edu", "DevPassw0rd!2026")
    profile = new_student.get("/api/v1/students/me")
    assert profile.status_code == 200
    assert profile.json()["register_number"] == "TENA-NEW-001"

    audit = admin_client.get("/api/v1/admin/audit-logs")
    assert "students.imported" in [entry["action"] for entry in audit.json()["items"]]


def test_import_accepts_xlsx(login, world: World) -> None:
    admin_client = login("TENA", world.a.admin_email)
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(
        [
            "register_number",
            "display_name",
            "institutional_email",
            "department_code",
            "batch_name",
        ]
    )
    sheet.append(
        ["TENA-XLSX-001", "Excel Student", "excelstudent@tena.example.edu", "ECE", "2023-2027"]
    )
    buffer = io.BytesIO()
    workbook.save(buffer)

    response = admin_client.post(
        "/api/v1/admin/students/import",
        files={
            "file": (
                "students.xlsx",
                buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["created"] == 1


def test_import_rejects_missing_columns(login, world: World) -> None:
    admin_client = login("TENA", world.a.admin_email)

    response = admin_client.post(
        "/api/v1/admin/students/import",
        files=csv_upload("register_number,display_name\nA-1,A Student\n"),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_columns"


def test_import_requires_college_admin(login, world: World) -> None:
    mentor_client = login("TENA", world.a.mentor_email)

    response = mentor_client.post(
        "/api/v1/admin/students/import", files=csv_upload(HEADER)
    )

    assert response.status_code == 403
