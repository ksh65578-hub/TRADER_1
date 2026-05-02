import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck import (
    EVENT_ID_SCOPE_REPAIR_REQUIRED_BLOCKER_CODE,
    ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    build_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report,
    upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_hash,
    validate_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report,
    write_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report,
)


ROOT = Path(__file__).resolve().parents[2]
ISOLATED_ROLLUP_REBUILD_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperStaleLoopIsolatedDuplicateRecheckTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(
            root=ROOT,
            isolated_ledger_rollup_rebuild_report=load_json(ISOLATED_ROLLUP_REBUILD_PATH),
            duplicate_reconciliation_recheck_id="test-isolated-duplicate-recheck",
        )

    def test_recheck_identifies_event_id_scope_duplicates_without_current_evidence(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["recheck_status"], "BLOCKED_REPAIR_PLAN_REQUIRED")
        self.assertEqual(report["primary_blocker_code"], ISOLATED_DUPLICATE_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertIn(EVENT_ID_SCOPE_REPAIR_REQUIRED_BLOCKER_CODE, report["blocker_codes"])
        self.assertEqual(report["candidate_count"], 4)
        self.assertEqual(report["affected_candidate_count"], 3)
        self.assertEqual(report["pass_candidate_count"], 1)
        self.assertEqual(report["blocked_candidate_count"], 3)
        self.assertEqual(report["ledger_jsonl_count"], 8)
        self.assertEqual(report["ledger_event_count"], 42)
        self.assertEqual(report["filled_order_count"], 7)
        self.assertEqual(report["duplicate_group_count"], 6)
        self.assertEqual(report["duplicate_event_id_group_count"], 6)
        self.assertEqual(report["duplicate_dedup_key_group_count"], 0)
        self.assertEqual(report["duplicate_semantic_group_count"], 0)
        self.assertEqual(report["duplicate_filled_order_group_count"], 0)
        self.assertEqual(report["duplicate_event_id_duplicate_count"], 6)
        self.assertEqual(report["duplicate_total_count"], 6)
        self.assertEqual(report["duplicate_occurrence_count"], 12)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(report["candidate_current_evidence_usable"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_duplicate_groups_keep_unique_dedup_keys_and_candidate_paths(self):
        report = self.build_report()
        affected = [item for item in report["items"] if item["duplicate_group_count"] > 0]

        self.assertEqual(len(affected), 3)
        for item in affected:
            self.assertEqual(item["candidate_recheck_status"], "BLOCKED_EVENT_ID_SCOPE_REPAIR_REQUIRED")
            self.assertEqual(item["duplicate_group_count"], 2)
            self.assertIn(EVENT_ID_SCOPE_REPAIR_REQUIRED_BLOCKER_CODE, item["blocker_codes"])
            for group in item["duplicate_groups"]:
                self.assertEqual(group["duplicate_key_type"], "EVENT_ID")
                self.assertEqual(group["occurrence_count"], 2)
                self.assertEqual(group["duplicate_count"], 1)
                self.assertTrue(group["dedup_keys_unique"])
                self.assertTrue(group["event_hashes_unique"])
                self.assertFalse(group["current_evidence_write_allowed"])
                self.assertFalse(group["live_permission_created"])
                for path in group["affected_ledger_paths"]:
                    self.assertIn("ledger_input_scope_repair_candidates", path)
                    self.assertTrue(path.endswith(".paper_ledger_events.jsonl"))

    def test_blocks_false_live_permission(self):
        report = self.build_report()
        report["live_order_allowed"] = True
        report["duplicate_reconciliation_recheck_hash"] = (
            upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_evidence_write_count(self):
        report = self.build_report()
        report["current_evidence_write_allowed_count"] = 1
        report["duplicate_reconciliation_recheck_hash"] = (
            upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_duplicate_aggregate(self):
        report = self.build_report()
        report["duplicate_group_count"] = 0
        report["duplicate_reconciliation_recheck_hash"] = (
            upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_blocks_path_escape_mutation(self):
        report = self.build_report()
        report["items"][0]["cycles"][0]["mirror_ledger_path"] = (
            "system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/unsafe.paper_ledger_events.jsonl"
        )
        report["duplicate_reconciliation_recheck_hash"] = (
            upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_writer_creates_recheck_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(
                written.name,
                "upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report.json",
            )
            loaded = load_json(written)
            self.assertEqual(
                validate_upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report(
                    loaded
                ).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
