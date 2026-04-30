import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS,
    _profitability_evidence_audit_errors,
    _profitability_evidence_maturity_rollup_errors,
    load_json,
    profitability_evidence_maturity_rollup_validator,
    profitability_optimizer_evidence_gap_validator,
)


ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json"
ROLLUP_FIXTURE_PATH = ROOT / "tests" / "validators" / "fixtures" / "profitability_evidence_maturity_rollup_pass.json"


class ProfitabilityOptimizerEvidenceGapValidatorTest(unittest.TestCase):
    def test_current_audit_is_explicit_and_live_blocked(self):
        result = profitability_optimizer_evidence_gap_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])
        self.assertIn("MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json", result["input_artifact_paths"][0])

    def test_audit_helper_rejects_live_flag_drift(self):
        audit = load_json(AUDIT_PATH)
        tampered = copy.deepcopy(audit)
        tampered["live_order_allowed"] = True

        errors = _profitability_evidence_audit_errors(tampered)

        self.assertIn("audit has forbidden true field: live_order_allowed", errors)

    def test_audit_helper_rejects_missing_component_gap(self):
        audit = load_json(AUDIT_PATH)
        tampered = copy.deepcopy(audit)
        tampered["gaps"] = [
            gap for gap in tampered["gaps"] if gap["component"] != "optimizer_objective_net_ev_after_cost"
        ]

        errors = _profitability_evidence_audit_errors(tampered)

        self.assertTrue(
            any("optimizer_objective_net_ev_after_cost" in error for error in errors),
            errors,
        )

    def test_audit_helper_covers_required_components(self):
        audit = load_json(AUDIT_PATH)
        inspected = {
            item["component_id"] for item in audit["inspected_components"]
        }
        gap_components = {item["component"] for item in audit["gaps"]}

        self.assertEqual(inspected, PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS)
        self.assertEqual(gap_components, PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS)

    def test_maturity_rollup_validator_passes_current_rollup(self):
        result = profitability_evidence_maturity_rollup_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])
        self.assertIn("MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json", result["input_artifact_paths"][1])

    def test_maturity_rollup_helper_rejects_missing_component(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["components"] = [
            component for component in tampered["components"] if component["component_id"] != "overfit_oos_walk_forward"
        ]
        tampered["component_count"] = 9

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                "component_count" in error
                or "components" in error
                or "overfit_oos_walk_forward" in error
                for error in errors
            ),
            errors,
        )

    def test_maturity_rollup_helper_rejects_live_or_scale_drift(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["live_order_allowed"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("live_order_allowed" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_component_live_review_eligibility(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["components"][0]["live_review_eligible"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("live_review_eligible" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_hidden_long_run_claim(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        paper_shadow = tampered["components"][8]
        self.assertEqual(paper_shadow["component_id"], "paper_shadow_evidence_accumulation")
        paper_shadow["long_run_evidence_eligible"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("long-run" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
