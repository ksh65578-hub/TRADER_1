import unittest

from trader1.adapters.upbit.market_data import build_upbit_public_market_data_fixture, validate_upbit_public_market_data
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
        status, blocker, _ = validate_upbit_krw_symbol("KRW-BTC")
        self.assertEqual(status, "PASS")
        self.assertIsNone(blocker)

        bad_status, bad_blocker, _ = validate_upbit_krw_symbol("BTC-USDT")
        self.assertEqual(bad_status, "BLOCKED")
        self.assertEqual(bad_blocker, "SYMBOL_RULE_UNVERIFIED")

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
