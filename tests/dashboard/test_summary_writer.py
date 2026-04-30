import json
import unittest
from pathlib import Path

from trader1.config.config_schema import build_runtime_config
from trader1.dashboard.summary_writer import build_summary_shell, validate_summary_shell
from trader1.runtime.boot.startup_probe import build_startup_probe
from trader1.runtime.health.heartbeat import build_heartbeat
from trader1.runtime.portfolio.paper_portfolio import build_initial_paper_portfolio_snapshot
from trader1.runtime.readiness.readiness_surface import build_readiness_surface
from trader1.validation.mvp0_validators import current_authority_hashes, run_validators, sha256_file, sha256_json


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


def build_summary(with_paper_portfolio=False):
    registry_hash, schema_bundle_hash, source_tree_hash = hashes()
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_summary_shell",
        registry_hash=registry_hash,
    )
    startup_probe = build_startup_probe(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_summary_shell",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        ledger_write_status=None,
    )
    heartbeat = build_heartbeat(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_summary_shell",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    readiness_surface = build_readiness_surface(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_summary_shell",
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    paper_portfolio = (
        build_initial_paper_portfolio_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test_summary_shell",
        )
        if with_paper_portfolio
        else None
    )
    return build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_summary_shell",
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
        paper_portfolio_snapshot=paper_portfolio,
    )


class SummaryWriterTest(unittest.TestCase):
    def test_summary_shell_is_dashboard_only_and_live_blocked(self):
        summary = build_summary()
        result = validate_summary_shell(summary, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        self.assertEqual(summary["schema_id"], "trader1.summary.v1")
        self.assertFalse(summary["live_ready"]["live_order_ready"])
        self.assertFalse(summary["live_ready"]["live_order_allowed"])
        self.assertEqual(summary["final_action"], "NO_TRADE")

    def test_summary_shell_cannot_emit_order_action(self):
        summary = build_summary()
        summary["final_action"] = "ENTER_LONG"
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_summary_shell_cannot_create_live_readiness(self):
        summary = build_summary()
        summary["live_ready"]["live_order_ready"] = True
        summary["live_ready"]["live_order_allowed"] = True
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_summary_builder_cannot_invent_portfolio_truth(self):
        summary = build_summary()
        summary["portfolio"]["equity"] = 1000.0
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_summary_accepts_scoped_paper_portfolio_snapshot(self):
        summary = build_summary(with_paper_portfolio=True)
        result = validate_summary_shell(summary, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        self.assertEqual(summary["portfolio"]["source"], "LEDGER")
        self.assertEqual(summary["portfolio"]["freshness_status"], "PASS")
        self.assertEqual(summary["portfolio"]["source_snapshot_status"], "PASS")
        self.assertEqual(len(summary["portfolio"]["source_snapshot_hash"]), 64)
        self.assertEqual(summary["portfolio"]["source_balance_kind"], "SIMULATED_PAPER_LEDGER")
        self.assertEqual(summary["portfolio"]["cash_available"], 1000000.0)
        self.assertEqual(summary["portfolio"]["equity"], 1000000.0)
        self.assertEqual(summary["positions"], [])

    def test_summary_blocks_verified_portfolio_without_snapshot_provenance(self):
        summary = build_summary(with_paper_portfolio=True)
        summary["portfolio"]["source_snapshot_hash"] = None
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_summary_blocks_verified_portfolio_arithmetic_drift(self):
        summary = build_summary(with_paper_portfolio=True)
        summary["portfolio"]["equity"] = summary["portfolio"]["equity"] + 1.0
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_summary_blocks_verified_portfolio_outside_paper(self):
        summary = build_summary(with_paper_portfolio=True)
        summary["mode"] = "LIVE"
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_summary_shell_validator_passes_current_contract(self):
        results = run_validators(["summary_shell_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
