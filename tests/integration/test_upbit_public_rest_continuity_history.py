import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.adapters.upbit.market_data import build_upbit_public_candle_data_from_rest_payload
from trader1.runtime.paper.upbit_public_rest_continuity import build_upbit_public_rest_continuity_report
from trader1.runtime.paper.upbit_public_rest_continuity_history import (
    append_upbit_public_rest_continuity_history,
    build_upbit_public_rest_continuity_history_report,
    upbit_public_rest_continuity_history_hash,
    validate_upbit_public_rest_continuity_history_report,
    write_upbit_public_rest_continuity_history_report,
)


class UpbitPublicRestContinuityHistoryTest(unittest.TestCase):
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

    def _continuity(self, continuity_id: str, starts: list[int]) -> dict[str, object]:
        return build_upbit_public_rest_continuity_report(
            continuity_id=continuity_id,
            session_id="mvp1_upbit_paper_launcher",
            fetcher=self._sequence_fetcher(starts),
        )

    def test_two_pass_attempts_create_paper_only_healthy_history(self):
        history = build_upbit_public_rest_continuity_history_report(
            history_id="mock-history-pass",
            session_id="mvp1_upbit_paper_launcher",
            continuity_attempts=[
                self._continuity("mock-history-pass-1", [0, 1]),
                self._continuity("mock-history-pass-2", [1, 2]),
            ],
        )
        result = validate_upbit_public_rest_continuity_history_report(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["pass_attempt_count"], 2)
        self.assertEqual(history["blocked_attempt_count"], 0)
        self.assertEqual(history["evidence_role"], "PAPER_DATA_CONTINUITY_HISTORY_ONLY_NOT_LIVE_READY")
        self.assertFalse(history["long_run_evidence_eligible"])
        self.assertFalse(history["promotion_eligible"])
        self.assertFalse(history["live_order_allowed"])
        self.assertFalse(history["can_live_trade"])
        self.assertFalse(history["scale_up_allowed"])

    def test_latest_duplicate_attempt_warns_without_live_ready(self):
        history = build_upbit_public_rest_continuity_history_report(
            history_id="mock-history-warn",
            session_id="mvp1_upbit_paper_launcher",
            continuity_attempts=[
                self._continuity("mock-history-pass-1", [0, 1]),
                self._continuity("mock-history-duplicate", [1, 1]),
            ],
        )
        result = validate_upbit_public_rest_continuity_history_report(history)

        self.assertEqual(result.status, "WARN")
        self.assertEqual(result.blocker_code, "DATA_QUALITY_INSUFFICIENT")
        self.assertEqual(history["duplicate_latest_event_block_count"], 1)
        self.assertEqual(history["non_advancing_block_count"], 1)
        self.assertEqual(history["latest_attempt_status"], "WARN")
        self.assertEqual(history["continuity_health_status"], "WARN")
        self.assertFalse(history["live_order_ready"])

    def test_empty_history_is_blocked_not_ready(self):
        history = build_upbit_public_rest_continuity_history_report(
            history_id="mock-history-empty",
            session_id="mvp1_upbit_paper_launcher",
            continuity_attempts=[],
        )
        result = validate_upbit_public_rest_continuity_history_report(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DATA_UNAVAILABLE")
        self.assertEqual(history["total_attempt_count"], 0)
        self.assertFalse(history["live_order_allowed"])

    def test_live_flag_mutation_is_blocked(self):
        history = build_upbit_public_rest_continuity_history_report(
            history_id="mock-history-live-mutation",
            session_id="mvp1_upbit_paper_launcher",
            continuity_attempts=[
                self._continuity("mock-history-pass-1", [0, 1]),
                self._continuity("mock-history-pass-2", [1, 2]),
            ],
        )
        history["live_order_allowed"] = True
        history["history_hash"] = upbit_public_rest_continuity_history_hash(history)
        result = validate_upbit_public_rest_continuity_history_report(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_writer_and_append_preserve_paper_namespace_and_previous_attempts(self):
        first = self._continuity("mock-history-append-1", [0, 1])
        second = self._continuity("mock-history-append-2", [1, 2])
        with TemporaryDirectory() as tmp:
            first_path, first_history = append_upbit_public_rest_continuity_history(root=Path(tmp), continuity_report=first)
            second_path, second_history = append_upbit_public_rest_continuity_history(root=Path(tmp), continuity_report=second)
            explicit_path = write_upbit_public_rest_continuity_history_report(root=Path(tmp), report=second_history)

            self.assertEqual(first_path, second_path)
            self.assertEqual(second_path, explicit_path)
            self.assertTrue(second_path.exists())
            self.assertIn("upbit/krw_spot/paper", second_path.as_posix())
            self.assertEqual(first_history["total_attempt_count"], 1)
            self.assertEqual(second_history["total_attempt_count"], 2)
            self.assertEqual(validate_upbit_public_rest_continuity_history_report(second_history).status, "PASS")
            self.assertFalse(second_history["live_order_allowed"])

    def test_append_quarantines_corrupted_previous_history(self):
        first = self._continuity("mock-history-corrupt-recovery", [0, 1])
        with TemporaryDirectory() as tmp:
            history_dir = Path(tmp) / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "market_data" / "public"
            history_dir.mkdir(parents=True)
            history_path = history_dir / "rest_continuity_history.json"
            history_path.write_text("{not-valid-json", encoding="utf-8")

            _, history = append_upbit_public_rest_continuity_history(root=Path(tmp), continuity_report=first)
            quarantined = list(history_dir.glob("rest_continuity_history.quarantine.*.corrupt-json.json"))

            self.assertEqual(len(quarantined), 1)
            self.assertEqual(history["total_attempt_count"], 1)
            self.assertTrue(history_path.exists())
            self.assertFalse(history["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
