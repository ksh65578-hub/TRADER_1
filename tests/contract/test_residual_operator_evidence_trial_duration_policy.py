import json
import unittest
from pathlib import Path

from trader1.reports.residual_operator_evidence_trial_duration_policy import (
    NEXT_TASK_CLASS,
    TRIAL_HEARTBEAT_TICKS,
    build_residual_operator_evidence_trial_duration_policy_report,
    validate_residual_operator_evidence_trial_duration_policy_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT.report.json"
)
INTAKE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT.report.json"
)
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
POLICY_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-TRIAL-DURATION-POLICY"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorEvidenceTrialDurationPolicyTest(unittest.TestCase):
    def source_inputs(self):
        return load_json(PREFLIGHT_PATH), load_json(INTAKE_PATH), load_json(STATE_PATH)

    def build_report(self):
        preflight, intake, state = self.source_inputs()
        return build_residual_operator_evidence_trial_duration_policy_report(
            preflight,
            intake,
            state,
            patch_id="MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY_TEST",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="F" * 64,
            agents_sha256="A" * 64,
        )

    def test_trial_profile_lowers_operator_run_without_creating_mvp5_evidence(self):
        preflight, intake, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["duration_policy_status"], "TRIAL_PROFILE_ALLOWED_FORMAL_MVP5_STILL_BLOCKED")
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["operator_recommended_next_profile_id"], "UPBIT_PAPER_SAFE_MONITOR_24H_TRIAL")
        self.assertEqual(report["operator_recommended_duration_hours"], 24)
        self.assertEqual(report["operator_recommended_heartbeat_ticks"], TRIAL_HEARTBEAT_TICKS)
        self.assertIn("TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS='8640'", report["operator_recommended_command_text"])
        self.assertIn("UPBIT_PAPER.py", report["operator_recommended_command_text"])
        self.assertNotIn("43200", report["operator_recommended_command_text"])
        self.assertFalse(report["trial_profile_mvp5_evidence_eligible"])
        self.assertFalse(report["trial_profile_gap_closure_allowed"])
        self.assertFalse(report["trial_profile_current_evidence_write_allowed"])
        self.assertTrue(report["formal_mvp5_profile_still_required_for_live_readiness"])
        self.assertFalse(report["formal_mvp5_profile_replaced_by_trial"])
        self.assertEqual(report["formal_mvp5_profile_id"], "UPBIT_PAPER_SAFE_MONITOR_48H")
        self.assertGreaterEqual(report["formal_mvp5_duration_hours"], 48)
        self.assertGreaterEqual(report["formal_mvp5_expected_heartbeat_ticks"], 17280)
        self.assertGreaterEqual(report["formal_mvp5_minimum_paper_shadow_window_count"], 8)
        self.assertFalse(report["operator_run_evidence_ready_for_mvp5"])
        self.assertTrue(report["mvp5_entry_blocked_until_operator_evidence"])

        self.assertEqual(
            validate_residual_operator_evidence_trial_duration_policy_report(report, preflight, intake, state),
            [],
        )

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not POLICY_PATH.exists():
            self.skipTest("residual operator evidence trial duration policy report has not been generated yet")
        preflight, intake, state = self.source_inputs()
        report = load_json(POLICY_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_evidence_trial_duration_policy_report(report, preflight, intake, state),
            [],
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
        self.assertFalse(report["live_ready_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])

    def test_generated_patch_preserves_residual_route_and_blockers(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual operator evidence trial duration policy patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(POLICY_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY_20260505_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["open_gap_ids"], state["open_contract_gap_ids"])
        self.assertEqual(patch_result["operator_recommended_duration_hours"], 24)
        self.assertFalse(patch_result["trial_profile_mvp5_evidence_eligible"])
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_trial_as_live_or_mvp5_evidence(self):
        preflight, intake, state = self.source_inputs()
        report = self.build_report()
        tampered = json.loads(json.dumps(report))
        tampered["trial_profile_mvp5_evidence_eligible"] = True
        tampered["formal_mvp5_profile_replaced_by_trial"] = True
        tampered["formal_mvp5_profile_still_required_for_live_readiness"] = False
        tampered["operator_run_evidence_ready_for_mvp5"] = True
        tampered["live_order_allowed"] = True

        errors = validate_residual_operator_evidence_trial_duration_policy_report(
            tampered,
            preflight,
            intake,
            state,
        )

        self.assertTrue(any("trial_profile_mvp5_evidence_eligible" in error for error in errors))
        self.assertTrue(any("formal_mvp5_profile_replaced_by_trial" in error for error in errors))
        self.assertTrue(any("formal MVP5 profile" in error for error in errors))
        self.assertTrue(any("operator_run_evidence_ready_for_mvp5" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
