import json
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import run_fixture_file, run_validators


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK.patch_result.json"
)
STAGE_GATE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "stage_gates"
    / "MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK.stage_gate_result.json"
)
CONTRACT_GAP_PATH = ROOT / "system" / "evidence" / "contract_gaps" / "SCALE_UP_NOT_ELIGIBLE.contract_gap.json"
REQUIREMENT_ID = "REQ-MVP4-SCALE-UP-NOT-ELIGIBLE-RECHECK"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-LIVE-ENABLING-EVIDENCE-MISSING-RECHECK"
NEXT_TASK_CLASS = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
RISK_SCALE_VALIDATORS = [
    "risk_scaling_decision_validator",
    "live_burn_in_feedback_validator",
    "paper_live_parity_validator",
    "execution_quality_measurement_validator",
    "survival_layer_validator",
]
GUARDRAIL_VALIDATORS = [
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "scale_up_eligibility_validator",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ScaleUpNotEligibleRecheckTest(unittest.TestCase):
    def test_scaleup_validators_remain_fail_closed_without_live_evidence(self):
        results = run_validators(RISK_SCALE_VALIDATORS + GUARDRAIL_VALIDATORS)
        statuses = {result["validator_id"]: result["status"] for result in results}
        blockers = {
            result["validator_id"]: [blocker["code"] for blocker in result.get("blockers", [])]
            for result in results
        }

        self.assertEqual(statuses["risk_scaling_decision_validator"], "BLOCKED")
        self.assertEqual(statuses["live_burn_in_feedback_validator"], "BLOCKED")
        self.assertEqual(statuses["paper_live_parity_validator"], "BLOCKED")
        self.assertEqual(statuses["execution_quality_measurement_validator"], "BLOCKED")
        self.assertEqual(statuses["survival_layer_validator"], "BLOCKED")
        self.assertEqual(statuses["scale_up_eligibility_validator"], "BLOCKED")
        self.assertEqual(statuses["optimizer_no_live_mutation_validator"], "PASS")
        self.assertEqual(statuses["optimizer_guardrail_validator"], "PASS")
        self.assertEqual(statuses["convergence_assessment_validator"], "PASS")
        self.assertEqual(blockers["scale_up_eligibility_validator"], ["SCALE_UP_NOT_ELIGIBLE"])
        self.assertEqual(blockers["risk_scaling_decision_validator"], ["RISK_SCALING_UNTESTED"])
        self.assertEqual(blockers["live_burn_in_feedback_validator"], ["LIVE_BURN_IN_FEEDBACK_MISSING"])
        self.assertEqual(blockers["paper_live_parity_validator"], ["READ_ONLY_BURN_IN_MISSING"])
        self.assertEqual(blockers["execution_quality_measurement_validator"], ["EXECUTION_QUALITY_UNTESTED"])
        self.assertEqual(blockers["survival_layer_validator"], ["SURVIVAL_LAYER_BLOCKED"])

    def test_scaleup_recheck_keeps_contract_gap_open_and_routes_to_priority(self):
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        stage_gate = load_json(STAGE_GATE_PATH)
        contract_gap = load_json(CONTRACT_GAP_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK_20260505_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        if state["last_patch_id"] == patch_result["patch_id"]:
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        else:
            self.assertNotEqual(state["next_allowed_task_class"], "")
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertIn(PREVIOUS_REQUIREMENT_ID, state["completed_requirement_ids"])

        self.assertIn("SCALE_UP_NOT_ELIGIBLE", state["open_contract_gap_ids"])
        self.assertIn("SCALE_UP_NOT_ELIGIBLE", patch_result["remaining_blockers"])
        self.assertIn("LIVE_ENABLING_EVIDENCE_MISSING", patch_result["remaining_blockers"])
        self.assertEqual(contract_gap["contract_gap_id"], "SCALE_UP_NOT_ELIGIBLE")
        self.assertEqual(contract_gap["status"], "OPEN")
        self.assertTrue(contract_gap["live_affecting"])
        self.assertEqual(stage_gate["scale_up_eligibility_status"], "BLOCKED")
        self.assertEqual(stage_gate["scale_up_primary_blocker_code"], "SCALE_UP_NOT_ELIGIBLE")
        self.assertEqual(stage_gate["risk_scaling_decision_status"], "BLOCKED")
        self.assertEqual(stage_gate["risk_scaling_primary_blocker_code"], "RISK_SCALING_UNTESTED")
        self.assertGreaterEqual(stage_gate["blocked_scale_validator_count"], 6)
        self.assertEqual(stage_gate["usable_for_live_enabling_count"], 0)

        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])
            self.assertFalse(stage_gate[field])
        for field in (
            "live_order_ready_after",
            "live_order_allowed_after",
            "can_live_trade_after",
            "scale_up_allowed_after",
            "convergence_live_order_allowed_after",
            "optimizer_live_order_allowed_after",
        ):
            self.assertFalse(patch_result[field])

    def test_scaleup_fixture_outcomes_remain_pass_fail_blocked(self):
        fixture_dir = ROOT / "tests" / "validators" / "fixtures"
        expected = {
            "convergence_risk_scale_pass.json": "PASS",
            "convergence_risk_scale_fail.json": "FAIL",
            "convergence_risk_scale_blocked.json": "BLOCKED",
            "convergence_scaleup_safety_pass.json": "PASS",
            "convergence_scaleup_safety_fail.json": "FAIL",
            "convergence_scaleup_safety_blocked.json": "BLOCKED",
        }
        for filename, expected_status in expected.items():
            with self.subTest(filename=filename):
                result = run_fixture_file(fixture_dir / filename)
                self.assertEqual(result["status"], expected_status)
                if expected_status != "PASS":
                    self.assertTrue(result["blocking"])


if __name__ == "__main__":
    unittest.main()
