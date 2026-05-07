import json
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.runtime.paper import upbit_paper_runtime_sample_history as sample_history_module
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    build_upbit_paper_runtime_sample_history,
    upbit_paper_runtime_sample_hash,
    upbit_paper_runtime_sample_history_hash,
    validate_upbit_paper_runtime_sample_history,
    write_upbit_paper_runtime_sample_history,
)
from trader1.validation.schema_instance import load_schema_bundle, schema_for_instance, validate_instance_against_schema


ROOT = Path(__file__).resolve().parents[2]


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
        first_sample = history["samples"][0]
        self.assertGreaterEqual(first_sample["candidate_count"], 1)
        self.assertGreaterEqual(first_sample["entry_reason_count"], 1)
        self.assertIn("exit_reason_count", first_sample)
        self.assertEqual(first_sample["scorecard_candidate_identity_binding_status"], "BOUND")
        self.assertEqual(first_sample["scorecard_candidate_live_flags_clear"], True)
        self.assertIsInstance(first_sample["scorecard_candidate_id"], str)
        self.assertIsInstance(first_sample["scorecard_symbol"], str)
        self.assertIsInstance(first_sample["scorecard_strategy_id"], str)
        self.assertEqual(len(first_sample["scorecard_parameter_hash"]), 64)
        self.assertEqual(
            first_sample["paper_entry_review_candidate_count"],
            len(first_sample["paper_entry_review_candidate_ids"]),
        )
        self.assertEqual(
            first_sample["paper_entry_review_symbol_count"],
            len(set(first_sample["paper_entry_review_symbols"])),
        )
        self.assertEqual(history["samples"][1]["previous_sample_hash"], history["samples"][0]["sample_hash"])

        written_path = write_upbit_paper_runtime_sample_history(root=root, history=history)
        written = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_runtime_sample_history(written).status, "PASS")
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(written, schema_bundle)
        self.assertIsNotNone(schema)
        schema_result = validate_instance_against_schema(written, schema, schema_bundle)
        self.assertEqual(schema_result.status, "PASS", schema_result.errors)

    def test_entry_reason_evidence_counts_blocked_candidate_entry_review(self):
        runtime_cycle = {
            "entry_reasons": [],
            "selected_candidate": {"decision": "PAPER_ENTRY_REVIEW"},
            "final_decision": "BLOCKED",
            "no_trade_reasons": ["RISK_VETO"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        self.assertEqual(sample_history_module._entry_reason_evidence_count(runtime_cycle), 1)

    def test_entry_reason_evidence_counts_review_candidates_when_position_management_overrides_final_decision(self):
        runtime_cycle = {
            "entry_reasons": [],
            "selected_candidate": {"decision": "NO_TRADE", "no_trade_reason": "REGIME_MISMATCH"},
            "strategy_candidates": [
                {"candidate_id": "candidate-1", "decision": "PAPER_ENTRY_REVIEW"},
                {"candidate_id": "candidate-2", "decision": "NO_TRADE"},
                {"candidate_id": "candidate-3", "decision": "PAPER_ENTRY_REVIEW"},
            ],
            "final_decision": "EXIT_POSITION",
            "no_trade_reasons": ["REGIME_ROTATION_EXIT"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        self.assertEqual(sample_history_module._entry_reason_evidence_count(runtime_cycle), 2)

    def test_exit_reason_evidence_counts_position_management_decision(self):
        runtime_cycle = {
            "final_decision": "REDUCE_POSITION",
            "no_trade_reasons": ["PARTIAL_EXIT_FILL", "REGIME_ROTATION_EXIT"],
            "position_management_decision": {
                "final_decision": "REDUCE_POSITION",
                "requested_position_decision": "EXIT_POSITION",
                "reason_code": "REGIME_ROTATION_EXIT",
                "execution_adjusted_position_decision_reason": "PARTIAL_EXIT_FILL",
            },
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        self.assertEqual(sample_history_module._exit_reason_evidence_count(runtime_cycle), 6)

    def test_runtime_sample_history_excludes_invalid_legacy_loop_sources_while_collecting(self):
        history, root = self._history()
        paper_runtime_dir = (
            root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime"
        )
        invalid_legacy = paper_runtime_dir / "legacy-schema.invalid.persistent_loop_report.json"
        invalid_legacy.write_text("{}\n", encoding="utf-8")

        history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["runtime_sample_status"], "COLLECTING")
        self.assertEqual(history["primary_blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        self.assertEqual(history["accepted_cycle_sample_count"], 2)
        self.assertEqual(history["invalid_source_count"], 1)
        self.assertEqual(len(history["invalid_sources"]), 1)
        self.assertIn("schema", history["invalid_sources"][0]["reason"].lower())
        self.assertFalse(history["long_run_evidence_eligible"])
        self.assertFalse(history["live_order_allowed"])

    def test_runtime_sample_history_binds_runtime_hashes_after_timestamp_sorting(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        run_upbit_paper_persistent_loop(root=root, loop_id="zz-sample-history-sort-source", requested_cycle_count=1)
        time.sleep(1.1)
        run_upbit_paper_persistent_loop(root=root, loop_id="aa-sample-history-sort-source", requested_cycle_count=1)

        history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(
            history["source_runtime_cycle_hashes"],
            [sample["source_runtime_cycle_hash"] for sample in history["samples"]],
        )
        self.assertEqual(history["samples"][0]["loop_id"], "zz-sample-history-sort-source")
        self.assertEqual(history["samples"][1]["loop_id"], "aa-sample-history-sort-source")

    def test_runtime_sample_history_uses_numeric_cycle_order_for_same_second_cycles(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        run_upbit_paper_persistent_loop(root=root, loop_id="sample-history-natural-cycle-sort", requested_cycle_count=12)

        history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        result = validate_upbit_paper_runtime_sample_history(history)
        cycle_ids = [sample["cycle_id"] for sample in history["samples"]]

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["accepted_cycle_sample_count"], 12)
        self.assertLess(
            cycle_ids.index("sample-history-natural-cycle-sort-cycle-9"),
            cycle_ids.index("sample-history-natural-cycle-sort-cycle-10"),
        )
        self.assertEqual(cycle_ids[-1], "sample-history-natural-cycle-sort-cycle-12")

    def test_runtime_sample_history_blocks_duplicate_source_cycle_hash_from_copied_loop_report(self):
        history, root = self._history()
        paper_runtime_dir = (
            root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime"
        )
        source = paper_runtime_dir / "sample-history-a.persistent_loop_report.json"
        duplicate = paper_runtime_dir / "sample-history-a-copy.persistent_loop_report.json"
        duplicate.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")
        self.assertEqual(history["runtime_sample_status"], "BLOCKED")
        self.assertEqual(history["primary_blocker_code"], "RECONCILIATION_REQUIRED")
        self.assertEqual(history["accepted_cycle_sample_count"], 2)
        self.assertEqual(history["duplicate_cycle_hash_count"], 1)
        self.assertFalse(history["live_order_allowed"])

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
