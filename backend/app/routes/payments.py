# routes/payments.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database import engine
from app.schemas import PaymentCreate
import time, random, string, threading

router = APIRouter()

def gen_id(prefix):
    return prefix + "_" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=14)
    )

@router.post("/api/v1/payments/public", status_code=201)
def create_payment_public(payload: PaymentCreate):
    payment_id = gen_id("pay")
    now = int(time.time())

    # Determine final status: UPI = success, Card = failed
    final_status = "success" if payload.method == "upi" else "failed"
    
    # Start with processing status for async simulation
    initial_status = "processing"

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

        # Insert payment with processing status initially
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
                "s": initial_status,
                "amt": order.amount,
                "ts": now
            }
        )

    # Update status asynchronously (simulated - in real app this would be a background job)
    # For simplicity, we update it immediately but the polling will catch the change
    def update_status():
        time.sleep(1)  # Simulate processing delay
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE payments
                    SET status = :status
                    WHERE id = :id
                """),
                {
                    "id": payment_id,
                    "status": final_status
                }
            )
    
    threading.Thread(target=update_status, daemon=True).start()

    return {
        "id": payment_id,
        "entity": "payment",
        "order_id": payload.order_id,
        "method": payload.method,
        "status": initial_status,  # Return processing initially
        "amount": order.amount,
        "created_at": now
    }

@router.get("/api/v1/payments/{payment_id}/public")
def get_payment_public(payment_id: str):
    with engine.connect() as conn:
        payment = conn.execute(
            text("SELECT id, entity, order_id, method, status, amount, created_at FROM payments WHERE id=:id"),
            {"id": payment_id}
        ).fetchone()
        
        if not payment:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "PAYMENT_NOT_FOUND",
                        "description": "Payment does not exist"
                    }
                }
            )
        
        return dict(payment._mapping)
