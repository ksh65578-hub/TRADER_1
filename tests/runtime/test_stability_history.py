import json
import unittest

from trader1.dashboard.read_only_dashboard import dashboard_shell_hash
from tests.dashboard.test_read_only_dashboard import build_dashboard
from trader1.runtime.health.stability_history import (
    DEFAULT_MIN_VALIDATED_SPAN_SECONDS,
    append_stability_history,
    history_hash,
    validate_stability_history,
)


def fresh_dashboard_snapshot(dashboard: dict, marker: str) -> dict:
    snapshot = json.loads(json.dumps(dashboard))
    snapshot["generated_at_utc"] = marker
    snapshot["dashboard_hash"] = dashboard_shell_hash(snapshot)
    return snapshot


class StabilityHistoryTest(unittest.TestCase):
    def test_stability_history_is_display_only_hash_linked_and_live_blocked(self):
        dashboard = fresh_dashboard_snapshot(build_dashboard(), "2026-04-30T00:00:00Z")
        history = append_stability_history(None, dashboard)
        history = append_stability_history(history, fresh_dashboard_snapshot(dashboard, "2026-04-30T00:01:00Z"))
        result = validate_stability_history(
            history,
            expected_exchange="UPBIT",
            expected_market_type="KRW_SPOT",
            expected_mode="PAPER",
            expected_session_id="test_read_only_dashboard",
        )
        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["history_status"], "INSUFFICIENT_HISTORY")
        self.assertEqual(history["span_validation_status"], "INSUFFICIENT_SPAN")
        self.assertEqual(history["observed_span_seconds"], 60)
        self.assertEqual(history["min_validated_span_seconds"], DEFAULT_MIN_VALIDATED_SPAN_SECONDS)
        self.assertEqual(history["sample_count"], 2)
        self.assertEqual(history["samples"][1]["previous_sample_hash"], history["samples"][0]["sample_hash"])
        self.assertFalse(history["live_order_ready"])
        self.assertFalse(history["live_order_allowed"])
        self.assertFalse(history["can_live_trade"])
        self.assertFalse(history["scale_up_allowed"])

    def test_repeated_same_dashboard_snapshot_stays_insufficient(self):
        dashboard = fresh_dashboard_snapshot(build_dashboard(), "2026-04-30T00:00:00Z")
        history = append_stability_history(None, dashboard)
        history = append_stability_history(history, dashboard)

        result = validate_stability_history(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["history_status"], "INSUFFICIENT_HISTORY")
        self.assertEqual(history["sample_count"], 2)

    def test_distinct_short_span_dashboard_snapshots_stay_insufficient(self):
        dashboard = fresh_dashboard_snapshot(build_dashboard(), "2026-04-30T00:00:00Z")
        history = append_stability_history(None, dashboard)
        history = append_stability_history(history, fresh_dashboard_snapshot(dashboard, "2026-04-30T00:02:00Z"))

        result = validate_stability_history(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["history_status"], "INSUFFICIENT_HISTORY")
        self.assertEqual(history["span_validation_status"], "INSUFFICIENT_SPAN")

    def test_distinct_dashboard_snapshots_can_validate_after_minimum_span(self):
        dashboard = fresh_dashboard_snapshot(build_dashboard(), "2026-04-30T00:00:00Z")
        history = append_stability_history(None, dashboard)
        history = append_stability_history(history, fresh_dashboard_snapshot(dashboard, "2026-04-30T01:05:00Z"))

        result = validate_stability_history(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["history_status"], "VALIDATED_HISTORY")
        self.assertEqual(history["span_validation_status"], "SPAN_VALIDATED")
        self.assertGreaterEqual(history["observed_span_seconds"], DEFAULT_MIN_VALIDATED_SPAN_SECONDS)

    def test_stability_history_rejects_fake_validated_short_span(self):
        dashboard = fresh_dashboard_snapshot(build_dashboard(), "2026-04-30T00:00:00Z")
        history = append_stability_history(None, dashboard)
        history = append_stability_history(history, fresh_dashboard_snapshot(dashboard, "2026-04-30T00:02:00Z"))
        history["history_status"] = "VALIDATED_HISTORY"
        history["span_validation_status"] = "SPAN_VALIDATED"
        history["history_hash"] = history_hash(history)

        result = validate_stability_history(history)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("span field mismatch", result.message)

    def test_single_attention_sample_remains_attention_not_insufficient(self):
        dashboard = fresh_dashboard_snapshot(build_dashboard(), "2026-04-30T00:00:00Z")
        dashboard["stability_trends"]["status"] = "ATTENTION"
        dashboard["stability_trends"]["metrics"][0]["status"] = "STALE"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)

        history = append_stability_history(None, dashboard)
        result = validate_stability_history(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["history_status"], "ATTENTION")
        self.assertEqual(history["sample_count"], 1)

    def test_stability_history_blocks_live_permission_mutation(self):
        history = append_stability_history(None, fresh_dashboard_snapshot(build_dashboard(), "2026-04-30T00:00:00Z"))
        history["live_order_allowed"] = True
        history["history_hash"] = history_hash(history)
        result = validate_stability_history(history)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_stability_history_blocks_hash_chain_mutation(self):
        dashboard = fresh_dashboard_snapshot(build_dashboard(), "2026-04-30T00:00:00Z")
        history = append_stability_history(None, dashboard)
        history = append_stability_history(history, fresh_dashboard_snapshot(dashboard, "2026-04-30T01:05:00Z"))
        history["samples"][1]["previous_sample_hash"] = "BAD"
        history["history_hash"] = history_hash(history)
        result = validate_stability_history(history)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_stability_history_isolates_scope_mismatch(self):
        history = append_stability_history(None, fresh_dashboard_snapshot(build_dashboard(), "2026-04-30T00:00:00Z"))
        other = fresh_dashboard_snapshot(build_dashboard(), "2026-04-30T00:01:00Z")
        other["session_id"] = "different_session"
        other["dashboard_hash"] = "A" * 64
        isolated = append_stability_history(history, other)
        self.assertEqual(isolated["sample_count"], 1)
        self.assertEqual(isolated["reset_reason"], "PREVIOUS_HISTORY_ISOLATED")
        self.assertEqual(isolated["session_id"], "different_session")
        result = validate_stability_history(isolated, expected_session_id="different_session")
        self.assertEqual(result.status, "PASS")


if __name__ == "__main__":
    unittest.main()
