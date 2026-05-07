from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.research.shadow.shadow_observation import build_shadow_observation_report
from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    build_shadow_observation_actual_runtime_harness_report,
)
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    build_shadow_observation_persistent_runtime_report,
    build_shadow_observation_persistent_runtime_report_from_paper_loop,
)
from trader1.research.shadow.shadow_observation_runtime_orchestration import (
    build_shadow_observation_runtime_orchestration_report,
    validate_shadow_observation_runtime_orchestration_report,
)
from trader1.research.shadow.shadow_observation_scheduler import build_shadow_observation_scheduler_guard_report
from trader1.research.shadow.shadow_observation_stream import build_shadow_observation_stream_report
from trader1.runtime.ledger.paper_ledger_rollup import build_paper_ledger_rollup_report, write_paper_ledger_rollup_report
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle
from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    build_upbit_paper_ledger_idempotency_runtime_evidence_report,
    validate_upbit_paper_ledger_idempotency_runtime_evidence_report,
    write_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    LONG_RUN_EVIDENCE_BLOCKER_CODE,
    run_upbit_paper_persistent_loop,
    validate_upbit_paper_persistent_loop_report,
    validate_upbit_paper_runtime_recovery_guard_report,
)
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    build_upbit_paper_runtime_sample_history,
    validate_upbit_paper_runtime_sample_history,
    write_upbit_paper_runtime_sample_history,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


REPORT_SCHEMA_ID = "trader1.upbit_paper_runtime_evidence_collection_profile_report.v1"
PROFILE_ID = "UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE_V1"
PROFILE_SCOPE = "UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE_ONLY_NO_LIVE"
LONG_RUN_COLLECTION_DEPTH_STATUS = "BLOCKED_FOR_LONG_RUN_COLLECTION_DEPTH"
LONG_RUN_COLLECTION_DEPTH_ROLE = "PAPER_RUNTIME_COLLECTION_DEPTH_BLOCKER_NOT_LONG_RUN_EVIDENCE"
RUNTIME_MODE_DEPTH_STATUS = "BLOCKED_FOR_PER_MODE_LONG_RUN_DEPTH"
RUNTIME_MODE_DEPTH_BLOCKER_CODE = "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING"
DEFAULT_REPORT_PATH = Path(
    "system/evidence/runtime_checks/MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.report.json"
)
DEFAULT_SESSION_ID = "mvp1_upbit_paper_launcher"
MAX_SAFE_PROFILE_BATCH_CYCLE_COUNT = 20
COLLECTION_PLAN_ROLE = "NON_LIVE_RUNTIME_COLLECTION_CONTINUATION_PLAN"
COLLECTION_PLAN_READY_STATUS = "READY_TO_CONTINUE_NON_LIVE_COLLECTION"
COLLECTION_PLAN_BLOCKED_STATUS = "BLOCKED_FOR_RECONCILIATION"
SHADOW_RUNTIME_ORCHESTRATION_REPORT_NAME = "runtime_orchestration_report.json"
SHADOW_ACTUAL_RUNTIME_HARNESS_REPORT_NAME = "actual_runtime_harness_report.json"
SHADOW_PERSISTENT_RUNTIME_REPORT_NAME = "shadow_observation_persistent_runtime_report.json"
SHADOW_RUNTIME_SAMPLE_HISTORY_NAME = "shadow_runtime_sample_history.json"
SHADOW_RUNTIME_SAMPLE_HISTORY_SCHEMA_ID = "trader1.shadow_runtime_sample_history.v1"
SHADOW_RUNTIME_SAMPLE_HISTORY_ROLE = "SHADOW_SHORT_WINDOW_RUNTIME_SAMPLE_HISTORY_NOT_LONG_RUN"


@dataclass(frozen=True)
class ProfileValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def write_text(path: Path, value: str) -> None:
    _atomic_write_text(path, value)


def upbit_paper_runtime_evidence_collection_profile_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("profile_hash", None)
    return _sha256_json(payload)


def _component(
    *,
    component_id: str,
    status: str,
    blocker_code: str | None,
    message: str,
    evidence_hash: str | None = None,
) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "status": status,
        "blocker_code": blocker_code,
        "message": message,
        "evidence_hash": evidence_hash,
    }


def _long_run_collection_depth(
    *,
    sample_history: dict[str, Any],
    idempotency_evidence: dict[str, Any],
    shadow_orchestration: dict[str, Any] | None = None,
    shadow_orchestration_result: Any | None = None,
    shadow_runtime_history: dict[str, Any] | None = None,
    shadow_runtime_history_result: Any | None = None,
) -> dict[str, Any]:
    observed_span_seconds = int(sample_history.get("observed_span_seconds") or 0)
    minimum_span_seconds = int(sample_history.get("min_actual_long_run_span_seconds") or 0)
    observed_cycle_count = int(sample_history.get("accepted_cycle_sample_count") or 0)
    minimum_cycle_count = int(sample_history.get("min_actual_long_run_cycle_count") or 0)
    missing_span_seconds = max(0, minimum_span_seconds - observed_span_seconds)
    missing_cycle_count = max(0, minimum_cycle_count - observed_cycle_count)
    observed_modes = ["PAPER"] if observed_cycle_count > 0 else []
    required_modes = ["PAPER", "SHADOW"]
    shadow_orchestration_present = (
        isinstance(shadow_orchestration, dict)
        and getattr(shadow_orchestration_result, "status", None) == "PASS"
        and shadow_orchestration.get("source_validation_status") == "PASS"
        and shadow_orchestration.get("source_runtime_hash_pairing_verified") is True
        and shadow_orchestration.get("runtime_evidence_role") == "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN"
        and shadow_orchestration.get("actual_long_run_runtime_present") is False
        and shadow_orchestration.get("long_run_evidence_eligible") is False
    )
    shadow_history_present = (
        isinstance(shadow_runtime_history, dict)
        and getattr(shadow_runtime_history_result, "status", None) == "PASS"
        and shadow_runtime_history.get("history_status") == "COLLECTING"
        and int(shadow_runtime_history.get("accepted_cycle_sample_count") or 0) > 0
        and shadow_runtime_history.get("long_run_evidence_eligible") is False
        and shadow_runtime_history.get("actual_long_run_evidence_created") is False
        and shadow_runtime_history.get("promotion_eligible") is False
    )
    shadow_source_present = shadow_orchestration_present or shadow_history_present
    shadow_source_blocked = (
        (isinstance(shadow_orchestration, dict) and not shadow_orchestration_present)
        or (shadow_runtime_history_result is not None and getattr(shadow_runtime_history_result, "status", None) != "PASS")
    )
    if shadow_source_present:
        observed_modes.append("SHADOW")
    missing_modes = [mode for mode in required_modes if mode not in observed_modes]
    if shadow_source_present and "SHADOW" not in missing_modes:
        missing_modes.append("SHADOW")
    span_floor_met = observed_span_seconds >= minimum_span_seconds > 0
    cycle_floor_met = observed_cycle_count >= minimum_cycle_count > 0
    paper_depth_status = "PASS" if observed_cycle_count > 0 and idempotency_evidence.get("runtime_evidence_status") == "PASS" else "MISSING"
    shadow_depth_status = "PRESENT_NOT_LONG_RUN" if shadow_source_present else ("BLOCKED" if shadow_source_blocked else "MISSING")
    paper_shadow_pairing_status = (
        "PAIRED_NOT_LONG_RUN"
        if paper_depth_status == "PASS" and shadow_source_present
        else ("BLOCKED" if shadow_source_blocked else "MISSING")
    )
    orchestration_shadow_span_seconds = (
        int(shadow_orchestration.get("observed_actual_runtime_seconds") or 0)
        if shadow_orchestration_present and isinstance(shadow_orchestration, dict)
        else 0
    )
    orchestration_shadow_cycle_count = (
        int(shadow_orchestration.get("observed_actual_cycle_count") or 0)
        if shadow_orchestration_present and isinstance(shadow_orchestration, dict)
        else 0
    )
    history_shadow_span_seconds = int(shadow_runtime_history.get("observed_span_seconds") or 0) if shadow_history_present else 0
    history_shadow_cycle_count = int(shadow_runtime_history.get("accepted_cycle_sample_count") or 0) if shadow_history_present else 0
    shadow_observed_span_seconds = max(orchestration_shadow_span_seconds, history_shadow_span_seconds)
    shadow_observed_cycle_count = max(orchestration_shadow_cycle_count, history_shadow_cycle_count)
    runtime_mode_depth_evidence = _runtime_mode_depth_evidence(
        paper_observed_span_seconds=observed_span_seconds,
        paper_observed_cycle_count=observed_cycle_count,
        paper_source_status="PRESENT_BOUNDED_NOT_LONG_RUN" if paper_depth_status == "PASS" else "MISSING",
        shadow_observed_span_seconds=shadow_observed_span_seconds,
        shadow_observed_cycle_count=shadow_observed_cycle_count,
        shadow_source_status=(
            "PRESENT_BLOCKER_ONLY_NOT_LONG_RUN"
            if shadow_source_present
            else ("BLOCKED" if shadow_source_blocked else "MISSING")
        ),
        minimum_span_seconds=minimum_span_seconds,
        minimum_cycle_count=minimum_cycle_count,
    )

    return {
        "status": LONG_RUN_COLLECTION_DEPTH_STATUS,
        "depth_role": LONG_RUN_COLLECTION_DEPTH_ROLE,
        "blocker_code": LONG_RUN_EVIDENCE_BLOCKER_CODE,
        "required_runtime_modes": required_modes,
        "observed_runtime_modes": observed_modes,
        "missing_runtime_modes": missing_modes,
        "observed_span_seconds": observed_span_seconds,
        "minimum_span_seconds": minimum_span_seconds,
        "missing_span_seconds": missing_span_seconds,
        "span_floor_met": span_floor_met,
        "observed_cycle_count": observed_cycle_count,
        "minimum_cycle_count": minimum_cycle_count,
        "missing_cycle_count": missing_cycle_count,
        "cycle_floor_met": cycle_floor_met,
        "paper_runtime_depth_status": paper_depth_status,
        "paper_ledger_idempotency_status": str(idempotency_evidence.get("idempotency_status") or "BLOCKED"),
        "shadow_runtime_depth_status": shadow_depth_status,
        "paper_shadow_pairing_status": paper_shadow_pairing_status,
        "runtime_mode_depth_evidence": runtime_mode_depth_evidence,
        "bounded_profile_counts_as_long_run_evidence": False,
        "dashboard_display_counts_as_long_run_evidence": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _runtime_mode_depth(
    *,
    mode: str,
    source_status: str,
    evidence_role: str,
    observed_span_seconds: int,
    observed_cycle_count: int,
    minimum_span_seconds: int,
    minimum_cycle_count: int,
    blocker_code: str,
) -> dict[str, Any]:
    missing_span_seconds = max(0, int(minimum_span_seconds) - int(observed_span_seconds))
    missing_cycle_count = max(0, int(minimum_cycle_count) - int(observed_cycle_count))
    span_floor_met = int(observed_span_seconds) >= int(minimum_span_seconds) > 0
    cycle_floor_met = int(observed_cycle_count) >= int(minimum_cycle_count) > 0
    return {
        "mode": mode,
        "source_status": source_status,
        "evidence_role": evidence_role,
        "observed_span_seconds": int(observed_span_seconds),
        "minimum_span_seconds": int(minimum_span_seconds),
        "missing_span_seconds": missing_span_seconds,
        "span_floor_met": span_floor_met,
        "observed_cycle_count": int(observed_cycle_count),
        "minimum_cycle_count": int(minimum_cycle_count),
        "missing_cycle_count": missing_cycle_count,
        "cycle_floor_met": cycle_floor_met,
        "long_run_floor_met": span_floor_met and cycle_floor_met,
        "counts_as_actual_long_run_evidence": False,
        "blocker_code": blocker_code,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _runtime_mode_depth_evidence(
    *,
    paper_observed_span_seconds: int,
    paper_observed_cycle_count: int,
    paper_source_status: str,
    shadow_observed_span_seconds: int,
    shadow_observed_cycle_count: int,
    shadow_source_status: str,
    minimum_span_seconds: int,
    minimum_cycle_count: int,
) -> dict[str, Any]:
    mode_depths = {
        "paper": _runtime_mode_depth(
            mode="PAPER",
            source_status=paper_source_status,
            evidence_role="BOUNDED_PAPER_RUNTIME_PROFILE_NOT_LONG_RUN",
            observed_span_seconds=paper_observed_span_seconds,
            observed_cycle_count=paper_observed_cycle_count,
            minimum_span_seconds=minimum_span_seconds,
            minimum_cycle_count=minimum_cycle_count,
            blocker_code=LONG_RUN_EVIDENCE_BLOCKER_CODE,
        ),
        "shadow": _runtime_mode_depth(
            mode="SHADOW",
            source_status=shadow_source_status,
            evidence_role="ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN",
            observed_span_seconds=shadow_observed_span_seconds,
            observed_cycle_count=shadow_observed_cycle_count,
            minimum_span_seconds=minimum_span_seconds,
            minimum_cycle_count=minimum_cycle_count,
            blocker_code=RUNTIME_MODE_DEPTH_BLOCKER_CODE,
        ),
    }
    missing_modes = [
        depth["mode"]
        for depth in mode_depths.values()
        if depth["long_run_floor_met"] is not True or depth["counts_as_actual_long_run_evidence"] is not True
    ]
    return {
        "status": RUNTIME_MODE_DEPTH_STATUS,
        "blocker_code": RUNTIME_MODE_DEPTH_BLOCKER_CODE,
        "required_modes": ["PAPER", "SHADOW"],
        "mode_depths": mode_depths,
        "missing_long_run_modes": missing_modes,
        "missing_long_run_mode_count": len(missing_modes),
        "all_required_modes_long_run_validated": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _ceil_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    return (max(0, numerator) + denominator - 1) // denominator


def _non_live_collection_plan(*, collection_depth: dict[str, Any], profile_status: str) -> dict[str, Any]:
    mode_depth_evidence = collection_depth.get("runtime_mode_depth_evidence")
    if not isinstance(mode_depth_evidence, dict):
        mode_depth_evidence = {}
    mode_depths = mode_depth_evidence.get("mode_depths")
    if not isinstance(mode_depths, dict):
        mode_depths = {}
    paper_depth = mode_depths.get("paper") if isinstance(mode_depths.get("paper"), dict) else {}
    shadow_depth = mode_depths.get("shadow") if isinstance(mode_depths.get("shadow"), dict) else {}
    missing_modes = mode_depth_evidence.get("missing_long_run_modes")
    if not isinstance(missing_modes, list):
        missing_modes = ["PAPER", "SHADOW"]
    missing_modes = [str(mode) for mode in missing_modes if str(mode) in {"PAPER", "SHADOW"}]
    if "SHADOW" not in missing_modes:
        missing_modes.append("SHADOW")

    paper_remaining_span_seconds = int(paper_depth.get("missing_span_seconds") or collection_depth.get("missing_span_seconds") or 0)
    paper_remaining_cycle_count = int(paper_depth.get("missing_cycle_count") or collection_depth.get("missing_cycle_count") or 0)
    shadow_remaining_span_seconds = int(shadow_depth.get("missing_span_seconds") or 0)
    shadow_remaining_cycle_count = int(shadow_depth.get("missing_cycle_count") or 0)
    minimum_span_seconds = int(collection_depth.get("minimum_span_seconds") or 0)
    minimum_cycle_count = int(collection_depth.get("minimum_cycle_count") or 0)
    minimum_cycle_wall_clock_spacing_seconds = _ceil_div(minimum_span_seconds, minimum_cycle_count)
    plan_ready = profile_status == "PASS"
    recommended_paper_batch_cycle_count = (
        min(MAX_SAFE_PROFILE_BATCH_CYCLE_COUNT, paper_remaining_cycle_count)
        if plan_ready and paper_remaining_cycle_count > 0
        else 0
    )
    next_action = (
        "Continue non-live PAPER collection in bounded batches and collect real SHADOW runtime evidence; do not treat this profile as long-run or live readiness."
        if plan_ready
        else "Resolve PAPER runtime reconciliation or idempotency blockers before continuing non-live collection."
    )
    return {
        "plan_status": COLLECTION_PLAN_READY_STATUS if plan_ready else COLLECTION_PLAN_BLOCKED_STATUS,
        "plan_role": COLLECTION_PLAN_ROLE,
        "required_next_runtime_modes": missing_modes,
        "recommended_next_paper_batch_cycle_count": recommended_paper_batch_cycle_count,
        "max_safe_paper_batch_cycle_count": MAX_SAFE_PROFILE_BATCH_CYCLE_COUNT,
        "paper_remaining_span_seconds": paper_remaining_span_seconds,
        "paper_remaining_cycle_count": paper_remaining_cycle_count,
        "shadow_remaining_span_seconds": shadow_remaining_span_seconds,
        "shadow_remaining_cycle_count": shadow_remaining_cycle_count,
        "minimum_cycle_wall_clock_spacing_seconds": minimum_cycle_wall_clock_spacing_seconds,
        "estimated_wall_clock_seconds_remaining": max(paper_remaining_span_seconds, shadow_remaining_span_seconds),
        "shadow_collection_required": "SHADOW" in missing_modes,
        "counts_as_actual_long_run_evidence": False,
        "current_evidence_write_allowed": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "next_operator_action": next_action,
    }


def _shadow_runtime_session_root(*, root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system/runtime/upbit/krw_spot/shadow" / session_id


def _shadow_runtime_orchestration_report_path(*, root: Path, session_id: str) -> Path:
    return _shadow_runtime_session_root(root=root, session_id=session_id) / SHADOW_RUNTIME_ORCHESTRATION_REPORT_NAME


def _shadow_runtime_harness_report_path(*, root: Path, session_id: str) -> Path:
    return _shadow_runtime_session_root(root=root, session_id=session_id) / SHADOW_ACTUAL_RUNTIME_HARNESS_REPORT_NAME


def _shadow_persistent_runtime_report_path(*, root: Path, session_id: str) -> Path:
    return (
        _shadow_runtime_session_root(root=root, session_id=session_id)
        / "shadow_observation"
        / SHADOW_PERSISTENT_RUNTIME_REPORT_NAME
    )


def _shadow_runtime_sample_history_path(*, root: Path, session_id: str) -> Path:
    return _shadow_runtime_session_root(root=root, session_id=session_id) / SHADOW_RUNTIME_SAMPLE_HISTORY_NAME


def _shadow_runtime_sample_history_hash(history: dict[str, Any]) -> str:
    payload = dict(history)
    payload.pop("history_hash", None)
    return _sha256_json(payload)


def _shadow_runtime_sample_history_template(*, session_id: str, samples: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    accepted_samples = [sample for sample in samples or [] if sample.get("accepted") is True]
    accepted_cycle_sample_count = sum(int(sample.get("observed_actual_cycle_count") or 0) for sample in accepted_samples)
    observed_span_seconds = sum(int(sample.get("observed_actual_runtime_seconds") or 0) for sample in accepted_samples)
    history = {
        "schema_id": SHADOW_RUNTIME_SAMPLE_HISTORY_SCHEMA_ID,
        "created_at_utc": utc_now(),
        "updated_at_utc": utc_now(),
        "history_id": f"{session_id}:shadow-runtime-sample-history",
        "history_role": SHADOW_RUNTIME_SAMPLE_HISTORY_ROLE,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "source_mode": "PAPER",
        "mode": "SHADOW",
        "session_id": session_id,
        "history_status": "COLLECTING" if accepted_samples else "INSUFFICIENT_HISTORY",
        "sample_count": len(samples or []),
        "accepted_sample_count": len(accepted_samples),
        "accepted_cycle_sample_count": accepted_cycle_sample_count,
        "observed_span_seconds": observed_span_seconds,
        "min_actual_long_run_span_seconds": 86400,
        "min_actual_long_run_cycle_count": 2880,
        "span_floor_met": observed_span_seconds >= 86400,
        "cycle_floor_met": accepted_cycle_sample_count >= 2880,
        "samples": samples or [],
        "long_run_evidence_eligible": False,
        "actual_long_run_evidence_created": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "history_hash": "",
    }
    history["history_hash"] = _shadow_runtime_sample_history_hash(history)
    return history


def _load_shadow_runtime_sample_history(*, root: Path, session_id: str) -> dict[str, Any]:
    path = _shadow_runtime_sample_history_path(root=root, session_id=session_id)
    if not path.is_file():
        return _shadow_runtime_sample_history_template(session_id=session_id)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        value = None
    if isinstance(value, dict):
        return value
    return _shadow_runtime_sample_history_template(
        session_id=session_id,
        samples=[
            {
                "sample_id": _sha256_json({"path": str(path), "error": "unreadable"}),
                "accepted": False,
                "validation_status": "FAIL",
                "rejection_code": "SCHEMA_IDENTITY_MISMATCH",
                "orchestration_id": "",
                "orchestration_report_hash": "",
                "persistent_runtime_report_hash": "",
                "harness_report_hash": "",
                "observed_actual_runtime_seconds": 0,
                "observed_actual_cycle_count": 0,
                "source_hashes_verified": False,
                "source_runtime_hash_pairing_verified": False,
                "source_validation_status": "FAIL",
                "runtime_evidence_role": "UNKNOWN",
                "long_run_evidence_eligible": False,
                "actual_long_run_runtime_present": False,
                "scorecard_input_eligible": False,
                "promotion_eligible": False,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
                "order_adapter_called": False,
            }
        ],
    )


def _validate_shadow_runtime_sample_history(history: dict[str, Any]) -> ProfileValidationResult:
    required = {
        "schema_id",
        "created_at_utc",
        "updated_at_utc",
        "history_id",
        "history_role",
        "exchange",
        "market_type",
        "source_mode",
        "mode",
        "session_id",
        "history_status",
        "sample_count",
        "accepted_sample_count",
        "accepted_cycle_sample_count",
        "observed_span_seconds",
        "min_actual_long_run_span_seconds",
        "min_actual_long_run_cycle_count",
        "span_floor_met",
        "cycle_floor_met",
        "samples",
        "long_run_evidence_eligible",
        "actual_long_run_evidence_created",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "history_hash",
    }
    missing = sorted(required - set(history))
    if missing:
        return ProfileValidationResult("FAIL", f"SHADOW runtime sample history missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("schema_id") != SHADOW_RUNTIME_SAMPLE_HISTORY_SCHEMA_ID:
        return ProfileValidationResult("FAIL", "SHADOW runtime sample history schema mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("history_hash") != _shadow_runtime_sample_history_hash(history):
        return ProfileValidationResult("FAIL", "SHADOW runtime sample history hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if (
        history.get("history_role") != SHADOW_RUNTIME_SAMPLE_HISTORY_ROLE
        or history.get("exchange") != "UPBIT"
        or history.get("market_type") != "KRW_SPOT"
        or history.get("source_mode") != "PAPER"
        or history.get("mode") != "SHADOW"
    ):
        return ProfileValidationResult("BLOCKED", "SHADOW runtime sample history scope drifted", "SNAPSHOT_SCOPE_MISMATCH")
    if any(
        history.get(field)
        for field in (
            "long_run_evidence_eligible",
            "actual_long_run_evidence_created",
            "promotion_eligible",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        )
    ):
        return ProfileValidationResult("BLOCKED", "SHADOW runtime sample history attempted long-run or live permission", "LIVE_FINAL_GUARD_FAILED")
    samples = history.get("samples")
    if not isinstance(samples, list):
        return ProfileValidationResult("FAIL", "SHADOW runtime sample history samples must be a list", "SCHEMA_IDENTITY_MISMATCH")
    seen_sample_ids: set[str] = set()
    accepted_count = 0
    accepted_cycles = 0
    accepted_span = 0
    for sample in samples:
        if not isinstance(sample, dict):
            return ProfileValidationResult("FAIL", "SHADOW runtime sample history contains a non-object sample", "SCHEMA_IDENTITY_MISMATCH")
        sample_required = {
            "sample_id",
            "accepted",
            "validation_status",
            "rejection_code",
            "orchestration_id",
            "orchestration_report_hash",
            "persistent_runtime_report_hash",
            "harness_report_hash",
            "observed_actual_runtime_seconds",
            "observed_actual_cycle_count",
            "source_hashes_verified",
            "source_runtime_hash_pairing_verified",
            "source_validation_status",
            "runtime_evidence_role",
            "long_run_evidence_eligible",
            "actual_long_run_runtime_present",
            "scorecard_input_eligible",
            "promotion_eligible",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
            "order_adapter_called",
        }
        sample_missing = sorted(sample_required - set(sample))
        if sample_missing:
            return ProfileValidationResult("FAIL", f"SHADOW runtime sample missing fields: {sample_missing}", "SCHEMA_IDENTITY_MISMATCH")
        sample_id = str(sample.get("sample_id") or "")
        if not sample_id or sample_id in seen_sample_ids:
            return ProfileValidationResult("BLOCKED", "SHADOW runtime sample history contains duplicate sample identity", "DUPLICATE_WRITER_RISK")
        seen_sample_ids.add(sample_id)
        for field in ("observed_actual_runtime_seconds", "observed_actual_cycle_count"):
            if isinstance(sample.get(field), bool) or not isinstance(sample.get(field), int) or sample.get(field) < 0:
                return ProfileValidationResult("FAIL", f"SHADOW runtime sample count is invalid: {field}", "SCHEMA_IDENTITY_MISMATCH")
        if any(
            sample.get(field)
            for field in (
                "long_run_evidence_eligible",
                "actual_long_run_runtime_present",
                "scorecard_input_eligible",
                "promotion_eligible",
                "live_order_ready",
                "live_order_allowed",
                "can_live_trade",
                "scale_up_allowed",
                "order_adapter_called",
            )
        ):
            return ProfileValidationResult("BLOCKED", "SHADOW runtime sample attempted long-run, optimizer, live, or order permission", "LIVE_FINAL_GUARD_FAILED")
        if sample.get("accepted") is True:
            if (
                sample.get("validation_status") != "PASS"
                or sample.get("source_validation_status") != "PASS"
                or sample.get("source_hashes_verified") is not True
                or sample.get("source_runtime_hash_pairing_verified") is not True
                or sample.get("runtime_evidence_role") != "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN"
                or int(sample.get("observed_actual_cycle_count") or 0) <= 0
            ):
                return ProfileValidationResult("BLOCKED", "accepted SHADOW runtime sample is not verified short-window evidence", "MEASUREMENT_MISSING")
            if int(sample.get("observed_actual_runtime_seconds") or 0) >= int(history.get("min_actual_long_run_span_seconds") or 0):
                return ProfileValidationResult("BLOCKED", "single SHADOW runtime sample cannot satisfy long-run span", LONG_RUN_EVIDENCE_BLOCKER_CODE)
            if int(sample.get("observed_actual_cycle_count") or 0) >= int(history.get("min_actual_long_run_cycle_count") or 0):
                return ProfileValidationResult("BLOCKED", "single SHADOW runtime sample cannot satisfy long-run cycles", LONG_RUN_EVIDENCE_BLOCKER_CODE)
            accepted_count += 1
            accepted_cycles += int(sample.get("observed_actual_cycle_count") or 0)
            accepted_span += int(sample.get("observed_actual_runtime_seconds") or 0)
    if int(history.get("sample_count") or 0) != len(samples):
        return ProfileValidationResult("FAIL", "SHADOW runtime sample history sample count drifted", "SCHEMA_IDENTITY_MISMATCH")
    if int(history.get("accepted_sample_count") or 0) != accepted_count:
        return ProfileValidationResult("FAIL", "SHADOW runtime sample history accepted sample count drifted", "SCHEMA_IDENTITY_MISMATCH")
    if int(history.get("accepted_cycle_sample_count") or 0) != accepted_cycles:
        return ProfileValidationResult("FAIL", "SHADOW runtime sample history accepted cycle count drifted", "SCHEMA_IDENTITY_MISMATCH")
    if int(history.get("observed_span_seconds") or 0) != accepted_span:
        return ProfileValidationResult("FAIL", "SHADOW runtime sample history observed span drifted", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("span_floor_met") is not (accepted_span >= int(history.get("min_actual_long_run_span_seconds") or 0) > 0):
        return ProfileValidationResult("FAIL", "SHADOW runtime sample history span floor drifted", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("cycle_floor_met") is not (accepted_cycles >= int(history.get("min_actual_long_run_cycle_count") or 0) > 0):
        return ProfileValidationResult("FAIL", "SHADOW runtime sample history cycle floor drifted", "SCHEMA_IDENTITY_MISMATCH")
    expected_status = "COLLECTING" if accepted_count else "INSUFFICIENT_HISTORY"
    if history.get("history_status") != expected_status:
        return ProfileValidationResult("FAIL", "SHADOW runtime sample history status drifted", "SCHEMA_IDENTITY_MISMATCH")
    return ProfileValidationResult("PASS", "SHADOW runtime sample history is source-bound, short-window only, and live-blocked", None)


def _shadow_runtime_sample_from_orchestration(orchestration: dict[str, Any], result: Any) -> dict[str, Any]:
    bindings = [item for item in orchestration.get("source_evidence_bindings") or [] if isinstance(item, dict)]
    persistent_hash = next(
        (str(item.get("source_hash") or "") for item in bindings if str(item.get("source_role") or "").startswith("PERSISTENT_RUNTIME")),
        "",
    )
    harness_hash = next((str(item.get("source_hash") or "") for item in bindings if item.get("source_role") == "SHORT_WINDOW_HARNESS"), "")
    observed_seconds = int(orchestration.get("observed_actual_runtime_seconds") or 0)
    observed_cycles = int(orchestration.get("observed_actual_cycle_count") or 0)
    validation_status = str(getattr(result, "status", "BLOCKED") or "BLOCKED")
    rejection_code = getattr(result, "blocker_code", None)
    accepted = (
        validation_status == "PASS"
        and orchestration.get("source_validation_status") == "PASS"
        and orchestration.get("source_hashes_verified") is True
        and orchestration.get("source_runtime_hash_pairing_verified") is True
        and orchestration.get("source_scope_match") is True
        and orchestration.get("runtime_evidence_role") == "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN"
        and orchestration.get("actual_long_run_runtime_present") is False
        and orchestration.get("long_run_evidence_eligible") is False
        and orchestration.get("scorecard_input_eligible") is False
        and orchestration.get("promotion_eligible") is False
        and observed_cycles > 0
        and not any(orchestration.get(field) for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called"))
    )
    sample_id = _sha256_json(
        {
            "orchestration_report_hash": str(orchestration.get("orchestration_report_hash") or ""),
            "persistent_runtime_report_hash": persistent_hash,
            "harness_report_hash": harness_hash,
            "observed_actual_runtime_seconds": observed_seconds,
            "observed_actual_cycle_count": observed_cycles,
        }
    )
    return {
        "sample_id": sample_id,
        "accepted": accepted,
        "validation_status": validation_status,
        "rejection_code": None if accepted else str(rejection_code or "MEASUREMENT_MISSING"),
        "orchestration_id": str(orchestration.get("orchestration_id") or ""),
        "orchestration_report_hash": str(orchestration.get("orchestration_report_hash") or ""),
        "persistent_runtime_report_hash": persistent_hash,
        "harness_report_hash": harness_hash,
        "observed_actual_runtime_seconds": observed_seconds,
        "observed_actual_cycle_count": observed_cycles,
        "source_hashes_verified": orchestration.get("source_hashes_verified") is True,
        "source_runtime_hash_pairing_verified": orchestration.get("source_runtime_hash_pairing_verified") is True,
        "source_validation_status": str(orchestration.get("source_validation_status") or "UNKNOWN"),
        "runtime_evidence_role": str(orchestration.get("runtime_evidence_role") or "UNKNOWN"),
        "long_run_evidence_eligible": bool(orchestration.get("long_run_evidence_eligible")),
        "actual_long_run_runtime_present": bool(orchestration.get("actual_long_run_runtime_present")),
        "scorecard_input_eligible": bool(orchestration.get("scorecard_input_eligible")),
        "promotion_eligible": bool(orchestration.get("promotion_eligible")),
        "live_order_ready": bool(orchestration.get("live_order_ready")),
        "live_order_allowed": bool(orchestration.get("live_order_allowed")),
        "can_live_trade": bool(orchestration.get("can_live_trade")),
        "scale_up_allowed": bool(orchestration.get("scale_up_allowed")),
        "order_adapter_called": bool(orchestration.get("order_adapter_called")),
    }


def _update_shadow_runtime_sample_history(
    *,
    root: Path,
    session_id: str,
    orchestration_sources: list[tuple[dict[str, Any], Any]],
) -> tuple[dict[str, Any], ProfileValidationResult]:
    existing = _load_shadow_runtime_sample_history(root=root, session_id=session_id)
    existing_result = _validate_shadow_runtime_sample_history(existing)
    if existing_result.status != "PASS":
        return existing, existing_result
    samples_by_id = {
        str(sample.get("sample_id")): dict(sample)
        for sample in existing.get("samples") or []
        if isinstance(sample, dict) and sample.get("sample_id")
    }
    for orchestration, result in orchestration_sources:
        if not isinstance(orchestration, dict):
            continue
        sample = _shadow_runtime_sample_from_orchestration(orchestration, result)
        samples_by_id.setdefault(str(sample["sample_id"]), sample)
    samples = sorted(samples_by_id.values(), key=lambda item: str(item.get("sample_id") or ""))
    updated = _shadow_runtime_sample_history_template(session_id=session_id, samples=samples)
    created_at = existing.get("created_at_utc")
    if isinstance(created_at, str) and created_at:
        updated["created_at_utc"] = created_at
        updated["history_hash"] = _shadow_runtime_sample_history_hash(updated)
    result = _validate_shadow_runtime_sample_history(updated)
    if result.status == "PASS":
        durable_atomic_write_json(_shadow_runtime_sample_history_path(root=root, session_id=session_id), updated)
    return updated, result


def _load_existing_shadow_runtime_orchestration_source(
    *,
    root: Path,
    session_id: str,
) -> tuple[dict[str, Any], Any] | None:
    path = _shadow_runtime_orchestration_report_path(root=root, session_id=session_id)
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        value = {}
    if not isinstance(value, dict):
        value = {}
    result = validate_shadow_observation_runtime_orchestration_report(value)
    if result.status != "PASS":
        return value, result

    expected_artifact_path = (
        f"system/runtime/upbit/krw_spot/shadow/{session_id}/{SHADOW_RUNTIME_ORCHESTRATION_REPORT_NAME}"
    )
    expected_scope = (
        value.get("exchange") == "UPBIT"
        and value.get("market_type") == "KRW_SPOT"
        and value.get("source_mode") == "PAPER"
        and value.get("mode") == "SHADOW"
        and value.get("session_id") == session_id
        and value.get("orchestration_artifact_path") == expected_artifact_path
    )
    if not expected_scope:
        return value, ProfileValidationResult(
            "BLOCKED",
            "existing SHADOW runtime orchestration source scope does not match the PAPER profile session",
            "SNAPSHOT_SCOPE_MISMATCH",
        )

    expected_not_long_run_source = (
        value.get("source_validation_status") == "PASS"
        and value.get("source_hashes_verified") is True
        and value.get("source_runtime_hash_pairing_verified") is True
        and value.get("source_scope_match") is True
        and value.get("runtime_evidence_role") == "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN"
        and value.get("actual_long_run_runtime_present") is False
        and value.get("long_run_evidence_eligible") is False
        and value.get("scorecard_input_eligible") is False
        and value.get("promotion_eligible") is False
        and value.get("order_adapter_called") is False
    )
    if not expected_not_long_run_source:
        return value, ProfileValidationResult(
            "BLOCKED",
            "existing SHADOW runtime orchestration source attempted unsafe evidence promotion",
            "LIVE_FINAL_GUARD_FAILED",
        )
    if any(value.get(field) for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        return value, ProfileValidationResult(
            "BLOCKED",
            "existing SHADOW runtime orchestration source attempted live or scale-up permission",
            "LIVE_FINAL_GUARD_FAILED",
        )
    return value, result


def _build_shadow_runtime_orchestration_source(*, loop_id: str, requested_cycle_count: int) -> tuple[dict[str, Any], Any]:
    seed = f"{loop_id}-shadow-depth"
    shadow_cycle_count = max(3, min(3, int(requested_cycle_count or 1)))
    observations = []
    for index in range(shadow_cycle_count):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id=f"{seed}-paper-gate",
            session_id=f"{seed}-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"{seed}-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"{seed}-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream = build_shadow_observation_stream_report(
        stream_id=f"{seed}-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    scheduler = build_shadow_observation_scheduler_guard_report(
        scheduler_id=f"{seed}-scheduler",
        stream_report=stream,
        writer_id=f"{seed}-writer",
        active_writer_id=f"{seed}-writer",
    )
    persistent = build_shadow_observation_persistent_runtime_report(
        runtime_id=f"{seed}-persistent-runtime",
        scheduler_guard_report=scheduler,
        requested_cycle_count=shadow_cycle_count,
        completed_cycle_count=shadow_cycle_count,
        max_cycle_count=20,
    )
    harness = build_shadow_observation_actual_runtime_harness_report(
        harness_id=f"{seed}-harness",
        requested_cycle_count=shadow_cycle_count,
        completed_cycle_count=shadow_cycle_count,
        observations_per_cycle=2,
        measured_runtime_seconds=90,
        runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
        monotonic_timer_started=True,
        monotonic_timer_stopped=True,
        measured_runtime_seconds_verified=True,
        source_runtime_report=persistent,
    )
    orchestration = build_shadow_observation_runtime_orchestration_report(
        orchestration_id=f"{seed}-orchestration",
        persistent_runtime_report=persistent,
        actual_runtime_harness_report=harness,
    )
    result = validate_shadow_observation_runtime_orchestration_report(orchestration)
    return orchestration, result


def _build_shadow_scheduler_guard_for_loop(
    *,
    loop_id: str,
    session_id: str,
    requested_cycle_count: int,
) -> dict[str, Any]:
    seed = f"{loop_id}-shadow-current"
    observation_count = max(3, min(3, int(requested_cycle_count or 1)))
    observations = []
    for index in range(observation_count):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id=f"{seed}-paper-gate",
            session_id=f"{session_id}-{seed}-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"{seed}-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"{session_id}-{seed}-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream = build_shadow_observation_stream_report(
        stream_id=f"{seed}-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    return build_shadow_observation_scheduler_guard_report(
        scheduler_id=f"{seed}-scheduler",
        stream_report=stream,
        writer_id=f"{seed}-writer",
        active_writer_id=f"{seed}-writer",
    )


def _measured_short_window_seconds(elapsed_seconds: float) -> int:
    if elapsed_seconds <= 0:
        return 0
    return max(0, min(300, int(elapsed_seconds)))


def _build_current_shadow_runtime_orchestration_source(
    *,
    root: Path,
    session_id: str,
    loop: dict[str, Any],
    measured_runtime_seconds: int,
) -> tuple[dict[str, Any], Any]:
    loop_id = str(loop.get("loop_id") or "upbit-paper-runtime-evidence-profile")
    completed = int(loop.get("completed_cycle_count") or 0)
    scheduler = _build_shadow_scheduler_guard_for_loop(
        loop_id=loop_id,
        session_id=session_id,
        requested_cycle_count=max(1, completed),
    )
    persistent = build_shadow_observation_persistent_runtime_report_from_paper_loop(
        runtime_id=session_id,
        scheduler_guard_report=scheduler,
        source_paper_loop_report=loop,
        runtime_artifact_path=f"system/runtime/upbit/krw_spot/shadow/{session_id}/shadow_observation/{SHADOW_PERSISTENT_RUNTIME_REPORT_NAME}",
        observed_runtime_seconds=measured_runtime_seconds,
        max_runtime_seconds=300,
    )
    harness = build_shadow_observation_actual_runtime_harness_report(
        harness_id=session_id,
        requested_cycle_count=completed,
        completed_cycle_count=completed,
        observations_per_cycle=2,
        measured_runtime_seconds=measured_runtime_seconds,
        runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
        monotonic_timer_started=True,
        monotonic_timer_stopped=True,
        measured_runtime_seconds_verified=True,
        source_runtime_report=persistent,
    )
    orchestration = build_shadow_observation_runtime_orchestration_report(
        orchestration_id=session_id,
        persistent_runtime_report=persistent,
        actual_runtime_harness_report=harness,
    )
    result = validate_shadow_observation_runtime_orchestration_report(orchestration)
    if result.status == "PASS":
        durable_atomic_write_json(_shadow_persistent_runtime_report_path(root=root, session_id=session_id), persistent)
        durable_atomic_write_json(_shadow_runtime_harness_report_path(root=root, session_id=session_id), harness)
        durable_atomic_write_json(_shadow_runtime_orchestration_report_path(root=root, session_id=session_id), orchestration)
    return orchestration, result


def _duplicate_first_ledger_jsonl(root: Path, loop: dict[str, Any]) -> None:
    for cycle_result in loop.get("cycle_results", []):
        for artifact_path in cycle_result.get("artifact_paths", []):
            artifact_text = str(artifact_path)
            if artifact_text.endswith(".paper_ledger_events.jsonl"):
                source = root / artifact_text
                duplicate = source.with_name("duplicate-runtime-evidence-profile.paper_ledger_events.jsonl")
                write_text(duplicate, source.read_text(encoding="utf-8"))
                rollup = build_paper_ledger_rollup_report(
                    root=root,
                    session_id=str(loop.get("session_id") or DEFAULT_SESSION_ID),
                    rollup_id=f"{loop.get('loop_id')}-duplicate-ledger-rollup",
                )
                write_paper_ledger_rollup_report(root=root, report=rollup)
                return
    raise RuntimeError("bounded PAPER loop did not write a ledger JSONL artifact")


def build_upbit_paper_runtime_evidence_collection_profile_report(
    *,
    root: Path,
    loop_id: str = "upbit-paper-runtime-evidence-profile",
    session_id: str = DEFAULT_SESSION_ID,
    requested_cycle_count: int = 2,
    duplicate_ledger_events: bool = False,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    loop_started_at = time.monotonic()
    loop = run_upbit_paper_persistent_loop(
        root=root,
        loop_id=loop_id,
        session_id=session_id,
        requested_cycle_count=requested_cycle_count,
    )
    measured_shadow_runtime_seconds = _measured_short_window_seconds(time.monotonic() - loop_started_at)
    if duplicate_ledger_events:
        _duplicate_first_ledger_jsonl(root, loop)

    loop_result = validate_upbit_paper_persistent_loop_report(loop)
    recovery_guard = build_recovery_guard_from_loop(root=root, loop=loop)
    recovery_result = validate_upbit_paper_runtime_recovery_guard_report(recovery_guard)
    sample_history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
    write_upbit_paper_runtime_sample_history(root=root, history=sample_history)
    sample_history_result = validate_upbit_paper_runtime_sample_history(sample_history)
    idempotency_evidence = build_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root, session_id=session_id)
    write_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root, report=idempotency_evidence)
    idempotency_result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(idempotency_evidence)
    existing_shadow_source = _load_existing_shadow_runtime_orchestration_source(root=root, session_id=session_id)
    shadow_sources: list[tuple[dict[str, Any], Any]] = []
    if existing_shadow_source is not None:
        shadow_sources.append(existing_shadow_source)
    current_shadow_orchestration, current_shadow_orchestration_result = _build_current_shadow_runtime_orchestration_source(
        root=root,
        session_id=session_id,
        loop=loop,
        measured_runtime_seconds=measured_shadow_runtime_seconds,
    )
    shadow_sources.append((current_shadow_orchestration, current_shadow_orchestration_result))
    shadow_runtime_history, shadow_runtime_history_result = _update_shadow_runtime_sample_history(
        root=root,
        session_id=session_id,
        orchestration_sources=shadow_sources,
    )
    if current_shadow_orchestration_result.status == "PASS":
        shadow_orchestration, shadow_orchestration_result = current_shadow_orchestration, current_shadow_orchestration_result
    elif existing_shadow_source is not None:
        shadow_orchestration, shadow_orchestration_result = existing_shadow_source
    else:
        shadow_orchestration, shadow_orchestration_result = _build_shadow_runtime_orchestration_source(
            loop_id=loop_id,
            requested_cycle_count=requested_cycle_count,
        )
    collection_depth = _long_run_collection_depth(
        sample_history=sample_history,
        idempotency_evidence=idempotency_evidence,
        shadow_orchestration=shadow_orchestration,
        shadow_orchestration_result=shadow_orchestration_result,
        shadow_runtime_history=shadow_runtime_history,
        shadow_runtime_history_result=shadow_runtime_history_result,
    )

    component_results = [
        _component(
            component_id="persistent_loop",
            status=loop_result.status,
            blocker_code=loop_result.blocker_code,
            message=loop_result.message,
            evidence_hash=loop.get("loop_hash"),
        ),
        _component(
            component_id="runtime_recovery_guard",
            status=recovery_result.status,
            blocker_code=recovery_result.blocker_code,
            message=recovery_result.message,
            evidence_hash=recovery_guard.get("guard_hash"),
        ),
        _component(
            component_id="runtime_sample_history",
            status=sample_history_result.status,
            blocker_code=sample_history_result.blocker_code,
            message=sample_history_result.message,
            evidence_hash=sample_history.get("history_hash"),
        ),
        _component(
            component_id="ledger_idempotency_runtime_evidence",
            status=idempotency_result.status,
            blocker_code=idempotency_result.blocker_code,
            message=idempotency_result.message,
            evidence_hash=idempotency_evidence.get("evidence_hash"),
        ),
        _component(
            component_id="shadow_runtime_orchestration",
            status=shadow_orchestration_result.status,
            blocker_code=shadow_orchestration_result.blocker_code,
            message=shadow_orchestration_result.message,
            evidence_hash=shadow_orchestration.get("orchestration_report_hash"),
        ),
        _component(
            component_id="shadow_runtime_sample_history",
            status=shadow_runtime_history_result.status,
            blocker_code=shadow_runtime_history_result.blocker_code,
            message=shadow_runtime_history_result.message,
            evidence_hash=shadow_runtime_history.get("history_hash"),
        ),
    ]
    blockers = [
        str(item["blocker_code"] or f"{item['component_id'].upper()}_NOT_PASS")
        for item in component_results
        if item.get("status") != "PASS"
    ]
    if sample_history.get("runtime_sample_status") == "BLOCKED":
        blockers.append(str(sample_history.get("primary_blocker_code") or "RECONCILIATION_REQUIRED"))
    if sample_history.get("long_run_evidence_eligible") or idempotency_evidence.get("long_run_evidence_eligible"):
        blockers.append("LONG_RUN_EVIDENCE_FALSE_POSITIVE")
    forbidden_flags = (
        loop.get("live_order_ready"),
        loop.get("live_order_allowed"),
        loop.get("can_live_trade"),
        loop.get("scale_up_allowed"),
        recovery_guard.get("live_order_ready"),
        recovery_guard.get("live_order_allowed"),
        recovery_guard.get("can_live_trade"),
        recovery_guard.get("scale_up_allowed"),
        sample_history.get("live_order_ready"),
        sample_history.get("live_order_allowed"),
        sample_history.get("can_live_trade"),
        sample_history.get("scale_up_allowed"),
        idempotency_evidence.get("live_order_ready"),
        idempotency_evidence.get("live_order_allowed"),
        idempotency_evidence.get("can_live_trade"),
        idempotency_evidence.get("can_submit_order"),
        idempotency_evidence.get("scale_up_allowed"),
        shadow_orchestration.get("live_order_ready"),
        shadow_orchestration.get("live_order_allowed"),
        shadow_orchestration.get("can_live_trade"),
        shadow_orchestration.get("scale_up_allowed"),
        shadow_runtime_history.get("live_order_ready"),
        shadow_runtime_history.get("live_order_allowed"),
        shadow_runtime_history.get("can_live_trade"),
        shadow_runtime_history.get("scale_up_allowed"),
    )
    if any(forbidden_flags):
        blockers.append("LIVE_FINAL_GUARD_FAILED")

    blocker_codes = sorted(set(blockers))
    profile_status = "PASS" if not blocker_codes else "BLOCKED"
    collection_plan = _non_live_collection_plan(collection_depth=collection_depth, profile_status=profile_status)
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "created_at_utc": created_at_utc or utc_now(),
        "profile_id": PROFILE_ID,
        "profile_scope": PROFILE_SCOPE,
        "status": profile_status,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "loop_id": loop_id,
        "requested_cycle_count": requested_cycle_count,
        "completed_cycle_count": int(loop.get("completed_cycle_count") or 0),
        "component_count": len(component_results),
        "component_pass_count": sum(1 for item in component_results if item["status"] == "PASS"),
        "component_blocked_count": sum(1 for item in component_results if item["status"] != "PASS"),
        "component_results": component_results,
        "loop_status": loop.get("loop_status"),
        "loop_hash": loop.get("loop_hash"),
        "recovery_guard_status": recovery_guard.get("recovery_guard_status"),
        "recovery_guard_hash": recovery_guard.get("guard_hash"),
        "runtime_sample_history_validation_status": sample_history_result.status,
        "runtime_sample_status": sample_history.get("runtime_sample_status"),
        "runtime_sample_history_hash": sample_history.get("history_hash"),
        "accepted_cycle_sample_count": int(sample_history.get("accepted_cycle_sample_count") or 0),
        "unique_runtime_cycle_hash_count": int(sample_history.get("unique_runtime_cycle_hash_count") or 0),
        "duplicate_cycle_hash_count": int(sample_history.get("duplicate_cycle_hash_count") or 0),
        "invalid_source_count": int(sample_history.get("invalid_source_count") or 0),
        "observed_span_seconds": int(sample_history.get("observed_span_seconds") or 0),
        "min_actual_long_run_span_seconds": int(sample_history.get("min_actual_long_run_span_seconds") or 0),
        "min_actual_long_run_cycle_count": int(sample_history.get("min_actual_long_run_cycle_count") or 0),
        "span_floor_met": bool(sample_history.get("span_floor_met")),
        "cycle_floor_met": bool(sample_history.get("cycle_floor_met")),
        "ledger_runtime_evidence_status": idempotency_evidence.get("runtime_evidence_status"),
        "ledger_idempotency_evidence_hash": idempotency_evidence.get("evidence_hash"),
        "idempotency_status": idempotency_evidence.get("idempotency_status"),
        "reconciliation_status": idempotency_evidence.get("reconciliation_status"),
        "mismatch_count": int(idempotency_evidence.get("mismatch_count") or 0),
        "source_ledger_jsonl_count": int(idempotency_evidence.get("source_ledger_jsonl_count") or 0),
        "recomputed_ledger_event_count": int(idempotency_evidence.get("recomputed_ledger_event_count") or 0),
        "recomputed_filled_order_count": int(idempotency_evidence.get("recomputed_filled_order_count") or 0),
        "duplicate_event_id_count": int(idempotency_evidence.get("duplicate_event_id_count") or 0),
        "duplicate_dedup_key_count": int(idempotency_evidence.get("duplicate_dedup_key_count") or 0),
        "duplicate_semantic_event_count": int(idempotency_evidence.get("duplicate_semantic_event_count") or 0),
        "duplicate_filled_order_key_count": int(idempotency_evidence.get("duplicate_filled_order_key_count") or 0),
        "primary_blocker_code": blocker_codes[0] if blocker_codes else None,
        "blockers": blocker_codes,
        "long_run_blocker_code": LONG_RUN_EVIDENCE_BLOCKER_CODE,
        "long_run_collection_depth": collection_depth,
        "non_live_collection_plan": collection_plan,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "current_evidence_write_allowed": False,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "scale_up_allowed": False,
        "profile_hash": "",
    }
    report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)
    return report


def build_recovery_guard_from_loop(*, root: Path, loop: dict[str, Any]) -> dict[str, Any]:
    guard_path_text = loop.get("runtime_recovery_guard_path")
    if isinstance(guard_path_text, str) and guard_path_text:
        guard_path = Path(root).resolve() / guard_path_text
        try:
            value = json.loads(guard_path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                return value
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
            pass
    from trader1.runtime.paper.upbit_paper_persistent_loop import build_upbit_paper_runtime_recovery_guard_report

    return build_upbit_paper_runtime_recovery_guard_report(
        root=Path(root).resolve(),
        session_id=str(loop.get("session_id") or DEFAULT_SESSION_ID),
        loop_id=str(loop.get("loop_id") or "upbit-paper-runtime-evidence-profile"),
    )


def validate_upbit_paper_runtime_evidence_collection_profile_report(
    report: dict[str, Any],
) -> ProfileValidationResult:
    required = {
        "schema_id",
        "created_at_utc",
        "profile_id",
        "profile_scope",
        "status",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "loop_id",
        "requested_cycle_count",
        "completed_cycle_count",
        "component_count",
        "component_pass_count",
        "component_blocked_count",
        "component_results",
        "loop_status",
        "loop_hash",
        "recovery_guard_status",
        "recovery_guard_hash",
        "runtime_sample_history_validation_status",
        "runtime_sample_status",
        "runtime_sample_history_hash",
        "accepted_cycle_sample_count",
        "unique_runtime_cycle_hash_count",
        "duplicate_cycle_hash_count",
        "invalid_source_count",
        "observed_span_seconds",
        "min_actual_long_run_span_seconds",
        "min_actual_long_run_cycle_count",
        "span_floor_met",
        "cycle_floor_met",
        "ledger_runtime_evidence_status",
        "ledger_idempotency_evidence_hash",
        "idempotency_status",
        "reconciliation_status",
        "mismatch_count",
        "source_ledger_jsonl_count",
        "recomputed_ledger_event_count",
        "recomputed_filled_order_count",
        "duplicate_event_id_count",
        "duplicate_dedup_key_count",
        "duplicate_semantic_event_count",
        "duplicate_filled_order_key_count",
        "primary_blocker_code",
        "blockers",
        "long_run_blocker_code",
        "long_run_collection_depth",
        "non_live_collection_plan",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "current_evidence_write_allowed",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
        "profile_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ProfileValidationResult("FAIL", f"runtime evidence profile missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != REPORT_SCHEMA_ID or report.get("profile_id") != PROFILE_ID:
        return ProfileValidationResult("FAIL", "runtime evidence profile identity mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("profile_hash") != upbit_paper_runtime_evidence_collection_profile_hash(report):
        return ProfileValidationResult("FAIL", "runtime evidence profile hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return ProfileValidationResult("BLOCKED", "runtime evidence profile scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    forbidden = (
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "current_evidence_write_allowed",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden):
        return ProfileValidationResult("BLOCKED", "runtime evidence profile attempted forbidden live or promotion permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("long_run_blocker_code") != LONG_RUN_EVIDENCE_BLOCKER_CODE:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile must preserve long-run evidence blocker", LONG_RUN_EVIDENCE_BLOCKER_CODE)
    collection_depth = report.get("long_run_collection_depth")
    if not isinstance(collection_depth, dict):
        return ProfileValidationResult("FAIL", "runtime evidence profile missing long-run collection depth", "SCHEMA_IDENTITY_MISMATCH")
    if collection_depth.get("status") != LONG_RUN_COLLECTION_DEPTH_STATUS:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile must keep long-run collection depth blocked", LONG_RUN_EVIDENCE_BLOCKER_CODE)
    if collection_depth.get("depth_role") != LONG_RUN_COLLECTION_DEPTH_ROLE:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile collection depth role cannot claim long-run evidence", LONG_RUN_EVIDENCE_BLOCKER_CODE)
    if collection_depth.get("blocker_code") != LONG_RUN_EVIDENCE_BLOCKER_CODE:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile collection depth must expose long-run blocker", LONG_RUN_EVIDENCE_BLOCKER_CODE)
    if collection_depth.get("required_runtime_modes") != ["PAPER", "SHADOW"]:
        return ProfileValidationResult("FAIL", "runtime evidence profile collection depth required modes drifted", "SCHEMA_IDENTITY_MISMATCH")
    if "SHADOW" not in collection_depth.get("missing_runtime_modes", []):
        return ProfileValidationResult("BLOCKED", "runtime evidence profile cannot hide missing SHADOW collection depth", "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")
    shadow_depth_status = collection_depth.get("shadow_runtime_depth_status")
    pairing_status = collection_depth.get("paper_shadow_pairing_status")
    if shadow_depth_status not in {"MISSING", "PRESENT_NOT_LONG_RUN", "BLOCKED"}:
        return ProfileValidationResult("FAIL", "runtime evidence profile shadow runtime depth status is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if pairing_status not in {"MISSING", "PAIRED_NOT_LONG_RUN", "BLOCKED"}:
        return ProfileValidationResult("FAIL", "runtime evidence profile PAPER/SHADOW pairing status is invalid", "SCHEMA_IDENTITY_MISMATCH")
    paper_depth_status = collection_depth.get("paper_runtime_depth_status")
    if paper_depth_status == "PASS" and shadow_depth_status == "PRESENT_NOT_LONG_RUN" and pairing_status != "PAIRED_NOT_LONG_RUN":
        return ProfileValidationResult("BLOCKED", "runtime evidence profile shadow depth must remain paired and not-long-run", "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")
    if pairing_status == "PAIRED_NOT_LONG_RUN" and (paper_depth_status != "PASS" or shadow_depth_status != "PRESENT_NOT_LONG_RUN"):
        return ProfileValidationResult("BLOCKED", "runtime evidence profile pairing cannot exist without not-long-run SHADOW depth", "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")
    mode_depth_evidence = collection_depth.get("runtime_mode_depth_evidence")
    if not isinstance(mode_depth_evidence, dict):
        return ProfileValidationResult("FAIL", "runtime evidence profile missing per-mode long-run depth evidence", "SCHEMA_IDENTITY_MISMATCH")
    if mode_depth_evidence.get("status") != RUNTIME_MODE_DEPTH_STATUS:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile per-mode long-run depth must remain blocked", RUNTIME_MODE_DEPTH_BLOCKER_CODE)
    if mode_depth_evidence.get("blocker_code") != RUNTIME_MODE_DEPTH_BLOCKER_CODE:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile per-mode depth must preserve PAPER/SHADOW blocker", RUNTIME_MODE_DEPTH_BLOCKER_CODE)
    if mode_depth_evidence.get("required_modes") != ["PAPER", "SHADOW"]:
        return ProfileValidationResult("FAIL", "runtime evidence profile per-mode depth required modes drifted", "SCHEMA_IDENTITY_MISMATCH")
    mode_depths = mode_depth_evidence.get("mode_depths")
    if not isinstance(mode_depths, dict) or set(mode_depths) != {"paper", "shadow"}:
        return ProfileValidationResult("FAIL", "runtime evidence profile per-mode depth entries are incomplete", "SCHEMA_IDENTITY_MISMATCH")
    expected_missing_modes: list[str] = []
    for key, expected_mode in (("paper", "PAPER"), ("shadow", "SHADOW")):
        depth = mode_depths.get(key)
        if not isinstance(depth, dict):
            return ProfileValidationResult("FAIL", "runtime evidence profile per-mode depth entry is invalid", "SCHEMA_IDENTITY_MISMATCH")
        if depth.get("mode") != expected_mode:
            return ProfileValidationResult("FAIL", "runtime evidence profile per-mode depth mode mismatch", "SCHEMA_IDENTITY_MISMATCH")
        for field in ("observed_span_seconds", "minimum_span_seconds", "missing_span_seconds", "observed_cycle_count", "minimum_cycle_count", "missing_cycle_count"):
            if isinstance(depth.get(field), bool) or not isinstance(depth.get(field), int) or depth.get(field) < 0:
                return ProfileValidationResult("FAIL", f"runtime evidence profile per-mode depth count is invalid: {field}", "SCHEMA_IDENTITY_MISMATCH")
        if depth.get("minimum_span_seconds") != report.get("min_actual_long_run_span_seconds"):
            return ProfileValidationResult("FAIL", "runtime evidence profile per-mode span floor drifted", "SCHEMA_IDENTITY_MISMATCH")
        if depth.get("minimum_cycle_count") != report.get("min_actual_long_run_cycle_count"):
            return ProfileValidationResult("FAIL", "runtime evidence profile per-mode cycle floor drifted", "SCHEMA_IDENTITY_MISMATCH")
        if depth.get("missing_span_seconds") != max(0, int(depth.get("minimum_span_seconds") or 0) - int(depth.get("observed_span_seconds") or 0)):
            return ProfileValidationResult("FAIL", "runtime evidence profile per-mode missing span mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if depth.get("missing_cycle_count") != max(0, int(depth.get("minimum_cycle_count") or 0) - int(depth.get("observed_cycle_count") or 0)):
            return ProfileValidationResult("FAIL", "runtime evidence profile per-mode missing cycle mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if depth.get("span_floor_met") is not (int(depth.get("observed_span_seconds") or 0) >= int(depth.get("minimum_span_seconds") or 0) > 0):
            return ProfileValidationResult("FAIL", "runtime evidence profile per-mode span floor flag drifted", "SCHEMA_IDENTITY_MISMATCH")
        if depth.get("cycle_floor_met") is not (int(depth.get("observed_cycle_count") or 0) >= int(depth.get("minimum_cycle_count") or 0) > 0):
            return ProfileValidationResult("FAIL", "runtime evidence profile per-mode cycle floor flag drifted", "SCHEMA_IDENTITY_MISMATCH")
        if depth.get("long_run_floor_met") is not (depth.get("span_floor_met") is True and depth.get("cycle_floor_met") is True):
            return ProfileValidationResult("FAIL", "runtime evidence profile per-mode long-run floor flag drifted", "SCHEMA_IDENTITY_MISMATCH")
        if (
            depth.get("counts_as_actual_long_run_evidence")
            or depth.get("live_order_ready")
            or depth.get("live_order_allowed")
            or depth.get("can_live_trade")
            or depth.get("scale_up_allowed")
        ):
            return ProfileValidationResult("BLOCKED", "runtime evidence profile per-mode depth attempted long-run, live, or scale permission", "LIVE_FINAL_GUARD_FAILED")
        if depth.get("long_run_floor_met") is not True or depth.get("counts_as_actual_long_run_evidence") is not True:
            expected_missing_modes.append(expected_mode)
    if mode_depths["paper"].get("observed_span_seconds") != report.get("observed_span_seconds"):
        return ProfileValidationResult("FAIL", "runtime evidence profile PAPER per-mode span drifted", "SCHEMA_IDENTITY_MISMATCH")
    if mode_depths["paper"].get("observed_cycle_count") != report.get("accepted_cycle_sample_count"):
        return ProfileValidationResult("FAIL", "runtime evidence profile PAPER per-mode cycle count drifted", "SCHEMA_IDENTITY_MISMATCH")
    if mode_depth_evidence.get("missing_long_run_modes") != expected_missing_modes:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile cannot hide per-mode long-run missing modes", RUNTIME_MODE_DEPTH_BLOCKER_CODE)
    if mode_depth_evidence.get("missing_long_run_mode_count") != len(expected_missing_modes):
        return ProfileValidationResult("FAIL", "runtime evidence profile per-mode missing mode count drifted", "SCHEMA_IDENTITY_MISMATCH")
    if (
        mode_depth_evidence.get("all_required_modes_long_run_validated")
        or mode_depth_evidence.get("actual_long_run_evidence_created")
        or mode_depth_evidence.get("long_run_evidence_eligible")
        or mode_depth_evidence.get("promotion_eligible")
        or mode_depth_evidence.get("live_order_ready")
        or mode_depth_evidence.get("live_order_allowed")
        or mode_depth_evidence.get("can_live_trade")
        or mode_depth_evidence.get("scale_up_allowed")
    ):
        return ProfileValidationResult("BLOCKED", "runtime evidence profile per-mode depth attempted actual long-run, live, promotion, or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if collection_depth.get("observed_span_seconds") != report.get("observed_span_seconds"):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection depth span drifted", "SCHEMA_IDENTITY_MISMATCH")
    if collection_depth.get("minimum_span_seconds") != report.get("min_actual_long_run_span_seconds"):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection depth span floor drifted", "SCHEMA_IDENTITY_MISMATCH")
    if collection_depth.get("observed_cycle_count") != report.get("accepted_cycle_sample_count"):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection depth cycle count drifted", "SCHEMA_IDENTITY_MISMATCH")
    if collection_depth.get("minimum_cycle_count") != report.get("min_actual_long_run_cycle_count"):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection depth cycle floor drifted", "SCHEMA_IDENTITY_MISMATCH")
    if collection_depth.get("missing_span_seconds") != max(0, int(report.get("min_actual_long_run_span_seconds") or 0) - int(report.get("observed_span_seconds") or 0)):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection depth missing span mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if collection_depth.get("missing_cycle_count") != max(0, int(report.get("min_actual_long_run_cycle_count") or 0) - int(report.get("accepted_cycle_sample_count") or 0)):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection depth missing cycle mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if collection_depth.get("span_floor_met") is not report.get("span_floor_met") or collection_depth.get("cycle_floor_met") is not report.get("cycle_floor_met"):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection depth floor flags drifted", "SCHEMA_IDENTITY_MISMATCH")
    if (
        collection_depth.get("bounded_profile_counts_as_long_run_evidence")
        or collection_depth.get("dashboard_display_counts_as_long_run_evidence")
        or collection_depth.get("actual_long_run_evidence_created")
        or collection_depth.get("long_run_evidence_eligible")
        or collection_depth.get("promotion_eligible")
        or collection_depth.get("live_order_ready")
        or collection_depth.get("live_order_allowed")
        or collection_depth.get("can_live_trade")
        or collection_depth.get("scale_up_allowed")
    ):
        return ProfileValidationResult("BLOCKED", "runtime evidence profile collection depth attempted long-run, live, promotion, or scale permission", "LIVE_FINAL_GUARD_FAILED")
    collection_plan = report.get("non_live_collection_plan")
    if not isinstance(collection_plan, dict):
        return ProfileValidationResult("FAIL", "runtime evidence profile missing non-live collection plan", "SCHEMA_IDENTITY_MISMATCH")
    if collection_plan.get("plan_role") != COLLECTION_PLAN_ROLE:
        return ProfileValidationResult("FAIL", "runtime evidence profile collection plan role mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_plan_status = COLLECTION_PLAN_READY_STATUS if report.get("status") == "PASS" else COLLECTION_PLAN_BLOCKED_STATUS
    if collection_plan.get("plan_status") != expected_plan_status:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile collection plan status does not match safe collection state", "RUNTIME_EVIDENCE_PROFILE_COMPONENT_NOT_PASS")
    required_next_modes = collection_plan.get("required_next_runtime_modes")
    if not isinstance(required_next_modes, list) or "SHADOW" not in required_next_modes:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile collection plan cannot hide missing SHADOW runtime evidence", RUNTIME_MODE_DEPTH_BLOCKER_CODE)
    if required_next_modes != mode_depth_evidence.get("missing_long_run_modes"):
        return ProfileValidationResult("BLOCKED", "runtime evidence profile collection plan mode gap drifted", RUNTIME_MODE_DEPTH_BLOCKER_CODE)
    plan_count_fields = (
        "recommended_next_paper_batch_cycle_count",
        "max_safe_paper_batch_cycle_count",
        "paper_remaining_span_seconds",
        "paper_remaining_cycle_count",
        "shadow_remaining_span_seconds",
        "shadow_remaining_cycle_count",
        "minimum_cycle_wall_clock_spacing_seconds",
        "estimated_wall_clock_seconds_remaining",
    )
    for field in plan_count_fields:
        if isinstance(collection_plan.get(field), bool) or not isinstance(collection_plan.get(field), int) or collection_plan.get(field) < 0:
            return ProfileValidationResult("FAIL", f"runtime evidence profile collection plan count is invalid: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if collection_plan.get("max_safe_paper_batch_cycle_count") != MAX_SAFE_PROFILE_BATCH_CYCLE_COUNT:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile collection plan batch cap drifted", "RUNTIME_BUDGET_EXCEEDED")
    if collection_plan.get("recommended_next_paper_batch_cycle_count") > MAX_SAFE_PROFILE_BATCH_CYCLE_COUNT:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile collection plan exceeds bounded PAPER batch budget", "RUNTIME_BUDGET_EXCEEDED")
    paper_mode_depth = mode_depths.get("paper")
    shadow_mode_depth = mode_depths.get("shadow")
    if not isinstance(paper_mode_depth, dict) or not isinstance(shadow_mode_depth, dict):
        return ProfileValidationResult("FAIL", "runtime evidence profile per-mode depth missing before collection plan validation", "SCHEMA_IDENTITY_MISMATCH")
    if collection_plan.get("paper_remaining_span_seconds") != int(paper_mode_depth.get("missing_span_seconds") or 0):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection plan PAPER span drifted", "SCHEMA_IDENTITY_MISMATCH")
    if collection_plan.get("paper_remaining_cycle_count") != int(paper_mode_depth.get("missing_cycle_count") or 0):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection plan PAPER cycle drifted", "SCHEMA_IDENTITY_MISMATCH")
    if collection_plan.get("shadow_remaining_span_seconds") != int(shadow_mode_depth.get("missing_span_seconds") or 0):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection plan SHADOW span drifted", "SCHEMA_IDENTITY_MISMATCH")
    if collection_plan.get("shadow_remaining_cycle_count") != int(shadow_mode_depth.get("missing_cycle_count") or 0):
        return ProfileValidationResult("FAIL", "runtime evidence profile collection plan SHADOW cycle drifted", "SCHEMA_IDENTITY_MISMATCH")
    expected_spacing = _ceil_div(int(report.get("min_actual_long_run_span_seconds") or 0), int(report.get("min_actual_long_run_cycle_count") or 0))
    if collection_plan.get("minimum_cycle_wall_clock_spacing_seconds") != expected_spacing:
        return ProfileValidationResult("FAIL", "runtime evidence profile collection plan wall-clock spacing drifted", "SCHEMA_IDENTITY_MISMATCH")
    expected_remaining_wall_clock = max(
        int(collection_plan.get("paper_remaining_span_seconds") or 0),
        int(collection_plan.get("shadow_remaining_span_seconds") or 0),
    )
    if collection_plan.get("estimated_wall_clock_seconds_remaining") != expected_remaining_wall_clock:
        return ProfileValidationResult("FAIL", "runtime evidence profile collection plan remaining wall-clock estimate drifted", "SCHEMA_IDENTITY_MISMATCH")
    expected_batch = (
        min(MAX_SAFE_PROFILE_BATCH_CYCLE_COUNT, int(collection_plan.get("paper_remaining_cycle_count") or 0))
        if report.get("status") == "PASS" and int(collection_plan.get("paper_remaining_cycle_count") or 0) > 0
        else 0
    )
    if collection_plan.get("recommended_next_paper_batch_cycle_count") != expected_batch:
        return ProfileValidationResult("FAIL", "runtime evidence profile collection plan next batch count drifted", "SCHEMA_IDENTITY_MISMATCH")
    if collection_plan.get("shadow_collection_required") is not True:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile collection plan must require SHADOW collection", RUNTIME_MODE_DEPTH_BLOCKER_CODE)
    if (
        collection_plan.get("counts_as_actual_long_run_evidence")
        or collection_plan.get("current_evidence_write_allowed")
        or collection_plan.get("promotion_eligible")
        or collection_plan.get("live_order_ready")
        or collection_plan.get("live_order_allowed")
        or collection_plan.get("can_live_trade")
        or collection_plan.get("scale_up_allowed")
    ):
        return ProfileValidationResult("BLOCKED", "runtime evidence profile collection plan attempted long-run, write, live, promotion, or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if not isinstance(collection_plan.get("next_operator_action"), str) or not collection_plan.get("next_operator_action", "").strip():
        return ProfileValidationResult("FAIL", "runtime evidence profile collection plan missing next operator action", "SCHEMA_IDENTITY_MISMATCH")
    component_results = report.get("component_results")
    if not isinstance(component_results, list) or report.get("component_count") != len(component_results):
        return ProfileValidationResult("FAIL", "runtime evidence profile component count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    component_pass_count = sum(1 for item in component_results if isinstance(item, dict) and item.get("status") == "PASS")
    if report.get("component_pass_count") != component_pass_count:
        return ProfileValidationResult("FAIL", "runtime evidence profile component pass count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("component_blocked_count") != len(component_results) - component_pass_count:
        return ProfileValidationResult("FAIL", "runtime evidence profile component blocked count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if component_pass_count != len(component_results) and report.get("status") == "PASS":
        return ProfileValidationResult(
            "BLOCKED",
            "runtime evidence profile cannot PASS when a component is not PASS",
            "RUNTIME_EVIDENCE_PROFILE_COMPONENT_NOT_PASS",
        )
    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return ProfileValidationResult("FAIL", "runtime evidence profile blockers must be a list", "SCHEMA_IDENTITY_MISMATCH")
    if blockers and report.get("status") != "BLOCKED":
        return ProfileValidationResult("FAIL", "runtime evidence profile with blockers must be BLOCKED", "SCHEMA_IDENTITY_MISMATCH")
    if not blockers and report.get("status") != "PASS":
        return ProfileValidationResult("FAIL", "runtime evidence profile without blockers must PASS", "SCHEMA_IDENTITY_MISMATCH")
    if blockers and report.get("primary_blocker_code") not in blockers:
        return ProfileValidationResult("FAIL", "runtime evidence profile primary blocker mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if not blockers and report.get("primary_blocker_code") is not None:
        return ProfileValidationResult("FAIL", "runtime evidence profile primary blocker set without blockers", "SCHEMA_IDENTITY_MISMATCH")
    expected_duplicate_total = (
        int(report.get("duplicate_event_id_count") or 0)
        + int(report.get("duplicate_dedup_key_count") or 0)
        + int(report.get("duplicate_semantic_event_count") or 0)
        + int(report.get("duplicate_filled_order_key_count") or 0)
    )
    if expected_duplicate_total > 0 and "RECONCILIATION_REQUIRED" not in blockers:
        return ProfileValidationResult("BLOCKED", "duplicate runtime ledger evidence must require reconciliation", "RECONCILIATION_REQUIRED")
    if report.get("status") == "PASS":
        pass_required = {
            "loop_status": "PASS",
            "recovery_guard_status": "PASS",
            "runtime_sample_history_validation_status": "PASS",
            "runtime_sample_status": "COLLECTING",
            "ledger_runtime_evidence_status": "PASS",
            "idempotency_status": "PASS",
            "reconciliation_status": "PASS",
        }
        for field, expected in pass_required.items():
            if report.get(field) != expected:
                return ProfileValidationResult("FAIL", f"PASS profile requires {field}={expected}", "SCHEMA_IDENTITY_MISMATCH")
        if int(report.get("accepted_cycle_sample_count") or 0) < int(report.get("completed_cycle_count") or 0):
            return ProfileValidationResult("FAIL", "accepted runtime sample count must cover completed bounded cycles", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("accepted_cycle_sample_count", 0) < 1 or report.get("source_ledger_jsonl_count", 0) < 1:
            return ProfileValidationResult("BLOCKED", "PASS profile requires actual bounded PAPER runtime and ledger artifacts", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    return ProfileValidationResult(report["status"], "Upbit PAPER runtime evidence collection profile is fail-closed", report.get("primary_blocker_code"))


def run_upbit_paper_runtime_evidence_collection_profile(
    *,
    requested_cycle_count: int = 2,
    duplicate_ledger_events: bool = False,
) -> dict[str, Any]:
    with TemporaryDirectory() as tmp:
        return build_upbit_paper_runtime_evidence_collection_profile_report(
            root=Path(tmp),
            requested_cycle_count=requested_cycle_count,
            duplicate_ledger_events=duplicate_ledger_events,
        )


def write_upbit_paper_runtime_evidence_collection_profile_report(
    *,
    root: Path,
    output: Path,
    loop_id: str | None = None,
    session_id: str = DEFAULT_SESSION_ID,
    requested_cycle_count: int = 2,
) -> tuple[dict[str, Any], ProfileValidationResult]:
    report = build_upbit_paper_runtime_evidence_collection_profile_report(
        root=Path(root),
        loop_id=loop_id or f"upbit-paper-runtime-evidence-profile-{_timestamp_compact()}",
        session_id=session_id,
        requested_cycle_count=requested_cycle_count,
    )
    result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)
    durable_atomic_write_json(Path(output), report)
    return report, result


def _refresh_dashboard_after_profile_write(
    *,
    root: Path,
    output: Path,
    session_id: str,
    duplicate_ledger_events: bool,
    refresh_dashboard: bool,
) -> None:
    if not refresh_dashboard or duplicate_ledger_events:
        return
    default_output = (ROOT / DEFAULT_REPORT_PATH).resolve()
    if output.resolve() != default_output:
        return
    from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle

    launcher_report = build_launcher_report("UPBIT_PAPER")
    launcher_report["session_id"] = session_id
    write_launcher_runtime_bundle(
        launcher_report,
        root=root,
        refresh_upbit_public_rest_continuity=False,
        refresh_paper_shadow_runtime=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded Upbit PAPER runtime evidence collection profile.")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH, help="JSON report path.")
    parser.add_argument("--requested-cycle-count", type=int, default=2, help="Bounded PAPER cycle count.")
    parser.add_argument("--source-root", type=Path, default=ROOT, help="Workspace root used for durable PAPER source artifacts.")
    parser.add_argument("--loop-id", type=str, default=None, help="Optional unique PAPER loop id for this profile run.")
    parser.add_argument("--session-id", type=str, default=DEFAULT_SESSION_ID, help="PAPER session id.")
    parser.add_argument(
        "--duplicate-ledger-events",
        action="store_true",
        help="Inject duplicate PAPER ledger events in an ephemeral fixture root to prove reconciliation blocking.",
    )
    parser.add_argument(
        "--no-refresh-dashboard",
        action="store_true",
        help="Do not refresh the UPBIT PAPER dashboard after writing the default profile report.",
    )
    args = parser.parse_args()

    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    output = args.output if args.output.is_absolute() else ROOT / args.output
    source_root = args.source_root if args.source_root.is_absolute() else ROOT / args.source_root
    if args.duplicate_ledger_events:
        report = run_upbit_paper_runtime_evidence_collection_profile(
            requested_cycle_count=args.requested_cycle_count,
            duplicate_ledger_events=True,
        )
        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)
        durable_atomic_write_json(output, report)
    else:
        report, result = write_upbit_paper_runtime_evidence_collection_profile_report(
            root=source_root,
            output=output,
            loop_id=args.loop_id,
            session_id=args.session_id,
            requested_cycle_count=args.requested_cycle_count,
        )
    if result.status in {"PASS", "BLOCKED"}:
        _refresh_dashboard_after_profile_write(
            root=source_root,
            output=output,
            session_id=args.session_id,
            duplicate_ledger_events=args.duplicate_ledger_events,
            refresh_dashboard=not args.no_refresh_dashboard,
        )
    print(json.dumps(report, indent=2))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
