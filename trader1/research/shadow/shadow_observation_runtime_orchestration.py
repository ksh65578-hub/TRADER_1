from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    shadow_observation_actual_runtime_harness_hash,
    validate_shadow_observation_actual_runtime_harness_report,
)
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    shadow_observation_persistent_runtime_hash,
    validate_shadow_observation_persistent_runtime_report,
)
from trader1.research.shadow.shadow_runner import AGENTS_SHA256, TRADER1_SHA256, utc_now


SHADOW_OBSERVATION_RUNTIME_ORCHESTRATION_SCHEMA_ID = "trader1.shadow_observation_runtime_orchestration_report.v1"
MINIMUM_LONG_RUN_RUNTIME_WINDOW_SECONDS = 86400
MINIMUM_LONG_RUN_ACTUAL_CYCLE_COUNT = 2880
MINIMUM_LONG_RUN_EVIDENCE_WINDOW_COUNT = 20


@dataclass(frozen=True)
class ShadowObservationRuntimeOrchestrationValidationResult:
    status: str
    message: str
    blocker_code: str | None


def shadow_observation_runtime_orchestration_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("orchestration_report_hash", None)
    return _sha256_payload(payload)


def build_shadow_observation_runtime_orchestration_report(
    *,
    orchestration_id: str,
    persistent_runtime_report: dict[str, Any],
    actual_runtime_harness_report: dict[str, Any],
    minimum_runtime_window_seconds: int = 86400,
    minimum_actual_cycle_count: int = 2880,
    minimum_evidence_window_count: int = 20,
) -> dict[str, Any]:
    persistent_result = validate_shadow_observation_persistent_runtime_report(persistent_runtime_report)
    harness_result = validate_shadow_observation_actual_runtime_harness_report(actual_runtime_harness_report)
    persistent_hash = str(persistent_runtime_report.get("runtime_report_hash") or "")
    harness_hash = str(actual_runtime_harness_report.get("harness_report_hash") or "")
    persistent_hash_verified = persistent_hash == shadow_observation_persistent_runtime_hash(persistent_runtime_report)
    harness_hash_verified = harness_hash == shadow_observation_actual_runtime_harness_hash(actual_runtime_harness_report)
    source_scope_match = (
        persistent_runtime_report.get("exchange") == "UPBIT"
        and persistent_runtime_report.get("market_type") == "KRW_SPOT"
        and actual_runtime_harness_report.get("exchange") == "UPBIT"
        and actual_runtime_harness_report.get("market_type") == "KRW_SPOT"
        and persistent_runtime_report.get("source_mode") == "PAPER"
        and persistent_runtime_report.get("mode") == "SHADOW"
        and actual_runtime_harness_report.get("source_mode") == "PAPER"
        and actual_runtime_harness_report.get("mode") == "SHADOW"
    )
    persistent_source_is_stub = (
        persistent_runtime_report.get("runtime_execution_mode") == "BOUNDED_SHADOW_STUB"
        and persistent_runtime_report.get("runtime_evidence_role") == "PERSISTENT_RUNTIME_STUB_ONLY"
        and persistent_runtime_report.get("duration_evidence_role") == "NOT_LONG_RUN_EVIDENCE"
        and persistent_runtime_report.get("actual_persistent_runtime_executed") is False
    )
    persistent_source_is_short_window = (
        persistent_runtime_report.get("runtime_execution_mode") == "ACTUAL_PAPER_SHADOW_SHORT_WINDOW"
        and persistent_runtime_report.get("runtime_evidence_role") == "PERSISTENT_RUNTIME_SHORT_WINDOW_ONLY"
        and persistent_runtime_report.get("duration_evidence_role") == "SHORT_WINDOW_RUNTIME_EVIDENCE_NOT_LONG_RUN"
        and persistent_runtime_report.get("actual_persistent_runtime_executed") is True
    )
    persistent_stub_confirmed = (
        (persistent_source_is_stub or persistent_source_is_short_window)
        and persistent_runtime_report.get("long_run_evidence_eligible") is False
    )
    short_window_confirmed = (
        actual_runtime_harness_report.get("harness_execution_mode") == "NON_LIVE_LOCAL_PAPER_SHADOW_HARNESS"
        and actual_runtime_harness_report.get("runtime_evidence_role") == "EXECUTION_HARNESS_PROOF_ONLY_NOT_LONG_RUN"
        and actual_runtime_harness_report.get("runtime_evidence_status") == "BLOCKED_LONG_RUN_EVIDENCE_MISSING"
        and actual_runtime_harness_report.get("long_run_evidence_present") is False
        and actual_runtime_harness_report.get("long_run_evidence_eligible") is False
    )
    source_hashes_verified = persistent_hash_verified and harness_hash_verified
    source_runtime_hash_pairing_verified = actual_runtime_harness_report.get("source_runtime_report_hash") == persistent_hash
    source_validation_status = "PASS" if persistent_result.status == "PASS" and harness_result.status == "PASS" else "BLOCKED"
    observed_actual_cycle_count = int(persistent_runtime_report.get("completed_cycle_count") or 0) if persistent_source_is_short_window else 0
    observed_actual_runtime_seconds = int(persistent_runtime_report.get("observed_runtime_seconds") or 0) if persistent_source_is_short_window else 0

    blockers: list[dict[str, str]] = []
    if persistent_result.status != "PASS":
        blockers.append(_blocker(persistent_result.blocker_code or "DATA_QUALITY_INSUFFICIENT", persistent_result.message))
    if harness_result.status != "PASS":
        blockers.append(_blocker(harness_result.blocker_code or "DATA_QUALITY_INSUFFICIENT", harness_result.message))
    if not source_hashes_verified:
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "runtime orchestration source hashes are not verified"))
    if not source_runtime_hash_pairing_verified:
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "runtime orchestration persistent runtime does not match the harness source runtime hash"))
    if not source_scope_match:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "runtime orchestration sources must remain UPBIT/KRW_SPOT PAPER-to-SHADOW scoped"))
    if not persistent_stub_confirmed:
        blockers.append(_blocker("ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING", "persistent runtime source did not remain stub or short-window not-long-run evidence"))
    if observed_actual_runtime_seconds >= int(minimum_runtime_window_seconds) or observed_actual_cycle_count >= int(minimum_actual_cycle_count):
        blockers.append(_blocker("ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING", "short-window orchestration cannot satisfy long-run thresholds"))
    if not short_window_confirmed:
        blockers.append(_blocker("ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING", "actual runtime harness source did not remain short-window not-long-run evidence"))
    blockers.append(
        _blocker(
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
            "Actual long-run PAPER/SHADOW runtime evidence is missing; short-window harness and stub artifacts cannot satisfy the review gate.",
        )
    )
    blockers.append(
        _blocker(
            "MEASUREMENT_MISSING",
            "No validated actual runtime window, cycle count, and per-window PAPER/SHADOW source coverage has been recorded.",
        )
    )

    source_evidence_bindings = [
        {
            "source_role": "PERSISTENT_RUNTIME_SHORT_WINDOW" if persistent_source_is_short_window else "PERSISTENT_RUNTIME_STUB",
            "source_id": str(persistent_runtime_report.get("runtime_id") or ""),
            "source_hash": persistent_hash,
            "hash_verified": persistent_hash_verified,
            "validation_status": persistent_result.status,
            "evidence_role": str(persistent_runtime_report.get("runtime_evidence_role") or ""),
        },
        {
            "source_role": "SHORT_WINDOW_HARNESS",
            "source_id": str(actual_runtime_harness_report.get("harness_id") or ""),
            "source_hash": harness_hash,
            "hash_verified": harness_hash_verified,
            "validation_status": harness_result.status,
            "evidence_role": str(actual_runtime_harness_report.get("runtime_evidence_role") or ""),
        },
    ]
    report = {
        "schema_id": SHADOW_OBSERVATION_RUNTIME_ORCHESTRATION_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": TRADER1_SHA256,
            "agents_sha256": AGENTS_SHA256,
        },
        "orchestration_id": orchestration_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "source_mode": "PAPER",
        "mode": "SHADOW",
        "session_id": orchestration_id,
        "orchestration_artifact_path": f"system/runtime/upbit/krw_spot/shadow/{orchestration_id}/runtime_orchestration_report.json",
        "orchestration_status": "BLOCKED",
        "orchestration_decision": "BLOCK_LONG_RUN_EVIDENCE",
        "source_validation_status": source_validation_status,
        "source_hashes_verified": source_hashes_verified,
        "source_runtime_hash_pairing_verified": source_runtime_hash_pairing_verified,
        "source_scope_match": source_scope_match,
        "source_binding_count": len(source_evidence_bindings),
        "source_evidence_bindings": source_evidence_bindings,
        "persistent_stub_not_long_run_confirmed": persistent_stub_confirmed,
        "short_window_harness_not_long_run_confirmed": short_window_confirmed,
        "minimum_runtime_window_seconds": int(minimum_runtime_window_seconds),
        "observed_actual_runtime_seconds": observed_actual_runtime_seconds,
        "minimum_actual_cycle_count": int(minimum_actual_cycle_count),
        "observed_actual_cycle_count": observed_actual_cycle_count,
        "minimum_evidence_window_count": int(minimum_evidence_window_count),
        "observed_evidence_window_count": 0,
        "actual_long_run_runtime_present": False,
        "long_run_evidence_eligible": False,
        "scorecard_input_eligible": False,
        "optimizer_ranking_action": "BLOCK_RANKING",
        "runtime_evidence_role": "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN",
        "dashboard_display_truth_only": True,
        "dashboard_visibility_status": "VISIBLE_AS_BLOCKED_LONG_RUN_REQUIREMENTS",
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"],
        "blockers": _dedupe_blockers(blockers),
        "operator_message": (
            "Runtime orchestration is healthy enough for display-only review, but it is short-window only and not long-run evidence. "
            "Live orders remain blocked."
        ),
        "next_operator_action": (
            "Continue PAPER/SHADOW collection until actual duration, cycle, heartbeat, recovery, and per-window source "
            "coverage pass; do not treat short-window harness output as LIVE_READY."
        ),
        "orchestration_report_hash": "",
    }
    report["orchestration_report_hash"] = shadow_observation_runtime_orchestration_hash(report)
    return report


def validate_shadow_observation_runtime_orchestration_report(
    report: dict[str, Any],
) -> ShadowObservationRuntimeOrchestrationValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "authority",
        "orchestration_id",
        "exchange",
        "market_type",
        "source_mode",
        "mode",
        "session_id",
        "orchestration_artifact_path",
        "orchestration_status",
        "orchestration_decision",
        "source_validation_status",
        "source_hashes_verified",
        "source_runtime_hash_pairing_verified",
        "source_scope_match",
        "source_binding_count",
        "source_evidence_bindings",
        "persistent_stub_not_long_run_confirmed",
        "short_window_harness_not_long_run_confirmed",
        "minimum_runtime_window_seconds",
        "observed_actual_runtime_seconds",
        "minimum_actual_cycle_count",
        "observed_actual_cycle_count",
        "minimum_evidence_window_count",
        "observed_evidence_window_count",
        "actual_long_run_runtime_present",
        "long_run_evidence_eligible",
        "scorecard_input_eligible",
        "optimizer_ranking_action",
        "runtime_evidence_role",
        "dashboard_display_truth_only",
        "dashboard_visibility_status",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "operator_message",
        "next_operator_action",
        "orchestration_report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ShadowObservationRuntimeOrchestrationValidationResult("FAIL", f"runtime orchestration report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != SHADOW_OBSERVATION_RUNTIME_ORCHESTRATION_SCHEMA_ID:
        return ShadowObservationRuntimeOrchestrationValidationResult("FAIL", "runtime orchestration schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("orchestration_report_hash") != shadow_observation_runtime_orchestration_hash(report):
        return ShadowObservationRuntimeOrchestrationValidationResult("FAIL", "runtime orchestration hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration must remain UPBIT/KRW_SPOT for MVP-4", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_mode") != "PAPER" or report.get("mode") != "SHADOW":
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration must bind PAPER source to SHADOW output", "SNAPSHOT_SCOPE_MISMATCH")
    if "/shadow/" not in str(report.get("orchestration_artifact_path") or ""):
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration artifact path lacks shadow namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("orchestration_status") != "BLOCKED" or report.get("orchestration_decision") != "BLOCK_LONG_RUN_EVIDENCE":
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration cannot claim long-run readiness in MVP-4", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if report.get("source_validation_status") != "PASS":
        source_blockers = report.get("blockers") or []
        source_blocker_code = source_blockers[0].get("code") if source_blockers else "DATA_QUALITY_INSUFFICIENT"
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration source validation is not PASS", source_blocker_code)
    if report.get("source_hashes_verified") is not True or report.get("source_runtime_hash_pairing_verified") is not True or report.get("source_scope_match") is not True:
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration source hash, pairing, or scope verification failed", "SCHEMA_IDENTITY_MISMATCH")
    bindings = report.get("source_evidence_bindings") or []
    if report.get("source_binding_count") != len(bindings) or len(bindings) != 2:
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration must bind exactly persistent runtime and short-window harness sources", "MEASUREMENT_MISSING")
    roles = {binding.get("source_role") for binding in bindings if isinstance(binding, dict)}
    persistent_roles = roles & {"PERSISTENT_RUNTIME_STUB", "PERSISTENT_RUNTIME_SHORT_WINDOW"}
    if roles - {"PERSISTENT_RUNTIME_STUB", "PERSISTENT_RUNTIME_SHORT_WINDOW", "SHORT_WINDOW_HARNESS"} or len(persistent_roles) != 1 or "SHORT_WINDOW_HARNESS" not in roles:
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration source roles are incomplete", "MEASUREMENT_MISSING")
    for binding in bindings:
        if binding.get("hash_verified") is not True or binding.get("validation_status") != "PASS":
            return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration source binding is not verified", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("persistent_stub_not_long_run_confirmed") is not True:
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "persistent runtime source must remain not-long-run evidence", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if report.get("short_window_harness_not_long_run_confirmed") is not True:
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "short-window harness source must remain not-long-run evidence", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if int(report.get("minimum_runtime_window_seconds", 0)) < MINIMUM_LONG_RUN_RUNTIME_WINDOW_SECONDS:
        return ShadowObservationRuntimeOrchestrationValidationResult(
            "BLOCKED",
            "runtime orchestration minimum runtime window is below the MVP-4 long-run evidence floor",
            "MEASUREMENT_MISSING",
        )
    if int(report.get("minimum_actual_cycle_count", 0)) < MINIMUM_LONG_RUN_ACTUAL_CYCLE_COUNT:
        return ShadowObservationRuntimeOrchestrationValidationResult(
            "BLOCKED",
            "runtime orchestration minimum cycle count is below the MVP-4 long-run evidence floor",
            "MEASUREMENT_MISSING",
        )
    if int(report.get("minimum_evidence_window_count", 0)) < MINIMUM_LONG_RUN_EVIDENCE_WINDOW_COUNT:
        return ShadowObservationRuntimeOrchestrationValidationResult(
            "BLOCKED",
            "runtime orchestration minimum evidence window count is below the MVP-4 long-run evidence floor",
            "MEASUREMENT_MISSING",
        )
    observed_runtime_seconds = int(report.get("observed_actual_runtime_seconds", -1))
    observed_cycle_count = int(report.get("observed_actual_cycle_count", -1))
    if observed_runtime_seconds < 0 or observed_cycle_count < 0:
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration observed duration and cycles cannot be negative", "MEASUREMENT_MISSING")
    if observed_runtime_seconds >= int(report.get("minimum_runtime_window_seconds", 0)) or observed_cycle_count >= int(report.get("minimum_actual_cycle_count", 0)):
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration cannot satisfy long-run duration or cycle thresholds from short-window evidence", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if int(report.get("observed_evidence_window_count", -1)) != 0:
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration cannot claim validated long-run evidence windows", "MEASUREMENT_MISSING")
    if any(report.get(field) for field in ("actual_long_run_runtime_present", "long_run_evidence_eligible", "scorecard_input_eligible", "promotion_eligible")):
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration attempted long-run, scorecard, or promotion eligibility", "LIVE_FINAL_GUARD_FAILED")
    if report.get("optimizer_ranking_action") != "BLOCK_RANKING" or report.get("runtime_evidence_role") != "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN":
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration cannot become optimizer ranking input", "OPTIMIZER_DIRECT_LIVE_FORBIDDEN")
    if report.get("dashboard_display_truth_only") is not True or report.get("dashboard_visibility_status") != "VISIBLE_AS_BLOCKED_LONG_RUN_REQUIREMENTS":
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration dashboard visibility must remain blocked display truth", "MEASUREMENT_MISSING")
    if any(report.get(field) for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called")):
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration attempted live/order or scale-up state", "LIVE_FINAL_GUARD_FAILED")
    blockers = report.get("blockers") or []
    if not blockers or report.get("primary_blocker_code") != blockers[0].get("code"):
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration must expose a primary blocker", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if not any(blocker.get("code") == "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING" for blocker in blockers):
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "runtime orchestration missing actual persistent runtime blocker", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    operator_text = f"{report.get('operator_message', '')} {report.get('next_operator_action', '')}".lower()
    if "not long-run evidence" not in operator_text or "live orders remain blocked" not in operator_text:
        return ShadowObservationRuntimeOrchestrationValidationResult("BLOCKED", "operator text must prevent long-run and live readiness misunderstanding", "MEASUREMENT_MISSING")
    return ShadowObservationRuntimeOrchestrationValidationResult(
        "PASS",
        "runtime orchestration correctly blocks long-run evidence, optimizer ranking, live orders, and scale-up",
        None,
    )


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
