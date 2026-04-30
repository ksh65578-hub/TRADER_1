import json
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import _patch_result_schema_error, run_fixture_file, run_validators


ROOT = Path(__file__).resolve().parents[2]


class MVP0ValidatorsTest(unittest.TestCase):
    def test_mvp0_core_validators_pass_current_artifacts(self):
        results = run_validators()
        statuses = {result["validator_id"]: result["status"] for result in results}
        self.assertEqual(statuses["authority_integrity_validator"], "PASS")
        self.assertEqual(statuses["external_authority_manifest_validator"], "PASS")
        self.assertEqual(statuses["registry_validator"], "PASS")
        self.assertEqual(statuses["schema_validator"], "PASS")
        self.assertEqual(statuses["closed_enum_validator"], "PASS")
        self.assertEqual(statuses["common_defs_drift_validator"], "PASS")
        self.assertEqual(statuses["patch_result_schema_validator"], "PASS")
        self.assertEqual(statuses["coverage_index_validator"], "PASS")
        self.assertEqual(statuses["active_schema_extraction_validator"], "PASS")
        self.assertEqual(statuses["generated_artifact_dirty_validator"], "PASS")

    def test_live_blocking_fixtures_have_pass_fail_blocked_outcomes(self):
        fixture_dir = ROOT / "tests" / "validators" / "fixtures"
        expected = {
            "mvp0_core_pass.json": "PASS",
            "mvp0_core_fail.json": "FAIL",
            "mvp0_core_blocked.json": "BLOCKED",
        }
        for filename, expected_status in expected.items():
            with self.subTest(filename=filename):
                result = run_fixture_file(fixture_dir / filename)
                self.assertEqual(result["status"], expected_status)

    def test_live_blocked_original_fixture_still_blocks_order_adapter(self):
        fixture = json.loads(
            (ROOT / "tests" / "live_blocked" / "fixtures" / "live_ready_missing.json").read_text(encoding="utf-8")
        )
        self.assertFalse(fixture["expected_order_adapter_called"])
        self.assertFalse(fixture["live_order_ready"])
        self.assertFalse(fixture["live_order_allowed"])
        self.assertFalse(fixture["can_live_trade"])

    def test_patch_result_history_keeps_non_live_invariants(self):
        patch_dir = ROOT / "system" / "evidence" / "patch_results"
        patch_paths = sorted(patch_dir.glob("*.patch_result.json"))
        self.assertGreater(len(patch_paths), 0)
        forbidden_true_fields = (
            "live_order_ready_after",
            "live_order_allowed_after",
            "can_live_trade_after",
            "optimizer_live_mutation_detected",
            "optimizer_live_order_allowed_after",
            "convergence_live_mutation_detected",
            "convergence_live_order_allowed_after",
            "scale_up_allowed_after",
        )
        for path in patch_paths:
            with self.subTest(path=path.name):
                patch = json.loads(path.read_text(encoding="utf-8"))
                self.assertNotEqual(patch.get("patch_class"), "LIVE_ENABLING_PATCH")
                self.assertEqual(patch.get("removed_requirements"), [])
                self.assertEqual(patch.get("merged_requirements"), [])
                self.assertIn(patch.get("coverage_index_result"), {"PASS", "UNCHANGED_PASS", "UPDATED_PASS"})
                self.assertFalse(patch.get("file_split"))
                self.assertFalse(patch.get("detail_reduction_allowed"))
                self.assertFalse(patch.get("semantic_reduction_allowed"))
                self.assertFalse(patch.get("scale_up_allowed_before"))
                for field in forbidden_true_fields:
                    self.assertFalse(patch.get(field), field)

    def test_patch_result_schema_validator_scans_full_history(self):
        result = run_validators(["patch_result_schema_validator"])[0]
        self.assertEqual(result["status"], "PASS")
        self.assertIn("patch_result artifacts", result["notes"])

    def test_current_state_implemented_validators_are_callable(self):
        state = json.loads((ROOT / "contracts" / "generated" / "current_implementation_state.json").read_text(encoding="utf-8"))
        validator_ids = state["implemented_validator_ids"]
        results = run_validators(validator_ids)
        statuses = {result["validator_id"]: result["status"] for result in results}
        self.assertEqual(len(results), len(validator_ids))
        self.assertEqual(statuses["live_blocked_scaffold_validator"], "PASS")
        self.assertNotIn("UNTESTED", statuses.values())
        self.assertEqual([validator_id for validator_id in validator_ids if validator_id not in statuses], [])

    def test_patch_result_schema_subset_rejects_type_enum_and_extra_field_drift(self):
        schema = json.loads((ROOT / "contracts" / "schema" / "patch_result.schema.json").read_text(encoding="utf-8"))
        patch = json.loads(
            (ROOT / "system" / "evidence" / "patch_results" / "MVP4_FULL_SAFETY_AUDIT.patch_result.json").read_text(
                encoding="utf-8"
            )
        )

        bad_type = dict(patch)
        bad_type["live_order_allowed_after"] = "false"
        self.assertIn(
            "type mismatch",
            _patch_result_schema_error(schema, bad_type, ROOT / "system/evidence/patch_results/synthetic.patch_result.json"),
        )

        bad_enum = dict(patch)
        bad_enum["target_mvp_level"] = "MVP-99"
        self.assertIn(
            "enum mismatch",
            _patch_result_schema_error(schema, bad_enum, ROOT / "system/evidence/patch_results/synthetic.patch_result.json"),
        )

        bad_extra = dict(patch)
        bad_extra["live_order_allowed_shadow"] = True
        self.assertIn(
            "outside patch_result schema",
            _patch_result_schema_error(schema, bad_extra, ROOT / "system/evidence/patch_results/synthetic.patch_result.json"),
        )


if __name__ == "__main__":
    unittest.main()
