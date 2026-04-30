import unittest

from trader1.runtime.operator_control.operator_control import (
    build_operator_action_audit,
    operator_action_hash,
    validate_operator_action_audit,
)
from trader1.validation.mvp0_validators import run_validators


def build_record(action_code: str, **kwargs):
    return build_operator_action_audit(
        action_id=kwargs.pop("action_id", f"test-{action_code}"),
        operator_id_hash=kwargs.pop("operator_id_hash", "operator-hash"),
        action_code=action_code,
        session_id=kwargs.pop("session_id", "test_operator_control"),
        **kwargs,
    )


class OperatorControlTest(unittest.TestCase):
    def test_manual_stop_is_audited_and_blocks_trading(self):
        record = build_record("manual_stop")
        result = validate_operator_action_audit(record)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(record["final_decision_id"], "KILL_SWITCH")
        self.assertEqual(record["result"], "BLOCKED")
        self.assertFalse(record["requested_state"]["live_order_allowed"])
        self.assertFalse(record["requested_state"]["can_live_trade"])

    def test_manual_safe_mode_is_confirmation_gated(self):
        record = build_record("manual_safe_mode")
        result = validate_operator_action_audit(record)
        self.assertEqual(result.status, "PASS")
        self.assertTrue(record["confirmation_required"])
        self.assertEqual(record["final_decision_id"], "SAFE_MODE")
        self.assertEqual(record["result"], "BLOCKED")

    def test_manual_resume_read_only_cannot_resume_live(self):
        record = build_record("manual_resume_read_only")
        result = validate_operator_action_audit(record)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(record["requested_state"]["mode"], "READ_ONLY")
        self.assertFalse(record["requested_state"]["live_order_ready"])
        self.assertFalse(record["requested_state"]["live_order_allowed"])

        record["requested_state"]["mode"] = "LIVE"
        record["event_hash"] = operator_action_hash(record)
        mutated_result = validate_operator_action_audit(record)
        self.assertEqual(mutated_result.status, "BLOCKED")
        self.assertEqual(mutated_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_manual_reduce_without_reconciliation_is_blocked(self):
        record = build_record("manual_reduce_position", target_symbol="KRW-BTC")
        result = validate_operator_action_audit(record)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_manual_exit_cannot_record_adapter_call(self):
        record = build_record(
            "manual_exit_all_positions",
            target_symbol="KRW-BTC",
            requested_state={"order_adapter_called": True},
        )
        record["event_hash"] = operator_action_hash(record)
        result = validate_operator_action_audit(record)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_live_permission_mutation_is_blocked(self):
        record = build_record(
            "manual_resume_read_only",
            requested_state={"live_order_allowed": True, "can_live_trade": True, "can_submit_order": True},
        )
        record["event_hash"] = operator_action_hash(record)
        result = validate_operator_action_audit(record)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_unknown_operator_action_is_blocked(self):
        record = build_record("manual_reduce_or_close_position")
        result = validate_operator_action_audit(record)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "UNKNOWN_BLOCKED")

    def test_hash_tamper_fails(self):
        record = build_record("manual_stop")
        record["target_symbol"] = "KRW-ETH"
        result = validate_operator_action_audit(record)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_operator_control_validators_pass_current_contract(self):
        results = run_validators(["operator_action_audit_validator", "operator_control_validator"])
        self.assertEqual([result["status"] for result in results], ["PASS", "PASS"])


if __name__ == "__main__":
    unittest.main()
