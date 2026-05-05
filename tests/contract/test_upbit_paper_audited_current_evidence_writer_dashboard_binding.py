import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING.patch_result.json"
)
STAGE_GATE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "stage_gates"
    / "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING.stage_gate_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-AUDITED-CURRENT-EVIDENCE-WRITER-DASHBOARD-BINDING"
NEXT_TASK = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperAuditedCurrentEvidenceWriterDashboardBindingContractTest(unittest.TestCase):
    def test_patch_result_binds_audited_writer_dashboard_without_live_or_scale(self):
        patch_result = load_json(PATCH_PATH)
        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING_20260505_001",
        )
        self.assertEqual(patch_result["task_class"], "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK)
        self.assertIn(REQUIREMENT_ID, patch_result["affected_contract_ids"])

        required = set(patch_result["validators_required"])
        run_status = {item["validator_id"]: item["status"] for item in patch_result["validators_run"]}
        for validator_id in (
            "read_only_dashboard_validator",
            "dashboard_visual_layout_validator",
            "upbit_paper_repaired_current_evidence_audited_writer_validator",
            "patch_result_runtime_schema_instance_validator",
            "live_final_guard_validator",
        ):
            self.assertIn(validator_id, required)
            self.assertEqual(run_status.get(validator_id), "PASS")

        test_commands = " ".join(item["command"] for item in patch_result["tests_run"])
        self.assertIn("test_dashboard_projects_audited_current_evidence_writer_portfolio_truth", test_commands)
        self.assertIn("test_launcher_dashboard_loads_audited_current_evidence_portfolio_truth", test_commands)
        for field in (
            "live_order_ready_after",
            "live_order_allowed_after",
            "can_live_trade_after",
            "scale_up_allowed_after",
        ):
            self.assertFalse(patch_result[field])

    def test_stage_gate_records_verified_paper_truth_but_no_runtime_write(self):
        stage_gate = load_json(STAGE_GATE_PATH)
        self.assertEqual(
            stage_gate["stage_gate_status"],
            "PASS_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BOUND_PAPER_ONLY",
        )
        self.assertEqual(stage_gate["writer_validation_status"], "PASS")
        self.assertEqual(stage_gate["dashboard_portfolio_status"], "VERIFIED")
        self.assertEqual(stage_gate["dashboard_portfolio_source"], "audited_current_evidence_snapshot.json")
        self.assertEqual(stage_gate["current_evidence_snapshot_status"], "PASS")
        self.assertFalse(stage_gate["repo_system_runtime_written"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(stage_gate[field])

    def test_current_state_advances_after_dashboard_binding_and_stays_live_blocked(self):
        state = load_json(STATE_PATH)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        if (state["last_patch_id"].startswith("MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_PAPER_PORTFOLIO_CURRENT_TRUTH_UX_")):
            expected_next_task = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK_"):
            expected_next_task = "MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK_"):
            expected_next_task = "MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK_"):
            expected_next_task = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK_"):
            expected_next_task = "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK_"):
            expected_next_task = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING_"):
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK)
        else:
            self.assertNotEqual(state["next_allowed_task_class"], "")
        self.assertIn("PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY", state["open_contract_gap_ids"])
        self.assertIn("LIVE_ENABLING_EVIDENCE_MISSING", state["open_contract_gap_ids"])
        self.assertIn("SCALE_UP_NOT_ELIGIBLE", state["open_contract_gap_ids"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])


if __name__ == "__main__":
    unittest.main()
