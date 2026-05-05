import json
import unittest
from pathlib import Path

from trader1.execution.live_order_gateway import evaluate_live_order_path
from trader1.safety.live_order_gate import REQUIRED_LIVE_TRUE_FIELDS, evaluate_live_order_gate


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK.patch_result.json"
)
STAGE_GATE_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "stage_gates"
    / "MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK.stage_gate_result.json"
)
CONTRACT_GAP_PATH = ROOT / "system" / "evidence" / "contract_gaps" / "LIVE_ENABLING_EVIDENCE_MISSING.contract_gap.json"
EXTERNAL_BLOCKER_MANIFEST_PATH = ROOT / "system" / "evidence" / "MVP4_EXTERNAL_BLOCKER.evidence_manifest.json"
REQUIREMENT_ID = "REQ-MVP4-LIVE-ENABLING-EVIDENCE-MISSING-RECHECK"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-CURRENT-EVIDENCE-WRITE-BLOCKED-RECHECK"
NEXT_TASK_CLASS = "MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class LiveEnablingEvidenceMissingRecheckTest(unittest.TestCase):
    def test_external_live_review_inputs_are_not_usable_for_live_enabling(self):
        manifest = load_json(EXTERNAL_BLOCKER_MANIFEST_PATH)

        self.assertIn("LIVE_ENABLING_EVIDENCE_MISSING", manifest["known_blockers"])
        self.assertGreater(len(manifest["external_review_input_statuses"]), 0)
        for item in manifest["external_review_input_statuses"]:
            with self.subTest(artifact_path=item["artifact_path"]):
                self.assertFalse(item["usable_for_live_enabling"])
                self.assertFalse(item["live_order_ready"])
                self.assertFalse(item["live_order_allowed"])
                self.assertFalse(item["can_live_trade"])

    def test_spoofed_all_green_live_inputs_still_block_before_adapter(self):
        live_gate = {field: True for field in REQUIRED_LIVE_TRUE_FIELDS}
        live_gate.update(
            {
                "live_order_ready": True,
                "live_order_allowed": True,
                "can_live_trade": True,
                "live_enabling_patch_valid": True,
            }
        )

        gate_decision = evaluate_live_order_gate(live_gate)
        self.assertFalse(gate_decision.live_order_ready)
        self.assertFalse(gate_decision.live_order_allowed)
        self.assertFalse(gate_decision.can_live_trade)
        self.assertEqual(gate_decision.primary_blocker_code, "LIVE_ENABLING_EVIDENCE_MISSING")

        path_decision = evaluate_live_order_path(
            {
                "source_kind": "FinalDecision",
                "final_decision": "ENTER_LONG",
                "client_order_id": "live-enabling-recheck-spoof",
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
                "live_gate": live_gate,
            }
        )
        self.assertFalse(path_decision.order_adapter_called)
        self.assertFalse(path_decision.external_submit_attempted)
        self.assertFalse(path_decision.live_order_ready)
        self.assertFalse(path_decision.live_order_allowed)
        self.assertFalse(path_decision.can_live_trade)
        self.assertEqual(path_decision.primary_blocker_code, "LIVE_ENABLING_EVIDENCE_MISSING")

    def test_recheck_keeps_gap_open_and_routes_to_scaleup_not_eligible(self):
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        stage_gate = load_json(STAGE_GATE_PATH)
        contract_gap = load_json(CONTRACT_GAP_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK_20260505_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        if state["last_patch_id"] == patch_result["patch_id"]:
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        else:
            self.assertNotEqual(state["next_allowed_task_class"], "")
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertIn(PREVIOUS_REQUIREMENT_ID, state["completed_requirement_ids"])

        self.assertIn("LIVE_ENABLING_EVIDENCE_MISSING", state["open_contract_gap_ids"])
        self.assertIn("LIVE_ENABLING_EVIDENCE_MISSING", patch_result["remaining_blockers"])
        self.assertEqual(contract_gap["contract_gap_id"], "LIVE_ENABLING_EVIDENCE_MISSING")
        self.assertEqual(contract_gap["status"], "OPEN")
        self.assertTrue(contract_gap["live_affecting"])
        self.assertEqual(stage_gate["usable_for_live_enabling_count"], 0)
        self.assertEqual(stage_gate["all_green_live_gate_primary_blocker_code"], "LIVE_ENABLING_EVIDENCE_MISSING")
        self.assertEqual(stage_gate["all_green_order_path_primary_blocker_code"], "LIVE_ENABLING_EVIDENCE_MISSING")
        self.assertFalse(stage_gate["all_green_order_adapter_called"])

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
