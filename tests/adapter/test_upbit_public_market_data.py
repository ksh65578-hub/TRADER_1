import json
import unittest
from urllib.parse import parse_qs, urlparse

from trader1.adapters.upbit.market_data import (
    fetch_upbit_public_candle_history_read_only,
    validate_upbit_public_candle_data,
)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def _payload(symbol: str, minutes_desc: list[int]) -> list[dict[str, object]]:
    return [
        {
            "market": symbol,
            "candle_date_time_utc": f"2026-04-30T09:{minute:02d}:00",
            "opening_price": 1000000 + minute * 100,
            "high_price": 1002500 + minute * 100,
            "low_price": 998000 + minute * 100,
            "trade_price": 1000500 + minute * 100,
            "candle_acc_trade_volume": 2 + minute,
        }
        for minute in minutes_desc
    ]


class UpbitPublicMarketDataTest(unittest.TestCase):
    def test_public_candle_history_retries_with_smaller_page_without_private_flags(self):
        calls: list[dict[str, object]] = []

        def opener(request, timeout: float):
            query = parse_qs(urlparse(request.full_url).query)
            calls.append({"count": int(query["count"][0]), "url": request.full_url, "timeout": timeout})
            if len(calls) == 1:
                raise TimeoutError("transient public read timeout")
            if len(calls) == 2:
                return _FakeResponse(_payload("KRW-BTC", [9, 8, 7, 6, 5]))
            return _FakeResponse(_payload("KRW-BTC", [4, 3, 2, 1, 0]))

        data = fetch_upbit_public_candle_history_read_only(
            symbol="KRW-BTC",
            session_id="mvp1_upbit_paper_launcher",
            target_count=10,
            page_size=10,
            timeout_seconds=1.0,
            retry_attempts=2,
            retry_backoff_seconds=0,
            urlopen_fn=opener,
        )
        status, blocker, _ = validate_upbit_public_candle_data(
            data,
            symbol="KRW-BTC",
            session_id="mvp1_upbit_paper_launcher",
        )

        self.assertEqual(status, "PASS")
        self.assertIsNone(blocker)
        self.assertEqual([call["count"] for call in calls], [10, 5, 5])
        self.assertEqual(len(data["candles"]), 10)
        self.assertEqual(data["candles"][0]["timestamp"], "2026-04-30T09:00:00Z")
        self.assertEqual(data["candles"][-1]["timestamp"], "2026-04-30T09:09:00Z")
        self.assertFalse(data["credential_load_attempted"])
        self.assertFalse(data["authorization_header_present"])
        self.assertFalse(data["private_endpoint_called"])
        self.assertFalse(data["order_endpoint_called"])

    def test_public_candle_history_still_raises_after_bounded_retries(self):
        calls = {"count": 0}

        def opener(request, timeout: float):
            del request, timeout
            calls["count"] += 1
            raise TimeoutError("public read unavailable")

        with self.assertRaises(TimeoutError):
            fetch_upbit_public_candle_history_read_only(
                symbol="KRW-BTC",
                session_id="mvp1_upbit_paper_launcher",
                target_count=10,
                page_size=10,
                timeout_seconds=1.0,
                retry_attempts=3,
                retry_backoff_seconds=0,
                urlopen_fn=opener,
            )

        self.assertEqual(calls["count"], 3)


if __name__ == "__main__":
    unittest.main()
