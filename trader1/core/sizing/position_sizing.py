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
}


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
    }


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("-1")


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


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
    equity_cap = max(Decimal("0"), equity * Decimal("0.01"))
    cash_cap = max(Decimal("0"), available_cash * Decimal("0.05"))
    risk_cap = max(Decimal("0"), equity * Decimal("0.02") - open_risk)
    liquidity_cap = max(Decimal("0"), min(liquidity, orderbook_depth) * Decimal("0.01"))
    exposure_cap = max(Decimal("0"), (equity * Decimal("0.35")) - current_exposure)
    confidence_cap = min(signal_strength, strategy_confidence, regime_confidence)
    if current_exposure > equity * Decimal("0.35"):
        blockers.append(_blocker("RISK_VETO", "current exposure exceeds 35% PAPER equity cap"))
    if available_cash <= 0:
        blockers.append(_blocker("RISK_VETO", "available PAPER cash is zero or locked"))
    selected = (min(equity_cap, cash_cap, risk_cap, liquidity_cap, exposure_cap) * confidence_cap).quantize(
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
        "confidence_cap": str(confidence_cap),
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
    if missing_inputs:
        return PositionSizingValidationResult("BLOCKED", f"sizing inputs missing: {missing_inputs}", "MEASUREMENT_MISSING")
    selected = _decimal(decision.get("selected_notional", "0"))
    caps = {key: _decimal(value) for key, value in decision.get("caps", {}).items()}
    required_cap_keys = ["equity_cap", "cash_cap", "risk_cap", "liquidity_cap"]
    if require_exposure_cap:
        required_cap_keys.append("exposure_cap")
    for key in required_cap_keys:
        if key not in caps:
            return PositionSizingValidationResult("FAIL", f"sizing cap missing: {key}", "SCHEMA_IDENTITY_MISMATCH")
        if selected > caps[key]:
            return PositionSizingValidationResult("BLOCKED", f"selected notional exceeds {key}", "RISK_VETO")
    if decision.get("sizing_status") == "PASS" and decision.get("blockers"):
        return PositionSizingValidationResult("BLOCKED", "sizing PASS cannot carry blockers", decision["blockers"][0].get("code", "UNKNOWN_BLOCKED"))
    return PositionSizingValidationResult("PASS", "position sizing is min-of-caps and paper-scoped", None)
