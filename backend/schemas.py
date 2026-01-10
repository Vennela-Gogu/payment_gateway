from pydantic import BaseModel

class OrderCreate(BaseModel):
    amount: int
    currency: str = "INR"
    receipt: str
    notes: dict | None = None

class PaymentCreate(BaseModel):
    order_id: str
    method: str  # card | upi