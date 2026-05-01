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
from trader1.runtime.paper.upbit_paper_stale_loop_safe_regeneration_executor import (
    validate_upbit_paper_stale_loop_safe_regeneration_executor_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_RECONCILIATION_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_post_regeneration_reconciliation_report.v1"
)
POST_REGENERATION_RECONCILIATION_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_POST_REGENERATION_RECONCILIATION_NOT_LONG_RUN_EVIDENCE"
)
POST_REGENERATION_EVIDENCE_USE_POLICY = (
    "PASS_REGENERATED_CURRENT_SCHEMA_ONLY_EXCLUDE_SOURCES_AND_BLOCKED_REPAIRS"
)
POST_REGENERATION_RECONCILIATION_BLOCKER_CODE = (
    "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED"
)


@dataclass(frozen=True)
class UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def stale_loop_post_regeneration_reconciliation_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("post_reconciliation_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return root.resolve().joinpath(*parts)


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return path.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "live" not in parts


def _safe_file_hash(path: Path) -> str | None:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        return None


def _safe_load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
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
    return value, None


def _unsafe_live_or_order_flag_detected(report: dict[str, Any] | None) -> bool:
    if not isinstance(report, dict):
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
        if report.get(field):
            return True
    for item in report.get("cycle_results") or []:
        if isinstance(item, dict) and (
            item.get("live_order_ready")
            or item.get("live_order_allowed")
            or item.get("can_live_trade")
            or item.get("scale_up_allowed")
        ):
            return True
    return False


def _runtime_cycle_hashes(report: dict[str, Any] | None) -> list[str]:
    if not isinstance(report, dict):
        return []
    return [
        str(item["runtime_cycle_hash"])
        for item in report.get("cycle_results") or []
        if isinstance(item, dict) and isinstance(item.get("runtime_cycle_hash"), str)
    ]


def _classify_replacement(
    *,
    source_hash_match: bool,
    source_retained: bool,
    replacement_exists: bool,
    replacement_load_error: str | None,
    replacement_loop_hash_match: bool,
    replacement_validation_status: str,
    replacement_validation_blocker_code: str | None,
    unsafe: bool,
    executor_item_status: str,
    replacement_written: bool,
) -> tuple[str, bool, str, str | None]:
    if unsafe:
        return "UNSAFE_BLOCKED", False, "QUARANTINE_OPERATOR_REVIEW", "LIVE_FINAL_GUARD_FAILED"
    if executor_item_status != "PASS" or not replacement_written:
        return "EXECUTOR_ITEM_BLOCKED", False, "REPLAY_SAFE_REGENERATION_EXECUTOR", "STALE_LOOP_REGENERATION_REQUIRED"
    if not source_retained or not source_hash_match:
        return "SOURCE_RETENTION_MISMATCH_BLOCKED", False, "QUARANTINE_OPERATOR_REVIEW", "STALE_LOOP_SOURCE_HASH_MISMATCH"
    if not replacement_exists or replacement_load_error or not replacement_loop_hash_match:
        return "REPLACEMENT_MISSING_OR_MISMATCH", False, "QUARANTINE_OPERATOR_REVIEW", "STALE_LOOP_REPLACEMENT_MISMATCH"
    if replacement_validation_status == "PASS":
        return "REGENERATED_CURRENT_ACCEPTED", True, "ACCEPT_REGENERATED_CURRENT_SOURCE", None
    if replacement_validation_status == "BLOCKED" and replacement_validation_blocker_code == "RECONCILIATION_REQUIRED":
        return (
            "REGENERATED_CURRENT_BLOCKED_RECONCILIATION_REQUIRED",
            False,
            "RECONCILE_LEDGER_AND_RECOVERY_BEFORE_EVIDENCE_USE",
            POST_REGENERATION_RECONCILIATION_BLOCKER_CODE,
        )
    return "REGENERATED_CURRENT_INVALID", False, "QUARANTINE_OPERATOR_REVIEW", "SCHEMA_IDENTITY_MISMATCH"


def _build_post_item(*, root: Path, session_id: str, executor_item: dict[str, Any]) -> dict[str, Any]:
    source_path = str(executor_item.get("source_path") or "")
    replacement_path = str(executor_item.get("planned_replacement_path") or "")
    source_absolute = _rooted(root, source_path)
    replacement_absolute = _rooted(root, replacement_path)
    source_hash_expected = executor_item.get("source_hash_expected")
    source_hash_actual = _safe_file_hash(source_absolute)
    replacement, replacement_load_error = _safe_load_json(replacement_absolute)
    replacement_validation_status = "FAIL"
    replacement_validation_message = replacement_load_error or "not loaded"
    replacement_validation_blocker_code = "SCHEMA_IDENTITY_MISMATCH" if replacement_load_error else None
    replacement_loop_hash = None
    if replacement is not None:
        replacement_loop_hash = replacement.get("loop_hash") if isinstance(replacement.get("loop_hash"), str) else None
        validation = validate_upbit_paper_persistent_loop_report(replacement)
        replacement_validation_status = validation.status
        replacement_validation_message = validation.message
        replacement_validation_blocker_code = validation.blocker_code

    replacement_loop_hash_expected = executor_item.get("regenerated_loop_hash")
    source_retained = source_absolute.exists()
    source_hash_match = bool(source_hash_expected and source_hash_actual == source_hash_expected)
    replacement_exists = replacement_absolute.exists()
    replacement_loop_hash_match = bool(replacement_loop_hash_expected and replacement_loop_hash == replacement_loop_hash_expected)
    source_path_allowed = _artifact_path_allowed(source_path, session_id)
    replacement_path_allowed = _artifact_path_allowed(replacement_path, session_id)
    unsafe = _unsafe_live_or_order_flag_detected(replacement)
    classification, usable, action, blocker_code = _classify_replacement(
        source_hash_match=source_hash_match,
        source_retained=source_retained,
        replacement_exists=replacement_exists,
        replacement_load_error=replacement_load_error,
        replacement_loop_hash_match=replacement_loop_hash_match,
        replacement_validation_status=replacement_validation_status,
        replacement_validation_blocker_code=replacement_validation_blocker_code,
        unsafe=unsafe,
        executor_item_status=str(executor_item.get("execution_item_status")),
        replacement_written=executor_item.get("replacement_written") is True,
    )
    if not source_path_allowed or not replacement_path_allowed:
        classification = "SOURCE_RETENTION_MISMATCH_BLOCKED"
        usable = False
        action = "QUARANTINE_OPERATOR_REVIEW"
        blocker_code = "SNAPSHOT_SCOPE_MISMATCH"
    return {
        "source_path": source_path,
        "source_hash_expected": source_hash_expected,
        "source_hash_actual": source_hash_actual,
        "source_hash_match": source_hash_match,
        "source_retained": source_retained,
        "source_path_scope_status": "MATCH" if source_path_allowed else "MISMATCH",
        "replacement_path": replacement_path,
        "replacement_path_scope_status": "MATCH" if replacement_path_allowed else "MISMATCH",
        "replacement_exists": replacement_exists,
        "replacement_loop_id": replacement.get("loop_id") if isinstance(replacement, dict) else None,
        "replacement_loop_hash_expected": replacement_loop_hash_expected,
        "replacement_loop_hash_actual": replacement_loop_hash,
        "replacement_loop_hash_match": replacement_loop_hash_match,
        "replacement_validation_status": replacement_validation_status,
        "replacement_validation_blocker_code": replacement_validation_blocker_code,
        "replacement_validation_message": replacement_validation_message,
        "classification": classification,
        "evidence_usable_current": usable,
        "recommended_action": action,
        "item_blocker_code": blocker_code,
        "runtime_cycle_hashes": _runtime_cycle_hashes(replacement),
        "unsafe_live_or_order_flag_detected": unsafe,
        "source_excluded_from_current_evidence": True,
        "delete_source_allowed": False,
        "overwrite_source_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
    *,
    root: Path,
    executor_report: dict[str, Any],
    reconciliation_id: str = "upbit-paper-stale-loop-post-regeneration-reconciliation",
) -> dict[str, Any]:
    root = Path(root).resolve()
    executor_result = validate_upbit_paper_stale_loop_safe_regeneration_executor_report(executor_report)
    session_id = str(executor_report.get("session_id", "UNKNOWN"))
    planned_paths = {
        str(item.get("planned_replacement_path"))
        for item in executor_report.get("items", [])
        if isinstance(item, dict) and isinstance(item.get("planned_replacement_path"), str)
    }
    base = _runtime_base(root, session_id)
    unpaired_paths = []
    if base.exists():
        for path in sorted((base / "paper_runtime").glob("*-regenerated-current-schema.persistent_loop_report.json")):
            rel_path = _relative_posix(path, root)
            if rel_path not in planned_paths:
                unpaired_paths.append(rel_path)
    items = []
    if executor_result.status == "PASS":
        items = [
            _build_post_item(root=root, session_id=session_id, executor_item=item)
            for item in executor_report.get("items", [])
            if isinstance(item, dict)
        ]
    accepted_count = sum(1 for item in items if item["classification"] == "REGENERATED_CURRENT_ACCEPTED")
    blocked_reconciliation_count = sum(
        1 for item in items if item["classification"] == "REGENERATED_CURRENT_BLOCKED_RECONCILIATION_REQUIRED"
    )
    invalid_count = sum(
        1
        for item in items
        if item["classification"]
        in {
            "REGENERATED_CURRENT_INVALID",
            "REPLACEMENT_MISSING_OR_MISMATCH",
            "SOURCE_RETENTION_MISMATCH_BLOCKED",
            "EXECUTOR_ITEM_BLOCKED",
            "UNSAFE_BLOCKED",
        }
    )
    evidence_usable_count = sum(1 for item in items if item["evidence_usable_current"])
    excluded_count = len(items) - evidence_usable_count
    usable_hashes = [runtime_hash for item in items if item["evidence_usable_current"] for runtime_hash in item["runtime_cycle_hashes"]]
    duplicate_usable_hash_count = len(usable_hashes) - len(set(usable_hashes))
    source_hash_mismatch_count = sum(1 for item in items if not item["source_hash_match"])
    replacement_hash_mismatch_count = sum(1 for item in items if not item["replacement_loop_hash_match"])
    source_retained_count = sum(1 for item in items if item["source_retained"])
    replacement_found_count = sum(1 for item in items if item["replacement_exists"])
    blockers: list[str] = []
    if executor_result.status != "PASS":
        blockers.append(executor_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    if executor_report.get("executor_status") != "PASS":
        blockers.append(executor_report.get("primary_blocker_code") or "STALE_LOOP_REGENERATION_REQUIRED")
    if source_hash_mismatch_count:
        blockers.append("STALE_LOOP_SOURCE_HASH_MISMATCH")
    if replacement_hash_mismatch_count:
        blockers.append("STALE_LOOP_REPLACEMENT_MISMATCH")
    if invalid_count:
        blockers.append("SCHEMA_IDENTITY_MISMATCH")
    if blocked_reconciliation_count:
        blockers.append(POST_REGENERATION_RECONCILIATION_BLOCKER_CODE)
    if duplicate_usable_hash_count:
        blockers.append("DUPLICATE_RUNTIME_CYCLE_HASH")
    if unpaired_paths:
        blockers.append("UNPAIRED_REGENERATED_ARTIFACT")
    unique_blockers = sorted({blocker for blocker in blockers if blocker})
    status = "PASS" if not unique_blockers and accepted_count > 0 else "BLOCKED"
    next_action = (
        "Use only PASS regenerated current-schema PAPER replacements as current evidence; originals remain audit references."
        if status == "PASS"
        else "Reconcile BLOCKED regenerated replacements and quarantine mismatched or unpaired artifacts before evidence use."
    )
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_RECONCILIATION_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "post_reconciliation_id": reconciliation_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": "paper_runtime_post_regeneration_reconciliation_truth",
        "post_reconciliation_role": POST_REGENERATION_RECONCILIATION_ROLE,
        "evidence_use_policy": POST_REGENERATION_EVIDENCE_USE_POLICY,
        "source_executor_hash": executor_report.get("executor_hash"),
        "source_executor_status": executor_report.get("executor_status"),
        "source_executor_validator_status": executor_result.status,
        "source_executor_validator_blocker_code": executor_result.blocker_code,
        "planned_regeneration_item_count": int(executor_report.get("planned_regeneration_item_count") or 0),
        "post_reconciliation_item_count": len(items),
        "source_retained_count": source_retained_count,
        "source_hash_mismatch_count": source_hash_mismatch_count,
        "replacement_found_count": replacement_found_count,
        "replacement_hash_mismatch_count": replacement_hash_mismatch_count,
        "regenerated_current_accepted_count": accepted_count,
        "regenerated_current_blocked_reconciliation_count": blocked_reconciliation_count,
        "regenerated_current_invalid_count": invalid_count,
        "current_evidence_usable_count": evidence_usable_count,
        "excluded_from_current_evidence_count": excluded_count,
        "usable_runtime_cycle_hash_duplicate_count": duplicate_usable_hash_count,
        "unpaired_regenerated_artifact_count": len(unpaired_paths),
        "unpaired_regenerated_artifact_paths": unpaired_paths,
        "post_reconciliation_status": status,
        "primary_blocker_code": unique_blockers[0] if unique_blockers else None,
        "blocker_codes": unique_blockers,
        "items": items,
        "delete_source_allowed": False,
        "overwrite_source_allowed": False,
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
        "operator_next_action": next_action,
        "post_reconciliation_hash": "",
    }
    report["post_reconciliation_hash"] = stale_loop_post_regeneration_reconciliation_hash(report)
    return report


def write_upbit_paper_stale_loop_post_regeneration_reconciliation_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = (
        _runtime_base(root, str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "post_reconciliation_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "post_reconciliation_role",
        "evidence_use_policy",
        "source_executor_hash",
        "source_executor_status",
        "source_executor_validator_status",
        "source_executor_validator_blocker_code",
        "planned_regeneration_item_count",
        "post_reconciliation_item_count",
        "source_retained_count",
        "source_hash_mismatch_count",
        "replacement_found_count",
        "replacement_hash_mismatch_count",
        "regenerated_current_accepted_count",
        "regenerated_current_blocked_reconciliation_count",
        "regenerated_current_invalid_count",
        "current_evidence_usable_count",
        "excluded_from_current_evidence_count",
        "usable_runtime_cycle_hash_duplicate_count",
        "unpaired_regenerated_artifact_count",
        "unpaired_regenerated_artifact_paths",
        "post_reconciliation_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
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
        "operator_next_action",
        "post_reconciliation_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult(
            "FAIL",
            f"post-regeneration reconciliation report missing fields: {missing}",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_RECONCILIATION_SCHEMA_ID:
        return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("FAIL", "post-regeneration schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("post_reconciliation_hash") != stale_loop_post_regeneration_reconciliation_hash(report):
        return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("FAIL", "post-regeneration hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "post-regeneration scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if (
        report.get("truth_role") != "paper_runtime_post_regeneration_reconciliation_truth"
        or report.get("post_reconciliation_role") != POST_REGENERATION_RECONCILIATION_ROLE
        or report.get("evidence_use_policy") != POST_REGENERATION_EVIDENCE_USE_POLICY
    ):
        return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "post-regeneration reconciliation cannot claim execution/live truth", "LIVE_FINAL_GUARD_FAILED")
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
        return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "post-regeneration reconciliation created forbidden permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("source_executor_validator_status") != "PASS" or report.get("source_executor_status") != "PASS":
        if report.get("post_reconciliation_status") != "BLOCKED":
            return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "invalid executor must keep post-regeneration reconciliation blocked", "STALE_LOOP_REGENERATION_REQUIRED")
    items = report.get("items")
    if not isinstance(items, list) or report.get("post_reconciliation_item_count") != len(items):
        return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("FAIL", "post-regeneration item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    accepted_count = 0
    blocked_reconciliation_count = 0
    invalid_count = 0
    usable_count = 0
    source_retained_count = 0
    source_hash_mismatch_count = 0
    replacement_found_count = 0
    replacement_hash_mismatch_count = 0
    usable_hashes: list[str] = []
    item_blockers: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("FAIL", "post-regeneration item must be object", "SCHEMA_IDENTITY_MISMATCH")
        item_required = {
            "source_path",
            "source_hash_expected",
            "source_hash_actual",
            "source_hash_match",
            "source_retained",
            "source_path_scope_status",
            "replacement_path",
            "replacement_path_scope_status",
            "replacement_exists",
            "replacement_loop_id",
            "replacement_loop_hash_expected",
            "replacement_loop_hash_actual",
            "replacement_loop_hash_match",
            "replacement_validation_status",
            "replacement_validation_blocker_code",
            "replacement_validation_message",
            "classification",
            "evidence_usable_current",
            "recommended_action",
            "item_blocker_code",
            "runtime_cycle_hashes",
            "unsafe_live_or_order_flag_detected",
            "source_excluded_from_current_evidence",
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
            return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("FAIL", f"post-regeneration item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH")
        session_id = str(report.get("session_id"))
        if (
            not _artifact_path_allowed(str(item["source_path"]), session_id)
            or not _artifact_path_allowed(str(item["replacement_path"]), session_id)
            or item.get("source_path_scope_status") != "MATCH"
            or item.get("replacement_path_scope_status") != "MATCH"
        ):
            return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "post-regeneration item path escaped UPBIT PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if item.get("delete_source_allowed") or item.get("overwrite_source_allowed") or item.get("actual_long_run_evidence_created"):
            return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "post-regeneration item allowed deletion, overwrite, or long-run evidence", "LIVE_FINAL_GUARD_FAILED")
        if item.get("live_order_ready") or item.get("live_order_allowed") or item.get("can_live_trade") or item.get("scale_up_allowed"):
            return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "post-regeneration item created live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
        if item.get("source_excluded_from_current_evidence") is not True:
            return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "source artifact must remain excluded from current evidence", POST_REGENERATION_RECONCILIATION_BLOCKER_CODE)
        if item.get("source_retained"):
            source_retained_count += 1
        if not item.get("source_hash_match"):
            source_hash_mismatch_count += 1
            item_blockers.append("STALE_LOOP_SOURCE_HASH_MISMATCH")
        if item.get("replacement_exists"):
            replacement_found_count += 1
        if not item.get("replacement_loop_hash_match"):
            replacement_hash_mismatch_count += 1
            item_blockers.append("STALE_LOOP_REPLACEMENT_MISMATCH")
        if item.get("evidence_usable_current"):
            usable_count += 1
            usable_hashes.extend(item.get("runtime_cycle_hashes") or [])
        classification = item.get("classification")
        if classification == "REGENERATED_CURRENT_ACCEPTED":
            accepted_count += 1
            if item.get("replacement_validation_status") != "PASS" or item.get("evidence_usable_current") is not True:
                return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("FAIL", "accepted replacement must validate PASS and be current usable", "SCHEMA_IDENTITY_MISMATCH")
        elif classification == "REGENERATED_CURRENT_BLOCKED_RECONCILIATION_REQUIRED":
            blocked_reconciliation_count += 1
            item_blockers.append(POST_REGENERATION_RECONCILIATION_BLOCKER_CODE)
            if (
                item.get("replacement_validation_status") != "BLOCKED"
                or item.get("replacement_validation_blocker_code") != "RECONCILIATION_REQUIRED"
                or item.get("evidence_usable_current")
            ):
                return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "blocked replacement must remain excluded until ledger/recovery reconciliation", POST_REGENERATION_RECONCILIATION_BLOCKER_CODE)
        else:
            invalid_count += 1
            if item.get("evidence_usable_current"):
                return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "non-accepted replacement marked usable", POST_REGENERATION_RECONCILIATION_BLOCKER_CODE)
            if item.get("item_blocker_code"):
                item_blockers.append(str(item["item_blocker_code"]))
    duplicate_usable_hash_count = len(usable_hashes) - len(set(usable_hashes))
    if (
        report.get("source_retained_count") != source_retained_count
        or report.get("source_hash_mismatch_count") != source_hash_mismatch_count
        or report.get("replacement_found_count") != replacement_found_count
        or report.get("replacement_hash_mismatch_count") != replacement_hash_mismatch_count
        or report.get("regenerated_current_accepted_count") != accepted_count
        or report.get("regenerated_current_blocked_reconciliation_count") != blocked_reconciliation_count
        or report.get("regenerated_current_invalid_count") != invalid_count
        or report.get("current_evidence_usable_count") != usable_count
        or report.get("excluded_from_current_evidence_count") != len(items) - usable_count
        or report.get("usable_runtime_cycle_hash_duplicate_count") != duplicate_usable_hash_count
    ):
        return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("FAIL", "post-regeneration rollup count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(report.get("unpaired_regenerated_artifact_paths"), list) or report.get("unpaired_regenerated_artifact_count") != len(report.get("unpaired_regenerated_artifact_paths")):
        return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("FAIL", "unpaired regenerated artifact count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_blockers = set(item_blockers)
    if duplicate_usable_hash_count:
        expected_blockers.add("DUPLICATE_RUNTIME_CYCLE_HASH")
    if report.get("unpaired_regenerated_artifact_count"):
        expected_blockers.add("UNPAIRED_REGENERATED_ARTIFACT")
    if expected_blockers:
        if report.get("post_reconciliation_status") != "BLOCKED":
            return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", "post-regeneration blockers must keep report blocked", POST_REGENERATION_RECONCILIATION_BLOCKER_CODE)
        missing_blockers = expected_blockers - set(report.get("blocker_codes") or [])
        if missing_blockers:
            return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("BLOCKED", f"post-regeneration blocker rollup missing: {sorted(missing_blockers)}", POST_REGENERATION_RECONCILIATION_BLOCKER_CODE)
    elif report.get("post_reconciliation_status") != "PASS" or report.get("primary_blocker_code") is not None:
        return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult("FAIL", "clean post-regeneration status mismatch", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperStaleLoopPostRegenerationReconciliationValidationResult(
        "PASS",
        "Upbit PAPER post-regeneration reconciliation separates usable regenerated evidence from blocked repairs and remains live-blocked",
        None,
    )
