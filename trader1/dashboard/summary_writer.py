from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.runtime.portfolio.paper_portfolio import validate_paper_portfolio_snapshot


SUMMARY_SCHEMA_ID = "trader1.summary.v1"
ORDER_AFFECTING_FINAL_ACTIONS = {
    "ENTER_LONG",
    "ENTER_SHORT",
    "EXIT_POSITION",
    "REDUCE_POSITION",
    "CANCEL_ORDER",
    "HOLD_POSITION",
}


@dataclass(frozen=True)
class SummaryValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _status_source(
    *,
    status: str,
    source: str,
    freshness_status: str,
    message: str | None = None,
    evidence_id: str | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "source": source,
        "freshness_status": freshness_status,
        "evidence_id": evidence_id,
        "message": message,
    }


def _first_blocker(*codes: str | None) -> str | None:
    for code in codes:
        if code:
            return code
    return None


def _empty_portfolio() -> dict[str, Any]:
    return {
        "source": "SUMMARY_BUILDER",
        "freshness_status": "UNTESTED",
        "equity": None,
        "cash_available": None,
        "locked_balance": None,
        "position_market_value": None,
        "open_position_count": 0,
        "realized_pnl": None,
        "unrealized_pnl": None,
        "total_pnl": None,
        "mdd": None,
    }


def _portfolio_from_paper_snapshot(
    snapshot: dict[str, Any] | None,
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not isinstance(snapshot, dict):
        return _empty_portfolio(), []
    result = validate_paper_portfolio_snapshot(snapshot)
    scope_matches = (
        snapshot.get("exchange") == exchange
        and snapshot.get("market_type") == market_type
        and snapshot.get("mode") == mode
        and snapshot.get("session_id") == session_id
    )
    if result.status != "PASS" or not scope_matches:
        return _empty_portfolio(), []
    return (
        {
            "source": "LEDGER",
            "freshness_status": "PASS",
            "equity": float(snapshot["equity"]),
            "cash_available": float(snapshot["cash_available"]),
            "locked_balance": float(snapshot["locked_balance"]),
            "position_market_value": float(snapshot.get("position_market_value", 0)),
            "open_position_count": int(snapshot.get("open_position_count", len(snapshot.get("positions", [])))),
            "realized_pnl": float(snapshot["realized_pnl"]),
            "unrealized_pnl": float(snapshot["unrealized_pnl"]),
            "total_pnl": float(snapshot.get("total_pnl", 0)),
            "mdd": 0.0,
        },
        list(snapshot.get("positions", [])),
    )


def build_summary_shell(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    startup_probe: dict[str, Any] | None,
    heartbeat: dict[str, Any] | None,
    readiness_surface: dict[str, Any] | None,
    paper_portfolio_snapshot: dict[str, Any] | None = None,
    entry_candidates: list[dict[str, Any]] | None = None,
    recent_entry_context: list[dict[str, Any]] | None = None,
    recent_no_trade_context: list[dict[str, Any]] | None = None,
    market_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    startup_blocker = startup_probe.get("primary_blocker_code") if startup_probe else "HARD_TRUTH_MISSING"
    heartbeat_blocker = heartbeat.get("primary_blocker_code") if heartbeat else "LATENCY_TTL_EXPIRED"
    readiness_blocker = readiness_surface.get("primary_blocker_code") if readiness_surface else "LIVE_READY_MISSING"
    primary_blocker = _first_blocker(startup_blocker, heartbeat_blocker, readiness_blocker)

    startup_passed = bool(startup_probe and startup_probe.get("startup_probe_passed"))
    heartbeat_status = heartbeat.get("heartbeat_status") if heartbeat else "STALE"
    heartbeat_freshness = "PASS" if heartbeat_status == "PASS" else "FAIL"
    start_message = startup_probe.get("next_action") if startup_probe else "startup probe missing"
    heartbeat_message = heartbeat.get("next_action") if heartbeat else "heartbeat missing"
    readiness_message = readiness_surface.get("primary_blocker_message") if readiness_surface else "LIVE_READY snapshot missing"
    portfolio, positions = _portfolio_from_paper_snapshot(
        paper_portfolio_snapshot,
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
    )

    summary = {
        "schema_id": SUMMARY_SCHEMA_ID,
        "project": "TRADER_1",
        "generated_at_utc": utc_now(),
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "engine": _status_source(
            status="BOOTSTRAP_READ_ONLY" if startup_passed else "SAFE_MODE",
            source="STARTUP_PROBE",
            freshness_status="PASS" if startup_probe else "STALE",
            message=start_message,
        ),
        "startup": _status_source(
            status="PASS" if startup_passed else "BLOCKED",
            source="STARTUP_PROBE",
            freshness_status="PASS" if startup_probe else "STALE",
            message=start_message,
        ),
        "operator_status": _status_source(
            status="UNTESTED",
            source="OPERATOR",
            freshness_status="UNTESTED",
            message="operator surface not implemented in MVP-1 summary shell",
        ),
        "connectivity": _status_source(
            status=heartbeat_status or "UNTESTED",
            source="HEARTBEAT",
            freshness_status=heartbeat_freshness,
            message=heartbeat_message,
        ),
        "caches": {},
        "queues": {},
        "rate_limits": {},
        "resources": _status_source(
            status=heartbeat_status or "UNTESTED",
            source="HEARTBEAT",
            freshness_status=heartbeat_freshness,
            message=heartbeat_message,
        ),
        "portfolio": portfolio,
        "orders": {
            "source": "SUMMARY_BUILDER",
            "freshness_status": "UNTESTED",
            "open_order_count": 0,
            "pending_confirm_count": 0,
            "reconciliation_age_sec": None,
        },
        "watch_universe": [],
        "entry_candidates": entry_candidates or [],
        "positions": positions,
        "strategies": [],
        "market_context": market_context
        or {
            "source": "SUMMARY_BUILDER",
            "freshness_status": "UNTESTED",
            "regime": None,
            "liquidity_status": None,
            "volatility_status": None,
        },
        "action_queue": [],
        "recent_errors": [],
        "recent_no_trade_context": recent_no_trade_context or [],
        "recent_entry_context": recent_entry_context or [],
        "fee_snapshot": None,
        "live_ready": {
            "source": "READINESS_SURFACE" if readiness_surface else "SUMMARY_BUILDER",
            "live_order_ready": False,
            "live_order_allowed": False,
            "primary_blocker_code": readiness_blocker,
            "primary_blocker_message": readiness_message,
            "blocks_live_order": True,
            "evidence_id": None,
        },
        "applied_snapshot": {
            "snapshot_id": None,
            "source": "NONE",
            "scope_hash": None,
            "freshness_status": "UNTESTED",
        },
        "final_action": "NO_TRADE" if primary_blocker else "SAFE_MODE",
        "blocking_reason": primary_blocker,
        "next_action": "resolve blocking reason before trading" if primary_blocker else "continue read-only dashboard shell",
    }
    return summary


def validate_summary_shell(summary: dict[str, Any], allowed_blockers: set[str] | None = None) -> SummaryValidationResult:
    if summary.get("schema_id") != SUMMARY_SCHEMA_ID:
        return SummaryValidationResult("FAIL", "summary schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if summary.get("project") != "TRADER_1":
        return SummaryValidationResult("FAIL", "summary project mismatch", "SCHEMA_IDENTITY_MISMATCH")

    final_action = summary.get("final_action")
    if final_action in ORDER_AFFECTING_FINAL_ACTIONS:
        return SummaryValidationResult("BLOCKED", "summary shell cannot emit order-affecting final_action", "LIVE_FINAL_GUARD_FAILED")

    live_ready = summary.get("live_ready")
    if not isinstance(live_ready, dict):
        return SummaryValidationResult("FAIL", "summary live_ready must be an object", "SCHEMA_IDENTITY_MISMATCH")
    if live_ready.get("live_order_ready") or live_ready.get("live_order_allowed"):
        return SummaryValidationResult("BLOCKED", "summary shell attempted to create live readiness", "LIVE_FINAL_GUARD_FAILED")
    if live_ready.get("blocks_live_order") is not True:
        return SummaryValidationResult("BLOCKED", "summary shell must keep live order blocked", "LIVE_FINAL_GUARD_FAILED")

    blocker = summary.get("blocking_reason")
    if allowed_blockers is not None and blocker is not None and blocker not in allowed_blockers:
        return SummaryValidationResult("FAIL", f"unknown summary blocker: {blocker}", "UNKNOWN_BLOCKED")
    live_blocker = live_ready.get("primary_blocker_code")
    if allowed_blockers is not None and live_blocker is not None and live_blocker not in allowed_blockers:
        return SummaryValidationResult("FAIL", f"unknown live_ready blocker: {live_blocker}", "UNKNOWN_BLOCKED")

    for field in ("engine", "startup", "operator_status", "resources"):
        value = summary.get(field)
        if not isinstance(value, dict) or "source" not in value or "freshness_status" not in value:
            return SummaryValidationResult("FAIL", f"summary {field} source object invalid", "SCHEMA_IDENTITY_MISMATCH")

    portfolio = summary.get("portfolio")
    if not isinstance(portfolio, dict):
        return SummaryValidationResult("FAIL", "summary portfolio must be an object", "SCHEMA_IDENTITY_MISMATCH")
    if portfolio.get("source") == "SUMMARY_BUILDER" and any(portfolio.get(key) is not None for key in ("equity", "cash_available", "locked_balance")):
        return SummaryValidationResult("BLOCKED", "summary builder cannot invent portfolio execution truth", "LIVE_FINAL_GUARD_FAILED")
    if portfolio.get("source") in {"LEDGER", "RECONCILIATION"} and portfolio.get("freshness_status") == "PASS":
        if any(portfolio.get(key) is None for key in ("equity", "cash_available", "locked_balance")):
            return SummaryValidationResult("BLOCKED", "verified portfolio source must include cash and equity", "HARD_TRUTH_MISSING")
        if summary.get("mode") != "PAPER":
            return SummaryValidationResult("BLOCKED", "verified dashboard portfolio is PAPER-only without live evidence", "LIVE_FINAL_GUARD_FAILED")
        if portfolio.get("open_position_count") != len(summary.get("positions", [])):
            return SummaryValidationResult("FAIL", "portfolio open position count must match positions list", "SCHEMA_IDENTITY_MISMATCH")

    orders = summary.get("orders")
    if not isinstance(orders, dict):
        return SummaryValidationResult("FAIL", "summary orders must be an object", "SCHEMA_IDENTITY_MISMATCH")
    if orders.get("source") == "SUMMARY_BUILDER" and (orders.get("open_order_count") or orders.get("pending_confirm_count")):
        return SummaryValidationResult("BLOCKED", "summary builder cannot invent order execution truth", "LIVE_FINAL_GUARD_FAILED")

    if summary.get("resources", {}).get("freshness_status") in {"FAIL", "STALE"} and summary.get("blocking_reason") is None:
        return SummaryValidationResult("BLOCKED", "resource failure must surface a blocking reason", "RESOURCE_LIMIT")
    return SummaryValidationResult("PASS", "summary shell is dashboard-only and fail-closed", None)
