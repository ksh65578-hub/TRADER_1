import copy
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
from trader1.research.profitability.candidate_scorecard import (
    PERFORMANCE_PASS,
    ROBUSTNESS_PASS,
    candidate_scorecard_from_upbit_paper_runtime_cycle,
    performance_source_evidence_id,
    robustness_source_evidence_id,
    source_role_semantics_errors,
)
from trader1.research.profitability.convergence_memory import (
    optimizer_memory_state_from_scorecard,
    strategy_performance_memory_from_scorecard,
)
from trader1.research.profitability.overfit_diagnostic import overfit_diagnostic_report_hash
from trader1.research.profitability.strategy_mutation_compiler import (
    StrategyMutationCompiler,
    mutated_paper_candidate_spec_hash,
    validate_strategy_mutation_compiler_report,
)
from trader1.research.replay.replay_runner import (
    build_public_replay_robustness_report,
    public_replay_robustness_report_hash,
    validate_public_replay_robustness_report,
)
from trader1.runtime.paper.upbit_paper_runtime import (
    build_upbit_paper_runtime_cycle_report,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]

PASS_PERFORMANCE_METRICS = {
    "closed_trade_sample_count": 42,
    "min_closed_trade_sample_count": 30,
    "strategy_exit_policy_sample_count": 42,
    "min_strategy_exit_policy_sample_count": 30,
    "strategy_exit_policy_match_count": 42,
    "strategy_exit_policy_mismatch_count": 0,
    "strategy_exit_reason_count": 42,
    "strategy_exit_reason_counts": [{"reason_code": "TRAILING_STOP", "count": 42}],
    "regime_outcome_sample_count": 42,
    "min_regime_outcome_sample_count": 4,
    "regime_outcome_covered_count": 4,
    "min_regime_outcome_covered_count": 4,
    "regime_outcome_trade_count": 39,
    "regime_outcome_no_trade_count": 3,
    "regime_outcome_mismatch_count": 0,
    "regime_outcome_counts": [
        {
            "regime": "UPTREND",
            "sample_count": 39,
            "trade_count": 39,
            "no_trade_count": 0,
            "mismatch_count": 0,
            "trade_allowed": True,
            "primary_blocker_code": None,
        },
        {
            "regime": "RANGE",
            "sample_count": 1,
            "trade_count": 0,
            "no_trade_count": 1,
            "mismatch_count": 0,
            "trade_allowed": True,
            "primary_blocker_code": "REGIME_MISMATCH",
        },
        {
            "regime": "DOWNTREND",
            "sample_count": 1,
            "trade_count": 0,
            "no_trade_count": 1,
            "mismatch_count": 0,
            "trade_allowed": False,
            "primary_blocker_code": "REGIME_MISMATCH",
        },
        {
            "regime": "RISK_OFF",
            "sample_count": 1,
            "trade_count": 0,
            "no_trade_count": 1,
            "mismatch_count": 0,
            "trade_allowed": False,
            "primary_blocker_code": "RISK_VETO",
        },
    ],
    "realized_vs_expected_sample_count": 42,
    "fill_quality_sample_count": 42,
    "execution_cost_sample_count": 42,
    "profit_factor": 1.42,
    "min_profit_factor": 1.25,
    "max_drawdown_pct": 4.8,
    "max_allowed_drawdown_pct": 8.0,
    "realized_vs_expected_edge_bps": 2.5,
    "min_realized_vs_expected_edge_bps": 0.0,
    "fill_quality_score": 0.91,
    "min_fill_quality_score": 0.80,
    "realized_fee_bps": 5.0,
    "realized_slippage_bps": 16.0,
    "realized_impact_bps": 3.0,
    "expected_total_execution_cost_bps": 20.0,
    "realized_total_execution_cost_bps": 21.0,
    "execution_cost_delta_bps": 1.0,
    "max_allowed_execution_cost_delta_bps": 2.0,
}


def _public_replay_fixture(*, symbol: str, session_id: str, count: int) -> dict:
    market_data = build_upbit_public_candle_fixture(symbol=symbol, session_id=session_id)
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
    market_data.update(
        {
            "source": "PUBLIC_REST_READ_ONLY",
            "profile": "TEST_PUBLIC_REPLAY_HISTORY",
            "candles": candles,
            "raw_payload_private_fields_present": False,
            "public_endpoint_host": "api.upbit.com",
            "public_endpoint_path": "/v1/candles/minutes/1",
            "credential_load_attempted": False,
            "authorization_header_present": False,
            "private_endpoint_called": False,
            "order_endpoint_called": False,
        }
    )
    return market_data


def _ranking_ready_scorecard(*, cycle_id: str = "mutation-compiler-scorecard") -> tuple[dict, dict]:
    runtime = build_upbit_paper_runtime_cycle_report(cycle_id=cycle_id)
    candidate_id = runtime["selected_candidate"]["candidate_id"]
    scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
        runtime,
        robustness_statuses=ROBUSTNESS_PASS,
        robustness_source_evidence_ids=[
            robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
            robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
            robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
        ],
        performance_statuses=PERFORMANCE_PASS,
        performance_metrics=PASS_PERFORMANCE_METRICS,
        performance_source_evidence_ids=[
            performance_source_evidence_id("closed_trades", runtime["cycle_id"], runtime["cycle_hash"], candidate_id),
            performance_source_evidence_id("execution_quality", runtime["cycle_id"], runtime["cycle_hash"], candidate_id),
            performance_source_evidence_id("performance_summary", runtime["cycle_id"], runtime["cycle_hash"], candidate_id),
        ],
    )
    return runtime, scorecard


def _overfit_diagnostic_for(scorecard: dict) -> dict:
    diagnostic = {
        "diagnostic_id": f"overfit:{scorecard['scorecard_id']}",
        "exchange": scorecard["exchange"],
        "market_type": scorecard["market_type"],
        "mode": "PAPER",
        "session_id": scorecard["session_id"],
        "candidate_id": scorecard["candidate_id"],
        "strategy_id": scorecard["strategy_id"],
        "strategy_build_id": scorecard["strategy_build_id"],
        "parameter_hash": scorecard["parameter_hash"],
        "symbol": scorecard["symbol"],
        "oos_status": "PASS",
        "walk_forward_status": "PASS",
        "bootstrap_status": "PASS",
        "overfit_status": "LOW",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    diagnostic["diagnostic_hash"] = overfit_diagnostic_report_hash(diagnostic)
    return diagnostic


def _mature_replay_for(scorecard: dict, *, min_closed_trade_count: int = 30) -> dict:
    replay = build_public_replay_robustness_report(
        candidate_scorecard=scorecard,
        market_data=_public_replay_fixture(
            symbol=scorecard["symbol"],
            session_id=scorecard["session_id"],
            count=70,
        ),
        min_required_sample_count=min_closed_trade_count,
        max_replay_windows=40,
    )
    for row in replay["sample_rows"]:
        row.update(
            {
                "closed_trade": True,
                "realized_trade_pnl_bps": 14.0,
                "realized_vs_expected_edge_bps": 2.0,
                "strategy_exit_policy_observed": True,
                "strategy_exit_policy_matched": True,
                "execution_cost_delta_bps": 0.2,
            }
        )
    sample_count = len(replay["sample_rows"])
    replay.update(
        {
            "replay_closed_trade_sample_count": sample_count,
            "replay_closed_trade_status": "PASS",
            "min_required_closed_trade_sample_count": min_closed_trade_count,
            "replay_closed_trade_deficit": max(0, min_closed_trade_count - sample_count),
            "replay_closed_trade_maturity_status": "PASS" if sample_count >= min_closed_trade_count else "BLOCKED",
            "replay_closed_trade_maturity_blocker_code": (
                None if sample_count >= min_closed_trade_count else "REPLAY_CLOSED_TRADES_BELOW_MIN"
            ),
            "replay_strategy_exit_policy_sample_count": sample_count,
            "replay_strategy_exit_policy_match_count": sample_count,
            "replay_strategy_exit_policy_mismatch_count": 0,
            "replay_strategy_exit_policy_status": "PASS",
            "replay_profit_factor": 2.4,
            "replay_profit_factor_status": "PASS",
            "replay_max_drawdown_bps": 8.0,
            "replay_realized_vs_expected_edge_bps": 2.0,
            "replay_realized_vs_expected_edge_status": "PASS",
            "replay_fill_quality_score": 0.95,
            "replay_execution_cost_delta_bps": 0.2,
            "replay_execution_cost_status": "PASS",
            "replay_status": "PASS",
            "primary_blocker_code": None,
            "blockers": [],
        }
    )
    replay["report_hash"] = public_replay_robustness_report_hash(replay)
    return replay


def _valid_inputs() -> dict:
    runtime, scorecard = _ranking_ready_scorecard()
    return {
        "runtime": runtime,
        "scorecard": scorecard,
        "overfit": _overfit_diagnostic_for(scorecard),
        "strategy_memory": strategy_performance_memory_from_scorecard(scorecard),
        "optimizer_memory": optimizer_memory_state_from_scorecard(scorecard),
        "replay": _mature_replay_for(scorecard),
    }


def _compile(inputs: dict, **overrides) -> dict:
    payload = {
        "candidate_scorecard": inputs.get("scorecard"),
        "overfit_diagnostic": inputs.get("overfit"),
        "convergence_memory": inputs.get("strategy_memory"),
        "optimizer_memory": inputs.get("optimizer_memory"),
        "replay_closed_trade_evidence": inputs.get("replay"),
    }
    payload.update(overrides)
    return StrategyMutationCompiler().compile(**payload)


class StrategyMutationCompilerTest(unittest.TestCase):
    def test_missing_evidence_blocks_mutation_and_keeps_live_flags_false(self):
        report = StrategyMutationCompiler().compile(
            candidate_scorecard=None,
            overfit_diagnostic=None,
            convergence_memory=None,
            optimizer_memory=None,
            replay_closed_trade_evidence=None,
        )

        self.assertEqual(report["compile_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "MEASUREMENT_MISSING")
        self.assertIsNone(report["mutated_paper_candidate_spec"])
        for flag in (
            "credential_load_attempted",
            "private_endpoint_called",
            "order_endpoint_called",
            "order_adapter_called",
            "live_key_loaded",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            self.assertFalse(report[flag])

    def test_robustness_triplet_and_source_role_mismatch_block_mutation(self):
        inputs = _valid_inputs()
        mismatched_triplet = copy.deepcopy(inputs["scorecard"])
        mismatched_triplet["source_evidence_ids"] = [
            source_id.replace(inputs["runtime"]["cycle_hash"], "A" * 64)
            if source_id.startswith("bootstrap:")
            else source_id
            for source_id in mismatched_triplet["source_evidence_ids"]
        ]

        report = _compile({**inputs, "scorecard": mismatched_triplet})
        self.assertEqual(report["compile_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "ROBUSTNESS_TRIPLET_MISMATCH")

        malformed_role = copy.deepcopy(inputs["scorecard"])
        malformed_role["source_evidence_ids"] = list(malformed_role["source_evidence_ids"]) + [
            "closed_trades:bad-history:" + "B" * 64
        ]
        role_report = _compile({**inputs, "scorecard": malformed_role})
        self.assertEqual(role_report["compile_status"], "BLOCKED")
        self.assertEqual(role_report["primary_blocker_code"], "SOURCE_ROLE_SEMANTICS_MISMATCH")

    def test_source_hash_mismatch_and_live_flag_drift_block_mutation(self):
        inputs = _valid_inputs()
        replay_hash_mismatch = copy.deepcopy(inputs["replay"])
        replay_hash_mismatch["sample_count"] += 1

        hash_report = _compile({**inputs, "replay": replay_hash_mismatch})
        self.assertEqual(hash_report["compile_status"], "BLOCKED")
        self.assertEqual(hash_report["primary_blocker_code"], "SCHEMA_IDENTITY_MISMATCH")

        live_drift = copy.deepcopy(inputs["replay"])
        live_drift["private_endpoint_called"] = True
        live_report = _compile({**inputs, "replay": live_drift})
        self.assertEqual(live_report["compile_status"], "BLOCKED")
        self.assertEqual(live_report["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")

    def test_replay_maturity_below_threshold_blocks_mutation(self):
        inputs = _valid_inputs()
        immature = copy.deepcopy(inputs["replay"])
        immature.update(
            {
                "replay_closed_trade_sample_count": 2,
                "min_required_closed_trade_sample_count": 30,
                "replay_closed_trade_deficit": 28,
                "replay_closed_trade_maturity_status": "BLOCKED",
                "replay_closed_trade_maturity_blocker_code": "REPLAY_CLOSED_TRADES_BELOW_MIN",
            }
        )
        immature["report_hash"] = public_replay_robustness_report_hash(immature)

        report = _compile({**inputs, "replay": immature})
        self.assertEqual(report["compile_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "REPLAY_CLOSED_TRADES_BELOW_MIN")

    def test_bounds_violation_fails_mutation(self):
        inputs = _valid_inputs()
        deltas = [
            {
                "parameter_id": "entry_signal_floor",
                "baseline_value": 0.55,
                "mutated_value": 0.70,
                "delta_pct": 27.2727,
                "rationale": "unsafe wide jump",
            }
        ]

        report = _compile(inputs, requested_parameter_deltas=deltas)
        self.assertEqual(report["compile_status"], "FAIL")
        self.assertEqual(report["primary_blocker_code"], "EXPANDED_BOUND_UNVERIFIED")
        self.assertIsNone(report["mutated_paper_candidate_spec"])

    def test_budget_overflow_blocks_mutation(self):
        inputs = _valid_inputs()
        cases = [
            ({"daily_exploration_budget": 1, "daily_exploration_used": 1}, "CANDIDATE_BUDGET_EXCEEDED"),
            ({"strategy_family_mutation_budget": 1, "strategy_family_mutation_used": 1}, "CANDIDATE_BUDGET_EXCEEDED"),
            (
                {"max_concurrent_experimental_candidates": 1, "concurrent_experimental_candidate_count": 1},
                "OPTIMIZER_RESOURCE_LIMIT",
            ),
            ({"replay_cost_budget": 1, "replay_cost_used": 1}, "EXPLORATION_RESOURCE_LIMIT"),
            ({"candidate_retirement_budget": 1, "candidate_retirement_used": 1}, "OPTIMIZER_RESOURCE_LIMIT"),
        ]
        for budget_patch, expected_code in cases:
            with self.subTest(expected_code=expected_code, budget_patch=budget_patch):
                report = _compile(inputs, mutation_budget_state=budget_patch)
                self.assertEqual(report["compile_status"], "BLOCKED")
                self.assertEqual(report["primary_blocker_code"], expected_code)
                self.assertIsNone(report["mutated_paper_candidate_spec"])

    def test_raw_pnl_improvement_alone_cannot_promote_or_mutate(self):
        inputs = _valid_inputs()
        raw_only = copy.deepcopy(inputs["scorecard"])
        raw_only["gross_expected_edge_bps"] = 25.0
        raw_only["net_ev_after_cost_bps"] = -1.0

        report = _compile({**inputs, "scorecard": raw_only})
        self.assertEqual(report["compile_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "COST_AFTER_EDGE_UNVERIFIED")
        self.assertFalse(report["ranking_eligible"])
        self.assertIsNone(report["mutated_paper_candidate_spec"])

    def test_successful_compile_writes_paper_only_spec_with_ranking_false(self):
        inputs = _valid_inputs()
        report = _compile(inputs)
        status, message, blocker_code = validate_strategy_mutation_compiler_report(report)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)
        schema_result = validate_instance_against_schema(report, schema, schema_bundle)

        self.assertEqual(report["compile_status"], "PASS")
        self.assertEqual(status, "PASS", message)
        self.assertIsNone(blocker_code)
        self.assertEqual(schema_result.status, "PASS", schema_result.errors)
        spec = report["mutated_paper_candidate_spec"]
        self.assertEqual(spec["mode"], "PAPER")
        self.assertEqual(spec["allowed_output_modes"], ["REPLAY", "PAPER"])
        self.assertTrue(spec["paper_input_allowed"])
        self.assertTrue(spec["replay_input_allowed"])
        self.assertFalse(spec["ranking_eligible"])
        self.assertFalse(spec["live_config_mutation_allowed"])
        self.assertFalse(spec["writes_live_ready_snapshot"])
        self.assertEqual(spec["spec_hash"], mutated_paper_candidate_spec_hash(spec))
        replay_source_ids = [
            source_id
            for source_id in report["source_evidence_ids"]
            if source_id.startswith("public_replay_robustness:")
        ]
        self.assertEqual(len(replay_source_ids), 1)
        self.assertEqual(len(replay_source_ids[0].split(":")), 3)
        self.assertFalse(source_role_semantics_errors(replay_source_ids))
        for flag in (
            "credential_load_attempted",
            "private_endpoint_called",
            "order_endpoint_called",
            "order_adapter_called",
            "live_key_loaded",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            self.assertFalse(report[flag])
            self.assertFalse(spec[flag])

    def test_mutation_spec_flows_to_runtime_scorecard_and_replay_input(self):
        inputs = _valid_inputs()
        report = _compile(inputs)
        spec = report["mutated_paper_candidate_spec"]
        focus = {
            "source": "TEST_MUTATION_SCOPE",
            "candidate_id": spec["candidate_id"],
            "symbol": spec["symbol"],
            "strategy_id": spec["strategy_id"],
            "strategy_build_id": spec["strategy_build_id"],
            "parameter_hash": spec["parameter_hash"],
            "sample_count": 0,
            "sample_deficit": 30,
            "mutated_paper_candidate_spec": spec,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="mutation-runtime-candidate-flow",
            symbol=spec["symbol"],
            paper_scope_focus=focus,
        )
        runtime_result = validate_upbit_paper_runtime_cycle_report(runtime)
        selected = runtime["selected_candidate"]
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        replay = build_public_replay_robustness_report(
            candidate_scorecard=scorecard,
            market_data=_public_replay_fixture(
                symbol=scorecard["symbol"],
                session_id=scorecard["session_id"],
                count=70,
            ),
            min_required_sample_count=30,
            max_replay_windows=40,
        )
        replay_result = validate_public_replay_robustness_report(replay, candidate_scorecard=scorecard)

        self.assertEqual(runtime_result.status, "PASS", runtime_result.message)
        self.assertEqual(selected["mutation_status"], "APPLIED_TO_PAPER_CANDIDATE")
        self.assertEqual(selected["mutation_id"], spec["mutation_id"])
        self.assertEqual(selected["parameter_hash"], spec["parameter_hash"])
        self.assertFalse(selected["ranking_eligible"])
        self.assertEqual(scorecard["mutation_status"], "APPLIED_TO_PAPER_CANDIDATE")
        self.assertEqual(scorecard["mutation_id"], spec["mutation_id"])
        self.assertEqual(scorecard["parameter_hash"], spec["parameter_hash"])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertEqual(replay_result.status, "PASS")
        self.assertEqual(replay["mutation_status"], "APPLIED_TO_PAPER_CANDIDATE")
        self.assertEqual(replay["mutation_id"], spec["mutation_id"])
        self.assertEqual(replay["parameter_hash"], spec["parameter_hash"])
        self.assertFalse(replay["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
