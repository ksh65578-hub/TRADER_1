from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_runtime import (
    BREAKOUT_RETEST_EXIT_VARIATION,
    STRATEGY_EXIT_ACTION_FULL_EXIT,
    STRATEGY_EXIT_POLICY_ID,
    TREND_PULLBACK_EXIT_VARIATION,
    VWAP_REVERSION_EXIT_VARIATION,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json
from trader1.research.replay.replay_runner import public_replay_robustness_report_hash


ROOT = Path(__file__).resolve().parents[3]
SCORECARD_SCHEMA_ID = "trader1.candidate_scorecard.v1"
CANDIDATE_GENERATION_SCHEMA_ID = "trader1.candidate_generation_report.v1"
COST_FIELD_MAP = {
    "expected_fee_bps": "fee_bps",
    "expected_spread_bps": "spread_bps",
    "expected_slippage_bps": "slippage_bps",
    "expected_impact_bps": "market_impact_bps",
    "expected_latency_penalty_bps": "latency_bps",
}
ROBUSTNESS_PASS = {
    "oos_status": "PASS",
    "walk_forward_status": "PASS",
    "bootstrap_status": "PASS",
    "overfit_status": "LOW",
}
PERFORMANCE_PASS = {
    "closed_trade_status": "PASS",
    "strategy_exit_policy_status": "PASS",
    "regime_outcome_status": "PASS",
    "profit_factor_status": "PASS",
    "max_drawdown_status": "PASS",
    "realized_vs_expected_edge_status": "PASS",
    "fill_quality_status": "PASS",
    "execution_cost_comparison_status": "PASS",
}
DEFAULT_PERFORMANCE_METRICS = {
    "closed_trade_sample_count": 0,
    "min_closed_trade_sample_count": 30,
    "strategy_exit_policy_sample_count": 0,
    "min_strategy_exit_policy_sample_count": 30,
    "strategy_exit_policy_match_count": 0,
    "strategy_exit_policy_mismatch_count": 0,
    "strategy_exit_reason_count": 0,
    "strategy_exit_reason_counts": [],
    "regime_outcome_sample_count": 0,
    "min_regime_outcome_sample_count": 4,
    "regime_outcome_covered_count": 0,
    "min_regime_outcome_covered_count": 4,
    "regime_outcome_trade_count": 0,
    "regime_outcome_no_trade_count": 0,
    "regime_outcome_mismatch_count": 0,
    "regime_outcome_counts": [],
    "realized_vs_expected_sample_count": 0,
    "fill_quality_sample_count": 0,
    "execution_cost_sample_count": 0,
    "profit_factor": 0.0,
    "min_profit_factor": 1.25,
    "max_drawdown_pct": 100.0,
    "max_allowed_drawdown_pct": 8.0,
    "realized_vs_expected_edge_bps": -999.0,
    "min_realized_vs_expected_edge_bps": 0.0,
    "fill_quality_score": 0.0,
    "min_fill_quality_score": 0.80,
    "realized_fee_bps": 0.0,
    "realized_slippage_bps": 0.0,
    "realized_impact_bps": 0.0,
    "expected_total_execution_cost_bps": 0.0,
    "realized_total_execution_cost_bps": 0.0,
    "execution_cost_delta_bps": 999.0,
    "max_allowed_execution_cost_delta_bps": 2.0,
}
ROBUSTNESS_SOURCE_PREFIXES = ("oos:", "walk_forward:", "bootstrap:")
PERFORMANCE_SOURCE_PREFIXES = ("closed_trades:", "execution_quality:", "performance_summary:")
RUNTIME_CYCLE_SOURCE_PREFIX = "upbit_paper_runtime_cycle:"
TOP_SYMBOL_SCORECARD_LIMIT = 5
REGIME_OUTCOME_REGIMES = ("UPTREND", "RANGE", "DOWNTREND", "RISK_OFF")
SPOT_LONG_NEW_ENTRY_BLOCKED_REGIMES = {"DOWNTREND", "RISK_OFF"}
STRATEGY_FAMILY_EVIDENCE_ORDER = ("PULLBACK_TREND_LONG", "VWAP_MEAN_REVERSION", "BREAKOUT_RETEST_LONG")
CANDIDATE_GENERATION_ITEM_LIMIT = 20
CANDIDATE_FAILURE_TRIGGER_BLOCKERS = {
    "PUBLIC_REPLAY_ROBUSTNESS_FAILED",
    "OOS_FAILED",
    "WALK_FORWARD_FAILED",
    "BOOTSTRAP_FAILED",
    "OVERFIT_RISK_HIGH",
    "EXECUTION_FEEDBACK_DIVERGENT",
}
CANDIDATE_GENERATION_PASS_STATUSES = {"ALTERNATIVE_REVIEW_READY", "ALTERNATIVE_PUBLIC_REPLAY_VALIDATED"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def stable_json_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def safe_candidate_scorecard_filename(candidate_id: Any) -> str:
    text = str(candidate_id or "unknown-candidate")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    safe = "".join(character if character in allowed else "_" for character in text).strip("._")
    if not safe:
        safe = "unknown-candidate"
    if len(safe) > 96:
        safe = f"{safe[:80]}-{stable_hash(text)[:16]}"
    return safe


def current_authority_hashes() -> dict[str, str]:
    return {
        "trader1_sha256": sha256_file(ROOT / "TRADER_1.md"),
        "agents_sha256": sha256_file(ROOT / "AGENTS.md"),
    }


def decimal_value(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def number_value(value: Any) -> float:
    return float(decimal_value(value))


def blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def runtime_cycle_source_evidence_id(cycle_id: str, cycle_hash: str) -> str:
    return f"{RUNTIME_CYCLE_SOURCE_PREFIX}{cycle_id}:{cycle_hash}"


def robustness_source_evidence_id(prefix: str, cycle_id: str, cycle_hash: str) -> str:
    normalized = prefix[:-1] if prefix.endswith(":") else prefix
    return f"{normalized}:{cycle_id}:{cycle_hash}"


def runtime_cycle_binding_from_source_ids(source_evidence_ids: list[str] | None) -> tuple[str, str] | None:
    for source_id in source_evidence_ids or []:
        if not isinstance(source_id, str) or not source_id.startswith(RUNTIME_CYCLE_SOURCE_PREFIX):
            continue
        parts = source_id.split(":")
        if len(parts) == 3 and parts[1] and len(parts[2]) == 64:
            return parts[1], parts[2]
    return None


def has_required_robustness_source_ids(
    source_evidence_ids: list[str] | None,
    *,
    cycle_id: str | None = None,
    cycle_hash: str | None = None,
) -> bool:
    ids = source_evidence_ids or []
    if cycle_id and cycle_hash:
        required = {
            robustness_source_evidence_id(prefix, cycle_id, cycle_hash)
            for prefix in ROBUSTNESS_SOURCE_PREFIXES
        }
        return required.issubset(set(ids))
    return all(any(source_id.startswith(prefix) for source_id in ids) for prefix in ROBUSTNESS_SOURCE_PREFIXES)


def performance_source_evidence_id(prefix: str, history_id: str, history_hash: str, candidate_id: str) -> str:
    normalized = prefix[:-1] if prefix.endswith(":") else prefix
    candidate_key = safe_candidate_scorecard_filename(candidate_id or "unknown-candidate")
    return f"{normalized}:{candidate_key}:{history_id}:{history_hash}"


def has_required_performance_source_ids(
    source_evidence_ids: list[str] | None,
    *,
    candidate_id: str | None = None,
    history_id: str | None = None,
    history_hash: str | None = None,
) -> bool:
    ids = source_evidence_ids or []
    if candidate_id is None:
        return all(any(source_id.startswith(prefix) for source_id in ids) for prefix in PERFORMANCE_SOURCE_PREFIXES)

    return performance_source_binding_from_source_ids(
        ids,
        candidate_id=candidate_id,
        history_id=history_id,
        history_hash=history_hash,
    ) is not None


def performance_source_binding_from_source_ids(
    source_evidence_ids: list[str] | None,
    *,
    candidate_id: str,
    history_id: str | None = None,
    history_hash: str | None = None,
) -> tuple[str, str] | None:
    ids = source_evidence_ids or []
    candidate_key = safe_candidate_scorecard_filename(candidate_id)
    matched_binding: tuple[str, str] | None = None
    for prefix in PERFORMANCE_SOURCE_PREFIXES:
        normalized = prefix[:-1] if prefix.endswith(":") else prefix
        prefix_binding: tuple[str, str] | None = None
        for source_id in ids:
            if not isinstance(source_id, str) or not source_id.startswith(prefix):
                continue
            parts = source_id.split(":")
            if len(parts) != 4 or parts[0] != normalized:
                continue
            if parts[1] != candidate_key or len(parts[3]) != 64:
                continue
            if history_id is not None and parts[2] != history_id:
                continue
            if history_hash is not None and parts[3] != history_hash:
                continue
            current_binding = (parts[2], parts[3])
            if prefix_binding is not None and prefix_binding != current_binding:
                return None
            prefix_binding = current_binding
        if prefix_binding is None:
            return None
        current_binding = prefix_binding
        if matched_binding is None:
            matched_binding = current_binding
        elif matched_binding != current_binding:
            return None
    return matched_binding


def _threshold_status(
    *,
    observed_count: int,
    value: float,
    threshold: float,
    comparison: str,
) -> str:
    if observed_count <= 0:
        return "UNTESTED"
    if comparison == "gte":
        return "PASS" if value >= threshold else "FAIL"
    if comparison == "lte":
        return "PASS" if value <= threshold else "FAIL"
    raise ValueError(f"unsupported threshold comparison: {comparison}")


def _performance_source_evidence_ids(history_id: str, history_hash: str, candidate_id: str) -> list[str]:
    return [
        performance_source_evidence_id("closed_trades", history_id, history_hash, candidate_id),
        performance_source_evidence_id("execution_quality", history_id, history_hash, candidate_id),
        performance_source_evidence_id("performance_summary", history_id, history_hash, candidate_id),
    ]


def _clamp_float(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _load_valid_runtime_sample(
    *,
    root: Path,
    sample: dict[str, Any],
    candidate_scorecard: dict[str, Any],
) -> dict[str, Any] | None:
    path = (root / str(sample.get("source_runtime_cycle_path") or "")).resolve()
    try:
        if root.resolve() not in path.parents and path != root.resolve():
            return None
        runtime = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(runtime, dict):
        return None
    validation = validate_upbit_paper_runtime_cycle_report(runtime, require_quantitative_policy_summary=False)
    if validation.status != "PASS":
        return None
    if runtime.get("cycle_hash") != sample.get("source_runtime_cycle_hash"):
        return None
    if (
        runtime.get("exchange") != candidate_scorecard.get("exchange")
        or runtime.get("market_type") != candidate_scorecard.get("market_type")
        or runtime.get("mode") != candidate_scorecard.get("mode")
        or runtime.get("session_id") != candidate_scorecard.get("session_id")
    ):
        return None
    return runtime


def _candidate_for_closed_trade(runtime: dict[str, Any], position_lifecycle: dict[str, Any]) -> dict[str, Any] | None:
    entry_candidate_id = position_lifecycle.get("entry_candidate_id")
    for candidate in runtime.get("strategy_candidates") or []:
        if isinstance(candidate, dict) and candidate.get("candidate_id") == entry_candidate_id:
            return candidate
    selected = runtime.get("selected_candidate")
    return selected if isinstance(selected, dict) else None


def _candidate_by_id(runtime: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
    selected = runtime.get("selected_candidate")
    if isinstance(selected, dict) and selected.get("candidate_id") == candidate_id:
        return selected
    for candidate in runtime.get("strategy_candidates") or []:
        if isinstance(candidate, dict) and candidate.get("candidate_id") == candidate_id:
            return candidate
    return None


def _runtime_regime_outcome_key(runtime: dict[str, Any]) -> str:
    features = runtime.get("feature_snapshot")
    features = features if isinstance(features, dict) else {}
    regime = str(runtime.get("regime") or features.get("regime") or "").upper()
    market_state = str(features.get("market_state") or runtime.get("market_state") or regime).upper()
    if market_state == "DOWNTREND":
        return "DOWNTREND"
    if market_state in {"PANIC", "DATA_BAD"} or regime == "RISK_OFF":
        return "RISK_OFF"
    if regime == "UPTREND":
        return "UPTREND"
    if regime == "RANGE":
        return "RANGE"
    return "RISK_OFF"


def _empty_regime_outcome_counts() -> dict[str, dict[str, Any]]:
    return {
        regime: {
            "regime": regime,
            "sample_count": 0,
            "trade_count": 0,
            "no_trade_count": 0,
            "mismatch_count": 0,
            "trade_allowed": regime not in SPOT_LONG_NEW_ENTRY_BLOCKED_REGIMES,
            "primary_blocker_code": None if regime not in SPOT_LONG_NEW_ENTRY_BLOCKED_REGIMES else "RISK_VETO",
        }
        for regime in REGIME_OUTCOME_REGIMES
    }


def _record_regime_outcome_sample(
    *,
    regime_counts: dict[str, dict[str, Any]],
    regime: str,
    candidate: dict[str, Any],
    trade_observed: bool,
) -> None:
    bucket = regime_counts.setdefault(regime, _empty_regime_outcome_counts()[regime])
    bucket["sample_count"] = int(bucket.get("sample_count", 0)) + 1
    if trade_observed:
        bucket["trade_count"] = int(bucket.get("trade_count", 0)) + 1
    else:
        bucket["no_trade_count"] = int(bucket.get("no_trade_count", 0)) + 1

    candidate_decision = str(candidate.get("decision") or "")
    no_trade_reason = str(candidate.get("no_trade_reason") or candidate.get("strategy_policy_reason") or "")
    strategy_allowed = candidate.get("strategy_regime_allowed") is True
    disallowed_trade = regime in SPOT_LONG_NEW_ENTRY_BLOCKED_REGIMES and (
        trade_observed or strategy_allowed or candidate_decision == "PAPER_ENTRY_REVIEW"
    )
    if disallowed_trade:
        bucket["mismatch_count"] = int(bucket.get("mismatch_count", 0)) + 1
        bucket["primary_blocker_code"] = "RISK_VETO" if regime == "RISK_OFF" else "REGIME_MISMATCH"
    elif not trade_observed and no_trade_reason and bucket.get("primary_blocker_code") is None:
        bucket["primary_blocker_code"] = no_trade_reason


def _expected_strategy_exit_variation(strategy_family: Any) -> str:
    mapping = {
        "PULLBACK_TREND_LONG": TREND_PULLBACK_EXIT_VARIATION,
        "VWAP_MEAN_REVERSION": VWAP_REVERSION_EXIT_VARIATION,
        "BREAKOUT_RETEST_LONG": BREAKOUT_RETEST_EXIT_VARIATION,
    }
    return mapping.get(str(strategy_family or ""), "")


def _strategy_exit_policy_sample(
    *,
    lifecycle: dict[str, Any],
    expected_exit_variation: str,
) -> tuple[bool, str | None]:
    policy_id = str(lifecycle.get("strategy_exit_policy_id") or "")
    exit_variation = str(lifecycle.get("strategy_exit_variation") or "")
    entry_exit_variation = str(lifecycle.get("entry_strategy_exit_variation") or "")
    reason_code = str(lifecycle.get("strategy_exit_reason_code") or lifecycle.get("position_exit_reason_code") or "")
    nested_evaluation = lifecycle.get("position_exit_evaluation")
    nested_evaluation = nested_evaluation if isinstance(nested_evaluation, dict) else {}
    action = str(lifecycle.get("strategy_exit_action") or nested_evaluation.get("strategy_exit_action") or "")
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


def _runtime_fill_matches_scorecard_candidate(
    *,
    runtime: dict[str, Any],
    fill: dict[str, Any],
    position_lifecycle: dict[str, Any] | None,
    candidate_scorecard: dict[str, Any],
) -> bool:
    target_candidate_id = str(candidate_scorecard.get("candidate_id") or "")
    if not target_candidate_id:
        return False
    side = fill.get("side")
    if side == "BUY":
        selected = runtime.get("selected_candidate")
        return (
            isinstance(selected, dict)
            and selected.get("candidate_id") == target_candidate_id
            and runtime.get("final_decision") == "ENTER_LONG"
        )
    if side == "SELL" and isinstance(position_lifecycle, dict):
        entry_candidate_id = position_lifecycle.get("entry_candidate_id")
        if isinstance(entry_candidate_id, str) and entry_candidate_id:
            return entry_candidate_id == target_candidate_id
        closed_candidate = _candidate_for_closed_trade(runtime, position_lifecycle)
        return isinstance(closed_candidate, dict) and closed_candidate.get("candidate_id") == target_candidate_id
    return False


def _paper_fill_execution_cost_comparison(fill: dict[str, Any]) -> dict[str, Decimal]:
    filled_notional = decimal_value(fill.get("filled_notional"))
    fee_amount = decimal_value(fill.get("fee_amount"))
    realized_fee = (
        fee_amount / filled_notional * Decimal("10000")
        if filled_notional > 0 and fee_amount >= 0
        else decimal_value(fill.get("fee_bps"))
    )
    realized_slippage = decimal_value(fill.get("slippage_bps"))
    realized_impact = decimal_value(fill.get("market_impact_bps"))
    expected_fee = decimal_value(fill.get("fee_bps"))
    if expected_fee <= 0:
        expected_fee = decimal_value(fill.get("fee_rate")) * Decimal("10000")
    expected_spread = decimal_value(fill.get("effective_spread_bps"))
    if expected_spread <= 0:
        expected_spread = decimal_value(fill.get("spread_bps"))
    expected_slippage = decimal_value(fill.get("adaptive_slippage_bps"))
    expected_impact = decimal_value(fill.get("market_impact_bps"))
    expected_latency = decimal_value(fill.get("latency_penalty_bps"))
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


def _paper_sell_fill_realized_delta(fill: dict[str, Any], lifecycle: dict[str, Any]) -> Decimal | None:
    quantity = decimal_value(fill.get("filled_quantity") or fill.get("quantity"))
    fill_price = decimal_value(fill.get("fill_price"))
    fee_amount = decimal_value(fill.get("fee_amount"))
    managed_quantity = decimal_value(lifecycle.get("managed_position_quantity"))
    managed_cost_basis = decimal_value(lifecycle.get("managed_position_cost_basis"))
    if min(quantity, fill_price, managed_quantity, managed_cost_basis) <= 0 or quantity > managed_quantity:
        return None
    allocated_cost_basis = managed_cost_basis * (quantity / managed_quantity)
    return (quantity * fill_price) - allocated_cost_basis - fee_amount


def performance_inputs_from_runtime_sample_history(
    *,
    candidate_scorecard: dict[str, Any],
    runtime_sample_history: dict[str, Any],
    root: Path,
) -> tuple[dict[str, str], dict[str, Any], list[str]]:
    root = Path(root).resolve()
    history_id = str(runtime_sample_history.get("history_id") or "unknown_history")
    history_hash = str(runtime_sample_history.get("history_hash") or "missing_hash")
    source_ids = _performance_source_evidence_ids(
        history_id,
        history_hash,
        str(candidate_scorecard.get("candidate_id") or ""),
    )

    candidate_realized_pnl_baseline: Decimal | None = None
    starting_cash: Decimal | None = None
    candidate_cumulative_realized_pnl = Decimal("0")
    candidate_realized_pnl_peak = Decimal("0")
    max_drawdown_pct = Decimal("0")
    closed_trade_count = 0
    gross_profit = Decimal("0")
    gross_loss = Decimal("0")
    realized_vs_expected_values: list[Decimal] = []
    fill_quality_values: list[Decimal] = []
    realized_fee_values: list[Decimal] = []
    realized_slippage_values: list[Decimal] = []
    realized_impact_values: list[Decimal] = []
    expected_total_cost_values: list[Decimal] = []
    realized_total_cost_values: list[Decimal] = []
    execution_cost_delta_values: list[Decimal] = []
    strategy_exit_policy_sample_count = 0
    strategy_exit_policy_match_count = 0
    strategy_exit_policy_mismatch_count = 0
    strategy_exit_reason_counts: dict[str, int] = {}
    regime_counts = _empty_regime_outcome_counts()
    target_candidate_id = str(candidate_scorecard.get("candidate_id") or "")

    for sample in runtime_sample_history.get("samples") or []:
        if not isinstance(sample, dict):
            continue
        runtime = _load_valid_runtime_sample(root=root, sample=sample, candidate_scorecard=candidate_scorecard)
        if runtime is None:
            continue
        runtime_regime = _runtime_regime_outcome_key(runtime)
        runtime_candidate = _candidate_by_id(runtime, target_candidate_id)
        portfolio = runtime.get("paper_portfolio_snapshot")
        if isinstance(portfolio, dict):
            candidate_starting_cash = decimal_value(portfolio.get("starting_cash"))
            if candidate_starting_cash > 0:
                starting_cash = candidate_starting_cash if starting_cash is None else starting_cash
            current_realized = decimal_value(portfolio.get("realized_pnl"))
        else:
            current_realized = candidate_realized_pnl_baseline if candidate_realized_pnl_baseline is not None else Decimal("0")

        fill = runtime.get("paper_fill")
        lifecycle = runtime.get("position_management_decision")
        candidate_fill = (
            _runtime_fill_matches_scorecard_candidate(
                runtime=runtime,
                fill=fill,
                position_lifecycle=lifecycle if isinstance(lifecycle, dict) else None,
                candidate_scorecard=candidate_scorecard,
            )
            if isinstance(fill, dict)
            else False
        )
        trade_observed = (
            isinstance(fill, dict)
            and fill.get("side") in {"BUY", "SELL"}
            and candidate_fill
            and runtime.get("final_decision") in {"ENTER_LONG", "EXIT_POSITION", "REDUCE_POSITION"}
        )
        if isinstance(runtime_candidate, dict):
            _record_regime_outcome_sample(
                regime_counts=regime_counts,
                regime=runtime_regime,
                candidate=runtime_candidate,
                trade_observed=trade_observed,
            )
        if isinstance(fill, dict) and fill.get("side") in {"BUY", "SELL"} and candidate_fill:
            execution_cost = _paper_fill_execution_cost_comparison(fill)
            expected_total = execution_cost["expected_total_execution_cost_bps"]
            cost_delta = execution_cost["execution_cost_delta_bps"]
            denominator = max(Decimal("1"), expected_total)
            quality = Decimal(str(_clamp_float(float(Decimal("1") - max(Decimal("0"), cost_delta) / denominator))))
            fill_quality_values.append(quality)
            realized_fee_values.append(execution_cost["realized_fee_bps"])
            realized_slippage_values.append(execution_cost["realized_slippage_bps"])
            realized_impact_values.append(execution_cost["realized_impact_bps"])
            expected_total_cost_values.append(expected_total)
            realized_total_cost_values.append(execution_cost["realized_total_execution_cost_bps"])
            execution_cost_delta_values.append(cost_delta)

        sell_policy_observed = (
            isinstance(fill, dict)
            and isinstance(lifecycle, dict)
            and fill.get("side") == "SELL"
            and runtime.get("final_decision") in {"EXIT_POSITION", "REDUCE_POSITION"}
            and candidate_fill
        )
        closed_candidate = _candidate_for_closed_trade(runtime, lifecycle) if sell_policy_observed else None
        if sell_policy_observed:
            expected_exit_variation = _expected_strategy_exit_variation(
                closed_candidate.get("strategy_family") if isinstance(closed_candidate, dict) else None
            )
            policy_matched, exit_reason = _strategy_exit_policy_sample(
                lifecycle=lifecycle,
                expected_exit_variation=expected_exit_variation,
            )
            strategy_exit_policy_sample_count += 1
            if policy_matched:
                strategy_exit_policy_match_count += 1
            else:
                strategy_exit_policy_mismatch_count += 1
            if exit_reason:
                strategy_exit_reason_counts[exit_reason] = strategy_exit_reason_counts.get(exit_reason, 0) + 1

        if candidate_fill and isinstance(fill, dict) and fill.get("side") == "BUY":
            candidate_realized_pnl_baseline = current_realized

        if sell_policy_observed and runtime.get("final_decision") == "EXIT_POSITION":
            direct_realized_delta = _paper_sell_fill_realized_delta(fill, lifecycle)
            if direct_realized_delta is not None:
                realized_delta = direct_realized_delta
            elif candidate_realized_pnl_baseline is not None:
                realized_delta = current_realized - candidate_realized_pnl_baseline
            else:
                continue
            closed_trade_count += 1
            if realized_delta >= 0:
                gross_profit += realized_delta
            else:
                gross_loss += abs(realized_delta)
            filled_notional = max(Decimal("1"), decimal_value(fill.get("filled_notional")))
            realized_bps = realized_delta / filled_notional * Decimal("10000")
            expected_bps = decimal_value(closed_candidate.get("net_ev_after_cost_bps")) if isinstance(closed_candidate, dict) else Decimal("0")
            realized_vs_expected_values.append(realized_bps - expected_bps)
            candidate_cumulative_realized_pnl += realized_delta
            candidate_realized_pnl_peak = max(candidate_realized_pnl_peak, candidate_cumulative_realized_pnl)
            drawdown_denominator = max(Decimal("1"), starting_cash or filled_notional)
            drawdown = max(
                Decimal("0"),
                (candidate_realized_pnl_peak - candidate_cumulative_realized_pnl) / drawdown_denominator * Decimal("100"),
            )
            max_drawdown_pct = max(max_drawdown_pct, drawdown)
            candidate_realized_pnl_baseline = current_realized

    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0 and closed_trade_count > 0:
        profit_factor = Decimal("999")
    else:
        profit_factor = Decimal("0")
    realized_vs_expected = (
        sum(realized_vs_expected_values, Decimal("0")) / Decimal(len(realized_vs_expected_values))
        if realized_vs_expected_values
        else Decimal("-999")
    )
    fill_quality = (
        sum(fill_quality_values, Decimal("0")) / Decimal(len(fill_quality_values))
        if fill_quality_values
        else Decimal("0")
    )
    realized_fee = (
        sum(realized_fee_values, Decimal("0")) / Decimal(len(realized_fee_values))
        if realized_fee_values
        else Decimal("0")
    )
    realized_slippage = (
        sum(realized_slippage_values, Decimal("0")) / Decimal(len(realized_slippage_values))
        if realized_slippage_values
        else Decimal("0")
    )
    realized_impact = (
        sum(realized_impact_values, Decimal("0")) / Decimal(len(realized_impact_values))
        if realized_impact_values
        else Decimal("0")
    )
    expected_total_cost = (
        sum(expected_total_cost_values, Decimal("0")) / Decimal(len(expected_total_cost_values))
        if expected_total_cost_values
        else Decimal("0")
    )
    realized_total_cost = (
        sum(realized_total_cost_values, Decimal("0")) / Decimal(len(realized_total_cost_values))
        if realized_total_cost_values
        else Decimal("0")
    )
    execution_cost_delta = (
        sum(execution_cost_delta_values, Decimal("0")) / Decimal(len(execution_cost_delta_values))
        if execution_cost_delta_values
        else Decimal("999")
    )
    regime_outcome_counts = list(regime_counts.values())
    regime_outcome_sample_count = sum(int(item["sample_count"]) for item in regime_outcome_counts)
    regime_outcome_trade_count = sum(int(item["trade_count"]) for item in regime_outcome_counts)
    regime_outcome_no_trade_count = sum(int(item["no_trade_count"]) for item in regime_outcome_counts)
    regime_outcome_mismatch_count = sum(int(item["mismatch_count"]) for item in regime_outcome_counts)
    regime_outcome_covered_count = sum(1 for item in regime_outcome_counts if int(item["sample_count"]) > 0)
    metrics = dict(DEFAULT_PERFORMANCE_METRICS)
    metrics.update(
        {
            "closed_trade_sample_count": closed_trade_count,
            "strategy_exit_policy_sample_count": strategy_exit_policy_sample_count,
            "strategy_exit_policy_match_count": strategy_exit_policy_match_count,
            "strategy_exit_policy_mismatch_count": strategy_exit_policy_mismatch_count,
            "strategy_exit_reason_count": sum(strategy_exit_reason_counts.values()),
            "strategy_exit_reason_counts": [
                {"reason_code": reason_code, "count": count}
                for reason_code, count in sorted(strategy_exit_reason_counts.items())
            ],
            "regime_outcome_sample_count": regime_outcome_sample_count,
            "regime_outcome_covered_count": regime_outcome_covered_count,
            "regime_outcome_trade_count": regime_outcome_trade_count,
            "regime_outcome_no_trade_count": regime_outcome_no_trade_count,
            "regime_outcome_mismatch_count": regime_outcome_mismatch_count,
            "regime_outcome_counts": regime_outcome_counts,
            "realized_vs_expected_sample_count": len(realized_vs_expected_values),
            "fill_quality_sample_count": len(fill_quality_values),
            "execution_cost_sample_count": len(execution_cost_delta_values),
            "profit_factor": float(profit_factor),
            "max_drawdown_pct": float(max_drawdown_pct),
            "realized_vs_expected_edge_bps": float(realized_vs_expected),
            "fill_quality_score": float(fill_quality),
            "realized_fee_bps": float(realized_fee),
            "realized_slippage_bps": float(realized_slippage),
            "realized_impact_bps": float(realized_impact),
            "expected_total_execution_cost_bps": float(expected_total_cost),
            "realized_total_execution_cost_bps": float(realized_total_cost),
            "execution_cost_delta_bps": float(execution_cost_delta),
        }
    )
    closed_trade_observed = int(metrics["closed_trade_sample_count"])
    strategy_exit_policy_observed = int(metrics["strategy_exit_policy_sample_count"])
    regime_outcome_observed = int(metrics["regime_outcome_sample_count"])
    realized_vs_expected_observed = int(metrics["realized_vs_expected_sample_count"])
    fill_quality_observed = int(metrics["fill_quality_sample_count"])
    execution_cost_observed = int(metrics["execution_cost_sample_count"])
    statuses = {
        "closed_trade_status": _threshold_status(
            observed_count=closed_trade_observed,
            value=float(metrics["closed_trade_sample_count"]),
            threshold=float(metrics["min_closed_trade_sample_count"]),
            comparison="gte",
        ),
        "strategy_exit_policy_status": (
            "UNTESTED"
            if strategy_exit_policy_observed <= 0
            else "PASS"
            if (
                strategy_exit_policy_observed >= int(metrics["min_strategy_exit_policy_sample_count"])
                and int(metrics["strategy_exit_policy_mismatch_count"]) == 0
                and int(metrics["strategy_exit_policy_match_count"]) >= int(metrics["min_strategy_exit_policy_sample_count"])
            )
            else "FAIL"
        ),
        "regime_outcome_status": (
            "UNTESTED"
            if regime_outcome_observed <= 0
            else "PASS"
            if (
                regime_outcome_observed >= int(metrics["min_regime_outcome_sample_count"])
                and int(metrics["regime_outcome_covered_count"]) >= int(metrics["min_regime_outcome_covered_count"])
                and int(metrics["regime_outcome_mismatch_count"]) == 0
            )
            else "FAIL"
        ),
        "profit_factor_status": _threshold_status(
            observed_count=closed_trade_observed,
            value=float(metrics["profit_factor"]),
            threshold=float(metrics["min_profit_factor"]),
            comparison="gte",
        ),
        "max_drawdown_status": _threshold_status(
            observed_count=closed_trade_observed,
            value=float(metrics["max_drawdown_pct"]),
            threshold=float(metrics["max_allowed_drawdown_pct"]),
            comparison="lte",
        ),
        "realized_vs_expected_edge_status": _threshold_status(
            observed_count=realized_vs_expected_observed,
            value=float(metrics["realized_vs_expected_edge_bps"]),
            threshold=float(metrics["min_realized_vs_expected_edge_bps"]),
            comparison="gte",
        ),
        "fill_quality_status": _threshold_status(
            observed_count=fill_quality_observed,
            value=float(metrics["fill_quality_score"]),
            threshold=float(metrics["min_fill_quality_score"]),
            comparison="gte",
        ),
        "execution_cost_comparison_status": _threshold_status(
            observed_count=execution_cost_observed,
            value=float(metrics["execution_cost_delta_bps"]),
            threshold=float(metrics["max_allowed_execution_cost_delta_bps"]),
            comparison="lte",
        ),
    }
    return statuses, metrics, source_ids


def strategy_id_for_family(strategy_family: str) -> str:
    mapping = {
        "PULLBACK_TREND_LONG": "trend_pullback",
        "BREAKOUT_RETEST_LONG": "breakout_retest",
        "VWAP_MEAN_REVERSION": "vwap_mean_reversion",
    }
    return mapping.get(strategy_family, strategy_family.lower())


def expected_strategy_exit_variation_for_family(strategy_family: str) -> str:
    return _expected_strategy_exit_variation(strategy_family)


def regime_scope_for_runtime_regime(regime: str) -> str:
    mapping = {
        "UPTREND": "TRENDING",
        "RANGE": "RANGE",
        "RISK_OFF": "RISK_OFF",
    }
    return mapping.get(regime, "RISK_OFF")


def _candidate_scorecard_rank_key(candidate: dict[str, Any]) -> tuple[Decimal, Decimal, int, str]:
    return (
        decimal_value(candidate.get("candidate_selection_score")),
        decimal_value(candidate.get("net_ev_after_cost_bps")),
        -int(candidate.get("selection_priority", 999)),
        str(candidate.get("candidate_id") or ""),
    )


def _scorecard_candidate_from_runtime(runtime_cycle_report: dict[str, Any]) -> dict[str, Any]:
    focused = _paper_scope_focus_candidate_from_runtime(runtime_cycle_report)
    if focused is not None:
        return focused
    selected = runtime_cycle_report["selected_candidate"]
    if selected.get("decision") == "PAPER_ENTRY_REVIEW":
        return selected

    entry_candidates = [
        candidate
        for candidate in runtime_cycle_report.get("strategy_candidates") or []
        if isinstance(candidate, dict)
        and candidate.get("decision") == "PAPER_ENTRY_REVIEW"
        and isinstance(candidate.get("candidate_id"), str)
        and candidate.get("live_order_ready") is False
        and candidate.get("live_order_allowed") is False
        and candidate.get("can_live_trade") is False
        and candidate.get("scale_up_allowed") is False
    ]
    if not entry_candidates:
        return selected
    return max(entry_candidates, key=_candidate_scorecard_rank_key)


def _candidate_is_non_live(candidate: dict[str, Any]) -> bool:
    return (
        candidate.get("live_order_ready") is False
        and candidate.get("live_order_allowed") is False
        and candidate.get("can_live_trade") is False
        and candidate.get("scale_up_allowed") is False
    )


def _entry_review_candidates(runtime_cycle_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        candidate
        for candidate in runtime_cycle_report.get("strategy_candidates") or []
        if isinstance(candidate, dict)
        and candidate.get("decision") == "PAPER_ENTRY_REVIEW"
        and isinstance(candidate.get("candidate_id"), str)
        and _candidate_is_non_live(candidate)
    ]


def _top_symbol_evidence_scorecards(runtime_cycle_report: dict[str, Any]) -> list[dict[str, Any]]:
    raw_scorecards = [
        scorecard
        for scorecard in runtime_cycle_report.get("symbol_evidence_scorecards") or []
        if isinstance(scorecard, dict)
        and isinstance(scorecard.get("symbol"), str)
        and not any(
            scorecard.get(flag) is True
            for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
        )
    ]
    sorted_scorecards = sorted(
        raw_scorecards,
        key=lambda scorecard: (
            decimal_value(scorecard.get("best_net_ev_after_cost_bps")),
            decimal_value(scorecard.get("best_candidate_selection_score")),
            -int(scorecard.get("rank_input_order", 999) or 999),
            str(scorecard.get("symbol") or ""),
        ),
        reverse=True,
    )
    compact: list[dict[str, Any]] = []
    for scorecard in sorted_scorecards[:TOP_SYMBOL_SCORECARD_LIMIT]:
        compact.append(
            {
                "symbol": scorecard["symbol"],
                "rank_input_order": int(scorecard.get("rank_input_order", 0) or 0),
                "best_candidate_id": scorecard.get("best_candidate_id"),
                "best_strategy_family": scorecard.get("best_strategy_family"),
                "best_decision": scorecard.get("best_decision"),
                "best_net_ev_after_cost_bps": number_value(scorecard.get("best_net_ev_after_cost_bps")),
                "symbol_selection_score": number_value(scorecard.get("symbol_selection_score")),
                "base_symbol_selection_score": number_value(scorecard.get("base_symbol_selection_score")),
                "correlation_cluster_status": scorecard.get("correlation_cluster_status"),
                "correlation_cluster_leader_symbol": scorecard.get("correlation_cluster_leader_symbol"),
                "correlation_cluster_rank": int(scorecard.get("correlation_cluster_rank", 0) or 0),
                "correlation_max_peer_symbol": scorecard.get("correlation_max_peer_symbol"),
                "correlation_max_abs": number_value(scorecard.get("correlation_max_abs")),
                "correlation_penalty": number_value(scorecard.get("correlation_penalty")),
                "adaptive_top_n": int(scorecard.get("adaptive_top_n", 0) or 0),
                "rank_after_correlation": int(scorecard.get("rank_after_correlation", 0) or 0),
                "adaptive_top_n_filter_status": scorecard.get("adaptive_top_n_filter_status"),
                "eligible_after_correlation": bool(scorecard.get("eligible_after_correlation")),
                "no_trade_reasons": [
                    str(reason)
                    for reason in (scorecard.get("no_trade_reasons") or [])
                    if reason
                ],
                "paper_entry_review_candidate_count": int(
                    scorecard.get("paper_entry_review_candidate_count", 0) or 0
                ),
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
    return compact


def _candidate_family_evidence_rank_key(candidate: dict[str, Any]) -> tuple[Decimal, Decimal, int, str, str]:
    return (
        decimal_value(candidate.get("net_ev_after_cost_bps")),
        decimal_value(candidate.get("candidate_selection_score")),
        -int(candidate.get("selection_priority", 999) or 999),
        str(candidate.get("symbol") or ""),
        str(candidate.get("candidate_id") or ""),
    )


def _strategy_family_evidence_scorecards(runtime_cycle_report: dict[str, Any]) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = {family: [] for family in STRATEGY_FAMILY_EVIDENCE_ORDER}
    for candidate in runtime_cycle_report.get("strategy_candidates") or []:
        if not isinstance(candidate, dict) or not _candidate_is_non_live(candidate):
            continue
        family = str(candidate.get("strategy_family") or "")
        if family in by_family:
            by_family[family].append(candidate)

    compact: list[dict[str, Any]] = []
    for family in STRATEGY_FAMILY_EVIDENCE_ORDER:
        candidates = by_family[family]
        if not candidates:
            compact.append(
                {
                    "strategy_family": family,
                    "strategy_id": strategy_id_for_family(family),
                    "evaluated_candidate_count": 0,
                    "paper_entry_review_candidate_count": 0,
                    "best_candidate_id": None,
                    "best_symbol": None,
                    "best_decision": None,
                    "best_no_trade_reason": "FAMILY_NOT_EVALUATED",
                    "best_strategy_policy_reason": "FAMILY_NOT_EVALUATED",
                    "best_net_ev_after_cost_bps": 0.0,
                    "best_candidate_selection_score": 0.0,
                    "no_trade_reasons": ["FAMILY_NOT_EVALUATED"],
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }
            )
            continue

        best = max(candidates, key=_candidate_family_evidence_rank_key)
        no_trade_reasons = sorted(
            {
                str(candidate.get("no_trade_reason") or candidate.get("strategy_policy_reason") or "")
                for candidate in candidates
                if candidate.get("decision") != "PAPER_ENTRY_REVIEW"
                and (candidate.get("no_trade_reason") or candidate.get("strategy_policy_reason"))
            }
        )
        compact.append(
            {
                "strategy_family": family,
                "strategy_id": strategy_id_for_family(family),
                "evaluated_candidate_count": len(candidates),
                "paper_entry_review_candidate_count": sum(
                    1 for candidate in candidates if candidate.get("decision") == "PAPER_ENTRY_REVIEW"
                ),
                "best_candidate_id": best.get("candidate_id"),
                "best_symbol": best.get("symbol"),
                "best_decision": best.get("decision"),
                "best_no_trade_reason": best.get("no_trade_reason"),
                "best_strategy_policy_reason": best.get("strategy_policy_reason"),
                "best_net_ev_after_cost_bps": number_value(best.get("net_ev_after_cost_bps")),
                "best_candidate_selection_score": number_value(best.get("candidate_selection_score")),
                "no_trade_reasons": no_trade_reasons,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
    return compact


def _best_alternative_candidate(
    runtime_cycle_report: dict[str, Any],
    selected_candidate_id: str,
) -> dict[str, Any] | None:
    alternatives = [
        candidate
        for candidate in _entry_review_candidates(runtime_cycle_report)
        if candidate.get("candidate_id") != selected_candidate_id
    ]
    if not alternatives:
        return None
    return max(alternatives, key=_candidate_scorecard_rank_key)


def _paper_scope_focus_candidate_from_runtime(runtime_cycle_report: dict[str, Any]) -> dict[str, Any] | None:
    continuity = runtime_cycle_report.get("paper_scope_continuity_decision")
    if not isinstance(continuity, dict):
        return None
    if continuity.get("selection_status") != "MANAGED_POSITION_OVERRIDES_SCOPE_FOCUS":
        return None
    if continuity.get("requested") is not True:
        return None

    requested_candidate_id = str(continuity.get("requested_candidate_id") or "")
    requested_symbol = str(continuity.get("requested_symbol") or "")
    requested_strategy_id = str(continuity.get("requested_strategy_id") or "")
    requested_parameter_hash = str(continuity.get("requested_parameter_hash") or "").upper()
    if not requested_candidate_id:
        return None

    for candidate in runtime_cycle_report.get("strategy_candidates") or []:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("candidate_id") != requested_candidate_id:
            continue
        if candidate.get("decision") != "PAPER_ENTRY_REVIEW":
            return None
        if not _candidate_is_non_live(candidate):
            return None
        candidate_symbol = str(candidate.get("symbol") or "")
        strategy_family = str(candidate.get("strategy_family") or "")
        candidate_strategy_id = strategy_id_for_family(strategy_family) if strategy_family else ""
        candidate_parameter_hash = stable_hash(f"{candidate['candidate_id']}:{strategy_family}:{candidate_symbol}")
        if requested_symbol and candidate_symbol != requested_symbol:
            return None
        if requested_strategy_id and candidate_strategy_id != requested_strategy_id:
            return None
        if requested_parameter_hash and requested_parameter_hash != candidate_parameter_hash:
            return None
        return candidate
    return None


def _rotation_review_reason(
    *,
    selected: dict[str, Any],
    net_ev: float,
    min_required_edge_bps: float,
    robustness_ready: bool,
    enough_robustness_sources: bool,
    performance_ready: bool,
    enough_performance_sources: bool,
    ranking_eligible: bool,
    has_alternative: bool,
) -> str:
    if not has_alternative or ranking_eligible:
        return "NONE"
    if selected.get("decision") != "PAPER_ENTRY_REVIEW":
        return "SELECTED_CANDIDATE_NOT_ENTRY_REVIEW_WITH_ALTERNATIVE"
    if net_ev < min_required_edge_bps:
        return "SELECTED_CANDIDATE_MIN_EDGE_FAIL_WITH_ALTERNATIVE"
    if not robustness_ready:
        return "SELECTED_CANDIDATE_ROBUSTNESS_BLOCKED_WITH_ALTERNATIVE"
    if not enough_robustness_sources:
        return "SELECTED_CANDIDATE_ROBUSTNESS_SOURCE_MISSING_WITH_ALTERNATIVE"
    if not performance_ready:
        return "SELECTED_CANDIDATE_CLOSED_TRADE_PERFORMANCE_BLOCKED_WITH_ALTERNATIVE"
    if not enough_performance_sources:
        return "SELECTED_CANDIDATE_PERFORMANCE_SOURCE_MISSING_WITH_ALTERNATIVE"
    return "SELECTED_CANDIDATE_RANKING_BLOCKED_WITH_ALTERNATIVE"


def _has_public_replay_robustness_source(source_ids: list[str]) -> bool:
    return any(str(source_id).startswith("public_replay_robustness:") for source_id in source_ids)


def _robustness_failure_blocker(
    *,
    status: str,
    missing_code: str,
    failed_code: str,
    missing_message: str,
    failed_message: str,
) -> dict[str, str]:
    if status == "FAIL":
        return blocker(failed_code, failed_message)
    return blocker(missing_code, missing_message)


def candidate_generation_report_hash(report: dict[str, Any]) -> str:
    return stable_json_hash({key: value for key, value in report.items() if key != "generation_hash"})


def _scorecard_source_id_for_candidate_generation(scorecard: dict[str, Any]) -> str:
    return f"candidate_scorecard:{scorecard.get('scorecard_id')}:{stable_json_hash(scorecard)}"


def _candidate_generation_item(
    candidate: dict[str, Any],
    *,
    status: str,
    reason_code: str,
    priority: int,
    candidate_source_role: str,
    source_runtime_cycle_id: str,
    source_runtime_cycle_hash: str,
) -> dict[str, Any]:
    family = str(candidate.get("strategy_family") or "")
    symbol = str(candidate.get("symbol") or "")
    candidate_id = str(candidate.get("candidate_id") or "")
    return {
        "candidate_id": candidate_id,
        "symbol": symbol,
        "strategy_id": strategy_id_for_family(family),
        "strategy_family": family,
        "decision": str(candidate.get("decision") or "NO_TRADE"),
        "candidate_status": status,
        "reason_code": reason_code,
        "candidate_source_role": candidate_source_role,
        "source_runtime_cycle_id": source_runtime_cycle_id,
        "source_runtime_cycle_hash": source_runtime_cycle_hash,
        "priority": max(1, priority),
        "net_ev_after_cost_bps": number_value(candidate.get("net_ev_after_cost_bps")),
        "candidate_selection_score": number_value(candidate.get("candidate_selection_score")),
        "strategy_policy_reason": str(candidate.get("strategy_policy_reason") or ""),
        "no_trade_reason": (
            str(candidate.get("no_trade_reason"))
            if candidate.get("no_trade_reason") is not None
            else None
        ),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _candidate_generation_rank_key(item: dict[str, Any]) -> tuple[int, Decimal, Decimal, int, str]:
    status_rank = 2 if item.get("candidate_status") == "REVIEW_READY" else 1
    return (
        status_rank,
        decimal_value(item.get("net_ev_after_cost_bps")),
        decimal_value(item.get("candidate_selection_score")),
        -int(item.get("priority", 999) or 999),
        str(item.get("candidate_id") or ""),
    )


def _dedupe_candidate_generation_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(items, key=_candidate_generation_rank_key, reverse=True):
        candidate_id = str(item.get("candidate_id") or "")
        if not candidate_id or candidate_id in seen:
            continue
        seen.add(candidate_id)
        deduped.append(item)
    return deduped


def _public_replay_source_evidence_ids(report: dict[str, Any]) -> list[str]:
    replay_id = str(report.get("replay_id") or "")
    report_hash = str(report.get("report_hash") or "").upper()
    symbol = str(report.get("symbol") or "")
    market_hash = str(report.get("public_market_data_hash") or "").upper()
    source_ids: list[str] = []
    if replay_id and len(report_hash) == 64:
        source_ids.append(f"public_replay_robustness:{replay_id}:{report_hash}")
    if symbol and len(market_hash) == 64:
        source_ids.append(f"public_market_data:{symbol}:{market_hash}")
    return source_ids


def _best_alternative_replay_binding(
    *,
    best: dict[str, Any] | None,
    replay_report: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, str] | None]:
    binding = {
        "best_alternative_public_replay_status": "NOT_RUN",
        "best_alternative_public_replay_replay_id": None,
        "best_alternative_public_replay_report_hash": None,
        "best_alternative_public_replay_sample_count": 0,
        "best_alternative_public_replay_primary_blocker_code": None,
        "best_alternative_public_replay_source_evidence_ids": [],
    }
    if replay_report is None:
        return binding, None
    binding.update(
        {
            "best_alternative_public_replay_status": "BLOCKED",
            "best_alternative_public_replay_replay_id": replay_report.get("replay_id"),
            "best_alternative_public_replay_report_hash": replay_report.get("report_hash"),
            "best_alternative_public_replay_sample_count": int(replay_report.get("sample_count") or 0),
            "best_alternative_public_replay_primary_blocker_code": replay_report.get("primary_blocker_code"),
            "best_alternative_public_replay_source_evidence_ids": _public_replay_source_evidence_ids(replay_report),
        }
    )
    if best is None:
        return binding, blocker("SNAPSHOT_SCOPE_MISMATCH", "Alternative replay was supplied without a best alternative candidate.")
    if any(replay_report.get(flag) is True for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        return binding, blocker("LIVE_FINAL_GUARD_FAILED", "Alternative replay attempted live or scale-up permission.")
    if replay_report.get("exchange") != "UPBIT" or replay_report.get("market_type") != "KRW_SPOT" or replay_report.get("mode") != "REPLAY":
        return binding, blocker("SNAPSHOT_SCOPE_MISMATCH", "Alternative replay report is outside UPBIT/KRW_SPOT/REPLAY scope.")
    if replay_report.get("replay_status") != "PASS":
        return binding, blocker(
            str(replay_report.get("primary_blocker_code") or "PUBLIC_REPLAY_ROBUSTNESS_FAILED"),
            "Best alternative public replay robustness did not pass.",
        )
    expected_parameter_hash = stable_hash(f"{best['candidate_id']}:{best['strategy_family']}:{best['symbol']}")
    for report_field, expected in (
        ("candidate_id", best["candidate_id"]),
        ("symbol", best["symbol"]),
        ("strategy_id", best["strategy_id"]),
        ("parameter_hash", expected_parameter_hash),
    ):
        if str(replay_report.get(report_field) or "") != str(expected):
            return binding, blocker("SNAPSHOT_SCOPE_MISMATCH", f"Alternative replay candidate scope mismatch: {report_field}.")
    if str(replay_report.get("report_hash") or "").upper() != public_replay_robustness_report_hash(replay_report):
        return binding, blocker("SCHEMA_IDENTITY_MISMATCH", "Alternative replay report hash mismatch.")
    if int(replay_report.get("sample_count") or 0) < int(replay_report.get("min_required_sample_count") or 1):
        return binding, blocker("SAMPLE_INSUFFICIENT", "Alternative replay sample count is below the required minimum.")
    binding["best_alternative_public_replay_status"] = "PASS"
    binding["best_alternative_public_replay_primary_blocker_code"] = None
    return binding, None


def candidate_generation_report_from_upbit_paper_runtime_cycle(
    runtime_cycle_report: dict[str, Any],
    *,
    candidate_scorecard: dict[str, Any],
    candidate_budget: int = CANDIDATE_GENERATION_ITEM_LIMIT,
    authority: dict[str, str] | None = None,
    additional_runtime_cycle_reports: list[dict[str, Any]] | None = None,
    best_alternative_public_replay_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if any(candidate_scorecard.get(flag) is True for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        raise ValueError("candidate generation refuses scorecard live or scale-up permission")
    if (
        runtime_cycle_report.get("exchange") != "UPBIT"
        or runtime_cycle_report.get("market_type") != "KRW_SPOT"
        or runtime_cycle_report.get("mode") != "PAPER"
        or candidate_scorecard.get("exchange") != "UPBIT"
        or candidate_scorecard.get("market_type") != "KRW_SPOT"
        or candidate_scorecard.get("mode") != "PAPER"
    ):
        raise ValueError("candidate generation is scoped to UPBIT/KRW_SPOT/PAPER")

    selected_candidate_id = str(candidate_scorecard.get("candidate_id") or "")
    min_required_edge = decimal_value(candidate_scorecard.get("min_required_edge_bps"))
    blocker_codes = [
        str(item.get("code"))
        for item in candidate_scorecard.get("blockers", [])
        if isinstance(item, dict) and item.get("code")
    ]
    failed_current_candidate = bool(set(blocker_codes) & CANDIDATE_FAILURE_TRIGGER_BLOCKERS)
    safe_budget = max(1, min(int(candidate_budget), CANDIDATE_GENERATION_ITEM_LIMIT))

    items: list[dict[str, Any]] = []
    live_flag_drift_count = 0
    selected_candidate_seen = False
    source_runtime_bindings = {
        (
            str(runtime_cycle_report.get("cycle_id") or candidate_scorecard.get("source_runtime_cycle_id") or ""),
            str(runtime_cycle_report.get("cycle_hash") or candidate_scorecard.get("source_runtime_cycle_hash") or ""),
        )
    }
    discovery_blockers: list[dict[str, str]] = []

    def add_candidate_item(
        candidate: dict[str, Any],
        *,
        candidate_source_role: str,
        source_runtime_cycle_id: str,
        source_runtime_cycle_hash: str,
    ) -> None:
        nonlocal live_flag_drift_count, selected_candidate_seen
        if not isinstance(candidate, dict) or not isinstance(candidate.get("candidate_id"), str):
            return
        candidate_id = str(candidate.get("candidate_id") or "")
        if any(candidate.get(flag) is True for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
            live_flag_drift_count += 1
            items.append(
                _candidate_generation_item(
                    candidate,
                    status="REJECTED_LIVE_FLAG",
                    reason_code="LIVE_FINAL_GUARD_FAILED",
                    priority=len(items) + 1,
                    candidate_source_role=candidate_source_role,
                    source_runtime_cycle_id=source_runtime_cycle_id,
                    source_runtime_cycle_hash=source_runtime_cycle_hash,
                )
            )
            return
        if candidate_id == selected_candidate_id:
            selected_candidate_seen = True
            items.append(
                _candidate_generation_item(
                    candidate,
                    status="RETIRED_FAILED_SOURCE" if failed_current_candidate else "SELECTED_CURRENT",
                    reason_code=blocker_codes[0] if failed_current_candidate and blocker_codes else "CURRENT_SCORECARD_CANDIDATE",
                    priority=len(items) + 1,
                    candidate_source_role=candidate_source_role,
                    source_runtime_cycle_id=source_runtime_cycle_id,
                    source_runtime_cycle_hash=source_runtime_cycle_hash,
                )
            )
            return
        if candidate.get("decision") == "PAPER_ENTRY_REVIEW" and decimal_value(candidate.get("net_ev_after_cost_bps")) >= min_required_edge:
            items.append(
                _candidate_generation_item(
                    candidate,
                    status="REVIEW_READY",
                    reason_code="ALTERNATIVE_ENTRY_REVIEW_READY",
                    priority=len(items) + 1,
                    candidate_source_role=candidate_source_role,
                    source_runtime_cycle_id=source_runtime_cycle_id,
                    source_runtime_cycle_hash=source_runtime_cycle_hash,
                )
            )
            return
        items.append(
            _candidate_generation_item(
                candidate,
                status="BLOCKED_NO_TRADE",
                reason_code=str(candidate.get("no_trade_reason") or candidate.get("strategy_policy_reason") or "STRATEGY_NOT_ELIGIBLE"),
                priority=len(items) + 1,
                candidate_source_role=candidate_source_role,
                source_runtime_cycle_id=source_runtime_cycle_id,
                source_runtime_cycle_hash=source_runtime_cycle_hash,
            )
        )

    current_cycle_id = str(runtime_cycle_report.get("cycle_id") or candidate_scorecard.get("source_runtime_cycle_id") or "")
    current_cycle_hash = str(runtime_cycle_report.get("cycle_hash") or candidate_scorecard.get("source_runtime_cycle_hash") or "")
    for candidate in runtime_cycle_report.get("strategy_candidates") or []:
        add_candidate_item(
            candidate,
            candidate_source_role="CURRENT_RUNTIME_CYCLE",
            source_runtime_cycle_id=current_cycle_id,
            source_runtime_cycle_hash=current_cycle_hash,
        )

    for discovery_runtime in additional_runtime_cycle_reports or []:
        if not isinstance(discovery_runtime, dict):
            continue
        discovery_cycle_id = str(discovery_runtime.get("cycle_id") or "")
        discovery_cycle_hash = str(discovery_runtime.get("cycle_hash") or "")
        source_runtime_bindings.add((discovery_cycle_id, discovery_cycle_hash))
        if (
            discovery_runtime.get("exchange") != "UPBIT"
            or discovery_runtime.get("market_type") != "KRW_SPOT"
            or discovery_runtime.get("mode") != "PAPER"
            or any(discovery_runtime.get(flag) is True for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"))
        ):
            discovery_blockers.append(
                blocker("SNAPSHOT_SCOPE_MISMATCH", "Additional candidate discovery runtime was not scoped to live-blocked UPBIT/KRW_SPOT/PAPER.")
            )
            continue
        runtime_result = validate_upbit_paper_runtime_cycle_report(discovery_runtime)
        if runtime_result.status != "PASS":
            discovery_blockers.append(
                blocker(
                    runtime_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
                    f"Additional candidate discovery runtime failed validation: {runtime_result.message}",
                )
            )
            continue
        for candidate in discovery_runtime.get("strategy_candidates") or []:
            add_candidate_item(
                candidate,
                candidate_source_role="BOUNDED_PUBLIC_DISCOVERY_RUNTIME",
                source_runtime_cycle_id=discovery_cycle_id,
                source_runtime_cycle_hash=discovery_cycle_hash,
            )

    sorted_items = _dedupe_candidate_generation_items(items)[:safe_budget]
    review_ready_items = [item for item in sorted_items if item["candidate_status"] == "REVIEW_READY"]
    best = review_ready_items[0] if review_ready_items else None
    blocked_count = sum(1 for item in sorted_items if item["candidate_status"] in {"BLOCKED_NO_TRADE", "REJECTED_LIVE_FLAG"})
    alternative_replay_binding, alternative_replay_blocker = _best_alternative_replay_binding(
        best=best,
        replay_report=best_alternative_public_replay_report,
    )
    alternative_replay_passed = alternative_replay_binding["best_alternative_public_replay_status"] == "PASS"
    blockers = []
    if best is None:
        blockers.append(
            blocker(
                "STRATEGY_NOT_ELIGIBLE",
                "Bounded candidate generation found no different non-live PAPER_ENTRY_REVIEW candidate above the minimum net EV threshold.",
            )
        )
    if failed_current_candidate and not alternative_replay_passed:
        blockers.append(
            blocker(
                "PUBLIC_REPLAY_ROBUSTNESS_FAILED" if "PUBLIC_REPLAY_ROBUSTNESS_FAILED" in blocker_codes else blocker_codes[0],
                "Current candidate is retired from ranking review until fresh robustness and performance evidence pass.",
            )
        )
    if alternative_replay_blocker is not None:
        blockers.append(alternative_replay_blocker)
    if live_flag_drift_count:
        blockers.append(blocker("LIVE_FINAL_GUARD_FAILED", "Candidate generation rejected a candidate with live or scale-up permission drift."))
    blockers.extend(discovery_blockers)
    if not selected_candidate_seen:
        blockers.append(blocker("SCORECARD_MISSING", "Current scorecard candidate was not present in the source runtime cycle candidate set."))

    generation_status = (
        "BLOCKED_LIVE_FLAG"
        if live_flag_drift_count
        else "ALTERNATIVE_PUBLIC_REPLAY_BLOCKED"
        if best is not None and alternative_replay_blocker is not None
        else "ALTERNATIVE_PUBLIC_REPLAY_VALIDATED"
        if best is not None and alternative_replay_passed
        else "ALTERNATIVE_REVIEW_READY"
        if best is not None
        else "NO_ALTERNATIVE_READY"
    )
    source_ids = [
        _scorecard_source_id_for_candidate_generation(candidate_scorecard),
        runtime_cycle_source_evidence_id(
            current_cycle_id,
            current_cycle_hash,
        ),
    ]
    for cycle_id, cycle_hash in sorted(source_runtime_bindings):
        if cycle_id and len(cycle_hash) == 64:
            source_ids.append(runtime_cycle_source_evidence_id(cycle_id, cycle_hash))
    source_ids.extend(str(item) for item in candidate_scorecard.get("source_evidence_ids", []) if item)
    source_ids.extend(str(item) for item in alternative_replay_binding["best_alternative_public_replay_source_evidence_ids"] if item)
    report = {
        "schema_id": CANDIDATE_GENERATION_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority or current_authority_hashes(),
        "generation_report_id": f"candidate_generation:{candidate_scorecard.get('scorecard_id')}",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": candidate_scorecard["session_id"],
        "source_runtime_cycle_id": str(runtime_cycle_report.get("cycle_id") or candidate_scorecard["source_runtime_cycle_id"]),
        "source_runtime_cycle_hash": str(runtime_cycle_report.get("cycle_hash") or candidate_scorecard["source_runtime_cycle_hash"]),
        "source_scorecard_id": candidate_scorecard["scorecard_id"],
        "selected_candidate_id": selected_candidate_id,
        "selected_symbol": candidate_scorecard["symbol"],
        "selected_strategy_id": candidate_scorecard["strategy_id"],
        "selected_parameter_hash": candidate_scorecard["parameter_hash"],
        "selected_candidate_retired_for_ranking": failed_current_candidate,
        "trigger_blocker_codes": sorted(set(blocker_codes)),
        "candidate_budget": safe_budget,
        "evaluated_candidate_count": len([item for item in items if item["candidate_status"] != "REJECTED_LIVE_FLAG"]),
        "review_ready_candidate_count": len(review_ready_items),
        "blocked_candidate_count": blocked_count,
        "alternative_candidate_count": len(review_ready_items),
        "best_alternative_candidate_id": best.get("candidate_id") if best else None,
        "best_alternative_symbol": best.get("symbol") if best else None,
        "best_alternative_strategy_id": best.get("strategy_id") if best else None,
        "best_alternative_net_ev_after_cost_bps": best.get("net_ev_after_cost_bps") if best else None,
        **alternative_replay_binding,
        "generation_status": generation_status,
        "status": "PASS" if generation_status in CANDIDATE_GENERATION_PASS_STATUSES else "BLOCKED",
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "candidate_items": sorted_items,
        "source_evidence_ids": sorted(set(source_ids)),
        "next_action": (
            "Alternative public replay passed; keep live blocked and bind this candidate into the next PAPER ranking review only after remaining scorecard gates pass."
            if generation_status == "ALTERNATIVE_PUBLIC_REPLAY_VALIDATED"
            else
            "Run bounded public replay robustness for the best alternative candidate before any PAPER ranking review."
            if best is not None
            else "Widen bounded public discovery across the fresh KRW universe and strategy families; do not run long PAPER until an alternative candidate is review-ready."
        ),
        "operator_warning": "Candidate generation is non-live PAPER research evidence only; it cannot create LIVE_READY or place orders.",
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "generation_hash": "",
    }
    report["generation_hash"] = candidate_generation_report_hash(report)
    return report


def validate_candidate_generation_report(
    report: dict[str, Any],
    *,
    candidate_scorecard: dict[str, Any] | None = None,
) -> tuple[str, str, str | None]:
    required = {
        "schema_id",
        "generation_report_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "source_runtime_cycle_id",
        "source_runtime_cycle_hash",
        "source_scorecard_id",
        "selected_candidate_id",
        "candidate_budget",
        "evaluated_candidate_count",
        "review_ready_candidate_count",
        "blocked_candidate_count",
        "alternative_candidate_count",
        "generation_status",
        "status",
        "blockers",
        "candidate_items",
        "source_evidence_ids",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "generation_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return "FAIL", f"candidate generation report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("schema_id") != CANDIDATE_GENERATION_SCHEMA_ID:
        return "FAIL", "candidate generation schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("generation_hash") != candidate_generation_report_hash(report):
        return "FAIL", "candidate generation hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return "BLOCKED", "candidate generation scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
    if any(report.get(flag) is True for flag in ("credential_load_attempted", "private_endpoint_called", "order_endpoint_called", "order_adapter_called", "live_key_loaded", "live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        return "BLOCKED", "candidate generation attempted private, order, live, or scale-up behavior", "LIVE_FINAL_GUARD_FAILED"
    items = report.get("candidate_items")
    if not isinstance(items, list):
        return "FAIL", "candidate generation items must be a list", "SCHEMA_IDENTITY_MISMATCH"
    source_evidence_ids = {str(source_id) for source_id in report.get("source_evidence_ids") or []}
    required_item_fields = {
        "candidate_id",
        "candidate_status",
        "candidate_source_role",
        "source_runtime_cycle_id",
        "source_runtime_cycle_hash",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    }
    allowed_item_source_roles = {"CURRENT_RUNTIME_CYCLE", "BOUNDED_PUBLIC_DISCOVERY_RUNTIME"}
    for item in items:
        if not isinstance(item, dict):
            return "FAIL", "candidate generation item must be an object", "SCHEMA_IDENTITY_MISMATCH"
        missing_item_fields = sorted(required_item_fields - set(item))
        if missing_item_fields:
            return (
                "FAIL",
                f"candidate generation item missing source or live-guard fields: {missing_item_fields}",
                "SCHEMA_IDENTITY_MISMATCH",
            )
        if item.get("candidate_source_role") not in allowed_item_source_roles:
            return "FAIL", "candidate generation item has unknown source role", "SCHEMA_IDENTITY_MISMATCH"
        if any(item.get(flag) is True for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
            return "BLOCKED", "candidate generation item attempted live or scale-up behavior", "LIVE_FINAL_GUARD_FAILED"
        item_cycle_id = str(item.get("source_runtime_cycle_id") or "")
        item_cycle_hash = str(item.get("source_runtime_cycle_hash") or "")
        if not item_cycle_id or len(item_cycle_hash) != 64:
            return "FAIL", "candidate generation item is missing runtime source binding", "SCHEMA_IDENTITY_MISMATCH"
        if runtime_cycle_source_evidence_id(item_cycle_id, item_cycle_hash) not in source_evidence_ids:
            return "FAIL", "candidate generation item source binding is not listed in source evidence", "SCHEMA_IDENTITY_MISMATCH"
    review_ready_count = sum(1 for item in items if isinstance(item, dict) and item.get("candidate_status") == "REVIEW_READY")
    if review_ready_count != report.get("review_ready_candidate_count"):
        return "FAIL", "candidate generation review-ready count mismatch", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("generation_status") in CANDIDATE_GENERATION_PASS_STATUSES and not report.get("best_alternative_candidate_id"):
        return "FAIL", "alternative-ready report requires best alternative candidate", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("generation_status") == "ALTERNATIVE_PUBLIC_REPLAY_VALIDATED":
        if report.get("best_alternative_public_replay_status") != "PASS":
            return "FAIL", "alternative public replay validated report requires replay PASS binding", "SCHEMA_IDENTITY_MISMATCH"
        if not report.get("best_alternative_public_replay_source_evidence_ids"):
            return "FAIL", "alternative public replay validated report requires source evidence binding", "SCHEMA_IDENTITY_MISMATCH"
        if report.get("primary_blocker_code") is not None:
            return "FAIL", "alternative public replay validated report cannot keep stale primary blocker", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("generation_status") == "ALTERNATIVE_PUBLIC_REPLAY_BLOCKED" and report.get("best_alternative_public_replay_status") != "BLOCKED":
        return "FAIL", "alternative public replay blocked report requires BLOCKED replay status", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("generation_status") not in CANDIDATE_GENERATION_PASS_STATUSES and report.get("status") != "BLOCKED":
        return "FAIL", "non-ready candidate generation report must stay BLOCKED", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("generation_status") in CANDIDATE_GENERATION_PASS_STATUSES and report.get("status") != "PASS":
        return "FAIL", "ready candidate generation report must be PASS", "SCHEMA_IDENTITY_MISMATCH"
    if candidate_scorecard is not None:
        for report_field, scorecard_field in (
            ("session_id", "session_id"),
            ("source_scorecard_id", "scorecard_id"),
            ("selected_candidate_id", "candidate_id"),
            ("selected_parameter_hash", "parameter_hash"),
        ):
            if str(report.get(report_field) or "") != str(candidate_scorecard.get(scorecard_field) or ""):
                return "BLOCKED", f"candidate generation scope mismatch: {report_field}", "SNAPSHOT_SCOPE_MISMATCH"
    return "PASS", "candidate generation report is scoped, deterministic, and live-blocked", None


def candidate_scorecard_from_upbit_paper_runtime_cycle(
    runtime_cycle_report: dict[str, Any],
    *,
    authority: dict[str, str] | None = None,
    scorecard_id: str | None = None,
    min_required_edge_bps: float = 10.0,
    robustness_statuses: dict[str, str] | None = None,
    robustness_source_evidence_ids: list[str] | None = None,
    performance_statuses: dict[str, str] | None = None,
    performance_metrics: dict[str, Any] | None = None,
    performance_source_evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    runtime_result = validate_upbit_paper_runtime_cycle_report(runtime_cycle_report)
    if runtime_result.status != "PASS":
        raise ValueError(f"runtime cycle is not valid for scorecard input: {runtime_result.status}:{runtime_result.blocker_code}")

    selected = _scorecard_candidate_from_runtime(runtime_cycle_report)
    selected_symbol = str(selected.get("symbol") or runtime_cycle_report["symbol"])
    cost_breakdown = selected["cost_breakdown_bps"]
    robustness = {
        "oos_status": "UNTESTED",
        "walk_forward_status": "UNTESTED",
        "bootstrap_status": "UNTESTED",
        "overfit_status": "UNTESTED",
    }
    if robustness_statuses:
        robustness.update(robustness_statuses)
    performance = dict(PERFORMANCE_PASS)
    for field in performance:
        performance[field] = "UNTESTED"
    if performance_statuses:
        performance.update(performance_statuses)
    performance_values = dict(DEFAULT_PERFORMANCE_METRICS)
    if performance_metrics:
        performance_values.update(performance_metrics)

    net_ev = number_value(selected["net_ev_after_cost_bps"])
    robustness_ready = all(robustness[field] == expected for field, expected in ROBUSTNESS_PASS.items())
    performance_thresholds_ready = (
        int(performance_values["closed_trade_sample_count"]) >= int(performance_values["min_closed_trade_sample_count"])
        and int(performance_values["strategy_exit_policy_sample_count"])
        >= int(performance_values["min_strategy_exit_policy_sample_count"])
        and int(performance_values["strategy_exit_policy_match_count"])
        >= int(performance_values["min_strategy_exit_policy_sample_count"])
        and int(performance_values["strategy_exit_policy_mismatch_count"]) == 0
        and int(performance_values["regime_outcome_sample_count"])
        >= int(performance_values["min_regime_outcome_sample_count"])
        and int(performance_values["regime_outcome_covered_count"])
        >= int(performance_values["min_regime_outcome_covered_count"])
        and int(performance_values["regime_outcome_mismatch_count"]) == 0
        and int(performance_values["realized_vs_expected_sample_count"]) >= int(performance_values["min_closed_trade_sample_count"])
        and int(performance_values["fill_quality_sample_count"]) >= int(performance_values["min_closed_trade_sample_count"])
        and int(performance_values["execution_cost_sample_count"]) >= int(performance_values["min_closed_trade_sample_count"])
        and float(performance_values["profit_factor"]) >= float(performance_values["min_profit_factor"])
        and float(performance_values["max_drawdown_pct"]) <= float(performance_values["max_allowed_drawdown_pct"])
        and float(performance_values["realized_vs_expected_edge_bps"])
        >= float(performance_values["min_realized_vs_expected_edge_bps"])
        and float(performance_values["fill_quality_score"]) >= float(performance_values["min_fill_quality_score"])
        and float(performance_values["execution_cost_delta_bps"])
        <= float(performance_values["max_allowed_execution_cost_delta_bps"])
    )
    performance_ready = (
        all(performance[field] == expected for field, expected in PERFORMANCE_PASS.items())
        and performance_thresholds_ready
    )
    source_runtime_cycle_id = str(runtime_cycle_report["cycle_id"])
    source_runtime_cycle_hash = str(runtime_cycle_report["cycle_hash"])
    source_ids = [runtime_cycle_source_evidence_id(source_runtime_cycle_id, source_runtime_cycle_hash)]
    source_ids.extend(robustness_source_evidence_ids or [])
    source_ids.extend(performance_source_evidence_ids or [])
    public_replay_robustness_bound = _has_public_replay_robustness_source(source_ids)
    enough_robustness_sources = has_required_robustness_source_ids(
        source_ids,
        cycle_id=source_runtime_cycle_id,
        cycle_hash=source_runtime_cycle_hash,
    )
    performance_source_binding = performance_source_binding_from_source_ids(
        source_ids,
        candidate_id=str(selected.get("candidate_id") or ""),
    )
    enough_performance_sources = performance_source_binding is not None
    performance_source_history_id = performance_source_binding[0] if performance_source_binding else None
    performance_source_history_hash = performance_source_binding[1] if performance_source_binding else None
    ranking_eligible = (
        selected.get("decision") == "PAPER_ENTRY_REVIEW"
        and net_ev >= min_required_edge_bps
        and robustness_ready
        and enough_robustness_sources
        and performance_ready
        and enough_performance_sources
    )
    top_symbol_scorecards = _top_symbol_evidence_scorecards(runtime_cycle_report)
    evaluated_symbol_count = int(runtime_cycle_report.get("symbol_evidence_scorecard_count", len(top_symbol_scorecards)) or 0)
    paper_entry_review_symbol_count = sum(
        1
        for scorecard in runtime_cycle_report.get("symbol_evidence_scorecards") or []
        if isinstance(scorecard, dict) and int(scorecard.get("paper_entry_review_candidate_count", 0) or 0) > 0
    )
    alternative = _best_alternative_candidate(runtime_cycle_report, str(selected["candidate_id"]))
    alternative_count = max(0, len(_entry_review_candidates(runtime_cycle_report)) - 1)
    rotation_reason = _rotation_review_reason(
        selected=selected,
        net_ev=net_ev,
        min_required_edge_bps=min_required_edge_bps,
        robustness_ready=robustness_ready,
        enough_robustness_sources=enough_robustness_sources,
        performance_ready=performance_ready,
        enough_performance_sources=enough_performance_sources,
        ranking_eligible=ranking_eligible,
        has_alternative=alternative is not None,
    )
    rotation_review_required = rotation_reason != "NONE"

    blockers: list[dict[str, str]] = []
    if selected.get("decision") != "PAPER_ENTRY_REVIEW":
        blockers.append(blocker(str(selected.get("no_trade_reason") or "MIN_EDGE_FAIL"), "selected PAPER candidate is not entry-review eligible"))
    if net_ev < min_required_edge_bps:
        blockers.append(blocker("MIN_EDGE_FAIL", "net EV after cost is below PAPER scorecard minimum"))
    if not robustness_ready:
        if public_replay_robustness_bound and any(
            robustness[field] == "FAIL"
            for field in ("oos_status", "walk_forward_status", "bootstrap_status")
        ):
            blockers.append(
                blocker(
                    "PUBLIC_REPLAY_ROBUSTNESS_FAILED",
                    "public read-only replay robustness evidence failed; retire this candidate for ranking until a bounded alternative review passes",
                )
            )
        if robustness["oos_status"] != "PASS":
            blockers.append(
                _robustness_failure_blocker(
                    status=robustness["oos_status"],
                    missing_code="OOS_MISSING",
                    failed_code="OOS_FAILED",
                    missing_message="OOS evidence is required before PAPER scorecard ranking",
                    failed_message="OOS net EV after cost failed the required threshold",
                )
            )
        if robustness["walk_forward_status"] != "PASS":
            blockers.append(
                _robustness_failure_blocker(
                    status=robustness["walk_forward_status"],
                    missing_code="WALK_FORWARD_MISSING",
                    failed_code="WALK_FORWARD_FAILED",
                    missing_message="walk-forward evidence is required before PAPER scorecard ranking",
                    failed_message="walk-forward robustness failed the required threshold",
                )
            )
        if robustness["bootstrap_status"] != "PASS":
            blockers.append(
                _robustness_failure_blocker(
                    status=robustness["bootstrap_status"],
                    missing_code="BOOTSTRAP_UNSTABLE",
                    failed_code="BOOTSTRAP_FAILED",
                    missing_message="bootstrap robustness evidence is required before PAPER scorecard ranking",
                    failed_message="bootstrap confidence lower bound failed the required threshold",
                )
            )
        if robustness["overfit_status"] != "LOW":
            blockers.append(blocker("OVERFIT_RISK_HIGH", "overfit risk must be LOW before PAPER scorecard ranking"))
    if robustness_ready and not enough_robustness_sources:
        blockers.append(
            blocker(
                "SCORECARD_MISSING",
                "OOS, walk-forward, and bootstrap source evidence ids are required before PAPER scorecard ranking",
            )
        )
    if not performance_ready:
        if performance["closed_trade_status"] != "PASS" or int(performance_values["closed_trade_sample_count"]) < int(
            performance_values["min_closed_trade_sample_count"]
        ):
            blockers.append(blocker("SAMPLE_INSUFFICIENT", "closed PAPER trade sample is required before PAPER scorecard ranking"))
        if performance["strategy_exit_policy_status"] != "PASS" or int(
            performance_values["strategy_exit_policy_sample_count"]
        ) < int(performance_values["min_strategy_exit_policy_sample_count"]) or int(
            performance_values["strategy_exit_policy_mismatch_count"]
        ) > 0:
            blockers.append(
                blocker(
                    "EXECUTION_FEEDBACK_MISSING",
                    "closed PAPER trades must be bound to the entry strategy exit router before PAPER scorecard ranking",
                )
            )
        if performance["regime_outcome_status"] != "PASS" or int(
            performance_values["regime_outcome_sample_count"]
        ) < int(performance_values["min_regime_outcome_sample_count"]) or int(
            performance_values["regime_outcome_covered_count"]
        ) < int(performance_values["min_regime_outcome_covered_count"]) or int(
            performance_values["regime_outcome_mismatch_count"]
        ) > 0:
            blockers.append(
                blocker(
                    "REGIME_MISMATCH",
                    "PAPER scorecard ranking requires regime-labeled outcomes across uptrend, range, downtrend, and risk-off with zero spot-long blocked-regime entries",
                )
            )
        if performance["profit_factor_status"] != "PASS" or float(performance_values["profit_factor"]) < float(
            performance_values["min_profit_factor"]
        ):
            blockers.append(blocker("MEASUREMENT_MISSING", "profit factor must pass before PAPER scorecard ranking"))
        if performance["max_drawdown_status"] != "PASS" or float(performance_values["max_drawdown_pct"]) > float(
            performance_values["max_allowed_drawdown_pct"]
        ):
            blockers.append(blocker("DRAWDOWN_FREEZE_ACTIVE", "max drawdown must remain inside policy before PAPER scorecard ranking"))
        if performance["realized_vs_expected_edge_status"] != "PASS" or float(
            performance_values["realized_vs_expected_edge_bps"]
        ) < float(performance_values["min_realized_vs_expected_edge_bps"]):
            blockers.append(
                blocker(
                    "EXECUTION_FEEDBACK_DIVERGENT",
                    "realized edge after fee/slippage/impact must match or exceed expected edge before ranking",
                )
            )
        if performance["fill_quality_status"] != "PASS" or float(performance_values["fill_quality_score"]) < float(
            performance_values["min_fill_quality_score"]
        ):
            blockers.append(blocker("EXECUTION_QUALITY_UNTESTED", "fill quality evidence is required before PAPER scorecard ranking"))
        if performance["execution_cost_comparison_status"] != "PASS" or float(
            performance_values["execution_cost_delta_bps"]
        ) > float(performance_values["max_allowed_execution_cost_delta_bps"]):
            blockers.append(
                blocker(
                    "EXECUTION_FEEDBACK_DIVERGENT",
                    "realized fee/slippage/impact cost must stay within expected execution cost before ranking",
                )
            )
    if performance_ready and not enough_performance_sources:
        blockers.append(
            blocker(
                "EXECUTION_FEEDBACK_MISSING",
                "closed trade, execution quality, and performance summary evidence ids are required before PAPER scorecard ranking",
            )
        )

    if ranking_eligible:
        blockers = []

    return {
        "schema_id": SCORECARD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority or current_authority_hashes(),
        "scorecard_id": scorecard_id or f"scorecard:{runtime_cycle_report['cycle_id']}:{selected['candidate_id']}",
        "candidate_id": selected["candidate_id"],
        "source_runtime_cycle_id": source_runtime_cycle_id,
        "source_runtime_cycle_hash": source_runtime_cycle_hash,
        "strategy_id": strategy_id_for_family(selected["strategy_family"]),
        "strategy_build_id": "upbit_paper_runtime_cycle_v1",
        "parameter_hash": stable_hash(f"{selected['candidate_id']}:{selected['strategy_family']}:{selected_symbol}"),
        "exchange": runtime_cycle_report["exchange"],
        "market_type": runtime_cycle_report["market_type"],
        "mode": runtime_cycle_report["mode"],
        "session_id": runtime_cycle_report["session_id"],
        "symbol": selected_symbol,
        "timeframe_scope": "runtime_cycle_fixture_or_public_collection",
        "regime_scope": regime_scope_for_runtime_regime(str(selected.get("regime") or runtime_cycle_report.get("regime"))),
        "objective_basis": "NET_EV_AFTER_COST",
        "gross_expected_edge_bps": number_value(selected["expected_edge_bps"]),
        "expected_fee_bps": number_value(cost_breakdown[COST_FIELD_MAP["expected_fee_bps"]]),
        "expected_spread_bps": number_value(cost_breakdown[COST_FIELD_MAP["expected_spread_bps"]]),
        "expected_slippage_bps": number_value(cost_breakdown[COST_FIELD_MAP["expected_slippage_bps"]]),
        "expected_impact_bps": number_value(cost_breakdown[COST_FIELD_MAP["expected_impact_bps"]]),
        "expected_latency_penalty_bps": number_value(cost_breakdown[COST_FIELD_MAP["expected_latency_penalty_bps"]]),
        "net_ev_after_cost_bps": net_ev,
        "min_required_edge_bps": float(min_required_edge_bps),
        "cost_model_status": "VALIDATED",
        "oos_status": robustness["oos_status"],
        "walk_forward_status": robustness["walk_forward_status"],
        "bootstrap_status": robustness["bootstrap_status"],
        "overfit_status": robustness["overfit_status"],
        "closed_trade_status": performance["closed_trade_status"],
        "closed_trade_sample_count": int(performance_values["closed_trade_sample_count"]),
        "min_closed_trade_sample_count": int(performance_values["min_closed_trade_sample_count"]),
        "strategy_exit_policy_status": performance["strategy_exit_policy_status"],
        "strategy_exit_policy_sample_count": int(performance_values["strategy_exit_policy_sample_count"]),
        "min_strategy_exit_policy_sample_count": int(performance_values["min_strategy_exit_policy_sample_count"]),
        "strategy_exit_policy_match_count": int(performance_values["strategy_exit_policy_match_count"]),
        "strategy_exit_policy_mismatch_count": int(performance_values["strategy_exit_policy_mismatch_count"]),
        "strategy_exit_reason_count": int(performance_values["strategy_exit_reason_count"]),
        "strategy_exit_reason_counts": [
            {"reason_code": str(item.get("reason_code") or ""), "count": int(item.get("count", 0) or 0)}
            for item in performance_values.get("strategy_exit_reason_counts", [])
            if isinstance(item, dict) and item.get("reason_code")
        ],
        "expected_strategy_exit_policy_id": STRATEGY_EXIT_POLICY_ID,
        "expected_strategy_exit_variation": expected_strategy_exit_variation_for_family(str(selected["strategy_family"])),
        "regime_outcome_status": performance["regime_outcome_status"],
        "regime_outcome_sample_count": int(performance_values["regime_outcome_sample_count"]),
        "min_regime_outcome_sample_count": int(performance_values["min_regime_outcome_sample_count"]),
        "regime_outcome_covered_count": int(performance_values["regime_outcome_covered_count"]),
        "min_regime_outcome_covered_count": int(performance_values["min_regime_outcome_covered_count"]),
        "regime_outcome_trade_count": int(performance_values["regime_outcome_trade_count"]),
        "regime_outcome_no_trade_count": int(performance_values["regime_outcome_no_trade_count"]),
        "regime_outcome_mismatch_count": int(performance_values["regime_outcome_mismatch_count"]),
        "regime_outcome_counts": [
            {
                "regime": str(item.get("regime") or ""),
                "sample_count": int(item.get("sample_count", 0) or 0),
                "trade_count": int(item.get("trade_count", 0) or 0),
                "no_trade_count": int(item.get("no_trade_count", 0) or 0),
                "mismatch_count": int(item.get("mismatch_count", 0) or 0),
                "trade_allowed": bool(item.get("trade_allowed")),
                "primary_blocker_code": (
                    str(item.get("primary_blocker_code")) if item.get("primary_blocker_code") is not None else None
                ),
            }
            for item in performance_values.get("regime_outcome_counts", [])
            if isinstance(item, dict) and item.get("regime")
        ],
        "realized_vs_expected_sample_count": int(performance_values["realized_vs_expected_sample_count"]),
        "fill_quality_sample_count": int(performance_values["fill_quality_sample_count"]),
        "execution_cost_sample_count": int(performance_values["execution_cost_sample_count"]),
        "profit_factor_status": performance["profit_factor_status"],
        "profit_factor": float(performance_values["profit_factor"]),
        "min_profit_factor": float(performance_values["min_profit_factor"]),
        "max_drawdown_status": performance["max_drawdown_status"],
        "max_drawdown_pct": float(performance_values["max_drawdown_pct"]),
        "max_allowed_drawdown_pct": float(performance_values["max_allowed_drawdown_pct"]),
        "realized_vs_expected_edge_status": performance["realized_vs_expected_edge_status"],
        "realized_vs_expected_edge_bps": float(performance_values["realized_vs_expected_edge_bps"]),
        "min_realized_vs_expected_edge_bps": float(performance_values["min_realized_vs_expected_edge_bps"]),
        "fill_quality_status": performance["fill_quality_status"],
        "fill_quality_score": float(performance_values["fill_quality_score"]),
        "min_fill_quality_score": float(performance_values["min_fill_quality_score"]),
        "execution_cost_comparison_status": performance["execution_cost_comparison_status"],
        "realized_fee_bps": float(performance_values["realized_fee_bps"]),
        "realized_slippage_bps": float(performance_values["realized_slippage_bps"]),
        "realized_impact_bps": float(performance_values["realized_impact_bps"]),
        "expected_total_execution_cost_bps": float(performance_values["expected_total_execution_cost_bps"]),
        "realized_total_execution_cost_bps": float(performance_values["realized_total_execution_cost_bps"]),
        "execution_cost_delta_bps": float(performance_values["execution_cost_delta_bps"]),
        "max_allowed_execution_cost_delta_bps": float(performance_values["max_allowed_execution_cost_delta_bps"]),
        "performance_ready": performance_ready,
        "performance_source_evidence_required": list(PERFORMANCE_SOURCE_PREFIXES),
        "performance_source_binding_status": "PASS" if enough_performance_sources else "MISSING_OR_MISMATCHED",
        "performance_source_history_id": performance_source_history_id,
        "performance_source_history_hash": performance_source_history_hash,
        "robustness_ready": robustness_ready,
        "robustness_source_evidence_required": list(ROBUSTNESS_SOURCE_PREFIXES),
        "ranking_eligible": ranking_eligible,
        "scorecard_scope": "PAPER_SCORECARD_INPUT_ONLY" if ranking_eligible else "PAPER_EVIDENCE_COLLECTION_ONLY",
        "live_readiness_status": "NOT_LIVE_READY",
        "operator_warning": "PAPER candidate scorecard is not LIVE_READY and live orders remain blocked.",
        "source_evidence_ids": source_ids,
        "blockers": blockers,
        "evaluated_symbol_count": evaluated_symbol_count,
        "paper_entry_review_symbol_count": paper_entry_review_symbol_count,
        "top_symbol_evidence_scorecards": top_symbol_scorecards,
        "strategy_family_evidence_scorecards": _strategy_family_evidence_scorecards(runtime_cycle_report),
        "alternative_candidate_count": alternative_count,
        "best_alternative_candidate_id": alternative.get("candidate_id") if alternative else None,
        "best_alternative_symbol": alternative.get("symbol") if alternative else None,
        "best_alternative_net_ev_after_cost_bps": (
            number_value(alternative.get("net_ev_after_cost_bps")) if alternative else None
        ),
        "rotation_review_required": rotation_review_required,
        "rotation_review_reason_code": rotation_reason,
        "rotation_review_acceptance_condition": (
            "rotation_review_required only when a different PAPER_ENTRY_REVIEW candidate exists and "
            "the selected scorecard is not ranking_eligible; recommendation is PAPER-only and live flags remain false"
        ),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "notes": "Generated from Upbit PAPER runtime cycle. It is PAPER scorecard evidence only and cannot create live permission.",
    }


def write_upbit_paper_candidate_scorecard(*, root: Path, scorecard: dict[str, Any]) -> Path:
    if (
        scorecard.get("exchange") != "UPBIT"
        or scorecard.get("market_type") != "KRW_SPOT"
        or scorecard.get("mode") != "PAPER"
    ):
        raise ValueError("candidate scorecard writer is scoped to UPBIT/KRW_SPOT/PAPER")
    forbidden_flags = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
    if any(scorecard.get(flag) is True for flag in forbidden_flags):
        raise ValueError("candidate scorecard writer refuses live or scale-up permission")
    path = (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(scorecard["session_id"])
        / "profitability"
        / "candidate_scorecard.json"
    )
    snapshot_path = (
        path.parent
        / "candidate_scorecards"
        / f"{safe_candidate_scorecard_filename(scorecard.get('candidate_id'))}.candidate_scorecard.json"
    )
    durable_atomic_write_json(path, scorecard)
    durable_atomic_write_json(snapshot_path, scorecard)
    return path


def write_upbit_paper_candidate_generation_report(*, root: Path, report: dict[str, Any]) -> Path:
    if (
        report.get("exchange") != "UPBIT"
        or report.get("market_type") != "KRW_SPOT"
        or report.get("mode") != "PAPER"
    ):
        raise ValueError("candidate generation writer is scoped to UPBIT/KRW_SPOT/PAPER")
    if any(
        report.get(flag) is True
        for flag in (
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
    ):
        raise ValueError("candidate generation writer refuses private, order, live, or scale-up permission")
    status, message, blocker_code = validate_candidate_generation_report(report)
    if status != "PASS":
        raise ValueError(f"candidate generation report failed validation: {blocker_code or status}: {message}")
    path = (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(report["session_id"])
        / "profitability"
        / "candidate_generation_report.json"
    )
    snapshot_path = (
        path.parent
        / "candidate_generation_reports"
        / f"{safe_candidate_scorecard_filename(report.get('selected_candidate_id'))}.candidate_generation_report.json"
    )
    durable_atomic_write_json(path, report)
    durable_atomic_write_json(snapshot_path, report)
    return path
