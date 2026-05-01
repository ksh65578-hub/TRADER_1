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
from trader1.runtime.paper.upbit_paper_post_rerun_current_evidence_promotion_guard import (
    build_upbit_paper_post_rerun_current_evidence_promotion_guard_report,
    upbit_paper_post_rerun_current_evidence_promotion_guard_hash,
    validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report,
    write_upbit_paper_post_rerun_current_evidence_promotion_guard_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report,
    validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report,
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


class UpbitPaperPostRerunCurrentEvidencePromotionGuardTest(unittest.TestCase):
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

    def _source_report_with_missing_current_ledger(self) -> tuple[Path, dict, Path]:
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
        source_report = build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(
            root=root,
            staging_executor_report=staging,
        )
        self.assertEqual(validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(source_report).status, "PASS")
        return root, source_report, current_ledger_path

    def test_builds_review_ready_guard_without_current_evidence_mutation(self):
        root, source_report, current_ledger_path = self._source_report_with_missing_current_ledger()

        report = build_upbit_paper_post_rerun_current_evidence_promotion_guard_report(
            root=root,
            post_rerun_reconciliation_report=source_report,
        )
        result = validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["promotion_guard_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertEqual(report["candidate_item_count"], 1)
        self.assertEqual(report["candidate_rollup_verified_count"], 1)
        self.assertEqual(report["promotion_review_ready_count"], 1)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["current_ledger_jsonl_write_allowed"])
        self.assertFalse(report["latest_runtime_pointer_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(current_ledger_path.exists())

        item = report["items"][0]
        self.assertIn("/rerun_candidates_post_rollup/", item["candidate_rollup_artifact_path"])
        self.assertIn("/ledger/cycles/", item["planned_current_ledger_jsonl_path"])
        self.assertEqual(item["promotion_review_status"], "REVIEW_READY_WRITE_BLOCKED")
        self.assertEqual(item["item_blocker_code"], POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertTrue(item["candidate_rollup_verified"])
        self.assertTrue(item["promotion_review_ready"])
        self.assertFalse(item["current_evidence_write_allowed"])
        self.assertFalse(item["candidate_current_evidence_usable"])

        written_path = write_upbit_paper_post_rerun_current_evidence_promotion_guard_report(root=root, report=report)
        self.assertTrue(written_path.exists())

    def test_blocks_live_mutation_current_write_count_and_source_hash_tamper(self):
        root, source_report, _current_ledger_path = self._source_report_with_missing_current_ledger()
        report = build_upbit_paper_post_rerun_current_evidence_promotion_guard_report(
            root=root,
            post_rerun_reconciliation_report=source_report,
        )

        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["promotion_guard_hash"] = upbit_paper_post_rerun_current_evidence_promotion_guard_hash(live_mutation)
        live_result = validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        write_count = json.loads(json.dumps(report))
        write_count["current_evidence_write_allowed_count"] = 1
        write_count["promotion_guard_hash"] = upbit_paper_post_rerun_current_evidence_promotion_guard_hash(write_count)
        count_result = validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report(write_count)
        self.assertEqual(count_result.status, "BLOCKED")
        self.assertEqual(count_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        source_hash_tamper = json.loads(json.dumps(report))
        source_hash_tamper["items"][0]["source_candidate_rollup_hash"] = "0" * 64
        source_hash_tamper["promotion_guard_hash"] = upbit_paper_post_rerun_current_evidence_promotion_guard_hash(source_hash_tamper)
        hash_result = validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report(source_hash_tamper)
        self.assertEqual(hash_result.status, "FAIL")
        self.assertEqual(hash_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_blocks_candidate_and_planned_current_path_escape(self):
        root, source_report, _current_ledger_path = self._source_report_with_missing_current_ledger()
        report = build_upbit_paper_post_rerun_current_evidence_promotion_guard_report(
            root=root,
            post_rerun_reconciliation_report=source_report,
        )

        candidate_escape = json.loads(json.dumps(report))
        candidate_escape["items"][0]["candidate_rollup_artifact_path"] = (
            "system/runtime/upbit/krw_spot/live/rerun_candidates_post_rollup/bad.json"
        )
        candidate_escape["promotion_guard_hash"] = upbit_paper_post_rerun_current_evidence_promotion_guard_hash(candidate_escape)
        candidate_result = validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report(candidate_escape)
        self.assertEqual(candidate_result.status, "BLOCKED")
        self.assertEqual(candidate_result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

        planned_escape = json.loads(json.dumps(report))
        planned_escape["items"][0]["planned_current_ledger_jsonl_path"] = (
            "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/not_current.jsonl"
        )
        planned_escape["promotion_guard_hash"] = upbit_paper_post_rerun_current_evidence_promotion_guard_hash(planned_escape)
        planned_result = validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report(planned_escape)
        self.assertEqual(planned_result.status, "BLOCKED")
        self.assertEqual(planned_result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
