import copy
import unittest

from trader1.research.shadow.evidence_accumulator import build_paper_shadow_evidence_accumulation_from_operation_reports
from trader1.research.shadow.shadow_observation import (
    build_shadow_observation_report,
    shadow_observation_hash,
    validate_shadow_observation_report,
)
from trader1.research.shadow.shadow_runner import (
    paper_shadow_evidence_hash,
    validate_paper_shadow_evidence_accumulation_report,
)
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle, operation_gate_hash


class ShadowObservationRuntimeTest(unittest.TestCase):
    def test_shadow_observation_binds_valid_paper_source_without_live_permission(self):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="shadow-observation-source",
            session_id="shadow-observation-paper",
            requested_entry=True,
        )

        report = build_shadow_observation_report(
            observation_id="shadow-observation-pass",
            paper_operation_gate_report=paper_gate,
            shadow_session_id="shadow-observation-shadow",
            shadow_sample_count=30,
        )
        result = validate_shadow_observation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["source_mode"], "PAPER")
        self.assertEqual(report["mode"], "SHADOW")
        self.assertEqual(report["source_paper_validation_status"], "PASS")
        self.assertTrue(report["source_paper_hash_valid"])
        self.assertEqual(report["optimizer_input_role"], "SHADOW_OBSERVATION_ONLY")
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(report["order_adapter_called"])

    def test_shadow_observation_blocks_live_flag_drift(self):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="shadow-observation-live-source",
            session_id="shadow-observation-live-paper",
            requested_entry=True,
        )
        report = build_shadow_observation_report(
            observation_id="shadow-observation-live",
            paper_operation_gate_report=paper_gate,
            shadow_sample_count=30,
        )
        report["live_order_allowed"] = True
        report["observation_hash"] = shadow_observation_hash(report)

        result = validate_shadow_observation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_shadow_observation_blocks_tampered_or_same_session_source(self):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="shadow-observation-tamper-source",
            session_id="shadow-observation-tamper-paper",
            requested_entry=True,
        )
        tampered = copy.deepcopy(paper_gate)
        tampered["session_id"] = "shadow-observation-tampered-paper"

        tampered_report = build_shadow_observation_report(
            observation_id="shadow-observation-tampered",
            paper_operation_gate_report=tampered,
            shadow_sample_count=30,
        )
        tampered_result = validate_shadow_observation_report(tampered_report)

        self.assertEqual(tampered_result.status, "BLOCKED")
        self.assertEqual(tampered_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

        same_session_report = build_shadow_observation_report(
            observation_id="shadow-observation-same-session",
            paper_operation_gate_report=paper_gate,
            shadow_session_id=paper_gate["session_id"],
            shadow_sample_count=30,
        )
        same_session_result = validate_shadow_observation_report(same_session_report)

        self.assertEqual(same_session_result.status, "BLOCKED")
        self.assertEqual(same_session_result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_shadow_observation_feeds_accumulator_as_paper_scorecard_only(self):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="shadow-observation-accumulator",
            session_id="shadow-observation-accumulator-paper",
            requested_entry=True,
        )
        paper_evidence = paper_gate["paper_shadow_evidence_accumulation_report"]
        paper_evidence["paper_sample_count"] = 30
        paper_evidence["entry_reason_count"] = 5
        paper_evidence["no_trade_reason_count"] = 5
        paper_evidence["cost_evidence_count"] = 5
        paper_evidence["evidence_hash"] = paper_shadow_evidence_hash(paper_evidence)
        paper_gate["operation_gate_hash"] = operation_gate_hash(paper_gate)
        shadow = build_shadow_observation_report(
            observation_id="shadow-observation-accumulator-shadow",
            paper_operation_gate_report=paper_gate,
            shadow_session_id="shadow-observation-accumulator-shadow",
            shadow_sample_count=30,
        )

        report = build_paper_shadow_evidence_accumulation_from_operation_reports(
            evidence_report_id="shadow-observation-accumulator-aggregate",
            paper_operation_reports=[paper_gate],
            shadow_evidence_reports=[shadow],
            evidence_span_hours=4,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertTrue(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "ALLOW_RANKING")
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])


if __name__ == "__main__":
    unittest.main()
