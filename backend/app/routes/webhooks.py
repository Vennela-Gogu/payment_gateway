import json
import random
import string
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import text

from app.database import engine
from app.auth import authenticate
from app.tasks import deliver_webhook_job, _increment_job_counter

router = APIRouter()


def _generate_webhook_secret(length: int = 32) -> str:
    return "whsec_" + "".join(random.choices(string.ascii_letters + string.digits, k=length))


@router.get("/api/v1/webhooks")
def list_webhook_logs(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    merchant=Depends(authenticate),
):
    with engine.connect() as conn:
        total = conn.execute(
            text("SELECT COUNT(*) FROM webhook_logs WHERE merchant_id = :mid"),
            {"mid": merchant.id}
        ).scalar()

        rows = conn.execute(
            text(
                "SELECT id, event, status, attempts, created_at, last_attempt_at, response_code "
                "FROM webhook_logs WHERE merchant_id = :mid "
                "ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            ),
            {"mid": merchant.id, "limit": limit, "offset": offset},
        ).fetchall()

        data = [
            {
                "id": r.id,
                "event": r.event,
                "status": r.status,
                "attempts": r.attempts,
                "created_at": r.created_at,
                "last_attempt_at": r.last_attempt_at,
                "response_code": r.response_code,
            }
            for r in rows
        ]

    return {"data": data, "total": total, "limit": limit, "offset": offset}


@router.post("/api/v1/webhooks/{webhook_id}/retry")
def retry_webhook(webhook_id: str, merchant=Depends(authenticate)):
    with engine.begin() as conn:
        log = conn.execute(
            text("SELECT * FROM webhook_logs WHERE id = :id"),
            {"id": webhook_id},
        ).fetchone()

        if not log or log.merchant_id != merchant.id:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "WEBHOOK_NOT_FOUND",
                        "description": "Webhook log not found"
                    }
                }
            )

        conn.execute(
            text(
                """
                UPDATE webhook_logs
                SET status = 'pending', attempts = 0, next_retry_at = NULL
                WHERE id = :id
                """
            ),
            {"id": webhook_id},
        )

    _increment_job_counter("jobs_pending")
    deliver_webhook_job.apply_async(args=[webhook_id])

    return {
        "id": webhook_id,
        "status": "pending",
        "message": "Webhook retry scheduled",
    }


@router.get("/api/v1/webhooks/config")
def get_webhook_config(merchant=Depends(authenticate)):
    """Return current webhook configuration for the authenticated merchant."""
    with engine.connect() as conn:
        m = conn.execute(
            text("SELECT webhook_url, webhook_secret FROM merchants WHERE id = :id"),
            {"id": merchant.id},
        ).fetchone()

    return {
        "webhook_url": m.webhook_url,
        "webhook_secret": m.webhook_secret,
    }


@router.post("/api/v1/webhooks/config")
def update_webhook_config(
    webhook_url: str | None = Body(None),
    webhook_secret: str | None = Body(None),
    merchant=Depends(authenticate),
):
    """Update webhook URL and/or secret."""
    updates = []
    params = {"id": merchant.id}

    if webhook_url is not None:
        updates.append("webhook_url = :webhook_url")
        params["webhook_url"] = webhook_url
    if webhook_secret is not None:
        updates.append("webhook_secret = :webhook_secret")
        params["webhook_secret"] = webhook_secret

    if not updates:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "BAD_REQUEST_ERROR",
                    "description": "No configuration values provided"
                }
            }
        )

    with engine.begin() as conn:
        conn.execute(
            text(f"UPDATE merchants SET {', '.join(updates)} WHERE id = :id"),
            params,
        )

    return {"message": "Webhook configuration updated"}


@router.post("/api/v1/webhooks/secret/regenerate")
def regenerate_webhook_secret(merchant=Depends(authenticate)):
    """Generate and persist a new webhook secret."""
    secret = _generate_webhook_secret()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE merchants SET webhook_secret = :secret WHERE id = :id"),
            {"secret": secret, "id": merchant.id},
        )

    return {"webhook_secret": secret}


@router.post("/api/v1/webhooks/test")
def send_test_webhook(merchant=Depends(authenticate)):
    """Send a test webhook event to the merchant's configured webhook URL."""
    with engine.begin() as conn:
        m = conn.execute(
            text("SELECT webhook_url, webhook_secret FROM merchants WHERE id = :id"),
            {"id": merchant.id},
        ).fetchone()

    if not m or not m.webhook_url:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "BAD_REQUEST_ERROR",
                    "description": "Merchant webhook URL is not configured"
                }
            }
        )

    payload = {
        "event": "webhook.test",
        "timestamp": int(time.time()),
        "data": {"message": "Test webhook"},
    }

    # Use existing webhook log and delivery mechanism
    # Insert log and enqueue delivery
    with engine.begin() as conn:
        log_id = str(uuid.uuid4())
        conn.execute(
            text(
                "INSERT INTO webhook_logs (id, merchant_id, event, payload, status, attempts, created_at) "
                "VALUES (:id, :mid, :event, :payload, 'pending', 0, :created_at)"
            ),
            {
                "id": log_id,
                "mid": merchant.id,
                "event": "webhook.test",
                "payload": json.dumps(payload, separators=(",", ":")),
                "created_at": int(time.time()),
            },
        )

    _increment_job_counter("jobs_pending")
    deliver_webhook_job.apply_async(args=[log_id])

    return {"message": "Test webhook enqueued"}
