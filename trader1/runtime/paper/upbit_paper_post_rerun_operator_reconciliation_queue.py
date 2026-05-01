from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_post_rerun_current_evidence_promotion_guard import (
    POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
    upbit_paper_post_rerun_current_evidence_promotion_guard_hash,
    validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE,
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_SCHEMA_ID = (
    "trader1.upbit_paper_post_rerun_operator_reconciliation_queue_report.v1"
)
POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_TRUTH_ROLE = (
    "PAPER_RUNTIME_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_REVIEW_ONLY_NOT_WRITER"
)
POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_ROLE = (
    "PAPER_POST_RERUN_RECONCILIATION_OPERATOR_QUEUE_NOT_CURRENT_EVIDENCE"
)
POST_RERUN_OPERATOR_RECONCILIATION_ACTION = "REVIEW_CANDIDATE_ROLLUP_KEEP_CURRENT_EVIDENCE_BLOCKED"


@dataclass(frozen=True)
class UpbitPaperPostRerunOperatorReconciliationQueueValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_post_rerun_operator_reconciliation_queue_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("queue_hash", None)
    return _sha256_json(payload)


def _candidate_rollup_hash(candidate: dict[str, Any]) -> str:
    payload = dict(candidate)
    payload.pop("candidate_rollup_hash", None)
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


def _staging_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return _artifact_path_allowed(normalized, session_id) and "/paper_runtime/rerun_candidates/" in normalized


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


def _source_promotion_guard_file_binding(
    *,
    root: Path,
    relative_path: str,
    expected_hash: Any,
    session_id: str,
) -> dict[str, Any]:
    if not _artifact_path_allowed(relative_path, session_id):
        return {
            "source_promotion_guard_file_load_status": "SCOPE_MISMATCH",
            "source_promotion_guard_file_hash": None,
            "source_promotion_guard_file_recomputed_hash": None,
            "source_promotion_guard_file_hash_match": False,
        }
    source, source_error = _safe_load_json(_rooted(root, relative_path))
    if source is None:
        return {
            "source_promotion_guard_file_load_status": str(source_error or "UNKNOWN"),
            "source_promotion_guard_file_hash": None,
            "source_promotion_guard_file_recomputed_hash": None,
            "source_promotion_guard_file_hash_match": False,
        }
    file_hash = source.get("promotion_guard_hash")
    recomputed_hash = upbit_paper_post_rerun_current_evidence_promotion_guard_hash(source)
    hash_match = bool(file_hash == expected_hash == recomputed_hash)
    return {
        "source_promotion_guard_file_load_status": "PASS" if hash_match else "HASH_MISMATCH",
        "source_promotion_guard_file_hash": file_hash,
        "source_promotion_guard_file_recomputed_hash": recomputed_hash,
        "source_promotion_guard_file_hash_match": hash_match,
    }


def _build_queue_item(*, priority_order: int, session_id: str, guard_item: dict[str, Any]) -> dict[str, Any]:
    candidate = guard_item.get("candidate_rollup") if isinstance(guard_item.get("candidate_rollup"), dict) else {}
    candidate_hash = candidate.get("candidate_rollup_hash") if isinstance(candidate, dict) else None
    candidate_recomputed_hash = _candidate_rollup_hash(candidate) if isinstance(candidate, dict) else None
    path_scope_status = (
        "MATCH"
        if _candidate_rollup_path_allowed(str(guard_item.get("candidate_rollup_artifact_path") or ""), session_id)
        and _staging_path_allowed(str(guard_item.get("staged_runtime_cycle_path") or ""), session_id)
        and _staging_path_allowed(str(guard_item.get("staged_ledger_jsonl_path") or ""), session_id)
        and _staging_path_allowed(str(guard_item.get("staged_writer_report_path") or ""), session_id)
        and _current_ledger_path_allowed(str(guard_item.get("planned_current_ledger_jsonl_path") or ""), session_id)
        else "MISMATCH"
    )
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(guard_item.get("replacement_loop_id") or "UNKNOWN"),
        "cycle_id": str(guard_item.get("cycle_id") or "UNKNOWN"),
        "operator_reconciliation_action": POST_RERUN_OPERATOR_RECONCILIATION_ACTION,
        "operator_reconciliation_status": "REVIEW_READY_RECONCILIATION_REQUIRED"
        if guard_item.get("promotion_review_ready") and path_scope_status == "MATCH"
        else "BLOCKED_PRE_REVIEW",
        "requires_operator_reconciliation": True,
        "source_guard_promotion_review_status": str(guard_item.get("promotion_review_status") or "UNKNOWN"),
        "source_guard_item_blocker_code": guard_item.get("item_blocker_code"),
        "source_candidate_classification": str(guard_item.get("source_candidate_classification") or "UNKNOWN"),
        "candidate_rollup_artifact_path": str(guard_item.get("candidate_rollup_artifact_path") or ""),
        "candidate_rollup_role": candidate.get("candidate_rollup_role") if isinstance(candidate, dict) else None,
        "candidate_rollup_hash": candidate_hash,
        "candidate_rollup_recomputed_hash": candidate_recomputed_hash,
        "candidate_rollup_hash_self_check": "PASS" if candidate_hash == candidate_recomputed_hash else "FAIL",
        "candidate_rollup_status": candidate.get("candidate_rollup_status") if isinstance(candidate, dict) else None,
        "candidate_rollup_verified": bool(guard_item.get("candidate_rollup_verified")),
        "candidate_ledger_jsonl_count": guard_item.get("candidate_ledger_jsonl_count"),
        "candidate_ledger_event_count": guard_item.get("candidate_ledger_event_count"),
        "candidate_filled_order_count": guard_item.get("candidate_filled_order_count"),
        "candidate_empty_no_trade_ledger": bool(guard_item.get("candidate_empty_no_trade_ledger")),
        "staged_runtime_cycle_path": str(guard_item.get("staged_runtime_cycle_path") or ""),
        "staged_ledger_jsonl_path": str(guard_item.get("staged_ledger_jsonl_path") or ""),
        "staged_writer_report_path": str(guard_item.get("staged_writer_report_path") or ""),
        "planned_current_ledger_jsonl_path": str(guard_item.get("planned_current_ledger_jsonl_path") or ""),
        "path_scope_status": path_scope_status,
        "candidate_rollup": candidate,
        "blocking_codes": sorted(
            {
                POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
                POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
                str(guard_item.get("item_blocker_code") or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE),
            }
        ),
        "operator_notes": (
            "Review the candidate rollup against staged runtime cycle, staged ledger JSONL, and writer report hashes. "
            "This queue is not a writer and must not create current evidence."
        ),
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


def build_upbit_paper_post_rerun_operator_reconciliation_queue_report(
    *,
    root: Path,
    promotion_guard_report: dict[str, Any],
    source_promotion_guard_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_current_evidence_promotion_guard_report.json",
    queue_id: str = "upbit-paper-post-rerun-operator-reconciliation-queue",
) -> dict[str, Any]:
    root = Path(root).resolve()
    guard_result = validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report(promotion_guard_report)
    session_id = str(promotion_guard_report.get("session_id") or "UNKNOWN")
    guard_items = [
        item
        for item in promotion_guard_report.get("items", [])
        if isinstance(item, dict) and item.get("promotion_review_ready")
    ]
    items = [
        _build_queue_item(priority_order=index, session_id=session_id, guard_item=item)
        for index, item in enumerate(guard_items, start=1)
    ] if guard_result.status == "PASS" else []
    blockers = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if guard_result.status != "PASS":
        blockers.add(guard_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    for item in items:
        blockers.update(str(code) for code in item.get("blocking_codes", []))
    source_hash = promotion_guard_report.get("promotion_guard_hash")
    source_file_binding = _source_promotion_guard_file_binding(
        root=root,
        relative_path=source_promotion_guard_path,
        expected_hash=source_hash,
        session_id=session_id,
    )
    if source_file_binding["source_promotion_guard_file_load_status"] != "PASS":
        blockers.add("POST_RERUN_OPERATOR_SOURCE_PROMOTION_GUARD_BINDING_REQUIRED")
    report = {
        "schema_id": UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "queue_id": queue_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_TRUTH_ROLE,
        "queue_role": POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_ROLE,
        "source_promotion_guard_path": source_promotion_guard_path,
        "source_promotion_guard_hash": source_hash,
        **source_file_binding,
        "source_promotion_guard_status": promotion_guard_report.get("promotion_guard_status"),
        "source_promotion_guard_primary_blocker_code": promotion_guard_report.get("primary_blocker_code"),
        "source_promotion_review_ready_count": int(promotion_guard_report.get("promotion_review_ready_count") or 0),
        "queue_item_count": len(items),
        "operator_reconciliation_required_count": sum(1 for item in items if item.get("requires_operator_reconciliation")),
        "review_ready_reconciliation_item_count": sum(
            1 for item in items if item.get("operator_reconciliation_status") == "REVIEW_READY_RECONCILIATION_REQUIRED"
        ),
        "blocked_pre_review_item_count": sum(1 for item in items if item.get("operator_reconciliation_status") == "BLOCKED_PRE_REVIEW"),
        "current_evidence_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "queue_status": "BLOCKED",
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "blocker_codes": sorted(blockers),
        "items": items,
        "operator_next_action": "Review candidate rollups only; do not write current evidence, latest pointers, live readiness, or scale-up artifacts from this queue.",
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
        "queue_hash": "",
    }
    report["queue_hash"] = upbit_paper_post_rerun_operator_reconciliation_queue_hash(report)
    return report


def write_upbit_paper_post_rerun_operator_reconciliation_queue_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_post_rerun_operator_reconciliation_queue_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_rerun_operator_reconciliation_queue_report(
    report: dict[str, Any],
) -> UpbitPaperPostRerunOperatorReconciliationQueueValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "queue_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "queue_role",
        "source_promotion_guard_path",
        "source_promotion_guard_hash",
        "source_promotion_guard_file_load_status",
        "source_promotion_guard_file_hash",
        "source_promotion_guard_file_recomputed_hash",
        "source_promotion_guard_file_hash_match",
        "source_promotion_guard_status",
        "source_promotion_guard_primary_blocker_code",
        "source_promotion_review_ready_count",
        "queue_item_count",
        "operator_reconciliation_required_count",
        "review_ready_reconciliation_item_count",
        "blocked_pre_review_item_count",
        "current_evidence_write_allowed_count",
        "candidate_current_evidence_usable_count",
        "queue_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
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
        "queue_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("FAIL", f"post-rerun operator queue missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_SCHEMA_ID:
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("FAIL", "post-rerun operator queue schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("queue_hash") != upbit_paper_post_rerun_operator_reconciliation_queue_hash(report):
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("FAIL", "post-rerun operator queue hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "post-rerun operator queue scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_TRUTH_ROLE or report.get("queue_role") != POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_ROLE:
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "post-rerun operator queue cannot claim writer or live truth", "LIVE_FINAL_GUARD_FAILED")
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
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "post-rerun operator queue created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if report.get("source_promotion_guard_status") != "BLOCKED" or report.get("source_promotion_guard_primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE:
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "source promotion guard boundary mismatch", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if report.get("queue_status") != "BLOCKED" or report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE:
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "post-rerun operator queue must remain blocked", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if report.get("current_evidence_write_allowed_count") != 0 or report.get("candidate_current_evidence_usable_count") != 0:
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "post-rerun operator queue exposed current evidence write/use", "LIVE_FINAL_GUARD_FAILED")
    session_id = str(report.get("session_id"))
    if not _artifact_path_allowed(str(report.get("source_promotion_guard_path") or ""), session_id):
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "source promotion guard path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if (
        report.get("source_promotion_guard_file_load_status") != "PASS"
        or report.get("source_promotion_guard_file_hash_match") is not True
    ):
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult(
            "BLOCKED",
            "source promotion guard file binding is missing or mismatched",
            POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        )
    if (
        report.get("source_promotion_guard_file_hash") != report.get("source_promotion_guard_hash")
        or report.get("source_promotion_guard_file_recomputed_hash") != report.get("source_promotion_guard_hash")
    ):
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult(
            "FAIL",
            "source promotion guard file hash does not match source report hash",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("queue_item_count") != len(items):
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("FAIL", "post-rerun operator queue item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected = {
        "operator_reconciliation_required_count": sum(1 for item in items if isinstance(item, dict) and item.get("requires_operator_reconciliation")),
        "review_ready_reconciliation_item_count": sum(
            1 for item in items if isinstance(item, dict) and item.get("operator_reconciliation_status") == "REVIEW_READY_RECONCILIATION_REQUIRED"
        ),
        "blocked_pre_review_item_count": sum(1 for item in items if isinstance(item, dict) and item.get("operator_reconciliation_status") == "BLOCKED_PRE_REVIEW"),
    }
    for field, value in expected.items():
        if report.get(field) != value:
            return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("FAIL", f"post-rerun operator queue count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_promotion_review_ready_count") != len(items):
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("FAIL", "post-rerun operator queue source review count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(report.get("blocker_codes") or []):
        return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "post-rerun operator queue missing reconciliation blocker", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("FAIL", "post-rerun operator queue item must be object", "SCHEMA_IDENTITY_MISMATCH")
        if not _candidate_rollup_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "operator queue candidate rollup path escaped post-rollup namespace", "SNAPSHOT_SCOPE_MISMATCH")
        for path_field in ("staged_runtime_cycle_path", "staged_ledger_jsonl_path", "staged_writer_report_path"):
            if not _staging_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", f"operator queue {path_field} escaped staging namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not _current_ledger_path_allowed(str(item.get("planned_current_ledger_jsonl_path") or ""), session_id):
            return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "operator queue planned current ledger path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        item_forbidden = (
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
            return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "post-rerun operator queue item attempted current evidence or live mutation", "LIVE_FINAL_GUARD_FAILED")
        if (
            item.get("operator_reconciliation_action") != POST_RERUN_OPERATOR_RECONCILIATION_ACTION
            or item.get("operator_reconciliation_status") != "REVIEW_READY_RECONCILIATION_REQUIRED"
            or item.get("source_guard_item_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
            or not item.get("requires_operator_reconciliation")
            or item.get("path_scope_status") != "MATCH"
            or not item.get("candidate_rollup_verified")
        ):
            return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("FAIL", "post-rerun operator queue item lost review-only reconciliation state", "SCHEMA_IDENTITY_MISMATCH")
        candidate = item.get("candidate_rollup")
        if not isinstance(candidate, dict):
            return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("FAIL", "post-rerun operator queue candidate rollup missing", "SCHEMA_IDENTITY_MISMATCH")
        if (
            item.get("candidate_rollup_role") != POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE
            or candidate.get("candidate_rollup_role") != POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE
            or item.get("candidate_rollup_hash") != candidate.get("candidate_rollup_hash")
            or item.get("candidate_rollup_recomputed_hash") != _candidate_rollup_hash(candidate)
            or item.get("candidate_rollup_hash_self_check") != "PASS"
            or item.get("candidate_rollup_status") != "PASS"
        ):
            return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("FAIL", "post-rerun operator queue candidate hash/status mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if (
            candidate.get("candidate_current_evidence_usable")
            or candidate.get("current_evidence_mutation_allowed")
            or candidate.get("live_order_allowed")
            or candidate.get("scale_up_allowed")
        ):
            return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult("BLOCKED", "post-rerun operator queue candidate attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED")
    return UpbitPaperPostRerunOperatorReconciliationQueueValidationResult(
        "PASS",
        "Upbit PAPER post-rerun operator reconciliation queue is review-only and keeps current evidence writes blocked",
        None,
    )
