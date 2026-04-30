from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from trader1.adapters.upbit.market_data import fetch_upbit_public_candle_data_read_only
from trader1.runtime.paper.upbit_public_collector import (
    build_upbit_public_market_data_collection_report,
    durable_atomic_write_json,
    validate_upbit_public_market_data_collection_report,
)


UPBIT_PUBLIC_REST_SAMPLE_SCHEMA_ID = "trader1.upbit_public_rest_sample_report.v1"


@dataclass(frozen=True)
class UpbitPublicRestSampleValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_public_rest_sample_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("sample_hash", None)
    return _sha256_json(payload)


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def build_upbit_public_rest_sample_report(
    *,
    sample_id: str,
    session_id: str = "mvp1_upbit_paper_launcher",
    symbol: str = "KRW-BTC",
    attempt_network: bool = True,
    fetcher: Callable[..., dict[str, Any]] | None = None,
    timeout_seconds: float = 2.5,
) -> dict[str, Any]:
    started = time.monotonic()
    generated_at = utc_now()
    fetcher = fetcher or fetch_upbit_public_candle_data_read_only
    public_market_data: dict[str, Any] | None = None
    collection_report: dict[str, Any] | None = None
    blockers: list[dict[str, str]] = []
    collection_status = "NOT_RUN"
    sample_status = "BLOCKED"
    primary_blocker_code: str | None = None
    fetch_error: str | None = None

    if not attempt_network:
        primary_blocker_code = "DATA_UNAVAILABLE"
        blockers.append(_blocker(primary_blocker_code, "public REST network sample was not attempted"))
    else:
        try:
            public_market_data = fetcher(symbol=symbol, session_id=session_id, timeout_seconds=timeout_seconds)
            collection_report = build_upbit_public_market_data_collection_report(
                collector_id=f"{sample_id}-collection",
                session_id=session_id,
                symbol=symbol,
                market_data=public_market_data,
            )
            collection_result = validate_upbit_public_market_data_collection_report(collection_report)
            collection_status = collection_result.status
            sample_status = "PASS" if collection_result.status == "PASS" else "BLOCKED"
            primary_blocker_code = collection_result.blocker_code
            if collection_result.status != "PASS":
                blockers.append(_blocker(collection_result.blocker_code or "DATA_UNAVAILABLE", collection_result.message))
        except Exception as exc:
            fetch_error = f"{type(exc).__name__}: {exc}"
            primary_blocker_code = "DATA_UNAVAILABLE"
            blockers.append(_blocker(primary_blocker_code, "public REST network sample failed safely"))

    report = {
        "schema_id": UPBIT_PUBLIC_REST_SAMPLE_SCHEMA_ID,
        "generated_at_utc": generated_at,
        "project_id": "TRADER_1",
        "sample_id": sample_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "symbol": symbol,
        "endpoint_host": "api.upbit.com",
        "endpoint_path": "/v1/candles/minutes/1",
        "network_call_attempted": attempt_network,
        "sample_status": sample_status,
        "collection_status": collection_status,
        "public_market_data": public_market_data,
        "public_collection_report": collection_report,
        "canonical_event_count": 0 if not collection_report else int(collection_report.get("canonical_event_count", 0)),
        "primary_blocker_code": primary_blocker_code,
        "blockers": blockers,
        "latency_ms": round((time.monotonic() - started) * 1000, 3),
        "fetch_error": fetch_error,
        "evidence_role": "PAPER_INPUT_QUALITY_SAMPLE_ONLY_NOT_LIVE_READY",
        "credential_load_attempted": False,
        "authorization_header_present": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "sample_hash": "",
    }
    report["sample_hash"] = upbit_public_rest_sample_hash(report)
    return report


def validate_upbit_public_rest_sample_report(report: dict[str, Any]) -> UpbitPublicRestSampleValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "sample_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "endpoint_host",
        "endpoint_path",
        "network_call_attempted",
        "sample_status",
        "collection_status",
        "public_market_data",
        "public_collection_report",
        "canonical_event_count",
        "primary_blocker_code",
        "blockers",
        "latency_ms",
        "fetch_error",
        "evidence_role",
        "credential_load_attempted",
        "authorization_header_present",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "sample_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPublicRestSampleValidationResult("FAIL", f"sample report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PUBLIC_REST_SAMPLE_SCHEMA_ID:
        return UpbitPublicRestSampleValidationResult("FAIL", "sample schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("sample_hash") != upbit_public_rest_sample_hash(report):
        return UpbitPublicRestSampleValidationResult("FAIL", "sample hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPublicRestSampleValidationResult("BLOCKED", "sample scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("endpoint_host") != "api.upbit.com" or report.get("endpoint_path") != "/v1/candles/minutes/1":
        return UpbitPublicRestSampleValidationResult("BLOCKED", "sample endpoint is not the approved public Upbit candle endpoint", "API_UNVERIFIED")
    if report.get("evidence_role") != "PAPER_INPUT_QUALITY_SAMPLE_ONLY_NOT_LIVE_READY":
        return UpbitPublicRestSampleValidationResult("BLOCKED", "public REST sample role must not imply LIVE_READY", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "credential_load_attempted",
        "authorization_header_present",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden):
        return UpbitPublicRestSampleValidationResult("BLOCKED", "sample attempted credential, private, order, live, or scale-up behavior", "LIVE_FINAL_GUARD_FAILED")
    if report.get("sample_status") not in {"PASS", "BLOCKED", "FAIL"}:
        return UpbitPublicRestSampleValidationResult("FAIL", "sample status is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("collection_status") not in {"PASS", "BLOCKED", "FAIL", "NOT_RUN"}:
        return UpbitPublicRestSampleValidationResult("FAIL", "collection status is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("sample_status") == "PASS":
        collection_report = report.get("public_collection_report")
        if not isinstance(collection_report, dict):
            return UpbitPublicRestSampleValidationResult("FAIL", "PASS sample requires public collection report", "MEASUREMENT_MISSING")
        collection_result = validate_upbit_public_market_data_collection_report(collection_report)
        if collection_result.status != "PASS":
            return UpbitPublicRestSampleValidationResult("FAIL", "PASS sample collection report did not validate", collection_result.blocker_code)
        if report.get("canonical_event_count", 0) < 5:
            return UpbitPublicRestSampleValidationResult("FAIL", "PASS sample requires at least five canonical events", "MEASUREMENT_MISSING")
        if report.get("primary_blocker_code") is not None or report.get("blockers"):
            return UpbitPublicRestSampleValidationResult("FAIL", "PASS sample must not carry blockers", "SCHEMA_IDENTITY_MISMATCH")
    else:
        if not report.get("blockers"):
            return UpbitPublicRestSampleValidationResult("BLOCKED", "blocked sample must expose operator-readable blocker", report.get("primary_blocker_code") or "DATA_UNAVAILABLE")
        if report.get("primary_blocker_code") is None:
            return UpbitPublicRestSampleValidationResult("BLOCKED", "blocked sample must carry primary blocker", "DATA_UNAVAILABLE")
    return UpbitPublicRestSampleValidationResult(report["sample_status"], "Upbit public REST sample is PAPER-only and live-blocked", report.get("primary_blocker_code"))


def write_upbit_public_rest_sample_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = (
        Path(root).resolve()
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(report["session_id"])
        / "market_data"
        / "public"
        / "rest_sample_report.json"
    )
    durable_atomic_write_json(path, report)
    return path
