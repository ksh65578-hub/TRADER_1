from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.core.ledger.paper_ledger import validate_upbit_paper_ledger
from trader1.runtime.ledger.paper_ledger_rollup import (
    build_paper_ledger_rollup_report,
    validate_paper_ledger_rollup_report,
    write_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_runtime import (
    build_upbit_paper_runtime_cycle_report,
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import (
    build_upbit_public_market_data_collection_report,
    durable_atomic_write_json,
    durable_atomic_write_jsonl,
    recover_jsonl_records,
    upbit_public_market_data_collection_hash,
    validate_upbit_public_market_data_collection_report,
    write_upbit_public_market_data_collection_artifacts,
)


UPBIT_PAPER_PERSISTENT_LOOP_SCHEMA_ID = "trader1.upbit_paper_persistent_loop_report.v1"
UPBIT_PAPER_RUNTIME_RECOVERY_GUARD_SCHEMA_ID = "trader1.upbit_paper_runtime_recovery_guard_report.v1"
DEFAULT_MAX_CYCLE_COUNT = 20


@dataclass(frozen=True)
class UpbitPaperPersistentLoopValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_persistent_loop_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("loop_hash", None)
    return _sha256_json(payload)


def upbit_paper_runtime_recovery_guard_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("guard_hash", None)
    return _sha256_json(payload)


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _runtime_base_dir(root: Path, session_id: str) -> Path:
    return root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _safe_read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(value, dict):
        return None, "not_object"
    return value, None


def build_upbit_paper_runtime_recovery_guard_report(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    loop_id: str,
) -> dict[str, Any]:
    root = Path(root).resolve()
    base = _runtime_base_dir(root, session_id)
    latest_path = base / "upbit_paper_runtime_cycle_report.json"
    blockers: list[dict[str, str]] = []
    artifact_paths: list[str] = []

    orphan_tmp_files = sorted(path for path in base.rglob("*.tmp") if path.is_file()) if base.exists() else []
    if orphan_tmp_files:
        blockers.append(
            {
                "code": "PARTIAL_WRITE_RECOVERY_REQUIRED",
                "severity": "HIGH",
                "message": "orphan runtime temp files require operator review before continuing PAPER runtime",
            }
        )
    artifact_paths.extend(_relative_posix(path, root) for path in orphan_tmp_files)

    corrupted_jsonl_quarantined_count = 0
    jsonl_paths = sorted((base / "market_data" / "public" / "canonical").glob("*.canonical_events.jsonl"))
    for path in jsonl_paths:
        records, quarantine_path = recover_jsonl_records(path)
        artifact_paths.append(_relative_posix(path, root))
        if quarantine_path is not None:
            corrupted_jsonl_quarantined_count += 1
            artifact_paths.append(_relative_posix(quarantine_path, root))
            blockers.append(
                {
                    "code": "PARTIAL_WRITE_RECOVERY_REQUIRED",
                    "severity": "HIGH",
                    "message": "corrupted canonical JSONL was quarantined; resume requires reconcile review",
                }
            )
        if not records:
            blockers.append(
                {
                    "code": "DATA_UNAVAILABLE",
                    "severity": "HIGH",
                    "message": "canonical JSONL exists but has no recoverable records",
                }
            )

    corrupted_ledger_jsonl_quarantined_count = 0
    ledger_jsonl_invalid_count = 0
    ledger_jsonl_paths = sorted((base / "ledger" / "cycles").glob("*.paper_ledger_events.jsonl"))
    for path in ledger_jsonl_paths:
        records, quarantine_path = recover_jsonl_records(path)
        artifact_paths.append(_relative_posix(path, root))
        if quarantine_path is not None:
            corrupted_ledger_jsonl_quarantined_count += 1
            artifact_paths.append(_relative_posix(quarantine_path, root))
            blockers.append(
                {
                    "code": "PARTIAL_WRITE_RECOVERY_REQUIRED",
                    "severity": "HIGH",
                    "message": "corrupted PAPER ledger JSONL was quarantined; resume requires reconcile review",
                }
            )
        if not records:
            continue
        ledger_status, ledger_blocker, ledger_message = validate_upbit_paper_ledger(records)
        if ledger_status != "PASS":
            ledger_jsonl_invalid_count += 1
            blockers.append(
                {
                    "code": ledger_blocker or "LEDGER_INTEGRITY_FAIL",
                    "severity": "HIGH",
                    "message": ledger_message,
                }
            )

    latest_cycle, latest_error = _safe_read_json(latest_path)
    latest_cycle_status = "MISSING"
    latest_cycle_hash = None
    latest_cycle_recoverable = False
    if latest_error is not None:
        blockers.append(
            {
                "code": "HARD_TRUTH_MISSING" if latest_error == "missing" else "PARTIAL_WRITE_RECOVERY_REQUIRED",
                "severity": "HIGH",
                "message": "latest PAPER runtime cycle is missing or unreadable",
            }
        )
    else:
        artifact_paths.append(_relative_posix(latest_path, root))
        runtime_result = validate_upbit_paper_runtime_cycle_report(latest_cycle or {})
        latest_cycle_status = runtime_result.status
        latest_cycle_hash = latest_cycle.get("cycle_hash") if isinstance(latest_cycle, dict) else None
        latest_cycle_recoverable = runtime_result.status == "PASS"
        if runtime_result.status != "PASS":
            blockers.append(
                {
                    "code": runtime_result.blocker_code or "RECONCILIATION_REQUIRED",
                    "severity": "HIGH",
                    "message": runtime_result.message,
                }
            )

    status = "PASS" if not blockers else "BLOCKED"
    report = {
        "schema_id": UPBIT_PAPER_RUNTIME_RECOVERY_GUARD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "guard_id": f"{loop_id}-recovery-guard",
        "loop_id": loop_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "latest_cycle_path": _relative_posix(latest_path, root),
        "latest_cycle_status": latest_cycle_status,
        "latest_cycle_hash": latest_cycle_hash,
        "latest_cycle_recoverable": latest_cycle_recoverable,
        "canonical_jsonl_checked_count": len(jsonl_paths),
        "corrupted_jsonl_quarantined_count": corrupted_jsonl_quarantined_count,
        "ledger_jsonl_checked_count": len(ledger_jsonl_paths),
        "corrupted_ledger_jsonl_quarantined_count": corrupted_ledger_jsonl_quarantined_count,
        "ledger_jsonl_invalid_count": ledger_jsonl_invalid_count,
        "orphan_tmp_file_count": len(orphan_tmp_files),
        "artifact_paths": sorted(set(artifact_paths)),
        "recovery_guard_status": status,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "resume_action": "RESUME_PAPER_ONLY" if status == "PASS" else "SAFE_MODE_RECONCILE",
        "paper_runtime_resume_allowed": status == "PASS",
        "actual_long_run_evidence_created": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "guard_hash": "",
    }
    report["guard_hash"] = upbit_paper_runtime_recovery_guard_hash(report)
    return report


def write_upbit_paper_runtime_recovery_guard_report(*, root: Path, report: dict[str, Any]) -> Path:
    root = Path(root).resolve()
    runtime_dir = _runtime_base_dir(root, str(report["session_id"])) / "paper_runtime"
    path = runtime_dir / f"{report['guard_id']}.json"
    durable_atomic_write_json(path, report)
    canonical_path = runtime_dir / "upbit_paper_runtime_recovery_guard_report.json"
    if canonical_path != path:
        durable_atomic_write_json(canonical_path, report)
    return path


def _write_runtime_cycle_artifacts(*, root: Path, cycle: dict[str, Any]) -> dict[str, Any]:
    result = validate_upbit_paper_runtime_cycle_report(cycle)
    session_id = str(cycle.get("session_id", "UNKNOWN"))
    base = _runtime_base_dir(root, session_id)
    cycle_path = base / "paper_runtime" / "cycles" / f"{cycle.get('cycle_id')}.runtime_cycle.json"
    latest_path = base / "upbit_paper_runtime_cycle_report.json"
    writer_report_path = base / "paper_runtime" / "cycles" / f"{cycle.get('cycle_id')}.writer_report.json"
    ledger_path = base / "ledger" / "cycles" / f"{cycle.get('cycle_id')}.paper_ledger_events.jsonl"
    ledger_head_path = base / "ledger" / "latest_paper_ledger_head.json"
    if result.status != "PASS":
        writer = {
            "schema_id": "trader1.upbit_paper_runtime_cycle_writer_report.v1",
            "generated_at_utc": utc_now(),
            "project_id": "TRADER_1",
            "writer_status": "BLOCKED",
            "cycle_id": cycle.get("cycle_id"),
            "exchange": cycle.get("exchange"),
            "market_type": cycle.get("market_type"),
            "mode": cycle.get("mode"),
            "session_id": session_id,
            "primary_blocker_code": result.blocker_code,
            "blocker_message": result.message,
            "artifact_paths": [],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        durable_atomic_write_json(writer_report_path, writer)
        return writer
    durable_atomic_write_json(cycle_path, cycle)
    durable_atomic_write_json(latest_path, cycle)
    artifact_paths = [_relative_posix(cycle_path, root), _relative_posix(latest_path, root)]
    if cycle.get("paper_ledger_events"):
        durable_atomic_write_jsonl(ledger_path, cycle["paper_ledger_events"])
        ledger_head = {
            "schema_id": "trader1.paper_ledger_head.v1",
            "generated_at_utc": utc_now(),
            "project_id": "TRADER_1",
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": session_id,
            "cycle_id": cycle["cycle_id"],
            "ledger_event_count": len(cycle["paper_ledger_events"]),
            "ledger_events_path": _relative_posix(ledger_path, root),
            "ledger_head_hash": cycle["paper_ledger_head_hash"],
            "display_only": True,
            "dashboard_truth_only": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        ledger_head["head_report_hash"] = _sha256_json(ledger_head)
        durable_atomic_write_json(ledger_head_path, ledger_head)
        artifact_paths.extend([_relative_posix(ledger_path, root), _relative_posix(ledger_head_path, root)])
    writer = {
        "schema_id": "trader1.upbit_paper_runtime_cycle_writer_report.v1",
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "writer_status": "PASS",
        "cycle_id": cycle["cycle_id"],
        "exchange": cycle["exchange"],
        "market_type": cycle["market_type"],
        "mode": cycle["mode"],
        "session_id": session_id,
        "primary_blocker_code": None,
        "blocker_message": "PAPER runtime cycle artifacts written atomically; latest pointer remains PAPER-only",
        "artifact_paths": artifact_paths,
        "cycle_hash": cycle["cycle_hash"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    durable_atomic_write_json(writer_report_path, writer)
    return writer


def run_upbit_paper_persistent_loop(
    *,
    root: Path,
    loop_id: str,
    session_id: str = "mvp1_upbit_paper_launcher",
    symbol: str = "KRW-BTC",
    requested_cycle_count: int = 2,
    max_cycle_count: int = DEFAULT_MAX_CYCLE_COUNT,
    market_data_sequence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    blockers: list[dict[str, str]] = []
    cycle_results: list[dict[str, Any]] = []
    if requested_cycle_count < 1 or requested_cycle_count > max_cycle_count or max_cycle_count > DEFAULT_MAX_CYCLE_COUNT:
        blockers.append({"code": "RUNTIME_BUDGET_EXCEEDED", "severity": "HIGH", "message": "requested PAPER loop cycles exceed bounded MVP-4 budget"})
        requested_cycle_count = max(0, min(requested_cycle_count, max_cycle_count, DEFAULT_MAX_CYCLE_COUNT))
    for index in range(requested_cycle_count):
        collector_id = f"{loop_id}-collector-{index + 1}"
        cycle_id = f"{loop_id}-cycle-{index + 1}"
        supplied_market_data = market_data_sequence[index] if market_data_sequence and index < len(market_data_sequence) else None
        collection = build_upbit_public_market_data_collection_report(
            collector_id=collector_id,
            session_id=session_id,
            symbol=symbol,
            market_data=supplied_market_data,
        )
        collection_result = validate_upbit_public_market_data_collection_report(collection)
        collection_writer = write_upbit_public_market_data_collection_artifacts(root=root, report=collection)
        cycle: dict[str, Any] | None = None
        cycle_writer: dict[str, Any] | None = None
        cycle_result_status = "BLOCKED"
        cycle_result_blocker = collection_result.blocker_code
        if collection_result.status == "PASS" and collection_writer.get("writer_status") == "PASS":
            cycle = build_upbit_paper_runtime_cycle_report(
                cycle_id=cycle_id,
                session_id=session_id,
                symbol=symbol,
                source_collection_report=collection,
            )
            runtime_result = validate_upbit_paper_runtime_cycle_report(cycle)
            cycle_result_status = runtime_result.status
            cycle_result_blocker = runtime_result.blocker_code
            cycle_writer = _write_runtime_cycle_artifacts(root=root, cycle=cycle)
        else:
            blockers.append({"code": collection_result.blocker_code or "DATA_UNAVAILABLE", "severity": "HIGH", "message": collection_result.message})
        if cycle_result_status != "PASS":
            blockers.append({"code": cycle_result_blocker or "UNKNOWN_BLOCKED", "severity": "HIGH", "message": "PAPER runtime cycle did not pass"})
        cycle_results.append(
            {
                "cycle_index": index + 1,
                "collector_id": collector_id,
                "cycle_id": cycle_id,
                "collection_status": collection_result.status,
                "collection_hash": collection.get("collection_hash"),
                "collection_writer_status": collection_writer.get("writer_status"),
                "runtime_status": cycle_result_status,
                "runtime_cycle_hash": cycle.get("cycle_hash") if isinstance(cycle, dict) else None,
                "runtime_writer_status": cycle_writer.get("writer_status") if isinstance(cycle_writer, dict) else "NOT_WRITTEN",
                "final_decision": cycle.get("final_decision") if isinstance(cycle, dict) else "BLOCKED",
                "artifact_paths": [*(collection_writer.get("artifact_paths") or []), *(cycle_writer.get("artifact_paths") if isinstance(cycle_writer, dict) else [])],
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
    completed_count = sum(1 for item in cycle_results if item.get("runtime_status") == "PASS")
    recovery_guard = build_upbit_paper_runtime_recovery_guard_report(root=root, session_id=session_id, loop_id=loop_id)
    recovery_guard_path = write_upbit_paper_runtime_recovery_guard_report(root=root, report=recovery_guard)
    if recovery_guard.get("recovery_guard_status") != "PASS":
        blockers.append(
            {
                "code": recovery_guard.get("primary_blocker_code") or "RECONCILIATION_REQUIRED",
                "severity": "HIGH",
                "message": "PAPER runtime recovery guard blocked resume",
            }
        )
    ledger_rollup = build_paper_ledger_rollup_report(root=root, session_id=session_id, rollup_id=f"{loop_id}-ledger-rollup")
    ledger_rollup_path = write_paper_ledger_rollup_report(root=root, report=ledger_rollup)
    ledger_rollup_result = validate_paper_ledger_rollup_report(ledger_rollup)
    if ledger_rollup_result.status != "PASS":
        blockers.append(
            {
                "code": ledger_rollup_result.blocker_code or "RECONCILIATION_REQUIRED",
                "severity": "HIGH",
                "message": ledger_rollup_result.message,
            }
        )
    report = {
        "schema_id": UPBIT_PAPER_PERSISTENT_LOOP_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "loop_id": loop_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "symbol": symbol,
        "loop_mode": "BOUNDED_PUBLIC_DATA_PAPER_LOOP",
        "requested_cycle_count": requested_cycle_count,
        "completed_cycle_count": completed_count,
        "max_cycle_count": max_cycle_count,
        "cycle_results": cycle_results,
        "loop_status": "PASS" if completed_count == requested_cycle_count and not blockers else "BLOCKED",
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "actual_paper_runtime_executed": completed_count > 0,
        "recovery_guard_status": recovery_guard["recovery_guard_status"],
        "recovery_guard_hash": recovery_guard["guard_hash"],
        "recovery_guard_primary_blocker_code": recovery_guard["primary_blocker_code"],
        "runtime_recovery_guard_path": _relative_posix(recovery_guard_path, root),
        "paper_ledger_rollup_status": ledger_rollup["rollup_status"],
        "paper_ledger_rollup_hash": ledger_rollup["rollup_hash"],
        "paper_ledger_rollup_primary_blocker_code": ledger_rollup["primary_blocker_code"],
        "paper_ledger_rollup_path": _relative_posix(ledger_rollup_path, root),
        "paper_runtime_resume_allowed": recovery_guard["paper_runtime_resume_allowed"],
        "partial_write_recovery_required": recovery_guard["recovery_guard_status"] != "PASS",
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "data_source_policy": "PUBLIC_OR_STATIC_FIXTURE_ONLY",
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "loop_hash": "",
    }
    report["loop_hash"] = upbit_paper_persistent_loop_hash(report)
    loop_path = _runtime_base_dir(root, session_id) / "paper_runtime" / f"{loop_id}.persistent_loop_report.json"
    durable_atomic_write_json(loop_path, report)
    return report


def validate_upbit_paper_persistent_loop_report(report: dict[str, Any]) -> UpbitPaperPersistentLoopValidationResult:
    required = {
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
        "long_run_evidence_eligible",
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
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPersistentLoopValidationResult("FAIL", f"persistent loop report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_PERSISTENT_LOOP_SCHEMA_ID:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("loop_hash") != upbit_paper_persistent_loop_hash(report):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("requested_cycle_count") < 1 or report.get("requested_cycle_count") > report.get("max_cycle_count") or report.get("max_cycle_count") > DEFAULT_MAX_CYCLE_COUNT:
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop exceeds bounded cycle budget", "RUNTIME_BUDGET_EXCEEDED")
    forbidden_fields = (
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
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop attempted live, private, order, promotion, or scale-up behavior", "LIVE_FINAL_GUARD_FAILED")
    if report.get("recovery_guard_status") not in {"PASS", "BLOCKED"}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop recovery guard status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("recovery_guard_hash") in {None, ""}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop missing recovery guard hash", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("paper_ledger_rollup_status") not in {"PASS", "BLOCKED"}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop ledger rollup status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("paper_ledger_rollup_hash") in {None, ""}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop missing ledger rollup hash", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("paper_ledger_rollup_status") == "PASS" and report.get("paper_ledger_rollup_primary_blocker_code") is not None:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS ledger rollup cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("paper_ledger_rollup_status") == "BLOCKED" and report.get("paper_ledger_rollup_primary_blocker_code") is None:
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "blocked ledger rollup must expose primary blocker", "RECONCILIATION_REQUIRED")
    if report.get("recovery_guard_status") == "PASS":
        if report.get("recovery_guard_primary_blocker_code") is not None or report.get("partial_write_recovery_required"):
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS recovery guard cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("paper_runtime_resume_allowed") is not True:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS recovery guard must allow PAPER runtime resume", "SCHEMA_IDENTITY_MISMATCH")
    else:
        if report.get("paper_runtime_resume_allowed"):
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "blocked recovery guard cannot allow PAPER runtime resume", "RECONCILIATION_REQUIRED")
        if not report.get("partial_write_recovery_required"):
            return UpbitPaperPersistentLoopValidationResult("FAIL", "blocked recovery guard must expose recovery requirement", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("data_source_policy") != "PUBLIC_OR_STATIC_FIXTURE_ONLY":
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop data source policy is unsafe", "LIVE_FINAL_GUARD_FAILED")
    cycle_results = report.get("cycle_results")
    if not isinstance(cycle_results, list) or len(cycle_results) != report.get("requested_cycle_count"):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop cycle result count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    pass_count = 0
    for item in cycle_results:
        if item.get("collection_status") != "PASS" or item.get("collection_writer_status") != "PASS":
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop collection did not pass", "DATA_UNAVAILABLE")
        if item.get("runtime_status") != "PASS" or item.get("runtime_writer_status") != "PASS":
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop runtime cycle did not pass", "RECONCILIATION_REQUIRED")
        if not item.get("collection_hash") or not item.get("runtime_cycle_hash"):
            return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop missing source hashes", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("live_order_ready") or item.get("live_order_allowed") or item.get("can_live_trade") or item.get("scale_up_allowed"):
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop cycle result attempted live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
        pass_count += 1
    if report.get("completed_cycle_count") != pass_count:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop completed count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("loop_status") == "PASS" and report.get("primary_blocker_code") is not None:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS persistent loop cannot carry primary blocker", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("loop_status") == "PASS":
        return UpbitPaperPersistentLoopValidationResult("PASS", "Upbit PAPER persistent loop is bounded, public-data backed, and live-blocked", None)
    return UpbitPaperPersistentLoopValidationResult("BLOCKED", "Upbit PAPER persistent loop is blocked", report.get("primary_blocker_code") or "UNKNOWN_BLOCKED")


def validate_upbit_paper_runtime_recovery_guard_report(report: dict[str, Any]) -> UpbitPaperPersistentLoopValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "guard_id",
        "loop_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "latest_cycle_path",
        "latest_cycle_status",
        "latest_cycle_hash",
        "latest_cycle_recoverable",
        "canonical_jsonl_checked_count",
        "corrupted_jsonl_quarantined_count",
        "ledger_jsonl_checked_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "ledger_jsonl_invalid_count",
        "orphan_tmp_file_count",
        "artifact_paths",
        "recovery_guard_status",
        "primary_blocker_code",
        "blockers",
        "resume_action",
        "paper_runtime_resume_allowed",
        "actual_long_run_evidence_created",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "guard_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPersistentLoopValidationResult("FAIL", f"recovery guard report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_RUNTIME_RECOVERY_GUARD_SCHEMA_ID:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "recovery guard schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("guard_hash") != upbit_paper_runtime_recovery_guard_hash(report):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "recovery guard hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "recovery guard scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("actual_long_run_evidence_created") or report.get("promotion_eligible"):
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "recovery guard cannot create long-run or promotion evidence", "LIVE_FINAL_GUARD_FAILED")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("scale_up_allowed"):
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "recovery guard attempted live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "recovery guard blockers must be an array", "SCHEMA_IDENTITY_MISMATCH")
    blocker_codes = {item.get("code") for item in blockers if isinstance(item, dict)}
    if blockers and report.get("primary_blocker_code") not in blocker_codes:
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "recovery guard primary blocker mismatch", report.get("primary_blocker_code") or "UNKNOWN_BLOCKED")
    if not blockers and report.get("primary_blocker_code") is not None:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "recovery guard primary blocker set without blockers", "SCHEMA_IDENTITY_MISMATCH")
    for count_field in (
        "canonical_jsonl_checked_count",
        "corrupted_jsonl_quarantined_count",
        "ledger_jsonl_checked_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "ledger_jsonl_invalid_count",
        "orphan_tmp_file_count",
    ):
        if not isinstance(report.get(count_field), int) or report.get(count_field) < 0:
            return UpbitPaperPersistentLoopValidationResult("FAIL", f"recovery guard count is invalid: {count_field}", "SCHEMA_IDENTITY_MISMATCH")
    if (
        report.get("corrupted_jsonl_quarantined_count", 0) > 0
        or report.get("corrupted_ledger_jsonl_quarantined_count", 0) > 0
        or report.get("ledger_jsonl_invalid_count", 0) > 0
        or report.get("orphan_tmp_file_count", 0) > 0
    ):
        if report.get("recovery_guard_status") != "BLOCKED":
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "partial write recovery must block resume", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if report.get("latest_cycle_status") != "PASS" or report.get("latest_cycle_recoverable") is not True:
        if report.get("recovery_guard_status") != "BLOCKED":
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "unrecoverable latest cycle cannot pass guard", "RECONCILIATION_REQUIRED")
    if report.get("recovery_guard_status") == "PASS":
        if blockers:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS recovery guard cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("resume_action") != "RESUME_PAPER_ONLY" or report.get("paper_runtime_resume_allowed") is not True:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS recovery guard must resume PAPER only", "SCHEMA_IDENTITY_MISMATCH")
        return UpbitPaperPersistentLoopValidationResult("PASS", "Upbit PAPER runtime recovery guard is recoverable and live-blocked", None)
    if report.get("paper_runtime_resume_allowed") or report.get("resume_action") != "SAFE_MODE_RECONCILE":
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "blocked recovery guard must use safe reconcile", "RECONCILIATION_REQUIRED")
    return UpbitPaperPersistentLoopValidationResult("BLOCKED", "Upbit PAPER runtime recovery guard is blocked", report.get("primary_blocker_code") or "UNKNOWN_BLOCKED")
