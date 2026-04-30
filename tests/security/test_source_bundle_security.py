import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.security.source_bundle import (
    build_source_bundle_manifest,
    classify_path,
    classify_shipped_forbidden_path,
    detect_credential_material,
    load_denylist,
)
from trader1.validation.mvp0_validators import run_validators


class SourceBundleSecurityTest(unittest.TestCase):
    def test_denylist_classifies_forbidden_paths(self):
        denylist = load_denylist()
        for path in [
            "system/evidence/example.json",
            "contracts/generated/current_implementation_state.json",
            "contracts/security/source_bundle_manifest.json",
            "logs/runtime.log",
            "__pycache__/module.pyc",
            ".env",
            "config/private.key",
            "contracts/security/token_dump.txt",
        ]:
            with self.subTest(path=path):
                self.assertFalse(classify_path(path, denylist).include)

    def test_manifest_candidate_is_fail_closed(self):
        manifest = build_source_bundle_manifest()
        self.assertFalse(manifest["live_order_ready"])
        self.assertFalse(manifest["live_order_allowed"])
        self.assertFalse(manifest["can_live_trade"])
        self.assertEqual(manifest["forbidden_count"], 0)
        self.assertEqual(manifest["shipped_forbidden_count"], 0)
        self.assertEqual(manifest["shipped_forbidden_files"], [])
        for item in manifest["included_files"]:
            self.assertNotIn("__pycache__/", item["path"])
            self.assertFalse(item["path"].startswith("system/"))
            self.assertFalse(item["path"].startswith("contracts/generated/"))
            self.assertNotEqual(item["path"], "contracts/security/source_bundle_manifest.json")
            self.assertFalse(item["path"].endswith(".pyc"))

    def test_manifest_includes_root_launchers_as_source_identity(self):
        manifest = build_source_bundle_manifest()
        included_paths = {item["path"] for item in manifest["included_files"]}
        for launcher in ("UPBIT_PAPER.py", "UPBIT_LIVE.py", "BINANCE_PAPER.py", "BINANCE_LIVE.py"):
            self.assertIn(launcher, included_paths)

    def test_shipped_package_forbidden_detection_catches_bytecode_cache(self):
        denylist = load_denylist()
        self.assertIsNotNone(classify_shipped_forbidden_path("trader1/__pycache__/module.cpython-314.pyc", denylist))
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "trader1" / "__pycache__").mkdir(parents=True)
            (root / "trader1" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "trader1" / "__pycache__" / "module.cpython-314.pyc").write_bytes(b"cache")
            manifest = build_source_bundle_manifest(root=root, denylist=denylist)
            self.assertEqual(manifest["shipped_forbidden_count"], 1)
            self.assertEqual(manifest["shipped_forbidden_files"][0]["path"], "trader1/__pycache__/module.cpython-314.pyc")

    def test_manifest_does_not_include_self_referential_generated_artifacts(self):
        manifest = build_source_bundle_manifest()
        included_paths = {item["path"] for item in manifest["included_files"]}
        self.assertNotIn("contracts/security/source_bundle_manifest.json", included_paths)
        self.assertNotIn("contracts/generated/current_implementation_state.json", included_paths)
        self.assertNotIn("contracts/generated/read_cache_manifest.json", included_paths)

    def test_secret_scan_detects_common_runtime_credential_shapes(self):
        cases = [
            ("aws_env_key", "AWS_" + "SECRET_" + "ACCESS_" + "KEY=" + ("A" * 32)),
            ("bearer_header", "Authorization: " + "Bearer " + ("b" * 48)),
            ("jwt_literal", "jwt=" + "eyJ" + ("c" * 20) + "." + ("d" * 20) + "." + ("e" * 20)),
        ]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name, text in cases:
                path = root / f"{name}.txt"
                path.write_text(text, encoding="utf-8")
                with self.subTest(name=name):
                    self.assertTrue(detect_credential_material(path))

    def test_bundle_security_validators_pass_current_candidate(self):
        statuses = {
            result["validator_id"]: result["status"]
            for result in run_validators(["source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator"])
        }
        self.assertEqual(statuses["source_bundle_hygiene_validator"], "PASS")
        self.assertEqual(statuses["shipped_package_hygiene_validator"], "PASS")
        self.assertEqual(statuses["secret_scan_validator"], "PASS")


if __name__ == "__main__":
    unittest.main()
