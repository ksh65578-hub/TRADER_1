from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_reconciliation_submission_manifest_preflight import (
    MISSING_PREFLIGHT_STATUS,
    STRUCTURAL_ERROR_STATUS,
    STRUCTURAL_REVIEW_STATUS,
)
from trader1.reports.residual_operator_reconciliation_submission_security_quarantine import (
    SCHEMA_ID as SECURITY_QUARANTINE_SCHEMA_ID,
)
from trader1.reports.residual_operator_reconciliation_submission_template_packet import (
    TEMPLATE_PACKET_STATUS,
)


SCHEMA_ID = "trader1.residual_operator_reconciliation_submission_review_queue_report.v1"
MANIFEST_PREFLIGHT_SCHEMA_ID = "trader1.residual_operator_reconciliation_submission_manifest_preflight_report.v1"
TEMPLATE_PACKET_SCHEMA_ID = "trader1.residual_operator_reconciliation_submission_template_packet_report.v1"
REVIEW_QUEUE_SOURCE = (
    "system/evidence/audit_reports/"
    "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE.report.json"
)
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
REVIEW_QUEUE_PHASES = (
    "TEMPLATE_PACKET",
    "MANIFEST_PREFLIGHT",
    "SECURITY_QUARANTINE",
    "OPERATOR_ACCEPTANCE",
)
ALLOWED_QUEUE_STATUSES = {
    "BLOCKED_OPERATOR_SUBMISSION_MISSING",
    "BLOCKED_OPERATOR_SUBMISSION_STRUCTURAL_ERRORS",
    "BLOCKED_OPERATOR_SUBMISSION_REVIEW_ONLY_NOT_ACCEPTED",
    "BLOCKED_OPERATOR_SUBMISSION_QUARANTINE_INVALID_SOURCE",
}
ALLOWED_MANIFEST_STATUSES = {
    MISSING_PREFLIGHT_STATUS,
    STRUCTURAL_ERROR_STATUS,
    STRUCTURAL_REVIEW_STATUS,
}
ALLOWED_QUARANTINE_STATUSES = {
    "QUARANTINE_PENDING_OPERATOR_SUBMISSION",
    "QUARANTINE_BLOCKED_STRUCTURAL_ERRORS",
    "QUARANTINE_STRUCTURAL_REVIEW_ONLY_NOT_ACCEPTED",
    "QUARANTINE_INVALID_SOURCE",
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


def _int_field(source: Mapping[str, Any], field: str, default: int) -> int:
    value = source.get(field, default)
    if value is None:
        return default
    return int(value)


def _queue_status(manifest_status: str, quarantine_status: str) -> str:
    if quarantine_status == "QUARANTINE_INVALID_SOURCE":
        return "BLOCKED_OPERATOR_SUBMISSION_QUARANTINE_INVALID_SOURCE"
    if manifest_status == STRUCTURAL_ERROR_STATUS or quarantine_status == "QUARANTINE_BLOCKED_STRUCTURAL_ERRORS":
        return "BLOCKED_OPERATOR_SUBMISSION_STRUCTURAL_ERRORS"
    if manifest_status == STRUCTURAL_REVIEW_STATUS or quarantine_status == "QUARANTINE_STRUCTURAL_REVIEW_ONLY_NOT_ACCEPTED":
        return "BLOCKED_OPERATOR_SUBMISSION_REVIEW_ONLY_NOT_ACCEPTED"
    return "BLOCKED_OPERATOR_SUBMISSION_MISSING"


def _next_operator_step(queue_status: str) -> str:
    if queue_status == "BLOCKED_OPERATOR_SUBMISSION_STRUCTURAL_ERRORS":
        return "REPAIR_OPERATOR_SUBMISSION_MANIFEST_STRUCTURE"
    if queue_status == "BLOCKED_OPERATOR_SUBMISSION_REVIEW_ONLY_NOT_ACCEPTED":
        return "WAIT_FOR_SEPARATE_OPERATOR_RECONCILIATION_REVIEW"
    if queue_status == "BLOCKED_OPERATOR_SUBMISSION_QUARANTINE_INVALID_SOURCE":
        return "REGENERATE_SECURITY_QUARANTINE_FROM_VALID_SOURCES"
    return "CREATE_OPERATOR_SUBMISSION_MANIFEST"


def _operator_message(next_step: str) -> str:
    messages = {
        "CREATE_OPERATOR_SUBMISSION_MANIFEST": (
            "Prepare the separate operator submission manifest under the allowed submissions folder; "
            "this queue does not read or accept evidence."
        ),
        "REPAIR_OPERATOR_SUBMISSION_MANIFEST_STRUCTURE": (
            "Repair manifest structure, path policy, source hashes, and false permission flags before review."
        ),
        "WAIT_FOR_SEPARATE_OPERATOR_RECONCILIATION_REVIEW": (
            "A structurally reviewed manifest still requires separate reconciliation review before any gap can close."
        ),
        "REGENERATE_SECURITY_QUARANTINE_FROM_VALID_SOURCES": (
            "Regenerate quarantine inputs from valid manifest preflight and template packet sources."
        ),
    }
    return messages[next_step]


def _review_steps(
    manifest_preflight_report: Mapping[str, Any],
    template_packet_report: Mapping[str, Any],
    security_quarantine_report: Mapping[str, Any],
    *,
    queue_status: str,
) -> list[dict[str, Any]]:
    template_ok = (
        template_packet_report.get("schema_id") == TEMPLATE_PACKET_SCHEMA_ID
        and template_packet_report.get("validation_status") == "PASS"
        and template_packet_report.get("template_packet_status") == TEMPLATE_PACKET_STATUS
        and template_packet_report.get("template_packet_scope") == "OPERATOR_PREPARATION_ONLY_NOT_EVIDENCE"
    )
    manifest_status = str(manifest_preflight_report.get("manifest_preflight_status", MISSING_PREFLIGHT_STATUS))
    quarantine_status = str(security_quarantine_report.get("quarantine_status", "QUARANTINE_INVALID_SOURCE"))
    return [
        {
            "phase_id": "TEMPLATE_PACKET",
            "priority_order": 1,
            "phase_status": "READY_FOR_OPERATOR_PREPARATION_ONLY" if template_ok else "BLOCKED_SOURCE_INVALID",
            "blocks_gap_closure": True,
            "operator_action_code": "USE_TEMPLATE_AS_CHECKLIST_ONLY",
            "reason_code": "OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_IS_NOT_EVIDENCE",
            "display_message": "Template packet is a checklist only; it is not evidence.",
        },
        {
            "phase_id": "MANIFEST_PREFLIGHT",
            "priority_order": 2,
            "phase_status": manifest_status,
            "blocks_gap_closure": True,
            "operator_action_code": _next_operator_step(queue_status),
            "reason_code": manifest_status,
            "display_message": str(manifest_preflight_report.get("one_line_summary", "Manifest preflight remains blocked.")),
        },
        {
            "phase_id": "SECURITY_QUARANTINE",
            "priority_order": 3,
            "phase_status": quarantine_status,
            "blocks_gap_closure": True,
            "operator_action_code": "KEEP_METADATA_ONLY_QUARANTINE",
            "reason_code": quarantine_status,
            "display_message": str(
                security_quarantine_report.get(
                    "one_line_summary",
                    "Security quarantine remains metadata-only and blocked.",
                )
            ),
        },
        {
            "phase_id": "OPERATOR_ACCEPTANCE",
            "priority_order": 4,
            "phase_status": "BLOCKED_NO_ACCEPTANCE_OR_CURRENT_EVIDENCE_WRITE",
            "blocks_gap_closure": True,
            "operator_action_code": "WAIT_FOR_SEPARATE_OPERATOR_RECONCILIATION_REVIEW",
            "reason_code": "OPERATOR_SUBMISSION_NOT_ACCEPTED_BY_REVIEW_QUEUE",
            "display_message": "This queue cannot accept evidence, close gaps, or write current evidence.",
        },
    ]


def build_residual_operator_reconciliation_submission_review_queue_report(
    manifest_preflight_report: Mapping[str, Any],
    template_packet_report: Mapping[str, Any],
    security_quarantine_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    manifest_status = str(manifest_preflight_report.get("manifest_preflight_status", MISSING_PREFLIGHT_STATUS))
    quarantine_status = str(security_quarantine_report.get("quarantine_status", "QUARANTINE_INVALID_SOURCE"))
    queue_status = _queue_status(manifest_status, quarantine_status)
    next_step = _next_operator_step(queue_status)
    review_steps = _review_steps(
        manifest_preflight_report,
        template_packet_report,
        security_quarantine_report,
        queue_status=queue_status,
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
            _source_report_ref("residual_operator_reconciliation_submission_manifest_preflight", manifest_preflight_report),
            _source_report_ref("residual_operator_reconciliation_submission_template_packet", template_packet_report),
            _source_report_ref("residual_operator_reconciliation_submission_security_quarantine", security_quarantine_report),
        ],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "review_queue_status": queue_status,
        "review_queue_source": REVIEW_QUEUE_SOURCE,
        "review_order_locked": True,
        "review_phase_count": len(REVIEW_QUEUE_PHASES),
        "blocked_phase_count": len(REVIEW_QUEUE_PHASES),
        "review_ready_phase_count": 0,
        "accepted_phase_count": 0,
        "single_next_operator_step": next_step,
        "single_next_operator_message": _operator_message(next_step),
        "manifest_preflight_status": manifest_status,
        "template_packet_status": str(template_packet_report.get("template_packet_status", "")),
        "security_quarantine_status": quarantine_status,
        "operator_submission_present": manifest_preflight_report.get("operator_submission_present") is True,
        "operator_submission_validated": False,
        "operator_submission_accepted": False,
        "operator_action_required_for_gap_closure": True,
        "operator_no_action_needed_for_next_non_live_patch": True,
        "required_manifest_item_count": _int_field(manifest_preflight_report, "required_manifest_item_count", 32),
        "manifest_item_count": _int_field(manifest_preflight_report, "manifest_item_count", 0),
        "missing_manifest_item_count": _int_field(manifest_preflight_report, "missing_manifest_item_count", 32),
        "required_control_count": _int_field(manifest_preflight_report, "required_control_count", 4),
        "manifest_control_count": _int_field(manifest_preflight_report, "manifest_control_count", 0),
        "missing_control_count": _int_field(manifest_preflight_report, "missing_control_count", 4),
        "security_control_count": _int_field(security_quarantine_report, "security_control_count", 0),
        "quarantine_blocker_count": _int_field(security_quarantine_report, "quarantine_blocker_count", 0),
        "review_steps": review_steps,
        "one_line_summary": (
            f"Operator submission review queue is {queue_status}; next step is {next_step}; "
            "no evidence contents are read or accepted."
        ),
        "primary_next_action": _operator_message(next_step),
        "evidence_file_content_read": False,
        "evidence_artifact_hash_recomputed": False,
        "secret_pattern_content_scan_performed": False,
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


def validate_residual_operator_reconciliation_submission_review_queue_report(
    report: Mapping[str, Any],
    manifest_preflight_report: Mapping[str, Any],
    template_packet_report: Mapping[str, Any],
    security_quarantine_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if manifest_preflight_report.get("schema_id") != MANIFEST_PREFLIGHT_SCHEMA_ID:
        errors.append("manifest preflight source schema mismatch")
    if template_packet_report.get("schema_id") != TEMPLATE_PACKET_SCHEMA_ID:
        errors.append("template packet source schema mismatch")
    if security_quarantine_report.get("schema_id") != SECURITY_QUARANTINE_SCHEMA_ID:
        errors.append("security quarantine source schema mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    manifest_status = str(manifest_preflight_report.get("manifest_preflight_status", ""))
    quarantine_status = str(security_quarantine_report.get("quarantine_status", ""))
    if manifest_status not in ALLOWED_MANIFEST_STATUSES:
        errors.append("manifest preflight status must remain blocked")
    if quarantine_status not in ALLOWED_QUARANTINE_STATUSES:
        errors.append("security quarantine status must remain blocked")
    expected_status = _queue_status(manifest_status, quarantine_status)
    expected_next = _next_operator_step(expected_status)
    if report.get("review_queue_status") != expected_status:
        errors.append("review_queue_status mismatch")
    if report.get("review_queue_status") not in ALLOWED_QUEUE_STATUSES:
        errors.append("review_queue_status unknown")
    if report.get("single_next_operator_step") != expected_next:
        errors.append("single_next_operator_step mismatch")
    if report.get("review_order_locked") is not True:
        errors.append("review_order_locked must remain true")
    if report.get("review_phase_count") != len(REVIEW_QUEUE_PHASES):
        errors.append("review_phase_count mismatch")
    if report.get("blocked_phase_count") != len(REVIEW_QUEUE_PHASES):
        errors.append("blocked_phase_count must keep every phase blocked for gap closure")
    if report.get("review_ready_phase_count") != 0 or report.get("accepted_phase_count") != 0:
        errors.append("review queue cannot claim ready or accepted phases")

    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        if manifest_preflight_report.get(field) is not False:
            errors.append(f"manifest preflight {field} must remain false")
        if template_packet_report.get(field) is not False:
            errors.append(f"template packet {field} must remain false")
        if security_quarantine_report.get(field) is not False:
            errors.append(f"security quarantine {field} must remain false")
    for field in (
        "operator_submission_validated",
        "operator_submission_accepted",
        "evidence_file_content_read",
        "evidence_artifact_hash_recomputed",
        "secret_pattern_content_scan_performed",
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
    if report.get("operator_action_required_for_gap_closure") is not True:
        errors.append("operator_action_required_for_gap_closure must remain true")
    if report.get("operator_no_action_needed_for_next_non_live_patch") is not True:
        errors.append("operator_no_action_needed_for_next_non_live_patch must remain true")

    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids or report.get("open_gap_count") != len(open_gap_ids):
        errors.append("open gap ids/count must match current implementation state")
    if report.get("required_manifest_item_count") != manifest_preflight_report.get("required_manifest_item_count"):
        errors.append("required_manifest_item_count must match manifest preflight")
    if report.get("manifest_item_count") != manifest_preflight_report.get("manifest_item_count"):
        errors.append("manifest_item_count must match manifest preflight")
    if report.get("missing_manifest_item_count") != manifest_preflight_report.get("missing_manifest_item_count"):
        errors.append("missing_manifest_item_count must match manifest preflight")
    if report.get("security_control_count") != security_quarantine_report.get("security_control_count"):
        errors.append("security_control_count must match quarantine")

    steps = report.get("review_steps", [])
    if not isinstance(steps, list) or len(steps) != len(REVIEW_QUEUE_PHASES):
        errors.append("review_steps must contain exactly four phases")
        steps = []
    for index, phase_id in enumerate(REVIEW_QUEUE_PHASES, start=1):
        step = steps[index - 1] if index - 1 < len(steps) and isinstance(steps[index - 1], Mapping) else {}
        if step.get("phase_id") != phase_id:
            errors.append(f"review step {index} phase_id mismatch")
        if step.get("priority_order") != index:
            errors.append(f"review step {phase_id} priority_order mismatch")
        if step.get("blocks_gap_closure") is not True:
            errors.append(f"review step {phase_id} must block gap closure")
        if not step.get("reason_code"):
            errors.append(f"review step {phase_id} reason_code missing")
    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    return errors
