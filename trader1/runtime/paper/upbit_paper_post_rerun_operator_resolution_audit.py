from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from trader1.runtime.paper.upbit_paper_post_rerun_current_evidence_promotion_guard import (
    POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
)
from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_reconciliation_review_guidance import (
    POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_STATUS,
    POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_ITEM_STATUS,
    upbit_paper_post_rerun_operator_reconciliation_review_guidance_hash,
    validate_upbit_paper_post_rerun_operator_reconciliation_review_guidance_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_decision_audit import (
    POST_RERUN_RECONCILIATION_WRITE_DENIED_STATUS,
    upbit_paper_post_rerun_reconciliation_decision_audit_hash,
    validate_upbit_paper_post_rerun_reconciliation_decision_audit_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT_SCHEMA_ID = (
    "trader1.upbit_paper_post_rerun_operator_resolution_audit_report.v1"
)
POST_RERUN_OPERATOR_RESOLUTION_AUDIT_TRUTH_ROLE = (
    "PAPER_RUNTIME_POST_RERUN_OPERATOR_RESOLUTION_AUDIT_REVIEW_ONLY_NOT_WRITER"
)
POST_RERUN_OPERATOR_RESOLUTION_AUDIT_ROLE = (
    "PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT_NOT_CURRENT_EVIDENCE"
)
POST_RERUN_OPERATOR_RESOLUTION_AUDIT_STATUS = "UNRESOLVED_RECONCILIATION_REVIEW_ONLY"
POST_RERUN_OPERATOR_RESOLUTION_AUDIT_OUTCOME = (
    "OPERATOR_RESOLUTION_NOT_ACCEPTED_CURRENT_EVIDENCE_BLOCKED"
)
POST_RERUN_OPERATOR_RESOLUTION_ITEM_STATUS = "UNRESOLVED_CURRENT_EVIDENCE_BLOCKED"
POST_RERUN_RESOLUTION_AUDIT_SOURCE_BINDING_REQUIRED = (
    "POST_RERUN_RESOLUTION_AUDIT_SOURCE_BINDING_REQUIRED"
)


@dataclass(frozen=True)
class UpbitPaperPostRerunOperatorResolutionAuditValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_post_rerun_operator_resolution_audit_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("resolution_audit_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    return normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "/live/" not in normalized


def _candidate_rollup_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return _artifact_path_allowed(normalized, session_id) and "/paper_runtime/rerun_candidates_post_rollup/" in normalized


def _current_ledger_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        _artifact_path_allowed(normalized, session_id)
        and normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/cycles/")
        and normalized.endswith(".paper_ledger_events.jsonl")
    )


def _source_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return _artifact_path_allowed(normalized, session_id) and normalized.endswith(".json")


def _safe_load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "MISSING"
    except UnicodeDecodeError:
        return None, "INVALID_UTF8"
    except json.JSONDecodeError:
        return None, "INVALID_JSON"
    if not isinstance(value, dict):
        return None, "NOT_OBJECT"
    return value, None


def _source_file_binding(
    *,
    root: Path,
    relative_path: str,
    expected_hash: Any,
    session_id: str,
    hash_field: str,
    recompute_hash: Callable[[dict[str, Any]], str],
    field_prefix: str,
) -> dict[str, Any]:
    if not _source_path_allowed(relative_path, session_id):
        return {
            f"{field_prefix}_file_load_status": "SCOPE_MISMATCH",
            f"{field_prefix}_file_hash": None,
            f"{field_prefix}_file_recomputed_hash": None,
            f"{field_prefix}_file_hash_match": False,
        }
    source, source_error = _safe_load_json(_rooted(root, relative_path))
    if source is None:
        return {
            f"{field_prefix}_file_load_status": str(source_error or "UNKNOWN"),
            f"{field_prefix}_file_hash": None,
            f"{field_prefix}_file_recomputed_hash": None,
            f"{field_prefix}_file_hash_match": False,
        }
    file_hash = source.get(hash_field)
    recomputed_hash = recompute_hash(source)
    hash_match = bool(file_hash == expected_hash == recomputed_hash)
    return {
        f"{field_prefix}_file_load_status": "PASS" if hash_match else "HASH_MISMATCH",
        f"{field_prefix}_file_hash": file_hash,
        f"{field_prefix}_file_recomputed_hash": recomputed_hash,
        f"{field_prefix}_file_hash_match": hash_match,
    }


def _join_key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item.get("replacement_loop_id") or "UNKNOWN"), str(item.get("cycle_id") or "UNKNOWN"))


def _resolution_controls() -> list[dict[str, Any]]:
    controls = [
        (
            "OPERATOR_RECONCILIATION_DECISION",
            "Operator reconciliation decision evidence is not present as a validated writer input.",
        ),
        (
            "CURRENT_LEDGER_REBUILD_VALIDATION",
            "Current ledger rebuild validation is not present and current ledger JSONL remains unwritten.",
        ),
        (
            "SOURCE_HASH_RECONCILIATION",
            "Staged candidate hashes are review inputs only and cannot resolve current evidence.",
        ),
        (
            "LIVE_AND_SCALE_BLOCK_CONFIRMATION",
            "LIVE_READY, live orders, and scale-up remain blocked for this scope.",
        ),
    ]
    return [
        {
            "control_order": index,
            "control_id": control_id,
            "required": True,
            "satisfied": False,
            "blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
            "message": message,
        }
        for index, (control_id, message) in enumerate(controls, start=1)
    ]


def _build_resolution_item(
    *,
    priority_order: int,
    guidance_item: dict[str, Any],
    decision_item: dict[str, Any] | None,
) -> dict[str, Any]:
    decision_item = decision_item if isinstance(decision_item, dict) else {}
    guidance_path = str(guidance_item.get("candidate_rollup_artifact_path") or "")
    decision_path = str(decision_item.get("candidate_rollup_artifact_path") or "")
    guidance_ledger_path = str(guidance_item.get("planned_current_ledger_jsonl_path") or "")
    decision_ledger_path = str(decision_item.get("planned_current_ledger_jsonl_path") or "")
    blocking_codes = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    blocking_codes.update(str(code) for code in guidance_item.get("blocking_codes", []) if code)
    blocking_codes.update(str(code) for code in decision_item.get("blocking_codes", []) if code)
    path_scope_status = (
        "MATCH"
        if guidance_path
        and guidance_path == decision_path
        and guidance_ledger_path
        and guidance_ledger_path == decision_ledger_path
        and guidance_item.get("path_scope_status") == "MATCH"
        and decision_item.get("path_scope_status") == "MATCH"
        else "MISMATCH"
    )
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(guidance_item.get("replacement_loop_id") or "UNKNOWN"),
        "cycle_id": str(guidance_item.get("cycle_id") or "UNKNOWN"),
        "source_guidance_review_status": str(guidance_item.get("review_status") or "UNKNOWN"),
        "source_decision_status": str(decision_item.get("decision_status") or "UNKNOWN"),
        "resolution_status": POST_RERUN_OPERATOR_RESOLUTION_ITEM_STATUS,
        "resolution_reason_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "resolution_evidence_present": False,
        "resolution_evidence_accepted": False,
        "candidate_rollup_artifact_path": guidance_path,
        "planned_current_ledger_jsonl_path": guidance_ledger_path,
        "decision_candidate_rollup_hash": decision_item.get("candidate_rollup_hash"),
        "path_scope_status": path_scope_status,
        "required_resolution_evidence": [
            "validated_operator_reconciliation_decision",
            "validated_current_ledger_rebuild",
            "validated_source_hash_reconciliation",
            "validated_no_live_or_scale_mutation",
        ],
        "blocking_codes": sorted(blocking_codes),
        "resolution_notes": (
            "Operator resolution is not accepted. This audit is review-only and keeps current evidence, "
            "latest runtime pointers, LIVE_READY, live orders, and scale-up blocked."
        ),
        "current_evidence_write_authorized": False,
        "candidate_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "live_permission_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_post_rerun_operator_resolution_audit_report(
    *,
    root: Path,
    review_guidance_report: dict[str, Any],
    decision_audit_report: dict[str, Any],
    source_review_guidance_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json",
    source_decision_audit_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_reconciliation_decision_audit_report.json",
    resolution_audit_id: str = "upbit-paper-post-rerun-operator-resolution-audit",
) -> dict[str, Any]:
    root = Path(root).resolve()
    guidance_result = validate_upbit_paper_post_rerun_operator_reconciliation_review_guidance_report(review_guidance_report)
    decision_result = validate_upbit_paper_post_rerun_reconciliation_decision_audit_report(decision_audit_report)
    session_id = str(review_guidance_report.get("session_id") or decision_audit_report.get("session_id") or "UNKNOWN")
    guidance_items = [item for item in review_guidance_report.get("guidance_items", []) if isinstance(item, dict)]
    decision_items = {
        _join_key(item): item
        for item in decision_audit_report.get("items", [])
        if isinstance(item, dict)
    }
    items = [
        _build_resolution_item(
            priority_order=index,
            guidance_item=item,
            decision_item=decision_items.get(_join_key(item)),
        )
        for index, item in enumerate(guidance_items, start=1)
    ] if guidance_result.status == "PASS" and decision_result.status == "PASS" else []
    blockers = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if guidance_result.status != "PASS":
        blockers.add(guidance_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    if decision_result.status != "PASS":
        blockers.add(decision_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    for item in items:
        blockers.update(str(code) for code in item.get("blocking_codes", []) if code)
    source_review_guidance_hash = review_guidance_report.get("guidance_hash")
    source_decision_audit_hash = decision_audit_report.get("decision_audit_hash")
    review_guidance_file_binding = _source_file_binding(
        root=root,
        relative_path=source_review_guidance_path,
        expected_hash=source_review_guidance_hash,
        session_id=session_id,
        hash_field="guidance_hash",
        recompute_hash=upbit_paper_post_rerun_operator_reconciliation_review_guidance_hash,
        field_prefix="source_review_guidance",
    )
    decision_audit_file_binding = _source_file_binding(
        root=root,
        relative_path=source_decision_audit_path,
        expected_hash=source_decision_audit_hash,
        session_id=session_id,
        hash_field="decision_audit_hash",
        recompute_hash=upbit_paper_post_rerun_reconciliation_decision_audit_hash,
        field_prefix="source_decision_audit",
    )
    if (
        review_guidance_file_binding["source_review_guidance_file_load_status"] != "PASS"
        or decision_audit_file_binding["source_decision_audit_file_load_status"] != "PASS"
    ):
        blockers.add(POST_RERUN_RESOLUTION_AUDIT_SOURCE_BINDING_REQUIRED)
    controls = _resolution_controls()
    report = {
        "schema_id": UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "resolution_audit_id": resolution_audit_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_RERUN_OPERATOR_RESOLUTION_AUDIT_TRUTH_ROLE,
        "resolution_audit_role": POST_RERUN_OPERATOR_RESOLUTION_AUDIT_ROLE,
        "source_review_guidance_path": source_review_guidance_path,
        "source_review_guidance_hash": source_review_guidance_hash,
        **review_guidance_file_binding,
        "source_review_guidance_status": review_guidance_report.get("review_guidance_status"),
        "source_review_guidance_primary_blocker_code": review_guidance_report.get("primary_blocker_code"),
        "source_review_guidance_item_count": int(review_guidance_report.get("guidance_item_count") or 0),
        "source_decision_audit_path": source_decision_audit_path,
        "source_decision_audit_hash": source_decision_audit_hash,
        **decision_audit_file_binding,
        "source_decision_audit_status": decision_audit_report.get("decision_audit_status"),
        "source_decision_audit_primary_blocker_code": decision_audit_report.get("primary_blocker_code"),
        "source_decision_item_count": int(decision_audit_report.get("decision_item_count") or 0),
        "source_write_denied_count": int(decision_audit_report.get("write_denied_count") or 0),
        "resolution_audit_status": POST_RERUN_OPERATOR_RESOLUTION_AUDIT_STATUS,
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "resolution_outcome": POST_RERUN_OPERATOR_RESOLUTION_AUDIT_OUTCOME,
        "operator_resolution_required": True,
        "resolution_control_count": len(controls),
        "resolution_controls_satisfied_count": 0,
        "reviewed_guidance_item_count": len(items),
        "reviewed_decision_item_count": sum(1 for item in items if item.get("source_decision_status") != "UNKNOWN"),
        "unresolved_item_count": len(items),
        "resolved_item_count": 0,
        "current_evidence_write_authorized_count": 0,
        "current_evidence_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "blocker_codes": sorted(blockers),
        "resolution_controls": controls,
        "items": items,
        "resolution_audit_next_action": "Keep operator resolution review-only and blocked until a separate validated reconciliation writer path exists.",
        "current_evidence_mutation_allowed": False,
        "current_evidence_write_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "resolution_audit_hash": "",
    }
    report["resolution_audit_hash"] = upbit_paper_post_rerun_operator_resolution_audit_hash(report)
    return report


def write_upbit_paper_post_rerun_operator_resolution_audit_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_post_rerun_operator_resolution_audit_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_rerun_operator_resolution_audit_report(
    report: dict[str, Any],
) -> UpbitPaperPostRerunOperatorResolutionAuditValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "resolution_audit_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "resolution_audit_role",
        "source_review_guidance_path",
        "source_review_guidance_hash",
        "source_review_guidance_file_load_status",
        "source_review_guidance_file_hash",
        "source_review_guidance_file_recomputed_hash",
        "source_review_guidance_file_hash_match",
        "source_review_guidance_status",
        "source_review_guidance_primary_blocker_code",
        "source_review_guidance_item_count",
        "source_decision_audit_path",
        "source_decision_audit_hash",
        "source_decision_audit_file_load_status",
        "source_decision_audit_file_hash",
        "source_decision_audit_file_recomputed_hash",
        "source_decision_audit_file_hash_match",
        "source_decision_audit_status",
        "source_decision_audit_primary_blocker_code",
        "source_decision_item_count",
        "source_write_denied_count",
        "resolution_audit_status",
        "primary_blocker_code",
        "resolution_outcome",
        "operator_resolution_required",
        "resolution_control_count",
        "resolution_controls_satisfied_count",
        "reviewed_guidance_item_count",
        "reviewed_decision_item_count",
        "unresolved_item_count",
        "resolved_item_count",
        "current_evidence_write_authorized_count",
        "current_evidence_write_allowed_count",
        "candidate_current_evidence_usable_count",
        "blocker_codes",
        "resolution_controls",
        "items",
        "resolution_audit_next_action",
        "current_evidence_mutation_allowed",
        "current_evidence_write_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "resolution_audit_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("FAIL", f"post-rerun operator resolution audit missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT_SCHEMA_ID:
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("FAIL", "post-rerun operator resolution audit schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("resolution_audit_hash") != upbit_paper_post_rerun_operator_resolution_audit_hash(report):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("FAIL", "post-rerun operator resolution audit hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "post-rerun operator resolution audit scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != POST_RERUN_OPERATOR_RESOLUTION_AUDIT_TRUTH_ROLE or report.get("resolution_audit_role") != POST_RERUN_OPERATOR_RESOLUTION_AUDIT_ROLE:
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "post-rerun operator resolution audit cannot claim writer or live truth", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "current_evidence_mutation_allowed",
        "current_evidence_write_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "post-rerun operator resolution audit created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if (
        report.get("current_evidence_write_authorized_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
        or report.get("candidate_current_evidence_usable_count") != 0
    ):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "post-rerun operator resolution audit exposed current evidence write/use", "LIVE_FINAL_GUARD_FAILED")
    if (
        report.get("source_review_guidance_status") != POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_STATUS
        or report.get("source_review_guidance_primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("source_decision_audit_status") != "BLOCKED"
        or report.get("source_decision_audit_primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
    ):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "source post-rerun audit boundary mismatch", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if (
        report.get("resolution_audit_status") != POST_RERUN_OPERATOR_RESOLUTION_AUDIT_STATUS
        or report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("resolution_outcome") != POST_RERUN_OPERATOR_RESOLUTION_AUDIT_OUTCOME
        or report.get("operator_resolution_required") is not True
    ):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "post-rerun operator resolution audit must remain unresolved and review-only", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    session_id = str(report.get("session_id"))
    if not _source_path_allowed(str(report.get("source_review_guidance_path") or ""), session_id):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "source review guidance path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if not _source_path_allowed(str(report.get("source_decision_audit_path") or ""), session_id):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "source decision audit path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if (
        report.get("source_review_guidance_file_load_status") != "PASS"
        or report.get("source_review_guidance_file_hash_match") is not True
        or report.get("source_decision_audit_file_load_status") != "PASS"
        or report.get("source_decision_audit_file_hash_match") is not True
    ):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult(
            "BLOCKED",
            "source review guidance or decision audit file binding is missing or mismatched",
            POST_RERUN_RESOLUTION_AUDIT_SOURCE_BINDING_REQUIRED,
        )
    if (
        report.get("source_review_guidance_file_hash") != report.get("source_review_guidance_hash")
        or report.get("source_review_guidance_file_recomputed_hash") != report.get("source_review_guidance_hash")
        or report.get("source_decision_audit_file_hash") != report.get("source_decision_audit_hash")
        or report.get("source_decision_audit_file_recomputed_hash") != report.get("source_decision_audit_hash")
    ):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult(
            "FAIL",
            "source review guidance or decision audit file hash does not match source report hash",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(report.get("blocker_codes") or []):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "post-rerun operator resolution audit missing reconciliation blocker", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    controls = report.get("resolution_controls")
    if not isinstance(controls, list) or report.get("resolution_control_count") != len(controls) or len(controls) < 4:
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("FAIL", "post-rerun operator resolution control count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("resolution_controls_satisfied_count") != 0:
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "post-rerun operator resolution audit accepted unresolved controls", "LIVE_FINAL_GUARD_FAILED")
    for control in controls:
        if not isinstance(control, dict):
            return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("FAIL", "post-rerun operator resolution control must be object", "SCHEMA_IDENTITY_MISMATCH")
        if (
            control.get("required") is not True
            or control.get("satisfied") is not False
            or control.get("blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        ):
            return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "post-rerun operator resolution control lost blocking semantics", "LIVE_FINAL_GUARD_FAILED")
    items = report.get("items")
    if not isinstance(items, list):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("FAIL", "post-rerun operator resolution audit items must be an array", "SCHEMA_IDENTITY_MISMATCH")
    if (
        report.get("source_review_guidance_item_count") != len(items)
        or report.get("reviewed_guidance_item_count") != len(items)
        or report.get("unresolved_item_count") != len(items)
        or report.get("resolved_item_count") != 0
        or report.get("source_decision_item_count") != report.get("reviewed_decision_item_count")
        or report.get("source_write_denied_count") != report.get("reviewed_decision_item_count")
    ):
        return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("FAIL", "post-rerun operator resolution audit count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("FAIL", "post-rerun operator resolution item must be object", "SCHEMA_IDENTITY_MISMATCH")
        if not _candidate_rollup_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "resolution audit candidate rollup path escaped post-rollup namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not _current_ledger_path_allowed(str(item.get("planned_current_ledger_jsonl_path") or ""), session_id):
            return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "resolution audit planned current ledger path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        item_forbidden = (
            "current_evidence_write_authorized",
            "candidate_current_evidence_usable",
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
        )
        if any(item.get(field) for field in item_forbidden):
            return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "post-rerun operator resolution item attempted current evidence or live mutation", "LIVE_FINAL_GUARD_FAILED")
        if (
            item.get("source_guidance_review_status") != POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_ITEM_STATUS
            or item.get("source_decision_status") != POST_RERUN_RECONCILIATION_WRITE_DENIED_STATUS
            or item.get("resolution_status") != POST_RERUN_OPERATOR_RESOLUTION_ITEM_STATUS
            or item.get("resolution_reason_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
            or item.get("resolution_evidence_present") is not False
            or item.get("resolution_evidence_accepted") is not False
            or item.get("path_scope_status") != "MATCH"
            or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(item.get("blocking_codes") or [])
        ):
            return UpbitPaperPostRerunOperatorResolutionAuditValidationResult("BLOCKED", "post-rerun operator resolution item lost unresolved write-blocked state", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    return UpbitPaperPostRerunOperatorResolutionAuditValidationResult(
        "PASS",
        "Upbit PAPER post-rerun operator resolution audit remains review-only and blocks current evidence/live/scale",
        None,
    )
