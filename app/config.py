import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/payments")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

API_KEY = "key_test_abc123"
API_SECRET = "secret_test_xyz789"

WEBHOOK_SECRET = "whsec_test_123"