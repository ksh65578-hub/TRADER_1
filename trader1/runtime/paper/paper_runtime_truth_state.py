from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.health.heartbeat import validate_heartbeat
from trader1.runtime.ledger.paper_ledger_rollup import validate_paper_ledger_rollup_report
from trader1.runtime.paper.upbit_paper_persistent_loop import validate_upbit_paper_persistent_loop_report
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json
from trader1.runtime.paper.upbit_public_rest_continuity_history import (
    validate_upbit_public_rest_continuity_history_report,
)
from trader1.runtime.portfolio.paper_current_truth_refresh import (
    PAPER_CURRENT_TRUTH_REFRESH_PASS_STATUS,
    validate_paper_current_truth_refresh_report,
)


PAPER_RUNTIME_TRUTH_STATE_SCHEMA_ID = "trader1.paper_runtime_truth_state_report.v1"
PAPER_RUNTIME_ACTIVE_STATUS = "PAPER_RUNTIME_ACTIVE"
MONITOR_ALIVE_ENGINE_NOT_PROVEN_STATUS = "MONITOR_ALIVE_ENGINE_NOT_PROVEN"
PAPER_RUNTIME_BLOCKED_STATUS = "PAPER_RUNTIME_BLOCKED"
PAPER_RUNTIME_NOT_LOADED_STATUS = "PAPER_RUNTIME_NOT_LOADED"
PAPER_RUNTIME_INVALID_STATUS = "INVALID"
PAPER_RUNTIME_TRUTH_STATUSES = {
    PAPER_RUNTIME_ACTIVE_STATUS,
    MONITOR_ALIVE_ENGINE_NOT_PROVEN_STATUS,
    PAPER_RUNTIME_BLOCKED_STATUS,
    PAPER_RUNTIME_NOT_LOADED_STATUS,
    PAPER_RUNTIME_INVALID_STATUS,
}
FRESH_CURRENT_TRUTH_STATUS = "FRESH_CURRENT_TRUTH"
STALE_DISPLAY_TRUTH_STATUS = "STALE_DISPLAY_TRUTH"
MONITOR_ONLY_TRUTH_STATUS = "MONITOR_ONLY"
INVALID_TRUTH_STATUS = "INVALID"
PAPER_RUNTIME_TRUTH_ROLE = "PAPER_RUNTIME_TRUTH_STATE_ONLY_NOT_LIVE_READY"
PAPER_RUNTIME_SOURCE_FRESH_SECONDS = 300.0


@dataclass(frozen=True)
class PaperRuntimeTruthStateValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def paper_runtime_truth_state_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("truth_state_hash", None)
    return _sha256_json(payload)


def _hash_from(report: dict[str, Any] | None, field: str) -> str | None:
    if not isinstance(report, dict):
        return None
    value = report.get(field)
    return value if isinstance(value, str) and len(value) == 64 else None


def _int_at_least(value: Any, minimum: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return minimum
    return parsed if parsed >= minimum else minimum


def _parse_utc_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _source_age_seconds(report: dict[str, Any] | None, now: datetime) -> float | None:
    if not isinstance(report, dict):
        return None
    generated_at = _parse_utc_timestamp(report.get("generated_at_utc"))
    if generated_at is None:
        return None
    return max(0.0, (now - generated_at).total_seconds())


def _source_fresh(report: dict[str, Any] | None, now: datetime) -> bool:
    age_seconds = _source_age_seconds(report, now)
    return age_seconds is not None and age_seconds <= PAPER_RUNTIME_SOURCE_FRESH_SECONDS


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _scoped(report: dict[str, Any] | None, *, exchange: str, market_type: str, mode: str, session_id: str) -> bool:
    return (
        isinstance(report, dict)
        and report.get("exchange") == exchange
        and report.get("market_type") == market_type
        and report.get("mode") == mode
        and report.get("session_id") == session_id
    )


def build_paper_runtime_truth_state_report(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    heartbeat: dict[str, Any] | None,
    upbit_paper_persistent_loop_report: dict[str, Any] | None,
    upbit_public_rest_continuity_history: dict[str, Any] | None,
    paper_ledger_rollup_report: dict[str, Any] | None,
    paper_current_truth_refresh_report: dict[str, Any] | None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    now = generated_at_utc or utc_now()
    now_dt = _parse_utc_timestamp(now) or datetime.now(timezone.utc)
    blockers: list[dict[str, str]] = []

    paper_scope = exchange == "UPBIT" and market_type == "KRW_SPOT" and mode == "PAPER"
    heartbeat_scoped = _scoped(heartbeat, exchange=exchange, market_type=market_type, mode=mode, session_id=session_id)
    heartbeat_result = validate_heartbeat(heartbeat) if isinstance(heartbeat, dict) else None
    heartbeat_status = heartbeat.get("heartbeat_status") if isinstance(heartbeat, dict) else None
    heartbeat_primary_blocker = heartbeat.get("primary_blocker_code") if isinstance(heartbeat, dict) else None
    heartbeat_blocker_code = (
        heartbeat_primary_blocker
        if isinstance(heartbeat_primary_blocker, str) and heartbeat_primary_blocker
        else heartbeat_result.blocker_code
        if heartbeat_result is not None
        else None
    )
    monitor_alive = bool(
        paper_scope
        and heartbeat_scoped
        and heartbeat_result is not None
        and heartbeat_result.status == "PASS"
        and heartbeat_status == "PASS"
    )
    if paper_scope and not monitor_alive:
        blockers.append(
            _blocker(
                heartbeat_blocker_code or "LATENCY_TTL_EXPIRED",
                (
                    "PAPER monitor heartbeat is not executable for current truth: "
                    f"heartbeat_status={heartbeat_status or 'MISSING'}; "
                    f"blocker={heartbeat_blocker_code or 'LATENCY_TTL_EXPIRED'}"
                ),
            )
        )

    loop_scoped = _scoped(
        upbit_paper_persistent_loop_report,
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
    )
    loop_result = (
        validate_upbit_paper_persistent_loop_report(upbit_paper_persistent_loop_report)
        if isinstance(upbit_paper_persistent_loop_report, dict)
        else None
    )
    completed_cycle_count = _int_at_least(
        upbit_paper_persistent_loop_report.get("completed_cycle_count")
        if isinstance(upbit_paper_persistent_loop_report, dict)
        else 0
    )
    loop_fresh = _source_fresh(upbit_paper_persistent_loop_report, now_dt)
    paper_loop_advancing = bool(
        paper_scope
        and loop_scoped
        and loop_result is not None
        and loop_result.status == "PASS"
        and upbit_paper_persistent_loop_report.get("loop_status") == "PASS"
        and completed_cycle_count > 0
        and upbit_paper_persistent_loop_report.get("actual_paper_runtime_executed") is True
        and loop_fresh
    )
    if paper_scope and not paper_loop_advancing:
        loop_was_valid_but_stale = bool(
            loop_scoped
            and loop_result is not None
            and loop_result.status == "PASS"
            and isinstance(upbit_paper_persistent_loop_report, dict)
            and upbit_paper_persistent_loop_report.get("loop_status") == "PASS"
            and completed_cycle_count > 0
            and upbit_paper_persistent_loop_report.get("actual_paper_runtime_executed") is True
            and not loop_fresh
        )
        blockers.append(
            _blocker(
                "LATENCY_TTL_EXPIRED"
                if loop_was_valid_but_stale
                else loop_result.blocker_code
                if loop_result is not None and loop_result.blocker_code
                else "ACTUAL_PAPER_RUNTIME_EXECUTION_MISSING",
                "Validated PAPER loop report is stale and no longer proves an advancing PAPER loop"
                if loop_was_valid_but_stale
                else "PAPER heartbeat exists but a validated advancing PAPER loop is not loaded",
            )
        )

    continuity_scoped = _scoped(
        upbit_public_rest_continuity_history,
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
    )
    continuity_result = (
        validate_upbit_public_rest_continuity_history_report(upbit_public_rest_continuity_history)
        if isinstance(upbit_public_rest_continuity_history, dict)
        else None
    )
    continuity_fresh = _source_fresh(upbit_public_rest_continuity_history, now_dt)
    market_data_advancing = bool(
        paper_scope
        and continuity_scoped
        and continuity_result is not None
        and continuity_result.status == "PASS"
        and upbit_public_rest_continuity_history.get("continuity_health_status") == "PASS"
        and continuity_fresh
    )
    if paper_scope and not market_data_advancing:
        continuity_was_valid_but_stale = bool(
            continuity_scoped
            and continuity_result is not None
            and continuity_result.status == "PASS"
            and isinstance(upbit_public_rest_continuity_history, dict)
            and upbit_public_rest_continuity_history.get("continuity_health_status") == "PASS"
            and not continuity_fresh
        )
        blockers.append(
            _blocker(
                "LATENCY_TTL_EXPIRED"
                if continuity_was_valid_but_stale
                else continuity_result.blocker_code
                if continuity_result is not None and continuity_result.blocker_code
                else "DATA_UNAVAILABLE",
                "PAPER public market-data continuity report is stale and no longer proves advancing data"
                if continuity_was_valid_but_stale
                else "PAPER public market-data continuity is not PASS for this scoped session",
            )
        )

    ledger_scoped = _scoped(
        paper_ledger_rollup_report,
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
    )
    ledger_result = (
        validate_paper_ledger_rollup_report(paper_ledger_rollup_report)
        if isinstance(paper_ledger_rollup_report, dict)
        else None
    )
    ledger_event_count = _int_at_least(
        paper_ledger_rollup_report.get("ledger_event_count") if isinstance(paper_ledger_rollup_report, dict) else 0
    )
    ledger_fresh = _source_fresh(paper_ledger_rollup_report, now_dt)
    ledger_advancing = bool(
        paper_scope
        and ledger_scoped
        and ledger_result is not None
        and ledger_result.status == "PASS"
        and paper_ledger_rollup_report.get("rollup_status") == "PASS"
        and ledger_event_count > 0
        and isinstance(paper_ledger_rollup_report.get("latest_ledger_head_hash"), str)
        and ledger_fresh
    )
    if paper_scope and not ledger_advancing:
        ledger_was_valid_but_stale = bool(
            ledger_scoped
            and ledger_result is not None
            and ledger_result.status == "PASS"
            and isinstance(paper_ledger_rollup_report, dict)
            and paper_ledger_rollup_report.get("rollup_status") == "PASS"
            and ledger_event_count > 0
            and isinstance(paper_ledger_rollup_report.get("latest_ledger_head_hash"), str)
            and not ledger_fresh
        )
        blockers.append(
            _blocker(
                "LATENCY_TTL_EXPIRED"
                if ledger_was_valid_but_stale
                else ledger_result.blocker_code
                if ledger_result is not None and ledger_result.blocker_code
                else "LEDGER_UNAVAILABLE",
                "PAPER ledger rollup is stale and no longer proves current ledger advancement"
                if ledger_was_valid_but_stale
                else "PAPER ledger rollup is missing, stale, invalid, or has no advancing ledger head",
            )
        )

    refresh_scoped = _scoped(
        paper_current_truth_refresh_report,
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
    )
    refresh_result = (
        validate_paper_current_truth_refresh_report(paper_current_truth_refresh_report)
        if isinstance(paper_current_truth_refresh_report, dict)
        else None
    )
    refresh_fresh = _source_fresh(paper_current_truth_refresh_report, now_dt)
    current_evidence_refreshing = bool(
        paper_scope
        and refresh_scoped
        and refresh_result is not None
        and refresh_result.status == "PASS"
        and paper_current_truth_refresh_report.get("refresh_status") == PAPER_CURRENT_TRUTH_REFRESH_PASS_STATUS
        and paper_current_truth_refresh_report.get("refresh_passed") is True
        and refresh_fresh
    )
    if paper_scope and not current_evidence_refreshing:
        refresh_was_valid_but_stale = bool(
            refresh_scoped
            and refresh_result is not None
            and refresh_result.status == "PASS"
            and isinstance(paper_current_truth_refresh_report, dict)
            and paper_current_truth_refresh_report.get("refresh_status") == PAPER_CURRENT_TRUTH_REFRESH_PASS_STATUS
            and paper_current_truth_refresh_report.get("refresh_passed") is True
            and not refresh_fresh
        )
        blockers.append(
            _blocker(
                "LATENCY_TTL_EXPIRED"
                if refresh_was_valid_but_stale
                else refresh_result.blocker_code
                if refresh_result is not None and refresh_result.blocker_code
                else "HARD_TRUTH_MISSING",
                "PAPER current-evidence refresh report is stale and no longer proves current truth"
                if refresh_was_valid_but_stale
                else "PAPER current-evidence refresh is not passing for this scoped session",
            )
        )

    if not paper_scope:
        runtime_truth_status = PAPER_RUNTIME_INVALID_STATUS
        dashboard_truth_status = INVALID_TRUTH_STATUS
        blockers = [_blocker("LIVE_FINAL_GUARD_FAILED", "runtime truth state is PAPER-only and cannot run for this scope")]
        state_summary = "Runtime truth state is not available outside UPBIT/KRW_SPOT/PAPER."
        next_action = "Use PAPER mode for runtime truth collection; live remains blocked."
    elif not monitor_alive:
        runtime_truth_status = PAPER_RUNTIME_NOT_LOADED_STATUS
        dashboard_truth_status = MONITOR_ONLY_TRUTH_STATUS
        state_summary = "PAPER monitor is not proven alive."
        next_action = "Rerun the PAPER launcher and wait for a fresh heartbeat before reviewing runtime truth."
    elif monitor_alive and not paper_loop_advancing:
        runtime_truth_status = MONITOR_ALIVE_ENGINE_NOT_PROVEN_STATUS
        dashboard_truth_status = MONITOR_ONLY_TRUTH_STATUS
        state_summary = "Monitor alive, PAPER engine not proven."
        next_action = "Run the scoped PAPER runtime loop so ledger, market data, and current evidence can advance."
    elif paper_loop_advancing and market_data_advancing and ledger_advancing and current_evidence_refreshing:
        runtime_truth_status = PAPER_RUNTIME_ACTIVE_STATUS
        dashboard_truth_status = FRESH_CURRENT_TRUTH_STATUS
        state_summary = "PAPER runtime active: loop, market data, ledger, and current evidence are refreshed."
        next_action = "Keep collecting PAPER/SHADOW evidence; live and scale remain blocked."
    else:
        runtime_truth_status = PAPER_RUNTIME_BLOCKED_STATUS
        dashboard_truth_status = STALE_DISPLAY_TRUTH_STATUS
        state_summary = "PAPER runtime is partially connected, but current truth is not fully refreshed."
        next_action = "Refresh the blocked PAPER source listed by primary_blocker_code before using current truth."

    report = {
        "schema_id": PAPER_RUNTIME_TRUTH_STATE_SCHEMA_ID,
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "runtime_truth_status": runtime_truth_status,
        "dashboard_truth_status": dashboard_truth_status,
        "state_summary": state_summary,
        "next_action": next_action,
        "monitor_alive": monitor_alive,
        "paper_loop_advancing": paper_loop_advancing,
        "market_data_advancing": market_data_advancing,
        "ledger_advancing": ledger_advancing,
        "current_evidence_refreshing": current_evidence_refreshing,
        "validated_paper_cycle_count": completed_cycle_count,
        "validated_paper_ledger_event_count": ledger_event_count,
        "source_heartbeat_hash": _hash_from(heartbeat, "heartbeat_hash"),
        "source_persistent_loop_hash": _hash_from(upbit_paper_persistent_loop_report, "loop_hash"),
        "source_market_continuity_history_hash": _hash_from(upbit_public_rest_continuity_history, "history_hash"),
        "source_paper_ledger_rollup_hash": _hash_from(paper_ledger_rollup_report, "rollup_hash"),
        "source_current_truth_refresh_hash": _hash_from(paper_current_truth_refresh_report, "refresh_report_hash"),
        "primary_blocker_code": blockers[0]["code"] if blockers else "LIVE_READY_MISSING",
        "blockers": blockers,
        "evidence_role": PAPER_RUNTIME_TRUTH_ROLE,
        "paper_only": True,
        "display_only": True,
        "dashboard_truth_only": True,
        "current_trading_review_allowed": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "credential_load_attempted": False,
        "authorization_header_present": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_ready_write_allowed": False,
        "live_config_mutation_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "scale_up_allowed": False,
        "truth_state_hash": "",
    }
    report["truth_state_hash"] = paper_runtime_truth_state_hash(report)
    return report


def validate_paper_runtime_truth_state_report(
    report: dict[str, Any],
) -> PaperRuntimeTruthStateValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "runtime_truth_status",
        "dashboard_truth_status",
        "state_summary",
        "next_action",
        "monitor_alive",
        "paper_loop_advancing",
        "market_data_advancing",
        "ledger_advancing",
        "current_evidence_refreshing",
        "validated_paper_cycle_count",
        "validated_paper_ledger_event_count",
        "source_heartbeat_hash",
        "source_persistent_loop_hash",
        "source_market_continuity_history_hash",
        "source_paper_ledger_rollup_hash",
        "source_current_truth_refresh_hash",
        "primary_blocker_code",
        "blockers",
        "evidence_role",
        "paper_only",
        "display_only",
        "dashboard_truth_only",
        "current_trading_review_allowed",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "authorization_header_present",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
        "truth_state_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return PaperRuntimeTruthStateValidationResult("FAIL", f"runtime truth state missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != PAPER_RUNTIME_TRUTH_STATE_SCHEMA_ID:
        return PaperRuntimeTruthStateValidationResult("FAIL", "runtime truth state schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("truth_state_hash") != paper_runtime_truth_state_hash(report):
        return PaperRuntimeTruthStateValidationResult("FAIL", "runtime truth state hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return PaperRuntimeTruthStateValidationResult("BLOCKED", "runtime truth state must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("runtime_truth_status") not in PAPER_RUNTIME_TRUTH_STATUSES:
        return PaperRuntimeTruthStateValidationResult("FAIL", "unknown runtime truth status", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("dashboard_truth_status") not in {
        FRESH_CURRENT_TRUTH_STATUS,
        STALE_DISPLAY_TRUTH_STATUS,
        MONITOR_ONLY_TRUTH_STATUS,
        INVALID_TRUTH_STATUS,
    }:
        return PaperRuntimeTruthStateValidationResult("FAIL", "unknown dashboard truth status", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("evidence_role") != PAPER_RUNTIME_TRUTH_ROLE:
        return PaperRuntimeTruthStateValidationResult("BLOCKED", "runtime truth role must not imply LIVE_READY", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "current_trading_review_allowed",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "authorization_header_present",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden):
        return PaperRuntimeTruthStateValidationResult("BLOCKED", "runtime truth state attempted live, order, promotion, or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("paper_only") is not True or report.get("display_only") is not True or report.get("dashboard_truth_only") is not True:
        return PaperRuntimeTruthStateValidationResult("BLOCKED", "runtime truth state must remain PAPER display truth only", "LIVE_FINAL_GUARD_FAILED")
    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return PaperRuntimeTruthStateValidationResult("FAIL", "runtime truth blockers must be an array", "SCHEMA_IDENTITY_MISMATCH")
    for field in (
        "monitor_alive",
        "paper_loop_advancing",
        "market_data_advancing",
        "ledger_advancing",
        "current_evidence_refreshing",
    ):
        if not isinstance(report.get(field), bool):
            return PaperRuntimeTruthStateValidationResult("FAIL", f"runtime truth field must be boolean: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("runtime_truth_status") == PAPER_RUNTIME_ACTIVE_STATUS:
        if any(
            report.get(field) is not True
            for field in (
                "monitor_alive",
                "paper_loop_advancing",
                "market_data_advancing",
                "ledger_advancing",
                "current_evidence_refreshing",
            )
        ):
            return PaperRuntimeTruthStateValidationResult("FAIL", "active PAPER runtime truth requires all source checks true", "SCHEMA_IDENTITY_MISMATCH")
        if blockers or report.get("dashboard_truth_status") != FRESH_CURRENT_TRUTH_STATUS:
            return PaperRuntimeTruthStateValidationResult("FAIL", "active PAPER runtime truth cannot carry blockers or stale display status", "SCHEMA_IDENTITY_MISMATCH")
        return PaperRuntimeTruthStateValidationResult("PASS", "PAPER runtime truth is active and PAPER-only", None)
    if report.get("runtime_truth_status") == MONITOR_ALIVE_ENGINE_NOT_PROVEN_STATUS:
        if report.get("monitor_alive") is not True or report.get("paper_loop_advancing") is not False:
            return PaperRuntimeTruthStateValidationResult("FAIL", "monitor-only status requires alive monitor and unproven loop", "SCHEMA_IDENTITY_MISMATCH")
    if not blockers or not isinstance(report.get("primary_blocker_code"), str) or not report.get("primary_blocker_code"):
        return PaperRuntimeTruthStateValidationResult("BLOCKED", "blocked runtime truth must expose a primary blocker", "HARD_TRUTH_MISSING")
    return PaperRuntimeTruthStateValidationResult("BLOCKED", "PAPER runtime truth is not fully active", report.get("primary_blocker_code"))


def write_paper_runtime_truth_state_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = (
        Path(root).resolve()
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(report["session_id"])
        / "paper_runtime"
        / "paper_runtime_truth_state_report.json"
    )
    durable_atomic_write_json(path, report)
    return path
