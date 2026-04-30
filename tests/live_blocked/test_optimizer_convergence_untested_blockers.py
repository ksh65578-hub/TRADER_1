import json
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


GUARDRAIL_VALIDATORS = {
    "optimizer_guardrail_validator",
    "optimizer_no_live_mutation_validator",
    "exploration_exploitation_policy_validator",
    "convergence_assessment_validator",
    "scale_up_eligibility_validator",
}
EXTERNAL_REVIEW_BLOCKER_INPUTS = {
    "system/evidence/upbit/krw_spot/read_only/mvp4_live_review/official_api_verification_report.json",
    "system/runtime/upbit/krw_spot/read_only/mvp4_live_review/read_only_account_snapshot.json",
    "system/evidence/upbit/krw_spot/read_only/mvp4_live_review/api_key_permission_check_report.json",
    "system/evidence/upbit/krw_spot/live/mvp4_live_review/manual_order_test_evidence_missing.json",
}


class OptimizerConvergenceUntestedBlockersTest(unittest.TestCase):
    def test_optimizer_and_convergence_guardrails_do_not_enable_live(self):
        state = json.loads((ROOT / "contracts/generated/current_implementation_state.json").read_text(encoding="utf-8"))
        patch = json.loads(
            (ROOT / "system/evidence/patch_results/MVP4_SCALEUP_SAFETY_BLOCKED.patch_result.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(GUARDRAIL_VALIDATORS.issubset(set(state["implemented_validator_ids"])))
        self.assertTrue(GUARDRAIL_VALIDATORS.isdisjoint(set(state["untested_validator_ids"])))
        self.assertEqual(patch["optimizer_guardrail_result"], "PASS")
        self.assertEqual(patch["convergence_guardrail_result"], "PASS")
        self.assertFalse(patch["optimizer_live_mutation_detected"])
        self.assertFalse(patch["convergence_live_mutation_detected"])
        self.assertFalse(patch["scale_up_allowed_after"])

        self.assertFalse(patch["live_order_ready_after"])
        self.assertFalse(patch["live_order_allowed_after"])
        self.assertFalse(patch["can_live_trade_after"])
        self.assertFalse(state["live_order_ready"])
        self.assertFalse(state["live_order_allowed"])
        self.assertFalse(state["can_live_trade"])

    def test_external_blocker_report_keeps_mvp5_forbidden_without_evidence(self):
        report = json.loads(
            (ROOT / "system/evidence/blocker_reports/MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE.blocker_report.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn("MVP5_LIVE_ENABLING_WITHOUT_EVIDENCE", report["forbidden_next_steps"])
        self.assertIn("LIVE_ENABLING_EVIDENCE_MISSING", report["remaining_blockers"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])

    def test_external_blocker_artifacts_agree_on_live_blocked_state(self):
        state = json.loads((ROOT / "contracts/generated/current_implementation_state.json").read_text(encoding="utf-8"))
        external_patch = json.loads((ROOT / "system/evidence/patch_results/MVP4_EXTERNAL_BLOCKER.patch_result.json").read_text(encoding="utf-8"))
        scaleup_patch = json.loads(
            (ROOT / "system/evidence/patch_results/MVP4_SCALEUP_SAFETY_BLOCKED.patch_result.json").read_text(
                encoding="utf-8"
            )
        )
        report = json.loads(
            (ROOT / "system/evidence/blocker_reports/MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE.blocker_report.json").read_text(
                encoding="utf-8"
            )
        )
        stage_gate = json.loads(
            (ROOT / "system/evidence/stage_gates/MVP4_EXTERNAL_BLOCKER.stage_gate_result.json").read_text(
                encoding="utf-8"
            )
        )
        evidence_manifest = json.loads(
            (ROOT / "system/evidence/MVP4_EXTERNAL_BLOCKER.evidence_manifest.json").read_text(encoding="utf-8")
        )
        patch_ledger = json.loads((ROOT / "system/evidence/implementation_patch_ledger.json").read_text(encoding="utf-8"))
        latest_ledger_entry = patch_ledger["patches"][-1]
        latest_patch = json.loads((ROOT / latest_ledger_entry["patch_result_path"]).read_text(encoding="utf-8"))

        self.assertEqual(state["last_patch_id"], latest_ledger_entry["patch_id"])
        self.assertEqual(state["last_patch_result_hash"], latest_ledger_entry["patch_result_hash"])
        self.assertEqual(latest_ledger_entry["patch_result_hash"], latest_patch["result_hash"])
        self.assertEqual(report["latest_scaleup_safety_result_hash"], scaleup_patch["result_hash"])
        self.assertEqual(report["last_patch_result_hash"], external_patch["result_hash"])
        self.assertEqual(external_patch["optimizer_guardrail_result"], "PASS")
        self.assertEqual(external_patch["convergence_guardrail_result"], "PASS")
        self.assertTrue(external_patch["optimizer_validators_run"])
        self.assertTrue(external_patch["convergence_validators_run"])
        self.assertEqual(stage_gate["stage_gate_status"], "BLOCKED_BY_EXTERNAL_LIVE_REVIEW_EVIDENCE")
        self.assertEqual(stage_gate["next_allowed_task_class"], "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED")

        self.assertEqual(set(evidence_manifest["known_blockers"]), set(external_patch["remaining_blockers"]))
        self.assertEqual(set(report["remaining_blockers"]), set(external_patch["remaining_blockers"]))
        for artifact_path in evidence_manifest["artifact_paths"]:
            self.assertTrue((ROOT / artifact_path).exists(), artifact_path)

        self.assertFalse(stage_gate["live_order_ready"])
        self.assertFalse(stage_gate["live_order_allowed"])
        self.assertFalse(stage_gate["can_live_trade"])
        self.assertFalse(evidence_manifest["live_order_ready"])
        self.assertFalse(evidence_manifest["live_order_allowed"])
        self.assertFalse(evidence_manifest["can_live_trade"])

    def test_evidence_manifest_tracks_external_review_blocker_inputs(self):
        evidence_manifest = json.loads(
            (ROOT / "system/evidence/MVP4_EXTERNAL_BLOCKER.evidence_manifest.json").read_text(encoding="utf-8")
        )

        artifact_paths = set(evidence_manifest["artifact_paths"])
        self.assertTrue(EXTERNAL_REVIEW_BLOCKER_INPUTS.issubset(artifact_paths))
        for artifact_path in EXTERNAL_REVIEW_BLOCKER_INPUTS:
            artifact = json.loads((ROOT / artifact_path).read_text(encoding="utf-8"))
            self.assertFalse(artifact.get("live_order_ready", False))
            self.assertFalse(artifact.get("live_order_allowed", False))
            self.assertFalse(artifact.get("can_live_trade", False))

    def test_external_review_status_summaries_are_non_live_enabling(self):
        report = json.loads(
            (ROOT / "system/evidence/blocker_reports/MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE.blocker_report.json").read_text(
                encoding="utf-8"
            )
        )
        evidence_manifest = json.loads(
            (ROOT / "system/evidence/MVP4_EXTERNAL_BLOCKER.evidence_manifest.json").read_text(encoding="utf-8")
        )

        report_statuses = {item["artifact_path"]: item for item in report["external_review_input_statuses"]}
        manifest_statuses = {
            item["artifact_path"]: item for item in evidence_manifest["external_review_input_statuses"]
        }
        self.assertEqual(set(report_statuses), EXTERNAL_REVIEW_BLOCKER_INPUTS)
        self.assertEqual(set(manifest_statuses), EXTERNAL_REVIEW_BLOCKER_INPUTS)

        for artifact_path in EXTERNAL_REVIEW_BLOCKER_INPUTS:
            self.assertEqual(report_statuses[artifact_path], manifest_statuses[artifact_path])
            self.assertEqual(report_statuses[artifact_path]["artifact_sha256"], sha256_file(ROOT / artifact_path))
            self.assertNotEqual(report_statuses[artifact_path]["status"], "MISSING_STATUS")
            self.assertFalse(report_statuses[artifact_path]["usable_for_live_enabling"])
            self.assertFalse(report_statuses[artifact_path]["live_order_ready"])
            self.assertFalse(report_statuses[artifact_path]["live_order_allowed"])
            self.assertFalse(report_statuses[artifact_path]["can_live_trade"])


if __name__ == "__main__":
    unittest.main()
