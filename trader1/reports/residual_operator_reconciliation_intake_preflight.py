from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS


SCHEMA_ID = "trader1.residual_operator_reconciliation_intake_preflight_report.v1"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
REVIEW_CARDS_SCHEMA_ID = "trader1.residual_operator_reconciliation_review_cards_report.v1"
EVIDENCE_INTAKE_SCHEMA_ID = "trader1.residual_operator_evidence_intake_audit_report.v1"
RECONCILIATION_MANIFEST_PATH = (
    "system/evidence/operator_submissions/residual_operator_reconciliation_submission_manifest.json"
)
PREFLIGHT_STATUS = "BLOCKED_RECONCILIATION_INTAKE_PACKAGE_MISSING"
INTAKE_ITEM_STATUS = "MISSING_OPERATOR_RECONCILIATION_EVIDENCE"
CONTROL_STATUS = "UNSATISFIED_RECONCILIATION_INTAKE_CONTROL"


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _source_report_ref(role: str, report: Mapping[str, Any]) -> dict[str, str]:
    return {
        "role": role,
        "patch_id": str(report.get("patch_id", "")),
        "report_hash": str(report.get("report_hash", "")),
    }


def _manifest_status(root: Path) -> str:
    return "PRESENT_NOT_VALIDATED" if (root / RECONCILIATION_MANIFEST_PATH).exists() else "MISSING_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST"


def _false_permission_fields(value: Mapping[str, Any]) -> list[str]:
    fields = (
        "resolution_evidence_present",
        "resolution_evidence_accepted",
        "candidate_current_evidence_usable",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "latest_runtime_pointer_write_allowed",
        "current_ledger_jsonl_write_allowed",
        "current_evidence_write_authorized",
        "gap_closure_allowed_by_this_patch",
        "promotion_eligible",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    return [field for field in fields if value.get(field) is True]


def _build_intake_items(review_cards_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    intake_items: list[dict[str, Any]] = []
    for card in review_cards_report.get("review_cards", []):
        if not isinstance(card, Mapping):
            continue
        priority = int(card.get("priority_order", 999) or 999)
        cycle_id = str(card.get("cycle_id", "UNKNOWN"))
        review_card_id = str(card.get("review_card_id", f"OPERATOR_RECONCILIATION_REVIEW:{priority}:{cycle_id}"))
        for evidence_index, evidence_kind in enumerate(card.get("required_resolution_evidence", []), start=1):
            intake_items.append(
                {
                    "intake_item_id": f"OPERATOR_RECONCILIATION_INTAKE:{priority}:{evidence_index}:{cycle_id}",
                    "review_card_id": review_card_id,
                    "priority_order": priority,
                    "cycle_id": cycle_id,
                    "required_resolution_evidence_kind": str(evidence_kind),
                    "resolution_reason_code": str(card.get("resolution_reason_code", "POST_RERUN_RECONCILIATION_REQUIRED")),
                    "source_candidate_rollup_artifact_path": str(card.get("candidate_rollup_artifact_path", "")),
                    "source_decision_candidate_rollup_hash": str(card.get("decision_candidate_rollup_hash", "")),
                    "planned_current_ledger_jsonl_path": str(card.get("planned_current_ledger_jsonl_path", "")),
                    "manifest_path": RECONCILIATION_MANIFEST_PATH,
                    "intake_item_status": INTAKE_ITEM_STATUS,
                    "operator_submission_required": True,
                    "operator_submission_validated": False,
                    "source_hash_recorded": False,
                    "review_ready": False,
                    "accepted_for_reconciliation": False,
                    "blocks_gap_closure": True,
                    "current_evidence_write_allowed": False,
                    "gap_closure_allowed_by_this_patch": False,
                    "live_ready_write_allowed": False,
                    "live_config_mutation_allowed": False,
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }
            )
    return intake_items


def _build_control_requirements(review_cards_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for control in review_cards_report.get("control_cards", []):
        if not isinstance(control, Mapping):
            continue
        requirements.append(
            {
                "control_id": str(control.get("control_id", "")),
                "control_order": int(control.get("control_order", 999) or 999),
                "blocker_code": str(control.get("blocker_code", "POST_RERUN_RECONCILIATION_REQUIRED")),
                "control_status": CONTROL_STATUS,
                "source_control_status": str(control.get("control_status", "")),
                "required": True,
                "satisfied": False,
                "operator_submission_required": True,
                "current_evidence_write_allowed": False,
                "gap_closure_allowed_by_this_patch": False,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
    return requirements


def build_residual_operator_reconciliation_intake_preflight_report(
    review_cards_report: Mapping[str, Any],
    evidence_intake_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    root: Path,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    intake_items = _build_intake_items(review_cards_report)
    control_requirements = _build_control_requirements(review_cards_report)
    manifest_status = _manifest_status(root)
    single_next = intake_items[0] if intake_items else {}
    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": [
            _source_report_ref("residual_operator_reconciliation_review_cards", review_cards_report),
            _source_report_ref("residual_operator_evidence_intake_audit", evidence_intake_report),
        ],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "preflight_status": PREFLIGHT_STATUS,
        "review_cards_source_status": str(review_cards_report.get("review_status", "UNKNOWN")),
        "review_cards_source_hashes_verified": review_cards_report.get("source_hashes_verified") is True,
        "review_card_count": int(review_cards_report.get("review_card_count", 0) or 0),
        "blocked_review_card_count": int(review_cards_report.get("blocked_review_card_count", 0) or 0),
        "review_ready_count": 0,
        "control_card_count": int(review_cards_report.get("control_card_count", 0) or 0),
        "unsatisfied_control_count": int(review_cards_report.get("unsatisfied_control_count", 0) or 0),
        "satisfied_control_count": 0,
        "operator_resolution_current_evidence_write_allowed_count": 0,
        "operator_resolution_candidate_current_evidence_usable_count": 0,
        "operator_reconciliation_submission_manifest_path": RECONCILIATION_MANIFEST_PATH,
        "operator_reconciliation_submission_manifest_status": manifest_status,
        "operator_submission_required": True,
        "operator_submission_validated": False,
        "required_intake_item_count": len(intake_items),
        "missing_intake_item_count": len(intake_items),
        "ready_for_review_intake_item_count": 0,
        "accepted_intake_item_count": 0,
        "single_next_intake_item": single_next,
        "intake_item_preview": intake_items[:4],
        "intake_items": intake_items,
        "control_requirement_count": len(control_requirements),
        "unsatisfied_control_requirement_count": len(control_requirements),
        "control_requirements": control_requirements,
        "paper_shadow_operator_evidence_intake_status": str(evidence_intake_report.get("intake_status", "UNKNOWN")),
        "paper_shadow_operator_submission_manifest_status": str(
            evidence_intake_report.get("operator_submission_manifest_status", "UNKNOWN")
        ),
        "one_line_summary": (
            f"{len(intake_items)} reconciliation evidence inputs remain missing across "
            f"{int(review_cards_report.get('review_card_count', 0) or 0)} review cards; current-evidence writes stay 0."
        ),
        "primary_next_action": (
            "Prepare a separate operator reconciliation submission manifest and evidence package; "
            "do not accept review cards, write current evidence, or enable LIVE_READY from this preflight."
        ),
        "operator_no_action_needed_for_next_non_live_patch": True,
        "operator_action_required_for_gap_closure": True,
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_ready_write_allowed": False,
        "live_config_mutation_allowed": False,
        "credential_values_read": False,
        "credential_environment_inspection_performed": False,
        "runtime_artifacts_staged_by_this_patch": False,
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


def validate_residual_operator_reconciliation_intake_preflight_report(
    report: Mapping[str, Any],
    review_cards_report: Mapping[str, Any],
    evidence_intake_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if report.get("preflight_status") != PREFLIGHT_STATUS:
        errors.append("preflight_status must remain blocked")
    if review_cards_report.get("schema_id") != REVIEW_CARDS_SCHEMA_ID:
        errors.append("review cards source schema mismatch")
    if evidence_intake_report.get("schema_id") != EVIDENCE_INTAKE_SCHEMA_ID:
        errors.append("evidence intake source schema mismatch")
    if review_cards_report.get("review_status") != "BLOCKED_RECONCILIATION_REVIEW_ONLY":
        errors.append("review cards source must remain blocked")
    if review_cards_report.get("source_hashes_verified") is not True:
        errors.append("review cards source hashes must remain verified")
    if report.get("review_cards_source_hashes_verified") is not True:
        errors.append("report review cards source hashes must remain verified")
    if report.get("review_cards_source_status") != "BLOCKED_RECONCILIATION_REVIEW_ONLY":
        errors.append("report review cards source status must remain blocked")
    if evidence_intake_report.get("intake_status") != "BLOCKED_AWAITING_OPERATOR_EVIDENCE_PACKAGE":
        errors.append("paper/shadow evidence intake must remain blocked")
    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        if review_cards_report.get(field) is not False:
            errors.append(f"review cards {field} must remain false")
        if evidence_intake_report.get(field) is not False:
            errors.append(f"evidence intake {field} must remain false")
    for field in (
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
        "credential_values_read",
        "credential_environment_inspection_performed",
        "runtime_artifacts_staged_by_this_patch",
    ):
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
    if report.get("operator_submission_required") is not True:
        errors.append("operator_submission_required must remain true")
    if report.get("operator_submission_validated") is not False:
        errors.append("operator_submission_validated must remain false")
    if report.get("operator_reconciliation_submission_manifest_status") == "VALIDATED":
        errors.append("operator reconciliation manifest cannot be validated in this patch")
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids or report.get("open_gap_count") != len(open_gap_ids):
        errors.append("open gap ids/count must match current implementation state")

    source_cards = [card for card in review_cards_report.get("review_cards", []) if isinstance(card, Mapping)]
    expected_item_count = sum(len(card.get("required_resolution_evidence", [])) for card in source_cards)
    intake_items = report.get("intake_items", [])
    if not isinstance(intake_items, list):
        return errors + ["intake_items must be array"]
    if report.get("required_intake_item_count") != expected_item_count or len(intake_items) != expected_item_count:
        errors.append("required intake item count must match review-card required evidence")
    if report.get("missing_intake_item_count") != len(intake_items):
        errors.append("missing intake item count must match intake_items while manifest is missing")
    if report.get("ready_for_review_intake_item_count") != 0 or report.get("accepted_intake_item_count") != 0:
        errors.append("intake items cannot be ready or accepted in this patch")
    for item in intake_items:
        if not isinstance(item, Mapping):
            errors.append("intake item must be object")
            continue
        if _false_permission_fields(item):
            errors.append(f"{item.get('intake_item_id', 'intake item')} attempted forbidden permission")
        if item.get("intake_item_status") != INTAKE_ITEM_STATUS:
            errors.append("intake item status must remain missing")
        if item.get("operator_submission_required") is not True or item.get("operator_submission_validated") is not False:
            errors.append("intake item must require unvalidated operator submission")
        if item.get("source_hash_recorded") is not False:
            errors.append("intake item cannot record source hash before manifest validation")
        if item.get("review_ready") is not False or item.get("accepted_for_reconciliation") is not False:
            errors.append("intake item cannot be ready or accepted")

    controls = report.get("control_requirements", [])
    if not isinstance(controls, list):
        return errors + ["control_requirements must be array"]
    if report.get("control_requirement_count") != len(controls):
        errors.append("control requirement count mismatch")
    if report.get("unsatisfied_control_requirement_count") != len(controls):
        errors.append("all control requirements must remain unsatisfied")
    if len(controls) != int(review_cards_report.get("control_card_count", 0) or 0):
        errors.append("control requirements must match review card source controls")
    for control in controls:
        if not isinstance(control, Mapping):
            errors.append("control requirement must be object")
            continue
        if _false_permission_fields(control):
            errors.append(f"{control.get('control_id', 'control')} attempted forbidden permission")
        if control.get("control_status") != CONTROL_STATUS:
            errors.append("control status must remain unsatisfied preflight control")
        if control.get("required") is not True or control.get("satisfied") is not False:
            errors.append("control requirement cannot be satisfied in this patch")

    single_next = report.get("single_next_intake_item", {})
    if intake_items and (not isinstance(single_next, Mapping) or single_next.get("intake_item_id") != intake_items[0].get("intake_item_id")):
        errors.append("single_next_intake_item must match first intake item")
    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
