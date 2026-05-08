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
    build_paper_portfolio_snapshot_after_sell_fill,
    build_paper_portfolio_snapshot_from_fill,
    paper_portfolio_hash,
    validate_paper_portfolio_snapshot,
)
from trader1.runtime.paper.upbit_public_collector import (
    public_market_data_hash,
    validate_upbit_public_market_data_collection_report,
)


UPBIT_PAPER_RUNTIME_CYCLE_SCHEMA_ID = "trader1.upbit_paper_runtime_cycle_report.v1"
SAFE_FINAL_DECISIONS = {"ENTER_LONG", "EXIT_POSITION", "REDUCE_POSITION", "HOLD_POSITION", "NO_TRADE", "BLOCKED", "SAFE_MODE", "RECONCILE_REQUIRED"}
PAPER_ENTRY_FEE_RATE = Decimal("0.0005")
PAPER_ENTRY_SLIPPAGE_BPS = Decimal("5")
PAPER_EXIT_FEE_RATE = Decimal("0.0005")
PAPER_EXIT_SLIPPAGE_BPS = Decimal("5")
PAPER_BROKER_MODEL_ID = "UPBIT_KRW_SPOT_ADAPTIVE_PUBLIC_L2_PROXY_V1"
PAPER_BROKER_FILL_SOURCE = "PAPER_BROKER_SIMULATION_ADAPTIVE_PUBLIC_L2_PROXY"
PAPER_RUNTIME_COST_MODEL_SOURCE = "PAPER_RUNTIME_ADAPTIVE_PUBLIC_L2_PROXY_COST_MODEL"
PAPER_BROKER_MIN_FILL_RATIO = Decimal("0.35")
PAPER_BROKER_MAX_IMPACT_BPS = Decimal("120")
PAPER_BROKER_MAX_LATENCY_BPS = Decimal("45")
UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL = Decimal("5000")
MIN_SYMBOL_SELECTION_SCORE = Decimal("0.60")
MIN_ENTRY_NET_EV_BPS = Decimal("5")
MIN_ENTRY_SIGNAL_STRENGTH = Decimal("0.55")
SYMBOL_CORRELATION_CLUSTER_THRESHOLD = Decimal("0.92")
SYMBOL_CORRELATION_CLUSTER_PENALTY = Decimal("0.18")
SYMBOL_ADAPTIVE_TOP_N_MIN = 2
SYMBOL_ADAPTIVE_TOP_N_MAX = 5
PAPER_SCOPE_CONTINUITY_POLICY_ID = "PAPER_SCOPE_CONTINUITY_V1"
PAPER_SCOPE_CONTINUITY_MAX_SCORE_GAP = Decimal("0.1000")
PAPER_SCOPE_CONTINUITY_MAX_NET_EV_GAP_BPS = Decimal("12")
MIN_EXIT_ATR_RATE = Decimal("0.003")
TREND_CONFIRMATION_MIN_VOLUME_EXPANSION = Decimal("1.05")
TREND_CONFIRMATION_MIN_MOMENTUM_PCT = Decimal("1.50")
TREND_PULLBACK_ALIGNMENT_MIN_SCORE = Decimal("0.70")
TREND_PULLBACK_ALIGNMENT_MIN_VWAP_DISTANCE_PCT = Decimal("-0.25")
TREND_PULLBACK_ALIGNMENT_EDGE_PENALTY_BPS = Decimal("35")
TREND_PULLBACK_ALIGNMENT_SIGNAL_PENALTY = Decimal("0.38")
TREND_PULLBACK_ALIGNMENT_FEATURE_PROJECTION_FIELDS = frozenset(
    {
        "trend_pullback_alignment_status",
        "trend_pullback_alignment_score",
        "trend_pullback_alignment_reason",
        "trend_pullback_alignment_formula",
    }
)
TREND_EXHAUSTION_MIN_VOLATILITY_PCT = Decimal("3.00")
TREND_EXHAUSTION_MIN_MOMENTUM_PCT = Decimal("3.00")
TREND_EXHAUSTION_MIN_VOLUME_EXPANSION = Decimal("1.50")
TREND_EXHAUSTION_EDGE_PENALTY_BPS = Decimal("42")
TREND_EXHAUSTION_SIGNAL_PENALTY = Decimal("0.30")
TREND_EXHAUSTION_FEATURE_PROJECTION_FIELDS = frozenset(
    {"trend_exhaustion_status", "trend_exhaustion_score", "trend_exhaustion_formula"}
)
REGIME_DETAIL_FEATURE_PROJECTION_FIELDS = frozenset(
    {"market_state", "quiet_range_status", "volatility_expansion_status", "regime_detail_formula"}
)
CORRELATION_FEATURE_PROJECTION_FIELDS = frozenset({"return_signature", "return_signature_formula"})
CURRENT_FEATURE_PROJECTION_UPGRADE_FIELDS = (
    TREND_EXHAUSTION_FEATURE_PROJECTION_FIELDS
    | TREND_PULLBACK_ALIGNMENT_FEATURE_PROJECTION_FIELDS
    | REGIME_DETAIL_FEATURE_PROJECTION_FIELDS
    | CORRELATION_FEATURE_PROJECTION_FIELDS
)
BREAKOUT_CONFIRMATION_MIN_VOLUME_EXPANSION = Decimal("1.20")
BREAKOUT_CONFIRMATION_MIN_RANGE_BREAKOUT_PCT = Decimal("0.03")
MEAN_REVERSION_MIN_VWAP_DISTANCE_PCT = Decimal("0.35")
MEAN_REVERSION_MAX_VOLUME_EXPANSION = Decimal("1.35")
WEAK_TREND_EDGE_PENALTY_BPS = Decimal("24")
FALSE_BREAKOUT_EDGE_PENALTY_BPS = Decimal("22")
FAILED_MEAN_REVERSION_EDGE_PENALTY_BPS = Decimal("18")
VOLATILITY_LIQUIDITY_EDGE_PENALTY_BPS = Decimal("8")
ROTATION_EXIT_MIN_NET_EV_ADVANTAGE_BPS = Decimal("8")
ROTATION_EXIT_MIN_SYMBOL_SCORE_BUFFER = Decimal("0.05")
ROTATION_EXIT_MAX_POSITIVE_RETURN_PCT = Decimal("0.25")
ROTATION_EXIT_WEAK_NO_TRADE_REASONS = {
    "REGIME_MISMATCH",
    "SYMBOL_SELECTION_BIAS",
    "STRATEGY_CONFIDENCE_LOW",
    "CLUSTER_RISK",
    "UNIVERSE_FILTERED",
}
ROTATION_SUPERSEDED_BY_HIGHER_PRIORITY_EXIT_REASONS = {
    "HARD_STOP",
    "REGIME_REVERSAL",
    "TREND_INVALIDATED",
    "VWAP_REVERSION_COMPLETE",
    "RANGE_BREAK_INVALIDATED",
    "VWAP_FIXED_TP",
    "BREAKOUT_LEVEL_LOST",
    "FALSE_BREAKOUT_INVALIDATED",
    "VOLATILITY_INVALIDATED",
    "TRAILING_STOP",
    "TAKE_PROFIT_2",
    "TAKE_PROFIT_1_MIN_NOTIONAL_FULL_EXIT",
    "COOLDOWN",
}
QUALITY_FEEDBACK_EXIT_FORMULA = (
    "PRELIMINARY_ROBUSTNESS_FAIL with active cooldown and return_pct<=0.25 triggers "
    "PAPER-only full exit using no_trade_reason=COOLDOWN; hard stop, regime, trailing, and TP2 exits keep priority; "
    "TP1 partial exits wait behind quality and rotation full-exit decisions"
)
RECENT_FAILURE_COOLDOWN_CYCLES = 3
RECENT_FAILURE_SYMBOL_EDGE_PENALTY_BPS = Decimal("32")
RECENT_FAILURE_STRATEGY_EDGE_PENALTY_BPS = Decimal("18")
RECENT_FAILURE_REGIME_REVERSAL_EDGE_PENALTY_BPS = Decimal("12")
RECENT_FAILURE_SYMBOL_SIGNAL_PENALTY = Decimal("0.18")
RECENT_FAILURE_STRATEGY_SIGNAL_PENALTY = Decimal("0.12")
RECENT_FAILURE_MAX_EDGE_PENALTY_BPS = Decimal("80")
RECENT_FAILURE_MAX_SIGNAL_PENALTY = Decimal("0.50")
RUNTIME_QUALITY_FEEDBACK_SYMBOL_EDGE_PENALTY_BPS = Decimal("18")
RUNTIME_QUALITY_FEEDBACK_CANDIDATE_EDGE_PENALTY_BPS = Decimal("55")
RUNTIME_QUALITY_FEEDBACK_SYMBOL_SIGNAL_PENALTY = Decimal("0.08")
RUNTIME_QUALITY_FEEDBACK_CANDIDATE_SIGNAL_PENALTY = Decimal("0.28")
RECENT_FAILURE_COOLDOWN_EXIT_REASONS = {
    "REGIME_REVERSAL",
    "HARD_STOP",
    "TRAILING_STOP",
    "REGIME_ROTATION_EXIT",
    "ROTATION_OPPORTUNITY_COST",
}
RECENT_FAILURE_FEEDBACK_FORMULA = (
    "active when recent PAPER closed loss has same symbol and cooldown_cycles_remaining>0; "
    "or when preliminary PAPER robustness/OOS feedback marks the same symbol/candidate as unfavorable; "
    "closed_loss_edge_penalty=min(80,32bps_symbol+18bps_same_strategy+12bps_regime_reversal); "
    "quality_edge_penalty=min(80,18bps_symbol+55bps_same_candidate_or_strategy); "
    "closed_loss_signal_penalty=min(0.50,0.18_symbol+0.12_same_strategy); "
    "quality_signal_penalty=min(0.50,0.08_symbol+0.28_same_candidate_or_strategy); "
    "active cooldown blocks PAPER_ENTRY_REVIEW"
)
STRATEGY_EXIT_POLICY_ID = "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1"
TREND_PULLBACK_EXIT_VARIATION = "trailing_tp"
VWAP_REVERSION_EXIT_VARIATION = "fixed_tp"
BREAKOUT_RETEST_EXIT_VARIATION = "invalidation_exit"
STRATEGY_EXIT_REASON_NONE = "NONE"
STRATEGY_EXIT_ACTION_NONE = "NONE"
STRATEGY_EXIT_ACTION_FULL_EXIT = "FULL_EXIT"
STRATEGY_EXIT_REASON_TREND_INVALIDATED = "TREND_INVALIDATED"
STRATEGY_EXIT_REASON_VWAP_REVERSION_COMPLETE = "VWAP_REVERSION_COMPLETE"
STRATEGY_EXIT_REASON_RANGE_BREAK_INVALIDATED = "RANGE_BREAK_INVALIDATED"
STRATEGY_EXIT_REASON_VWAP_FIXED_TP = "VWAP_FIXED_TP"
STRATEGY_EXIT_REASON_BREAKOUT_LEVEL_LOST = "BREAKOUT_LEVEL_LOST"
STRATEGY_EXIT_REASON_FALSE_BREAKOUT_INVALIDATED = "FALSE_BREAKOUT_INVALIDATED"
STRATEGY_EXIT_REASON_VOLATILITY_INVALIDATED = "VOLATILITY_INVALIDATED"
BREAKOUT_INVALIDATION_BUFFER_ATR = Decimal("0.20")
VWAP_REVERSION_FIXED_TP_ATR_MULTIPLIER = Decimal("0.80")
QUIET_MAX_VOLATILITY_PCT = Decimal("0.35")
QUIET_MAX_VOLUME_EXPANSION_RATIO = Decimal("0.90")
QUIET_RANGE_MIN_VWAP_DISTANCE_PCT = Decimal("0.55")
QUIET_RANGE_MIN_SYMBOL_SELECTION_SCORE = Decimal("0.60")
QUIET_RANGE_EDGE_PENALTY_BPS = Decimal("12")
QUIET_RANGE_SIGNAL_PENALTY = Decimal("0.08")
VOLATILITY_EXPANSION_MIN_VOLATILITY_PCT = Decimal("2.50")
VOLATILITY_EXPANSION_MIN_VOLUME_RATIO = Decimal("1.20")
VOLATILITY_EXPANSION_MIN_RANGE_BREAKOUT_PCT = Decimal("0.03")
PANIC_MOMENTUM_PCT = Decimal("-6.00")
PANIC_VOLATILITY_PCT = Decimal("6.00")
UNCERTAIN_MAX_ABS_MOMENTUM_PCT = Decimal("0.15")
UNCERTAIN_MAX_ABS_VWAP_DISTANCE_PCT = Decimal("0.20")
SPOT_LONG_BLOCKED_MARKET_STATES = frozenset({"RISK_OFF", "DOWNTREND", "PANIC", "DATA_BAD", "UNCERTAIN"})
POSITION_ROTATION_EXIT_FIELDS = frozenset(
    {
        "rotation_candidate_symbol",
        "rotation_candidate_id",
        "rotation_candidate_decision",
        "rotation_candidate_selection_score",
        "rotation_candidate_net_ev_after_cost_bps",
        "rotation_managed_candidate_id",
        "rotation_managed_candidate_decision",
        "rotation_managed_symbol_selection_score",
        "rotation_managed_net_ev_after_cost_bps",
        "rotation_net_ev_advantage_bps",
        "rotation_symbol_score_advantage",
        "rotation_threshold_bps",
        "rotation_score_buffer_threshold",
        "rotation_max_positive_return_pct",
        "rotation_condition_passed",
        "rotation_reason_code",
        "rotation_action",
        "quality_feedback_exit_status",
        "quality_feedback_exit_feedback_kind",
        "quality_feedback_exit_reason_code",
        "quality_feedback_exit_max_positive_return_pct",
        "quality_feedback_exit_condition_passed",
        "quality_feedback_exit_action",
        "quality_feedback_exit_formula",
        "strategy_exit_policy_id",
        "strategy_family",
        "exit_variation",
        "strategy_exit_reason_code",
        "strategy_exit_condition_passed",
        "strategy_exit_action",
        "strategy_exit_formula",
        "strategy_exit_acceptance_condition",
        "vwap_reversion_target",
        "breakout_invalidation_level",
        "trend_invalidation_regime",
    }
)
STRATEGY_EXIT_POLICY_EVALUATION_FIELDS = frozenset(
    {
        "strategy_exit_policy_id",
        "strategy_family",
        "exit_variation",
        "strategy_exit_reason_code",
        "strategy_exit_condition_passed",
        "strategy_exit_action",
        "strategy_exit_formula",
        "strategy_exit_acceptance_condition",
        "vwap_reversion_target",
        "breakout_invalidation_level",
        "trend_invalidation_regime",
    }
)
STRATEGY_EXIT_PLAN_FIELDS = frozenset(
    {
        "strategy_exit_policy_id",
        "strategy_family",
        "exit_variation",
        "strategy_exit_formula",
        "strategy_exit_acceptance_condition",
    }
)


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


def _spot_long_entry_block_reason(*, regime: str, market_state: str) -> str | None:
    normalized_regime = str(regime or "").upper()
    normalized_state = str(market_state or normalized_regime).upper()
    if normalized_state == "DATA_BAD":
        return "DATA_BAD_BLOCK"
    if normalized_state == "PANIC":
        return "PANIC_BLOCK"
    if normalized_state == "DOWNTREND":
        return "DOWNTREND_SPOT_LONG_BLOCK"
    if normalized_state == "UNCERTAIN":
        return "UNCERTAIN_MARKET_BLOCK"
    if normalized_state == "RISK_OFF" or normalized_regime == "RISK_OFF":
        return "RISK_OFF_BLOCK"
    return None


def _strategy_entry_policy_evaluation(
    *,
    strategy_family: str,
    regime: str,
    market_state: str,
    features: dict[str, Any],
    symbol_score: Decimal,
) -> tuple[bool, str]:
    entry_block_reason = _spot_long_entry_block_reason(regime=regime, market_state=market_state)
    if entry_block_reason:
        return False, entry_block_reason
    volume_expansion = _decimal(features.get("volume_expansion_ratio"))
    range_breakout = max(Decimal("0"), _decimal(features.get("range_breakout_pct")))
    vwap_distance = abs(_decimal(features.get("vwap_distance_pct")))
    if market_state == "QUIET_RANGE":
        if strategy_family != "VWAP_MEAN_REVERSION":
            return False, "QUIET_RANGE_NO_TREND_OR_BREAKOUT_ENTRY"
        if (
            regime == "RANGE"
            and vwap_distance >= QUIET_RANGE_MIN_VWAP_DISTANCE_PCT
            and symbol_score >= QUIET_RANGE_MIN_SYMBOL_SELECTION_SCORE
            and volume_expansion <= QUIET_MAX_VOLUME_EXPANSION_RATIO
        ):
            return True, "QUIET_RANGE_LIMITED_VWAP_REVERSION"
        return False, "QUIET_RANGE_REQUIRES_DEEP_VWAP_DISLOCATION"
    if strategy_family == "PULLBACK_TREND_LONG":
        if (
            regime == "UPTREND"
            and features.get("trend_pullback_alignment_status") == "PASS"
            and features.get("trend_exhaustion_status") != "WARN"
        ):
            return True, "PASS"
        return False, "PULLBACK_REQUIRES_VALID_UPTREND_ALIGNMENT"
    if strategy_family == "BREAKOUT_RETEST_LONG":
        if market_state == "VOLATILITY_EXPANSION" or (
            regime == "UPTREND"
            and volume_expansion >= BREAKOUT_CONFIRMATION_MIN_VOLUME_EXPANSION
            and range_breakout >= BREAKOUT_CONFIRMATION_MIN_RANGE_BREAKOUT_PCT
        ):
            return True, "PASS"
        return False, "BREAKOUT_REQUIRES_VOLUME_CONFIRMED_EXPANSION_OR_RETEST"
    if strategy_family == "VWAP_MEAN_REVERSION":
        if regime == "RANGE" and market_state != "VOLATILITY_EXPANSION":
            return True, "PASS"
        return False, "VWAP_REVERSION_RANGE_ONLY"
    return False, "UNKNOWN_STRATEGY_FAMILY"


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


def _cycle_bound_current_portfolio_snapshot(
    snapshot: dict[str, Any] | None,
    *,
    cycle_id: str,
) -> dict[str, Any] | None:
    if not isinstance(snapshot, dict):
        return None
    result = validate_paper_portfolio_snapshot(snapshot)
    if result.status != "PASS":
        return None
    current = dict(snapshot)
    current["positions"] = [dict(item) for item in snapshot.get("positions", []) if isinstance(item, dict)]
    current["source_runtime_cycle_id"] = cycle_id
    current["live_order_ready"] = False
    current["live_order_allowed"] = False
    current["can_live_trade"] = False
    current["scale_up_allowed"] = False
    current["can_submit_order"] = False
    current["snapshot_hash"] = paper_portfolio_hash(current)
    return current


def _open_long_positions(snapshot: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(snapshot, dict):
        return []
    positions = snapshot.get("positions")
    if not isinstance(positions, list):
        return []
    return [
        dict(position)
        for position in positions
        if isinstance(position, dict) and position.get("side") == "LONG" and _decimal(position.get("quantity")) > 0
    ]


def _select_managed_position(
    snapshot: dict[str, Any] | None,
    *,
    feature_snapshots_by_symbol: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    priced_positions = [
        position
        for position in _open_long_positions(snapshot)
        if isinstance(position.get("symbol"), str) and position["symbol"] in feature_snapshots_by_symbol
    ]
    if not priced_positions:
        return None
    return sorted(
        priced_positions,
        key=lambda position: (-_decimal(position.get("market_value")), str(position.get("symbol"))),
    )[0]


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


def _paper_scope_focus_requested(paper_scope_focus: dict[str, Any] | None) -> bool:
    if not isinstance(paper_scope_focus, dict):
        return False
    return bool(
        paper_scope_focus.get("candidate_id")
        and paper_scope_focus.get("symbol")
        and int(paper_scope_focus.get("sample_deficit", 0) or 0) > 0
        and not any(
            paper_scope_focus.get(flag)
            for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
        )
    )


def _candidate_passes_scope_continuity_floor(candidate: dict[str, Any]) -> bool:
    return (
        candidate.get("decision") == "PAPER_ENTRY_REVIEW"
        and not _candidate_recent_failure_cooldown_active(candidate)
        and _decimal(candidate.get("net_ev_after_cost_bps")) > MIN_ENTRY_NET_EV_BPS
        and _decimal(candidate.get("signal_strength")) >= MIN_ENTRY_SIGNAL_STRENGTH
        and _decimal(candidate.get("symbol_selection_score")) >= MIN_SYMBOL_SELECTION_SCORE
        and not any(
            candidate.get(flag)
            for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
        )
    )


def _paper_scope_continuity_decision(
    *,
    candidates: list[dict[str, Any]],
    paper_scope_focus: dict[str, Any] | None,
    managed_position_symbol: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    entry_review_candidates = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict) and candidate.get("decision") == "PAPER_ENTRY_REVIEW"
    ]
    best_candidate = max(entry_review_candidates or candidates, key=_candidate_rank_key)
    requested_candidate_id = (
        str(paper_scope_focus.get("candidate_id") or "") if isinstance(paper_scope_focus, dict) else ""
    )
    requested_symbol = str(paper_scope_focus.get("symbol") or "") if isinstance(paper_scope_focus, dict) else ""
    requested_strategy_id = (
        str(paper_scope_focus.get("strategy_id") or "") if isinstance(paper_scope_focus, dict) else ""
    )
    requested_parameter_hash = (
        str(paper_scope_focus.get("parameter_hash") or "").upper() if isinstance(paper_scope_focus, dict) else ""
    )
    focus_requested = _paper_scope_focus_requested(paper_scope_focus)
    if not focus_requested:
        requested_candidate_id = ""
        requested_symbol = ""
        requested_strategy_id = ""
        requested_parameter_hash = ""
    selected = best_candidate
    status = "NOT_REQUESTED"
    score_gap = Decimal("0")
    net_ev_gap = Decimal("0")
    if focus_requested:
        status = "FOCUS_CANDIDATE_MISSING"
        focused = next(
            (candidate for candidate in candidates if candidate.get("candidate_id") == requested_candidate_id),
            None,
        )
        if managed_position_symbol:
            status = "MANAGED_POSITION_OVERRIDES_SCOPE_FOCUS"
        elif not isinstance(focused, dict):
            status = "FOCUS_CANDIDATE_MISSING"
        elif not _candidate_passes_scope_continuity_floor(focused):
            status = (
                "FOCUS_CANDIDATE_LIVE_FLAG_UNSAFE"
                if any(
                    focused.get(flag)
                    for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
                )
                else "FOCUS_CANDIDATE_NOT_ENTRY_REVIEW"
            )
        else:
            score_gap = max(
                Decimal("0"),
                _decimal(best_candidate.get("candidate_selection_score"))
                - _decimal(focused.get("candidate_selection_score")),
            )
            net_ev_gap = max(
                Decimal("0"),
                _decimal(best_candidate.get("net_ev_after_cost_bps"))
                - _decimal(focused.get("net_ev_after_cost_bps")),
            )
            if score_gap > PAPER_SCOPE_CONTINUITY_MAX_SCORE_GAP:
                status = "SCORE_GAP_TOO_WIDE"
            elif net_ev_gap > PAPER_SCOPE_CONTINUITY_MAX_NET_EV_GAP_BPS:
                status = "NET_EV_GAP_TOO_WIDE"
            else:
                selected = focused
                status = "SELECTED"

    decision = {
        "policy_id": PAPER_SCOPE_CONTINUITY_POLICY_ID,
        "requested": focus_requested,
        "selection_status": status,
        "requested_candidate_id": requested_candidate_id or None,
        "requested_symbol": requested_symbol or None,
        "requested_strategy_id": requested_strategy_id or None,
        "requested_parameter_hash": requested_parameter_hash or None,
        "selected": status == "SELECTED",
        "selected_candidate_id": selected.get("candidate_id"),
        "selected_symbol": selected.get("symbol"),
        "best_candidate_id": best_candidate.get("candidate_id"),
        "best_symbol": best_candidate.get("symbol"),
        "score_gap": _decimal_text(score_gap),
        "net_ev_gap_bps": _decimal_text(net_ev_gap),
        "max_score_gap": _decimal_text(PAPER_SCOPE_CONTINUITY_MAX_SCORE_GAP),
        "max_net_ev_gap_bps": _decimal_text(PAPER_SCOPE_CONTINUITY_MAX_NET_EV_GAP_BPS),
        "acceptance_condition": (
            "Only select the active PAPER scope when the candidate is still PAPER_ENTRY_REVIEW, "
            "live flags are false, net EV/signal/symbol floors pass, and score/net-EV gaps stay within policy bounds."
        ),
        "fallback_behavior": "Fallback to highest scored candidate when focus is absent, unsafe, stale, managed-position overridden, or outside gap limits.",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    return selected, decision


def _recent_failure_clear_feedback() -> dict[str, Any]:
    return {
        "recent_failure_cooldown_status": "CLEAR",
        "recent_failure_feedback_kind": "NONE",
        "recent_failure_cooldown_cycles_remaining": 0,
        "recent_failure_penalty_bps": "0",
        "recent_failure_signal_penalty": "0",
        "recent_failure_reason_code": None,
        "recent_failure_source_cycle_id": None,
        "recent_failure_source_cycle_hash": None,
        "recent_failure_realized_pnl_delta": "0",
        "recent_failure_formula": RECENT_FAILURE_FEEDBACK_FORMULA,
    }


def _candidate_recent_failure_cooldown_active(candidate: dict[str, Any]) -> bool:
    try:
        remaining = int(candidate.get("recent_failure_cooldown_cycles_remaining", 0) or 0)
    except (TypeError, ValueError):
        remaining = 0
    return (
        candidate.get("recent_failure_cooldown_status") == "ACTIVE"
        and remaining > 0
        and _decimal(candidate.get("recent_failure_penalty_bps")) > 0
    )


def _recent_failure_feedback_for_candidate(
    *,
    symbol: str,
    strategy_family: str,
    candidate_id: str,
    recent_failure_feedback: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    if not isinstance(recent_failure_feedback, list):
        return _recent_failure_clear_feedback()
    matched: list[dict[str, Any]] = []
    for feedback in recent_failure_feedback:
        if not isinstance(feedback, dict) or feedback.get("symbol") != symbol:
            continue
        try:
            remaining = int(feedback.get("cooldown_cycles_remaining", 0) or 0)
        except (TypeError, ValueError):
            continue
        if remaining <= 0:
            continue
        kind = str(feedback.get("feedback_kind") or "RECENT_NEGATIVE_EXIT")
        if kind == "PRELIMINARY_ROBUSTNESS_FAIL":
            matched.append(feedback)
            continue
        if _decimal(feedback.get("realized_pnl_delta", feedback.get("realized_pnl", "0"))) >= 0:
            continue
        reason = str(feedback.get("exit_reason_code") or feedback.get("failure_reason_code") or "")
        if reason not in RECENT_FAILURE_COOLDOWN_EXIT_REASONS:
            continue
        matched.append(feedback)
    if not matched:
        return _recent_failure_clear_feedback()

    matched.sort(
        key=lambda item: (
            int(item.get("cooldown_cycles_remaining", 0) or 0),
            abs(_decimal(item.get("realized_pnl_delta", item.get("realized_pnl", "0")))),
            str(item.get("source_runtime_cycle_id") or ""),
        ),
        reverse=True,
    )
    selected = matched[0]
    same_strategy = selected.get("strategy_family") == strategy_family or selected.get("candidate_id") == candidate_id
    reason = str(selected.get("exit_reason_code") or selected.get("failure_reason_code") or "RECENT_PAPER_CLOSED_LOSS")
    if str(selected.get("feedback_kind") or "") == "PRELIMINARY_ROBUSTNESS_FAIL":
        edge_penalty = RUNTIME_QUALITY_FEEDBACK_SYMBOL_EDGE_PENALTY_BPS
        signal_penalty = RUNTIME_QUALITY_FEEDBACK_SYMBOL_SIGNAL_PENALTY
        if same_strategy:
            edge_penalty += RUNTIME_QUALITY_FEEDBACK_CANDIDATE_EDGE_PENALTY_BPS
            signal_penalty += RUNTIME_QUALITY_FEEDBACK_CANDIDATE_SIGNAL_PENALTY
    else:
        edge_penalty = RECENT_FAILURE_SYMBOL_EDGE_PENALTY_BPS
        signal_penalty = RECENT_FAILURE_SYMBOL_SIGNAL_PENALTY
        if same_strategy:
            edge_penalty += RECENT_FAILURE_STRATEGY_EDGE_PENALTY_BPS
            signal_penalty += RECENT_FAILURE_STRATEGY_SIGNAL_PENALTY
        if reason == "REGIME_REVERSAL":
            edge_penalty += RECENT_FAILURE_REGIME_REVERSAL_EDGE_PENALTY_BPS
    edge_penalty = min(edge_penalty, RECENT_FAILURE_MAX_EDGE_PENALTY_BPS)
    signal_penalty = min(signal_penalty, RECENT_FAILURE_MAX_SIGNAL_PENALTY)
    return {
        "recent_failure_cooldown_status": "ACTIVE",
        "recent_failure_feedback_kind": str(selected.get("feedback_kind") or "RECENT_NEGATIVE_EXIT"),
        "recent_failure_cooldown_cycles_remaining": int(selected.get("cooldown_cycles_remaining", 0) or 0),
        "recent_failure_penalty_bps": _decimal_text(edge_penalty),
        "recent_failure_signal_penalty": _decimal_text(signal_penalty),
        "recent_failure_reason_code": reason,
        "recent_failure_source_cycle_id": selected.get("source_runtime_cycle_id"),
        "recent_failure_source_cycle_hash": selected.get("source_runtime_cycle_hash"),
        "recent_failure_realized_pnl_delta": _decimal_text(
            _decimal(selected.get("realized_pnl_delta", selected.get("realized_pnl", "0")))
        ),
        "recent_failure_formula": RECENT_FAILURE_FEEDBACK_FORMULA,
    }


def _best_rotation_alternative_candidate(
    candidates: list[dict[str, Any]],
    *,
    managed_symbol: str | None,
) -> dict[str, Any] | None:
    alternatives = [
        candidate
        for candidate in candidates
        if candidate.get("symbol") != managed_symbol and candidate.get("decision") == "PAPER_ENTRY_REVIEW"
    ]
    if not alternatives:
        return None
    return max(alternatives, key=_candidate_rank_key)


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
    entry_price_override: str | int | float | Decimal | None = None,
) -> dict[str, Any]:
    entry_price = max(_decimal(entry_price_override if entry_price_override is not None else features.get("last_price")), Decimal("0"))
    volatility_rate = max(MIN_EXIT_ATR_RATE, _decimal(features.get("volatility_pct")) / Decimal("100"))
    atr_proxy = max(Decimal("0.0000001"), entry_price * volatility_rate)
    strategy_family = str(selected_candidate.get("strategy_family") or "PULLBACK_TREND_LONG")
    trend_exhaustion_active = features.get("trend_exhaustion_status") == "WARN"
    hard_stop_atr = Decimal("0.9") if trend_exhaustion_active else Decimal("1.2")
    tp1_atr = Decimal("0.9") if trend_exhaustion_active else Decimal("1.2")
    tp2_atr = Decimal("1.8") if trend_exhaustion_active else Decimal("2.5")
    trailing_start_atr = Decimal("0.8") if trend_exhaustion_active else Decimal("1.5")
    trailing_distance_atr = Decimal("0.55") if trend_exhaustion_active else Decimal("1.0")
    partial_take_profit_ratio = Decimal("0.50") if trend_exhaustion_active else Decimal("0.40")
    time_stop_candles = 5 if trend_exhaustion_active else 8
    exit_variation = TREND_PULLBACK_EXIT_VARIATION
    strategy_exit_formula = (
        "TREND_PULLBACK: hard_stop first, then RISK_OFF exit, trend invalidation, "
        "ATR trailing, TP2, quality/rotation, and partial TP1"
    )
    strategy_exit_acceptance_condition = (
        "trend remains UPTREND or exit via hard stop/RISK_OFF/trailing when trend continuation evidence fails"
    )
    vwap = max(_decimal(features.get("vwap")), Decimal("0"))
    previous_high = max(_decimal(features.get("previous_high")), Decimal("0"))
    vwap_reversion_target: str | None = None
    breakout_invalidation_level: str | None = None
    if strategy_family == "VWAP_MEAN_REVERSION" and not trend_exhaustion_active:
        exit_variation = VWAP_REVERSION_EXIT_VARIATION
        hard_stop_atr = Decimal("0.9")
        tp1_atr = VWAP_REVERSION_FIXED_TP_ATR_MULTIPLIER
        tp2_atr = Decimal("1.4")
        trailing_start_atr = Decimal("2.2")
        trailing_distance_atr = Decimal("1.2")
        partial_take_profit_ratio = Decimal("0.50")
        time_stop_candles = 6
        vwap_target = vwap if vwap > entry_price else entry_price + VWAP_REVERSION_FIXED_TP_ATR_MULTIPLIER * atr_proxy
        vwap_reversion_target = _decimal_text(vwap_target)
        strategy_exit_formula = (
            "VWAP_REVERSION: hard_stop first, then RISK_OFF/range-break invalidation, "
            "full exit on VWAP target or fixed TP; no partial hold-through after mean reversion completes"
        )
        strategy_exit_acceptance_condition = (
            "mark_price>=vwap_reversion_target or range breaks against position; otherwise hold only inside RANGE"
        )
    elif strategy_family == "BREAKOUT_RETEST_LONG" and not trend_exhaustion_active:
        exit_variation = BREAKOUT_RETEST_EXIT_VARIATION
        hard_stop_atr = Decimal("1.0")
        tp1_atr = Decimal("1.4")
        tp2_atr = Decimal("3.0")
        trailing_start_atr = Decimal("1.2")
        trailing_distance_atr = Decimal("0.8")
        partial_take_profit_ratio = Decimal("0.35")
        time_stop_candles = 6
        breakout_reference = previous_high if previous_high > 0 else entry_price
        breakout_reference = min(entry_price, breakout_reference)
        breakout_invalidation_level = _decimal_text(breakout_reference - BREAKOUT_INVALIDATION_BUFFER_ATR * atr_proxy)
        strategy_exit_formula = (
            "BREAKOUT_RETEST: hard_stop first, then RISK_OFF, breakout level lost, false breakout invalidation, "
            "volatility exhaustion invalidation, trailing, and staged TP"
        )
        strategy_exit_acceptance_condition = (
            "hold only while breakout reference holds and range_breakout remains non-negative after retest"
        )
    plan = build_exit_plan(
        {
            "entry_price": _decimal_text(entry_price),
            "atr": _decimal_text(atr_proxy),
            "side": "LONG",
            "hard_stop_atr": _decimal_text(hard_stop_atr),
            "tp1_atr": _decimal_text(tp1_atr),
            "tp2_atr": _decimal_text(tp2_atr),
            "trailing_start_atr": _decimal_text(trailing_start_atr),
            "trailing_distance_atr": _decimal_text(trailing_distance_atr),
            "partial_take_profit_ratio": _decimal_text(partial_take_profit_ratio),
            "time_stop_candles": str(time_stop_candles),
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
            "strategy_exit_policy_id": STRATEGY_EXIT_POLICY_ID,
            "strategy_family": strategy_family,
            "exit_variation": exit_variation,
            "strategy_exit_formula": strategy_exit_formula,
            "strategy_exit_acceptance_condition": strategy_exit_acceptance_condition,
            "vwap_reversion_target": vwap_reversion_target,
            "breakout_invalidation_level": breakout_invalidation_level,
            "breakout_invalidation_buffer_atr": _decimal_text(BREAKOUT_INVALIDATION_BUFFER_ATR),
            "strategy_exit_priority": [
                "hard_stop",
                "risk_off_regime_reversal",
                "strategy_invalidation",
                "strategy_profit_target",
                "common_trailing",
                "take_profit_2",
                "quality_feedback",
                "rotation",
                "take_profit_1",
            ],
            "hard_stop_formula": f"entry_price - {_decimal_text(hard_stop_atr)}*atr_proxy",
            "tp1_formula": f"entry_price + {_decimal_text(tp1_atr)}*atr_proxy",
            "tp2_formula": f"entry_price + {_decimal_text(tp2_atr)}*atr_proxy",
            "trailing_formula": (
                f"start_after_{_decimal_text(trailing_start_atr)}*atr_proxy"
                f"_then_distance_{_decimal_text(trailing_distance_atr)}*atr_proxy"
            ),
            "trend_exhaustion_status": features.get("trend_exhaustion_status", "PASS"),
            "trend_exhaustion_score": features.get("trend_exhaustion_score", "0"),
            "trend_exhaustion_exit_adjustment": (
                "TIGHTENED_TRAILING_AND_TIME_STOP" if trend_exhaustion_active else "STANDARD_ATR_EXIT_PLAN"
            ),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    return plan


def _build_entry_strategy_context(
    *,
    cycle_id: str,
    selected_candidate: dict[str, Any],
    exit_plan: dict[str, Any],
) -> dict[str, Any]:
    return {
        "entry_strategy_context_status": "BOUND_TO_ENTRY_CANDIDATE",
        "entry_strategy_context_source": "PAPER_RUNTIME_ENTRY_FILL",
        "entry_candidate_id": str(selected_candidate.get("candidate_id") or ""),
        "entry_strategy_family": str(selected_candidate.get("strategy_family") or ""),
        "entry_strategy_exit_policy_id": STRATEGY_EXIT_POLICY_ID,
        "entry_strategy_exit_variation": str(exit_plan.get("exit_variation") or ""),
        "entry_strategy_source_runtime_cycle_id": cycle_id,
        "entry_strategy_source_candidate_hash": _hash_payload(selected_candidate),
        "entry_strategy_source_exit_plan_hash": _hash_payload(exit_plan),
        "entry_strategy_context_formula": (
            "Bind PAPER position exits to the candidate strategy active at entry fill; "
            "existing-position management uses this persisted context before current candidate fallback."
        ),
    }


def _position_entry_strategy_candidate(
    *,
    position: dict[str, Any] | None,
    candidates: list[dict[str, Any]],
    fallback_candidate: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(position, dict):
        return fallback_candidate, {
            "entry_strategy_context_status": "SELECTED_CANDIDATE_CONTEXT",
            "entry_strategy_context_source": "NO_MANAGED_POSITION",
            "entry_candidate_id": fallback_candidate.get("candidate_id"),
            "entry_strategy_family": fallback_candidate.get("strategy_family"),
            "entry_strategy_exit_variation": None,
            "entry_strategy_current_candidate_match": True,
            "entry_strategy_fallback_used": False,
        }
    entry_candidate_id = position.get("entry_candidate_id")
    entry_strategy_family = position.get("entry_strategy_family")
    if (
        position.get("entry_strategy_context_status") == "BOUND_TO_ENTRY_CANDIDATE"
        and isinstance(entry_candidate_id, str)
        and entry_candidate_id
        and entry_strategy_family in {"PULLBACK_TREND_LONG", "VWAP_MEAN_REVERSION", "BREAKOUT_RETEST_LONG"}
    ):
        matched_candidate = next(
            (
                candidate
                for candidate in candidates
                if candidate.get("candidate_id") == entry_candidate_id
                and candidate.get("symbol") == position.get("symbol")
                and candidate.get("strategy_family") == entry_strategy_family
            ),
            None,
        )
        candidate = matched_candidate or {
            "candidate_id": entry_candidate_id,
            "symbol": position.get("symbol"),
            "strategy_family": entry_strategy_family,
            "decision": "NO_TRADE",
            "no_trade_reason": "ENTRY_STRATEGY_CONTEXT_ONLY",
            "recent_failure_feedback_kind": "NONE",
            "recent_failure_cooldown_status": "CLEAR",
            "recent_failure_cooldown_cycles_remaining": 0,
            "recent_failure_penalty_bps": "0",
            "recent_failure_reason_code": None,
            "symbol_selection_score": "0",
            "net_ev_after_cost_bps": "0",
        }
        return candidate, {
            "entry_strategy_context_status": "BOUND_TO_POSITION_ENTRY",
            "entry_strategy_context_source": position.get("entry_strategy_context_source"),
            "entry_candidate_id": entry_candidate_id,
            "entry_strategy_family": entry_strategy_family,
            "entry_strategy_exit_variation": position.get("entry_strategy_exit_variation"),
            "entry_strategy_current_candidate_match": entry_candidate_id == fallback_candidate.get("candidate_id"),
            "entry_strategy_fallback_used": matched_candidate is None,
        }
    return fallback_candidate, {
        "entry_strategy_context_status": "FALLBACK_TO_CURRENT_SELECTED_CANDIDATE",
        "entry_strategy_context_source": "POSITION_ENTRY_CONTEXT_MISSING",
        "entry_candidate_id": fallback_candidate.get("candidate_id"),
        "entry_strategy_family": fallback_candidate.get("strategy_family"),
        "entry_strategy_exit_variation": None,
        "entry_strategy_current_candidate_match": True,
        "entry_strategy_fallback_used": True,
    }


def _evaluate_existing_position_exit(
    *,
    position: dict[str, Any] | None,
    features: dict[str, Any] | None,
    exit_plan: dict[str, Any],
    managed_candidate: dict[str, Any] | None = None,
    rotation_candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rotation_context: dict[str, Any] = {
        "rotation_candidate_symbol": None,
        "rotation_candidate_id": None,
        "rotation_candidate_decision": None,
        "rotation_candidate_selection_score": "0",
        "rotation_candidate_net_ev_after_cost_bps": "0",
        "rotation_managed_candidate_id": managed_candidate.get("candidate_id") if isinstance(managed_candidate, dict) else None,
        "rotation_managed_candidate_decision": managed_candidate.get("decision") if isinstance(managed_candidate, dict) else None,
        "rotation_managed_symbol_selection_score": (
            managed_candidate.get("symbol_selection_score") if isinstance(managed_candidate, dict) else "0"
        ),
        "rotation_managed_net_ev_after_cost_bps": (
            managed_candidate.get("net_ev_after_cost_bps") if isinstance(managed_candidate, dict) else "0"
        ),
        "rotation_net_ev_advantage_bps": "0",
        "rotation_symbol_score_advantage": "0",
        "rotation_threshold_bps": _decimal_text(ROTATION_EXIT_MIN_NET_EV_ADVANTAGE_BPS),
        "rotation_score_buffer_threshold": _decimal_text(ROTATION_EXIT_MIN_SYMBOL_SCORE_BUFFER),
        "rotation_max_positive_return_pct": _decimal_text(ROTATION_EXIT_MAX_POSITIVE_RETURN_PCT),
        "rotation_condition_passed": False,
        "rotation_reason_code": None,
        "rotation_action": "NONE",
        "quality_feedback_exit_status": "CLEAR",
        "quality_feedback_exit_feedback_kind": "NONE",
        "quality_feedback_exit_reason_code": None,
        "quality_feedback_exit_max_positive_return_pct": _decimal_text(ROTATION_EXIT_MAX_POSITIVE_RETURN_PCT),
        "quality_feedback_exit_condition_passed": False,
        "quality_feedback_exit_action": "NONE",
        "quality_feedback_exit_formula": QUALITY_FEEDBACK_EXIT_FORMULA,
        "strategy_exit_policy_id": exit_plan.get("strategy_exit_policy_id"),
        "strategy_family": exit_plan.get("strategy_family"),
        "exit_variation": exit_plan.get("exit_variation"),
        "strategy_exit_reason_code": STRATEGY_EXIT_REASON_NONE,
        "strategy_exit_condition_passed": False,
        "strategy_exit_action": STRATEGY_EXIT_ACTION_NONE,
        "strategy_exit_formula": exit_plan.get("strategy_exit_formula"),
        "strategy_exit_acceptance_condition": exit_plan.get("strategy_exit_acceptance_condition"),
        "vwap_reversion_target": exit_plan.get("vwap_reversion_target"),
        "breakout_invalidation_level": exit_plan.get("breakout_invalidation_level"),
        "trend_invalidation_regime": None,
    }
    if isinstance(rotation_candidate, dict):
        rotation_context.update(
            {
                "rotation_candidate_symbol": rotation_candidate.get("symbol"),
                "rotation_candidate_id": rotation_candidate.get("candidate_id"),
                "rotation_candidate_decision": rotation_candidate.get("decision"),
                "rotation_candidate_selection_score": rotation_candidate.get("symbol_selection_score", "0"),
                "rotation_candidate_net_ev_after_cost_bps": rotation_candidate.get("net_ev_after_cost_bps", "0"),
            }
        )
        if isinstance(managed_candidate, dict):
            rotation_context["rotation_net_ev_advantage_bps"] = _decimal_text(
                _decimal(rotation_candidate.get("net_ev_after_cost_bps")) - _decimal(managed_candidate.get("net_ev_after_cost_bps"))
            )
            rotation_context["rotation_symbol_score_advantage"] = _decimal_text(
                _decimal(rotation_candidate.get("symbol_selection_score")) - _decimal(managed_candidate.get("symbol_selection_score"))
            )
    if not isinstance(position, dict) or not isinstance(features, dict):
        return {
            "final_decision": None,
            "reason_code": None,
            "message": "no managed PAPER position",
            "sell_quantity": "0",
            "sell_notional": "0",
            **rotation_context,
        }
    mark_price = _decimal(features.get("last_price"))
    quantity = _decimal(position.get("quantity"))
    average_entry = _decimal(position.get("average_entry_price"))
    hard_stop = _decimal(exit_plan.get("hard_stop"))
    tp1 = _decimal(exit_plan.get("tp1"))
    tp2 = _decimal(exit_plan.get("tp2"))
    trailing_start = _decimal(exit_plan.get("trailing_start"))
    trailing_distance = _decimal(exit_plan.get("trailing_distance"))
    previous_high = _decimal(features.get("previous_high"))
    partial_ratio = _decimal(exit_plan.get("partial_take_profit_ratio"))
    if min(mark_price, quantity, average_entry, hard_stop, tp1, tp2, trailing_start, trailing_distance, partial_ratio) <= 0:
        return {
            "final_decision": "HOLD_POSITION",
            "reason_code": "POSITION_MARK_DATA_INVALID",
            "message": "PAPER position exit evaluation is missing valid public mark data",
            "sell_quantity": "0",
            "sell_notional": "0",
            **rotation_context,
        }

    decision = "HOLD_POSITION"
    reason = "EXIT_CONDITION_NOT_MET"
    return_pct = Decimal("0") if average_entry <= 0 else ((mark_price - average_entry) / average_entry * Decimal("100"))
    quality_feedback_exit_condition_passed = (
        isinstance(managed_candidate, dict)
        and managed_candidate.get("recent_failure_feedback_kind") == "PRELIMINARY_ROBUSTNESS_FAIL"
        and _candidate_recent_failure_cooldown_active(managed_candidate)
        and return_pct <= ROTATION_EXIT_MAX_POSITIVE_RETURN_PCT
    )
    if quality_feedback_exit_condition_passed:
        rotation_context.update(
            {
                "quality_feedback_exit_status": "ACTIVE",
                "quality_feedback_exit_feedback_kind": managed_candidate.get("recent_failure_feedback_kind"),
                "quality_feedback_exit_reason_code": managed_candidate.get("recent_failure_reason_code"),
                "quality_feedback_exit_condition_passed": True,
                "quality_feedback_exit_action": "FULL_EXIT",
            }
        )
    if isinstance(managed_candidate, dict) and isinstance(rotation_candidate, dict):
        net_ev_advantage = _decimal(rotation_context["rotation_net_ev_advantage_bps"])
        score_advantage = _decimal(rotation_context["rotation_symbol_score_advantage"])
        managed_no_trade_reason = str(managed_candidate.get("no_trade_reason") or "")
        managed_is_weak_or_unqualified = (
            managed_candidate.get("decision") != "PAPER_ENTRY_REVIEW"
            or managed_no_trade_reason in ROTATION_EXIT_WEAK_NO_TRADE_REASONS
            or return_pct <= ROTATION_EXIT_MAX_POSITIVE_RETURN_PCT
        )
        rotation_condition_passed = (
            rotation_candidate.get("decision") == "PAPER_ENTRY_REVIEW"
            and net_ev_advantage >= ROTATION_EXIT_MIN_NET_EV_ADVANTAGE_BPS
            and score_advantage >= ROTATION_EXIT_MIN_SYMBOL_SCORE_BUFFER
            and managed_is_weak_or_unqualified
        )
        rotation_context["rotation_condition_passed"] = rotation_condition_passed
        if rotation_condition_passed:
            rotation_context["rotation_reason_code"] = (
                "REGIME_ROTATION_EXIT"
                if managed_candidate.get("regime") == "RISK_OFF"
                else "ROTATION_OPPORTUNITY_COST"
            )
            rotation_context["rotation_action"] = "FULL_EXIT"
    strategy_family = str(exit_plan.get("strategy_family") or "")
    regime = str(features.get("regime") or "")
    vwap_reversion_target = _decimal(exit_plan.get("vwap_reversion_target"))
    breakout_invalidation_level = _decimal(exit_plan.get("breakout_invalidation_level"))
    range_breakout_pct = _decimal(features.get("range_breakout_pct"))
    trend_exhaustion_status = str(features.get("trend_exhaustion_status") or "PASS")
    strategy_exit_reason: str | None = None
    if strategy_family == "PULLBACK_TREND_LONG" and regime != "UPTREND" and return_pct <= Decimal("0.25"):
        strategy_exit_reason = STRATEGY_EXIT_REASON_TREND_INVALIDATED
        rotation_context["trend_invalidation_regime"] = regime
    elif strategy_family == "VWAP_MEAN_REVERSION":
        if regime not in {"RANGE"} and return_pct <= Decimal("0.25"):
            strategy_exit_reason = STRATEGY_EXIT_REASON_RANGE_BREAK_INVALIDATED
        elif vwap_reversion_target > 0 and mark_price >= vwap_reversion_target:
            strategy_exit_reason = STRATEGY_EXIT_REASON_VWAP_REVERSION_COMPLETE
        elif mark_price >= tp1:
            strategy_exit_reason = STRATEGY_EXIT_REASON_VWAP_FIXED_TP
    elif strategy_family == "BREAKOUT_RETEST_LONG":
        if breakout_invalidation_level > 0 and mark_price <= breakout_invalidation_level:
            strategy_exit_reason = STRATEGY_EXIT_REASON_BREAKOUT_LEVEL_LOST
        elif range_breakout_pct < 0 and return_pct <= Decimal("0.25"):
            strategy_exit_reason = STRATEGY_EXIT_REASON_FALSE_BREAKOUT_INVALIDATED
        elif trend_exhaustion_status == "WARN" and return_pct <= ROTATION_EXIT_MAX_POSITIVE_RETURN_PCT:
            strategy_exit_reason = STRATEGY_EXIT_REASON_VOLATILITY_INVALIDATED
    if mark_price <= hard_stop:
        decision = "EXIT_POSITION"
        reason = "HARD_STOP"
    elif str(features.get("regime")) == "RISK_OFF" and mark_price < average_entry:
        decision = "EXIT_POSITION"
        reason = "REGIME_REVERSAL"
    elif strategy_exit_reason is not None:
        decision = "EXIT_POSITION"
        reason = strategy_exit_reason
        rotation_context.update(
            {
                "strategy_exit_reason_code": strategy_exit_reason,
                "strategy_exit_condition_passed": True,
                "strategy_exit_action": STRATEGY_EXIT_ACTION_FULL_EXIT,
            }
        )
    elif previous_high >= trailing_start and mark_price <= previous_high - trailing_distance:
        decision = "EXIT_POSITION"
        reason = "TRAILING_STOP"
    elif mark_price >= tp2:
        decision = "EXIT_POSITION"
        reason = "TAKE_PROFIT_2"
    elif quality_feedback_exit_condition_passed:
        decision = "EXIT_POSITION"
        reason = "COOLDOWN"
    elif rotation_context["rotation_condition_passed"]:
        decision = "EXIT_POSITION"
        reason = str(rotation_context["rotation_reason_code"] or "ROTATION_OPPORTUNITY_COST")
    elif mark_price >= tp1:
        decision = "REDUCE_POSITION"
        reason = "TAKE_PROFIT_1"

    if decision == "REDUCE_POSITION":
        sell_quantity = quantity * partial_ratio
        if sell_quantity * mark_price < UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL:
            decision = "EXIT_POSITION"
            reason = "TAKE_PROFIT_1_MIN_NOTIONAL_FULL_EXIT"
            sell_quantity = quantity
    elif decision == "EXIT_POSITION":
        sell_quantity = quantity
    else:
        sell_quantity = Decimal("0")
    return {
        "final_decision": decision,
        "reason_code": reason,
        "message": f"{reason}: mark={_decimal_text(mark_price)}, entry={_decimal_text(average_entry)}, return_pct={_decimal_text(return_pct)}",
        "sell_quantity": _decimal_text(sell_quantity),
        "sell_notional": _decimal_text(sell_quantity * mark_price),
        "mark_price": _decimal_text(mark_price),
        "average_entry_price": _decimal_text(average_entry),
        "return_pct": _decimal_text(return_pct),
        "hard_stop": _decimal_text(hard_stop),
        "tp1": _decimal_text(tp1),
        "tp2": _decimal_text(tp2),
        "trailing_start": _decimal_text(trailing_start),
        "trailing_distance": _decimal_text(trailing_distance),
        **rotation_context,
    }


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
    last = closes[-1]
    first = closes[0]
    data_bad_active = total_volume <= 0 or last <= 0 or first <= 0
    vwap = last if total_volume <= 0 else sum(price * volume for price, volume in zip(typical_values, volumes)) / total_volume
    total_quote_volume = sum(close * volume for close, volume in zip(closes, volumes))
    previous_high = max(_decimal(candle["high"]) for candle in candles[:-1])
    ema_fast = _ema(closes, 3)
    ema_slow = _ema(closes, 5)
    high = max(closes)
    low = min(closes)
    volatility_pct = Decimal("0") if last <= 0 else ((high - low) / last * Decimal("100"))
    momentum_pct = Decimal("0") if first <= 0 else ((last - first) / first * Decimal("100"))
    return_signature = [
        _decimal_text(
            Decimal("0")
            if closes[index - 1] <= 0
            else ((closes[index] - closes[index - 1]) / closes[index - 1] * Decimal("100")).quantize(Decimal("0.0001"))
        )
        for index in range(1, len(closes))
    ]
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
    quiet_range_active = (
        regime == "RANGE"
        and volatility_pct <= QUIET_MAX_VOLATILITY_PCT
        and volume_expansion_ratio <= QUIET_MAX_VOLUME_EXPANSION_RATIO
    )
    volatility_expansion_active = (
        volatility_pct >= VOLATILITY_EXPANSION_MIN_VOLATILITY_PCT
        and volume_expansion_ratio >= VOLATILITY_EXPANSION_MIN_VOLUME_RATIO
        and max(Decimal("0"), range_breakout_pct) >= VOLATILITY_EXPANSION_MIN_RANGE_BREAKOUT_PCT
    )
    panic_active = regime == "RISK_OFF" and (
        momentum_pct <= PANIC_MOMENTUM_PCT
        or (
            volatility_pct >= PANIC_VOLATILITY_PCT
            and volume_expansion_ratio >= VOLATILITY_EXPANSION_MIN_VOLUME_RATIO
        )
    )
    uncertain_active = (
        regime == "RANGE"
        and not quiet_range_active
        and not volatility_expansion_active
        and abs(momentum_pct) <= UNCERTAIN_MAX_ABS_MOMENTUM_PCT
        and abs(vwap_distance_pct) <= UNCERTAIN_MAX_ABS_VWAP_DISTANCE_PCT
    )
    if data_bad_active:
        market_state = "DATA_BAD"
    elif panic_active:
        market_state = "PANIC"
    elif regime == "RISK_OFF":
        market_state = "DOWNTREND"
    elif volatility_expansion_active:
        market_state = "VOLATILITY_EXPANSION"
    elif quiet_range_active:
        market_state = "QUIET_RANGE"
    elif uncertain_active:
        market_state = "UNCERTAIN"
    else:
        market_state = regime
    trend_structure_score = Decimal("1") if regime == "UPTREND" else Decimal("0")
    trend_momentum_confirmation = _clamp_decimal((momentum_pct - Decimal("0.35")) / Decimal("1.65"))
    trend_volume_confirmation = _clamp_decimal(
        (volume_expansion_ratio - Decimal("0.85")) / Decimal("0.65")
    )
    trend_vwap_pullback_quality = _clamp_decimal(
        (vwap_distance_pct - TREND_PULLBACK_ALIGNMENT_MIN_VWAP_DISTANCE_PCT) / Decimal("1.25")
    )
    trend_ema_alignment = Decimal("1") if ema_fast > ema_slow and last >= ema_slow else Decimal("0")
    trend_pullback_alignment_score = (
        Decimal("0.30") * trend_structure_score
        + Decimal("0.25") * trend_momentum_confirmation
        + Decimal("0.20") * trend_volume_confirmation
        + Decimal("0.15") * trend_vwap_pullback_quality
        + Decimal("0.10") * trend_ema_alignment
    )
    trend_confirmation_active = (
        volume_expansion_ratio >= TREND_CONFIRMATION_MIN_VOLUME_EXPANSION
        or momentum_pct >= TREND_CONFIRMATION_MIN_MOMENTUM_PCT
        or max(Decimal("0"), range_breakout_pct) >= BREAKOUT_CONFIRMATION_MIN_RANGE_BREAKOUT_PCT
    )
    if regime != "UPTREND":
        trend_pullback_alignment_reason = "REGIME_NOT_UPTREND"
    elif not trend_confirmation_active:
        trend_pullback_alignment_reason = "WEAK_TREND_CONFIRMATION"
    elif vwap_distance_pct < TREND_PULLBACK_ALIGNMENT_MIN_VWAP_DISTANCE_PCT:
        trend_pullback_alignment_reason = "VWAP_BREAKDOWN"
    elif trend_pullback_alignment_score < TREND_PULLBACK_ALIGNMENT_MIN_SCORE:
        trend_pullback_alignment_reason = "ALIGNMENT_SCORE_LOW"
    else:
        trend_pullback_alignment_reason = "PASS"
    positive_vwap_extension_pct = max(Decimal("0"), vwap_distance_pct)
    trend_exhaustion_score = (
        Decimal("0.35") * _clamp_decimal((volatility_pct - TREND_EXHAUSTION_MIN_VOLATILITY_PCT) / Decimal("3.00"))
        + Decimal("0.30") * _clamp_decimal((momentum_pct - TREND_EXHAUSTION_MIN_MOMENTUM_PCT) / Decimal("3.00"))
        + Decimal("0.25") * _clamp_decimal((volume_expansion_ratio - TREND_EXHAUSTION_MIN_VOLUME_EXPANSION) / Decimal("1.50"))
        + Decimal("0.10") * _clamp_decimal(positive_vwap_extension_pct / Decimal("1.50"))
    )
    trend_exhaustion_active = (
        regime == "UPTREND"
        and volatility_pct >= TREND_EXHAUSTION_MIN_VOLATILITY_PCT
        and momentum_pct >= TREND_EXHAUSTION_MIN_MOMENTUM_PCT
        and volume_expansion_ratio >= TREND_EXHAUSTION_MIN_VOLUME_EXPANSION
    )
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
        "return_signature": return_signature,
        "return_signature_formula": "close_to_close_return_pct over the runtime candle window, used only for PAPER symbol correlation clustering",
        "total_quote_volume": _decimal_text(total_quote_volume),
        "volume_expansion_ratio": _decimal_text(volume_expansion_ratio),
        "vwap_distance_pct": _decimal_text(vwap_distance_pct),
        "range_breakout_pct": _decimal_text(range_breakout_pct),
        "spread_bps": "1.00",
        "liquidity_status": "PASS",
        "volatility_status": "PASS" if volatility_pct < Decimal("6") else "WARN",
        "regime": regime,
        "market_state": market_state,
        "quiet_range_status": "ACTIVE" if quiet_range_active else "CLEAR",
        "volatility_expansion_status": "ACTIVE" if volatility_expansion_active else "CLEAR",
        "regime_detail_formula": (
            "Upbit KRW spot is long-only: DATA_BAD, PANIC, DOWNTREND/RISK_OFF, and UNCERTAIN block new entries; "
            "QUIET_RANGE blocks trend/breakout and permits only limited VWAP range candidates when abs(vwap_distance)>=0.55pct "
            "and symbol_score>=0.60; VOLATILITY_EXPANSION enables breakout candidates when volatility>=2.50pct, "
            "volume_expansion>=1.20, and range_breakout>=0.03pct"
        ),
        "trend_pullback_alignment_status": "PASS" if trend_pullback_alignment_reason == "PASS" else "FAIL",
        "trend_pullback_alignment_score": _decimal_text(
            trend_pullback_alignment_score.quantize(Decimal("0.0001"))
        ),
        "trend_pullback_alignment_reason": trend_pullback_alignment_reason,
        "trend_pullback_alignment_formula": (
            "PASS when UPTREND, confirmation(volume>=1.05 or momentum>=1.50 or breakout>=0.03), "
            "vwap_distance>=-0.25pct, and score>=0.70; "
            "score=0.30*trend_structure+0.25*momentum+0.20*volume+0.15*vwap_pullback+0.10*ema_alignment"
        ),
        "trend_exhaustion_status": "WARN" if trend_exhaustion_active else "PASS",
        "trend_exhaustion_score": _decimal_text(trend_exhaustion_score.quantize(Decimal("0.0001"))),
        "trend_exhaustion_formula": (
            "WARN when UPTREND and volatility>=3.00pct and momentum>=3.00pct "
            "and volume_expansion>=1.50; score=0.35*vol+0.30*momentum+0.25*volume+0.10*vwap_extension"
        ),
    }


def _matches_legacy_feature_snapshot_projection(
    reported: Any,
    expected: dict[str, Any],
) -> bool:
    if not isinstance(reported, dict):
        return False
    if not set(reported).issubset(set(expected)):
        return False
    for key, value in expected.items():
        if key in CURRENT_FEATURE_PROJECTION_UPGRADE_FIELDS and key not in reported:
            continue
        if reported.get(key) != value:
            return False
    return True


def _paper_orderbook_proxy(features: dict[str, Any]) -> dict[str, Any]:
    mark_price = max(Decimal("0"), _decimal(features.get("last_price")))
    spread_bps = max(Decimal("0.5"), _decimal(features.get("spread_bps")))
    quote_volume = max(Decimal("0"), _decimal(features.get("total_quote_volume")))
    volatility_pct = max(Decimal("0"), _decimal(features.get("volatility_pct")))
    volume_expansion = max(Decimal("0"), _decimal(features.get("volume_expansion_ratio")))
    depth_factor = (
        Decimal("0.040")
        + _clamp_decimal(volume_expansion / Decimal("3"), high=Decimal("1")) * Decimal("0.015")
        - _clamp_decimal(volatility_pct / Decimal("10"), high=Decimal("1")) * Decimal("0.010")
    )
    depth_factor = _clamp_decimal(depth_factor, low=Decimal("0.015"), high=Decimal("0.060"))
    aggregate_depth = Decimal("0") if quote_volume <= 0 else max(Decimal("100000"), quote_volume * depth_factor)
    top_depth = Decimal("0") if aggregate_depth <= 0 else max(Decimal("10000"), aggregate_depth * Decimal("0.012"))
    queue_ahead = top_depth * Decimal("0.22")
    bid_price = Decimal("0") if mark_price <= 0 else mark_price * (Decimal("1") - (spread_bps / Decimal("20000")))
    ask_price = Decimal("0") if mark_price <= 0 else mark_price * (Decimal("1") + (spread_bps / Decimal("20000")))
    liquidity_status = str(features.get("liquidity_status") or "BLOCKED")
    if mark_price <= 0 or aggregate_depth < UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL:
        liquidity_status = "BLOCKED"
    return {
        "model_id": PAPER_BROKER_MODEL_ID,
        "source": "PUBLIC_CANDLE_DERIVED_L2_PROXY",
        "mark_price": _decimal_text(mark_price),
        "best_bid": _decimal_text(bid_price),
        "best_ask": _decimal_text(ask_price),
        "spread_bps": _decimal_text(spread_bps),
        "estimated_top_bid_depth_krw": _decimal_text(top_depth),
        "estimated_top_ask_depth_krw": _decimal_text(top_depth),
        "estimated_aggregate_depth_krw": _decimal_text(aggregate_depth),
        "queue_ahead_notional_krw": _decimal_text(queue_ahead),
        "queue_position_fraction": _decimal_text(Decimal("0.22")),
        "depth_formula": "max(100000,total_quote_volume*(0.040+volume_expansion_adj-volatility_adj)); top_depth=max(10000,aggregate*0.012)",
        "total_quote_volume": _decimal_text(quote_volume),
        "volatility_pct": _decimal_text(volatility_pct),
        "volume_expansion_ratio": _decimal_text(volume_expansion),
        "liquidity_status": liquidity_status,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _paper_candidate_cost_breakdown(features: dict[str, Any]) -> dict[str, str]:
    proxy = _paper_orderbook_proxy(features)
    spread_bps = _decimal(proxy["spread_bps"])
    volatility_pct = max(Decimal("0"), _decimal(features.get("volatility_pct")))
    aggregate_depth = max(Decimal("1"), _decimal(proxy["estimated_aggregate_depth_krw"]))
    expected_notional = UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL
    adaptive_slippage_bps = max(Decimal("1.50"), (spread_bps / Decimal("2")) + (volatility_pct * Decimal("0.80")))
    impact_bps = min(Decimal("30"), (expected_notional / aggregate_depth) * Decimal("500"))
    latency_bps = min(Decimal("15"), Decimal("0.75") + (volatility_pct * Decimal("0.45")) + (impact_bps * Decimal("0.10")))
    return {
        "fee_bps": "5",
        "slippage_bps": _decimal_text(adaptive_slippage_bps),
        "spread_bps": _decimal_text(spread_bps),
        "market_impact_bps": _decimal_text(impact_bps),
        "latency_bps": _decimal_text(latency_bps),
    }


def _cost_breakdown_sum(cost_breakdown_bps: dict[str, Any]) -> Decimal:
    return sum(
        (_decimal(cost_breakdown_bps.get(field)) for field in ("fee_bps", "slippage_bps", "spread_bps", "market_impact_bps", "latency_bps")),
        Decimal("0"),
    )


def _simulate_paper_broker_execution(
    *,
    cycle_id: str,
    symbol: str,
    side: str,
    requested_notional: Decimal,
    requested_quantity: Decimal,
    mark_price: Decimal,
    features: dict[str, Any],
    fee_rate: Decimal,
) -> dict[str, Any]:
    proxy = _paper_orderbook_proxy(features)
    spread_bps = _decimal(proxy["spread_bps"])
    volatility_pct = max(Decimal("0"), _decimal(features.get("volatility_pct")))
    aggregate_depth = max(Decimal("1"), _decimal(proxy["estimated_aggregate_depth_krw"]))
    top_depth = max(
        Decimal("0"),
        _decimal(proxy["estimated_top_ask_depth_krw"] if side == "BUY" else proxy["estimated_top_bid_depth_krw"]),
    )
    queue_ahead = max(Decimal("0"), _decimal(proxy["queue_ahead_notional_krw"]))
    queue_fill_probability = _clamp_decimal((top_depth - queue_ahead) / max(top_depth, Decimal("1")), low=Decimal("0"), high=Decimal("1"))
    impact_bps = min(Decimal("150"), (requested_notional / aggregate_depth) * Decimal("500"))
    adaptive_slippage_bps = max(Decimal("1.50"), volatility_pct * Decimal("0.80"))
    latency_bps = min(Decimal("60"), Decimal("0.75") + (volatility_pct * Decimal("0.45")) + (impact_bps * Decimal("0.10")))
    latency_ms = Decimal("250") + (volatility_pct * Decimal("80")) + (impact_bps * Decimal("5"))
    adverse_price_bps = (spread_bps / Decimal("2")) + adaptive_slippage_bps + impact_bps + latency_bps
    if requested_notional <= top_depth * Decimal("0.85"):
        fill_ratio = Decimal("1")
    else:
        available = top_depth * (Decimal("0.70") + (queue_fill_probability * Decimal("0.20")))
        fill_ratio = _clamp_decimal(available / max(requested_notional, Decimal("1")), low=Decimal("0"), high=Decimal("1"))
    lifecycle_state = "FILLED" if fill_ratio >= Decimal("0.999999") else "PARTIALLY_FILLED"
    reject_reason = None
    cancel_reason = None
    estimated_filled_notional = requested_notional * fill_ratio
    risk_reducing_partial_exit_allowed = (
        side == "SELL"
        and fill_ratio > 0
        and estimated_filled_notional >= UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL
    )
    if (
        mark_price <= 0
        or requested_notional <= 0
        or requested_quantity <= 0
        or proxy.get("liquidity_status") == "BLOCKED"
        or (impact_bps > PAPER_BROKER_MAX_IMPACT_BPS and not risk_reducing_partial_exit_allowed)
        or (fill_ratio < PAPER_BROKER_MIN_FILL_RATIO and not risk_reducing_partial_exit_allowed)
    ):
        lifecycle_state = "REJECTED"
        reject_reason = "PAPER_DEPTH_OR_IMPACT_REJECT"
        fill_ratio = Decimal("0")
    elif latency_bps > PAPER_BROKER_MAX_LATENCY_BPS:
        lifecycle_state = "CANCELLED"
        cancel_reason = "PAPER_LATENCY_CANCEL"
        fill_ratio = Decimal("0")

    if side == "BUY":
        fill_price = mark_price * (Decimal("1") + (adverse_price_bps / Decimal("10000")))
        filled_notional = requested_notional * fill_ratio
        filled_quantity = Decimal("0") if fill_price <= 0 else filled_notional / fill_price
        reserved_cash = requested_notional * (Decimal("1") + fee_rate)
        reserved_quantity = Decimal("0")
    else:
        fill_price = mark_price * (Decimal("1") - (adverse_price_bps / Decimal("10000")))
        filled_quantity = requested_quantity * fill_ratio
        filled_notional = filled_quantity * fill_price
        reserved_cash = Decimal("0")
        reserved_quantity = requested_quantity
    fee_amount = filled_notional * fee_rate
    reservation_used = filled_notional + fee_amount if side == "BUY" else filled_quantity
    reservation_requested = reserved_cash if side == "BUY" else reserved_quantity
    reservation_release = max(Decimal("0"), reservation_requested - reservation_used)
    return {
        "fill_source": PAPER_BROKER_FILL_SOURCE,
        "broker_model_id": PAPER_BROKER_MODEL_ID,
        "order_lifecycle_state": lifecycle_state,
        "client_order_id": hashlib.sha256(f"{cycle_id}:{symbol}:{side}:adaptive-paper-fill".encode("utf-8")).hexdigest()[:24].upper(),
        "symbol": symbol,
        "side": side,
        "order_type": "MARKETABLE_LIMIT_PAPER",
        "time_in_force": "IOC_PAPER",
        "maker_taker": "TAKER",
        "requested_notional": _decimal_text(requested_notional),
        "requested_quantity": _decimal_text(requested_quantity),
        "filled_notional": _decimal_text(filled_notional),
        "filled_quantity": _decimal_text(filled_quantity),
        "notional": _decimal_text(filled_notional),
        "quantity": _decimal_text(filled_quantity),
        "fill_ratio": _decimal_text(fill_ratio),
        "partial_fill": lifecycle_state == "PARTIALLY_FILLED",
        "fill_price": _decimal_text(fill_price),
        "mark_price": _decimal_text(mark_price),
        "fee_rate": _decimal_text(fee_rate),
        "fee_amount": _decimal_text(fee_amount),
        "fee_asset": "KRW",
        "slippage_bps": _decimal_text(adverse_price_bps),
        "adaptive_slippage_bps": _decimal_text(adaptive_slippage_bps),
        "spread_bps": _decimal_text(spread_bps),
        "market_impact_bps": _decimal_text(impact_bps),
        "latency_penalty_bps": _decimal_text(latency_bps),
        "latency_ms": _decimal_text(latency_ms),
        "queue_ahead_notional_krw": _decimal_text(queue_ahead),
        "queue_fill_probability": _decimal_text(queue_fill_probability),
        "orderbook_proxy": proxy,
        "reservation_required": True,
        "reserved_cash": _decimal_text(reserved_cash),
        "reserved_quantity": _decimal_text(reserved_quantity),
        "reservation_released": True,
        "reservation_release_amount": _decimal_text(reservation_release),
        "reject_reason": reject_reason,
        "cancel_reason": cancel_reason,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "private_endpoint_called": False,
        "credential_load_attempted": False,
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


def _return_signature_correlation(left: list[Any], right: list[Any]) -> Decimal:
    left_values = [_decimal(value) for value in left]
    right_values = [_decimal(value) for value in right]
    count = min(len(left_values), len(right_values))
    if count < 3:
        return Decimal("0")
    left_values = left_values[-count:]
    right_values = right_values[-count:]
    left_mean = sum(left_values, Decimal("0")) / Decimal(count)
    right_mean = sum(right_values, Decimal("0")) / Decimal(count)
    numerator = sum(
        (left_values[index] - left_mean) * (right_values[index] - right_mean)
        for index in range(count)
    )
    left_variance = sum((value - left_mean) ** 2 for value in left_values)
    right_variance = sum((value - right_mean) ** 2 for value in right_values)
    if left_variance <= 0 or right_variance <= 0:
        return Decimal("0")
    denominator = (left_variance.sqrt() * right_variance.sqrt())
    if denominator <= 0:
        return Decimal("0")
    return _clamp_decimal(numerator / denominator, low=Decimal("-1"), high=Decimal("1"))


def _adaptive_symbol_top_n(symbol_count: int) -> int:
    if symbol_count <= 0:
        return 0
    if symbol_count <= SYMBOL_ADAPTIVE_TOP_N_MIN:
        return symbol_count
    # Conservative square-root growth keeps the PAPER review set broad enough to rotate,
    # but bounded so weak tail symbols do not become entry candidates.
    sqrt_ceiling = 1
    while sqrt_ceiling * sqrt_ceiling < symbol_count:
        sqrt_ceiling += 1
    top_n = sqrt_ceiling + 1
    return max(SYMBOL_ADAPTIVE_TOP_N_MIN, min(SYMBOL_ADAPTIVE_TOP_N_MAX, symbol_count, top_n))


def _symbol_selection_score(
    features: dict[str, Any],
    *,
    correlation_context: dict[str, Any] | None = None,
) -> dict[str, str | bool | int | None]:
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
    context = correlation_context or {}
    correlation_penalty = _decimal(context.get("correlation_penalty", "0"))
    adjusted_score = max(Decimal("0"), score - correlation_penalty)
    return {
        "symbol_selection_score": _decimal_text(adjusted_score.quantize(Decimal("0.0001"))),
        "base_symbol_selection_score": _decimal_text(score.quantize(Decimal("0.0001"))),
        "liquidity_score": _decimal_text(liquidity_score.quantize(Decimal("0.0001"))),
        "volatility_score": _decimal_text(volatility_score.quantize(Decimal("0.0001"))),
        "relative_strength_score": _decimal_text(relative_strength_score.quantize(Decimal("0.0001"))),
        "spread_quality_score": _decimal_text(spread_quality_score.quantize(Decimal("0.0001"))),
        "volume_expansion_score": _decimal_text(volume_expansion_score.quantize(Decimal("0.0001"))),
        "regime_fit_score": _decimal_text(regime_fit.quantize(Decimal("0.0001"))),
        "correlation_cluster_id": context.get("correlation_cluster_id") or f"cluster:{features.get('symbol')}",
        "correlation_cluster_rank": int(context.get("correlation_cluster_rank", 1) or 1),
        "correlation_cluster_status": context.get("correlation_cluster_status") or "LEADER",
        "correlation_cluster_leader_symbol": context.get("correlation_cluster_leader_symbol") or features.get("symbol"),
        "correlation_max_peer_symbol": context.get("correlation_max_peer_symbol"),
        "correlation_max_abs": _decimal_text(_decimal(context.get("correlation_max_abs", "0")).quantize(Decimal("0.0001"))),
        "correlation_penalty": _decimal_text(correlation_penalty.quantize(Decimal("0.0001"))),
        "correlation_cluster_threshold": _decimal_text(SYMBOL_CORRELATION_CLUSTER_THRESHOLD),
        "adaptive_top_n": int(context.get("adaptive_top_n", 1) or 1),
        "rank_after_correlation": int(context.get("rank_after_correlation", 1) or 1),
        "adaptive_top_n_filter_status": context.get("adaptive_top_n_filter_status") or "IN_TOP_N",
        "eligible_after_correlation": bool(context.get("eligible_after_correlation", True)),
        "minimum_symbol_selection_score": _decimal_text(MIN_SYMBOL_SELECTION_SCORE),
    }


def _symbol_selection_scores_for_universe(
    feature_snapshots_by_symbol: dict[str, dict[str, Any]]
) -> dict[str, dict[str, str | bool | int | None]]:
    if not feature_snapshots_by_symbol:
        return {}
    base_scores = {
        symbol: _decimal(_symbol_selection_score(features).get("base_symbol_selection_score"))
        for symbol, features in feature_snapshots_by_symbol.items()
    }
    ordered_symbols = sorted(
        feature_snapshots_by_symbol,
        key=lambda item: (
            -base_scores[item],
            -_decimal(feature_snapshots_by_symbol[item].get("momentum_pct")),
            -_decimal(feature_snapshots_by_symbol[item].get("total_quote_volume")),
            item,
        ),
    )
    clusters: list[dict[str, Any]] = []
    contexts: dict[str, dict[str, Any]] = {}
    for symbol in ordered_symbols:
        features = feature_snapshots_by_symbol[symbol]
        signature = list(features.get("return_signature") or [])
        best_cluster: dict[str, Any] | None = None
        best_correlation = Decimal("0")
        best_peer: str | None = None
        for cluster in clusters:
            correlation = abs(_return_signature_correlation(signature, cluster["return_signature"]))
            if correlation > best_correlation:
                best_correlation = correlation
                best_cluster = cluster
                best_peer = str(cluster["leader_symbol"])
        if best_cluster is not None and best_correlation >= SYMBOL_CORRELATION_CLUSTER_THRESHOLD:
            best_cluster["members"].append(symbol)
            contexts[symbol] = {
                "correlation_cluster_id": best_cluster["cluster_id"],
                "correlation_cluster_rank": len(best_cluster["members"]),
                "correlation_cluster_status": "DIVERSIFICATION_FILTERED",
                "correlation_cluster_leader_symbol": best_cluster["leader_symbol"],
                "correlation_max_peer_symbol": best_peer,
                "correlation_max_abs": best_correlation,
                "correlation_penalty": SYMBOL_CORRELATION_CLUSTER_PENALTY,
            }
        else:
            cluster_id = f"cluster:{len(clusters) + 1}:{symbol}"
            clusters.append(
                {
                    "cluster_id": cluster_id,
                    "leader_symbol": symbol,
                    "return_signature": signature,
                    "members": [symbol],
                }
            )
            contexts[symbol] = {
                "correlation_cluster_id": cluster_id,
                "correlation_cluster_rank": 1,
                "correlation_cluster_status": "LEADER",
                "correlation_cluster_leader_symbol": symbol,
                "correlation_max_peer_symbol": best_peer,
                "correlation_max_abs": best_correlation,
                "correlation_penalty": Decimal("0"),
            }

    adaptive_top_n = _adaptive_symbol_top_n(len(feature_snapshots_by_symbol))
    preliminary = {
        symbol: _symbol_selection_score(features, correlation_context={**contexts[symbol], "adaptive_top_n": adaptive_top_n})
        for symbol, features in feature_snapshots_by_symbol.items()
    }
    ranked_after_correlation = sorted(
        preliminary,
        key=lambda item: (
            -_decimal(preliminary[item].get("symbol_selection_score")),
            -_decimal(feature_snapshots_by_symbol[item].get("momentum_pct")),
            -_decimal(feature_snapshots_by_symbol[item].get("total_quote_volume")),
            item,
        ),
    )
    rank_by_symbol = {symbol: index for index, symbol in enumerate(ranked_after_correlation, start=1)}
    final: dict[str, dict[str, str | bool | int | None]] = {}
    for symbol, features in feature_snapshots_by_symbol.items():
        rank = rank_by_symbol[symbol]
        cluster_filtered = contexts[symbol]["correlation_cluster_status"] == "DIVERSIFICATION_FILTERED"
        outside_top_n = rank > adaptive_top_n
        final[symbol] = _symbol_selection_score(
            features,
            correlation_context={
                **contexts[symbol],
                "adaptive_top_n": adaptive_top_n,
                "rank_after_correlation": rank,
                "adaptive_top_n_filter_status": "OUTSIDE_ADAPTIVE_TOP_N" if outside_top_n else "IN_TOP_N",
                "eligible_after_correlation": not cluster_filtered and not outside_top_n,
            },
        )
    return final


def _setup_confirmation_scores(features: dict[str, Any]) -> dict[str, Decimal]:
    momentum = _decimal(features.get("momentum_pct"))
    volume_expansion = _decimal(features.get("volume_expansion_ratio"))
    range_breakout = max(Decimal("0"), _decimal(features.get("range_breakout_pct")))
    vwap_distance = abs(_decimal(features.get("vwap_distance_pct")))
    trend_persistence = _clamp_decimal((momentum - Decimal("0.35")) / Decimal("1.65"))
    volume_confirmation = _clamp_decimal((volume_expansion - Decimal("0.85")) / Decimal("0.65"))
    breakout_confirmation = (
        _clamp_decimal(range_breakout / Decimal("0.75")) * volume_confirmation
        if range_breakout > 0
        else Decimal("0")
    )
    mean_reversion_distance = _clamp_decimal((vwap_distance - Decimal("0.25")) / Decimal("1.25"))
    mean_reversion_volume = _clamp_decimal((MEAN_REVERSION_MAX_VOLUME_EXPANSION - volume_expansion) / Decimal("0.65"))
    return {
        "trend_persistence": trend_persistence,
        "volume_confirmation": volume_confirmation,
        "breakout_confirmation": breakout_confirmation,
        "mean_reversion_quality": mean_reversion_distance * mean_reversion_volume,
    }


def _candidate(
    *,
    candidate_id: str,
    symbol: str,
    strategy_family: str,
    features: dict[str, Any],
    expected_edge_bps: Decimal,
    cost_breakdown_bps: dict[str, str],
    signal_strength: Decimal,
    regime: str,
    symbol_selection: dict[str, str],
    selection_priority: int,
    recent_failure_feedback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected_cost_bps = _cost_breakdown_sum(cost_breakdown_bps)
    net_ev = expected_edge_bps - expected_cost_bps
    symbol_score = _decimal(symbol_selection.get("symbol_selection_score"))
    recent_failure_feedback = recent_failure_feedback or _recent_failure_clear_feedback()
    cooldown_active = (
        recent_failure_feedback.get("recent_failure_cooldown_status") == "ACTIVE"
        and int(recent_failure_feedback.get("recent_failure_cooldown_cycles_remaining", 0) or 0) > 0
    )
    candidate_selection_score = _candidate_selection_score_value(
        symbol_score=symbol_score,
        net_ev_bps=net_ev,
        signal_strength=signal_strength,
    )
    correlation_filtered = symbol_selection.get("correlation_cluster_status") == "DIVERSIFICATION_FILTERED"
    adaptive_top_n_filtered = symbol_selection.get("adaptive_top_n_filter_status") == "OUTSIDE_ADAPTIVE_TOP_N"
    market_state = str(features.get("market_state") or regime)
    entry_block_reason = _spot_long_entry_block_reason(regime=regime, market_state=market_state)
    strategy_regime_allowed, strategy_policy_reason = _strategy_entry_policy_evaluation(
        strategy_family=strategy_family,
        regime=regime,
        market_state=market_state,
        features=features,
        symbol_score=symbol_score,
    )
    threshold_passed = (
        net_ev > MIN_ENTRY_NET_EV_BPS
        and signal_strength >= MIN_ENTRY_SIGNAL_STRENGTH
        and symbol_score >= MIN_SYMBOL_SELECTION_SCORE
        and entry_block_reason is None
        and strategy_regime_allowed
        and not correlation_filtered
        and not adaptive_top_n_filtered
    )
    decision = "PAPER_ENTRY_REVIEW" if threshold_passed else "NO_TRADE"
    no_trade_reason = None if decision == "PAPER_ENTRY_REVIEW" else "MIN_EDGE_FAIL"
    if entry_block_reason:
        decision = "NO_TRADE"
        no_trade_reason = "REGIME_MISMATCH"
    elif cooldown_active:
        decision = "NO_TRADE"
        no_trade_reason = "COOLDOWN"
    elif correlation_filtered:
        decision = "NO_TRADE"
        no_trade_reason = "CLUSTER_RISK"
    elif adaptive_top_n_filtered:
        decision = "NO_TRADE"
        no_trade_reason = "UNIVERSE_FILTERED"
    elif not strategy_regime_allowed:
        no_trade_reason = "REGIME_MISMATCH" if strategy_policy_reason.endswith("_BLOCK") else "STRATEGY_NOT_ELIGIBLE"
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
        "strategy_entry_policy_id": "UPBIT_KRW_SPOT_STRATEGY_ENTRY_ROUTER_V1",
        "strategy_regime_allowed": strategy_regime_allowed,
        "strategy_policy_reason": strategy_policy_reason,
        "market_state": market_state,
        "entry_block_reason": entry_block_reason,
        "quiet_range_entry_policy": (
            "VWAP_ONLY_DEEP_DISLOCATION" if market_state == "QUIET_RANGE" else "NOT_APPLICABLE"
        ),
        "signal_strength": _decimal_text(signal_strength),
        "signal_grade": "A" if signal_strength >= Decimal("0.7") else "B" if signal_strength >= Decimal("0.55") else "C",
        "expected_edge_bps": _decimal_text(expected_edge_bps),
        "expected_cost_bps": _decimal_text(expected_cost_bps),
        "cost_breakdown_bps": dict(cost_breakdown_bps),
        "cost_model_source": PAPER_RUNTIME_COST_MODEL_SOURCE,
        "cost_model_formula": "fee_bps+adaptive_slippage_bps+spread_bps+public_depth_impact_bps+latency_penalty_bps",
        "net_ev_after_cost_bps": _decimal_text(net_ev),
        "decision": decision,
        "no_trade_reason": no_trade_reason,
        **recent_failure_feedback,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _apply_recent_failure_penalty(
    *,
    edge_bps: Decimal,
    signal_strength: Decimal,
    feedback: dict[str, Any],
) -> tuple[Decimal, Decimal]:
    if feedback.get("recent_failure_cooldown_status") != "ACTIVE":
        return edge_bps, signal_strength
    return (
        edge_bps - _decimal(feedback.get("recent_failure_penalty_bps")),
        _clamp_decimal(signal_strength - _decimal(feedback.get("recent_failure_signal_penalty"))),
    )


def _build_candidates(
    symbol: str,
    features: dict[str, Any],
    *,
    edge_profile: str,
    symbol_selection: dict[str, Any] | None = None,
    recent_failure_feedback: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    regime = str(features["regime"])
    market_state = str(features.get("market_state") or regime)
    cost_breakdown_bps = _paper_candidate_cost_breakdown(features)
    symbol_selection = symbol_selection or _symbol_selection_score(features)
    symbol_score = _decimal(symbol_selection["symbol_selection_score"])
    momentum = _decimal(features.get("momentum_pct"))
    volume_expansion = _decimal(features.get("volume_expansion_ratio"))
    range_breakout = _decimal(features.get("range_breakout_pct"))
    vwap_distance = abs(_decimal(features.get("vwap_distance_pct")))
    setup_scores = _setup_confirmation_scores(features)
    trend_persistence = setup_scores["trend_persistence"]
    volume_confirmation = setup_scores["volume_confirmation"]
    breakout_confirmation = setup_scores["breakout_confirmation"]
    mean_reversion_quality = setup_scores["mean_reversion_quality"]
    pullback_edge = (
        Decimal("5")
        + symbol_score * Decimal("25")
        + trend_persistence * Decimal("14")
        + volume_confirmation * Decimal("10")
    )
    pullback_signal = _clamp_decimal(
        Decimal("0.42") + symbol_score * Decimal("0.25") + trend_persistence * Decimal("0.18") + volume_confirmation * Decimal("0.12")
    )
    trend_confirmation_passed = (
        volume_expansion >= TREND_CONFIRMATION_MIN_VOLUME_EXPANSION
        or momentum >= TREND_CONFIRMATION_MIN_MOMENTUM_PCT
        or max(Decimal("0"), range_breakout) >= BREAKOUT_CONFIRMATION_MIN_RANGE_BREAKOUT_PCT
    )
    if features.get("trend_pullback_alignment_status") != "PASS":
        pullback_edge -= TREND_PULLBACK_ALIGNMENT_EDGE_PENALTY_BPS
        pullback_signal = _clamp_decimal(pullback_signal - TREND_PULLBACK_ALIGNMENT_SIGNAL_PENALTY)
    if not trend_confirmation_passed:
        pullback_edge -= WEAK_TREND_EDGE_PENALTY_BPS
        pullback_signal = _clamp_decimal(pullback_signal - Decimal("0.20"))
    if _decimal(features.get("volatility_pct")) > Decimal("4") and volume_confirmation < Decimal("0.50"):
        pullback_edge -= VOLATILITY_LIQUIDITY_EDGE_PENALTY_BPS
        pullback_signal = _clamp_decimal(pullback_signal - Decimal("0.06"))
    if features.get("trend_exhaustion_status") == "WARN":
        pullback_edge -= TREND_EXHAUSTION_EDGE_PENALTY_BPS
        pullback_signal = _clamp_decimal(pullback_signal - TREND_EXHAUSTION_SIGNAL_PENALTY)

    breakout_edge = Decimal("4") + symbol_score * Decimal("20") + volume_confirmation * Decimal("12") + breakout_confirmation * Decimal("10")
    breakout_signal = _clamp_decimal(
        Decimal("0.38") + symbol_score * Decimal("0.22") + volume_confirmation * Decimal("0.16") + breakout_confirmation * Decimal("0.18")
    )
    breakout_confirmation_passed = (
        volume_expansion >= BREAKOUT_CONFIRMATION_MIN_VOLUME_EXPANSION
        and max(Decimal("0"), range_breakout) >= BREAKOUT_CONFIRMATION_MIN_RANGE_BREAKOUT_PCT
    )
    if not breakout_confirmation_passed:
        breakout_edge -= FALSE_BREAKOUT_EDGE_PENALTY_BPS
        breakout_signal = _clamp_decimal(breakout_signal - Decimal("0.18"))
    if features.get("trend_exhaustion_status") == "WARN":
        breakout_edge -= TREND_EXHAUSTION_EDGE_PENALTY_BPS
        breakout_signal = _clamp_decimal(breakout_signal - TREND_EXHAUSTION_SIGNAL_PENALTY)

    mean_reversion_edge = Decimal("4") + symbol_score * Decimal("16") + mean_reversion_quality * Decimal("14")
    mean_reversion_signal = _clamp_decimal(
        Decimal("0.36") + symbol_score * Decimal("0.18") + mean_reversion_quality * Decimal("0.20")
    )
    mean_reversion_guard_passed = (
        regime == "RANGE"
        and vwap_distance >= MEAN_REVERSION_MIN_VWAP_DISTANCE_PCT
        and volume_expansion <= MEAN_REVERSION_MAX_VOLUME_EXPANSION
    )
    if not mean_reversion_guard_passed:
        mean_reversion_edge -= FAILED_MEAN_REVERSION_EDGE_PENALTY_BPS
        mean_reversion_signal = _clamp_decimal(mean_reversion_signal - Decimal("0.12"))
    if _spot_long_entry_block_reason(regime=regime, market_state=market_state):
        pullback_edge -= Decimal("30")
        breakout_edge -= Decimal("25")
        mean_reversion_edge -= Decimal("18")
        pullback_signal = _clamp_decimal(pullback_signal - Decimal("0.25"))
        breakout_signal = _clamp_decimal(breakout_signal - Decimal("0.22"))
        mean_reversion_signal = _clamp_decimal(mean_reversion_signal - Decimal("0.16"))
    if market_state == "QUIET_RANGE":
        pullback_edge -= Decimal("24")
        breakout_edge -= Decimal("24")
        mean_reversion_edge -= QUIET_RANGE_EDGE_PENALTY_BPS
        pullback_signal = _clamp_decimal(pullback_signal - Decimal("0.20"))
        breakout_signal = _clamp_decimal(breakout_signal - Decimal("0.20"))
        mean_reversion_signal = _clamp_decimal(mean_reversion_signal - QUIET_RANGE_SIGNAL_PENALTY)
    edge_shift = Decimal("-45") if edge_profile == "NEGATIVE" else Decimal("-25") if edge_profile == "WEAK" else Decimal("0")
    pullback_feedback = _recent_failure_feedback_for_candidate(
        symbol=symbol,
        strategy_family="PULLBACK_TREND_LONG",
        candidate_id=f"{symbol}-pullback-trend-long",
        recent_failure_feedback=recent_failure_feedback,
    )
    breakout_feedback = _recent_failure_feedback_for_candidate(
        symbol=symbol,
        strategy_family="BREAKOUT_RETEST_LONG",
        candidate_id=f"{symbol}-breakout-retest-long",
        recent_failure_feedback=recent_failure_feedback,
    )
    mean_reversion_feedback = _recent_failure_feedback_for_candidate(
        symbol=symbol,
        strategy_family="VWAP_MEAN_REVERSION",
        candidate_id=f"{symbol}-vwap-mean-reversion",
        recent_failure_feedback=recent_failure_feedback,
    )
    pullback_edge, pullback_signal = _apply_recent_failure_penalty(
        edge_bps=pullback_edge,
        signal_strength=pullback_signal,
        feedback=pullback_feedback,
    )
    breakout_edge, breakout_signal = _apply_recent_failure_penalty(
        edge_bps=breakout_edge,
        signal_strength=breakout_signal,
        feedback=breakout_feedback,
    )
    mean_reversion_edge, mean_reversion_signal = _apply_recent_failure_penalty(
        edge_bps=mean_reversion_edge,
        signal_strength=mean_reversion_signal,
        feedback=mean_reversion_feedback,
    )
    return [
        _candidate(
            candidate_id=f"{symbol}-pullback-trend-long",
            symbol=symbol,
            strategy_family="PULLBACK_TREND_LONG",
            features=features,
            expected_edge_bps=pullback_edge + edge_shift,
            cost_breakdown_bps=cost_breakdown_bps,
            signal_strength=pullback_signal,
            regime=regime,
            symbol_selection=symbol_selection,
            selection_priority=1,
            recent_failure_feedback=pullback_feedback,
        ),
        _candidate(
            candidate_id=f"{symbol}-breakout-retest-long",
            symbol=symbol,
            strategy_family="BREAKOUT_RETEST_LONG",
            features=features,
            expected_edge_bps=breakout_edge + edge_shift,
            cost_breakdown_bps=cost_breakdown_bps,
            signal_strength=breakout_signal,
            regime=regime,
            symbol_selection=symbol_selection,
            selection_priority=2,
            recent_failure_feedback=breakout_feedback,
        ),
        _candidate(
            candidate_id=f"{symbol}-vwap-mean-reversion",
            symbol=symbol,
            strategy_family="VWAP_MEAN_REVERSION",
            features=features,
            expected_edge_bps=mean_reversion_edge + edge_shift,
            cost_breakdown_bps=cost_breakdown_bps,
            signal_strength=mean_reversion_signal,
            regime=regime,
            symbol_selection=symbol_selection,
            selection_priority=3,
            recent_failure_feedback=mean_reversion_feedback,
        ),
    ]


def _symbol_selection_policy(*, runtime_input_role: str, symbol_count: int) -> dict[str, Any]:
    return {
        "policy_id": "UPBIT_KRW_SPOT_ADAPTIVE_SYMBOL_SELECTION_V1",
        "runtime_input_role": runtime_input_role,
        "symbol_scope": "KRW_UNIVERSE" if symbol_count > 1 else "SINGLE_SYMBOL_FALLBACK",
        "evaluated_symbol_count": symbol_count,
        "adaptive_top_n": _adaptive_symbol_top_n(symbol_count),
        "correlation_cluster_threshold": _decimal_text(SYMBOL_CORRELATION_CLUSTER_THRESHOLD),
        "correlation_cluster_penalty": _decimal_text(SYMBOL_CORRELATION_CLUSTER_PENALTY),
        "selection_formula": (
            "base=0.25*liquidity+0.20*volatility+0.20*relative_strength+0.15*spread_quality"
            "+0.10*volume_expansion+0.10*regime_fit; "
            "symbol_selection_score=max(0,base-correlation_cluster_penalty)"
        ),
        "candidate_formula": (
            "edge=strategy_base+symbol_score+trend_or_breakout_or_mean_reversion_confirmation"
            "-pullback_alignment_weak_trend_false_breakout_failed_mean_reversion_trend_exhaustion_recent_failure_penalties; "
            "selection=0.45*symbol_score+0.35*net_ev_score+0.20*signal_strength"
        ),
        "minimum_symbol_selection_score": _decimal_text(MIN_SYMBOL_SELECTION_SCORE),
        "minimum_entry_net_ev_bps": _decimal_text(MIN_ENTRY_NET_EV_BPS),
        "minimum_entry_signal_strength": _decimal_text(MIN_ENTRY_SIGNAL_STRENGTH),
        "deterministic_priority": (
            "candidate_selection_score DESC, net_ev_after_cost_bps DESC, selection_priority ASC; "
            "pullback requires UPTREND alignment score>=0.70 and vwap_distance>=-0.25pct, "
            "setup confirmation thresholds volume>=1.05 or momentum>=1.50 for pullback, "
            "volume>=1.20 and range_breakout>=0.03 for breakout, RANGE and VWAP distance>=0.35 for mean reversion; "
            "trend exhaustion guard volatility>=3.00pct and momentum>=3.00pct and volume>=1.50 applies -42bps edge; "
            "recent negative PAPER closed loss applies 3-cycle symbol cooldown and ranking penalty; "
            "preliminary robustness/OOS failure applies evidence-backed candidate/symbol cooldown before more PAPER entry review; "
            "correlation clusters use close-to-close return Pearson abs>=0.92, keep the strongest leader, "
            "filter duplicate cluster members with CLUSTER_RISK, and keep only adaptive top-N symbols eligible for entry review"
        ),
        "fallback_behavior": (
            "Use configured single symbol when no universe is supplied; block with RISK_OFF/MEASUREMENT_MISSING "
            "when no valid public candle source exists; symbols outside adaptive top-N or duplicate correlation clusters remain PAPER evidence only."
        ),
        "acceptance_condition": (
            "Every evaluated symbol must have one PAPER_SYMBOL_EVIDENCE_ONLY scorecard, correlation/top-N reason fields, "
            "and all live/order flags false."
        ),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _build_symbol_evidence_scorecard(
    *,
    cycle_id: str,
    rank_input_order: int,
    symbol: str,
    features: dict[str, Any],
    symbol_selection: dict[str, str],
    symbol_candidates: list[dict[str, Any]],
    source_binding: dict[str, Any] | None,
) -> dict[str, Any]:
    sorted_candidates = sorted(symbol_candidates, key=_candidate_rank_key, reverse=True)
    best_candidate = sorted_candidates[0] if sorted_candidates else {}
    paper_entry_review_count = sum(1 for candidate in symbol_candidates if candidate.get("decision") == "PAPER_ENTRY_REVIEW")
    no_trade_reasons = sorted(
        {
            str(candidate.get("no_trade_reason"))
            for candidate in symbol_candidates
            if candidate.get("no_trade_reason")
        }
    )
    source_binding = source_binding or {}
    return {
        "source": "PAPER_RUNTIME_SYMBOL_EVIDENCE_SCORECARD",
        "evidence_scope": "PAPER_SYMBOL_EVIDENCE_ONLY",
        "cycle_id": cycle_id,
        "rank_input_order": rank_input_order,
        "symbol": symbol,
        "regime": features.get("regime"),
        "market_state": features.get("market_state"),
        "quiet_range_status": features.get("quiet_range_status"),
        "volatility_expansion_status": features.get("volatility_expansion_status"),
        "last_price": features.get("last_price"),
        "total_quote_volume": features.get("total_quote_volume"),
        "volatility_pct": features.get("volatility_pct"),
        "momentum_pct": features.get("momentum_pct"),
        "volume_expansion_ratio": features.get("volume_expansion_ratio"),
        "trend_pullback_alignment_status": features.get("trend_pullback_alignment_status"),
        "trend_pullback_alignment_score": features.get("trend_pullback_alignment_score"),
        "trend_pullback_alignment_reason": features.get("trend_pullback_alignment_reason"),
        "trend_exhaustion_status": features.get("trend_exhaustion_status"),
        "trend_exhaustion_score": features.get("trend_exhaustion_score"),
        "spread_bps": features.get("spread_bps"),
        "symbol_selection": symbol_selection,
        "symbol_selection_score": symbol_selection.get("symbol_selection_score"),
        "base_symbol_selection_score": symbol_selection.get("base_symbol_selection_score"),
        "correlation_cluster_id": symbol_selection.get("correlation_cluster_id"),
        "correlation_cluster_rank": symbol_selection.get("correlation_cluster_rank"),
        "correlation_cluster_status": symbol_selection.get("correlation_cluster_status"),
        "correlation_cluster_leader_symbol": symbol_selection.get("correlation_cluster_leader_symbol"),
        "correlation_max_peer_symbol": symbol_selection.get("correlation_max_peer_symbol"),
        "correlation_max_abs": symbol_selection.get("correlation_max_abs"),
        "correlation_penalty": symbol_selection.get("correlation_penalty"),
        "adaptive_top_n": symbol_selection.get("adaptive_top_n"),
        "rank_after_correlation": symbol_selection.get("rank_after_correlation"),
        "adaptive_top_n_filter_status": symbol_selection.get("adaptive_top_n_filter_status"),
        "eligible_after_correlation": symbol_selection.get("eligible_after_correlation"),
        "candidate_count": len(symbol_candidates),
        "paper_entry_review_candidate_count": paper_entry_review_count,
        "no_trade_candidate_count": len(symbol_candidates) - paper_entry_review_count,
        "no_trade_reasons": no_trade_reasons,
        "best_candidate_id": best_candidate.get("candidate_id"),
        "best_strategy_family": best_candidate.get("strategy_family"),
        "best_candidate_selection_score": best_candidate.get("candidate_selection_score"),
        "best_net_ev_after_cost_bps": best_candidate.get("net_ev_after_cost_bps"),
        "best_decision": best_candidate.get("decision"),
        "best_no_trade_reason": best_candidate.get("no_trade_reason"),
        "best_strategy_policy_reason": best_candidate.get("strategy_policy_reason"),
        "best_recent_failure_cooldown_status": best_candidate.get("recent_failure_cooldown_status", "CLEAR"),
        "best_recent_failure_feedback_kind": best_candidate.get("recent_failure_feedback_kind", "NONE"),
        "best_recent_failure_cooldown_cycles_remaining": int(
            best_candidate.get("recent_failure_cooldown_cycles_remaining", 0) or 0
        ),
        "best_recent_failure_reason_code": best_candidate.get("recent_failure_reason_code"),
        "best_recent_failure_penalty_bps": best_candidate.get("recent_failure_penalty_bps", "0"),
        "source_collection_report_hash": source_binding.get("source_collection_report_hash"),
        "source_public_market_data_hash": source_binding.get("source_public_market_data_hash"),
        "canonical_event_count": int(source_binding.get("canonical_event_count", 0) or 0),
        "acceptance_condition": "candidate_count>=1; scorecard is PAPER-only; validator recomputes best candidate and live flags.",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


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


def _validate_candidate_costs(
    candidate: dict[str, Any],
    *,
    features: dict[str, Any] | None = None,
    require_adaptive_cost_model: bool = True,
    require_current_strategy_entry_policy: bool = True,
) -> UpbitPaperRuntimeCycleValidationResult:
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
    if require_adaptive_cost_model:
        required.add("cost_model_formula")
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
    if require_adaptive_cost_model:
        if candidate.get("cost_model_source") != PAPER_RUNTIME_COST_MODEL_SOURCE:
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "candidate cost model source is not adaptive PAPER public L2 proxy model", "MEASUREMENT_MISSING")
        if candidate.get("cost_model_formula") != "fee_bps+adaptive_slippage_bps+spread_bps+public_depth_impact_bps+latency_penalty_bps":
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate cost model formula mismatch", "SCHEMA_IDENTITY_MISMATCH")
    elif candidate.get("cost_model_source") not in {PAPER_RUNTIME_COST_MODEL_SOURCE, "PAPER_RUNTIME_STATIC_COST_MODEL"}:
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "candidate cost model source is not recognized for PAPER recovery", "MEASUREMENT_MISSING")
    expected_edge = _decimal(candidate.get("expected_edge_bps"))
    expected_cost = _decimal(candidate.get("expected_cost_bps"))
    reported_net_ev = _decimal(candidate.get("net_ev_after_cost_bps"))
    signal_strength = _decimal(candidate.get("signal_strength"))
    symbol_score = _decimal(candidate.get("symbol_selection_score", "1"))
    cooldown_active = _candidate_recent_failure_cooldown_active(candidate)
    expected_candidate_selection_score = _candidate_selection_score_value(
        symbol_score=symbol_score,
        net_ev_bps=reported_net_ev,
        signal_strength=signal_strength,
    )
    symbol_selection = candidate.get("symbol_selection") if isinstance(candidate.get("symbol_selection"), dict) else {}
    correlation_filtered = symbol_selection.get("correlation_cluster_status") == "DIVERSIFICATION_FILTERED"
    adaptive_top_n_filtered = symbol_selection.get("adaptive_top_n_filter_status") == "OUTSIDE_ADAPTIVE_TOP_N"
    component_cost = sum((_decimal(breakdown[field]) for field in sorted(cost_fields)), Decimal("0"))
    if require_adaptive_cost_model and isinstance(features, dict):
        expected_breakdown = _paper_candidate_cost_breakdown(features)
        for field in sorted(cost_fields):
            if _decimal(breakdown.get(field)) != _decimal(expected_breakdown.get(field)):
                return UpbitPaperRuntimeCycleValidationResult(
                    "FAIL",
                    f"candidate adaptive cost component mismatch: {field}",
                    "SCHEMA_IDENTITY_MISMATCH",
                )
    if not _decimal_close(expected_cost, component_cost):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate expected cost does not equal fee+slippage+spread+impact+latency", "SCHEMA_IDENTITY_MISMATCH")
    if not _decimal_close(reported_net_ev, expected_edge - expected_cost):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate net EV after cost arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if signal_strength < 0 or signal_strength > 1:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate signal strength must be between 0 and 1", "SCHEMA_IDENTITY_MISMATCH")
    expected_grade = "A" if signal_strength >= Decimal("0.7") else "B" if signal_strength >= Decimal("0.55") else "C"
    if candidate.get("signal_grade") != expected_grade:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate signal grade does not match signal strength", "SCHEMA_IDENTITY_MISMATCH")
    if (
        require_current_strategy_entry_policy
        and candidate.get("strategy_entry_policy_id") != "UPBIT_KRW_SPOT_STRATEGY_ENTRY_ROUTER_V1"
    ):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate strategy entry policy id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if require_current_strategy_entry_policy and isinstance(features, dict) and candidate.get("regime") != features.get("regime"):
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "strategy candidate regime does not match runtime regime", "REGIME_MISMATCH")
    if require_current_strategy_entry_policy:
        if not isinstance(candidate.get("strategy_regime_allowed"), bool):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate strategy_regime_allowed must be boolean", "SCHEMA_IDENTITY_MISMATCH")
        strategy_regime_allowed = candidate.get("strategy_regime_allowed") is True
        candidate_market_state = str(candidate.get("market_state") or (features or {}).get("market_state") or candidate.get("regime"))
        if isinstance(features, dict) and candidate_market_state != str(features.get("market_state") or features.get("regime")):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate market_state does not match runtime feature snapshot", "SCHEMA_IDENTITY_MISMATCH")
        expected_entry_block_reason = _spot_long_entry_block_reason(
            regime=str(candidate.get("regime") or ""),
            market_state=candidate_market_state,
        )
        if "entry_block_reason" not in candidate:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate entry_block_reason missing", "SCHEMA_IDENTITY_MISMATCH")
        if candidate.get("entry_block_reason") != expected_entry_block_reason:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate entry block reason mismatch", "SCHEMA_IDENTITY_MISMATCH")
        expected_strategy_allowed, expected_strategy_reason = _strategy_entry_policy_evaluation(
            strategy_family=str(candidate.get("strategy_family") or ""),
            regime=str(candidate.get("regime") or ""),
            market_state=candidate_market_state,
            features=features or {},
            symbol_score=symbol_score,
        )
        if strategy_regime_allowed is not expected_strategy_allowed:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate strategy_regime_allowed does not match entry router", "SCHEMA_IDENTITY_MISMATCH")
        if candidate.get("strategy_policy_reason") != expected_strategy_reason:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate strategy_policy_reason does not match entry router", "SCHEMA_IDENTITY_MISMATCH")
        expected_quiet_policy = "VWAP_ONLY_DEEP_DISLOCATION" if candidate_market_state == "QUIET_RANGE" else "NOT_APPLICABLE"
        if candidate.get("quiet_range_entry_policy") != expected_quiet_policy:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "candidate quiet range policy marker mismatch", "SCHEMA_IDENTITY_MISMATCH")
    else:
        strategy_regime_allowed = (
            candidate.get("strategy_regime_allowed")
            if isinstance(candidate.get("strategy_regime_allowed"), bool)
            else candidate.get("regime") != "RISK_OFF"
        )
        candidate_market_state = str(candidate.get("market_state") or candidate.get("regime"))
        expected_entry_block_reason = _spot_long_entry_block_reason(
            regime=str(candidate.get("regime") or ""),
            market_state=candidate_market_state,
        )
    if expected_entry_block_reason and candidate.get("decision") != "NO_TRADE":
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "blocked spot market state cannot be paper entry review", "REGIME_MISMATCH")
    entry_threshold_passed = (
        reported_net_ev > MIN_ENTRY_NET_EV_BPS
        and signal_strength >= MIN_ENTRY_SIGNAL_STRENGTH
        and symbol_score >= MIN_SYMBOL_SELECTION_SCORE
        and expected_entry_block_reason is None
        and strategy_regime_allowed
        and not cooldown_active
        and not correlation_filtered
        and not adaptive_top_n_filtered
    )
    no_trade_reason = candidate.get("no_trade_reason")
    if candidate.get("decision") == "PAPER_ENTRY_REVIEW":
        if cooldown_active:
            return UpbitPaperRuntimeCycleValidationResult(
                "BLOCKED",
                "recent failure cooldown candidate cannot be paper entry review",
                "COOLDOWN",
            )
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
        if expected_entry_block_reason:
            expected_reason = "REGIME_MISMATCH"
        elif cooldown_active:
            expected_reason = "COOLDOWN"
        elif correlation_filtered:
            expected_reason = "CLUSTER_RISK"
        elif adaptive_top_n_filtered:
            expected_reason = "UNIVERSE_FILTERED"
        elif not strategy_regime_allowed:
            expected_reason = (
                "REGIME_MISMATCH"
                if str(candidate.get("strategy_policy_reason") or "").endswith("_BLOCK")
                else "STRATEGY_NOT_ELIGIBLE"
            )
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


def _decimal_close(left: Decimal, right: Decimal, tolerance: Decimal = Decimal("0.000001")) -> bool:
    return abs(left - right) <= tolerance


def _validate_paper_broker_fill(fill: dict[str, Any], *, features: dict[str, Any], expected_side: str) -> UpbitPaperRuntimeCycleValidationResult:
    required = {
        "fill_source",
        "broker_model_id",
        "order_lifecycle_state",
        "client_order_id",
        "symbol",
        "side",
        "order_type",
        "time_in_force",
        "maker_taker",
        "requested_notional",
        "requested_quantity",
        "filled_notional",
        "filled_quantity",
        "notional",
        "quantity",
        "fill_ratio",
        "partial_fill",
        "fill_price",
        "mark_price",
        "fee_rate",
        "fee_amount",
        "fee_asset",
        "slippage_bps",
        "adaptive_slippage_bps",
        "spread_bps",
        "market_impact_bps",
        "latency_penalty_bps",
        "latency_ms",
        "queue_ahead_notional_krw",
        "queue_fill_probability",
        "orderbook_proxy",
        "reservation_required",
        "reserved_cash",
        "reserved_quantity",
        "reservation_released",
        "reservation_release_amount",
        "reject_reason",
        "cancel_reason",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "order_adapter_called",
        "private_endpoint_called",
        "credential_load_attempted",
    }
    missing = sorted(required - set(fill))
    if missing:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", f"paper broker fill missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if fill.get("fill_source") != PAPER_BROKER_FILL_SOURCE or fill.get("broker_model_id") != PAPER_BROKER_MODEL_ID:
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper fill is not from adaptive PAPER broker model", "MEASUREMENT_MISSING")
    if fill.get("side") != expected_side:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper fill side mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if fill.get("order_lifecycle_state") not in {"FILLED", "PARTIALLY_FILLED"}:
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper fill lifecycle state is not accepted", "RECONCILIATION_REQUIRED")
    if fill.get("partial_fill") is not (fill.get("order_lifecycle_state") == "PARTIALLY_FILLED"):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper partial fill flag does not match lifecycle", "SCHEMA_IDENTITY_MISMATCH")
    if fill.get("order_type") != "MARKETABLE_LIMIT_PAPER" or fill.get("time_in_force") != "IOC_PAPER" or fill.get("maker_taker") != "TAKER":
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper fill order type, TIF, or maker/taker marker mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if (
        fill.get("live_order_ready")
        or fill.get("live_order_allowed")
        or fill.get("can_live_trade")
        or fill.get("scale_up_allowed")
        or fill.get("order_adapter_called")
        or fill.get("private_endpoint_called")
        or fill.get("credential_load_attempted")
    ):
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper broker fill attempted live/order/private access", "LIVE_FINAL_GUARD_FAILED")
    expected_proxy = _paper_orderbook_proxy(features)
    if fill.get("orderbook_proxy") != expected_proxy:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper broker orderbook proxy does not match runtime features", "SCHEMA_IDENTITY_MISMATCH")
    mark_price = _decimal(fill.get("mark_price"))
    fill_price = _decimal(fill.get("fill_price"))
    filled_notional = _decimal(fill.get("filled_notional"))
    filled_quantity = _decimal(fill.get("filled_quantity"))
    fee_rate = _decimal(fill.get("fee_rate"))
    fee_amount = _decimal(fill.get("fee_amount"))
    fill_ratio = _decimal(fill.get("fill_ratio"))
    if min(mark_price, fill_price, filled_notional, filled_quantity, fee_rate, fee_amount, fill_ratio) < 0 or fill_ratio <= 0 or fill_ratio > 1:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper fill numeric fields are outside closed ranges", "SCHEMA_IDENTITY_MISMATCH")
    if not _decimal_close(_decimal(fill.get("notional")), filled_notional) or not _decimal_close(_decimal(fill.get("quantity")), filled_quantity):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper fill notional/quantity aliases mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if not _decimal_close(filled_quantity * fill_price, filled_notional, tolerance=Decimal("0.01")):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper fill notional does not equal filled quantity times fill price", "SCHEMA_IDENTITY_MISMATCH")
    if not _decimal_close(fee_amount, filled_notional * fee_rate):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper fill fee accounting mismatch", "SCHEMA_IDENTITY_MISMATCH")
    adverse_bps = (
        (_decimal(fill.get("spread_bps")) / Decimal("2"))
        + _decimal(fill.get("adaptive_slippage_bps"))
        + _decimal(fill.get("market_impact_bps"))
        + _decimal(fill.get("latency_penalty_bps"))
    )
    if not _decimal_close(_decimal(fill.get("slippage_bps")), adverse_bps):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper fill slippage components do not sum to execution slippage", "SCHEMA_IDENTITY_MISMATCH")
    if expected_side == "BUY" and fill_price <= mark_price:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper BUY fill price must include adverse spread/slippage", "SCHEMA_IDENTITY_MISMATCH")
    if expected_side == "SELL" and fill_price >= mark_price:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper SELL fill price must include adverse spread/slippage", "SCHEMA_IDENTITY_MISMATCH")
    if fill.get("reservation_required") is not True or fill.get("reservation_released") is not True:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper broker reservation lifecycle did not release", "RECONCILIATION_REQUIRED")
    queue_probability = _decimal(fill.get("queue_fill_probability"))
    if queue_probability < 0 or queue_probability > 1:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper broker queue fill probability outside closed range", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperRuntimeCycleValidationResult("PASS", "adaptive PAPER broker fill is depth, fee, and live-guard consistent", None)


def _validate_position_rotation_context(
    lifecycle: dict[str, Any],
    *,
    selected: dict[str, Any],
    candidates_by_id: dict[str, dict[str, Any]],
    final_decision: str,
    require_current_strategy_exit_policy: bool = True,
) -> UpbitPaperRuntimeCycleValidationResult:
    evaluation = lifecycle.get("position_exit_evaluation")
    if not isinstance(evaluation, dict):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "position exit evaluation must be an object", "SCHEMA_IDENTITY_MISMATCH")
    required_exit_fields = (
        POSITION_ROTATION_EXIT_FIELDS
        if require_current_strategy_exit_policy
        else POSITION_ROTATION_EXIT_FIELDS - STRATEGY_EXIT_POLICY_EVALUATION_FIELDS
    )
    missing = sorted(required_exit_fields - set(evaluation))
    if missing:
        return UpbitPaperRuntimeCycleValidationResult(
            "FAIL",
            f"position exit evaluation missing executable exit fields: {missing}",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if _decimal(evaluation.get("quality_feedback_exit_max_positive_return_pct")) != ROTATION_EXIT_MAX_POSITIVE_RETURN_PCT:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "quality feedback exit weak-return threshold drifted", "SCHEMA_IDENTITY_MISMATCH")
    if evaluation.get("quality_feedback_exit_formula") != QUALITY_FEEDBACK_EXIT_FORMULA:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "quality feedback exit formula mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if require_current_strategy_exit_policy:
        if evaluation.get("strategy_exit_policy_id") != STRATEGY_EXIT_POLICY_ID:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy exit policy id mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if evaluation.get("strategy_family") not in {"PULLBACK_TREND_LONG", "VWAP_MEAN_REVERSION", "BREAKOUT_RETEST_LONG"}:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy exit family is not an executable strategy", "SCHEMA_IDENTITY_MISMATCH")
        if evaluation.get("exit_variation") not in {TREND_PULLBACK_EXIT_VARIATION, VWAP_REVERSION_EXIT_VARIATION, BREAKOUT_RETEST_EXIT_VARIATION}:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy exit variation is not supported", "SCHEMA_IDENTITY_MISMATCH")
        if not evaluation.get("strategy_exit_formula") or not evaluation.get("strategy_exit_acceptance_condition"):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy exit formula or acceptance condition missing", "SCHEMA_IDENTITY_MISMATCH")
        if evaluation.get("strategy_exit_condition_passed"):
            if evaluation.get("strategy_exit_action") != STRATEGY_EXIT_ACTION_FULL_EXIT:
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy exit action must be FULL_EXIT when condition passes", "SCHEMA_IDENTITY_MISMATCH")
            partial_exit_fill = (
                final_decision == "REDUCE_POSITION"
                and lifecycle.get("requested_position_decision") == "EXIT_POSITION"
                and lifecycle.get("execution_adjusted_position_decision_reason") == "PARTIAL_EXIT_FILL"
            )
            if (
                lifecycle.get("position_exit_reason_code") != evaluation.get("strategy_exit_reason_code")
                or (final_decision != "EXIT_POSITION" and not partial_exit_fill)
            ):
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy exit did not drive the PAPER exit decision", "SCHEMA_IDENTITY_MISMATCH")
        elif evaluation.get("strategy_exit_reason_code") != STRATEGY_EXIT_REASON_NONE or evaluation.get("strategy_exit_action") != STRATEGY_EXIT_ACTION_NONE:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy exit action is set when strategy condition did not pass", "SCHEMA_IDENTITY_MISMATCH")
    expected_quality_feedback_exit = (
        lifecycle.get("managed_position_symbol") is not None
        and selected.get("recent_failure_feedback_kind") == "PRELIMINARY_ROBUSTNESS_FAIL"
        and _candidate_recent_failure_cooldown_active(selected)
        and _decimal(evaluation.get("return_pct")) <= ROTATION_EXIT_MAX_POSITIVE_RETURN_PCT
    )
    if evaluation.get("quality_feedback_exit_condition_passed") is not expected_quality_feedback_exit:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "quality feedback exit condition does not match formula", "SCHEMA_IDENTITY_MISMATCH")
    if expected_quality_feedback_exit:
        if (
            evaluation.get("quality_feedback_exit_status") != "ACTIVE"
            or evaluation.get("quality_feedback_exit_feedback_kind") != selected.get("recent_failure_feedback_kind")
            or evaluation.get("quality_feedback_exit_reason_code") != selected.get("recent_failure_reason_code")
            or evaluation.get("quality_feedback_exit_action") != "FULL_EXIT"
        ):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "quality feedback exit action fields do not match formula", "SCHEMA_IDENTITY_MISMATCH")
        partial_exit_fill = (
            final_decision == "REDUCE_POSITION"
            and lifecycle.get("requested_position_decision") == "EXIT_POSITION"
            and lifecycle.get("execution_adjusted_position_decision_reason") == "PARTIAL_EXIT_FILL"
        )
        higher_priority_exit = (
            final_decision == "EXIT_POSITION"
            and lifecycle.get("position_exit_reason_code")
            in ROTATION_SUPERSEDED_BY_HIGHER_PRIORITY_EXIT_REASONS
            and lifecycle.get("position_exit_reason_code") != "COOLDOWN"
        )
        if not higher_priority_exit and (
            (final_decision != "EXIT_POSITION" and not partial_exit_fill)
            or lifecycle.get("position_exit_reason_code") != "COOLDOWN"
        ):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "quality feedback exit did not drive the PAPER exit decision", "SCHEMA_IDENTITY_MISMATCH")
    elif (
        evaluation.get("quality_feedback_exit_status") != "CLEAR"
        or evaluation.get("quality_feedback_exit_feedback_kind") != "NONE"
        or evaluation.get("quality_feedback_exit_reason_code") is not None
        or evaluation.get("quality_feedback_exit_action") != "NONE"
    ):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "quality feedback exit action is set when formula did not pass", "SCHEMA_IDENTITY_MISMATCH")
    if lifecycle.get("managed_position_symbol") is None:
        if evaluation.get("rotation_candidate_id") is not None or evaluation.get("rotation_condition_passed") or evaluation.get("rotation_action") != "NONE":
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation context cannot be active without a managed position", "SCHEMA_IDENTITY_MISMATCH")
        return UpbitPaperRuntimeCycleValidationResult("PASS", "position rotation context is inactive without a managed position", None)
    if evaluation.get("rotation_managed_candidate_id") not in {None, selected.get("candidate_id")}:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation managed candidate diverges from selected position candidate", "SCHEMA_IDENTITY_MISMATCH")
    if _decimal(evaluation.get("rotation_managed_net_ev_after_cost_bps")) != _decimal(selected.get("net_ev_after_cost_bps")):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation managed net EV does not match selected candidate", "SCHEMA_IDENTITY_MISMATCH")
    if _decimal(evaluation.get("rotation_managed_symbol_selection_score")) != _decimal(selected.get("symbol_selection_score")):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation managed symbol score does not match selected candidate", "SCHEMA_IDENTITY_MISMATCH")

    rotation_candidate_id = evaluation.get("rotation_candidate_id")
    if rotation_candidate_id is None:
        if evaluation.get("rotation_condition_passed") or evaluation.get("rotation_action") != "NONE":
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation action cannot pass without a rotation candidate", "SCHEMA_IDENTITY_MISMATCH")
        return UpbitPaperRuntimeCycleValidationResult("PASS", "position rotation context is internally consistent", None)
    if not isinstance(rotation_candidate_id, str) or rotation_candidate_id not in candidates_by_id:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation candidate id is not present in strategy candidates", "SCHEMA_IDENTITY_MISMATCH")
    rotation_candidate = candidates_by_id[rotation_candidate_id]
    if rotation_candidate.get("symbol") == selected.get("symbol"):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation candidate must be a different symbol", "SCHEMA_IDENTITY_MISMATCH")
    if evaluation.get("rotation_candidate_symbol") != rotation_candidate.get("symbol"):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation candidate symbol mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if evaluation.get("rotation_candidate_decision") != rotation_candidate.get("decision"):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation candidate decision mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if _decimal(evaluation.get("rotation_candidate_net_ev_after_cost_bps")) != _decimal(rotation_candidate.get("net_ev_after_cost_bps")):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation candidate net EV mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if _decimal(evaluation.get("rotation_candidate_selection_score")) != _decimal(rotation_candidate.get("symbol_selection_score")):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation candidate symbol score mismatch", "SCHEMA_IDENTITY_MISMATCH")

    expected_net_advantage = _decimal(rotation_candidate.get("net_ev_after_cost_bps")) - _decimal(selected.get("net_ev_after_cost_bps"))
    expected_score_advantage = _decimal(rotation_candidate.get("symbol_selection_score")) - _decimal(selected.get("symbol_selection_score"))
    if _decimal(evaluation.get("rotation_net_ev_advantage_bps")) != expected_net_advantage:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation net EV advantage formula mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if _decimal(evaluation.get("rotation_symbol_score_advantage")) != expected_score_advantage:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation symbol score advantage formula mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if _decimal(evaluation.get("rotation_threshold_bps")) != ROTATION_EXIT_MIN_NET_EV_ADVANTAGE_BPS:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation threshold drifted", "SCHEMA_IDENTITY_MISMATCH")
    if _decimal(evaluation.get("rotation_score_buffer_threshold")) != ROTATION_EXIT_MIN_SYMBOL_SCORE_BUFFER:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation score buffer threshold drifted", "SCHEMA_IDENTITY_MISMATCH")
    if _decimal(evaluation.get("rotation_max_positive_return_pct")) != ROTATION_EXIT_MAX_POSITIVE_RETURN_PCT:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation weak-return threshold drifted", "SCHEMA_IDENTITY_MISMATCH")

    managed_no_trade_reason = str(selected.get("no_trade_reason") or "")
    managed_is_weak_or_unqualified = (
        selected.get("decision") != "PAPER_ENTRY_REVIEW"
        or managed_no_trade_reason in ROTATION_EXIT_WEAK_NO_TRADE_REASONS
        or _decimal(evaluation.get("return_pct")) <= ROTATION_EXIT_MAX_POSITIVE_RETURN_PCT
    )
    expected_condition = (
        rotation_candidate.get("decision") == "PAPER_ENTRY_REVIEW"
        and expected_net_advantage >= ROTATION_EXIT_MIN_NET_EV_ADVANTAGE_BPS
        and expected_score_advantage >= ROTATION_EXIT_MIN_SYMBOL_SCORE_BUFFER
        and managed_is_weak_or_unqualified
    )
    if evaluation.get("rotation_condition_passed") is not expected_condition:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation condition does not match formula", "SCHEMA_IDENTITY_MISMATCH")
    if expected_condition:
        expected_reason = "REGIME_ROTATION_EXIT" if selected.get("regime") == "RISK_OFF" else "ROTATION_OPPORTUNITY_COST"
        if evaluation.get("rotation_action") != "FULL_EXIT" or evaluation.get("rotation_reason_code") != expected_reason:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation action or reason does not match formula", "SCHEMA_IDENTITY_MISMATCH")
        partial_exit_fill = (
            final_decision == "REDUCE_POSITION"
            and lifecycle.get("requested_position_decision") == "EXIT_POSITION"
            and lifecycle.get("execution_adjusted_position_decision_reason") == "PARTIAL_EXIT_FILL"
        )
        higher_priority_exit = (
            final_decision == "EXIT_POSITION"
            and lifecycle.get("position_exit_reason_code")
            in ROTATION_SUPERSEDED_BY_HIGHER_PRIORITY_EXIT_REASONS
        )
        higher_priority_partial_fill = (
            partial_exit_fill
            and lifecycle.get("position_exit_reason_code")
            in ROTATION_SUPERSEDED_BY_HIGHER_PRIORITY_EXIT_REASONS
        )
        if not higher_priority_exit and not higher_priority_partial_fill and (
            (final_decision != "EXIT_POSITION" and not partial_exit_fill)
            or lifecycle.get("position_exit_reason_code") != expected_reason
        ):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation exit did not drive the PAPER exit decision", "SCHEMA_IDENTITY_MISMATCH")
    elif evaluation.get("rotation_action") != "NONE" or evaluation.get("rotation_reason_code") is not None:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "rotation action is set when formula did not pass", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperRuntimeCycleValidationResult("PASS", "position rotation context is internally consistent", None)


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
    current_paper_portfolio_snapshot: dict[str, Any] | None = None,
    recent_failure_feedback: list[dict[str, Any]] | None = None,
    paper_scope_focus: dict[str, Any] | None = None,
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
    valid_symbol_rows: list[tuple[int, str, dict[str, Any]]] = []
    symbol_selection_universe: list[dict[str, Any]] = []
    symbol_evidence_scorecards: list[dict[str, Any]] = []
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
        feature_snapshots_by_symbol[candidate_symbol] = candidate_features
        market_data_by_symbol[candidate_symbol] = candidate_market_data
        valid_symbol_rows.append((index, candidate_symbol, candidate_features))

    symbol_selection_by_symbol = _symbol_selection_scores_for_universe(feature_snapshots_by_symbol)
    for index, candidate_symbol, candidate_features in valid_symbol_rows:
        symbol_selection = symbol_selection_by_symbol[candidate_symbol]
        entry_block_reason = _spot_long_entry_block_reason(
            regime=str(candidate_features["regime"]),
            market_state=str(candidate_features.get("market_state") or candidate_features["regime"]),
        )
        symbol_candidates = _build_candidates(
            candidate_symbol,
            candidate_features,
            edge_profile=edge_profile,
            symbol_selection=symbol_selection,
            recent_failure_feedback=recent_failure_feedback,
        )
        symbol_selection_universe.append(
            {
                "rank_input_order": index,
                "symbol": candidate_symbol,
                "regime": candidate_features["regime"],
                "market_state": candidate_features.get("market_state"),
                "entry_block_reason": entry_block_reason,
                "quiet_range_status": candidate_features.get("quiet_range_status"),
                "volatility_expansion_status": candidate_features.get("volatility_expansion_status"),
                **symbol_selection,
                "eligible_for_entry_candidate": _decimal(symbol_selection["symbol_selection_score"]) >= MIN_SYMBOL_SELECTION_SCORE
                and entry_block_reason is None
                and symbol_selection.get("eligible_after_correlation") is True,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
        candidates.extend(symbol_candidates)
        symbol_evidence_scorecards.append(
            _build_symbol_evidence_scorecard(
                cycle_id=cycle_id,
                rank_input_order=index,
                symbol=candidate_symbol,
                features=candidate_features,
                symbol_selection=symbol_selection,
                symbol_candidates=symbol_candidates,
                source_binding=source_by_symbol.get(candidate_symbol),
            )
        )
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
            "return_signature": [],
            "return_signature_formula": "close_to_close_return_pct over the runtime candle window, used only for PAPER symbol correlation clustering",
            "total_quote_volume": "0",
            "volume_expansion_ratio": "0",
            "vwap_distance_pct": "0",
            "range_breakout_pct": "0",
            "spread_bps": "0",
            "liquidity_status": "BLOCKED",
            "volatility_status": "BLOCKED",
            "market_state": "RISK_OFF",
            "quiet_range_status": "CLEAR",
            "volatility_expansion_status": "CLEAR",
            "regime_detail_formula": (
                "Upbit KRW spot is long-only: DATA_BAD, PANIC, DOWNTREND/RISK_OFF, and UNCERTAIN block new entries; "
                "QUIET_RANGE blocks trend/breakout and permits only limited VWAP range candidates when abs(vwap_distance)>=0.55pct "
                "and symbol_score>=0.60; VOLATILITY_EXPANSION enables breakout candidates when volatility>=2.50pct, "
                "volume_expansion>=1.20, and range_breakout>=0.03pct"
            ),
        }
        candidates = _build_candidates(
            symbol,
            feature_snapshots_by_symbol[symbol],
            edge_profile="NEGATIVE",
            symbol_selection=_symbol_selection_scores_for_universe(feature_snapshots_by_symbol)[symbol],
            recent_failure_feedback=recent_failure_feedback,
        )
        fallback_symbol_selection = _symbol_selection_scores_for_universe(feature_snapshots_by_symbol)[symbol]
        symbol_selection_universe = [
            {
                "rank_input_order": 1,
                "symbol": symbol,
                "regime": feature_snapshots_by_symbol[symbol]["regime"],
                "market_state": feature_snapshots_by_symbol[symbol].get("market_state"),
                "entry_block_reason": "RISK_OFF_BLOCK",
                "quiet_range_status": feature_snapshots_by_symbol[symbol].get("quiet_range_status"),
                "volatility_expansion_status": feature_snapshots_by_symbol[symbol].get("volatility_expansion_status"),
                **fallback_symbol_selection,
                "eligible_for_entry_candidate": False,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        ]
        symbol_evidence_scorecards = [
            _build_symbol_evidence_scorecard(
                cycle_id=cycle_id,
                rank_input_order=1,
                symbol=symbol,
                features=feature_snapshots_by_symbol[symbol],
                symbol_selection=fallback_symbol_selection,
                symbol_candidates=candidates,
                source_binding=None,
            )
        ]
    current_portfolio = _cycle_bound_current_portfolio_snapshot(
        current_paper_portfolio_snapshot,
        cycle_id=cycle_id,
    )
    current_open_positions = _open_long_positions(current_portfolio)
    unpriced_position_symbols = sorted(
        str(position.get("symbol"))
        for position in current_open_positions
        if str(position.get("symbol")) not in feature_snapshots_by_symbol
    )
    if unpriced_position_symbols:
        blockers.append(
            _blocker(
                "MEASUREMENT_MISSING",
                f"open PAPER position symbols are missing public mark data: {', '.join(unpriced_position_symbols)}",
            )
        )
    managed_position = _select_managed_position(
        current_portfolio,
        feature_snapshots_by_symbol=feature_snapshots_by_symbol,
    )
    if managed_position is not None:
        managed_symbol = str(managed_position["symbol"])
        managed_candidates = [candidate for candidate in candidates if candidate.get("symbol") == managed_symbol]
        selected = max(managed_candidates or candidates, key=_candidate_rank_key)
        paper_scope_continuity = _paper_scope_continuity_decision(
            candidates=managed_candidates or candidates,
            paper_scope_focus=paper_scope_focus,
            managed_position_symbol=managed_symbol,
        )[1]
        rotation_candidate = _best_rotation_alternative_candidate(candidates, managed_symbol=managed_symbol)
    else:
        selected, paper_scope_continuity = _paper_scope_continuity_decision(
            candidates=candidates,
            paper_scope_focus=paper_scope_focus,
            managed_position_symbol=None,
        )
        rotation_candidate = None
    selected_symbol = str(selected["symbol"])
    market_data = market_data_by_symbol[selected_symbol]
    features = feature_snapshots_by_symbol[selected_symbol]
    selected_symbol_evidence_scorecard = next(
        (scorecard for scorecard in symbol_evidence_scorecards if scorecard.get("symbol") == selected_symbol),
        {},
    )
    symbol_selection_policy = _symbol_selection_policy(
        runtime_input_role=runtime_input_role,
        symbol_count=len(symbol_selection_universe),
    )
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
    risk_new_entry_blockers = [
        risk_blocker
        for risk_blocker in risk_state.get("blockers", [])
        if isinstance(risk_blocker, dict)
    ]
    # A new-entry veto must not suppress existing PAPER position exit/hold management.
    if risk_state.get("new_entry_allowed") is not True and managed_position is None:
        blockers.extend(risk_new_entry_blockers)
        final_decision = "BLOCKED"
        no_trade_reasons = order_blocker_codes(blockers)
        entry_reasons = []

    exit_strategy_candidate, exit_strategy_context = _position_entry_strategy_candidate(
        position=managed_position,
        candidates=candidates,
        fallback_candidate=selected,
    )
    exit_plan = _build_runtime_exit_plan(
        selected_candidate=exit_strategy_candidate,
        features=features,
        entry_price_override=managed_position.get("average_entry_price") if isinstance(managed_position, dict) else None,
    )
    position_exit_evaluation = _evaluate_existing_position_exit(
        position=managed_position,
        features=features,
        exit_plan=exit_plan,
        managed_candidate=exit_strategy_candidate if isinstance(managed_position, dict) else None,
        rotation_candidate=rotation_candidate,
    )

    sizing = build_position_sizing_decision(
        sizing_decision_id=f"{cycle_id}-sizing",
        strategy_unit_id=selected["candidate_id"],
        session_id=session_id,
        inputs=sizing_inputs,
    )
    sizing_result = validate_position_sizing_decision(sizing)
    if managed_position is None and (sizing_result.status != "PASS" or sizing.get("sizing_status") != "PASS"):
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

    if managed_position is not None and not blockers:
        position_decision = position_exit_evaluation.get("final_decision")
        if position_decision in {"EXIT_POSITION", "REDUCE_POSITION"}:
            final_decision = str(position_decision)
            no_trade_reasons = [str(position_exit_evaluation.get("reason_code") or "POSITION_EXIT")]
            entry_reasons = []
        else:
            final_decision = "HOLD_POSITION"
            hold_reasons = []
            current_exposure = _decimal(sizing.get("inputs", {}).get("current_exposure", "0"))
            exposure_cap = _decimal(sizing.get("caps", {}).get("exposure_cap", "0"))
            if current_exposure > 0 and exposure_cap < UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL:
                hold_reasons.append("POSITION_LIMIT")
            hold_reasons.extend(["POSITION_ALREADY_OPEN", str(position_exit_evaluation.get("reason_code") or "EXIT_CONDITION_NOT_MET")])
            no_trade_reasons = hold_reasons
            selected_no_trade_reason = selected.get("no_trade_reason")
            if selected_no_trade_reason and selected_no_trade_reason not in no_trade_reasons:
                no_trade_reasons.append(str(selected_no_trade_reason))
            entry_reasons = []

    if final_decision == "ENTER_LONG":
        selected_notional = _decimal(sizing["selected_notional"])
        entry_cash_required = selected_notional * (Decimal("1") + PAPER_ENTRY_FEE_RATE)
        if selected_notional < UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL:
            current_exposure = _decimal(sizing.get("inputs", {}).get("current_exposure", "0"))
            exposure_cap = _decimal(sizing.get("caps", {}).get("exposure_cap", "0"))
            if current_exposure > 0 and exposure_cap < UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL:
                final_decision = "HOLD_POSITION"
                no_trade_reasons = ["POSITION_LIMIT"]
                entry_reasons = []
            else:
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

    broker_execution: dict[str, Any] | None = None
    execution_adjusted_position_decision_reason: str | None = None
    if final_decision == "ENTER_LONG":
        requested_notional = _decimal(sizing["selected_notional"])
        mark_price = _decimal(features["last_price"])
        requested_quantity = Decimal("0") if mark_price <= 0 else requested_notional / mark_price
        broker_execution = _simulate_paper_broker_execution(
            cycle_id=cycle_id,
            symbol=selected_symbol,
            side="BUY",
            requested_notional=requested_notional,
            requested_quantity=requested_quantity,
            mark_price=mark_price,
            features=features,
            fee_rate=PAPER_ENTRY_FEE_RATE,
        )
        accepted_state = broker_execution.get("order_lifecycle_state") in {"FILLED", "PARTIALLY_FILLED"}
        if not accepted_state or _decimal(broker_execution.get("filled_notional")) < UPBIT_KRW_PAPER_MIN_ENTRY_NOTIONAL:
            blockers.append(
                _blocker(
                    "MEASUREMENT_MISSING",
                    (
                        "adaptive PAPER broker could not produce an acceptable entry fill "
                        f"(state={broker_execution.get('order_lifecycle_state')}, "
                        f"filled_notional={broker_execution.get('filled_notional')})"
                    ),
                )
            )
            final_decision = "BLOCKED"
            no_trade_reasons = order_blocker_codes(blockers)
            entry_reasons = []
    elif final_decision in {"EXIT_POSITION", "REDUCE_POSITION"} and isinstance(managed_position, dict):
        sell_quantity = _decimal(position_exit_evaluation.get("sell_quantity"))
        mark_price = _decimal(features["last_price"])
        broker_execution = _simulate_paper_broker_execution(
            cycle_id=cycle_id,
            symbol=selected_symbol,
            side="SELL",
            requested_notional=sell_quantity * mark_price,
            requested_quantity=sell_quantity,
            mark_price=mark_price,
            features=features,
            fee_rate=PAPER_EXIT_FEE_RATE,
        )
        if broker_execution.get("order_lifecycle_state") not in {"FILLED", "PARTIALLY_FILLED"} or _decimal(
            broker_execution.get("filled_quantity")
        ) <= 0:
            blockers.append(
                _blocker(
                    "MEASUREMENT_MISSING",
                    (
                        "adaptive PAPER broker could not produce an acceptable exit fill "
                        f"(state={broker_execution.get('order_lifecycle_state')})"
                    ),
                )
            )
            final_decision = "BLOCKED"
            no_trade_reasons = order_blocker_codes(blockers)
            entry_reasons = []
        elif final_decision == "EXIT_POSITION" and _decimal(broker_execution.get("filled_quantity")) < sell_quantity:
            final_decision = "REDUCE_POSITION"
            execution_adjusted_position_decision_reason = "PARTIAL_EXIT_FILL"
            no_trade_reasons = [
                "PARTIAL_EXIT_FILL",
                str(position_exit_evaluation.get("reason_code") or "POSITION_EXIT"),
            ]
            entry_reasons = []

    current_open_position_count = int(current_portfolio.get("open_position_count", 0)) if current_portfolio else 0
    current_ledger_head_hash = current_portfolio.get("source_paper_ledger_head_hash") if current_portfolio else None

    position_management_decision = {
        "source": "PAPER_RUNTIME_POSITION_LIFECYCLE_DECISION",
        "selected_symbol": selected_symbol,
        "selected_candidate_id": selected.get("candidate_id"),
        "entry_strategy_context_status": exit_strategy_context.get("entry_strategy_context_status"),
        "entry_strategy_context_source": exit_strategy_context.get("entry_strategy_context_source"),
        "entry_candidate_id": exit_strategy_context.get("entry_candidate_id"),
        "entry_strategy_family": exit_strategy_context.get("entry_strategy_family"),
        "entry_strategy_exit_variation": exit_strategy_context.get("entry_strategy_exit_variation"),
        "entry_strategy_current_candidate_match": exit_strategy_context.get("entry_strategy_current_candidate_match"),
        "entry_strategy_fallback_used": exit_strategy_context.get("entry_strategy_fallback_used"),
        "risk_state": risk_state.get("risk_state"),
        "decision": (
            "ENTER_LONG_WITH_ATTACHED_EXIT_PLAN"
            if final_decision == "ENTER_LONG"
            else "EXIT_POSITION_WITH_PAPER_SELL_FILL"
            if final_decision == "EXIT_POSITION"
            else "REDUCE_POSITION_WITH_PAPER_SELL_FILL"
            if final_decision == "REDUCE_POSITION"
            else "HOLD_EXISTING_POSITION_NO_NEW_ENTRY"
            if final_decision == "HOLD_POSITION" or current_open_position_count > 0
            else "ENTRY_BLOCKED_NO_POSITION"
            if final_decision == "BLOCKED"
            else "NO_ENTRY_NO_POSITION"
        ),
        "exit_plan_status": (
            "ARMED_PAPER_ONLY_AFTER_FILL"
            if final_decision == "ENTER_LONG"
            else "TRIGGERED_PAPER_ONLY_SELL"
            if final_decision in {"EXIT_POSITION", "REDUCE_POSITION"}
            else "MONITORING_EXISTING_POSITION"
            if final_decision == "HOLD_POSITION" or current_open_position_count > 0
            else "NOT_ACTIVE_NO_POSITION"
        ),
        "managed_position_symbol": managed_position.get("symbol") if isinstance(managed_position, dict) else None,
        "managed_position_quantity": managed_position.get("quantity") if isinstance(managed_position, dict) else None,
        "position_exit_reason_code": position_exit_evaluation.get("reason_code"),
        "position_exit_evaluation": position_exit_evaluation,
        "strategy_exit_policy_id": exit_plan.get("strategy_exit_policy_id"),
        "strategy_exit_variation": exit_plan.get("exit_variation"),
        "strategy_exit_reason_code": position_exit_evaluation.get("strategy_exit_reason_code"),
        "strategy_exit_condition_passed": position_exit_evaluation.get("strategy_exit_condition_passed"),
        "requested_position_decision": position_exit_evaluation.get("final_decision"),
        "execution_adjusted_position_decision_reason": execution_adjusted_position_decision_reason,
        "sell_quantity": position_exit_evaluation.get("sell_quantity"),
        "sell_notional": position_exit_evaluation.get("sell_notional"),
        "exit_fee_rate": _decimal_text(PAPER_EXIT_FEE_RATE),
        "exit_slippage_bps": _paper_candidate_cost_breakdown(features)["slippage_bps"],
        "paper_broker_model_id": PAPER_BROKER_MODEL_ID,
        "paper_broker_cost_model_source": PAPER_RUNTIME_COST_MODEL_SOURCE,
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
    ledger_head_hash: str | None = str(current_ledger_head_hash) if current_ledger_head_hash else None
    if final_decision == "ENTER_LONG" and isinstance(broker_execution, dict):
        notional = _decimal(broker_execution["filled_notional"])
        mark_price = _decimal(broker_execution["mark_price"])
        fill_price = _decimal(broker_execution["fill_price"])
        quantity = _decimal(broker_execution["filled_quantity"])
        fee_amount = _decimal(broker_execution["fee_amount"])
        client_order_id = str(broker_execution["client_order_id"])
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
        fill = dict(broker_execution)
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
            entry_strategy_context=_build_entry_strategy_context(
                cycle_id=cycle_id,
                selected_candidate=selected,
                exit_plan=exit_plan,
            ),
        )
    elif final_decision in {"EXIT_POSITION", "REDUCE_POSITION"} and isinstance(managed_position, dict) and isinstance(broker_execution, dict):
        sell_quantity = _decimal(broker_execution["filled_quantity"])
        mark_price = _decimal(broker_execution["mark_price"])
        fill_price = _decimal(broker_execution["fill_price"])
        fee_amount = _decimal(broker_execution["fee_amount"])
        client_order_id = str(broker_execution["client_order_id"])
        ledger_events = build_upbit_paper_fill_chain(
            session_id=session_id,
            symbol=selected_symbol,
            intent_id=f"{cycle_id}-exit-intent",
            client_order_id=client_order_id,
            side="SELL",
            quantity=_decimal_text(sell_quantity),
            price=_decimal_text(fill_price),
            fee_amount=_decimal_text(fee_amount),
        )
        ledger_head_hash = ledger_events[-1]["event_hash"]
        fill = dict(broker_execution)
        fill["position_exit_reason_code"] = position_exit_evaluation.get("reason_code")
        portfolio = build_paper_portfolio_snapshot_after_sell_fill(
            current_snapshot=current_portfolio,
            session_id=session_id,
            symbol=selected_symbol,
            quantity=sell_quantity,
            fill_price=fill_price,
            fee_amount=fee_amount,
            source_runtime_cycle_id=cycle_id,
            source_paper_ledger_head_hash=ledger_head_hash,
        )
    else:
        portfolio = current_portfolio or build_initial_paper_portfolio_snapshot(
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
        "symbol_selection_policy": symbol_selection_policy,
        "symbol_evidence_scorecards": symbol_evidence_scorecards,
        "symbol_evidence_scorecard_count": len(symbol_evidence_scorecards),
        "selected_symbol_evidence_scorecard": selected_symbol_evidence_scorecard,
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
        "paper_scope_continuity_decision": paper_scope_continuity,
        "strategy_regime_cost_linkage": strategy_regime_cost_linkage,
        "risk_state": risk_state,
        "sizing_decision": sizing,
        "exit_plan": exit_plan,
        "position_management_decision": position_management_decision,
        "paper_broker_execution": broker_execution,
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
    require_symbol_evidence_scorecard_fields: bool = True,
    require_adaptive_candidate_cost_model: bool = True,
    require_position_rotation_fields: bool = True,
    require_current_symbol_selection_policy: bool = True,
    require_current_feature_snapshot_projection: bool = True,
    require_paper_scope_continuity_decision: bool = True,
    require_current_strategy_entry_policy: bool = True,
    require_current_strategy_exit_policy: bool = True,
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
        "requested_symbol",
        "symbol_universe",
        "symbol_selection_universe",
        "selected_symbol",
        "runtime_input_role",
        "source_collection_report_hash",
        "source_public_market_data_hash",
        "source_collection_hashes_by_symbol",
        "canonical_event_count",
        "runtime_public_market_data_hash",
        "market_data_source",
        "public_market_data",
        "public_market_data_by_symbol",
        "feature_snapshot",
        "feature_snapshots_by_symbol",
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
    if require_paper_scope_continuity_decision:
        required.add("paper_scope_continuity_decision")
    if require_symbol_evidence_scorecard_fields:
        required.update(
            {
                "symbol_selection_policy",
                "symbol_evidence_scorecards",
                "symbol_evidence_scorecard_count",
                "selected_symbol_evidence_scorecard",
            }
        )
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
    symbol_universe = report.get("symbol_universe")
    symbol_selection_universe = report.get("symbol_selection_universe")
    if not isinstance(symbol_universe, list) or not all(isinstance(item, str) and item for item in symbol_universe):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper runtime requires a string symbol universe", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(symbol_selection_universe, list) or len(symbol_selection_universe) != len(symbol_universe):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol selection universe must match symbol universe", "SCHEMA_IDENTITY_MISMATCH")
    if [str(item.get("symbol")) for item in symbol_selection_universe if isinstance(item, dict)] != symbol_universe:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol selection universe order must bind to symbol universe", "SCHEMA_IDENTITY_MISMATCH")
    expected_policy = _symbol_selection_policy(
        runtime_input_role=str(report.get("runtime_input_role")),
        symbol_count=len(symbol_universe),
    )
    if require_symbol_evidence_scorecard_fields:
        reported_policy = report.get("symbol_selection_policy")
        if reported_policy != expected_policy:
            if require_current_symbol_selection_policy:
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol selection policy does not match runtime formula", "SCHEMA_IDENTITY_MISMATCH")
            if not isinstance(reported_policy, dict):
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol selection policy must be an object", "SCHEMA_IDENTITY_MISMATCH")
            if (
                reported_policy.get("symbol_scope") != expected_policy.get("symbol_scope")
                or reported_policy.get("evaluated_symbol_count") != expected_policy.get("evaluated_symbol_count")
                or reported_policy.get("runtime_input_role") != expected_policy.get("runtime_input_role")
            ):
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "legacy symbol selection policy scope mismatch", "SCHEMA_IDENTITY_MISMATCH")
            if (
                reported_policy.get("live_order_ready")
                or reported_policy.get("live_order_allowed")
                or reported_policy.get("can_live_trade")
                or reported_policy.get("scale_up_allowed")
            ):
                return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "legacy symbol selection policy attempted live or scale permission", "LIVE_FINAL_GUARD_FAILED")
        if (
            expected_policy.get("live_order_ready")
            or expected_policy.get("live_order_allowed")
            or expected_policy.get("can_live_trade")
            or expected_policy.get("scale_up_allowed")
        ):
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "symbol selection policy attempted live or scale permission", "LIVE_FINAL_GUARD_FAILED")

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
    reported_features = report.get("feature_snapshot")
    if require_current_feature_snapshot_projection:
        if reported_features != expected_features:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "feature snapshot does not match public market data", "SCHEMA_IDENTITY_MISMATCH")
        expected_feature_hash = _hash_payload(expected_features)
        if report.get("feature_snapshot_hash") != expected_feature_hash:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "feature snapshot hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    else:
        if not _matches_legacy_feature_snapshot_projection(reported_features, expected_features):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "legacy feature snapshot projection scope mismatch", "SCHEMA_IDENTITY_MISMATCH")
        expected_feature_hash = _hash_payload(reported_features)
        if report.get("feature_snapshot_hash") != expected_feature_hash:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "legacy feature snapshot hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
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
            expected_universe_features = _feature_snapshot(universe_data)
            reported_universe_features = feature_snapshots_by_symbol.get(universe_symbol)
            if require_current_feature_snapshot_projection:
                if reported_universe_features != expected_universe_features:
                    return UpbitPaperRuntimeCycleValidationResult("FAIL", "multi-symbol feature snapshot mismatch", "SCHEMA_IDENTITY_MISMATCH")
            elif not _matches_legacy_feature_snapshot_projection(reported_universe_features, expected_universe_features):
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "legacy multi-symbol feature snapshot scope mismatch", "SCHEMA_IDENTITY_MISMATCH")
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
        cost_result = _validate_candidate_costs(
            candidate,
            features=candidate_features,
            require_adaptive_cost_model=require_adaptive_candidate_cost_model,
            require_current_strategy_entry_policy=require_current_strategy_entry_policy,
        )
        if cost_result.status != "PASS":
            return cost_result
        if candidate.get("regime") != candidate_features.get("regime"):
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "strategy candidate regime does not match runtime regime", "REGIME_MISMATCH")
        if _decimal(candidate.get("cost_breakdown_bps", {}).get("spread_bps")) != _decimal(candidate_features.get("spread_bps")):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "strategy candidate spread cost is not bound to feature spread", "SCHEMA_IDENTITY_MISMATCH")
        candidates_by_id[candidate_id] = candidate
    source_by_symbol = report.get("source_collection_hashes_by_symbol")
    if not isinstance(source_by_symbol, dict):
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "source collection hashes by symbol must be an object", "SCHEMA_IDENTITY_MISMATCH")
    if require_symbol_evidence_scorecard_fields:
        raw_scorecards = report.get("symbol_evidence_scorecards")
        if not isinstance(raw_scorecards, list):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol evidence scorecards must be a list", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("symbol_evidence_scorecard_count") != len(raw_scorecards):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol evidence scorecard count mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if len(raw_scorecards) != len(symbol_universe):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "each symbol requires one symbol evidence scorecard", "SCHEMA_IDENTITY_MISMATCH")
        scorecards_by_symbol: dict[str, dict[str, Any]] = {}
        for scorecard in raw_scorecards:
            if not isinstance(scorecard, dict):
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol evidence scorecard must be an object", "SCHEMA_IDENTITY_MISMATCH")
            scorecard_symbol = scorecard.get("symbol")
            if not isinstance(scorecard_symbol, str) or scorecard_symbol not in symbol_universe:
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol evidence scorecard symbol is outside universe", "SCHEMA_IDENTITY_MISMATCH")
            if scorecard_symbol in scorecards_by_symbol:
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "duplicate symbol evidence scorecard", "SCHEMA_IDENTITY_MISMATCH")
            if (
                scorecard.get("live_order_ready")
                or scorecard.get("live_order_allowed")
                or scorecard.get("can_live_trade")
                or scorecard.get("scale_up_allowed")
            ):
                return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "symbol evidence scorecard attempted live or scale permission", "LIVE_FINAL_GUARD_FAILED")
            scorecards_by_symbol[scorecard_symbol] = scorecard
        selection_by_symbol = {
            str(item.get("symbol")): item
            for item in symbol_selection_universe
            if isinstance(item, dict) and isinstance(item.get("symbol"), str)
        }
        expected_symbol_selection_by_symbol = _symbol_selection_scores_for_universe(feature_snapshots_by_symbol)
        for universe_symbol in symbol_universe:
            symbol_candidates = [candidate for candidate in candidates if candidate.get("symbol") == universe_symbol]
            if not symbol_candidates:
                return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "symbol evidence scorecard missing strategy candidates", "MEASUREMENT_MISSING")
            symbol_features = feature_snapshots_by_symbol[universe_symbol]
            try:
                rank_input_order = int(selection_by_symbol[universe_symbol].get("rank_input_order"))
            except (KeyError, TypeError, ValueError):
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol selection rank input order is invalid", "SCHEMA_IDENTITY_MISMATCH")
            expected_selection = expected_symbol_selection_by_symbol[universe_symbol]
            expected_entry_block_reason = _spot_long_entry_block_reason(
                regime=str(symbol_features["regime"]),
                market_state=str(symbol_features.get("market_state") or symbol_features["regime"]),
            )
            expected_selection_entry = {
                "rank_input_order": rank_input_order,
                "symbol": universe_symbol,
                "regime": symbol_features["regime"],
                "market_state": symbol_features.get("market_state"),
                "entry_block_reason": expected_entry_block_reason,
                "quiet_range_status": symbol_features.get("quiet_range_status"),
                "volatility_expansion_status": symbol_features.get("volatility_expansion_status"),
                **expected_selection,
                "eligible_for_entry_candidate": _decimal(expected_selection["symbol_selection_score"]) >= MIN_SYMBOL_SELECTION_SCORE
                and expected_entry_block_reason is None
                and expected_selection.get("eligible_after_correlation") is True,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
            if require_current_symbol_selection_policy and selection_by_symbol[universe_symbol] != expected_selection_entry:
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol selection universe entry does not match runtime formula", "SCHEMA_IDENTITY_MISMATCH")
            expected_scorecard = _build_symbol_evidence_scorecard(
                cycle_id=str(report["cycle_id"]),
                rank_input_order=rank_input_order,
                symbol=universe_symbol,
                features=symbol_features,
                symbol_selection=expected_selection,
                symbol_candidates=symbol_candidates,
                source_binding=source_by_symbol.get(universe_symbol) if isinstance(source_by_symbol.get(universe_symbol), dict) else None,
            )
            if scorecards_by_symbol.get(universe_symbol) != expected_scorecard:
                return UpbitPaperRuntimeCycleValidationResult("FAIL", "symbol evidence scorecard does not match runtime symbol candidates", "SCHEMA_IDENTITY_MISMATCH")
        selected_symbol_scorecard = report.get("selected_symbol_evidence_scorecard")
        if not isinstance(selected_symbol_scorecard, dict) or selected_symbol_scorecard != scorecards_by_symbol.get(report.get("symbol")):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "selected symbol evidence scorecard must match selected runtime symbol", "SCHEMA_IDENTITY_MISMATCH")
    selected_id = selected.get("candidate_id")
    if selected_id not in candidates_by_id:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "selected candidate is not present in strategy candidates", "SCHEMA_IDENTITY_MISMATCH")
    if selected != candidates_by_id[selected_id]:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "selected candidate diverges from candidate list", "SCHEMA_IDENTITY_MISMATCH")
    expected_candidate_pool = list(candidates_by_id.values())
    lifecycle_preview = report.get("position_management_decision")
    managed_position_symbol = (
        lifecycle_preview.get("managed_position_symbol")
        if isinstance(lifecycle_preview, dict) and isinstance(lifecycle_preview.get("managed_position_symbol"), str)
        else None
    )
    if final_decision in {"EXIT_POSITION", "REDUCE_POSITION", "HOLD_POSITION"} and managed_position_symbol:
        managed_pool = [candidate for candidate in expected_candidate_pool if candidate.get("symbol") == managed_position_symbol]
        if managed_pool:
            expected_candidate_pool = managed_pool
    expected_focus = None
    continuity = report.get("paper_scope_continuity_decision")
    if require_paper_scope_continuity_decision:
        if not isinstance(continuity, dict):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper scope continuity decision must be an object", "SCHEMA_IDENTITY_MISMATCH")
        if (
            continuity.get("live_order_ready")
            or continuity.get("live_order_allowed")
            or continuity.get("can_live_trade")
            or continuity.get("scale_up_allowed")
        ):
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper scope continuity attempted live or scale permission", "LIVE_FINAL_GUARD_FAILED")
        if continuity.get("requested") is True:
            expected_focus = {
                "candidate_id": continuity.get("requested_candidate_id"),
                "symbol": continuity.get("requested_symbol"),
                "strategy_id": continuity.get("requested_strategy_id"),
                "parameter_hash": continuity.get("requested_parameter_hash"),
                "sample_deficit": 1,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
    elif isinstance(continuity, dict) and (
        continuity.get("live_order_ready")
        or continuity.get("live_order_allowed")
        or continuity.get("can_live_trade")
        or continuity.get("scale_up_allowed")
    ):
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "legacy paper scope continuity attempted live or scale permission", "LIVE_FINAL_GUARD_FAILED")
    expected_selected_candidate, expected_continuity = _paper_scope_continuity_decision(
        candidates=expected_candidate_pool,
        paper_scope_focus=expected_focus,
        managed_position_symbol=managed_position_symbol,
    )
    if require_paper_scope_continuity_decision and continuity != expected_continuity:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper scope continuity decision mismatch", "SCHEMA_IDENTITY_MISMATCH")
    net_ev = _decimal(selected.get("net_ev_after_cost_bps"))
    if selected_id != expected_selected_candidate.get("candidate_id"):
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
    exit_plan_required_fields = {
        "entry_price",
        "hard_stop",
        "tp1",
        "tp2",
        "trailing_start",
        "trailing_distance",
        "time_stop_candles",
        "partial_take_profit_ratio",
    }
    if require_current_strategy_exit_policy:
        exit_plan_required_fields |= STRATEGY_EXIT_PLAN_FIELDS
    for field in sorted(exit_plan_required_fields):
        if field not in exit_plan:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", f"exit_plan missing {field}", "SCHEMA_IDENTITY_MISMATCH")
    if require_current_strategy_exit_policy:
        if exit_plan.get("strategy_exit_policy_id") != STRATEGY_EXIT_POLICY_ID:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "exit_plan strategy exit policy id mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if exit_plan.get("exit_variation") not in {TREND_PULLBACK_EXIT_VARIATION, VWAP_REVERSION_EXIT_VARIATION, BREAKOUT_RETEST_EXIT_VARIATION}:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "exit_plan strategy exit variation unsupported", "SCHEMA_IDENTITY_MISMATCH")
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
    open_position_count = int(report["paper_portfolio_snapshot"].get("open_position_count", 0) or 0)
    expected_lifecycle_decision = (
        "ENTER_LONG_WITH_ATTACHED_EXIT_PLAN"
        if final_decision == "ENTER_LONG"
        else "EXIT_POSITION_WITH_PAPER_SELL_FILL"
        if final_decision == "EXIT_POSITION"
        else "REDUCE_POSITION_WITH_PAPER_SELL_FILL"
        if final_decision == "REDUCE_POSITION"
        else "HOLD_EXISTING_POSITION_NO_NEW_ENTRY"
        if final_decision == "HOLD_POSITION" or open_position_count > 0
        else "ENTRY_BLOCKED_NO_POSITION"
        if final_decision == "BLOCKED"
        else "NO_ENTRY_NO_POSITION"
    )
    if lifecycle.get("decision") != expected_lifecycle_decision:
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "position lifecycle decision does not match final decision", "SCHEMA_IDENTITY_MISMATCH")
    if lifecycle.get("live_order_ready") or lifecycle.get("live_order_allowed") or lifecycle.get("can_live_trade") or lifecycle.get("scale_up_allowed") or lifecycle.get("can_submit_order"):
        return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "position lifecycle attempted live/order permission", "LIVE_FINAL_GUARD_FAILED")
    entry_context_status = lifecycle.get("entry_strategy_context_status")
    if require_current_strategy_exit_policy:
        if entry_context_status not in {
            "SELECTED_CANDIDATE_CONTEXT",
            "BOUND_TO_POSITION_ENTRY",
            "FALLBACK_TO_CURRENT_SELECTED_CANDIDATE",
        }:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "position lifecycle entry strategy context status is invalid", "SCHEMA_IDENTITY_MISMATCH")
        if lifecycle.get("entry_candidate_id") != exit_plan.get("source_candidate_id"):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "position lifecycle entry candidate is not the exit plan source", "SCHEMA_IDENTITY_MISMATCH")
    if require_current_strategy_exit_policy:
        if lifecycle.get("entry_strategy_family") != exit_plan.get("strategy_family"):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "position lifecycle entry strategy family is not the exit plan family", "SCHEMA_IDENTITY_MISMATCH")
        if lifecycle.get("entry_strategy_exit_variation") is not None and lifecycle.get("entry_strategy_exit_variation") != exit_plan.get("exit_variation"):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "position lifecycle entry exit variation drifted", "SCHEMA_IDENTITY_MISMATCH")
    if require_current_strategy_exit_policy and entry_context_status == "BOUND_TO_POSITION_ENTRY" and final_decision == "ENTER_LONG":
        return UpbitPaperRuntimeCycleValidationResult("FAIL", "new PAPER entry cannot claim existing position entry context", "SCHEMA_IDENTITY_MISMATCH")
    if require_position_rotation_fields:
        rotation_selected = candidates_by_id.get(lifecycle.get("entry_candidate_id"), selected)
        rotation_result = _validate_position_rotation_context(
            lifecycle,
            selected=rotation_selected,
            candidates_by_id=candidates_by_id,
            final_decision=str(final_decision),
            require_current_strategy_exit_policy=require_current_strategy_exit_policy,
        )
        if rotation_result.status != "PASS":
            return rotation_result
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
        fill_result = _validate_paper_broker_fill(report["paper_fill"], features=expected_features, expected_side="BUY")
        if fill_result.status != "PASS":
            return fill_result
        if report["paper_portfolio_snapshot"].get("open_position_count") < 1:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper fill did not update open positions", "SCHEMA_IDENTITY_MISMATCH")
    elif final_decision in {"EXIT_POSITION", "REDUCE_POSITION"}:
        if not report.get("paper_fill") or not report.get("paper_ledger_events"):
            return UpbitPaperRuntimeCycleValidationResult("BLOCKED", "paper exit/reduce requires simulated sell fill and ledger events", "LEDGER_UNAVAILABLE")
        ledger_status, ledger_blocker, ledger_message = validate_upbit_paper_ledger(report["paper_ledger_events"])
        if ledger_status != "PASS":
            return UpbitPaperRuntimeCycleValidationResult(ledger_status, ledger_message, ledger_blocker)
        if report.get("paper_ledger_head_hash") != report["paper_ledger_events"][-1]["event_hash"]:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper runtime sell ledger head hash mismatch", "LEDGER_INTEGRITY_FAIL")
        fill_result = _validate_paper_broker_fill(report["paper_fill"], features=expected_features, expected_side="SELL")
        if fill_result.status != "PASS":
            return fill_result
        if lifecycle.get("managed_position_symbol") != report["paper_fill"].get("symbol"):
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper exit/reduce fill symbol does not match managed position", "SCHEMA_IDENTITY_MISMATCH")
        if final_decision == "EXIT_POSITION" and report["paper_portfolio_snapshot"].get("open_position_count") != 0:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper exit did not close the managed position", "SCHEMA_IDENTITY_MISMATCH")
        if final_decision == "REDUCE_POSITION" and report["paper_portfolio_snapshot"].get("open_position_count") < 1:
            return UpbitPaperRuntimeCycleValidationResult("FAIL", "paper reduce unexpectedly closed all positions", "SCHEMA_IDENTITY_MISMATCH")
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
