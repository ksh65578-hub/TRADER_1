import copy
import unittest
from pathlib import Path

from trader1.runtime.readiness.live_ready_snapshot import (
    attach_writer_input_hash,
    build_writer_input,
    evaluate_live_ready_snapshot_writer,
)
from trader1.validation.mvp0_validators import (
    _candidate_scorecard_net_ev_errors,
    _overfit_diagnostic_errors,
    _parameter_narrowing_errors,
    candidate_scorecard_validator,
    current_authority_hashes,
    load_json,
    parameter_bound_validator,
    promotion_threshold_validator,
    ranking_stability_validator,
    sha256_file,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class OptimizerBacklogValidatorsTest(unittest.TestCase):
    def test_candidate_scorecard_validator_rejects_missing_evidence(self):
        scorecard = load_json(FIXTURE_DIR / "candidate_scorecard_net_ev_pass.json")
        scorecard["source_evidence_ids"] = []

        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertTrue(any("source_evidence_ids" in error for error in errors), errors)

    def test_ranking_stability_rejects_low_score(self):
        diagnostic = load_json(FIXTURE_DIR / "overfit_diagnostic_pass.json")
        diagnostic["ranking_stability_score"] = diagnostic["min_required_ranking_stability_score"] - 0.01

        errors = _overfit_diagnostic_errors(diagnostic)

        self.assertIn(
            "ranking_stability_score below min_required_ranking_stability_score while robustness_eligible=true",
            errors,
        )

    def test_parameter_bound_rejects_expanding_narrow_range(self):
        report = load_json(FIXTURE_DIR / "parameter_narrowing_pass.json")
        expanded = copy.deepcopy(report)
        expanded["parameter_changes"][0]["proposed_min"] = expanded["parameter_changes"][0]["previous_min"] - 1

        errors = _parameter_narrowing_errors(expanded)

        self.assertIn("parameter change 0 expands bounds while marked NARROW", errors)

    def test_promotion_threshold_does_not_enable_live_readiness(self):
        registry_path = ROOT / "contracts" / "registry.yaml"
        module_path = ROOT / "trader1" / "runtime" / "readiness" / "live_ready_snapshot.py"
        writer_input = build_writer_input(
            authority=current_authority_hashes(),
            exchange="UPBIT",
            market_type="KRW_SPOT",
            strategy_id="mvp4_strategy",
            strategy_build_id="mvp4_strategy_build",
            parameter_hash="A" * 64,
            risk_profile="CONSERVATIVE",
            registry_hash=sha256_file(registry_path),
            schema_bundle_hash=sha256_file(ROOT / "contracts" / "schema" / "common.defs.schema.json"),
            source_tree_hash=sha256_file(module_path),
            writer_input_id="mvp4_promotion_threshold_test_input",
        )
        writer_input["promotion_threshold_status"] = "PASS"
        writer_input["live_ready_snapshot_writer_status"] = "PASS"
        writer_input["blockers"] = []
        writer_input["evidence_manifest_hash"] = "E" * 64
        writer_input = attach_writer_input_hash(writer_input)

        result = evaluate_live_ready_snapshot_writer(writer_input, evidence_manifest_present=True)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_READY_SNAPSHOT_WRITER_UNTESTED")
        self.assertFalse(result.would_write_snapshot)
        self.assertFalse(result.live_order_ready)
        self.assertFalse(result.live_order_allowed)
        self.assertFalse(result.can_live_trade)

    def test_registered_backlog_validators_pass_current_fixtures(self):
        for validator in (
            candidate_scorecard_validator,
            ranking_stability_validator,
            parameter_bound_validator,
            promotion_threshold_validator,
        ):
            result = validator().as_dict()
            self.assertEqual(result["status"], "PASS", result)
            self.assertFalse(result["blocking"], result)


if __name__ == "__main__":
    unittest.main()
