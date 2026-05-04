import unittest
from pathlib import Path

from tools.run_upbit_paper_runtime_evidence_collection_profile import (
    build_upbit_paper_runtime_evidence_collection_profile_report,
    run_upbit_paper_runtime_evidence_collection_profile,
    upbit_paper_runtime_evidence_collection_profile_hash,
    validate_upbit_paper_runtime_evidence_collection_profile_report,
)
from trader1.validation.schema_instance import load_schema_bundle, schema_for_instance, validate_instance_against_schema


ROOT = Path(__file__).resolve().parents[2]


class UpbitPaperRuntimeEvidenceCollectionProfileTest(unittest.TestCase):
    def test_profile_runs_bounded_paper_runtime_evidence_and_keeps_live_blocked(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=2)
        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["loop_status"], "PASS")
        self.assertEqual(report["recovery_guard_status"], "PASS")
        self.assertEqual(report["runtime_sample_history_validation_status"], "PASS")
        self.assertEqual(report["runtime_sample_status"], "COLLECTING")
        self.assertEqual(report["accepted_cycle_sample_count"], 2)
        self.assertEqual(report["unique_runtime_cycle_hash_count"], 2)
        self.assertEqual(report["ledger_runtime_evidence_status"], "PASS")
        self.assertEqual(report["idempotency_status"], "PASS")
        self.assertEqual(report["reconciliation_status"], "PASS")
        self.assertEqual(report["source_ledger_jsonl_count"], 2)
        self.assertEqual(report["recomputed_filled_order_count"], 2)
        depth = report["long_run_collection_depth"]
        self.assertEqual(depth["status"], "BLOCKED_FOR_LONG_RUN_COLLECTION_DEPTH")
        self.assertEqual(depth["blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        self.assertEqual(depth["required_runtime_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(depth["observed_runtime_modes"], ["PAPER"])
        self.assertEqual(depth["missing_runtime_modes"], ["SHADOW"])
        self.assertEqual(depth["observed_cycle_count"], report["accepted_cycle_sample_count"])
        self.assertEqual(depth["minimum_cycle_count"], report["min_actual_long_run_cycle_count"])
        self.assertEqual(depth["missing_cycle_count"], report["min_actual_long_run_cycle_count"] - report["accepted_cycle_sample_count"])
        self.assertEqual(depth["observed_span_seconds"], report["observed_span_seconds"])
        self.assertEqual(depth["minimum_span_seconds"], report["min_actual_long_run_span_seconds"])
        self.assertGreater(depth["missing_span_seconds"], 0)
        self.assertEqual(depth["shadow_runtime_depth_status"], "MISSING")
        self.assertEqual(depth["paper_shadow_pairing_status"], "MISSING")
        self.assertFalse(depth["bounded_profile_counts_as_long_run_evidence"])
        self.assertFalse(depth["dashboard_display_counts_as_long_run_evidence"])
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["actual_long_run_evidence_created"])
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(report, schema_bundle)
        self.assertIsNotNone(schema)
        schema_result = validate_instance_against_schema(report, schema, schema_bundle)
        self.assertEqual(schema_result.status, "PASS", schema_result.errors)

    def test_profile_blocks_duplicate_ledger_events_as_reconciliation_required(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(
            requested_cycle_count=1,
            duplicate_ledger_events=True,
        )
        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["ledger_runtime_evidence_status"], "BLOCKED")
        self.assertEqual(report["idempotency_status"], "BLOCKED")
        self.assertIn("RECONCILIATION_REQUIRED", report["blockers"])
        self.assertGreater(report["duplicate_event_id_count"], 0)
        self.assertFalse(report["live_order_allowed"])

    def test_profile_blocks_live_or_long_run_flag_drift(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
        report["live_order_allowed"] = True
        report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)

        live_result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        report["live_order_allowed"] = False
        report["long_run_evidence_eligible"] = True
        report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)
        long_run_result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)
        self.assertEqual(long_run_result.status, "BLOCKED")
        self.assertEqual(long_run_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_profile_blocks_hidden_long_run_collection_depth_gap(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
        report["long_run_collection_depth"]["missing_runtime_modes"] = []
        report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)

        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")

    def test_profile_detects_long_run_collection_depth_count_drift(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
        report["long_run_collection_depth"]["missing_cycle_count"] = 0
        report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)

        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_profile_detects_hash_mutation(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
        report["accepted_cycle_sample_count"] += 1

        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_builder_can_use_explicit_root_for_evidence_fixture_generation(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            report = build_upbit_paper_runtime_evidence_collection_profile_report(
                root=Path(tmp),
                loop_id="profile-explicit-root",
                requested_cycle_count=1,
            )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["completed_cycle_count"], 1)
        self.assertFalse(report["current_evidence_write_allowed"])


if __name__ == "__main__":
    unittest.main()
