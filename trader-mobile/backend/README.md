# SUPER TRADER AI — Read-only market data API

This service is a first backend foundation. It only reads aggregated public crypto reference prices from CoinGecko. It cannot access exchange accounts, place orders, transfer funds, or withdraw.

## Endpoints

- `GET /health` — process health
- `GET /api/v1/quotes` — BTC/USD, ETH/USD and USDT/USD normalized quotes

Each quote includes provider, observed_at, received_at, source_status and last price. Bid/ask are deliberately null: aggregated reference prices must not be presented as executable exchange quotes.

## Run locally

Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/api/v1/quotes`.

## Configuration

- `QUOTE_CACHE_SECONDS` (default 45)
- `QUOTE_STALE_AFTER_SECONDS` (default 180)
- `PROVIDER_TIMEOUT_SECONDS` (default 8)
- `CORS_ORIGINS` (comma-separated exact trusted frontend origins; leave empty if same-origin reverse proxy is used)

The public CoinGecko API has variable rate limits. Keep polling modestly, respect HTTP 429 responses, and do not assume a guaranteed update interval. This service caches responses briefly.

## Important limitations

- USD reference prices only; no Iranian free-market USD/EUR or USDT/IRT feed is wired yet.
- No candle history, technical signals, paper orders, exchange adapters, credentials, or live trading.
- CoinGecko data is aggregated reference data and may be delayed. It is not a substitute for exchange order-book bid/ask.
- Do not expose a future exchange API key in this service's public environment or frontend. Any future secrets belong in server-side secret storage, with withdrawal permission disabled.
- Deploy behind HTTPS. A sleeping/free host is not suitable for guaranteed 24/7 monitoring.
