import json
import unittest
from pathlib import Path

from trader1.config.config_schema import (
    attach_config_hash,
    build_runtime_config,
    validate_runtime_config,
)
from trader1.validation.mvp0_validators import sha256_file, run_validators


ROOT = Path(__file__).resolve().parents[2]


def registry():
    return json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))


def registry_hash():
    return sha256_file(ROOT / "contracts" / "registry.yaml")


class RuntimeConfigValidationTest(unittest.TestCase):
    def test_upbit_paper_config_passes_fail_closed(self):
        config = build_runtime_config(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_upbit_paper",
            registry_hash=registry_hash(),
        )
        result = validate_runtime_config(config, registry(), expected_registry_hash=registry_hash())
        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.live_order_ready)
        self.assertFalse(result.live_order_allowed)
        self.assertFalse(result.can_live_trade)

    def test_binance_config_requires_explicit_market_type_source(self):
        config = build_runtime_config(
            exchange="BINANCE",
            market_type="SPOT",
            mode="PAPER",
            session_id="test_binance_paper",
            registry_hash=registry_hash(),
            market_type_source="SAFE_CONFIG_SCHEMA",
        )
        self.assertEqual(validate_runtime_config(config, registry(), expected_registry_hash=registry_hash()).status, "PASS")

        missing_source = dict(config)
        missing_source["market_type_source"] = "NOT_APPLICABLE"
        missing_source = attach_config_hash(missing_source)
        blocked = validate_runtime_config(missing_source, registry(), expected_registry_hash=registry_hash())
        self.assertEqual(blocked.status, "BLOCKED")
        self.assertEqual(blocked.primary_blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_upbit_wrong_market_type_blocks(self):
        config = build_runtime_config(
            exchange="UPBIT",
            market_type="SPOT",
            mode="PAPER",
            session_id="test_bad_market",
            registry_hash=registry_hash(),
        )
        blocked = validate_runtime_config(config, registry(), expected_registry_hash=registry_hash())
        self.assertEqual(blocked.status, "BLOCKED")
        self.assertEqual(blocked.primary_blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_live_capability_flags_block(self):
        config = build_runtime_config(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="LIVE",
            session_id="test_live_blocked",
            registry_hash=registry_hash(),
        )
        config["allow_live_credentials"] = True
        config = attach_config_hash(config)
        blocked = validate_runtime_config(config, registry(), expected_registry_hash=registry_hash())
        self.assertEqual(blocked.status, "BLOCKED")
        self.assertEqual(blocked.primary_blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_missing_hard_truth_blocks(self):
        config = build_runtime_config(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_missing_truth",
            registry_hash=registry_hash(),
        )
        config.pop("session_id")
        blocked = validate_runtime_config(config, registry(), expected_registry_hash=registry_hash())
        self.assertEqual(blocked.status, "BLOCKED")
        self.assertEqual(blocked.primary_blocker_code, "HARD_TRUTH_MISSING")

    def test_runtime_config_validator_passes_current_contract(self):
        results = run_validators(["runtime_config_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
