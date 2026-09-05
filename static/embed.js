// static/embed.js
// WHAT: Client-facing loader script. Reads optional config the client sets
// BEFORE including this script, and passes it to the widget via URL params.
// WHY: Lets each client customize brand color/store name WITHOUT us
// maintaining a separate widget.html per client — one file serves everyone.

(function () {
  const WIDGET_BASE_URL = "http://127.0.0.1:8000";

  if (window.__storeChatWidgetLoaded) return;
  window.__storeChatWidgetLoaded = true;

  // WHY: Clients set window.StoreChatConfig BEFORE the script tag to
  // customize their widget — if they don't, we fall back to sensible
  // defaults so the widget still works with zero configuration.
  const config = window.StoreChatConfig || {};
  const color = config.color || "#2563eb";
  const storeName = config.storeName || "Store Assistant";

  // WHY: Build the iframe URL with config passed as query params —
  // widget.html reads these on load via URLSearchParams.
  const params = new URLSearchParams({
    color: color,
    storeName: storeName,
  });

  const button = document.createElement("div");
  button.innerHTML = "💬";
  Object.assign(button.style, {
    position: "fixed",
    bottom: "20px",
    right: "20px",
    width: "56px",
    height: "56px",
    borderRadius: "50%",
    background: color,
    color: "white",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "24px",
    cursor: "pointer",
    boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
    zIndex: "999999",
  });

  const iframe = document.createElement("iframe");
  iframe.src = WIDGET_BASE_URL + "/static/widget.html?" + params.toString();
  Object.assign(iframe.style, {
    position: "fixed",
    bottom: "90px",
    right: "20px",
    width: "360px",
    height: "500px",
    border: "none",
    borderRadius: "12px",
    boxShadow: "0 8px 30px rgba(0,0,0,0.2)",
    zIndex: "999999",
    display: "none",
  });

  let isOpen = false;
  button.addEventListener("click", () => {
    isOpen = !isOpen;
    iframe.style.display = isOpen ? "block" : "none";
    button.innerHTML = isOpen ? "✕" : "💬";
  });

  document.body.appendChild(iframe);
  document.body.appendChild(button);
})();