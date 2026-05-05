import json
import unittest
from pathlib import Path

from trader1.reports.residual_operator_evidence_intake_audit import (
    NEXT_TASK_CLASS,
    build_residual_operator_evidence_intake_audit_report,
    validate_residual_operator_evidence_intake_audit_report,
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
PROGRESS_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
)
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
INTAKE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-INTAKE-AUDIT"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorEvidenceIntakeAuditTest(unittest.TestCase):
    def source_inputs(self):
        return load_json(PREFLIGHT_PATH), load_json(PROGRESS_PATH), load_json(STATE_PATH)

    def build_report(self):
        preflight, progress, state = self.source_inputs()
        return build_residual_operator_evidence_intake_audit_report(
            preflight,
            progress,
            state,
            root=ROOT,
            patch_id="MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT_TEST",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="F" * 64,
            agents_sha256="A" * 64,
        )

    def test_intake_audit_blocks_until_operator_submission_package(self):
        preflight, progress, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["intake_status"], "BLOCKED_AWAITING_OPERATOR_EVIDENCE_PACKAGE")
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["expected_artifact_count"], len(preflight["expected_runtime_artifacts"]))
        self.assertEqual(report["operator_submission_manifest_status"], "MISSING_OPERATOR_SUBMISSION_MANIFEST")
        self.assertTrue(report["operator_submission_required"])
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["intake_review_ready"])
        self.assertFalse(report["operator_run_evidence_ready_for_mvp5"])
        self.assertFalse(report["runtime_artifacts_staged_by_this_patch"])
        self.assertEqual({item["content_hash_recorded"] for item in report["expected_artifact_intake_items"]}, {False})
        self.assertEqual({item["review_ready"] for item in report["expected_artifact_intake_items"]}, {False})
        self.assertIn("paper_shadow_evidence_accumulation_validator", {item["validator_id"] for item in report["validator_queue"]})

        self.assertEqual(
            validate_residual_operator_evidence_intake_audit_report(report, preflight, progress, state),
            [],
        )

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not INTAKE_PATH.exists():
            self.skipTest("residual operator evidence intake audit report has not been generated yet")
        preflight, progress, state = self.source_inputs()
        report = load_json(INTAKE_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_evidence_intake_audit_report(report, preflight, progress, state),
            [],
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["live_ready_write_allowed"])

    def test_generated_patch_preserves_residual_route_and_blockers(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual operator evidence intake audit patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(INTAKE_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT_20260505_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["open_gap_ids"], state["open_contract_gap_ids"])
        self.assertEqual(report["intake_status"], "BLOCKED_AWAITING_OPERATOR_EVIDENCE_PACKAGE")
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])
        self.assertFalse(patch_result["intake_review_ready"])

    def test_validator_rejects_live_permission_or_ready_claim(self):
        preflight, progress, state = self.source_inputs()
        report = self.build_report()
        tampered = json.loads(json.dumps(report))
        tampered["live_order_allowed"] = True
        tampered["intake_review_ready"] = True
        tampered["operator_submission_validated"] = True
        tampered["operator_run_evidence_ready_for_mvp5"] = True
        tampered["expected_artifact_intake_items"][0]["content_hash_recorded"] = True
        tampered["expected_artifact_intake_items"][0]["review_ready"] = True

        errors = validate_residual_operator_evidence_intake_audit_report(
            tampered,
            preflight,
            progress,
            state,
        )

        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("intake_review_ready" in error for error in errors))
        self.assertTrue(any("operator_submission_validated" in error for error in errors))
        self.assertTrue(any("operator_run_evidence_ready_for_mvp5" in error for error in errors))
        self.assertTrue(any("content hash" in error for error in errors))
        self.assertTrue(any("review_ready" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
