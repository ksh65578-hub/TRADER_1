from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.ledger.paper_ledger_rollup import (
    paper_ledger_rollup_hash,
    validate_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_normalized_reconciliation_recheck import (
    validate_upbit_paper_stale_loop_normalized_reconciliation_recheck_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report.v1"
)
STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK_TRUTH_ROLE = (
    "paper_runtime_stale_loop_ledger_rollup_reconciliation_recheck_truth"
)
STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK_NO_WRITES"
)
LEDGER_ROLLUP_RECONCILIATION_RECHECK_BLOCKER_CODE = "LEDGER_ROLLUP_RECONCILIATION_RECHECK_BLOCKED"
LEDGER_ROLLUP_RECHECK_REQUIRES_ROLLUP_ARTIFACT_BLOCKER_CODE = (
    "LEDGER_ROLLUP_RECHECK_REQUIRES_ROLLUP_ARTIFACT"
)


@dataclass(frozen=True)
class UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("ledger_rollup_reconciliation_recheck_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/")
        and ".." not in normalized.split("/")
        and "/live/" not in normalized
    )


def _safe_load_json(path: Path) -> tuple[dict[str, Any] | None, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "MISSING"
    except UnicodeDecodeError:
        return None, "INVALID_UTF8"
    except json.JSONDecodeError:
        return None, "INVALID_JSON"
    if not isinstance(value, dict):
        return None, "NOT_OBJECT"
    return value, "PASS"


def _reason_codes(
    *,
    load_status: str,
    validator_status: str,
    rollup_hash_match: bool,
    source_reason_codes: list[Any],
) -> list[str]:
    reasons = {str(reason) for reason in source_reason_codes if reason}
    if load_status == "MISSING":
        reasons.add("LEDGER_ROLLUP_ARTIFACT_MISSING")
    elif load_status != "PASS":
        reasons.add("LEDGER_ROLLUP_ARTIFACT_UNREADABLE")
    if validator_status != "PASS":
        reasons.add("LEDGER_ROLLUP_VALIDATOR_NOT_PASS")
    if not rollup_hash_match:
        reasons.add("LEDGER_ROLLUP_HASH_NOT_RECONCILED")
    reasons.add("LEDGER_ROLLUP_RECONCILIATION_REQUIRED")
    return sorted(reasons)


def _reason_rollup(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        for reason in item.get("recheck_reason_codes") or []:
            counts[str(reason)] = counts.get(str(reason), 0) + 1
    return [{"reason_code": reason, "count": counts[reason]} for reason in sorted(counts)]


def _build_item(*, root: Path, session_id: str, source_item: dict[str, Any], priority_order: int) -> dict[str, Any]:
    rollup_path = str(source_item.get("normalized_paper_ledger_rollup_path") or "")
    rollup, load_status = _safe_load_json(_rooted(root, rollup_path))
    artifact_hash = rollup.get("rollup_hash") if isinstance(rollup, dict) else None
    recomputed_hash = paper_ledger_rollup_hash(rollup) if isinstance(rollup, dict) else None
    hash_self_check = (
        "PASS"
        if isinstance(artifact_hash, str) and artifact_hash == recomputed_hash
        else "FAIL"
        if isinstance(rollup, dict)
        else "NOT_AVAILABLE"
    )
    if isinstance(rollup, dict):
        result = validate_paper_ledger_rollup_report(rollup)
        validator_status = result.status
        validator_blocker_code = result.blocker_code
        validator_message = result.message
    else:
        validator_status = load_status
        validator_blocker_code = "LEDGER_ROLLUP_ARTIFACT_MISSING" if load_status == "MISSING" else load_status
        validator_message = f"ledger rollup artifact load status: {load_status}"
    expected_hash = source_item.get("normalized_paper_ledger_rollup_hash")
    rollup_hash_match = (
        isinstance(expected_hash, str)
        and isinstance(artifact_hash, str)
        and expected_hash == artifact_hash
        and artifact_hash == recomputed_hash
    )
    if load_status != "PASS":
        reconciliation_status = "BLOCKED_ROLLUP_ARTIFACT_MISSING_OR_UNREADABLE"
        primary_blocker = LEDGER_ROLLUP_RECHECK_REQUIRES_ROLLUP_ARTIFACT_BLOCKER_CODE
    elif validator_status != "PASS":
        reconciliation_status = "BLOCKED_ROLLUP_VALIDATION"
        primary_blocker = validator_blocker_code or "LEDGER_ROLLUP_VALIDATOR_NOT_PASS"
    elif not rollup_hash_match:
        reconciliation_status = "BLOCKED_ROLLUP_HASH_MISMATCH"
        primary_blocker = "LEDGER_ROLLUP_HASH_NOT_RECONCILED"
    else:
        reconciliation_status = "PASS_RECHECK_ONLY_CURRENT_EVIDENCE_BLOCKED"
        primary_blocker = "LEDGER_ROLLUP_RECONCILIATION_REQUIRED"
    reason_codes = _reason_codes(
        load_status=load_status,
        validator_status=validator_status,
        rollup_hash_match=rollup_hash_match,
        source_reason_codes=list(source_item.get("recheck_reason_codes") or []),
    )
    blocker_codes = sorted(
        {
            LEDGER_ROLLUP_RECONCILIATION_RECHECK_BLOCKER_CODE,
            primary_blocker,
            *reason_codes,
            *(str(code) for code in source_item.get("blocker_codes") or []),
        }
    )
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(source_item.get("replacement_loop_id") or "UNKNOWN"),
        "replacement_path": str(source_item.get("replacement_path") or ""),
        "ledger_rollup_path": rollup_path,
        "ledger_rollup_path_exists": rollup is not None,
        "ledger_rollup_load_status": load_status,
        "source_expected_rollup_hash": expected_hash,
        "artifact_rollup_hash": artifact_hash,
        "artifact_recomputed_rollup_hash": recomputed_hash,
        "rollup_hash_self_check": hash_self_check,
        "rollup_hash_match": rollup_hash_match,
        "rollup_validator_status": validator_status,
        "rollup_validator_blocker_code": validator_blocker_code,
        "rollup_validator_message": validator_message,
        "source_normalized_validation_status": source_item.get("normalized_validation_status"),
        "source_normalized_validation_blocker_code": source_item.get("normalized_validation_blocker_code"),
        "source_normalized_loop_status": source_item.get("normalized_loop_status"),
        "source_normalized_primary_blocker_code": source_item.get("normalized_primary_blocker_code"),
        "source_ledger_rollup_status": source_item.get("normalized_paper_ledger_rollup_status"),
        "source_ledger_rollup_primary_blocker_code": source_item.get(
            "normalized_paper_ledger_rollup_primary_blocker_code"
        ),
        "reconciliation_status": reconciliation_status,
        "primary_blocker_code": primary_blocker,
        "blocker_codes": blocker_codes,
        "recheck_reason_codes": reason_codes,
        "operator_action": (
            "Regenerate or reconcile the missing ledger-rollup artifact before any current-evidence closure."
            if load_status != "PASS"
            else "Keep this ledger-rollup result candidate-only until an explicit current-evidence promotion guard passes."
        ),
        "ledger_rollup_reconciliation_recheck_only": True,
        "ledger_rollup_write_allowed": False,
        "current_evidence_write_allowed": False,
        "candidate_current_evidence_usable": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(
    *,
    root: Path,
    normalized_reconciliation_recheck_report: dict[str, Any],
    ledger_rollup_reconciliation_recheck_id: str = "upbit-paper-stale-loop-ledger-rollup-reconciliation-recheck",
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(
        normalized_reconciliation_recheck_report
    )
    session_id = str(normalized_reconciliation_recheck_report.get("session_id", "UNKNOWN"))
    source_items = [
        item
        for item in normalized_reconciliation_recheck_report.get("items", [])
        if isinstance(item, dict) and item.get("ledger_rollup_recheck_required") is True
    ]
    items = [
        _build_item(root=root, session_id=session_id, source_item=item, priority_order=index)
        for index, item in enumerate(source_items, start=1)
    ]
    blocker_codes = {LEDGER_ROLLUP_RECONCILIATION_RECHECK_BLOCKER_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or "NORMALIZED_RECONCILIATION_RECHECK_INVALID")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    artifact_missing_count = sum(1 for item in items if item["ledger_rollup_load_status"] == "MISSING")
    artifact_exists_count = sum(1 for item in items if item["ledger_rollup_path_exists"])
    hash_match_count = sum(1 for item in items if item["rollup_hash_match"])
    validator_pass_count = sum(1 for item in items if item["rollup_validator_status"] == "PASS")
    blocked_count = sum(1 for item in items if item["reconciliation_status"].startswith("BLOCKED"))
    if artifact_missing_count:
        primary_blocker_code = LEDGER_ROLLUP_RECHECK_REQUIRES_ROLLUP_ARTIFACT_BLOCKER_CODE
        blocker_codes.add(primary_blocker_code)
    elif blocked_count:
        primary_blocker_code = sorted(
            str(item["primary_blocker_code"]) for item in items if item["reconciliation_status"].startswith("BLOCKED")
        )[0]
        blocker_codes.add(primary_blocker_code)
    else:
        primary_blocker_code = "LEDGER_ROLLUP_RECONCILIATION_REQUIRED"
        blocker_codes.add(primary_blocker_code)
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "ledger_rollup_reconciliation_recheck_id": ledger_rollup_reconciliation_recheck_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK_TRUTH_ROLE,
        "ledger_rollup_reconciliation_recheck_role": STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK_ROLE,
        "source_normalized_reconciliation_recheck_hash": normalized_reconciliation_recheck_report.get(
            "normalized_reconciliation_recheck_hash"
        ),
        "source_normalized_reconciliation_recheck_status": normalized_reconciliation_recheck_report.get(
            "recheck_status"
        ),
        "source_normalized_reconciliation_recheck_validator_status": source_result.status,
        "source_ledger_rollup_recheck_required_count": normalized_reconciliation_recheck_report.get(
            "ledger_rollup_recheck_required_count"
        ),
        "item_count": len(items),
        "ledger_rollup_recheck_candidate_count": len(items),
        "ledger_rollup_artifact_exists_count": artifact_exists_count,
        "ledger_rollup_artifact_missing_count": artifact_missing_count,
        "ledger_rollup_hash_match_count": hash_match_count,
        "ledger_rollup_validator_pass_count": validator_pass_count,
        "ledger_rollup_reconciliation_blocked_count": blocked_count,
        "reason_code_rollup": _reason_rollup(items),
        "candidate_current_evidence_usable_count": 0,
        "ledger_rollup_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "recheck_status": "BLOCKED",
        "primary_blocker_code": primary_blocker_code,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Regenerate or reconcile missing ledger-rollup artifacts before current-evidence closure.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "ledger_rollup_reconciliation_recheck_only": True,
        "ledger_rollup_write_allowed": False,
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
        "ledger_rollup_reconciliation_recheck_hash": "",
    }
    report["ledger_rollup_reconciliation_recheck_hash"] = (
        upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_hash(report)
    )
    return report


def write_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "ledger_rollup_reconciliation_recheck_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "ledger_rollup_reconciliation_recheck_role",
        "source_normalized_reconciliation_recheck_hash",
        "source_normalized_reconciliation_recheck_status",
        "source_normalized_reconciliation_recheck_validator_status",
        "source_ledger_rollup_recheck_required_count",
        "item_count",
        "ledger_rollup_recheck_candidate_count",
        "ledger_rollup_artifact_exists_count",
        "ledger_rollup_artifact_missing_count",
        "ledger_rollup_hash_match_count",
        "ledger_rollup_validator_pass_count",
        "ledger_rollup_reconciliation_blocked_count",
        "reason_code_rollup",
        "candidate_current_evidence_usable_count",
        "ledger_rollup_write_allowed_count",
        "current_evidence_write_allowed_count",
        "recheck_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "ledger_rollup_reconciliation_recheck_only",
        "ledger_rollup_write_allowed",
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
        "ledger_rollup_reconciliation_recheck_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "FAIL", f"ledger-rollup reconciliation recheck missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK_SCHEMA_ID:
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "FAIL", "ledger-rollup reconciliation recheck schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("ledger_rollup_reconciliation_recheck_hash") != upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_hash(report):
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "FAIL", "ledger-rollup reconciliation recheck hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "BLOCKED", "ledger-rollup reconciliation recheck scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if (
        report.get("truth_role") != STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK_TRUTH_ROLE
        or report.get("ledger_rollup_reconciliation_recheck_role")
        != STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK_ROLE
    ):
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "FAIL", "ledger-rollup reconciliation recheck role mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    false_fields = (
        "ledger_rollup_write_allowed",
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
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "BLOCKED", "ledger-rollup reconciliation recheck attempted mutation or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("display_only") is not True
        or report.get("dashboard_truth_only") is not True
        or report.get("paper_only") is not True
        or report.get("ledger_rollup_reconciliation_recheck_only") is not True
    ):
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "BLOCKED", "ledger-rollup reconciliation recheck must remain display-only", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("candidate_current_evidence_usable_count") != 0
        or report.get("ledger_rollup_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
    ):
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "BLOCKED", "ledger-rollup reconciliation recheck exposed writes or current evidence", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("item_count") != len(items) or report.get("ledger_rollup_recheck_candidate_count") != len(items):
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "FAIL", "ledger-rollup reconciliation recheck item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected_counts = {
        "ledger_rollup_artifact_exists_count": 0,
        "ledger_rollup_artifact_missing_count": 0,
        "ledger_rollup_hash_match_count": 0,
        "ledger_rollup_validator_pass_count": 0,
        "ledger_rollup_reconciliation_blocked_count": 0,
    }
    reason_counts: dict[str, int] = {}
    session_id = str(report.get("session_id"))
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
                "FAIL", "ledger-rollup reconciliation recheck item must be an object", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_required = {
            "priority_order",
            "replacement_loop_id",
            "replacement_path",
            "ledger_rollup_path",
            "ledger_rollup_path_exists",
            "ledger_rollup_load_status",
            "source_expected_rollup_hash",
            "artifact_rollup_hash",
            "artifact_recomputed_rollup_hash",
            "rollup_hash_self_check",
            "rollup_hash_match",
            "rollup_validator_status",
            "rollup_validator_blocker_code",
            "rollup_validator_message",
            "source_normalized_validation_status",
            "source_normalized_validation_blocker_code",
            "source_normalized_loop_status",
            "source_normalized_primary_blocker_code",
            "source_ledger_rollup_status",
            "source_ledger_rollup_primary_blocker_code",
            "reconciliation_status",
            "primary_blocker_code",
            "blocker_codes",
            "recheck_reason_codes",
            "operator_action",
            "ledger_rollup_reconciliation_recheck_only",
            "ledger_rollup_write_allowed",
            "current_evidence_write_allowed",
            "candidate_current_evidence_usable",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "actual_long_run_evidence_created",
            "live_permission_created",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
                "FAIL", f"ledger-rollup reconciliation recheck item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("priority_order") != index:
            return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
                "FAIL", "ledger-rollup reconciliation recheck priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for path_field in ("replacement_path", "ledger_rollup_path"):
            if not _artifact_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
                    "BLOCKED", f"ledger-rollup reconciliation recheck {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
        if (
            item.get("ledger_rollup_reconciliation_recheck_only") is not True
            or item.get("ledger_rollup_write_allowed")
            or item.get("current_evidence_write_allowed")
            or item.get("candidate_current_evidence_usable")
            or item.get("persistent_loop_mutation_allowed")
            or item.get("replacement_write_allowed")
            or item.get("source_delete_allowed")
            or item.get("actual_long_run_evidence_created")
            or item.get("live_permission_created")
        ):
            return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
                "BLOCKED", "ledger-rollup reconciliation recheck item attempted write or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        if item.get("ledger_rollup_path_exists"):
            expected_counts["ledger_rollup_artifact_exists_count"] += 1
        if item.get("ledger_rollup_load_status") == "MISSING":
            expected_counts["ledger_rollup_artifact_missing_count"] += 1
        if item.get("rollup_hash_match"):
            expected_counts["ledger_rollup_hash_match_count"] += 1
            if item.get("rollup_hash_self_check") != "PASS" or item.get("rollup_validator_status") != "PASS":
                return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
                    "FAIL", "ledger-rollup hash match requires rollup validator PASS", "SCHEMA_IDENTITY_MISMATCH"
                )
        if item.get("rollup_validator_status") == "PASS":
            expected_counts["ledger_rollup_validator_pass_count"] += 1
        if str(item.get("reconciliation_status") or "").startswith("BLOCKED"):
            expected_counts["ledger_rollup_reconciliation_blocked_count"] += 1
        reason_codes = item.get("recheck_reason_codes")
        if not isinstance(reason_codes, list) or not reason_codes:
            return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
                "FAIL", "ledger-rollup reconciliation recheck item must expose reason codes", "SCHEMA_IDENTITY_MISMATCH"
            )
        for reason in reason_codes:
            reason_counts[str(reason)] = reason_counts.get(str(reason), 0) + 1
    for field, expected in expected_counts.items():
        if report.get(field) != expected:
            return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
                "FAIL", f"ledger-rollup reconciliation recheck count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    expected_rollup = [{"reason_code": reason, "count": reason_counts[reason]} for reason in sorted(reason_counts)]
    if report.get("reason_code_rollup") != expected_rollup:
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "FAIL", "ledger-rollup reconciliation recheck reason rollup mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("recheck_status") != "BLOCKED" or not report.get("primary_blocker_code"):
        return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
            "FAIL", "ledger-rollup reconciliation recheck must remain blocked", "SCHEMA_IDENTITY_MISMATCH"
        )
    return UpbitPaperStaleLoopLedgerRollupReconciliationRecheckValidationResult(
        "PASS",
        "Upbit PAPER stale-loop ledger-rollup reconciliation recheck is display-only and live-blocked",
        None,
    )
