import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    CONVERGENCE_FOUNDATION_VALIDATORS,
    run_fixture_file,
    run_validators,
)


ROOT = Path(__file__).resolve().parents[2]


class ConvergenceFoundationValidatorsTest(unittest.TestCase):
    def test_convergence_foundation_validators_pass_non_live_objective_guards(self):
        results = run_validators(CONVERGENCE_FOUNDATION_VALIDATORS)
        statuses = {result["validator_id"]: result["status"] for result in results}
        notes = {result["validator_id"]: result["notes"] for result in results}
        self.assertEqual(statuses["convergence_objective_profile_validator"], "PASS")
        self.assertEqual(statuses["optimizer_memory_state_validator"], "PASS")
        self.assertEqual(statuses["strategy_performance_memory_validator"], "PASS")
        self.assertIn("net EV after cost", notes["convergence_objective_profile_validator"])
        for result in results:
            self.assertFalse(result["blocking"])
            self.assertEqual(result["blockers"], [])

    def test_convergence_foundation_fixtures_have_pass_fail_blocked_outcomes(self):
        fixture_dir = ROOT / "tests" / "validators" / "fixtures"
        expected = {
            "convergence_foundation_pass.json": "PASS",
            "convergence_foundation_fail.json": "FAIL",
            "convergence_foundation_blocked.json": "BLOCKED",
        }
        for filename, expected_status in expected.items():
            with self.subTest(filename=filename):
                result = run_fixture_file(fixture_dir / filename)
                self.assertEqual(result["status"], expected_status)


if __name__ == "__main__":
    unittest.main()
