export default function Failure() {
  return (
    <div data-test-id="error-state">
      <h2>Payment Failed</h2>

      <div data-test-id="error-message">
        Payment could not be processed
      </div>

      <button
        data-test-id="retry-button"
        onClick={() => window.history.back()}
      >
        Retry
      </button>
    </div>
  );
}