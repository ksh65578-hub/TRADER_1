import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_ledger_input_scope_repair_plan import (
    LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE,
    build_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report,
    upbit_paper_stale_loop_ledger_input_scope_repair_plan_hash,
    validate_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report,
    write_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report,
)


ROOT = Path(__file__).resolve().parents[2]
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
LEDGER_ROLLUP_EXECUTOR_RECHECK_PATH = (
    RUNTIME_BASE / "upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report.json"
)
LEDGER_ROLLUP_REGENERATION_PLAN_PATH = (
    RUNTIME_BASE / "upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperStaleLoopLedgerInputScopeRepairPlanTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(
            root=ROOT,
            ledger_rollup_executor_reconciliation_recheck_report=load_json(LEDGER_ROLLUP_EXECUTOR_RECHECK_PATH),
            ledger_rollup_regeneration_plan_report=load_json(LEDGER_ROLLUP_REGENERATION_PLAN_PATH),
            ledger_input_scope_repair_plan_id="test-ledger-input-scope-repair-plan",
        )

    def test_builds_plan_only_isolated_candidate_mirror_report(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["plan_status"], "READY_PLAN_ONLY")
        self.assertEqual(report["primary_blocker_code"], LEDGER_INPUT_SCOPE_REPAIR_PLAN_BLOCKER_CODE)
        self.assertEqual(report["repair_plan_candidate_count"], 4)
        self.assertEqual(report["repair_plan_ready_count"], 4)
        self.assertEqual(report["repair_plan_blocked_count"], 0)
        self.assertEqual(report["planned_cycle_count"], 8)
        self.assertEqual(report["repair_cycle_ready_count"], 8)
        self.assertEqual(report["missing_source_ledger_count"], 0)
        self.assertEqual(report["source_ledger_event_count"], 42)
        self.assertEqual(report["planned_mirror_ledger_count"], 8)
        self.assertEqual(report["candidate_mirror_write_allowed_count"], 0)
        self.assertEqual(report["current_canonical_ledger_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(report["automatic_execution_allowed"])
        self.assertFalse(report["candidate_mirror_write_allowed"])
        self.assertFalse(report["current_canonical_ledger_write_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_blocks_false_execution_permission(self):
        report = self.build_report()
        report["automatic_execution_allowed"] = True
        report["ledger_input_scope_repair_plan_hash"] = upbit_paper_stale_loop_ledger_input_scope_repair_plan_hash(
            report
        )

        result = validate_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_ledger_write_count(self):
        report = self.build_report()
        report["current_canonical_ledger_write_allowed_count"] = 1
        report["ledger_input_scope_repair_plan_hash"] = upbit_paper_stale_loop_ledger_input_scope_repair_plan_hash(
            report
        )

        result = validate_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_ready_count(self):
        report = self.build_report()
        report["repair_cycle_ready_count"] = 7
        report["ledger_input_scope_repair_plan_hash"] = upbit_paper_stale_loop_ledger_input_scope_repair_plan_hash(
            report
        )

        result = validate_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_writer_creates_plan_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_stale_loop_ledger_input_scope_repair_plan_report.json")
            self.assertEqual(
                validate_upbit_paper_stale_loop_ledger_input_scope_repair_plan_report(load_json(written)).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
