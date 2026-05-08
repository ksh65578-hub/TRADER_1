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
UPBIT_PUBLIC_MARKET_ALL_PATH = "/v1/market/all"
UPBIT_PUBLIC_TICKER_PATH = "/v1/ticker"
UPBIT_PUBLIC_SYMBOL_DISCOVERY_SCHEMA_ID = "trader1.upbit_public_krw_symbol_discovery_report.v1"
UPBIT_PUBLIC_TICKER_SNAPSHOT_SCHEMA_ID = "trader1.upbit_public_ticker_snapshot_report.v1"
UPBIT_PUBLIC_SYMBOL_RANKING_SCHEMA_ID = "trader1.upbit_public_krw_symbol_ranking_report.v1"
DEFAULT_DISCOVERY_EVALUATION_LIMIT = 30
DEFAULT_MINIMUM_DISCOVERY_QUOTE_VOLUME_KRW = Decimal("50000000")


def _decimal_text(value: Any) -> str:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "0"
    return format(decimal.normalize(), "f") if decimal != decimal.to_integral() else str(decimal.quantize(Decimal("1")))


def _decimal_or_zero(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _public_read_only_safety_fields() -> dict[str, bool]:
    return {
        "is_public": True,
        "private_account_fields_present": False,
        "raw_payload_private_fields_present": False,
        "credential_load_attempted": False,
        "authorization_header_present": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_krw_market_symbols_from_rest_payload(payload: list[dict[str, Any]]) -> list[str]:
    symbols: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        market = str(item.get("market", "")).strip().upper()
        if not market.startswith("KRW-"):
            continue
        quote, _, base = market.partition("-")
        if quote != "KRW" or not base or not base.replace("-", "").isalnum():
            continue
        symbols.add(market)
    return sorted(symbols)


def build_upbit_public_krw_symbol_discovery_report_from_payload(
    *,
    payload: list[dict[str, Any]],
    session_id: str = "mvp1_upbit_paper_launcher",
) -> dict[str, Any]:
    symbols = build_upbit_krw_market_symbols_from_rest_payload(payload)
    status = "PASS" if symbols else "BLOCKED"
    primary_blocker_code = None if symbols else "DATA_UNAVAILABLE"
    return {
        "schema_id": UPBIT_PUBLIC_SYMBOL_DISCOVERY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "source": "PUBLIC_REST_READ_ONLY",
        "public_endpoint_host": UPBIT_PUBLIC_CANDLE_HOST,
        "public_endpoint_path": UPBIT_PUBLIC_MARKET_ALL_PATH,
        "query_is_details": "false",
        "discovery_status": status,
        "primary_blocker_code": primary_blocker_code,
        "market_count": len(symbols),
        "symbols": symbols,
        "selection_scope": "ALL_UPBIT_KRW_MARKETS",
        "blockers": [] if status == "PASS" else [{"code": primary_blocker_code, "severity": "HIGH", "message": "Upbit KRW market list returned no usable symbols"}],
        **_public_read_only_safety_fields(),
    }


def fetch_upbit_krw_market_symbols_read_only(
    *,
    session_id: str = "mvp1_upbit_paper_launcher",
    timeout_seconds: float = 3.0,
) -> dict[str, Any]:
    query = urlencode({"isDetails": "false"})
    url = f"https://{UPBIT_PUBLIC_CANDLE_HOST}{UPBIT_PUBLIC_MARKET_ALL_PATH}?{query}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "TRADER_1-public-read-only-paper-symbol-discovery",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {
            "schema_id": UPBIT_PUBLIC_SYMBOL_DISCOVERY_SCHEMA_ID,
            "generated_at_utc": utc_now(),
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": session_id,
            "source": "PUBLIC_REST_READ_ONLY",
            "public_endpoint_host": UPBIT_PUBLIC_CANDLE_HOST,
            "public_endpoint_path": UPBIT_PUBLIC_MARKET_ALL_PATH,
            "query_is_details": "false",
            "discovery_status": "BLOCKED",
            "primary_blocker_code": "DATA_UNAVAILABLE",
            "market_count": 0,
            "symbols": [],
            "selection_scope": "ALL_UPBIT_KRW_MARKETS",
            "blockers": [{"code": "DATA_UNAVAILABLE", "severity": "HIGH", "message": f"Upbit KRW market discovery failed: {exc}"}],
            **_public_read_only_safety_fields(),
        }
    if not isinstance(payload, list):
        payload = []
    return build_upbit_public_krw_symbol_discovery_report_from_payload(payload=payload, session_id=session_id)


def build_upbit_public_ticker_snapshot_from_rest_payload(
    *,
    payload: list[dict[str, Any]],
    requested_symbols: list[str],
    session_id: str = "mvp1_upbit_paper_launcher",
) -> dict[str, Any]:
    requested_set = {str(symbol).upper() for symbol in requested_symbols}
    ticker_by_symbol: dict[str, dict[str, str]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("market", "")).strip().upper()
        if symbol not in requested_set:
            continue
        ticker_by_symbol[symbol] = {
            "symbol": symbol,
            "trade_price": _decimal_text(item.get("trade_price")),
            "acc_trade_price_24h": _decimal_text(item.get("acc_trade_price_24h")),
            "signed_change_rate": _decimal_text(item.get("signed_change_rate")),
            "acc_trade_volume_24h": _decimal_text(item.get("acc_trade_volume_24h")),
        }
    status = "PASS" if ticker_by_symbol else "BLOCKED"
    primary_blocker_code = None if ticker_by_symbol else "DATA_UNAVAILABLE"
    return {
        "schema_id": UPBIT_PUBLIC_TICKER_SNAPSHOT_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "source": "PUBLIC_REST_READ_ONLY",
        "public_endpoint_host": UPBIT_PUBLIC_CANDLE_HOST,
        "public_endpoint_path": UPBIT_PUBLIC_TICKER_PATH,
        "requested_symbol_count": len(requested_symbols),
        "ticker_count": len(ticker_by_symbol),
        "ticker_status": status,
        "primary_blocker_code": primary_blocker_code,
        "ticker_by_symbol": ticker_by_symbol,
        "blockers": [] if status == "PASS" else [{"code": primary_blocker_code, "severity": "HIGH", "message": "Upbit public ticker returned no usable KRW ticker samples"}],
        **_public_read_only_safety_fields(),
    }


def fetch_upbit_public_ticker_snapshot_read_only(
    *,
    symbols: list[str],
    session_id: str = "mvp1_upbit_paper_launcher",
    timeout_seconds: float = 3.0,
    chunk_size: int = 100,
) -> dict[str, Any]:
    unique_symbols = sorted({str(symbol).strip().upper() for symbol in symbols if str(symbol).strip().upper().startswith("KRW-")})
    if not unique_symbols:
        return build_upbit_public_ticker_snapshot_from_rest_payload(payload=[], requested_symbols=[], session_id=session_id)
    payload: list[dict[str, Any]] = []
    safe_chunk_size = max(1, min(int(chunk_size), 100))
    try:
        for index in range(0, len(unique_symbols), safe_chunk_size):
            chunk = unique_symbols[index : index + safe_chunk_size]
            query = urlencode({"markets": ",".join(chunk)})
            url = f"https://{UPBIT_PUBLIC_CANDLE_HOST}{UPBIT_PUBLIC_TICKER_PATH}?{query}"
            request = Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "TRADER_1-public-read-only-paper-ticker-snapshot",
                },
                method="GET",
            )
            with urlopen(request, timeout=timeout_seconds) as response:
                chunk_payload = json.loads(response.read().decode("utf-8"))
            if isinstance(chunk_payload, list):
                payload.extend(item for item in chunk_payload if isinstance(item, dict))
    except Exception as exc:
        report = build_upbit_public_ticker_snapshot_from_rest_payload(
            payload=[],
            requested_symbols=unique_symbols,
            session_id=session_id,
        )
        report["blockers"] = [{"code": "DATA_UNAVAILABLE", "severity": "HIGH", "message": f"Upbit public ticker snapshot failed: {exc}"}]
        return report
    return build_upbit_public_ticker_snapshot_from_rest_payload(
        payload=payload,
        requested_symbols=unique_symbols,
        session_id=session_id,
    )


def rank_upbit_krw_symbols_by_public_ticker(
    *,
    symbols: list[str],
    ticker_by_symbol: dict[str, dict[str, Any]],
    session_id: str = "mvp1_upbit_paper_launcher",
    limit: int = DEFAULT_DISCOVERY_EVALUATION_LIMIT,
    minimum_quote_volume_krw: Decimal = DEFAULT_MINIMUM_DISCOVERY_QUOTE_VOLUME_KRW,
) -> dict[str, Any]:
    safe_limit = max(1, min(int(limit), 80))
    rankings: list[dict[str, Any]] = []
    for input_order, symbol in enumerate(sorted({str(item).strip().upper() for item in symbols if str(item).strip().upper().startswith("KRW-")}), start=1):
        ticker = ticker_by_symbol.get(symbol, {})
        trade_price = _decimal_or_zero(ticker.get("trade_price"))
        quote_volume_24h = _decimal_or_zero(ticker.get("acc_trade_price_24h"))
        signed_change_rate = _decimal_or_zero(ticker.get("signed_change_rate"))
        liquidity_score = min(Decimal("1"), max(Decimal("0"), quote_volume_24h / Decimal("5000000000")))
        positive_change_rate = max(Decimal("0"), signed_change_rate)
        negative_change_rate = max(Decimal("0"), -signed_change_rate)
        positive_momentum_score = min(Decimal("1"), positive_change_rate / Decimal("0.08"))
        downside_penalty_score = min(Decimal("1"), negative_change_rate / Decimal("0.08"))
        price_valid = trade_price > Decimal("0")
        quote_volume_valid = quote_volume_24h >= minimum_quote_volume_krw
        source_complete = bool(ticker)
        raw_score = (
            Decimal("0.60") * liquidity_score
            + Decimal("0.30") * positive_momentum_score
            + Decimal("0.10") * (Decimal("1") if price_valid else Decimal("0"))
            - Decimal("0.45") * downside_penalty_score
        )
        score = max(Decimal("0"), raw_score)
        rankings.append(
            {
                "rank_input_order": input_order,
                "symbol": symbol,
                "source_complete": source_complete,
                "trade_price": _decimal_text(trade_price),
                "quote_volume_24h_krw": _decimal_text(quote_volume_24h),
                "signed_change_rate": _decimal_text(signed_change_rate),
                "abs_change_rate": _decimal_text(abs(signed_change_rate)),
                "positive_change_rate": _decimal_text(positive_change_rate),
                "negative_change_rate": _decimal_text(negative_change_rate),
                "liquidity_score": _decimal_text(liquidity_score.quantize(Decimal("0.0001"))),
                "momentum_score": _decimal_text(positive_momentum_score.quantize(Decimal("0.0001"))),
                "positive_momentum_score": _decimal_text(positive_momentum_score.quantize(Decimal("0.0001"))),
                "downside_penalty_score": _decimal_text(downside_penalty_score.quantize(Decimal("0.0001"))),
                "rank_score": _decimal_text(score.quantize(Decimal("0.0001"))),
                "rank_formula": (
                    "max(0,0.60*liquidity_score+0.30*positive_momentum_score+"
                    "0.10*valid_price_score-0.45*downside_penalty_score)"
                ),
                "minimum_quote_volume_24h_krw": _decimal_text(minimum_quote_volume_krw),
                "eligible_for_candle_evaluation": source_complete and price_valid and quote_volume_valid,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
    ranked = sorted(
        rankings,
        key=lambda item: (
            not bool(item["eligible_for_candle_evaluation"]),
            -_decimal_or_zero(item["rank_score"]),
            -_decimal_or_zero(item["quote_volume_24h_krw"]),
            item["symbol"],
        ),
    )
    eligible_symbols = [item["symbol"] for item in ranked if item["eligible_for_candle_evaluation"]]
    selected_symbols = (eligible_symbols or [item["symbol"] for item in ranked])[:safe_limit]
    status = "PASS" if selected_symbols else "BLOCKED"
    primary_blocker_code = None if selected_symbols else "DATA_UNAVAILABLE"
    return {
        "schema_id": UPBIT_PUBLIC_SYMBOL_RANKING_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "ranking_status": status,
        "primary_blocker_code": primary_blocker_code,
        "selection_scope": "ALL_UPBIT_KRW_MARKETS_RANKED_BY_PUBLIC_TICKER",
        "input_symbol_count": len({str(item).strip().upper() for item in symbols if str(item).strip().upper().startswith("KRW-")}),
        "ranked_symbol_count": len(ranked),
        "eligible_symbol_count": len(eligible_symbols),
        "evaluation_limit": safe_limit,
        "selected_symbols_for_candle_evaluation": selected_symbols,
        "ranking_formula": (
            "max(0,0.60*liquidity_score+0.30*positive_momentum_score+"
            "0.10*valid_price_score-0.45*downside_penalty_score)"
        ),
        "minimum_quote_volume_24h_krw": _decimal_text(minimum_quote_volume_krw),
        "symbol_rankings": ranked,
        "blockers": [] if status == "PASS" else [{"code": primary_blocker_code, "severity": "HIGH", "message": "No Upbit KRW symbols were available for candle evaluation"}],
        **_public_read_only_safety_fields(),
    }


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
    volumes: list[str] | None = None
    if profile == "WEAK_RANGE":
        closes = ["1000000", "1000040", "999970", "1000020", "1000005", "999990"]
    elif profile == "QUIET_RANGE":
        closes = ["1000000", "1000010", "999990", "1000005", "999995", "1000000"]
        volumes = ["5", "4.8", "5.1", "4.9", "5", "4"]
    elif profile == "PANIC":
        closes = ["1050000", "1030000", "990000", "940000", "900000", "860000"]
        volumes = ["5", "7", "11", "17", "24", "35"]
    elif profile == "VOLATILITY_EXPANSION":
        closes = ["1000000", "1008000", "1016000", "1024000", "1018000", "1046000"]
        volumes = ["5", "6", "7", "8", "9", "18"]
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
                "volume": volumes[index] if volumes is not None else str(2 + index),
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
    to_utc: str | None = None,
) -> dict[str, Any]:
    query_params = {"market": symbol, "count": max(1, min(count, 200))}
    if to_utc:
        query_params["to"] = to_utc.replace("T", " ").replace("Z", "")
    query = urlencode(query_params)
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


def fetch_upbit_public_candle_history_read_only(
    *,
    symbol: str = "KRW-BTC",
    session_id: str = "mvp4_upbit_paper_runtime",
    target_count: int = 400,
    page_size: int = 200,
    timeout_seconds: float = 3.0,
) -> dict[str, Any]:
    safe_target_count = max(5, min(int(target_count), 1000))
    safe_page_size = max(5, min(int(page_size), 200))
    payload: list[dict[str, Any]] = []
    seen_timestamps: set[str] = set()
    to_utc: str | None = None
    while len(payload) < safe_target_count:
        query_params = {
            "market": symbol,
            "count": min(safe_page_size, safe_target_count - len(payload)),
        }
        if to_utc:
            query_params["to"] = to_utc.replace("T", " ").replace("Z", "")
        query = urlencode(query_params)
        url = f"https://{UPBIT_PUBLIC_CANDLE_HOST}{UPBIT_PUBLIC_CANDLE_PATH}?{query}"
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "TRADER_1-public-read-only-paper-history-collector",
            },
            method="GET",
        )
        with urlopen(request, timeout=timeout_seconds) as response:
            page_payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(page_payload, list) or not page_payload:
            break
        added = 0
        oldest_timestamp: str | None = None
        for item in page_payload:
            if not isinstance(item, dict):
                continue
            timestamp = str(item.get("candle_date_time_utc") or "")
            if not timestamp or timestamp in seen_timestamps:
                continue
            payload.append(item)
            seen_timestamps.add(timestamp)
            oldest_timestamp = timestamp if oldest_timestamp is None or timestamp < oldest_timestamp else oldest_timestamp
            added += 1
            if len(payload) >= safe_target_count:
                break
        if added == 0 or oldest_timestamp is None:
            break
        to_utc = oldest_timestamp
    return build_upbit_public_candle_data_from_rest_payload(
        payload=payload[:safe_target_count],
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
