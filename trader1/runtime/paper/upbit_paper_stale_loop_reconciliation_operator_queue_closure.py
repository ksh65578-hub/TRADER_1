from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    validate_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_post_regeneration_reconciliation import (
    POST_REGENERATION_RECONCILIATION_BLOCKER_CODE,
    validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1"
)
STALE_LOOP_OPERATOR_QUEUE_CLOSURE_TRUTH_ROLE = (
    "paper_runtime_stale_loop_reconciliation_operator_queue_closure_truth"
)
STALE_LOOP_OPERATOR_QUEUE_CLOSURE_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE_DISPLAY_ONLY_NOT_EVIDENCE"
)
STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE = (
    "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING"
)

LEDGER_ONLY_RECHECK_REASONS = {
    "LEDGER_ROLLUP_BLOCKED",
    "LEDGER_ROLLUP_RECONCILIATION_REQUIRED",
    "LOOP_RECONCILIATION_REQUIRED",
    "LOOP_STATUS_BLOCKED",
}
RECOVERY_RECHECK_REASONS = {
    "RECOVERY_GUARD_BLOCKED",
    "PARTIAL_WRITE_RECOVERY_REQUIRED",
    "PAPER_RUNTIME_RESUME_BLOCKED",
}


@dataclass(frozen=True)
class UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_reconciliation_operator_queue_closure_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("closure_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    return (
        normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/")
        and ".." not in parts
        and "/live/" not in normalized
    )


def _ledger_evidence_passes(ledger_evidence_report: dict[str, Any]) -> bool:
    return (
        ledger_evidence_report.get("runtime_evidence_status") == "PASS"
        and ledger_evidence_report.get("source_rollup_validation_status") == "PASS"
        and ledger_evidence_report.get("idempotency_status") == "PASS"
        and ledger_evidence_report.get("reconciliation_status") == "PASS"
        and ledger_evidence_report.get("portfolio_provenance_status") == "PASS"
        and ledger_evidence_report.get("mismatch_count") == 0
        and ledger_evidence_report.get("live_order_allowed") is False
        and ledger_evidence_report.get("can_live_trade") is False
        and ledger_evidence_report.get("scale_up_allowed") is False
    )


def _item_lane(*, item: dict[str, Any], ledger_evidence_ready: bool) -> tuple[str, str, bool]:
    reasons = {str(code) for code in item.get("blocked_repair_reason_codes") or []}
    if item.get("unsafe_live_or_order_flag_detected") or item.get("source_path_scope_status") != "MATCH" or item.get("replacement_path_scope_status") != "MATCH":
        return (
            "UNSAFE_OR_SCOPE_BLOCKED",
            "Quarantine this regenerated replacement for operator review before any reconciliation attempt.",
            False,
        )
    if reasons & RECOVERY_RECHECK_REASONS:
        return (
            "RECOVERY_GUARD_REQUIRED",
            "Rerun the PAPER recovery guard and resolve partial-write recovery before ledger recheck.",
            False,
        )
    if "RUNTIME_CYCLE_RECONCILIATION_REQUIRED" in reasons:
        return (
            "RUNTIME_CYCLE_RERUN_REQUIRED",
            "Rerun the affected PAPER runtime cycle, then rebuild ledger evidence before recheck.",
            False,
        )
    if (
        ledger_evidence_ready
        and reasons
        and reasons <= LEDGER_ONLY_RECHECK_REASONS
        and item.get("recovery_reconciliation_status") == "PASS"
        and item.get("cycle_reconciliation_status") == "PASS"
        and item.get("ledger_reconciliation_status") == "BLOCKED"
    ):
        return (
            "LEDGER_RECHECK_READY",
            "Use the current PASS ledger/idempotency evidence to recheck this stale regenerated replacement; do not mark it current evidence yet.",
            True,
        )
    return (
        "OPERATOR_REVIEW_REQUIRED",
        "Inspect this blocked regenerated replacement before any further repair or evidence decision.",
        False,
    )


def _build_item(
    *,
    priority_order: int,
    item: dict[str, Any],
    ledger_evidence_report: dict[str, Any],
    ledger_evidence_ready: bool,
) -> dict[str, Any]:
    lane, operator_action, recheck_ready = _item_lane(item=item, ledger_evidence_ready=ledger_evidence_ready)
    reasons = sorted({str(code) for code in item.get("blocked_repair_reason_codes") or []})
    blocking_codes = sorted(
        {
            STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE,
            POST_REGENERATION_RECONCILIATION_BLOCKER_CODE,
            *reasons,
        }
    )
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(item.get("replacement_loop_id") or "UNKNOWN"),
        "source_path": str(item.get("source_path") or ""),
        "replacement_path": str(item.get("replacement_path") or ""),
        "source_item_classification": str(item.get("classification") or "UNKNOWN"),
        "source_item_blocker_code": item.get("item_blocker_code"),
        "source_blocked_repair_reason_codes": reasons,
        "source_recovery_reconciliation_status": str(item.get("recovery_reconciliation_status") or "UNKNOWN"),
        "source_ledger_reconciliation_status": str(item.get("ledger_reconciliation_status") or "UNKNOWN"),
        "source_cycle_reconciliation_status": str(item.get("cycle_reconciliation_status") or "UNKNOWN"),
        "current_ledger_evidence_status": str(ledger_evidence_report.get("runtime_evidence_status") or "UNKNOWN"),
        "current_ledger_idempotency_status": str(ledger_evidence_report.get("idempotency_status") or "UNKNOWN"),
        "current_ledger_reconciliation_status": str(ledger_evidence_report.get("reconciliation_status") or "UNKNOWN"),
        "current_ledger_head_hash": ledger_evidence_report.get("source_ledger_head_hash"),
        "current_ledger_rollup_hash": ledger_evidence_report.get("source_rollup_hash"),
        "closure_lane": lane,
        "closure_recheck_ready": recheck_ready,
        "requires_recovery_guard_rerun": lane == "RECOVERY_GUARD_REQUIRED",
        "requires_runtime_cycle_rerun": lane == "RUNTIME_CYCLE_RERUN_REQUIRED",
        "requires_operator_review": lane in {"OPERATOR_REVIEW_REQUIRED", "UNSAFE_OR_SCOPE_BLOCKED"},
        "operator_action": operator_action,
        "blocking_codes": blocking_codes,
        "current_evidence_usable_after_closure": False,
        "current_evidence_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(
    *,
    post_regeneration_reconciliation_report: dict[str, Any],
    ledger_idempotency_evidence_report: dict[str, Any],
    closure_id: str = "upbit-paper-stale-loop-reconciliation-operator-queue-closure",
) -> dict[str, Any]:
    post_result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
        post_regeneration_reconciliation_report
    )
    ledger_result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(ledger_idempotency_evidence_report)
    session_id = str(post_regeneration_reconciliation_report.get("session_id", "UNKNOWN"))
    ledger_evidence_ready = ledger_result.status == "PASS" and _ledger_evidence_passes(ledger_idempotency_evidence_report)
    blocked_items = [
        item
        for item in post_regeneration_reconciliation_report.get("items", [])
        if isinstance(item, dict)
        and item.get("classification") == "REGENERATED_CURRENT_BLOCKED_RECONCILIATION_REQUIRED"
    ]
    items = [
        _build_item(
            priority_order=index,
            item=item,
            ledger_evidence_report=ledger_idempotency_evidence_report,
            ledger_evidence_ready=ledger_evidence_ready,
        )
        for index, item in enumerate(blocked_items, start=1)
    ]
    closure_status = "PASS" if not items and post_regeneration_reconciliation_report.get("post_reconciliation_status") == "PASS" else "BLOCKED"
    blocker_codes = set()
    if closure_status != "PASS":
        blocker_codes.add(STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE)
    if post_result.status != "PASS":
        blocker_codes.add(post_result.blocker_code or POST_REGENERATION_RECONCILIATION_BLOCKER_CODE)
    if ledger_result.status != "PASS":
        blocker_codes.add(ledger_result.blocker_code or "LEDGER_INTEGRITY_FAIL")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocking_codes"])
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "closure_id": closure_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_OPERATOR_QUEUE_CLOSURE_TRUTH_ROLE,
        "closure_role": STALE_LOOP_OPERATOR_QUEUE_CLOSURE_ROLE,
        "source_post_regeneration_reconciliation_hash": post_regeneration_reconciliation_report.get("post_reconciliation_hash"),
        "source_post_regeneration_reconciliation_status": post_regeneration_reconciliation_report.get("post_reconciliation_status"),
        "source_post_regeneration_reconciliation_validator_status": post_result.status,
        "source_post_regeneration_reconciliation_blocker_code": post_result.blocker_code,
        "source_ledger_idempotency_evidence_hash": ledger_idempotency_evidence_report.get("evidence_hash"),
        "source_ledger_idempotency_evidence_status": ledger_idempotency_evidence_report.get("runtime_evidence_status"),
        "source_ledger_idempotency_validator_status": ledger_result.status,
        "source_ledger_idempotency_blocker_code": ledger_result.blocker_code,
        "source_ledger_reconciliation_status": ledger_idempotency_evidence_report.get("reconciliation_status"),
        "source_ledger_idempotency_status": ledger_idempotency_evidence_report.get("idempotency_status"),
        "source_ledger_mismatch_count": int(ledger_idempotency_evidence_report.get("mismatch_count") or 0),
        "source_ledger_head_hash": ledger_idempotency_evidence_report.get("source_ledger_head_hash"),
        "source_ledger_rollup_hash": ledger_idempotency_evidence_report.get("source_rollup_hash"),
        "closure_item_count": len(items),
        "source_blocked_item_count": len(blocked_items),
        "ledger_recheck_ready_count": sum(1 for item in items if item["closure_lane"] == "LEDGER_RECHECK_READY"),
        "recovery_guard_required_count": sum(1 for item in items if item["closure_lane"] == "RECOVERY_GUARD_REQUIRED"),
        "runtime_cycle_rerun_required_count": sum(1 for item in items if item["closure_lane"] == "RUNTIME_CYCLE_RERUN_REQUIRED"),
        "operator_review_required_count": sum(1 for item in items if item["closure_lane"] == "OPERATOR_REVIEW_REQUIRED"),
        "unsafe_or_scope_blocked_count": sum(1 for item in items if item["closure_lane"] == "UNSAFE_OR_SCOPE_BLOCKED"),
        "current_evidence_usable_after_closure_count": 0,
        "current_evidence_write_allowed_count": 0,
        "closure_status": closure_status,
        "primary_blocker_code": None if closure_status == "PASS" else STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": (
            "Recheck ledger-only stale-loop replacements with the current PASS ledger/idempotency evidence; keep recovery-blocked replacements out of current evidence."
            if items
            else "No blocked stale-loop replacements require operator queue closure."
        ),
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
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
        "closure_hash": "",
    }
    report["closure_hash"] = upbit_paper_stale_loop_reconciliation_operator_queue_closure_hash(report)
    return report


def write_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "closure_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "closure_role",
        "source_post_regeneration_reconciliation_hash",
        "source_post_regeneration_reconciliation_status",
        "source_post_regeneration_reconciliation_validator_status",
        "source_post_regeneration_reconciliation_blocker_code",
        "source_ledger_idempotency_evidence_hash",
        "source_ledger_idempotency_evidence_status",
        "source_ledger_idempotency_validator_status",
        "source_ledger_idempotency_blocker_code",
        "source_ledger_reconciliation_status",
        "source_ledger_idempotency_status",
        "source_ledger_mismatch_count",
        "source_ledger_head_hash",
        "source_ledger_rollup_hash",
        "closure_item_count",
        "source_blocked_item_count",
        "ledger_recheck_ready_count",
        "recovery_guard_required_count",
        "runtime_cycle_rerun_required_count",
        "operator_review_required_count",
        "unsafe_or_scope_blocked_count",
        "current_evidence_usable_after_closure_count",
        "current_evidence_write_allowed_count",
        "closure_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
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
        "closure_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
            "FAIL", f"stale-loop operator queue closure missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE_SCHEMA_ID:
        return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
            "FAIL", "stale-loop operator queue closure schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("closure_hash") != upbit_paper_stale_loop_reconciliation_operator_queue_closure_hash(report):
        return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
            "FAIL", "stale-loop operator queue closure hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
            "BLOCKED", "stale-loop operator queue closure scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if report.get("truth_role") != STALE_LOOP_OPERATOR_QUEUE_CLOSURE_TRUTH_ROLE or report.get("closure_role") != STALE_LOOP_OPERATOR_QUEUE_CLOSURE_ROLE:
        return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
            "BLOCKED", "stale-loop operator queue closure cannot claim execution or live truth", "LIVE_FINAL_GUARD_FAILED"
        )
    forbidden = (
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
    if any(report.get(field) for field in forbidden):
        return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
            "BLOCKED", "stale-loop operator queue closure created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED"
        )
    if not report.get("display_only") or not report.get("dashboard_truth_only") or not report.get("paper_only"):
        return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
            "BLOCKED", "stale-loop operator queue closure must remain display-only PAPER evidence", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("closure_item_count") != len(items) or report.get("source_blocked_item_count") != len(items):
        return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
            "FAIL", "stale-loop operator queue closure item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected = {
        "ledger_recheck_ready_count": 0,
        "recovery_guard_required_count": 0,
        "runtime_cycle_rerun_required_count": 0,
        "operator_review_required_count": 0,
        "unsafe_or_scope_blocked_count": 0,
        "current_evidence_usable_after_closure_count": 0,
        "current_evidence_write_allowed_count": 0,
    }
    session_id = str(report.get("session_id"))
    seen_priorities: set[int] = set()
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                "FAIL", "stale-loop operator queue closure item must be object", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_required = {
            "priority_order",
            "replacement_loop_id",
            "source_path",
            "replacement_path",
            "source_item_classification",
            "source_item_blocker_code",
            "source_blocked_repair_reason_codes",
            "source_recovery_reconciliation_status",
            "source_ledger_reconciliation_status",
            "source_cycle_reconciliation_status",
            "current_ledger_evidence_status",
            "current_ledger_idempotency_status",
            "current_ledger_reconciliation_status",
            "current_ledger_head_hash",
            "current_ledger_rollup_hash",
            "closure_lane",
            "closure_recheck_ready",
            "requires_recovery_guard_rerun",
            "requires_runtime_cycle_rerun",
            "requires_operator_review",
            "operator_action",
            "blocking_codes",
            "current_evidence_usable_after_closure",
            "current_evidence_write_allowed",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "actual_long_run_evidence_created",
            "live_permission_created",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                "FAIL", f"stale-loop operator queue closure item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH"
            )
        priority = int(item.get("priority_order") or 0)
        if priority < 1 or priority in seen_priorities:
            return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                "FAIL", "stale-loop operator queue closure priority invalid", "SCHEMA_IDENTITY_MISMATCH"
            )
        seen_priorities.add(priority)
        if not _artifact_path_allowed(str(item.get("source_path") or ""), session_id) or not _artifact_path_allowed(
            str(item.get("replacement_path") or ""), session_id
        ):
            return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                "BLOCKED", "stale-loop operator queue closure item escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
            )
        if (
            item.get("current_evidence_usable_after_closure")
            or item.get("current_evidence_write_allowed")
            or item.get("persistent_loop_mutation_allowed")
            or item.get("replacement_write_allowed")
            or item.get("source_delete_allowed")
            or item.get("actual_long_run_evidence_created")
            or item.get("live_permission_created")
        ):
            return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                "BLOCKED", "stale-loop operator queue closure item created evidence mutation or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        lane = item.get("closure_lane")
        if lane == "LEDGER_RECHECK_READY":
            expected["ledger_recheck_ready_count"] += 1
            reasons = set(item.get("source_blocked_repair_reason_codes") or [])
            if (
                item.get("closure_recheck_ready") is not True
                or not reasons
                or not reasons <= LEDGER_ONLY_RECHECK_REASONS
                or item.get("current_ledger_evidence_status") != "PASS"
                or item.get("current_ledger_idempotency_status") != "PASS"
                or item.get("current_ledger_reconciliation_status") != "PASS"
                or item.get("source_recovery_reconciliation_status") != "PASS"
                or item.get("source_cycle_reconciliation_status") != "PASS"
                or item.get("source_ledger_reconciliation_status") != "BLOCKED"
            ):
                return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                    "FAIL", "ledger-recheck-ready item lacks PASS ledger evidence or ledger-only source blockers", "LEDGER_INTEGRITY_FAIL"
                )
        else:
            if item.get("closure_recheck_ready"):
                return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                    "FAIL", "non-ledger lane cannot be marked recheck-ready", "SCHEMA_IDENTITY_MISMATCH"
                )
            if lane == "RECOVERY_GUARD_REQUIRED":
                expected["recovery_guard_required_count"] += 1
                if not item.get("requires_recovery_guard_rerun"):
                    return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                        "FAIL", "recovery lane must require recovery guard rerun", "SCHEMA_IDENTITY_MISMATCH"
                    )
            elif lane == "RUNTIME_CYCLE_RERUN_REQUIRED":
                expected["runtime_cycle_rerun_required_count"] += 1
                if not item.get("requires_runtime_cycle_rerun"):
                    return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                        "FAIL", "runtime-cycle lane must require cycle rerun", "SCHEMA_IDENTITY_MISMATCH"
                    )
            elif lane == "OPERATOR_REVIEW_REQUIRED":
                expected["operator_review_required_count"] += 1
                if not item.get("requires_operator_review"):
                    return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                        "FAIL", "operator-review lane must require operator review", "SCHEMA_IDENTITY_MISMATCH"
                    )
            elif lane == "UNSAFE_OR_SCOPE_BLOCKED":
                expected["unsafe_or_scope_blocked_count"] += 1
                if not item.get("requires_operator_review"):
                    return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                        "FAIL", "unsafe lane must require operator review", "SCHEMA_IDENTITY_MISMATCH"
                    )
            else:
                return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                    "FAIL", f"unknown stale-loop operator queue closure lane: {lane}", "SCHEMA_IDENTITY_MISMATCH"
                )
    for field, value in expected.items():
        if report.get(field) != value:
            return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                "FAIL", f"stale-loop operator queue closure count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if items:
        if report.get("closure_status") != "BLOCKED" or report.get("primary_blocker_code") != STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE:
            return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                "BLOCKED", "blocked stale-loop items must keep operator queue closure blocked", STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE
            )
        if STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE not in set(report.get("blocker_codes") or []):
            return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
                "FAIL", "stale-loop operator queue closure missing primary blocker", "SCHEMA_IDENTITY_MISMATCH"
            )
    elif report.get("closure_status") != "PASS" or report.get("primary_blocker_code") is not None:
        return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
            "FAIL", "clean stale-loop operator queue closure status mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    return UpbitPaperStaleLoopReconciliationOperatorQueueClosureValidationResult(
        "PASS",
        "Upbit PAPER stale-loop operator queue closure classifies blocked replacements without mutating evidence or live state",
        None,
    )
