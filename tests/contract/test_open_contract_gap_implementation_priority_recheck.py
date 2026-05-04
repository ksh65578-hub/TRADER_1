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
    / "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK.patch_result.json"
)
STAGE_GATE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "stage_gates"
    / "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK.stage_gate_result.json"
)
PAPER_SHADOW_GAP_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "contract_gaps"
    / "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP.contract_gap.json"
)
REQUIREMENT_ID = "REQ-MVP4-OPEN-CONTRACT-GAP-IMPLEMENTATION-PRIORITY-RECHECK"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-COMPLETED-RECHECK-ROUTE-DEPTH-GUARD"
NEXT_TASK_CLASS = "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK"
SELECTED_GAP_ID = "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP"
DOWNSTREAM_REQUIREMENT_ID = (
    "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-IMPLEMENTATION-DEPTH-RECHECK"
)
DOWNSTREAM_PATCH_ID = (
    "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK_20260504_001"
)
DOWNSTREAM_NEXT_TASK_CLASS = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class OpenContractGapImplementationPriorityRecheckTest(unittest.TestCase):
    def test_priority_recheck_selects_non_live_paper_shadow_depth_task(self):
        if not PATCH_PATH.exists():
            self.skipTest("open contract gap priority recheck patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        stage_gate = load_json(STAGE_GATE_PATH)
        paper_shadow_gap = load_json(PAPER_SHADOW_GAP_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK_20260504_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        if DOWNSTREAM_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["last_patch_id"], DOWNSTREAM_PATCH_ID)
            self.assertEqual(state["next_allowed_task_class"], DOWNSTREAM_NEXT_TASK_CLASS)
        else:
            self.assertEqual(state["last_patch_id"], "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK_20260504_001")
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertIn(PREVIOUS_REQUIREMENT_ID, state["completed_requirement_ids"])

        self.assertEqual(stage_gate["selected_gap_id"], SELECTED_GAP_ID)
        self.assertEqual(stage_gate["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertGreater(stage_gate["implementable_non_live_candidate_count"], 0)
        self.assertGreater(stage_gate["operator_or_policy_blocked_gap_count"], 0)
        self.assertEqual(paper_shadow_gap["status"], "OPEN")
        self.assertTrue(paper_shadow_gap["live_affecting"])

        for gap_id in (
            SELECTED_GAP_ID,
            "PATCH_RESULT_VALIDATOR_RUN_GAP",
            "POST_REPAIR_RECONCILIATION_REQUIRED",
            "LIVE_ENABLING_EVIDENCE_MISSING",
            "SCALE_UP_NOT_ELIGIBLE",
        ):
            self.assertIn(gap_id, state["open_contract_gap_ids"])
            self.assertIn(gap_id, patch_result["remaining_blockers"])

    def test_priority_recheck_keeps_live_and_scale_flags_false(self):
        patch_result = load_json(PATCH_PATH)
        state = load_json(STATE_PATH)

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
