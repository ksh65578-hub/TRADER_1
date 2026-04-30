import unittest

from trader1.runtime.portfolio.paper_portfolio import (
    build_initial_paper_portfolio_snapshot,
    build_paper_portfolio_snapshot_from_fill,
    paper_portfolio_hash,
    validate_paper_portfolio_snapshot,
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
        self.assertEqual(snapshot["display_balance_kind"], "SIMULATED_PAPER_LEDGER")
        self.assertFalse(snapshot["live_order_ready"])
        self.assertFalse(snapshot["live_order_allowed"])
        self.assertFalse(snapshot["can_live_trade"])
        self.assertFalse(snapshot["can_submit_order"])

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
        )
        result = validate_paper_portfolio_snapshot(snapshot)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(snapshot["open_position_count"], 1)
        self.assertEqual(snapshot["positions"][0]["symbol"], "KRW-BTC")
        self.assertEqual(snapshot["position_market_value"], "10000")
        self.assertEqual(snapshot["unrealized_pnl"], "-10")
        self.assertEqual(snapshot["total_pnl"], "-10")
        self.assertEqual(snapshot["equity"], "999990")
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
