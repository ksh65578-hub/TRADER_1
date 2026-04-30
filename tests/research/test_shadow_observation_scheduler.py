import unittest

from trader1.research.shadow.shadow_observation import build_shadow_observation_report
from trader1.research.shadow.shadow_observation_scheduler import (
    build_shadow_observation_scheduler_guard_report,
    shadow_observation_scheduler_guard_hash,
    validate_shadow_observation_scheduler_guard_report,
)
from trader1.research.shadow.shadow_observation_stream import build_shadow_observation_stream_report
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle


def _stream_report() -> dict:
    observations = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="shadow-scheduler-source",
            session_id=f"shadow-scheduler-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"shadow-scheduler-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"shadow-scheduler-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    return build_shadow_observation_stream_report(
        stream_id="shadow-scheduler-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )


class ShadowObservationSchedulerGuardTest(unittest.TestCase):
    def test_scheduler_passes_single_writer_clean_recovery_and_live_blocked(self):
        stream = _stream_report()
        report = build_shadow_observation_scheduler_guard_report(
            scheduler_id="shadow-scheduler-pass",
            stream_report=stream,
            writer_id="writer-a",
            active_writer_id="writer-a",
        )
        result = validate_shadow_observation_scheduler_guard_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["run_action"], "APPEND_SHADOW_OBSERVATION_ONLY")
        self.assertEqual(report["recovery_action"], "NO_RECOVERY_NEEDED")
        self.assertTrue(report["lock_owner_match"])
        self.assertFalse(report["concurrent_writer_detected"])
        self.assertTrue(report["lock_lease_fresh"])
        self.assertEqual(report["lock_lease_status"], "PASS")
        self.assertFalse(report["sequence_gap_detected"])
        self.assertEqual(report["partial_write_recovery_status"], "PASS")
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_scheduler_blocks_concurrent_writer(self):
        report = build_shadow_observation_scheduler_guard_report(
            scheduler_id="shadow-scheduler-concurrent",
            stream_report=_stream_report(),
            writer_id="writer-a",
            active_writer_id="writer-b",
        )
        result = validate_shadow_observation_scheduler_guard_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DUPLICATE_WRITER_RISK")
        self.assertEqual(report["run_action"], "BLOCKED")

    def test_scheduler_recomputes_lock_summary_and_blocks_zero_lease(self):
        zero_lease = build_shadow_observation_scheduler_guard_report(
            scheduler_id="shadow-scheduler-zero-lease",
            stream_report=_stream_report(),
            writer_id="writer-a",
            active_writer_id="writer-a",
            lock_lease_seconds=0,
        )
        zero_lease_result = validate_shadow_observation_scheduler_guard_report(zero_lease)

        self.assertEqual(zero_lease_result.status, "BLOCKED")
        self.assertEqual(zero_lease_result.blocker_code, "DUPLICATE_WRITER_RISK")

        owner_drift = build_shadow_observation_scheduler_guard_report(
            scheduler_id="shadow-scheduler-owner-drift",
            stream_report=_stream_report(),
            writer_id="writer-a",
            active_writer_id="writer-a",
        )
        owner_drift["active_writer_id"] = "writer-b"
        owner_drift["lock_owner_match"] = True
        owner_drift["concurrent_writer_detected"] = False
        owner_drift["scheduler_guard_hash"] = shadow_observation_scheduler_guard_hash(owner_drift)
        owner_drift_result = validate_shadow_observation_scheduler_guard_report(owner_drift)

        self.assertEqual(owner_drift_result.status, "BLOCKED")
        self.assertEqual(owner_drift_result.blocker_code, "DUPLICATE_WRITER_RISK")

    def test_scheduler_blocks_stale_lock_lease_and_summary_drift(self):
        stale_lease = build_shadow_observation_scheduler_guard_report(
            scheduler_id="shadow-scheduler-stale-lease",
            stream_report=_stream_report(),
            writer_id="writer-a",
            active_writer_id="writer-a",
            lock_lease_fresh=False,
        )
        stale_result = validate_shadow_observation_scheduler_guard_report(stale_lease)

        self.assertEqual(stale_result.status, "BLOCKED")
        self.assertEqual(stale_result.blocker_code, "DUPLICATE_WRITER_RISK")
        self.assertEqual(stale_lease["lock_lease_status"], "BLOCKED")

        stale_summary_drift = build_shadow_observation_scheduler_guard_report(
            scheduler_id="shadow-scheduler-stale-lease-summary-drift",
            stream_report=_stream_report(),
            writer_id="writer-a",
            active_writer_id="writer-a",
            lock_lease_fresh=False,
        )
        stale_summary_drift["lock_lease_status"] = "PASS"
        stale_summary_drift["scheduler_guard_hash"] = shadow_observation_scheduler_guard_hash(stale_summary_drift)
        drift_result = validate_shadow_observation_scheduler_guard_report(stale_summary_drift)

        self.assertEqual(drift_result.status, "BLOCKED")
        self.assertEqual(drift_result.blocker_code, "DUPLICATE_WRITER_RISK")

    def test_scheduler_blocks_partial_write_and_sequence_gap(self):
        partial = build_shadow_observation_scheduler_guard_report(
            scheduler_id="shadow-scheduler-partial",
            stream_report=_stream_report(),
            writer_id="writer-a",
            partial_temp_artifact_count=1,
        )
        partial_result = validate_shadow_observation_scheduler_guard_report(partial)

        self.assertEqual(partial_result.status, "BLOCKED")
        self.assertEqual(partial_result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")

        sequence_gap = build_shadow_observation_scheduler_guard_report(
            scheduler_id="shadow-scheduler-sequence-gap",
            stream_report=_stream_report(),
            writer_id="writer-a",
            next_sequence_number=99,
        )
        sequence_result = validate_shadow_observation_scheduler_guard_report(sequence_gap)

        self.assertEqual(sequence_result.status, "BLOCKED")
        self.assertEqual(sequence_result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")

    def test_scheduler_blocks_persisted_hash_or_live_flag_drift(self):
        hash_drift = build_shadow_observation_scheduler_guard_report(
            scheduler_id="shadow-scheduler-hash-drift",
            stream_report=_stream_report(),
            writer_id="writer-a",
            persisted_stream_hash="A" * 64,
        )
        hash_result = validate_shadow_observation_scheduler_guard_report(hash_drift)

        self.assertEqual(hash_result.status, "BLOCKED")
        self.assertEqual(hash_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

        live_drift = build_shadow_observation_scheduler_guard_report(
            scheduler_id="shadow-scheduler-live-drift",
            stream_report=_stream_report(),
            writer_id="writer-a",
        )
        live_drift["live_order_allowed"] = True
        live_drift["scheduler_guard_hash"] = shadow_observation_scheduler_guard_hash(live_drift)
        live_result = validate_shadow_observation_scheduler_guard_report(live_drift)

        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
