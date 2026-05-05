from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SCANNED_PATHS = [
    ROOT / "trader1" / "runtime" / "boot" / "safe_launcher.py",
    ROOT / "tools" / "emit_dashboard_residual_evidence_progress_clarity_patch_evidence.py",
    ROOT / "tools" / "emit_dashboard_residual_execution_guide_clarity_patch_evidence.py",
    ROOT / "tools" / "emit_residual_operator_evidence_run_preflight_patch_evidence.py",
    ROOT / "tools" / "emit_residual_operator_evidence_intake_audit_patch_evidence.py",
    ROOT / "tools" / "emit_residual_operator_evidence_trial_duration_policy_patch_evidence.py",
    ROOT / "tools" / "emit_residual_operator_handoff_execution_guide_patch_evidence.py",
    ROOT / "tools" / "emit_residual_mvp5_entry_duration_policy_patch_evidence.py",
    ROOT / "contracts" / "generated" / "context_pack" / "MVP4_DASHBOARD_RESIDUAL_EVIDENCE_PROGRESS_CLARITY.md",
    ROOT / "contracts" / "generated" / "context_pack" / "MVP4_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY.md",
    ROOT / "contracts" / "generated" / "context_pack" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.md",
    ROOT / "contracts" / "generated" / "context_pack" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT.md",
    ROOT / "contracts" / "generated" / "context_pack" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY.md",
    ROOT / "contracts" / "generated" / "context_pack" / "MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.md",
    ROOT / "contracts" / "generated" / "context_pack" / "MVP4_RESIDUAL_MVP5_ENTRY_DURATION_POLICY.md",
    ROOT / "contracts" / "generated" / "requirement_index.json",
]

FORBIDDEN_STALE_SNIPPETS = [
    'or report.get("minimum_observation_hours_required", 0) < 120',
    '"minimum_observation_hours_required": 120',
    '"minimum_observation_hours": 120',
    "120h minimum observation requirement",
    "120h collection",
    "after the 120h PAPER/SHADOW run",
    "expected after the 120h PAPER/SHADOW run",
    "requires 120 hours before the next review",
    "Set minimum local observation duration to 120 hours",
    "minimum_observation_hours_for_local_runtime: 120",
    "formal MVP-5 profile remains 120h / 43200 ticks",
    "formal MVP-5 profile remains {report[\"formal_mvp5_duration_hours\"]}h",
    "MVP5 review-entry PAPER/SHADOW duration is 48h / 17280 ticks",
    "The old 120h profile is retained only",
    "retaining 120h as optional extended observation",
    "retaining 120h as optional",
    "The 120h profile is retained only",
    "Moved 120h to optional extended observation",
]


class ResidualAdaptiveDurationWordingHygieneTest(unittest.TestCase):
    def test_active_emitters_and_read_caches_do_not_reintroduce_fixed_duration_gates(self) -> None:
        for path in SCANNED_PATHS:
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                for snippet in FORBIDDEN_STALE_SNIPPETS:
                    self.assertNotIn(snippet, text)

    def test_active_emitters_and_read_caches_name_adaptive_gate(self) -> None:
        combined = "\n".join(path.read_text(encoding="utf-8") for path in SCANNED_PATHS)

        self.assertIn("REMOVED_NO_FIXED_RUNTIME_FLOOR", combined)
        self.assertIn("adaptive evidence", combined.lower())
        self.assertIn("no fixed observation-duration floor", combined)


if __name__ == "__main__":
    unittest.main()
