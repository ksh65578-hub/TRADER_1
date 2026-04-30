import json
import unittest
from pathlib import Path

from trader1.runtime.resource_guard.safety_control import (
    build_safety_control_report,
    safety_control_hash,
    validate_safety_control_report,
)
from trader1.validation.mvp0_validators import run_validators


ROOT = Path(__file__).resolve().parents[2]


def registry():
    return json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))


def build_report(**kwargs):
    return build_safety_control_report(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_safety_control",
        **kwargs,
    )


class SafetyControlTest(unittest.TestCase):
    def test_default_report_is_fail_closed_and_non_trading(self):
        report = build_report()
        result = validate_safety_control_report(report, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["can_submit_order"])
        self.assertFalse(report["order_adapter_called"])
        self.assertEqual(report["final_decision"], "SAFE_MODE")

    def test_manual_stop_forces_kill_switch(self):
        report = build_report(operator_action="manual_stop")
        result = validate_safety_control_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["kill_switch_state"], "ENGAGED")
        self.assertEqual(report["final_decision"], "KILL_SWITCH")
        self.assertEqual(report["primary_blocker_code"], "KILL_SWITCH_ACTIVE")

    def test_unavailable_kill_switch_blocks_readiness(self):
        report = build_report(kill_switch_available=False)
        result = validate_safety_control_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["kill_switch_state"], "UNAVAILABLE")
        self.assertEqual(report["primary_blocker_code"], "KILL_SWITCH_ACTIVE")
        self.assertFalse(report["live_order_ready"])

    def test_critical_resource_blocks_new_entries(self):
        report = build_report(resource_metrics={"critical": True})
        result = validate_safety_control_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["resource_health_state"], "CRITICAL")
        self.assertTrue(report["resource_block_new_entries"])
        self.assertIn("RESOURCE_LIMIT_BLOCK", {blocker["code"] for blocker in report["blockers"]})
        self.assertEqual(report["final_decision"], "NO_TRADE")

    def test_live_permission_mutation_is_blocked(self):
        report = build_report()
        report["live_order_allowed"] = True
        report["can_live_trade"] = True
        report["can_submit_order"] = True
        report["safety_control_hash"] = safety_control_hash(report)
        result = validate_safety_control_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_adapter_call_mutation_is_blocked(self):
        report = build_report()
        report["order_adapter_called"] = True
        report["safety_control_hash"] = safety_control_hash(report)
        result = validate_safety_control_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_safety_control_validator_passes_current_contract(self):
        results = run_validators(["safety_control_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
