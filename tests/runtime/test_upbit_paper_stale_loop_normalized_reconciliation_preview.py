import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_normalized_reconciliation_preview import (
    NORMALIZED_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    build_upbit_paper_stale_loop_normalized_reconciliation_preview_report,
    upbit_paper_stale_loop_normalized_reconciliation_preview_hash,
    validate_upbit_paper_stale_loop_normalized_reconciliation_preview_report,
    write_upbit_paper_stale_loop_normalized_reconciliation_preview_report,
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


class UpbitPaperStaleLoopNormalizedReconciliationPreviewTest(unittest.TestCase):
    def build_report(self) -> dict:
        normalization_preview = build_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(
            root=ROOT,
            ledger_recheck_preview_report=load_json(LEDGER_RECHECK_PREVIEW_PATH),
            normalization_preview_id="test-stale-loop-normalized-reconciliation-source-normalization-preview",
        )
        return build_upbit_paper_stale_loop_normalized_reconciliation_preview_report(
            root=ROOT,
            normalization_preview_report=normalization_preview,
            normalized_reconciliation_preview_id="test-stale-loop-normalized-reconciliation-preview",
        )

    def test_builds_display_only_normalized_reconciliation_preview(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_normalized_reconciliation_preview_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["preview_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], NORMALIZED_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertEqual(report["normalized_reconciliation_candidate_count"], 5)
        self.assertEqual(report["schema_normalization_resolved_count"], 5)
        self.assertEqual(report["reconciliation_required_count"], 5)
        self.assertEqual(report["schema_mismatch_after_normalization_count"], 0)
        self.assertEqual(report["reconciliation_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_usable_after_reconciliation_preview_count"], 0)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertTrue(all(item["schema_normalization_resolved"] for item in report["items"]))
        self.assertTrue(all(item["reconciliation_required"] for item in report["items"]))
        self.assertTrue(all(not item["reconciliation_write_allowed"] for item in report["items"]))
        self.assertTrue(all(not item["preview_current_evidence_usable"] for item in report["items"]))

    def test_blocks_false_reconciliation_write_permission(self):
        report = self.build_report()
        report["reconciliation_write_allowed"] = True
        report["normalized_reconciliation_preview_hash"] = upbit_paper_stale_loop_normalized_reconciliation_preview_hash(report)

        result = validate_upbit_paper_stale_loop_normalized_reconciliation_preview_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_evidence_usability(self):
        report = self.build_report()
        report["items"][0]["preview_current_evidence_usable"] = True
        report["normalized_reconciliation_preview_hash"] = upbit_paper_stale_loop_normalized_reconciliation_preview_hash(report)

        result = validate_upbit_paper_stale_loop_normalized_reconciliation_preview_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_reconciliation_required_without_reconciliation_blocker(self):
        report = self.build_report()
        report["items"][0]["normalized_validation_blocker_code"] = "OTHER_BLOCKER"
        report["normalized_reconciliation_preview_hash"] = upbit_paper_stale_loop_normalized_reconciliation_preview_hash(report)

        result = validate_upbit_paper_stale_loop_normalized_reconciliation_preview_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_writer_creates_preview_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_normalized_reconciliation_preview_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_stale_loop_normalized_reconciliation_preview_report.json")
            self.assertEqual(
                validate_upbit_paper_stale_loop_normalized_reconciliation_preview_report(load_json(written)).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
