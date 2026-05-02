from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.ledger.execution_ledger import ledger_event_hash, validate_ledger_chain
from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repair_plan import (
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json, recover_jsonl_records


UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report.v1"
)
ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CANDIDATE_ONLY"
)
ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED_CODE = (
    "ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED"
)
ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKED_CODE = (
    "ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKED"
)


@dataclass(frozen=True)
class UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_hash(
    report: dict[str, Any],
) -> str:
    payload = dict(report)
    payload.pop("event_id_scope_repair_executor_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _candidate_root_prefix(session_id: str) -> str:
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        "ledger_input_scope_repair_candidates/"
    )


def _candidate_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith(_candidate_root_prefix(session_id))
        and ".." not in normalized.split("/")
        and "/live/" not in normalized
    )


def _safe_name(value: str, limit: int = 48) -> str:
    sanitized = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value)
    if len(sanitized) <= limit:
        return sanitized
    return f"{sanitized[:limit]}-{_sha256_bytes(value.encode('utf-8'))[:12]}"


def _planned_repaired_ledger_path(session_id: str, replacement_loop_id: str, cycle_id: str) -> str:
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        f"ledger_input_scope_repair_candidates/{_safe_name(replacement_loop_id, 32)}/"
        f"eid_repair/{_safe_name(cycle_id, 32)}.jsonl"
    )


def _jsonl_bytes(records: list[dict[str, Any]]) -> bytes:
    lines = [json.dumps(record, sort_keys=True, separators=(",", ":")) for record in records]
    return ("\n".join(lines) + "\n").encode("utf-8")


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


def _updates_by_ledger(plan_item: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    updates: dict[str, list[dict[str, Any]]] = {}
    for group in plan_item.get("event_id_groups", []):
        if not isinstance(group, dict):
            continue
        for update in group.get("planned_updates", []):
            if not isinstance(update, dict):
                continue
            ledger_path = str(update.get("ledger_path") or "")
            updates.setdefault(ledger_path, []).append(update)
    return updates


def _repair_records(
    records: list[dict[str, Any]],
    updates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, int, list[str]]:
    repaired = [dict(record) for record in records]
    blockers: list[str] = []
    updated_count = 0
    for update in sorted(updates, key=lambda item: int(item.get("event_index") or 0)):
        index = int(update.get("event_index") or 0)
        if index < 0 or index >= len(repaired):
            blockers.append("EVENT_ID_SCOPE_REPAIR_EVENT_INDEX_MISMATCH")
            continue
        event = repaired[index]
        original_event_id = str(update.get("original_event_id") or "")
        planned_event_id = str(update.get("planned_event_id") or "")
        if event.get("event_id") != original_event_id or not planned_event_id or planned_event_id == original_event_id:
            blockers.append("EVENT_ID_SCOPE_REPAIR_SOURCE_EVENT_MISMATCH")
            continue
        event["event_id"] = planned_event_id
        updated_count += 1

    if blockers:
        return repaired, updated_count, 0, sorted(set(blockers))

    recalculated_count = 0
    previous_hash: str | None = None
    for event in repaired:
        event["previous_hash"] = previous_hash
        event["event_hash"] = ledger_event_hash(event)
        previous_hash = event["event_hash"]
        recalculated_count += 1
    return repaired, updated_count, recalculated_count, []


def _duplicate_event_id_count(records: list[dict[str, Any]]) -> int:
    seen: set[str] = set()
    duplicates = 0
    for record in records:
        event_id = str(record.get("event_id") or "")
        if event_id in seen:
            duplicates += 1
        seen.add(event_id)
    return duplicates


def _duplicate_string_count(values: list[str]) -> int:
    seen: set[str] = set()
    duplicates = 0
    for value in values:
        if value in seen:
            duplicates += 1
        seen.add(value)
    return duplicates


def _build_cycle(
    *,
    root: Path,
    session_id: str,
    replacement_loop_id: str,
    ledger_path: str,
    updates: list[dict[str, Any]],
    candidate_repair_write_enabled: bool,
) -> dict[str, Any]:
    cycle_id = str(updates[0].get("cycle_id") if updates else "UNKNOWN")
    repaired_ledger_path = _planned_repaired_ledger_path(session_id, replacement_loop_id, cycle_id)
    load_status = "PASS"
    quarantine_path: str | None = None
    try:
        records, quarantine = recover_jsonl_records(_rooted(root, ledger_path))
        if quarantine is not None:
            quarantine_path = quarantine.as_posix()
    except FileNotFoundError:
        records = []
        load_status = "MISSING"
    except OSError:
        records = []
        load_status = "UNREADABLE"
    source_ledger_path_allowed = _candidate_path_allowed(ledger_path, session_id)
    repaired_ledger_path_allowed = _candidate_path_allowed(repaired_ledger_path, session_id)
    source_event_count = len(records)
    repaired_records: list[dict[str, Any]] = []
    updated_count = 0
    recalculated_count = 0
    repair_blockers: list[str] = []
    chain_status = "NOT_RUN"
    chain_blocker_code: str | None = None
    post_duplicate_count = 0
    write_status = "BLOCKED_INPUT_MISSING"
    written = False
    reused = False
    repaired_hash: str | None = None
    if load_status == "PASS" and source_ledger_path_allowed and repaired_ledger_path_allowed:
        repaired_records, updated_count, recalculated_count, repair_blockers = _repair_records(records, updates)
        if not repair_blockers:
            chain_result = validate_ledger_chain(repaired_records)
            chain_status = chain_result.status
            chain_blocker_code = chain_result.blocker_code
            post_duplicate_count = _duplicate_event_id_count(repaired_records)
            if chain_result.status == "PASS" and post_duplicate_count == 0:
                payload = _jsonl_bytes(repaired_records)
                write_status, written, reused, repaired_hash = _write_bytes_atomic(
                    _rooted(root, repaired_ledger_path),
                    payload,
                    enabled=candidate_repair_write_enabled,
                )
    ready = write_status in {"WRITTEN", "REUSED_EXISTING_MATCH"}
    blocker_codes = {ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED_CODE}
    if load_status != "PASS":
        blocker_codes.add(ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKED_CODE)
    if not source_ledger_path_allowed or not repaired_ledger_path_allowed:
        blocker_codes.add("SNAPSHOT_SCOPE_MISMATCH")
    for blocker in repair_blockers:
        blocker_codes.add(blocker)
    if chain_status not in {"PASS", "NOT_RUN"}:
        blocker_codes.add(chain_blocker_code or "LEDGER_INTEGRITY_FAIL")
    if post_duplicate_count:
        blocker_codes.add("EVENT_ID_SCOPE_REPAIR_DUPLICATE_REMAINS")
    if not ready:
        blocker_codes.add(ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED_CODE)
    return {
        "cycle_id": cycle_id,
        "replacement_loop_id": replacement_loop_id,
        "source_ledger_path": ledger_path,
        "source_ledger_path_allowed": source_ledger_path_allowed,
        "source_ledger_load_status": load_status,
        "source_ledger_event_count": source_event_count,
        "source_quarantine_path": quarantine_path,
        "planned_update_count": len(updates),
        "event_id_updated_count": updated_count,
        "event_hash_recalculation_count": recalculated_count,
        "repaired_ledger_path": repaired_ledger_path,
        "repaired_ledger_path_allowed": repaired_ledger_path_allowed,
        "repaired_ledger_event_count": len(repaired_records),
        "repaired_event_ids": [str(record.get("event_id") or "") for record in repaired_records],
        "repaired_ledger_hash": repaired_hash,
        "candidate_repair_write_status": write_status,
        "candidate_repair_written": written,
        "candidate_repair_reused_existing": reused,
        "candidate_repair_artifact_ready": ready,
        "post_repair_chain_status": chain_status,
        "post_repair_chain_blocker_code": chain_blocker_code,
        "post_repair_duplicate_event_id_count": post_duplicate_count,
        "executor_cycle_status": "CANDIDATE_REPAIR_READY_CURRENT_EVIDENCE_BLOCKED"
        if ready
        else "BLOCKED_INPUT_OR_REPAIR",
        "primary_blocker_code": ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED_CODE,
        "blocker_codes": sorted(blocker_codes),
        "candidate_mirror_only": True,
        "candidate_repair_is_current_evidence": False,
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
    candidate_repair_write_enabled: bool,
) -> dict[str, Any]:
    replacement_loop_id = str(plan_item.get("replacement_loop_id") or "UNKNOWN")
    updates_by_ledger = _updates_by_ledger(plan_item)
    cycles = [
        _build_cycle(
            root=root,
            session_id=session_id,
            replacement_loop_id=replacement_loop_id,
            ledger_path=ledger_path,
            updates=updates,
            candidate_repair_write_enabled=candidate_repair_write_enabled,
        )
        for ledger_path, updates in sorted(updates_by_ledger.items())
    ]
    cycle_count = len(cycles)
    ready_count = sum(1 for cycle in cycles if cycle["candidate_repair_artifact_ready"])
    written_count = sum(1 for cycle in cycles if cycle["candidate_repair_written"])
    reused_count = sum(1 for cycle in cycles if cycle["candidate_repair_reused_existing"])
    blocker_codes = {ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED_CODE}
    for cycle in cycles:
        blocker_codes.update(str(code) for code in cycle["blocker_codes"])
    repaired_event_ids: list[str] = []
    for cycle in cycles:
        repaired_event_ids.extend(str(event_id) for event_id in cycle.get("repaired_event_ids", []))
    return {
        "priority_order": priority_order,
        "replacement_loop_id": replacement_loop_id,
        "source_repair_plan_item_status": plan_item.get("repair_plan_item_status"),
        "source_planned_event_id_update_count": int(plan_item.get("planned_event_id_update_count") or 0),
        "candidate_repair_cycle_count": cycle_count,
        "candidate_repair_ready_count": ready_count,
        "candidate_repair_blocked_count": cycle_count - ready_count,
        "candidate_repair_written_count": written_count,
        "candidate_repair_reused_existing_count": reused_count,
        "event_id_updated_count": sum(int(cycle["event_id_updated_count"]) for cycle in cycles),
        "event_hash_recalculation_count": sum(int(cycle["event_hash_recalculation_count"]) for cycle in cycles),
        "post_repair_duplicate_event_id_count": _duplicate_string_count(repaired_event_ids),
        "executor_item_status": "CANDIDATE_REPAIR_READY_CURRENT_EVIDENCE_BLOCKED"
        if cycle_count and ready_count == cycle_count
        else "BLOCKED_INPUT_OR_REPAIR",
        "primary_blocker_code": ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED_CODE,
        "blocker_codes": sorted(blocker_codes),
        "cycles": cycles,
        "candidate_mirror_only": True,
        "actual_candidate_repair_performed": written_count > 0 or reused_count > 0,
        "candidate_repair_is_current_evidence": False,
        "current_canonical_ledger_write_allowed": False,
        "target_rollup_write_allowed": False,
        "current_evidence_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(
    *,
    root: Path,
    event_id_scope_repair_plan_report: dict[str, Any],
    event_id_scope_repair_executor_id: str = "upbit-paper-stale-loop-isolated-event-id-scope-repair-executor",
    candidate_repair_write_enabled: bool = False,
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(
        event_id_scope_repair_plan_report
    )
    session_id = str(event_id_scope_repair_plan_report.get("session_id") or "UNKNOWN")
    source_items = [
        item
        for item in event_id_scope_repair_plan_report.get("items", [])
        if isinstance(item, dict) and item.get("repair_plan_item_status") == "READY_PLAN_ONLY"
    ]
    items = [
        _build_item(
            root=root,
            session_id=session_id,
            plan_item=item,
            priority_order=index,
            candidate_repair_write_enabled=candidate_repair_write_enabled,
        )
        for index, item in enumerate(source_items, start=1)
    ]
    cycle_count = sum(int(item["candidate_repair_cycle_count"]) for item in items)
    ready_count = sum(int(item["candidate_repair_ready_count"]) for item in items)
    written_count = sum(int(item["candidate_repair_written_count"]) for item in items)
    reused_count = sum(int(item["candidate_repair_reused_existing_count"]) for item in items)
    event_id_updated_count = sum(int(item["event_id_updated_count"]) for item in items)
    event_hash_recalculation_count = sum(int(item["event_hash_recalculation_count"]) for item in items)
    repaired_event_ids: list[str] = []
    for item in items:
        for cycle in item.get("cycles", []):
            repaired_event_ids.extend(str(event_id) for event_id in cycle.get("repaired_event_ids", []))
    duplicate_count = _duplicate_string_count(repaired_event_ids)
    if candidate_repair_write_enabled and cycle_count and ready_count == cycle_count and duplicate_count == 0:
        executor_status = "CANDIDATE_REPAIR_READY_CURRENT_EVIDENCE_BLOCKED"
    elif not candidate_repair_write_enabled:
        executor_status = "WRITE_DISABLED_CURRENT_EVIDENCE_BLOCKED"
    else:
        executor_status = "BLOCKED_INPUT_OR_REPAIR"
    blocker_codes = {ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKED_CODE)
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "event_id_scope_repair_executor_id": event_id_scope_repair_executor_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "event_id_scope_repair_executor_role": ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_ROLE,
        "source_event_id_scope_repair_plan_hash": event_id_scope_repair_plan_report.get(
            "event_id_scope_repair_plan_hash"
        ),
        "source_event_id_scope_repair_plan_status": event_id_scope_repair_plan_report.get("plan_status"),
        "source_event_id_scope_repair_plan_validator_status": source_result.status,
        "source_planned_event_id_update_count": int(
            event_id_scope_repair_plan_report.get("planned_event_id_update_count") or 0
        ),
        "candidate_count": int(event_id_scope_repair_plan_report.get("candidate_count") or 0),
        "repair_executor_candidate_count": len(items),
        "candidate_repair_cycle_count": cycle_count,
        "candidate_repair_ready_count": ready_count,
        "candidate_repair_blocked_count": cycle_count - ready_count,
        "candidate_repair_written_count": written_count,
        "candidate_repair_reused_existing_count": reused_count,
        "event_id_updated_count": event_id_updated_count,
        "event_hash_recalculation_count": event_hash_recalculation_count,
        "post_repair_duplicate_event_id_count": duplicate_count,
        "candidate_repair_artifact_ready_count": ready_count,
        "current_canonical_ledger_write_allowed_count": 0,
        "target_rollup_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "executor_status": executor_status,
        "primary_blocker_code": ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Rebuild isolated candidate rollups from repaired candidate mirror ledgers; keep current evidence blocked.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "candidate_only": True,
        "candidate_mirror_only": True,
        "candidate_repair_write_enabled": bool(candidate_repair_write_enabled),
        "actual_candidate_repair_performed": written_count > 0 or reused_count > 0,
        "candidate_repair_is_current_evidence": False,
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
        "event_id_scope_repair_executor_hash": "",
    }
    report["event_id_scope_repair_executor_hash"] = (
        upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_hash(report)
    )
    return report


def write_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "event_id_scope_repair_executor_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "event_id_scope_repair_executor_role",
        "source_event_id_scope_repair_plan_hash",
        "source_event_id_scope_repair_plan_status",
        "source_event_id_scope_repair_plan_validator_status",
        "source_planned_event_id_update_count",
        "candidate_count",
        "repair_executor_candidate_count",
        "candidate_repair_cycle_count",
        "candidate_repair_ready_count",
        "candidate_repair_blocked_count",
        "candidate_repair_written_count",
        "candidate_repair_reused_existing_count",
        "event_id_updated_count",
        "event_hash_recalculation_count",
        "post_repair_duplicate_event_id_count",
        "candidate_repair_artifact_ready_count",
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
        "candidate_only",
        "candidate_mirror_only",
        "candidate_repair_write_enabled",
        "actual_candidate_repair_performed",
        "candidate_repair_is_current_evidence",
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
        "event_id_scope_repair_executor_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
            "FAIL", f"isolated event-id repair executor missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_SCHEMA_ID:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
            "FAIL", "isolated event-id repair executor schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("event_id_scope_repair_executor_hash") != upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_hash(report):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
            "FAIL", "isolated event-id repair executor hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
            "BLOCKED", "isolated event-id repair executor scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if report.get("event_id_scope_repair_executor_role") != ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_ROLE:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
            "BLOCKED", "isolated event-id repair executor role cannot claim live or current evidence", "LIVE_FINAL_GUARD_FAILED"
        )
    false_fields = (
        "candidate_repair_is_current_evidence",
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
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
            "BLOCKED", "isolated event-id repair executor attempted current evidence or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("current_canonical_ledger_write_allowed_count") != 0
        or report.get("target_rollup_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
    ):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
            "BLOCKED", "isolated event-id repair executor exposed forbidden write counts", "LIVE_FINAL_GUARD_FAILED"
        )
    if not all(
        report.get(field) is True
        for field in ("display_only", "dashboard_truth_only", "paper_only", "candidate_only", "candidate_mirror_only")
    ):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
            "BLOCKED", "isolated event-id repair executor must stay candidate-only", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("repair_executor_candidate_count") != len(items):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
            "FAIL", "isolated event-id repair executor item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    session_id = str(report.get("session_id"))
    totals = {
        "candidate_repair_cycle_count": 0,
        "candidate_repair_ready_count": 0,
        "candidate_repair_blocked_count": 0,
        "candidate_repair_written_count": 0,
        "candidate_repair_reused_existing_count": 0,
        "event_id_updated_count": 0,
        "event_hash_recalculation_count": 0,
        "post_repair_duplicate_event_id_count": 0,
    }
    repaired_paths: set[str] = set()
    global_repaired_event_ids: list[str] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or item.get("priority_order") != index:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                "FAIL", "isolated event-id repair executor priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if any(
            item.get(field) is not False
            for field in (
                "candidate_repair_is_current_evidence",
                "current_canonical_ledger_write_allowed",
                "target_rollup_write_allowed",
                "current_evidence_write_allowed",
                "persistent_loop_mutation_allowed",
                "replacement_write_allowed",
                "source_delete_allowed",
                "actual_long_run_evidence_created",
                "live_permission_created",
            )
        ):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                "BLOCKED", "isolated event-id repair executor item attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
            )
        cycles = item.get("cycles")
        if not isinstance(cycles, list) or item.get("candidate_repair_cycle_count") != len(cycles):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                "FAIL", "isolated event-id repair executor cycle count mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_counts = {
            "candidate_repair_ready_count": 0,
            "candidate_repair_written_count": 0,
            "candidate_repair_reused_existing_count": 0,
            "event_id_updated_count": 0,
            "event_hash_recalculation_count": 0,
            "post_repair_duplicate_event_id_count": 0,
        }
        item_repaired_event_ids: list[str] = []
        for cycle in cycles:
            if not isinstance(cycle, dict):
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                    "FAIL", "isolated event-id repair executor cycle must be object", "SCHEMA_IDENTITY_MISMATCH"
                )
            if not _candidate_path_allowed(str(cycle.get("source_ledger_path") or ""), session_id):
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                    "BLOCKED", "isolated event-id repair executor source path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
            repaired_path = str(cycle.get("repaired_ledger_path") or "")
            if not _candidate_path_allowed(repaired_path, session_id):
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                    "BLOCKED", "isolated event-id repair executor repaired path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
            if repaired_path in repaired_paths:
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                    "FAIL", "isolated event-id repair executor reused repaired path", "SCHEMA_IDENTITY_MISMATCH"
                )
            repaired_paths.add(repaired_path)
            if (
                cycle.get("candidate_repair_is_current_evidence") is not False
                or cycle.get("current_canonical_ledger_write_allowed") is not False
                or cycle.get("target_rollup_write_allowed") is not False
                or cycle.get("current_evidence_write_allowed") is not False
                or cycle.get("live_permission_created") is not False
            ):
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                    "BLOCKED", "isolated event-id repair executor cycle attempted forbidden permission",
                    "LIVE_FINAL_GUARD_FAILED",
                )
            if cycle.get("candidate_repair_artifact_ready") is True:
                item_counts["candidate_repair_ready_count"] += 1
                if cycle.get("post_repair_chain_status") != "PASS" or cycle.get("post_repair_duplicate_event_id_count") != 0:
                    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                        "FAIL", "isolated event-id repair executor marked invalid repaired ledger ready",
                        "LEDGER_INTEGRITY_FAIL",
                    )
            if cycle.get("candidate_repair_written") is True:
                item_counts["candidate_repair_written_count"] += 1
            if cycle.get("candidate_repair_reused_existing") is True:
                item_counts["candidate_repair_reused_existing_count"] += 1
            item_counts["event_id_updated_count"] += int(cycle.get("event_id_updated_count") or 0)
            item_counts["event_hash_recalculation_count"] += int(cycle.get("event_hash_recalculation_count") or 0)
            repaired_event_ids = cycle.get("repaired_event_ids")
            if not isinstance(repaired_event_ids, list):
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                    "FAIL", "isolated event-id repair executor repaired event ids missing",
                    "SCHEMA_IDENTITY_MISMATCH",
                )
            item_repaired_event_ids.extend(str(event_id) for event_id in repaired_event_ids)
        item_counts["post_repair_duplicate_event_id_count"] = _duplicate_string_count(item_repaired_event_ids)
        global_repaired_event_ids.extend(item_repaired_event_ids)
        expected_blocked = len(cycles) - item_counts["candidate_repair_ready_count"]
        if (
            item.get("candidate_repair_ready_count") != item_counts["candidate_repair_ready_count"]
            or item.get("candidate_repair_blocked_count") != expected_blocked
            or item.get("candidate_repair_written_count") != item_counts["candidate_repair_written_count"]
            or item.get("candidate_repair_reused_existing_count") != item_counts["candidate_repair_reused_existing_count"]
            or item.get("event_id_updated_count") != item_counts["event_id_updated_count"]
            or item.get("event_hash_recalculation_count") != item_counts["event_hash_recalculation_count"]
            or item.get("post_repair_duplicate_event_id_count") != item_counts["post_repair_duplicate_event_id_count"]
        ):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                "FAIL", "isolated event-id repair executor item aggregate mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        totals["candidate_repair_cycle_count"] += len(cycles)
        totals["candidate_repair_ready_count"] += item_counts["candidate_repair_ready_count"]
        totals["candidate_repair_blocked_count"] += expected_blocked
        for field in (
            "candidate_repair_written_count",
            "candidate_repair_reused_existing_count",
            "event_id_updated_count",
            "event_hash_recalculation_count",
        ):
            totals[field] += item_counts[field]
    totals["candidate_repair_artifact_ready_count"] = totals["candidate_repair_ready_count"]
    totals["post_repair_duplicate_event_id_count"] = _duplicate_string_count(global_repaired_event_ids)
    for field, value in totals.items():
        if report.get(field) != value:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                "FAIL", f"isolated event-id repair executor aggregate mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("candidate_repair_write_enabled") is True:
        if report.get("actual_candidate_repair_performed") is not True:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                "FAIL", "isolated event-id repair executor enabled writes without candidate repair evidence",
                "SCHEMA_IDENTITY_MISMATCH",
            )
        if report.get("candidate_repair_ready_count") != report.get("candidate_repair_cycle_count"):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
                "FAIL", "isolated event-id repair executor enabled writes without full readiness",
                ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_INPUT_BLOCKED_CODE,
            )
    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorValidationResult(
        "PASS", "isolated event-id repair executor writes candidate-only repaired ledgers and blocks current/live",
        None,
    )
