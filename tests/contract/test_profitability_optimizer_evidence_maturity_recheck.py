import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK.patch_result.json"
)
STAGE_GATE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "stage_gates"
    / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK.stage_gate_result.json"
)
ROLLUP_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json"
GAP_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "contract_gaps"
    / "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json"
)
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-RECHECK"
NEXT_TASK = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ProfitabilityOptimizerEvidenceMaturityRecheckContractTest(unittest.TestCase):
    def test_patch_result_refreshes_maturity_evidence_without_live_or_scale(self):
        patch_result = load_json(PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK_20260505_001",
        )
        self.assertEqual(patch_result["task_class"], "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK)
        self.assertIn(REQUIREMENT_ID, patch_result["affected_contract_ids"])
        self.assertIn("PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY", patch_result["remaining_blockers"])
        self.assertIn("ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY", patch_result["remaining_blockers"])

        run_status = {item["validator_id"]: item["status"] for item in patch_result["validators_run"]}
        for validator_id in (
            "profitability_evidence_maturity_rollup_validator",
            "profitability_optimizer_evidence_gap_validator",
            "optimizer_guardrail_validator",
            "convergence_assessment_validator",
            "patch_result_runtime_schema_instance_validator",
            "live_final_guard_validator",
        ):
            self.assertEqual(run_status.get(validator_id), "PASS")

        test_commands = " ".join(item["command"] for item in patch_result["tests_run"])
        if test_commands:
            self.assertIn("test_profitability_optimizer_evidence_maturity_recheck.py", test_commands)
        for field in (
            "live_order_ready_after",
            "live_order_allowed_after",
            "can_live_trade_after",
            "scale_up_allowed_after",
            "optimizer_live_order_allowed_after",
            "convergence_live_order_allowed_after",
        ):
            self.assertFalse(patch_result[field])

    def test_rollup_and_stage_gate_expose_threshold_blockers(self):
        rollup = load_json(ROLLUP_PATH)
        stage_gate = load_json(STAGE_GATE_PATH)
        thresholds = rollup["promotion_threshold_evidence"]

        self.assertEqual(rollup["status"], "BLOCKED_FOR_PROFITABILITY_EVIDENCE_MATURITY")
        self.assertEqual(thresholds["status"], "BLOCKED_FOR_THRESHOLD_EVIDENCE")
        self.assertTrue(thresholds["explicit_insufficient_sample_blocker"])
        self.assertIn("REPLAY_CLOSED_TRADES_BELOW_MIN", thresholds["missing_threshold_codes"])
        self.assertIn("PAPER_RUNTIME_HOURS_BELOW_MIN", thresholds["missing_threshold_codes"])
        self.assertIn("HIGH_OR_CRITICAL_CONTRACT_GAP_OPEN", thresholds["missing_threshold_codes"])
        self.assertEqual(stage_gate["stage_gate_status"], "PASS_THRESHOLD_EXPLICIT_RECHECK_LIVE_BLOCKED")
        self.assertEqual(stage_gate["next_allowed_task_class"], NEXT_TASK)
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(rollup[field])
            self.assertFalse(stage_gate[field])

    def test_state_and_contract_gap_remain_fail_closed(self):
        state = load_json(STATE_PATH)
        gap = load_json(GAP_PATH)

        if (state["last_patch_id"].startswith("MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_BLOCKER_SUMMARY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING_") or state["last_patch_id"].startswith("MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_OPERATOR_HANDOFF_CLARITY_") or state["last_patch_id"].startswith("MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE_") or state["last_patch_id"].startswith("MVP4_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY_")):
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
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertIn("PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY", state["open_contract_gap_ids"])
        self.assertEqual(gap["status"], "OPEN")
        self.assertTrue(gap["live_affecting"])
        self.assertFalse(gap.get("live_order_allowed", False))
        self.assertFalse(gap.get("scale_up_allowed", False))
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])


if __name__ == "__main__":
    unittest.main()
