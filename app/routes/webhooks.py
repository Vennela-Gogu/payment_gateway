from fastapi import APIRouter, Depends
from app.database import SessionLocal
from app.models import WebhookDelivery
from app.auth import authenticate

router = APIRouter()

@router.get("/api/v1/webhooks/logs")
def webhook_logs(merchant_id=Depends(authenticate)):
    db = SessionLocal()
    logs = db.query(WebhookDelivery).all()
    return logs