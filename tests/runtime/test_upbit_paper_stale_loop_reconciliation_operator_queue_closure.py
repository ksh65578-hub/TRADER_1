import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    build_upbit_paper_ledger_idempotency_runtime_evidence_report,
    upbit_paper_ledger_idempotency_runtime_evidence_hash,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
)
from trader1.runtime.paper.upbit_paper_stale_loop_execution_guard import (
    build_upbit_paper_stale_loop_execution_guard,
)
from trader1.runtime.paper.upbit_paper_stale_loop_post_regeneration_reconciliation import (
    build_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
    stale_loop_post_regeneration_reconciliation_hash,
    validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import (
    build_upbit_paper_stale_loop_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation_operator_queue_closure import (
    build_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
    upbit_paper_stale_loop_reconciliation_operator_queue_closure_hash,
    validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
    write_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import (
    build_upbit_paper_stale_loop_regeneration_plan,
)
from trader1.runtime.paper.upbit_paper_stale_loop_safe_regeneration_executor import (
    build_upbit_paper_stale_loop_safe_regeneration_executor_report,
)


POST_REGENERATION_BLOCKER = "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED"
LEDGER_ONLY_REASONS = [
    "LEDGER_ROLLUP_BLOCKED",
    "LEDGER_ROLLUP_RECONCILIATION_REQUIRED",
    "LOOP_RECONCILIATION_REQUIRED",
    "LOOP_STATUS_BLOCKED",
]


class UpbitPaperStaleLoopReconciliationOperatorQueueClosureTest(unittest.TestCase):
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

    def _post_report(self, *, missing_recovery_and_ledger: bool = False) -> tuple[Path, dict, dict]:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="current-loop", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "legacy-loop"
        if missing_recovery_and_ledger:
            for field in (
                "recovery_guard_status",
                "recovery_guard_hash",
                "recovery_guard_primary_blocker_code",
                "runtime_recovery_guard_path",
                "paper_runtime_resume_allowed",
                "partial_write_recovery_required",
                "paper_ledger_rollup_status",
                "paper_ledger_rollup_hash",
                "paper_ledger_rollup_primary_blocker_code",
                "paper_ledger_rollup_path",
            ):
                legacy.pop(field, None)
        else:
            legacy.pop("paper_ledger_rollup_hash")
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        self._loop_path(root, "legacy-loop").write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        post = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(root=root, executor_report=executor)
        ledger = build_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root)
        return root, post, ledger

    def _ledger_only_blocked_post_report(self, report: dict) -> dict:
        blocked = json.loads(json.dumps(report))
        item = blocked["items"][0]
        item["classification"] = "REGENERATED_CURRENT_BLOCKED_RECONCILIATION_REQUIRED"
        item["evidence_usable_current"] = False
        item["replacement_validation_status"] = "BLOCKED"
        item["replacement_validation_blocker_code"] = "RECONCILIATION_REQUIRED"
        item["replacement_validation_message"] = "ledger rollup requires recheck"
        item["recommended_action"] = "RECONCILE_LEDGER_AND_RECOVERY_BEFORE_EVIDENCE_USE"
        item["item_blocker_code"] = POST_REGENERATION_BLOCKER
        item["blocked_repair_reason_codes"] = list(LEDGER_ONLY_REASONS)
        item["blocked_repair_reason_summary"] = (
            "Paper ledger rollup is blocked; keep this replacement out of current evidence until ledger reconciliation passes."
        )
        item["ledger_reconciliation_status"] = "BLOCKED"
        item["recovery_reconciliation_status"] = "PASS"
        item["cycle_reconciliation_status"] = "PASS"
        item["operator_repair_action"] = "Before evidence use, rebuild or reconcile the PAPER ledger rollup."
        blocked["regenerated_current_accepted_count"] = 0
        blocked["regenerated_current_blocked_reconciliation_count"] = 1
        blocked["current_evidence_usable_count"] = 0
        blocked["excluded_from_current_evidence_count"] = 1
        blocked["blocked_repair_reason_counts"] = [{"reason_code": code, "count": 1} for code in sorted(LEDGER_ONLY_REASONS)]
        blocked["post_reconciliation_status"] = "BLOCKED"
        blocked["primary_blocker_code"] = POST_REGENERATION_BLOCKER
        blocked["blocker_codes"] = [POST_REGENERATION_BLOCKER]
        blocked["operator_next_action"] = "Reconcile BLOCKED regenerated replacements before evidence use."
        blocked["post_reconciliation_hash"] = stale_loop_post_regeneration_reconciliation_hash(blocked)
        self.assertEqual(validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(blocked).status, "PASS")
        return blocked

    def test_closure_marks_ledger_only_blocked_replacement_recheck_ready_without_evidence_mutation(self):
        root, post, ledger = self._post_report()
        blocked = self._ledger_only_blocked_post_report(post)

        report = build_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(
            post_regeneration_reconciliation_report=blocked,
            ledger_idempotency_evidence_report=ledger,
        )
        result = validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["closure_status"], "BLOCKED")
        self.assertEqual(report["ledger_recheck_ready_count"], 1)
        self.assertEqual(report["recovery_guard_required_count"], 0)
        self.assertEqual(report["current_evidence_usable_after_closure_count"], 0)
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertEqual(report["items"][0]["closure_lane"], "LEDGER_RECHECK_READY")
        self.assertTrue(report["items"][0]["closure_recheck_ready"])
        self.assertFalse(report["items"][0]["current_evidence_usable_after_closure"])

        written_path = write_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(root=root, report=report)
        written = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(written).status, "PASS")

    def test_closure_keeps_recovery_blocked_replacement_out_of_recheck_ready_lane(self):
        _root, post, ledger = self._post_report(missing_recovery_and_ledger=True)

        report = build_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(
            post_regeneration_reconciliation_report=post,
            ledger_idempotency_evidence_report=ledger,
        )

        self.assertEqual(validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(report).status, "PASS")
        self.assertEqual(report["ledger_recheck_ready_count"], 0)
        self.assertEqual(report["recovery_guard_required_count"], 1)
        self.assertEqual(report["items"][0]["closure_lane"], "RECOVERY_GUARD_REQUIRED")
        self.assertFalse(report["items"][0]["closure_recheck_ready"])

    def test_closure_does_not_mark_ledger_recheck_ready_when_current_ledger_evidence_is_blocked(self):
        _root, post, ledger = self._post_report()
        blocked = self._ledger_only_blocked_post_report(post)
        ledger["runtime_evidence_status"] = "BLOCKED"
        ledger["idempotency_status"] = "BLOCKED"
        ledger["reconciliation_status"] = "BLOCKED"
        ledger["primary_blocker_code"] = "RECONCILIATION_REQUIRED"
        ledger["blockers"] = [{"code": "RECONCILIATION_REQUIRED", "severity": "HIGH", "message": "test blocker"}]
        ledger["evidence_hash"] = upbit_paper_ledger_idempotency_runtime_evidence_hash(ledger)

        report = build_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(
            post_regeneration_reconciliation_report=blocked,
            ledger_idempotency_evidence_report=ledger,
        )

        self.assertEqual(validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(report).status, "PASS")
        self.assertEqual(report["ledger_recheck_ready_count"], 0)
        self.assertEqual(report["operator_review_required_count"], 1)
        self.assertEqual(report["items"][0]["closure_lane"], "OPERATOR_REVIEW_REQUIRED")

    def test_closure_validator_blocks_live_permission_and_false_recheck_ready(self):
        _root, post, ledger = self._post_report(missing_recovery_and_ledger=True)
        report = build_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(
            post_regeneration_reconciliation_report=post,
            ledger_idempotency_evidence_report=ledger,
        )

        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["closure_hash"] = upbit_paper_stale_loop_reconciliation_operator_queue_closure_hash(live_mutation)
        live_result = validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        false_ready = json.loads(json.dumps(report))
        false_ready["items"][0]["closure_recheck_ready"] = True
        false_ready["closure_hash"] = upbit_paper_stale_loop_reconciliation_operator_queue_closure_hash(false_ready)
        ready_result = validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(false_ready)
        self.assertEqual(ready_result.status, "FAIL")
        self.assertEqual(ready_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
