import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report,
    upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash,
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report,
    write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report,
)


ROOT = Path(__file__).resolve().parents[2]
REPAIRED_DUPLICATE_RECHECK_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report.json"
)
OPERATOR_GUIDANCE_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperStaleLoopIsolatedEventIdScopeRepairedCurrentEvidenceGuardTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
            root=ROOT,
            event_id_scope_repaired_duplicate_recheck_report=load_json(REPAIRED_DUPLICATE_RECHECK_PATH),
            operator_review_guidance_report=load_json(OPERATOR_GUIDANCE_PATH),
            event_id_scope_repaired_current_evidence_guard_id="test-event-id-repaired-current-evidence-guard",
        )

    def test_blocks_current_evidence_writes_after_clean_repaired_duplicate_recheck(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
            report
        )

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["current_evidence_guard_status"], "BLOCKED_CURRENT_EVIDENCE_WRITE_DENIED")
        self.assertEqual(report["primary_blocker_code"], POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertEqual(report["candidate_count"], 3)
        self.assertEqual(report["guard_review_ready_count"], 3)
        self.assertEqual(report["guard_blocked_count"], 3)
        self.assertEqual(report["clean_candidate_count"], 3)
        self.assertEqual(report["duplicate_total_count"], 0)
        self.assertEqual(report["ledger_jsonl_count"], 6)
        self.assertEqual(report["ledger_event_count"], 36)
        self.assertEqual(report["filled_order_count"], 6)
        self.assertTrue(report["operator_guidance_loaded"])
        self.assertEqual(report["operator_guidance_item_count"], 8)
        self.assertEqual(report["operator_guidance_forbidden_output_count"], 6)
        self.assertEqual(report["operator_guidance_current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertEqual(report["portfolio_truth_write_allowed_count"], 0)
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["portfolio_truth_write_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_items_remain_review_only_candidate_evidence(self):
        report = self.build_report()

        for item in report["items"]:
            self.assertEqual(item["guard_item_status"], "REVIEW_READY_CURRENT_EVIDENCE_BLOCKED")
            self.assertEqual(item["item_blocker_code"], POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
            self.assertTrue(item["candidate_rollup_artifact_path_allowed"])
            self.assertTrue(item["candidate_rollup_hash_match"])
            self.assertEqual(item["duplicate_total_count"], 0)
            self.assertEqual(item["repaired_ledger_path_count"], 2)
            self.assertFalse(item["candidate_current_evidence_usable"])
            self.assertFalse(item["current_evidence_write_allowed"])
            self.assertFalse(item["portfolio_truth_write_allowed"])
            self.assertFalse(item["live_permission_created"])
            for path in item["repaired_ledger_paths"]:
                self.assertIn("eid_repair", path)

    def test_blocks_false_live_and_current_write_permission(self):
        report = self.build_report()
        report["live_order_allowed"] = True
        report["event_id_scope_repaired_current_evidence_guard_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash(report)
        )

        live_result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
            report
        )
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        count_report = self.build_report()
        count_report["current_evidence_write_allowed_count"] = 1
        count_report["event_id_scope_repaired_current_evidence_guard_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash(count_report)
        )
        count_result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
            count_report
        )
        self.assertEqual(count_result.status, "BLOCKED")
        self.assertEqual(count_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_aggregate_count(self):
        report = self.build_report()
        report["guard_review_ready_count"] = 2
        report["event_id_scope_repaired_current_evidence_guard_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
            report
        )

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_blocks_candidate_path_escape(self):
        report = self.build_report()
        report["items"][0]["candidate_rollup_artifact_path"] = (
            "system/runtime/upbit/krw_spot/live/unsafe/repaired_isolated_rollup.json"
        )
        report["event_id_scope_repaired_current_evidence_guard_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
            report
        )

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_writer_creates_guard_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(
                written.name,
                "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json",
            )
            loaded = load_json(written)
            self.assertEqual(
                validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
                    loaded
                ).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
