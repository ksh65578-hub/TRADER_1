import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _model_drift_errors,
    load_json,
    model_drift_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class ModelDriftValidatorTest(unittest.TestCase):
    def test_pass_fixture_allows_only_local_analysis_claim(self):
        report = load_json(FIXTURE_DIR / "model_drift_pass.json")

        errors = _model_drift_errors(report)

        self.assertEqual(errors, [])

    def test_live_permission_is_rejected(self):
        report = load_json(FIXTURE_DIR / "model_drift_live_flag_fail.json")

        errors = _model_drift_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_detected_drift_cannot_keep_robust_claim(self):
        report = load_json(FIXTURE_DIR / "model_drift_detected_claim_fail.json")

        errors = _model_drift_errors(report)

        self.assertIn("DRIFT_DETECTED cannot keep convergence_claim_after=ROBUSTLY_IMPROVING", errors)

    def test_suspected_drift_requires_promotion_block(self):
        report = load_json(FIXTURE_DIR / "model_drift_suspected_unblocked_fail.json")

        errors = _model_drift_errors(report)

        self.assertIn("DRIFT_SUSPECTED requires blocks_promotion=true", errors)

    def test_no_drift_requires_baseline_sample_floor(self):
        report = load_json(FIXTURE_DIR / "model_drift_missing_baseline_fail.json")

        errors = _model_drift_errors(report)

        self.assertIn("NO_DRIFT requires baseline_sample_count >= min_required_sample_count", errors)

    def test_stale_input_requires_blockers(self):
        report = load_json(FIXTURE_DIR / "model_drift_stale_input_fail.json")

        errors = _model_drift_errors(report)

        self.assertIn("stale or missing model drift input requires blockers", errors)

    def test_scale_up_recommendation_is_rejected(self):
        report = load_json(FIXTURE_DIR / "model_drift_scale_up_fail.json")

        errors = _model_drift_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_current_validator_fixtures_pass(self):
        result = model_drift_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
