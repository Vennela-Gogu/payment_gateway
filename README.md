# Payment Gateway Simulator

This project is a simplified **Payment Gateway Simulator** that demonstrates how merchants can create orders, process payments, and view transaction statistics.  
It includes a backend API, a merchant dashboard frontend, and a checkout application, all containerized using Docker.

---

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React (Vite)
- **Checkout App**: React
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose

---

## Project Structure
payment_gateway/ ├── api/                # FastAPI backend ├── frontend/           # Merchant dashboard (React) ├── checkout/           # Checkout UI (React) ├── docker-compose.yml ├── README.md └── .gitignore

---

## How to Run the Project

### Prerequisites
- Docker
- Docker Compose

### Steps

```bash
git clone https://github.com/Vennela-Gogu/payment_gateway.git
cd payment_gateway
docker-compose up -d --build
After successful startup, the services will be available at:
Backend API: http://localhost:8000
Swagger Docs: http://localhost:8000/docs
Frontend Dashboard: http://localhost:3000
Checkout App: http://localhost:3001
API Documentation
Swagger UI is enabled for easy testing:

http://localhost:8000/docs
You can test all endpoints directly from the browser.
Available API Endpoints
Health Check

GET /api/v1/health
No request body required.
Create Order

POST /api/v1/orders
Headers

x-api-key: key_test_abc123
x-api-secret: secret_test_xyz789
Body
Json
{
  "order_id": "order_001",
  "amount": 1500,
  "currency": "INR"
}
Process Payment

POST /api/v1/payments
Headers

x-api-key: key_test_abc123
x-api-secret: secret_test_xyz789
Body
Json
{
  "order_id": "order_001",
  "payment_method": "card",
  "card_number": "4111111111111111",
  "expiry": "12/26",
  "cvv": "123"
}

Authentication
All protected endpoints require merchant authentication using:
x-api-key
x-api-secret
These credentials are validated against the merchants table in PostgreSQL.
Database
The application uses PostgreSQL for storing:
Merchants
Orders
Payments
Transactions
The database runs as a Docker service and connects automatically via Docker Compose.
Frontend Pages
Login Page
Merchant Dashboard
API credentials
Transaction statistics
Checkout Page
Each page includes data-test-id attributes to support automated testing.
=======
Payment Gateway – Async Processing & Webhooks
This project is a production-ready payment gateway built as an extension of an earlier payment system.
It enhances the basic payment flow with asynchronous processing, idempotency, secure webhooks, retries, and refunds, similar to real-world fintech platforms.
Key Features
API key–based authentication
Payment creation with safe retries (Idempotency-Key)
Asynchronous payment processing using Redis and Celery
Webhook notifications for payment status updates
HMAC signature verification for webhook security
Automatic retries with exponential backoff
Refund processing support
Dockerized setup for easy execution
Payment Flow (High Level)
Client creates a payment via API
Payment is stored with status pending
Background worker processes the payment asynchronously
Final status is updated (success / failed)
Merchant is notified via a signed webhook
Authentication
All APIs require API credentials sent as headers:
Copy code

X-API-Key
X-API-Secret
Requests with invalid credentials are rejected.
Create Payment API
Endpoint
Copy code

POST /api/v1/payments
Optional Header
Copy code

Idempotency-Key
The idempotency key ensures duplicate requests return the same response and prevents double charging.
Asynchronous Processing
Payment processing is handled in the background using a queue.
This keeps APIs fast, scalable, and resilient to failures.
Webhooks & Security
Webhooks are triggered on payment status changes
Each webhook payload is signed using HMAC SHA-256
Merchants verify authenticity using the shared secret
Failed deliveries are retried with exponential backoff
Refunds
Refunds can be initiated for completed payments using a dedicated API endpoint.
Refund status is tracked independently from the payment.
Running the Project
Copy code
docker-compose up --build
This starts the API server, database, Redis, and background worker.

