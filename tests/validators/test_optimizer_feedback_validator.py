import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _optimizer_feedback_errors,
    execution_feedback_loop_validator,
    load_json,
    optimizer_feedback_hash,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class OptimizerFeedbackValidatorTest(unittest.TestCase):
    def test_pass_fixture_allows_paper_ranking_only_after_cost_feedback(self):
        report = load_json(FIXTURE_DIR / "optimizer_feedback_pass.json")

        errors = _optimizer_feedback_errors(report)

        self.assertEqual(errors, [])

    def test_slippage_divergence_blocks_ranking(self):
        report = load_json(FIXTURE_DIR / "optimizer_feedback_slippage_divergent_fail.json")

        errors = _optimizer_feedback_errors(report)

        self.assertTrue(
            any("slippage_deviation_bps above max_allowed_slippage_deviation_bps" in error for error in errors),
            errors,
        )

    def test_non_eligible_feedback_requires_explicit_blocker(self):
        report = load_json(FIXTURE_DIR / "optimizer_feedback_missing_blocker_fail.json")

        errors = _optimizer_feedback_errors(report)

        self.assertIn("non-eligible optimizer feedback must carry explicit blocker evidence", errors)

    def test_report_cannot_carry_live_permission(self):
        report = load_json(FIXTURE_DIR / "optimizer_feedback_live_flag_fail.json")

        errors = _optimizer_feedback_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_net_ev_deviation_must_match_expected_vs_realized_cost_gap(self):
        report = load_json(FIXTURE_DIR / "optimizer_feedback_pass.json")
        tampered = copy.deepcopy(report)
        tampered["net_ev_deviation_bps"] = 0.0

        errors = _optimizer_feedback_errors(tampered)

        self.assertIn("net_ev_deviation_bps must equal absolute expected-vs-realized net EV difference", errors)

    def test_feedback_eligible_requires_risk_review_pass(self):
        report = load_json(FIXTURE_DIR / "optimizer_feedback_missing_risk_review_fail.json")

        errors = _optimizer_feedback_errors(report)

        self.assertIn("feedback_eligible requires risk_review_status=PASS", errors)

    def test_feedback_hash_must_match_payload(self):
        report = load_json(FIXTURE_DIR / "optimizer_feedback_pass.json")
        self.assertEqual(report["feedback_hash"], optimizer_feedback_hash(report))
        tampered = copy.deepcopy(report)
        tampered["realized_slippage_bps"] = tampered["realized_slippage_bps"] + 1

        errors = _optimizer_feedback_errors(tampered)

        self.assertIn("optimizer feedback hash mismatch", errors)

    def test_current_validator_fixtures_pass(self):
        result = execution_feedback_loop_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
