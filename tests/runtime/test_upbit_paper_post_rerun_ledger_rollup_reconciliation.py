import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_blocked_repair_plan import build_upbit_paper_blocked_repair_plan_report
from trader1.runtime.paper.upbit_paper_bounded_rerun_staging_executor import (
    build_upbit_paper_bounded_rerun_staging_executor_report,
)
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import build_upbit_paper_ledger_rollup_repair_report
from trader1.runtime.paper.upbit_paper_missing_cycle_rerun_guard import build_upbit_paper_missing_cycle_rerun_guard_report
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
)
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import build_upbit_paper_post_repair_reconciliation_report
from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report,
    upbit_paper_post_rerun_ledger_rollup_reconciliation_hash,
    validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report,
    write_upbit_paper_post_rerun_ledger_rollup_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_repair_operator_queue import build_upbit_paper_repair_operator_queue_report
from trader1.runtime.paper.upbit_paper_stale_loop_execution_guard import build_upbit_paper_stale_loop_execution_guard
from trader1.runtime.paper.upbit_paper_stale_loop_post_regeneration_reconciliation import (
    build_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import build_upbit_paper_stale_loop_reconciliation_report
from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import build_upbit_paper_stale_loop_regeneration_plan
from trader1.runtime.paper.upbit_paper_stale_loop_safe_regeneration_executor import (
    build_upbit_paper_stale_loop_safe_regeneration_executor_report,
)


class UpbitPaperPostRerunLedgerRollupReconciliationTest(unittest.TestCase):
    def _loop_path(self, root: Path, loop_id: str) -> Path:
        return (
            root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / f"{loop_id}.persistent_loop_report.json"
        )

    def _staging_report_with_missing_cycle(self) -> tuple[Path, dict, Path]:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-post-rerun-current", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-post-rerun-legacy"
        for field in (
            "paper_ledger_rollup_status",
            "paper_ledger_rollup_hash",
            "paper_ledger_rollup_primary_blocker_code",
            "paper_ledger_rollup_path",
        ):
            legacy.pop(field, None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        self._loop_path(root, "validator-post-rerun-legacy").write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        stale = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        regeneration = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=stale)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=regeneration)
        executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        post_regeneration = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
            root=root,
            executor_report=executor,
        )
        item = post_regeneration["items"][0]
        replacement_path = root.joinpath(*item["replacement_path"].split("/"))
        replacement = json.loads(replacement_path.read_text(encoding="utf-8"))
        cycle_id = replacement["cycle_results"][0]["cycle_id"]
        current_ledger_path = (
            root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "ledger"
            / "cycles"
            / f"{cycle_id}.paper_ledger_events.jsonl"
        )
        current_ledger_path.unlink()
        blocked_plan = build_upbit_paper_blocked_repair_plan_report(
            root=root,
            post_reconciliation_report=post_regeneration,
        )
        ledger_repair = build_upbit_paper_ledger_rollup_repair_report(
            root=root,
            repair_plan_report=blocked_plan,
        )
        post_repair = build_upbit_paper_post_repair_reconciliation_report(
            ledger_rollup_repair_report=ledger_repair,
        )
        queue = build_upbit_paper_repair_operator_queue_report(
            blocked_repair_plan_report=blocked_plan,
            ledger_rollup_repair_report=ledger_repair,
            post_repair_reconciliation_report=post_repair,
        )
        missing_guard = build_upbit_paper_missing_cycle_rerun_guard_report(
            root=root,
            repair_operator_queue_report=queue,
        )
        staging = build_upbit_paper_bounded_rerun_staging_executor_report(
            root=root,
            missing_cycle_rerun_guard_report=missing_guard,
        )
        return root, staging, current_ledger_path

    def test_builds_candidate_rollup_without_current_evidence_mutation(self):
        root, staging, current_ledger_path = self._staging_report_with_missing_cycle()

        report = build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(
            root=root,
            staging_executor_report=staging,
        )
        result = validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["post_rerun_ledger_rollup_status"], "PASS")
        self.assertEqual(report["post_rerun_reconciliation_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertEqual(report["candidate_item_count"], 1)
        self.assertEqual(report["candidate_rollup_pass_count"], 1)
        self.assertEqual(report["candidate_rollup_artifact_ready_count"], 1)
        self.assertEqual(report["candidate_rollup_written_count"], 1)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertFalse(report["current_ledger_jsonl_write_allowed"])
        self.assertFalse(report["latest_runtime_pointer_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(current_ledger_path.exists())

        item = report["items"][0]
        self.assertIn("/rerun_candidates/", item["staged_ledger_jsonl_path"])
        self.assertIn("/rerun_candidates_post_rollup/", item["candidate_rollup_artifact_path"])
        self.assertTrue(root.joinpath(*item["candidate_rollup_artifact_path"].split("/")).exists())
        self.assertEqual(item["candidate_rollup_status"], "PASS")
        self.assertEqual(item["item_blocker_code"], POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertFalse(item["candidate_current_evidence_usable"])
        self.assertFalse(item["candidate_rollup"]["candidate_current_evidence_usable"])

        written_path = write_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(root=root, report=report)
        self.assertTrue(written_path.exists())

    def test_reuses_existing_candidate_rollups_idempotently(self):
        root, staging, _current_ledger_path = self._staging_report_with_missing_cycle()
        first = build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(root=root, staging_executor_report=staging)

        second = build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(root=root, staging_executor_report=staging)

        self.assertEqual(validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(first).status, "PASS")
        self.assertEqual(validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(second).status, "PASS")
        self.assertEqual(second["candidate_rollup_written_count"], 0)
        self.assertEqual(second["candidate_rollup_reused_existing_count"], 1)
        self.assertEqual(second["items"][0]["candidate_rollup_write_status"], "REUSED_EXISTING_MATCH")

    def test_blocks_live_mutation_and_count_tamper(self):
        root, staging, _current_ledger_path = self._staging_report_with_missing_cycle()
        report = build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(
            root=root,
            staging_executor_report=staging,
        )

        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["post_rerun_reconciliation_hash"] = upbit_paper_post_rerun_ledger_rollup_reconciliation_hash(live_mutation)
        live_result = validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        count_tamper = json.loads(json.dumps(report))
        count_tamper["candidate_rollup_pass_count"] = 0
        count_tamper["post_rerun_reconciliation_hash"] = upbit_paper_post_rerun_ledger_rollup_reconciliation_hash(count_tamper)
        count_result = validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(count_tamper)
        self.assertEqual(count_result.status, "FAIL")
        self.assertEqual(count_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_blocks_staged_path_escape(self):
        root, staging, _current_ledger_path = self._staging_report_with_missing_cycle()
        report = build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(
            root=root,
            staging_executor_report=staging,
        )
        report["items"][0]["staged_ledger_jsonl_path"] = "system/runtime/upbit/krw_spot/live/bad.jsonl"
        report["post_rerun_reconciliation_hash"] = upbit_paper_post_rerun_ledger_rollup_reconciliation_hash(report)

        result = validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
