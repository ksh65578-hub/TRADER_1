from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from trader1.research.shadow.shadow_observation_persistent_runtime import (
    shadow_observation_persistent_runtime_hash,
    validate_shadow_observation_persistent_runtime_report,
)
from trader1.research.shadow.shadow_runner import AGENTS_SHA256, TRADER1_SHA256, utc_now


SHADOW_OBSERVATION_ACTUAL_RUNTIME_BLOCKER_SCHEMA_ID = "trader1.shadow_observation_actual_runtime_blocker_report.v1"
MINIMUM_LONG_RUN_RUNTIME_WINDOW_SECONDS = 86400
MINIMUM_LONG_RUN_ACTUAL_CYCLE_COUNT = 2880


@dataclass(frozen=True)
class ShadowObservationActualRuntimeBlockerValidationResult:
    status: str
    message: str
    blocker_code: str | None


def shadow_observation_actual_runtime_blocker_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("blocker_report_hash", None)
    return _sha256_payload(payload)


def build_shadow_observation_actual_runtime_blocker_report(
    *,
    blocker_report_id: str,
    runtime_report: dict[str, Any],
    minimum_runtime_window_seconds: int = 86400,
    minimum_actual_cycle_count: int = 2880,
) -> dict[str, Any]:
    source_result = validate_shadow_observation_persistent_runtime_report(runtime_report)
    source_hash = str(runtime_report.get("runtime_report_hash") or "")
    source_hash_verified = source_hash == shadow_observation_persistent_runtime_hash(runtime_report)
    stub_cycle_count = int(runtime_report.get("completed_cycle_count") or 0)
    short_window_source = (
        runtime_report.get("runtime_execution_mode") == "ACTUAL_PAPER_SHADOW_SHORT_WINDOW"
        and runtime_report.get("runtime_evidence_role") == "PERSISTENT_RUNTIME_SHORT_WINDOW_ONLY"
    )
    actual_runtime_window_seconds = int(runtime_report.get("observed_runtime_seconds") or 0) if short_window_source else 0

    blockers: list[dict[str, str]] = []
    if source_result.status != "PASS":
        blockers.append(_blocker(source_result.blocker_code or "DATA_QUALITY_INSUFFICIENT", source_result.message))
    if not source_hash_verified:
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "source persistent runtime report hash is not verified"))
    blockers.append(
        _blocker(
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
            "Only short-window PAPER/SHADOW runtime output exists; actual long-run PAPER/SHADOW runtime evidence is missing.",
        )
    )
    blockers.append(
        _blocker(
            "MEASUREMENT_MISSING",
            "Stub cycles do not count toward the required actual runtime window or long-run evidence minimum.",
        )
    )

    report = {
        "schema_id": SHADOW_OBSERVATION_ACTUAL_RUNTIME_BLOCKER_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": TRADER1_SHA256,
            "agents_sha256": AGENTS_SHA256,
        },
        "blocker_report_id": blocker_report_id,
        "source_runtime_id": str(runtime_report.get("runtime_id") or ""),
        "source_runtime_report_hash": source_hash,
        "source_runtime_hash_verified": source_hash_verified,
        "source_runtime_validation_status": source_result.status,
        "exchange": str(runtime_report.get("exchange") or "UPBIT"),
        "market_type": str(runtime_report.get("market_type") or "KRW_SPOT"),
        "source_mode": "PAPER",
        "mode": "SHADOW",
        "runtime_execution_mode": str(runtime_report.get("runtime_execution_mode") or ""),
        "runtime_evidence_role": str(runtime_report.get("runtime_evidence_role") or ""),
        "runtime_evidence_status": "BLOCKED",
        "actual_runtime_evidence_present": short_window_source,
        "long_run_evidence_present": False,
        "actual_runtime_window_seconds": actual_runtime_window_seconds,
        "minimum_runtime_window_seconds": int(minimum_runtime_window_seconds),
        "stub_cycle_count": stub_cycle_count,
        "minimum_actual_cycle_count": int(minimum_actual_cycle_count),
        "stub_cycles_do_not_count_as_long_run": True,
        "minimum_evidence_window_met": False,
        "minimum_cycle_count_met": False,
        "dashboard_display_truth_only": True,
        "dashboard_visibility_status": "VISIBLE_AS_BLOCKED",
        "optimizer_input_role": "BLOCKER_ONLY_NOT_RANKING_INPUT",
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"],
        "blockers": _dedupe_blockers(blockers),
        "operator_message": (
            "PAPER/SHADOW short-window output is visible for operator review only. It is not actual long-run evidence and cannot support "
            "LIVE_READY, optimizer promotion, or scale-up."
        ),
        "next_operator_action": (
            "Run non-live PAPER/SHADOW observation until actual runtime-window evidence is collected, validated, and still "
            "keeps live orders blocked."
        ),
        "blocker_report_hash": "",
    }
    report["blocker_report_hash"] = shadow_observation_actual_runtime_blocker_hash(report)
    return report


def validate_shadow_observation_actual_runtime_blocker_report(
    report: dict[str, Any],
    *,
    runtime_report: dict[str, Any] | None = None,
) -> ShadowObservationActualRuntimeBlockerValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "authority",
        "blocker_report_id",
        "source_runtime_id",
        "source_runtime_report_hash",
        "source_runtime_hash_verified",
        "source_runtime_validation_status",
        "exchange",
        "market_type",
        "source_mode",
        "mode",
        "runtime_execution_mode",
        "runtime_evidence_role",
        "runtime_evidence_status",
        "actual_runtime_evidence_present",
        "long_run_evidence_present",
        "actual_runtime_window_seconds",
        "minimum_runtime_window_seconds",
        "stub_cycle_count",
        "minimum_actual_cycle_count",
        "stub_cycles_do_not_count_as_long_run",
        "minimum_evidence_window_met",
        "minimum_cycle_count_met",
        "dashboard_display_truth_only",
        "dashboard_visibility_status",
        "optimizer_input_role",
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
        "blocker_report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ShadowObservationActualRuntimeBlockerValidationResult("FAIL", f"actual runtime blocker report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != SHADOW_OBSERVATION_ACTUAL_RUNTIME_BLOCKER_SCHEMA_ID:
        return ShadowObservationActualRuntimeBlockerValidationResult("FAIL", "actual runtime blocker schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("blocker_report_hash") != shadow_observation_actual_runtime_blocker_hash(report):
        return ShadowObservationActualRuntimeBlockerValidationResult("FAIL", "actual runtime blocker hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "actual runtime blocker must remain UPBIT/KRW_SPOT for MVP-4", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_mode") != "PAPER" or report.get("mode") != "SHADOW":
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "actual runtime blocker must bind PAPER source to SHADOW output", "SNAPSHOT_SCOPE_MISMATCH")
    source_is_stub = report.get("runtime_execution_mode") == "BOUNDED_SHADOW_STUB" and report.get("runtime_evidence_role") == "PERSISTENT_RUNTIME_STUB_ONLY"
    source_is_short_window = (
        report.get("runtime_execution_mode") == "ACTUAL_PAPER_SHADOW_SHORT_WINDOW"
        and report.get("runtime_evidence_role") == "PERSISTENT_RUNTIME_SHORT_WINDOW_ONLY"
    )
    if not (source_is_stub or source_is_short_window):
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "actual runtime blocker can only describe stub-only or short-window non-live source runtime", "LIVE_FINAL_GUARD_FAILED")

    if runtime_report is not None:
        source_result = validate_shadow_observation_persistent_runtime_report(runtime_report)
        source_hash = shadow_observation_persistent_runtime_hash(runtime_report)
        if report.get("source_runtime_report_hash") != source_hash or report.get("source_runtime_hash_verified") is not True:
            return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "source runtime hash is not verified", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("source_runtime_validation_status") != source_result.status:
            return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "source runtime validation status drifted", source_result.blocker_code or "DATA_QUALITY_INSUFFICIENT")
        if source_result.status != "PASS":
            return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "source runtime is not a valid stub-only report", source_result.blocker_code or "DATA_QUALITY_INSUFFICIENT")
    else:
        if report.get("source_runtime_hash_verified") is not True:
            return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "source runtime hash must be verified even when source report is not loaded", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("source_runtime_validation_status") != "PASS":
            return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "source runtime validation must be PASS before blocker report can be display-trusted", "DATA_QUALITY_INSUFFICIENT")

    if report.get("runtime_evidence_status") != "BLOCKED":
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "actual runtime blocker must remain BLOCKED until real non-live evidence exists", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if int(report.get("minimum_runtime_window_seconds", 0)) < MINIMUM_LONG_RUN_RUNTIME_WINDOW_SECONDS:
        return ShadowObservationActualRuntimeBlockerValidationResult(
            "BLOCKED",
            "actual runtime blocker minimum runtime window is below the MVP-4 long-run evidence floor",
            "MEASUREMENT_MISSING",
        )
    if int(report.get("minimum_actual_cycle_count", 0)) < MINIMUM_LONG_RUN_ACTUAL_CYCLE_COUNT:
        return ShadowObservationActualRuntimeBlockerValidationResult(
            "BLOCKED",
            "actual runtime blocker minimum cycle count is below the MVP-4 long-run evidence floor",
            "MEASUREMENT_MISSING",
        )
    if report.get("long_run_evidence_present") is not False:
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "blocker report cannot claim long-run evidence", "LIVE_FINAL_GUARD_FAILED")
    actual_window_seconds = int(report.get("actual_runtime_window_seconds") or 0)
    if source_is_stub:
        if report.get("actual_runtime_evidence_present") is not False:
            return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "stub-only source cannot claim actual runtime evidence", "LIVE_FINAL_GUARD_FAILED")
        if actual_window_seconds != 0:
            return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "stub-only source cannot report actual runtime window seconds", "MEASUREMENT_MISSING")
    if source_is_short_window:
        if report.get("actual_runtime_evidence_present") is not True:
            return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "short-window source must disclose non-live actual runtime evidence presence", "MEASUREMENT_MISSING")
        if actual_window_seconds < 0 or actual_window_seconds >= int(report.get("minimum_runtime_window_seconds", 0)):
            return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "short-window runtime window cannot satisfy long-run threshold", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if report.get("stub_cycles_do_not_count_as_long_run") is not True:
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "stub cycles must not count as long-run evidence", "MEASUREMENT_MISSING")
    if report.get("minimum_evidence_window_met") is not False or report.get("minimum_cycle_count_met") is not False:
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "stub-only source cannot satisfy actual evidence thresholds", "LIVE_FINAL_GUARD_FAILED")
    if report.get("dashboard_display_truth_only") is not True or report.get("dashboard_visibility_status") != "VISIBLE_AS_BLOCKED":
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "dashboard must show actual runtime evidence as blocked display truth only", "MEASUREMENT_MISSING")
    if report.get("optimizer_input_role") != "BLOCKER_ONLY_NOT_RANKING_INPUT":
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "actual runtime blocker cannot become optimizer ranking input", "OPTIMIZER_DIRECT_LIVE_FORBIDDEN")
    if any(report.get(field) for field in ("promotion_eligible", "live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called")):
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "actual runtime blocker attempted promotion, live, order, or scale-up state", "LIVE_FINAL_GUARD_FAILED")

    blockers = report.get("blockers") or []
    if not blockers or report.get("primary_blocker_code") != blockers[0].get("code"):
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "actual runtime blocker must carry explicit primary blocker", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if not any(blocker.get("code") == "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING" for blocker in blockers):
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "actual runtime execution missing blocker is absent", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

    combined_operator_text = f"{report.get('operator_message', '')} {report.get('next_operator_action', '')}".lower()
    if "not actual long-run evidence" not in combined_operator_text or "live" not in combined_operator_text or "blocked" not in combined_operator_text:
        return ShadowObservationActualRuntimeBlockerValidationResult("BLOCKED", "operator text must state stub is not actual long-run evidence and live remains blocked", "MEASUREMENT_MISSING")
    return ShadowObservationActualRuntimeBlockerValidationResult(
        "PASS",
        "actual SHADOW runtime execution remains explicitly blocked until real long-run non-live evidence exists",
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
