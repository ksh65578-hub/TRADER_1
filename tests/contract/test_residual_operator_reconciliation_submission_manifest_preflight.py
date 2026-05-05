import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_reconciliation_intake_preflight import RECONCILIATION_MANIFEST_PATH
from trader1.reports.residual_operator_reconciliation_submission_manifest_preflight import (
    MANIFEST_EVIDENCE_PREFIX,
    build_residual_operator_reconciliation_submission_manifest_preflight_report,
    sha256_json,
    validate_residual_operator_reconciliation_submission_manifest_preflight_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
INTAKE_PREFLIGHT_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT.report.json"
)
SUBMISSION_MANIFEST_PREFLIGHT_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-SUBMISSION-MANIFEST-PREFLIGHT"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_valid_manifest(intake_preflight_report):
    source_reports = {
        str(item.get("role")): item for item in intake_preflight_report.get("source_reports", []) if isinstance(item, dict)
    }
    manifest = {
        "schema_id": "trader1.residual_operator_reconciliation_submission_manifest.v1",
        "manifest_id": "TEST_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST",
        "created_at_utc": "2026-05-06T00:00:00Z",
        "submission_scope": {
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "purpose": "OPERATOR_RECONCILIATION_REVIEW",
        },
        "source_intake_preflight_report_hash": intake_preflight_report["report_hash"],
        "source_review_cards_report_hash": source_reports["residual_operator_reconciliation_review_cards"]["report_hash"],
        "source_evidence_intake_report_hash": source_reports["residual_operator_evidence_intake_audit"]["report_hash"],
        "operator_attestation": {
            "attestation_type": "OPERATOR_RECONCILIATION_SUBMISSION_ONLY",
            "credential_values_excluded": True,
            "no_live_or_scale_mutation": True,
            "current_evidence_write_requested": False,
            "live_ready_write_requested": False,
            "live_config_mutation_requested": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
        "manifest_items": [],
        "control_assertions": [],
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_manifest": False,
        "live_ready_write_allowed": False,
        "live_config_mutation_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "manifest_hash": "",
    }
    for index, item in enumerate(intake_preflight_report["intake_items"], start=1):
        manifest["manifest_items"].append(
            {
                "intake_item_id": item["intake_item_id"],
                "review_card_id": item["review_card_id"],
                "priority_order": item["priority_order"],
                "cycle_id": item["cycle_id"],
                "required_resolution_evidence_kind": item["required_resolution_evidence_kind"],
                "source_decision_candidate_rollup_hash": item["source_decision_candidate_rollup_hash"],
                "evidence_artifact_path": f"{MANIFEST_EVIDENCE_PREFIX}item_{index:02d}.json",
                "evidence_artifact_sha256": "A" * 64,
                "operator_decision": "SUBMIT_FOR_RECONCILIATION_REVIEW",
                "decision_reason_code": "POST_RERUN_RECONCILIATION_REQUIRED",
                "current_evidence_write_requested": False,
                "accepted_for_reconciliation": False,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
    for control in intake_preflight_report["control_requirements"]:
        manifest["control_assertions"].append(
            {
                "control_id": control["control_id"],
                "control_order": control["control_order"],
                "blocker_code": control["blocker_code"],
                "operator_assertion_present": True,
                "accepted_for_reconciliation": False,
                "current_evidence_write_requested": False,
                "live_order_allowed": False,
                "scale_up_allowed": False,
            }
        )
    manifest["manifest_hash"] = sha256_json({key: value for key, value in manifest.items() if key != "manifest_hash"})
    return manifest


def write_manifest(root: Path, manifest):
    path = root / RECONCILIATION_MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


class ResidualOperatorReconciliationSubmissionManifestPreflightTest(unittest.TestCase):
    def source_inputs(self):
        return load_json(INTAKE_PREFLIGHT_REPORT_PATH), load_json(STATE_PATH)

    def build_report(self, root: Path):
        intake_preflight_report, state = self.source_inputs()
        return build_residual_operator_reconciliation_submission_manifest_preflight_report(
            intake_preflight_report,
            state,
            root=root,
            patch_id="TEST_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT",
            generated_at_utc="2026-05-06T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_missing_manifest_keeps_reconciliation_blocked(self):
        intake_preflight_report, state = self.source_inputs()
        with TemporaryDirectory() as tmpdir:
            report = self.build_report(Path(tmpdir))

        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["manifest_status"], "MISSING_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST")
        self.assertEqual(report["manifest_preflight_status"], "BLOCKED_MANIFEST_MISSING")
        self.assertEqual(report["manifest_schema_validation_status"], "NOT_RUN_MISSING")
        self.assertTrue(report["operator_submission_required"])
        self.assertFalse(report["operator_submission_present"])
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["operator_submission_accepted"])
        self.assertEqual(report["required_manifest_item_count"], 32)
        self.assertEqual(report["manifest_item_count"], 0)
        self.assertEqual(report["missing_manifest_item_count"], 32)
        self.assertEqual(report["required_control_count"], 4)
        self.assertEqual(report["manifest_control_count"], 0)
        self.assertEqual(report["missing_control_count"], 4)
        self.assertTrue(report["operator_no_action_needed_for_next_non_live_patch"])
        self.assertTrue(report["operator_action_required_for_gap_closure"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["live_ready_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_manifest_preflight_report(
                report,
                intake_preflight_report,
                state,
            ),
            [],
        )

    def test_structurally_valid_manifest_remains_review_only(self):
        intake_preflight_report, state = self.source_inputs()
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_manifest(root, build_valid_manifest(intake_preflight_report))
            report = self.build_report(root)

        self.assertEqual(report["manifest_status"], "PRESENT_STRUCTURAL_CHECK_ONLY")
        self.assertEqual(report["manifest_preflight_status"], "BLOCKED_MANIFEST_STRUCTURAL_REVIEW_ONLY")
        self.assertEqual(report["manifest_schema_validation_status"], "PASS_STRUCTURAL_ONLY")
        self.assertTrue(report["operator_submission_present"])
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["operator_submission_accepted"])
        self.assertTrue(report["manifest_structural_check_only"])
        self.assertEqual(report["manifest_item_count"], 32)
        self.assertEqual(report["missing_manifest_item_count"], 0)
        self.assertEqual(report["manifest_control_count"], 4)
        self.assertEqual(report["missing_control_count"], 0)
        self.assertEqual(report["unsafe_manifest_flag_count"], 0)
        self.assertEqual(report["path_policy_violation_count"], 0)
        self.assertEqual(report["source_hash_mismatch_count"], 0)
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["live_ready_write_allowed"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_manifest_preflight_report(
                report,
                intake_preflight_report,
                state,
            ),
            [],
        )

    def test_structural_manifest_errors_do_not_enable_acceptance(self):
        intake_preflight_report, state = self.source_inputs()
        manifest = build_valid_manifest(intake_preflight_report)
        manifest["manifest_items"].append(copy.deepcopy(manifest["manifest_items"][0]))
        manifest["manifest_items"][0]["evidence_artifact_path"] = "system/runtime/leaked.json"
        manifest["manifest_items"][0]["current_evidence_write_requested"] = True
        manifest["manifest_items"][0]["live_order_allowed"] = True
        manifest["source_intake_preflight_report_hash"] = "0" * 64
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_manifest(root, manifest)
            report = self.build_report(root)

        self.assertEqual(report["manifest_status"], "PRESENT_STRUCTURAL_INVALID")
        self.assertEqual(report["manifest_preflight_status"], "BLOCKED_MANIFEST_STRUCTURAL_ERRORS")
        self.assertEqual(report["manifest_schema_validation_status"], "FAIL_STRUCTURAL")
        self.assertGreater(report["duplicate_manifest_item_count"], 0)
        self.assertGreater(report["unsafe_manifest_flag_count"], 0)
        self.assertGreater(report["path_policy_violation_count"], 0)
        self.assertGreater(report["source_hash_mismatch_count"], 0)
        self.assertFalse(report["operator_submission_validated"])
        self.assertFalse(report["operator_submission_accepted"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_manifest_preflight_report(
                report,
                intake_preflight_report,
                state,
            ),
            [],
        )

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not SUBMISSION_MANIFEST_PREFLIGHT_REPORT_PATH.exists():
            self.skipTest("submission manifest preflight report has not been generated yet")
        intake_preflight_report, state = self.source_inputs()
        report = load_json(SUBMISSION_MANIFEST_PREFLIGHT_REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_reconciliation_submission_manifest_preflight_report(
                report,
                intake_preflight_report,
                state,
            ),
            [],
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_route(self):
        if not PATCH_PATH.exists():
            self.skipTest("submission manifest preflight patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(SUBMISSION_MANIFEST_PREFLIGHT_REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT_20260506_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_acceptance_or_permission_drift(self):
        intake_preflight_report, state = self.source_inputs()
        with TemporaryDirectory() as tmpdir:
            report = self.build_report(Path(tmpdir))
        tampered = copy.deepcopy(report)
        tampered["operator_submission_validated"] = True
        tampered["operator_submission_accepted"] = True
        tampered["current_evidence_write_allowed"] = True
        tampered["live_ready_write_allowed"] = True
        tampered["live_order_allowed"] = True
        tampered["manifest_template_preview"][0]["current_evidence_write_requested"] = True
        tampered["report_hash"] = "0" * 64

        errors = validate_residual_operator_reconciliation_submission_manifest_preflight_report(
            tampered,
            intake_preflight_report,
            state,
        )
        self.assertTrue(any("operator_submission_validated" in error for error in errors))
        self.assertTrue(any("operator_submission_accepted" in error for error in errors))
        self.assertTrue(any("current_evidence_write_allowed" in error for error in errors))
        self.assertTrue(any("live_ready_write_allowed" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("manifest template" in error for error in errors))
        self.assertTrue(any("report_hash" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
