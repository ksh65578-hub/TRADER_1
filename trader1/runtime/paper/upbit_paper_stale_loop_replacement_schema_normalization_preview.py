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
from trader1.runtime.paper.upbit_paper_stale_loop_ledger_recheck_preview import (
    PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED_BLOCKER_CODE,
    validate_upbit_paper_stale_loop_ledger_recheck_preview_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_replacement_schema_normalization_preview_report.v1"
)
STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_TRUTH_ROLE = (
    "paper_runtime_stale_loop_replacement_schema_normalization_preview_truth"
)
STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_NO_WRITES"
)
REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_BLOCKER_CODE = "REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_BLOCKED"
POST_NORMALIZATION_RECONCILIATION_REQUIRED_BLOCKER_CODE = "POST_NORMALIZATION_RECONCILIATION_REQUIRED"

MISSING_PREFLIGHT_FIELDS = [
    "current_evidence_write_allowed",
    "preflight_existing_runtime_state_detected",
    "preflight_paper_runtime_resume_allowed",
    "preflight_recovery_guard_hash",
    "preflight_recovery_guard_primary_blocker_code",
    "preflight_recovery_guard_status",
    "preflight_runtime_recovery_guard_path",
]
SYMBOL_DISCOVERY_NORMALIZATION_FIELDS = [
    "symbol_universe",
    "symbol_universe_source",
    "public_symbol_discovery_attempted",
    "symbol_universe_discovery_status",
    "symbol_universe_discovery_blocker_code",
    "symbol_universe_total_count",
    "symbol_universe_evaluated_count",
    "max_symbol_evaluation_count",
    "public_symbol_discovery_market_count",
    "public_ticker_ranked_symbol_count",
    "public_ticker_eligible_symbol_count",
    "public_symbol_discovery_report",
    "public_ticker_snapshot_report",
    "public_symbol_ranking_report",
]
NORMALIZATION_SCHEMA_UPGRADE_FIELDS = MISSING_PREFLIGHT_FIELDS + SYMBOL_DISCOVERY_NORMALIZATION_FIELDS


@dataclass(frozen=True)
class UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_replacement_schema_normalization_preview_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("normalization_preview_hash", None)
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


def _build_item(*, root: Path, session_id: str, preview_item: dict[str, Any], priority_order: int) -> dict[str, Any]:
    replacement_path = str(preview_item.get("replacement_path") or "")
    replacement_report = _load_json(Path(root).resolve() / replacement_path)
    replacement_exists = replacement_report is not None
    original_missing_fields = list(MISSING_PREFLIGHT_FIELDS)
    proposed = {}
    normalized_hash = None
    normalized_status = "MISSING"
    normalized_blocker_code = "MEASUREMENT_MISSING"
    normalized_message = "replacement report missing or unreadable"
    proposed_current_write = False
    if replacement_report is not None:
        original_missing_fields = sorted(set(NORMALIZATION_SCHEMA_UPGRADE_FIELDS) - set(replacement_report))
        proposed = _proposed_normalization_fields(replacement_report)
        proposed_current_write = proposed.get("current_evidence_write_allowed") is True
        normalized = _normalized_candidate(replacement_report)
        normalized_hash = normalized.get("loop_hash")
        normalized_result = validate_upbit_paper_persistent_loop_report(normalized)
        normalized_status = normalized_result.status
        normalized_blocker_code = normalized_result.blocker_code
        normalized_message = normalized_result.message

    normalization_item_status = "BLOCKED"
    blocker_codes = set(str(code) for code in preview_item.get("blocker_codes") or [])
    blocker_codes.add(REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_BLOCKER_CODE)
    if normalized_status in {"PASS", "BLOCKED"} and normalized_blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        normalization_item_status = "READY_PREVIEW_ONLY"
        if normalized_status == "BLOCKED":
            blocker_codes.add(POST_NORMALIZATION_RECONCILIATION_REQUIRED_BLOCKER_CODE)
            if normalized_blocker_code:
                blocker_codes.add(str(normalized_blocker_code))
    else:
        blocker_codes.add(PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED_BLOCKER_CODE)

    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(preview_item.get("replacement_loop_id") or "UNKNOWN"),
        "replacement_path": replacement_path,
        "source_path": str(preview_item.get("source_path") or ""),
        "replacement_path_exists": replacement_exists,
        "original_validation_status": str(preview_item.get("replacement_validation_status") or "UNKNOWN"),
        "original_validation_blocker_code": preview_item.get("replacement_validation_blocker_code"),
        "original_missing_fields": original_missing_fields,
        "proposed_field_count": len(proposed),
        "proposed_field_names": sorted(proposed),
        "proposed_preflight_existing_runtime_state_detected": proposed.get("preflight_existing_runtime_state_detected"),
        "proposed_preflight_recovery_guard_status": proposed.get("preflight_recovery_guard_status"),
        "proposed_preflight_recovery_guard_hash": proposed.get("preflight_recovery_guard_hash"),
        "proposed_preflight_recovery_guard_primary_blocker_code": proposed.get(
            "preflight_recovery_guard_primary_blocker_code"
        ),
        "proposed_preflight_runtime_recovery_guard_path": proposed.get("preflight_runtime_recovery_guard_path"),
        "proposed_preflight_paper_runtime_resume_allowed": proposed.get("preflight_paper_runtime_resume_allowed"),
        "proposed_current_evidence_write_allowed": proposed_current_write,
        "proposed_current_evidence_write_required_by_validator": proposed_current_write,
        "normalized_replacement_hash": normalized_hash,
        "normalized_validation_status": normalized_status,
        "normalized_validation_blocker_code": normalized_blocker_code,
        "normalized_validation_message": normalized_message,
        "normalization_item_status": normalization_item_status,
        "primary_blocker_code": None if normalization_item_status == "READY_PREVIEW_ONLY" else PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "operator_action": (
            "Preview says schema normalization can remove SCHEMA_IDENTITY_MISMATCH, but post-normalization ledger reconciliation is still required before any current-evidence decision."
            if normalization_item_status == "READY_PREVIEW_ONLY"
            else "Replacement schema still cannot be normalized safely; keep it out of current evidence."
        ),
        "normalization_preview_only": True,
        "normalization_write_allowed": False,
        "replacement_write_allowed": False,
        "current_evidence_write_allowed": False,
        "preview_current_evidence_usable": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(
    *,
    root: Path,
    ledger_recheck_preview_report: dict[str, Any],
    normalization_preview_id: str = "upbit-paper-stale-loop-replacement-schema-normalization-preview",
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_ledger_recheck_preview_report(ledger_recheck_preview_report)
    session_id = str(ledger_recheck_preview_report.get("session_id", "UNKNOWN"))
    candidate_items = [
        item
        for item in ledger_recheck_preview_report.get("items", [])
        if isinstance(item, dict)
        and item.get("ledger_recheck_candidate") is True
        and item.get("replacement_validation_status") != "PASS"
    ]
    items = [
        _build_item(root=root, session_id=session_id, preview_item=item, priority_order=index)
        for index, item in enumerate(candidate_items, start=1)
    ]
    ready_preview_count = sum(1 for item in items if item["normalization_item_status"] == "READY_PREVIEW_ONLY")
    normalized_schema_fail_count = sum(
        1 for item in items if item["normalized_validation_blocker_code"] == "SCHEMA_IDENTITY_MISMATCH"
    )
    normalized_reconciliation_blocked_count = sum(
        1 for item in items if item["normalized_validation_status"] == "BLOCKED"
    )
    blocker_codes = {REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_BLOCKER_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED_BLOCKER_CODE)
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])

    preview_status = "BLOCKED"
    primary_blocker_code = REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_BLOCKER_CODE
    if normalized_schema_fail_count:
        primary_blocker_code = PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED_BLOCKER_CODE
    elif normalized_reconciliation_blocked_count:
        primary_blocker_code = POST_NORMALIZATION_RECONCILIATION_REQUIRED_BLOCKER_CODE
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "normalization_preview_id": normalization_preview_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_TRUTH_ROLE,
        "normalization_preview_role": STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_ROLE,
        "source_ledger_recheck_preview_hash": ledger_recheck_preview_report.get("preview_hash"),
        "source_ledger_recheck_preview_status": ledger_recheck_preview_report.get("preview_status"),
        "source_ledger_recheck_preview_validator_status": source_result.status,
        "source_ledger_recheck_candidate_count": ledger_recheck_preview_report.get("ledger_recheck_candidate_count"),
        "source_replacement_validation_fail_count": ledger_recheck_preview_report.get("replacement_validation_fail_count"),
        "item_count": len(items),
        "normalization_candidate_count": len(items),
        "replacement_path_exists_count": sum(1 for item in items if item["replacement_path_exists"]),
        "missing_field_total_count": sum(len(item["original_missing_fields"]) for item in items),
        "proposed_field_total_count": sum(int(item["proposed_field_count"]) for item in items),
        "proposed_current_evidence_write_true_count": sum(
            1 for item in items if item["proposed_current_evidence_write_allowed"]
        ),
        "normalized_schema_fail_count": normalized_schema_fail_count,
        "normalized_reconciliation_blocked_count": normalized_reconciliation_blocked_count,
        "normalized_pass_count": sum(1 for item in items if item["normalized_validation_status"] == "PASS"),
        "ready_preview_only_count": ready_preview_count,
        "normalization_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "current_evidence_usable_after_normalization_preview_count": 0,
        "preview_status": preview_status,
        "primary_blocker_code": primary_blocker_code,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": (
            "Schema normalization preview can remove the missing-field failures, but post-normalization reconciliation remains required. Do not write replacements or current evidence."
            if items
            else "No stale-loop replacement schema normalization candidates were found."
        ),
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "normalization_preview_only": True,
        "normalization_write_allowed": False,
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
        "normalization_preview_hash": "",
    }
    report["normalization_preview_hash"] = upbit_paper_stale_loop_replacement_schema_normalization_preview_hash(report)
    return report


def write_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_replacement_schema_normalization_preview_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "normalization_preview_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "normalization_preview_role",
        "source_ledger_recheck_preview_hash",
        "source_ledger_recheck_preview_status",
        "source_ledger_recheck_preview_validator_status",
        "source_ledger_recheck_candidate_count",
        "source_replacement_validation_fail_count",
        "item_count",
        "normalization_candidate_count",
        "replacement_path_exists_count",
        "missing_field_total_count",
        "proposed_field_total_count",
        "proposed_current_evidence_write_true_count",
        "normalized_schema_fail_count",
        "normalized_reconciliation_blocked_count",
        "normalized_pass_count",
        "ready_preview_only_count",
        "normalization_write_allowed_count",
        "current_evidence_write_allowed_count",
        "current_evidence_usable_after_normalization_preview_count",
        "preview_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "normalization_preview_only",
        "normalization_write_allowed",
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
        "normalization_preview_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
            "FAIL",
            f"stale-loop replacement schema normalization preview missing fields: {missing}",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_SCHEMA_ID:
        return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
            "FAIL", "stale-loop replacement schema normalization preview schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("normalization_preview_hash") != upbit_paper_stale_loop_replacement_schema_normalization_preview_hash(report):
        return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
            "FAIL", "stale-loop replacement schema normalization preview hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
            "BLOCKED", "stale-loop replacement schema normalization preview scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if (
        report.get("truth_role") != STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_TRUTH_ROLE
        or report.get("normalization_preview_role") != STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW_ROLE
    ):
        return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
            "FAIL", "stale-loop replacement schema normalization preview role mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    false_fields = (
        "normalization_write_allowed",
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
        return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
            "BLOCKED",
            "stale-loop replacement schema normalization preview attempted mutation or live permission",
            "LIVE_FINAL_GUARD_FAILED",
        )
    if (
        report.get("display_only") is not True
        or report.get("dashboard_truth_only") is not True
        or report.get("paper_only") is not True
        or report.get("normalization_preview_only") is not True
    ):
        return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
            "BLOCKED", "stale-loop replacement schema normalization preview must remain display-only", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("normalization_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
        or report.get("current_evidence_usable_after_normalization_preview_count") != 0
    ):
        return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
            "BLOCKED",
            "stale-loop replacement schema normalization preview exposed write or current-evidence usability",
            "LIVE_FINAL_GUARD_FAILED",
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("item_count") != len(items) or report.get("normalization_candidate_count") != len(items):
        return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
            "FAIL", "stale-loop replacement schema normalization preview item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected = {
        "replacement_path_exists_count": 0,
        "missing_field_total_count": 0,
        "proposed_field_total_count": 0,
        "proposed_current_evidence_write_true_count": 0,
        "normalized_schema_fail_count": 0,
        "normalized_reconciliation_blocked_count": 0,
        "normalized_pass_count": 0,
        "ready_preview_only_count": 0,
    }
    session_id = str(report.get("session_id"))
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                "FAIL", "stale-loop replacement schema normalization preview item must be an object", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_required = {
            "priority_order",
            "replacement_loop_id",
            "replacement_path",
            "source_path",
            "replacement_path_exists",
            "original_validation_status",
            "original_validation_blocker_code",
            "original_missing_fields",
            "proposed_field_count",
            "proposed_field_names",
            "proposed_preflight_existing_runtime_state_detected",
            "proposed_preflight_recovery_guard_status",
            "proposed_preflight_recovery_guard_hash",
            "proposed_preflight_recovery_guard_primary_blocker_code",
            "proposed_preflight_runtime_recovery_guard_path",
            "proposed_preflight_paper_runtime_resume_allowed",
            "proposed_current_evidence_write_allowed",
            "proposed_current_evidence_write_required_by_validator",
            "normalized_replacement_hash",
            "normalized_validation_status",
            "normalized_validation_blocker_code",
            "normalized_validation_message",
            "normalization_item_status",
            "primary_blocker_code",
            "blocker_codes",
            "operator_action",
            "normalization_preview_only",
            "normalization_write_allowed",
            "replacement_write_allowed",
            "current_evidence_write_allowed",
            "preview_current_evidence_usable",
            "actual_long_run_evidence_created",
            "live_permission_created",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                "FAIL", f"stale-loop replacement schema normalization preview item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("priority_order") != index:
            return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                "FAIL", "stale-loop replacement schema normalization preview priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for path_field in ("source_path", "replacement_path"):
            if not _artifact_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                    "BLOCKED", f"stale-loop replacement schema normalization preview {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
        if (
            item.get("normalization_preview_only") is not True
            or item.get("normalization_write_allowed")
            or item.get("replacement_write_allowed")
            or item.get("current_evidence_write_allowed")
            or item.get("preview_current_evidence_usable")
            or item.get("actual_long_run_evidence_created")
            or item.get("live_permission_created")
        ):
            return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                "BLOCKED", "stale-loop replacement schema normalization preview item attempted write or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        missing_fields = item.get("original_missing_fields")
        proposed_fields = item.get("proposed_field_names")
        if not isinstance(missing_fields, list) or not isinstance(proposed_fields, list):
            return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                "FAIL", "stale-loop replacement schema normalization preview fields must be arrays", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("original_validation_blocker_code") != "SCHEMA_IDENTITY_MISMATCH":
            return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                "FAIL", "normalization preview item must originate from schema identity mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("proposed_field_count") != len(proposed_fields):
            return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                "FAIL", "normalization preview proposed field count mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("proposed_current_evidence_write_allowed") is not item.get("proposed_current_evidence_write_required_by_validator"):
            return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                "FAIL", "normalization preview validator-required current evidence write flag mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("normalized_validation_status") == "PASS":
            expected["normalized_pass_count"] += 1
        elif item.get("normalized_validation_status") == "BLOCKED":
            expected["normalized_reconciliation_blocked_count"] += 1
            if item.get("normalized_validation_blocker_code") is None:
                return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                    "FAIL", "blocked normalized preview item must expose blocker", "SCHEMA_IDENTITY_MISMATCH"
                )
        else:
            expected["normalized_schema_fail_count"] += 1
        if item.get("normalization_item_status") == "READY_PREVIEW_ONLY":
            expected["ready_preview_only_count"] += 1
            if item.get("normalized_validation_blocker_code") == "SCHEMA_IDENTITY_MISMATCH":
                return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                    "FAIL", "READY preview cannot still have schema identity mismatch", "SCHEMA_IDENTITY_MISMATCH"
                )
        else:
            if item.get("normalization_item_status") != "BLOCKED":
                return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                    "FAIL", "normalization preview item status is invalid", "SCHEMA_IDENTITY_MISMATCH"
                )
        if item.get("replacement_path_exists"):
            expected["replacement_path_exists_count"] += 1
        expected["missing_field_total_count"] += len(missing_fields)
        expected["proposed_field_total_count"] += int(item.get("proposed_field_count") or 0)
        if item.get("proposed_current_evidence_write_allowed"):
            expected["proposed_current_evidence_write_true_count"] += 1
        if not isinstance(item.get("blocker_codes"), list):
            return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                "FAIL", "normalization preview item blocker_codes must be an array", "SCHEMA_IDENTITY_MISMATCH"
            )
    for field, value in expected.items():
        if report.get(field) != value:
            return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
                "FAIL", f"stale-loop replacement schema normalization preview count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("preview_status") != "BLOCKED" or not report.get("primary_blocker_code"):
        return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
            "FAIL", "stale-loop replacement schema normalization preview must remain blocked", "SCHEMA_IDENTITY_MISMATCH"
        )
    return UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewValidationResult(
        "PASS",
        "Upbit PAPER stale-loop replacement schema normalization preview is display-only and live-blocked",
        None,
    )
