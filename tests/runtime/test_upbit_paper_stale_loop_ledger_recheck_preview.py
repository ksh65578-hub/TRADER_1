import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_ledger_recheck_preview import (
    PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED_BLOCKER_CODE,
    build_upbit_paper_stale_loop_ledger_recheck_preview_report,
    upbit_paper_stale_loop_ledger_recheck_preview_hash,
    validate_upbit_paper_stale_loop_ledger_recheck_preview_report,
    write_upbit_paper_stale_loop_ledger_recheck_preview_report,
)


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher"
CLOSURE_PATH = RUNTIME_BASE / "paper_runtime" / "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json"
LEDGER_PATH = RUNTIME_BASE / "ledger" / "upbit_paper_ledger_idempotency_runtime_evidence_report.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperStaleLoopLedgerRecheckPreviewTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_stale_loop_ledger_recheck_preview_report(
            root=ROOT,
            closure_report=load_json(CLOSURE_PATH),
            ledger_idempotency_evidence_report=load_json(LEDGER_PATH),
            preview_id="test-stale-loop-ledger-recheck-preview",
        )

    def test_builds_blocked_display_only_preview_without_evidence_writes(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_ledger_recheck_preview_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["preview_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED_BLOCKER_CODE)
        self.assertEqual(report["item_count"], 6)
        self.assertEqual(report["ledger_recheck_candidate_count"], 5)
        self.assertEqual(report["ledger_binding_pass_count"], 5)
        self.assertEqual(report["ledger_binding_blocked_count"], 0)
        self.assertEqual(report["replacement_path_exists_count"], 6)
        self.assertEqual(report["replacement_validation_pass_count"], 0)
        self.assertEqual(report["replacement_validation_fail_count"], 5)
        self.assertEqual(report["preview_pass_count"], 0)
        self.assertEqual(report["preview_blocked_count"], 5)
        self.assertEqual(report["skipped_recovery_guard_required_count"], 1)
        self.assertEqual(report["current_evidence_usable_after_preview_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertTrue(all(not item["preview_current_evidence_usable"] for item in report["items"]))

    def test_blocks_false_current_evidence_usability(self):
        report = self.build_report()
        report["items"][0]["preview_current_evidence_usable"] = True
        report["preview_hash"] = upbit_paper_stale_loop_ledger_recheck_preview_hash(report)

        result = validate_upbit_paper_stale_loop_ledger_recheck_preview_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_pass_when_replacement_schema_is_not_validated(self):
        report = self.build_report()
        report["items"][0]["preview_item_status"] = "PASS_PREVIEW_ONLY"
        report["preview_pass_count"] = 1
        report["preview_blocked_count"] = 4
        report["preview_hash"] = upbit_paper_stale_loop_ledger_recheck_preview_hash(report)

        result = validate_upbit_paper_stale_loop_ledger_recheck_preview_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_fails_ledger_binding_false_pass(self):
        report = self.build_report()
        report["items"][0]["ledger_binding_status"] = "PASS"
        report["items"][0]["ledger_head_hash_match"] = False
        report["preview_hash"] = upbit_paper_stale_loop_ledger_recheck_preview_hash(report)

        result = validate_upbit_paper_stale_loop_ledger_recheck_preview_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_writer_creates_preview_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for item in report["items"]:
                source = ROOT / item["replacement_path"]
                target = root / item["replacement_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            written = write_upbit_paper_stale_loop_ledger_recheck_preview_report(root=root, report=report)

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_stale_loop_ledger_recheck_preview_report.json")
            persisted = load_json(written)
            self.assertEqual(validate_upbit_paper_stale_loop_ledger_recheck_preview_report(persisted).status, "PASS")


if __name__ == "__main__":
    unittest.main()
