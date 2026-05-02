import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_ledger_rollup_regeneration_plan import (
    LEDGER_ROLLUP_REGENERATION_PLAN_BLOCKER_CODE,
    build_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report,
    upbit_paper_stale_loop_ledger_rollup_regeneration_plan_hash,
    validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report,
    write_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report,
)


ROOT = Path(__file__).resolve().parents[2]
LEDGER_ROLLUP_RECHECK_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperStaleLoopLedgerRollupRegenerationPlanTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(
            root=ROOT,
            ledger_rollup_reconciliation_recheck_report=load_json(LEDGER_ROLLUP_RECHECK_PATH),
            ledger_rollup_regeneration_plan_id="test-ledger-rollup-regeneration-plan",
        )

    def test_builds_plan_only_input_complete_report(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["plan_status"], "READY_PLAN_ONLY")
        self.assertEqual(report["primary_blocker_code"], LEDGER_ROLLUP_REGENERATION_PLAN_BLOCKER_CODE)
        self.assertEqual(report["plan_candidate_count"], 5)
        self.assertEqual(report["plan_ready_count"], 5)
        self.assertEqual(report["plan_blocked_count"], 0)
        self.assertEqual(report["planned_cycle_count"], 9)
        self.assertEqual(report["cycle_regeneration_input_ready_count"], 9)
        self.assertEqual(report["missing_input_ledger_count"], 0)
        self.assertEqual(report["candidate_rollup_reference_present_count"], 9)
        self.assertEqual(report["post_rollup_candidate_reference_count"], 8)
        self.assertEqual(report["repair_candidate_reference_count"], 1)
        self.assertFalse(report["automatic_execution_allowed"])
        self.assertFalse(report["ledger_rollup_write_allowed"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_blocks_false_execution_permission(self):
        report = self.build_report()
        report["automatic_execution_allowed"] = True
        report["ledger_rollup_regeneration_plan_hash"] = upbit_paper_stale_loop_ledger_rollup_regeneration_plan_hash(
            report
        )

        result = validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_cycle_current_evidence_write(self):
        report = self.build_report()
        report["items"][0]["cycles"][0]["current_evidence_write_allowed"] = True
        report["ledger_rollup_regeneration_plan_hash"] = upbit_paper_stale_loop_ledger_rollup_regeneration_plan_hash(
            report
        )

        result = validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_ready_cycle_without_candidate_reference(self):
        report = self.build_report()
        report["items"][0]["cycles"][0]["candidate_rollup_reference_exists"] = False
        report["ledger_rollup_regeneration_plan_hash"] = upbit_paper_stale_loop_ledger_rollup_regeneration_plan_hash(
            report
        )

        result = validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_writer_creates_plan_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report.json")
            self.assertEqual(
                validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(load_json(written)).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
