from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Payment, IdempotencyKey
from app.schemas import PaymentCreate
from app.auth import authenticate
from app.utils import generate_id
from app.tasks import process_payment
from datetime import datetime, timedelta
import json

router = APIRouter()

@router.post("/api/v1/payments", status_code=201)
def create_payment(
    payload: PaymentCreate,
    merchant_id=Depends(authenticate),
    idempotency_key: str | None = Header(None)
):
    db: Session = SessionLocal()

    if idempotency_key:
        record = db.query(IdempotencyKey).filter_by(
            key=idempotency_key,
            merchant_id=merchant_id
        ).first()
        if record and record.expires_at > datetime.utcnow():
            return json.loads(record.response)

    payment = Payment(
        id=generate_id("pay"),
        order_id=payload.order_id,
        amount=50000,
        currency="INR",
        method=payload.method,
        vpa=payload.vpa,
        status="pending"
    )
    db.add(payment)
    db.commit()

    response = {
        "id": payment.id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "method": payment.method,
        "vpa": payment.vpa,
        "status": payment.status,
        "created_at": payment.created_at.isoformat()
    }

    if idempotency_key:
        db.add(IdempotencyKey(
            key=idempotency_key,
            merchant_id=merchant_id,
            response=json.dumps(response),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        ))
        db.commit()

    process_payment.delay(payment.id)
    return response