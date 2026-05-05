import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.patch_result.json"
)
STAGE_GATE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "stage_gates"
    / "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.stage_gate_result.json"
)
DEPTH_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.json"
)
CONTRACT_GAP_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "contract_gaps"
    / "POST_REPAIR_RECONCILIATION_REQUIRED.contract_gap.json"
)
RUNTIME_BASE = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
)
REQUIREMENT_ID = "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
GAP_ID = "POST_REPAIR_RECONCILIATION_REQUIRED"
NEXT_TASK_CLASS = "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
HASH_MISMATCH_DEPTH_REQUIREMENT_ID = (
    "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_HASH_MISMATCH_DEPTH_NEXT_TASK = (
    "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"
)
BLOCKED_REPAIR_PLAN_DEPTH_REQUIREMENT_ID = (
    "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_BLOCKED_REPAIR_PLAN_DEPTH_NEXT_TASK = (
    "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"
)
REGENERATED_CURRENT_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-RECONCILIATION-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_REGENERATED_CURRENT_DEPTH_NEXT_TASK = (
    "MVP4_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
STALE_LOOP_REGENERATION_REQUIRED_DEPTH_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_STALE_LOOP_REGENERATION_REQUIRED_DEPTH_NEXT_TASK = (
    "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
STALE_LOOP_REGENERATION_EXECUTION_DEPTH_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_STALE_LOOP_REGENERATION_EXECUTION_DEPTH_NEXT_TASK = (
    "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PostRepairReconciliationRequiredImplementationDepthRecheckTest(unittest.TestCase):
    def test_depth_recheck_keeps_post_repair_candidate_review_only(self):
        patch_result = load_json(PATCH_PATH)
        stage_gate = load_json(STAGE_GATE_PATH)
        depth_report = load_json(DEPTH_REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(
            depth_report["status"],
            "PASS_DEPTH_5_POST_REPAIR_RECONCILIATION_REQUIRED_LIVE_BLOCKING",
        )
        self.assertEqual(
            stage_gate["stage_gate_status"],
            "PASS_POST_REPAIR_RECONCILIATION_REQUIRED_DEPTH_RECHECK_LIVE_BLOCKING",
        )

        self.assertEqual(depth_report["post_repair_reconciliation_status"], "BLOCKED")
        self.assertEqual(depth_report["primary_blocker_code"], GAP_ID)
        self.assertEqual(depth_report["repair_candidate_count"], 1)
        self.assertEqual(depth_report["reconciliation_item_count"], 1)
        self.assertEqual(depth_report["source_loop_expected_rollup_hash_mismatch_count"], 1)
        self.assertEqual(depth_report["hash_operator_reconciliation_required_count"], 1)
        self.assertEqual(depth_report["operator_queue_status"], "BLOCKED")
        self.assertEqual(depth_report["operator_queue_item_count"], 6)
        self.assertEqual(depth_report["operator_queue_hash_required_count"], 1)
        self.assertEqual(depth_report["candidate_current_evidence_usable_count"], 0)
        self.assertEqual(depth_report["operator_queue_candidate_current_evidence_usable_count"], 0)
        self.assertFalse(depth_report["current_evidence_mutation_allowed"])
        self.assertFalse(depth_report["persistent_loop_mutation_allowed"])
        self.assertFalse(depth_report["source_delete_allowed"])

    def test_runtime_artifact_chain_remains_fail_closed(self):
        for artifact_name in (
            "upbit_paper_post_repair_reconciliation_report.json",
            "upbit_paper_repair_operator_queue_report.json",
        ):
            with self.subTest(artifact_name=artifact_name):
                report = load_json(RUNTIME_BASE / artifact_name)
                self.assertFalse(report.get("live_order_ready", False))
                self.assertFalse(report.get("live_order_allowed", False))
                self.assertFalse(report.get("can_live_trade", False))
                self.assertFalse(report.get("scale_up_allowed", False))
                self.assertFalse(report.get("current_evidence_mutation_allowed", False))
                self.assertFalse(report.get("persistent_loop_mutation_allowed", False))
                self.assertFalse(report.get("source_delete_allowed", False))
                self.assertEqual(report.get("candidate_current_evidence_usable_count", 0), 0)

    def test_contract_gap_projection_remains_open_and_live_affecting(self):
        gap = load_json(CONTRACT_GAP_PATH)
        self.assertEqual(gap["schema_id"], "trader1.contract_gap.v1")
        self.assertEqual(gap["contract_gap_id"], GAP_ID)
        self.assertEqual(gap["status"], "OPEN")
        self.assertEqual(gap["severity"], "HIGH")
        self.assertTrue(gap["live_affecting"])
        self.assertEqual(gap["exchange"], "UPBIT")
        self.assertEqual(gap["market_type"], "KRW_SPOT")
        self.assertEqual(gap["mode"], "PAPER")

    def test_state_routes_forward_after_post_repair_depth_recheck(self):
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertIn(GAP_ID, state["open_contract_gap_ids"])
        self.assertIn(GAP_ID, patch_result["remaining_blockers"])
        if (state["last_patch_id"].startswith("MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_BLOCKER_SUMMARY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING_") or state["last_patch_id"].startswith("MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_OPERATOR_HANDOFF_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_EVIDENCE_PROGRESS_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT_")):
            expected_next_task = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif (state["last_patch_id"].startswith("MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_PAPER_PORTFOLIO_CURRENT_TRUTH_UX_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_OPERATOR_FOCUS_SIMPLIFICATION_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_LIVE_AVAILABILITY_REASON_")))):
            expected_next_task = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK_"):
            expected_next_task = "MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK_"):
            expected_next_task = "MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK_"):
            expected_next_task = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK_"):
            expected_next_task = "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK_"):
            expected_next_task = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING_"):
            expected_next_task = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK_"):
            expected_next_task = "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
            self.assertEqual(
                state["next_allowed_task_class"],
                expected_next_task,
            )
            self.assertNotIn(
                "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING",
                state["open_contract_gap_ids"],
            )
        elif state["last_patch_id"].startswith("MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK_"):
            self.assertEqual(
                state["next_allowed_task_class"],
                "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK",
            )
        elif STALE_LOOP_REGENERATION_EXECUTION_DEPTH_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_STALE_LOOP_REGENERATION_EXECUTION_DEPTH_NEXT_TASK)
        elif STALE_LOOP_REGENERATION_REQUIRED_DEPTH_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_STALE_LOOP_REGENERATION_REQUIRED_DEPTH_NEXT_TASK)
        elif REGENERATED_CURRENT_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_REGENERATED_CURRENT_DEPTH_NEXT_TASK)
        elif BLOCKED_REPAIR_PLAN_DEPTH_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_BLOCKED_REPAIR_PLAN_DEPTH_NEXT_TASK)
        elif HASH_MISMATCH_DEPTH_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["next_allowed_task_class"], AFTER_HASH_MISMATCH_DEPTH_NEXT_TASK)
        else:
            self.assertEqual(state["last_patch_id"], patch_result["patch_id"])
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)

        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])
        for field in (
            "live_order_ready_after",
            "live_order_allowed_after",
            "can_live_trade_after",
            "scale_up_allowed_after",
            "convergence_live_order_allowed_after",
            "optimizer_live_order_allowed_after",
        ):
            self.assertFalse(patch_result[field])


if __name__ == "__main__":
    unittest.main()
