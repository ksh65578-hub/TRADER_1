import unittest

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
from trader1.core.sizing.position_sizing import sizing_decision_hash
from trader1.runtime.paper.upbit_paper_runtime import (
    build_upbit_paper_runtime_cycle_report,
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import build_upbit_public_market_data_collection_report
from trader1.validation.mvp0_validators import run_validators


class UpbitPaperRuntimeCycleTest(unittest.TestCase):
    def test_positive_net_ev_cycle_connects_fill_ledger_portfolio_and_summary_without_live_permission(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-positive")
        result = validate_upbit_paper_runtime_cycle_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "ENTER_LONG")
        self.assertEqual(report["paper_fill"]["order_lifecycle_state"], "FILLED")
        self.assertEqual(report["paper_ledger_events"][-1]["event_type"], "ORDER_FILLED")
        self.assertEqual(report["paper_ledger_head_hash"], report["paper_ledger_events"][-1]["event_hash"])
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 1)
        self.assertEqual(report["paper_portfolio_snapshot"]["positions"][0]["symbol"], "KRW-BTC")
        self.assertEqual(report["summary"]["portfolio"]["source"], "LEDGER")
        self.assertEqual(report["summary"]["portfolio"]["freshness_status"], "PASS")
        self.assertTrue(report["summary"]["entry_candidates"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["can_submit_order"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(report["order_adapter_called"])

    def test_cycle_can_bind_public_collection_hash_without_live_permission(self):
        collection = build_upbit_public_market_data_collection_report(
            collector_id="runtime-cycle-collection-source",
            session_id="mvp4_upbit_paper_runtime",
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-from-public-collection",
            source_collection_report=collection,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["runtime_input_role"], "PUBLIC_MARKET_DATA_COLLECTION")
        self.assertEqual(report["source_collection_report_hash"], collection["collection_hash"])
        self.assertEqual(report["source_public_market_data_hash"], collection["public_market_data_hash"])
        self.assertEqual(report["canonical_event_count"], collection["canonical_event_count"])
        self.assertFalse(report["live_order_allowed"])

    def test_cycle_blocks_collection_payload_mutation_after_source_hash_binding(self):
        collection = build_upbit_public_market_data_collection_report(
            collector_id="runtime-cycle-collection-payload-mismatch",
            session_id="mvp4_upbit_paper_runtime",
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-collection-payload-mismatch",
            source_collection_report=collection,
        )
        report["public_market_data"]["candles"][0]["close"] = "1234567"
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_negative_net_ev_cycle_is_no_trade_and_writes_no_fill_ledger(self):
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-negative",
            edge_profile="NEGATIVE",
        )
        result = validate_upbit_paper_runtime_cycle_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "NO_TRADE")
        self.assertIn("MIN_EDGE_FAIL", report["no_trade_reasons"])
        self.assertIsNone(report["paper_fill"])
        self.assertEqual(report["paper_ledger_events"], [])
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 0)

    def test_risk_off_regime_is_no_trade_and_writes_no_fill_ledger(self):
        data = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="DOWNTREND",
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-risk-off",
            market_data=data,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["regime"], "RISK_OFF")
        self.assertEqual(report["final_decision"], "NO_TRADE")
        self.assertIn("REGIME_MISMATCH", report["no_trade_reasons"])
        self.assertIsNone(report["paper_fill"])
        self.assertEqual(report["paper_ledger_events"], [])
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 0)

    def test_selected_candidate_must_be_highest_net_ev_candidate(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-wrong-selected")
        lower_ranked = report["strategy_candidates"][-1]
        report["selected_candidate"] = dict(lower_ranked)
        report["sizing_decision"]["strategy_unit_id"] = lower_ranked["candidate_id"]
        report["sizing_decision"]["sizing_decision_hash"] = sizing_decision_hash(report["sizing_decision"])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MIN_EDGE_FAIL")

    def test_sizing_strategy_unit_must_match_selected_candidate(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-sizing-mismatch")
        report["sizing_decision"]["strategy_unit_id"] = "KRW-BTC-unrelated-candidate"
        report["sizing_decision"]["sizing_decision_hash"] = sizing_decision_hash(report["sizing_decision"])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_candidate_cost_breakdown_is_required_for_net_ev(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-missing-cost-breakdown")
        del report["strategy_candidates"][0]["cost_breakdown_bps"]
        report["selected_candidate"] = dict(report["strategy_candidates"][0])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_candidate_expected_cost_must_equal_cost_components(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-cost-sum-mismatch")
        report["strategy_candidates"][0]["cost_breakdown_bps"]["slippage_bps"] = "99"
        report["selected_candidate"] = dict(report["strategy_candidates"][0])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_weak_signal_candidate_cannot_force_paper_entry_review(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-weak-signal-entry")
        report["strategy_candidates"][0]["signal_strength"] = "0.40"
        report["strategy_candidates"][0]["signal_grade"] = "C"
        report["strategy_candidates"][0]["decision"] = "PAPER_ENTRY_REVIEW"
        report["strategy_candidates"][0]["no_trade_reason"] = None
        report["selected_candidate"] = dict(report["strategy_candidates"][0])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MIN_EDGE_FAIL")

    def test_candidate_signal_grade_must_match_signal_strength(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-signal-grade-mismatch")
        report["strategy_candidates"][0]["signal_strength"] = "0.40"
        report["strategy_candidates"][0]["signal_grade"] = "A"
        report["selected_candidate"] = dict(report["strategy_candidates"][0])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_entry_review_candidate_cannot_carry_no_trade_reason(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-entry-with-no-trade-reason")
        report["strategy_candidates"][0]["no_trade_reason"] = "MIN_EDGE_FAIL"
        report["selected_candidate"] = dict(report["strategy_candidates"][0])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_threshold_passing_candidate_cannot_be_marked_no_trade(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-threshold-pass-suppressed")
        report["strategy_candidates"][0]["decision"] = "NO_TRADE"
        report["strategy_candidates"][0]["no_trade_reason"] = "MIN_EDGE_FAIL"
        report["selected_candidate"] = dict(report["strategy_candidates"][0])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MIN_EDGE_FAIL")

    def test_private_field_mixing_blocks_runtime_cycle(self):
        data = build_upbit_public_candle_fixture(symbol="KRW-BTC", session_id="mvp4_upbit_paper_runtime")
        data["private_account_fields_present"] = True
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-private-field",
            market_data=data,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_live_permission_mutation_is_blocked(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-live-mutation")
        report["live_order_allowed"] = True
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)
        result = validate_upbit_paper_runtime_cycle_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_upbit_paper_runtime_cycle_validator_passes_current_contract(self):
        results = run_validators(["upbit_paper_runtime_cycle_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
