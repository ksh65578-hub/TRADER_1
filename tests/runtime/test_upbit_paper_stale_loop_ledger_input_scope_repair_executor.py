import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_stale_loop_ledger_input_scope_repair_executor import (
    LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE,
    build_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report,
    upbit_paper_stale_loop_ledger_input_scope_repair_executor_hash,
    validate_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report,
    write_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report,
)


ROOT = Path(__file__).resolve().parents[2]
REPAIR_PLAN_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_ledger_input_scope_repair_plan_report.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rooted(root: Path, relative_path: str) -> Path:
    return root.joinpath(*[part for part in relative_path.replace("\\", "/").split("/") if part])


def materialize_source_ledgers(tmp_root: Path, plan: dict) -> None:
    for item in plan["items"]:
        for cycle in item["cycles"]:
            relative_path = cycle["source_selected_ledger_path"]
            source = rooted(ROOT, relative_path)
            target = rooted(tmp_root, relative_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())


class UpbitPaperStaleLoopLedgerInputScopeRepairExecutorTest(unittest.TestCase):
    def build_report(self, *, root: Path = ROOT, enabled: bool = False) -> dict:
        return build_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(
            root=root,
            ledger_input_scope_repair_plan_report=load_json(REPAIR_PLAN_PATH),
            ledger_input_scope_repair_executor_id="test-ledger-input-scope-repair-executor",
            candidate_mirror_write_enabled=enabled,
        )

    def test_builds_disabled_candidate_mirror_executor_report(self):
        report = self.build_report(enabled=False)
        result = validate_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["executor_status"], "WRITE_DISABLED_CURRENT_EVIDENCE_BLOCKED")
        self.assertEqual(report["primary_blocker_code"], LEDGER_INPUT_SCOPE_REPAIR_EXECUTOR_BLOCKER_CODE)
        self.assertEqual(report["repair_executor_candidate_count"], 4)
        self.assertEqual(report["candidate_mirror_cycle_attempt_count"], 8)
        self.assertEqual(report["candidate_mirror_ready_count"], 0)
        self.assertEqual(report["candidate_mirror_blocked_count"], 8)
        self.assertEqual(report["candidate_mirror_written_count"], 0)
        self.assertEqual(report["source_hash_match_count"], 8)
        self.assertEqual(report["source_ledger_event_count"], 42)
        self.assertEqual(report["current_canonical_ledger_write_allowed_count"], 0)
        self.assertEqual(report["target_rollup_write_allowed_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(report["candidate_mirror_is_current_evidence"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_enabled_executor_writes_only_isolated_candidate_mirror_ledgers(self):
        plan = load_json(REPAIR_PLAN_PATH)
        with TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            materialize_source_ledgers(tmp_root, plan)

            report = build_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(
                root=tmp_root,
                ledger_input_scope_repair_plan_report=plan,
                ledger_input_scope_repair_executor_id="test-ledger-input-scope-repair-executor",
                candidate_mirror_write_enabled=True,
            )
            result = validate_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(report)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(report["executor_status"], "CANDIDATE_MIRROR_READY_CURRENT_EVIDENCE_BLOCKED")
            self.assertEqual(report["candidate_mirror_cycle_attempt_count"], 8)
            self.assertEqual(report["candidate_mirror_ready_count"], 8)
            self.assertEqual(report["candidate_mirror_written_count"], 8)
            self.assertEqual(report["candidate_mirror_reused_existing_count"], 0)
            self.assertEqual(report["candidate_mirror_artifact_ready_count"], 8)
            self.assertEqual(report["current_evidence_write_allowed_count"], 0)
            for item in report["items"]:
                for cycle in item["cycles"]:
                    mirror_path = rooted(tmp_root, cycle["windows_safe_mirror_ledger_path"])
                    self.assertTrue(mirror_path.exists())
                    self.assertIn("ledger_input_scope_repair_candidates", cycle["windows_safe_mirror_ledger_path"])
                    self.assertTrue(cycle["windows_safe_mirror_ledger_path_allowed"])
                    self.assertTrue(cycle["candidate_mirror_hash_match"])
                    self.assertFalse(cycle["candidate_mirror_is_current_evidence"])

    def test_enabled_executor_reuses_existing_matching_mirrors(self):
        plan = load_json(REPAIR_PLAN_PATH)
        with TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            materialize_source_ledgers(tmp_root, plan)
            build_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(
                root=tmp_root,
                ledger_input_scope_repair_plan_report=plan,
                ledger_input_scope_repair_executor_id="test-ledger-input-scope-repair-executor",
                candidate_mirror_write_enabled=True,
            )

            report = build_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(
                root=tmp_root,
                ledger_input_scope_repair_plan_report=plan,
                ledger_input_scope_repair_executor_id="test-ledger-input-scope-repair-executor",
                candidate_mirror_write_enabled=True,
            )

            self.assertEqual(
                validate_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(report).status,
                "PASS",
            )
            self.assertEqual(report["candidate_mirror_written_count"], 0)
            self.assertEqual(report["candidate_mirror_reused_existing_count"], 8)
            self.assertEqual(report["candidate_mirror_ready_count"], 8)

    def test_blocks_false_live_permission(self):
        report = self.build_report(enabled=False)
        report["live_order_allowed"] = True
        report["ledger_input_scope_repair_executor_hash"] = (
            upbit_paper_stale_loop_ledger_input_scope_repair_executor_hash(report)
        )

        result = validate_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_blocks_false_current_evidence_write_count(self):
        report = self.build_report(enabled=False)
        report["current_evidence_write_allowed_count"] = 1
        report["ledger_input_scope_repair_executor_hash"] = (
            upbit_paper_stale_loop_ledger_input_scope_repair_executor_hash(report)
        )

        result = validate_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_fails_false_ready_count(self):
        report = self.build_report(enabled=False)
        report["source_hash_match_count"] = 0
        report["ledger_input_scope_repair_executor_hash"] = (
            upbit_paper_stale_loop_ledger_input_scope_repair_executor_hash(report)
        )

        result = validate_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_writer_creates_executor_report_in_paper_runtime(self):
        report = self.build_report(enabled=False)
        with TemporaryDirectory() as tmp:
            written = write_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(
                root=Path(tmp),
                report=report,
            )

            self.assertTrue(written.exists())
            self.assertEqual(written.name, "upbit_paper_stale_loop_ledger_input_scope_repair_executor_report.json")
            self.assertEqual(
                validate_upbit_paper_stale_loop_ledger_input_scope_repair_executor_report(
                    load_json(written)
                ).status,
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
