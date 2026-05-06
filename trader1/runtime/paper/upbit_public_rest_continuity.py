from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json
from trader1.runtime.paper.upbit_public_rest_sample import (
    build_upbit_public_rest_sample_report,
    upbit_public_rest_sample_hash,
    validate_upbit_public_rest_sample_report,
)


UPBIT_PUBLIC_REST_CONTINUITY_SCHEMA_ID = "trader1.upbit_public_rest_continuity_report.v1"


@dataclass(frozen=True)
class UpbitPublicRestContinuityValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_public_rest_continuity_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("continuity_hash", None)
    return _sha256_json(payload)


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _event_times(sample_report: dict[str, Any]) -> list[str]:
    collection = sample_report.get("public_collection_report")
    if not isinstance(collection, dict):
        return []
    events = collection.get("canonical_events", [])
    if not isinstance(events, list):
        return []
    times = [event.get("event_time_utc") for event in events if isinstance(event, dict)]
    return [value for value in times if isinstance(value, str) and value]


def _latest_event_time(sample_report: dict[str, Any]) -> str | None:
    parsed: list[tuple[datetime, str]] = []
    for value in _event_times(sample_report):
        parsed_value = _parse_utc(value)
        if parsed_value is not None:
            parsed.append((parsed_value, value))
    if not parsed:
        return None
    return max(parsed, key=lambda item: item[0])[1]


def build_upbit_public_rest_continuity_report(
    *,
    continuity_id: str,
    session_id: str = "mvp1_upbit_paper_launcher",
    symbol: str = "KRW-BTC",
    sample_count: int = 2,
    min_required_pass_samples: int = 2,
    interval_seconds: float = 0.0,
    attempt_network: bool = True,
    fetcher: Callable[..., dict[str, Any]] | None = None,
    timeout_seconds: float = 2.5,
) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    sample_reports: list[dict[str, Any]] = []
    sample_hashes: list[str] = []
    latest_times: list[str] = []

    if sample_count < 1 or sample_count > 20:
        blockers.append(_blocker("RUNTIME_BUDGET_EXCEEDED", "public REST continuity sample count exceeds bounded MVP-4 budget"))
        sample_count = max(1, min(sample_count, 20))
    if min_required_pass_samples < 1 or min_required_pass_samples > sample_count:
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "minimum required pass samples must fit within requested sample count"))
        min_required_pass_samples = min(sample_count, max(1, min_required_pass_samples))

    for index in range(sample_count):
        if index and interval_seconds > 0:
            time.sleep(min(interval_seconds, 1.0))
        sample = build_upbit_public_rest_sample_report(
            sample_id=f"{continuity_id}-sample-{index + 1}",
            session_id=session_id,
            symbol=symbol,
            attempt_network=attempt_network,
            fetcher=fetcher,
            timeout_seconds=timeout_seconds,
        )
        sample_reports.append(sample)
        sample_hashes.append(sample["sample_hash"])
        result = validate_upbit_public_rest_sample_report(sample)
        if result.status != "PASS":
            blockers.append(_blocker(result.blocker_code or "DATA_UNAVAILABLE", result.message))
            continue
        latest_time = _latest_event_time(sample)
        if latest_time is None:
            blockers.append(_blocker("MEASUREMENT_MISSING", "PASS sample did not expose a latest event timestamp"))
        else:
            latest_times.append(latest_time)

    pass_count = sum(1 for sample in sample_reports if sample.get("sample_status") == "PASS")
    duplicate_latest = len(set(latest_times)) != len(latest_times)
    non_advancing = False
    parsed_latest = [_parse_utc(value) for value in latest_times]
    if any(value is None for value in parsed_latest):
        non_advancing = True
    else:
        for previous, current in zip(parsed_latest, parsed_latest[1:]):
            if current is None or previous is None or current <= previous:
                non_advancing = True
                break
    if pass_count < min_required_pass_samples:
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "public REST continuity did not collect enough PASS samples"))
    short_window_warnings: list[dict[str, str]] = []
    if duplicate_latest:
        short_window_warnings.append(
            _blocker(
                "DATA_QUALITY_INSUFFICIENT",
                "public REST continuity latest candle timestamp repeated across a short sample window",
                "MEDIUM",
            )
        )
    if non_advancing and len(latest_times) >= min_required_pass_samples:
        short_window_warnings.append(
            _blocker(
                "DATA_QUALITY_INSUFFICIENT",
                "public REST continuity samples did not advance in time across a short sample window",
                "MEDIUM",
            )
        )

    first_time = latest_times[0] if latest_times else None
    last_time = latest_times[-1] if latest_times else None
    first_parsed = _parse_utc(first_time)
    last_parsed = _parse_utc(last_time)
    observed_span_seconds = 0.0
    if first_parsed is not None and last_parsed is not None:
        observed_span_seconds = max(0.0, (last_parsed - first_parsed).total_seconds())

    if blockers:
        status = "BLOCKED"
    elif short_window_warnings:
        status = "WARN"
        blockers.extend(short_window_warnings)
    else:
        status = "PASS"
    report = {
        "schema_id": UPBIT_PUBLIC_REST_CONTINUITY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "continuity_id": continuity_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "symbol": symbol,
        "sample_count_requested": sample_count,
        "sample_count_completed": len(sample_reports),
        "pass_sample_count": pass_count,
        "min_required_pass_samples": min_required_pass_samples,
        "interval_seconds": interval_seconds,
        "sample_reports": sample_reports,
        "sample_hashes": sample_hashes,
        "first_event_time_utc": first_time,
        "latest_event_time_utc": last_time,
        "latest_event_times_utc": latest_times,
        "observed_span_seconds": observed_span_seconds,
        "duplicate_latest_event_time_detected": duplicate_latest,
        "non_advancing_sample_detected": non_advancing,
        "continuity_status": status,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "evidence_role": "PAPER_DATA_CONTINUITY_ONLY_NOT_LIVE_READY",
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
        "continuity_hash": "",
    }
    report["continuity_hash"] = upbit_public_rest_continuity_hash(report)
    return report


def validate_upbit_public_rest_continuity_report(report: dict[str, Any]) -> UpbitPublicRestContinuityValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "continuity_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "sample_count_requested",
        "sample_count_completed",
        "pass_sample_count",
        "min_required_pass_samples",
        "interval_seconds",
        "sample_reports",
        "sample_hashes",
        "first_event_time_utc",
        "latest_event_time_utc",
        "latest_event_times_utc",
        "observed_span_seconds",
        "duplicate_latest_event_time_detected",
        "non_advancing_sample_detected",
        "continuity_status",
        "primary_blocker_code",
        "blockers",
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
        "continuity_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPublicRestContinuityValidationResult("FAIL", f"continuity report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PUBLIC_REST_CONTINUITY_SCHEMA_ID:
        return UpbitPublicRestContinuityValidationResult("FAIL", "continuity schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("continuity_hash") != upbit_public_rest_continuity_hash(report):
        return UpbitPublicRestContinuityValidationResult("FAIL", "continuity hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPublicRestContinuityValidationResult("BLOCKED", "continuity scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("evidence_role") != "PAPER_DATA_CONTINUITY_ONLY_NOT_LIVE_READY":
        return UpbitPublicRestContinuityValidationResult("BLOCKED", "continuity role must not imply LIVE_READY", "LIVE_FINAL_GUARD_FAILED")
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
        return UpbitPublicRestContinuityValidationResult("BLOCKED", "continuity attempted credential, private, order, live, or scale-up behavior", "LIVE_FINAL_GUARD_FAILED")
    sample_reports = report.get("sample_reports")
    sample_hashes = report.get("sample_hashes")
    if not isinstance(sample_reports, list) or not isinstance(sample_hashes, list):
        return UpbitPublicRestContinuityValidationResult("FAIL", "continuity sample collections must be arrays", "SCHEMA_IDENTITY_MISMATCH")
    if len(sample_reports) != report.get("sample_count_completed") or len(sample_hashes) != len(sample_reports):
        return UpbitPublicRestContinuityValidationResult("FAIL", "continuity sample count mismatch", "SCHEMA_IDENTITY_MISMATCH")

    pass_count = 0
    latest_times: list[str] = []
    for sample, expected_hash in zip(sample_reports, sample_hashes):
        if not isinstance(sample, dict):
            return UpbitPublicRestContinuityValidationResult("FAIL", "continuity sample report must be object", "SCHEMA_IDENTITY_MISMATCH")
        if expected_hash != upbit_public_rest_sample_hash(sample):
            return UpbitPublicRestContinuityValidationResult("FAIL", "continuity sample hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
        sample_result = validate_upbit_public_rest_sample_report(sample)
        if sample_result.status == "PASS":
            pass_count += 1
            latest = _latest_event_time(sample)
            if latest is None:
                return UpbitPublicRestContinuityValidationResult("FAIL", "PASS sample missing latest event time", "MEASUREMENT_MISSING")
            latest_times.append(latest)
        elif sample_result.status == "FAIL":
            return UpbitPublicRestContinuityValidationResult("FAIL", "continuity contains invalid sample report", sample_result.blocker_code)
    if pass_count != report.get("pass_sample_count"):
        return UpbitPublicRestContinuityValidationResult("FAIL", "continuity pass count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if latest_times != report.get("latest_event_times_utc"):
        return UpbitPublicRestContinuityValidationResult("FAIL", "continuity latest event time list mismatch", "SCHEMA_IDENTITY_MISMATCH")

    duplicate_latest = len(set(latest_times)) != len(latest_times)
    parsed_latest = [_parse_utc(value) for value in latest_times]
    non_advancing = any(value is None for value in parsed_latest)
    if not non_advancing:
        for previous, current in zip(parsed_latest, parsed_latest[1:]):
            if current is None or previous is None or current <= previous:
                non_advancing = True
                break
    if duplicate_latest != report.get("duplicate_latest_event_time_detected"):
        return UpbitPublicRestContinuityValidationResult("FAIL", "continuity duplicate latest flag mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if non_advancing != report.get("non_advancing_sample_detected"):
        return UpbitPublicRestContinuityValidationResult("FAIL", "continuity non-advancing flag mismatch", "SCHEMA_IDENTITY_MISMATCH")

    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return UpbitPublicRestContinuityValidationResult("FAIL", "continuity blockers must be an array", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("continuity_status") == "PASS":
        if blockers or report.get("primary_blocker_code") is not None:
            return UpbitPublicRestContinuityValidationResult("FAIL", "PASS continuity cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
        if pass_count < report.get("min_required_pass_samples"):
            return UpbitPublicRestContinuityValidationResult("FAIL", "PASS continuity requires enough pass samples", "DATA_QUALITY_INSUFFICIENT")
        if duplicate_latest or non_advancing:
            return UpbitPublicRestContinuityValidationResult("FAIL", "PASS continuity requires advancing sample timestamps", "DATA_QUALITY_INSUFFICIENT")
        return UpbitPublicRestContinuityValidationResult("PASS", "Upbit public REST continuity advanced across PAPER-only samples", None)
    if report.get("continuity_status") == "WARN":
        if not blockers or report.get("primary_blocker_code") != "DATA_QUALITY_INSUFFICIENT":
            return UpbitPublicRestContinuityValidationResult("FAIL", "WARN continuity must expose the short-window non-advancing reason", "SCHEMA_IDENTITY_MISMATCH")
        if pass_count < report.get("min_required_pass_samples"):
            return UpbitPublicRestContinuityValidationResult("BLOCKED", "WARN continuity still requires enough structurally valid PAPER samples", "DATA_QUALITY_INSUFFICIENT")
        if not (duplicate_latest or non_advancing):
            return UpbitPublicRestContinuityValidationResult("FAIL", "WARN continuity requires duplicate or non-advancing short-window evidence", "SCHEMA_IDENTITY_MISMATCH")
        return UpbitPublicRestContinuityValidationResult("WARN", "Upbit public REST continuity is structurally valid but short-window samples did not advance", "DATA_QUALITY_INSUFFICIENT")
    if not blockers:
        return UpbitPublicRestContinuityValidationResult("BLOCKED", "blocked continuity must expose blocker", report.get("primary_blocker_code") or "DATA_QUALITY_INSUFFICIENT")
    if report.get("primary_blocker_code") is None:
        return UpbitPublicRestContinuityValidationResult("BLOCKED", "blocked continuity must carry primary blocker", "DATA_QUALITY_INSUFFICIENT")
    return UpbitPublicRestContinuityValidationResult("BLOCKED", "Upbit public REST continuity is blocked", report.get("primary_blocker_code"))


def write_upbit_public_rest_continuity_report(*, root: Path, report: dict[str, Any]) -> Path:
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
        / "rest_continuity_report.json"
    )
    durable_atomic_write_json(path, report)
    return path
