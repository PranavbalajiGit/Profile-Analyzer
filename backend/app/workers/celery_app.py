"""Celery application for asynchronous work.

Milestone 1 only proves the wiring; sync/scoring/ranking tasks arrive in later
milestones.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "profile_analyzer",
    broker=settings.broker_url,
    backend=settings.result_backend_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_default_queue="default",
    task_routes={
        "app.workers.tasks.sync_*": {"queue": "sync"},
        "app.workers.tasks.score_*": {"queue": "scoring"},
        "app.workers.tasks.rank_*": {"queue": "ranking"},
    },
)

# Populated in later milestones; kept explicit so Beat has a stable schedule key.
celery_app.conf.beat_schedule = {}

from app.workers import tasks  # noqa: E402,F401  (register tasks)
