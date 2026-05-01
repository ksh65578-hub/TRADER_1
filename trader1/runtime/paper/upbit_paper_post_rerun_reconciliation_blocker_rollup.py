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
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_decision_audit import (
    POST_RERUN_RECONCILIATION_WRITE_DENIED_OUTCOME,
    POST_RERUN_RECONCILIATION_WRITE_DENIED_STATUS,
    upbit_paper_post_rerun_reconciliation_decision_audit_hash,
    validate_upbit_paper_post_rerun_reconciliation_decision_audit_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_SCHEMA_ID = (
    "trader1.upbit_paper_post_rerun_reconciliation_blocker_rollup_report.v1"
)
POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_TRUTH_ROLE = (
    "PAPER_RUNTIME_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_REVIEW_ONLY_NOT_WRITER"
)
POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_ROLE = (
    "PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_NOT_CURRENT_EVIDENCE"
)
POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_OUTCOME = (
    "POST_RERUN_RECONCILIATION_BLOCKERS_ROLLED_UP_CURRENT_EVIDENCE_BLOCKED"
)
POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_ITEM_STATUS = "BLOCKED_CURRENT_EVIDENCE_WRITE_DENIED"
POST_RERUN_BLOCKER_ROLLUP_SOURCE_DECISION_AUDIT_BINDING_REQUIRED = (
    "POST_RERUN_BLOCKER_ROLLUP_SOURCE_DECISION_AUDIT_BINDING_REQUIRED"
)


@dataclass(frozen=True)
class UpbitPaperPostRerunReconciliationBlockerRollupValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_post_rerun_reconciliation_blocker_rollup_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("blocker_rollup_hash", None)
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


def _source_decision_audit_file_binding(
    *,
    root: Path,
    relative_path: str,
    expected_hash: Any,
    session_id: str,
) -> dict[str, Any]:
    if not _artifact_path_allowed(relative_path, session_id):
        return {
            "source_decision_audit_file_load_status": "SCOPE_MISMATCH",
            "source_decision_audit_file_hash": None,
            "source_decision_audit_file_recomputed_hash": None,
            "source_decision_audit_file_hash_match": False,
        }
    source, source_error = _safe_load_json(_rooted(root, relative_path))
    if source is None:
        return {
            "source_decision_audit_file_load_status": str(source_error or "UNKNOWN"),
            "source_decision_audit_file_hash": None,
            "source_decision_audit_file_recomputed_hash": None,
            "source_decision_audit_file_hash_match": False,
        }
    file_hash = source.get("decision_audit_hash")
    recomputed_hash = upbit_paper_post_rerun_reconciliation_decision_audit_hash(source)
    hash_match = bool(file_hash == expected_hash == recomputed_hash)
    return {
        "source_decision_audit_file_load_status": "PASS" if hash_match else "HASH_MISMATCH",
        "source_decision_audit_file_hash": file_hash,
        "source_decision_audit_file_recomputed_hash": recomputed_hash,
        "source_decision_audit_file_hash_match": hash_match,
    }


def _build_rollup_item(*, priority_order: int, session_id: str, decision_item: dict[str, Any]) -> dict[str, Any]:
    blocking_codes = sorted({str(code) for code in decision_item.get("blocking_codes", []) if code})
    if POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in blocking_codes:
        blocking_codes = sorted({*blocking_codes, POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE})
    path_scope_status = (
        "MATCH"
        if _candidate_rollup_path_allowed(str(decision_item.get("candidate_rollup_artifact_path") or ""), session_id)
        and _current_ledger_path_allowed(str(decision_item.get("planned_current_ledger_jsonl_path") or ""), session_id)
        and decision_item.get("path_scope_status") == "MATCH"
        else "MISMATCH"
    )
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(decision_item.get("replacement_loop_id") or "UNKNOWN"),
        "cycle_id": str(decision_item.get("cycle_id") or "UNKNOWN"),
        "source_decision_status": str(decision_item.get("decision_status") or "UNKNOWN"),
        "source_decision_reason_code": str(decision_item.get("decision_reason_code") or "UNKNOWN"),
        "source_decision_outcome": str(decision_item.get("decision_outcome") or "UNKNOWN"),
        "candidate_rollup_artifact_path": str(decision_item.get("candidate_rollup_artifact_path") or ""),
        "planned_current_ledger_jsonl_path": str(decision_item.get("planned_current_ledger_jsonl_path") or ""),
        "primary_item_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "blocking_codes": blocking_codes,
        "item_blocker_count": len(blocking_codes),
        "operator_resolution_required": True,
        "item_rollup_status": POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_ITEM_STATUS,
        "path_scope_status": path_scope_status,
        "rollup_notes": (
            "This item remains blocked from current evidence because post-rerun reconciliation is unresolved. "
            "The rollup is informational and must not write current evidence, latest pointers, live readiness, or scale-up artifacts."
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


def _blocker_counts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        for code in item.get("blocking_codes", []):
            counts[str(code)] = counts.get(str(code), 0) + 1
    return [
        {
            "blocker_code": code,
            "blocked_item_count": counts[code],
            "blocks_current_evidence": True,
            "blocks_live_order": True,
            "blocks_scale_up": True,
            "operator_resolution_required": True,
            "resolution_scope": "REVIEW_ONLY_POST_RERUN_RECONCILIATION_REQUIRED",
        }
        for code in sorted(counts)
    ]


def build_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(
    *,
    root: Path,
    decision_audit_report: dict[str, Any],
    source_decision_audit_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_reconciliation_decision_audit_report.json",
    rollup_id: str = "upbit-paper-post-rerun-reconciliation-blocker-rollup",
) -> dict[str, Any]:
    root = Path(root).resolve()
    decision_result = validate_upbit_paper_post_rerun_reconciliation_decision_audit_report(decision_audit_report)
    session_id = str(decision_audit_report.get("session_id") or "UNKNOWN")
    decision_items = [item for item in decision_audit_report.get("items", []) if isinstance(item, dict)]
    items = [
        _build_rollup_item(priority_order=index, session_id=session_id, decision_item=item)
        for index, item in enumerate(decision_items, start=1)
    ] if decision_result.status == "PASS" else []
    blocker_counts = _blocker_counts(items)
    blockers = {item["blocker_code"] for item in blocker_counts}
    blockers.update(
        {
            POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
            POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
            "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
            "LIVE_READY_MISSING",
            "SCALE_UP_NOT_ELIGIBLE",
        }
    )
    if decision_result.status != "PASS":
        blockers.add(decision_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    source_hash = decision_audit_report.get("decision_audit_hash")
    source_file_binding = _source_decision_audit_file_binding(
        root=root,
        relative_path=source_decision_audit_path,
        expected_hash=source_hash,
        session_id=session_id,
    )
    if source_file_binding["source_decision_audit_file_load_status"] != "PASS":
        blockers.add(POST_RERUN_BLOCKER_ROLLUP_SOURCE_DECISION_AUDIT_BINDING_REQUIRED)
    report = {
        "schema_id": UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "rollup_id": rollup_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_TRUTH_ROLE,
        "blocker_rollup_role": POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_ROLE,
        "source_decision_audit_path": source_decision_audit_path,
        "source_decision_audit_hash": source_hash,
        **source_file_binding,
        "source_decision_audit_status": decision_audit_report.get("decision_audit_status"),
        "source_decision_audit_primary_blocker_code": decision_audit_report.get("primary_blocker_code"),
        "source_decision_item_count": int(decision_audit_report.get("decision_item_count") or 0),
        "source_write_denied_count": int(decision_audit_report.get("write_denied_count") or 0),
        "source_operator_reconciliation_required_count": int(decision_audit_report.get("operator_reconciliation_required_count") or 0),
        "rollup_item_count": len(items),
        "primary_blocker_item_count": sum(1 for item in items if item.get("primary_item_blocker_code") == POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE),
        "unique_blocker_count": len(blocker_counts),
        "unresolved_blocker_count": len(blocker_counts),
        "current_evidence_write_authorized_count": 0,
        "current_evidence_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "blocker_rollup_status": "BLOCKED",
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "rollup_outcome": POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_OUTCOME,
        "blocker_codes": sorted(blockers),
        "blocker_counts": blocker_counts,
        "items": items,
        "rollup_next_action": "Use this rollup only for operator visibility and blocker tracking; do not write current evidence, live readiness, or scale-up artifacts from it.",
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
        "blocker_rollup_hash": "",
    }
    report["blocker_rollup_hash"] = upbit_paper_post_rerun_reconciliation_blocker_rollup_hash(report)
    return report


def write_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(
    report: dict[str, Any],
) -> UpbitPaperPostRerunReconciliationBlockerRollupValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "rollup_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "blocker_rollup_role",
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
        "source_operator_reconciliation_required_count",
        "rollup_item_count",
        "primary_blocker_item_count",
        "unique_blocker_count",
        "unresolved_blocker_count",
        "current_evidence_write_authorized_count",
        "current_evidence_write_allowed_count",
        "candidate_current_evidence_usable_count",
        "blocker_rollup_status",
        "primary_blocker_code",
        "rollup_outcome",
        "blocker_codes",
        "blocker_counts",
        "items",
        "rollup_next_action",
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
        "blocker_rollup_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", f"post-rerun blocker rollup missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_SCHEMA_ID:
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker rollup schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("blocker_rollup_hash") != upbit_paper_post_rerun_reconciliation_blocker_rollup_hash(report):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker rollup hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "post-rerun blocker rollup scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_TRUTH_ROLE or report.get("blocker_rollup_role") != POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_ROLE:
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "post-rerun blocker rollup cannot claim writer or live truth", "LIVE_FINAL_GUARD_FAILED")
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
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "post-rerun blocker rollup created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if (
        report.get("current_evidence_write_authorized_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
        or report.get("candidate_current_evidence_usable_count") != 0
    ):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "post-rerun blocker rollup exposed current evidence write/use", "LIVE_FINAL_GUARD_FAILED")
    if report.get("source_decision_audit_status") != "BLOCKED" or report.get("source_decision_audit_primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE:
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "source decision audit boundary mismatch", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if (
        report.get("blocker_rollup_status") != "BLOCKED"
        or report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("rollup_outcome") != POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_OUTCOME
    ):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "post-rerun blocker rollup must remain blocked", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    session_id = str(report.get("session_id"))
    if not _artifact_path_allowed(str(report.get("source_decision_audit_path") or ""), session_id):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "source decision audit path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if (
        report.get("source_decision_audit_file_load_status") != "PASS"
        or report.get("source_decision_audit_file_hash_match") is not True
    ):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult(
            "BLOCKED",
            "source decision audit file binding is missing or mismatched",
            POST_RERUN_BLOCKER_ROLLUP_SOURCE_DECISION_AUDIT_BINDING_REQUIRED,
        )
    if (
        report.get("source_decision_audit_file_hash") != report.get("source_decision_audit_hash")
        or report.get("source_decision_audit_file_recomputed_hash") != report.get("source_decision_audit_hash")
    ):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult(
            "FAIL",
            "source decision audit file hash does not match source report hash",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(report.get("blocker_codes") or []):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "post-rerun blocker rollup missing reconciliation blocker", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    items = report.get("items")
    if not isinstance(items, list) or report.get("rollup_item_count") != len(items) or report.get("source_decision_item_count") != len(items):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker rollup item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_write_denied_count") != len(items) or report.get("source_operator_reconciliation_required_count") != len(items):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker rollup source count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_primary = sum(1 for item in items if isinstance(item, dict) and item.get("primary_item_blocker_code") == POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if report.get("primary_blocker_item_count") != expected_primary or expected_primary != len(items):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker rollup primary blocker count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    blocker_counts = report.get("blocker_counts")
    if not isinstance(blocker_counts, list):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker counts must be a list", "SCHEMA_IDENTITY_MISMATCH")
    expected_counts: dict[str, int] = {}
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker rollup item must be object", "SCHEMA_IDENTITY_MISMATCH")
        for code in item.get("blocking_codes", []):
            expected_counts[str(code)] = expected_counts.get(str(code), 0) + 1
    actual_counts: dict[str, int] = {}
    for entry in blocker_counts:
        if not isinstance(entry, dict):
            return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker count entry must be object", "SCHEMA_IDENTITY_MISMATCH")
        code = str(entry.get("blocker_code") or "")
        actual_counts[code] = int(entry.get("blocked_item_count") or 0)
        if not (
            entry.get("blocks_current_evidence") is True
            and entry.get("blocks_live_order") is True
            and entry.get("blocks_scale_up") is True
            and entry.get("operator_resolution_required") is True
            and entry.get("resolution_scope") == "REVIEW_ONLY_POST_RERUN_RECONCILIATION_REQUIRED"
        ):
            return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "post-rerun blocker count entry lost blocking semantics", "LIVE_FINAL_GUARD_FAILED")
    if actual_counts != expected_counts:
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("unique_blocker_count") != len(blocker_counts) or report.get("unresolved_blocker_count") != len(blocker_counts):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun unique blocker count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if set(report.get("blocker_codes") or []) != set(actual_counts):
        return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker code set mismatch", "SCHEMA_IDENTITY_MISMATCH")
    for item in items:
        if not _candidate_rollup_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "blocker rollup candidate rollup path escaped post-rollup namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not _current_ledger_path_allowed(str(item.get("planned_current_ledger_jsonl_path") or ""), session_id):
            return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "blocker rollup planned current ledger path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
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
            return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("BLOCKED", "post-rerun blocker rollup item attempted current evidence or live mutation", "LIVE_FINAL_GUARD_FAILED")
        if (
            item.get("source_decision_status") != POST_RERUN_RECONCILIATION_WRITE_DENIED_STATUS
            or item.get("source_decision_reason_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
            or item.get("source_decision_outcome") != POST_RERUN_RECONCILIATION_WRITE_DENIED_OUTCOME
            or item.get("primary_item_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
            or item.get("item_rollup_status") != POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_ITEM_STATUS
            or item.get("operator_resolution_required") is not True
            or item.get("path_scope_status") != "MATCH"
            or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(item.get("blocking_codes") or [])
            or item.get("item_blocker_count") != len(item.get("blocking_codes") or [])
        ):
            return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult("FAIL", "post-rerun blocker rollup item lost blocked decision state", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperPostRerunReconciliationBlockerRollupValidationResult(
        "PASS",
        "Upbit PAPER post-rerun reconciliation blocker rollup preserves unresolved blockers without enabling current evidence or live/scale",
        None,
    )
