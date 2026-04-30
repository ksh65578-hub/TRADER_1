import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    OPTIMIZER_CONVERGENCE_GUARDRAIL_VALIDATORS,
    run_fixture_file,
    run_validators,
)


ROOT = Path(__file__).resolve().parents[2]


class OptimizerConvergenceGuardrailValidatorsTest(unittest.TestCase):
    def test_guardrail_validators_are_runnable_and_fail_closed(self):
        results = run_validators(OPTIMIZER_CONVERGENCE_GUARDRAIL_VALIDATORS)
        statuses = {result["validator_id"]: result["status"] for result in results}
        blockers = {
            result["validator_id"]: [blocker["code"] for blocker in result["blockers"]]
            for result in results
        }

        self.assertEqual(statuses["optimizer_no_live_mutation_validator"], "PASS")
        self.assertEqual(statuses["exploration_exploitation_policy_validator"], "PASS")
        self.assertEqual(statuses["exploration_to_exploitation_validator"], "PASS")
        self.assertEqual(statuses["candidate_cooldown_validator"], "PASS")
        self.assertEqual(statuses["rolling_window_default_validator"], "PASS")
        self.assertEqual(statuses["optimizer_guardrail_validator"], "PASS")
        self.assertEqual(statuses["convergence_assessment_validator"], "PASS")
        self.assertEqual(statuses["scale_up_eligibility_validator"], "BLOCKED")
        self.assertEqual(blockers["exploration_exploitation_policy_validator"], [])
        self.assertEqual(blockers["exploration_to_exploitation_validator"], [])
        self.assertEqual(blockers["candidate_cooldown_validator"], [])
        self.assertEqual(blockers["rolling_window_default_validator"], [])
        self.assertEqual(blockers["optimizer_guardrail_validator"], [])
        self.assertEqual(blockers["convergence_assessment_validator"], [])
        self.assertEqual(blockers["scale_up_eligibility_validator"], ["SCALE_UP_NOT_ELIGIBLE"])

    def test_guardrail_fixtures_have_pass_fail_blocked_outcomes(self):
        fixture_dir = ROOT / "tests" / "validators" / "fixtures"
        expected = {
            "optimizer_convergence_guardrail_pass.json": "PASS",
            "optimizer_convergence_guardrail_fail.json": "FAIL",
            "optimizer_convergence_guardrail_blocked.json": "BLOCKED",
        }
        for filename, expected_status in expected.items():
            with self.subTest(filename=filename):
                result = run_fixture_file(fixture_dir / filename)
                self.assertEqual(result["status"], expected_status)


if __name__ == "__main__":
    unittest.main()
