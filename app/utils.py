import uuid, hmac, hashlib
from app.config import WEBHOOK_SECRET

def generate_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def sign_payload(payload: str):
    return hmac.new(
        WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()