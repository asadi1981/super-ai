# SUPER TRADER AI — Technical architecture

## Client
The first deliverable is a mobile-first installable PWA because development and operation currently need to be possible from an Android phone without a PC. It can later be packaged as an APK with Capacitor or replaced by a Kotlin/Jetpack Compose client without changing the backend contract.

Client responsibilities:
- Dashboard, watchlists, charts, signal explanations, paper portfolio, settings.
- Secure login and session handling.
- Display-only access to account and order status.
- Never store exchange API secrets or sign exchange requests.

## Backend services
1. API gateway/authentication: HTTPS, rate limits, device/session controls.
2. Market data: provider adapters, timestamping, source health, normalization into a common quote schema.
3. Analysis: trend, volatility, momentum, support/resistance, market regime.
4. Strategy coordinator: compare strategies and abstain when evidence conflicts.
5. Risk manager: independent pre-trade approval; strategy cannot override it.
6. Paper execution: simulated orders with bid/ask, fees, spread, slippage, partial fills, and latency.
7. Live execution: isolated service, disabled by default, allowlisted providers and symbols only.
8. Ledger/audit: immutable decision and order events; daily reconciliation.

## Initial conservative risk policy (simulation only)
- Risk budget per trade: 0.25% of paper equity.
- Daily loss stop: 0.5% of start-of-day paper equity.
- Drawdown circuit breaker: 3% from the paper-equity high-water mark.
- Pause after 3 consecutive losing trades.
- No leverage, margin, futures, or borrowing in the initial release.
- No trade if data is stale, provider states disagree materially, spread/fees are unknown, or order status cannot be reconciled.
These are provisional test parameters, not a profit guarantee or a live trading recommendation.

## Data model
Normalized quote fields: provider, instrument, base, quote, bid, ask, last, volume, observed_at, received_at, source_status.
Order fields: client_order_id, provider_order_id, account_id, instrument, side, type, quantity, limit_price, status, created_at, updated_at.
Every decision references exact quote timestamps and a strategy/risk-policy version.

## Provider policy
- CoinMarketCap is market-data only, not an execution venue.
- Exchange adapters are added only after official documentation and account eligibility are verified.
- Regional restrictions must be respected. Do not use VPNs, false residency, or third-party accounts to evade controls.
- Iranian FX rates may be quote-only if no lawful, supported execution API exists.

## Deployment
Backend must be a continuously available HTTPS service for unattended operation. Free hosting tiers may sleep, impose quotas, or change terms; therefore no always-on execution guarantee is assumed until a suitable host and budget are selected. The Android client may close or the phone may be offline while the server continues monitoring.
