from decimal import Decimal
import unittest

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
from trader1.core.sizing.position_sizing import sizing_decision_hash
from trader1.runtime.paper.upbit_paper_runtime import (
    _build_runtime_exit_plan,
    _evaluate_existing_position_exit,
    build_upbit_paper_runtime_cycle_report,
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import build_upbit_public_market_data_collection_report
from trader1.runtime.portfolio.paper_portfolio import build_paper_portfolio_snapshot_from_fill, paper_portfolio_hash
from trader1.validation.mvp0_validators import run_validators


class UpbitPaperRuntimeCycleTest(unittest.TestCase):
    def test_pullback_strategy_exit_uses_trailing_router(self):
        candidate = {
            "candidate_id": "KRW-BTC-pullback-trend-long",
            "symbol": "KRW-BTC",
            "strategy_family": "PULLBACK_TREND_LONG",
        }
        features = {
            "last_price": "101",
            "previous_high": "106",
            "vwap": "100.5",
            "volatility_pct": "1.0",
            "range_breakout_pct": "0.1",
            "regime": "UPTREND",
            "trend_exhaustion_status": "PASS",
            "trend_exhaustion_score": "0",
        }
        exit_plan = _build_runtime_exit_plan(
            selected_candidate=candidate,
            features=features,
            entry_price_override="100",
        )
        evaluation = _evaluate_existing_position_exit(
            position={"symbol": "KRW-BTC", "quantity": "1", "average_entry_price": "100"},
            features=features,
            exit_plan=exit_plan,
            managed_candidate=candidate,
        )

        self.assertEqual(exit_plan["strategy_exit_policy_id"], "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1")
        self.assertEqual(exit_plan["exit_variation"], "trailing_tp")
        self.assertEqual(evaluation["final_decision"], "EXIT_POSITION")
        self.assertEqual(evaluation["reason_code"], "TRAILING_STOP")
        self.assertFalse(evaluation["strategy_exit_condition_passed"])

    def test_vwap_reversion_strategy_exit_closes_on_vwap_target(self):
        candidate = {
            "candidate_id": "KRW-BTC-vwap-mean-reversion",
            "symbol": "KRW-BTC",
            "strategy_family": "VWAP_MEAN_REVERSION",
        }
        features = {
            "last_price": "102",
            "previous_high": "103",
            "vwap": "102",
            "volatility_pct": "1.0",
            "range_breakout_pct": "-0.1",
            "regime": "RANGE",
            "trend_exhaustion_status": "PASS",
            "trend_exhaustion_score": "0",
        }
        exit_plan = _build_runtime_exit_plan(
            selected_candidate=candidate,
            features=features,
            entry_price_override="100",
        )
        evaluation = _evaluate_existing_position_exit(
            position={"symbol": "KRW-BTC", "quantity": "1", "average_entry_price": "100"},
            features=features,
            exit_plan=exit_plan,
            managed_candidate=candidate,
        )

        self.assertEqual(exit_plan["exit_variation"], "fixed_tp")
        self.assertEqual(exit_plan["vwap_reversion_target"], "102")
        self.assertEqual(evaluation["final_decision"], "EXIT_POSITION")
        self.assertEqual(evaluation["reason_code"], "VWAP_REVERSION_COMPLETE")
        self.assertTrue(evaluation["strategy_exit_condition_passed"])
        self.assertEqual(evaluation["strategy_exit_action"], "FULL_EXIT")

    def test_breakout_strategy_exit_closes_when_breakout_level_is_lost(self):
        candidate = {
            "candidate_id": "KRW-BTC-breakout-retest-long",
            "symbol": "KRW-BTC",
            "strategy_family": "BREAKOUT_RETEST_LONG",
        }
        features = {
            "last_price": "99.7",
            "previous_high": "100.5",
            "vwap": "99",
            "volatility_pct": "1.0",
            "range_breakout_pct": "-0.8",
            "regime": "UPTREND",
            "trend_exhaustion_status": "PASS",
            "trend_exhaustion_score": "0",
        }
        exit_plan = _build_runtime_exit_plan(
            selected_candidate=candidate,
            features=features,
            entry_price_override="100",
        )
        evaluation = _evaluate_existing_position_exit(
            position={"symbol": "KRW-BTC", "quantity": "1", "average_entry_price": "100"},
            features=features,
            exit_plan=exit_plan,
            managed_candidate=candidate,
        )

        self.assertEqual(exit_plan["exit_variation"], "invalidation_exit")
        self.assertEqual(exit_plan["breakout_invalidation_level"], "99.8")
        self.assertEqual(evaluation["final_decision"], "EXIT_POSITION")
        self.assertEqual(evaluation["reason_code"], "BREAKOUT_LEVEL_LOST")
        self.assertTrue(evaluation["strategy_exit_condition_passed"])

    def test_existing_position_uses_entry_strategy_context_for_exit_router(self):
        market_data = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        mark_price = market_data["candles"][-1]["close"]
        average_entry = Decimal("990000")
        quantity = Decimal("7000") / average_entry
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity=str(quantity),
            fill_price=str(average_entry),
            mark_price=mark_price,
            fee_amount="3.5",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle-vwap-entry",
            source_paper_ledger_head_hash="C" * 64,
            entry_strategy_context={
                "entry_strategy_context_status": "BOUND_TO_ENTRY_CANDIDATE",
                "entry_strategy_context_source": "PAPER_RUNTIME_ENTRY_FILL",
                "entry_candidate_id": "KRW-BTC-vwap-mean-reversion",
                "entry_strategy_family": "VWAP_MEAN_REVERSION",
                "entry_strategy_exit_policy_id": "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1",
                "entry_strategy_exit_variation": "fixed_tp",
                "entry_strategy_source_runtime_cycle_id": "previous-paper-cycle-vwap-entry",
                "entry_strategy_source_candidate_hash": "C" * 64,
                "entry_strategy_source_exit_plan_hash": "D" * 64,
                "entry_strategy_context_formula": "bind exit policy to entry strategy at fill time",
            },
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-vwap-context-exit",
            symbol="KRW-BTC",
            market_data=market_data,
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["final_decision"], "EXIT_POSITION")
        lifecycle = report["position_management_decision"]
        self.assertEqual(lifecycle["entry_strategy_context_status"], "BOUND_TO_POSITION_ENTRY")
        self.assertEqual(lifecycle["entry_candidate_id"], "KRW-BTC-vwap-mean-reversion")
        self.assertEqual(lifecycle["entry_strategy_family"], "VWAP_MEAN_REVERSION")
        self.assertEqual(lifecycle["entry_strategy_exit_variation"], "fixed_tp")
        self.assertFalse(lifecycle["entry_strategy_fallback_used"])
        self.assertNotEqual(lifecycle["selected_candidate_id"], lifecycle["entry_candidate_id"])
        self.assertEqual(report["exit_plan"]["source_candidate_id"], "KRW-BTC-vwap-mean-reversion")
        self.assertEqual(report["exit_plan"]["strategy_family"], "VWAP_MEAN_REVERSION")
        evaluation = lifecycle["position_exit_evaluation"]
        self.assertEqual(evaluation["strategy_family"], "VWAP_MEAN_REVERSION")
        self.assertEqual(evaluation["exit_variation"], "fixed_tp")
        self.assertEqual(evaluation["strategy_exit_reason_code"], "VWAP_REVERSION_COMPLETE")
        self.assertEqual(evaluation["reason_code"], "VWAP_REVERSION_COMPLETE")
        self.assertTrue(evaluation["strategy_exit_condition_passed"])
        self.assertEqual(report["paper_fill"]["side"], "SELL")
        self.assertFalse(report["paper_fill"]["order_adapter_called"])
        self.assertFalse(report["paper_fill"]["private_endpoint_called"])
        self.assertFalse(report["live_order_allowed"])

    def test_positive_net_ev_cycle_connects_fill_ledger_portfolio_and_summary_without_live_permission(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-positive")
        result = validate_upbit_paper_runtime_cycle_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "ENTER_LONG")
        self.assertEqual(report["paper_fill"]["order_lifecycle_state"], "FILLED")
        self.assertEqual(report["selected_candidate"]["cost_model_source"], "PAPER_RUNTIME_ADAPTIVE_PUBLIC_L2_PROXY_COST_MODEL")
        self.assertEqual(report["paper_fill"]["fill_source"], "PAPER_BROKER_SIMULATION_ADAPTIVE_PUBLIC_L2_PROXY")
        self.assertEqual(report["paper_fill"]["broker_model_id"], "UPBIT_KRW_SPOT_ADAPTIVE_PUBLIC_L2_PROXY_V1")
        self.assertEqual(report["paper_fill"]["maker_taker"], "TAKER")
        self.assertEqual(report["paper_fill"]["order_type"], "MARKETABLE_LIMIT_PAPER")
        self.assertEqual(report["paper_fill"]["time_in_force"], "IOC_PAPER")
        self.assertEqual(report["paper_fill"]["orderbook_proxy"]["source"], "PUBLIC_CANDLE_DERIVED_L2_PROXY")
        self.assertGreater(float(report["paper_fill"]["slippage_bps"]), float(report["paper_fill"]["spread_bps"]))
        self.assertGreater(float(report["paper_fill"]["market_impact_bps"]), 0)
        self.assertGreater(float(report["paper_fill"]["latency_penalty_bps"]), 0)
        self.assertTrue(report["paper_fill"]["reservation_released"])
        self.assertFalse(report["paper_fill"]["order_adapter_called"])
        self.assertFalse(report["paper_fill"]["private_endpoint_called"])
        self.assertFalse(report["paper_fill"]["credential_load_attempted"])
        self.assertEqual(report["paper_ledger_events"][-1]["event_type"], "ORDER_FILLED")
        self.assertEqual(report["paper_ledger_head_hash"], report["paper_ledger_events"][-1]["event_hash"])
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 1)
        self.assertEqual(report["paper_portfolio_snapshot"]["source_runtime_cycle_id"], report["cycle_id"])
        self.assertEqual(report["paper_portfolio_snapshot"]["source_paper_ledger_head_hash"], report["paper_ledger_head_hash"])
        self.assertEqual(report["paper_portfolio_snapshot"]["positions"][0]["symbol"], "KRW-BTC")
        self.assertEqual(report["paper_portfolio_snapshot"]["positions"][0]["entry_candidate_id"], report["selected_candidate"]["candidate_id"])
        self.assertEqual(
            report["paper_portfolio_snapshot"]["positions"][0]["entry_strategy_exit_policy_id"],
            "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1",
        )
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

    def test_recent_negative_exit_feedback_cooldown_blocks_same_symbol_reentry(self):
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-recent-negative-exit-cooldown",
            recent_failure_feedback=[
                {
                    "source": "PAPER_RUNTIME_RECENT_NEGATIVE_EXIT_FEEDBACK",
                    "symbol": "KRW-BTC",
                    "candidate_id": "KRW-BTC-pullback-trend-long",
                    "strategy_family": "PULLBACK_TREND_LONG",
                    "exit_reason_code": "REGIME_REVERSAL",
                    "realized_pnl_delta": "-1250.50",
                    "source_runtime_cycle_id": "previous-negative-regime-reversal-exit",
                    "source_runtime_cycle_hash": "B" * 64,
                    "cycles_since_failure": 1,
                    "cooldown_cycles_remaining": 2,
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }
            ],
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["final_decision"], "NO_TRADE")
        self.assertIn("COOLDOWN", report["no_trade_reasons"])
        self.assertEqual(report["selected_candidate"]["recent_failure_cooldown_status"], "ACTIVE")
        self.assertEqual(report["selected_candidate"]["recent_failure_cooldown_cycles_remaining"], 2)
        self.assertEqual(report["selected_candidate"]["recent_failure_reason_code"], "REGIME_REVERSAL")
        self.assertEqual(report["selected_candidate"]["no_trade_reason"], "COOLDOWN")
        self.assertGreater(float(report["selected_candidate"]["recent_failure_penalty_bps"]), 0)
        self.assertIsNone(report["paper_fill"])
        self.assertEqual(report["paper_ledger_events"], [])
        self.assertEqual(report["selected_symbol_evidence_scorecard"]["best_recent_failure_cooldown_status"], "ACTIVE")
        self.assertFalse(report["live_order_allowed"])

    def test_adaptive_paper_broker_can_record_partial_fill_without_live_permission(self):
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-adaptive-partial-fill",
            starting_cash="50000000",
            paper_cash_available="50000000",
            paper_equity="50000000",
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "ENTER_LONG")
        self.assertEqual(report["paper_fill"]["order_lifecycle_state"], "PARTIALLY_FILLED")
        self.assertTrue(report["paper_fill"]["partial_fill"])
        self.assertLess(float(report["paper_fill"]["filled_notional"]), float(report["paper_fill"]["requested_notional"]))
        self.assertGreaterEqual(float(report["paper_fill"]["filled_notional"]), 5000)
        self.assertGreater(float(report["paper_fill"]["reservation_release_amount"]), 0)
        self.assertEqual(report["paper_ledger_events"][-1]["quantity"], report["paper_fill"]["filled_quantity"])
        self.assertEqual(report["paper_portfolio_snapshot"]["positions"][0]["quantity"], report["paper_fill"]["filled_quantity"])
        self.assertFalse(report["paper_fill"]["live_order_allowed"])
        self.assertFalse(report["live_order_allowed"])

    def test_adaptive_paper_broker_allows_risk_reducing_partial_exit_without_live_permission(self):
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
        mark_price = weak_btc["candles"][-1]["close"]
        portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.3",
            fill_price=mark_price,
            mark_price=mark_price,
            fee_amount="150",
            source_runtime_cycle_id="prior-paper-entry",
            source_paper_ledger_head_hash="B" * 64,
        )

        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-risk-reducing-partial-exit",
            market_data_universe=[weak_btc, strong_eth],
            current_paper_portfolio_snapshot=portfolio,
            paper_cash_available=portfolio["cash_available"],
            paper_equity=portfolio["equity"],
            paper_position_market_value=portfolio["position_market_value"],
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["selected_symbol"], "KRW-BTC")
        self.assertEqual(report["final_decision"], "REDUCE_POSITION")
        self.assertEqual(report["position_management_decision"]["requested_position_decision"], "EXIT_POSITION")
        self.assertEqual(report["position_management_decision"]["execution_adjusted_position_decision_reason"], "PARTIAL_EXIT_FILL")
        self.assertEqual(report["paper_fill"]["side"], "SELL")
        self.assertEqual(report["paper_fill"]["order_lifecycle_state"], "PARTIALLY_FILLED")
        self.assertLess(float(report["paper_fill"]["fill_ratio"]), 0.35)
        self.assertGreaterEqual(float(report["paper_fill"]["filled_notional"]), 5000)
        self.assertEqual(report["paper_fill"]["reject_reason"], None)
        self.assertEqual(report["paper_fill"]["order_adapter_called"], False)
        self.assertEqual(report["paper_fill"]["private_endpoint_called"], False)
        self.assertEqual(report["paper_fill"]["credential_load_attempted"], False)
        self.assertLess(
            Decimal(report["paper_portfolio_snapshot"]["positions"][0]["quantity"]),
            Decimal(portfolio["positions"][0]["quantity"]),
        )
        self.assertFalse(report["paper_fill"]["live_order_allowed"])
        self.assertFalse(report["live_order_allowed"])

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
        self.assertEqual(report["symbol_selection_policy"]["symbol_scope"], "KRW_UNIVERSE")
        self.assertEqual(report["symbol_selection_policy"]["live_order_allowed"], False)
        scorecards_by_symbol = {item["symbol"]: item for item in report["symbol_evidence_scorecards"]}
        self.assertEqual(report["symbol_evidence_scorecard_count"], 2)
        self.assertEqual(set(scorecards_by_symbol), {"KRW-BTC", "KRW-ETH"})
        self.assertEqual(report["selected_symbol_evidence_scorecard"], scorecards_by_symbol["KRW-ETH"])
        self.assertEqual(scorecards_by_symbol["KRW-ETH"]["best_candidate_id"], report["selected_candidate"]["candidate_id"])
        self.assertGreater(float(scorecards_by_symbol["KRW-ETH"]["best_net_ev_after_cost_bps"]), 0)
        self.assertGreaterEqual(scorecards_by_symbol["KRW-BTC"]["candidate_count"], 3)
        self.assertEqual(scorecards_by_symbol["KRW-BTC"]["live_order_allowed"], False)
        self.assertGreater(
            float(report["selected_candidate"]["symbol_selection_score"]),
            float(next(item for item in report["symbol_selection_universe"] if item["symbol"] == "KRW-BTC")["symbol_selection_score"]),
        )
        self.assertEqual(
            float(report["selected_candidate"]["candidate_selection_score"]),
            max(float(candidate["candidate_selection_score"]) for candidate in report["strategy_candidates"]),
        )
        self.assertFalse(report["live_order_allowed"])

    def test_symbol_selection_filters_correlated_duplicate_cluster_without_live_permission(self):
        btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(eth["candles"], start=1):
            candle["volume"] = str(15 + index * 5)

        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-correlated-cluster-filter",
            symbol="KRW-BTC",
            market_data_universe=[btc, eth],
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        universe_by_symbol = {item["symbol"]: item for item in report["symbol_selection_universe"]}
        self.assertEqual(report["selected_symbol"], "KRW-ETH")
        self.assertEqual(report["symbol_selection_policy"]["adaptive_top_n"], 2)
        self.assertEqual(report["symbol_selection_policy"]["correlation_cluster_threshold"], "0.92")
        self.assertEqual(universe_by_symbol["KRW-ETH"]["correlation_cluster_status"], "LEADER")
        self.assertEqual(universe_by_symbol["KRW-BTC"]["correlation_cluster_status"], "DIVERSIFICATION_FILTERED")
        self.assertEqual(universe_by_symbol["KRW-BTC"]["correlation_cluster_leader_symbol"], "KRW-ETH")
        self.assertEqual(universe_by_symbol["KRW-BTC"]["correlation_penalty"], "0.18")
        self.assertFalse(universe_by_symbol["KRW-BTC"]["eligible_after_correlation"])
        self.assertFalse(universe_by_symbol["KRW-BTC"]["eligible_for_entry_candidate"])
        btc_candidates = [candidate for candidate in report["strategy_candidates"] if candidate["symbol"] == "KRW-BTC"]
        self.assertTrue(btc_candidates)
        self.assertTrue(all(candidate["decision"] == "NO_TRADE" for candidate in btc_candidates))
        self.assertTrue(all(candidate["no_trade_reason"] == "CLUSTER_RISK" for candidate in btc_candidates))
        scorecards_by_symbol = {item["symbol"]: item for item in report["symbol_evidence_scorecards"]}
        self.assertIn("CLUSTER_RISK", scorecards_by_symbol["KRW-BTC"]["no_trade_reasons"])
        self.assertEqual(scorecards_by_symbol["KRW-BTC"]["correlation_cluster_status"], "DIVERSIFICATION_FILTERED")
        self.assertFalse(report["live_order_allowed"])

    def test_paper_scope_focus_can_select_valid_active_candidate_without_live_permission(self):
        base = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-paper-scope-focus-base")
        focus_candidate = base["selected_candidate"]

        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-paper-scope-focus",
            paper_scope_focus={
                "source": "TEST_ACTIVE_CANDIDATE_SCOPE",
                "candidate_id": focus_candidate["candidate_id"],
                "symbol": focus_candidate["symbol"],
                "strategy_id": "trend_pullback",
                "parameter_hash": "A" * 64,
                "sample_count": 1,
                "sample_deficit": 29,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["selected_candidate"]["candidate_id"], focus_candidate["candidate_id"])
        continuity = report["paper_scope_continuity_decision"]
        self.assertTrue(continuity["requested"])
        self.assertTrue(continuity["selected"])
        self.assertEqual(continuity["selection_status"], "SELECTED")
        self.assertEqual(continuity["requested_candidate_id"], focus_candidate["candidate_id"])
        self.assertFalse(continuity["live_order_allowed"])
        self.assertFalse(report["live_order_allowed"])

    def test_paper_scope_focus_live_flag_is_ignored_and_stays_fail_closed(self):
        base = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-paper-scope-focus-live-flag-base")
        focus_candidate = base["selected_candidate"]

        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-paper-scope-focus-live-flag",
            paper_scope_focus={
                "candidate_id": focus_candidate["candidate_id"],
                "symbol": focus_candidate["symbol"],
                "strategy_id": "trend_pullback",
                "parameter_hash": "A" * 64,
                "sample_deficit": 29,
                "live_order_allowed": True,
            },
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertFalse(report["paper_scope_continuity_decision"]["requested"])
        self.assertEqual(report["paper_scope_continuity_decision"]["selection_status"], "NOT_REQUESTED")
        self.assertFalse(report["paper_scope_continuity_decision"]["live_order_allowed"])
        self.assertFalse(report["live_order_allowed"])

    def test_preliminary_robustness_feedback_rotates_away_from_unfavorable_candidate(self):
        repeated_wlfi = build_upbit_public_candle_fixture(
            symbol="KRW-WLFI",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(repeated_wlfi["candles"], start=1):
            candle["volume"] = str(10 + index * 3)
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)

        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-preliminary-robustness-feedback-rotation",
            symbol="KRW-WLFI",
            market_data_universe=[repeated_wlfi, strong_eth],
            recent_failure_feedback=[
                {
                    "source": "PAPER_RUNTIME_PRELIMINARY_ROBUSTNESS_FEEDBACK",
                    "feedback_kind": "PRELIMINARY_ROBUSTNESS_FAIL",
                    "symbol": "KRW-WLFI",
                    "candidate_id": "KRW-WLFI-pullback-trend-long",
                    "strategy_family": "PULLBACK_TREND_LONG",
                    "failure_reason_code": "PRELIMINARY_OOS_BELOW_THRESHOLD",
                    "exit_reason_code": "PRELIMINARY_OOS_BELOW_THRESHOLD",
                    "realized_pnl_delta": "0",
                    "cooldown_cycles_remaining": 5,
                }
            ],
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["selected_symbol"], "KRW-ETH")
        wlfi_pullback = next(
            candidate
            for candidate in report["strategy_candidates"]
            if candidate["candidate_id"] == "KRW-WLFI-pullback-trend-long"
        )
        self.assertEqual(wlfi_pullback["decision"], "NO_TRADE")
        self.assertEqual(wlfi_pullback["no_trade_reason"], "COOLDOWN")
        self.assertEqual(wlfi_pullback["recent_failure_feedback_kind"], "PRELIMINARY_ROBUSTNESS_FAIL")
        self.assertEqual(wlfi_pullback["recent_failure_reason_code"], "PRELIMINARY_OOS_BELOW_THRESHOLD")
        self.assertGreater(float(wlfi_pullback["recent_failure_penalty_bps"]), 50)
        scorecards_by_symbol = {item["symbol"]: item for item in report["symbol_evidence_scorecards"]}
        self.assertEqual(scorecards_by_symbol["KRW-WLFI"]["best_recent_failure_feedback_kind"], "PRELIMINARY_ROBUSTNESS_FAIL")
        self.assertEqual(report["selected_candidate"]["recent_failure_feedback_kind"], "NONE")
        self.assertFalse(report["live_order_allowed"])

    def test_open_position_exits_on_preliminary_robustness_feedback_cooldown(self):
        wlfi = build_upbit_public_candle_fixture(
            symbol="KRW-WLFI",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(wlfi["candles"], start=1):
            candle["volume"] = str(20 + index * 4)
        mark_price = wlfi["candles"][-1]["close"]
        quantity = Decimal("6000") / Decimal(str(mark_price))
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-WLFI",
            side="BUY",
            quantity=str(quantity),
            fill_price=mark_price,
            mark_price=mark_price,
            fee_amount="3",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle-quality-feedback",
            source_paper_ledger_head_hash="Q" * 64,
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-quality-feedback-exit",
            symbol="KRW-WLFI",
            market_data_universe=[wlfi],
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
            recent_failure_feedback=[
                {
                    "source": "PAPER_RUNTIME_PRELIMINARY_ROBUSTNESS_FEEDBACK",
                    "feedback_kind": "PRELIMINARY_ROBUSTNESS_FAIL",
                    "symbol": "KRW-WLFI",
                    "candidate_id": "KRW-WLFI-pullback-trend-long",
                    "strategy_family": "PULLBACK_TREND_LONG",
                    "failure_reason_code": "PRELIMINARY_OOS_BELOW_THRESHOLD",
                    "exit_reason_code": "PRELIMINARY_OOS_BELOW_THRESHOLD",
                    "realized_pnl_delta": "0",
                    "cooldown_cycles_remaining": 5,
                }
            ],
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["final_decision"], "EXIT_POSITION")
        self.assertIn("COOLDOWN", report["no_trade_reasons"])
        self.assertEqual(report["position_management_decision"]["requested_position_decision"], "EXIT_POSITION")
        self.assertEqual(report["position_management_decision"]["position_exit_reason_code"], "COOLDOWN")
        evaluation = report["position_management_decision"]["position_exit_evaluation"]
        self.assertEqual(evaluation["quality_feedback_exit_status"], "ACTIVE")
        self.assertTrue(evaluation["quality_feedback_exit_condition_passed"])
        self.assertEqual(evaluation["quality_feedback_exit_action"], "FULL_EXIT")
        self.assertEqual(evaluation["quality_feedback_exit_feedback_kind"], "PRELIMINARY_ROBUSTNESS_FAIL")
        self.assertEqual(evaluation["quality_feedback_exit_reason_code"], "PRELIMINARY_OOS_BELOW_THRESHOLD")
        self.assertEqual(report["paper_fill"]["side"], "SELL")
        self.assertEqual(report["paper_fill"]["order_lifecycle_state"], "FILLED")
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 0)
        self.assertFalse(report["paper_fill"]["order_adapter_called"])
        self.assertFalse(report["paper_fill"]["private_endpoint_called"])
        self.assertFalse(report["paper_fill"]["credential_load_attempted"])
        self.assertFalse(report["live_order_allowed"])

        evaluation["quality_feedback_exit_condition_passed"] = False
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)
        tampered_result = validate_upbit_paper_runtime_cycle_report(report)
        self.assertEqual(tampered_result.status, "FAIL")
        self.assertEqual(tampered_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_symbol_evidence_scorecard_tamper_is_rejected(self):
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
            cycle_id="runtime-cycle-symbol-scorecard-tamper",
            symbol="KRW-BTC",
            market_data_universe=[weak_btc, strong_eth],
        )
        report["symbol_evidence_scorecards"] = [
            item for item in report["symbol_evidence_scorecards"] if item["symbol"] != report["selected_symbol"]
        ]
        report["symbol_evidence_scorecard_count"] = len(report["symbol_evidence_scorecards"])
        report["selected_symbol_evidence_scorecard"] = {}
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

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

    def test_weak_confirmation_uptrend_is_no_trade_before_paper_fill(self):
        market_data = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        closes = ["1000000", "1001500", "1004000", "1009000", "1007000", "1008000"]
        for candle, close in zip(market_data["candles"], closes):
            price = int(close)
            candle["open"] = str(price - 1200)
            candle["high"] = str(price + 2500)
            candle["low"] = str(price - 2500)
            candle["close"] = close
            candle["volume"] = "5"

        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-weak-confirmation-uptrend",
            market_data=market_data,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["regime"], "UPTREND")
        self.assertEqual(report["final_decision"], "NO_TRADE")
        self.assertIn("STRATEGY_NOT_ELIGIBLE", report["no_trade_reasons"])
        self.assertLess(float(report["feature_snapshot"]["volume_expansion_ratio"]), 1.05)
        self.assertLess(float(report["feature_snapshot"]["momentum_pct"]), 1.50)
        self.assertLessEqual(float(report["feature_snapshot"]["range_breakout_pct"]), 0)
        self.assertTrue(all(candidate["decision"] == "NO_TRADE" for candidate in report["strategy_candidates"]))
        self.assertIsNone(report["paper_fill"])
        self.assertEqual(report["paper_ledger_events"], [])
        self.assertFalse(report["live_order_allowed"])

    def test_range_regime_blocks_pullback_trend_entry_review(self):
        market_data = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        closes = ["1000000", "1020000", "1030000", "1025000", "1020000", "1015000"]
        for candle, close in zip(market_data["candles"], closes):
            price = int(close)
            candle["open"] = str(price - 1000)
            candle["high"] = str(price + 2500)
            candle["low"] = str(price - 2500)
            candle["close"] = close
            candle["volume"] = "20"
        market_data["candles"][-1]["volume"] = "80"

        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-range-pullback-alignment-block",
            market_data=market_data,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["feature_snapshot"]["regime"], "RANGE")
        self.assertEqual(report["feature_snapshot"]["trend_pullback_alignment_status"], "FAIL")
        self.assertEqual(report["feature_snapshot"]["trend_pullback_alignment_reason"], "REGIME_NOT_UPTREND")
        self.assertLess(float(report["feature_snapshot"]["trend_pullback_alignment_score"]), 0.70)
        pullback_candidate = next(
            candidate
            for candidate in report["strategy_candidates"]
            if candidate["strategy_family"] == "PULLBACK_TREND_LONG"
        )
        self.assertEqual(pullback_candidate["decision"], "NO_TRADE")
        self.assertEqual(pullback_candidate["no_trade_reason"], "STRATEGY_NOT_ELIGIBLE")
        self.assertLess(float(pullback_candidate["signal_strength"]), 0.55)
        self.assertEqual(report["final_decision"], "NO_TRADE")
        self.assertIsNone(report["paper_fill"])
        self.assertEqual(report["paper_ledger_events"], [])
        self.assertEqual(
            report["selected_symbol_evidence_scorecard"]["trend_pullback_alignment_status"],
            "FAIL",
        )
        self.assertFalse(report["live_order_allowed"])

    def test_overextended_uptrend_exhaustion_blocks_new_entry_and_tightens_exit_plan(self):
        market_data = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        closes = ["1000000", "1010000", "1020000", "1030000", "1040000", "1050000"]
        volumes = ["5", "5", "5", "5", "5", "20"]
        for candle, close, volume in zip(market_data["candles"], closes, volumes):
            price = int(close)
            candle["open"] = str(price - 2500)
            candle["high"] = str(price + 3500)
            candle["low"] = str(price - 3500)
            candle["close"] = close
            candle["volume"] = volume

        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-overextended-trend-exhaustion",
            market_data=market_data,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["feature_snapshot"]["regime"], "UPTREND")
        self.assertEqual(report["feature_snapshot"]["trend_exhaustion_status"], "WARN")
        self.assertGreaterEqual(float(report["feature_snapshot"]["volatility_pct"]), 3.0)
        self.assertGreaterEqual(float(report["feature_snapshot"]["momentum_pct"]), 3.0)
        self.assertGreaterEqual(float(report["feature_snapshot"]["volume_expansion_ratio"]), 1.5)
        self.assertEqual(report["final_decision"], "NO_TRADE")
        self.assertIn(
            report["selected_candidate"]["no_trade_reason"],
            {"MIN_EDGE_FAIL", "STRATEGY_CONFIDENCE_LOW", "STRATEGY_NOT_ELIGIBLE"},
        )
        self.assertTrue(all(candidate["decision"] == "NO_TRADE" for candidate in report["strategy_candidates"]))
        self.assertIsNone(report["paper_fill"])
        self.assertEqual(report["paper_ledger_events"], [])
        self.assertEqual(report["exit_plan"]["trend_exhaustion_exit_adjustment"], "TIGHTENED_TRAILING_AND_TIME_STOP")
        self.assertEqual(report["exit_plan"]["time_stop_candles"], 5)
        self.assertEqual(report["exit_plan"]["trailing_formula"], "start_after_0.8*atr_proxy_then_distance_0.55*atr_proxy")
        self.assertFalse(report["live_order_allowed"])

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

    def test_existing_position_near_exposure_cap_holds_position_without_new_fill(self):
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.3465",
            fill_price="1000000",
            mark_price="1000000",
            fee_amount="173.25",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle",
            source_paper_ledger_head_hash="A" * 64,
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-hold-existing-position",
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "HOLD_POSITION")
        self.assertIn("POSITION_LIMIT", report["no_trade_reasons"])
        self.assertIsNone(report["paper_fill"])
        self.assertEqual(report["paper_ledger_events"], [])
        self.assertEqual(report["paper_ledger_head_hash"], "A" * 64)
        self.assertEqual(report["paper_portfolio_snapshot"]["source_runtime_cycle_id"], report["cycle_id"])
        self.assertEqual(report["paper_portfolio_snapshot"]["source_paper_ledger_head_hash"], "A" * 64)
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 1)
        self.assertEqual(report["paper_portfolio_snapshot"]["positions"][0]["symbol"], "KRW-BTC")
        self.assertEqual(report["position_management_decision"]["decision"], "HOLD_EXISTING_POSITION_NO_NEW_ENTRY")
        self.assertFalse(report["live_order_allowed"])

    def test_existing_position_sizing_veto_keeps_managed_symbol_scope_when_universe_top_differs(self):
        btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for candle in [*btc["candles"], *eth["candles"]]:
            candle["volume"] = "5"
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.36",
            fill_price="1000000",
            mark_price="1000000",
            fee_amount="180",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle-managed-scope",
            source_paper_ledger_head_hash="E" * 64,
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-managed-scope-with-entry-sizing-veto",
            symbol="KRW-BTC",
            market_data_universe=[eth, btc],
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["selected_symbol"], "KRW-BTC")
        self.assertEqual(report["final_decision"], "HOLD_POSITION")
        self.assertIn("POSITION_LIMIT", report["no_trade_reasons"])
        self.assertEqual(report["sizing_decision"]["sizing_status"], "BLOCKED")
        self.assertEqual(report["sizing_decision"]["primary_blocker_code"], "RISK_VETO")
        self.assertIsNone(report["paper_fill"])
        self.assertEqual(report["paper_ledger_events"], [])
        self.assertEqual(report["position_management_decision"]["decision"], "HOLD_EXISTING_POSITION_NO_NEW_ENTRY")
        self.assertEqual(report["position_management_decision"]["managed_position_symbol"], "KRW-BTC")
        self.assertFalse(report["live_order_allowed"])

    def test_existing_position_exits_when_rotation_opportunity_cost_is_material(self):
        weak_btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for candle in weak_btc["candles"]:
            candle["volume"] = "1"
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)
        mark_price = weak_btc["candles"][-1]["close"]
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.005",
            fill_price=mark_price,
            mark_price=mark_price,
            fee_amount="2.5",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle-rotation",
            source_paper_ledger_head_hash="B" * 64,
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-rotation-exit",
            symbol="KRW-BTC",
            market_data_universe=[weak_btc, strong_eth],
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "EXIT_POSITION")
        self.assertIn("ROTATION_OPPORTUNITY_COST", report["no_trade_reasons"])
        self.assertEqual(report["selected_symbol"], "KRW-BTC")
        self.assertEqual(report["paper_fill"]["side"], "SELL")
        self.assertEqual(report["paper_fill"]["symbol"], "KRW-BTC")
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 0)
        rotation = report["position_management_decision"]["position_exit_evaluation"]
        self.assertTrue(rotation["rotation_condition_passed"])
        self.assertEqual(rotation["rotation_action"], "FULL_EXIT")
        self.assertEqual(rotation["rotation_candidate_symbol"], "KRW-ETH")
        self.assertGreaterEqual(float(rotation["rotation_net_ev_advantage_bps"]), float(rotation["rotation_threshold_bps"]))
        self.assertFalse(report["paper_fill"]["order_adapter_called"])
        self.assertFalse(report["paper_fill"]["private_endpoint_called"])
        self.assertFalse(report["live_order_allowed"])

    def test_rotation_exit_outranks_weak_tp1_partial_exit(self):
        weak_btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, close in enumerate(
            ["117720000", "117760000", "117820000", "117880000", "117940000", "118073000"]
        ):
            price = Decimal(close)
            weak_btc["candles"][index].update(
                {
                    "open": str(price - Decimal("10000")),
                    "high": str(price + Decimal("15000")),
                    "low": str(price - Decimal("15000")),
                    "close": close,
                    "volume": "1",
                }
            )
        strong_jto = build_upbit_public_candle_fixture(
            symbol="KRW-JTO",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_jto["candles"], start=1):
            candle["volume"] = str(8 + index * 2)
        mark_price = Decimal(weak_btc["candles"][-1]["close"])
        average_entry = Decimal("117554915.2186509936099053524")
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity=str(Decimal("95000") / average_entry),
            fill_price=str(average_entry),
            mark_price=str(mark_price),
            fee_amount="47.5",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle-tp1-rotation-conflict",
            source_paper_ledger_head_hash="A" * 64,
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-rotation-outranks-tp1",
            symbol="KRW-BTC",
            market_data_universe=[weak_btc, strong_jto],
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["final_decision"], "EXIT_POSITION")
        self.assertIn("ROTATION_OPPORTUNITY_COST", report["no_trade_reasons"])
        self.assertNotIn("TAKE_PROFIT_1", report["no_trade_reasons"])
        rotation = report["position_management_decision"]["position_exit_evaluation"]
        self.assertLess(Decimal(rotation["tp1"]), Decimal(rotation["mark_price"]))
        self.assertTrue(rotation["rotation_condition_passed"])
        self.assertEqual(rotation["rotation_action"], "FULL_EXIT")
        self.assertEqual(rotation["rotation_candidate_symbol"], "KRW-JTO")
        self.assertFalse(report["paper_fill"]["order_adapter_called"])
        self.assertFalse(report["paper_fill"]["private_endpoint_called"])
        self.assertFalse(report["live_order_allowed"])

    def test_existing_position_rotation_partial_exit_records_reduce_without_blocking_writer(self):
        weak_btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for candle in weak_btc["candles"]:
            candle["volume"] = "1"
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)
        mark_price = weak_btc["candles"][-1]["close"]
        quantity = Decimal("20000") / Decimal(str(mark_price))
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity=str(quantity),
            fill_price=mark_price,
            mark_price=mark_price,
            fee_amount="10",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle-partial-rotation",
            source_paper_ledger_head_hash="F" * 64,
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-rotation-partial-exit",
            symbol="KRW-BTC",
            market_data_universe=[weak_btc, strong_eth],
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "REDUCE_POSITION")
        self.assertEqual(report["paper_fill"]["side"], "SELL")
        self.assertTrue(report["paper_fill"]["partial_fill"])
        self.assertEqual(report["position_management_decision"]["requested_position_decision"], "EXIT_POSITION")
        self.assertEqual(report["position_management_decision"]["execution_adjusted_position_decision_reason"], "PARTIAL_EXIT_FILL")
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 1)
        self.assertFalse(report["paper_fill"]["order_adapter_called"])
        self.assertFalse(report["paper_fill"]["private_endpoint_called"])
        self.assertFalse(report["live_order_allowed"])

    def test_risk_off_exit_records_rotation_opportunity_without_blocking_writer(self):
        weak_btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="DOWNTREND",
        )
        for candle in weak_btc["candles"]:
            candle["volume"] = "1"
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)
        mark_price = weak_btc["candles"][-1]["close"]
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.005",
            fill_price="1000000",
            mark_price=mark_price,
            fee_amount="2.5",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle-risk-off-rotation",
            source_paper_ledger_head_hash="E" * 64,
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-risk-off-exit-with-rotation-opportunity",
            symbol="KRW-BTC",
            market_data_universe=[weak_btc, strong_eth],
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["final_decision"], "EXIT_POSITION")
        self.assertIn("REGIME_REVERSAL", report["no_trade_reasons"])
        rotation = report["position_management_decision"]["position_exit_evaluation"]
        self.assertTrue(rotation["rotation_condition_passed"])
        self.assertEqual(rotation["rotation_action"], "FULL_EXIT")
        self.assertEqual(rotation["rotation_reason_code"], "REGIME_ROTATION_EXIT")
        self.assertEqual(report["position_management_decision"]["position_exit_reason_code"], "REGIME_REVERSAL")
        self.assertEqual(report["paper_fill"]["side"], "SELL")
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 0)
        self.assertFalse(report["paper_fill"]["order_adapter_called"])
        self.assertFalse(report["paper_fill"]["private_endpoint_called"])
        self.assertFalse(report["live_order_allowed"])

    def test_existing_position_rotation_stays_hold_when_advantage_is_below_threshold(self):
        btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for candle in [*btc["candles"], *eth["candles"]]:
            candle["volume"] = "5"
        mark_price = btc["candles"][-1]["close"]
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.005",
            fill_price=mark_price,
            mark_price=mark_price,
            fee_amount="2.5",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle-rotation-hold",
            source_paper_ledger_head_hash="D" * 64,
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-rotation-hold",
            symbol="KRW-BTC",
            market_data_universe=[btc, eth],
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "HOLD_POSITION")
        self.assertIsNone(report["paper_fill"])
        rotation = report["position_management_decision"]["position_exit_evaluation"]
        self.assertFalse(rotation["rotation_condition_passed"])
        self.assertEqual(rotation["rotation_action"], "NONE")
        self.assertEqual(rotation["rotation_net_ev_advantage_bps"], "0")
        self.assertFalse(report["live_order_allowed"])

    def test_position_rotation_advantage_tamper_is_rejected(self):
        weak_btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for candle in weak_btc["candles"]:
            candle["volume"] = "1"
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)
        mark_price = weak_btc["candles"][-1]["close"]
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.005",
            fill_price=mark_price,
            mark_price=mark_price,
            fee_amount="2.5",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle-rotation-tamper",
            source_paper_ledger_head_hash="E" * 64,
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-rotation-tamper",
            symbol="KRW-BTC",
            market_data_universe=[weak_btc, strong_eth],
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )
        report["position_management_decision"]["position_exit_evaluation"]["rotation_net_ev_advantage_bps"] = "0"
        report["cycle_hash"] = upbit_paper_runtime_cycle_hash(report)

        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_existing_position_take_profit_exits_with_paper_sell_fill_and_closes_portfolio(self):
        market_data = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="900000",
            mark_price=market_data["candles"][-1]["close"],
            fee_amount="4.5",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-paper-cycle-tp",
            source_paper_ledger_head_hash="C" * 64,
        )
        report = build_upbit_paper_runtime_cycle_report(
            cycle_id="runtime-cycle-exit-existing-position",
            market_data=market_data,
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )
        result = validate_upbit_paper_runtime_cycle_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "EXIT_POSITION")
        self.assertIn("TAKE_PROFIT_2", report["no_trade_reasons"])
        self.assertEqual(report["paper_fill"]["side"], "SELL")
        self.assertEqual(report["paper_fill"]["order_lifecycle_state"], "FILLED")
        self.assertEqual(report["paper_ledger_events"][-1]["side"], "SELL")
        self.assertEqual(report["paper_ledger_head_hash"], report["paper_ledger_events"][-1]["event_hash"])
        self.assertEqual(report["paper_portfolio_snapshot"]["open_position_count"], 0)
        self.assertEqual(report["position_management_decision"]["decision"], "EXIT_POSITION_WITH_PAPER_SELL_FILL")
        self.assertEqual(report["position_management_decision"]["managed_position_symbol"], "KRW-BTC")
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

    def test_paper_broker_fill_component_tamper_is_rejected(self):
        report = build_upbit_paper_runtime_cycle_report(cycle_id="runtime-cycle-fill-cost-tamper")
        report["paper_fill"]["market_impact_bps"] = "999"
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
