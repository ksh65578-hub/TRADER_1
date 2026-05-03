import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_post_rerun_current_evidence_closure_recheck import (
    POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_STATUS,
    POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_SOURCE_BINDING_REQUIRED,
    build_upbit_paper_post_rerun_current_evidence_closure_recheck_report,
    upbit_paper_post_rerun_current_evidence_closure_recheck_hash,
    validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report,
    write_upbit_paper_post_rerun_current_evidence_closure_recheck_report,
)
from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    build_upbit_paper_ledger_idempotency_runtime_evidence_report,
    upbit_paper_ledger_idempotency_runtime_evidence_hash,
    write_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.validation.mvp0_validators import run_validators


ROOT = Path(__file__).resolve().parents[2]
SESSION_ID = "mvp1_upbit_paper_launcher"


class UpbitPaperPostRerunCurrentEvidenceClosureRecheckTest(unittest.TestCase):
    def build_recheck_with_ledger_mutation(self, mutator=None) -> dict:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            closure_source = (
                ROOT
                / "system"
                / "runtime"
                / "upbit"
                / "krw_spot"
                / "paper"
                / SESSION_ID
                / "paper_runtime"
                / "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json"
            )
            closure_target = root / closure_source.relative_to(ROOT)
            closure_target.parent.mkdir(parents=True, exist_ok=True)
            closure_target.write_text(closure_source.read_text(encoding="utf-8"), encoding="utf-8")
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-post-rerun-closure-recheck-mutated-ledger",
                session_id=SESSION_ID,
                requested_cycle_count=1,
            )
            ledger_report = build_upbit_paper_ledger_idempotency_runtime_evidence_report(
                root=root,
                session_id=SESSION_ID,
                evidence_id="test-post-rerun-closure-recheck-mutated-ledger",
            )
            if mutator is not None:
                mutator(ledger_report)
                ledger_report["evidence_hash"] = upbit_paper_ledger_idempotency_runtime_evidence_hash(ledger_report)
            write_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root, report=ledger_report)
            return build_upbit_paper_post_rerun_current_evidence_closure_recheck_report(
                root=root,
                session_id=SESSION_ID,
            )

    def test_recheck_confirms_ledger_pass_cannot_override_post_rerun_closure(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            closure_source = (
                ROOT
                / "system"
                / "runtime"
                / "upbit"
                / "krw_spot"
                / "paper"
                / SESSION_ID
                / "paper_runtime"
                / "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json"
            )
            closure_target = root / closure_source.relative_to(ROOT)
            closure_target.parent.mkdir(parents=True, exist_ok=True)
            closure_target.write_text(closure_source.read_text(encoding="utf-8"), encoding="utf-8")
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-post-rerun-closure-recheck-ledger-pass",
                session_id=SESSION_ID,
                requested_cycle_count=1,
            )
            ledger_report = build_upbit_paper_ledger_idempotency_runtime_evidence_report(
                root=root,
                session_id=SESSION_ID,
                evidence_id="test-post-rerun-closure-recheck-ledger-pass",
            )
            write_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root, report=ledger_report)
            report = build_upbit_paper_post_rerun_current_evidence_closure_recheck_report(
                root=root,
                session_id=SESSION_ID,
            )
        result = validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["recheck_status"], POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_STATUS)
        self.assertEqual(report["source_closure_file_load_status"], "PASS")
        self.assertTrue(report["source_closure_file_hash_match"])
        self.assertEqual(report["source_ledger_idempotency_file_load_status"], "PASS")
        self.assertTrue(report["source_ledger_idempotency_file_hash_match"])
        self.assertEqual(report["source_closure_validation_status"], "PASS")
        self.assertEqual(report["source_ledger_idempotency_validation_status"], "PASS")
        self.assertEqual(report["ledger_runtime_evidence_status"], "PASS")
        self.assertEqual(report["ledger_reconciliation_status"], "PASS")
        self.assertEqual(report["ledger_idempotency_status"], "PASS")
        self.assertEqual(report["ledger_portfolio_provenance_status"], "PASS")
        self.assertEqual(report["ledger_source_persistent_loop_validation_status"], "PASS")
        self.assertEqual(report["ledger_source_persistent_loop_hash_self_check"], "PASS")
        self.assertTrue(report["ledger_head_cycle_in_persistent_loop"])
        self.assertEqual(report["ledger_source_runtime_input_role"], "PUBLIC_MARKET_DATA_COLLECTION")
        self.assertEqual(
            report["ledger_source_public_market_data_hash"],
            report["ledger_source_runtime_public_market_data_hash"],
        )
        self.assertGreaterEqual(report["ledger_source_canonical_event_count"], 5)
        self.assertEqual(report["ledger_source_runtime_depth_status"], "PASS")
        self.assertIsNone(report["ledger_source_runtime_depth_blocker_code"])
        self.assertEqual(report["ledger_source_runtime_depth_mismatch_count"], 0)
        self.assertFalse(report["ledger_source_strategy_regime_cost_linkage_live_order_ready"])
        self.assertFalse(report["ledger_source_strategy_regime_cost_linkage_live_order_allowed"])
        self.assertFalse(report["ledger_source_strategy_regime_cost_linkage_can_live_trade"])
        self.assertFalse(report["ledger_source_strategy_regime_cost_linkage_scale_up_allowed"])
        self.assertGreater(report["ledger_source_ledger_jsonl_count"], 0)
        self.assertGreater(report["ledger_recomputed_ledger_event_count"], 0)
        self.assertEqual(report["ledger_duplicate_total_count"], 0)
        self.assertEqual(report["ledger_mismatch_count"], 0)
        self.assertEqual(report["current_evidence_bridge_status"], "BLOCKED_BY_POST_RERUN_CLOSURE")
        self.assertEqual(
            report["portfolio_truth_recheck_status"],
            "LEDGER_PROVENANCE_PASS_BUT_OPERATOR_CURRENT_EVIDENCE_BLOCKED",
        )
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

        with TemporaryDirectory() as tmp:
            path = write_upbit_paper_post_rerun_current_evidence_closure_recheck_report(
                root=Path(tmp),
                report=report,
            )
            self.assertTrue(path.exists())

    def test_recheck_blocks_missing_ledger_source(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            closure_source = (
                ROOT
                / "system"
                / "runtime"
                / "upbit"
                / "krw_spot"
                / "paper"
                / SESSION_ID
                / "paper_runtime"
                / "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json"
            )
            closure_target = root / closure_source.relative_to(ROOT)
            closure_target.parent.mkdir(parents=True, exist_ok=True)
            closure_target.write_text(closure_source.read_text(encoding="utf-8"), encoding="utf-8")
            report = build_upbit_paper_post_rerun_current_evidence_closure_recheck_report(
                root=root,
                session_id=SESSION_ID,
            )
        result = validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report(report)

        self.assertEqual(report["source_ledger_idempotency_file_load_status"], "MISSING")
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_SOURCE_BINDING_REQUIRED)
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])

    def test_recheck_blocks_ledger_runtime_depth_regression(self):
        def mutate(ledger_report: dict) -> None:
            ledger_report["source_runtime_depth_status"] = "BLOCKED"
            ledger_report["source_runtime_depth_blocker_code"] = "MEASUREMENT_MISSING"
            ledger_report["source_runtime_depth_mismatch_count"] = 1

        report = self.build_recheck_with_ledger_mutation(mutate)
        result = validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report(report)

        self.assertEqual(report["ledger_source_runtime_depth_status"], "BLOCKED")
        self.assertEqual(report["ledger_source_runtime_depth_blocker_code"], "MEASUREMENT_MISSING")
        self.assertEqual(report["ledger_source_runtime_depth_mismatch_count"], 1)
        self.assertEqual(report["recheck_status"], "BLOCKED_CURRENT_LEDGER_IDEMPOTENCY_RECHECK_REQUIRED")
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn(result.blocker_code, {"SCHEMA_IDENTITY_MISMATCH", "MEASUREMENT_MISSING"})
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])

    def test_recheck_blocks_ledger_runtime_depth_live_linkage_mutation(self):
        def mutate(ledger_report: dict) -> None:
            ledger_report["source_strategy_regime_cost_linkage_live_order_allowed"] = True

        report = self.build_recheck_with_ledger_mutation(mutate)
        result = validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report(report)

        self.assertTrue(report["ledger_source_strategy_regime_cost_linkage_live_order_allowed"])
        self.assertEqual(report["recheck_status"], "BLOCKED_CURRENT_LEDGER_IDEMPOTENCY_RECHECK_REQUIRED")
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["scale_up_allowed"])

    def test_recheck_blocks_live_override_and_path_escape_mutations(self):
        report = build_upbit_paper_post_rerun_current_evidence_closure_recheck_report(
            root=ROOT,
            session_id=SESSION_ID,
        )

        live_mutation = json.loads(json.dumps(report))
        live_mutation["post_rerun_override_allowed"] = True
        live_mutation["live_order_allowed"] = True
        live_mutation["recheck_hash"] = upbit_paper_post_rerun_current_evidence_closure_recheck_hash(live_mutation)
        live_result = validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        path_escape = json.loads(json.dumps(report))
        path_escape["source_ledger_idempotency_path"] = (
            "system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/ledger/"
            "upbit_paper_ledger_idempotency_runtime_evidence_report.json"
        )
        path_escape["recheck_hash"] = upbit_paper_post_rerun_current_evidence_closure_recheck_hash(path_escape)
        path_result = validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report(path_escape)
        self.assertEqual(path_result.status, "BLOCKED")
        self.assertEqual(path_result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_validator_passes_current_contract(self):
        results = run_validators(["upbit_paper_post_rerun_current_evidence_closure_recheck_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
