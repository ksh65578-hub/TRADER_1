import unittest
from pathlib import Path

from tools.run_upbit_paper_runtime_evidence_collection_profile import (
    build_upbit_paper_runtime_evidence_collection_profile_report,
    run_upbit_paper_runtime_evidence_collection_profile,
    upbit_paper_runtime_evidence_collection_profile_hash,
    validate_upbit_paper_runtime_evidence_collection_profile_report,
    write_upbit_paper_runtime_evidence_collection_profile_report,
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
        self.assertEqual(depth["observed_runtime_modes"], ["PAPER", "SHADOW"])
        self.assertIn("SHADOW", depth["missing_runtime_modes"])
        self.assertEqual(depth["observed_cycle_count"], report["accepted_cycle_sample_count"])
        self.assertEqual(depth["minimum_cycle_count"], report["min_actual_long_run_cycle_count"])
        self.assertEqual(depth["missing_cycle_count"], report["min_actual_long_run_cycle_count"] - report["accepted_cycle_sample_count"])
        self.assertEqual(depth["observed_span_seconds"], report["observed_span_seconds"])
        self.assertEqual(depth["minimum_span_seconds"], report["min_actual_long_run_span_seconds"])
        self.assertGreater(depth["missing_span_seconds"], 0)
        self.assertEqual(depth["shadow_runtime_depth_status"], "PRESENT_NOT_LONG_RUN")
        self.assertEqual(depth["paper_shadow_pairing_status"], "PAIRED_NOT_LONG_RUN")
        mode_depth = depth["runtime_mode_depth_evidence"]
        self.assertEqual(mode_depth["status"], "BLOCKED_FOR_PER_MODE_LONG_RUN_DEPTH")
        self.assertEqual(mode_depth["blocker_code"], "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")
        self.assertEqual(mode_depth["required_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(mode_depth["missing_long_run_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(mode_depth["missing_long_run_mode_count"], 2)
        self.assertFalse(mode_depth["all_required_modes_long_run_validated"])
        paper_depth = mode_depth["mode_depths"]["paper"]
        shadow_depth = mode_depth["mode_depths"]["shadow"]
        self.assertEqual(paper_depth["source_status"], "PRESENT_BOUNDED_NOT_LONG_RUN")
        self.assertEqual(shadow_depth["source_status"], "PRESENT_BLOCKER_ONLY_NOT_LONG_RUN")
        self.assertEqual(paper_depth["observed_cycle_count"], report["accepted_cycle_sample_count"])
        self.assertEqual(paper_depth["missing_cycle_count"], report["min_actual_long_run_cycle_count"] - report["accepted_cycle_sample_count"])
        self.assertEqual(shadow_depth["observed_cycle_count"], report["completed_cycle_count"])
        self.assertEqual(
            shadow_depth["missing_cycle_count"],
            report["min_actual_long_run_cycle_count"] - shadow_depth["observed_cycle_count"],
        )
        self.assertEqual(
            shadow_depth["missing_span_seconds"],
            report["min_actual_long_run_span_seconds"] - shadow_depth["observed_span_seconds"],
        )
        self.assertFalse(paper_depth["counts_as_actual_long_run_evidence"])
        self.assertFalse(shadow_depth["counts_as_actual_long_run_evidence"])
        self.assertFalse(depth["bounded_profile_counts_as_long_run_evidence"])
        self.assertFalse(depth["dashboard_display_counts_as_long_run_evidence"])
        plan = report["non_live_collection_plan"]
        self.assertEqual(plan["plan_status"], "READY_TO_CONTINUE_NON_LIVE_COLLECTION")
        self.assertEqual(plan["plan_role"], "NON_LIVE_RUNTIME_COLLECTION_CONTINUATION_PLAN")
        self.assertEqual(plan["required_next_runtime_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(plan["recommended_next_paper_batch_cycle_count"], 20)
        self.assertEqual(plan["max_safe_paper_batch_cycle_count"], 20)
        self.assertEqual(plan["paper_remaining_span_seconds"], paper_depth["missing_span_seconds"])
        self.assertEqual(plan["paper_remaining_cycle_count"], paper_depth["missing_cycle_count"])
        self.assertEqual(plan["shadow_remaining_span_seconds"], shadow_depth["missing_span_seconds"])
        self.assertEqual(plan["shadow_remaining_cycle_count"], shadow_depth["missing_cycle_count"])
        self.assertEqual(plan["minimum_cycle_wall_clock_spacing_seconds"], 30)
        self.assertEqual(
            plan["estimated_wall_clock_seconds_remaining"],
            max(plan["paper_remaining_span_seconds"], plan["shadow_remaining_span_seconds"]),
        )
        self.assertTrue(plan["shadow_collection_required"])
        self.assertFalse(plan["counts_as_actual_long_run_evidence"])
        self.assertFalse(plan["current_evidence_write_allowed"])
        self.assertFalse(plan["promotion_eligible"])
        self.assertFalse(plan["live_order_allowed"])
        self.assertFalse(plan["scale_up_allowed"])
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
        self.assertEqual(report["non_live_collection_plan"]["plan_status"], "BLOCKED_FOR_RECONCILIATION")
        self.assertEqual(report["non_live_collection_plan"]["recommended_next_paper_batch_cycle_count"], 0)
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

    def test_profile_blocks_collection_plan_false_long_run_or_batch_drift(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
        report["non_live_collection_plan"]["counts_as_actual_long_run_evidence"] = True
        report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)

        false_long_run_result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)
        self.assertEqual(false_long_run_result.status, "BLOCKED")
        self.assertEqual(false_long_run_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        report["non_live_collection_plan"]["counts_as_actual_long_run_evidence"] = False
        report["non_live_collection_plan"]["recommended_next_paper_batch_cycle_count"] = 21
        report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)
        batch_result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)
        self.assertEqual(batch_result.status, "BLOCKED")
        self.assertEqual(batch_result.blocker_code, "RUNTIME_BUDGET_EXCEEDED")

    def test_profile_blocks_hidden_long_run_collection_depth_gap(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
        report["long_run_collection_depth"]["missing_runtime_modes"] = []
        report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)

        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")

    def test_profile_blocks_shadow_pairing_drift(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
        report["long_run_collection_depth"]["paper_shadow_pairing_status"] = "MISSING"
        report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)

        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")

    def test_profile_blocks_hidden_per_mode_long_run_depth_gap(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
        report["long_run_collection_depth"]["runtime_mode_depth_evidence"]["missing_long_run_modes"] = ["SHADOW"]
        report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)

        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")

    def test_profile_blocks_per_mode_bounded_evidence_as_actual_long_run(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
        report["long_run_collection_depth"]["runtime_mode_depth_evidence"]["mode_depths"]["paper"][
            "counts_as_actual_long_run_evidence"
        ] = True
        report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)

        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

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

    def test_profile_blocks_duplicate_runtime_sample_history_as_reconciliation_required(self):
        from tempfile import TemporaryDirectory
        import json

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = build_upbit_paper_runtime_evidence_collection_profile_report(
                root=root,
                loop_id="profile-duplicate-sample-a",
                requested_cycle_count=1,
            )
            paper_runtime_dir = (
                root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime"
            )
            first_loop_path = paper_runtime_dir / f"{first['loop_id']}.persistent_loop_report.json"
            duplicate_path = paper_runtime_dir / "profile-duplicate-sample-copy.persistent_loop_report.json"
            duplicate_path.write_text(first_loop_path.read_text(encoding="utf-8"), encoding="utf-8")

            report = build_upbit_paper_runtime_evidence_collection_profile_report(
                root=root,
                loop_id="profile-duplicate-sample-b",
                requested_cycle_count=1,
            )
        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["runtime_sample_status"], "BLOCKED")
        self.assertIn("RECONCILIATION_REQUIRED", report["blockers"])
        self.assertFalse(json.loads(json.dumps(report))["live_order_allowed"])

    def test_profile_accepts_cumulative_sample_history_beyond_current_bounded_loop(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = build_upbit_paper_runtime_evidence_collection_profile_report(
                root=root,
                loop_id="profile-cumulative-sample-history-a",
                requested_cycle_count=1,
            )
            first_result = validate_upbit_paper_runtime_evidence_collection_profile_report(first)
            second = build_upbit_paper_runtime_evidence_collection_profile_report(
                root=root,
                loop_id="profile-cumulative-sample-history-b",
                requested_cycle_count=1,
            )
        second_result = validate_upbit_paper_runtime_evidence_collection_profile_report(second)

        self.assertEqual(first_result.status, "PASS")
        self.assertEqual(second_result.status, "PASS")
        self.assertEqual(second["status"], "PASS")
        self.assertGreater(second["accepted_cycle_sample_count"], second["completed_cycle_count"])
        self.assertEqual(second["runtime_sample_status"], "COLLECTING")
        self.assertFalse(second["live_order_allowed"])

    def test_profile_accumulates_shadow_short_window_runtime_history(self):
        from tempfile import TemporaryDirectory
        import json

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = build_upbit_paper_runtime_evidence_collection_profile_report(
                root=root,
                loop_id="profile-shadow-history-a",
                requested_cycle_count=2,
            )
            second = build_upbit_paper_runtime_evidence_collection_profile_report(
                root=root,
                loop_id="profile-shadow-history-b",
                requested_cycle_count=3,
            )
            history_path = (
                root
                / "system/runtime/upbit/krw_spot/shadow/mvp1_upbit_paper_launcher/shadow_runtime_sample_history.json"
            )
            history = json.loads(history_path.read_text(encoding="utf-8"))

        first_result = validate_upbit_paper_runtime_evidence_collection_profile_report(first)
        second_result = validate_upbit_paper_runtime_evidence_collection_profile_report(second)
        shadow_depth = second["long_run_collection_depth"]["runtime_mode_depth_evidence"]["mode_depths"]["shadow"]

        self.assertEqual(first_result.status, "PASS")
        self.assertEqual(second_result.status, "PASS")
        self.assertEqual(history["history_status"], "COLLECTING")
        self.assertEqual(history["accepted_sample_count"], 2)
        self.assertEqual(history["accepted_cycle_sample_count"], 5)
        self.assertEqual(shadow_depth["observed_cycle_count"], 5)
        self.assertEqual(shadow_depth["missing_cycle_count"], second["min_actual_long_run_cycle_count"] - 5)
        self.assertFalse(history["live_order_allowed"])
        self.assertFalse(second["live_order_allowed"])

    def test_profile_uses_existing_short_window_shadow_runtime_orchestration_without_live_permission(self):
        from tempfile import TemporaryDirectory
        import json

        from trader1.research.shadow.shadow_observation import build_shadow_observation_report
        from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
            build_shadow_observation_actual_runtime_harness_report,
        )
        from trader1.research.shadow.shadow_observation_persistent_runtime import (
            build_shadow_observation_persistent_runtime_report_from_paper_loop,
        )
        from trader1.research.shadow.shadow_observation_runtime_orchestration import (
            build_shadow_observation_runtime_orchestration_report,
        )
        from trader1.research.shadow.shadow_observation_scheduler import build_shadow_observation_scheduler_guard_report
        from trader1.research.shadow.shadow_observation_stream import build_shadow_observation_stream_report
        from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle

        session_id = "mvp1_upbit_paper_launcher"
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_profile = build_upbit_paper_runtime_evidence_collection_profile_report(
                root=root,
                loop_id="profile-shadow-short-window-source",
                requested_cycle_count=2,
            )
            source_loop_path = (
                root
                / "system/runtime/upbit/krw_spot/paper"
                / session_id
                / "paper_runtime"
                / f"{source_profile['loop_id']}.persistent_loop_report.json"
            )
            source_loop = json.loads(source_loop_path.read_text(encoding="utf-8"))
            observations = []
            for index in range(3):
                paper_gate = build_upbit_operational_paper_cycle(
                    operation_gate_id="profile-shadow-short-window-paper-gate",
                    session_id=f"profile-shadow-short-window-paper-{index}",
                    requested_entry=True,
                )
                observations.append(
                    build_shadow_observation_report(
                        observation_id=f"profile-shadow-short-window-observation-{index}",
                        paper_operation_gate_report=paper_gate,
                        shadow_session_id=f"profile-shadow-short-window-shadow-{index}",
                        shadow_sample_count=30,
                    )
                )
            stream = build_shadow_observation_stream_report(
                stream_id="profile-shadow-short-window-stream",
                observations=observations,
                min_required_observation_count=3,
                min_required_evidence_span_hours=24,
                evidence_span_hours=24,
            )
            scheduler = build_shadow_observation_scheduler_guard_report(
                scheduler_id="profile-shadow-short-window-scheduler",
                stream_report=stream,
                writer_id="profile-shadow-short-window-writer",
                active_writer_id="profile-shadow-short-window-writer",
            )
            persistent = build_shadow_observation_persistent_runtime_report_from_paper_loop(
                runtime_id=session_id,
                scheduler_guard_report=scheduler,
                source_paper_loop_report=source_loop,
                observed_runtime_seconds=2,
                max_runtime_seconds=300,
            )
            harness = build_shadow_observation_actual_runtime_harness_report(
                harness_id=session_id,
                requested_cycle_count=int(source_loop["completed_cycle_count"]),
                completed_cycle_count=int(source_loop["completed_cycle_count"]),
                observations_per_cycle=2,
                measured_runtime_seconds=2,
                runtime_measurement_source="PAPER_LOOP_TIMESTAMP_SPAN_VERIFIED",
                measured_runtime_seconds_verified=True,
                source_runtime_report=persistent,
            )
            orchestration = build_shadow_observation_runtime_orchestration_report(
                orchestration_id=session_id,
                persistent_runtime_report=persistent,
                actual_runtime_harness_report=harness,
            )
            orchestration_path = (
                root / "system/runtime/upbit/krw_spot/shadow" / session_id / "runtime_orchestration_report.json"
            )
            orchestration_path.parent.mkdir(parents=True, exist_ok=True)
            orchestration_path.write_text(json.dumps(orchestration, indent=2) + "\n", encoding="utf-8")

            report = build_upbit_paper_runtime_evidence_collection_profile_report(
                root=root,
                loop_id="profile-shadow-short-window-consumer",
                requested_cycle_count=1,
            )

        result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)
        shadow_depth = report["long_run_collection_depth"]["runtime_mode_depth_evidence"]["mode_depths"]["shadow"]

        self.assertEqual(result.status, "PASS")
        self.assertEqual(shadow_depth["source_status"], "PRESENT_BLOCKER_ONLY_NOT_LONG_RUN")
        self.assertGreaterEqual(shadow_depth["observed_span_seconds"], 2)
        self.assertGreaterEqual(shadow_depth["observed_cycle_count"], 5)
        self.assertEqual(
            shadow_depth["missing_span_seconds"],
            report["min_actual_long_run_span_seconds"] - shadow_depth["observed_span_seconds"],
        )
        self.assertEqual(
            shadow_depth["missing_cycle_count"],
            report["min_actual_long_run_cycle_count"] - shadow_depth["observed_cycle_count"],
        )
        self.assertEqual(
            report["non_live_collection_plan"]["shadow_remaining_cycle_count"],
            report["min_actual_long_run_cycle_count"] - shadow_depth["observed_cycle_count"],
        )
        self.assertFalse(shadow_depth["counts_as_actual_long_run_evidence"])
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_profile_writer_persists_source_bound_runtime_artifacts(self):
        from tempfile import TemporaryDirectory
        import json

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "profile.json"
            report, result = write_upbit_paper_runtime_evidence_collection_profile_report(
                root=root,
                output=output,
                loop_id="profile-source-bound-runtime-artifacts",
                requested_cycle_count=1,
            )

            runtime_root = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher"
            sample_history_path = runtime_root / "paper_runtime/upbit_paper_runtime_sample_history.json"
            idempotency_path = runtime_root / "ledger/upbit_paper_ledger_idempotency_runtime_evidence_report.json"
            loop_path = runtime_root / "paper_runtime/profile-source-bound-runtime-artifacts.persistent_loop_report.json"

            persisted_profile = json.loads(output.read_text(encoding="utf-8"))
            persisted_history = json.loads(sample_history_path.read_text(encoding="utf-8"))
            persisted_idempotency = json.loads(idempotency_path.read_text(encoding="utf-8"))
            loop_exists = loop_path.exists()

        self.assertEqual(result.status, "PASS")
        self.assertEqual(persisted_profile["profile_hash"], report["profile_hash"])
        self.assertTrue(loop_exists)
        self.assertEqual(persisted_history["history_hash"], report["runtime_sample_history_hash"])
        self.assertEqual(persisted_idempotency["evidence_hash"], report["ledger_idempotency_evidence_hash"])
        self.assertFalse(report["current_evidence_write_allowed"])
        self.assertFalse(report["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
