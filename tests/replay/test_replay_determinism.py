import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
from trader1.research.profitability.candidate_scorecard import candidate_scorecard_from_upbit_paper_runtime_cycle
from trader1.research.profitability.overfit_diagnostic import overfit_diagnostic_from_upbit_paper_runtime
from trader1.research.replay.replay_runner import (
    build_replay_consistency_report,
    build_public_replay_robustness_report,
    public_replay_robustness_values_from_report,
    validate_public_replay_robustness_report,
    replay_consistency_hash,
    validate_replay_consistency_report,
)
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]


def _public_replay_fixture(*, symbol: str, count: int) -> dict:
    market_data = build_upbit_public_candle_fixture(symbol=symbol, session_id="mvp4_upbit_paper_runtime")
    start = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    candles = []
    for index in range(count):
        price = 980000 + index * 900 + (index % 5) * 250
        candles.append(
            {
                "timestamp": (start + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"),
                "open": str(price - 700),
                "high": str(price + 1800),
                "low": str(price - 1400),
                "close": str(price),
                "volume": str(5 + (index % 7)),
            }
        )
    market_data["source"] = "PUBLIC_REST_READ_ONLY"
    market_data["profile"] = "TEST_PUBLIC_REPLAY_HISTORY"
    market_data["candles"] = candles
    market_data["raw_payload_private_fields_present"] = False
    market_data["public_endpoint_host"] = "api.upbit.com"
    market_data["public_endpoint_path"] = "/v1/candles/minutes/1"
    market_data["credential_load_attempted"] = False
    market_data["authorization_header_present"] = False
    market_data["private_endpoint_called"] = False
    market_data["order_endpoint_called"] = False
    return market_data


class ReplayDeterminismTest(unittest.TestCase):
    def test_same_input_replays_to_same_hash(self):
        report = build_replay_consistency_report(
            replay_id="replay-pass",
            strategy_unit_id="strategy-1",
            parameter_hash="A" * 64,
            input_events=[{"event_id": "event-1", "price": "100"}],
        )
        result = validate_replay_consistency_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(len(set(report["result_hashes"])), 1)

    def test_replay_hash_mismatch_fails(self):
        report = build_replay_consistency_report(
            replay_id="replay-fail",
            strategy_unit_id="strategy-1",
            parameter_hash="A" * 64,
            input_events=[{"event_id": "event-1", "price": "100"}],
        )
        report["result_hashes"][1] = "B" * 64
        report["deterministic_pass"] = False
        report["replay_consistency_hash"] = replay_consistency_hash(report)
        result = validate_replay_consistency_report(report)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")

    def test_replay_live_mutation_blocks(self):
        report = build_replay_consistency_report(
            replay_id="replay-live",
            strategy_unit_id="strategy-1",
            parameter_hash="A" * 64,
            input_events=[{"event_id": "event-1", "price": "100"}],
        )
        report["live_order_allowed"] = True
        report["replay_consistency_hash"] = replay_consistency_hash(report)
        result = validate_replay_consistency_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_public_replay_robustness_builds_non_live_candidate_samples(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
            max_replay_windows=80,
        )
        result = validate_public_replay_robustness_report(report, candidate_scorecard=scorecard)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["replay_status"], "PASS")
        self.assertGreaterEqual(report["sample_count"], 50)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(report["credential_load_attempted"])
        self.assertFalse(report["private_endpoint_called"])
        self.assertFalse(report["order_endpoint_called"])
        self.assertFalse(report["order_adapter_called"])

    def test_public_replay_no_trade_rows_are_flat_cash_returns(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-flat-no-trade-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
            max_replay_windows=80,
        )
        result = validate_public_replay_robustness_report(report, candidate_scorecard=scorecard)
        no_trade_rows = [row for row in report["sample_rows"] if row["decision"] == "NO_TRADE"]

        self.assertEqual(result.status, "PASS")
        self.assertGreater(len(no_trade_rows), 0)
        for row in no_trade_rows:
            self.assertFalse(row["executed_trade"])
            self.assertEqual(row["replay_return_basis"], "FLAT_NO_TRADE_CASH_RETURN")
            self.assertEqual(row["net_ev_after_cost_bps"], 0.0)
            self.assertEqual(row["gross_expected_edge_bps"], 0.0)
            self.assertEqual(row["total_execution_cost_bps"], 0.0)
            self.assertIn("opportunity_net_ev_after_cost_bps", row)
            self.assertIn("opportunity_gross_expected_edge_bps", row)
            self.assertIn("opportunity_total_execution_cost_bps", row)

        values, samples, source_ids = public_replay_robustness_values_from_report(
            report,
            candidate_scorecard=scorecard,
        )
        self.assertEqual(len(values), report["sample_count"])
        self.assertEqual(len(samples), report["sample_count"])
        self.assertIn(
            f"public_replay_robustness:{report['replay_id']}:{report['report_hash']}",
            source_ids,
        )
        for row, value in zip(report["sample_rows"], values, strict=True):
            if row["decision"] == "NO_TRADE":
                self.assertEqual(value, 0.0)
            else:
                self.assertEqual(value, row["net_ev_after_cost_bps"])

    def test_public_replay_robustness_report_matches_contract_schema(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-schema-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
            max_replay_windows=80,
        )
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)

    def test_public_replay_robustness_hash_tamper_fails(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-hash-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
        )
        report["sample_count"] = 1
        result = validate_public_replay_robustness_report(report, candidate_scorecard=scorecard)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_overfit_diagnostic_uses_public_replay_without_ranking_or_live_permission(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-overfit-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
        )
        diagnostic = overfit_diagnostic_from_upbit_paper_runtime(
            candidate_scorecard=scorecard,
            runtime_sample_history={
                "history_id": "invalid-history",
                "history_hash": "A" * 64,
            },
            replay_robustness_report=report,
            min_required_sample_count=50,
            min_required_bootstrap_iterations=50,
            min_required_oos_net_ev_bps=-1000.0,
            min_required_walk_forward_pass_rate=0.0,
            min_required_bootstrap_confidence_lower_bps=-1000.0,
            min_required_ranking_stability_score=0.0,
        )

        self.assertEqual(diagnostic["sample_count"], report["sample_count"])
        self.assertEqual(diagnostic["oos_status"], "PASS")
        self.assertEqual(diagnostic["walk_forward_status"], "PASS")
        self.assertEqual(diagnostic["bootstrap_status"], "PASS")
        self.assertFalse(diagnostic["robustness_eligible"])
        self.assertEqual(diagnostic["promotion_eligible"], False)
        self.assertIn("SURVIVORSHIP_BIAS_RISK", {blocker["code"] for blocker in diagnostic["blockers"]})
        self.assertIn(
            f"public_replay_robustness:{report['replay_id']}:{report['report_hash']}",
            diagnostic["source_evidence_ids"],
        )
        self.assertFalse(diagnostic["live_order_ready"])
        self.assertFalse(diagnostic["live_order_allowed"])
        self.assertFalse(diagnostic["can_live_trade"])
        self.assertFalse(diagnostic["scale_up_allowed"])

    def test_overfit_diagnostic_marks_public_replay_failures_as_failures(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="public-replay-scorecard-overfit-fail-base",
            symbol="KRW-AXL",
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=12),
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        report = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(symbol="KRW-AXL", count=70),
            min_required_sample_count=50,
        )
        diagnostic = overfit_diagnostic_from_upbit_paper_runtime(
            candidate_scorecard=scorecard,
            runtime_sample_history={
                "history_id": "invalid-history",
                "history_hash": "A" * 64,
            },
            replay_robustness_report=report,
            min_required_sample_count=50,
            min_required_bootstrap_iterations=50,
            min_required_oos_net_ev_bps=1000.0,
            min_required_walk_forward_pass_rate=1.0,
            min_required_bootstrap_confidence_lower_bps=1000.0,
            min_required_ranking_stability_score=0.99,
        )
        blocker_codes = {blocker["code"] for blocker in diagnostic["blockers"]}

        self.assertEqual(diagnostic["oos_status"], "FAIL")
        self.assertEqual(diagnostic["walk_forward_status"], "FAIL")
        self.assertEqual(diagnostic["bootstrap_status"], "FAIL")
        self.assertIn("PUBLIC_REPLAY_ROBUSTNESS_FAILED", blocker_codes)
        self.assertIn("OOS_FAILED", blocker_codes)
        self.assertIn("WALK_FORWARD_FAILED", blocker_codes)
        self.assertIn("BOOTSTRAP_FAILED", blocker_codes)
        self.assertFalse(diagnostic["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
