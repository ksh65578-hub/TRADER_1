import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_paper_ledger_rerun_readiness import (
    LEDGER_RERUN_GAP_IDS,
    build_residual_paper_ledger_rerun_readiness_report,
    load_runtime_source_reports,
    validate_residual_paper_ledger_rerun_readiness_report,
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
    / "MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-PAPER-LEDGER-RERUN-READINESS"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualPaperLedgerRerunReadinessTest(unittest.TestCase):
    def test_current_runtime_sources_build_blocked_readiness_report(self):
        state = load_json(STATE_PATH)
        sources = load_runtime_source_reports(ROOT)
        report = build_residual_paper_ledger_rerun_readiness_report(
            sources,
            state,
            patch_id="TEST_RESIDUAL_PAPER_LEDGER_RERUN_READINESS",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

        self.assertEqual(tuple(report["gap_ids"]), LEDGER_RERUN_GAP_IDS)
        self.assertEqual(report["gap_count"], 3)
        self.assertEqual(report["readiness_status"], "BLOCKED_RECONCILIATION_REQUIRED")
        self.assertEqual(report["bounded_staging_status"], "PASS")
        self.assertEqual(report["bounded_executor_status"], "BLOCKED")
        self.assertEqual(report["post_rerun_ledger_rollup_status"], "PASS")
        self.assertEqual(report["post_rerun_reconciliation_status"], "BLOCKED")
        self.assertEqual(report["current_evidence_bridge_status"], "BLOCKED_BY_POST_RERUN_CLOSURE")
        self.assertEqual(report["operator_queue_status"], "BLOCKED")
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["current_evidence_mutation_allowed"])
        self.assertFalse(report["latest_runtime_pointer_write_allowed"])
        self.assertFalse(report["actual_rerun_executed"])
        self.assertTrue(report["operator_reconciliation_required"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(validate_residual_paper_ledger_rerun_readiness_report(report, sources, state), [])

    def test_generated_report_matches_schema_and_keeps_live_flags_false(self):
        if not REPORT_PATH.exists():
            self.skipTest("residual paper ledger rerun readiness report has not been generated yet")
        state = load_json(STATE_PATH)
        sources = load_runtime_source_reports(ROOT)
        report = load_json(REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(validate_residual_paper_ledger_rerun_readiness_report(report, sources, state), [])

        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_blocker_route(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual paper ledger rerun readiness patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(REPORT_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS_20260505_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_live_or_current_evidence_permission(self):
        state = load_json(STATE_PATH)
        sources = load_runtime_source_reports(ROOT)
        report = build_residual_paper_ledger_rerun_readiness_report(
            sources,
            state,
            patch_id="TEST_RESIDUAL_PAPER_LEDGER_RERUN_READINESS",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

        tampered = copy.deepcopy(report)
        tampered["live_order_allowed"] = True
        tampered["current_evidence_write_allowed"] = True
        errors = validate_residual_paper_ledger_rerun_readiness_report(tampered, sources, state)
        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("current_evidence_write_allowed" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
