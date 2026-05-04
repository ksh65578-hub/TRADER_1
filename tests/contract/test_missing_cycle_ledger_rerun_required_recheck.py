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
    / "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_STATE_SYNC_RECHECK.patch_result.json"
)
COMPLETED_REQUIREMENT_ID = "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-STATE-SYNC-RECHECK"
COMPLETED_POST_RERUN_RECONCILIATION_REQUIREMENT_ID = (
    "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-STATE-SYNC-RECHECK"
)
COMPLETED_POST_RERUN_WRITE_BLOCKED_REQUIREMENT_ID = (
    "REQ-MVP4-POST-RERUN-CURRENT-EVIDENCE-WRITE-BLOCKED-STATE-SYNC-RECHECK"
)
COMPLETED_POST_REPAIR_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-RECHECK"
)
COMPLETED_HASH_MISMATCH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK"
)
COMPLETED_BLOCKED_REPAIR_PLAN_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK"
)
COMPLETED_REGENERATED_REPAIR_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-"
    "RECONCILIATION-RECHECK"
)
COMPLETED_STALE_LOOP_REGENERATION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-RECHECK"
)
BACKWARD_NEXT_TASK = "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_RECHECK"
EXPECTED_NEXT_TASK = "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_RECHECK"
EXPECTED_DOWNSTREAM_NEXT_TASK = "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK"
EXPECTED_POST_REPAIR_NEXT_TASK = "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK"
EXPECTED_HASH_MISMATCH_NEXT_TASK = "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK"
EXPECTED_BLOCKED_REPAIR_PLAN_NEXT_TASK = (
    "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_RECHECK"
)
EXPECTED_REGENERATED_REPAIR_NEXT_TASK = "MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK"
EXPECTED_STALE_LOOP_REGENERATION_NEXT_TASK = "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK"
RUNTIME_BASE = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class MissingCycleLedgerRerunRequiredRecheckTest(unittest.TestCase):
    def test_missing_cycle_guard_and_staging_remain_blocked_from_current_evidence(self):
        guard = load_json(RUNTIME_BASE / "upbit_paper_missing_cycle_rerun_guard_report.json")
        executor = load_json(RUNTIME_BASE / "upbit_paper_bounded_rerun_staging_executor_report.json")

        self.assertEqual(guard["guard_status"], "BLOCKED")
        self.assertGreater(guard["rerun_ready_item_count"], 0)
        self.assertGreater(guard["missing_cycle_ledger_jsonl_total_count"], 0)
        self.assertFalse(guard["actual_rerun_executed"])
        self.assertEqual(guard["candidate_current_evidence_usable_count"], 0)

        self.assertEqual(executor["executor_status"], "BLOCKED")
        self.assertGreater(executor["staged_cycle_count"], 0)
        self.assertFalse(executor["actual_rerun_executed"])
        self.assertEqual(executor["staged_current_evidence_usable_count"], 0)

        for report in (guard, executor):
            for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
                self.assertFalse(report[field])

    def test_post_rerun_reconciliation_does_not_make_current_evidence_usable(self):
        reconciliation = load_json(RUNTIME_BASE / "upbit_paper_post_rerun_ledger_rollup_reconciliation_report.json")
        blocker_rollup = load_json(RUNTIME_BASE / "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json")

        self.assertFalse(reconciliation["actual_rerun_executed"])
        self.assertEqual(reconciliation["candidate_current_evidence_usable_count"], 0)
        self.assertGreater(reconciliation["candidate_item_count"], 0)
        self.assertFalse(blocker_rollup["current_evidence_write_allowed"])
        self.assertEqual(blocker_rollup["current_evidence_write_allowed_count"], 0)
        self.assertEqual(blocker_rollup["candidate_current_evidence_usable_count"], 0)

        for report in (reconciliation, blocker_rollup):
            for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
                self.assertFalse(report[field])

    def test_state_sync_recheck_keeps_gap_open_and_routes_to_post_rerun_reconciliation(self):
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_STATE_SYNC_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], EXPECTED_NEXT_TASK)
        if state["last_patch_id"] == patch_result["patch_id"]:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_NEXT_TASK)
        else:
            self.assertNotEqual(state["next_allowed_task_class"], "")
        self.assertIn("MISSING_CYCLE_LEDGER_RERUN_REQUIRED", state["open_contract_gap_ids"])
        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", patch_result["remaining_blockers"])

        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])
        for field in (
            "live_order_ready_after",
            "live_order_allowed_after",
            "can_live_trade_after",
            "scale_up_allowed_after",
            "convergence_live_order_allowed_after",
            "optimizer_live_order_allowed_after",
        ):
            self.assertFalse(patch_result[field])

    def test_completed_missing_cycle_recheck_does_not_route_backward(self):
        state = load_json(STATE_PATH)
        if COMPLETED_REQUIREMENT_ID not in state["completed_requirement_ids"]:
            self.skipTest("missing-cycle ledger rerun state-sync recheck has not completed yet")

        self.assertIn("MISSING_CYCLE_LEDGER_RERUN_REQUIRED", state["open_contract_gap_ids"])
        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", state["open_contract_gap_ids"])
        self.assertNotEqual(state["next_allowed_task_class"], BACKWARD_NEXT_TASK)
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])

    def test_completed_downstream_post_rerun_rechecks_do_not_route_backward(self):
        state = load_json(STATE_PATH)
        completed = set(state["completed_requirement_ids"])
        required_completed = {
            COMPLETED_REQUIREMENT_ID,
            COMPLETED_POST_RERUN_RECONCILIATION_REQUIREMENT_ID,
            COMPLETED_POST_RERUN_WRITE_BLOCKED_REQUIREMENT_ID,
        }
        if not required_completed.issubset(completed):
            self.skipTest("downstream post-rerun state-sync rechecks have not completed yet")

        self.assertNotIn(
            state["next_allowed_task_class"],
            {
                BACKWARD_NEXT_TASK,
                "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_RECHECK",
                "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK",
                EXPECTED_POST_REPAIR_NEXT_TASK,
                EXPECTED_HASH_MISMATCH_NEXT_TASK,
                EXPECTED_BLOCKED_REPAIR_PLAN_NEXT_TASK,
                EXPECTED_REGENERATED_REPAIR_NEXT_TASK,
            },
        )
        if COMPLETED_STALE_LOOP_REGENERATION_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_STALE_LOOP_REGENERATION_NEXT_TASK
        elif COMPLETED_REGENERATED_REPAIR_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_REGENERATED_REPAIR_NEXT_TASK
        elif COMPLETED_BLOCKED_REPAIR_PLAN_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_BLOCKED_REPAIR_PLAN_NEXT_TASK
        elif COMPLETED_HASH_MISMATCH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_HASH_MISMATCH_NEXT_TASK
        elif COMPLETED_POST_REPAIR_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_POST_REPAIR_NEXT_TASK
        else:
            expected_next_task = EXPECTED_DOWNSTREAM_NEXT_TASK
        self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])

    def test_historical_missing_cycle_patch_results_remain_live_blocked(self):
        patch_names = [
            "MVP4_UPBIT_PAPER_MISSING_CYCLE_RERUN_GUARD",
            "MVP4_UPBIT_PAPER_BOUNDED_RERUN_STAGING_EXECUTOR",
            "MVP4_UPBIT_PAPER_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION",
            "MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD",
        ]
        for patch_name in patch_names:
            with self.subTest(patch_name=patch_name):
                patch_result = load_json(
                    ROOT / "system" / "evidence" / "patch_results" / f"{patch_name}.patch_result.json"
                )
                self.assertFalse(patch_result["live_order_ready_after"])
                self.assertFalse(patch_result["live_order_allowed_after"])
                self.assertFalse(patch_result["can_live_trade_after"])
                self.assertFalse(patch_result["scale_up_allowed_after"])
                self.assertIn("LIVE_ENABLING_EVIDENCE_MISSING", patch_result["remaining_blockers"])


if __name__ == "__main__":
    unittest.main()
