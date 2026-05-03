import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.ledger.paper_ledger_rollup import paper_ledger_rollup_hash
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer import (
    AUDITED_WRITER_BLOCKED_LEDGER_STATUS,
    AUDITED_WRITER_BLOCKED_SOURCE_STATUS,
    AUDITED_WRITER_BLOCKED_TARGET_STATUS,
    AUDITED_WRITER_IDEMPOTENT_STATUS,
    AUDITED_WRITER_WRITTEN_STATUS,
    EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS,
    build_upbit_paper_repaired_current_evidence_audited_writer_report,
    upbit_paper_repaired_current_evidence_audited_writer_report_hash,
    validate_upbit_paper_audited_current_evidence_idempotency_manifest,
    validate_upbit_paper_audited_current_evidence_snapshot,
    validate_upbit_paper_repaired_current_evidence_audited_writer_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_implementation_prep import (
    upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash,
)
from trader1.runtime.portfolio.paper_portfolio import validate_paper_portfolio_snapshot


ROOT = Path(__file__).resolve().parents[2]
SESSION_ID = "mvp1_upbit_paper_launcher"
RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
SOURCE_IMPLEMENTATION_PREP_PATH = (
    RUNTIME_BASE
    / "paper_runtime"
    / "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report.json"
)
SOURCE_LEDGER_ROLLUP_PATH = RUNTIME_BASE / "ledger" / "paper_ledger_rollup_report.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperRepairedCurrentEvidenceAuditedWriterTest(unittest.TestCase):
    def source_implementation_prep(self) -> dict:
        return load_json(SOURCE_IMPLEMENTATION_PREP_PATH)

    def source_ledger_rollup(self) -> dict:
        return load_json(SOURCE_LEDGER_ROLLUP_PATH)

    def build_report(self, root: Path, *, prep: dict | None = None, ledger: dict | None = None) -> dict:
        return build_upbit_paper_repaired_current_evidence_audited_writer_report(
            root=root,
            source_implementation_prep_report=prep or self.source_implementation_prep(),
            source_ledger_rollup_report=ledger or self.source_ledger_rollup(),
            audited_writer_id="test-upbit-paper-repaired-current-evidence-audited-writer",
        )

    def test_writer_publishes_verified_paper_current_evidence(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self.build_report(root)
            result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(report["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertTrue(report["writer_passed"])
            self.assertEqual(report["writer_control_pass_count"], 11)
            self.assertEqual(report["writer_control_blocked_count"], 0)
            self.assertEqual(report["artifact_written_count"], 3)
            self.assertFalse(report["lock_present_after_run"])
            self.assertFalse(report["live_order_ready"])
            self.assertFalse(report["live_order_allowed"])
            self.assertFalse(report["can_live_trade"])
            self.assertFalse(report["scale_up_allowed"])

            runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            current_evidence = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
            manifest = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[1])
            portfolio = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])

            self.assertEqual(validate_upbit_paper_audited_current_evidence_snapshot(current_evidence).status, "PASS")
            self.assertEqual(
                validate_upbit_paper_audited_current_evidence_idempotency_manifest(manifest).status,
                "PASS",
            )
            self.assertEqual(validate_paper_portfolio_snapshot(portfolio).status, "PASS")
            self.assertEqual(current_evidence["portfolio_truth_status"], "VERIFIED_PAPER_LEDGER_ROLLUP")
            self.assertEqual(current_evidence["cash_status"], "VERIFIED")
            self.assertEqual(current_evidence["configured_initial_cash_krw"], "1000000")
            self.assertEqual(portfolio["source"], "PAPER_LEDGER_ROLLUP")
            self.assertEqual(portfolio["starting_cash"], "1000000")
            self.assertEqual(portfolio["cash_available"], "845923")
            self.assertEqual(portfolio["open_position_count"], 1)

            written_path = write_upbit_paper_repaired_current_evidence_audited_writer_report(
                root=root,
                report=report,
            )
            self.assertTrue(written_path.exists())
            loaded = load_json(written_path)
            self.assertEqual(
                validate_upbit_paper_repaired_current_evidence_audited_writer_report(loaded).status,
                "PASS",
            )

    def test_writer_is_idempotent_when_outputs_match_sources(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.build_report(root)
            second = self.build_report(root)

            self.assertEqual(first["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertEqual(second["writer_status"], AUDITED_WRITER_IDEMPOTENT_STATUS)
            self.assertEqual(second["artifact_written_count"], 0)
            self.assertEqual(second["artifact_reused_count"], 3)
            self.assertTrue(second["idempotent_replay"])
            self.assertEqual(validate_upbit_paper_repaired_current_evidence_audited_writer_report(second).status, "PASS")

    def test_invalid_source_implementation_prep_blocks_writer(self):
        with TemporaryDirectory() as tmp:
            prep = self.source_implementation_prep()
            prep["live_order_allowed"] = True
            prep["audited_writer_implementation_prep_hash"] = (
                upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash(prep)
            )

            report = self.build_report(Path(tmp), prep=prep)
            result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(report["writer_status"], AUDITED_WRITER_BLOCKED_SOURCE_STATUS)
            self.assertFalse(report["writer_passed"])
            self.assertEqual(report["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
            self.assertEqual(report["artifact_written_count"], 0)
            self.assertFalse(report["live_order_allowed"])

    def test_invalid_ledger_rollup_blocks_writer(self):
        with TemporaryDirectory() as tmp:
            ledger = self.source_ledger_rollup()
            ledger["ledger_head_match_status"] = "MISMATCH"
            ledger["primary_blocker_code"] = "LEDGER_INTEGRITY_FAIL"
            ledger["blockers"] = [
                {
                    "code": "LEDGER_INTEGRITY_FAIL",
                    "severity": "HIGH",
                    "message": "test ledger head mismatch",
                }
            ]
            ledger["rollup_status"] = "BLOCKED"
            ledger["rollup_hash"] = paper_ledger_rollup_hash(ledger)

            report = self.build_report(Path(tmp), ledger=ledger)
            result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(report["writer_status"], AUDITED_WRITER_BLOCKED_LEDGER_STATUS)
            self.assertFalse(report["writer_passed"])
            self.assertEqual(report["primary_blocker_code"], "LEDGER_INTEGRITY_FAIL")
            self.assertEqual(report["artifact_written_count"], 0)

    def test_partial_existing_target_blocks_writer(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            partial_path = runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0]
            partial_path.parent.mkdir(parents=True, exist_ok=True)
            partial_path.write_text("{}\n", encoding="utf-8")

            report = self.build_report(root)
            result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(report["writer_status"], AUDITED_WRITER_BLOCKED_TARGET_STATUS)
            self.assertFalse(report["writer_passed"])
            self.assertEqual(report["primary_blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
            self.assertEqual(report["artifact_written_count"], 0)

    def test_report_validation_blocks_live_mutation(self):
        with TemporaryDirectory() as tmp:
            report = self.build_report(Path(tmp))
            report["live_order_allowed"] = True
            report["audited_writer_report_hash"] = upbit_paper_repaired_current_evidence_audited_writer_report_hash(
                report
            )
            result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
