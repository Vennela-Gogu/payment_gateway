import React from "react";

export default function Docs() {
  return (
    <div data-testid="api-docs" style={{ padding: "20px" }}>
      <h2>Integration Guide</h2>

      <section data-testid="section-create-order" style={{ marginBottom: "24px" }}>
        <h3>1. Create Order</h3>
        <pre data-testid="code-snippet-create-order" style={{ background: "#f5f5f5", padding: "12px" }}>
          <code>{`curl -X POST http://localhost:8000/api/v1/orders \
  -H "X-Api-Key: key_test_abc123" \
  -H "X-Api-Secret: secret_test_xyz789" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50000, "currency": "INR", "receipt": "receipt_123"}'`}</code>
        </pre>
      </section>

      <section data-testid="section-sdk-integration" style={{ marginBottom: "24px" }}>
        <h3>2. SDK Integration</h3>
        <pre data-testid="code-snippet-sdk" style={{ background: "#f5f5f5", padding: "12px" }}>
          <code>{`<script src="http://localhost:3001/checkout.js"></script>
<script>
  const checkout = new PaymentGateway({
    key: 'key_test_abc123',
    orderId: 'order_xyz',
    onSuccess: (response) => {
      console.log('Payment ID:', response.paymentId);
    },
    onFailure: (error) => {
      console.error('Payment failed', error);
    },
  });
  checkout.open();
</script>`}</code>
        </pre>
      </section>

      <section data-testid="section-webhook-verification">
        <h3>3. Verify Webhook Signature</h3>
        <pre data-testid="code-snippet-webhook" style={{ background: "#f5f5f5", padding: "12px" }}>
          <code>{`const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(JSON.stringify(payload))
    .digest('hex');
  return signature === expectedSignature;
}`}</code>
        </pre>
      </section>
    </div>
  );
}
