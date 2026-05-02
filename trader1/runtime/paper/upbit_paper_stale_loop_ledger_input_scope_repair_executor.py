from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_stale_loop_ledger_input_scope_repair_plan import (
    validate_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_ledger_input_scope_repair_executor_report.v1"
)
STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_TRUTH_ROLE = (
    "paper_runtime_stale_loop_ledger_input_scope_repair_executor_truth"
)
STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_ISOLATED_CANDIDATE_ONLY"
)
LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE = (
    "LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED"
)
LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKER_CODE = (
    "LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKED"
)


@dataclass(frozen=True)
class UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def upbit_paper_stale_loop_ledger_input_scope_repair_executor_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("ledger_input_scope_repair_executor_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _candidate_mirror_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    prefix = (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        "ledger_input_scope_repair_candidates/"
    )
    return normalized.startswith(prefix) and ".." not in normalized.split("/") and "/live/" not in normalized


def _safe_name(value: str, limit: int = 36) -> str:
    sanitized = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value)
    if len(sanitized) <= limit:
        return sanitized
    return f"{sanitized[:limit]}-{_sha256_bytes(value.encode('utf-8'))[:12]}"


def _windows_safe_mirror_path(session_id: str, replacement_loop_id: str, cycle_id: str) -> str:
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        f"ledger_input_scope_repair_candidates/{_safe_name(replacement_loop_id)}/"
        f"ledger/{_safe_name(cycle_id)}.paper_ledger_events.jsonl"
    )


def _current_canonical_path(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/cycles/")


def _read_source_bytes(path: Path) -> tuple[bytes | None, str, str | None]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None, "MISSING", None
    except OSError:
        return None, "UNREADABLE", None
    return raw, "PASS", _sha256_bytes(raw)


def _write_bytes_atomic(path: Path, payload: bytes, *, enabled: bool) -> tuple[str, bool, bool, str | None]:
    payload_hash = _sha256_bytes(payload)
    if not enabled:
        return "WRITE_DISABLED", False, False, None
    if path.exists():
        try:
            existing = path.read_bytes()
        except OSError:
            return "BLOCKED_EXISTING_UNREADABLE", False, False, None
        existing_hash = _sha256_bytes(existing)
        if existing_hash == payload_hash:
            return "REUSED_EXISTING_MATCH", False, True, existing_hash
        return "BLOCKED_EXISTING_MISMATCH", False, False, existing_hash
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(payload)
    tmp.replace(path)
    return "WRITTEN", True, False, payload_hash


def _cycle_status(write_status: str, source_status: str, source_hash_match: bool, path_allowed: bool) -> tuple[str, str]:
    if not path_allowed:
        return "BLOCKED_PATH_ESCAPE", "SNAPSHOT_SCOPE_MISMATCH"
    if source_status != "PASS":
        return "BLOCKED_INPUT_MISSING", LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKER_CODE
    if not source_hash_match:
        return "BLOCKED_SOURCE_HASH_MISMATCH", "LEDGER_INPUT_SCOPE_REPAIR_SOURCE_HASH_MISMATCH"
    if write_status in {"WRITTEN", "REUSED_EXISTING_MATCH"}:
        return "CANDIDATE_MIRROR_READY", LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE
    if write_status == "WRITE_DISABLED":
        return "WRITE_DISABLED", LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE
    return "BLOCKED_MIRROR_WRITE", "LEDGER_INPUT_SCOPE_REPAIR_MIRROR_WRITE_BLOCKED"


def _build_cycle(
    *,
    root: Path,
    session_id: str,
    replacement_loop_id: str,
    plan_cycle: dict[str, Any],
    candidate_mirror_write_enabled: bool,
) -> dict[str, Any]:
    cycle_id = str(plan_cycle.get("cycle_id") or "UNKNOWN")
    source_path = str(plan_cycle.get("source_selected_ledger_path") or "")
    planned_mirror_path = str(plan_cycle.get("planned_mirror_ledger_path") or "")
    mirror_path = _windows_safe_mirror_path(session_id, replacement_loop_id, cycle_id)
    expected_source_hash = plan_cycle.get("source_selected_ledger_hash")
    raw, source_status, source_hash = _read_source_bytes(_rooted(root, source_path))
    source_hash_match = isinstance(expected_source_hash, str) and source_hash == expected_source_hash
    planned_mirror_path_allowed = _candidate_mirror_path_allowed(planned_mirror_path, session_id)
    mirror_path_allowed = _candidate_mirror_path_allowed(mirror_path, session_id)
    source_in_current_canonical_scope = _current_canonical_path(source_path, session_id)
    write_status = "BLOCKED_INPUT_MISSING"
    mirror_written = False
    mirror_reused = False
    mirror_hash: str | None = None
    if raw is not None and source_hash_match and mirror_path_allowed:
        write_status, mirror_written, mirror_reused, mirror_hash = _write_bytes_atomic(
            _rooted(root, mirror_path),
            raw,
            enabled=candidate_mirror_write_enabled,
        )
    cycle_status, primary_blocker_code = _cycle_status(
        write_status,
        source_status,
        source_hash_match,
        mirror_path_allowed,
    )
    ready = cycle_status == "CANDIDATE_MIRROR_READY"
    blocker_codes = {LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE, primary_blocker_code}
    if source_in_current_canonical_scope:
        blocker_codes.add("LEDGER_INPUT_SCOPE_REPAIR_SOURCE_CANONICAL_SCOPE_BLOCKED")
    if not source_hash_match:
        blocker_codes.add("LEDGER_INPUT_SCOPE_REPAIR_SOURCE_HASH_MISMATCH")
    return {
        "cycle_id": cycle_id,
        "final_decision": plan_cycle.get("final_decision"),
        "source_selected_ledger_path": source_path,
        "source_selected_ledger_path_exists": raw is not None,
        "source_selected_ledger_hash": source_hash,
        "source_expected_ledger_hash": expected_source_hash,
        "source_hash_match": source_hash_match,
        "source_ledger_load_status": source_status,
        "source_ledger_event_count": int(plan_cycle.get("source_ledger_event_count") or 0),
        "source_ledger_in_current_canonical_scope": source_in_current_canonical_scope,
        "planned_mirror_ledger_path": planned_mirror_path,
        "planned_mirror_ledger_path_allowed": planned_mirror_path_allowed,
        "windows_safe_mirror_ledger_path": mirror_path,
        "windows_safe_mirror_ledger_path_allowed": mirror_path_allowed,
        "candidate_mirror_write_status": write_status,
        "candidate_mirror_written": mirror_written,
        "candidate_mirror_reused_existing": mirror_reused,
        "candidate_mirror_artifact_ready": ready,
        "candidate_mirror_ledger_hash": mirror_hash,
        "candidate_mirror_hash_match": ready and mirror_hash == source_hash,
        "executor_cycle_status": cycle_status,
        "primary_blocker_code": primary_blocker_code,
        "blocker_codes": sorted(blocker_codes),
        "candidate_mirror_is_current_evidence": False,
        "current_canonical_ledger_write_allowed": False,
        "target_rollup_write_allowed": False,
        "current_evidence_write_allowed": False,
        "live_permission_created": False,
    }


def _build_item(
    *,
    root: Path,
    session_id: str,
    plan_item: dict[str, Any],
    priority_order: int,
    candidate_mirror_write_enabled: bool,
) -> dict[str, Any]:
    cycles = [
        _build_cycle(
            root=root,
            session_id=session_id,
            replacement_loop_id=str(plan_item.get("replacement_loop_id") or "UNKNOWN"),
            plan_cycle=cycle,
            candidate_mirror_write_enabled=candidate_mirror_write_enabled,
        )
        for cycle in plan_item.get("cycles", [])
        if isinstance(cycle, dict)
    ]
    attempt_count = len(cycles)
    ready_count = sum(1 for cycle in cycles if cycle["candidate_mirror_artifact_ready"])
    written_count = sum(1 for cycle in cycles if cycle["candidate_mirror_written"])
    reused_count = sum(1 for cycle in cycles if cycle["candidate_mirror_reused_existing"])
    source_hash_match_count = sum(1 for cycle in cycles if cycle["source_hash_match"])
    blocked_count = attempt_count - ready_count
    blocker_codes = {LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE}
    for cycle in cycles:
        blocker_codes.update(str(code) for code in cycle["blocker_codes"])
    if attempt_count and ready_count == attempt_count:
        item_status = "CANDIDATE_MIRROR_READY_CURRENT_EVIDENCE_BLOCKED"
        primary_blocker_code = LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE
    elif not candidate_mirror_write_enabled:
        item_status = "WRITE_DISABLED_CURRENT_EVIDENCE_BLOCKED"
        primary_blocker_code = LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE
    else:
        item_status = "BLOCKED_INPUT_OR_MIRROR"
        primary_blocker_code = LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKER_CODE
        blocker_codes.add(primary_blocker_code)
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(plan_item.get("replacement_loop_id") or "UNKNOWN"),
        "source_plan_item_status": plan_item.get("plan_item_status"),
        "source_planned_isolated_root_path": plan_item.get("planned_isolated_root_path"),
        "source_planned_rollup_candidate_path": plan_item.get("planned_rollup_candidate_path"),
        "candidate_mirror_cycle_attempt_count": attempt_count,
        "candidate_mirror_ready_count": ready_count,
        "candidate_mirror_blocked_count": blocked_count,
        "candidate_mirror_written_count": written_count,
        "candidate_mirror_reused_existing_count": reused_count,
        "source_hash_match_count": source_hash_match_count,
        "source_ledger_event_count": sum(int(cycle.get("source_ledger_event_count") or 0) for cycle in cycles),
        "executor_item_status": item_status,
        "primary_blocker_code": primary_blocker_code,
        "blocker_codes": sorted(blocker_codes),
        "cycles": cycles,
        "candidate_mirror_only": True,
        "candidate_mirror_is_current_evidence": False,
        "current_canonical_ledger_write_allowed": False,
        "target_rollup_write_allowed": False,
        "current_evidence_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(
    *,
    root: Path,
    ledger_input_scope_repair_plan_report: dict[str, Any],
    ledger_input_scope_repair_executor_id: str = "upbit-paper-stale-loop-ledger-input-scope-repair-executor",
    candidate_mirror_write_enabled: bool = False,
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(
        ledger_input_scope_repair_plan_report
    )
    session_id = str(ledger_input_scope_repair_plan_report.get("session_id", "UNKNOWN"))
    source_items = [
        item
        for item in ledger_input_scope_repair_plan_report.get("items", [])
        if isinstance(item, dict) and item.get("plan_item_status") == "READY_PLAN_ONLY"
    ]
    items = [
        _build_item(
            root=root,
            session_id=session_id,
            plan_item=item,
            priority_order=index,
            candidate_mirror_write_enabled=candidate_mirror_write_enabled,
        )
        for index, item in enumerate(source_items, start=1)
    ]
    attempt_count = sum(int(item["candidate_mirror_cycle_attempt_count"]) for item in items)
    ready_count = sum(int(item["candidate_mirror_ready_count"]) for item in items)
    blocked_count = sum(int(item["candidate_mirror_blocked_count"]) for item in items)
    written_count = sum(int(item["candidate_mirror_written_count"]) for item in items)
    reused_count = sum(int(item["candidate_mirror_reused_existing_count"]) for item in items)
    source_hash_match_count = sum(int(item["source_hash_match_count"]) for item in items)
    if candidate_mirror_write_enabled and attempt_count and ready_count == attempt_count:
        executor_status = "CANDIDATE_MIRROR_READY_CURRENT_EVIDENCE_BLOCKED"
    elif not candidate_mirror_write_enabled:
        executor_status = "WRITE_DISABLED_CURRENT_EVIDENCE_BLOCKED"
    else:
        executor_status = "BLOCKED_INPUT_OR_MIRROR"
    blocker_codes = {LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or "LEDGER_INPUT_SCOPE_REPAIR_PLAN_INVALID")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    if blocked_count:
        blocker_codes.add(LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKER_CODE)
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "ledger_input_scope_repair_executor_id": ledger_input_scope_repair_executor_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_TRUTH_ROLE,
        "ledger_input_scope_repair_executor_role": STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_ROLE,
        "source_ledger_input_scope_repair_plan_hash": ledger_input_scope_repair_plan_report.get(
            "ledger_input_scope_repair_plan_hash"
        ),
        "source_ledger_input_scope_repair_plan_status": ledger_input_scope_repair_plan_report.get("plan_status"),
        "source_ledger_input_scope_repair_plan_validator_status": source_result.status,
        "source_repair_plan_candidate_count": ledger_input_scope_repair_plan_report.get("repair_plan_candidate_count"),
        "item_count": len(items),
        "repair_executor_candidate_count": len(items),
        "candidate_mirror_cycle_attempt_count": attempt_count,
        "candidate_mirror_ready_count": ready_count,
        "candidate_mirror_blocked_count": blocked_count,
        "candidate_mirror_written_count": written_count,
        "candidate_mirror_reused_existing_count": reused_count,
        "source_hash_match_count": source_hash_match_count,
        "source_ledger_event_count": sum(int(item.get("source_ledger_event_count") or 0) for item in items),
        "candidate_mirror_artifact_ready_count": ready_count,
        "current_canonical_ledger_write_allowed_count": 0,
        "target_rollup_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "executor_status": executor_status,
        "primary_blocker_code": LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Rebuild candidate rollups from isolated mirror roots before any current-evidence closure.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "candidate_mirror_only": True,
        "candidate_mirror_write_enabled": bool(candidate_mirror_write_enabled),
        "candidate_mirror_is_current_evidence": False,
        "current_canonical_ledger_write_allowed": False,
        "target_rollup_write_allowed": False,
        "current_evidence_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
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
        "can_submit_order": False,
        "scale_up_allowed": False,
        "ledger_input_scope_repair_executor_hash": "",
    }
    report["ledger_input_scope_repair_executor_hash"] = (
        upbit_paper_stale_loop_ledger_input_scope_repair_executor_hash(report)
    )
    return report


def write_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_ledger_input_scope_repair_executor_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "ledger_input_scope_repair_executor_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "ledger_input_scope_repair_executor_role",
        "source_ledger_input_scope_repair_plan_hash",
        "source_ledger_input_scope_repair_plan_status",
        "source_ledger_input_scope_repair_plan_validator_status",
        "source_repair_plan_candidate_count",
        "item_count",
        "repair_executor_candidate_count",
        "candidate_mirror_cycle_attempt_count",
        "candidate_mirror_ready_count",
        "candidate_mirror_blocked_count",
        "candidate_mirror_written_count",
        "candidate_mirror_reused_existing_count",
        "source_hash_match_count",
        "source_ledger_event_count",
        "candidate_mirror_artifact_ready_count",
        "current_canonical_ledger_write_allowed_count",
        "target_rollup_write_allowed_count",
        "current_evidence_write_allowed_count",
        "executor_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "candidate_mirror_only",
        "candidate_mirror_write_enabled",
        "candidate_mirror_is_current_evidence",
        "current_canonical_ledger_write_allowed",
        "target_rollup_write_allowed",
        "current_evidence_write_allowed",
        "persistent_loop_mutation_allowed",
        "replacement_write_allowed",
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
        "can_submit_order",
        "scale_up_allowed",
        "ledger_input_scope_repair_executor_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
            "FAIL", f"ledger input scope repair executor missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_SCHEMA_ID:
        return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
            "FAIL", "ledger input scope repair executor schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("ledger_input_scope_repair_executor_hash") != upbit_paper_stale_loop_ledger_input_scope_repair_executor_hash(report):
        return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
            "FAIL", "ledger input scope repair executor hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
            "BLOCKED", "ledger input scope repair executor scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    false_fields = (
        "candidate_mirror_is_current_evidence",
        "current_canonical_ledger_write_allowed",
        "target_rollup_write_allowed",
        "current_evidence_write_allowed",
        "persistent_loop_mutation_allowed",
        "replacement_write_allowed",
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
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(report.get(field) is not False for field in false_fields):
        return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
            "BLOCKED", "ledger input scope repair executor attempted current evidence or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if report.get("display_only") is not True or report.get("dashboard_truth_only") is not True or report.get("paper_only") is not True or report.get("candidate_mirror_only") is not True:
        return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
            "BLOCKED", "ledger input scope repair executor must stay candidate-mirror-only", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("current_canonical_ledger_write_allowed_count") != 0
        or report.get("target_rollup_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
    ):
        return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
            "BLOCKED", "ledger input scope repair executor exposed forbidden write counts", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("item_count") != len(items) or report.get("repair_executor_candidate_count") != len(items):
        return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
            "FAIL", "ledger input scope repair executor item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    session_id = str(report.get("session_id"))
    attempt_count = 0
    ready_count = 0
    blocked_count = 0
    written_count = 0
    reused_count = 0
    source_hash_match_count = 0
    source_event_count = 0
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                "FAIL", "ledger input scope repair executor item must be an object", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("priority_order") != index:
            return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                "FAIL", "ledger input scope repair executor priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_false = (
            "candidate_mirror_is_current_evidence",
            "current_canonical_ledger_write_allowed",
            "target_rollup_write_allowed",
            "current_evidence_write_allowed",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "actual_long_run_evidence_created",
            "live_permission_created",
        )
        if any(item.get(field) is not False for field in item_false):
            return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                "BLOCKED", "ledger input scope repair executor item attempted forbidden write or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        cycles = item.get("cycles")
        if not isinstance(cycles, list) or item.get("candidate_mirror_cycle_attempt_count") != len(cycles):
            return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                "FAIL", "ledger input scope repair executor cycle count mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_ready = item_written = item_reused = item_hash_match = item_events = 0
        for cycle in cycles:
            if not isinstance(cycle, dict):
                return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                    "FAIL", "ledger input scope repair executor cycle must be an object", "SCHEMA_IDENTITY_MISMATCH"
                )
            if not _candidate_mirror_path_allowed(str(cycle.get("planned_mirror_ledger_path") or ""), session_id):
                return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                    "BLOCKED", "ledger input scope repair executor planned mirror path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
            if not _candidate_mirror_path_allowed(str(cycle.get("windows_safe_mirror_ledger_path") or ""), session_id):
                return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                    "BLOCKED", "ledger input scope repair executor Windows-safe mirror path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
            if cycle.get("source_ledger_in_current_canonical_scope") is not False:
                return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                    "BLOCKED", "ledger input scope repair executor source remained current canonical scope", "SNAPSHOT_SCOPE_MISMATCH"
                )
            cycle_false = (
                "candidate_mirror_is_current_evidence",
                "current_canonical_ledger_write_allowed",
                "target_rollup_write_allowed",
                "current_evidence_write_allowed",
                "live_permission_created",
            )
            if any(cycle.get(field) is not False for field in cycle_false):
                return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                    "BLOCKED", "ledger input scope repair executor cycle attempted forbidden write or live permission", "LIVE_FINAL_GUARD_FAILED"
                )
            if cycle.get("candidate_mirror_artifact_ready") is True:
                item_ready += 1
            if cycle.get("candidate_mirror_written") is True:
                item_written += 1
            if cycle.get("candidate_mirror_reused_existing") is True:
                item_reused += 1
            if cycle.get("source_hash_match") is True:
                item_hash_match += 1
            item_events += int(cycle.get("source_ledger_event_count") or 0)
            if cycle.get("candidate_mirror_artifact_ready") is True and cycle.get("candidate_mirror_hash_match") is not True:
                return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                    "FAIL", "ledger input scope repair executor ready mirror did not match source hash", "SCHEMA_IDENTITY_MISMATCH"
                )
        item_attempt = len(cycles)
        if (
            item.get("candidate_mirror_ready_count") != item_ready
            or item.get("candidate_mirror_blocked_count") != item_attempt - item_ready
            or item.get("candidate_mirror_written_count") != item_written
            or item.get("candidate_mirror_reused_existing_count") != item_reused
            or item.get("source_hash_match_count") != item_hash_match
            or item.get("source_ledger_event_count") != item_events
        ):
            return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
                "FAIL", "ledger input scope repair executor item aggregate mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        attempt_count += item_attempt
        ready_count += item_ready
        blocked_count += item_attempt - item_ready
        written_count += item_written
        reused_count += item_reused
        source_hash_match_count += item_hash_match
        source_event_count += item_events
    if (
        report.get("candidate_mirror_cycle_attempt_count") != attempt_count
        or report.get("candidate_mirror_ready_count") != ready_count
        or report.get("candidate_mirror_blocked_count") != blocked_count
        or report.get("candidate_mirror_written_count") != written_count
        or report.get("candidate_mirror_reused_existing_count") != reused_count
        or report.get("source_hash_match_count") != source_hash_match_count
        or report.get("source_ledger_event_count") != source_event_count
        or report.get("candidate_mirror_artifact_ready_count") != ready_count
    ):
        return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
            "FAIL", "ledger input scope repair executor aggregate mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("candidate_mirror_write_enabled") is True and attempt_count > 0 and ready_count != attempt_count:
        return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
            "FAIL", "ledger input scope repair executor enabled mirror writes without full readiness", LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKER_CODE
        )
    return UpbitPaperStaleLoopLedgerInputScopeRepairExecutorValidationResult(
        "PASS", "ledger input scope repair executor preserves isolated candidate mirrors and blocks current evidence/live", None
    )
