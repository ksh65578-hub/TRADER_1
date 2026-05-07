from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_stale_loop_replacement_schema_normalization_preview import (
    POST_NORMALIZATION_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    validate_upbit_paper_stale_loop_replacement_schema_normalization_preview_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_NORMALIZED_RECONCILIATION_PREVIEW_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_normalized_reconciliation_preview_report.v1"
)
STALE_LOOP_NORMALIZED_RECONCILIATION_PREVIEW_TRUTH_ROLE = (
    "paper_runtime_stale_loop_normalized_reconciliation_preview_truth"
)
STALE_LOOP_NORMALIZED_RECONCILIATION_PREVIEW_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_NORMALIZED_RECONCILIATION_PREVIEW_NO_WRITES"
)
NORMALIZED_RECONCILIATION_PREVIEW_BLOCKER_CODE = "NORMALIZED_RECONCILIATION_PREVIEW_BLOCKED"
NORMALIZED_RECONCILIATION_REQUIRED_BLOCKER_CODE = "NORMALIZED_RECONCILIATION_REQUIRED"

RECONCILIATION_INPUTS_NEEDED = [
    "normalized persistent-loop candidate must be recomputed against the latest ledger rollup",
    "ledger rollup reconciliation must PASS for the normalized loop hash",
    "operator reconciliation queue must be closed for the normalized loop hash",
    "current evidence closure recheck must PASS after reconciliation",
]


@dataclass(frozen=True)
class UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_normalized_reconciliation_preview_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("normalized_reconciliation_preview_hash", None)
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


def _build_item(item: dict[str, Any], priority_order: int) -> dict[str, Any]:
    normalized_blocker = item.get("normalized_validation_blocker_code")
    reconciliation_required = (
        item.get("normalized_validation_status") == "BLOCKED"
        and normalized_blocker in {"RECONCILIATION_REQUIRED", "MEASUREMENT_MISSING"}
    )
    blocker_codes = set(str(code) for code in item.get("blocker_codes") or [])
    blocker_codes.add(NORMALIZED_RECONCILIATION_PREVIEW_BLOCKER_CODE)
    if reconciliation_required:
        blocker_codes.add(NORMALIZED_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        blocker_codes.add(POST_NORMALIZATION_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(item.get("replacement_loop_id") or "UNKNOWN"),
        "replacement_path": str(item.get("replacement_path") or ""),
        "source_path": str(item.get("source_path") or ""),
        "normalized_replacement_hash": item.get("normalized_replacement_hash"),
        "normalized_validation_status": str(item.get("normalized_validation_status") or "UNKNOWN"),
        "normalized_validation_blocker_code": normalized_blocker,
        "normalization_item_status": str(item.get("normalization_item_status") or "UNKNOWN"),
        "schema_normalization_resolved": (
            item.get("normalization_item_status") == "READY_PREVIEW_ONLY"
            and normalized_blocker != "SCHEMA_IDENTITY_MISMATCH"
        ),
        "reconciliation_required": reconciliation_required,
        "post_normalization_reconciliation_required": reconciliation_required,
        "reconciliation_preview_status": "BLOCKED_RECONCILIATION_REQUIRED"
        if reconciliation_required
        else "BLOCKED_SCHEMA_OR_SOURCE_NOT_READY",
        "reconciliation_inputs_needed": list(RECONCILIATION_INPUTS_NEEDED),
        "primary_blocker_code": NORMALIZED_RECONCILIATION_REQUIRED_BLOCKER_CODE
        if reconciliation_required
        else NORMALIZED_RECONCILIATION_PREVIEW_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "operator_action": (
            "Do not write current evidence. Recompute the normalized loop against ledger reconciliation evidence first."
            if reconciliation_required
            else "Do not reconcile this item until schema normalization preview is READY_PREVIEW_ONLY."
        ),
        "normalized_reconciliation_preview_only": True,
        "reconciliation_write_allowed": False,
        "current_evidence_write_allowed": False,
        "preview_current_evidence_usable": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_normalized_reconciliation_preview_report(
    *,
    root: Path,
    normalization_preview_report: dict[str, Any],
    normalized_reconciliation_preview_id: str = "upbit-paper-stale-loop-normalized-reconciliation-preview",
) -> dict[str, Any]:
    source_result = validate_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(
        normalization_preview_report
    )
    session_id = str(normalization_preview_report.get("session_id", "UNKNOWN"))
    candidate_items = [
        item
        for item in normalization_preview_report.get("items", [])
        if isinstance(item, dict) and item.get("normalization_item_status") == "READY_PREVIEW_ONLY"
    ]
    items = [_build_item(item, index) for index, item in enumerate(candidate_items, start=1)]
    reconciliation_required_count = sum(1 for item in items if item["reconciliation_required"])
    schema_normalization_resolved_count = sum(1 for item in items if item["schema_normalization_resolved"])
    blocker_codes = {NORMALIZED_RECONCILIATION_PREVIEW_BLOCKER_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or "NORMALIZATION_PREVIEW_INVALID")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    if reconciliation_required_count:
        blocker_codes.add(NORMALIZED_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        blocker_codes.add(POST_NORMALIZATION_RECONCILIATION_REQUIRED_BLOCKER_CODE)

    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_NORMALIZED_RECONCILIATION_PREVIEW_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "normalized_reconciliation_preview_id": normalized_reconciliation_preview_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_NORMALIZED_RECONCILIATION_PREVIEW_TRUTH_ROLE,
        "normalized_reconciliation_preview_role": STALE_LOOP_NORMALIZED_RECONCILIATION_PREVIEW_ROLE,
        "source_normalization_preview_hash": normalization_preview_report.get("normalization_preview_hash"),
        "source_normalization_preview_status": normalization_preview_report.get("preview_status"),
        "source_normalization_preview_validator_status": source_result.status,
        "source_normalization_candidate_count": normalization_preview_report.get("normalization_candidate_count"),
        "item_count": len(items),
        "normalized_reconciliation_candidate_count": len(items),
        "schema_normalization_resolved_count": schema_normalization_resolved_count,
        "reconciliation_required_count": reconciliation_required_count,
        "schema_mismatch_after_normalization_count": sum(
            1 for item in items if item["normalized_validation_blocker_code"] == "SCHEMA_IDENTITY_MISMATCH"
        ),
        "current_evidence_usable_after_reconciliation_preview_count": 0,
        "reconciliation_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "preview_status": "BLOCKED",
        "primary_blocker_code": NORMALIZED_RECONCILIATION_REQUIRED_BLOCKER_CODE
        if reconciliation_required_count
        else NORMALIZED_RECONCILIATION_PREVIEW_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": (
            "Run a bounded normalized reconciliation recheck before any current-evidence closure decision."
            if items
            else "No normalized reconciliation candidates are available."
        ),
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "normalized_reconciliation_preview_only": True,
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
        "normalized_reconciliation_preview_hash": "",
    }
    report["normalized_reconciliation_preview_hash"] = (
        upbit_paper_stale_loop_normalized_reconciliation_preview_hash(report)
    )
    return report


def write_upbit_paper_stale_loop_normalized_reconciliation_preview_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_normalized_reconciliation_preview_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_normalized_reconciliation_preview_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "normalized_reconciliation_preview_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "normalized_reconciliation_preview_role",
        "source_normalization_preview_hash",
        "source_normalization_preview_status",
        "source_normalization_preview_validator_status",
        "source_normalization_candidate_count",
        "item_count",
        "normalized_reconciliation_candidate_count",
        "schema_normalization_resolved_count",
        "reconciliation_required_count",
        "schema_mismatch_after_normalization_count",
        "current_evidence_usable_after_reconciliation_preview_count",
        "reconciliation_write_allowed_count",
        "current_evidence_write_allowed_count",
        "preview_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "normalized_reconciliation_preview_only",
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
        "normalized_reconciliation_preview_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "FAIL", f"normalized reconciliation preview missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_NORMALIZED_RECONCILIATION_PREVIEW_SCHEMA_ID:
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "FAIL", "normalized reconciliation preview schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("normalized_reconciliation_preview_hash") != upbit_paper_stale_loop_normalized_reconciliation_preview_hash(report):
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "FAIL", "normalized reconciliation preview hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "BLOCKED", "normalized reconciliation preview scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if (
        report.get("truth_role") != STALE_LOOP_NORMALIZED_RECONCILIATION_PREVIEW_TRUTH_ROLE
        or report.get("normalized_reconciliation_preview_role") != STALE_LOOP_NORMALIZED_RECONCILIATION_PREVIEW_ROLE
    ):
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "FAIL", "normalized reconciliation preview role mismatch", "SCHEMA_IDENTITY_MISMATCH"
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
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "BLOCKED", "normalized reconciliation preview attempted mutation or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("display_only") is not True
        or report.get("dashboard_truth_only") is not True
        or report.get("paper_only") is not True
        or report.get("normalized_reconciliation_preview_only") is not True
    ):
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "BLOCKED", "normalized reconciliation preview must remain display-only", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("reconciliation_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
        or report.get("current_evidence_usable_after_reconciliation_preview_count") != 0
    ):
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "BLOCKED", "normalized reconciliation preview exposed write or current-evidence usability", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("item_count") != len(items) or report.get("normalized_reconciliation_candidate_count") != len(items):
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "FAIL", "normalized reconciliation preview item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected_schema_resolved = 0
    expected_reconciliation_required = 0
    expected_schema_mismatch = 0
    session_id = str(report.get("session_id"))
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
                "FAIL", "normalized reconciliation preview item must be an object", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_required = {
            "priority_order",
            "replacement_loop_id",
            "replacement_path",
            "source_path",
            "normalized_replacement_hash",
            "normalized_validation_status",
            "normalized_validation_blocker_code",
            "normalization_item_status",
            "schema_normalization_resolved",
            "reconciliation_required",
            "post_normalization_reconciliation_required",
            "reconciliation_preview_status",
            "reconciliation_inputs_needed",
            "primary_blocker_code",
            "blocker_codes",
            "operator_action",
            "normalized_reconciliation_preview_only",
            "reconciliation_write_allowed",
            "current_evidence_write_allowed",
            "preview_current_evidence_usable",
            "actual_long_run_evidence_created",
            "live_permission_created",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
                "FAIL", f"normalized reconciliation preview item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("priority_order") != index:
            return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
                "FAIL", "normalized reconciliation preview priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for path_field in ("source_path", "replacement_path"):
            if not _artifact_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
                    "BLOCKED", f"normalized reconciliation preview {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
        if (
            item.get("normalized_reconciliation_preview_only") is not True
            or item.get("reconciliation_write_allowed")
            or item.get("current_evidence_write_allowed")
            or item.get("preview_current_evidence_usable")
            or item.get("actual_long_run_evidence_created")
            or item.get("live_permission_created")
        ):
            return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
                "BLOCKED", "normalized reconciliation preview item attempted write or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        if item.get("schema_normalization_resolved"):
            expected_schema_resolved += 1
            if item.get("normalized_validation_blocker_code") == "SCHEMA_IDENTITY_MISMATCH":
                return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
                    "FAIL", "schema-resolved item still has schema identity mismatch", "SCHEMA_IDENTITY_MISMATCH"
                )
        if item.get("reconciliation_required"):
            expected_reconciliation_required += 1
            if (
                item.get("normalized_validation_status") != "BLOCKED"
                or item.get("normalized_validation_blocker_code") not in {"RECONCILIATION_REQUIRED", "MEASUREMENT_MISSING"}
            ):
                return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
                    "FAIL",
                    "reconciliation-required item must be blocked by reconciliation or runtime-depth evidence",
                    "SCHEMA_IDENTITY_MISMATCH",
                )
            if item.get("primary_blocker_code") != NORMALIZED_RECONCILIATION_REQUIRED_BLOCKER_CODE:
                return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
                    "FAIL", "reconciliation-required item primary blocker mismatch", "SCHEMA_IDENTITY_MISMATCH"
                )
        if item.get("normalized_validation_blocker_code") == "SCHEMA_IDENTITY_MISMATCH":
            expected_schema_mismatch += 1
        if not isinstance(item.get("reconciliation_inputs_needed"), list) or not item["reconciliation_inputs_needed"]:
            return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
                "FAIL", "normalized reconciliation preview must list required reconciliation inputs", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("schema_normalization_resolved_count") != expected_schema_resolved:
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "FAIL", "schema normalization resolved count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("reconciliation_required_count") != expected_reconciliation_required:
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "FAIL", "reconciliation required count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_mismatch_after_normalization_count") != expected_schema_mismatch:
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "FAIL", "schema mismatch after normalization count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("preview_status") != "BLOCKED" or not report.get("primary_blocker_code"):
        return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
            "FAIL", "normalized reconciliation preview must remain blocked", "SCHEMA_IDENTITY_MISMATCH"
        )
    return UpbitPaperStaleLoopNormalizedReconciliationPreviewValidationResult(
        "PASS",
        "Upbit PAPER stale-loop normalized reconciliation preview is display-only and live-blocked",
        None,
    )
