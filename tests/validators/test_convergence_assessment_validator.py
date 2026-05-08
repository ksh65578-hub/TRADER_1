import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _convergence_assessment_errors,
    convergence_assessment_validator,
    load_json,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class ConvergenceAssessmentValidatorTest(unittest.TestCase):
    def test_pass_fixture_keeps_assessment_analysis_only(self):
        report = load_json(FIXTURE_DIR / "convergence_assessment_pass.json")

        errors = _convergence_assessment_errors(report)

        self.assertEqual(errors, [])

    def test_live_permission_is_rejected(self):
        report = load_json(FIXTURE_DIR / "convergence_assessment_live_flag_fail.json")

        errors = _convergence_assessment_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_missing_dependency_blocks_improvement_claim(self):
        report = load_json(FIXTURE_DIR / "convergence_assessment_missing_dependency_fail.json")

        errors = _convergence_assessment_errors(report)

        self.assertIn("convergence assessment cannot claim improvement while dependency is not PASS", errors)

    def test_untested_dependency_blocks_claim(self):
        report = load_json(FIXTURE_DIR / "convergence_assessment_untested_dependency_fail.json")

        errors = _convergence_assessment_errors(report)

        self.assertIn("convergence assessment cannot keep improvement claim while dependency is not PASS", errors)

    def test_model_drift_requires_promotion_blocker(self):
        report = load_json(FIXTURE_DIR / "convergence_assessment_drift_unblocked_fail.json")

        errors = _convergence_assessment_errors(report)

        self.assertIn("DRIFT_DETECTED requires blocks_promotion=true", errors)

    def test_improving_assessment_requires_candidate_scoped_performance_sources(self):
        report = load_json(FIXTURE_DIR / "convergence_assessment_pass.json")
        tampered = copy.deepcopy(report)
        tampered["source_evidence_ids"] = [
            source_id
            for source_id in tampered["source_evidence_ids"]
            if not source_id.startswith("performance_summary:")
        ]

        errors = _convergence_assessment_errors(tampered)

        self.assertIn(
            "improving convergence assessment requires candidate-scoped closed trade, execution quality, and performance summary source ids",
            errors,
        )

    def test_writer_input_eligibility_is_rejected(self):
        report = load_json(FIXTURE_DIR / "convergence_assessment_writer_input_fail.json")

        errors = _convergence_assessment_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_scale_up_recommendation_is_rejected(self):
        report = load_json(FIXTURE_DIR / "convergence_assessment_scale_up_fail.json")

        errors = _convergence_assessment_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_current_validator_fixtures_pass(self):
        result = convergence_assessment_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
