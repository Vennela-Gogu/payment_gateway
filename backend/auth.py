from fastapi import Header, HTTPException
from sqlalchemy import text
from app.database import engine

def authenticate(
    x_api_key: str = Header(...),
    x_api_secret: str = Header(...)
):
    with engine.connect() as conn:
        merchant = conn.execute(
            text("""
                SELECT * FROM merchants
                WHERE api_key=:k AND api_secret=:s
            """),
            {"k": x_api_key, "s": x_api_secret}
        ).fetchone()

        if not merchant:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "description": "Invalid API credentials"
                    }
                }
            )
        return merchant