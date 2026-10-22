// SUPER TRADER AI prototype. No exchange connection and no order execution.
"use strict";
if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch(() => {
      // Offline caching is optional; the dashboard remains usable without it.
    });
  });
}
