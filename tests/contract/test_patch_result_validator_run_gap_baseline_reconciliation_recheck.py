import copy
import json
import unittest
from pathlib import Path

from tools.emit_patch_result_validator_run_gap_baseline_reconciliation_recheck_patch_evidence import (
    PATCH_ID,
    build_reconciliation_report,
    gap_key,
)
from tools.emit_root_launcher_operator_visibility_patch_evidence import sha256_json
from tools.emit_patch_result_runtime_schema_validation_patch_evidence import current_gap_rows


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE.json"
AUDIT_PATH = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json"
CONTRACT_GAP_PATH = ROOT / "system" / "evidence" / "contract_gaps" / "PATCH_RESULT_VALIDATOR_RUN_GAP.contract_gap.json"
RECONCILIATION_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION.json"
)
PATCH_RESULT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK.patch_result.json"
)
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
REQUIREMENT_ID = "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-BASELINE-RECONCILIATION-RECHECK"
NEXT_TASK_CLASS = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
ROUTE_DEPTH_GUARD_REQUIREMENT_ID = "REQ-MVP4-COMPLETED-RECHECK-ROUTE-DEPTH-GUARD"
ROUTE_DEPTH_GUARD_PATCH_ID = "MVP4_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_20260504_001"
ROUTE_DEPTH_GUARD_NEXT_TASK_CLASS = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID = "REQ-MVP4-OPEN-CONTRACT-GAP-IMPLEMENTATION-PRIORITY-RECHECK"
OPEN_GAP_PRIORITY_RECHECK_PATCH_ID = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK_20260504_001"
OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK_CLASS = (
    "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK"
)
PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-IMPLEMENTATION-DEPTH-RECHECK"
)
PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_PATCH_ID = (
    "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK_20260504_001"
)
PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK_CLASS = (
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


class PatchResultValidatorRunGapBaselineReconciliationRecheckTest(unittest.TestCase):
    def test_reconciliation_report_matches_current_baseline_audit_and_contract_gap(self):
        report = load_json(RECONCILIATION_PATH)
        baseline = load_json(BASELINE_PATH)
        audit = load_json(AUDIT_PATH)
        contract_gap = load_json(CONTRACT_GAP_PATH)
        current_gaps = current_gap_rows()

        baseline_keys = sorted(gap_key(item) for item in baseline["gaps"])
        audit_keys = sorted(gap_key(item) for item in audit["gaps"])
        current_keys = sorted(gap_key(item) for item in current_gaps)

        self.assertEqual(report["status"], "PASS_BASELINE_RECONCILED_HISTORICAL_GAP_REMAINS_LIVE_BLOCKING")
        self.assertEqual(report["patch_id"], PATCH_ID)
        self.assertEqual(report["baseline_gap_count"], 9)
        self.assertEqual(report["baseline_gap_count"], len(baseline_keys))
        self.assertEqual(report["current_gap_count"], len(current_keys))
        self.assertEqual(report["audit_gap_count"], len(audit_keys))
        self.assertEqual(report["unbaselined_gap_count"], 0)
        self.assertEqual(baseline_keys, current_keys)
        self.assertEqual(audit_keys, current_keys)
        self.assertEqual(report["baseline_gap_key_hash"], sha256_json(baseline_keys))
        self.assertEqual(report["current_gap_key_hash"], sha256_json(current_keys))
        self.assertEqual(report["audit_gap_key_hash"], sha256_json(audit_keys))
        self.assertEqual(report["contract_gap_status"], "OPEN")
        self.assertTrue(report["contract_gap_live_affecting"])
        self.assertEqual(contract_gap["status"], "OPEN")
        self.assertTrue(contract_gap["live_affecting"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(audit[field])

    def test_reconciliation_builder_blocks_missing_baseline_gap(self):
        baseline = load_json(BASELINE_PATH)
        audit = load_json(AUDIT_PATH)
        contract_gap = load_json(CONTRACT_GAP_PATH)
        current_gaps = current_gap_rows()
        tampered = copy.deepcopy(baseline)
        tampered["gaps"] = tampered["gaps"][:-1]
        tampered["baseline_gap_count"] = len(tampered["gaps"])
        tampered["baseline_gap_keys"] = [gap_key(item) for item in tampered["gaps"]]
        tampered["baseline_hash"] = sha256_json({key: value for key, value in tampered.items() if key != "baseline_hash"})

        report = build_reconciliation_report(
            "2026-05-04T00:00:00Z",
            baseline["authority"]["trader1_sha256"],
            baseline["authority"]["agents_sha256"],
            current_gaps,
            tampered,
            audit,
            contract_gap,
        )

        self.assertEqual(report["status"], "BLOCKED_BASELINE_RECONCILIATION_DRIFT")
        self.assertEqual(report["missing_from_baseline_count"], 1)
        self.assertFalse(report["checks"]["baseline_matches_current"])

    def test_patch_result_and_state_advance_without_resolving_live_blocker(self):
        patch_result = load_json(PATCH_RESULT_PATH)
        state = load_json(STATE_PATH)

        self.assertEqual(patch_result["patch_id"], PATCH_ID)
        self.assertIn(REQUIREMENT_ID, patch_result["affected_contract_ids"])
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        if state["last_patch_id"].startswith("MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK_"):
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
        elif STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            expected_next_task = AFTER_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK
            self.assertEqual(state["next_allowed_task_class"], expected_next_task)
        elif PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["last_patch_id"], PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_PATCH_ID)
            self.assertEqual(state["next_allowed_task_class"], PAPER_SHADOW_IMPLEMENTATION_DEPTH_RECHECK_NEXT_TASK_CLASS)
        elif OPEN_GAP_PRIORITY_RECHECK_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["last_patch_id"], OPEN_GAP_PRIORITY_RECHECK_PATCH_ID)
            self.assertEqual(state["next_allowed_task_class"], OPEN_GAP_PRIORITY_RECHECK_NEXT_TASK_CLASS)
        elif ROUTE_DEPTH_GUARD_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["last_patch_id"], ROUTE_DEPTH_GUARD_PATCH_ID)
            self.assertEqual(state["next_allowed_task_class"], ROUTE_DEPTH_GUARD_NEXT_TASK_CLASS)
        else:
            self.assertEqual(state["last_patch_id"], PATCH_ID)
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertIn("PATCH_RESULT_VALIDATOR_RUN_GAP", state["open_contract_gap_ids"])
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
