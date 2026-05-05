from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_evidence_audit_binding import (
    SCHEMA_ID as AUDIT_BINDING_SCHEMA_ID,
    validate_residual_operator_evidence_audit_binding_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_resolution_audit import (
    POST_RERUN_OPERATOR_RESOLUTION_AUDIT_STATUS,
    POST_RERUN_OPERATOR_RESOLUTION_ITEM_STATUS,
    UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT_SCHEMA_ID,
    validate_upbit_paper_post_rerun_operator_resolution_audit_report,
)


SCHEMA_ID = "trader1.residual_operator_reconciliation_review_cards_report.v1"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
OPERATOR_RECONCILIATION_ACTION_CLASS = "OPERATOR_RECONCILIATION_ACTION"
REVIEW_STATUS = "BLOCKED_RECONCILIATION_REVIEW_ONLY"
REVIEW_CARD_STATUS = "BLOCKED_REVIEW_ONLY"
CONTROL_CARD_STATUS = "UNSATISFIED_BLOCKING_CONTROL"


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _source_report_ref(role: str, report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "role": role,
        "patch_id": str(report.get("patch_id", "")),
        "report_hash": str(report.get("report_hash", report.get("resolution_audit_hash", ""))),
    }


def _operator_action_binding(audit_binding_report: Mapping[str, Any]) -> Mapping[str, Any]:
    for binding in audit_binding_report.get("audit_bindings", []):
        if isinstance(binding, Mapping) and binding.get("action_class") == OPERATOR_RECONCILIATION_ACTION_CLASS:
            return binding
    return {}


def _false_permission_fields(value: Mapping[str, Any]) -> list[str]:
    fields = [
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_permission_created",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
        "candidate_current_evidence_usable",
        "current_evidence_write_authorized",
        "resolution_evidence_present",
        "resolution_evidence_accepted",
    ]
    return [field for field in fields if value.get(field) is True]


def _review_card(item: Mapping[str, Any]) -> dict[str, Any]:
    priority = int(item.get("priority_order", 999) or 999)
    required_resolution_evidence = [str(value) for value in item.get("required_resolution_evidence", [])]
    blocking_codes = sorted(str(value) for value in item.get("blocking_codes", []) if value)
    cycle_id = str(item.get("cycle_id", "UNKNOWN"))
    return {
        "review_card_id": f"OPERATOR_RECONCILIATION_REVIEW:{priority}:{cycle_id}",
        "priority_order": priority,
        "cycle_id": cycle_id,
        "replacement_loop_id": str(item.get("replacement_loop_id", "UNKNOWN")),
        "candidate_rollup_artifact_path": str(item.get("candidate_rollup_artifact_path", "")),
        "decision_candidate_rollup_hash": str(item.get("decision_candidate_rollup_hash", "")),
        "planned_current_ledger_jsonl_path": str(item.get("planned_current_ledger_jsonl_path", "")),
        "source_guidance_review_status": str(item.get("source_guidance_review_status", "UNKNOWN")),
        "source_decision_status": str(item.get("source_decision_status", "UNKNOWN")),
        "resolution_status": str(item.get("resolution_status", "UNKNOWN")),
        "resolution_reason_code": str(item.get("resolution_reason_code", "UNKNOWN")),
        "path_scope_status": str(item.get("path_scope_status", "UNKNOWN")),
        "required_resolution_evidence": required_resolution_evidence,
        "required_resolution_evidence_count": len(required_resolution_evidence),
        "blocking_codes": blocking_codes,
        "blocking_code_count": len(blocking_codes),
        "review_status": REVIEW_CARD_STATUS,
        "next_safe_action": (
            "Review this source-bound candidate and keep current evidence, LIVE_READY, live orders, "
            "and scale-up blocked until separate reconciliation evidence passes."
        ),
        "resolution_evidence_present": False,
        "resolution_evidence_accepted": False,
        "candidate_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "current_evidence_write_authorized": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _control_card(control: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "control_id": str(control.get("control_id", "")),
        "control_order": int(control.get("control_order", 999) or 999),
        "blocker_code": str(control.get("blocker_code", "UNKNOWN")),
        "message": str(control.get("message", "")),
        "required": control.get("required") is True,
        "satisfied": False,
        "control_status": CONTROL_CARD_STATUS,
        "next_safe_action": "Keep this control blocked until validated operator reconciliation evidence satisfies it.",
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_residual_operator_reconciliation_review_cards_report(
    audit_binding_report: Mapping[str, Any],
    operator_resolution_audit_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    operator_binding = _operator_action_binding(audit_binding_report)
    operator_reconciliation_gap_ids = sorted(str(gap_id) for gap_id in operator_binding.get("gap_ids", []))
    items = sorted(
        [item for item in operator_resolution_audit_report.get("items", []) if isinstance(item, Mapping)],
        key=lambda item: int(item.get("priority_order", 999) or 999),
    )
    controls = sorted(
        [control for control in operator_resolution_audit_report.get("resolution_controls", []) if isinstance(control, Mapping)],
        key=lambda control: int(control.get("control_order", 999) or 999),
    )
    review_cards = [_review_card(item) for item in items]
    control_cards = [_control_card(control) for control in controls]
    single_next = review_cards[0] if review_cards else {}

    source_hashes_verified = (
        operator_resolution_audit_report.get("source_review_guidance_file_hash_match") is True
        and operator_resolution_audit_report.get("source_decision_audit_file_hash_match") is True
        and audit_binding_report.get("operator_resolution_source_review_guidance_file_hash_match") is True
        and audit_binding_report.get("operator_resolution_source_decision_audit_file_hash_match") is True
    )
    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": [
            _source_report_ref("residual_operator_evidence_audit_binding", audit_binding_report),
            _source_report_ref("upbit_paper_post_rerun_operator_resolution_audit", operator_resolution_audit_report),
        ],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "operator_reconciliation_gap_ids": operator_reconciliation_gap_ids,
        "operator_reconciliation_gap_count": len(operator_reconciliation_gap_ids),
        "operator_reconciliation_required_evidence_kinds": [
            str(value) for value in operator_binding.get("required_evidence_kinds", [])
        ],
        "operator_resolution_audit_loaded": True,
        "operator_resolution_audit_schema_id": str(operator_resolution_audit_report.get("schema_id", "UNKNOWN")),
        "operator_resolution_audit_hash": str(operator_resolution_audit_report.get("resolution_audit_hash", "")),
        "operator_resolution_audit_status": str(operator_resolution_audit_report.get("resolution_audit_status", "UNKNOWN")),
        "operator_resolution_audit_validation_status": validate_upbit_paper_post_rerun_operator_resolution_audit_report(
            dict(operator_resolution_audit_report)
        ).status,
        "operator_resolution_binding_status": str(audit_binding_report.get("operator_resolution_binding_status", "UNKNOWN")),
        "source_review_guidance_file_hash_match": operator_resolution_audit_report.get(
            "source_review_guidance_file_hash_match"
        )
        is True,
        "source_decision_audit_file_hash_match": operator_resolution_audit_report.get(
            "source_decision_audit_file_hash_match"
        )
        is True,
        "source_hashes_verified": source_hashes_verified,
        "operator_resolution_unresolved_item_count": int(operator_resolution_audit_report.get("unresolved_item_count") or 0),
        "operator_resolution_resolved_item_count": int(operator_resolution_audit_report.get("resolved_item_count") or 0),
        "operator_resolution_controls_satisfied_count": int(
            operator_resolution_audit_report.get("resolution_controls_satisfied_count") or 0
        ),
        "operator_resolution_current_evidence_write_allowed_count": int(
            operator_resolution_audit_report.get("current_evidence_write_allowed_count") or 0
        ),
        "operator_resolution_candidate_current_evidence_usable_count": int(
            operator_resolution_audit_report.get("candidate_current_evidence_usable_count") or 0
        ),
        "review_card_count": len(review_cards),
        "blocked_review_card_count": len(review_cards),
        "review_ready_count": 0,
        "control_card_count": len(control_cards),
        "unsatisfied_control_count": len(control_cards),
        "satisfied_control_count": 0,
        "single_next_review_card": single_next,
        "review_cards": review_cards,
        "control_cards": control_cards,
        "review_status": REVIEW_STATUS,
        "one_line_summary": (
            f"{len(review_cards)} operator reconciliation review cards remain blocked; "
            f"{len(control_cards)} controls are unsatisfied; current-evidence writes stay 0."
        ),
        "primary_next_action": (
            "Review the first operator reconciliation card and satisfy all controls with separate validated evidence; "
            "do not write current evidence or LIVE_READY from this report."
        ),
        "operator_no_action_needed_for_next_non_live_patch": True,
        "operator_action_required_for_gap_closure": True,
        "gap_closure_allowed_by_this_patch": False,
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "live_ready_write_allowed": False,
        "live_config_mutation_allowed": False,
        "open_gaps_preserved": True,
        "validation_status": "PASS",
        "validation_errors": [],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_residual_operator_reconciliation_review_cards_report(
    report: Mapping[str, Any],
    audit_binding_report: Mapping[str, Any],
    operator_resolution_audit_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if report.get("review_status") != REVIEW_STATUS:
        errors.append("review_status must remain blocked review-only")
    if audit_binding_report.get("schema_id") != AUDIT_BINDING_SCHEMA_ID:
        errors.append("audit binding source schema mismatch")
    binding_validation = validate_residual_operator_evidence_audit_binding_report(
        audit_binding_report,
        {"live_order_ready": False, "live_order_allowed": False, "can_live_trade": False, "scale_up_allowed": False},
        {"action_items": [], "live_order_ready": False, "live_order_allowed": False, "can_live_trade": False, "scale_up_allowed": False},
        {"live_order_ready": False, "live_order_allowed": False, "can_live_trade": False, "scale_up_allowed": False},
        state,
        operator_resolution_audit_report,
    )
    if audit_binding_report.get("validation_status") != "PASS" or audit_binding_report.get("audit_binding_status") != "PASS_BOUND_BLOCKED":
        errors.append("audit binding source must be PASS_BOUND_BLOCKED")
    if binding_validation and audit_binding_report.get("operator_resolution_binding_status") != "BOUND_BLOCKED":
        errors.append("audit binding source failed operator resolution binding")
    resolution_validation = validate_upbit_paper_post_rerun_operator_resolution_audit_report(
        dict(operator_resolution_audit_report)
    )
    if resolution_validation.status != "PASS":
        errors.append("operator resolution audit source must validate PASS")
    if operator_resolution_audit_report.get("schema_id") != UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT_SCHEMA_ID:
        errors.append("operator resolution audit schema mismatch")
    if operator_resolution_audit_report.get("resolution_audit_status") != POST_RERUN_OPERATOR_RESOLUTION_AUDIT_STATUS:
        errors.append("operator resolution audit must remain unresolved")

    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        if audit_binding_report.get(field) is not False:
            errors.append(f"audit binding {field} must remain false")
        if operator_resolution_audit_report.get(field) is not False:
            errors.append(f"operator resolution audit {field} must remain false")
    for field in (
        "gap_closure_allowed_by_this_patch",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "latest_runtime_pointer_write_allowed",
        "current_ledger_jsonl_write_allowed",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
    ):
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")

    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids or report.get("open_gap_count") != len(open_gap_ids):
        errors.append("open gap ids/count must match current implementation state")
    operator_binding = _operator_action_binding(audit_binding_report)
    expected_operator_gap_ids = sorted(str(gap_id) for gap_id in operator_binding.get("gap_ids", []))
    if report.get("operator_reconciliation_gap_ids") != expected_operator_gap_ids:
        errors.append("operator reconciliation gap ids must match audit binding")
    if report.get("operator_resolution_binding_status") != "BOUND_BLOCKED":
        errors.append("operator_resolution_binding_status must be BOUND_BLOCKED")
    if report.get("source_hashes_verified") is not True:
        errors.append("source_hashes_verified must be true")
    if report.get("operator_resolution_unresolved_item_count") != operator_resolution_audit_report.get("unresolved_item_count"):
        errors.append("operator resolution unresolved count mismatch")
    for field in (
        "operator_resolution_resolved_item_count",
        "operator_resolution_controls_satisfied_count",
        "operator_resolution_current_evidence_write_allowed_count",
        "operator_resolution_candidate_current_evidence_usable_count",
    ):
        if report.get(field) != 0:
            errors.append(f"{field} must remain 0")

    source_items = sorted(
        [item for item in operator_resolution_audit_report.get("items", []) if isinstance(item, Mapping)],
        key=lambda item: int(item.get("priority_order", 999) or 999),
    )
    cards = report.get("review_cards", [])
    if not isinstance(cards, list):
        return errors + ["review_cards must be an array"]
    if report.get("review_card_count") != len(cards) or len(cards) != len(source_items):
        errors.append("review card count must match source audit items")
    if report.get("blocked_review_card_count") != len(cards) or report.get("review_ready_count") != 0:
        errors.append("all review cards must stay blocked with review_ready_count=0")
    for index, card in enumerate(cards):
        if not isinstance(card, Mapping):
            errors.append("review card must be object")
            continue
        source = source_items[index]
        if _false_permission_fields(card):
            errors.append(f"{card.get('review_card_id', 'review card')} attempted forbidden permission")
        if card.get("review_status") != REVIEW_CARD_STATUS:
            errors.append("review card status must remain BLOCKED_REVIEW_ONLY")
        for key in (
            "priority_order",
            "cycle_id",
            "replacement_loop_id",
            "candidate_rollup_artifact_path",
            "decision_candidate_rollup_hash",
            "planned_current_ledger_jsonl_path",
            "source_guidance_review_status",
            "source_decision_status",
            "resolution_status",
            "resolution_reason_code",
            "path_scope_status",
        ):
            if card.get(key) != source.get(key):
                errors.append(f"review card {key} must match source audit item")
        if card.get("resolution_status") != POST_RERUN_OPERATOR_RESOLUTION_ITEM_STATUS:
            errors.append("review card resolution_status must remain unresolved")
        if card.get("required_resolution_evidence") != source.get("required_resolution_evidence", []):
            errors.append("review card required resolution evidence mismatch")
        if card.get("blocking_codes") != sorted(str(value) for value in source.get("blocking_codes", []) if value):
            errors.append("review card blocking codes mismatch")

    controls = report.get("control_cards", [])
    source_controls = sorted(
        [control for control in operator_resolution_audit_report.get("resolution_controls", []) if isinstance(control, Mapping)],
        key=lambda control: int(control.get("control_order", 999) or 999),
    )
    if not isinstance(controls, list):
        return errors + ["control_cards must be an array"]
    if report.get("control_card_count") != len(controls) or len(controls) != len(source_controls):
        errors.append("control card count must match source controls")
    if report.get("unsatisfied_control_count") != len(controls) or report.get("satisfied_control_count") != 0:
        errors.append("all control cards must remain unsatisfied")
    for index, control in enumerate(controls):
        if not isinstance(control, Mapping):
            errors.append("control card must be object")
            continue
        source = source_controls[index]
        if _false_permission_fields(control):
            errors.append(f"{control.get('control_id', 'control card')} attempted forbidden permission")
        if control.get("control_status") != CONTROL_CARD_STATUS:
            errors.append("control card status must remain UNSATISFIED_BLOCKING_CONTROL")
        for key in ("control_id", "control_order", "blocker_code", "message", "required"):
            if control.get(key) != source.get(key):
                errors.append(f"control card {key} must match source control")
        if control.get("satisfied") is not False:
            errors.append("control card satisfied must remain false")

    single_next = report.get("single_next_review_card", {})
    if cards and (not isinstance(single_next, Mapping) or single_next.get("review_card_id") != cards[0].get("review_card_id")):
        errors.append("single_next_review_card must match the first review card")
    if report.get("open_gaps_preserved") is not True:
        errors.append("open_gaps_preserved must be true")
    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
