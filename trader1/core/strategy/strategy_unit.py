from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


STRATEGY_UNIT_SCHEMA_ID = "trader1.strategy_unit.v1"


@dataclass(frozen=True)
class StrategyUnitValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def strategy_unit_hash(unit: dict[str, Any]) -> str:
    payload = dict(unit)
    payload.pop("strategy_unit_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def _parameter_hash(strategy_id: str, strategy_build_id: str) -> str:
    return hashlib.sha256(f"{strategy_id}:{strategy_build_id}:mvp3".encode("utf-8")).hexdigest().upper()


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def build_basic_strategy_unit(
    *,
    strategy_unit_id: str,
    strategy_id: str = "basic_momentum_fixture",
    strategy_build_id: str = "mvp3_fixture_001",
    parameter_hash: str | None = None,
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "PAPER",
    session_id: str = "mvp3_operational_paper",
    timeframe_scope: str = "15m",
    regime_scope: str = "RANGE",
    risk_profile: str = "CONSERVATIVE",
    signal_intent: str = "ENTER_LONG",
    signal_strength: str = "0.60",
    strategy_confidence: str = "0.55",
    regime_confidence: str = "0.55",
    source_evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    if exchange != "UPBIT" or market_type != "KRW_SPOT" or mode not in {"PAPER", "SHADOW"}:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "strategy unit is scoped to UPBIT/KRW_SPOT PAPER or SHADOW"))
    if signal_intent not in {"ENTER_LONG", "NO_TRADE"}:
        blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "strategy unit signal intent is not allowed in MVP-3"))
    unit = {
        "schema_id": STRATEGY_UNIT_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "strategy_unit_id": strategy_unit_id,
        "strategy_id": strategy_id,
        "strategy_build_id": strategy_build_id,
        "parameter_hash": parameter_hash or _parameter_hash(strategy_id, strategy_build_id),
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "timeframe_scope": timeframe_scope,
        "regime_scope": regime_scope,
        "risk_profile": risk_profile,
        "signal_intent": signal_intent,
        "signal_strength": signal_strength,
        "strategy_confidence": strategy_confidence,
        "regime_confidence": regime_confidence,
        "source_evidence_ids": source_evidence_ids or [],
        "strategy_level": "LEVEL_2_OPERATIONAL_PAPER" if mode == "PAPER" else "LEVEL_1_PAPER_DRY_RUN",
        "paper_live_namespace_separated": mode in {"PAPER", "SHADOW"},
        "exchange_market_type_separated": exchange == "UPBIT" and market_type == "KRW_SPOT",
        "strategy_order_adapter_called": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "blockers": blockers,
        "strategy_unit_hash": "",
    }
    unit["strategy_unit_hash"] = strategy_unit_hash(unit)
    return unit


def validate_strategy_unit(unit: dict[str, Any]) -> StrategyUnitValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "strategy_unit_id",
        "strategy_id",
        "strategy_build_id",
        "parameter_hash",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "timeframe_scope",
        "regime_scope",
        "risk_profile",
        "signal_intent",
        "signal_strength",
        "strategy_confidence",
        "regime_confidence",
        "source_evidence_ids",
        "strategy_level",
        "paper_live_namespace_separated",
        "exchange_market_type_separated",
        "strategy_order_adapter_called",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "blockers",
        "strategy_unit_hash",
    }
    missing = sorted(required - set(unit))
    if missing:
        return StrategyUnitValidationResult("FAIL", f"strategy unit missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if unit.get("schema_id") != STRATEGY_UNIT_SCHEMA_ID:
        return StrategyUnitValidationResult("FAIL", "strategy unit schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if unit.get("strategy_unit_hash") != strategy_unit_hash(unit):
        return StrategyUnitValidationResult("FAIL", "strategy unit hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if unit.get("exchange") != "UPBIT" or unit.get("market_type") != "KRW_SPOT" or unit.get("mode") not in {"PAPER", "SHADOW"}:
        return StrategyUnitValidationResult("BLOCKED", "strategy unit scope must remain UPBIT/KRW_SPOT PAPER or SHADOW", "SNAPSHOT_SCOPE_MISMATCH")
    if unit.get("strategy_order_adapter_called"):
        return StrategyUnitValidationResult("BLOCKED", "strategy unit cannot call an order adapter directly", "LIVE_FINAL_GUARD_FAILED")
    if unit.get("live_order_ready") or unit.get("live_order_allowed") or unit.get("can_live_trade"):
        return StrategyUnitValidationResult("BLOCKED", "strategy unit attempted to create live permission", "LIVE_FINAL_GUARD_FAILED")
    if unit.get("paper_live_namespace_separated") is not True or unit.get("exchange_market_type_separated") is not True:
        return StrategyUnitValidationResult("BLOCKED", "strategy unit namespace separation failed", "SNAPSHOT_SCOPE_MISMATCH")
    if unit.get("blockers"):
        return StrategyUnitValidationResult("BLOCKED", "strategy unit carries blockers", unit["blockers"][0].get("code", "UNKNOWN_BLOCKED"))
    return StrategyUnitValidationResult("PASS", "strategy unit is paper/shadow scoped and non-ordering", None)
