from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck import (
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.v1"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_REVIEW_ONLY"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_TRUTH_ROLE = (
    "paper_runtime_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_truth"
)
ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_BLOCKER_CODE = (
    "ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_CURRENT_WRITES_BLOCKED"
)
POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE = "POST_RERUN_RECONCILIATION_REQUIRED"


@dataclass(frozen=True)
class UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash(
    report: dict[str, Any],
) -> str:
    payload = dict(report)
    payload.pop("event_id_scope_repaired_current_evidence_guard_hash", None)
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


def _operator_guidance_summary(operator_review_guidance_report: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(operator_review_guidance_report, dict):
        return {
            "operator_guidance_loaded": False,
            "operator_guidance_status": "NOT_LOADED",
            "operator_guidance_item_count": 0,
            "operator_guidance_forbidden_output_count": 0,
            "operator_guidance_current_evidence_write_allowed_count": 0,
            "operator_guidance_primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        }
    forbidden_outputs = operator_review_guidance_report.get("forbidden_outputs")
    guidance_items = operator_review_guidance_report.get("guidance_items")
    return {
        "operator_guidance_loaded": True,
        "operator_guidance_status": str(operator_review_guidance_report.get("guidance_status") or "BLOCKED"),
        "operator_guidance_item_count": len(guidance_items) if isinstance(guidance_items, list) else int(operator_review_guidance_report.get("guidance_item_count") or 0),
        "operator_guidance_forbidden_output_count": len(forbidden_outputs) if isinstance(forbidden_outputs, list) else int(operator_review_guidance_report.get("forbidden_output_count") or 0),
        "operator_guidance_current_evidence_write_allowed_count": int(operator_review_guidance_report.get("current_evidence_write_allowed_count") or 0),
        "operator_guidance_primary_blocker_code": str(
            operator_review_guidance_report.get("primary_blocker_code") or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        ),
    }


def _build_item(*, session_id: str, source_item: dict[str, Any], priority_order: int) -> dict[str, Any]:
    path = str(source_item.get("candidate_rollup_artifact_path") or "")
    duplicate_total_count = int(source_item.get("duplicate_total_count") or 0)
    clean = (
        source_item.get("candidate_recheck_status") == "PASS_CURRENT_EVIDENCE_BLOCKED"
        and source_item.get("candidate_rollup_hash_match") is True
        and source_item.get("candidate_rollup_load_status") == "PASS"
        and duplicate_total_count == 0
        and not source_item.get("load_blockers")
    )
    repaired_ledger_paths = [
        str(cycle.get("repaired_ledger_path"))
        for cycle in source_item.get("cycles", [])
        if isinstance(cycle, dict) and isinstance(cycle.get("repaired_ledger_path"), str)
    ]
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(source_item.get("replacement_loop_id") or "UNKNOWN"),
        "source_candidate_recheck_status": source_item.get("candidate_recheck_status"),
        "candidate_rollup_artifact_path": path,
        "candidate_rollup_artifact_path_allowed": _candidate_path_allowed(path, session_id),
        "candidate_rollup_hash": source_item.get("candidate_rollup_hash"),
        "candidate_rollup_hash_match": source_item.get("candidate_rollup_hash_match") is True,
        "candidate_rollup_load_status": source_item.get("candidate_rollup_load_status"),
        "ledger_jsonl_count": int(source_item.get("ledger_jsonl_count") or 0),
        "ledger_event_count": int(source_item.get("ledger_event_count") or 0),
        "filled_order_count": int(source_item.get("filled_order_count") or 0),
        "duplicate_total_count": duplicate_total_count,
        "duplicate_event_id_duplicate_count": int(source_item.get("duplicate_event_id_duplicate_count") or 0),
        "duplicate_dedup_key_duplicate_count": int(source_item.get("duplicate_dedup_key_duplicate_count") or 0),
        "duplicate_filled_order_duplicate_count": int(source_item.get("duplicate_filled_order_duplicate_count") or 0),
        "repaired_ledger_paths": repaired_ledger_paths,
        "repaired_ledger_path_count": len(repaired_ledger_paths),
        "guard_item_status": "REVIEW_READY_CURRENT_EVIDENCE_BLOCKED" if clean else "BLOCKED_RECONCILIATION_REQUIRED",
        "item_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        if clean
        else ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_BLOCKER_CODE,
        "recommended_operator_action": "Keep this repaired candidate as review-only evidence; this guard cannot write current ledger, pointer, or portfolio truth.",
        "candidate_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "live_permission_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
    *,
    root: Path,
    event_id_scope_repaired_duplicate_recheck_report: dict[str, Any],
    operator_review_guidance_report: dict[str, Any] | None = None,
    event_id_scope_repaired_current_evidence_guard_id: str = "upbit-paper-stale-loop-isolated-event-id-scope-repaired-current-evidence-guard",
) -> dict[str, Any]:
    source_result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(
        event_id_scope_repaired_duplicate_recheck_report
    )
    session_id = str(event_id_scope_repaired_duplicate_recheck_report.get("session_id", "UNKNOWN"))
    items = [
        _build_item(session_id=session_id, source_item=item, priority_order=index)
        for index, item in enumerate(event_id_scope_repaired_duplicate_recheck_report.get("items", []), start=1)
        if isinstance(item, dict)
    ]
    ready_count = sum(1 for item in items if item["guard_item_status"] == "REVIEW_READY_CURRENT_EVIDENCE_BLOCKED")
    duplicate_total_count = sum(int(item["duplicate_total_count"]) for item in items)
    blocker_codes = {
        ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_BLOCKER_CODE,
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    for item in items:
        blocker_codes.add(str(item["item_blocker_code"]))
    guidance = _operator_guidance_summary(operator_review_guidance_report)
    if guidance["operator_guidance_loaded"]:
        blocker_codes.add(str(guidance["operator_guidance_primary_blocker_code"]))
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "event_id_scope_repaired_current_evidence_guard_id": event_id_scope_repaired_current_evidence_guard_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_TRUTH_ROLE,
        "event_id_scope_repaired_current_evidence_guard_role": ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_ROLE,
        "source_event_id_scope_repaired_duplicate_recheck_hash": event_id_scope_repaired_duplicate_recheck_report.get(
            "event_id_scope_repaired_duplicate_recheck_hash"
        ),
        "source_event_id_scope_repaired_duplicate_recheck_status": event_id_scope_repaired_duplicate_recheck_report.get(
            "recheck_status"
        ),
        "source_event_id_scope_repaired_duplicate_recheck_validator_status": source_result.status,
        **guidance,
        "candidate_count": len(items),
        "guard_review_ready_count": ready_count,
        "guard_blocked_count": len(items),
        "clean_candidate_count": sum(1 for item in items if int(item["duplicate_total_count"]) == 0),
        "duplicate_total_count": duplicate_total_count,
        "ledger_jsonl_count": sum(int(item["ledger_jsonl_count"]) for item in items),
        "ledger_event_count": sum(int(item["ledger_event_count"]) for item in items),
        "filled_order_count": sum(int(item["filled_order_count"]) for item in items),
        "current_evidence_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "portfolio_truth_write_allowed_count": 0,
        "current_evidence_guard_status": "BLOCKED_CURRENT_EVIDENCE_WRITE_DENIED",
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Keep repaired candidates review-only. Current evidence writes require a separate audited writer and remain blocked here.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "candidate_only": True,
        "candidate_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "portfolio_truth_write_allowed": False,
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
        "can_submit_order": False,
        "scale_up_allowed": False,
        "event_id_scope_repaired_current_evidence_guard_hash": "",
    }
    report["event_id_scope_repaired_current_evidence_guard_hash"] = (
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash(report)
    )
    return report


def write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "event_id_scope_repaired_current_evidence_guard_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "event_id_scope_repaired_current_evidence_guard_role",
        "source_event_id_scope_repaired_duplicate_recheck_hash",
        "source_event_id_scope_repaired_duplicate_recheck_status",
        "source_event_id_scope_repaired_duplicate_recheck_validator_status",
        "operator_guidance_loaded",
        "operator_guidance_status",
        "operator_guidance_item_count",
        "operator_guidance_forbidden_output_count",
        "operator_guidance_current_evidence_write_allowed_count",
        "operator_guidance_primary_blocker_code",
        "candidate_count",
        "guard_review_ready_count",
        "guard_blocked_count",
        "clean_candidate_count",
        "duplicate_total_count",
        "ledger_jsonl_count",
        "ledger_event_count",
        "filled_order_count",
        "current_evidence_write_allowed_count",
        "candidate_current_evidence_usable_count",
        "portfolio_truth_write_allowed_count",
        "current_evidence_guard_status",
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
        "current_evidence_mutation_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "portfolio_truth_write_allowed",
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
        "can_submit_order",
        "scale_up_allowed",
        "event_id_scope_repaired_current_evidence_guard_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "FAIL", f"event-id repaired current evidence guard missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_SCHEMA_ID:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "FAIL", "event-id repaired current evidence guard schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("event_id_scope_repaired_current_evidence_guard_hash") != (
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash(report)
    ):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "FAIL", "event-id repaired current evidence guard hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "BLOCKED", "event-id repaired current evidence guard scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if report.get("truth_role") != ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_TRUTH_ROLE:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "BLOCKED", "event-id repaired current evidence guard truth role cannot claim writer authority", "LIVE_FINAL_GUARD_FAILED"
        )
    false_fields = (
        "candidate_current_evidence_usable",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "portfolio_truth_write_allowed",
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
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(report.get(field) is not False for field in false_fields):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "BLOCKED", "event-id repaired current evidence guard attempted current evidence or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("current_evidence_write_allowed_count") != 0
        or report.get("candidate_current_evidence_usable_count") != 0
        or report.get("portfolio_truth_write_allowed_count") != 0
        or report.get("operator_guidance_current_evidence_write_allowed_count") != 0
    ):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "BLOCKED", "event-id repaired current evidence guard exposed forbidden write counts", "LIVE_FINAL_GUARD_FAILED"
        )
    if report.get("current_evidence_guard_status") != "BLOCKED_CURRENT_EVIDENCE_WRITE_DENIED":
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "BLOCKED", "event-id repaired current evidence guard must remain blocked", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        )
    if report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE:
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "BLOCKED", "event-id repaired current evidence guard primary blocker drifted", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        )
    if not report.get("display_only") or not report.get("dashboard_truth_only") or not report.get("paper_only") or not report.get("candidate_only"):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "BLOCKED", "event-id repaired current evidence guard must remain display-only candidate PAPER evidence", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("candidate_count") != len(items):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "FAIL", "event-id repaired current evidence guard item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    sums = {
        "guard_review_ready_count": 0,
        "guard_blocked_count": len(items),
        "clean_candidate_count": 0,
        "duplicate_total_count": 0,
        "ledger_jsonl_count": 0,
        "ledger_event_count": 0,
        "filled_order_count": 0,
    }
    session_id = str(report.get("session_id"))
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict) or item.get("priority_order") != index:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
                "FAIL", "event-id repaired current evidence guard priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if not _candidate_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
                "BLOCKED", "event-id repaired current evidence guard candidate path escaped namespace", "SNAPSHOT_SCOPE_MISMATCH"
            )
        for path in item.get("repaired_ledger_paths", []):
            if not isinstance(path, str) or not _candidate_path_allowed(path, session_id):
                return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
                    "BLOCKED", "event-id repaired current evidence guard ledger path escaped namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
        if item.get("repaired_ledger_path_count") != len(item.get("repaired_ledger_paths", [])):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
                "FAIL", "event-id repaired current evidence guard ledger path count mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_false = (
            "candidate_current_evidence_usable",
            "current_evidence_write_allowed",
            "current_evidence_mutation_allowed",
            "current_ledger_jsonl_write_allowed",
            "latest_runtime_pointer_write_allowed",
            "portfolio_truth_write_allowed",
            "persistent_loop_mutation_allowed",
            "source_delete_allowed",
            "actual_long_run_evidence_created",
            "long_run_evidence_eligible",
            "promotion_eligible",
            "live_permission_created",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        )
        if any(item.get(field) is not False for field in item_false):
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
                "BLOCKED", "event-id repaired current evidence guard item attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
            )
        if item.get("guard_item_status") == "REVIEW_READY_CURRENT_EVIDENCE_BLOCKED":
            sums["guard_review_ready_count"] += 1
        if int(item.get("duplicate_total_count") or 0) == 0:
            sums["clean_candidate_count"] += 1
        for field in ("duplicate_total_count", "ledger_jsonl_count", "ledger_event_count", "filled_order_count"):
            sums[field] += int(item.get(field) or 0)
    for field, value in sums.items():
        if report.get(field) != value:
            return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
                "FAIL", f"event-id repaired current evidence guard aggregate mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("guard_review_ready_count") != report.get("candidate_count"):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "BLOCKED", "not all repaired candidates are review-ready", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        )
    if POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(report.get("blocker_codes") or []):
        return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
            "BLOCKED", "event-id repaired current evidence guard missing post-rerun blocker", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        )
    return UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardValidationResult(
        "PASS", "event-id repaired current evidence guard keeps clean candidates review-only and live blocked", None
    )
