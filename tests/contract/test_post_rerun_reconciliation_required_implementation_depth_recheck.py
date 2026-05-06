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
    / "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.patch_result.json"
)
STAGE_GATE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "stage_gates"
    / "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.stage_gate_result.json"
)
DEPTH_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.json"
)
CONTRACT_GAP_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "contract_gaps"
    / "POST_RERUN_RECONCILIATION_REQUIRED.contract_gap.json"
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
REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
GAP_ID = "POST_RERUN_RECONCILIATION_REQUIRED"
NEXT_TASK_CLASS = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-POST-RERUN-CURRENT-EVIDENCE-WRITE-BLOCKED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"
)
BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"
)
REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-RECONCILIATION-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
)

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PostRerunReconciliationRequiredImplementationDepthRecheckTest(unittest.TestCase):
    def test_depth_recheck_records_reconciliation_chain_without_current_evidence_promotion(self):
        patch_result = load_json(PATCH_PATH)
        stage_gate = load_json(STAGE_GATE_PATH)
        depth_report = load_json(DEPTH_REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(depth_report["status"], "PASS_DEPTH_5_POST_RERUN_RECONCILIATION_CHAIN_LIVE_BLOCKING")
        self.assertEqual(stage_gate["stage_gate_status"], "PASS_POST_RERUN_RECONCILIATION_DEPTH_RECHECK_LIVE_BLOCKING")

        self.assertEqual(depth_report["operator_reconciliation_required_count"], 8)
        self.assertEqual(depth_report["unresolved_item_count"], 8)
        self.assertEqual(depth_report["resolved_item_count"], 0)
        self.assertEqual(depth_report["candidate_current_evidence_usable_count"], 0)
        self.assertEqual(depth_report["current_evidence_write_allowed_count"], 0)
        self.assertFalse(depth_report["current_evidence_mutation_allowed"])

    def test_post_rerun_runtime_artifact_chain_remains_fail_closed(self):
        artifact_names = [
            "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json",
            "upbit_paper_post_rerun_reconciliation_repair_path_report.json",
            "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json",
            "upbit_paper_post_rerun_reconciliation_decision_audit_report.json",
            "upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
            "upbit_paper_post_rerun_operator_resolution_audit_report.json",
            "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json",
        ]
        for artifact_name in artifact_names:
            with self.subTest(artifact_name=artifact_name):
                report = load_json(RUNTIME_BASE / artifact_name)
                self.assertFalse(report.get("live_order_ready", False))
                self.assertFalse(report.get("live_order_allowed", False))
                self.assertFalse(report.get("can_live_trade", False))
                self.assertFalse(report.get("scale_up_allowed", False))
                self.assertFalse(report.get("current_evidence_mutation_allowed", False))
                self.assertFalse(report.get("current_ledger_jsonl_write_allowed", False))
                self.assertFalse(report.get("latest_runtime_pointer_write_allowed", False))
                self.assertFalse(report.get("current_evidence_write_allowed", False))
                self.assertEqual(report.get("current_evidence_write_allowed_count", 0), 0)
                self.assertEqual(report.get("candidate_current_evidence_usable_count", 0), 0)

    def test_operator_resolution_and_closure_remain_unresolved(self):
        queue = load_json(RUNTIME_BASE / "upbit_paper_post_rerun_operator_reconciliation_queue_report.json")
        resolution = load_json(RUNTIME_BASE / "upbit_paper_post_rerun_operator_resolution_audit_report.json")
        closure = load_json(RUNTIME_BASE / "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json")

        self.assertEqual(queue["queue_status"], "BLOCKED")
        self.assertEqual(queue["operator_reconciliation_required_count"], 8)
        self.assertEqual(resolution["resolution_audit_status"], "UNRESOLVED_RECONCILIATION_REVIEW_ONLY")
        self.assertTrue(resolution["operator_resolution_required"])
        self.assertEqual(resolution["unresolved_item_count"], 8)
        self.assertEqual(resolution["resolved_item_count"], 0)
        self.assertEqual(closure["closure_status"], "CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED")
        self.assertEqual(closure["current_evidence_closed_count"], 8)
        self.assertEqual(closure["resolved_item_count"], 0)

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

    def test_state_routes_forward_after_post_rerun_depth_recheck(self):
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertIn(GAP_ID, state["open_contract_gap_ids"])
        self.assertIn(GAP_ID, patch_result["remaining_blockers"])
        if (state["last_patch_id"].startswith("MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_BLOCKER_SUMMARY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING_") or state["last_patch_id"].startswith("MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_OPERATOR_HANDOFF_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_SECURITY_QUARANTINE_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_EVIDENCE_PROGRESS_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_MVP5_ENTRY_DURATION_POLICY_") or (state["last_patch_id"].startswith("MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_GAP_ACTION_MAP_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_PAPER_TRUTH_FRESHNESS_SEPARATION_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RUNTIME_CONTINUITY_LADDER_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_AUDITED_WRITER_READINESS_LADDER_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_AUDITED_WRITER_ACTIVATION_PREFLIGHT_") or (state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_OPERATOR_COMPLETION_ACCEPTANCE_VISIBILITY_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_AUDITED_WRITER_BLOCKER_DECISION_") or (state["last_patch_id"].startswith("MVP4_PAPER_SHADOW_ACTIONABILITY_DEFICIT_SUMMARY_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_PAPER_SHADOW_ACTIONABILITY_VISIBILITY_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_RUNTIME_SOURCE_BINDING_VISIBILITY_") or state["last_patch_id"].startswith("MVP4_PAPER_CURRENT_TRUTH_REFRESH_WRITER_"))))))))))):
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
            expected_next_task = "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state[
            "completed_requirement_ids"
        ]:
            expected_next_task = AFTER_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state[
            "completed_requirement_ids"
        ]:
            expected_next_task = AFTER_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state[
            "completed_requirement_ids"
        ]:
            expected_next_task = AFTER_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state[
            "completed_requirement_ids"
        ]:
            expected_next_task = AFTER_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state[
            "completed_requirement_ids"
        ]:
            expected_next_task = AFTER_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state[
            "completed_requirement_ids"
        ]:
            expected_next_task = AFTER_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state[
            "completed_requirement_ids"
        ]:
            self.assertEqual(
                state["next_allowed_task_class"],
                AFTER_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK,
            )
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
