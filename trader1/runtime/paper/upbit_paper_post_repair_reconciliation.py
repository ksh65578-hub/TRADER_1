from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.ledger.paper_ledger_rollup import paper_ledger_rollup_hash, validate_paper_ledger_rollup_report
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import (
    LEDGER_ROLLUP_REPAIR_BLOCKER_CODE,
    validate_upbit_paper_ledger_rollup_repair_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_POST_REPAIR_RECONCILIATION_SCHEMA_ID = "trader1.upbit_paper_post_repair_reconciliation_report.v1"
POST_REPAIR_RECONCILIATION_TRUTH_ROLE = "paper_runtime_post_repair_reconciliation_truth"
POST_REPAIR_RECONCILIATION_BLOCKER_CODE = "POST_REPAIR_RECONCILIATION_REQUIRED"
REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE = "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED"


@dataclass(frozen=True)
class UpbitPaperPostRepairReconciliationValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_post_repair_reconciliation_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("post_repair_reconciliation_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return path.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "live" not in parts


def _classification_for_item(item: dict[str, Any], candidate_status: str) -> tuple[str, str]:
    if candidate_status != "PASS":
        return "REPAIR_CANDIDATE_BLOCKED_ROLLUP_VALIDATION", item.get("candidate_rollup_validator_blocker_code") or "LEDGER_ROLLUP_BLOCKED"
    if not item.get("source_loop_expected_rollup_hash_match"):
        return "REPAIR_CANDIDATE_BLOCKED_HASH_MISMATCH", REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE
    if item.get("post_repair_reconciliation_required"):
        return "REPAIR_CANDIDATE_BLOCKED_OPERATOR_RECONCILIATION", POST_REPAIR_RECONCILIATION_BLOCKER_CODE
    return "REPAIR_CANDIDATE_BLOCKED_CURRENT_EVIDENCE_MUTATION_POLICY", POST_REPAIR_RECONCILIATION_BLOCKER_CODE


def _status_counts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("hash_reconciliation_status") or "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1
    return [{"hash_reconciliation_status": status, "count": counts[status]} for status in sorted(counts)]


def _build_item(item: dict[str, Any]) -> dict[str, Any]:
    candidate = item.get("candidate_rollup") if isinstance(item.get("candidate_rollup"), dict) else {}
    candidate_result = validate_paper_ledger_rollup_report(candidate)
    classification, blocker_code = _classification_for_item(item, candidate_result.status)
    candidate_hash = item.get("candidate_rollup_hash")
    candidate_recomputed_hash = item.get("candidate_rollup_recomputed_hash")
    if not isinstance(candidate_recomputed_hash, str) and candidate:
        candidate_recomputed_hash = paper_ledger_rollup_hash(candidate)
    return {
        "replacement_loop_id": str(item.get("replacement_loop_id") or "UNKNOWN"),
        "replacement_path": str(item.get("replacement_path") or ""),
        "source_loop_expected_rollup_path": str(item.get("source_loop_expected_rollup_path") or ""),
        "source_loop_expected_rollup_hash": item.get("source_loop_expected_rollup_hash"),
        "source_loop_expected_rollup_artifact_exists": bool(item.get("source_loop_expected_rollup_artifact_exists")),
        "source_loop_expected_rollup_artifact_load_status": str(item.get("source_loop_expected_rollup_artifact_load_status") or "UNKNOWN"),
        "source_loop_expected_rollup_recomputed_hash": item.get("source_loop_expected_rollup_recomputed_hash"),
        "candidate_rollup_artifact_path": str(item.get("candidate_rollup_artifact_path") or ""),
        "candidate_rollup_hash": candidate_hash,
        "candidate_rollup_recomputed_hash": candidate_recomputed_hash,
        "candidate_rollup_hash_self_check": item.get("candidate_rollup_hash_self_check") or ("PASS" if candidate_hash == candidate_recomputed_hash else "FAIL"),
        "candidate_rollup_validator_status": candidate_result.status,
        "candidate_rollup_validator_blocker_code": candidate_result.blocker_code,
        "candidate_rollup_status": candidate.get("rollup_status"),
        "candidate_ledger_jsonl_count": candidate.get("ledger_jsonl_count"),
        "candidate_ledger_event_count": candidate.get("ledger_event_count"),
        "candidate_filled_order_count": candidate.get("filled_order_count"),
        "source_loop_expected_rollup_hash_match": bool(item.get("source_loop_expected_rollup_hash_match")),
        "hash_reconciliation_status": str(item.get("hash_reconciliation_status") or "UNKNOWN"),
        "hash_reconciliation_blocker_code": item.get("hash_reconciliation_blocker_code"),
        "hash_reconciliation_requires_operator_action": bool(item.get("hash_reconciliation_requires_operator_action")),
        "candidate_current_evidence_usable": False,
        "candidate_classification": classification,
        "item_blocker_code": blocker_code,
        "recommended_operator_action": "Rebuild or explicitly reconcile the replacement loop hash before using this PAPER artifact as current evidence.",
        "candidate_rollup": candidate,
        "current_evidence_mutation_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "live_permission_created": False,
    }


def build_upbit_paper_post_repair_reconciliation_report(
    *,
    ledger_rollup_repair_report: dict[str, Any],
    source_repair_report_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_ledger_rollup_repair_report.json",
    reconciliation_id: str = "upbit-paper-post-repair-reconciliation",
) -> dict[str, Any]:
    repair_result = validate_upbit_paper_ledger_rollup_repair_report(ledger_rollup_repair_report)
    session_id = str(ledger_rollup_repair_report.get("session_id", "UNKNOWN"))
    items = [
        _build_item(item)
        for item in ledger_rollup_repair_report.get("items", [])
        if isinstance(item, dict)
    ]
    candidate_pass_count = sum(1 for item in items if item.get("candidate_rollup_validator_status") == "PASS")
    hash_match_count = sum(1 for item in items if item.get("source_loop_expected_rollup_hash_match"))
    usable_count = sum(1 for item in items if item.get("candidate_current_evidence_usable"))
    hash_reconciliation_operator_action_required_count = sum(1 for item in items if item.get("hash_reconciliation_requires_operator_action"))
    blocker_codes = {POST_REPAIR_RECONCILIATION_BLOCKER_CODE}
    if repair_result.status != "PASS":
        blocker_codes.add(repair_result.blocker_code or LEDGER_ROLLUP_REPAIR_BLOCKER_CODE)
    for item in items:
        blocker_codes.add(str(item.get("item_blocker_code") or "UNKNOWN_BLOCKED"))
    if len(items) != int(ledger_rollup_repair_report.get("repair_candidate_count") or 0):
        blocker_codes.add("REPAIR_CANDIDATE_COUNT_MISMATCH")
    report = {
        "schema_id": UPBIT_PAPER_POST_REPAIR_RECONCILIATION_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "post_repair_reconciliation_id": reconciliation_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_REPAIR_RECONCILIATION_TRUTH_ROLE,
        "source_repair_report_path": source_repair_report_path,
        "source_repair_report_hash": ledger_rollup_repair_report.get("repair_report_hash"),
        "source_repair_report_status": ledger_rollup_repair_report.get("repair_report_status"),
        "source_repair_primary_blocker_code": ledger_rollup_repair_report.get("primary_blocker_code"),
        "repair_candidate_count": int(ledger_rollup_repair_report.get("repair_candidate_count") or 0),
        "reconciliation_item_count": len(items),
        "candidate_rollup_pass_count": candidate_pass_count,
        "candidate_rollup_blocked_count": len(items) - candidate_pass_count,
        "source_loop_expected_rollup_hash_match_count": hash_match_count,
        "source_loop_expected_rollup_hash_mismatch_count": len(items) - hash_match_count,
        "hash_reconciliation_status_counts": _status_counts(items),
        "hash_reconciliation_operator_action_required_count": hash_reconciliation_operator_action_required_count,
        "candidate_current_evidence_usable_count": usable_count,
        "candidate_current_evidence_blocked_count": len(items) - usable_count,
        "post_repair_reconciliation_status": "BLOCKED",
        "primary_blocker_code": POST_REPAIR_RECONCILIATION_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Keep the repaired ledger rollup as a candidate only. Resolve hash mismatch or run an explicit operator reconciliation before any current-evidence update.",
        "current_evidence_mutation_allowed": False,
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
        "post_repair_reconciliation_hash": "",
    }
    report["post_repair_reconciliation_hash"] = upbit_paper_post_repair_reconciliation_hash(report)
    return report


def write_upbit_paper_post_repair_reconciliation_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_post_repair_reconciliation_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_repair_reconciliation_report(report: dict[str, Any]) -> UpbitPaperPostRepairReconciliationValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "post_repair_reconciliation_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "source_repair_report_path",
        "source_repair_report_hash",
        "source_repair_report_status",
        "source_repair_primary_blocker_code",
        "repair_candidate_count",
        "reconciliation_item_count",
        "candidate_rollup_pass_count",
        "candidate_rollup_blocked_count",
        "source_loop_expected_rollup_hash_match_count",
        "source_loop_expected_rollup_hash_mismatch_count",
        "hash_reconciliation_status_counts",
        "hash_reconciliation_operator_action_required_count",
        "candidate_current_evidence_usable_count",
        "candidate_current_evidence_blocked_count",
        "post_repair_reconciliation_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "current_evidence_mutation_allowed",
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
        "post_repair_reconciliation_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", f"post-repair reconciliation missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_POST_REPAIR_RECONCILIATION_SCHEMA_ID:
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("post_repair_reconciliation_hash") != upbit_paper_post_repair_reconciliation_hash(report):
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRepairReconciliationValidationResult("BLOCKED", "post-repair reconciliation scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != POST_REPAIR_RECONCILIATION_TRUTH_ROLE:
        return UpbitPaperPostRepairReconciliationValidationResult("BLOCKED", "post-repair reconciliation cannot claim live or execution truth", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "current_evidence_mutation_allowed",
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
        return UpbitPaperPostRepairReconciliationValidationResult("BLOCKED", "post-repair reconciliation created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if report.get("post_repair_reconciliation_status") != "BLOCKED" or report.get("primary_blocker_code") != POST_REPAIR_RECONCILIATION_BLOCKER_CODE:
        return UpbitPaperPostRepairReconciliationValidationResult("BLOCKED", "post-repair reconciliation must remain BLOCKED until operator reconciliation", POST_REPAIR_RECONCILIATION_BLOCKER_CODE)
    if report.get("source_repair_report_status") != "BLOCKED" or report.get("source_repair_primary_blocker_code") != LEDGER_ROLLUP_REPAIR_BLOCKER_CODE:
        return UpbitPaperPostRepairReconciliationValidationResult("BLOCKED", "source repair report must remain the blocked repair candidate source", LEDGER_ROLLUP_REPAIR_BLOCKER_CODE)
    session_id = str(report.get("session_id"))
    if not _artifact_path_allowed(str(report.get("source_repair_report_path") or ""), session_id):
        return UpbitPaperPostRepairReconciliationValidationResult("BLOCKED", "source repair report escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    items = report.get("items")
    if not isinstance(items, list) or report.get("reconciliation_item_count") != len(items):
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("repair_candidate_count") != len(items):
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation candidate count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    pass_count = sum(1 for item in items if isinstance(item, dict) and item.get("candidate_rollup_validator_status") == "PASS")
    hash_match_count = sum(1 for item in items if isinstance(item, dict) and item.get("source_loop_expected_rollup_hash_match"))
    usable_count = sum(1 for item in items if isinstance(item, dict) and item.get("candidate_current_evidence_usable"))
    if report.get("candidate_rollup_pass_count") != pass_count or report.get("candidate_rollup_blocked_count") != len(items) - pass_count:
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation candidate validator rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if (
        report.get("source_loop_expected_rollup_hash_match_count") != hash_match_count
        or report.get("source_loop_expected_rollup_hash_mismatch_count") != len(items) - hash_match_count
    ):
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation hash-match rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_status_counts = _status_counts(items)
    if report.get("hash_reconciliation_status_counts") != expected_status_counts:
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation hash status rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
    required_operator_count = sum(1 for item in items if item.get("hash_reconciliation_requires_operator_action"))
    if report.get("hash_reconciliation_operator_action_required_count") != required_operator_count:
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation hash operator-action count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("candidate_current_evidence_usable_count") != usable_count or report.get("candidate_current_evidence_blocked_count") != len(items) - usable_count:
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation current-evidence count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if usable_count:
        return UpbitPaperPostRepairReconciliationValidationResult("BLOCKED", "post-repair reconciliation cannot mark repair candidates as current evidence", "LIVE_FINAL_GUARD_FAILED")
    blocker_codes = set(report.get("blocker_codes") or [])
    if POST_REPAIR_RECONCILIATION_BLOCKER_CODE not in blocker_codes:
        return UpbitPaperPostRepairReconciliationValidationResult("BLOCKED", "post-repair reconciliation blocker missing", POST_REPAIR_RECONCILIATION_BLOCKER_CODE)
    if report.get("source_loop_expected_rollup_hash_mismatch_count") and REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE not in blocker_codes:
        return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation did not expose hash mismatch blocker", "SCHEMA_IDENTITY_MISMATCH")
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation item must be object", "SCHEMA_IDENTITY_MISMATCH")
        for path_field in ("replacement_path", "source_loop_expected_rollup_path", "candidate_rollup_artifact_path"):
            if not _artifact_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperPostRepairReconciliationValidationResult("BLOCKED", f"post-repair reconciliation {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if (
            item.get("candidate_current_evidence_usable")
            or item.get("current_evidence_mutation_allowed")
            or item.get("persistent_loop_mutation_allowed")
            or item.get("source_delete_allowed")
            or item.get("live_permission_created")
        ):
            return UpbitPaperPostRepairReconciliationValidationResult("BLOCKED", "post-repair reconciliation item attempted evidence mutation or live permission", "LIVE_FINAL_GUARD_FAILED")
        candidate = item.get("candidate_rollup")
        if not isinstance(candidate, dict):
            return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation candidate rollup missing", "SCHEMA_IDENTITY_MISMATCH")
        candidate_result = validate_paper_ledger_rollup_report(candidate)
        if item.get("candidate_rollup_validator_status") != candidate_result.status:
            return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation candidate validator status mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if candidate.get("rollup_hash") != item.get("candidate_rollup_hash"):
            return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation candidate hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
        candidate_recomputed_hash = paper_ledger_rollup_hash(candidate)
        if (
            item.get("candidate_rollup_recomputed_hash") != candidate_recomputed_hash
            or item.get("candidate_rollup_hash_self_check") != ("PASS" if candidate.get("rollup_hash") == candidate_recomputed_hash else "FAIL")
        ):
            return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation candidate hash self-check mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if not item.get("source_loop_expected_rollup_artifact_exists") and item.get("source_loop_expected_rollup_artifact_load_status") == "PASS":
            return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation expected artifact existence mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("source_loop_expected_rollup_artifact_load_status") == "PASS":
            expected_recomputed_hash = item.get("source_loop_expected_rollup_recomputed_hash")
            if not isinstance(expected_recomputed_hash, str) or len(expected_recomputed_hash) != 64:
                return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation expected artifact hash missing", "SCHEMA_IDENTITY_MISMATCH")
        elif item.get("source_loop_expected_rollup_recomputed_hash") is not None:
            return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation expected artifact hash set while unreadable", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("hash_reconciliation_status") == "MATCH":
            if (
                not item.get("source_loop_expected_rollup_hash_match")
                or item.get("hash_reconciliation_blocker_code") is not None
                or item.get("hash_reconciliation_requires_operator_action")
            ):
                return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation hash match status mismatch", "SCHEMA_IDENTITY_MISMATCH")
        elif (
            item.get("hash_reconciliation_blocker_code") != REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE
            or not item.get("hash_reconciliation_requires_operator_action")
        ):
            return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation hash reconciliation blocker mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if (
            candidate.get("ledger_jsonl_count") != item.get("candidate_ledger_jsonl_count")
            or candidate.get("ledger_event_count") != item.get("candidate_ledger_event_count")
            or candidate.get("filled_order_count") != item.get("candidate_filled_order_count")
        ):
            return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation candidate counts mismatch", "SCHEMA_IDENTITY_MISMATCH")
        classification, expected_blocker = _classification_for_item(item, candidate_result.status)
        if item.get("candidate_classification") != classification or item.get("item_blocker_code") != expected_blocker:
            return UpbitPaperPostRepairReconciliationValidationResult("FAIL", "post-repair reconciliation candidate classification mismatch", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperPostRepairReconciliationValidationResult(
        "PASS",
        "Upbit PAPER post-repair reconciliation is scoped, blocked, hash-aware, and keeps repair candidates out of current evidence",
        None,
    )
