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
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-PROGRESS-AUDIT"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorEvidenceProgressTest(unittest.TestCase):
    def source_inputs(self):
        return load_json(EXECUTION_GUIDE_PATH), load_json(STATE_PATH)

    def build_report(self):
        execution_guide_report, state = self.source_inputs()
        return build_residual_operator_evidence_progress_report(
            execution_guide_report,
            state,
            root=ROOT,
            patch_id="TEST_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_progress_report_tracks_required_evidence_without_closing(self):
        execution_guide_report, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["execution_step_count"], 6)
        self.assertEqual(report["evidence_item_count"], len(report["evidence_items"]))
        self.assertEqual(report["local_runtime_command_count"], 1)
        self.assertEqual(report["local_runtime_completed_count"], 0)
        self.assertEqual(report["minimum_observation_hours_required"], 120)
        self.assertFalse(report["operator_evidence_ready_for_mvp5"])
        self.assertFalse(report["any_evidence_item_ready_for_closure"])
        self.assertTrue(report["mvp5_entry_blocked_until_operator_evidence"])
        self.assertEqual(report["binance_runtime_status"], "SCAFFOLD_ONLY_NOT_ELIGIBLE_FOR_READINESS")
        self.assertEqual(report["progress_status"], "BLOCKED_EVIDENCE_MISSING")
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["live_config_mutation_allowed"])
        self.assertFalse(report["live_ready_write_allowed"])

        counted = (
            report["present_blocked_evidence_item_count"]
            + report["missing_operator_evidence_item_count"]
            + report["placeholder_pending_evidence_item_count"]
            + report["external_evidence_required_item_count"]
            + report["local_runtime_output_item_count"]
        )
        self.assertEqual(counted, report["evidence_item_count"])
        statuses = {item["path_status"] for item in report["evidence_items"]}
        self.assertIn("EXTERNAL_EVIDENCE_REQUIRED", statuses)
        self.assertTrue(
            {
                "MISSING_OPERATOR_EVIDENCE",
                "PLACEHOLDER_PATTERN_PENDING",
                "LOCAL_RUNTIME_OUTPUT_PRESENT_NOT_CLOSURE_READY",
                "LOCAL_RUNTIME_OUTPUT_MISSING",
            }
            & statuses
        )

        for item in report["evidence_items"]:
            self.assertTrue(item["blocks_mvp5_entry"])
            self.assertFalse(item["evidence_ready_for_closure"])
            self.assertFalse(item["current_evidence_write_allowed"])
            self.assertFalse(item["gap_closure_allowed_by_this_patch"])
            self.assertFalse(item["live_order_ready"])
            self.assertFalse(item["live_order_allowed"])
            self.assertFalse(item["can_live_trade"])
            self.assertFalse(item["scale_up_allowed"])

        command = report["local_runtime_commands"][0]
        self.assertEqual(command["command_id"], "UPBIT_PAPER_SAFE_MONITOR_120H")
        self.assertEqual(command["scope"], "UPBIT/KRW_SPOT/PAPER")
        self.assertEqual(command["command_status"], "NOT_RUN_BY_THIS_PATCH")
        self.assertTrue(command["non_live_only"])
        self.assertFalse(command["credential_required"])
        self.assertFalse(command["live_order_allowed"])
        self.assertFalse(command["evidence_ready_for_closure"])
        self.assertFalse(command["current_evidence_write_allowed"])
        self.assertFalse(command["gap_closure_allowed_by_this_patch"])
        self.assertFalse(command["scale_up_allowed"])

        self.assertEqual(validate_residual_operator_evidence_progress_report(report, execution_guide_report, state), [])

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
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
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_route_and_blockers(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual operator evidence progress patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(PROGRESS_REPORT_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT_20260505_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["progress_status"], "BLOCKED_EVIDENCE_MISSING")
        self.assertEqual(report["open_gap_ids"], state["open_contract_gap_ids"])
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_evidence_closure_and_live_permission(self):
        execution_guide_report, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["operator_evidence_ready_for_mvp5"] = True
        tampered["live_ready_write_allowed"] = True
        tampered["live_order_allowed"] = True
        tampered["evidence_items"][0]["evidence_ready_for_closure"] = True
        tampered["local_runtime_commands"][0]["live_order_allowed"] = True

        errors = validate_residual_operator_evidence_progress_report(tampered, execution_guide_report, state)
        self.assertTrue(any("operator_evidence_ready_for_mvp5" in error for error in errors))
        self.assertTrue(any("live_ready_write_allowed" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("ready for closure" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
