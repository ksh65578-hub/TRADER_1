from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.research.profitability.candidate_scorecard import (
    current_authority_hashes,
    source_role_semantics_errors,
    stable_hash,
    strict_robustness_triplet_binding_from_source_ids,
)
from trader1.research.profitability.overfit_diagnostic import overfit_diagnostic_report_hash
from trader1.research.replay.replay_runner import (
    public_replay_robustness_report_hash,
    validate_public_replay_robustness_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


STRATEGY_MUTATION_COMPILER_SCHEMA_ID = "trader1.strategy_mutation_compiler_report.v1"
MUTATED_PAPER_CANDIDATE_SPEC_SCHEMA_ID = "trader1.mutated_paper_candidate_spec.v1"
MUTATION_BUDGET_STATE_SCHEMA_ID = "trader1.mutation_budget_state.v1"
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_UPBIT_PAPER_SESSION_ID = "mvp1_upbit_paper_launcher"

LIVE_PRIVATE_ORDER_FLAGS = (
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
LIVE_FALSE_FLAGS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
MAX_PARAMETER_DELTA_PCT = 20.0
MAX_MUTATION_DELTA_COUNT = 3


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def strategy_mutation_compiler_report_hash(report: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in report.items() if key != "report_hash"})


def mutated_paper_candidate_spec_hash(spec: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in spec.items() if key != "spec_hash"})


def blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _integer(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _has_live_private_order_drift(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in LIVE_PRIVATE_ORDER_FLAGS and item is True:
                return True
            if isinstance(item, (dict, list)) and _has_live_private_order_drift(item):
                return True
    elif isinstance(value, list):
        return any(_has_live_private_order_drift(item) for item in value)
    return False


def _codes_from_blockers(value: dict[str, Any] | None) -> set[str]:
    return {
        str(item.get("code"))
        for item in (value or {}).get("blockers", [])
        if isinstance(item, dict) and item.get("code")
    }


def _artifact_hash(value: dict[str, Any] | None, *, hash_field: str | None = None) -> str:
    if not isinstance(value, dict):
        return "0" * 64
    if hash_field and isinstance(value.get(hash_field), str) and len(str(value[hash_field])) == 64:
        return str(value[hash_field]).upper()
    return sha256_json(value)


def _source_evidence_ids(
    *,
    scorecard: dict[str, Any],
    overfit_diagnostic: dict[str, Any],
    convergence_memory: dict[str, Any],
    optimizer_memory: dict[str, Any],
    replay_evidence: dict[str, Any],
) -> list[str]:
    replay_hash = _artifact_hash(replay_evidence, hash_field="report_hash")
    overfit_hash = _artifact_hash(overfit_diagnostic, hash_field="diagnostic_hash")
    optimizer_hash = _artifact_hash(optimizer_memory, hash_field="memory_state_hash")
    strategy_memory_hash = _artifact_hash(convergence_memory, hash_field="strategy_performance_memory_hash")
    return sorted(
        {
            f"candidate_scorecard:{scorecard.get('scorecard_id')}:{sha256_json(scorecard)}",
            f"overfit_diagnostic:{overfit_diagnostic.get('diagnostic_id')}:{overfit_hash}",
            f"strategy_performance_memory:{convergence_memory.get('strategy_performance_memory_id')}:{strategy_memory_hash}",
            f"optimizer_memory_state:{optimizer_memory.get('optimizer_memory_state_id')}:{optimizer_hash}",
            f"public_replay_robustness:{replay_evidence.get('replay_id')}:{replay_hash}",
        }
    )


def _scope_mismatch_blocker(
    *,
    scorecard: dict[str, Any],
    overfit_diagnostic: dict[str, Any],
    convergence_memory: dict[str, Any],
    optimizer_memory: dict[str, Any],
    replay_evidence: dict[str, Any],
) -> dict[str, str] | None:
    scorecard_scope = {
        "candidate_id": str(scorecard.get("candidate_id") or ""),
        "strategy_id": str(scorecard.get("strategy_id") or ""),
        "strategy_build_id": str(scorecard.get("strategy_build_id") or ""),
        "parameter_hash": str(scorecard.get("parameter_hash") or "").upper(),
        "symbol": str(scorecard.get("symbol") or ""),
        "session_id": str(scorecard.get("session_id") or ""),
    }
    for artifact_name, artifact, fields in (
        ("overfit diagnostic", overfit_diagnostic, ("candidate_id", "strategy_id", "strategy_build_id", "parameter_hash", "symbol", "session_id")),
        ("public replay evidence", replay_evidence, ("candidate_id", "strategy_id", "strategy_build_id", "parameter_hash", "symbol", "session_id")),
        ("strategy performance memory", convergence_memory, ("strategy_id", "strategy_build_id", "parameter_hash", "session_id")),
        ("optimizer memory", optimizer_memory, ("strategy_id", "strategy_build_id", "parameter_hash", "session_id")),
    ):
        if not isinstance(artifact, dict):
            return blocker("MEASUREMENT_MISSING", f"{artifact_name} is missing")
        for field in fields:
            if str(artifact.get(field) or "").upper() != scorecard_scope[field].upper():
                return blocker("SNAPSHOT_SCOPE_MISMATCH", f"{artifact_name} {field} does not match candidate scorecard")
    if scorecard.get("exchange") != "UPBIT" or scorecard.get("market_type") != "KRW_SPOT" or scorecard.get("mode") != "PAPER":
        return blocker("SNAPSHOT_SCOPE_MISMATCH", "mutation compiler accepts only UPBIT/KRW_SPOT/PAPER scorecards")
    if replay_evidence.get("mode") != "REPLAY":
        return blocker("SNAPSHOT_SCOPE_MISMATCH", "mutation replay evidence must be REPLAY scoped")
    return None


def _source_hash_blocker(
    *,
    overfit_diagnostic: dict[str, Any],
    replay_evidence: dict[str, Any],
) -> dict[str, str] | None:
    replay_hash = str(replay_evidence.get("report_hash") or "").upper()
    if replay_hash != public_replay_robustness_report_hash(replay_evidence).upper():
        return blocker("SCHEMA_IDENTITY_MISMATCH", "public replay evidence hash mismatch")
    diagnostic_hash = str(overfit_diagnostic.get("diagnostic_hash") or "").upper()
    if diagnostic_hash and diagnostic_hash != overfit_diagnostic_report_hash(overfit_diagnostic).upper():
        return blocker("SCHEMA_IDENTITY_MISMATCH", "overfit diagnostic hash mismatch")
    return None


def _robustness_blocker(
    *,
    scorecard: dict[str, Any],
    overfit_diagnostic: dict[str, Any],
) -> dict[str, str] | None:
    source_ids = [str(item) for item in scorecard.get("source_evidence_ids") or []]
    role_errors = source_role_semantics_errors(source_ids)
    if role_errors or "SOURCE_ROLE_SEMANTICS_MISMATCH" in _codes_from_blockers(scorecard):
        return blocker("SOURCE_ROLE_SEMANTICS_MISMATCH", "; ".join(role_errors[:3]) or "source role semantics mismatch")
    triplet = strict_robustness_triplet_binding_from_source_ids(
        source_ids,
        cycle_id=str(scorecard.get("source_runtime_cycle_id") or ""),
        cycle_hash=str(scorecard.get("source_runtime_cycle_hash") or ""),
    )
    if triplet is None or "ROBUSTNESS_TRIPLET_MISMATCH" in _codes_from_blockers(scorecard):
        return blocker(
            "ROBUSTNESS_TRIPLET_MISMATCH",
            "OOS, walk-forward, and bootstrap evidence must bind to one source runtime cycle/hash triplet",
        )
    for field, missing_code, failed_code in (
        ("oos_status", "OOS_MISSING", "OOS_FAILED"),
        ("walk_forward_status", "WALK_FORWARD_MISSING", "WALK_FORWARD_FAILED"),
        ("bootstrap_status", "BOOTSTRAP_UNSTABLE", "BOOTSTRAP_FAILED"),
    ):
        scorecard_status = str(scorecard.get(field) or "")
        diagnostic_status = str(overfit_diagnostic.get(field) or "")
        if scorecard_status != "PASS" or diagnostic_status != "PASS":
            return blocker(failed_code if "FAIL" in {scorecard_status, diagnostic_status} else missing_code, f"{field} must PASS before mutation")
    if scorecard.get("overfit_status") != "LOW" or overfit_diagnostic.get("overfit_status") != "LOW":
        return blocker("OVERFIT_RISK_HIGH", "overfit status must be LOW before mutation")
    return None


def _replay_maturity_blocker(replay_evidence: dict[str, Any]) -> dict[str, str] | None:
    validation = validate_public_replay_robustness_report(replay_evidence)
    if validation.status != "PASS":
        return blocker(validation.blocker_code or "PUBLIC_REPLAY_ROBUSTNESS_FAILED", validation.message)
    if replay_evidence.get("replay_closed_trade_maturity_status") != "PASS":
        code = str(replay_evidence.get("replay_closed_trade_maturity_blocker_code") or "REPLAY_CLOSED_TRADES_MISSING")
        return blocker(code, "public replay closed-trade maturity must PASS before mutation")
    closed_count = _integer(replay_evidence.get("replay_closed_trade_sample_count"))
    min_count = _integer(replay_evidence.get("min_required_closed_trade_sample_count"), 1)
    if closed_count < min_count:
        return blocker("REPLAY_CLOSED_TRADES_BELOW_MIN", "public replay closed-trade count is below mutation threshold")
    if replay_evidence.get("replay_status") != "PASS":
        return blocker(str(replay_evidence.get("primary_blocker_code") or "PUBLIC_REPLAY_ROBUSTNESS_FAILED"), "public replay status must PASS")
    return None


def _raw_pnl_only_blocker(scorecard: dict[str, Any]) -> dict[str, str] | None:
    gross_edge = _number(scorecard.get("gross_expected_edge_bps"))
    net_ev = _number(scorecard.get("net_ev_after_cost_bps"))
    if gross_edge > 0 and net_ev <= 0:
        return blocker("COST_AFTER_EDGE_UNVERIFIED", "raw edge is positive but net EV after fee/slippage/impact is not positive")
    if scorecard.get("cost_model_status") != "VALIDATED" or scorecard.get("execution_cost_comparison_status") != "PASS":
        return blocker("COST_AFTER_EDGE_UNVERIFIED", "execution cost model must pass before mutation")
    return None


def _normal_budget_state(
    *,
    session_id: str,
    strategy_id: str,
    source: dict[str, Any] | None,
) -> dict[str, Any]:
    raw = source or {}
    today = datetime.now(timezone.utc).date().isoformat()
    state = {
        "schema_id": MUTATION_BUDGET_STATE_SCHEMA_ID,
        "budget_date_utc": str(raw.get("budget_date_utc") or today),
        "session_id": session_id,
        "strategy_id": strategy_id,
        "daily_exploration_budget": _integer(raw.get("daily_exploration_budget"), 8),
        "daily_exploration_used": _integer(raw.get("daily_exploration_used"), 0),
        "strategy_family_mutation_budget": _integer(raw.get("strategy_family_mutation_budget"), 3),
        "strategy_family_mutation_used": _integer(raw.get("strategy_family_mutation_used"), 0),
        "max_concurrent_experimental_candidates": _integer(raw.get("max_concurrent_experimental_candidates"), 2),
        "concurrent_experimental_candidate_count": _integer(raw.get("concurrent_experimental_candidate_count"), 0),
        "replay_cost_budget": _integer(raw.get("replay_cost_budget"), 420),
        "replay_cost_used": _integer(raw.get("replay_cost_used"), 0),
        "candidate_retirement_budget": _integer(raw.get("candidate_retirement_budget"), 3),
        "candidate_retirement_used": _integer(raw.get("candidate_retirement_used"), 0),
    }
    state["exploration_budget_id"] = str(
        raw.get("exploration_budget_id")
        or f"mutation-budget:{state['budget_date_utc']}:{session_id}:{strategy_id}:{sha256_json(state)[:12]}"
    )
    state["budget_hash"] = sha256_json(state)
    return state


def _budget_blocker(state: dict[str, Any]) -> dict[str, str] | None:
    if state["daily_exploration_used"] >= state["daily_exploration_budget"]:
        return blocker("CANDIDATE_BUDGET_EXCEEDED", "daily exploration mutation budget is exhausted")
    if state["strategy_family_mutation_used"] >= state["strategy_family_mutation_budget"]:
        return blocker("CANDIDATE_BUDGET_EXCEEDED", "strategy-family mutation budget is exhausted")
    if state["concurrent_experimental_candidate_count"] >= state["max_concurrent_experimental_candidates"]:
        return blocker("OPTIMIZER_RESOURCE_LIMIT", "max concurrent experimental candidates is reached")
    if state["replay_cost_used"] >= state["replay_cost_budget"]:
        return blocker("EXPLORATION_RESOURCE_LIMIT", "replay cost mutation budget is exhausted")
    if state["candidate_retirement_used"] >= state["candidate_retirement_budget"]:
        return blocker("OPTIMIZER_RESOURCE_LIMIT", "candidate retirement review budget is exhausted")
    return None


def _delta_pct(baseline: float, mutated: float) -> float:
    if baseline == 0:
        return 0.0 if mutated == 0 else 100.0
    return (mutated - baseline) / abs(baseline) * 100.0


def _delta(parameter_id: str, baseline: float, mutated: float, rationale: str) -> dict[str, Any]:
    return {
        "parameter_id": parameter_id,
        "baseline_value": baseline,
        "mutated_value": mutated,
        "delta_pct": _delta_pct(baseline, mutated),
        "rationale": rationale,
    }


def _delta_violation(deltas: list[dict[str, Any]]) -> dict[str, str] | None:
    if len(deltas) > MAX_MUTATION_DELTA_COUNT:
        return blocker("EXPANDED_BOUND_UNVERIFIED", "mutation changes more than three parameters")
    for item in deltas:
        if not isinstance(item, dict) or not item.get("parameter_id"):
            return blocker("EXPANDED_BOUND_UNVERIFIED", "mutation parameter delta is malformed")
        if abs(_number(item.get("delta_pct"), 1000.0)) > MAX_PARAMETER_DELTA_PCT:
            return blocker("EXPANDED_BOUND_UNVERIFIED", "mutation parameter delta exceeds 20 percent bound")
    return None


def _mutation_reason(
    *,
    scorecard: dict[str, Any],
    execution_delta: dict[str, Any] | None,
    exit_policy_mismatch: dict[str, Any] | bool | None,
    realized_vs_expected_edge: dict[str, Any] | float | None,
) -> str:
    max_cost_delta = _number(scorecard.get("max_allowed_execution_cost_delta_bps"), 2.0)
    observed_cost_delta = _number((execution_delta or {}).get("execution_cost_delta_bps"), _number(scorecard.get("execution_cost_delta_bps")))
    if scorecard.get("execution_cost_comparison_status") != "PASS" or observed_cost_delta > max_cost_delta:
        return "EXECUTION_COST_DIVERGENCE"
    mismatch_count = _integer(scorecard.get("strategy_exit_policy_mismatch_count"))
    mismatch_requested = bool(exit_policy_mismatch)
    if isinstance(exit_policy_mismatch, dict):
        mismatch_requested = bool(exit_policy_mismatch.get("mismatch_detected", True))
    if scorecard.get("strategy_exit_policy_status") != "PASS" or mismatch_count > 0 or mismatch_requested:
        return "EXIT_POLICY_MISMATCH"
    if isinstance(realized_vs_expected_edge, dict):
        realized_edge = _number(realized_vs_expected_edge.get("realized_vs_expected_edge_bps"))
    elif realized_vs_expected_edge is not None:
        realized_edge = _number(realized_vs_expected_edge)
    else:
        realized_edge = _number(scorecard.get("realized_vs_expected_edge_bps"))
    if realized_edge < _number(scorecard.get("min_realized_vs_expected_edge_bps")):
        return "REALIZED_EXPECTED_EDGE_DEFICIT"
    if _number(scorecard.get("profit_factor")) < _number(scorecard.get("min_profit_factor"), 1.0):
        return "PROFIT_FACTOR_WEAKNESS"
    if _number(scorecard.get("max_drawdown_pct")) > _number(scorecard.get("max_allowed_drawdown_pct"), 100.0):
        return "DRAWDOWN_GUARD_TIGHTENING"
    return "BOUNDED_EXPLORATION"


def _default_deltas(reason: str, scorecard: dict[str, Any]) -> tuple[list[dict[str, Any]], float, float]:
    if reason == "EXECUTION_COST_DIVERGENCE":
        baseline = max(1.0, _number(scorecard.get("max_allowed_execution_cost_delta_bps"), 2.0))
        return [_delta("max_execution_cost_delta_bps", baseline, baseline * 0.85, "tighten execution cost tolerance")], -6.0, -0.02
    if reason == "EXIT_POLICY_MISMATCH":
        return [_delta("exit_confirmation_window", 1.0, 1.15, "require stronger exit-policy confirmation")], -4.0, -0.02
    if reason == "REALIZED_EXPECTED_EDGE_DEFICIT":
        return [_delta("expected_edge_scale", 1.0, 0.90, "discount expected edge after realized underperformance")], -8.0, -0.03
    if reason in {"PROFIT_FACTOR_WEAKNESS", "DRAWDOWN_GUARD_TIGHTENING"}:
        return [_delta("entry_signal_floor", 0.55, 0.60, "raise entry threshold for weaker risk-adjusted outcome")], -3.0, -0.01
    return [_delta("exploration_band", 1.0, 1.05, "bounded neighborhood exploration around validated parent")], 0.0, 0.0


class StrategyMutationCompiler:
    def compile(
        self,
        *,
        candidate_scorecard: dict[str, Any] | None,
        overfit_diagnostic: dict[str, Any] | None,
        convergence_memory: dict[str, Any] | None,
        optimizer_memory: dict[str, Any] | None,
        replay_closed_trade_evidence: dict[str, Any] | None,
        execution_delta: dict[str, Any] | None = None,
        exit_policy_mismatch: dict[str, Any] | bool | None = None,
        realized_vs_expected_edge: dict[str, Any] | float | None = None,
        mutation_budget_state: dict[str, Any] | None = None,
        requested_parameter_deltas: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        scorecard = candidate_scorecard if isinstance(candidate_scorecard, dict) else None
        diagnostic = overfit_diagnostic if isinstance(overfit_diagnostic, dict) else None
        strategy_memory = convergence_memory if isinstance(convergence_memory, dict) else None
        opt_memory = optimizer_memory if isinstance(optimizer_memory, dict) else None
        replay = replay_closed_trade_evidence if isinstance(replay_closed_trade_evidence, dict) else None
        if not all(isinstance(item, dict) for item in (scorecard, diagnostic, strategy_memory, opt_memory, replay)):
            return self._blocked(
                scorecard=scorecard or {},
                budget_state={},
                source_evidence_ids=[],
                blocker_item=blocker("MEASUREMENT_MISSING", "mutation compiler requires scorecard, overfit, convergence memory, optimizer memory, and replay evidence"),
            )
        assert scorecard is not None and diagnostic is not None and strategy_memory is not None and opt_memory is not None and replay is not None
        budget = _normal_budget_state(
            session_id=str(scorecard.get("session_id") or DEFAULT_UPBIT_PAPER_SESSION_ID),
            strategy_id=str(scorecard.get("strategy_id") or "unknown_strategy"),
            source=mutation_budget_state,
        )
        sources = _source_evidence_ids(
            scorecard=scorecard,
            overfit_diagnostic=diagnostic,
            convergence_memory=strategy_memory,
            optimizer_memory=opt_memory,
            replay_evidence=replay,
        )
        for check in (
            blocker("LIVE_FINAL_GUARD_FAILED", "mutation inputs attempted private/order/live/key behavior")
            if _has_live_private_order_drift([scorecard, diagnostic, strategy_memory, opt_memory, replay])
            else None,
            _scope_mismatch_blocker(
                scorecard=scorecard,
                overfit_diagnostic=diagnostic,
                convergence_memory=strategy_memory,
                optimizer_memory=opt_memory,
                replay_evidence=replay,
            ),
            _source_hash_blocker(overfit_diagnostic=diagnostic, replay_evidence=replay),
            _robustness_blocker(scorecard=scorecard, overfit_diagnostic=diagnostic),
            _replay_maturity_blocker(replay),
            _raw_pnl_only_blocker(scorecard),
            _budget_blocker(budget),
        ):
            if check is not None:
                return self._blocked(scorecard=scorecard, budget_state=budget, source_evidence_ids=sources, blocker_item=check)
        reason = _mutation_reason(
            scorecard=scorecard,
            execution_delta=execution_delta,
            exit_policy_mismatch=exit_policy_mismatch,
            realized_vs_expected_edge=realized_vs_expected_edge,
        )
        if requested_parameter_deltas is not None:
            deltas = [dict(item) for item in requested_parameter_deltas]
            edge_delta_bps = _number(sum(_number(item.get("edge_delta_bps")) for item in deltas))
            signal_delta = _number(sum(_number(item.get("signal_delta")) for item in deltas))
        else:
            deltas, edge_delta_bps, signal_delta = _default_deltas(reason, scorecard)
        delta_blocker = _delta_violation(deltas)
        if delta_blocker is not None:
            return self._failed(scorecard=scorecard, budget_state=budget, source_evidence_ids=sources, blocker_item=delta_blocker)
        return self._pass(
            scorecard=scorecard,
            budget_state=budget,
            source_evidence_ids=sources,
            mutation_reason_code=reason,
            bounded_parameter_delta=deltas,
            edge_delta_bps=edge_delta_bps,
            signal_delta=signal_delta,
        )

    def _base(
        self,
        *,
        scorecard: dict[str, Any],
        budget_state: dict[str, Any],
        source_evidence_ids: list[str],
    ) -> dict[str, Any]:
        return {
            "schema_id": STRATEGY_MUTATION_COMPILER_SCHEMA_ID,
            "generated_at_utc": utc_now(),
            "project_id": "TRADER_1",
            "authority": current_authority_hashes(),
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": str(scorecard.get("session_id") or DEFAULT_UPBIT_PAPER_SESSION_ID),
            "candidate_id": scorecard.get("candidate_id"),
            "strategy_id": scorecard.get("strategy_id"),
            "strategy_build_id": scorecard.get("strategy_build_id"),
            "parent_parameter_hash": str(scorecard.get("parameter_hash") or "").upper() or None,
            "source_evidence_ids": source_evidence_ids,
            "mutation_budget_state": budget_state,
            "mutated_paper_candidate_spec": None,
            "ranking_eligible": False,
            "credential_load_attempted": False,
            "private_endpoint_called": False,
            "order_endpoint_called": False,
            "order_adapter_called": False,
            "live_key_loaded": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    def _blocked(
        self,
        *,
        scorecard: dict[str, Any],
        budget_state: dict[str, Any],
        source_evidence_ids: list[str],
        blocker_item: dict[str, str],
    ) -> dict[str, Any]:
        report = self._base(scorecard=scorecard, budget_state=budget_state, source_evidence_ids=source_evidence_ids)
        report.update(
            {
                "compile_status": "BLOCKED",
                "status": "BLOCKED",
                "mutation_reason_code": None,
                "primary_blocker_code": blocker_item["code"],
                "blockers": [blocker_item],
                "next_action": "Keep collecting non-live evidence; mutation output remains blocked.",
            }
        )
        report["report_hash"] = strategy_mutation_compiler_report_hash(report)
        return report

    def _failed(
        self,
        *,
        scorecard: dict[str, Any],
        budget_state: dict[str, Any],
        source_evidence_ids: list[str],
        blocker_item: dict[str, str],
    ) -> dict[str, Any]:
        report = self._base(scorecard=scorecard, budget_state=budget_state, source_evidence_ids=source_evidence_ids)
        report.update(
            {
                "compile_status": "FAIL",
                "status": "FAIL",
                "mutation_reason_code": None,
                "primary_blocker_code": blocker_item["code"],
                "blockers": [blocker_item],
                "next_action": "Reject the unsafe mutation delta; do not pass it into replay or PAPER.",
            }
        )
        report["report_hash"] = strategy_mutation_compiler_report_hash(report)
        return report

    def _pass(
        self,
        *,
        scorecard: dict[str, Any],
        budget_state: dict[str, Any],
        source_evidence_ids: list[str],
        mutation_reason_code: str,
        bounded_parameter_delta: list[dict[str, Any]],
        edge_delta_bps: float,
        signal_delta: float,
    ) -> dict[str, Any]:
        report = self._base(scorecard=scorecard, budget_state=budget_state, source_evidence_ids=source_evidence_ids)
        mutation_id = f"mutation:{scorecard.get('candidate_id')}:{sha256_json([mutation_reason_code, bounded_parameter_delta, source_evidence_ids])[:16]}"
        mutated_parameter_hash = stable_hash(f"{scorecard.get('parameter_hash')}:{mutation_id}:{sha256_json(bounded_parameter_delta)}")
        lineage = {
            "parent_candidate_id": scorecard.get("candidate_id"),
            "parent_scorecard_id": scorecard.get("scorecard_id"),
            "parent_parameter_hash": scorecard.get("parameter_hash"),
            "source_runtime_cycle_id": scorecard.get("source_runtime_cycle_id"),
            "source_runtime_cycle_hash": scorecard.get("source_runtime_cycle_hash"),
            "source_evidence_ids": source_evidence_ids,
        }
        spec = {
            "schema_id": MUTATED_PAPER_CANDIDATE_SPEC_SCHEMA_ID,
            "generated_at_utc": utc_now(),
            "project_id": "TRADER_1",
            "spec_id": f"mutated-paper-candidate-spec:{mutation_id}",
            "mutation_id": mutation_id,
            "mutation_status": "PASS",
            "candidate_id": scorecard.get("candidate_id"),
            "parent_candidate_id": scorecard.get("candidate_id"),
            "symbol": scorecard.get("symbol"),
            "strategy_id": scorecard.get("strategy_id"),
            "strategy_build_id": scorecard.get("strategy_build_id"),
            "parent_parameter_hash": scorecard.get("parameter_hash"),
            "parameter_hash": mutated_parameter_hash,
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "allowed_output_modes": ["REPLAY", "PAPER"],
            "timeframe_scope": scorecard.get("timeframe_scope"),
            "regime_scope": scorecard.get("regime_scope"),
            "mutation_reason_code": mutation_reason_code,
            "mutation_reason": mutation_reason_code.lower().replace("_", " "),
            "bounded_parameter_delta": bounded_parameter_delta,
            "edge_delta_bps": edge_delta_bps,
            "signal_delta": signal_delta,
            "exploration_budget_id": budget_state.get("exploration_budget_id"),
            "parent_candidate_lineage": lineage,
            "source_evidence_ids": source_evidence_ids,
            "ranking_eligible": False,
            "replay_input_allowed": True,
            "paper_input_allowed": True,
            "live_config_mutation_allowed": False,
            "writes_live_ready_snapshot": False,
            "credential_load_attempted": False,
            "private_endpoint_called": False,
            "order_endpoint_called": False,
            "order_adapter_called": False,
            "live_key_loaded": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        spec["spec_hash"] = mutated_paper_candidate_spec_hash(spec)
        report.update(
            {
                "compile_status": "PASS",
                "status": "PASS",
                "mutation_reason_code": mutation_reason_code,
                "primary_blocker_code": None,
                "blockers": [],
                "mutated_paper_candidate_spec": spec,
                "next_action": "Pass this PAPER-only mutation spec into bounded replay or the next PAPER scope focus; ranking remains false.",
            }
        )
        report["report_hash"] = strategy_mutation_compiler_report_hash(report)
        return report


def validate_strategy_mutation_compiler_report(report: dict[str, Any]) -> tuple[str, str, str | None]:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "compile_status",
        "status",
        "primary_blocker_code",
        "blockers",
        "mutated_paper_candidate_spec",
        "ranking_eligible",
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
        return "FAIL", f"strategy mutation report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("schema_id") != STRATEGY_MUTATION_COMPILER_SCHEMA_ID:
        return "FAIL", "strategy mutation report schema mismatch", "SCHEMA_IDENTITY_MISMATCH"
    if _has_live_private_order_drift(report):
        return "BLOCKED", "strategy mutation report attempted live/private/order/key behavior", "LIVE_FINAL_GUARD_FAILED"
    if report.get("ranking_eligible") is not False:
        return "FAIL", "mutation compiler output must keep ranking_eligible=false", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("report_hash") != strategy_mutation_compiler_report_hash(report):
        return "FAIL", "strategy mutation report hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("compile_status") == "PASS":
        spec = report.get("mutated_paper_candidate_spec")
        if not isinstance(spec, dict):
            return "FAIL", "PASS mutation requires mutated PAPER candidate spec", "SCHEMA_IDENTITY_MISMATCH"
        if spec.get("schema_id") != MUTATED_PAPER_CANDIDATE_SPEC_SCHEMA_ID or spec.get("mode") != "PAPER":
            return "BLOCKED", "mutated candidate spec must be PAPER scoped", "SNAPSHOT_SCOPE_MISMATCH"
        if spec.get("ranking_eligible") is not False:
            return "FAIL", "mutated candidate spec must keep ranking_eligible=false", "SCHEMA_IDENTITY_MISMATCH"
        if spec.get("spec_hash") != mutated_paper_candidate_spec_hash(spec):
            return "FAIL", "mutated candidate spec hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        delta_blocker = _delta_violation(list(spec.get("bounded_parameter_delta") or []))
        if delta_blocker is not None:
            return "BLOCKED", delta_blocker["message"], delta_blocker["code"]
    elif report.get("compile_status") not in {"BLOCKED", "FAIL"}:
        return "FAIL", "strategy mutation compile_status must be PASS, BLOCKED, or FAIL", "SCHEMA_IDENTITY_MISMATCH"
    return "PASS", "strategy mutation report is PAPER-only, budget-scoped, and fail-closed", None


def strategy_mutation_compiler_report_path(
    root: Path = ROOT,
    session_id: str = DEFAULT_UPBIT_PAPER_SESSION_ID,
) -> Path:
    return (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / session_id
        / "profitability"
        / "mutation"
        / "strategy_mutation_compiler_report.json"
    )


def write_strategy_mutation_compiler_report(
    *,
    root: Path = ROOT,
    report: dict[str, Any],
) -> Path:
    status, message, blocker_code = validate_strategy_mutation_compiler_report(report)
    if status != "PASS":
        raise ValueError(f"strategy mutation compiler report failed validation: {blocker_code or status}: {message}")
    path = strategy_mutation_compiler_report_path(root=root, session_id=str(report["session_id"]))
    durable_atomic_write_json(path, report)
    spec = report.get("mutated_paper_candidate_spec")
    if isinstance(spec, dict):
        spec_dir = path.parent / "specs"
        spec_path = spec_dir / f"{str(spec['mutation_id']).replace(':', '-')}.mutated_paper_candidate_spec.json"
        durable_atomic_write_json(spec_path, spec)
    return path


def load_validated_mutation_spec_for_candidate(
    *,
    root: Path = ROOT,
    session_id: str = DEFAULT_UPBIT_PAPER_SESSION_ID,
    candidate_id: str,
) -> dict[str, Any] | None:
    path = strategy_mutation_compiler_report_path(root=root, session_id=session_id)
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    status, _, _ = validate_strategy_mutation_compiler_report(report)
    if status != "PASS" or report.get("compile_status") != "PASS":
        return None
    spec = report.get("mutated_paper_candidate_spec")
    if not isinstance(spec, dict) or str(spec.get("candidate_id") or "") != candidate_id:
        return None
    return dict(spec)
