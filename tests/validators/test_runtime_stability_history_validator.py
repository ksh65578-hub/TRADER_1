import json
import unittest
from pathlib import Path

from trader1.runtime.health.stability_history import history_hash, validate_stability_history
from trader1.validation.mvp0_validators import run_validators


ROOT = Path(__file__).resolve().parents[2]
UPBIT_PAPER_HISTORY = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "stability_history.json"


def load_history() -> dict:
    return json.loads(UPBIT_PAPER_HISTORY.read_text(encoding="utf-8"))


class RuntimeStabilityHistoryValidatorTest(unittest.TestCase):
    def test_runtime_stability_history_validator_passes_current_artifacts(self):
        result = run_validators(["runtime_stability_history_validator"])[0]
        self.assertEqual(result["status"], "PASS")
        self.assertIn("stability histories", result["notes"])

    def test_runtime_stability_history_blocks_live_or_scaleup_drift(self):
        history = load_history()
        history["live_order_allowed"] = True
        history["history_hash"] = history_hash(history)

        result = validate_stability_history(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_runtime_stability_history_blocks_scope_mismatch(self):
        history = load_history()

        result = validate_stability_history(history, expected_exchange="BINANCE")

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_runtime_stability_history_rejects_fake_validated_history(self):
        history = load_history()
        history["samples"] = [history["samples"][0]]
        history["sample_count"] = 1
        history["stable_sample_count"] = 1 if history["samples"][0]["status"] == "STABLE" else 0
        history["attention_sample_count"] = 1 if history["samples"][0]["status"] == "ATTENTION" else 0
        history["error_sample_count"] = 1 if history["samples"][0]["status"] == "ERROR" else 0
        history["stale_metric_sample_count"] = 1 if history["samples"][0]["metric_status_counts"]["STALE"] else 0
        history["latest_sample_hash"] = history["samples"][0]["sample_hash"]
        history["first_sample_at_utc"] = history["samples"][0]["generated_at_utc"]
        history["latest_sample_at_utc"] = history["samples"][0]["generated_at_utc"]
        history["observed_span_seconds"] = 0
        history["span_validation_status"] = "INSUFFICIENT_SPAN"
        history["history_status"] = "VALIDATED_HISTORY"
        history["history_hash"] = history_hash(history)

        result = validate_stability_history(history)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("status mismatch", result.message)

    def test_runtime_stability_history_rejects_aggregate_count_mismatch(self):
        history = load_history()
        actual_stable_count = sum(1 for sample in history["samples"] if sample["status"] == "STABLE")
        history["stable_sample_count"] = actual_stable_count + 1
        history["history_hash"] = history_hash(history)

        result = validate_stability_history(history)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("aggregate count mismatch", result.message)


if __name__ == "__main__":
    unittest.main()
