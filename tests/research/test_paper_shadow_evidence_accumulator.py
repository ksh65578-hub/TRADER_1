import copy
import hashlib
import json
import unittest

from trader1.research.shadow.evidence_accumulator import (
    build_paper_shadow_evidence_accumulation_from_operation_reports,
    build_paper_shadow_evidence_accumulation_from_runtime_artifacts,
)
from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    build_shadow_observation_actual_runtime_harness_report,
)
from trader1.research.shadow.shadow_runner import (
    build_paper_shadow_evidence_accumulation_report,
    validate_paper_shadow_evidence_accumulation_report,
)
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle


class PaperShadowEvidenceAccumulatorTest(unittest.TestCase):
    def test_paper_only_evidence_accumulation_blocks_optimizer_ranking(self):
        reports = [
            build_upbit_operational_paper_cycle(
                operation_gate_id="paper-only-entry",
                session_id="paper-only-entry-session",
                requested_entry=True,
            ),
            build_upbit_operational_paper_cycle(
                operation_gate_id="paper-only-no-trade",
                session_id="paper-only-no-trade-session",
                requested_entry=False,
            ),
        ]

        report = build_paper_shadow_evidence_accumulation_from_operation_reports(
            evidence_report_id="paper-only-aggregate",
            paper_operation_reports=reports,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SAMPLE_INSUFFICIENT")
        self.assertGreater(report["paper_sample_count"], 0)
        self.assertLess(report["paper_sample_count"], report["min_required_sample_count"])
        self.assertEqual(report["shadow_sample_count"], 0)
        self.assertEqual(
            set(report["source_evidence_ids"]),
            {binding["source_evidence_id"] for binding in report["source_evidence_bindings"]},
        )
        self.assertEqual(report["evidence_span_hours"], 0)
        self.assertEqual(report["evidence_span_source"], "NOT_PROVIDED")
        self.assertEqual(report["evidence_span_source_status"], "MISSING")
        self.assertEqual(report["paper_runtime_span_seconds"], 0)
        self.assertEqual(report["shadow_runtime_span_seconds"], 0)
        self.assertEqual(report["paired_runtime_span_seconds"], 0)
        self.assertTrue(any(source_id.startswith("paper-operation:") for source_id in report["supporting_source_evidence_ids"]))
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_mixed_candidate_identity_blocks_even_with_sufficient_counts(self):
        base = build_upbit_operational_paper_cycle(
            operation_gate_id="aggregate-base",
            session_id="aggregate-base-session",
            requested_entry=True,
        )
        mismatched = copy.deepcopy(base)
        mismatched["operation_gate_id"] = "aggregate-mismatch"
        mismatched["session_id"] = "aggregate-mismatch-session"
        mismatched["paper_shadow_evidence_accumulation_report"]["candidate_id"] = "candidate-other"
        for source in (base, mismatched):
            source["paper_shadow_evidence_accumulation_report"]["paper_sample_count"] = 2
            source["paper_shadow_evidence_accumulation_report"]["entry_reason_count"] = 1
            source["paper_shadow_evidence_accumulation_report"]["no_trade_reason_count"] = 1
            source["paper_shadow_evidence_accumulation_report"]["cost_evidence_count"] = 1

        shadow = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="shadow-source",
            candidate_id=base["paper_shadow_evidence_accumulation_report"]["candidate_id"],
            strategy_id=base["paper_shadow_evidence_accumulation_report"]["strategy_id"],
            strategy_build_id=base["paper_shadow_evidence_accumulation_report"]["strategy_build_id"],
            parameter_hash=base["paper_shadow_evidence_accumulation_report"]["parameter_hash"],
            paper_sample_count=30,
            shadow_sample_count=60,
            entry_reason_count=3,
            no_trade_reason_count=3,
            cost_evidence_count=3,
        )

        report = build_paper_shadow_evidence_accumulation_from_operation_reports(
            evidence_report_id="mixed-identity-aggregate",
            paper_operation_reports=[base, mismatched],
            shadow_evidence_reports=[shadow],
            min_required_sample_count=1,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "BLOCK_RANKING")

    def test_matched_paper_shadow_short_window_can_feed_paper_scorecard_only(self):
        base = build_upbit_operational_paper_cycle(
            operation_gate_id="aggregate-scorecard",
            session_id="aggregate-scorecard-session",
            requested_entry=True,
        )
        evidence = base["paper_shadow_evidence_accumulation_report"]
        paper = copy.deepcopy(base)
        paper["paper_shadow_evidence_accumulation_report"]["paper_sample_count"] = 30
        paper["paper_shadow_evidence_accumulation_report"]["entry_reason_count"] = 5
        paper["paper_shadow_evidence_accumulation_report"]["no_trade_reason_count"] = 5
        paper["paper_shadow_evidence_accumulation_report"]["cost_evidence_count"] = 5
        shadow = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="matched-shadow-source",
            candidate_id=evidence["candidate_id"],
            strategy_id=evidence["strategy_id"],
            strategy_build_id=evidence["strategy_build_id"],
            parameter_hash=evidence["parameter_hash"],
            paper_sample_count=30,
            shadow_sample_count=30,
            entry_reason_count=5,
            no_trade_reason_count=5,
            cost_evidence_count=5,
        )

        report = build_paper_shadow_evidence_accumulation_from_operation_reports(
            evidence_report_id="matched-short-window-aggregate",
            paper_operation_reports=[paper],
            shadow_evidence_reports=[shadow],
            evidence_span_hours=4,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertTrue(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "ALLOW_RANKING")
        self.assertEqual(
            set(report["source_evidence_ids"]),
            {binding["source_evidence_id"] for binding in report["source_evidence_bindings"]},
        )
        self.assertTrue(any(source_id.startswith("paper-operation:") for source_id in report["supporting_source_evidence_ids"]))
        self.assertTrue(any(source_id.startswith("shadow-evidence:") for source_id in report["supporting_source_evidence_ids"]))
        self.assertEqual(report["evidence_span_source"], "EXPLICIT_OPERATOR_SUPPLIED")
        self.assertEqual(report["evidence_span_source_status"], "PASS")
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertEqual(
            report["long_run_blocker_code"],
            "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
        )
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_runtime_artifact_accumulation_counts_validated_cost_and_entry_review_evidence(self):
        scorecard = {
            "candidate_id": "KRW-BTC-pullback-trend-long",
            "strategy_id": "trend_pullback",
            "strategy_build_id": "upbit_paper_runtime_cycle_v1",
            "parameter_hash": "B" * 64,
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "gross_expected_edge_bps": 42.0,
            "expected_fee_bps": 5.0,
            "expected_spread_bps": 1.0,
            "expected_slippage_bps": 5.0,
            "expected_impact_bps": 0.0,
            "expected_latency_penalty_bps": 0.0,
            "net_ev_after_cost_bps": 31.0,
            "cost_model_status": "VALIDATED",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        overfit = {
            "candidate_id": scorecard["candidate_id"],
            "strategy_id": scorecard["strategy_id"],
            "strategy_build_id": scorecard["strategy_build_id"],
            "parameter_hash": scorecard["parameter_hash"],
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "sample_count": 30,
            "diagnostic_hash": "C" * 64,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        samples = [
            {
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "loop_id": f"loop-{index}",
                "cycle_id": f"cycle-{index}",
                "entry_reason_count": 1,
                "exit_reason_count": 0,
                "no_trade_reason_count": 1,
                "candidate_count": 3,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
            for index in range(30)
        ]
        history = {
            "history_id": "runtime-paper-validated-cost",
            "history_hash": "D" * 64,
            "accepted_cycle_sample_count": 30,
            "accepted_loop_report_count": 30,
            "observed_span_seconds": 0,
            "samples": samples,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        harness = {
            "harness_id": "runtime-paper-shadow-validated-cost",
            "harness_status": "PASS",
            "completed_cycle_count": 20,
            "observation_count": 40,
            "observations_per_cycle": 2,
            "heartbeat_count": 20,
            "measured_runtime_seconds": 60,
            "minimum_runtime_window_seconds": 86400,
            "minimum_actual_cycle_count": 2880,
            "harness_report_hash": "E" * 64,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        report = build_paper_shadow_evidence_accumulation_from_runtime_artifacts(
            evidence_report_id="runtime-artifact-validated-cost",
            candidate_scorecard=scorecard,
            overfit_diagnostic_report=overfit,
            paper_sample_history=history,
            shadow_runtime_harness_report=harness,
        )

        self.assertEqual(report["entry_reason_count"], 30)
        self.assertEqual(report["cost_evidence_count"], 30)
        self.assertEqual(report["reason_coverage_deficit_count"], 0)
        self.assertEqual(report["supporting_source_window_count"], 20)
        self.assertEqual(report["supporting_window_deficit"], 0)
        self.assertEqual(report["paper_runtime_span_seconds"], 0)
        self.assertEqual(report["shadow_runtime_span_seconds"], 60)
        self.assertEqual(report["paired_runtime_span_seconds"], 0)
        self.assertEqual(report["evidence_span_source"], "NOT_PROVIDED")
        self.assertEqual(report["evidence_actionability_status"], "SCORECARD_READY_EXTEND_RUNTIME_SPAN")
        self.assertEqual(report["primary_collection_deficit_code"], "EVIDENCE_SPAN_DEFICIT")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_runtime_artifact_accumulation_exposes_shadow_deficit_without_live_permission(self):
        scorecard = {
            "candidate_id": "KRW-BTC-pullback-trend-long",
            "strategy_id": "trend_pullback",
            "strategy_build_id": "upbit_paper_runtime_cycle_v1",
            "parameter_hash": "B" * 64,
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "cost_model_status": "PASS",
            "net_ev_after_cost_bps": 31.0,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        overfit = {
            "candidate_id": scorecard["candidate_id"],
            "strategy_id": scorecard["strategy_id"],
            "strategy_build_id": scorecard["strategy_build_id"],
            "parameter_hash": scorecard["parameter_hash"],
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "sample_count": 300,
            "diagnostic_hash": "C" * 64,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        samples = [
            {
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "loop_id": f"loop-{index // 10}",
                "cycle_id": f"cycle-{index}",
                "entry_reason_count": 0,
                "exit_reason_count": 0,
                "no_trade_reason_count": 1,
                "candidate_count": 3,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
            for index in range(300)
        ]
        history = {
            "history_id": "runtime-paper-samples",
            "history_hash": "D" * 64,
            "accepted_cycle_sample_count": 300,
            "accepted_loop_report_count": 30,
            "observed_span_seconds": 7200,
            "samples": samples,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        harness = build_shadow_observation_actual_runtime_harness_report(
            harness_id="runtime-paper-shadow-short",
            requested_cycle_count=1,
            completed_cycle_count=1,
            observations_per_cycle=2,
            measured_runtime_seconds=60,
            runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
            monotonic_timer_started=True,
            monotonic_timer_stopped=True,
            measured_runtime_seconds_verified=True,
        )

        report = build_paper_shadow_evidence_accumulation_from_runtime_artifacts(
            evidence_report_id="runtime-artifact-aggregate",
            candidate_scorecard=scorecard,
            overfit_diagnostic_report=overfit,
            paper_sample_history=history,
            shadow_runtime_harness_report=harness,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SAMPLE_INSUFFICIENT")
        self.assertEqual(report["paper_sample_count"], 300)
        self.assertEqual(report["shadow_sample_count"], 2)
        self.assertEqual(report["paper_sample_deficit"], 0)
        self.assertEqual(report["shadow_sample_deficit"], 28)
        self.assertEqual(report["paper_runtime_span_seconds"], 7200)
        self.assertEqual(report["shadow_runtime_span_seconds"], 60)
        self.assertEqual(report["paired_runtime_span_seconds"], 60)
        self.assertEqual(report["evidence_span_hours"], 0)
        self.assertEqual(report["evidence_span_source"], "DERIVED_FROM_SUPPORTING_WINDOWS")
        self.assertEqual(report["evidence_span_source_status"], "BLOCKED")
        self.assertEqual(report["evidence_actionability_status"], "COLLECT_SHADOW_SAMPLES")
        self.assertEqual(report["primary_collection_deficit_code"], "SHADOW_SAMPLE_DEFICIT")
        self.assertEqual(report["actual_runtime_source_status"], "PARTIAL_NON_LIVE_RUNTIME")
        self.assertEqual(
            report["actual_runtime_source_evidence_ids"],
            [
                "actual-runtime-source:upbit:krw_spot:paper:mvp1_upbit_paper_launcher:" + "D" * 64,
                (
                    "actual-runtime-source:upbit:krw_spot:shadow:mvp1_upbit_paper_launcher_shadow:"
                    + report["shadow_artifact_hash"]
                ),
            ],
        )
        self.assertEqual(report["actual_runtime_requirement_statuses"]["runtime_span"], "BLOCKED")
        self.assertEqual(report["actual_runtime_requirement_statuses"]["cycle_count"], "BLOCKED")
        self.assertEqual(report["actual_runtime_source_deficit"], 2)
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_runtime_artifact_accumulation_uses_shadow_history_for_runtime_depth(self):
        scorecard = {
            "candidate_id": "KRW-BTC-pullback-trend-long",
            "strategy_id": "trend_pullback",
            "strategy_build_id": "upbit_paper_runtime_cycle_v1",
            "parameter_hash": "B" * 64,
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "gross_expected_edge_bps": 42.0,
            "expected_fee_bps": 5.0,
            "expected_spread_bps": 1.0,
            "expected_slippage_bps": 5.0,
            "expected_impact_bps": 0.0,
            "expected_latency_penalty_bps": 0.0,
            "net_ev_after_cost_bps": 31.0,
            "cost_model_status": "VALIDATED",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        overfit = {
            "candidate_id": scorecard["candidate_id"],
            "strategy_id": scorecard["strategy_id"],
            "strategy_build_id": scorecard["strategy_build_id"],
            "parameter_hash": scorecard["parameter_hash"],
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "sample_count": 300,
            "diagnostic_hash": "C" * 64,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        samples = [
            {
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "loop_id": f"loop-{index}",
                "cycle_id": f"cycle-{index}",
                "entry_reason_count": 1,
                "exit_reason_count": 0,
                "no_trade_reason_count": 1,
                "candidate_count": 3,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
            for index in range(300)
        ]
        history = {
            "history_id": "runtime-paper-history",
            "history_hash": "D" * 64,
            "accepted_cycle_sample_count": 300,
            "accepted_loop_report_count": 30,
            "observed_span_seconds": 7200,
            "samples": samples,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        harness = {
            "harness_id": "runtime-paper-shadow-history",
            "harness_status": "PASS",
            "completed_cycle_count": 20,
            "observation_count": 40,
            "observations_per_cycle": 2,
            "heartbeat_count": 20,
            "measured_runtime_seconds": 2,
            "minimum_runtime_window_seconds": 86400,
            "minimum_actual_cycle_count": 2880,
            "harness_report_hash": "E" * 64,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        shadow_history = _shadow_history(
            accepted_cycles=(20, 20),
            observed_seconds=(2, 2),
        )

        report = build_paper_shadow_evidence_accumulation_from_runtime_artifacts(
            evidence_report_id="runtime-artifact-shadow-history",
            candidate_scorecard=scorecard,
            overfit_diagnostic_report=overfit,
            paper_sample_history=history,
            shadow_runtime_harness_report=harness,
            shadow_runtime_sample_history=shadow_history,
        )

        self.assertEqual(report["shadow_artifact_hash"], shadow_history["history_hash"])
        self.assertEqual(report["shadow_sample_count"], 80)
        self.assertEqual(report["evidence_window_count"], 30)
        self.assertEqual(report["supporting_source_window_count"], 30)
        self.assertEqual(report["shadow_runtime_span_seconds"], 4)
        self.assertEqual(report["paired_runtime_span_seconds"], 4)
        self.assertEqual(report["actual_runtime_source_status"], "PARTIAL_NON_LIVE_RUNTIME")
        self.assertEqual(report["actual_runtime_requirement_statuses"]["runtime_span"], "BLOCKED")
        self.assertEqual(report["actual_runtime_requirement_statuses"]["cycle_count"], "BLOCKED")
        self.assertEqual(report["actual_runtime_requirement_statuses"]["heartbeat_freshness"], "PASS")
        self.assertTrue(report["actual_runtime_source_evidence_ids"][1].endswith(shadow_history["history_hash"]))
        self.assertEqual(report["evidence_actionability_status"], "SCORECARD_READY_EXTEND_RUNTIME_SPAN")
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])

    def test_runtime_artifact_accumulation_blocks_live_flag_drift(self):
        scorecard = {
            "candidate_id": "candidate-live-drift",
            "strategy_id": "strategy-a",
            "strategy_build_id": "build-a",
            "parameter_hash": "E" * 64,
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "cost_model_status": "PASS",
            "net_ev_after_cost_bps": 3.0,
            "live_order_allowed": True,
        }
        overfit = {"sample_count": 30, "diagnostic_hash": "F" * 64}
        history = {"accepted_cycle_sample_count": 30, "samples": []}
        harness = build_shadow_observation_actual_runtime_harness_report(
            harness_id="runtime-paper-shadow-live-drift",
            requested_cycle_count=1,
            completed_cycle_count=1,
            observations_per_cycle=30,
            measured_runtime_seconds=60,
            runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
            monotonic_timer_started=True,
            monotonic_timer_stopped=True,
            measured_runtime_seconds_verified=True,
        )

        report = build_paper_shadow_evidence_accumulation_from_runtime_artifacts(
            evidence_report_id="runtime-artifact-live-drift",
            candidate_scorecard=scorecard,
            overfit_diagnostic_report=overfit,
            paper_sample_history=history,
            shadow_runtime_harness_report=harness,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])


if __name__ == "__main__":
    unittest.main()


def _shadow_history(*, accepted_cycles: tuple[int, ...], observed_seconds: tuple[int, ...]) -> dict:
    samples = []
    for index, (cycle_count, seconds) in enumerate(zip(accepted_cycles, observed_seconds), start=1):
        samples.append(
            {
                "sample_id": f"shadow-history-sample-{index}",
                "accepted": True,
                "validation_status": "PASS",
                "source_validation_status": "PASS",
                "source_hashes_verified": True,
                "source_runtime_hash_pairing_verified": True,
                "runtime_evidence_role": "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN",
                "observed_actual_cycle_count": cycle_count,
                "observed_actual_runtime_seconds": seconds,
                "orchestration_report_hash": hashlib.sha256(f"orchestration-{index}".encode("utf-8")).hexdigest().upper(),
                "long_run_evidence_eligible": False,
                "actual_long_run_runtime_present": False,
                "scorecard_input_eligible": False,
                "promotion_eligible": False,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
                "order_adapter_called": False,
            }
        )
    history = {
        "schema_id": "trader1.shadow_runtime_sample_history.v1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "source_mode": "PAPER",
        "mode": "SHADOW",
        "history_hash": "",
        "accepted_cycle_sample_count": sum(accepted_cycles),
        "observed_span_seconds": sum(observed_seconds),
        "samples": samples,
        "long_run_evidence_eligible": False,
        "actual_long_run_evidence_created": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    history["history_hash"] = _hash_payload({key: value for key, value in history.items() if key != "history_hash"})
    return history


def _hash_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()
