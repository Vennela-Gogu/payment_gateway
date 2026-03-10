import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function Checkout() {
  const params = new URLSearchParams(window.location.search);
  const orderId = params.get("order_id");

  const [order, setOrder] = useState(null);
  const [method, setMethod] = useState(null);
  const [paymentId, setPaymentId] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const embedded = new URLSearchParams(window.location.search).get("embedded") === "true";

  // Fetch order details (PUBLIC)
  useEffect(() => {
    if (!orderId) return;

    fetch(`${API_BASE}/api/v1/orders/${orderId}/public`)
      .then(res => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then(setOrder)
      .catch(() => setError("Invalid order"));
  }, [orderId]);

  // Poll payment status
  useEffect(() => {
    if (!paymentId || status !== "processing") return;

    const interval = setInterval(() => {
      fetch(`${API_BASE}/api/v1/payments/${paymentId}/public`)
        .then(res => res.json())
        .then(data => {
          if (data.status !== "processing") {
            clearInterval(interval);
            if (embedded) {
              window.parent.postMessage(
                {
                  type: data.status === "success" ? "payment_success" : "payment_failed",
                  data,
                },
                "*"
              );
            } else {
              if (data.status === "success") {
                window.location.href = `/success?payment_id=${paymentId}`;
              } else {
                window.location.href = `/failure`;
              }
            }
          }
        });
    }, 2000);

    return () => clearInterval(interval);
  }, [paymentId, status]);

  const startPayment = (method) => {
    setStatus("processing");

    fetch(`${API_BASE}/api/v1/payments/public`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        order_id: order.id,
        method
      })
    })
      .then(res => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then(data => setPaymentId(data.id))
      .catch(() => {
        setStatus("error");
        setError("Payment could not be processed");
      });
  };

  if (error) {
    return (
      <div data-test-id="error-state">
        <p data-test-id="error-message">{error}</p>
        <button data-test-id="retry-button" onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  if (!order) return <div>Loading...</div>;

  return (
    <div data-test-id="checkout-container">

      {/* Order Summary */}
      <div data-test-id="order-summary">
        <h2>Payment</h2>
        <span data-test-id="order-amount">₹{order.amount}</span>
        <span data-test-id="order-id">{order.id}</span>
      </div>

      {/* Payment Method Selector */}
      <div data-test-id="payment-methods">
        <button data-test-id="method-upi" onClick={() => setMethod("upi")}>
          UPI
        </button>
        <button data-test-id="method-card" onClick={() => setMethod("card")}>
          Card
        </button>
      </div>

      {/* UPI Form */}
      {method === "upi" && (
        <form data-test-id="upi-form">
          <input
            data-test-id="upi-input"
            placeholder="yourname@upi"
          />
          <button
            data-test-id="pay-button"
            type="button"
            onClick={() => startPayment("upi")}
          >
            Pay Now
          </button>
        </form>
      )}

      {/* Card Form */}
      {method === "card" && (
        <form data-test-id="card-form">
          <input data-test-id="card-number-input" placeholder="Card Number" />
          <input data-test-id="expiry-input" placeholder="MM/YY" />
          <input data-test-id="cvv-input" placeholder="CVV" />
          <input data-test-id="cardholder-name-input" placeholder="Name" />
          <button
            data-test-id="pay-button"
            type="button"
            onClick={() => startPayment("card")}
          >
            Pay ₹{order.amount}
          </button>
        </form>
      )}

      {/* Processing State */}
      {status === "processing" && (
        <div data-test-id="processing-state">
          <span data-test-id="processing-message">
            Processing payment...
          </span>
        </div>
      )}
    </div>
  );
}