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
    / "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK.patch_result.json"
)
POST_REPAIR_REPORT_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_post_repair_reconciliation_report.json"
)
REPAIR_QUEUE_REPORT_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_repair_operator_queue_report.json"
)
REQUIREMENT_ID = "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK"
BLOCKED_REPAIR_PLAN_REQUIREMENT_ID = "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK"
REGENERATED_REPAIR_REQUIREMENT_ID = (
    "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-"
    "RECONCILIATION-RECHECK"
)
STALE_LOOP_REGENERATION_REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-RECHECK"
STALE_LOOP_EXECUTION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-RECHECK"
)
STALE_LOOP_POST_REGENERATION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-RECONCILIATION-AFTER-REGENERATION-REQUIRED-RECHECK"
)
STALE_LOOP_OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID = (
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
BLOCKER = "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED"
EXPECTED_NEXT_TASK = "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK"
EXPECTED_BLOCKED_REPAIR_NEXT_TASK = (
    "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_RECHECK"
)
EXPECTED_REGENERATED_REPAIR_NEXT_TASK = "MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK"
EXPECTED_STALE_LOOP_REGENERATION_NEXT_TASK = "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK"
EXPECTED_STALE_LOOP_POST_REGENERATION_NEXT_TASK = (
    "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
)
EXPECTED_STALE_LOOP_OPERATOR_QUEUE_PENDING_NEXT_TASK = (
    "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK"
)
EXPECTED_AUDITED_WRITER_DASHBOARD_BINDING_NEXT_TASK = (
    "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
)
EXPECTED_AFTER_AUDITED_WRITER_DASHBOARD_BINDING_NEXT_TASK = (
    "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
)
EXPECTED_AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK = (
    "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
)
EXPECTED_AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
)
EXPECTED_AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK = (
    "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK"
)
EXPECTED_AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK = (
    "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
)
EXPECTED_AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK = (
    "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK"
)
EXPECTED_AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
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
MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
AFTER_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK = (
    "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
)
def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class RepairCandidateHashMismatchReconciliationRequiredRecheckTest(unittest.TestCase):
    def test_post_repair_item_exposes_missing_source_expected_rollup_artifact(self):
        report = load_json(POST_REPAIR_REPORT_PATH)

        self.assertEqual(report["post_repair_reconciliation_status"], "BLOCKED")
        self.assertEqual(report["source_loop_expected_rollup_hash_mismatch_count"], 1)
        self.assertEqual(report["hash_reconciliation_operator_action_required_count"], 1)
        self.assertEqual(report["candidate_current_evidence_usable_count"], 0)
        self.assertIn(BLOCKER, report["blocker_codes"])

        item = report["items"][0]
        self.assertEqual(item["item_blocker_code"], BLOCKER)
        self.assertEqual(item["candidate_classification"], "REPAIR_CANDIDATE_BLOCKED_HASH_MISMATCH")
        self.assertEqual(item["hash_reconciliation_status"], "SOURCE_EXPECTED_ROLLUP_ARTIFACT_MISSING")
        self.assertEqual(item["hash_reconciliation_blocker_code"], BLOCKER)
        self.assertTrue(item["hash_reconciliation_requires_operator_action"])
        self.assertFalse(item["source_loop_expected_rollup_artifact_exists"])
        self.assertEqual(item["source_loop_expected_rollup_artifact_load_status"], "MISSING")
        self.assertFalse(item["source_loop_expected_rollup_hash_match"])
        self.assertIsNone(item["source_loop_expected_rollup_recomputed_hash"])
        self.assertEqual(item["candidate_rollup_hash_self_check"], "PASS")
        self.assertEqual(item["candidate_rollup_recomputed_hash"], item["candidate_rollup_hash"])
        self.assertFalse(item["candidate_current_evidence_usable"])
        self.assertFalse(item["current_evidence_mutation_allowed"])

    def test_repair_operator_queue_keeps_hash_mismatch_review_only(self):
        queue = load_json(REPAIR_QUEUE_REPORT_PATH)

        self.assertEqual(queue["queue_status"], "BLOCKED")
        self.assertEqual(queue["hash_operator_reconciliation_required_count"], 1)
        self.assertEqual(queue["candidate_current_evidence_usable_count"], 0)
        self.assertFalse(queue["current_evidence_mutation_allowed"])
        self.assertFalse(queue["persistent_loop_mutation_allowed"])
        self.assertFalse(queue["source_delete_allowed"])

        item = next(item for item in queue["items"] if item.get("post_repair_item_blocker_code") == BLOCKER)
        self.assertEqual(item["safe_repair_lane"], "LEDGER_ROLLUP_REBUILD_READY")
        self.assertTrue(item["ready_for_operator_ledger_candidate_review"])
        self.assertTrue(item["requires_hash_operator_reconciliation"])
        self.assertFalse(item["requires_runtime_cycle_rerun"])
        self.assertFalse(item["requires_recovery_guard_rerun"])
        self.assertFalse(item["candidate_current_evidence_usable"])
        self.assertFalse(item["current_evidence_mutation_allowed"])
        self.assertFalse(item["persistent_loop_mutation_allowed"])
        self.assertFalse(item["source_delete_allowed"])
        self.assertFalse(item["live_permission_created"])
        self.assertIn(BLOCKER, item["blocking_codes"])

    def test_recheck_patch_advances_without_resolving_hash_mismatch_gap(self):
        if not PATCH_PATH.exists():
            self.skipTest("hash mismatch recheck patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK_20260504_001",
        )
        self.assertEqual(patch_result["next_task_class"], EXPECTED_NEXT_TASK)
        self.assertIn(BLOCKER, patch_result["remaining_blockers"])
        self.assertIn("POST_REPAIR_RECONCILIATION_REQUIRED", patch_result["remaining_blockers"])
        self.assertEqual(patch_result["post_repair_reconciliation_status"], "BLOCKED")
        self.assertEqual(patch_result["post_repair_source_loop_expected_rollup_hash_mismatch_count"], 1)
        self.assertEqual(patch_result["repair_operator_queue_status"], "BLOCKED")
        self.assertEqual(patch_result["repair_operator_queue_ledger_candidate_review_ready_count"], 1)
        self.assertEqual(patch_result["repair_operator_queue_candidate_current_evidence_usable_count"], 0)

        completed = set(state["completed_requirement_ids"])
        if (state["last_patch_id"].startswith("MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_BLOCKER_SUMMARY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING_") or state["last_patch_id"].startswith("MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_OPERATOR_HANDOFF_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE_")):
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
        elif STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = AFTER_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
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
            self.assertEqual(
                state["next_allowed_task_class"],
                EXPECTED_AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK,
            )
        elif COMPLETED_OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(
                state["next_allowed_task_class"],
                EXPECTED_AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK,
            )
        elif COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_REQUIREMENT_ID in completed:
            self.assertEqual(
                state["next_allowed_task_class"],
                EXPECTED_AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK,
            )
        elif PATCH_RESULT_VALIDATOR_BASELINE_RECONCILIATION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(
                state["next_allowed_task_class"],
                EXPECTED_AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK,
            )
        elif ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK)
        elif PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK)
        elif DASHBOARD_BINDING_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_AFTER_AUDITED_WRITER_DASHBOARD_BINDING_NEXT_TASK)
        elif STALE_LOOP_OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_AUDITED_WRITER_DASHBOARD_BINDING_NEXT_TASK)
        elif STALE_LOOP_POST_REGENERATION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_STALE_LOOP_OPERATOR_QUEUE_PENDING_NEXT_TASK)
        elif STALE_LOOP_EXECUTION_RECHECK_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_STALE_LOOP_POST_REGENERATION_NEXT_TASK)
        elif STALE_LOOP_REGENERATION_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_STALE_LOOP_REGENERATION_NEXT_TASK)
        elif REGENERATED_REPAIR_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_REGENERATED_REPAIR_NEXT_TASK)
        elif BLOCKED_REPAIR_PLAN_REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_BLOCKED_REPAIR_NEXT_TASK)
        elif REQUIREMENT_ID in completed:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_NEXT_TASK)
        self.assertIn(BLOCKER, state["open_contract_gap_ids"])
        self.assertIn("POST_REPAIR_RECONCILIATION_REQUIRED", state["open_contract_gap_ids"])

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


if __name__ == "__main__":
    unittest.main()
