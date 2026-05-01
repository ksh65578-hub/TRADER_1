from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import (
    STALE_LOOP_BLOCKER_CODE,
    validate_upbit_paper_stale_loop_reconciliation_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_REGENERATION_PLAN_SCHEMA_ID = "trader1.upbit_paper_stale_loop_regeneration_plan.v1"
REGENERATION_PLAN_ROLE = "PAPER_RUNTIME_STALE_LOOP_REGENERATION_PLAN_NOT_EXECUTION"
DEFAULT_REGENERATION_SUFFIX = "regenerated-current-schema"


@dataclass(frozen=True)
class UpbitPaperStaleLoopRegenerationPlanValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def stale_loop_regeneration_plan_hash(plan: dict[str, Any]) -> str:
    payload = dict(plan)
    payload.pop("plan_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return path.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "live" not in parts


def _safe_loop_id(value: Any, fallback_index: int) -> str:
    raw = str(value or f"legacy-loop-{fallback_index}")
    safe = "".join(char.lower() if char.isalnum() else "-" for char in raw).strip("-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe or f"legacy-loop-{fallback_index}"


def _replacement_loop_id(item: dict[str, Any], index: int) -> str:
    return f"{_safe_loop_id(item.get('loop_id'), index)}-{DEFAULT_REGENERATION_SUFFIX}"


def _replacement_path(session_id: str, replacement_loop_id: str) -> str:
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        f"{replacement_loop_id}.persistent_loop_report.json"
    )


def _build_plan_item(item: dict[str, Any], *, index: int, session_id: str) -> dict[str, Any]:
    replacement_loop_id = _replacement_loop_id(item, index)
    classification = item["classification"]
    if classification == "LEGACY_SCHEMA_DRIFT":
        action = "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT"
        blocking_reason = None
    elif classification == "RECONCILIATION_REQUIRED":
        action = "OPERATOR_REVIEW_REQUIRED"
        blocking_reason = "RECONCILIATION_REQUIRED_OPERATOR_REVIEW"
    elif classification == "UNREADABLE_OR_CORRUPT":
        action = "OPERATOR_REVIEW_REQUIRED"
        blocking_reason = "CORRUPT_SOURCE_REQUIRES_OPERATOR_REVIEW"
    elif classification in {"UNSAFE_BLOCKED", "SCOPE_MISMATCH_BLOCKED"}:
        action = "OPERATOR_REVIEW_REQUIRED"
        blocking_reason = "UNSAFE_SOURCE_REQUIRES_OPERATOR_REVIEW"
    else:
        action = "RETAIN_EXCLUDED_REFERENCE"
        blocking_reason = "SOURCE_NOT_REGENERATION_ELIGIBLE"
    return {
        "source_path": item["source_path"],
        "source_hash": item.get("source_hash"),
        "source_classification": classification,
        "source_loop_id": item.get("loop_id"),
        "source_generated_at_utc": item.get("generated_at_utc"),
        "source_evidence_usable_current": bool(item.get("evidence_usable_current")),
        "planned_action": action,
        "planned_replacement_loop_id": replacement_loop_id if action == "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT" else None,
        "planned_replacement_path": _replacement_path(session_id, replacement_loop_id)
        if action == "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT"
        else None,
        "overwrite_source_allowed": False,
        "delete_source_allowed": False,
        "automatic_live_or_order_allowed": False,
        "requires_operator_review": action == "OPERATOR_REVIEW_REQUIRED",
        "blocking_reason": blocking_reason,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_stale_loop_regeneration_plan(
    *,
    root: Path,
    reconciliation_report: dict[str, Any],
    plan_id: str = "upbit-paper-stale-loop-regeneration-plan",
) -> dict[str, Any]:
    root = Path(root).resolve()
    result = validate_upbit_paper_stale_loop_reconciliation_report(reconciliation_report)
    if result.status != "PASS":
        raise ValueError(f"invalid reconciliation report: {result.status} {result.blocker_code} {result.message}")
    session_id = str(reconciliation_report["session_id"])
    excluded_items = [
        item for item in reconciliation_report.get("items", [])
        if isinstance(item, dict) and not item.get("evidence_usable_current")
    ]
    plan_items = [
        _build_plan_item(item, index=index, session_id=session_id)
        for index, item in enumerate(excluded_items, start=1)
    ]
    regeneration_item_count = sum(
        1 for item in plan_items if item["planned_action"] == "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT"
    )
    operator_review_count = sum(1 for item in plan_items if item["requires_operator_review"])
    overwrite_or_delete_count = sum(1 for item in plan_items if item["overwrite_source_allowed"] or item["delete_source_allowed"])
    duplicate_replacement_count = len(
        [
            path for path in [item.get("planned_replacement_path") for item in plan_items]
            if path is not None
        ]
    ) - len({path for path in [item.get("planned_replacement_path") for item in plan_items] if path is not None})
    plan_status = "READY_FOR_SAFE_PAPER_REGENERATION" if regeneration_item_count and not operator_review_count and not duplicate_replacement_count else "BLOCKED"
    primary_blocker_code = None if plan_status == "READY_FOR_SAFE_PAPER_REGENERATION" else "STALE_LOOP_REGENERATION_REQUIRED"
    if operator_review_count:
        primary_blocker_code = "STALE_LOOP_REGENERATION_OPERATOR_REVIEW_REQUIRED"
    if duplicate_replacement_count:
        primary_blocker_code = "STALE_LOOP_REPLACEMENT_PATH_COLLISION"
    if overwrite_or_delete_count:
        primary_blocker_code = "STALE_LOOP_DELETION_OR_OVERWRITE_BLOCKED"
    plan = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_REGENERATION_PLAN_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "plan_id": plan_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "plan_role": REGENERATION_PLAN_ROLE,
        "source_reconciliation_status": reconciliation_report["reconciliation_status"],
        "source_reconciliation_hash": reconciliation_report["reconciliation_hash"],
        "source_loop_report_count": reconciliation_report["source_loop_report_count"],
        "source_current_accepted_count": reconciliation_report["current_accepted_count"],
        "source_excluded_count": reconciliation_report["excluded_from_current_evidence_count"],
        "legacy_schema_drift_count": reconciliation_report["legacy_schema_drift_count"],
        "unsafe_blocked_count": reconciliation_report["unsafe_blocked_count"],
        "invalid_json_count": reconciliation_report["invalid_json_count"],
        "duplicate_runtime_cycle_hash_count": reconciliation_report["duplicate_runtime_cycle_hash_count"],
        "regeneration_item_count": regeneration_item_count,
        "operator_review_item_count": operator_review_count,
        "duplicate_replacement_path_count": duplicate_replacement_count,
        "overwrite_or_delete_count": overwrite_or_delete_count,
        "plan_status": plan_status,
        "primary_blocker_code": primary_blocker_code,
        "stale_loop_blocker_code": STALE_LOOP_BLOCKER_CODE,
        "safe_regeneration_scope": "UPBIT_KRW_SPOT_PAPER_PUBLIC_OR_STATIC_DATA_ONLY",
        "automatic_regeneration_allowed": False,
        "operator_confirmation_required_before_execution": False,
        "delete_source_allowed": False,
        "overwrite_source_allowed": False,
        "actual_regeneration_performed": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "items": plan_items,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "plan_hash": "",
    }
    plan["plan_hash"] = stale_loop_regeneration_plan_hash(plan)
    return plan


def write_upbit_paper_stale_loop_regeneration_plan(*, root: Path, plan: dict[str, Any]) -> Path:
    path = _runtime_base(root, str(plan["session_id"])) / "paper_runtime" / "upbit_paper_stale_loop_regeneration_plan.json"
    durable_atomic_write_json(path, plan)
    return path


def validate_upbit_paper_stale_loop_regeneration_plan(plan: dict[str, Any]) -> UpbitPaperStaleLoopRegenerationPlanValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "plan_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "plan_role",
        "source_reconciliation_status",
        "source_reconciliation_hash",
        "source_loop_report_count",
        "source_current_accepted_count",
        "source_excluded_count",
        "legacy_schema_drift_count",
        "unsafe_blocked_count",
        "invalid_json_count",
        "duplicate_runtime_cycle_hash_count",
        "regeneration_item_count",
        "operator_review_item_count",
        "duplicate_replacement_path_count",
        "overwrite_or_delete_count",
        "plan_status",
        "primary_blocker_code",
        "stale_loop_blocker_code",
        "safe_regeneration_scope",
        "automatic_regeneration_allowed",
        "operator_confirmation_required_before_execution",
        "delete_source_allowed",
        "overwrite_source_allowed",
        "actual_regeneration_performed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "items",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "plan_hash",
    }
    missing = sorted(required - set(plan))
    if missing:
        return UpbitPaperStaleLoopRegenerationPlanValidationResult("FAIL", f"regeneration plan missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if plan.get("schema_id") != UPBIT_PAPER_STALE_LOOP_REGENERATION_PLAN_SCHEMA_ID:
        return UpbitPaperStaleLoopRegenerationPlanValidationResult("FAIL", "regeneration plan schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if plan.get("plan_hash") != stale_loop_regeneration_plan_hash(plan):
        return UpbitPaperStaleLoopRegenerationPlanValidationResult("FAIL", "regeneration plan hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if plan.get("exchange") != "UPBIT" or plan.get("market_type") != "KRW_SPOT" or plan.get("mode") != "PAPER":
        return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "regeneration plan scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if plan.get("plan_role") != REGENERATION_PLAN_ROLE or plan.get("safe_regeneration_scope") != "UPBIT_KRW_SPOT_PAPER_PUBLIC_OR_STATIC_DATA_ONLY":
        return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "regeneration plan cannot claim execution, live, or cross-scope authority", "LIVE_FINAL_GUARD_FAILED")
    forbidden_fields = (
        "automatic_regeneration_allowed",
        "operator_confirmation_required_before_execution",
        "delete_source_allowed",
        "overwrite_source_allowed",
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
        "scale_up_allowed",
    )
    if any(plan.get(field) for field in forbidden_fields):
        return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "regeneration plan attempted execution, deletion, live/order, promotion, long-run, or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    items = plan.get("items")
    if not isinstance(items, list) or plan.get("source_excluded_count") != len(items):
        return UpbitPaperStaleLoopRegenerationPlanValidationResult("FAIL", "regeneration plan item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    regeneration_count = 0
    operator_review_count = 0
    replacement_paths: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopRegenerationPlanValidationResult("FAIL", "regeneration plan item must be an object", "SCHEMA_IDENTITY_MISMATCH")
        item_required = {
            "source_path",
            "source_hash",
            "source_classification",
            "source_loop_id",
            "source_generated_at_utc",
            "source_evidence_usable_current",
            "planned_action",
            "planned_replacement_loop_id",
            "planned_replacement_path",
            "overwrite_source_allowed",
            "delete_source_allowed",
            "automatic_live_or_order_allowed",
            "requires_operator_review",
            "blocking_reason",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopRegenerationPlanValidationResult("FAIL", f"regeneration plan item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH")
        if not isinstance(item["source_path"], str) or not _artifact_path_allowed(item["source_path"], str(plan.get("session_id"))):
            return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "regeneration plan source path escaped UPBIT PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if item.get("source_evidence_usable_current"):
            return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "current evidence source cannot be included in stale regeneration plan", "STALE_LOOP_REGENERATION_REQUIRED")
        if item.get("overwrite_source_allowed") or item.get("delete_source_allowed") or item.get("automatic_live_or_order_allowed"):
            return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "regeneration plan item attempted overwrite, delete, or live/order permission", "LIVE_FINAL_GUARD_FAILED")
        if item.get("live_order_ready") or item.get("live_order_allowed") or item.get("can_live_trade") or item.get("scale_up_allowed"):
            return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "regeneration plan item created live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
        if item.get("planned_action") == "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT":
            regeneration_count += 1
            replacement_path = item.get("planned_replacement_path")
            if not isinstance(replacement_path, str) or not _artifact_path_allowed(replacement_path, str(plan.get("session_id"))):
                return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "regeneration replacement path escaped UPBIT PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
            if replacement_path == item["source_path"]:
                return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "regeneration replacement path cannot overwrite source", "LIVE_FINAL_GUARD_FAILED")
            replacement_paths.append(replacement_path)
            if item.get("source_classification") != "LEGACY_SCHEMA_DRIFT":
                return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "only legacy schema drift sources can be regenerated automatically as PAPER artifacts", "STALE_LOOP_REGENERATION_REQUIRED")
        elif item.get("requires_operator_review"):
            operator_review_count += 1
        else:
            return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "non-regeneration item must require operator review", "STALE_LOOP_REGENERATION_REQUIRED")
    duplicate_replacement_count = len(replacement_paths) - len(set(replacement_paths))
    overwrite_or_delete_count = sum(1 for item in items if item.get("overwrite_source_allowed") or item.get("delete_source_allowed"))
    if (
        plan.get("regeneration_item_count") != regeneration_count
        or plan.get("operator_review_item_count") != operator_review_count
        or plan.get("duplicate_replacement_path_count") != duplicate_replacement_count
        or plan.get("overwrite_or_delete_count") != overwrite_or_delete_count
    ):
        return UpbitPaperStaleLoopRegenerationPlanValidationResult("FAIL", "regeneration plan rollup count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if duplicate_replacement_count or operator_review_count or overwrite_or_delete_count:
        if plan.get("plan_status") != "BLOCKED" or not plan.get("primary_blocker_code"):
            return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "unsafe regeneration plan must remain blocked", "STALE_LOOP_REGENERATION_REQUIRED")
    elif regeneration_count:
        if plan.get("plan_status") != "READY_FOR_SAFE_PAPER_REGENERATION" or plan.get("primary_blocker_code") is not None:
            return UpbitPaperStaleLoopRegenerationPlanValidationResult("FAIL", "safe regeneration plan status mismatch", "SCHEMA_IDENTITY_MISMATCH")
    else:
        if plan.get("plan_status") != "BLOCKED":
            return UpbitPaperStaleLoopRegenerationPlanValidationResult("BLOCKED", "empty regeneration plan cannot pass", "STALE_LOOP_REGENERATION_REQUIRED")
    return UpbitPaperStaleLoopRegenerationPlanValidationResult("PASS", "Upbit PAPER stale loop regeneration plan is source-preserving, namespace-scoped, and live-blocked", None)
