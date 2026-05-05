import copy
import json
import unittest
from pathlib import Path

from trader1.reports.residual_mvp5_entry_duration_policy import (
    MVP5_REVIEW_ENTRY_DURATION_HOURS,
    MVP5_REVIEW_ENTRY_HEARTBEAT_TICKS,
    build_residual_mvp5_entry_duration_policy_report,
    validate_residual_mvp5_entry_duration_policy_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
EXECUTION_GUIDE_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.report.json"
)
PROGRESS_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
)
PREFLIGHT_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT.report.json"
)
INTAKE_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT.report.json"
)
TRIAL_POLICY_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY.report.json"
)
POLICY_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_MVP5_ENTRY_DURATION_POLICY.report.json"
)
PATCH_PATH = (
    ROOT / "system" / "evidence" / "patch_results" / "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualMvp5EntryDurationPolicyTest(unittest.TestCase):
    def source_inputs(self):
        return (
            load_json(EXECUTION_GUIDE_PATH),
            load_json(PROGRESS_PATH),
            load_json(PREFLIGHT_PATH),
            load_json(INTAKE_PATH),
            load_json(TRIAL_POLICY_PATH),
            load_json(STATE_PATH),
        )

    def build_report(self):
        execution_guide, progress, preflight, intake, trial_policy, state = self.source_inputs()
        return build_residual_mvp5_entry_duration_policy_report(
            execution_guide,
            progress,
            preflight,
            intake,
            trial_policy,
            state,
            patch_id="TEST_RESIDUAL_MVP5_ENTRY_DURATION_POLICY",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="F" * 64,
            agents_sha256="A" * 64,
        )

    def test_mvp5_review_entry_uses_adaptive_evidence_gate_without_live_permission(self):
        execution_guide, progress, preflight, intake, trial_policy, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["duration_policy_status"], "FIXED_DURATION_GATE_REMOVED_LIVE_STILL_BLOCKED")
        self.assertEqual(report["superseded_duration_hours"], 120)
        self.assertEqual(report["mvp5_review_entry_duration_hours"], MVP5_REVIEW_ENTRY_DURATION_HOURS)
        self.assertEqual(report["mvp5_review_entry_heartbeat_ticks"], MVP5_REVIEW_ENTRY_HEARTBEAT_TICKS)
        self.assertEqual(report["mvp5_review_entry_minimum_paper_shadow_window_count"], 0)
        self.assertEqual(report["mvp5_review_entry_gate_type"], "ADAPTIVE_EVIDENCE_QUALITY_GATE")
        self.assertTrue(report["fixed_duration_gate_removed_by_this_patch"])
        self.assertTrue(report["adaptive_evidence_gate_enabled"])
        self.assertTrue(report["adaptive_stepwise_judgement_required"])
        self.assertIn("TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS=''", report["mvp5_review_entry_command_text"])
        self.assertTrue(report["trial_24h_profile_still_not_mvp5_eligible"])
        self.assertEqual(report["extended_120h_profile_role"], "OPTIONAL_EXTENDED_OBSERVATION_OR_SCALE_UP_CONFIDENCE_ONLY")
        self.assertFalse(report["duration_only_live_ready_allowed"])
        self.assertTrue(report["external_live_evidence_still_required"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

        self.assertEqual(
            validate_residual_mvp5_entry_duration_policy_report(
                report,
                execution_guide,
                progress,
                preflight,
                intake,
                trial_policy,
                state,
            ),
            [],
        )

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not POLICY_PATH.exists():
            self.skipTest("residual MVP5 entry duration policy report has not been generated yet")
        execution_guide, progress, preflight, intake, trial_policy, state = self.source_inputs()
        report = load_json(POLICY_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_mvp5_entry_duration_policy_report(
                report,
                execution_guide,
                progress,
                preflight,
                intake,
                trial_policy,
                state,
            ),
            [],
        )

    def test_generated_patch_preserves_residual_route_and_blockers(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual MVP5 entry duration policy patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(POLICY_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_20260505_001")
        self.assertEqual(report["open_gap_ids"], state["open_contract_gap_ids"])
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(patch_result["mvp5_review_entry_duration_hours_after"], 0)
        self.assertEqual(patch_result["mvp5_review_entry_gate_type"], "ADAPTIVE_EVIDENCE_QUALITY_GATE")
        self.assertTrue(patch_result["fixed_duration_gate_removed"])
        self.assertTrue(patch_result["adaptive_evidence_gate_enabled"])
        self.assertFalse(patch_result["duration_only_live_ready_allowed"])
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_duration_as_live_ready(self):
        execution_guide, progress, preflight, intake, trial_policy, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["duration_only_live_ready_allowed"] = True
        tampered["external_live_evidence_still_required"] = False
        tampered["live_order_allowed"] = True
        tampered["operator_run_evidence_ready_for_mvp5"] = True

        errors = validate_residual_mvp5_entry_duration_policy_report(
            tampered,
            execution_guide,
            progress,
            preflight,
            intake,
            trial_policy,
            state,
        )

        self.assertTrue(any("duration_only_live_ready_allowed" in error for error in errors))
        self.assertTrue(any("external_live_evidence_still_required" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("operator_run_evidence_ready_for_mvp5" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
