import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _candidate_scorecard_net_ev_errors,
    candidate_scorecard_net_ev_validator,
    load_json,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class CandidateScorecardNetEvValidatorTest(unittest.TestCase):
    def test_pass_fixture_is_ranking_eligible_after_costs(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_pass.json")

        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])

    def test_raw_positive_edge_is_rejected_when_net_ev_is_below_minimum(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_raw_cost_fail.json")

        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertTrue(
            any("net_ev_after_cost_bps below min_required_edge_bps" in error for error in errors),
            errors,
        )

    def test_scorecard_cannot_carry_live_permission(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_live_flag_fail.json")

        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_scorecard_cannot_use_misleading_live_ready_wording(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_live_ready_wording_fail.json")

        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertIn("candidate scorecard warning must state not LIVE_READY and live orders blocked", errors)

    def test_ranking_scorecard_scope_remains_paper_input_only(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_pass.json")
        tampered = copy.deepcopy(scorecard)
        tampered["scorecard_scope"] = "BLOCKED_RESEARCH_ONLY"

        errors = _candidate_scorecard_net_ev_errors(tampered)

        self.assertIn("ranking_eligible scorecard must remain PAPER_SCORECARD_INPUT_ONLY", errors)

    def test_oos_must_pass_before_ranking_eligibility(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_missing_oos_fail.json")

        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertIn("oos_status must be PASS before ranking eligibility", errors)

    def test_robustness_source_types_must_be_present_before_ranking(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_missing_robustness_sources_fail.json")

        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertTrue(
            any("ranking_eligible scorecard requires OOS, walk-forward, and bootstrap source evidence ids" in error for error in errors),
            errors,
        )

    def test_robustness_sources_must_match_runtime_cycle_binding(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_mismatched_robustness_sources_fail.json")

        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertIn(
            "ranking_eligible scorecard requires OOS, walk-forward, and bootstrap source evidence ids linked to the same runtime cycle hash",
            errors,
        )

    def test_performance_sources_must_be_candidate_scoped_before_ranking(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_pass.json")
        tampered = copy.deepcopy(scorecard)
        tampered["source_evidence_ids"] = [
            source_id
            for source_id in scorecard["source_evidence_ids"]
            if not source_id.startswith(("closed_trades:", "execution_quality:", "performance_summary:"))
        ] + [
            "closed_trades:paper_scorecard_fixture_001:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "execution_quality:paper_scorecard_fixture_001:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "performance_summary:paper_scorecard_fixture_001:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        ]

        errors = _candidate_scorecard_net_ev_errors(tampered)

        self.assertIn(
            "ranking_eligible scorecard requires candidate-scoped closed trade, execution quality, and performance summary evidence ids",
            errors,
        )

    def test_scorecard_schema_requires_performance_maturity_fields(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_pass.json")
        tampered = copy.deepcopy(scorecard)
        del tampered["performance_source_binding_status"]

        errors = _candidate_scorecard_net_ev_errors(tampered)

        self.assertTrue(
            any("performance_source_binding_status" in error for error in errors),
            errors,
        )

    def test_execution_cost_delta_must_pass_before_ranking(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_pass.json")
        tampered = copy.deepcopy(scorecard)
        tampered["execution_cost_delta_bps"] = 5.0

        errors = _candidate_scorecard_net_ev_errors(tampered)

        self.assertIn(
            "execution_cost_delta_bps must stay within allowed execution cost delta before ranking eligibility",
            errors,
        )

    def test_scorecard_schema_requires_robustness_maturity_fields(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_pass.json")
        tampered = copy.deepcopy(scorecard)
        del tampered["robustness_ready"]

        errors = _candidate_scorecard_net_ev_errors(tampered)

        self.assertTrue(any("robustness_ready" in error for error in errors), errors)

    def test_non_ranking_scorecard_must_explain_blocker(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_pass.json")
        tampered = copy.deepcopy(scorecard)
        tampered["ranking_eligible"] = False

        errors = _candidate_scorecard_net_ev_errors(tampered)

        self.assertIn("non-ranking scorecard must carry explicit blocker evidence", errors)

    def test_current_validator_fixtures_pass(self):
        result = candidate_scorecard_net_ev_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
