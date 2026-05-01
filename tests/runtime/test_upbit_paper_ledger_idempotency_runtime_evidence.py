import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.ledger.paper_ledger_rollup import (
    build_paper_ledger_rollup_report,
    write_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    build_upbit_paper_ledger_idempotency_runtime_evidence_report,
    upbit_paper_ledger_idempotency_runtime_evidence_hash,
    validate_upbit_paper_ledger_idempotency_runtime_evidence_report,
    write_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.validation.mvp0_validators import run_validators


class UpbitPaperLedgerIdempotencyRuntimeEvidenceTest(unittest.TestCase):
    def test_evidence_recomputes_current_rollup_idempotency_and_stays_live_blocked(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-upbit-paper-idempotency-evidence",
                requested_cycle_count=2,
            )

            report = build_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root)
            result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(report)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(report["runtime_evidence_status"], "PASS")
            self.assertEqual(report["source_rollup_validation_status"], "PASS")
            self.assertEqual(report["source_count_match_status"], "PASS")
            self.assertEqual(report["idempotency_status"], "PASS")
            self.assertEqual(report["reconciliation_status"], "PASS")
            self.assertEqual(report["portfolio_provenance_status"], "PASS")
            self.assertEqual(report["ledger_head_binding_status"], "PASS")
            self.assertEqual(report["source_ledger_jsonl_count"], 2)
            self.assertEqual(report["recomputed_filled_order_count"], 2)
            self.assertEqual(report["duplicate_event_id_count"], 0)
            self.assertEqual(report["duplicate_dedup_key_count"], 0)
            self.assertEqual(report["duplicate_semantic_event_count"], 0)
            self.assertEqual(report["duplicate_filled_order_key_count"], 0)
            self.assertFalse(report["live_order_ready"])
            self.assertFalse(report["live_order_allowed"])
            self.assertFalse(report["can_live_trade"])
            self.assertFalse(report["scale_up_allowed"])

            path = write_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root, report=report)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(validate_upbit_paper_ledger_idempotency_runtime_evidence_report(loaded).status, "PASS")

    def test_evidence_blocks_duplicate_cross_cycle_ledger_events(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-upbit-paper-idempotency-duplicate",
                requested_cycle_count=1,
            )
            ledger_path = None
            for artifact_path in loop["cycle_results"][0]["artifact_paths"]:
                if str(artifact_path).endswith(".paper_ledger_events.jsonl"):
                    ledger_path = root / str(artifact_path)
                    break
            self.assertIsNotNone(ledger_path)
            duplicate_path = ledger_path.with_name("duplicate-idempotency.paper_ledger_events.jsonl")
            duplicate_path.write_text(ledger_path.read_text(encoding="utf-8"), encoding="utf-8")
            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-upbit-paper-idempotency-duplicate",
            )
            write_paper_ledger_rollup_report(root=root, report=rollup)

            report = build_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root)
            result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(report)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")
            self.assertEqual(report["runtime_evidence_status"], "BLOCKED")
            self.assertEqual(report["idempotency_status"], "BLOCKED")
            self.assertGreater(report["duplicate_event_id_count"], 0)
            self.assertFalse(report["live_order_allowed"])

    def test_evidence_blocks_source_count_mismatch_mutation(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-upbit-paper-idempotency-count-mismatch",
                requested_cycle_count=1,
            )
            report = build_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root)

        report["source_ledger_event_count"] = report["source_ledger_event_count"] + 1
        report["evidence_hash"] = upbit_paper_ledger_idempotency_runtime_evidence_hash(report)
        result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_evidence_blocks_live_permission_and_path_escape_mutations(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-upbit-paper-idempotency-mutation",
                requested_cycle_count=1,
            )
            report = build_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root)

        live_mutation = dict(report)
        live_mutation["live_order_allowed"] = True
        live_mutation["evidence_hash"] = upbit_paper_ledger_idempotency_runtime_evidence_hash(live_mutation)
        live_result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        path_escape = dict(report)
        path_escape["source_ledger_paths"] = list(path_escape["source_ledger_paths"]) + [
            "system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/ledger/unsafe.paper_ledger_events.jsonl"
        ]
        path_escape["recomputed_ledger_jsonl_count"] = len(path_escape["source_ledger_paths"])
        path_escape["evidence_hash"] = upbit_paper_ledger_idempotency_runtime_evidence_hash(path_escape)
        path_result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(path_escape)
        self.assertEqual(path_result.status, "BLOCKED")
        self.assertEqual(path_result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_validator_passes_current_contract(self):
        results = run_validators(["upbit_paper_ledger_idempotency_runtime_evidence_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
