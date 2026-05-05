from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


SCHEMA_ID = "trader1.residual_operator_evidence_trial_duration_policy_report.v1"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
TRIAL_PROFILE_ID = "UPBIT_PAPER_SAFE_MONITOR_24H_TRIAL"
TRIAL_DURATION_HOURS = 24
TRIAL_HEARTBEAT_INTERVAL_SECONDS = 10
TRIAL_HEARTBEAT_TICKS = TRIAL_DURATION_HOURS * 60 * 60 // TRIAL_HEARTBEAT_INTERVAL_SECONDS
TRIAL_MINIMUM_PAPER_SHADOW_WINDOW_COUNT = 4
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _source_report_ref(role: str, report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "role": role,
        "patch_id": str(report.get("patch_id", "")),
        "report_hash": str(report.get("report_hash", "")),
    }


def _trial_command_text() -> str:
    return (
        f"$env:TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS='{TRIAL_HEARTBEAT_TICKS}'; "
        f"$env:TRADER1_ROOT_OPERATOR_HEARTBEAT_INTERVAL_SECONDS='{TRIAL_HEARTBEAT_INTERVAL_SECONDS}'; "
        "python -B UPBIT_PAPER.py"
    )


def build_residual_operator_evidence_trial_duration_policy_report(
    preflight_report: Mapping[str, Any],
    intake_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    formal_duration_hours = int(preflight_report.get("minimum_duration_hours", 0) or 0)
    formal_ticks = int(preflight_report.get("expected_heartbeat_ticks", 0) or 0)
    formal_window_count = int(preflight_report.get("minimum_paper_shadow_window_count", 0) or 0)
    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": [
            _source_report_ref("residual_operator_evidence_run_preflight", preflight_report),
            _source_report_ref("residual_operator_evidence_intake_audit", intake_report),
        ],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "duration_policy_status": "TRIAL_PROFILE_ALLOWED_FORMAL_MVP5_STILL_BLOCKED",
        "operator_recommended_next_profile_id": TRIAL_PROFILE_ID,
        "operator_recommended_duration_hours": TRIAL_DURATION_HOURS,
        "operator_recommended_heartbeat_ticks": TRIAL_HEARTBEAT_TICKS,
        "operator_recommended_heartbeat_interval_seconds": TRIAL_HEARTBEAT_INTERVAL_SECONDS,
        "operator_recommended_minimum_paper_shadow_window_count": TRIAL_MINIMUM_PAPER_SHADOW_WINDOW_COUNT,
        "operator_recommended_command_shell": "powershell",
        "operator_recommended_command_text": _trial_command_text(),
        "trial_profile_non_live_only": True,
        "trial_profile_credential_required": False,
        "trial_profile_live_order_allowed": False,
        "trial_profile_mvp5_evidence_eligible": False,
        "trial_profile_gap_closure_allowed": False,
        "trial_profile_current_evidence_write_allowed": False,
        "trial_profile_purpose": "SHORT_RUNTIME_DEFECT_DISCOVERY_BEFORE_LONG_RUN",
        "formal_mvp5_profile_id": str(preflight_report.get("command_id", "")),
        "formal_mvp5_duration_hours": formal_duration_hours,
        "formal_mvp5_expected_heartbeat_ticks": formal_ticks,
        "formal_mvp5_minimum_paper_shadow_window_count": formal_window_count,
        "formal_mvp5_profile_still_required_for_live_readiness": True,
        "formal_mvp5_profile_replaced_by_trial": False,
        "operator_submission_manifest_status": str(intake_report.get("operator_submission_manifest_status", "")),
        "intake_review_ready": False,
        "command_executed_by_this_patch": False,
        "operator_run_completed_by_this_patch": False,
        "operator_run_evidence_ready_for_mvp5": False,
        "mvp5_entry_blocked_until_operator_evidence": True,
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_config_mutation_allowed": False,
        "live_ready_write_allowed": False,
        "credential_values_read": False,
        "credential_environment_inspection_performed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "validation_status": "PASS",
        "validation_errors": [],
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_residual_operator_evidence_trial_duration_policy_report(
    report: Mapping[str, Any],
    preflight_report: Mapping[str, Any],
    intake_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if report.get("duration_policy_status") != "TRIAL_PROFILE_ALLOWED_FORMAL_MVP5_STILL_BLOCKED":
        errors.append("duration policy must remain trial-only and formal MVP5 blocked")
    if report.get("open_gap_ids") != sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", [])):
        errors.append("open_gap_ids must match current state")
    if preflight_report.get("preflight_status") != "NON_LIVE_OPERATOR_RUN_PRECHECK_PASS":
        errors.append("source preflight must pass non-live precheck")
    if intake_report.get("intake_status") != "BLOCKED_AWAITING_OPERATOR_EVIDENCE_PACKAGE":
        errors.append("source intake audit must remain blocked")
    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
    if report.get("operator_recommended_next_profile_id") != TRIAL_PROFILE_ID:
        errors.append("operator recommended profile must be the 24h trial")
    if report.get("operator_recommended_duration_hours") != TRIAL_DURATION_HOURS:
        errors.append("operator recommended duration must be 24h")
    if report.get("operator_recommended_heartbeat_ticks") != TRIAL_HEARTBEAT_TICKS:
        errors.append("operator recommended heartbeat ticks must be 8640")
    if "UPBIT_PAPER.py" not in str(report.get("operator_recommended_command_text", "")):
        errors.append("operator recommended command must run UPBIT_PAPER.py")
    if "43200" in str(report.get("operator_recommended_command_text", "")):
        errors.append("operator recommended trial command must not keep 120h ticks")
    false_fields = (
        "trial_profile_credential_required",
        "trial_profile_live_order_allowed",
        "trial_profile_mvp5_evidence_eligible",
        "trial_profile_gap_closure_allowed",
        "trial_profile_current_evidence_write_allowed",
        "formal_mvp5_profile_replaced_by_trial",
        "intake_review_ready",
        "command_executed_by_this_patch",
        "operator_run_completed_by_this_patch",
        "operator_run_evidence_ready_for_mvp5",
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_config_mutation_allowed",
        "live_ready_write_allowed",
        "credential_values_read",
        "credential_environment_inspection_performed",
    )
    for field in false_fields:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
    if report.get("trial_profile_non_live_only") is not True:
        errors.append("trial profile must remain non-live only")
    if report.get("formal_mvp5_profile_still_required_for_live_readiness") is not True:
        errors.append("formal MVP5 profile must still be required for live readiness")
    if report.get("formal_mvp5_duration_hours") < 120:
        errors.append("formal MVP5 duration must stay at least 120h")
    if report.get("formal_mvp5_expected_heartbeat_ticks") < 43200:
        errors.append("formal MVP5 heartbeat ticks must stay at least 43200")
    if report.get("mvp5_entry_blocked_until_operator_evidence") is not True:
        errors.append("MVP5 entry must remain blocked")
    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    return errors
