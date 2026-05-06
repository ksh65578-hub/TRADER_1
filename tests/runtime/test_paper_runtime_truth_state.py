import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.adapters.upbit.market_data import build_upbit_public_candle_data_from_rest_payload
from trader1.runtime.boot.safe_launcher import launcher_dashboard_paths, load_json
from trader1.runtime.health.heartbeat import build_heartbeat
from trader1.runtime.paper.paper_runtime_truth_state import (
    MONITOR_ALIVE_ENGINE_NOT_PROVEN_STATUS,
    PAPER_RUNTIME_ACTIVE_STATUS,
    build_paper_runtime_truth_state_report,
    paper_runtime_truth_state_hash,
    validate_paper_runtime_truth_state_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
)
from trader1.runtime.paper.upbit_public_rest_continuity import build_upbit_public_rest_continuity_report
from trader1.runtime.paper.upbit_public_rest_continuity_history import build_upbit_public_rest_continuity_history_report
from trader1.runtime.portfolio.paper_current_truth_refresh import build_paper_current_truth_refresh_report


class PaperRuntimeTruthStateTest(unittest.TestCase):
    def _heartbeat(self) -> dict:
        return build_heartbeat(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="mvp1_upbit_paper_launcher",
            config_hash="A" * 64,
            registry_hash="B" * 64,
            schema_bundle_hash="C" * 64,
            source_tree_hash="D" * 64,
        )

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

    def _continuity_history(self) -> dict:
        attempts = [
            build_upbit_public_rest_continuity_report(
                continuity_id="truth-state-continuity-1",
                session_id="mvp1_upbit_paper_launcher",
                fetcher=self._sequence_fetcher([0, 1]),
            ),
            build_upbit_public_rest_continuity_report(
                continuity_id="truth-state-continuity-2",
                session_id="mvp1_upbit_paper_launcher",
                fetcher=self._sequence_fetcher([1, 2]),
            ),
        ]
        return build_upbit_public_rest_continuity_history_report(
            history_id="truth-state-continuity-history",
            session_id="mvp1_upbit_paper_launcher",
            continuity_attempts=attempts,
        )

    def test_fresh_monitor_without_loop_reports_engine_not_proven(self):
        report = build_paper_runtime_truth_state_report(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="mvp1_upbit_paper_launcher",
            heartbeat=self._heartbeat(),
            upbit_paper_persistent_loop_report=None,
            upbit_public_rest_continuity_history=None,
            paper_ledger_rollup_report=None,
            paper_current_truth_refresh_report=None,
        )
        result = validate_paper_runtime_truth_state_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(report["runtime_truth_status"], MONITOR_ALIVE_ENGINE_NOT_PROVEN_STATUS)
        self.assertTrue(report["monitor_alive"])
        self.assertFalse(report["paper_loop_advancing"])
        self.assertIn("PAPER engine not proven", report["state_summary"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_blocked_heartbeat_preserves_resource_blocker_code(self):
        heartbeat = build_heartbeat(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="mvp1_upbit_paper_launcher",
            config_hash="A" * 64,
            registry_hash="B" * 64,
            schema_bundle_hash="C" * 64,
            source_tree_hash="D" * 64,
            component_overrides={
                "disk": {
                    "status": "FAIL",
                    "message": "Runtime artifact byte pressure exceeded fail threshold",
                }
            },
        )

        report = build_paper_runtime_truth_state_report(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="mvp1_upbit_paper_launcher",
            heartbeat=heartbeat,
            upbit_paper_persistent_loop_report=None,
            upbit_public_rest_continuity_history=None,
            paper_ledger_rollup_report=None,
            paper_current_truth_refresh_report=None,
        )

        self.assertEqual(report["primary_blocker_code"], "RESOURCE_LIMIT")
        self.assertFalse(report["monitor_alive"])
        self.assertIn("RESOURCE_LIMIT", {blocker["code"] for blocker in report["blockers"]})
        self.assertFalse(report["live_order_allowed"])

    def test_runtime_truth_active_requires_loop_market_ledger_and_current_refresh(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="truth-state-loop",
                session_id="mvp1_upbit_paper_launcher",
                requested_cycle_count=1,
            )
            ledger_rollup = load_json(launcher_dashboard_paths({"exchange": "UPBIT", "market_type": "KRW_SPOT", "mode": "PAPER", "session_id": "mvp1_upbit_paper_launcher"}, root)["paper_ledger_rollup_report"])
            heartbeat = self._heartbeat()
            current_refresh = build_paper_current_truth_refresh_report(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id="mvp1_upbit_paper_launcher",
                paper_portfolio_snapshot=ledger_rollup["portfolio_snapshot"],
                heartbeat=heartbeat,
                startup_probe=None,
            )
            report = build_paper_runtime_truth_state_report(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id="mvp1_upbit_paper_launcher",
                heartbeat=heartbeat,
                upbit_paper_persistent_loop_report=loop,
                upbit_public_rest_continuity_history=self._continuity_history(),
                paper_ledger_rollup_report=ledger_rollup,
                paper_current_truth_refresh_report=current_refresh,
            )
            result = validate_paper_runtime_truth_state_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["runtime_truth_status"], PAPER_RUNTIME_ACTIVE_STATUS)
        self.assertEqual(report["dashboard_truth_status"], "FRESH_CURRENT_TRUTH")
        self.assertTrue(report["paper_loop_advancing"])
        self.assertTrue(report["market_data_advancing"])
        self.assertTrue(report["ledger_advancing"])
        self.assertTrue(report["current_evidence_refreshing"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_stale_valid_loop_does_not_prove_runtime_advancement(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="truth-state-stale-loop",
                session_id="mvp1_upbit_paper_launcher",
                requested_cycle_count=1,
            )
            ledger_rollup = load_json(launcher_dashboard_paths({"exchange": "UPBIT", "market_type": "KRW_SPOT", "mode": "PAPER", "session_id": "mvp1_upbit_paper_launcher"}, root)["paper_ledger_rollup_report"])
            heartbeat = self._heartbeat()
            current_refresh = build_paper_current_truth_refresh_report(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id="mvp1_upbit_paper_launcher",
                paper_portfolio_snapshot=ledger_rollup["portfolio_snapshot"],
                heartbeat=heartbeat,
                startup_probe=None,
            )
            continuity_history = self._continuity_history()
            now = datetime.now(timezone.utc).replace(microsecond=0)
            stale = now - timedelta(seconds=301)
            loop["generated_at_utc"] = stale.isoformat().replace("+00:00", "Z")
            loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)
            report = build_paper_runtime_truth_state_report(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id="mvp1_upbit_paper_launcher",
                heartbeat=heartbeat,
                upbit_paper_persistent_loop_report=loop,
                upbit_public_rest_continuity_history=continuity_history,
                paper_ledger_rollup_report=ledger_rollup,
                paper_current_truth_refresh_report=current_refresh,
                generated_at_utc=now.isoformat().replace("+00:00", "Z"),
            )
            result = validate_paper_runtime_truth_state_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(report["runtime_truth_status"], MONITOR_ALIVE_ENGINE_NOT_PROVEN_STATUS)
        self.assertEqual(report["primary_blocker_code"], "LATENCY_TTL_EXPIRED")
        self.assertFalse(report["paper_loop_advancing"])
        self.assertIn("stale", report["blockers"][0]["message"])
        self.assertFalse(report["live_order_allowed"])

    def test_live_flag_mutation_is_blocked(self):
        report = build_paper_runtime_truth_state_report(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="mvp1_upbit_paper_launcher",
            heartbeat=self._heartbeat(),
            upbit_paper_persistent_loop_report=None,
            upbit_public_rest_continuity_history=None,
            paper_ledger_rollup_report=None,
            paper_current_truth_refresh_report=None,
        )
        report["live_order_allowed"] = True
        report["truth_state_hash"] = paper_runtime_truth_state_hash(report)
        result = validate_paper_runtime_truth_state_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
