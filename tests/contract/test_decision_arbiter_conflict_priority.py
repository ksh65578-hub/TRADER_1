import unittest

from trader1.core.decision.decision_arbiter import (
    choose_operational_paper_decision,
    order_blocker_codes,
    select_primary_blocker,
)


class DecisionArbiterConflictPriorityTest(unittest.TestCase):
    def test_kill_switch_alias_becomes_safe_mode_before_reconciliation_and_risk(self):
        blockers = [
            {"code": "RISK_VETO", "severity": "HIGH", "message": "risk veto"},
            {"code": "KILL_SWITCH", "severity": "CRITICAL", "message": "legacy kill switch alias"},
            {"code": "RECONCILIATION_REQUIRED", "severity": "HIGH", "message": "reconcile"},
        ]

        decision, primary = choose_operational_paper_decision(requested_entry=True, blockers=blockers)

        self.assertEqual(decision, "SAFE_MODE")
        self.assertEqual(primary, "KILL_SWITCH_ACTIVE")

    def test_reconciliation_family_beats_risk_and_min_edge(self):
        blockers = [
            {"code": "MIN_EDGE_FAIL", "severity": "LOW", "message": "weak edge"},
            {"code": "RISK_VETO", "severity": "HIGH", "message": "risk veto"},
            {"code": "LEDGER_INTEGRITY_FAIL", "severity": "CRITICAL", "message": "ledger hash mismatch"},
        ]

        decision, primary = choose_operational_paper_decision(requested_entry=True, blockers=blockers)

        self.assertEqual(decision, "RECONCILE_REQUIRED")
        self.assertEqual(primary, "LEDGER_INTEGRITY_FAIL")

    def test_live_final_guard_beats_risk_and_candidate_thresholds(self):
        blockers = [
            {"code": "MIN_EDGE_FAIL", "severity": "LOW", "message": "weak edge"},
            {"code": "RISK_VETO", "severity": "HIGH", "message": "risk veto"},
            {"code": "LIVE_FINAL_GUARD_FAILED", "severity": "CRITICAL", "message": "live guard"},
        ]

        decision, primary = choose_operational_paper_decision(requested_entry=True, blockers=blockers)

        self.assertEqual(decision, "NO_TRADE")
        self.assertEqual(primary, "LIVE_FINAL_GUARD_FAILED")

    def test_data_and_cost_blockers_are_ordered_before_min_edge(self):
        blockers = [
            {"code": "MIN_EDGE_FAIL", "severity": "LOW", "message": "weak edge"},
            {"code": "EXPECTED_SLIPPAGE_EXCEEDED", "severity": "MEDIUM", "message": "slippage"},
            {"code": "DATA_UNAVAILABLE", "severity": "HIGH", "message": "data missing"},
        ]

        self.assertEqual(
            order_blocker_codes(blockers),
            ["DATA_UNAVAILABLE", "EXPECTED_SLIPPAGE_EXCEEDED", "MIN_EDGE_FAIL"],
        )
        self.assertEqual(select_primary_blocker(blockers), "DATA_UNAVAILABLE")

    def test_unknown_blocker_fallback_preserves_input_order(self):
        blockers = [
            {"code": "FUTURE_BLOCKER_ALPHA", "severity": "HIGH", "message": "future"},
            {"code": "FUTURE_BLOCKER_BETA", "severity": "HIGH", "message": "future"},
        ]

        self.assertEqual(order_blocker_codes(blockers), ["FUTURE_BLOCKER_ALPHA", "FUTURE_BLOCKER_BETA"])
        self.assertEqual(select_primary_blocker(blockers), "FUTURE_BLOCKER_ALPHA")


if __name__ == "__main__":
    unittest.main()
