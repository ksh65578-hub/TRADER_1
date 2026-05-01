import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_paper_post_rerun_resolution_current_evidence_closure import (
    POST_RERUN_RESOLUTION_CLOSURE_SOURCE_BINDING_REQUIRED,
    POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_ITEM_STATUS,
    POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED,
    POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_STATUS,
    build_upbit_paper_post_rerun_resolution_current_evidence_closure_report,
    upbit_paper_post_rerun_resolution_current_evidence_closure_hash,
    validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report,
    write_upbit_paper_post_rerun_resolution_current_evidence_closure_report,
)


ROOT = Path(__file__).resolve().parents[2]
SESSION_ID = "mvp1_upbit_paper_launcher"


class UpbitPaperPostRerunResolutionCurrentEvidenceClosureTest(unittest.TestCase):
    def _source_path(self) -> Path:
        return (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / SESSION_ID
            / "paper_runtime"
            / "upbit_paper_post_rerun_operator_resolution_audit_report.json"
        )

    def _source_report(self) -> tuple[dict, str]:
        source_path = self._source_path()
        source = json.loads(source_path.read_text(encoding="utf-8"))
        return source, source_path.relative_to(ROOT).as_posix()

    def test_builds_closure_without_current_evidence_mutation(self):
        source, source_path = self._source_report()

        report = build_upbit_paper_post_rerun_resolution_current_evidence_closure_report(
            root=ROOT,
            resolution_audit_report=source,
            source_resolution_audit_path=source_path,
        )
        result = validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["closure_status"], POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_STATUS)
        self.assertEqual(report["primary_blocker_code"], POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertEqual(report["source_resolution_audit_file_load_status"], "PASS")
        self.assertTrue(report["source_resolution_audit_file_hash_match"])
        self.assertEqual(report["source_unresolved_item_count"], source["unresolved_item_count"])
        self.assertEqual(report["closed_item_count"], source["unresolved_item_count"])
        self.assertEqual(report["unresolved_item_count"], source["unresolved_item_count"])
        self.assertEqual(report["resolved_item_count"], 0)
        self.assertEqual(report["current_evidence_write_authorized_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertIn(POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED, report["blocker_codes"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["current_ledger_jsonl_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])

        item = report["closure_items"][0]
        self.assertEqual(item["closure_status"], POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_ITEM_STATUS)
        self.assertFalse(item["current_evidence_write_authorized"])
        self.assertFalse(item["candidate_current_evidence_usable"])
        self.assertFalse(item["live_order_allowed"])

        with TemporaryDirectory() as tmp:
            path = write_upbit_paper_post_rerun_resolution_current_evidence_closure_report(
                root=Path(tmp),
                report=report,
            )
            self.assertTrue(path.exists())

    def test_blocks_live_mutation_resolution_drift_and_path_escape(self):
        source, source_path = self._source_report()
        report = build_upbit_paper_post_rerun_resolution_current_evidence_closure_report(
            root=ROOT,
            resolution_audit_report=source,
            source_resolution_audit_path=source_path,
        )

        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["closure_hash"] = upbit_paper_post_rerun_resolution_current_evidence_closure_hash(live_mutation)
        live_result = validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        resolution_drift = json.loads(json.dumps(report))
        resolution_drift["closure_items"][0]["source_resolution_evidence_present"] = True
        resolution_drift["closure_hash"] = upbit_paper_post_rerun_resolution_current_evidence_closure_hash(resolution_drift)
        drift_result = validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report(resolution_drift)
        self.assertEqual(drift_result.status, "BLOCKED")
        self.assertEqual(drift_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        path_escape = json.loads(json.dumps(report))
        path_escape["closure_items"][0]["planned_current_ledger_jsonl_path"] = (
            "system/runtime/upbit/krw_spot/live/bad.paper_ledger_events.jsonl"
        )
        path_escape["closure_hash"] = upbit_paper_post_rerun_resolution_current_evidence_closure_hash(path_escape)
        path_result = validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report(path_escape)
        self.assertEqual(path_result.status, "BLOCKED")
        self.assertEqual(path_result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_blocks_missing_source_resolution_audit_file(self):
        source, source_path = self._source_report()

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / source_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(source, sort_keys=True), encoding="utf-8")
            target.unlink()

            report = build_upbit_paper_post_rerun_resolution_current_evidence_closure_report(
                root=root,
                resolution_audit_report=source,
                source_resolution_audit_path=source_path,
            )
            result = validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report(report)

            self.assertEqual(report["source_resolution_audit_file_load_status"], "MISSING")
            self.assertIn(POST_RERUN_RESOLUTION_CLOSURE_SOURCE_BINDING_REQUIRED, report["blocker_codes"])
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, POST_RERUN_RESOLUTION_CLOSURE_SOURCE_BINDING_REQUIRED)


if __name__ == "__main__":
    unittest.main()
