import json
import unittest
from pathlib import Path

from trader1.reports.no_trade_reason import NO_TRADE_REASONS, build_no_trade_reason


ROOT = Path(__file__).resolve().parents[2]


class NoTradeReasonEnumTest(unittest.TestCase):
    def test_no_trade_reasons_are_registered_blockers(self):
        registry = json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))
        registered = set(registry["enums"]["no_trade_reason"]["values"])
        self.assertTrue(NO_TRADE_REASONS.issubset(registered))

    def test_unknown_no_trade_reason_fails_closed(self):
        reason = build_no_trade_reason("NOT_REGISTERED", "unknown reason")
        self.assertEqual(reason["code"], "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
