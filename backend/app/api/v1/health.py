"""Health and readiness endpoints.

Liveness (``/health``) answers without touching dependencies. Readiness
(``/health/ready``) verifies the database and is allowed to report degraded.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.database.session import check_database

router = APIRouter(tags=["health"])


@router.get("")
def liveness(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/ready")
def readiness() -> JSONResponse:
    database_ok = check_database()
    return JSONResponse(
        status_code=200 if database_ok else 503,
        content={
            "status": "ok" if database_ok else "degraded",
            "checks": {"database": "ok" if database_ok else "unavailable"},
        },
    )
