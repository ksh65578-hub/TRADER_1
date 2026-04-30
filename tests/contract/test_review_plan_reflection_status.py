from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.review_plan_reflection_status import (
    EXPECTED_REVIEW_NUMBERS,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_READY,
    build_reflection_ledger,
    catalog_review_files,
    validate_reflection_ledger,
)


class ReviewPlanReflectionStatusTests(unittest.TestCase):
    def test_catalog_covers_current_review_plan_files(self) -> None:
        catalog = catalog_review_files()
        numbers = [entry["review_number"] for entry in catalog]
        self.assertEqual(numbers, EXPECTED_REVIEW_NUMBERS)
        self.assertEqual(len(catalog), 43)
        self.assertTrue(all(entry["sha256"] and len(entry["sha256"]) == 64 for entry in catalog))
        self.assertTrue(all(entry["theme_ids"] for entry in catalog))

    def test_default_ledger_preserves_review_files_until_reflection_evidence_exists(self) -> None:
        ledger = build_reflection_ledger()
        self.assertEqual(ledger["review_files_count"], 43)
        self.assertEqual(ledger["delete_ready_count"], 0)
        self.assertEqual(ledger["pending_reflection_count"], 43)
        self.assertFalse(ledger["live_order_ready"])
        self.assertFalse(ledger["live_order_allowed"])
        self.assertFalse(ledger["can_live_trade"])
        self.assertFalse(ledger["scale_up_allowed"])
        self.assertTrue(all(entry["reflection_status"] == REVIEW_STATUS_PENDING for entry in ledger["review_files"]))
        self.assertTrue(all(not entry["deletion_allowed"] for entry in ledger["review_files"]))

    def test_delete_ready_without_evidence_is_blocked(self) -> None:
        ledger = build_reflection_ledger()
        entry = ledger["review_files"][0]
        entry["reflection_status"] = REVIEW_STATUS_READY
        entry["deletion_allowed"] = True
        entry["reflected_by_patch_ids"] = []
        entry["reflection_evidence_paths"] = []
        result = validate_reflection_ledger(ledger)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn(f"unsafe_delete_ready:{entry['review_file']}", result["blockers"])

    def test_missing_review_file_is_blocked_unless_deleted_status_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            review_dir = root / "검토안"
            review_dir.mkdir()
            (review_dir / "1.md").write_text("1차 전수검사 결과입니다.\nBinance dashboard paper live\n", encoding="utf-8")
            ledger = build_reflection_ledger(root=root, review_dir=review_dir)
            (review_dir / "1.md").unlink()
            result = validate_reflection_ledger(ledger, root=root)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("review_file_missing:검토안/1.md", result["blockers"])


if __name__ == "__main__":
    unittest.main()
