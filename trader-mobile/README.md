# SUPER TRADER AI — Mobile prototype 0.1

This folder contains the first Android-friendly installable web-app shell for the SUPER TRADER AI project.

## Current status
- Persian RTL mobile dashboard.
- Installable PWA manifest and basic offline shell cache.
- Explicit demo-only mode.
- No live prices, exchange credentials, account balances, signals, or order execution.
- All market values are intentionally shown as unavailable rather than fabricated.

## Open on Android
After this branch is reviewed and merged/published through GitHub Pages, open the published `/trader-mobile/` path in Chrome and use **Add to Home screen**. This branch is not yet published.

## Planned architecture
- Android client: PWA first for phone-only development; later wrap with Capacitor or build a native Android client if needed.
- Backend: HTTPS API service; exchange credentials and signing keys remain server-side, never in the app.
- Market-data service: separate read-only adapters for Iranian FX sources, CoinMarketCap, and supported exchanges.
- Strategy engine: deterministic rules first; AI may explain/score signals but must not independently bypass risk controls.
- Risk engine: position sizing, daily loss limit, drawdown circuit breaker, stale-data guard, duplicate-order guard.
- Execution service: disabled until exchange API terms, user eligibility, regional restrictions, and order permissions are verified.
- Database: encrypted secrets store plus auditable order/decision records; never store withdrawal credentials.

## Release gates
1. Validate source licensing and API terms for each data provider.
2. Verify the user's legal eligibility and account access for each exchange.
3. Test with historical data, then paper trading with live market data.
4. Reconcile simulated fills against actual bid/ask, fees, slippage, and transfer costs.
5. Require explicit user approval before enabling any real-money order route.

## Security baseline
- No withdrawal permission in any exchange API key.
- No API keys in browser storage, GitHub, app source, or screenshots.
- HTTPS only; server-side secret storage; key rotation and audit logs.
- Kill switch and fail-closed behavior when market data or exchange state is uncertain.
