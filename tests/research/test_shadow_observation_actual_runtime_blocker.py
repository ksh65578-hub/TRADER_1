import unittest

from trader1.research.shadow.shadow_observation import build_shadow_observation_report
from trader1.research.shadow.shadow_observation_actual_runtime_blocker import (
    build_shadow_observation_actual_runtime_blocker_report,
    shadow_observation_actual_runtime_blocker_hash,
    validate_shadow_observation_actual_runtime_blocker_report,
)
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    build_shadow_observation_persistent_runtime_report,
    shadow_observation_persistent_runtime_hash,
)
from trader1.research.shadow.shadow_observation_scheduler import (
    build_shadow_observation_scheduler_guard_report,
)
from trader1.research.shadow.shadow_observation_stream import build_shadow_observation_stream_report
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle


def _runtime_report() -> dict:
    observations = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="actual-runtime-blocker-source",
            session_id=f"actual-runtime-blocker-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"actual-runtime-blocker-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"actual-runtime-blocker-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream = build_shadow_observation_stream_report(
        stream_id="actual-runtime-blocker-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    scheduler = build_shadow_observation_scheduler_guard_report(
        scheduler_id="actual-runtime-blocker-scheduler",
        stream_report=stream,
        writer_id="writer-a",
        active_writer_id="writer-a",
    )
    return build_shadow_observation_persistent_runtime_report(
        runtime_id="actual-runtime-blocker-runtime",
        scheduler_guard_report=scheduler,
        requested_cycle_count=3,
        completed_cycle_count=3,
        max_cycle_count=10,
    )


class ShadowObservationActualRuntimeBlockerTest(unittest.TestCase):
    def test_actual_runtime_blocker_passes_when_only_stub_exists(self):
        runtime_report = _runtime_report()
        report = build_shadow_observation_actual_runtime_blocker_report(
            blocker_report_id="actual-runtime-blocker-pass",
            runtime_report=runtime_report,
        )
        result = validate_shadow_observation_actual_runtime_blocker_report(report, runtime_report=runtime_report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["runtime_evidence_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertFalse(report["actual_runtime_evidence_present"])
        self.assertFalse(report["long_run_evidence_present"])
        self.assertEqual(report["actual_runtime_window_seconds"], 0)
        self.assertTrue(report["stub_cycles_do_not_count_as_long_run"])
        self.assertFalse(report["minimum_evidence_window_met"])
        self.assertFalse(report["minimum_cycle_count_met"])
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(report["order_adapter_called"])

    def test_actual_runtime_blocker_blocks_false_long_run_claim(self):
        runtime_report = _runtime_report()
        report = build_shadow_observation_actual_runtime_blocker_report(
            blocker_report_id="actual-runtime-blocker-false-claim",
            runtime_report=runtime_report,
        )
        report["long_run_evidence_present"] = True
        report["blocker_report_hash"] = shadow_observation_actual_runtime_blocker_hash(report)

        result = validate_shadow_observation_actual_runtime_blocker_report(report, runtime_report=runtime_report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_actual_runtime_blocker_blocks_threshold_or_window_claim(self):
        runtime_report = _runtime_report()
        report = build_shadow_observation_actual_runtime_blocker_report(
            blocker_report_id="actual-runtime-blocker-threshold-claim",
            runtime_report=runtime_report,
        )
        report["actual_runtime_window_seconds"] = report["minimum_runtime_window_seconds"]
        report["minimum_evidence_window_met"] = True
        report["blocker_report_hash"] = shadow_observation_actual_runtime_blocker_hash(report)

        result = validate_shadow_observation_actual_runtime_blocker_report(report, runtime_report=runtime_report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertIn(result.blocker_code, {"MEASUREMENT_MISSING", "LIVE_FINAL_GUARD_FAILED"})

    def test_actual_runtime_blocker_blocks_weakened_long_run_thresholds(self):
        runtime_report = _runtime_report()
        for field, value in (
            ("minimum_runtime_window_seconds", 300),
            ("minimum_actual_cycle_count", 20),
        ):
            report = build_shadow_observation_actual_runtime_blocker_report(
                blocker_report_id=f"actual-runtime-blocker-weakened-{field}",
                runtime_report=runtime_report,
            )
            report[field] = value
            report["blocker_report_hash"] = shadow_observation_actual_runtime_blocker_hash(report)

            result = validate_shadow_observation_actual_runtime_blocker_report(report, runtime_report=runtime_report)

            self.assertEqual(result.status, "BLOCKED", field)
            self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING", field)
            self.assertFalse(report["live_order_allowed"])
            self.assertFalse(report["scale_up_allowed"])

    def test_actual_runtime_blocker_blocks_source_runtime_drift(self):
        runtime_report = _runtime_report()
        runtime_report["live_order_allowed"] = True
        runtime_report["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(runtime_report)
        report = build_shadow_observation_actual_runtime_blocker_report(
            blocker_report_id="actual-runtime-blocker-source-drift",
            runtime_report=runtime_report,
        )

        result = validate_shadow_observation_actual_runtime_blocker_report(report, runtime_report=runtime_report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(report["live_order_allowed"])

    def test_actual_runtime_blocker_blocks_standalone_unverified_source_status(self):
        runtime_report = _runtime_report()
        report = build_shadow_observation_actual_runtime_blocker_report(
            blocker_report_id="actual-runtime-blocker-standalone-source-drift",
            runtime_report=runtime_report,
        )

        hash_drift = dict(report)
        hash_drift["source_runtime_hash_verified"] = False
        hash_drift["blocker_report_hash"] = shadow_observation_actual_runtime_blocker_hash(hash_drift)
        hash_result = validate_shadow_observation_actual_runtime_blocker_report(hash_drift)
        self.assertEqual(hash_result.status, "BLOCKED")
        self.assertEqual(hash_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

        status_drift = dict(report)
        status_drift["source_runtime_validation_status"] = "BLOCKED"
        status_drift["blocker_report_hash"] = shadow_observation_actual_runtime_blocker_hash(status_drift)
        status_result = validate_shadow_observation_actual_runtime_blocker_report(status_drift)
        self.assertEqual(status_result.status, "BLOCKED")
        self.assertEqual(status_result.blocker_code, "DATA_QUALITY_INSUFFICIENT")
        self.assertFalse(status_drift["live_order_allowed"])
        self.assertFalse(status_drift["scale_up_allowed"])


if __name__ == "__main__":
    unittest.main()
