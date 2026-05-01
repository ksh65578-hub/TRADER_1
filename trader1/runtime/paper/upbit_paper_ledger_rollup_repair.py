from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.ledger.paper_ledger_rollup import (
    build_paper_ledger_rollup_report,
    paper_ledger_rollup_hash,
    validate_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_blocked_repair_plan import (
    BLOCKED_REPAIR_PLAN_BLOCKER_CODE,
    validate_upbit_paper_blocked_repair_plan_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_LEDGER_ROLLUP_REPAIR_SCHEMA_ID = "trader1.upbit_paper_ledger_rollup_repair_report.v1"
LEDGER_ROLLUP_REPAIR_ARTIFACT_ROLE = "LEDGER_ROLLUP_REPAIR_CANDIDATE_NOT_CURRENT_EVIDENCE"
LEDGER_ROLLUP_REPAIR_BLOCKER_CODE = "POST_REPAIR_RECONCILIATION_REQUIRED"
REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE = "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED"


@dataclass(frozen=True)
class UpbitPaperLedgerRollupRepairValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_ledger_rollup_repair_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("repair_report_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return root.resolve().joinpath(*parts)


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return path.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "live" not in parts


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


def _expected_rollup_artifact_state(*, root: Path, session_id: str, expected_rollup_path: str) -> tuple[bool, str, str | None]:
    if not expected_rollup_path:
        return False, "MISSING_PATH", None
    if not _artifact_path_allowed(expected_rollup_path, session_id):
        return False, "PATH_SCOPE_MISMATCH", None
    path = _rooted(root, expected_rollup_path)
    exists = path.exists()
    expected_rollup, load_error = _safe_load_json(path)
    if expected_rollup is None:
        return exists, str(load_error or "MISSING"), None
    return exists, "PASS", paper_ledger_rollup_hash(expected_rollup)


def _hash_reconciliation_status(
    *,
    source_loop_expected_hash: Any,
    candidate_hash: Any,
    candidate_recomputed_hash: str,
    expected_artifact_exists: bool,
    expected_artifact_load_status: str,
    expected_artifact_recomputed_hash: str | None,
) -> str:
    if candidate_hash != candidate_recomputed_hash:
        return "CANDIDATE_HASH_SELF_CHECK_FAIL"
    if not isinstance(source_loop_expected_hash, str) or len(source_loop_expected_hash) != 64:
        return "SOURCE_EXPECTED_HASH_MISSING"
    if source_loop_expected_hash != candidate_hash:
        if not expected_artifact_exists:
            return "SOURCE_EXPECTED_ROLLUP_ARTIFACT_MISSING"
        if expected_artifact_load_status != "PASS":
            return "SOURCE_EXPECTED_ROLLUP_ARTIFACT_UNREADABLE"
        if expected_artifact_recomputed_hash and expected_artifact_recomputed_hash != source_loop_expected_hash:
            return "SOURCE_EXPECTED_ROLLUP_HASH_STALE"
        return "SOURCE_EXPECTED_ROLLUP_HASH_MISMATCH"
    if expected_artifact_load_status != "PASS":
        return "SOURCE_EXPECTED_ROLLUP_ARTIFACT_UNREADABLE"
    if expected_artifact_recomputed_hash != source_loop_expected_hash:
        return "SOURCE_EXPECTED_ROLLUP_HASH_STALE"
    return "MATCH"


def _status_counts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("hash_reconciliation_status") or "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1
    return [{"hash_reconciliation_status": status, "count": counts[status]} for status in sorted(counts)]


def _cycle_ledger_path(root: Path, session_id: str, cycle_id: str) -> Path:
    return _runtime_base(root, session_id) / "ledger" / "cycles" / f"{cycle_id}.paper_ledger_events.jsonl"


def _candidate_path(root: Path, session_id: str, replacement_loop_id: str) -> Path:
    safe_loop_id = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in replacement_loop_id)
    return _runtime_base(root, session_id) / "paper_runtime" / "repairs" / f"{safe_loop_id}.ledger_rollup_candidate.json"


def _build_repair_item(*, root: Path, session_id: str, plan_item: dict[str, Any]) -> dict[str, Any]:
    replacement_loop_id = str(plan_item.get("replacement_loop_id") or "unknown-replacement")
    replacement_path = str(plan_item.get("replacement_path") or "")
    expected_rollup_path = str(plan_item.get("paper_ledger_rollup_path") or "")
    replacement, load_error = _safe_load_json(_rooted(root, replacement_path))
    cycle_ids = [
        str(cycle.get("cycle_id"))
        for cycle in (replacement or {}).get("cycle_results", [])
        if isinstance(cycle, dict) and isinstance(cycle.get("cycle_id"), str)
    ]
    cycle_ledger_paths = [_cycle_ledger_path(root, session_id, cycle_id) for cycle_id in cycle_ids]
    present_cycle_ledger_paths = [path for path in cycle_ledger_paths if path.exists()]
    missing_cycle_ledger_paths = [path for path in cycle_ledger_paths if not path.exists()]
    candidate = build_paper_ledger_rollup_report(
        root=root,
        session_id=session_id,
        rollup_id=f"{replacement_loop_id}-repair-candidate",
        ledger_paths=present_cycle_ledger_paths,
    )
    candidate_result = validate_paper_ledger_rollup_report(candidate)
    candidate_artifact_path = _candidate_path(root, session_id, replacement_loop_id)
    durable_atomic_write_json(candidate_artifact_path, candidate)
    source_loop_expected_hash = (replacement or {}).get("paper_ledger_rollup_hash")
    candidate_hash = candidate.get("rollup_hash")
    candidate_recomputed_hash = paper_ledger_rollup_hash(candidate)
    expected_exists, expected_load_status, expected_recomputed_hash = _expected_rollup_artifact_state(
        root=root,
        session_id=session_id,
        expected_rollup_path=expected_rollup_path,
    )
    hash_reconciliation_status = _hash_reconciliation_status(
        source_loop_expected_hash=source_loop_expected_hash,
        candidate_hash=candidate_hash,
        candidate_recomputed_hash=candidate_recomputed_hash,
        expected_artifact_exists=expected_exists,
        expected_artifact_load_status=expected_load_status,
        expected_artifact_recomputed_hash=expected_recomputed_hash,
    )
    hash_reconciliation_blocker_code = None if hash_reconciliation_status == "MATCH" else REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE
    return {
        "replacement_loop_id": replacement_loop_id,
        "replacement_path": replacement_path,
        "replacement_load_status": "PASS" if replacement is not None else str(load_error or "UNKNOWN"),
        "replacement_path_scope_status": "MATCH" if _artifact_path_allowed(replacement_path, session_id) else "MISMATCH",
        "safe_repair_lane": str(plan_item.get("safe_repair_lane") or "UNKNOWN"),
        "source_cycle_count": len(cycle_ids),
        "present_cycle_ledger_jsonl_count": len(present_cycle_ledger_paths),
        "missing_cycle_ledger_jsonl_count": len(missing_cycle_ledger_paths),
        "missing_cycle_ledger_jsonl_paths": [_relative_posix(path, root) for path in missing_cycle_ledger_paths],
        "source_loop_expected_rollup_path": expected_rollup_path,
        "source_loop_expected_rollup_hash": source_loop_expected_hash,
        "source_loop_expected_rollup_artifact_exists": expected_exists,
        "source_loop_expected_rollup_artifact_load_status": expected_load_status,
        "source_loop_expected_rollup_recomputed_hash": expected_recomputed_hash,
        "candidate_rollup_artifact_path": _relative_posix(candidate_artifact_path, root),
        "candidate_rollup_status": candidate.get("rollup_status"),
        "candidate_rollup_validator_status": candidate_result.status,
        "candidate_rollup_validator_blocker_code": candidate_result.blocker_code,
        "candidate_rollup_hash": candidate_hash,
        "candidate_rollup_recomputed_hash": candidate_recomputed_hash,
        "candidate_rollup_hash_self_check": "PASS" if candidate_hash == candidate_recomputed_hash else "FAIL",
        "source_loop_expected_rollup_hash_match": bool(source_loop_expected_hash and source_loop_expected_hash == candidate_hash),
        "hash_reconciliation_status": hash_reconciliation_status,
        "hash_reconciliation_blocker_code": hash_reconciliation_blocker_code,
        "hash_reconciliation_requires_operator_action": hash_reconciliation_status != "MATCH",
        "candidate_ledger_jsonl_count": candidate.get("ledger_jsonl_count"),
        "candidate_ledger_event_count": candidate.get("ledger_event_count"),
        "candidate_filled_order_count": candidate.get("filled_order_count"),
        "candidate_primary_blocker_code": candidate.get("primary_blocker_code"),
        "candidate_rollup": candidate,
        "candidate_artifact_is_current_evidence": False,
        "current_evidence_mutation_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "post_repair_reconciliation_required": True,
        "source_delete_allowed": False,
        "live_permission_created": False,
    }


def build_upbit_paper_ledger_rollup_repair_report(
    *,
    root: Path,
    repair_plan_report: dict[str, Any],
    source_repair_plan_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_blocked_repair_plan_report.json",
    repair_report_id: str = "upbit-paper-ledger-rollup-ready-repair",
) -> dict[str, Any]:
    root = Path(root).resolve()
    plan_result = validate_upbit_paper_blocked_repair_plan_report(repair_plan_report)
    session_id = str(repair_plan_report.get("session_id", "UNKNOWN"))
    repair_plan_items = [
        item
        for item in repair_plan_report.get("items", [])
        if isinstance(item, dict) and item.get("safe_repair_lane") == "LEDGER_ROLLUP_REBUILD_READY"
    ]
    items = [_build_repair_item(root=root, session_id=session_id, plan_item=item) for item in repair_plan_items]
    candidate_pass_count = sum(1 for item in items if item.get("candidate_rollup_validator_status") == "PASS")
    source_hash_match_count = sum(1 for item in items if item.get("source_loop_expected_rollup_hash_match"))
    hash_reconciliation_operator_action_required_count = sum(1 for item in items if item.get("hash_reconciliation_requires_operator_action"))
    blockers = [LEDGER_ROLLUP_REPAIR_BLOCKER_CODE]
    if plan_result.status != "PASS":
        blockers.append(plan_result.blocker_code or BLOCKED_REPAIR_PLAN_BLOCKER_CODE)
    if candidate_pass_count != len(items):
        blockers.append("LEDGER_ROLLUP_BLOCKED")
    if repair_plan_report.get("repair_item_count", 0) != len(items):
        blockers.append(BLOCKED_REPAIR_PLAN_BLOCKER_CODE)
    report = {
        "schema_id": UPBIT_PAPER_LEDGER_ROLLUP_REPAIR_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "repair_report_id": repair_report_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": "paper_runtime_ledger_rollup_repair_truth",
        "repair_artifact_role": LEDGER_ROLLUP_REPAIR_ARTIFACT_ROLE,
        "source_repair_plan_path": source_repair_plan_path,
        "source_repair_plan_hash": repair_plan_report.get("repair_plan_hash"),
        "source_repair_plan_status": repair_plan_report.get("repair_plan_status"),
        "source_repair_plan_item_count": repair_plan_report.get("repair_item_count"),
        "ledger_rollup_rebuild_ready_source_count": repair_plan_report.get("ledger_rollup_rebuild_ready_count"),
        "repair_candidate_count": len(items),
        "candidate_rollup_pass_count": candidate_pass_count,
        "candidate_rollup_blocked_count": len(items) - candidate_pass_count,
        "source_loop_expected_rollup_hash_match_count": source_hash_match_count,
        "source_loop_expected_rollup_hash_mismatch_count": len(items) - source_hash_match_count,
        "hash_reconciliation_status_counts": _status_counts(items),
        "hash_reconciliation_operator_action_required_count": hash_reconciliation_operator_action_required_count,
        "remaining_non_ready_repair_item_count": int(repair_plan_report.get("repair_item_count") or 0) - len(items),
        "repair_report_status": "BLOCKED",
        "primary_blocker_code": LEDGER_ROLLUP_REPAIR_BLOCKER_CODE,
        "blocker_codes": sorted(set(blockers)),
        "items": items,
        "operator_next_action": "Run validator-backed post-repair reconciliation before using any regenerated replacement as current evidence.",
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
        "repair_report_hash": "",
    }
    report["repair_report_hash"] = upbit_paper_ledger_rollup_repair_hash(report)
    return report


def write_upbit_paper_ledger_rollup_repair_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(root, str(report["session_id"])) / "paper_runtime" / "upbit_paper_ledger_rollup_repair_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_ledger_rollup_repair_report(report: dict[str, Any]) -> UpbitPaperLedgerRollupRepairValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "repair_report_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "repair_artifact_role",
        "source_repair_plan_path",
        "source_repair_plan_hash",
        "source_repair_plan_status",
        "source_repair_plan_item_count",
        "ledger_rollup_rebuild_ready_source_count",
        "repair_candidate_count",
        "candidate_rollup_pass_count",
        "candidate_rollup_blocked_count",
        "source_loop_expected_rollup_hash_match_count",
        "source_loop_expected_rollup_hash_mismatch_count",
        "hash_reconciliation_status_counts",
        "hash_reconciliation_operator_action_required_count",
        "remaining_non_ready_repair_item_count",
        "repair_report_status",
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
        "repair_report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperLedgerRollupRepairValidationResult("FAIL", f"ledger rollup repair report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_LEDGER_ROLLUP_REPAIR_SCHEMA_ID:
        return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair report schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("repair_report_hash") != upbit_paper_ledger_rollup_repair_hash(report):
        return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair report hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperLedgerRollupRepairValidationResult("BLOCKED", "ledger rollup repair scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != "paper_runtime_ledger_rollup_repair_truth" or report.get("repair_artifact_role") != LEDGER_ROLLUP_REPAIR_ARTIFACT_ROLE:
        return UpbitPaperLedgerRollupRepairValidationResult("BLOCKED", "ledger rollup repair cannot claim execution/live truth", "LIVE_FINAL_GUARD_FAILED")
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
        return UpbitPaperLedgerRollupRepairValidationResult("BLOCKED", "ledger rollup repair created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    items = report.get("items")
    if not isinstance(items, list) or report.get("repair_candidate_count") != len(items):
        return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair candidate count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    pass_count = sum(1 for item in items if item.get("candidate_rollup_validator_status") == "PASS")
    hash_match_count = sum(1 for item in items if item.get("source_loop_expected_rollup_hash_match"))
    if report.get("candidate_rollup_pass_count") != pass_count or report.get("candidate_rollup_blocked_count") != len(items) - pass_count:
        return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair candidate status rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if (
        report.get("source_loop_expected_rollup_hash_match_count") != hash_match_count
        or report.get("source_loop_expected_rollup_hash_mismatch_count") != len(items) - hash_match_count
    ):
        return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair source hash rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_status_counts = _status_counts(items)
    if report.get("hash_reconciliation_status_counts") != expected_status_counts:
        return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair hash status rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
    required_operator_count = sum(1 for item in items if item.get("hash_reconciliation_requires_operator_action"))
    if report.get("hash_reconciliation_operator_action_required_count") != required_operator_count:
        return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair hash operator-action count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("repair_report_status") != "BLOCKED" or report.get("primary_blocker_code") != LEDGER_ROLLUP_REPAIR_BLOCKER_CODE:
        return UpbitPaperLedgerRollupRepairValidationResult("BLOCKED", "ledger rollup repair must remain blocked until post-repair reconciliation", LEDGER_ROLLUP_REPAIR_BLOCKER_CODE)
    session_id = str(report.get("session_id"))
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair item must be object", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("safe_repair_lane") != "LEDGER_ROLLUP_REBUILD_READY":
            return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair item lane mismatch", "SCHEMA_IDENTITY_MISMATCH")
        for path_field in ("replacement_path", "source_loop_expected_rollup_path", "candidate_rollup_artifact_path"):
            if not _artifact_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperLedgerRollupRepairValidationResult("BLOCKED", f"ledger rollup repair {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if (
            item.get("candidate_artifact_is_current_evidence")
            or item.get("current_evidence_mutation_allowed")
            or item.get("persistent_loop_mutation_allowed")
            or item.get("source_delete_allowed")
            or item.get("live_permission_created")
            or not item.get("post_repair_reconciliation_required")
        ):
            return UpbitPaperLedgerRollupRepairValidationResult("BLOCKED", "ledger rollup repair item attempted evidence mutation or live permission", "LIVE_FINAL_GUARD_FAILED")
        candidate = item.get("candidate_rollup")
        if not isinstance(candidate, dict):
            return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair candidate rollup missing", "SCHEMA_IDENTITY_MISMATCH")
        candidate_result = validate_paper_ledger_rollup_report(candidate)
        if item.get("candidate_rollup_validator_status") != candidate_result.status:
            return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair candidate validator status mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if candidate_result.status != "PASS":
            return UpbitPaperLedgerRollupRepairValidationResult("BLOCKED", candidate_result.message, candidate_result.blocker_code or "LEDGER_ROLLUP_BLOCKED")
        if candidate.get("rollup_hash") != item.get("candidate_rollup_hash"):
            return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair candidate hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
        candidate_recomputed_hash = paper_ledger_rollup_hash(candidate)
        if (
            item.get("candidate_rollup_recomputed_hash") != candidate_recomputed_hash
            or item.get("candidate_rollup_hash_self_check") != ("PASS" if candidate.get("rollup_hash") == candidate_recomputed_hash else "FAIL")
        ):
            return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair candidate hash self-check mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if not item.get("source_loop_expected_rollup_artifact_exists") and item.get("source_loop_expected_rollup_artifact_load_status") == "PASS":
            return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair expected artifact existence mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("source_loop_expected_rollup_artifact_load_status") == "PASS":
            expected_recomputed_hash = item.get("source_loop_expected_rollup_recomputed_hash")
            if not isinstance(expected_recomputed_hash, str) or len(expected_recomputed_hash) != 64:
                return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair expected artifact hash missing", "SCHEMA_IDENTITY_MISMATCH")
        elif item.get("source_loop_expected_rollup_recomputed_hash") is not None:
            return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair expected artifact hash set while unreadable", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("hash_reconciliation_status") == "MATCH":
            if (
                not item.get("source_loop_expected_rollup_hash_match")
                or item.get("hash_reconciliation_blocker_code") is not None
                or item.get("hash_reconciliation_requires_operator_action")
            ):
                return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair hash match status mismatch", "SCHEMA_IDENTITY_MISMATCH")
        elif (
            item.get("hash_reconciliation_blocker_code") != REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE
            or not item.get("hash_reconciliation_requires_operator_action")
        ):
            return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair hash reconciliation blocker mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if (
            candidate.get("ledger_jsonl_count") != item.get("candidate_ledger_jsonl_count")
            or candidate.get("ledger_event_count") != item.get("candidate_ledger_event_count")
            or candidate.get("filled_order_count") != item.get("candidate_filled_order_count")
        ):
            return UpbitPaperLedgerRollupRepairValidationResult("FAIL", "ledger rollup repair candidate count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperLedgerRollupRepairValidationResult(
        "PASS",
        "Upbit PAPER ledger rollup repair candidates are scoped, self-validating, not current evidence, and live-blocked",
        None,
    )
