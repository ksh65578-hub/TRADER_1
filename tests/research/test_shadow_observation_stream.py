import copy
import unittest

from trader1.research.shadow.shadow_observation import (
    build_shadow_observation_report,
    shadow_observation_hash,
)
from trader1.research.shadow.shadow_observation_stream import (
    build_shadow_observation_stream_report,
    shadow_observation_stream_hash,
    validate_shadow_observation_stream_report,
)
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle


def _observation(index: int) -> dict:
    paper_gate = build_upbit_operational_paper_cycle(
        operation_gate_id="shadow-stream-source",
        session_id=f"shadow-stream-paper-{index}",
        requested_entry=True,
    )
    return build_shadow_observation_report(
        observation_id=f"shadow-stream-observation-{index}",
        paper_operation_gate_report=paper_gate,
        shadow_session_id=f"shadow-stream-shadow-{index}",
        shadow_sample_count=30,
    )


class ShadowObservationStreamTest(unittest.TestCase):
    def test_stream_passes_when_ordered_unique_source_bound_and_live_blocked(self):
        observations = [_observation(index) for index in range(3)]

        report = build_shadow_observation_stream_report(
            stream_id="shadow-stream-pass",
            observations=observations,
            min_required_observation_count=3,
            min_required_evidence_span_hours=24,
            evidence_span_hours=24,
        )
        result = validate_shadow_observation_stream_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["source_mode"], "PAPER")
        self.assertEqual(report["mode"], "SHADOW")
        self.assertEqual(report["optimizer_input_role"], "SHADOW_STREAM_OBSERVATION_ONLY")
        self.assertEqual(report["duplicate_observation_count"], 0)
        self.assertEqual(report["duplicate_paper_source_count"], 0)
        self.assertTrue(report["sequence_monotonic"])
        self.assertTrue(report["source_binding_hash_match"])
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_stream_blocks_duplicate_writer_risk(self):
        observations = [_observation(index) for index in range(2)]

        report = build_shadow_observation_stream_report(
            stream_id="shadow-stream-duplicate",
            observations=[observations[0], observations[0], observations[1]],
            min_required_observation_count=3,
            min_required_evidence_span_hours=24,
            evidence_span_hours=24,
        )
        result = validate_shadow_observation_stream_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DUPLICATE_WRITER_RISK")

    def test_stream_validator_recomputes_duplicate_summaries_after_hash_rewrite(self):
        report = build_shadow_observation_stream_report(
            stream_id="shadow-stream-false-safe-duplicate",
            observations=[_observation(index) for index in range(3)],
            min_required_observation_count=3,
            min_required_evidence_span_hours=24,
            evidence_span_hours=24,
        )
        duplicate_hash = report["paper_operation_gate_hashes"][0]
        report["paper_operation_gate_hashes"][1] = duplicate_hash
        report["source_binding_hashes"][1] = duplicate_hash
        report["observation_bindings"][1]["paper_operation_gate_hash"] = duplicate_hash
        report["duplicate_paper_source_count"] = 0
        report["stream_hash"] = shadow_observation_stream_hash(report)

        result = validate_shadow_observation_stream_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DUPLICATE_WRITER_RISK")

    def test_stream_validator_recomputes_binding_and_evidence_window_summaries(self):
        window_drift = build_shadow_observation_stream_report(
            stream_id="shadow-stream-window-drift",
            observations=[_observation(index) for index in range(3)],
            min_required_observation_count=3,
            min_required_evidence_span_hours=24,
            evidence_span_hours=24,
        )
        window_drift["evidence_window_count"] = 99
        window_drift["stream_hash"] = shadow_observation_stream_hash(window_drift)
        window_result = validate_shadow_observation_stream_report(window_drift)

        self.assertEqual(window_result.status, "BLOCKED")
        self.assertEqual(window_result.blocker_code, "DATA_QUALITY_INSUFFICIENT")

        source_drift = build_shadow_observation_stream_report(
            stream_id="shadow-stream-source-binding-false-safe",
            observations=[_observation(index) for index in range(3)],
            min_required_observation_count=3,
            min_required_evidence_span_hours=24,
            evidence_span_hours=24,
        )
        source_drift["source_binding_hashes"][1] = "A" * 64
        source_drift["source_binding_hash_match"] = True
        source_drift["stream_hash"] = shadow_observation_stream_hash(source_drift)
        source_result = validate_shadow_observation_stream_report(source_drift)

        self.assertEqual(source_result.status, "BLOCKED")
        self.assertEqual(source_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_stream_blocks_non_monotonic_sequence_and_source_drift(self):
        observations = [_observation(index) for index in range(3)]
        non_monotonic = [copy.deepcopy(item) for item in observations]
        for sequence, item in zip((1, 3, 2), non_monotonic):
            item["stream_sequence_number"] = sequence
            item["observation_hash"] = shadow_observation_hash(item)

        report = build_shadow_observation_stream_report(
            stream_id="shadow-stream-non-monotonic",
            observations=non_monotonic,
            min_required_observation_count=3,
            min_required_evidence_span_hours=24,
            evidence_span_hours=24,
        )
        result = validate_shadow_observation_stream_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")

        drifted = [copy.deepcopy(item) for item in observations]
        drifted[0]["source_evidence_binding"]["artifact_hash"] = "A" * 64
        drifted[0]["observation_hash"] = shadow_observation_hash(drifted[0])
        drift_report = build_shadow_observation_stream_report(
            stream_id="shadow-stream-source-drift",
            observations=drifted,
            min_required_observation_count=3,
            min_required_evidence_span_hours=24,
            evidence_span_hours=24,
        )
        drift_result = validate_shadow_observation_stream_report(drift_report)

        self.assertEqual(drift_result.status, "BLOCKED")
        self.assertEqual(drift_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_stream_blocks_live_or_long_run_claim_drift(self):
        observations = [_observation(index) for index in range(3)]
        live_drift = [copy.deepcopy(item) for item in observations]
        live_drift[0]["live_order_allowed"] = True
        live_drift[0]["observation_hash"] = shadow_observation_hash(live_drift[0])

        live_report = build_shadow_observation_stream_report(
            stream_id="shadow-stream-live-drift",
            observations=live_drift,
            min_required_observation_count=3,
            min_required_evidence_span_hours=24,
            evidence_span_hours=24,
        )
        live_result = validate_shadow_observation_stream_report(live_report)

        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        pass_report = build_shadow_observation_stream_report(
            stream_id="shadow-stream-long-run-drift",
            observations=observations,
            min_required_observation_count=3,
            min_required_evidence_span_hours=24,
            evidence_span_hours=24,
        )
        pass_report["long_run_evidence_eligible"] = True
        pass_report["stream_hash"] = shadow_observation_stream_hash(pass_report)
        long_run_result = validate_shadow_observation_stream_report(pass_report)

        self.assertEqual(long_run_result.status, "BLOCKED")
        self.assertEqual(long_run_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
