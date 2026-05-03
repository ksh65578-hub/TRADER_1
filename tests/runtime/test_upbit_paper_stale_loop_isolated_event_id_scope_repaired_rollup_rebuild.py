import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild import (
    ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_BLOCKER_CODE,
    build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report,
    event_id_repaired_candidate_rollup_hash,
    upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_hash,
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report,
    write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report,
)


ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_REPORT_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rooted(root: Path, relative_path: str) -> Path:
    return root.joinpath(*[part for part in relative_path.replace("\\", "/").split("/") if part])


def materialize_repaired_ledgers(tmp_root: Path, executor_report: dict) -> None:
    for item in executor_report["items"]:
        for cycle in item["cycles"]:
            relative_path = cycle["repaired_ledger_path"]
            source = rooted(ROOT, relative_path)
            target = rooted(tmp_root, relative_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())


class UpbitPaperStaleLoopIsolatedEventIdScopeRepairedRollupRebuildTest(unittest.TestCase):
    def build_report(self, *, root: Path = ROOT, enabled: bool = False) -> dict:
        return build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
            root=root,
            event_id_scope_repair_executor_report=load_json(EXECUTOR_REPORT_PATH),
            event_id_scope_repaired_rollup_rebuild_id="test-event-id-repaired-rollup-rebuild",
            candidate_rollup_write_enabled=enabled,
        )

    def test_builds_disabled_candidate_only_repaired_rollup_rebuild_report(self):
        report = self.build_report(enabled=False)
        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["rebuild_status"], "WRITE_DISABLED_CURRENT_EVIDENCE_BLOCKED")
        self.assertEqual(report["primary_blocker_code"], ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD_BLOCKER_CODE)
        self.assertEqual(report["candidate_rollup_attempt_count"], 3)
        self.assertEqual(report["candidate_rollup_pass_count"], 3)
        self.assertEqual(report["candidate_rollup_blocked_count"], 0)
        self.assertEqual(report["candidate_rollup_artifact_ready_count"], 0)
        self.assertEqual(report["ledger_jsonl_count"], 6)
        self.assertEqual(report["ledger_event_count"], 36)
        self.assertEqual(report["filled_order_count"], 6)
        self.assertEqual(report["duplicate_event_count"], 0)
        self.assertEqual(report["event_id_updated_count"], 12)
        self.assertEqual(report["event_hash_recalculation_count"], 36)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(report["candidate_current_evidence_usable"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_enabled_rebuild_writes_all_repaired_candidate_rollups(self):
        executor_report = load_json(EXECUTOR_REPORT_PATH)
        with TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            materialize_repaired_ledgers(tmp_root, executor_report)

            report = build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
                root=tmp_root,
                event_id_scope_repair_executor_report=executor_report,
                event_id_scope_repaired_rollup_rebuild_id="test-event-id-repaired-rollup-rebuild",
                candidate_rollup_write_enabled=True,
            )
            result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(report)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(report["rebuild_status"], "REPAIRED_CANDIDATE_ROLLUPS_READY_CURRENT_EVIDENCE_BLOCKED")
            self.assertEqual(report["candidate_rollup_pass_count"], 3)
            self.assertEqual(report["candidate_rollup_blocked_count"], 0)
            self.assertEqual(report["candidate_rollup_written_count"], 3)
            self.assertEqual(report["candidate_rollup_reused_existing_count"], 0)
            self.assertEqual(report["candidate_rollup_artifact_ready_count"], 3)
            self.assertEqual(report["duplicate_event_count"], 0)
            self.assertEqual(report["current_evidence_write_allowed_count"], 0)

            for item in report["items"]:
                artifact_path = rooted(tmp_root, item["candidate_rollup_artifact_path"])
                self.assertTrue(artifact_path.exists())
                self.assertIn("eid_repair/rollup", item["candidate_rollup_artifact_path"])
                self.assertFalse(item["candidate_current_evidence_usable"])
                self.assertFalse(item["live_permission_created"])

    def test_enabled_rebuild_reuses_existing_matching_candidate_rollups(self):
        executor_report = load_json(EXECUTOR_REPORT_PATH)
        with TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            materialize_repaired_ledgers(tmp_root, executor_report)
            build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
                root=tmp_root,
                event_id_scope_repair_executor_report=executor_report,
                event_id_scope_repaired_rollup_rebuild_id="test-event-id-repaired-rollup-rebuild",
                candidate_rollup_write_enabled=True,
            )
            for artifact_path in (
                rooted(tmp_root, item["candidate_rollup_artifact_path"])
                for item in build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
                    root=tmp_root,
                    event_id_scope_repair_executor_report=executor_report,
                    event_id_scope_repaired_rollup_rebuild_id="test-event-id-repaired-rollup-rebuild",
                    candidate_rollup_write_enabled=False,
                )["items"]
            ):
                candidate_rollup = load_json(artifact_path)
                candidate_rollup["generated_at_utc"] = "2000-01-01T00:00:00Z"
                candidate_rollup["candidate_rollup_hash"] = event_id_repaired_candidate_rollup_hash(candidate_rollup)
                artifact_path.write_text(json.dumps(candidate_rollup, indent=2, sort_keys=True), encoding="utf-8")

            report = build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
                root=tmp_root,
                event_id_scope_repair_executor_report=executor_report,
                event_id_scope_repaired_rollup_rebuild_id="test-event-id-repaired-rollup-rebuild",
                candidate_rollup_write_enabled=True,
            )

            self.assertEqual(
                validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(report).status,
                "PASS",
            )
            self.assertEqual(report["candidate_rollup_written_count"], 0)
            self.assertEqual(report["candidate_rollup_reused_existing_count"], 3)
            self.assertEqual(report["candidate_rollup_artifact_ready_count"], 3)

    def test_blocks_false_live_permission(self):
        report = self.build_report(enabled=False)
        report["live_order_allowed"] = True
        report["event_id_scope_repaired_rollup_rebuild_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_evidence_write_count(self):
        report = self.build_report(enabled=False)
        report["current_evidence_write_allowed_count"] = 1
        report["event_id_scope_repaired_rollup_rebuild_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_aggregate_count(self):
        report = self.build_report(enabled=False)
        report["duplicate_event_count"] = 1
        report["event_id_scope_repaired_rollup_rebuild_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_blocks_repaired_path_escape(self):
        report = self.build_report(enabled=False)
        report["items"][0]["cycles"][0]["repaired_ledger_path"] = (
            "system/runtime/upbit/krw_spot/live/escaped.paper_ledger_events.jsonl"
        )
        report["event_id_scope_repaired_rollup_rebuild_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_writer_creates_rebuild_report_in_paper_runtime(self):
        report = self.build_report(enabled=False)
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(
                written.name,
                "upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report.json",
            )
            self.assertEqual(
                validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report(
                    load_json(written)
                ).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
