import copy
import json
import unittest
from pathlib import Path

from tools.run_profitability_maturity_rollup_refresh import paper_shadow_next_required_evidence
from trader1.validation.mvp0_validators import (
    PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS,
    _profitability_evidence_audit_errors,
    _profitability_evidence_maturity_rollup_errors,
    load_json,
    profitability_evidence_maturity_rollup_validator,
    profitability_optimizer_evidence_gap_validator,
)


ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json"
CONTRACT_GAP_PATH = (
    ROOT / "system" / "evidence" / "contract_gaps" / "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json"
)
STATE_PATH = ROOT / "contracts" / "generated" / "current_implementation_state.json"
STATE_SYNC_PATCH_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "patch_results"
    / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_STATE_SYNC_RECHECK.patch_result.json"
)
ROLLUP_FIXTURE_PATH = ROOT / "tests" / "validators" / "fixtures" / "profitability_evidence_maturity_rollup_pass.json"


class ProfitabilityOptimizerEvidenceGapValidatorTest(unittest.TestCase):
    def test_current_audit_is_explicit_and_live_blocked(self):
        result = profitability_optimizer_evidence_gap_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])
        self.assertIn("MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json", result["input_artifact_paths"][0])

    def test_audit_helper_rejects_live_flag_drift(self):
        audit = load_json(AUDIT_PATH)
        tampered = copy.deepcopy(audit)
        tampered["live_order_allowed"] = True

        errors = _profitability_evidence_audit_errors(tampered)

        self.assertIn("audit has forbidden true field: live_order_allowed", errors)

    def test_audit_helper_rejects_missing_component_gap(self):
        audit = load_json(AUDIT_PATH)
        tampered = copy.deepcopy(audit)
        tampered["gaps"] = [
            gap for gap in tampered["gaps"] if gap["component"] != "optimizer_objective_net_ev_after_cost"
        ]

        errors = _profitability_evidence_audit_errors(tampered)

        self.assertTrue(
            any("optimizer_objective_net_ev_after_cost" in error for error in errors),
            errors,
        )

    def test_audit_helper_covers_required_components(self):
        audit = load_json(AUDIT_PATH)
        inspected = {
            item["component_id"] for item in audit["inspected_components"]
        }
        gap_components = {item["component"] for item in audit["gaps"]}

        self.assertEqual(inspected, PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS)
        self.assertEqual(gap_components, PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS)

    def test_contract_gap_remains_open_live_affecting_and_not_scale_eligible(self):
        gap = load_json(CONTRACT_GAP_PATH)

        self.assertEqual(gap["status"], "OPEN")
        self.assertTrue(gap["live_affecting"])
        self.assertFalse(gap.get("live_order_allowed", False))
        self.assertFalse(gap.get("scale_up_allowed", False))
        blocker_codes = {item["code"] for item in gap["blockers"]}
        self.assertIn("CONTRACT_GAP_HIGH", blocker_codes)
        self.assertIn("LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING", blocker_codes)
        self.assertNotIn("OOS_WALK_FORWARD_BOOTSTRAP_EVIDENCE_MISSING", blocker_codes)
        self.assertNotIn("ROBUSTNESS_SOURCE_TYPE_EVIDENCE_REQUIRED", blocker_codes)

    def test_state_sync_recheck_keeps_gap_open_and_routes_to_long_run_boundary(self):
        state = load_json(STATE_PATH)
        patch_result = load_json(STATE_SYNC_PATCH_PATH)

        self.assertEqual(
            patch_result["patch_id"],
            "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_STATE_SYNC_RECHECK_20260504_001",
        )
        self.assertEqual(
            patch_result["next_task_class"],
            "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECK",
        )
        if state["last_patch_id"] == patch_result["patch_id"]:
            self.assertEqual(
                state["next_allowed_task_class"],
                "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECK",
            )
        self.assertIn("PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY", state["open_contract_gap_ids"])
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            self.assertFalse(state[field])
        for field in (
            "live_order_ready_after",
            "live_order_allowed_after",
            "can_live_trade_after",
            "scale_up_allowed_after",
            "convergence_live_order_allowed_after",
        ):
            self.assertFalse(patch_result[field])

    def test_maturity_rollup_validator_passes_current_rollup(self):
        result = profitability_evidence_maturity_rollup_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])
        self.assertIn("MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json", result["input_artifact_paths"][1])

    def test_maturity_rollup_exposes_candidate_scorecard_snapshot_truth(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        runtime_linkage = rollup["runtime_linkage_evidence"]

        self.assertIn(runtime_linkage["candidate_scorecard_snapshot_status"], {"PASS", "BLOCKED"})
        if runtime_linkage["candidate_scorecard_snapshot_status"] == "PASS":
            self.assertIsNone(runtime_linkage["candidate_scorecard_snapshot_blocker_code"])
        else:
            self.assertTrue(runtime_linkage["candidate_scorecard_snapshot_blocker_code"])
            self.assertFalse(rollup["paper_scorecard_input_allowed"])
        self.assertIn(runtime_linkage["candidate_scorecard_runtime_membership_status"], {"PASS", "BLOCKED"})
        if runtime_linkage["candidate_scorecard_runtime_membership_status"] == "PASS":
            self.assertIsNone(runtime_linkage["candidate_scorecard_runtime_membership_blocker_code"])
            self.assertIn(
                runtime_linkage["candidate_scorecard_runtime_membership_source"],
                {"selected_candidate", "symbol_evidence_scorecards.best_candidate_id"},
            )
            self.assertTrue(runtime_linkage["candidate_scorecard_runtime_symbol"])
            self.assertTrue(runtime_linkage["candidate_scorecard_runtime_decision"])
        else:
            self.assertTrue(runtime_linkage["candidate_scorecard_runtime_membership_blocker_code"])
            self.assertFalse(rollup["paper_scorecard_input_allowed"])
        self.assertFalse(runtime_linkage["live_order_allowed"])
        self.assertFalse(runtime_linkage["can_live_trade"])

    def test_maturity_rollup_helper_rejects_snapshot_blocked_scorecard_input(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        runtime_linkage = tampered["runtime_linkage_evidence"]
        runtime_linkage["candidate_scorecard_snapshot_status"] = "BLOCKED"
        runtime_linkage["candidate_scorecard_snapshot_blocker_code"] = "SCORECARD_SNAPSHOT_MISSING"
        tampered["paper_scorecard_input_allowed"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("candidate scorecard snapshot" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_membership_blocked_scorecard_input(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        runtime_linkage = tampered["runtime_linkage_evidence"]
        runtime_linkage["candidate_scorecard_runtime_membership_status"] = "BLOCKED"
        runtime_linkage[
            "candidate_scorecard_runtime_membership_blocker_code"
        ] = "CANDIDATE_SCORECARD_NOT_IN_RUNTIME_SYMBOL_SCORECARDS"
        tampered["paper_scorecard_input_allowed"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("scorecard runtime membership" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_scorecard_candidate_mismatch(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["runtime_linkage_evidence"]["candidate_scorecard_candidate_id"] = "KRW-FAKE-pullback-trend-long"

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("scorecard candidate id" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_missing_component(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["components"] = [
            component for component in tampered["components"] if component["component_id"] != "overfit_oos_walk_forward"
        ]
        tampered["component_count"] = 9

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                "component_count" in error
                or "components" in error
                or "overfit_oos_walk_forward" in error
                for error in errors
            ),
            errors,
        )

    def test_maturity_rollup_helper_rejects_live_or_scale_drift(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["live_order_allowed"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("live_order_allowed" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_component_live_review_eligibility(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["components"][0]["live_review_eligible"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("live_review_eligible" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_hidden_long_run_claim(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        paper_shadow = tampered["components"][8]
        self.assertEqual(paper_shadow["component_id"], "paper_shadow_evidence_accumulation")
        paper_shadow["long_run_evidence_eligible"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("long-run" in error for error in errors), errors)

    def test_paper_shadow_next_required_evidence_distinguishes_sample_and_source_id_deficits(self):
        message = paper_shadow_next_required_evidence(
            {
                "paper_sample_count": 320,
                "shadow_sample_count": 40,
                "min_required_sample_count": 30,
                "evidence_window_count": 20,
                "supporting_source_window_count": 0,
                "min_required_evidence_window_count": 20,
                "evidence_span_hours": 0,
                "min_required_evidence_span_hours": 120,
                "entry_reason_count": 0,
                "no_trade_reason_count": 320,
                "cost_evidence_count": 0,
                "actual_runtime_source_deficit": 2,
            }
        )

        self.assertIn("SHADOW observations 40/30", message)
        self.assertIn("runtime windows 20/20", message)
        self.assertIn("source-bound window IDs 0/20", message)
        self.assertIn("collect 20 source-bound PAPER/SHADOW window IDs", message)
        self.assertIn("entry reasons", message)
        self.assertIn("cost evidence", message)
        self.assertNotIn("more non-live SHADOW observations", message)

    def test_paper_shadow_next_required_evidence_includes_runtime_collection_depth(self):
        message = paper_shadow_next_required_evidence(
            {
                "paper_sample_count": 381,
                "shadow_sample_count": 20,
                "min_required_sample_count": 30,
                "evidence_window_count": 20,
                "supporting_source_window_count": 20,
                "min_required_evidence_window_count": 20,
                "evidence_span_hours": 0,
                "min_required_evidence_span_hours": 120,
                "entry_reason_count": 1,
                "no_trade_reason_count": 381,
                "cost_evidence_count": 1,
                "actual_runtime_source_deficit": 0,
            },
            runtime_profile_evidence={
                "paper_remaining_cycle_count": 2499,
                "paper_remaining_span_seconds": 70767,
                "shadow_remaining_cycle_count": 2860,
                "shadow_remaining_span_seconds": 86398,
                "recommended_next_paper_batch_cycle_count": 20,
            },
        )

        self.assertIn("remaining PAPER 2499 cycles/70767s", message)
        self.assertIn("SHADOW 2860 cycles/86398s", message)
        self.assertIn("next safe PAPER batch is 20 cycles", message)

    def test_maturity_rollup_helper_requires_runtime_linkage_evidence(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        del tampered["runtime_linkage_evidence"]

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("runtime_linkage_evidence" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_runtime_linkage_live_drift(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["runtime_linkage_evidence"]["live_order_allowed"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("live_order_allowed" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_runtime_linkage_hash_mismatch(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["runtime_linkage_evidence"]["source_runtime_cycle_hash"] = "A" * 64

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("cycle hash" in error for error in errors), errors)

    def test_maturity_rollup_helper_requires_runtime_collection_profile_evidence(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        del tampered["runtime_collection_profile_evidence"]

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("runtime_collection_profile_evidence" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_runtime_collection_profile_live_drift(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["runtime_collection_profile_evidence"]["live_order_allowed"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(
            any("runtime_collection_profile_evidence" in error and "live_order_allowed" in error for error in errors),
            errors,
        )

    def test_maturity_rollup_helper_rejects_runtime_collection_profile_hash_mismatch(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["runtime_collection_profile_evidence"]["profile_hash"] = "A" * 64

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("profile hash" in error for error in errors), errors)

    def test_maturity_rollup_helper_requires_promotion_threshold_evidence(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        del tampered["promotion_threshold_evidence"]

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("promotion_threshold_evidence" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_threshold_false_pass_below_minimum(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        thresholds = tampered["promotion_threshold_evidence"]
        thresholds["status"] = "PASS"

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("claim PASS" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_missing_threshold_blocker_code(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        thresholds = tampered["promotion_threshold_evidence"]
        thresholds["missing_threshold_codes"] = [
            code
            for code in thresholds["missing_threshold_codes"]
            if code != "SHADOW_SIGNAL_OPPORTUNITIES_BELOW_MIN"
        ]

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("SHADOW_SIGNAL_OPPORTUNITIES_BELOW_MIN" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_fixed_runtime_hour_floor(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        thresholds = tampered["promotion_threshold_evidence"]
        thresholds["min_paper_runtime_hours"] = 72

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("fixed PAPER runtime-hour floor" in error for error in errors), errors)

    def test_maturity_rollup_active_text_has_no_fixed_runtime_hour_floor(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        text = json.dumps(rollup, sort_keys=True).lower()

        self.assertNotIn("120 hours", text)
        self.assertNotIn("paper_runtime_hours_below_min", text)
        self.assertIn("observed_context_only_no_fixed_runtime_floor", text)

    def test_maturity_rollup_helper_requires_robustness_source_type_evidence(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        del tampered["robustness_source_type_evidence"]

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("robustness_source_type_evidence" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_robustness_source_type_false_pass(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        source_evidence = tampered["robustness_source_type_evidence"]
        source_evidence["source_type_counts"] = {
            "oos_count": 0,
            "walk_forward_count": 0,
            "bootstrap_count": 0,
            "concentration_count": 0,
        }
        source_evidence["present_source_types"] = []
        source_evidence["missing_source_types"] = ["OOS", "WALK_FORWARD", "BOOTSTRAP", "CONCENTRATION"]
        source_evidence["primary_blocker_code"] = None
        source_evidence["explicit_source_type_blocker"] = False
        tampered["robustness_source_type_evidence"]["status"] = "PASS"

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("claims PASS" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_hidden_robustness_missing_source_types(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        source_evidence = tampered["robustness_source_type_evidence"]
        source_evidence["status"] = "BLOCKED_FOR_SOURCE_TYPE_EVIDENCE"
        source_evidence["source_type_counts"] = {
            "oos_count": 0,
            "walk_forward_count": 0,
            "bootstrap_count": 0,
            "concentration_count": 0,
        }
        source_evidence["present_source_types"] = []
        source_evidence["missing_source_types"] = []
        source_evidence["primary_blocker_code"] = "ROBUSTNESS_SOURCE_TYPE_EVIDENCE_REQUIRED"
        source_evidence["explicit_source_type_blocker"] = True

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("must list missing source types" in error for error in errors), errors)

    def test_maturity_rollup_helper_accepts_robustness_source_type_truth_without_live_permission(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        source_evidence = rollup["robustness_source_type_evidence"]

        if source_evidence["status"] == "PASS":
            self.assertEqual(source_evidence["missing_source_types"], [])
            self.assertIsNone(source_evidence["primary_blocker_code"])
            self.assertFalse(source_evidence["explicit_source_type_blocker"])
        else:
            self.assertEqual(source_evidence["status"], "BLOCKED_FOR_SOURCE_TYPE_EVIDENCE")
            self.assertTrue(source_evidence["missing_source_types"])
            self.assertEqual(source_evidence["primary_blocker_code"], "ROBUSTNESS_SOURCE_TYPE_EVIDENCE_REQUIRED")
            self.assertTrue(source_evidence["explicit_source_type_blocker"])
        self.assertFalse(rollup["live_order_allowed"])
        self.assertEqual(_profitability_evidence_maturity_rollup_errors(rollup), [])

    def test_maturity_rollup_helper_counts_open_high_contract_gap(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["promotion_threshold_evidence"]["high_or_critical_contract_gap_count"] = 0

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("open HIGH profitability contract gap" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_missing_component_source_artifact(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["components"][0]["source_artifact_paths"] = [
            "system/evidence/missing-profitability-source-artifact.json"
        ]

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("source artifact path is missing" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_component_source_artifact_escape(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["components"][0]["source_artifact_paths"] = ["../outside-repo-artifact.json"]

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("source artifact path escapes repository root" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
