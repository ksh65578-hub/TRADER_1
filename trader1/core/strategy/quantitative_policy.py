from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


QUANTITATIVE_POLICY_SCHEMA_ID = "trader1.quantitative_policy_report.v1"

SAFE_MODES = {"REPLAY", "PAPER", "SHADOW", "SAFE", "READ_ONLY"}
LIVE_FALSE_FLAGS = {
    "live_order_ready": False,
    "live_order_allowed": False,
    "can_live_trade": False,
    "scale_up_allowed": False,
}

REGIME_PRIORITY = [
    "panic",
    "data_bad",
    "downtrend",
    "uptrend",
    "range",
    "quiet",
    "uncertain",
]

EXIT_PRIORITY = [
    "kill_switch",
    "hard_stop",
    "position_uncertainty",
    "signal_invalidation",
    "regime_reversal",
    "time_stop",
    "partial_tp",
    "trailing_stop",
]

REQUIRED_MARKET_INPUTS = {
    "price",
    "ema20",
    "ema50",
    "ema200",
    "ema50_slope",
    "adx",
    "atr",
    "realized_volatility_zscore",
    "realized_volatility_percentile",
    "volume_zscore",
    "volume_percentile",
    "vwap_distance_atr",
    "spread_percentile",
    "liquidity_score",
    "data_health_score",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _num(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result != result:
        return default
    return result


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _round(value: float) -> float:
    return round(float(value), 6)


def _bool_score(condition: bool) -> float:
    return 1.0 if condition else 0.0


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _safe_mode(mode: str) -> bool:
    return str(mode).upper() in SAFE_MODES


def _primary_blocker(blockers: list[dict[str, str]]) -> str | None:
    return blockers[0]["code"] if blockers else None


def policy_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("policy_report_hash", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def classify_regime(inputs: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_MARKET_INPUTS - set(inputs))
    price = _num(inputs.get("price"))
    ema20 = _num(inputs.get("ema20"))
    ema50 = _num(inputs.get("ema50"))
    ema200 = _num(inputs.get("ema200"))
    ema50_slope = _num(inputs.get("ema50_slope"))
    adx = _num(inputs.get("adx"))
    atr = _num(inputs.get("atr"))
    vol_z = _num(inputs.get("realized_volatility_zscore"))
    vol_pct = _num(inputs.get("realized_volatility_percentile"))
    volume_z = _num(inputs.get("volume_zscore"))
    volume_pct = _num(inputs.get("volume_percentile"))
    vwap_distance_atr = _num(inputs.get("vwap_distance_atr"))
    spread_pct = _num(inputs.get("spread_percentile"))
    liquidity = _clamp(_num(inputs.get("liquidity_score")))
    data_health = _num(inputs.get("data_health_score"), default=0.0)

    trend_score = _round(
        0.30 * _bool_score(ema50 > ema200)
        + 0.20 * _bool_score(ema50_slope > 0)
        + 0.20 * _clamp((adx - 18.0) / 12.0)
        + 0.15 * _bool_score(price >= ema20)
        + 0.15 * liquidity
    )
    downtrend_score = _round(
        0.30 * _bool_score(ema50 < ema200)
        + 0.20 * _bool_score(ema50_slope < 0)
        + 0.20 * _clamp((adx - 18.0) / 12.0)
        + 0.15 * _bool_score(price <= ema20)
        + 0.15 * liquidity
    )
    range_score = _round(
        0.35 * _clamp((18.0 - adx) / 18.0)
        + 0.35 * _clamp((1.5 - abs(vwap_distance_atr)) / 1.5)
        + 0.15 * _clamp((80.0 - spread_pct) / 80.0)
        + 0.15 * liquidity
    )
    panic_score = _round(
        0.35 * _clamp(vol_z / 2.5)
        + 0.30 * _clamp(spread_pct / 95.0)
        + 0.20 * (1.0 - liquidity)
        + 0.15 * _clamp(volume_z / 3.0)
    )
    quiet_score = _round(
        0.40 * _clamp((20.0 - vol_pct) / 20.0)
        + 0.30 * _clamp((30.0 - volume_pct) / 30.0)
        + 0.20 * _clamp((18.0 - adx) / 18.0)
        + 0.10 * _clamp((80.0 - spread_pct) / 80.0)
    )
    scores = {
        "trend_score": trend_score,
        "range_score": range_score,
        "downtrend_score": downtrend_score,
        "panic_score": panic_score,
        "quiet_score": quiet_score,
    }

    blockers: list[dict[str, str]] = []
    if missing or data_health < 1.0 or atr <= 0 or price <= 0:
        blockers.append(
            _blocker(
                "DATA_QUALITY_INSUFFICIENT",
                "regime classification requires complete fresh inputs, positive price/ATR, and data_health_score=1.0",
                "HIGH",
            )
        )
        regime = "data_bad"
        confidence = 0.0
    elif vol_z >= 2.5 or spread_pct >= 95.0 or panic_score >= 0.80:
        regime = "panic"
        confidence = panic_score
    elif ema50 < ema200 and ema50_slope < 0 and adx >= 20.0 and downtrend_score >= 0.60:
        regime = "downtrend"
        confidence = downtrend_score
    elif ema50 > ema200 and ema50_slope > 0 and adx >= 20.0 and trend_score >= 0.60:
        regime = "uptrend"
        confidence = trend_score
    elif adx < 18.0 and abs(vwap_distance_atr) <= 1.5 and range_score >= 0.60:
        regime = "range"
        confidence = range_score
    elif vol_pct <= 20.0 and volume_pct <= 30.0 and quiet_score >= 0.60:
        regime = "quiet"
        confidence = quiet_score
    else:
        regime = "uncertain"
        confidence = min(max(scores.values()), 0.54)
        blockers.append(_blocker("REGIME_MISMATCH", "regime confidence below closed entry thresholds", "MEDIUM"))

    return {
        "regime": regime,
        "regime_confidence": _round(confidence),
        "scores": scores,
        "priority_order": REGIME_PRIORITY,
        "blockers": blockers,
        "primary_blocker_code": _primary_blocker(blockers),
    }


def score_symbol(inputs: dict[str, Any]) -> dict[str, Any]:
    liquidity = _clamp(_num(inputs.get("liquidity_score")))
    volatility = _clamp(_num(inputs.get("volatility_score")))
    relative_strength = _clamp(_num(inputs.get("relative_strength_score")))
    spread_quality = _clamp(_num(inputs.get("spread_quality_score")))
    volume_expansion = _clamp(_num(inputs.get("volume_expansion_score")))
    regime_fit = _clamp(_num(inputs.get("regime_fit_score")))
    data_health = _num(inputs.get("data_health_score"), default=0.0)
    score = _round(
        0.25 * liquidity
        + 0.20 * volatility
        + 0.20 * relative_strength
        + 0.15 * spread_quality
        + 0.10 * volume_expansion
        + 0.10 * regime_fit
    )
    blockers: list[dict[str, str]] = []
    if spread_quality < 0.50:
        blockers.append(_blocker("EXPECTED_SLIPPAGE_EXCEEDED", "spread_quality_score must be >= 0.50"))
    if liquidity < 0.60:
        blockers.append(_blocker("DEPTH_TOO_THIN", "liquidity_score must be >= 0.60"))
    if data_health < 1.0:
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "data_health_score must be 1.0"))
    return {
        "symbol_score": score,
        "eligible_for_entry_candidate": not blockers,
        "candidate_ranges": {
            "UPBIT": "top_20_to_40_universe_then_top_3_to_10_entry_candidates",
            "BINANCE_SPOT": "top_30_to_60_universe_then_top_3_to_10_entry_candidates",
            "BINANCE_FUTURES": "top_30_to_80_universe_then_top_3_to_10_entry_candidates",
        },
        "blockers": blockers,
        "primary_blocker_code": _primary_blocker(blockers),
    }


def grade_signal(inputs: dict[str, Any]) -> dict[str, Any]:
    score = _round(
        0.20 * _clamp(_num(inputs.get("regime_confidence")))
        + 0.20 * _clamp(_num(inputs.get("strategy_fit_score")))
        + 0.15 * _clamp(_num(inputs.get("confirmation_score")))
        + 0.15 * _clamp(_num(inputs.get("net_edge_score")))
        + 0.10 * _clamp(_num(inputs.get("liquidity_score")))
        + 0.10 * _clamp(_num(inputs.get("execution_quality_score")))
        + 0.10 * _clamp(_num(inputs.get("historical_pattern_score")))
    )
    if score < 0.55:
        grade = "no_trade"
    elif score < 0.65:
        grade = "weak"
    elif score < 0.75:
        grade = "normal"
    elif score < 0.85:
        grade = "strong"
    else:
        grade = "exceptional"
    blockers: list[dict[str, str]] = []
    if grade in {"no_trade", "weak"}:
        blockers.append(_blocker("STRATEGY_CONFIDENCE_LOW", "signal_score below 0.65 blocks entry"))
    return {
        "signal_score": score,
        "signal_grade": grade,
        "entry_candidate_allowed": grade in {"normal", "strong", "exceptional"},
        "live_candidate_input_grade": grade in {"strong", "exceptional"},
        "blockers": blockers,
        "primary_blocker_code": _primary_blocker(blockers),
    }


def compute_net_expected_edge(inputs: dict[str, Any]) -> dict[str, Any]:
    required = {
        "expected_target_move",
        "probability_of_target",
        "expected_stop_move",
        "probability_of_stop",
        "fee_cost",
        "spread_cost",
        "slippage_cost",
        "funding_cost",
    }
    missing = sorted(required - set(inputs))
    target = _num(inputs.get("expected_target_move"))
    p_target = _clamp(_num(inputs.get("probability_of_target")))
    stop = _num(inputs.get("expected_stop_move"))
    p_stop = _clamp(_num(inputs.get("probability_of_stop")))
    fee = _num(inputs.get("fee_cost"))
    spread = _num(inputs.get("spread_cost"))
    slippage = _num(inputs.get("slippage_cost"))
    funding = _num(inputs.get("funding_cost"))
    gross = _round(target * p_target - stop * p_stop)
    total_cost = _round(fee + spread + slippage + funding)
    net = _round(gross - total_cost)
    blockers: list[dict[str, str]] = []
    if missing:
        blockers.append(_blocker("FEE_MODEL_UNVERIFIED", f"cost model inputs missing: {missing}"))
    if total_cost <= 0:
        blockers.append(_blocker("FEE_MODEL_UNVERIFIED", "total_cost must be positive"))
    if net <= 0:
        blockers.append(_blocker("MIN_EDGE_FAIL", "net_expected_edge must be > 0"))
    return {
        "gross_expected_edge": gross,
        "total_cost": total_cost,
        "net_expected_edge": net,
        "net_edge_positive": net > 0 and total_cost > 0 and not missing,
        "high_return_candidate": net >= 1.5 * total_cost and total_cost > 0,
        "blockers": blockers,
        "primary_blocker_code": _primary_blocker(blockers),
    }


def evaluate_pullback_trend_entry(inputs: dict[str, Any]) -> dict[str, Any]:
    edge = inputs.get("edge") or compute_net_expected_edge(inputs)
    signal = inputs.get("signal") or grade_signal(inputs)
    blockers: list[dict[str, str]] = []
    mode = str(inputs.get("mode", "PAPER")).upper()
    regime = str(inputs.get("regime", "")).lower()
    if not _safe_mode(mode):
        blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "pullback entry evaluator cannot enable LIVE mode"))
    if regime != "uptrend":
        blockers.append(_blocker("REGIME_MISMATCH", "pullback trend entry requires regime=uptrend"))
    if _num(inputs.get("ema50")) <= _num(inputs.get("ema200")) or _num(inputs.get("ema50_slope")) <= 0:
        blockers.append(_blocker("REGIME_MISMATCH", "EMA50 must be above EMA200 and rising"))
    if _num(inputs.get("adx")) < 20.0:
        blockers.append(_blocker("REGIME_MISMATCH", "ADX must be >= 20"))
    pullback_depth_atr = _num(inputs.get("pullback_depth_atr"))
    if pullback_depth_atr < 0.30 or pullback_depth_atr > 1.50:
        blockers.append(_blocker("STRATEGY_NOT_ELIGIBLE", "pullback_depth_atr must be between 0.30 and 1.50"))
    if _num(inputs.get("price_distance_to_anchor_atr")) > 0.50:
        blockers.append(_blocker("STRATEGY_NOT_ELIGIBLE", "price must be near EMA20/EMA50/VWAP within 0.50 ATR"))
    if _num(inputs.get("confirmation_score")) < 0.65:
        blockers.append(_blocker("STRATEGY_CONFIDENCE_LOW", "confirmation_score must be >= 0.65"))
    if _num(signal.get("signal_score")) < 0.75:
        blockers.append(_blocker("STRATEGY_CONFIDENCE_LOW", "pullback live-candidate input requires signal_score >= 0.75"))
    blockers.extend(edge.get("blockers", []))
    return _entry_result(
        strategy_family="TREND_PULLBACK",
        side="LONG",
        candidate_allowed=not blockers,
        runtime_blocker_code=None,
        blockers=blockers,
    )


def evaluate_breakout_entry(inputs: dict[str, Any]) -> dict[str, Any]:
    edge = inputs.get("edge") or compute_net_expected_edge(inputs)
    blockers: list[dict[str, str]] = []
    regime = str(inputs.get("regime", "")).lower()
    if regime not in {"uptrend", "volatility_expansion"}:
        blockers.append(_blocker("REGIME_MISMATCH", "breakout entry requires uptrend or volatility_expansion"))
    atr = max(_num(inputs.get("atr")), 0.0000001)
    breakout_buffer_atr = _num(inputs.get("breakout_buffer_atr"))
    if breakout_buffer_atr < 0.20 or breakout_buffer_atr > 1.00:
        blockers.append(_blocker("STRATEGY_NOT_ELIGIBLE", "breakout_buffer must be 0.20 to 1.00 ATR"))
    close = _num(inputs.get("close"))
    recent_high = _num(inputs.get("recent_range_high"))
    if close <= recent_high + breakout_buffer_atr * atr:
        blockers.append(_blocker("STRATEGY_NOT_ELIGIBLE", "close must exceed recent_range_high plus breakout_buffer"))
    volume_expansion = _num(inputs.get("volume_expansion"))
    if volume_expansion < 1.20 or volume_expansion > 3.00:
        blockers.append(_blocker("STRATEGY_NOT_ELIGIBLE", "volume_expansion must be between 1.20x and 3.00x"))
    if _num(inputs.get("spread_percentile")) >= 80.0:
        blockers.append(_blocker("EXPECTED_SLIPPAGE_EXCEEDED", "breakout requires spread_percentile < 80"))
    if inputs.get("slippage_budget_ok") is not True:
        blockers.append(_blocker("EXPECTED_SLIPPAGE_EXCEEDED", "slippage_budget_ok must be true"))
    if _num(inputs.get("chase_candle_atr")) > 2.0:
        blockers.append(_blocker("MARKET_EVENT_RISK", "breakout chase candle exceeds 2.0 ATR"))
    if _num(inputs.get("expected_hold_candles")) < _num(inputs.get("min_hold_candles"), 2.0):
        blockers.append(_blocker("STRATEGY_NOT_ELIGIBLE", "breakout must be expected to hold for minimum candles"))
    blockers.extend(edge.get("blockers", []))
    return _entry_result("BREAKOUT_RETEST", "LONG", not blockers, None, blockers)


def evaluate_vwap_mean_reversion_entry(inputs: dict[str, Any]) -> dict[str, Any]:
    edge = inputs.get("edge") or compute_net_expected_edge(inputs)
    blockers: list[dict[str, str]] = []
    if str(inputs.get("regime", "")).lower() != "range":
        blockers.append(_blocker("REGIME_MISMATCH", "VWAP mean reversion requires regime=range"))
    adx = _num(inputs.get("adx"))
    if adx < 18.0 or adx > 22.0:
        blockers.append(_blocker("REGIME_MISMATCH", "VWAP mean reversion requires ADX between 18 and 22"))
    sigma_distance = abs(_num(inputs.get("vwap_sigma_distance")))
    if sigma_distance < 1.0 or sigma_distance > 2.5:
        blockers.append(_blocker("STRATEGY_NOT_ELIGIBLE", "abs(price - VWAP) must be 1.0 to 2.5 sigma"))
    if inputs.get("reversal_confirmation") is not True:
        blockers.append(_blocker("STRATEGY_CONFIDENCE_LOW", "reversal_confirmation must be true"))
    if inputs.get("trend_expansion") is True:
        blockers.append(_blocker("REGIME_MISMATCH", "trend_expansion blocks VWAP reversion"))
    if _num(inputs.get("range_regime_confidence")) < 0.65:
        blockers.append(_blocker("REGIME_MISMATCH", "range_regime_confidence must be >= 0.65"))
    if inputs.get("breakout_confirmation") is True:
        blockers.append(_blocker("REGIME_MISMATCH", "breakout confirmation blocks VWAP reversion"))
    if inputs.get("trend_volume_expansion") is True:
        blockers.append(_blocker("REGIME_MISMATCH", "trend-direction volume expansion blocks VWAP reversion"))
    blockers.extend(edge.get("blockers", []))
    return _entry_result("VWAP_REVERSION", "LONG", not blockers, None, blockers)


def evaluate_binance_futures_short_entry(inputs: dict[str, Any]) -> dict[str, Any]:
    edge = inputs.get("edge") or compute_net_expected_edge(inputs)
    blockers: list[dict[str, str]] = []
    exchange = str(inputs.get("exchange", "")).upper()
    market_type = str(inputs.get("market_type", "")).upper()
    if exchange != "BINANCE" or market_type != "FUTURES_USDT_M":
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "short entry requires BINANCE/FUTURES_USDT_M"))
    if _num(inputs.get("leverage")) != 1.0:
        blockers.append(_blocker("RISK_VETO", "Binance futures policy is fixed at 1x leverage"))
    if str(inputs.get("regime", "")).lower() != "downtrend":
        blockers.append(_blocker("REGIME_MISMATCH", "Binance futures short requires regime=downtrend"))
    if inputs.get("breakdown_confirmation") is not True:
        blockers.append(_blocker("STRATEGY_CONFIDENCE_LOW", "breakdown_confirmation must be true"))
    if inputs.get("failed_rebound") is not True and inputs.get("continuation_confirmation") is not True:
        blockers.append(_blocker("STRATEGY_CONFIDENCE_LOW", "failed_rebound or continuation_confirmation must be true"))
    if inputs.get("funding_cost_acceptable") is not True:
        blockers.append(_blocker("FEE_EXCEEDS_EDGE", "funding_cost_acceptable must be true"))
    if _num(inputs.get("liquidity_score")) < 0.60:
        blockers.append(_blocker("DEPTH_TOO_THIN", "liquidity_score must be >= 0.60"))
    if _num(inputs.get("spread_percentile")) >= 80.0:
        blockers.append(_blocker("EXPECTED_SLIPPAGE_EXCEEDED", "spread_percentile must be < 80"))
    if _num(inputs.get("panic_spread_percentile")) >= 95.0:
        blockers.append(_blocker("EXPECTED_SLIPPAGE_EXCEEDED", "panic spread blocks short entry"))
    if inputs.get("post_crash_chase") is True:
        blockers.append(_blocker("MARKET_EVENT_RISK", "do not chase short immediately after crash candle"))
    if inputs.get("rebound_volume_spike") is True:
        blockers.append(_blocker("MARKET_EVENT_RISK", "rebound volume spike blocks short entry"))
    if inputs.get("data_stale") is True:
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "stale data blocks short entry"))
    if inputs.get("reconciliation_mismatch") is True:
        blockers.append(_blocker("RECONCILIATION_REQUIRED", "reconciliation mismatch blocks short entry"))
    blockers.extend(edge.get("blockers", []))
    runtime_blocker = "BINANCE_FUTURES_SURFACE_ONLY"
    return _entry_result("BINANCE_FUTURES_SHORT", "SHORT", not blockers, runtime_blocker, blockers)


def _entry_result(
    strategy_family: str,
    side: str,
    candidate_allowed: bool,
    runtime_blocker_code: str | None,
    blockers: list[dict[str, str]],
) -> dict[str, Any]:
    runtime_blockers = list(blockers)
    if candidate_allowed and runtime_blocker_code:
        runtime_blockers.append(_blocker(runtime_blocker_code, "policy candidate exists but runtime adapter/order route is not enabled"))
    can_submit_order = candidate_allowed and runtime_blocker_code is None
    return {
        "strategy_family": strategy_family,
        "side": side,
        "candidate_allowed": candidate_allowed,
        "candidate_decision": f"ENTER_{side}" if candidate_allowed else "NO_TRADE",
        "runtime_decision": f"ENTER_{side}" if can_submit_order else "NO_TRADE",
        "can_submit_order": can_submit_order,
        "paper_candidate_scope": "PAPER_POLICY_CANDIDATE_ONLY" if runtime_blocker_code else "PAPER_RUNTIME_CANDIDATE",
        **LIVE_FALSE_FLAGS,
        "blockers": runtime_blockers,
        "primary_blocker_code": _primary_blocker(runtime_blockers),
    }


def build_exit_plan(inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    inputs = inputs or {}
    atr = max(_num(inputs.get("atr"), 1.0), 0.0000001)
    entry_price = _num(inputs.get("entry_price"), 100.0)
    side = str(inputs.get("side", "LONG")).upper()
    direction = 1.0 if side == "LONG" else -1.0
    hard_stop_atr = _clamp(_num(inputs.get("hard_stop_atr"), 1.2), 1.0, 1.8)
    tp1_atr = _clamp(_num(inputs.get("tp1_atr"), 1.2), 1.0, 1.5)
    tp2_atr = _clamp(_num(inputs.get("tp2_atr"), 2.5), 2.0, 4.0)
    trailing_start_atr = _clamp(_num(inputs.get("trailing_start_atr"), 1.5), 1.0, 2.5)
    trailing_distance_atr = _clamp(_num(inputs.get("trailing_distance_atr"), 1.0), 0.8, 1.8)
    partial_ratio = _clamp(_num(inputs.get("partial_take_profit_ratio"), 0.40), 0.30, 0.50)
    time_stop_candles = int(max(3, min(12, _num(inputs.get("time_stop_candles"), 8))))
    return {
        "side": side,
        "hard_stop": _round(entry_price - direction * hard_stop_atr * atr),
        "tp1": _round(entry_price + direction * tp1_atr * atr),
        "tp2": _round(entry_price + direction * tp2_atr * atr),
        "partial_take_profit_ratio": _round(partial_ratio),
        "trailing_start": _round(entry_price + direction * trailing_start_atr * atr),
        "trailing_distance": _round(trailing_distance_atr * atr),
        "time_stop_candles": time_stop_candles,
        "invalidation_rule": inputs.get("invalidation_rule", "regime_reversal_or_signal_score_below_0.55"),
        "exit_priority": EXIT_PRIORITY,
    }


def evaluate_risk_state(inputs: dict[str, Any]) -> dict[str, Any]:
    equity_high = max(_num(inputs.get("equity_high")), 0.0000001)
    current_equity = _num(inputs.get("current_equity"))
    drawdown_pct = _round((equity_high - current_equity) / equity_high)
    daily_loss = _num(inputs.get("daily_loss_pct"))
    weekly_loss = _num(inputs.get("weekly_loss_pct"))
    monthly_loss = _num(inputs.get("monthly_loss_pct"))
    consecutive_losses = int(_num(inputs.get("consecutive_losses")))
    blockers: list[dict[str, str]] = []
    if inputs.get("reconciliation_mismatch") is True or inputs.get("data_corruption") is True or inputs.get("live_safety_violation") is True:
        state = "kill_switch"
        blockers.append(_blocker("KILL_SWITCH_ACTIVE", "kill switch condition detected", "CRITICAL"))
    elif weekly_loss >= 0.03 or drawdown_pct >= 0.05 or monthly_loss >= 0.08:
        state = "no_trade"
        blockers.append(_blocker("DRAWDOWN_FREEZE_ACTIVE", "weekly, monthly, or total drawdown cap reached", "CRITICAL"))
    elif consecutive_losses >= 3 or daily_loss >= 0.01:
        state = "cooling"
        blockers.append(_blocker("COOLDOWN", "cooling state blocks new entries", "HIGH"))
    elif drawdown_pct >= 0.02:
        state = "risk_down"
        blockers.append(_blocker("RISK_VETO", "risk_down reduces position sizing", "MEDIUM"))
    else:
        state = "normal"
    return {
        "drawdown_pct": drawdown_pct,
        "risk_state": state,
        "new_entry_allowed": state in {"normal", "risk_down"},
        "daily_loss_cap_range": [0.01, 0.015],
        "weekly_loss_cap_range": [0.03, 0.04],
        "monthly_hard_stop_range": [0.08, 0.10],
        "blockers": blockers,
        "primary_blocker_code": _primary_blocker(blockers),
    }


def size_position(inputs: dict[str, Any]) -> dict[str, Any]:
    equity = _num(inputs.get("equity"))
    stop_distance = _num(inputs.get("stop_distance"))
    risk_per_trade = _clamp(_num(inputs.get("risk_per_trade"), 0.002), 0.001, 0.003)
    base_risk = equity * risk_per_trade
    signal_grade = str(inputs.get("signal_grade", "normal")).lower()
    signal_mult = {
        "no_trade": 0.0,
        "weak": 0.0,
        "normal": 0.5,
        "strong": 1.0,
        "exceptional": _clamp(_num(inputs.get("exceptional_multiplier"), 1.5), 1.5, 2.0),
    }.get(signal_grade, 0.0)
    regime_confidence = _clamp(_num(inputs.get("regime_confidence")))
    regime_mult = 0.5 if regime_confidence < 0.65 else 1.0 if regime_confidence < 0.85 else 1.15
    strategy_score = _clamp(_num(inputs.get("strategy_score")))
    strategy_mult = 0.5 if strategy_score < 0.65 else 1.0 if strategy_score < 0.85 else 1.15
    drawdown_pct = _num(inputs.get("drawdown_pct"))
    drawdown_mult = 1.0 if drawdown_pct < 0.02 else 0.50 if drawdown_pct < 0.05 else 0.0
    liquidity_score = _clamp(_num(inputs.get("liquidity_score")))
    liquidity_mult = 0.5 if liquidity_score < 0.70 else 1.0
    volatility_percentile = _num(inputs.get("volatility_percentile"), 50.0)
    volatility_mult = 0.75 if volatility_percentile >= 90.0 else 1.0
    risk_multiplier = _round(signal_mult * regime_mult * strategy_mult * drawdown_mult * liquidity_mult * volatility_mult)
    position_risk = _round(base_risk * risk_multiplier)
    raw_position_size = 0.0 if stop_distance <= 0 else position_risk / stop_distance
    blockers: list[dict[str, str]] = []
    if stop_distance <= 0:
        blockers.append(_blocker("RISK_VETO", "stop_distance must be > 0"))
    if _num(inputs.get("daily_loss_pct")) >= 0.01:
        blockers.append(_blocker("DRAWDOWN_FREEZE_ACTIVE", "daily loss cap reached"))
    if _num(inputs.get("weekly_loss_pct")) >= 0.03:
        blockers.append(_blocker("DRAWDOWN_FREEZE_ACTIVE", "weekly loss cap reached"))
    if _num(inputs.get("monthly_loss_pct")) >= 0.08:
        blockers.append(_blocker("DRAWDOWN_FREEZE_ACTIVE", "monthly hard stop reached"))
    max_exposure = _num(inputs.get("max_exposure"), equity * 0.40)
    current_exposure = _num(inputs.get("current_exposure"))
    if current_exposure >= max_exposure:
        blockers.append(_blocker("POSITION_LIMIT", "max exposure reached"))
    liquidity_notional = _num(inputs.get("liquidity_notional"), equity)
    if raw_position_size > liquidity_notional * 0.01:
        blockers.append(_blocker("DEPTH_TOO_THIN", "position size exceeds 1 percent of liquidity notional"))
    if signal_mult == 0.0:
        blockers.append(_blocker("STRATEGY_CONFIDENCE_LOW", "signal grade blocks sizing"))
    position_size = 0.0 if blockers else raw_position_size
    return {
        "base_risk": _round(base_risk),
        "risk_multiplier": risk_multiplier,
        "position_risk": _round(position_risk if not blockers else 0.0),
        "position_size": _round(position_size),
        "risk_per_trade_range": [0.001, 0.003],
        "grade_multipliers": {"normal": [0.25, 0.50], "strong": 1.0, "exceptional": [1.5, 2.0]},
        "blockers": blockers,
        "primary_blocker_code": _primary_blocker(blockers),
    }


def score_strategy(inputs: dict[str, Any]) -> dict[str, Any]:
    score = _round(
        0.25 * _clamp(_num(inputs.get("expectancy_score")))
        + 0.20 * _clamp(_num(inputs.get("profit_factor_score")))
        + 0.15 * _clamp(_num(inputs.get("drawdown_score")))
        + 0.15 * _clamp(_num(inputs.get("trade_count_confidence")))
        + 0.10 * _clamp(_num(inputs.get("regime_fit_score")))
        + 0.10 * _clamp(_num(inputs.get("execution_quality_score")))
        + 0.05 * _clamp(_num(inputs.get("stability_score")))
    )
    trade_count = int(_num(inputs.get("trade_count")))
    profit_factor = _num(inputs.get("profit_factor"))
    net_expectancy = _num(inputs.get("net_expectancy"))
    max_drawdown = _num(inputs.get("max_drawdown_pct"))
    fee_ratio = _num(inputs.get("fee_to_gross_profit_ratio"))
    oos_status = str(inputs.get("oos_status", "FAIL")).upper()
    stability_confirmed = inputs.get("stable_expectancy") is True
    recovery_confirmed = inputs.get("drawdown_recovery_confirmed") is True
    blockers: list[dict[str, str]] = []
    if net_expectancy <= 0:
        blockers.append(_blocker("MIN_EDGE_FAIL", "net_expectancy must be > 0"))
    if profit_factor < 1.10:
        blockers.append(_blocker("STRATEGY_NOT_ELIGIBLE", "profit_factor must be >= 1.10"))
    if trade_count < 100:
        blockers.append(_blocker("SAMPLE_INSUFFICIENT", "trade_count must be >= 100 for promotion evaluation"))
    if max_drawdown > 0.05:
        blockers.append(_blocker("DRAWDOWN_FREEZE_ACTIVE", "max_drawdown exceeds 5 percent promotion limit"))
    if fee_ratio > 0.35:
        blockers.append(_blocker("FEE_EXCEEDS_EDGE", "fee_to_gross_profit_ratio must be <= 0.35"))
    if oos_status != "PASS":
        blockers.append(_blocker("OOS_MISSING", "out-of-sample validation must PASS"))
    promotion_eligible = not blockers and trade_count >= 100 and profit_factor >= 1.25 and net_expectancy > 0
    high_return_candidate = (
        promotion_eligible
        and trade_count >= 300
        and profit_factor >= 1.35
        and stability_confirmed
        and recovery_confirmed
    )
    return {
        "strategy_score": score,
        "eliminated": bool(blockers),
        "promotion_eligible": promotion_eligible,
        "high_return_candidate": high_return_candidate,
        "promotion_thresholds": {
            "trade_count": 100,
            "high_return_trade_count": 300,
            "profit_factor": 1.25,
            "high_return_profit_factor": 1.35,
            "net_expectancy": ">0",
            "max_drawdown_pct": "<=0.05",
            "fee_to_gross_profit_ratio": "<=0.35",
            "oos_status": "PASS",
        },
        **LIVE_FALSE_FLAGS,
        "blockers": blockers,
        "primary_blocker_code": _primary_blocker(blockers),
    }


def allocate_capital(strategies: list[dict[str, Any]]) -> dict[str, Any]:
    allocations: list[dict[str, Any]] = []
    for index, strategy in enumerate(strategies):
        status = str(strategy.get("status", "experimental")).lower()
        if status == "disabled":
            cap = 0.0
        elif status == "deteriorating":
            cap = min(_num(strategy.get("requested_risk_budget"), 0.05), 0.05)
        elif status == "experimental":
            cap = min(max(_num(strategy.get("requested_risk_budget"), 0.05), 0.05), 0.10)
        elif status == "secondary":
            cap = min(max(_num(strategy.get("requested_risk_budget"), 0.20), 0.20), 0.30)
        elif status == "top":
            cap = min(_num(strategy.get("requested_risk_budget"), 0.40), 0.40)
        else:
            cap = 0.0
        allocations.append({"strategy_id": strategy.get("strategy_id", f"strategy_{index}"), "status": status, "risk_budget": _round(cap)})
    total = sum(item["risk_budget"] for item in allocations)
    if total > 1.0:
        scale = 1.0 / total
        for item in allocations:
            item["risk_budget"] = _round(item["risk_budget"] * scale)
    return {
        "allocations": allocations,
        "rules": {
            "top_strategy_max": 0.40,
            "secondary_strategy_range": [0.20, 0.30],
            "experimental_range": [0.05, 0.10],
            "deteriorating_range": [0.0, 0.05],
            "disabled": 0.0,
        },
        "forbidden": [
            "no_averaging_down_losing_strategy",
            "no_risk_increase_to_hit_monthly_target",
            "no_large_capital_to_unverified_strategy",
        ],
    }


def evaluate_live_ready_snapshot_candidate(inputs: dict[str, Any]) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    if inputs.get("snapshot_present") is not True:
        blockers.append(_blocker("LIVE_READY_MISSING", "LIVE_READY snapshot is absent"))
    if int(_num(inputs.get("trade_count"))) < 100:
        blockers.append(_blocker("SAMPLE_INSUFFICIENT", "trade_count must be >= 100"))
    if inputs.get("high_return_candidate") is True and int(_num(inputs.get("trade_count"))) < 300:
        blockers.append(_blocker("SAMPLE_INSUFFICIENT", "high-return candidate requires trade_count >= 300"))
    if _num(inputs.get("profit_factor")) < (1.35 if inputs.get("high_return_candidate") is True else 1.25):
        blockers.append(_blocker("STRATEGY_NOT_ELIGIBLE", "profit_factor below promotion threshold"))
    if _num(inputs.get("net_expectancy")) <= 0:
        blockers.append(_blocker("MIN_EDGE_FAIL", "net_expectancy must be > 0"))
    for field, code, message in [
        ("costs_reflected", "COST_AFTER_EDGE_UNVERIFIED", "fee/slippage/funding costs must be reflected"),
        ("max_drawdown_within_limit", "DRAWDOWN_FREEZE_ACTIVE", "max drawdown must be within limit"),
        ("regime_breakdown_verified", "REGIME_FIT_UNTESTED", "regime breakdown verification required"),
        ("symbol_concentration_verified", "SYMBOL_SELECTION_BIAS", "symbol concentration verification required"),
        ("reconciliation_clean", "RECONCILIATION_REQUIRED", "reconciliation must be clean"),
        ("data_health_pass", "DATA_QUALITY_INSUFFICIENT", "data health must PASS"),
        ("live_block_proof_pass", "LIVE_FINAL_GUARD_FAILED", "live block proof must PASS"),
        ("official_api_verified", "API_UNVERIFIED", "official API verification required before live readiness"),
        ("operator_approved", "OPERATOR_APPROVAL_MISSING", "operator approval required before live readiness"),
        ("read_only_burn_in_pass", "READ_ONLY_BURN_IN_MISSING", "read-only burn-in evidence required"),
    ]:
        if inputs.get(field) is not True:
            blockers.append(_blocker(code, message))
    return {
        "snapshot_candidate_metrics_pass": not blockers,
        "writer_input_eligible": False,
        **LIVE_FALSE_FLAGS,
        "blockers": blockers,
        "primary_blocker_code": _primary_blocker(blockers),
    }


def deduplicate_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    duplicates: list[str] = []
    for event in events:
        event_id = str(event.get("event_id", "")).strip()
        if not event_id:
            duplicates.append("<missing_event_id>")
            continue
        if event_id in seen:
            duplicates.append(event_id)
            continue
        seen.add(event_id)
        unique.append(event)
    return {
        "unique_events": unique,
        "duplicate_event_ids": duplicates,
        "input_count": len(events),
        "unique_count": len(unique),
        "duplicate_count": len(duplicates),
        "idempotent": True,
    }


def build_quantitative_policy_report(*, report_id: str = "quantitative_policy_closure_report") -> dict[str, Any]:
    regime = classify_regime(
        {
            "price": 100.0,
            "ema20": 99.0,
            "ema50": 98.0,
            "ema200": 90.0,
            "ema50_slope": 0.15,
            "adx": 25.0,
            "atr": 2.0,
            "realized_volatility_zscore": 0.7,
            "realized_volatility_percentile": 55.0,
            "volume_zscore": 0.5,
            "volume_percentile": 55.0,
            "vwap_distance_atr": 0.4,
            "spread_percentile": 40.0,
            "liquidity_score": 0.82,
            "data_health_score": 1.0,
        }
    )
    symbol = score_symbol(
        {
            "liquidity_score": 0.82,
            "volatility_score": 0.65,
            "relative_strength_score": 0.70,
            "spread_quality_score": 0.76,
            "volume_expansion_score": 0.62,
            "regime_fit_score": 0.74,
            "data_health_score": 1.0,
        }
    )
    edge = compute_net_expected_edge(
        {
            "expected_target_move": 0.020,
            "probability_of_target": 0.58,
            "expected_stop_move": 0.010,
            "probability_of_stop": 0.42,
            "fee_cost": 0.0010,
            "spread_cost": 0.0005,
            "slippage_cost": 0.0007,
            "funding_cost": 0.0,
        }
    )
    signal = grade_signal(
        {
            "regime_confidence": regime["regime_confidence"],
            "strategy_fit_score": 0.82,
            "confirmation_score": 0.80,
            "net_edge_score": 0.78,
            "liquidity_score": 0.82,
            "execution_quality_score": 0.75,
            "historical_pattern_score": 0.70,
        }
    )
    risk = evaluate_risk_state(
        {
            "equity_high": 1_000_000,
            "current_equity": 990_000,
            "daily_loss_pct": 0.004,
            "weekly_loss_pct": 0.006,
            "monthly_loss_pct": 0.010,
            "consecutive_losses": 1,
        }
    )
    live_ready = evaluate_live_ready_snapshot_candidate({"snapshot_present": False})
    blockers = live_ready["blockers"]
    report = {
        "schema_id": QUANTITATIVE_POLICY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "policy_report_id": report_id,
        "policy_status": "IMPLEMENTED_LIVE_BLOCKED",
        "law_of_large_numbers_basis": {
            "minimum_trade_count": 100,
            "high_return_candidate_trade_count": 300,
            "walk_forward_required": True,
            "out_of_sample_required": True,
            "bootstrap_stability_required": True,
        },
        "regime_policy": regime,
        "symbol_policy": symbol,
        "signal_policy": signal,
        "edge_policy": edge,
        "exit_policy": build_exit_plan({"entry_price": 100.0, "atr": 2.0, "side": "LONG"}),
        "risk_policy": risk,
        "capital_allocation_policy": allocate_capital(
            [
                {"strategy_id": "top_fixture", "status": "top", "requested_risk_budget": 0.45},
                {"strategy_id": "experimental_fixture", "status": "experimental", "requested_risk_budget": 0.12},
            ]
        ),
        "live_ready_policy": live_ready,
        "dashboard_reason_code": live_ready["primary_blocker_code"],
        "dashboard_operator_message": "LIVE blocked: LIVE_READY snapshot and external live evidence are missing.",
        **LIVE_FALSE_FLAGS,
        "blockers": blockers,
        "policy_report_hash": "",
    }
    report["policy_report_hash"] = policy_report_hash(report)
    return report
