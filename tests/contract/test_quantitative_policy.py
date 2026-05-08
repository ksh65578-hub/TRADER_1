import unittest

from trader1.core.strategy.quantitative_policy import (
    build_exit_plan,
    build_quantitative_policy_report,
    classify_regime,
    compute_net_expected_edge,
    deduplicate_events,
    evaluate_binance_futures_short_entry,
    evaluate_live_ready_snapshot_candidate,
    evaluate_pullback_trend_entry,
    evaluate_risk_state,
    grade_signal,
    size_position,
)
from trader1.validation.mvp0_validators import quantitative_policy_validator


class QuantitativePolicyClosureTest(unittest.TestCase):
    def test_weak_signal_is_no_trade(self):
        result = grade_signal(
            {
                "regime_confidence": 0.50,
                "strategy_fit_score": 0.50,
                "confirmation_score": 0.50,
                "net_edge_score": 0.50,
                "liquidity_score": 0.50,
                "execution_quality_score": 0.50,
                "historical_pattern_score": 0.50,
            }
        )

        self.assertEqual(result["signal_grade"], "no_trade")
        self.assertFalse(result["entry_candidate_allowed"])
        self.assertEqual(result["primary_blocker_code"], "STRATEGY_CONFIDENCE_LOW")

    def test_negative_net_edge_blocks_entry(self):
        result = compute_net_expected_edge(
            {
                "expected_target_move": 0.010,
                "probability_of_target": 0.40,
                "expected_stop_move": 0.012,
                "probability_of_stop": 0.60,
                "fee_cost": 0.0010,
                "spread_cost": 0.0008,
                "slippage_cost": 0.0008,
                "funding_cost": 0.0,
            }
        )

        self.assertLessEqual(result["net_expected_edge"], 0)
        self.assertFalse(result["net_edge_positive"])
        self.assertEqual(result["primary_blocker_code"], "MIN_EDGE_FAIL")

    def test_downtrend_blocks_spot_long_pullback(self):
        edge = compute_net_expected_edge(
            {
                "expected_target_move": 0.030,
                "probability_of_target": 0.60,
                "expected_stop_move": 0.010,
                "probability_of_stop": 0.40,
                "fee_cost": 0.0010,
                "spread_cost": 0.0005,
                "slippage_cost": 0.0005,
                "funding_cost": 0.0,
            }
        )
        result = evaluate_pullback_trend_entry(
            {
                "mode": "PAPER",
                "regime": "downtrend",
                "ema50": 90,
                "ema200": 100,
                "ema50_slope": -0.2,
                "adx": 30,
                "pullback_depth_atr": 0.8,
                "price_distance_to_anchor_atr": 0.2,
                "confirmation_score": 0.9,
                "regime_confidence": 0.85,
                "strategy_fit_score": 0.9,
                "net_edge_score": 0.9,
                "liquidity_score": 0.9,
                "execution_quality_score": 0.9,
                "historical_pattern_score": 0.9,
                "edge": edge,
            }
        )

        self.assertFalse(result["candidate_allowed"])
        self.assertEqual(result["candidate_decision"], "NO_TRADE")
        self.assertEqual(result["primary_blocker_code"], "REGIME_MISMATCH")

    def test_binance_futures_short_paper_candidate_is_surface_only_and_live_false(self):
        edge = compute_net_expected_edge(
            {
                "expected_target_move": 0.025,
                "probability_of_target": 0.62,
                "expected_stop_move": 0.010,
                "probability_of_stop": 0.38,
                "fee_cost": 0.0008,
                "spread_cost": 0.0004,
                "slippage_cost": 0.0006,
                "funding_cost": 0.0001,
            }
        )
        result = evaluate_binance_futures_short_entry(
            {
                "exchange": "BINANCE",
                "market_type": "FUTURES_USDT_M",
                "leverage": 1,
                "regime": "downtrend",
                "breakdown_confirmation": True,
                "failed_rebound": True,
                "funding_cost_acceptable": True,
                "liquidity_score": 0.75,
                "spread_percentile": 55,
                "panic_spread_percentile": 70,
                "edge": edge,
            }
        )

        self.assertTrue(result["candidate_allowed"])
        self.assertEqual(result["candidate_decision"], "ENTER_SHORT")
        self.assertEqual(result["runtime_decision"], "NO_TRADE")
        self.assertFalse(result["can_submit_order"])
        self.assertFalse(result["live_order_ready"])
        self.assertEqual(result["primary_blocker_code"], "BINANCE_FUTURES_SURFACE_ONLY")

    def test_risk_cap_blocks_position_sizing(self):
        result = size_position(
            {
                "equity": 1_000_000,
                "risk_per_trade": 0.002,
                "signal_grade": "strong",
                "regime_confidence": 0.80,
                "strategy_score": 0.80,
                "drawdown_pct": 0.01,
                "liquidity_score": 0.90,
                "volatility_percentile": 50,
                "stop_distance": 1000,
                "daily_loss_pct": 0.011,
                "weekly_loss_pct": 0.0,
                "monthly_loss_pct": 0.0,
                "current_exposure": 0,
                "max_exposure": 400_000,
                "liquidity_notional": 5_000_000,
            }
        )

        self.assertEqual(result["position_size"], 0.0)
        self.assertEqual(result["primary_blocker_code"], "DRAWDOWN_FREEZE_ACTIVE")

    def test_drawdown_reduces_sizing_before_freeze(self):
        base_inputs = {
            "equity": 1_000_000,
            "risk_per_trade": 0.002,
            "signal_grade": "strong",
            "regime_confidence": 0.80,
            "strategy_score": 0.80,
            "liquidity_score": 0.90,
            "volatility_percentile": 50,
            "stop_distance": 1000,
            "daily_loss_pct": 0.0,
            "weekly_loss_pct": 0.0,
            "monthly_loss_pct": 0.0,
            "current_exposure": 0,
            "max_exposure": 400_000,
            "liquidity_notional": 5_000_000,
        }
        normal = size_position({**base_inputs, "drawdown_pct": 0.01})
        reduced = size_position({**base_inputs, "drawdown_pct": 0.03})

        self.assertGreater(normal["position_size"], reduced["position_size"])
        self.assertEqual(reduced["risk_multiplier"], 0.5)

    def test_cooling_blocks_new_entry(self):
        result = evaluate_risk_state(
            {
                "equity_high": 1_000_000,
                "current_equity": 990_000,
                "daily_loss_pct": 0.010,
                "weekly_loss_pct": 0.0,
                "monthly_loss_pct": 0.0,
                "consecutive_losses": 3,
            }
        )

        self.assertEqual(result["risk_state"], "cooling")
        self.assertFalse(result["new_entry_allowed"])
        self.assertEqual(result["primary_blocker_code"], "COOLDOWN")

    def test_exit_plan_preserves_strategy_tight_atr_multipliers(self):
        result = build_exit_plan(
            {
                "entry_price": 100,
                "atr": 2,
                "side": "LONG",
                "hard_stop_atr": 0.75,
                "tp1_atr": 0.65,
                "tp2_atr": 1.0,
                "trailing_start_atr": 0.9,
                "trailing_distance_atr": 0.5,
                "partial_take_profit_ratio": 0.50,
                "time_stop_candles": 4,
            }
        )

        self.assertAlmostEqual(result["hard_stop"], 98.5)
        self.assertAlmostEqual(result["tp1"], 101.3)
        self.assertAlmostEqual(result["tp2"], 102.0)
        self.assertAlmostEqual(result["trailing_start"], 101.8)
        self.assertAlmostEqual(result["trailing_distance"], 1.0)
        self.assertEqual(result["time_stop_candles"], 4)

    def test_duplicate_event_not_double_counted(self):
        result = deduplicate_events(
            [
                {"event_id": "cycle-1", "value": 1},
                {"event_id": "cycle-1", "value": 999},
                {"event_id": "cycle-2", "value": 2},
            ]
        )

        self.assertEqual(result["input_count"], 3)
        self.assertEqual(result["unique_count"], 2)
        self.assertEqual(result["duplicate_event_ids"], ["cycle-1"])

    def test_live_without_snapshot_is_blocked(self):
        result = evaluate_live_ready_snapshot_candidate({"snapshot_present": False})

        self.assertFalse(result["live_order_ready"])
        self.assertFalse(result["live_order_allowed"])
        self.assertFalse(result["can_live_trade"])
        self.assertEqual(result["primary_blocker_code"], "LIVE_READY_MISSING")

    def test_dashboard_reason_code_emitted(self):
        report = build_quantitative_policy_report()

        self.assertEqual(report["dashboard_reason_code"], "LIVE_READY_MISSING")
        self.assertFalse(report["live_order_allowed"])
        self.assertIn("LIVE blocked", report["dashboard_operator_message"])

    def test_regime_priority_panic_beats_uptrend(self):
        result = classify_regime(
            {
                "price": 110,
                "ema20": 105,
                "ema50": 100,
                "ema200": 80,
                "ema50_slope": 0.5,
                "adx": 35,
                "atr": 4,
                "realized_volatility_zscore": 2.6,
                "realized_volatility_percentile": 98,
                "volume_zscore": 3.0,
                "volume_percentile": 95,
                "vwap_distance_atr": 0.5,
                "spread_percentile": 60,
                "liquidity_score": 0.9,
                "data_health_score": 1.0,
            }
        )

        self.assertEqual(result["regime"], "panic")
        self.assertEqual(result["priority_order"][0], "panic")

    def test_quantitative_policy_validator_passes(self):
        result = quantitative_policy_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
