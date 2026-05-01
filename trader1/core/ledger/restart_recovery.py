from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.core.events.intent_wal import build_intent_wal_from_ledger_events, validate_intent_wal_chain
from trader1.runtime.ledger.execution_ledger import build_minimal_intent_chain, validate_ledger_chain


RESTART_RECOVERY_SCHEMA_ID = "trader1.restart_recovery_report.v1"
DEFAULT_RECOVERY_ARTIFACT_PATHS = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/summary.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/heartbeat.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/launcher/root_launcher_report.json",
)


@dataclass(frozen=True)
class RestartRecoveryValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def restart_recovery_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("restart_recovery_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _is_safe_relative_artifact_path(path: Any) -> bool:
    if not isinstance(path, str) or not path:
        return False
    if "\\" in path or path.startswith("/") or path.startswith("//") or path.startswith("~"):
        return False
    if len(path) >= 2 and path[1] == ":" and path[0].isalpha():
        return False
    parts = path.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def build_restart_recovery_report(
    *,
    restart_id: str,
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "PAPER",
    session_id: str = "mvp2_restart_recovery",
    ledger_events: list[dict[str, Any]] | None = None,
    intent_wal_events: list[dict[str, Any]] | None = None,
    startup_recovery_rto_ms: int = 0,
    snapshot_recovery_rpo_events: int = 0,
    single_writer_recovered: bool = True,
    windows_path_recovery_checked: bool = True,
    atomic_write_recovery_checked: bool = True,
    partial_write_recovery_checked: bool = True,
    stale_lock_recovery_checked: bool = True,
    recovery_artifact_paths: list[str] | None = None,
) -> dict[str, Any]:
    if ledger_events is None:
        ledger_events = build_minimal_intent_chain(
            exchange=exchange,
            market_type=market_type,
            mode=mode,
            session_id=session_id,
            intent_id=f"{restart_id}-intent",
            client_order_id=f"{restart_id}-client",
            symbol="KRW-BTC",
            side="BUY",
        )
    if intent_wal_events is None:
        intent_wal_events = build_intent_wal_from_ledger_events(ledger_events)

    blockers: list[dict[str, str]] = []
    if exchange != "UPBIT" or market_type != "KRW_SPOT" or mode != "PAPER":
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "MVP-2 restart recovery is scoped to UPBIT/KRW_SPOT/PAPER"))

    ledger_result = validate_ledger_chain(ledger_events)
    if ledger_result.status != "PASS":
        blockers.append(_blocker(ledger_result.blocker_code or "LEDGER_UNAVAILABLE", ledger_result.message))
    wal_result = validate_intent_wal_chain(intent_wal_events)
    if wal_result.status != "PASS":
        blockers.append(_blocker(wal_result.blocker_code or "LEDGER_UNAVAILABLE", wal_result.message))
    if not single_writer_recovered:
        blockers.append(_blocker("RECONCILIATION_REQUIRED", "single-writer recovery is unavailable"))
    if not windows_path_recovery_checked:
        blockers.append(_blocker("RECONCILIATION_REQUIRED", "Windows recovery path evidence is unavailable"))
    if not atomic_write_recovery_checked:
        blockers.append(_blocker("RECONCILIATION_REQUIRED", "atomic write recovery evidence is unavailable"))
    if not partial_write_recovery_checked:
        blockers.append(_blocker("RECONCILIATION_REQUIRED", "partial-write recovery evidence is unavailable"))
    if not stale_lock_recovery_checked:
        blockers.append(_blocker("RECONCILIATION_REQUIRED", "stale lock recovery evidence is unavailable"))
    if recovery_artifact_paths is None:
        recovery_artifact_paths = list(DEFAULT_RECOVERY_ARTIFACT_PATHS)
    if not recovery_artifact_paths or not all(_is_safe_relative_artifact_path(path) for path in recovery_artifact_paths):
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "recovery artifact paths must be safe relative POSIX paths"))

    report = {
        "schema_id": RESTART_RECOVERY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "restart_id": restart_id,
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "recovery_scope": "PAPER_RESTART_ONLY",
        "startup_recovery_rto_ms": startup_recovery_rto_ms,
        "snapshot_recovery_rpo_events": snapshot_recovery_rpo_events,
        "ledger_events": ledger_events,
        "ledger_recovered": ledger_result.status == "PASS",
        "ledger_head_hash": ledger_events[-1]["event_hash"] if ledger_events else None,
        "intent_wal_events": intent_wal_events,
        "intent_wal_recovered": wal_result.status == "PASS",
        "intent_wal_head_hash": intent_wal_events[-1]["wal_event_hash"] if intent_wal_events else None,
        "single_writer_recovered": single_writer_recovered,
        "windows_path_recovery_checked": windows_path_recovery_checked,
        "atomic_write_recovery_checked": atomic_write_recovery_checked,
        "partial_write_recovery_checked": partial_write_recovery_checked,
        "stale_lock_recovery_checked": stale_lock_recovery_checked,
        "recovery_artifact_paths": recovery_artifact_paths,
        "paper_live_namespace_separated": mode == "PAPER",
        "recovery_action": "RESUME_PAPER_ONLY" if not blockers else "SAFE_MODE_RECONCILE",
        "restart_recovery_status": "PASS" if not blockers else "BLOCKED",
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "restart_recovery_hash": "",
    }
    report["restart_recovery_hash"] = restart_recovery_hash(report)
    return report


def validate_restart_recovery_report(
    report: dict[str, Any],
    allowed_blockers: set[str] | None = None,
) -> RestartRecoveryValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "restart_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "recovery_scope",
        "startup_recovery_rto_ms",
        "snapshot_recovery_rpo_events",
        "ledger_events",
        "ledger_recovered",
        "ledger_head_hash",
        "intent_wal_events",
        "intent_wal_recovered",
        "intent_wal_head_hash",
        "single_writer_recovered",
        "windows_path_recovery_checked",
        "atomic_write_recovery_checked",
        "partial_write_recovery_checked",
        "stale_lock_recovery_checked",
        "recovery_artifact_paths",
        "paper_live_namespace_separated",
        "recovery_action",
        "restart_recovery_status",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "restart_recovery_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return RestartRecoveryValidationResult("FAIL", f"restart recovery report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != RESTART_RECOVERY_SCHEMA_ID:
        return RestartRecoveryValidationResult("FAIL", "restart recovery schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("restart_recovery_hash") != restart_recovery_hash(report):
        return RestartRecoveryValidationResult("FAIL", "restart recovery hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return RestartRecoveryValidationResult("BLOCKED", "restart recovery scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("recovery_scope") != "PAPER_RESTART_ONLY":
        return RestartRecoveryValidationResult("BLOCKED", "restart recovery scope cannot imply live resume", "LIVE_FINAL_GUARD_FAILED")
    if report.get("live_key_loaded") or report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("can_submit_order"):
        return RestartRecoveryValidationResult("BLOCKED", "restart recovery attempted to create live or order permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("order_adapter_called"):
        return RestartRecoveryValidationResult("BLOCKED", "restart recovery cannot call an order adapter", "LIVE_FINAL_GUARD_FAILED")
    if report.get("paper_live_namespace_separated") is not True:
        return RestartRecoveryValidationResult("BLOCKED", "restart recovery lacks paper/live namespace separation", "SNAPSHOT_SCOPE_MISMATCH")
    for field in (
        "windows_path_recovery_checked",
        "atomic_write_recovery_checked",
        "partial_write_recovery_checked",
        "stale_lock_recovery_checked",
    ):
        if report.get(field) is not True:
            return RestartRecoveryValidationResult("BLOCKED", f"restart recovery missing required evidence: {field}", "RECONCILIATION_REQUIRED")
    artifact_paths = report.get("recovery_artifact_paths")
    if not isinstance(artifact_paths, list) or not artifact_paths:
        return RestartRecoveryValidationResult("BLOCKED", "restart recovery artifact paths are missing", "RECONCILIATION_REQUIRED")
    for artifact_path in artifact_paths:
        if not _is_safe_relative_artifact_path(artifact_path):
            return RestartRecoveryValidationResult(
                "BLOCKED",
                "restart recovery artifact paths must be safe relative POSIX paths",
                "SNAPSHOT_SCOPE_MISMATCH",
            )

    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return RestartRecoveryValidationResult("FAIL", "restart recovery blockers must be an array", "SCHEMA_IDENTITY_MISMATCH")
    for blocker in blockers:
        code = blocker.get("code") if isinstance(blocker, dict) else None
        if allowed_blockers is not None and code not in allowed_blockers:
            return RestartRecoveryValidationResult("FAIL", f"unknown restart recovery blocker: {code}", "UNKNOWN_BLOCKED")
    primary = report.get("primary_blocker_code")
    blocker_codes = {blocker.get("code") for blocker in blockers if isinstance(blocker, dict)}
    if blockers and primary not in blocker_codes:
        return RestartRecoveryValidationResult("BLOCKED", "primary blocker must match blockers", primary or "UNKNOWN_BLOCKED")
    if not blockers and primary is not None:
        return RestartRecoveryValidationResult("FAIL", "primary blocker set without blockers", "LIVE_FINAL_GUARD_FAILED")

    ledger_result = validate_ledger_chain(report.get("ledger_events", []))
    wal_result = validate_intent_wal_chain(report.get("intent_wal_events", []))
    if ledger_result.status != "PASS":
        return RestartRecoveryValidationResult("BLOCKED", ledger_result.message, ledger_result.blocker_code or "LEDGER_UNAVAILABLE")
    if wal_result.status != "PASS":
        return RestartRecoveryValidationResult("BLOCKED", wal_result.message, wal_result.blocker_code or "LEDGER_UNAVAILABLE")
    if report.get("ledger_recovered") is not True:
        return RestartRecoveryValidationResult("FAIL", "ledger_recovered flag does not match recovered ledger chain", "LEDGER_INTEGRITY_FAIL")
    if report.get("intent_wal_recovered") is not True:
        return RestartRecoveryValidationResult("FAIL", "intent_wal_recovered flag does not match recovered WAL chain", "LEDGER_INTEGRITY_FAIL")
    ledger_events = report.get("ledger_events", [])
    wal_events = report.get("intent_wal_events", [])
    ledger_event_hashes = {event.get("event_hash") for event in ledger_events if isinstance(event, dict)}
    wal_source_hashes = {event.get("source_ledger_event_hash") for event in wal_events if isinstance(event, dict)}
    if not wal_source_hashes.issubset(ledger_event_hashes):
        return RestartRecoveryValidationResult(
            "BLOCKED",
            "intent WAL references a ledger event outside the recovered ledger chain",
            "RECONCILIATION_REQUIRED",
        )
    intent_ledger_hashes = {
        event.get("event_hash")
        for event in ledger_events
        if isinstance(event, dict) and event.get("intent_id") and event.get("client_order_id")
    }
    if not intent_ledger_hashes.issubset(wal_source_hashes):
        return RestartRecoveryValidationResult(
            "BLOCKED",
            "intent WAL is missing a recovered idempotent ledger event",
            "RECONCILIATION_REQUIRED",
        )
    if report.get("ledger_head_hash") != ledger_events[-1]["event_hash"]:
        return RestartRecoveryValidationResult("FAIL", "ledger head hash mismatch", "LEDGER_INTEGRITY_FAIL")
    if report.get("intent_wal_head_hash") != wal_events[-1]["wal_event_hash"]:
        return RestartRecoveryValidationResult("FAIL", "intent WAL head hash mismatch", "LEDGER_INTEGRITY_FAIL")
    if report.get("single_writer_recovered") is not True:
        if (
            report.get("restart_recovery_status") == "PASS"
            or report.get("recovery_action") != "SAFE_MODE_RECONCILE"
            or "RECONCILIATION_REQUIRED" not in blocker_codes
        ):
            return RestartRecoveryValidationResult(
                "BLOCKED",
                "single-writer recovery unavailable cannot be reported as recovered",
                "RECONCILIATION_REQUIRED",
            )
    if report.get("restart_recovery_status") == "PASS" and blockers:
        return RestartRecoveryValidationResult("BLOCKED", "restart recovery PASS cannot carry blockers", primary or "UNKNOWN_BLOCKED")
    if report.get("restart_recovery_status") == "PASS" and report.get("recovery_action") != "RESUME_PAPER_ONLY":
        return RestartRecoveryValidationResult("BLOCKED", "paper restart PASS must only resume paper mode", "LIVE_FINAL_GUARD_FAILED")
    return RestartRecoveryValidationResult("PASS", "paper restart recovery is WAL-backed, ledger-checked, and live-blocked", None)
