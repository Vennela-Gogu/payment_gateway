from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String, primary_key=True)
    order_id = Column(String, index=True)
    amount = Column(Integer)
    currency = Column(String)
    method = Column(String)
    vpa = Column(String)
    status = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key = Column(String, primary_key=True)
    merchant_id = Column(String)
    response = Column(String)
    expires_at = Column(DateTime)

class Refund(Base):
    __tablename__ = "refunds"
    id = Column(String, primary_key=True)
    payment_id = Column(String, ForeignKey("payments.id"))
    amount = Column(Integer)
    reason = Column(String)
    status = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(String, primary_key=True)
    merchant_id = Column(String)
    url = Column(String)
    secret = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String, primary_key=True)
    event_type = Column(String)
    payload = Column(String)
    status = Column(String)
    attempts = Column(Integer, default=0)
    last_response_code = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())