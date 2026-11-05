"""Worker tasks."""

from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.healthcheck", bind=True, max_retries=3)
def healthcheck(self) -> dict[str, str]:
    """Trivial idempotent task used to verify broker/worker wiring."""
    return {"status": "ok", "task_id": self.request.id or "eager"}
