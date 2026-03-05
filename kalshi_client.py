"""
Kalshi REST API client.
Handles RSA-signed authentication for Kalshi's v2 API.
"""

from __future__ import annotations

import base64
import hashlib
import os
import time
from pathlib import Path
from typing import Any

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

PROD_BASE = "https://trading-api.kalshi.com/trade-api/v2"
DEMO_BASE = "https://demo-api.kalshi.co/trade-api/v2"


def _load_private_key(path: str):
    pem = Path(path).read_bytes()
    return serialization.load_pem_private_key(pem, password=None)


def _sign(private_key, method: str, path: str, timestamp_ms: int) -> str:
    msg = f"{timestamp_ms}{method}{path}".encode()
    sig = private_key.sign(msg, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()


class KalshiClient:
    def __init__(
        self,
        api_key_id: str | None = None,
        private_key_path: str | None = None,
        env: str = "demo",
    ):
        self.api_key_id = api_key_id or os.environ.get("KALSHI_API_KEY_ID", "")
        pkey_path = private_key_path or os.environ.get("KALSHI_PRIVATE_KEY_PATH", "")
        self.private_key = _load_private_key(pkey_path) if pkey_path else None
        self.base = PROD_BASE if env == "prod" else DEMO_BASE
        self._http = httpx.Client(base_url=self.base, timeout=20)

    def _headers(self, method: str, path: str) -> dict:
        ts = int(time.time() * 1000)
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": str(ts),
        }
        if self.private_key:
            headers["KALSHI-ACCESS-SIGNATURE"] = _sign(
                self.private_key, method, path, ts
            )
        return headers

    def _get(self, path: str, params: dict | None = None) -> Any:
        r = self._http.get(path, params=params, headers=self._headers("GET", path))
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict) -> Any:
        r = self._http.post(
            path, json=body, headers=self._headers("POST", path)
        )
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str) -> Any:
        r = self._http.delete(path, headers=self._headers("DELETE", path))
        r.raise_for_status()
        return r.json()

    # ── Markets ────────────────────────────────────────────────────────────────

    def get_markets(
        self,
        limit: int = 20,
        cursor: str | None = None,
        status: str = "open",
        series_ticker: str | None = None,
        event_ticker: str | None = None,
    ) -> dict:
        params: dict = {"limit": limit, "status": status}
        if cursor:
            params["cursor"] = cursor
        if series_ticker:
            params["series_ticker"] = series_ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        return self._get("/markets", params)

    def get_market(self, ticker: str) -> dict:
        return self._get(f"/markets/{ticker}")

    def get_events(self, limit: int = 20, status: str = "open") -> dict:
        return self._get("/events", {"limit": limit, "status": status})

    def search_events(self, query: str, limit: int = 20) -> dict:
        return self._get("/events", {"limit": limit, "status": "open"})

    # ── Orders ─────────────────────────────────────────────────────────────────

    def create_order(
        self,
        ticker: str,
        side: str,  # "yes" | "no"
        action: str,  # "buy" | "sell"
        count: int,
        type: str = "market",
        yes_price: int | None = None,
        no_price: int | None = None,
    ) -> dict:
        body: dict = {
            "ticker": ticker,
            "action": action,
            "side": side,
            "count": count,
            "type": type,
            "client_order_id": f"kalshiclaw_{int(time.time()*1000)}",
        }
        if yes_price is not None:
            body["yes_price"] = yes_price
        if no_price is not None:
            body["no_price"] = no_price
        return self._post("/portfolio/orders", body)

    def get_orders(self, ticker: str | None = None, status: str = "resting") -> dict:
        params: dict = {"status": status}
        if ticker:
            params["ticker"] = ticker
        return self._get("/portfolio/orders", params)

    def cancel_order(self, order_id: str) -> dict:
        return self._delete(f"/portfolio/orders/{order_id}")

    # ── Portfolio ──────────────────────────────────────────────────────────────

    def get_balance(self) -> dict:
        return self._get("/portfolio/balance")

    def get_positions(
        self,
        limit: int = 100,
        ticker: str | None = None,
        settlement_status: str = "unsettled",
    ) -> dict:
        params: dict = {"limit": limit, "settlement_status": settlement_status}
        if ticker:
            params["ticker"] = ticker
        return self._get("/portfolio/positions", params)

    def get_fills(self, ticker: str | None = None, limit: int = 50) -> dict:
        params: dict = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        return self._get("/portfolio/fills", params)
