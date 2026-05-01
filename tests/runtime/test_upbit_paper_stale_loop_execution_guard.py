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
    stale_loop_regeneration_plan_hash,
)
from trader1.runtime.paper.upbit_paper_stale_loop_execution_guard import (
    build_upbit_paper_stale_loop_execution_guard,
    stale_loop_execution_guard_hash,
    validate_upbit_paper_stale_loop_execution_guard,
    write_upbit_paper_stale_loop_execution_guard,
)


class UpbitPaperStaleLoopExecutionGuardTest(unittest.TestCase):
    def _root_with_plan(self) -> tuple[Path, dict]:
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
        return root, plan

    def test_execution_guard_passes_only_as_create_new_precondition(self):
        root, plan = self._root_with_plan()
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        result = validate_upbit_paper_stale_loop_execution_guard(guard)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(guard["guard_status"], "PASS")
        self.assertTrue(guard["paper_regeneration_preconditions_passed"])
        self.assertTrue(guard["separate_safe_executor_required"])
        self.assertEqual(guard["replacement_write_mode"], "CREATE_NEW_ONLY")
        self.assertTrue(guard["source_retention_required"])
        self.assertFalse(guard["execution_performed"])
        self.assertFalse(guard["actual_regeneration_performed"])
        self.assertFalse(guard["actual_long_run_evidence_created"])
        self.assertFalse(guard["live_order_ready"])
        self.assertFalse(guard["live_order_allowed"])
        self.assertFalse(guard["can_live_trade"])
        self.assertFalse(guard["scale_up_allowed"])

        path = write_upbit_paper_stale_loop_execution_guard(root=root, report=guard)
        written = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_stale_loop_execution_guard(written).status, "PASS")

    def test_execution_guard_blocks_existing_replacement_path(self):
        root, plan = self._root_with_plan()
        replacement_path = root.joinpath(*plan["items"][0]["planned_replacement_path"].split("/"))
        replacement_path.parent.mkdir(parents=True, exist_ok=True)
        replacement_path.write_text("{}", encoding="utf-8")

        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)

        self.assertEqual(guard["guard_status"], "BLOCKED")
        self.assertIn("STALE_LOOP_REPLACEMENT_ALREADY_EXISTS", guard["blocker_codes"])
        self.assertFalse(guard["paper_regeneration_preconditions_passed"])
        self.assertEqual(validate_upbit_paper_stale_loop_execution_guard(guard).status, "PASS")

    def test_execution_guard_blocks_source_hash_mismatch(self):
        root, plan = self._root_with_plan()
        plan["items"][0]["source_hash"] = "0" * 64
        plan["plan_hash"] = stale_loop_regeneration_plan_hash(plan)

        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)

        self.assertEqual(guard["guard_status"], "BLOCKED")
        self.assertIn("STALE_LOOP_SOURCE_HASH_MISMATCH", guard["blocker_codes"])
        self.assertEqual(validate_upbit_paper_stale_loop_execution_guard(guard).status, "PASS")

    def test_execution_guard_blocks_replacement_scope_escape(self):
        root, plan = self._root_with_plan()
        plan["items"][0]["planned_replacement_path"] = "system/runtime/upbit/krw_spot/live/mvp1/paper_runtime/escape.json"
        plan["plan_hash"] = stale_loop_regeneration_plan_hash(plan)

        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)

        self.assertEqual(guard["guard_status"], "BLOCKED")
        self.assertIn("SNAPSHOT_SCOPE_MISMATCH", guard["blocker_codes"])
        self.assertEqual(validate_upbit_paper_stale_loop_execution_guard(guard).status, "PASS")

    def test_execution_guard_blocks_delete_or_live_mutation(self):
        root, plan = self._root_with_plan()
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        guard["delete_source_allowed"] = True
        guard["guard_hash"] = stale_loop_execution_guard_hash(guard)

        result = validate_upbit_paper_stale_loop_execution_guard(guard)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_execution_guard_blocks_operator_review_plan(self):
        root, plan = self._root_with_plan()
        plan["plan_status"] = "BLOCKED"
        plan["primary_blocker_code"] = "STALE_LOOP_REGENERATION_OPERATOR_REVIEW_REQUIRED"
        plan["operator_review_item_count"] = 1
        plan["regeneration_item_count"] = 0
        plan["plan_hash"] = stale_loop_regeneration_plan_hash(plan)

        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)

        self.assertEqual(guard["guard_status"], "BLOCKED")
        self.assertIn("STALE_LOOP_REGENERATION_OPERATOR_REVIEW_REQUIRED", guard["blocker_codes"])
        self.assertFalse(guard["paper_regeneration_preconditions_passed"])
        self.assertEqual(validate_upbit_paper_stale_loop_execution_guard(guard).status, "PASS")


if __name__ == "__main__":
    unittest.main()
