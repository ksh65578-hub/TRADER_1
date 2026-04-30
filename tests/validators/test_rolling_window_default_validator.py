import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _rolling_window_default_errors,
    load_json,
    rolling_window_default_validator,
    run_validators,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class RollingWindowDefaultValidatorTest(unittest.TestCase):
    def test_pass_fixture_requires_default_rolling_window_depth(self):
        report = load_json(FIXTURE_DIR / "rolling_window_default_pass.json")

        self.assertEqual([], _rolling_window_default_errors(report))

    def test_short_sample_fixture_is_rejected(self):
        report = load_json(FIXTURE_DIR / "overfit_diagnostic_short_window_fail.json")
        errors = _rolling_window_default_errors(report)

        self.assertTrue(any("sample_count below rolling default minimum" in error for error in errors), errors)

    def test_train_window_minimum_is_rejected(self):
        report = load_json(FIXTURE_DIR / "rolling_window_default_train_window_fail.json")
        errors = _rolling_window_default_errors(report)

        self.assertIn("train_window_count below rolling default minimum 6", errors)

    def test_oos_window_minimum_is_rejected(self):
        report = load_json(FIXTURE_DIR / "rolling_window_default_oos_window_fail.json")
        errors = _rolling_window_default_errors(report)

        self.assertIn("oos_window_count below rolling default minimum 3", errors)

    def test_walk_forward_window_minimum_is_rejected(self):
        report = load_json(FIXTURE_DIR / "rolling_window_default_walk_forward_fail.json")
        errors = _rolling_window_default_errors(report)

        self.assertIn("walk_forward_window_count below rolling default minimum 4", errors)

    def test_source_evidence_minimum_is_rejected(self):
        report = load_json(FIXTURE_DIR / "rolling_window_default_source_evidence_fail.json")
        errors = _rolling_window_default_errors(report)

        self.assertIn("rolling window default requires at least 3 source_evidence_ids", errors)

    def test_stale_status_is_rejected(self):
        report = load_json(FIXTURE_DIR / "rolling_window_default_stale_status_fail.json")
        errors = _rolling_window_default_errors(report)

        self.assertIn("oos_status cannot be STALE for rolling window default", errors)

    def test_registered_validator_passes_current_fixtures(self):
        result = rolling_window_default_validator().as_dict()

        self.assertEqual("PASS", result["status"], result)
        self.assertFalse(result["blocking"], result)

    def test_run_validators_dispatch_includes_rolling_window_default(self):
        result = run_validators(["rolling_window_default_validator"])[0]

        self.assertEqual("PASS", result["status"], result)


if __name__ == "__main__":
    unittest.main()
