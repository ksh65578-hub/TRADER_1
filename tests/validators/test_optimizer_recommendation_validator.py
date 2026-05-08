import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _optimizer_recommendation_errors,
    load_json,
    optimizer_recommendation_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class OptimizerRecommendationValidatorTest(unittest.TestCase):
    def test_pass_fixture_is_paper_ranking_only(self):
        report = load_json(FIXTURE_DIR / "optimizer_recommendation_pass.json")

        errors = _optimizer_recommendation_errors(report)

        self.assertEqual(errors, [])
        self.assertTrue(report["source_scorecard_ranking_eligible"])
        self.assertEqual(report["source_scorecard_scope"], "PAPER_SCORECARD_INPUT_ONLY")
        self.assertTrue(report["source_scorecard_robustness_ready"])
        self.assertTrue(report["source_scorecard_performance_ready"])
        self.assertEqual(report["source_scorecard_performance_source_binding_status"], "PASS")

    def test_recommendation_cannot_carry_live_permission(self):
        report = load_json(FIXTURE_DIR / "optimizer_recommendation_live_flag_fail.json")

        errors = _optimizer_recommendation_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_recommendation_cannot_use_misleading_live_ready_wording(self):
        report = load_json(FIXTURE_DIR / "optimizer_recommendation_live_ready_wording_fail.json")

        errors = _optimizer_recommendation_errors(report)

        self.assertIn("optimizer recommendation warning must state not LIVE_READY and live orders blocked", errors)

    def test_allow_paper_ranking_requires_paper_scope(self):
        report = load_json(FIXTURE_DIR / "optimizer_recommendation_scope_mismatch_fail.json")

        errors = _optimizer_recommendation_errors(report)

        self.assertIn("ALLOW_PAPER_RANKING requires PAPER_RANKING_RECOMMENDATION_ONLY scope", errors)

    def test_recommendation_cannot_write_live_ready_snapshot(self):
        report = load_json(FIXTURE_DIR / "optimizer_recommendation_live_writer_fail.json")

        errors = _optimizer_recommendation_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_non_ranking_recommendation_requires_blocker(self):
        report = load_json(FIXTURE_DIR / "optimizer_recommendation_pass.json")
        tampered = copy.deepcopy(report)
        tampered["recommendation_action"] = "BLOCK_RANKING"
        tampered["recommendation_scope"] = "RESEARCH_ONLY_BLOCKED"
        tampered["optimizer_output_type"] = "ANALYSIS_ONLY"

        errors = _optimizer_recommendation_errors(tampered)

        self.assertIn("non-ranking optimizer recommendation must carry explicit blocker evidence", errors)

    def test_paper_ranking_requires_mature_source_scorecard(self):
        report = load_json(FIXTURE_DIR / "optimizer_recommendation_scorecard_immature_fail.json")

        errors = _optimizer_recommendation_errors(report)

        self.assertIn("ALLOW_PAPER_RANKING requires source_scorecard_performance_ready=true", errors)
        self.assertIn("ALLOW_PAPER_RANKING requires source scorecard performance source binding PASS", errors)

    def test_current_validator_fixtures_pass(self):
        result = optimizer_recommendation_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
