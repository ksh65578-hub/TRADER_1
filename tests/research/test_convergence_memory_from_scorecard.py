import copy
import json
import tempfile
import unittest
from pathlib import Path

from trader1.research.profitability.candidate_scorecard import (
    PERFORMANCE_PASS,
    ROBUSTNESS_PASS,
    candidate_scorecard_from_upbit_paper_runtime_cycle,
    performance_source_evidence_id,
    robustness_source_evidence_id,
)
from trader1.research.profitability.convergence_memory import (
    convergence_objective_profile_from_scorecard,
    exploration_exploitation_policy_from_scorecard,
    failure_analysis_from_scorecard,
    optimizer_memory_state_from_scorecard,
    profit_convergence_cycle_from_scorecard,
    strategy_performance_memory_from_scorecard,
    write_upbit_paper_convergence_memory_artifacts,
)
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
from trader1.validation.mvp0_validators import (
    _failure_analysis_errors,
    _convergence_objective_profile_errors,
    _exploration_exploitation_policy_errors,
    _optimizer_memory_state_errors,
    _profit_convergence_cycle_errors,
    _strategy_performance_memory_errors,
)


PASS_PERFORMANCE_METRICS = {
    "closed_trade_sample_count": 42,
    "min_closed_trade_sample_count": 30,
    "strategy_exit_policy_sample_count": 42,
    "min_strategy_exit_policy_sample_count": 30,
    "strategy_exit_policy_match_count": 42,
    "strategy_exit_policy_mismatch_count": 0,
    "strategy_exit_reason_count": 42,
    "strategy_exit_reason_counts": [{"reason_code": "TRAILING_STOP", "count": 42}],
    "regime_outcome_sample_count": 42,
    "min_regime_outcome_sample_count": 4,
    "regime_outcome_covered_count": 4,
    "min_regime_outcome_covered_count": 4,
    "regime_outcome_trade_count": 39,
    "regime_outcome_no_trade_count": 3,
    "regime_outcome_mismatch_count": 0,
    "regime_outcome_counts": [
        {
            "regime": "UPTREND",
            "sample_count": 39,
            "trade_count": 39,
            "no_trade_count": 0,
            "mismatch_count": 0,
            "trade_allowed": True,
            "primary_blocker_code": None,
        },
        {
            "regime": "RANGE",
            "sample_count": 1,
            "trade_count": 0,
            "no_trade_count": 1,
            "mismatch_count": 0,
            "trade_allowed": True,
            "primary_blocker_code": "REGIME_MISMATCH",
        },
        {
            "regime": "DOWNTREND",
            "sample_count": 1,
            "trade_count": 0,
            "no_trade_count": 1,
            "mismatch_count": 0,
            "trade_allowed": False,
            "primary_blocker_code": "REGIME_MISMATCH",
        },
        {
            "regime": "RISK_OFF",
            "sample_count": 1,
            "trade_count": 0,
            "no_trade_count": 1,
            "mismatch_count": 0,
            "trade_allowed": False,
            "primary_blocker_code": "RISK_VETO",
        },
    ],
    "realized_vs_expected_sample_count": 42,
    "fill_quality_sample_count": 42,
    "execution_cost_sample_count": 42,
    "profit_factor": 1.42,
    "min_profit_factor": 1.25,
    "max_drawdown_pct": 4.8,
    "max_allowed_drawdown_pct": 8.0,
    "realized_vs_expected_edge_bps": 2.5,
    "min_realized_vs_expected_edge_bps": 0.0,
    "fill_quality_score": 0.91,
    "min_fill_quality_score": 0.80,
    "realized_fee_bps": 5.0,
    "realized_slippage_bps": 16.0,
    "realized_impact_bps": 3.0,
    "expected_total_execution_cost_bps": 20.0,
    "realized_total_execution_cost_bps": 21.0,
    "execution_cost_delta_bps": 1.0,
    "max_allowed_execution_cost_delta_bps": 2.0,
}


def _ranking_ready_scorecard() -> dict:
    runtime = build_upbit_paper_runtime_cycle_report(cycle_id="convergence-memory-scorecard-ready")
    candidate_id = runtime["selected_candidate"]["candidate_id"]
    return candidate_scorecard_from_upbit_paper_runtime_cycle(
        runtime,
        robustness_statuses=ROBUSTNESS_PASS,
        robustness_source_evidence_ids=[
            robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
            robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
            robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
        ],
        performance_statuses=PERFORMANCE_PASS,
        performance_metrics=PASS_PERFORMANCE_METRICS,
        performance_source_evidence_ids=[
            performance_source_evidence_id("closed_trades", runtime["cycle_id"], runtime["cycle_hash"], candidate_id),
            performance_source_evidence_id("execution_quality", runtime["cycle_id"], runtime["cycle_hash"], candidate_id),
            performance_source_evidence_id("performance_summary", runtime["cycle_id"], runtime["cycle_hash"], candidate_id),
        ],
    )


class ConvergenceMemoryFromScorecardTest(unittest.TestCase):
    def test_paper_scorecard_memory_stays_blocked_until_shadow_is_bound(self):
        scorecard = _ranking_ready_scorecard()

        memory = strategy_performance_memory_from_scorecard(scorecard)
        objective_profile = convergence_objective_profile_from_scorecard(scorecard, strategy_memory=memory)
        optimizer_memory = optimizer_memory_state_from_scorecard(scorecard)
        exploration_policy = exploration_exploitation_policy_from_scorecard(
            scorecard,
            objective_profile=objective_profile,
            strategy_memory=memory,
            optimizer_memory=optimizer_memory,
        )
        cycle = profit_convergence_cycle_from_scorecard(
            scorecard,
            objective_profile=objective_profile,
            strategy_memory=memory,
            optimizer_memory=optimizer_memory,
            exploration_policy=exploration_policy,
            failure_analysis=None,
        )

        self.assertEqual(_strategy_performance_memory_errors(memory), [])
        self.assertEqual(_convergence_objective_profile_errors(objective_profile), [])
        self.assertEqual(_optimizer_memory_state_errors(optimizer_memory), [])
        self.assertEqual(_exploration_exploitation_policy_errors(exploration_policy), [])
        self.assertEqual(_profit_convergence_cycle_errors(cycle), [])
        self.assertEqual(objective_profile["objective_status"], "EVALUATION_ONLY")
        self.assertEqual(exploration_policy["policy_status"], "ACTIVE_ANALYSIS_ONLY")
        self.assertEqual(exploration_policy["transition_decision"], "KEEP_EXPLORING")
        self.assertFalse(exploration_policy["exploitation_allowed_for_paper_ranking"])
        self.assertIn("MEASUREMENT_MISSING", {blocker["code"] for blocker in exploration_policy["blockers"]})
        self.assertEqual(cycle["exploration_exploitation_policy_validator_status"], "PASS")
        self.assertEqual(memory["performance_scope"], "PAPER_RUNTIME_SCORECARD_ONLY")
        self.assertEqual(memory["performance_status"], "COLLECTING")
        self.assertEqual(cycle["cycle_status"], "COLLECTING")
        self.assertEqual(cycle["convergence_claim"], "NO_CLAIM")
        self.assertFalse(cycle["candidate_ranking_allowed_for_paper"])
        self.assertEqual(memory["source_modes"], ["PAPER"])
        self.assertFalse(memory["paper_shadow_separated"])
        self.assertIn("MEASUREMENT_MISSING", {blocker["code"] for blocker in memory["blockers"]})
        self.assertFalse(memory["live_order_allowed"])
        self.assertFalse(memory["scale_up_allowed"])

    def test_validated_shadow_source_switches_memory_to_paper_shadow_scope_without_live_permission(self):
        scorecard = _ranking_ready_scorecard()

        with tempfile.TemporaryDirectory() as tmp:
            written = write_upbit_paper_convergence_memory_artifacts(
                root=Path(tmp),
                scorecard=scorecard,
                extra_source_modes=["SHADOW"],
                extra_source_artifact_ids=["paper_shadow_evidence_accumulation:matched:ABC"],
                profit_cycle_dependency_statuses={
                    "paper_shadow_evidence_accumulation_validator_status": "PASS",
                },
            )
            strategy_memory = json.loads(written["strategy_performance_memory_path"].read_text(encoding="utf-8"))
            optimizer_memory = json.loads(written["optimizer_memory_state_path"].read_text(encoding="utf-8"))
            exploration_policy = json.loads(written["exploration_exploitation_policy_path"].read_text(encoding="utf-8"))
            cycle = json.loads(written["profit_convergence_cycle_report_path"].read_text(encoding="utf-8"))

        self.assertEqual(_strategy_performance_memory_errors(strategy_memory), [])
        self.assertEqual(_optimizer_memory_state_errors(optimizer_memory), [])
        self.assertEqual(_exploration_exploitation_policy_errors(exploration_policy), [])
        self.assertEqual(_profit_convergence_cycle_errors(cycle), [])
        self.assertEqual(strategy_memory["source_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(strategy_memory["performance_scope"], "PAPER_SHADOW_RESEARCH_ONLY")
        self.assertEqual(strategy_memory["performance_status"], "IMPROVING_AFTER_COST")
        self.assertTrue(strategy_memory["paper_shadow_separated"])
        self.assertIn("paper_shadow_evidence_accumulation:matched:ABC", strategy_memory["source_artifact_ids"])
        regimes = {item["regime"]: item for item in strategy_memory["regime_performance"]}
        self.assertEqual(regimes["UPTREND"]["trade_count"], 39)
        self.assertEqual(regimes["RANGE"]["no_trade_count"], 1)
        self.assertEqual(regimes["DOWNTREND"]["trade_count"], 0)
        self.assertFalse(regimes["DOWNTREND"]["trade_allowed"])
        self.assertEqual(regimes["RISK_OFF"]["trade_count"], 0)
        self.assertFalse(regimes["RISK_OFF"]["trade_allowed"])
        self.assertEqual(optimizer_memory["source_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(cycle["paper_shadow_evidence_accumulation_validator_status"], "PASS")
        self.assertNotIn("MEASUREMENT_MISSING", {blocker["code"] for blocker in strategy_memory["blockers"]})
        self.assertFalse(cycle["candidate_ranking_allowed_for_paper"])
        self.assertFalse(cycle["live_order_allowed"])
        self.assertFalse(cycle["scale_up_allowed"])

    def test_blocked_scorecard_creates_failure_analysis_and_optimizer_memory(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="convergence-memory-blocked")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)

        failure = failure_analysis_from_scorecard(scorecard)
        optimizer_memory = optimizer_memory_state_from_scorecard(scorecard, failure_analysis=failure)
        strategy_memory = strategy_performance_memory_from_scorecard(scorecard)
        objective_profile = convergence_objective_profile_from_scorecard(scorecard, strategy_memory=strategy_memory)
        exploration_policy = exploration_exploitation_policy_from_scorecard(
            scorecard,
            objective_profile=objective_profile,
            strategy_memory=strategy_memory,
            optimizer_memory=optimizer_memory,
            failure_analysis=failure,
        )
        cycle = profit_convergence_cycle_from_scorecard(
            scorecard,
            objective_profile=objective_profile,
            strategy_memory=strategy_memory,
            optimizer_memory=optimizer_memory,
            exploration_policy=exploration_policy,
            failure_analysis=failure,
        )

        self.assertIsNotNone(failure)
        self.assertEqual(_failure_analysis_errors(failure), [])
        self.assertEqual(_convergence_objective_profile_errors(objective_profile), [])
        self.assertEqual(_optimizer_memory_state_errors(optimizer_memory), [])
        self.assertEqual(_exploration_exploitation_policy_errors(exploration_policy), [])
        self.assertEqual(_profit_convergence_cycle_errors(cycle), [])
        self.assertEqual(objective_profile["objective_status"], "BLOCKED")
        self.assertEqual(exploration_policy["policy_status"], "BLOCKED")
        self.assertEqual(exploration_policy["transition_decision"], "BLOCK_TRANSITION")
        self.assertIn("COOLDOWN", {blocker["code"] for blocker in exploration_policy["blockers"]})
        self.assertEqual(cycle["convergence_objective_profile_validator_status"], "PASS")
        self.assertEqual(cycle["exploration_exploitation_policy_validator_status"], "PASS")
        self.assertEqual(cycle["cycle_status"], "BLOCKED")
        self.assertFalse(cycle["candidate_ranking_allowed_for_paper"])
        self.assertTrue(cycle["blocks_live_order"])
        self.assertEqual(failure["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertTrue(failure["blocks_promotion"])
        self.assertTrue(failure["blocks_live_order"])
        self.assertEqual(optimizer_memory["blocked_candidate_count"], 1)
        self.assertFalse(optimizer_memory["live_order_allowed"])
        self.assertFalse(optimizer_memory["scale_up_allowed"])

    def test_optimizer_memory_append_preserves_previous_failed_candidate(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="convergence-memory-append")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        first_failure = failure_analysis_from_scorecard(scorecard)
        first_state = optimizer_memory_state_from_scorecard(scorecard, failure_analysis=first_failure)
        second_failure = failure_analysis_from_scorecard(scorecard, previous_failure_reports=[first_failure])

        second_state = optimizer_memory_state_from_scorecard(
            scorecard,
            previous_memory_state=first_state,
            failure_analysis=second_failure,
        )

        self.assertEqual(_failure_analysis_errors(second_failure), [])
        self.assertEqual(_optimizer_memory_state_errors(second_state), [])
        self.assertEqual(second_state["memory_sequence_number"], 2)
        self.assertEqual(second_state["previous_memory_state_hash"], first_state["memory_state_hash"])
        self.assertEqual(second_state["blocked_candidate_count"], 2)
        self.assertEqual(len(second_state["candidate_memory_records"]), 2)
        self.assertTrue(second_failure["repeated_failure_same_root_cause"])
        self.assertFalse(second_state["forget_failed_candidate_allowed"])

    def test_writer_persists_strategy_memory_optimizer_memory_and_failure_analysis(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="convergence-memory-writer")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)

        with tempfile.TemporaryDirectory() as tmp:
            written = write_upbit_paper_convergence_memory_artifacts(root=Path(tmp), scorecard=scorecard)
            strategy_memory = json.loads(written["strategy_performance_memory_path"].read_text(encoding="utf-8"))
            objective_profile = json.loads(written["convergence_objective_profile_path"].read_text(encoding="utf-8"))
            exploration_policy = json.loads(written["exploration_exploitation_policy_path"].read_text(encoding="utf-8"))
            optimizer_memory = json.loads(written["optimizer_memory_state_path"].read_text(encoding="utf-8"))
            failure = json.loads(written["failure_analysis_path"].read_text(encoding="utf-8"))
            cycle = json.loads(written["profit_convergence_cycle_report_path"].read_text(encoding="utf-8"))

        self.assertEqual(_strategy_performance_memory_errors(strategy_memory), [])
        self.assertEqual(_convergence_objective_profile_errors(objective_profile), [])
        self.assertEqual(_exploration_exploitation_policy_errors(exploration_policy), [])
        self.assertEqual(_optimizer_memory_state_errors(optimizer_memory), [])
        self.assertEqual(_failure_analysis_errors(failure), [])
        self.assertEqual(_profit_convergence_cycle_errors(cycle), [])
        self.assertFalse(strategy_memory["live_order_allowed"])
        self.assertFalse(exploration_policy["live_order_allowed"])
        self.assertFalse(optimizer_memory["live_order_allowed"])
        self.assertFalse(failure["live_order_allowed"])
        self.assertFalse(cycle["live_order_allowed"])

    def test_writer_rejects_live_flag_mutated_scorecard(self):
        scorecard = _ranking_ready_scorecard()
        mutated = copy.deepcopy(scorecard)
        mutated["live_order_allowed"] = True

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                write_upbit_paper_convergence_memory_artifacts(root=Path(tmp), scorecard=mutated)


if __name__ == "__main__":
    unittest.main()
