#!/usr/bin/env python3
"""
Test script for Payment Gateway API endpoints
"""
import requests
import json
import time
import sys

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "key_test_abc123"
API_SECRET = "secret_test_xyz789"

# Headers for authenticated endpoints
AUTH_HEADERS = {
    "X-API-Key": API_KEY,
    "X-API-Secret": API_SECRET,
    "Content-Type": "application/json"
}

def validate_auth_headers():
    """Validate that auth headers are properly configured"""
    if not API_KEY or not API_SECRET:
        raise ValueError("API_KEY and API_SECRET must be set")
    if "X-API-Key" not in AUTH_HEADERS or "X-API-Secret" not in AUTH_HEADERS:
        raise ValueError("AUTH_HEADERS must include X-API-Key and X-API-Secret")
    return True

# Headers for public endpoints
PUBLIC_HEADERS = {
    "Content-Type": "application/json"
}

def print_test(name):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")

def print_result(success, response=None, error=None):
    if success:
        print("[PASS] PASSED")
        if response:
            print(f"Response: {json.dumps(response, indent=2)}")
    else:
        print("[FAIL] FAILED")
        if error:
            print(f"Error: {error}")
        if response:
            print(f"Response: {json.dumps(response, indent=2)}")

def test_health():
    """Test health endpoint"""
    print_test("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        success = response.status_code == 200
        result = response.json() if success else response.text
        print_result(success, result)
        # Health endpoint should return status "ok" (from routes/health.py)
        if success and isinstance(result, dict):
            status = result.get("status")
            if status in ["ok", "healthy"]:  # Accept both possible values
                print(f"[OK] Health check returned status: {status}")
        return success
    except Exception as e:
        print_result(False, error=str(e))
        return False

def test_create_order():
    """Test creating an order (authenticated)"""
    print_test("Create Order (Authenticated)")
    try:
        payload = {
            "amount": 50000,
            "currency": "INR",
            "receipt": f"test_receipt_{int(time.time())}",
            "notes": {"test": "data"}
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            headers=AUTH_HEADERS,
            json=payload,
            timeout=5
        )
        success = response.status_code == 201
        result = response.json() if success else response.text
        print_result(success, result)
        
        if success:
            return result.get("id")
        return None
    except Exception as e:
        print_result(False, error=str(e))
        return None

def test_create_order_invalid_amount():
    """Test creating an order with invalid amount"""
    print_test("Create Order - Invalid Amount (< 100)")
    try:
        payload = {
            "amount": 50,
            "currency": "INR",
            "receipt": f"test_receipt_invalid_{int(time.time())}"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            headers=AUTH_HEADERS,
            json=payload,
            timeout=5
        )
        success = response.status_code == 400
        result = response.json() if success else response.text
        print_result(success, result)
        return success
    except Exception as e:
        print_result(False, error=str(e))
        return False

def test_create_order_invalid_auth():
    """Test creating an order with invalid credentials"""
    print_test("Create Order - Invalid Authentication")
    try:
        payload = {
            "amount": 50000,
            "currency": "INR",
            "receipt": f"test_receipt_auth_{int(time.time())}"
        }
        invalid_headers = {
            "X-API-Key": "invalid_key",
            "X-API-Secret": "invalid_secret",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/orders",
            headers=invalid_headers,
            json=payload,
            timeout=5
        )
        success = response.status_code == 401
        result = response.json() if success else response.text
        print_result(success, result)
        return success
    except Exception as e:
        print_result(False, error=str(e))
        return False

def test_get_order_public(order_id):
    """Test getting order details (public)"""
    print_test(f"Get Order Public - Order ID: {order_id}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/orders/{order_id}/public",
            timeout=5
        )
        success = response.status_code == 200
        result = response.json() if success else response.text
        print_result(success, result)
        return success
    except Exception as e:
        print_result(False, error=str(e))
        return False

def test_get_order_public_invalid():
    """Test getting non-existent order"""
    print_test("Get Order Public - Invalid Order ID")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/orders/invalid_order_id/public",
            timeout=5
        )
        success = response.status_code == 404
        result = response.json() if success else response.text
        print_result(success, result)
        return success
    except Exception as e:
        print_result(False, error=str(e))
        return False

def test_create_payment(order_id):
    """Test creating a payment (authenticated)"""
    print_test(f"Create Payment (Authenticated) - Order ID: {order_id}")
    try:
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
        success = response.status_code == 201
        result = response.json() if success else response.text
        print_result(success, result)
        
        if success:
            # Authenticated payments use "captured" for UPI (different from public "success")
            payment_status = result.get("status") if isinstance(result, dict) else None
            if payment_status == "captured":
                print("[OK] Authenticated UPI payment correctly returns 'captured' status")
            else:
                print(f"[WARN] Expected 'captured' status for authenticated payment, got '{payment_status}'")
            return result.get("id")
        return None
    except Exception as e:
        print_result(False, error=str(e))
        return None

def test_create_payment_card(order_id):
    """Test creating a payment with card method (should fail)"""
    print_test(f"Create Payment - Card Method (Should Fail) - Order ID: {order_id}")
    try:
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
        success = response.status_code == 201
        result = response.json() if success else response.text
        if success:
            # Card payments should have status "failed"
            payment_status = result.get("status") if isinstance(result, dict) else None
            print_result(success, result)
            if payment_status == "failed":
                print("[OK] Card payment correctly returns 'failed' status")
            else:
                print(f"[WARN] Expected 'failed' status, got '{payment_status}'")
        else:
            print_result(success, result)
        return success
    except Exception as e:
        print_result(False, error=str(e))
        return False

def test_create_payment_public(order_id):
    """Test creating a payment (public endpoint)"""
    print_test(f"Create Payment Public - Order ID: {order_id}")
    try:
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
        success = response.status_code == 201
        result = response.json() if success else response.text
        print_result(success, result)
        
        if success:
            payment_id = result.get("id") if isinstance(result, dict) else None
            payment_status = result.get("status") if isinstance(result, dict) else None
            if payment_status == "processing":
                print("[OK] Payment correctly starts with 'processing' status")
            return payment_id
        return None
    except Exception as e:
        print_result(False, error=str(e))
        return None

def test_get_payment_public(payment_id):
    """Test getting payment status (public)"""
    print_test(f"Get Payment Public - Payment ID: {payment_id}")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/payments/{payment_id}/public",
            timeout=5
        )
        success = response.status_code == 200
        result = response.json() if success else response.text
        print_result(success, result)
        
        if success and isinstance(result, dict):
            status = result.get("status")
            print(f"Payment Status: {status}")
        return success
    except Exception as e:
        print_result(False, error=str(e))
        return False

def test_payment_status_polling(payment_id):
    """Test polling payment status until it changes from processing"""
    print_test(f"Payment Status Polling - Payment ID: {payment_id}")
    try:
        max_attempts = 10
        for attempt in range(max_attempts):
            response = requests.get(
                f"{BASE_URL}/api/v1/payments/{payment_id}/public",
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                print(f"Attempt {attempt + 1}: Status = {status}")
                
                if status != "processing":
                    print(f"[OK] Payment status changed to: {status}")
                    return True
            
            time.sleep(2)
        
        print("[WARN] Payment status did not change after polling")
        return False
    except Exception as e:
        print_result(False, error=str(e))
        return False

def main():
    print("\n" + "="*60)
    print("Payment Gateway API Test Suite")
    print("="*60)
    
    # Validate auth headers
    try:
        validate_auth_headers()
        print("[OK] Auth headers configured correctly")
    except ValueError as e:
        print(f"[ERROR] Auth header configuration error: {e}")
        sys.exit(1)
    
    # Check if API is running
    print("\nChecking if API is running...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print("[OK] API is running")
    except Exception as e:
        print(f"[ERROR] API is not running. Please start the API server first.")
        print(f"   Error: {e}")
        print(f"\n   To start the API:")
        print(f"   cd backend && uvicorn app.main:app --reload")
        sys.exit(1)
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    
    # Test 2: Create order (authenticated)
    order_id = test_create_order()
    results.append(("Create Order", order_id is not None))
    
    if not order_id:
        print("\n[ERROR] Cannot continue tests without a valid order ID")
        return
    
    # Test 3: Get order public
    results.append(("Get Order Public", test_get_order_public(order_id)))
    
    # Test 4: Get invalid order
    results.append(("Get Invalid Order", test_get_order_public_invalid()))
    
    # Test 5: Create order with invalid amount
    results.append(("Create Order - Invalid Amount", test_create_order_invalid_amount()))
    
    # Test 6: Create order with invalid auth
    results.append(("Create Order - Invalid Auth", test_create_order_invalid_auth()))
    
    # Test 7: Create payment (authenticated) - UPI
    payment_id = test_create_payment(order_id)
    results.append(("Create Payment (UPI)", payment_id is not None))
    
    # Test 8: Create payment (authenticated) - Card
    test_create_payment_card(order_id)
    
    # Test 9: Create payment (public) - UPI
    public_payment_id = test_create_payment_public(order_id)
    results.append(("Create Payment Public", public_payment_id is not None))
    
    if public_payment_id:
        # Test 10: Get payment public
        results.append(("Get Payment Public", test_get_payment_public(public_payment_id)))
        
        # Test 11: Poll payment status
        results.append(("Payment Status Polling", test_payment_status_polling(public_payment_id)))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} - {name}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
