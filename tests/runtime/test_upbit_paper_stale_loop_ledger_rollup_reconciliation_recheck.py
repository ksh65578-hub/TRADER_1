import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck import (
    LEDGER_ROLLUP_RECHECK_REQUIRES_ROLLUP_ARTIFACT_BLOCKER_CODE,
    build_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report,
    upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_hash,
    validate_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report,
    write_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report,
)


ROOT = Path(__file__).resolve().parents[2]
NORMALIZED_RECONCILIATION_RECHECK_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_normalized_reconciliation_recheck_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperStaleLoopLedgerRollupReconciliationRecheckTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(
            root=ROOT,
            normalized_reconciliation_recheck_report=load_json(NORMALIZED_RECONCILIATION_RECHECK_PATH),
            ledger_rollup_reconciliation_recheck_id="test-ledger-rollup-reconciliation-recheck",
        )

    def test_builds_blocked_display_only_ledger_rollup_recheck(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["recheck_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], LEDGER_ROLLUP_RECHECK_REQUIRES_ROLLUP_ARTIFACT_BLOCKER_CODE)
        self.assertEqual(report["ledger_rollup_recheck_candidate_count"], 5)
        self.assertEqual(report["ledger_rollup_artifact_exists_count"], 0)
        self.assertEqual(report["ledger_rollup_artifact_missing_count"], 5)
        self.assertEqual(report["ledger_rollup_hash_match_count"], 0)
        self.assertEqual(report["ledger_rollup_validator_pass_count"], 0)
        self.assertEqual(report["ledger_rollup_reconciliation_blocked_count"], 5)
        self.assertEqual(report["ledger_rollup_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        reason_counts = {item["reason_code"]: item["count"] for item in report["reason_code_rollup"]}
        self.assertEqual(reason_counts["LEDGER_ROLLUP_ARTIFACT_MISSING"], 5)
        self.assertEqual(reason_counts["LEDGER_ROLLUP_RECONCILIATION_REQUIRED"], 5)
        self.assertEqual(reason_counts["LEDGER_ROLLUP_HASH_NOT_RECONCILED"], 5)
        self.assertTrue(all(item["ledger_rollup_load_status"] == "MISSING" for item in report["items"]))
        self.assertTrue(all(not item["candidate_current_evidence_usable"] for item in report["items"]))

    def test_blocks_false_current_evidence_usability(self):
        report = self.build_report()
        report["items"][0]["candidate_current_evidence_usable"] = True
        report["ledger_rollup_reconciliation_recheck_hash"] = (
            upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_rollup_write_count(self):
        report = self.build_report()
        report["ledger_rollup_write_allowed_count"] = 1
        report["ledger_rollup_reconciliation_recheck_hash"] = (
            upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_hash_match_without_rollup_validator_pass(self):
        report = self.build_report()
        report["items"][0]["rollup_hash_match"] = True
        report["ledger_rollup_hash_match_count"] = 1
        report["ledger_rollup_reconciliation_recheck_hash"] = (
            upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_writer_creates_recheck_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(
                written.name,
                "upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report.json",
            )
            self.assertEqual(
                validate_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report(
                    load_json(written)
                ).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
