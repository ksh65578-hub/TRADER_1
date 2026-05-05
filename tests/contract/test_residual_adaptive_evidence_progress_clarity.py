import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_evidence_progress import (
    build_residual_operator_evidence_progress_report,
    validate_residual_operator_evidence_progress_report,
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
PROGRESS_REPORT_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_PROGRESS_CLARITY.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY-PROGRESS-CLARITY"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualAdaptiveEvidenceProgressClarityTest(unittest.TestCase):
    def source_inputs(self):
        return load_json(EXECUTION_GUIDE_PATH), load_json(STATE_PATH)

    def build_report(self):
        execution_guide_report, state = self.source_inputs()
        return build_residual_operator_evidence_progress_report(
            execution_guide_report,
            state,
            root=ROOT,
            patch_id="TEST_RESIDUAL_ADAPTIVE_EVIDENCE_PROGRESS_CLARITY",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_progress_report_allows_codex_non_live_review_without_user_runtime_now(self):
        execution_guide_report, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(
            report["adaptive_judgement_status"],
            "CODEX_CAN_CONTINUE_NON_LIVE_REVIEW_EVIDENCE_NOT_CLOSURE_READY",
        )
        self.assertEqual(report["fixed_duration_gate_status"], "REMOVED_NO_FIXED_RUNTIME_FLOOR")
        self.assertTrue(report["codex_stepwise_review_allowed"])
        self.assertTrue(report["codex_can_continue_non_live_patches"])
        self.assertFalse(report["user_runtime_required_for_next_non_live_patch"])
        self.assertTrue(report["user_runtime_required_for_gap_closure"])
        self.assertEqual(
            report["evidence_quality_status"],
            "INSUFFICIENT_FOR_GAP_CLOSURE_NON_LIVE_WORK_CONTINUES",
        )
        self.assertIn("No immediate user action", report["user_action_summary"])
        self.assertFalse(report["operator_evidence_ready_for_mvp5"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

        self.assertEqual(validate_residual_operator_evidence_progress_report(report, execution_guide_report, state), [])

    def test_generated_report_matches_schema(self):
        if not PROGRESS_REPORT_PATH.exists():
            self.skipTest("residual operator evidence progress report has not been generated yet")
        execution_guide_report, state = self.source_inputs()
        report = load_json(PROGRESS_REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(validate_residual_operator_evidence_progress_report(report, execution_guide_report, state), [])
        self.assertFalse(report["user_runtime_required_for_next_non_live_patch"])
        self.assertTrue(report["user_runtime_required_for_gap_closure"])

    def test_generated_patch_preserves_live_and_scale_blocks(self):
        if not PATCH_PATH.exists():
            self.skipTest("adaptive evidence progress clarity patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_PROGRESS_CLARITY_20260505_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertTrue(patch_result["codex_stepwise_review_allowed"])
        self.assertTrue(patch_result["codex_can_continue_non_live_patches"])
        self.assertFalse(patch_result["user_runtime_required_for_next_non_live_patch"])
        self.assertTrue(patch_result["user_runtime_required_for_gap_closure"])
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_runtime_or_live_permission_drift(self):
        execution_guide_report, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["user_runtime_required_for_next_non_live_patch"] = True
        tampered["user_runtime_required_for_gap_closure"] = False
        tampered["codex_can_continue_non_live_patches"] = False
        tampered["live_order_allowed"] = True

        errors = validate_residual_operator_evidence_progress_report(tampered, execution_guide_report, state)
        self.assertTrue(any("user_runtime_required_for_next_non_live_patch" in error for error in errors))
        self.assertTrue(any("user_runtime_required_for_gap_closure" in error for error in errors))
        self.assertTrue(any("codex_can_continue_non_live_patches" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
