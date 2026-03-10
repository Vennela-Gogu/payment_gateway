import json, requests, time
from app.utils import generate_id
from app.database import SessionLocal
from app.models import WebhookEndpoint, WebhookDelivery
import hmac, hashlib

MAX_RETRIES = 5

def sign_payload(payload: str, secret: str):
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def send_webhook(event_type: str, data: dict, merchant_id: str):
    db = SessionLocal()
    endpoints = db.query(WebhookEndpoint).filter_by(
        merchant_id=merchant_id,
        active=True
    ).all()

    payload = json.dumps({
        "id": generate_id("evt"),
        "type": event_type,
        "data": data
    })

    for endpoint in endpoints:
        delivery = WebhookDelivery(
            id=generate_id("whd"),
            event_type=event_type,
            payload=payload,
            status="pending"
        )
        db.add(delivery)
        db.commit()

        for attempt in range(MAX_RETRIES):
            signature = sign_payload(payload, endpoint.secret)
            try:
                resp = requests.post(
                    endpoint.url,
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature
                    },
                    timeout=5
                )
                delivery.attempts += 1
                delivery.last_response_code = resp.status_code

                if 200 <= resp.status_code < 300:
                    delivery.status = "success"
                    break
            except Exception:
                delivery.attempts += 1

            time.sleep(2 ** attempt)  # exponential backoff

        if delivery.status != "success":
            delivery.status = "failed"

        db.commit()