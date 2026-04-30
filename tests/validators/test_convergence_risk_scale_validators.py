import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    CONVERGENCE_RISK_SCALE_VALIDATORS,
    run_fixture_file,
    run_validators,
)


ROOT = Path(__file__).resolve().parents[2]


class ConvergenceRiskScaleValidatorsTest(unittest.TestCase):
    def test_convergence_risk_scale_validators_block_without_external_evidence(self):
        results = run_validators(CONVERGENCE_RISK_SCALE_VALIDATORS)
        statuses = {result["validator_id"]: result["status"] for result in results}
        blockers = {
            result["validator_id"]: [blocker["code"] for blocker in result["blockers"]]
            for result in results
        }

        self.assertEqual(statuses["risk_scaling_decision_validator"], "BLOCKED")
        self.assertEqual(statuses["live_burn_in_feedback_validator"], "BLOCKED")
        self.assertEqual(statuses["paper_live_parity_validator"], "BLOCKED")
        self.assertEqual(statuses["execution_quality_measurement_validator"], "BLOCKED")
        self.assertEqual(statuses["survival_layer_validator"], "BLOCKED")
        self.assertEqual(blockers["risk_scaling_decision_validator"], ["RISK_SCALING_UNTESTED"])
        self.assertEqual(blockers["live_burn_in_feedback_validator"], ["LIVE_BURN_IN_FEEDBACK_MISSING"])
        self.assertEqual(blockers["paper_live_parity_validator"], ["READ_ONLY_BURN_IN_MISSING"])
        self.assertEqual(blockers["execution_quality_measurement_validator"], ["EXECUTION_QUALITY_UNTESTED"])
        self.assertEqual(blockers["survival_layer_validator"], ["SURVIVAL_LAYER_BLOCKED"])

    def test_convergence_risk_scale_fixtures_have_pass_fail_blocked_outcomes(self):
        fixture_dir = ROOT / "tests" / "validators" / "fixtures"
        expected = {
            "convergence_risk_scale_pass.json": "PASS",
            "convergence_risk_scale_fail.json": "FAIL",
            "convergence_risk_scale_blocked.json": "BLOCKED",
            "convergence_scaleup_safety_pass.json": "PASS",
            "convergence_scaleup_safety_fail.json": "FAIL",
            "convergence_scaleup_safety_blocked.json": "BLOCKED",
        }
        for filename, expected_status in expected.items():
            with self.subTest(filename=filename):
                result = run_fixture_file(fixture_dir / filename)
                self.assertEqual(result["status"], expected_status)


if __name__ == "__main__":
    unittest.main()
