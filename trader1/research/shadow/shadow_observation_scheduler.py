from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from trader1.research.shadow.shadow_observation_stream import (
    shadow_observation_stream_hash,
    validate_shadow_observation_stream_report,
)
from trader1.research.shadow.shadow_runner import AGENTS_SHA256, TRADER1_SHA256, utc_now


SHADOW_OBSERVATION_SCHEDULER_GUARD_SCHEMA_ID = "trader1.shadow_observation_scheduler_guard_report.v1"


@dataclass(frozen=True)
class ShadowObservationSchedulerGuardValidationResult:
    status: str
    message: str
    blocker_code: str | None


def shadow_observation_scheduler_guard_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("scheduler_guard_hash", None)
    return _sha256_payload(payload)


def build_shadow_observation_scheduler_guard_report(
    *,
    scheduler_id: str,
    stream_report: dict[str, Any],
    writer_id: str,
    active_writer_id: str | None = None,
    lock_acquired: bool = True,
    lock_lease_seconds: int = 30,
    lock_lease_fresh: bool = True,
    partial_temp_artifact_count: int = 0,
    persisted_stream_hash: str | None = None,
    next_sequence_number: int | None = None,
) -> dict[str, Any]:
    stream_result = validate_shadow_observation_stream_report(stream_report)
    stream_hash = str(stream_report.get("stream_hash") or "")
    persisted_hash = persisted_stream_hash if persisted_stream_hash is not None else stream_hash
    active_owner = active_writer_id if active_writer_id is not None else writer_id
    observation_bindings = stream_report.get("observation_bindings") if isinstance(stream_report.get("observation_bindings"), list) else []
    last_committed_sequence = max(
        [int(item.get("sequence_number", 0)) for item in observation_bindings if isinstance(item, dict)] or [0]
    )
    expected_next_sequence_number = last_committed_sequence + 1
    chosen_next_sequence_number = next_sequence_number if next_sequence_number is not None else expected_next_sequence_number

    lock_owner_match = bool(lock_acquired and active_owner == writer_id)
    concurrent_writer_detected = bool(active_owner != writer_id)
    persisted_stream_hash_match = persisted_hash == stream_hash
    sequence_gap_detected = chosen_next_sequence_number != expected_next_sequence_number
    partial_write_recovery_status = "PASS" if partial_temp_artifact_count == 0 else "BLOCKED"
    lock_lease_valid = int(lock_lease_seconds) > 0
    lock_lease_status = "PASS" if lock_lease_valid and bool(lock_lease_fresh) else "BLOCKED"

    blockers: list[dict[str, str]] = []
    if stream_result.status != "PASS":
        blockers.append(_blocker(stream_result.blocker_code or "DATA_QUALITY_INSUFFICIENT", stream_result.message))
    if not lock_acquired or concurrent_writer_detected or not lock_owner_match:
        blockers.append(_blocker("DUPLICATE_WRITER_RISK", "SHADOW observation scheduler lock is not exclusively owned"))
    if not lock_lease_valid:
        blockers.append(_blocker("DUPLICATE_WRITER_RISK", "SHADOW observation scheduler lock lease must be positive"))
    if not lock_lease_fresh:
        blockers.append(_blocker("DUPLICATE_WRITER_RISK", "SHADOW observation scheduler lock lease is stale or freshness is not proven"))
    if partial_temp_artifact_count:
        blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "partial SHADOW stream temp artifacts require recovery"))
    if not persisted_stream_hash_match:
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "persisted SHADOW stream hash does not match scheduler input"))
    if sequence_gap_detected:
        blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "next SHADOW stream sequence does not follow committed sequence"))

    scheduler_status = "PASS" if not blockers else "BLOCKED"
    report = {
        "schema_id": SHADOW_OBSERVATION_SCHEDULER_GUARD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": TRADER1_SHA256,
            "agents_sha256": AGENTS_SHA256,
        },
        "scheduler_id": scheduler_id,
        "stream_id": str(stream_report.get("stream_id") or ""),
        "exchange": str(stream_report.get("exchange") or "UPBIT"),
        "market_type": str(stream_report.get("market_type") or "KRW_SPOT"),
        "source_mode": "PAPER",
        "mode": "SHADOW",
        "scheduler_artifact_path": f"system/runtime/upbit/krw_spot/shadow/{scheduler_id}/shadow_observation_scheduler_guard_report.json",
        "writer_id": writer_id,
        "active_writer_id": active_owner,
        "lock_acquired": bool(lock_acquired),
        "lock_owner_match": lock_owner_match,
        "concurrent_writer_detected": concurrent_writer_detected,
        "lock_lease_seconds": int(lock_lease_seconds),
        "lock_lease_fresh": bool(lock_lease_fresh),
        "lock_lease_status": lock_lease_status,
        "source_stream_hash": stream_hash,
        "persisted_stream_hash": persisted_hash,
        "persisted_stream_hash_match": persisted_stream_hash_match,
        "source_stream_status": str(stream_report.get("stream_status") or "UNKNOWN"),
        "source_stream_validation_status": stream_result.status,
        "observation_count": int(stream_report.get("observation_count", 0)),
        "last_committed_sequence": last_committed_sequence,
        "expected_next_sequence_number": expected_next_sequence_number,
        "next_sequence_number": int(chosen_next_sequence_number),
        "sequence_gap_detected": sequence_gap_detected,
        "partial_temp_artifact_count": int(partial_temp_artifact_count),
        "partial_write_recovery_status": partial_write_recovery_status,
        "recovery_action": "NO_RECOVERY_NEEDED" if scheduler_status == "PASS" else "RECONCILE_REQUIRED",
        "scheduler_status": scheduler_status,
        "run_action": "APPEND_SHADOW_OBSERVATION_ONLY" if scheduler_status == "PASS" else "BLOCKED",
        "optimizer_input_role": "SHADOW_SCHEDULER_GUARD_ONLY",
        "dashboard_display_truth_only": True,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": _dedupe_blockers(blockers),
        "scheduler_guard_hash": "",
    }
    report["scheduler_guard_hash"] = shadow_observation_scheduler_guard_hash(report)
    return report


def validate_shadow_observation_scheduler_guard_report(
    report: dict[str, Any],
) -> ShadowObservationSchedulerGuardValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "authority",
        "scheduler_id",
        "stream_id",
        "exchange",
        "market_type",
        "source_mode",
        "mode",
        "scheduler_artifact_path",
        "writer_id",
        "active_writer_id",
        "lock_acquired",
        "lock_owner_match",
        "concurrent_writer_detected",
        "lock_lease_seconds",
        "lock_lease_fresh",
        "lock_lease_status",
        "source_stream_hash",
        "persisted_stream_hash",
        "persisted_stream_hash_match",
        "source_stream_status",
        "source_stream_validation_status",
        "observation_count",
        "last_committed_sequence",
        "expected_next_sequence_number",
        "next_sequence_number",
        "sequence_gap_detected",
        "partial_temp_artifact_count",
        "partial_write_recovery_status",
        "recovery_action",
        "scheduler_status",
        "run_action",
        "optimizer_input_role",
        "dashboard_display_truth_only",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "scheduler_guard_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ShadowObservationSchedulerGuardValidationResult("FAIL", f"SHADOW scheduler guard missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != SHADOW_OBSERVATION_SCHEDULER_GUARD_SCHEMA_ID:
        return ShadowObservationSchedulerGuardValidationResult("FAIL", "SHADOW scheduler guard schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("scheduler_guard_hash") != shadow_observation_scheduler_guard_hash(report):
        return ShadowObservationSchedulerGuardValidationResult("FAIL", "SHADOW scheduler guard hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler guard must remain UPBIT/KRW_SPOT in MVP-4", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_mode") != "PAPER" or report.get("mode") != "SHADOW":
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler guard must bind PAPER source to SHADOW output", "SNAPSHOT_SCOPE_MISMATCH")
    if "/shadow/" not in str(report.get("scheduler_artifact_path") or ""):
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler guard path lacks shadow namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_stream_validation_status") != "PASS" or report.get("source_stream_status") != "PASS":
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler source stream is not PASS", "DATA_QUALITY_INSUFFICIENT")
    expected_lock_owner_match = bool(report.get("lock_acquired") and report.get("active_writer_id") == report.get("writer_id"))
    expected_concurrent_writer_detected = bool(report.get("active_writer_id") != report.get("writer_id"))
    if report.get("lock_owner_match") is not expected_lock_owner_match:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler lock owner summary drift", "DUPLICATE_WRITER_RISK")
    if report.get("concurrent_writer_detected") is not expected_concurrent_writer_detected:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler concurrent writer summary drift", "DUPLICATE_WRITER_RISK")
    if int(report.get("lock_lease_seconds", 0)) <= 0:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler lock lease is invalid", "DUPLICATE_WRITER_RISK")
    expected_lock_lease_status = "PASS" if bool(report.get("lock_lease_fresh")) else "BLOCKED"
    if report.get("lock_lease_status") != expected_lock_lease_status:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler lock lease freshness summary drift", "DUPLICATE_WRITER_RISK")
    if report.get("lock_lease_status") != "PASS":
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler lock lease is stale or freshness is unproven", "DUPLICATE_WRITER_RISK")
    if not report.get("lock_acquired") or not expected_lock_owner_match or expected_concurrent_writer_detected:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler lock is not single-writer", "DUPLICATE_WRITER_RISK")
    persisted_stream_hash_match = report.get("source_stream_hash") == report.get("persisted_stream_hash")
    if report.get("persisted_stream_hash_match") is not persisted_stream_hash_match:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler persisted hash summary drift", "SCHEMA_IDENTITY_MISMATCH")
    if not persisted_stream_hash_match:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler persisted stream hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_next_sequence_number = int(report.get("last_committed_sequence", -1)) + 1
    sequence_gap_detected = report.get("next_sequence_number") != report.get("expected_next_sequence_number")
    if int(report.get("expected_next_sequence_number", -1)) != expected_next_sequence_number:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler expected sequence summary drift", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if report.get("sequence_gap_detected") is not sequence_gap_detected:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler sequence gap summary drift", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if sequence_gap_detected:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler sequence gap requires recovery", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if report.get("partial_temp_artifact_count") != 0 or report.get("partial_write_recovery_status") != "PASS":
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler partial write recovery is required", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if report.get("optimizer_input_role") != "SHADOW_SCHEDULER_GUARD_ONLY":
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler guard cannot become optimizer ranking or live input", "OPTIMIZER_DIRECT_LIVE_FORBIDDEN")
    if any(report.get(field) for field in ("promotion_eligible", "live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called")):
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler guard attempted live/order or scale-up state", "LIVE_FINAL_GUARD_FAILED")

    blockers = report.get("blockers") or []
    if report.get("scheduler_status") == "PASS":
        if blockers:
            return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "PASS SHADOW scheduler guard cannot carry blockers", blockers[0].get("code", "UNKNOWN_BLOCKED"))
        if report.get("recovery_action") != "NO_RECOVERY_NEEDED" or report.get("run_action") != "APPEND_SHADOW_OBSERVATION_ONLY":
            return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "PASS SHADOW scheduler guard has unsafe action", "PARTIAL_WRITE_RECOVERY_REQUIRED")
        return ShadowObservationSchedulerGuardValidationResult("PASS", "SHADOW scheduler guard is single-writer, sequence-safe, recovery-clean, and live-blocked", None)
    if not blockers:
        return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "blocked SHADOW scheduler guard must carry explicit blockers", "MEASUREMENT_MISSING")
    return ShadowObservationSchedulerGuardValidationResult("BLOCKED", "SHADOW scheduler guard is blocked", blockers[0].get("code", "UNKNOWN_BLOCKED"))


def _blocker(code: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": "HIGH", "message": message}


def _dedupe_blockers(blockers: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for blocker in blockers:
        key = (blocker.get("code", ""), blocker.get("message", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(blocker)
    return deduped


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()
