# Manual API Endpoint Testing Guide

This guide shows you how to manually test all backend API endpoints.

## Prerequisites

1. **API Server Running**: Make sure the API is running on `http://localhost:8000`
2. **Database Seeded**: Run the seed script to create test merchant:
   ```bash
   cd backend
   python -m app.seed
   ```

## Test Credentials

- **API Key**: `key_test_abc123`
- **API Secret**: `secret_test_xyz789`

---

## Method 1: Using Browser (GET requests only)

### 1. Health Check
Open in browser:
```
http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890
}
```

### 2. Get Order Public
```
http://localhost:8000/api/v1/orders/{order_id}/public
```
Replace `{order_id}` with an actual order ID (you'll get this from creating an order first).

### 3. Get Payment Public
```
http://localhost:8000/api/v1/payments/{payment_id}/public
```
Replace `{payment_id}` with an actual payment ID.

---

## Method 2: Using curl (Command Line)

### Windows PowerShell

#### 1. Health Check
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET | Select-Object -ExpandProperty Content
```

Or using curl (if available):
```powershell
curl http://localhost:8000/health
```

#### 2. Create Order (Authenticated)
```powershell
$headers = @{
    "X-API-Key" = "key_test_abc123"
    "X-API-Secret" = "secret_test_xyz789"
    "Content-Type" = "application/json"
}
$body = @{
    amount = 50000
    currency = "INR"
    receipt = "test_receipt_001"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/orders" -Method POST -Headers $headers -Body $body | Select-Object -ExpandProperty Content
```

**Expected Response:**
```json
{
  "id": "order_abc123...",
  "entity": "order",
  "amount": 50000,
  "currency": "INR",
  "receipt": "test_receipt_001",
  "status": "created",
  "created_at": 1234567890
}
```

**Save the `id` value - you'll need it for next steps!**

#### 3. Get Order Public
```powershell
# Replace ORDER_ID with the id from step 2
$orderId = "order_abc123..."
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/orders/$orderId/public" -Method GET | Select-Object -ExpandProperty Content
```

#### 4. Create Payment (Authenticated) - UPI
```powershell
$headers = @{
    "X-API-Key" = "key_test_abc123"
    "X-API-Secret" = "secret_test_xyz789"
    "Content-Type" = "application/json"
}
$body = @{
    order_id = "order_abc123..."  # Use order ID from step 2
    method = "upi"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/payments" -Method POST -Headers $headers -Body $body | Select-Object -ExpandProperty Content
```

**Expected Response (UPI - should succeed):**
```json
{
  "id": "pay_xyz789...",
  "entity": "payment",
  "order_id": "order_abc123...",
  "method": "upi",
  "status": "captured",
  "amount": 50000,
  "created_at": 1234567890
}
```

#### 5. Create Payment (Authenticated) - Card
```powershell
$body = @{
    order_id = "order_abc123..."  # Use order ID from step 2
    method = "card"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/payments" -Method POST -Headers $headers -Body $body | Select-Object -ExpandProperty Content
```

**Expected Response (Card - should fail):**
```json
{
  "id": "pay_xyz789...",
  "status": "failed",
  ...
}
```

#### 6. Create Payment Public - UPI
```powershell
$body = @{
    order_id = "order_abc123..."  # Use order ID from step 2
    method = "upi"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/payments/public" -Method POST -Body $body -ContentType "application/json" | Select-Object -ExpandProperty Content
```

**Expected Response:**
```json
{
  "id": "pay_xyz789...",
  "status": "processing",
  ...
}
```

**Save the payment `id` - you'll need it for next step!**

#### 7. Get Payment Public
```powershell
# Replace PAYMENT_ID with the id from step 6
$paymentId = "pay_xyz789..."
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/payments/$paymentId/public" -Method GET | Select-Object -ExpandProperty Content
```

**Wait 2-3 seconds and check again - status should change from "processing" to "success" (for UPI) or "failed" (for card)**

---

## Method 3: Using Python requests

Create a file `test_manual.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "key_test_abc123"
API_SECRET = "secret_test_xyz789"

# 1. Health Check
print("1. Health Check")
response = requests.get(f"{BASE_URL}/health")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
print()

# 2. Create Order
print("2. Create Order")
headers = {
    "X-API-Key": API_KEY,
    "X-API-Secret": API_SECRET,
    "Content-Type": "application/json"
}
order_data = {
    "amount": 50000,
    "currency": "INR",
    "receipt": "test_manual_001"
}
response = requests.post(f"{BASE_URL}/api/v1/orders", headers=headers, json=order_data)
print(f"Status: {response.status_code}")
order = response.json()
print(json.dumps(order, indent=2))
order_id = order.get("id")
print()

# 3. Get Order Public
print("3. Get Order Public")
response = requests.get(f"{BASE_URL}/api/v1/orders/{order_id}/public")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
print()

# 4. Create Payment (Authenticated) - UPI
print("4. Create Payment (Authenticated) - UPI")
payment_data = {
    "order_id": order_id,
    "method": "upi"
}
response = requests.post(f"{BASE_URL}/api/v1/payments", headers=headers, json=payment_data)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
print()

# 5. Create Payment Public - UPI
print("5. Create Payment Public - UPI")
response = requests.post(f"{BASE_URL}/api/v1/payments/public", json=payment_data)
print(f"Status: {response.status_code}")
payment = response.json()
print(json.dumps(payment, indent=2))
payment_id = payment.get("id")
print()

# 6. Get Payment Public
print("6. Get Payment Public")
import time
time.sleep(2)  # Wait for status to update
response = requests.get(f"{BASE_URL}/api/v1/payments/{payment_id}/public")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
print()
```

Run it:
```bash
python test_manual.py
```

---

## Method 4: Using Postman or Insomnia

### Import Collection

1. **Base URL**: `http://localhost:8000`

2. **Create Environment Variables**:
   - `base_url`: `http://localhost:8000`
   - `api_key`: `key_test_abc123`
   - `api_secret`: `secret_test_xyz789`
   - `order_id`: (will be set after creating order)
   - `payment_id`: (will be set after creating payment)

### Endpoints to Create:

#### 1. Health Check
- **Method**: GET
- **URL**: `{{base_url}}/health`
- **Headers**: None

#### 2. Create Order
- **Method**: POST
- **URL**: `{{base_url}}/api/v1/orders`
- **Headers**:
  - `X-API-Key`: `{{api_key}}`
  - `X-API-Secret`: `{{api_secret}}`
  - `Content-Type`: `application/json`
- **Body** (JSON):
```json
{
  "amount": 50000,
  "currency": "INR",
  "receipt": "test_postman_001"
}
```
- **Tests** (to save order_id):
```javascript
var jsonData = pm.response.json();
pm.environment.set("order_id", jsonData.id);
```

#### 3. Get Order Public
- **Method**: GET
- **URL**: `{{base_url}}/api/v1/orders/{{order_id}}/public`
- **Headers**: None

#### 4. Create Payment (Authenticated)
- **Method**: POST
- **URL**: `{{base_url}}/api/v1/payments`
- **Headers**:
  - `X-API-Key`: `{{api_key}}`
  - `X-API-Secret`: `{{api_secret}}`
  - `Content-Type`: `application/json`
- **Body** (JSON):
```json
{
  "order_id": "{{order_id}}",
  "method": "upi"
}
```

#### 5. Create Payment Public
- **Method**: POST
- **URL**: `{{base_url}}/api/v1/payments/public`
- **Headers**: `Content-Type: application/json`
- **Body** (JSON):
```json
{
  "order_id": "{{order_id}}",
  "method": "upi"
}
```
- **Tests** (to save payment_id):
```javascript
var jsonData = pm.response.json();
pm.environment.set("payment_id", jsonData.id);
```

#### 6. Get Payment Public
- **Method**: GET
- **URL**: `{{base_url}}/api/v1/payments/{{payment_id}}/public`
- **Headers**: None

---

## Method 5: Using FastAPI Interactive Docs

The easiest way! FastAPI automatically generates interactive documentation.

1. **Open in browser**:
   ```
   http://localhost:8000/docs
   ```

2. **You'll see all available endpoints** with:
   - Try it out buttons
   - Request/response schemas
   - Authentication options

3. **To test authenticated endpoints**:
   - Click "Authorize" button at top
   - Enter:
     - `X-API-Key`: `key_test_abc123`
     - `X-API-Secret`: `secret_test_xyz789`
   - Click "Authorize"

4. **Test each endpoint**:
   - Click on an endpoint
   - Click "Try it out"
   - Fill in parameters/body
   - Click "Execute"
   - See response below

---

## Testing Error Cases

### 1. Invalid Amount (< 100)
```powershell
$body = @{
    amount = 50
    currency = "INR"
    receipt = "test_invalid"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/orders" -Method POST -Headers $headers -Body $body
```
**Expected**: Status 400 with error message

### 2. Invalid Authentication
```powershell
$invalidHeaders = @{
    "X-API-Key" = "wrong_key"
    "X-API-Secret" = "wrong_secret"
    "Content-Type" = "application/json"
}

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/orders" -Method POST -Headers $invalidHeaders -Body $body
```
**Expected**: Status 401 with authentication error

### 3. Non-existent Order
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/orders/invalid_order_id/public" -Method GET
```
**Expected**: Status 404 with error message

### 4. Payment for Non-existent Order
```powershell
$body = @{
    order_id = "invalid_order_id"
    method = "upi"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/payments/public" -Method POST -Body $body -ContentType "application/json"
```
**Expected**: Status 404 with error message

---

## Quick Reference: All Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/health` | No | Health check |
| POST | `/api/v1/orders` | Yes | Create order |
| GET | `/api/v1/orders/{id}/public` | No | Get order details |
| POST | `/api/v1/payments` | Yes | Create payment (authenticated) |
| POST | `/api/v1/payments/public` | No | Create payment (public) |
| GET | `/api/v1/payments/{id}/public` | No | Get payment status |

---

## Tips

1. **Save IDs**: When creating orders/payments, save the returned `id` values for subsequent requests
2. **Check Status**: Public payments start as "processing" and change to "success" (UPI) or "failed" (Card) after ~1 second
3. **Use Interactive Docs**: FastAPI's `/docs` endpoint is the easiest way to test
4. **Watch for Errors**: Check status codes - 200/201 = success, 400 = bad request, 401 = auth error, 404 = not found
