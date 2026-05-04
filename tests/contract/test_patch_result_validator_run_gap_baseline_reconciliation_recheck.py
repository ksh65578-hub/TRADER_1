import copy
import json
import unittest
from pathlib import Path

from tools.emit_patch_result_validator_run_gap_baseline_reconciliation_recheck_patch_evidence import (
    PATCH_ID,
    build_reconciliation_report,
    gap_key,
)
from tools.emit_root_launcher_operator_visibility_patch_evidence import sha256_json
from tools.emit_patch_result_runtime_schema_validation_patch_evidence import current_gap_rows


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE.json"
AUDIT_PATH = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json"
CONTRACT_GAP_PATH = ROOT / "system" / "evidence" / "contract_gaps" / "PATCH_RESULT_VALIDATOR_RUN_GAP.contract_gap.json"
RECONCILIATION_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION.json"
)
PATCH_RESULT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK.patch_result.json"
)
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
REQUIREMENT_ID = "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-BASELINE-RECONCILIATION-RECHECK"
NEXT_TASK_CLASS = "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK"
ROUTE_DEPTH_GUARD_REQUIREMENT_ID = "REQ-MVP4-COMPLETED-RECHECK-ROUTE-DEPTH-GUARD"
ROUTE_DEPTH_GUARD_PATCH_ID = "MVP4_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_20260504_001"
ROUTE_DEPTH_GUARD_NEXT_TASK_CLASS = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PatchResultValidatorRunGapBaselineReconciliationRecheckTest(unittest.TestCase):
    def test_reconciliation_report_matches_current_baseline_audit_and_contract_gap(self):
        report = load_json(RECONCILIATION_PATH)
        baseline = load_json(BASELINE_PATH)
        audit = load_json(AUDIT_PATH)
        contract_gap = load_json(CONTRACT_GAP_PATH)
        current_gaps = current_gap_rows()

        baseline_keys = sorted(gap_key(item) for item in baseline["gaps"])
        audit_keys = sorted(gap_key(item) for item in audit["gaps"])
        current_keys = sorted(gap_key(item) for item in current_gaps)

        self.assertEqual(report["status"], "PASS_BASELINE_RECONCILED_HISTORICAL_GAP_REMAINS_LIVE_BLOCKING")
        self.assertEqual(report["patch_id"], PATCH_ID)
        self.assertEqual(report["baseline_gap_count"], 9)
        self.assertEqual(report["baseline_gap_count"], len(baseline_keys))
        self.assertEqual(report["current_gap_count"], len(current_keys))
        self.assertEqual(report["audit_gap_count"], len(audit_keys))
        self.assertEqual(report["unbaselined_gap_count"], 0)
        self.assertEqual(baseline_keys, current_keys)
        self.assertEqual(audit_keys, current_keys)
        self.assertEqual(report["baseline_gap_key_hash"], sha256_json(baseline_keys))
        self.assertEqual(report["current_gap_key_hash"], sha256_json(current_keys))
        self.assertEqual(report["audit_gap_key_hash"], sha256_json(audit_keys))
        self.assertEqual(report["contract_gap_status"], "OPEN")
        self.assertTrue(report["contract_gap_live_affecting"])
        self.assertEqual(contract_gap["status"], "OPEN")
        self.assertTrue(contract_gap["live_affecting"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(audit[field])

    def test_reconciliation_builder_blocks_missing_baseline_gap(self):
        baseline = load_json(BASELINE_PATH)
        audit = load_json(AUDIT_PATH)
        contract_gap = load_json(CONTRACT_GAP_PATH)
        current_gaps = current_gap_rows()
        tampered = copy.deepcopy(baseline)
        tampered["gaps"] = tampered["gaps"][:-1]
        tampered["baseline_gap_count"] = len(tampered["gaps"])
        tampered["baseline_gap_keys"] = [gap_key(item) for item in tampered["gaps"]]
        tampered["baseline_hash"] = sha256_json({key: value for key, value in tampered.items() if key != "baseline_hash"})

        report = build_reconciliation_report(
            "2026-05-04T00:00:00Z",
            baseline["authority"]["trader1_sha256"],
            baseline["authority"]["agents_sha256"],
            current_gaps,
            tampered,
            audit,
            contract_gap,
        )

        self.assertEqual(report["status"], "BLOCKED_BASELINE_RECONCILIATION_DRIFT")
        self.assertEqual(report["missing_from_baseline_count"], 1)
        self.assertFalse(report["checks"]["baseline_matches_current"])

    def test_patch_result_and_state_advance_without_resolving_live_blocker(self):
        patch_result = load_json(PATCH_RESULT_PATH)
        state = load_json(STATE_PATH)

        self.assertEqual(patch_result["patch_id"], PATCH_ID)
        self.assertIn(REQUIREMENT_ID, patch_result["affected_contract_ids"])
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        if ROUTE_DEPTH_GUARD_REQUIREMENT_ID in state["completed_requirement_ids"]:
            self.assertEqual(state["last_patch_id"], ROUTE_DEPTH_GUARD_PATCH_ID)
            self.assertEqual(state["next_allowed_task_class"], ROUTE_DEPTH_GUARD_NEXT_TASK_CLASS)
        else:
            self.assertEqual(state["last_patch_id"], PATCH_ID)
            self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertIn("PATCH_RESULT_VALIDATOR_RUN_GAP", state["open_contract_gap_ids"])
        self.assertIn("POST_REPAIR_RECONCILIATION_REQUIRED", state["open_contract_gap_ids"])
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
