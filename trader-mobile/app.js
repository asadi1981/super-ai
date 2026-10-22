// SUPER TRADER AI read-only market-data client. No order execution exists.
"use strict";

const API_URL = "./api/v1/quotes";
const SYMBOL_TO_CARD = {
  "BTC/USD": "btc",
  "ETH/USD": "eth",
  "USDT/USD": "usdt"
};

function setText(selector, value) {
  const node = document.querySelector(selector);
  if (node) node.textContent = value;
}

function formatPrice(value) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: value >= 100 ? 2 : value >= 1 ? 4 : 6
  }).format(value) + " USD";
}

function formatTime(value) {
  if (!value) return "زمان منبع نامشخص";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "زمان منبع نامشخص";
  return new Intl.DateTimeFormat("fa-IR", {
    dateStyle: "short", timeStyle: "medium", timeZone: "Asia/Tehran"
  }).format(date);
}

function renderQuotes(payload) {
  const quotes = Array.isArray(payload.quotes) ? payload.quotes : [];
  let rendered = 0;
  for (const quote of quotes) {
    const cardKey = SYMBOL_TO_CARD[quote.instrument];
    if (!cardKey || typeof quote.last !== "number" || quote.last <= 0) continue;
    setText('[data-price="' + cardKey + '"]', formatPrice(quote.last));
    setText('[data-time="' + cardKey + '"]', "به‌روزرسانی: " + formatTime(quote.observed_at));
    rendered++;
  }
  if (!rendered) throw new Error("no_valid_quotes");
  const stale = Boolean(payload.stale);
  setText("#market-connection", stale ? "داده قدیمی" : "داده دریافت شد");
  setText("#market-updated", "دریافت از " + (payload.provider || "منبع نامشخص") +
    " · " + formatTime(payload.received_at));
  setText("#data-warning", payload.notice || "قیمت‌ها مرجع تجمیعی هستند، نه قیمت قابل اجرای سفارش.");
  setText("#analysis-status", stale
    ? "داده‌ها قدیمی‌اند؛ تحلیل و سیگنال‌سازی متوقف است."
    : "داده مرجع دریافت شد؛ موتور تحلیل هنوز در مرحله آماده‌سازی است.");
}

async function refreshQuotes() {
  setText("#market-connection", "در حال دریافت…");
  try {
    const response = await fetch(API_URL, { method: "GET", cache: "no-store" });
    if (!response.ok) throw new Error("api_" + response.status);
    renderQuotes(await response.json());
  } catch (error) {
    setText("#market-connection", "اتصال برقرار نیست");
    setText("#analysis-status", "منبع داده در دسترس نیست؛ هیچ سیگنالی صادر نمی‌شود.");
    setText("#market-updated", "برای دریافت قیمت، ابتدا سرور امن باید راه‌اندازی شود.");
  }
}

if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  });
}
window.addEventListener("load", () => {
  refreshQuotes();
  window.setInterval(refreshQuotes, 60000);
});
