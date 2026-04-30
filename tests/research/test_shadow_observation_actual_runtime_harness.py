import unittest

from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    build_shadow_observation_actual_runtime_harness_report,
    shadow_observation_actual_runtime_harness_hash,
    validate_shadow_observation_actual_runtime_harness_report,
)


def _verified_runtime_measurement() -> dict:
    return {
        "runtime_measurement_source": "MONOTONIC_LOCAL_TIMER_VERIFIED",
        "monotonic_timer_started": True,
        "monotonic_timer_stopped": True,
        "measured_runtime_seconds_verified": True,
    }


class ShadowObservationActualRuntimeHarnessTest(unittest.TestCase):
    def test_harness_runs_short_window_non_live_and_keeps_long_run_blocked(self):
        report = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-pass",
            requested_cycle_count=3,
            completed_cycle_count=3,
            observations_per_cycle=2,
            measured_runtime_seconds=90,
            **_verified_runtime_measurement(),
        )
        result = validate_shadow_observation_actual_runtime_harness_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["harness_status"], "PASS")
        self.assertTrue(report["actual_non_live_runtime_harness_executed"])
        self.assertFalse(report["long_run_evidence_present"])
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["minimum_evidence_window_met"])
        self.assertFalse(report["minimum_cycle_count_met"])
        self.assertEqual(report["runtime_evidence_status"], "BLOCKED_LONG_RUN_EVIDENCE_MISSING")
        self.assertEqual(report["runtime_measurement_status"], "VERIFIED_SHORT_WINDOW")
        self.assertEqual(report["optimizer_input_role"], "BLOCKER_ONLY_NOT_RANKING_INPUT")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_harness_blocks_live_credential_order_and_scale_drift(self):
        for field in (
            "credential_access_attempted",
            "exchange_account_call_attempted",
            "live_order_api_attempted",
            "order_adapter_called",
            "scale_up_requested",
            "live_order_allowed",
        ):
            report = build_shadow_observation_actual_runtime_harness_report(
                harness_id=f"shadow-actual-runtime-harness-{field}",
                requested_cycle_count=3,
                completed_cycle_count=3,
                **_verified_runtime_measurement(),
            )
            report[field] = True
            report["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(report)

            result = validate_shadow_observation_actual_runtime_harness_report(report)
            self.assertEqual(result.status, "BLOCKED", field)
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED", field)

    def test_harness_blocks_false_long_run_or_threshold_claim(self):
        for field in (
            "long_run_evidence_present",
            "long_run_evidence_eligible",
            "minimum_evidence_window_met",
            "minimum_cycle_count_met",
        ):
            report = build_shadow_observation_actual_runtime_harness_report(
                harness_id=f"shadow-actual-runtime-harness-{field}",
                requested_cycle_count=3,
                completed_cycle_count=3,
                **_verified_runtime_measurement(),
            )
            report[field] = True
            report["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(report)

            result = validate_shadow_observation_actual_runtime_harness_report(report)
            self.assertEqual(result.status, "BLOCKED", field)
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED", field)

    def test_harness_blocks_execution_summary_drift(self):
        false_not_executed = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-execution-summary-false",
            requested_cycle_count=3,
            completed_cycle_count=3,
            **_verified_runtime_measurement(),
        )
        false_not_executed["actual_non_live_runtime_harness_executed"] = False
        false_not_executed["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(false_not_executed)
        false_not_executed_result = validate_shadow_observation_actual_runtime_harness_report(false_not_executed)
        self.assertEqual(false_not_executed_result.status, "BLOCKED")
        self.assertEqual(false_not_executed_result.blocker_code, "MEASUREMENT_MISSING")

        false_executed = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-execution-summary-true",
            requested_cycle_count=3,
            completed_cycle_count=2,
            **_verified_runtime_measurement(),
        )
        false_executed["actual_non_live_runtime_harness_executed"] = True
        false_executed["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(false_executed)
        false_executed_result = validate_shadow_observation_actual_runtime_harness_report(false_executed)
        self.assertEqual(false_executed_result.status, "BLOCKED")
        self.assertEqual(false_executed_result.blocker_code, "MEASUREMENT_MISSING")

    def test_harness_blocks_partial_duplicate_and_source_hash_drift(self):
        partial = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-partial",
            requested_cycle_count=3,
            completed_cycle_count=2,
            **_verified_runtime_measurement(),
        )
        partial_result = validate_shadow_observation_actual_runtime_harness_report(partial)
        self.assertEqual(partial_result.status, "BLOCKED")
        self.assertEqual(partial_result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")

        duplicate = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-duplicate",
            requested_cycle_count=3,
            completed_cycle_count=3,
            duplicate_writer_detected=True,
            **_verified_runtime_measurement(),
        )
        duplicate_result = validate_shadow_observation_actual_runtime_harness_report(duplicate)
        self.assertEqual(duplicate_result.status, "BLOCKED")
        self.assertEqual(duplicate_result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")

        hash_drift = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-hash-drift",
            requested_cycle_count=3,
            completed_cycle_count=3,
            **_verified_runtime_measurement(),
        )
        hash_drift["source_runtime_report_hash"] = "0" * 64
        hash_drift["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(hash_drift)
        hash_result = validate_shadow_observation_actual_runtime_harness_report(hash_drift)
        self.assertEqual(hash_result.status, "BLOCKED")
        self.assertEqual(hash_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_harness_blocks_oversized_short_window_cycle_and_heartbeat_counts(self):
        report = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-oversized-cycles",
            requested_cycle_count=21,
            completed_cycle_count=21,
            heartbeat_count=21,
            **_verified_runtime_measurement(),
        )

        result = validate_shadow_observation_actual_runtime_harness_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RESOURCE_LIMIT_BLOCK")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_harness_blocks_oversized_observation_fanout_and_runtime(self):
        fanout = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-oversized-fanout",
            requested_cycle_count=3,
            completed_cycle_count=3,
            observations_per_cycle=21,
            **_verified_runtime_measurement(),
        )
        fanout_result = validate_shadow_observation_actual_runtime_harness_report(fanout)
        self.assertEqual(fanout_result.status, "BLOCKED")
        self.assertEqual(fanout_result.blocker_code, "RESOURCE_LIMIT_BLOCK")

        runtime = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-oversized-runtime",
            requested_cycle_count=3,
            completed_cycle_count=3,
            measured_runtime_seconds=301,
            **_verified_runtime_measurement(),
        )
        runtime_result = validate_shadow_observation_actual_runtime_harness_report(runtime)
        self.assertEqual(runtime_result.status, "BLOCKED")
        self.assertEqual(runtime_result.blocker_code, "RESOURCE_LIMIT_BLOCK")

    def test_harness_blocks_negative_runtime_measurement(self):
        report = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-negative-runtime",
            requested_cycle_count=3,
            completed_cycle_count=3,
            measured_runtime_seconds=-1,
            **_verified_runtime_measurement(),
        )

        result = validate_shadow_observation_actual_runtime_harness_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DATA_QUALITY_INSUFFICIENT")
        self.assertEqual(report["harness_status"], "BLOCKED")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_harness_blocks_parameterized_long_run_threshold_satisfaction(self):
        runtime_threshold = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-runtime-threshold",
            requested_cycle_count=3,
            completed_cycle_count=3,
            measured_runtime_seconds=90,
            minimum_runtime_window_seconds=90,
            **_verified_runtime_measurement(),
        )
        runtime_result = validate_shadow_observation_actual_runtime_harness_report(runtime_threshold)
        self.assertEqual(runtime_result.status, "BLOCKED")
        self.assertEqual(runtime_result.blocker_code, "MEASUREMENT_MISSING")

        cycle_threshold = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-cycle-threshold",
            requested_cycle_count=3,
            completed_cycle_count=3,
            minimum_actual_cycle_count=3,
            **_verified_runtime_measurement(),
        )
        cycle_result = validate_shadow_observation_actual_runtime_harness_report(cycle_threshold)
        self.assertEqual(cycle_result.status, "BLOCKED")
        self.assertEqual(cycle_result.blocker_code, "MEASUREMENT_MISSING")

    def test_harness_blocks_weakened_long_run_threshold_floors(self):
        report = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-weakened-floor",
            requested_cycle_count=3,
            completed_cycle_count=3,
            measured_runtime_seconds=90,
            **_verified_runtime_measurement(),
        )
        for field, value in (
            ("minimum_runtime_window_seconds", 302),
            ("minimum_actual_cycle_count", 21),
        ):
            mutated = dict(report)
            mutated[field] = value
            mutated["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(mutated)
            result = validate_shadow_observation_actual_runtime_harness_report(mutated)

            self.assertEqual(result.status, "BLOCKED", field)
            self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING", field)
            self.assertFalse(mutated["live_order_allowed"])
            self.assertFalse(mutated["scale_up_allowed"])

    def test_harness_blocks_unverified_runtime_measurement_source(self):
        report = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-unverified-measurement",
            requested_cycle_count=3,
            completed_cycle_count=3,
            measured_runtime_seconds=90,
        )

        result = validate_shadow_observation_actual_runtime_harness_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")
        self.assertEqual(report["runtime_measurement_source"], "CALLER_SUPPLIED_UNVERIFIED")
        self.assertEqual(report["runtime_measurement_status"], "BLOCKED_UNVERIFIED_MEASUREMENT")
        self.assertFalse(report["actual_non_live_runtime_harness_executed"])

    def test_harness_blocks_measurement_status_summary_drift(self):
        report = build_shadow_observation_actual_runtime_harness_report(
            harness_id="shadow-actual-runtime-harness-measurement-drift",
            requested_cycle_count=3,
            completed_cycle_count=3,
            measured_runtime_seconds=90,
        )
        report["runtime_measurement_status"] = "VERIFIED_SHORT_WINDOW"
        report["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(report)

        result = validate_shadow_observation_actual_runtime_harness_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")


if __name__ == "__main__":
    unittest.main()
