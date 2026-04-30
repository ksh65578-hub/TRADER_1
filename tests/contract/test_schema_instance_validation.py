import json
import unittest
from pathlib import Path

from tests.dashboard.test_read_only_dashboard import build_dashboard
from trader1.validation.mvp0_validators import run_validators
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)


ROOT = Path(__file__).resolve().parents[2]


class SchemaInstanceValidationTest(unittest.TestCase):
    def test_dashboard_runtime_instance_matches_schema(self):
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        dashboard = build_dashboard()
        schema = schema_for_instance(dashboard, schema_bundle)
        self.assertIsNotNone(schema)
        result = validate_instance_against_schema(dashboard, schema, schema_bundle)
        self.assertEqual(result.status, "PASS", result.errors)

    def test_dashboard_extra_property_fails_schema_instance_validation(self):
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        dashboard = build_dashboard()
        dashboard["unexpected_execution_truth"] = True
        schema = schema_for_instance(dashboard, schema_bundle)
        result = validate_instance_against_schema(dashboard, schema, schema_bundle)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("additional properties", result.errors[0])

    def test_dashboard_metric_count_mismatch_fails_schema_instance_validation(self):
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        dashboard = build_dashboard()
        dashboard["stability_trends"]["metrics"] = dashboard["stability_trends"]["metrics"][:-1]
        schema = schema_for_instance(dashboard, schema_bundle)
        result = validate_instance_against_schema(dashboard, schema, schema_bundle)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("minItems", result.errors[0])

    def test_runtime_schema_instance_validator_passes_current_contract(self):
        results = run_validators(["runtime_schema_instance_validator"])
        self.assertEqual(results[0]["status"], "PASS", json.dumps(results[0], indent=2))


if __name__ == "__main__":
    unittest.main()
