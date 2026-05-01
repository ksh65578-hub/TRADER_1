import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_blocked_repair_plan import (
    build_upbit_paper_blocked_repair_plan_report,
)
from trader1.runtime.ledger.paper_ledger_rollup import paper_ledger_rollup_hash
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import (
    build_upbit_paper_ledger_rollup_repair_report,
    upbit_paper_ledger_rollup_repair_hash,
    validate_upbit_paper_ledger_rollup_repair_report,
    write_upbit_paper_ledger_rollup_repair_report,
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


class UpbitPaperLedgerRollupRepairTest(unittest.TestCase):
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

    def _blocked_repair_plan(self) -> tuple[Path, dict]:
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
        repair_plan = build_upbit_paper_blocked_repair_plan_report(
            root=root,
            post_reconciliation_report=post_reconciliation,
        )
        self.assertEqual(repair_plan["ledger_rollup_rebuild_ready_count"], 1)
        return root, repair_plan

    def test_rebuilds_scoped_candidate_rollup_without_current_evidence_mutation(self):
        root, repair_plan = self._blocked_repair_plan()

        report = build_upbit_paper_ledger_rollup_repair_report(root=root, repair_plan_report=repair_plan)
        result = validate_upbit_paper_ledger_rollup_repair_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["repair_report_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "POST_REPAIR_RECONCILIATION_REQUIRED")
        self.assertEqual(report["repair_candidate_count"], 1)
        self.assertEqual(report["candidate_rollup_pass_count"], 1)
        self.assertEqual(report["candidate_rollup_blocked_count"], 0)
        item = report["items"][0]
        self.assertEqual(item["candidate_rollup_validator_status"], "PASS")
        self.assertEqual(item["candidate_rollup"]["ledger_jsonl_count"], 1)
        self.assertGreater(item["candidate_rollup"]["ledger_event_count"], 0)
        self.assertEqual(item["candidate_rollup_hash_self_check"], "PASS")
        self.assertEqual(item["candidate_rollup_recomputed_hash"], item["candidate_rollup_hash"])
        self.assertEqual(item["hash_reconciliation_status"], "SOURCE_EXPECTED_ROLLUP_ARTIFACT_MISSING")
        self.assertEqual(item["hash_reconciliation_blocker_code"], "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED")
        self.assertTrue(item["hash_reconciliation_requires_operator_action"])
        self.assertFalse(item["source_loop_expected_rollup_artifact_exists"])
        self.assertEqual(report["hash_reconciliation_operator_action_required_count"], 1)
        self.assertFalse(item["candidate_artifact_is_current_evidence"])
        self.assertFalse(item["current_evidence_mutation_allowed"])
        self.assertTrue(item["post_repair_reconciliation_required"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

        written_path = write_upbit_paper_ledger_rollup_repair_report(root=root, report=report)
        candidate_path = root / item["candidate_rollup_artifact_path"]
        self.assertTrue(written_path.exists())
        self.assertTrue(candidate_path.exists())
        written = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_ledger_rollup_repair_report(written).status, "PASS")

    def test_repair_report_blocks_live_mutation_and_candidate_count_tamper(self):
        root, repair_plan = self._blocked_repair_plan()
        report = build_upbit_paper_ledger_rollup_repair_report(root=root, repair_plan_report=repair_plan)

        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["repair_report_hash"] = upbit_paper_ledger_rollup_repair_hash(live_mutation)
        live_result = validate_upbit_paper_ledger_rollup_repair_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        count_tamper = json.loads(json.dumps(report))
        count_tamper["candidate_rollup_pass_count"] = 0
        count_tamper["repair_report_hash"] = upbit_paper_ledger_rollup_repair_hash(count_tamper)
        count_result = validate_upbit_paper_ledger_rollup_repair_report(count_tamper)
        self.assertEqual(count_result.status, "FAIL")
        self.assertEqual(count_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

        hash_tamper = json.loads(json.dumps(report))
        hash_tamper["items"][0]["hash_reconciliation_status"] = "MATCH"
        hash_tamper["items"][0]["hash_reconciliation_blocker_code"] = None
        hash_tamper["items"][0]["hash_reconciliation_requires_operator_action"] = False
        hash_tamper["hash_reconciliation_status_counts"] = [{"hash_reconciliation_status": "MATCH", "count": 1}]
        hash_tamper["hash_reconciliation_operator_action_required_count"] = 0
        hash_tamper["repair_report_hash"] = upbit_paper_ledger_rollup_repair_hash(hash_tamper)
        hash_result = validate_upbit_paper_ledger_rollup_repair_report(hash_tamper)
        self.assertEqual(hash_result.status, "FAIL")
        self.assertEqual(hash_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_repair_report_fails_closed_on_candidate_rollup_live_mutation(self):
        root, repair_plan = self._blocked_repair_plan()
        report = build_upbit_paper_ledger_rollup_repair_report(root=root, repair_plan_report=repair_plan)
        report["items"][0]["candidate_rollup"]["live_order_allowed"] = True
        report["items"][0]["candidate_rollup"]["rollup_hash"] = paper_ledger_rollup_hash(report["items"][0]["candidate_rollup"])
        report["repair_report_hash"] = upbit_paper_ledger_rollup_repair_hash(report)

        result = validate_upbit_paper_ledger_rollup_repair_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
