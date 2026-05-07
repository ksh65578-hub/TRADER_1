import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_normalized_reconciliation_recheck import (
    NORMALIZED_RECONCILIATION_RECHECK_REQUIRES_LEDGER_ROLLUP_BLOCKER_CODE,
    build_upbit_paper_stale_loop_normalized_reconciliation_recheck_report,
    upbit_paper_stale_loop_normalized_reconciliation_recheck_hash,
    validate_upbit_paper_stale_loop_normalized_reconciliation_recheck_report,
    write_upbit_paper_stale_loop_normalized_reconciliation_recheck_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_normalized_reconciliation_preview import (
    build_upbit_paper_stale_loop_normalized_reconciliation_preview_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_replacement_schema_normalization_preview import (
    build_upbit_paper_stale_loop_replacement_schema_normalization_preview_report,
)


ROOT = Path(__file__).resolve().parents[2]
LEDGER_RECHECK_PREVIEW_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_ledger_recheck_preview_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperStaleLoopNormalizedReconciliationRecheckTest(unittest.TestCase):
    def build_report(self) -> dict:
        normalization_preview = build_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(
            root=ROOT,
            ledger_recheck_preview_report=load_json(LEDGER_RECHECK_PREVIEW_PATH),
            normalization_preview_id="test-stale-loop-normalized-reconciliation-recheck-source-normalization-preview",
        )
        normalized_reconciliation_preview = build_upbit_paper_stale_loop_normalized_reconciliation_preview_report(
            root=ROOT,
            normalization_preview_report=normalization_preview,
            normalized_reconciliation_preview_id="test-stale-loop-normalized-reconciliation-recheck-source-preview",
        )
        return build_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(
            root=ROOT,
            normalized_reconciliation_preview_report=normalized_reconciliation_preview,
            normalized_reconciliation_recheck_id="test-stale-loop-normalized-reconciliation-recheck",
        )

    def test_builds_display_only_normalized_reconciliation_recheck(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["recheck_status"], "BLOCKED")
        self.assertEqual(
            report["primary_blocker_code"],
            NORMALIZED_RECONCILIATION_RECHECK_REQUIRES_LEDGER_ROLLUP_BLOCKER_CODE,
        )
        self.assertEqual(report["normalized_reconciliation_recheck_candidate_count"], 5)
        self.assertEqual(report["normalized_hash_match_count"], 5)
        self.assertEqual(report["normalized_validation_blocked_count"], 5)
        self.assertEqual(report["ledger_rollup_recheck_required_count"], 5)
        self.assertEqual(report["recovery_guard_blocked_count"], 0)
        self.assertEqual(report["reconciliation_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_usable_after_recheck_count"], 0)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        reason_counts = {item["reason_code"]: item["count"] for item in report["reason_code_rollup"]}
        self.assertEqual(reason_counts["LEDGER_ROLLUP_BLOCKED"], 5)
        self.assertEqual(reason_counts["LEDGER_ROLLUP_RECONCILIATION_REQUIRED"], 5)
        self.assertEqual(reason_counts["NORMALIZED_RECONCILIATION_REQUIRED"], 5)
        self.assertEqual(reason_counts["RUNTIME_DEPTH_RECHECK_REQUIRED"], 5)
        self.assertTrue(all(item["ledger_rollup_recheck_required"] for item in report["items"]))
        self.assertTrue(all(item["normalized_hash_match"] for item in report["items"]))
        self.assertTrue(all(not item["preview_current_evidence_usable"] for item in report["items"]))

    def test_blocks_false_reconciliation_write_permission(self):
        report = self.build_report()
        report["reconciliation_write_allowed"] = True
        report["normalized_reconciliation_recheck_hash"] = upbit_paper_stale_loop_normalized_reconciliation_recheck_hash(report)

        result = validate_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_evidence_usability(self):
        report = self.build_report()
        report["items"][0]["preview_current_evidence_usable"] = True
        report["normalized_reconciliation_recheck_hash"] = upbit_paper_stale_loop_normalized_reconciliation_recheck_hash(report)

        result = validate_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_reason_rollup_drift(self):
        report = self.build_report()
        report["reason_code_rollup"][0]["count"] += 1
        report["normalized_reconciliation_recheck_hash"] = upbit_paper_stale_loop_normalized_reconciliation_recheck_hash(report)

        result = validate_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_writer_creates_recheck_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_stale_loop_normalized_reconciliation_recheck_report.json")
            self.assertEqual(
                validate_upbit_paper_stale_loop_normalized_reconciliation_recheck_report(load_json(written)).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
