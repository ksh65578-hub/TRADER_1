import unittest

from trader1.core.decision.decision_arbiter import choose_operational_paper_decision
from trader1.core.strategy.strategy_unit import build_basic_strategy_unit, strategy_unit_hash, validate_strategy_unit
from trader1.validation.mvp0_validators import run_validators


class StrategyUnitScopeTest(unittest.TestCase):
    def test_strategy_unit_is_upbit_paper_scoped(self):
        unit = build_basic_strategy_unit(strategy_unit_id="strategy-scope")
        result = validate_strategy_unit(unit)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(unit["exchange"], "UPBIT")
        self.assertEqual(unit["market_type"], "KRW_SPOT")
        self.assertEqual(unit["mode"], "PAPER")
        self.assertFalse(unit["strategy_order_adapter_called"])
        self.assertFalse(unit["live_order_allowed"])

    def test_strategy_unit_wrong_scope_blocks(self):
        unit = build_basic_strategy_unit(strategy_unit_id="strategy-bad-scope", exchange="BINANCE", market_type="SPOT")
        result = validate_strategy_unit(unit)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_strategy_direct_adapter_call_blocks(self):
        unit = build_basic_strategy_unit(strategy_unit_id="strategy-adapter")
        unit["strategy_order_adapter_called"] = True
        unit["strategy_unit_hash"] = strategy_unit_hash(unit)
        result = validate_strategy_unit(unit)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_strategy_live_permission_mutation_blocks(self):
        unit = build_basic_strategy_unit(strategy_unit_id="strategy-live")
        unit["live_order_allowed"] = True
        unit["can_live_trade"] = True
        unit["strategy_unit_hash"] = strategy_unit_hash(unit)
        result = validate_strategy_unit(unit)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_decision_arbiter_prioritizes_reconciliation(self):
        blockers = [
            {"code": "RISK_VETO", "severity": "HIGH", "message": "risk"},
            {"code": "RECONCILIATION_REQUIRED", "severity": "HIGH", "message": "reconcile"},
        ]
        decision, primary = choose_operational_paper_decision(requested_entry=True, blockers=blockers)
        self.assertEqual(decision, "RECONCILE_REQUIRED")
        self.assertEqual(primary, "RECONCILIATION_REQUIRED")

    def test_operational_paper_validator_passes_current_contract(self):
        results = run_validators(["upbit_operational_paper_gate_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
