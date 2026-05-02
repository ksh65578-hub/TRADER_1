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
from trader1.runtime.paper.upbit_paper_persistent_loop import validate_upbit_paper_persistent_loop_report
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation_operator_queue_closure import (
    STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE,
    validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_LEDGER_RECHECK_PREVIEW_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_ledger_recheck_preview_report.v1"
)
STALE_LOOP_LEDGER_RECHECK_PREVIEW_TRUTH_ROLE = "paper_runtime_stale_loop_ledger_recheck_preview_truth"
STALE_LOOP_LEDGER_RECHECK_PREVIEW_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_LEDGER_RECHECK_PREVIEW_DISPLAY_ONLY_NO_EVIDENCE_WRITES"
)
STALE_LOOP_LEDGER_RECHECK_PREVIEW_BLOCKER_CODE = "STALE_LOOP_LEDGER_RECHECK_PREVIEW_BLOCKED"
PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED_BLOCKER_CODE = "PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED"
LEDGER_RECHECK_BINDING_MISMATCH_BLOCKER_CODE = "LEDGER_RECHECK_BINDING_MISMATCH"


@dataclass(frozen=True)
class UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_ledger_recheck_preview_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("preview_hash", None)
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


def _ledger_evidence_passes(ledger_evidence_report: dict[str, Any]) -> bool:
    return (
        ledger_evidence_report.get("runtime_evidence_status") == "PASS"
        and ledger_evidence_report.get("idempotency_status") == "PASS"
        and ledger_evidence_report.get("reconciliation_status") == "PASS"
        and ledger_evidence_report.get("source_rollup_validation_status") == "PASS"
        and int(ledger_evidence_report.get("mismatch_count") or 0) == 0
        and ledger_evidence_report.get("live_order_allowed") is False
        and ledger_evidence_report.get("can_live_trade") is False
        and ledger_evidence_report.get("scale_up_allowed") is False
    )


def _skip_status_for_lane(lane: str) -> str:
    if lane == "RECOVERY_GUARD_REQUIRED":
        return "SKIPPED_RECOVERY_REQUIRED"
    if lane in {"OPERATOR_REVIEW_REQUIRED", "UNSAFE_OR_SCOPE_BLOCKED"}:
        return "SKIPPED_OPERATOR_REVIEW"
    return "BLOCKED"


def _build_item(
    *,
    root: Path,
    session_id: str,
    closure_item: dict[str, Any],
    ledger_evidence_report: dict[str, Any],
    ledger_evidence_ready: bool,
) -> dict[str, Any]:
    replacement_path = str(closure_item.get("replacement_path") or "")
    replacement_absolute = Path(root).resolve() / replacement_path
    replacement_report = _load_json(replacement_absolute)
    replacement_exists = replacement_report is not None
    replacement_result = None
    if replacement_report is not None:
        replacement_result = validate_upbit_paper_persistent_loop_report(replacement_report)

    lane = str(closure_item.get("closure_lane") or "UNKNOWN")
    is_candidate = lane == "LEDGER_RECHECK_READY"
    ledger_head_hash_match = (
        closure_item.get("current_ledger_head_hash") == ledger_evidence_report.get("source_ledger_head_hash")
    )
    ledger_rollup_hash_match = (
        closure_item.get("current_ledger_rollup_hash") == ledger_evidence_report.get("source_rollup_hash")
    )
    ledger_binding_pass = (
        is_candidate
        and ledger_evidence_ready
        and ledger_head_hash_match
        and ledger_rollup_hash_match
        and closure_item.get("current_ledger_idempotency_status") == "PASS"
        and closure_item.get("current_ledger_reconciliation_status") == "PASS"
    )
    replacement_validation_status = "MISSING"
    replacement_validation_message = "replacement report missing or unreadable"
    replacement_validation_blocker_code = "MEASUREMENT_MISSING"
    if replacement_result is not None:
        replacement_validation_status = replacement_result.status
        replacement_validation_message = replacement_result.message
        replacement_validation_blocker_code = replacement_result.blocker_code

    blocker_codes = set(str(code) for code in closure_item.get("blocking_codes") or [])
    if is_candidate and not ledger_binding_pass:
        blocker_codes.add(LEDGER_RECHECK_BINDING_MISMATCH_BLOCKER_CODE)
    if is_candidate and replacement_validation_status != "PASS":
        blocker_codes.add(PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED_BLOCKER_CODE)
    if not is_candidate:
        blocker_codes.add(str(closure_item.get("source_item_blocker_code") or STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE))

    if not is_candidate:
        preview_item_status = _skip_status_for_lane(lane)
    elif ledger_binding_pass and replacement_validation_status == "PASS":
        preview_item_status = "PASS_PREVIEW_ONLY"
    else:
        preview_item_status = "BLOCKED"

    return {
        "priority_order": int(closure_item.get("priority_order") or 0),
        "replacement_loop_id": str(closure_item.get("replacement_loop_id") or "UNKNOWN"),
        "source_path": str(closure_item.get("source_path") or ""),
        "replacement_path": replacement_path,
        "closure_lane": lane,
        "ledger_recheck_candidate": is_candidate,
        "replacement_path_exists": replacement_exists,
        "replacement_validation_status": replacement_validation_status,
        "replacement_validation_blocker_code": replacement_validation_blocker_code,
        "replacement_validation_message": replacement_validation_message,
        "ledger_binding_status": "PASS" if ledger_binding_pass else ("BLOCKED" if is_candidate else "NOT_APPLICABLE"),
        "ledger_head_hash_match": ledger_head_hash_match,
        "ledger_rollup_hash_match": ledger_rollup_hash_match,
        "current_ledger_evidence_status": str(ledger_evidence_report.get("runtime_evidence_status") or "UNKNOWN"),
        "current_ledger_idempotency_status": str(ledger_evidence_report.get("idempotency_status") or "UNKNOWN"),
        "current_ledger_reconciliation_status": str(ledger_evidence_report.get("reconciliation_status") or "UNKNOWN"),
        "current_ledger_head_hash": ledger_evidence_report.get("source_ledger_head_hash"),
        "current_ledger_rollup_hash": ledger_evidence_report.get("source_rollup_hash"),
        "preview_item_status": preview_item_status,
        "primary_blocker_code": None if preview_item_status == "PASS_PREVIEW_ONLY" else sorted(blocker_codes)[0],
        "blocker_codes": sorted(blocker_codes),
        "operator_action": (
            "Repair the replacement persistent-loop schema before any current-evidence promotion."
            if is_candidate and replacement_validation_status != "PASS"
            else "Keep this stale-loop item out of ledger recheck until its closure lane is resolved."
            if not is_candidate
            else "Ledger binding preview passed; keep current-evidence writes blocked until an explicit promotion gate exists."
        ),
        "preview_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_ledger_recheck_preview_report(
    *,
    root: Path,
    closure_report: dict[str, Any],
    ledger_idempotency_evidence_report: dict[str, Any],
    preview_id: str = "upbit-paper-stale-loop-ledger-recheck-preview",
) -> dict[str, Any]:
    root = Path(root).resolve()
    closure_result = validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(closure_report)
    ledger_result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(ledger_idempotency_evidence_report)
    session_id = str(closure_report.get("session_id", "UNKNOWN"))
    ledger_evidence_ready = ledger_result.status == "PASS" and _ledger_evidence_passes(ledger_idempotency_evidence_report)
    items = [
        _build_item(
            root=root,
            session_id=session_id,
            closure_item=item,
            ledger_evidence_report=ledger_idempotency_evidence_report,
            ledger_evidence_ready=ledger_evidence_ready,
        )
        for item in closure_report.get("items", [])
        if isinstance(item, dict)
    ]

    ledger_recheck_candidate_count = sum(1 for item in items if item["ledger_recheck_candidate"])
    preview_pass_count = sum(1 for item in items if item["preview_item_status"] == "PASS_PREVIEW_ONLY")
    preview_blocked_count = sum(1 for item in items if item["preview_item_status"] == "BLOCKED")
    replacement_validation_fail_count = sum(
        1 for item in items if item["ledger_recheck_candidate"] and item["replacement_validation_status"] != "PASS"
    )
    ledger_binding_blocked_count = sum(
        1 for item in items if item["ledger_recheck_candidate"] and item["ledger_binding_status"] != "PASS"
    )

    blocker_codes = {STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE}
    if closure_result.status != "PASS":
        blocker_codes.add(closure_result.blocker_code or STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE)
    if ledger_result.status != "PASS":
        blocker_codes.add(ledger_result.blocker_code or "LEDGER_INTEGRITY_FAIL")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])

    preview_status = "PASS_PREVIEW_ONLY"
    primary_blocker_code = STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE
    if replacement_validation_fail_count:
        preview_status = "BLOCKED"
        primary_blocker_code = PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED_BLOCKER_CODE
    elif ledger_binding_blocked_count or ledger_result.status != "PASS":
        preview_status = "BLOCKED"
        primary_blocker_code = LEDGER_RECHECK_BINDING_MISMATCH_BLOCKER_CODE
    elif any(item["preview_item_status"].startswith("SKIPPED") for item in items):
        preview_status = "BLOCKED"
        primary_blocker_code = STALE_LOOP_OPERATOR_QUEUE_CLOSURE_BLOCKER_CODE

    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_LEDGER_RECHECK_PREVIEW_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "preview_id": preview_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_LEDGER_RECHECK_PREVIEW_TRUTH_ROLE,
        "preview_role": STALE_LOOP_LEDGER_RECHECK_PREVIEW_ROLE,
        "source_closure_id": closure_report.get("closure_id"),
        "source_closure_hash": closure_report.get("closure_hash"),
        "source_closure_validator_status": closure_result.status,
        "source_closure_status": closure_report.get("closure_status"),
        "source_ledger_idempotency_evidence_hash": ledger_idempotency_evidence_report.get("evidence_hash"),
        "source_ledger_idempotency_validator_status": ledger_result.status,
        "source_ledger_idempotency_status": ledger_idempotency_evidence_report.get("idempotency_status"),
        "source_ledger_reconciliation_status": ledger_idempotency_evidence_report.get("reconciliation_status"),
        "source_ledger_mismatch_count": int(ledger_idempotency_evidence_report.get("mismatch_count") or 0),
        "source_ledger_head_hash": ledger_idempotency_evidence_report.get("source_ledger_head_hash"),
        "source_ledger_rollup_hash": ledger_idempotency_evidence_report.get("source_rollup_hash"),
        "item_count": len(items),
        "ledger_recheck_candidate_count": ledger_recheck_candidate_count,
        "ledger_binding_pass_count": sum(1 for item in items if item["ledger_binding_status"] == "PASS"),
        "ledger_binding_blocked_count": ledger_binding_blocked_count,
        "replacement_path_exists_count": sum(1 for item in items if item["replacement_path_exists"]),
        "replacement_validation_pass_count": sum(
            1 for item in items if item["ledger_recheck_candidate"] and item["replacement_validation_status"] == "PASS"
        ),
        "replacement_validation_fail_count": replacement_validation_fail_count,
        "preview_pass_count": preview_pass_count,
        "preview_blocked_count": preview_blocked_count,
        "skipped_recovery_guard_required_count": sum(
            1 for item in items if item["preview_item_status"] == "SKIPPED_RECOVERY_REQUIRED"
        ),
        "skipped_operator_review_count": sum(
            1 for item in items if item["preview_item_status"] == "SKIPPED_OPERATOR_REVIEW"
        ),
        "current_evidence_usable_after_preview_count": 0,
        "current_evidence_write_allowed_count": 0,
        "preview_status": preview_status,
        "primary_blocker_code": primary_blocker_code,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": (
            "Repair replacement persistent-loop schemas before any current-evidence promotion."
            if replacement_validation_fail_count
            else "Resolve remaining stale-loop closure lanes before any current-evidence promotion."
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
        "preview_hash": "",
    }
    report["preview_hash"] = upbit_paper_stale_loop_ledger_recheck_preview_hash(report)
    return report


def write_upbit_paper_stale_loop_ledger_recheck_preview_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_ledger_recheck_preview_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_ledger_recheck_preview_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "preview_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "preview_role",
        "source_closure_id",
        "source_closure_hash",
        "source_closure_validator_status",
        "source_closure_status",
        "source_ledger_idempotency_evidence_hash",
        "source_ledger_idempotency_validator_status",
        "source_ledger_idempotency_status",
        "source_ledger_reconciliation_status",
        "source_ledger_mismatch_count",
        "source_ledger_head_hash",
        "source_ledger_rollup_hash",
        "item_count",
        "ledger_recheck_candidate_count",
        "ledger_binding_pass_count",
        "ledger_binding_blocked_count",
        "replacement_path_exists_count",
        "replacement_validation_pass_count",
        "replacement_validation_fail_count",
        "preview_pass_count",
        "preview_blocked_count",
        "skipped_recovery_guard_required_count",
        "skipped_operator_review_count",
        "current_evidence_usable_after_preview_count",
        "current_evidence_write_allowed_count",
        "preview_status",
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
        "preview_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "FAIL", f"stale-loop ledger recheck preview missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_LEDGER_RECHECK_PREVIEW_SCHEMA_ID:
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "FAIL", "stale-loop ledger recheck preview schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("preview_hash") != upbit_paper_stale_loop_ledger_recheck_preview_hash(report):
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "FAIL", "stale-loop ledger recheck preview hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "BLOCKED", "stale-loop ledger recheck preview scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if report.get("truth_role") != STALE_LOOP_LEDGER_RECHECK_PREVIEW_TRUTH_ROLE or report.get("preview_role") != STALE_LOOP_LEDGER_RECHECK_PREVIEW_ROLE:
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "FAIL", "stale-loop ledger recheck preview role mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    false_fields = (
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
    if any(report.get(field) is not False for field in false_fields):
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "BLOCKED", "stale-loop ledger recheck preview attempted mutation or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("display_only") is not True
        or report.get("dashboard_truth_only") is not True
        or report.get("paper_only") is not True
    ):
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "BLOCKED", "stale-loop ledger recheck preview must stay display-only PAPER evidence", "LIVE_FINAL_GUARD_FAILED"
        )
    if report.get("current_evidence_usable_after_preview_count") != 0 or report.get("current_evidence_write_allowed_count") != 0:
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "BLOCKED", "stale-loop ledger recheck preview exposed current evidence usability", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list):
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "FAIL", "stale-loop ledger recheck preview items must be an array", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("item_count") != len(items):
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "FAIL", "stale-loop ledger recheck preview item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected = {
        "ledger_recheck_candidate_count": 0,
        "ledger_binding_pass_count": 0,
        "ledger_binding_blocked_count": 0,
        "replacement_path_exists_count": 0,
        "replacement_validation_pass_count": 0,
        "replacement_validation_fail_count": 0,
        "preview_pass_count": 0,
        "preview_blocked_count": 0,
        "skipped_recovery_guard_required_count": 0,
        "skipped_operator_review_count": 0,
    }
    session_id = str(report.get("session_id"))
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                "FAIL", "stale-loop ledger recheck preview item must be an object", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_required = {
            "priority_order",
            "replacement_loop_id",
            "source_path",
            "replacement_path",
            "closure_lane",
            "ledger_recheck_candidate",
            "replacement_path_exists",
            "replacement_validation_status",
            "replacement_validation_blocker_code",
            "replacement_validation_message",
            "ledger_binding_status",
            "ledger_head_hash_match",
            "ledger_rollup_hash_match",
            "current_ledger_evidence_status",
            "current_ledger_idempotency_status",
            "current_ledger_reconciliation_status",
            "current_ledger_head_hash",
            "current_ledger_rollup_hash",
            "preview_item_status",
            "primary_blocker_code",
            "blocker_codes",
            "operator_action",
            "preview_current_evidence_usable",
            "current_evidence_write_allowed",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "actual_long_run_evidence_created",
            "live_permission_created",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                "FAIL", f"stale-loop ledger recheck preview item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("priority_order") != index:
            return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                "FAIL", "stale-loop ledger recheck preview priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for path_field in ("source_path", "replacement_path"):
            if not _artifact_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                    "BLOCKED", f"stale-loop ledger recheck preview {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
        if (
            item.get("preview_current_evidence_usable")
            or item.get("current_evidence_write_allowed")
            or item.get("persistent_loop_mutation_allowed")
            or item.get("replacement_write_allowed")
            or item.get("source_delete_allowed")
            or item.get("actual_long_run_evidence_created")
            or item.get("live_permission_created")
        ):
            return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                "BLOCKED", "stale-loop ledger recheck preview item attempted mutation or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        is_candidate = item.get("ledger_recheck_candidate") is True
        if is_candidate:
            expected["ledger_recheck_candidate_count"] += 1
            if item.get("ledger_binding_status") == "PASS" and (
                item.get("ledger_head_hash_match") is not True
                or item.get("ledger_rollup_hash_match") is not True
                or item.get("current_ledger_evidence_status") != "PASS"
                or item.get("current_ledger_idempotency_status") != "PASS"
                or item.get("current_ledger_reconciliation_status") != "PASS"
            ):
                return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                    "FAIL",
                    "stale-loop ledger recheck preview ledger PASS requires matching PASS ledger evidence",
                    "SCHEMA_IDENTITY_MISMATCH",
                )
            if item.get("ledger_binding_status") == "PASS":
                expected["ledger_binding_pass_count"] += 1
            else:
                expected["ledger_binding_blocked_count"] += 1
            if item.get("replacement_validation_status") == "PASS":
                expected["replacement_validation_pass_count"] += 1
            else:
                expected["replacement_validation_fail_count"] += 1
            if item.get("preview_item_status") == "PASS_PREVIEW_ONLY":
                expected["preview_pass_count"] += 1
                if item.get("ledger_binding_status") != "PASS" or item.get("replacement_validation_status") != "PASS":
                    return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                        "FAIL", "stale-loop ledger recheck preview passed without ledger and schema PASS", "SCHEMA_IDENTITY_MISMATCH"
                    )
            elif item.get("preview_item_status") == "BLOCKED":
                expected["preview_blocked_count"] += 1
            else:
                return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                    "FAIL", "ledger recheck candidate cannot be skipped", "SCHEMA_IDENTITY_MISMATCH"
                )
        elif item.get("preview_item_status") == "SKIPPED_RECOVERY_REQUIRED":
            expected["skipped_recovery_guard_required_count"] += 1
        elif item.get("preview_item_status") == "SKIPPED_OPERATOR_REVIEW":
            expected["skipped_operator_review_count"] += 1
        else:
            return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                "FAIL", "non-ledger stale-loop item must be skipped for operator/recovery review", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("replacement_path_exists"):
            expected["replacement_path_exists_count"] += 1
        if not isinstance(item.get("blocker_codes"), list):
            return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                "FAIL", "stale-loop ledger recheck preview item blocker_codes must be an array", "SCHEMA_IDENTITY_MISMATCH"
            )
    for field, value in expected.items():
        if report.get(field) != value:
            return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
                "FAIL", f"stale-loop ledger recheck preview count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("preview_status") == "PASS_PREVIEW_ONLY" and (
        expected["preview_blocked_count"]
        or expected["replacement_validation_fail_count"]
        or expected["ledger_binding_blocked_count"]
        or expected["skipped_recovery_guard_required_count"]
        or expected["skipped_operator_review_count"]
    ):
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "FAIL", "stale-loop ledger recheck preview cannot pass with blocked or skipped items", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("preview_status") == "BLOCKED" and not report.get("primary_blocker_code"):
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "FAIL", "blocked stale-loop ledger recheck preview must expose primary blocker", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("preview_status") not in {"PASS_PREVIEW_ONLY", "BLOCKED"}:
        return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
            "FAIL", "stale-loop ledger recheck preview status is invalid", "SCHEMA_IDENTITY_MISMATCH"
        )
    return UpbitPaperStaleLoopLedgerRecheckPreviewValidationResult(
        "PASS",
        "Upbit PAPER stale-loop ledger recheck preview is display-only, namespace-scoped, and live-blocked",
        None,
    )
