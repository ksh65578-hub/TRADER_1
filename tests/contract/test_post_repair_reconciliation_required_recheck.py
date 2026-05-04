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
    / "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK.patch_result.json"
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
REQUIREMENT_ID = "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-RECHECK"
HASH_MISMATCH_REQUIREMENT_ID = "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK"
BLOCKED_REPAIR_PLAN_REQUIREMENT_ID = "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK"
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
EXPECTED_NEXT_TASK = "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK"
EXPECTED_HASH_MISMATCH_NEXT_TASK = "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK"
EXPECTED_BLOCKED_REPAIR_PLAN_NEXT_TASK = (
    "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_RECHECK"
)
EXPECTED_REGENERATED_REPAIR_NEXT_TASK = "MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK"
EXPECTED_STALE_LOOP_REGENERATION_NEXT_TASK = "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK"
EXPECTED_STALE_LOOP_POST_REGENERATION_NEXT_TASK = (
    "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
)
EXPECTED_STALE_LOOP_OPERATOR_QUEUE_PENDING_NEXT_TASK = (
    "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK"
)
EXPECTED_AUDITED_WRITER_DASHBOARD_BINDING_NEXT_TASK = (
    "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
)
EXPECTED_AFTER_AUDITED_WRITER_DASHBOARD_BINDING_NEXT_TASK = (
    "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
)
EXPECTED_AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK = (
    "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
)
EXPECTED_AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
)
EXPECTED_AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK = (
    "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK"
)
EXPECTED_AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK = (
    "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
)
EXPECTED_AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK = (
    "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK"
)
EXPECTED_AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
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
def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PostRepairReconciliationRequiredRecheckTest(unittest.TestCase):
    def test_post_repair_report_remains_blocked_without_current_evidence(self):
        report = load_json(POST_REPAIR_REPORT_PATH)

        self.assertEqual(report["post_repair_reconciliation_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "POST_REPAIR_RECONCILIATION_REQUIRED")
        self.assertIn("POST_REPAIR_RECONCILIATION_REQUIRED", report["blocker_codes"])
        self.assertIn("REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED", report["blocker_codes"])
        self.assertEqual(report["source_loop_expected_rollup_hash_mismatch_count"], 1)
        self.assertEqual(report["hash_reconciliation_operator_action_required_count"], 1)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertFalse(report["current_evidence_mutation_allowed"])
        self.assertFalse(report["persistent_loop_mutation_allowed"])
        self.assertFalse(report["source_delete_allowed"])

        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])

    def test_recheck_patch_routes_to_hash_mismatch_gap_without_resolving_post_repair_gap(self):
        if not PATCH_PATH.exists():
            self.skipTest("post-repair reconciliation required recheck patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], EXPECTED_NEXT_TASK)
        self.assertIn("POST_REPAIR_RECONCILIATION_REQUIRED", patch_result["remaining_blockers"])
        self.assertIn("REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED", patch_result["remaining_blockers"])
        self.assertEqual(patch_result["post_repair_reconciliation_status"], "BLOCKED")
        self.assertEqual(patch_result["post_repair_source_loop_expected_rollup_hash_mismatch_count"], 1)
        self.assertEqual(patch_result["post_repair_candidate_current_evidence_usable_count"], 0)
        self.assertEqual(patch_result["candidate_current_evidence_usable_count"], 0)

        completed = set(state["completed_requirement_ids"])
        if ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(
                state["next_allowed_task_class"],
                EXPECTED_AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK,
            )
        elif COMPLETED_OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(
                state["next_allowed_task_class"],
                EXPECTED_AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK,
            )
        elif COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_REQUIREMENT_ID in completed:
            self.assertEqual(
                state["next_allowed_task_class"],
                EXPECTED_AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK,
            )
        elif PATCH_RESULT_VALIDATOR_BASELINE_RECONCILIATION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(
                state["next_allowed_task_class"],
                EXPECTED_AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK,
            )
        elif ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK)
        elif PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK)
        elif DASHBOARD_BINDING_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_AFTER_AUDITED_WRITER_DASHBOARD_BINDING_NEXT_TASK)
        elif STALE_LOOP_OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_AUDITED_WRITER_DASHBOARD_BINDING_NEXT_TASK)
        elif STALE_LOOP_POST_REGENERATION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_STALE_LOOP_OPERATOR_QUEUE_PENDING_NEXT_TASK)
        elif STALE_LOOP_EXECUTION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_STALE_LOOP_POST_REGENERATION_NEXT_TASK)
        elif STALE_LOOP_REGENERATION_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_STALE_LOOP_REGENERATION_NEXT_TASK)
        elif REGENERATED_REPAIR_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_REGENERATED_REPAIR_NEXT_TASK)
        elif BLOCKED_REPAIR_PLAN_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_BLOCKED_REPAIR_PLAN_NEXT_TASK)
        elif HASH_MISMATCH_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_HASH_MISMATCH_NEXT_TASK)
        elif REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_NEXT_TASK)
        self.assertIn("POST_REPAIR_RECONCILIATION_REQUIRED", state["open_contract_gap_ids"])
        self.assertIn("REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED", state["open_contract_gap_ids"])

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
