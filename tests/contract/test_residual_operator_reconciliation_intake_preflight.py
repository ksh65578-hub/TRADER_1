import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_reconciliation_intake_preflight import (
    build_residual_operator_reconciliation_intake_preflight_report,
    validate_residual_operator_reconciliation_intake_preflight_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
REVIEW_CARDS_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS.report.json"
)
EVIDENCE_INTAKE_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT.report.json"
)
INTAKE_PREFLIGHT_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-INTAKE-PREFLIGHT"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorReconciliationIntakePreflightTest(unittest.TestCase):
    def source_inputs(self):
        return (
            load_json(REVIEW_CARDS_REPORT_PATH),
            load_json(EVIDENCE_INTAKE_REPORT_PATH),
            load_json(STATE_PATH),
        )

    def build_report(self):
        review_cards_report, evidence_intake_report, state = self.source_inputs()
        return build_residual_operator_reconciliation_intake_preflight_report(
            review_cards_report,
            evidence_intake_report,
            state,
            root=ROOT,
            patch_id="TEST_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT",
            generated_at_utc="2026-05-06T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_reconciliation_intake_preflight_blocks_manifestless_review_cards(self):
        review_cards_report, evidence_intake_report, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["preflight_status"], "BLOCKED_RECONCILIATION_INTAKE_PACKAGE_MISSING")
        self.assertEqual(report["review_cards_source_status"], "BLOCKED_RECONCILIATION_REVIEW_ONLY")
        self.assertTrue(report["review_cards_source_hashes_verified"])
        self.assertEqual(report["review_card_count"], 8)
        self.assertEqual(report["blocked_review_card_count"], 8)
        self.assertEqual(report["review_ready_count"], 0)
        self.assertEqual(report["control_card_count"], 4)
        self.assertEqual(report["unsatisfied_control_count"], 4)
        self.assertEqual(report["satisfied_control_count"], 0)
        self.assertEqual(report["operator_resolution_current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["operator_resolution_candidate_current_evidence_usable_count"], 0)
        self.assertEqual(
            report["operator_reconciliation_submission_manifest_path"],
            "system/evidence/operator_submissions/residual_operator_reconciliation_submission_manifest.json",
        )
        self.assertIn(
            report["operator_reconciliation_submission_manifest_status"],
            {"MISSING_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST", "PRESENT_NOT_VALIDATED"},
        )
        self.assertTrue(report["operator_submission_required"])
        self.assertFalse(report["operator_submission_validated"])
        self.assertEqual(report["required_intake_item_count"], 32)
        self.assertEqual(report["missing_intake_item_count"], 32)
        self.assertEqual(report["ready_for_review_intake_item_count"], 0)
        self.assertEqual(report["accepted_intake_item_count"], 0)
        self.assertEqual(report["control_requirement_count"], 4)
        self.assertEqual(report["unsatisfied_control_requirement_count"], 4)
        self.assertEqual(report["paper_shadow_operator_evidence_intake_status"], "BLOCKED_AWAITING_OPERATOR_EVIDENCE_PACKAGE")
        self.assertTrue(report["operator_no_action_needed_for_next_non_live_patch"])
        self.assertTrue(report["operator_action_required_for_gap_closure"])

        first = report["single_next_intake_item"]
        self.assertEqual(first["priority_order"], 1)
        self.assertEqual(first["intake_item_status"], "MISSING_OPERATOR_RECONCILIATION_EVIDENCE")
        self.assertEqual(first["resolution_reason_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertTrue(first["operator_submission_required"])
        self.assertFalse(first["operator_submission_validated"])
        self.assertFalse(first["review_ready"])
        self.assertFalse(first["accepted_for_reconciliation"])
        self.assertTrue(first["blocks_gap_closure"])
        self.assertFalse(first["current_evidence_write_allowed"])
        self.assertFalse(first["live_ready_write_allowed"])
        self.assertFalse(first["live_order_allowed"])
        self.assertFalse(first["scale_up_allowed"])

        for item in report["intake_items"]:
            self.assertEqual(item["intake_item_status"], "MISSING_OPERATOR_RECONCILIATION_EVIDENCE")
            self.assertFalse(item["operator_submission_validated"])
            self.assertFalse(item["source_hash_recorded"])
            self.assertFalse(item["review_ready"])
            self.assertFalse(item["accepted_for_reconciliation"])
            self.assertFalse(item["current_evidence_write_allowed"])
            self.assertFalse(item["gap_closure_allowed_by_this_patch"])
            self.assertFalse(item["live_order_ready"])
            self.assertFalse(item["live_order_allowed"])
            self.assertFalse(item["can_live_trade"])
            self.assertFalse(item["scale_up_allowed"])

        for control in report["control_requirements"]:
            self.assertEqual(control["control_status"], "UNSATISFIED_RECONCILIATION_INTAKE_CONTROL")
            self.assertEqual(control["source_control_status"], "UNSATISFIED_BLOCKING_CONTROL")
            self.assertTrue(control["required"])
            self.assertFalse(control["satisfied"])
            self.assertFalse(control["current_evidence_write_allowed"])
            self.assertFalse(control["live_order_allowed"])
            self.assertFalse(control["scale_up_allowed"])

        self.assertEqual(
            validate_residual_operator_reconciliation_intake_preflight_report(
                report,
                review_cards_report,
                evidence_intake_report,
                state,
            ),
            [],
        )

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not INTAKE_PREFLIGHT_REPORT_PATH.exists():
            self.skipTest("residual operator reconciliation intake preflight report has not been generated yet")
        review_cards_report, evidence_intake_report, state = self.source_inputs()
        report = load_json(INTAKE_PREFLIGHT_REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_reconciliation_intake_preflight_report(
                report,
                review_cards_report,
                evidence_intake_report,
                state,
            ),
            [],
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_route(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual operator reconciliation intake preflight patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(INTAKE_PREFLIGHT_REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT_20260506_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_ready_or_permission_drift(self):
        review_cards_report, evidence_intake_report, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["review_cards_source_hashes_verified"] = False
        tampered["operator_submission_validated"] = True
        tampered["ready_for_review_intake_item_count"] = 1
        tampered["intake_items"][0]["current_evidence_write_allowed"] = True
        tampered["intake_items"][0]["review_ready"] = True
        tampered["intake_items"][0]["accepted_for_reconciliation"] = True
        tampered["control_requirements"][0]["satisfied"] = True
        tampered["live_ready_write_allowed"] = True
        tampered["report_hash"] = "0" * 64

        errors = validate_residual_operator_reconciliation_intake_preflight_report(
            tampered,
            review_cards_report,
            evidence_intake_report,
            state,
        )
        self.assertTrue(any("source hashes" in error for error in errors))
        self.assertTrue(any("operator_submission_validated" in error for error in errors))
        self.assertTrue(any("ready or accepted" in error for error in errors))
        self.assertTrue(any("forbidden permission" in error for error in errors))
        self.assertTrue(any("live_ready_write_allowed" in error for error in errors))
        self.assertTrue(any("report_hash" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
