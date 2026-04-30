import json
import unittest
from pathlib import Path

from trader1.safety.live_order_gate import BLOCKED_CASES, REQUIRED_LIVE_TRUE_FIELDS, evaluate_live_order_gate


ROOT = Path(__file__).resolve().parents[2]


class LiveBlockedScaffoldTest(unittest.TestCase):
    def test_live_ready_missing_blocks_order_adapter(self):
        fixture = json.loads(
            (ROOT / "tests" / "live_blocked" / "fixtures" / "live_ready_missing.json").read_text(encoding="utf-8")
        )
        self.assertFalse(fixture["live_order_ready"])
        self.assertFalse(fixture["live_order_allowed"])
        self.assertFalse(fixture["can_live_trade"])
        self.assertFalse(fixture["expected_order_adapter_called"])
        self.assertEqual(fixture["expected_blocker_code"], "LIVE_READY_MISSING")

    def test_required_negative_matrix_blocks_order_adapter(self):
        matrix = json.loads(
            (ROOT / "tests" / "live_blocked" / "fixtures" / "live_blocked_matrix.json").read_text(encoding="utf-8")
        )
        case_ids = {case["case_id"] for case in matrix["cases"]}
        self.assertEqual(case_ids, set(BLOCKED_CASES))
        for case in matrix["cases"]:
            with self.subTest(case_id=case["case_id"]):
                decision = evaluate_live_order_gate(
                    {
                        "live_order_ready": False,
                        "live_order_allowed": False,
                        "can_live_trade": False,
                        "blocker_code": case["blocker_code"],
                    }
                )
                self.assertFalse(decision.order_adapter_called)
                self.assertFalse(decision.live_order_ready)
                self.assertFalse(decision.live_order_allowed)
                self.assertFalse(decision.can_live_trade)
                self.assertEqual(decision.final_decision, "BLOCKED")
                self.assertEqual(decision.primary_blocker_code, case["blocker_code"])

    def test_spoofed_all_live_true_inputs_still_block_without_live_enabling_patch(self):
        signal = {field: True for field in REQUIRED_LIVE_TRUE_FIELDS}
        signal.update(
            {
                "live_order_ready": True,
                "live_order_allowed": True,
                "can_live_trade": True,
                "live_enabling_patch_valid": True,
            }
        )
        decision = evaluate_live_order_gate(signal)
        self.assertFalse(decision.order_adapter_called)
        self.assertFalse(decision.live_order_ready)
        self.assertFalse(decision.live_order_allowed)
        self.assertFalse(decision.can_live_trade)
        self.assertEqual(decision.final_decision, "BLOCKED")
        self.assertEqual(decision.primary_blocker_code, "LIVE_ENABLING_EVIDENCE_MISSING")


if __name__ == "__main__":
    unittest.main()
