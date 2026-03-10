from fastapi import APIRouter, Depends
from app.database import SessionLocal
from app.models import Refund
from app.auth import authenticate
from app.utils import generate_id

router = APIRouter()

@router.post("/api/v1/payments/{payment_id}/refunds", status_code=201)
def refund_payment(payment_id: str, merchant_id=Depends(authenticate)):
    db = SessionLocal()
    refund = Refund(
        id=generate_id("rfnd"),
        payment_id=payment_id,
        amount=50000,
        reason="Customer requested refund",
        status="processed"
    )
    db.add(refund)
    db.commit()
    return refund