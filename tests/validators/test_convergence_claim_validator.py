import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _convergence_claim_errors,
    convergence_claim_validator,
    load_json,
    run_validators,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class ConvergenceClaimValidatorTest(unittest.TestCase):
    def test_pass_fixture_is_analysis_only_and_not_live_ready(self):
        report = load_json(FIXTURE_DIR / "convergence_claim_pass.json")

        errors = _convergence_claim_errors(report)

        self.assertEqual(errors, [])

    def test_untested_dependency_blocks_improvement_claim(self):
        report = load_json(FIXTURE_DIR / "convergence_claim_dependency_fail.json")

        errors = _convergence_claim_errors(report)

        self.assertIn("convergence claim cannot remain improving while dependency is not PASS", errors)

    def test_stale_data_blocks_improvement_claim(self):
        report = load_json(FIXTURE_DIR / "convergence_claim_stale_data_fail.json")

        errors = _convergence_claim_errors(report)

        self.assertIn("convergence claim cannot remain improving with stale or missing data", errors)

    def test_model_drift_blocks_improvement_claim(self):
        report = load_json(FIXTURE_DIR / "convergence_claim_drift_fail.json")

        errors = _convergence_claim_errors(report)

        self.assertIn("convergence claim cannot remain improving while model_drift_status=DRIFT_DETECTED", errors)

    def test_profit_guarantee_wording_is_rejected(self):
        report = load_json(FIXTURE_DIR / "convergence_claim_forbidden_wording_fail.json")

        errors = _convergence_claim_errors(report)

        self.assertTrue(any("forbidden profitability wording" in error for error in errors), errors)

    def test_writer_input_eligibility_is_rejected(self):
        report = load_json(FIXTURE_DIR / "convergence_claim_writer_input_fail.json")

        errors = _convergence_claim_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_registered_validator_passes_current_fixtures(self):
        result = convergence_claim_validator().as_dict()

        self.assertEqual(result["status"], "PASS", result)
        self.assertFalse(result["blocking"], result)

    def test_run_validators_dispatch_includes_convergence_claim(self):
        result = run_validators(["convergence_claim_validator"])[0]

        self.assertEqual(result["status"], "PASS", result)
        self.assertFalse(result["blocking"], result)


if __name__ == "__main__":
    unittest.main()
