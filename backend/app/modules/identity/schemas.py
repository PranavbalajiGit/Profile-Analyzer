"""Institution, student and audit schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CollegeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    short_code: str = Field(min_length=2, max_length=32)
    domain: str | None = Field(default=None, max_length=255)
    timezone: str = Field(default="Asia/Kolkata", max_length=64)


class CollegeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    short_code: str
    domain: str | None
    status: str
    timezone: str


class DepartmentCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=2, max_length=200)


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    status: Literal["ACTIVE", "INACTIVE"] | None = None


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    status: str


class BatchCreate(BaseModel):
    department_id: UUID
    name: str = Field(min_length=1, max_length=100)
    start_year: int = Field(ge=1900, le=2200)
    end_year: int = Field(ge=1900, le=2300)


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    department_id: UUID
    name: str
    start_year: int
    end_year: int
    status: str


class MentorCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=2, max_length=200)
    employee_code: str = Field(min_length=1, max_length=64)
    department_id: UUID | None = None
    temporary_password: str | None = Field(default=None, max_length=256)


class MentorOut(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    display_name: str
    employee_code: str
    department_id: UUID | None
    status: str


class AssignmentCreate(BaseModel):
    mentor_id: UUID
    batch_id: UUID


class AssignmentOut(BaseModel):
    id: UUID
    mentor_id: UUID
    batch_id: UUID
    assigned_at: datetime


class StudentOut(BaseModel):
    id: UUID
    user_id: UUID
    register_number: str
    display_name: str
    email: str
    department_id: UUID
    department_name: str
    batch_id: UUID
    batch_name: str
    admission_year: int | None
    current_year: int | None
    status: str


class StudentUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=200)
    current_year: int | None = Field(default=None, ge=1, le=8)


class UserStatusUpdate(BaseModel):
    status: Literal["ACTIVE", "SUSPENDED", "GRADUATED", "DEACTIVATED"]


class ImportRowError(BaseModel):
    row: int
    message: str


class ImportResult(BaseModel):
    created: int
    skipped: int
    failed: int
    errors: list[ImportRowError]


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_user_id: UUID | None
    action: str
    entity_type: str
    entity_id: UUID | None
    details: dict[str, Any]
    request_id: str | None
    occurred_at: datetime
