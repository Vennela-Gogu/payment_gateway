export default function Success() {
  const params = new URLSearchParams(window.location.search);
  const paymentId = params.get("payment_id");

  return (
    <div data-test-id="success-state">
      <h2>Payment Successful</h2>

      <p>
        Payment ID:
        <span data-test-id="payment-id">{paymentId}</span>
      </p>

      <div data-test-id="success-message">
        Your payment has been processed successfully
      </div>
    </div>
  );
}