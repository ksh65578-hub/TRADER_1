import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from trader1.config.config_schema import build_runtime_config
from trader1.runtime.health.heartbeat import build_heartbeat, heartbeat_hash, validate_heartbeat
from trader1.validation.mvp0_validators import run_validators, sha256_file, sha256_json


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


def build_safe_heartbeat(**kwargs):
    registry_hash, schema_bundle_hash, source_tree_hash = hashes()
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_heartbeat",
        registry_hash=registry_hash,
    )
    return build_heartbeat(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_heartbeat",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        **kwargs,
    )


class HeartbeatTest(unittest.TestCase):
    def test_heartbeat_is_dashboard_truth_only_and_non_trading(self):
        heartbeat = build_safe_heartbeat()
        result = validate_heartbeat(heartbeat, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        self.assertTrue(heartbeat["dashboard_truth_only"])
        self.assertFalse(heartbeat["can_trade"])
        self.assertFalse(heartbeat["live_order_ready"])
        self.assertFalse(heartbeat["live_order_allowed"])
        self.assertFalse(heartbeat["can_live_trade"])

    def test_live_permission_attempt_is_blocked(self):
        heartbeat = build_safe_heartbeat()
        heartbeat["live_order_allowed"] = True
        heartbeat["can_live_trade"] = True
        heartbeat["heartbeat_hash"] = heartbeat_hash(heartbeat)
        result = validate_heartbeat(heartbeat)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_stale_heartbeat_cannot_remain_pass(self):
        heartbeat = build_safe_heartbeat(stale_after_seconds=10)
        heartbeat["heartbeat_age_seconds"] = 11
        heartbeat["heartbeat_hash"] = heartbeat_hash(heartbeat)
        result = validate_heartbeat(heartbeat, now=datetime.now(timezone.utc))
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LATENCY_TTL_EXPIRED")

    def test_component_failure_cannot_remain_pass(self):
        heartbeat = build_safe_heartbeat()
        heartbeat["components"]["disk"]["status"] = "FAIL"
        heartbeat["components"]["disk"]["message"] = "disk full"
        heartbeat["heartbeat_hash"] = heartbeat_hash(heartbeat)
        result = validate_heartbeat(heartbeat)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RESOURCE_LIMIT")

    def test_heartbeat_validator_passes_current_contract(self):
        results = run_validators(["heartbeat_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()

