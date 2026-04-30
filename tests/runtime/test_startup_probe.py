import json
import unittest
from pathlib import Path

from trader1.config.config_schema import build_runtime_config
from trader1.runtime.boot.startup_probe import build_startup_probe, startup_probe_hash, validate_startup_probe
from trader1.validation.mvp0_validators import sha256_file, sha256_json, run_validators


ROOT = Path(__file__).resolve().parents[2]


def registry():
    return json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))


def hashes():
    registry_hash = sha256_file(ROOT / "contracts" / "registry.yaml")
    schema_bundle_hash = sha256_json(
        {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))}
    )
    source_tree_hash = sha256_json(
        {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted((ROOT / "trader1").rglob("*.py")) if "__pycache__" not in path.parts}
    )
    return registry_hash, schema_bundle_hash, source_tree_hash


def build_probe(ledger_write_status=None, can_start=False):
    registry_hash, schema_bundle_hash, source_tree_hash = hashes()
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_startup_probe",
        registry_hash=registry_hash,
    )
    return build_startup_probe(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_startup_probe",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        ledger_write_status=ledger_write_status,
        can_start=can_start,
    )


class StartupProbeTest(unittest.TestCase):
    def test_missing_hard_truth_blocks_startup_and_trade(self):
        probe = build_probe(ledger_write_status=None)
        result = validate_startup_probe(probe, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        self.assertFalse(probe["startup_probe_passed"])
        self.assertFalse(probe["can_trade"])
        self.assertFalse(probe["live_order_allowed"])
        self.assertEqual(probe["primary_blocker_code"], "HARD_TRUTH_MISSING")

    def test_startup_probe_is_dashboard_truth_only(self):
        probe = build_probe(ledger_write_status=None)
        probe["dashboard_truth_only"] = False
        probe["probe_hash"] = startup_probe_hash(probe)
        result = validate_startup_probe(probe)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_running_before_startup_pass_is_blocked(self):
        probe = build_probe(ledger_write_status=None)
        probe["engine_state_after_probe"] = "RUNNING"
        probe["probe_hash"] = startup_probe_hash(probe)
        result = validate_startup_probe(probe)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "PREFLIGHT_FAILED")

    def test_startup_pass_does_not_create_trading_permission(self):
        probe = build_probe(ledger_write_status="PASS", can_start=True)
        result = validate_startup_probe(probe)
        self.assertEqual(result.status, "PASS")
        self.assertTrue(probe["startup_probe_passed"])
        self.assertTrue(probe["can_start"])
        self.assertFalse(probe["can_trade"])
        self.assertFalse(probe["live_order_allowed"])

    def test_startup_probe_validator_passes_current_contract(self):
        results = run_validators(["startup_probe_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
