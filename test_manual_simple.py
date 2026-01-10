#!/usr/bin/env python3
"""
Simple manual test script for all API endpoints
Run this to test all endpoints step by step
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_KEY = "key_test_abc123"
API_SECRET = "secret_test_xyz789"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response, show_status=True):
    if show_status:
        print(f"Status Code: {response.status_code}")
    
    try:
        data = response.json()
        print("Response:")
        print(json.dumps(data, indent=2))
        return data
    except:
        print("Response (text):")
        print(response.text)
        return None

# Test 1: Health Check
print_section("1. Health Check")
response = requests.get(f"{BASE_URL}/health")
print_response(response)

# Test 2: Create Order (Authenticated)
print_section("2. Create Order (Authenticated)")
headers = {
    "X-API-Key": API_KEY,
    "X-API-Secret": API_SECRET,
    "Content-Type": "application/json"
}
order_data = {
    "amount": 50000,
    "currency": "INR",
    "receipt": f"test_manual_{int(time.time())}",
    "notes": {"test": "manual testing"}
}
response = requests.post(f"{BASE_URL}/api/v1/orders", headers=headers, json=order_data)
order = print_response(response)
order_id = order.get("id") if order else None

if not order_id:
    print("\n[ERROR] Failed to create order. Cannot continue.")
    exit(1)

# Test 3: Get Order Public
print_section("3. Get Order Public")
response = requests.get(f"{BASE_URL}/api/v1/orders/{order_id}/public")
print_response(response)

# Test 4: Create Payment (Authenticated) - UPI
print_section("4. Create Payment (Authenticated) - UPI")
payment_data = {
    "order_id": order_id,
    "method": "upi"
}
response = requests.post(f"{BASE_URL}/api/v1/payments", headers=headers, json=payment_data)
print_response(response)

# Test 5: Create Payment (Authenticated) - Card (should fail)
print_section("5. Create Payment (Authenticated) - Card (Expected: failed)")
payment_data_card = {
    "order_id": order_id,
    "method": "card"
}
response = requests.post(f"{BASE_URL}/api/v1/payments", headers=headers, json=payment_data_card)
print_response(response)

# Test 6: Create Payment Public - UPI
print_section("6. Create Payment Public - UPI")
public_headers = {"Content-Type": "application/json"}
response = requests.post(f"{BASE_URL}/api/v1/payments/public", headers=public_headers, json=payment_data)
payment = print_response(response)
payment_id = payment.get("id") if payment else None

if not payment_id:
    print("\n[ERROR] Failed to create public payment. Cannot continue.")
    exit(1)

# Test 7: Get Payment Public (immediately)
print_section("7. Get Payment Public (Initial Status)")
response = requests.get(f"{BASE_URL}/api/v1/payments/{payment_id}/public")
print_response(response)

# Test 8: Get Payment Public (after delay - status should change)
print_section("8. Get Payment Public (After 3 seconds - Status should update)")
print("Waiting 3 seconds for payment status to update...")
time.sleep(3)
response = requests.get(f"{BASE_URL}/api/v1/payments/{payment_id}/public")
print_response(response)

# Test 9: Error Cases
print_section("9. Error Case - Invalid Amount (< 100)")
invalid_order = {
    "amount": 50,
    "currency": "INR",
    "receipt": "test_invalid_amount"
}
response = requests.post(f"{BASE_URL}/api/v1/orders", headers=headers, json=invalid_order)
print_response(response)

print_section("10. Error Case - Invalid Authentication")
invalid_headers = {
    "X-API-Key": "wrong_key",
    "X-API-Secret": "wrong_secret",
    "Content-Type": "application/json"
}
response = requests.post(f"{BASE_URL}/api/v1/orders", headers=invalid_headers, json=order_data)
print_response(response)

print_section("11. Error Case - Non-existent Order")
response = requests.get(f"{BASE_URL}/api/v1/orders/invalid_order_id/public")
print_response(response)

print_section("12. Error Case - Payment for Non-existent Order")
invalid_payment = {
    "order_id": "invalid_order_id",
    "method": "upi"
}
response = requests.post(f"{BASE_URL}/api/v1/payments/public", headers=public_headers, json=invalid_payment)
print_response(response)

print("\n" + "="*60)
print("  All Tests Complete!")
print("="*60)
print(f"\nOrder ID used: {order_id}")
print(f"Payment ID used: {payment_id}")
