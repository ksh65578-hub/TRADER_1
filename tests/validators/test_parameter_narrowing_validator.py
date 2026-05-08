import unittest

from trader1.research.profitability.candidate_scorecard import has_required_performance_source_ids
from trader1.validation.mvp0_validators import ROOT, _parameter_narrowing_errors, load_json, run_validators


FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class ParameterNarrowingValidatorTest(unittest.TestCase):
    def test_parameter_narrowing_validator_passes_with_negative_fixtures(self):
        result = run_validators(["parameter_narrowing_validator"])[0]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["blockers"], [])
        self.assertIn("proposal-only", result["notes"])

    def test_pass_fixture_requires_bound_paper_shadow_and_optimizer_evidence(self):
        report = load_json(FIXTURE_DIR / "parameter_narrowing_pass.json")
        self.assertEqual(_parameter_narrowing_errors(report), [])
        self.assertEqual(report["candidate_id"], "trend_pullback_candidate_001")
        source_ids = " ".join(report["source_evidence_ids"]).lower()
        self.assertIn("paper_shadow", source_ids)
        self.assertIn("scorecard", source_ids)
        self.assertIn("optimizer_run", source_ids)
        self.assertIn("optimizer_recommendation", source_ids)
        self.assertTrue(report["candidate_scorecard_ranking_eligible"])
        self.assertEqual(report["candidate_scorecard_scorecard_scope"], "PAPER_SCORECARD_INPUT_ONLY")
        self.assertTrue(report["candidate_scorecard_robustness_ready"])
        self.assertTrue(report["candidate_scorecard_performance_ready"])
        self.assertEqual(report["candidate_scorecard_performance_source_binding_status"], "PASS")
        self.assertTrue(
            has_required_performance_source_ids(
                report["source_evidence_ids"],
                candidate_id=report["candidate_id"],
                history_id=report["candidate_scorecard_performance_source_history_id"],
                history_hash=report["candidate_scorecard_performance_source_history_hash"],
            )
        )
        self.assertGreaterEqual(
            report["candidate_scorecard_closed_trade_sample_count"],
            report["candidate_scorecard_min_closed_trade_sample_count"],
        )
        self.assertGreaterEqual(
            report["candidate_scorecard_realized_vs_expected_sample_count"],
            report["candidate_scorecard_min_closed_trade_sample_count"],
        )
        self.assertGreaterEqual(
            report["candidate_scorecard_fill_quality_sample_count"],
            report["candidate_scorecard_min_closed_trade_sample_count"],
        )
        bindings_by_id = {
            binding["source_evidence_id"]: binding
            for binding in report["source_evidence_identity_bindings"]
        }
        self.assertEqual(set(bindings_by_id), set(report["source_evidence_ids"]))
        for binding in bindings_by_id.values():
            self.assertEqual(binding["candidate_id"], report["candidate_id"])
            self.assertEqual(binding["strategy_id"], report["strategy_id"])
            self.assertEqual(binding["proposed_parameter_hash"], report["proposed_parameter_hash"])
            self.assertEqual(binding["timeframe_scope"], report["timeframe_scope"])
            self.assertEqual(binding["regime_scope"], report["regime_scope"])
            self.assertEqual(binding["identity_match_status"], "PASS")

    def test_missing_evidence_binding_fails_closed(self):
        report = load_json(FIXTURE_DIR / "parameter_narrowing_missing_binding_fail.json")
        errors = _parameter_narrowing_errors(report)
        self.assertIn("source_evidence_id missing identity binding: optimizer_recommendation_pass", errors)

    def test_identity_mismatch_and_stale_binding_fail_closed(self):
        mismatch = load_json(FIXTURE_DIR / "parameter_narrowing_identity_mismatch_fail.json")
        mismatch_errors = _parameter_narrowing_errors(mismatch)
        self.assertIn(
            "source evidence identity binding mismatch for proposed_parameter_hash: candidate_scorecard_net_ev_pass",
            mismatch_errors,
        )

        stale = load_json(FIXTURE_DIR / "parameter_narrowing_identity_stale_fail.json")
        stale_errors = _parameter_narrowing_errors(stale)
        self.assertIn(
            "source evidence identity binding cannot be STALE: optimizer_run_pass",
            stale_errors,
        )

    def test_immature_scorecard_blocks_parameter_narrowing(self):
        report = load_json(FIXTURE_DIR / "parameter_narrowing_scorecard_immature_fail.json")
        errors = _parameter_narrowing_errors(report)
        self.assertIn(
            "paper parameter narrowing requires candidate_scorecard_performance_ready=true",
            errors,
        )
        self.assertIn(
            "paper parameter narrowing requires candidate scorecard performance source binding PASS",
            errors,
        )

    def test_candidate_scoped_performance_source_ids_are_required(self):
        report = load_json(FIXTURE_DIR / "parameter_narrowing_pass.json")
        report["source_evidence_ids"] = [
            source_id
            for source_id in report["source_evidence_ids"]
            if not source_id.startswith("performance_summary:")
        ]
        report["source_evidence_identity_bindings"] = [
            binding
            for binding in report["source_evidence_identity_bindings"]
            if not binding["source_evidence_id"].startswith("performance_summary:")
        ]

        errors = _parameter_narrowing_errors(report)

        self.assertIn(
            "paper parameter narrowing requires candidate-scoped closed trade, execution quality, and performance summary source ids",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
