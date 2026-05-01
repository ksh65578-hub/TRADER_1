from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.core.ledger.paper_ledger import validate_upbit_paper_ledger
from trader1.runtime.paper.upbit_paper_bounded_rerun_staging_executor import (
    POST_RERUN_LEDGER_ROLLUP_REQUIRED_BLOCKER_CODE,
    validate_upbit_paper_bounded_rerun_staging_executor_report,
)
from trader1.runtime.paper.upbit_paper_runtime import (
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION_SCHEMA_ID = (
    "trader1.upbit_paper_post_rerun_ledger_rollup_reconciliation_report.v1"
)
POST_RERUN_LEDGER_ROLLUP_RECONCILIATION_TRUTH_ROLE = (
    "PAPER_RUNTIME_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION_CANDIDATE_ONLY_NOT_CURRENT_EVIDENCE"
)
POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE = "PAPER_RERUN_CANDIDATE_LEDGER_ROLLUP_NOT_CURRENT_EVIDENCE"
POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE = "POST_RERUN_RECONCILIATION_REQUIRED"
RERUN_CANDIDATE_LEDGER_ROLLUP_MISMATCH_BLOCKER_CODE = (
    "RERUN_CANDIDATE_LEDGER_ROLLUP_MISMATCH_RECONCILIATION_REQUIRED"
)


@dataclass(frozen=True)
class UpbitPaperPostRerunLedgerRollupReconciliationValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_post_rerun_ledger_rollup_reconciliation_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("post_rerun_reconciliation_hash", None)
    return _sha256_json(payload)


def _candidate_rollup_hash(candidate: dict[str, Any]) -> str:
    payload = dict(candidate)
    payload.pop("candidate_rollup_hash", None)
    return _sha256_json(payload)


def _writer_report_hash(writer: dict[str, Any]) -> str:
    payload = dict(writer)
    payload.pop("writer_report_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    return normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "/live/" not in normalized


def _staging_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return _artifact_path_allowed(normalized, session_id) and "/paper_runtime/rerun_candidates/" in normalized


def _candidate_rollup_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return _artifact_path_allowed(normalized, session_id) and "/paper_runtime/rerun_candidates_post_rollup/" in normalized


def _safe_segment(value: Any) -> str:
    text = str(value or "UNKNOWN")
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in text)


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


def _safe_read_jsonl(path: Path) -> tuple[list[dict[str, Any]] | None, str | None]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None, "MISSING"
    except UnicodeDecodeError:
        return None, "INVALID_UTF8"
    records: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            return None, "INVALID_JSON"
        if not isinstance(value, dict):
            return None, "NOT_OBJECT"
        records.append(value)
    return records, None


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _candidate_artifact_path(session_id: str, replacement_loop_id: str, cycle_id: str) -> str:
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/rerun_candidates_post_rollup/"
        f"{_safe_segment(replacement_loop_id)}/{_safe_segment(cycle_id)}.ledger_rollup_candidate.json"
    )


def _candidate_current_evidence_blocker() -> dict[str, str]:
    return _blocker(
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "post-rerun candidate rollup is not current evidence; explicit reconciliation and promotion guard are still required",
    )


def _build_candidate_rollup(
    *,
    session_id: str,
    source_executor_hash: str | None,
    item: dict[str, Any],
    cycle: dict[str, Any] | None,
    records: list[dict[str, Any]] | None,
    runtime_status: str,
    runtime_blocker: str | None,
    ledger_status: str,
    ledger_blocker: str | None,
    ledger_message: str,
    writer_status: str,
    writer_blocker: str | None,
    candidate_path: str,
) -> dict[str, Any]:
    records = records or []
    fill_events = [event for event in records if event.get("event_type") == "ORDER_FILLED"]
    latest_ledger_head_hash = records[-1].get("event_hash") if records else None
    blockers: list[dict[str, str]] = []
    if runtime_status != "PASS":
        blockers.append(_blocker(runtime_blocker or "SCHEMA_IDENTITY_MISMATCH", "staged runtime cycle failed validation"))
    if ledger_status != "PASS":
        blockers.append(_blocker(ledger_blocker or "LEDGER_INTEGRITY_FAIL", ledger_message))
    if writer_status != "PASS":
        blockers.append(_blocker(writer_blocker or "SCHEMA_IDENTITY_MISMATCH", "staged writer report failed validation"))
    if not _candidate_rollup_path_allowed(candidate_path, session_id):
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "candidate rollup path escaped PAPER post-rollup namespace"))
    candidate = {
        "candidate_rollup_role": POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "replacement_loop_id": str(item.get("replacement_loop_id") or "UNKNOWN"),
        "cycle_id": str(item.get("cycle_id") or "UNKNOWN"),
        "source_staging_executor_hash": source_executor_hash,
        "source_staging_executor_item_status": item.get("staging_item_status"),
        "staged_runtime_cycle_path": item.get("planned_runtime_cycle_path"),
        "staged_ledger_jsonl_path": item.get("planned_ledger_jsonl_path"),
        "staged_writer_report_path": item.get("planned_writer_report_path"),
        "candidate_rollup_artifact_path": candidate_path,
        "staged_runtime_cycle_hash": cycle.get("cycle_hash") if isinstance(cycle, dict) else None,
        "final_decision": cycle.get("final_decision") if isinstance(cycle, dict) else None,
        "ledger_jsonl_count": 1,
        "ledger_event_count": len(records),
        "filled_order_count": len(fill_events),
        "latest_ledger_head_hash": latest_ledger_head_hash,
        "empty_no_trade_ledger": len(records) == 0 and isinstance(cycle, dict) and cycle.get("final_decision") != "ENTER_LONG",
        "candidate_rollup_status": "PASS" if not blockers else "BLOCKED",
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "display_only": True,
        "paper_only": True,
        "candidate_artifact_is_current_evidence": False,
        "candidate_current_evidence_usable": False,
        "current_evidence_mutation_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "candidate_rollup_hash": "",
    }
    candidate["candidate_rollup_hash"] = _candidate_rollup_hash(candidate)
    return candidate


def _candidate_stable_hash(candidate: dict[str, Any]) -> str:
    payload = dict(candidate)
    payload.pop("candidate_rollup_hash", None)
    payload.pop("generated_at_utc", None)
    return _sha256_json(payload)


def _existing_candidate_matches(path: Path, candidate: dict[str, Any]) -> dict[str, Any] | None:
    existing, error = _safe_load_json(path)
    if error or existing is None:
        return None
    existing_hash = existing.get("candidate_rollup_hash")
    if existing_hash != _candidate_rollup_hash(existing):
        return None
    if _candidate_stable_hash(existing) != _candidate_stable_hash(candidate):
        return None
    return existing


def _write_or_reuse_candidate(path: Path, candidate: dict[str, Any]) -> tuple[str, dict[str, Any], bool, bool]:
    existed = path.exists()
    if existed:
        existing = _existing_candidate_matches(path, candidate)
        if existing is not None:
            return "REUSED_EXISTING_MATCH", existing, False, True
        return "BLOCKED_EXISTING_MISMATCH", candidate, False, False
    durable_atomic_write_json(path, candidate)
    return "WRITTEN", candidate, True, False


def _staged_writer_status(
    writer: dict[str, Any] | None,
    *,
    cycle_id: str,
    staged_runtime_cycle_hash: str | None,
    staged_runtime_cycle_path: str,
    staged_ledger_jsonl_path: str,
    staged_writer_report_path: str,
) -> tuple[str, str | None, str | None, str | None, str]:
    if not isinstance(writer, dict):
        return "BLOCKED", "MEASUREMENT_MISSING", None, None, "FAIL"
    expected_hash = writer.get("writer_report_hash")
    recomputed_hash = _writer_report_hash(writer)
    hash_self_check = "PASS" if expected_hash == recomputed_hash else "FAIL"
    if hash_self_check != "PASS":
        return "BLOCKED", "SCHEMA_IDENTITY_MISMATCH", expected_hash, recomputed_hash, hash_self_check
    if (
        writer.get("writer_status") != "PASS"
        or writer.get("cycle_id") != cycle_id
        or writer.get("staged_runtime_cycle_hash") != staged_runtime_cycle_hash
        or writer.get("staged_runtime_cycle_path") != staged_runtime_cycle_path
        or writer.get("staged_ledger_jsonl_path") != staged_ledger_jsonl_path
        or writer.get("staged_writer_report_path") != staged_writer_report_path
        or writer.get("staged_artifact_is_current_evidence")
        or writer.get("live_order_allowed")
        or writer.get("scale_up_allowed")
    ):
        return "BLOCKED", "RERUN_STAGING_ARTIFACT_MISMATCH_RECONCILIATION_REQUIRED", expected_hash, recomputed_hash, hash_self_check
    return "PASS", None, expected_hash, recomputed_hash, hash_self_check


def _ledger_status_for_cycle(cycle: dict[str, Any] | None, records: list[dict[str, Any]] | None, ledger_error: str | None) -> tuple[str, str | None, str]:
    if ledger_error:
        return "BLOCKED", "LEDGER_UNAVAILABLE", f"staged PAPER ledger JSONL load failed: {ledger_error}"
    if records is None:
        return "BLOCKED", "LEDGER_UNAVAILABLE", "staged PAPER ledger JSONL was not loaded"
    if records:
        status, blocker, message = validate_upbit_paper_ledger(records)
        return status, blocker, message
    if isinstance(cycle, dict) and cycle.get("final_decision") != "ENTER_LONG":
        return "PASS", None, "no-trade staged PAPER cycle has empty ledger JSONL"
    return "BLOCKED", "MEASUREMENT_MISSING", "ENTER_LONG staged PAPER cycle requires ledger events"


def _build_item(*, root: Path, session_id: str, source_executor_hash: str | None, source_item: dict[str, Any]) -> dict[str, Any]:
    cycle_id = str(source_item.get("cycle_id") or "UNKNOWN")
    replacement_loop_id = str(source_item.get("replacement_loop_id") or "UNKNOWN")
    runtime_path_text = str(source_item.get("planned_runtime_cycle_path") or "")
    ledger_path_text = str(source_item.get("planned_ledger_jsonl_path") or "")
    writer_path_text = str(source_item.get("planned_writer_report_path") or "")
    candidate_path_text = _candidate_artifact_path(session_id, replacement_loop_id, cycle_id)

    cycle, runtime_error = _safe_load_json(_rooted(root, runtime_path_text))
    records, ledger_error = _safe_read_jsonl(_rooted(root, ledger_path_text))
    writer, writer_error = _safe_load_json(_rooted(root, writer_path_text))
    runtime_result = validate_upbit_paper_runtime_cycle_report(cycle or {})
    runtime_hash_recomputed = upbit_paper_runtime_cycle_hash(cycle) if isinstance(cycle, dict) else None
    runtime_hash_actual = cycle.get("cycle_hash") if isinstance(cycle, dict) else None
    runtime_hash_expected = source_item.get("staged_runtime_cycle_hash_actual")
    runtime_hash_self_check = "PASS" if runtime_hash_actual == runtime_hash_recomputed else "FAIL"
    ledger_status, ledger_blocker, ledger_message = _ledger_status_for_cycle(cycle, records, ledger_error)
    writer_status, writer_blocker, writer_hash, writer_recomputed_hash, writer_hash_self_check = _staged_writer_status(
        writer,
        cycle_id=cycle_id,
        staged_runtime_cycle_hash=runtime_hash_actual,
        staged_runtime_cycle_path=runtime_path_text,
        staged_ledger_jsonl_path=ledger_path_text,
        staged_writer_report_path=writer_path_text,
    )
    path_scope_status = (
        "MATCH"
        if _staging_path_allowed(runtime_path_text, session_id)
        and _staging_path_allowed(ledger_path_text, session_id)
        and _staging_path_allowed(writer_path_text, session_id)
        and _candidate_rollup_path_allowed(candidate_path_text, session_id)
        else "MISMATCH"
    )
    if runtime_error and runtime_result.status == "FAIL":
        runtime_status = "BLOCKED"
        runtime_blocker = runtime_error
    else:
        runtime_status = runtime_result.status
        runtime_blocker = runtime_result.blocker_code
    if (
        runtime_status == "PASS"
        and (runtime_hash_self_check != "PASS" or runtime_hash_expected != runtime_hash_actual)
    ):
        runtime_status = "BLOCKED"
        runtime_blocker = "RERUN_STAGING_ARTIFACT_MISMATCH_RECONCILIATION_REQUIRED"
    if writer_error and writer_status == "BLOCKED":
        writer_blocker = writer_error
    if path_scope_status != "MATCH":
        runtime_status = "BLOCKED"
        runtime_blocker = "SNAPSHOT_SCOPE_MISMATCH"

    candidate = _build_candidate_rollup(
        session_id=session_id,
        source_executor_hash=source_executor_hash,
        item=source_item,
        cycle=cycle,
        records=records,
        runtime_status=runtime_status,
        runtime_blocker=runtime_blocker,
        ledger_status=ledger_status,
        ledger_blocker=ledger_blocker,
        ledger_message=ledger_message,
        writer_status=writer_status,
        writer_blocker=writer_blocker,
        candidate_path=candidate_path_text,
    )
    write_status = "NOT_WRITTEN"
    candidate_written = False
    candidate_reused = False
    if candidate.get("candidate_rollup_status") == "PASS":
        write_status, candidate, candidate_written, candidate_reused = _write_or_reuse_candidate(
            _rooted(root, candidate_path_text),
            candidate,
        )
        if write_status == "BLOCKED_EXISTING_MISMATCH":
            blockers = list(candidate["blockers"])
            blockers.append(_blocker(RERUN_CANDIDATE_LEDGER_ROLLUP_MISMATCH_BLOCKER_CODE, "existing candidate rollup artifact does not match recomputed staged ledger rollup"))
            candidate["candidate_rollup_status"] = "BLOCKED"
            candidate["primary_blocker_code"] = RERUN_CANDIDATE_LEDGER_ROLLUP_MISMATCH_BLOCKER_CODE
            candidate["blockers"] = blockers
            candidate["candidate_rollup_hash"] = _candidate_rollup_hash(candidate)
    candidate_recomputed_hash = _candidate_rollup_hash(candidate)
    candidate_hash_self_check = "PASS" if candidate.get("candidate_rollup_hash") == candidate_recomputed_hash else "FAIL"
    item_blocker = (
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        if candidate.get("candidate_rollup_status") == "PASS"
        else candidate.get("primary_blocker_code") or "UNKNOWN_BLOCKED"
    )
    classification = (
        "RERUN_CANDIDATE_LEDGER_ROLLUP_PASS_CURRENT_EVIDENCE_BLOCKED"
        if candidate.get("candidate_rollup_status") == "PASS"
        else "RERUN_CANDIDATE_BLOCKED_ROLLUP_VALIDATION"
    )
    return {
        "source_guard_priority_order": int(source_item.get("source_guard_priority_order") or 0),
        "replacement_loop_id": replacement_loop_id,
        "cycle_id": cycle_id,
        "source_staging_item_status": str(source_item.get("staging_item_status") or "UNKNOWN"),
        "staged_runtime_cycle_path": runtime_path_text,
        "staged_ledger_jsonl_path": ledger_path_text,
        "staged_writer_report_path": writer_path_text,
        "candidate_rollup_artifact_path": candidate_path_text,
        "staged_runtime_cycle_load_status": "PASS" if cycle is not None else str(runtime_error or "UNKNOWN"),
        "staged_ledger_jsonl_load_status": "PASS" if records is not None else str(ledger_error or "UNKNOWN"),
        "staged_writer_report_load_status": "PASS" if writer is not None else str(writer_error or "UNKNOWN"),
        "staged_runtime_cycle_hash_expected": runtime_hash_expected,
        "staged_runtime_cycle_hash_actual": runtime_hash_actual,
        "staged_runtime_cycle_hash_recomputed": runtime_hash_recomputed,
        "staged_runtime_cycle_hash_match": bool(runtime_hash_expected and runtime_hash_expected == runtime_hash_actual == runtime_hash_recomputed),
        "runtime_cycle_validator_status": runtime_result.status,
        "runtime_cycle_validator_blocker_code": runtime_result.blocker_code,
        "runtime_cycle_hash_self_check": runtime_hash_self_check,
        "staged_writer_report_hash": writer_hash,
        "staged_writer_report_recomputed_hash": writer_recomputed_hash,
        "staged_writer_report_hash_self_check": writer_hash_self_check,
        "staged_writer_validator_status": writer_status,
        "staged_writer_validator_blocker_code": writer_blocker,
        "ledger_validator_status": ledger_status,
        "ledger_validator_blocker_code": ledger_blocker,
        "ledger_validator_message": ledger_message,
        "final_decision": cycle.get("final_decision") if isinstance(cycle, dict) else None,
        "candidate_ledger_jsonl_count": 1,
        "candidate_ledger_event_count": len(records or []),
        "candidate_filled_order_count": len([event for event in (records or []) if event.get("event_type") == "ORDER_FILLED"]),
        "candidate_empty_no_trade_ledger": len(records or []) == 0 and isinstance(cycle, dict) and cycle.get("final_decision") != "ENTER_LONG",
        "latest_ledger_head_hash": (records or [{}])[-1].get("event_hash") if records else None,
        "path_scope_status": path_scope_status,
        "candidate_rollup_status": candidate.get("candidate_rollup_status"),
        "candidate_rollup_hash": candidate.get("candidate_rollup_hash"),
        "candidate_rollup_recomputed_hash": candidate_recomputed_hash,
        "candidate_rollup_hash_self_check": candidate_hash_self_check,
        "candidate_rollup_write_status": write_status,
        "candidate_rollup_written": candidate_written,
        "candidate_rollup_reused_existing": candidate_reused,
        "candidate_rollup_artifact_ready": candidate.get("candidate_rollup_status") == "PASS" and write_status in {"WRITTEN", "REUSED_EXISTING_MATCH"},
        "candidate_current_evidence_usable": False,
        "candidate_classification": classification,
        "item_blocker_code": item_blocker,
        "recommended_operator_action": "Keep staged PAPER rerun rollup as candidate evidence only; run explicit current-evidence promotion guard before changing pointers.",
        "candidate_rollup": candidate,
        "current_evidence_mutation_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
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


def build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(
    *,
    root: Path,
    staging_executor_report: dict[str, Any],
    source_staging_executor_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_bounded_rerun_staging_executor_report.json",
    reconciliation_id: str = "upbit-paper-post-rerun-ledger-rollup-reconciliation",
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_bounded_rerun_staging_executor_report(staging_executor_report)
    session_id = str(staging_executor_report.get("session_id", "UNKNOWN"))
    source_items = [
        item
        for item in staging_executor_report.get("items", [])
        if isinstance(item, dict) and item.get("staging_item_status") in {"STAGED", "REUSED_EXISTING"}
    ]
    blockers = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if staging_executor_report.get("primary_blocker_code"):
        blockers.add(str(staging_executor_report["primary_blocker_code"]))
    if source_result.status != "PASS":
        blockers.add(source_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    items = [
        _build_item(root=root, session_id=session_id, source_executor_hash=staging_executor_report.get("executor_hash"), source_item=item)
        for item in source_items
    ] if source_result.status == "PASS" and staging_executor_report.get("staging_status") == "PASS" else []
    blockers.update(str(item["item_blocker_code"]) for item in items if item.get("item_blocker_code"))

    candidate_pass_count = sum(1 for item in items if item.get("candidate_rollup_status") == "PASS")
    candidate_blocked_count = len(items) - candidate_pass_count
    artifact_ready_count = sum(1 for item in items if item.get("candidate_rollup_artifact_ready"))
    candidate_written_count = sum(1 for item in items if item.get("candidate_rollup_written"))
    candidate_reused_count = sum(1 for item in items if item.get("candidate_rollup_reused_existing"))
    candidate_mismatch_count = sum(1 for item in items if item.get("candidate_rollup_write_status") == "BLOCKED_EXISTING_MISMATCH")
    staged_hash_match_count = sum(1 for item in items if item.get("staged_runtime_cycle_hash_match"))
    writer_hash_match_count = sum(1 for item in items if item.get("staged_writer_report_hash_self_check") == "PASS")
    empty_no_trade_count = sum(1 for item in items if item.get("candidate_empty_no_trade_ledger"))
    expected_count = int(staging_executor_report.get("staged_cycle_count") or 0)
    rollup_status = "PASS" if len(items) == expected_count and expected_count > 0 and artifact_ready_count == expected_count and candidate_mismatch_count == 0 else "BLOCKED"
    if rollup_status != "PASS":
        blockers.add("POST_RERUN_LEDGER_ROLLUP_REQUIRED")
    report = {
        "schema_id": UPBIT_PAPER_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "post_rerun_reconciliation_id": reconciliation_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_RERUN_LEDGER_ROLLUP_RECONCILIATION_TRUTH_ROLE,
        "source_staging_executor_path": source_staging_executor_path,
        "source_staging_executor_hash": staging_executor_report.get("executor_hash"),
        "source_staging_status": staging_executor_report.get("staging_status"),
        "source_executor_status": staging_executor_report.get("executor_status"),
        "source_primary_blocker_code": staging_executor_report.get("primary_blocker_code"),
        "eligible_missing_cycle_count": int(staging_executor_report.get("eligible_missing_cycle_count") or 0),
        "source_staged_cycle_count": expected_count,
        "source_staged_artifact_count": int(staging_executor_report.get("staged_artifact_count") or 0),
        "candidate_item_count": len(items),
        "candidate_rollup_pass_count": candidate_pass_count,
        "candidate_rollup_blocked_count": candidate_blocked_count,
        "candidate_rollup_artifact_ready_count": artifact_ready_count,
        "candidate_rollup_written_count": candidate_written_count,
        "candidate_rollup_reused_existing_count": candidate_reused_count,
        "candidate_rollup_mismatch_count": candidate_mismatch_count,
        "candidate_ledger_jsonl_count": sum(int(item.get("candidate_ledger_jsonl_count") or 0) for item in items),
        "candidate_ledger_event_count": sum(int(item.get("candidate_ledger_event_count") or 0) for item in items),
        "candidate_filled_order_count": sum(int(item.get("candidate_filled_order_count") or 0) for item in items),
        "candidate_empty_no_trade_ledger_count": empty_no_trade_count,
        "staged_runtime_cycle_hash_match_count": staged_hash_match_count,
        "staged_writer_hash_match_count": writer_hash_match_count,
        "candidate_current_evidence_usable_count": 0,
        "candidate_current_evidence_blocked_count": len(items),
        "post_rerun_ledger_rollup_status": rollup_status,
        "post_rerun_reconciliation_status": "BLOCKED",
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "blocker_codes": sorted(blockers),
        "items": items,
        "operator_next_action": "Review post-rerun candidate rollups, then run a current-evidence promotion guard before any ledger or runtime pointer can change.",
        "current_evidence_mutation_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_rerun_executed": False,
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
        "post_rerun_reconciliation_hash": "",
    }
    report["post_rerun_reconciliation_hash"] = upbit_paper_post_rerun_ledger_rollup_reconciliation_hash(report)
    return report


def write_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_post_rerun_ledger_rollup_reconciliation_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(
    report: dict[str, Any],
) -> UpbitPaperPostRerunLedgerRollupReconciliationValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "post_rerun_reconciliation_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "source_staging_executor_path",
        "source_staging_executor_hash",
        "source_staging_status",
        "source_executor_status",
        "source_primary_blocker_code",
        "eligible_missing_cycle_count",
        "source_staged_cycle_count",
        "source_staged_artifact_count",
        "candidate_item_count",
        "candidate_rollup_pass_count",
        "candidate_rollup_blocked_count",
        "candidate_rollup_artifact_ready_count",
        "candidate_rollup_written_count",
        "candidate_rollup_reused_existing_count",
        "candidate_rollup_mismatch_count",
        "candidate_ledger_jsonl_count",
        "candidate_ledger_event_count",
        "candidate_filled_order_count",
        "candidate_empty_no_trade_ledger_count",
        "staged_runtime_cycle_hash_match_count",
        "staged_writer_hash_match_count",
        "candidate_current_evidence_usable_count",
        "candidate_current_evidence_blocked_count",
        "post_rerun_ledger_rollup_status",
        "post_rerun_reconciliation_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "current_evidence_mutation_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_rerun_executed",
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
        "post_rerun_reconciliation_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", f"post-rerun reconciliation missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION_SCHEMA_ID:
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", "post-rerun reconciliation schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("post_rerun_reconciliation_hash") != upbit_paper_post_rerun_ledger_rollup_reconciliation_hash(report):
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", "post-rerun reconciliation hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun reconciliation scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != POST_RERUN_LEDGER_ROLLUP_RECONCILIATION_TRUTH_ROLE:
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun reconciliation cannot claim current evidence or live truth", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "current_evidence_mutation_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_rerun_executed",
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
    if any(report.get(field) for field in forbidden):
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun reconciliation created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if report.get("source_staging_status") != "PASS" or report.get("source_executor_status") != "BLOCKED":
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "source bounded rerun staging executor must be PASS/BLOCKED source", POST_RERUN_LEDGER_ROLLUP_REQUIRED_BLOCKER_CODE)
    if report.get("source_primary_blocker_code") != POST_RERUN_LEDGER_ROLLUP_REQUIRED_BLOCKER_CODE:
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "source staging executor must require post-rerun ledger rollup", POST_RERUN_LEDGER_ROLLUP_REQUIRED_BLOCKER_CODE)
    if report.get("post_rerun_reconciliation_status") != "BLOCKED" or report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE:
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun reconciliation must remain blocked before current evidence promotion", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if report.get("candidate_current_evidence_usable_count") != 0:
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun reconciliation exposed current evidence usability", "LIVE_FINAL_GUARD_FAILED")
    session_id = str(report.get("session_id"))
    if not _artifact_path_allowed(str(report.get("source_staging_executor_path") or ""), session_id):
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "source staging executor path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    items = report.get("items")
    if not isinstance(items, list) or report.get("candidate_item_count") != len(items):
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", "post-rerun item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    pass_count = sum(1 for item in items if isinstance(item, dict) and item.get("candidate_rollup_status") == "PASS")
    ready_count = sum(1 for item in items if isinstance(item, dict) and item.get("candidate_rollup_artifact_ready"))
    written_count = sum(1 for item in items if isinstance(item, dict) and item.get("candidate_rollup_written"))
    reused_count = sum(1 for item in items if isinstance(item, dict) and item.get("candidate_rollup_reused_existing"))
    mismatch_count = sum(1 for item in items if isinstance(item, dict) and item.get("candidate_rollup_write_status") == "BLOCKED_EXISTING_MISMATCH")
    ledger_jsonl_count = sum(int(item.get("candidate_ledger_jsonl_count") or 0) for item in items if isinstance(item, dict))
    ledger_event_count = sum(int(item.get("candidate_ledger_event_count") or 0) for item in items if isinstance(item, dict))
    filled_order_count = sum(int(item.get("candidate_filled_order_count") or 0) for item in items if isinstance(item, dict))
    empty_no_trade_count = sum(1 for item in items if isinstance(item, dict) and item.get("candidate_empty_no_trade_ledger"))
    staged_hash_match_count = sum(1 for item in items if isinstance(item, dict) and item.get("staged_runtime_cycle_hash_match"))
    writer_hash_match_count = sum(1 for item in items if isinstance(item, dict) and item.get("staged_writer_report_hash_self_check") == "PASS")
    expected_counts = {
        "candidate_rollup_pass_count": pass_count,
        "candidate_rollup_blocked_count": len(items) - pass_count,
        "candidate_rollup_artifact_ready_count": ready_count,
        "candidate_rollup_written_count": written_count,
        "candidate_rollup_reused_existing_count": reused_count,
        "candidate_rollup_mismatch_count": mismatch_count,
        "candidate_ledger_jsonl_count": ledger_jsonl_count,
        "candidate_ledger_event_count": ledger_event_count,
        "candidate_filled_order_count": filled_order_count,
        "candidate_empty_no_trade_ledger_count": empty_no_trade_count,
        "staged_runtime_cycle_hash_match_count": staged_hash_match_count,
        "staged_writer_hash_match_count": writer_hash_match_count,
        "candidate_current_evidence_blocked_count": len(items),
    }
    for field, expected in expected_counts.items():
        if report.get(field) != expected:
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", f"post-rerun count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_staged_cycle_count") != len(items) or report.get("eligible_missing_cycle_count") != len(items):
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", "post-rerun source staged count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("post_rerun_ledger_rollup_status") != "PASS":
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun candidate ledger rollup is not fully ready", POST_RERUN_LEDGER_ROLLUP_REQUIRED_BLOCKER_CODE)
    if ready_count != len(items) or pass_count != len(items) or mismatch_count:
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun rollup candidate readiness mismatch", POST_RERUN_LEDGER_ROLLUP_REQUIRED_BLOCKER_CODE)
    blocker_codes = set(report.get("blocker_codes") or [])
    if POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in blocker_codes:
        return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun reconciliation blocker missing", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", "post-rerun item must be object", "SCHEMA_IDENTITY_MISMATCH")
        for path_field in ("staged_runtime_cycle_path", "staged_ledger_jsonl_path", "staged_writer_report_path"):
            if not _staging_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", f"post-rerun {path_field} escaped staging namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not _candidate_rollup_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun candidate rollup path escaped post-rollup namespace", "SNAPSHOT_SCOPE_MISMATCH")
        item_forbidden = (
            "candidate_current_evidence_usable",
            "current_evidence_mutation_allowed",
            "current_ledger_jsonl_write_allowed",
            "latest_runtime_pointer_write_allowed",
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
        if any(item.get(field) for field in item_forbidden):
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun item attempted current evidence or live mutation", "LIVE_FINAL_GUARD_FAILED")
        candidate = item.get("candidate_rollup")
        if not isinstance(candidate, dict):
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", "post-rerun candidate rollup missing", "SCHEMA_IDENTITY_MISMATCH")
        if candidate.get("candidate_rollup_hash") != item.get("candidate_rollup_hash") or _candidate_rollup_hash(candidate) != item.get("candidate_rollup_recomputed_hash"):
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", "post-rerun candidate rollup hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("candidate_rollup_hash_self_check") != "PASS" or candidate.get("candidate_rollup_status") != "PASS":
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun candidate rollup did not pass self-check", candidate.get("primary_blocker_code") or "UNKNOWN_BLOCKED")
        if (
            candidate.get("candidate_artifact_is_current_evidence")
            or candidate.get("candidate_current_evidence_usable")
            or candidate.get("current_evidence_mutation_allowed")
            or candidate.get("live_order_allowed")
            or candidate.get("scale_up_allowed")
        ):
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun candidate rollup attempted live/current evidence permission", "LIVE_FINAL_GUARD_FAILED")
        if item.get("runtime_cycle_validator_status") != "PASS" or not item.get("staged_runtime_cycle_hash_match"):
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", "post-rerun runtime linkage mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("staged_writer_validator_status") != "PASS" or item.get("staged_writer_report_hash_self_check") != "PASS":
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", "post-rerun writer linkage mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("ledger_validator_status") != "PASS":
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun ledger validation blocked", item.get("ledger_validator_blocker_code") or "LEDGER_INTEGRITY_FAIL")
        if item.get("candidate_ledger_event_count") == 0 and not item.get("candidate_empty_no_trade_ledger"):
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("FAIL", "empty post-rerun ledger must be classified as no-trade", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("item_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE:
            return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult("BLOCKED", "post-rerun candidate must remain blocked by reconciliation", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    return UpbitPaperPostRerunLedgerRollupReconciliationValidationResult(
        "PASS",
        "Upbit PAPER post-rerun candidate rollups are hash-linked, staged-only, idempotent, and blocked from current evidence",
        None,
    )
