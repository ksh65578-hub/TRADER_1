from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS


SCHEMA_ID = "trader1.external_live_evidence_intake_preflight_report.v1"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

BLOCKED_REQUIREMENT_IDS = (
    "REQ-MVP4-OFFICIAL-API-PASS-EVIDENCE",
    "REQ-MVP4-OPERATOR-APPROVAL-EVIDENCE",
    "REQ-MVP4-READ-ONLY-ACCOUNT-SNAPSHOT-EVIDENCE",
    "REQ-MVP4-READ-ONLY-BURN-IN-EVIDENCE",
)

EVIDENCE_REQUIREMENTS: tuple[dict[str, Any], ...] = (
    {
        "requirement_id": "REQ-MVP4-OFFICIAL-API-PASS-EVIDENCE",
        "evidence_kind": "OFFICIAL_API_VERIFICATION",
        "expected_artifact_path": (
            "system/evidence/upbit/krw_spot/read_only/mvp4_live_review/"
            "official_api_verification_report.json"
        ),
        "required_schema_id": "trader1.official_api_verification_report.v1",
        "validator_id": "official_api_verification_validator",
        "expected_exchange": "UPBIT",
        "expected_market_type": "KRW_SPOT",
        "expected_mode": "READ_ONLY",
        "fallback_status": "UNVERIFIED",
        "fallback_blocker_code": "API_UNVERIFIED",
        "closure_preconditions": [
            "official API verification PASS for the exact exchange, market_type, and READ_ONLY scope",
            "official sources and content hashes are current and independently reviewable",
            "live final guard remains PASS with live permission still false until a separate reviewed live path exists",
        ],
    },
    {
        "requirement_id": "REQ-MVP4-READ-ONLY-ACCOUNT-SNAPSHOT-EVIDENCE",
        "evidence_kind": "READ_ONLY_ACCOUNT_SNAPSHOT",
        "expected_artifact_path": (
            "system/runtime/upbit/krw_spot/read_only/mvp4_live_review/"
            "read_only_account_snapshot.json"
        ),
        "required_schema_id": "trader1.read_only_account_snapshot.v1",
        "validator_id": "upbit_live_review_preflight_validator",
        "expected_exchange": "UPBIT",
        "expected_market_type": "KRW_SPOT",
        "expected_mode": "READ_ONLY",
        "fallback_status": "UNVERIFIED",
        "fallback_blocker_code": "API_UNVERIFIED",
        "closure_preconditions": [
            "read-only account snapshot exists for the exact scope",
            "snapshot proves no order adapter call and no order permission",
            "snapshot is reconciled without exposing credentials or enabling private write actions",
        ],
    },
    {
        "requirement_id": "REQ-MVP4-OPERATOR-APPROVAL-EVIDENCE",
        "evidence_kind": "OPERATOR_APPROVAL",
        "expected_artifact_path": (
            "system/evidence/upbit/krw_spot/live/mvp4_live_review/"
            "operator_approval_evidence.json"
        ),
        "required_schema_id": "trader1.operator_action_audit.v1",
        "validator_id": "operator_control_validator",
        "expected_exchange": "UPBIT",
        "expected_market_type": "KRW_SPOT",
        "expected_mode": "LIVE",
        "fallback_status": "MISSING",
        "fallback_blocker_code": "OPERATOR_APPROVAL_MISSING",
        "closure_preconditions": [
            "operator approval evidence is supplied outside this non-live patch",
            "approval is scoped to the exact exchange, market_type, mode, and session",
            "approval does not directly mutate live config or bypass live final guard",
        ],
    },
    {
        "requirement_id": "REQ-MVP4-READ-ONLY-BURN-IN-EVIDENCE",
        "evidence_kind": "READ_ONLY_BURN_IN",
        "expected_artifact_path": (
            "system/evidence/upbit/krw_spot/read_only/mvp4_live_review/"
            "read_only_burn_in_feedback_report.json"
        ),
        "required_schema_id": "trader1.live_burn_in_feedback_report.v1",
        "validator_id": "live_burn_in_feedback_validator",
        "expected_exchange": "UPBIT",
        "expected_market_type": "KRW_SPOT",
        "expected_mode": "READ_ONLY",
        "fallback_status": "MISSING",
        "fallback_blocker_code": "READ_ONLY_BURN_IN_MISSING",
        "closure_preconditions": [
            "read-only burn-in feedback exists for the exact scope",
            "paper/live parity, execution quality, and survival layer blockers are reconciled",
            "scale-up remains disabled unless scale-up eligibility independently passes later",
        ],
    },
)


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _source_review_status_by_path(manifest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    statuses: dict[str, Mapping[str, Any]] = {}
    for item in manifest.get("external_review_input_statuses", []):
        if isinstance(item, Mapping):
            artifact_path = str(item.get("artifact_path", ""))
            if artifact_path:
                statuses[artifact_path] = item
    return statuses


def _source_status_for(requirement: Mapping[str, Any], manifest: Mapping[str, Any]) -> Mapping[str, Any] | None:
    return _source_review_status_by_path(manifest).get(str(requirement["expected_artifact_path"]))


def _artifact_sha256(status: Mapping[str, Any] | None) -> str | None:
    if not status:
        return None
    value = status.get("artifact_sha256")
    return str(value) if value else None


def _build_evidence_item(requirement: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    status = _source_status_for(requirement, manifest)
    source_status = str(status.get("status", requirement["fallback_status"])) if status else str(requirement["fallback_status"])
    source_exists = bool(status.get("exists")) if status else False
    primary_blocker = (
        str(status.get("primary_blocker_code", requirement["fallback_blocker_code"]))
        if status
        else str(requirement["fallback_blocker_code"])
    )
    usable_for_live = bool(status.get("usable_for_live_enabling")) if status else False
    intake_status = "MISSING" if not source_exists or source_status == "MISSING" else "UNUSABLE_UNVERIFIED"

    return {
        "requirement_id": str(requirement["requirement_id"]),
        "evidence_kind": str(requirement["evidence_kind"]),
        "expected_artifact_path": str(requirement["expected_artifact_path"]),
        "source_artifact_path": str(status.get("artifact_path")) if status else None,
        "source_artifact_exists": source_exists,
        "source_artifact_sha256": _artifact_sha256(status),
        "source_status": source_status,
        "required_schema_id": str(requirement["required_schema_id"]),
        "validator_id": str(requirement["validator_id"]),
        "expected_exchange": str(requirement["expected_exchange"]),
        "expected_market_type": str(requirement["expected_market_type"]),
        "expected_mode": str(requirement["expected_mode"]),
        "primary_blocker_code": primary_blocker,
        "closure_preconditions": list(requirement["closure_preconditions"]),
        "intake_status": intake_status,
        "usable_for_live_enabling": usable_for_live,
        "credential_required_by_this_patch": False,
        "api_call_required_by_this_patch": False,
        "live_order_required_by_this_patch": False,
        "live_config_mutation_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _unmapped_source_review_inputs(manifest: Mapping[str, Any]) -> list[str]:
    expected_paths = {str(item["expected_artifact_path"]) for item in EVIDENCE_REQUIREMENTS}
    return sorted(
        str(item.get("artifact_path"))
        for item in manifest.get("external_review_input_statuses", [])
        if isinstance(item, Mapping)
        and item.get("artifact_path")
        and str(item["artifact_path"]) not in expected_paths
    )


def build_external_live_evidence_intake_preflight_report(
    external_blocker_manifest: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
    source_manifest_path: str,
    source_manifest_sha256: str,
) -> dict[str, Any]:
    blocked_requirement_ids = sorted(str(item) for item in state.get("blocked_requirement_ids", []))
    evidence_items = [_build_evidence_item(requirement, external_blocker_manifest) for requirement in EVIDENCE_REQUIREMENTS]
    intake_ready_count = sum(1 for item in evidence_items if item["intake_status"] == "INTAKE_READY")
    missing_or_unusable_count = sum(1 for item in evidence_items if not item["usable_for_live_enabling"])
    expected_blocked_requirement_ids = sorted(BLOCKED_REQUIREMENT_IDS)

    status_inputs_pass = (
        blocked_requirement_ids == expected_blocked_requirement_ids
        and len(evidence_items) == len(expected_blocked_requirement_ids)
        and intake_ready_count == 0
        and missing_or_unusable_count == len(expected_blocked_requirement_ids)
        and all(item["usable_for_live_enabling"] is False for item in evidence_items)
    )

    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_manifest": {
            "path": source_manifest_path,
            "evidence_manifest_id": str(external_blocker_manifest.get("evidence_manifest_id", "")),
            "patch_id": str(external_blocker_manifest.get("patch_id", "")),
            "artifact_sha256": source_manifest_sha256,
        },
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "expected_blocked_requirement_ids": expected_blocked_requirement_ids,
        "blocked_requirement_ids": blocked_requirement_ids,
        "blocked_requirement_count": len(blocked_requirement_ids),
        "evidence_item_count": len(evidence_items),
        "intake_ready_count": intake_ready_count,
        "missing_or_unusable_count": missing_or_unusable_count,
        "unmapped_source_review_inputs": _unmapped_source_review_inputs(external_blocker_manifest),
        "preflight_status": "BLOCKED_EXTERNAL_EVIDENCE_MISSING" if status_inputs_pass else "FAIL",
        "external_evidence_collection_performed": False,
        "credential_use_allowed": False,
        "credential_loaded": False,
        "api_call_performed": False,
        "live_order_submitted": False,
        "live_config_mutation_allowed": False,
        "scale_up_allowed_by_this_patch": False,
        "gap_closure_allowed_by_this_patch": False,
        "evidence_items": evidence_items,
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


def validate_external_live_evidence_intake_preflight_report(
    report: Mapping[str, Any],
    external_blocker_manifest: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []

    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        if external_blocker_manifest.get(field) is True:
            errors.append(f"source manifest {field} must not be true")

    for field in (
        "external_evidence_collection_performed",
        "credential_use_allowed",
        "credential_loaded",
        "api_call_performed",
        "live_order_submitted",
        "live_config_mutation_allowed",
        "scale_up_allowed_by_this_patch",
        "gap_closure_allowed_by_this_patch",
    ):
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")

    expected_blocked = sorted(BLOCKED_REQUIREMENT_IDS)
    state_blocked = sorted(str(item) for item in state.get("blocked_requirement_ids", []))
    if report.get("expected_blocked_requirement_ids") != expected_blocked:
        errors.append("expected_blocked_requirement_ids mismatch")
    if report.get("blocked_requirement_ids") != state_blocked:
        errors.append("blocked_requirement_ids must match current implementation state")
    if state_blocked != expected_blocked:
        errors.append("state blocked_requirement_ids must remain the four external live-readiness requirements")
    if report.get("blocked_requirement_count") != len(expected_blocked):
        errors.append("blocked_requirement_count mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")

    evidence_items = report.get("evidence_items", [])
    if not isinstance(evidence_items, list):
        return errors + ["evidence_items must be an array"]

    seen_requirement_ids = sorted(str(item.get("requirement_id")) for item in evidence_items if isinstance(item, Mapping))
    if seen_requirement_ids != expected_blocked:
        errors.append("evidence_items must cover each blocked requirement exactly once")
    if report.get("evidence_item_count") != len(expected_blocked):
        errors.append("evidence_item_count mismatch")
    if report.get("intake_ready_count") != 0:
        errors.append("intake_ready_count must remain 0")
    if report.get("missing_or_unusable_count") != len(expected_blocked):
        errors.append("missing_or_unusable_count must cover every blocked requirement")

    requirement_by_id = {str(item["requirement_id"]): item for item in EVIDENCE_REQUIREMENTS}
    for item in evidence_items:
        if not isinstance(item, Mapping):
            errors.append("evidence_items contains a non-object item")
            continue
        requirement_id = str(item.get("requirement_id", ""))
        expected = requirement_by_id.get(requirement_id)
        if expected is None:
            errors.append(f"unknown evidence item requirement_id: {requirement_id}")
            continue
        source_status = _source_status_for(expected, external_blocker_manifest)
        if item.get("expected_artifact_path") != expected["expected_artifact_path"]:
            errors.append(f"{requirement_id} expected_artifact_path mismatch")
        if item.get("required_schema_id") != expected["required_schema_id"]:
            errors.append(f"{requirement_id} required_schema_id mismatch")
        if item.get("validator_id") != expected["validator_id"]:
            errors.append(f"{requirement_id} validator_id mismatch")
        if source_status is not None and item.get("source_artifact_path") != source_status.get("artifact_path"):
            errors.append(f"{requirement_id} source_artifact_path mismatch")
        if source_status is None and item.get("source_artifact_path") is not None:
            errors.append(f"{requirement_id} must not invent a source_artifact_path")
        if item.get("usable_for_live_enabling") is not False:
            errors.append(f"{requirement_id} usable_for_live_enabling must remain false")
        if item.get("intake_status") not in ("MISSING", "UNUSABLE_UNVERIFIED"):
            errors.append(f"{requirement_id} intake_status must be blocked")
        for field in (
            "credential_required_by_this_patch",
            "api_call_required_by_this_patch",
            "live_order_required_by_this_patch",
            "live_config_mutation_allowed",
            "gap_closure_allowed_by_this_patch",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            if item.get(field) is not False:
                errors.append(f"{requirement_id} {field} must remain false")

    if report.get("preflight_status") != "BLOCKED_EXTERNAL_EVIDENCE_MISSING":
        errors.append("preflight_status must be BLOCKED_EXTERNAL_EVIDENCE_MISSING")
    if report.get("validation_status") != "PASS":
        errors.append("validation_status must be PASS")
    if report.get("validation_errors") != []:
        errors.append("validation_errors must be empty")

    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
