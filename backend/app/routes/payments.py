# routes/payments.py
import json
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from sqlalchemy import text
from datetime import datetime, timedelta

from app.database import engine
from app.schemas import PaymentCreate, RefundCreate
from app.auth import authenticate
from app.tasks import (
    process_payment_job,
    process_refund_job,
    _increment_job_counter,
    enqueue_webhook_event,
)

router = APIRouter()


def _gen_id(prefix: str, length: int = 16) -> str:
    import random, string
    return prefix + "_" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=length)
    )


def _now() -> int:
    return int(datetime.utcnow().timestamp())


@router.post("/api/v1/payments", status_code=201)
def create_payment(
    payload: PaymentCreate,
    merchant=Depends(authenticate),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key")
):
    """Create a payment and enqueue processing job."""
    now = _now()

    # Idempotency check
    if idempotency_key:
        with engine.begin() as conn:
            existing = conn.execute(
                text(
                    "SELECT response, expires_at FROM idempotency_keys WHERE key = :key AND merchant_id = :mid"
                ),
                {"key": idempotency_key, "mid": merchant.id}
            ).fetchone()

            if existing:
                expires_at = existing.expires_at
                if expires_at and expires_at > now:
                    resp = existing.response
                    if isinstance(resp, str):
                        try:
                            return json.loads(resp)
                        except Exception:
                            pass
                    else:
                        return resp

                # expired: remove
                conn.execute(
                    text("DELETE FROM idempotency_keys WHERE key = :key AND merchant_id = :mid"),
                    {"key": idempotency_key, "mid": merchant.id}
                )

    with engine.begin() as conn:
        order = conn.execute(
            text("SELECT * FROM orders WHERE id = :id"),
            {"id": payload.order_id}
        ).fetchone()

        if not order:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "ORDER_NOT_FOUND",
                        "description": "Order does not exist"
                    }
                }
            )

        payment_id = _gen_id("pay")

        conn.execute(
            text(
                """
                INSERT INTO payments
                (id, entity, order_id, method, status, amount, currency, vpa, merchant_id, created_at)
                VALUES (:id, 'payment', :oid, :method, 'pending', :amt, :cur, :vpa, :mid, :ts)
                """
            ),
            {
                "id": payment_id,
                "oid": payload.order_id,
                "method": payload.method,
                "amt": order.amount,
                "cur": order.currency,
                "vpa": payload.vpa,
                "mid": merchant.id,
                "ts": now,
            }
        )

    response = {
        "id": payment_id,
        "order_id": payload.order_id,
        "amount": order.amount,
        "currency": order.currency,
        "method": payload.method,
        "status": "pending",
        "created_at": now,
    }

    # Emit webhook events for creation/pending
    enqueue_webhook_event(
        merchant.id,
        "payment.created",
        {
            "event": "payment.created",
            "timestamp": now,
            "data": {"payment": response},
        },
    )
    enqueue_webhook_event(
        merchant.id,
        "payment.pending",
        {
            "event": "payment.pending",
            "timestamp": now,
            "data": {"payment": response},
        },
    )

    # Store idempotency response
    if idempotency_key:
        expires_at = now + 24 * 60 * 60
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO idempotency_keys
                    (key, merchant_id, response, created_at, expires_at)
                    VALUES (:key, :mid, :resp, :created_at, :expires_at)
                    """
                ),
                {
                    "key": idempotency_key,
                    "mid": merchant.id,
                    "resp": json.dumps(response, separators=(",", ":")),
                    "created_at": now,
                    "expires_at": expires_at,
                }
            )

    # Enqueue background job
    try:
        _increment_job_counter("jobs_pending")
        process_payment_job.apply_async(args=[payment_id])
    except Exception:
        # If the queue/broker is unavailable, we still return the payment record.
        pass

    return response


@router.post("/api/v1/payments/public", status_code=201)
def create_payment_public(payload: PaymentCreate):
    """Create a public payment (no auth) and enqueue processing job."""
    now = _now()

    with engine.begin() as conn:
        order = conn.execute(
            text("SELECT * FROM orders WHERE id = :id"),
            {"id": payload.order_id}
        ).fetchone()

        if not order:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "ORDER_NOT_FOUND",
                        "description": "Order does not exist"
                    }
                }
            )

        payment_id = _gen_id("pay")
        # Use order merchant_id for any webhook delivery.
        merchant_id = getattr(order, "merchant_id", None)

        conn.execute(
            text(
                """
                INSERT INTO payments
                (id, entity, order_id, method, status, amount, currency, vpa, merchant_id, created_at)
                VALUES (:id, 'payment', :oid, :method, 'processing', :amt, :cur, :vpa, :mid, :ts)
                """
            ),
            {
                "id": payment_id,
                "oid": payload.order_id,
                "method": payload.method,
                "amt": order.amount,
                "cur": order.currency,
                "vpa": payload.vpa,
                "mid": merchant_id,
                "ts": now,
            }
        )

    response = {
        "id": payment_id,
        "order_id": payload.order_id,
        "amount": order.amount,
        "currency": order.currency,
        "method": payload.method,
        "status": "processing",
        "created_at": now,
    }

    try:
        _increment_job_counter("jobs_pending")
        process_payment_job.apply_async(args=[payment_id])
    except Exception:
        pass

    return response


@router.get("/api/v1/payments/{payment_id}/public")
def get_payment_public(payment_id: str):
    """Retrieve public payment status by ID."""
    with engine.connect() as conn:
        payment = conn.execute(
            text("SELECT * FROM payments WHERE id = :id"),
            {"id": payment_id}
        ).fetchone()

        if not payment:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "PAYMENT_NOT_FOUND",
                        "description": "Payment not found"
                    }
                }
            )

        return {
            "id": payment.id,
            "order_id": payment.order_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "method": payment.method,
            "status": payment.status,
            "created_at": payment.created_at,
            "updated_at": getattr(payment, "updated_at", None),
            "error_code": getattr(payment, "error_code", None),
            "error_description": getattr(payment, "error_description", None),
        }


@router.post("/api/v1/payments/{payment_id}/capture")
def capture_payment(payment_id: str, merchant=Depends(authenticate)):
    now = _now()
    with engine.begin() as conn:
        payment = conn.execute(
            text("SELECT * FROM payments WHERE id = :id"),
            {"id": payment_id}
        ).fetchone()

        if not payment or payment.merchant_id != merchant.id:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "PAYMENT_NOT_FOUND",
                        "description": "Payment not found"
                    }
                }
            )

        if payment.status != "pending":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "BAD_REQUEST_ERROR",
                        "description": "Payment not in capturable state"
                    }
                }
            )

        conn.execute(
            text(
                """
                UPDATE payments
                SET status = 'success', captured = true, updated_at = :ts
                WHERE id = :id
                """
            ),
            {"ts": now, "id": payment_id}
        )

        # Enqueue webhook for success
        payload = {
            "event": "payment.success",
            "timestamp": now,
            "data": {
                "payment": {
                    "id": payment.id,
                    "order_id": payment.order_id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "method": payment.method,
                    "status": "success",
                    "created_at": payment.created_at,
                }
            }
        }
        enqueue_webhook_event(merchant.id, "payment.success", payload)

    return {
        "id": payment_id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "method": payment.method,
        "status": "success",
        "captured": True,
        "created_at": payment.created_at,
        "updated_at": now,
    }


@router.post("/api/v1/payments/{payment_id}/refunds", status_code=201)
def create_refund(
    payment_id: str,
    payload: RefundCreate,
    merchant=Depends(authenticate)
):
    now = _now()
    with engine.begin() as conn:
        payment = conn.execute(
            text("SELECT * FROM payments WHERE id = :id"),
            {"id": payment_id}
        ).fetchone()

        if not payment or payment.merchant_id != merchant.id:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "PAYMENT_NOT_FOUND",
                        "description": "Payment not found"
                    }
                }
            )

        if payment.status != "success":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "BAD_REQUEST_ERROR",
                        "description": "Payment not in capturable state"
                    }
                }
            )

        total_refunded = conn.execute(
            text(
                """
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM refunds
                WHERE payment_id = :payment_id
                  AND status IN ('pending', 'processed')
                """
            ),
            {"payment_id": payment_id}
        ).scalar()

        if payload.amount > (payment.amount - total_refunded):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "BAD_REQUEST_ERROR",
                        "description": "Refund amount exceeds available amount"
                    }
                }
            )

        # Generate unique refund id
        refund_id = _gen_id("rfnd")
        existing = conn.execute(
            text("SELECT 1 FROM refunds WHERE id = :id"),
            {"id": refund_id}
        ).fetchone()
        while existing:
            refund_id = _gen_id("rfnd")
            existing = conn.execute(
                text("SELECT 1 FROM refunds WHERE id = :id"),
                {"id": refund_id}
            ).fetchone()

        conn.execute(
            text(
                """
                INSERT INTO refunds
                (id, payment_id, merchant_id, amount, reason, status, created_at)
                VALUES (:id, :payment_id, :merchant_id, :amount, :reason, 'pending', :created_at)
                """
            ),
            {
                "id": refund_id,
                "payment_id": payment_id,
                "merchant_id": merchant.id,
                "amount": payload.amount,
                "reason": payload.reason,
                "created_at": now,
            }
        )

    # Emit refund.created webhook
    enqueue_webhook_event(
        merchant.id,
        "refund.created",
        {
            "event": "refund.created",
            "timestamp": now,
            "data": {
                "refund": {
                    "id": refund_id,
                    "payment_id": payment_id,
                    "amount": payload.amount,
                    "reason": payload.reason,
                    "status": "pending",
                    "created_at": now,
                }
            }
        },
    )

    try:
        _increment_job_counter("jobs_pending")
        process_refund_job.apply_async(args=[refund_id])
    except Exception:
        pass

    return {
        "id": refund_id,
        "payment_id": payment_id,
        "amount": payload.amount,
        "reason": payload.reason,
        "status": "pending",
        "created_at": now,
    }


@router.get("/api/v1/refunds/{refund_id}")
def get_refund(refund_id: str, merchant=Depends(authenticate)):
    with engine.connect() as conn:
        refund = conn.execute(
            text("SELECT * FROM refunds WHERE id = :id"),
            {"id": refund_id}
        ).fetchone()

        if not refund or refund.merchant_id != merchant.id:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "REFUND_NOT_FOUND",
                        "description": "Refund not found"
                    }
                }
            )

        return {
            "id": refund.id,
            "payment_id": refund.payment_id,
            "amount": refund.amount,
            "reason": refund.reason,
            "status": refund.status,
            "created_at": refund.created_at,
            "processed_at": refund.processed_at,
        }
