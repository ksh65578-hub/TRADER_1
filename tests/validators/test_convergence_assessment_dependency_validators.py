import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    CONVERGENCE_ASSESSMENT_DEPENDENCY_VALIDATORS,
    run_fixture_file,
    run_validators,
)


ROOT = Path(__file__).resolve().parents[2]


class ConvergenceAssessmentDependencyValidatorsTest(unittest.TestCase):
    def test_convergence_assessment_dependencies_pass_schema_only_scaffolds(self):
        results = run_validators(CONVERGENCE_ASSESSMENT_DEPENDENCY_VALIDATORS)
        statuses = {result["validator_id"]: result["status"] for result in results}
        self.assertEqual(statuses["overfit_diagnostic_validator"], "PASS")
        self.assertEqual(statuses["execution_feedback_loop_validator"], "PASS")
        self.assertEqual(statuses["model_drift_validator"], "PASS")
        for result in results:
            self.assertFalse(result["blocking"])
            self.assertEqual(result["blockers"], [])

    def test_convergence_assessment_dependency_fixtures_have_pass_fail_blocked_outcomes(self):
        fixture_dir = ROOT / "tests" / "validators" / "fixtures"
        expected = {
            "convergence_assessment_dependencies_pass.json": "PASS",
            "convergence_assessment_dependencies_fail.json": "FAIL",
            "convergence_assessment_dependencies_blocked.json": "BLOCKED",
        }
        for filename, expected_status in expected.items():
            with self.subTest(filename=filename):
                result = run_fixture_file(fixture_dir / filename)
                self.assertEqual(result["status"], expected_status)


if __name__ == "__main__":
    unittest.main()
