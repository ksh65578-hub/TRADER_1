import copy
import json
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _patch_result_instance_errors,
    _patch_result_unbaselined_gaps,
    _patch_result_validator_run_gaps,
    run_validators,
)
from trader1.validation.schema_instance import load_schema_bundle


ROOT = Path(__file__).resolve().parents[2]


def latest_patch_result() -> tuple[Path, dict]:
    path = sorted((ROOT / "system" / "evidence" / "patch_results").glob("*.patch_result.json"))[-1]
    return path, json.loads(path.read_text(encoding="utf-8"))


class PatchResultRuntimeSchemaValidationTest(unittest.TestCase):
    def test_current_patch_result_history_passes_runtime_schema_validator(self):
        results = run_validators(["patch_result_runtime_schema_instance_validator"])
        self.assertEqual(results[0]["status"], "PASS", json.dumps(results[0], indent=2))

    def test_patch_result_extra_property_fails_runtime_schema_instance_validation(self):
        path, patch = latest_patch_result()
        tampered = copy.deepcopy(patch)
        tampered["dashboard_truth_override"] = True
        errors = _patch_result_instance_errors(tampered, path, load_schema_bundle(ROOT / "contracts" / "schema"))
        self.assertTrue(errors)
        self.assertIn("additional properties", errors[0])

    def test_patch_result_live_flag_true_fails_runtime_schema_instance_validation(self):
        path, patch = latest_patch_result()
        tampered = copy.deepcopy(patch)
        tampered["live_order_allowed_after"] = True
        errors = _patch_result_instance_errors(tampered, path, load_schema_bundle(ROOT / "contracts" / "schema"))
        self.assertTrue(errors)
        self.assertIn("live_order_allowed_after", errors[0])

    def test_patch_result_missing_required_validator_run_is_detected(self):
        path, patch = latest_patch_result()
        tampered = copy.deepcopy(patch)
        tampered["validators_required"] = ["registry_validator", "patch_result_runtime_schema_instance_validator"]
        tampered["validators_run"] = [{"validator_id": "registry_validator", "status": "PASS"}]
        gaps = _patch_result_validator_run_gaps(tampered, path)
        self.assertEqual(
            gaps,
            [
                {
                    "patch_result_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "validator_id": "patch_result_runtime_schema_instance_validator",
                    "gap_type": "MISSING_VALIDATOR_RUN",
                }
            ],
        )

    def test_unbaselined_validator_run_gap_is_detected(self):
        baseline_gap = {
            "patch_result_path": "system/evidence/patch_results/MVP0_CONTRACT_BASELINE.patch_result.json",
            "validator_id": "patch_result_schema_validator",
            "gap_type": "MISSING_VALIDATOR_RUN",
        }
        new_gap = {
            "patch_result_path": "system/evidence/patch_results/NEW_PATCH.patch_result.json",
            "validator_id": "live_final_guard_validator",
            "gap_type": "MISSING_VALIDATOR_RUN",
        }
        self.assertEqual(_patch_result_unbaselined_gaps([baseline_gap, new_gap], [baseline_gap]), [new_gap])

    def test_current_validator_run_gaps_match_sealed_baseline(self):
        baseline_path = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE.json"
        if not baseline_path.exists():
            self.skipTest("sealed patch_result validator-run baseline is not generated yet")
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        current_gaps = []
        for patch_path in sorted((ROOT / "system" / "evidence" / "patch_results").glob("*.patch_result.json")):
            current_gaps.extend(_patch_result_validator_run_gaps(json.loads(patch_path.read_text(encoding="utf-8")), patch_path))
        self.assertEqual(_patch_result_unbaselined_gaps(current_gaps, baseline["gaps"]), [])

    def test_patch_result_validator_gap_audit_remains_live_blocking_without_unbaselined_gaps(self):
        baseline_path = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE.json"
        audit_path = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json"
        contract_gap_path = ROOT / "system" / "evidence" / "contract_gaps" / "PATCH_RESULT_VALIDATOR_RUN_GAP.contract_gap.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        contract_gap = json.loads(contract_gap_path.read_text(encoding="utf-8"))
        self.assertEqual(audit["status"], "AUDIT_PRESERVED_BASELINE_MATCH_LIVE_BLOCKING")
        self.assertEqual(audit["baseline_gap_count"], len(baseline["gaps"]))
        self.assertEqual(audit["current_gap_count"], len(baseline["gaps"]))
        self.assertEqual(audit["unbaselined_gap_count"], 0)
        self.assertEqual(contract_gap["status"], "OPEN")
        self.assertEqual(contract_gap["contract_gap_id"], "PATCH_RESULT_VALIDATOR_RUN_GAP")
        self.assertFalse(audit["live_order_allowed"])
        self.assertFalse(audit["scale_up_allowed"])

    def test_patch_result_validator_gap_state_sync_advances_next_task_without_resolving_gap(self):
        state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("last_patch_id") != "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_STATE_SYNC_RECHECK_20260504_001":
            self.skipTest("patch_result validator-run gap state-sync recheck has not been generated yet")
        self.assertEqual(
            state["next_allowed_task_class"],
            "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_RECHECK",
        )
        self.assertIn("PATCH_RESULT_VALIDATOR_RUN_GAP", state["open_contract_gap_ids"])
        self.assertFalse(state["live_order_ready"])
        self.assertFalse(state["live_order_allowed"])
        self.assertFalse(state["can_live_trade"])
        self.assertFalse(state["scale_up_allowed"])


if __name__ == "__main__":
    unittest.main()
