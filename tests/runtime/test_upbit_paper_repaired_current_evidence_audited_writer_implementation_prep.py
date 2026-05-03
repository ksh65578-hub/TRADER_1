import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_implementation_prep import (
    AUDITED_WRITER_IMPLEMENTATION_PREP_STATUS,
    build_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report,
    upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash,
    validate_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_locked_output import (
    upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_LOCKED_OUTPUT_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_repaired_current_evidence_audited_writer_locked_output_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepTest(unittest.TestCase):
    def build_report(self, root: Path | None = None) -> dict:
        if root is None:
            with TemporaryDirectory() as tmp:
                return self.build_report(root=Path(tmp))
        return build_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
            root=root,
            source_audited_writer_locked_output_report=load_json(SOURCE_LOCKED_OUTPUT_PATH),
            audited_writer_implementation_prep_id=(
                "test-upbit-paper-repaired-current-evidence-audited-writer-implementation-prep"
            ),
        )

    def test_implementation_prep_checks_targets_without_enabling_writer(self):
        report = self.build_report()
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["implementation_prep_status"], AUDITED_WRITER_IMPLEMENTATION_PREP_STATUS)
        self.assertEqual(report["primary_blocker_code"], AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE)
        self.assertEqual(report["source_locked_output_control_pass_count"], 11)
        self.assertEqual(report["source_locked_output_control_blocked_count"], 1)
        self.assertEqual(report["implementation_prep_check_count"], 11)
        self.assertEqual(report["implementation_prep_check_pass_count"], 10)
        self.assertEqual(report["implementation_prep_check_blocked_count"], 1)
        self.assertTrue(report["implementation_prep_inputs_clean"])
        self.assertFalse(report["implementation_prep_passed"])
        self.assertFalse(report["writer_enabled"])
        self.assertFalse(report["lock_acquire_attempted"])
        self.assertFalse(report["lock_acquired"])
        self.assertFalse(report["lock_file_written"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["current_evidence_artifact_written"])
        self.assertFalse(report["idempotency_manifest_write_allowed"])
        self.assertFalse(report["idempotency_manifest_written"])
        self.assertFalse(report["portfolio_truth_write_allowed"])
        self.assertFalse(report["portfolio_truth_artifact_written"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_implementation_prep_target_states_are_safe_and_unwritten(self):
        report = self.build_report()
        expected_paths = [
            "paper_runtime/current_evidence/audited_current_evidence_snapshot.json",
            "paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json",
            "paper_runtime/portfolio/paper_portfolio_snapshot.json",
        ]

        self.assertEqual(report["planned_artifact_paths"], expected_paths)
        self.assertEqual(report["planned_temp_paths"], [f"{path}.tmp" for path in expected_paths])
        self.assertEqual(report["lock_path"], "paper_runtime/locks/audited_current_evidence_writer.lock")
        self.assertEqual(len(report["target_states"]), 3)
        for state in report["target_states"]:
            self.assertTrue(state["final_path_resolves_under_session"])
            self.assertTrue(state["temp_path_resolves_under_session"])
            self.assertFalse(state["final_exists"])
            self.assertFalse(state["temp_exists"])
            self.assertFalse(state["artifact_write_allowed"])
            self.assertFalse(state["artifact_written"])
            self.assertFalse(state["live_order_allowed"])
            self.assertFalse(state["scale_up_allowed"])

    def test_implementation_prep_manifest_is_prepared_not_written(self):
        report = self.build_report()
        manifest = report["pre_write_idempotency_manifest"]

        self.assertEqual(
            manifest["manifest_schema_id"],
            "trader1.upbit_paper_audited_writer_pre_write_idempotency_manifest.v1",
        )
        self.assertEqual(manifest["manifest_status"], "PREPARED_NOT_WRITTEN")
        self.assertEqual(manifest["target_state_hash"], report["target_state_hash"])
        self.assertFalse(manifest["manifest_write_allowed"])
        self.assertFalse(manifest["artifact_written"])
        self.assertFalse(manifest["current_evidence_write_allowed"])
        self.assertFalse(manifest["portfolio_truth_write_allowed"])
        self.assertFalse(manifest["live_order_allowed"])
        self.assertFalse(manifest["scale_up_allowed"])

    def test_blocks_writer_live_or_target_mutation(self):
        report = self.build_report()
        report["writer_enabled"] = True
        report["audited_writer_implementation_prep_hash"] = (
            upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash(report)
        )
        writer_result = validate_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
            report
        )
        self.assertEqual(writer_result.status, "BLOCKED")
        self.assertEqual(writer_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        live_report = self.build_report()
        live_report["implementation_prep_checks"][0]["live_order_allowed"] = True
        live_report["audited_writer_implementation_prep_hash"] = (
            upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash(live_report)
        )
        live_result = validate_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
            live_report
        )
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        target_report = self.build_report()
        target_report["target_states"][0]["final_exists"] = True
        target_report["target_state_hash"] = target_report["target_state_hash"]
        target_report["audited_writer_implementation_prep_hash"] = (
            upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash(target_report)
        )
        target_result = validate_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
            target_report
        )
        self.assertEqual(target_result.status, "FAIL")
        self.assertEqual(target_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_invalid_source_locked_output_stays_blocked_without_writer_permission(self):
        source = load_json(SOURCE_LOCKED_OUTPUT_PATH)
        source["lock_acquired"] = True
        source["audited_writer_locked_output_hash"] = (
            upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash(source)
        )

        report = build_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
            root=ROOT,
            source_audited_writer_locked_output_report=source,
            audited_writer_implementation_prep_id=(
                "test-upbit-paper-repaired-current-evidence-audited-writer-implementation-prep-invalid-source"
            ),
        )
        result = validate_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertEqual(report["implementation_prep_status"], "BLOCKED_SOURCE_LOCKED_OUTPUT_INVALID")
        self.assertFalse(report["writer_enabled"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["portfolio_truth_write_allowed"])
        self.assertFalse(report["live_order_allowed"])

    def test_writer_creates_implementation_prep_report_only(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(
                written.name,
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report.json",
            )
            loaded = load_json(written)
            self.assertEqual(
                validate_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
                    loaded
                ).status,
                "PASS",
            )
            self.assertFalse((written.parent / "current_evidence").exists())
            self.assertFalse((written.parent / "portfolio").exists())
            self.assertFalse((written.parent / "locks").exists())


if __name__ == "__main__":
    unittest.main()
