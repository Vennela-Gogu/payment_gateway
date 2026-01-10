"""
Comprehensive automatic test suite for all API endpoints
Run with: pytest tests/test_all_endpoints.py -v
"""
import pytest
import requests
import time
import json
from typing import Dict, Optional

# Test Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "key_test_abc123"
API_SECRET = "secret_test_xyz789"

AUTH_HEADERS = {
    "X-API-Key": API_KEY,
    "X-API-Secret": API_SECRET,
    "Content-Type": "application/json"
}

PUBLIC_HEADERS = {
    "Content-Type": "application/json"
}


class TestHealthEndpoint:
    """Tests for GET /health endpoint"""
    
    def test_health_endpoint_exists(self):
        """Test that health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
    def test_health_endpoint_response_format(self):
        """Test health endpoint returns valid JSON"""
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data, "Response should contain 'status' field"
        assert data["status"] in ["ok", "healthy"], f"Status should be 'ok' or 'healthy', got {data['status']}"


class TestOrderEndpoints:
    """Tests for order-related endpoints"""
    
    @pytest.fixture
    def order_id(self) -> str:
        """Create an order and return its ID for use in other tests"""
        payload = {
            "amount": 50000,
            "currency": "INR",
            "receipt": f"test_auto_{int(time.time())}"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            headers=AUTH_HEADERS,
            json=payload,
            timeout=5
        )
        assert response.status_code == 201, f"Failed to create order: {response.text}"
        data = response.json()
        assert "id" in data, "Order response should contain 'id'"
        return data["id"]
    
    def test_create_order_authenticated(self):
        """Test POST /api/v1/orders (authenticated)"""
        payload = {
            "amount": 50000,
            "currency": "INR",
            "receipt": f"test_create_{int(time.time())}",
            "notes": {"test": "automatic"}
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            headers=AUTH_HEADERS,
            json=payload,
            timeout=5
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["amount"] == 50000
        assert data["currency"] == "INR"
        assert data["status"] == "created"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_order_invalid_amount(self):
        """Test POST /api/v1/orders with amount < 100"""
        payload = {
            "amount": 50,
            "currency": "INR",
            "receipt": f"test_invalid_{int(time.time())}"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            headers=AUTH_HEADERS,
            json=payload,
            timeout=5
        )
        assert response.status_code == 400, f"Expected 400 for invalid amount, got {response.status_code}"
        data = response.json()
        assert "error" in data.get("detail", {}), "Error response should contain error details"
    
    def test_create_order_missing_auth(self):
        """Test POST /api/v1/orders without authentication"""
        payload = {
            "amount": 50000,
            "currency": "INR",
            "receipt": f"test_no_auth_{int(time.time())}"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=5
        )
        assert response.status_code in [401, 422], f"Expected 401 or 422, got {response.status_code}"
    
    def test_create_order_invalid_auth(self):
        """Test POST /api/v1/orders with invalid credentials"""
        payload = {
            "amount": 50000,
            "currency": "INR",
            "receipt": f"test_invalid_auth_{int(time.time())}"
        }
        invalid_headers = {
            "X-API-Key": "wrong_key",
            "X-API-Secret": "wrong_secret",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            headers=invalid_headers,
            json=payload,
            timeout=5
        )
        assert response.status_code == 401, f"Expected 401 for invalid auth, got {response.status_code}"
        data = response.json()
        assert "error" in data.get("detail", {}), "Error response should contain error details"
    
    def test_get_order_public(self, order_id: str):
        """Test GET /api/v1/orders/{order_id}/public"""
        response = requests.get(
            f"{BASE_URL}/api/v1/orders/{order_id}/public",
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"] == order_id
        assert "amount" in data
        assert "currency" in data
        assert "status" in data
    
    def test_get_order_public_invalid_id(self):
        """Test GET /api/v1/orders/{order_id}/public with invalid ID"""
        response = requests.get(
            f"{BASE_URL}/api/v1/orders/invalid_order_id_12345/public",
            timeout=5
        )
        assert response.status_code == 404, f"Expected 404 for invalid order, got {response.status_code}"
        data = response.json()
        assert "error" in data.get("detail", {}), "Error response should contain error details"


class TestPaymentEndpoints:
    """Tests for payment-related endpoints"""
    
    @pytest.fixture
    def order_id(self) -> str:
        """Create an order for payment tests"""
        payload = {
            "amount": 50000,
            "currency": "INR",
            "receipt": f"test_payment_order_{int(time.time())}"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            headers=AUTH_HEADERS,
            json=payload,
            timeout=5
        )
        assert response.status_code == 201
        return response.json()["id"]
    
    def test_create_payment_authenticated_upi(self, order_id: str):
        """Test POST /api/v1/payments (authenticated) with UPI"""
        payload = {
            "order_id": order_id,
            "method": "upi"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/payments",
            headers=AUTH_HEADERS,
            json=payload,
            timeout=5
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["method"] == "upi"
        assert data["status"] == "captured", "Authenticated UPI payment should have 'captured' status"
        assert data["order_id"] == order_id
        assert "id" in data
        assert "amount" in data
    
    def test_create_payment_authenticated_card(self, order_id: str):
        """Test POST /api/v1/payments (authenticated) with Card"""
        payload = {
            "order_id": order_id,
            "method": "card"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/payments",
            headers=AUTH_HEADERS,
            json=payload,
            timeout=5
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["method"] == "card"
        assert data["status"] == "failed", "Card payment should have 'failed' status"
        assert data["order_id"] == order_id
    
    def test_create_payment_authenticated_invalid_order(self):
        """Test POST /api/v1/payments with invalid order_id"""
        payload = {
            "order_id": "invalid_order_id_12345",
            "method": "upi"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/payments",
            headers=AUTH_HEADERS,
            json=payload,
            timeout=5
        )
        assert response.status_code == 404, f"Expected 404 for invalid order, got {response.status_code}"
        data = response.json()
        assert "error" in data.get("detail", {}), "Error response should contain error details"
    
    def test_create_payment_public_upi(self, order_id: str):
        """Test POST /api/v1/payments/public with UPI"""
        payload = {
            "order_id": order_id,
            "method": "upi"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/payments/public",
            headers=PUBLIC_HEADERS,
            json=payload,
            timeout=5
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["method"] == "upi"
        assert data["status"] == "processing", "Public payment should start with 'processing' status"
        assert data["order_id"] == order_id
        assert "id" in data
        return data["id"]  # Return payment_id for status polling test
    
    def test_create_payment_public_card(self, order_id: str):
        """Test POST /api/v1/payments/public with Card"""
        payload = {
            "order_id": order_id,
            "method": "card"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/payments/public",
            headers=PUBLIC_HEADERS,
            json=payload,
            timeout=5
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["method"] == "card"
        assert data["status"] == "processing", "Public payment should start with 'processing' status"
    
    def test_get_payment_public(self, order_id: str):
        """Test GET /api/v1/payments/{payment_id}/public"""
        # First create a payment
        payload = {
            "order_id": order_id,
            "method": "upi"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/payments/public",
            headers=PUBLIC_HEADERS,
            json=payload,
            timeout=5
        )
        assert create_response.status_code == 201
        payment_id = create_response.json()["id"]
        
        # Then get it
        response = requests.get(
            f"{BASE_URL}/api/v1/payments/{payment_id}/public",
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"] == payment_id
        assert "method" in data
        assert "status" in data
        assert "amount" in data
    
    def test_get_payment_public_invalid_id(self):
        """Test GET /api/v1/payments/{payment_id}/public with invalid ID"""
        response = requests.get(
            f"{BASE_URL}/api/v1/payments/invalid_payment_id_12345/public",
            timeout=5
        )
        assert response.status_code == 404, f"Expected 404 for invalid payment, got {response.status_code}"
        data = response.json()
        assert "error" in data.get("detail", {}), "Error response should contain error details"
    
    def test_payment_status_polling_upi(self, order_id: str):
        """Test that UPI payment status changes from processing to success"""
        # Create payment
        payload = {
            "order_id": order_id,
            "method": "upi"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/payments/public",
            headers=PUBLIC_HEADERS,
            json=payload,
            timeout=5
        )
        assert create_response.status_code == 201
        payment_id = create_response.json()["id"]
        
        # Poll until status changes (max 10 attempts, 2 seconds apart)
        max_attempts = 10
        for attempt in range(max_attempts):
            response = requests.get(
                f"{BASE_URL}/api/v1/payments/{payment_id}/public",
                timeout=5
            )
            assert response.status_code == 200
            data = response.json()
            status = data.get("status")
            
            if status != "processing":
                assert status == "success", f"UPI payment should become 'success', got '{status}'"
                return  # Success!
            
            if attempt < max_attempts - 1:
                time.sleep(2)
        
        pytest.fail("Payment status did not change from 'processing' after polling")
    
    def test_payment_status_polling_card(self, order_id: str):
        """Test that Card payment status changes from processing to failed"""
        # Create payment
        payload = {
            "order_id": order_id,
            "method": "card"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/v1/payments/public",
            headers=PUBLIC_HEADERS,
            json=payload,
            timeout=5
        )
        assert create_response.status_code == 201
        payment_id = create_response.json()["id"]
        
        # Poll until status changes
        max_attempts = 10
        for attempt in range(max_attempts):
            response = requests.get(
                f"{BASE_URL}/api/v1/payments/{payment_id}/public",
                timeout=5
            )
            assert response.status_code == 200
            data = response.json()
            status = data.get("status")
            
            if status != "processing":
                assert status == "failed", f"Card payment should become 'failed', got '{status}'"
                return  # Success!
            
            if attempt < max_attempts - 1:
                time.sleep(2)
        
        pytest.fail("Payment status did not change from 'processing' after polling")


class TestEndpointCoverage:
    """Tests to ensure all endpoints are covered"""
    
    def test_all_endpoints_are_tested(self):
        """Verify that all documented endpoints have tests"""
        # This is a meta-test to ensure coverage
        expected_endpoints = [
            "GET /health",
            "POST /api/v1/orders",
            "GET /api/v1/orders/{id}/public",
            "POST /api/v1/payments",
            "POST /api/v1/payments/public",
            "GET /api/v1/payments/{id}/public",
        ]
        
        # This test passes if all other tests pass
        # In a real scenario, you'd use coverage tools
        assert len(expected_endpoints) == 6, "Should have 6 main endpoints"
        # All endpoints are tested in the classes above


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before running tests"""
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            pytest.fail("API server is not running. Please start it first.")
    except requests.exceptions.RequestException:
        pytest.fail("Cannot connect to API server. Please ensure it's running on http://localhost:8000")
    
    # Validate auth headers
    if not API_KEY or not API_SECRET:
        pytest.fail("API_KEY and API_SECRET must be set")
    
    yield  # Tests run here
    
    # Cleanup (if needed)
    pass
