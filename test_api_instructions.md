# API Testing Instructions

## Prerequisites

1. **Start the database and API server:**
   ```bash
   # Using Docker Compose (recommended)
   docker-compose up -d
   
   # OR manually:
   # 1. Start PostgreSQL
   # 2. Set DATABASE_URL environment variable
   # 3. Run database migrations/seeding:
   cd backend
   python -m app.seed
   # 4. Start the API server:
   uvicorn app.main:app --reload
   ```

2. **Install test dependencies:**
   ```bash
   pip install requests
   ```

## Running Tests

### Option 1: Python Test Script (Recommended)

```bash
# Make sure API is running on http://localhost:8000
python test_api.py
```

This script will test:
- ✅ Health endpoint
- ✅ Create order (authenticated)
- ✅ Get order public
- ✅ Create payment (authenticated)
- ✅ Create payment public
- ✅ Get payment public
- ✅ Payment status polling
- ✅ Error cases (invalid amount, invalid auth, etc.)

### Option 2: Using curl (Linux/Mac)

```bash
chmod +x test_api_curl.sh
./test_api_curl.sh
```

### Option 3: Manual Testing with curl

```bash
# 1. Health Check
curl http://localhost:8000/health

# 2. Create Order (Authenticated)
curl -X POST http://localhost:8000/api/v1/orders \
  -H "X-API-Key: key_test_abc123" \
  -H "X-API-Secret: secret_test_xyz789" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50000,
    "currency": "INR",
    "receipt": "test_123"
  }'

# 3. Get Order Public (use order_id from step 2)
curl http://localhost:8000/api/v1/orders/{order_id}/public

# 4. Create Payment Public
curl -X POST http://localhost:8000/api/v1/payments/public \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "{order_id}",
    "method": "upi"
  }'

# 5. Get Payment Public (use payment_id from step 4)
curl http://localhost:8000/api/v1/payments/{payment_id}/public
```

## Test Credentials

- **API Key:** `key_test_abc123`
- **API Secret:** `secret_test_xyz789`

These are seeded by default in the database.

## Expected Results

- **UPI payments:** Should succeed (status: "success" after processing)
- **Card payments:** Should fail (status: "failed")
- **Order amount < 100:** Should return 400 error
- **Invalid credentials:** Should return 401 error
- **Non-existent order/payment:** Should return 404 error

## API Endpoints Summary

### Public Endpoints (No Authentication)
- `GET /health` - Health check
- `GET /api/v1/orders/{order_id}/public` - Get order details
- `POST /api/v1/payments/public` - Create payment
- `GET /api/v1/payments/{payment_id}/public` - Get payment status

### Authenticated Endpoints (Require X-API-Key and X-API-Secret headers)
- `POST /api/v1/orders` - Create order
- `POST /api/v1/payments` - Create payment
