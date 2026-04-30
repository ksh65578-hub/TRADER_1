import unittest

from trader1.execution.live_order_gateway import evaluate_live_order_path
from trader1.runtime.readiness.live_preflight import build_upbit_live_review_preflight
from trader1.validation.mvp0_validators import current_authority_hashes


class UpbitLiveReviewNoNewOrderTest(unittest.TestCase):
    def test_live_review_preflight_payload_blocks_order_adapter(self):
        preflight = build_upbit_live_review_preflight(authority=current_authority_hashes())
        decision = evaluate_live_order_path(
            {
                "source_kind": "FinalDecision",
                "final_decision": "ENTER_LONG",
                "client_order_id": "mvp4-live-review-client",
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
                "live_order_ready": preflight["live_order_ready"],
                "live_order_allowed": preflight["live_order_allowed"],
                "can_live_trade": preflight["can_live_trade"],
                "blockers": [blocker["code"] for blocker in preflight["blockers"]],
            }
        )
        self.assertFalse(decision.external_submit_attempted)
        self.assertFalse(decision.order_adapter_called)
        self.assertEqual(decision.primary_blocker_code, "LIVE_READY_MISSING")
        self.assertIn("API_UNVERIFIED", decision.blockers)
        self.assertIn("MANUAL_ORDER_TEST_MISSING", decision.blockers)
        self.assertIn("OPERATOR_APPROVAL_MISSING", decision.blockers)
        self.assertIn("READ_ONLY_BURN_IN_MISSING", decision.blockers)

    def test_review_only_surface_cannot_be_promoted_to_live_order(self):
        preflight = build_upbit_live_review_preflight(authority=current_authority_hashes())
        preflight["readiness_surface"]["live_order_ready"] = True
        decision = evaluate_live_order_path(
            {
                "source_kind": "FinalDecision",
                "final_decision": "ENTER_LONG",
                "client_order_id": "mvp4-mutated-client",
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
                "live_gate": preflight["readiness_surface"],
            }
        )
        self.assertFalse(decision.order_adapter_called)
        self.assertIn("LIVE_READY_MISSING", decision.blockers)


if __name__ == "__main__":
    unittest.main()
