import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck import (
    ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_BLOCKER_CODE,
    build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report,
    upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_hash,
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report,
    write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report,
)


ROOT = Path(__file__).resolve().parents[2]
REPAIRED_ROLLUP_REBUILD_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperStaleLoopIsolatedEventIdScopeRepairedDuplicateRecheckTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(
            root=ROOT,
            event_id_scope_repaired_rollup_rebuild_report=load_json(REPAIRED_ROLLUP_REBUILD_PATH),
            event_id_scope_repaired_duplicate_recheck_id="test-event-id-repaired-duplicate-recheck",
        )

    def test_rechecks_repaired_candidate_rollups_without_current_evidence_use(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["recheck_status"], "REPAIRED_DUPLICATE_RECHECK_PASS_CURRENT_EVIDENCE_BLOCKED")
        self.assertEqual(report["primary_blocker_code"], ISOLATED_EVENT_ID_SCOPE_REPAIRED_DUPLICATE_RECHECK_BLOCKER_CODE)
        self.assertEqual(report["candidate_count"], 3)
        self.assertEqual(report["clean_candidate_count"], 3)
        self.assertEqual(report["affected_candidate_count"], 0)
        self.assertEqual(report["blocked_candidate_count"], 0)
        self.assertEqual(report["candidate_rollup_artifact_checked_count"], 3)
        self.assertEqual(report["candidate_rollup_artifact_missing_count"], 0)
        self.assertEqual(report["candidate_rollup_hash_mismatch_count"], 0)
        self.assertEqual(report["ledger_jsonl_count"], 6)
        self.assertEqual(report["ledger_event_count"], 36)
        self.assertEqual(report["filled_order_count"], 6)
        self.assertEqual(report["duplicate_group_count"], 0)
        self.assertEqual(report["duplicate_event_id_duplicate_count"], 0)
        self.assertEqual(report["duplicate_dedup_key_duplicate_count"], 0)
        self.assertEqual(report["duplicate_filled_order_duplicate_count"], 0)
        self.assertEqual(report["duplicate_total_count"], 0)
        self.assertEqual(report["duplicate_occurrence_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(report["candidate_current_evidence_usable"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_repaired_candidate_items_are_candidate_only_and_path_scoped(self):
        report = self.build_report()

        for item in report["items"]:
            self.assertEqual(item["candidate_recheck_status"], "PASS_CURRENT_EVIDENCE_BLOCKED")
            self.assertTrue(item["candidate_rollup_artifact_path_allowed"])
            self.assertTrue(item["candidate_rollup_hash_match"])
            self.assertEqual(item["duplicate_group_count"], 0)
            self.assertFalse(item["candidate_current_evidence_usable"])
            self.assertFalse(item["current_evidence_write_allowed"])
            self.assertFalse(item["live_permission_created"])
            for cycle in item["cycles"]:
                self.assertIn("eid_repair", cycle["repaired_ledger_path"])
                self.assertTrue(cycle["repaired_ledger_path_allowed"])
                self.assertEqual(cycle["repaired_ledger_load_status"], "PASS")
                self.assertFalse(cycle["current_evidence_write_allowed"])
                self.assertFalse(cycle["live_permission_created"])

    def test_blocks_false_live_permission(self):
        report = self.build_report()
        report["live_order_allowed"] = True
        report["event_id_scope_repaired_duplicate_recheck_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_evidence_write_count(self):
        report = self.build_report()
        report["current_evidence_write_allowed_count"] = 1
        report["event_id_scope_repaired_duplicate_recheck_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_duplicate_aggregate(self):
        report = self.build_report()
        report["duplicate_group_count"] = 1
        report["event_id_scope_repaired_duplicate_recheck_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_blocks_path_escape_mutation(self):
        report = self.build_report()
        report["items"][0]["cycles"][0]["repaired_ledger_path"] = (
            "system/runtime/upbit/krw_spot/live/escaped.paper_ledger_events.jsonl"
        )
        report["event_id_scope_repaired_duplicate_recheck_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_writer_creates_recheck_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(
                written.name,
                "upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report.json",
            )
            loaded = load_json(written)
            self.assertEqual(
                validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report(
                    loaded
                ).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
