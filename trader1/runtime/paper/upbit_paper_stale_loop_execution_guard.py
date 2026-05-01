from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import (
    validate_upbit_paper_stale_loop_regeneration_plan,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_REGENERATION_EXECUTION_GUARD_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_regeneration_execution_guard.v1"
)
EXECUTION_GUARD_ROLE = "PAPER_RUNTIME_STALE_LOOP_REGENERATION_EXECUTION_GUARD_NOT_EXECUTION"
MAX_REGENERATION_ITEM_COUNT = 20


@dataclass(frozen=True)
class UpbitPaperStaleLoopExecutionGuardValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def stale_loop_execution_guard_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("guard_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return path.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "live" not in parts


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return root.resolve().joinpath(*parts)


def _safe_file_hash(path: Path) -> str | None:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        return None


def _build_guard_item(*, root: Path, session_id: str, item: dict[str, Any]) -> dict[str, Any]:
    source_path = str(item.get("source_path"))
    replacement_path = item.get("planned_replacement_path")
    expected_hash = item.get("source_hash")
    source_absolute = _rooted(root, source_path)
    replacement_absolute = _rooted(root, str(replacement_path)) if isinstance(replacement_path, str) else None
    actual_hash = _safe_file_hash(source_absolute)
    source_allowed = _artifact_path_allowed(source_path, session_id)
    replacement_allowed = isinstance(replacement_path, str) and _artifact_path_allowed(replacement_path, session_id)
    source_exists = source_absolute.exists()
    replacement_exists = bool(replacement_absolute and replacement_absolute.exists())
    replacement_parent_exists = bool(replacement_absolute and replacement_absolute.parent.exists())
    blocker_code = None
    if item.get("planned_action") != "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT":
        blocker_code = "STALE_LOOP_REGENERATION_OPERATOR_REVIEW_REQUIRED"
    elif item.get("source_evidence_usable_current"):
        blocker_code = "STALE_LOOP_REGENERATION_REQUIRED"
    elif item.get("overwrite_source_allowed") or item.get("delete_source_allowed") or item.get("automatic_live_or_order_allowed"):
        blocker_code = "LIVE_FINAL_GUARD_FAILED"
    elif item.get("live_order_ready") or item.get("live_order_allowed") or item.get("can_live_trade") or item.get("scale_up_allowed"):
        blocker_code = "LIVE_FINAL_GUARD_FAILED"
    elif not source_allowed or not replacement_allowed:
        blocker_code = "SNAPSHOT_SCOPE_MISMATCH"
    elif not source_exists or actual_hash is None:
        blocker_code = "STALE_LOOP_SOURCE_MISSING"
    elif expected_hash and actual_hash != expected_hash:
        blocker_code = "STALE_LOOP_SOURCE_HASH_MISMATCH"
    elif replacement_exists:
        blocker_code = "STALE_LOOP_REPLACEMENT_ALREADY_EXISTS"
    elif not replacement_parent_exists:
        blocker_code = "STALE_LOOP_REPLACEMENT_PARENT_MISSING"
    elif replacement_path == source_path:
        blocker_code = "LIVE_FINAL_GUARD_FAILED"
    return {
        "source_path": source_path,
        "source_hash_expected": expected_hash,
        "source_hash_actual": actual_hash,
        "source_hash_match": bool(expected_hash and actual_hash == expected_hash),
        "source_path_scope_status": "MATCH" if source_allowed else "MISMATCH",
        "source_exists": source_exists,
        "planned_replacement_loop_id": item.get("planned_replacement_loop_id"),
        "planned_replacement_path": replacement_path,
        "replacement_path_scope_status": "MATCH" if replacement_allowed else "MISMATCH",
        "replacement_path_exists": replacement_exists,
        "replacement_parent_exists": replacement_parent_exists,
        "replacement_write_mode": "CREATE_NEW_ONLY",
        "planned_action": item.get("planned_action"),
        "guard_item_status": "PASS" if blocker_code is None else "BLOCKED",
        "blocker_code": blocker_code,
        "delete_source_allowed": False,
        "overwrite_source_allowed": False,
        "execution_performed": False,
        "actual_long_run_evidence_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_stale_loop_execution_guard(
    *,
    root: Path,
    plan: dict[str, Any],
    guard_id: str = "upbit-paper-stale-loop-regeneration-execution-guard",
) -> dict[str, Any]:
    root = Path(root).resolve()
    plan_result = validate_upbit_paper_stale_loop_regeneration_plan(plan)
    session_id = str(plan.get("session_id", "UNKNOWN"))
    items = [
        _build_guard_item(root=root, session_id=session_id, item=item)
        for item in plan.get("items", [])
        if isinstance(item, dict) and item.get("planned_action") == "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT"
    ]
    blockers: list[str] = []
    if plan_result.status != "PASS":
        blockers.append(plan_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    if plan.get("plan_status") != "READY_FOR_SAFE_PAPER_REGENERATION":
        blockers.append(plan.get("primary_blocker_code") or "STALE_LOOP_REGENERATION_REQUIRED")
    if plan.get("regeneration_item_count", 0) < 1:
        blockers.append("STALE_LOOP_REGENERATION_REQUIRED")
    if plan.get("regeneration_item_count", 0) > MAX_REGENERATION_ITEM_COUNT:
        blockers.append("RUNTIME_BUDGET_EXCEEDED")
    if plan.get("operator_review_item_count") or plan.get("duplicate_replacement_path_count") or plan.get("overwrite_or_delete_count"):
        blockers.append(plan.get("primary_blocker_code") or "STALE_LOOP_REGENERATION_REQUIRED")
    for field in (
        "automatic_regeneration_allowed",
        "operator_confirmation_required_before_execution",
        "delete_source_allowed",
        "overwrite_source_allowed",
        "actual_regeneration_performed",
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
    ):
        if plan.get(field):
            blockers.append("LIVE_FINAL_GUARD_FAILED")
    blockers.extend(item["blocker_code"] for item in items if item.get("blocker_code"))
    duplicate_replacement_paths = len([item.get("planned_replacement_path") for item in items]) - len(
        {item.get("planned_replacement_path") for item in items}
    )
    if duplicate_replacement_paths:
        blockers.append("STALE_LOOP_REPLACEMENT_PATH_COLLISION")
    unique_blockers = sorted({str(blocker) for blocker in blockers if blocker})
    guard_status = "PASS" if not unique_blockers else "BLOCKED"
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_REGENERATION_EXECUTION_GUARD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "guard_id": guard_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "guard_role": EXECUTION_GUARD_ROLE,
        "source_plan_hash": plan.get("plan_hash"),
        "source_plan_status": plan.get("plan_status"),
        "planned_regeneration_item_count": len(items),
        "operator_review_item_count": int(plan.get("operator_review_item_count") or 0),
        "duplicate_replacement_path_count": duplicate_replacement_paths,
        "replacement_existing_count": sum(1 for item in items if item["replacement_path_exists"]),
        "source_hash_mismatch_count": sum(1 for item in items if not item["source_hash_match"]),
        "source_missing_count": sum(1 for item in items if not item["source_exists"]),
        "guard_status": guard_status,
        "primary_blocker_code": unique_blockers[0] if unique_blockers else None,
        "blocker_codes": unique_blockers,
        "paper_regeneration_preconditions_passed": guard_status == "PASS",
        "separate_safe_executor_required": True,
        "replacement_write_mode": "CREATE_NEW_ONLY",
        "source_retention_required": True,
        "items": items,
        "delete_source_allowed": False,
        "overwrite_source_allowed": False,
        "execution_performed": False,
        "actual_regeneration_performed": False,
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
    report["guard_hash"] = stale_loop_execution_guard_hash(report)
    return report


def write_upbit_paper_stale_loop_execution_guard(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(root, str(report["session_id"])) / "paper_runtime" / "upbit_paper_stale_loop_regeneration_execution_guard.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_execution_guard(report: dict[str, Any]) -> UpbitPaperStaleLoopExecutionGuardValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "guard_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "guard_role",
        "source_plan_hash",
        "source_plan_status",
        "planned_regeneration_item_count",
        "operator_review_item_count",
        "duplicate_replacement_path_count",
        "replacement_existing_count",
        "source_hash_mismatch_count",
        "source_missing_count",
        "guard_status",
        "primary_blocker_code",
        "blocker_codes",
        "paper_regeneration_preconditions_passed",
        "separate_safe_executor_required",
        "replacement_write_mode",
        "source_retention_required",
        "items",
        "delete_source_allowed",
        "overwrite_source_allowed",
        "execution_performed",
        "actual_regeneration_performed",
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
        return UpbitPaperStaleLoopExecutionGuardValidationResult("FAIL", f"execution guard missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_REGENERATION_EXECUTION_GUARD_SCHEMA_ID:
        return UpbitPaperStaleLoopExecutionGuardValidationResult("FAIL", "execution guard schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("guard_hash") != stale_loop_execution_guard_hash(report):
        return UpbitPaperStaleLoopExecutionGuardValidationResult("FAIL", "execution guard hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopExecutionGuardValidationResult("BLOCKED", "execution guard scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("guard_role") != EXECUTION_GUARD_ROLE:
        return UpbitPaperStaleLoopExecutionGuardValidationResult("BLOCKED", "execution guard cannot claim execution authority", "LIVE_FINAL_GUARD_FAILED")
    forbidden_fields = (
        "delete_source_allowed",
        "overwrite_source_allowed",
        "execution_performed",
        "actual_regeneration_performed",
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
    if any(report.get(field) for field in forbidden_fields):
        return UpbitPaperStaleLoopExecutionGuardValidationResult("BLOCKED", "execution guard created forbidden execution, deletion, live/order, long-run, promotion, or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("replacement_write_mode") != "CREATE_NEW_ONLY" or report.get("source_retention_required") is not True or report.get("separate_safe_executor_required") is not True:
        return UpbitPaperStaleLoopExecutionGuardValidationResult("BLOCKED", "execution guard must require source retention, create-new writes, and separate executor", "LIVE_FINAL_GUARD_FAILED")
    items = report.get("items")
    if not isinstance(items, list) or report.get("planned_regeneration_item_count") != len(items):
        return UpbitPaperStaleLoopExecutionGuardValidationResult("FAIL", "execution guard item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    item_blockers: list[str] = []
    replacement_paths: list[str] = []
    source_missing_count = 0
    source_hash_mismatch_count = 0
    replacement_existing_count = 0
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopExecutionGuardValidationResult("FAIL", "execution guard item must be object", "SCHEMA_IDENTITY_MISMATCH")
        item_required = {
            "source_path",
            "source_hash_expected",
            "source_hash_actual",
            "source_hash_match",
            "source_path_scope_status",
            "source_exists",
            "planned_replacement_loop_id",
            "planned_replacement_path",
            "replacement_path_scope_status",
            "replacement_path_exists",
            "replacement_parent_exists",
            "replacement_write_mode",
            "planned_action",
            "guard_item_status",
            "blocker_code",
            "delete_source_allowed",
            "overwrite_source_allowed",
            "execution_performed",
            "actual_long_run_evidence_created",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopExecutionGuardValidationResult("FAIL", f"execution guard item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("delete_source_allowed") or item.get("overwrite_source_allowed") or item.get("execution_performed") or item.get("actual_long_run_evidence_created"):
            return UpbitPaperStaleLoopExecutionGuardValidationResult("BLOCKED", "execution guard item created execution, delete, overwrite, or long-run evidence", "LIVE_FINAL_GUARD_FAILED")
        if item.get("live_order_ready") or item.get("live_order_allowed") or item.get("can_live_trade") or item.get("scale_up_allowed"):
            return UpbitPaperStaleLoopExecutionGuardValidationResult("BLOCKED", "execution guard item created live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
        if item.get("source_path_scope_status") != "MATCH" or item.get("replacement_path_scope_status") != "MATCH":
            item_blockers.append("SNAPSHOT_SCOPE_MISMATCH")
        if item.get("replacement_write_mode") != "CREATE_NEW_ONLY":
            item_blockers.append("LIVE_FINAL_GUARD_FAILED")
        if not item.get("source_exists"):
            source_missing_count += 1
            item_blockers.append("STALE_LOOP_SOURCE_MISSING")
        if not item.get("source_hash_match"):
            source_hash_mismatch_count += 1
            item_blockers.append("STALE_LOOP_SOURCE_HASH_MISMATCH")
        if item.get("replacement_path_exists"):
            replacement_existing_count += 1
            item_blockers.append("STALE_LOOP_REPLACEMENT_ALREADY_EXISTS")
        if not item.get("replacement_parent_exists"):
            item_blockers.append("STALE_LOOP_REPLACEMENT_PARENT_MISSING")
        if item.get("blocker_code"):
            item_blockers.append(str(item["blocker_code"]))
        replacement_paths.append(str(item.get("planned_replacement_path")))
    duplicate_replacement_count = len(replacement_paths) - len(set(replacement_paths))
    if (
        report.get("source_missing_count") != source_missing_count
        or report.get("source_hash_mismatch_count") != source_hash_mismatch_count
        or report.get("replacement_existing_count") != replacement_existing_count
        or report.get("duplicate_replacement_path_count") != duplicate_replacement_count
    ):
        return UpbitPaperStaleLoopExecutionGuardValidationResult("FAIL", "execution guard rollup count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    unique_blockers = sorted({str(blocker) for blocker in [*item_blockers, *report.get("blocker_codes", [])] if blocker})
    if unique_blockers:
        if report.get("guard_status") != "BLOCKED" or not report.get("primary_blocker_code") or report.get("paper_regeneration_preconditions_passed"):
            return UpbitPaperStaleLoopExecutionGuardValidationResult("BLOCKED", "blocked execution guard cannot expose passed preconditions", unique_blockers[0])
    else:
        if report.get("guard_status") != "PASS" or report.get("primary_blocker_code") is not None or not report.get("paper_regeneration_preconditions_passed"):
            return UpbitPaperStaleLoopExecutionGuardValidationResult("FAIL", "clean execution guard status mismatch", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperStaleLoopExecutionGuardValidationResult("PASS", "Upbit PAPER stale loop execution guard is source-preserving, create-new-only, and live-blocked", None)
