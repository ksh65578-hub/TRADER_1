import unittest

from trader1.research.shadow.shadow_observation import build_shadow_observation_report
from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    build_shadow_observation_actual_runtime_harness_report,
    shadow_observation_actual_runtime_harness_hash,
)
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    build_shadow_observation_persistent_runtime_report,
    build_shadow_observation_persistent_runtime_report_from_paper_loop,
)
from trader1.research.shadow.shadow_observation_runtime_orchestration import (
    build_shadow_observation_runtime_orchestration_report,
    shadow_observation_runtime_orchestration_hash,
    validate_shadow_observation_runtime_orchestration_report,
)
from trader1.research.shadow.shadow_observation_scheduler import build_shadow_observation_scheduler_guard_report
from trader1.research.shadow.shadow_observation_stream import build_shadow_observation_stream_report
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from tempfile import TemporaryDirectory
from pathlib import Path


def _scheduler_guard_report(seed: str = "runtime-orchestration") -> dict:
    observations = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id=f"{seed}-paper-gate",
            session_id=f"{seed}-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"{seed}-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"{seed}-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream = build_shadow_observation_stream_report(
        stream_id=f"{seed}-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    return build_shadow_observation_scheduler_guard_report(
        scheduler_id=f"{seed}-scheduler",
        stream_report=stream,
        writer_id=f"{seed}-writer",
        active_writer_id=f"{seed}-writer",
    )


def _source_reports(seed: str = "runtime-orchestration") -> tuple[dict, dict]:
    persistent = build_shadow_observation_persistent_runtime_report(
        runtime_id=f"{seed}-persistent-runtime",
        scheduler_guard_report=_scheduler_guard_report(seed),
        requested_cycle_count=3,
        completed_cycle_count=3,
        max_cycle_count=20,
    )
    harness = build_shadow_observation_actual_runtime_harness_report(
        harness_id=f"{seed}-harness",
        requested_cycle_count=3,
        completed_cycle_count=3,
        observations_per_cycle=2,
        measured_runtime_seconds=90,
        runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
        monotonic_timer_started=True,
        monotonic_timer_stopped=True,
        measured_runtime_seconds_verified=True,
        source_runtime_report=persistent,
    )
    return persistent, harness


class ShadowObservationRuntimeOrchestrationTest(unittest.TestCase):
    def test_orchestration_blocks_long_run_evidence_and_live_state(self):
        persistent, harness = _source_reports()
        report = build_shadow_observation_runtime_orchestration_report(
            orchestration_id="runtime-orchestration-pass",
            persistent_runtime_report=persistent,
            actual_runtime_harness_report=harness,
        )
        result = validate_shadow_observation_runtime_orchestration_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["orchestration_status"], "BLOCKED")
        self.assertEqual(report["orchestration_decision"], "BLOCK_LONG_RUN_EVIDENCE")
        self.assertTrue(report["source_hashes_verified"])
        self.assertTrue(report["source_runtime_hash_pairing_verified"])
        self.assertTrue(report["source_scope_match"])
        self.assertTrue(report["persistent_stub_not_long_run_confirmed"])
        self.assertTrue(report["short_window_harness_not_long_run_confirmed"])
        self.assertFalse(report["actual_long_run_runtime_present"])
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_orchestration_accepts_actual_paper_loop_short_window_but_keeps_long_run_blocked(self):
        with TemporaryDirectory() as tmp:
            source_loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="runtime-orchestration-actual-paper-loop",
                session_id="mvp1_upbit_paper_launcher",
                requested_cycle_count=2,
            )
        persistent = build_shadow_observation_persistent_runtime_report_from_paper_loop(
            runtime_id="runtime-orchestration-actual-persistent-runtime",
            scheduler_guard_report=_scheduler_guard_report("runtime-orchestration-actual"),
            source_paper_loop_report=source_loop,
            observed_runtime_seconds=0,
        )
        harness = build_shadow_observation_actual_runtime_harness_report(
            harness_id="runtime-orchestration-actual-harness",
            requested_cycle_count=2,
            completed_cycle_count=2,
            observations_per_cycle=2,
            measured_runtime_seconds=0,
            runtime_measurement_source="PAPER_LOOP_TIMESTAMP_SPAN_VERIFIED",
            measured_runtime_seconds_verified=True,
            source_runtime_report=persistent,
        )
        report = build_shadow_observation_runtime_orchestration_report(
            orchestration_id="runtime-orchestration-actual-short-window",
            persistent_runtime_report=persistent,
            actual_runtime_harness_report=harness,
        )
        result = validate_shadow_observation_runtime_orchestration_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["source_validation_status"], "PASS")
        self.assertEqual(report["observed_actual_cycle_count"], 2)
        self.assertEqual(report["observed_actual_runtime_seconds"], 0)
        self.assertFalse(report["actual_long_run_runtime_present"])
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertFalse(report["live_order_allowed"])

    def test_orchestration_blocks_source_runtime_pairing_mismatch(self):
        persistent, harness = _source_reports("runtime-orchestration-a")
        mismatched_persistent, _ = _source_reports("runtime-orchestration-b")
        report = build_shadow_observation_runtime_orchestration_report(
            orchestration_id="runtime-orchestration-pairing-mismatch",
            persistent_runtime_report=mismatched_persistent,
            actual_runtime_harness_report=harness,
        )
        result = validate_shadow_observation_runtime_orchestration_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")
        self.assertFalse(report["source_runtime_hash_pairing_verified"])
        self.assertNotEqual(persistent["runtime_report_hash"], mismatched_persistent["runtime_report_hash"])

    def test_orchestration_blocks_false_long_run_or_scorecard_claim(self):
        persistent, harness = _source_reports()
        report = build_shadow_observation_runtime_orchestration_report(
            orchestration_id="runtime-orchestration-false-long-run",
            persistent_runtime_report=persistent,
            actual_runtime_harness_report=harness,
        )
        for field in ("actual_long_run_runtime_present", "long_run_evidence_eligible", "scorecard_input_eligible", "promotion_eligible"):
            mutated = dict(report)
            mutated[field] = True
            mutated["orchestration_report_hash"] = shadow_observation_runtime_orchestration_hash(mutated)
            result = validate_shadow_observation_runtime_orchestration_report(mutated)
            self.assertEqual(result.status, "BLOCKED", field)
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED", field)

    def test_orchestration_blocks_weakened_long_run_thresholds(self):
        persistent, harness = _source_reports()
        report = build_shadow_observation_runtime_orchestration_report(
            orchestration_id="runtime-orchestration-weakened-thresholds",
            persistent_runtime_report=persistent,
            actual_runtime_harness_report=harness,
        )
        for field, value in (
            ("minimum_runtime_window_seconds", 300),
            ("minimum_actual_cycle_count", 20),
            ("minimum_evidence_window_count", 1),
        ):
            mutated = dict(report)
            mutated[field] = value
            mutated["orchestration_report_hash"] = shadow_observation_runtime_orchestration_hash(mutated)
            result = validate_shadow_observation_runtime_orchestration_report(mutated)

            self.assertEqual(result.status, "BLOCKED", field)
            self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING", field)
            self.assertFalse(mutated["live_order_allowed"])
            self.assertFalse(mutated["scale_up_allowed"])

    def test_orchestration_blocks_source_hash_or_harness_summary_drift(self):
        persistent, harness = _source_reports()
        hash_drift = dict(harness)
        hash_drift["source_runtime_report_hash"] = "0" * 64
        hash_drift["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(hash_drift)
        report = build_shadow_observation_runtime_orchestration_report(
            orchestration_id="runtime-orchestration-source-hash-drift",
            persistent_runtime_report=persistent,
            actual_runtime_harness_report=hash_drift,
        )
        result = validate_shadow_observation_runtime_orchestration_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

        summary_drift = build_shadow_observation_runtime_orchestration_report(
            orchestration_id="runtime-orchestration-summary-drift",
            persistent_runtime_report=persistent,
            actual_runtime_harness_report=harness,
        )
        summary_drift["short_window_harness_not_long_run_confirmed"] = False
        summary_drift["orchestration_report_hash"] = shadow_observation_runtime_orchestration_hash(summary_drift)
        summary_result = validate_shadow_observation_runtime_orchestration_report(summary_drift)
        self.assertEqual(summary_result.status, "BLOCKED")
        self.assertEqual(summary_result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

    def test_orchestration_blocks_live_order_or_scale_drift(self):
        persistent, harness = _source_reports()
        report = build_shadow_observation_runtime_orchestration_report(
            orchestration_id="runtime-orchestration-live-drift",
            persistent_runtime_report=persistent,
            actual_runtime_harness_report=harness,
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called"):
            mutated = dict(report)
            mutated[field] = True
            mutated["orchestration_report_hash"] = shadow_observation_runtime_orchestration_hash(mutated)
            result = validate_shadow_observation_runtime_orchestration_report(mutated)
            self.assertEqual(result.status, "BLOCKED", field)
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED", field)


if __name__ == "__main__":
    unittest.main()
