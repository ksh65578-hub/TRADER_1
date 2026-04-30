import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class MVP0ContractScaffoldTest(unittest.TestCase):
    def test_json_artifacts_parse(self):
        for path in [
            *sorted((ROOT / "contracts" / "schema").glob("*.schema.json")),
            ROOT / "contracts" / "authority_manifest.json",
            ROOT / "contracts" / "generated" / "authority_section_map.json",
            ROOT / "contracts" / "generated" / "requirement_index.json",
            ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json",
            ROOT / "contracts" / "generated" / "read_cache_manifest.json",
            ROOT / "contracts" / "generated" / "current_implementation_state.json",
            ROOT / "contracts" / "validators" / "validator_registry.json",
        ]:
            with self.subTest(path=str(path)):
                json.loads(path.read_text(encoding="utf-8"))

    def test_registry_is_json_yaml_and_live_defaults_false(self):
        registry = json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))
        self.assertEqual(registry["registry_schema_id"], "trader1.registry.v1")
        self.assertFalse(registry["live_defaults"]["live_order_ready"])
        self.assertFalse(registry["live_defaults"]["live_order_allowed"])
        self.assertFalse(registry["live_defaults"]["can_live_trade"])

    def test_patch_result_invariants(self):
        patch = json.loads(
            (ROOT / "system" / "evidence" / "patch_results" / "MVP0_CONTRACT_BASELINE.patch_result.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(patch["removed_requirements"], [])
        self.assertFalse(patch["file_split"])
        self.assertFalse(patch["detail_reduction_allowed"])
        self.assertFalse(patch["semantic_reduction_allowed"])
        self.assertFalse(patch["live_order_ready_after"])
        self.assertFalse(patch["live_order_allowed_after"])
        self.assertFalse(patch["can_live_trade_after"])


if __name__ == "__main__":
    unittest.main()
