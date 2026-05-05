import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_evidence_audit_binding import (
    build_residual_operator_evidence_audit_binding_report,
    validate_residual_operator_evidence_audit_binding_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
CLASSIFICATION_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION.report.json"
)
ACTION_PLAN_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN.report.json"
)
PAPER_RERUN_READINESS_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS.report.json"
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
BINDING_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-AUDIT-BINDING"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorEvidenceAuditBindingTest(unittest.TestCase):
    def source_inputs(self):
        return (
            load_json(CLASSIFICATION_REPORT_PATH),
            load_json(ACTION_PLAN_REPORT_PATH),
            load_json(PAPER_RERUN_READINESS_REPORT_PATH),
            load_json(OPERATOR_RESOLUTION_AUDIT_REPORT_PATH),
            load_json(STATE_PATH),
        )

    def test_current_reports_bind_every_open_gap_without_closing(self):
        classification, action_plan, paper_rerun_readiness, operator_resolution_audit, state = self.source_inputs()
        report = build_residual_operator_evidence_audit_binding_report(
            classification,
            action_plan,
            paper_rerun_readiness,
            state,
            post_rerun_operator_resolution_audit_report=operator_resolution_audit,
            patch_id="TEST_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["bound_gap_count"], 13)
        self.assertEqual(report["unbound_gap_ids"], [])
        self.assertEqual(report["extra_bound_gap_ids"], [])
        self.assertEqual(report["duplicate_bound_gap_ids"], [])
        self.assertEqual(report["implementation_recheck_action_count"], 0)
        self.assertEqual(report["paper_ledger_rerun_readiness_status"], "BLOCKED_RECONCILIATION_REQUIRED")
        self.assertEqual(report["post_rerun_reconciliation_status"], "BLOCKED")
        self.assertEqual(report["current_evidence_bridge_status"], "BLOCKED_BY_POST_RERUN_CLOSURE")
        self.assertTrue(report["operator_resolution_audit_loaded"])
        self.assertEqual(report["operator_resolution_audit_status"], "UNRESOLVED_RECONCILIATION_REVIEW_ONLY")
        self.assertEqual(report["operator_resolution_audit_validation_status"], "PASS")
        self.assertEqual(report["operator_resolution_binding_status"], "BOUND_BLOCKED")
        self.assertEqual(report["operator_resolution_unresolved_item_count"], 8)
        self.assertEqual(report["operator_resolution_resolved_item_count"], 0)
        self.assertEqual(report["operator_resolution_controls_satisfied_count"], 0)
        self.assertEqual(report["operator_resolution_current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["operator_resolution_candidate_current_evidence_usable_count"], 0)
        self.assertEqual(report["operator_resolution_source_review_guidance_file_load_status"], "PASS")
        self.assertTrue(report["operator_resolution_source_review_guidance_file_hash_match"])
        self.assertEqual(report["operator_resolution_source_decision_audit_file_load_status"], "PASS")
        self.assertTrue(report["operator_resolution_source_decision_audit_file_hash_match"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertEqual(report["audit_binding_status"], "PASS_BOUND_BLOCKED")
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)

        action_classes = {binding["action_class"] for binding in report["audit_bindings"]}
        self.assertIn("OPERATOR_RECONCILIATION_ACTION", action_classes)
        self.assertIn("PAPER_LEDGER_RERUN_RECONCILIATION_ACTION", action_classes)
        for binding in report["audit_bindings"]:
            self.assertEqual(binding["audit_binding_status"], "BOUND_BLOCKED")
            self.assertFalse(binding["gap_closure_allowed_by_this_patch"])
            self.assertFalse(binding["current_evidence_write_allowed"])
            self.assertFalse(binding["live_order_allowed"])
            self.assertFalse(binding["live_config_mutation_allowed"])
            self.assertFalse(binding["scale_up_allowed"])

        self.assertEqual(
            validate_residual_operator_evidence_audit_binding_report(
                report,
                classification,
                action_plan,
                paper_rerun_readiness,
                state,
                operator_resolution_audit,
            ),
            [],
        )

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not BINDING_REPORT_PATH.exists():
            self.skipTest("residual operator evidence audit binding report has not been generated yet")
        classification, action_plan, paper_rerun_readiness, operator_resolution_audit, state = self.source_inputs()
        report = load_json(BINDING_REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_evidence_audit_binding_report(
                report,
                classification,
                action_plan,
                paper_rerun_readiness,
                state,
                operator_resolution_audit,
            ),
            [],
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_route(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual operator evidence audit binding patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(BINDING_REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_OPERATOR_RESOLUTION_AUDIT_BINDING_20260506_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_gap_closure_or_live_permission(self):
        classification, action_plan, paper_rerun_readiness, operator_resolution_audit, state = self.source_inputs()
        report = build_residual_operator_evidence_audit_binding_report(
            classification,
            action_plan,
            paper_rerun_readiness,
            state,
            post_rerun_operator_resolution_audit_report=operator_resolution_audit,
            patch_id="TEST_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

        tampered = copy.deepcopy(report)
        tampered["gap_closure_allowed_by_this_patch"] = True
        tampered["current_evidence_write_allowed"] = True
        tampered["live_order_allowed"] = True
        tampered["audit_bindings"][0]["gap_closure_allowed_by_this_patch"] = True

        errors = validate_residual_operator_evidence_audit_binding_report(
            tampered,
            classification,
            action_plan,
            paper_rerun_readiness,
            state,
            operator_resolution_audit,
        )
        self.assertTrue(any("gap_closure_allowed_by_this_patch" in error for error in errors))
        self.assertTrue(any("current_evidence_write_allowed" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))

    def test_validator_rejects_operator_resolution_source_binding_drift(self):
        classification, action_plan, paper_rerun_readiness, operator_resolution_audit, state = self.source_inputs()
        report = build_residual_operator_evidence_audit_binding_report(
            classification,
            action_plan,
            paper_rerun_readiness,
            state,
            post_rerun_operator_resolution_audit_report=operator_resolution_audit,
            patch_id="TEST_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

        tampered = copy.deepcopy(report)
        tampered["operator_resolution_source_decision_audit_file_hash_match"] = False
        tampered["operator_resolution_binding_status"] = "FAIL"
        tampered["report_hash"] = "0" * 64

        errors = validate_residual_operator_evidence_audit_binding_report(
            tampered,
            classification,
            action_plan,
            paper_rerun_readiness,
            state,
            operator_resolution_audit,
        )
        self.assertTrue(any("operator_resolution_source_decision_audit_file_hash_match" in error for error in errors))
        self.assertTrue(any("operator_resolution_binding_status" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
