import json
import unittest
from pathlib import Path

from trader1.runtime.protection.emergency_flatten import (
    build_emergency_flatten_report,
    emergency_flatten_hash,
    validate_emergency_flatten_report,
)
from trader1.validation.mvp0_validators import run_validators


ROOT = Path(__file__).resolve().parents[2]


def registry():
    return json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))


def allowed_blockers():
    return set(registry()["enums"]["live_blocker_code"]["values"])


class EmergencyFlattenDryRunTest(unittest.TestCase):
    def test_available_dry_run_passes_without_live_permission(self):
        report = build_emergency_flatten_report(emergency_flatten_id="test-pass")
        result = validate_emergency_flatten_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertTrue(report["emergency_protection_available"])
        self.assertEqual(report["dry_run_status"], "PASS")
        self.assertEqual(report["final_decision"], "NO_TRADE")
        self.assertFalse(report["new_entry_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["can_submit_order"])
        self.assertFalse(report["order_adapter_called"])

    def test_missing_cancel_all_blocks_emergency_protection(self):
        report = build_emergency_flatten_report(
            emergency_flatten_id="test-cancel-missing",
            cancel_all_open_orders_available=False,
        )
        result = validate_emergency_flatten_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertFalse(report["emergency_protection_available"])
        self.assertEqual(report["primary_blocker_code"], "EMERGENCY_FLATTEN_UNAVAILABLE")

    def test_missing_reconciliation_path_blocks(self):
        report = build_emergency_flatten_report(
            emergency_flatten_id="test-reconcile-missing",
            reconciliation_path_available=False,
        )
        result = validate_emergency_flatten_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["primary_blocker_code"], "RECONCILIATION_REQUIRED")

    def test_orphan_position_blocks(self):
        report = build_emergency_flatten_report(
            emergency_flatten_id="test-orphan-position",
            orphan_position_state="PRESENT",
        )
        result = validate_emergency_flatten_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["primary_blocker_code"], "ORPHAN_POSITION_REVIEW_REQUIRED")

    def test_orphan_open_order_blocks(self):
        report = build_emergency_flatten_report(
            emergency_flatten_id="test-orphan-open-order",
            orphan_open_order_state="UNKNOWN",
        )
        result = validate_emergency_flatten_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["primary_blocker_code"], "ORPHAN_OPEN_ORDER_REVIEW_REQUIRED")

    def test_futures_without_reduce_only_path_blocks(self):
        report = build_emergency_flatten_report(
            emergency_flatten_id="test-futures-reduce-only",
            exchange="BINANCE",
            market_type="FUTURES_USDT_M",
            reduce_only_path_available_for_futures=False,
        )
        result = validate_emergency_flatten_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["primary_blocker_code"], "EMERGENCY_FLATTEN_UNAVAILABLE")

    def test_component_scope_mismatch_blocks(self):
        report = build_emergency_flatten_report(
            emergency_flatten_id="test-scope",
            component_scope_overrides={"ledger_recording": {"session_id": "wrong-session"}},
        )
        result = validate_emergency_flatten_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["primary_blocker_code"], "SNAPSHOT_SCOPE_MISMATCH")

    def test_live_permission_mutation_is_blocked(self):
        report = build_emergency_flatten_report(emergency_flatten_id="test-live")
        report["live_order_allowed"] = True
        report["can_live_trade"] = True
        report["can_submit_order"] = True
        report["emergency_flatten_hash"] = emergency_flatten_hash(report)
        result = validate_emergency_flatten_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_order_adapter_call_mutation_is_blocked(self):
        report = build_emergency_flatten_report(emergency_flatten_id="test-adapter")
        report["order_adapter_called"] = True
        report["emergency_flatten_hash"] = emergency_flatten_hash(report)
        result = validate_emergency_flatten_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_non_dry_run_mutation_is_blocked(self):
        report = build_emergency_flatten_report(emergency_flatten_id="test-real", dry_run=False)
        result = validate_emergency_flatten_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_hash_tamper_fails(self):
        report = build_emergency_flatten_report(emergency_flatten_id="test-tamper")
        report["session_id"] = "tampered"
        result = validate_emergency_flatten_report(report)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_emergency_flatten_validator_passes_current_contract(self):
        results = run_validators(["emergency_flatten_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
