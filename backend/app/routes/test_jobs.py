import os

import redis
from fastapi import APIRouter

from app.celery_app import celery_app

router = APIRouter()


@router.get("/api/v1/test/jobs/status")
def jobs_status():
    """Return approximate job queue status for automated evaluation."""
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        r = redis.from_url(redis_url)
        pending = int(r.get("jobs_pending") or 0)
        processing = int(r.get("jobs_processing") or 0)
        completed = int(r.get("jobs_completed") or 0)
        failed = int(r.get("jobs_failed") or 0)
    except Exception:
        pending = processing = completed = failed = 0

    try:
        # Check worker connectivity
        response = celery_app.control.ping(timeout=1)
        worker_status = "running" if response else "stopped"
    except Exception:
        worker_status = "stopped"

    return {
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "worker_status": worker_status,
    }
