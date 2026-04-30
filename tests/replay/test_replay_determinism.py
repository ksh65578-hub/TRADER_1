import unittest

from trader1.research.replay.replay_runner import (
    build_replay_consistency_report,
    replay_consistency_hash,
    validate_replay_consistency_report,
)


class ReplayDeterminismTest(unittest.TestCase):
    def test_same_input_replays_to_same_hash(self):
        report = build_replay_consistency_report(
            replay_id="replay-pass",
            strategy_unit_id="strategy-1",
            parameter_hash="A" * 64,
            input_events=[{"event_id": "event-1", "price": "100"}],
        )
        result = validate_replay_consistency_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(len(set(report["result_hashes"])), 1)

    def test_replay_hash_mismatch_fails(self):
        report = build_replay_consistency_report(
            replay_id="replay-fail",
            strategy_unit_id="strategy-1",
            parameter_hash="A" * 64,
            input_events=[{"event_id": "event-1", "price": "100"}],
        )
        report["result_hashes"][1] = "B" * 64
        report["deterministic_pass"] = False
        report["replay_consistency_hash"] = replay_consistency_hash(report)
        result = validate_replay_consistency_report(report)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")

    def test_replay_live_mutation_blocks(self):
        report = build_replay_consistency_report(
            replay_id="replay-live",
            strategy_unit_id="strategy-1",
            parameter_hash="A" * 64,
            input_events=[{"event_id": "event-1", "price": "100"}],
        )
        report["live_order_allowed"] = True
        report["replay_consistency_hash"] = replay_consistency_hash(report)
        result = validate_replay_consistency_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
