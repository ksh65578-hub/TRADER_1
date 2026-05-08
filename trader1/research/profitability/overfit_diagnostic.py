from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from trader1.research.profitability.candidate_scorecard import (
    ROBUSTNESS_PASS,
    ROBUSTNESS_SOURCE_PREFIXES,
    current_authority_hashes,
    number_value,
    regime_scope_for_runtime_regime,
    robustness_source_evidence_id,
    strategy_id_for_family,
)
from trader1.research.replay.replay_runner import public_replay_robustness_values_from_report
from trader1.runtime.paper.upbit_paper_runtime import validate_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_paper_runtime_sample_history import validate_upbit_paper_runtime_sample_history
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


ROOT = Path(__file__).resolve().parents[3]
OVERFIT_DIAGNOSTIC_SCHEMA_ID = "trader1.overfit_diagnostic_report.v1"
DEFAULT_MIN_REQUIRED_SAMPLE_COUNT = 300
DEFAULT_MIN_REQUIRED_BOOTSTRAP_ITERATIONS = 500
DEFAULT_MIN_REQUIRED_OOS_NET_EV_BPS = 5.0
DEFAULT_MAX_ALLOWED_OOS_DEGRADATION_BPS = 12.0
DEFAULT_MIN_REQUIRED_WALK_FORWARD_PASS_RATE = 0.70
DEFAULT_MIN_REQUIRED_BOOTSTRAP_CONFIDENCE_LOWER_BPS = 1.0
DEFAULT_MIN_REQUIRED_RANKING_STABILITY_SCORE = 0.75
DEFAULT_MIN_PRELIMINARY_SAMPLE_COUNT = 20
WALK_FORWARD_WINDOW_SIZE = 50


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def overfit_diagnostic_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("diagnostic_hash", None)
    return _sha256_json(payload)


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _has_public_replay_robustness_source(source_ids: list[str]) -> bool:
    return any(str(source_id).startswith("public_replay_robustness:") for source_id in source_ids)


def _robustness_blocker_for_status(
    *,
    status: str,
    missing_code: str,
    failed_code: str,
    missing_message: str,
    failed_message: str,
) -> dict[str, str]:
    if status == "FAIL":
        return _blocker(failed_code, failed_message)
    return _blocker(missing_code, missing_message)


def _relative_id(prefix: str, primary: str, secondary: str | None = None) -> str:
    return f"{prefix}:{primary}" if secondary is None else f"{prefix}:{primary}:{secondary}"


def _load_json(root: Path, artifact_path: str) -> dict[str, Any] | None:
    path = (root / artifact_path).resolve()
    try:
        if root.resolve() not in path.parents and path != root.resolve():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _decimal_value(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _candidate_net_ev(runtime_cycle: dict[str, Any], candidate_id: str) -> float | None:
    selected = runtime_cycle.get("selected_candidate")
    if isinstance(selected, dict) and selected.get("candidate_id") == candidate_id:
        return number_value(selected.get("net_ev_after_cost_bps"))
    candidates = runtime_cycle.get("strategy_candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if isinstance(candidate, dict) and candidate.get("candidate_id") == candidate_id:
                return number_value(candidate.get("net_ev_after_cost_bps"))
    return None


def _validated_runtime_from_sample(
    *,
    root: Path,
    sample: dict[str, Any],
    candidate_scorecard: dict[str, Any],
) -> dict[str, Any] | None:
    runtime = _load_json(root, str(sample.get("source_runtime_cycle_path") or ""))
    if not runtime:
        return None
    validation = validate_upbit_paper_runtime_cycle_report(runtime, require_quantitative_policy_summary=False)
    if validation.status != "PASS":
        return None
    if runtime.get("cycle_hash") != sample.get("source_runtime_cycle_hash"):
        return None
    if (
        runtime.get("exchange") != candidate_scorecard.get("exchange")
        or runtime.get("market_type") != candidate_scorecard.get("market_type")
    ):
        return None
    if runtime.get("mode") != candidate_scorecard.get("mode") or runtime.get("session_id") != candidate_scorecard.get("session_id"):
        return None
    return runtime


def _matched_runtime_values(
    *,
    root: Path,
    candidate_scorecard: dict[str, Any],
    runtime_sample_history: dict[str, Any],
) -> tuple[list[float], list[dict[str, Any]], list[str]]:
    candidate_id = str(candidate_scorecard.get("candidate_id", ""))
    values: list[float] = []
    matched_samples: list[dict[str, Any]] = []
    source_ids: list[str] = []

    history_id = str(runtime_sample_history.get("history_id") or "unknown_history")
    history_hash = str(runtime_sample_history.get("history_hash") or "missing_hash")
    source_ids.append(_relative_id("runtime_sample_history", history_id, history_hash))

    for sample in runtime_sample_history.get("samples") or []:
        if not isinstance(sample, dict):
            continue
        runtime = _validated_runtime_from_sample(root=root, sample=sample, candidate_scorecard=candidate_scorecard)
        if not runtime:
            continue
        net_ev = _candidate_net_ev(runtime, candidate_id)
        if net_ev is None:
            continue
        values.append(net_ev)
        matched_samples.append(sample)
        source_ids.append(_relative_id("upbit_paper_runtime_cycle", str(runtime["cycle_id"]), str(runtime["cycle_hash"])))

    return values, matched_samples, sorted(set(source_ids))


def _matched_realized_closed_trade_values(
    *,
    root: Path,
    candidate_scorecard: dict[str, Any],
    runtime_sample_history: dict[str, Any],
) -> tuple[list[float], list[dict[str, Any]], list[str]]:
    candidate_id = str(candidate_scorecard.get("candidate_id", ""))
    values: list[float] = []
    matched_samples: list[dict[str, Any]] = []
    source_ids: list[str] = []
    candidate_realized_pnl_baseline: Decimal | None = None

    history_id = str(runtime_sample_history.get("history_id") or "unknown_history")
    history_hash = str(runtime_sample_history.get("history_hash") or "missing_hash")
    source_ids.append(_relative_id("runtime_sample_history", history_id, history_hash))

    for sample in runtime_sample_history.get("samples") or []:
        if not isinstance(sample, dict):
            continue
        runtime = _validated_runtime_from_sample(root=root, sample=sample, candidate_scorecard=candidate_scorecard)
        if not runtime:
            continue

        portfolio = runtime.get("paper_portfolio_snapshot")
        current_realized_pnl = (
            _decimal_value(portfolio.get("realized_pnl"))
            if isinstance(portfolio, dict)
            else candidate_realized_pnl_baseline if candidate_realized_pnl_baseline is not None else Decimal("0")
        )
        fill = runtime.get("paper_fill")
        lifecycle = runtime.get("position_management_decision")
        selected = runtime.get("selected_candidate")
        candidate_entry = (
            isinstance(fill, dict)
            and isinstance(selected, dict)
            and runtime.get("final_decision") == "ENTER_LONG"
            and fill.get("side") == "BUY"
            and str(selected.get("candidate_id") or "") == candidate_id
        )
        candidate_exit = (
            isinstance(fill, dict)
            and isinstance(lifecycle, dict)
            and runtime.get("final_decision") == "EXIT_POSITION"
            and fill.get("side") == "SELL"
            and str(lifecycle.get("entry_candidate_id") or "") == candidate_id
        )
        if candidate_entry:
            candidate_realized_pnl_baseline = current_realized_pnl
        if candidate_exit:
            direct_realized_delta = _paper_sell_fill_realized_delta(fill, lifecycle)
            if direct_realized_delta is not None:
                realized_delta = direct_realized_delta
            elif candidate_realized_pnl_baseline is not None:
                realized_delta = current_realized_pnl - candidate_realized_pnl_baseline
            else:
                continue
            filled_notional = max(Decimal("1"), _decimal_value(fill.get("filled_notional")))
            values.append(float(realized_delta / filled_notional * Decimal("10000")))
            matched_samples.append(sample)
            source_ids.append(
                _relative_id("upbit_paper_runtime_cycle", str(runtime["cycle_id"]), str(runtime["cycle_hash"]))
            )
            candidate_realized_pnl_baseline = current_realized_pnl

    return values, matched_samples, sorted(set(source_ids))


def _paper_sell_fill_realized_delta(fill: dict[str, Any], lifecycle: dict[str, Any]) -> Decimal | None:
    quantity = _decimal_value(fill.get("filled_quantity") or fill.get("quantity"))
    fill_price = _decimal_value(fill.get("fill_price"))
    fee_amount = _decimal_value(fill.get("fee_amount"))
    managed_quantity = _decimal_value(lifecycle.get("managed_position_quantity"))
    managed_cost_basis = _decimal_value(lifecycle.get("managed_position_cost_basis"))
    if min(quantity, fill_price, managed_quantity, managed_cost_basis) <= 0 or quantity > managed_quantity:
        return None
    allocated_cost_basis = managed_cost_basis * (quantity / managed_quantity)
    return (quantity * fill_price) - allocated_cost_basis - fee_amount


def _compatible_preliminary_candidate(
    runtime_cycle: dict[str, Any],
    *,
    strategy_id: str,
    regime_scope: str,
) -> dict[str, Any] | None:
    compatible: list[dict[str, Any]] = []
    for candidate in runtime_cycle.get("strategy_candidates") or []:
        if not isinstance(candidate, dict):
            continue
        candidate_strategy_id = strategy_id_for_family(str(candidate.get("strategy_family") or ""))
        candidate_regime_scope = regime_scope_for_runtime_regime(str(candidate.get("regime") or runtime_cycle.get("regime") or ""))
        if candidate_strategy_id != strategy_id or candidate_regime_scope != regime_scope:
            continue
        net_ev = number_value(candidate.get("net_ev_after_cost_bps"))
        score = number_value(candidate.get("candidate_selection_score"))
        if not math.isfinite(net_ev) or not math.isfinite(score):
            continue
        compatible.append(candidate)
    if not compatible:
        return None
    return max(
        compatible,
        key=lambda candidate: (
            1 if candidate.get("decision") == "PAPER_ENTRY_REVIEW" else 0,
            number_value(candidate.get("candidate_selection_score")),
            number_value(candidate.get("net_ev_after_cost_bps")),
            str(candidate.get("candidate_id") or ""),
        ),
    )


def _compatible_preliminary_runtime_values(
    *,
    root: Path,
    candidate_scorecard: dict[str, Any],
    runtime_sample_history: dict[str, Any],
) -> tuple[list[float], list[dict[str, Any]], list[str], dict[str, Any]]:
    strategy_id = str(candidate_scorecard.get("strategy_id") or "")
    regime_scope = str(candidate_scorecard.get("regime_scope") or "")
    values: list[float] = []
    matched_samples: list[dict[str, Any]] = []
    source_ids: list[str] = []
    matched_symbols: set[str] = set()
    matched_candidate_ids: set[str] = set()

    history_id = str(runtime_sample_history.get("history_id") or "unknown_history")
    history_hash = str(runtime_sample_history.get("history_hash") or "missing_hash")
    source_ids.append(_relative_id("runtime_sample_history", history_id, history_hash))

    for sample in runtime_sample_history.get("samples") or []:
        if not isinstance(sample, dict):
            continue
        runtime = _validated_runtime_from_sample(root=root, sample=sample, candidate_scorecard=candidate_scorecard)
        if not runtime:
            continue
        candidate = _compatible_preliminary_candidate(
            runtime,
            strategy_id=strategy_id,
            regime_scope=regime_scope,
        )
        if candidate is None:
            continue
        values.append(number_value(candidate.get("net_ev_after_cost_bps")))
        matched_samples.append(sample)
        matched_symbols.add(str(candidate.get("symbol") or "UNKNOWN"))
        matched_candidate_ids.add(str(candidate.get("candidate_id") or "UNKNOWN"))
        source_ids.append(_relative_id("upbit_paper_runtime_cycle", str(runtime["cycle_id"]), str(runtime["cycle_hash"])))

    meta = {
        "preliminary_evidence_scope": "STRATEGY_REGIME_CYCLE_POOL",
        "preliminary_match_scope": f"strategy_id={strategy_id};regime_scope={regime_scope};one_candidate_per_cycle=true;live_order_allowed=false",
        "preliminary_distinct_symbol_count": len(matched_symbols),
        "preliminary_distinct_candidate_count": len(matched_candidate_ids),
    }
    return values, matched_samples, sorted(set(source_ids)), meta


def _walk_forward_metrics(
    values: list[float],
    *,
    min_required_sample_count: int,
    min_required_oos_net_ev_bps: float,
) -> tuple[int, float]:
    if len(values) < min_required_sample_count:
        return 0, 0.0
    windows = [values[index:index + WALK_FORWARD_WINDOW_SIZE] for index in range(0, len(values) - WALK_FORWARD_WINDOW_SIZE + 1, WALK_FORWARD_WINDOW_SIZE)]
    if not windows:
        return 0, 0.0
    passed = sum(1 for window in windows if _mean(window) >= min_required_oos_net_ev_bps)
    return len(windows), passed / len(windows)


def _preliminary_walk_forward_metrics(
    values: list[float],
    *,
    min_required_sample_count: int,
    min_required_oos_net_ev_bps: float,
) -> tuple[int, float, int]:
    if len(values) < min_required_sample_count or min_required_sample_count < 2:
        return 0, 0.0, 0
    window_size = max(2, min(WALK_FORWARD_WINDOW_SIZE, max(2, len(values) // 4)))
    windows = [values[index:index + window_size] for index in range(0, len(values) - window_size + 1, window_size)]
    if not windows:
        return 0, 0.0, window_size
    passed = sum(1 for window in windows if _mean(window) >= min_required_oos_net_ev_bps)
    return len(windows), passed / len(windows), window_size


def _ranking_stability(values: list[float], *, min_required_sample_count: int) -> float:
    if len(values) < min_required_sample_count or not values:
        return 0.0
    mean_value = abs(_mean(values))
    if len(values) == 1:
        return 1.0
    return _clamp(1.0 - (statistics.pstdev(values) / (mean_value + 1.0)))


def _stable_seed_int(payload: dict[str, Any]) -> int:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return int(hashlib.sha256(encoded).hexdigest()[:16], 16)


def _bootstrap_confidence_lower_bound(
    values: list[float],
    *,
    min_required_sample_count: int,
    iteration_count: int,
    confidence_quantile: float = 0.05,
    seed_material: dict[str, Any] | None = None,
) -> tuple[float, int]:
    if len(values) < min_required_sample_count or not values or iteration_count < 1:
        return 0.0, 0
    sample_size = len(values)
    rng = random.Random(
        _stable_seed_int(
            {
                "algorithm": "deterministic_bootstrap_mean_lower_bound_v1",
                "confidence_quantile": confidence_quantile,
                "iteration_count": iteration_count,
                "sample_size": sample_size,
                "seed_material": seed_material or {},
                "values_hash": hashlib.sha256(
                    json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
            }
        )
    )
    bootstrap_means: list[float] = []
    for _ in range(iteration_count):
        total = 0.0
        for _ in range(sample_size):
            total += values[rng.randrange(sample_size)]
        bootstrap_means.append(total / sample_size)
    bootstrap_means.sort()
    quantile_index = max(0, min(len(bootstrap_means) - 1, math.ceil(confidence_quantile * len(bootstrap_means)) - 1))
    return bootstrap_means[quantile_index], iteration_count


def _concentration_status(samples: list[dict[str, Any]], *, min_required_sample_count: int) -> str:
    if len(samples) < min_required_sample_count:
        return "UNTESTED"
    loop_counts = Counter(str(sample.get("loop_id") or sample.get("source_loop_report_hash") or "unknown") for sample in samples)
    max_share = max(loop_counts.values(), default=0) / len(samples)
    if max_share <= 0.60:
        return "LOW"
    if max_share <= 0.80:
        return "MEDIUM"
    return "HIGH"


def _preliminary_robustness_summary(
    *,
    status: str,
    sample_count: int,
    min_preliminary_sample_count: int,
    min_required_sample_count: int,
) -> tuple[str, str]:
    if status == "INSUFFICIENT_PRELIMINARY_SAMPLE":
        return (
            f"{sample_count}/{min_preliminary_sample_count} matched PAPER samples available for early diagnostics.",
            "Keep PAPER running until early OOS, walk-forward, bootstrap, and ranking-stability diagnostics can be measured.",
        )
    if status == "FAVORABLE_BLOCKED_BY_MATURITY":
        return (
            "Early PAPER diagnostics are favorable, but full robustness remains blocked by maturity requirements.",
            f"Keep collecting non-live PAPER samples until {min_required_sample_count} samples and full OOS/walk-forward/bootstrap checks pass.",
        )
    return (
        "Early PAPER diagnostics are unfavorable or unstable; treat the candidate as evidence-collection only.",
        "Review symbol selection, regime fit, fees/slippage, and entry/no-trade thresholds while continuing PAPER collection.",
    )


def overfit_diagnostic_from_upbit_paper_runtime(
    *,
    candidate_scorecard: dict[str, Any],
    runtime_sample_history: dict[str, Any],
    root: Path = ROOT,
    replay_robustness_report: dict[str, Any] | None = None,
    diagnostic_id: str | None = None,
    min_required_sample_count: int = DEFAULT_MIN_REQUIRED_SAMPLE_COUNT,
    min_required_bootstrap_iterations: int = DEFAULT_MIN_REQUIRED_BOOTSTRAP_ITERATIONS,
    min_required_oos_net_ev_bps: float = DEFAULT_MIN_REQUIRED_OOS_NET_EV_BPS,
    max_allowed_oos_degradation_bps: float = DEFAULT_MAX_ALLOWED_OOS_DEGRADATION_BPS,
    min_required_walk_forward_pass_rate: float = DEFAULT_MIN_REQUIRED_WALK_FORWARD_PASS_RATE,
    min_required_bootstrap_confidence_lower_bps: float = DEFAULT_MIN_REQUIRED_BOOTSTRAP_CONFIDENCE_LOWER_BPS,
    min_required_ranking_stability_score: float = DEFAULT_MIN_REQUIRED_RANKING_STABILITY_SCORE,
    min_preliminary_sample_count: int = DEFAULT_MIN_PRELIMINARY_SAMPLE_COUNT,
) -> dict[str, Any]:
    root = Path(root).resolve()
    sample_validation = validate_upbit_paper_runtime_sample_history(runtime_sample_history)
    if sample_validation.status == "PASS":
        expected_values, expected_samples, expected_source_ids = _matched_runtime_values(
            root=root,
            candidate_scorecard=candidate_scorecard,
            runtime_sample_history=runtime_sample_history,
        )
        realized_values, realized_samples, realized_source_ids = _matched_realized_closed_trade_values(
            root=root,
            candidate_scorecard=candidate_scorecard,
            runtime_sample_history=runtime_sample_history,
        )
        values = realized_values
        samples = realized_samples
        source_ids = realized_source_ids
        preliminary_values = realized_values if realized_values else expected_values
        preliminary_samples = realized_samples if realized_values else expected_samples
        preliminary_source_ids = realized_source_ids if realized_values else expected_source_ids
        preliminary_value_source = "REALIZED_CLOSED_TRADE_BPS" if realized_values else "EXPECTED_NET_EV_AFTER_COST_BPS"
        preliminary_meta = {
            "preliminary_evidence_scope": "EXACT_CANDIDATE",
            "preliminary_match_scope": (
                f"candidate_id={candidate_scorecard.get('candidate_id')};"
                f"value_source={preliminary_value_source};one_candidate_per_cycle=true;live_order_allowed=false"
            ),
            "preliminary_distinct_symbol_count": 1 if preliminary_values else 0,
            "preliminary_distinct_candidate_count": 1 if preliminary_values else 0,
        }
        preliminary_exact_candidate_sample_count = len(expected_values)
    else:
        values = []
        samples = []
        source_ids = [
            _relative_id(
                "runtime_sample_history",
                str(runtime_sample_history.get("history_id") or "invalid_history"),
                str(runtime_sample_history.get("history_hash") or sample_validation.blocker_code or "invalid"),
            )
        ]
        preliminary_values = []
        preliminary_samples = []
        preliminary_source_ids = source_ids
        preliminary_meta = {
            "preliminary_evidence_scope": "EXACT_CANDIDATE",
            "preliminary_match_scope": "invalid_runtime_sample_history",
            "preliminary_distinct_symbol_count": 0,
            "preliminary_distinct_candidate_count": 0,
        }
        preliminary_exact_candidate_sample_count = 0

    replay_values, replay_samples, replay_source_ids = (
        public_replay_robustness_values_from_report(
            replay_robustness_report,
            candidate_scorecard=candidate_scorecard,
        )
        if isinstance(replay_robustness_report, dict)
        else ([], [], [])
    )
    if len(values) < int(min_required_sample_count) and replay_values:
        values = replay_values
        samples = replay_samples
        source_ids = sorted(set(source_ids + replay_source_ids))

    sample_count = len(values)
    min_preliminary_sample_count = max(2, min(int(min_preliminary_sample_count), int(min_required_sample_count)))
    if sample_validation.status == "PASS" and len(preliminary_values) < min_preliminary_sample_count:
        compatible_values, compatible_samples, compatible_source_ids, compatible_meta = _compatible_preliminary_runtime_values(
            root=root,
            candidate_scorecard=candidate_scorecard,
            runtime_sample_history=runtime_sample_history,
        )
        if len(compatible_values) > len(preliminary_values):
            preliminary_values = compatible_values
            preliminary_samples = compatible_samples
            preliminary_source_ids = compatible_source_ids
            preliminary_meta = compatible_meta

    enough_samples = sample_count >= min_required_sample_count
    train_count = int(sample_count * 0.60) if enough_samples else min(sample_count, int(sample_count * 0.60))
    train_values = values[:train_count] if train_count else values
    oos_values = values[train_count:] if enough_samples else []
    in_sample_ev = _mean(train_values)
    oos_ev = _mean(oos_values)
    degradation = max(0.0, in_sample_ev - oos_ev)
    oos_window_count = 1 if oos_values else 0
    walk_forward_window_count, walk_forward_pass_rate = _walk_forward_metrics(
        values,
        min_required_sample_count=min_required_sample_count,
        min_required_oos_net_ev_bps=min_required_oos_net_ev_bps,
    )
    bootstrap_lower, bootstrap_iteration_count = _bootstrap_confidence_lower_bound(
        values,
        min_required_sample_count=min_required_sample_count,
        iteration_count=min_required_bootstrap_iterations,
        seed_material={
            "candidate_id": candidate_scorecard.get("candidate_id"),
            "strategy_build_id": candidate_scorecard.get("strategy_build_id"),
            "parameter_hash": candidate_scorecard.get("parameter_hash"),
            "session_id": candidate_scorecard.get("session_id"),
            "source_evidence_ids": source_ids,
        },
    )
    ranking_stability = _ranking_stability(values, min_required_sample_count=min_required_sample_count)
    concentration_status = _concentration_status(samples, min_required_sample_count=min_required_sample_count)

    preliminary_sample_count = len(preliminary_values)
    preliminary_enough_samples = preliminary_sample_count >= min_preliminary_sample_count
    preliminary_train_count = 0
    preliminary_oos_values: list[float] = []
    if preliminary_enough_samples:
        preliminary_train_count = max(1, min(preliminary_sample_count - 1, int(preliminary_sample_count * 0.60)))
        preliminary_oos_values = preliminary_values[preliminary_train_count:]
    preliminary_train_values = preliminary_values[:preliminary_train_count] if preliminary_train_count else []
    preliminary_in_sample_ev = _mean(preliminary_train_values)
    preliminary_oos_ev = _mean(preliminary_oos_values)
    preliminary_degradation = max(0.0, preliminary_in_sample_ev - preliminary_oos_ev)
    preliminary_oos_window_count = 1 if preliminary_oos_values else 0
    preliminary_walk_forward_window_count, preliminary_walk_forward_pass_rate, preliminary_walk_forward_window_size = (
        _preliminary_walk_forward_metrics(
            preliminary_values,
            min_required_sample_count=min_preliminary_sample_count,
            min_required_oos_net_ev_bps=min_required_oos_net_ev_bps,
        )
    )
    preliminary_bootstrap_lower, preliminary_bootstrap_iteration_count = _bootstrap_confidence_lower_bound(
        preliminary_values,
        min_required_sample_count=min_preliminary_sample_count,
        iteration_count=min_required_bootstrap_iterations,
        seed_material={
            "preliminary": True,
            "preliminary_evidence_scope": preliminary_meta["preliminary_evidence_scope"],
            "preliminary_match_scope": preliminary_meta["preliminary_match_scope"],
            "candidate_id": candidate_scorecard.get("candidate_id"),
            "strategy_build_id": candidate_scorecard.get("strategy_build_id"),
            "parameter_hash": candidate_scorecard.get("parameter_hash"),
            "session_id": candidate_scorecard.get("session_id"),
            "source_evidence_ids": preliminary_source_ids,
        },
    )
    preliminary_ranking_stability = _ranking_stability(
        preliminary_values,
        min_required_sample_count=min_preliminary_sample_count,
    )
    preliminary_concentration_status = _concentration_status(
        preliminary_samples,
        min_required_sample_count=min_preliminary_sample_count,
    )

    preliminary_oos_status = "UNTESTED"
    if preliminary_enough_samples and preliminary_oos_values:
        preliminary_oos_status = (
            "PASS"
            if preliminary_oos_ev >= min_required_oos_net_ev_bps
            and preliminary_degradation <= max_allowed_oos_degradation_bps
            else "FAIL"
        )

    preliminary_walk_forward_status = "UNTESTED"
    if preliminary_walk_forward_window_count > 0:
        preliminary_walk_forward_status = (
            "PASS" if preliminary_walk_forward_pass_rate >= min_required_walk_forward_pass_rate else "FAIL"
        )

    preliminary_bootstrap_status = "UNTESTED"
    if preliminary_bootstrap_iteration_count >= min_required_bootstrap_iterations:
        preliminary_bootstrap_status = (
            "PASS"
            if preliminary_bootstrap_lower >= min_required_bootstrap_confidence_lower_bps
            else "FAIL"
        )

    preliminary_ranking_stability_status = "UNTESTED"
    if preliminary_enough_samples:
        preliminary_ranking_stability_status = (
            "PASS" if preliminary_ranking_stability >= min_required_ranking_stability_score else "FAIL"
        )

    preliminary_status_checks = {
        "preliminary_oos_status": preliminary_oos_status,
        "preliminary_walk_forward_status": preliminary_walk_forward_status,
        "preliminary_bootstrap_status": preliminary_bootstrap_status,
        "preliminary_ranking_stability_status": preliminary_ranking_stability_status,
    }
    preliminary_primary_blocker_code = "PRELIMINARY_SAMPLE_INSUFFICIENT"
    preliminary_robustness_status = "INSUFFICIENT_PRELIMINARY_SAMPLE"
    if preliminary_enough_samples:
        preliminary_failure_codes = [
            ("preliminary_oos_status", "PRELIMINARY_OOS_BELOW_THRESHOLD"),
            ("preliminary_walk_forward_status", "PRELIMINARY_WALK_FORWARD_UNSTABLE"),
            ("preliminary_bootstrap_status", "PRELIMINARY_BOOTSTRAP_UNSTABLE"),
            ("preliminary_ranking_stability_status", "PRELIMINARY_RANKING_UNSTABLE"),
        ]
        preliminary_primary_blocker_code = next(
            (
                code
                for field, code in preliminary_failure_codes
                if preliminary_status_checks[field] != "PASS"
            ),
            "PRELIMINARY_CONCENTRATION_HIGH"
            if preliminary_concentration_status == "HIGH"
            else "ROBUSTNESS_MATURITY_BLOCKED",
        )
        preliminary_robustness_status = (
            "FAVORABLE_BLOCKED_BY_MATURITY"
            if preliminary_primary_blocker_code == "ROBUSTNESS_MATURITY_BLOCKED"
            else "UNFAVORABLE_BLOCKED_BY_EVIDENCE"
        )
    preliminary_summary, preliminary_next_action = _preliminary_robustness_summary(
        status=preliminary_robustness_status,
        sample_count=preliminary_sample_count,
        min_preliminary_sample_count=min_preliminary_sample_count,
        min_required_sample_count=min_required_sample_count,
    )

    oos_status = "BLOCKED"
    if enough_samples:
        oos_status = "PASS" if oos_ev >= min_required_oos_net_ev_bps and degradation <= max_allowed_oos_degradation_bps else "FAIL"

    min_walk_windows = max(1, min_required_sample_count // WALK_FORWARD_WINDOW_SIZE)
    walk_forward_status = "BLOCKED"
    if enough_samples and walk_forward_window_count >= min_walk_windows:
        walk_forward_status = "PASS" if walk_forward_pass_rate >= min_required_walk_forward_pass_rate else "FAIL"

    bootstrap_status = "BLOCKED"
    if enough_samples and bootstrap_iteration_count >= min_required_bootstrap_iterations:
        bootstrap_status = "PASS" if bootstrap_lower >= min_required_bootstrap_confidence_lower_bps else "FAIL"

    ranking_stability_status = "BLOCKED"
    if enough_samples:
        ranking_stability_status = "PASS" if ranking_stability >= min_required_ranking_stability_score else "FAIL"

    survivorship_bias_check = "PASS" if enough_samples and concentration_status in {"LOW", "MEDIUM"} else "BLOCKED"
    data_snooping_check = "PASS" if enough_samples and oos_window_count > 0 and walk_forward_window_count >= min_walk_windows else "BLOCKED"

    base_eligible = (
        oos_status == "PASS"
        and walk_forward_status == "PASS"
        and bootstrap_status == "PASS"
        and ranking_stability_status == "PASS"
        and concentration_status == "LOW"
        and survivorship_bias_check == "PASS"
        and data_snooping_check == "PASS"
    )
    robustness_eligible = bool(base_eligible)
    overfit_status = "LOW" if robustness_eligible else ("HIGH" if not enough_samples or oos_status != "PASS" or bootstrap_status != "PASS" else "MEDIUM")

    if robustness_eligible and samples:
        source_cycle_id = str(candidate_scorecard.get("source_runtime_cycle_id"))
        source_cycle_hash = str(candidate_scorecard.get("source_runtime_cycle_hash"))
        source_ids.extend(robustness_source_evidence_id(prefix, source_cycle_id, source_cycle_hash) for prefix in ROBUSTNESS_SOURCE_PREFIXES)
    source_ids = sorted(set(source_ids + preliminary_source_ids))

    blockers: list[dict[str, str]] = []
    if sample_count < min_required_sample_count:
        blockers.append(
            _blocker(
                "SAMPLE_INSUFFICIENT",
                f"{sample_count} matched robustness samples collected; {min_required_sample_count} required",
            )
        )
    public_replay_robustness_bound = _has_public_replay_robustness_source(source_ids)
    if public_replay_robustness_bound and any(
        status == "FAIL"
        for status in (oos_status, walk_forward_status, bootstrap_status)
    ):
        blockers.append(
            _blocker(
                "PUBLIC_REPLAY_ROBUSTNESS_FAILED",
                "public read-only replay robustness evidence failed and cannot support PAPER ranking",
            )
        )
    if oos_status != "PASS":
        blockers.append(
            _robustness_blocker_for_status(
                status=oos_status,
                missing_code="OOS_MISSING",
                failed_code="OOS_FAILED",
                missing_message="OOS net EV after cost has not passed the required threshold",
                failed_message="OOS net EV after cost failed the required threshold",
            )
        )
    if walk_forward_status != "PASS":
        blockers.append(
            _robustness_blocker_for_status(
                status=walk_forward_status,
                missing_code="WALK_FORWARD_MISSING",
                failed_code="WALK_FORWARD_FAILED",
                missing_message="walk-forward windows have not passed the required threshold",
                failed_message="walk-forward windows failed the required threshold",
            )
        )
    if bootstrap_status != "PASS":
        blockers.append(
            _robustness_blocker_for_status(
                status=bootstrap_status,
                missing_code="BOOTSTRAP_UNSTABLE",
                failed_code="BOOTSTRAP_FAILED",
                missing_message="bootstrap confidence lower bound has not passed the required threshold",
                failed_message="bootstrap confidence lower bound failed the required threshold",
            )
        )
    if overfit_status == "HIGH":
        blockers.append(_blocker("OVERFIT_RISK_HIGH", "overfit risk remains HIGH until OOS, walk-forward, and bootstrap evidence pass"))
    if survivorship_bias_check != "PASS":
        blockers.append(_blocker("SURVIVORSHIP_BIAS_RISK", "survivorship bias check requires sufficient namespace-bound PAPER samples"))
    if data_snooping_check != "PASS":
        blockers.append(_blocker("DATA_SNOOPING_RISK", "data-snooping check requires separate OOS and walk-forward windows"))

    if robustness_eligible:
        blockers = []

    report = {
        "schema_id": OVERFIT_DIAGNOSTIC_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": current_authority_hashes(),
        "diagnostic_id": diagnostic_id or f"overfit:{candidate_scorecard.get('source_runtime_cycle_id')}:{candidate_scorecard.get('candidate_id')}",
        "candidate_id": candidate_scorecard["candidate_id"],
        "strategy_id": candidate_scorecard["strategy_id"],
        "strategy_build_id": candidate_scorecard["strategy_build_id"],
        "parameter_hash": candidate_scorecard["parameter_hash"],
        "exchange": candidate_scorecard["exchange"],
        "market_type": candidate_scorecard["market_type"],
        "mode": candidate_scorecard["mode"],
        "session_id": candidate_scorecard["session_id"],
        "symbol": candidate_scorecard["symbol"],
        "timeframe_scope": candidate_scorecard["timeframe_scope"],
        "regime_scope": candidate_scorecard["regime_scope"],
        "diagnostic_status": "ROBUST_FOR_PAPER_REVIEW" if robustness_eligible else "BLOCKED_FOR_ROBUSTNESS",
        "oos_status": oos_status,
        "walk_forward_status": walk_forward_status,
        "bootstrap_status": bootstrap_status,
        "ranking_stability_status": ranking_stability_status,
        "overfit_status": overfit_status,
        "sample_count": sample_count,
        "min_required_sample_count": int(min_required_sample_count),
        "train_window_count": train_count if enough_samples else 0,
        "oos_window_count": oos_window_count,
        "walk_forward_window_count": walk_forward_window_count,
        "bootstrap_iteration_count": bootstrap_iteration_count,
        "min_required_bootstrap_iterations": int(min_required_bootstrap_iterations),
        "in_sample_net_ev_after_cost_bps": round(in_sample_ev, 8),
        "oos_net_ev_after_cost_bps": round(oos_ev, 8),
        "min_required_oos_net_ev_bps": float(min_required_oos_net_ev_bps),
        "oos_degradation_bps": round(degradation, 8),
        "max_allowed_oos_degradation_bps": float(max_allowed_oos_degradation_bps),
        "walk_forward_pass_rate": round(walk_forward_pass_rate, 8),
        "min_required_walk_forward_pass_rate": float(min_required_walk_forward_pass_rate),
        "bootstrap_confidence_lower_bps": round(bootstrap_lower, 8),
        "min_required_bootstrap_confidence_lower_bps": float(min_required_bootstrap_confidence_lower_bps),
        "ranking_stability_score": round(ranking_stability, 8),
        "min_required_ranking_stability_score": float(min_required_ranking_stability_score),
        "concentration_risk_status": concentration_status,
        "survivorship_bias_check": survivorship_bias_check,
        "data_snooping_check": data_snooping_check,
        "preliminary_robustness_status": preliminary_robustness_status,
        "preliminary_min_required_sample_count": int(min_preliminary_sample_count),
        "preliminary_sample_count": preliminary_sample_count,
        "preliminary_exact_candidate_sample_count": preliminary_exact_candidate_sample_count,
        **preliminary_meta,
        "preliminary_train_window_count": preliminary_train_count,
        "preliminary_oos_window_count": preliminary_oos_window_count,
        "preliminary_walk_forward_window_count": preliminary_walk_forward_window_count,
        "preliminary_walk_forward_window_size": preliminary_walk_forward_window_size,
        "preliminary_bootstrap_iteration_count": preliminary_bootstrap_iteration_count,
        "preliminary_oos_status": preliminary_oos_status,
        "preliminary_walk_forward_status": preliminary_walk_forward_status,
        "preliminary_bootstrap_status": preliminary_bootstrap_status,
        "preliminary_ranking_stability_status": preliminary_ranking_stability_status,
        "preliminary_concentration_risk_status": preliminary_concentration_status,
        "preliminary_in_sample_net_ev_after_cost_bps": round(preliminary_in_sample_ev, 8),
        "preliminary_oos_net_ev_after_cost_bps": round(preliminary_oos_ev, 8),
        "preliminary_oos_degradation_bps": round(preliminary_degradation, 8),
        "preliminary_walk_forward_pass_rate": round(preliminary_walk_forward_pass_rate, 8),
        "preliminary_bootstrap_confidence_lower_bps": round(preliminary_bootstrap_lower, 8),
        "preliminary_ranking_stability_score": round(preliminary_ranking_stability, 8),
        "preliminary_primary_blocker_code": preliminary_primary_blocker_code,
        "preliminary_summary": preliminary_summary,
        "preliminary_next_action": preliminary_next_action,
        "robustness_eligible": robustness_eligible,
        "dashboard_display_truth_only": True,
        "promotion_eligible": False,
        "source_evidence_ids": source_ids,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "blockers": blockers,
        "diagnostic_hash": "",
    }
    report["diagnostic_hash"] = overfit_diagnostic_report_hash(report)
    return report


def robustness_inputs_from_overfit_diagnostic(report: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    statuses = {
        "oos_status": str(report.get("oos_status") or "UNTESTED"),
        "walk_forward_status": str(report.get("walk_forward_status") or "UNTESTED"),
        "bootstrap_status": str(report.get("bootstrap_status") or "UNTESTED"),
        "overfit_status": str(report.get("overfit_status") or "UNTESTED"),
    }
    if statuses != ROBUSTNESS_PASS or not report.get("robustness_eligible"):
        public_replay_source_ids = [
            str(source_id)
            for source_id in report.get("source_evidence_ids") or []
            if isinstance(source_id, str)
            and source_id.startswith(("public_replay_robustness:", "public_market_data:"))
        ]
        return statuses, sorted(set(public_replay_source_ids))
    source_ids = set(report.get("source_evidence_ids") or [])
    oos_sources = [source_id.split(":") for source_id in source_ids if isinstance(source_id, str) and source_id.startswith("oos:")]
    for parts in oos_sources:
        if len(parts) != 3:
            continue
        cycle_id, cycle_hash = parts[1], parts[2]
        required = {robustness_source_evidence_id(prefix, cycle_id, cycle_hash) for prefix in ROBUSTNESS_SOURCE_PREFIXES}
        if required.issubset(source_ids):
            return statuses, sorted(required)
    return statuses, []


def _safe_candidate_diagnostic_filename(candidate_id: Any) -> str:
    text = str(candidate_id or "unknown-candidate")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    safe = "".join(character if character in allowed else "_" for character in text).strip("._")
    if not safe:
        safe = "unknown-candidate"
    if len(safe) > 96:
        safe = f"{safe[:80]}-{_sha256_json({'candidate_id': text})[:16]}"
    return safe


def _candidate_overfit_diagnostic_report_path(*, root: Path, report: dict[str, Any]) -> Path:
    return (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(report["session_id"])
        / "profitability"
        / "overfit_diagnostics"
        / f"{_safe_candidate_diagnostic_filename(report.get('candidate_id'))}.overfit_diagnostic_report.json"
    )


def write_overfit_diagnostic_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(report["session_id"])
        / "profitability"
        / "overfit_diagnostic_report.json"
    )
    durable_atomic_write_json(path, report)
    durable_atomic_write_json(_candidate_overfit_diagnostic_report_path(root=Path(root), report=report), report)
    return path
