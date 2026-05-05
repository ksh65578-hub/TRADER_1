from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


SCHEMA_ID = "trader1.residual_mvp5_entry_duration_policy_report.v1"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
MVP5_REVIEW_ENTRY_PROFILE_ID = "UPBIT_PAPER_ADAPTIVE_EVIDENCE_REVIEW"
MVP5_REVIEW_ENTRY_DURATION_HOURS = 0
MVP5_REVIEW_ENTRY_HEARTBEAT_TICKS = 0
MVP5_REVIEW_ENTRY_HEARTBEAT_INTERVAL_SECONDS = 10
MVP5_REVIEW_ENTRY_MINIMUM_PAPER_SHADOW_WINDOW_COUNT = 0
SUPERSEDED_PROFILE_ID = "UPBIT_PAPER_SAFE_MONITOR_120H"
SUPERSEDED_DURATION_HOURS = 120
SUPERSEDED_HEARTBEAT_TICKS = 43200
SUPERSEDED_MINIMUM_PAPER_SHADOW_WINDOW_COUNT = 20
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


def build_residual_mvp5_entry_duration_policy_report(
    execution_guide_report: Mapping[str, Any],
    progress_report: Mapping[str, Any],
    preflight_report: Mapping[str, Any],
    intake_report: Mapping[str, Any],
    trial_duration_policy_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": [
            _source_report_ref("residual_operator_execution_guide", execution_guide_report),
            _source_report_ref("residual_operator_evidence_progress", progress_report),
            _source_report_ref("residual_operator_evidence_run_preflight", preflight_report),
            _source_report_ref("residual_operator_evidence_intake_audit", intake_report),
            _source_report_ref("residual_operator_evidence_trial_duration_policy", trial_duration_policy_report),
        ],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "duration_policy_status": "FIXED_DURATION_GATE_REMOVED_LIVE_STILL_BLOCKED",
        "superseded_profile_id": SUPERSEDED_PROFILE_ID,
        "superseded_duration_hours": SUPERSEDED_DURATION_HOURS,
        "superseded_heartbeat_ticks": SUPERSEDED_HEARTBEAT_TICKS,
        "superseded_minimum_paper_shadow_window_count": SUPERSEDED_MINIMUM_PAPER_SHADOW_WINDOW_COUNT,
        "mvp5_review_entry_profile_id": MVP5_REVIEW_ENTRY_PROFILE_ID,
        "mvp5_review_entry_duration_hours": MVP5_REVIEW_ENTRY_DURATION_HOURS,
        "mvp5_review_entry_heartbeat_ticks": MVP5_REVIEW_ENTRY_HEARTBEAT_TICKS,
        "mvp5_review_entry_heartbeat_interval_seconds": MVP5_REVIEW_ENTRY_HEARTBEAT_INTERVAL_SECONDS,
        "mvp5_review_entry_minimum_paper_shadow_window_count": (
            MVP5_REVIEW_ENTRY_MINIMUM_PAPER_SHADOW_WINDOW_COUNT
        ),
        "mvp5_review_entry_command_text": str(preflight_report.get("command_text", "")),
        "mvp5_review_entry_gate_type": "ADAPTIVE_EVIDENCE_QUALITY_GATE",
        "mvp5_review_entry_lowered_by_this_patch": True,
        "fixed_duration_gate_removed_by_this_patch": True,
        "adaptive_evidence_gate_enabled": True,
        "adaptive_stepwise_judgement_required": True,
        "trial_24h_profile_still_not_mvp5_eligible": True,
        "extended_48h_or_120h_profile_role": "OPTIONAL_OPERATOR_BURN_IN_REFERENCE_ONLY",
        "extended_120h_profile_role": "OPTIONAL_EXTENDED_OBSERVATION_OR_SCALE_UP_CONFIDENCE_ONLY",
        "duration_only_live_ready_allowed": False,
        "duration_only_gap_closure_allowed": False,
        "duration_only_current_evidence_write_allowed": False,
        "external_live_evidence_still_required": True,
        "operator_submission_required": True,
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


def validate_residual_mvp5_entry_duration_policy_report(
    report: Mapping[str, Any],
    execution_guide_report: Mapping[str, Any],
    progress_report: Mapping[str, Any],
    preflight_report: Mapping[str, Any],
    intake_report: Mapping[str, Any],
    trial_duration_policy_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if report.get("duration_policy_status") != "FIXED_DURATION_GATE_REMOVED_LIVE_STILL_BLOCKED":
        errors.append("duration policy status mismatch")
    if report.get("open_gap_ids") != sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", [])):
        errors.append("open_gap_ids must match current state")
    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")

    if preflight_report.get("command_id") != MVP5_REVIEW_ENTRY_PROFILE_ID:
        errors.append("preflight must use the adaptive evidence review profile")
    if preflight_report.get("minimum_duration_hours") != MVP5_REVIEW_ENTRY_DURATION_HOURS:
        errors.append("preflight duration must be 0h for adaptive evidence review")
    if preflight_report.get("expected_heartbeat_ticks") != MVP5_REVIEW_ENTRY_HEARTBEAT_TICKS:
        errors.append("preflight heartbeat ticks must be 0 for adaptive evidence review")
    if preflight_report.get("minimum_paper_shadow_window_count") != MVP5_REVIEW_ENTRY_MINIMUM_PAPER_SHADOW_WINDOW_COUNT:
        errors.append("preflight PAPER/SHADOW window count must be 0 for adaptive evidence review")
    if execution_guide_report.get("execution_steps"):
        paper_steps = [
            item
            for item in execution_guide_report.get("execution_steps", [])
            if isinstance(item, Mapping) and item.get("action_class") == "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION"
        ]
        if not paper_steps or paper_steps[0].get("minimum_observation_hours") != MVP5_REVIEW_ENTRY_DURATION_HOURS:
            errors.append("execution guide must expose adaptive evidence review without a fixed observation duration")
    if progress_report.get("minimum_observation_hours_required") != MVP5_REVIEW_ENTRY_DURATION_HOURS:
        errors.append("progress report must expose adaptive evidence review without a fixed observation duration")
    if intake_report.get("minimum_duration_hours") != MVP5_REVIEW_ENTRY_DURATION_HOURS:
        errors.append("intake audit must mirror the adaptive preflight duration")
    if trial_duration_policy_report.get("formal_mvp5_duration_hours") != MVP5_REVIEW_ENTRY_DURATION_HOURS:
        errors.append("trial duration policy must mirror the adaptive MVP5 profile")
    if "TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS=''" not in str(report.get("mvp5_review_entry_command_text", "")):
        errors.append("MVP5 review-entry command must leave heartbeat ticks empty for adaptive evidence review")
    if report.get("mvp5_review_entry_gate_type") != "ADAPTIVE_EVIDENCE_QUALITY_GATE":
        errors.append("MVP5 review-entry gate type must be adaptive evidence quality")

    true_fields = (
        "mvp5_review_entry_lowered_by_this_patch",
        "fixed_duration_gate_removed_by_this_patch",
        "adaptive_evidence_gate_enabled",
        "adaptive_stepwise_judgement_required",
        "trial_24h_profile_still_not_mvp5_eligible",
        "external_live_evidence_still_required",
        "operator_submission_required",
        "mvp5_entry_blocked_until_operator_evidence",
    )
    for field in true_fields:
        if report.get(field) is not True:
            errors.append(f"{field} must remain true")
    false_fields = (
        "duration_only_live_ready_allowed",
        "duration_only_gap_closure_allowed",
        "duration_only_current_evidence_write_allowed",
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
    if report.get("superseded_duration_hours") != SUPERSEDED_DURATION_HOURS:
        errors.append("superseded duration must preserve the 120h reference")
    if report.get("mvp5_review_entry_duration_hours") != MVP5_REVIEW_ENTRY_DURATION_HOURS:
        errors.append("MVP5 review-entry duration must be 0h for adaptive evidence review")
    if report.get("mvp5_review_entry_heartbeat_ticks") != MVP5_REVIEW_ENTRY_HEARTBEAT_TICKS:
        errors.append("MVP5 review-entry heartbeat ticks must be 0 for adaptive evidence review")
    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
