import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import run_fixture_file, run_validators


ROOT = Path(__file__).resolve().parents[2]


class LiveFinalGuardValidatorTest(unittest.TestCase):
    def test_live_final_guard_validator_passes_current_fail_closed_state(self):
        results = run_validators(["live_final_guard_validator"])
        self.assertEqual(results[0]["status"], "PASS")
        self.assertFalse(results[0]["blocking"])
        self.assertEqual(results[0]["blockers"], [])

    def test_live_final_guard_fixtures_have_pass_fail_blocked_outcomes(self):
        fixture_dir = ROOT / "tests" / "validators" / "fixtures"
        expected = {
            "live_final_guard_pass.json": "PASS",
            "live_final_guard_fail.json": "FAIL",
            "live_final_guard_blocked.json": "BLOCKED",
        }
        for filename, expected_status in expected.items():
            with self.subTest(filename=filename):
                result = run_fixture_file(fixture_dir / filename)
                self.assertEqual(result["status"], expected_status)


if __name__ == "__main__":
    unittest.main()
