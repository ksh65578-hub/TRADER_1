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
    / "MVP4_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD.patch_result.json"
)
STAGE_GATE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "stage_gates"
    / "MVP4_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD.stage_gate_result.json"
)
POST_REPAIR_REPORT_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_post_repair_reconciliation_report.json"
)
REPAIR_QUEUE_REPORT_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_repair_operator_queue_report.json"
)
REQUIREMENT_ID = "REQ-MVP4-COMPLETED-RECHECK-ROUTE-DEPTH-GUARD"
NEXT_TASK_CLASS = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
PRIORITY_RECHECK_REQUIREMENT_ID = "REQ-MVP4-OPEN-CONTRACT-GAP-IMPLEMENTATION-PRIORITY-RECHECK"
PRIORITY_RECHECK_NEXT_TASK_CLASS = "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK"
PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-IMPLEMENTATION-DEPTH-RECHECK"
)
PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK_CLASS = (
    "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK"
)
PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK"
)
ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK"
)
PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
)
POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-POST-RERUN-CURRENT-EVIDENCE-WRITE-BLOCKED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"
)
BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"
)
REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-RECONCILIATION-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
)
MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
COMPLETED_RECHECK_TASK_CLASSES = {
    "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK",
    "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK",
    "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK",
}
PREREQUISITE_REQUIREMENTS = {
    "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-BASELINE-RECONCILIATION-RECHECK",
    "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-RECHECK",
    "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK",
    "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class CompletedRecheckRouteDepthGuardTest(unittest.TestCase):
    def test_guard_routes_to_uncompleted_open_gap_priority_recheck(self):
        if not PATCH_PATH.exists():
            self.skipTest("completed recheck route-depth guard patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        stage_gate = load_json(STAGE_GATE_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_20260504_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        if state["last_patch_id"].startswith("MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK_"):
            expected_next_task = "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK_"):
            expected_next_task = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING_"):
            expected_next_task = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK_"):
            expected_next_task = "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
            self.assertEqual(
                state["next_allowed_task_class"],
                expected_next_task,
            )
            self.assertNotIn(
                "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING",
                state["open_contract_gap_ids"],
            )
        elif state["last_patch_id"].startswith("MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK_"):
            expected_next_task = "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(
                state["next_allowed_task_class"],
                PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK_CLASS,
            )
        elif PRIORITY_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], PRIORITY_RECHECK_NEXT_TASK_CLASS)
        else:
            self.assertEqual(state["last_patch_id"], "MVP4_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_20260504_001")
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(stage_gate["route_before_patch"], "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK")
        self.assertTrue(stage_gate["route_regression_detected"])
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertTrue(PREREQUISITE_REQUIREMENTS.issubset(set(state["completed_requirement_ids"])))
        self.assertNotIn(state["next_allowed_task_class"], COMPLETED_RECHECK_TASK_CLASSES)

        for gap_id in (
            "PATCH_RESULT_VALIDATOR_RUN_GAP",
            "POST_REPAIR_RECONCILIATION_REQUIRED",
            "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
            "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
            "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
            "LIVE_ENABLING_EVIDENCE_MISSING",
            "SCALE_UP_NOT_ELIGIBLE",
        ):
            self.assertIn(gap_id, state["open_contract_gap_ids"])
            self.assertIn(gap_id, patch_result["remaining_blockers"])

        for field in (
            "live_order_ready_after",
            "live_order_allowed_after",
            "can_live_trade_after",
            "scale_up_allowed_after",
            "convergence_live_order_allowed_after",
            "optimizer_live_order_allowed_after",
        ):
            self.assertFalse(patch_result[field])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])

    def test_guard_keeps_repair_candidates_review_only(self):
        post_repair = load_json(POST_REPAIR_REPORT_PATH)
        repair_queue = load_json(REPAIR_QUEUE_REPORT_PATH)

        self.assertEqual(post_repair["post_repair_reconciliation_status"], "BLOCKED")
        self.assertEqual(post_repair["candidate_current_evidence_usable_count"], 0)
        self.assertEqual(repair_queue["queue_status"], "BLOCKED")
        self.assertEqual(repair_queue["candidate_current_evidence_usable_count"], 0)
        self.assertFalse(post_repair["current_evidence_mutation_allowed"])
        self.assertFalse(repair_queue["current_evidence_mutation_allowed"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(post_repair[field])
            self.assertFalse(repair_queue[field])


if __name__ == "__main__":
    unittest.main()
