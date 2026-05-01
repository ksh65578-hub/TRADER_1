from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.review_plan_reflection_status import (
    EXPECTED_REVIEW_NUMBERS,
    ORIGINAL_REVIEW_FILE_PRESERVATION_REQUIRED_AFTER_REFLECTION,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_DELETED,
    REVIEW_STATUS_READY,
    build_reflection_ledger,
    catalog_review_files,
    delete_reflected_files,
    mark_current_files_reflected,
    validate_reflection_ledger,
)


class ReviewPlanReflectionStatusTests(unittest.TestCase):
    def test_catalog_covers_current_review_plan_files(self) -> None:
        catalog = catalog_review_files()
        ledger = build_reflection_ledger()
        numbers = sorted(
            entry["review_number"]
            for entry in ledger["review_files"]
            if isinstance(entry.get("review_number"), int) and entry["review_number"] in EXPECTED_REVIEW_NUMBERS
        )
        self.assertEqual(numbers, EXPECTED_REVIEW_NUMBERS)
        self.assertEqual(ledger["review_files_count"], 43)
        self.assertTrue(all(entry["sha256"] and len(entry["sha256"]) == 64 for entry in catalog))
        self.assertTrue(all(entry["theme_ids"] for entry in catalog))
        self.assertEqual(validate_reflection_ledger(ledger)["status"], "PASS")

    def test_default_ledger_preserves_review_files_until_reflection_evidence_exists(self) -> None:
        ledger = build_reflection_ledger()
        self.assertEqual(ledger["review_files_count"], 43)
        self.assertEqual(ledger["delete_ready_count"], 0)
        self.assertEqual(ledger["pending_reflection_count"] + ledger.get("deleted_after_reflection_count", 0), 43)
        self.assertFalse(ledger["live_order_ready"])
        self.assertFalse(ledger["live_order_allowed"])
        self.assertFalse(ledger["can_live_trade"])
        self.assertFalse(ledger["scale_up_allowed"])
        self.assertFalse(ledger["deletion_policy"]["original_review_file_preservation_required_after_reflection"])
        self.assertFalse(ORIGINAL_REVIEW_FILE_PRESERVATION_REQUIRED_AFTER_REFLECTION)
        self.assertTrue(
            all(
                entry["reflection_status"] in {REVIEW_STATUS_PENDING, REVIEW_STATUS_DELETED}
                for entry in ledger["review_files"]
            )
        )
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

    def test_new_review_number_is_accepted_as_pending_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            review_dir = root / "검토안"
            review_dir.mkdir()
            (review_dir / "45.md").write_text("새 검토안입니다.\nDashboard paper live strategy\n", encoding="utf-8")
            ledger = build_reflection_ledger(root=root, review_dir=review_dir)
            self.assertEqual(ledger["review_files_count"], 1)
            self.assertEqual(ledger["pending_reflection_count"], 1)
            self.assertEqual(validate_reflection_ledger(ledger, root=root)["status"], "PASS")

    def test_reflected_review_file_can_be_deleted_without_preserving_original(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            review_dir = root / "검토안"
            evidence_dir = root / "system" / "evidence" / "patch_results"
            review_dir.mkdir()
            evidence_dir.mkdir(parents=True)
            for number in EXPECTED_REVIEW_NUMBERS:
                (review_dir / f"{number}.md").write_text(
                    f"{number}차 검토 결과입니다.\nBinance dashboard paper live strategy runtime\n",
                    encoding="utf-8",
                )
            evidence_path = evidence_dir / "REFLECTED.patch_result.json"
            evidence_path.write_text('{"live_order_ready": false}\n', encoding="utf-8")

            ledger = build_reflection_ledger(root=root, review_dir=review_dir)
            first = ledger["review_files"][0]
            first["reflection_status"] = REVIEW_STATUS_READY
            first["reflected_by_patch_ids"] = ["REFLECTED"]
            first["reflection_evidence_paths"] = ["system/evidence/patch_results/REFLECTED.patch_result.json"]
            first["authority_priority_preserved"] = True
            first["original_review_file_preservation_required_after_reflection"] = False
            first["deletion_allowed"] = True

            result = validate_reflection_ledger(ledger, root=root)
            self.assertEqual(result["status"], "PASS")
            deleted = delete_reflected_files(ledger, root=root, max_delete_count=1)
            self.assertEqual(deleted, ["검토안/1.md"])
            self.assertFalse((review_dir / "1.md").exists())
            self.assertTrue((review_dir / "2.md").exists())
            self.assertEqual(validate_reflection_ledger(ledger, root=root)["status"], "PASS")

    def test_current_files_can_be_marked_reflected_and_deleted_as_a_batch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            review_dir = root / "검토안"
            evidence_dir = root / "system" / "evidence" / "patch_results"
            review_dir.mkdir()
            evidence_dir.mkdir(parents=True)
            for number in EXPECTED_REVIEW_NUMBERS:
                (review_dir / f"{number}.md").write_text(
                    f"{number}차 검토 결과입니다.\nBinance dashboard paper live strategy runtime\n",
                    encoding="utf-8",
                )
            evidence_path = evidence_dir / "REFLECTED.patch_result.json"
            evidence_path.write_text('{"live_order_ready": false}\n', encoding="utf-8")

            ledger = build_reflection_ledger(root=root, review_dir=review_dir)
            marked = mark_current_files_reflected(
                ledger,
                patch_id="REFLECTED",
                evidence_paths=["system/evidence/patch_results/REFLECTED.patch_result.json"],
                root=root,
            )
            self.assertEqual(len(marked), 43)
            self.assertEqual(validate_reflection_ledger(ledger, root=root)["status"], "PASS")
            deleted = delete_reflected_files(ledger, root=root, max_delete_count=1000)
            self.assertEqual(len(deleted), 43)
            self.assertFalse(any(review_dir.glob("*.md")))
            self.assertTrue(all(entry["reflection_status"] == REVIEW_STATUS_DELETED for entry in ledger["review_files"]))
            self.assertEqual(validate_reflection_ledger(ledger, root=root)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
