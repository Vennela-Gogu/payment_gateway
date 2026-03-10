from sqlalchemy import (
    Table,
    Column,
    String,
    Integer,
    MetaData,
    ForeignKey,
    Boolean,
    Text,
    Index
)

metadata = MetaData()

merchants = Table(
    "merchants",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String),
    Column("api_key", String, unique=True),
    Column("api_secret", String),
    Column("webhook_url", String, nullable=True),
    Column("webhook_secret", String, nullable=True)
)

orders = Table(
    "orders",
    metadata,
    Column("id", String, primary_key=True),
    Column("entity", String, default="order"),
    Column("amount", Integer),
    Column("currency", String),
    Column("receipt", String, unique=True),
    Column("status", String),
    Column("created_at", Integer),
    Column("merchant_id", String, ForeignKey("merchants.id"))
)

payments = Table(
    "payments",
    metadata,
    Column("id", String, primary_key=True),
    Column("entity", String, default="payment"),
    Column("order_id", String, ForeignKey("orders.id")),
    Column("merchant_id", String, ForeignKey("merchants.id")),
    Column("method", String),
    Column("status", String),
    Column("amount", Integer),
    Column("currency", String),
    Column("vpa", String, nullable=True),
    Column("error_code", String, nullable=True),
    Column("error_description", Text, nullable=True),
    Column("captured", Boolean, default=False),
    Column("created_at", Integer),
    Column("updated_at", Integer, nullable=True),
)

refunds = Table(
    "refunds",
    metadata,
    Column("id", String, primary_key=True),
    Column("payment_id", String, ForeignKey("payments.id"), nullable=False),
    Column("merchant_id", String, ForeignKey("merchants.id"), nullable=False),
    Column("amount", Integer, nullable=False),
    Column("reason", Text, nullable=True),
    Column("status", String, default="pending"),
    Column("created_at", Integer),
    Column("processed_at", Integer, nullable=True),
)

webhook_logs = Table(
    "webhook_logs",
    metadata,
    Column("id", String, primary_key=True),
    Column("merchant_id", String, ForeignKey("merchants.id"), nullable=False),
    Column("event", String, nullable=False),
    Column("payload", Text, nullable=False),
    Column("status", String, default="pending"),
    Column("attempts", Integer, default=0),
    Column("last_attempt_at", Integer, nullable=True),
    Column("next_retry_at", Integer, nullable=True),
    Column("response_code", Integer, nullable=True),
    Column("response_body", Text, nullable=True),
    Column("created_at", Integer)
)

idempotency_keys = Table(
    "idempotency_keys",
    metadata,
    Column("key", String, primary_key=True),
    Column("merchant_id", String, ForeignKey("merchants.id"), primary_key=True),
    Column("response", Text, nullable=False),
    Column("created_at", Integer),
    Column("expires_at", Integer)
)

Index("idx_refunds_payment_id", refunds.c.payment_id)
Index("idx_webhook_logs_merchant_id", webhook_logs.c.merchant_id)
Index("idx_webhook_logs_status", webhook_logs.c.status)
Index("idx_webhook_logs_next_retry", webhook_logs.c.next_retry_at)
