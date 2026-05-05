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
    / "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK.patch_result.json"
)
COMPLETED_RECONCILIATION_REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-STATE-SYNC-RECHECK"
COMPLETED_WRITE_BLOCKED_REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-CURRENT-EVIDENCE-WRITE-BLOCKED-STATE-SYNC-RECHECK"
COMPLETED_CURRENT_WRITE_BLOCKED_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-POST-RERUN-CURRENT-EVIDENCE-WRITE-BLOCKED-RECHECK"
)
COMPLETED_POST_REPAIR_RECHECK_REQUIREMENT_ID = "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-RECHECK"
COMPLETED_HASH_MISMATCH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK"
)
COMPLETED_BLOCKED_REPAIR_PLAN_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK"
)
COMPLETED_REGENERATED_REPAIR_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-"
    "RECONCILIATION-RECHECK"
)
COMPLETED_STALE_LOOP_REGENERATION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-RECHECK"
)
COMPLETED_STALE_LOOP_REGENERATION_EXECUTION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-RECHECK"
)
COMPLETED_STALE_LOOP_POST_REGENERATION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-RECONCILIATION-AFTER-REGENERATION-REQUIRED-RECHECK"
)
COMPLETED_STALE_LOOP_OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-PENDING-RECHECK"
)
COMPLETED_AUDITED_WRITER_DASHBOARD_BINDING_REQUIREMENT_ID = (
    "REQ-MVP4-UPBIT-PAPER-AUDITED-CURRENT-EVIDENCE-WRITER-DASHBOARD-BINDING"
)
COMPLETED_PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-RECHECK"
)
COMPLETED_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-COLLECTION-DEPTH-RECHECK"
)
COMPLETED_PATCH_RESULT_VALIDATOR_BASELINE_RECONCILIATION_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-BASELINE-RECONCILIATION-RECHECK"
)
COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_REQUIREMENT_ID = "REQ-MVP4-COMPLETED-RECHECK-ROUTE-DEPTH-GUARD"
COMPLETED_OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-OPEN-CONTRACT-GAP-IMPLEMENTATION-PRIORITY-RECHECK"
)
COMPLETED_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-IMPLEMENTATION-DEPTH-RECHECK"
)
BACKWARD_RECONCILIATION_TASK = "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_RECHECK"
BACKWARD_WRITE_BLOCKED_TASK = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
EXPECTED_NEXT_TASK = "MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK"
EXPECTED_POST_REPAIR_NEXT_TASK = "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK"
EXPECTED_HASH_MISMATCH_NEXT_TASK = "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK"
EXPECTED_BLOCKED_REPAIR_PLAN_NEXT_TASK = (
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


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PostRerunCurrentEvidenceWriteBlockedRecheckTest(unittest.TestCase):
    def test_post_rerun_reports_keep_current_evidence_writes_denied(self):
        report_names = [
            "upbit_paper_post_rerun_current_evidence_promotion_guard_report.json",
            "upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
            "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json",
            "upbit_paper_post_rerun_operator_resolution_audit_report.json",
            "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json",
            "upbit_paper_post_rerun_reconciliation_decision_audit_report.json",
            "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json",
        ]
        for name in report_names:
            with self.subTest(name=name):
                report = load_json(RUNTIME_BASE / name)
                self.assertFalse(report["live_order_allowed"])
                self.assertFalse(report["can_live_trade"])
                self.assertFalse(report["scale_up_allowed"])
                self.assertFalse(report.get("current_evidence_write_allowed", False))
                self.assertEqual(report.get("current_evidence_write_allowed_count", 0), 0)
                self.assertEqual(report.get("current_evidence_write_authorized_count", 0), 0)
                self.assertEqual(report.get("candidate_current_evidence_usable_count", 0), 0)
                self.assertIn("POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED", report["blocker_codes"])

    def test_review_ready_candidates_stay_write_blocked(self):
        promotion = load_json(RUNTIME_BASE / "upbit_paper_post_rerun_current_evidence_promotion_guard_report.json")

        self.assertEqual(promotion["promotion_guard_status"], "BLOCKED")
        self.assertGreater(promotion["promotion_review_ready_count"], 0)
        self.assertEqual(promotion["current_evidence_write_allowed_count"], 0)
        self.assertEqual(promotion["candidate_current_evidence_usable_count"], 0)
        for item in promotion["items"]:
            with self.subTest(cycle_id=item["cycle_id"]):
                self.assertTrue(item["promotion_review_ready"])
                self.assertEqual(item["promotion_review_status"], "REVIEW_READY_WRITE_BLOCKED")
                self.assertFalse(item["current_evidence_write_allowed"])
                self.assertFalse(item["candidate_current_evidence_usable"])
                self.assertFalse(item["current_ledger_jsonl_write_allowed"])
                self.assertFalse(item["latest_runtime_pointer_write_allowed"])
                self.assertFalse(item["persistent_loop_mutation_allowed"])
                self.assertFalse(item["live_order_allowed"])
                self.assertFalse(item["scale_up_allowed"])

    def test_recheck_keeps_write_blocked_gap_open_and_routes_to_live_evidence_gap(self):
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK_20260505_001",
        )
        self.assertEqual(patch_result["next_task_class"], EXPECTED_NEXT_TASK)
        if state["last_patch_id"] == patch_result["patch_id"]:
            self.assertEqual(state["next_allowed_task_class"], EXPECTED_NEXT_TASK)
        else:
            self.assertNotEqual(state["next_allowed_task_class"], "")
        self.assertIn("POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED", state["open_contract_gap_ids"])
        self.assertIn("POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED", patch_result["remaining_blockers"])
        self.assertEqual(patch_result["post_rerun_current_evidence_write_allowed_count"], 0)
        self.assertEqual(patch_result["post_rerun_current_evidence_write_authorized_count"], 0)
        self.assertEqual(patch_result["candidate_current_evidence_usable_count"], 0)

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

    def test_completed_post_rerun_state_syncs_do_not_route_backward(self):
        state = load_json(STATE_PATH)
        completed = set(state["completed_requirement_ids"])
        if not {COMPLETED_RECONCILIATION_REQUIREMENT_ID, COMPLETED_WRITE_BLOCKED_REQUIREMENT_ID}.issubset(
            completed
        ):
            self.skipTest("post-rerun state-sync rechecks have not both completed yet")

        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", state["open_contract_gap_ids"])
        self.assertIn("POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED", state["open_contract_gap_ids"])
        completed_route_task_classes = {
            BACKWARD_RECONCILIATION_TASK,
            BACKWARD_WRITE_BLOCKED_TASK,
            EXPECTED_POST_REPAIR_NEXT_TASK,
            EXPECTED_HASH_MISMATCH_NEXT_TASK,
            EXPECTED_BLOCKED_REPAIR_PLAN_NEXT_TASK,
            EXPECTED_REGENERATED_REPAIR_NEXT_TASK,
        }
        if POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            completed_route_task_classes.remove(BACKWARD_WRITE_BLOCKED_TASK)
        self.assertNotIn(state["next_allowed_task_class"], completed_route_task_classes)
        if state["last_patch_id"].startswith("MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK_"):
            expected_next_task = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK_"):
            expected_next_task = "MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK"
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif state["last_patch_id"].startswith("MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK_"):
            self.assertIn(COMPLETED_CURRENT_WRITE_BLOCKED_RECHECK_REQUIREMENT_ID, completed)
            expected_next_task = EXPECTED_NEXT_TASK
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
        elif COMPLETED_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_AFTER_PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
        elif COMPLETED_OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_AFTER_OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK
        elif COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_AFTER_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_NEXT_TASK
        elif COMPLETED_PATCH_RESULT_VALIDATOR_BASELINE_RECONCILIATION_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_AFTER_PATCH_RESULT_BASELINE_RECONCILIATION_NEXT_TASK
        elif COMPLETED_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_AFTER_ACTUAL_LONG_RUN_COLLECTION_DEPTH_RECHECK_NEXT_TASK
        elif COMPLETED_PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_AFTER_PROFITABILITY_MATURITY_RECHECK_NEXT_TASK
        elif COMPLETED_AUDITED_WRITER_DASHBOARD_BINDING_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_AFTER_AUDITED_WRITER_DASHBOARD_BINDING_NEXT_TASK
        elif COMPLETED_STALE_LOOP_OPERATOR_QUEUE_PENDING_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_AUDITED_WRITER_DASHBOARD_BINDING_NEXT_TASK
        elif COMPLETED_STALE_LOOP_POST_REGENERATION_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_STALE_LOOP_OPERATOR_QUEUE_PENDING_NEXT_TASK
        elif COMPLETED_STALE_LOOP_REGENERATION_EXECUTION_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_STALE_LOOP_POST_REGENERATION_NEXT_TASK
        elif COMPLETED_STALE_LOOP_REGENERATION_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_STALE_LOOP_REGENERATION_NEXT_TASK
        elif COMPLETED_REGENERATED_REPAIR_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_REGENERATED_REPAIR_NEXT_TASK
        elif COMPLETED_BLOCKED_REPAIR_PLAN_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_BLOCKED_REPAIR_PLAN_NEXT_TASK
        elif COMPLETED_HASH_MISMATCH_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_HASH_MISMATCH_NEXT_TASK
        elif COMPLETED_POST_REPAIR_RECHECK_REQUIREMENT_ID in completed:
            expected_next_task = EXPECTED_POST_REPAIR_NEXT_TASK
        else:
            expected_next_task = EXPECTED_NEXT_TASK
        self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])

    def test_historical_post_rerun_patch_results_preserve_write_blocked_boundary(self):
        patch_names = [
            "MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD",
            "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE",
            "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE",
            "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT",
            "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP",
            "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_DECISION_AUDIT",
            "MVP4_UPBIT_PAPER_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE",
        ]
        for patch_name in patch_names:
            with self.subTest(patch_name=patch_name):
                patch_result = load_json(
                    ROOT / "system" / "evidence" / "patch_results" / f"{patch_name}.patch_result.json"
                )
                self.assertFalse(patch_result["live_order_ready_after"])
                self.assertFalse(patch_result["live_order_allowed_after"])
                self.assertFalse(patch_result["can_live_trade_after"])
                self.assertFalse(patch_result["scale_up_allowed_after"])
                self.assertEqual(patch_result.get("post_rerun_current_evidence_write_allowed_count", 0), 0)
                self.assertEqual(patch_result.get("candidate_current_evidence_usable_count", 0), 0)
                self.assertIn("POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED", patch_result["remaining_blockers"])


if __name__ == "__main__":
    unittest.main()
