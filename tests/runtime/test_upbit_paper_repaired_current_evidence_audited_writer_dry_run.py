import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_design import (
    upbit_paper_repaired_current_evidence_audited_writer_design_hash,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_dry_run import (
    AUDITED_WRITER_DRY_RUN_STATUS,
    build_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report,
    upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash,
    validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DESIGN_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_repaired_current_evidence_audited_writer_design_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(
            root=ROOT,
            source_audited_writer_design_report=load_json(SOURCE_DESIGN_PATH),
            audited_writer_dry_run_id="test-upbit-paper-repaired-current-evidence-audited-writer-dry-run",
        )

    def test_dry_run_previews_writer_outputs_without_writing_truth(self):
        report = self.build_report()
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["dry_run_status"], AUDITED_WRITER_DRY_RUN_STATUS)
        self.assertEqual(report["primary_blocker_code"], AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE)
        self.assertEqual(report["dry_run_check_count"], 10)
        self.assertEqual(report["dry_run_check_pass_count"], 9)
        self.assertEqual(report["dry_run_check_blocked_count"], 1)
        self.assertFalse(report["dry_run_passed"])
        self.assertFalse(report["writer_enabled"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["current_evidence_artifact_written"])
        self.assertFalse(report["portfolio_truth_write_allowed"])
        self.assertFalse(report["portfolio_truth_artifact_written"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_dry_run_keeps_configured_capital_unverified_until_writer(self):
        report = self.build_report()
        current_preview = report["current_evidence_snapshot_preview"]
        portfolio_preview = report["portfolio_snapshot_preview"]

        self.assertEqual(current_preview["configured_initial_cash_krw"], 1000000)
        self.assertEqual(current_preview["configured_initial_cash_source"], "PAPER_CONFIG_ONLY_UNVERIFIED")
        self.assertEqual(current_preview["cash_status"], "UNVERIFIED")
        self.assertEqual(portfolio_preview["configured_initial_cash_krw"], 1000000)
        self.assertIsNone(portfolio_preview["verified_cash_krw"])
        self.assertEqual(portfolio_preview["portfolio_source_status"], "UNVERIFIED_UNTIL_AUDITED_WRITER")
        self.assertFalse(portfolio_preview["current_evidence_write_allowed"])
        self.assertFalse(portfolio_preview["portfolio_truth_write_allowed"])

    def test_dry_run_check_sequence_blocks_only_write_approval(self):
        report = self.build_report()
        checks = {check["check_id"]: check for check in report["dry_run_checks"]}

        for check_id in [
            "SOURCE_AUDITED_WRITER_DESIGN_VALID",
            "PLANNED_WRITE_TARGETS_PRESENT",
            "PRE_WRITE_CHECKS_PRESENT",
            "POST_WRITE_CHECKS_PRESENT",
            "IDEMPOTENCY_DRY_RUN_DIGEST_CREATED",
            "CURRENT_EVIDENCE_SNAPSHOT_PREVIEW_CREATED",
            "PORTFOLIO_TRUTH_PREVIEW_CREATED",
            "ATOMIC_WRITE_PLAN_PREVIEW_CREATED",
            "LIVE_AND_SCALE_BOUNDARY_CONFIRMED",
        ]:
            self.assertEqual(checks[check_id]["check_status"], "PASS")
        self.assertEqual(checks["CURRENT_EVIDENCE_WRITE_APPROVAL_GRANTED"]["check_status"], "BLOCKED")
        self.assertEqual(
            checks["CURRENT_EVIDENCE_WRITE_APPROVAL_GRANTED"]["blocker_code"],
            AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
        )
        for check in report["dry_run_checks"]:
            self.assertFalse(check["current_evidence_write_allowed"])
            self.assertFalse(check["portfolio_truth_write_allowed"])
            self.assertFalse(check["live_order_allowed"])
            self.assertFalse(check["scale_up_allowed"])

    def test_blocks_writer_live_or_preview_permission_mutation(self):
        report = self.build_report()
        report["current_evidence_artifact_written"] = True
        report["audited_writer_dry_run_hash"] = upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash(
            report
        )
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        live_report = self.build_report()
        live_report["live_order_allowed"] = True
        live_report["audited_writer_dry_run_hash"] = upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash(
            live_report
        )
        live_result = validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(live_report)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        preview_report = self.build_report()
        preview_report["portfolio_snapshot_preview"]["portfolio_truth_write_allowed"] = True
        preview_report["portfolio_snapshot_preview_hash"] = preview_report["portfolio_snapshot_preview_hash"]
        preview_report["audited_writer_dry_run_hash"] = upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash(
            preview_report
        )
        preview_result = validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(preview_report)
        self.assertEqual(preview_result.status, "FAIL")
        self.assertEqual(preview_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_invalid_source_design_stays_blocked_without_writer_permission(self):
        source = load_json(SOURCE_DESIGN_PATH)
        source["current_evidence_write_allowed"] = True
        source["audited_writer_design_hash"] = upbit_paper_repaired_current_evidence_audited_writer_design_hash(source)

        report = build_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(
            root=ROOT,
            source_audited_writer_design_report=source,
            audited_writer_dry_run_id="test-upbit-paper-repaired-current-evidence-audited-writer-dry-run-invalid-source",
        )
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertEqual(report["dry_run_status"], "BLOCKED_SOURCE_DESIGN_INVALID")
        self.assertFalse(report["writer_enabled"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["portfolio_truth_write_allowed"])

    def test_writer_creates_dry_run_report_only(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_repaired_current_evidence_audited_writer_dry_run_report.json")
            loaded = load_json(written)
            self.assertEqual(
                validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(loaded).status,
                "PASS",
            )
            self.assertFalse((written.parent / "current_evidence").exists())
            self.assertFalse((written.parent / "portfolio").exists())


if __name__ == "__main__":
    unittest.main()
