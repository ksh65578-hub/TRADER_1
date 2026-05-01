import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import (
    build_upbit_paper_stale_loop_reconciliation_report,
    stale_loop_reconciliation_hash,
    validate_upbit_paper_stale_loop_reconciliation_report,
    write_upbit_paper_stale_loop_reconciliation_report,
)


class UpbitPaperStaleLoopReconciliationTest(unittest.TestCase):
    def _root_with_current_loop(self) -> tuple[Path, dict]:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="current-loop", requested_cycle_count=1)
        return root, current

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

    def test_reconciliation_accepts_current_loop_without_live_or_long_run_evidence(self):
        root, _ = self._root_with_current_loop()
        report = build_upbit_paper_stale_loop_reconciliation_report(root=root)

        result = validate_upbit_paper_stale_loop_reconciliation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["source_loop_report_count"], 1)
        self.assertEqual(report["current_accepted_count"], 1)
        self.assertEqual(report["current_evidence_usable_count"], 1)
        self.assertEqual(report["legacy_schema_drift_count"], 0)
        self.assertEqual(report["duplicate_runtime_cycle_hash_count"], 0)
        self.assertEqual(report["evidence_use_policy"], "CURRENT_SCHEMA_PASS_ONLY")
        self.assertFalse(report["actual_long_run_evidence_created"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

        written_path = write_upbit_paper_stale_loop_reconciliation_report(root=root, report=report)
        written = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_stale_loop_reconciliation_report(written).status, "PASS")

    def test_reconciliation_classifies_legacy_schema_drift_as_excluded(self):
        root, current = self._root_with_current_loop()
        legacy = dict(current)
        legacy["loop_id"] = "legacy-loop"
        legacy.pop("paper_ledger_rollup_hash")
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        self._loop_path(root, "legacy-loop").write_text(json.dumps(legacy, indent=2), encoding="utf-8")

        report = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        result = validate_upbit_paper_stale_loop_reconciliation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["reconciliation_status"], "BLOCKED")
        self.assertEqual(report["legacy_schema_drift_count"], 1)
        self.assertEqual(report["excluded_from_current_evidence_count"], 1)
        legacy_items = [item for item in report["items"] if item["classification"] == "LEGACY_SCHEMA_DRIFT"]
        self.assertEqual(len(legacy_items), 1)
        self.assertFalse(legacy_items[0]["evidence_usable_current"])
        self.assertEqual(
            legacy_items[0]["recommended_action"],
            "RETAIN_LEGACY_REFERENCE_EXCLUDE_FROM_CURRENT_EVIDENCE",
        )

    def test_reconciliation_blocks_unsafe_live_flag_and_invalid_json(self):
        root, current = self._root_with_current_loop()
        unsafe = dict(current)
        unsafe["loop_id"] = "unsafe-loop"
        unsafe["live_order_allowed"] = True
        unsafe["loop_hash"] = upbit_paper_persistent_loop_hash(unsafe)
        self._loop_path(root, "unsafe-loop").write_text(json.dumps(unsafe, indent=2), encoding="utf-8")
        invalid_path = self._loop_path(root, "invalid-loop")
        invalid_path.write_text("{not-json", encoding="utf-8")

        report = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        result = validate_upbit_paper_stale_loop_reconciliation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["reconciliation_status"], "BLOCKED")
        self.assertGreaterEqual(report["unsafe_blocked_count"], 2)
        self.assertEqual(report["invalid_json_count"], 1)
        classifications = {item["classification"] for item in report["items"]}
        self.assertIn("UNSAFE_BLOCKED", classifications)
        self.assertIn("UNREADABLE_OR_CORRUPT", classifications)

    def test_reconciliation_detects_duplicate_runtime_cycle_hash(self):
        root, current = self._root_with_current_loop()
        duplicate = json.loads(json.dumps(current))
        duplicate["loop_id"] = "duplicate-loop"
        duplicate["cycle_results"][0]["cycle_id"] = "duplicate-loop-cycle-1"
        duplicate["loop_hash"] = upbit_paper_persistent_loop_hash(duplicate)
        self._loop_path(root, "duplicate-loop").write_text(json.dumps(duplicate, indent=2), encoding="utf-8")

        report = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        result = validate_upbit_paper_stale_loop_reconciliation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["reconciliation_status"], "BLOCKED")
        self.assertEqual(report["duplicate_runtime_cycle_hash_count"], 1)
        self.assertEqual(report["primary_blocker_code"], "STALE_PERSISTENT_LOOP_REPORTS_REQUIRE_RECONCILIATION")

    def test_reconciliation_validator_blocks_false_permission_and_deletion(self):
        root, _ = self._root_with_current_loop()
        report = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        report["safe_delete_allowed"] = True
        report["reconciliation_hash"] = stale_loop_reconciliation_hash(report)

        result = validate_upbit_paper_stale_loop_reconciliation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_reconciliation_validator_blocks_non_current_item_marked_usable(self):
        root, current = self._root_with_current_loop()
        legacy = dict(current)
        legacy["loop_id"] = "legacy-loop"
        legacy.pop("paper_ledger_rollup_hash")
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        self._loop_path(root, "legacy-loop").write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        report = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        legacy_item = next(item for item in report["items"] if item["classification"] == "LEGACY_SCHEMA_DRIFT")
        legacy_item["evidence_usable_current"] = True
        report["current_evidence_usable_count"] += 1
        report["excluded_from_current_evidence_count"] -= 1
        report["reconciliation_hash"] = stale_loop_reconciliation_hash(report)

        result = validate_upbit_paper_stale_loop_reconciliation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "STALE_PERSISTENT_LOOP_REPORTS_REQUIRE_RECONCILIATION")


if __name__ == "__main__":
    unittest.main()
