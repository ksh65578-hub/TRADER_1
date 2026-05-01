import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_blocked_repair_plan import (
    build_upbit_paper_blocked_repair_plan_report,
)
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import build_upbit_paper_ledger_rollup_repair_report
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
)
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import (
    REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE,
    build_upbit_paper_post_repair_reconciliation_report,
    upbit_paper_post_repair_reconciliation_hash,
    validate_upbit_paper_post_repair_reconciliation_report,
    write_upbit_paper_post_repair_reconciliation_report,
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


class UpbitPaperPostRepairReconciliationTest(unittest.TestCase):
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

    def _repair_report(self) -> tuple[Path, dict]:
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
        repair_report = build_upbit_paper_ledger_rollup_repair_report(root=root, repair_plan_report=repair_plan)
        self.assertEqual(repair_report["repair_candidate_count"], 1)
        return root, repair_report

    def test_blocks_repair_candidate_when_source_loop_expected_hash_mismatch_remains(self):
        root, repair_report = self._repair_report()

        report = build_upbit_paper_post_repair_reconciliation_report(ledger_rollup_repair_report=repair_report)
        result = validate_upbit_paper_post_repair_reconciliation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["post_repair_reconciliation_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "POST_REPAIR_RECONCILIATION_REQUIRED")
        self.assertEqual(report["repair_candidate_count"], 1)
        self.assertEqual(report["candidate_rollup_pass_count"], 1)
        self.assertEqual(report["source_loop_expected_rollup_hash_mismatch_count"], 1)
        self.assertEqual(report["hash_reconciliation_operator_action_required_count"], 1)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertIn(REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE, report["blocker_codes"])
        item = report["items"][0]
        self.assertEqual(item["candidate_classification"], "REPAIR_CANDIDATE_BLOCKED_HASH_MISMATCH")
        self.assertEqual(item["candidate_rollup_hash_self_check"], "PASS")
        self.assertEqual(item["candidate_rollup_recomputed_hash"], item["candidate_rollup_hash"])
        self.assertEqual(item["hash_reconciliation_status"], "SOURCE_EXPECTED_ROLLUP_ARTIFACT_MISSING")
        self.assertEqual(item["hash_reconciliation_blocker_code"], REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE)
        self.assertTrue(item["hash_reconciliation_requires_operator_action"])
        self.assertFalse(item["source_loop_expected_rollup_artifact_exists"])
        self.assertFalse(item["candidate_current_evidence_usable"])
        self.assertFalse(item["current_evidence_mutation_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

        written_path = write_upbit_paper_post_repair_reconciliation_report(root=root, report=report)
        self.assertTrue(written_path.exists())
        written = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_post_repair_reconciliation_report(written).status, "PASS")

    def test_rejects_current_evidence_mutation_and_count_tamper(self):
        _, repair_report = self._repair_report()
        report = build_upbit_paper_post_repair_reconciliation_report(ledger_rollup_repair_report=repair_report)

        mutation = json.loads(json.dumps(report))
        mutation["items"][0]["candidate_current_evidence_usable"] = True
        mutation["candidate_current_evidence_usable_count"] = 1
        mutation["candidate_current_evidence_blocked_count"] = 0
        mutation["post_repair_reconciliation_hash"] = upbit_paper_post_repair_reconciliation_hash(mutation)
        mutation_result = validate_upbit_paper_post_repair_reconciliation_report(mutation)
        self.assertEqual(mutation_result.status, "BLOCKED")
        self.assertEqual(mutation_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        count_tamper = json.loads(json.dumps(report))
        count_tamper["source_loop_expected_rollup_hash_mismatch_count"] = 0
        count_tamper["post_repair_reconciliation_hash"] = upbit_paper_post_repair_reconciliation_hash(count_tamper)
        count_result = validate_upbit_paper_post_repair_reconciliation_report(count_tamper)
        self.assertEqual(count_result.status, "FAIL")
        self.assertEqual(count_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

        hash_tamper = json.loads(json.dumps(report))
        hash_tamper["items"][0]["hash_reconciliation_status"] = "MATCH"
        hash_tamper["items"][0]["hash_reconciliation_blocker_code"] = None
        hash_tamper["items"][0]["hash_reconciliation_requires_operator_action"] = False
        hash_tamper["hash_reconciliation_status_counts"] = [{"hash_reconciliation_status": "MATCH", "count": 1}]
        hash_tamper["hash_reconciliation_operator_action_required_count"] = 0
        hash_tamper["post_repair_reconciliation_hash"] = upbit_paper_post_repair_reconciliation_hash(hash_tamper)
        hash_result = validate_upbit_paper_post_repair_reconciliation_report(hash_tamper)
        self.assertEqual(hash_result.status, "FAIL")
        self.assertEqual(hash_result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_rejects_missing_hash_mismatch_blocker(self):
        _, repair_report = self._repair_report()
        report = build_upbit_paper_post_repair_reconciliation_report(ledger_rollup_repair_report=repair_report)
        report["blocker_codes"] = [code for code in report["blocker_codes"] if code != REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE]
        report["post_repair_reconciliation_hash"] = upbit_paper_post_repair_reconciliation_hash(report)

        result = validate_upbit_paper_post_repair_reconciliation_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
