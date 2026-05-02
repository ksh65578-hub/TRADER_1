import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_ledger_rollup_rebuild import (
    ISOLATED_LEDGER_ROLLUP_REBUILD_BLOCKER_CODE,
    build_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report,
    upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_hash,
    validate_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report,
    write_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report,
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
    / "upbit_paper_stale_loop_ledger_input_scope_repair_executor_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rooted(root: Path, relative_path: str) -> Path:
    return root.joinpath(*[part for part in relative_path.replace("\\", "/").split("/") if part])


def materialize_mirror_ledgers(tmp_root: Path, executor_report: dict) -> None:
    for item in executor_report["items"]:
        for cycle in item["cycles"]:
            relative_path = cycle["windows_safe_mirror_ledger_path"]
            source = rooted(ROOT, relative_path)
            target = rooted(tmp_root, relative_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())


class UpbitPaperStaleLoopIsolatedLedgerRollupRebuildTest(unittest.TestCase):
    def build_report(self, *, root: Path = ROOT, enabled: bool = False) -> dict:
        return build_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(
            root=root,
            ledger_input_scope_repair_executor_report=load_json(EXECUTOR_REPORT_PATH),
            isolated_ledger_rollup_rebuild_id="test-isolated-ledger-rollup-rebuild",
            candidate_rollup_write_enabled=enabled,
        )

    def test_builds_disabled_candidate_only_rollup_rebuild_report(self):
        report = self.build_report(enabled=False)
        result = validate_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["rebuild_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], ISOLATED_LEDGER_ROLLUP_REBUILD_BLOCKER_CODE)
        self.assertEqual(report["candidate_rollup_attempt_count"], 4)
        self.assertEqual(report["candidate_rollup_pass_count"], 1)
        self.assertEqual(report["candidate_rollup_blocked_count"], 3)
        self.assertEqual(report["candidate_rollup_artifact_ready_count"], 0)
        self.assertEqual(report["ledger_jsonl_count"], 8)
        self.assertEqual(report["ledger_event_count"], 42)
        self.assertEqual(report["filled_order_count"], 7)
        self.assertEqual(report["duplicate_event_count"], 6)
        self.assertEqual(report["duplicate_order_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(report["candidate_current_evidence_usable"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_enabled_rebuild_writes_only_passing_isolated_candidate_rollup(self):
        executor_report = load_json(EXECUTOR_REPORT_PATH)
        with TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            materialize_mirror_ledgers(tmp_root, executor_report)

            report = build_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(
                root=tmp_root,
                ledger_input_scope_repair_executor_report=executor_report,
                isolated_ledger_rollup_rebuild_id="test-isolated-ledger-rollup-rebuild",
                candidate_rollup_write_enabled=True,
            )
            result = validate_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(report)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(report["rebuild_status"], "BLOCKED")
            self.assertEqual(report["candidate_rollup_pass_count"], 1)
            self.assertEqual(report["candidate_rollup_blocked_count"], 3)
            self.assertEqual(report["candidate_rollup_written_count"], 1)
            self.assertEqual(report["candidate_rollup_reused_existing_count"], 0)
            self.assertEqual(report["candidate_rollup_artifact_ready_count"], 1)
            self.assertEqual(report["current_evidence_write_allowed_count"], 0)

            ready_items = [item for item in report["items"] if item["candidate_rollup_artifact_ready"]]
            blocked_items = [item for item in report["items"] if item["candidate_rollup_status"] == "BLOCKED"]
            self.assertEqual(len(ready_items), 1)
            self.assertEqual(len(blocked_items), 3)
            for item in ready_items:
                artifact_path = rooted(tmp_root, item["candidate_rollup_artifact_path"])
                self.assertTrue(artifact_path.exists())
                self.assertIn("ledger_input_scope_repair_candidates", item["candidate_rollup_artifact_path"])
                self.assertFalse(item["candidate_current_evidence_usable"])
            for item in blocked_items:
                self.assertEqual(item["candidate_rollup_write_status"], "BLOCKED_CANDIDATE_ROLLUP_STATUS")
                self.assertIn("RECONCILIATION_REQUIRED", item["blocker_codes"])

    def test_enabled_rebuild_reuses_existing_matching_candidate_rollup(self):
        executor_report = load_json(EXECUTOR_REPORT_PATH)
        with TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            materialize_mirror_ledgers(tmp_root, executor_report)
            build_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(
                root=tmp_root,
                ledger_input_scope_repair_executor_report=executor_report,
                isolated_ledger_rollup_rebuild_id="test-isolated-ledger-rollup-rebuild",
                candidate_rollup_write_enabled=True,
            )

            report = build_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(
                root=tmp_root,
                ledger_input_scope_repair_executor_report=executor_report,
                isolated_ledger_rollup_rebuild_id="test-isolated-ledger-rollup-rebuild",
                candidate_rollup_write_enabled=True,
            )

            self.assertEqual(
                validate_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(report).status,
                "PASS",
            )
            self.assertEqual(report["candidate_rollup_written_count"], 0)
            self.assertEqual(report["candidate_rollup_reused_existing_count"], 1)
            self.assertEqual(report["candidate_rollup_artifact_ready_count"], 1)

    def test_blocks_false_live_permission(self):
        report = self.build_report(enabled=False)
        report["live_order_allowed"] = True
        report["isolated_ledger_rollup_rebuild_hash"] = (
            upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_evidence_write_count(self):
        report = self.build_report(enabled=False)
        report["current_evidence_write_allowed_count"] = 1
        report["isolated_ledger_rollup_rebuild_hash"] = (
            upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_aggregate_count(self):
        report = self.build_report(enabled=False)
        report["candidate_rollup_pass_count"] = 4
        report["isolated_ledger_rollup_rebuild_hash"] = (
            upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_hash(report)
        )

        result = validate_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_writer_creates_rebuild_report_in_paper_runtime(self):
        report = self.build_report(enabled=False)
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report.json")
            self.assertEqual(
                validate_upbit_paper_stale_loop_isolated_ledger_rollup_rebuild_report(
                    load_json(written)
                ).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
