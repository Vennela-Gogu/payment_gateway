from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from app.database import engine
from app.schemas import OrderCreate, PaymentCreate
from app.auth import authenticate
from app.routes import orders, payments, health
import time, random, string

app = FastAPI(
    title="Payment Gateway API",
    description="Payment Gateway API with merchant authentication",
    version="1.0.0"
)

# Add security scheme to OpenAPI docs
app.openapi_schema = None  # Force regeneration

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key for merchant authentication"
        },
        "ApiSecretAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Secret",
            "description": "API Secret for merchant authentication"
        }
    }
    
    # Add security requirements to authenticated endpoints
    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            if method.lower() in ["post", "put", "patch", "delete"]:
                # Check if this endpoint requires authentication (not public endpoints)
                if "/public" not in path and path not in ["/health", "/docs", "/openapi.json", "/redoc"]:
                    if "security" not in details:
                        details["security"] = [
                            {"ApiKeyAuth": [], "ApiSecretAuth": []}
                        ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Include routers
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(health.router)

def gen_id(prefix):
    return prefix + "_" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=14)
    )

# Health endpoint is now in routes/health.py

# -------- ORDERS --------
@app.post("/api/v1/orders", status_code=201)
def create_order(
    payload: OrderCreate,
    merchant=Depends(authenticate)
):
    if payload.amount < 100:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "BAD_REQUEST_ERROR",
                    "description": "Amount must be at least 100"
                }
            }
        )

    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT * FROM orders WHERE receipt=:r"),
            {"r": payload.receipt}
        ).fetchone()

        if existing:
            return dict(existing._mapping)

    order_id = gen_id("order")
    now = int(time.time())

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO orders
                (id, entity, amount, currency, receipt, status, created_at, merchant_id)
                VALUES (:id, 'order', :amt, :cur, :rec, 'created', :ts, :mid)
            """),
            {
                "id": order_id,
                "amt": payload.amount,
                "cur": payload.currency,
                "rec": payload.receipt,
                "ts": now,
                "mid": merchant.id
            }
        )

    return {
        "id": order_id,
        "entity": "order",
        "amount": payload.amount,
        "currency": payload.currency,
        "receipt": payload.receipt,
        "status": "created",
        "created_at": now
    }

# -------- PAYMENTS --------
@app.post("/api/v1/payments", status_code=201)
def create_payment(
    payload: PaymentCreate,
    merchant=Depends(authenticate)
):
    payment_id = gen_id("pay")
    now = int(time.time())

    # deterministic rule (as per specs)
    status = "captured" if payload.method == "upi" else "failed"

    with engine.begin() as conn:
        order = conn.execute(
            text("SELECT * FROM orders WHERE id=:id"),
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

        conn.execute(
            text("""
                INSERT INTO payments
                (id, entity, order_id, method, status, amount, created_at)
                VALUES (:id, 'payment', :oid, :m, :s, :amt, :ts)
            """),
            {
                "id": payment_id,
                "oid": payload.order_id,
                "m": payload.method,
                "s": status,
                "amt": order.amount,
                "ts": now
            }
        )

    return {
        "id": payment_id,
        "entity": "payment",
        "order_id": payload.order_id,
        "method": payload.method,
        "status": status,
        "amount": order.amount,
        "created_at": now
    }