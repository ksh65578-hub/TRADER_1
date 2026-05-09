import unittest
from decimal import Decimal

from trader1.adapters.upbit.market_data import build_upbit_public_candle_data_from_rest_payload
from trader1.runtime.paper.upbit_public_collector import build_upbit_public_market_data_collection_report
from trader1.runtime.portfolio.paper_portfolio import (
    build_initial_paper_portfolio_snapshot,
    build_paper_portfolio_snapshot_after_sell_fill,
    build_paper_portfolio_snapshot_from_fill,
    mark_paper_portfolio_snapshot_to_public_market,
    paper_portfolio_hash,
    validate_paper_portfolio_snapshot,
)
from trader1.runtime.portfolio.paper_current_truth_refresh import (
    build_paper_current_truth_refresh_report,
    paper_current_truth_refresh_report_hash,
    validate_paper_current_truth_refresh_report,
)


class PaperPortfolioTest(unittest.TestCase):
    def test_upbit_paper_portfolio_snapshot_is_simulated_and_live_blocked(self):
        snapshot = build_initial_paper_portfolio_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio",
        )
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(snapshot["currency"], "KRW")
        self.assertEqual(snapshot["cash_available"], "1000000")
        self.assertEqual(snapshot["position_market_value"], "0")
        self.assertEqual(snapshot["equity"], "1000000")
        self.assertEqual(snapshot["total_pnl"], "0")
        self.assertEqual(snapshot["return_pct"], "0")
        self.assertEqual(snapshot["open_position_count"], 0)
        self.assertIsNone(snapshot["source_runtime_cycle_id"])
        self.assertIsNone(snapshot["source_paper_ledger_head_hash"])
        self.assertEqual(snapshot["display_balance_kind"], "SIMULATED_PAPER_LEDGER")
        self.assertFalse(snapshot["live_order_ready"])
        self.assertFalse(snapshot["live_order_allowed"])
        self.assertFalse(snapshot["can_live_trade"])
        self.assertFalse(snapshot["can_submit_order"])

    def test_paper_current_truth_refresh_binds_verified_snapshot_without_live_permission(self):
        snapshot = build_initial_paper_portfolio_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-current-truth-refresh",
        )
        report = build_paper_current_truth_refresh_report(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test-paper-current-truth-refresh",
            paper_portfolio_snapshot=snapshot,
            heartbeat={"heartbeat_status": "PASS", "heartbeat_hash": "A" * 64},
            startup_probe={"startup_probe_passed": True, "probe_hash": "B" * 64},
        )
        result = validate_paper_current_truth_refresh_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["refresh_status"], "PASS_PAPER_CURRENT_TRUTH_REFRESHED")
        self.assertEqual(report["source_portfolio_snapshot_hash"], snapshot["snapshot_hash"])
        self.assertEqual(report["verified_cash"], "1000000")
        self.assertEqual(report["verified_equity"], "1000000")
        self.assertEqual(report["verified_locked_cash"], "0")
        self.assertEqual(report["verified_realized_pnl"], "0")
        self.assertEqual(report["source_balance_kind"], "SIMULATED_PAPER_LEDGER")
        self.assertFalse(report["audited_current_evidence_writer"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_paper_current_truth_refresh_blocks_permission_drift(self):
        snapshot = build_initial_paper_portfolio_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-current-truth-refresh-live",
        )
        report = build_paper_current_truth_refresh_report(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test-paper-current-truth-refresh-live",
            paper_portfolio_snapshot=snapshot,
            heartbeat={"heartbeat_status": "PASS", "heartbeat_hash": "A" * 64},
            startup_probe={"startup_probe_passed": True, "probe_hash": "B" * 64},
        )
        report["live_order_allowed"] = True
        report["refresh_report_hash"] = paper_current_truth_refresh_report_hash(report)
        result = validate_paper_current_truth_refresh_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_binance_paper_portfolio_snapshot_is_scoped(self):
        snapshot = build_initial_paper_portfolio_snapshot(
            exchange="BINANCE",
            market_type="SPOT",
            session_id="test-binance-paper-portfolio",
        )
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(snapshot["currency"], "USDT")
        self.assertEqual(snapshot["cash_available"], "10000")
        self.assertEqual(snapshot["equity"], "10000")

    def test_upbit_paper_portfolio_updates_cash_position_and_unrealized_pnl_from_fill(self):
        snapshot = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio-fill",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
            source_runtime_cycle_id="portfolio-fill-cycle",
            source_paper_ledger_head_hash="A" * 64,
        )
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(snapshot["source_runtime_cycle_id"], "portfolio-fill-cycle")
        self.assertEqual(snapshot["source_paper_ledger_head_hash"], "A" * 64)
        self.assertEqual(snapshot["open_position_count"], 1)
        self.assertEqual(snapshot["positions"][0]["symbol"], "KRW-BTC")
        self.assertEqual(snapshot["position_market_value"], "10000")
        self.assertEqual(snapshot["unrealized_pnl"], "-10")
        self.assertEqual(snapshot["total_pnl"], "-10")
        self.assertEqual(snapshot["equity"], "999990")
        self.assertFalse(snapshot["live_order_allowed"])

    def test_paper_portfolio_normalizes_legacy_static_altcoin_price_basis_to_public_mark(self):
        snapshot = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio-alt-price-basis",
            symbol="KRW-ADA",
            side="BUY",
            quantity="0.007",
            fill_price="1000870",
            mark_price="1000870",
            fee_amount="3",
            source_runtime_cycle_id="portfolio-alt-price-basis-cycle",
            source_paper_ledger_head_hash="A" * 64,
        )
        close = Decimal("405")
        payload = [
            {
                "market": "KRW-ADA",
                "candle_date_time_utc": f"2026-05-06T21:{35 - offset:02d}:00",
                "opening_price": str(close),
                "high_price": str(close),
                "low_price": str(close),
                "trade_price": str(close),
                "candle_acc_trade_volume": str(10 + offset),
            }
            for offset in range(6)
        ]
        market_data = build_upbit_public_candle_data_from_rest_payload(
            payload=payload,
            symbol="KRW-ADA",
            session_id="test-paper-portfolio-alt-price-basis",
        )
        public_collection = build_upbit_public_market_data_collection_report(
            collector_id="test-paper-portfolio-alt-price-basis-public",
            session_id="test-paper-portfolio-alt-price-basis",
            symbol="KRW-ADA",
            market_data=market_data,
        )

        marked = mark_paper_portfolio_snapshot_to_public_market(
            paper_portfolio_snapshot=snapshot,
            public_market_data_collection_report=public_collection,
        )
        result = validate_paper_portfolio_snapshot(marked)

        self.assertEqual(result.status, "PASS")
        position = marked["positions"][0]
        expected_quantity = Decimal("0.007") * Decimal("1000870") / close
        self.assertEqual(marked["mark_to_market_status"], "PASS_PUBLIC_MARK_TO_MARKET")
        self.assertEqual(marked["price_basis_repair_status"], "APPLIED_PUBLIC_MARK_PRICE_BASIS_NORMALIZATION")
        self.assertEqual(
            marked["price_basis_repair_source"],
            "LEGACY_STATIC_FIXTURE_PRICE_BASIS_TO_UPBIT_KRW_SPOT_PUBLIC_MARK",
        )
        self.assertEqual(position["symbol"], "KRW-ADA")
        self.assertEqual(position["average_entry_price"], "405")
        self.assertEqual(position["mark_price"], "405")
        self.assertEqual(Decimal(position["quantity"]), expected_quantity)
        self.assertFalse(marked["live_order_ready"])
        self.assertFalse(marked["live_order_allowed"])
        self.assertFalse(marked["can_live_trade"])
        self.assertFalse(marked["scale_up_allowed"])

    def test_paper_portfolio_persists_entry_strategy_context_through_partial_sell(self):
        entry_context = {
            "entry_strategy_context_status": "BOUND_TO_ENTRY_CANDIDATE",
            "entry_strategy_context_source": "PAPER_RUNTIME_ENTRY_FILL",
            "entry_candidate_id": "KRW-BTC-vwap-mean-reversion",
            "entry_strategy_family": "VWAP_MEAN_REVERSION",
            "entry_strategy_exit_policy_id": "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1",
            "entry_strategy_exit_variation": "fixed_tp",
            "entry_strategy_source_runtime_cycle_id": "portfolio-strategy-entry-cycle",
            "entry_strategy_source_candidate_hash": "A" * 64,
            "entry_strategy_source_exit_plan_hash": "B" * 64,
            "entry_strategy_context_formula": "bind exit policy to entry strategy at fill time",
        }
        entry = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio-strategy-context",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000000",
            mark_price="1000000",
            fee_amount="5",
            source_runtime_cycle_id="portfolio-strategy-entry-cycle",
            source_paper_ledger_head_hash="A" * 64,
            entry_strategy_context=entry_context,
        )
        entry_result = validate_paper_portfolio_snapshot(entry)
        self.assertEqual(entry_result.status, "PASS")
        self.assertEqual(entry["positions"][0]["entry_candidate_id"], "KRW-BTC-vwap-mean-reversion")
        self.assertEqual(entry["positions"][0]["entry_strategy_family"], "VWAP_MEAN_REVERSION")

        reduced = build_paper_portfolio_snapshot_after_sell_fill(
            current_snapshot=entry,
            session_id="test-paper-portfolio-strategy-context",
            symbol="KRW-BTC",
            quantity="0.004",
            fill_price="1100000",
            fee_amount="2",
            source_runtime_cycle_id="portfolio-strategy-reduce-cycle",
            source_paper_ledger_head_hash="B" * 64,
        )
        reduced_result = validate_paper_portfolio_snapshot(reduced)
        self.assertEqual(reduced_result.status, "PASS")
        self.assertEqual(reduced["positions"][0]["entry_candidate_id"], "KRW-BTC-vwap-mean-reversion")
        self.assertEqual(reduced["positions"][0]["entry_strategy_exit_variation"], "fixed_tp")
        self.assertFalse(reduced["live_order_allowed"])

    def test_upbit_paper_portfolio_reduces_long_position_with_realized_pnl_from_sell_fill(self):
        entry = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio-sell",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000000",
            mark_price="1000000",
            fee_amount="5",
            source_runtime_cycle_id="portfolio-buy-cycle",
            source_paper_ledger_head_hash="A" * 64,
        )
        snapshot = build_paper_portfolio_snapshot_after_sell_fill(
            current_snapshot=entry,
            session_id="test-paper-portfolio-sell",
            symbol="KRW-BTC",
            quantity="0.004",
            fill_price="1100000",
            fee_amount="2",
            source_runtime_cycle_id="portfolio-sell-cycle",
            source_paper_ledger_head_hash="B" * 64,
        )
        result = validate_paper_portfolio_snapshot(snapshot)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(snapshot["cash_available"], "994393")
        self.assertEqual(snapshot["realized_pnl"], "396")
        self.assertEqual(snapshot["unrealized_pnl"], "597")
        self.assertEqual(snapshot["total_pnl"], "993")
        self.assertEqual(snapshot["equity"], "1000993")
        self.assertEqual(snapshot["open_position_count"], 1)
        self.assertEqual(snapshot["positions"][0]["quantity"], "0.006")
        self.assertEqual(snapshot["positions"][0]["cost_basis"], "6003")
        self.assertFalse(snapshot["live_order_allowed"])

    def test_paper_portfolio_accepts_explicit_rollup_source(self):
        snapshot = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio-rollup-source",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
        )
        snapshot["source"] = "PAPER_LEDGER_ROLLUP"
        snapshot["positions"][0]["source"] = "PAPER_LEDGER_ROLLUP"
        snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "PASS")
        self.assertFalse(snapshot["live_order_allowed"])

    def test_paper_portfolio_blocks_live_permission_drift(self):
        snapshot = build_initial_paper_portfolio_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio-live",
        )
        snapshot["live_order_allowed"] = True
        snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_paper_portfolio_detects_arithmetic_tamper(self):
        snapshot = build_initial_paper_portfolio_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio-tamper",
        )
        snapshot["equity"] = "2000000"
        snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_paper_portfolio_detects_total_pnl_tamper(self):
        snapshot = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio-pnl-tamper",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
        )
        snapshot["total_pnl"] = "0"
        snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_paper_portfolio_detects_position_market_value_tamper(self):
        snapshot = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-position-market-value-tamper",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
        )
        snapshot["positions"][0]["market_value"] = "9999"
        snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_paper_portfolio_detects_position_unrealized_pnl_tamper(self):
        snapshot = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-position-unrealized-tamper",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
        )
        snapshot["positions"][0]["unrealized_pnl"] = "0"
        snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_paper_portfolio_blocks_position_side_drift(self):
        snapshot = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-position-side-drift",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
        )
        snapshot["positions"][0]["side"] = "SHORT"
        snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_paper_portfolio_detects_invalid_runtime_cycle_source(self):
        snapshot = build_initial_paper_portfolio_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio-source-cycle",
            source_runtime_cycle_id="",
        )
        snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_paper_portfolio_detects_invalid_source_ledger_head_hash(self):
        snapshot = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test-paper-portfolio-source-ledger",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
            source_runtime_cycle_id="portfolio-source-ledger-cycle",
            source_paper_ledger_head_hash="not-a-ledger-head-hash",
        )
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_paper_portfolio_blocks_unsupported_scope(self):
        snapshot = build_initial_paper_portfolio_snapshot(
            exchange="BINANCE",
            market_type="FUTURES_USDT_M",
            session_id="test-paper-portfolio-scope",
        )
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
