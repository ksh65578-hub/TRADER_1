import json
import unittest
from pathlib import Path

from trader1.dashboard.read_only_dashboard import dashboard_shell_hash, validate_read_only_dashboard_shell


ROOT = Path(__file__).resolve().parents[2]
PATCH_RESULT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK.patch_result.json"
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


class ActualLongRunRuntimeEvidenceCollectionDepthRecheckTest(unittest.TestCase):
    def test_profile_report_exposes_collection_depth_blocker(self):
        report = load_json(PROFILE_REPORT_PATH)
        depth = report["long_run_collection_depth"]

        self.assertEqual(depth["status"], "BLOCKED_FOR_LONG_RUN_COLLECTION_DEPTH")
        self.assertEqual(depth["blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        self.assertEqual(depth["required_runtime_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(depth["observed_runtime_modes"], ["PAPER", "SHADOW"])
        self.assertIn("SHADOW", depth["missing_runtime_modes"])
        self.assertEqual(depth["observed_cycle_count"], report["accepted_cycle_sample_count"])
        self.assertEqual(depth["minimum_cycle_count"], report["min_actual_long_run_cycle_count"])
        self.assertEqual(
            depth["missing_cycle_count"],
            report["min_actual_long_run_cycle_count"] - report["accepted_cycle_sample_count"],
        )
        self.assertEqual(depth["observed_span_seconds"], report["observed_span_seconds"])
        self.assertEqual(depth["minimum_span_seconds"], report["min_actual_long_run_span_seconds"])
        self.assertGreaterEqual(depth["missing_span_seconds"], 0)
        self.assertEqual(depth["shadow_runtime_depth_status"], "PRESENT_NOT_LONG_RUN")
        self.assertEqual(depth["paper_shadow_pairing_status"], "PAIRED_NOT_LONG_RUN")
        mode_depth = depth["runtime_mode_depth_evidence"]
        self.assertEqual(mode_depth["status"], "BLOCKED_FOR_PER_MODE_LONG_RUN_DEPTH")
        self.assertEqual(mode_depth["blocker_code"], "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")
        self.assertEqual(mode_depth["missing_long_run_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(mode_depth["missing_long_run_mode_count"], 2)
        self.assertEqual(mode_depth["mode_depths"]["paper"]["source_status"], "PRESENT_BOUNDED_NOT_LONG_RUN")
        self.assertEqual(mode_depth["mode_depths"]["shadow"]["source_status"], "PRESENT_BLOCKER_ONLY_NOT_LONG_RUN")
        self.assertFalse(mode_depth["mode_depths"]["paper"]["counts_as_actual_long_run_evidence"])
        self.assertFalse(mode_depth["mode_depths"]["shadow"]["counts_as_actual_long_run_evidence"])
        self.assertFalse(depth["bounded_profile_counts_as_long_run_evidence"])
        self.assertFalse(depth["dashboard_display_counts_as_long_run_evidence"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(depth[field])
            self.assertFalse(report[field])

    def test_dashboard_projection_blocks_hidden_collection_depth(self):
        from tests.dashboard.test_read_only_dashboard import build_dashboard_with_paper_runtime_evidence_collection_profile

        dashboard = build_dashboard_with_paper_runtime_evidence_collection_profile(load_json(PROFILE_REPORT_PATH))
        profile = dashboard["paper_runtime_evidence_collection_profile_status"]

        self.assertEqual(profile["collection_depth_status"], "BLOCKED_FOR_LONG_RUN_COLLECTION_DEPTH")
        self.assertIn("SHADOW", profile["collection_depth_missing_runtime_modes"])
        self.assertEqual(profile["collection_depth_shadow_runtime_status"], "PRESENT_NOT_LONG_RUN")
        self.assertEqual(profile["collection_depth_pairing_status"], "PAIRED_NOT_LONG_RUN")
        self.assertEqual(profile["runtime_mode_depth_status"], "BLOCKED_FOR_PER_MODE_LONG_RUN_DEPTH")
        self.assertEqual(profile["runtime_mode_depth_missing_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(profile["runtime_mode_depth_missing_mode_count"], 2)
        self.assertEqual(profile["paper_mode_source_status"], "PRESENT_BOUNDED_NOT_LONG_RUN")
        self.assertEqual(profile["shadow_mode_source_status"], "PRESENT_BLOCKER_ONLY_NOT_LONG_RUN")
        self.assertFalse(profile["paper_mode_counts_as_actual_long_run_evidence"])
        self.assertFalse(profile["shadow_mode_counts_as_actual_long_run_evidence"])
        self.assertFalse(profile["bounded_profile_counts_as_long_run_evidence"])
        self.assertEqual(validate_read_only_dashboard_shell(dashboard).status, "PASS")

        profile["status"] = "BLOCKED"
        profile["severity"] = "ERROR"
        profile["color_token"] = "red"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        self.assertEqual(validate_read_only_dashboard_shell(dashboard).status, "PASS")
        profile["collection_depth_missing_runtime_modes"] = []
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")

    def test_patch_result_keeps_gap_open_and_routes_to_shadow_observation_gap(self):
        patch_result = load_json(PATCH_RESULT_PATH)
        state = load_json(STATE_PATH)
        gap = load_json(CONTRACT_GAP_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK_20260505_001",
        )
        self.assertEqual(
            patch_result["next_task_class"],
            "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK",
        )
        self.assertEqual(gap["status"], "OPEN")
        self.assertTrue(gap["live_affecting"])
        if state["last_patch_id"] == patch_result["patch_id"]:
            self.assertEqual(
                state["next_allowed_task_class"],
                "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK",
            )
        self.assertIn("ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY", state["open_contract_gap_ids"])
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
