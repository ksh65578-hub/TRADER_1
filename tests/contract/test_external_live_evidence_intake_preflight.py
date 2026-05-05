import copy
import json
import unittest
from pathlib import Path

from trader1.reports.external_live_evidence_intake_preflight import (
    BLOCKED_REQUIREMENT_IDS,
    build_external_live_evidence_intake_preflight_report,
    validate_external_live_evidence_intake_preflight_report,
)
from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
SOURCE_MANIFEST_PATH = ROOT / "system" / "evidence" / "MVP4_EXTERNAL_BLOCKER.evidence_manifest.json"
REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "audit_reports"
    / "MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT.report.json"
)
PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT.patch_result.json"
)
REQUIREMENT_ID = "REQ-MVP4-EXTERNAL-LIVE-EVIDENCE-INTAKE-PREFLIGHT"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ExternalLiveEvidenceIntakePreflightTest(unittest.TestCase):
    def source_inputs(self):
        return load_json(SOURCE_MANIFEST_PATH), load_json(STATE_PATH)

    def build_report(self):
        manifest, state = self.source_inputs()
        return build_external_live_evidence_intake_preflight_report(
            manifest,
            state,
            patch_id="TEST_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
            source_manifest_path="system/evidence/MVP4_EXTERNAL_BLOCKER.evidence_manifest.json",
            source_manifest_sha256="A" * 64,
        )

    def test_current_external_inputs_are_preflight_blocked_without_live_permission(self):
        manifest, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["blocked_requirement_ids"], sorted(BLOCKED_REQUIREMENT_IDS))
        self.assertEqual(report["blocked_requirement_count"], 4)
        self.assertEqual(report["evidence_item_count"], 4)
        self.assertEqual(report["intake_ready_count"], 0)
        self.assertEqual(report["missing_or_unusable_count"], 4)
        self.assertEqual(report["preflight_status"], "BLOCKED_EXTERNAL_EVIDENCE_MISSING")
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(report["external_evidence_collection_performed"])
        self.assertFalse(report["credential_use_allowed"])
        self.assertFalse(report["api_call_performed"])
        self.assertFalse(report["live_order_submitted"])
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])

        by_requirement = {item["requirement_id"]: item for item in report["evidence_items"]}
        self.assertEqual(
            by_requirement["REQ-MVP4-OFFICIAL-API-PASS-EVIDENCE"]["source_status"],
            "UNVERIFIED",
        )
        self.assertEqual(
            by_requirement["REQ-MVP4-READ-ONLY-ACCOUNT-SNAPSHOT-EVIDENCE"]["source_status"],
            "UNVERIFIED",
        )
        self.assertEqual(by_requirement["REQ-MVP4-OPERATOR-APPROVAL-EVIDENCE"]["source_status"], "MISSING")
        self.assertEqual(by_requirement["REQ-MVP4-READ-ONLY-BURN-IN-EVIDENCE"]["source_status"], "MISSING")
        for item in report["evidence_items"]:
            self.assertFalse(item["usable_for_live_enabling"])
            self.assertFalse(item["live_order_ready"])
            self.assertFalse(item["live_order_allowed"])
            self.assertFalse(item["can_live_trade"])
            self.assertFalse(item["scale_up_allowed"])

        self.assertEqual(validate_external_live_evidence_intake_preflight_report(report, manifest, state), [])

    def test_generated_report_matches_schema_and_preserves_false_flags(self):
        if not REPORT_PATH.exists():
            self.skipTest("external live evidence intake preflight report has not been generated yet")
        manifest, state = self.source_inputs()
        report = load_json(REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(validate_external_live_evidence_intake_preflight_report(report, manifest, state), [])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_keeps_residual_route_and_external_blockers(self):
        if not PATCH_PATH.exists():
            self.skipTest("external live evidence intake preflight patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(REPORT_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT_20260505_001",
        )
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(state["blocked_requirement_ids"], sorted(BLOCKED_REQUIREMENT_IDS))
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_evidence_closure_or_live_permission(self):
        manifest, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["intake_ready_count"] = 1
        tampered["missing_or_unusable_count"] = 3
        tampered["evidence_items"][0]["usable_for_live_enabling"] = True
        tampered["evidence_items"][0]["live_order_allowed"] = True
        tampered["gap_closure_allowed_by_this_patch"] = True

        errors = validate_external_live_evidence_intake_preflight_report(tampered, manifest, state)
        self.assertTrue(any("intake_ready_count" in error for error in errors))
        self.assertTrue(any("missing_or_unusable_count" in error for error in errors))
        self.assertTrue(any("usable_for_live_enabling" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))
        self.assertTrue(any("gap_closure_allowed_by_this_patch" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
