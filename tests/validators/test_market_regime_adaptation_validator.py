import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _candidate_scoped_performance_source_binding_count,
    _market_regime_adaptation_errors,
    load_json,
    market_regime_adaptation_validator,
)
from trader1.research.profitability.candidate_scorecard import has_required_robustness_source_ids


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class MarketRegimeAdaptationValidatorTest(unittest.TestCase):
    def test_pass_fixture_links_fresh_regime_to_strategy_dependencies(self):
        report = load_json(FIXTURE_DIR / "market_regime_adaptation_pass.json")

        errors = _market_regime_adaptation_errors(report)

        self.assertEqual(errors, [])
        self.assertTrue(has_required_robustness_source_ids(report["source_evidence_ids"]))
        self.assertGreater(_candidate_scoped_performance_source_binding_count(report["source_evidence_ids"]), 0)

    def test_entry_allowed_requires_robustness_source_evidence_ids(self):
        report = load_json(FIXTURE_DIR / "market_regime_adaptation_pass.json")
        report["source_evidence_ids"] = [
            source_id
            for source_id in report["source_evidence_ids"]
            if not source_id.startswith("bootstrap:")
        ]

        errors = _market_regime_adaptation_errors(report)

        self.assertIn(
            "entry_allowed market regime adaptation requires OOS, walk-forward, and bootstrap source evidence ids",
            errors,
        )

    def test_entry_allowed_requires_candidate_scoped_performance_sources(self):
        report = load_json(FIXTURE_DIR / "market_regime_adaptation_pass.json")
        report["source_evidence_ids"] = [
            source_id
            for source_id in report["source_evidence_ids"]
            if not source_id.startswith("execution_quality:")
        ]

        errors = _market_regime_adaptation_errors(report)

        self.assertIn(
            "entry_allowed market regime adaptation requires candidate-scoped closed trade, execution quality, and performance summary source ids",
            errors,
        )

    def test_live_permission_is_rejected(self):
        report = load_json(FIXTURE_DIR / "market_regime_adaptation_live_flag_fail.json")

        errors = _market_regime_adaptation_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_stale_data_cannot_allow_entry(self):
        report = load_json(FIXTURE_DIR / "market_regime_adaptation_stale_data_entry_fail.json")

        errors = _market_regime_adaptation_errors(report)

        self.assertIn("entry_allowed must be false when regime data is not FRESH", errors)

    def test_risk_off_cannot_allow_entry(self):
        report = load_json(FIXTURE_DIR / "market_regime_adaptation_risk_off_entry_fail.json")

        errors = _market_regime_adaptation_errors(report)

        self.assertIn("RISK_OFF regime adaptation must set entry_allowed=false", errors)

    def test_live_observation_is_blocked_in_mvp4(self):
        report = load_json(FIXTURE_DIR / "market_regime_adaptation_live_observation_fail.json")

        errors = _market_regime_adaptation_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_entry_requires_dependency_pass_status(self):
        report = load_json(FIXTURE_DIR / "market_regime_adaptation_missing_dependency_fail.json")

        errors = _market_regime_adaptation_errors(report)

        self.assertIn("entry_allowed requires symbol_strategy_regime_fit_validator_status=PASS", errors)

    def test_source_artifact_roles_are_required(self):
        report = load_json(FIXTURE_DIR / "market_regime_adaptation_missing_source_role_fail.json")

        errors = _market_regime_adaptation_errors(report)

        self.assertTrue(any("market regime adaptation missing source artifact roles" in error for error in errors), errors)

    def test_current_validator_fixtures_pass(self):
        result = market_regime_adaptation_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
