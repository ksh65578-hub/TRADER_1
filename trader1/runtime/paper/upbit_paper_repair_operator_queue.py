from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_blocked_repair_plan import (
    BLOCKED_REPAIR_PLAN_BLOCKER_CODE,
    validate_upbit_paper_blocked_repair_plan_report,
)
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import (
    LEDGER_ROLLUP_REPAIR_BLOCKER_CODE,
    validate_upbit_paper_ledger_rollup_repair_report,
)
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import (
    POST_REPAIR_RECONCILIATION_BLOCKER_CODE,
    validate_upbit_paper_post_repair_reconciliation_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_REPAIR_OPERATOR_QUEUE_SCHEMA_ID = "trader1.upbit_paper_repair_operator_queue_report.v1"
REPAIR_OPERATOR_QUEUE_TRUTH_ROLE = "paper_runtime_repair_operator_queue_truth"
REPAIR_OPERATOR_QUEUE_ROLE = "PAPER_RUNTIME_REPAIR_OPERATOR_QUEUE_NOT_EVIDENCE"
REPAIR_OPERATOR_QUEUE_BLOCKER_CODE = "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION"


@dataclass(frozen=True)
class UpbitPaperRepairOperatorQueueValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_repair_operator_queue_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("queue_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return path.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "live" not in parts


def _lane_priority(lane: str) -> int:
    return {
        "LEDGER_ROLLUP_REBUILD_READY": 10,
        "RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP": 20,
        "RECOVERY_GUARD_THEN_LEDGER_ROLLUP": 30,
        "RERUN_POST_REGENERATION_RECONCILIATION": 40,
        "QUARANTINE_OPERATOR_REVIEW": 50,
    }.get(lane, 90)


def _operator_action_for_lane(lane: str, post_repair_item: dict[str, Any] | None) -> str:
    if lane == "LEDGER_ROLLUP_REBUILD_READY":
        if post_repair_item is not None and post_repair_item.get("hash_reconciliation_requires_operator_action"):
            return (
                "Review the ledger rollup candidate hash mismatch; do not promote the candidate until an operator "
                "reconciles the replacement loop hash and source expectation."
            )
        return "Build a ledger rollup candidate, then run post-repair reconciliation before evidence use."
    if lane == "RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP":
        return "Rerun the missing PAPER runtime cycles, rebuild the ledger rollup, then rerun reconciliation."
    if lane == "RECOVERY_GUARD_THEN_LEDGER_ROLLUP":
        return "Clear recovery guard and partial-write blockers before rerunning cycles or rebuilding ledger rollup."
    if lane == "QUARANTINE_OPERATOR_REVIEW":
        return "Quarantine the replacement for operator review before any repair attempt."
    return "Rerun validator-backed post-regeneration reconciliation before evidence use."


def _index_by_loop(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        loop_id = item.get("replacement_loop_id")
        if isinstance(loop_id, str) and loop_id:
            indexed[loop_id] = item
    return indexed


def _build_queue_item(
    *,
    priority_order: int,
    plan_item: dict[str, Any],
    repair_item: dict[str, Any] | None,
    post_repair_item: dict[str, Any] | None,
) -> dict[str, Any]:
    lane = str(plan_item.get("safe_repair_lane") or "UNKNOWN")
    repair_candidate_path = repair_item.get("candidate_rollup_artifact_path") if repair_item else None
    post_repair_classification = post_repair_item.get("candidate_classification") if post_repair_item else None
    post_repair_blocker = post_repair_item.get("item_blocker_code") if post_repair_item else None
    blockers = set(str(code) for code in plan_item.get("blocked_repair_reason_codes") or [])
    blockers.add(BLOCKED_REPAIR_PLAN_BLOCKER_CODE)
    if lane == "LEDGER_ROLLUP_REBUILD_READY":
        blockers.add(LEDGER_ROLLUP_REPAIR_BLOCKER_CODE)
        blockers.add(POST_REPAIR_RECONCILIATION_BLOCKER_CODE)
    if post_repair_blocker:
        blockers.add(str(post_repair_blocker))
    if repair_item and repair_item.get("hash_reconciliation_blocker_code"):
        blockers.add(str(repair_item["hash_reconciliation_blocker_code"]))
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(plan_item.get("replacement_loop_id") or "UNKNOWN"),
        "replacement_path": str(plan_item.get("replacement_path") or ""),
        "safe_repair_lane": lane,
        "operator_action": _operator_action_for_lane(lane, post_repair_item),
        "ready_for_operator_ledger_candidate_review": bool(
            lane == "LEDGER_ROLLUP_REBUILD_READY"
            and repair_item is not None
            and post_repair_item is not None
            and repair_item.get("candidate_rollup_validator_status") == "PASS"
        ),
        "requires_runtime_cycle_rerun": bool(plan_item.get("requires_runtime_cycle_rerun")),
        "requires_recovery_guard_rerun": bool(plan_item.get("requires_recovery_guard_rerun")),
        "requires_hash_operator_reconciliation": bool(
            (repair_item or {}).get("hash_reconciliation_requires_operator_action")
            or (post_repair_item or {}).get("hash_reconciliation_requires_operator_action")
        ),
        "cycle_ledger_jsonl_missing_count": int(plan_item.get("cycle_ledger_jsonl_missing_count") or 0),
        "cycle_ledger_jsonl_missing_paths": list(plan_item.get("cycle_ledger_jsonl_missing_paths") or []),
        "paper_ledger_rollup_path": str(plan_item.get("paper_ledger_rollup_path") or ""),
        "paper_ledger_rollup_artifact_exists": bool(plan_item.get("paper_ledger_rollup_artifact_exists")),
        "candidate_rollup_artifact_path": repair_candidate_path,
        "candidate_rollup_validator_status": (repair_item or {}).get("candidate_rollup_validator_status"),
        "candidate_rollup_hash": (repair_item or {}).get("candidate_rollup_hash"),
        "candidate_current_evidence_usable": bool((post_repair_item or {}).get("candidate_current_evidence_usable")),
        "post_repair_candidate_classification": post_repair_classification,
        "post_repair_item_blocker_code": post_repair_blocker,
        "blocking_codes": sorted(blockers),
        "current_evidence_mutation_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "live_permission_created": False,
    }


def build_upbit_paper_repair_operator_queue_report(
    *,
    blocked_repair_plan_report: dict[str, Any],
    ledger_rollup_repair_report: dict[str, Any],
    post_repair_reconciliation_report: dict[str, Any],
    queue_id: str = "upbit-paper-repair-operator-queue",
) -> dict[str, Any]:
    plan_result = validate_upbit_paper_blocked_repair_plan_report(blocked_repair_plan_report)
    repair_result = validate_upbit_paper_ledger_rollup_repair_report(ledger_rollup_repair_report)
    post_result = validate_upbit_paper_post_repair_reconciliation_report(post_repair_reconciliation_report)
    session_id = str(blocked_repair_plan_report.get("session_id", "UNKNOWN"))
    repair_items = _index_by_loop(
        [item for item in ledger_rollup_repair_report.get("items", []) if isinstance(item, dict)]
    )
    post_repair_items = _index_by_loop(
        [item for item in post_repair_reconciliation_report.get("items", []) if isinstance(item, dict)]
    )
    plan_items = [
        item for item in blocked_repair_plan_report.get("items", []) if isinstance(item, dict)
    ]
    sorted_plan_items = sorted(
        plan_items,
        key=lambda item: (_lane_priority(str(item.get("safe_repair_lane") or "")), str(item.get("replacement_loop_id") or "")),
    )
    items = [
        _build_queue_item(
            priority_order=index,
            plan_item=item,
            repair_item=repair_items.get(str(item.get("replacement_loop_id") or "")),
            post_repair_item=post_repair_items.get(str(item.get("replacement_loop_id") or "")),
        )
        for index, item in enumerate(sorted_plan_items, start=1)
    ]
    blockers = {REPAIR_OPERATOR_QUEUE_BLOCKER_CODE}
    if plan_result.status != "PASS":
        blockers.add(plan_result.blocker_code or BLOCKED_REPAIR_PLAN_BLOCKER_CODE)
    if repair_result.status != "PASS":
        blockers.add(repair_result.blocker_code or LEDGER_ROLLUP_REPAIR_BLOCKER_CODE)
    if post_result.status != "PASS":
        blockers.add(post_result.blocker_code or POST_REPAIR_RECONCILIATION_BLOCKER_CODE)
    if any(item["candidate_current_evidence_usable"] for item in items):
        blockers.add("LIVE_FINAL_GUARD_FAILED")
    report = {
        "schema_id": UPBIT_PAPER_REPAIR_OPERATOR_QUEUE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "queue_id": queue_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": REPAIR_OPERATOR_QUEUE_TRUTH_ROLE,
        "queue_role": REPAIR_OPERATOR_QUEUE_ROLE,
        "source_blocked_repair_plan_hash": blocked_repair_plan_report.get("repair_plan_hash"),
        "source_blocked_repair_plan_status": blocked_repair_plan_report.get("repair_plan_status"),
        "source_ledger_rollup_repair_hash": ledger_rollup_repair_report.get("repair_report_hash"),
        "source_ledger_rollup_repair_status": ledger_rollup_repair_report.get("repair_report_status"),
        "source_post_repair_reconciliation_hash": post_repair_reconciliation_report.get("post_repair_reconciliation_hash"),
        "source_post_repair_reconciliation_status": post_repair_reconciliation_report.get("post_repair_reconciliation_status"),
        "queue_item_count": len(items),
        "ledger_candidate_review_ready_count": sum(1 for item in items if item["ready_for_operator_ledger_candidate_review"]),
        "runtime_cycle_rerun_required_count": sum(1 for item in items if item["requires_runtime_cycle_rerun"]),
        "recovery_guard_rerun_required_count": sum(1 for item in items if item["requires_recovery_guard_rerun"]),
        "hash_operator_reconciliation_required_count": sum(1 for item in items if item["requires_hash_operator_reconciliation"]),
        "candidate_current_evidence_usable_count": sum(1 for item in items if item["candidate_current_evidence_usable"]),
        "queue_status": "BLOCKED",
        "primary_blocker_code": REPAIR_OPERATOR_QUEUE_BLOCKER_CODE,
        "blocker_codes": sorted(blockers),
        "items": items,
        "operator_next_action": (
            "Review the single ledger-candidate-ready item first; all other blocked replacements require PAPER cycle rerun "
            "or recovery guard evidence before ledger repair."
        ),
        "current_evidence_mutation_allowed": False,
        "persistent_loop_mutation_allowed": False,
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
        "queue_hash": "",
    }
    report["queue_hash"] = upbit_paper_repair_operator_queue_hash(report)
    return report


def write_upbit_paper_repair_operator_queue_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_repair_operator_queue_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_repair_operator_queue_report(report: dict[str, Any]) -> UpbitPaperRepairOperatorQueueValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "queue_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "queue_role",
        "source_blocked_repair_plan_hash",
        "source_blocked_repair_plan_status",
        "source_ledger_rollup_repair_hash",
        "source_ledger_rollup_repair_status",
        "source_post_repair_reconciliation_hash",
        "source_post_repair_reconciliation_status",
        "queue_item_count",
        "ledger_candidate_review_ready_count",
        "runtime_cycle_rerun_required_count",
        "recovery_guard_rerun_required_count",
        "hash_operator_reconciliation_required_count",
        "candidate_current_evidence_usable_count",
        "queue_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "current_evidence_mutation_allowed",
        "persistent_loop_mutation_allowed",
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
        "queue_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperRepairOperatorQueueValidationResult("FAIL", f"repair operator queue missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_REPAIR_OPERATOR_QUEUE_SCHEMA_ID:
        return UpbitPaperRepairOperatorQueueValidationResult("FAIL", "repair operator queue schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("queue_hash") != upbit_paper_repair_operator_queue_hash(report):
        return UpbitPaperRepairOperatorQueueValidationResult("FAIL", "repair operator queue hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperRepairOperatorQueueValidationResult("BLOCKED", "repair operator queue scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != REPAIR_OPERATOR_QUEUE_TRUTH_ROLE or report.get("queue_role") != REPAIR_OPERATOR_QUEUE_ROLE:
        return UpbitPaperRepairOperatorQueueValidationResult("BLOCKED", "repair operator queue cannot claim execution/live truth", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "current_evidence_mutation_allowed",
        "persistent_loop_mutation_allowed",
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
        return UpbitPaperRepairOperatorQueueValidationResult("BLOCKED", "repair operator queue created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if report.get("queue_status") != "BLOCKED" or report.get("primary_blocker_code") != REPAIR_OPERATOR_QUEUE_BLOCKER_CODE:
        return UpbitPaperRepairOperatorQueueValidationResult("BLOCKED", "repair operator queue must stay blocked until ledger/recovery reconciliation completes", REPAIR_OPERATOR_QUEUE_BLOCKER_CODE)
    blocker_codes = set(report.get("blocker_codes") or [])
    if REPAIR_OPERATOR_QUEUE_BLOCKER_CODE not in blocker_codes:
        return UpbitPaperRepairOperatorQueueValidationResult("FAIL", "repair operator queue missing primary blocker rollup", "SCHEMA_IDENTITY_MISMATCH")
    items = report.get("items")
    if not isinstance(items, list) or report.get("queue_item_count") != len(items):
        return UpbitPaperRepairOperatorQueueValidationResult("FAIL", "repair operator queue item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected = {
        "ledger_candidate_review_ready_count": 0,
        "runtime_cycle_rerun_required_count": 0,
        "recovery_guard_rerun_required_count": 0,
        "hash_operator_reconciliation_required_count": 0,
        "candidate_current_evidence_usable_count": 0,
    }
    seen_priorities: set[int] = set()
    session_id = str(report.get("session_id"))
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperRepairOperatorQueueValidationResult("FAIL", "repair operator queue item must be object", "SCHEMA_IDENTITY_MISMATCH")
        item_required = {
            "priority_order",
            "replacement_loop_id",
            "replacement_path",
            "safe_repair_lane",
            "operator_action",
            "ready_for_operator_ledger_candidate_review",
            "requires_runtime_cycle_rerun",
            "requires_recovery_guard_rerun",
            "requires_hash_operator_reconciliation",
            "cycle_ledger_jsonl_missing_count",
            "cycle_ledger_jsonl_missing_paths",
            "paper_ledger_rollup_path",
            "paper_ledger_rollup_artifact_exists",
            "candidate_rollup_artifact_path",
            "candidate_rollup_validator_status",
            "candidate_rollup_hash",
            "candidate_current_evidence_usable",
            "post_repair_candidate_classification",
            "post_repair_item_blocker_code",
            "blocking_codes",
            "current_evidence_mutation_allowed",
            "persistent_loop_mutation_allowed",
            "source_delete_allowed",
            "live_permission_created",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperRepairOperatorQueueValidationResult("FAIL", f"repair operator queue item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH")
        priority = int(item.get("priority_order") or 0)
        if priority < 1 or priority in seen_priorities:
            return UpbitPaperRepairOperatorQueueValidationResult("FAIL", "repair operator queue priority order invalid", "SCHEMA_IDENTITY_MISMATCH")
        seen_priorities.add(priority)
        for path_field in ("replacement_path", "paper_ledger_rollup_path", "candidate_rollup_artifact_path"):
            path_value = item.get(path_field)
            if path_value is not None and not _artifact_path_allowed(str(path_value), session_id):
                return UpbitPaperRepairOperatorQueueValidationResult("BLOCKED", f"repair operator queue {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if (
            item.get("current_evidence_mutation_allowed")
            or item.get("persistent_loop_mutation_allowed")
            or item.get("source_delete_allowed")
            or item.get("live_permission_created")
        ):
            return UpbitPaperRepairOperatorQueueValidationResult("BLOCKED", "repair operator queue item attempted mutation or live permission", "LIVE_FINAL_GUARD_FAILED")
        if item.get("candidate_current_evidence_usable"):
            return UpbitPaperRepairOperatorQueueValidationResult("BLOCKED", "repair operator queue cannot mark repair candidates usable", "LIVE_FINAL_GUARD_FAILED")
        blocking_codes = set(item.get("blocking_codes") or [])
        if not blocking_codes or BLOCKED_REPAIR_PLAN_BLOCKER_CODE not in blocking_codes:
            return UpbitPaperRepairOperatorQueueValidationResult("FAIL", "repair operator queue item missing blocked repair plan blocker", "SCHEMA_IDENTITY_MISMATCH")
        lane = item.get("safe_repair_lane")
        if lane == "LEDGER_ROLLUP_REBUILD_READY":
            if not item.get("ready_for_operator_ledger_candidate_review"):
                return UpbitPaperRepairOperatorQueueValidationResult("FAIL", "ledger-ready item must be operator review ready", "SCHEMA_IDENTITY_MISMATCH")
            if item.get("requires_runtime_cycle_rerun") or item.get("requires_recovery_guard_rerun"):
                return UpbitPaperRepairOperatorQueueValidationResult("FAIL", "ledger-ready item cannot require rerun or recovery guard", "SCHEMA_IDENTITY_MISMATCH")
        elif item.get("ready_for_operator_ledger_candidate_review"):
            return UpbitPaperRepairOperatorQueueValidationResult("FAIL", "non-ledger-ready item marked operator review ready", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("ready_for_operator_ledger_candidate_review"):
            expected["ledger_candidate_review_ready_count"] += 1
        if item.get("requires_runtime_cycle_rerun"):
            expected["runtime_cycle_rerun_required_count"] += 1
        if item.get("requires_recovery_guard_rerun"):
            expected["recovery_guard_rerun_required_count"] += 1
        if item.get("requires_hash_operator_reconciliation"):
            expected["hash_operator_reconciliation_required_count"] += 1
        if item.get("candidate_current_evidence_usable"):
            expected["candidate_current_evidence_usable_count"] += 1
    for field, value in expected.items():
        if report.get(field) != value:
            return UpbitPaperRepairOperatorQueueValidationResult("FAIL", f"repair operator queue count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("candidate_current_evidence_usable_count") != 0:
        return UpbitPaperRepairOperatorQueueValidationResult("BLOCKED", "repair operator queue exposed current evidence usability", "LIVE_FINAL_GUARD_FAILED")
    return UpbitPaperRepairOperatorQueueValidationResult(
        "PASS",
        "Upbit PAPER repair operator queue prioritizes blocked repairs without mutating evidence or live state",
        None,
    )
