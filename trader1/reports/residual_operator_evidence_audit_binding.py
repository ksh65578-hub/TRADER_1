from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_open_gap_operator_action_plan import (
    FORBIDDEN_ACTIONS,
    validate_residual_open_gap_operator_action_plan_report,
)
from trader1.reports.residual_paper_ledger_rerun_readiness import LEDGER_RERUN_GAP_IDS


SCHEMA_ID = "trader1.residual_operator_evidence_audit_binding_report.v1"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

SOURCE_REPORT_ROLES = (
    "open_gap_current_blocker_classification",
    "residual_open_gap_operator_action_plan",
    "residual_paper_ledger_rerun_readiness",
)

ACTION_AUDIT_REQUIREMENTS = {
    "OPERATOR_RECONCILIATION_ACTION": {
        "required_evidence_kinds": [
            "operator_reconciliation_audit",
            "repair_candidate_hash_review",
            "ledger_recovery_reconciliation",
        ],
        "required_operator_action": "Review repaired, regenerated, and hash-mismatched evidence before any promotion.",
        "closure_preconditions": [
            "operator reconciliation artifact PASS for the exact exchange, market_type, mode, and session",
            "candidate evidence hashes match the source artifacts under review",
            "current evidence write remains blocked until reconciliation explicitly resolves the gap",
        ],
    },
    "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION": {
        "required_evidence_kinds": [
            "bounded_paper_rerun_output",
            "post_rerun_ledger_rollup",
            "post_rerun_operator_reconciliation",
        ],
        "required_operator_action": "Use PAPER-only rerun outputs as candidates until post-rerun reconciliation passes.",
        "closure_preconditions": [
            "bounded staging report PASS",
            "post-rerun ledger rollup report PASS",
            "post-rerun reconciliation report PASS before current evidence promotion",
        ],
    },
    "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION": {
        "required_evidence_kinds": [
            "long_run_paper_shadow_runtime_evidence",
            "shadow_observation_evidence",
            "profitability_maturity_evidence",
        ],
        "required_operator_action": "Collect longer PAPER/SHADOW evidence without credentials or live order paths.",
        "closure_preconditions": [
            "long-run PAPER/SHADOW evidence satisfies the required runtime boundary",
            "shadow observation and profitability maturity validators pass",
            "evidence is not inferred across exchange, market_type, mode, or session",
        ],
    },
    "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION": {
        "required_evidence_kinds": [
            "official_api_verification",
            "read_only_account_snapshot",
            "live_burn_in_feedback",
            "operator_approval",
        ],
        "required_operator_action": "Provide independent live-readiness evidence outside this non-live patch path.",
        "closure_preconditions": [
            "external live-readiness evidence exists for the exact scope",
            "all live-blocking validators pass independently",
            "a separate reviewed LIVE_ENABLING path is required before live permission can change",
        ],
    },
    "SEALED_BASELINE_PRESERVATION_ACTION": {
        "required_evidence_kinds": ["sealed_patch_result_baseline_reconciliation"],
        "required_operator_action": "Preserve sealed validator-run history; do not rewrite historical baselines by inference.",
        "closure_preconditions": [
            "sealed baseline status remains explicit",
            "historical patch_result validator-run gaps are not rewritten",
        ],
    },
    "SCALE_UP_POLICY_EVIDENCE_ACTION": {
        "required_evidence_kinds": [
            "scale_up_eligibility_validation",
            "live_burn_in_parity",
            "survival_layer_evidence",
            "operator_policy_permission",
        ],
        "required_operator_action": "Keep scale-up disabled until validators and operator policy pass for the exact scope.",
        "closure_preconditions": [
            "scale_up_eligibility_validator PASS",
            "burn-in, paper/live parity, survival layer, and operator policy evidence PASS",
            "scale-up is never enabled by optimizer score alone",
        ],
    },
    "CLASSIFY_OPEN_GAP_ACTION": {
        "required_evidence_kinds": ["closed_gap_category_mapping"],
        "required_operator_action": "Classify the open gap before selecting an evidence path.",
        "closure_preconditions": ["gap is mapped to a closed blocker category"],
    },
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


def _source_report_refs(
    classification_report: Mapping[str, Any],
    action_plan_report: Mapping[str, Any],
    paper_rerun_readiness_report: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        _source_report_ref("open_gap_current_blocker_classification", classification_report),
        _source_report_ref("residual_open_gap_operator_action_plan", action_plan_report),
        _source_report_ref("residual_paper_ledger_rerun_readiness", paper_rerun_readiness_report),
    ]


def _binding_source_roles(action_class: str) -> list[str]:
    roles = [
        "open_gap_current_blocker_classification",
        "residual_open_gap_operator_action_plan",
    ]
    if action_class == "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION":
        roles.append("residual_paper_ledger_rerun_readiness")
    return roles


def _safe_action_item(item: Mapping[str, Any]) -> bool:
    return (
        item.get("allows_live_order") is False
        and item.get("allows_live_config_mutation") is False
        and item.get("allows_scale_up") is False
    )


def _build_audit_binding(action: Mapping[str, Any]) -> dict[str, Any]:
    action_class = str(action.get("action_class", "CLASSIFY_OPEN_GAP_ACTION"))
    requirement = ACTION_AUDIT_REQUIREMENTS.get(action_class, ACTION_AUDIT_REQUIREMENTS["CLASSIFY_OPEN_GAP_ACTION"])
    gap_ids = sorted(str(gap_id) for gap_id in action.get("gap_ids", []))
    source_categories = [str(category) for category in action.get("source_categories", [])]
    forbidden_actions = list(action.get("forbidden_actions", []))
    return {
        "action_class": action_class,
        "priority": int(action.get("priority", 999) or 999),
        "gap_ids": gap_ids,
        "gap_count": len(gap_ids),
        "source_categories": source_categories,
        "required_evidence_kinds": list(requirement["required_evidence_kinds"]),
        "required_operator_action": str(requirement["required_operator_action"]),
        "closure_preconditions": list(requirement["closure_preconditions"]),
        "audit_source_report_roles": _binding_source_roles(action_class),
        "audit_binding_status": "BOUND_BLOCKED" if _safe_action_item(action) else "FAIL_UNSAFE_PERMISSION",
        "gap_closure_allowed_by_this_patch": False,
        "current_evidence_write_allowed": False,
        "live_order_allowed": False,
        "live_config_mutation_allowed": False,
        "scale_up_allowed": False,
        "forbidden_actions": forbidden_actions,
    }


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def build_residual_operator_evidence_audit_binding_report(
    classification_report: Mapping[str, Any],
    action_plan_report: Mapping[str, Any],
    paper_rerun_readiness_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    audit_bindings = [
        _build_audit_binding(action)
        for action in action_plan_report.get("action_items", [])
        if isinstance(action, Mapping)
    ]
    bound_gap_ids = sorted(gap_id for binding in audit_bindings for gap_id in binding["gap_ids"])
    duplicate_bound_gap_ids = _duplicates(bound_gap_ids)
    unbound_gap_ids = sorted(set(open_gap_ids) - set(bound_gap_ids))
    extra_bound_gap_ids = sorted(set(bound_gap_ids) - set(open_gap_ids))
    readiness_status = str(paper_rerun_readiness_report.get("readiness_status", "UNKNOWN"))

    status_inputs_pass = (
        not unbound_gap_ids
        and not extra_bound_gap_ids
        and not duplicate_bound_gap_ids
        and all(binding["audit_binding_status"] == "BOUND_BLOCKED" for binding in audit_bindings)
        and readiness_status == "BLOCKED_RECONCILIATION_REQUIRED"
    )

    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": _source_report_refs(
            classification_report,
            action_plan_report,
            paper_rerun_readiness_report,
        ),
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "bound_gap_ids": bound_gap_ids,
        "bound_gap_count": len(bound_gap_ids),
        "unbound_gap_ids": unbound_gap_ids,
        "extra_bound_gap_ids": extra_bound_gap_ids,
        "duplicate_bound_gap_ids": duplicate_bound_gap_ids,
        "action_binding_count": len(audit_bindings),
        "implementation_recheck_action_count": int(action_plan_report.get("implementation_recheck_action_count", -1)),
        "external_or_operator_action_required": action_plan_report.get("external_or_operator_action_required") is True,
        "paper_ledger_rerun_gap_ids": list(LEDGER_RERUN_GAP_IDS),
        "paper_ledger_rerun_readiness_status": readiness_status,
        "post_rerun_reconciliation_status": str(
            paper_rerun_readiness_report.get("post_rerun_reconciliation_status", "UNKNOWN")
        ),
        "current_evidence_bridge_status": str(
            paper_rerun_readiness_report.get("current_evidence_bridge_status", "UNKNOWN")
        ),
        "operator_queue_status": str(paper_rerun_readiness_report.get("operator_queue_status", "UNKNOWN")),
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "open_gaps_preserved": True,
        "audit_bindings": audit_bindings,
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "audit_binding_status": "PASS_BOUND_BLOCKED" if status_inputs_pass else "FAIL",
        "validation_status": "PASS" if status_inputs_pass else "FAIL",
        "validation_errors": [],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_residual_operator_evidence_audit_binding_report(
    report: Mapping[str, Any],
    classification_report: Mapping[str, Any],
    action_plan_report: Mapping[str, Any],
    paper_rerun_readiness_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []

    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        for name, source in (
            ("classification", classification_report),
            ("action_plan", action_plan_report),
            ("paper_rerun_readiness", paper_rerun_readiness_report),
        ):
            if source.get(field) is not False:
                errors.append(f"{name} {field} must remain false")

    for field in (
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "latest_runtime_pointer_write_allowed",
        "gap_closure_allowed_by_this_patch",
    ):
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")

    action_plan_errors = validate_residual_open_gap_operator_action_plan_report(
        action_plan_report,
        classification_report,
        state,
    )
    errors.extend(f"action_plan: {error}" for error in action_plan_errors)

    expected_refs = _source_report_refs(classification_report, action_plan_report, paper_rerun_readiness_report)
    if report.get("source_reports") != expected_refs:
        errors.append("source_reports must bind exact source report ids and hashes")

    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids:
        errors.append("open_gap_ids must match current implementation state")
    if report.get("open_gap_count") != len(open_gap_ids):
        errors.append("open_gap_count mismatch")
    if report.get("bound_gap_ids") != open_gap_ids:
        errors.append("bound_gap_ids must cover every current open gap exactly once")
    if report.get("bound_gap_count") != len(open_gap_ids):
        errors.append("bound_gap_count mismatch")
    if report.get("unbound_gap_ids") != []:
        errors.append("unbound_gap_ids must be empty")
    if report.get("extra_bound_gap_ids") != []:
        errors.append("extra_bound_gap_ids must be empty")
    if report.get("duplicate_bound_gap_ids") != []:
        errors.append("duplicate_bound_gap_ids must be empty")
    if report.get("implementation_recheck_action_count") != 0:
        errors.append("implementation_recheck_action_count must remain 0")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if report.get("open_gaps_preserved") is not True:
        errors.append("open_gaps_preserved must be true")
    if tuple(report.get("paper_ledger_rerun_gap_ids", [])) != LEDGER_RERUN_GAP_IDS:
        errors.append("paper_ledger_rerun_gap_ids mismatch")
    if report.get("paper_ledger_rerun_readiness_status") != "BLOCKED_RECONCILIATION_REQUIRED":
        errors.append("paper_ledger_rerun_readiness_status must remain BLOCKED_RECONCILIATION_REQUIRED")
    if report.get("post_rerun_reconciliation_status") != "BLOCKED":
        errors.append("post_rerun_reconciliation_status must remain BLOCKED")
    if report.get("current_evidence_bridge_status") != "BLOCKED_BY_POST_RERUN_CLOSURE":
        errors.append("current_evidence_bridge_status must remain BLOCKED_BY_POST_RERUN_CLOSURE")
    if paper_rerun_readiness_report.get("current_evidence_write_allowed") is not False:
        errors.append("source paper rerun readiness must keep current_evidence_write_allowed=false")

    seen_gap_ids: list[str] = []
    for binding in report.get("audit_bindings", []):
        if not isinstance(binding, Mapping):
            errors.append("audit_bindings contains a non-object item")
            continue
        action_class = str(binding.get("action_class", ""))
        if action_class not in ACTION_AUDIT_REQUIREMENTS:
            errors.append(f"unknown action_class in audit binding: {action_class}")
        seen_gap_ids.extend(str(gap_id) for gap_id in binding.get("gap_ids", []))
        if binding.get("audit_binding_status") != "BOUND_BLOCKED":
            errors.append(f"{action_class} audit_binding_status must be BOUND_BLOCKED")
        for field in (
            "gap_closure_allowed_by_this_patch",
            "current_evidence_write_allowed",
            "live_order_allowed",
            "live_config_mutation_allowed",
            "scale_up_allowed",
        ):
            if binding.get(field) is not False:
                errors.append(f"{action_class} {field} must remain false")
        forbidden = set(binding.get("forbidden_actions", []))
        if not set(FORBIDDEN_ACTIONS).issubset(forbidden):
            errors.append(f"{action_class} missing forbidden actions")
        expected_roles = _binding_source_roles(action_class)
        if binding.get("audit_source_report_roles") != expected_roles:
            errors.append(f"{action_class} audit_source_report_roles mismatch")

    if sorted(seen_gap_ids) != open_gap_ids:
        errors.append("audit_bindings must cover current open gaps exactly once")
    if report.get("audit_binding_status") != "PASS_BOUND_BLOCKED":
        errors.append("audit_binding_status must be PASS_BOUND_BLOCKED")
    if report.get("validation_status") != "PASS":
        errors.append("validation_status must be PASS")
    if report.get("validation_errors") != []:
        errors.append("validation_errors must be empty")

    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
