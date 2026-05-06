from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json
from trader1.runtime.paper.upbit_public_rest_continuity import (
    _blocker,
    _sha256_json,
    utc_now,
    upbit_public_rest_continuity_hash,
    validate_upbit_public_rest_continuity_report,
)


UPBIT_PUBLIC_REST_CONTINUITY_HISTORY_SCHEMA_ID = "trader1.upbit_public_rest_continuity_history.v1"


@dataclass(frozen=True)
class UpbitPublicRestContinuityHistoryValidationResult:
    status: str
    message: str
    blocker_code: str | None


def upbit_public_rest_continuity_history_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("history_hash", None)
    return _sha256_json(payload)


def _history_path(root: Path, session_id: str) -> Path:
    return (
        Path(root).resolve()
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / session_id
        / "market_data"
        / "public"
        / "rest_continuity_history.json"
    )


def _quarantine_history(path: Path, reason: str) -> Path | None:
    if not path.exists():
        return None
    suffix = utc_now().replace("-", "").replace(":", "")
    quarantine_path = path.with_name(f"{path.stem}.quarantine.{suffix}.{reason}{path.suffix}")
    path.rename(quarantine_path)
    return quarantine_path


def _count_with_flag(attempts: list[dict[str, Any]], flag_name: str) -> int:
    return sum(1 for attempt in attempts if bool(attempt.get(flag_name)))


def _count_with_blocker(attempts: list[dict[str, Any]], blocker_code: str) -> int:
    return sum(1 for attempt in attempts if attempt.get("primary_blocker_code") == blocker_code)


def build_upbit_public_rest_continuity_history_report(
    *,
    history_id: str,
    session_id: str = "mvp1_upbit_paper_launcher",
    symbol: str = "KRW-BTC",
    continuity_attempts: list[dict[str, Any]] | None = None,
    history_window_label: str = "SHORT_PUBLIC_REST_CONTINUITY_HISTORY",
    min_required_pass_attempts: int = 2,
    max_attempts: int = 50,
) -> dict[str, Any]:
    attempts = list(continuity_attempts or [])[-max(1, min(max_attempts, 200)) :]
    blockers: list[dict[str, str]] = []
    attempt_hashes = [str(attempt.get("continuity_hash", "")) for attempt in attempts]
    total_count = len(attempts)
    pass_count = sum(1 for attempt in attempts if attempt.get("continuity_status") == "PASS")
    blocked_count = sum(1 for attempt in attempts if attempt.get("continuity_status") == "BLOCKED")
    duplicate_count = _count_with_flag(attempts, "duplicate_latest_event_time_detected")
    non_advancing_count = _count_with_flag(attempts, "non_advancing_sample_detected")
    data_unavailable_count = _count_with_blocker(attempts, "DATA_UNAVAILABLE")
    latest_attempt = attempts[-1] if attempts else None
    latest_status = latest_attempt.get("continuity_status") if isinstance(latest_attempt, dict) else "BLOCKED"
    latest_blocker = latest_attempt.get("primary_blocker_code") if isinstance(latest_attempt, dict) else "DATA_UNAVAILABLE"

    if not attempts:
        blockers.append(_blocker("DATA_UNAVAILABLE", "public REST continuity history has no attempts yet"))
    elif latest_status == "WARN":
        blockers.append(_blocker(str(latest_blocker or "DATA_QUALITY_INSUFFICIENT"), "latest public REST continuity attempt is structurally valid but short-window non-advancing"))
    elif latest_status != "PASS":
        blockers.append(_blocker(str(latest_blocker or "DATA_QUALITY_INSUFFICIENT"), "latest public REST continuity attempt is not PASS"))
    elif pass_count < min_required_pass_attempts:
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "public REST continuity history has insufficient PASS attempts"))

    status = "PASS" if not blockers else "WARN" if latest_status == "WARN" and pass_count >= 1 else "BLOCKED"
    report = {
        "schema_id": UPBIT_PUBLIC_REST_CONTINUITY_HISTORY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "history_id": history_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "symbol": symbol,
        "history_window_label": history_window_label,
        "continuity_attempts": attempts,
        "attempt_hashes": attempt_hashes,
        "total_attempt_count": total_count,
        "pass_attempt_count": pass_count,
        "blocked_attempt_count": blocked_count,
        "duplicate_latest_event_block_count": duplicate_count,
        "non_advancing_block_count": non_advancing_count,
        "data_unavailable_block_count": data_unavailable_count,
        "min_required_pass_attempts": min_required_pass_attempts,
        "latest_attempt_status": latest_status,
        "latest_primary_blocker_code": latest_blocker,
        "continuity_health_status": status,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "evidence_role": "PAPER_DATA_CONTINUITY_HISTORY_ONLY_NOT_LIVE_READY",
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
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
        "history_hash": "",
    }
    report["history_hash"] = upbit_public_rest_continuity_history_hash(report)
    return report


def validate_upbit_public_rest_continuity_history_report(report: dict[str, Any]) -> UpbitPublicRestContinuityHistoryValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "history_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "history_window_label",
        "continuity_attempts",
        "attempt_hashes",
        "total_attempt_count",
        "pass_attempt_count",
        "blocked_attempt_count",
        "duplicate_latest_event_block_count",
        "non_advancing_block_count",
        "data_unavailable_block_count",
        "min_required_pass_attempts",
        "latest_attempt_status",
        "latest_primary_blocker_code",
        "continuity_health_status",
        "primary_blocker_code",
        "blockers",
        "evidence_role",
        "long_run_evidence_eligible",
        "promotion_eligible",
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
        "history_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", f"continuity history missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PUBLIC_REST_CONTINUITY_HISTORY_SCHEMA_ID:
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("history_hash") != upbit_public_rest_continuity_history_hash(report):
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPublicRestContinuityHistoryValidationResult("BLOCKED", "continuity history scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("evidence_role") != "PAPER_DATA_CONTINUITY_HISTORY_ONLY_NOT_LIVE_READY":
        return UpbitPublicRestContinuityHistoryValidationResult("BLOCKED", "continuity history role must not imply LIVE_READY", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "long_run_evidence_eligible",
        "promotion_eligible",
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
        return UpbitPublicRestContinuityHistoryValidationResult("BLOCKED", "continuity history attempted promotion, credential, private, order, live, or scale-up behavior", "LIVE_FINAL_GUARD_FAILED")

    attempts = report.get("continuity_attempts")
    attempt_hashes = report.get("attempt_hashes")
    if not isinstance(attempts, list) or not isinstance(attempt_hashes, list):
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history attempts and hashes must be arrays", "SCHEMA_IDENTITY_MISMATCH")
    if len(attempts) != len(attempt_hashes) or len(attempts) != report.get("total_attempt_count"):
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history attempt count mismatch", "SCHEMA_IDENTITY_MISMATCH")

    pass_count = 0
    blocked_count = 0
    for attempt, expected_hash in zip(attempts, attempt_hashes):
        if not isinstance(attempt, dict):
            return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history attempt must be object", "SCHEMA_IDENTITY_MISMATCH")
        if expected_hash != upbit_public_rest_continuity_hash(attempt):
            return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history attempt hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if attempt.get("session_id") != report.get("session_id") or attempt.get("symbol") != report.get("symbol"):
            return UpbitPublicRestContinuityHistoryValidationResult("BLOCKED", "continuity history mixes session or symbol scope", "SNAPSHOT_SCOPE_MISMATCH")
        result = validate_upbit_public_rest_continuity_report(attempt)
        if result.status == "FAIL":
            return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history contains invalid attempt", result.blocker_code)
        if result.status == "PASS":
            pass_count += 1
        elif result.status == "BLOCKED":
            blocked_count += 1
        elif result.status == "WARN":
            pass
    if pass_count != report.get("pass_attempt_count") or blocked_count != report.get("blocked_attempt_count"):
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history status counts mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if _count_with_flag(attempts, "duplicate_latest_event_time_detected") != report.get("duplicate_latest_event_block_count"):
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history duplicate block count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if _count_with_flag(attempts, "non_advancing_sample_detected") != report.get("non_advancing_block_count"):
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history non-advancing block count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if _count_with_blocker(attempts, "DATA_UNAVAILABLE") != report.get("data_unavailable_block_count"):
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history data-unavailable block count mismatch", "SCHEMA_IDENTITY_MISMATCH")

    latest_attempt = attempts[-1] if attempts else None
    expected_latest_status = latest_attempt.get("continuity_status") if isinstance(latest_attempt, dict) else "BLOCKED"
    expected_latest_blocker = latest_attempt.get("primary_blocker_code") if isinstance(latest_attempt, dict) else "DATA_UNAVAILABLE"
    if report.get("latest_attempt_status") != expected_latest_status or report.get("latest_primary_blocker_code") != expected_latest_blocker:
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history latest attempt summary mismatch", "SCHEMA_IDENTITY_MISMATCH")

    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "continuity history blockers must be an array", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("continuity_health_status") == "PASS":
        if blockers or report.get("primary_blocker_code") is not None:
            return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "PASS continuity history cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
        if pass_count < report.get("min_required_pass_attempts"):
            return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "PASS continuity history requires enough PASS attempts", "DATA_QUALITY_INSUFFICIENT")
        if expected_latest_status != "PASS":
            return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "PASS continuity history requires latest PASS attempt", "DATA_QUALITY_INSUFFICIENT")
        return UpbitPublicRestContinuityHistoryValidationResult("PASS", "Upbit public REST continuity history is PAPER-only and currently healthy", None)
    if report.get("continuity_health_status") == "WARN":
        if not blockers or report.get("primary_blocker_code") is None:
            return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "WARN continuity history must expose blocker", "SCHEMA_IDENTITY_MISMATCH")
        if expected_latest_status != "WARN":
            return UpbitPublicRestContinuityHistoryValidationResult("FAIL", "WARN continuity history requires latest WARN attempt", "DATA_QUALITY_INSUFFICIENT")
        if pass_count < 1:
            return UpbitPublicRestContinuityHistoryValidationResult("BLOCKED", "WARN continuity history requires at least one PASS attempt in the short window", "DATA_QUALITY_INSUFFICIENT")
        return UpbitPublicRestContinuityHistoryValidationResult("WARN", "Upbit public REST continuity history is structurally valid but waiting for advancing samples", report.get("primary_blocker_code"))
    if not blockers or report.get("primary_blocker_code") is None:
        return UpbitPublicRestContinuityHistoryValidationResult("BLOCKED", "blocked continuity history must expose blocker", "DATA_QUALITY_INSUFFICIENT")
    return UpbitPublicRestContinuityHistoryValidationResult("BLOCKED", "Upbit public REST continuity history is blocked", report.get("primary_blocker_code"))


def write_upbit_public_rest_continuity_history_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _history_path(Path(root), str(report["session_id"]))
    durable_atomic_write_json(path, report)
    return path


def append_upbit_public_rest_continuity_history(
    *,
    root: Path,
    continuity_report: dict[str, Any],
    history_id: str = "upbit-public-rest-continuity-history",
    max_attempts: int = 50,
) -> tuple[Path, dict[str, Any]]:
    session_id = str(continuity_report["session_id"])
    history_path = _history_path(Path(root), session_id)
    previous_attempts: list[dict[str, Any]] = []
    if history_path.exists():
        try:
            previous = json.loads(history_path.read_text(encoding="utf-8"))
            if isinstance(previous, dict):
                previous_result = validate_upbit_public_rest_continuity_history_report(previous)
                if previous_result.status in {"PASS", "WARN", "BLOCKED"} and isinstance(previous.get("continuity_attempts"), list):
                    previous_attempts = [attempt for attempt in previous["continuity_attempts"] if isinstance(attempt, dict)]
                else:
                    _quarantine_history(history_path, "invalid")
            else:
                _quarantine_history(history_path, "invalid")
        except json.JSONDecodeError:
            _quarantine_history(history_path, "corrupt-json")
    history = build_upbit_public_rest_continuity_history_report(
        history_id=history_id,
        session_id=session_id,
        symbol=str(continuity_report["symbol"]),
        continuity_attempts=[*previous_attempts, continuity_report],
        max_attempts=max_attempts,
    )
    path = write_upbit_public_rest_continuity_history_report(root=root, report=history)
    return path, history
