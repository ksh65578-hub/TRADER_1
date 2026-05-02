from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_ledger_rollup_rebuild import (
    validate_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json, recover_jsonl_records


UPBIT_PAPER_STALE_LOOP_ISOLATED_DUPLICATE_RECONCILIATION_RECHECK_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report.v1"
)
ISOLATED_DUPLICATE_RECONCILIATION_RECHECK_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_ISOLATED_DUPLICATE_RECONCILIATION_RECHECK_CANDIDATE_ONLY"
)
ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED_BLOCKER_CODE = (
    "ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED"
)
EVENT_ID_SCOPE_REPAIR_REQUIRED_BLOCKER_CODE = "EVENT_ID_SCOPE_REPAIR_REQUIRED"
ISOLATED_DUPLICATE_RECHECK_CURRENT_EVIDENCE_BLOCKED_CODE = (
    "ISOLATED_DUPLICATE_RECHECK_CURRENT_EVIDENCE_BLOCKED"
)


@dataclass(frozen=True)
class UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_hash(
    report: dict[str, Any],
) -> str:
    payload = dict(report)
    payload.pop("duplicate_reconciliation_recheck_hash", None)
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


def _load_records(root: Path, relative_path: str) -> tuple[list[dict[str, Any]], str, str | None]:
    try:
        records, quarantine_path = recover_jsonl_records(_rooted(root, relative_path))
    except FileNotFoundError:
        return [], "MISSING", None
    except OSError:
        return [], "UNREADABLE", None
    return records, "PASS", quarantine_path.as_posix() if quarantine_path is not None else None


def _semantic_key(event: dict[str, Any]) -> str | None:
    if not (event.get("intent_id") or event.get("client_order_id") or event.get("order_id")):
        return None
    return json.dumps(
        [
            event.get("event_type"),
            event.get("intent_id"),
            event.get("client_order_id"),
            event.get("order_id"),
        ],
        sort_keys=True,
        separators=(",", ":"),
    )


def _filled_order_key(event: dict[str, Any]) -> str | None:
    if event.get("event_type") != "ORDER_FILLED":
        return None
    return json.dumps([event.get("client_order_id"), event.get("order_id")], separators=(",", ":"))


def _event_context(*, cycle_id: str, ledger_path: str, event_index: int, event: dict[str, Any]) -> dict[str, Any]:
    return {
        "cycle_id": cycle_id,
        "ledger_path": ledger_path,
        "event_index": event_index,
        "event_type": event.get("event_type"),
        "event_id": event.get("event_id"),
        "dedup_key": event.get("dedup_key"),
        "intent_id": event.get("intent_id"),
        "client_order_id": event.get("client_order_id"),
        "order_id": event.get("order_id"),
        "event_hash": event.get("event_hash"),
    }


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
                "dedup_keys_unique": len({str(item.get("dedup_key")) for item in occurrences}) == len(occurrences),
                "event_hashes_unique": len({str(item.get("event_hash")) for item in occurrences}) == len(occurrences),
                "occurrences": occurrences,
                "resolution_hint": resolution_hint,
                "current_evidence_write_allowed": False,
                "live_permission_created": False,
            }
        )
    return duplicates


def _build_candidate(*, root: Path, session_id: str, source_item: dict[str, Any], priority_order: int) -> dict[str, Any]:
    replacement_loop_id = str(source_item.get("replacement_loop_id") or "UNKNOWN")
    by_event_id: dict[str, list[dict[str, Any]]] = {}
    by_dedup_key: dict[str, list[dict[str, Any]]] = {}
    by_semantic_key: dict[str, list[dict[str, Any]]] = {}
    by_filled_order_key: dict[str, list[dict[str, Any]]] = {}
    load_blockers: list[dict[str, str]] = []
    cycle_summaries: list[dict[str, Any]] = []
    event_count = 0
    filled_order_count = 0

    for cycle in source_item.get("cycles", []):
        if not isinstance(cycle, dict):
            continue
        cycle_id = str(cycle.get("cycle_id") or "UNKNOWN")
        ledger_path = str(cycle.get("mirror_ledger_path") or "")
        records, load_status, quarantine_path = _load_records(root, ledger_path)
        if not _candidate_path_allowed(ledger_path, session_id):
            load_blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "isolated duplicate recheck path escaped candidate namespace"))
        if load_status != "PASS":
            load_blockers.append(_blocker("LEDGER_UNAVAILABLE", f"isolated duplicate recheck could not load {ledger_path}: {load_status}"))
        cycle_summaries.append(
            {
                "cycle_id": cycle_id,
                "mirror_ledger_path": ledger_path,
                "mirror_ledger_path_allowed": _candidate_path_allowed(ledger_path, session_id),
                "mirror_ledger_load_status": load_status,
                "mirror_ledger_event_count": len(records),
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
            semantic_key = _semantic_key(event)
            if semantic_key is not None:
                by_semantic_key.setdefault(semantic_key, []).append(context)
            filled_order_key = _filled_order_key(event)
            if filled_order_key is not None:
                by_filled_order_key.setdefault(filled_order_key, []).append(context)

    event_id_duplicate_groups = _duplicate_groups(
        groups=by_event_id,
        duplicate_key_type="EVENT_ID",
        resolution_hint="REGENERATE_EVENT_ID_WITH_CYCLE_SCOPE_IN_CANDIDATE_MIRROR_ONLY",
    )
    dedup_key_duplicate_groups = _duplicate_groups(
        groups=by_dedup_key,
        duplicate_key_type="DEDUP_KEY",
        resolution_hint="RECONCILE_DEDUP_KEY_BEFORE_ANY_CURRENT_EVIDENCE_USE",
    )
    semantic_duplicate_groups = _duplicate_groups(
        groups=by_semantic_key,
        duplicate_key_type="SEMANTIC_EVENT",
        resolution_hint="RECONCILE_SEMANTIC_DUPLICATE_BEFORE_ANY_CURRENT_EVIDENCE_USE",
    )
    filled_order_duplicate_groups = _duplicate_groups(
        groups=by_filled_order_key,
        duplicate_key_type="FILLED_ORDER",
        resolution_hint="RECONCILE_DUPLICATE_FILL_BEFORE_ANY_POSITION_OR_PNL_USE",
    )
    duplicate_groups = [
        *event_id_duplicate_groups,
        *dedup_key_duplicate_groups,
        *semantic_duplicate_groups,
        *filled_order_duplicate_groups,
    ]
    duplicate_count = sum(int(group["duplicate_count"]) for group in duplicate_groups)
    occurrence_count = sum(int(group["occurrence_count"]) for group in duplicate_groups)
    status = "BLOCKED_EVENT_ID_SCOPE_REPAIR_REQUIRED" if duplicate_groups or load_blockers else "PASS_CURRENT_EVIDENCE_BLOCKED"
    blocker_codes = {ISOLATED_DUPLICATE_RECHECK_CURRENT_EVIDENCE_BLOCKED_CODE}
    if duplicate_groups:
        blocker_codes.update({ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED_BLOCKER_CODE, "RECONCILIATION_REQUIRED"})
        if event_id_duplicate_groups:
            blocker_codes.add(EVENT_ID_SCOPE_REPAIR_REQUIRED_BLOCKER_CODE)
    for blocker in load_blockers:
        blocker_codes.add(blocker["code"])
    return {
        "priority_order": priority_order,
        "replacement_loop_id": replacement_loop_id,
        "source_candidate_rollup_status": source_item.get("candidate_rollup_status"),
        "candidate_recheck_status": status,
        "primary_blocker_code": EVENT_ID_SCOPE_REPAIR_REQUIRED_BLOCKER_CODE
        if event_id_duplicate_groups
        else ISOLATED_DUPLICATE_RECHECK_CURRENT_EVIDENCE_BLOCKED_CODE,
        "blocker_codes": sorted(blocker_codes),
        "ledger_jsonl_count": len(cycle_summaries),
        "ledger_event_count": event_count,
        "filled_order_count": filled_order_count,
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_event_id_group_count": len(event_id_duplicate_groups),
        "duplicate_dedup_key_group_count": len(dedup_key_duplicate_groups),
        "duplicate_semantic_group_count": len(semantic_duplicate_groups),
        "duplicate_filled_order_group_count": len(filled_order_duplicate_groups),
        "duplicate_event_id_duplicate_count": sum(int(group["duplicate_count"]) for group in event_id_duplicate_groups),
        "duplicate_dedup_key_duplicate_count": sum(int(group["duplicate_count"]) for group in dedup_key_duplicate_groups),
        "duplicate_semantic_duplicate_count": sum(int(group["duplicate_count"]) for group in semantic_duplicate_groups),
        "duplicate_filled_order_duplicate_count": sum(int(group["duplicate_count"]) for group in filled_order_duplicate_groups),
        "duplicate_total_count": duplicate_count,
        "duplicate_occurrence_count": occurrence_count,
        "cycles": cycle_summaries,
        "duplicate_groups": duplicate_groups,
        "load_blockers": load_blockers,
        "recommended_next_action": "repair duplicate event_id scope in isolated candidate mirrors only"
        if event_id_duplicate_groups
        else "keep candidate-only evidence blocked from current promotion",
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


def build_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(
    *,
    root: Path,
    isolated_ledger_rollup_rebuild_report: dict[str, Any],
    duplicate_reconciliation_recheck_id: str = "upbit-paper-stale-loop-isolated-duplicate-reconciliation-recheck",
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(
        isolated_ledger_rollup_rebuild_report
    )
    session_id = str(isolated_ledger_rollup_rebuild_report.get("session_id", "UNKNOWN"))
    items = [
        _build_candidate(root=root, session_id=session_id, source_item=item, priority_order=index)
        for index, item in enumerate(isolated_ledger_rollup_rebuild_report.get("items", []), start=1)
        if isinstance(item, dict)
    ]
    affected_items = [item for item in items if item["duplicate_group_count"] > 0]
    blocker_codes = {ISOLATED_DUPLICATE_RECHECK_CURRENT_EVIDENCE_BLOCKED_CODE}
    if affected_items:
        blocker_codes.update(
            {
                ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED_BLOCKER_CODE,
                EVENT_ID_SCOPE_REPAIR_REQUIRED_BLOCKER_CODE,
                "RECONCILIATION_REQUIRED",
            }
        )
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or "ISOLATED_LEDGER_ROLLUP_REBUILD_INVALID")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_ISOLATED_DUPLICATE_RECONCILIATION_RECHECK_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "duplicate_reconciliation_recheck_id": duplicate_reconciliation_recheck_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "duplicate_reconciliation_recheck_role": ISOLATED_DUPLICATE_RECONCILIATION_RECHECK_ROLE,
        "source_isolated_ledger_rollup_rebuild_hash": isolated_ledger_rollup_rebuild_report.get(
            "isolated_ledger_rollup_rebuild_hash"
        ),
        "source_isolated_ledger_rollup_rebuild_status": isolated_ledger_rollup_rebuild_report.get("rebuild_status"),
        "source_isolated_ledger_rollup_rebuild_validator_status": source_result.status,
        "candidate_count": len(items),
        "affected_candidate_count": len(affected_items),
        "pass_candidate_count": sum(1 for item in items if item["candidate_recheck_status"] == "PASS_CURRENT_EVIDENCE_BLOCKED"),
        "blocked_candidate_count": sum(1 for item in items if item["candidate_recheck_status"] != "PASS_CURRENT_EVIDENCE_BLOCKED"),
        "ledger_jsonl_count": sum(int(item["ledger_jsonl_count"]) for item in items),
        "ledger_event_count": sum(int(item["ledger_event_count"]) for item in items),
        "filled_order_count": sum(int(item["filled_order_count"]) for item in items),
        "duplicate_group_count": sum(int(item["duplicate_group_count"]) for item in items),
        "duplicate_event_id_group_count": sum(int(item["duplicate_event_id_group_count"]) for item in items),
        "duplicate_dedup_key_group_count": sum(int(item["duplicate_dedup_key_group_count"]) for item in items),
        "duplicate_semantic_group_count": sum(int(item["duplicate_semantic_group_count"]) for item in items),
        "duplicate_filled_order_group_count": sum(int(item["duplicate_filled_order_group_count"]) for item in items),
        "duplicate_event_id_duplicate_count": sum(int(item["duplicate_event_id_duplicate_count"]) for item in items),
        "duplicate_dedup_key_duplicate_count": sum(int(item["duplicate_dedup_key_duplicate_count"]) for item in items),
        "duplicate_semantic_duplicate_count": sum(int(item["duplicate_semantic_duplicate_count"]) for item in items),
        "duplicate_filled_order_duplicate_count": sum(int(item["duplicate_filled_order_duplicate_count"]) for item in items),
        "duplicate_total_count": sum(int(item["duplicate_total_count"]) for item in items),
        "duplicate_occurrence_count": sum(int(item["duplicate_occurrence_count"]) for item in items),
        "current_evidence_write_allowed_count": 0,
        "target_rollup_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "recheck_status": "BLOCKED_REPAIR_PLAN_REQUIRED" if affected_items else "PASS_CURRENT_EVIDENCE_BLOCKED",
        "primary_blocker_code": ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED_BLOCKER_CODE
        if affected_items
        else ISOLATED_DUPLICATE_RECHECK_CURRENT_EVIDENCE_BLOCKED_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Build an isolated candidate-only event-id repair plan; do not promote mirror ledgers to current evidence.",
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
        "duplicate_reconciliation_recheck_hash": "",
    }
    report["duplicate_reconciliation_recheck_hash"] = (
        upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_hash(report)
    )
    return report


def write_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "duplicate_reconciliation_recheck_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "duplicate_reconciliation_recheck_role",
        "source_isolated_ledger_rollup_rebuild_hash",
        "source_isolated_ledger_rollup_rebuild_status",
        "source_isolated_ledger_rollup_rebuild_validator_status",
        "candidate_count",
        "affected_candidate_count",
        "pass_candidate_count",
        "blocked_candidate_count",
        "ledger_jsonl_count",
        "ledger_event_count",
        "filled_order_count",
        "duplicate_group_count",
        "duplicate_event_id_group_count",
        "duplicate_dedup_key_group_count",
        "duplicate_semantic_group_count",
        "duplicate_filled_order_group_count",
        "duplicate_event_id_duplicate_count",
        "duplicate_dedup_key_duplicate_count",
        "duplicate_semantic_duplicate_count",
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
        "duplicate_reconciliation_recheck_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
            "FAIL", f"isolated duplicate recheck missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_ISOLATED_DUPLICATE_RECONCILIATION_RECHECK_SCHEMA_ID:
        return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
            "FAIL", "isolated duplicate recheck schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("duplicate_reconciliation_recheck_hash") != upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_hash(report):
        return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
            "FAIL", "isolated duplicate recheck hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
            "BLOCKED", "isolated duplicate recheck scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if report.get("duplicate_reconciliation_recheck_role") != ISOLATED_DUPLICATE_RECONCILIATION_RECHECK_ROLE:
        return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
            "BLOCKED", "isolated duplicate recheck role cannot claim live or current evidence", "LIVE_FINAL_GUARD_FAILED"
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
        return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
            "BLOCKED", "isolated duplicate recheck attempted current evidence or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("current_evidence_write_allowed_count") != 0
        or report.get("target_rollup_write_allowed_count") != 0
        or report.get("candidate_current_evidence_usable_count") != 0
    ):
        return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
            "BLOCKED", "isolated duplicate recheck exposed forbidden current evidence counts", "LIVE_FINAL_GUARD_FAILED"
        )
    if not report.get("display_only") or not report.get("dashboard_truth_only") or not report.get("paper_only") or not report.get("candidate_only"):
        return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
            "BLOCKED", "isolated duplicate recheck must remain display-only candidate PAPER evidence", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("candidate_count") != len(items):
        return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
            "FAIL", "isolated duplicate recheck item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    session_id = str(report.get("session_id"))
    sums = {
        "affected_candidate_count": 0,
        "pass_candidate_count": 0,
        "blocked_candidate_count": 0,
        "ledger_jsonl_count": 0,
        "ledger_event_count": 0,
        "filled_order_count": 0,
        "duplicate_group_count": 0,
        "duplicate_event_id_group_count": 0,
        "duplicate_dedup_key_group_count": 0,
        "duplicate_semantic_group_count": 0,
        "duplicate_filled_order_group_count": 0,
        "duplicate_event_id_duplicate_count": 0,
        "duplicate_dedup_key_duplicate_count": 0,
        "duplicate_semantic_duplicate_count": 0,
        "duplicate_filled_order_duplicate_count": 0,
        "duplicate_total_count": 0,
        "duplicate_occurrence_count": 0,
    }
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or item.get("priority_order") != index:
            return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                "FAIL", "isolated duplicate recheck priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
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
            return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                "BLOCKED", "isolated duplicate recheck item attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
            )
        if item.get("duplicate_group_count", 0) > 0:
            sums["affected_candidate_count"] += 1
        if item.get("candidate_recheck_status") == "PASS_CURRENT_EVIDENCE_BLOCKED":
            sums["pass_candidate_count"] += 1
        else:
            sums["blocked_candidate_count"] += 1
        for cycle in item.get("cycles", []):
            if not isinstance(cycle, dict) or not _candidate_path_allowed(str(cycle.get("mirror_ledger_path") or ""), session_id):
                return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                    "BLOCKED", "isolated duplicate recheck cycle path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
            if cycle.get("current_evidence_write_allowed") is not False or cycle.get("live_permission_created") is not False:
                return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                    "BLOCKED", "isolated duplicate recheck cycle attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
                )
        duplicate_group_duplicate_sum = 0
        duplicate_group_occurrence_sum = 0
        for group in item.get("duplicate_groups", []):
            if not isinstance(group, dict):
                return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                    "FAIL", "isolated duplicate group must be an object", "SCHEMA_IDENTITY_MISMATCH"
                )
            if group.get("duplicate_count") != int(group.get("occurrence_count") or 0) - 1:
                return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                    "FAIL", "isolated duplicate group count mismatch", "SCHEMA_IDENTITY_MISMATCH"
                )
            for path in group.get("affected_ledger_paths", []):
                if not isinstance(path, str) or not _candidate_path_allowed(path, session_id):
                    return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                        "BLOCKED", "isolated duplicate group path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                    )
            if group.get("current_evidence_write_allowed") is not False or group.get("live_permission_created") is not False:
                return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                    "BLOCKED", "isolated duplicate group attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
                )
            duplicate_group_duplicate_sum += int(group.get("duplicate_count") or 0)
            duplicate_group_occurrence_sum += int(group.get("occurrence_count") or 0)
        if item.get("duplicate_total_count") != duplicate_group_duplicate_sum:
            return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                "FAIL", "isolated duplicate item total mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("duplicate_occurrence_count") != duplicate_group_occurrence_sum:
            return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                "FAIL", "isolated duplicate item occurrence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for field in (
            "ledger_jsonl_count",
            "ledger_event_count",
            "filled_order_count",
            "duplicate_group_count",
            "duplicate_event_id_group_count",
            "duplicate_dedup_key_group_count",
            "duplicate_semantic_group_count",
            "duplicate_filled_order_group_count",
            "duplicate_event_id_duplicate_count",
            "duplicate_dedup_key_duplicate_count",
            "duplicate_semantic_duplicate_count",
            "duplicate_filled_order_duplicate_count",
            "duplicate_total_count",
            "duplicate_occurrence_count",
        ):
            sums[field] += int(item.get(field) or 0)
    for field, value in sums.items():
        if report.get(field) != value:
            return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                "FAIL", f"isolated duplicate recheck aggregate mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("duplicate_total_count", 0) > 0:
        if report.get("recheck_status") != "BLOCKED_REPAIR_PLAN_REQUIRED":
            return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                "FAIL", "duplicate recheck with duplicates must require repair plan", "RECONCILIATION_REQUIRED"
            )
        if report.get("primary_blocker_code") != ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED_BLOCKER_CODE:
            return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
                "FAIL", "duplicate recheck primary blocker mismatch", "RECONCILIATION_REQUIRED"
            )
    return UpbitPaperStaleLoopIsolatedDuplicateRecheckValidationResult(
        "PASS", "isolated duplicate reconciliation recheck preserves blockers and live remains blocked", None
    )
