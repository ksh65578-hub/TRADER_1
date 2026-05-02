from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.core.ledger.paper_ledger import validate_upbit_paper_ledger
from trader1.runtime.ledger.paper_ledger_rollup import paper_ledger_rollup_hash
from trader1.runtime.paper.upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck import (
    validate_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_PLAN_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report.v1"
)
STALE_LOOP_LEDGER_ROLLUP_REGENERATION_PLAN_TRUTH_ROLE = (
    "paper_runtime_stale_loop_ledger_rollup_regeneration_plan_truth"
)
STALE_LOOP_LEDGER_ROLLUP_REGENERATION_PLAN_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_PLAN_NO_EXECUTION"
)
LEDGER_ROLLUP_REGENERATION_PLAN_BLOCKER_CODE = "LEDGER_ROLLUP_REGENERATION_PLAN_ONLY_EXECUTION_REQUIRED"
LEDGER_ROLLUP_REGENERATION_INPUT_MISSING_BLOCKER_CODE = "LEDGER_ROLLUP_REGENERATION_INPUT_MISSING"


@dataclass(frozen=True)
class UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_ledger_rollup_regeneration_plan_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("ledger_rollup_regeneration_plan_hash", None)
    return _sha256_json(payload)


def _candidate_rollup_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("candidate_rollup_hash", None)
    return _sha256_json(payload)


def _candidate_hash_fields(report: dict[str, Any]) -> tuple[Any, str | None, str | None]:
    if "candidate_rollup_hash" in report:
        return report.get("candidate_rollup_hash"), _candidate_rollup_hash(report), report.get("candidate_rollup_status")
    if "rollup_hash" in report:
        return report.get("rollup_hash"), paper_ledger_rollup_hash(report), report.get("rollup_status")
    return None, None, None


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/")
        and ".." not in normalized.split("/")
        and "/live/" not in normalized
    )


def _safe_load_json(path: Path) -> tuple[dict[str, Any] | None, str]:
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
    return value, "PASS"


def _safe_read_jsonl(path: Path) -> tuple[list[dict[str, Any]] | None, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None, "MISSING"
    except UnicodeDecodeError:
        return None, "INVALID_UTF8"
    records: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            return None, "INVALID_JSON"
        if not isinstance(value, dict):
            return None, "NOT_OBJECT"
        records.append(value)
    return records, "PASS"


def _cycle_ids(replacement: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(replacement, dict):
        return []
    cycles: list[dict[str, Any]] = []
    for cycle in replacement.get("cycle_results", []):
        if isinstance(cycle, dict) and isinstance(cycle.get("cycle_id"), str):
            cycles.append(
                {
                    "cycle_id": cycle["cycle_id"],
                    "final_decision": cycle.get("final_decision"),
                }
            )
    return cycles


def _staged_ledger_path(session_id: str, replacement_loop_id: str, cycle_id: str) -> str:
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/rerun_candidates/"
        f"{replacement_loop_id}/{cycle_id}.paper_ledger_events.jsonl"
    )


def _fallback_ledger_path(session_id: str, cycle_id: str) -> str:
    return f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/cycles/{cycle_id}.paper_ledger_events.jsonl"


def _post_rollup_candidate_path(session_id: str, replacement_loop_id: str, cycle_id: str) -> str:
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/rerun_candidates_post_rollup/"
        f"{replacement_loop_id}/{cycle_id}.ledger_rollup_candidate.json"
    )


def _repair_candidate_path(session_id: str, replacement_loop_id: str) -> str:
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/repairs/"
        f"{replacement_loop_id}.ledger_rollup_candidate.json"
    )


def _candidate_reference(root: Path, session_id: str, replacement_loop_id: str, cycle_id: str) -> tuple[str, str, dict[str, Any] | None, str]:
    post_path = _post_rollup_candidate_path(session_id, replacement_loop_id, cycle_id)
    post_candidate, post_status = _safe_load_json(_rooted(root, post_path))
    if post_candidate is not None:
        return post_path, "POST_RERUN_CANDIDATE_ROLLUP", post_candidate, post_status
    repair_path = _repair_candidate_path(session_id, replacement_loop_id)
    repair_candidate, repair_status = _safe_load_json(_rooted(root, repair_path))
    if repair_candidate is not None:
        return repair_path, "REPAIR_CANDIDATE_ROLLUP", repair_candidate, repair_status
    return post_path, "MISSING", None, post_status


def _build_cycle_item(*, root: Path, session_id: str, replacement_loop_id: str, cycle: dict[str, Any]) -> dict[str, Any]:
    cycle_id = str(cycle["cycle_id"])
    staged_path = _staged_ledger_path(session_id, replacement_loop_id, cycle_id)
    fallback_path = _fallback_ledger_path(session_id, cycle_id)
    selected_path = staged_path if _rooted(root, staged_path).exists() else fallback_path
    records, ledger_load_status = _safe_read_jsonl(_rooted(root, selected_path))
    if records is None:
        ledger_validator_status = ledger_load_status
        ledger_validator_blocker_code = LEDGER_ROLLUP_REGENERATION_INPUT_MISSING_BLOCKER_CODE
        ledger_validator_message = f"ledger input load status: {ledger_load_status}"
        ledger_event_count = 0
    elif records:
        ledger_validator_status, ledger_validator_blocker_code, ledger_validator_message = validate_upbit_paper_ledger(records)
        ledger_event_count = len(records)
    elif cycle.get("final_decision") != "ENTER_LONG":
        ledger_validator_status = "PASS"
        ledger_validator_blocker_code = None
        ledger_validator_message = "no-trade cycle may have empty ledger JSONL"
        ledger_event_count = 0
    else:
        ledger_validator_status = "BLOCKED"
        ledger_validator_blocker_code = LEDGER_ROLLUP_REGENERATION_INPUT_MISSING_BLOCKER_CODE
        ledger_validator_message = "ENTER_LONG cycle requires ledger events"
        ledger_event_count = 0
    candidate_path, candidate_kind, candidate, candidate_load_status = _candidate_reference(
        root,
        session_id,
        replacement_loop_id,
        cycle_id,
    )
    candidate_hash, candidate_recomputed_hash, candidate_status = (
        _candidate_hash_fields(candidate) if isinstance(candidate, dict) else (None, None, None)
    )
    candidate_hash_self_check = (
        "PASS"
        if isinstance(candidate_hash, str) and candidate_hash == candidate_recomputed_hash
        else "FAIL"
        if isinstance(candidate, dict)
        else "NOT_AVAILABLE"
    )
    candidate_status = candidate_status if isinstance(candidate, dict) else candidate_load_status
    cycle_ready = (
        records is not None
        and ledger_validator_status == "PASS"
        and isinstance(candidate, dict)
        and candidate_status == "PASS"
        and candidate_hash_self_check == "PASS"
    )
    return {
        "cycle_id": cycle_id,
        "final_decision": cycle.get("final_decision"),
        "preferred_staged_ledger_path": staged_path,
        "fallback_ledger_path": fallback_path,
        "selected_ledger_path": selected_path,
        "selected_ledger_path_exists": records is not None,
        "ledger_load_status": ledger_load_status,
        "ledger_event_count": ledger_event_count,
        "ledger_validator_status": ledger_validator_status,
        "ledger_validator_blocker_code": ledger_validator_blocker_code,
        "ledger_validator_message": ledger_validator_message,
        "candidate_rollup_reference_path": candidate_path,
        "candidate_rollup_reference_kind": candidate_kind,
        "candidate_rollup_reference_exists": isinstance(candidate, dict),
        "candidate_rollup_load_status": candidate_load_status,
        "candidate_rollup_status": candidate_status,
        "candidate_rollup_hash": candidate_hash,
        "candidate_rollup_recomputed_hash": candidate_recomputed_hash,
        "candidate_rollup_hash_self_check": candidate_hash_self_check,
        "cycle_regeneration_input_ready": cycle_ready,
        "current_evidence_write_allowed": False,
        "ledger_rollup_write_allowed": False,
        "live_permission_created": False,
    }


def _build_item(*, root: Path, session_id: str, source_item: dict[str, Any], priority_order: int) -> dict[str, Any]:
    replacement_loop_id = str(source_item.get("replacement_loop_id") or "UNKNOWN")
    replacement_path = str(source_item.get("replacement_path") or "")
    replacement, replacement_load_status = _safe_load_json(_rooted(root, replacement_path))
    cycles = [
        _build_cycle_item(root=root, session_id=session_id, replacement_loop_id=replacement_loop_id, cycle=cycle)
        for cycle in _cycle_ids(replacement)
    ]
    cycle_count = len(cycles)
    input_ready_count = sum(1 for cycle in cycles if cycle["cycle_regeneration_input_ready"])
    missing_input_count = sum(1 for cycle in cycles if not cycle["selected_ledger_path_exists"])
    candidate_present_count = sum(1 for cycle in cycles if cycle["candidate_rollup_reference_exists"])
    post_rollup_count = sum(1 for cycle in cycles if cycle["candidate_rollup_reference_kind"] == "POST_RERUN_CANDIDATE_ROLLUP")
    repair_count = sum(1 for cycle in cycles if cycle["candidate_rollup_reference_kind"] == "REPAIR_CANDIDATE_ROLLUP")
    item_ready = cycle_count > 0 and input_ready_count == cycle_count
    blocker_codes = set(str(code) for code in source_item.get("blocker_codes") or [])
    if not item_ready:
        blocker_codes.add(LEDGER_ROLLUP_REGENERATION_INPUT_MISSING_BLOCKER_CODE)
    blocker_codes.add(LEDGER_ROLLUP_REGENERATION_PLAN_BLOCKER_CODE)
    return {
        "priority_order": priority_order,
        "replacement_loop_id": replacement_loop_id,
        "replacement_path": replacement_path,
        "replacement_load_status": replacement_load_status,
        "target_ledger_rollup_path": str(source_item.get("ledger_rollup_path") or ""),
        "target_ledger_rollup_hash": source_item.get("source_expected_rollup_hash"),
        "target_ledger_rollup_missing": source_item.get("ledger_rollup_load_status") == "MISSING",
        "cycle_count": cycle_count,
        "cycle_regeneration_input_ready_count": input_ready_count,
        "missing_input_ledger_count": missing_input_count,
        "candidate_rollup_reference_present_count": candidate_present_count,
        "post_rollup_candidate_reference_count": post_rollup_count,
        "repair_candidate_reference_count": repair_count,
        "plan_item_status": "READY_PLAN_ONLY" if item_ready else "BLOCKED_INPUT_MISSING",
        "primary_blocker_code": LEDGER_ROLLUP_REGENERATION_PLAN_BLOCKER_CODE
        if item_ready
        else LEDGER_ROLLUP_REGENERATION_INPUT_MISSING_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "planned_action": "PLAN_AGGREGATE_ROLLUP_FROM_SCOPED_LEDGER_INPUTS",
        "operator_action": "Run a separate no-live ledger-rollup regeneration executor, then rerun reconciliation.",
        "cycles": cycles,
        "plan_only": True,
        "automatic_execution_allowed": False,
        "ledger_rollup_write_allowed": False,
        "current_evidence_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_regeneration_performed": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(
    *,
    root: Path,
    ledger_rollup_reconciliation_recheck_report: dict[str, Any],
    ledger_rollup_regeneration_plan_id: str = "upbit-paper-stale-loop-ledger-rollup-regeneration-plan",
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(
        ledger_rollup_reconciliation_recheck_report
    )
    session_id = str(ledger_rollup_reconciliation_recheck_report.get("session_id", "UNKNOWN"))
    source_items = [
        item
        for item in ledger_rollup_reconciliation_recheck_report.get("items", [])
        if isinstance(item, dict) and item.get("ledger_rollup_load_status") == "MISSING"
    ]
    items = [
        _build_item(root=root, session_id=session_id, source_item=item, priority_order=index)
        for index, item in enumerate(source_items, start=1)
    ]
    plan_ready_count = sum(1 for item in items if item["plan_item_status"] == "READY_PLAN_ONLY")
    blocked_count = len(items) - plan_ready_count
    cycle_count = sum(int(item["cycle_count"]) for item in items)
    input_ready_count = sum(int(item["cycle_regeneration_input_ready_count"]) for item in items)
    missing_input_count = sum(int(item["missing_input_ledger_count"]) for item in items)
    candidate_reference_count = sum(int(item["candidate_rollup_reference_present_count"]) for item in items)
    post_rollup_count = sum(int(item["post_rollup_candidate_reference_count"]) for item in items)
    repair_count = sum(int(item["repair_candidate_reference_count"]) for item in items)
    blocker_codes = {LEDGER_ROLLUP_REGENERATION_PLAN_BLOCKER_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or "LEDGER_ROLLUP_RECONCILIATION_RECHECK_INVALID")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    if blocked_count or missing_input_count:
        blocker_codes.add(LEDGER_ROLLUP_REGENERATION_INPUT_MISSING_BLOCKER_CODE)
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_PLAN_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "ledger_rollup_regeneration_plan_id": ledger_rollup_regeneration_plan_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_LEDGER_ROLLUP_REGENERATION_PLAN_TRUTH_ROLE,
        "ledger_rollup_regeneration_plan_role": STALE_LOOP_LEDGER_ROLLUP_REGENERATION_PLAN_ROLE,
        "source_ledger_rollup_reconciliation_recheck_hash": ledger_rollup_reconciliation_recheck_report.get(
            "ledger_rollup_reconciliation_recheck_hash"
        ),
        "source_ledger_rollup_reconciliation_recheck_status": ledger_rollup_reconciliation_recheck_report.get(
            "recheck_status"
        ),
        "source_ledger_rollup_reconciliation_recheck_validator_status": source_result.status,
        "source_ledger_rollup_artifact_missing_count": ledger_rollup_reconciliation_recheck_report.get(
            "ledger_rollup_artifact_missing_count"
        ),
        "item_count": len(items),
        "plan_candidate_count": len(items),
        "plan_ready_count": plan_ready_count,
        "plan_blocked_count": blocked_count,
        "planned_cycle_count": cycle_count,
        "cycle_regeneration_input_ready_count": input_ready_count,
        "missing_input_ledger_count": missing_input_count,
        "candidate_rollup_reference_present_count": candidate_reference_count,
        "post_rollup_candidate_reference_count": post_rollup_count,
        "repair_candidate_reference_count": repair_count,
        "plan_status": "READY_PLAN_ONLY" if plan_ready_count == len(items) and items else "BLOCKED",
        "primary_blocker_code": LEDGER_ROLLUP_REGENERATION_PLAN_BLOCKER_CODE
        if plan_ready_count == len(items) and items
        else LEDGER_ROLLUP_REGENERATION_INPUT_MISSING_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Run a separate no-live ledger-rollup regeneration executor; this plan cannot write artifacts.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "plan_only": True,
        "automatic_execution_allowed": False,
        "ledger_rollup_write_allowed": False,
        "current_evidence_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
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
        "can_submit_order": False,
        "scale_up_allowed": False,
        "ledger_rollup_regeneration_plan_hash": "",
    }
    report["ledger_rollup_regeneration_plan_hash"] = upbit_paper_stale_loop_ledger_rollup_regeneration_plan_hash(report)
    return report


def write_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "ledger_rollup_regeneration_plan_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "ledger_rollup_regeneration_plan_role",
        "source_ledger_rollup_reconciliation_recheck_hash",
        "source_ledger_rollup_reconciliation_recheck_status",
        "source_ledger_rollup_reconciliation_recheck_validator_status",
        "source_ledger_rollup_artifact_missing_count",
        "item_count",
        "plan_candidate_count",
        "plan_ready_count",
        "plan_blocked_count",
        "planned_cycle_count",
        "cycle_regeneration_input_ready_count",
        "missing_input_ledger_count",
        "candidate_rollup_reference_present_count",
        "post_rollup_candidate_reference_count",
        "repair_candidate_reference_count",
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
        "ledger_rollup_write_allowed",
        "current_evidence_write_allowed",
        "persistent_loop_mutation_allowed",
        "replacement_write_allowed",
        "source_delete_allowed",
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
        "can_submit_order",
        "scale_up_allowed",
        "ledger_rollup_regeneration_plan_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
            "FAIL", f"ledger-rollup regeneration plan missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_PLAN_SCHEMA_ID:
        return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
            "FAIL", "ledger-rollup regeneration plan schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("ledger_rollup_regeneration_plan_hash") != upbit_paper_stale_loop_ledger_rollup_regeneration_plan_hash(report):
        return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
            "FAIL", "ledger-rollup regeneration plan hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
            "BLOCKED", "ledger-rollup regeneration plan scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if (
        report.get("truth_role") != STALE_LOOP_LEDGER_ROLLUP_REGENERATION_PLAN_TRUTH_ROLE
        or report.get("ledger_rollup_regeneration_plan_role") != STALE_LOOP_LEDGER_ROLLUP_REGENERATION_PLAN_ROLE
    ):
        return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
            "FAIL", "ledger-rollup regeneration plan role mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    false_fields = (
        "automatic_execution_allowed",
        "ledger_rollup_write_allowed",
        "current_evidence_write_allowed",
        "persistent_loop_mutation_allowed",
        "replacement_write_allowed",
        "source_delete_allowed",
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
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(report.get(field) is not False for field in false_fields):
        return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
            "BLOCKED", "ledger-rollup regeneration plan attempted execution or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if report.get("display_only") is not True or report.get("dashboard_truth_only") is not True or report.get("paper_only") is not True or report.get("plan_only") is not True:
        return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
            "BLOCKED", "ledger-rollup regeneration plan must stay plan-only", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("item_count") != len(items) or report.get("plan_candidate_count") != len(items):
        return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
            "FAIL", "ledger-rollup regeneration plan item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected = {
        "plan_ready_count": 0,
        "plan_blocked_count": 0,
        "planned_cycle_count": 0,
        "cycle_regeneration_input_ready_count": 0,
        "missing_input_ledger_count": 0,
        "candidate_rollup_reference_present_count": 0,
        "post_rollup_candidate_reference_count": 0,
        "repair_candidate_reference_count": 0,
    }
    session_id = str(report.get("session_id"))
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                "FAIL", "ledger-rollup regeneration plan item must be an object", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_required = {
            "priority_order",
            "replacement_loop_id",
            "replacement_path",
            "replacement_load_status",
            "target_ledger_rollup_path",
            "target_ledger_rollup_hash",
            "target_ledger_rollup_missing",
            "cycle_count",
            "cycle_regeneration_input_ready_count",
            "missing_input_ledger_count",
            "candidate_rollup_reference_present_count",
            "post_rollup_candidate_reference_count",
            "repair_candidate_reference_count",
            "plan_item_status",
            "primary_blocker_code",
            "blocker_codes",
            "planned_action",
            "operator_action",
            "cycles",
            "plan_only",
            "automatic_execution_allowed",
            "ledger_rollup_write_allowed",
            "current_evidence_write_allowed",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "actual_regeneration_performed",
            "actual_long_run_evidence_created",
            "live_permission_created",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                "FAIL", f"ledger-rollup regeneration plan item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("priority_order") != index:
            return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                "FAIL", "ledger-rollup regeneration plan priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for path_field in ("replacement_path", "target_ledger_rollup_path"):
            if not _artifact_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                    "BLOCKED", f"ledger-rollup regeneration plan {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
        item_false = (
            "automatic_execution_allowed",
            "ledger_rollup_write_allowed",
            "current_evidence_write_allowed",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "actual_regeneration_performed",
            "actual_long_run_evidence_created",
            "live_permission_created",
        )
        if any(item.get(field) for field in item_false) or item.get("plan_only") is not True:
            return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                "BLOCKED", "ledger-rollup regeneration plan item attempted execution or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        cycles = item.get("cycles")
        if not isinstance(cycles, list) or item.get("cycle_count") != len(cycles):
            return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                "FAIL", "ledger-rollup regeneration plan cycle count mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        cycle_ready_count = 0
        missing_input_count = 0
        candidate_present_count = 0
        post_rollup_count = 0
        repair_count = 0
        for cycle in cycles:
            if not isinstance(cycle, dict):
                return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                    "FAIL", "ledger-rollup regeneration plan cycle must be an object", "SCHEMA_IDENTITY_MISMATCH"
                )
            for path_field in (
                "preferred_staged_ledger_path",
                "fallback_ledger_path",
                "selected_ledger_path",
                "candidate_rollup_reference_path",
            ):
                if not _artifact_path_allowed(str(cycle.get(path_field) or ""), session_id):
                    return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                        "BLOCKED", f"ledger-rollup regeneration plan cycle {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
                    )
            if cycle.get("current_evidence_write_allowed") or cycle.get("ledger_rollup_write_allowed") or cycle.get("live_permission_created"):
                return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                    "BLOCKED", "ledger-rollup regeneration plan cycle attempted write or live permission", "LIVE_FINAL_GUARD_FAILED"
                )
            if cycle.get("cycle_regeneration_input_ready"):
                cycle_ready_count += 1
                if (
                    cycle.get("selected_ledger_path_exists") is not True
                    or cycle.get("ledger_validator_status") != "PASS"
                    or cycle.get("candidate_rollup_reference_exists") is not True
                    or cycle.get("candidate_rollup_status") != "PASS"
                    or cycle.get("candidate_rollup_hash_self_check") != "PASS"
                ):
                    return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                        "FAIL", "ready ledger-rollup regeneration cycle lacks validated inputs", "SCHEMA_IDENTITY_MISMATCH"
                    )
            if not cycle.get("selected_ledger_path_exists"):
                missing_input_count += 1
            if cycle.get("candidate_rollup_reference_exists"):
                candidate_present_count += 1
            if cycle.get("candidate_rollup_reference_kind") == "POST_RERUN_CANDIDATE_ROLLUP":
                post_rollup_count += 1
            if cycle.get("candidate_rollup_reference_kind") == "REPAIR_CANDIDATE_ROLLUP":
                repair_count += 1
        if item.get("cycle_regeneration_input_ready_count") != cycle_ready_count or item.get("missing_input_ledger_count") != missing_input_count:
            return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                "FAIL", "ledger-rollup regeneration plan item cycle input rollup mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if (
            item.get("candidate_rollup_reference_present_count") != candidate_present_count
            or item.get("post_rollup_candidate_reference_count") != post_rollup_count
            or item.get("repair_candidate_reference_count") != repair_count
        ):
            return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                "FAIL", "ledger-rollup regeneration plan item candidate-reference rollup mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("plan_item_status") == "READY_PLAN_ONLY":
            expected["plan_ready_count"] += 1
        else:
            expected["plan_blocked_count"] += 1
        expected["planned_cycle_count"] += len(cycles)
        expected["cycle_regeneration_input_ready_count"] += cycle_ready_count
        expected["missing_input_ledger_count"] += missing_input_count
        expected["candidate_rollup_reference_present_count"] += candidate_present_count
        expected["post_rollup_candidate_reference_count"] += post_rollup_count
        expected["repair_candidate_reference_count"] += repair_count
    for field, value in expected.items():
        if report.get(field) != value:
            return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
                "FAIL", f"ledger-rollup regeneration plan count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("plan_status") != "READY_PLAN_ONLY" or report.get("primary_blocker_code") != LEDGER_ROLLUP_REGENERATION_PLAN_BLOCKER_CODE:
        return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
            "BLOCKED", "ledger-rollup regeneration plan must remain plan-only before execution", LEDGER_ROLLUP_REGENERATION_PLAN_BLOCKER_CODE
        )
    return UpbitPaperStaleLoopLedgerRollupRegenerationPlanValidationResult(
        "PASS",
        "Upbit PAPER stale-loop ledger-rollup regeneration plan is input-complete, plan-only, and live-blocked",
        None,
    )
