import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck import (
    LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_BLOCKER_CODE,
    build_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report,
    upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_hash,
    validate_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report,
    write_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report,
)


ROOT = Path(__file__).resolve().parents[2]
LEDGER_ROLLUP_EXECUTOR_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(
            root=ROOT,
            ledger_rollup_regeneration_executor_report=load_json(LEDGER_ROLLUP_EXECUTOR_PATH),
            ledger_rollup_executor_reconciliation_recheck_id="test-ledger-rollup-executor-recheck",
        )

    def test_builds_candidate_recheck_current_evidence_blocked_report(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["recheck_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_BLOCKER_CODE)
        self.assertEqual(report["candidate_recheck_attempt_count"], 5)
        self.assertEqual(report["candidate_recheck_pass_count"], 1)
        self.assertEqual(report["candidate_recheck_blocked_count"], 4)
        self.assertEqual(report["source_candidate_rollup_artifact_ready_count"], 1)
        self.assertEqual(report["candidate_rollup_artifact_exists_count"], 1)
        self.assertEqual(report["candidate_rollup_artifact_validator_pass_count"], 1)
        self.assertEqual(report["candidate_rollup_hash_match_count"], 1)
        self.assertEqual(report["strict_input_scope_blocked_count"], 4)
        self.assertEqual(report["target_rollup_artifact_exists_count"], 0)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertEqual(report["target_rollup_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_blocks_false_live_permission(self):
        report = self.build_report()
        report["live_order_allowed"] = True
        report["ledger_rollup_executor_reconciliation_recheck_hash"] = (
            upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_evidence_write_count(self):
        report = self.build_report()
        report["current_evidence_write_allowed_count"] = 1
        report["ledger_rollup_executor_reconciliation_recheck_hash"] = (
            upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_pass_count(self):
        report = self.build_report()
        report["candidate_recheck_pass_count"] = 0
        report["ledger_rollup_executor_reconciliation_recheck_hash"] = (
            upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_writer_creates_recheck_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(
                written.name,
                "upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report.json",
            )
            self.assertEqual(
                validate_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(
                    load_json(written)
                ).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
