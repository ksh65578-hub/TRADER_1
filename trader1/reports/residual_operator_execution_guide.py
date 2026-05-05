from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS


SCHEMA_ID = "trader1.residual_operator_execution_guide_report.v1"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

STEP_MODE_BY_ACTION = {
    "OPERATOR_RECONCILIATION_ACTION": "OPERATOR_REVIEW_REQUIRED",
    "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION": "PAPER_RERUN_RECONCILIATION_BLOCKED",
    "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION": "LOCAL_PAPER_SHADOW_RUNTIME_ALLOWED",
    "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION": "EXTERNAL_EVIDENCE_REQUIRED",
    "SEALED_BASELINE_PRESERVATION_ACTION": "PRESERVE_BASELINE_ONLY",
    "SCALE_UP_POLICY_EVIDENCE_ACTION": "POLICY_EVIDENCE_REQUIRED",
}

VALIDATORS_BY_ACTION = {
    "OPERATOR_RECONCILIATION_ACTION": [
        "operator_action_audit_validator",
        "ledger_reconciliation_validator",
        "live_final_guard_validator",
    ],
    "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION": [
        "upbit_paper_bounded_rerun_staging_executor_validator",
        "upbit_paper_post_rerun_ledger_rollup_reconciliation_validator",
        "upbit_paper_post_rerun_operator_reconciliation_queue_validator",
        "live_final_guard_validator",
    ],
    "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION": [
        "upbit_paper_persistent_loop_validator",
        "shadow_observation_persistent_runtime_validator",
        "paper_shadow_evidence_accumulation_validator",
        "profitability_evidence_maturity_rollup_validator",
        "runtime_schema_instance_validator",
        "live_final_guard_validator",
    ],
    "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION": [
        "official_api_verification_validator",
        "readiness_surface_validator",
        "live_burn_in_feedback_validator",
        "operator_control_validator",
        "live_final_guard_validator",
    ],
    "SEALED_BASELINE_PRESERVATION_ACTION": [
        "patch_result_runtime_schema_instance_validator",
        "patch_result_schema_validator",
        "live_final_guard_validator",
    ],
    "SCALE_UP_POLICY_EVIDENCE_ACTION": [
        "scale_up_eligibility_validator",
        "risk_scaling_decision_validator",
        "survival_layer_validator",
        "operator_control_validator",
        "live_final_guard_validator",
    ],
}

ARTIFACTS_BY_ACTION = {
    "OPERATOR_RECONCILIATION_ACTION": [
        "system/evidence/audit_reports/operator_reconciliation_audit.json",
        "system/evidence/audit_reports/repair_candidate_hash_review.json",
        "system/evidence/audit_reports/ledger_recovery_reconciliation.json",
    ],
    "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION": [
        "system/evidence/audit_reports/MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS.report.json",
        "system/runtime/upbit/krw_spot/paper/<session_id>/paper_runtime/post_rerun_ledger_rollup.json",
        "system/runtime/upbit/krw_spot/paper/<session_id>/paper_runtime/post_rerun_reconciliation_report.json",
    ],
    "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION": [
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/heartbeat.json",
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/summary.json",
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_persistent_loop_report.json",
        "system/runtime/upbit/krw_spot/shadow/<shadow_session_id>/shadow_observation_persistent_runtime_report.json",
        "system/evidence/audit_reports/paper_shadow_evidence_accumulation_report.json",
    ],
    "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION": [
        "system/evidence/external/official_api_verification_report.json",
        "system/evidence/external/read_only_account_snapshot.json",
        "system/evidence/external/live_burn_in_feedback_report.json",
        "system/evidence/external/operator_approval.json",
    ],
    "SEALED_BASELINE_PRESERVATION_ACTION": [
        "system/evidence/audit_reports/PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE.json",
        "system/evidence/audit_reports/PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json",
    ],
    "SCALE_UP_POLICY_EVIDENCE_ACTION": [
        "system/evidence/external/scale_up_eligibility_validation.json",
        "system/evidence/external/survival_layer_evidence.json",
        "system/evidence/external/operator_policy_permission.json",
    ],
}


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _source_report_ref(role: str, report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "role": role,
        "patch_id": str(report.get("patch_id", "")),
        "report_hash": str(report.get("report_hash", "")),
    }


def _allowed_local_commands(action_class: str) -> list[dict[str, Any]]:
    if action_class != "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION":
        return []
    return [
        {
            "command_id": "UPBIT_PAPER_SAFE_MONITOR_120H",
            "shell": "powershell",
            "command": (
                "$env:TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS='43200'; "
                "$env:TRADER1_ROOT_OPERATOR_HEARTBEAT_INTERVAL_SECONDS='10'; "
                "python -B UPBIT_PAPER.py"
            ),
            "scope": "UPBIT/KRW_SPOT/PAPER",
            "minimum_duration_hours": 120,
            "non_live_only": True,
            "credential_required": False,
            "live_order_allowed": False,
        }
    ]


def _operator_goal(packet: Mapping[str, Any]) -> str:
    action_class = str(packet.get("action_class", ""))
    if action_class == "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION":
        return "Collect long-run UPBIT PAPER plus SHADOW evidence without credentials or live order paths."
    if action_class == "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION":
        return "Prepare bounded PAPER rerun and post-rerun reconciliation evidence before any current evidence promotion."
    if action_class == "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION":
        return "Submit independent official API, read-only account, burn-in, and operator approval evidence outside this patch."
    return str(packet.get("required_operator_action", "Resolve this blocked handoff packet."))


def _build_execution_step(packet: Mapping[str, Any]) -> dict[str, Any]:
    action_class = str(packet.get("action_class", ""))
    commands = _allowed_local_commands(action_class)
    return {
        "step_id": f"EXECUTION_GUIDE:{action_class}",
        "packet_id": str(packet.get("packet_id", "")),
        "action_class": action_class,
        "handoff_type": str(packet.get("handoff_type", "")),
        "priority": int(packet.get("priority", 999) or 999),
        "operator_action_mode": STEP_MODE_BY_ACTION.get(action_class, "OPERATOR_REVIEW_REQUIRED"),
        "operator_goal": _operator_goal(packet),
        "gap_ids": sorted(str(gap_id) for gap_id in packet.get("gap_ids", [])),
        "gap_count": int(packet.get("gap_count", 0) or 0),
        "allowed_local_commands": commands,
        "required_evidence_artifacts": ARTIFACTS_BY_ACTION.get(action_class, []),
        "validators_required_for_next_review": VALIDATORS_BY_ACTION.get(action_class, ["live_final_guard_validator"]),
        "minimum_observation_hours": 120 if action_class == "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION" else 0,
        "minimum_paper_shadow_window_count": 20 if action_class == "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION" else 0,
        "forbidden_actions": [
            "LIVE_ORDER",
            "CREDENTIAL_OR_API_KEY_USE",
            "LIVE_CONFIG_MUTATION",
            "CURRENT_EVIDENCE_WRITE",
            "GAP_CLOSURE_BY_GUIDE",
            "RISK_SCALE_UP",
            "LIVE_READY_WRITE",
        ],
        "execution_status": "BLOCKED_GUIDE_ONLY",
        "evidence_ready_for_closure": False,
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_residual_operator_execution_guide_report(
    handoff_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    packets = [packet for packet in handoff_report.get("handoff_packets", []) if isinstance(packet, Mapping)]
    steps = [_build_execution_step(packet) for packet in packets]
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    covered_gap_ids = sorted(gap_id for step in steps for gap_id in step["gap_ids"])
    paper_shadow_steps = [
        step for step in steps if step["operator_action_mode"] == "LOCAL_PAPER_SHADOW_RUNTIME_ALLOWED"
    ]
    external_steps = [
        step for step in steps if step["operator_action_mode"] in {"EXTERNAL_EVIDENCE_REQUIRED", "POLICY_EVIDENCE_REQUIRED"}
    ]
    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": [_source_report_ref("residual_operator_handoff_packet", handoff_report)],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "covered_gap_ids": covered_gap_ids,
        "covered_gap_count": len(covered_gap_ids),
        "handoff_packet_count": int(handoff_report.get("handoff_packet_count", len(packets)) or 0),
        "execution_step_count": len(steps),
        "local_paper_shadow_runtime_step_count": len(paper_shadow_steps),
        "external_or_policy_evidence_step_count": len(external_steps),
        "operator_runtime_required_before_mvp5": True,
        "mvp5_entry_blocked_until_operator_evidence": True,
        "binance_runtime_status": "SCAFFOLD_ONLY_NOT_ELIGIBLE_FOR_READINESS",
        "execution_steps": steps,
        "guide_status": "BLOCKED_GUIDE_ONLY",
        "validation_status": "PASS",
        "validation_errors": [],
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_config_mutation_allowed": False,
        "live_ready_write_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_residual_operator_execution_guide_report(
    report: Mapping[str, Any],
    handoff_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if handoff_report.get("handoff_status") != "BLOCKED_HANDOFF_REQUIRED":
        errors.append("source handoff report must remain blocked")
    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        if handoff_report.get(field) is not False:
            errors.append(f"handoff {field} must remain false")
    for field in (
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_config_mutation_allowed",
        "live_ready_write_allowed",
    ):
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids:
        errors.append("open_gap_ids must match current state")
    if report.get("covered_gap_ids") != open_gap_ids:
        errors.append("execution guide must cover each open gap exactly once")
    packets = [packet for packet in handoff_report.get("handoff_packets", []) if isinstance(packet, Mapping)]
    steps = report.get("execution_steps", [])
    if not isinstance(steps, list):
        return errors + ["execution_steps must be an array"]
    if report.get("execution_step_count") != len(steps) or len(steps) != len(packets):
        errors.append("execution_step_count must match handoff packets")
    local_step_count = 0
    for step in steps:
        if not isinstance(step, Mapping):
            errors.append("execution step must be object")
            continue
        action_class = str(step.get("action_class", ""))
        if step.get("execution_status") != "BLOCKED_GUIDE_ONLY":
            errors.append(f"{action_class} execution_status must remain BLOCKED_GUIDE_ONLY")
        if step.get("evidence_ready_for_closure") is not False:
            errors.append(f"{action_class} evidence_ready_for_closure must remain false")
        for field in (
            "current_evidence_write_allowed",
            "gap_closure_allowed_by_this_patch",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            if step.get(field) is not False:
                errors.append(f"{action_class} {field} must remain false")
        commands = step.get("allowed_local_commands", [])
        if not isinstance(commands, list):
            errors.append(f"{action_class} allowed_local_commands must be array")
            continue
        if step.get("operator_action_mode") == "LOCAL_PAPER_SHADOW_RUNTIME_ALLOWED":
            local_step_count += 1
            if len(commands) != 1:
                errors.append("paper/shadow runtime step must expose exactly one safe local command")
        elif commands:
            errors.append(f"{action_class} must not expose local commands")
        for command in commands:
            if not isinstance(command, Mapping):
                errors.append(f"{action_class} command must be object")
                continue
            command_text = str(command.get("command", ""))
            if "LIVE" in command_text.upper() or "API_KEY" in command_text.upper():
                errors.append(f"{action_class} command must not reference live/API key paths")
            if command.get("credential_required") is not False or command.get("live_order_allowed") is not False:
                errors.append(f"{action_class} command must remain non-live and credential-free")
    if local_step_count != 1 or report.get("local_paper_shadow_runtime_step_count") != 1:
        errors.append("exactly one local PAPER/SHADOW runtime guide step is allowed")
    if report.get("guide_status") != "BLOCKED_GUIDE_ONLY":
        errors.append("guide_status must remain BLOCKED_GUIDE_ONLY")
    if report.get("validation_status") != "PASS":
        errors.append("validation_status must be PASS")
    if report.get("validation_errors") != []:
        errors.append("validation_errors must be empty")
    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
