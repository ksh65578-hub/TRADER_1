import json
import unittest
from pathlib import Path

from trader1.validation.mvp0_validators import run_validators
from trader1.validation.namespace import (
    NamespaceScope,
    artifact_path,
    classify_dashboard_artifact,
    validate_artifact_path,
    validate_namespace_join,
    validate_truth_override,
)


ROOT = Path(__file__).resolve().parents[2]


class NamespaceTruthTest(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))
        self.scope = NamespaceScope(exchange="UPBIT", market_type="KRW_SPOT", mode="PAPER", session_id="session_mvp0")

    def test_artifact_paths_include_required_namespace_segments(self):
        evidence_path = artifact_path("evidence", self.scope, self.registry, "evidence_manifest.json")
        self.assertEqual(evidence_path, "system/evidence/upbit/krw_spot/paper/session_mvp0/evidence_manifest.json")
        self.assertEqual(validate_artifact_path(evidence_path, self.scope, self.registry).status, "PASS")

    def test_cross_scope_raw_joins_are_blocked(self):
        cases = [
            NamespaceScope(exchange="UPBIT", market_type="KRW_SPOT", mode="LIVE", session_id="session_mvp0"),
            NamespaceScope(exchange="BINANCE", market_type="KRW_SPOT", mode="PAPER", session_id="session_mvp0"),
            NamespaceScope(exchange="UPBIT", market_type="SPOT", mode="PAPER", session_id="session_mvp0"),
            NamespaceScope(exchange="UPBIT", market_type="KRW_SPOT", mode="PAPER", session_id="session_other"),
        ]
        for other in cases:
            with self.subTest(other=other):
                self.assertEqual(validate_namespace_join(self.scope, other).status, "BLOCKED")

    def test_dashboard_truth_cannot_override_execution_truth(self):
        self.assertEqual(classify_dashboard_artifact("summary.json"), "dashboard_serving_truth")
        self.assertEqual(validate_truth_override("dashboard_serving_truth", "execution_truth").status, "BLOCKED")
        self.assertEqual(validate_truth_override("execution_truth", "dashboard_serving_truth").status, "PASS")

    def test_namespace_validators_pass_current_contract(self):
        statuses = {result["validator_id"]: result["status"] for result in run_validators(["path_namespace_validator", "truth_hierarchy_validator"])}
        self.assertEqual(statuses["path_namespace_validator"], "PASS")
        self.assertEqual(statuses["truth_hierarchy_validator"], "PASS")


if __name__ == "__main__":
    unittest.main()
