"""
Pytest configuration and shared fixtures
"""
import pytest
import requests
import time

BASE_URL = "http://localhost:8000"
API_KEY = "key_test_abc123"
API_SECRET = "secret_test_xyz789"

AUTH_HEADERS = {
    "X-API-Key": API_KEY,
    "X-API-Secret": API_SECRET,
    "Content-Type": "application/json"
}


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API"""
    return BASE_URL


@pytest.fixture(scope="session")
def auth_headers():
    """Authentication headers"""
    return AUTH_HEADERS


@pytest.fixture(scope="session")
def test_order_id(api_base_url, auth_headers):
    """Create a test order and return its ID"""
    payload = {
        "amount": 50000,
        "currency": "INR",
        "receipt": f"test_fixture_{int(time.time())}"
    }
    response = requests.post(
        f"{api_base_url}/api/v1/orders",
        headers=auth_headers,
        json=payload,
        timeout=5
    )
    if response.status_code != 201:
        pytest.fail(f"Failed to create test order: {response.text}")
    return response.json()["id"]


@pytest.fixture(scope="function")
def fresh_order_id(api_base_url, auth_headers):
    """Create a fresh order for each test"""
    payload = {
        "amount": 50000,
        "currency": "INR",
        "receipt": f"test_fresh_{int(time.time())}_{int(time.time() * 1000) % 10000}"
    }
    response = requests.post(
        f"{api_base_url}/api/v1/orders",
        headers=auth_headers,
        json=payload,
        timeout=5
    )
    if response.status_code != 201:
        pytest.fail(f"Failed to create fresh order: {response.text}")
    return response.json()["id"]
