import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.adapters.upbit.market_data import build_upbit_public_candle_data_from_rest_payload
from trader1.runtime.paper.upbit_public_rest_sample import (
    build_upbit_public_rest_sample_report,
    upbit_public_rest_sample_hash,
    validate_upbit_public_rest_sample_report,
    write_upbit_public_rest_sample_report,
)


class UpbitPublicRestSampleTest(unittest.TestCase):
    def _payload(self) -> list[dict[str, object]]:
        return [
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": f"2026-04-30T09:{index:02d}:00",
                "opening_price": 1000000 + index * 1000,
                "high_price": 1002500 + index * 1000,
                "low_price": 998000 + index * 1000,
                "trade_price": 1000500 + index * 1000,
                "candle_acc_trade_volume": 2 + index,
            }
            for index in range(5, -1, -1)
        ]

    def _fetcher(self, *, symbol: str, session_id: str, timeout_seconds: float) -> dict[str, object]:
        self.assertEqual(symbol, "KRW-BTC")
        self.assertEqual(session_id, "mvp1_upbit_paper_launcher")
        self.assertGreater(timeout_seconds, 0)
        return build_upbit_public_candle_data_from_rest_payload(
            payload=self._payload(),
            session_id=session_id,
        )

    def test_mocked_public_rest_sample_passes_as_paper_only_evidence(self):
        report = build_upbit_public_rest_sample_report(
            sample_id="mock-public-rest-pass",
            session_id="mvp1_upbit_paper_launcher",
            fetcher=self._fetcher,
        )
        result = validate_upbit_public_rest_sample_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["sample_status"], "PASS")
        self.assertEqual(report["evidence_role"], "PAPER_INPUT_QUALITY_SAMPLE_ONLY_NOT_LIVE_READY")
        self.assertGreaterEqual(report["canonical_event_count"], 5)
        self.assertFalse(report["credential_load_attempted"])
        self.assertFalse(report["authorization_header_present"])
        self.assertFalse(report["order_endpoint_called"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_network_exception_is_operator_visible_blocked_evidence(self):
        def failing_fetcher(*, symbol: str, session_id: str, timeout_seconds: float) -> dict[str, object]:
            raise TimeoutError("synthetic public endpoint timeout")

        report = build_upbit_public_rest_sample_report(
            sample_id="mock-public-rest-timeout",
            session_id="mvp1_upbit_paper_launcher",
            fetcher=failing_fetcher,
        )
        result = validate_upbit_public_rest_sample_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DATA_UNAVAILABLE")
        self.assertEqual(report["collection_status"], "NOT_RUN")
        self.assertTrue(report["blockers"])
        self.assertFalse(report["live_order_allowed"])

    def test_no_network_mode_is_safe_blocked_and_never_live_ready(self):
        report = build_upbit_public_rest_sample_report(
            sample_id="public-rest-not-attempted",
            session_id="mvp1_upbit_paper_launcher",
            attempt_network=False,
        )
        result = validate_upbit_public_rest_sample_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "DATA_UNAVAILABLE")
        self.assertFalse(report["network_call_attempted"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])

    def test_auth_header_marker_blocks_even_when_payload_is_public_shaped(self):
        def auth_fetcher(*, symbol: str, session_id: str, timeout_seconds: float) -> dict[str, object]:
            data = build_upbit_public_candle_data_from_rest_payload(
                payload=self._payload(),
                session_id=session_id,
            )
            data["authorization_header_present"] = True
            return data

        report = build_upbit_public_rest_sample_report(
            sample_id="mock-public-rest-auth-header",
            session_id="mvp1_upbit_paper_launcher",
            fetcher=auth_fetcher,
        )
        result = validate_upbit_public_rest_sample_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(report["live_order_allowed"])

    def test_live_flag_mutation_is_blocked(self):
        report = build_upbit_public_rest_sample_report(
            sample_id="mock-public-rest-live-mutation",
            session_id="mvp1_upbit_paper_launcher",
            fetcher=self._fetcher,
        )
        report["live_order_allowed"] = True
        report["sample_hash"] = upbit_public_rest_sample_hash(report)
        result = validate_upbit_public_rest_sample_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_writer_persists_sample_report_without_live_permission(self):
        report = build_upbit_public_rest_sample_report(
            sample_id="mock-public-rest-writer",
            session_id="mvp1_upbit_paper_launcher",
            fetcher=self._fetcher,
        )
        with TemporaryDirectory() as tmp:
            path = write_upbit_public_rest_sample_report(root=Path(tmp), report=report)
            self.assertTrue(path.exists())
            self.assertIn("paper", path.as_posix())
            self.assertFalse(report["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
