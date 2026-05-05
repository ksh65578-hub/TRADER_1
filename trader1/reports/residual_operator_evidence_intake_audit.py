from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_ID = "trader1.residual_operator_evidence_intake_audit_report.v1"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
RUNTIME_PREFIX = "system/runtime/"
OPERATOR_SUBMISSION_MANIFEST_PATH = (
    "system/evidence/operator_submissions/residual_operator_adaptive_evidence_submission_manifest.json"
)
PLACEHOLDER_TOKENS = ("<session_id>", "<shadow_session_id>")


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _source_report_ref(role: str, report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "role": role,
        "patch_id": str(report.get("patch_id", "")),
        "report_hash": str(report.get("report_hash", "")),
    }


def _path_status(path: str, root: Path) -> str:
    if any(token in path for token in PLACEHOLDER_TOKENS):
        return "PLACEHOLDER_PATTERN_PENDING"
    if path.startswith(RUNTIME_PREFIX):
        return "LOCAL_RUNTIME_OUTPUT_PRESENT_NOT_REVIEW_PACKAGE" if (root / path).exists() else "LOCAL_RUNTIME_OUTPUT_MISSING"
    if path.endswith("paper_shadow_evidence_accumulation_report.json"):
        return "OPERATOR_REVIEW_REPORT_PRESENT_NOT_BOUND" if (root / path).exists() else "OPERATOR_REVIEW_REPORT_MISSING"
    return "PRESENT_NOT_BOUND_TO_OPERATOR_PACKAGE" if (root / path).exists() else "MISSING_OPERATOR_EVIDENCE"


def _manifest_status(root: Path) -> str:
    if (root / OPERATOR_SUBMISSION_MANIFEST_PATH).exists():
        return "PRESENT_NOT_VALIDATED"
    return "MISSING_OPERATOR_SUBMISSION_MANIFEST"


def _build_expected_artifact_intake_items(preflight_report: Mapping[str, Any], root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, source_item in enumerate(preflight_report.get("expected_runtime_artifacts", []), start=1):
        if not isinstance(source_item, Mapping):
            continue
        path = str(source_item.get("path", ""))
        intake_status = _path_status(path, root)
        items.append(
            {
                "artifact_intake_id": f"OPERATOR-EVIDENCE-ARTIFACT:{index}",
                "path": path,
                "preflight_path_status": str(source_item.get("current_path_status", "")),
                "intake_path_status": intake_status,
                "operator_package_required": True,
                "content_hash_recorded": False,
                "content_hash_recording_policy": "DISABLED_UNTIL_OPERATOR_SUBMISSION_MANIFEST_VALIDATED",
                "review_ready": False,
                "blocks_mvp5_entry": True,
                "current_evidence_write_allowed": False,
                "gap_closure_allowed_by_this_patch": False,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
    return items


def _build_validator_queue(preflight_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    validators = list(dict.fromkeys(str(item) for item in preflight_report.get("required_validator_ids", [])))
    return [
        {
            "validator_id": validator_id,
            "required_before_mvp5_review": True,
            "run_status_for_this_patch": "QUEUED_AFTER_OPERATOR_EVIDENCE",
            "blocks_mvp5_entry_until_pass": True,
        }
        for validator_id in validators
    ]


def build_residual_operator_evidence_intake_audit_report(
    preflight_report: Mapping[str, Any],
    progress_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    root: Path,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    expected_items = _build_expected_artifact_intake_items(preflight_report, root)
    validator_queue = _build_validator_queue(preflight_report)
    status_counts: dict[str, int] = {}
    for item in expected_items:
        status = item["intake_path_status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    manifest_status = _manifest_status(root)
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
            _source_report_ref("residual_operator_evidence_run_preflight", preflight_report),
            _source_report_ref("residual_operator_evidence_progress", progress_report),
        ],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "intake_status": "BLOCKED_AWAITING_OPERATOR_EVIDENCE_PACKAGE",
        "operator_submission_manifest_path": OPERATOR_SUBMISSION_MANIFEST_PATH,
        "operator_submission_manifest_status": manifest_status,
        "operator_submission_required": True,
        "operator_submission_validated": False,
        "expected_artifact_count": len(expected_items),
        "local_runtime_output_observed_count": status_counts.get("LOCAL_RUNTIME_OUTPUT_PRESENT_NOT_REVIEW_PACKAGE", 0),
        "missing_expected_artifact_count": (
            status_counts.get("LOCAL_RUNTIME_OUTPUT_MISSING", 0)
            + status_counts.get("OPERATOR_REVIEW_REPORT_MISSING", 0)
            + status_counts.get("MISSING_OPERATOR_EVIDENCE", 0)
        ),
        "placeholder_expected_artifact_count": status_counts.get("PLACEHOLDER_PATTERN_PENDING", 0),
        "ready_for_review_artifact_count": 0,
        "expected_artifact_intake_items": expected_items,
        "validator_queue_count": len(validator_queue),
        "validator_queue": validator_queue,
        "preflight_command_id": str(preflight_report.get("command_id", "")),
        "preflight_command_text": str(preflight_report.get("command_text", "")),
        "minimum_duration_hours": int(preflight_report.get("minimum_duration_hours", 0) or 0),
        "expected_heartbeat_ticks": int(preflight_report.get("expected_heartbeat_ticks", 0) or 0),
        "minimum_paper_shadow_window_count": int(preflight_report.get("minimum_paper_shadow_window_count", 0) or 0),
        "command_executed_by_this_patch": False,
        "operator_run_completed_by_this_patch": False,
        "operator_run_evidence_ready_for_mvp5": False,
        "intake_review_ready": False,
        "mvp5_entry_blocked_until_operator_evidence": True,
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_config_mutation_allowed": False,
        "live_ready_write_allowed": False,
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


def validate_residual_operator_evidence_intake_audit_report(
    report: Mapping[str, Any],
    preflight_report: Mapping[str, Any],
    progress_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if report.get("open_gap_ids") != sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", [])):
        errors.append("open_gap_ids must match current state")
    if preflight_report.get("preflight_status") != "NON_LIVE_OPERATOR_RUN_PRECHECK_PASS":
        errors.append("source preflight must pass non-live precheck")
    if progress_report.get("progress_status") != "BLOCKED_EVIDENCE_MISSING":
        errors.append("source progress report must remain blocked evidence missing")

    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        if preflight_report.get(field) is not False:
            errors.append(f"preflight {field} must remain false")
        if progress_report.get(field) is not False:
            errors.append(f"progress {field} must remain false")

    false_fields = (
        "operator_submission_validated",
        "command_executed_by_this_patch",
        "operator_run_completed_by_this_patch",
        "operator_run_evidence_ready_for_mvp5",
        "intake_review_ready",
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_config_mutation_allowed",
        "live_ready_write_allowed",
        "credential_values_read",
        "credential_environment_inspection_performed",
        "runtime_artifacts_staged_by_this_patch",
    )
    for field in false_fields:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
    if report.get("operator_submission_required") is not True:
        errors.append("operator_submission_required must remain true")
    if report.get("mvp5_entry_blocked_until_operator_evidence") is not True:
        errors.append("mvp5 entry must stay blocked until operator evidence")
    if report.get("intake_status") != "BLOCKED_AWAITING_OPERATOR_EVIDENCE_PACKAGE":
        errors.append("intake_status must remain BLOCKED_AWAITING_OPERATOR_EVIDENCE_PACKAGE")
    if report.get("operator_submission_manifest_status") == "REVIEW_READY":
        errors.append("operator submission manifest cannot be REVIEW_READY in this patch")

    items = report.get("expected_artifact_intake_items", [])
    if not isinstance(items, list):
        return errors + ["expected_artifact_intake_items must be an array"]
    if report.get("expected_artifact_count") != len(items):
        errors.append("expected_artifact_count must match expected_artifact_intake_items")
    ready_count = 0
    for item in items:
        if not isinstance(item, Mapping):
            errors.append("artifact intake item must be object")
            continue
        if item.get("content_hash_recorded") is not False:
            errors.append("artifact content hash must not be recorded before operator manifest validation")
        if item.get("review_ready") is not False:
            ready_count += 1
            errors.append("artifact intake item cannot be review_ready in this patch")
        for field in (
            "current_evidence_write_allowed",
            "gap_closure_allowed_by_this_patch",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            if item.get(field) is not False:
                errors.append(f"artifact intake item {field} must remain false")
    if report.get("ready_for_review_artifact_count") != ready_count:
        errors.append("ready_for_review_artifact_count must match artifact items")

    queue = report.get("validator_queue", [])
    if not isinstance(queue, list):
        return errors + ["validator_queue must be an array"]
    if report.get("validator_queue_count") != len(queue):
        errors.append("validator_queue_count must match validator_queue")
    required_validators = set(str(item) for item in preflight_report.get("required_validator_ids", []))
    queued_validators = {str(item.get("validator_id", "")) for item in queue if isinstance(item, Mapping)}
    if required_validators != queued_validators:
        errors.append("validator queue must match preflight required validators")
    for item in queue:
        if not isinstance(item, Mapping):
            errors.append("validator queue item must be object")
            continue
        if item.get("run_status_for_this_patch") != "QUEUED_AFTER_OPERATOR_EVIDENCE":
            errors.append("validator queue must remain queued after operator evidence")
        if item.get("blocks_mvp5_entry_until_pass") is not True:
            errors.append("validator queue must block MVP5 until pass")

    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    return errors
