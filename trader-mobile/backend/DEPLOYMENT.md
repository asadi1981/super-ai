# Deployment notes

1. Use a continuously available Python 3.10+ HTTPS host. A free/sleeping service is only suitable for a temporary smoke test, not 24/7 monitoring.
2. Install dependencies from requirements.txt.
3. Start the service with: uvicorn app:app --host 0.0.0.0 --port $PORT
4. Configure CORS_ORIGINS to the exact HTTPS origin of the frontend if frontend and API are on different origins. Never use wildcard origins for an authenticated production app.
5. Prefer a same-origin reverse proxy so the frontend can call /api/v1/quotes.
6. Verify /health and /api/v1/quotes before connecting the dashboard.
7. Monitor provider errors and rate limits. The public CoinGecko API has variable throughput; the application intentionally caches and polls slowly.
8. Do not add exchange credentials yet. No trading endpoints exist in this service.

## Smoke-test checklist
- [ ] HTTPS certificate valid
- [ ] /health returns status: ok
- [ ] /api/v1/quotes returns valid BTC/USD, ETH/USD and USDT/USD prices
- [ ] observed_at and received_at are present
- [ ] provider outage returns an error rather than invented/old prices
- [ ] stale data is never treated as a signal
- [ ] dashboard refresh works after phone is offline and reconnects