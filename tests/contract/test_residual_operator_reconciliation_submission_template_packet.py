import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_reconciliation_submission_template_packet import (
    MANIFEST_EVIDENCE_PREFIX,
    PLACEHOLDER_SHA256,
    SCHEMA_ID,
    build_residual_operator_reconciliation_submission_template_packet_report,
    validate_residual_operator_reconciliation_submission_template_packet_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
INTAKE_PREFLIGHT_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT.report.json"
)
MANIFEST_PREFLIGHT_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT.report.json"
)
TEMPLATE_PACKET_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-SUBMISSION-TEMPLATE-PACKET"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorReconciliationSubmissionTemplatePacketTest(unittest.TestCase):
    def source_inputs(self):
        return load_json(INTAKE_PREFLIGHT_REPORT_PATH), load_json(MANIFEST_PREFLIGHT_REPORT_PATH), load_json(STATE_PATH)

    def build_report(self):
        intake_preflight_report, manifest_preflight_report, state = self.source_inputs()
        return build_residual_operator_reconciliation_submission_template_packet_report(
            intake_preflight_report,
            manifest_preflight_report,
            state,
            patch_id="TEST_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET",
            generated_at_utc="2026-05-06T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_template_packet_is_preparation_only_and_complete(self):
        intake_preflight_report, manifest_preflight_report, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["schema_id"], SCHEMA_ID)
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["template_packet_status"], "TEMPLATE_PACKET_READY_FOR_OPERATOR_PREPARATION_ONLY")
        self.assertEqual(report["template_packet_scope"], "OPERATOR_PREPARATION_ONLY_NOT_EVIDENCE")
        self.assertEqual(
            report["actual_submission_manifest_path"],
            "system/evidence/operator_submissions/residual_operator_reconciliation_submission_manifest.json",
        )
        self.assertFalse(report["actual_submission_manifest_written_by_this_patch"])
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["operator_submission_accepted"])
        self.assertEqual(report["required_manifest_item_count"], 32)
        self.assertEqual(report["template_manifest_item_count"], 32)
        self.assertEqual(len(report["template_manifest_items"]), 32)
        self.assertEqual(report["required_control_count"], 4)
        self.assertEqual(report["template_control_count"], 4)
        self.assertEqual(len(report["template_control_assertions"]), 4)
        self.assertTrue(report["operator_no_action_needed_for_next_non_live_patch"])
        self.assertTrue(report["operator_action_required_for_gap_closure"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["live_ready_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])

        first_item = report["template_manifest_items"][0]
        self.assertTrue(first_item["evidence_artifact_path_placeholder"].startswith(MANIFEST_EVIDENCE_PREFIX))
        self.assertEqual(first_item["evidence_artifact_sha256_placeholder"], PLACEHOLDER_SHA256)
        self.assertFalse(first_item["current_evidence_write_requested"])
        self.assertFalse(first_item["accepted_for_reconciliation"])
        self.assertFalse(first_item["live_order_allowed"])
        self.assertFalse(first_item["scale_up_allowed"])
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_template_packet_report(
                report,
                intake_preflight_report,
                manifest_preflight_report,
                state,
            ),
            [],
        )

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not TEMPLATE_PACKET_REPORT_PATH.exists():
            self.skipTest("submission template packet report has not been generated yet")
        intake_preflight_report, manifest_preflight_report, state = self.source_inputs()
        report = load_json(TEMPLATE_PACKET_REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_template_packet_report(
                report,
                intake_preflight_report,
                manifest_preflight_report,
                state,
            ),
            [],
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_route(self):
        if not PATCH_PATH.exists():
            self.skipTest("submission template packet patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(TEMPLATE_PACKET_REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_20260506_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_template_permission_or_count_drift(self):
        intake_preflight_report, manifest_preflight_report, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["actual_submission_manifest_written_by_this_patch"] = True
        tampered["operator_submission_validated"] = True
        tampered["operator_submission_accepted"] = True
        tampered["current_evidence_write_allowed"] = True
        tampered["live_ready_write_allowed"] = True
        tampered["live_order_allowed"] = True
        tampered["template_manifest_item_count"] = 31
        tampered["template_manifest_items"][0]["evidence_artifact_path_placeholder"] = "system/runtime/not_allowed.json"
        tampered["template_manifest_items"][0]["live_order_allowed"] = True
        tampered["template_control_assertions"][0]["scale_up_allowed"] = True
        tampered["report_hash"] = "0" * 64

        errors = validate_residual_operator_reconciliation_submission_template_packet_report(
            tampered,
            intake_preflight_report,
            manifest_preflight_report,
            state,
        )
        self.assertTrue(any("actual_submission_manifest_written_by_this_patch" in error for error in errors))
        self.assertTrue(any("operator_submission_validated" in error for error in errors))
        self.assertTrue(any("operator_submission_accepted" in error for error in errors))
        self.assertTrue(any("current_evidence_write_allowed" in error for error in errors))
        self.assertTrue(any("live_ready_write_allowed" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("template_manifest_item_count" in error for error in errors))
        self.assertTrue(any("path placeholder" in error for error in errors))
        self.assertTrue(any("attempted forbidden permission" in error for error in errors))
        self.assertTrue(any("report_hash" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
