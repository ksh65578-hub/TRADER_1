import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_open_gap_operator_action_plan import (
    FORBIDDEN_ACTIONS,
    build_residual_open_gap_operator_action_plan_report,
    validate_residual_open_gap_operator_action_plan_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
CLASSIFICATION_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION.report.json"
)
REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPEN-GAP-OPERATOR-ACTION-PLAN"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOpenGapOperatorActionPlanTest(unittest.TestCase):
    def test_current_classification_builds_operator_action_plan(self):
        state = load_json(STATE_PATH)
        classification = load_json(CLASSIFICATION_REPORT_PATH)
        report = build_residual_open_gap_operator_action_plan_report(
            classification,
            state,
            patch_id="TEST_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["total_action_gap_count"], report["open_gap_count"])
        self.assertEqual(report["implementation_recheck_action_count"], 0)
        self.assertTrue(report["external_or_operator_action_required"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["classification_validation_status"], "PASS")
        self.assertEqual(report["classification_validation_errors"], [])

        action_counts = {item["action_class"]: item["gap_count"] for item in report["action_items"]}
        self.assertEqual(action_counts["OPERATOR_RECONCILIATION_ACTION"], 4)
        self.assertEqual(action_counts["PAPER_LEDGER_RERUN_RECONCILIATION_ACTION"], 3)
        self.assertEqual(action_counts["PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION"], 3)
        self.assertEqual(action_counts["EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION"], 1)
        self.assertEqual(action_counts["SEALED_BASELINE_PRESERVATION_ACTION"], 1)
        self.assertEqual(action_counts["SCALE_UP_POLICY_EVIDENCE_ACTION"], 1)

        for action in report["action_items"]:
            self.assertFalse(action["allows_live_order"])
            self.assertFalse(action["allows_live_config_mutation"])
            self.assertFalse(action["allows_scale_up"])
            for forbidden in FORBIDDEN_ACTIONS:
                self.assertIn(forbidden, action["forbidden_actions"])
        self.assertEqual(validate_residual_open_gap_operator_action_plan_report(report, classification, state), [])

    def test_generated_report_matches_schema_and_keeps_live_flags_false(self):
        if not REPORT_PATH.exists():
            self.skipTest("residual open gap operator action plan report has not been generated yet")
        state = load_json(STATE_PATH)
        classification = load_json(CLASSIFICATION_REPORT_PATH)
        report = load_json(REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(validate_residual_open_gap_operator_action_plan_report(report, classification, state), [])

        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_blocker_route(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual open gap operator action plan patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(REPORT_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN_20260505_001")
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
