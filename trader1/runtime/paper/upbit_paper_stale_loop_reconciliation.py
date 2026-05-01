from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_persistent_loop import (
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_RECONCILIATION_SCHEMA_ID = "trader1.upbit_paper_stale_loop_reconciliation_report.v1"
STALE_LOOP_BLOCKER_CODE = "STALE_PERSISTENT_LOOP_REPORTS_REQUIRE_RECONCILIATION"
CURRENT_EVIDENCE_USE_POLICY = "CURRENT_SCHEMA_PASS_ONLY"
STALE_LOOP_RECONCILIATION_ROLE = "PAPER_RUNTIME_STALE_LOOP_RECONCILIATION_NOT_LONG_RUN_EVIDENCE"


@dataclass(frozen=True)
class UpbitPaperStaleLoopReconciliationValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def stale_loop_reconciliation_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("reconciliation_hash", None)
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


def _safe_read_bytes(path: Path) -> tuple[bytes | None, str | None]:
    try:
        return path.read_bytes(), None
    except FileNotFoundError:
        return None, "missing"
    except OSError:
        return None, "unreadable"


def _safe_json_from_bytes(raw: bytes) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return None, "invalid_utf8"
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(value, dict):
        return None, "not_object"
    return value, None


def _current_required_fields() -> set[str]:
    return {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "loop_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "loop_mode",
        "requested_cycle_count",
        "completed_cycle_count",
        "max_cycle_count",
        "cycle_results",
        "loop_status",
        "primary_blocker_code",
        "blockers",
        "actual_paper_runtime_executed",
        "recovery_guard_status",
        "recovery_guard_hash",
        "recovery_guard_primary_blocker_code",
        "runtime_recovery_guard_path",
        "paper_ledger_rollup_status",
        "paper_ledger_rollup_hash",
        "paper_ledger_rollup_primary_blocker_code",
        "paper_ledger_rollup_path",
        "paper_runtime_resume_allowed",
        "partial_write_recovery_required",
        "runtime_evidence_role",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "long_run_next_action",
        "promotion_eligible",
        "data_source_policy",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "loop_hash",
    }


def _unsafe_live_or_order_flag_detected(loop_report: dict[str, Any] | None) -> bool:
    if not isinstance(loop_report, dict):
        return False
    for field in (
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if loop_report.get(field):
            return True
    for item in loop_report.get("cycle_results") or []:
        if isinstance(item, dict) and (item.get("live_order_ready") or item.get("live_order_allowed") or item.get("can_live_trade") or item.get("scale_up_allowed")):
            return True
    return False


def _runtime_cycle_hashes(loop_report: dict[str, Any] | None) -> list[str]:
    if not isinstance(loop_report, dict):
        return []
    hashes: list[str] = []
    for item in loop_report.get("cycle_results") or []:
        if isinstance(item, dict) and isinstance(item.get("runtime_cycle_hash"), str):
            hashes.append(str(item["runtime_cycle_hash"]))
    return hashes


def _scope_status(loop_report: dict[str, Any] | None) -> str:
    if not isinstance(loop_report, dict):
        return "UNKNOWN"
    if loop_report.get("exchange") == "UPBIT" and loop_report.get("market_type") == "KRW_SPOT" and loop_report.get("mode") == "PAPER":
        return "MATCH"
    return "MISMATCH"


def _classification(
    *,
    loop_report: dict[str, Any] | None,
    load_error: str | None,
    validator_status: str,
    validator_blocker: str | None,
    missing_fields: list[str],
    unsafe: bool,
) -> tuple[str, bool, str]:
    if load_error:
        return "UNREADABLE_OR_CORRUPT", False, "QUARANTINE_OPERATOR_REVIEW"
    if unsafe or validator_blocker == "LIVE_FINAL_GUARD_FAILED":
        return "UNSAFE_BLOCKED", False, "QUARANTINE_OPERATOR_REVIEW"
    if _scope_status(loop_report) == "MISMATCH" or validator_blocker == "SNAPSHOT_SCOPE_MISMATCH":
        return "SCOPE_MISMATCH_BLOCKED", False, "QUARANTINE_OPERATOR_REVIEW"
    if validator_status == "PASS":
        return "CURRENT_ACCEPTED", True, "ACCEPT_CURRENT_SOURCE"
    if validator_blocker == "SCHEMA_IDENTITY_MISMATCH" or missing_fields:
        return "LEGACY_SCHEMA_DRIFT", False, "RETAIN_LEGACY_REFERENCE_EXCLUDE_FROM_CURRENT_EVIDENCE"
    return "RECONCILIATION_REQUIRED", False, "REGENERATE_WITH_CURRENT_SCHEMA"


def classify_persistent_loop_report(*, root: Path, session_id: str, path: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    raw, read_error = _safe_read_bytes(path)
    source_hash = _sha256_bytes(raw) if raw is not None else None
    loop_report: dict[str, Any] | None = None
    load_error: str | None = read_error
    if raw is not None:
        loop_report, load_error = _safe_json_from_bytes(raw)
    missing_fields = sorted(_current_required_fields() - set(loop_report or {}))
    validator_status = "FAIL"
    validator_message = load_error or "unreadable"
    validator_blocker = "SCHEMA_IDENTITY_MISMATCH" if load_error else None
    if loop_report is not None:
        result = validate_upbit_paper_persistent_loop_report(loop_report)
        validator_status = result.status
        validator_message = result.message
        validator_blocker = result.blocker_code
    unsafe = _unsafe_live_or_order_flag_detected(loop_report)
    classification, usable, action = _classification(
        loop_report=loop_report,
        load_error=load_error,
        validator_status=validator_status,
        validator_blocker=validator_blocker,
        missing_fields=missing_fields,
        unsafe=unsafe,
    )
    return {
        "source_path": _relative_posix(path, root),
        "source_hash": source_hash,
        "loop_id": loop_report.get("loop_id") if isinstance(loop_report, dict) else None,
        "generated_at_utc": loop_report.get("generated_at_utc") if isinstance(loop_report, dict) else None,
        "scope_status": _scope_status(loop_report),
        "current_validator_status": validator_status,
        "current_validator_blocker_code": validator_blocker,
        "current_validator_message": validator_message,
        "classification": classification,
        "evidence_usable_current": usable,
        "recommended_action": action,
        "missing_current_required_fields": missing_fields,
        "runtime_cycle_hashes": _runtime_cycle_hashes(loop_report),
        "unsafe_live_or_order_flag_detected": unsafe,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_stale_loop_reconciliation_report(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    reconciliation_id: str = "upbit-paper-stale-loop-reconciliation",
) -> dict[str, Any]:
    root = Path(root).resolve()
    base = _runtime_base(root, session_id)
    loop_paths = sorted((base / "paper_runtime").glob("*.persistent_loop_report.json")) if base.exists() else []
    items = [classify_persistent_loop_report(root=root, session_id=session_id, path=path) for path in loop_paths]
    current_count = sum(1 for item in items if item["classification"] == "CURRENT_ACCEPTED")
    legacy_count = sum(1 for item in items if item["classification"] == "LEGACY_SCHEMA_DRIFT")
    unsafe_count = sum(1 for item in items if item["classification"] in {"UNSAFE_BLOCKED", "SCOPE_MISMATCH_BLOCKED", "UNREADABLE_OR_CORRUPT"})
    invalid_json_count = sum(1 for item in items if item["classification"] == "UNREADABLE_OR_CORRUPT")
    excluded_count = sum(1 for item in items if not item["evidence_usable_current"])
    runtime_hashes = [runtime_hash for item in items for runtime_hash in item.get("runtime_cycle_hashes", [])]
    duplicate_hash_count = len(runtime_hashes) - len(set(runtime_hashes))
    current_evidence_usable_count = sum(1 for item in items if item["evidence_usable_current"])
    legacy_reference_retained_count = legacy_count
    status = "PASS" if excluded_count == 0 and duplicate_hash_count == 0 and current_count > 0 else "BLOCKED"
    primary = None if status == "PASS" else STALE_LOOP_BLOCKER_CODE
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_RECONCILIATION_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "reconciliation_id": reconciliation_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": "paper_runtime_reconciliation_truth",
        "reconciliation_role": STALE_LOOP_RECONCILIATION_ROLE,
        "evidence_use_policy": CURRENT_EVIDENCE_USE_POLICY,
        "source_loop_report_count": len(loop_paths),
        "current_accepted_count": current_count,
        "legacy_schema_drift_count": legacy_count,
        "unsafe_blocked_count": unsafe_count,
        "invalid_json_count": invalid_json_count,
        "duplicate_runtime_cycle_hash_count": duplicate_hash_count,
        "current_evidence_usable_count": current_evidence_usable_count,
        "legacy_reference_retained_count": legacy_reference_retained_count,
        "excluded_from_current_evidence_count": excluded_count,
        "reconciliation_status": status,
        "primary_blocker_code": primary,
        "items": items,
        "delete_performed": False,
        "safe_delete_allowed": False,
        "operator_next_action": "Regenerate stale PAPER loop reports with the current schema or retain them as legacy references excluded from current evidence.",
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
        "reconciliation_hash": "",
    }
    report["reconciliation_hash"] = stale_loop_reconciliation_hash(report)
    return report


def write_upbit_paper_stale_loop_reconciliation_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(root, str(report["session_id"])) / "paper_runtime" / "upbit_paper_stale_loop_reconciliation_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_reconciliation_report(report: dict[str, Any]) -> UpbitPaperStaleLoopReconciliationValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "reconciliation_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "reconciliation_role",
        "evidence_use_policy",
        "source_loop_report_count",
        "current_accepted_count",
        "legacy_schema_drift_count",
        "unsafe_blocked_count",
        "invalid_json_count",
        "duplicate_runtime_cycle_hash_count",
        "current_evidence_usable_count",
        "legacy_reference_retained_count",
        "excluded_from_current_evidence_count",
        "reconciliation_status",
        "primary_blocker_code",
        "items",
        "delete_performed",
        "safe_delete_allowed",
        "operator_next_action",
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
        "reconciliation_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", f"stale loop reconciliation report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_RECONCILIATION_SCHEMA_ID:
        return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", "stale loop reconciliation schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("reconciliation_hash") != stale_loop_reconciliation_hash(report):
        return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", "stale loop reconciliation hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopReconciliationValidationResult("BLOCKED", "stale loop reconciliation scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != "paper_runtime_reconciliation_truth" or report.get("reconciliation_role") != STALE_LOOP_RECONCILIATION_ROLE:
        return UpbitPaperStaleLoopReconciliationValidationResult("BLOCKED", "stale loop reconciliation cannot claim execution, dashboard, or live truth", "LIVE_FINAL_GUARD_FAILED")
    if report.get("evidence_use_policy") != CURRENT_EVIDENCE_USE_POLICY:
        return UpbitPaperStaleLoopReconciliationValidationResult("BLOCKED", "stale loop reconciliation evidence policy must exclude non-current reports", STALE_LOOP_BLOCKER_CODE)
    forbidden_fields = (
        "delete_performed",
        "safe_delete_allowed",
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
    if any(report.get(field) for field in forbidden_fields):
        return UpbitPaperStaleLoopReconciliationValidationResult("BLOCKED", "stale loop reconciliation attempted deletion, live, order, promotion, long-run, or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    items = report.get("items")
    if not isinstance(items, list) or report.get("source_loop_report_count") != len(items):
        return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", "stale loop reconciliation item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    current_count = 0
    legacy_count = 0
    unsafe_count = 0
    excluded_count = 0
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", "stale loop reconciliation item must be an object", "SCHEMA_IDENTITY_MISMATCH")
        item_required = {
            "source_path",
            "source_hash",
            "loop_id",
            "generated_at_utc",
            "scope_status",
            "current_validator_status",
            "current_validator_blocker_code",
            "current_validator_message",
            "classification",
            "evidence_usable_current",
            "recommended_action",
            "missing_current_required_fields",
            "runtime_cycle_hashes",
            "unsafe_live_or_order_flag_detected",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", f"stale loop reconciliation item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH")
        if not isinstance(item["source_path"], str) or not _artifact_path_allowed(item["source_path"], str(report.get("session_id"))):
            return UpbitPaperStaleLoopReconciliationValidationResult("BLOCKED", "stale loop reconciliation source path escaped UPBIT PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not isinstance(item.get("runtime_cycle_hashes"), list) or any(not isinstance(value, str) for value in item.get("runtime_cycle_hashes")):
            return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", "stale loop reconciliation runtime cycle hashes must be an array of strings", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("live_order_ready") or item.get("live_order_allowed") or item.get("can_live_trade") or item.get("scale_up_allowed"):
            return UpbitPaperStaleLoopReconciliationValidationResult("BLOCKED", "stale loop reconciliation item created live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
        classification = item.get("classification")
        usable = item.get("evidence_usable_current")
        if classification == "CURRENT_ACCEPTED":
            current_count += 1
            if usable is not True or item.get("recommended_action") != "ACCEPT_CURRENT_SOURCE":
                return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", "current accepted item must be usable and accepted", "SCHEMA_IDENTITY_MISMATCH")
        else:
            excluded_count += 1
            if usable:
                return UpbitPaperStaleLoopReconciliationValidationResult("BLOCKED", "non-current loop report was usable as current evidence", STALE_LOOP_BLOCKER_CODE)
        if classification == "LEGACY_SCHEMA_DRIFT":
            legacy_count += 1
            if not item.get("missing_current_required_fields") and item.get("current_validator_blocker_code") != "SCHEMA_IDENTITY_MISMATCH":
                return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", "legacy schema drift item lacks schema-drift evidence", "SCHEMA_IDENTITY_MISMATCH")
            if item.get("recommended_action") != "RETAIN_LEGACY_REFERENCE_EXCLUDE_FROM_CURRENT_EVIDENCE":
                return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", "legacy schema drift action must retain and exclude", "SCHEMA_IDENTITY_MISMATCH")
        if classification in {"UNSAFE_BLOCKED", "SCOPE_MISMATCH_BLOCKED", "UNREADABLE_OR_CORRUPT"}:
            unsafe_count += 1
            if item.get("recommended_action") != "QUARANTINE_OPERATOR_REVIEW":
                return UpbitPaperStaleLoopReconciliationValidationResult("BLOCKED", "unsafe item must require operator review", "LIVE_FINAL_GUARD_FAILED")
    invalid_json_count = sum(1 for item in items if item.get("classification") == "UNREADABLE_OR_CORRUPT")
    runtime_hashes = [runtime_hash for item in items for runtime_hash in item.get("runtime_cycle_hashes", [])]
    duplicate_hash_count = len(runtime_hashes) - len(set(runtime_hashes))
    if (
        report.get("current_accepted_count") != current_count
        or report.get("legacy_schema_drift_count") != legacy_count
        or report.get("unsafe_blocked_count") != unsafe_count
        or report.get("invalid_json_count") != invalid_json_count
        or report.get("duplicate_runtime_cycle_hash_count") != duplicate_hash_count
        or report.get("current_evidence_usable_count") != current_count
        or report.get("legacy_reference_retained_count") != legacy_count
        or report.get("excluded_from_current_evidence_count") != excluded_count
    ):
        return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", "stale loop reconciliation rollup count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if duplicate_hash_count:
        if report.get("reconciliation_status") != "BLOCKED" or report.get("primary_blocker_code") != STALE_LOOP_BLOCKER_CODE:
            return UpbitPaperStaleLoopReconciliationValidationResult("BLOCKED", "duplicate runtime cycle hashes must block stale loop reconciliation", STALE_LOOP_BLOCKER_CODE)
    if excluded_count:
        if report.get("reconciliation_status") != "BLOCKED" or report.get("primary_blocker_code") != STALE_LOOP_BLOCKER_CODE:
            return UpbitPaperStaleLoopReconciliationValidationResult("BLOCKED", "excluded stale loop reports must block reconciliation", STALE_LOOP_BLOCKER_CODE)
    if not duplicate_hash_count and not excluded_count and (report.get("reconciliation_status") != "PASS" or report.get("primary_blocker_code") is not None):
        return UpbitPaperStaleLoopReconciliationValidationResult("FAIL", "clean reconciliation status mismatch", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperStaleLoopReconciliationValidationResult("PASS", "Upbit PAPER stale loop reconciliation excludes stale sources and remains live-blocked", None)
