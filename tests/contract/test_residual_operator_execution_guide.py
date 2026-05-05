import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_execution_guide import (
    build_residual_operator_execution_guide_report,
    validate_residual_operator_execution_guide_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
HANDOFF_REPORT_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET.report.json"
)
EXECUTION_GUIDE_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-EXECUTION-GUIDE"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorExecutionGuideTest(unittest.TestCase):
    def source_inputs(self):
        return load_json(HANDOFF_REPORT_PATH), load_json(STATE_PATH)

    def build_report(self):
        handoff_report, state = self.source_inputs()
        return build_residual_operator_execution_guide_report(
            handoff_report,
            state,
            patch_id="TEST_RESIDUAL_OPERATOR_EXECUTION_GUIDE",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_execution_guide_covers_residual_gaps_without_closing(self):
        handoff_report, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["covered_gap_count"], 13)
        self.assertEqual(report["handoff_packet_count"], 6)
        self.assertEqual(report["execution_step_count"], 6)
        self.assertEqual(report["local_paper_shadow_runtime_step_count"], 1)
        self.assertEqual(report["external_or_policy_evidence_step_count"], 2)
        self.assertTrue(report["operator_runtime_required_before_mvp5"])
        self.assertTrue(report["mvp5_entry_blocked_until_operator_evidence"])
        self.assertEqual(report["binance_runtime_status"], "SCAFFOLD_ONLY_NOT_ELIGIBLE_FOR_READINESS")
        self.assertEqual(report["guide_status"], "BLOCKED_GUIDE_ONLY")
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["live_config_mutation_allowed"])
        self.assertFalse(report["live_ready_write_allowed"])

        steps_by_action = {step["action_class"]: step for step in report["execution_steps"]}
        runtime_step = steps_by_action["PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION"]
        self.assertEqual(runtime_step["operator_action_mode"], "LOCAL_PAPER_SHADOW_RUNTIME_ALLOWED")
        self.assertEqual(runtime_step["minimum_observation_hours"], 48)
        self.assertEqual(runtime_step["minimum_paper_shadow_window_count"], 8)
        self.assertEqual(len(runtime_step["allowed_local_commands"]), 1)
        command = runtime_step["allowed_local_commands"][0]
        self.assertEqual(command["command_id"], "UPBIT_PAPER_SAFE_MONITOR_48H")
        self.assertEqual(command["shell"], "powershell")
        self.assertIn("UPBIT_PAPER.py", command["command"])
        self.assertEqual(command["minimum_duration_hours"], 48)
        self.assertTrue(command["non_live_only"])
        self.assertFalse(command["credential_required"])
        self.assertFalse(command["live_order_allowed"])

        for action_class, step in steps_by_action.items():
            if action_class != "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION":
                self.assertEqual(step["allowed_local_commands"], [])
            self.assertEqual(step["execution_status"], "BLOCKED_GUIDE_ONLY")
            self.assertFalse(step["evidence_ready_for_closure"])
            self.assertFalse(step["current_evidence_write_allowed"])
            self.assertFalse(step["gap_closure_allowed_by_this_patch"])
            self.assertFalse(step["live_order_ready"])
            self.assertFalse(step["live_order_allowed"])
            self.assertFalse(step["can_live_trade"])
            self.assertFalse(step["scale_up_allowed"])

        self.assertEqual(validate_residual_operator_execution_guide_report(report, handoff_report, state), [])

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not EXECUTION_GUIDE_PATH.exists():
            self.skipTest("residual operator execution guide report has not been generated yet")
        handoff_report, state = self.source_inputs()
        report = load_json(EXECUTION_GUIDE_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(validate_residual_operator_execution_guide_report(report, handoff_report, state), [])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_route_and_blockers(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual operator execution guide patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(EXECUTION_GUIDE_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE_20260505_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["guide_status"], "BLOCKED_GUIDE_ONLY")
        self.assertEqual(report["open_gap_ids"], state["open_contract_gap_ids"])
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_live_permission_and_forbidden_command(self):
        handoff_report, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["live_order_allowed"] = True
        tampered["execution_steps"][0]["live_order_allowed"] = True
        runtime_step = next(
            step
            for step in tampered["execution_steps"]
            if step["action_class"] == "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION"
        )
        runtime_step["allowed_local_commands"][0]["command"] += " --use LIVE_API_KEY"

        errors = validate_residual_operator_execution_guide_report(tampered, handoff_report, state)
        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("live/API key" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
