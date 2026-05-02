import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
    AUDITED_CURRENT_EVIDENCE_WRITER_PRECHECK_STATUS,
    build_upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
    upbit_paper_repaired_current_evidence_audited_writer_precheck_hash,
    validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard import (
    upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_GUARD_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(
            root=ROOT,
            source_current_evidence_guard_report=load_json(SOURCE_GUARD_PATH),
            audited_writer_precheck_id="test-upbit-paper-repaired-current-evidence-audited-writer-precheck",
        )

    def test_precheck_keeps_writer_disabled_after_clean_guard_inputs(self):
        report = self.build_report()
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertTrue(report["audit_inputs_clean"])
        self.assertEqual(report["audited_writer_precheck_status"], AUDITED_CURRENT_EVIDENCE_WRITER_PRECHECK_STATUS)
        self.assertEqual(report["primary_blocker_code"], AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE)
        self.assertEqual(report["source_candidate_count"], 3)
        self.assertEqual(report["source_guard_review_ready_count"], 3)
        self.assertEqual(report["source_clean_candidate_count"], 3)
        self.assertEqual(report["source_duplicate_total_count"], 0)
        self.assertEqual(report["source_ledger_jsonl_count"], 6)
        self.assertEqual(report["source_ledger_event_count"], 36)
        self.assertEqual(report["source_filled_order_count"], 6)
        self.assertEqual(report["audit_gate_count"], 7)
        self.assertEqual(report["audit_gate_pass_count"], 6)
        self.assertEqual(report["audit_gate_blocked_count"], 1)
        self.assertEqual(report["audited_writer_candidate_ready_count"], 3)
        self.assertFalse(report["audited_writer_precheck_passed"])
        self.assertFalse(report["audited_writer_enabled"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["portfolio_truth_write_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_gate_list_blocks_only_missing_audited_writer(self):
        report = self.build_report()
        gates = {gate["gate_id"]: gate for gate in report["audit_gates"]}

        self.assertEqual(gates["SOURCE_CURRENT_EVIDENCE_GUARD_VALID"]["gate_status"], "PASS")
        self.assertEqual(gates["CLEAN_REPAIRED_CANDIDATES_PRESENT"]["gate_status"], "PASS")
        self.assertEqual(gates["DUPLICATE_TOTAL_ZERO"]["gate_status"], "PASS")
        self.assertEqual(gates["LEDGER_COUNTS_PRESENT"]["gate_status"], "PASS")
        self.assertEqual(gates["SOURCE_WRITE_COUNTS_ZERO"]["gate_status"], "PASS")
        self.assertEqual(gates["SOURCE_LIVE_AND_SCALE_FALSE"]["gate_status"], "PASS")
        self.assertEqual(gates["AUDITED_WRITER_IMPLEMENTATION_PRESENT"]["gate_status"], "BLOCKED")
        self.assertEqual(
            gates["AUDITED_WRITER_IMPLEMENTATION_PRESENT"]["gate_blocker_code"],
            AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
        )
        for gate in report["audit_gates"]:
            self.assertFalse(gate["current_evidence_write_allowed"])
            self.assertFalse(gate["portfolio_truth_write_allowed"])
            self.assertFalse(gate["live_order_allowed"])
            self.assertFalse(gate["scale_up_allowed"])

    def test_blocks_false_writer_or_live_permission(self):
        report = self.build_report()
        report["audited_writer_enabled"] = True
        report["audited_writer_precheck_hash"] = upbit_paper_repaired_current_evidence_audited_writer_precheck_hash(
            report
        )

        writer_result = validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(report)
        self.assertEqual(writer_result.status, "BLOCKED")
        self.assertEqual(writer_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        live_report = self.build_report()
        live_report["live_order_allowed"] = True
        live_report["audited_writer_precheck_hash"] = (
            upbit_paper_repaired_current_evidence_audited_writer_precheck_hash(live_report)
        )
        live_result = validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(live_report)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_gate_aggregate(self):
        report = self.build_report()
        report["audit_gate_pass_count"] = 7
        report["audited_writer_precheck_hash"] = upbit_paper_repaired_current_evidence_audited_writer_precheck_hash(
            report
        )

        result = validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_invalid_source_guard_stays_blocked_without_writer_permission(self):
        source = load_json(SOURCE_GUARD_PATH)
        source["current_evidence_write_allowed_count"] = 1
        source["event_id_scope_repaired_current_evidence_guard_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash(source)
        )

        report = build_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(
            root=ROOT,
            source_current_evidence_guard_report=source,
            audited_writer_precheck_id="test-upbit-paper-repaired-current-evidence-source-invalid",
        )
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(report["audit_inputs_clean"])
        self.assertEqual(report["audited_writer_precheck_status"], "BLOCKED_SOURCE_GUARD_INVALID")
        self.assertEqual(report["source_current_evidence_write_allowed_count"], 1)
        self.assertFalse(report["audited_writer_precheck_passed"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])

    def test_writer_creates_precheck_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(
                written.name,
                "upbit_paper_repaired_current_evidence_audited_writer_precheck_report.json",
            )
            loaded = load_json(written)
            self.assertEqual(
                validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(loaded).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
