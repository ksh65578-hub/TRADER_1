from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from trader1.research.shadow.shadow_observation_scheduler import (
    shadow_observation_scheduler_guard_hash,
    validate_shadow_observation_scheduler_guard_report,
)
from trader1.research.shadow.shadow_runner import AGENTS_SHA256, TRADER1_SHA256, utc_now


SHADOW_OBSERVATION_PERSISTENT_RUNTIME_SCHEMA_ID = "trader1.shadow_observation_persistent_runtime_report.v1"
PERSISTENT_RUNTIME_MAX_STUB_CYCLES = 20
PERSISTENT_RUNTIME_MAX_STUB_SECONDS = 300


@dataclass(frozen=True)
class ShadowObservationPersistentRuntimeValidationResult:
    status: str
    message: str
    blocker_code: str | None


def shadow_observation_persistent_runtime_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("runtime_report_hash", None)
    return _sha256_payload(payload)


def build_shadow_observation_persistent_runtime_report(
    *,
    runtime_id: str,
    scheduler_guard_report: dict[str, Any],
    requested_cycle_count: int = 1,
    completed_cycle_count: int | None = None,
    max_cycle_count: int = 20,
    heartbeat_interval_seconds: int = 30,
    max_runtime_seconds: int = 300,
    observed_runtime_seconds: int = 0,
    atomic_commit_count: int | None = None,
    cycle_commit_ids: list[str] | None = None,
    partial_temp_artifact_count: int = 0,
    graceful_shutdown: bool = True,
    order_adapter_called: bool = False,
) -> dict[str, Any]:
    guard_result = validate_shadow_observation_scheduler_guard_report(scheduler_guard_report)
    guard_hash = str(scheduler_guard_report.get("scheduler_guard_hash") or "")
    completed = int(completed_cycle_count if completed_cycle_count is not None else requested_cycle_count)
    atomic_commits = int(atomic_commit_count if atomic_commit_count is not None else completed)
    heartbeat_count = max(0, completed)
    commits = list(cycle_commit_ids) if cycle_commit_ids is not None else _default_cycle_commit_ids(runtime_id, guard_hash, completed)
    distinct_cycle_commit_count = len(set(commits))
    duplicate_cycle_commit_count = len(commits) - distinct_cycle_commit_count
    cycle_identity_status = "PASS"
    if len(commits) != max(0, completed) or duplicate_cycle_commit_count or not all(_is_sha256_hex(item) for item in commits):
        cycle_identity_status = "BLOCKED"
    estimated_runtime_seconds = max(0, completed) * int(heartbeat_interval_seconds)
    observed_seconds = int(observed_runtime_seconds)

    blockers: list[dict[str, str]] = []
    if guard_result.status != "PASS":
        blockers.append(_blocker(guard_result.blocker_code or "DATA_QUALITY_INSUFFICIENT", guard_result.message))
    if guard_hash != shadow_observation_scheduler_guard_hash(scheduler_guard_report):
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "scheduler guard hash does not match persistent runtime input"))
    if int(requested_cycle_count) <= 0 or int(max_cycle_count) <= 0:
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "persistent SHADOW runtime cycle limits must be positive"))
    if int(requested_cycle_count) > int(max_cycle_count):
        blockers.append(_blocker("RESOURCE_LIMIT_BLOCK", "persistent SHADOW runtime requested more cycles than the bounded stub allows"))
    if (
        int(requested_cycle_count) > PERSISTENT_RUNTIME_MAX_STUB_CYCLES
        or completed > PERSISTENT_RUNTIME_MAX_STUB_CYCLES
        or int(max_cycle_count) > PERSISTENT_RUNTIME_MAX_STUB_CYCLES
        or heartbeat_count > PERSISTENT_RUNTIME_MAX_STUB_CYCLES
    ):
        blockers.append(_blocker("RESOURCE_LIMIT_BLOCK", "persistent SHADOW runtime exceeds bounded stub cycle capacity"))
    if completed != int(requested_cycle_count):
        blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "persistent SHADOW runtime completed cycle count does not match request"))
    if atomic_commits != completed:
        blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "persistent SHADOW runtime atomic commit count does not match completed cycles"))
    if len(commits) != max(0, completed):
        blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "persistent SHADOW runtime cycle commit identity count does not match completed cycles"))
    if duplicate_cycle_commit_count:
        blockers.append(_blocker("DUPLICATE_WRITER_RISK", "persistent SHADOW runtime reused a cycle commit identity"))
    if not all(_is_sha256_hex(item) for item in commits):
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "persistent SHADOW runtime cycle commit identity is not a SHA256 hash"))
    if int(partial_temp_artifact_count) != 0:
        blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "persistent SHADOW runtime left partial temp artifacts"))
    if not graceful_shutdown:
        blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "persistent SHADOW runtime did not stop cleanly"))
    if int(heartbeat_interval_seconds) <= 0 or int(heartbeat_interval_seconds) > int(max_runtime_seconds):
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "persistent SHADOW runtime heartbeat interval is invalid for bounded stub"))
    if int(max_runtime_seconds) > PERSISTENT_RUNTIME_MAX_STUB_SECONDS:
        blockers.append(_blocker("RESOURCE_LIMIT_BLOCK", "persistent SHADOW runtime max duration exceeds short-window stub capacity"))
    if estimated_runtime_seconds > PERSISTENT_RUNTIME_MAX_STUB_SECONDS:
        blockers.append(_blocker("RESOURCE_LIMIT_BLOCK", "persistent SHADOW runtime estimated duration exceeds short-window stub capacity"))
    if observed_seconds < 0:
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "persistent SHADOW runtime observed duration cannot be negative"))
    if observed_seconds > 0:
        blockers.append(_blocker("ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING", "bounded SHADOW runtime stub cannot claim observed wall-clock runtime duration"))
    if order_adapter_called:
        blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "persistent SHADOW runtime attempted order adapter use"))

    runtime_status = "PASS" if not blockers else "BLOCKED"
    report = {
        "schema_id": SHADOW_OBSERVATION_PERSISTENT_RUNTIME_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": TRADER1_SHA256,
            "agents_sha256": AGENTS_SHA256,
        },
        "runtime_id": runtime_id,
        "scheduler_id": str(scheduler_guard_report.get("scheduler_id") or ""),
        "stream_id": str(scheduler_guard_report.get("stream_id") or ""),
        "exchange": str(scheduler_guard_report.get("exchange") or "UPBIT"),
        "market_type": str(scheduler_guard_report.get("market_type") or "KRW_SPOT"),
        "source_mode": "PAPER",
        "mode": "SHADOW",
        "runtime_artifact_path": f"system/runtime/upbit/krw_spot/shadow/{runtime_id}/shadow_observation_persistent_runtime_report.json",
        "runtime_execution_mode": "BOUNDED_SHADOW_STUB",
        "runtime_evidence_role": "PERSISTENT_RUNTIME_STUB_ONLY",
        "actual_persistent_runtime_executed": False,
        "source_scheduler_guard_hash": guard_hash,
        "source_scheduler_guard_status": str(scheduler_guard_report.get("scheduler_status") or "UNKNOWN"),
        "source_scheduler_validation_status": guard_result.status,
        "requested_cycle_count": int(requested_cycle_count),
        "completed_cycle_count": completed,
        "max_cycle_count": int(max_cycle_count),
        "heartbeat_count": heartbeat_count,
        "heartbeat_interval_seconds": int(heartbeat_interval_seconds),
        "heartbeat_status": "PASS" if heartbeat_count == completed and int(heartbeat_interval_seconds) > 0 else "BLOCKED",
        "max_runtime_seconds": int(max_runtime_seconds),
        "runtime_duration_evidence_source": "STUB_ESTIMATE_ONLY",
        "estimated_runtime_seconds": estimated_runtime_seconds,
        "observed_runtime_seconds": observed_seconds,
        "duration_evidence_role": "NOT_LONG_RUN_EVIDENCE",
        "atomic_commit_count": atomic_commits,
        "cycle_commit_ids": commits,
        "distinct_cycle_commit_count": distinct_cycle_commit_count,
        "duplicate_cycle_commit_count": duplicate_cycle_commit_count,
        "cycle_identity_status": cycle_identity_status,
        "partial_temp_artifact_count": int(partial_temp_artifact_count),
        "graceful_shutdown": bool(graceful_shutdown),
        "recovery_action": "NO_RECOVERY_NEEDED" if runtime_status == "PASS" else "RECONCILE_REQUIRED",
        "runtime_status": runtime_status,
        "run_action": "COLLECT_SHADOW_OBSERVATION_STUB_ONLY" if runtime_status == "PASS" else "BLOCKED",
        "long_run_evidence_eligible": False,
        "optimizer_input_role": "SHADOW_PERSISTENT_RUNTIME_STUB_ONLY",
        "dashboard_display_truth_only": True,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": bool(order_adapter_called),
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": _dedupe_blockers(blockers),
        "runtime_report_hash": "",
    }
    report["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(report)
    return report


def validate_shadow_observation_persistent_runtime_report(
    report: dict[str, Any],
) -> ShadowObservationPersistentRuntimeValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "authority",
        "runtime_id",
        "scheduler_id",
        "stream_id",
        "exchange",
        "market_type",
        "source_mode",
        "mode",
        "runtime_artifact_path",
        "runtime_execution_mode",
        "runtime_evidence_role",
        "actual_persistent_runtime_executed",
        "source_scheduler_guard_hash",
        "source_scheduler_guard_status",
        "source_scheduler_validation_status",
        "requested_cycle_count",
        "completed_cycle_count",
        "max_cycle_count",
        "heartbeat_count",
        "heartbeat_interval_seconds",
        "heartbeat_status",
        "max_runtime_seconds",
        "runtime_duration_evidence_source",
        "estimated_runtime_seconds",
        "observed_runtime_seconds",
        "duration_evidence_role",
        "atomic_commit_count",
        "cycle_commit_ids",
        "distinct_cycle_commit_count",
        "duplicate_cycle_commit_count",
        "cycle_identity_status",
        "partial_temp_artifact_count",
        "graceful_shutdown",
        "recovery_action",
        "runtime_status",
        "run_action",
        "long_run_evidence_eligible",
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
        "runtime_report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ShadowObservationPersistentRuntimeValidationResult("FAIL", f"persistent SHADOW runtime missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != SHADOW_OBSERVATION_PERSISTENT_RUNTIME_SCHEMA_ID:
        return ShadowObservationPersistentRuntimeValidationResult("FAIL", "persistent SHADOW runtime schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("runtime_report_hash") != shadow_observation_persistent_runtime_hash(report):
        return ShadowObservationPersistentRuntimeValidationResult("FAIL", "persistent SHADOW runtime hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime must remain UPBIT/KRW_SPOT for MVP-4", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_mode") != "PAPER" or report.get("mode") != "SHADOW":
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime must bind PAPER source to SHADOW output", "SNAPSHOT_SCOPE_MISMATCH")
    if "/shadow/" not in str(report.get("runtime_artifact_path") or ""):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime path lacks shadow namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("runtime_execution_mode") != "BOUNDED_SHADOW_STUB" or report.get("runtime_evidence_role") != "PERSISTENT_RUNTIME_STUB_ONLY":
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime cannot claim real long-run execution", "LIVE_FINAL_GUARD_FAILED")
    if report.get("actual_persistent_runtime_executed") is not False or report.get("long_run_evidence_eligible") is not False:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime stub cannot claim long-run evidence", "LIVE_FINAL_GUARD_FAILED")
    if report.get("source_scheduler_guard_status") != "PASS" or report.get("source_scheduler_validation_status") != "PASS":
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime source scheduler guard is not PASS", "DATA_QUALITY_INSUFFICIENT")
    if int(report.get("requested_cycle_count", 0)) <= 0 or int(report.get("max_cycle_count", 0)) <= 0:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime cycle limits are invalid", "DATA_QUALITY_INSUFFICIENT")
    if int(report.get("requested_cycle_count", 0)) > int(report.get("max_cycle_count", 0)):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime cycle count exceeds bounded stub limit", "RESOURCE_LIMIT_BLOCK")
    if (
        int(report.get("requested_cycle_count", 0)) > PERSISTENT_RUNTIME_MAX_STUB_CYCLES
        or int(report.get("completed_cycle_count", 0)) > PERSISTENT_RUNTIME_MAX_STUB_CYCLES
        or int(report.get("max_cycle_count", 0)) > PERSISTENT_RUNTIME_MAX_STUB_CYCLES
        or int(report.get("heartbeat_count", 0)) > PERSISTENT_RUNTIME_MAX_STUB_CYCLES
    ):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime exceeds bounded stub cycle capacity", "RESOURCE_LIMIT_BLOCK")
    if report.get("completed_cycle_count") != report.get("requested_cycle_count"):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime did not complete requested cycles", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if report.get("atomic_commit_count") != report.get("completed_cycle_count"):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime atomic commit count mismatch", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    cycle_commit_ids = [str(item) for item in report.get("cycle_commit_ids") or []]
    duplicate_cycle_commit_count = len(cycle_commit_ids) - len(set(cycle_commit_ids))
    if len(cycle_commit_ids) != int(report.get("completed_cycle_count", -1)):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime cycle commit identity count mismatch", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if int(report.get("distinct_cycle_commit_count", -1)) != len(set(cycle_commit_ids)):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime distinct cycle identity summary drift", "SCHEMA_IDENTITY_MISMATCH")
    if int(report.get("duplicate_cycle_commit_count", -1)) != duplicate_cycle_commit_count:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime duplicate cycle identity summary drift", "DUPLICATE_WRITER_RISK")
    if duplicate_cycle_commit_count:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime reused cycle commit identity", "DUPLICATE_WRITER_RISK")
    if not all(_is_sha256_hex(item) for item in cycle_commit_ids):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime cycle commit identity is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("cycle_identity_status") != "PASS":
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime cycle identity status is not PASS", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if report.get("partial_temp_artifact_count") != 0:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime requires recovery", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if report.get("graceful_shutdown") is not True:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime shutdown was not graceful", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if report.get("heartbeat_status") != "PASS" or int(report.get("heartbeat_count", 0)) < int(report.get("completed_cycle_count", 0)):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime heartbeat is insufficient", "DATA_QUALITY_INSUFFICIENT")
    if int(report.get("max_runtime_seconds", 0)) > PERSISTENT_RUNTIME_MAX_STUB_SECONDS:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime max duration exceeds short-window stub capacity", "RESOURCE_LIMIT_BLOCK")
    if int(report.get("heartbeat_interval_seconds", 0)) > int(report.get("max_runtime_seconds", 0)):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime heartbeat interval exceeds max runtime budget", "RESOURCE_LIMIT_BLOCK")
    if report.get("runtime_duration_evidence_source") != "STUB_ESTIMATE_ONLY":
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime cannot claim observed wall-clock duration evidence", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    expected_estimated_runtime_seconds = int(report.get("completed_cycle_count", 0)) * int(report.get("heartbeat_interval_seconds", 0))
    if int(report.get("estimated_runtime_seconds", -1)) != expected_estimated_runtime_seconds:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime estimated duration summary drift", "SCHEMA_IDENTITY_MISMATCH")
    if expected_estimated_runtime_seconds > int(report.get("max_runtime_seconds", 0)):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime estimated duration exceeds max runtime budget", "RESOURCE_LIMIT_BLOCK")
    if expected_estimated_runtime_seconds > PERSISTENT_RUNTIME_MAX_STUB_SECONDS:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime estimated duration exceeds short-window stub capacity", "RESOURCE_LIMIT_BLOCK")
    if int(report.get("observed_runtime_seconds", -1)) != 0:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime stub cannot claim observed runtime duration", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if report.get("duration_evidence_role") != "NOT_LONG_RUN_EVIDENCE":
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime duration role must remain not-long-run evidence", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if report.get("optimizer_input_role") != "SHADOW_PERSISTENT_RUNTIME_STUB_ONLY":
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime cannot become optimizer ranking or live input", "OPTIMIZER_DIRECT_LIVE_FORBIDDEN")
    if any(report.get(field) for field in ("promotion_eligible", "live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called")):
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime attempted live/order or scale-up state", "LIVE_FINAL_GUARD_FAILED")
    if report.get("recovery_action") != "NO_RECOVERY_NEEDED":
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime recovery action is required", "PARTIAL_WRITE_RECOVERY_REQUIRED")

    blockers = report.get("blockers") or []
    if report.get("runtime_status") == "PASS":
        if blockers:
            return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "PASS persistent SHADOW runtime cannot carry blockers", blockers[0].get("code", "UNKNOWN_BLOCKED"))
        if report.get("run_action") != "COLLECT_SHADOW_OBSERVATION_STUB_ONLY":
            return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "PASS persistent SHADOW runtime has unsafe action", "LIVE_FINAL_GUARD_FAILED")
        return ShadowObservationPersistentRuntimeValidationResult("PASS", "persistent SHADOW runtime stub is bounded, recovery-clean, heartbeat-visible, and live-blocked", None)
    if not blockers:
        return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "blocked persistent SHADOW runtime must carry explicit blockers", "MEASUREMENT_MISSING")
    return ShadowObservationPersistentRuntimeValidationResult("BLOCKED", "persistent SHADOW runtime is blocked", blockers[0].get("code", "UNKNOWN_BLOCKED"))


def _blocker(code: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": "HIGH", "message": message}


def _default_cycle_commit_ids(runtime_id: str, guard_hash: str, completed: int) -> list[str]:
    return [
        _sha256_payload(
            {
                "runtime_id": runtime_id,
                "source_scheduler_guard_hash": guard_hash,
                "cycle_number": index,
                "evidence_role": "PERSISTENT_RUNTIME_STUB_ONLY",
            }
        )
        for index in range(1, max(0, completed) + 1)
    ]


def _is_sha256_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


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
