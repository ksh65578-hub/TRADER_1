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
AFTER_DASHBOARD_BINDING_NEXT_TASK = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
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

        if DASHBOARD_BINDING_REQUIREMENT_ID in state["completed_requirement_ids"]:
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
