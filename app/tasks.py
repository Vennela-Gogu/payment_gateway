from celery import Celery
from app.database import SessionLocal
from app.models import Payment
from app.webhook import send_webhook
import time

celery = Celery("worker", broker="redis://redis:6379/0")

@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 5})
def process_payment(self, payment_id):
    db = SessionLocal()
    payment = db.query(Payment).get(payment_id)
    time.sleep(2)
    payment.status = "success"
    db.commit()
from app.webhook import send_webhook


def process_payment(self, payment_id):
    db = SessionLocal()
    payment = db.query(Payment).get(payment_id)

    time.sleep(2)
    payment.status = "success"
    db.commit()

    send_webhook(
        event_type="payment.success",
        data={
            "payment_id": payment.id,
            "status": payment.status,
            "amount": payment.amount,
            "currency": payment.currency
        },
        merchant_id="merchant_123"
    )
