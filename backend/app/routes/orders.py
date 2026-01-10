# routes/orders.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.database import engine

router = APIRouter()

@router.get("/api/v1/orders/{order_id}/public")
def get_order_public(order_id: str):
    with engine.connect() as conn:
        order = conn.execute(
            text("SELECT id, amount, currency, status FROM orders WHERE id=:id"),
            {"id": order_id}
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
        
        return dict(order._mapping)