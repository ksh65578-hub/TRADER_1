import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_replacement_schema_normalization_preview import (
    POST_NORMALIZATION_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    build_upbit_paper_stale_loop_replacement_schema_normalization_preview_report,
    upbit_paper_stale_loop_replacement_schema_normalization_preview_hash,
    validate_upbit_paper_stale_loop_replacement_schema_normalization_preview_report,
    write_upbit_paper_stale_loop_replacement_schema_normalization_preview_report,
)


ROOT = Path(__file__).resolve().parents[2]
PREVIEW_PATH = (
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


class UpbitPaperStaleLoopReplacementSchemaNormalizationPreviewTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(
            root=ROOT,
            ledger_recheck_preview_report=load_json(PREVIEW_PATH),
            normalization_preview_id="test-stale-loop-replacement-schema-normalization-preview",
        )

    def test_builds_display_only_normalization_preview(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["preview_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], POST_NORMALIZATION_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertEqual(report["normalization_candidate_count"], 5)
        self.assertEqual(report["replacement_path_exists_count"], 5)
        self.assertEqual(report["missing_field_total_count"], 35)
        self.assertEqual(report["proposed_field_total_count"], 35)
        self.assertEqual(report["proposed_current_evidence_write_true_count"], 5)
        self.assertEqual(report["normalized_schema_fail_count"], 0)
        self.assertEqual(report["normalized_reconciliation_blocked_count"], 5)
        self.assertEqual(report["ready_preview_only_count"], 5)
        self.assertEqual(report["normalization_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_usable_after_normalization_preview_count"], 0)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertTrue(all(item["normalization_item_status"] == "READY_PREVIEW_ONLY" for item in report["items"]))
        self.assertTrue(all(item["normalized_validation_status"] == "BLOCKED" for item in report["items"]))
        self.assertTrue(all(not item["normalization_write_allowed"] for item in report["items"]))

    def test_blocks_false_normalization_write_permission(self):
        report = self.build_report()
        report["normalization_write_allowed"] = True
        report["normalization_preview_hash"] = upbit_paper_stale_loop_replacement_schema_normalization_preview_hash(report)

        result = validate_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_evidence_usability(self):
        report = self.build_report()
        report["items"][0]["preview_current_evidence_usable"] = True
        report["normalization_preview_hash"] = upbit_paper_stale_loop_replacement_schema_normalization_preview_hash(report)

        result = validate_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_ready_preview_with_schema_identity_mismatch(self):
        report = self.build_report()
        report["items"][0]["normalized_validation_blocker_code"] = "SCHEMA_IDENTITY_MISMATCH"
        report["normalization_preview_hash"] = upbit_paper_stale_loop_replacement_schema_normalization_preview_hash(report)

        result = validate_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_writer_creates_preview_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(
                written.name,
                "upbit_paper_stale_loop_replacement_schema_normalization_preview_report.json",
            )
            self.assertEqual(
                validate_upbit_paper_stale_loop_replacement_schema_normalization_preview_report(
                    load_json(written)
                ).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
