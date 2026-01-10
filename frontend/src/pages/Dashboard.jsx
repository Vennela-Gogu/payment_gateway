import React from "react";

const Dashboard = () => {
  return (
    <div data-test-id="dashboard" style={{ padding: "20px" }}>
      <div data-test-id="api-credentials">
        <span data-test-id="api-key">key_test_abc123</span>
        <span data-test-id="api-secret">secret_test_xyz789</span>
      </div>

      <div data-test-id="stats-container" style={{ marginTop: "20px" }}>
        <div data-test-id="total-transactions">Total Transactions: 0</div>
        <div data-test-id="total-amount">Total Amount: $0</div>
        <div data-test-id="success-rate">Success Rate: 0%</div>
      </div>

      <table data-test-id="transactions-table" border="1" style={{ marginTop: "20px", width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th>Payment ID</th>
            <th>Order ID</th>
            <th>Amount</th>
            <th>Method</th>
            <th>Status</th>
            <th>Created At</th>
          </tr>
        </thead>
        <tbody>
          {/* Transactions will go here */}
        </tbody>
      </table>
    </div>
  );
};

export default Dashboard;