import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    build_upbit_paper_runtime_sample_history,
    upbit_paper_runtime_sample_hash,
    upbit_paper_runtime_sample_history_hash,
    validate_upbit_paper_runtime_sample_history,
    write_upbit_paper_runtime_sample_history,
)


class UpbitPaperRuntimeSampleHistoryTest(unittest.TestCase):
    def _history(self) -> tuple[dict, Path]:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        run_upbit_paper_persistent_loop(root=root, loop_id="sample-history-a", requested_cycle_count=1)
        run_upbit_paper_persistent_loop(root=root, loop_id="sample-history-b", requested_cycle_count=1)
        return build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher"), root

    def test_runtime_sample_history_binds_actual_cycle_files_and_remains_live_blocked(self):
        history, root = self._history()
        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["accepted_cycle_sample_count"], 2)
        self.assertEqual(history["unique_runtime_cycle_hash_count"], 2)
        self.assertEqual(history["runtime_sample_status"], "COLLECTING")
        self.assertEqual(history["history_evidence_role"], "PAPER_RUNTIME_SAMPLE_HISTORY_NOT_LONG_RUN_EVIDENCE")
        self.assertEqual(history["long_run_blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        self.assertFalse(history["actual_long_run_evidence_created"])
        self.assertFalse(history["long_run_evidence_eligible"])
        self.assertFalse(history["promotion_eligible"])
        self.assertFalse(history["live_order_ready"])
        self.assertFalse(history["live_order_allowed"])
        self.assertFalse(history["can_live_trade"])
        self.assertFalse(history["scale_up_allowed"])
        self.assertEqual(history["samples"][1]["previous_sample_hash"], history["samples"][0]["sample_hash"])

        written_path = write_upbit_paper_runtime_sample_history(root=root, history=history)
        written = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_runtime_sample_history(written).status, "PASS")

    def test_runtime_sample_history_blocks_false_long_run_claim(self):
        history, _ = self._history()
        history["long_run_evidence_eligible"] = True
        history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)

        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_runtime_sample_history_blocks_duplicate_runtime_cycle_hash(self):
        history, _ = self._history()
        duplicate_sample = dict(history["samples"][0])
        duplicate_sample["generated_at_utc"] = history["samples"][-1]["generated_at_utc"]
        duplicate_sample["previous_sample_hash"] = history["samples"][-1]["sample_hash"]
        duplicate_sample["sample_hash"] = upbit_paper_runtime_sample_hash(duplicate_sample)
        history["samples"].append(duplicate_sample)
        history["accepted_cycle_sample_count"] = len(history["samples"])
        history["unique_runtime_cycle_hash_count"] = len({item["source_runtime_cycle_hash"] for item in history["samples"]})
        history["duplicate_cycle_hash_count"] = history["accepted_cycle_sample_count"] - history["unique_runtime_cycle_hash_count"]
        history["source_runtime_cycle_hashes"] = [item["source_runtime_cycle_hash"] for item in history["samples"]]
        history["latest_sample_at_utc"] = history["samples"][-1]["generated_at_utc"]
        history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)

        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_runtime_sample_history_blocks_cross_namespace_source_path(self):
        history, _ = self._history()
        history["samples"][0]["source_runtime_cycle_path"] = "system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/unsafe.runtime_cycle.json"
        history["samples"][0]["sample_hash"] = upbit_paper_runtime_sample_hash(history["samples"][0])
        history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)

        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_runtime_sample_history_detects_floor_flag_drift(self):
        history, _ = self._history()
        history["span_floor_met"] = True
        history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)

        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
