import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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
    write_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import (
    build_upbit_paper_stale_loop_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import (
    build_upbit_paper_stale_loop_regeneration_plan,
)
from trader1.runtime.paper.upbit_paper_stale_loop_safe_regeneration_executor import (
    build_upbit_paper_stale_loop_safe_regeneration_executor_report,
)


class UpbitPaperStaleLoopPostRegenerationReconciliationTest(unittest.TestCase):
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

    def _executor_with_legacy(self, *, missing_recovery_and_ledger: bool = False) -> tuple[Path, dict]:
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
        self.assertEqual(executor["executor_status"], "PASS")
        return root, executor

    def test_post_reconciliation_accepts_pass_replacement_and_excludes_source(self):
        root, executor = self._executor_with_legacy()

        report = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
            root=root,
            executor_report=executor,
        )
        result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["post_reconciliation_status"], "PASS")
        self.assertEqual(report["planned_regeneration_item_count"], 1)
        self.assertEqual(report["source_retained_count"], 1)
        self.assertEqual(report["replacement_found_count"], 1)
        self.assertEqual(report["regenerated_current_accepted_count"], 1)
        self.assertEqual(report["current_evidence_usable_count"], 1)
        self.assertEqual(report["excluded_from_current_evidence_count"], 0)
        self.assertFalse(report["actual_long_run_evidence_created"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertTrue(report["items"][0]["source_excluded_from_current_evidence"])

        written_path = write_upbit_paper_stale_loop_post_regeneration_reconciliation_report(root=root, report=report)
        written = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(written).status, "PASS")

    def test_post_reconciliation_blocks_schema_repaired_missing_recovery_and_ledger(self):
        root, executor = self._executor_with_legacy(missing_recovery_and_ledger=True)

        report = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
            root=root,
            executor_report=executor,
        )
        result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["post_reconciliation_status"], "BLOCKED")
        self.assertIn("STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED", report["blocker_codes"])
        self.assertEqual(report["regenerated_current_accepted_count"], 0)
        self.assertEqual(report["regenerated_current_blocked_reconciliation_count"], 1)
        self.assertEqual(report["current_evidence_usable_count"], 0)
        self.assertEqual(report["excluded_from_current_evidence_count"], 1)
        self.assertEqual(
            report["items"][0]["recommended_action"],
            "RECONCILE_LEDGER_AND_RECOVERY_BEFORE_EVIDENCE_USE",
        )

    def test_post_reconciliation_blocks_source_hash_mutation_after_executor(self):
        root, executor = self._executor_with_legacy()
        source_path = root.joinpath(*executor["items"][0]["source_path"].split("/"))
        source = json.loads(source_path.read_text(encoding="utf-8"))
        source["loop_id"] = "legacy-loop-mutated"
        source["loop_hash"] = upbit_paper_persistent_loop_hash(source)
        source_path.write_text(json.dumps(source, indent=2), encoding="utf-8")

        report = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
            root=root,
            executor_report=executor,
        )
        result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["post_reconciliation_status"], "BLOCKED")
        self.assertIn("STALE_LOOP_SOURCE_HASH_MISMATCH", report["blocker_codes"])
        self.assertEqual(report["source_hash_mismatch_count"], 1)
        self.assertFalse(report["items"][0]["evidence_usable_current"])

    def test_post_reconciliation_blocks_unpaired_regenerated_artifact(self):
        root, executor = self._executor_with_legacy()
        replacement_path = root.joinpath(*executor["items"][0]["planned_replacement_path"].split("/"))
        unpaired_path = replacement_path.with_name("unpaired-regenerated-current-schema.persistent_loop_report.json")
        unpaired_path.write_text(replacement_path.read_text(encoding="utf-8"), encoding="utf-8")

        report = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
            root=root,
            executor_report=executor,
        )

        self.assertEqual(validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(report).status, "PASS")
        self.assertEqual(report["post_reconciliation_status"], "BLOCKED")
        self.assertEqual(report["unpaired_regenerated_artifact_count"], 1)
        self.assertIn("UNPAIRED_REGENERATED_ARTIFACT", report["blocker_codes"])

    def test_post_reconciliation_validator_blocks_live_mutation_and_false_usable(self):
        root, executor = self._executor_with_legacy(missing_recovery_and_ledger=True)
        report = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
            root=root,
            executor_report=executor,
        )
        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["post_reconciliation_hash"] = stale_loop_post_regeneration_reconciliation_hash(live_mutation)

        live_result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(live_mutation)

        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        false_usable = json.loads(json.dumps(report))
        false_usable["items"][0]["evidence_usable_current"] = True
        false_usable["current_evidence_usable_count"] = 1
        false_usable["excluded_from_current_evidence_count"] = 0
        false_usable["post_reconciliation_hash"] = stale_loop_post_regeneration_reconciliation_hash(false_usable)

        usable_result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(false_usable)

        self.assertEqual(usable_result.status, "BLOCKED")
        self.assertEqual(usable_result.blocker_code, "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED")


if __name__ == "__main__":
    unittest.main()
