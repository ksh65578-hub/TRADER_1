import copy
import unittest

from trader1.research.profitability.candidate_scorecard import (
    ROBUSTNESS_PASS,
    candidate_scorecard_from_upbit_paper_runtime_cycle,
)
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report, upbit_paper_runtime_cycle_hash
from trader1.validation.mvp0_validators import _candidate_scorecard_net_ev_errors


class CandidateScorecardFromRuntimeTest(unittest.TestCase):
    def test_runtime_cycle_builds_non_live_scorecard_with_robustness_blockers(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-positive")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertEqual(scorecard["schema_id"], "trader1.candidate_scorecard.v1")
        self.assertEqual(scorecard["candidate_id"], runtime["selected_candidate"]["candidate_id"])
        self.assertEqual(scorecard["objective_basis"], "NET_EV_AFTER_COST")
        self.assertEqual(scorecard["mode"], "PAPER")
        self.assertEqual(scorecard["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn("OOS_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})
        self.assertIn("WALK_FORWARD_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})
        self.assertFalse(scorecard["live_order_ready"])
        self.assertFalse(scorecard["live_order_allowed"])
        self.assertFalse(scorecard["can_live_trade"])
        self.assertFalse(scorecard["scale_up_allowed"])

    def test_no_trade_runtime_builds_blocked_research_scorecard_without_fill_or_live_permission(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-runtime-negative",
            edge_profile="NEGATIVE",
        )

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn("MIN_EDGE_FAIL", {blocker["code"] for blocker in scorecard["blockers"]})
        self.assertLess(scorecard["net_ev_after_cost_bps"], scorecard["min_required_edge_bps"])
        self.assertFalse(scorecard["live_order_allowed"])

    def test_robustness_pass_requires_source_evidence_before_paper_ranking(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-robust-no-source")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn("SCORECARD_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_robust_paper_scorecard_can_be_paper_ranking_input_only(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-robust")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                "oos:scorecard-runtime-robust",
                "walk_forward:scorecard-runtime-robust",
                "bootstrap:scorecard-runtime-robust",
            ],
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertTrue(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["scorecard_scope"], "PAPER_SCORECARD_INPUT_ONLY")
        self.assertEqual(scorecard["blockers"], [])
        self.assertEqual(scorecard["live_readiness_status"], "NOT_LIVE_READY")
        self.assertFalse(scorecard["live_order_allowed"])

    def test_scorecard_live_flag_mutation_is_rejected(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-live-mutation")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        mutated = copy.deepcopy(scorecard)
        mutated["live_order_allowed"] = True

        errors = _candidate_scorecard_net_ev_errors(mutated)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_invalid_runtime_cycle_cannot_become_scorecard(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-invalid-source")
        runtime["live_order_allowed"] = True
        runtime["cycle_hash"] = upbit_paper_runtime_cycle_hash(runtime)

        with self.assertRaises(ValueError):
            candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)


if __name__ == "__main__":
    unittest.main()
