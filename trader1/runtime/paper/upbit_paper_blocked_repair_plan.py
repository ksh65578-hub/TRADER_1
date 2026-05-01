from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_stale_loop_post_regeneration_reconciliation import (
    POST_REGENERATION_RECONCILIATION_BLOCKER_CODE,
    validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_BLOCKED_REPAIR_PLAN_SCHEMA_ID = "trader1.upbit_paper_blocked_repair_plan_report.v1"
BLOCKED_REPAIR_PLAN_ROLE = "PAPER_RUNTIME_BLOCKED_REPAIR_PLAN_NOT_EVIDENCE"
BLOCKED_REPAIR_PLAN_BLOCKER_CODE = "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION"


@dataclass(frozen=True)
class UpbitPaperBlockedRepairPlanValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_blocked_repair_plan_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("repair_plan_hash", None)
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


def _cycle_ledger_path(root: Path, session_id: str, cycle_id: str) -> Path:
    return _runtime_base(root, session_id) / "ledger" / "cycles" / f"{cycle_id}.paper_ledger_events.jsonl"


def _repair_lane(item: dict[str, Any], missing_cycle_ledger_count: int) -> str:
    reasons = set(item.get("blocked_repair_reason_codes") or [])
    if item.get("unsafe_live_or_order_flag_detected"):
        return "QUARANTINE_OPERATOR_REVIEW"
    if reasons & {"RECOVERY_GUARD_BLOCKED", "PARTIAL_WRITE_RECOVERY_REQUIRED", "PAPER_RUNTIME_RESUME_BLOCKED"}:
        return "RECOVERY_GUARD_THEN_LEDGER_ROLLUP"
    if missing_cycle_ledger_count:
        return "RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP"
    if "LEDGER_ROLLUP_BLOCKED" in reasons:
        return "LEDGER_ROLLUP_REBUILD_READY"
    return "RERUN_POST_REGENERATION_RECONCILIATION"


def _repair_steps(lane: str) -> list[dict[str, Any]]:
    steps_by_lane = {
        "LEDGER_ROLLUP_REBUILD_READY": [
            ("VERIFY_REPLACEMENT_LOOP_HASH", "READY", "replacement loop hash matches post-regeneration plan"),
            ("REBUILD_LEDGER_ROLLUP_FROM_EXISTING_CYCLE_JSONL", "READY", "all referenced PAPER cycle ledger JSONL files are present"),
            ("RERUN_POST_REGENERATION_RECONCILIATION", "READY", "replacement remains blocked until validator-backed reconciliation passes"),
        ],
        "RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP": [
            ("RERUN_MISSING_PAPER_RUNTIME_CYCLES", "BLOCKED", "one or more referenced PAPER cycle ledger JSONL files are missing"),
            ("REBUILD_LEDGER_ROLLUP_FROM_CYCLE_JSONL", "BLOCKED", "ledger rollup cannot be rebuilt until missing cycle ledgers exist"),
            ("RERUN_POST_REGENERATION_RECONCILIATION", "BLOCKED", "replacement remains excluded from current evidence"),
        ],
        "RECOVERY_GUARD_THEN_LEDGER_ROLLUP": [
            ("RERUN_RECOVERY_GUARD", "BLOCKED", "partial-write or safe-resume blocker must be cleared first"),
            ("RERUN_MISSING_PAPER_RUNTIME_CYCLES", "BLOCKED", "cycle ledgers must be present before ledger rollup rebuild"),
            ("REBUILD_LEDGER_ROLLUP_FROM_CYCLE_JSONL", "BLOCKED", "ledger rollup cannot be rebuilt until recovery and cycle ledgers pass"),
            ("RERUN_POST_REGENERATION_RECONCILIATION", "BLOCKED", "replacement remains excluded from current evidence"),
        ],
        "QUARANTINE_OPERATOR_REVIEW": [
            ("QUARANTINE_OPERATOR_REVIEW", "BLOCKED", "unsafe flag or scope mismatch requires manual audit before any repair"),
        ],
        "RERUN_POST_REGENERATION_RECONCILIATION": [
            ("RERUN_POST_REGENERATION_RECONCILIATION", "BLOCKED", "blocked reason is not specific enough for an automatic repair lane"),
        ],
    }
    return [
        {
            "step_order": index,
            "action_code": action,
            "action_status": status,
            "evidence_required": evidence,
            "mutates_current_evidence": False,
            "live_permission_created": False,
        }
        for index, (action, status, evidence) in enumerate(steps_by_lane[lane], start=1)
    ]


def _build_plan_item(*, root: Path, session_id: str, post_item: dict[str, Any]) -> dict[str, Any]:
    replacement_path = str(post_item.get("replacement_path") or "")
    replacement, load_error = _safe_load_json(_rooted(root, replacement_path))
    cycle_ids = [
        str(cycle.get("cycle_id"))
        for cycle in (replacement or {}).get("cycle_results", [])
        if isinstance(cycle, dict) and isinstance(cycle.get("cycle_id"), str)
    ]
    cycle_ledger_paths = [_cycle_ledger_path(root, session_id, cycle_id) for cycle_id in cycle_ids]
    existing_cycle_ledger_paths = [path for path in cycle_ledger_paths if path.exists()]
    missing_cycle_ledger_paths = [path for path in cycle_ledger_paths if not path.exists()]
    ledger_rollup_path = str((replacement or {}).get("paper_ledger_rollup_path") or "")
    ledger_rollup_exists = bool(ledger_rollup_path and _rooted(root, ledger_rollup_path).exists())
    lane = _repair_lane(post_item, len(missing_cycle_ledger_paths))
    return {
        "replacement_loop_id": post_item.get("replacement_loop_id"),
        "replacement_path": replacement_path,
        "replacement_load_status": "PASS" if replacement is not None else str(load_error or "UNKNOWN"),
        "replacement_path_scope_status": "MATCH" if _artifact_path_allowed(replacement_path, session_id) else "MISMATCH",
        "blocked_repair_reason_codes": sorted(str(code) for code in post_item.get("blocked_repair_reason_codes") or []),
        "ledger_reconciliation_status": post_item.get("ledger_reconciliation_status"),
        "recovery_reconciliation_status": post_item.get("recovery_reconciliation_status"),
        "cycle_reconciliation_status": post_item.get("cycle_reconciliation_status"),
        "safe_repair_lane": lane,
        "cycle_count": len(cycle_ids),
        "cycle_ledger_jsonl_present_count": len(existing_cycle_ledger_paths),
        "cycle_ledger_jsonl_missing_count": len(missing_cycle_ledger_paths),
        "cycle_ledger_jsonl_missing_paths": [_relative_posix(path, root) for path in missing_cycle_ledger_paths],
        "paper_ledger_rollup_path": ledger_rollup_path,
        "paper_ledger_rollup_artifact_exists": ledger_rollup_exists,
        "can_rebuild_ledger_rollup_without_rerun": lane == "LEDGER_ROLLUP_REBUILD_READY",
        "requires_recovery_guard_rerun": lane == "RECOVERY_GUARD_THEN_LEDGER_ROLLUP",
        "requires_runtime_cycle_rerun": lane in {"RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP", "RECOVERY_GUARD_THEN_LEDGER_ROLLUP"},
        "current_evidence_mutation_allowed": False,
        "source_delete_allowed": False,
        "live_permission_created": False,
        "repair_steps": _repair_steps(lane),
    }


def _lane_counts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        lane = str(item["safe_repair_lane"])
        counts[lane] = counts.get(lane, 0) + 1
    return [{"safe_repair_lane": lane, "count": counts[lane]} for lane in sorted(counts)]


def build_upbit_paper_blocked_repair_plan_report(
    *,
    root: Path,
    post_reconciliation_report: dict[str, Any],
    source_report_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_post_regeneration_reconciliation_report.json",
    repair_plan_id: str = "upbit-paper-blocked-repair-plan",
) -> dict[str, Any]:
    root = Path(root).resolve()
    validation = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(post_reconciliation_report)
    session_id = str(post_reconciliation_report.get("session_id", "UNKNOWN"))
    blocked_source_items = [
        item
        for item in post_reconciliation_report.get("items", [])
        if isinstance(item, dict) and item.get("classification") == "REGENERATED_CURRENT_BLOCKED_RECONCILIATION_REQUIRED"
    ]
    items = [
        _build_plan_item(root=root, session_id=session_id, post_item=item)
        for item in blocked_source_items
    ]
    lane_counts = _lane_counts(items)
    blockers = [BLOCKED_REPAIR_PLAN_BLOCKER_CODE] if items else []
    if validation.status != "PASS":
        blockers.append(validation.blocker_code or POST_REGENERATION_RECONCILIATION_BLOCKER_CODE)
    if any(item["replacement_path_scope_status"] != "MATCH" for item in items):
        blockers.append("SNAPSHOT_SCOPE_MISMATCH")
    unique_blockers = sorted(set(blockers))
    report = {
        "schema_id": UPBIT_PAPER_BLOCKED_REPAIR_PLAN_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "repair_plan_id": repair_plan_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": "paper_runtime_blocked_repair_plan_truth",
        "repair_plan_role": BLOCKED_REPAIR_PLAN_ROLE,
        "source_report_path": source_report_path,
        "source_post_reconciliation_hash": post_reconciliation_report.get("post_reconciliation_hash"),
        "source_post_reconciliation_status": post_reconciliation_report.get("post_reconciliation_status"),
        "source_blocked_reconciliation_count": int(post_reconciliation_report.get("regenerated_current_blocked_reconciliation_count") or 0),
        "repair_item_count": len(items),
        "repair_lane_counts": lane_counts,
        "ledger_rollup_rebuild_ready_count": sum(1 for item in items if item["safe_repair_lane"] == "LEDGER_ROLLUP_REBUILD_READY"),
        "runtime_cycle_rerun_required_count": sum(1 for item in items if item["requires_runtime_cycle_rerun"]),
        "recovery_guard_rerun_required_count": sum(1 for item in items if item["requires_recovery_guard_rerun"]),
        "missing_cycle_ledger_jsonl_item_count": sum(1 for item in items if item["cycle_ledger_jsonl_missing_count"] > 0),
        "missing_cycle_ledger_jsonl_total_count": sum(int(item["cycle_ledger_jsonl_missing_count"]) for item in items),
        "missing_paper_ledger_rollup_artifact_count": sum(1 for item in items if not item["paper_ledger_rollup_artifact_exists"]),
        "repair_plan_status": "BLOCKED" if unique_blockers else "PASS",
        "primary_blocker_code": unique_blockers[0] if unique_blockers else None,
        "blocker_codes": unique_blockers,
        "items": items,
        "operator_next_action": (
            "Repair only the LEDGER_ROLLUP_REBUILD_READY item first; rerun missing PAPER cycles before using other blocked replacements."
            if items
            else "No blocked regenerated replacements require repair planning."
        ),
        "current_evidence_mutation_allowed": False,
        "generated_artifact_mutation_allowed": False,
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
        "repair_plan_hash": "",
    }
    report["repair_plan_hash"] = upbit_paper_blocked_repair_plan_hash(report)
    return report


def write_upbit_paper_blocked_repair_plan_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(root, str(report["session_id"])) / "paper_runtime" / "upbit_paper_blocked_repair_plan_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_blocked_repair_plan_report(report: dict[str, Any]) -> UpbitPaperBlockedRepairPlanValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "repair_plan_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "repair_plan_role",
        "source_report_path",
        "source_post_reconciliation_hash",
        "source_post_reconciliation_status",
        "source_blocked_reconciliation_count",
        "repair_item_count",
        "repair_lane_counts",
        "ledger_rollup_rebuild_ready_count",
        "runtime_cycle_rerun_required_count",
        "recovery_guard_rerun_required_count",
        "missing_cycle_ledger_jsonl_item_count",
        "missing_cycle_ledger_jsonl_total_count",
        "missing_paper_ledger_rollup_artifact_count",
        "repair_plan_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "current_evidence_mutation_allowed",
        "generated_artifact_mutation_allowed",
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
        "repair_plan_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperBlockedRepairPlanValidationResult("FAIL", f"blocked repair plan missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_BLOCKED_REPAIR_PLAN_SCHEMA_ID:
        return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "blocked repair plan schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("repair_plan_hash") != upbit_paper_blocked_repair_plan_hash(report):
        return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "blocked repair plan hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperBlockedRepairPlanValidationResult("BLOCKED", "blocked repair plan scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != "paper_runtime_blocked_repair_plan_truth" or report.get("repair_plan_role") != BLOCKED_REPAIR_PLAN_ROLE:
        return UpbitPaperBlockedRepairPlanValidationResult("BLOCKED", "blocked repair plan cannot claim execution/live truth", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "current_evidence_mutation_allowed",
        "generated_artifact_mutation_allowed",
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
        return UpbitPaperBlockedRepairPlanValidationResult("BLOCKED", "blocked repair plan created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    items = report.get("items")
    if not isinstance(items, list) or report.get("repair_item_count") != len(items):
        return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "blocked repair plan item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_lane_counts = _lane_counts(items)
    if report.get("repair_lane_counts") != expected_lane_counts:
        return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "blocked repair plan lane rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_blocked_reconciliation_count") != len(items):
        return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "blocked repair plan source count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    counts = {
        "ledger_rollup_rebuild_ready_count": sum(1 for item in items if item.get("safe_repair_lane") == "LEDGER_ROLLUP_REBUILD_READY"),
        "runtime_cycle_rerun_required_count": sum(1 for item in items if item.get("requires_runtime_cycle_rerun")),
        "recovery_guard_rerun_required_count": sum(1 for item in items if item.get("requires_recovery_guard_rerun")),
        "missing_cycle_ledger_jsonl_item_count": sum(1 for item in items if item.get("cycle_ledger_jsonl_missing_count", 0) > 0),
        "missing_cycle_ledger_jsonl_total_count": sum(int(item.get("cycle_ledger_jsonl_missing_count", 0)) for item in items),
        "missing_paper_ledger_rollup_artifact_count": sum(1 for item in items if not item.get("paper_ledger_rollup_artifact_exists")),
    }
    for field, expected in counts.items():
        if report.get(field) != expected:
            return UpbitPaperBlockedRepairPlanValidationResult("FAIL", f"blocked repair plan count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH")
    session_id = str(report.get("session_id"))
    valid_lanes = {
        "LEDGER_ROLLUP_REBUILD_READY",
        "RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP",
        "RECOVERY_GUARD_THEN_LEDGER_ROLLUP",
        "QUARANTINE_OPERATOR_REVIEW",
        "RERUN_POST_REGENERATION_RECONCILIATION",
    }
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "blocked repair plan item must be object", "SCHEMA_IDENTITY_MISMATCH")
        lane = item.get("safe_repair_lane")
        if lane not in valid_lanes:
            return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "blocked repair plan lane invalid", "SCHEMA_IDENTITY_MISMATCH")
        if not _artifact_path_allowed(str(item.get("replacement_path")), session_id):
            return UpbitPaperBlockedRepairPlanValidationResult("BLOCKED", "blocked repair plan replacement path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if item.get("current_evidence_mutation_allowed") or item.get("source_delete_allowed") or item.get("live_permission_created"):
            return UpbitPaperBlockedRepairPlanValidationResult("BLOCKED", "blocked repair plan item created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
        steps = item.get("repair_steps")
        if not isinstance(steps, list) or not steps:
            return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "blocked repair plan item lacks repair steps", "SCHEMA_IDENTITY_MISMATCH")
        if lane == "LEDGER_ROLLUP_REBUILD_READY" and item.get("cycle_ledger_jsonl_missing_count") != 0:
            return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "ledger rebuild ready item cannot have missing cycle ledgers", "SCHEMA_IDENTITY_MISMATCH")
        if lane == "RECOVERY_GUARD_THEN_LEDGER_ROLLUP" and not item.get("requires_recovery_guard_rerun"):
            return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "recovery lane must require recovery guard rerun", "SCHEMA_IDENTITY_MISMATCH")
        for step in steps:
            if step.get("mutates_current_evidence") or step.get("live_permission_created"):
                return UpbitPaperBlockedRepairPlanValidationResult("BLOCKED", "blocked repair step attempted evidence mutation or live permission", "LIVE_FINAL_GUARD_FAILED")
    expected_blockers = [BLOCKED_REPAIR_PLAN_BLOCKER_CODE] if items else []
    if set(report.get("blocker_codes") or []) != set(expected_blockers):
        return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "blocked repair plan blocker rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if items:
        if report.get("repair_plan_status") != "BLOCKED" or report.get("primary_blocker_code") != BLOCKED_REPAIR_PLAN_BLOCKER_CODE:
            return UpbitPaperBlockedRepairPlanValidationResult("BLOCKED", "blocked repairs must keep plan blocked until operator reconciliation", BLOCKED_REPAIR_PLAN_BLOCKER_CODE)
    elif report.get("repair_plan_status") != "PASS" or report.get("primary_blocker_code") is not None:
        return UpbitPaperBlockedRepairPlanValidationResult("FAIL", "empty blocked repair plan status mismatch", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperBlockedRepairPlanValidationResult("PASS", "Upbit PAPER blocked repair plan is scoped, operator-visible, and live-blocked", None)
