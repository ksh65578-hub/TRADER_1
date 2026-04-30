import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class FinalDecisionSchemaTest(unittest.TestCase):
    def test_final_decision_schema_is_closed_and_non_live(self):
        schema = json.loads((ROOT / "contracts" / "schema" / "final_decision.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "trader1.final_decision.v1")
        self.assertIs(schema["additionalProperties"], False)
        self.assertNotIn("live_order_allowed", schema.get("required", []))
        self.assertNotIn("can_live_trade", schema.get("required", []))


if __name__ == "__main__":
    unittest.main()
