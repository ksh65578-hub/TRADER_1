import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repair_plan import (
    EVENT_ID_SCOPE_REPAIR_PLAN_ONLY_EXECUTION_REQUIRED_BLOCKER_CODE,
    build_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report,
    upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_hash,
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report,
    write_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report,
)


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_BASE = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
)
DUPLICATE_RECHECK_PATH = (
    RUNTIME_BASE / "upbit_paper_stale_loop_isolated_duplicate_reconciliation_recheck_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperStaleLoopIsolatedEventIdScopeRepairPlanTest(unittest.TestCase):
    def build_report(self) -> dict:
        return build_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(
            root=ROOT,
            duplicate_reconciliation_recheck_report=load_json(DUPLICATE_RECHECK_PATH),
            event_id_scope_repair_plan_id="test-isolated-event-id-scope-repair-plan",
        )

    def test_builds_candidate_only_event_id_scope_plan(self):
        report = self.build_report()
        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["plan_status"], "READY_PLAN_ONLY")
        self.assertEqual(
            report["primary_blocker_code"],
            EVENT_ID_SCOPE_REPAIR_PLAN_ONLY_EXECUTION_REQUIRED_BLOCKER_CODE,
        )
        self.assertEqual(report["candidate_count"], 4)
        self.assertEqual(report["repair_plan_candidate_count"], 3)
        self.assertEqual(report["no_repair_candidate_count"], 1)
        self.assertEqual(report["planned_duplicate_group_count"], 6)
        self.assertEqual(report["planned_duplicate_count"], 6)
        self.assertEqual(report["planned_occurrence_count"], 12)
        self.assertEqual(report["planned_event_id_update_count"], 12)
        self.assertEqual(report["planned_hash_recalculation_count"], 12)
        self.assertEqual(report["candidate_mirror_write_allowed_count"], 0)
        self.assertEqual(report["current_canonical_ledger_write_allowed_count"], 0)
        self.assertEqual(report["target_rollup_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(report["automatic_execution_allowed"])
        self.assertFalse(report["candidate_mirror_write_allowed"])
        self.assertFalse(report["current_canonical_ledger_write_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_planned_event_ids_are_cycle_scoped_and_candidate_only(self):
        report = self.build_report()
        planned_event_ids: list[str] = []
        affected = [item for item in report["items"] if item["affected_by_event_id_duplicates"]]

        self.assertEqual(len(affected), 3)
        for item in affected:
            self.assertEqual(item["repair_plan_item_status"], "READY_PLAN_ONLY")
            for group in item["event_id_groups"]:
                self.assertEqual(group["duplicate_key_type"], "EVENT_ID")
                self.assertTrue(group["source_dedup_keys_unique"])
                self.assertTrue(group["planned_event_ids_unique"])
                self.assertEqual(group["planned_repair_scope"], "CANDIDATE_MIRROR_ONLY")
                for update in group["planned_updates"]:
                    self.assertIn(update["cycle_id"], update["planned_event_id"])
                    self.assertIn(update["original_event_id"], update["planned_event_id"])
                    self.assertNotEqual(update["original_event_id"], update["planned_event_id"])
                    self.assertTrue(update["ledger_path_allowed"])
                    self.assertTrue(update["dedup_key_preserved"])
                    self.assertTrue(update["event_hash_recalculation_required"])
                    self.assertTrue(update["candidate_mirror_only"])
                    self.assertFalse(update["candidate_mirror_write_allowed"])
                    self.assertFalse(update["current_evidence_write_allowed"])
                    planned_event_ids.append(update["planned_event_id"])

        self.assertEqual(len(planned_event_ids), 12)
        self.assertEqual(len(set(planned_event_ids)), 12)

    def test_blocks_false_live_permission(self):
        report = self.build_report()
        report["live_order_allowed"] = True
        report["event_id_scope_repair_plan_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_write_count(self):
        report = self.build_report()
        report["current_evidence_write_allowed_count"] = 1
        report["event_id_scope_repair_plan_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_planned_update_count(self):
        report = self.build_report()
        report["planned_event_id_update_count"] = 11
        report["event_id_scope_repair_plan_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_blocks_path_escape_mutation(self):
        report = self.build_report()
        report["items"][0]["event_id_groups"][0]["planned_updates"][0]["ledger_path"] = (
            "system/runtime/upbit/krw_spot/live/escaped.paper_ledger_events.jsonl"
        )
        report["event_id_scope_repair_plan_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_writer_creates_report_in_paper_runtime(self):
        report = self.build_report()
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report.json")
            self.assertEqual(
                validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report(load_json(written)).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
