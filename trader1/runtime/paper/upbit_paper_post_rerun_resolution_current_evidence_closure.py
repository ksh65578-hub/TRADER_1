from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_post_rerun_current_evidence_promotion_guard import (
    POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
)
from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_resolution_audit import (
    POST_RERUN_OPERATOR_RESOLUTION_AUDIT_OUTCOME,
    POST_RERUN_OPERATOR_RESOLUTION_AUDIT_ROLE,
    POST_RERUN_OPERATOR_RESOLUTION_AUDIT_STATUS,
    POST_RERUN_OPERATOR_RESOLUTION_ITEM_STATUS,
    upbit_paper_post_rerun_operator_resolution_audit_hash,
    validate_upbit_paper_post_rerun_operator_resolution_audit_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_SCHEMA_ID = (
    "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1"
)
POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_TRUTH_ROLE = (
    "PAPER_RUNTIME_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REVIEW_ONLY_NOT_WRITER"
)
POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_ROLE = (
    "PAPER_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_NOT_CURRENT_EVIDENCE"
)
POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_STATUS = (
    "CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED"
)
POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_OUTCOME = (
    "RESOLUTION_UNRESOLVED_CURRENT_EVIDENCE_CLOSED"
)
POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_ITEM_STATUS = (
    "CLOSED_CURRENT_EVIDENCE_BLOCKED"
)
POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED = (
    "POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED"
)
POST_RERUN_RESOLUTION_CLOSURE_SOURCE_BINDING_REQUIRED = (
    "POST_RERUN_RESOLUTION_CLOSURE_SOURCE_BINDING_REQUIRED"
)


@dataclass(frozen=True)
class UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_post_rerun_resolution_current_evidence_closure_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("closure_hash", None)
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


def _source_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return _artifact_path_allowed(normalized, session_id) and normalized.endswith(".json")


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


def _source_resolution_audit_file_binding(
    *,
    root: Path,
    relative_path: str,
    expected_hash: Any,
    session_id: str,
) -> dict[str, Any]:
    if not _source_path_allowed(relative_path, session_id):
        return {
            "source_resolution_audit_file_load_status": "SCOPE_MISMATCH",
            "source_resolution_audit_file_hash": None,
            "source_resolution_audit_file_recomputed_hash": None,
            "source_resolution_audit_file_hash_match": False,
        }
    source, source_error = _safe_load_json(_rooted(root, relative_path))
    if source is None:
        return {
            "source_resolution_audit_file_load_status": str(source_error or "UNKNOWN"),
            "source_resolution_audit_file_hash": None,
            "source_resolution_audit_file_recomputed_hash": None,
            "source_resolution_audit_file_hash_match": False,
        }
    file_hash = source.get("resolution_audit_hash")
    recomputed_hash = upbit_paper_post_rerun_operator_resolution_audit_hash(source)
    hash_match = bool(file_hash == expected_hash == recomputed_hash)
    return {
        "source_resolution_audit_file_load_status": "PASS" if hash_match else "HASH_MISMATCH",
        "source_resolution_audit_file_hash": file_hash,
        "source_resolution_audit_file_recomputed_hash": recomputed_hash,
        "source_resolution_audit_file_hash_match": hash_match,
    }


def _build_closure_item(*, source_item: dict[str, Any]) -> dict[str, Any]:
    blocking_codes = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
        POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    blocking_codes.update(str(code) for code in source_item.get("blocking_codes", []) if code)
    return {
        "priority_order": int(source_item.get("priority_order") or 0),
        "replacement_loop_id": str(source_item.get("replacement_loop_id") or "UNKNOWN"),
        "cycle_id": str(source_item.get("cycle_id") or "UNKNOWN"),
        "source_resolution_status": str(source_item.get("resolution_status") or "UNKNOWN"),
        "source_resolution_reason_code": str(source_item.get("resolution_reason_code") or "UNKNOWN"),
        "source_resolution_evidence_present": bool(source_item.get("resolution_evidence_present")),
        "source_resolution_evidence_accepted": bool(source_item.get("resolution_evidence_accepted")),
        "closure_status": POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_ITEM_STATUS,
        "closure_reason_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "candidate_rollup_artifact_path": str(source_item.get("candidate_rollup_artifact_path") or ""),
        "planned_current_ledger_jsonl_path": str(source_item.get("planned_current_ledger_jsonl_path") or ""),
        "path_scope_status": str(source_item.get("path_scope_status") or "UNKNOWN"),
        "required_closure_evidence": [
            "validated_operator_resolution_acceptance",
            "validated_current_ledger_rebuild",
            "validated_source_hash_reconciliation",
            "validated_no_live_or_scale_mutation",
        ],
        "blocking_codes": sorted(blocking_codes),
        "closure_notes": (
            "This item is explicitly closed as non-current evidence while operator resolution is unresolved. "
            "It cannot write current ledger, latest runtime pointer, LIVE_READY, live orders, or scale-up."
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


def build_upbit_paper_post_rerun_resolution_current_evidence_closure_report(
    *,
    root: Path,
    resolution_audit_report: dict[str, Any],
    source_resolution_audit_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_operator_resolution_audit_report.json",
    closure_guard_id: str = "upbit-paper-post-rerun-resolution-current-evidence-closure",
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_post_rerun_operator_resolution_audit_report(resolution_audit_report)
    session_id = str(resolution_audit_report.get("session_id") or "UNKNOWN")
    source_items = [item for item in resolution_audit_report.get("items", []) if isinstance(item, dict)]
    items = [_build_closure_item(source_item=item) for item in source_items] if source_result.status == "PASS" else []
    blockers = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
        POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if source_result.status != "PASS":
        blockers.add(source_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    for item in items:
        blockers.update(str(code) for code in item.get("blocking_codes", []) if code)

    source_hash = resolution_audit_report.get("resolution_audit_hash")
    source_file_binding = _source_resolution_audit_file_binding(
        root=root,
        relative_path=source_resolution_audit_path,
        expected_hash=source_hash,
        session_id=session_id,
    )
    if source_file_binding["source_resolution_audit_file_load_status"] != "PASS":
        blockers.add(POST_RERUN_RESOLUTION_CLOSURE_SOURCE_BINDING_REQUIRED)

    report = {
        "schema_id": UPBIT_PAPER_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "closure_guard_id": closure_guard_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_TRUTH_ROLE,
        "closure_role": POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_ROLE,
        "source_resolution_audit_path": source_resolution_audit_path,
        "source_resolution_audit_hash": source_hash,
        **source_file_binding,
        "source_resolution_audit_role": resolution_audit_report.get("resolution_audit_role"),
        "source_resolution_audit_status": resolution_audit_report.get("resolution_audit_status"),
        "source_resolution_audit_primary_blocker_code": resolution_audit_report.get("primary_blocker_code"),
        "source_resolution_audit_outcome": resolution_audit_report.get("resolution_outcome"),
        "source_unresolved_item_count": int(resolution_audit_report.get("unresolved_item_count") or 0),
        "source_resolved_item_count": int(resolution_audit_report.get("resolved_item_count") or 0),
        "source_resolution_control_count": int(resolution_audit_report.get("resolution_control_count") or 0),
        "source_resolution_controls_satisfied_count": int(resolution_audit_report.get("resolution_controls_satisfied_count") or 0),
        "source_current_evidence_write_authorized_count": int(resolution_audit_report.get("current_evidence_write_authorized_count") or 0),
        "source_current_evidence_write_allowed_count": int(resolution_audit_report.get("current_evidence_write_allowed_count") or 0),
        "source_candidate_current_evidence_usable_count": int(resolution_audit_report.get("candidate_current_evidence_usable_count") or 0),
        "closure_status": POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_STATUS,
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "closure_outcome": POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_OUTCOME,
        "closure_control_count": int(resolution_audit_report.get("resolution_control_count") or 0),
        "closure_controls_satisfied_count": 0,
        "closed_item_count": len(items),
        "unresolved_item_count": len(items),
        "resolved_item_count": 0,
        "current_evidence_write_authorized_count": 0,
        "current_evidence_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "current_evidence_closed_count": len(items),
        "blocker_codes": sorted(blockers),
        "closure_items": items,
        "closure_next_action": "Keep resolution audit outputs closed as non-current evidence until a separate validated reconciliation writer exists.",
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
        "closure_hash": "",
    }
    report["closure_hash"] = upbit_paper_post_rerun_resolution_current_evidence_closure_hash(report)
    return report


def write_upbit_paper_post_rerun_resolution_current_evidence_closure_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report(
    report: dict[str, Any],
) -> UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "closure_guard_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "closure_role",
        "source_resolution_audit_path",
        "source_resolution_audit_hash",
        "source_resolution_audit_file_load_status",
        "source_resolution_audit_file_hash",
        "source_resolution_audit_file_recomputed_hash",
        "source_resolution_audit_file_hash_match",
        "source_resolution_audit_role",
        "source_resolution_audit_status",
        "source_resolution_audit_primary_blocker_code",
        "source_resolution_audit_outcome",
        "source_unresolved_item_count",
        "source_resolved_item_count",
        "source_resolution_control_count",
        "source_resolution_controls_satisfied_count",
        "source_current_evidence_write_authorized_count",
        "source_current_evidence_write_allowed_count",
        "source_candidate_current_evidence_usable_count",
        "closure_status",
        "primary_blocker_code",
        "closure_outcome",
        "closure_control_count",
        "closure_controls_satisfied_count",
        "closed_item_count",
        "unresolved_item_count",
        "resolved_item_count",
        "current_evidence_write_authorized_count",
        "current_evidence_write_allowed_count",
        "candidate_current_evidence_usable_count",
        "current_evidence_closed_count",
        "blocker_codes",
        "closure_items",
        "closure_next_action",
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
        "closure_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("FAIL", f"post-rerun resolution current-evidence closure missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_SCHEMA_ID:
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("FAIL", "post-rerun resolution current-evidence closure schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("closure_hash") != upbit_paper_post_rerun_resolution_current_evidence_closure_hash(report):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("FAIL", "post-rerun resolution current-evidence closure hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "post-rerun resolution closure scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_TRUTH_ROLE or report.get("closure_role") != POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_ROLE:
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "post-rerun resolution closure cannot claim writer/current/live truth", "LIVE_FINAL_GUARD_FAILED")
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
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "post-rerun resolution closure created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if (
        report.get("source_resolution_audit_role") != POST_RERUN_OPERATOR_RESOLUTION_AUDIT_ROLE
        or report.get("source_resolution_audit_status") != POST_RERUN_OPERATOR_RESOLUTION_AUDIT_STATUS
        or report.get("source_resolution_audit_primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("source_resolution_audit_outcome") != POST_RERUN_OPERATOR_RESOLUTION_AUDIT_OUTCOME
    ):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "source resolution audit boundary mismatch", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if (
        report.get("source_resolved_item_count") != 0
        or report.get("source_resolution_controls_satisfied_count") != 0
        or report.get("source_current_evidence_write_authorized_count") != 0
        or report.get("source_current_evidence_write_allowed_count") != 0
        or report.get("source_candidate_current_evidence_usable_count") != 0
    ):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "source resolution audit exposed accepted resolution or current evidence", "LIVE_FINAL_GUARD_FAILED")
    session_id = str(report.get("session_id"))
    if not _source_path_allowed(str(report.get("source_resolution_audit_path") or ""), session_id):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "source resolution audit path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if (
        report.get("source_resolution_audit_file_load_status") != "PASS"
        or report.get("source_resolution_audit_file_hash_match") is not True
    ):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult(
            "BLOCKED",
            "source resolution audit file binding is missing or mismatched",
            POST_RERUN_RESOLUTION_CLOSURE_SOURCE_BINDING_REQUIRED,
        )
    if (
        report.get("source_resolution_audit_file_hash") != report.get("source_resolution_audit_hash")
        or report.get("source_resolution_audit_file_recomputed_hash") != report.get("source_resolution_audit_hash")
    ):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult(
            "FAIL",
            "source resolution audit file hash does not match source report hash",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if (
        report.get("closure_status") != POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_STATUS
        or report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("closure_outcome") != POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_OUTCOME
    ):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "post-rerun resolution closure must remain unresolved and blocked", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if (
        report.get("current_evidence_write_authorized_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
        or report.get("candidate_current_evidence_usable_count") != 0
        or report.get("resolved_item_count") != 0
        or report.get("closure_controls_satisfied_count") != 0
    ):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "post-rerun resolution closure exposed current evidence or resolved controls", "LIVE_FINAL_GUARD_FAILED")
    blocker_codes = set(report.get("blocker_codes") or [])
    for required_blocker in (
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
        POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED,
    ):
        if required_blocker not in blocker_codes:
            return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", f"post-rerun resolution closure missing blocker: {required_blocker}", required_blocker)

    items = report.get("closure_items")
    if not isinstance(items, list):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("FAIL", "post-rerun resolution closure items must be an array", "SCHEMA_IDENTITY_MISMATCH")
    if (
        report.get("closed_item_count") != len(items)
        or report.get("unresolved_item_count") != len(items)
        or report.get("current_evidence_closed_count") != len(items)
        or report.get("source_unresolved_item_count") != len(items)
    ):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("FAIL", "post-rerun resolution closure count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("closure_control_count") != report.get("source_resolution_control_count"):
        return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("FAIL", "post-rerun resolution closure control count mismatch", "SCHEMA_IDENTITY_MISMATCH")

    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("FAIL", "post-rerun resolution closure item must be object", "SCHEMA_IDENTITY_MISMATCH")
        if not _candidate_rollup_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "closure item candidate rollup path escaped post-rollup namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not _current_ledger_path_allowed(str(item.get("planned_current_ledger_jsonl_path") or ""), session_id):
            return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "closure item planned current ledger path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        item_forbidden = (
            "source_resolution_evidence_present",
            "source_resolution_evidence_accepted",
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
            return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "post-rerun resolution closure item attempted current evidence or live mutation", "LIVE_FINAL_GUARD_FAILED")
        if (
            item.get("source_resolution_status") != POST_RERUN_OPERATOR_RESOLUTION_ITEM_STATUS
            or item.get("source_resolution_reason_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
            or item.get("closure_status") != POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_ITEM_STATUS
            or item.get("closure_reason_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
            or item.get("path_scope_status") != "MATCH"
            or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(item.get("blocking_codes") or [])
        ):
            return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult("BLOCKED", "post-rerun resolution closure item lost unresolved write-blocked state", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    return UpbitPaperPostRerunResolutionCurrentEvidenceClosureValidationResult(
        "PASS",
        "Upbit PAPER post-rerun resolution current-evidence closure keeps unresolved audit outputs out of current evidence/live/scale",
        None,
    )
