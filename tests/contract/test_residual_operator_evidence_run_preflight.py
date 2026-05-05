import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_evidence_run_preflight import (
    build_residual_operator_evidence_run_preflight_report,
    validate_residual_operator_evidence_run_preflight_report,
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
PREFLIGHT_REPORT_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-RUN-PREFLIGHT"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorEvidenceRunPreflightTest(unittest.TestCase):
    def source_inputs(self):
        return load_json(EXECUTION_GUIDE_PATH), load_json(PROGRESS_REPORT_PATH), load_json(STATE_PATH)

    def build_report(self):
        execution_guide_report, progress_report, state = self.source_inputs()
        return build_residual_operator_evidence_run_preflight_report(
            execution_guide_report,
            progress_report,
            state,
            root=ROOT,
            patch_id="TEST_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_preflight_binds_operator_run_command_without_running_it(self):
        execution_guide_report, progress_report, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["preflight_status"], "NON_LIVE_OPERATOR_RUN_PRECHECK_PASS")
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["command_id"], "UPBIT_PAPER_SAFE_MONITOR_120H")
        self.assertEqual(report["command_shell"], "powershell")
        self.assertEqual(report["command_scope"], "UPBIT/KRW_SPOT/PAPER")
        self.assertEqual(report["command_entrypoint"], "UPBIT_PAPER.py")
        self.assertIn("python -B UPBIT_PAPER.py", report["command_text"])
        self.assertEqual(report["minimum_duration_hours"], 120)
        self.assertEqual(report["minimum_paper_shadow_window_count"], 20)
        self.assertEqual(report["expected_heartbeat_ticks"], 43200)
        self.assertEqual(report["heartbeat_interval_seconds"], 10)
        self.assertGreaterEqual(len(report["expected_runtime_artifacts"]), 5)
        self.assertGreaterEqual(len(report["required_validator_ids"]), 6)
        self.assertEqual(report["preflight_blocked_count"], 0)
        self.assertTrue(report["non_live_operator_command_preflight_passed"])
        self.assertFalse(report["credential_values_read"])
        self.assertFalse(report["credential_environment_inspection_performed"])
        self.assertFalse(report["command_executed_by_this_patch"])
        self.assertFalse(report["operator_run_started_by_this_patch"])
        self.assertFalse(report["operator_run_completed_by_this_patch"])
        self.assertFalse(report["operator_run_evidence_ready_for_mvp5"])
        self.assertTrue(report["mvp5_entry_blocked_until_operator_evidence"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["live_config_mutation_allowed"])
        self.assertFalse(report["live_ready_write_allowed"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])
            self.assertFalse(progress_report[field])
            self.assertFalse(execution_guide_report[field])

        validators = set(report["required_validator_ids"])
        self.assertIn("upbit_paper_persistent_loop_validator", validators)
        self.assertIn("shadow_observation_persistent_runtime_validator", validators)
        self.assertIn("paper_shadow_evidence_accumulation_validator", validators)
        self.assertIn("profitability_evidence_maturity_rollup_validator", validators)
        self.assertIn("runtime_schema_instance_validator", validators)
        self.assertIn("live_final_guard_validator", validators)

        self.assertEqual(
            validate_residual_operator_evidence_run_preflight_report(
                report,
                execution_guide_report,
                progress_report,
                state,
            ),
            [],
        )

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not PREFLIGHT_REPORT_PATH.exists():
            self.skipTest("residual operator evidence run preflight report has not been generated yet")
        execution_guide_report, progress_report, state = self.source_inputs()
        report = load_json(PREFLIGHT_REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_evidence_run_preflight_report(
                report,
                execution_guide_report,
                progress_report,
                state,
            ),
            [],
        )
        self.assertFalse(report["command_executed_by_this_patch"])
        self.assertFalse(report["operator_run_completed_by_this_patch"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])

    def test_generated_patch_preserves_residual_route_and_blockers(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual operator evidence run preflight patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(PREFLIGHT_REPORT_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT_20260505_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["preflight_status"], "NON_LIVE_OPERATOR_RUN_PRECHECK_PASS")
        self.assertEqual(report["open_gap_ids"], state["open_contract_gap_ids"])
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_live_permission_and_run_completion_claim(self):
        execution_guide_report, progress_report, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["live_order_allowed"] = True
        tampered["live_ready_write_allowed"] = True
        tampered["command_executed_by_this_patch"] = True
        tampered["operator_run_completed_by_this_patch"] = True
        tampered["operator_run_evidence_ready_for_mvp5"] = True
        tampered["expected_runtime_artifacts"][0]["evidence_ready_for_closure"] = True

        errors = validate_residual_operator_evidence_run_preflight_report(
            tampered,
            execution_guide_report,
            progress_report,
            state,
        )
        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("live_ready_write_allowed" in error for error in errors))
        self.assertTrue(any("command_executed_by_this_patch" in error for error in errors))
        self.assertTrue(any("operator_run_completed_by_this_patch" in error for error in errors))
        self.assertTrue(any("operator_run_evidence_ready_for_mvp5" in error for error in errors))
        self.assertTrue(any("ready for closure" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
