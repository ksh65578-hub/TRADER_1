from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_persistent_loop import (
    DEFAULT_PUBLIC_DISCOVERY_EVALUATION_LIMIT,
    upbit_paper_persistent_loop_hash,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_normalized_reconciliation_preview import (
    NORMALIZED_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    validate_upbit_paper_stale_loop_normalized_reconciliation_preview_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_NORMALIZED_RECONCILIATION_RECHECK_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_normalized_reconciliation_recheck_report.v1"
)
STALE_LOOP_NORMALIZED_RECONCILIATION_RECHECK_TRUTH_ROLE = (
    "paper_runtime_stale_loop_normalized_reconciliation_recheck_truth"
)
STALE_LOOP_NORMALIZED_RECONCILIATION_RECHECK_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_NORMALIZED_RECONCILIATION_RECHECK_NO_WRITES"
)
NORMALIZED_RECONCILIATION_RECHECK_BLOCKER_CODE = "NORMALIZED_RECONCILIATION_RECHECK_BLOCKED"
NORMALIZED_RECONCILIATION_RECHECK_REQUIRES_LEDGER_ROLLUP_BLOCKER_CODE = (
    "NORMALIZED_RECONCILIATION_RECHECK_REQUIRES_LEDGER_ROLLUP"
)
RUNTIME_DEPTH_RECHECK_REQUIRED_REASON_CODE = "RUNTIME_DEPTH_RECHECK_REQUIRED"


@dataclass(frozen=True)
class UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_normalized_reconciliation_recheck_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("normalized_reconciliation_recheck_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/")
        and ".." not in normalized.split("/")
        and "/live/" not in normalized
    )


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _proposed_normalization_fields(replacement_report: dict[str, Any]) -> dict[str, Any]:
    raw_universe = replacement_report.get("symbol_universe")
    if isinstance(raw_universe, list):
        universe = [str(symbol) for symbol in raw_universe if isinstance(symbol, str) and symbol.startswith("KRW-")]
    else:
        universe = []
    if not universe:
        symbol = replacement_report.get("symbol")
        universe = [str(symbol)] if isinstance(symbol, str) and symbol.startswith("KRW-") else ["KRW-BTC"]
    universe = list(dict.fromkeys(universe))
    return {
        "preflight_existing_runtime_state_detected": True,
        "preflight_recovery_guard_status": replacement_report.get("recovery_guard_status"),
        "preflight_recovery_guard_hash": replacement_report.get("recovery_guard_hash"),
        "preflight_recovery_guard_primary_blocker_code": replacement_report.get("recovery_guard_primary_blocker_code"),
        "preflight_runtime_recovery_guard_path": replacement_report.get("runtime_recovery_guard_path"),
        "preflight_paper_runtime_resume_allowed": replacement_report.get("paper_runtime_resume_allowed"),
        "current_evidence_write_allowed": True,
        "symbol_universe": universe,
        "symbol_universe_source": replacement_report.get("symbol_universe_source") or "EXPLICIT_SYMBOL_UNIVERSE",
        "public_symbol_discovery_attempted": bool(replacement_report.get("public_symbol_discovery_attempted")),
        "symbol_universe_discovery_status": replacement_report.get("symbol_universe_discovery_status") or "SKIPPED",
        "symbol_universe_discovery_blocker_code": replacement_report.get("symbol_universe_discovery_blocker_code"),
        "symbol_universe_total_count": int(replacement_report.get("symbol_universe_total_count") or len(universe)),
        "symbol_universe_evaluated_count": int(
            replacement_report.get("symbol_universe_evaluated_count") or len(universe)
        ),
        "max_symbol_evaluation_count": int(
            replacement_report.get("max_symbol_evaluation_count")
            or max(DEFAULT_PUBLIC_DISCOVERY_EVALUATION_LIMIT, len(universe))
        ),
        "public_symbol_discovery_market_count": int(replacement_report.get("public_symbol_discovery_market_count") or 0),
        "public_ticker_ranked_symbol_count": int(replacement_report.get("public_ticker_ranked_symbol_count") or 0),
        "public_ticker_eligible_symbol_count": int(replacement_report.get("public_ticker_eligible_symbol_count") or 0),
        "public_symbol_discovery_report": replacement_report.get("public_symbol_discovery_report"),
        "public_ticker_snapshot_report": replacement_report.get("public_ticker_snapshot_report"),
        "public_symbol_ranking_report": replacement_report.get("public_symbol_ranking_report"),
    }


def _normalized_candidate(replacement_report: dict[str, Any]) -> dict[str, Any]:
    candidate = dict(replacement_report)
    candidate.update(_proposed_normalization_fields(replacement_report))
    candidate["loop_hash"] = upbit_paper_persistent_loop_hash(candidate)
    return candidate


def _reason_codes(candidate: dict[str, Any], validation_status: str, blocker_code: str | None) -> list[str]:
    reasons: list[str] = []
    if validation_status == "MISSING":
        return ["NORMALIZED_CANDIDATE_MISSING"]
    if validation_status == "FAIL":
        reasons.append(blocker_code or "NORMALIZED_CANDIDATE_FAILED")
    if candidate.get("loop_status") == "BLOCKED":
        reasons.append("LOOP_STATUS_BLOCKED")
    if candidate.get("primary_blocker_code") == "RECONCILIATION_REQUIRED":
        reasons.append("LOOP_RECONCILIATION_REQUIRED")
    if candidate.get("recovery_guard_status") == "BLOCKED":
        reasons.append("RECOVERY_GUARD_BLOCKED")
    if candidate.get("partial_write_recovery_required"):
        reasons.append("PARTIAL_WRITE_RECOVERY_REQUIRED")
    if candidate.get("paper_runtime_resume_allowed") is False:
        reasons.append("PAPER_RUNTIME_RESUME_BLOCKED")
    if candidate.get("paper_ledger_rollup_status") == "BLOCKED":
        reasons.append("LEDGER_ROLLUP_BLOCKED")
    if candidate.get("paper_ledger_rollup_primary_blocker_code") == "RECONCILIATION_REQUIRED":
        reasons.append("LEDGER_ROLLUP_RECONCILIATION_REQUIRED")
    if validation_status == "BLOCKED" and blocker_code in {"RECONCILIATION_REQUIRED", "MEASUREMENT_MISSING"}:
        reasons.append(NORMALIZED_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if validation_status == "BLOCKED" and blocker_code == "MEASUREMENT_MISSING":
        reasons.append(RUNTIME_DEPTH_RECHECK_REQUIRED_REASON_CODE)
    if not reasons:
        reasons.append("NORMALIZED_RECONCILIATION_RECHECK_UNKNOWN_BLOCKER")
    return sorted(set(str(reason) for reason in reasons))


def _reason_rollup(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        for reason in item.get("recheck_reason_codes") or []:
            counts[str(reason)] = counts.get(str(reason), 0) + 1
    return [{"reason_code": reason, "count": counts[reason]} for reason in sorted(counts)]


def _build_item(*, root: Path, session_id: str, preview_item: dict[str, Any], priority_order: int) -> dict[str, Any]:
    replacement_path = str(preview_item.get("replacement_path") or "")
    replacement_report = _load_json(Path(root).resolve() / replacement_path)
    normalized: dict[str, Any] = {}
    normalized_hash = None
    validation_status = "MISSING"
    validation_blocker_code = "MEASUREMENT_MISSING"
    validation_message = "replacement report missing or unreadable"
    if replacement_report is not None:
        normalized = _normalized_candidate(replacement_report)
        normalized_hash = normalized.get("loop_hash")
        result = validate_upbit_paper_persistent_loop_report(normalized)
        validation_status = result.status
        validation_blocker_code = result.blocker_code
        validation_message = result.message
    reason_codes = _reason_codes(normalized, validation_status, validation_blocker_code)
    ledger_rollup_recheck_required = "LEDGER_ROLLUP_BLOCKED" in reason_codes or "LEDGER_ROLLUP_RECONCILIATION_REQUIRED" in reason_codes
    blocker_codes = set(str(code) for code in preview_item.get("blocker_codes") or [])
    blocker_codes.add(NORMALIZED_RECONCILIATION_RECHECK_BLOCKER_CODE)
    blocker_codes.update(reason_codes)
    if ledger_rollup_recheck_required:
        blocker_codes.add(NORMALIZED_RECONCILIATION_RECHECK_REQUIRES_LEDGER_ROLLUP_BLOCKER_CODE)
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(preview_item.get("replacement_loop_id") or "UNKNOWN"),
        "replacement_path": replacement_path,
        "source_path": str(preview_item.get("source_path") or ""),
        "replacement_path_exists": replacement_report is not None,
        "preview_normalized_hash": preview_item.get("normalized_replacement_hash"),
        "recomputed_normalized_hash": normalized_hash,
        "normalized_hash_match": normalized_hash == preview_item.get("normalized_replacement_hash"),
        "normalized_validation_status": validation_status,
        "normalized_validation_blocker_code": validation_blocker_code,
        "normalized_validation_message": validation_message,
        "normalized_loop_status": normalized.get("loop_status"),
        "normalized_primary_blocker_code": normalized.get("primary_blocker_code"),
        "normalized_recovery_guard_status": normalized.get("recovery_guard_status"),
        "normalized_recovery_guard_primary_blocker_code": normalized.get("recovery_guard_primary_blocker_code"),
        "normalized_paper_runtime_resume_allowed": normalized.get("paper_runtime_resume_allowed"),
        "normalized_partial_write_recovery_required": normalized.get("partial_write_recovery_required"),
        "normalized_paper_ledger_rollup_status": normalized.get("paper_ledger_rollup_status"),
        "normalized_paper_ledger_rollup_primary_blocker_code": normalized.get(
            "paper_ledger_rollup_primary_blocker_code"
        ),
        "normalized_paper_ledger_rollup_hash": normalized.get("paper_ledger_rollup_hash"),
        "normalized_paper_ledger_rollup_path": normalized.get("paper_ledger_rollup_path"),
        "recheck_status": "BLOCKED_RECONCILIATION_REQUIRED"
        if validation_status == "BLOCKED"
        else "BLOCKED_SOURCE_NOT_READY",
        "recheck_reason_codes": reason_codes,
        "ledger_rollup_recheck_required": ledger_rollup_recheck_required,
        "operator_action": (
            "Run a ledger-rollup reconciliation recheck for this normalized loop before current evidence closure."
            if ledger_rollup_recheck_required
            else "Resolve normalized candidate measurement before ledger-rollup recheck."
        ),
        "primary_blocker_code": NORMALIZED_RECONCILIATION_RECHECK_REQUIRES_LEDGER_ROLLUP_BLOCKER_CODE
        if ledger_rollup_recheck_required
        else NORMALIZED_RECONCILIATION_RECHECK_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "normalized_reconciliation_recheck_only": True,
        "reconciliation_write_allowed": False,
        "current_evidence_write_allowed": False,
        "preview_current_evidence_usable": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(
    *,
    root: Path,
    normalized_reconciliation_preview_report: dict[str, Any],
    normalized_reconciliation_recheck_id: str = "upbit-paper-stale-loop-normalized-reconciliation-recheck",
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_normalized_reconciliation_preview_report(
        normalized_reconciliation_preview_report
    )
    session_id = str(normalized_reconciliation_preview_report.get("session_id", "UNKNOWN"))
    candidate_items = [
        item
        for item in normalized_reconciliation_preview_report.get("items", [])
        if isinstance(item, dict) and item.get("reconciliation_required") is True
    ]
    items = [
        _build_item(root=root, session_id=session_id, preview_item=item, priority_order=index)
        for index, item in enumerate(candidate_items, start=1)
    ]
    reason_rollup = _reason_rollup(items)
    ledger_rollup_recheck_required_count = sum(1 for item in items if item["ledger_rollup_recheck_required"])
    blocker_codes = {NORMALIZED_RECONCILIATION_RECHECK_BLOCKER_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or "NORMALIZED_RECONCILIATION_PREVIEW_INVALID")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    if ledger_rollup_recheck_required_count:
        blocker_codes.add(NORMALIZED_RECONCILIATION_RECHECK_REQUIRES_LEDGER_ROLLUP_BLOCKER_CODE)
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_NORMALIZED_RECONCILIATION_RECHECK_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "normalized_reconciliation_recheck_id": normalized_reconciliation_recheck_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_NORMALIZED_RECONCILIATION_RECHECK_TRUTH_ROLE,
        "normalized_reconciliation_recheck_role": STALE_LOOP_NORMALIZED_RECONCILIATION_RECHECK_ROLE,
        "source_normalized_reconciliation_preview_hash": normalized_reconciliation_preview_report.get(
            "normalized_reconciliation_preview_hash"
        ),
        "source_normalized_reconciliation_preview_status": normalized_reconciliation_preview_report.get("preview_status"),
        "source_normalized_reconciliation_preview_validator_status": source_result.status,
        "source_reconciliation_required_count": normalized_reconciliation_preview_report.get(
            "reconciliation_required_count"
        ),
        "item_count": len(items),
        "normalized_reconciliation_recheck_candidate_count": len(items),
        "normalized_hash_match_count": sum(1 for item in items if item["normalized_hash_match"]),
        "normalized_validation_blocked_count": sum(1 for item in items if item["normalized_validation_status"] == "BLOCKED"),
        "ledger_rollup_recheck_required_count": ledger_rollup_recheck_required_count,
        "recovery_guard_blocked_count": sum(1 for item in items if item["normalized_recovery_guard_status"] == "BLOCKED"),
        "reason_code_rollup": reason_rollup,
        "current_evidence_usable_after_recheck_count": 0,
        "reconciliation_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "recheck_status": "BLOCKED",
        "primary_blocker_code": NORMALIZED_RECONCILIATION_RECHECK_REQUIRES_LEDGER_ROLLUP_BLOCKER_CODE
        if ledger_rollup_recheck_required_count
        else NORMALIZED_RECONCILIATION_RECHECK_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": (
            "Run a bounded ledger-rollup reconciliation recheck for the normalized stale-loop candidates."
            if items
            else "No normalized reconciliation recheck candidates are available."
        ),
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "normalized_reconciliation_recheck_only": True,
        "reconciliation_write_allowed": False,
        "replacement_write_allowed": False,
        "current_evidence_write_allowed": False,
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
        "normalized_reconciliation_recheck_hash": "",
    }
    report["normalized_reconciliation_recheck_hash"] = upbit_paper_stale_loop_normalized_reconciliation_recheck_hash(report)
    return report


def write_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_normalized_reconciliation_recheck_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "normalized_reconciliation_recheck_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "normalized_reconciliation_recheck_role",
        "source_normalized_reconciliation_preview_hash",
        "source_normalized_reconciliation_preview_status",
        "source_normalized_reconciliation_preview_validator_status",
        "source_reconciliation_required_count",
        "item_count",
        "normalized_reconciliation_recheck_candidate_count",
        "normalized_hash_match_count",
        "normalized_validation_blocked_count",
        "ledger_rollup_recheck_required_count",
        "recovery_guard_blocked_count",
        "reason_code_rollup",
        "current_evidence_usable_after_recheck_count",
        "reconciliation_write_allowed_count",
        "current_evidence_write_allowed_count",
        "recheck_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "normalized_reconciliation_recheck_only",
        "reconciliation_write_allowed",
        "replacement_write_allowed",
        "current_evidence_write_allowed",
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
        "normalized_reconciliation_recheck_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", f"normalized reconciliation recheck missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_NORMALIZED_RECONCILIATION_RECHECK_SCHEMA_ID:
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", "normalized reconciliation recheck schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("normalized_reconciliation_recheck_hash") != upbit_paper_stale_loop_normalized_reconciliation_recheck_hash(report):
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", "normalized reconciliation recheck hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "BLOCKED", "normalized reconciliation recheck scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if (
        report.get("truth_role") != STALE_LOOP_NORMALIZED_RECONCILIATION_RECHECK_TRUTH_ROLE
        or report.get("normalized_reconciliation_recheck_role") != STALE_LOOP_NORMALIZED_RECONCILIATION_RECHECK_ROLE
    ):
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", "normalized reconciliation recheck role mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    false_fields = (
        "reconciliation_write_allowed",
        "replacement_write_allowed",
        "current_evidence_write_allowed",
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
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "BLOCKED", "normalized reconciliation recheck attempted mutation or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("display_only") is not True
        or report.get("dashboard_truth_only") is not True
        or report.get("paper_only") is not True
        or report.get("normalized_reconciliation_recheck_only") is not True
    ):
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "BLOCKED", "normalized reconciliation recheck must remain display-only", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("reconciliation_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
        or report.get("current_evidence_usable_after_recheck_count") != 0
    ):
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "BLOCKED", "normalized reconciliation recheck exposed write or current-evidence usability", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("item_count") != len(items) or report.get("normalized_reconciliation_recheck_candidate_count") != len(items):
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", "normalized reconciliation recheck item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected_hash_match_count = 0
    expected_blocked_count = 0
    expected_ledger_required_count = 0
    expected_recovery_blocked_count = 0
    session_id = str(report.get("session_id"))
    expected_reason_counts: dict[str, int] = {}
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
                "FAIL", "normalized reconciliation recheck item must be an object", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_required = {
            "priority_order",
            "replacement_loop_id",
            "replacement_path",
            "source_path",
            "replacement_path_exists",
            "preview_normalized_hash",
            "recomputed_normalized_hash",
            "normalized_hash_match",
            "normalized_validation_status",
            "normalized_validation_blocker_code",
            "normalized_validation_message",
            "normalized_loop_status",
            "normalized_primary_blocker_code",
            "normalized_recovery_guard_status",
            "normalized_recovery_guard_primary_blocker_code",
            "normalized_paper_runtime_resume_allowed",
            "normalized_partial_write_recovery_required",
            "normalized_paper_ledger_rollup_status",
            "normalized_paper_ledger_rollup_primary_blocker_code",
            "normalized_paper_ledger_rollup_hash",
            "normalized_paper_ledger_rollup_path",
            "recheck_status",
            "recheck_reason_codes",
            "ledger_rollup_recheck_required",
            "operator_action",
            "primary_blocker_code",
            "blocker_codes",
            "normalized_reconciliation_recheck_only",
            "reconciliation_write_allowed",
            "current_evidence_write_allowed",
            "preview_current_evidence_usable",
            "actual_long_run_evidence_created",
            "live_permission_created",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
                "FAIL", f"normalized reconciliation recheck item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("priority_order") != index:
            return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
                "FAIL", "normalized reconciliation recheck priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for path_field in ("source_path", "replacement_path"):
            if not _artifact_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
                    "BLOCKED", f"normalized reconciliation recheck {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
        ledger_path = item.get("normalized_paper_ledger_rollup_path")
        if isinstance(ledger_path, str) and ledger_path and not _artifact_path_allowed(ledger_path, session_id):
            return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
                "BLOCKED", "normalized reconciliation recheck ledger rollup path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
            )
        if (
            item.get("normalized_reconciliation_recheck_only") is not True
            or item.get("reconciliation_write_allowed")
            or item.get("current_evidence_write_allowed")
            or item.get("preview_current_evidence_usable")
            or item.get("actual_long_run_evidence_created")
            or item.get("live_permission_created")
        ):
            return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
                "BLOCKED", "normalized reconciliation recheck item attempted write or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        if item.get("normalized_hash_match"):
            expected_hash_match_count += 1
        if item.get("normalized_validation_status") == "BLOCKED":
            expected_blocked_count += 1
            if item.get("normalized_validation_blocker_code") not in {"RECONCILIATION_REQUIRED", "MEASUREMENT_MISSING"}:
                return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
                    "FAIL",
                    "blocked normalized recheck item must be reconciliation or runtime-depth blocked",
                    "SCHEMA_IDENTITY_MISMATCH",
                )
        if item.get("ledger_rollup_recheck_required"):
            expected_ledger_required_count += 1
            if item.get("primary_blocker_code") != NORMALIZED_RECONCILIATION_RECHECK_REQUIRES_LEDGER_ROLLUP_BLOCKER_CODE:
                return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
                    "FAIL", "ledger-rollup recheck item primary blocker mismatch", "SCHEMA_IDENTITY_MISMATCH"
                )
        if item.get("normalized_recovery_guard_status") == "BLOCKED":
            expected_recovery_blocked_count += 1
        reason_codes = item.get("recheck_reason_codes")
        if not isinstance(reason_codes, list) or not reason_codes:
            return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
                "FAIL", "normalized reconciliation recheck item must expose reason codes", "SCHEMA_IDENTITY_MISMATCH"
            )
        for reason in reason_codes:
            expected_reason_counts[str(reason)] = expected_reason_counts.get(str(reason), 0) + 1
    if report.get("normalized_hash_match_count") != expected_hash_match_count:
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", "normalized hash match count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("normalized_validation_blocked_count") != expected_blocked_count:
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", "normalized validation blocked count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("ledger_rollup_recheck_required_count") != expected_ledger_required_count:
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", "ledger rollup recheck required count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("recovery_guard_blocked_count") != expected_recovery_blocked_count:
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", "recovery guard blocked count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    reason_rollup = report.get("reason_code_rollup")
    expected_rollup = [{"reason_code": reason, "count": expected_reason_counts[reason]} for reason in sorted(expected_reason_counts)]
    if reason_rollup != expected_rollup:
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", "normalized reconciliation recheck reason rollup mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("recheck_status") != "BLOCKED" or not report.get("primary_blocker_code"):
        return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
            "FAIL", "normalized reconciliation recheck must remain blocked", "SCHEMA_IDENTITY_MISMATCH"
        )
    return UpbitPaperStaleLoopNormalizedReconciliationRecheckValidationResult(
        "PASS",
        "Upbit PAPER stale-loop normalized reconciliation recheck is display-only and live-blocked",
        None,
    )
