from sqlalchemy import text
from app.database import engine
from app.models import metadata

def seed():
    metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO merchants (id, name, api_key, api_secret)
            VALUES (
                'm_test',
                'Test Merchant',
                'key_test_abc123',
                'secret_test_xyz789'
            )
            ON CONFLICT DO NOTHING
        """))

if __name__ == "__main__":
    seed()