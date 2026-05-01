from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_persistent_loop import (
    BOUNDED_LOOP_RUNTIME_EVIDENCE_ROLE,
    LONG_RUN_EVIDENCE_BLOCKER_CODE,
    LONG_RUN_EVIDENCE_NEXT_ACTION,
    upbit_paper_persistent_loop_hash,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_execution_guard import (
    validate_upbit_paper_stale_loop_execution_guard,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_safe_regeneration_executor_report.v1"
)
SAFE_REGENERATION_EXECUTOR_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_SAFE_REGENERATION_EXECUTOR_CREATE_NEW_ONLY_NOT_LONG_RUN_EVIDENCE"
)
PERSISTENT_LOOP_REQUIRED_FIELDS = {
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
    "preflight_existing_runtime_state_detected",
    "preflight_recovery_guard_status",
    "preflight_recovery_guard_hash",
    "preflight_recovery_guard_primary_blocker_code",
    "preflight_runtime_recovery_guard_path",
    "preflight_paper_runtime_resume_allowed",
    "current_evidence_write_allowed",
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
SAFE_REGENERATED_BLOCKER_CODES = {
    "DATA_UNAVAILABLE",
    "MEASUREMENT_MISSING",
    "RECONCILIATION_REQUIRED",
}


@dataclass(frozen=True)
class UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def stale_loop_safe_regeneration_executor_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("executor_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return root.resolve().joinpath(*parts)


def _safe_file_hash(path: Path) -> str | None:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        return None


def _safe_load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "STALE_LOOP_SOURCE_MISSING"
    except json.JSONDecodeError:
        return None, "STALE_LOOP_SOURCE_UNREADABLE"
    if not isinstance(value, dict):
        return None, "SCHEMA_IDENTITY_MISMATCH"
    return value, None


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_rollup_hash(root: Path, source: dict[str, Any]) -> str | None:
    if source.get("paper_ledger_rollup_hash"):
        return str(source["paper_ledger_rollup_hash"])
    rollup_path = source.get("paper_ledger_rollup_path")
    if not isinstance(rollup_path, str) or not rollup_path:
        return None
    rollup, error = _safe_load_json(_rooted(root, rollup_path))
    if error or not isinstance(rollup, dict):
        return None
    rollup_hash = rollup.get("rollup_hash")
    return str(rollup_hash) if isinstance(rollup_hash, str) and rollup_hash else None


def _normalized_persistent_loop_report(
    *,
    root: Path,
    source: dict[str, Any],
    replacement_loop_id: str,
) -> dict[str, Any]:
    report = {key: source[key] for key in PERSISTENT_LOOP_REQUIRED_FIELDS if key in source}
    session_id = str(source.get("session_id") or "mvp1_upbit_paper_launcher")
    recovery_fields_missing = any(
        field not in source
        for field in (
            "recovery_guard_status",
            "recovery_guard_hash",
            "recovery_guard_primary_blocker_code",
            "runtime_recovery_guard_path",
            "paper_runtime_resume_allowed",
            "partial_write_recovery_required",
        )
    )
    rollup_hash = _load_rollup_hash(root, source)
    ledger_fields_missing = (
        any(
            field not in source
            for field in (
                "paper_ledger_rollup_status",
                "paper_ledger_rollup_primary_blocker_code",
                "paper_ledger_rollup_path",
            )
        )
        or not (source.get("paper_ledger_rollup_hash") or rollup_hash)
    )
    report["schema_id"] = "trader1.upbit_paper_persistent_loop_report.v1"
    report["generated_at_utc"] = utc_now()
    report["project_id"] = "TRADER_1"
    report["loop_id"] = replacement_loop_id
    report["exchange"] = "UPBIT"
    report["market_type"] = "KRW_SPOT"
    report["mode"] = "PAPER"
    report["session_id"] = session_id
    report.setdefault("symbol", "KRW-BTC")
    report.setdefault("loop_mode", "BOUNDED_PUBLIC_DATA_PAPER_LOOP")
    report.setdefault("cycle_results", [])
    report.setdefault("requested_cycle_count", len(report["cycle_results"]) or 1)
    report.setdefault("completed_cycle_count", len(report["cycle_results"]))
    report.setdefault("max_cycle_count", max(1, int(report["requested_cycle_count"])))
    report.setdefault("blockers", [])
    report.setdefault("preflight_existing_runtime_state_detected", False)
    report.setdefault("preflight_recovery_guard_status", "SKIPPED")
    report.setdefault("preflight_recovery_guard_hash", None)
    report.setdefault("preflight_recovery_guard_primary_blocker_code", None)
    report.setdefault("preflight_runtime_recovery_guard_path", None)
    report.setdefault("preflight_paper_runtime_resume_allowed", True)
    report.setdefault("current_evidence_write_allowed", True)
    report["runtime_evidence_role"] = BOUNDED_LOOP_RUNTIME_EVIDENCE_ROLE
    report["long_run_evidence_eligible"] = False
    report["long_run_blocker_code"] = LONG_RUN_EVIDENCE_BLOCKER_CODE
    report["long_run_next_action"] = LONG_RUN_EVIDENCE_NEXT_ACTION
    report["promotion_eligible"] = False
    report["data_source_policy"] = "PUBLIC_OR_STATIC_FIXTURE_ONLY"
    report["credential_load_attempted"] = False
    report["private_endpoint_called"] = False
    report["order_endpoint_called"] = False
    report["order_adapter_called"] = False
    report["live_key_loaded"] = False
    report["live_order_ready"] = False
    report["live_order_allowed"] = False
    report["can_live_trade"] = False
    report["scale_up_allowed"] = False
    if rollup_hash:
        report["paper_ledger_rollup_hash"] = rollup_hash
    if recovery_fields_missing:
        report["recovery_guard_status"] = "BLOCKED"
        report["recovery_guard_hash"] = _sha256_json(
            {
                "source_loop_id": source.get("loop_id"),
                "replacement_loop_id": replacement_loop_id,
                "missing": "recovery_guard",
            }
        )
        report["recovery_guard_primary_blocker_code"] = "RECONCILIATION_REQUIRED"
        report["runtime_recovery_guard_path"] = (
            f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
            f"{replacement_loop_id}.synthetic_recovery_guard_missing.json"
        )
        report["paper_runtime_resume_allowed"] = False
        report["partial_write_recovery_required"] = True
    if ledger_fields_missing or not report.get("paper_ledger_rollup_hash"):
        report["paper_ledger_rollup_status"] = "BLOCKED"
        report["paper_ledger_rollup_hash"] = report.get("paper_ledger_rollup_hash") or _sha256_json(
            {
                "source_loop_id": source.get("loop_id"),
                "replacement_loop_id": replacement_loop_id,
                "missing": "paper_ledger_rollup",
            }
        )
        report["paper_ledger_rollup_primary_blocker_code"] = "RECONCILIATION_REQUIRED"
        report["paper_ledger_rollup_path"] = (
            f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
            f"{replacement_loop_id}.synthetic_ledger_rollup_missing.json"
        )
    if recovery_fields_missing or ledger_fields_missing:
        report["loop_status"] = "BLOCKED"
        report["primary_blocker_code"] = "RECONCILIATION_REQUIRED"
        report["blockers"] = [
            {
                "code": "RECONCILIATION_REQUIRED",
                "severity": "HIGH",
                "message": "legacy persistent loop report was schema-repaired but still requires reconciliation before evidence use",
            }
        ]
    report["loop_hash"] = ""
    report["loop_hash"] = upbit_paper_persistent_loop_hash(report)
    return report


def _build_executor_item(*, root: Path, item: dict[str, Any]) -> dict[str, Any]:
    source_path = str(item.get("source_path"))
    replacement_path = str(item.get("planned_replacement_path"))
    source_absolute = _rooted(root, source_path)
    replacement_absolute = _rooted(root, replacement_path)
    source_hash_expected = item.get("source_hash_expected")
    source_hash_actual = _safe_file_hash(source_absolute)
    replacement_existed_before = replacement_absolute.exists()
    source, source_error = _safe_load_json(source_absolute)
    blocker_code = None
    regenerated: dict[str, Any] | None = None
    validation_status = "NOT_RUN"
    validation_message = "not run"
    replacement_written = False

    if item.get("guard_item_status") != "PASS":
        blocker_code = item.get("blocker_code") or "STALE_LOOP_REGENERATION_REQUIRED"
    elif source_hash_expected and source_hash_actual != source_hash_expected:
        blocker_code = "STALE_LOOP_SOURCE_HASH_MISMATCH"
    elif replacement_existed_before:
        blocker_code = "STALE_LOOP_REPLACEMENT_ALREADY_EXISTS"
    elif source_error:
        blocker_code = source_error
    elif not isinstance(item.get("planned_replacement_loop_id"), str):
        blocker_code = "SCHEMA_IDENTITY_MISMATCH"
    elif not isinstance(source, dict):
        blocker_code = "SCHEMA_IDENTITY_MISMATCH"
    else:
        regenerated = _normalized_persistent_loop_report(
            root=root,
            source=source,
            replacement_loop_id=str(item["planned_replacement_loop_id"]),
        )
        validation_result = validate_upbit_paper_persistent_loop_report(regenerated)
        validation_status = validation_result.status
        validation_message = validation_result.message
        if validation_result.status == "BLOCKED" and validation_result.blocker_code in SAFE_REGENERATED_BLOCKER_CODES:
            durable_atomic_write_json(replacement_absolute, regenerated)
            replacement_written = True
        elif validation_result.status != "PASS":
            blocker_code = validation_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH"
        else:
            durable_atomic_write_json(replacement_absolute, regenerated)
            replacement_written = True

    replacement_exists_after = replacement_absolute.exists()
    return {
        "source_path": source_path,
        "source_hash_expected": source_hash_expected,
        "source_hash_actual": source_hash_actual,
        "source_hash_match": bool(source_hash_expected and source_hash_actual == source_hash_expected),
        "source_retained": source_absolute.exists(),
        "planned_replacement_loop_id": item.get("planned_replacement_loop_id"),
        "planned_replacement_path": replacement_path,
        "replacement_write_mode": "CREATE_NEW_ONLY",
        "replacement_existed_before": replacement_existed_before,
        "replacement_exists_after": replacement_exists_after,
        "replacement_written": replacement_written,
        "regenerated_loop_hash": regenerated.get("loop_hash") if isinstance(regenerated, dict) else None,
        "persistent_loop_validation_status": validation_status,
        "persistent_loop_validation_message": validation_message,
        "execution_item_status": "PASS" if blocker_code is None and replacement_written else "BLOCKED",
        "blocker_code": blocker_code,
        "delete_source_allowed": False,
        "overwrite_source_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_stale_loop_safe_regeneration_executor_report(
    *,
    root: Path,
    guard: dict[str, Any],
    executor_id: str = "upbit-paper-stale-loop-safe-regeneration-executor",
) -> dict[str, Any]:
    root = Path(root).resolve()
    guard_result = validate_upbit_paper_stale_loop_execution_guard(guard)
    session_id = str(guard.get("session_id", "UNKNOWN"))
    blockers: list[str] = []
    items: list[dict[str, Any]] = []
    if guard_result.status != "PASS":
        blockers.append(guard_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    if guard.get("guard_status") != "PASS" or guard.get("paper_regeneration_preconditions_passed") is not True:
        blockers.append(guard.get("primary_blocker_code") or "STALE_LOOP_REGENERATION_REQUIRED")
    if guard.get("execution_performed") or guard.get("actual_regeneration_performed"):
        blockers.append("LIVE_FINAL_GUARD_FAILED")
    if guard.get("actual_long_run_evidence_created") or guard.get("long_run_evidence_eligible") or guard.get("promotion_eligible"):
        blockers.append("LIVE_FINAL_GUARD_FAILED")
    if guard.get("live_order_ready") or guard.get("live_order_allowed") or guard.get("can_live_trade") or guard.get("scale_up_allowed"):
        blockers.append("LIVE_FINAL_GUARD_FAILED")

    if not blockers:
        items = [_build_executor_item(root=root, item=item) for item in guard.get("items", []) if isinstance(item, dict)]
        blockers.extend(str(item["blocker_code"]) for item in items if item.get("blocker_code"))

    unique_blockers = sorted({blocker for blocker in blockers if blocker})
    regenerated_count = sum(1 for item in items if item.get("replacement_written"))
    skipped_count = max(0, int(guard.get("planned_regeneration_item_count") or 0) - regenerated_count)
    validation_fail_count = sum(1 for item in items if item.get("persistent_loop_validation_status") not in {"PASS", "NOT_RUN"})
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "executor_id": executor_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "executor_role": SAFE_REGENERATION_EXECUTOR_ROLE,
        "source_guard_hash": guard.get("guard_hash"),
        "source_guard_status": guard.get("guard_status"),
        "planned_regeneration_item_count": int(guard.get("planned_regeneration_item_count") or 0),
        "regenerated_item_count": regenerated_count,
        "skipped_item_count": skipped_count,
        "validation_fail_count": validation_fail_count,
        "replacement_existing_count": sum(1 for item in items if item.get("replacement_existed_before")),
        "source_hash_mismatch_count": sum(1 for item in items if not item.get("source_hash_match")),
        "executor_status": "PASS" if not unique_blockers and regenerated_count == int(guard.get("planned_regeneration_item_count") or 0) else "BLOCKED",
        "primary_blocker_code": unique_blockers[0] if unique_blockers else None,
        "blocker_codes": unique_blockers,
        "source_retention_required": True,
        "replacement_write_mode": "CREATE_NEW_ONLY",
        "items": items,
        "delete_source_allowed": False,
        "overwrite_source_allowed": False,
        "actual_regeneration_performed": regenerated_count > 0 and not unique_blockers,
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
        "executor_hash": "",
    }
    report["executor_hash"] = stale_loop_safe_regeneration_executor_hash(report)
    return report


def write_upbit_paper_stale_loop_safe_regeneration_executor_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(root, str(report["session_id"])) / "paper_runtime" / "upbit_paper_stale_loop_safe_regeneration_executor_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_safe_regeneration_executor_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "executor_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "executor_role",
        "source_guard_hash",
        "source_guard_status",
        "planned_regeneration_item_count",
        "regenerated_item_count",
        "skipped_item_count",
        "validation_fail_count",
        "replacement_existing_count",
        "source_hash_mismatch_count",
        "executor_status",
        "primary_blocker_code",
        "blocker_codes",
        "source_retention_required",
        "replacement_write_mode",
        "items",
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
        "executor_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", f"safe regeneration executor missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR_SCHEMA_ID:
        return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", "safe regeneration executor schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("executor_hash") != stale_loop_safe_regeneration_executor_hash(report):
        return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", "safe regeneration executor hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("BLOCKED", "safe regeneration executor scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("executor_role") != SAFE_REGENERATION_EXECUTOR_ROLE:
        return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("BLOCKED", "safe regeneration executor role mismatch", "LIVE_FINAL_GUARD_FAILED")
    forbidden_fields = (
        "delete_source_allowed",
        "overwrite_source_allowed",
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
        return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("BLOCKED", "safe regeneration executor created forbidden live/order/long-run/promotion/scale behavior", "LIVE_FINAL_GUARD_FAILED")
    if report.get("source_retention_required") is not True or report.get("replacement_write_mode") != "CREATE_NEW_ONLY":
        return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("BLOCKED", "safe regeneration executor must retain sources and create new replacements only", "LIVE_FINAL_GUARD_FAILED")
    items = report.get("items")
    if not isinstance(items, list):
        return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", "safe regeneration executor items must be an array", "SCHEMA_IDENTITY_MISMATCH")
    regenerated_count = 0
    item_level_skipped_count = 0
    validation_fail_count = 0
    replacement_existing_count = 0
    source_hash_mismatch_count = 0
    item_blockers: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", "safe regeneration executor item must be object", "SCHEMA_IDENTITY_MISMATCH")
        item_required = {
            "source_path",
            "source_hash_expected",
            "source_hash_actual",
            "source_hash_match",
            "source_retained",
            "planned_replacement_loop_id",
            "planned_replacement_path",
            "replacement_write_mode",
            "replacement_existed_before",
            "replacement_exists_after",
            "replacement_written",
            "regenerated_loop_hash",
            "persistent_loop_validation_status",
            "persistent_loop_validation_message",
            "execution_item_status",
            "blocker_code",
            "delete_source_allowed",
            "overwrite_source_allowed",
            "actual_long_run_evidence_created",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", f"safe regeneration executor item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("delete_source_allowed") or item.get("overwrite_source_allowed") or item.get("actual_long_run_evidence_created"):
            return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("BLOCKED", "safe regeneration executor item created delete, overwrite, or long-run evidence", "LIVE_FINAL_GUARD_FAILED")
        if item.get("live_order_ready") or item.get("live_order_allowed") or item.get("can_live_trade") or item.get("scale_up_allowed"):
            return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("BLOCKED", "safe regeneration executor item created live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
        if item.get("replacement_write_mode") != "CREATE_NEW_ONLY" or item.get("source_retained") is not True:
            return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("BLOCKED", "safe regeneration executor item violated source retention or create-new write mode", "LIVE_FINAL_GUARD_FAILED")
        if item.get("replacement_written"):
            regenerated_count += 1
            if item.get("execution_item_status") != "PASS" or item.get("persistent_loop_validation_status") not in {"PASS", "BLOCKED"}:
                return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", "written replacement item did not validate as current-schema PASS or BLOCKED", "SCHEMA_IDENTITY_MISMATCH")
            if not item.get("regenerated_loop_hash"):
                return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", "written replacement item missing regenerated loop hash", "SCHEMA_IDENTITY_MISMATCH")
        else:
            item_level_skipped_count += 1
            if not item.get("blocker_code"):
                return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("BLOCKED", "skipped replacement item must expose blocker", "STALE_LOOP_REGENERATION_REQUIRED")
        if item.get("replacement_existed_before"):
            replacement_existing_count += 1
            item_blockers.append("STALE_LOOP_REPLACEMENT_ALREADY_EXISTS")
        if not item.get("source_hash_match"):
            source_hash_mismatch_count += 1
            item_blockers.append("STALE_LOOP_SOURCE_HASH_MISMATCH")
        if item.get("persistent_loop_validation_status") not in {"PASS", "NOT_RUN"}:
            validation_fail_count += 1
        if item.get("blocker_code"):
            item_blockers.append(str(item["blocker_code"]))
    if (
        report.get("regenerated_item_count") != regenerated_count
        or report.get("skipped_item_count") != max(item_level_skipped_count, int(report.get("planned_regeneration_item_count") or 0) - regenerated_count)
        or report.get("validation_fail_count") != validation_fail_count
        or report.get("replacement_existing_count") != replacement_existing_count
        or report.get("source_hash_mismatch_count") != source_hash_mismatch_count
    ):
        return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", "safe regeneration executor rollup count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    unique_blockers = sorted({str(blocker) for blocker in [*item_blockers, *report.get("blocker_codes", [])] if blocker})
    if unique_blockers:
        if report.get("executor_status") != "BLOCKED" or report.get("primary_blocker_code") is None or report.get("actual_regeneration_performed"):
            return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("BLOCKED", "blocked safe regeneration executor cannot claim successful execution", unique_blockers[0])
    else:
        if report.get("executor_status") != "PASS" or report.get("primary_blocker_code") is not None:
            return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", "clean safe regeneration executor status mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("actual_regeneration_performed") is not (regenerated_count > 0):
            return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("FAIL", "actual regeneration flag does not match regenerated count", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperStaleLoopSafeRegenerationExecutorValidationResult("PASS", "Upbit PAPER stale loop safe regeneration executor is create-new-only, source-retaining, and live-blocked", None)
