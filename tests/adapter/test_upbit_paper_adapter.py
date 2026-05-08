import unittest

from trader1.adapters.upbit.fee_model import build_upbit_fee_slippage_model
from trader1.adapters.upbit.market_data import (
    build_upbit_krw_market_symbols_from_rest_payload,
    build_upbit_public_market_data_fixture,
    build_upbit_public_ticker_snapshot_from_rest_payload,
    rank_upbit_krw_symbols_by_public_ticker,
    validate_upbit_public_market_data,
)
from trader1.adapters.upbit.paper_broker import build_upbit_paper_dry_run_report, validate_upbit_paper_dry_run_report
from trader1.adapters.upbit.symbol_rules import validate_upbit_krw_symbol


class UpbitPaperAdapterTest(unittest.TestCase):
    def test_public_market_data_fixture_is_paper_scoped(self):
        data = build_upbit_public_market_data_fixture(symbol="KRW-BTC", session_id="adapter-test")
        status, blocker, _ = validate_upbit_public_market_data(data, symbol="KRW-BTC", session_id="adapter-test")
        self.assertEqual(status, "PASS")
        self.assertIsNone(blocker)
        self.assertTrue(data["is_public"])
        self.assertFalse(data["private_account_fields_present"])

    def test_symbol_rule_accepts_krw_symbol_only(self):
        status, blocker, message = validate_upbit_krw_symbol("KRW-BTC")
        self.assertEqual(status, "PASS")
        self.assertIsNone(blocker)
        self.assertIn("UPBIT_KRW_SPOT_SYMBOL_RULE_V1", message)

        bad_status, bad_blocker, _ = validate_upbit_krw_symbol("BTC-USDT")
        self.assertEqual(bad_status, "BLOCKED")
        self.assertEqual(bad_blocker, "SYMBOL_RULE_UNVERIFIED")

    def test_symbol_rule_rejects_ambiguous_or_non_upbit_krw_symbols(self):
        blocked_symbols = [
            "KRW-btc",
            "KRW-",
            "KRW-KRW",
            "KRW-BTC-USDT",
            " KRW-BTC",
            "KRW-BTC ",
            "KRW-BTC/USD",
            "KRW-TOO-LONG-BASE",
        ]

        for symbol in blocked_symbols:
            with self.subTest(symbol=symbol):
                status, blocker, message = validate_upbit_krw_symbol(symbol)
                self.assertEqual(status, "BLOCKED")
                self.assertEqual(blocker, "SYMBOL_RULE_UNVERIFIED")
                self.assertNotIn("scaffold", message.lower())

    def test_fee_slippage_model_adapts_to_public_spread_and_liquidity(self):
        data = build_upbit_public_market_data_fixture(symbol="KRW-BTC", session_id="adapter-cost")
        model = build_upbit_fee_slippage_model(public_market_data=data)
        self.assertEqual(model["fee_model_status"], "PASS")
        self.assertEqual(model["slippage_model_status"], "PASS")
        self.assertEqual(model["slippage_bps"], "5")
        self.assertIn("spread_bps+min(25,5/volume_24h)", model["slippage_model_formula"])

        wide = dict(data)
        wide["best_ask"] = "1015000"
        wide["volume_24h"] = "0.5"
        wide_model = build_upbit_fee_slippage_model(public_market_data=wide)
        self.assertEqual(wide_model["slippage_model_status"], "PASS")
        self.assertGreater(float(wide_model["slippage_bps"]), float(model["slippage_bps"]))

    def test_fee_slippage_model_blocks_bad_public_inputs(self):
        data = build_upbit_public_market_data_fixture(symbol="KRW-BTC", session_id="adapter-cost-bad")
        data["best_ask"] = data["best_bid"]
        model = build_upbit_fee_slippage_model(public_market_data=data)
        self.assertEqual(model["fee_model_status"], "PASS")
        self.assertEqual(model["slippage_model_status"], "BLOCKED")

    def test_public_symbol_discovery_uses_strict_upbit_symbol_rule(self):
        payload = [
            {"market": "KRW-BTC"},
            {"market": "KRW-ETH"},
            {"market": "KRW-btc"},
            {"market": "KRW-"},
            {"market": "KRW-KRW"},
            {"market": "KRW-BTC-USDT"},
            {"market": "BTC-USDT"},
            {"market": " KRW-SOL"},
        ]
        symbols = build_upbit_krw_market_symbols_from_rest_payload(payload)
        self.assertEqual(symbols, ["KRW-BTC", "KRW-ETH"])

    def test_ticker_snapshot_and_ranking_skip_invalid_symbols(self):
        requested = ["KRW-BTC", "KRW-BTC-USDT", "KRW-btc", "KRW-ETH"]
        snapshot = build_upbit_public_ticker_snapshot_from_rest_payload(
            payload=[
                {"market": "KRW-BTC", "trade_price": "1000", "acc_trade_price_24h": "1000000000", "signed_change_rate": "0.02", "acc_trade_volume_24h": "100"},
                {"market": "KRW-BTC-USDT", "trade_price": "1000", "acc_trade_price_24h": "900000000", "signed_change_rate": "0.05", "acc_trade_volume_24h": "90"},
                {"market": "KRW-ETH", "trade_price": "900", "acc_trade_price_24h": "700000000", "signed_change_rate": "0.01", "acc_trade_volume_24h": "80"},
            ],
            requested_symbols=requested,
            session_id="adapter-ranking",
        )
        self.assertEqual(sorted(snapshot["ticker_by_symbol"]), ["KRW-BTC", "KRW-ETH"])
        ranking = rank_upbit_krw_symbols_by_public_ticker(
            symbols=requested,
            ticker_by_symbol=snapshot["ticker_by_symbol"],
            session_id="adapter-ranking",
        )
        self.assertEqual(ranking["input_symbol_count"], 2)
        self.assertNotIn("KRW-BTC-USDT", ranking["selected_symbols_for_candle_evaluation"])

    def test_paper_adapter_blocks_non_upbit_scope(self):
        report = build_upbit_paper_dry_run_report(
            paper_run_id="adapter-scope",
            exchange="BINANCE",
            market_type="SPOT",
        )
        result = validate_upbit_paper_dry_run_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
