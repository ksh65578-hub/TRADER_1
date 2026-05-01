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
)
from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report,
    write_upbit_paper_post_rerun_ledger_rollup_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_reconciliation_queue import (
    build_upbit_paper_post_rerun_operator_reconciliation_queue_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_blocker_rollup import (
    POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_ITEM_STATUS,
    build_upbit_paper_post_rerun_reconciliation_blocker_rollup_report,
    upbit_paper_post_rerun_reconciliation_blocker_rollup_hash,
    validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report,
    write_upbit_paper_post_rerun_reconciliation_blocker_rollup_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_decision_audit import (
    build_upbit_paper_post_rerun_reconciliation_decision_audit_report,
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


class UpbitPaperPostRerunReconciliationBlockerRollupTest(unittest.TestCase):
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

    def _decision_audit_with_missing_current_ledger(self) -> tuple[Path, dict, Path]:
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
        repair_queue = build_upbit_paper_repair_operator_queue_report(
            blocked_repair_plan_report=blocked_plan,
            ledger_rollup_repair_report=ledger_repair,
            post_repair_reconciliation_report=post_repair,
        )
        missing_guard = build_upbit_paper_missing_cycle_rerun_guard_report(
            root=root,
            repair_operator_queue_report=repair_queue,
        )
        staging = build_upbit_paper_bounded_rerun_staging_executor_report(
            root=root,
            missing_cycle_rerun_guard_report=missing_guard,
        )
        source_report = build_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(
            root=root,
            staging_executor_report=staging,
        )
        write_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(root=root, report=source_report)
        promotion_guard = build_upbit_paper_post_rerun_current_evidence_promotion_guard_report(
            root=root,
            post_rerun_reconciliation_report=source_report,
        )
        operator_queue = build_upbit_paper_post_rerun_operator_reconciliation_queue_report(
            promotion_guard_report=promotion_guard,
        )
        decision_audit = build_upbit_paper_post_rerun_reconciliation_decision_audit_report(
            operator_queue_report=operator_queue,
        )
        return root, decision_audit, current_ledger_path

    def test_builds_blocker_rollup_without_current_evidence_mutation(self):
        root, decision_audit, current_ledger_path = self._decision_audit_with_missing_current_ledger()

        report = build_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(
            decision_audit_report=decision_audit,
        )
        result = validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["blocker_rollup_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertEqual(report["rollup_item_count"], 1)
        self.assertEqual(report["primary_blocker_item_count"], 1)
        self.assertGreaterEqual(report["unique_blocker_count"], 1)
        self.assertEqual(report["current_evidence_write_authorized_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["current_ledger_jsonl_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(current_ledger_path.exists())
        self.assertIn(POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE, report["blocker_codes"])

        item = report["items"][0]
        self.assertEqual(item["item_rollup_status"], POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_ITEM_STATUS)
        self.assertEqual(item["primary_item_blocker_code"], POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
        self.assertFalse(item["current_evidence_write_authorized"])
        self.assertFalse(item["current_evidence_write_allowed"])
        self.assertFalse(item["candidate_current_evidence_usable"])

        path = write_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(root=root, report=report)
        self.assertTrue(path.exists())

    def test_blocks_live_and_current_write_mutation(self):
        _root, decision_audit, _current_ledger_path = self._decision_audit_with_missing_current_ledger()
        report = build_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(
            decision_audit_report=decision_audit,
        )

        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["blocker_rollup_hash"] = upbit_paper_post_rerun_reconciliation_blocker_rollup_hash(live_mutation)
        live_result = validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        write_count = json.loads(json.dumps(report))
        write_count["current_evidence_write_allowed_count"] = 1
        write_count["blocker_rollup_hash"] = upbit_paper_post_rerun_reconciliation_blocker_rollup_hash(write_count)
        write_result = validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(write_count)
        self.assertEqual(write_result.status, "BLOCKED")
        self.assertEqual(write_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_rejects_count_tamper_and_path_escape(self):
        _root, decision_audit, _current_ledger_path = self._decision_audit_with_missing_current_ledger()
        report = build_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(
            decision_audit_report=decision_audit,
        )

        count_tamper = json.loads(json.dumps(report))
        count_tamper["primary_blocker_item_count"] = 0
        count_tamper["blocker_rollup_hash"] = upbit_paper_post_rerun_reconciliation_blocker_rollup_hash(count_tamper)
        count_result = validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(count_tamper)
        self.assertEqual(count_result.status, "FAIL")
        self.assertEqual(count_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

        path_escape = json.loads(json.dumps(report))
        path_escape["items"][0]["planned_current_ledger_jsonl_path"] = "system/runtime/upbit/krw_spot/live/bad.paper_ledger_events.jsonl"
        path_escape["blocker_rollup_hash"] = upbit_paper_post_rerun_reconciliation_blocker_rollup_hash(path_escape)
        path_result = validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(path_escape)
        self.assertEqual(path_result.status, "BLOCKED")
        self.assertEqual(path_result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
