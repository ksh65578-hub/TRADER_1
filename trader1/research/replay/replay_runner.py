from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.adapters.upbit.market_data import validate_upbit_public_candle_data
from trader1.runtime.paper.upbit_paper_runtime import (
    BREAKOUT_RETEST_EXIT_VARIATION,
    STRATEGY_EXIT_ACTION_FULL_EXIT,
    STRATEGY_EXIT_POLICY_ID,
    TREND_PULLBACK_EXIT_VARIATION,
    VWAP_REVERSION_EXIT_VARIATION,
    build_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


REPLAY_CONSISTENCY_SCHEMA_ID = "trader1.replay_consistency_report.v1"
PUBLIC_REPLAY_ROBUSTNESS_SCHEMA_ID = "trader1.public_replay_robustness_report.v1"
PUBLIC_REPLAY_VALUE_SOURCE = "PUBLIC_REST_REPLAY_DECISION_ADJUSTED_NET_EV_AFTER_COST_BPS"
PUBLIC_REPLAY_LEGACY_VALUE_SOURCE = "PUBLIC_REST_REPLAY_EXPECTED_NET_EV_AFTER_COST_BPS"
PUBLIC_REPLAY_FETCH_FAILED_SOURCE = "PUBLIC_REST_READ_ONLY_FETCH_FAILED"
PUBLIC_REPLAY_MIN_WINDOW_SIZE = 5
PUBLIC_REPLAY_DEFAULT_WINDOW_SIZE = 6
PUBLIC_REPLAY_DEFAULT_MAX_WINDOWS = 420
PUBLIC_REPLAY_MAX_WINDOW_CAP = 6000
ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ReplayConsistencyValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def replay_consistency_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("replay_consistency_hash", None)
    return sha256_json(payload)


def public_replay_robustness_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("report_hash", None)
    return sha256_json(payload)


def run_replay_once(*, input_events: list[dict[str, Any]], parameter_hash: str) -> str:
    return sha256_json({"input_events": input_events, "parameter_hash": parameter_hash})


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _number(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    return result if math.isfinite(result) else 0.0


def _candidate_by_id(runtime_cycle: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
    selected = runtime_cycle.get("selected_candidate")
    if isinstance(selected, dict) and selected.get("candidate_id") == candidate_id:
        return selected
    for candidate in runtime_cycle.get("strategy_candidates") or []:
        if isinstance(candidate, dict) and candidate.get("candidate_id") == candidate_id:
            return candidate
    return None


def _fill_cost_comparison(fill: dict[str, Any]) -> dict[str, float]:
    filled_notional = _number(fill.get("filled_notional"))
    fee_amount = _number(fill.get("fee_amount"))
    realized_fee = fee_amount / filled_notional * 10000.0 if filled_notional > 0 and fee_amount >= 0 else _number(fill.get("fee_bps"))
    realized_slippage = _number(fill.get("slippage_bps"))
    realized_impact = _number(fill.get("market_impact_bps"))
    expected_fee = _number(fill.get("fee_bps")) or _number(fill.get("fee_rate")) * 10000.0
    expected_spread = _number(fill.get("effective_spread_bps")) or _number(fill.get("spread_bps"))
    expected_slippage = _number(fill.get("adaptive_slippage_bps"))
    expected_impact = _number(fill.get("market_impact_bps"))
    expected_latency = _number(fill.get("latency_penalty_bps"))
    expected_total = expected_fee + expected_spread + expected_slippage + expected_impact + expected_latency
    realized_total = realized_fee + realized_slippage
    return {
        "realized_fee_bps": realized_fee,
        "realized_slippage_bps": realized_slippage,
        "realized_impact_bps": realized_impact,
        "expected_total_execution_cost_bps": expected_total,
        "realized_total_execution_cost_bps": realized_total,
        "execution_cost_delta_bps": realized_total - expected_total,
    }


def _expected_exit_variation(strategy_family: Any) -> str:
    return {
        "PULLBACK_TREND_LONG": TREND_PULLBACK_EXIT_VARIATION,
        "VWAP_MEAN_REVERSION": VWAP_REVERSION_EXIT_VARIATION,
        "BREAKOUT_RETEST_LONG": BREAKOUT_RETEST_EXIT_VARIATION,
    }.get(str(strategy_family or ""), "")


def _strategy_exit_policy_sample(
    *,
    lifecycle: dict[str, Any],
    expected_exit_variation: str,
) -> tuple[bool, str | None]:
    policy_id = str(lifecycle.get("strategy_exit_policy_id") or "")
    exit_variation = str(lifecycle.get("strategy_exit_variation") or "")
    entry_exit_variation = str(lifecycle.get("entry_strategy_exit_variation") or "")
    reason_code = str(lifecycle.get("strategy_exit_reason_code") or lifecycle.get("position_exit_reason_code") or "")
    nested = lifecycle.get("position_exit_evaluation")
    nested = nested if isinstance(nested, dict) else {}
    action = str(lifecycle.get("strategy_exit_action") or nested.get("strategy_exit_action") or "")
    strategy_reason = str(lifecycle.get("strategy_exit_reason_code") or "")
    if strategy_reason == "NONE":
        strategy_reason = ""
    policy_matched = (
        policy_id == STRATEGY_EXIT_POLICY_ID
        and bool(expected_exit_variation)
        and exit_variation == expected_exit_variation
        and (not entry_exit_variation or entry_exit_variation == expected_exit_variation)
        and bool(reason_code)
    )
    if strategy_reason and action != STRATEGY_EXIT_ACTION_FULL_EXIT:
        policy_matched = False
    return policy_matched, reason_code or None


def _sell_fill_realized_delta(fill: dict[str, Any], lifecycle: dict[str, Any]) -> float | None:
    quantity = _number(fill.get("filled_quantity") or fill.get("quantity"))
    fill_price = _number(fill.get("fill_price"))
    fee_amount = _number(fill.get("fee_amount"))
    managed_quantity = _number(lifecycle.get("managed_position_quantity"))
    managed_cost_basis = _number(lifecycle.get("managed_position_cost_basis"))
    if min(quantity, fill_price, managed_quantity, managed_cost_basis) <= 0 or quantity > managed_quantity:
        return None
    allocated_cost_basis = managed_cost_basis * (quantity / managed_quantity)
    return (quantity * fill_price) - allocated_cost_basis - fee_amount


def _replay_trade_lifecycle_fields(
    *,
    runtime: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    fill = runtime.get("paper_fill")
    lifecycle = runtime.get("position_management_decision")
    fill = fill if isinstance(fill, dict) else {}
    lifecycle = lifecycle if isinstance(lifecycle, dict) else {}
    target_candidate_id = str(candidate.get("candidate_id") or "")
    final_decision = str(runtime.get("final_decision") or "")
    side = str(fill.get("side") or "")
    selected = runtime.get("selected_candidate")
    candidate_fill = (
        (
            side == "BUY"
            and final_decision == "ENTER_LONG"
            and isinstance(selected, dict)
            and str(selected.get("candidate_id") or "") == target_candidate_id
        )
        or (side == "SELL" and str(lifecycle.get("entry_candidate_id") or "") == target_candidate_id)
    )
    expected_exit_variation = _expected_exit_variation(candidate.get("strategy_family"))
    strategy_exit_observed = side == "SELL" and final_decision in {"EXIT_POSITION", "REDUCE_POSITION"} and candidate_fill
    strategy_exit_matched = False
    strategy_exit_reason_code = None
    if strategy_exit_observed:
        strategy_exit_matched, strategy_exit_reason_code = _strategy_exit_policy_sample(
            lifecycle=lifecycle,
            expected_exit_variation=expected_exit_variation,
        )
    closed_trade = strategy_exit_observed and final_decision == "EXIT_POSITION"
    realized_trade_pnl_bps = None
    realized_vs_expected_edge_bps = None
    if closed_trade:
        realized_delta = _sell_fill_realized_delta(fill, lifecycle)
        filled_notional = max(1.0, _number(fill.get("filled_notional")))
        if realized_delta is not None:
            realized_trade_pnl_bps = realized_delta / filled_notional * 10000.0
            realized_vs_expected_edge_bps = realized_trade_pnl_bps - _number(candidate.get("net_ev_after_cost_bps"))
    cost = _fill_cost_comparison(fill) if candidate_fill and side in {"BUY", "SELL"} else {}
    return {
        "runtime_final_decision": final_decision,
        "runtime_no_trade_reasons": [str(reason) for reason in runtime.get("no_trade_reasons", []) if reason],
        "runtime_paper_fill_side": side or None,
        "runtime_paper_broker_state": fill.get("order_lifecycle_state"),
        "paper_fill_belongs_to_candidate": bool(candidate_fill),
        "paper_fill_side": side if candidate_fill else None,
        "paper_broker_state": fill.get("order_lifecycle_state") if candidate_fill else None,
        "closed_trade": bool(closed_trade and realized_trade_pnl_bps is not None),
        "realized_trade_pnl_bps": realized_trade_pnl_bps,
        "realized_vs_expected_edge_bps": realized_vs_expected_edge_bps,
        "strategy_exit_policy_observed": strategy_exit_observed,
        "strategy_exit_policy_matched": strategy_exit_matched,
        "strategy_exit_policy_id": lifecycle.get("strategy_exit_policy_id"),
        "strategy_exit_variation": lifecycle.get("strategy_exit_variation"),
        "expected_strategy_exit_variation": expected_exit_variation,
        "strategy_exit_reason_code": strategy_exit_reason_code,
        "strategy_exit_action": lifecycle.get("strategy_exit_action"),
        **cost,
    }


def _portfolio_contains_candidate_position(snapshot: dict[str, Any] | None, candidate_id: str) -> bool:
    if not isinstance(snapshot, dict) or not candidate_id:
        return False
    for position in snapshot.get("positions") or []:
        if isinstance(position, dict) and str(position.get("entry_candidate_id") or "") == candidate_id:
            return True
    return False


def _public_replay_closed_trade_summary(sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed_rows = [row for row in sample_rows if row.get("closed_trade") is True and row.get("realized_trade_pnl_bps") is not None]
    policy_rows = [row for row in sample_rows if row.get("strategy_exit_policy_observed") is True]
    cost_rows = [row for row in sample_rows if row.get("execution_cost_delta_bps") is not None]
    gross_profit = sum(max(0.0, _number(row.get("realized_trade_pnl_bps"))) for row in closed_rows)
    gross_loss = sum(abs(min(0.0, _number(row.get("realized_trade_pnl_bps")))) for row in closed_rows)
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0 and closed_rows:
        profit_factor = 999.0
    else:
        profit_factor = 0.0
    cumulative = 0.0
    peak = 0.0
    max_drawdown_bps = 0.0
    for row in closed_rows:
        cumulative += _number(row.get("realized_trade_pnl_bps"))
        peak = max(peak, cumulative)
        max_drawdown_bps = max(max_drawdown_bps, peak - cumulative)
    reason_counts: dict[str, int] = {}
    for row in policy_rows:
        reason = str(row.get("strategy_exit_reason_code") or "")
        if reason:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    realized_vs_expected_values = [_number(row.get("realized_vs_expected_edge_bps")) for row in closed_rows]
    cost_delta_values = [_number(row.get("execution_cost_delta_bps")) for row in cost_rows]
    fill_quality_values = [
        max(
            0.0,
            min(
                1.0,
                1.0 - max(0.0, _number(row.get("execution_cost_delta_bps"))) / max(1.0, _number(row.get("expected_total_execution_cost_bps"))),
            ),
        )
        for row in cost_rows
    ]
    closed_count = len(closed_rows)
    policy_count = len(policy_rows)
    policy_mismatch_count = sum(1 for row in policy_rows if row.get("strategy_exit_policy_matched") is not True)
    mean_realized_vs_expected = sum(realized_vs_expected_values) / len(realized_vs_expected_values) if realized_vs_expected_values else -999.0
    mean_cost_delta = sum(cost_delta_values) / len(cost_delta_values) if cost_delta_values else 999.0
    return {
        "replay_closed_trade_sample_count": closed_count,
        "replay_closed_trade_status": "PASS" if closed_count > 0 else "UNTESTED",
        "replay_strategy_exit_policy_sample_count": policy_count,
        "replay_strategy_exit_policy_match_count": policy_count - policy_mismatch_count,
        "replay_strategy_exit_policy_mismatch_count": policy_mismatch_count,
        "replay_strategy_exit_policy_status": "PASS" if policy_count > 0 and policy_mismatch_count == 0 else "UNTESTED" if policy_count == 0 else "FAIL",
        "replay_strategy_exit_reason_counts": [
            {"reason_code": reason, "count": count}
            for reason, count in sorted(reason_counts.items())
        ],
        "replay_profit_factor": profit_factor,
        "replay_profit_factor_status": "PASS" if closed_count > 0 and profit_factor >= 1.25 else "UNTESTED" if closed_count == 0 else "FAIL",
        "replay_max_drawdown_bps": max_drawdown_bps,
        "replay_realized_vs_expected_edge_bps": mean_realized_vs_expected,
        "replay_realized_vs_expected_edge_status": "PASS" if realized_vs_expected_values and mean_realized_vs_expected >= 0 else "UNTESTED" if not realized_vs_expected_values else "FAIL",
        "replay_fill_quality_score": sum(fill_quality_values) / len(fill_quality_values) if fill_quality_values else 0.0,
        "replay_execution_cost_delta_bps": mean_cost_delta,
        "replay_execution_cost_status": "PASS" if cost_delta_values and mean_cost_delta <= 2.0 else "UNTESTED" if not cost_delta_values else "FAIL",
        "replay_performance_scope": "PUBLIC_REPLAY_ONLY_NOT_PAPER_RANKING",
    }


def required_replay_closed_trade_threshold(
    replay_window_minimum: int,
    runtime_mode: str,
    replay_type: str,
) -> int:
    """Return the single closed-trade maturity floor used by replay promotion gates."""
    window_minimum = max(1, int(replay_window_minimum))
    normalized_mode = str(runtime_mode or "").strip().upper()
    normalized_replay_type = str(replay_type or "").strip().upper()
    if normalized_mode not in {"PAPER", "SHADOW", "REPLAY"}:
        normalized_mode = "PAPER"
    if normalized_replay_type not in {"PUBLIC_REPLAY", "PUBLIC", "PUBLIC_REPLAY_ROBUSTNESS"}:
        normalized_replay_type = "PUBLIC_REPLAY"
    if window_minimum < 30:
        return window_minimum
    one_tenth_of_windows = (window_minimum + 9) // 10
    return max(30, min(120, one_tenth_of_windows))


def min_required_closed_trade_sample_count_for_public_replay(min_required_sample_count: int) -> int:
    """Backward-compatible public replay threshold wrapper."""
    return required_replay_closed_trade_threshold(
        replay_window_minimum=min_required_sample_count,
        runtime_mode="PAPER",
        replay_type="PUBLIC_REPLAY",
    )


def _public_replay_closed_trade_maturity_summary(
    *,
    closed_trade_count: int,
    min_required_closed_trade_sample_count: int,
) -> dict[str, Any]:
    safe_minimum = required_replay_closed_trade_threshold(
        replay_window_minimum=int(min_required_closed_trade_sample_count),
        runtime_mode="PAPER",
        replay_type="PUBLIC_REPLAY",
    )
    deficit = max(0, safe_minimum - int(closed_trade_count))
    if deficit <= 0:
        status = "PASS"
        blocker_code = None
    elif closed_trade_count > 0:
        status = "BLOCKED"
        blocker_code = "REPLAY_CLOSED_TRADES_BELOW_MIN"
    else:
        status = "UNTESTED"
        blocker_code = "REPLAY_CLOSED_TRADES_MISSING"
    return {
        "min_required_closed_trade_sample_count": safe_minimum,
        "replay_closed_trade_deficit": deficit,
        "replay_closed_trade_maturity_status": status,
        "replay_closed_trade_maturity_blocker_code": blocker_code,
    }


def _public_replay_sample_row(
    *,
    replay_id: str,
    replay_index: int,
    window_candles: list[dict[str, Any]],
    runtime: dict[str, Any],
    candidate: dict[str, Any],
    strategy_id: Any,
) -> dict[str, Any]:
    opportunity_net_ev = _number(candidate.get("net_ev_after_cost_bps"))
    opportunity_gross_edge = _number(candidate.get("gross_expected_edge_bps"))
    opportunity_cost = _number(candidate.get("total_execution_cost_bps"))
    lifecycle_fields = _replay_trade_lifecycle_fields(runtime=runtime, candidate=candidate)
    executed_trade = (
        candidate.get("decision") == "PAPER_ENTRY_REVIEW"
        and lifecycle_fields.get("paper_fill_belongs_to_candidate") is True
        and lifecycle_fields.get("paper_fill_side") == "BUY"
    )
    if executed_trade:
        net_ev_after_cost = opportunity_net_ev
        gross_expected_edge = opportunity_gross_edge
        total_execution_cost = opportunity_cost
        replay_return_basis = "EXECUTED_ENTRY_REVIEW_NET_EV_AFTER_COST"
    else:
        net_ev_after_cost = 0.0
        gross_expected_edge = 0.0
        total_execution_cost = 0.0
        replay_return_basis = "FLAT_NO_TRADE_CASH_RETURN"
    return {
        "sample_id": f"{replay_id}:sample:{replay_index:04d}",
        "sample_index": replay_index,
        "event_time_utc": window_candles[-1].get("timestamp"),
        "runtime_cycle_id": runtime["cycle_id"],
        "runtime_cycle_hash": runtime["cycle_hash"],
        "symbol": candidate.get("symbol"),
        "strategy_family": candidate.get("strategy_family"),
        "strategy_id": strategy_id,
        "candidate_id": candidate.get("candidate_id"),
        "decision": "PAPER_ENTRY_REVIEW" if executed_trade else "NO_TRADE",
        "executed_trade": executed_trade,
        "replay_return_basis": replay_return_basis,
        "regime": candidate.get("regime") or runtime.get("regime"),
        "strategy_policy_reason": candidate.get("strategy_policy_reason"),
        "no_trade_reason": candidate.get("no_trade_reason"),
        "net_ev_after_cost_bps": net_ev_after_cost,
        "gross_expected_edge_bps": gross_expected_edge,
        "total_execution_cost_bps": total_execution_cost,
        "opportunity_net_ev_after_cost_bps": opportunity_net_ev,
        "opportunity_gross_expected_edge_bps": opportunity_gross_edge,
        "opportunity_total_execution_cost_bps": opportunity_cost,
        **lifecycle_fields,
    }


def _safe_artifact_stem(value: Any) -> str:
    text = str(value or "unknown")
    safe = "".join(character if character.isalnum() or character in "-_." else "_" for character in text).strip("._")
    if not safe:
        safe = "unknown"
    if len(safe) > 96:
        safe = f"{safe[:80]}-{hashlib.sha256(text.encode('utf-8')).hexdigest().upper()[:16]}"
    return safe


def build_public_replay_robustness_report(
    *,
    candidate_scorecard: dict[str, Any],
    market_data: dict[str, Any],
    replay_id: str | None = None,
    window_size: int = PUBLIC_REPLAY_DEFAULT_WINDOW_SIZE,
    max_replay_windows: int = PUBLIC_REPLAY_DEFAULT_MAX_WINDOWS,
    min_required_sample_count: int = 300,
) -> dict[str, Any]:
    symbol = str(candidate_scorecard.get("symbol") or "")
    session_id = str(candidate_scorecard.get("session_id") or "mvp1_upbit_paper_launcher")
    safe_window_size = max(PUBLIC_REPLAY_MIN_WINDOW_SIZE, int(window_size))
    safe_max_windows = max(1, min(int(max_replay_windows), PUBLIC_REPLAY_MAX_WINDOW_CAP))
    replay_id = replay_id or f"public-replay:{candidate_scorecard.get('source_runtime_cycle_id')}:{candidate_scorecard.get('candidate_id')}"
    data_status, data_blocker, data_message = validate_upbit_public_candle_data(
        market_data,
        symbol=symbol,
        session_id=session_id,
    )
    blockers: list[dict[str, str]] = []
    sample_rows: list[dict[str, Any]] = []
    source_hash = sha256_json(market_data)

    if data_status != "PASS":
        blockers.append(_blocker(data_blocker or "DATA_UNAVAILABLE", data_message))
    else:
        candles = [candle for candle in market_data.get("candles") or [] if isinstance(candle, dict)]
        if len(candles) < safe_window_size:
            blockers.append(_blocker("MEASUREMENT_MISSING", "public replay requires enough candle history for windowed evaluation"))
        window_count = max(0, len(candles) - safe_window_size + 1)
        start_index = max(0, window_count - safe_max_windows)
        current_replay_portfolio: dict[str, Any] | None = None
        target_candidate_id = str(candidate_scorecard.get("candidate_id") or "")
        target_strategy_id = str(candidate_scorecard.get("strategy_id") or "")
        target_parameter_hash = str(candidate_scorecard.get("parameter_hash") or "").upper()
        for replay_index, candle_index in enumerate(range(start_index, window_count), start=1):
            window_candles = candles[candle_index : candle_index + safe_window_size]
            window_market_data = dict(market_data)
            window_market_data["candles"] = window_candles
            window_market_data["profile"] = "PUBLIC_REST_REPLAY_WINDOW"
            cycle_id = f"public-replay-{_safe_artifact_stem(symbol)}-{candle_index + 1:04d}"
            portfolio_kwargs: dict[str, Any] = {}
            if isinstance(current_replay_portfolio, dict):
                portfolio_kwargs = {
                    "current_paper_portfolio_snapshot": current_replay_portfolio,
                    "paper_cash_available": current_replay_portfolio.get("cash_available"),
                    "paper_equity": current_replay_portfolio.get("equity"),
                    "paper_position_market_value": current_replay_portfolio.get("position_market_value"),
                }
            runtime = build_upbit_paper_runtime_cycle_report(
                cycle_id=cycle_id,
                session_id=session_id,
                symbol=symbol,
                market_data=window_market_data,
                paper_scope_focus={
                    "source": "PUBLIC_REPLAY_CANDIDATE_SCOPE",
                    "candidate_id": target_candidate_id,
                    "symbol": symbol,
                    "strategy_id": target_strategy_id,
                    "parameter_hash": target_parameter_hash,
                    "sample_count": replay_index - 1,
                    "sample_deficit": max(1, safe_max_windows - replay_index + 1),
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                },
                **portfolio_kwargs,
            )
            candidate = _candidate_by_id(runtime, target_candidate_id)
            if not isinstance(candidate, dict):
                continue
            if any(candidate.get(flag) is True for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
                blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "public replay candidate attempted live or scale-up permission"))
                continue
            sample_row = _public_replay_sample_row(
                replay_id=replay_id,
                replay_index=replay_index,
                window_candles=window_candles,
                runtime=runtime,
                candidate=candidate,
                strategy_id=candidate_scorecard.get("strategy_id"),
            )
            sample_rows.append(sample_row)
            runtime_portfolio = runtime.get("paper_portfolio_snapshot")
            if isinstance(runtime_portfolio, dict) and (
                sample_row.get("paper_fill_belongs_to_candidate") is True
                or _portfolio_contains_candidate_position(runtime_portfolio, target_candidate_id)
                or _portfolio_contains_candidate_position(current_replay_portfolio, target_candidate_id)
            ):
                current_replay_portfolio = runtime_portfolio

    sample_count = len(sample_rows)
    if sample_count < int(min_required_sample_count):
        blockers.append(
            _blocker(
                "SAMPLE_INSUFFICIENT",
                f"{sample_count} public replay robustness samples collected; {int(min_required_sample_count)} required",
            )
        )
    status = "PASS" if not blockers else "BLOCKED"
    replay_closed_trade_summary = _public_replay_closed_trade_summary(sample_rows)
    closed_trade_maturity_summary = _public_replay_closed_trade_maturity_summary(
        closed_trade_count=int(replay_closed_trade_summary["replay_closed_trade_sample_count"]),
        min_required_closed_trade_sample_count=int(min_required_sample_count),
    )
    report = {
        "schema_id": PUBLIC_REPLAY_ROBUSTNESS_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "replay_id": replay_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "REPLAY",
        "session_id": session_id,
        "symbol": symbol,
        "candidate_id": candidate_scorecard.get("candidate_id"),
        "strategy_id": candidate_scorecard.get("strategy_id"),
        "strategy_build_id": candidate_scorecard.get("strategy_build_id"),
        "parameter_hash": candidate_scorecard.get("parameter_hash"),
        "mutation_status": candidate_scorecard.get("mutation_status", "NOT_MUTATED"),
        "mutation_id": candidate_scorecard.get("mutation_id"),
        "mutation_reason_code": candidate_scorecard.get("mutation_reason_code"),
        "mutated_paper_candidate_spec_id": candidate_scorecard.get("mutated_paper_candidate_spec_id"),
        "mutation_spec_hash": candidate_scorecard.get("mutation_spec_hash"),
        "parent_parameter_hash": candidate_scorecard.get("parent_parameter_hash"),
        "value_source": PUBLIC_REPLAY_VALUE_SOURCE,
        "public_market_data_source": market_data.get("source"),
        "public_market_data_hash": source_hash,
        "window_size": safe_window_size,
        "sample_count": sample_count,
        "min_required_sample_count": int(min_required_sample_count),
        "max_replay_windows": safe_max_windows,
        "sample_rows": sample_rows,
        **replay_closed_trade_summary,
        **closed_trade_maturity_summary,
        "replay_status": status,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = public_replay_robustness_report_hash(report)
    return report


def build_public_replay_fetch_failure_report(
    *,
    candidate_scorecard: dict[str, Any],
    replay_id: str,
    error_type: str,
    error_message: str,
    target_count: int,
    page_size: int,
    timeout_seconds: float,
    window_size: int = PUBLIC_REPLAY_DEFAULT_WINDOW_SIZE,
    max_replay_windows: int = PUBLIC_REPLAY_DEFAULT_MAX_WINDOWS,
    min_required_sample_count: int = 300,
) -> dict[str, Any]:
    symbol = str(candidate_scorecard.get("symbol") or "")
    session_id = str(candidate_scorecard.get("session_id") or "mvp1_upbit_paper_launcher")
    safe_window_size = max(PUBLIC_REPLAY_MIN_WINDOW_SIZE, int(window_size))
    safe_max_windows = max(1, min(int(max_replay_windows), PUBLIC_REPLAY_MAX_WINDOW_CAP))
    failure_source = {
        "source": PUBLIC_REPLAY_FETCH_FAILED_SOURCE,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "REPLAY",
        "session_id": session_id,
        "symbol": symbol,
        "target_count": max(0, int(target_count)),
        "page_size": max(0, int(page_size)),
        "timeout_seconds": max(0.0, float(timeout_seconds)),
        "error_type": str(error_type or "Exception")[:96],
        "error_message": str(error_message or "")[:240],
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
    }
    report = {
        "schema_id": PUBLIC_REPLAY_ROBUSTNESS_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "replay_id": replay_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "REPLAY",
        "session_id": session_id,
        "symbol": symbol,
        "candidate_id": candidate_scorecard.get("candidate_id"),
        "strategy_id": candidate_scorecard.get("strategy_id"),
        "strategy_build_id": candidate_scorecard.get("strategy_build_id"),
        "parameter_hash": candidate_scorecard.get("parameter_hash"),
        "value_source": PUBLIC_REPLAY_VALUE_SOURCE,
        "public_market_data_source": PUBLIC_REPLAY_FETCH_FAILED_SOURCE,
        "public_market_data_hash": sha256_json(failure_source),
        "public_market_data_fetch_status": "FAILED",
        "public_market_data_error_type": failure_source["error_type"],
        "public_market_data_error_message": failure_source["error_message"],
        "window_size": safe_window_size,
        "sample_count": 0,
        "min_required_sample_count": int(min_required_sample_count),
        "max_replay_windows": safe_max_windows,
        "sample_rows": [],
        "replay_closed_trade_sample_count": 0,
        "replay_closed_trade_status": "UNTESTED",
        "min_required_closed_trade_sample_count": required_replay_closed_trade_threshold(
            replay_window_minimum=int(min_required_sample_count),
            runtime_mode="PAPER",
            replay_type="PUBLIC_REPLAY",
        ),
        "replay_closed_trade_deficit": required_replay_closed_trade_threshold(
            replay_window_minimum=int(min_required_sample_count),
            runtime_mode="PAPER",
            replay_type="PUBLIC_REPLAY",
        ),
        "replay_closed_trade_maturity_status": "UNTESTED",
        "replay_closed_trade_maturity_blocker_code": "REPLAY_CLOSED_TRADES_MISSING",
        "replay_status": "BLOCKED",
        "primary_blocker_code": "DATA_QUALITY_INSUFFICIENT",
        "blockers": [
            _blocker(
                "DATA_QUALITY_INSUFFICIENT",
                "public replay could not collect read-only public candles; candidate review remains blocked",
            )
        ],
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = public_replay_robustness_report_hash(report)
    return report


def validate_public_replay_robustness_report(
    report: dict[str, Any],
    *,
    candidate_scorecard: dict[str, Any] | None = None,
) -> ReplayConsistencyValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "replay_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "candidate_id",
        "strategy_id",
        "strategy_build_id",
        "parameter_hash",
        "value_source",
        "public_market_data_source",
        "public_market_data_hash",
        "window_size",
        "sample_count",
        "min_required_sample_count",
        "max_replay_windows",
        "sample_rows",
        "replay_closed_trade_sample_count",
        "replay_closed_trade_status",
        "min_required_closed_trade_sample_count",
        "replay_closed_trade_deficit",
        "replay_closed_trade_maturity_status",
        "replay_closed_trade_maturity_blocker_code",
        "replay_status",
        "primary_blocker_code",
        "blockers",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ReplayConsistencyValidationResult("FAIL", f"public replay report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != PUBLIC_REPLAY_ROBUSTNESS_SCHEMA_ID:
        return ReplayConsistencyValidationResult("FAIL", "public replay schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("report_hash") != public_replay_robustness_report_hash(report):
        return ReplayConsistencyValidationResult("FAIL", "public replay report hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "REPLAY":
        return ReplayConsistencyValidationResult("BLOCKED", "public replay scope must remain UPBIT/KRW_SPOT/REPLAY", "SNAPSHOT_SCOPE_MISMATCH")
    forbidden = (
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden):
        return ReplayConsistencyValidationResult("BLOCKED", "public replay attempted private, order, live, or scale-up behavior", "LIVE_FINAL_GUARD_FAILED")
    if report.get("value_source") not in {PUBLIC_REPLAY_VALUE_SOURCE, PUBLIC_REPLAY_LEGACY_VALUE_SOURCE}:
        return ReplayConsistencyValidationResult("FAIL", "public replay value source mismatch", "SCHEMA_IDENTITY_MISMATCH")
    allowed_market_sources = {"STATIC_FIXTURE", "PUBLIC_REST_READ_ONLY", PUBLIC_REPLAY_FETCH_FAILED_SOURCE}
    if report.get("public_market_data_source") not in allowed_market_sources:
        return ReplayConsistencyValidationResult("FAIL", "public replay public market data source mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("public_market_data_source") == PUBLIC_REPLAY_FETCH_FAILED_SOURCE:
        if report.get("replay_status") != "BLOCKED" or report.get("primary_blocker_code") != "DATA_QUALITY_INSUFFICIENT":
            return ReplayConsistencyValidationResult("FAIL", "failed public replay fetch must stay DATA_QUALITY_INSUFFICIENT/BLOCKED", "SCHEMA_IDENTITY_MISMATCH")
        if int(report.get("sample_count") or 0) != 0 or report.get("sample_rows"):
            return ReplayConsistencyValidationResult("FAIL", "failed public replay fetch cannot carry sample rows", "SCHEMA_IDENTITY_MISMATCH")
    strict_decision_adjusted_rows = report.get("value_source") == PUBLIC_REPLAY_VALUE_SOURCE
    sample_rows = report.get("sample_rows")
    if not isinstance(sample_rows, list) or int(report.get("sample_count") or 0) != len(sample_rows):
        return ReplayConsistencyValidationResult("FAIL", "public replay sample count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    for row in sample_rows:
        if not isinstance(row, dict):
            return ReplayConsistencyValidationResult("FAIL", "public replay sample row must be an object", "SCHEMA_IDENTITY_MISMATCH")
        decision = row.get("decision")
        if decision == "NO_TRADE":
            row_uses_decision_adjusted_fields = (
                strict_decision_adjusted_rows
                or "executed_trade" in row
                or "replay_return_basis" in row
                or "opportunity_net_ev_after_cost_bps" in row
            )
            if not row_uses_decision_adjusted_fields:
                continue
            if row.get("executed_trade") is not False:
                return ReplayConsistencyValidationResult("FAIL", "NO_TRADE replay row cannot be executed", "SCHEMA_IDENTITY_MISMATCH")
            if _number(row.get("net_ev_after_cost_bps")) != 0.0:
                return ReplayConsistencyValidationResult("FAIL", "NO_TRADE replay row must use flat-cash zero return", "SCHEMA_IDENTITY_MISMATCH")
            if _number(row.get("total_execution_cost_bps")) != 0.0:
                return ReplayConsistencyValidationResult("FAIL", "NO_TRADE replay row cannot carry execution cost", "SCHEMA_IDENTITY_MISMATCH")
        elif decision == "PAPER_ENTRY_REVIEW":
            if strict_decision_adjusted_rows and row.get("executed_trade") is not True:
                return ReplayConsistencyValidationResult("FAIL", "entry replay row must be marked executed", "SCHEMA_IDENTITY_MISMATCH")
            if row.get("executed_trade") is False:
                return ReplayConsistencyValidationResult("FAIL", "entry replay row must be marked executed", "SCHEMA_IDENTITY_MISMATCH")
        else:
            return ReplayConsistencyValidationResult("FAIL", "public replay decision is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("replay_status") == "PASS" and report.get("blockers"):
        return ReplayConsistencyValidationResult("BLOCKED", "public replay PASS cannot carry blockers", report["blockers"][0].get("code", "UNKNOWN_BLOCKED"))
    if candidate_scorecard is not None:
        for field in ("candidate_id", "strategy_id", "strategy_build_id", "parameter_hash", "session_id", "symbol"):
            if str(report.get(field) or "") != str(candidate_scorecard.get(field) or ""):
                return ReplayConsistencyValidationResult("BLOCKED", f"public replay candidate scope mismatch: {field}", "SNAPSHOT_SCOPE_MISMATCH")
    return ReplayConsistencyValidationResult("PASS", "public replay robustness report is scoped, hash-bound, and live-blocked", None)


def public_replay_robustness_values_from_report(
    report: dict[str, Any],
    *,
    candidate_scorecard: dict[str, Any],
) -> tuple[list[float], list[dict[str, Any]], list[str]]:
    result = validate_public_replay_robustness_report(report, candidate_scorecard=candidate_scorecard)
    if result.status != "PASS":
        return [], [], []
    source_ids = [
        f"public_replay_robustness:{report['replay_id']}:{report['report_hash']}",
        f"public_market_data:{report['symbol']}:{report['public_market_data_hash']}",
    ]
    values: list[float] = []
    samples: list[dict[str, Any]] = []
    for row in report.get("sample_rows") or []:
        if not isinstance(row, dict) or row.get("candidate_id") != report.get("candidate_id"):
            continue
        if row.get("closed_trade") is not True or row.get("realized_trade_pnl_bps") is None:
            continue
        values.append(_number(row.get("realized_trade_pnl_bps")))
        samples.append(
            {
                "loop_id": report["replay_id"],
                "source_loop_report_hash": report["report_hash"],
                "source_runtime_cycle_hash": row.get("runtime_cycle_hash"),
                "source_runtime_cycle_id": row.get("runtime_cycle_id"),
                "closed_trade": True,
                "value_source": "PUBLIC_REPLAY_REALIZED_CLOSED_TRADE_PNL_BPS",
            }
        )
    return values, samples, source_ids


def public_replay_robustness_report_path(*, root: Path = ROOT, report: dict[str, Any]) -> Path:
    return (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(report["session_id"])
        / "profitability"
        / "replay_robustness"
        / f"{_safe_artifact_stem(report.get('candidate_id'))}.public_replay_robustness_report.json"
    )


def write_public_replay_robustness_report(*, root: Path = ROOT, report: dict[str, Any]) -> Path:
    path = public_replay_robustness_report_path(root=root, report=report)
    durable_atomic_write_json(path, report)
    return path


def load_public_replay_robustness_report(
    *,
    root: Path = ROOT,
    session_id: str,
    candidate_id: str,
) -> dict[str, Any] | None:
    path = (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(session_id)
        / "profitability"
        / "replay_robustness"
        / f"{_safe_artifact_stem(candidate_id)}.public_replay_robustness_report.json"
    )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def build_replay_consistency_report(
    *,
    replay_id: str,
    strategy_unit_id: str,
    parameter_hash: str,
    input_events: list[dict[str, Any]],
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    session_id: str = "mvp3_replay",
    repeated_runs: int = 2,
) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    if exchange != "UPBIT" or market_type != "KRW_SPOT":
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "replay consistency is scoped to UPBIT/KRW_SPOT"))
    if repeated_runs < 2:
        blockers.append(_blocker("MEASUREMENT_MISSING", "replay consistency requires at least two repeated runs"))
    if not input_events:
        blockers.append(_blocker("DATA_UNAVAILABLE", "replay input events are missing"))
    result_hashes = [run_replay_once(input_events=input_events, parameter_hash=parameter_hash) for _ in range(max(0, repeated_runs))]
    deterministic_pass = bool(result_hashes) and len(set(result_hashes)) == 1
    if not deterministic_pass:
        blockers.append(_blocker("MEASUREMENT_MISSING", "replay repeated result hashes do not match"))
    report = {
        "schema_id": REPLAY_CONSISTENCY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "replay_id": replay_id,
        "exchange": exchange,
        "market_type": market_type,
        "mode": "REPLAY",
        "session_id": session_id,
        "strategy_unit_id": strategy_unit_id,
        "parameter_hash": parameter_hash,
        "input_hash": sha256_json(input_events),
        "result_hashes": result_hashes,
        "deterministic_pass": deterministic_pass,
        "replay_status": "PASS" if not blockers else "BLOCKED",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "replay_consistency_hash": "",
    }
    report["replay_consistency_hash"] = replay_consistency_hash(report)
    return report


def validate_replay_consistency_report(report: dict[str, Any]) -> ReplayConsistencyValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "replay_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "strategy_unit_id",
        "parameter_hash",
        "input_hash",
        "result_hashes",
        "deterministic_pass",
        "replay_status",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "replay_consistency_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ReplayConsistencyValidationResult("FAIL", f"replay report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != REPLAY_CONSISTENCY_SCHEMA_ID:
        return ReplayConsistencyValidationResult("FAIL", "replay schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("replay_consistency_hash") != replay_consistency_hash(report):
        return ReplayConsistencyValidationResult("FAIL", "replay report hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "REPLAY":
        return ReplayConsistencyValidationResult("BLOCKED", "replay scope must remain UPBIT/KRW_SPOT/REPLAY", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("order_adapter_called"):
        return ReplayConsistencyValidationResult("BLOCKED", "replay attempted to create live/order permission", "LIVE_FINAL_GUARD_FAILED")
    hashes = report.get("result_hashes", [])
    if not hashes or len(set(hashes)) != 1 or report.get("deterministic_pass") is not True:
        return ReplayConsistencyValidationResult("FAIL", "replay repeated result hashes do not match", "MEASUREMENT_MISSING")
    if report.get("replay_status") == "PASS" and report.get("blockers"):
        return ReplayConsistencyValidationResult("BLOCKED", "replay PASS cannot carry blockers", report["blockers"][0].get("code", "UNKNOWN_BLOCKED"))
    return ReplayConsistencyValidationResult("PASS", "replay consistency is deterministic and research-only", None)
