import copy
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import (
    _optimizer_memory_state_errors,
    load_json,
    optimizer_memory_state_validator,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "validators" / "fixtures"


class OptimizerMemoryStateValidatorTest(unittest.TestCase):
    def test_pass_fixture_is_append_audit_hash_linked_memory(self):
        report = load_json(FIXTURE_DIR / "optimizer_memory_state_pass.json")

        errors = _optimizer_memory_state_errors(report)

        self.assertEqual(errors, [])

    def test_memory_state_cannot_carry_live_permission(self):
        report = load_json(FIXTURE_DIR / "optimizer_memory_state_live_flag_fail.json")

        errors = _optimizer_memory_state_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_memory_reset_without_audit_is_rejected(self):
        report = load_json(FIXTURE_DIR / "optimizer_memory_state_reset_without_audit_fail.json")

        errors = _optimizer_memory_state_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_failed_candidate_forgetting_is_rejected(self):
        report = load_json(FIXTURE_DIR / "optimizer_memory_state_forget_failed_candidate_fail.json")

        errors = _optimizer_memory_state_errors(report)

        self.assertTrue(any("expected const True" in error for error in errors), errors)

    def test_cross_scope_memory_reuse_is_rejected(self):
        report = load_json(FIXTURE_DIR / "optimizer_memory_state_cross_scope_reuse_fail.json")

        errors = _optimizer_memory_state_errors(report)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_failed_candidates_remain_promotion_blocked(self):
        report = load_json(FIXTURE_DIR / "optimizer_memory_state_failed_candidate_unblocked_fail.json")

        errors = _optimizer_memory_state_errors(report)

        self.assertIn("FAILED candidate must remain promotion_blocked: candidate_failed_after_cost", errors)

    def test_append_write_requires_previous_hash(self):
        report = load_json(FIXTURE_DIR / "optimizer_memory_state_append_without_hash_fail.json")

        errors = _optimizer_memory_state_errors(report)

        self.assertIn("memory_sequence_number greater than 1 requires previous_memory_state_hash", errors)
        self.assertIn("APPEND memory write requires previous_memory_state_hash", errors)

    def test_live_source_mode_is_rejected(self):
        report = load_json(FIXTURE_DIR / "optimizer_memory_state_live_source_mode_fail.json")

        errors = _optimizer_memory_state_errors(report)

        self.assertTrue(any("LIVE" in error for error in errors), errors)

    def test_failed_candidate_count_must_match_records(self):
        report = load_json(FIXTURE_DIR / "optimizer_memory_state_pass.json")
        tampered = copy.deepcopy(report)
        tampered["failed_candidate_count"] = 0

        errors = _optimizer_memory_state_errors(tampered)

        self.assertIn("failed_candidate_count must match FAILED candidate records", errors)

    def test_active_memory_requires_candidate_scoped_performance_source_binding(self):
        report = load_json(FIXTURE_DIR / "optimizer_memory_state_pass.json")
        tampered = copy.deepcopy(report)
        tampered["source_artifact_ids"] = [
            source_id
            for source_id in tampered["source_artifact_ids"]
            if not str(source_id).startswith(("closed_trades:", "execution_quality:", "performance_summary:"))
        ]

        errors = _optimizer_memory_state_errors(tampered)

        self.assertIn(
            "ACTIVE optimizer memory record requires candidate-scoped performance source artifact ids: candidate_active_after_cost",
            errors,
        )

    def test_current_validator_fixtures_pass(self):
        result = optimizer_memory_state_validator().as_dict()

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["blocking"])


if __name__ == "__main__":
    unittest.main()
