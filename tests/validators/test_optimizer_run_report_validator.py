import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _optimizer_run_errors,
    load_json,
    optimizer_run_report_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class OptimizerRunReportValidatorTest(unittest.TestCase):
    def test_pass_fixture_is_analysis_only_and_net_ev_scoped(self):
        report = load_json(FIXTURE_DIR / "optimizer_run_pass.json")

        errors = _optimizer_run_errors(report)

        self.assertEqual(errors, [])
        self.assertEqual(report["candidate_scorecard_validator_status"], "PASS")
        self.assertEqual(report["ranking_input_maturity_status"], "PASS")
        self.assertGreaterEqual(
            report["ranking_input_mature_scorecard_count"],
            report["ranking_input_min_mature_scorecard_count"],
        )

    def test_optimizer_run_cannot_carry_live_permission(self):
        report = load_json(FIXTURE_DIR / "optimizer_run_live_flag_fail.json")

        errors = _optimizer_run_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_optimizer_run_cannot_use_live_mode(self):
        report = load_json(FIXTURE_DIR / "optimizer_run_live_mode_fail.json")

        errors = _optimizer_run_errors(report)

        self.assertIn("optimizer run mode LIVE is forbidden before independent live-enabling evidence", errors)

    def test_optimizer_run_warning_must_prevent_live_ready_confusion(self):
        report = load_json(FIXTURE_DIR / "optimizer_run_live_ready_wording_fail.json")

        errors = _optimizer_run_errors(report)

        self.assertIn("optimizer run warning must state not LIVE_READY and live orders blocked", errors)

    def test_blocked_optimizer_run_requires_blocker_evidence(self):
        report = load_json(FIXTURE_DIR / "optimizer_run_missing_blocker_fail.json")

        errors = _optimizer_run_errors(report)

        self.assertIn("non-completed optimizer run must carry explicit blocker evidence", errors)

    def test_optimizer_run_cannot_write_live_ready_snapshot(self):
        report = load_json(FIXTURE_DIR / "optimizer_run_live_writer_fail.json")

        errors = _optimizer_run_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_optimizer_run_rejects_raw_pnl_objective(self):
        report = load_json(FIXTURE_DIR / "optimizer_run_raw_pnl_objective_fail.json")

        errors = _optimizer_run_errors(report)

        self.assertTrue(any("RAW_PNL" in error for error in errors), errors)

    def test_candidate_ranking_requires_output_artifact(self):
        report = load_json(FIXTURE_DIR / "optimizer_run_pass.json")
        tampered = copy.deepcopy(report)
        tampered["output_artifact_ids"] = []

        errors = _optimizer_run_errors(tampered)

        self.assertIn("CANDIDATE_RANKING_INPUT requires output_artifact_ids", errors)

    def test_candidate_ranking_requires_mature_scorecard_input(self):
        report = load_json(FIXTURE_DIR / "optimizer_run_scorecard_immature_fail.json")

        errors = _optimizer_run_errors(report)

        self.assertIn("CANDIDATE_RANKING_INPUT requires mature ranking scorecards above minimum", errors)
        self.assertIn("CANDIDATE_RANKING_INPUT requires ranking_input_maturity_status=PASS", errors)

    def test_current_validator_fixtures_pass(self):
        result = optimizer_run_report_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
