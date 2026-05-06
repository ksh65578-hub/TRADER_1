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
    / "MVP4_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.patch_result.json"
)
PLAN_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_stale_loop_regeneration_plan.json"
)
STAGE_GATE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "stage_gates"
    / "MVP4_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.stage_gate_result.json"
)
DEPTH_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.json"
)
CONTRACT_GAP_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "contract_gaps"
    / "STALE_LOOP_REGENERATION_REQUIRED.contract_gap.json"
)
REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
EXECUTION_RECHECK_REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-RECHECK"
EXECUTION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
POST_REGENERATION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-RECONCILIATION-AFTER-REGENERATION-REQUIRED-RECHECK"
)
OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-PENDING-RECHECK"
)
DASHBOARD_BINDING_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-AUDITED-CURRENT-EVIDENCE-WRITER-DASHBOARD-BINDING"
PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-RECHECK"
ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-COLLECTION-DEPTH-RECHECK"
)
PATCH_RESULT_VALIDATOR_BASELINE_RECONCILIATION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-BASELINE-RECONCILIATION-RECHECK"
)
COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_REQUIREMENT_ID = "REQ-MVP4-COMPLETED-RECHECK-ROUTE-DEPTH-GUARD"
COMPLETED_OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-OPEN-CONTRACT-GAP-IMPLEMENTATION-PRIORITY-RECHECK"
)
PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-IMPLEMENTATION-DEPTH-RECHECK"
)
NEXT_TASK = "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
AFTER_EXECUTION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
)
POST_REGENERATION_NEXT_TASK = "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
OPERATOR_QUEUE_PENDING_NEXT_TASK = "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK"
AUDITED_WRITER_DASHBOARD_NEXT_TASK = "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
AFTER_AUDITED_WRITER_DASHBOARD_NEXT_TASK = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
)
AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK = (
    "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK"
)
AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK"
)
PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK"
)
ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK"
)
PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
)
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
MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
BLOCKER = "STALE_LOOP_REGENERATION_REQUIRED"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class StaleLoopRegenerationRequiredImplementationDepthRecheckTest(unittest.TestCase):
    def test_regeneration_plan_remains_ready_but_non_executing(self):
        plan = load_json(PLAN_PATH)

        self.assertEqual(plan["plan_status"], "READY_FOR_SAFE_PAPER_REGENERATION")
        self.assertIsNone(plan["primary_blocker_code"])
        self.assertEqual(plan["source_loop_report_count"], 17)
        self.assertEqual(plan["source_current_accepted_count"], 1)
        self.assertEqual(plan["source_excluded_count"], 16)
        self.assertEqual(plan["legacy_schema_drift_count"], 16)
        self.assertEqual(plan["regeneration_item_count"], 16)
        self.assertEqual(plan["operator_review_item_count"], 0)
        self.assertEqual(plan["duplicate_replacement_path_count"], 0)
        self.assertEqual(plan["overwrite_or_delete_count"], 0)
        self.assertFalse(plan["automatic_regeneration_allowed"])
        self.assertFalse(plan["operator_confirmation_required_before_execution"])
        self.assertFalse(plan["delete_source_allowed"])
        self.assertFalse(plan["overwrite_source_allowed"])
        self.assertFalse(plan["actual_regeneration_performed"])
        self.assertFalse(plan["actual_long_run_evidence_created"])
        self.assertFalse(plan["long_run_evidence_eligible"])
        self.assertFalse(plan["promotion_eligible"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(plan[field])

    def test_regeneration_items_are_source_preserving_paper_replacements(self):
        plan = load_json(PLAN_PATH)
        replacement_paths = []

        for item in plan["items"]:
            self.assertEqual(item["source_classification"], "LEGACY_SCHEMA_DRIFT")
            self.assertFalse(item["source_evidence_usable_current"])
            self.assertEqual(item["planned_action"], "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT")
            self.assertIn("regenerated-current-schema", item["planned_replacement_path"])
            self.assertNotEqual(item["planned_replacement_path"], item["source_path"])
            self.assertTrue(
                item["planned_replacement_path"].startswith(
                    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/"
                )
            )
            self.assertFalse(item["overwrite_source_allowed"])
            self.assertFalse(item["delete_source_allowed"])
            self.assertFalse(item["automatic_live_or_order_allowed"])
            self.assertFalse(item["requires_operator_review"])
            self.assertFalse(item["live_order_ready"])
            self.assertFalse(item["live_order_allowed"])
            self.assertFalse(item["can_live_trade"])
            self.assertFalse(item["scale_up_allowed"])
            replacement_paths.append(item["planned_replacement_path"])

        self.assertEqual(len(replacement_paths), len(set(replacement_paths)))

    def test_recheck_patch_routes_to_execution_required_without_live_or_scale_permission(self):
        if not PATCH_PATH.exists():
            self.skipTest("stale loop regeneration required implementation depth recheck patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        stage_gate = load_json(STAGE_GATE_PATH)
        depth_report = load_json(DEPTH_REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK)
        self.assertEqual(
            stage_gate["stage_gate_status"],
            "PASS_DEPTH_5_STALE_LOOP_REGENERATION_REQUIRED_EXECUTION_BLOCKED",
        )
        self.assertEqual(depth_report["status"], "PASS_DEPTH_5_STALE_LOOP_REGENERATION_REQUIRED_EXECUTION_BLOCKED")
        self.assertEqual(depth_report["contract_gap_id"], BLOCKER)
        self.assertEqual(depth_report["execution_blocker_code"], "STALE_LOOP_REGENERATION_EXECUTION_REQUIRED")
        self.assertIn(BLOCKER, patch_result["remaining_blockers"])
        self.assertIn("STALE_LOOP_REGENERATION_EXECUTION_REQUIRED", patch_result["remaining_blockers"])
        self.assertEqual(patch_result["stale_loop_regeneration_plan_status"], "READY_FOR_SAFE_PAPER_REGENERATION")
        self.assertEqual(patch_result["stale_loop_regeneration_item_count"], 16)
        self.assertEqual(patch_result["stale_loop_regeneration_operator_review_item_count"], 0)
        self.assertEqual(patch_result["stale_loop_regeneration_duplicate_replacement_path_count"], 0)
        self.assertEqual(patch_result["stale_loop_regeneration_overwrite_or_delete_count"], 0)
        self.assertFalse(patch_result["stale_loop_regeneration_actual_regeneration_performed"])
        self.assertFalse(patch_result["stale_loop_regeneration_automatic_regeneration_allowed"])
        self.assertFalse(patch_result["stale_loop_regeneration_delete_source_allowed"])
        self.assertFalse(patch_result["stale_loop_regeneration_overwrite_source_allowed"])

        completed = set(state["completed_requirement_ids"])
        if (state["last_patch_id"].startswith("MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_BLOCKER_SUMMARY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING_") or state["last_patch_id"].startswith("MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_OPERATOR_HANDOFF_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_SECURITY_QUARANTINE_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_EVIDENCE_PROGRESS_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_MVP5_ENTRY_DURATION_POLICY_") or (state["last_patch_id"].startswith("MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_GAP_ACTION_MAP_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_PAPER_TRUTH_FRESHNESS_SEPARATION_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RUNTIME_CONTINUITY_LADDER_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_AUDITED_WRITER_READINESS_LADDER_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_AUDITED_WRITER_ACTIVATION_PREFLIGHT_") or (state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_OPERATOR_COMPLETION_ACCEPTANCE_VISIBILITY_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_AUDITED_WRITER_BLOCKER_DECISION_") or (state["last_patch_id"].startswith("MVP4_PAPER_SHADOW_ACTIONABILITY_DEFICIT_SUMMARY_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_PAPER_SHADOW_ACTIONABILITY_VISIBILITY_") or (state["last_patch_id"].startswith("MVP4_DASHBOARD_RUNTIME_SOURCE_BINDING_VISIBILITY_") or (state["last_patch_id"].startswith("MVP4_PAPER_CURRENT_TRUTH_REFRESH_WRITER_") or state["last_patch_id"].startswith("MVP4_RUNTIME_TRUTH_MARKET_CONTINUITY_REPAIR_")))))))))))):
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
        elif EXECUTION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_EXECUTION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK)
        elif REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK)
        elif REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK)
        elif COMPLETED_OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK)
        elif COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK)
        elif PATCH_RESULT_VALIDATOR_BASELINE_RECONCILIATION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK)
        elif ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK)
        elif PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK)
        elif DASHBOARD_BINDING_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AFTER_AUDITED_WRITER_DASHBOARD_NEXT_TASK)
        elif OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], AUDITED_WRITER_DASHBOARD_NEXT_TASK)
        elif POST_REGENERATION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], OPERATOR_QUEUE_PENDING_NEXT_TASK)
        elif EXECUTION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], POST_REGENERATION_NEXT_TASK)
        if EXECUTION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            self.assertNotIn(BLOCKER, state["open_contract_gap_ids"])
            self.assertNotIn("STALE_LOOP_REGENERATION_EXECUTION_REQUIRED", state["open_contract_gap_ids"])
        elif REQUIREMENT_ID in completed:
            self.assertIn(BLOCKER, state["open_contract_gap_ids"])
            self.assertIn("STALE_LOOP_REGENERATION_EXECUTION_REQUIRED", state["open_contract_gap_ids"])
        elif REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            self.assertIn(BLOCKER, state["open_contract_gap_ids"])
            self.assertIn("STALE_LOOP_REGENERATION_EXECUTION_REQUIRED", state["open_contract_gap_ids"])
        elif EXECUTION_RECHECK_REQUIREMENT_ID in completed:
            self.assertNotIn(BLOCKER, state["open_contract_gap_ids"])
            self.assertNotIn("STALE_LOOP_REGENERATION_EXECUTION_REQUIRED", state["open_contract_gap_ids"])
        else:
            self.assertIn(BLOCKER, state["open_contract_gap_ids"])
        for field in (
            "live_order_ready_after",
            "live_order_allowed_after",
            "can_live_trade_after",
            "scale_up_allowed_after",
            "convergence_live_order_allowed_after",
            "optimizer_live_order_allowed_after",
        ):
            self.assertFalse(patch_result[field])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])

    def test_contract_gap_projection_remains_open_and_live_affecting(self):
        gap = load_json(CONTRACT_GAP_PATH)

        self.assertEqual(gap["schema_id"], "trader1.contract_gap.v1")
        self.assertEqual(gap["contract_gap_id"], BLOCKER)
        state = load_json(STATE_PATH)
        if EXECUTION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(gap["status"], "RESOLVED")
        else:
            self.assertEqual(gap["status"], "OPEN")
        self.assertEqual(gap["severity"], "HIGH")
        self.assertTrue(gap["live_affecting"])
        self.assertEqual(gap["exchange"], "UPBIT")
        self.assertEqual(gap["market_type"], "KRW_SPOT")
        self.assertEqual(gap["mode"], "PAPER")


if __name__ == "__main__":
    unittest.main()
