import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _candidate_cooldown_errors,
    candidate_cooldown_validator,
    load_json,
    run_validators,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class CandidateCooldownValidatorTest(unittest.TestCase):
    def test_zero_cooldown_pass_fixture_allows_paper_ranking_review(self):
        report = load_json(FIXTURE_DIR / "exploration_exploitation_policy_pass.json")

        self.assertEqual([], _candidate_cooldown_errors(report))

    def test_blocked_cooldown_pass_fixture_is_visible_and_non_live(self):
        report = load_json(FIXTURE_DIR / "candidate_cooldown_blocked_pass.json")

        self.assertEqual([], _candidate_cooldown_errors(report))
        self.assertEqual("BLOCK_TRANSITION", report["transition_decision"])
        self.assertEqual("BLOCKED", report["recommendation_scope"])
        self.assertFalse(report["exploitation_allowed_for_paper_ranking"])
        self.assertFalse(report["live_order_allowed"])

    def test_cooldown_bypass_blocks_paper_ranking_review(self):
        report = load_json(FIXTURE_DIR / "candidate_cooldown_bypass_fail.json")

        errors = _candidate_cooldown_errors(report)

        self.assertIn("candidate cooldown requires transition_decision=BLOCK_TRANSITION", errors)
        self.assertIn("candidate cooldown forbids exploitation_allowed_for_paper_ranking=true", errors)

    def test_cooldown_missing_blocker_is_rejected(self):
        report = load_json(FIXTURE_DIR / "candidate_cooldown_missing_blocker_fail.json")

        errors = _candidate_cooldown_errors(report)

        self.assertIn("candidate cooldown requires COOLDOWN blocker", errors)

    def test_stale_cooldown_blocker_is_rejected(self):
        report = load_json(FIXTURE_DIR / "candidate_cooldown_stale_blocker_fail.json")

        errors = _candidate_cooldown_errors(report)

        self.assertIn("cooldown_cycles_remaining=0 cannot carry COOLDOWN blocker", errors)

    def test_cooldown_status_cannot_be_false_pass(self):
        report = load_json(FIXTURE_DIR / "candidate_cooldown_false_pass_status_fail.json")

        errors = _candidate_cooldown_errors(report)

        self.assertIn("candidate cooldown cannot expose status=PASS", errors)

    def test_registered_validator_passes_current_fixtures(self):
        result = candidate_cooldown_validator().as_dict()

        self.assertEqual("PASS", result["status"], result)
        self.assertFalse(result["blocking"], result)

    def test_run_validators_dispatch_includes_candidate_cooldown(self):
        result = run_validators(["candidate_cooldown_validator"])[0]

        self.assertEqual("PASS", result["status"], result)


if __name__ == "__main__":
    unittest.main()
