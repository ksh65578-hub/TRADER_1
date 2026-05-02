from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild import (
    event_id_repaired_candidate_rollup_hash,
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json, recover_jsonl_records


UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report.v1"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_CANDIDATE_ONLY"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_TRUTH_ROLE = (
    "paper_runtime_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_truth"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_BLOCKER_CODE = (
    "ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_CURRENT_EVIDENCE_BLOCKED"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_INPUT_BLOCKER_CODE = (
    "ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_INPUT_BLOCKED"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_RECONCILIATION_BLOCKER_CODE = (
    "ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_RECONCILIATION_REQUIRED"
)


@dataclass(frozen=True)
class UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_hash(
    report: dict[str, Any],
) -> str:
    payload = dict(report)
    payload.pop("event_id_scope_repaired_duplicate_recheck_hash", None)
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


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _load_json(root: Path, relative_path: str) -> tuple[dict[str, Any] | None, str]:
    try:
        loaded = json.loads(_rooted(root, relative_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "MISSING"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "UNREADABLE"
    if not isinstance(loaded, dict):
        return None, "INVALID"
    return loaded, "PASS"


def _load_records(root: Path, relative_path: str) -> tuple[list[dict[str, Any]], str, str | None]:
    try:
        records, quarantine_path = recover_jsonl_records(_rooted(root, relative_path))
    except FileNotFoundError:
        return [], "MISSING", None
    except OSError:
        return [], "UNREADABLE", None
    return records, "PASS", quarantine_path.as_posix() if quarantine_path is not None else None


def _event_context(*, cycle_id: str, ledger_path: str, event_index: int, event: dict[str, Any]) -> dict[str, Any]:
    return {
        "cycle_id": cycle_id,
        "ledger_path": ledger_path,
        "event_index": event_index,
        "event_type": event.get("event_type"),
        "event_id": event.get("event_id"),
        "dedup_key": event.get("dedup_key"),
        "client_order_id": event.get("client_order_id"),
        "order_id": event.get("order_id"),
        "event_hash": event.get("event_hash"),
    }


def _filled_order_key(event: dict[str, Any]) -> str | None:
    if event.get("event_type") != "ORDER_FILLED":
        return None
    return json.dumps([event.get("client_order_id"), event.get("order_id")], separators=(",", ":"))


def _duplicate_groups(
    *,
    groups: dict[str, list[dict[str, Any]]],
    duplicate_key_type: str,
    resolution_hint: str,
) -> list[dict[str, Any]]:
    duplicates: list[dict[str, Any]] = []
    for key, occurrences in sorted(groups.items()):
        if len(occurrences) < 2:
            continue
        duplicates.append(
            {
                "duplicate_key_type": duplicate_key_type,
                "duplicate_key_value": key,
                "occurrence_count": len(occurrences),
                "duplicate_count": len(occurrences) - 1,
                "affected_cycle_ids": sorted({str(item.get("cycle_id")) for item in occurrences}),
                "affected_ledger_paths": sorted({str(item.get("ledger_path")) for item in occurrences}),
                "event_types": sorted({str(item.get("event_type")) for item in occurrences}),
                "occurrences": occurrences,
                "resolution_hint": resolution_hint,
                "current_evidence_write_allowed": False,
                "live_permission_created": False,
            }
        )
    return duplicates


def _source_cycle_ids(source_item: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for cycle in source_item.get("cycles", []):
        if not isinstance(cycle, dict):
            continue
        repaired_path = cycle.get("repaired_ledger_path")
        if isinstance(repaired_path, str):
            mapping[repaired_path] = str(cycle.get("cycle_id") or "UNKNOWN")
    return mapping


def _build_candidate(*, root: Path, session_id: str, source_item: dict[str, Any], priority_order: int) -> dict[str, Any]:
    replacement_loop_id = str(source_item.get("replacement_loop_id") or "UNKNOWN")
    candidate_rollup_path = str(source_item.get("candidate_rollup_artifact_path") or "")
    candidate_rollup, candidate_rollup_load_status = _load_json(root, candidate_rollup_path)
    load_blockers: list[dict[str, str]] = []
    if not _candidate_path_allowed(candidate_rollup_path, session_id):
        load_blockers.append(
            _blocker("SNAPSHOT_SCOPE_MISMATCH", "repaired duplicate recheck candidate rollup path escaped candidate namespace")
        )
    if candidate_rollup_load_status != "PASS":
        load_blockers.append(
            _blocker(
                ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_INPUT_BLOCKER_CODE,
                f"repaired duplicate recheck could not load candidate rollup: {candidate_rollup_load_status}",
            )
        )
        candidate_rollup = {}
    expected_hash = source_item.get("candidate_rollup_hash")
    actual_hash = event_id_repaired_candidate_rollup_hash(candidate_rollup) if candidate_rollup else None
    candidate_rollup_hash_match = bool(actual_hash and actual_hash == expected_hash)
    if candidate_rollup and not candidate_rollup_hash_match:
        load_blockers.append(
            _blocker("LEDGER_INTEGRITY_FAIL", "repaired duplicate recheck candidate rollup hash mismatch")
        )

    cycle_ids = _source_cycle_ids(source_item)
    by_event_id: dict[str, list[dict[str, Any]]] = {}
    by_dedup_key: dict[str, list[dict[str, Any]]] = {}
    by_filled_order_key: dict[str, list[dict[str, Any]]] = {}
    cycles: list[dict[str, Any]] = []
    event_count = 0
    filled_order_count = 0

    for ledger_path in candidate_rollup.get("artifact_paths", []):
        if not isinstance(ledger_path, str):
            continue
        cycle_id = cycle_ids.get(ledger_path, "UNKNOWN")
        records, load_status, quarantine_path = _load_records(root, ledger_path)
        ledger_path_allowed = _candidate_path_allowed(ledger_path, session_id)
        if not ledger_path_allowed:
            load_blockers.append(
                _blocker("SNAPSHOT_SCOPE_MISMATCH", "repaired duplicate recheck ledger path escaped candidate namespace")
            )
        if load_status != "PASS":
            load_blockers.append(
                _blocker(
                    ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_INPUT_BLOCKER_CODE,
                    f"repaired duplicate recheck could not load ledger {ledger_path}: {load_status}",
                )
            )
        cycles.append(
            {
                "cycle_id": cycle_id,
                "repaired_ledger_path": ledger_path,
                "repaired_ledger_path_allowed": ledger_path_allowed,
                "repaired_ledger_load_status": load_status,
                "repaired_ledger_event_count": len(records),
                "quarantine_path": quarantine_path,
                "current_evidence_write_allowed": False,
                "live_permission_created": False,
            }
        )
        for index, event in enumerate(records):
            if not isinstance(event, dict):
                continue
            event_count += 1
            if event.get("event_type") == "ORDER_FILLED":
                filled_order_count += 1
            context = _event_context(cycle_id=cycle_id, ledger_path=ledger_path, event_index=index, event=event)
            event_id = str(event.get("event_id") or "")
            dedup_key = str(event.get("dedup_key") or "")
            if event_id:
                by_event_id.setdefault(event_id, []).append(context)
            if dedup_key:
                by_dedup_key.setdefault(dedup_key, []).append(context)
            filled_key = _filled_order_key(event)
            if filled_key is not None:
                by_filled_order_key.setdefault(filled_key, []).append(context)

    event_id_duplicate_groups = _duplicate_groups(
        groups=by_event_id,
        duplicate_key_type="EVENT_ID",
        resolution_hint="REPAIR_EVENT_ID_SCOPE_BEFORE_ANY_CURRENT_EVIDENCE_USE",
    )
    dedup_key_duplicate_groups = _duplicate_groups(
        groups=by_dedup_key,
        duplicate_key_type="DEDUP_KEY",
        resolution_hint="RECONCILE_DEDUP_KEY_BEFORE_ANY_CURRENT_EVIDENCE_USE",
    )
    filled_order_duplicate_groups = _duplicate_groups(
        groups=by_filled_order_key,
        duplicate_key_type="FILLED_ORDER",
        resolution_hint="RECONCILE_DUPLICATE_FILL_BEFORE_ANY_POSITION_OR_PNL_USE",
    )
    duplicate_groups = [*event_id_duplicate_groups, *dedup_key_duplicate_groups, *filled_order_duplicate_groups]
    duplicate_total_count = sum(int(group["duplicate_count"]) for group in duplicate_groups)
    duplicate_occurrence_count = sum(int(group["occurrence_count"]) for group in duplicate_groups)
    clean = not load_blockers and not duplicate_groups and bool(cycles)
    blocker_codes = {ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_BLOCKER_CODE}
    if duplicate_groups:
        blocker_codes.update(
            {
                ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_RECONCILIATION_BLOCKER_CODE,
                "RECONCILIATION_REQUIRED",
            }
        )
    for blocker in load_blockers:
        blocker_codes.add(blocker["code"])
    return {
        "priority_order": priority_order,
        "replacement_loop_id": replacement_loop_id,
        "source_candidate_rollup_status": source_item.get("candidate_rollup_status"),
        "candidate_rollup_artifact_path": candidate_rollup_path,
        "candidate_rollup_artifact_path_allowed": _candidate_path_allowed(candidate_rollup_path, session_id),
        "candidate_rollup_load_status": candidate_rollup_load_status,
        "candidate_rollup_hash": actual_hash,
        "source_candidate_rollup_hash": expected_hash,
        "candidate_rollup_hash_match": candidate_rollup_hash_match,
        "candidate_recheck_status": "PASS_CURRENT_EVIDENCE_BLOCKED" if clean else "BLOCKED_RECONCILIATION_REQUIRED",
        "primary_blocker_code": ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_BLOCKER_CODE
        if clean
        else ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_RECONCILIATION_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "ledger_jsonl_count": len(cycles),
        "ledger_event_count": event_count,
        "filled_order_count": filled_order_count,
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_event_id_group_count": len(event_id_duplicate_groups),
        "duplicate_dedup_key_group_count": len(dedup_key_duplicate_groups),
        "duplicate_filled_order_group_count": len(filled_order_duplicate_groups),
        "duplicate_event_id_duplicate_count": sum(int(group["duplicate_count"]) for group in event_id_duplicate_groups),
        "duplicate_dedup_key_duplicate_count": sum(int(group["duplicate_count"]) for group in dedup_key_duplicate_groups),
        "duplicate_filled_order_duplicate_count": sum(int(group["duplicate_count"]) for group in filled_order_duplicate_groups),
        "duplicate_total_count": duplicate_total_count,
        "duplicate_occurrence_count": duplicate_occurrence_count,
        "cycles": cycles,
        "duplicate_groups": duplicate_groups,
        "load_blockers": load_blockers,
        "recommended_next_action": "keep repaired candidate rollup blocked from current evidence promotion guard"
        if clean
        else "repair or quarantine repaired duplicate candidates before any current evidence guard",
        "candidate_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "target_rollup_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "live_permission_created": False,
        "promotion_eligible": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(
    *,
    root: Path,
    event_id_scope_repaired_rollup_rebuild_report: dict[str, Any],
    event_id_scope_repaired_duplicate_recheck_id: str = "upbit-paper-stale-loop-isolated-event-id-scope-repaired-duplicate-recheck",
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
        event_id_scope_repaired_rollup_rebuild_report
    )
    session_id = str(event_id_scope_repaired_rollup_rebuild_report.get("session_id", "UNKNOWN"))
    items = [
        _build_candidate(root=root, session_id=session_id, source_item=item, priority_order=index)
        for index, item in enumerate(event_id_scope_repaired_rollup_rebuild_report.get("items", []), start=1)
        if isinstance(item, dict)
    ]
    affected_items = [item for item in items if item["duplicate_group_count"] > 0]
    blocked_items = [item for item in items if item["candidate_recheck_status"] != "PASS_CURRENT_EVIDENCE_BLOCKED"]
    blocker_codes = {ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_BLOCKER_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_INPUT_BLOCKER_CODE)
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    recheck_status = (
        "REPAIRED_DUPLICATE_RECHECK_PASS_CURRENT_EVIDENCE_BLOCKED"
        if items and not blocked_items and source_result.status == "PASS"
        else "BLOCKED_RECONCILIATION_REQUIRED"
    )
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "event_id_scope_repaired_duplicate_recheck_id": event_id_scope_repaired_duplicate_recheck_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_TRUTH_ROLE,
        "event_id_scope_repaired_duplicate_recheck_role": ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_ROLE,
        "source_event_id_scope_repaired_rollup_rebuild_hash": event_id_scope_repaired_rollup_rebuild_report.get(
            "event_id_scope_repaired_rollup_rebuild_hash"
        ),
        "source_event_id_scope_repaired_rollup_rebuild_status": event_id_scope_repaired_rollup_rebuild_report.get(
            "rebuild_status"
        ),
        "source_event_id_scope_repaired_rollup_rebuild_validator_status": source_result.status,
        "candidate_count": len(items),
        "clean_candidate_count": sum(1 for item in items if item["candidate_recheck_status"] == "PASS_CURRENT_EVIDENCE_BLOCKED"),
        "affected_candidate_count": len(affected_items),
        "blocked_candidate_count": len(blocked_items),
        "candidate_rollup_artifact_checked_count": sum(1 for item in items if item["candidate_rollup_load_status"] == "PASS"),
        "candidate_rollup_artifact_missing_count": sum(1 for item in items if item["candidate_rollup_load_status"] != "PASS"),
        "candidate_rollup_hash_mismatch_count": sum(1 for item in items if item["candidate_rollup_hash_match"] is not True),
        "ledger_jsonl_count": sum(int(item["ledger_jsonl_count"]) for item in items),
        "ledger_event_count": sum(int(item["ledger_event_count"]) for item in items),
        "filled_order_count": sum(int(item["filled_order_count"]) for item in items),
        "duplicate_group_count": sum(int(item["duplicate_group_count"]) for item in items),
        "duplicate_event_id_group_count": sum(int(item["duplicate_event_id_group_count"]) for item in items),
        "duplicate_dedup_key_group_count": sum(int(item["duplicate_dedup_key_group_count"]) for item in items),
        "duplicate_filled_order_group_count": sum(int(item["duplicate_filled_order_group_count"]) for item in items),
        "duplicate_event_id_duplicate_count": sum(int(item["duplicate_event_id_duplicate_count"]) for item in items),
        "duplicate_dedup_key_duplicate_count": sum(int(item["duplicate_dedup_key_duplicate_count"]) for item in items),
        "duplicate_filled_order_duplicate_count": sum(int(item["duplicate_filled_order_duplicate_count"]) for item in items),
        "duplicate_total_count": sum(int(item["duplicate_total_count"]) for item in items),
        "duplicate_occurrence_count": sum(int(item["duplicate_occurrence_count"]) for item in items),
        "current_evidence_write_allowed_count": 0,
        "target_rollup_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "recheck_status": recheck_status,
        "primary_blocker_code": ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_BLOCKER_CODE
        if recheck_status == "REPAIRED_DUPLICATE_RECHECK_PASS_CURRENT_EVIDENCE_BLOCKED"
        else ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_RECONCILIATION_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Proceed only to a candidate-only current-evidence promotion guard; do not mutate current evidence.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "candidate_only": True,
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
        "event_id_scope_repaired_duplicate_recheck_hash": "",
    }
    report["event_id_scope_repaired_duplicate_recheck_hash"] = (
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_hash(report)
    )
    return report


def write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "event_id_scope_repaired_duplicate_recheck_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "event_id_scope_repaired_duplicate_recheck_role",
        "source_event_id_scope_repaired_rollup_rebuild_hash",
        "source_event_id_scope_repaired_rollup_rebuild_status",
        "source_event_id_scope_repaired_rollup_rebuild_validator_status",
        "candidate_count",
        "clean_candidate_count",
        "affected_candidate_count",
        "blocked_candidate_count",
        "candidate_rollup_artifact_checked_count",
        "candidate_rollup_artifact_missing_count",
        "candidate_rollup_hash_mismatch_count",
        "ledger_jsonl_count",
        "ledger_event_count",
        "filled_order_count",
        "duplicate_group_count",
        "duplicate_event_id_group_count",
        "duplicate_dedup_key_group_count",
        "duplicate_filled_order_group_count",
        "duplicate_event_id_duplicate_count",
        "duplicate_dedup_key_duplicate_count",
        "duplicate_filled_order_duplicate_count",
        "duplicate_total_count",
        "duplicate_occurrence_count",
        "current_evidence_write_allowed_count",
        "target_rollup_write_allowed_count",
        "candidate_current_evidence_usable_count",
        "recheck_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "candidate_only",
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
        "event_id_scope_repaired_duplicate_recheck_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
            "FAIL", f"event-id repaired duplicate recheck missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_SCHEMA_ID:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
            "FAIL", "event-id repaired duplicate recheck schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("event_id_scope_repaired_duplicate_recheck_hash") != (
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_hash(report)
    ):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
            "FAIL", "event-id repaired duplicate recheck hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
            "BLOCKED", "event-id repaired duplicate recheck scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if report.get("truth_role") != ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_TRUTH_ROLE:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
            "FAIL", "event-id repaired duplicate recheck truth role mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("event_id_scope_repaired_duplicate_recheck_role") != ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_ROLE:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
            "BLOCKED", "event-id repaired duplicate recheck role cannot claim live or current evidence", "LIVE_FINAL_GUARD_FAILED"
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
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
            "BLOCKED", "event-id repaired duplicate recheck attempted current evidence or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("current_evidence_write_allowed_count") != 0
        or report.get("target_rollup_write_allowed_count") != 0
        or report.get("candidate_current_evidence_usable_count") != 0
    ):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
            "BLOCKED", "event-id repaired duplicate recheck exposed forbidden current evidence counts", "LIVE_FINAL_GUARD_FAILED"
        )
    if not report.get("display_only") or not report.get("dashboard_truth_only") or not report.get("paper_only") or not report.get("candidate_only"):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
            "BLOCKED", "event-id repaired duplicate recheck must remain display-only candidate PAPER evidence", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("candidate_count") != len(items):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
            "FAIL", "event-id repaired duplicate recheck item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    session_id = str(report.get("session_id"))
    sums = {
        "clean_candidate_count": 0,
        "affected_candidate_count": 0,
        "blocked_candidate_count": 0,
        "candidate_rollup_artifact_checked_count": 0,
        "candidate_rollup_artifact_missing_count": 0,
        "candidate_rollup_hash_mismatch_count": 0,
        "ledger_jsonl_count": 0,
        "ledger_event_count": 0,
        "filled_order_count": 0,
        "duplicate_group_count": 0,
        "duplicate_event_id_group_count": 0,
        "duplicate_dedup_key_group_count": 0,
        "duplicate_filled_order_group_count": 0,
        "duplicate_event_id_duplicate_count": 0,
        "duplicate_dedup_key_duplicate_count": 0,
        "duplicate_filled_order_duplicate_count": 0,
        "duplicate_total_count": 0,
        "duplicate_occurrence_count": 0,
    }
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or item.get("priority_order") != index:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                "FAIL", "event-id repaired duplicate recheck priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_false = (
            "candidate_current_evidence_usable",
            "current_evidence_write_allowed",
            "target_rollup_write_allowed",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "live_permission_created",
            "promotion_eligible",
            "scale_up_allowed",
        )
        if any(item.get(field) is not False for field in item_false):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                "BLOCKED", "event-id repaired duplicate recheck item attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
            )
        if not _candidate_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                "BLOCKED", "event-id repaired duplicate recheck candidate rollup path escaped namespace", "SNAPSHOT_SCOPE_MISMATCH"
            )
        if item.get("candidate_recheck_status") == "PASS_CURRENT_EVIDENCE_BLOCKED":
            sums["clean_candidate_count"] += 1
        else:
            sums["blocked_candidate_count"] += 1
        if item.get("duplicate_group_count", 0) > 0:
            sums["affected_candidate_count"] += 1
        if item.get("candidate_rollup_load_status") == "PASS":
            sums["candidate_rollup_artifact_checked_count"] += 1
        else:
            sums["candidate_rollup_artifact_missing_count"] += 1
        if item.get("candidate_rollup_hash_match") is not True:
            sums["candidate_rollup_hash_mismatch_count"] += 1
        for cycle in item.get("cycles", []):
            if not isinstance(cycle, dict) or not _candidate_path_allowed(str(cycle.get("repaired_ledger_path") or ""), session_id):
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                    "BLOCKED", "event-id repaired duplicate recheck cycle path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
            if cycle.get("current_evidence_write_allowed") is not False or cycle.get("live_permission_created") is not False:
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                    "BLOCKED", "event-id repaired duplicate recheck cycle attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
                )
        group_duplicate_sum = 0
        group_occurrence_sum = 0
        for group in item.get("duplicate_groups", []):
            if not isinstance(group, dict) or group.get("duplicate_count") != int(group.get("occurrence_count") or 0) - 1:
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                    "FAIL", "event-id repaired duplicate group count mismatch", "SCHEMA_IDENTITY_MISMATCH"
                )
            for path in group.get("affected_ledger_paths", []):
                if not isinstance(path, str) or not _candidate_path_allowed(path, session_id):
                    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                        "BLOCKED", "event-id repaired duplicate group path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                    )
            if group.get("current_evidence_write_allowed") is not False or group.get("live_permission_created") is not False:
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                    "BLOCKED", "event-id repaired duplicate group attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
                )
            group_duplicate_sum += int(group.get("duplicate_count") or 0)
            group_occurrence_sum += int(group.get("occurrence_count") or 0)
        if item.get("duplicate_total_count") != group_duplicate_sum:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                "FAIL", "event-id repaired duplicate item total mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("duplicate_occurrence_count") != group_occurrence_sum:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                "FAIL", "event-id repaired duplicate item occurrence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for field in (
            "ledger_jsonl_count",
            "ledger_event_count",
            "filled_order_count",
            "duplicate_group_count",
            "duplicate_event_id_group_count",
            "duplicate_dedup_key_group_count",
            "duplicate_filled_order_group_count",
            "duplicate_event_id_duplicate_count",
            "duplicate_dedup_key_duplicate_count",
            "duplicate_filled_order_duplicate_count",
            "duplicate_total_count",
            "duplicate_occurrence_count",
        ):
            sums[field] += int(item.get(field) or 0)
    for field, value in sums.items():
        if report.get(field) != value:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                "FAIL", f"event-id repaired duplicate recheck aggregate mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("duplicate_total_count", 0) == 0:
        if report.get("recheck_status") != "REPAIRED_DUPLICATE_RECHECK_PASS_CURRENT_EVIDENCE_BLOCKED":
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                "FAIL", "clean repaired duplicate recheck status mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if report.get("primary_blocker_code") != ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_BLOCKER_CODE:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                "FAIL", "clean repaired duplicate recheck primary blocker drifted", "SCHEMA_IDENTITY_MISMATCH"
            )
    else:
        if report.get("recheck_status") != "BLOCKED_RECONCILIATION_REQUIRED":
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
                "FAIL", "repaired duplicate recheck with duplicates must remain reconciliation blocked", "RECONCILIATION_REQUIRED"
            )
    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckValidationResult(
        "PASS", "event-id repaired duplicate recheck preserves clean candidate blockers and live remains blocked", None
    )
