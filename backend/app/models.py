from sqlalchemy import (
    Table, Column, String, Integer, MetaData, ForeignKey
)

metadata = MetaData()

merchants = Table(
    "merchants",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String),
    Column("api_key", String, unique=True),
    Column("api_secret", String)
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
    Column("method", String),
    Column("status", String),
    Column("amount", Integer),
    Column("created_at", Integer)
)