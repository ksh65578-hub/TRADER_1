import unittest

from trader1.research.shadow.evidence_refresh_policy import choose_paper_shadow_evidence_refresh_report
from trader1.research.shadow.paper_shadow_harness_binding import (
    build_paper_shadow_harness_binding_report,
    validate_paper_shadow_harness_binding_report,
)
from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    build_shadow_observation_actual_runtime_harness_report,
)
from trader1.research.shadow.shadow_runner import (
    build_paper_shadow_evidence_accumulation_report,
    paper_shadow_evidence_hash,
    validate_paper_shadow_evidence_accumulation_report,
)


class PaperShadowEvidenceRefreshPolicyTest(unittest.TestCase):
    def test_preserves_existing_scorecard_evidence_when_latest_shadow_sample_regresses(self):
        existing = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="existing-scorecard-evidence",
            paper_sample_count=30,
            shadow_sample_count=40,
        )
        existing_result = validate_paper_shadow_evidence_accumulation_report(existing)
        binding = _binding_for(existing)
        binding_result = validate_paper_shadow_harness_binding_report(binding)
        latest = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="latest-short-shadow-evidence",
            paper_sample_count=30,
            shadow_sample_count=2,
        )
        latest_result = validate_paper_shadow_evidence_accumulation_report(latest)

        decision = choose_paper_shadow_evidence_refresh_report(
            existing_report=existing,
            existing_validation_result=existing_result,
            existing_binding_report=binding,
            existing_binding_validation_result=binding_result,
            latest_report=latest,
            latest_validation_result=latest_result,
        )

        self.assertEqual(existing_result.status, "PASS")
        self.assertEqual(binding_result.status, "PASS")
        self.assertEqual(latest_result.status, "BLOCKED")
        self.assertEqual(latest_result.blocker_code, "SAMPLE_INSUFFICIENT")
        self.assertEqual(decision.selected_source, "existing")
        self.assertEqual(decision.evidence_refresh_action, "PRESERVE_EXISTING_SOURCE_BOUND_SCORECARD_EVIDENCE")
        self.assertEqual(decision.evidence_refresh_reason_code, "LATEST_SHORT_WINDOW_SHADOW_SAMPLE_REGRESSION")
        self.assertEqual(decision.selected_report["shadow_sample_count"], 40)
        self.assertFalse(decision.selected_report["live_order_ready"])
        self.assertFalse(decision.selected_report["live_order_allowed"])
        self.assertFalse(decision.selected_report["can_live_trade"])
        self.assertFalse(decision.selected_report["scale_up_allowed"])

    def test_latest_critical_live_blocker_is_never_hidden_by_existing_evidence(self):
        existing = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="existing-scorecard-evidence",
            paper_sample_count=30,
            shadow_sample_count=40,
        )
        existing_result = validate_paper_shadow_evidence_accumulation_report(existing)
        binding = _binding_for(existing)
        binding_result = validate_paper_shadow_harness_binding_report(binding)
        latest = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="latest-live-drift",
            paper_sample_count=30,
            shadow_sample_count=2,
        )
        latest["live_order_allowed"] = True
        latest["evidence_hash"] = paper_shadow_evidence_hash(latest)
        latest_result = validate_paper_shadow_evidence_accumulation_report(latest)

        decision = choose_paper_shadow_evidence_refresh_report(
            existing_report=existing,
            existing_validation_result=existing_result,
            existing_binding_report=binding,
            existing_binding_validation_result=binding_result,
            latest_report=latest,
            latest_validation_result=latest_result,
        )

        self.assertEqual(latest_result.status, "BLOCKED")
        self.assertEqual(latest_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertEqual(decision.selected_source, "latest")
        self.assertEqual(decision.evidence_refresh_reason_code, "LATEST_CRITICAL_BLOCKER_SURFACED")
        self.assertTrue(decision.selected_report["live_order_allowed"])

    def test_existing_evidence_without_verified_binding_is_not_preserved(self):
        existing = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="existing-unbound-scorecard-evidence",
            paper_sample_count=30,
            shadow_sample_count=40,
        )
        latest = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="latest-short-shadow-evidence",
            paper_sample_count=30,
            shadow_sample_count=2,
        )

        decision = choose_paper_shadow_evidence_refresh_report(
            existing_report=existing,
            existing_validation_result=validate_paper_shadow_evidence_accumulation_report(existing),
            existing_binding_report=None,
            existing_binding_validation_result=None,
            latest_report=latest,
            latest_validation_result=validate_paper_shadow_evidence_accumulation_report(latest),
        )

        self.assertEqual(decision.selected_source, "latest")
        self.assertEqual(decision.evidence_refresh_reason_code, "EXISTING_BINDING_NOT_VERIFIED")
        self.assertEqual(decision.selected_report["shadow_sample_count"], 2)


def _binding_for(evidence_report: dict) -> dict:
    harness = build_shadow_observation_actual_runtime_harness_report(
        harness_id=f"{evidence_report['evidence_report_id']}-harness",
        requested_cycle_count=3,
        completed_cycle_count=3,
        observations_per_cycle=3,
        measured_runtime_seconds=60,
        runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
        monotonic_timer_started=True,
        monotonic_timer_stopped=True,
        measured_runtime_seconds_verified=True,
    )
    return build_paper_shadow_harness_binding_report(
        binding_report_id=f"{evidence_report['evidence_report_id']}-binding",
        shadow_runtime_harness_report=harness,
        paper_shadow_evidence_accumulation_report=evidence_report,
    )


if __name__ == "__main__":
    unittest.main()
