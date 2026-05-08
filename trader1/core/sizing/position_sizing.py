from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import Any


POSITION_SIZING_SCHEMA_ID = "trader1.position_sizing_decision.v1"
SIZING_REQUIRED_INPUTS = {
    "equity",
    "cash",
    "locked_cash",
    "open_risk",
    "unrealized_pnl",
    "realized_pnl",
    "volatility",
    "liquidity",
    "spread",
    "orderbook_depth",
    "signal_strength",
    "strategy_confidence",
    "regime_confidence",
    "loss_streak",
    "current_exposure",
    "strategy_score",
    "exchange",
    "market_type",
    "symbol_rules",
    "fee",
    "slippage",
    "market_impact",
    "atr_rate",
    "drawdown_pct",
    "regime",
    "market_state",
    "correlation_cluster_status",
    "correlation_penalty",
    "realized_performance_feedback_status",
    "realized_performance_multiplier",
}

ATR_STOP_MULTIPLIER = Decimal("1.20")
MIN_STOP_DISTANCE_RATE = Decimal("0.003")
RISK_PER_TRADE_PCT = Decimal("0.005")
VOLATILITY_TARGET_RATE = Decimal("0.04")
MIN_VOLATILITY_RATE = Decimal("0.005")
MAX_BASE_POSITION_PCT = Decimal("0.01")
MAX_CASH_POSITION_PCT = Decimal("0.05")
MAX_OPEN_RISK_PCT = Decimal("0.02")
MAX_LIQUIDITY_TAKE_PCT = Decimal("0.01")
MAX_EXPOSURE_PCT = Decimal("0.35")
DRAWDOWN_REDUCE_PCT = Decimal("0.02")
DRAWDOWN_FREEZE_PCT = Decimal("0.05")
CORRELATION_FILTERED_MULTIPLIER = Decimal("0")
PERFORMANCE_FEEDBACK_MIN_MULTIPLIER = Decimal("0.35")


@dataclass(frozen=True)
class PositionSizingValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sizing_decision_hash(decision: dict[str, Any]) -> str:
    payload = dict(decision)
    payload.pop("sizing_decision_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def default_sizing_inputs() -> dict[str, str]:
    return {
        "equity": "1000000",
        "cash": "900000",
        "locked_cash": "0",
        "open_risk": "0",
        "unrealized_pnl": "0",
        "realized_pnl": "0",
        "volatility": "0.02",
        "liquidity": "10000000",
        "spread": "0.001",
        "orderbook_depth": "5000000",
        "signal_strength": "0.60",
        "strategy_confidence": "0.55",
        "regime_confidence": "0.55",
        "loss_streak": "0",
        "current_exposure": "0",
        "strategy_score": "0.55",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "symbol_rules": "PASS",
        "fee": "0.0005",
        "slippage": "0.0005",
        "market_impact": "0.001",
        "atr_rate": "0.02",
        "drawdown_pct": "0",
        "regime": "UPTREND",
        "market_state": "UPTREND",
        "correlation_cluster_status": "LEADER",
        "correlation_penalty": "0",
        "realized_performance_feedback_status": "CLEAR",
        "realized_performance_multiplier": "1",
    }


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("-1")


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f") if value != value.to_integral() else str(value.quantize(Decimal("1")))


def _clamp_decimal(value: Decimal, lower: Decimal, upper: Decimal) -> Decimal:
    return max(lower, min(upper, value))


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _drawdown_multiplier(drawdown_pct: Decimal) -> Decimal:
    if drawdown_pct >= DRAWDOWN_FREEZE_PCT:
        return Decimal("0")
    if drawdown_pct >= DRAWDOWN_REDUCE_PCT:
        return Decimal("0.50")
    return Decimal("1.00")


def _regime_multiplier(regime: str, market_state: str) -> Decimal:
    normalized_regime = str(regime or "").upper()
    normalized_state = str(market_state or normalized_regime).upper()
    if normalized_state in {"RISK_OFF", "DOWNTREND", "PANIC", "DATA_BAD", "UNCERTAIN"} or normalized_regime == "RISK_OFF":
        return Decimal("0")
    if normalized_state == "VOLATILITY_EXPANSION":
        return Decimal("0.75")
    if normalized_state == "QUIET_RANGE":
        return Decimal("0.40")
    if normalized_regime == "RANGE":
        return Decimal("0.65")
    if normalized_regime == "UPTREND":
        return Decimal("1.00")
    return Decimal("0")


def _correlation_multiplier(status: str, penalty: Decimal) -> Decimal:
    normalized = str(status or "").upper()
    if normalized == "DIVERSIFICATION_FILTERED":
        return CORRELATION_FILTERED_MULTIPLIER
    return _clamp_decimal(Decimal("1") - max(Decimal("0"), penalty), Decimal("0.35"), Decimal("1"))


def _performance_multiplier(status: str, supplied: Decimal) -> Decimal:
    normalized = str(status or "CLEAR").upper()
    base = _clamp_decimal(supplied, Decimal("0"), Decimal("1"))
    if normalized in {"ACTIVE", "FAIL", "BLOCKED", "RECENT_FAILURE_COOLDOWN_ACTIVE"}:
        return min(base, PERFORMANCE_FEEDBACK_MIN_MULTIPLIER)
    if normalized in {"WARN", "WATCH"}:
        return min(base, Decimal("0.65"))
    return base


def build_position_sizing_decision(
    *,
    sizing_decision_id: str,
    strategy_unit_id: str,
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "PAPER",
    session_id: str = "mvp3_operational_paper",
    inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inputs = inputs or default_sizing_inputs()
    blockers: list[dict[str, str]] = []
    missing = sorted(SIZING_REQUIRED_INPUTS - set(inputs))
    if missing:
        blockers.append(_blocker("MEASUREMENT_MISSING", f"sizing inputs missing: {missing}"))
    if exchange != "UPBIT" or market_type != "KRW_SPOT" or mode != "PAPER":
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "position sizing is scoped to UPBIT/KRW_SPOT/PAPER"))
    if inputs.get("exchange") != exchange or inputs.get("market_type") != market_type:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "sizing input exchange or market_type mismatch"))
    if inputs.get("symbol_rules") != "PASS":
        blockers.append(_blocker("SYMBOL_RULE_UNVERIFIED", "symbol rules are not pass"))

    equity = _decimal(inputs.get("equity", "0"))
    cash = _decimal(inputs.get("cash", "0"))
    locked_cash = _decimal(inputs.get("locked_cash", "0"))
    open_risk = _decimal(inputs.get("open_risk", "0"))
    liquidity = _decimal(inputs.get("liquidity", "0"))
    orderbook_depth = _decimal(inputs.get("orderbook_depth", "0"))
    current_exposure = _decimal(inputs.get("current_exposure", "0"))
    signal_strength = max(Decimal("0"), min(Decimal("1"), _decimal(inputs.get("signal_strength", "0"))))
    strategy_confidence = max(Decimal("0"), min(Decimal("1"), _decimal(inputs.get("strategy_confidence", "0"))))
    regime_confidence = max(Decimal("0"), min(Decimal("1"), _decimal(inputs.get("regime_confidence", "0"))))
    if equity <= 0 or cash < 0 or current_exposure < 0 or liquidity <= 0 or orderbook_depth <= 0:
        blockers.append(_blocker("MEASUREMENT_MISSING", "sizing cannot compute with non-positive equity, liquidity, or depth"))

    available_cash = max(Decimal("0"), cash - locked_cash)
    volatility = max(Decimal("0"), _decimal(inputs.get("volatility", "0")))
    atr_rate = max(Decimal("0"), _decimal(inputs.get("atr_rate", volatility)))
    spread = max(Decimal("0"), _decimal(inputs.get("spread", "0")))
    fee = max(Decimal("0"), _decimal(inputs.get("fee", "0")))
    slippage = max(Decimal("0"), _decimal(inputs.get("slippage", "0")))
    market_impact = max(Decimal("0"), _decimal(inputs.get("market_impact", "0")))
    drawdown_pct = max(Decimal("0"), _decimal(inputs.get("drawdown_pct", "0")))
    correlation_penalty = max(Decimal("0"), _decimal(inputs.get("correlation_penalty", "0")))
    stop_distance_rate = max(
        MIN_STOP_DISTANCE_RATE,
        atr_rate * ATR_STOP_MULTIPLIER,
        (spread + fee + slippage + market_impact) * Decimal("2"),
    )
    equity_cap = max(Decimal("0"), equity * MAX_BASE_POSITION_PCT)
    cash_cap = max(Decimal("0"), available_cash * MAX_CASH_POSITION_PCT)
    risk_cap = max(Decimal("0"), equity * MAX_OPEN_RISK_PCT - open_risk)
    liquidity_cap = max(Decimal("0"), min(liquidity, orderbook_depth) * MAX_LIQUIDITY_TAKE_PCT)
    exposure_cap = max(Decimal("0"), (equity * MAX_EXPOSURE_PCT) - current_exposure)
    atr_risk_cap = max(Decimal("0"), equity * RISK_PER_TRADE_PCT / stop_distance_rate)
    volatility_reference = max(MIN_VOLATILITY_RATE, volatility)
    volatility_multiplier = _clamp_decimal(
        VOLATILITY_TARGET_RATE / volatility_reference,
        Decimal("0.25"),
        Decimal("1"),
    )
    volatility_cap = max(Decimal("0"), equity_cap * volatility_multiplier)
    drawdown_multiplier = _drawdown_multiplier(drawdown_pct)
    regime_multiplier = _regime_multiplier(str(inputs.get("regime") or ""), str(inputs.get("market_state") or ""))
    correlation_multiplier = _correlation_multiplier(
        str(inputs.get("correlation_cluster_status") or "LEADER"),
        correlation_penalty,
    )
    realized_performance_multiplier = _performance_multiplier(
        str(inputs.get("realized_performance_feedback_status") or "CLEAR"),
        _decimal(inputs.get("realized_performance_multiplier", "1")),
    )
    combined_sizing_multiplier = (
        volatility_multiplier
        * drawdown_multiplier
        * regime_multiplier
        * correlation_multiplier
        * realized_performance_multiplier
    )
    confidence_cap = min(signal_strength, strategy_confidence, regime_confidence)
    if current_exposure > equity * MAX_EXPOSURE_PCT:
        blockers.append(_blocker("RISK_VETO", "current exposure exceeds 35% PAPER equity cap"))
    if available_cash <= 0:
        blockers.append(_blocker("RISK_VETO", "available PAPER cash is zero or locked"))
    if drawdown_multiplier == 0:
        blockers.append(_blocker("DRAWDOWN_FREEZE_ACTIVE", "drawdown is at or above 5% PAPER freeze threshold"))
    if regime_multiplier == 0:
        blockers.append(_blocker("REGIME_MISMATCH", "market regime/state does not allow new spot-long sizing"))
    if correlation_multiplier == 0:
        blockers.append(_blocker("CORRELATION_CAP", "symbol is filtered by correlation clustering cap"))
    if realized_performance_multiplier == 0:
        blockers.append(_blocker("PERFORMANCE_FEEDBACK_BLOCK", "realized performance feedback multiplier is zero"))
    selected = (
        min(equity_cap, cash_cap, risk_cap, liquidity_cap, exposure_cap, atr_risk_cap, volatility_cap)
        * confidence_cap
        * combined_sizing_multiplier
    ).quantize(
        Decimal("1"),
        rounding=ROUND_DOWN,
    )
    if blockers:
        selected = Decimal("0")
    caps = {
        "equity_cap": str(equity_cap),
        "cash_cap": str(cash_cap),
        "risk_cap": str(risk_cap),
        "liquidity_cap": str(liquidity_cap),
        "exposure_cap": str(exposure_cap),
        "atr_risk_cap": _decimal_text(atr_risk_cap),
        "volatility_cap": _decimal_text(volatility_cap),
        "stop_distance_rate": _decimal_text(stop_distance_rate),
        "confidence_cap": str(confidence_cap),
        "volatility_multiplier": _decimal_text(volatility_multiplier),
        "drawdown_multiplier": _decimal_text(drawdown_multiplier),
        "regime_multiplier": _decimal_text(regime_multiplier),
        "correlation_multiplier": _decimal_text(correlation_multiplier),
        "realized_performance_multiplier": _decimal_text(realized_performance_multiplier),
        "combined_sizing_multiplier": _decimal_text(combined_sizing_multiplier),
        "sizing_formula": (
            "floor(min(equity,cash,risk,liquidity,exposure,atr_risk_cap,volatility_cap)"
            "*confidence*volatility*drawdown*regime*correlation*performance)"
        ),
    }
    decision = {
        "schema_id": POSITION_SIZING_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "sizing_decision_id": sizing_decision_id,
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "strategy_unit_id": strategy_unit_id,
        "inputs": {key: str(value) for key, value in inputs.items()},
        "caps": caps,
        "selected_notional": str(selected),
        "sizing_status": "PASS" if not blockers else "BLOCKED",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "sizing_decision_hash": "",
    }
    decision["sizing_decision_hash"] = sizing_decision_hash(decision)
    return decision


def validate_position_sizing_decision(
    decision: dict[str, Any],
    *,
    require_exposure_cap: bool = True,
    require_current_sizing_model: bool = True,
) -> PositionSizingValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "sizing_decision_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "strategy_unit_id",
        "inputs",
        "caps",
        "selected_notional",
        "sizing_status",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "sizing_decision_hash",
    }
    missing = sorted(required - set(decision))
    if missing:
        return PositionSizingValidationResult("FAIL", f"sizing decision missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if decision.get("schema_id") != POSITION_SIZING_SCHEMA_ID:
        return PositionSizingValidationResult("FAIL", "sizing schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if decision.get("sizing_decision_hash") != sizing_decision_hash(decision):
        return PositionSizingValidationResult("FAIL", "sizing decision hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if decision.get("exchange") != "UPBIT" or decision.get("market_type") != "KRW_SPOT" or decision.get("mode") != "PAPER":
        return PositionSizingValidationResult("BLOCKED", "sizing scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if decision.get("live_order_ready") or decision.get("live_order_allowed") or decision.get("can_live_trade") or decision.get("can_submit_order"):
        return PositionSizingValidationResult("BLOCKED", "sizing attempted to create live/order permission", "LIVE_FINAL_GUARD_FAILED")
    if decision.get("order_adapter_called"):
        return PositionSizingValidationResult("BLOCKED", "sizing cannot call an order adapter", "LIVE_FINAL_GUARD_FAILED")
    inputs = decision.get("inputs", {})
    missing_inputs = sorted(SIZING_REQUIRED_INPUTS - set(inputs))
    if missing_inputs and require_current_sizing_model:
        return PositionSizingValidationResult("BLOCKED", f"sizing inputs missing: {missing_inputs}", "MEASUREMENT_MISSING")
    selected = _decimal(decision.get("selected_notional", "0"))
    caps = {key: _decimal(value) for key, value in decision.get("caps", {}).items()}
    if require_current_sizing_model:
        required_cap_keys = [
            "equity_cap",
            "cash_cap",
            "risk_cap",
            "liquidity_cap",
            "atr_risk_cap",
            "volatility_cap",
            "stop_distance_rate",
            "volatility_multiplier",
            "drawdown_multiplier",
            "regime_multiplier",
            "correlation_multiplier",
            "realized_performance_multiplier",
            "combined_sizing_multiplier",
            "sizing_formula",
        ]
    else:
        required_cap_keys = ["equity_cap", "cash_cap", "risk_cap", "liquidity_cap"]
    if require_exposure_cap:
        required_cap_keys.append("exposure_cap")
    for key in required_cap_keys:
        if key not in caps:
            return PositionSizingValidationResult("FAIL", f"sizing cap missing: {key}", "SCHEMA_IDENTITY_MISMATCH")
        if key.endswith("_multiplier") or key in {"stop_distance_rate", "sizing_formula"}:
            continue
        if selected > caps[key]:
            return PositionSizingValidationResult("BLOCKED", f"selected notional exceeds {key}", "RISK_VETO")
    for key in (
        "volatility_multiplier",
        "drawdown_multiplier",
        "regime_multiplier",
        "correlation_multiplier",
        "realized_performance_multiplier",
        "combined_sizing_multiplier",
    ):
        if key not in caps and not require_current_sizing_model:
            continue
        value = _decimal(caps[key])
        if value < 0 or value > 1:
            return PositionSizingValidationResult("FAIL", f"sizing multiplier out of range: {key}", "SCHEMA_IDENTITY_MISMATCH")
    if decision.get("sizing_status") == "PASS" and decision.get("blockers"):
        return PositionSizingValidationResult("BLOCKED", "sizing PASS cannot carry blockers", decision["blockers"][0].get("code", "UNKNOWN_BLOCKED"))
    return PositionSizingValidationResult("PASS", "position sizing is min-of-caps and paper-scoped", None)
