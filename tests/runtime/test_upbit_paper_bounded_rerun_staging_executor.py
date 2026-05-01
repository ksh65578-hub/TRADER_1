import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_blocked_repair_plan import build_upbit_paper_blocked_repair_plan_report
from trader1.runtime.paper.upbit_paper_bounded_rerun_staging_executor import (
    build_upbit_paper_bounded_rerun_staging_executor_report,
    upbit_paper_bounded_rerun_staging_executor_hash,
    validate_upbit_paper_bounded_rerun_staging_executor_report,
    write_upbit_paper_bounded_rerun_staging_executor_report,
)
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import build_upbit_paper_ledger_rollup_repair_report
from trader1.runtime.paper.upbit_paper_missing_cycle_rerun_guard import build_upbit_paper_missing_cycle_rerun_guard_report
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
)
from trader1.runtime.paper.upbit_paper_runtime import upbit_paper_runtime_cycle_hash
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import build_upbit_paper_post_repair_reconciliation_report
from trader1.runtime.paper.upbit_paper_repair_operator_queue import (
    build_upbit_paper_repair_operator_queue_report,
    upbit_paper_repair_operator_queue_hash,
)
from trader1.runtime.paper.upbit_paper_stale_loop_execution_guard import build_upbit_paper_stale_loop_execution_guard
from trader1.runtime.paper.upbit_paper_stale_loop_post_regeneration_reconciliation import (
    build_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import build_upbit_paper_stale_loop_reconciliation_report
from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import build_upbit_paper_stale_loop_regeneration_plan
from trader1.runtime.paper.upbit_paper_stale_loop_safe_regeneration_executor import (
    build_upbit_paper_stale_loop_safe_regeneration_executor_report,
)
from trader1.runtime.portfolio.paper_portfolio import paper_portfolio_hash


class UpbitPaperBoundedRerunStagingExecutorTest(unittest.TestCase):
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

    def _guard_with_missing_cycle(self) -> tuple[Path, dict, Path]:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-staging-current", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-staging-legacy"
        for field in (
            "paper_ledger_rollup_status",
            "paper_ledger_rollup_hash",
            "paper_ledger_rollup_primary_blocker_code",
            "paper_ledger_rollup_path",
        ):
            legacy.pop(field, None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        self._loop_path(root, "validator-staging-legacy").write_text(json.dumps(legacy, indent=2), encoding="utf-8")
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
        return root, missing_guard, current_ledger_path

    def test_stages_ready_cycle_without_current_evidence_mutation(self):
        root, guard, current_ledger_path = self._guard_with_missing_cycle()

        report = build_upbit_paper_bounded_rerun_staging_executor_report(
            root=root,
            missing_cycle_rerun_guard_report=guard,
        )
        result = validate_upbit_paper_bounded_rerun_staging_executor_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["executor_status"], "BLOCKED")
        self.assertEqual(report["staging_status"], "PASS")
        self.assertEqual(report["ready_guard_item_count"], 1)
        self.assertEqual(report["staged_cycle_count"], 1)
        self.assertEqual(report["staged_artifact_count"], 3)
        self.assertEqual(report["staged_current_evidence_usable_count"], 0)
        self.assertFalse(report["actual_rerun_executed"])
        self.assertFalse(report["current_ledger_jsonl_write_allowed"])
        self.assertFalse(report["latest_runtime_pointer_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(current_ledger_path.exists())

        item = report["items"][0]
        self.assertEqual(item["staging_item_status"], "STAGED")
        self.assertEqual(item["runtime_cycle_validator_status"], "PASS")
        self.assertEqual(item["ledger_validator_status"], "PASS")
        self.assertTrue(item["source_runtime_cycle_hash_match"])
        self.assertFalse(item["staged_artifact_is_current_evidence"])
        for staged_path in item["staging_artifact_paths"]:
            self.assertIn("/rerun_candidates/", staged_path)
            self.assertTrue(root.joinpath(*staged_path.split("/")).exists())

        written_path = write_upbit_paper_bounded_rerun_staging_executor_report(root=root, report=report)
        self.assertTrue(written_path.exists())

    def test_reuses_existing_staging_artifacts_idempotently(self):
        root, guard, _current_ledger_path = self._guard_with_missing_cycle()
        first = build_upbit_paper_bounded_rerun_staging_executor_report(root=root, missing_cycle_rerun_guard_report=guard)

        second = build_upbit_paper_bounded_rerun_staging_executor_report(root=root, missing_cycle_rerun_guard_report=guard)

        self.assertEqual(validate_upbit_paper_bounded_rerun_staging_executor_report(first).status, "PASS")
        self.assertEqual(validate_upbit_paper_bounded_rerun_staging_executor_report(second).status, "PASS")
        self.assertEqual(second["staged_cycle_count"], 1)
        self.assertEqual(second["staging_written_artifact_count"], 0)
        self.assertEqual(second["staging_reused_existing_artifact_count"], 3)
        self.assertEqual(second["items"][0]["staging_item_status"], "REUSED_EXISTING")

    def test_normalizes_legacy_runtime_cycle_only_inside_staging_namespace(self):
        root, guard, _current_ledger_path = self._guard_with_missing_cycle()
        guard_item = guard["items"][0]
        cycle_id = guard_item["missing_cycle_ids"][0]
        replacement_path = root.joinpath(*guard_item["replacement_path"].split("/"))
        replacement = json.loads(replacement_path.read_text(encoding="utf-8"))
        source_cycle_path = next(
            root.joinpath(*path.split("/"))
            for result in replacement["cycle_results"]
            if result["cycle_id"] == cycle_id
            for path in result["artifact_paths"]
            if path.endswith(f"/{cycle_id}.runtime_cycle.json")
        )
        source_cycle = json.loads(source_cycle_path.read_text(encoding="utf-8"))
        for field in (
            "feature_snapshot_hash",
            "runtime_public_market_data_hash",
            "source_public_market_data_hash",
            "strategy_regime_cost_linkage",
        ):
            source_cycle.pop(field, None)
        for candidate in source_cycle["strategy_candidates"]:
            candidate.pop("cost_breakdown_bps", None)
            candidate.pop("cost_model_source", None)
        source_cycle["selected_candidate"] = dict(source_cycle["strategy_candidates"][0])
        source_cycle["paper_portfolio_snapshot"].pop("source_runtime_cycle_id", None)
        source_cycle["paper_portfolio_snapshot"].pop("source_paper_ledger_head_hash", None)
        source_cycle["paper_portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(source_cycle["paper_portfolio_snapshot"])
        source_cycle["cycle_hash"] = upbit_paper_runtime_cycle_hash(source_cycle)
        source_cycle_path.write_text(json.dumps(source_cycle, indent=2), encoding="utf-8")
        for result in replacement["cycle_results"]:
            if result["cycle_id"] == cycle_id:
                result["runtime_cycle_hash"] = source_cycle["cycle_hash"]
        replacement["loop_hash"] = upbit_paper_persistent_loop_hash(replacement)
        replacement_path.write_text(json.dumps(replacement, indent=2), encoding="utf-8")

        report = build_upbit_paper_bounded_rerun_staging_executor_report(root=root, missing_cycle_rerun_guard_report=guard)
        result = validate_upbit_paper_bounded_rerun_staging_executor_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["staging_status"], "PASS")
        item = report["items"][0]
        self.assertEqual(item["source_runtime_cycle_validator_status"], "FAIL")
        self.assertEqual(item["runtime_cycle_normalization_status"], "APPLIED_STAGING_ONLY")
        self.assertEqual(item["runtime_cycle_validator_status"], "PASS")
        self.assertEqual(item["staging_item_status"], "STAGED")
        staged_cycle_path = root.joinpath(*item["planned_runtime_cycle_path"].split("/"))
        staged_cycle = json.loads(staged_cycle_path.read_text(encoding="utf-8"))
        self.assertIn("strategy_regime_cost_linkage", staged_cycle)
        self.assertIn("cost_breakdown_bps", staged_cycle["selected_candidate"])
        self.assertNotIn("strategy_regime_cost_linkage", json.loads(source_cycle_path.read_text(encoding="utf-8")))

    def test_recovery_guard_blocked_items_are_not_staged(self):
        root, guard, _current_ledger_path = self._guard_with_missing_cycle()
        guard = json.loads(json.dumps(guard))
        recovery_item = json.loads(json.dumps(guard["items"][0]))
        recovery_item["source_queue_priority_order"] = 2
        recovery_item["requires_recovery_guard_rerun"] = True
        recovery_item["rerun_guard_status"] = "BLOCKED_RECOVERY_GUARD_REQUIRED"
        recovery_item["next_patch_staging_rerun_candidate_eligible"] = False
        recovery_item["rerun_guard_blocker_code"] = "RECOVERY_GUARD_RERUN_REQUIRED_BEFORE_CYCLE_RERUN"
        guard["items"].append(recovery_item)
        guard["guard_item_count"] = 2
        guard["rerun_ready_item_count"] = 1
        guard["recovery_guard_blocked_item_count"] = 1
        guard["source_runtime_cycle_rerun_required_count"] = 2
        guard["source_recovery_guard_rerun_required_count"] = 1
        guard["missing_cycle_ledger_jsonl_total_count"] = 2
        guard["planned_staging_artifact_total_count"] = 6
        from trader1.runtime.paper.upbit_paper_missing_cycle_rerun_guard import upbit_paper_missing_cycle_rerun_guard_hash

        guard["guard_hash"] = upbit_paper_missing_cycle_rerun_guard_hash(guard)

        report = build_upbit_paper_bounded_rerun_staging_executor_report(
            root=root,
            missing_cycle_rerun_guard_report=guard,
        )

        self.assertEqual(validate_upbit_paper_bounded_rerun_staging_executor_report(report).status, "PASS")
        self.assertEqual(report["ready_guard_item_count"], 1)
        self.assertEqual(report["recovery_guard_blocked_item_count"], 1)
        self.assertEqual(report["staged_cycle_count"], 1)
        self.assertEqual(report["skipped_cycle_count"], 1)
        self.assertIn("RECOVERY_GUARD_RERUN_REQUIRED_BEFORE_CYCLE_RERUN", report["blocker_codes"])

    def test_blocks_live_mutation_and_count_tamper(self):
        root, guard, _current_ledger_path = self._guard_with_missing_cycle()
        report = build_upbit_paper_bounded_rerun_staging_executor_report(
            root=root,
            missing_cycle_rerun_guard_report=guard,
        )
        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["executor_hash"] = upbit_paper_bounded_rerun_staging_executor_hash(live_mutation)

        live_result = validate_upbit_paper_bounded_rerun_staging_executor_report(live_mutation)

        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        count_tamper = json.loads(json.dumps(report))
        count_tamper["staged_cycle_count"] = 0
        count_tamper["executor_hash"] = upbit_paper_bounded_rerun_staging_executor_hash(count_tamper)

        count_result = validate_upbit_paper_bounded_rerun_staging_executor_report(count_tamper)

        self.assertEqual(count_result.status, "FAIL")
        self.assertEqual(count_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_blocks_staged_path_escape(self):
        root, guard, _current_ledger_path = self._guard_with_missing_cycle()
        report = build_upbit_paper_bounded_rerun_staging_executor_report(
            root=root,
            missing_cycle_rerun_guard_report=guard,
        )
        report["items"][0]["staging_artifact_paths"][0] = "system/runtime/upbit/krw_spot/live/bad.json"
        report["executor_hash"] = upbit_paper_bounded_rerun_staging_executor_hash(report)

        result = validate_upbit_paper_bounded_rerun_staging_executor_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
