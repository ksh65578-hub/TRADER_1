import unittest

from trader1.research.shadow.paper_shadow_harness_binding import (
    build_paper_shadow_harness_binding_report,
    paper_shadow_harness_binding_hash,
    validate_paper_shadow_harness_binding_report,
)
from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    build_shadow_observation_actual_runtime_harness_report,
    shadow_observation_actual_runtime_harness_hash,
)
from trader1.research.shadow.shadow_runner import (
    build_paper_shadow_evidence_accumulation_report,
)


def _verified_runtime_measurement() -> dict:
    return {
        "runtime_measurement_source": "MONOTONIC_LOCAL_TIMER_VERIFIED",
        "monotonic_timer_started": True,
        "monotonic_timer_stopped": True,
        "measured_runtime_seconds_verified": True,
    }


def _harness() -> dict:
    return build_shadow_observation_actual_runtime_harness_report(
        harness_id="paper-shadow-binding-harness",
        requested_cycle_count=3,
        completed_cycle_count=3,
        observations_per_cycle=2,
        measured_runtime_seconds=90,
        **_verified_runtime_measurement(),
    )


class PaperShadowHarnessBindingTest(unittest.TestCase):
    def test_harness_only_waits_for_evidence_without_blocking_current_truth(self):
        report = build_paper_shadow_harness_binding_report(
            binding_report_id="binding-harness-only",
            shadow_runtime_harness_report=_harness(),
        )
        result = validate_paper_shadow_harness_binding_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["binding_status"], "HARNESS_ONLY_WAITING_EVIDENCE")
        self.assertEqual(report["evidence_validation_status"], "NOT_LOADED")
        self.assertEqual(report["critical_blocker_count"], 0)
        self.assertGreater(report["warning_count"], 0)
        self.assertFalse(report["blocks_paper_current_truth_write"])
        self.assertFalse(report["blocks_non_live_runtime_collection"])
        self.assertTrue(report["blocks_live_ready"])
        self.assertTrue(report["blocks_optimizer_or_convergence"])
        self.assertEqual(report["operator_action_required"], "LOCAL_PAPER_SHADOW_RUNTIME_COLLECTION")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_valid_evidence_binds_scorecard_input_but_keeps_optimizer_and_live_blocked(self):
        evidence = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="binding-valid-evidence",
            paper_sample_count=30,
            shadow_sample_count=30,
            entry_reason_count=5,
            no_trade_reason_count=5,
            cost_evidence_count=5,
        )

        report = build_paper_shadow_harness_binding_report(
            binding_report_id="binding-scorecard-input",
            shadow_runtime_harness_report=_harness(),
            paper_shadow_evidence_accumulation_report=evidence,
        )
        result = validate_paper_shadow_harness_binding_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["binding_status"], "BOUND_TO_SCORECARD_INPUT")
        self.assertEqual(report["evidence_validation_status"], "PASS")
        self.assertEqual(report["critical_blocker_count"], 0)
        self.assertEqual(report["paper_sample_count"], 30)
        self.assertEqual(report["shadow_sample_count"], 30)
        self.assertEqual(report["cost_assumption_count"], 5)
        self.assertEqual(report["optimizer_status"], "WAITING_FOR_LONG_RUN_EVIDENCE")
        self.assertTrue(report["blocks_live_ready"])
        self.assertTrue(report["blocks_optimizer_or_convergence"])
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_allowed"])

    def test_stale_evidence_is_warning_not_current_truth_write_blocker(self):
        stale_evidence = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="binding-stale-evidence",
            paper_artifact_age_seconds=1200,
            shadow_artifact_age_seconds=1200,
            max_artifact_age_seconds=900,
        )

        report = build_paper_shadow_harness_binding_report(
            binding_report_id="binding-stale-display",
            shadow_runtime_harness_report=_harness(),
            paper_shadow_evidence_accumulation_report=stale_evidence,
        )
        result = validate_paper_shadow_harness_binding_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["binding_status"], "STALE_DISPLAY_ONLY")
        self.assertEqual(report["latency_freshness_status"], "STALE_DISPLAY_ONLY")
        self.assertEqual(report["critical_blocker_count"], 0)
        self.assertIn("DATA_QUALITY_INSUFFICIENT", report["top_level_blocker_codes"])
        self.assertFalse(report["blocks_paper_current_truth_write"])
        self.assertFalse(report["blocks_non_live_runtime_collection"])
        self.assertEqual(report["operator_action_required"], "NONE_FOR_ROUTINE_REFRESH")

    def test_scope_or_live_source_drift_is_critical(self):
        harness = _harness()
        harness["live_order_api_attempted"] = True
        harness["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(harness)

        report = build_paper_shadow_harness_binding_report(
            binding_report_id="binding-critical-live-drift",
            shadow_runtime_harness_report=harness,
        )
        result = validate_paper_shadow_harness_binding_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertEqual(report["binding_status"], "BLOCKED_SOURCE_INVALID")
        self.assertEqual(report["critical_blocker_count"], 1)
        self.assertTrue(report["blocks_paper_current_truth_write"])
        self.assertTrue(report["blocks_non_live_runtime_collection"])
        self.assertEqual(report["source_scope_status"], "BLOCKED")

    def test_binding_blocks_forbidden_live_flag_mutation(self):
        report = build_paper_shadow_harness_binding_report(
            binding_report_id="binding-live-flag-mutation",
            shadow_runtime_harness_report=_harness(),
        )
        report["live_order_allowed"] = True
        report["binding_report_hash"] = paper_shadow_harness_binding_hash(report)

        result = validate_paper_shadow_harness_binding_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
