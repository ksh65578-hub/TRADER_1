import unittest

from trader1.execution.live_order_gateway import evaluate_live_order_path
from trader1.safety.live_order_gate import REQUIRED_LIVE_TRUE_FIELDS
from trader1.validation.mvp0_validators import run_validators


class RecordingOrderAdapter:
    def __init__(self):
        self.called = False

    def submit_order(self, *_args, **_kwargs):
        self.called = True


class ExplodingOrderAdapter:
    def __getattribute__(self, name):
        if name == "submit_order":
            raise AssertionError("submit_order must not be accessed before live-enabling evidence")
        return super().__getattribute__(name)


class OrderPathGuardTest(unittest.TestCase):
    def test_strategy_signal_cannot_call_order_adapter(self):
        adapter = RecordingOrderAdapter()
        decision = evaluate_live_order_path(
            {
                "source_kind": "StrategySignal",
                "final_decision": "ENTER_LONG",
                "strategy_attempted_exchange_call": True,
                "client_order_id": "mvp0-client-1",
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
            },
            order_adapter=adapter,
        )
        self.assertFalse(adapter.called)
        self.assertFalse(decision.order_adapter_called)
        self.assertTrue(decision.direct_strategy_order_blocked)
        self.assertEqual(decision.primary_blocker_code, "CANDIDATE_DIRECT_LIVE_FORBIDDEN")
        self.assertFalse(decision.live_order_ready)
        self.assertFalse(decision.live_order_allowed)
        self.assertFalse(decision.can_live_trade)

    def test_final_decision_without_live_ready_blocks_before_adapter(self):
        adapter = RecordingOrderAdapter()
        decision = evaluate_live_order_path(
            {
                "source_kind": "FinalDecision",
                "final_decision": "ENTER_LONG",
                "client_order_id": "mvp0-client-2",
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
            },
            order_adapter=adapter,
        )
        self.assertFalse(adapter.called)
        self.assertFalse(decision.external_submit_attempted)
        self.assertFalse(decision.order_adapter_called)
        self.assertEqual(decision.primary_blocker_code, "LIVE_READY_MISSING")

    def test_ambiguous_submit_requires_same_identifier_reconciliation(self):
        decision = evaluate_live_order_path(
            {
                "source_kind": "FinalDecision",
                "final_decision": "ENTER_LONG",
                "original_client_order_id": "client-old",
                "client_order_id": "client-new",
                "idempotency_state": "PENDING_CONFIRM",
                "new_identifier_proposed": True,
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
            }
        )
        self.assertFalse(decision.order_adapter_called)
        self.assertIn("RECONCILIATION_REQUIRED", decision.blockers)
        self.assertEqual(decision.idempotency_action, "RECONCILE_SAME_IDENTIFIER_FIRST")

    def test_ambiguous_transport_same_identifier_still_requires_reconciliation(self):
        live_gate = {field: True for field in REQUIRED_LIVE_TRUE_FIELDS}
        live_gate.update(
            {
                "live_order_ready": True,
                "live_order_allowed": True,
                "can_live_trade": True,
                "live_enabling_patch_valid": True,
            }
        )
        decision = evaluate_live_order_path(
            {
                "source_kind": "FinalDecision",
                "final_decision": "ENTER_LONG",
                "original_client_order_id": "client-same",
                "client_order_id": "client-same",
                "idempotency_state": "TRANSPORT_AMBIGUOUS",
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
                "live_gate": live_gate,
            }
        )
        self.assertFalse(decision.order_adapter_called)
        self.assertEqual(decision.final_decision, "RECONCILE_REQUIRED")
        self.assertEqual(decision.primary_blocker_code, "RECONCILIATION_REQUIRED")
        self.assertEqual(decision.idempotency_action, "RECONCILE_SAME_IDENTIFIER_FIRST")

    def test_ambiguous_transport_missing_original_identifier_requires_reconciliation(self):
        live_gate = {field: True for field in REQUIRED_LIVE_TRUE_FIELDS}
        live_gate.update(
            {
                "live_order_ready": True,
                "live_order_allowed": True,
                "can_live_trade": True,
                "live_enabling_patch_valid": True,
            }
        )
        decision = evaluate_live_order_path(
            {
                "source_kind": "FinalDecision",
                "final_decision": "ENTER_LONG",
                "client_order_id": "client-without-original",
                "idempotency_state": "PENDING_CONFIRM",
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
                "live_gate": live_gate,
            }
        )
        self.assertFalse(decision.order_adapter_called)
        self.assertEqual(decision.final_decision, "RECONCILE_REQUIRED")
        self.assertEqual(decision.primary_blocker_code, "RECONCILIATION_REQUIRED")
        self.assertEqual(decision.idempotency_action, "RECONCILE_SAME_IDENTIFIER_FIRST")

    def test_all_green_live_gate_payload_still_never_submits_before_live_enabling_patch(self):
        adapter = RecordingOrderAdapter()
        live_gate = {field: True for field in REQUIRED_LIVE_TRUE_FIELDS}
        live_gate.update(
            {
                "live_order_ready": True,
                "live_order_allowed": True,
                "can_live_trade": True,
                "live_enabling_patch_valid": True,
            }
        )
        decision = evaluate_live_order_path(
            {
                "source_kind": "FinalDecision",
                "final_decision": "ENTER_LONG",
                "client_order_id": "spoofed-all-green-client",
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
                "live_gate": live_gate,
            },
            order_adapter=adapter,
        )
        self.assertFalse(adapter.called)
        self.assertFalse(decision.external_submit_attempted)
        self.assertFalse(decision.order_adapter_called)
        self.assertFalse(decision.live_order_ready)
        self.assertFalse(decision.live_order_allowed)
        self.assertFalse(decision.can_live_trade)
        self.assertEqual(decision.primary_blocker_code, "LIVE_ENABLING_EVIDENCE_MISSING")

    def test_existing_submit_attempt_evidence_is_not_reported_safe(self):
        adapter = RecordingOrderAdapter()
        decision = evaluate_live_order_path(
            {
                "source_kind": "FinalDecision",
                "final_decision": "ENTER_LONG",
                "client_order_id": "mvp4-existing-submit-attempt",
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
                "order_adapter_submit_attempted": True,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
            },
            order_adapter=adapter,
        )
        self.assertFalse(adapter.called)
        self.assertFalse(decision.order_adapter_called)
        self.assertTrue(decision.external_submit_attempted)
        self.assertIn("LIVE_FINAL_GUARD_FAILED", decision.blockers)
        self.assertFalse(decision.live_order_ready)
        self.assertFalse(decision.live_order_allowed)
        self.assertFalse(decision.can_live_trade)

    def test_order_adapter_object_is_never_touched_before_live_enabling_evidence(self):
        live_gate = {field: True for field in REQUIRED_LIVE_TRUE_FIELDS}
        live_gate.update(
            {
                "live_order_ready": True,
                "live_order_allowed": True,
                "can_live_trade": True,
                "live_enabling_patch_valid": True,
            }
        )
        decision = evaluate_live_order_path(
            {
                "source_kind": "FinalDecision",
                "final_decision": "ENTER_LONG",
                "client_order_id": "mvp4-exploding-adapter",
                "single_writer_available": True,
                "budget_reserved": True,
                "local_reservation_committed": True,
                "ledger_reconciled": True,
                "live_gate": live_gate,
            },
            order_adapter=ExplodingOrderAdapter(),
        )
        self.assertFalse(decision.order_adapter_called)
        self.assertFalse(decision.external_submit_attempted)
        self.assertEqual(decision.primary_blocker_code, "LIVE_ENABLING_EVIDENCE_MISSING")

    def test_order_path_validators_pass_current_contract(self):
        results = run_validators(["single_writer_order_path_validator", "strategy_direct_order_validator"])
        self.assertEqual({result["status"] for result in results}, {"PASS"})


if __name__ == "__main__":
    unittest.main()
