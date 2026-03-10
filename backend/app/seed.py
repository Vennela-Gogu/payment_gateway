from sqlalchemy import text
from app.database import engine
from app.models import metadata

def seed():
    # Ensure base tables exist
    from app.models import metadata

    metadata.create_all(engine)

    # Apply schema migrations and ensure required tables/columns exist
    with engine.begin() as conn:
        # Add new merchant columns
        conn.execute(text("""
            ALTER TABLE merchants
            ADD COLUMN IF NOT EXISTS email TEXT,
            ADD COLUMN IF NOT EXISTS webhook_url TEXT,
            ADD COLUMN IF NOT EXISTS webhook_secret TEXT;
        """))

        # Extend payments table
        conn.execute(text("""
            ALTER TABLE payments
            ADD COLUMN IF NOT EXISTS currency TEXT,
            ADD COLUMN IF NOT EXISTS vpa TEXT,
            ADD COLUMN IF NOT EXISTS merchant_id TEXT,
            ADD COLUMN IF NOT EXISTS error_code TEXT,
            ADD COLUMN IF NOT EXISTS error_description TEXT,
            ADD COLUMN IF NOT EXISTS captured BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS updated_at INTEGER;
        """))

        # Create refunds table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS refunds (
                id TEXT PRIMARY KEY,
                payment_id TEXT NOT NULL REFERENCES payments(id),
                merchant_id TEXT NOT NULL REFERENCES merchants(id),
                amount INTEGER NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                created_at INTEGER,
                processed_at INTEGER
            );
        """))

        # Create webhook logs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS webhook_logs (
                id TEXT PRIMARY KEY,
                merchant_id TEXT NOT NULL REFERENCES merchants(id),
                event TEXT NOT NULL,
                payload JSONB NOT NULL,
                status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                last_attempt_at INTEGER,
                next_retry_at INTEGER,
                response_code INTEGER,
                response_body TEXT,
                created_at INTEGER
            );
        """))

        # Create idempotency keys table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                key TEXT NOT NULL,
                merchant_id TEXT NOT NULL REFERENCES merchants(id),
                response JSONB NOT NULL,
                created_at INTEGER,
                expires_at INTEGER,
                PRIMARY KEY (key, merchant_id)
            );
        """))

        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_refunds_payment_id ON refunds(payment_id);
            CREATE INDEX IF NOT EXISTS idx_webhook_logs_merchant_id ON webhook_logs(merchant_id);
            CREATE INDEX IF NOT EXISTS idx_webhook_logs_status ON webhook_logs(status);
            CREATE INDEX IF NOT EXISTS idx_webhook_logs_next_retry ON webhook_logs(next_retry_at) WHERE status = 'pending';
        """))

        # Ensure test merchant record exists
        conn.execute(text("""
            INSERT INTO merchants (id, name, email, api_key, api_secret, webhook_secret)
            VALUES (
                'm_test',
                'Test Merchant',
                'test@example.com',
                'key_test_abc123',
                'secret_test_xyz789',
                'whsec_test_abc123'
            )
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                webhook_secret = EXCLUDED.webhook_secret;
        """))

if __name__ == "__main__":
    seed()