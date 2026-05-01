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
    stale_loop_reconciliation_hash,
)
from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import (
    build_upbit_paper_stale_loop_regeneration_plan,
    stale_loop_regeneration_plan_hash,
    validate_upbit_paper_stale_loop_regeneration_plan,
    write_upbit_paper_stale_loop_regeneration_plan,
)


class UpbitPaperStaleLoopRegenerationPlanTest(unittest.TestCase):
    def _root_with_legacy_loop(self) -> tuple[Path, dict]:
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
        return root, reconciliation

    def test_regeneration_plan_maps_legacy_sources_to_new_paths_without_execution(self):
        root, reconciliation = self._root_with_legacy_loop()
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        result = validate_upbit_paper_stale_loop_regeneration_plan(plan)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(plan["plan_status"], "READY_FOR_SAFE_PAPER_REGENERATION")
        self.assertEqual(plan["regeneration_item_count"], 1)
        self.assertEqual(plan["operator_review_item_count"], 0)
        self.assertFalse(plan["automatic_regeneration_allowed"])
        self.assertFalse(plan["actual_regeneration_performed"])
        self.assertFalse(plan["delete_source_allowed"])
        self.assertFalse(plan["overwrite_source_allowed"])
        self.assertFalse(plan["live_order_ready"])
        self.assertFalse(plan["live_order_allowed"])
        self.assertFalse(plan["can_live_trade"])
        self.assertFalse(plan["scale_up_allowed"])
        item = plan["items"][0]
        self.assertEqual(item["planned_action"], "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT")
        self.assertNotEqual(item["planned_replacement_path"], item["source_path"])
        self.assertIn("regenerated-current-schema", item["planned_replacement_path"])
        self.assertFalse(item["delete_source_allowed"])
        self.assertFalse(item["overwrite_source_allowed"])

        written_path = write_upbit_paper_stale_loop_regeneration_plan(root=root, plan=plan)
        written = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_stale_loop_regeneration_plan(written).status, "PASS")

    def test_regeneration_plan_blocks_delete_or_overwrite_mutation(self):
        root, reconciliation = self._root_with_legacy_loop()
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        plan["items"][0]["overwrite_source_allowed"] = True
        plan["plan_hash"] = stale_loop_regeneration_plan_hash(plan)

        result = validate_upbit_paper_stale_loop_regeneration_plan(plan)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_regeneration_plan_blocks_live_or_long_run_mutation(self):
        root, reconciliation = self._root_with_legacy_loop()
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        plan["actual_long_run_evidence_created"] = True
        plan["plan_hash"] = stale_loop_regeneration_plan_hash(plan)

        result = validate_upbit_paper_stale_loop_regeneration_plan(plan)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_regeneration_plan_blocks_current_source_inclusion(self):
        root, reconciliation = self._root_with_legacy_loop()
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        plan["items"][0]["source_evidence_usable_current"] = True
        plan["plan_hash"] = stale_loop_regeneration_plan_hash(plan)

        result = validate_upbit_paper_stale_loop_regeneration_plan(plan)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "STALE_LOOP_REGENERATION_REQUIRED")

    def test_regeneration_plan_maps_reconciliation_required_to_operator_review(self):
        root, reconciliation = self._root_with_legacy_loop()
        legacy_index = next(
            index for index, item in enumerate(reconciliation["items"])
            if item["classification"] == "LEGACY_SCHEMA_DRIFT"
        )
        reconciliation["items"][legacy_index]["classification"] = "RECONCILIATION_REQUIRED"
        reconciliation["items"][legacy_index]["recommended_action"] = "REGENERATE_WITH_CURRENT_SCHEMA"
        reconciliation["legacy_schema_drift_count"] = 0
        reconciliation["legacy_reference_retained_count"] = 0
        reconciliation["reconciliation_hash"] = ""
        reconciliation["reconciliation_hash"] = stale_loop_reconciliation_hash(reconciliation)

        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        result = validate_upbit_paper_stale_loop_regeneration_plan(plan)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(plan["plan_status"], "BLOCKED")
        self.assertEqual(plan["primary_blocker_code"], "STALE_LOOP_REGENERATION_OPERATOR_REVIEW_REQUIRED")
        self.assertEqual(plan["operator_review_item_count"], 1)
        self.assertEqual(plan["regeneration_item_count"], 0)
        self.assertEqual(plan["items"][0]["planned_action"], "OPERATOR_REVIEW_REQUIRED")
        self.assertEqual(plan["items"][0]["blocking_reason"], "RECONCILIATION_REQUIRED_OPERATOR_REVIEW")

    def test_regeneration_plan_blocks_replacement_path_collision(self):
        root, _ = self._root_with_legacy_loop()
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
        legacy_copy = json.loads(legacy_path.read_text(encoding="utf-8"))
        copy_path = legacy_path.with_name("legacy-loop-copy.persistent_loop_report.json")
        copy_path.write_text(json.dumps(legacy_copy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root)

        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)

        self.assertEqual(plan["plan_status"], "BLOCKED")
        self.assertEqual(plan["primary_blocker_code"], "STALE_LOOP_REPLACEMENT_PATH_COLLISION")
        self.assertEqual(validate_upbit_paper_stale_loop_regeneration_plan(plan).status, "PASS")


if __name__ == "__main__":
    unittest.main()
