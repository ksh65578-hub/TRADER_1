import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_blocked_repair_plan import build_upbit_paper_blocked_repair_plan_report
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import build_upbit_paper_ledger_rollup_repair_report
from trader1.runtime.paper.upbit_paper_missing_cycle_rerun_guard import (
    build_upbit_paper_missing_cycle_rerun_guard_report,
    upbit_paper_missing_cycle_rerun_guard_hash,
    validate_upbit_paper_missing_cycle_rerun_guard_report,
    write_upbit_paper_missing_cycle_rerun_guard_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
)
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import build_upbit_paper_post_repair_reconciliation_report
from trader1.runtime.paper.upbit_paper_repair_operator_queue import (
    build_upbit_paper_repair_operator_queue_report,
    upbit_paper_repair_operator_queue_hash,
)
from trader1.runtime.paper.upbit_paper_stale_loop_execution_guard import build_upbit_paper_stale_loop_execution_guard
from trader1.runtime.paper.upbit_paper_stale_loop_post_regeneration_reconciliation import (
    build_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import build_upbit_paper_stale_loop_reconciliation_report
from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import build_upbit_paper_stale_loop_regeneration_plan
from trader1.runtime.paper.upbit_paper_stale_loop_safe_regeneration_executor import (
    build_upbit_paper_stale_loop_safe_regeneration_executor_report,
)


class UpbitPaperMissingCycleRerunGuardTest(unittest.TestCase):
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

    def _queue_with_missing_cycle(self) -> tuple[Path, dict]:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-rerun-current", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-rerun-legacy"
        for field in (
            "paper_ledger_rollup_status",
            "paper_ledger_rollup_hash",
            "paper_ledger_rollup_primary_blocker_code",
            "paper_ledger_rollup_path",
        ):
            legacy.pop(field, None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        self._loop_path(root, "validator-rerun-legacy").write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        stale = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        regeneration = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=stale)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=regeneration)
        executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        post_regeneration = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
            root=root,
            executor_report=executor,
        )

        item = post_regeneration["items"][0]
        replacement_path = root.joinpath(*item["replacement_path"].split("/"))
        replacement = json.loads(replacement_path.read_text(encoding="utf-8"))
        cycle_id = replacement["cycle_results"][0]["cycle_id"]
        ledger_path = (
            root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "ledger"
            / "cycles"
            / f"{cycle_id}.paper_ledger_events.jsonl"
        )
        ledger_path.unlink()

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
        queue = build_upbit_paper_repair_operator_queue_report(
            blocked_repair_plan_report=blocked_plan,
            ledger_rollup_repair_report=ledger_repair,
            post_repair_reconciliation_report=post_repair,
        )
        return root, queue

    def test_guard_marks_missing_cycle_ready_for_staging_without_current_evidence_mutation(self):
        root, queue = self._queue_with_missing_cycle()

        report = build_upbit_paper_missing_cycle_rerun_guard_report(
            root=root,
            repair_operator_queue_report=queue,
        )
        result = validate_upbit_paper_missing_cycle_rerun_guard_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["guard_status"], "BLOCKED")
        self.assertEqual(report["guard_item_count"], 1)
        self.assertEqual(report["rerun_ready_item_count"], 1)
        self.assertEqual(report["recovery_guard_blocked_item_count"], 0)
        self.assertEqual(report["identity_blocked_item_count"], 0)
        self.assertEqual(report["missing_cycle_ledger_jsonl_total_count"], 1)
        self.assertEqual(report["planned_staging_artifact_total_count"], 3)
        self.assertFalse(report["actual_rerun_executed"])
        self.assertFalse(report["current_ledger_jsonl_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])

        item = report["items"][0]
        self.assertEqual(item["rerun_guard_status"], "READY_FOR_BOUNDED_PAPER_RERUN_STAGING")
        self.assertTrue(item["missing_cycle_identity_match"])
        self.assertTrue(item["next_patch_staging_rerun_candidate_eligible"])
        self.assertFalse(item["current_ledger_jsonl_write_allowed"])
        self.assertFalse(item["latest_runtime_pointer_write_allowed"])
        self.assertIn("/rerun_candidates/", item["planned_staging_artifact_paths"][0])

        written_path = write_upbit_paper_missing_cycle_rerun_guard_report(root=root, report=report)
        self.assertTrue(written_path.exists())

    def test_guard_blocks_recovery_lane_before_staging(self):
        root, queue = self._queue_with_missing_cycle()
        queue = json.loads(json.dumps(queue))
        recovery_item = json.loads(json.dumps(queue["items"][0]))
        recovery_item["priority_order"] = 2
        recovery_item["safe_repair_lane"] = "RECOVERY_GUARD_THEN_LEDGER_ROLLUP"
        recovery_item["requires_recovery_guard_rerun"] = True
        recovery_item["blocking_codes"] = sorted(set(recovery_item["blocking_codes"] + ["RECOVERY_GUARD_BLOCKED"]))
        queue["items"].append(recovery_item)
        queue["queue_item_count"] = 2
        queue["runtime_cycle_rerun_required_count"] = 2
        queue["recovery_guard_rerun_required_count"] = 1
        queue["queue_hash"] = upbit_paper_repair_operator_queue_hash(queue)

        report = build_upbit_paper_missing_cycle_rerun_guard_report(
            root=root,
            repair_operator_queue_report=queue,
        )

        self.assertEqual(validate_upbit_paper_missing_cycle_rerun_guard_report(report).status, "PASS")
        self.assertEqual(report["guard_item_count"], 2)
        self.assertEqual(report["rerun_ready_item_count"], 1)
        self.assertEqual(report["recovery_guard_blocked_item_count"], 1)
        self.assertEqual(report["items"][1]["rerun_guard_status"], "BLOCKED_RECOVERY_GUARD_REQUIRED")
        self.assertFalse(report["items"][1]["next_patch_staging_rerun_candidate_eligible"])

    def test_guard_blocks_live_mutation_and_count_tamper(self):
        root, queue = self._queue_with_missing_cycle()
        report = build_upbit_paper_missing_cycle_rerun_guard_report(
            root=root,
            repair_operator_queue_report=queue,
        )
        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["guard_hash"] = upbit_paper_missing_cycle_rerun_guard_hash(live_mutation)

        live_result = validate_upbit_paper_missing_cycle_rerun_guard_report(live_mutation)

        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        count_tamper = json.loads(json.dumps(report))
        count_tamper["rerun_ready_item_count"] = 0
        count_tamper["guard_hash"] = upbit_paper_missing_cycle_rerun_guard_hash(count_tamper)

        count_result = validate_upbit_paper_missing_cycle_rerun_guard_report(count_tamper)

        self.assertEqual(count_result.status, "FAIL")
        self.assertEqual(count_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_guard_blocks_staging_path_escape(self):
        root, queue = self._queue_with_missing_cycle()
        report = build_upbit_paper_missing_cycle_rerun_guard_report(
            root=root,
            repair_operator_queue_report=queue,
        )
        report["items"][0]["planned_staging_artifact_paths"][0] = "system/runtime/upbit/krw_spot/live/bad.json"
        report["guard_hash"] = upbit_paper_missing_cycle_rerun_guard_hash(report)

        result = validate_upbit_paper_missing_cycle_rerun_guard_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_guard_blocks_replacement_path_escape_before_staging(self):
        root, queue = self._queue_with_missing_cycle()
        queue = json.loads(json.dumps(queue))
        queue["items"][0]["replacement_path"] = "system/runtime/upbit/krw_spot/live/escaped.json"
        queue["queue_hash"] = upbit_paper_repair_operator_queue_hash(queue)

        report = build_upbit_paper_missing_cycle_rerun_guard_report(
            root=root,
            repair_operator_queue_report=queue,
        )
        item = report["items"][0]

        self.assertEqual(item["replacement_load_status"], "PATH_SCOPE_MISMATCH")
        self.assertEqual(item["replacement_path_scope_status"], "MISMATCH")
        self.assertEqual(item["rerun_guard_status"], "BLOCKED_IDENTITY_RECONCILIATION_REQUIRED")
        self.assertFalse(item["next_patch_staging_rerun_candidate_eligible"])
        result = validate_upbit_paper_missing_cycle_rerun_guard_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
