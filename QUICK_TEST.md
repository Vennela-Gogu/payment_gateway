# Quick Testing Guide

## 🚀 Automatic Testing (Recommended)

**Run all endpoint tests automatically:**

```bash
# Install test dependencies (first time only)
pip install pytest requests

# Run all automatic tests
python run_tests.py

# Or use pytest directly
pytest tests/ -v
```

This will test **ALL endpoints automatically** including:
- ✅ Health check
- ✅ Order creation (authenticated)
- ✅ Order retrieval (public)
- ✅ Payment creation (authenticated & public)
- ✅ Payment status polling
- ✅ Error cases (invalid auth, invalid data, etc.)

**See `AUTOMATIC_TESTING_GUIDE.md` for details.**

---

## Manual Testing: FastAPI Interactive Docs

1. **Open browser**: http://localhost:8000/docs
2. **Look for "Authorize" button** at the top right (if it doesn't appear, see alternative below)
3. **If "Authorize" button is visible**, click it and enter:
   - `X-API-Key`: `key_test_abc123`
   - `X-API-Secret`: `secret_test_xyz789`
4. **Test each endpoint** using the "Try it out" button

**Note**: If the "Authorize" button doesn't appear, you can still test authenticated endpoints by manually adding headers in the "Try it out" section. Look for the "Headers" or "Parameters" section when testing an endpoint.

---

## Quick PowerShell Commands

### 1. Health Check
```powershell
Invoke-WebRequest http://localhost:8000/health | Select-Object -ExpandProperty Content
```

### 2. Create Order
```powershell
$h = @{"X-API-Key"="key_test_abc123"; "X-API-Secret"="secret_test_xyz789"; "Content-Type"="application/json"}
$b = '{"amount":50000,"currency":"INR","receipt":"test001"}' | ConvertFrom-Json | ConvertTo-Json
$r = Invoke-WebRequest -Uri http://localhost:8000/api/v1/orders -Method POST -Headers $h -Body $b
$r.Content
# Save the "id" from response as $orderId
```

### 3. Get Order Public
```powershell
Invoke-WebRequest "http://localhost:8000/api/v1/orders/$orderId/public" | Select-Object -ExpandProperty Content
```

### 4. Create Payment Public
```powershell
$b = "{\"order_id\":\"$orderId\",\"method\":\"upi\"}"
$r = Invoke-WebRequest -Uri http://localhost:8000/api/v1/payments/public -Method POST -Body $b -ContentType "application/json"
$r.Content
# Save the "id" from response as $paymentId
```

### 5. Get Payment Status
```powershell
Invoke-WebRequest "http://localhost:8000/api/v1/payments/$paymentId/public" | Select-Object -ExpandProperty Content
```

---

## Using Python Script

```bash
python test_manual_simple.py
```

This will test all endpoints automatically and show you the results.

---

## All Endpoints Summary

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/health` | GET | No | Check if API is running |
| `/api/v1/orders` | POST | Yes | Create new order |
| `/api/v1/orders/{id}/public` | GET | No | Get order details |
| `/api/v1/payments` | POST | Yes | Create payment (merchant) |
| `/api/v1/payments/public` | POST | No | Create payment (public) |
| `/api/v1/payments/{id}/public` | GET | No | Get payment status |

---

## Test Credentials

- **API Key**: `key_test_abc123`
- **API Secret**: `secret_test_xyz789`

These are created automatically when you run the seed script.
