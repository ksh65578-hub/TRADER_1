import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _optimization_state_errors,
    load_json,
    optimization_state_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class OptimizationStateValidatorTest(unittest.TestCase):
    def test_pass_fixture_is_append_audit_non_live_state(self):
        report = load_json(FIXTURE_DIR / "optimization_state_pass.json")

        errors = _optimization_state_errors(report)

        self.assertEqual(errors, [])

    def test_optimization_state_cannot_carry_live_permission(self):
        report = load_json(FIXTURE_DIR / "optimization_state_live_flag_fail.json")

        errors = _optimization_state_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_active_state_cannot_override_untested_dependency(self):
        report = load_json(FIXTURE_DIR / "optimization_state_dependency_override_fail.json")

        errors = _optimization_state_errors(report)

        self.assertIn("ACTIVE_ANALYSIS_ONLY cannot override dependency FAIL/BLOCKED/UNTESTED/STALE/TIMEOUT", errors)

    def test_optimization_state_warning_must_prevent_live_ready_confusion(self):
        report = load_json(FIXTURE_DIR / "optimization_state_live_ready_wording_fail.json")

        errors = _optimization_state_errors(report)

        self.assertIn("optimization state warning must state not LIVE_READY and live orders blocked", errors)

    def test_blocked_optimization_state_requires_blocker_evidence(self):
        report = load_json(FIXTURE_DIR / "optimization_state_missing_blocker_fail.json")

        errors = _optimization_state_errors(report)

        self.assertIn("non-active optimization state must carry explicit blocker evidence", errors)

    def test_optimization_state_cannot_mutate_active_snapshot(self):
        report = load_json(FIXTURE_DIR / "optimization_state_active_snapshot_mutation_fail.json")

        errors = _optimization_state_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_optimization_state_rejects_raw_pnl_objective(self):
        report = load_json(FIXTURE_DIR / "optimization_state_raw_pnl_objective_fail.json")

        errors = _optimization_state_errors(report)

        self.assertTrue(any("RAW_PNL" in error for error in errors), errors)

    def test_paper_ranking_state_requires_latest_recommendation(self):
        report = load_json(FIXTURE_DIR / "optimization_state_pass.json")
        tampered = copy.deepcopy(report)
        tampered["latest_recommendation_id"] = None

        errors = _optimization_state_errors(tampered)

        self.assertIn("PAPER_RANKING_STATE_ONLY requires latest_recommendation_id", errors)

    def test_current_validator_fixtures_pass(self):
        result = optimization_state_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
