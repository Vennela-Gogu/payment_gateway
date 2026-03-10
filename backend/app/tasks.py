import os
import time
import random
import string
import json
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta

import requests
from sqlalchemy import text

from app.database import engine
from app.celery_app import celery_app

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() in ("1", "true", "yes")
WEBHOOK_RETRY_INTERVALS_TEST = os.getenv("WEBHOOK_RETRY_INTERVALS_TEST", "false").lower() in ("1", "true", "yes")

# Webhook retry schedule (seconds)
WEBHOOK_RETRY_SCHEDULE = [0, 60, 5 * 60, 30 * 60, 2 * 60 * 60]
WEBHOOK_RETRY_SCHEDULE_TEST = [0, 5, 10, 15, 20]


def _now_ts() -> int:
    return int(time.time())


def _gen_id(prefix: str, length: int = 16) -> str:
    return f"{prefix}_{''.join(random.choices(string.ascii_letters + string.digits, k=length))}"


def _get_webhook_retry_interval(attempt: int) -> int:
    schedule = WEBHOOK_RETRY_SCHEDULE_TEST if WEBHOOK_RETRY_INTERVALS_TEST else WEBHOOK_RETRY_SCHEDULE
    # attempt is 1-based; schedule[0] is first attempt (immediate)
    if attempt <= 1:
        return schedule[0]
    idx = min(attempt - 1, len(schedule) - 1)
    return schedule[idx]


def _make_signature(payload_str: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()


def _increment_job_counter(counter_name: str):
    try:
        import redis

        r = redis.from_url(REDIS_URL)
        r.incr(counter_name)
    except Exception:
        pass


def _decrement_job_counter(counter_name: str):
    try:
        import redis

        r = redis.from_url(REDIS_URL)
        # Prevent negative values
        pipe = r.pipeline()
        pipe.decr(counter_name)
        pipe.get(counter_name)
        _, val = pipe.execute()
        if val is not None and int(val) < 0:
            r.set(counter_name, 0)
    except Exception:
        pass


@celery_app.task(bind=True, name="process_payment_job")
def process_payment_job(self, payment_id: str):
    """Process a payment asynchronously."""
    # When the job starts executing, move it from pending -> processing
    _decrement_job_counter("jobs_pending")
    _increment_job_counter("jobs_processing")

    try:
        with engine.begin() as conn:
            payment = conn.execute(
                text("SELECT * FROM payments WHERE id = :id"),
                {"id": payment_id}
            ).fetchone()

            if not payment:
                return

            # Simulate processing delay
            if TEST_MODE:
                delay_ms = int(os.getenv("TEST_PROCESSING_DELAY", "1000"))
                time.sleep(delay_ms / 1000.0)
            else:
                time.sleep(random.uniform(5, 10))

            # Determine outcome
            if TEST_MODE:
                # In test mode, make results deterministic: UPI succeeds, card fails
                success = payment.method == "upi"
            else:
                if payment.method == "upi":
                    success = random.random() < 0.90
                else:
                    success = random.random() < 0.95

            status = "success" if success else "failed"
            update_fields = {
                "status": status,
                "updated_at": _now_ts()
            }

            if not success:
                update_fields["error_code"] = "PAYMENT_FAILED"
                update_fields["error_description"] = "Payment processing failed"

            conn.execute(
                text(
                    """
                    UPDATE payments
                    SET status = :status,
                        error_code = :error_code,
                        error_description = :error_description,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {**update_fields, "id": payment_id}
            )

            event = "payment.success" if success else "payment.failed"
            payload = {
                "event": event,
                "timestamp": _now_ts(),
                "data": {
                    "payment": {
                        "id": payment.id,
                        "order_id": payment.order_id,
                        "amount": payment.amount,
                        "currency": payment.currency,
                        "method": payment.method,
                        "vpa": getattr(payment, "vpa", None),
                        "status": status,
                        "created_at": payment.created_at,
                    }
                }
            }

            # Create webhook log record and queue delivery
            webhook_log_id = _create_webhook_log(conn, payment.merchant_id, event, payload)
            deliver_webhook_job.apply_async(args=[webhook_log_id], countdown=0)
    except Exception:
        _increment_job_counter("jobs_failed")
        raise
    finally:
        _decrement_job_counter("jobs_processing")
        _increment_job_counter("jobs_completed")


def _create_webhook_log(conn, merchant_id: str, event: str, payload: dict) -> str:
    webhook_log_id = str(uuid.uuid4())
    conn.execute(
        text(
            """
            INSERT INTO webhook_logs
            (id, merchant_id, event, payload, status, attempts, created_at)
            VALUES (:id, :merchant_id, :event, :payload, 'pending', 0, :created_at)
            """
        ),
        {
            "id": webhook_log_id,
            "merchant_id": merchant_id,
            "event": event,
            "payload": json.dumps(payload, separators=(",", ":")),
            "created_at": _now_ts(),
        }
    )
    return webhook_log_id


def enqueue_webhook_event(merchant_id: str, event: str, payload: dict):
    """Create a webhook log entry and schedule delivery."""
    with engine.begin() as conn:
        log_id = _create_webhook_log(conn, merchant_id, event, payload)

    _increment_job_counter("jobs_pending")
    deliver_webhook_job.apply_async(args=[log_id], countdown=0)

    return log_id


@celery_app.task(bind=True, name="deliver_webhook_job")
def deliver_webhook_job(self, webhook_log_id: str):
    """Deliver a webhook event with retry logic."""
    # Track job status counters
    _decrement_job_counter("jobs_pending")
    _increment_job_counter("jobs_processing")

    try:
        with engine.begin() as conn:
            log = conn.execute(
                text("SELECT * FROM webhook_logs WHERE id = :id"),
                {"id": webhook_log_id}
            ).fetchone()

            if not log:
                return

            merchant = conn.execute(
                text("SELECT * FROM merchants WHERE id = :id"),
                {"id": log.merchant_id}
            ).fetchone()

            if not merchant or not merchant.webhook_url:
                # No configured webhook URL; mark as failed
                conn.execute(
                    text("""
                    UPDATE webhook_logs SET status = 'failed', attempts = attempts + 1, last_attempt_at = :ts
                    WHERE id = :id
                    """),
                    {"ts": _now_ts(), "id": webhook_log_id}
                )
                return

            payload_obj = log.payload
            if isinstance(payload_obj, str):
                try:
                    payload_obj = json.loads(payload_obj)
                except Exception:
                    pass
            payload_str = json.dumps(payload_obj, separators=(",", ":"))
            signature = _make_signature(payload_str, merchant.webhook_secret or "")

            try:
                resp = requests.post(
                    merchant.webhook_url,
                    data=payload_str,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                    },
                    timeout=5,
                )

                success = 200 <= resp.status_code < 300
                attempts = log.attempts + 1
                now_ts = _now_ts()

                if success:
                    conn.execute(
                        text("""
                        UPDATE webhook_logs
                        SET status = 'success', attempts = :attempts, last_attempt_at = :last, response_code = :code, response_body = :body
                        WHERE id = :id
                        """),
                        {
                            "attempts": attempts,
                            "last": now_ts,
                            "code": resp.status_code,
                            "body": resp.text,
                            "id": webhook_log_id,
                        }
                    )
                    return

                # Failure path
                next_retry = None
                if attempts < 5:
                    interval = _get_webhook_retry_interval(attempts)
                    next_retry = now_ts + interval

                conn.execute(
                    text("""
                    UPDATE webhook_logs
                    SET status = :status, attempts = :attempts, last_attempt_at = :last,
                        next_retry_at = :next_retry, response_code = :code, response_body = :body
                    WHERE id = :id
                    """),
                    {
                        "status": "pending" if attempts < 5 else "failed",
                        "attempts": attempts,
                        "last": now_ts,
                        "next_retry": next_retry,
                        "code": resp.status_code,
                        "body": resp.text,
                        "id": webhook_log_id,
                    }
                )

                if attempts < 5:
                    deliver_webhook_job.apply_async(
                        args=[webhook_log_id],
                        countdown=_get_webhook_retry_interval(attempts),
                    )
            except Exception as exc:
                # Network error or timeout
                attempts = log.attempts + 1
                now_ts = _now_ts()
                next_retry = None
                if attempts < 5:
                    next_retry = now_ts + _get_webhook_retry_interval(attempts)

                conn.execute(
                    text("""
                    UPDATE webhook_logs
                    SET status = :status, attempts = :attempts, last_attempt_at = :last,
                        next_retry_at = :next_retry, response_body = :body
                    WHERE id = :id
                    """),
                    {
                        "status": "pending" if attempts < 5 else "failed",
                        "attempts": attempts,
                        "last": now_ts,
                        "next_retry": next_retry,
                        "body": str(exc),
                        "id": webhook_log_id,
                    }
                )

                if attempts < 5:
                    deliver_webhook_job.apply_async(
                        args=[webhook_log_id],
                        countdown=_get_webhook_retry_interval(attempts),
                    )
    finally:
        _decrement_job_counter("jobs_processing")
        _increment_job_counter("jobs_completed")


@celery_app.task(bind=True, name="process_refund_job")
def process_refund_job(self, refund_id: str):
    """Process a refund asynchronously."""
    # When the job starts executing, move it from pending -> processing
    _decrement_job_counter("jobs_pending")
    _increment_job_counter("jobs_processing")

    try:
        with engine.begin() as conn:
            refund = conn.execute(
                text("SELECT * FROM refunds WHERE id = :id"),
                {"id": refund_id}
            ).fetchone()

            if not refund:
                return

            payment = conn.execute(
                text("SELECT * FROM payments WHERE id = :id"),
                {"id": refund.payment_id}
            ).fetchone()

            if not payment or payment.status != "success":
                # Nothing to do; mark refund as failed
                conn.execute(
                    text("""
                    UPDATE refunds SET status = 'failed', processed_at = :ts
                    WHERE id = :id
                    """),
                    {"ts": _now_ts(), "id": refund_id}
                )
                return

            # Ensure refund amount is valid
            total_refunded = conn.execute(
                text("""
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM refunds
                    WHERE payment_id = :payment_id
                      AND status IN ('pending', 'processed')
                """),
                {"payment_id": refund.payment_id}
            ).scalar()

            if total_refunded > payment.amount:
                conn.execute(
                    text("""
                    UPDATE refunds SET status = 'failed', processed_at = :ts
                    WHERE id = :id
                    """),
                    {"ts": _now_ts(), "id": refund_id}
                )
                return

            # Simulate processing delay
            if TEST_MODE:
                time.sleep(1)
            else:
                time.sleep(random.uniform(3, 5))

            # Update refund to processed
            conn.execute(
                text("""
                UPDATE refunds
                SET status = 'processed', processed_at = :ts
                WHERE id = :id
                """),
                {"ts": _now_ts(), "id": refund_id}
            )

            # Optionally update payment if fully refunded
            if refund.amount >= payment.amount:
                conn.execute(
                    text("""
                    UPDATE payments
                    SET status = 'refunded', updated_at = :ts
                    WHERE id = :id
                    """),
                    {"ts": _now_ts(), "id": payment.id}
                )

            # Enqueue webhook
            payload = {
                "event": "refund.processed",
                "timestamp": _now_ts(),
                "data": {
                    "refund": {
                        "id": refund.id,
                        "payment_id": refund.payment_id,
                        "amount": refund.amount,
                        "reason": refund.reason,
                        "status": "processed",
                        "created_at": refund.created_at,
                        "processed_at": _now_ts(),
                    }
                }
            }
            webhook_log_id = _create_webhook_log(conn, refund.merchant_id, "refund.processed", payload)
            deliver_webhook_job.apply_async(args=[webhook_log_id], countdown=0)
    except Exception:
        _increment_job_counter("jobs_failed")
        raise
    finally:
        _decrement_job_counter("jobs_processing")
        _increment_job_counter("jobs_completed")
