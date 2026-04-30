import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _strategy_performance_memory_errors,
    load_json,
    strategy_performance_memory_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class StrategyPerformanceMemoryValidatorTest(unittest.TestCase):
    def test_pass_fixture_requires_net_ev_regime_and_reason_visibility(self):
        report = load_json(FIXTURE_DIR / "strategy_performance_memory_pass.json")

        errors = _strategy_performance_memory_errors(report)

        self.assertEqual(errors, [])

    def test_strategy_performance_memory_cannot_carry_live_permission(self):
        report = load_json(FIXTURE_DIR / "strategy_performance_memory_live_flag_fail.json")

        errors = _strategy_performance_memory_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_raw_pnl_positive_net_negative_cannot_be_improving(self):
        report = load_json(FIXTURE_DIR / "strategy_performance_memory_raw_pnl_positive_net_negative_fail.json")

        errors = _strategy_performance_memory_errors(report)

        self.assertIn("IMPROVING_AFTER_COST requires positive net_ev_after_cost", errors)

    def test_improving_status_requires_enough_samples(self):
        report = load_json(FIXTURE_DIR / "strategy_performance_memory_insufficient_sample_fail.json")

        errors = _strategy_performance_memory_errors(report)

        self.assertIn("IMPROVING_AFTER_COST requires sample_count >= min_required_sample_count", errors)

    def test_reason_counts_are_required(self):
        report = load_json(FIXTURE_DIR / "strategy_performance_memory_missing_reason_fail.json")

        errors = _strategy_performance_memory_errors(report)

        self.assertTrue(any("minItems" in error for error in errors), errors)

    def test_downtrend_must_remain_no_trade(self):
        report = load_json(FIXTURE_DIR / "strategy_performance_memory_downtrend_trade_allowed_fail.json")

        errors = _strategy_performance_memory_errors(report)

        self.assertIn("DOWNTREND regime must not allow trading in MVP-4 strategy performance memory", errors)

    def test_live_source_mixing_is_rejected(self):
        report = load_json(FIXTURE_DIR / "strategy_performance_memory_live_source_mixing_fail.json")

        errors = _strategy_performance_memory_errors(report)

        self.assertTrue(any("LIVE" in error for error in errors), errors)

    def test_scope_separation_is_required(self):
        report = load_json(FIXTURE_DIR / "strategy_performance_memory_unscoped_fail.json")

        errors = _strategy_performance_memory_errors(report)

        self.assertTrue(any("expected const True" in error for error in errors), errors)

    def test_net_ev_cannot_exceed_gross_after_costs(self):
        report = load_json(FIXTURE_DIR / "strategy_performance_memory_pass.json")
        tampered = copy.deepcopy(report)
        tampered["net_ev_after_cost"] = 12.0

        errors = _strategy_performance_memory_errors(tampered)

        self.assertIn("net_ev_after_cost must not exceed gross_pnl minus fee, spread, slippage, and market impact costs", errors)

    def test_paper_shadow_scope_requires_both_sources(self):
        report = load_json(FIXTURE_DIR / "strategy_performance_memory_pass.json")
        tampered = copy.deepcopy(report)
        tampered["source_modes"] = ["PAPER"]

        errors = _strategy_performance_memory_errors(tampered)

        self.assertIn("PAPER_SHADOW_RESEARCH_ONLY requires PAPER and SHADOW source modes", errors)

    def test_current_validator_fixtures_pass(self):
        result = strategy_performance_memory_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
