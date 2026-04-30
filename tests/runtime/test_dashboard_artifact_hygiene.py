from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trader1.runtime.artifact_hygiene import (
    ACTIVE_DASHBOARD_SHELLS,
    build_runtime_dashboard_artifact_hygiene_report,
    validate_runtime_dashboard_artifact_hygiene_report,
)
from trader1.validation.mvp0_validators import runtime_dashboard_artifact_hygiene_validator


class RuntimeDashboardArtifactHygieneTest(unittest.TestCase):
    def test_current_runtime_dashboard_shells_are_classified(self) -> None:
        report = build_runtime_dashboard_artifact_hygiene_report()
        result = validate_runtime_dashboard_artifact_hygiene_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["unknown_count"], 0)
        self.assertEqual(report["active_count"], 4)
        self.assertEqual(report["legacy_retained_count"], 1)
        self.assertEqual(report["live_order_ready"], False)
        self.assertEqual(report["live_order_allowed"], False)
        self.assertEqual(report["can_live_trade"], False)
        self.assertEqual(report["scale_up_allowed"], False)

        legacy_paths = {item["artifact_path"] for item in report["legacy_retained_dashboard_shells"]}
        self.assertIn("system/runtime/upbit/krw_spot/paper/dashboard_shell.json", legacy_paths)
        for item in report["legacy_retained_dashboard_shells"]:
            self.assertEqual(item["classification"], "LEGACY_UNSESSIONED_RETAINED")
            self.assertEqual(item["execution_authority"], False)
            self.assertEqual(item["dashboard_serving_truth"], False)

    def test_validator_passes_for_current_repo(self) -> None:
        result = runtime_dashboard_artifact_hygiene_validator()
        self.assertEqual(result.status, "PASS")
        self.assertIn("legacy unscoped shells", result.message)

    def test_unscoped_legacy_live_flag_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            legacy_path = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "dashboard_shell.json"
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_path.write_text(
                json.dumps(
                    {
                        "schema_id": "trader1.read_only_dashboard_shell.v1",
                        "exchange": "UPBIT",
                        "market_type": "KRW_SPOT",
                        "mode": "PAPER",
                        "session_id": "",
                        "live_order_ready": False,
                        "live_order_allowed": True,
                        "can_live_trade": False,
                        "scale_up_allowed": False,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            report = build_runtime_dashboard_artifact_hygiene_report(root, active_dashboard_shells=set())
            result = validate_runtime_dashboard_artifact_hygiene_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("LEGACY_UNSAFE_PATHS_NON_EMPTY", result.blocking_reasons)

    def test_unrecognized_dashboard_shell_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            unknown_path = (
                root
                / "system"
                / "runtime"
                / "upbit"
                / "krw_spot"
                / "paper"
                / "custom_session"
                / "nested"
                / "dashboard_shell.json"
            )
            unknown_path.parent.mkdir(parents=True, exist_ok=True)
            unknown_path.write_text(
                json.dumps(
                    {
                        "schema_id": "trader1.read_only_dashboard_shell.v1",
                        "exchange": "UPBIT",
                        "market_type": "KRW_SPOT",
                        "mode": "PAPER",
                        "session_id": "custom_session",
                        "live_order_ready": False,
                        "live_order_allowed": False,
                        "can_live_trade": False,
                        "scale_up_allowed": False,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            report = build_runtime_dashboard_artifact_hygiene_report(root, active_dashboard_shells=ACTIVE_DASHBOARD_SHELLS)
            result = validate_runtime_dashboard_artifact_hygiene_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("UNKNOWN_DASHBOARD_SHELL_ARTIFACT_PRESENT", result.blocking_reasons)


if __name__ == "__main__":
    unittest.main()
