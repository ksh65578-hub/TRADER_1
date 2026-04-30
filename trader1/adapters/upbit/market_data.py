from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


UPBIT_PUBLIC_CANDLE_HOST = "api.upbit.com"
UPBIT_PUBLIC_CANDLE_PATH = "/v1/candles/minutes/1"


def _decimal_text(value: Any) -> str:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "0"
    return format(decimal.normalize(), "f") if decimal != decimal.to_integral() else str(decimal.quantize(Decimal("1")))


def build_upbit_public_market_data_fixture(
    *,
    symbol: str = "KRW-BTC",
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "PAPER",
    session_id: str = "mvp2_upbit_paper",
) -> dict[str, Any]:
    return {
        "source": "STATIC_FIXTURE",
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "symbol": symbol,
        "best_bid": "1000000",
        "best_ask": "1000100",
        "last_trade_price": "1000050",
        "volume_24h": "10.0",
        "loaded_at_utc": utc_now(),
        "is_public": True,
        "private_account_fields_present": False,
    }


def validate_upbit_public_market_data(data: dict[str, Any], *, symbol: str, session_id: str) -> tuple[str, str | None, str]:
    if not data:
        return "BLOCKED", "DATA_UNAVAILABLE", "public market data is missing"
    if data.get("exchange") != "UPBIT" or data.get("market_type") != "KRW_SPOT" or data.get("mode") != "PAPER":
        return "BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "public market data scope is not UPBIT/KRW_SPOT/PAPER"
    if data.get("session_id") != session_id or data.get("symbol") != symbol:
        return "BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "public market data session or symbol scope mismatch"
    if data.get("private_account_fields_present"):
        return "BLOCKED", "LIVE_FINAL_GUARD_FAILED", "paper public data path contains private account fields"
    if not data.get("is_public"):
        return "BLOCKED", "API_UNVERIFIED", "paper dry-run requires public data only"
    return "PASS", None, "public Upbit fixture data loaded"


def build_upbit_public_candle_fixture(
    *,
    symbol: str = "KRW-BTC",
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "PAPER",
    session_id: str = "mvp4_upbit_paper_runtime",
    profile: str = "UPTREND_PULLBACK",
) -> dict[str, Any]:
    if profile == "WEAK_RANGE":
        closes = ["1000000", "1000040", "999970", "1000020", "1000005", "999990"]
    elif profile == "DOWNTREND":
        closes = ["1020000", "1012000", "1007000", "1001000", "996000", "990000"]
    else:
        closes = ["980000", "990000", "1002000", "1009000", "1003000", "1000050"]
    candles: list[dict[str, str]] = []
    for index, close in enumerate(closes):
        price = int(close)
        candles.append(
            {
                "timestamp": f"2026-04-30T09:{index:02d}:00Z",
                "open": str(price - 1200),
                "high": str(price + 2500),
                "low": str(price - 2500),
                "close": close,
                "volume": str(2 + index),
            }
        )
    return {
        "source": "STATIC_FIXTURE",
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "symbol": symbol,
        "interval": "1m",
        "profile": profile,
        "candles": candles,
        "loaded_at_utc": utc_now(),
        "is_public": True,
        "private_account_fields_present": False,
    }


def build_upbit_public_candle_data_from_rest_payload(
    *,
    payload: list[dict[str, Any]],
    symbol: str = "KRW-BTC",
    session_id: str = "mvp4_upbit_paper_runtime",
) -> dict[str, Any]:
    candles: list[dict[str, str]] = []
    for item in reversed(payload):
        if item.get("market") != symbol:
            return {
                "source": "PUBLIC_REST_READ_ONLY",
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "session_id": session_id,
                "symbol": symbol,
                "interval": "1m",
                "profile": "PUBLIC_REST_MISMATCHED_SYMBOL",
                "candles": [],
                "loaded_at_utc": utc_now(),
                "is_public": True,
                "private_account_fields_present": False,
                "raw_payload_private_fields_present": False,
                "public_endpoint_host": UPBIT_PUBLIC_CANDLE_HOST,
                "public_endpoint_path": UPBIT_PUBLIC_CANDLE_PATH,
                "credential_load_attempted": False,
                "authorization_header_present": False,
                "private_endpoint_called": False,
                "order_endpoint_called": False,
            }
        candles.append(
            {
                "timestamp": str(item.get("candle_date_time_utc", "")) + "Z",
                "open": _decimal_text(item.get("opening_price")),
                "high": _decimal_text(item.get("high_price")),
                "low": _decimal_text(item.get("low_price")),
                "close": _decimal_text(item.get("trade_price")),
                "volume": _decimal_text(item.get("candle_acc_trade_volume")),
            }
        )
    return {
        "source": "PUBLIC_REST_READ_ONLY",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "symbol": symbol,
        "interval": "1m",
        "profile": "PUBLIC_REST_READ_ONLY_1M_CANDLES",
        "candles": candles,
        "raw_sample_count": len(payload),
        "loaded_at_utc": utc_now(),
        "is_public": True,
        "private_account_fields_present": False,
        "raw_payload_private_fields_present": False,
        "public_endpoint_host": UPBIT_PUBLIC_CANDLE_HOST,
        "public_endpoint_path": UPBIT_PUBLIC_CANDLE_PATH,
        "credential_load_attempted": False,
        "authorization_header_present": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
    }


def fetch_upbit_public_candle_data_read_only(
    *,
    symbol: str = "KRW-BTC",
    session_id: str = "mvp4_upbit_paper_runtime",
    count: int = 6,
    timeout_seconds: float = 3.0,
) -> dict[str, Any]:
    query = urlencode({"market": symbol, "count": max(1, min(count, 200))})
    url = f"https://{UPBIT_PUBLIC_CANDLE_HOST}{UPBIT_PUBLIC_CANDLE_PATH}?{query}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "TRADER_1-public-read-only-paper-collector",
        },
        method="GET",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        payload = []
    return build_upbit_public_candle_data_from_rest_payload(
        payload=payload,
        symbol=symbol,
        session_id=session_id,
    )


def validate_upbit_public_candle_data(data: dict[str, Any], *, symbol: str, session_id: str) -> tuple[str, str | None, str]:
    if not data:
        return "BLOCKED", "DATA_UNAVAILABLE", "public candle data is missing"
    if data.get("exchange") != "UPBIT" or data.get("market_type") != "KRW_SPOT" or data.get("mode") != "PAPER":
        return "BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "public candle data scope is not UPBIT/KRW_SPOT/PAPER"
    if data.get("session_id") != session_id or data.get("symbol") != symbol:
        return "BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "public candle data session or symbol scope mismatch"
    if data.get("private_account_fields_present") or data.get("raw_payload_private_fields_present"):
        return "BLOCKED", "LIVE_FINAL_GUARD_FAILED", "paper public candle path contains private account fields"
    if data.get("credential_load_attempted") or data.get("authorization_header_present"):
        return "BLOCKED", "LIVE_FINAL_GUARD_FAILED", "public candle path attempted credential or authorization header use"
    if data.get("private_endpoint_called") or data.get("order_endpoint_called"):
        return "BLOCKED", "LIVE_FINAL_GUARD_FAILED", "public candle path attempted private or order endpoint"
    if not data.get("is_public"):
        return "BLOCKED", "API_UNVERIFIED", "paper runtime requires public data only"
    if data.get("source") not in {"STATIC_FIXTURE", "PUBLIC_REST_READ_ONLY"}:
        return "BLOCKED", "DATA_UNAVAILABLE", "paper runtime public candle source is unsupported"
    if data.get("source") == "PUBLIC_REST_READ_ONLY":
        if data.get("public_endpoint_host") != UPBIT_PUBLIC_CANDLE_HOST or data.get("public_endpoint_path") != UPBIT_PUBLIC_CANDLE_PATH:
            return "BLOCKED", "API_UNVERIFIED", "public REST candle endpoint is not the approved Upbit public candle endpoint"
    candles = data.get("candles")
    if not isinstance(candles, list) or len(candles) < 5:
        return "BLOCKED", "MEASUREMENT_MISSING", "paper runtime requires at least five candle samples"
    seen_timestamps: set[str] = set()
    previous_timestamp: datetime | None = None
    for candle in candles:
        if not isinstance(candle, dict):
            return "BLOCKED", "MEASUREMENT_MISSING", "candle sample must be an object"
        timestamp = candle.get("timestamp")
        if not isinstance(timestamp, str) or not timestamp:
            return "BLOCKED", "MEASUREMENT_MISSING", "candle timestamp is invalid"
        if timestamp in seen_timestamps:
            return "BLOCKED", "RECONCILIATION_REQUIRED", "duplicate public candle timestamp requires reconcile review"
        seen_timestamps.add(timestamp)
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return "BLOCKED", "MEASUREMENT_MISSING", "candle timestamp cannot be parsed"
        if previous_timestamp is not None and parsed_timestamp <= previous_timestamp:
            return "BLOCKED", "RECONCILIATION_REQUIRED", "public candle timestamps must be strictly increasing"
        previous_timestamp = parsed_timestamp
        for field in ("open", "high", "low", "close", "volume"):
            try:
                if float(candle[field]) <= 0:
                    return "BLOCKED", "MEASUREMENT_MISSING", f"candle {field} must be positive"
            except (KeyError, TypeError, ValueError):
                return "BLOCKED", "MEASUREMENT_MISSING", f"candle {field} is invalid"
    return "PASS", None, "public Upbit candle fixture data loaded"
