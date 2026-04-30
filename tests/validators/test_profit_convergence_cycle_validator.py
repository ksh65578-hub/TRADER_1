import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _profit_convergence_cycle_errors,
    load_json,
    profit_convergence_cycle_validator,
    run_validators,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class ProfitConvergenceCycleValidatorTest(unittest.TestCase):
    def test_pass_fixture_is_paper_shadow_net_ev_cycle_only(self):
        report = load_json(FIXTURE_DIR / "profit_convergence_cycle_pass.json")

        errors = _profit_convergence_cycle_errors(report)

        self.assertEqual(errors, [])

    def test_untested_dependency_cannot_claim_improvement_or_rank(self):
        report = load_json(FIXTURE_DIR / "profit_convergence_cycle_dependency_untested_fail.json")

        errors = _profit_convergence_cycle_errors(report)

        self.assertIn("non-PASS dependency cannot allow LOCAL_IMPROVEMENT_REVIEW", errors)
        self.assertIn("non-PASS dependency cannot allow paper candidate ranking", errors)

    def test_raw_pnl_positive_but_net_ev_negative_blocks_cycle(self):
        report = load_json(FIXTURE_DIR / "profit_convergence_cycle_raw_pnl_net_negative_fail.json")

        errors = _profit_convergence_cycle_errors(report)

        self.assertIn("raw PnL improvement with negative net EV cannot allow LOCAL_IMPROVEMENT_REVIEW", errors)
        self.assertIn("raw PnL improvement with negative net EV cannot allow paper candidate ranking", errors)

    def test_model_drift_blocks_improvement_and_ranking(self):
        report = load_json(FIXTURE_DIR / "profit_convergence_cycle_drift_unblocked_fail.json")

        errors = _profit_convergence_cycle_errors(report)

        self.assertIn("DRIFT_DETECTED cannot allow profit convergence improvement review, claim, or ranking", errors)
        self.assertIn("DRIFT_DETECTED requires blocks_promotion=true", errors)

    def test_live_flag_is_schema_blocked(self):
        report = load_json(FIXTURE_DIR / "profit_convergence_cycle_live_flag_fail.json")

        errors = _profit_convergence_cycle_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_registered_validator_passes_current_fixtures(self):
        result = profit_convergence_cycle_validator().as_dict()

        self.assertEqual(result["status"], "PASS", result)
        self.assertFalse(result["blocking"], result)

    def test_run_validators_dispatch_includes_profit_cycle(self):
        result = run_validators(["profit_convergence_cycle_validator"])[0]

        self.assertEqual(result["status"], "PASS", result)
        self.assertFalse(result["blocking"], result)


if __name__ == "__main__":
    unittest.main()
