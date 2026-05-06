from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from trader1.research.shadow.shadow_observation import build_shadow_observation_report
from trader1.research.shadow.shadow_observation_actual_runtime_blocker import (
    build_shadow_observation_actual_runtime_blocker_report,
    shadow_observation_actual_runtime_blocker_hash,
    validate_shadow_observation_actual_runtime_blocker_report,
)
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    build_shadow_observation_persistent_runtime_report,
    shadow_observation_persistent_runtime_hash,
    validate_shadow_observation_persistent_runtime_report,
)
from trader1.research.shadow.shadow_observation_scheduler import build_shadow_observation_scheduler_guard_report
from trader1.research.shadow.shadow_observation_stream import build_shadow_observation_stream_report
from trader1.research.shadow.shadow_runner import AGENTS_SHA256, TRADER1_SHA256, utc_now
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle


SHADOW_OBSERVATION_ACTUAL_RUNTIME_HARNESS_SCHEMA_ID = "trader1.shadow_observation_actual_runtime_harness_report.v1"
ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_CYCLES = 20
ACTUAL_RUNTIME_HARNESS_MAX_OBSERVATIONS_PER_CYCLE = 20
ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_SECONDS = 300
ACTUAL_RUNTIME_HARNESS_MAX_OBSERVATION_COUNT = (
    ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_CYCLES * ACTUAL_RUNTIME_HARNESS_MAX_OBSERVATIONS_PER_CYCLE
)
MINIMUM_LONG_RUN_RUNTIME_WINDOW_SECONDS = 86400
MINIMUM_LONG_RUN_ACTUAL_CYCLE_COUNT = 2880


@dataclass(frozen=True)
class ShadowObservationActualRuntimeHarnessValidationResult:
    status: str
    message: str
    blocker_code: str | None


def shadow_observation_actual_runtime_harness_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("harness_report_hash", None)
    return _sha256_payload(payload)


def build_shadow_observation_actual_runtime_harness_report(
    *,
    harness_id: str,
    requested_cycle_count: int = 3,
    completed_cycle_count: int | None = None,
    observations_per_cycle: int = 3,
    measured_runtime_seconds: int = 0,
    runtime_measurement_source: str = "CALLER_SUPPLIED_UNVERIFIED",
    monotonic_timer_started: bool = False,
    monotonic_timer_stopped: bool = False,
    measured_runtime_seconds_verified: bool = False,
    minimum_runtime_window_seconds: int = 86400,
    minimum_actual_cycle_count: int = 2880,
    heartbeat_count: int | None = None,
    partial_write_detected: bool = False,
    duplicate_writer_detected: bool = False,
    credential_access_attempted: bool = False,
    exchange_account_call_attempted: bool = False,
    live_order_api_attempted: bool = False,
    order_adapter_called: bool = False,
    optimizer_ranking_input_attempted: bool = False,
    scale_up_requested: bool = False,
    source_runtime_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    requested = int(requested_cycle_count)
    completed = int(completed_cycle_count if completed_cycle_count is not None else requested)
    observations_each = int(observations_per_cycle)
    heartbeat_total = int(heartbeat_count if heartbeat_count is not None else max(0, completed))

    if source_runtime_report is None:
        scheduler_guard_report = _build_scheduler_guard_report(
            harness_id=harness_id,
            requested_cycle_count=max(1, min(max(requested, 1), ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_CYCLES)),
            observations_per_cycle=max(1, min(max(observations_each, 1), ACTUAL_RUNTIME_HARNESS_MAX_OBSERVATIONS_PER_CYCLE)),
        )
        runtime_report = build_shadow_observation_persistent_runtime_report(
            runtime_id=f"{harness_id}_persistent_runtime",
            scheduler_guard_report=scheduler_guard_report,
            requested_cycle_count=max(1, requested),
            completed_cycle_count=max(0, completed),
            max_cycle_count=max(1, max(requested, completed, 20)),
            heartbeat_interval_seconds=30,
            max_runtime_seconds=max(300, int(measured_runtime_seconds)),
            atomic_commit_count=max(0, completed),
            partial_temp_artifact_count=1 if partial_write_detected else 0,
            graceful_shutdown=not partial_write_detected,
            order_adapter_called=order_adapter_called,
        )
    else:
        runtime_report = dict(source_runtime_report)
    data_source_role = (
        "UPBIT_PAPER_RUNTIME_LOOP_NO_CREDENTIALS"
        if runtime_report.get("runtime_execution_mode") == "ACTUAL_PAPER_SHADOW_SHORT_WINDOW"
        else "DETERMINISTIC_PAPER_FIXTURE_NO_CREDENTIALS"
    )
    blocker_report = build_shadow_observation_actual_runtime_blocker_report(
        blocker_report_id=f"{harness_id}_actual_runtime_blocker",
        runtime_report=runtime_report,
        minimum_runtime_window_seconds=minimum_runtime_window_seconds,
        minimum_actual_cycle_count=minimum_actual_cycle_count,
    )

    runtime_result = validate_shadow_observation_persistent_runtime_report(runtime_report)
    blocker_result = validate_shadow_observation_actual_runtime_blocker_report(blocker_report, runtime_report=runtime_report)
    runtime_hash = str(runtime_report.get("runtime_report_hash") or "")
    blocker_hash = str(blocker_report.get("blocker_report_hash") or "")
    runtime_hash_verified = runtime_hash == shadow_observation_persistent_runtime_hash(runtime_report)
    blocker_hash_verified = blocker_hash == shadow_observation_actual_runtime_blocker_hash(blocker_report)
    measurement_verified = (
        (
            runtime_measurement_source == "MONOTONIC_LOCAL_TIMER_VERIFIED"
            and bool(monotonic_timer_started)
            and bool(monotonic_timer_stopped)
        )
        or runtime_measurement_source == "PAPER_LOOP_TIMESTAMP_SPAN_VERIFIED"
    ) and (
        bool(measured_runtime_seconds_verified)
        and int(measured_runtime_seconds) >= 0
        and int(measured_runtime_seconds) <= ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_SECONDS
    )
    runtime_measurement_status = "VERIFIED_SHORT_WINDOW" if measurement_verified else "BLOCKED_UNVERIFIED_MEASUREMENT"

    operational_blockers: list[dict[str, str]] = []
    if requested <= 0 or completed <= 0 or observations_each <= 0:
        operational_blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "actual runtime harness cycle and observation counts must be positive"))
    if requested > ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_CYCLES or completed > ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_CYCLES:
        operational_blockers.append(_blocker("RESOURCE_LIMIT_BLOCK", "actual runtime harness cycle counts exceed bounded short-window capacity"))
    if heartbeat_total > ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_CYCLES:
        operational_blockers.append(_blocker("RESOURCE_LIMIT_BLOCK", "actual runtime harness heartbeat count exceeds bounded short-window capacity"))
    if observations_each > ACTUAL_RUNTIME_HARNESS_MAX_OBSERVATIONS_PER_CYCLE:
        operational_blockers.append(_blocker("RESOURCE_LIMIT_BLOCK", "actual runtime harness observations per cycle exceed bounded short-window capacity"))
    if max(0, completed) * max(0, observations_each) > ACTUAL_RUNTIME_HARNESS_MAX_OBSERVATION_COUNT:
        operational_blockers.append(_blocker("RESOURCE_LIMIT_BLOCK", "actual runtime harness observation count exceeds bounded short-window capacity"))
    if int(measured_runtime_seconds) < 0:
        operational_blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "actual runtime harness measured runtime cannot be negative"))
    if int(measured_runtime_seconds) > ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_SECONDS:
        operational_blockers.append(_blocker("RESOURCE_LIMIT_BLOCK", "actual runtime harness measured runtime exceeds short-window harness limit"))
    if not measurement_verified:
        operational_blockers.append(_blocker("MEASUREMENT_MISSING", "actual runtime harness measured runtime lacks verified monotonic timer source"))
    if int(measured_runtime_seconds) >= int(minimum_runtime_window_seconds) or completed >= int(minimum_actual_cycle_count):
        operational_blockers.append(
            _blocker(
                "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
                "short-window harness cannot be parameterized to satisfy long-run runtime or cycle thresholds",
            )
        )
    if completed != requested:
        operational_blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "actual runtime harness did not complete the requested non-live cycles"))
    if heartbeat_total < completed:
        operational_blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "actual runtime harness heartbeat count is below completed cycle count"))
    if partial_write_detected:
        operational_blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "actual runtime harness detected partial write recovery risk"))
    if duplicate_writer_detected:
        operational_blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "actual runtime harness detected duplicate writer risk"))
    if runtime_result.status != "PASS":
        operational_blockers.append(_blocker(runtime_result.blocker_code or "DATA_QUALITY_INSUFFICIENT", runtime_result.message))
    if blocker_result.status != "PASS":
        operational_blockers.append(_blocker(blocker_result.blocker_code or "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING", blocker_result.message))
    if not runtime_hash_verified or not blocker_hash_verified:
        operational_blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "actual runtime harness source report hash verification failed"))
    if credential_access_attempted or exchange_account_call_attempted or live_order_api_attempted or order_adapter_called:
        operational_blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "actual runtime harness attempted credential, account, live API, or order adapter use"))
    if optimizer_ranking_input_attempted:
        operational_blockers.append(_blocker("OPTIMIZER_DIRECT_LIVE_FORBIDDEN", "actual runtime harness attempted optimizer ranking input before long-run evidence"))
    if scale_up_requested:
        operational_blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "actual runtime harness attempted risk scale-up"))

    evidence_blockers = [
        _blocker(
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
            "Harness execution is short-window and non-live; it is not validated long-run PAPER/SHADOW runtime evidence.",
        ),
        _blocker(
            "MEASUREMENT_MISSING",
            "Minimum runtime window and actual cycle thresholds are not satisfied by this harness report.",
        ),
    ]
    blockers = _dedupe_blockers(operational_blockers + evidence_blockers)
    harness_status = "PASS" if not operational_blockers else "BLOCKED"

    report = {
        "schema_id": SHADOW_OBSERVATION_ACTUAL_RUNTIME_HARNESS_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": TRADER1_SHA256,
            "agents_sha256": AGENTS_SHA256,
        },
        "harness_id": harness_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "source_mode": "PAPER",
        "mode": "SHADOW",
        "session_id": harness_id,
        "harness_execution_mode": "NON_LIVE_LOCAL_PAPER_SHADOW_HARNESS",
        "data_source_role": data_source_role,
        "runtime_artifact_path": f"system/runtime/upbit/krw_spot/shadow/{harness_id}/actual_runtime_harness_report.json",
        "source_runtime_id": str(runtime_report.get("runtime_id") or ""),
        "source_runtime_report_hash": runtime_hash,
        "source_runtime_hash_verified": runtime_hash_verified,
        "source_runtime_validation_status": runtime_result.status,
        "source_actual_blocker_report_hash": blocker_hash,
        "source_actual_blocker_hash_verified": blocker_hash_verified,
        "source_actual_blocker_validation_status": blocker_result.status,
        "requested_cycle_count": requested,
        "completed_cycle_count": completed,
        "observations_per_cycle": observations_each,
        "observation_count": max(0, completed) * max(0, observations_each),
        "heartbeat_count": heartbeat_total,
        "measured_runtime_seconds": int(measured_runtime_seconds),
        "runtime_measurement_source": str(runtime_measurement_source),
        "monotonic_timer_started": bool(monotonic_timer_started),
        "monotonic_timer_stopped": bool(monotonic_timer_stopped),
        "measured_runtime_seconds_verified": bool(measured_runtime_seconds_verified),
        "runtime_measurement_status": runtime_measurement_status,
        "minimum_runtime_window_seconds": int(minimum_runtime_window_seconds),
        "minimum_actual_cycle_count": int(minimum_actual_cycle_count),
        "minimum_evidence_window_met": False,
        "minimum_cycle_count_met": False,
        "actual_non_live_runtime_harness_executed": harness_status == "PASS",
        "runtime_evidence_status": "BLOCKED_LONG_RUN_EVIDENCE_MISSING",
        "runtime_evidence_role": "EXECUTION_HARNESS_PROOF_ONLY_NOT_LONG_RUN",
        "long_run_evidence_present": False,
        "long_run_evidence_eligible": False,
        "dashboard_display_truth_only": True,
        "dashboard_visibility_status": "VISIBLE_AS_SHORT_WINDOW_BLOCKED",
        "optimizer_input_role": "BLOCKER_ONLY_NOT_RANKING_INPUT",
        "promotion_eligible": False,
        "credential_access_attempted": bool(credential_access_attempted),
        "exchange_account_call_attempted": bool(exchange_account_call_attempted),
        "live_order_api_attempted": bool(live_order_api_attempted),
        "order_adapter_called": bool(order_adapter_called),
        "optimizer_ranking_input_attempted": bool(optimizer_ranking_input_attempted),
        "scale_up_requested": bool(scale_up_requested),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "harness_status": harness_status,
        "primary_blocker_code": blockers[0]["code"],
        "blockers": blockers,
        "operator_message": (
            "Non-live PAPER/SHADOW harness execution is working as a short-window operational check. "
            "It is not long-run evidence, not LIVE_READY evidence, and live orders remain blocked."
        ),
        "next_operator_action": (
            "Use this harness for safe monitoring readiness, then run a real non-live long-window PAPER/SHADOW session "
            "with validated duration, cycle, heartbeat, and recovery evidence before any live review."
        ),
        "harness_report_hash": "",
    }
    report["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(report)
    return report


def validate_shadow_observation_actual_runtime_harness_report(
    report: dict[str, Any],
) -> ShadowObservationActualRuntimeHarnessValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "authority",
        "harness_id",
        "exchange",
        "market_type",
        "source_mode",
        "mode",
        "session_id",
        "harness_execution_mode",
        "data_source_role",
        "runtime_artifact_path",
        "source_runtime_id",
        "source_runtime_report_hash",
        "source_runtime_hash_verified",
        "source_runtime_validation_status",
        "source_actual_blocker_report_hash",
        "source_actual_blocker_hash_verified",
        "source_actual_blocker_validation_status",
        "requested_cycle_count",
        "completed_cycle_count",
        "observations_per_cycle",
        "observation_count",
        "heartbeat_count",
        "measured_runtime_seconds",
        "runtime_measurement_source",
        "monotonic_timer_started",
        "monotonic_timer_stopped",
        "measured_runtime_seconds_verified",
        "runtime_measurement_status",
        "minimum_runtime_window_seconds",
        "minimum_actual_cycle_count",
        "minimum_evidence_window_met",
        "minimum_cycle_count_met",
        "actual_non_live_runtime_harness_executed",
        "runtime_evidence_status",
        "runtime_evidence_role",
        "long_run_evidence_present",
        "long_run_evidence_eligible",
        "dashboard_display_truth_only",
        "dashboard_visibility_status",
        "optimizer_input_role",
        "promotion_eligible",
        "credential_access_attempted",
        "exchange_account_call_attempted",
        "live_order_api_attempted",
        "order_adapter_called",
        "optimizer_ranking_input_attempted",
        "scale_up_requested",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "harness_status",
        "primary_blocker_code",
        "blockers",
        "operator_message",
        "next_operator_action",
        "harness_report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ShadowObservationActualRuntimeHarnessValidationResult("FAIL", f"actual runtime harness report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != SHADOW_OBSERVATION_ACTUAL_RUNTIME_HARNESS_SCHEMA_ID:
        return ShadowObservationActualRuntimeHarnessValidationResult("FAIL", "actual runtime harness schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("harness_report_hash") != shadow_observation_actual_runtime_harness_hash(report):
        return ShadowObservationActualRuntimeHarnessValidationResult("FAIL", "actual runtime harness hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness must remain UPBIT/KRW_SPOT for MVP-4", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_mode") != "PAPER" or report.get("mode") != "SHADOW":
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness must bind PAPER source to SHADOW output", "SNAPSHOT_SCOPE_MISMATCH")
    if "/shadow/" not in str(report.get("runtime_artifact_path") or ""):
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness path lacks shadow namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("harness_execution_mode") != "NON_LIVE_LOCAL_PAPER_SHADOW_HARNESS":
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness execution mode is unsafe or unknown", "LIVE_FINAL_GUARD_FAILED")
    if report.get("data_source_role") not in {
        "DETERMINISTIC_PAPER_FIXTURE_NO_CREDENTIALS",
        "UPBIT_PAPER_RUNTIME_LOOP_NO_CREDENTIALS",
    }:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness cannot use credentialed or live account data", "API_UNVERIFIED")
    if report.get("source_runtime_hash_verified") is not True or report.get("source_actual_blocker_hash_verified") is not True:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness source hashes are not verified", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_runtime_report_hash") == "0" * 64 or report.get("source_actual_blocker_report_hash") == "0" * 64:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness source hash is a placeholder", "SCHEMA_IDENTITY_MISMATCH")
    expected_harness_executed = report.get("harness_status") == "PASS"
    if report.get("actual_non_live_runtime_harness_executed") is not expected_harness_executed:
        return ShadowObservationActualRuntimeHarnessValidationResult(
            "BLOCKED",
            "actual runtime harness execution summary does not match harness status",
            "MEASUREMENT_MISSING",
        )
    if int(report.get("requested_cycle_count", 0)) <= 0 or int(report.get("completed_cycle_count", 0)) <= 0:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness cycle counts must be positive", "DATA_QUALITY_INSUFFICIENT")
    if (
        int(report.get("requested_cycle_count", 0)) > ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_CYCLES
        or int(report.get("completed_cycle_count", 0)) > ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_CYCLES
        or int(report.get("heartbeat_count", 0)) > ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_CYCLES
    ):
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness cycle or heartbeat count exceeds short-window capacity", "RESOURCE_LIMIT_BLOCK")
    if int(report.get("observations_per_cycle", 0)) > ACTUAL_RUNTIME_HARNESS_MAX_OBSERVATIONS_PER_CYCLE:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness observations per cycle exceeds short-window capacity", "RESOURCE_LIMIT_BLOCK")
    if int(report.get("observation_count", 0)) > ACTUAL_RUNTIME_HARNESS_MAX_OBSERVATION_COUNT:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness observation count exceeds short-window capacity", "RESOURCE_LIMIT_BLOCK")
    if int(report.get("measured_runtime_seconds", 0)) < 0:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness measured runtime cannot be negative", "DATA_QUALITY_INSUFFICIENT")
    if int(report.get("measured_runtime_seconds", 0)) > ACTUAL_RUNTIME_HARNESS_MAX_SHORT_WINDOW_SECONDS:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness measured runtime exceeds short-window capacity", "RESOURCE_LIMIT_BLOCK")
    expected_measurement_status = (
        "VERIFIED_SHORT_WINDOW"
        if (
            (
                report.get("runtime_measurement_source") == "MONOTONIC_LOCAL_TIMER_VERIFIED"
                and report.get("monotonic_timer_started") is True
                and report.get("monotonic_timer_stopped") is True
            )
            or report.get("runtime_measurement_source") == "PAPER_LOOP_TIMESTAMP_SPAN_VERIFIED"
        )
        and report.get("measured_runtime_seconds_verified") is True
        else "BLOCKED_UNVERIFIED_MEASUREMENT"
    )
    if report.get("runtime_measurement_status") != expected_measurement_status:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness measurement summary drift", "MEASUREMENT_MISSING")
    if report.get("runtime_measurement_status") != "VERIFIED_SHORT_WINDOW":
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness measured runtime lacks verified monotonic timer source", "MEASUREMENT_MISSING")
    if int(report.get("minimum_runtime_window_seconds", 0)) < MINIMUM_LONG_RUN_RUNTIME_WINDOW_SECONDS:
        return ShadowObservationActualRuntimeHarnessValidationResult(
            "BLOCKED",
            "actual runtime harness minimum runtime window is below the MVP-4 long-run evidence floor",
            "MEASUREMENT_MISSING",
        )
    if int(report.get("minimum_actual_cycle_count", 0)) < MINIMUM_LONG_RUN_ACTUAL_CYCLE_COUNT:
        return ShadowObservationActualRuntimeHarnessValidationResult(
            "BLOCKED",
            "actual runtime harness minimum cycle count is below the MVP-4 long-run evidence floor",
            "MEASUREMENT_MISSING",
        )
    if int(report.get("measured_runtime_seconds", 0)) >= int(report.get("minimum_runtime_window_seconds", 1)) or int(
        report.get("completed_cycle_count", 0)
    ) >= int(report.get("minimum_actual_cycle_count", 1)):
        return ShadowObservationActualRuntimeHarnessValidationResult(
            "BLOCKED",
            "short-window harness cannot satisfy long-run runtime or cycle thresholds by parameter changes",
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        )
    if report.get("completed_cycle_count") != report.get("requested_cycle_count"):
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness completed cycle count does not match requested count", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if int(report.get("heartbeat_count", 0)) < int(report.get("completed_cycle_count", 0)):
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness heartbeat count is insufficient", "DATA_QUALITY_INSUFFICIENT")
    if report.get("observation_count") != int(report.get("completed_cycle_count", 0)) * int(report.get("observations_per_cycle", 0)):
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness observation count is inconsistent", "DATA_QUALITY_INSUFFICIENT")
    if report.get("source_runtime_validation_status") != "PASS" or report.get("source_actual_blocker_validation_status") != "PASS":
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness source reports are not validated", "DATA_QUALITY_INSUFFICIENT")
    if report.get("minimum_evidence_window_met") is not False or report.get("minimum_cycle_count_met") is not False:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "short-window harness cannot claim minimum long-run thresholds", "LIVE_FINAL_GUARD_FAILED")
    if report.get("long_run_evidence_present") is not False or report.get("long_run_evidence_eligible") is not False:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness cannot claim long-run evidence", "LIVE_FINAL_GUARD_FAILED")
    if report.get("runtime_evidence_status") != "BLOCKED_LONG_RUN_EVIDENCE_MISSING":
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness must leave long-run evidence blocked", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if report.get("runtime_evidence_role") != "EXECUTION_HARNESS_PROOF_ONLY_NOT_LONG_RUN":
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness evidence role is unsafe", "LIVE_FINAL_GUARD_FAILED")
    if report.get("dashboard_display_truth_only") is not True or report.get("dashboard_visibility_status") != "VISIBLE_AS_SHORT_WINDOW_BLOCKED":
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "dashboard must show harness as display-only short-window blocked status", "MEASUREMENT_MISSING")
    if report.get("optimizer_input_role") != "BLOCKER_ONLY_NOT_RANKING_INPUT":
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness cannot become optimizer ranking input", "OPTIMIZER_DIRECT_LIVE_FORBIDDEN")
    forbidden_true = (
        "promotion_eligible",
        "credential_access_attempted",
        "exchange_account_call_attempted",
        "live_order_api_attempted",
        "order_adapter_called",
        "optimizer_ranking_input_attempted",
        "scale_up_requested",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden_true):
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness attempted live, credential, optimizer, or scale-up state", "LIVE_FINAL_GUARD_FAILED")
    blockers = report.get("blockers") or []
    if not blockers or report.get("primary_blocker_code") != blockers[0].get("code"):
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness must expose a primary blocker", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if not any(blocker.get("code") == "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING" for blocker in blockers):
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness must preserve actual runtime missing blocker", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    text = f"{report.get('operator_message', '')} {report.get('next_operator_action', '')}".lower()
    if "not long-run evidence" not in text or "live orders remain blocked" not in text:
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "operator text must prevent long-run and live readiness misunderstanding", "MEASUREMENT_MISSING")
    if report.get("harness_status") != "PASS":
        return ShadowObservationActualRuntimeHarnessValidationResult("BLOCKED", "actual runtime harness report is operationally blocked", blockers[0].get("code", "UNKNOWN_BLOCKED"))
    return ShadowObservationActualRuntimeHarnessValidationResult(
        "PASS",
        "non-live PAPER/SHADOW harness runs short-window checks while long-run and live evidence remain blocked",
        None,
    )


def _build_scheduler_guard_report(*, harness_id: str, requested_cycle_count: int, observations_per_cycle: int) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    total_observations = max(1, requested_cycle_count * observations_per_cycle)
    for index in range(total_observations):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id=f"{harness_id}_paper_gate",
            session_id=f"{harness_id}_paper_{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"{harness_id}_observation_{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"{harness_id}_shadow_{index}",
                shadow_sample_count=30,
            )
        )
    stream = build_shadow_observation_stream_report(
        stream_id=f"{harness_id}_stream",
        observations=observations,
        min_required_observation_count=max(1, min(3, total_observations)),
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    return build_shadow_observation_scheduler_guard_report(
        scheduler_id=f"{harness_id}_scheduler",
        stream_report=stream,
        writer_id=f"{harness_id}_writer",
        active_writer_id=f"{harness_id}_writer",
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
