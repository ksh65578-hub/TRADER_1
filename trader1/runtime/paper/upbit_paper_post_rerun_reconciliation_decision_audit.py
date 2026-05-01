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
    POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE,
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_reconciliation_queue import (
    POST_RERUN_OPERATOR_RECONCILIATION_ACTION,
    POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_ROLE,
    validate_upbit_paper_post_rerun_operator_reconciliation_queue_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_POST_RERUN_RECONCILIATION_DECISION_AUDIT_SCHEMA_ID = (
    "trader1.upbit_paper_post_rerun_reconciliation_decision_audit_report.v1"
)
POST_RERUN_RECONCILIATION_DECISION_AUDIT_TRUTH_ROLE = (
    "PAPER_RUNTIME_POST_RERUN_RECONCILIATION_DECISION_AUDIT_REVIEW_ONLY_NOT_WRITER"
)
POST_RERUN_RECONCILIATION_DECISION_AUDIT_ROLE = (
    "PAPER_POST_RERUN_RECONCILIATION_DECISION_AUDIT_NOT_CURRENT_EVIDENCE"
)
POST_RERUN_RECONCILIATION_WRITE_DENIED_STATUS = "WRITE_DENIED_RECONCILIATION_REQUIRED"
POST_RERUN_RECONCILIATION_WRITE_DENIED_OUTCOME = "CURRENT_EVIDENCE_WRITE_DENIED_RECONCILIATION_REQUIRED"


@dataclass(frozen=True)
class UpbitPaperPostRerunReconciliationDecisionAuditValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_post_rerun_reconciliation_decision_audit_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("decision_audit_hash", None)
    return _sha256_json(payload)


def _candidate_rollup_hash(candidate: dict[str, Any]) -> str:
    payload = dict(candidate)
    payload.pop("candidate_rollup_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


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


def _build_decision_item(*, priority_order: int, session_id: str, queue_item: dict[str, Any]) -> dict[str, Any]:
    candidate = queue_item.get("candidate_rollup") if isinstance(queue_item.get("candidate_rollup"), dict) else {}
    candidate_hash = candidate.get("candidate_rollup_hash") if isinstance(candidate, dict) else None
    candidate_recomputed_hash = _candidate_rollup_hash(candidate) if isinstance(candidate, dict) else None
    path_scope_status = (
        "MATCH"
        if _candidate_rollup_path_allowed(str(queue_item.get("candidate_rollup_artifact_path") or ""), session_id)
        and _current_ledger_path_allowed(str(queue_item.get("planned_current_ledger_jsonl_path") or ""), session_id)
        and queue_item.get("path_scope_status") == "MATCH"
        else "MISMATCH"
    )
    blocking_codes = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    blocking_codes.update(str(code) for code in queue_item.get("blocking_codes", []) if code)
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(queue_item.get("replacement_loop_id") or "UNKNOWN"),
        "cycle_id": str(queue_item.get("cycle_id") or "UNKNOWN"),
        "source_operator_reconciliation_status": str(queue_item.get("operator_reconciliation_status") or "UNKNOWN"),
        "source_operator_reconciliation_action": str(queue_item.get("operator_reconciliation_action") or "UNKNOWN"),
        "source_operator_reconciliation_required": bool(queue_item.get("requires_operator_reconciliation")),
        "source_queue_role": POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_ROLE,
        "decision_status": POST_RERUN_RECONCILIATION_WRITE_DENIED_STATUS,
        "decision_reason_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "decision_outcome": POST_RERUN_RECONCILIATION_WRITE_DENIED_OUTCOME,
        "candidate_rollup_artifact_path": str(queue_item.get("candidate_rollup_artifact_path") or ""),
        "planned_current_ledger_jsonl_path": str(queue_item.get("planned_current_ledger_jsonl_path") or ""),
        "candidate_rollup_role": queue_item.get("candidate_rollup_role"),
        "candidate_rollup_hash": candidate_hash,
        "candidate_rollup_recomputed_hash": candidate_recomputed_hash,
        "candidate_rollup_hash_self_check": "PASS" if candidate_hash == candidate_recomputed_hash else "FAIL",
        "candidate_rollup_status": queue_item.get("candidate_rollup_status"),
        "candidate_rollup_verified": bool(queue_item.get("candidate_rollup_verified")),
        "candidate_ledger_event_count": queue_item.get("candidate_ledger_event_count"),
        "candidate_filled_order_count": queue_item.get("candidate_filled_order_count"),
        "path_scope_status": path_scope_status,
        "candidate_rollup": candidate,
        "blocking_codes": sorted(blocking_codes),
        "decision_notes": (
            "Current evidence write is denied because post-rerun reconciliation remains required. "
            "This audit is review-only and must not create current ledger JSONL, latest pointers, live readiness, or scale-up artifacts."
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


def build_upbit_paper_post_rerun_reconciliation_decision_audit_report(
    *,
    operator_queue_report: dict[str, Any],
    source_operator_queue_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
    audit_id: str = "upbit-paper-post-rerun-reconciliation-decision-audit",
) -> dict[str, Any]:
    queue_result = validate_upbit_paper_post_rerun_operator_reconciliation_queue_report(operator_queue_report)
    session_id = str(operator_queue_report.get("session_id") or "UNKNOWN")
    queue_items = [item for item in operator_queue_report.get("items", []) if isinstance(item, dict)]
    items = [
        _build_decision_item(priority_order=index, session_id=session_id, queue_item=item)
        for index, item in enumerate(queue_items, start=1)
    ] if queue_result.status == "PASS" else []
    blockers = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if queue_result.status != "PASS":
        blockers.add(queue_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    for item in items:
        blockers.update(str(code) for code in item.get("blocking_codes", []))
    report = {
        "schema_id": UPBIT_PAPER_POST_RERUN_RECONCILIATION_DECISION_AUDIT_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "audit_id": audit_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_RERUN_RECONCILIATION_DECISION_AUDIT_TRUTH_ROLE,
        "decision_audit_role": POST_RERUN_RECONCILIATION_DECISION_AUDIT_ROLE,
        "source_operator_queue_path": source_operator_queue_path,
        "source_operator_queue_hash": operator_queue_report.get("queue_hash"),
        "source_operator_queue_status": operator_queue_report.get("queue_status"),
        "source_operator_queue_primary_blocker_code": operator_queue_report.get("primary_blocker_code"),
        "source_queue_item_count": int(operator_queue_report.get("queue_item_count") or 0),
        "decision_item_count": len(items),
        "write_denied_count": sum(1 for item in items if item.get("decision_status") == POST_RERUN_RECONCILIATION_WRITE_DENIED_STATUS),
        "operator_reconciliation_required_count": sum(1 for item in items if item.get("source_operator_reconciliation_required")),
        "current_evidence_write_authorized_count": 0,
        "current_evidence_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "decision_audit_status": "BLOCKED",
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "decision_outcome": POST_RERUN_RECONCILIATION_WRITE_DENIED_OUTCOME,
        "blocker_codes": sorted(blockers),
        "items": items,
        "decision_audit_next_action": "Keep current evidence writes denied until operator reconciliation has a separate validated writer review; do not mutate live readiness or scale-up state from this audit.",
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
        "decision_audit_hash": "",
    }
    report["decision_audit_hash"] = upbit_paper_post_rerun_reconciliation_decision_audit_hash(report)
    return report


def write_upbit_paper_post_rerun_reconciliation_decision_audit_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_post_rerun_reconciliation_decision_audit_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_rerun_reconciliation_decision_audit_report(
    report: dict[str, Any],
) -> UpbitPaperPostRerunReconciliationDecisionAuditValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "audit_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "decision_audit_role",
        "source_operator_queue_path",
        "source_operator_queue_hash",
        "source_operator_queue_status",
        "source_operator_queue_primary_blocker_code",
        "source_queue_item_count",
        "decision_item_count",
        "write_denied_count",
        "operator_reconciliation_required_count",
        "current_evidence_write_authorized_count",
        "current_evidence_write_allowed_count",
        "candidate_current_evidence_usable_count",
        "decision_audit_status",
        "primary_blocker_code",
        "decision_outcome",
        "blocker_codes",
        "items",
        "decision_audit_next_action",
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
        "decision_audit_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("FAIL", f"post-rerun reconciliation decision audit missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_POST_RERUN_RECONCILIATION_DECISION_AUDIT_SCHEMA_ID:
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("FAIL", "post-rerun reconciliation decision audit schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("decision_audit_hash") != upbit_paper_post_rerun_reconciliation_decision_audit_hash(report):
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("FAIL", "post-rerun reconciliation decision audit hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "post-rerun reconciliation decision audit scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != POST_RERUN_RECONCILIATION_DECISION_AUDIT_TRUTH_ROLE or report.get("decision_audit_role") != POST_RERUN_RECONCILIATION_DECISION_AUDIT_ROLE:
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "post-rerun reconciliation decision audit cannot claim writer or live truth", "LIVE_FINAL_GUARD_FAILED")
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
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "post-rerun reconciliation decision audit created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if (
        report.get("current_evidence_write_authorized_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
        or report.get("candidate_current_evidence_usable_count") != 0
    ):
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "post-rerun reconciliation decision audit exposed current evidence write/use", "LIVE_FINAL_GUARD_FAILED")
    if report.get("source_operator_queue_status") != "BLOCKED" or report.get("source_operator_queue_primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE:
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "source operator queue boundary mismatch", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if (
        report.get("decision_audit_status") != "BLOCKED"
        or report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("decision_outcome") != POST_RERUN_RECONCILIATION_WRITE_DENIED_OUTCOME
    ):
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "post-rerun reconciliation decision audit must remain write-denied", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    session_id = str(report.get("session_id"))
    if not _artifact_path_allowed(str(report.get("source_operator_queue_path") or ""), session_id):
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "source operator queue path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(report.get("blocker_codes") or []):
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "post-rerun reconciliation decision audit missing reconciliation blocker", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    items = report.get("items")
    if not isinstance(items, list) or report.get("decision_item_count") != len(items) or report.get("source_queue_item_count") != len(items):
        return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("FAIL", "post-rerun reconciliation decision audit item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected = {
        "write_denied_count": sum(1 for item in items if isinstance(item, dict) and item.get("decision_status") == POST_RERUN_RECONCILIATION_WRITE_DENIED_STATUS),
        "operator_reconciliation_required_count": sum(1 for item in items if isinstance(item, dict) and item.get("source_operator_reconciliation_required")),
    }
    for field, value in expected.items():
        if report.get(field) != value:
            return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("FAIL", f"post-rerun reconciliation decision audit count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH")
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("FAIL", "post-rerun reconciliation decision audit item must be object", "SCHEMA_IDENTITY_MISMATCH")
        if not _candidate_rollup_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "decision audit candidate rollup path escaped post-rollup namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not _current_ledger_path_allowed(str(item.get("planned_current_ledger_jsonl_path") or ""), session_id):
            return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "decision audit planned current ledger path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
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
            return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "post-rerun reconciliation decision audit item attempted current evidence or live mutation", "LIVE_FINAL_GUARD_FAILED")
        if (
            item.get("source_operator_reconciliation_status") != "REVIEW_READY_RECONCILIATION_REQUIRED"
            or item.get("source_operator_reconciliation_action") != POST_RERUN_OPERATOR_RECONCILIATION_ACTION
            or item.get("source_operator_reconciliation_required") is not True
            or item.get("source_queue_role") != POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_ROLE
            or item.get("decision_status") != POST_RERUN_RECONCILIATION_WRITE_DENIED_STATUS
            or item.get("decision_reason_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
            or item.get("decision_outcome") != POST_RERUN_RECONCILIATION_WRITE_DENIED_OUTCOME
            or item.get("path_scope_status") != "MATCH"
            or not item.get("candidate_rollup_verified")
        ):
            return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("FAIL", "post-rerun reconciliation decision audit item lost write-denied reconciliation state", "SCHEMA_IDENTITY_MISMATCH")
        candidate = item.get("candidate_rollup")
        if not isinstance(candidate, dict):
            return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("FAIL", "post-rerun reconciliation decision audit candidate rollup missing", "SCHEMA_IDENTITY_MISMATCH")
        if (
            item.get("candidate_rollup_role") != POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE
            or candidate.get("candidate_rollup_role") != POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE
            or item.get("candidate_rollup_hash") != candidate.get("candidate_rollup_hash")
            or item.get("candidate_rollup_recomputed_hash") != _candidate_rollup_hash(candidate)
            or item.get("candidate_rollup_hash_self_check") != "PASS"
            or item.get("candidate_rollup_status") != "PASS"
        ):
            return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("FAIL", "post-rerun reconciliation decision audit candidate hash/status mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if (
            candidate.get("candidate_current_evidence_usable")
            or candidate.get("current_evidence_mutation_allowed")
            or candidate.get("live_order_allowed")
            or candidate.get("scale_up_allowed")
        ):
            return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult("BLOCKED", "post-rerun reconciliation decision audit candidate attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED")
    return UpbitPaperPostRerunReconciliationDecisionAuditValidationResult(
        "PASS",
        "Upbit PAPER post-rerun reconciliation decision audit denies current evidence writes while reconciliation remains required",
        None,
    )
