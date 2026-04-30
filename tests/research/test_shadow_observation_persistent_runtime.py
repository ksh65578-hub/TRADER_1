import unittest

from trader1.research.shadow.shadow_observation import build_shadow_observation_report
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    build_shadow_observation_persistent_runtime_report,
    shadow_observation_persistent_runtime_hash,
    validate_shadow_observation_persistent_runtime_report,
)
from trader1.research.shadow.shadow_observation_scheduler import (
    build_shadow_observation_scheduler_guard_report,
)
from trader1.research.shadow.shadow_observation_stream import build_shadow_observation_stream_report
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle


def _scheduler_guard_report() -> dict:
    observations = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="shadow-runtime-source",
            session_id=f"shadow-runtime-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"shadow-runtime-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"shadow-runtime-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream = build_shadow_observation_stream_report(
        stream_id="shadow-runtime-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    return build_shadow_observation_scheduler_guard_report(
        scheduler_id="shadow-runtime-scheduler",
        stream_report=stream,
        writer_id="writer-a",
        active_writer_id="writer-a",
    )


class ShadowObservationPersistentRuntimeTest(unittest.TestCase):
    def test_persistent_runtime_stub_passes_bounded_clean_and_live_blocked(self):
        report = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-pass",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=3,
            completed_cycle_count=3,
            max_cycle_count=10,
        )
        result = validate_shadow_observation_persistent_runtime_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["runtime_execution_mode"], "BOUNDED_SHADOW_STUB")
        self.assertEqual(report["runtime_evidence_role"], "PERSISTENT_RUNTIME_STUB_ONLY")
        self.assertEqual(report["runtime_duration_evidence_source"], "STUB_ESTIMATE_ONLY")
        self.assertEqual(report["estimated_runtime_seconds"], 90)
        self.assertEqual(report["observed_runtime_seconds"], 0)
        self.assertEqual(report["duration_evidence_role"], "NOT_LONG_RUN_EVIDENCE")
        self.assertEqual(report["distinct_cycle_commit_count"], 3)
        self.assertEqual(report["duplicate_cycle_commit_count"], 0)
        self.assertEqual(report["cycle_identity_status"], "PASS")
        self.assertEqual(len(report["cycle_commit_ids"]), 3)
        self.assertFalse(report["actual_persistent_runtime_executed"])
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(report["order_adapter_called"])

    def test_persistent_runtime_blocks_scheduler_guard_failure(self):
        guard = _scheduler_guard_report()
        guard["source_stream_status"] = "BLOCKED"
        guard["scheduler_status"] = "BLOCKED"
        report = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-source-blocked",
            scheduler_guard_report=guard,
        )
        result = validate_shadow_observation_persistent_runtime_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DATA_QUALITY_INSUFFICIENT")

    def test_persistent_runtime_blocks_cycle_limit_partial_and_shutdown_risk(self):
        over_limit = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-over-limit",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=11,
            max_cycle_count=10,
        )
        over_limit_result = validate_shadow_observation_persistent_runtime_report(over_limit)
        self.assertEqual(over_limit_result.status, "BLOCKED")
        self.assertEqual(over_limit_result.blocker_code, "RESOURCE_LIMIT_BLOCK")

        partial = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-partial",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=3,
            completed_cycle_count=2,
            atomic_commit_count=1,
            partial_temp_artifact_count=1,
            graceful_shutdown=False,
        )
        partial_result = validate_shadow_observation_persistent_runtime_report(partial)
        self.assertEqual(partial_result.status, "BLOCKED")
        self.assertEqual(partial_result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")

    def test_persistent_runtime_blocks_stub_resource_explosion(self):
        too_many_cycles = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-too-many-cycles",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=21,
            completed_cycle_count=21,
            max_cycle_count=21,
        )
        too_many_result = validate_shadow_observation_persistent_runtime_report(too_many_cycles)
        self.assertEqual(too_many_result.status, "BLOCKED")
        self.assertEqual(too_many_result.blocker_code, "RESOURCE_LIMIT_BLOCK")

        too_long_estimate = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-too-long-estimate",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=10,
            completed_cycle_count=10,
            max_cycle_count=10,
            heartbeat_interval_seconds=31,
            max_runtime_seconds=300,
        )
        too_long_result = validate_shadow_observation_persistent_runtime_report(too_long_estimate)
        self.assertEqual(too_long_result.status, "BLOCKED")
        self.assertEqual(too_long_result.blocker_code, "RESOURCE_LIMIT_BLOCK")

        false_safe_capacity = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-capacity-drift",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=3,
            completed_cycle_count=3,
            max_cycle_count=10,
        )
        false_safe_capacity["max_cycle_count"] = 1000
        false_safe_capacity["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(false_safe_capacity)
        false_safe_result = validate_shadow_observation_persistent_runtime_report(false_safe_capacity)
        self.assertEqual(false_safe_result.status, "BLOCKED")
        self.assertEqual(false_safe_result.blocker_code, "RESOURCE_LIMIT_BLOCK")

        false_safe_runtime_budget = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-budget-drift",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=3,
            completed_cycle_count=3,
            max_cycle_count=10,
        )
        false_safe_runtime_budget["max_runtime_seconds"] = 60
        false_safe_runtime_budget["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(false_safe_runtime_budget)
        false_safe_budget_result = validate_shadow_observation_persistent_runtime_report(false_safe_runtime_budget)
        self.assertEqual(false_safe_budget_result.status, "BLOCKED")
        self.assertEqual(false_safe_budget_result.blocker_code, "RESOURCE_LIMIT_BLOCK")

    def test_persistent_runtime_blocks_duplicate_cycle_commit_identity(self):
        duplicate_commit_id = "A" * 64
        duplicate_cycle = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-duplicate-cycle",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=3,
            completed_cycle_count=3,
            atomic_commit_count=3,
            cycle_commit_ids=[duplicate_commit_id, duplicate_commit_id, duplicate_commit_id],
        )
        duplicate_result = validate_shadow_observation_persistent_runtime_report(duplicate_cycle)
        self.assertEqual(duplicate_result.status, "BLOCKED")
        self.assertEqual(duplicate_result.blocker_code, "DUPLICATE_WRITER_RISK")

        false_safe_summary = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-cycle-summary-drift",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=3,
            completed_cycle_count=3,
            atomic_commit_count=3,
            cycle_commit_ids=[duplicate_commit_id, duplicate_commit_id, duplicate_commit_id],
        )
        false_safe_summary["duplicate_cycle_commit_count"] = 0
        false_safe_summary["cycle_identity_status"] = "PASS"
        false_safe_summary["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(false_safe_summary)
        false_safe_result = validate_shadow_observation_persistent_runtime_report(false_safe_summary)
        self.assertEqual(false_safe_result.status, "BLOCKED")
        self.assertEqual(false_safe_result.blocker_code, "DUPLICATE_WRITER_RISK")

    def test_persistent_runtime_blocks_observed_duration_claim_for_stub(self):
        observed_duration = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-observed-duration",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=3,
            completed_cycle_count=3,
            atomic_commit_count=3,
            observed_runtime_seconds=90,
        )
        observed_result = validate_shadow_observation_persistent_runtime_report(observed_duration)
        self.assertEqual(observed_result.status, "BLOCKED")
        self.assertEqual(observed_result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

        false_safe_duration = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-duration-drift",
            scheduler_guard_report=_scheduler_guard_report(),
            requested_cycle_count=3,
            completed_cycle_count=3,
            atomic_commit_count=3,
        )
        false_safe_duration["runtime_duration_evidence_source"] = "OBSERVED_WALL_CLOCK"
        false_safe_duration["duration_evidence_role"] = "LONG_RUN_EVIDENCE"
        false_safe_duration["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(false_safe_duration)
        false_safe_result = validate_shadow_observation_persistent_runtime_report(false_safe_duration)
        self.assertEqual(false_safe_result.status, "BLOCKED")
        self.assertEqual(false_safe_result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

    def test_persistent_runtime_blocks_order_or_live_flag_drift(self):
        order_adapter = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-order-adapter",
            scheduler_guard_report=_scheduler_guard_report(),
            order_adapter_called=True,
        )
        order_result = validate_shadow_observation_persistent_runtime_report(order_adapter)
        self.assertEqual(order_result.status, "BLOCKED")
        self.assertEqual(order_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        live_drift = build_shadow_observation_persistent_runtime_report(
            runtime_id="shadow-runtime-live-drift",
            scheduler_guard_report=_scheduler_guard_report(),
        )
        live_drift["live_order_allowed"] = True
        live_drift["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(live_drift)
        live_result = validate_shadow_observation_persistent_runtime_report(live_drift)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
