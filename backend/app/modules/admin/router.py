"""Institution administration endpoints (FR-06, FR-09, FR-59)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.permissions import require_admin, require_super_admin
from app.core.schemas import Page
from app.database.session import get_db
from app.modules.admin import importer, service
from app.modules.auth.identity import Identity
from app.modules.identity.schemas import (
    AssignmentCreate,
    AssignmentOut,
    AuditLogOut,
    BatchCreate,
    BatchOut,
    CollegeCreate,
    CollegeOut,
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
    ImportResult,
    MentorCreate,
    MentorOut,
    UserStatusUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])

DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[Identity, Depends(require_admin)]
SuperAdminUser = Annotated[Identity, Depends(require_super_admin)]
Upload = Annotated[UploadFile, File(...)]


@router.get("/colleges", response_model=list[CollegeOut])
def list_colleges(
    identity: SuperAdminUser,
    db: DbSession,
) -> list[CollegeOut]:
    return service.list_colleges(db, identity)


@router.post("/colleges", response_model=CollegeOut, status_code=201)
def create_college(
    payload: CollegeCreate,
    identity: SuperAdminUser,
    db: DbSession,
) -> CollegeOut:
    return service.create_college(db, identity, payload)


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(
    identity: AdminUser,
    db: DbSession,
) -> list[DepartmentOut]:
    return service.list_departments(db, identity)


@router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(
    payload: DepartmentCreate,
    identity: AdminUser,
    db: DbSession,
) -> DepartmentOut:
    return service.create_department(db, identity, payload)


@router.patch("/departments/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: UUID,
    payload: DepartmentUpdate,
    identity: AdminUser,
    db: DbSession,
) -> DepartmentOut:
    return service.update_department(db, identity, department_id, payload)


@router.get("/batches", response_model=list[BatchOut])
def list_batches(
    identity: AdminUser,
    db: DbSession,
    department_id: UUID | None = None,
) -> list[BatchOut]:
    return service.list_batches(db, identity, department_id)


@router.post("/batches", response_model=BatchOut, status_code=201)
def create_batch(
    payload: BatchCreate,
    identity: AdminUser,
    db: DbSession,
) -> BatchOut:
    return service.create_batch(db, identity, payload)


@router.get("/mentors", response_model=list[MentorOut])
def list_mentors(
    identity: AdminUser,
    db: DbSession,
) -> list[MentorOut]:
    return service.list_mentors(db, identity)


@router.post("/mentors", response_model=MentorOut, status_code=201)
def create_mentor(
    payload: MentorCreate,
    identity: AdminUser,
    db: DbSession,
) -> MentorOut:
    return service.create_mentor(db, identity, payload)


@router.post("/mentors/assign", response_model=AssignmentOut, status_code=201)
def assign_mentor(
    payload: AssignmentCreate,
    identity: AdminUser,
    db: DbSession,
) -> AssignmentOut:
    assignment = service.assign_mentor(db, identity, payload)
    return AssignmentOut(
        id=assignment.id,
        mentor_id=assignment.mentor_id,
        batch_id=assignment.batch_id,
        assigned_at=assignment.assigned_at,
    )


@router.post("/students/import", response_model=ImportResult)
async def import_students(
    file: Upload,
    identity: AdminUser,
    db: DbSession,
) -> ImportResult:
    content = await file.read()
    rows = importer.parse_upload(file.filename or "", content)
    return importer.import_students(db, identity, rows)


@router.patch("/users/{user_id}/status", status_code=204)
def update_user_status(
    user_id: UUID,
    payload: UserStatusUpdate,
    identity: AdminUser,
    db: DbSession,
) -> Response:
    service.update_user_status(db, identity, user_id, payload.status)
    return Response(status_code=204)


@router.get("/audit-logs", response_model=Page[AuditLogOut])
def audit_logs(
    identity: AdminUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[AuditLogOut]:
    items = service.list_audit_logs(db, identity, page, page_size)
    total = service.count_audit_logs(db, identity)
    return Page(
        items=[AuditLogOut.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )
