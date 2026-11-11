"""Student endpoints (FR-10, FR-11)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.permissions import RoleCode, require_roles
from app.core.schemas import Page
from app.database.session import get_db
from app.modules.auth.identity import Identity
from app.modules.identity.schemas import StudentOut, StudentUpdate
from app.modules.students import service

router = APIRouter(prefix="/students", tags=["students"])

DbSession = Annotated[Session, Depends(get_db)]
StudentUser = Annotated[Identity, Depends(require_roles(RoleCode.STUDENT))]
CAN_LIST_STUDENTS = require_roles(
    RoleCode.MENTOR,
    RoleCode.PLACEMENT_COORDINATOR,
    RoleCode.COLLEGE_ADMIN,
    RoleCode.SUPER_ADMIN,
)
StudentLister = Annotated[Identity, Depends(CAN_LIST_STUDENTS)]


@router.get("/me", response_model=StudentOut)
def my_student(
    identity: StudentUser,
    db: DbSession,
) -> StudentOut:
    return service.get_my_student(db, identity)


@router.patch("/me", response_model=StudentOut)
def update_my_student(
    payload: StudentUpdate,
    identity: StudentUser,
    db: DbSession,
) -> StudentOut:
    return service.update_me(db, identity, payload)


@router.get("", response_model=Page[StudentOut])
def list_students(
    identity: StudentLister,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    department_id: UUID | None = None,
    batch_id: UUID | None = None,
    status: Annotated[str | None, Query(max_length=20)] = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
) -> Page[StudentOut]:
    items, total = service.list_students(
        db,
        identity,
        page=page,
        page_size=page_size,
        department_id=department_id,
        batch_id=batch_id,
        status=status,
        search=search,
    )
    return Page(items=items, page=page, page_size=page_size, total=total)
