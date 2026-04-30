import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.smoke import SAFE_SMOKE_VALIDATORS, run_safe_smoke
from trader1.validation.schema_instance import load_schema_bundle, schema_for_instance, validate_instance_against_schema


ROOT = Path(__file__).resolve().parents[2]


class SafeSmokeTest(unittest.TestCase):
    def test_safe_smoke_builds_temp_runtime_bundles_and_blocks_live(self):
        report = run_safe_smoke(include_validators=True)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["root_launchers_checked"], 4)
        self.assertEqual(report["temporary_runtime_bundles_checked"], 4)
        self.assertEqual(report["validators_requested"], SAFE_SMOKE_VALIDATORS)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(report["external_calls_attempted"])
        self.assertFalse(report["credential_load_attempted"])
        self.assertFalse(report["live_order_api_attempted"])
        self.assertTrue(all(item["live_flags_false"] for item in report["runtime_bundle_checks"]))
        self.assertTrue(all(item["paths_are_session_scoped"] for item in report["runtime_bundle_checks"]))
        self.assertTrue(all(item["dashboard_display_truth_only"] for item in report["runtime_bundle_checks"]))
        self.assertTrue(all(item["final_action"] == "NO_TRADE" for item in report["runtime_bundle_checks"]))
        self.assertTrue(all(result["status"] == "PASS" for result in report["validators_run"]))
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)
        self.assertIsNotNone(schema)
        schema_result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(schema_result.status, "PASS", schema_result.errors)

    def test_safe_smoke_cli_writes_reproducible_json_report(self):
        with TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "safe_smoke_report.json"
            result = subprocess.run(
                [sys.executable, "tools/run_safe_smoke.py", "--output", str(output_path)],
                cwd=ROOT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                text=True,
                capture_output=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_path.exists())
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["zip_reproducibility_status"], "PASS")
            self.assertEqual(report["root_launchers_checked"], 4)
            self.assertFalse(report["live_order_allowed"])
            self.assertFalse(report["can_live_trade"])


if __name__ == "__main__":
    unittest.main()
