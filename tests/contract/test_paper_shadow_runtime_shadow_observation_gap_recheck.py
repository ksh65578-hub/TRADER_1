import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GAP_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "contract_gaps"
    / "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP.contract_gap.json"
)
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
STATE_SYNC_PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_STATE_SYNC_RECHECK.patch_result.json"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PaperShadowRuntimeShadowObservationGapRecheckTest(unittest.TestCase):
    def test_contract_gap_remains_open_live_affecting_and_live_blocked(self):
        gap = load_json(CONTRACT_GAP_PATH)

        self.assertEqual(gap["contract_gap_id"], "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP")
        self.assertEqual(gap["status"], "OPEN")
        self.assertTrue(gap["live_affecting"])
        self.assertEqual(gap["severity"], "HIGH")
        blocker_codes = {item["code"] for item in gap["blockers"]}
        self.assertIn("ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING", blocker_codes)
        self.assertIn("LONG_RUN_EVIDENCE_MISSING", blocker_codes)
        self.assertIn("API_UNVERIFIED", blocker_codes)
        self.assertIn("READ_ONLY_ACCOUNT_SNAPSHOT_MISSING", blocker_codes)
        self.assertIn("long-run evidence", gap["notes"].lower())
        self.assertIn("live readiness", gap["notes"].lower())
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(gap.get(field, False))

    def test_state_sync_recheck_routes_to_ledger_reconciliation_task(self):
        state = load_json(STATE_PATH)
        patch_result = load_json(STATE_SYNC_PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_STATE_SYNC_RECHECK_20260504_001",
        )
        self.assertEqual(
            patch_result["next_task_class"],
            "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_RECHECK",
        )
        self.assertEqual(
            state["next_allowed_task_class"],
            "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_RECHECK",
        )
        self.assertIn("PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP", state["open_contract_gap_ids"])
        self.assertIn("ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING", patch_result["remaining_blockers"])
        self.assertIn("LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING", patch_result["remaining_blockers"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])
        for field in (
            "live_order_ready_after",
            "live_order_allowed_after",
            "can_live_trade_after",
            "scale_up_allowed_after",
            "convergence_live_order_allowed_after",
            "optimizer_live_order_allowed_after",
        ):
            self.assertFalse(patch_result[field])

    def test_historical_shadow_runtime_patch_results_remain_live_blocked(self):
        patch_names = [
            "MVP4_SHADOW_OBSERVATION_ACTUAL_RUNTIME_BLOCKER_RECHECK",
            "MVP4_SHADOW_OBSERVATION_ACTUAL_RUNTIME_HARNESS",
            "MVP4_PAPER_SHADOW_LONG_RUN_SOURCE_COVERAGE_RECHECK",
        ]
        for patch_name in patch_names:
            with self.subTest(patch_name=patch_name):
                patch_result = load_json(
                    ROOT / "system" / "evidence" / "patch_results" / f"{patch_name}.patch_result.json"
                )
                self.assertFalse(patch_result["live_order_ready_after"])
                self.assertFalse(patch_result["live_order_allowed_after"])
                self.assertFalse(patch_result["can_live_trade_after"])
                self.assertFalse(patch_result["scale_up_allowed_after"])
                self.assertIn(
                    "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
                    patch_result["remaining_blockers"],
                )


if __name__ == "__main__":
    unittest.main()
