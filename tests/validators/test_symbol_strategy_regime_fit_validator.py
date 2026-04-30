import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _symbol_strategy_regime_fit_errors,
    load_json,
    symbol_strategy_regime_fit_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class SymbolStrategyRegimeFitValidatorTest(unittest.TestCase):
    def test_pass_fixture_links_symbol_to_liquidity_depth_spread_and_regime(self):
        report = load_json(FIXTURE_DIR / "symbol_strategy_regime_fit_pass.json")

        errors = _symbol_strategy_regime_fit_errors(report)

        self.assertEqual(errors, [])

    def test_low_liquidity_fails_when_marked_paper_review_eligible(self):
        report = load_json(FIXTURE_DIR / "symbol_strategy_regime_fit_low_liquidity_fail.json")

        errors = _symbol_strategy_regime_fit_errors(report)

        self.assertTrue(any("liquidity_score below min_required_liquidity_score" in error for error in errors), errors)

    def test_high_spread_fails_when_marked_paper_review_eligible(self):
        report = load_json(FIXTURE_DIR / "symbol_strategy_regime_fit_high_spread_fail.json")

        errors = _symbol_strategy_regime_fit_errors(report)

        self.assertTrue(any("spread_bps above max_allowed_spread_bps" in error for error in errors), errors)

    def test_low_depth_fails_when_marked_paper_review_eligible(self):
        report = load_json(FIXTURE_DIR / "symbol_strategy_regime_fit_low_depth_fail.json")

        errors = _symbol_strategy_regime_fit_errors(report)

        self.assertTrue(any("depth_score below min_required_depth_score" in error for error in errors), errors)

    def test_report_cannot_carry_live_permission(self):
        report = load_json(FIXTURE_DIR / "symbol_strategy_regime_fit_live_flag_fail.json")

        errors = _symbol_strategy_regime_fit_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_strategy_family_coverage_is_required(self):
        report = load_json(FIXTURE_DIR / "symbol_strategy_regime_fit_missing_family_fail.json")

        errors = _symbol_strategy_regime_fit_errors(report)

        self.assertTrue(any("strategy family coverage missing" in error for error in errors), errors)

    def test_risk_off_cannot_be_paper_review_eligible(self):
        report = load_json(FIXTURE_DIR / "symbol_strategy_regime_fit_pass.json")
        tampered = copy.deepcopy(report)
        tampered["regime_family"] = "RISK_OFF"
        tampered["paper_review_eligible"] = True

        errors = _symbol_strategy_regime_fit_errors(tampered)

        self.assertTrue(any("RISK_OFF" in error for error in errors), errors)

    def test_current_validator_fixtures_pass(self):
        result = symbol_strategy_regime_fit_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
