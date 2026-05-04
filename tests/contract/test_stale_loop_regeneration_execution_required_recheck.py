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
    / "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK.patch_result.json"
)
GUARD_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_regeneration_execution_guard.json"
)
EXECUTOR_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_safe_regeneration_executor_report.json"
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
REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-RECHECK"
POST_REGENERATION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-RECONCILIATION-AFTER-REGENERATION-REQUIRED-RECHECK"
)
OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-PENDING-RECHECK"
)
DASHBOARD_BINDING_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-AUDITED-CURRENT-EVIDENCE-WRITER-DASHBOARD-BINDING"
PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-RECHECK"
NEXT_TASK = "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
OPERATOR_QUEUE_PENDING_NEXT_TASK = "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK"
AUDITED_WRITER_DASHBOARD_NEXT_TASK = "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
AFTER_AUDITED_WRITER_DASHBOARD_NEXT_TASK = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
CLOSED_BLOCKERS = {"STALE_LOOP_REGENERATION_REQUIRED", "STALE_LOOP_REGENERATION_EXECUTION_REQUIRED"}
NEXT_BLOCKER = "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED"
OPERATOR_QUEUE_PENDING_BLOCKER = "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class StaleLoopRegenerationExecutionRequiredRecheckTest(unittest.TestCase):
    def test_guard_remains_pre_execution_and_executor_completed_safe_paper_regeneration(self):
        guard = load_json(GUARD_PATH)
        executor = load_json(EXECUTOR_PATH)

        self.assertEqual(guard["guard_status"], "PASS")
        self.assertEqual(guard["planned_regeneration_item_count"], 16)
        self.assertEqual(guard["replacement_existing_count"], 0)
        self.assertEqual(guard["source_hash_mismatch_count"], 0)
        self.assertFalse(guard["actual_regeneration_performed"])
        self.assertFalse(guard["actual_long_run_evidence_created"])

        self.assertEqual(executor["executor_status"], "PASS")
        self.assertEqual(executor["planned_regeneration_item_count"], 16)
        self.assertEqual(executor["regenerated_item_count"], 16)
        self.assertEqual(executor["skipped_item_count"], 0)
        self.assertTrue(executor["actual_regeneration_performed"])
        self.assertFalse(executor["actual_long_run_evidence_created"])
        self.assertFalse(executor["long_run_evidence_eligible"])
        self.assertFalse(executor["promotion_eligible"])
        self.assertTrue(executor["source_retention_required"])
        self.assertFalse(executor["delete_source_allowed"])
        self.assertFalse(executor["overwrite_source_allowed"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(executor[field])

    def test_executor_items_are_source_retaining_create_new_paper_replacements(self):
        executor = load_json(EXECUTOR_PATH)
        replacement_paths = []

        for item in executor["items"]:
            self.assertEqual(item["execution_item_status"], "PASS")
            self.assertTrue(item["source_retained"])
            self.assertTrue(item["replacement_written"])
            self.assertTrue(item["replacement_exists_after"])
            self.assertTrue(item["source_hash_match"])
            self.assertEqual(item["replacement_write_mode"], "CREATE_NEW_ONLY")
            self.assertIn("regenerated-current-schema", item["planned_replacement_path"])
            self.assertNotEqual(item["source_path"], item["planned_replacement_path"])
            self.assertTrue(
                item["planned_replacement_path"].startswith(
                    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/"
                )
            )
            self.assertTrue(ROOT.joinpath(*item["source_path"].split("/")).exists())
            self.assertTrue(ROOT.joinpath(*item["planned_replacement_path"].split("/")).exists())
            self.assertFalse(item["delete_source_allowed"])
            self.assertFalse(item["overwrite_source_allowed"])
            self.assertFalse(item["actual_long_run_evidence_created"])
            self.assertFalse(item["live_order_allowed"])
            self.assertFalse(item["scale_up_allowed"])
            replacement_paths.append(item["planned_replacement_path"])

        self.assertEqual(len(replacement_paths), 16)
        self.assertEqual(len(replacement_paths), len(set(replacement_paths)))

    def test_post_regeneration_reconciliation_stays_blocked_for_next_recheck(self):
        report = load_json(POST_REGENERATION_PATH)

        self.assertEqual(report["post_reconciliation_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], NEXT_BLOCKER)
        self.assertIn(NEXT_BLOCKER, report["blocker_codes"])
        self.assertEqual(report["planned_regeneration_item_count"], 16)
        self.assertEqual(report["regenerated_current_accepted_count"], 10)
        self.assertEqual(report["regenerated_current_blocked_reconciliation_count"], 6)
        self.assertEqual(report["current_evidence_usable_count"], 10)
        self.assertEqual(report["excluded_from_current_evidence_count"], 6)
        self.assertFalse(report["actual_long_run_evidence_created"])
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["promotion_eligible"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])

    def test_recheck_closes_execution_gap_and_routes_to_post_regeneration_reconciliation(self):
        if not PATCH_PATH.exists():
            self.skipTest("stale loop regeneration execution recheck patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK)
        self.assertEqual(patch_result["stale_loop_execution_guard_status"], "PASS")
        self.assertEqual(patch_result["stale_loop_safe_executor_status"], "PASS")
        self.assertEqual(patch_result["stale_loop_safe_executor_regenerated_item_count"], 16)
        self.assertTrue(patch_result["stale_loop_safe_executor_actual_regeneration_performed"])
        self.assertFalse(patch_result["stale_loop_safe_executor_actual_long_run_evidence_created"])
        self.assertEqual(patch_result["stale_loop_post_regeneration_reconciliation_status"], "BLOCKED")
        self.assertEqual(patch_result["stale_loop_post_regeneration_current_evidence_usable_count"], 10)
        self.assertIn(NEXT_BLOCKER, patch_result["remaining_blockers"])
        for blocker in CLOSED_BLOCKERS:
            self.assertNotIn(blocker, patch_result["remaining_blockers"])

        completed = set(state["completed_requirement_ids"])
        if PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK)
            self.assertNotIn(OPERATOR_QUEUE_PENDING_BLOCKER, state["open_contract_gap_ids"])
            self.assertNotIn(NEXT_BLOCKER, state["open_contract_gap_ids"])
        elif DASHBOARD_BINDING_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_AUDITED_WRITER_DASHBOARD_NEXT_TASK)
            self.assertNotIn(OPERATOR_QUEUE_PENDING_BLOCKER, state["open_contract_gap_ids"])
            self.assertNotIn(NEXT_BLOCKER, state["open_contract_gap_ids"])
        elif OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AUDITED_WRITER_DASHBOARD_NEXT_TASK)
            self.assertNotIn(OPERATOR_QUEUE_PENDING_BLOCKER, state["open_contract_gap_ids"])
            self.assertNotIn(NEXT_BLOCKER, state["open_contract_gap_ids"])
        elif POST_REGENERATION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], OPERATOR_QUEUE_PENDING_NEXT_TASK)
            self.assertIn(OPERATOR_QUEUE_PENDING_BLOCKER, state["open_contract_gap_ids"])
            self.assertNotIn(NEXT_BLOCKER, state["open_contract_gap_ids"])
        elif REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK)
            self.assertIn(NEXT_BLOCKER, state["open_contract_gap_ids"])
            for blocker in CLOSED_BLOCKERS:
                self.assertNotIn(blocker, state["open_contract_gap_ids"])
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
