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
    failure_analysis_from_scorecard,
    optimizer_memory_state_from_scorecard,
    strategy_performance_memory_from_scorecard,
    write_upbit_paper_convergence_memory_artifacts,
)
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
from trader1.validation.mvp0_validators import (
    _failure_analysis_errors,
    _optimizer_memory_state_errors,
    _strategy_performance_memory_errors,
)


PASS_PERFORMANCE_METRICS = {
    "closed_trade_sample_count": 42,
    "min_closed_trade_sample_count": 30,
    "realized_vs_expected_sample_count": 42,
    "fill_quality_sample_count": 42,
    "profit_factor": 1.42,
    "min_profit_factor": 1.25,
    "max_drawdown_pct": 4.8,
    "max_allowed_drawdown_pct": 8.0,
    "realized_vs_expected_edge_bps": 2.5,
    "min_realized_vs_expected_edge_bps": 0.0,
    "fill_quality_score": 0.91,
    "min_fill_quality_score": 0.80,
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

        self.assertEqual(_strategy_performance_memory_errors(memory), [])
        self.assertEqual(memory["performance_scope"], "PAPER_RUNTIME_SCORECARD_ONLY")
        self.assertEqual(memory["performance_status"], "COLLECTING")
        self.assertEqual(memory["source_modes"], ["PAPER"])
        self.assertFalse(memory["paper_shadow_separated"])
        self.assertIn("MEASUREMENT_MISSING", {blocker["code"] for blocker in memory["blockers"]})
        self.assertFalse(memory["live_order_allowed"])
        self.assertFalse(memory["scale_up_allowed"])

    def test_blocked_scorecard_creates_failure_analysis_and_optimizer_memory(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="convergence-memory-blocked")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)

        failure = failure_analysis_from_scorecard(scorecard)
        optimizer_memory = optimizer_memory_state_from_scorecard(scorecard, failure_analysis=failure)

        self.assertIsNotNone(failure)
        self.assertEqual(_failure_analysis_errors(failure), [])
        self.assertEqual(_optimizer_memory_state_errors(optimizer_memory), [])
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
            optimizer_memory = json.loads(written["optimizer_memory_state_path"].read_text(encoding="utf-8"))
            failure = json.loads(written["failure_analysis_path"].read_text(encoding="utf-8"))

        self.assertEqual(_strategy_performance_memory_errors(strategy_memory), [])
        self.assertEqual(_optimizer_memory_state_errors(optimizer_memory), [])
        self.assertEqual(_failure_analysis_errors(failure), [])
        self.assertFalse(strategy_memory["live_order_allowed"])
        self.assertFalse(optimizer_memory["live_order_allowed"])
        self.assertFalse(failure["live_order_allowed"])

    def test_writer_rejects_live_flag_mutated_scorecard(self):
        scorecard = _ranking_ready_scorecard()
        mutated = copy.deepcopy(scorecard)
        mutated["live_order_allowed"] = True

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                write_upbit_paper_convergence_memory_artifacts(root=Path(tmp), scorecard=mutated)


if __name__ == "__main__":
    unittest.main()
