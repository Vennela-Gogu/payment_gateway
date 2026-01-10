# Automatic Testing Guide

This guide explains how to run automatic tests for all API endpoints.

## Quick Start

### Option 1: Using the Test Runner (Recommended)

```bash
python run_tests.py
```

This script will:
1. Check if pytest is installed
2. Verify API server is running
3. Run all automatic tests
4. Show a summary of results

### Option 2: Using pytest Directly

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_all_endpoints.py -v

# Run specific test class
pytest tests/test_all_endpoints.py::TestHealthEndpoint -v

# Run specific test
pytest tests/test_all_endpoints.py::TestHealthEndpoint::test_health_endpoint_exists -v
```

### Option 3: Using the Original Test Script

```bash
python test_api.py
```

---

## Test Coverage

The automatic test suite covers **ALL** endpoints:

### ✅ Health Endpoint
- `GET /health` - Health check
- Response format validation

### ✅ Order Endpoints
- `POST /api/v1/orders` - Create order (authenticated)
  - Valid order creation
  - Invalid amount (< 100)
  - Missing authentication
  - Invalid authentication
- `GET /api/v1/orders/{id}/public` - Get order details
  - Valid order ID
  - Invalid order ID (404)

### ✅ Payment Endpoints
- `POST /api/v1/payments` - Create payment (authenticated)
  - UPI method (should succeed)
  - Card method (should fail)
  - Invalid order ID
- `POST /api/v1/payments/public` - Create payment (public)
  - UPI method
  - Card method
- `GET /api/v1/payments/{id}/public` - Get payment status
  - Valid payment ID
  - Invalid payment ID (404)
  - Status polling (processing → success/failed)

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
└── test_all_endpoints.py    # All endpoint tests
```

### Test Classes

1. **TestHealthEndpoint** - Health check tests
2. **TestOrderEndpoints** - Order creation and retrieval tests
3. **TestPaymentEndpoints** - Payment creation and status tests
4. **TestEndpointCoverage** - Meta-tests for coverage verification

---

## Prerequisites

### 1. Install Dependencies

```bash
pip install pytest requests
```

### 2. Start API Server

```bash
cd backend
uvicorn app.main:app --reload
```

### 3. Seed Database

```bash
cd backend
python -m app.seed
```

---

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run with Coverage Report

```bash
pip install pytest-cov
pytest tests/ --cov=backend/app --cov-report=html
```

### Run Only Fast Tests (Skip Slow Ones)

```bash
pytest tests/ -v -m "not slow"
```

### Run Tests in Parallel (Faster)

```bash
pip install pytest-xdist
pytest tests/ -n auto
```

---

## Test Output

### Successful Run

```
tests/test_all_endpoints.py::TestHealthEndpoint::test_health_endpoint_exists PASSED
tests/test_all_endpoints.py::TestHealthEndpoint::test_health_endpoint_response_format PASSED
tests/test_all_endpoints.py::TestOrderEndpoints::test_create_order_authenticated PASSED
...
==================== 15 passed in 5.23s ====================
```

### Failed Test

```
tests/test_all_endpoints.py::TestOrderEndpoints::test_create_order_authenticated FAILED
...
AssertionError: Expected 201, got 500: Internal Server Error
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest requests
      - name: Start services
        run: |
          docker-compose up -d
          sleep 10
      - name: Seed database
        run: |
          cd backend
          python -m app.seed
      - name: Run tests
        run: pytest tests/ -v
```

---

## Test Maintenance

### Adding New Tests

1. Add test method to appropriate test class in `tests/test_all_endpoints.py`
2. Follow naming convention: `test_<description>`
3. Use assertions to verify expected behavior
4. Use fixtures for shared data (orders, payments)

### Example: Adding a New Test

```python
def test_new_endpoint_feature(self, order_id: str):
    """Test description"""
    response = requests.get(
        f"{BASE_URL}/api/v1/new-endpoint/{order_id}",
        timeout=5
    )
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

---

## Troubleshooting

### Issue: "pytest: command not found"

**Solution**: Install pytest
```bash
pip install pytest
```

### Issue: "API server is not running"

**Solution**: Start the API server
```bash
cd backend
uvicorn app.main:app --reload
```

### Issue: "401 Unauthorized" errors

**Solution**: Seed the database
```bash
cd backend
python -m app.seed
```

### Issue: Tests are slow

**Solution**: 
- Use `-n auto` for parallel execution
- Mark slow tests with `@pytest.mark.slow`
- Skip slow tests with `-m "not slow"`

---

## Comparison: Automatic vs Manual Testing

| Aspect | Automatic Tests | Manual Tests |
|--------|----------------|--------------|
| **Speed** | Fast (runs all in seconds) | Slow (one at a time) |
| **Coverage** | All endpoints + edge cases | Selective |
| **Repeatability** | 100% consistent | Human error possible |
| **CI/CD** | Easy to integrate | Not suitable |
| **Debugging** | Clear error messages | Requires investigation |
| **Maintenance** | Update code when API changes | Update documentation |

**Recommendation**: Use automatic tests for regular testing, manual tests for exploration.

---

## Summary

✅ **All endpoints are automatically tested**
✅ **Edge cases are covered**
✅ **Easy to run with `python run_tests.py`**
✅ **Suitable for CI/CD integration**
✅ **Comprehensive coverage of success and error scenarios**

Run `python run_tests.py` to verify all endpoints are working correctly!
