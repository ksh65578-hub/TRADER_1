import json
import unittest
from pathlib import Path

from trader1.adapters.upbit.market_data import build_upbit_public_market_data_fixture
from trader1.adapters.upbit.paper_broker import (
    build_upbit_paper_dry_run_report,
    upbit_paper_dry_run_hash,
    validate_upbit_paper_dry_run_report,
)
from trader1.validation.mvp0_validators import run_validators


ROOT = Path(__file__).resolve().parents[2]


def registry():
    return json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))


def allowed_blockers():
    return set(registry()["enums"]["live_blocker_code"]["values"])


class UpbitPaperDryRunTest(unittest.TestCase):
    def test_entry_dry_run_writes_paper_ledger_without_live_permission(self):
        report = build_upbit_paper_dry_run_report(paper_run_id="paper-entry")
        result = validate_upbit_paper_dry_run_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "ENTER_LONG")
        self.assertTrue(report["paper_order_submitted"])
        self.assertEqual(report["paper_ledger_write_status"], "WRITTEN")
        self.assertTrue(report["paper_ledger_events"])
        symbol_reason = next(item for item in report["entry_reasons"] if item["reason_code"] == "SYMBOL_RULE_PASS")
        self.assertIn("UPBIT_KRW_SPOT_SYMBOL_RULE_V1", symbol_reason["message"])
        self.assertNotIn("scaffold", symbol_reason["message"].lower())
        cost_reason = next(item for item in report["entry_reasons"] if item["reason_code"] == "FEE_SLIPPAGE_MODEL_PASS")
        self.assertIn("public bid/ask spread", cost_reason["message"])
        self.assertEqual(report["fee_rate"], "0.0005")
        self.assertEqual(report["slippage_bps"], "5")
        self.assertFalse(report["live_key_loaded"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["can_submit_order"])
        self.assertFalse(report["order_adapter_called"])

    def test_no_trade_dry_run_logs_no_trade_reason(self):
        report = build_upbit_paper_dry_run_report(paper_run_id="paper-no-trade", requested_entry=False)
        result = validate_upbit_paper_dry_run_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["final_decision"], "NO_TRADE")
        self.assertEqual(report["paper_ledger_write_status"], "SKIPPED_NO_TRADE")
        self.assertIn("MIN_EDGE_FAIL", report["no_trade_reasons"])

    def test_bad_symbol_blocks_and_logs_reason(self):
        report = build_upbit_paper_dry_run_report(paper_run_id="paper-bad-symbol", symbol="BTC-USDT")
        result = validate_upbit_paper_dry_run_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["paper_broker_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "SYMBOL_RULE_UNVERIFIED")
        self.assertIn("SYMBOL_RULE_UNVERIFIED", report["no_trade_reasons"])

    def test_public_private_data_mixing_blocks(self):
        data = build_upbit_public_market_data_fixture(symbol="KRW-BTC", session_id="mvp2_upbit_paper")
        data["private_account_fields_present"] = True
        report = build_upbit_paper_dry_run_report(paper_run_id="paper-private-data", public_market_data=data)
        result = validate_upbit_paper_dry_run_report(report, allowed_blockers())
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_bad_fee_or_slippage_inputs_block_entry(self):
        bad_fee = build_upbit_paper_dry_run_report(paper_run_id="paper-bad-fee", fee_rate="0.01")
        bad_fee_result = validate_upbit_paper_dry_run_report(bad_fee, allowed_blockers())
        self.assertEqual(bad_fee_result.status, "BLOCKED")
        self.assertEqual(bad_fee["primary_blocker_code"], "FEE_MODEL_UNVERIFIED")

        data = build_upbit_public_market_data_fixture(symbol="KRW-BTC", session_id="mvp2_upbit_paper")
        data["volume_24h"] = "0"
        bad_slippage = build_upbit_paper_dry_run_report(paper_run_id="paper-bad-slippage", public_market_data=data)
        bad_slippage_result = validate_upbit_paper_dry_run_report(bad_slippage, allowed_blockers())
        self.assertEqual(bad_slippage_result.status, "BLOCKED")
        self.assertEqual(bad_slippage["primary_blocker_code"], "MEASUREMENT_MISSING")

    def test_slippage_tamper_below_public_minimum_fails(self):
        data = build_upbit_public_market_data_fixture(symbol="KRW-BTC", session_id="mvp2_upbit_paper")
        data["best_ask"] = "1015000"
        report = build_upbit_paper_dry_run_report(paper_run_id="paper-slippage-tamper", public_market_data=data)
        report["slippage_bps"] = "0.25"
        report["dry_run_hash"] = upbit_paper_dry_run_hash(report)
        result = validate_upbit_paper_dry_run_report(report, allowed_blockers())
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_live_permission_mutation_is_blocked(self):
        report = build_upbit_paper_dry_run_report(paper_run_id="paper-live")
        report["live_order_allowed"] = True
        report["can_live_trade"] = True
        report["can_submit_order"] = True
        report["dry_run_hash"] = upbit_paper_dry_run_hash(report)
        result = validate_upbit_paper_dry_run_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_live_adapter_call_mutation_is_blocked(self):
        report = build_upbit_paper_dry_run_report(paper_run_id="paper-adapter")
        report["order_adapter_called"] = True
        report["dry_run_hash"] = upbit_paper_dry_run_hash(report)
        result = validate_upbit_paper_dry_run_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_strategy_promotion_mutation_is_blocked(self):
        report = build_upbit_paper_dry_run_report(paper_run_id="paper-promotion")
        report["strategy_promotion_attempted"] = True
        report["dry_run_hash"] = upbit_paper_dry_run_hash(report)
        result = validate_upbit_paper_dry_run_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_hash_tamper_fails(self):
        report = build_upbit_paper_dry_run_report(paper_run_id="paper-tamper")
        report["symbol"] = "KRW-ETH"
        result = validate_upbit_paper_dry_run_report(report)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_upbit_paper_dry_run_validator_passes_current_contract(self):
        results = run_validators(["upbit_paper_dry_run_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
