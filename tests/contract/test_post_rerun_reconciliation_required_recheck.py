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
    / "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_STATE_SYNC_RECHECK.patch_result.json"
)
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


class PostRerunReconciliationRequiredRecheckTest(unittest.TestCase):
    def test_post_rerun_reports_keep_current_evidence_writes_blocked(self):
        report_names = [
            "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json",
            "upbit_paper_post_rerun_reconciliation_repair_path_report.json",
            "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json",
            "upbit_paper_post_rerun_reconciliation_decision_audit_report.json",
            "upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
            "upbit_paper_post_rerun_operator_resolution_audit_report.json",
            "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json",
        ]
        for name in report_names:
            with self.subTest(name=name):
                report = load_json(RUNTIME_BASE / name)
                self.assertFalse(report["live_order_allowed"])
                self.assertFalse(report["can_live_trade"])
                self.assertFalse(report["scale_up_allowed"])
                self.assertEqual(report.get("candidate_current_evidence_usable_count", 0), 0)
                self.assertFalse(report.get("current_evidence_write_allowed", False))
                self.assertEqual(report.get("current_evidence_write_allowed_count", 0), 0)

    def test_operator_reconciliation_and_resolution_remain_required(self):
        queue = load_json(RUNTIME_BASE / "upbit_paper_post_rerun_operator_reconciliation_queue_report.json")
        resolution = load_json(RUNTIME_BASE / "upbit_paper_post_rerun_operator_resolution_audit_report.json")
        closure = load_json(RUNTIME_BASE / "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json")

        self.assertEqual(queue["queue_status"], "BLOCKED")
        self.assertGreater(queue["operator_reconciliation_required_count"], 0)
        self.assertTrue(resolution["operator_resolution_required"])
        self.assertGreater(resolution["unresolved_item_count"], 0)
        self.assertEqual(resolution["resolved_item_count"], 0)
        self.assertEqual(closure["closure_status"], "CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED")
        self.assertEqual(closure["resolved_item_count"], 0)

    def test_state_sync_recheck_keeps_gap_open_and_routes_to_write_blocked_recheck(self):
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_STATE_SYNC_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK")
        if state["last_patch_id"] == patch_result["patch_id"]:
            self.assertEqual(state["next_allowed_task_class"], "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK")
        else:
            self.assertNotEqual(state["next_allowed_task_class"], "")
        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", state["open_contract_gap_ids"])
        self.assertIn("POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED", patch_result["remaining_blockers"])

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

    def test_historical_post_rerun_patch_results_remain_live_blocked(self):
        patch_names = [
            "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_RECHECK",
            "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH",
            "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP",
            "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE",
            "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT",
            "MVP4_UPBIT_PAPER_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE",
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
                self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", patch_result["remaining_blockers"])


if __name__ == "__main__":
    unittest.main()
