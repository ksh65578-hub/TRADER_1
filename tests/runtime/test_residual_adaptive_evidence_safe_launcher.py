from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from trader1.runtime.boot.safe_launcher import load_residual_operator_evidence_progress_report


ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REPORT = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
)


class ResidualAdaptiveEvidenceSafeLauncherTest(unittest.TestCase):
    def test_launcher_loads_adaptive_zero_floor_progress_report(self) -> None:
        report = load_residual_operator_evidence_progress_report(ROOT)

        self.assertIsNotNone(report)
        assert report is not None
        self.assertEqual(report["minimum_observation_hours_required"], 0)
        self.assertEqual(report["fixed_duration_gate_status"], "REMOVED_NO_FIXED_RUNTIME_FLOOR")
        self.assertTrue(report["codex_stepwise_review_allowed"])
        self.assertTrue(report["codex_can_continue_non_live_patches"])
        self.assertFalse(report["user_runtime_required_for_next_non_live_patch"])
        self.assertTrue(report["user_runtime_required_for_gap_closure"])
        for field in (
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
            "current_evidence_write_allowed",
            "gap_closure_allowed_by_this_patch",
            "live_ready_write_allowed",
        ):
            self.assertFalse(report[field])

    def test_launcher_rejects_legacy_fixed_duration_progress_report(self) -> None:
        report = json.loads(PROGRESS_REPORT.read_text(encoding="utf-8"))
        report["minimum_observation_hours_required"] = 120
        report["fixed_duration_gate_status"] = "LEGACY_FIXED_RUNTIME_FLOOR"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = (
                temp_root
                / "system"
                / "evidence"
                / "audit_reports"
                / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(report, indent=2), encoding="utf-8")

            self.assertIsNone(load_residual_operator_evidence_progress_report(temp_root))

    def test_launcher_rejects_user_runtime_required_for_next_patch_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target = (
                temp_root
                / "system"
                / "evidence"
                / "audit_reports"
                / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROGRESS_REPORT, target)
            report = json.loads(target.read_text(encoding="utf-8"))
            report["user_runtime_required_for_next_non_live_patch"] = True
            target.write_text(json.dumps(report, indent=2), encoding="utf-8")

            self.assertIsNone(load_residual_operator_evidence_progress_report(temp_root))


if __name__ == "__main__":
    unittest.main()
