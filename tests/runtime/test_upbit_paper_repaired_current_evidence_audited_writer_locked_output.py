import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_dry_run import (
    upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_locked_output import (
    AUDITED_WRITER_LOCKED_OUTPUT_STATUS,
    build_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report,
    upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash,
    validate_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DRY_RUN_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_repaired_current_evidence_audited_writer_dry_run_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(
            root=ROOT,
            source_audited_writer_dry_run_report=load_json(SOURCE_DRY_RUN_PATH),
            audited_writer_locked_output_id="test-upbit-paper-repaired-current-evidence-audited-writer-locked-output",
        )

    def test_locked_output_scaffold_fixes_targets_without_writing_truth(self):
        report = self.build_report()
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["locked_output_status"], AUDITED_WRITER_LOCKED_OUTPUT_STATUS)
        self.assertEqual(report["primary_blocker_code"], AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE)
        self.assertEqual(report["locked_output_control_count"], 12)
        self.assertEqual(report["locked_output_control_pass_count"], 11)
        self.assertEqual(report["locked_output_control_blocked_count"], 1)
        self.assertFalse(report["locked_output_passed"])
        self.assertFalse(report["writer_enabled"])
        self.assertFalse(report["lock_acquired"])
        self.assertFalse(report["lock_file_written"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["current_evidence_artifact_written"])
        self.assertFalse(report["portfolio_truth_write_allowed"])
        self.assertFalse(report["portfolio_truth_artifact_written"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_locked_output_keeps_configured_capital_unverified(self):
        report = self.build_report()
        current_payload = report["current_evidence_locked_payload"]
        portfolio_payload = report["portfolio_truth_locked_payload"]

        self.assertEqual(current_payload["source_preview"]["configured_initial_cash_krw"], 1000000)
        self.assertEqual(current_payload["source_preview"]["cash_status"], "UNVERIFIED")
        self.assertEqual(portfolio_payload["source_preview"]["configured_initial_cash_krw"], 1000000)
        self.assertIsNone(portfolio_payload["source_preview"]["verified_cash_krw"])
        self.assertEqual(
            portfolio_payload["source_preview"]["portfolio_source_status"],
            "UNVERIFIED_UNTIL_AUDITED_WRITER",
        )
        self.assertFalse(current_payload["artifact_write_allowed"])
        self.assertFalse(portfolio_payload["artifact_write_allowed"])

    def test_locked_output_plan_has_only_locked_relative_targets(self):
        report = self.build_report()
        expected_paths = [
            "paper_runtime/current_evidence/audited_current_evidence_snapshot.json",
            "paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json",
            "paper_runtime/portfolio/paper_portfolio_snapshot.json",
        ]

        self.assertEqual(report["planned_artifact_paths"], expected_paths)
        self.assertEqual(report["planned_temp_paths"], [f"{path}.tmp" for path in expected_paths])
        self.assertEqual(report["lock_path"], "paper_runtime/locks/audited_current_evidence_writer.lock")
        plan = report["locked_write_plan"]
        self.assertEqual(plan["planned_artifact_paths"], expected_paths)
        self.assertFalse(plan["plan_write_allowed"])
        for output in plan["locked_outputs"]:
            self.assertTrue(output["relative_temp_path"].endswith(".tmp"))
            self.assertFalse(output["artifact_write_allowed"])
            self.assertFalse(output["artifact_written"])

    def test_blocks_locked_output_permission_mutations(self):
        report = self.build_report()
        report["lock_acquired"] = True
        report["audited_writer_locked_output_hash"] = (
            upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash(report)
        )
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        live_report = self.build_report()
        live_report["locked_output_controls"][0]["live_order_allowed"] = True
        live_report["audited_writer_locked_output_hash"] = (
            upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash(live_report)
        )
        live_result = validate_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(live_report)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        plan_report = self.build_report()
        plan_report["locked_write_plan"]["locked_outputs"][0]["artifact_write_allowed"] = True
        plan_report["locked_write_plan"]["plan_hash"] = plan_report["locked_write_plan"]["plan_hash"]
        plan_report["audited_writer_locked_output_hash"] = (
            upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash(plan_report)
        )
        plan_result = validate_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(plan_report)
        self.assertEqual(plan_result.status, "FAIL")
        self.assertEqual(plan_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_invalid_source_dry_run_stays_blocked_without_write_permission(self):
        source = load_json(SOURCE_DRY_RUN_PATH)
        source["current_evidence_artifact_written"] = True
        source["audited_writer_dry_run_hash"] = upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash(
            source
        )

        report = build_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(
            root=ROOT,
            source_audited_writer_dry_run_report=source,
            audited_writer_locked_output_id="test-upbit-paper-repaired-current-evidence-audited-writer-locked-output-invalid-source",
        )
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertEqual(report["locked_output_status"], "BLOCKED_SOURCE_DRY_RUN_INVALID")
        self.assertFalse(report["writer_enabled"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["portfolio_truth_write_allowed"])

    def test_writer_creates_locked_output_report_only(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(
                written.name,
                "upbit_paper_repaired_current_evidence_audited_writer_locked_output_report.json",
            )
            loaded = load_json(written)
            self.assertEqual(
                validate_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(loaded).status,
                "PASS",
            )
            self.assertFalse((written.parent / "current_evidence").exists())
            self.assertFalse((written.parent / "portfolio").exists())
            self.assertFalse((written.parent / "locks").exists())


if __name__ == "__main__":
    unittest.main()
