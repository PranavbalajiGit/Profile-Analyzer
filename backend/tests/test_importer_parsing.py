"""Unit tests for CSV/Excel parsing used by student import."""

from __future__ import annotations

import io

import pytest
from openpyxl import Workbook

from app.core.exceptions import AppError
from app.modules.admin.importer import parse_upload

HEADER = "Register Number,Display Name,Institutional Email,Department Code,Batch Name"
VALID_ROW = "A-001,Aarav Synthetic,aarav@example.edu,CSE,2023-2027"


def build_csv(*rows: str) -> bytes:
    return ("\n".join((HEADER, *rows)) + "\n").encode("utf-8")


def test_csv_headers_are_normalized() -> None:
    rows = parse_upload("students.csv", build_csv(VALID_ROW))

    assert rows == [
        {
            "register_number": "A-001",
            "display_name": "Aarav Synthetic",
            "institutional_email": "aarav@example.edu",
            "department_code": "CSE",
            "batch_name": "2023-2027",
        }
    ]


def test_xlsx_is_parsed_with_the_same_shape() -> None:
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
    sheet.append(["A-002", "Bhavna Synthetic", "bhavna@example.edu", "ECE", "2024-2028"])
    buffer = io.BytesIO()
    workbook.save(buffer)

    rows = parse_upload("students.xlsx", buffer.getvalue())

    assert rows[0]["register_number"] == "A-002"
    assert rows[0]["department_code"] == "ECE"


def test_missing_required_column_is_rejected() -> None:
    content = b"register_number,display_name\nA-001,Aarav Synthetic\n"

    with pytest.raises(AppError) as excinfo:
        parse_upload("students.csv", content)

    assert excinfo.value.code == "invalid_columns"
    assert "institutional_email" in excinfo.value.message


def test_unsupported_extension_is_rejected() -> None:
    with pytest.raises(AppError) as excinfo:
        parse_upload("students.txt", b"data")

    assert excinfo.value.code == "unsupported_file"


def test_empty_upload_is_rejected() -> None:
    with pytest.raises(AppError) as excinfo:
        parse_upload("students.csv", b"")

    assert excinfo.value.code == "empty_file"
