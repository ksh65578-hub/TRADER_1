import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_blocked_repair_plan import (
    build_upbit_paper_blocked_repair_plan_report,
    upbit_paper_blocked_repair_plan_hash,
    validate_upbit_paper_blocked_repair_plan_report,
    write_upbit_paper_blocked_repair_plan_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
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


class UpbitPaperBlockedRepairPlanTest(unittest.TestCase):
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

    def _blocked_post_reconciliation(self) -> tuple[Path, dict]:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="current-loop", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "legacy-loop"
        for field in (
            "paper_ledger_rollup_status",
            "paper_ledger_rollup_hash",
            "paper_ledger_rollup_primary_blocker_code",
            "paper_ledger_rollup_path",
        ):
            legacy.pop(field, None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        self._loop_path(root, "legacy-loop").write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        post_reconciliation = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
            root=root,
            executor_report=executor,
        )
        self.assertEqual(post_reconciliation["post_reconciliation_status"], "BLOCKED")
        self.assertEqual(post_reconciliation["regenerated_current_blocked_reconciliation_count"], 1)
        return root, post_reconciliation

    def test_repair_plan_classifies_ledger_rebuild_ready_item_without_evidence_mutation(self):
        root, post_reconciliation = self._blocked_post_reconciliation()

        report = build_upbit_paper_blocked_repair_plan_report(
            root=root,
            post_reconciliation_report=post_reconciliation,
        )
        result = validate_upbit_paper_blocked_repair_plan_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["repair_plan_status"], "BLOCKED")
        self.assertEqual(report["repair_item_count"], 1)
        self.assertEqual(report["ledger_rollup_rebuild_ready_count"], 1)
        self.assertEqual(report["runtime_cycle_rerun_required_count"], 0)
        self.assertEqual(report["recovery_guard_rerun_required_count"], 0)
        self.assertEqual(report["missing_cycle_ledger_jsonl_total_count"], 0)
        self.assertEqual(report["missing_paper_ledger_rollup_artifact_count"], 1)
        item = report["items"][0]
        self.assertEqual(item["safe_repair_lane"], "LEDGER_ROLLUP_REBUILD_READY")
        self.assertTrue(item["can_rebuild_ledger_rollup_without_rerun"])
        self.assertFalse(item["current_evidence_mutation_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

        written_path = write_upbit_paper_blocked_repair_plan_report(root=root, report=report)
        written = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_blocked_repair_plan_report(written).status, "PASS")

    def test_repair_plan_detects_missing_cycle_ledger_requires_runtime_rerun(self):
        root, post_reconciliation = self._blocked_post_reconciliation()
        item = post_reconciliation["items"][0]
        replacement_path = root.joinpath(*item["replacement_path"].split("/"))
        replacement = json.loads(replacement_path.read_text(encoding="utf-8"))
        cycle_id = replacement["cycle_results"][0]["cycle_id"]
        ledger_path = (
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
        ledger_path.unlink()

        report = build_upbit_paper_blocked_repair_plan_report(
            root=root,
            post_reconciliation_report=post_reconciliation,
        )

        self.assertEqual(validate_upbit_paper_blocked_repair_plan_report(report).status, "PASS")
        self.assertEqual(report["ledger_rollup_rebuild_ready_count"], 0)
        self.assertEqual(report["runtime_cycle_rerun_required_count"], 1)
        self.assertEqual(report["missing_cycle_ledger_jsonl_total_count"], 1)
        self.assertEqual(report["items"][0]["safe_repair_lane"], "RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP")
        self.assertFalse(report["items"][0]["can_rebuild_ledger_rollup_without_rerun"])

    def test_repair_plan_blocks_live_mutation_and_count_tamper(self):
        root, post_reconciliation = self._blocked_post_reconciliation()
        report = build_upbit_paper_blocked_repair_plan_report(
            root=root,
            post_reconciliation_report=post_reconciliation,
        )
        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["repair_plan_hash"] = upbit_paper_blocked_repair_plan_hash(live_mutation)

        live_result = validate_upbit_paper_blocked_repair_plan_report(live_mutation)

        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        count_tamper = json.loads(json.dumps(report))
        count_tamper["ledger_rollup_rebuild_ready_count"] = 0
        count_tamper["repair_plan_hash"] = upbit_paper_blocked_repair_plan_hash(count_tamper)

        count_result = validate_upbit_paper_blocked_repair_plan_report(count_tamper)

        self.assertEqual(count_result.status, "FAIL")
        self.assertEqual(count_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
