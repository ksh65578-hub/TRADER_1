from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.core.ledger.paper_ledger import validate_upbit_paper_ledger
from trader1.runtime.paper.upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck import (
    validate_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_ledger_rollup_regeneration_plan import (
    validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_ledger_input_scope_repair_plan_report.v1"
)
STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN_TRUTH_ROLE = (
    "paper_runtime_stale_loop_ledger_input_scope_repair_plan_truth"
)
STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN_NO_EXECUTION"
)
LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE = "LEDGER_INPUT_SCOPE_REPAIR_PLAN_ONLY_EXECUTION_REQUIRED"
LEDGER_INPUT_SCOPE_REPAIR_INPUT_MISSING_BLOCKER_CODE = "LEDGER_INPUT_SCOPE_REPAIR_INPUT_MISSING"


@dataclass(frozen=True)
class UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def upbit_paper_stale_loop_ledger_input_scope_repair_plan_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("ledger_input_scope_repair_plan_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _runtime_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/")
        and ".." not in normalized.split("/")
        and "/live/" not in normalized
    )


def _repair_candidate_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    prefix = (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        "ledger_input_scope_repair_candidates/"
    )
    return normalized.startswith(prefix) and ".." not in normalized.split("/") and "/live/" not in normalized


def _safe_read_jsonl(path: Path) -> tuple[list[dict[str, Any]] | None, str, str | None]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None, "MISSING", None
    except OSError:
        return None, "UNREADABLE", None
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return None, "INVALID_UTF8", _sha256_bytes(raw)
    records: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            return None, "INVALID_JSON", _sha256_bytes(raw)
        if not isinstance(value, dict):
            return None, "NOT_OBJECT", _sha256_bytes(raw)
        records.append(value)
    return records, "PASS", _sha256_bytes(raw)


def _plan_item_by_loop(regeneration_plan_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for item in regeneration_plan_report.get("items", []):
        if isinstance(item, dict) and isinstance(item.get("replacement_loop_id"), str):
            items[item["replacement_loop_id"]] = item
    return items


def _mirror_root_path(session_id: str, replacement_loop_id: str) -> str:
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        f"ledger_input_scope_repair_candidates/{replacement_loop_id}/isolated_root"
    )


def _planned_mirror_relative_ledger_path(session_id: str, cycle_id: str) -> str:
    return f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/cycles/{cycle_id}.paper_ledger_events.jsonl"


def _planned_rollup_candidate_path(session_id: str, replacement_loop_id: str) -> str:
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        f"ledger_input_scope_repair_candidates/{replacement_loop_id}/{replacement_loop_id}.paper_ledger_rollup_report.json"
    )


def _in_current_canonical_scope(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/cycles/")


def _build_cycle(*, root: Path, session_id: str, replacement_loop_id: str, cycle: dict[str, Any]) -> dict[str, Any]:
    cycle_id = str(cycle.get("cycle_id") or "UNKNOWN")
    final_decision = cycle.get("final_decision")
    source_path = str(cycle.get("selected_ledger_path") or "")
    records, load_status, source_hash = _safe_read_jsonl(_rooted(root, source_path))
    if records is None:
        ledger_status = load_status
        ledger_blocker = LEDGER_INPUT_SCOPE_REPAIR_INPUT_MISSING_BLOCKER_CODE
        ledger_message = f"source ledger load status: {load_status}"
        event_count = 0
    elif not records and final_decision != "ENTER_LONG":
        ledger_status = "PASS"
        ledger_blocker = None
        ledger_message = "no-trade cycle may have empty ledger JSONL"
        event_count = 0
    else:
        ledger_status, ledger_blocker, ledger_message = validate_upbit_paper_ledger(records)
        event_count = len(records)
    mirror_root = _mirror_root_path(session_id, replacement_loop_id)
    mirror_relative = _planned_mirror_relative_ledger_path(session_id, cycle_id)
    planned_mirror_path = f"{mirror_root}/{mirror_relative}"
    source_in_current_canonical_scope = _in_current_canonical_scope(source_path, session_id)
    repair_ready = (
        load_status == "PASS"
        and ledger_status == "PASS"
        and not source_in_current_canonical_scope
        and bool(source_hash)
    )
    blocker_codes = {LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE}
    if not repair_ready:
        blocker_codes.add(ledger_blocker or LEDGER_INPUT_SCOPE_REPAIR_INPUT_MISSING_BLOCKER_CODE)
    return {
        "cycle_id": cycle_id,
        "final_decision": final_decision,
        "source_selected_ledger_path": source_path,
        "source_selected_ledger_path_exists": records is not None,
        "source_selected_ledger_hash": source_hash,
        "source_ledger_load_status": load_status,
        "source_ledger_event_count": event_count,
        "source_ledger_validator_status": ledger_status,
        "source_ledger_validator_blocker_code": ledger_blocker,
        "source_ledger_validator_message": ledger_message,
        "source_ledger_in_current_canonical_scope": source_in_current_canonical_scope,
        "planned_isolated_root_path": mirror_root,
        "planned_mirror_relative_ledger_path": mirror_relative,
        "planned_mirror_ledger_path": planned_mirror_path,
        "planned_mirror_ledger_path_allowed": _repair_candidate_path_allowed(planned_mirror_path, session_id),
        "planned_mirror_ledger_hash": source_hash,
        "planned_isolated_canonical_scope": True,
        "repair_cycle_status": "READY_PLAN_ONLY" if repair_ready else "BLOCKED_INPUT_MISSING",
        "primary_blocker_code": LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE
        if repair_ready
        else LEDGER_INPUT_SCOPE_REPAIR_INPUT_MISSING_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "candidate_mirror_write_allowed": False,
        "current_canonical_ledger_write_allowed": False,
        "current_evidence_write_allowed": False,
        "live_permission_created": False,
    }


def _build_item(
    *,
    root: Path,
    session_id: str,
    recheck_item: dict[str, Any],
    plan_item: dict[str, Any] | None,
    priority_order: int,
) -> dict[str, Any]:
    replacement_loop_id = str(recheck_item.get("replacement_loop_id") or "UNKNOWN")
    cycles = [
        _build_cycle(root=root, session_id=session_id, replacement_loop_id=replacement_loop_id, cycle=cycle)
        for cycle in (plan_item or {}).get("cycles", [])
        if isinstance(cycle, dict)
    ]
    cycle_count = len(cycles)
    ready_count = sum(1 for cycle in cycles if cycle["repair_cycle_status"] == "READY_PLAN_ONLY")
    event_count = sum(int(cycle["source_ledger_event_count"]) for cycle in cycles)
    missing_count = sum(1 for cycle in cycles if not cycle["source_selected_ledger_path_exists"])
    mirror_root = _mirror_root_path(session_id, replacement_loop_id)
    rollup_candidate_path = _planned_rollup_candidate_path(session_id, replacement_loop_id)
    item_ready = cycle_count > 0 and ready_count == cycle_count
    blocker_codes = {LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE}
    for cycle in cycles:
        blocker_codes.update(str(code) for code in cycle["blocker_codes"])
    if not item_ready:
        blocker_codes.add(LEDGER_INPUT_SCOPE_REPAIR_INPUT_MISSING_BLOCKER_CODE)
    return {
        "priority_order": priority_order,
        "replacement_loop_id": replacement_loop_id,
        "source_recheck_status": recheck_item.get("recheck_status"),
        "source_primary_blocker_code": recheck_item.get("primary_blocker_code"),
        "source_candidate_rollup_artifact_path": recheck_item.get("candidate_rollup_artifact_path"),
        "source_target_ledger_rollup_path": recheck_item.get("target_ledger_rollup_path"),
        "source_target_ledger_rollup_hash": recheck_item.get("target_ledger_rollup_hash"),
        "planned_isolated_root_path": mirror_root,
        "planned_rollup_candidate_path": rollup_candidate_path,
        "planned_rollup_candidate_path_allowed": _repair_candidate_path_allowed(rollup_candidate_path, session_id),
        "cycle_count": cycle_count,
        "repair_cycle_ready_count": ready_count,
        "missing_source_ledger_count": missing_count,
        "source_ledger_event_count": event_count,
        "planned_mirror_ledger_count": ready_count,
        "plan_item_status": "READY_PLAN_ONLY" if item_ready else "BLOCKED_INPUT_MISSING",
        "primary_blocker_code": LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE
        if item_ready
        else LEDGER_INPUT_SCOPE_REPAIR_INPUT_MISSING_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "cycles": cycles,
        "plan_only": True,
        "automatic_execution_allowed": False,
        "candidate_mirror_write_allowed": False,
        "current_canonical_ledger_write_allowed": False,
        "target_rollup_write_allowed": False,
        "current_evidence_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_repair_performed": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(
    *,
    root: Path,
    ledger_rollup_executor_reconciliation_recheck_report: dict[str, Any],
    ledger_rollup_regeneration_plan_report: dict[str, Any],
    ledger_input_scope_repair_plan_id: str = "upbit-paper-stale-loop-ledger-input-scope-repair-plan",
) -> dict[str, Any]:
    root = Path(root).resolve()
    recheck_result = validate_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(
        ledger_rollup_executor_reconciliation_recheck_report
    )
    plan_result = validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(
        ledger_rollup_regeneration_plan_report
    )
    session_id = str(ledger_rollup_executor_reconciliation_recheck_report.get("session_id", "UNKNOWN"))
    plan_by_loop = _plan_item_by_loop(ledger_rollup_regeneration_plan_report)
    source_items = [
        item
        for item in ledger_rollup_executor_reconciliation_recheck_report.get("items", [])
        if isinstance(item, dict) and item.get("recheck_status") == "BLOCKED_STRICT_LEDGER_INPUT_SCOPE"
    ]
    items = [
        _build_item(
            root=root,
            session_id=session_id,
            recheck_item=item,
            plan_item=plan_by_loop.get(str(item.get("replacement_loop_id") or "")),
            priority_order=index,
        )
        for index, item in enumerate(source_items, start=1)
    ]
    plan_ready_count = sum(1 for item in items if item["plan_item_status"] == "READY_PLAN_ONLY")
    plan_blocked_count = len(items) - plan_ready_count
    planned_cycle_count = sum(int(item["cycle_count"]) for item in items)
    repair_cycle_ready_count = sum(int(item["repair_cycle_ready_count"]) for item in items)
    missing_source_ledger_count = sum(int(item["missing_source_ledger_count"]) for item in items)
    source_event_count = sum(int(item["source_ledger_event_count"]) for item in items)
    planned_mirror_count = sum(int(item["planned_mirror_ledger_count"]) for item in items)
    blocker_codes = {LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE}
    if recheck_result.status != "PASS":
        blocker_codes.add(recheck_result.blocker_code or "LEDGER_ROLLUP_EXECUTOR_RECHECK_INVALID")
    if plan_result.status != "PASS":
        blocker_codes.add(plan_result.blocker_code or "LEDGER_ROLLUP_REGENERATION_PLAN_INVALID")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    if plan_blocked_count or missing_source_ledger_count:
        blocker_codes.add(LEDGER_INPUT_SCOPE_REPAIR_INPUT_MISSING_BLOCKER_CODE)
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "ledger_input_scope_repair_plan_id": ledger_input_scope_repair_plan_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN_TRUTH_ROLE,
        "ledger_input_scope_repair_plan_role": STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN_ROLE,
        "source_ledger_rollup_executor_reconciliation_recheck_hash": (
            ledger_rollup_executor_reconciliation_recheck_report.get("ledger_rollup_executor_reconciliation_recheck_hash")
        ),
        "source_ledger_rollup_executor_reconciliation_recheck_status": (
            ledger_rollup_executor_reconciliation_recheck_report.get("recheck_status")
        ),
        "source_ledger_rollup_executor_reconciliation_recheck_validator_status": recheck_result.status,
        "source_ledger_rollup_regeneration_plan_hash": (
            ledger_rollup_regeneration_plan_report.get("ledger_rollup_regeneration_plan_hash")
        ),
        "source_ledger_rollup_regeneration_plan_status": ledger_rollup_regeneration_plan_report.get("plan_status"),
        "source_ledger_rollup_regeneration_plan_validator_status": plan_result.status,
        "item_count": len(items),
        "repair_plan_candidate_count": len(items),
        "repair_plan_ready_count": plan_ready_count,
        "repair_plan_blocked_count": plan_blocked_count,
        "planned_cycle_count": planned_cycle_count,
        "repair_cycle_ready_count": repair_cycle_ready_count,
        "missing_source_ledger_count": missing_source_ledger_count,
        "source_ledger_event_count": source_event_count,
        "planned_mirror_ledger_count": planned_mirror_count,
        "candidate_mirror_write_allowed_count": 0,
        "current_canonical_ledger_write_allowed_count": 0,
        "target_rollup_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "plan_status": "READY_PLAN_ONLY" if items and plan_ready_count == len(items) else "BLOCKED",
        "primary_blocker_code": LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE
        if items and plan_ready_count == len(items)
        else LEDGER_INPUT_SCOPE_REPAIR_INPUT_MISSING_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Run a separate no-live isolated-root mirror executor before any candidate rollup rerun.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "plan_only": True,
        "automatic_execution_allowed": False,
        "candidate_mirror_write_allowed": False,
        "current_canonical_ledger_write_allowed": False,
        "target_rollup_write_allowed": False,
        "current_evidence_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_repair_performed": False,
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
        "can_submit_order": False,
        "scale_up_allowed": False,
        "ledger_input_scope_repair_plan_hash": "",
    }
    report["ledger_input_scope_repair_plan_hash"] = upbit_paper_stale_loop_ledger_input_scope_repair_plan_hash(report)
    return report


def write_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_ledger_input_scope_repair_plan_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "ledger_input_scope_repair_plan_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "ledger_input_scope_repair_plan_role",
        "source_ledger_rollup_executor_reconciliation_recheck_hash",
        "source_ledger_rollup_executor_reconciliation_recheck_status",
        "source_ledger_rollup_executor_reconciliation_recheck_validator_status",
        "source_ledger_rollup_regeneration_plan_hash",
        "source_ledger_rollup_regeneration_plan_status",
        "source_ledger_rollup_regeneration_plan_validator_status",
        "item_count",
        "repair_plan_candidate_count",
        "repair_plan_ready_count",
        "repair_plan_blocked_count",
        "planned_cycle_count",
        "repair_cycle_ready_count",
        "missing_source_ledger_count",
        "source_ledger_event_count",
        "planned_mirror_ledger_count",
        "candidate_mirror_write_allowed_count",
        "current_canonical_ledger_write_allowed_count",
        "target_rollup_write_allowed_count",
        "current_evidence_write_allowed_count",
        "plan_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "plan_only",
        "automatic_execution_allowed",
        "candidate_mirror_write_allowed",
        "current_canonical_ledger_write_allowed",
        "target_rollup_write_allowed",
        "current_evidence_write_allowed",
        "persistent_loop_mutation_allowed",
        "replacement_write_allowed",
        "source_delete_allowed",
        "actual_repair_performed",
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
        "can_submit_order",
        "scale_up_allowed",
        "ledger_input_scope_repair_plan_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
            "FAIL", f"ledger input scope repair plan missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN_SCHEMA_ID:
        return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
            "FAIL", "ledger input scope repair plan schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("ledger_input_scope_repair_plan_hash") != upbit_paper_stale_loop_ledger_input_scope_repair_plan_hash(report):
        return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
            "FAIL", "ledger input scope repair plan hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
            "BLOCKED", "ledger input scope repair plan scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    false_fields = (
        "automatic_execution_allowed",
        "candidate_mirror_write_allowed",
        "current_canonical_ledger_write_allowed",
        "target_rollup_write_allowed",
        "current_evidence_write_allowed",
        "persistent_loop_mutation_allowed",
        "replacement_write_allowed",
        "source_delete_allowed",
        "actual_repair_performed",
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
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(report.get(field) is not False for field in false_fields):
        return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
            "BLOCKED", "ledger input scope repair plan attempted execution or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if report.get("display_only") is not True or report.get("dashboard_truth_only") is not True or report.get("paper_only") is not True or report.get("plan_only") is not True:
        return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
            "BLOCKED", "ledger input scope repair plan must stay plan-only", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("candidate_mirror_write_allowed_count") != 0
        or report.get("current_canonical_ledger_write_allowed_count") != 0
        or report.get("target_rollup_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
    ):
        return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
            "BLOCKED", "ledger input scope repair plan exposed write counts", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("item_count") != len(items) or report.get("repair_plan_candidate_count") != len(items):
        return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
            "FAIL", "ledger input scope repair plan item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected = {
        "repair_plan_ready_count": 0,
        "repair_plan_blocked_count": 0,
        "planned_cycle_count": 0,
        "repair_cycle_ready_count": 0,
        "missing_source_ledger_count": 0,
        "source_ledger_event_count": 0,
        "planned_mirror_ledger_count": 0,
    }
    session_id = str(report.get("session_id"))
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                "FAIL", "ledger input scope repair plan item must be an object", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("priority_order") != index:
            return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                "FAIL", "ledger input scope repair plan priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if not _repair_candidate_path_allowed(str(item.get("planned_isolated_root_path") or ""), session_id):
            return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                "BLOCKED", "ledger input scope repair plan isolated root escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
            )
        if not _repair_candidate_path_allowed(str(item.get("planned_rollup_candidate_path") or ""), session_id):
            return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                "BLOCKED", "ledger input scope repair plan rollup candidate escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
            )
        for field in (
            "automatic_execution_allowed",
            "candidate_mirror_write_allowed",
            "current_canonical_ledger_write_allowed",
            "target_rollup_write_allowed",
            "current_evidence_write_allowed",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "actual_repair_performed",
            "actual_long_run_evidence_created",
            "live_permission_created",
        ):
            if item.get(field):
                return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                    "BLOCKED", "ledger input scope repair plan item attempted execution or live permission", "LIVE_FINAL_GUARD_FAILED"
                )
        cycles = item.get("cycles")
        if not isinstance(cycles, list) or item.get("cycle_count") != len(cycles):
            return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                "FAIL", "ledger input scope repair plan cycle count mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_ready = item.get("plan_item_status") == "READY_PLAN_ONLY"
        expected["repair_plan_ready_count"] += 1 if item_ready else 0
        expected["repair_plan_blocked_count"] += 0 if item_ready else 1
        expected["planned_cycle_count"] += len(cycles)
        ready_cycles = 0
        missing_cycles = 0
        event_count = 0
        for cycle in cycles:
            if not isinstance(cycle, dict):
                return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                    "FAIL", "ledger input scope repair plan cycle must be an object", "SCHEMA_IDENTITY_MISMATCH"
                )
            if not _runtime_path_allowed(str(cycle.get("source_selected_ledger_path") or ""), session_id):
                return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                    "BLOCKED", "ledger input scope repair plan source path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
            if not _repair_candidate_path_allowed(str(cycle.get("planned_mirror_ledger_path") or ""), session_id):
                return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                    "BLOCKED", "ledger input scope repair plan mirror path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
            if cycle.get("source_ledger_in_current_canonical_scope") is not False:
                return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                    "FAIL", "ledger input scope repair plan included an already-canonical source", "SCHEMA_IDENTITY_MISMATCH"
                )
            for field in (
                "candidate_mirror_write_allowed",
                "current_canonical_ledger_write_allowed",
                "current_evidence_write_allowed",
                "live_permission_created",
            ):
                if cycle.get(field):
                    return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                        "BLOCKED", "ledger input scope repair plan cycle attempted writes or live permission", "LIVE_FINAL_GUARD_FAILED"
                    )
            if cycle.get("repair_cycle_status") == "READY_PLAN_ONLY":
                ready_cycles += 1
            if not cycle.get("source_selected_ledger_path_exists"):
                missing_cycles += 1
            event_count += int(cycle.get("source_ledger_event_count") or 0)
        if item.get("repair_cycle_ready_count") != ready_cycles or item.get("missing_source_ledger_count") != missing_cycles or item.get("source_ledger_event_count") != event_count or item.get("planned_mirror_ledger_count") != ready_cycles:
            return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                "FAIL", "ledger input scope repair plan item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        expected["repair_cycle_ready_count"] += ready_cycles
        expected["missing_source_ledger_count"] += missing_cycles
        expected["source_ledger_event_count"] += event_count
        expected["planned_mirror_ledger_count"] += ready_cycles
    for field, expected_value in expected.items():
        if report.get(field) != expected_value:
            return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
                "FAIL", f"ledger input scope repair plan count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("plan_status") != "READY_PLAN_ONLY" or report.get("primary_blocker_code") != LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE:
        return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
            "BLOCKED",
            "ledger input scope repair plan must remain execution-only blocked",
            LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE,
        )
    return UpbitPaperStaleLoopLedgerInputScopeRepairPlanValidationResult(
        "PASS",
        "Upbit PAPER ledger input scope repair plan maps staged ledger JSONL into isolated candidate roots without writes",
        None,
    )
