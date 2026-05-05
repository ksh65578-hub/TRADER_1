from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_open_gap_operator_action_plan import FORBIDDEN_ACTIONS


SCHEMA_ID = "trader1.residual_paper_ledger_rerun_readiness_report.v1"
DEFAULT_SESSION_ID = "mvp1_upbit_paper_launcher"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
SAFE_FALSE_OR_ABSENT_FIELDS = (
    "current_evidence_mutation_allowed",
    "current_evidence_write_allowed",
    "current_ledger_jsonl_write_allowed",
    "latest_runtime_pointer_write_allowed",
    "persistent_loop_mutation_allowed",
    "source_delete_allowed",
    "actual_rerun_executed",
    "actual_long_run_evidence_created",
    "long_run_evidence_eligible",
    "promotion_eligible",
    "credential_load_attempted",
    "private_endpoint_called",
    "order_endpoint_called",
    "order_adapter_called",
    "live_key_loaded",
)

LEDGER_RERUN_GAP_IDS = (
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RECONCILIATION_REQUIRED",
)

RUNTIME_SOURCE_SPECS = {
    "missing_cycle_rerun_guard": {
        "relative_path": (
            "system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
            "upbit_paper_missing_cycle_rerun_guard_report.json"
        ),
        "schema_id": "trader1.upbit_paper_missing_cycle_rerun_guard_report.v1",
        "status_field": "guard_status",
        "expected": {
            "guard_status": "BLOCKED",
            "primary_blocker_code": "MISSING_CYCLE_LEDGER_RERUN_GUARD_ACTIVE",
        },
    },
    "bounded_rerun_staging_executor": {
        "relative_path": (
            "system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
            "upbit_paper_bounded_rerun_staging_executor_report.json"
        ),
        "schema_id": "trader1.upbit_paper_bounded_rerun_staging_executor_report.v1",
        "status_field": "executor_status",
        "expected": {
            "staging_status": "PASS",
            "executor_status": "BLOCKED",
            "primary_blocker_code": "POST_RERUN_LEDGER_ROLLUP_REQUIRED",
            "staged_current_evidence_usable_count": 0,
        },
    },
    "post_rerun_ledger_rollup_reconciliation": {
        "relative_path": (
            "system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
            "upbit_paper_post_rerun_ledger_rollup_reconciliation_report.json"
        ),
        "schema_id": "trader1.upbit_paper_post_rerun_ledger_rollup_reconciliation_report.v1",
        "status_field": "post_rerun_reconciliation_status",
        "expected": {
            "post_rerun_ledger_rollup_status": "PASS",
            "post_rerun_reconciliation_status": "BLOCKED",
            "primary_blocker_code": "POST_RERUN_RECONCILIATION_REQUIRED",
            "candidate_current_evidence_usable_count": 0,
        },
    },
    "current_evidence_closure_recheck": {
        "relative_path": (
            "system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
            "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json"
        ),
        "schema_id": "trader1.upbit_paper_post_rerun_current_evidence_closure_recheck_report.v1",
        "status_field": "recheck_status",
        "expected": {
            "recheck_status": "BLOCKED_POST_RERUN_CLOSURE_CONFIRMED",
            "closure_status": "CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED",
            "current_evidence_bridge_status": "BLOCKED_BY_POST_RERUN_CLOSURE",
            "portfolio_truth_recheck_status": "LEDGER_PROVENANCE_PASS_BUT_OPERATOR_CURRENT_EVIDENCE_BLOCKED",
            "primary_blocker_code": "POST_RERUN_RECONCILIATION_REQUIRED",
            "current_evidence_write_allowed": False,
            "latest_runtime_pointer_write_allowed": False,
        },
    },
    "operator_reconciliation_queue": {
        "relative_path": (
            "system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
            "upbit_paper_post_rerun_operator_reconciliation_queue_report.json"
        ),
        "schema_id": "trader1.upbit_paper_post_rerun_operator_reconciliation_queue_report.v1",
        "status_field": "queue_status",
        "expected": {
            "queue_status": "BLOCKED",
            "primary_blocker_code": "POST_RERUN_RECONCILIATION_REQUIRED",
            "current_evidence_write_allowed": False,
            "current_evidence_write_allowed_count": 0,
            "candidate_current_evidence_usable_count": 0,
        },
    },
}


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def runtime_source_paths(session_id: str = DEFAULT_SESSION_ID) -> dict[str, str]:
    return {
        source_id: str(spec["relative_path"]).format(session_id=session_id)
        for source_id, spec in RUNTIME_SOURCE_SPECS.items()
    }


def load_runtime_source_reports(root: Path, session_id: str = DEFAULT_SESSION_ID) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for source_id, relative_path in runtime_source_paths(session_id).items():
        path = Path(root) / relative_path
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            reports[source_id] = {"_load_status": "MISSING", "_relative_path": relative_path}
            continue
        except UnicodeDecodeError:
            reports[source_id] = {"_load_status": "INVALID_UTF8", "_relative_path": relative_path}
            continue
        except json.JSONDecodeError:
            reports[source_id] = {"_load_status": "INVALID_JSON", "_relative_path": relative_path}
            continue
        if not isinstance(value, dict):
            reports[source_id] = {"_load_status": "NOT_OBJECT", "_relative_path": relative_path}
            continue
        value = dict(value)
        value["_load_status"] = "PASS"
        value["_relative_path"] = relative_path
        reports[source_id] = value
    return reports


def _safe_bool_false(report: Mapping[str, Any], field: str) -> bool:
    return bool(report.get(field, False))


def _validate_source_report(source_id: str, report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    spec = RUNTIME_SOURCE_SPECS[source_id]
    load_status = report.get("_load_status", "PASS")
    if load_status != "PASS":
        return [f"{source_id} load_status must be PASS, got {load_status}"]
    if report.get("schema_id") != spec["schema_id"]:
        errors.append(f"{source_id} schema_id mismatch")
    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{source_id} {field} must remain false")
    for field in SAFE_FALSE_OR_ABSENT_FIELDS:
        if field in report and report.get(field) is not False:
            errors.append(f"{source_id} {field} must remain false when present")
    expected = spec.get("expected", {})
    if isinstance(expected, Mapping):
        for key, expected_value in expected.items():
            if report.get(key) != expected_value:
                errors.append(f"{source_id} {key} expected {expected_value!r}, got {report.get(key)!r}")
    return errors


def _source_summary(source_id: str, report: Mapping[str, Any]) -> dict[str, Any]:
    spec = RUNTIME_SOURCE_SPECS[source_id]
    status_field = str(spec["status_field"])
    validation_errors = _validate_source_report(source_id, report)
    load_status = str(report.get("_load_status", "PASS"))
    visible_report = {key: value for key, value in report.items() if not key.startswith("_")}
    source_hash = sha256_json(visible_report) if load_status == "PASS" else None
    return {
        "source_id": source_id,
        "relative_path": str(report.get("_relative_path") or runtime_source_paths()[source_id]),
        "load_status": load_status,
        "source_schema_id": str(report.get("schema_id", "")),
        "source_hash": source_hash,
        "validation_status": "PASS" if not validation_errors else "FAIL",
        "validation_errors": validation_errors,
        "primary_status_field": status_field,
        "primary_status_value": str(report.get(status_field, "UNKNOWN")),
        "primary_blocker_code": report.get("primary_blocker_code"),
        "current_evidence_mutation_allowed": _safe_bool_false(report, "current_evidence_mutation_allowed"),
        "current_evidence_write_allowed": _safe_bool_false(report, "current_evidence_write_allowed"),
        "latest_runtime_pointer_write_allowed": _safe_bool_false(report, "latest_runtime_pointer_write_allowed"),
        "actual_rerun_executed": _safe_bool_false(report, "actual_rerun_executed"),
        "live_order_ready": report.get("live_order_ready") is True,
        "live_order_allowed": report.get("live_order_allowed") is True,
        "can_live_trade": report.get("can_live_trade") is True,
        "scale_up_allowed": report.get("scale_up_allowed") is True,
    }


def _readiness_status(source_reports: Mapping[str, Mapping[str, Any]], source_errors: list[str]) -> str:
    if source_errors:
        return "BLOCKED_INVALID_SOURCE"
    staging = source_reports["bounded_rerun_staging_executor"]
    rollup = source_reports["post_rerun_ledger_rollup_reconciliation"]
    if rollup.get("post_rerun_reconciliation_status") == "BLOCKED":
        return "BLOCKED_RECONCILIATION_REQUIRED"
    if staging.get("staging_status") == "PASS":
        return "BLOCKED_LEDGER_ROLLUP_REQUIRED"
    return "BLOCKED_RERUN_INPUT_REQUIRED"


def build_residual_paper_ledger_rerun_readiness_report(
    source_reports: Mapping[str, Mapping[str, Any]],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
    session_id: str = DEFAULT_SESSION_ID,
) -> dict[str, Any]:
    summaries = [_source_summary(source_id, source_reports.get(source_id, {})) for source_id in RUNTIME_SOURCE_SPECS]
    source_errors = [error for summary in summaries for error in summary["validation_errors"]]
    open_gaps = list(state.get("open_contract_gap_ids", []))
    missing_gap_ids = [gap_id for gap_id in LEDGER_RERUN_GAP_IDS if gap_id not in open_gaps]
    state_errors = [f"current state missing open gap {gap_id}" for gap_id in missing_gap_ids]
    for field in LIVE_FALSE_FIELDS:
        if state.get(field) is not False:
            state_errors.append(f"state {field} must remain false")

    staging = source_reports.get("bounded_rerun_staging_executor", {})
    rollup = source_reports.get("post_rerun_ledger_rollup_reconciliation", {})
    closure = source_reports.get("current_evidence_closure_recheck", {})
    queue = source_reports.get("operator_reconciliation_queue", {})
    validation_errors = source_errors + state_errors

    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "gap_ids": list(LEDGER_RERUN_GAP_IDS),
        "gap_count": len(LEDGER_RERUN_GAP_IDS),
        "runtime_sources": summaries,
        "readiness_status": _readiness_status(source_reports, source_errors),
        "missing_cycle_guard_status": str(source_reports.get("missing_cycle_rerun_guard", {}).get("guard_status", "UNKNOWN")),
        "bounded_staging_status": str(staging.get("staging_status", "UNKNOWN")),
        "bounded_executor_status": str(staging.get("executor_status", "UNKNOWN")),
        "post_rerun_ledger_rollup_status": str(rollup.get("post_rerun_ledger_rollup_status", "UNKNOWN")),
        "post_rerun_reconciliation_status": str(rollup.get("post_rerun_reconciliation_status", "UNKNOWN")),
        "closure_status": str(closure.get("closure_status", "UNKNOWN")),
        "current_evidence_bridge_status": str(closure.get("current_evidence_bridge_status", "UNKNOWN")),
        "operator_queue_status": str(queue.get("queue_status", "UNKNOWN")),
        "staged_cycle_count": int(staging.get("staged_cycle_count", 0) or 0),
        "staged_current_evidence_usable_count": int(staging.get("staged_current_evidence_usable_count", 0) or 0),
        "candidate_rollup_pass_count": int(rollup.get("candidate_rollup_pass_count", 0) or 0),
        "candidate_current_evidence_usable_count": int(rollup.get("candidate_current_evidence_usable_count", 0) or 0),
        "operator_reconciliation_required_count": int(queue.get("operator_reconciliation_required_count", 0) or 0),
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "actual_rerun_executed": False,
        "operator_reconciliation_required": True,
        "post_rerun_reconciliation_required": True,
        "current_evidence_promotion_allowed": False,
        "selected_next_task_class": NEXT_TASK_CLASS,
        "operator_next_action": (
            "Complete post-rerun operator reconciliation before any PAPER current evidence promotion."
        ),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "validation_status": "PASS" if not validation_errors else "FAIL",
        "validation_errors": validation_errors,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_residual_paper_ledger_rerun_readiness_report(
    report: Mapping[str, Any],
    source_reports: Mapping[str, Mapping[str, Any]],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []

    expected = build_residual_paper_ledger_rerun_readiness_report(
        source_reports,
        state,
        patch_id=str(report.get("patch_id", "")),
        generated_at_utc=str(report.get("generated_at_utc", "")),
        trader1_sha256=str(report.get("authority", {}).get("trader1_sha256", "")) if isinstance(report.get("authority"), Mapping) else "",
        agents_sha256=str(report.get("authority", {}).get("agents_sha256", "")) if isinstance(report.get("authority"), Mapping) else "",
        session_id=str(report.get("session_id") or DEFAULT_SESSION_ID),
    )
    snapshot_fields = {"state_last_patch_id_before", "state_next_task_before", "report_hash"}
    comparable_report = {key: value for key, value in report.items() if key not in snapshot_fields}
    comparable_expected = {key: value for key, value in expected.items() if key not in snapshot_fields}
    if comparable_report != comparable_expected:
        errors.append("report content does not match current PAPER rerun source reports and implementation state")

    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
    for field in (
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "latest_runtime_pointer_write_allowed",
        "actual_rerun_executed",
        "current_evidence_promotion_allowed",
    ):
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")

    if tuple(report.get("gap_ids", [])) != LEDGER_RERUN_GAP_IDS:
        errors.append("gap_ids must exactly cover the residual PAPER ledger rerun gaps")
    if report.get("gap_count") != len(LEDGER_RERUN_GAP_IDS):
        errors.append("gap_count mismatch")
    if report.get("readiness_status") != "BLOCKED_RECONCILIATION_REQUIRED":
        errors.append("readiness_status must remain BLOCKED_RECONCILIATION_REQUIRED")
    if report.get("post_rerun_ledger_rollup_status") != "PASS":
        errors.append("post_rerun_ledger_rollup_status must be PASS")
    if report.get("post_rerun_reconciliation_status") != "BLOCKED":
        errors.append("post_rerun_reconciliation_status must be BLOCKED")
    if report.get("current_evidence_bridge_status") != "BLOCKED_BY_POST_RERUN_CLOSURE":
        errors.append("current_evidence_bridge_status must be BLOCKED_BY_POST_RERUN_CLOSURE")
    if report.get("operator_reconciliation_required") is not True:
        errors.append("operator_reconciliation_required must be true")
    if report.get("post_rerun_reconciliation_required") is not True:
        errors.append("post_rerun_reconciliation_required must be true")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if report.get("validation_status") != "PASS":
        errors.append("validation_status must be PASS")
    if report.get("validation_errors") != []:
        errors.append("validation_errors must be empty")

    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
