from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_repair_operator_queue import (
    REPAIR_OPERATOR_QUEUE_BLOCKER_CODE,
    validate_upbit_paper_repair_operator_queue_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_MISSING_CYCLE_RERUN_GUARD_SCHEMA_ID = "trader1.upbit_paper_missing_cycle_rerun_guard_report.v1"
MISSING_CYCLE_RERUN_GUARD_TRUTH_ROLE = "paper_runtime_missing_cycle_rerun_guard_truth"
MISSING_CYCLE_RERUN_GUARD_ROLE = "PAPER_RUNTIME_MISSING_CYCLE_RERUN_GUARD_NOT_EVIDENCE"
MISSING_CYCLE_RERUN_GUARD_BLOCKER_CODE = "MISSING_CYCLE_LEDGER_RERUN_GUARD_ACTIVE"
MISSING_CYCLE_LEDGER_RERUN_REQUIRED_BLOCKER_CODE = "MISSING_CYCLE_LEDGER_RERUN_REQUIRED"
RECOVERY_GUARD_RERUN_REQUIRED_BLOCKER_CODE = "RECOVERY_GUARD_RERUN_REQUIRED_BEFORE_CYCLE_RERUN"
RERUN_IDENTITY_RECONCILIATION_BLOCKER_CODE = "MISSING_CYCLE_RERUN_IDENTITY_RECONCILIATION_REQUIRED"


@dataclass(frozen=True)
class UpbitPaperMissingCycleRerunGuardValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_missing_cycle_rerun_guard_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("guard_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
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


def _cycle_id_from_ledger_path(path: str) -> str:
    name = Path(path.replace("\\", "/")).name
    suffix = ".paper_ledger_events.jsonl"
    return name[: -len(suffix)] if name.endswith(suffix) else ""


def _planned_staging_paths(root: Path, session_id: str, replacement_loop_id: str, cycle_id: str) -> list[str]:
    safe_loop_id = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in replacement_loop_id)
    safe_cycle_id = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in cycle_id)
    base = _runtime_base(root, session_id) / "paper_runtime" / "rerun_candidates" / safe_loop_id
    return [
        _relative_posix(base / f"{safe_cycle_id}.runtime_cycle.json", root),
        _relative_posix(base / f"{safe_cycle_id}.paper_ledger_events.jsonl", root),
        _relative_posix(base / f"{safe_cycle_id}.writer_report.json", root),
    ]


def _replacement_cycle_ids(replacement: dict[str, Any] | None) -> list[str]:
    return [
        str(cycle.get("cycle_id"))
        for cycle in (replacement or {}).get("cycle_results", [])
        if isinstance(cycle, dict) and isinstance(cycle.get("cycle_id"), str)
    ]


def _build_guard_item(*, root: Path, session_id: str, queue_item: dict[str, Any]) -> dict[str, Any]:
    replacement_loop_id = str(queue_item.get("replacement_loop_id") or "unknown-replacement")
    replacement_path = str(queue_item.get("replacement_path") or "")
    replacement_path_scope_status = "MATCH" if _artifact_path_allowed(replacement_path, session_id) else "MISMATCH"
    if replacement_path_scope_status == "MATCH":
        replacement, load_error = _safe_load_json(_rooted(root, replacement_path))
    else:
        replacement, load_error = None, "PATH_SCOPE_MISMATCH"
    expected_cycle_ids = _replacement_cycle_ids(replacement)
    missing_paths = [str(path) for path in queue_item.get("cycle_ledger_jsonl_missing_paths") or []]
    missing_cycle_ids = [_cycle_id_from_ledger_path(path) for path in missing_paths]
    planned_paths = [
        planned_path
        for cycle_id in missing_cycle_ids
        for planned_path in _planned_staging_paths(root, session_id, replacement_loop_id, cycle_id)
    ]
    missing_path_scope_status = "MATCH" if all(_artifact_path_allowed(path, session_id) for path in missing_paths) else "MISMATCH"
    planned_path_scope_status = "MATCH" if all(_artifact_path_allowed(path, session_id) for path in planned_paths) else "MISMATCH"
    identity_match = bool(missing_cycle_ids) and all(cycle_id in expected_cycle_ids for cycle_id in missing_cycle_ids)
    recovery_required = bool(queue_item.get("requires_recovery_guard_rerun"))
    if recovery_required:
        status = "BLOCKED_RECOVERY_GUARD_REQUIRED"
        action = "Run and pass the recovery guard before staging any missing PAPER cycle rerun."
        blocker = RECOVERY_GUARD_RERUN_REQUIRED_BLOCKER_CODE
    elif replacement is None or missing_path_scope_status != "MATCH" or planned_path_scope_status != "MATCH" or not identity_match:
        status = "BLOCKED_IDENTITY_RECONCILIATION_REQUIRED"
        action = "Reconcile replacement loop identity and scoped missing-cycle paths before any rerun."
        blocker = RERUN_IDENTITY_RECONCILIATION_BLOCKER_CODE
    else:
        status = "READY_FOR_BOUNDED_PAPER_RERUN_STAGING"
        action = "A later bounded PAPER rerun executor may stage these cycles; current evidence remains unchanged."
        blocker = MISSING_CYCLE_LEDGER_RERUN_REQUIRED_BLOCKER_CODE
    blockers = set(str(code) for code in queue_item.get("blocking_codes") or [])
    blockers.update({REPAIR_OPERATOR_QUEUE_BLOCKER_CODE, blocker})
    return {
        "source_queue_priority_order": int(queue_item.get("priority_order") or 0),
        "replacement_loop_id": replacement_loop_id,
        "replacement_path": replacement_path,
        "replacement_load_status": "PASS" if replacement is not None else str(load_error or "UNKNOWN"),
        "replacement_path_scope_status": replacement_path_scope_status,
        "safe_repair_lane": str(queue_item.get("safe_repair_lane") or "UNKNOWN"),
        "requires_runtime_cycle_rerun": bool(queue_item.get("requires_runtime_cycle_rerun")),
        "requires_recovery_guard_rerun": recovery_required,
        "missing_cycle_ledger_jsonl_count": len(missing_paths),
        "missing_cycle_ledger_jsonl_paths": missing_paths,
        "missing_cycle_ids": missing_cycle_ids,
        "replacement_cycle_ids": expected_cycle_ids,
        "missing_cycle_identity_match": identity_match,
        "missing_cycle_path_scope_status": missing_path_scope_status,
        "planned_staging_artifact_paths": planned_paths,
        "planned_staging_artifact_count": len(planned_paths),
        "planned_staging_path_scope_status": planned_path_scope_status,
        "rerun_guard_status": status,
        "rerun_guard_blocker_code": blocker,
        "next_action": action,
        "next_patch_staging_rerun_candidate_eligible": status == "READY_FOR_BOUNDED_PAPER_RERUN_STAGING",
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "candidate_current_evidence_usable": False,
        "requires_post_rerun_ledger_rollup": True,
        "requires_post_rerun_reconciliation": True,
        "live_permission_created": False,
        "blocking_codes": sorted(blockers),
    }


def build_upbit_paper_missing_cycle_rerun_guard_report(
    *,
    root: Path,
    repair_operator_queue_report: dict[str, Any],
    guard_id: str = "upbit-paper-missing-cycle-rerun-guard",
) -> dict[str, Any]:
    root = Path(root).resolve()
    queue_result = validate_upbit_paper_repair_operator_queue_report(repair_operator_queue_report)
    session_id = str(repair_operator_queue_report.get("session_id", "UNKNOWN"))
    source_items = [
        item
        for item in repair_operator_queue_report.get("items", [])
        if isinstance(item, dict) and item.get("requires_runtime_cycle_rerun")
    ]
    items = [_build_guard_item(root=root, session_id=session_id, queue_item=item) for item in source_items]
    blockers = {MISSING_CYCLE_RERUN_GUARD_BLOCKER_CODE, MISSING_CYCLE_LEDGER_RERUN_REQUIRED_BLOCKER_CODE}
    if queue_result.status != "PASS":
        blockers.add(queue_result.blocker_code or REPAIR_OPERATOR_QUEUE_BLOCKER_CODE)
    if any(item.get("requires_recovery_guard_rerun") for item in items):
        blockers.add(RECOVERY_GUARD_RERUN_REQUIRED_BLOCKER_CODE)
    if any(item.get("rerun_guard_status") == "BLOCKED_IDENTITY_RECONCILIATION_REQUIRED" for item in items):
        blockers.add(RERUN_IDENTITY_RECONCILIATION_BLOCKER_CODE)
    report = {
        "schema_id": UPBIT_PAPER_MISSING_CYCLE_RERUN_GUARD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "guard_id": guard_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": MISSING_CYCLE_RERUN_GUARD_TRUTH_ROLE,
        "guard_role": MISSING_CYCLE_RERUN_GUARD_ROLE,
        "source_repair_operator_queue_hash": repair_operator_queue_report.get("queue_hash"),
        "source_repair_operator_queue_status": repair_operator_queue_report.get("queue_status"),
        "source_queue_item_count": repair_operator_queue_report.get("queue_item_count"),
        "source_runtime_cycle_rerun_required_count": repair_operator_queue_report.get("runtime_cycle_rerun_required_count"),
        "source_recovery_guard_rerun_required_count": repair_operator_queue_report.get("recovery_guard_rerun_required_count"),
        "guard_item_count": len(items),
        "rerun_ready_item_count": sum(1 for item in items if item["next_patch_staging_rerun_candidate_eligible"]),
        "recovery_guard_blocked_item_count": sum(1 for item in items if item["requires_recovery_guard_rerun"]),
        "identity_blocked_item_count": sum(1 for item in items if item["rerun_guard_status"] == "BLOCKED_IDENTITY_RECONCILIATION_REQUIRED"),
        "missing_cycle_ledger_jsonl_total_count": sum(int(item["missing_cycle_ledger_jsonl_count"]) for item in items),
        "planned_staging_artifact_total_count": sum(int(item["planned_staging_artifact_count"]) for item in items),
        "candidate_current_evidence_usable_count": sum(1 for item in items if item["candidate_current_evidence_usable"]),
        "guard_status": "BLOCKED",
        "primary_blocker_code": MISSING_CYCLE_RERUN_GUARD_BLOCKER_CODE,
        "blocker_codes": sorted(blockers),
        "items": items,
        "operator_next_action": (
            "Stage bounded PAPER reruns only for READY items in a later executor patch; run recovery guard first for "
            "recovery-blocked items, then rebuild ledger rollup and rerun reconciliation."
        ),
        "actual_rerun_executed": False,
        "rerun_executor_created": False,
        "current_evidence_mutation_allowed": False,
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
        "guard_hash": "",
    }
    report["guard_hash"] = upbit_paper_missing_cycle_rerun_guard_hash(report)
    return report


def write_upbit_paper_missing_cycle_rerun_guard_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_missing_cycle_rerun_guard_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_missing_cycle_rerun_guard_report(report: dict[str, Any]) -> UpbitPaperMissingCycleRerunGuardValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "guard_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "guard_role",
        "source_repair_operator_queue_hash",
        "source_repair_operator_queue_status",
        "source_queue_item_count",
        "source_runtime_cycle_rerun_required_count",
        "source_recovery_guard_rerun_required_count",
        "guard_item_count",
        "rerun_ready_item_count",
        "recovery_guard_blocked_item_count",
        "identity_blocked_item_count",
        "missing_cycle_ledger_jsonl_total_count",
        "planned_staging_artifact_total_count",
        "candidate_current_evidence_usable_count",
        "guard_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "actual_rerun_executed",
        "rerun_executor_created",
        "current_evidence_mutation_allowed",
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
        "guard_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", f"missing cycle rerun guard missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_MISSING_CYCLE_RERUN_GUARD_SCHEMA_ID:
        return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("guard_hash") != upbit_paper_missing_cycle_rerun_guard_hash(report):
        return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperMissingCycleRerunGuardValidationResult("BLOCKED", "missing cycle rerun guard scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != MISSING_CYCLE_RERUN_GUARD_TRUTH_ROLE or report.get("guard_role") != MISSING_CYCLE_RERUN_GUARD_ROLE:
        return UpbitPaperMissingCycleRerunGuardValidationResult("BLOCKED", "missing cycle rerun guard cannot claim execution/live truth", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "actual_rerun_executed",
        "rerun_executor_created",
        "current_evidence_mutation_allowed",
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
        return UpbitPaperMissingCycleRerunGuardValidationResult("BLOCKED", "missing cycle rerun guard created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if report.get("guard_status") != "BLOCKED" or report.get("primary_blocker_code") != MISSING_CYCLE_RERUN_GUARD_BLOCKER_CODE:
        return UpbitPaperMissingCycleRerunGuardValidationResult("BLOCKED", "missing cycle rerun guard must remain blocked until a later executor and reconciliation pass", MISSING_CYCLE_RERUN_GUARD_BLOCKER_CODE)
    items = report.get("items")
    if not isinstance(items, list) or report.get("guard_item_count") != len(items):
        return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_runtime_cycle_rerun_required_count") != len(items):
        return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard source rerun count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected = {
        "rerun_ready_item_count": 0,
        "recovery_guard_blocked_item_count": 0,
        "identity_blocked_item_count": 0,
        "missing_cycle_ledger_jsonl_total_count": 0,
        "planned_staging_artifact_total_count": 0,
        "candidate_current_evidence_usable_count": 0,
    }
    session_id = str(report.get("session_id"))
    allowed_statuses = {
        "READY_FOR_BOUNDED_PAPER_RERUN_STAGING",
        "BLOCKED_RECOVERY_GUARD_REQUIRED",
        "BLOCKED_IDENTITY_RECONCILIATION_REQUIRED",
    }
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard item must be object", "SCHEMA_IDENTITY_MISMATCH")
        item_required = {
            "source_queue_priority_order",
            "replacement_loop_id",
            "replacement_path",
            "replacement_load_status",
            "replacement_path_scope_status",
            "safe_repair_lane",
            "requires_runtime_cycle_rerun",
            "requires_recovery_guard_rerun",
            "missing_cycle_ledger_jsonl_count",
            "missing_cycle_ledger_jsonl_paths",
            "missing_cycle_ids",
            "replacement_cycle_ids",
            "missing_cycle_identity_match",
            "missing_cycle_path_scope_status",
            "planned_staging_artifact_paths",
            "planned_staging_artifact_count",
            "planned_staging_path_scope_status",
            "rerun_guard_status",
            "rerun_guard_blocker_code",
            "next_action",
            "next_patch_staging_rerun_candidate_eligible",
            "current_ledger_jsonl_write_allowed",
            "latest_runtime_pointer_write_allowed",
            "persistent_loop_mutation_allowed",
            "source_delete_allowed",
            "candidate_current_evidence_usable",
            "requires_post_rerun_ledger_rollup",
            "requires_post_rerun_reconciliation",
            "live_permission_created",
            "blocking_codes",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", f"missing cycle rerun guard item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH")
        if not item.get("requires_runtime_cycle_rerun"):
            return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard item must require runtime rerun", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("rerun_guard_status") not in allowed_statuses:
            return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard item status invalid", "SCHEMA_IDENTITY_MISMATCH")
        if not _artifact_path_allowed(str(item.get("replacement_path") or ""), session_id):
            return UpbitPaperMissingCycleRerunGuardValidationResult("BLOCKED", "missing cycle rerun guard replacement path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        for path in item.get("missing_cycle_ledger_jsonl_paths") or []:
            if not isinstance(path, str) or not _artifact_path_allowed(path, session_id):
                return UpbitPaperMissingCycleRerunGuardValidationResult("BLOCKED", "missing cycle rerun guard missing ledger path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        planned_paths = item.get("planned_staging_artifact_paths")
        if not isinstance(planned_paths, list) or item.get("planned_staging_artifact_count") != len(planned_paths):
            return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard planned path count mismatch", "SCHEMA_IDENTITY_MISMATCH")
        for path in planned_paths:
            if not isinstance(path, str) or not _artifact_path_allowed(path, session_id) or "/rerun_candidates/" not in path.replace("\\", "/"):
                return UpbitPaperMissingCycleRerunGuardValidationResult("BLOCKED", "missing cycle rerun guard planned path escaped staging namespace", "SNAPSHOT_SCOPE_MISMATCH")
        missing_ids = item.get("missing_cycle_ids")
        replacement_ids = item.get("replacement_cycle_ids")
        if not isinstance(missing_ids, list) or len(missing_ids) != item.get("missing_cycle_ledger_jsonl_count"):
            return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard missing cycle id count mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if not isinstance(replacement_ids, list):
            return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard replacement cycle ids must be array", "SCHEMA_IDENTITY_MISMATCH")
        identity_match = bool(missing_ids) and all(cycle_id in replacement_ids for cycle_id in missing_ids)
        if item.get("missing_cycle_identity_match") != identity_match:
            return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard identity rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if (
            item.get("current_ledger_jsonl_write_allowed")
            or item.get("latest_runtime_pointer_write_allowed")
            or item.get("persistent_loop_mutation_allowed")
            or item.get("source_delete_allowed")
            or item.get("candidate_current_evidence_usable")
            or item.get("live_permission_created")
        ):
            return UpbitPaperMissingCycleRerunGuardValidationResult("BLOCKED", "missing cycle rerun guard item attempted mutation or live permission", "LIVE_FINAL_GUARD_FAILED")
        if not item.get("requires_post_rerun_ledger_rollup") or not item.get("requires_post_rerun_reconciliation"):
            return UpbitPaperMissingCycleRerunGuardValidationResult("BLOCKED", "missing cycle rerun guard must require post-rerun reconciliation", "RECONCILIATION_REQUIRED")
        if item.get("requires_recovery_guard_rerun"):
            if item.get("rerun_guard_status") != "BLOCKED_RECOVERY_GUARD_REQUIRED" or item.get("next_patch_staging_rerun_candidate_eligible"):
                return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "recovery-blocked item cannot be staging eligible", "SCHEMA_IDENTITY_MISMATCH")
        elif identity_match:
            if item.get("rerun_guard_status") != "READY_FOR_BOUNDED_PAPER_RERUN_STAGING" or not item.get("next_patch_staging_rerun_candidate_eligible"):
                return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "identity-matched item must be staging eligible", "SCHEMA_IDENTITY_MISMATCH")
        elif item.get("rerun_guard_status") != "BLOCKED_IDENTITY_RECONCILIATION_REQUIRED":
            return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "identity mismatch must block staging", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("next_patch_staging_rerun_candidate_eligible"):
            expected["rerun_ready_item_count"] += 1
        if item.get("requires_recovery_guard_rerun"):
            expected["recovery_guard_blocked_item_count"] += 1
        if item.get("rerun_guard_status") == "BLOCKED_IDENTITY_RECONCILIATION_REQUIRED":
            expected["identity_blocked_item_count"] += 1
        expected["missing_cycle_ledger_jsonl_total_count"] += int(item.get("missing_cycle_ledger_jsonl_count") or 0)
        expected["planned_staging_artifact_total_count"] += int(item.get("planned_staging_artifact_count") or 0)
        if item.get("candidate_current_evidence_usable"):
            expected["candidate_current_evidence_usable_count"] += 1
    for field, value in expected.items():
        if report.get(field) != value:
            return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", f"missing cycle rerun guard count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if MISSING_CYCLE_RERUN_GUARD_BLOCKER_CODE not in set(report.get("blocker_codes") or []):
        return UpbitPaperMissingCycleRerunGuardValidationResult("FAIL", "missing cycle rerun guard missing primary blocker", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("candidate_current_evidence_usable_count") != 0:
        return UpbitPaperMissingCycleRerunGuardValidationResult("BLOCKED", "missing cycle rerun guard exposed current evidence usability", "LIVE_FINAL_GUARD_FAILED")
    return UpbitPaperMissingCycleRerunGuardValidationResult(
        "PASS",
        "Upbit PAPER missing cycle rerun guard separates staging-eligible reruns from recovery-blocked work without mutating evidence",
        None,
    )
