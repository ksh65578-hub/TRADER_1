import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import (
    NEXT_TASK_CLASS,
    OPEN_GAP_RECHECK_REQUIREMENTS,
    build_open_gap_current_blocker_classification_report,
    validate_open_gap_current_blocker_classification_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-OPEN-GAP-CURRENT-BLOCKER-CLASSIFICATION"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class OpenGapCurrentBlockerClassificationTest(unittest.TestCase):
    def test_current_state_classifies_all_open_gaps_as_residual_blockers(self):
        state = load_json(STATE_PATH)
        report = build_open_gap_current_blocker_classification_report(
            state,
            patch_id="TEST_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

        self.assertEqual(report["open_gap_count"], len(state["open_contract_gap_ids"]))
        self.assertEqual(report["completed_recheck_gap_count"], len(state["open_contract_gap_ids"]))
        self.assertTrue(report["all_open_gaps_have_completed_recheck"])
        self.assertFalse(report["repeat_completed_recheck_selected"])
        self.assertEqual(report["remaining_implementation_recheck_gap_ids"], [])
        self.assertEqual(report["residual_blocked_gap_ids"], sorted(state["open_contract_gap_ids"]))
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["blocker_category_counts"]["UNCLASSIFIED_OPEN_GAP"], 0)

        completed = set(state["completed_requirement_ids"])
        for gap_id, requirement_id in OPEN_GAP_RECHECK_REQUIREMENTS.items():
            self.assertIn(gap_id, state["open_contract_gap_ids"])
            self.assertIn(requirement_id, completed)
        self.assertEqual(validate_open_gap_current_blocker_classification_report(report, state), [])

    def test_generated_report_matches_schema_and_keeps_live_flags_false(self):
        if not REPORT_PATH.exists():
            self.skipTest("open gap current blocker classification report has not been generated yet")
        state = load_json(STATE_PATH)
        report = load_json(REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(validate_open_gap_current_blocker_classification_report(report, state), [])

        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_routes_to_residual_blocker_classification(self):
        if not PATCH_PATH.exists():
            self.skipTest("open gap current blocker classification patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(REPORT_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION_20260505_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])


if __name__ == "__main__":
    unittest.main()
