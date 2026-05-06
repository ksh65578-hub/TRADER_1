from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture, validate_upbit_public_candle_data
from trader1.adapters.upbit.symbol_rules import validate_upbit_krw_symbol
from trader1.core.decision.decision_arbiter import order_blocker_codes, select_primary_blocker
from trader1.core.ledger.paper_ledger import build_upbit_paper_fill_chain, validate_upbit_paper_ledger
from trader1.core.sizing.position_sizing import (
    build_position_sizing_decision,
    default_sizing_inputs,
    validate_position_sizing_decision,
)
from trader1.core.strategy.quantitative_policy import (
    build_exit_plan,
    build_quantitative_policy_report,
    evaluate_risk_state,
)
from trader1.dashboard.summary_writer import build_summary_shell, validate_summary_shell
from trader1.runtime.portfolio.paper_portfolio import (
    build_initial_paper_portfolio_snapshot,
    build_paper_portfolio_snapshot_from_fill,
    validate_paper_portfolio_snapshot,
)
from trader1.runtime.paper.upbit_public_collector import (
    public_market_data_hash,
    validate_upbit_public_market_data_collection_report,
)


UPBIT_PAPER_RUNTIME_CYCLE_SCHEMA_ID = "trader1.upbit_paper_runtime_cycle_report.v1"
SAFE_FINAL_DECISIONS = {"ENTER_LONG", "NO_TRADE", "BLOCKED", "SAFE_MODE", "RECONCILE_REQUIRED"}
PAPER_ENTRY_FEE_RATE = Decimal("0.0005")
PAPER_ENTRY_SLIPPAGE_BPS = Decimal("5")
UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL = Decimal("5000")
MIN_SYMBOL_SELECTION_SCORE = Decimal("0.60")
MIN_ENTRY_NET_EV_BPS = Decimal("5")
MIN_ENTRY_SIGNAL_STRENGTH = Decimal("0.55")
MIN_EXIT_ATR_RATE = Decimal("0.003")


@dataclass(frozen=True)
class UpbitPaperRuntimeCycleValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("-1")


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f") if value != value.to_integral() else str(value.quantize(Decimal("1")))


def _clamp_decimal(value: Decimal, low: Decimal = Decimal("0"), high: Decimal = Decimal("1")) -> Decimal:
    return max(low, min(high, value))


def _hash_report(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("cycle_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _paper_cash_bound_sizing_inputs(
    *,
    paper_cash_available: str | int | float | Decimal | None,
    paper_equity: str | int | float | Decimal | None,
    paper_position_market_value: str | int | float | Decimal | None,
    paper_cash_source: str,
) -> tuple[dict[str, Any], list[dict[str, str]], Decimal | None]:
    inputs = default_sizing_inputs()
    if paper_cash_available is None:
        return inputs, [], None

    cash_available = _decimal(paper_cash_available)
    equity = _decimal(paper_equity if paper_equity is not None else paper_cash_available)
    position_market_value = _decimal(paper_position_market_value or "0")
    blockers: list[dict[str, str]] = []
    if cash_available < 0 or equity < 0 or position_market_value < 0:
        blockers.append(_blocker("RISK_VETO", "PAPER cash guard received negative ledger-backed cash, equity, or exposure"))
    inputs.update(
        {
            "equity": _decimal_text(max(Decimal("0"), equity)),
            "cash": _decimal_text(max(Decimal("0"), cash_available)),
            "locked_cash": "0",
            "current_exposure": _decimal_text(max(Decimal("0"), position_market_value)),
            "paper_cash_guard_source": paper_cash_source,
            "paper_cash_available": _decimal_text(cash_available),
            "paper_equity": _decimal_text(equity),
            "paper_position_market_value": _decimal_text(position_market_value),
            "paper_min_entry_notional_krw": _decimal_text(UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL),
            "paper_entry_fee_rate": _decimal_text(PAPER_ENTRY_FEE_RATE),
        }
    )
    return inputs, blockers, cash_available


def _candidate_sizing_inputs(
    *,
    base_inputs: dict[str, Any],
    selected_candidate: dict[str, Any],
    features: dict[str, Any],
    risk_state: dict[str, Any],
) -> dict[str, Any]:
    inputs = dict(base_inputs)
    costs = selected_candidate.get("cost_breakdown_bps", {})
    risk_multiplier = Decimal("0.50") if risk_state.get("risk_state") == "risk_down" else Decimal("1.00")
    symbol_score = _decimal(selected_candidate.get("symbol_selection_score"))
    strategy_confidence = _clamp_decimal(symbol_score * risk_multiplier)
    regime_confidence = {
        "UPTREND": Decimal("0.75"),
        "RANGE": Decimal("0.65"),
        "RISK_OFF": Decimal("0.00"),
    }.get(str(features.get("regime")), Decimal("0.00"))
    quote_volume = max(Decimal("0"), _decimal(features.get("total_quote_volume")))
    volatility_rate = max(Decimal("0"), _decimal(features.get("volatility_pct")) / Decimal("100"))
    inputs.update(
        {
            "volatility": _decimal_text(volatility_rate),
            "liquidity": _decimal_text(quote_volume),
            "spread": _decimal_text(max(Decimal("0"), _decimal(features.get("spread_bps"))) / Decimal("10000")),
            "orderbook_depth": _decimal_text(max(Decimal("0"), quote_volume * Decimal("0.10"))),
            "signal_strength": selected_candidate.get("signal_strength", "0"),
            "strategy_confidence": _decimal_text(strategy_confidence),
            "regime_confidence": _decimal_text(regime_confidence),
            "strategy_score": selected_candidate.get("symbol_selection_score", "0"),
            "fee": _decimal_text(max(Decimal("0"), _decimal(costs.get("fee_bps"))) / Decimal("10000")),
            "slippage": _decimal_text(max(Decimal("0"), _decimal(costs.get("slippage_bps"))) / Decimal("10000")),
            "market_impact": _decimal_text(max(Decimal("0"), _decimal(costs.get("market_impact_bps"))) / Decimal("10000")),
            "risk_state": str(risk_state.get("risk_state") or "unknown"),
            "risk_drawdown_pct": str(risk_state.get("drawdown_pct", "0")),
            "orderbook_depth_source": "PUBLIC_CANDLE_QUOTE_VOLUME_10PCT_PROXY",
            "sizing_formula": "min(equity_cap,cash_cap,risk_cap,liquidity_cap,exposure_cap)*min(signal,strategy,regime)",
        }
    )
    return inputs


def _candidate_selection_score_value(*, symbol_score: Decimal, net_ev_bps: Decimal, signal_strength: Decimal) -> Decimal:
    net_ev_score = _clamp_decimal((net_ev_bps - MIN_ENTRY_NET_EV_BPS) / Decimal("35"))
    score = Decimal("0.45") * symbol_score + Decimal("0.35") * net_ev_score + Decimal("0.20") * signal_strength
    return score.quantize(Decimal("0.0001"))


def _candidate_rank_key(candidate: dict[str, Any]) -> tuple[Decimal, Decimal, int]:
    return (
        _decimal(candidate.get("candidate_selection_score")),
        _decimal(candidate.get("net_ev_after_cost_bps")),
        -int(candidate.get("selection_priority", 999)),
    )


def _build_runtime_risk_state(
    *,
    starting_cash: str | int | float | Decimal,
    sizing_inputs: dict[str, Any],
    data_blocked: bool,
) -> dict[str, Any]:
    starting = max(_decimal(starting_cash), Decimal("0.0000001"))
    current_equity = max(_decimal(sizing_inputs.get("equity")), Decimal("0"))
    equity_high = max(starting, current_equity, Decimal("0.0000001"))
    loss_pct = Decimal("0") if starting <= 0 else max(Decimal("0"), (starting - current_equity) / starting)
    risk_state = evaluate_risk_state(
        {
            "equity_high": _decimal_text(equity_high),
            "current_equity": _decimal_text(current_equity),
            "daily_loss_pct": _decimal_text(loss_pct),
            "weekly_loss_pct": _decimal_text(loss_pct),
            "monthly_loss_pct": _decimal_text(loss_pct),
            "consecutive_losses": sizing_inputs.get("loss_streak", "0"),
            "reconciliation_mismatch": False,
            "data_corruption": data_blocked,
            "live_safety_violation": False,
        }
    )
    risk_state.update(
        {
            "risk_source": "LEDGER_BACKED_PAPER_CASH_AND_EQUITY_INPUTS",
            "entry_blocking_states": ["kill_switch", "no_trade", "cooling"],
            "risk_down_sizing_multiplier": "0.50",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    return risk_state


def _build_runtime_exit_plan(
    *,
    selected_candidate: dict[str, Any],
    features: dict[str, Any],
) -> dict[str, Any]:
    entry_price = max(_decimal(features.get("last_price")), Decimal("0"))
    volatility_rate = max(MIN_EXIT_ATR_RATE, _decimal(features.get("volatility_pct")) / Decimal("100"))
    atr_proxy = max(Decimal("0.0000001"), entry_price * volatility_rate)
    plan = build_exit_plan(
        {
            "entry_price": _decimal_text(entry_price),
            "atr": _decimal_text(atr_proxy),
            "side": "LONG",
            "hard_stop_atr": "1.2",
            "tp1_atr": "1.2",
            "tp2_atr": "2.5",
            "trailing_start_atr": "1.5",
            "trailing_distance_atr": "1.0",
            "partial_take_profit_ratio": "0.40",
            "time_stop_candles": "8",
            "invalidation_rule": "regime_reversal_or_signal_score_below_0.55",
        }
    )
    plan.update(
        {
            "exit_plan_source": "PAPER_RUNTIME_FEATURE_ATR_PROXY",
            "entry_price": _decimal_text(entry_price),
            "atr_proxy": _decimal_text(atr_proxy),
            "source_candidate_id": selected_candidate.get("candidate_id"),
            "source_symbol": selected_candidate.get("symbol"),
            "activation_condition": "ACTIVE_AFTER_PAPER_FILL_ONLY",
            "hard_stop_formula": "entry_price - 1.2*atr_proxy",
            "tp1_formula": "entry_price + 1.2*atr_proxy",
            "tp2_formula": "entry_price + 2.5*atr_proxy",
            "trailing_formula": "start_after_1.5*atr_proxy_then_distance_1.0*atr_proxy",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    return plan


def _ema(values: list[Decimal], period: int) -> Decimal:
    if not values:
        return Decimal("0")
    alpha = Decimal("2") / Decimal(period + 1)
    current = values[0]
    for value in values[1:]:
        current = (value * alpha) + (current * (Decimal("1") - alpha))
    return current


def _feature_snapshot(market_data: dict[str, Any]) -> dict[str, Any]:
    candles = market_data["candles"]
    closes = [_decimal(candle["close"]) for candle in candles]
    volumes = [_decimal(candle["volume"]) for candle in candles]
    typical_values = [
        (_decimal(candle["high"]) + _decimal(candle["low"]) + _decimal(candle["close"])) / Decimal("3")
        for candle in candles
    ]
    total_volume = sum(volumes, Decimal("0"))
    vwap = sum(price * volume for price, volume in zip(typical_values, volumes)) / total_volume
    total_quote_volume = sum(close * volume for close, volume in zip(closes, volumes))
    last = closes[-1]
    first = closes[0]
    previous_high = max(_decimal(candle["high"]) for candle in candles[:-1])
    ema_fast = _ema(closes, 3)
    ema_slow = _ema(closes, 5)
    high = max(closes)
    low = min(closes)
    volatility_pct = Decimal("0") if last <= 0 else ((high - low) / last * Decimal("100"))
    momentum_pct = Decimal("0") if first <= 0 else ((last - first) / first * Decimal("100"))
    average_prior_volume = sum(volumes[:-1], Decimal("0")) / Decimal(max(1, len(volumes) - 1))
    volume_expansion_ratio = Decimal("0") if average_prior_volume <= 0 else volumes[-1] / average_prior_volume
    vwap_distance_pct = Decimal("0") if last <= 0 else ((last - vwap) / last * Decimal("100"))
    range_breakout_pct = Decimal("0") if last <= 0 else ((last - previous_high) / last * Decimal("100"))
    if ema_fast > ema_slow and last >= ema_slow:
        regime = "UPTREND"
    elif ema_fast < ema_slow and last < ema_slow:
        regime = "RISK_OFF"
    else:
        regime = "RANGE"
    return {
        "source": market_data.get("source", "UNAVAILABLE"),
        "symbol": market_data["symbol"],
        "last_price": _decimal_text(last),
        "previous_high": _decimal_text(previous_high),
        "vwap": _decimal_text(vwap),
        "ema_fast": _decimal_text(ema_fast),
        "ema_slow": _decimal_text(ema_slow),
        "volatility_pct": _decimal_text(volatility_pct),
        "momentum_pct": _decimal_text(momentum_pct),
        "total_quote_volume": _decimal_text(total_quote_volume),
        "volume_expansion_ratio": _decimal_text(volume_expansion_ratio),
        "vwap_distance_pct": _decimal_text(vwap_distance_pct),
        "range_breakout_pct": _decimal_text(range_breakout_pct),
        "spread_bps": "1.00",
        "liquidity_status": "PASS",
        "volatility_status": "PASS" if volatility_pct < Decimal("6") else "WARN",
        "regime": regime,
    }


def _volatility_score(volatility_pct: Decimal) -> Decimal:
    if volatility_pct <= 0:
        return Decimal("0")
    if volatility_pct < Decimal("0.40"):
        return _clamp_decimal(volatility_pct / Decimal("0.40") * Decimal("0.50"))
    if volatility_pct <= Decimal("4.00"):
        return Decimal("1")
    if volatility_pct <= Decimal("8.00"):
        return _clamp_decimal((Decimal("8.00") - volatility_pct) / Decimal("4.00"))
    return Decimal("0")


def _symbol_selection_score(features: dict[str, Any]) -> dict[str, str]:
    regime = str(features.get("regime"))
    regime_fit = {
        "UPTREND": Decimal("1.00"),
        "RANGE": Decimal("0.65"),
        "RISK_OFF": Decimal("0.00"),
    }.get(regime, Decimal("0.00"))
    liquidity_score = _clamp_decimal(_decimal(features.get("total_quote_volume")) / Decimal("30000000"))
    volatility_score = _volatility_score(_decimal(features.get("volatility_pct")))
    relative_strength_score = _clamp_decimal((_decimal(features.get("momentum_pct")) + Decimal("0.50")) / Decimal("3.00"))
    spread_quality_score = _clamp_decimal((Decimal("5.00") - _decimal(features.get("spread_bps"))) / Decimal("5.00"))
    volume_expansion_score = _clamp_decimal((_decimal(features.get("volume_expansion_ratio")) - Decimal("0.80")) / Decimal("1.20"))
    score = (
        Decimal("0.25") * liquidity_score
        + Decimal("0.20") * volatility_score
        + Decimal("0.20") * relative_strength_score
        + Decimal("0.15") * spread_quality_score
        + Decimal("0.10") * volume_expansion_score
        + Decimal("0.10") * regime_fit
    )
    return {
        "symbol_selection_score": _decimal_text(score.quantize(Decimal("0.0001"))),
        "liquidity_score": _decimal_text(liquidity_score.quantize(Decimal("0.0001"))),
        "volatility_score": _decimal_text(volatility_score.quantize(Decimal("0.0001"))),
        "relative_strength_score": _decimal_text(relative_strength_score.quantize(Decimal("0.0001"))),
        "spread_quality_score": _decimal_text(spread_quality_score.quantize(Decimal("0.0001"))),
        "volume_expansion_score": _decimal_text(volume_expansion_score.quantize(Decimal("0.0001"))),
        "regime_fit_score": _decimal_text(regime_fit.quantize(Decimal("0.0001"))),
        "minimum_symbol_selection_score": _decimal_text(MIN_SYMBOL_SELECTION_SCORE),
    }


def _candidate(
    *,
    candidate_id: str,
    symbol: str,
    strategy_family: str,
    expected_edge_bps: Decimal,
    expected_cost_bps: Decimal,
    signal_strength: Decimal,
    regime: str,
    symbol_selection: dict[str, str],
    selection_priority: int,
) -> dict[str, Any]:
    net_ev = expected_edge_bps - expected_cost_bps
    symbol_score = _decimal(symbol_selection.get("symbol_selection_score"))
    candidate_selection_score = _candidate_selection_score_value(
        symbol_score=symbol_score,
        net_ev_bps=net_ev,
        signal_strength=signal_strength,
    )
    threshold_passed = (
        net_ev > MIN_ENTRY_NET_EV_BPS
        and signal_strength >= MIN_ENTRY_SIGNAL_STRENGTH
        and symbol_score >= MIN_SYMBOL_SELECTION_SCORE
        and regime != "RISK_OFF"
    )
    decision = "PAPER_ENTRY_REVIEW" if threshold_passed else "NO_TRADE"
    no_trade_reason = None if decision == "PAPER_ENTRY_REVIEW" else "MIN_EDGE_FAIL"
    if regime == "RISK_OFF":
        decision = "NO_TRADE"
        no_trade_reason = "REGIME_MISMATCH"
    elif symbol_score < MIN_SYMBOL_SELECTION_SCORE:
        no_trade_reason = "SYMBOL_SELECTION_BIAS"
    elif signal_strength < MIN_ENTRY_SIGNAL_STRENGTH:
        no_trade_reason = "STRATEGY_CONFIDENCE_LOW"
    return {
        "candidate_id": candidate_id,
        "symbol": symbol,
        "strategy_family": strategy_family,
        "regime": regime,
        "selection_priority": selection_priority,
        "symbol_selection": symbol_selection,
        "symbol_selection_score": symbol_selection["symbol_selection_score"],
        "candidate_selection_score": _decimal_text(candidate_selection_score),
        "candidate_selection_formula": "0.45*symbol_score+0.35*net_ev_score+0.20*signal_strength",
        "signal_strength": _decimal_text(signal_strength),
        "signal_grade": "A" if signal_strength >= Decimal("0.7") else "B" if signal_strength >= Decimal("0.55") else "C",
        "expected_edge_bps": _decimal_text(expected_edge_bps),
        "expected_cost_bps": _decimal_text(expected_cost_bps),
        "cost_breakdown_bps": {
            "fee_bps": "5",
            "slippage_bps": "5",
            "spread_bps": "1",
            "market_impact_bps": "0",
            "latency_bps": "0",
        },
        "cost_model_source": "PAPER_RUNTIME_STATIC_COST_MODEL",
        "net_ev_after_cost_bps": _decimal_text(net_ev),
        "decision": decision,
        "no_trade_reason": no_trade_reason,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _build_candidates(symbol: str, features: dict[str, Any], *, edge_profile: str) -> list[dict[str, Any]]:
    regime = str(features["regime"])
    cost_bps = Decimal("11")
    symbol_selection = _symbol_selection_score(features)
    symbol_score = _decimal(symbol_selection["symbol_selection_score"])
    momentum = _decimal(features.get("momentum_pct"))
    volume_expansion = _decimal(features.get("volume_expansion_ratio"))
    range_breakout = _decimal(features.get("range_breakout_pct"))
    vwap_distance = abs(_decimal(features.get("vwap_distance_pct")))
    pullback_edge = Decimal("8") + symbol_score * Decimal("36") + _clamp_decimal(momentum / Decimal("3")) * Decimal("8")
    breakout_edge = Decimal("6") + symbol_score * Decimal("28") + _clamp_decimal(volume_expansion / Decimal("2")) * Decimal("8")
    if range_breakout > 0:
        breakout_edge += _clamp_decimal(range_breakout / Decimal("1.5")) * Decimal("6")
    mean_reversion_edge = Decimal("4") + symbol_score * Decimal("18") + _clamp_decimal(vwap_distance / Decimal("1.5")) * Decimal("6")
    if regime == "RISK_OFF":
        pullback_edge -= Decimal("30")
        breakout_edge -= Decimal("25")
        mean_reversion_edge -= Decimal("18")
    edge_shift = Decimal("-45") if edge_profile == "NEGATIVE" else Decimal("-25") if edge_profile == "WEAK" else Decimal("0")
    return [
        _candidate(
            candidate_id=f"{symbol}-pullback-trend-long",
            symbol=symbol,
            strategy_family="PULLBACK_TREND_LONG",
            expected_edge_bps=pullback_edge + edge_shift,
            expected_cost_bps=cost_bps,
            signal_strength=_clamp_decimal(Decimal("0.46") + symbol_score * Decimal("0.38")),
            regime=regime,
            symbol_selection=symbol_selection,
            selection_priority=1,
        ),
        _candidate(
            candidate_id=f"{symbol}-breakout-retest-long",
            symbol=symbol,
            strategy_family="BREAKOUT_RETEST_LONG",
            expected_edge_bps=breakout_edge + edge_shift,
            expected_cost_bps=cost_bps,
            signal_strength=_clamp_decimal(Decimal("0.42") + symbol_score * Decimal("0.32")),
            regime=regime,
            symbol_selection=symbol_selection,
            selection_priority=2,
        ),
        _candidate(
            candidate_id=f"{symbol}-vwap-mean-reversion",
            symbol=symbol,
            strategy_family="VWAP_MEAN_REVERSION",
            expected_edge_bps=mean_reversion_edge + edge_shift,
            expected_cost_bps=cost_bps,
            signal_strength=_clamp_decimal(Decimal("0.38") + symbol_score * Decimal("0.28")),
            regime=regime,
            symbol_selection=symbol_selection,
            selection_priority=3,
        ),
    ]


def _ordered_market_data_universe(
    *,
    session_id: str,
    symbol: str,
    market_data: dict[str, Any] | None,
    market_data_universe: list[dict[str, Any]] | dict[str, dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if isinstance(market_data_universe, dict):
        return [market_data_universe[key] for key in sorted(market_data_universe)]
    if isinstance(market_data_universe, list):
        return list(market_data_universe)
    return [market_data or build_upbit_public_candle_fixture(symbol=symbol, session_id=session_id)]


def _collection_reports_to_market_data(
    source_collection_reports: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str | int]], list[dict[str, str]]]:
    market_data_items: list[dict[str, Any]] = []
    source_by_symbol: dict[str, dict[str, str | int]] = {}
    blockers: list[dict[str, str]] = []
    for source_report in source_collection_reports:
        source_result = validate_upbit_public_market_data_collection_report(source_report)
        source_symbol = str(source_report.get("symbol") or "")
        if source_result.status != "PASS":
            blockers.append(_blocker(source_result.blocker_code or "DATA_UNAVAILABLE", source_result.message))
            continue
        market_data_items.append(source_report["public_market_data"])
        source_by_symbol[source_symbol] = {
            "source_collection_report_hash": source_report["collection_hash"],
            "source_public_market_data_hash": source_report["public_market_data_hash"],
            "canonical_event_count": int(source_report.get("canonical_event_count", 0)),
        }
    return market_data_items, source_by_symbol, blockers


def _build_strategy_regime_cost_linkage(
    *,
    cycle_id: str,
    runtime_input_role: str,
    runtime_public_market_data_hash: str,
    feature_snapshot_hash: str,
    selected_candidate: dict[str, Any],
    regime: str,
) -> dict[str, Any]:
    breakdown = selected_candidate.get("cost_breakdown_bps", {})
    cost_sum = sum(
        (_decimal(breakdown.get(field)) for field in ("fee_bps", "slippage_bps", "spread_bps", "market_impact_bps", "latency_bps")),
        Decimal("0"),
    )
    return {
        "source_runtime_cycle_id": cycle_id,
        "runtime_input_role": runtime_input_role,
        "runtime_public_market_data_hash": runtime_public_market_data_hash,
        "feature_snapshot_hash": feature_snapshot_hash,
        "report_regime": regime,
        "selected_candidate_id": selected_candidate.get("candidate_id"),
        "selected_candidate_regime": selected_candidate.get("regime"),
        "selected_candidate_cost_model_source": selected_candidate.get("cost_model_source"),
        "selected_candidate_expected_cost_bps": selected_candidate.get("expected_cost_bps"),
        "cost_breakdown_sum_bps": _decimal_text(cost_sum),
        "selected_candidate_net_ev_after_cost_bps": selected_candidate.get("net_ev_after_cost_bps"),
        "decision_basis": "NET_EV_AFTER_COST_AND_REGIME",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def upbit_paper_runtime_cycle_hash(report: dict[str, Any]) -> str:
    return _hash_report(report)


def _validate_candidate_costs(candidate: dict[str, Any]) -> UpbitPaperRuntimeCycleValidationResult:
    required = {
        "candidate_id",
        "symbol",
        "strategy_family",
        "regime",
        "selection_priority",
        "symbol_selection",
        "symbol_selection_score",
        "candidate_selection_score",
        "candidate_selection_formula",
        "signal_strength",
        "signal_grade",
        "expected_edge_bps",
        "expected_cost_bps",
        "cost_breakdown_bps",
        "cost_model_source",
        "net_ev_after_cost_bps",
        "decision",
        "no_trade_reason",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    }
    missing = sorted(required - set(candidate))
    if missing:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", f"strategy candidate missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    breakdown = candidate.get("cost_breakdown_bps")
    if not isinstance(breakdown, dict):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate cost breakdown must be an object", "SCHEMA_IDENTITY_MISMATCH")
    cost_fields = {"fee_bps", "slippage_bps", "spread_bps", "market_impact_bps", "latency_bps"}
    missing_costs = sorted(cost_fields - set(breakdown))
    if missing_costs:
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", f"candidate cost breakdown missing: {missing_costs}", "MEASUREMENT_MISSING")
    if candidate.get("cost_model_source") != "PAPER_RUNTIME_STATIC_COST_MODEL":
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "candidate cost model source is not PAPER runtime static cost model", "MEASUREMENT_MISSING")
    expected_edge = _decimal(candidate.get("expected_edge_bps"))
    expected_cost = _decimal(candidate.get("expected_cost_bps"))
    reported_net_ev = _decimal(candidate.get("net_ev_after_cost_bps"))
    signal_strength = _decimal(candidate.get("signal_strength"))
    symbol_score = _decimal(candidate.get("symbol_selection_score", "1"))
    expected_candidate_selection_score = _candidate_selection_score_value(
        symbol_score=symbol_score,
        net_ev_bps=reported_net_ev,
        signal_strength=signal_strength,
    )
    component_cost = sum((_decimal(breakdown[field]) for field in sorted(cost_fields)), Decimal("0"))
    if expected_cost != component_cost:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate expected cost does not equal fee+slippage+spread+impact+latency", "SCHEMA_IDENTITY_MISMATCH")
    if reported_net_ev != expected_edge - expected_cost:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate net EV after cost arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if signal_strength < 0 or signal_strength > 1:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate signal strength must be between 0 and 1", "SCHEMA_IDENTITY_MISMATCH")
    expected_grade = "A" if signal_strength >= Decimal("0.7") else "B" if signal_strength >= Decimal("0.55") else "C"
    if candidate.get("signal_grade") != expected_grade:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate signal grade does not match signal strength", "SCHEMA_IDENTITY_MISMATCH")
    if candidate.get("regime") == "RISK_OFF" and candidate.get("decision") != "NO_TRADE":
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "risk-off candidate cannot be paper entry review", "REGIME_MISMATCH")
    entry_threshold_passed = (
        reported_net_ev > MIN_ENTRY_NET_EV_BPS
        and signal_strength >= MIN_ENTRY_SIGNAL_STRENGTH
        and symbol_score >= MIN_SYMBOL_SELECTION_SCORE
        and candidate.get("regime") != "RISK_OFF"
    )
    no_trade_reason = candidate.get("no_trade_reason")
    if candidate.get("decision") == "PAPER_ENTRY_REVIEW":
        if not entry_threshold_passed:
            return UpbitPaperRuntimeCycleValidationResult(
                "BLOCKED",
                "candidate attempted paper entry review without passing net EV and signal thresholds",
                "MIN_EDGE_FAIL",
            )
        if no_trade_reason is not None:
            return UpbitPaperRuntimeCycleValidationResult(
                "FAIL",
                "paper entry review candidate cannot carry a no-trade reason",
                "SCHEMA_IDENTITY_MISMATCH",
            )
    elif candidate.get("decision") == "NO_TRADE":
        if not isinstance(no_trade_reason, str) or not no_trade_reason:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "no-trade candidate requires a no-trade reason", "SCHEMA_IDENTITY_MISMATCH")
        if candidate.get("regime") == "RISK_OFF":
            expected_reason = "REGIME_MISMATCH"
        elif symbol_score < MIN_SYMBOL_SELECTION_SCORE:
            expected_reason = "SYMBOL_SELECTION_BIAS"
        elif signal_strength < MIN_ENTRY_SIGNAL_STRENGTH:
            expected_reason = "STRATEGY_CONFIDENCE_LOW"
        else:
            expected_reason = "MIN_EDGE_FAIL"
        if no_trade_reason != expected_reason:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate no-trade reason does not match threshold failure", "SCHEMA_IDENTITY_MISMATCH")
        if entry_threshold_passed:
            return UpbitPaperRuntimeCycleValidationResult(
                "BLOCKED",
                "candidate suppressed paper entry review despite passing net EV and signal thresholds",
                "MIN_EDGE_FAIL",
            )
    else:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate decision is unsupported", "SCHEMA_IDENTITY_MISMATCH")
    if _decimal(candidate.get("candidate_selection_score")) != expected_candidate_selection_score:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate selection score formula mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if candidate.get("candidate_selection_formula") != "0.45*symbol_score+0.35*net_ev_score+0.20*signal_strength":
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate selection formula mismatch", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperRuntimeCycleValidationResult("PASS", "candidate cost model is internally consistent", None)


def build_upbit_paper_runtime_cycle_report(
    *,
    cycle_id: str,
    session_id: str = "mvp4_upbit_paper_runtime",
    symbol: str = "KRW-BTC",
    market_data: dict[str, Any] | None = None,
    market_data_universe: list[dict[str, Any]] | dict[str, dict[str, Any]] | None = None,
    source_collection_report: dict[str, Any] | None = None,
    source_collection_reports: list[dict[str, Any]] | None = None,
    edge_profile: str = "POSITIVE",
    starting_cash: str | int | float | Decimal = "1000000",
    paper_cash_available: str | int | float | Decimal | None = None,
    paper_equity: str | int | float | Decimal | None = None,
    paper_position_market_value: str | int | float | Decimal | None = None,
    paper_cash_source: str = "PAPER_LEDGER_ROLLUP",
) -> dict[str, Any]:
    source_collection_report_hash = None
    source_public_market_data_hash = None
    canonical_event_count = 0
    runtime_input_role = "STATIC_FIXTURE"
    blockers: list[dict[str, str]] = []
    supplied_collection_reports: list[dict[str, Any]] = []
    if isinstance(source_collection_report, dict):
        supplied_collection_reports.append(source_collection_report)
    if isinstance(source_collection_reports, list):
        supplied_collection_reports.extend(item for item in source_collection_reports if isinstance(item, dict))
    source_by_symbol: dict[str, dict[str, str | int]] = {}
    if supplied_collection_reports:
        market_data_items, source_by_symbol, collection_blockers = _collection_reports_to_market_data(supplied_collection_reports)
        blockers.extend(collection_blockers)
        runtime_input_role = (
            "PUBLIC_MARKET_DATA_COLLECTION"
            if len(market_data_items) == 1
            else "MULTI_SYMBOL_PUBLIC_MARKET_DATA_COLLECTION"
        )
    else:
        market_data_items = _ordered_market_data_universe(
            session_id=session_id,
            symbol=symbol,
            market_data=market_data,
            market_data_universe=market_data_universe,
        )
        runtime_input_role = "MULTI_SYMBOL_MARKET_DATA_UNIVERSE" if len(market_data_items) > 1 else "STATIC_FIXTURE"

    feature_snapshots_by_symbol: dict[str, dict[str, Any]] = {}
    market_data_by_symbol: dict[str, dict[str, Any]] = {}
    symbol_selection_universe: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for index, candidate_market_data in enumerate(market_data_items, start=1):
        candidate_symbol = str(candidate_market_data.get("symbol") or symbol)
        data_status, data_blocker, data_message = validate_upbit_public_candle_data(
            candidate_market_data,
            symbol=candidate_symbol,
            session_id=session_id,
        )
        if data_status != "PASS" and data_blocker:
            blockers.append(_blocker(data_blocker, data_message))
            continue
        symbol_status, symbol_blocker, symbol_message = validate_upbit_krw_symbol(candidate_symbol, market_type="KRW_SPOT")
        if symbol_status != "PASS" and symbol_blocker:
            blockers.append(_blocker(symbol_blocker, symbol_message))
            continue
        candidate_features = _feature_snapshot(candidate_market_data)
        symbol_selection = _symbol_selection_score(candidate_features)
        feature_snapshots_by_symbol[candidate_symbol] = candidate_features
        market_data_by_symbol[candidate_symbol] = candidate_market_data
        symbol_selection_universe.append(
            {
                "rank_input_order": index,
                "symbol": candidate_symbol,
                "regime": candidate_features["regime"],
                **symbol_selection,
                "eligible_for_entry_candidate": _decimal(symbol_selection["symbol_selection_score"]) >= MIN_SYMBOL_SELECTION_SCORE
                and candidate_features["regime"] != "RISK_OFF",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
        candidates.extend(_build_candidates(candidate_symbol, candidate_features, edge_profile=edge_profile))
    if not candidates:
        fallback_market_data = market_data or build_upbit_public_candle_fixture(symbol=symbol, session_id=session_id)
        market_data_by_symbol[symbol] = fallback_market_data
        feature_snapshots_by_symbol[symbol] = {
            "source": fallback_market_data.get("source", "UNAVAILABLE"),
            "symbol": symbol,
            "regime": "RISK_OFF",
            "last_price": "0",
            "previous_high": "0",
            "vwap": "0",
            "ema_fast": "0",
            "ema_slow": "0",
            "volatility_pct": "0",
            "momentum_pct": "0",
            "total_quote_volume": "0",
            "volume_expansion_ratio": "0",
            "vwap_distance_pct": "0",
            "range_breakout_pct": "0",
            "spread_bps": "0",
            "liquidity_status": "BLOCKED",
            "volatility_status": "BLOCKED",
        }
        candidates = _build_candidates(symbol, feature_snapshots_by_symbol[symbol], edge_profile="NEGATIVE")
    selected = max(candidates, key=_candidate_rank_key)
    selected_symbol = str(selected["symbol"])
    market_data = market_data_by_symbol[selected_symbol]
    features = feature_snapshots_by_symbol[selected_symbol]
    selected_source = source_by_symbol.get(selected_symbol, {})
    source_collection_report_hash = selected_source.get("source_collection_report_hash")  # type: ignore[assignment]
    source_public_market_data_hash = selected_source.get("source_public_market_data_hash")  # type: ignore[assignment]
    canonical_event_count = int(selected_source.get("canonical_event_count", 0)) if selected_source else 0
    no_trade_reasons: list[str] = []
    entry_reasons: list[dict[str, str]] = []
    if blockers:
        final_decision = "BLOCKED"
        no_trade_reasons = order_blocker_codes(blockers)
    elif selected["decision"] == "PAPER_ENTRY_REVIEW":
        final_decision = "ENTER_LONG"
        entry_reasons = [
            {"reason_code": "PAPER_RUNTIME_ENTRY", "message": "PAPER-only runtime candidate passed net EV after cost"},
            {"reason_code": "REGIME_FILTER_PASS", "message": f"regime={features['regime']} allows long paper review"},
            {"reason_code": "NET_EV_AFTER_COST_PASS", "message": f"net_ev_after_cost_bps={selected['net_ev_after_cost_bps']}"},
        ]
    else:
        final_decision = "NO_TRADE"
        no_trade_reasons = [str(selected.get("no_trade_reason") or "MIN_EDGE_FAIL")]
    runtime_public_market_data_hash = public_market_data_hash(market_data)
    feature_snapshot_hash = _hash_payload(features)
    strategy_regime_cost_linkage = _build_strategy_regime_cost_linkage(
        cycle_id=cycle_id,
        runtime_input_role=runtime_input_role,
        runtime_public_market_data_hash=runtime_public_market_data_hash,
        feature_snapshot_hash=feature_snapshot_hash,
        selected_candidate=selected,
        regime=str(features.get("regime")),
    )

    base_sizing_inputs, sizing_input_blockers, guarded_cash_available = _paper_cash_bound_sizing_inputs(
        paper_cash_available=paper_cash_available,
        paper_equity=paper_equity,
        paper_position_market_value=paper_position_market_value,
        paper_cash_source=paper_cash_source,
    )
    risk_state = _build_runtime_risk_state(
        starting_cash=starting_cash,
        sizing_inputs=base_sizing_inputs,
        data_blocked=bool(blockers or sizing_input_blockers),
    )
    sizing_inputs = _candidate_sizing_inputs(
        base_inputs=base_sizing_inputs,
        selected_candidate=selected,
        features=features,
        risk_state=risk_state,
    )
    blockers.extend(sizing_input_blockers)
    if risk_state.get("new_entry_allowed") is not True:
        for risk_blocker in risk_state.get("blockers", []):
            if isinstance(risk_blocker, dict):
                blockers.append(risk_blocker)
        final_decision = "BLOCKED"
        no_trade_reasons = order_blocker_codes(blockers)
        entry_reasons = []

    exit_plan = _build_runtime_exit_plan(selected_candidate=selected, features=features)

    sizing = build_position_sizing_decision(
        sizing_decision_id=f"{cycle_id}-sizing",
        strategy_unit_id=selected["candidate_id"],
        session_id=session_id,
        inputs=sizing_inputs,
    )
    sizing_result = validate_position_sizing_decision(sizing)
    if sizing_result.status != "PASS" or sizing.get("sizing_status") != "PASS":
        sizing_blocker = sizing.get("primary_blocker_code") or sizing_result.blocker_code or "RISK_VETO"
        sizing_message = sizing_result.message
        if sizing.get("sizing_status") != "PASS":
            sizing_blockers = sizing.get("blockers")
            first_sizing_blocker = sizing_blockers[0] if isinstance(sizing_blockers, list) and sizing_blockers else {}
            sizing_message = first_sizing_blocker.get("message", "position sizing blocked PAPER entry")
        blockers.append(_blocker(str(sizing_blocker), str(sizing_message)))
        final_decision = "BLOCKED"
        no_trade_reasons = order_blocker_codes(blockers)
        entry_reasons = []

    if final_decision == "ENTER_LONG":
        selected_notional = _decimal(sizing["selected_notional"])
        entry_cash_required = selected_notional * (Decimal("1") + PAPER_ENTRY_FEE_RATE)
        if selected_notional < UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL:
            blockers.append(
                _blocker(
                    "RISK_VETO",
                    (
                        "PAPER entry notional is below the 5000 KRW minimum simulation floor "
                        f"(selected_notional={_decimal_text(selected_notional)})"
                    ),
                )
            )
        elif guarded_cash_available is not None and guarded_cash_available - entry_cash_required < Decimal("0"):
            blockers.append(
                _blocker(
                    "RISK_VETO",
                    (
                        "PAPER entry would exceed ledger-backed simulated cash "
                        f"(cash_available={_decimal_text(guarded_cash_available)}, "
                        f"cash_required={_decimal_text(entry_cash_required)})"
                    ),
                )
            )
        if blockers:
            final_decision = "BLOCKED"
            no_trade_reasons = order_blocker_codes(blockers)
            entry_reasons = []

    if blockers and final_decision == "ENTER_LONG":
        final_decision = "BLOCKED"
        no_trade_reasons = order_blocker_codes(blockers)
        entry_reasons = []

    position_management_decision = {
        "source": "PAPER_RUNTIME_POSITION_LIFECYCLE_DECISION",
        "selected_symbol": selected_symbol,
        "selected_candidate_id": selected.get("candidate_id"),
        "risk_state": risk_state.get("risk_state"),
        "decision": (
            "ENTER_LONG_WITH_ATTACHED_EXIT_PLAN"
            if final_decision == "ENTER_LONG"
            else "ENTRY_BLOCKED_NO_POSITION"
            if final_decision == "BLOCKED"
            else "NO_ENTRY_NO_POSITION"
        ),
        "exit_plan_status": "ARMED_PAPER_ONLY_AFTER_FILL" if final_decision == "ENTER_LONG" else "NOT_ACTIVE_NO_POSITION",
        "position_sizing_status": sizing.get("sizing_status"),
        "selected_notional": sizing.get("selected_notional"),
        "hard_stop": exit_plan.get("hard_stop"),
        "tp1": exit_plan.get("tp1"),
        "tp2": exit_plan.get("tp2"),
        "time_stop_candles": exit_plan.get("time_stop_candles"),
        "no_trade_reasons": no_trade_reasons,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "can_submit_order": False,
    }

    fill: dict[str, Any] | None = None
    ledger_events: list[dict[str, Any]] = []
    ledger_head_hash: str | None = None
    if final_decision == "ENTER_LONG":
        notional = _decimal(sizing["selected_notional"])
        mark_price = _decimal(features["last_price"])
        slippage_bps = PAPER_ENTRY_SLIPPAGE_BPS
        fee_rate = PAPER_ENTRY_FEE_RATE
        fill_price = mark_price * (Decimal("1") + (slippage_bps / Decimal("10000")))
        quantity = notional / fill_price
        fee_amount = notional * fee_rate
        client_order_id = hashlib.sha256(f"{cycle_id}:{selected_symbol}:paper-fill".encode("utf-8")).hexdigest()[:24].upper()
        ledger_events = build_upbit_paper_fill_chain(
            session_id=session_id,
            symbol=selected_symbol,
            intent_id=f"{cycle_id}-intent",
            client_order_id=client_order_id,
            side="BUY",
            quantity=_decimal_text(quantity),
            price=_decimal_text(fill_price),
            fee_amount=_decimal_text(fee_amount),
        )
        ledger_head_hash = ledger_events[-1]["event_hash"]
        fill = {
            "fill_source": "PAPER_BROKER_SIMULATION",
            "order_lifecycle_state": "FILLED",
            "client_order_id": client_order_id,
            "symbol": selected_symbol,
            "side": "BUY",
            "notional": _decimal_text(notional),
            "quantity": _decimal_text(quantity),
            "fill_price": _decimal_text(fill_price),
            "mark_price": _decimal_text(mark_price),
            "fee_amount": _decimal_text(fee_amount),
            "fee_asset": "KRW",
            "slippage_bps": _decimal_text(slippage_bps),
        }
        portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id=session_id,
            symbol=selected_symbol,
            side="BUY",
            quantity=quantity,
            fill_price=fill_price,
            mark_price=mark_price,
            fee_amount=fee_amount,
            starting_cash=starting_cash,
            source_runtime_cycle_id=cycle_id,
            source_paper_ledger_head_hash=ledger_head_hash,
        )
    else:
        portfolio = build_initial_paper_portfolio_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id=session_id,
            starting_cash=starting_cash,
            source_runtime_cycle_id=cycle_id,
            source_paper_ledger_head_hash=None,
        )

    summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        startup_probe={"startup_probe_passed": True, "primary_blocker_code": None, "next_action": "continue PAPER runtime evidence collection"},
        heartbeat={"heartbeat_status": "PASS", "primary_blocker_code": None, "next_action": "PAPER runtime cycle completed safely"},
        readiness_surface={
            "primary_blocker_code": "LIVE_READY_MISSING",
            "primary_blocker_message": "LIVE remains blocked; PAPER runtime evidence is not live readiness.",
        },
        paper_portfolio_snapshot=portfolio,
        entry_candidates=candidates,
        recent_entry_context=entry_reasons,
        recent_no_trade_context=[{"reason_code": reason, "message": "PAPER runtime did not enter"} for reason in no_trade_reasons],
        market_context={
            "source": "MARKET_DATA",
            "freshness_status": "PASS" if not blockers else "FAIL",
            "selected_symbol": selected_symbol,
            "symbol_universe_count": len(symbol_selection_universe),
            "regime": features.get("regime"),
            "liquidity_status": features.get("liquidity_status"),
            "volatility_status": features.get("volatility_status"),
        },
        quantitative_policy_report=build_quantitative_policy_report(report_id=f"{cycle_id}_quantitative_policy"),
    )
    report = {
        "schema_id": UPBIT_PAPER_RUNTIME_CYCLE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "cycle_id": cycle_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "symbol": selected_symbol,
        "requested_symbol": symbol,
        "symbol_universe": [item["symbol"] for item in symbol_selection_universe],
        "symbol_selection_universe": symbol_selection_universe,
        "selected_symbol": selected_symbol,
        "runtime_input_role": runtime_input_role,
        "source_collection_report_hash": source_collection_report_hash,
        "source_public_market_data_hash": source_public_market_data_hash,
        "source_collection_hashes_by_symbol": source_by_symbol,
        "canonical_event_count": canonical_event_count,
        "runtime_public_market_data_hash": runtime_public_market_data_hash,
        "market_data_source": market_data.get("source", "UNAVAILABLE"),
        "public_market_data": market_data,
        "public_market_data_by_symbol": market_data_by_symbol,
        "feature_snapshot": features,
        "feature_snapshots_by_symbol": feature_snapshots_by_symbol,
        "feature_snapshot_hash": feature_snapshot_hash,
        "regime": features.get("regime"),
        "strategy_candidates": candidates,
        "selected_candidate": selected,
        "strategy_regime_cost_linkage": strategy_regime_cost_linkage,
        "risk_state": risk_state,
        "sizing_decision": sizing,
        "exit_plan": exit_plan,
        "position_management_decision": position_management_decision,
        "paper_fill": fill,
        "paper_ledger_events": ledger_events,
        "paper_ledger_head_hash": ledger_head_hash,
        "paper_portfolio_snapshot": portfolio,
        "summary": summary,
        "final_decision": final_decision,
        "no_trade_reasons": no_trade_reasons,
        "entry_reasons": entry_reasons,
        "paper_order_adapter": "SIMULATED_PAPER_BROKER_ONLY",
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "scale_up_allowed": False,
        "primary_blocker_code": select_primary_blocker(blockers),
        "blockers": blockers,
        "cycle_hash": "",
    }
    report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)
    return report


def validate_upbit_paper_runtime_cycle_report(
    report: dict[str, Any],
    *,
    require_quantitative_policy_summary: bool = True,
    require_current_sizing_caps: bool = True,
) -> UpbitPaperRuntimeCycleValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "cycle_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "runtime_input_role",
        "source_collection_report_hash",
        "source_public_market_data_hash",
        "canonical_event_count",
        "runtime_public_market_data_hash",
        "market_data_source",
        "public_market_data",
        "feature_snapshot",
        "feature_snapshot_hash",
        "regime",
        "strategy_candidates",
        "selected_candidate",
        "strategy_regime_cost_linkage",
        "risk_state",
        "sizing_decision",
        "exit_plan",
        "position_management_decision",
        "paper_fill",
        "paper_ledger_events",
        "paper_ledger_head_hash",
        "paper_portfolio_snapshot",
        "summary",
        "final_decision",
        "no_trade_reasons",
        "entry_reasons",
        "paper_order_adapter",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
        "primary_blocker_code",
        "blockers",
        "cycle_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", f"paper runtime cycle missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_RUNTIME_CYCLE_SCHEMA_ID:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper runtime cycle schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("cycle_hash") != upbit_paper_runtime_cycle_hash(report):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper runtime cycle hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper runtime cycle scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if (
        report.get("live_key_loaded")
        or report.get("live_order_ready")
        or report.get("live_order_allowed")
        or report.get("can_live_trade")
        or report.get("can_submit_order")
        or report.get("scale_up_allowed")
        or report.get("order_adapter_called")
    ):
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper runtime cycle attempted forbidden live/order permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("paper_order_adapter") != "SIMULATED_PAPER_BROKER_ONLY":
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper runtime cycle cannot use an exchange order adapter", "LIVE_FINAL_GUARD_FAILED")
    if report.get("runtime_input_role") not in {
        "STATIC_FIXTURE",
        "PUBLIC_MARKET_DATA_COLLECTION",
        "MULTI_SYMBOL_MARKET_DATA_UNIVERSE",
        "MULTI_SYMBOL_PUBLIC_MARKET_DATA_COLLECTION",
    }:
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper runtime cycle input role is unsafe", "LIVE_FINAL_GUARD_FAILED")
    if report.get("runtime_input_role") in {"PUBLIC_MARKET_DATA_COLLECTION", "MULTI_SYMBOL_PUBLIC_MARKET_DATA_COLLECTION"}:
        if not isinstance(report.get("source_collection_report_hash"), str) or len(report["source_collection_report_hash"]) != 64:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "public collection input requires source collection hash", "SCHEMA_IDENTITY_MISMATCH")
        if not isinstance(report.get("source_public_market_data_hash"), str) or len(report["source_public_market_data_hash"]) != 64:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "public collection input requires source market data hash", "SCHEMA_IDENTITY_MISMATCH")
        if public_market_data_hash(report["public_market_data"]) != report["source_public_market_data_hash"]:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "runtime public market data does not match source collection payload", "SCHEMA_IDENTITY_MISMATCH")
        if not isinstance(report.get("canonical_event_count"), int) or report["canonical_event_count"] < 5:
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "public collection input requires canonical events", "MEASUREMENT_MISSING")
    elif report.get("runtime_input_role") == "STATIC_FIXTURE":
        if (
            report.get("source_collection_report_hash") is not None
            or report.get("source_public_market_data_hash") is not None
            or report.get("canonical_event_count") != 0
        ):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "static fixture runtime cannot carry collection hash", "SCHEMA_IDENTITY_MISMATCH")

    data_status, data_blocker, data_message = validate_upbit_public_candle_data(
        report["public_market_data"],
        symbol=report["symbol"],
        session_id=report["session_id"],
    )
    if data_status != "PASS":
        return UpbitPaperRuntimeCycleValidationResult(data_status, data_message, data_blocker)
    expected_market_data_hash = public_market_data_hash(report["public_market_data"])
    if report.get("runtime_public_market_data_hash") != expected_market_data_hash:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "runtime public market data hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("runtime_input_role") == "PUBLIC_MARKET_DATA_COLLECTION" and report.get("source_public_market_data_hash") != expected_market_data_hash:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "runtime source market data hash does not match payload hash", "SCHEMA_IDENTITY_MISMATCH")
    expected_features = _feature_snapshot(report["public_market_data"])
    if report.get("feature_snapshot") != expected_features:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "feature snapshot does not match public market data", "SCHEMA_IDENTITY_MISMATCH")
    expected_feature_hash = _hash_payload(expected_features)
    if report.get("feature_snapshot_hash") != expected_feature_hash:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "feature snapshot hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("regime") != expected_features.get("regime"):
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "runtime regime does not match computed feature regime", "REGIME_MISMATCH")
    feature_snapshots_by_symbol = report.get("feature_snapshots_by_symbol")
    public_market_data_by_symbol = report.get("public_market_data_by_symbol")
    if isinstance(feature_snapshots_by_symbol, dict) or isinstance(public_market_data_by_symbol, dict):
        if not isinstance(feature_snapshots_by_symbol, dict) or not isinstance(public_market_data_by_symbol, dict):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "multi-symbol runtime requires both market data and feature maps", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("selected_symbol") != report.get("symbol"):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "selected symbol must match runtime report symbol", "SCHEMA_IDENTITY_MISMATCH")
        symbol_universe = report.get("symbol_universe")
        if not isinstance(symbol_universe, list) or report.get("symbol") not in symbol_universe:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "selected symbol missing from symbol universe", "SCHEMA_IDENTITY_MISMATCH")
        for universe_symbol in symbol_universe:
            if not isinstance(universe_symbol, str) or universe_symbol not in public_market_data_by_symbol:
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol universe missing public market data", "SCHEMA_IDENTITY_MISMATCH")
            universe_data = public_market_data_by_symbol[universe_symbol]
            data_status, data_blocker, data_message = validate_upbit_public_candle_data(
                universe_data,
                symbol=universe_symbol,
                session_id=report["session_id"],
            )
            if data_status != "PASS":
                return UpbitPaperRuntimeCycleValidationResult(data_status, data_message, data_blocker)
            if feature_snapshots_by_symbol.get(universe_symbol) != _feature_snapshot(universe_data):
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "multi-symbol feature snapshot mismatch", "SCHEMA_IDENTITY_MISMATCH")
    sizing_result = validate_position_sizing_decision(
        report["sizing_decision"],
        require_exposure_cap=require_current_sizing_caps,
    )
    if sizing_result.status != "PASS":
        return UpbitPaperRuntimeCycleValidationResult(sizing_result.status, sizing_result.message, sizing_result.blocker_code)
    portfolio_result = validate_paper_portfolio_snapshot(report["paper_portfolio_snapshot"])
    if portfolio_result.status != "PASS":
        return UpbitPaperRuntimeCycleValidationResult(portfolio_result.status, portfolio_result.message, portfolio_result.blocker_code)
    if report["paper_portfolio_snapshot"].get("source_runtime_cycle_id") != report["cycle_id"]:
        return UpbitPaperRuntimeCycleValidationResult(
            "FAIL",
            "paper portfolio snapshot source runtime cycle id mismatch",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report["paper_portfolio_snapshot"].get("source_paper_ledger_head_hash") != report.get("paper_ledger_head_hash"):
        return UpbitPaperRuntimeCycleValidationResult(
            "FAIL",
            "paper portfolio snapshot source ledger head hash mismatch",
            "LEDGER_INTEGRITY_FAIL",
        )
    summary_result = validate_summary_shell(
        report["summary"],
        require_quantitative_policy_summary=require_quantitative_policy_summary,
    )
    if summary_result.status != "PASS":
        return UpbitPaperRuntimeCycleValidationResult(summary_result.status, summary_result.message, summary_result.blocker_code)

    final_decision = report.get("final_decision")
    if final_decision not in SAFE_FINAL_DECISIONS:
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "unknown paper runtime final decision", "LIVE_FINAL_GUARD_FAILED")
    selected = report.get("selected_candidate")
    if not isinstance(selected, dict):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "selected candidate must be an object", "SCHEMA_IDENTITY_MISMATCH")
    candidates = report.get("strategy_candidates")
    if not isinstance(candidates, list) or not candidates:
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper runtime requires strategy candidates", "MEASUREMENT_MISSING")
    candidates_by_id: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy candidate must be an object", "SCHEMA_IDENTITY_MISMATCH")
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy candidate missing candidate_id", "SCHEMA_IDENTITY_MISMATCH")
        if candidate_id in candidates_by_id:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "duplicate strategy candidate id", "SCHEMA_IDENTITY_MISMATCH")
        cost_result = _validate_candidate_costs(candidate)
        if cost_result.status != "PASS":
            return cost_result
        candidate_symbol = candidate.get("symbol")
        if not isinstance(candidate_symbol, str) or not candidate_symbol:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy candidate symbol is invalid", "SCHEMA_IDENTITY_MISMATCH")
        candidate_features = expected_features
        if isinstance(feature_snapshots_by_symbol, dict):
            if candidate_symbol not in feature_snapshots_by_symbol:
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy candidate symbol missing feature snapshot", "SCHEMA_IDENTITY_MISMATCH")
            candidate_features = feature_snapshots_by_symbol[candidate_symbol]
        elif candidate_symbol != report.get("symbol"):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy candidate symbol does not match runtime symbol", "SCHEMA_IDENTITY_MISMATCH")
        if candidate.get("regime") != candidate_features.get("regime"):
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "strategy candidate regime does not match runtime regime", "REGIME_MISMATCH")
        if _decimal(candidate.get("cost_breakdown_bps", {}).get("spread_bps")) != _decimal(candidate_features.get("spread_bps")):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy candidate spread cost is not bound to feature spread", "SCHEMA_IDENTITY_MISMATCH")
        candidates_by_id[candidate_id] = candidate
    selected_id = selected.get("candidate_id")
    if selected_id not in candidates_by_id:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "selected candidate is not present in strategy candidates", "SCHEMA_IDENTITY_MISMATCH")
    if selected != candidates_by_id[selected_id]:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "selected candidate diverges from candidate list", "SCHEMA_IDENTITY_MISMATCH")
    expected_top_candidate = max(candidates_by_id.values(), key=_candidate_rank_key)
    net_ev = _decimal(selected.get("net_ev_after_cost_bps"))
    if selected_id != expected_top_candidate.get("candidate_id"):
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "selected candidate is not the highest scored candidate", "MIN_EDGE_FAIL")
    if report["sizing_decision"].get("strategy_unit_id") != selected_id:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "sizing decision strategy unit does not match selected candidate", "SCHEMA_IDENTITY_MISMATCH")
    expected_linkage = _build_strategy_regime_cost_linkage(
        cycle_id=report["cycle_id"],
        runtime_input_role=report["runtime_input_role"],
        runtime_public_market_data_hash=expected_market_data_hash,
        feature_snapshot_hash=expected_feature_hash,
        selected_candidate=selected,
        regime=str(report["regime"]),
    )
    if report.get("strategy_regime_cost_linkage") != expected_linkage:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy/regime/cost linkage does not match runtime evidence", "SCHEMA_IDENTITY_MISMATCH")
    risk_state = report.get("risk_state")
    if not isinstance(risk_state, dict):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "risk_state must be an object", "SCHEMA_IDENTITY_MISMATCH")
    for field in ("risk_state", "drawdown_pct", "new_entry_allowed", "blockers"):
        if field not in risk_state:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", f"risk_state missing {field}", "SCHEMA_IDENTITY_MISMATCH")
    if risk_state.get("live_order_ready") or risk_state.get("live_order_allowed") or risk_state.get("can_live_trade") or risk_state.get("scale_up_allowed"):
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "risk_state attempted live or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if risk_state.get("risk_state") in {"kill_switch", "no_trade", "cooling"} and final_decision == "ENTER_LONG":
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper entry attempted while risk state blocks new entries", "RISK_VETO")
    exit_plan = report.get("exit_plan")
    if not isinstance(exit_plan, dict):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "exit_plan must be an object", "SCHEMA_IDENTITY_MISMATCH")
    for field in ("entry_price", "hard_stop", "tp1", "tp2", "trailing_start", "trailing_distance", "time_stop_candles", "partial_take_profit_ratio"):
        if field not in exit_plan:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", f"exit_plan missing {field}", "SCHEMA_IDENTITY_MISMATCH")
    entry_price = _decimal(exit_plan.get("entry_price"))
    hard_stop = _decimal(exit_plan.get("hard_stop"))
    tp1 = _decimal(exit_plan.get("tp1"))
    tp2 = _decimal(exit_plan.get("tp2"))
    trailing_start = _decimal(exit_plan.get("trailing_start"))
    trailing_distance = _decimal(exit_plan.get("trailing_distance"))
    partial_take_profit_ratio = _decimal(exit_plan.get("partial_take_profit_ratio"))
    if not (hard_stop < entry_price < tp1 < tp2 and trailing_start > entry_price and trailing_distance > 0):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "LONG exit plan price ladder is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if partial_take_profit_ratio < Decimal("0.30") or partial_take_profit_ratio > Decimal("0.50"):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "exit partial take-profit ratio outside closed range", "SCHEMA_IDENTITY_MISMATCH")
    try:
        time_stop_candles = int(exit_plan.get("time_stop_candles"))
    except (TypeError, ValueError):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "exit time stop must be an integer", "SCHEMA_IDENTITY_MISMATCH")
    if time_stop_candles < 3 or time_stop_candles > 12:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "exit time stop outside closed range", "SCHEMA_IDENTITY_MISMATCH")
    if exit_plan.get("live_order_ready") or exit_plan.get("live_order_allowed") or exit_plan.get("can_live_trade") or exit_plan.get("scale_up_allowed"):
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "exit plan attempted live or scale permission", "LIVE_FINAL_GUARD_FAILED")
    lifecycle = report.get("position_management_decision")
    if not isinstance(lifecycle, dict):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "position_management_decision must be an object", "SCHEMA_IDENTITY_MISMATCH")
    expected_lifecycle_decision = (
        "ENTER_LONG_WITH_ATTACHED_EXIT_PLAN"
        if final_decision == "ENTER_LONG"
        else "ENTRY_BLOCKED_NO_POSITION"
        if final_decision == "BLOCKED"
        else "NO_ENTRY_NO_POSITION"
    )
    if lifecycle.get("decision") != expected_lifecycle_decision:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "position lifecycle decision does not match final decision", "SCHEMA_IDENTITY_MISMATCH")
    if lifecycle.get("live_order_ready") or lifecycle.get("live_order_allowed") or lifecycle.get("can_live_trade") or lifecycle.get("scale_up_allowed") or lifecycle.get("can_submit_order"):
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "position lifecycle attempted live/order permission", "LIVE_FINAL_GUARD_FAILED")
    if final_decision == "ENTER_LONG":
        if selected.get("decision") != "PAPER_ENTRY_REVIEW":
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper entry requires selected candidate entry review decision", "MIN_EDGE_FAIL")
        if net_ev <= 0:
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "positive paper entry requires positive net EV after cost", "MIN_EDGE_FAIL")
        if not report.get("paper_fill") or not report.get("paper_ledger_events"):
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper entry requires simulated fill and ledger events", "LEDGER_UNAVAILABLE")
        ledger_status, ledger_blocker, ledger_message = validate_upbit_paper_ledger(report["paper_ledger_events"])
        if ledger_status != "PASS":
            return UpbitPaperRuntimeCycleValidationResult(ledger_status, ledger_message, ledger_blocker)
        if report.get("paper_ledger_head_hash") != report["paper_ledger_events"][-1]["event_hash"]:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper runtime ledger head hash mismatch", "LEDGER_INTEGRITY_FAIL")
        if report["paper_fill"].get("order_lifecycle_state") != "FILLED":
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper entry requires FILLED lifecycle state", "RECONCILIATION_REQUIRED")
        if report["paper_portfolio_snapshot"].get("open_position_count") < 1:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper fill did not update open positions", "SCHEMA_IDENTITY_MISMATCH")
    else:
        if report.get("paper_fill") is not None or report.get("paper_ledger_events"):
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "no-trade paper cycle cannot write fill ledger events", "LIVE_FINAL_GUARD_FAILED")
        if not report.get("no_trade_reasons"):
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "no-trade paper cycle requires a no-trade reason", "MEASUREMENT_MISSING")
        selected_no_trade_reason = selected.get("no_trade_reason")
        if not report.get("blockers") and selected_no_trade_reason and selected_no_trade_reason not in report.get("no_trade_reasons", []):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "no-trade reasons do not match selected candidate", "SCHEMA_IDENTITY_MISMATCH")
    for candidate in candidates:
        if candidate.get("live_order_ready") or candidate.get("live_order_allowed") or candidate.get("can_live_trade") or candidate.get("scale_up_allowed"):
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "strategy candidate attempted live permission", "LIVE_FINAL_GUARD_FAILED")
    return UpbitPaperRuntimeCycleValidationResult("PASS", "Upbit PAPER runtime cycle is simulated, scoped, ledger-backed, and live-blocked", None)
