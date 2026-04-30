import tempfile
import unittest
from pathlib import Path

from trader1.runtime.boot.launcher_guard import ALLOWED_ROOT_LAUNCHERS, inspect_root_launchers
from trader1.runtime.boot.safe_launcher import build_launcher_report, validate_launcher_report
from trader1.validation.mvp0_validators import run_validators


SAFE_LAUNCHER = """
from trader1.runtime.readiness.readiness_surface import build_readiness_surface

market_type = "SPOT"
market_type_options = ("SPOT", "FUTURES_USDT_M")
futures_usdt_m_status = "BLOCKED_NOT_IMPLEMENTED"
live_order_ready = False
live_order_allowed = False
can_live_trade = False
"""


class RootLauncherGuardTest(unittest.TestCase):
    def test_current_repo_has_no_unexpected_root_launcher(self):
        result = inspect_root_launchers(Path(__file__).resolve().parents[2])
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.unexpected_root_launchers_found, [])
        self.assertFalse(result.live_order_ready)
        self.assertFalse(result.live_order_allowed)
        self.assertFalse(result.can_live_trade)

    def test_current_repo_exposes_exactly_four_allowed_launchers(self):
        result = inspect_root_launchers(Path(__file__).resolve().parents[2], require_exact_four=True)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(set(result.root_launchers_found), ALLOWED_ROOT_LAUNCHERS)

    def test_exact_four_allowed_launchers_pass_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for launcher in ALLOWED_ROOT_LAUNCHERS:
                (root / f"{launcher}.py").write_text(SAFE_LAUNCHER, encoding="utf-8")
            result = inspect_root_launchers(root, require_exact_four=True)
            self.assertEqual(result.status, "PASS")
            self.assertEqual(set(result.root_launchers_found), ALLOWED_ROOT_LAUNCHERS)

    def test_unexpected_dashboard_launcher_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dashboard_debug.py").write_text("print('debug')", encoding="utf-8")
            result = inspect_root_launchers(root)
            self.assertEqual(result.status, "BLOCKED")
            self.assertIn("dashboard_debug.py", result.unexpected_root_launchers_found)
            self.assertIn("CONTRACT_GAP_HIGH", result.blockers)

    def test_partial_allowed_launcher_surface_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "UPBIT_PAPER.py").write_text(SAFE_LAUNCHER, encoding="utf-8")
            result = inspect_root_launchers(root)
            self.assertEqual(result.status, "BLOCKED")
            self.assertIn("CONTRACT_GAP_HIGH", result.blockers)

    def test_paper_launcher_live_order_reference_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "UPBIT_PAPER.py").write_text("submit_live_order()\nmarket_type = 'KRW_SPOT'\n", encoding="utf-8")
            for launcher in ["UPBIT_LIVE", "BINANCE_PAPER", "BINANCE_LIVE"]:
                (root / f"{launcher}.py").write_text(SAFE_LAUNCHER, encoding="utf-8")
            result = inspect_root_launchers(root)
            self.assertEqual(result.status, "BLOCKED")
            self.assertTrue(result.live_order_path_found)
            self.assertIn("LIVE_FINAL_GUARD_FAILED", result.blockers)

    def test_binance_launcher_missing_market_type_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for launcher in ["UPBIT_PAPER", "UPBIT_LIVE", "BINANCE_LIVE"]:
                (root / f"{launcher}.py").write_text(SAFE_LAUNCHER, encoding="utf-8")
            (root / "BINANCE_PAPER.py").write_text("live_order_allowed = False\n", encoding="utf-8")
            result = inspect_root_launchers(root)
            self.assertEqual(result.status, "BLOCKED")
            self.assertIn("LIVE_FINAL_GUARD_FAILED", result.blockers)

    def test_binance_spot_only_market_type_disclosure_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for launcher in ["UPBIT_PAPER", "UPBIT_LIVE", "BINANCE_LIVE"]:
                (root / f"{launcher}.py").write_text(SAFE_LAUNCHER, encoding="utf-8")
            (root / "BINANCE_PAPER.py").write_text('market_type = "SPOT"\nlive_order_allowed = False\n', encoding="utf-8")
            result = inspect_root_launchers(root)
            self.assertEqual(result.status, "BLOCKED")
            self.assertIn("LIVE_FINAL_GUARD_FAILED", result.blockers)
            issues = [issue for finding in result.findings for issue in finding.issues]
            self.assertIn("binance launcher must disclose both SPOT and FUTURES_USDT_M market_type boundary", issues)

    def test_root_launcher_guard_validator_passes_current_repo(self):
        results = run_validators(["root_launcher_guard_validator", "root_launcher_surface_validator"])
        self.assertTrue(all(result["status"] == "PASS" for result in results))

    def test_safe_launcher_reports_are_fail_closed(self):
        for launcher_name in ALLOWED_ROOT_LAUNCHERS:
            report = build_launcher_report(launcher_name)
            result = validate_launcher_report(report)
            self.assertEqual(result.status, "PASS", launcher_name)
            self.assertFalse(report["live_order_ready"])
            self.assertFalse(report["live_order_allowed"])
            self.assertFalse(report["can_live_trade"])
            self.assertTrue(report["live_path_hard_blocked"])


if __name__ == "__main__":
    unittest.main()
