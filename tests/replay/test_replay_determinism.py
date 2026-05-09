import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
from trader1.research.profitability.candidate_scorecard import candidate_scorecard_from_upbit_paper_runtime_cycle
from trader1.research.profitability.overfit_diagnostic import overfit_diagnostic_from_upbit_paper_runtime
from trader1.research.replay.replay_runner import (
    build_public_replay_fetch_failure_report,
    build_replay_consistency_report,
    build_public_replay_robustness_report,
    min_required_closed_trade_sample_count_for_public_replay,
    public_replay_robustness_report_hash,
    public_replay_robustness_values_from_report,
    public_replay_source_evidence_id,
    required_replay_closed_trade_threshold,
    validate_public_replay_robustness_report,
    replay_consistency_hash,
    validate_replay_consistency_report,
)
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]


def _public_replay_fixture(*, symbol: str, count: int) -> dict:
    market_data = build_upbit_public_candle_fixture(symbol=symbol, session_id="mvp4_upbit_paper_runtime")
    start = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    candles = []
    for index in range(count):
        price = 980000 + index * 900 + (index % 5) * 250
        candles.append(
            {
                "timestamp": (start + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"),
                "open": str(price - 700),
                "high": str(price + 1800),
                "low": str(price - 1400),
                "close": str(price),
                "volume": str(5 + (index % 7)),
            }
        )
    market_data["source"] = "PUBLIC_REST_READ_ONLY"
    market_data["profile"] = "TEST_PUBLIC_REPLAY_HISTORY"
    market_data["candles"] = candles
    market_data["raw_payload_private_fields_present"] = False
    market_data["public_endpoint_host"] = "api.upbit.com"
    market_data["public_endpoint_path"] = "/v1/candles/minutes/1"
    market_data["credential_load_attempted"] = False
    market_data["authorization_header_present"] = False
    market_data["private_endpoint_called"] = False
    market_data["order_endpoint_called"] = False
    return market_data


class ReplayDeterminismTest(unittest.TestCase):
    def test_same_input_replays_to_same_hash(self):
        report = build_replay_consistency_report(
            replay_id="replay-pass",
            strategy_unit_id="strategy-1",
            parameter_hash="A" * 64,
            input_events=[{"event_id": "event-1", "price": "100"}],
        )
        result = validate_replay_consistency_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(len(set(report["result_hashes"])), 1)

    def test_replay_hash_mismatch_fails(self):
        report = build_replay_consistency_report(
            replay_id="replay-fail",
            strategy_unit_id="strategy-1",
            parameter_hash="A" * 64,
            input_events=[{"event_id": "event-1", "price": "100"}],
        )
        report["result_hashes"][1] = "B" * 64
        report["deterministic_pass"] = False
        report["replay_consistency_hash"] = replay_consistency_hash(report)
        result = validate_replay_consistency_report(report)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")

    def test_replay_live_mutation_blocks(self):
        report = build_replay_consistency_report(
            replay_id="replay-live",
            strategy_unit_id="strategy-1",
            parameter_hash="A" * 64,
            input_events=[{"event_id": "event-1", "price": "100"}],
        )
        report["live_order_allowed"] = True
        report["replay_consistency_hash"] = replay_consistency_hash(report)
        result = validate_replay_consistency_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_public_replay_robustness_builds_non_live_candidate_samples(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
            max_replay_windows=80,
        )
        result = validate_public_replay_robustness_report(report, candidate_scorecard=scorecard)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["replay_status"], "PASS")
        self.assertGreaterEqual(report["sample_count"], 50)
        self.assertEqual(report["min_required_closed_trade_sample_count"], 30)
        self.assertEqual(
            report["replay_closed_trade_deficit"],
            max(30 - report["replay_closed_trade_sample_count"], 0),
        )
        self.assertIn(report["replay_closed_trade_maturity_status"], {"PASS", "BLOCKED", "UNTESTED"})
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(report["credential_load_attempted"])
        self.assertFalse(report["private_endpoint_called"])
        self.assertFalse(report["order_endpoint_called"])
        self.assertFalse(report["order_adapter_called"])

    def test_public_replay_tracks_sequential_closed_trade_exit_router_evidence(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-sequential-base",
            symbol="KRW-AXL",
            market_data=build_upbit_public_candle_fixture(
                symbol="KRW-AXL",
                session_id="mvp4_upbit_paper_runtime",
                profile="UPTREND_PULLBACK",
            ),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        candidate = dict(runtime["selected_candidate"])
        candidate["candidate_id"] = scorecard["candidate_id"]
        candidate["symbol"] = scorecard["symbol"]
        candidate["strategy_family"] = "PULLBACK_TREND_LONG"
        candidate["strategy_policy_reason"] = "PASS"
        candidate["decision"] = "PAPER_ENTRY_REVIEW"
        candidate["live_order_ready"] = False
        candidate["live_order_allowed"] = False
        candidate["can_live_trade"] = False
        candidate["scale_up_allowed"] = False
        calls: list[dict] = []

        def fake_runtime(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                return {
                    "cycle_id": kwargs["cycle_id"],
                    "cycle_hash": "A" * 64,
                    "final_decision": "ENTER_LONG",
                    "regime": "UPTREND",
                    "selected_candidate": candidate,
                    "strategy_candidates": [candidate],
                    "paper_fill": {
                        "side": "BUY",
                        "filled_notional": "10000",
                        "fee_amount": "5",
                        "fee_bps": "5",
                        "slippage_bps": "1",
                        "market_impact_bps": "0.5",
                        "adaptive_slippage_bps": "1",
                        "effective_spread_bps": "0.5",
                        "latency_penalty_bps": "0.25",
                        "order_lifecycle_state": "FILLED",
                    },
                    "position_management_decision": {},
                    "paper_portfolio_snapshot": {
                        "cash_available": "98995",
                        "equity": "100000",
                        "position_market_value": "10000",
                    },
                    "no_trade_reasons": [],
                }
            return {
                "cycle_id": kwargs["cycle_id"],
                "cycle_hash": "B" * 64,
                "final_decision": "EXIT_POSITION",
                "regime": "UPTREND",
                "selected_candidate": candidate,
                "strategy_candidates": [candidate],
                "paper_fill": {
                    "side": "SELL",
                    "filled_quantity": "1",
                    "filled_notional": "10200",
                    "fill_price": "10200",
                    "fee_amount": "5",
                    "fee_bps": "5",
                    "slippage_bps": "1",
                    "market_impact_bps": "0.5",
                    "adaptive_slippage_bps": "1",
                    "effective_spread_bps": "0.5",
                    "latency_penalty_bps": "0.25",
                    "order_lifecycle_state": "FILLED",
                },
                "position_management_decision": {
                    "entry_candidate_id": candidate["candidate_id"],
                    "managed_position_quantity": "1",
                    "managed_position_cost_basis": "10000",
                    "strategy_exit_policy_id": "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1",
                    "strategy_exit_variation": "trailing_tp",
                    "entry_strategy_exit_variation": "trailing_tp",
                    "strategy_exit_reason_code": "TRAILING_STOP",
                    "position_exit_reason_code": "TRAILING_STOP",
                    "strategy_exit_action": "FULL_EXIT",
                },
                "paper_portfolio_snapshot": {
                    "cash_available": "100190",
                    "equity": "100190",
                    "position_market_value": "0",
                },
                "no_trade_reasons": ["TRAILING_STOP"],
            }

        with patch("trader1.research.replay.replay_runner.build_upbit_paper_runtime_cycle_report", side_effect=fake_runtime):
            report = build_public_replay_robustness_report(
                candidate_scorecard=scorecard,
                market_data=_public_replay_fixture(symbol="KRW-AXL", count=7),
                min_required_sample_count=2,
                max_replay_windows=2,
            )

        result = validate_public_replay_robustness_report(report, candidate_scorecard=scorecard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["replay_closed_trade_sample_count"], 1)
        self.assertEqual(report["min_required_closed_trade_sample_count"], 2)
        self.assertEqual(report["replay_closed_trade_deficit"], 1)
        self.assertEqual(report["replay_closed_trade_maturity_status"], "BLOCKED")
        self.assertEqual(report["replay_closed_trade_maturity_blocker_code"], "REPLAY_CLOSED_TRADES_BELOW_MIN")
        self.assertEqual(report["replay_strategy_exit_policy_sample_count"], 1)
        self.assertEqual(report["replay_strategy_exit_policy_match_count"], 1)
        self.assertEqual(report["replay_strategy_exit_policy_mismatch_count"], 0)
        self.assertEqual(report["replay_strategy_exit_policy_status"], "PASS")
        self.assertEqual(report["sample_rows"][1]["closed_trade"], True)
        self.assertEqual(report["sample_rows"][1]["strategy_exit_reason_code"], "TRAILING_STOP")
        self.assertGreater(report["sample_rows"][1]["realized_trade_pnl_bps"], 0)
        self.assertEqual(calls[0]["paper_scope_focus"]["candidate_id"], scorecard["candidate_id"])
        self.assertEqual(calls[0]["paper_scope_focus"]["source"], "PUBLIC_REPLAY_CANDIDATE_SCOPE")
        self.assertFalse(calls[0]["paper_scope_focus"]["live_order_allowed"])
        self.assertIsNotNone(calls[1].get("current_paper_portfolio_snapshot"))
        self.assertFalse(report["live_order_allowed"])

    def test_closed_trade_maturity_threshold_is_not_window_count(self):
        self.assertEqual(
            required_replay_closed_trade_threshold(
                replay_window_minimum=2,
                runtime_mode="PAPER",
                replay_type="PUBLIC_REPLAY",
            ),
            2,
        )
        self.assertEqual(
            required_replay_closed_trade_threshold(
                replay_window_minimum=50,
                runtime_mode="PAPER",
                replay_type="PUBLIC_REPLAY",
            ),
            30,
        )
        self.assertEqual(
            required_replay_closed_trade_threshold(
                replay_window_minimum=300,
                runtime_mode="PAPER",
                replay_type="PUBLIC_REPLAY",
            ),
            30,
        )
        self.assertEqual(
            required_replay_closed_trade_threshold(
                replay_window_minimum=1000,
                runtime_mode="PAPER",
                replay_type="PUBLIC_REPLAY",
            ),
            100,
        )
        self.assertEqual(
            required_replay_closed_trade_threshold(
                replay_window_minimum=5000,
                runtime_mode="PAPER",
                replay_type="PUBLIC_REPLAY",
            ),
            120,
        )
        self.assertEqual(
            min_required_closed_trade_sample_count_for_public_replay(1000),
            required_replay_closed_trade_threshold(
                replay_window_minimum=1000,
                runtime_mode="PAPER",
                replay_type="PUBLIC_REPLAY",
            ),
        )

    def test_public_replay_ignores_non_target_candidate_fills_for_candidate_lifecycle(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-nontarget-base",
            symbol="KRW-AXL",
            market_data=build_upbit_public_candle_fixture(
                symbol="KRW-AXL",
                session_id="mvp4_upbit_paper_runtime",
                profile="UPTREND_PULLBACK",
            ),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        target = dict(runtime["selected_candidate"])
        target["candidate_id"] = scorecard["candidate_id"]
        target["symbol"] = scorecard["symbol"]
        target["strategy_family"] = "BREAKOUT_RETEST_LONG"
        target["decision"] = "PAPER_ENTRY_REVIEW"
        target["live_order_ready"] = False
        target["live_order_allowed"] = False
        target["can_live_trade"] = False
        target["scale_up_allowed"] = False
        other = dict(target)
        other["candidate_id"] = "KRW-AXL-nontarget-vwap"
        other["strategy_family"] = "VWAP_MEAN_REVERSION"
        calls: list[dict] = []

        def fake_runtime(**kwargs):
            calls.append(kwargs)
            return {
                "cycle_id": kwargs["cycle_id"],
                "cycle_hash": "C" * 64,
                "final_decision": "ENTER_LONG",
                "regime": "UPTREND",
                "selected_candidate": other,
                "strategy_candidates": [target, other],
                "paper_scope_continuity_decision": {
                    "requested": True,
                    "selection_status": "SELECTED",
                    "requested_candidate_id": target["candidate_id"],
                    "selected_candidate_id": other["candidate_id"],
                },
                "paper_fill": {
                    "side": "BUY",
                    "filled_notional": "10000",
                    "fee_amount": "5",
                    "fee_bps": "5",
                    "slippage_bps": "1",
                    "market_impact_bps": "0.5",
                    "adaptive_slippage_bps": "1",
                    "effective_spread_bps": "0.5",
                    "latency_penalty_bps": "0.25",
                    "order_lifecycle_state": "FILLED",
                },
                "position_management_decision": {
                    "entry_candidate_id": other["candidate_id"],
                    "managed_position_quantity": "1",
                    "managed_position_cost_basis": "10000",
                    "strategy_exit_policy_id": "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1",
                    "strategy_exit_variation": "trailing_tp",
                    "position_exit_reason_code": None,
                },
                "paper_portfolio_snapshot": {
                    "cash_available": "98995",
                    "equity": "100000",
                    "position_market_value": "10000",
                    "positions": [{"entry_candidate_id": other["candidate_id"]}],
                },
                "no_trade_reasons": [],
            }

        with patch("trader1.research.replay.replay_runner.build_upbit_paper_runtime_cycle_report", side_effect=fake_runtime):
            report = build_public_replay_robustness_report(
                candidate_scorecard=scorecard,
                market_data=_public_replay_fixture(symbol="KRW-AXL", count=7),
                min_required_sample_count=2,
                max_replay_windows=2,
            )

        result = validate_public_replay_robustness_report(report, candidate_scorecard=scorecard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["paper_scope_focus"]["candidate_id"], target["candidate_id"])
        self.assertNotIn("current_paper_portfolio_snapshot", calls[1])
        for row in report["sample_rows"]:
            self.assertEqual(row["runtime_paper_fill_side"], "BUY")
            self.assertFalse(row["paper_fill_belongs_to_candidate"])
            self.assertIsNone(row["paper_fill_side"])
            self.assertFalse(row["closed_trade"])
        self.assertEqual(report["replay_closed_trade_sample_count"], 0)
        self.assertEqual(report["replay_strategy_exit_policy_sample_count"], 0)
        self.assertFalse(report["live_order_allowed"])

    def test_public_replay_no_trade_rows_are_flat_cash_returns(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-flat-no-trade-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
            max_replay_windows=80,
        )
        result = validate_public_replay_robustness_report(report, candidate_scorecard=scorecard)
        no_trade_rows = [row for row in report["sample_rows"] if row["decision"] == "NO_TRADE"]

        self.assertEqual(result.status, "PASS")
        self.assertGreater(len(no_trade_rows), 0)
        for row in no_trade_rows:
            self.assertFalse(row["executed_trade"])
            self.assertEqual(row["replay_return_basis"], "FLAT_NO_TRADE_CASH_RETURN")
            self.assertEqual(row["net_ev_after_cost_bps"], 0.0)
            self.assertEqual(row["gross_expected_edge_bps"], 0.0)
            self.assertEqual(row["total_execution_cost_bps"], 0.0)
            self.assertIn("opportunity_net_ev_after_cost_bps", row)
            self.assertIn("opportunity_gross_expected_edge_bps", row)
            self.assertIn("opportunity_total_execution_cost_bps", row)

        values, samples, source_ids = public_replay_robustness_values_from_report(
            report,
            candidate_scorecard=scorecard,
        )
        self.assertEqual(len(values), report["replay_closed_trade_sample_count"])
        self.assertEqual(len(samples), report["replay_closed_trade_sample_count"])
        self.assertIn(
            public_replay_source_evidence_id(report["replay_id"], report["report_hash"]),
            source_ids,
        )
        for sample in samples:
            self.assertTrue(sample["closed_trade"])
            self.assertEqual(sample["value_source"], "PUBLIC_REPLAY_REALIZED_CLOSED_TRADE_PNL_BPS")

    def test_public_replay_robustness_report_matches_contract_schema(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-schema-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
            max_replay_windows=80,
        )
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)

    def test_public_replay_fetch_failure_report_is_source_bound_and_contract_valid(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-fetch-failed-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_fetch_failure_report(
            candidate_scorecard=scorecard,
            replay_id="public-replay-fetch-failed",
            error_type="TimeoutError",
            error_message="public candle read timed out",
            target_count=80,
            page_size=80,
            timeout_seconds=3.0,
            min_required_sample_count=1,
        )
        validation = validate_public_replay_robustness_report(report, candidate_scorecard=scorecard)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)
        schema_result = validate_instance_against_schema(report, schema, schema_bundle)

        self.assertEqual(validation.status, "PASS")
        self.assertEqual(schema_result.status, "PASS", schema_result.errors)
        self.assertEqual(report["public_market_data_source"], "PUBLIC_REST_READ_ONLY_FETCH_FAILED")
        self.assertEqual(report["public_market_data_fetch_status"], "FAILED")
        self.assertEqual(report["replay_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "DATA_QUALITY_INSUFFICIENT")
        self.assertEqual(report["sample_count"], 0)
        self.assertEqual(report["sample_rows"], [])
        self.assertEqual(len(report["public_market_data_hash"]), 64)
        self.assertFalse(report["credential_load_attempted"])
        self.assertFalse(report["private_endpoint_called"])
        self.assertFalse(report["order_endpoint_called"])
        self.assertFalse(report["order_adapter_called"])
        self.assertFalse(report["live_key_loaded"])
        self.assertFalse(report["live_order_allowed"])

    def test_public_replay_robustness_hash_tamper_fails(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-hash-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
        )
        report["sample_count"] = 1
        result = validate_public_replay_robustness_report(report, candidate_scorecard=scorecard)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_overfit_diagnostic_uses_public_replay_without_ranking_or_live_permission(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-overfit-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
        )
        diagnostic = overfit_diagnostic_from_upbit_paper_runtime(
            candidate_scorecard=scorecard,
            runtime_sample_history={
                "history_id": "invalid-history",
                "history_hash": "A" * 64,
            },
            replay_robustness_report=report,
            min_required_sample_count=50,
            min_required_bootstrap_iterations=50,
            min_required_oos_net_ev_bps=-1000.0,
            min_required_walk_forward_pass_rate=0.0,
            min_required_bootstrap_confidence_lower_bps=-1000.0,
            min_required_ranking_stability_score=0.0,
        )

        self.assertEqual(diagnostic["sample_count"], report["replay_closed_trade_sample_count"])
        self.assertEqual(diagnostic["oos_status"], "BLOCKED")
        self.assertEqual(diagnostic["walk_forward_status"], "BLOCKED")
        self.assertEqual(diagnostic["bootstrap_status"], "BLOCKED")
        self.assertFalse(diagnostic["robustness_eligible"])
        self.assertEqual(diagnostic["promotion_eligible"], False)
        self.assertIn("SAMPLE_INSUFFICIENT", {blocker["code"] for blocker in diagnostic["blockers"]})
        self.assertIn("SURVIVORSHIP_BIAS_RISK", {blocker["code"] for blocker in diagnostic["blockers"]})
        self.assertIn(
            public_replay_source_evidence_id(report["replay_id"], report["report_hash"]),
            diagnostic["source_evidence_ids"],
        )
        self.assertFalse(diagnostic["live_order_ready"])
        self.assertFalse(diagnostic["live_order_allowed"])
        self.assertFalse(diagnostic["can_live_trade"])
        self.assertFalse(diagnostic["scale_up_allowed"])

    def test_overfit_diagnostic_marks_public_replay_failures_as_failures(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-overfit-fail-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
        )
        for row in report["sample_rows"]:
            row["closed_trade"] = True
            row["realized_trade_pnl_bps"] = -25.0
            row["realized_vs_expected_edge_bps"] = -50.0
            row["strategy_exit_policy_observed"] = True
            row["strategy_exit_policy_matched"] = True
            row["strategy_exit_policy_id"] = "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1"
            row["strategy_exit_variation"] = row["expected_strategy_exit_variation"]
            row["strategy_exit_reason_code"] = "TEST_REALIZED_LOSS"
            row["strategy_exit_action"] = "FULL_EXIT"
        report.update(
            {
                "replay_closed_trade_sample_count": report["sample_count"],
                "replay_closed_trade_status": "PASS",
                "replay_strategy_exit_policy_sample_count": report["sample_count"],
                "replay_strategy_exit_policy_match_count": report["sample_count"],
                "replay_strategy_exit_policy_mismatch_count": 0,
                "replay_strategy_exit_policy_status": "PASS",
                "replay_strategy_exit_reason_counts": [
                    {"reason_code": "TEST_REALIZED_LOSS", "count": report["sample_count"]}
                ],
                "replay_profit_factor": 0.0,
                "replay_profit_factor_status": "FAIL",
                "replay_max_drawdown_bps": 25.0 * report["sample_count"],
                "replay_realized_vs_expected_edge_bps": -50.0,
                "replay_realized_vs_expected_edge_status": "FAIL",
                "replay_fill_quality_score": 1.0,
                "replay_execution_cost_delta_bps": 0.0,
                "replay_execution_cost_status": "PASS",
            }
        )
        report["report_hash"] = public_replay_robustness_report_hash(report)
        diagnostic = overfit_diagnostic_from_upbit_paper_runtime(
            candidate_scorecard=scorecard,
            runtime_sample_history={
                "history_id": "invalid-history",
                "history_hash": "A" * 64,
            },
            replay_robustness_report=report,
            min_required_sample_count=50,
            min_required_bootstrap_iterations=50,
            min_required_oos_net_ev_bps=1000.0,
            min_required_walk_forward_pass_rate=1.0,
            min_required_bootstrap_confidence_lower_bps=1000.0,
            min_required_ranking_stability_score=0.99,
        )
        blocker_codes = {blocker["code"] for blocker in diagnostic["blockers"]}

        self.assertEqual(diagnostic["oos_status"], "FAIL")
        self.assertEqual(diagnostic["walk_forward_status"], "FAIL")
        self.assertEqual(diagnostic["bootstrap_status"], "FAIL")
        self.assertIn("PUBLIC_REPLAY_ROBUSTNESS_FAILED", blocker_codes)
        self.assertIn("OOS_FAILED", blocker_codes)
        self.assertIn("WALK_FORWARD_FAILED", blocker_codes)
        self.assertIn("BOOTSTRAP_FAILED", blocker_codes)
        self.assertFalse(diagnostic["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
