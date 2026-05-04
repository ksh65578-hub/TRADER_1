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
    / "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK.patch_result.json"
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
LEDGER_PREVIEW_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_ledger_recheck_preview_report.json"
)
NORMALIZED_RECHECK_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_normalized_reconciliation_recheck_report.json"
)
AUDITED_WRITER_PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-PENDING-RECHECK"
NEXT_TASK = "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
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
AFTER_DASHBOARD_BINDING_NEXT_TASK = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
)
AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK = "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK"
AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK = (
    "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK"
)
AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK"
)
CLOSED_BLOCKER = "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class StaleLoopReconciliationOperatorQueuePendingRecheckTest(unittest.TestCase):
    def test_downstream_evidence_classifies_operator_queue_without_live_or_current_writes(self):
        closure = load_json(CLOSURE_PATH)
        ledger_preview = load_json(LEDGER_PREVIEW_PATH)
        normalized = load_json(NORMALIZED_RECHECK_PATH)
        audited_writer = load_json(AUDITED_WRITER_PATCH_PATH)

        self.assertEqual(closure["closure_status"], "BLOCKED")
        self.assertEqual(closure["primary_blocker_code"], CLOSED_BLOCKER)
        self.assertEqual(closure["closure_item_count"], 6)
        self.assertEqual(closure["ledger_recheck_ready_count"], 5)
        self.assertEqual(closure["recovery_guard_required_count"], 1)
        self.assertEqual(closure["current_evidence_write_allowed_count"], 0)
        self.assertEqual(closure["current_evidence_usable_after_closure_count"], 0)

        self.assertEqual(ledger_preview["preview_status"], "BLOCKED")
        self.assertEqual(ledger_preview["ledger_recheck_candidate_count"], 5)
        self.assertEqual(ledger_preview["ledger_binding_pass_count"], 5)
        self.assertEqual(ledger_preview["replacement_validation_fail_count"], 5)
        self.assertEqual(ledger_preview["preview_blocked_count"], 5)
        self.assertEqual(ledger_preview["current_evidence_write_allowed_count"], 0)
        self.assertEqual(ledger_preview["current_evidence_usable_after_preview_count"], 0)

        self.assertEqual(normalized["recheck_status"], "BLOCKED")
        self.assertEqual(normalized["normalized_reconciliation_recheck_candidate_count"], 5)
        self.assertEqual(normalized["normalized_hash_match_count"], 5)
        self.assertEqual(normalized["normalized_validation_blocked_count"], 5)
        self.assertEqual(normalized["ledger_rollup_recheck_required_count"], 5)
        self.assertEqual(normalized["current_evidence_write_allowed_count"], 0)

        self.assertEqual(audited_writer["next_task_class"], NEXT_TASK)
        self.assertNotIn(CLOSED_BLOCKER, audited_writer["remaining_blockers"])
        for field in (
            "live_order_allowed_after",
            "can_live_trade_after",
            "scale_up_allowed_after",
            "convergence_live_order_allowed_after",
            "optimizer_live_order_allowed_after",
        ):
            self.assertFalse(audited_writer[field])

    def test_recheck_closes_operator_queue_pending_and_routes_to_audited_writer_dashboard_binding(self):
        if not PATCH_PATH.exists():
            self.skipTest("stale loop operator queue pending recheck patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK)
        self.assertEqual(patch_result["stale_loop_operator_queue_closure_status"], "BLOCKED")
        self.assertEqual(patch_result["stale_loop_operator_queue_closure_item_count"], 6)
        self.assertEqual(patch_result["stale_loop_ledger_recheck_candidate_count"], 5)
        self.assertEqual(patch_result["stale_loop_ledger_recheck_preview_blocked_count"], 5)
        self.assertEqual(patch_result["stale_loop_normalized_reconciliation_recheck_candidate_count"], 5)
        self.assertEqual(patch_result["stale_loop_normalized_reconciliation_recheck_ledger_rollup_required_count"], 5)
        self.assertNotIn(CLOSED_BLOCKER, patch_result["remaining_blockers"])

        if PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK)
        elif COMPLETED_OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK)
        elif COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK)
        elif PATCH_RESULT_VALIDATOR_BASELINE_RECONCILIATION_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK)
        elif ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK)
        elif PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK)
            self.assertNotIn(CLOSED_BLOCKER, state["open_contract_gap_ids"])
        elif DASHBOARD_BINDING_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_DASHBOARD_BINDING_NEXT_TASK)
            self.assertNotIn(CLOSED_BLOCKER, state["open_contract_gap_ids"])
        elif REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK)
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
