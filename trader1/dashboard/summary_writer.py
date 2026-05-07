from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from trader1.runtime.portfolio.paper_portfolio import (
    PAPER_STARTING_CASH_BY_SCOPE,
    PUBLIC_MARK_PRICE_SOURCE,
    validate_paper_portfolio_snapshot,
)


SUMMARY_SCHEMA_ID = "trader1.summary.v1"
PAPER_PORTFOLIO_SNAPSHOT_STALE_AFTER_SECONDS = 300
SOURCE_CLOCK_SKEW_ALLOWANCE_SECONDS = 60
ORDER_AFFECTING_FINAL_ACTIONS = {
    "ENTER_LONG",
    "ENTER_SHORT",
    "EXIT_POSITION",
    "REDUCE_POSITION",
    "CANCEL_ORDER",
    "HOLD_POSITION",
}
CONFIGURED_PAPER_STARTING_CASH_SOURCE = "MVP_PAPER_DEFAULT_NOT_LIVE_ACCOUNT"
CONFIGURED_PAPER_STARTING_CASH_STATUSES = {
    "CONFIGURED_NOT_VERIFIED",
    "VERIFIED_SOURCE_PRESENT",
    "UNSUPPORTED_SCOPE",
}
QUANTITATIVE_POLICY_SOURCES = {"SUMMARY_BUILDER", "QUANTITATIVE_POLICY_REPORT"}
QUANTITATIVE_POLICY_STATUSES = {"IMPLEMENTED_LIVE_BLOCKED", "BLOCKED", "UNTESTED"}
SUMMARY_POSITION_PAPER_SOURCES = {
    "PAPER_LEDGER_SCAFFOLD",
    "PAPER_LEDGER_ROLLUP",
    "PAPER_LEDGER_ROLLUP_PUBLIC_MARK",
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


def _configured_paper_capital_fields(
    *,
    exchange: str,
    market_type: str,
    snapshot: dict[str, Any] | None = None,
    verified_source: bool = False,
) -> dict[str, Any]:
    if verified_source and isinstance(snapshot, dict):
        starting_cash = _decimal(snapshot.get("starting_cash"))
        currency = snapshot.get("currency")
        source = snapshot.get("starting_cash_source")
        if starting_cash is not None and starting_cash > 0 and isinstance(currency, str) and currency:
            return {
                "configured_paper_starting_cash": float(starting_cash),
                "configured_paper_starting_cash_currency": currency,
                "configured_paper_starting_cash_source": source or CONFIGURED_PAPER_STARTING_CASH_SOURCE,
                "configured_paper_starting_cash_status": "VERIFIED_SOURCE_PRESENT",
                "configured_paper_starting_cash_message": "PAPER starting capital from the verified simulated ledger snapshot.",
            }

    configured = PAPER_STARTING_CASH_BY_SCOPE.get((exchange, market_type))
    if configured is None:
        return {
            "configured_paper_starting_cash": None,
            "configured_paper_starting_cash_currency": None,
            "configured_paper_starting_cash_source": None,
            "configured_paper_starting_cash_status": "UNSUPPORTED_SCOPE",
            "configured_paper_starting_cash_message": "No configured PAPER starting capital exists for this exchange and market.",
        }
    currency, amount = configured
    return {
        "configured_paper_starting_cash": float(amount),
        "configured_paper_starting_cash_currency": currency,
        "configured_paper_starting_cash_source": CONFIGURED_PAPER_STARTING_CASH_SOURCE,
        "configured_paper_starting_cash_status": "CONFIGURED_NOT_VERIFIED",
        "configured_paper_starting_cash_message": "Configured PAPER starting capital only; verified portfolio ledger is not loaded.",
    }


def _empty_portfolio(
    *,
    exchange: str,
    market_type: str,
    message: str = "No verified paper portfolio snapshot loaded",
) -> dict[str, Any]:
    return {
        "source": "SUMMARY_BUILDER",
        "freshness_status": "UNTESTED",
        "source_snapshot_hash": None,
        "source_runtime_cycle_id": None,
        "source_paper_ledger_head_hash": None,
        "source_snapshot_status": "UNTESTED",
        "source_snapshot_generated_at_utc": None,
        "source_snapshot_age_seconds": None,
        "source_snapshot_stale_after_seconds": PAPER_PORTFOLIO_SNAPSHOT_STALE_AFTER_SECONDS,
        "source_snapshot_freshness_message": message,
        "source_balance_kind": None,
        "equity": None,
        "cash_available": None,
        "locked_balance": None,
        "position_market_value": None,
        "open_position_count": 0,
        "realized_pnl": None,
        "unrealized_pnl": None,
        "total_pnl": None,
        "mdd": None,
        "next_action": "Run PAPER with a fresh verified paper portfolio ledger before trusting portfolio values",
        **_configured_paper_capital_fields(exchange=exchange, market_type=market_type),
    }


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _source_age_seconds(generated_at_utc: Any, *, now: datetime | None = None) -> int | None:
    generated_at = _parse_utc(generated_at_utc)
    if generated_at is None:
        return None
    now_utc = now or datetime.now(timezone.utc)
    delta = (now_utc - generated_at).total_seconds()
    if delta < -SOURCE_CLOCK_SKEW_ALLOWANCE_SECONDS:
        return None
    return max(0, int(delta))


def _portfolio_from_paper_snapshot(
    snapshot: dict[str, Any] | None,
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not isinstance(snapshot, dict):
        return _empty_portfolio(exchange=exchange, market_type=market_type), []
    result = validate_paper_portfolio_snapshot(snapshot)
    scope_matches = (
        snapshot.get("exchange") == exchange
        and snapshot.get("market_type") == market_type
        and snapshot.get("mode") == mode
        and snapshot.get("session_id") == session_id
    )
    if result.status != "PASS" or not scope_matches:
        return _empty_portfolio(exchange=exchange, market_type=market_type), []
    source_age_seconds = _source_age_seconds(snapshot.get("generated_at_utc"))
    if source_age_seconds is None:
        return _empty_portfolio(
            exchange=exchange,
            market_type=market_type,
            message="PAPER portfolio snapshot timestamp is invalid; rerun PAPER before trusting portfolio values",
        ), []
    if source_age_seconds > PAPER_PORTFOLIO_SNAPSHOT_STALE_AFTER_SECONDS:
        freshness_status = "STALE"
        freshness_message = (
            "PAPER portfolio snapshot is stale; values are the last verified simulated ledger values, "
            "not fresh execution truth."
        )
        next_action = "Rerun PAPER before using cash, equity, PnL, return, or positions for operator review"
    else:
        freshness_status = "PASS"
        freshness_message = "PAPER portfolio snapshot is fresh and display-only"
        next_action = "Continue PAPER monitoring; portfolio values are display truth only"
    return (
        {
            "source": "LEDGER",
            "freshness_status": freshness_status,
            "source_snapshot_hash": snapshot["snapshot_hash"],
            "source_runtime_cycle_id": snapshot.get("source_runtime_cycle_id"),
            "source_paper_ledger_head_hash": snapshot.get("source_paper_ledger_head_hash"),
            "source_snapshot_status": snapshot["snapshot_status"],
            "source_snapshot_generated_at_utc": snapshot["generated_at_utc"],
            "source_snapshot_age_seconds": source_age_seconds,
            "source_snapshot_stale_after_seconds": PAPER_PORTFOLIO_SNAPSHOT_STALE_AFTER_SECONDS,
            "source_snapshot_freshness_message": freshness_message,
            "source_balance_kind": snapshot["display_balance_kind"],
            "equity": float(snapshot["equity"]),
            "cash_available": float(snapshot["cash_available"]),
            "locked_balance": float(snapshot["locked_balance"]),
            "position_market_value": float(snapshot.get("position_market_value", 0)),
            "open_position_count": int(snapshot.get("open_position_count", len(snapshot.get("positions", [])))),
            "realized_pnl": float(snapshot["realized_pnl"]),
            "unrealized_pnl": float(snapshot["unrealized_pnl"]),
            "total_pnl": float(snapshot.get("total_pnl", 0)),
            "mdd": 0.0,
            "next_action": next_action,
            **_configured_paper_capital_fields(exchange=exchange, market_type=market_type, snapshot=snapshot, verified_source=True),
        },
        list(snapshot.get("positions", [])),
    )


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _float_or_none(value: Any) -> float | None:
    decimal_value = _decimal(value)
    if decimal_value is None:
        return None
    return float(decimal_value)


def _is_hash64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789ABCDEFabcdef" for char in value)


def _nearly_equal(left: Decimal, right: Decimal, tolerance: Decimal = Decimal("0.000001")) -> bool:
    return abs(left - right) <= tolerance


def _validate_configured_paper_capital(portfolio: dict[str, Any]) -> SummaryValidationResult | None:
    keys = (
        "configured_paper_starting_cash",
        "configured_paper_starting_cash_currency",
        "configured_paper_starting_cash_source",
        "configured_paper_starting_cash_status",
        "configured_paper_starting_cash_message",
    )
    if not any(key in portfolio for key in keys):
        return None

    status = portfolio.get("configured_paper_starting_cash_status")
    if status not in CONFIGURED_PAPER_STARTING_CASH_STATUSES:
        return SummaryValidationResult("FAIL", "configured PAPER capital status is invalid", "SCHEMA_IDENTITY_MISMATCH")
    amount = _decimal(portfolio.get("configured_paper_starting_cash"))
    currency = portfolio.get("configured_paper_starting_cash_currency")
    source = portfolio.get("configured_paper_starting_cash_source")
    message = portfolio.get("configured_paper_starting_cash_message")
    if status == "UNSUPPORTED_SCOPE":
        if any(portfolio.get(key) is not None for key in ("configured_paper_starting_cash", "configured_paper_starting_cash_currency", "configured_paper_starting_cash_source")):
            return SummaryValidationResult("FAIL", "unsupported PAPER capital scope cannot carry configured value", "SCHEMA_IDENTITY_MISMATCH")
    elif status == "VERIFIED_SOURCE_PRESENT" and portfolio.get("source") not in {"LEDGER", "RECONCILIATION"}:
        return SummaryValidationResult("BLOCKED", "verified PAPER capital label requires verified portfolio source", "HARD_TRUTH_MISSING")
    elif amount is None or amount <= 0 or not isinstance(currency, str) or not currency:
        return SummaryValidationResult("FAIL", "configured PAPER capital amount or currency is invalid", "SCHEMA_IDENTITY_MISMATCH")
    elif source != CONFIGURED_PAPER_STARTING_CASH_SOURCE:
        return SummaryValidationResult("BLOCKED", "configured PAPER capital cannot claim exchange or live account source", "LIVE_FINAL_GUARD_FAILED")
    if not isinstance(message, str) or not message:
        return SummaryValidationResult("FAIL", "configured PAPER capital message is missing", "SCHEMA_IDENTITY_MISMATCH")
    return None


def _validate_summary_positions(positions: Any) -> tuple[SummaryValidationResult | None, Decimal, Decimal]:
    if not isinstance(positions, list):
        return SummaryValidationResult("FAIL", "summary positions must be a list", "SCHEMA_IDENTITY_MISMATCH"), Decimal("0"), Decimal("0")
    required = {
        "symbol",
        "side",
        "quantity",
        "average_entry_price",
        "mark_price",
        "cost_basis",
        "market_value",
        "unrealized_pnl",
        "source",
        "paper_only",
    }
    market_value_sum = Decimal("0")
    unrealized_sum = Decimal("0")
    for position in positions:
        if not isinstance(position, dict):
            return SummaryValidationResult("FAIL", "summary position must be an object", "SCHEMA_IDENTITY_MISMATCH"), Decimal("0"), Decimal("0")
        missing = sorted(required - set(position))
        if missing:
            return (
                SummaryValidationResult("FAIL", f"summary position missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"),
                Decimal("0"),
                Decimal("0"),
            )
        position_source = position.get("source")
        if position.get("paper_only") is not True or position_source not in SUMMARY_POSITION_PAPER_SOURCES:
            return SummaryValidationResult("BLOCKED", "summary position cannot claim exchange truth", "LIVE_FINAL_GUARD_FAILED"), Decimal("0"), Decimal("0")
        if position_source == "PAPER_LEDGER_ROLLUP_PUBLIC_MARK":
            public_mark_time = position.get("source_public_market_event_time_utc")
            public_mark_hash = position.get("source_public_market_event_hash")
            if (
                position.get("mark_price_source") != PUBLIC_MARK_PRICE_SOURCE
                or _parse_utc(public_mark_time) is None
                or not isinstance(public_mark_hash, str)
                or len(public_mark_hash) != 64
            ):
                return (
                    SummaryValidationResult(
                        "BLOCKED",
                        "public-marked summary position requires public mark provenance",
                        "HARD_TRUTH_MISSING",
                    ),
                    Decimal("0"),
                    Decimal("0"),
                )
        if position.get("side") != "LONG":
            return SummaryValidationResult("BLOCKED", "summary position must remain long spot only", "LIVE_FINAL_GUARD_FAILED"), Decimal("0"), Decimal("0")
        if not isinstance(position.get("symbol"), str) or not position["symbol"]:
            return SummaryValidationResult("FAIL", "summary position symbol is missing", "SCHEMA_IDENTITY_MISMATCH"), Decimal("0"), Decimal("0")
        quantity = _decimal(position.get("quantity"))
        average_entry = _decimal(position.get("average_entry_price"))
        mark = _decimal(position.get("mark_price"))
        cost_basis = _decimal(position.get("cost_basis"))
        market_value = _decimal(position.get("market_value"))
        unrealized = _decimal(position.get("unrealized_pnl"))
        if any(value is None for value in (quantity, average_entry, mark, cost_basis, market_value, unrealized)):
            return SummaryValidationResult("FAIL", "summary position values must be numeric", "SCHEMA_IDENTITY_MISMATCH"), Decimal("0"), Decimal("0")
        if min(quantity, average_entry, mark, cost_basis, market_value) < 0 or quantity <= 0 or average_entry <= 0 or mark <= 0:
            return SummaryValidationResult("BLOCKED", "summary position values are invalid", "MEASUREMENT_MISSING"), Decimal("0"), Decimal("0")
        if not _nearly_equal(market_value, quantity * mark):
            return SummaryValidationResult("FAIL", "summary position market value arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH"), Decimal("0"), Decimal("0")
        if cost_basis < quantity * average_entry:
            return SummaryValidationResult("FAIL", "summary position cost basis is below gross entry cost", "SCHEMA_IDENTITY_MISMATCH"), Decimal("0"), Decimal("0")
        if not _nearly_equal(unrealized, market_value - cost_basis):
            return SummaryValidationResult("FAIL", "summary position unrealized PnL arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH"), Decimal("0"), Decimal("0")
        market_value_sum += market_value
        unrealized_sum += unrealized
    return None, market_value_sum, unrealized_sum


def _default_quantitative_policy_report(session_id: str) -> dict[str, Any]:
    from trader1.core.strategy.quantitative_policy import build_quantitative_policy_report

    return build_quantitative_policy_report(report_id=f"{session_id}_summary_quantitative_policy")


def _quantitative_policy_summary(
    policy_report: dict[str, Any] | None,
    *,
    exchange: str,
    market_type: str,
) -> dict[str, Any]:
    if not isinstance(policy_report, dict):
        if exchange == "BINANCE" and market_type == "FUTURES_USDT_M":
            reason_code = "BINANCE_FUTURES_SURFACE_ONLY"
        elif exchange == "BINANCE":
            reason_code = "BINANCE_ADAPTER_SURFACE_ONLY"
        else:
            reason_code = "LIVE_READY_MISSING"
        message = (
            "LIVE blocked: Binance strategy policy is scaffold-only and cannot be used as runtime readiness."
            if exchange == "BINANCE"
            else "LIVE blocked: quantitative policy report is not loaded."
        )
        return {
            "source": "SUMMARY_BUILDER",
            "freshness_status": "UNTESTED",
            "policy_status": "BLOCKED" if exchange == "BINANCE" else "UNTESTED",
            "decision_surface": "DASHBOARD_ONLY",
            "source_policy_report_id": None,
            "source_policy_report_hash": None,
            "dashboard_reason_code": reason_code,
            "dashboard_operator_message": message,
            "minimum_trade_count": 100,
            "high_return_candidate_trade_count": 300,
            "signal_grade": None,
            "signal_score": None,
            "net_expected_edge": None,
            "total_cost": None,
            "primary_blocker_code": reason_code,
            "next_action": "Regenerate the summary with a quantitative policy report before strategy review.",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    basis = policy_report.get("law_of_large_numbers_basis", {})
    signal = policy_report.get("signal_policy", {})
    edge = policy_report.get("edge_policy", {})
    live_ready = policy_report.get("live_ready_policy", {})
    reason_code = (
        policy_report.get("dashboard_reason_code")
        or live_ready.get("primary_blocker_code")
        or policy_report.get("primary_blocker_code")
        or "LIVE_READY_MISSING"
    )
    return {
        "source": "QUANTITATIVE_POLICY_REPORT",
        "freshness_status": "PASS",
        "policy_status": str(policy_report.get("policy_status") or "BLOCKED"),
        "decision_surface": "DASHBOARD_ONLY",
        "source_policy_report_id": policy_report.get("policy_report_id"),
        "source_policy_report_hash": policy_report.get("policy_report_hash"),
        "dashboard_reason_code": reason_code,
        "dashboard_operator_message": policy_report.get(
            "dashboard_operator_message",
            "LIVE blocked: quantitative policy is display-only and cannot approve orders.",
        ),
        "minimum_trade_count": int(basis.get("minimum_trade_count", 100)),
        "high_return_candidate_trade_count": int(basis.get("high_return_candidate_trade_count", 300)),
        "signal_grade": signal.get("signal_grade"),
        "signal_score": _float_or_none(signal.get("signal_score")),
        "net_expected_edge": _float_or_none(edge.get("net_expected_edge")),
        "total_cost": _float_or_none(edge.get("total_cost")),
        "primary_blocker_code": reason_code,
        "next_action": "Use the policy summary for PAPER/SHADOW review only; LIVE_READY and scale-up remain blocked.",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _validate_quantitative_policy_summary(
    policy_summary: Any,
    allowed_blockers: set[str] | None,
) -> SummaryValidationResult | None:
    if not isinstance(policy_summary, dict):
        return SummaryValidationResult("FAIL", "quantitative policy summary must be an object", "SCHEMA_IDENTITY_MISMATCH")
    if policy_summary.get("source") not in QUANTITATIVE_POLICY_SOURCES:
        return SummaryValidationResult("FAIL", "quantitative policy summary source is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if policy_summary.get("policy_status") not in QUANTITATIVE_POLICY_STATUSES:
        return SummaryValidationResult("FAIL", "quantitative policy status is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if policy_summary.get("decision_surface") != "DASHBOARD_ONLY":
        return SummaryValidationResult("BLOCKED", "quantitative policy summary must stay dashboard-only", "LIVE_FINAL_GUARD_FAILED")
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if policy_summary.get(field) is not False:
            return SummaryValidationResult("BLOCKED", f"quantitative policy summary attempted live or scale flag: {field}", "LIVE_FINAL_GUARD_FAILED")
    if policy_summary.get("minimum_trade_count") != 100 or policy_summary.get("high_return_candidate_trade_count") != 300:
        return SummaryValidationResult("FAIL", "quantitative policy sample thresholds must remain 100 and 300", "SCHEMA_IDENTITY_MISMATCH")
    reason_code = policy_summary.get("dashboard_reason_code")
    primary_blocker = policy_summary.get("primary_blocker_code")
    if allowed_blockers is not None:
        for code in (reason_code, primary_blocker):
            if code is not None and code not in allowed_blockers:
                return SummaryValidationResult("FAIL", f"unknown quantitative policy blocker: {code}", "UNKNOWN_BLOCKED")
    message = str(policy_summary.get("dashboard_operator_message") or "").lower()
    if "live" not in message or "blocked" not in message:
        return SummaryValidationResult("FAIL", "quantitative policy message must state LIVE is blocked", "SCHEMA_IDENTITY_MISMATCH")
    if policy_summary.get("source") == "QUANTITATIVE_POLICY_REPORT":
        if policy_summary.get("freshness_status") != "PASS":
            return SummaryValidationResult("BLOCKED", "loaded quantitative policy report must be fresh", "LATENCY_TTL_EXPIRED")
        if not isinstance(policy_summary.get("source_policy_report_id"), str) or not policy_summary.get("source_policy_report_id"):
            return SummaryValidationResult("FAIL", "quantitative policy report id is missing", "SCHEMA_IDENTITY_MISMATCH")
        if not _is_hash64(policy_summary.get("source_policy_report_hash")):
            return SummaryValidationResult("FAIL", "quantitative policy report hash is invalid", "SCHEMA_IDENTITY_MISMATCH")
    return None


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
    quantitative_policy_report: dict[str, Any] | None = None,
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
    policy_report = quantitative_policy_report
    if policy_report is None and exchange == "UPBIT" and market_type == "KRW_SPOT" and mode == "PAPER":
        policy_report = _default_quantitative_policy_report(session_id)

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
        "quantitative_policy_summary": _quantitative_policy_summary(
            policy_report,
            exchange=exchange,
            market_type=market_type,
        ),
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


def validate_summary_shell(
    summary: dict[str, Any],
    allowed_blockers: set[str] | None = None,
    *,
    require_quantitative_policy_summary: bool = True,
) -> SummaryValidationResult:
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

    if require_quantitative_policy_summary or "quantitative_policy_summary" in summary:
        quantitative_policy_result = _validate_quantitative_policy_summary(
            summary.get("quantitative_policy_summary"),
            allowed_blockers,
        )
        if quantitative_policy_result is not None:
            return quantitative_policy_result

    portfolio = summary.get("portfolio")
    if not isinstance(portfolio, dict):
        return SummaryValidationResult("FAIL", "summary portfolio must be an object", "SCHEMA_IDENTITY_MISMATCH")
    configured_capital_result = _validate_configured_paper_capital(portfolio)
    if configured_capital_result is not None:
        return configured_capital_result
    if portfolio.get("source") == "SUMMARY_BUILDER" and any(portfolio.get(key) is not None for key in ("equity", "cash_available", "locked_balance")):
        return SummaryValidationResult("BLOCKED", "summary builder cannot invent portfolio execution truth", "LIVE_FINAL_GUARD_FAILED")
    if portfolio.get("source") == "SUMMARY_BUILDER" and any(
        portfolio.get(key) is not None
        for key in (
            "source_snapshot_hash",
            "source_runtime_cycle_id",
            "source_paper_ledger_head_hash",
            "source_snapshot_generated_at_utc",
            "source_snapshot_age_seconds",
            "source_balance_kind",
        )
    ):
        return SummaryValidationResult("BLOCKED", "summary builder cannot claim portfolio snapshot provenance", "LIVE_FINAL_GUARD_FAILED")
    if portfolio.get("source") in {"LEDGER", "RECONCILIATION"} and portfolio.get("freshness_status") in {"PASS", "STALE"}:
        if any(portfolio.get(key) is None for key in ("equity", "cash_available", "locked_balance")):
            return SummaryValidationResult("BLOCKED", "verified portfolio source must include cash and equity", "HARD_TRUTH_MISSING")
        if portfolio.get("source_snapshot_status") != "PASS" or not _is_hash64(portfolio.get("source_snapshot_hash")):
            return SummaryValidationResult("BLOCKED", "verified portfolio source must carry PASS source snapshot provenance", "HARD_TRUTH_MISSING")
        if portfolio.get("source_runtime_cycle_id") is not None and (
            not isinstance(portfolio.get("source_runtime_cycle_id"), str) or not portfolio.get("source_runtime_cycle_id")
        ):
            return SummaryValidationResult("FAIL", "verified portfolio runtime cycle provenance is invalid", "SCHEMA_IDENTITY_MISMATCH")
        if portfolio.get("source_paper_ledger_head_hash") is not None and not _is_hash64(portfolio.get("source_paper_ledger_head_hash")):
            return SummaryValidationResult("FAIL", "verified portfolio ledger head provenance is invalid", "SCHEMA_IDENTITY_MISMATCH")
        if not isinstance(portfolio.get("source_snapshot_generated_at_utc"), str):
            return SummaryValidationResult("BLOCKED", "verified portfolio source must carry snapshot timestamp provenance", "HARD_TRUTH_MISSING")
        source_age = _decimal(portfolio.get("source_snapshot_age_seconds"))
        stale_after = _decimal(portfolio.get("source_snapshot_stale_after_seconds"))
        if source_age is None or stale_after is None or source_age < 0 or stale_after <= 0:
            return SummaryValidationResult("FAIL", "verified portfolio snapshot age fields must be numeric", "SCHEMA_IDENTITY_MISMATCH")
        if portfolio.get("freshness_status") == "PASS" and source_age > stale_after:
            return SummaryValidationResult("BLOCKED", "verified portfolio source snapshot is stale", "LATENCY_TTL_EXPIRED")
        if portfolio.get("freshness_status") == "STALE" and source_age <= stale_after:
            return SummaryValidationResult("FAIL", "stale portfolio source must exceed stale threshold", "SCHEMA_IDENTITY_MISMATCH")
        if portfolio.get("source_balance_kind") != "SIMULATED_PAPER_LEDGER":
            return SummaryValidationResult("BLOCKED", "verified summary portfolio must remain simulated PAPER ledger truth", "LIVE_FINAL_GUARD_FAILED")
        if summary.get("mode") != "PAPER":
            return SummaryValidationResult("BLOCKED", "verified dashboard portfolio is PAPER-only without live evidence", "LIVE_FINAL_GUARD_FAILED")
        positions = summary.get("positions")
        if not isinstance(positions, list) or portfolio.get("open_position_count") != len(positions):
            return SummaryValidationResult("FAIL", "portfolio open position count must match positions list", "SCHEMA_IDENTITY_MISMATCH")
        cash = _decimal(portfolio.get("cash_available"))
        locked = _decimal(portfolio.get("locked_balance"))
        position_market_value = _decimal(portfolio.get("position_market_value"))
        equity = _decimal(portfolio.get("equity"))
        realized = _decimal(portfolio.get("realized_pnl"))
        unrealized = _decimal(portfolio.get("unrealized_pnl"))
        total_pnl = _decimal(portfolio.get("total_pnl"))
        if any(value is None for value in (cash, locked, position_market_value, equity, realized, unrealized, total_pnl)):
            return SummaryValidationResult("FAIL", "verified portfolio values must be numeric", "SCHEMA_IDENTITY_MISMATCH")
        positions_result, positions_market_value, positions_unrealized = _validate_summary_positions(positions)
        if positions_result is not None:
            return positions_result
        if not _nearly_equal(position_market_value, positions_market_value):
            return SummaryValidationResult("FAIL", "summary position market value rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if not _nearly_equal(unrealized, positions_unrealized):
            return SummaryValidationResult("FAIL", "summary position unrealized PnL rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if not _nearly_equal(equity, cash + locked + position_market_value):
            return SummaryValidationResult("FAIL", "verified portfolio equity arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if not _nearly_equal(total_pnl, realized + unrealized):
            return SummaryValidationResult("FAIL", "verified portfolio total PnL arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH")
    elif portfolio.get("source") in {"LEDGER", "RECONCILIATION"}:
        return SummaryValidationResult("FAIL", "portfolio ledger freshness status is invalid", "SCHEMA_IDENTITY_MISMATCH")

    orders = summary.get("orders")
    if not isinstance(orders, dict):
        return SummaryValidationResult("FAIL", "summary orders must be an object", "SCHEMA_IDENTITY_MISMATCH")
    if orders.get("source") == "SUMMARY_BUILDER" and (orders.get("open_order_count") or orders.get("pending_confirm_count")):
        return SummaryValidationResult("BLOCKED", "summary builder cannot invent order execution truth", "LIVE_FINAL_GUARD_FAILED")

    if summary.get("resources", {}).get("freshness_status") in {"FAIL", "STALE"} and summary.get("blocking_reason") is None:
        return SummaryValidationResult("BLOCKED", "resource failure must surface a blocking reason", "RESOURCE_LIMIT")
    return SummaryValidationResult("PASS", "summary shell is dashboard-only and fail-closed", None)
