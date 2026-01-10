# Testing Guide - Payment Gateway API

## Quick Start

### Automatic Testing (Recommended)

```bash
# Run all tests automatically
python run_tests.py
```

This tests **ALL endpoints** automatically. See `AUTOMATIC_TESTING_GUIDE.md` for details.

### Manual Testing

See `QUICK_TEST.md` or `MANUAL_API_TESTING.md` for manual testing instructions.

---

## Test Files

| File | Purpose |
|------|---------|
| `run_tests.py` | **Main test runner** - Run this to test all endpoints |
| `tests/test_all_endpoints.py` | Comprehensive pytest test suite |
| `test_api.py` | Original test script (still works) |
| `test_manual_simple.py` | Simple manual test script |

---

## All Endpoints Covered

✅ **GET /health** - Health check  
✅ **POST /api/v1/orders** - Create order (authenticated)  
✅ **GET /api/v1/orders/{id}/public** - Get order details  
✅ **POST /api/v1/payments** - Create payment (authenticated)  
✅ **POST /api/v1/payments/public** - Create payment (public)  
✅ **GET /api/v1/payments/{id}/public** - Get payment status  

**All endpoints are automatically tested with:**
- Success cases
- Error cases (invalid auth, invalid data, etc.)
- Edge cases
- Status transitions

---

## Running Tests

### Quick Test
```bash
python run_tests.py
```

### Detailed Test
```bash
pytest tests/ -v
```

### Specific Test
```bash
pytest tests/test_all_endpoints.py::TestHealthEndpoint -v
```

---

## Prerequisites

1. **API Server Running**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Database Seeded**
   ```bash
   cd backend
   python -m app.seed
   ```

3. **Test Dependencies**
   ```bash
   pip install pytest requests
   ```

---

## Test Coverage

- ✅ All 6 main endpoints
- ✅ Authentication (valid & invalid)
- ✅ Error handling (400, 401, 404)
- ✅ Payment status transitions
- ✅ Request/response validation

---

## Documentation

- `AUTOMATIC_TESTING_GUIDE.md` - Complete guide for automatic testing
- `QUICK_TEST.md` - Quick reference for testing
- `MANUAL_API_TESTING.md` - Detailed manual testing guide
- `AUTH_HEADER_ERRORS_GUIDE.md` - Troubleshooting auth issues
