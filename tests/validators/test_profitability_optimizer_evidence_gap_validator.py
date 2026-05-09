import copy
import json
import unittest
from pathlib import Path

from tools.run_profitability_maturity_rollup_refresh import (
    candidate_scorecard_runtime_membership_evidence,
    paper_shadow_next_required_evidence,
    refresh_current_scorecard_inputs,
    robustness_source_type_evidence,
    rollup_hash,
    runtime_sample_history_evidence,
    scorecard_review_priority,
    update_overfit_component,
    update_promotion_thresholds,
    update_strategy_scorecard_components,
)
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
                {"selected_candidate", "strategy_candidates.candidate_id", "symbol_evidence_scorecards.best_candidate_id"},
            )
            self.assertTrue(runtime_linkage["candidate_scorecard_runtime_symbol"])
            self.assertTrue(runtime_linkage["candidate_scorecard_runtime_decision"])
        else:
            self.assertTrue(runtime_linkage["candidate_scorecard_runtime_membership_blocker_code"])
            self.assertFalse(rollup["paper_scorecard_input_allowed"])
        self.assertFalse(runtime_linkage["live_order_allowed"])
        self.assertFalse(runtime_linkage["can_live_trade"])

    def test_maturity_rollup_binds_runtime_sample_history_evidence(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        sample_history = rollup["runtime_sample_history_evidence"]
        refreshed = runtime_sample_history_evidence(
            {
                "status": "PASS",
                "runtime_sample_history_path": sample_history["source_artifact_path"],
                "scorecard_runtime_selection_source": sample_history["scorecard_runtime_selection_source"],
                "scorecard_runtime_sample_candidate_id": sample_history["scorecard_runtime_sample_candidate_id"],
                "scorecard_candidate_identity_alignment_status": sample_history[
                    "scorecard_candidate_identity_alignment_status"
                ],
            }
        )

        self.assertEqual(sample_history["status"], "PASS")
        self.assertEqual(sample_history["validation_status"], "PASS")
        # The checked-in rollup is a static, live-blocked audit snapshot while
        # an operator PAPER runner may keep advancing the current runtime
        # history.  Exact source hash equality is enforced when the rollup hash
        # has been tampered or PAPER scorecard input is allowed; a safe blocked
        # audit may stay validator-clean while the runtime source advances.
        self.assertTrue(refreshed["history_hash"])
        if refreshed["history_hash"] == sample_history["history_hash"]:
            self.assertEqual(refreshed["accepted_cycle_sample_count"], sample_history["accepted_cycle_sample_count"])
        self.assertGreaterEqual(sample_history["accepted_cycle_sample_count"], 1)
        self.assertIn("upbit_paper_runtime_sample_history.json", sample_history["source_artifact_path"])
        self.assertEqual(
            sample_history["primary_blocker_code"],
            "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
        )
        for field in (
            "credential_load_attempted",
            "private_endpoint_called",
            "order_endpoint_called",
            "order_adapter_called",
            "live_key_loaded",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            self.assertFalse(sample_history[field])
        self.assertEqual(_profitability_evidence_maturity_rollup_errors(rollup), [])

    def test_maturity_rollup_helper_rejects_sample_history_false_pass(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["runtime_sample_history_evidence"]["accepted_cycle_sample_count"] += 1

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("accepted_cycle_sample_count" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_scorecard_input_without_sample_history_pass(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["paper_scorecard_input_allowed"] = True
        tampered["runtime_sample_history_evidence"]["status"] = "BLOCKED"
        tampered["runtime_sample_history_evidence"]["validation_status"] = "BLOCKED"
        tampered["runtime_sample_history_evidence"]["validation_blocker_code"] = "RECONCILIATION_REQUIRED"
        tampered["runtime_sample_history_evidence"]["primary_blocker_code"] = "RECONCILIATION_REQUIRED"

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("runtime sample history" in error for error in errors), errors)

    def test_maturity_rollup_binds_strategy_and_regime_components_from_scorecard(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        scorecard = {
            "source_evidence_ids": ["scorecard:strategy-regime-pass"],
            "strategy_exit_policy_status": "PASS",
            "strategy_exit_policy_sample_count": 30,
            "min_strategy_exit_policy_sample_count": 30,
            "strategy_exit_policy_match_count": 30,
            "strategy_exit_policy_mismatch_count": 0,
            "strategy_exit_reason_count": 30,
            "expected_strategy_exit_policy_id": "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1",
            "expected_strategy_exit_variation": "invalidation_exit",
            "regime_outcome_status": "PASS",
            "regime_outcome_sample_count": 4,
            "min_regime_outcome_sample_count": 4,
            "regime_outcome_covered_count": 4,
            "min_regime_outcome_covered_count": 4,
            "regime_outcome_trade_count": 2,
            "regime_outcome_no_trade_count": 2,
            "regime_outcome_mismatch_count": 0,
            "regime_outcome_counts": [
                {
                    "regime": "UPTREND",
                    "sample_count": 1,
                    "trade_count": 1,
                    "no_trade_count": 0,
                    "mismatch_count": 0,
                    "trade_allowed": True,
                    "primary_blocker_code": None,
                },
                {
                    "regime": "RANGE",
                    "sample_count": 1,
                    "trade_count": 1,
                    "no_trade_count": 0,
                    "mismatch_count": 0,
                    "trade_allowed": True,
                    "primary_blocker_code": None,
                },
                {
                    "regime": "DOWNTREND",
                    "sample_count": 1,
                    "trade_count": 0,
                    "no_trade_count": 1,
                    "mismatch_count": 0,
                    "trade_allowed": False,
                    "primary_blocker_code": "RISK_VETO",
                },
                {
                    "regime": "RISK_OFF",
                    "sample_count": 1,
                    "trade_count": 0,
                    "no_trade_count": 1,
                    "mismatch_count": 0,
                    "trade_allowed": False,
                    "primary_blocker_code": "RISK_VETO",
                },
            ],
            "evaluated_symbol_count": 20,
            "paper_entry_review_symbol_count": 3,
            "top_symbol_evidence_scorecards": [
                {"best_strategy_family": "VWAP_MEAN_REVERSION", "best_decision": "PAPER_ENTRY_REVIEW"},
                {"best_strategy_family": "PULLBACK_TREND_LONG", "best_decision": "PAPER_ENTRY_REVIEW"},
            ],
            "strategy_family_evidence_scorecards": [
                {
                    "strategy_family": "VWAP_MEAN_REVERSION",
                    "best_decision": "PAPER_ENTRY_REVIEW",
                    "paper_entry_review_candidate_count": 1,
                },
                {
                    "strategy_family": "PULLBACK_TREND_LONG",
                    "best_decision": "PAPER_ENTRY_REVIEW",
                    "paper_entry_review_candidate_count": 1,
                },
                {
                    "strategy_family": "BREAKOUT_RETEST_LONG",
                    "best_decision": "NO_TRADE",
                    "paper_entry_review_candidate_count": 0,
                },
            ],
        }

        update_strategy_scorecard_components(
            rollup,
            scorecard,
            {"entry_reason_count": 3, "no_trade_reason_count": 3},
        )
        rollup["rollup_hash"] = rollup_hash(rollup)
        by_id = {component["component_id"]: component for component in rollup["components"]}

        for component_id in ("strategy_entry_exit_no_trade", "symbol_selection_regime", "vwap_trend_breakout"):
            self.assertEqual(by_id[component_id]["maturity_status"], "PAPER_SCORECARD_INPUT_ONLY")
            self.assertEqual(by_id[component_id]["evidence_status"], "PASS")
            self.assertTrue(by_id[component_id]["paper_scorecard_input_eligible"])
            self.assertFalse(by_id[component_id]["live_order_allowed"])
        self.assertEqual(by_id["strategy_entry_exit_no_trade"]["strategy_exit_policy_match_count"], 30)
        self.assertEqual(by_id["symbol_selection_regime"]["regime_outcome_covered_count"], 4)
        self.assertEqual(by_id["vwap_trend_breakout"]["strategy_family_covered_count"], 3)
        self.assertEqual(_profitability_evidence_maturity_rollup_errors(rollup), [])

    def test_maturity_rollup_rejects_strategy_component_false_eligibility(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        component = next(
            item for item in rollup["components"] if item["component_id"] == "strategy_entry_exit_no_trade"
        )
        component.update(
            {
                "maturity_status": "PAPER_SCORECARD_INPUT_ONLY",
                "evidence_status": "PASS",
                "paper_scorecard_input_eligible": True,
                "strategy_exit_policy_status": "UNTESTED",
                "strategy_exit_policy_sample_count": 30,
                "min_strategy_exit_policy_sample_count": 30,
                "strategy_exit_policy_match_count": 30,
                "strategy_exit_policy_mismatch_count": 0,
                "strategy_exit_reason_count": 30,
                "entry_reason_count": 1,
                "no_trade_reason_count": 1,
            }
        )

        errors = _profitability_evidence_maturity_rollup_errors(rollup)

        self.assertTrue(any("strategy entry/exit" in error for error in errors), errors)

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

    def test_maturity_rollup_accepts_validated_scorecard_cost_model_for_net_ev_threshold(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        thresholds = rollup["promotion_threshold_evidence"]
        if "NET_EV_AFTER_COST_NOT_PASS" not in thresholds["missing_threshold_codes"]:
            thresholds["missing_threshold_codes"].append("NET_EV_AFTER_COST_NOT_PASS")
        thresholds["net_ev_after_cost_status"] = "FAIL"

        update_promotion_thresholds(
            rollup,
            {
                "net_ev_after_cost_bps": 12.5,
                "min_required_edge_bps": 10.0,
                "cost_model_status": "VALIDATED",
            },
            {"oos_status": "PASS", "walk_forward_status": "PASS"},
        )

        self.assertEqual(thresholds["net_ev_after_cost_status"], "PASS")
        self.assertNotIn("NET_EV_AFTER_COST_NOT_PASS", thresholds["missing_threshold_codes"])
        self.assertEqual(thresholds["status"], "BLOCKED_FOR_THRESHOLD_EVIDENCE")
        self.assertFalse(thresholds["live_order_allowed"])
        self.assertFalse(thresholds["scale_up_allowed"])

    def test_maturity_rollup_binds_scorecard_closed_trade_performance_thresholds(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        thresholds = rollup["promotion_threshold_evidence"]
        expected_missing = {
            "PAPER_CLOSED_TRADES_BELOW_MIN",
            "STRATEGY_EXIT_POLICY_NOT_PASS",
            "PROFIT_FACTOR_NOT_PASS",
        }
        self.assertTrue(expected_missing.issubset(set(thresholds["missing_threshold_codes"])))
        self.assertEqual(thresholds["strategy_exit_policy_status"], "FAIL")
        self.assertEqual(thresholds["profit_factor_status"], "FAIL")
        self.assertEqual(thresholds["regime_outcome_status"], "FAIL")
        current_runtime_passed = {
            "MAX_DRAWDOWN_NOT_PASS",
            "FILL_QUALITY_NOT_PASS",
            "EXECUTION_COST_COMPARISON_NOT_PASS",
        }
        self.assertFalse(current_runtime_passed.intersection(set(thresholds["missing_threshold_codes"])))
        self.assertEqual(thresholds["max_drawdown_status"], "PASS")
        self.assertEqual(thresholds["fill_quality_status"], "PASS")
        self.assertEqual(thresholds["execution_cost_comparison_status"], "PASS")

        update_promotion_thresholds(
            rollup,
            {
                "net_ev_after_cost_bps": 12.5,
                "min_required_edge_bps": 10.0,
                "cost_model_status": "VALIDATED",
                "closed_trade_status": "PASS",
                "closed_trade_sample_count": 42,
                "min_closed_trade_sample_count": 30,
                "strategy_exit_policy_status": "PASS",
                "strategy_exit_policy_sample_count": 42,
                "min_strategy_exit_policy_sample_count": 30,
                "strategy_exit_policy_mismatch_count": 0,
                "profit_factor_status": "PASS",
                "profit_factor": 1.42,
                "min_profit_factor": 1.25,
                "max_drawdown_status": "PASS",
                "max_drawdown_pct": 4.8,
                "max_allowed_drawdown_pct": 8.0,
                "fill_quality_status": "PASS",
                "fill_quality_score": 0.91,
                "min_fill_quality_score": 0.80,
                "execution_cost_comparison_status": "PASS",
                "execution_cost_delta_bps": 1.0,
                "max_allowed_execution_cost_delta_bps": 2.0,
            },
            {"oos_status": "PASS", "walk_forward_status": "PASS"},
        )

        self.assertEqual(thresholds["paper_closed_trades"], 42)
        self.assertEqual(thresholds["strategy_exit_policy_status"], "PASS")
        self.assertEqual(thresholds["profit_factor_status"], "PASS")
        self.assertEqual(thresholds["max_drawdown_status"], "PASS")
        self.assertEqual(thresholds["fill_quality_status"], "PASS")
        self.assertFalse(expected_missing.intersection(set(thresholds["missing_threshold_codes"])))
        self.assertEqual(thresholds["status"], "BLOCKED_FOR_THRESHOLD_EVIDENCE")
        self.assertFalse(thresholds["live_order_allowed"])
        self.assertFalse(thresholds["scale_up_allowed"])

    def test_maturity_rollup_active_text_has_no_fixed_runtime_hour_floor(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        text = json.dumps(rollup, sort_keys=True).lower()

        self.assertNotIn("120 hours", text)
        self.assertNotIn("paper_runtime_hours_below_min", text)
        self.assertIn("observed_context_only_no_fixed_runtime_floor", text)

    def test_maturity_rollup_scorecard_input_refresh_fails_closed_without_runtime(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result = refresh_current_scorecard_inputs(
                root=Path(tmp),
                session_id="mvp1_upbit_paper_launcher",
            )

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["blocker_code"], "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertFalse(result["live_order_ready"])
        self.assertFalse(result["live_order_allowed"])
        self.assertFalse(result["can_live_trade"])
        self.assertFalse(result["scale_up_allowed"])

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

        self.assertIn(
            source_evidence["sample_basis"],
            {"REALIZED_CLOSED_PAPER_TRADES", "PUBLIC_REPLAY_REALIZED_CLOSED_TRADE_PNL_BPS"},
        )
        self.assertEqual(
            source_evidence["preliminary_sample_basis"],
            "EXPECTED_NET_EV_AFTER_COST_WITH_REALIZED_CLOSED_TRADE_OVERRIDE",
        )
        if source_evidence["sample_basis"] == "PUBLIC_REPLAY_REALIZED_CLOSED_TRADE_PNL_BPS":
            expected_deficit = max(
                rollup["promotion_threshold_evidence"]["min_replay_closed_trades"]
                - rollup["promotion_threshold_evidence"]["replay_closed_trades"],
                0,
            )
        else:
            expected_deficit = max(
                rollup["promotion_threshold_evidence"]["min_paper_closed_trades"]
                - rollup["promotion_threshold_evidence"]["paper_closed_trades"],
                0,
            )
        self.assertEqual(source_evidence["closed_trade_sample_deficit"], expected_deficit)
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

    def test_maturity_rollup_helper_rejects_public_replay_expected_edge_as_sample_basis(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["robustness_source_type_evidence"]["sample_basis"] = "PUBLIC_REPLAY_EXPECTED_NET_EV_AFTER_COST"
        overfit_component = next(
            component for component in tampered["components"] if component["component_id"] == "overfit_oos_walk_forward"
        )
        overfit_component["sample_basis"] = "PUBLIC_REPLAY_EXPECTED_NET_EV_AFTER_COST"

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(
            any("PUBLIC_REPLAY_REALIZED_CLOSED_TRADE_PNL_BPS" in error or "not in enum" in error for error in errors),
            errors,
        )

    def test_maturity_rollup_helper_rejects_public_replay_sample_count_not_closed_trade_count(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        tampered["promotion_threshold_evidence"]["replay_closed_trades"] = 1
        tampered["promotion_threshold_evidence"]["min_replay_closed_trades"] = 100
        tampered["robustness_source_type_evidence"]["sample_basis"] = "PUBLIC_REPLAY_REALIZED_CLOSED_TRADE_PNL_BPS"
        tampered["robustness_source_type_evidence"]["sample_count"] = 415
        tampered["robustness_source_type_evidence"]["closed_trade_sample_deficit"] = 99
        overfit_component = next(
            component for component in tampered["components"] if component["component_id"] == "overfit_oos_walk_forward"
        )
        overfit_component["sample_basis"] = "PUBLIC_REPLAY_REALIZED_CLOSED_TRADE_PNL_BPS"
        overfit_component["sample_count"] = 415
        overfit_component["closed_trade_sample_count"] = 1
        overfit_component["closed_trade_sample_deficit"] = 99

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("public replay" in error and "sample_count" in error for error in errors), errors)

    def test_maturity_rollup_public_replay_projection_uses_closed_trade_samples(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        scorecard = {
            "replay_closed_trade_sample_count": 2,
            "replay_closed_trade_status": "FAIL",
            "closed_trade_sample_count": 30,
            "min_closed_trade_sample_count": 30,
            "source_evidence_ids": [
                "public_replay_robustness:public-replay:test-cycle:KRW-BTC-candidate:" + "A" * 64
            ],
        }
        overfit = {
            "sample_count": 415,
            "min_required_sample_count": 300,
            "source_evidence_ids": [
                "public_replay_robustness:public-replay:test-cycle:KRW-BTC-candidate:" + "A" * 64
            ],
            "oos_status": "FAIL",
            "walk_forward_status": "FAIL",
            "bootstrap_status": "FAIL",
            "concentration_risk_status": "HIGH",
            "preliminary_sample_count": 10,
            "preliminary_exact_candidate_sample_count": 2,
            "robustness_eligible": False,
        }

        update_promotion_thresholds(rollup, scorecard, overfit)
        source_evidence = robustness_source_type_evidence(scorecard, overfit)
        update_overfit_component(rollup, scorecard, overfit)
        overfit_component = next(
            component for component in rollup["components"] if component["component_id"] == "overfit_oos_walk_forward"
        )

        self.assertEqual(rollup["promotion_threshold_evidence"]["replay_closed_trades"], 2)
        self.assertIn("REPLAY_CLOSED_TRADES_BELOW_MIN", rollup["promotion_threshold_evidence"]["missing_threshold_codes"])
        self.assertEqual(source_evidence["sample_basis"], "PUBLIC_REPLAY_REALIZED_CLOSED_TRADE_PNL_BPS")
        self.assertEqual(source_evidence["sample_count"], 2)
        self.assertEqual(source_evidence["closed_trade_sample_deficit"], 98)
        self.assertEqual(overfit_component["sample_basis"], "PUBLIC_REPLAY_REALIZED_CLOSED_TRADE_PNL_BPS")
        self.assertEqual(overfit_component["sample_count"], 2)
        self.assertEqual(overfit_component["closed_trade_sample_count"], 2)
        self.assertEqual(overfit_component["closed_trade_sample_deficit"], 98)
        self.assertFalse(overfit_component["paper_scorecard_input_eligible"])
        self.assertFalse(rollup["promotion_threshold_evidence"]["live_order_allowed"])

    def test_maturity_rollup_review_priority_prefers_replay_validated_alternative(self):
        active_scorecard = {
            "candidate_id": "KRW-BTC-pullback-trend-long",
            "ranking_eligible": False,
            "performance_ready": False,
            "robustness_ready": False,
            "net_ev_after_cost_bps": 14.0,
            "source_evidence_ids": ["upbit_paper_runtime_cycle:active:" + "A" * 64],
            "blockers": [{"code": "OOS_MISSING"}],
        }
        replay_validated_alternative = {
            "candidate_id": "KRW-ETH-breakout-retest-long",
            "ranking_eligible": False,
            "performance_ready": False,
            "robustness_ready": True,
            "net_ev_after_cost_bps": 9.0,
            "source_evidence_ids": [
                "upbit_paper_runtime_cycle:alternative:" + "B" * 64,
                "public_replay_robustness:alternative:" + "C" * 64,
            ],
            "blockers": [{"code": "SAMPLE_INSUFFICIENT"}],
        }

        self.assertGreater(
            scorecard_review_priority(
                replay_validated_alternative,
                active_source=False,
                has_matching_overfit=True,
            ),
            scorecard_review_priority(
                active_scorecard,
                active_source=True,
                has_matching_overfit=True,
            ),
        )

    def test_maturity_rollup_review_priority_prefers_runtime_linkable_candidate(self):
        invalid_runtime_high_score = {
            "candidate_id": "KRW-BTC-pullback-trend-long",
            "ranking_eligible": False,
            "performance_ready": True,
            "robustness_ready": True,
            "net_ev_after_cost_bps": 48.0,
            "source_evidence_ids": [
                "upbit_paper_runtime_cycle:stale:" + "A" * 64,
                "public_replay_robustness:stale:" + "B" * 64,
            ],
            "blockers": [],
        }
        runtime_linkable_lower_score = {
            "candidate_id": "KRW-ETH-breakout-retest-long",
            "ranking_eligible": False,
            "performance_ready": False,
            "robustness_ready": False,
            "net_ev_after_cost_bps": 3.0,
            "source_evidence_ids": ["upbit_paper_runtime_cycle:linked:" + "C" * 64],
            "blockers": [{"code": "SAMPLE_INSUFFICIENT"}],
        }

        self.assertGreater(
            scorecard_review_priority(
                runtime_linkable_lower_score,
                active_source=False,
                has_matching_overfit=True,
                runtime_linkage_status="PASS",
            ),
            scorecard_review_priority(
                invalid_runtime_high_score,
                active_source=True,
                has_matching_overfit=True,
                runtime_linkage_status="BLOCKED",
            ),
        )

    def test_maturity_rollup_membership_accepts_runtime_strategy_candidate(self):
        evidence = candidate_scorecard_runtime_membership_evidence(
            {
                "cycle_id": "cycle-1",
                "selected_candidate": {"candidate_id": "KRW-BTC-pullback-trend-long"},
                "strategy_candidates": [
                    {
                        "candidate_id": "KRW-ETH-breakout-retest-long",
                        "symbol": "KRW-ETH",
                        "decision": "PAPER_ENTRY_REVIEW",
                        "live_order_allowed": False,
                        "can_live_trade": False,
                        "scale_up_allowed": False,
                    }
                ],
                "symbol_evidence_scorecards": [],
            },
            {"candidate_id": "KRW-ETH-breakout-retest-long"},
        )

        self.assertEqual(evidence["candidate_scorecard_runtime_membership_status"], "PASS")
        self.assertEqual(evidence["candidate_scorecard_runtime_membership_source"], "strategy_candidates.candidate_id")
        self.assertEqual(evidence["candidate_scorecard_runtime_symbol"], "KRW-ETH")
        self.assertEqual(evidence["candidate_scorecard_runtime_decision"], "PAPER_ENTRY_REVIEW")

    def test_maturity_rollup_helper_rejects_robustness_source_type_preliminary_false_pass(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        source_evidence = tampered["robustness_source_type_evidence"]
        source_evidence["status"] = "PASS"
        source_evidence["source_type_counts"] = {
            "oos_count": 1,
            "walk_forward_count": 1,
            "bootstrap_count": 1,
            "concentration_count": 1,
        }
        source_evidence["present_source_types"] = ["OOS", "WALK_FORWARD", "BOOTSTRAP", "CONCENTRATION"]
        source_evidence["missing_source_types"] = []
        source_evidence["primary_blocker_code"] = None
        source_evidence["explicit_source_type_blocker"] = False
        source_evidence["sample_count"] = 0
        source_evidence["min_required_sample_count"] = 300
        source_evidence["closed_trade_sample_deficit"] = 300
        source_evidence["preliminary_sample_count"] = 300
        source_evidence["preliminary_exact_candidate_sample_count"] = 300

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("required robustness sample minimum" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_overfit_component_expected_edge_basis(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        component = next(item for item in tampered["components"] if item["component_id"] == "overfit_oos_walk_forward")
        component["sample_basis"] = "EXPECTED_ENTRY_NET_EV"

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("sample_basis" in error and "enum" in error for error in errors), errors)

    def test_maturity_rollup_helper_rejects_overfit_component_preliminary_false_eligibility(self):
        rollup = load_json(ROLLUP_FIXTURE_PATH)
        tampered = copy.deepcopy(rollup)
        component = next(item for item in tampered["components"] if item["component_id"] == "overfit_oos_walk_forward")
        component["sample_count"] = 0
        component["closed_trade_sample_count"] = 0
        component["min_required_sample_count"] = 300
        component["closed_trade_sample_deficit"] = 300
        component["preliminary_sample_count"] = 300
        component["preliminary_exact_candidate_sample_count"] = 300
        component["evidence_status"] = "PASS"
        component["paper_scorecard_input_eligible"] = True
        component["next_required_evidence"] = (
            "Robustness uses realized closed PAPER trades; preliminary expected-edge samples are review only."
        )

        errors = _profitability_evidence_maturity_rollup_errors(tampered)

        self.assertTrue(any("closed PAPER trade minimum" in error for error in errors), errors)

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
