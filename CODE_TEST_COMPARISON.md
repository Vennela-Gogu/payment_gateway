# Code vs Test Comparison

## Issues Found

### 1. ❌ Payment Status Inconsistency

**Problem**: Different status values for authenticated vs public endpoints

**Code Implementation:**
- **Authenticated** (`/api/v1/payments` in `main.py`): Returns `"captured"` for UPI, `"failed"` for Card
- **Public** (`/api/v1/payments/public` in `routes/payments.py`): Returns `"success"` for UPI, `"failed"` for Card

**Test Expectations:**
- Tests expect `"success"` for public payments (✅ matches public endpoint)
- Tests don't check authenticated payment status explicitly

**Impact**: 
- Authenticated payments use "captured" 
- Public payments use "success"
- Frontend checkout page expects "success" (matches public endpoint ✅)

**Recommendation**: This is actually OK - different endpoints can have different status values. But should be documented.

---

### 2. ⚠️ Health Endpoint Response

**Code Implementation:**
- `routes/health.py`: Returns `{"status": "ok", "service": "payment-gateway"}`
- But when tested, it returned `{"status": "healthy", "timestamp": ...}`

**Issue**: There might be a duplicate health endpoint or the router isn't being used.

**Need to verify**: Which health endpoint is actually active.

---

## ✅ What Matches Correctly

### 1. Endpoint Paths
All endpoint paths in tests match the code:
- ✅ `GET /health`
- ✅ `POST /api/v1/orders`
- ✅ `GET /api/v1/orders/{id}/public`
- ✅ `POST /api/v1/payments`
- ✅ `POST /api/v1/payments/public`
- ✅ `GET /api/v1/payments/{id}/public`

### 2. Authentication Headers
- ✅ Tests use `X-API-Key` and `X-API-Secret` (matches `auth.py`)

### 3. Request Payloads
- ✅ Order creation: `amount`, `currency`, `receipt`, `notes` (matches `OrderCreate` schema)
- ✅ Payment creation: `order_id`, `method` (matches `PaymentCreate` schema)

### 4. Error Cases
- ✅ Invalid amount (< 100) → 400 error (matches code)
- ✅ Invalid auth → 401 error (matches code)
- ✅ Non-existent order → 404 error (matches code)

### 5. Payment Status Flow (Public)
- ✅ Starts as "processing"
- ✅ Changes to "success" (UPI) or "failed" (Card) after delay
- ✅ Matches checkout page expectations

---

## Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| Endpoint paths | ✅ Match | All correct |
| Request formats | ✅ Match | All correct |
| Auth headers | ✅ Match | Correct |
| Error responses | ✅ Match | All correct |
| Public payment status | ✅ Match | "success"/"failed" |
| Authenticated payment status | ⚠️ Different | Uses "captured" not "success" |
| Health response | ⚠️ Unclear | Need to verify which endpoint is active |

---

## Recommendations

1. **Document the status difference**: Authenticated payments use "captured", public payments use "success"
2. **Verify health endpoint**: Check which one is actually being used
3. **Update tests if needed**: Make sure tests check for "captured" when testing authenticated payments
