import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_reconciliation_review_cards import (
    build_residual_operator_reconciliation_review_cards_report,
    validate_residual_operator_reconciliation_review_cards_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
AUDIT_BINDING_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING.report.json"
)
OPERATOR_RESOLUTION_AUDIT_REPORT_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_post_rerun_operator_resolution_audit_report.json"
)
REVIEW_CARDS_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-REVIEW-CARDS"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorReconciliationReviewCardsTest(unittest.TestCase):
    def source_inputs(self):
        return (
            load_json(AUDIT_BINDING_REPORT_PATH),
            load_json(OPERATOR_RESOLUTION_AUDIT_REPORT_PATH),
            load_json(STATE_PATH),
        )

    def build_report(self):
        audit_binding_report, operator_resolution_audit_report, state = self.source_inputs()
        return build_residual_operator_reconciliation_review_cards_report(
            audit_binding_report,
            operator_resolution_audit_report,
            state,
            patch_id="TEST_RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS",
            generated_at_utc="2026-05-06T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_review_cards_bind_source_audit_without_accepting_evidence(self):
        audit_binding_report, operator_resolution_audit_report, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["operator_reconciliation_gap_count"], 4)
        self.assertTrue(report["operator_resolution_audit_loaded"])
        self.assertEqual(report["operator_resolution_audit_status"], "UNRESOLVED_RECONCILIATION_REVIEW_ONLY")
        self.assertEqual(report["operator_resolution_audit_validation_status"], "PASS")
        self.assertEqual(report["operator_resolution_binding_status"], "BOUND_BLOCKED")
        self.assertTrue(report["source_hashes_verified"])
        self.assertEqual(report["operator_resolution_unresolved_item_count"], 8)
        self.assertEqual(report["operator_resolution_resolved_item_count"], 0)
        self.assertEqual(report["operator_resolution_controls_satisfied_count"], 0)
        self.assertEqual(report["operator_resolution_current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["operator_resolution_candidate_current_evidence_usable_count"], 0)
        self.assertEqual(report["review_card_count"], 8)
        self.assertEqual(report["blocked_review_card_count"], 8)
        self.assertEqual(report["review_ready_count"], 0)
        self.assertEqual(report["control_card_count"], 4)
        self.assertEqual(report["unsatisfied_control_count"], 4)
        self.assertEqual(report["satisfied_control_count"], 0)
        self.assertEqual(report["review_status"], "BLOCKED_RECONCILIATION_REVIEW_ONLY")
        self.assertTrue(report["operator_no_action_needed_for_next_non_live_patch"])
        self.assertTrue(report["operator_action_required_for_gap_closure"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["live_ready_write_allowed"])
        self.assertFalse(report["live_config_mutation_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

        first = report["single_next_review_card"]
        self.assertEqual(first["priority_order"], 1)
        self.assertEqual(first["review_status"], "BLOCKED_REVIEW_ONLY")
        self.assertEqual(first["cycle_id"], operator_resolution_audit_report["items"][0]["cycle_id"])
        self.assertEqual(first["decision_candidate_rollup_hash"], operator_resolution_audit_report["items"][0]["decision_candidate_rollup_hash"])
        self.assertFalse(first["resolution_evidence_present"])
        self.assertFalse(first["resolution_evidence_accepted"])
        self.assertFalse(first["candidate_current_evidence_usable"])
        self.assertFalse(first["current_evidence_write_allowed"])
        self.assertFalse(first["promotion_eligible"])
        self.assertFalse(first["live_order_allowed"])
        self.assertFalse(first["scale_up_allowed"])

        for card, source in zip(report["review_cards"], operator_resolution_audit_report["items"]):
            self.assertEqual(card["cycle_id"], source["cycle_id"])
            self.assertEqual(card["replacement_loop_id"], source["replacement_loop_id"])
            self.assertEqual(card["candidate_rollup_artifact_path"], source["candidate_rollup_artifact_path"])
            self.assertEqual(card["planned_current_ledger_jsonl_path"], source["planned_current_ledger_jsonl_path"])
            self.assertEqual(card["resolution_status"], "UNRESOLVED_CURRENT_EVIDENCE_BLOCKED")
            self.assertEqual(card["resolution_reason_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
            self.assertEqual(card["required_resolution_evidence_count"], 4)
            self.assertFalse(card["current_evidence_write_allowed"])
            self.assertFalse(card["live_order_ready"])
            self.assertFalse(card["live_order_allowed"])
            self.assertFalse(card["can_live_trade"])
            self.assertFalse(card["scale_up_allowed"])

        for control in report["control_cards"]:
            self.assertEqual(control["control_status"], "UNSATISFIED_BLOCKING_CONTROL")
            self.assertEqual(control["blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
            self.assertTrue(control["required"])
            self.assertFalse(control["satisfied"])
            self.assertFalse(control["current_evidence_write_allowed"])
            self.assertFalse(control["live_order_allowed"])
            self.assertFalse(control["scale_up_allowed"])

        self.assertEqual(
            validate_residual_operator_reconciliation_review_cards_report(
                report,
                audit_binding_report,
                operator_resolution_audit_report,
                state,
            ),
            [],
        )

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not REVIEW_CARDS_REPORT_PATH.exists():
            self.skipTest("residual operator reconciliation review cards report has not been generated yet")
        audit_binding_report, operator_resolution_audit_report, state = self.source_inputs()
        report = load_json(REVIEW_CARDS_REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_reconciliation_review_cards_report(
                report,
                audit_binding_report,
                operator_resolution_audit_report,
                state,
            ),
            [],
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_route(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual operator reconciliation review cards patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(REVIEW_CARDS_REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS_20260506_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_review_card_permission_or_source_drift(self):
        audit_binding_report, operator_resolution_audit_report, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["review_cards"][0]["live_order_allowed"] = True
        tampered["review_cards"][0]["current_evidence_write_allowed"] = True
        tampered["review_cards"][0]["decision_candidate_rollup_hash"] = "0" * 64
        tampered["control_cards"][0]["satisfied"] = True
        tampered["source_hashes_verified"] = False
        tampered["operator_resolution_current_evidence_write_allowed_count"] = 1
        tampered["report_hash"] = "0" * 64

        errors = validate_residual_operator_reconciliation_review_cards_report(
            tampered,
            audit_binding_report,
            operator_resolution_audit_report,
            state,
        )
        self.assertTrue(any("forbidden permission" in error for error in errors))
        self.assertTrue(any("decision_candidate_rollup_hash" in error for error in errors))
        self.assertTrue(any("satisfied" in error for error in errors))
        self.assertTrue(any("source_hashes_verified" in error for error in errors))
        self.assertTrue(any("write_allowed_count" in error for error in errors))
        self.assertTrue(any("report_hash" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
