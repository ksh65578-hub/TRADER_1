import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _paper_exposure_quality_errors,
    load_json,
    paper_exposure_quality_report_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class PaperExposureQualityReportValidatorTest(unittest.TestCase):
    def test_current_fixture_set_passes_validator(self):
        result = paper_exposure_quality_report_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])

    def test_helper_rejects_live_or_scale_flag_drift(self):
        report = load_json(FIXTURE_DIR / "paper_exposure_quality_pass.json")
        tampered = copy.deepcopy(report)
        tampered["scale_up_allowed"] = True

        errors = _paper_exposure_quality_errors(tampered)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_helper_rejects_missing_source_evidence(self):
        report = load_json(FIXTURE_DIR / "paper_exposure_quality_pass.json")
        tampered = copy.deepcopy(report)
        tampered["source_evidence_ids"] = []

        errors = _paper_exposure_quality_errors(tampered)

        self.assertIn("source_evidence_ids missing for paper exposure quality report", errors)

    def test_helper_rejects_passing_report_with_exposure_breach(self):
        report = load_json(FIXTURE_DIR / "paper_exposure_quality_pass.json")
        tampered = copy.deepcopy(report)
        tampered["gross_exposure_pct"] = 0.9
        tampered["exposure_breach_count"] = 1

        errors = _paper_exposure_quality_errors(tampered)

        self.assertIn("gross_exposure_pct exceeds max_allowed_gross_exposure_pct", errors)
        self.assertIn("PASS_PAPER_ONLY cannot have exposure_breach_count > 0", errors)

    def test_helper_rejects_live_mode(self):
        report = load_json(FIXTURE_DIR / "paper_exposure_quality_pass.json")
        tampered = copy.deepcopy(report)
        tampered["mode"] = "LIVE"

        errors = _paper_exposure_quality_errors(tampered)

        self.assertIn(
            "paper exposure report mode must be PAPER and never LIVE before independent live-enabling evidence",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
