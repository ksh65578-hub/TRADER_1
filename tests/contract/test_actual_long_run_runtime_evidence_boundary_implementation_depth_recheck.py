import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATCH_RESULT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK.patch_result.json"
)
PROFILE_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "runtime_checks"
    / "MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.report.json"
)
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
CONTRACT_GAP_PATH = (
    ROOT / "system" / "evidence" / "contract_gaps" / "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY.contract_gap.json"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ActualLongRunRuntimeEvidenceBoundaryImplementationDepthRecheckTest(unittest.TestCase):
    def test_profile_exposes_per_mode_long_run_depth_as_live_blocking(self):
        report = load_json(PROFILE_REPORT_PATH)
        depth = report["long_run_collection_depth"]
        mode_depth = depth["runtime_mode_depth_evidence"]

        self.assertEqual(mode_depth["status"], "BLOCKED_FOR_PER_MODE_LONG_RUN_DEPTH")
        self.assertEqual(mode_depth["blocker_code"], "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")
        self.assertEqual(mode_depth["required_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(mode_depth["missing_long_run_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(mode_depth["missing_long_run_mode_count"], 2)
        self.assertFalse(mode_depth["all_required_modes_long_run_validated"])
        paper_depth = mode_depth["mode_depths"]["paper"]
        shadow_depth = mode_depth["mode_depths"]["shadow"]
        self.assertEqual(paper_depth["source_status"], "PRESENT_BOUNDED_NOT_LONG_RUN")
        self.assertEqual(shadow_depth["source_status"], "PRESENT_BLOCKER_ONLY_NOT_LONG_RUN")
        self.assertFalse(paper_depth["long_run_floor_met"])
        self.assertFalse(shadow_depth["long_run_floor_met"])
        self.assertFalse(paper_depth["counts_as_actual_long_run_evidence"])
        self.assertFalse(shadow_depth["counts_as_actual_long_run_evidence"])
        self.assertEqual(paper_depth["observed_cycle_count"], report["accepted_cycle_sample_count"])
        self.assertEqual(shadow_depth["observed_cycle_count"], 0)
        for artifact in (mode_depth, paper_depth, shadow_depth):
            for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
                self.assertFalse(artifact[field])

    def test_patch_result_routes_to_patch_result_gap_depth_without_live_permission(self):
        patch_result = load_json(PATCH_RESULT_PATH)
        state = load_json(STATE_PATH)
        gap = load_json(CONTRACT_GAP_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK_20260504_001",
        )
        self.assertEqual(
            patch_result["next_task_class"],
            "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK",
        )
        self.assertEqual(gap["status"], "OPEN")
        self.assertTrue(gap["live_affecting"])
        self.assertIn("ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY", state["open_contract_gap_ids"])
        if state["last_patch_id"] == patch_result["patch_id"]:
            self.assertEqual(
                state["next_allowed_task_class"],
                "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK",
            )
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
