"""Versioned API router (``/api/v1``)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import health
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.students.router import router as students_router

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health")
api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(admin_router)
