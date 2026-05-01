import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_execution_guard import (
    build_upbit_paper_stale_loop_execution_guard,
    stale_loop_execution_guard_hash,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import (
    build_upbit_paper_stale_loop_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import (
    build_upbit_paper_stale_loop_regeneration_plan,
)
from trader1.runtime.paper.upbit_paper_stale_loop_safe_regeneration_executor import (
    build_upbit_paper_stale_loop_safe_regeneration_executor_report,
    stale_loop_safe_regeneration_executor_hash,
    validate_upbit_paper_stale_loop_safe_regeneration_executor_report,
    write_upbit_paper_stale_loop_safe_regeneration_executor_report,
)


class UpbitPaperStaleLoopSafeRegenerationExecutorTest(unittest.TestCase):
    def _root_with_guard(self) -> tuple[Path, dict, dict]:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="current-loop", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "legacy-loop"
        legacy.pop("paper_ledger_rollup_hash")
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        legacy_path = (
            root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "legacy-loop.persistent_loop_report.json"
        )
        legacy_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        return root, plan, guard

    def test_safe_executor_writes_create_new_current_schema_artifact(self):
        root, plan, guard = self._root_with_guard()

        report = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        result = validate_upbit_paper_stale_loop_safe_regeneration_executor_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["executor_status"], "PASS")
        self.assertEqual(report["planned_regeneration_item_count"], 1)
        self.assertEqual(report["regenerated_item_count"], 1)
        self.assertTrue(report["actual_regeneration_performed"])
        self.assertFalse(report["actual_long_run_evidence_created"])
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

        item = report["items"][0]
        self.assertTrue(item["source_retained"])
        self.assertTrue(item["replacement_written"])
        self.assertFalse(item["replacement_existed_before"])
        self.assertEqual(item["persistent_loop_validation_status"], "PASS")
        replacement = root.joinpath(*item["planned_replacement_path"].split("/"))
        self.assertTrue(replacement.exists())
        replacement_report = json.loads(replacement.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_persistent_loop_report(replacement_report).status, "PASS")
        self.assertEqual(replacement_report["loop_id"], plan["items"][0]["planned_replacement_loop_id"])
        self.assertFalse(replacement_report["long_run_evidence_eligible"])
        self.assertFalse(replacement_report["live_order_allowed"])

        writer_path = write_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, report=report)
        self.assertTrue(writer_path.exists())

    def test_safe_executor_schema_repairs_older_missing_recovery_and_ledger_fields_as_blocked(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="older-current-loop", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "older-legacy-loop"
        for field in (
            "recovery_guard_status",
            "recovery_guard_hash",
            "recovery_guard_primary_blocker_code",
            "runtime_recovery_guard_path",
            "paper_runtime_resume_allowed",
            "partial_write_recovery_required",
            "paper_ledger_rollup_status",
            "paper_ledger_rollup_hash",
            "paper_ledger_rollup_primary_blocker_code",
            "paper_ledger_rollup_path",
        ):
            legacy.pop(field, None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        legacy_path = (
            root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "older-legacy-loop.persistent_loop_report.json"
        )
        legacy_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)

        report = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)

        self.assertEqual(validate_upbit_paper_stale_loop_safe_regeneration_executor_report(report).status, "PASS")
        self.assertEqual(report["executor_status"], "PASS")
        self.assertEqual(report["planned_regeneration_item_count"], 1)
        self.assertEqual(report["regenerated_item_count"], 1)
        item = report["items"][0]
        self.assertTrue(item["replacement_written"])
        self.assertEqual(item["persistent_loop_validation_status"], "BLOCKED")
        self.assertIsNone(item["blocker_code"])
        replacement = root.joinpath(*item["planned_replacement_path"].split("/"))
        replacement_report = json.loads(replacement.read_text(encoding="utf-8"))
        replacement_result = validate_upbit_paper_persistent_loop_report(replacement_report)
        self.assertEqual(replacement_result.status, "BLOCKED")
        self.assertEqual(replacement_result.blocker_code, "RECONCILIATION_REQUIRED")
        self.assertEqual(replacement_report["loop_status"], "BLOCKED")
        self.assertEqual(replacement_report["paper_ledger_rollup_status"], "BLOCKED")
        self.assertEqual(replacement_report["recovery_guard_status"], "BLOCKED")
        self.assertFalse(replacement_report["live_order_allowed"])

    def test_safe_executor_blocks_second_run_without_overwrite(self):
        root, _, guard = self._root_with_guard()
        first = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        self.assertEqual(first["executor_status"], "PASS")

        second = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)

        self.assertEqual(second["executor_status"], "BLOCKED")
        self.assertIn("STALE_LOOP_REPLACEMENT_ALREADY_EXISTS", second["blocker_codes"])
        self.assertFalse(second["actual_regeneration_performed"])
        self.assertEqual(validate_upbit_paper_stale_loop_safe_regeneration_executor_report(second).status, "PASS")

    def test_safe_executor_blocks_guard_hash_mutation(self):
        root, _, guard = self._root_with_guard()
        guard["live_order_allowed"] = True
        guard["guard_hash"] = stale_loop_execution_guard_hash(guard)

        report = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)

        self.assertEqual(report["executor_status"], "BLOCKED")
        self.assertIn("LIVE_FINAL_GUARD_FAILED", report["blocker_codes"])
        self.assertFalse(report["actual_regeneration_performed"])
        self.assertEqual(validate_upbit_paper_stale_loop_safe_regeneration_executor_report(report).status, "PASS")

    def test_safe_executor_blocks_report_live_mutation(self):
        root, _, guard = self._root_with_guard()
        report = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        report["live_order_allowed"] = True
        report["executor_hash"] = stale_loop_safe_regeneration_executor_hash(report)

        result = validate_upbit_paper_stale_loop_safe_regeneration_executor_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
