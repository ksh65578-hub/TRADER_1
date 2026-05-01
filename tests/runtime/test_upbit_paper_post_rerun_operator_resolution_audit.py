import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_resolution_audit import (
    POST_RERUN_OPERATOR_RESOLUTION_AUDIT_STATUS,
    POST_RERUN_OPERATOR_RESOLUTION_ITEM_STATUS,
    POST_RERUN_RESOLUTION_AUDIT_SOURCE_BINDING_REQUIRED,
    build_upbit_paper_post_rerun_operator_resolution_audit_report,
    upbit_paper_post_rerun_operator_resolution_audit_hash,
    validate_upbit_paper_post_rerun_operator_resolution_audit_report,
    write_upbit_paper_post_rerun_operator_resolution_audit_report,
)


ROOT = Path(__file__).resolve().parents[2]
SESSION_ID = "mvp1_upbit_paper_launcher"


class UpbitPaperPostRerunOperatorResolutionAuditTest(unittest.TestCase):
    def _runtime_path(self, name: str) -> Path:
        return (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / SESSION_ID
            / "paper_runtime"
            / name
        )

    def _source_reports(self) -> tuple[dict, dict, str, str]:
        guidance_path = self._runtime_path("upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json")
        decision_path = self._runtime_path("upbit_paper_post_rerun_reconciliation_decision_audit_report.json")
        guidance = json.loads(guidance_path.read_text(encoding="utf-8"))
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        return guidance, decision, guidance_path.relative_to(ROOT).as_posix(), decision_path.relative_to(ROOT).as_posix()

    def test_builds_review_only_resolution_audit_without_current_evidence_mutation(self):
        guidance, decision, guidance_path, decision_path = self._source_reports()

        report = build_upbit_paper_post_rerun_operator_resolution_audit_report(
            root=ROOT,
            review_guidance_report=guidance,
            decision_audit_report=decision,
            source_review_guidance_path=guidance_path,
            source_decision_audit_path=decision_path,
        )
        result = validate_upbit_paper_post_rerun_operator_resolution_audit_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["resolution_audit_status"], POST_RERUN_OPERATOR_RESOLUTION_AUDIT_STATUS)
        self.assertEqual(report["source_review_guidance_file_load_status"], "PASS")
        self.assertTrue(report["source_review_guidance_file_hash_match"])
        self.assertEqual(report["source_decision_audit_file_load_status"], "PASS")
        self.assertTrue(report["source_decision_audit_file_hash_match"])
        self.assertEqual(report["primary_blocker_code"], POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertEqual(report["reviewed_guidance_item_count"], guidance["guidance_item_count"])
        self.assertEqual(report["reviewed_decision_item_count"], decision["decision_item_count"])
        self.assertEqual(report["unresolved_item_count"], report["reviewed_guidance_item_count"])
        self.assertEqual(report["resolved_item_count"], 0)
        self.assertEqual(report["current_evidence_write_authorized_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["current_ledger_jsonl_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])

        item = report["items"][0]
        self.assertEqual(item["resolution_status"], POST_RERUN_OPERATOR_RESOLUTION_ITEM_STATUS)
        self.assertFalse(item["resolution_evidence_present"])
        self.assertFalse(item["resolution_evidence_accepted"])
        self.assertFalse(item["current_evidence_write_allowed"])

        with TemporaryDirectory() as tmp:
            path = write_upbit_paper_post_rerun_operator_resolution_audit_report(
                root=Path(tmp),
                report=report,
            )
            self.assertTrue(path.exists())

    def test_blocks_resolution_drift_live_mutation_and_path_escape(self):
        guidance, decision, guidance_path, decision_path = self._source_reports()
        report = build_upbit_paper_post_rerun_operator_resolution_audit_report(
            root=ROOT,
            review_guidance_report=guidance,
            decision_audit_report=decision,
            source_review_guidance_path=guidance_path,
            source_decision_audit_path=decision_path,
        )

        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["resolution_audit_hash"] = upbit_paper_post_rerun_operator_resolution_audit_hash(live_mutation)
        live_result = validate_upbit_paper_post_rerun_operator_resolution_audit_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        resolved = json.loads(json.dumps(report))
        resolved["items"][0]["resolution_evidence_present"] = True
        resolved["resolution_audit_hash"] = upbit_paper_post_rerun_operator_resolution_audit_hash(resolved)
        resolved_result = validate_upbit_paper_post_rerun_operator_resolution_audit_report(resolved)
        self.assertEqual(resolved_result.status, "BLOCKED")
        self.assertEqual(resolved_result.blocker_code, POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)

        path_escape = json.loads(json.dumps(report))
        path_escape["items"][0]["planned_current_ledger_jsonl_path"] = (
            "system/runtime/upbit/krw_spot/live/bad.paper_ledger_events.jsonl"
        )
        path_escape["resolution_audit_hash"] = upbit_paper_post_rerun_operator_resolution_audit_hash(path_escape)
        path_result = validate_upbit_paper_post_rerun_operator_resolution_audit_report(path_escape)
        self.assertEqual(path_result.status, "BLOCKED")
        self.assertEqual(path_result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_blocks_missing_source_files(self):
        guidance, decision, guidance_path, decision_path = self._source_reports()

        for missing_path, expected_status_key in (
            (guidance_path, "source_review_guidance_file_load_status"),
            (decision_path, "source_decision_audit_file_load_status"),
        ):
            with self.subTest(missing_path=missing_path), TemporaryDirectory() as tmp:
                root = Path(tmp)
                for relative_path, payload in ((guidance_path, guidance), (decision_path, decision)):
                    target = root / relative_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
                (root / missing_path).unlink()

                report = build_upbit_paper_post_rerun_operator_resolution_audit_report(
                    root=root,
                    review_guidance_report=guidance,
                    decision_audit_report=decision,
                    source_review_guidance_path=guidance_path,
                    source_decision_audit_path=decision_path,
                )
                result = validate_upbit_paper_post_rerun_operator_resolution_audit_report(report)

                self.assertEqual(report[expected_status_key], "MISSING")
                self.assertIn(POST_RERUN_RESOLUTION_AUDIT_SOURCE_BINDING_REQUIRED, report["blocker_codes"])
                self.assertEqual(result.status, "BLOCKED")
                self.assertEqual(result.blocker_code, POST_RERUN_RESOLUTION_AUDIT_SOURCE_BINDING_REQUIRED)


if __name__ == "__main__":
    unittest.main()
