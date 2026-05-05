from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_reconciliation_intake_preflight import (
    RECONCILIATION_MANIFEST_PATH,
)
from trader1.reports.residual_operator_reconciliation_submission_manifest_preflight import (
    MANIFEST_EVIDENCE_PREFIX,
    MANIFEST_SCHEMA_ID,
    SAFE_OPERATOR_DECISIONS,
)


SCHEMA_ID = "trader1.residual_operator_reconciliation_submission_template_packet_report.v1"
INTAKE_PREFLIGHT_SCHEMA_ID = "trader1.residual_operator_reconciliation_intake_preflight_report.v1"
MANIFEST_PREFLIGHT_SCHEMA_ID = "trader1.residual_operator_reconciliation_submission_manifest_preflight_report.v1"
TEMPLATE_PACKET_STATUS = "TEMPLATE_PACKET_READY_FOR_OPERATOR_PREPARATION_ONLY"
TEMPLATE_PACKET_SOURCE = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET.report.json"
PLACEHOLDER_SHA256 = "<64_HEX_SHA256_OF_OPERATOR_EVIDENCE_FILE>"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
BLOCKED_MANIFEST_STATUSES = {
    "BLOCKED_MANIFEST_MISSING",
    "BLOCKED_MANIFEST_STRUCTURAL_ERRORS",
    "BLOCKED_MANIFEST_STRUCTURAL_REVIEW_ONLY",
}


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _source_report_ref(role: str, report: Mapping[str, Any]) -> dict[str, str]:
    return {
        "role": role,
        "patch_id": str(report.get("patch_id", "")),
        "report_hash": str(report.get("report_hash", "")),
    }


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:72] or "operator_evidence"


def _false_permission_fields(value: Mapping[str, Any]) -> list[str]:
    fields = (
        "actual_submission_manifest_written_by_this_patch",
        "operator_submission_validated",
        "operator_submission_accepted",
        "current_evidence_write_requested",
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "gap_closure_allowed_by_this_manifest",
        "live_ready_write_requested",
        "live_ready_write_allowed",
        "live_config_mutation_requested",
        "live_config_mutation_allowed",
        "accepted_for_reconciliation",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    return [field for field in fields if value.get(field) is True]


def _template_manifest_items(intake_preflight_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, item in enumerate(intake_preflight_report.get("intake_items", []), start=1):
        if not isinstance(item, Mapping):
            continue
        intake_item_id = str(item.get("intake_item_id", ""))
        items.append(
            {
                "intake_item_id": intake_item_id,
                "review_card_id": str(item.get("review_card_id", "")),
                "priority_order": int(item.get("priority_order", index) or index),
                "cycle_id": str(item.get("cycle_id", "")),
                "required_resolution_evidence_kind": str(item.get("required_resolution_evidence_kind", "")),
                "source_decision_candidate_rollup_hash": str(item.get("source_decision_candidate_rollup_hash", "")),
                "evidence_artifact_path_placeholder": (
                    f"{MANIFEST_EVIDENCE_PREFIX}{index:02d}_{_safe_slug(intake_item_id)}.json"
                ),
                "evidence_artifact_path_rule": f"must start with {MANIFEST_EVIDENCE_PREFIX}",
                "evidence_artifact_sha256_placeholder": PLACEHOLDER_SHA256,
                "operator_decision_allowed_values": sorted(SAFE_OPERATOR_DECISIONS),
                "decision_reason_code": "POST_RERUN_RECONCILIATION_REQUIRED",
                "current_evidence_write_requested": False,
                "accepted_for_reconciliation": False,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
    return items


def _template_control_assertions(intake_preflight_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    for index, control in enumerate(intake_preflight_report.get("control_requirements", []), start=1):
        if not isinstance(control, Mapping):
            continue
        control_id = str(control.get("control_id", ""))
        controls.append(
            {
                "control_id": control_id,
                "control_order": int(control.get("control_order", index) or index),
                "blocker_code": str(control.get("blocker_code", "POST_RERUN_RECONCILIATION_REQUIRED")),
                "operator_assertion_required": True,
                "operator_assertion_present_placeholder": False,
                "accepted_for_reconciliation": False,
                "current_evidence_write_requested": False,
                "live_order_allowed": False,
                "scale_up_allowed": False,
            }
        )
    return controls


def _operator_attestation_template() -> dict[str, Any]:
    return {
        "attestation_type": "OPERATOR_RECONCILIATION_SUBMISSION_ONLY",
        "credential_values_excluded": True,
        "no_live_or_scale_mutation": True,
        "current_evidence_write_requested": False,
        "live_ready_write_requested": False,
        "live_config_mutation_requested": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_residual_operator_reconciliation_submission_template_packet_report(
    intake_preflight_report: Mapping[str, Any],
    manifest_preflight_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    template_items = _template_manifest_items(intake_preflight_report)
    template_controls = _template_control_assertions(intake_preflight_report)
    expected_item_count = int(manifest_preflight_report.get("required_manifest_item_count", len(template_items)) or 0)
    expected_control_count = int(manifest_preflight_report.get("required_control_count", len(template_controls)) or 0)
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    operator_template = {
        "schema_id": MANIFEST_SCHEMA_ID,
        "manifest_id": "OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_TEMPLATE_ONLY",
        "created_at_utc": generated_at_utc,
        "submission_scope": {
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "purpose": "OPERATOR_RECONCILIATION_REVIEW",
        },
        "source_intake_preflight_report_hash": str(intake_preflight_report.get("report_hash", "")),
        "source_manifest_preflight_report_hash": str(manifest_preflight_report.get("report_hash", "")),
        "operator_attestation_template": _operator_attestation_template(),
        "manifest_items_template": template_items,
        "control_assertions_template": template_controls,
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_manifest": False,
        "live_ready_write_allowed": False,
        "live_config_mutation_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": [
            _source_report_ref("residual_operator_reconciliation_intake_preflight", intake_preflight_report),
            _source_report_ref("residual_operator_reconciliation_submission_manifest_preflight", manifest_preflight_report),
        ],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "template_packet_status": TEMPLATE_PACKET_STATUS,
        "template_packet_scope": "OPERATOR_PREPARATION_ONLY_NOT_EVIDENCE",
        "template_packet_path": TEMPLATE_PACKET_SOURCE,
        "manifest_schema_id": MANIFEST_SCHEMA_ID,
        "actual_submission_manifest_path": RECONCILIATION_MANIFEST_PATH,
        "actual_submission_manifest_written_by_this_patch": False,
        "operator_submission_required": True,
        "operator_submission_present": manifest_preflight_report.get("operator_submission_present") is True,
        "operator_submission_validated": False,
        "operator_submission_accepted": False,
        "source_manifest_preflight_status": str(
            manifest_preflight_report.get("manifest_preflight_status", "BLOCKED_MANIFEST_MISSING")
        ),
        "required_manifest_item_count": expected_item_count,
        "template_manifest_item_count": len(template_items),
        "template_manifest_items": template_items,
        "required_control_count": expected_control_count,
        "template_control_count": len(template_controls),
        "template_control_assertions": template_controls,
        "operator_attestation_template": _operator_attestation_template(),
        "operator_submission_manifest_template": operator_template,
        "template_hash": sha256_json(operator_template),
        "blocking_reasons": [
            "OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_IS_NOT_EVIDENCE",
            str(manifest_preflight_report.get("manifest_preflight_status", "BLOCKED_MANIFEST_MISSING")),
        ],
        "one_line_summary": (
            f"Operator submission template packet is preparation-only with {len(template_items)} manifest items "
            f"and {len(template_controls)} controls; no submission was written or accepted."
        ),
        "primary_next_action": (
            "Use this packet as a checklist when preparing a separate operator submission manifest; "
            "this report itself is not evidence and cannot close gaps."
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


def validate_residual_operator_reconciliation_submission_template_packet_report(
    report: Mapping[str, Any],
    intake_preflight_report: Mapping[str, Any],
    manifest_preflight_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if intake_preflight_report.get("schema_id") != INTAKE_PREFLIGHT_SCHEMA_ID:
        errors.append("intake preflight source schema mismatch")
    if manifest_preflight_report.get("schema_id") != MANIFEST_PREFLIGHT_SCHEMA_ID:
        errors.append("manifest preflight source schema mismatch")
    if report.get("manifest_schema_id") != MANIFEST_SCHEMA_ID:
        errors.append("manifest_schema_id mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if report.get("template_packet_status") != TEMPLATE_PACKET_STATUS:
        errors.append("template_packet_status mismatch")
    if report.get("template_packet_scope") != "OPERATOR_PREPARATION_ONLY_NOT_EVIDENCE":
        errors.append("template packet scope must remain preparation-only")
    if report.get("actual_submission_manifest_path") != RECONCILIATION_MANIFEST_PATH:
        errors.append("actual submission manifest path mismatch")
    if manifest_preflight_report.get("manifest_preflight_status") not in BLOCKED_MANIFEST_STATUSES:
        errors.append("source manifest preflight must remain blocked")
    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        if intake_preflight_report.get(field) is not False:
            errors.append(f"intake preflight {field} must remain false")
        if manifest_preflight_report.get(field) is not False:
            errors.append(f"manifest preflight {field} must remain false")
    for field in (
        "actual_submission_manifest_written_by_this_patch",
        "operator_submission_validated",
        "operator_submission_accepted",
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
    if report.get("operator_action_required_for_gap_closure") is not True:
        errors.append("operator_action_required_for_gap_closure must remain true")
    if report.get("operator_no_action_needed_for_next_non_live_patch") is not True:
        errors.append("operator_no_action_needed_for_next_non_live_patch must remain true")
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids or report.get("open_gap_count") != len(open_gap_ids):
        errors.append("open gap ids/count must match current implementation state")

    expected_items = _template_manifest_items(intake_preflight_report)
    expected_controls = _template_control_assertions(intake_preflight_report)
    if report.get("required_manifest_item_count") != manifest_preflight_report.get("required_manifest_item_count"):
        errors.append("required_manifest_item_count must match manifest preflight")
    if report.get("required_control_count") != manifest_preflight_report.get("required_control_count"):
        errors.append("required_control_count must match manifest preflight")
    if report.get("template_manifest_item_count") != len(expected_items):
        errors.append("template_manifest_item_count must match intake item count")
    if report.get("template_control_count") != len(expected_controls):
        errors.append("template_control_count must match intake control count")
    if report.get("required_manifest_item_count") != len(expected_items):
        errors.append("required manifest item count must equal template item count")
    if report.get("required_control_count") != len(expected_controls):
        errors.append("required control count must equal template control count")

    template_items = report.get("template_manifest_items", [])
    if not isinstance(template_items, list):
        errors.append("template_manifest_items must be array")
        template_items = []
    if len(template_items) != len(expected_items):
        errors.append("template_manifest_items length mismatch")
    expected_by_id = {item["intake_item_id"]: item for item in expected_items}
    seen: set[str] = set()
    for item in template_items:
        if not isinstance(item, Mapping):
            errors.append("template manifest item must be object")
            continue
        intake_item_id = str(item.get("intake_item_id", ""))
        if intake_item_id in seen:
            errors.append(f"duplicate template manifest item: {intake_item_id}")
        seen.add(intake_item_id)
        expected = expected_by_id.get(intake_item_id)
        if expected is None:
            errors.append(f"unexpected template manifest item: {intake_item_id}")
            continue
        for field in (
            "review_card_id",
            "priority_order",
            "cycle_id",
            "required_resolution_evidence_kind",
            "source_decision_candidate_rollup_hash",
            "evidence_artifact_path_placeholder",
            "evidence_artifact_path_rule",
            "evidence_artifact_sha256_placeholder",
            "decision_reason_code",
        ):
            if item.get(field) != expected.get(field):
                errors.append(f"template manifest item {intake_item_id} field mismatch: {field}")
        if item.get("operator_decision_allowed_values") != sorted(SAFE_OPERATOR_DECISIONS):
            errors.append(f"template manifest item {intake_item_id} operator decisions mismatch")
        if _false_permission_fields(item):
            errors.append(f"template manifest item {intake_item_id} attempted forbidden permission")
        if not str(item.get("evidence_artifact_path_placeholder", "")).startswith(MANIFEST_EVIDENCE_PREFIX):
            errors.append(f"template manifest item {intake_item_id} path placeholder violates policy")

    template_controls = report.get("template_control_assertions", [])
    if not isinstance(template_controls, list):
        errors.append("template_control_assertions must be array")
        template_controls = []
    if len(template_controls) != len(expected_controls):
        errors.append("template_control_assertions length mismatch")
    expected_control_by_id = {item["control_id"]: item for item in expected_controls}
    seen_controls: set[str] = set()
    for control in template_controls:
        if not isinstance(control, Mapping):
            errors.append("template control assertion must be object")
            continue
        control_id = str(control.get("control_id", ""))
        if control_id in seen_controls:
            errors.append(f"duplicate template control assertion: {control_id}")
        seen_controls.add(control_id)
        expected_control = expected_control_by_id.get(control_id)
        if expected_control is None:
            errors.append(f"unexpected template control assertion: {control_id}")
            continue
        for field in ("control_order", "blocker_code", "operator_assertion_required", "operator_assertion_present_placeholder"):
            if control.get(field) != expected_control.get(field):
                errors.append(f"template control {control_id} field mismatch: {field}")
        if _false_permission_fields(control):
            errors.append(f"template control {control_id} attempted forbidden permission")

    attestation = report.get("operator_attestation_template", {})
    if not isinstance(attestation, Mapping):
        errors.append("operator_attestation_template must be object")
        attestation = {}
    if attestation != _operator_attestation_template():
        errors.append("operator_attestation_template mismatch")
    operator_template = report.get("operator_submission_manifest_template", {})
    if not isinstance(operator_template, Mapping):
        errors.append("operator_submission_manifest_template must be object")
        operator_template = {}
    elif _false_permission_fields(operator_template):
        errors.append("operator_submission_manifest_template attempted forbidden permission")
    if report.get("template_hash") != sha256_json(operator_template):
        errors.append("template_hash mismatch")

    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    return errors
