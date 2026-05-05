import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_reconciliation_submission_security_quarantine import (
    ALLOWED_ARTIFACT_EXTENSIONS,
    FORBIDDEN_PATH_TOKENS,
    MANIFEST_EVIDENCE_PREFIX,
    SCHEMA_ID,
    build_residual_operator_reconciliation_submission_security_quarantine_report,
    validate_residual_operator_reconciliation_submission_security_quarantine_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
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
SECURITY_QUARANTINE_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_SECURITY_QUARANTINE.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_SECURITY_QUARANTINE.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-SUBMISSION-SECURITY-QUARANTINE"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorReconciliationSubmissionSecurityQuarantineTest(unittest.TestCase):
    def source_inputs(self):
        return (
            load_json(MANIFEST_PREFLIGHT_REPORT_PATH),
            load_json(TEMPLATE_PACKET_REPORT_PATH),
            load_json(STATE_PATH),
        )

    def build_report(self, manifest_preflight_report=None, template_packet_report=None):
        source_manifest, source_template, state = self.source_inputs()
        return build_residual_operator_reconciliation_submission_security_quarantine_report(
            manifest_preflight_report or source_manifest,
            template_packet_report or source_template,
            state,
            patch_id="TEST_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_SECURITY_QUARANTINE",
            generated_at_utc="2026-05-06T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_missing_manifest_quarantine_is_metadata_only_and_blocked(self):
        manifest_preflight_report, template_packet_report, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["schema_id"], SCHEMA_ID)
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["quarantine_status"], "QUARANTINE_PENDING_OPERATOR_SUBMISSION")
        self.assertEqual(report["quarantine_scope"], "METADATA_ONLY_NO_FILE_CONTENT_READ")
        self.assertEqual(report["allowed_submission_prefix"], MANIFEST_EVIDENCE_PREFIX)
        self.assertEqual(report["allowed_artifact_extensions"], list(ALLOWED_ARTIFACT_EXTENSIONS))
        self.assertEqual(report["forbidden_path_tokens"], list(FORBIDDEN_PATH_TOKENS))
        self.assertFalse(report["operator_submission_present"])
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["operator_submission_accepted"])
        self.assertEqual(report["required_manifest_item_count"], 32)
        self.assertEqual(report["manifest_item_count"], 0)
        self.assertEqual(report["missing_manifest_item_count"], 32)
        self.assertEqual(report["required_control_count"], 4)
        self.assertEqual(report["manifest_control_count"], 0)
        self.assertEqual(report["missing_control_count"], 4)
        self.assertEqual(report["template_manifest_item_count"], 32)
        self.assertEqual(report["template_control_count"], 4)
        self.assertEqual(report["template_path_placeholder_violation_count"], 0)
        self.assertEqual(report["security_control_count"], 4)
        self.assertEqual(report["quarantine_blocker_count"], 2)
        self.assertTrue(report["operator_no_action_needed_for_next_non_live_patch"])
        self.assertTrue(report["operator_action_required_for_gap_closure"])
        self.assertFalse(report["evidence_file_content_read"])
        self.assertFalse(report["evidence_artifact_hash_recomputed"])
        self.assertFalse(report["secret_pattern_content_scan_performed"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["live_ready_write_allowed"])
        self.assertFalse(report["live_config_mutation_allowed"])
        self.assertFalse(report["credential_values_read"])
        self.assertFalse(report["runtime_artifacts_staged_by_this_patch"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_security_quarantine_report(
                report,
                manifest_preflight_report,
                template_packet_report,
                state,
            ),
            [],
        )

    def test_structural_error_manifest_stays_quarantined_without_reading_evidence_files(self):
        manifest_preflight_report, template_packet_report, state = self.source_inputs()
        manifest = copy.deepcopy(manifest_preflight_report)
        manifest["manifest_preflight_status"] = "BLOCKED_MANIFEST_STRUCTURAL_ERRORS"
        manifest["manifest_schema_validation_status"] = "FAIL_STRUCTURAL"
        manifest["operator_submission_present"] = True
        manifest["manifest_item_count"] = 32
        manifest["missing_manifest_item_count"] = 0
        manifest["manifest_control_count"] = 4
        manifest["missing_control_count"] = 0
        manifest["unsafe_manifest_flag_count"] = 1
        manifest["path_policy_violation_count"] = 1
        manifest["source_hash_mismatch_count"] = 1
        report = self.build_report(manifest_preflight_report=manifest)

        self.assertEqual(report["quarantine_status"], "QUARANTINE_BLOCKED_STRUCTURAL_ERRORS")
        self.assertTrue(report["operator_submission_present"])
        self.assertEqual(report["preflight_unsafe_manifest_flag_count"], 1)
        self.assertEqual(report["preflight_path_policy_violation_count"], 1)
        self.assertEqual(report["preflight_source_hash_mismatch_count"], 1)
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["operator_submission_accepted"])
        self.assertFalse(report["evidence_file_content_read"])
        self.assertFalse(report["secret_pattern_content_scan_performed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_security_quarantine_report(
                report,
                manifest,
                template_packet_report,
                state,
            ),
            [],
        )

    def test_structural_review_only_manifest_is_still_not_accepted(self):
        manifest_preflight_report, template_packet_report, state = self.source_inputs()
        manifest = copy.deepcopy(manifest_preflight_report)
        manifest["manifest_preflight_status"] = "BLOCKED_MANIFEST_STRUCTURAL_REVIEW_ONLY"
        manifest["manifest_schema_validation_status"] = "PASS_STRUCTURAL_ONLY"
        manifest["operator_submission_present"] = True
        manifest["manifest_structural_check_only"] = True
        manifest["manifest_item_count"] = 32
        manifest["missing_manifest_item_count"] = 0
        manifest["manifest_control_count"] = 4
        manifest["missing_control_count"] = 0
        report = self.build_report(manifest_preflight_report=manifest)

        self.assertEqual(report["quarantine_status"], "QUARANTINE_STRUCTURAL_REVIEW_ONLY_NOT_ACCEPTED")
        self.assertTrue(report["operator_submission_present"])
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["operator_submission_accepted"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_ready_write_allowed"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_security_quarantine_report(
                report,
                manifest,
                template_packet_report,
                state,
            ),
            [],
        )

    def test_template_path_or_permission_drift_invalidates_quarantine_source(self):
        manifest_preflight_report, template_packet_report, state = self.source_inputs()
        template = copy.deepcopy(template_packet_report)
        template["template_manifest_items"][0]["evidence_artifact_path_placeholder"] = "system/runtime/leaked_secret.env"
        template["template_manifest_items"][0]["live_order_allowed"] = True
        report = self.build_report(template_packet_report=template)

        self.assertEqual(report["quarantine_status"], "QUARANTINE_INVALID_SOURCE")
        self.assertGreater(report["template_path_placeholder_violation_count"], 0)
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["live_order_allowed"])
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_security_quarantine_report(
                report,
                manifest_preflight_report,
                template,
                state,
            ),
            [],
        )

    def test_validator_rejects_content_read_or_permission_drift(self):
        manifest_preflight_report, template_packet_report, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["evidence_file_content_read"] = True
        tampered["secret_pattern_content_scan_performed"] = True
        tampered["operator_submission_accepted"] = True
        tampered["current_evidence_write_allowed"] = True
        tampered["live_ready_write_allowed"] = True
        tampered["live_order_allowed"] = True
        tampered["report_hash"] = "0" * 64

        errors = validate_residual_operator_reconciliation_submission_security_quarantine_report(
            tampered,
            manifest_preflight_report,
            template_packet_report,
            state,
        )
        self.assertTrue(any("evidence_file_content_read" in error for error in errors))
        self.assertTrue(any("secret_pattern_content_scan_performed" in error for error in errors))
        self.assertTrue(any("operator_submission_accepted" in error for error in errors))
        self.assertTrue(any("current_evidence_write_allowed" in error for error in errors))
        self.assertTrue(any("live_ready_write_allowed" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("report_hash" in error for error in errors))

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not SECURITY_QUARANTINE_REPORT_PATH.exists():
            self.skipTest("submission security quarantine report has not been generated yet")
        manifest_preflight_report, template_packet_report, state = self.source_inputs()
        report = load_json(SECURITY_QUARANTINE_REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_security_quarantine_report(
                report,
                manifest_preflight_report,
                template_packet_report,
                state,
            ),
            [],
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_route(self):
        if not PATCH_PATH.exists():
            self.skipTest("submission security quarantine patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(SECURITY_QUARANTINE_REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_SECURITY_QUARANTINE_20260506_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])


if __name__ == "__main__":
    unittest.main()
