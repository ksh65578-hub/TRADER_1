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
    / "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK.patch_result.json"
)
BLOCKED_REPAIR_PLAN_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_blocked_repair_plan_report.json"
)
REPAIR_QUEUE_PATH = (
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
REQUIREMENT_ID = "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK"
REGENERATED_REPAIR_REQUIREMENT_ID = (
    "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-"
    "RECONCILIATION-RECHECK"
)
STALE_LOOP_REGENERATION_REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-RECHECK"
STALE_LOOP_EXECUTION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-RECHECK"
)
STALE_LOOP_POST_REGENERATION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-RECONCILIATION-AFTER-REGENERATION-REQUIRED-RECHECK"
)
STALE_LOOP_OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-PENDING-RECHECK"
)
DASHBOARD_BINDING_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-AUDITED-CURRENT-EVIDENCE-WRITER-DASHBOARD-BINDING"
PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-RECHECK"
ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-COLLECTION-DEPTH-RECHECK"
)
PATCH_RESULT_VALIDATOR_BASELINE_RECONCILIATION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-BASELINE-RECONCILIATION-RECHECK"
)
COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_REQUIREMENT_ID = "REQ-MVP4-COMPLETED-RECHECK-ROUTE-DEPTH-GUARD"
COMPLETED_OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-OPEN-CONTRACT-GAP-IMPLEMENTATION-PRIORITY-RECHECK"
)
PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-IMPLEMENTATION-DEPTH-RECHECK"
)
BLOCKER = "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION"
NEXT_TASK = "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_RECHECK"
REGENERATED_NEXT_TASK = "MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK"
STALE_LOOP_EXECUTION_NEXT_TASK = "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK"
STALE_LOOP_POST_REGENERATION_NEXT_TASK = "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
STALE_LOOP_OPERATOR_QUEUE_PENDING_NEXT_TASK = "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK"
AUDITED_WRITER_DASHBOARD_NEXT_TASK = "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
AFTER_AUDITED_WRITER_DASHBOARD_NEXT_TASK = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
)
AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK = (
    "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK"
)
AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
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
def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class BlockedRepairPlanRequiresOperatorReconciliationRecheckTest(unittest.TestCase):
    def test_blocked_repair_plan_keeps_all_repair_lanes_operator_blocked(self):
        report = load_json(BLOCKED_REPAIR_PLAN_PATH)

        self.assertEqual(report["repair_plan_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], BLOCKER)
        self.assertIn(BLOCKER, report["blocker_codes"])
        self.assertEqual(report["repair_item_count"], 6)
        self.assertEqual(report["ledger_rollup_rebuild_ready_count"], 1)
        self.assertEqual(report["runtime_cycle_rerun_required_count"], 5)
        self.assertEqual(report["recovery_guard_rerun_required_count"], 1)
        self.assertEqual(report["missing_cycle_ledger_jsonl_total_count"], 10)
        self.assertEqual(report["missing_paper_ledger_rollup_artifact_count"], 6)
        self.assertFalse(report["current_evidence_mutation_allowed"])
        self.assertFalse(report["generated_artifact_mutation_allowed"])
        self.assertFalse(report["source_delete_allowed"])

        lanes = [item["safe_repair_lane"] for item in report["items"]]
        self.assertEqual(lanes.count("LEDGER_ROLLUP_REBUILD_READY"), 1)
        self.assertEqual(lanes.count("RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP"), 4)
        self.assertEqual(lanes.count("RECOVERY_GUARD_THEN_LEDGER_ROLLUP"), 1)
        for item in report["items"]:
            self.assertFalse(item["current_evidence_mutation_allowed"])
            self.assertFalse(item["source_delete_allowed"])
            self.assertFalse(item["live_permission_created"])
            for step in item["repair_steps"]:
                self.assertFalse(step["mutates_current_evidence"])
                self.assertFalse(step["live_permission_created"])

    def test_repair_operator_queue_preserves_same_blocked_scope_without_current_evidence(self):
        queue = load_json(REPAIR_QUEUE_PATH)

        self.assertEqual(queue["queue_status"], "BLOCKED")
        self.assertEqual(queue["queue_item_count"], 6)
        self.assertEqual(queue["ledger_candidate_review_ready_count"], 1)
        self.assertEqual(queue["runtime_cycle_rerun_required_count"], 5)
        self.assertEqual(queue["recovery_guard_rerun_required_count"], 1)
        self.assertEqual(queue["candidate_current_evidence_usable_count"], 0)
        self.assertFalse(queue["current_evidence_mutation_allowed"])
        self.assertFalse(queue["persistent_loop_mutation_allowed"])
        self.assertFalse(queue["source_delete_allowed"])
        self.assertFalse(queue["live_order_allowed"])
        self.assertFalse(queue["scale_up_allowed"])

    def test_recheck_patch_routes_to_regenerated_blocked_repair_gap_without_resolving_blockers(self):
        if not PATCH_PATH.exists():
            self.skipTest("blocked repair plan recheck patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK)
        self.assertIn(BLOCKER, patch_result["remaining_blockers"])
        self.assertIn(
            "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
            patch_result["remaining_blockers"],
        )
        self.assertEqual(patch_result["blocked_repair_plan_status"], "BLOCKED")
        self.assertEqual(patch_result["blocked_repair_plan_item_count"], 6)
        self.assertEqual(patch_result["blocked_repair_plan_ledger_rollup_rebuild_ready_count"], 1)
        self.assertEqual(patch_result["blocked_repair_plan_runtime_cycle_rerun_required_count"], 5)
        self.assertEqual(patch_result["blocked_repair_plan_recovery_guard_rerun_required_count"], 1)
        self.assertEqual(patch_result["repair_operator_queue_status"], "BLOCKED")
        self.assertEqual(patch_result["repair_operator_queue_candidate_current_evidence_usable_count"], 0)

        completed = set(state["completed_requirement_ids"])
        if (state["last_patch_id"].startswith("MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_BLOCKER_SUMMARY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING_") or state["last_patch_id"].startswith("MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_OPERATOR_HANDOFF_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT_")):
            expected_next_task = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif (state["last_patch_id"].startswith("MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_PAPER_PORTFOLIO_CURRENT_TRUTH_UX_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_OPERATOR_FOCUS_SIMPLIFICATION_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_LIVE_AVAILABILITY_REASON_")))):
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
        elif STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK)
        elif COMPLETED_OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK)
        elif COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK)
        elif PATCH_RESULT_VALIDATOR_BASELINE_RECONCILIATION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK)
        elif ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK)
        elif PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK)
        elif DASHBOARD_BINDING_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_AUDITED_WRITER_DASHBOARD_NEXT_TASK)
        elif STALE_LOOP_OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AUDITED_WRITER_DASHBOARD_NEXT_TASK)
        elif STALE_LOOP_POST_REGENERATION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], STALE_LOOP_OPERATOR_QUEUE_PENDING_NEXT_TASK)
        elif STALE_LOOP_EXECUTION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], STALE_LOOP_POST_REGENERATION_NEXT_TASK)
        elif STALE_LOOP_REGENERATION_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], STALE_LOOP_EXECUTION_NEXT_TASK)
        elif REGENERATED_REPAIR_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], REGENERATED_NEXT_TASK)
        elif REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK)
        self.assertIn(BLOCKER, state["open_contract_gap_ids"])
        self.assertIn(
            "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
            state["open_contract_gap_ids"],
        )
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


if __name__ == "__main__":
    unittest.main()
