(function () {
  class PaymentGateway {
    constructor(options = {}) {
      if (!options.key) throw new Error("PaymentGateway requires a key");
      if (!options.orderId) throw new Error("PaymentGateway requires an orderId");

      this.key = options.key;
      this.orderId = options.orderId;
      this.onSuccess = typeof options.onSuccess === "function" ? options.onSuccess : () => {};
      this.onFailure = typeof options.onFailure === "function" ? options.onFailure : () => {};
      this.onClose = typeof options.onClose === "function" ? options.onClose : () => {};
      this.checkoutUrl = options.checkoutUrl || "http://localhost:3001/checkout";
      this._messageHandler = this._handleMessage.bind(this);
      this._modal = null;
      this._iframe = null;
    }

    open() {
      if (this._modal) return;

      const overlay = document.createElement("div");
      overlay.id = "payment-gateway-modal";
      overlay.setAttribute("data-testid", "payment-modal");
      overlay.style.position = "fixed";
      overlay.style.top = "0";
      overlay.style.left = "0";
      overlay.style.width = "100vw";
      overlay.style.height = "100vh";
      overlay.style.background = "rgba(0,0,0,0.5)";
      overlay.style.display = "flex";
      overlay.style.alignItems = "center";
      overlay.style.justifyContent = "center";
      overlay.style.zIndex = "999999";

      const content = document.createElement("div");
      content.className = "modal-content";
      content.style.position = "relative";
      content.style.width = "420px";
      content.style.maxWidth = "90vw";
      content.style.height = "640px";
      content.style.background = "#fff";
      content.style.boxShadow = "0 20px 60px rgba(0,0,0,0.25)";
      content.style.borderRadius = "12px";
      content.style.overflow = "hidden";

      const iframe = document.createElement("iframe");
      iframe.setAttribute("data-testid", "payment-iframe");
      iframe.style.width = "100%";
      iframe.style.height = "100%";
      iframe.style.border = "0";
      iframe.src = `${this.checkoutUrl}?order_id=${encodeURIComponent(this.orderId)}&embedded=true`;

      const closeButton = document.createElement("button");
      closeButton.setAttribute("data-testid", "close-modal-button");
      closeButton.textContent = "×";
      closeButton.style.position = "absolute";
      closeButton.style.top = "10px";
      closeButton.style.right = "10px";
      closeButton.style.width = "32px";
      closeButton.style.height = "32px";
      closeButton.style.border = "none";
      closeButton.style.background = "rgba(0,0,0,0.6)";
      closeButton.style.color = "#fff";
      closeButton.style.borderRadius = "16px";
      closeButton.style.cursor = "pointer";
      closeButton.style.fontSize = "18px";
      closeButton.addEventListener("click", () => this.close());

      content.appendChild(closeButton);
      content.appendChild(iframe);
      overlay.appendChild(content);
      document.body.appendChild(overlay);

      this._modal = overlay;
      this._iframe = iframe;

      window.addEventListener("message", this._messageHandler, false);
    }

    close() {
      if (this._modal) {
        this._modal.remove();
        this._modal = null;
        this._iframe = null;
      }
      window.removeEventListener("message", this._messageHandler, false);
      this.onClose();
    }

    _handleMessage(event) {
      // Allow all origins by default, but ensure the expected message format
      const data = event.data;
      if (!data || typeof data !== "object") return;

      if (data.type === "payment_success") {
        this.onSuccess(data.data);
        this.close();
      } else if (data.type === "payment_failed") {
        this.onFailure(data.data);
        this.close();
      } else if (data.type === "close_modal") {
        this.close();
      }
    }
  }

  if (typeof window !== "undefined") {
    window.PaymentGateway = PaymentGateway;
  }
})();
