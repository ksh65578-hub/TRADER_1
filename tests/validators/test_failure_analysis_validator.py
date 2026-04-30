import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _failure_analysis_errors,
    failure_analysis_validator,
    load_json,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class FailureAnalysisValidatorTest(unittest.TestCase):
    def test_pass_fixture_records_known_failure_as_append_only_memory(self):
        report = load_json(FIXTURE_DIR / "failure_analysis_pass.json")

        errors = _failure_analysis_errors(report)

        self.assertEqual(errors, [])

    def test_unknown_live_affecting_root_cause_blocks_live_order(self):
        report = load_json(FIXTURE_DIR / "failure_analysis_unknown_root_live_affecting_fail.json")

        errors = _failure_analysis_errors(report)

        self.assertIn("UNKNOWN_ROOT_CAUSE in live-affecting failure must block live order", errors)

    def test_repeated_same_root_cause_cannot_keep_ranking_allowed(self):
        report = load_json(FIXTURE_DIR / "failure_analysis_repeated_unblocked_fail.json")

        errors = _failure_analysis_errors(report)

        self.assertIn("repeated same-root-cause failure must block ranking", errors)

    def test_report_cannot_carry_live_permission(self):
        report = load_json(FIXTURE_DIR / "failure_analysis_live_flag_fail.json")

        errors = _failure_analysis_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_memory_write_required_must_be_append_recorded(self):
        report = load_json(FIXTURE_DIR / "failure_analysis_pass.json")
        tampered = copy.deepcopy(report)
        tampered["memory_write_status"] = "REQUIRED_NOT_RECORDED"

        errors = _failure_analysis_errors(tampered)

        self.assertIn("memory_write_required requires memory_write_status=APPEND_ONLY_RECORDED", errors)

    def test_current_validator_fixtures_pass(self):
        result = failure_analysis_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
