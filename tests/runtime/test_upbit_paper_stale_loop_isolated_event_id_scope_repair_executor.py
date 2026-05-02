import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.ledger.execution_ledger import validate_ledger_chain
from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repair_executor import (
    ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED_CODE,
    build_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report,
    upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_hash,
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report,
    write_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report,
)


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_isolated_event_id_scope_repair_plan_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rooted(root: Path, relative_path: str) -> Path:
    return root.joinpath(*[part for part in relative_path.replace("\\", "/").split("/") if part])


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def materialize_source_ledgers(tmp_root: Path, plan: dict) -> None:
    copied: set[str] = set()
    for item in plan["items"]:
        for group in item["event_id_groups"]:
            for update in group["planned_updates"]:
                relative_path = update["ledger_path"]
                if relative_path in copied:
                    continue
                source = rooted(ROOT, relative_path)
                target = rooted(tmp_root, relative_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
                copied.add(relative_path)


class UpbitPaperStaleLoopIsolatedEventIdScopeRepairExecutorTest(unittest.TestCase):
    def build_report(self, *, root: Path = ROOT, enabled: bool = False) -> dict:
        return build_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(
            root=root,
            event_id_scope_repair_plan_report=load_json(PLAN_PATH),
            event_id_scope_repair_executor_id="test-isolated-event-id-scope-repair-executor",
            candidate_repair_write_enabled=enabled,
        )

    def test_builds_disabled_candidate_only_executor_report(self):
        report = self.build_report(enabled=False)
        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["executor_status"], "WRITE_DISABLED_CURRENT_EVIDENCE_BLOCKED")
        self.assertEqual(
            report["primary_blocker_code"],
            ISOLATED_EVENT_ID_SCOPE_REPAIR_EXECUTOR_CURRENT_EVIDENCE_BLOCKED_CODE,
        )
        self.assertEqual(report["candidate_count"], 4)
        self.assertEqual(report["repair_executor_candidate_count"], 3)
        self.assertEqual(report["candidate_repair_cycle_count"], 6)
        self.assertEqual(report["candidate_repair_ready_count"], 0)
        self.assertEqual(report["candidate_repair_blocked_count"], 6)
        self.assertEqual(report["candidate_repair_written_count"], 0)
        self.assertEqual(report["event_id_updated_count"], 12)
        self.assertEqual(report["event_hash_recalculation_count"], 36)
        self.assertEqual(report["post_repair_duplicate_event_id_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(report["actual_candidate_repair_performed"])
        self.assertFalse(report["candidate_repair_is_current_evidence"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_enabled_executor_writes_repaired_candidate_ledgers(self):
        plan = load_json(PLAN_PATH)
        with TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            materialize_source_ledgers(tmp_root, plan)

            report = build_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(
                root=tmp_root,
                event_id_scope_repair_plan_report=plan,
                event_id_scope_repair_executor_id="test-isolated-event-id-scope-repair-executor",
                candidate_repair_write_enabled=True,
            )
            result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(report)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(report["executor_status"], "CANDIDATE_REPAIR_READY_CURRENT_EVIDENCE_BLOCKED")
            self.assertEqual(report["candidate_repair_cycle_count"], 6)
            self.assertEqual(report["candidate_repair_ready_count"], 6)
            self.assertEqual(report["candidate_repair_written_count"], 6)
            self.assertEqual(report["candidate_repair_artifact_ready_count"], 6)
            self.assertEqual(report["event_id_updated_count"], 12)
            self.assertEqual(report["event_hash_recalculation_count"], 36)
            self.assertEqual(report["post_repair_duplicate_event_id_count"], 0)
            self.assertTrue(report["actual_candidate_repair_performed"])
            self.assertFalse(report["current_evidence_write_allowed"])

            all_event_ids: list[str] = []
            for item in report["items"]:
                for cycle in item["cycles"]:
                    repaired_path = rooted(tmp_root, cycle["repaired_ledger_path"])
                    self.assertTrue(repaired_path.exists())
                    self.assertIn("eid_repair", cycle["repaired_ledger_path"])
                    self.assertTrue(cycle["repaired_ledger_path_allowed"])
                    self.assertTrue(cycle["candidate_repair_artifact_ready"])
                    self.assertFalse(cycle["candidate_repair_is_current_evidence"])
                    records = read_jsonl(repaired_path)
                    self.assertEqual(validate_ledger_chain(records).status, "PASS")
                    all_event_ids.extend(record["event_id"] for record in records)

            self.assertEqual(len(all_event_ids), 36)
            self.assertEqual(len(set(all_event_ids)), 36)

    def test_enabled_executor_reuses_existing_matching_repairs(self):
        plan = load_json(PLAN_PATH)
        with TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            materialize_source_ledgers(tmp_root, plan)
            build_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(
                root=tmp_root,
                event_id_scope_repair_plan_report=plan,
                event_id_scope_repair_executor_id="test-isolated-event-id-scope-repair-executor",
                candidate_repair_write_enabled=True,
            )

            report = build_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(
                root=tmp_root,
                event_id_scope_repair_plan_report=plan,
                event_id_scope_repair_executor_id="test-isolated-event-id-scope-repair-executor",
                candidate_repair_write_enabled=True,
            )

            self.assertEqual(
                validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(report).status,
                "PASS",
            )
            self.assertEqual(report["candidate_repair_written_count"], 0)
            self.assertEqual(report["candidate_repair_reused_existing_count"], 6)
            self.assertEqual(report["candidate_repair_ready_count"], 6)

    def test_blocks_false_live_permission(self):
        report = self.build_report(enabled=False)
        report["live_order_allowed"] = True
        report["event_id_scope_repair_executor_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_evidence_write_count(self):
        report = self.build_report(enabled=False)
        report["current_evidence_write_allowed_count"] = 1
        report["event_id_scope_repair_executor_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_update_count(self):
        report = self.build_report(enabled=False)
        report["event_id_updated_count"] = 11
        report["event_id_scope_repair_executor_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_blocks_repaired_path_escape_mutation(self):
        report = self.build_report(enabled=False)
        report["items"][0]["cycles"][0]["repaired_ledger_path"] = (
            "system/runtime/upbit/krw_spot/live/escaped.paper_ledger_events.jsonl"
        )
        report["event_id_scope_repair_executor_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_writer_creates_executor_report_in_paper_runtime(self):
        report = self.build_report(enabled=False)
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report.json")
            self.assertEqual(
                validate_upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report(
                    load_json(written)
                ).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
