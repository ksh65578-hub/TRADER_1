import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.adapters.binance.surface import (
    binance_adapter_surface_hash,
    build_binance_adapter_surface_report,
    validate_binance_adapter_surface_report,
)
from trader1.runtime.boot.safe_launcher import (
    build_launcher_report,
    launcher_dashboard_paths,
    validate_launcher_report,
    write_launcher_dashboard,
)
from trader1.validation.mvp0_validators import run_validators


class BinanceAdapterSurfaceTest(unittest.TestCase):
    def test_binance_spot_paper_surface_is_explicitly_not_implemented(self):
        report = build_binance_adapter_surface_report(market_type="SPOT", mode="PAPER")
        result = validate_binance_adapter_surface_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["adapter_status"], "SURFACE_ONLY")
        self.assertEqual(report["paper_runtime_status"], "NOT_IMPLEMENTED")
        self.assertEqual(report["primary_blocker_code"], "BINANCE_ADAPTER_SURFACE_ONLY")
        self.assertFalse(report["public_market_data_supported"])
        self.assertFalse(report["paper_broker_supported"])
        self.assertFalse(report["order_adapter_called"])
        self.assertFalse(report["credentials_loaded"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_binance_futures_surface_remains_blocked_before_later_mvp(self):
        report = build_binance_adapter_surface_report(market_type="FUTURES_USDT_M", mode="PAPER")
        result = validate_binance_adapter_surface_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["adapter_status"], "BLOCKED")
        self.assertEqual(report["futures_runtime_status"], "NOT_IMPLEMENTED")
        self.assertEqual(report["primary_blocker_code"], "BINANCE_FUTURES_SURFACE_ONLY")
        self.assertFalse(report["futures_usdt_m_supported"])
        self.assertFalse(report["live_order_allowed"])

    def test_binance_surface_blocks_credential_and_live_mutations(self):
        report = build_binance_adapter_surface_report(market_type="SPOT", mode="PAPER")
        for field in ("credentials_loaded", "order_adapter_called", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            mutated = dict(report)
            mutated[field] = True
            mutated["report_hash"] = binance_adapter_surface_hash(mutated)
            result = validate_binance_adapter_surface_report(mutated)
            self.assertEqual(result.status, "BLOCKED", field)
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED", field)

    def test_binance_launcher_and_dashboard_expose_surface_only_blocker(self):
        report = build_launcher_report("BINANCE_PAPER")
        result = validate_launcher_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["blocking_reason"], "BINANCE_ADAPTER_SURFACE_ONLY")
        self.assertFalse(report["live_order_allowed"])

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            dashboard_paths = write_launcher_dashboard(report, root)
            summary = json.loads(dashboard_paths["summary"].read_text(encoding="utf-8"))
            shell = json.loads(dashboard_paths["dashboard_shell"].read_text(encoding="utf-8"))
            html = dashboard_paths["dashboard_html"].read_text(encoding="utf-8")

        self.assertEqual(summary["blocking_reason"], "BINANCE_ADAPTER_SURFACE_ONLY")
        self.assertEqual(summary["live_ready"]["primary_blocker_code"], "BINANCE_ADAPTER_SURFACE_ONLY")
        self.assertEqual(shell["blocking_reason"], "BINANCE_ADAPTER_SURFACE_ONLY")
        self.assertIn("BINANCE_ADAPTER_SURFACE_ONLY", html)
        self.assertIn("Binance SPOT is visible only as a surface", html)
        self.assertIn("mvp1_binance_paper_launcher", str(launcher_dashboard_paths(report)["dashboard_html"]))
        self.assertFalse(shell["live_order_allowed"])

    def test_binance_surface_validator_passes(self):
        results = run_validators(["binance_adapter_surface_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
