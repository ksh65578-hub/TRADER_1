import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.validation.bytecode_free_syntax import (
    build_bytecode_free_syntax_report,
    validate_bytecode_free_syntax_report,
)
from trader1.validation.mvp0_validators import run_validators
from trader1.validation.schema_instance import load_schema_bundle, schema_for_instance, validate_instance_against_schema


ROOT = Path(__file__).resolve().parents[2]


class BytecodeFreeSyntaxCheckTest(unittest.TestCase):
    def test_current_repo_syntax_check_does_not_require_pycache_writes(self):
        report = build_bytecode_free_syntax_report(root=ROOT, scan_paths=["trader1", "tools", "tests"])
        result = validate_bytecode_free_syntax_report(report)
        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["status"], "PASS")
        self.assertGreater(report["files_checked"], 0)
        self.assertFalse(report["bytecode_write_attempted"])
        self.assertFalse(report["pycache_write_attempted"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)
        self.assertIsNotNone(schema)
        schema_result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(schema_result.status, "PASS", schema_result.errors)

    def test_temp_syntax_check_creates_no_pycache_directory(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "sample"
            package.mkdir()
            source = package / "module.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")

            report = build_bytecode_free_syntax_report(root=root, scan_paths=["sample"])
            result = validate_bytecode_free_syntax_report(report)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertFalse((package / "__pycache__").exists())
            self.assertFalse(report["pycache_write_attempted"])

    def test_cli_writes_reproducible_report_without_bytecode(self):
        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "bytecode_free_syntax_report.json"
            result = subprocess.run(
                [sys.executable, "tools/run_bytecode_free_syntax_check.py", "--output", str(output_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertFalse(report["bytecode_write_attempted"])
            self.assertFalse(report["pycache_write_attempted"])
            self.assertFalse(report["live_order_api_attempted"])

    def test_registered_validator_passes_current_repo(self):
        statuses = {result["validator_id"]: result["status"] for result in run_validators(["bytecode_free_syntax_validator"])}
        self.assertEqual(statuses["bytecode_free_syntax_validator"], "PASS")


if __name__ == "__main__":
    unittest.main()
