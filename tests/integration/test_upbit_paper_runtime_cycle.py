import unittest

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
from trader1.core.sizing.position_sizing import sizing_decision_hash
from trader1.runtime.paper.upbit_paper_runtime import (
    build_upbit_paper_runtime_cycle_report,
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import build_upbit_public_market_data_collection_report
from trader1.runtime.portfolio.paper_portfolio import paper_portfolio_hash
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
        self.assertEqual(report["paper_portfolio_snapshot"]["source_runtime_cycle_id"], report["cycle_id"])
        self.assertEqual(report["paper_portfolio_snapshot"]["source_paper_ledger_head_hash"], report["paper_ledger_head_hash"])
        self.assertEqual(report["paper_portfolio_snapshot"]["positions"][0]["symbol"], "KRW-BTC")
        self.assertEqual(report["risk_state"]["risk_state"], "normal")
        self.assertTrue(report["risk_state"]["new_entry_allowed"])
        self.assertEqual(report["position_management_decision"]["decision"], "ENTER_LONG_WITH_ATTACHED_EXIT_PLAN")
        self.assertEqual(report["position_management_decision"]["exit_plan_status"], "ARMED_PAPER_ONLY_AFTER_FILL")
        self.assertLess(float(report["exit_plan"]["hard_stop"]), float(report["exit_plan"]["entry_price"]))
        self.assertGreater(float(report["exit_plan"]["tp1"]), float(report["exit_plan"]["entry_price"]))
        self.assertGreater(float(report["exit_plan"]["tp2"]), float(report["exit_plan"]["tp1"]))
        self.assertEqual(report["sizing_decision"]["inputs"]["sizing_formula"], "min(equity_cap,cash_cap,risk_cap,liquidity_cap,exposure_cap)*min(signal,strategy,regime)")
        self.assertEqual(report["summary"]["portfolio"]["source"], "LEDGER")
        self.assertEqual(report["summary"]["portfolio"]["freshness_status"], "PASS")
        self.assertTrue(report["summary"]["entry_candidates"])
        self.assertEqual(report["strategy_regime_cost_linkage"]["source_runtime_cycle_id"], report["cycle_id"])
        self.assertEqual(report["strategy_regime_cost_linkage"]["selected_candidate_id"], report["selected_candidate"]["candidate_id"])
        self.assertEqual(report["strategy_regime_cost_linkage"]["report_regime"], report["regime"])
        self.assertEqual(report["strategy_regime_cost_linkage"]["runtime_public_market_data_hash"], report["runtime_public_market_data_hash"])
        self.assertEqual(report["strategy_regime_cost_linkage"]["feature_snapshot_hash"], report["feature_snapshot_hash"])
        self.assertEqual(report["summary"]["quantitative_policy_summary"]["source"], "QUANTITATIVE_POLICY_REPORT")
        self.assertEqual(
            report["summary"]["quantitative_policy_summary"]["source_policy_report_id"],
            "runtime-cycle-positive_quantitative_policy",
        )
        self.assertEqual(report["summary"]["quantitative_policy_summary"]["dashboard_reason_code"], "LIVE_READY_MISSING")
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
        self.assertEqual(report["runtime_public_market_data_hash"], collection["public_market_data_hash"])
        self.assertEqual(report["canonical_event_count"], collection["canonical_event_count"])
        self.assertFalse(report["live_order_allowed"])

    def test_multi_symbol_universe_scores_and_selects_best_symbol_for_paper_entry(self):
        weak_btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="WEAK_RANGE",
        )
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)

        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-multi-symbol-selection",
            symbol="KRW-BTC",
            market_data_universe=[weak_btc, strong_eth],
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["runtime_input_role"], "MULTI_SYMBOL_MARKET_DATA_UNIVERSE")
        self.assertEqual(report["selected_symbol"], "KRW-ETH")
        self.assertEqual(report["symbol"], "KRW-ETH")
        self.assertEqual(report["paper_fill"]["symbol"], "KRW-ETH")
        self.assertEqual(report["paper_portfolio_snapshot"]["positions"][0]["symbol"], "KRW-ETH")
        self.assertEqual(report["exit_plan"]["source_symbol"], "KRW-ETH")
        self.assertEqual(report["position_management_decision"]["selected_symbol"], "KRW-ETH")
        self.assertIn("KRW-BTC", report["symbol_universe"])
        self.assertIn("KRW-ETH", report["symbol_universe"])
        self.assertGreater(
            float(report["selected_candidate"]["symbol_selection_score"]),
            float(next(item for item in report["symbol_selection_universe"] if item["symbol"] == "KRW-BTC")["symbol_selection_score"]),
        )
        self.assertEqual(
            float(report["selected_candidate"]["candidate_selection_score"]),
            max(float(candidate["candidate_selection_score"]) for candidate in report["strategy_candidates"]),
        )
        self.assertFalse(report["live_order_allowed"])

    def test_drawdown_risk_state_blocks_new_paper_entry_before_fill(self):
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-drawdown-risk-block",
            paper_cash_available="940000",
            paper_equity="940000",
            paper_position_market_value="0",
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["risk_state"]["risk_state"], "no_trade")
        self.assertFalse(report["risk_state"]["new_entry_allowed"])
        self.assertEqual(report["final_decision"], "BLOCKED")
        self.assertIn("DRAWDOWN_FREEZE_ACTIVE", report["no_trade_reasons"])
        self.assertIsNone(report["paper_fill"])
        self.assertEqual(report["position_management_decision"]["decision"], "ENTRY_BLOCKED_NO_POSITION")
        self.assertFalse(report["live_order_allowed"])

    def test_new_runtime_cycle_requires_quantitative_policy_binding(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-missing-quant-policy")
        del report["summary"]["quantitative_policy_summary"]
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_legacy_runtime_cycle_can_be_rechecked_without_quantitative_policy_binding(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-legacy-quant-policy")
        del report["summary"]["quantitative_policy_summary"]
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(
            report,
            require_quantitative_policy_summary=False,
        )

        self.assertEqual(result.status, "PASS")
        self.assertFalse(report["live_order_allowed"])

    def test_legacy_runtime_cycle_can_be_rechecked_without_current_sizing_exposure_cap(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-legacy-sizing-cap")
        del report["sizing_decision"]["caps"]["exposure_cap"]
        report["sizing_decision"]["sizing_decision_hash"] = sizing_decision_hash(report["sizing_decision"])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        strict_result = validate_upbit_paper_runtime_cycle_report(report)
        legacy_result = validate_upbit_paper_runtime_cycle_report(
            report,
            require_current_sizing_caps=False,
        )

        self.assertEqual(strict_result.status, "FAIL")
        self.assertEqual(strict_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")
        self.assertEqual(legacy_result.status, "PASS")
        self.assertFalse(report["live_order_allowed"])

    def test_runtime_blocks_tampered_position_detail_rollup(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-position-tamper")
        report["paper_portfolio_snapshot"]["positions"][0]["market_value"] = "9999"
        report["paper_portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(report["paper_portfolio_snapshot"])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

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
        self.assertEqual(report["paper_portfolio_snapshot"]["source_runtime_cycle_id"], report["cycle_id"])
        self.assertIsNone(report["paper_portfolio_snapshot"]["source_paper_ledger_head_hash"])
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 0)

    def test_ledger_backed_cash_guard_blocks_entry_before_fill(self):
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-cash-guard",
            paper_cash_available="100000",
            paper_equity="1000000",
            paper_position_market_value="340000",
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "BLOCKED")
        self.assertIn("RISK_VETO", report["no_trade_reasons"])
        self.assertIsNone(report["paper_fill"])
        self.assertEqual(report["paper_ledger_events"], [])
        self.assertEqual(report["sizing_decision"]["inputs"]["paper_cash_available"], "100000")
        self.assertEqual(report["sizing_decision"]["inputs"]["paper_position_market_value"], "340000")
        self.assertFalse(report["live_order_allowed"])

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

    def test_feature_snapshot_must_match_public_market_data_regime(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-feature-regime-mismatch")
        report["feature_snapshot"]["regime"] = "RISK_OFF"
        report["regime"] = "RISK_OFF"
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_candidate_regime_must_match_runtime_regime(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-candidate-regime-mismatch")
        report["strategy_candidates"][0]["regime"] = "RANGE"
        report["selected_candidate"] = dict(report["strategy_candidates"][0])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "REGIME_MISMATCH")

    def test_candidate_spread_cost_must_match_feature_spread(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-spread-cost-mismatch")
        candidate = report["strategy_candidates"][0]
        candidate["cost_breakdown_bps"]["spread_bps"] = "2"
        candidate["expected_cost_bps"] = "12"
        candidate["net_ev_after_cost_bps"] = "30"
        report["selected_candidate"] = dict(candidate)
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

    def test_runtime_blocks_portfolio_cycle_source_mismatch(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-portfolio-source-mismatch")
        report["paper_portfolio_snapshot"]["source_runtime_cycle_id"] = "different-cycle"
        report["paper_portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(report["paper_portfolio_snapshot"])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_runtime_blocks_portfolio_ledger_source_mismatch(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-portfolio-ledger-source-mismatch")
        report["paper_portfolio_snapshot"]["source_paper_ledger_head_hash"] = "B" * 64
        report["paper_portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(report["paper_portfolio_snapshot"])
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "LEDGER_INTEGRITY_FAIL")

    def test_upbit_paper_runtime_cycle_validator_passes_current_contract(self):
        results = run_validators(["upbit_paper_runtime_cycle_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
