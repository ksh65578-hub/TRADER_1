import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_design import (
    AUDITED_WRITER_DESIGN_STATUS,
    build_upbit_paper_repaired_current_evidence_audited_writer_design_report,
    upbit_paper_repaired_current_evidence_audited_writer_design_hash,
    validate_upbit_paper_repaired_current_evidence_audited_writer_design_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_design_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
    upbit_paper_repaired_current_evidence_audited_writer_precheck_hash,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PRECHECK_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_repaired_current_evidence_audited_writer_precheck_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_repaired_current_evidence_audited_writer_design_report(
            root=ROOT,
            source_audited_writer_precheck_report=load_json(SOURCE_PRECHECK_PATH),
            audited_writer_design_id="test-upbit-paper-repaired-current-evidence-audited-writer-design",
        )

    def test_design_specifies_writer_controls_without_enabling_writes(self):
        report = self.build_report()
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_design_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["design_status"], AUDITED_WRITER_DESIGN_STATUS)
        self.assertFalse(report["design_passed"])
        self.assertEqual(report["primary_blocker_code"], AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE)
        self.assertEqual(report["source_audited_writer_candidate_ready_count"], 3)
        self.assertEqual(report["source_audit_gate_pass_count"], 6)
        self.assertEqual(report["source_audit_gate_blocked_count"], 1)
        self.assertEqual(report["design_control_count"], 8)
        self.assertEqual(report["design_control_pass_count"], 7)
        self.assertEqual(report["design_control_blocked_count"], 1)
        self.assertFalse(report["writer_implementation_allowed"])
        self.assertFalse(report["writer_enabled"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["portfolio_truth_write_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_design_control_sequence_blocks_only_missing_writer_approval(self):
        report = self.build_report()
        controls = {control["control_id"]: control for control in report["design_controls"]}

        for control_id in [
            "SOURCE_AUDITED_WRITER_PRECHECK_VALID",
            "SINGLE_WRITER_LOCK_DISCIPLINE_SPECIFIED",
            "IDEMPOTENCY_MANIFEST_SPECIFIED",
            "ATOMIC_WRITE_RENAME_SPECIFIED",
            "POST_WRITE_RECONCILIATION_SPECIFIED",
            "PORTFOLIO_TRUTH_PROVENANCE_SPECIFIED",
            "LIVE_AND_SCALE_BOUNDARY_SPECIFIED",
        ]:
            self.assertEqual(controls[control_id]["control_status"], "PASS")
        self.assertEqual(controls["WRITER_IMPLEMENTATION_APPROVED"]["control_status"], "BLOCKED")
        self.assertEqual(
            controls["WRITER_IMPLEMENTATION_APPROVED"]["blocker_code"],
            AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
        )
        for control in report["design_controls"]:
            self.assertFalse(control["current_evidence_write_allowed"])
            self.assertFalse(control["portfolio_truth_write_allowed"])
            self.assertFalse(control["live_order_allowed"])
            self.assertFalse(control["scale_up_allowed"])

    def test_blocks_writer_or_live_permission_mutation(self):
        report = self.build_report()
        report["writer_enabled"] = True
        report["audited_writer_design_hash"] = upbit_paper_repaired_current_evidence_audited_writer_design_hash(report)

        writer_result = validate_upbit_paper_repaired_current_evidence_audited_writer_design_report(report)
        self.assertEqual(writer_result.status, "BLOCKED")
        self.assertEqual(writer_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        live_report = self.build_report()
        live_report["live_order_allowed"] = True
        live_report["audited_writer_design_hash"] = upbit_paper_repaired_current_evidence_audited_writer_design_hash(
            live_report
        )
        live_result = validate_upbit_paper_repaired_current_evidence_audited_writer_design_report(live_report)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_design_aggregate(self):
        report = self.build_report()
        report["design_control_pass_count"] = 8
        report["audited_writer_design_hash"] = upbit_paper_repaired_current_evidence_audited_writer_design_hash(report)

        result = validate_upbit_paper_repaired_current_evidence_audited_writer_design_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_invalid_source_precheck_stays_blocked_without_writer_permission(self):
        source = load_json(SOURCE_PRECHECK_PATH)
        source["current_evidence_write_allowed"] = True
        source["audited_writer_precheck_hash"] = upbit_paper_repaired_current_evidence_audited_writer_precheck_hash(
            source
        )

        report = build_upbit_paper_repaired_current_evidence_audited_writer_design_report(
            root=ROOT,
            source_audited_writer_precheck_report=source,
            audited_writer_design_id="test-upbit-paper-repaired-current-evidence-audited-writer-design-invalid-source",
        )
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_design_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertEqual(report["design_status"], "BLOCKED_SOURCE_PRECHECK_INVALID")
        self.assertFalse(report["design_passed"])
        self.assertFalse(report["writer_enabled"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])

    def test_writer_creates_design_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_repaired_current_evidence_audited_writer_design_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_repaired_current_evidence_audited_writer_design_report.json")
            loaded = load_json(written)
            self.assertEqual(validate_upbit_paper_repaired_current_evidence_audited_writer_design_report(loaded).status, "PASS")


if __name__ == "__main__":
    unittest.main()
