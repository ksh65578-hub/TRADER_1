import unittest
from pathlib import Path

from trader1.research.shadow.shadow_runner import (
    build_paper_shadow_evidence_accumulation_report,
    paper_shadow_evidence_actionability_fields,
    paper_shadow_evidence_hash,
    validate_paper_shadow_evidence_accumulation_report,
)
from trader1.validation.mvp0_validators import (
    _paper_shadow_evidence_accumulation_errors,
    paper_shadow_evidence_accumulation_validator,
)


FIXTURE_DIR = Path("tests/validators/fixtures")


class PaperShadowEvidenceAccumulationValidatorTest(unittest.TestCase):
    def test_valid_evidence_passes_for_paper_scorecard_only(self):
        report = build_paper_shadow_evidence_accumulation_report(evidence_report_id="paper-shadow-pass")
        result = validate_paper_shadow_evidence_accumulation_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertTrue(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "ALLOW_RANKING")
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertEqual(
            report["long_run_blocker_code"],
            "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
        )
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertEqual(
            {binding["source_role"] for binding in report["source_evidence_bindings"]},
            {"PAPER_OPERATION", "SHADOW_OBSERVATION"},
        )
        self.assertEqual(report["evidence_span_source"], "EXPLICIT_OPERATOR_SUPPLIED")
        self.assertEqual(report["evidence_span_source_status"], "PASS")
        self.assertEqual(report["supporting_source_window_count"], 0)
        self.assertEqual(report["paper_shadow_actionability_version"], "paper_shadow_actionability.v1")
        self.assertEqual(report["scorecard_input_truth_status"], "PAPER_SCORECARD_INPUT_READY_ONLY")
        self.assertEqual(report["evidence_actionability_status"], "SCORECARD_READY_COLLECT_PAIRED_WINDOWS")
        self.assertEqual(report["primary_collection_deficit_code"], "PAIRED_WINDOW_DEFICIT")
        self.assertEqual(report["next_collection_action"], "RUN_PAIRED_PAPER_SHADOW_WINDOWS")
        self.assertEqual(report["paper_sample_deficit"], 0)
        self.assertEqual(report["shadow_sample_deficit"], 0)
        self.assertEqual(report["evidence_window_deficit"], 20)
        self.assertEqual(report["evidence_span_hours_deficit"], 116)
        self.assertEqual(report["actual_runtime_source_deficit"], 2)

    def test_insufficient_samples_block_scorecard_input(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-low-sample",
            paper_sample_count=2,
            shadow_sample_count=2,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SAMPLE_INSUFFICIENT")
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertEqual(report["scorecard_input_truth_status"], "BLOCKED_NOT_SCORECARD_INPUT")
        self.assertEqual(report["evidence_actionability_status"], "COLLECT_PAPER_SAMPLES")
        self.assertEqual(report["primary_collection_deficit_code"], "PAPER_SAMPLE_DEFICIT")
        self.assertEqual(report["next_collection_action"], "RUN_MORE_PAPER_SAMPLE_WINDOWS")
        self.assertEqual(report["paper_sample_deficit"], 28)
        self.assertEqual(report["shadow_sample_deficit"], 28)

    def test_shadow_sample_deficit_is_actionable_when_paper_is_ready(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-low-shadow-sample",
            paper_sample_count=30,
            shadow_sample_count=4,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SAMPLE_INSUFFICIENT")
        self.assertEqual(report["evidence_actionability_status"], "COLLECT_SHADOW_SAMPLES")
        self.assertEqual(report["primary_collection_deficit_code"], "SHADOW_SAMPLE_DEFICIT")
        self.assertEqual(report["next_collection_action"], "RUN_MORE_SHADOW_SAMPLE_WINDOWS")
        self.assertEqual(report["paper_sample_deficit"], 0)
        self.assertEqual(report["shadow_sample_deficit"], 26)

    def test_binance_scope_blocks_mvp4_scorecard_input(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-binance-scope",
            exchange="BINANCE",
            market_type="SPOT",
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])

    def test_artifact_paths_must_match_session_scope(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-artifact-path-scope-drift"
        )
        drifted_paper_path = (
            f"system/runtime/upbit/krw_spot/paper/{report['paper_session_id']}_drift/"
            "paper_operation_gate_report.json"
        )
        report["paper_artifact_path"] = drifted_paper_path
        report["source_evidence_bindings"][0]["artifact_path"] = drifted_paper_path
        report["blockers"] = [
            {
                "code": "SNAPSHOT_SCOPE_MISMATCH",
                "severity": "HIGH",
                "message": "paper/shadow evidence artifact path scope mismatch",
            }
        ]
        report["primary_blocker_code"] = "SNAPSHOT_SCOPE_MISMATCH"
        report["evidence_chain_complete"] = False
        report["scorecard_input_eligible"] = False
        report["optimizer_ranking_action"] = "BLOCK_RANKING"
        report.update(paper_shadow_evidence_actionability_fields(report))
        report["evidence_hash"] = paper_shadow_evidence_hash(report)

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")
        self.assertTrue(any("artifact path scope mismatch" in error for error in errors), errors)

    def test_stale_artifact_blocks_scorecard_input(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-stale",
            paper_artifact_age_seconds=1200,
            shadow_artifact_age_seconds=1200,
            max_artifact_age_seconds=900,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DATA_QUALITY_INSUFFICIENT")

    def test_missing_reason_evidence_blocks_scorecard_input(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-missing-reason",
            entry_reason_count=0,
            no_trade_reason_count=0,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")
        self.assertEqual(report["evidence_actionability_status"], "COLLECT_REASON_AND_COST_EVIDENCE")
        self.assertEqual(report["primary_collection_deficit_code"], "REASON_OR_COST_EVIDENCE_DEFICIT")
        self.assertEqual(report["next_collection_action"], "RECORD_ENTRY_NO_TRADE_AND_COST_REASONS")
        self.assertEqual(report["reason_coverage_deficit_count"], 2)

    def test_short_window_cannot_claim_long_run_evidence(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-false-long-run",
            long_run_evidence_eligible=True,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SAMPLE_INSUFFICIENT")
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertTrue(
            any("long-run evidence eligibility claimed before minimum window/span coverage" in error for error in errors),
            errors,
        )

    def test_long_run_claim_requires_per_window_supporting_sources(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-unbacked-long-run",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertTrue(
            any("per-window PAPER and SHADOW supporting source ids" in error for error in errors),
            errors,
        )

        tampered = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-tampered-unbacked-long-run",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            long_run_evidence_eligible=False,
        )
        tampered["long_run_evidence_eligible"] = True
        tampered["long_run_blocker_code"] = None
        tampered["blockers"] = []
        tampered["evidence_chain_complete"] = True
        tampered["scorecard_input_eligible"] = True
        tampered["optimizer_ranking_action"] = "ALLOW_RANKING"
        tampered.update(paper_shadow_evidence_actionability_fields(tampered))
        tampered["evidence_hash"] = paper_shadow_evidence_hash(tampered)
        tampered_result = validate_paper_shadow_evidence_accumulation_report(tampered)
        self.assertEqual(tampered_result.status, "BLOCKED")
        self.assertEqual(tampered_result.blocker_code, "MEASUREMENT_MISSING")

    def test_long_run_claim_requires_actual_runtime_source_evidence(self):
        supporting_ids = _supporting_window_ids(20)
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-no-actual-runtime-source",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            source_evidence_ids=supporting_ids,
            long_run_evidence_eligible=True,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertEqual(report["evidence_actionability_status"], "SCORECARD_READY_BIND_ACTUAL_RUNTIME_SOURCE")
        self.assertEqual(report["primary_collection_deficit_code"], "ACTUAL_RUNTIME_SOURCE_DEFICIT")
        self.assertEqual(report["next_collection_action"], "ATTACH_VALIDATED_NON_LIVE_RUNTIME_SOURCE")
        self.assertTrue(
            any("validated non-live persistent runtime source evidence" in error for error in errors),
            errors,
        )

        tampered = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-tampered-no-actual-runtime-source",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            source_evidence_ids=supporting_ids,
            long_run_evidence_eligible=False,
        )
        tampered["long_run_evidence_eligible"] = True
        tampered["long_run_blocker_code"] = None
        tampered["blockers"] = []
        tampered["evidence_chain_complete"] = True
        tampered["scorecard_input_eligible"] = True
        tampered["optimizer_ranking_action"] = "ALLOW_RANKING"
        tampered.update(paper_shadow_evidence_actionability_fields(tampered))
        tampered["evidence_hash"] = paper_shadow_evidence_hash(tampered)
        tampered_result = validate_paper_shadow_evidence_accumulation_report(tampered)
        self.assertEqual(tampered_result.status, "BLOCKED")
        self.assertEqual(tampered_result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

    def test_actual_runtime_source_ids_require_validated_status(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-runtime-source-id-without-status",
            actual_runtime_source_evidence_ids=["actual-runtime:unvalidated-local-stub"],
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertTrue(
            any("actual runtime source ids require validated non-live runtime status" in error for error in errors),
            errors,
        )

    def test_actual_runtime_source_ids_reject_display_truth_sources(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-display-truth-runtime-source",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            source_evidence_ids=_supporting_window_ids(20),
            actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
            actual_runtime_requirement_statuses=_runtime_requirement_pass_statuses(),
            actual_runtime_source_evidence_ids=[
                "dashboard_shell:summary.json:" + "D" * 64,
                "heartbeat:heartbeat.json:" + "E" * 64,
            ],
        )

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertTrue(
            any("display-only, not execution evidence" in error for error in errors),
            errors,
        )

    def test_validated_long_run_non_live_runtime_source_sets_review_ready_actionability(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-long-run-actionable",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            source_evidence_ids=_supporting_window_ids(20),
            actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
            actual_runtime_requirement_statuses=_runtime_requirement_pass_statuses(),
            actual_runtime_source_evidence_ids=[
                "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "D" * 64,
                "actual-runtime-source:upbit:krw_spot:shadow:mvp4_shadow_evidence:" + "E" * 64,
            ],
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertTrue(report["long_run_evidence_eligible"])
        self.assertEqual(report["scorecard_input_truth_status"], "LONG_RUN_REVIEW_READY_NON_LIVE")
        self.assertEqual(report["evidence_actionability_status"], "LONG_RUN_REVIEW_READY")
        self.assertEqual(report["primary_collection_deficit_code"], "NONE")
        self.assertEqual(report["next_collection_action"], "REVIEW_LONG_RUN_EVIDENCE_NON_LIVE")
        self.assertEqual(report["actual_runtime_source_deficit"], 0)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_actual_runtime_source_ids_require_paper_and_shadow_non_live_scope(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-paper-only-runtime-source",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            source_evidence_ids=_supporting_window_ids(20),
            actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
            actual_runtime_requirement_statuses=_runtime_requirement_pass_statuses(),
            actual_runtime_source_evidence_ids=[
                "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "D" * 64,
                "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "E" * 64,
            ],
        )

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertTrue(
            any("both PAPER and SHADOW persistent runtime sources" in error for error in errors),
            errors,
        )

    def test_long_run_eligibility_state_mismatch_blocks_scorecard_input(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-long-run-state-drift",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            source_evidence_ids=_supporting_window_ids(20),
            actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
            actual_runtime_requirement_statuses=_runtime_requirement_pass_statuses(),
            actual_runtime_source_evidence_ids=[
                "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "D" * 64,
                "actual-runtime-source:upbit:krw_spot:shadow:mvp4_shadow_evidence:" + "E" * 64,
            ],
        )
        self.assertTrue(report["long_run_evidence_eligible"])
        self.assertTrue(report["scorecard_input_eligible"])

        report["long_run_evidence_eligible"] = False
        report["long_run_blocker_code"] = "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING"
        report["scorecard_input_eligible"] = True
        report["evidence_chain_complete"] = True
        report["optimizer_ranking_action"] = "ALLOW_RANKING"
        report["blockers"] = []
        report["primary_blocker_code"] = None
        report["evidence_hash"] = paper_shadow_evidence_hash(report)

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")
        self.assertTrue(
            any("long-run eligibility flag must match" in error for error in errors),
            errors,
        )

    def test_long_run_supporting_sources_must_share_window_keys(self):
        supporting_ids = [
            *[f"paper-operation:paper-window-{index:03d}:paper-hash-{index:03d}" for index in range(20)],
            *[f"shadow-evidence:shadow-window-{index:03d}:shadow-hash-{index:03d}" for index in range(20)],
        ]
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-unpaired-supporting-windows",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            source_evidence_ids=supporting_ids,
            actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
            actual_runtime_requirement_statuses=_runtime_requirement_pass_statuses(),
            actual_runtime_source_evidence_ids=[
                "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "D" * 64,
                "actual-runtime-source:upbit:krw_spot:shadow:mvp4_shadow_evidence:" + "E" * 64,
            ],
        )

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertTrue(
            any("per-window PAPER and SHADOW supporting source ids" in error for error in errors),
            errors,
        )

    def test_validated_actual_runtime_requires_all_runtime_requirement_statuses_pass(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-runtime-requirement-status-missing",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            source_evidence_ids=_supporting_window_ids(20),
            actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
            actual_runtime_source_evidence_ids=[
                "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "D" * 64,
                "actual-runtime-source:upbit:krw_spot:shadow:mvp4_shadow_evidence:" + "E" * 64,
            ],
            actual_runtime_requirement_statuses={
                **_runtime_requirement_pass_statuses(),
                "heartbeat_freshness": "STALE",
            },
        )

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertTrue(
            any("actual runtime requirement not PASS: heartbeat_freshness=STALE" in error for error in errors),
            errors,
        )

    def test_missing_actual_runtime_source_fields_block_legacy_partial_report(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-legacy-partial-runtime-source-fields"
        )
        for field in (
            "actual_runtime_source_evidence_ids",
            "actual_runtime_source_status",
            "actual_runtime_requirement_statuses",
            "supporting_source_evidence_ids",
            "supporting_source_window_count",
            "evidence_span_source",
            "evidence_span_source_status",
        ):
            legacy = dict(report)
            legacy.pop(field, None)
            legacy["evidence_hash"] = paper_shadow_evidence_hash(legacy)

            result = validate_paper_shadow_evidence_accumulation_report(legacy)
            errors = _paper_shadow_evidence_accumulation_errors(legacy)

            self.assertEqual(result.status, "FAIL", field)
            self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH", field)
            self.assertTrue(any(field in error for error in errors), errors)

    def test_span_source_and_supporting_window_count_drift_blocks(self):
        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-span-source-drift",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            source_evidence_ids=_supporting_window_ids(20),
            actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
            actual_runtime_requirement_statuses=_runtime_requirement_pass_statuses(),
            actual_runtime_source_evidence_ids=[
                "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "D" * 64,
                "actual-runtime-source:upbit:krw_spot:shadow:mvp4_shadow_evidence:" + "E" * 64,
            ],
        )
        self.assertTrue(report["long_run_evidence_eligible"])

        report["evidence_span_source"] = "NOT_PROVIDED"
        report["evidence_span_source_status"] = "MISSING"
        report["evidence_hash"] = paper_shadow_evidence_hash(report)
        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")
        self.assertTrue(any("evidence_span_hours must be zero" in error for error in errors), errors)

        report = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="paper-shadow-supporting-window-count-drift",
            evidence_window_count=20,
            min_required_evidence_window_count=20,
            evidence_span_hours=120,
            min_required_evidence_span_hours=120,
            source_evidence_ids=_supporting_window_ids(20),
        )
        report["supporting_source_window_count"] = 19
        report["evidence_hash"] = paper_shadow_evidence_hash(report)
        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")
        self.assertTrue(any("supporting_source_window_count must match" in error for error in errors), errors)

    def test_live_flag_drift_blocks(self):
        report = build_paper_shadow_evidence_accumulation_report(evidence_report_id="paper-shadow-live")
        report["live_order_allowed"] = True
        report["can_live_trade"] = True
        report["evidence_hash"] = paper_shadow_evidence_hash(report)
        result = validate_paper_shadow_evidence_accumulation_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_actionability_drift_blocks_even_when_hash_is_recomputed(self):
        report = build_paper_shadow_evidence_accumulation_report(evidence_report_id="paper-shadow-actionability-drift")
        report["primary_collection_deficit_code"] = "NONE"
        report["evidence_hash"] = paper_shadow_evidence_hash(report)

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")
        self.assertTrue(
            any("paper/shadow evidence actionability field drifted" in error for error in errors),
            errors,
        )

    def test_validator_fixtures_pass(self):
        result = paper_shadow_evidence_accumulation_validator()
        self.assertEqual(result.status, "PASS", result.message)

    def test_negative_fixture_errors_are_semantic_not_only_schema(self):
        insufficient = _paper_shadow_evidence_accumulation_errors(
            _load_fixture("paper_shadow_evidence_accumulation_insufficient_sample_fail.json")
        )
        self.assertTrue(any("sample count below min_required_sample_count" in error for error in insufficient))
        stale = _paper_shadow_evidence_accumulation_errors(
            _load_fixture("paper_shadow_evidence_accumulation_stale_fail.json")
        )
        self.assertTrue(any("artifact age exceeds max_artifact_age_seconds" in error for error in stale))
        false_long_run = _paper_shadow_evidence_accumulation_errors(
            _load_fixture("paper_shadow_evidence_accumulation_false_long_run_claim_fail.json")
        )
        self.assertTrue(
            any("long-run evidence eligibility claimed before minimum window/span coverage" in error for error in false_long_run),
            false_long_run,
        )

    def test_source_identity_binding_mismatch_blocks_scorecard_input(self):
        report = build_paper_shadow_evidence_accumulation_report(evidence_report_id="paper-shadow-identity-mismatch")
        report["source_evidence_bindings"][0]["artifact_hash"] = "D" * 64
        report["evidence_hash"] = paper_shadow_evidence_hash(report)

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")
        self.assertTrue(any("source evidence binding mismatch for artifact_hash" in error for error in errors), errors)

    def test_source_identity_stale_status_blocks_scorecard_input(self):
        report = build_paper_shadow_evidence_accumulation_report(evidence_report_id="paper-shadow-identity-stale")
        report["source_evidence_bindings"][1]["identity_match_status"] = "STALE"
        report["evidence_hash"] = paper_shadow_evidence_hash(report)

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DATA_QUALITY_INSUFFICIENT")
        self.assertTrue(any("source evidence binding status is not PASS" in error for error in errors), errors)

    def test_unbound_source_evidence_id_blocks_scorecard_input(self):
        report = build_paper_shadow_evidence_accumulation_report(evidence_report_id="paper-shadow-orphan-source")
        report["source_evidence_ids"].append("paper:unbound-source:" + "E" * 64)
        report["evidence_hash"] = paper_shadow_evidence_hash(report)

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")
        self.assertTrue(any("source evidence id lacks binding" in error for error in errors), errors)

    def test_supporting_source_ids_cannot_duplicate_bound_sources(self):
        report = build_paper_shadow_evidence_accumulation_report(evidence_report_id="paper-shadow-supporting-duplicate")
        report["supporting_source_evidence_ids"] = [report["source_evidence_ids"][0]]
        report["evidence_hash"] = paper_shadow_evidence_hash(report)

        result = validate_paper_shadow_evidence_accumulation_report(report)
        errors = _paper_shadow_evidence_accumulation_errors(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")
        self.assertTrue(any("duplicated as supporting" in error for error in errors), errors)


def _load_fixture(name: str) -> dict:
    import json

    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _supporting_window_ids(count: int) -> list[str]:
    return [
        source_id
        for index in range(count)
        for source_id in (
            f"paper-operation:window-{index:03d}:paper-hash-{index:03d}",
            f"shadow-evidence:window-{index:03d}:shadow-hash-{index:03d}",
        )
    ]


def _runtime_requirement_pass_statuses() -> dict[str, str]:
    return {
        "runtime_span": "PASS",
        "cycle_count": "PASS",
        "heartbeat_freshness": "PASS",
        "recovery_clean": "PASS",
        "partial_write_clean": "PASS",
    }


if __name__ == "__main__":
    unittest.main()
