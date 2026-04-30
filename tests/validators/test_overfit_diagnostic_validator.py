import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _overfit_diagnostic_errors,
    load_json,
    overfit_diagnostic_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class OverfitDiagnosticValidatorTest(unittest.TestCase):
    def test_pass_fixture_requires_oos_walk_forward_bootstrap_and_bias_checks(self):
        report = load_json(FIXTURE_DIR / "overfit_diagnostic_pass.json")

        errors = _overfit_diagnostic_errors(report)

        self.assertEqual(errors, [])

    def test_short_window_result_cannot_be_robustness_eligible(self):
        report = load_json(FIXTURE_DIR / "overfit_diagnostic_short_window_fail.json")

        errors = _overfit_diagnostic_errors(report)

        self.assertTrue(any("sample_count below min_required_sample_count" in error for error in errors), errors)

    def test_bootstrap_fail_blocks_robustness_eligibility(self):
        report = load_json(FIXTURE_DIR / "overfit_diagnostic_bootstrap_unstable_fail.json")

        errors = _overfit_diagnostic_errors(report)

        self.assertTrue(any("bootstrap_status must be PASS" in error for error in errors), errors)

    def test_report_cannot_carry_live_permission(self):
        report = load_json(FIXTURE_DIR / "overfit_diagnostic_live_flag_fail.json")

        errors = _overfit_diagnostic_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_non_eligible_diagnostic_must_explain_blocker(self):
        report = load_json(FIXTURE_DIR / "overfit_diagnostic_pass.json")
        tampered = copy.deepcopy(report)
        tampered["robustness_eligible"] = False
        tampered["diagnostic_status"] = "BLOCKED_FOR_ROBUSTNESS"

        errors = _overfit_diagnostic_errors(tampered)

        self.assertIn("non-eligible overfit diagnostic must carry explicit blocker evidence", errors)

    def test_current_validator_fixtures_pass(self):
        result = overfit_diagnostic_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
