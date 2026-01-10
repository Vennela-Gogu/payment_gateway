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
