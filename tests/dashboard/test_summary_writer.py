import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trader1.adapters.upbit.market_data import (
    UPBIT_PUBLIC_CANDLE_HOST,
    UPBIT_PUBLIC_CANDLE_PATH,
    build_upbit_public_candle_fixture,
)
from trader1.config.config_schema import build_runtime_config
from trader1.dashboard.summary_writer import build_summary_shell, validate_summary_shell
from trader1.runtime.boot.startup_probe import build_startup_probe
from trader1.runtime.health.heartbeat import build_heartbeat
from trader1.runtime.paper.upbit_public_collector import build_upbit_public_market_data_collection_report
from trader1.runtime.portfolio.paper_portfolio import (
    build_initial_paper_portfolio_snapshot,
    build_paper_portfolio_snapshot_from_fill,
    mark_paper_portfolio_snapshot_to_public_market,
    paper_portfolio_hash,
)
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


def build_summary(with_paper_portfolio=False, paper_portfolio_snapshot=None):
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
    paper_portfolio = paper_portfolio_snapshot or (
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


def stale_paper_portfolio(snapshot, seconds_old=3600):
    stale = json.loads(json.dumps(snapshot))
    generated_at = datetime.now(timezone.utc) - timedelta(seconds=seconds_old)
    stale["generated_at_utc"] = generated_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    stale["snapshot_hash"] = paper_portfolio_hash(stale)
    return stale


def public_rest_collection(symbol="KRW-BTC", session_id="test_summary_shell"):
    market_data = build_upbit_public_candle_fixture(symbol=symbol, session_id=session_id)
    market_data.update(
        {
            "source": "PUBLIC_REST_READ_ONLY",
            "profile": "PUBLIC_REST_READ_ONLY_1M_CANDLES",
            "public_endpoint_host": UPBIT_PUBLIC_CANDLE_HOST,
            "public_endpoint_path": UPBIT_PUBLIC_CANDLE_PATH,
            "raw_payload_private_fields_present": False,
            "credential_load_attempted": False,
            "authorization_header_present": False,
            "private_endpoint_called": False,
            "order_endpoint_called": False,
        }
    )
    return build_upbit_public_market_data_collection_report(
        collector_id="summary-public-mark",
        session_id=session_id,
        symbol=symbol,
        market_data=market_data,
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

    def test_summary_binds_quantitative_policy_for_dashboard_without_live_permission(self):
        summary = build_summary()
        result = validate_summary_shell(summary, set(registry()["enums"]["live_blocker_code"]["values"]))

        policy = summary["quantitative_policy_summary"]
        self.assertEqual(result.status, "PASS")
        self.assertEqual(policy["source"], "QUANTITATIVE_POLICY_REPORT")
        self.assertEqual(policy["policy_status"], "IMPLEMENTED_LIVE_BLOCKED")
        self.assertEqual(policy["decision_surface"], "DASHBOARD_ONLY")
        self.assertEqual(policy["dashboard_reason_code"], "LIVE_READY_MISSING")
        self.assertEqual(policy["minimum_trade_count"], 100)
        self.assertEqual(policy["high_return_candidate_trade_count"], 300)
        self.assertEqual(len(policy["source_policy_report_hash"]), 64)
        self.assertFalse(policy["live_order_ready"])
        self.assertFalse(policy["live_order_allowed"])
        self.assertFalse(policy["can_live_trade"])
        self.assertFalse(policy["scale_up_allowed"])

    def test_summary_blocks_quantitative_policy_live_flag_drift(self):
        summary = build_summary()
        summary["quantitative_policy_summary"]["live_order_allowed"] = True

        result = validate_summary_shell(summary)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_summary_keeps_binance_quantitative_policy_scaffold_only(self):
        summary = build_summary_shell(
            exchange="BINANCE",
            market_type="SPOT",
            mode="PAPER",
            session_id="test_summary_binance_scaffold",
            startup_probe=None,
            heartbeat=None,
            readiness_surface=None,
        )
        result = validate_summary_shell(summary, set(registry()["enums"]["live_blocker_code"]["values"]))

        policy = summary["quantitative_policy_summary"]
        self.assertEqual(result.status, "PASS")
        self.assertEqual(policy["source"], "SUMMARY_BUILDER")
        self.assertEqual(policy["policy_status"], "BLOCKED")
        self.assertEqual(policy["dashboard_reason_code"], "BINANCE_ADAPTER_SURFACE_ONLY")
        self.assertFalse(policy["live_order_allowed"])
        self.assertFalse(policy["can_live_trade"])

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

    def test_summary_shows_configured_paper_capital_without_verifying_portfolio(self):
        summary = build_summary()
        result = validate_summary_shell(summary, set(registry()["enums"]["live_blocker_code"]["values"]))
        portfolio = summary["portfolio"]
        self.assertEqual(result.status, "PASS")
        self.assertEqual(portfolio["source"], "SUMMARY_BUILDER")
        self.assertEqual(portfolio["freshness_status"], "UNTESTED")
        self.assertIsNone(portfolio["cash_available"])
        self.assertIsNone(portfolio["equity"])
        self.assertEqual(portfolio["configured_paper_starting_cash"], 1000000.0)
        self.assertEqual(portfolio["configured_paper_starting_cash_currency"], "KRW")
        self.assertEqual(portfolio["configured_paper_starting_cash_source"], "MVP_PAPER_DEFAULT_NOT_LIVE_ACCOUNT")
        self.assertEqual(portfolio["configured_paper_starting_cash_status"], "CONFIGURED_NOT_VERIFIED")
        self.assertFalse(summary["live_ready"]["live_order_ready"])
        self.assertFalse(summary["live_ready"]["live_order_allowed"])

    def test_summary_blocks_configured_paper_capital_exchange_source_claim(self):
        summary = build_summary()
        summary["portfolio"]["configured_paper_starting_cash_source"] = "EXCHANGE_BALANCE"
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_summary_blocks_verified_configured_capital_label_without_ledger_source(self):
        summary = build_summary()
        summary["portfolio"]["configured_paper_starting_cash_status"] = "VERIFIED_SOURCE_PRESENT"
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_summary_accepts_scoped_paper_portfolio_snapshot(self):
        summary = build_summary(with_paper_portfolio=True)
        result = validate_summary_shell(summary, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        self.assertEqual(summary["portfolio"]["source"], "LEDGER")
        self.assertEqual(summary["portfolio"]["freshness_status"], "PASS")
        self.assertEqual(summary["portfolio"]["source_snapshot_status"], "PASS")
        self.assertEqual(len(summary["portfolio"]["source_snapshot_hash"]), 64)
        self.assertIsNone(summary["portfolio"]["source_runtime_cycle_id"])
        self.assertIsNone(summary["portfolio"]["source_paper_ledger_head_hash"])
        self.assertEqual(summary["portfolio"]["source_balance_kind"], "SIMULATED_PAPER_LEDGER")
        self.assertIsInstance(summary["portfolio"]["source_snapshot_generated_at_utc"], str)
        self.assertGreaterEqual(summary["portfolio"]["source_snapshot_age_seconds"], 0)
        self.assertEqual(summary["portfolio"]["source_snapshot_stale_after_seconds"], 300)
        self.assertEqual(summary["portfolio"]["cash_available"], 1000000.0)
        self.assertEqual(summary["portfolio"]["equity"], 1000000.0)
        self.assertEqual(summary["portfolio"]["configured_paper_starting_cash"], 1000000.0)
        self.assertEqual(summary["portfolio"]["configured_paper_starting_cash_status"], "VERIFIED_SOURCE_PRESENT")
        self.assertEqual(summary["positions"], [])

    def test_summary_accepts_filled_paper_position_detail(self):
        paper_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test_summary_shell",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
            source_runtime_cycle_id="summary-runtime-cycle",
            source_paper_ledger_head_hash="C" * 64,
        )
        summary = build_summary(with_paper_portfolio=True, paper_portfolio_snapshot=paper_portfolio)
        result = validate_summary_shell(summary, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        self.assertEqual(summary["portfolio"]["source"], "LEDGER")
        self.assertEqual(summary["portfolio"]["source_runtime_cycle_id"], "summary-runtime-cycle")
        self.assertEqual(summary["portfolio"]["source_paper_ledger_head_hash"], "C" * 64)
        self.assertEqual(summary["portfolio"]["open_position_count"], 1)
        self.assertEqual(summary["portfolio"]["position_market_value"], 10000.0)
        self.assertEqual(summary["portfolio"]["unrealized_pnl"], -10.0)
        self.assertEqual(len(summary["positions"]), 1)
        self.assertEqual(summary["positions"][0]["symbol"], "KRW-BTC")
        self.assertEqual(summary["positions"][0]["side"], "LONG")
        self.assertIn(summary["positions"][0]["source"], {"PAPER_LEDGER_SCAFFOLD", "PAPER_LEDGER_ROLLUP"})
        self.assertTrue(summary["positions"][0]["paper_only"])

    def test_summary_accepts_public_marked_paper_position_detail(self):
        paper_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test_summary_shell",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
            source_runtime_cycle_id="summary-runtime-cycle",
            source_paper_ledger_head_hash="D" * 64,
        )
        marked = mark_paper_portfolio_snapshot_to_public_market(
            paper_portfolio_snapshot=paper_portfolio,
            public_market_data_collection_report=public_rest_collection(),
        )

        summary = build_summary(with_paper_portfolio=True, paper_portfolio_snapshot=marked)
        result = validate_summary_shell(summary, set(registry()["enums"]["live_blocker_code"]["values"]))

        self.assertEqual(result.status, "PASS")
        self.assertEqual(summary["positions"][0]["source"], "PAPER_LEDGER_ROLLUP_PUBLIC_MARK")
        self.assertEqual(summary["positions"][0]["mark_price_source"], "PUBLIC_REST_READ_ONLY_1M_CLOSE")
        self.assertIsInstance(summary["positions"][0]["source_public_market_event_time_utc"], str)
        self.assertEqual(len(summary["positions"][0]["source_public_market_event_hash"]), 64)
        self.assertTrue(summary["positions"][0]["paper_only"])

    def test_summary_blocks_public_marked_position_without_public_provenance(self):
        paper_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test_summary_shell",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
        )
        marked = mark_paper_portfolio_snapshot_to_public_market(
            paper_portfolio_snapshot=paper_portfolio,
            public_market_data_collection_report=public_rest_collection(),
        )
        summary = build_summary(with_paper_portfolio=True, paper_portfolio_snapshot=marked)
        summary["positions"][0]["source_public_market_event_hash"] = None

        result = validate_summary_shell(summary)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_summary_blocks_tampered_position_market_value(self):
        paper_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test_summary_shell",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
        )
        summary = build_summary(with_paper_portfolio=True, paper_portfolio_snapshot=paper_portfolio)
        summary["positions"][0]["market_value"] = "9999"
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_summary_blocks_position_side_drift(self):
        paper_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test_summary_shell",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
        )
        summary = build_summary(with_paper_portfolio=True, paper_portfolio_snapshot=paper_portfolio)
        summary["positions"][0]["side"] = "SHORT"
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_summary_blocks_position_rollup_mismatch(self):
        paper_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test_summary_shell",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
        )
        summary = build_summary(with_paper_portfolio=True, paper_portfolio_snapshot=paper_portfolio)
        summary["portfolio"]["position_market_value"] = summary["portfolio"]["position_market_value"] + 1.0
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

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

    def test_summary_keeps_stale_paper_portfolio_values_as_stale_not_unverified(self):
        paper_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="test_summary_shell",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
        )
        summary = build_summary(with_paper_portfolio=True, paper_portfolio_snapshot=stale_paper_portfolio(paper_portfolio))
        result = validate_summary_shell(summary, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        self.assertEqual(summary["portfolio"]["source"], "LEDGER")
        self.assertEqual(summary["portfolio"]["freshness_status"], "STALE")
        self.assertIsNotNone(summary["portfolio"]["equity"])
        self.assertEqual(summary["portfolio"]["configured_paper_starting_cash"], 1000000.0)
        self.assertEqual(summary["portfolio"]["configured_paper_starting_cash_status"], "VERIFIED_SOURCE_PRESENT")
        self.assertEqual(len(summary["positions"]), 1)
        self.assertIn("stale", summary["portfolio"]["source_snapshot_freshness_message"])
        self.assertIn("Rerun PAPER", summary["portfolio"]["next_action"])

    def test_summary_blocks_stale_label_on_fresh_paper_portfolio(self):
        summary = build_summary(with_paper_portfolio=True)
        summary["portfolio"]["freshness_status"] = "STALE"
        summary["portfolio"]["source_snapshot_age_seconds"] = 0

        result = validate_summary_shell(summary)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_summary_blocks_verified_portfolio_missing_snapshot_time(self):
        summary = build_summary(with_paper_portfolio=True)
        summary["portfolio"]["source_snapshot_generated_at_utc"] = None
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_summary_blocks_verified_portfolio_stale_age_claim(self):
        summary = build_summary(with_paper_portfolio=True)
        summary["portfolio"]["source_snapshot_age_seconds"] = summary["portfolio"]["source_snapshot_stale_after_seconds"] + 1
        result = validate_summary_shell(summary)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LATENCY_TTL_EXPIRED")

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
