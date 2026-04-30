import json
import unittest
from pathlib import Path

from trader1.runtime.reconciliation.reconciliation import (
    build_reconciliation_report,
    reconciliation_report_hash,
    snapshot_hash,
    validate_reconciliation_report,
)
from trader1.runtime.reconciliation.paper_reconciliation import build_paper_reconciliation_report
from trader1.validation.mvp0_validators import run_validators


ROOT = Path(__file__).resolve().parents[2]


def registry():
    return json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))


def allowed_blockers():
    return set(registry()["enums"]["live_blocker_code"]["values"])


class ReconciliationTest(unittest.TestCase):
    def test_fresh_matching_snapshots_pass_but_do_not_allow_entries(self):
        report = build_reconciliation_report(reconciliation_id="test-pass")
        result = validate_reconciliation_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["reconciliation_status"], "PASS")
        self.assertEqual(report["final_decision"], "NO_TRADE")
        self.assertFalse(report["new_entry_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["can_submit_order"])
        self.assertFalse(report["order_adapter_called"])

    def test_stale_snapshot_requires_reconciliation(self):
        report = build_reconciliation_report(reconciliation_id="test-stale", fresh=False)
        result = validate_reconciliation_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["reconciliation_status"], "STALE")
        self.assertEqual(report["final_decision"], "RECONCILE_REQUIRED")
        self.assertEqual(report["primary_blocker_code"], "RECONCILIATION_REQUIRED")

    def test_balance_mismatch_requires_reconciliation(self):
        report = build_reconciliation_report(
            reconciliation_id="test-mismatch",
            exchange_snapshot={"balances": {"KRW": "1000"}, "positions": [], "open_orders": []},
            internal_state={"balances": {"KRW": "900"}, "positions": [], "open_orders": []},
        )
        result = validate_reconciliation_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["reconciliation_status"], "MISMATCH")
        self.assertEqual(report["primary_blocker_code"], "RECONCILIATION_REQUIRED")
        self.assertTrue(report["mismatches"])

    def test_crafted_pass_with_snapshot_mismatch_is_blocked(self):
        report = build_reconciliation_report(reconciliation_id="test-crafted-mismatch")
        report["internal_state"] = {
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": "mvp1_reconciliation",
            "balances": {"KRW": "900"},
            "positions": [],
            "open_orders": [],
        }
        report["reconciliation_status"] = "PASS"
        report["final_decision"] = "NO_TRADE"
        report["primary_blocker_code"] = None
        report["blockers"] = []
        report["mismatches"] = []
        report["internal_state_hash"] = snapshot_hash(report["internal_state"])
        report["reconciliation_hash"] = reconciliation_report_hash(report)
        result = validate_reconciliation_report(report, allowed_blockers())
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_snapshot_hash_mismatch_fails_closed(self):
        report = build_reconciliation_report(reconciliation_id="test-snapshot-hash")
        report["internal_state"] = {
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": "mvp1_reconciliation",
            "balances": {"KRW": "900"},
            "positions": [],
            "open_orders": [],
        }
        report["reconciliation_hash"] = reconciliation_report_hash(report)
        result = validate_reconciliation_report(report, allowed_blockers())
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_crafted_pass_with_missing_hard_truth_is_blocked(self):
        report = build_reconciliation_report(reconciliation_id="test-crafted-missing-truth")
        report["ledger_head_hash"] = None
        report["reconciliation_status"] = "PASS"
        report["final_decision"] = "NO_TRADE"
        report["primary_blocker_code"] = None
        report["blockers"] = []
        report["mismatches"] = []
        report["reconciliation_hash"] = reconciliation_report_hash(report)
        result = validate_reconciliation_report(report, allowed_blockers())
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_namespace_mismatch_is_blocked(self):
        report = build_reconciliation_report(
            reconciliation_id="test-scope",
            exchange_snapshot={"exchange": "UPBIT", "market_type": "KRW_SPOT", "mode": "PAPER", "session_id": "wrong"},
            internal_state={"exchange": "UPBIT", "market_type": "KRW_SPOT", "mode": "PAPER", "session_id": "mvp1_reconciliation"},
        )
        result = validate_reconciliation_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["reconciliation_status"], "MISMATCH")
        self.assertEqual(report["primary_blocker_code"], "SNAPSHOT_SCOPE_MISMATCH")

    def test_missing_hard_truth_blocks(self):
        report = build_reconciliation_report(reconciliation_id="test-missing", ledger_head_hash=None)
        result = validate_reconciliation_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["reconciliation_status"], "UNKNOWN")
        self.assertEqual(report["primary_blocker_code"], "HARD_TRUTH_MISSING")

    def test_paper_reconciliation_wrapper_matches_current_core_contract(self):
        report = build_paper_reconciliation_report(session_id="test-paper-wrapper")
        result = validate_reconciliation_report(report, allowed_blockers())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["exchange"], "UPBIT")
        self.assertEqual(report["market_type"], "KRW_SPOT")
        self.assertEqual(report["mode"], "PAPER")
        self.assertEqual(report["session_id"], "test-paper-wrapper")
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])

    def test_live_permission_mutation_is_blocked(self):
        report = build_reconciliation_report(reconciliation_id="test-live")
        report["live_order_allowed"] = True
        report["can_live_trade"] = True
        report["can_submit_order"] = True
        report["reconciliation_hash"] = reconciliation_report_hash(report)
        result = validate_reconciliation_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_order_adapter_call_mutation_is_blocked(self):
        report = build_reconciliation_report(reconciliation_id="test-adapter")
        report["order_adapter_called"] = True
        report["reconciliation_hash"] = reconciliation_report_hash(report)
        result = validate_reconciliation_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_hash_tamper_fails(self):
        report = build_reconciliation_report(reconciliation_id="test-tamper")
        report["session_id"] = "tampered"
        result = validate_reconciliation_report(report)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_reconciliation_validators_pass_current_contract(self):
        results = run_validators(["reconciliation_validator", "ledger_reconciliation_validator"])
        self.assertEqual([result["status"] for result in results], ["PASS", "PASS"])


if __name__ == "__main__":
    unittest.main()
