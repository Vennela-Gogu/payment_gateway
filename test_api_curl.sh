#!/bin/bash
# Simple curl-based API tests
# Make sure the API server is running on http://localhost:8000

BASE_URL="http://localhost:8000"
API_KEY="key_test_abc123"
API_SECRET="secret_test_xyz789"

echo "=========================================="
echo "Payment Gateway API Tests (curl)"
echo "=========================================="

echo -e "\n1. Testing Health Endpoint"
curl -X GET "$BASE_URL/health" -w "\nStatus: %{http_code}\n"

echo -e "\n\n2. Testing Create Order (Authenticated)"
ORDER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/orders" \
  -H "X-API-Key: $API_KEY" \
  -H "X-API-Secret: $API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50000,
    "currency": "INR",
    "receipt": "test_receipt_123"
  }')
echo "$ORDER_RESPONSE" | python -m json.tool
ORDER_ID=$(echo "$ORDER_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")

if [ -z "$ORDER_ID" ]; then
  echo "Failed to get order ID"
  exit 1
fi

echo -e "\n\n3. Testing Get Order Public"
curl -X GET "$BASE_URL/api/v1/orders/$ORDER_ID/public" -w "\nStatus: %{http_code}\n" | python -m json.tool

echo -e "\n\n4. Testing Create Payment (Authenticated) - UPI"
PAYMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/payments" \
  -H "X-API-Key: $API_KEY" \
  -H "X-API-Secret: $API_SECRET" \
  -H "Content-Type: application/json" \
  -d "{
    \"order_id\": \"$ORDER_ID\",
    \"method\": \"upi\"
  }")
echo "$PAYMENT_RESPONSE" | python -m json.tool

echo -e "\n\n5. Testing Create Payment Public - UPI"
PUBLIC_PAYMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/payments/public" \
  -H "Content-Type: application/json" \
  -d "{
    \"order_id\": \"$ORDER_ID\",
    \"method\": \"upi\"
  }")
echo "$PUBLIC_PAYMENT_RESPONSE" | python -m json.tool
PUBLIC_PAYMENT_ID=$(echo "$PUBLIC_PAYMENT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")

if [ ! -z "$PUBLIC_PAYMENT_ID" ]; then
  echo -e "\n\n6. Testing Get Payment Public"
  sleep 2
  curl -X GET "$BASE_URL/api/v1/payments/$PUBLIC_PAYMENT_ID/public" -w "\nStatus: %{http_code}\n" | python -m json.tool
fi

echo -e "\n\n7. Testing Create Order - Invalid Amount (< 100)"
curl -X POST "$BASE_URL/api/v1/orders" \
  -H "X-API-Key: $API_KEY" \
  -H "X-API-Secret: $API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50,
    "currency": "INR",
    "receipt": "test_invalid"
  }' -w "\nStatus: %{http_code}\n" | python -m json.tool

echo -e "\n\n8. Testing Create Order - Invalid Auth"
curl -X POST "$BASE_URL/api/v1/orders" \
  -H "X-API-Key: invalid_key" \
  -H "X-API-Secret: invalid_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50000,
    "currency": "INR",
    "receipt": "test_auth"
  }' -w "\nStatus: %{http_code}\n" | python -m json.tool

echo -e "\n\n=========================================="
echo "Tests Complete"
echo "=========================================="
