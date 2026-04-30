import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _strategy_condition_matrix_errors,
    load_json,
    strategy_condition_matrix_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class StrategyConditionMatrixValidatorTest(unittest.TestCase):
    def test_pass_fixture_covers_entry_exit_no_trade_and_regime(self):
        matrix = load_json(FIXTURE_DIR / "strategy_condition_matrix_pass.json")

        errors = _strategy_condition_matrix_errors(matrix)

        self.assertEqual(errors, [])

    def test_missing_risk_off_row_fails_closed(self):
        matrix = load_json(FIXTURE_DIR / "strategy_condition_matrix_missing_risk_off_fail.json")

        errors = _strategy_condition_matrix_errors(matrix)

        self.assertTrue(any("condition matrix missing regime families" in error for error in errors), errors)

    def test_matrix_cannot_carry_live_permission(self):
        matrix = load_json(FIXTURE_DIR / "strategy_condition_matrix_live_flag_fail.json")

        errors = _strategy_condition_matrix_errors(matrix)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_global_no_trade_reasons_must_cover_core_blockers(self):
        matrix = load_json(FIXTURE_DIR / "strategy_condition_matrix_missing_no_trade_fail.json")

        errors = _strategy_condition_matrix_errors(matrix)

        self.assertTrue(any("global_no_trade_reasons missing required blockers" in error for error in errors), errors)

    def test_entry_row_must_keep_downtrend_avoidance(self):
        matrix = load_json(FIXTURE_DIR / "strategy_condition_matrix_pass.json")
        tampered = copy.deepcopy(matrix)
        tampered["condition_rows"][0]["downtrend_avoidance_required"] = False

        errors = _strategy_condition_matrix_errors(tampered)

        self.assertTrue(any("downtrend avoidance" in error for error in errors), errors)

    def test_entry_row_must_have_edge_above_spread_and_slippage(self):
        matrix = load_json(FIXTURE_DIR / "strategy_condition_matrix_pass.json")
        tampered = copy.deepcopy(matrix)
        tampered["condition_rows"][0]["min_edge_bps"] = 9.0

        errors = _strategy_condition_matrix_errors(tampered)

        self.assertTrue(
            any("min_edge_bps must exceed max_expected_slippage_bps plus max_spread_bps" in error for error in errors),
            errors,
        )

    def test_current_validator_fixtures_pass(self):
        result = strategy_condition_matrix_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
