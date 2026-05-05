import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_reconciliation_submission_review_queue import (
    SCHEMA_ID,
    build_residual_operator_reconciliation_submission_review_queue_report,
    validate_residual_operator_reconciliation_submission_review_queue_report,
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
REVIEW_QUEUE_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-SUBMISSION-REVIEW-QUEUE"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorReconciliationSubmissionReviewQueueTest(unittest.TestCase):
    def source_inputs(self):
        return (
            load_json(MANIFEST_PREFLIGHT_REPORT_PATH),
            load_json(TEMPLATE_PACKET_REPORT_PATH),
            load_json(SECURITY_QUARANTINE_REPORT_PATH),
            load_json(STATE_PATH),
        )

    def build_report(self, manifest_preflight_report=None, template_packet_report=None, security_quarantine_report=None):
        source_manifest, source_template, source_quarantine, state = self.source_inputs()
        return build_residual_operator_reconciliation_submission_review_queue_report(
            manifest_preflight_report or source_manifest,
            template_packet_report or source_template,
            security_quarantine_report or source_quarantine,
            state,
            patch_id="TEST_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE",
            generated_at_utc="2026-05-06T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_missing_manifest_review_queue_is_ordered_and_blocked(self):
        manifest, template, quarantine, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["schema_id"], SCHEMA_ID)
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["review_queue_status"], "BLOCKED_OPERATOR_SUBMISSION_MISSING")
        self.assertTrue(report["review_order_locked"])
        self.assertEqual(report["review_phase_count"], 4)
        self.assertEqual(report["blocked_phase_count"], 4)
        self.assertEqual(report["review_ready_phase_count"], 0)
        self.assertEqual(report["accepted_phase_count"], 0)
        self.assertEqual(report["single_next_operator_step"], "CREATE_OPERATOR_SUBMISSION_MANIFEST")
        self.assertFalse(report["operator_submission_present"])
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["operator_submission_accepted"])
        self.assertEqual(report["required_manifest_item_count"], 32)
        self.assertEqual(report["manifest_item_count"], 0)
        self.assertEqual(report["missing_manifest_item_count"], 32)
        self.assertEqual(report["required_control_count"], 4)
        self.assertEqual(report["security_control_count"], 4)
        self.assertEqual([step["phase_id"] for step in report["review_steps"]], [
            "TEMPLATE_PACKET",
            "MANIFEST_PREFLIGHT",
            "SECURITY_QUARANTINE",
            "OPERATOR_ACCEPTANCE",
        ])
        for step in report["review_steps"]:
            self.assertTrue(step["blocks_gap_closure"])
            self.assertIn("reason_code", step)
        for field in (
            "evidence_file_content_read",
            "evidence_artifact_hash_recomputed",
            "secret_pattern_content_scan_performed",
            "current_evidence_write_allowed",
            "gap_closure_allowed_by_this_patch",
            "live_ready_write_allowed",
            "live_config_mutation_allowed",
            "credential_values_read",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            self.assertFalse(report[field])
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_review_queue_report(
                report,
                manifest,
                template,
                quarantine,
                state,
            ),
            [],
        )

    def test_structural_error_routes_to_repair_without_acceptance(self):
        manifest, template, quarantine, state = self.source_inputs()
        manifest = copy.deepcopy(manifest)
        quarantine = copy.deepcopy(quarantine)
        manifest["manifest_preflight_status"] = "BLOCKED_MANIFEST_STRUCTURAL_ERRORS"
        manifest["manifest_item_count"] = 32
        manifest["missing_manifest_item_count"] = 0
        quarantine["quarantine_status"] = "QUARANTINE_BLOCKED_STRUCTURAL_ERRORS"
        report = self.build_report(manifest_preflight_report=manifest, security_quarantine_report=quarantine)

        self.assertEqual(report["review_queue_status"], "BLOCKED_OPERATOR_SUBMISSION_STRUCTURAL_ERRORS")
        self.assertEqual(report["single_next_operator_step"], "REPAIR_OPERATOR_SUBMISSION_MANIFEST_STRUCTURE")
        self.assertFalse(report["operator_submission_accepted"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_review_queue_report(
                report,
                manifest,
                template,
                quarantine,
                state,
            ),
            [],
        )

    def test_structural_review_still_waits_for_separate_review(self):
        manifest, template, quarantine, state = self.source_inputs()
        manifest = copy.deepcopy(manifest)
        quarantine = copy.deepcopy(quarantine)
        manifest["manifest_preflight_status"] = "BLOCKED_MANIFEST_STRUCTURAL_REVIEW_ONLY"
        manifest["operator_submission_present"] = True
        manifest["manifest_item_count"] = 32
        manifest["missing_manifest_item_count"] = 0
        manifest["manifest_control_count"] = 4
        manifest["missing_control_count"] = 0
        quarantine["quarantine_status"] = "QUARANTINE_STRUCTURAL_REVIEW_ONLY_NOT_ACCEPTED"
        report = self.build_report(manifest_preflight_report=manifest, security_quarantine_report=quarantine)

        self.assertEqual(report["review_queue_status"], "BLOCKED_OPERATOR_SUBMISSION_REVIEW_ONLY_NOT_ACCEPTED")
        self.assertEqual(report["single_next_operator_step"], "WAIT_FOR_SEPARATE_OPERATOR_RECONCILIATION_REVIEW")
        self.assertTrue(report["operator_submission_present"])
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["operator_submission_accepted"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])

    def test_validator_rejects_live_or_acceptance_drift(self):
        manifest, template, quarantine, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["operator_submission_accepted"] = True
        tampered["current_evidence_write_allowed"] = True
        tampered["evidence_file_content_read"] = True
        tampered["live_order_allowed"] = True
        tampered["review_ready_phase_count"] = 1
        tampered["report_hash"] = "0" * 64

        errors = validate_residual_operator_reconciliation_submission_review_queue_report(
            tampered,
            manifest,
            template,
            quarantine,
            state,
        )
        self.assertTrue(any("operator_submission_accepted" in error for error in errors))
        self.assertTrue(any("current_evidence_write_allowed" in error for error in errors))
        self.assertTrue(any("evidence_file_content_read" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("ready or accepted phases" in error for error in errors))
        self.assertTrue(any("report_hash" in error for error in errors))

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not REVIEW_QUEUE_REPORT_PATH.exists():
            self.skipTest("submission review queue report has not been generated yet")
        manifest, template, quarantine, state = self.source_inputs()
        report = load_json(REVIEW_QUEUE_REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_review_queue_report(
                report,
                manifest,
                template,
                quarantine,
                state,
            ),
            [],
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_route(self):
        if not PATCH_PATH.exists():
            self.skipTest("submission review queue patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(REVIEW_QUEUE_REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE_20260506_001",
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
