import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_GAP_PATH = (
    ROOT / "system" / "evidence" / "contract_gaps" / "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY.contract_gap.json"
)
DASHBOARD_AUDIT_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY.audit.json"
)
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
STATE_SYNC_PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_STATE_SYNC_RECHECK.patch_result.json"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ActualLongRunRuntimeEvidenceBoundaryRecheckTest(unittest.TestCase):
    def test_contract_gap_remains_open_live_affecting_and_not_live_ready(self):
        gap = load_json(CONTRACT_GAP_PATH)

        self.assertEqual(gap["contract_gap_id"], "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY")
        self.assertEqual(gap["status"], "OPEN")
        self.assertTrue(gap["live_affecting"])
        self.assertEqual(gap["severity"], "HIGH")
        self.assertIn("dashboard", gap["notes"].lower())
        self.assertIn("cannot be closed", gap["notes"].lower())
        blocker_codes = {item["code"] for item in gap["blockers"]}
        self.assertIn("CONTRACT_GAP_HIGH", blocker_codes)
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(gap.get(field, False))

    def test_dashboard_runtime_evidence_boundary_audit_is_display_only(self):
        audit = load_json(DASHBOARD_AUDIT_PATH)

        self.assertEqual(audit["audit_id"], "MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY")
        self.assertEqual(audit["classification"], "dashboard_false_safe_runtime_evidence_boundary")
        self.assertFalse(audit["live_order_ready"])
        self.assertFalse(audit["live_order_allowed"])
        self.assertFalse(audit["can_live_trade"])
        self.assertFalse(audit["scale_up_allowed"])
        self.assertIn("separate actual long-run evidence", audit["condition"].lower())

    def test_state_sync_recheck_keeps_gap_open_and_routes_to_paper_shadow_gap(self):
        state = load_json(STATE_PATH)
        patch_result = load_json(STATE_SYNC_PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_STATE_SYNC_RECHECK_20260504_001",
        )
        self.assertEqual(
            patch_result["next_task_class"],
            "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_RECHECK",
        )
        self.assertEqual(
            state["next_allowed_task_class"],
            "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_RECHECK",
        )
        self.assertIn("ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY", state["open_contract_gap_ids"])
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


if __name__ == "__main__":
    unittest.main()
