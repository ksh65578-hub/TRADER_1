import json
import unittest
from pathlib import Path

from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY-SCHEMA-STATE-SYNC"
PATCH_BASENAME = "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_SCHEMA_STATE_SYNC"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"

RESIDUAL_SCHEMA_FILES = {
    "trader1.residual_mvp5_entry_duration_policy_report.v1": (
        "contracts/schema/residual_mvp5_entry_duration_policy_report.schema.json"
    ),
    "trader1.residual_operator_evidence_intake_audit_report.v1": (
        "contracts/schema/residual_operator_evidence_intake_audit_report.schema.json"
    ),
    "trader1.residual_operator_evidence_run_preflight_report.v1": (
        "contracts/schema/residual_operator_evidence_run_preflight_report.schema.json"
    ),
    "trader1.residual_operator_evidence_trial_duration_policy_report.v1": (
        "contracts/schema/residual_operator_evidence_trial_duration_policy_report.schema.json"
    ),
}

RESIDUAL_REPORT_FILES = {
    "trader1.residual_mvp5_entry_duration_policy_report.v1": (
        "system/evidence/audit_reports/MVP4_RESIDUAL_MVP5_ENTRY_DURATION_POLICY.report.json"
    ),
    "trader1.residual_operator_evidence_intake_audit_report.v1": (
        "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT.report.json"
    ),
    "trader1.residual_operator_evidence_run_preflight_report.v1": (
        "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT.report.json"
    ),
    "trader1.residual_operator_evidence_trial_duration_policy_report.v1": (
        "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY.report.json"
    ),
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualAdaptiveEvidenceSchemaStateSyncTest(unittest.TestCase):
    def test_residual_operator_evidence_schema_ids_are_in_current_state(self):
        state = load_json(STATE_PATH)
        implemented = set(state["implemented_schema_ids"])

        for schema_id, rel_path in RESIDUAL_SCHEMA_FILES.items():
            schema_path = ROOT / rel_path
            self.assertTrue(schema_path.exists(), rel_path)
            schema = load_json(schema_path)
            self.assertEqual(schema["$id"], schema_id)
            self.assertIn(schema_id, implemented)

    def test_generated_residual_reports_are_schema_bound(self):
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")

        for schema_id, rel_path in RESIDUAL_REPORT_FILES.items():
            report_path = ROOT / rel_path
            self.assertTrue(report_path.exists(), rel_path)
            report = load_json(report_path)
            if "schema_id" in report:
                self.assertEqual(report["schema_id"], schema_id)
            schema = schema_for_instance(report, schema_bundle)
            self.assertIsNotNone(schema, rel_path)
            result = validate_instance_against_schema(report, schema, schema_bundle)
            self.assertEqual(result.status, "PASS", result.errors)

    def test_generated_patch_preserves_residual_route_and_live_blocks(self):
        patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
        if not patch_path.exists():
            self.skipTest("residual schema state sync patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(patch_path)

        if state["last_patch_id"] == PATCH_ID:
            self.assertEqual(state["last_patch_result_hash"], patch_result["result_hash"])
        else:
            self.assertTrue(
                (state["last_patch_id"].startswith("MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_GAP_ACTION_MAP_"))
                or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT_")
                or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_SECURITY_QUARANTINE_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE_")
            )
        self.assertEqual(patch_result["patch_id"], PATCH_ID)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(len(state["open_contract_gap_ids"]), 13)
        self.assertEqual(set(patch_result["remaining_blockers"]), set(state["open_contract_gap_ids"]))
        for schema_id in RESIDUAL_SCHEMA_FILES:
            self.assertIn(schema_id, patch_result["new_or_changed_schema_ids"])

        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])
        self.assertFalse(patch_result["operator_run_started_by_this_patch"])
        self.assertFalse(patch_result["operator_run_completed_by_this_patch"])
        self.assertFalse(patch_result["operator_run_evidence_ready_for_mvp5"])

    def test_generated_read_maps_include_schema_state_sync_requirement(self):
        req_index = load_json(ROOT / "contracts" / "generated" / "requirement_index.json")
        matrix = load_json(ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json")
        req_rows = [item for item in req_index["requirements"] if item["requirement_id"] == REQUIREMENT_ID]
        matrix_rows = [item for item in matrix["rows"] if item["requirement_id"] == REQUIREMENT_ID]
        if not req_rows or not matrix_rows:
            self.skipTest("residual schema state sync generated maps have not been generated yet")

        self.assertEqual(len(req_rows), 1)
        self.assertEqual(len(matrix_rows), 1)
        req_row = req_rows[0]
        matrix_row = matrix_rows[0]
        for schema_id in RESIDUAL_SCHEMA_FILES:
            self.assertIn(schema_id, req_row["schema_ids"])
        for schema_file in RESIDUAL_SCHEMA_FILES.values():
            self.assertIn(schema_file, matrix_row["schema_files"])
        self.assertTrue(req_row["live_affecting"])
        self.assertTrue(matrix_row["live_affecting"])
        self.assertEqual(req_row["implementation_status"], "IMPLEMENTED_FAIL_CLOSED")
        self.assertEqual(matrix_row["status"], "IMPLEMENTED_FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
