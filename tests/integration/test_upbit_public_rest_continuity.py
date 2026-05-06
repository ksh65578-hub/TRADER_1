import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.adapters.upbit.market_data import build_upbit_public_candle_data_from_rest_payload
from trader1.runtime.paper.upbit_public_rest_continuity import (
    build_upbit_public_rest_continuity_report,
    upbit_public_rest_continuity_hash,
    validate_upbit_public_rest_continuity_report,
    write_upbit_public_rest_continuity_report,
)


class UpbitPublicRestContinuityTest(unittest.TestCase):
    def _payload(self, start_minute: int) -> list[dict[str, object]]:
        return [
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": f"2026-04-30T09:{start_minute + index:02d}:00",
                "opening_price": 1000000 + (start_minute + index) * 1000,
                "high_price": 1002500 + (start_minute + index) * 1000,
                "low_price": 998000 + (start_minute + index) * 1000,
                "trade_price": 1000500 + (start_minute + index) * 1000,
                "candle_acc_trade_volume": 2 + index,
            }
            for index in range(5, -1, -1)
        ]

    def _sequence_fetcher(self, starts: list[int]):
        calls = {"count": 0}

        def fetcher(*, symbol: str, session_id: str, timeout_seconds: float) -> dict[str, object]:
            index = min(calls["count"], len(starts) - 1)
            calls["count"] += 1
            return build_upbit_public_candle_data_from_rest_payload(
                payload=self._payload(starts[index]),
                symbol=symbol,
                session_id=session_id,
            )

        return fetcher

    def test_advancing_mocked_samples_pass_as_paper_only_continuity(self):
        report = build_upbit_public_rest_continuity_report(
            continuity_id="mock-continuity-pass",
            session_id="mvp1_upbit_paper_launcher",
            fetcher=self._sequence_fetcher([0, 1]),
        )
        result = validate_upbit_public_rest_continuity_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["pass_sample_count"], 2)
        self.assertEqual(report["evidence_role"], "PAPER_DATA_CONTINUITY_ONLY_NOT_LIVE_READY")
        self.assertGreater(report["observed_span_seconds"], 0)
        self.assertFalse(report["duplicate_latest_event_time_detected"])
        self.assertFalse(report["non_advancing_sample_detected"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_duplicate_latest_timestamp_warns_without_live_ready(self):
        report = build_upbit_public_rest_continuity_report(
            continuity_id="mock-continuity-duplicate",
            session_id="mvp1_upbit_paper_launcher",
            fetcher=self._sequence_fetcher([0, 0]),
        )
        result = validate_upbit_public_rest_continuity_report(report)

        self.assertEqual(result.status, "WARN")
        self.assertEqual(result.blocker_code, "DATA_QUALITY_INSUFFICIENT")
        self.assertEqual(report["continuity_status"], "WARN")
        self.assertTrue(report["duplicate_latest_event_time_detected"])
        self.assertTrue(report["non_advancing_sample_detected"])
        self.assertFalse(report["live_order_allowed"])

    def test_no_network_mode_blocks_without_live_ready(self):
        report = build_upbit_public_rest_continuity_report(
            continuity_id="mock-continuity-no-network",
            session_id="mvp1_upbit_paper_launcher",
            attempt_network=False,
        )
        result = validate_upbit_public_rest_continuity_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DATA_UNAVAILABLE")
        self.assertEqual(report["pass_sample_count"], 0)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])

    def test_live_flag_mutation_is_blocked(self):
        report = build_upbit_public_rest_continuity_report(
            continuity_id="mock-continuity-live-mutation",
            session_id="mvp1_upbit_paper_launcher",
            fetcher=self._sequence_fetcher([0, 1]),
        )
        report["live_order_allowed"] = True
        report["continuity_hash"] = upbit_public_rest_continuity_hash(report)
        result = validate_upbit_public_rest_continuity_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_writer_persists_continuity_report_under_paper_namespace(self):
        report = build_upbit_public_rest_continuity_report(
            continuity_id="mock-continuity-writer",
            session_id="mvp1_upbit_paper_launcher",
            fetcher=self._sequence_fetcher([0, 1]),
        )
        with TemporaryDirectory() as tmp:
            path = write_upbit_public_rest_continuity_report(root=Path(tmp), report=report)
            self.assertTrue(path.exists())
            self.assertIn("upbit/krw_spot/paper", path.as_posix())
            self.assertFalse(report["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
