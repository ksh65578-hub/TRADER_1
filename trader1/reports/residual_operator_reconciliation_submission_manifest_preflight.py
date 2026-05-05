from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath, Path
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_reconciliation_intake_preflight import (
    RECONCILIATION_MANIFEST_PATH,
)


SCHEMA_ID = "trader1.residual_operator_reconciliation_submission_manifest_preflight_report.v1"
MANIFEST_SCHEMA_ID = "trader1.residual_operator_reconciliation_submission_manifest.v1"
INTAKE_PREFLIGHT_SCHEMA_ID = "trader1.residual_operator_reconciliation_intake_preflight_report.v1"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
MANIFEST_EVIDENCE_PREFIX = "system/evidence/operator_submissions/residual_operator_reconciliation/"
MISSING_MANIFEST_STATUS = "MISSING_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST"
STRUCTURAL_REVIEW_STATUS = "BLOCKED_MANIFEST_STRUCTURAL_REVIEW_ONLY"
MISSING_PREFLIGHT_STATUS = "BLOCKED_MANIFEST_MISSING"
STRUCTURAL_ERROR_STATUS = "BLOCKED_MANIFEST_STRUCTURAL_ERRORS"
SAFE_OPERATOR_DECISIONS = {
    "SUBMIT_FOR_RECONCILIATION_REVIEW",
    "REJECT_CANDIDATE_KEEP_BLOCKED",
    "REQUEST_ADDITIONAL_RERUN_EVIDENCE",
    "ESCALATE_BLOCKED_RECONCILIATION",
}
FORBIDDEN_PATH_TOKENS = (
    ".env",
    "secret",
    "credential",
    "api_key",
    "apikey",
    "private_key",
    "token",
    "password",
)


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
        "current_evidence_write_requested",
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "accepted_for_reconciliation",
        "live_ready_write_requested",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    return [field for field in fields if value.get(field) is True]


def _safe_relative_submission_path(path: str) -> bool:
    if not path or "\\" in path or path.startswith(("/", "~")):
        return False
    lowered = path.lower()
    if any(token in lowered for token in FORBIDDEN_PATH_TOKENS):
        return False
    try:
        parts = PurePosixPath(path).parts
    except ValueError:
        return False
    return ".." not in parts and path.startswith(MANIFEST_EVIDENCE_PREFIX)


def _read_manifest(root: Path) -> tuple[str, dict[str, Any] | None, list[str]]:
    path = root / RECONCILIATION_MANIFEST_PATH
    if not path.exists():
        return MISSING_MANIFEST_STATUS, None, []
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return "PRESENT_JSON_INVALID", None, [f"manifest json parse failed: {exc.msg}"]
    if not isinstance(parsed, dict):
        return "PRESENT_STRUCTURAL_INVALID", None, ["manifest root must be an object"]
    return "PRESENT_NOT_VALIDATED", parsed, []


def _expected_item_templates(intake_preflight_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for item in intake_preflight_report.get("intake_items", []):
        if not isinstance(item, Mapping):
            continue
        templates.append(
            {
                "intake_item_id": str(item.get("intake_item_id", "")),
                "review_card_id": str(item.get("review_card_id", "")),
                "priority_order": int(item.get("priority_order", 999) or 999),
                "cycle_id": str(item.get("cycle_id", "")),
                "required_resolution_evidence_kind": str(item.get("required_resolution_evidence_kind", "")),
                "source_decision_candidate_rollup_hash": str(item.get("source_decision_candidate_rollup_hash", "")),
                "evidence_artifact_path_rule": f"must start with {MANIFEST_EVIDENCE_PREFIX}",
                "evidence_artifact_sha256_required": True,
                "operator_decision_allowed_values": sorted(SAFE_OPERATOR_DECISIONS),
                "current_evidence_write_requested": False,
                "live_order_allowed": False,
                "scale_up_allowed": False,
            }
        )
    return templates


def _expected_control_templates(intake_preflight_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for control in intake_preflight_report.get("control_requirements", []):
        if not isinstance(control, Mapping):
            continue
        templates.append(
            {
                "control_id": str(control.get("control_id", "")),
                "control_order": int(control.get("control_order", 999) or 999),
                "blocker_code": str(control.get("blocker_code", "POST_RERUN_RECONCILIATION_REQUIRED")),
                "operator_assertion_required": True,
                "accepted_for_reconciliation": False,
                "current_evidence_write_requested": False,
                "live_order_allowed": False,
                "scale_up_allowed": False,
            }
        )
    return templates


def build_residual_operator_reconciliation_submission_manifest_template(
    intake_preflight_report: Mapping[str, Any],
    *,
    generated_at_utc: str,
    manifest_id: str = "OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_TEMPLATE",
) -> dict[str, Any]:
    source_reports = {
        str(item.get("role")): item for item in intake_preflight_report.get("source_reports", []) if isinstance(item, Mapping)
    }
    manifest = {
        "schema_id": MANIFEST_SCHEMA_ID,
        "manifest_id": manifest_id,
        "created_at_utc": generated_at_utc,
        "submission_scope": {
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "purpose": "OPERATOR_RECONCILIATION_REVIEW",
        },
        "source_intake_preflight_report_hash": str(intake_preflight_report.get("report_hash", "")),
        "source_review_cards_report_hash": str(
            source_reports.get("residual_operator_reconciliation_review_cards", {}).get("report_hash", "")
        ),
        "source_evidence_intake_report_hash": str(
            source_reports.get("residual_operator_evidence_intake_audit", {}).get("report_hash", "")
        ),
        "operator_attestation": {
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
        },
        "manifest_items": [],
        "control_assertions": [],
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_manifest": False,
        "live_ready_write_allowed": False,
        "live_config_mutation_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "manifest_hash": "",
    }
    manifest["manifest_hash"] = sha256_json({key: value for key, value in manifest.items() if key != "manifest_hash"})
    return manifest


def _validate_manifest_against_intake(
    manifest: Mapping[str, Any] | None,
    intake_preflight_report: Mapping[str, Any],
) -> dict[str, Any]:
    expected_items = _expected_item_templates(intake_preflight_report)
    expected_controls = _expected_control_templates(intake_preflight_report)
    expected_by_id = {item["intake_item_id"]: item for item in expected_items}
    expected_control_by_id = {item["control_id"]: item for item in expected_controls}
    errors: list[str] = []

    result = {
        "manifest_item_count": 0,
        "missing_manifest_item_count": len(expected_items),
        "duplicate_manifest_item_count": 0,
        "unexpected_manifest_item_count": 0,
        "mismatched_manifest_item_count": 0,
        "manifest_control_count": 0,
        "missing_control_count": len(expected_controls),
        "duplicate_control_count": 0,
        "unsafe_manifest_flag_count": 0,
        "path_policy_violation_count": 0,
        "source_hash_mismatch_count": 0,
        "manifest_errors": errors,
    }
    if manifest is None:
        return result

    if manifest.get("schema_id") != MANIFEST_SCHEMA_ID:
        errors.append("manifest schema_id mismatch")
    if manifest.get("source_intake_preflight_report_hash") != intake_preflight_report.get("report_hash"):
        errors.append("source intake preflight report hash mismatch")
        result["source_hash_mismatch_count"] += 1
    source_reports = {
        str(item.get("role")): item for item in intake_preflight_report.get("source_reports", []) if isinstance(item, Mapping)
    }
    if manifest.get("source_review_cards_report_hash") != source_reports.get(
        "residual_operator_reconciliation_review_cards",
        {},
    ).get("report_hash"):
        errors.append("source review cards report hash mismatch")
        result["source_hash_mismatch_count"] += 1
    if manifest.get("source_evidence_intake_report_hash") != source_reports.get(
        "residual_operator_evidence_intake_audit",
        {},
    ).get("report_hash"):
        errors.append("source evidence intake report hash mismatch")
        result["source_hash_mismatch_count"] += 1

    unsafe_manifest_flags = _false_permission_fields(manifest)
    attestation = manifest.get("operator_attestation", {})
    if not isinstance(attestation, Mapping):
        errors.append("operator_attestation must be object")
        attestation = {}
    unsafe_attestation_flags = _false_permission_fields(attestation)
    result["unsafe_manifest_flag_count"] += len(unsafe_manifest_flags) + len(unsafe_attestation_flags)
    for field in unsafe_manifest_flags:
        errors.append(f"manifest attempted forbidden permission: {field}")
    for field in unsafe_attestation_flags:
        errors.append(f"operator_attestation attempted forbidden permission: {field}")
    if attestation.get("credential_values_excluded") is not True:
        errors.append("operator_attestation must exclude credential values")
    if attestation.get("no_live_or_scale_mutation") is not True:
        errors.append("operator_attestation must confirm no live or scale mutation")

    items = manifest.get("manifest_items", [])
    if not isinstance(items, list):
        errors.append("manifest_items must be array")
        items = []
    result["manifest_item_count"] = len(items)
    seen: set[str] = set()
    missing_ids = set(expected_by_id)
    for item in items:
        if not isinstance(item, Mapping):
            errors.append("manifest item must be object")
            continue
        intake_item_id = str(item.get("intake_item_id", ""))
        expected = expected_by_id.get(intake_item_id)
        if intake_item_id in seen:
            result["duplicate_manifest_item_count"] += 1
            errors.append(f"duplicate manifest item: {intake_item_id}")
        seen.add(intake_item_id)
        if expected is None:
            result["unexpected_manifest_item_count"] += 1
            errors.append(f"unexpected manifest item: {intake_item_id}")
            continue
        missing_ids.discard(intake_item_id)
        for field in (
            "review_card_id",
            "cycle_id",
            "required_resolution_evidence_kind",
            "source_decision_candidate_rollup_hash",
        ):
            if str(item.get(field, "")) != str(expected.get(field, "")):
                result["mismatched_manifest_item_count"] += 1
                errors.append(f"manifest item {intake_item_id} field mismatch: {field}")
        if item.get("operator_decision") not in SAFE_OPERATOR_DECISIONS:
            result["mismatched_manifest_item_count"] += 1
            errors.append(f"manifest item {intake_item_id} has unsafe operator_decision")
        evidence_path = str(item.get("evidence_artifact_path", ""))
        if not _safe_relative_submission_path(evidence_path):
            result["path_policy_violation_count"] += 1
            errors.append(f"manifest item {intake_item_id} evidence path violates submission policy")
        evidence_hash = str(item.get("evidence_artifact_sha256", ""))
        if len(evidence_hash) != 64:
            result["mismatched_manifest_item_count"] += 1
            errors.append(f"manifest item {intake_item_id} evidence hash must be 64 hex chars")
        unsafe_item_flags = _false_permission_fields(item)
        result["unsafe_manifest_flag_count"] += len(unsafe_item_flags)
        for field in unsafe_item_flags:
            errors.append(f"manifest item {intake_item_id} attempted forbidden permission: {field}")
    result["missing_manifest_item_count"] = len(missing_ids)
    for intake_item_id in sorted(missing_ids):
        errors.append(f"missing manifest item: {intake_item_id}")

    controls = manifest.get("control_assertions", [])
    if not isinstance(controls, list):
        errors.append("control_assertions must be array")
        controls = []
    result["manifest_control_count"] = len(controls)
    seen_controls: set[str] = set()
    missing_controls = set(expected_control_by_id)
    for control in controls:
        if not isinstance(control, Mapping):
            errors.append("control assertion must be object")
            continue
        control_id = str(control.get("control_id", ""))
        if control_id in seen_controls:
            result["duplicate_control_count"] += 1
            errors.append(f"duplicate control assertion: {control_id}")
        seen_controls.add(control_id)
        expected_control = expected_control_by_id.get(control_id)
        if expected_control is None:
            errors.append(f"unexpected control assertion: {control_id}")
            continue
        missing_controls.discard(control_id)
        if control.get("operator_assertion_present") is not True:
            errors.append(f"control assertion {control_id} must be present")
        if control.get("accepted_for_reconciliation") is not False:
            result["unsafe_manifest_flag_count"] += 1
            errors.append(f"control assertion {control_id} cannot be accepted in manifest preflight")
        unsafe_control_flags = _false_permission_fields(control)
        result["unsafe_manifest_flag_count"] += len(unsafe_control_flags)
        for field in unsafe_control_flags:
            errors.append(f"control assertion {control_id} attempted forbidden permission: {field}")
    result["missing_control_count"] = len(missing_controls)
    for control_id in sorted(missing_controls):
        errors.append(f"missing control assertion: {control_id}")

    manifest_hash = manifest.get("manifest_hash")
    expected_hash = sha256_json({key: value for key, value in manifest.items() if key != "manifest_hash"})
    if manifest_hash != expected_hash:
        errors.append("manifest_hash mismatch")
    return result


def build_residual_operator_reconciliation_submission_manifest_preflight_report(
    intake_preflight_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    root: Path,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    manifest_file_status, manifest, manifest_load_errors = _read_manifest(root)
    expected_items = _expected_item_templates(intake_preflight_report)
    expected_controls = _expected_control_templates(intake_preflight_report)
    validation = _validate_manifest_against_intake(manifest, intake_preflight_report)
    validation["manifest_errors"].extend(manifest_load_errors)
    has_manifest = manifest is not None
    has_errors = bool(validation["manifest_errors"])
    manifest_status = (
        MISSING_MANIFEST_STATUS
        if not (root / RECONCILIATION_MANIFEST_PATH).exists()
        else "PRESENT_STRUCTURAL_INVALID"
        if has_errors
        else "PRESENT_STRUCTURAL_CHECK_ONLY"
    )
    preflight_status = (
        MISSING_PREFLIGHT_STATUS
        if manifest_status == MISSING_MANIFEST_STATUS
        else STRUCTURAL_ERROR_STATUS
        if has_errors
        else STRUCTURAL_REVIEW_STATUS
    )
    schema_validation_status = (
        "NOT_RUN_MISSING"
        if manifest_status == MISSING_MANIFEST_STATUS
        else "FAIL_STRUCTURAL"
        if has_errors
        else "PASS_STRUCTURAL_ONLY"
    )
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    first_missing = expected_items[0] if expected_items else {}
    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": [_source_report_ref("residual_operator_reconciliation_intake_preflight", intake_preflight_report)],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "manifest_schema_id": MANIFEST_SCHEMA_ID,
        "operator_reconciliation_submission_manifest_path": RECONCILIATION_MANIFEST_PATH,
        "manifest_file_status": manifest_file_status,
        "manifest_status": manifest_status,
        "manifest_preflight_status": preflight_status,
        "manifest_schema_validation_status": schema_validation_status,
        "operator_submission_required": True,
        "operator_submission_present": has_manifest,
        "operator_submission_validated": False,
        "operator_submission_accepted": False,
        "manifest_structural_check_only": has_manifest and not has_errors,
        "required_manifest_item_count": len(expected_items),
        "manifest_item_count": int(validation["manifest_item_count"]),
        "missing_manifest_item_count": int(validation["missing_manifest_item_count"]),
        "duplicate_manifest_item_count": int(validation["duplicate_manifest_item_count"]),
        "unexpected_manifest_item_count": int(validation["unexpected_manifest_item_count"]),
        "mismatched_manifest_item_count": int(validation["mismatched_manifest_item_count"]),
        "required_control_count": len(expected_controls),
        "manifest_control_count": int(validation["manifest_control_count"]),
        "missing_control_count": int(validation["missing_control_count"]),
        "duplicate_control_count": int(validation["duplicate_control_count"]),
        "unsafe_manifest_flag_count": int(validation["unsafe_manifest_flag_count"]),
        "path_policy_violation_count": int(validation["path_policy_violation_count"]),
        "source_hash_mismatch_count": int(validation["source_hash_mismatch_count"]),
        "first_missing_manifest_item": first_missing,
        "manifest_template_preview": expected_items[:4],
        "manifest_control_template": expected_controls,
        "blocking_reasons": (
            [MISSING_MANIFEST_STATUS]
            if manifest_status == MISSING_MANIFEST_STATUS
            else ["OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_STRUCTURAL_ERRORS"]
            if has_errors
            else ["OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_REVIEW_NOT_ACCEPTED"]
        ),
        "manifest_validation_errors": list(validation["manifest_errors"]),
        "one_line_summary": (
            f"Operator reconciliation submission manifest is {manifest_status}; "
            f"{validation['missing_manifest_item_count']} of {len(expected_items)} manifest items are missing."
        ),
        "primary_next_action": (
            "Prepare or repair the operator reconciliation submission manifest under system/evidence/operator_submissions; "
            "this preflight can only run structural checks and cannot accept evidence or write current evidence."
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


def validate_residual_operator_reconciliation_submission_manifest_preflight_report(
    report: Mapping[str, Any],
    intake_preflight_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if report.get("manifest_schema_id") != MANIFEST_SCHEMA_ID:
        errors.append("manifest_schema_id mismatch")
    if intake_preflight_report.get("schema_id") != INTAKE_PREFLIGHT_SCHEMA_ID:
        errors.append("intake preflight source schema mismatch")
    if intake_preflight_report.get("preflight_status") != "BLOCKED_RECONCILIATION_INTAKE_PACKAGE_MISSING":
        errors.append("intake preflight source must remain blocked")
    if intake_preflight_report.get("operator_submission_validated") is not False:
        errors.append("intake preflight source cannot be validated")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        if intake_preflight_report.get(field) is not False:
            errors.append(f"intake preflight {field} must remain false")
    for field in (
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
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids or report.get("open_gap_count") != len(open_gap_ids):
        errors.append("open gap ids/count must match current implementation state")

    expected_item_count = len(_expected_item_templates(intake_preflight_report))
    expected_control_count = len(_expected_control_templates(intake_preflight_report))
    if report.get("required_manifest_item_count") != expected_item_count:
        errors.append("required_manifest_item_count must match intake items")
    if report.get("required_control_count") != expected_control_count:
        errors.append("required_control_count must match intake controls")
    if report.get("manifest_status") == MISSING_MANIFEST_STATUS:
        if report.get("manifest_preflight_status") != MISSING_PREFLIGHT_STATUS:
            errors.append("missing manifest must use missing preflight status")
        if report.get("manifest_schema_validation_status") != "NOT_RUN_MISSING":
            errors.append("missing manifest must not claim schema validation")
        if report.get("missing_manifest_item_count") != expected_item_count:
            errors.append("missing manifest item count must equal expected item count")
        if report.get("manifest_control_count") != 0:
            errors.append("missing manifest cannot have controls")
        if report.get("operator_submission_present") is not False:
            errors.append("missing manifest cannot be present")
    elif report.get("manifest_preflight_status") == STRUCTURAL_REVIEW_STATUS:
        if report.get("manifest_schema_validation_status") != "PASS_STRUCTURAL_ONLY":
            errors.append("structural review must be PASS_STRUCTURAL_ONLY")
        if report.get("operator_submission_present") is not True:
            errors.append("structural review requires present manifest")
        if report.get("operator_submission_accepted") is not False:
            errors.append("structural review cannot accept operator submission")
    else:
        if report.get("manifest_preflight_status") != STRUCTURAL_ERROR_STATUS:
            errors.append("invalid manifest must use structural error status")
    if report.get("unsafe_manifest_flag_count", 0) != 0 and report.get("manifest_preflight_status") != STRUCTURAL_ERROR_STATUS:
        errors.append("unsafe manifest flags must force structural error status")

    for item in report.get("manifest_template_preview", []):
        if not isinstance(item, Mapping):
            errors.append("manifest template preview item must be object")
            continue
        if item.get("current_evidence_write_requested") is not False:
            errors.append("manifest template cannot request current evidence writes")
        if item.get("live_order_allowed") is not False or item.get("scale_up_allowed") is not False:
            errors.append("manifest template cannot allow live or scale")
        if not str(item.get("evidence_artifact_path_rule", "")).startswith("must start with system/evidence/operator_submissions/"):
            errors.append("manifest template must constrain evidence path")
    for control in report.get("manifest_control_template", []):
        if not isinstance(control, Mapping):
            errors.append("manifest control template item must be object")
            continue
        if control.get("current_evidence_write_requested") is not False:
            errors.append("manifest control template cannot request current evidence writes")
        if control.get("accepted_for_reconciliation") is not False:
            errors.append("manifest control template cannot be accepted")
        if control.get("live_order_allowed") is not False or control.get("scale_up_allowed") is not False:
            errors.append("manifest control template cannot allow live or scale")

    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
