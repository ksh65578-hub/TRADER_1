import unittest

from tools.run_bundle_security_validators import VALIDATORS as BUNDLE_SECURITY_VALIDATORS
from tools.run_source_release_proof_profile import (
    PROFILE_ID,
    build_source_release_proof_profile_report,
    default_release_profile_commands,
)
from trader1.validation.schema_instance import load_schema_bundle, schema_for_instance, validate_instance_against_schema

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def clean_manifest_summary() -> dict:
    return {
        "included_count": 10,
        "excluded_count": 2,
        "forbidden_count": 0,
        "shipped_forbidden_count": 0,
        "contains_secret": False,
        "repo_secret_findings_count": 0,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }


def pass_command(name: str = "python -B tool.py") -> dict:
    return {
        "command": name,
        "status": "PASS",
        "returncode": 0,
        "duration_ms": 1,
        "stdout_tail": "",
        "stderr_tail": "",
    }


class SourceReleaseProofProfileTest(unittest.TestCase):
    def test_report_passes_schema_and_keeps_live_flags_false(self):
        report = build_source_release_proof_profile_report(
            command_results=[pass_command()],
            preexisting_cache_artifacts=[],
            post_run_cache_artifacts=[],
            manifest_summary=clean_manifest_summary(),
            created_at_utc="2026-05-02T00:00:00Z",
        )

        self.assertEqual(report["schema_id"], "trader1.source_release_proof_profile_report.v1")
        self.assertEqual(report["profile_id"], PROFILE_ID)
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)
        self.assertIsNotNone(schema)
        schema_result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(schema_result.status, "PASS", schema_result.errors)

    def test_report_blocks_cache_artifacts_failed_commands_and_live_flag_drift(self):
        manifest = clean_manifest_summary()
        manifest["live_order_allowed"] = True
        report = build_source_release_proof_profile_report(
            command_results=[{**pass_command(), "status": "FAIL", "returncode": 1}],
            preexisting_cache_artifacts=[{"path": "__pycache__", "reason": "forbidden_directory:__pycache__"}],
            post_run_cache_artifacts=[{"path": "tests/.pytest_cache", "reason": "forbidden_directory:.pytest_cache"}],
            manifest_summary=manifest,
            created_at_utc="2026-05-02T00:00:00Z",
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("RELEASE_PROOF_COMMAND_FAILED", report["blockers"])
        self.assertIn("PREEXISTING_CACHE_ARTIFACTS", report["blockers"])
        self.assertIn("POST_RUN_CACHE_ARTIFACTS", report["blockers"])
        self.assertIn("LIVE_FLAG_DRIFT", report["blockers"])
        self.assertFalse(report["live_order_allowed"])

    def test_default_profile_commands_cover_release_proof_requirements(self):
        commands = [" ".join(command) for command in default_release_profile_commands(python_executable="python")]
        joined = "\n".join(commands)

        self.assertIn("tools/run_hygiene_safe_pytest.py", joined)
        self.assertIn("tests/security/test_source_bundle_security.py", joined)
        self.assertIn("tools/build_source_bundle_manifest.py", joined)
        self.assertIn("tools/run_bundle_security_validators.py", joined)
        self.assertIn("tools/run_patch_result_runtime_schema_validators.py", joined)
        self.assertIn("tools/run_runtime_schema_instance_validators.py", joined)
        self.assertIn("tools/run_live_final_guard_validators.py", joined)
        self.assertIn("tools/run_bytecode_free_syntax_check.py", joined)

    def test_bundle_security_profile_includes_shipped_package_hygiene(self):
        self.assertIn("source_bundle_hygiene_validator", BUNDLE_SECURITY_VALIDATORS)
        self.assertIn("shipped_package_hygiene_validator", BUNDLE_SECURITY_VALIDATORS)
        self.assertIn("secret_scan_validator", BUNDLE_SECURITY_VALIDATORS)


if __name__ == "__main__":
    unittest.main()
