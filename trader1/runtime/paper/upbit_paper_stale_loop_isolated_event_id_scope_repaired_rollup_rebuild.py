from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.core.ledger.paper_ledger import (
    count_incomplete_upbit_paper_order_lifecycles,
    validate_upbit_paper_ledger,
)
from trader1.runtime.ledger.execution_ledger import validate_ledger_chain
from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repair_executor import (
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json, recover_jsonl_records


UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report.v1"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_CANDIDATE_ONLY"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_TRUTH_ROLE = (
    "paper_runtime_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_truth"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_BLOCKER_CODE = (
    "ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_CURRENT_EVIDENCE_BLOCKED"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_INPUT_BLOCKER_CODE = (
    "ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_INPUT_BLOCKED"
)


@dataclass(frozen=True)
class UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_hash(
    report: dict[str, Any],
) -> str:
    payload = dict(report)
    payload.pop("event_id_scope_repaired_rollup_rebuild_hash", None)
    return _sha256_json(payload)


def event_id_repaired_candidate_rollup_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("candidate_rollup_hash", None)
    return _sha256_json(payload)


def _event_id_repaired_candidate_rollup_semantic_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("generated_at_utc", None)
    payload.pop("candidate_rollup_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _safe_name(value: str, limit: int = 32) -> str:
    sanitized = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value)
    if len(sanitized) <= limit:
        return sanitized
    return f"{sanitized[:limit]}-{_sha256_bytes(value.encode('utf-8'))[:12]}"


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


def _candidate_rollup_path(session_id: str, replacement_loop_id: str) -> str:
    return (
        f"{_candidate_root_prefix(session_id)}{_safe_name(replacement_loop_id)}/"
        "eid_repair/rollup/repaired_isolated_rollup.json"
    )


def _load_ledger_records(path: Path) -> tuple[list[dict[str, Any]], str, str | None, str | None]:
    try:
        path.read_bytes()
    except FileNotFoundError:
        return [], "MISSING", None, None
    except OSError:
        return [], "UNREADABLE", None, None
    records, quarantine_path = recover_jsonl_records(path)
    quarantine_rel = quarantine_path.as_posix() if quarantine_path is not None else None
    normalized = ("\n".join(json.dumps(record, sort_keys=True, separators=(",", ":")) for record in records) + "\n")
    return records, "PASS", _sha256_bytes(normalized.encode("utf-8")), quarantine_rel


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _event_duplicate_counts(records_by_cycle: list[list[dict[str, Any]]]) -> tuple[int, int, list[dict[str, str]]]:
    seen_event_ids: set[str] = set()
    seen_dedup_keys: set[str] = set()
    seen_fill_keys: set[tuple[Any, Any]] = set()
    duplicate_event_count = 0
    duplicate_order_count = 0
    blockers: list[dict[str, str]] = []
    for records in records_by_cycle:
        for event in records:
            event_id = str(event.get("event_id"))
            dedup_key = str(event.get("dedup_key"))
            if event_id in seen_event_ids:
                duplicate_event_count += 1
                blockers.append(_blocker("RECONCILIATION_REQUIRED", f"duplicate repaired event_id: {event_id}"))
            seen_event_ids.add(event_id)
            if dedup_key in seen_dedup_keys:
                duplicate_event_count += 1
                blockers.append(_blocker("RECONCILIATION_REQUIRED", f"duplicate repaired dedup_key: {dedup_key}"))
            seen_dedup_keys.add(dedup_key)
            if event.get("event_type") == "ORDER_FILLED":
                fill_key = (event.get("client_order_id"), event.get("order_id"))
                if fill_key in seen_fill_keys:
                    duplicate_order_count += 1
                    blockers.append(_blocker("RECONCILIATION_REQUIRED", "duplicate repaired filled PAPER order"))
                seen_fill_keys.add(fill_key)
    return duplicate_event_count, duplicate_order_count, blockers


def _write_candidate_rollup(*, root: Path, path: str, candidate_rollup: dict[str, Any]) -> tuple[str, bool, bool]:
    target = _rooted(root, path)
    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return "BLOCKED_EXISTING_UNREADABLE", False, False
        if isinstance(existing, dict) and existing.get("candidate_rollup_hash") == candidate_rollup.get(
            "candidate_rollup_hash"
        ):
            return "REUSED_EXISTING_MATCH", False, True
        if isinstance(existing, dict) and _event_id_repaired_candidate_rollup_semantic_hash(
            existing
        ) == _event_id_repaired_candidate_rollup_semantic_hash(candidate_rollup):
            return "REUSED_EXISTING_MATCH", False, True
        return "BLOCKED_EXISTING_MISMATCH", False, False
    durable_atomic_write_json(target, candidate_rollup)
    return "WRITTEN", True, False


def _build_cycle(*, root: Path, session_id: str, source_cycle: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = str(source_cycle.get("repaired_ledger_path") or "")
    expected_hash = source_cycle.get("repaired_ledger_hash")
    records, load_status, file_hash, quarantine_path = _load_ledger_records(_rooted(root, path))
    hash_match = isinstance(expected_hash, str) and file_hash == expected_hash
    repaired_event_count_match = len(records) == int(source_cycle.get("repaired_ledger_event_count") or 0)
    chain_result = validate_ledger_chain(records) if load_status == "PASS" else None
    ledger_status = "PASS"
    ledger_blocker_code = None
    ledger_message = "repaired ledger valid"
    lifecycle_count = 0
    if load_status != "PASS":
        ledger_status = "BLOCKED"
        ledger_blocker_code = ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_INPUT_BLOCKER_CODE
        ledger_message = f"repaired ledger load status: {load_status}"
    elif records:
        lifecycle_count = count_incomplete_upbit_paper_order_lifecycles(records)
        chain_status = chain_result.status if chain_result is not None else "BLOCKED"
        if chain_status != "PASS":
            ledger_status = chain_status
            ledger_blocker_code = chain_result.blocker_code if chain_result is not None else "LEDGER_INTEGRITY_FAIL"
            ledger_message = chain_result.message if chain_result is not None else "repaired ledger chain unavailable"
        else:
            ledger_status, ledger_blocker_code, ledger_message = validate_upbit_paper_ledger(records)
    else:
        ledger_status = "BLOCKED"
        ledger_blocker_code = "LEDGER_UNAVAILABLE"
        ledger_message = "repaired ledger is empty"
    scope_mismatch_count = sum(
        1
        for event in records
        if event.get("exchange") != "UPBIT"
        or event.get("market_type") != "KRW_SPOT"
        or event.get("mode") != "PAPER"
        or event.get("session_id") != session_id
    )
    if scope_mismatch_count:
        ledger_status = "BLOCKED"
        ledger_blocker_code = "SNAPSHOT_SCOPE_MISMATCH"
        ledger_message = "repaired ledger contains cross-scope events"
    return (
        {
            "cycle_id": str(source_cycle.get("cycle_id") or "UNKNOWN"),
            "replacement_loop_id": str(source_cycle.get("replacement_loop_id") or "UNKNOWN"),
            "source_ledger_path": source_cycle.get("source_ledger_path"),
            "repaired_ledger_path": path,
            "repaired_ledger_path_allowed": _candidate_path_allowed(path, session_id),
            "repaired_ledger_exists": load_status == "PASS",
            "repaired_ledger_hash": file_hash,
            "source_expected_repaired_hash": expected_hash,
            "repaired_hash_match": hash_match,
            "repaired_ledger_load_status": load_status,
            "repaired_ledger_event_count": len(records),
            "source_repaired_ledger_event_count": int(source_cycle.get("repaired_ledger_event_count") or 0),
            "repaired_event_count_match": repaired_event_count_match,
            "repaired_ledger_chain_status": chain_result.status if chain_result is not None else "NOT_RUN",
            "repaired_ledger_chain_blocker_code": chain_result.blocker_code if chain_result is not None else None,
            "repaired_ledger_validator_status": ledger_status,
            "repaired_ledger_validator_blocker_code": ledger_blocker_code,
            "repaired_ledger_validator_message": ledger_message,
            "event_id_updated_count": int(source_cycle.get("event_id_updated_count") or 0),
            "event_hash_recalculation_count": int(source_cycle.get("event_hash_recalculation_count") or 0),
            "post_repair_duplicate_event_id_count": int(source_cycle.get("post_repair_duplicate_event_id_count") or 0),
            "lifecycle_incomplete_order_count": lifecycle_count,
            "scope_mismatch_count": scope_mismatch_count,
            "quarantine_path": quarantine_path,
            "candidate_rollup_current_evidence_usable": False,
            "current_evidence_write_allowed": False,
            "live_permission_created": False,
        },
        records,
    )


def _build_candidate(
    *,
    root: Path,
    session_id: str,
    source_item: dict[str, Any],
    priority_order: int,
    candidate_rollup_write_enabled: bool,
) -> dict[str, Any]:
    replacement_loop_id = str(source_item.get("replacement_loop_id") or "UNKNOWN")
    cycle_pairs = [
        _build_cycle(root=root, session_id=session_id, source_cycle=cycle)
        for cycle in source_item.get("cycles", [])
        if isinstance(cycle, dict)
    ]
    cycles = [pair[0] for pair in cycle_pairs]
    records_by_cycle = [pair[1] for pair in cycle_pairs]
    all_events = [event for records in records_by_cycle for event in records]
    filled_events = [event for event in all_events if event.get("event_type") == "ORDER_FILLED"]
    duplicate_event_count, duplicate_order_count, duplicate_blockers = _event_duplicate_counts(records_by_cycle)
    invalid_count = sum(1 for cycle in cycles if cycle["repaired_ledger_validator_status"] != "PASS")
    missing_count = sum(1 for cycle in cycles if cycle["repaired_ledger_exists"] is not True)
    hash_mismatch_count = sum(1 for cycle in cycles if cycle["repaired_hash_match"] is not True)
    chain_invalid_count = sum(1 for cycle in cycles if cycle["repaired_ledger_chain_status"] != "PASS")
    event_count_mismatch_count = sum(1 for cycle in cycles if cycle["repaired_event_count_match"] is not True)
    lifecycle_count = sum(int(cycle["lifecycle_incomplete_order_count"]) for cycle in cycles)
    scope_mismatch_count = sum(int(cycle["scope_mismatch_count"]) for cycle in cycles)
    blockers = list(duplicate_blockers)
    if missing_count:
        blockers.append(_blocker("LEDGER_UNAVAILABLE", "repaired candidate ledger input is missing"))
    if hash_mismatch_count:
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "repaired candidate ledger hash does not match executor source"))
    if chain_invalid_count:
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "repaired candidate ledger chain validation did not pass"))
    if invalid_count:
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "repaired candidate ledger validator did not pass"))
    if event_count_mismatch_count:
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "repaired candidate ledger event count drifted"))
    if lifecycle_count:
        blockers.append(_blocker("RECONCILIATION_REQUIRED", "repaired candidate ledger lifecycle is incomplete"))
    if scope_mismatch_count:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "repaired candidate ledger scope mismatch"))
    candidate_status = "PASS_CURRENT_EVIDENCE_BLOCKED" if not blockers and cycles else "BLOCKED"
    candidate_artifact_path = _candidate_rollup_path(session_id, replacement_loop_id)
    candidate_rollup = {
        "schema_id": "trader1.event_id_repaired_candidate_ledger_rollup.v1",
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "candidate_rollup_id": f"{replacement_loop_id}-event-id-repaired-rollup",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "replacement_loop_id": replacement_loop_id,
        "ledger_input_scope": "ISOLATED_EVENT_ID_REPAIRED_CANDIDATE_MIRROR_PATHS",
        "ledger_jsonl_count": len(cycles),
        "ledger_event_count": len(all_events),
        "filled_order_count": len(filled_events),
        "duplicate_event_count": duplicate_event_count,
        "duplicate_order_count": duplicate_order_count,
        "lifecycle_incomplete_order_count": lifecycle_count,
        "invalid_ledger_jsonl_count": invalid_count,
        "missing_ledger_jsonl_count": missing_count,
        "hash_mismatch_count": hash_mismatch_count,
        "chain_invalid_count": chain_invalid_count,
        "scope_mismatch_count": scope_mismatch_count,
        "event_count_mismatch_count": event_count_mismatch_count,
        "event_id_updated_count": int(source_item.get("event_id_updated_count") or 0),
        "event_hash_recalculation_count": int(source_item.get("event_hash_recalculation_count") or 0),
        "post_repair_duplicate_event_id_count": int(source_item.get("post_repair_duplicate_event_id_count") or 0),
        "latest_ledger_head_hash": all_events[-1].get("event_hash") if all_events else None,
        "artifact_paths": [cycle["repaired_ledger_path"] for cycle in cycles],
        "candidate_status": candidate_status,
        "primary_blocker_code": ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_BLOCKER_CODE
        if candidate_status == "PASS_CURRENT_EVIDENCE_BLOCKED"
        else blockers[0]["code"]
        if blockers
        else ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_INPUT_BLOCKER_CODE,
        "blockers": blockers,
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "candidate_only": True,
        "candidate_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "target_rollup_write_allowed": False,
        "actual_long_run_evidence_created": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "candidate_rollup_hash": "",
    }
    candidate_rollup["candidate_rollup_hash"] = event_id_repaired_candidate_rollup_hash(candidate_rollup)
    write_status = "WRITE_DISABLED"
    written = False
    reused = False
    if candidate_rollup_write_enabled:
        if candidate_status == "PASS_CURRENT_EVIDENCE_BLOCKED":
            write_status, written, reused = _write_candidate_rollup(
                root=root, path=candidate_artifact_path, candidate_rollup=candidate_rollup
            )
        else:
            write_status = "BLOCKED_CANDIDATE_ROLLUP_STATUS"
    return {
        "priority_order": priority_order,
        "replacement_loop_id": replacement_loop_id,
        "source_executor_item_status": source_item.get("executor_item_status"),
        "candidate_rollup_artifact_path": candidate_artifact_path,
        "candidate_rollup_artifact_path_allowed": _candidate_path_allowed(candidate_artifact_path, session_id),
        "candidate_rollup_write_status": write_status,
        "candidate_rollup_written": written,
        "candidate_rollup_reused_existing": reused,
        "candidate_rollup_artifact_ready": write_status in {"WRITTEN", "REUSED_EXISTING_MATCH"},
        "candidate_rollup_status": candidate_status,
        "candidate_rollup_hash": candidate_rollup["candidate_rollup_hash"],
        "ledger_jsonl_count": len(cycles),
        "ledger_event_count": len(all_events),
        "filled_order_count": len(filled_events),
        "duplicate_event_count": duplicate_event_count,
        "duplicate_order_count": duplicate_order_count,
        "lifecycle_incomplete_order_count": lifecycle_count,
        "invalid_ledger_jsonl_count": invalid_count,
        "missing_ledger_jsonl_count": missing_count,
        "hash_mismatch_count": hash_mismatch_count,
        "chain_invalid_count": chain_invalid_count,
        "scope_mismatch_count": scope_mismatch_count,
        "event_count_mismatch_count": event_count_mismatch_count,
        "event_id_updated_count": int(source_item.get("event_id_updated_count") or 0),
        "event_hash_recalculation_count": int(source_item.get("event_hash_recalculation_count") or 0),
        "post_repair_duplicate_event_id_count": int(source_item.get("post_repair_duplicate_event_id_count") or 0),
        "cycles": cycles,
        "candidate_rollup": candidate_rollup,
        "primary_blocker_code": ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_BLOCKER_CODE
        if candidate_status == "PASS_CURRENT_EVIDENCE_BLOCKED"
        else candidate_rollup["primary_blocker_code"],
        "blocker_codes": sorted(
            {
                ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_BLOCKER_CODE,
                candidate_rollup["primary_blocker_code"],
                *(blocker["code"] for blocker in blockers),
            }
        ),
        "candidate_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "target_rollup_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
    *,
    root: Path,
    event_id_scope_repair_executor_report: dict[str, Any],
    event_id_scope_repaired_rollup_rebuild_id: str = "upbit-paper-stale-loop-isolated-event-id-scope-repaired-rollup-rebuild",
    candidate_rollup_write_enabled: bool = False,
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(
        event_id_scope_repair_executor_report
    )
    session_id = str(event_id_scope_repair_executor_report.get("session_id", "UNKNOWN"))
    source_items = [
        item
        for item in event_id_scope_repair_executor_report.get("items", [])
        if isinstance(item, dict) and item.get("executor_item_status") == "CANDIDATE_REPAIR_READY_CURRENT_EVIDENCE_BLOCKED"
    ]
    items = [
        _build_candidate(
            root=root,
            session_id=session_id,
            source_item=item,
            priority_order=index,
            candidate_rollup_write_enabled=candidate_rollup_write_enabled,
        )
        for index, item in enumerate(source_items, start=1)
    ]
    pass_count = sum(1 for item in items if item["candidate_rollup_status"] == "PASS_CURRENT_EVIDENCE_BLOCKED")
    blocked_count = len(items) - pass_count
    artifact_ready_count = sum(1 for item in items if item["candidate_rollup_artifact_ready"])
    written_count = sum(1 for item in items if item["candidate_rollup_written"])
    reused_count = sum(1 for item in items if item["candidate_rollup_reused_existing"])
    blocker_codes = {ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_BLOCKER_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_INPUT_BLOCKER_CODE)
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    if blocked_count:
        blocker_codes.add(ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_INPUT_BLOCKER_CODE)
    if not candidate_rollup_write_enabled:
        rebuild_status = "WRITE_DISABLED_CURRENT_EVIDENCE_BLOCKED"
    elif items and pass_count == len(items) and artifact_ready_count == len(items):
        rebuild_status = "REPAIRED_CANDIDATE_ROLLUPS_READY_CURRENT_EVIDENCE_BLOCKED"
    else:
        rebuild_status = "BLOCKED"
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "event_id_scope_repaired_rollup_rebuild_id": event_id_scope_repaired_rollup_rebuild_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_TRUTH_ROLE,
        "event_id_scope_repaired_rollup_rebuild_role": ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_ROLE,
        "source_event_id_scope_repair_executor_hash": event_id_scope_repair_executor_report.get(
            "event_id_scope_repair_executor_hash"
        ),
        "source_event_id_scope_repair_executor_status": event_id_scope_repair_executor_report.get("executor_status"),
        "source_event_id_scope_repair_executor_validator_status": source_result.status,
        "source_candidate_repair_ready_count": event_id_scope_repair_executor_report.get("candidate_repair_ready_count"),
        "candidate_count": len(items),
        "candidate_rollup_attempt_count": len(items),
        "candidate_rollup_pass_count": pass_count,
        "candidate_rollup_blocked_count": blocked_count,
        "candidate_rollup_artifact_ready_count": artifact_ready_count,
        "candidate_rollup_written_count": written_count,
        "candidate_rollup_reused_existing_count": reused_count,
        "ledger_jsonl_count": sum(int(item["ledger_jsonl_count"]) for item in items),
        "ledger_event_count": sum(int(item["ledger_event_count"]) for item in items),
        "filled_order_count": sum(int(item["filled_order_count"]) for item in items),
        "duplicate_event_count": sum(int(item["duplicate_event_count"]) for item in items),
        "duplicate_order_count": sum(int(item["duplicate_order_count"]) for item in items),
        "lifecycle_incomplete_order_count": sum(int(item["lifecycle_incomplete_order_count"]) for item in items),
        "invalid_ledger_jsonl_count": sum(int(item["invalid_ledger_jsonl_count"]) for item in items),
        "missing_ledger_jsonl_count": sum(int(item["missing_ledger_jsonl_count"]) for item in items),
        "hash_mismatch_count": sum(int(item["hash_mismatch_count"]) for item in items),
        "chain_invalid_count": sum(int(item["chain_invalid_count"]) for item in items),
        "scope_mismatch_count": sum(int(item["scope_mismatch_count"]) for item in items),
        "event_count_mismatch_count": sum(int(item["event_count_mismatch_count"]) for item in items),
        "event_id_updated_count": sum(int(item["event_id_updated_count"]) for item in items),
        "event_hash_recalculation_count": sum(int(item["event_hash_recalculation_count"]) for item in items),
        "post_repair_duplicate_event_id_count": sum(int(item["post_repair_duplicate_event_id_count"]) for item in items),
        "candidate_current_evidence_usable_count": 0,
        "target_rollup_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "rebuild_status": rebuild_status,
        "primary_blocker_code": ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Run repaired-rollup duplicate reconciliation recheck before any current-evidence promotion guard.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "candidate_only": True,
        "candidate_rollup_write_enabled": bool(candidate_rollup_write_enabled),
        "candidate_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "target_rollup_write_allowed": False,
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
        "event_id_scope_repaired_rollup_rebuild_hash": "",
    }
    report["event_id_scope_repaired_rollup_rebuild_hash"] = (
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_hash(report)
    )
    return report


def write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "event_id_scope_repaired_rollup_rebuild_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "event_id_scope_repaired_rollup_rebuild_role",
        "source_event_id_scope_repair_executor_hash",
        "source_event_id_scope_repair_executor_status",
        "source_event_id_scope_repair_executor_validator_status",
        "source_candidate_repair_ready_count",
        "candidate_count",
        "candidate_rollup_attempt_count",
        "candidate_rollup_pass_count",
        "candidate_rollup_blocked_count",
        "candidate_rollup_artifact_ready_count",
        "candidate_rollup_written_count",
        "candidate_rollup_reused_existing_count",
        "ledger_jsonl_count",
        "ledger_event_count",
        "filled_order_count",
        "duplicate_event_count",
        "duplicate_order_count",
        "lifecycle_incomplete_order_count",
        "invalid_ledger_jsonl_count",
        "missing_ledger_jsonl_count",
        "hash_mismatch_count",
        "chain_invalid_count",
        "scope_mismatch_count",
        "event_count_mismatch_count",
        "event_id_updated_count",
        "event_hash_recalculation_count",
        "post_repair_duplicate_event_id_count",
        "candidate_current_evidence_usable_count",
        "target_rollup_write_allowed_count",
        "current_evidence_write_allowed_count",
        "rebuild_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "candidate_only",
        "candidate_rollup_write_enabled",
        "candidate_current_evidence_usable",
        "current_evidence_write_allowed",
        "target_rollup_write_allowed",
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
        "event_id_scope_repaired_rollup_rebuild_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
            "FAIL", f"event-id repaired rollup rebuild missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_SCHEMA_ID:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
            "FAIL", "event-id repaired rollup rebuild schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("event_id_scope_repaired_rollup_rebuild_hash") != (
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_hash(report)
    ):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
            "FAIL", "event-id repaired rollup rebuild hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
            "BLOCKED", "event-id repaired rollup rebuild scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    false_fields = (
        "candidate_current_evidence_usable",
        "current_evidence_write_allowed",
        "target_rollup_write_allowed",
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
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
            "BLOCKED", "event-id repaired rollup rebuild attempted current evidence or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("candidate_current_evidence_usable_count") != 0
        or report.get("target_rollup_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
    ):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
            "BLOCKED", "event-id repaired rollup rebuild exposed forbidden current evidence counts", "LIVE_FINAL_GUARD_FAILED"
        )
    if report.get("primary_blocker_code") != ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_BLOCKER_CODE:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
            "FAIL", "event-id repaired rollup rebuild primary blocker drifted", "SCHEMA_IDENTITY_MISMATCH"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("candidate_count") != len(items) or report.get(
        "candidate_rollup_attempt_count"
    ) != len(items):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
            "FAIL", "event-id repaired rollup rebuild item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    session_id = str(report.get("session_id"))
    sums = {
        "candidate_rollup_pass_count": 0,
        "candidate_rollup_blocked_count": 0,
        "candidate_rollup_artifact_ready_count": 0,
        "candidate_rollup_written_count": 0,
        "candidate_rollup_reused_existing_count": 0,
        "ledger_jsonl_count": 0,
        "ledger_event_count": 0,
        "filled_order_count": 0,
        "duplicate_event_count": 0,
        "duplicate_order_count": 0,
        "lifecycle_incomplete_order_count": 0,
        "invalid_ledger_jsonl_count": 0,
        "missing_ledger_jsonl_count": 0,
        "hash_mismatch_count": 0,
        "chain_invalid_count": 0,
        "scope_mismatch_count": 0,
        "event_count_mismatch_count": 0,
        "event_id_updated_count": 0,
        "event_hash_recalculation_count": 0,
        "post_repair_duplicate_event_id_count": 0,
    }
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or item.get("priority_order") != index:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
                "FAIL", "event-id repaired rollup rebuild priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if not _candidate_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
                "BLOCKED", "event-id repaired candidate rollup path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
            )
        item_false = (
            "candidate_current_evidence_usable",
            "current_evidence_write_allowed",
            "target_rollup_write_allowed",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "actual_long_run_evidence_created",
            "live_permission_created",
        )
        if any(item.get(field) is not False for field in item_false):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
                "BLOCKED", "event-id repaired rollup item attempted forbidden write or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        candidate_rollup = item.get("candidate_rollup")
        if not isinstance(candidate_rollup, dict) or candidate_rollup.get(
            "candidate_rollup_hash"
        ) != event_id_repaired_candidate_rollup_hash(candidate_rollup):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
                "FAIL", "event-id repaired candidate rollup hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if candidate_rollup.get("candidate_current_evidence_usable") is not False or candidate_rollup.get(
            "live_order_allowed"
        ) is not False:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
                "BLOCKED", "event-id repaired candidate rollup attempted current evidence or live permission",
                "LIVE_FINAL_GUARD_FAILED",
            )
        cycles = item.get("cycles")
        if not isinstance(cycles, list) or item.get("ledger_jsonl_count") != len(cycles):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
                "FAIL", "event-id repaired rollup cycle count mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for cycle in cycles:
            if not isinstance(cycle, dict) or not _candidate_path_allowed(
                str(cycle.get("repaired_ledger_path") or ""), session_id
            ):
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
                    "BLOCKED", "event-id repaired rollup cycle path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
            if cycle.get("candidate_rollup_current_evidence_usable") is not False or cycle.get(
                "live_permission_created"
            ) is not False:
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
                    "BLOCKED", "event-id repaired rollup cycle attempted current evidence or live permission",
                    "LIVE_FINAL_GUARD_FAILED",
                )
        if item.get("candidate_rollup_status") == "PASS_CURRENT_EVIDENCE_BLOCKED":
            sums["candidate_rollup_pass_count"] += 1
        else:
            sums["candidate_rollup_blocked_count"] += 1
        if item.get("candidate_rollup_artifact_ready") is True:
            sums["candidate_rollup_artifact_ready_count"] += 1
        if item.get("candidate_rollup_written") is True:
            sums["candidate_rollup_written_count"] += 1
        if item.get("candidate_rollup_reused_existing") is True:
            sums["candidate_rollup_reused_existing_count"] += 1
        for field in (
            "ledger_jsonl_count",
            "ledger_event_count",
            "filled_order_count",
            "duplicate_event_count",
            "duplicate_order_count",
            "lifecycle_incomplete_order_count",
            "invalid_ledger_jsonl_count",
            "missing_ledger_jsonl_count",
            "hash_mismatch_count",
            "chain_invalid_count",
            "scope_mismatch_count",
            "event_count_mismatch_count",
            "event_id_updated_count",
            "event_hash_recalculation_count",
            "post_repair_duplicate_event_id_count",
        ):
            sums[field] += int(item.get(field) or 0)
    for field, value in sums.items():
        if report.get(field) != value:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
                "FAIL", f"event-id repaired rollup aggregate mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("rebuild_status") == "REPAIRED_CANDIDATE_ROLLUPS_READY_CURRENT_EVIDENCE_BLOCKED":
        if (
            report.get("candidate_rollup_pass_count") != len(items)
            or report.get("candidate_rollup_artifact_ready_count") != len(items)
            or report.get("duplicate_event_count") != 0
            or report.get("chain_invalid_count") != 0
            or report.get("hash_mismatch_count") != 0
        ):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
                "FAIL", "ready event-id repaired rollup rebuild must have clean candidate-only inputs",
                "SCHEMA_IDENTITY_MISMATCH",
            )
    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildValidationResult(
        "PASS", "event-id repaired candidate rollups are rebuilt and current evidence/live remain blocked", None
    )
