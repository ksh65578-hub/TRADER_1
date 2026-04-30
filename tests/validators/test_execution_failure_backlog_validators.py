import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _optimizer_feedback_errors,
    _order_failure_taxonomy_errors,
    load_json,
    optimizer_feedback_hash,
    order_failure_taxonomy_validator,
    realized_slippage_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class ExecutionFailureBacklogValidatorsTest(unittest.TestCase):
    def test_realized_slippage_deviation_is_positive_cost_drift_only(self):
        report = load_json(FIXTURE_DIR / "optimizer_feedback_pass.json")
        report["realized_slippage_bps"] = report["expected_slippage_bps"] - 1.0
        report["slippage_deviation_bps"] = 1.0
        report["feedback_hash"] = optimizer_feedback_hash(report)

        errors = _optimizer_feedback_errors(report)

        self.assertIn("slippage_deviation_bps must equal positive realized-minus-expected cost difference", errors)

    def test_slippage_divergence_still_blocks_ranking(self):
        report = load_json(FIXTURE_DIR / "optimizer_feedback_slippage_divergent_fail.json")

        errors = _optimizer_feedback_errors(report)

        self.assertTrue(
            any("slippage_deviation_bps above max_allowed_slippage_deviation_bps" in error for error in errors),
            errors,
        )

    def test_known_execution_failure_cannot_remain_unknown_root_cause(self):
        report = load_json(FIXTURE_DIR / "failure_analysis_pass.json")
        unknown_execution = copy.deepcopy(report)
        unknown_execution["primary_root_cause_code"] = "UNKNOWN_ROOT_CAUSE"
        unknown_execution["root_cause_status"] = "UNKNOWN"
        unknown_execution["failure_status"] = "BLOCKED_UNKNOWN_ROOT_CAUSE"
        unknown_execution["recommended_response"] = "REQUIRE_MORE_EVIDENCE"
        unknown_execution["blockers"] = [
            {
                "code": "ROOT_CAUSE_UNKNOWN_LIVE_AFFECTING",
                "severity": "HIGH",
                "message": "Known execution feedback evidence cannot be left as unknown root cause.",
            }
        ]

        errors = _order_failure_taxonomy_errors(unknown_execution)

        self.assertIn("known execution failure evidence cannot remain outside execution failure taxonomy", errors)

    def test_slippage_taxonomy_requires_execution_feedback_blocker(self):
        report = load_json(FIXTURE_DIR / "failure_analysis_pass.json")
        report["blockers"] = []

        errors = _order_failure_taxonomy_errors(report)

        self.assertTrue(
            any(
                "SLIPPAGE_DIVERGENCE failure must carry EXECUTION_FEEDBACK_DIVERGENT blocker" in error
                or "blocking failure analysis must carry explicit blocker evidence" in error
                for error in errors
            ),
            errors,
        )

    def test_registered_backlog_validators_pass_current_fixtures(self):
        for validator in (realized_slippage_validator, order_failure_taxonomy_validator):
            result = validator().as_dict()
            self.assertEqual(result["status"], "PASS", result)
            self.assertFalse(result["blocking"], result)


if __name__ == "__main__":
    unittest.main()
