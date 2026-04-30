import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _profit_optimizer_config_errors,
    candidate_ranking_validator,
    load_json,
    objective_function_validator,
    profit_optimizer_config_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class ProfitOptimizerConfigValidatorTest(unittest.TestCase):
    def test_pass_fixture_is_non_live_net_ev_after_cost_config(self):
        config = load_json(FIXTURE_DIR / "profit_optimizer_config_pass.json")

        errors = _profit_optimizer_config_errors(config)

        self.assertEqual(errors, [])

    def test_config_cannot_carry_live_permission(self):
        config = load_json(FIXTURE_DIR / "profit_optimizer_config_live_flag_fail.json")

        errors = _profit_optimizer_config_errors(config)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_config_cannot_use_raw_pnl_objective(self):
        config = load_json(FIXTURE_DIR / "profit_optimizer_config_raw_pnl_fail.json")

        errors = _profit_optimizer_config_errors(config)

        self.assertTrue(any("RAW_PNL" in error or "NET_EV_AFTER_COST" in error for error in errors), errors)

    def test_config_cannot_use_live_source(self):
        config = load_json(FIXTURE_DIR / "profit_optimizer_config_live_source_fail.json")

        errors = _profit_optimizer_config_errors(config)

        self.assertTrue(any("LIVE" in error for error in errors), errors)

    def test_config_requires_full_cost_stack(self):
        config = load_json(FIXTURE_DIR / "profit_optimizer_config_missing_cost_fail.json")

        errors = _profit_optimizer_config_errors(config)

        self.assertTrue(any("cost components" in error or "minItems 5" in error for error in errors), errors)

    def test_config_cannot_write_live_ready_snapshot(self):
        config = load_json(FIXTURE_DIR / "profit_optimizer_config_live_writer_fail.json")

        errors = _profit_optimizer_config_errors(config)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_registered_validators_pass_current_fixtures(self):
        for validator in (
            profit_optimizer_config_validator,
            objective_function_validator,
            candidate_ranking_validator,
        ):
            result = validator().as_dict()
            self.assertEqual(result["status"], "PASS", result)
            self.assertFalse(result["blocking"], result)


if __name__ == "__main__":
    unittest.main()
