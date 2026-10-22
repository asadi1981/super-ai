"""Read-only market-data API for SUPER TRADER AI.
No exchange credentials, account access, or order execution are implemented.
"""
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

APP_VERSION = "0.1.0"
PROVIDER_URL = "https://api.coingecko.com/api/v3/simple/price"
ASSETS = {"bitcoin": "BTC", "ethereum": "ETH", "tether": "USDT"}
CACHE_SECONDS = int(os.getenv("QUOTE_CACHE_SECONDS", "45"))
STALE_AFTER_SECONDS = int(os.getenv("QUOTE_STALE_AFTER_SECONDS", "180"))
_timeout = int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "8"))

app = FastAPI(title="SUPER TRADER AI Read-only API", version=APP_VERSION)
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET"],
        allow_headers=["Content-Type"],
    )

_lock = Lock()
_cache = {"saved_at": 0.0, "payload": None}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def fetch_quotes():
    params = urlencode({
        "ids": ",".join(ASSETS.keys()),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_last_updated_at": "true",
    })
    request = Request(
        PROVIDER_URL + "?" + params,
        headers={"Accept": "application/json", "User-Agent": "SUPER-TRADER-AI/0.1"},
    )
    try:
        with urlopen(request, timeout=_timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 429:
            raise HTTPException(status_code=503, detail="Provider rate limit reached; retry later")
        raise HTTPException(status_code=502, detail="Market-data provider returned an error")
    except (URLError, TimeoutError, ValueError):
        raise HTTPException(status_code=502, detail="Market-data provider unavailable")

    received_at = utc_now()
    quotes = []
    for asset_id, symbol in ASSETS.items():
        item = raw.get(asset_id) or {}
        price = item.get("usd")
        if not isinstance(price, (int, float)) or price <= 0:
            continue
        provider_epoch = item.get("last_updated_at")
        observed_at = (
            datetime.fromtimestamp(provider_epoch, timezone.utc).isoformat()
            if isinstance(provider_epoch, (int, float)) else None
        )
        quotes.append({
            "instrument": symbol + "/USD",
            "base": symbol,
            "quote": "USD",
            "last": price,
            "bid": None,
            "ask": None,
            "change_24h_pct": item.get("usd_24h_change"),
            "volume": None,
            "provider": "CoinGecko",
            "observed_at": observed_at,
            "received_at": received_at,
            "source_status": "ok" if observed_at else "timestamp_missing",
        })
    if not quotes:
        raise HTTPException(status_code=502, detail="Provider returned no valid quotes")
    return {
        "provider": "CoinGecko",
        "received_at": received_at,
        "quotes": quotes,
        "notice": "Aggregated reference prices; not executable exchange bid/ask quotes.",
    }


@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION, "mode": "read_only"}


@app.get("/api/v1/quotes")
def get_quotes():
    now = monotonic()
    with _lock:
        if _cache["payload"] and now - _cache["saved_at"] < CACHE_SECONDS:
            payload = _cache["payload"]
        else:
            payload = fetch_quotes()
            _cache["payload"] = payload
            _cache["saved_at"] = now

    age_seconds = max(0, int((datetime.now(timezone.utc) -
                              datetime.fromisoformat(payload["received_at"])).total_seconds()))
    result = dict(payload)
    result["age_seconds"] = age_seconds
    result["stale"] = age_seconds > STALE_AFTER_SECONDS
    return result
