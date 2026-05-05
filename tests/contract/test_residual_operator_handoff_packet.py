import copy
import json
import unittest
from pathlib import Path

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_handoff_packet import (
    build_residual_operator_handoff_packet_report,
    validate_residual_operator_handoff_packet_report,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
ACTION_PLAN_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN.report.json"
)
AUDIT_BINDING_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING.report.json"
)
PAPER_RERUN_READINESS_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS.report.json"
)
EXTERNAL_PREFLIGHT_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT.report.json"
)
HANDOFF_REPORT_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET.report.json"
)
PATCH_PATH = ROOT / "system" / "evidence" / "patch_results" / "MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET.patch_result.json"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-PACKET"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ResidualOperatorHandoffPacketTest(unittest.TestCase):
    def source_inputs(self):
        return (
            load_json(ACTION_PLAN_PATH),
            load_json(AUDIT_BINDING_PATH),
            load_json(PAPER_RERUN_READINESS_PATH),
            load_json(EXTERNAL_PREFLIGHT_PATH),
            load_json(STATE_PATH),
        )

    def build_report(self):
        action_plan, audit_binding, paper_rerun, external_preflight, state = self.source_inputs()
        return build_residual_operator_handoff_packet_report(
            action_plan,
            audit_binding,
            paper_rerun,
            external_preflight,
            state,
            patch_id="TEST_RESIDUAL_OPERATOR_HANDOFF_PACKET",
            generated_at_utc="2026-05-05T00:00:00Z",
            trader1_sha256="TEST_TRADER_HASH",
            agents_sha256="TEST_AGENTS_HASH",
        )

    def test_handoff_packets_cover_all_open_gaps_without_closing(self):
        action_plan, audit_binding, paper_rerun, external_preflight, state = self.source_inputs()
        report = self.build_report()

        self.assertEqual(report["open_gap_count"], 13)
        self.assertEqual(report["covered_gap_count"], 13)
        self.assertEqual(report["unassigned_gap_ids"], [])
        self.assertEqual(report["extra_gap_ids"], [])
        self.assertEqual(report["duplicate_gap_ids"], [])
        self.assertEqual(report["handoff_packet_count"], 6)
        self.assertEqual(report["blocked_handoff_packet_count"], 6)
        self.assertEqual(report["handoff_ready_count"], 0)
        self.assertEqual(report["external_intake_ready_count"], 0)
        self.assertEqual(report["paper_ledger_rerun_readiness_status"], "BLOCKED_RECONCILIATION_REQUIRED")
        self.assertEqual(report["handoff_status"], "BLOCKED_HANDOFF_REQUIRED")
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertFalse(report["gap_closure_allowed_by_this_patch"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_config_mutation_allowed"])

        packet_by_class = {packet["action_class"]: packet for packet in report["handoff_packets"]}
        self.assertIn("OPERATOR_RECONCILIATION_ACTION", packet_by_class)
        self.assertIn("EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION", packet_by_class)
        self.assertEqual(
            packet_by_class["EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION"]["extra_status"][
                "external_preflight_status"
            ],
            "BLOCKED_EXTERNAL_EVIDENCE_MISSING",
        )
        self.assertEqual(
            packet_by_class["PAPER_LEDGER_RERUN_RECONCILIATION_ACTION"]["extra_status"][
                "paper_ledger_rerun_readiness_status"
            ],
            "BLOCKED_RECONCILIATION_REQUIRED",
        )
        for packet in report["handoff_packets"]:
            self.assertEqual(packet["handoff_status"], "BLOCKED_HANDOFF_REQUIRED")
            self.assertFalse(packet["evidence_ready_for_closure"])
            self.assertFalse(packet["current_evidence_write_allowed"])
            self.assertFalse(packet["gap_closure_allowed_by_this_patch"])
            self.assertFalse(packet["live_order_allowed"])
            self.assertFalse(packet["scale_up_allowed"])

        self.assertEqual(
            validate_residual_operator_handoff_packet_report(
                report,
                action_plan,
                audit_binding,
                paper_rerun,
                external_preflight,
                state,
            ),
            [],
        )

    def test_generated_report_matches_schema_and_keeps_permissions_false(self):
        if not HANDOFF_REPORT_PATH.exists():
            self.skipTest("residual operator handoff packet report has not been generated yet")
        action_plan, audit_binding, paper_rerun, external_preflight, state = self.source_inputs()
        report = load_json(HANDOFF_REPORT_PATH)
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)

        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)
        self.assertEqual(
            validate_residual_operator_handoff_packet_report(
                report,
                action_plan,
                audit_binding,
                paper_rerun,
                external_preflight,
                state,
            ),
            [],
        )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(report[field])
            self.assertFalse(state[field])

    def test_generated_patch_preserves_residual_route(self):
        if not PATCH_PATH.exists():
            self.skipTest("residual operator handoff packet patch has not been generated yet")
        state = load_json(STATE_PATH)
        patch_result = load_json(PATCH_PATH)
        report = load_json(HANDOFF_REPORT_PATH)

        self.assertEqual(patch_result["patch_id"], "MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET_20260505_001")
        self.assertEqual(patch_result["next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(state["next_allowed_task_class"], NEXT_TASK_CLASS)
        self.assertIn(REQUIREMENT_ID, state["completed_requirement_ids"])
        self.assertEqual(report["selected_next_task_class"], NEXT_TASK_CLASS)
        self.assertEqual(report["handoff_status"], "BLOCKED_HANDOFF_REQUIRED")
        self.assertFalse(patch_result["live_order_ready_after"])
        self.assertFalse(patch_result["live_order_allowed_after"])
        self.assertFalse(patch_result["can_live_trade_after"])
        self.assertFalse(patch_result["scale_up_allowed_after"])

    def test_validator_rejects_gap_closure_or_live_permission(self):
        action_plan, audit_binding, paper_rerun, external_preflight, state = self.source_inputs()
        report = self.build_report()
        tampered = copy.deepcopy(report)
        tampered["handoff_ready_count"] = 1
        tampered["current_evidence_write_allowed"] = True
        tampered["gap_closure_allowed_by_this_patch"] = True
        tampered["handoff_packets"][0]["evidence_ready_for_closure"] = True
        tampered["handoff_packets"][0]["live_order_allowed"] = True

        errors = validate_residual_operator_handoff_packet_report(
            tampered,
            action_plan,
            audit_binding,
            paper_rerun,
            external_preflight,
            state,
        )
        self.assertTrue(any("handoff_ready_count" in error for error in errors))
        self.assertTrue(any("current_evidence_write_allowed" in error for error in errors))
        self.assertTrue(any("gap_closure_allowed_by_this_patch" in error for error in errors))
        self.assertTrue(any("evidence_ready_for_closure" in error for error in errors))
        self.assertTrue(any("live_order_allowed" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
