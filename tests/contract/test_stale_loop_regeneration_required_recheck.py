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
    / "MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK.patch_result.json"
)
PLAN_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_regeneration_plan.json"
)
REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-RECHECK"
NEXT_TASK = "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK"
BLOCKER = "STALE_LOOP_REGENERATION_REQUIRED"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class StaleLoopRegenerationRequiredRecheckTest(unittest.TestCase):
    def test_regeneration_plan_remains_ready_but_non_executing(self):
        plan = load_json(PLAN_PATH)

        self.assertEqual(plan["plan_status"], "READY_FOR_SAFE_PAPER_REGENERATION")
        self.assertIsNone(plan["primary_blocker_code"])
        self.assertEqual(plan["source_loop_report_count"], 17)
        self.assertEqual(plan["source_current_accepted_count"], 1)
        self.assertEqual(plan["source_excluded_count"], 16)
        self.assertEqual(plan["legacy_schema_drift_count"], 16)
        self.assertEqual(plan["regeneration_item_count"], 16)
        self.assertEqual(plan["operator_review_item_count"], 0)
        self.assertEqual(plan["duplicate_replacement_path_count"], 0)
        self.assertEqual(plan["overwrite_or_delete_count"], 0)
        self.assertFalse(plan["automatic_regeneration_allowed"])
        self.assertFalse(plan["operator_confirmation_required_before_execution"])
        self.assertFalse(plan["delete_source_allowed"])
        self.assertFalse(plan["overwrite_source_allowed"])
        self.assertFalse(plan["actual_regeneration_performed"])
        self.assertFalse(plan["actual_long_run_evidence_created"])
        self.assertFalse(plan["long_run_evidence_eligible"])
        self.assertFalse(plan["promotion_eligible"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(plan[field])

    def test_regeneration_items_are_source_preserving_paper_replacements(self):
        plan = load_json(PLAN_PATH)
        replacement_paths = []

        for item in plan["items"]:
            self.assertEqual(item["source_classification"], "LEGACY_SCHEMA_DRIFT")
            self.assertFalse(item["source_evidence_usable_current"])
            self.assertEqual(item["planned_action"], "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT")
            self.assertIn("regenerated-current-schema", item["planned_replacement_path"])
            self.assertNotEqual(item["planned_replacement_path"], item["source_path"])
            self.assertTrue(
                item["planned_replacement_path"].startswith(
                    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/"
                )
            )
            self.assertFalse(item["overwrite_source_allowed"])
            self.assertFalse(item["delete_source_allowed"])
            self.assertFalse(item["automatic_live_or_order_allowed"])
            self.assertFalse(item["requires_operator_review"])
            self.assertFalse(item["live_order_ready"])
            self.assertFalse(item["live_order_allowed"])
            self.assertFalse(item["can_live_trade"])
            self.assertFalse(item["scale_up_allowed"])
            replacement_paths.append(item["planned_replacement_path"])

        self.assertEqual(len(replacement_paths), len(set(replacement_paths)))

    def test_recheck_patch_routes_to_execution_required_without_live_or_scale_permission(self):
        if not PATCH_PATH.exists():
            self.skipTest("stale loop regeneration required recheck patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK)
        self.assertIn(BLOCKER, patch_result["remaining_blockers"])
        self.assertIn("STALE_LOOP_REGENERATION_EXECUTION_REQUIRED", patch_result["remaining_blockers"])
        self.assertEqual(patch_result["stale_loop_regeneration_plan_status"], "READY_FOR_SAFE_PAPER_REGENERATION")
        self.assertEqual(patch_result["stale_loop_regeneration_item_count"], 16)
        self.assertEqual(patch_result["stale_loop_regeneration_operator_review_item_count"], 0)
        self.assertEqual(patch_result["stale_loop_regeneration_duplicate_replacement_path_count"], 0)
        self.assertEqual(patch_result["stale_loop_regeneration_overwrite_or_delete_count"], 0)
        self.assertFalse(patch_result["stale_loop_regeneration_actual_regeneration_performed"])
        self.assertFalse(patch_result["stale_loop_regeneration_automatic_regeneration_allowed"])
        self.assertFalse(patch_result["stale_loop_regeneration_delete_source_allowed"])
        self.assertFalse(patch_result["stale_loop_regeneration_overwrite_source_allowed"])

        if REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK)
        self.assertIn(BLOCKER, state["open_contract_gap_ids"])
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
