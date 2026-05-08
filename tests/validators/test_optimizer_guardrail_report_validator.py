import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _optimizer_guardrail_report_errors,
    load_json,
    optimizer_guardrail_report_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class OptimizerGuardrailReportValidatorTest(unittest.TestCase):
    def test_pass_fixture_is_non_live_guardrail_only(self):
        report = load_json(FIXTURE_DIR / "optimizer_guardrail_report_pass.json")

        errors = _optimizer_guardrail_report_errors(report)

        self.assertEqual(errors, [])

    def test_guardrail_report_cannot_carry_live_permission(self):
        report = load_json(FIXTURE_DIR / "optimizer_guardrail_report_live_flag_fail.json")

        errors = _optimizer_guardrail_report_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_guardrail_pass_cannot_override_untested_dependency(self):
        report = load_json(FIXTURE_DIR / "optimizer_guardrail_report_dependency_override_fail.json")

        errors = _optimizer_guardrail_report_errors(report)

        self.assertIn("guardrail PASS cannot override dependency FAIL/BLOCKED/UNTESTED/STALE/TIMEOUT", errors)

    def test_guardrail_warning_must_prevent_live_ready_confusion(self):
        report = load_json(FIXTURE_DIR / "optimizer_guardrail_report_live_ready_wording_fail.json")

        errors = _optimizer_guardrail_report_errors(report)

        self.assertIn("optimizer guardrail report warning must state not LIVE_READY and live orders blocked", errors)

    def test_blocked_guardrail_requires_blocker_evidence(self):
        report = load_json(FIXTURE_DIR / "optimizer_guardrail_report_missing_blocker_fail.json")

        errors = _optimizer_guardrail_report_errors(report)

        self.assertIn("non-PASS optimizer guardrail report must carry explicit blocker evidence", errors)

    def test_guardrail_report_cannot_write_live_ready_snapshot(self):
        report = load_json(FIXTURE_DIR / "optimizer_guardrail_report_live_writer_fail.json")

        errors = _optimizer_guardrail_report_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_guardrail_report_cannot_recommend_scale_up(self):
        report = load_json(FIXTURE_DIR / "optimizer_guardrail_report_scale_up_fail.json")

        errors = _optimizer_guardrail_report_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_paper_ranking_scope_must_match_guardrail_scope(self):
        report = load_json(FIXTURE_DIR / "optimizer_guardrail_report_pass.json")
        tampered = copy.deepcopy(report)
        tampered["guardrail_scope"] = "OPTIMIZER_ANALYSIS_ONLY"

        errors = _optimizer_guardrail_report_errors(tampered)

        self.assertIn("PAPER_RANKING_ONLY output requires OPTIMIZER_PAPER_RANKING_ONLY scope", errors)

    def test_paper_ranking_guardrail_requires_checked_performance_sources(self):
        report = load_json(FIXTURE_DIR / "optimizer_guardrail_report_pass.json")
        tampered = copy.deepcopy(report)
        tampered["checked_artifact_ids"] = [
            artifact_id
            for artifact_id in tampered["checked_artifact_ids"]
            if not artifact_id.startswith("performance_summary:")
        ]

        errors = _optimizer_guardrail_report_errors(tampered)

        self.assertIn(
            "PAPER_RANKING_ONLY guardrail requires checked candidate-scoped closed trade, execution quality, and performance summary source ids",
            errors,
        )

    def test_current_validator_fixtures_pass(self):
        result = optimizer_guardrail_report_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
