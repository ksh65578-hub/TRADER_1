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
    / "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK.patch_result.json"
)
POST_REGENERATION_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json"
)
CLOSURE_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json"
)
REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-RECONCILIATION-AFTER-REGENERATION-REQUIRED-RECHECK"
OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID = (
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
NEXT_TASK = "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK"
AUDITED_WRITER_DASHBOARD_NEXT_TASK = "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
AFTER_AUDITED_WRITER_DASHBOARD_NEXT_TASK = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
)
AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK = "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK"
CLOSED_BLOCKER = "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED"
NEXT_BLOCKER = "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class StaleLoopReconciliationAfterRegenerationRequiredRecheckTest(unittest.TestCase):
    def test_closure_decomposes_post_regeneration_blocker_into_operator_queue(self):
        post = load_json(POST_REGENERATION_PATH)
        closure = load_json(CLOSURE_PATH)

        self.assertEqual(post["post_reconciliation_status"], "BLOCKED")
        self.assertEqual(post["primary_blocker_code"], CLOSED_BLOCKER)
        self.assertEqual(post["regenerated_current_blocked_reconciliation_count"], 6)
        self.assertEqual(post["current_evidence_usable_count"], 10)

        self.assertEqual(closure["closure_status"], "BLOCKED")
        self.assertEqual(closure["primary_blocker_code"], NEXT_BLOCKER)
        self.assertIn(CLOSED_BLOCKER, closure["blocker_codes"])
        self.assertIn(NEXT_BLOCKER, closure["blocker_codes"])
        self.assertEqual(closure["source_post_regeneration_reconciliation_hash"], post["post_reconciliation_hash"])
        self.assertEqual(closure["closure_item_count"], post["regenerated_current_blocked_reconciliation_count"])
        self.assertEqual(closure["ledger_recheck_ready_count"], 5)
        self.assertEqual(closure["recovery_guard_required_count"], 1)
        self.assertEqual(closure["current_evidence_write_allowed_count"], 0)
        self.assertEqual(closure["current_evidence_usable_after_closure_count"], 0)
        self.assertFalse(closure["current_evidence_write_allowed"])
        self.assertFalse(closure["live_order_allowed"])
        self.assertFalse(closure["can_live_trade"])
        self.assertFalse(closure["scale_up_allowed"])

    def test_closure_items_remain_fail_closed_without_runtime_or_current_evidence_mutation(self):
        closure = load_json(CLOSURE_PATH)
        lanes = [item["closure_lane"] for item in closure["items"]]

        self.assertEqual(lanes.count("LEDGER_RECHECK_READY"), 5)
        self.assertEqual(lanes.count("RECOVERY_GUARD_REQUIRED"), 1)
        for item in closure["items"]:
            self.assertEqual(item["source_item_blocker_code"], CLOSED_BLOCKER)
            self.assertIn(NEXT_BLOCKER, item["blocking_codes"])
            self.assertFalse(item["current_evidence_usable_after_closure"])
            self.assertFalse(item["current_evidence_write_allowed"])
            self.assertFalse(item["persistent_loop_mutation_allowed"])
            self.assertFalse(item["replacement_write_allowed"])
            self.assertFalse(item["source_delete_allowed"])
            self.assertFalse(item["live_permission_created"])
            self.assertFalse(item["actual_long_run_evidence_created"])
            if item["closure_lane"] == "LEDGER_RECHECK_READY":
                self.assertTrue(item["closure_recheck_ready"])
            if item["closure_lane"] == "RECOVERY_GUARD_REQUIRED":
                self.assertFalse(item["closure_recheck_ready"])

    def test_recheck_patch_closes_after_regeneration_gap_and_routes_to_operator_queue_pending(self):
        if not PATCH_PATH.exists():
            self.skipTest("stale loop post-regeneration reconciliation recheck patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK)
        self.assertEqual(patch_result["stale_loop_post_regeneration_reconciliation_status"], "BLOCKED")
        self.assertEqual(patch_result["stale_loop_post_regeneration_blocked_reconciliation_count"], 6)
        self.assertEqual(patch_result["stale_loop_operator_queue_closure_status"], "BLOCKED")
        self.assertEqual(patch_result["stale_loop_operator_queue_closure_item_count"], 6)
        self.assertEqual(patch_result["stale_loop_operator_queue_closure_ledger_recheck_ready_count"], 5)
        self.assertEqual(patch_result["stale_loop_operator_queue_closure_recovery_guard_required_count"], 1)
        self.assertEqual(patch_result["stale_loop_operator_queue_closure_current_evidence_write_allowed_count"], 0)
        self.assertIn(NEXT_BLOCKER, patch_result["remaining_blockers"])
        self.assertNotIn(CLOSED_BLOCKER, patch_result["remaining_blockers"])

        if PATCH_RESULT_VALIDATOR_BASELINE_RECONCILIATION_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK)
        elif ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK)
        elif PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK)
            self.assertNotIn(NEXT_BLOCKER, state["open_contract_gap_ids"])
            self.assertNotIn(CLOSED_BLOCKER, state["open_contract_gap_ids"])
        elif DASHBOARD_BINDING_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_AUDITED_WRITER_DASHBOARD_NEXT_TASK)
            self.assertNotIn(NEXT_BLOCKER, state["open_contract_gap_ids"])
            self.assertNotIn(CLOSED_BLOCKER, state["open_contract_gap_ids"])
        elif OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AUDITED_WRITER_DASHBOARD_NEXT_TASK)
            self.assertNotIn(NEXT_BLOCKER, state["open_contract_gap_ids"])
            self.assertNotIn(CLOSED_BLOCKER, state["open_contract_gap_ids"])
        elif REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK)
            self.assertIn(NEXT_BLOCKER, state["open_contract_gap_ids"])
            self.assertNotIn(CLOSED_BLOCKER, state["open_contract_gap_ids"])
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
