import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_repair_path import (
    POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED,
    POST_RERUN_RECONCILIATION_REPAIR_PATH_STATUS,
    build_upbit_paper_post_rerun_reconciliation_repair_path_report,
    upbit_paper_post_rerun_reconciliation_repair_path_hash,
    validate_upbit_paper_post_rerun_reconciliation_repair_path_report,
    write_upbit_paper_post_rerun_reconciliation_repair_path_report,
)
from trader1.validation.mvp0_validators import run_validators


ROOT = Path(__file__).resolve().parents[2]
SESSION_ID = "mvp1_upbit_paper_launcher"


class UpbitPaperPostRerunReconciliationRepairPathTest(unittest.TestCase):
    def test_repair_path_declares_blocked_repair_gates_without_current_evidence(self):
        report = build_upbit_paper_post_rerun_reconciliation_repair_path_report(
            root=ROOT,
            session_id=SESSION_ID,
        )
        result = validate_upbit_paper_post_rerun_reconciliation_repair_path_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["repair_path_status"], POST_RERUN_RECONCILIATION_REPAIR_PATH_STATUS)
        self.assertEqual(report["primary_blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertEqual(report["source_closure_file_load_status"], "PASS")
        self.assertTrue(report["source_closure_file_hash_match"])
        self.assertEqual(report["source_recheck_file_load_status"], "PASS")
        self.assertTrue(report["source_recheck_file_hash_match"])
        self.assertEqual(report["source_closure_validation_status"], "PASS")
        self.assertEqual(report["source_recheck_validation_status"], "PASS")
        self.assertEqual(report["source_closure_current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["source_closure_candidate_current_evidence_usable_count"], 0)
        self.assertEqual(report["source_recheck_bridge_status"], "BLOCKED_BY_POST_RERUN_CLOSURE")
        self.assertEqual(report["source_recheck_ledger_source_persistent_loop_validation_status"], "PASS")
        self.assertEqual(report["source_recheck_ledger_source_persistent_loop_hash_self_check"], "PASS")
        self.assertTrue(report["source_recheck_ledger_head_cycle_in_persistent_loop"])
        self.assertEqual(report["source_recheck_ledger_source_runtime_input_role"], "PUBLIC_MARKET_DATA_COLLECTION")
        self.assertEqual(
            report["source_recheck_ledger_source_public_market_data_hash"],
            report["source_recheck_ledger_source_runtime_public_market_data_hash"],
        )
        self.assertGreaterEqual(report["source_recheck_ledger_source_canonical_event_count"], 5)
        self.assertEqual(report["source_recheck_ledger_source_runtime_depth_status"], "PASS")
        self.assertIsNone(report["source_recheck_ledger_source_runtime_depth_blocker_code"])
        self.assertEqual(report["source_recheck_ledger_source_runtime_depth_mismatch_count"], 0)
        self.assertFalse(report["source_recheck_ledger_source_strategy_regime_cost_linkage_live_order_ready"])
        self.assertFalse(report["source_recheck_ledger_source_strategy_regime_cost_linkage_live_order_allowed"])
        self.assertFalse(report["source_recheck_ledger_source_strategy_regime_cost_linkage_can_live_trade"])
        self.assertFalse(report["source_recheck_ledger_source_strategy_regime_cost_linkage_scale_up_allowed"])
        self.assertEqual(report["repair_gate_count"], 4)
        self.assertEqual(report["satisfied_repair_gate_count"], 0)
        self.assertEqual(report["blocked_repair_gate_count"], 4)
        self.assertEqual(report["current_evidence_write_authorized_count"], 0)
        self.assertEqual(report["current_evidence_write_allowed_count"], 0)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertEqual(
            [gate["gate_id"] for gate in report["repair_gates"]],
            [
                "VALIDATED_OPERATOR_RESOLUTION_ACCEPTANCE",
                "VALIDATED_CURRENT_LEDGER_REBUILD",
                "VALIDATED_SOURCE_HASH_RECONCILIATION",
                "VALIDATED_NO_LIVE_OR_SCALE_MUTATION",
            ],
        )
        for gate in report["repair_gates"]:
            self.assertEqual(gate["gate_status"], "BLOCKED")
            self.assertFalse(gate["satisfied"])
            self.assertFalse(gate["current_evidence_write_allowed"])
            self.assertFalse(gate["live_order_allowed"])
            self.assertFalse(gate["can_live_trade"])
            self.assertFalse(gate["scale_up_allowed"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

        with TemporaryDirectory() as tmp:
            path = write_upbit_paper_post_rerun_reconciliation_repair_path_report(
                root=Path(tmp),
                report=report,
            )
            self.assertTrue(path.exists())

    def test_repair_path_blocks_missing_recheck_source(self):
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
            report = build_upbit_paper_post_rerun_reconciliation_repair_path_report(
                root=root,
                session_id=SESSION_ID,
            )
        result = validate_upbit_paper_post_rerun_reconciliation_repair_path_report(report)

        self.assertEqual(report["source_recheck_file_load_status"], "MISSING")
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED)
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])

    def test_repair_path_blocks_live_gate_satisfaction_and_path_escape(self):
        report = build_upbit_paper_post_rerun_reconciliation_repair_path_report(
            root=ROOT,
            session_id=SESSION_ID,
        )

        live_mutation = json.loads(json.dumps(report))
        live_mutation["repair_gates"][0]["satisfied"] = True
        live_mutation["repair_gates"][0]["live_order_allowed"] = True
        live_mutation["live_order_allowed"] = True
        live_mutation["repair_path_hash"] = upbit_paper_post_rerun_reconciliation_repair_path_hash(live_mutation)
        live_result = validate_upbit_paper_post_rerun_reconciliation_repair_path_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        path_escape = json.loads(json.dumps(report))
        path_escape["source_recheck_path"] = (
            "system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/paper_runtime/"
            "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json"
        )
        path_escape["repair_path_hash"] = upbit_paper_post_rerun_reconciliation_repair_path_hash(path_escape)
        path_result = validate_upbit_paper_post_rerun_reconciliation_repair_path_report(path_escape)
        self.assertEqual(path_result.status, "BLOCKED")
        self.assertEqual(path_result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_repair_path_blocks_recheck_runtime_depth_and_live_linkage_drift(self):
        report = build_upbit_paper_post_rerun_reconciliation_repair_path_report(
            root=ROOT,
            session_id=SESSION_ID,
        )

        runtime_depth_drift = json.loads(json.dumps(report))
        runtime_depth_drift["source_recheck_ledger_source_runtime_depth_status"] = "BLOCKED"
        runtime_depth_drift["source_recheck_ledger_source_runtime_depth_mismatch_count"] = 1
        runtime_depth_drift["repair_path_hash"] = upbit_paper_post_rerun_reconciliation_repair_path_hash(
            runtime_depth_drift
        )
        runtime_depth_result = validate_upbit_paper_post_rerun_reconciliation_repair_path_report(
            runtime_depth_drift
        )
        self.assertEqual(runtime_depth_result.status, "BLOCKED")
        self.assertEqual(runtime_depth_result.blocker_code, POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED)

        live_linkage_drift = json.loads(json.dumps(report))
        live_linkage_drift["source_recheck_ledger_source_strategy_regime_cost_linkage_live_order_allowed"] = True
        live_linkage_drift["repair_path_hash"] = upbit_paper_post_rerun_reconciliation_repair_path_hash(
            live_linkage_drift
        )
        live_linkage_result = validate_upbit_paper_post_rerun_reconciliation_repair_path_report(live_linkage_drift)
        self.assertEqual(live_linkage_result.status, "BLOCKED")
        self.assertEqual(live_linkage_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_validator_passes_current_contract(self):
        results = run_validators(["upbit_paper_post_rerun_reconciliation_repair_path_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
