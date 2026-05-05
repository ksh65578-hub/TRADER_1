from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_reconciliation_submission_manifest_preflight import (
    MANIFEST_EVIDENCE_PREFIX,
    MISSING_PREFLIGHT_STATUS,
    STRUCTURAL_ERROR_STATUS,
    STRUCTURAL_REVIEW_STATUS,
)
from trader1.reports.residual_operator_reconciliation_submission_template_packet import (
    TEMPLATE_PACKET_STATUS,
)


SCHEMA_ID = "trader1.residual_operator_reconciliation_submission_security_quarantine_report.v1"
MANIFEST_PREFLIGHT_SCHEMA_ID = "trader1.residual_operator_reconciliation_submission_manifest_preflight_report.v1"
TEMPLATE_PACKET_SCHEMA_ID = "trader1.residual_operator_reconciliation_submission_template_packet_report.v1"
SECURITY_QUARANTINE_SOURCE = (
    "system/evidence/audit_reports/"
    "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_SECURITY_QUARANTINE.report.json"
)
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
ALLOWED_ARTIFACT_EXTENSIONS = (".json", ".jsonl", ".md", ".txt", ".csv")
FORBIDDEN_PATH_TOKENS = (
    ".env",
    "secret",
    "credential",
    "api_key",
    "apikey",
    "private_key",
    "token",
    "password",
    "live_ready",
    "live_config",
    "live_order",
)
ALLOWED_MANIFEST_PREFLIGHT_STATUSES = {
    MISSING_PREFLIGHT_STATUS,
    STRUCTURAL_ERROR_STATUS,
    STRUCTURAL_REVIEW_STATUS,
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


def _false_permission_fields(value: Mapping[str, Any]) -> list[str]:
    fields = (
        "actual_submission_manifest_written_by_this_patch",
        "operator_submission_validated",
        "operator_submission_accepted",
        "current_evidence_write_requested",
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "gap_closure_allowed_by_this_manifest",
        "accepted_for_reconciliation",
        "live_ready_write_requested",
        "live_ready_write_allowed",
        "live_config_mutation_requested",
        "live_config_mutation_allowed",
        "evidence_file_content_read",
        "evidence_artifact_hash_recomputed",
        "secret_pattern_content_scan_performed",
        "credential_values_read",
        "credential_environment_inspection_performed",
        "runtime_artifacts_staged_by_this_patch",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    return [field for field in fields if value.get(field) is True]


def _safe_submission_metadata_path(path: str) -> bool:
    if not path or "\\" in path or path.startswith(("/", "~")):
        return False
    lowered = path.lower()
    if any(token in lowered for token in FORBIDDEN_PATH_TOKENS):
        return False
    try:
        parts = PurePosixPath(path).parts
    except ValueError:
        return False
    if ".." in parts or not path.startswith(MANIFEST_EVIDENCE_PREFIX):
        return False
    return any(lowered.endswith(extension) for extension in ALLOWED_ARTIFACT_EXTENSIONS)


def _template_path_placeholder_violations(template_packet_report: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    items = template_packet_report.get("template_manifest_items", [])
    if not isinstance(items, list):
        return ["template_manifest_items must be array"]
    for item in items:
        if not isinstance(item, Mapping):
            violations.append("template manifest item must be object")
            continue
        intake_item_id = str(item.get("intake_item_id", "UNKNOWN"))
        path = str(item.get("evidence_artifact_path_placeholder", ""))
        if not _safe_submission_metadata_path(path):
            violations.append(f"template path placeholder violates quarantine policy: {intake_item_id}")
        if _false_permission_fields(item):
            violations.append(f"template item attempted forbidden permission: {intake_item_id}")
    return violations


def _security_controls() -> list[dict[str, str]]:
    return [
        {
            "control_id": "SUBMISSION_PATH_PREFIX_ONLY",
            "status": "PASS",
            "required_behavior": f"all metadata paths must start with {MANIFEST_EVIDENCE_PREFIX}",
        },
        {
            "control_id": "NO_CONTENT_READ_IN_QUARANTINE",
            "status": "PASS",
            "required_behavior": "quarantine review records metadata only and does not read submitted evidence file contents",
        },
        {
            "control_id": "NO_CREDENTIAL_OR_LIVE_CONFIG_PATHS",
            "status": "PASS",
            "required_behavior": "path metadata containing credential, token, LIVE_READY, live order, or live config tokens is blocked",
        },
        {
            "control_id": "NO_ACCEPTANCE_OR_GAP_CLOSURE",
            "status": "PASS",
            "required_behavior": "operator submission remains unvalidated, unaccepted, and cannot write current evidence",
        },
    ]


def _quarantine_status(
    *,
    source_valid: bool,
    manifest_preflight_status: str,
    unsafe_count: int,
    path_violation_count: int,
    source_hash_mismatch_count: int,
    template_path_violation_count: int,
) -> str:
    if not source_valid or template_path_violation_count:
        return "QUARANTINE_INVALID_SOURCE"
    if (
        manifest_preflight_status == STRUCTURAL_ERROR_STATUS
        or unsafe_count
        or path_violation_count
        or source_hash_mismatch_count
    ):
        return "QUARANTINE_BLOCKED_STRUCTURAL_ERRORS"
    if manifest_preflight_status == STRUCTURAL_REVIEW_STATUS:
        return "QUARANTINE_STRUCTURAL_REVIEW_ONLY_NOT_ACCEPTED"
    return "QUARANTINE_PENDING_OPERATOR_SUBMISSION"


def _quarantine_blockers(status: str, manifest_preflight_status: str) -> list[str]:
    if status == "QUARANTINE_PENDING_OPERATOR_SUBMISSION":
        return [
            "MISSING_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST",
            "OPERATOR_SUBMISSION_SECURITY_QUARANTINE_PENDING_METADATA_ONLY",
        ]
    if status == "QUARANTINE_BLOCKED_STRUCTURAL_ERRORS":
        return [
            "OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_STRUCTURAL_ERRORS",
            "OPERATOR_SUBMISSION_SECURITY_QUARANTINE_BLOCKED",
        ]
    if status == "QUARANTINE_STRUCTURAL_REVIEW_ONLY_NOT_ACCEPTED":
        return [
            "OPERATOR_SUBMISSION_METADATA_ONLY_REVIEW_NOT_ACCEPTED",
            "OPERATOR_SUBMISSION_EVIDENCE_CONTENT_NOT_READ",
        ]
    return [
        "OPERATOR_SUBMISSION_SECURITY_QUARANTINE_INVALID_SOURCE",
        manifest_preflight_status or "UNKNOWN_MANIFEST_PREFLIGHT_STATUS",
    ]


def build_residual_operator_reconciliation_submission_security_quarantine_report(
    manifest_preflight_report: Mapping[str, Any],
    template_packet_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    manifest_preflight_status = str(manifest_preflight_report.get("manifest_preflight_status", MISSING_PREFLIGHT_STATUS))
    template_path_violations = _template_path_placeholder_violations(template_packet_report)
    source_valid = (
        manifest_preflight_report.get("schema_id") == MANIFEST_PREFLIGHT_SCHEMA_ID
        and template_packet_report.get("schema_id") == TEMPLATE_PACKET_SCHEMA_ID
        and manifest_preflight_report.get("validation_status") == "PASS"
        and template_packet_report.get("validation_status") == "PASS"
        and manifest_preflight_status in ALLOWED_MANIFEST_PREFLIGHT_STATUSES
        and template_packet_report.get("template_packet_status") == TEMPLATE_PACKET_STATUS
        and template_packet_report.get("template_packet_scope") == "OPERATOR_PREPARATION_ONLY_NOT_EVIDENCE"
    )
    unsafe_count = int(manifest_preflight_report.get("unsafe_manifest_flag_count", 0) or 0)
    path_violation_count = int(manifest_preflight_report.get("path_policy_violation_count", 0) or 0)
    source_hash_mismatch_count = int(manifest_preflight_report.get("source_hash_mismatch_count", 0) or 0)
    status = _quarantine_status(
        source_valid=source_valid,
        manifest_preflight_status=manifest_preflight_status,
        unsafe_count=unsafe_count,
        path_violation_count=path_violation_count,
        source_hash_mismatch_count=source_hash_mismatch_count,
        template_path_violation_count=len(template_path_violations),
    )
    blockers = _quarantine_blockers(status, manifest_preflight_status)
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
        ],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "quarantine_status": status,
        "quarantine_scope": "METADATA_ONLY_NO_FILE_CONTENT_READ",
        "quarantine_source": SECURITY_QUARANTINE_SOURCE,
        "manifest_preflight_status": manifest_preflight_status,
        "template_packet_status": str(template_packet_report.get("template_packet_status", "")),
        "operator_submission_required": True,
        "operator_submission_present": manifest_preflight_report.get("operator_submission_present") is True,
        "operator_submission_validated": False,
        "operator_submission_accepted": False,
        "allowed_submission_prefix": MANIFEST_EVIDENCE_PREFIX,
        "allowed_artifact_extensions": list(ALLOWED_ARTIFACT_EXTENSIONS),
        "forbidden_path_tokens": list(FORBIDDEN_PATH_TOKENS),
        "required_manifest_item_count": int(manifest_preflight_report.get("required_manifest_item_count", 32) or 32),
        "manifest_item_count": int(manifest_preflight_report.get("manifest_item_count", 0) or 0),
        "missing_manifest_item_count": int(manifest_preflight_report.get("missing_manifest_item_count", 32) or 32),
        "required_control_count": int(manifest_preflight_report.get("required_control_count", 4) or 4),
        "manifest_control_count": int(manifest_preflight_report.get("manifest_control_count", 0) or 0),
        "missing_control_count": int(manifest_preflight_report.get("missing_control_count", 4) or 4),
        "template_manifest_item_count": int(template_packet_report.get("template_manifest_item_count", 0) or 0),
        "template_control_count": int(template_packet_report.get("template_control_count", 0) or 0),
        "preflight_unsafe_manifest_flag_count": unsafe_count,
        "preflight_path_policy_violation_count": path_violation_count,
        "preflight_source_hash_mismatch_count": source_hash_mismatch_count,
        "template_path_placeholder_violation_count": len(template_path_violations),
        "template_path_placeholder_violations": template_path_violations[:8],
        "security_control_count": 4,
        "security_controls": _security_controls(),
        "quarantine_blocker_count": len(blockers),
        "quarantine_blockers": blockers,
        "one_line_summary": (
            f"Operator submission security quarantine is {status}; metadata only, no evidence file contents are read, "
            "and live/current-evidence/scale paths stay blocked."
        ),
        "primary_next_action": (
            "Keep the operator submission under the allowed submission folder and provide hashes only; "
            "this quarantine cannot accept evidence or write current evidence."
        ),
        "operator_no_action_needed_for_next_non_live_patch": True,
        "operator_action_required_for_gap_closure": True,
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


def validate_residual_operator_reconciliation_submission_security_quarantine_report(
    report: Mapping[str, Any],
    manifest_preflight_report: Mapping[str, Any],
    template_packet_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if manifest_preflight_report.get("schema_id") != MANIFEST_PREFLIGHT_SCHEMA_ID:
        errors.append("manifest preflight source schema mismatch")
    if template_packet_report.get("schema_id") != TEMPLATE_PACKET_SCHEMA_ID:
        errors.append("template packet source schema mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if report.get("quarantine_scope") != "METADATA_ONLY_NO_FILE_CONTENT_READ":
        errors.append("quarantine_scope must remain metadata-only")
    if report.get("allowed_submission_prefix") != MANIFEST_EVIDENCE_PREFIX:
        errors.append("allowed submission prefix mismatch")
    if report.get("allowed_artifact_extensions") != list(ALLOWED_ARTIFACT_EXTENSIONS):
        errors.append("allowed artifact extensions mismatch")
    if report.get("forbidden_path_tokens") != list(FORBIDDEN_PATH_TOKENS):
        errors.append("forbidden path tokens mismatch")
    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        if manifest_preflight_report.get(field) is not False:
            errors.append(f"manifest preflight {field} must remain false")
        if template_packet_report.get(field) is not False:
            errors.append(f"template packet {field} must remain false")
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
    if report.get("operator_submission_required") is not True:
        errors.append("operator_submission_required must remain true")
    if report.get("operator_action_required_for_gap_closure") is not True:
        errors.append("operator_action_required_for_gap_closure must remain true")
    if report.get("operator_no_action_needed_for_next_non_live_patch") is not True:
        errors.append("operator_no_action_needed_for_next_non_live_patch must remain true")
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids or report.get("open_gap_count") != len(open_gap_ids):
        errors.append("open gap ids/count must match current implementation state")
    if report.get("required_manifest_item_count") != 32 or report.get("required_control_count") != 4:
        errors.append("manifest required counts must remain 32 and 4")
    if report.get("template_manifest_item_count") != 32 or report.get("template_control_count") != 4:
        errors.append("template counts must remain 32 and 4")
    if report.get("manifest_preflight_status") not in ALLOWED_MANIFEST_PREFLIGHT_STATUSES:
        errors.append("manifest preflight status must remain blocked")
    expected_template_violations = _template_path_placeholder_violations(template_packet_report)
    if report.get("template_path_placeholder_violation_count") != len(expected_template_violations):
        errors.append("template path placeholder violation count mismatch")
    if report.get("template_path_placeholder_violations") != expected_template_violations[:8]:
        errors.append("template path placeholder violation list mismatch")
    expected_status = _quarantine_status(
        source_valid=(
            manifest_preflight_report.get("schema_id") == MANIFEST_PREFLIGHT_SCHEMA_ID
            and template_packet_report.get("schema_id") == TEMPLATE_PACKET_SCHEMA_ID
            and manifest_preflight_report.get("validation_status") == "PASS"
            and template_packet_report.get("validation_status") == "PASS"
            and str(manifest_preflight_report.get("manifest_preflight_status", "")) in ALLOWED_MANIFEST_PREFLIGHT_STATUSES
            and template_packet_report.get("template_packet_status") == TEMPLATE_PACKET_STATUS
            and template_packet_report.get("template_packet_scope") == "OPERATOR_PREPARATION_ONLY_NOT_EVIDENCE"
        ),
        manifest_preflight_status=str(manifest_preflight_report.get("manifest_preflight_status", "")),
        unsafe_count=int(manifest_preflight_report.get("unsafe_manifest_flag_count", 0) or 0),
        path_violation_count=int(manifest_preflight_report.get("path_policy_violation_count", 0) or 0),
        source_hash_mismatch_count=int(manifest_preflight_report.get("source_hash_mismatch_count", 0) or 0),
        template_path_violation_count=len(expected_template_violations),
    )
    if report.get("quarantine_status") != expected_status:
        errors.append("quarantine_status mismatch")
    expected_blockers = _quarantine_blockers(expected_status, str(manifest_preflight_report.get("manifest_preflight_status", "")))
    if report.get("quarantine_blockers") != expected_blockers or report.get("quarantine_blocker_count") != len(expected_blockers):
        errors.append("quarantine blockers mismatch")
    controls = report.get("security_controls", [])
    if not isinstance(controls, list) or len(controls) != 4 or report.get("security_control_count") != 4:
        errors.append("security controls must expose four controls")
    else:
        for control in controls:
            if not isinstance(control, Mapping) or control.get("status") != "PASS":
                errors.append("security control must be PASS object")
    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
