import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import (
    build_upbit_paper_stale_loop_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import (
    build_upbit_paper_stale_loop_regeneration_plan,
)
from trader1.runtime.paper.upbit_paper_stale_loop_execution_guard import (
    build_upbit_paper_stale_loop_execution_guard,
)
from trader1.runtime.paper.upbit_paper_stale_loop_safe_regeneration_executor import (
    build_upbit_paper_stale_loop_safe_regeneration_executor_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_post_regeneration_reconciliation import (
    build_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_blocked_repair_plan import (
    build_upbit_paper_blocked_repair_plan_report,
)
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import (
    build_upbit_paper_ledger_rollup_repair_report,
)
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import (
    build_upbit_paper_post_repair_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_repair_operator_queue import (
    build_upbit_paper_repair_operator_queue_report,
    upbit_paper_repair_operator_queue_hash,
    validate_upbit_paper_repair_operator_queue_report,
    write_upbit_paper_repair_operator_queue_report,
)


class UpbitPaperRepairOperatorQueueTest(unittest.TestCase):
    def _loop_path(self, root: Path, loop_id: str) -> Path:
        return (
            root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / f"{loop_id}.persistent_loop_report.json"
        )

    def _reports(self) -> tuple[Path, dict, dict, dict]:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        current = run_upbit_paper_persistent_loop(
            root=root,
            loop_id="validator-repair-queue-current",
            requested_cycle_count=1,
        )
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-repair-queue-legacy"
        for field in (
            "paper_ledger_rollup_status",
            "paper_ledger_rollup_hash",
            "paper_ledger_rollup_primary_blocker_code",
            "paper_ledger_rollup_path",
        ):
            legacy.pop(field, None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        self._loop_path(root, "validator-repair-queue-legacy").write_text(
            json.dumps(legacy, indent=2),
            encoding="utf-8",
        )
        stale = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        regeneration = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=stale)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=regeneration)
        executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        post_regeneration = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
            root=root,
            executor_report=executor,
        )
        blocked_plan = build_upbit_paper_blocked_repair_plan_report(
            root=root,
            post_reconciliation_report=post_regeneration,
        )
        ledger_repair = build_upbit_paper_ledger_rollup_repair_report(
            root=root,
            repair_plan_report=blocked_plan,
        )
        post_repair = build_upbit_paper_post_repair_reconciliation_report(
            ledger_rollup_repair_report=ledger_repair,
        )
        return root, blocked_plan, ledger_repair, post_repair

    def test_operator_queue_prioritizes_hash_blocked_ledger_candidate_without_live_permission(self):
        root, blocked_plan, ledger_repair, post_repair = self._reports()

        report = build_upbit_paper_repair_operator_queue_report(
            blocked_repair_plan_report=blocked_plan,
            ledger_rollup_repair_report=ledger_repair,
            post_repair_reconciliation_report=post_repair,
        )
        result = validate_upbit_paper_repair_operator_queue_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["queue_status"], "BLOCKED")
        self.assertEqual(report["queue_item_count"], 1)
        self.assertEqual(report["ledger_candidate_review_ready_count"], 1)
        self.assertEqual(report["runtime_cycle_rerun_required_count"], 0)
        self.assertEqual(report["recovery_guard_rerun_required_count"], 0)
        self.assertEqual(report["hash_operator_reconciliation_required_count"], 1)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

        item = report["items"][0]
        self.assertEqual(item["safe_repair_lane"], "LEDGER_ROLLUP_REBUILD_READY")
        self.assertTrue(item["ready_for_operator_ledger_candidate_review"])
        self.assertTrue(item["requires_hash_operator_reconciliation"])
        self.assertFalse(item["candidate_current_evidence_usable"])
        self.assertIn("POST_REPAIR_RECONCILIATION_REQUIRED", item["blocking_codes"])
        self.assertIn("hash mismatch", item["operator_action"])

        path = write_upbit_paper_repair_operator_queue_report(root=root, report=report)
        self.assertTrue(path.exists())

    def test_operator_queue_blocks_live_mutation(self):
        _, blocked_plan, ledger_repair, post_repair = self._reports()
        report = build_upbit_paper_repair_operator_queue_report(
            blocked_repair_plan_report=blocked_plan,
            ledger_rollup_repair_report=ledger_repair,
            post_repair_reconciliation_report=post_repair,
        )
        report["live_order_allowed"] = True
        report["queue_hash"] = upbit_paper_repair_operator_queue_hash(report)

        result = validate_upbit_paper_repair_operator_queue_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_operator_queue_rejects_count_tamper(self):
        _, blocked_plan, ledger_repair, post_repair = self._reports()
        report = build_upbit_paper_repair_operator_queue_report(
            blocked_repair_plan_report=blocked_plan,
            ledger_rollup_repair_report=ledger_repair,
            post_repair_reconciliation_report=post_repair,
        )
        report["ledger_candidate_review_ready_count"] = 0
        report["queue_hash"] = upbit_paper_repair_operator_queue_hash(report)

        result = validate_upbit_paper_repair_operator_queue_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_operator_queue_blocks_path_escape(self):
        _, blocked_plan, ledger_repair, post_repair = self._reports()
        report = build_upbit_paper_repair_operator_queue_report(
            blocked_repair_plan_report=blocked_plan,
            ledger_rollup_repair_report=ledger_repair,
            post_repair_reconciliation_report=post_repair,
        )
        report["items"][0]["candidate_rollup_artifact_path"] = "system/runtime/upbit/krw_spot/live/bad.json"
        report["queue_hash"] = upbit_paper_repair_operator_queue_hash(report)

        result = validate_upbit_paper_repair_operator_queue_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
