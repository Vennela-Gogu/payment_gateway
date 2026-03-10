from fastapi import Header, HTTPException
from app.config import API_KEY, API_SECRET

def authenticate(
    x_api_key: str = Header(...),
    x_api_secret: str = Header(...)
):
    if x_api_key != API_KEY or x_api_secret != API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid API credentials")
    return "merchant_123"