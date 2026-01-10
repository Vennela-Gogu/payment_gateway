# API Endpoint Status Values Reference

## Payment Status Values

### Authenticated Endpoint (`POST /api/v1/payments`)
- **UPI**: `"captured"` ✅
- **Card**: `"failed"` ❌

**Code Location**: `backend/app/main.py` line 89

### Public Endpoint (`POST /api/v1/payments/public`)
- **Initial Status**: `"processing"` ⏳
- **Final Status (UPI)**: `"success"` ✅
- **Final Status (Card)**: `"failed"` ❌

**Code Location**: `backend/app/routes/payments.py` lines 21, 24

### Why Different?

- **Authenticated endpoint**: Uses payment gateway terminology ("captured" = payment captured)
- **Public endpoint**: Uses user-friendly terminology ("success" = payment successful)
- Both represent the same outcome (UPI succeeds, Card fails)

## Order Status Values

- **Created Order**: `"created"` 📝

**Code Location**: `backend/app/main.py` line 75

## Health Check Response

**Endpoint**: `GET /health`

**Response Format**:
```json
{
  "status": "ok",
  "service": "payment-gateway"
}
```

**Code Location**: `backend/app/routes/health.py` lines 8-11

## Error Response Format

All errors follow this format:
```json
{
  "detail": {
    "error": {
      "code": "ERROR_CODE",
      "description": "Error description"
    }
  }
}
```

### Common Error Codes

- `BAD_REQUEST_ERROR` - Invalid request (e.g., amount < 100)
- `AUTHENTICATION_ERROR` - Invalid API credentials
- `ORDER_NOT_FOUND` - Order doesn't exist
- `PAYMENT_NOT_FOUND` - Payment doesn't exist

## Test Expectations

When writing tests, expect:
- ✅ Authenticated payments: `"captured"` (UPI) or `"failed"` (Card)
- ✅ Public payments: `"processing"` → `"success"` (UPI) or `"failed"` (Card)
- ✅ Orders: `"created"`
- ✅ Health: `"ok"` or `"healthy"`
