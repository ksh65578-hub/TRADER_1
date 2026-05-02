from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck import (
    EVENT_ID_SCOPE_REPAIR_REQUIRED_BLOCKER_CODE,
    ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    validate_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report.v1"
)
ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_NO_EXECUTION"
)
EVENT_ID_SCOPE_REPAIR_PLAN_ONLY_EXECUTION_REQUIRED_BLOCKER_CODE = (
    "EVENT_ID_SCOPE_REPAIR_PLAN_ONLY_EXECUTION_REQUIRED"
)
ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_CURRENT_EVIDENCE_BLOCKED_CODE = (
    "ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_CURRENT_EVIDENCE_BLOCKED"
)


@dataclass(frozen=True)
class UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_hash(
    report: dict[str, Any],
) -> str:
    payload = dict(report)
    payload.pop("event_id_scope_repair_plan_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


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


def _planned_event_id(
    *,
    session_id: str,
    replacement_loop_id: str,
    cycle_id: str,
    original_event_id: str,
    event_index: int,
) -> str:
    return (
        f"{session_id}:{replacement_loop_id}:{cycle_id}:event-index-{event_index}:"
        f"{original_event_id}"
    )


def _build_update(
    *,
    session_id: str,
    replacement_loop_id: str,
    occurrence: dict[str, Any],
) -> dict[str, Any]:
    cycle_id = str(occurrence.get("cycle_id") or "UNKNOWN")
    original_event_id = str(occurrence.get("event_id") or "UNKNOWN")
    event_index = int(occurrence.get("event_index") or 0)
    planned = _planned_event_id(
        session_id=session_id,
        replacement_loop_id=replacement_loop_id,
        cycle_id=cycle_id,
        original_event_id=original_event_id,
        event_index=event_index,
    )
    return {
        "cycle_id": cycle_id,
        "ledger_path": str(occurrence.get("ledger_path") or ""),
        "ledger_path_allowed": _candidate_path_allowed(str(occurrence.get("ledger_path") or ""), session_id),
        "event_index": event_index,
        "event_type": occurrence.get("event_type"),
        "original_event_id": original_event_id,
        "planned_event_id": planned,
        "planned_event_id_scope": "SESSION_REPLACEMENT_LOOP_CYCLE_EVENT_INDEX_EVENT_ID",
        "planned_event_id_differs": planned != original_event_id,
        "original_dedup_key": occurrence.get("dedup_key"),
        "dedup_key_preserved": True,
        "original_event_hash": occurrence.get("event_hash"),
        "event_hash_recalculation_required": True,
        "candidate_mirror_only": True,
        "candidate_mirror_write_allowed": False,
        "current_evidence_write_allowed": False,
        "live_permission_created": False,
    }


def _build_group(
    *,
    session_id: str,
    replacement_loop_id: str,
    duplicate_group: dict[str, Any],
) -> dict[str, Any]:
    updates = [
        _build_update(session_id=session_id, replacement_loop_id=replacement_loop_id, occurrence=occurrence)
        for occurrence in duplicate_group.get("occurrences", [])
        if isinstance(occurrence, dict)
    ]
    planned_event_ids = [str(update["planned_event_id"]) for update in updates]
    return {
        "duplicate_key_type": duplicate_group.get("duplicate_key_type"),
        "original_event_id": duplicate_group.get("duplicate_key_value"),
        "event_types": duplicate_group.get("event_types", []),
        "affected_cycle_ids": duplicate_group.get("affected_cycle_ids", []),
        "affected_ledger_paths": duplicate_group.get("affected_ledger_paths", []),
        "occurrence_count": int(duplicate_group.get("occurrence_count") or 0),
        "duplicate_count": int(duplicate_group.get("duplicate_count") or 0),
        "source_dedup_keys_unique": bool(duplicate_group.get("dedup_keys_unique")),
        "source_event_hashes_unique": bool(duplicate_group.get("event_hashes_unique")),
        "planned_update_count": len(updates),
        "planned_event_ids_unique": len(set(planned_event_ids)) == len(planned_event_ids),
        "planned_repair_scope": "CANDIDATE_MIRROR_ONLY",
        "planned_updates": updates,
        "candidate_mirror_write_allowed": False,
        "current_evidence_write_allowed": False,
        "target_rollup_write_allowed": False,
        "live_permission_created": False,
    }


def _build_item(*, session_id: str, source_item: dict[str, Any], priority_order: int) -> dict[str, Any]:
    replacement_loop_id = str(source_item.get("replacement_loop_id") or "UNKNOWN")
    event_id_groups = [
        _build_group(session_id=session_id, replacement_loop_id=replacement_loop_id, duplicate_group=group)
        for group in source_item.get("duplicate_groups", [])
        if isinstance(group, dict) and group.get("duplicate_key_type") == "EVENT_ID"
    ]
    update_count = sum(int(group["planned_update_count"]) for group in event_id_groups)
    duplicate_count = sum(int(group["duplicate_count"]) for group in event_id_groups)
    occurrence_count = sum(int(group["occurrence_count"]) for group in event_id_groups)
    affected = bool(event_id_groups)
    blocker_codes = {ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_CURRENT_EVIDENCE_BLOCKED_CODE}
    if affected:
        blocker_codes.update(
            {
                EVENT_ID_SCOPE_REPAIR_PLAN_ONLY_EXECUTION_REQUIRED_BLOCKER_CODE,
                EVENT_ID_SCOPE_REPAIR_REQUIRED_BLOCKER_CODE,
                ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED_BLOCKER_CODE,
                "RECONCILIATION_REQUIRED",
            }
        )
    return {
        "priority_order": priority_order,
        "replacement_loop_id": replacement_loop_id,
        "source_candidate_recheck_status": source_item.get("candidate_recheck_status"),
        "source_primary_blocker_code": source_item.get("primary_blocker_code"),
        "source_duplicate_group_count": int(source_item.get("duplicate_group_count") or 0),
        "source_duplicate_event_id_group_count": int(source_item.get("duplicate_event_id_group_count") or 0),
        "affected_by_event_id_duplicates": affected,
        "repair_plan_item_status": "READY_PLAN_ONLY" if affected else "NO_EVENT_ID_REPAIR_NEEDED",
        "planned_duplicate_group_count": len(event_id_groups),
        "planned_duplicate_count": duplicate_count,
        "planned_occurrence_count": occurrence_count,
        "planned_event_id_update_count": update_count,
        "planned_hash_recalculation_count": update_count,
        "event_id_groups": event_id_groups,
        "primary_blocker_code": EVENT_ID_SCOPE_REPAIR_PLAN_ONLY_EXECUTION_REQUIRED_BLOCKER_CODE
        if affected
        else ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_CURRENT_EVIDENCE_BLOCKED_CODE,
        "blocker_codes": sorted(blocker_codes),
        "candidate_mirror_only": True,
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
        "promotion_eligible": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(
    *,
    root: Path,
    duplicate_reconciliation_recheck_report: dict[str, Any],
    event_id_scope_repair_plan_id: str = "upbit-paper-stale-loop-isolated-event-id-scope-repair-plan",
) -> dict[str, Any]:
    del root
    source_result = validate_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(
        duplicate_reconciliation_recheck_report
    )
    session_id = str(duplicate_reconciliation_recheck_report.get("session_id") or "UNKNOWN")
    items = [
        _build_item(session_id=session_id, source_item=item, priority_order=index)
        for index, item in enumerate(duplicate_reconciliation_recheck_report.get("items", []), start=1)
        if isinstance(item, dict)
    ]
    affected_items = [item for item in items if item["affected_by_event_id_duplicates"]]
    planned_update_count = sum(int(item["planned_event_id_update_count"]) for item in items)
    blocker_codes = {ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_CURRENT_EVIDENCE_BLOCKED_CODE}
    if affected_items:
        blocker_codes.update(
            {
                EVENT_ID_SCOPE_REPAIR_PLAN_ONLY_EXECUTION_REQUIRED_BLOCKER_CODE,
                EVENT_ID_SCOPE_REPAIR_REQUIRED_BLOCKER_CODE,
                ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED_BLOCKER_CODE,
                "RECONCILIATION_REQUIRED",
            }
        )
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or "ISOLATED_DUPLICATE_RECONCILIATION_RECHECK_INVALID")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "event_id_scope_repair_plan_id": event_id_scope_repair_plan_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "event_id_scope_repair_plan_role": ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_ROLE,
        "source_duplicate_reconciliation_recheck_hash": duplicate_reconciliation_recheck_report.get(
            "duplicate_reconciliation_recheck_hash"
        ),
        "source_duplicate_reconciliation_recheck_status": duplicate_reconciliation_recheck_report.get(
            "recheck_status"
        ),
        "source_duplicate_reconciliation_recheck_validator_status": source_result.status,
        "source_duplicate_event_id_group_count": int(
            duplicate_reconciliation_recheck_report.get("duplicate_event_id_group_count") or 0
        ),
        "source_duplicate_event_id_duplicate_count": int(
            duplicate_reconciliation_recheck_report.get("duplicate_event_id_duplicate_count") or 0
        ),
        "source_duplicate_occurrence_count": int(
            duplicate_reconciliation_recheck_report.get("duplicate_occurrence_count") or 0
        ),
        "candidate_count": len(items),
        "repair_plan_candidate_count": len(affected_items),
        "no_repair_candidate_count": len(items) - len(affected_items),
        "planned_duplicate_group_count": sum(int(item["planned_duplicate_group_count"]) for item in items),
        "planned_duplicate_count": sum(int(item["planned_duplicate_count"]) for item in items),
        "planned_occurrence_count": sum(int(item["planned_occurrence_count"]) for item in items),
        "planned_event_id_update_count": planned_update_count,
        "planned_hash_recalculation_count": planned_update_count,
        "candidate_mirror_write_allowed_count": 0,
        "current_canonical_ledger_write_allowed_count": 0,
        "target_rollup_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "plan_status": "READY_PLAN_ONLY" if affected_items else "NO_EVENT_ID_REPAIR_NEEDED",
        "primary_blocker_code": EVENT_ID_SCOPE_REPAIR_PLAN_ONLY_EXECUTION_REQUIRED_BLOCKER_CODE
        if affected_items
        else ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_CURRENT_EVIDENCE_BLOCKED_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": (
            "Review the isolated event-id scope repair plan, then run a candidate-only repair executor; "
            "do not promote mirror ledgers to current evidence."
        ),
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "candidate_only": True,
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
        "event_id_scope_repair_plan_hash": "",
    }
    report["event_id_scope_repair_plan_hash"] = (
        upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_hash(report)
    )
    return report


def write_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "event_id_scope_repair_plan_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "event_id_scope_repair_plan_role",
        "source_duplicate_reconciliation_recheck_hash",
        "source_duplicate_reconciliation_recheck_status",
        "source_duplicate_reconciliation_recheck_validator_status",
        "source_duplicate_event_id_group_count",
        "source_duplicate_event_id_duplicate_count",
        "source_duplicate_occurrence_count",
        "candidate_count",
        "repair_plan_candidate_count",
        "no_repair_candidate_count",
        "planned_duplicate_group_count",
        "planned_duplicate_count",
        "planned_occurrence_count",
        "planned_event_id_update_count",
        "planned_hash_recalculation_count",
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
        "candidate_only",
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
        "event_id_scope_repair_plan_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
            "FAIL", f"isolated event-id repair plan missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_SCHEMA_ID:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
            "FAIL", "isolated event-id repair plan schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("event_id_scope_repair_plan_hash") != upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_hash(report):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
            "FAIL", "isolated event-id repair plan hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
            "BLOCKED", "isolated event-id repair plan scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if report.get("event_id_scope_repair_plan_role") != ISOLATED_EVENT_ID_SCOPE_REPAIR_PLAN_ROLE:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
            "BLOCKED", "isolated event-id repair plan role cannot claim execution or live permission", "LIVE_FINAL_GUARD_FAILED"
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
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
            "BLOCKED", "isolated event-id repair plan attempted execution, current evidence, or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("candidate_mirror_write_allowed_count") != 0
        or report.get("current_canonical_ledger_write_allowed_count") != 0
        or report.get("target_rollup_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
    ):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
            "BLOCKED", "isolated event-id repair plan exposed forbidden write counts", "LIVE_FINAL_GUARD_FAILED"
        )
    if not all(
        report.get(field) is True
        for field in ("display_only", "dashboard_truth_only", "paper_only", "candidate_only", "plan_only")
    ):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
            "BLOCKED", "isolated event-id repair plan must remain display-only candidate PAPER plan", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("candidate_count") != len(items):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
            "FAIL", "isolated event-id repair plan item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    session_id = str(report.get("session_id"))
    planned_event_ids: list[str] = []
    sums = {
        "repair_plan_candidate_count": 0,
        "no_repair_candidate_count": 0,
        "planned_duplicate_group_count": 0,
        "planned_duplicate_count": 0,
        "planned_occurrence_count": 0,
        "planned_event_id_update_count": 0,
        "planned_hash_recalculation_count": 0,
    }
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or item.get("priority_order") != index:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                "FAIL", "isolated event-id repair plan priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if any(
            item.get(field) is not False
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
                "promotion_eligible",
                "scale_up_allowed",
            )
        ):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                "BLOCKED", "isolated event-id repair plan item attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
            )
        affected = item.get("affected_by_event_id_duplicates") is True
        if affected:
            sums["repair_plan_candidate_count"] += 1
            if item.get("repair_plan_item_status") != "READY_PLAN_ONLY":
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                    "FAIL", "affected isolated event-id repair item must be ready plan only", "RECONCILIATION_REQUIRED"
                )
        else:
            sums["no_repair_candidate_count"] += 1
            if item.get("repair_plan_item_status") != "NO_EVENT_ID_REPAIR_NEEDED":
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                    "FAIL", "unaffected isolated event-id repair item status mismatch", "SCHEMA_IDENTITY_MISMATCH"
                )
        for field in (
            "planned_duplicate_group_count",
            "planned_duplicate_count",
            "planned_occurrence_count",
            "planned_event_id_update_count",
            "planned_hash_recalculation_count",
        ):
            sums[field] += int(item.get(field) or 0)
        item_group_count = 0
        item_update_count = 0
        for group in item.get("event_id_groups", []):
            if not isinstance(group, dict):
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                    "FAIL", "isolated event-id repair group must be object", "SCHEMA_IDENTITY_MISMATCH"
                )
            if group.get("duplicate_key_type") != "EVENT_ID":
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                    "FAIL", "isolated event-id repair plan included non-event-id duplicate", "RECONCILIATION_REQUIRED"
                )
            if group.get("source_dedup_keys_unique") is not True or group.get("planned_event_ids_unique") is not True:
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                    "FAIL", "isolated event-id repair plan did not preserve dedup uniqueness or planned event-id uniqueness",
                    "RECONCILIATION_REQUIRED",
                )
            if group.get("planned_repair_scope") != "CANDIDATE_MIRROR_ONLY":
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                    "BLOCKED", "isolated event-id repair plan escaped candidate mirror scope", "SNAPSHOT_SCOPE_MISMATCH"
                )
            if (
                group.get("candidate_mirror_write_allowed") is not False
                or group.get("current_evidence_write_allowed") is not False
                or group.get("target_rollup_write_allowed") is not False
                or group.get("live_permission_created") is not False
            ):
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                    "BLOCKED", "isolated event-id repair group attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
                )
            item_group_count += 1
            group_update_count = 0
            for update in group.get("planned_updates", []):
                if not isinstance(update, dict):
                    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                        "FAIL", "isolated event-id repair update must be object", "SCHEMA_IDENTITY_MISMATCH"
                    )
                if not _candidate_path_allowed(str(update.get("ledger_path") or ""), session_id):
                    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                        "BLOCKED", "isolated event-id repair update path escaped candidate namespace", "SNAPSHOT_SCOPE_MISMATCH"
                    )
                if update.get("ledger_path_allowed") is not True:
                    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                        "BLOCKED", "isolated event-id repair update marked candidate path invalid", "SNAPSHOT_SCOPE_MISMATCH"
                    )
                planned_event_id = str(update.get("planned_event_id") or "")
                original_event_id = str(update.get("original_event_id") or "")
                cycle_id = str(update.get("cycle_id") or "")
                if (
                    not planned_event_id
                    or planned_event_id == original_event_id
                    or cycle_id not in planned_event_id
                    or original_event_id not in planned_event_id
                ):
                    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                        "FAIL", "planned event_id is not cycle-scoped", "RECONCILIATION_REQUIRED"
                    )
                if (
                    update.get("planned_event_id_differs") is not True
                    or update.get("dedup_key_preserved") is not True
                    or update.get("event_hash_recalculation_required") is not True
                    or update.get("candidate_mirror_only") is not True
                    or update.get("candidate_mirror_write_allowed") is not False
                    or update.get("current_evidence_write_allowed") is not False
                    or update.get("live_permission_created") is not False
                ):
                    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                        "BLOCKED", "isolated event-id repair update violated safety flags", "LIVE_FINAL_GUARD_FAILED"
                    )
                planned_event_ids.append(planned_event_id)
                group_update_count += 1
            if group.get("planned_update_count") != group_update_count:
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                    "FAIL", "isolated event-id repair group update count mismatch", "SCHEMA_IDENTITY_MISMATCH"
                )
            item_update_count += group_update_count
        if item.get("planned_duplicate_group_count") != item_group_count:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                "FAIL", "isolated event-id repair item group count mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("planned_event_id_update_count") != item_update_count:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                "FAIL", "isolated event-id repair item update count mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
    for field, value in sums.items():
        if report.get(field) != value:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                "FAIL", f"isolated event-id repair plan aggregate mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if len(planned_event_ids) != len(set(planned_event_ids)):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
            "FAIL", "isolated event-id repair plan produced duplicate planned event_id values", "RECONCILIATION_REQUIRED"
        )
    if report.get("planned_event_id_update_count", 0) > 0:
        if report.get("plan_status") != "READY_PLAN_ONLY":
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                "FAIL", "isolated event-id repair plan with updates must remain ready plan only", "RECONCILIATION_REQUIRED"
            )
        if report.get("primary_blocker_code") != EVENT_ID_SCOPE_REPAIR_PLAN_ONLY_EXECUTION_REQUIRED_BLOCKER_CODE:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
                "FAIL", "isolated event-id repair plan primary blocker mismatch", "RECONCILIATION_REQUIRED"
            )
    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanValidationResult(
        "PASS", "isolated event-id scope repair plan is candidate-only and live remains blocked", None
    )
