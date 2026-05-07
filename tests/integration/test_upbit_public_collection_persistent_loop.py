import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.adapters.upbit.market_data import (
    build_upbit_public_krw_symbol_discovery_report_from_payload,
    build_upbit_public_candle_data_from_rest_payload,
    build_upbit_public_candle_fixture,
    build_upbit_public_ticker_snapshot_from_rest_payload,
    validate_upbit_public_candle_data,
)
from trader1.core.sizing.position_sizing import sizing_decision_hash
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    build_upbit_paper_runtime_recovery_guard_report,
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
    upbit_paper_runtime_recovery_guard_hash,
    validate_upbit_paper_persistent_loop_report,
    validate_upbit_paper_runtime_recovery_guard_report,
)
from trader1.runtime.paper.upbit_paper_runtime import (
    build_upbit_paper_runtime_cycle_report,
    upbit_paper_runtime_cycle_hash,
)
from trader1.runtime.paper.upbit_public_collector import (
    build_upbit_public_market_data_collection_report,
    recover_jsonl_records,
    upbit_public_market_data_collection_hash,
    validate_upbit_public_market_data_collection_report,
    validate_upbit_public_market_data_collection_writer_report,
    validate_upbit_public_market_data_latest_pointer,
    write_upbit_public_market_data_collection_artifacts,
)
from trader1.runtime.portfolio.paper_portfolio import build_paper_portfolio_snapshot_from_fill
from trader1.validation.mvp0_validators import run_validators


class UpbitPublicCollectionPersistentLoopTest(unittest.TestCase):
    def _hash_payload(self, payload: dict[str, object]) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest().upper()

    def _upbit_rest_payload(self) -> list[dict[str, object]]:
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

    def test_public_collection_canonicalizes_fixture_without_private_or_live_behavior(self):
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-positive",
            session_id="mvp1_upbit_paper_launcher",
        )
        result = validate_upbit_public_market_data_collection_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["canonical_event_count"], report["raw_sample_count"])
        self.assertGreaterEqual(report["canonical_event_count"], 5)
        self.assertEqual(len(report["public_market_data_hash"]), 64)
        self.assertFalse(report["credential_load_attempted"])
        self.assertFalse(report["private_endpoint_called"])
        self.assertFalse(report["order_endpoint_called"])
        self.assertFalse(report["live_order_allowed"])

    def test_public_collection_blocks_payload_mutation_after_data_hash_binding(self):
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-payload-mismatch",
            session_id="mvp1_upbit_paper_launcher",
        )
        report["public_market_data"]["candles"][0]["close"] = "1234567"
        report["collection_hash"] = upbit_public_market_data_collection_hash(report)

        result = validate_upbit_public_market_data_collection_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_public_rest_payload_canonicalizes_without_credentials_or_private_endpoint(self):
        data = build_upbit_public_candle_data_from_rest_payload(
            payload=self._upbit_rest_payload(),
            session_id="mvp1_upbit_paper_launcher",
        )
        data_status, data_blocker, _ = validate_upbit_public_candle_data(
            data,
            symbol="KRW-BTC",
            session_id="mvp1_upbit_paper_launcher",
        )
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-public-rest-read-only",
            session_id="mvp1_upbit_paper_launcher",
            market_data=data,
        )
        result = validate_upbit_public_market_data_collection_report(report)

        self.assertEqual(data_status, "PASS")
        self.assertIsNone(data_blocker)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["data_source"], "PUBLIC_REST_READ_ONLY")
        self.assertEqual(report["canonical_event_count"], 6)
        self.assertFalse(report["credential_load_attempted"])
        self.assertFalse(report["private_endpoint_called"])
        self.assertFalse(report["order_endpoint_called"])
        self.assertFalse(report["live_order_allowed"])

    def test_public_rest_payload_blocks_authorization_header_or_private_endpoint(self):
        data = build_upbit_public_candle_data_from_rest_payload(
            payload=self._upbit_rest_payload(),
            session_id="mvp1_upbit_paper_launcher",
        )
        data["authorization_header_present"] = True
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-public-rest-auth-header",
            session_id="mvp1_upbit_paper_launcher",
            market_data=data,
        )
        result = validate_upbit_public_market_data_collection_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_public_rest_payload_duplicate_timestamp_requires_reconcile(self):
        payload = self._upbit_rest_payload()
        payload[1]["candle_date_time_utc"] = payload[0]["candle_date_time_utc"]
        data = build_upbit_public_candle_data_from_rest_payload(
            payload=payload,
            session_id="mvp1_upbit_paper_launcher",
        )
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-public-rest-duplicate-timestamp",
            session_id="mvp1_upbit_paper_launcher",
            market_data=data,
        )
        result = validate_upbit_public_market_data_collection_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_public_rest_payload_out_of_order_timestamp_requires_reconcile(self):
        payload = self._upbit_rest_payload()
        data = build_upbit_public_candle_data_from_rest_payload(
            payload=payload,
            session_id="mvp1_upbit_paper_launcher",
        )
        data["candles"][3]["timestamp"] = "2026-04-30T08:59:00Z"
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-public-rest-out-of-order-timestamp",
            session_id="mvp1_upbit_paper_launcher",
            market_data=data,
        )
        result = validate_upbit_public_market_data_collection_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_public_collection_blocks_private_field_mixing(self):
        data = build_upbit_public_candle_fixture(session_id="mvp1_upbit_paper_launcher")
        data["private_account_fields_present"] = True
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-private-mix",
            session_id="mvp1_upbit_paper_launcher",
            market_data=data,
        )
        result = validate_upbit_public_market_data_collection_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_public_collection_writer_recovers_partial_jsonl_without_live_permission(self):
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-writer",
            session_id="mvp1_upbit_paper_launcher",
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = write_upbit_public_market_data_collection_artifacts(root=root, report=report)
            self.assertEqual(writer["writer_status"], "PASS")
            self.assertEqual(validate_upbit_public_market_data_collection_writer_report(writer, source_report=report).status, "PASS")
            self.assertEqual(writer["public_market_data_hash"], report["public_market_data_hash"])
            latest_pointer = json.loads((root / writer["artifact_paths"][3]).read_text(encoding="utf-8"))
            self.assertEqual(validate_upbit_public_market_data_latest_pointer(latest_pointer, source_report=report).status, "PASS")
            self.assertEqual(latest_pointer["exchange"], "UPBIT")
            self.assertEqual(latest_pointer["market_type"], "KRW_SPOT")
            self.assertEqual(latest_pointer["mode"], "PAPER")
            self.assertEqual(latest_pointer["session_id"], report["session_id"])
            self.assertEqual(latest_pointer["public_market_data_hash"], report["public_market_data_hash"])
            canonical_path = root / writer["artifact_paths"][1]
            with canonical_path.open("a", encoding="utf-8", newline="") as handle:
                handle.write('{"partial":')
            records, quarantine_path = recover_jsonl_records(canonical_path)
            self.assertEqual(len(records), report["canonical_event_count"])
            self.assertIsNotNone(quarantine_path)
            self.assertFalse(writer["live_order_allowed"])

    def test_latest_pointer_hash_mismatch_fails_closed(self):
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-pointer-hash-mismatch",
            session_id="mvp1_upbit_paper_launcher",
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = write_upbit_public_market_data_collection_artifacts(root=root, report=report)
            latest_pointer = json.loads((root / writer["artifact_paths"][3]).read_text(encoding="utf-8"))
            latest_pointer["public_market_data_hash"] = "0" * 64

            result = validate_upbit_public_market_data_latest_pointer(latest_pointer, source_report=report)

            self.assertEqual(result.status, "FAIL")
            self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_collection_writer_live_flag_mutation_is_blocked(self):
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-writer-live-flag-mutation",
            session_id="mvp1_upbit_paper_launcher",
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = write_upbit_public_market_data_collection_artifacts(root=root, report=report)
            writer["live_order_allowed"] = True

            result = validate_upbit_public_market_data_collection_writer_report(writer, source_report=report)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_bounded_paper_loop_writes_latest_cycle_and_remains_live_blocked(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop",
                requested_cycle_count=2,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            self.assertEqual(result.status, "PASS")
            self.assertEqual(loop["completed_cycle_count"], 2)
            self.assertTrue(loop["actual_paper_runtime_executed"])
            self.assertEqual(loop["recovery_guard_status"], "PASS")
            self.assertTrue(loop["paper_runtime_resume_allowed"])
            self.assertFalse(loop["partial_write_recovery_required"])
            self.assertEqual(loop["paper_ledger_rollup_status"], "PASS")
            self.assertIsNone(loop["paper_ledger_rollup_primary_blocker_code"])
            self.assertTrue((root / loop["paper_ledger_rollup_path"]).exists())
            self.assertEqual(loop["runtime_evidence_role"], "BOUNDED_PAPER_LOOP_NOT_LONG_RUN_EVIDENCE")
            self.assertFalse(loop["long_run_evidence_eligible"])
            self.assertEqual(loop["long_run_blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
            self.assertFalse(loop["live_order_allowed"])
            canonical_loop_path = (
                root
                / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_persistent_loop_report.json"
            )
            self.assertTrue(canonical_loop_path.exists())
            canonical_loop = json.loads(canonical_loop_path.read_text(encoding="utf-8"))
            self.assertEqual(canonical_loop["loop_hash"], loop["loop_hash"])
            self.assertEqual(validate_upbit_paper_persistent_loop_report(canonical_loop).status, "PASS")
            self.assertFalse(canonical_loop["live_order_allowed"])
            self.assertFalse(canonical_loop["long_run_evidence_eligible"])
            guard_path = root / loop["runtime_recovery_guard_path"]
            guard = json.loads(guard_path.read_text(encoding="utf-8"))
            self.assertEqual(validate_upbit_paper_runtime_recovery_guard_report(guard).status, "PASS")
            self.assertEqual(guard["runtime_evidence_role"], "PAPER_RECOVERY_GUARD_ONLY_NOT_LONG_RUN_EVIDENCE")
            self.assertFalse(guard["long_run_evidence_eligible"])
            self.assertEqual(guard["long_run_blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
            latest_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            self.assertEqual(latest["runtime_input_role"], "MULTI_SYMBOL_PUBLIC_MARKET_DATA_COLLECTION")
            self.assertGreaterEqual(len(latest["symbol_universe"]), 10)
            self.assertIn("KRW-BTC", latest["symbol_universe"])
            self.assertIn("KRW-ETH", latest["symbol_universe"])
            self.assertIn("KRW-XRP", latest["symbol_universe"])
            self.assertIn(latest["selected_symbol"], latest["symbol_universe"])
            self.assertFalse(latest["live_order_allowed"])
            self.assertEqual(loop["symbol_universe_source"], "STATIC_FALLBACK_CONFIGURED_KRW_UNIVERSE")
            self.assertEqual(loop["symbol_universe_discovery_status"], "SKIPPED")
            self.assertFalse(loop["public_symbol_discovery_attempted"])
            self.assertEqual(loop["symbol_universe_evaluated_count"], len(loop["symbol_universe"]))
            for cycle_result in loop["cycle_results"]:
                self.assertEqual(cycle_result["runtime_input_role"], "MULTI_SYMBOL_PUBLIC_MARKET_DATA_COLLECTION")
                self.assertEqual(cycle_result["symbol_universe"], latest["symbol_universe"])
                self.assertEqual(cycle_result["symbol_universe_source"], "STATIC_FALLBACK_CONFIGURED_KRW_UNIVERSE")
                self.assertEqual(cycle_result["symbol_universe_evaluated_count"], len(cycle_result["symbol_universe"]))
                self.assertIn(cycle_result["selected_symbol"], cycle_result["symbol_universe"])
                self.assertEqual(len(cycle_result["source_collection_report_hash"]), 64)
                self.assertEqual(len(cycle_result["source_public_market_data_hash"]), 64)
                self.assertEqual(cycle_result["source_public_market_data_hash"], cycle_result["runtime_public_market_data_hash"])
                self.assertGreaterEqual(cycle_result["canonical_event_count"], 5)
                self.assertEqual(len(cycle_result["feature_snapshot_hash"]), 64)
                self.assertEqual(cycle_result["strategy_regime_cost_linkage"]["source_runtime_cycle_id"], cycle_result["cycle_id"])
                self.assertEqual(
                    cycle_result["strategy_regime_cost_linkage"]["runtime_public_market_data_hash"],
                    cycle_result["runtime_public_market_data_hash"],
                )
                self.assertEqual(
                    cycle_result["strategy_regime_cost_linkage"]["selected_candidate_id"],
                    cycle_result["selected_candidate_id"],
                )
                self.assertFalse(cycle_result["strategy_regime_cost_linkage"]["live_order_allowed"])
            ledger_artifacts = [
                artifact_path
                for cycle_result in loop["cycle_results"]
                for artifact_path in cycle_result["artifact_paths"]
                if artifact_path.endswith(".paper_ledger_events.jsonl")
            ]
            self.assertEqual(len(ledger_artifacts), 1)
            ledger_head_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/latest_paper_ledger_head.json"
            ledger_head = json.loads(ledger_head_path.read_text(encoding="utf-8"))
            self.assertEqual(ledger_head["schema_id"], "trader1.paper_ledger_head.v1")
            self.assertEqual(ledger_head["ledger_head_hash"], latest["paper_ledger_head_hash"])
            self.assertFalse(ledger_head["live_order_allowed"])
            self.assertEqual(guard["ledger_jsonl_checked_count"], 1)
            self.assertEqual(guard["corrupted_ledger_jsonl_quarantined_count"], 0)
            self.assertEqual(guard["ledger_jsonl_invalid_count"], 0)
            rollup = json.loads((root / loop["paper_ledger_rollup_path"]).read_text(encoding="utf-8"))
            self.assertEqual(rollup["ledger_jsonl_count"], 1)
            self.assertEqual(rollup["filled_order_count"], 1)
            self.assertEqual(rollup["portfolio_snapshot"]["source"], "PAPER_LEDGER_ROLLUP")
            self.assertEqual(rollup["portfolio_snapshot"]["source_runtime_cycle_id"], "bounded-paper-loop-cycle-1")
            self.assertEqual(rollup["portfolio_snapshot"]["source_paper_ledger_head_hash"], rollup["latest_ledger_head_hash"])
            self.assertFalse(rollup["live_order_allowed"])

    def test_bounded_paper_loop_can_select_non_btc_from_multi_symbol_universe(self):
        weak_btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp1_upbit_paper_launcher",
            profile="WEAK_RANGE",
        )
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp1_upbit_paper_launcher",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-multi-symbol-select",
                requested_cycle_count=1,
                market_data_universe_sequence=[[weak_btc, strong_eth]],
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            latest_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.status, "PASS")
        self.assertEqual(loop["cycle_results"][0]["selected_symbol"], "KRW-ETH")
        self.assertEqual(latest["selected_symbol"], "KRW-ETH")
        self.assertEqual(latest["paper_fill"]["symbol"], "KRW-ETH")
        self.assertEqual(latest["paper_portfolio_snapshot"]["positions"][0]["symbol"], "KRW-ETH")
        self.assertFalse(latest["live_order_allowed"])

    def test_persistent_loop_applies_preliminary_robustness_feedback_to_rotate_candidate(self):
        repeated_wlfi = build_upbit_public_candle_fixture(
            symbol="KRW-WLFI",
            session_id="quality-feedback-session",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(repeated_wlfi["candles"], start=1):
            candle["volume"] = str(10 + index * 3)
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="quality-feedback-session",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            diagnostic_dir = (
                root
                / "system/runtime/upbit/krw_spot/paper/quality-feedback-session/profitability"
            )
            diagnostic_dir.mkdir(parents=True)
            diagnostic = {
                "schema_id": "trader1.overfit_diagnostic_report.v1",
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "session_id": "quality-feedback-session",
                "candidate_id": "KRW-WLFI-pullback-trend-long",
                "symbol": "KRW-WLFI",
                "overfit_status": "HIGH",
                "preliminary_sample_count": 21,
                "preliminary_robustness_status": "UNFAVORABLE_BLOCKED_BY_EVIDENCE",
                "preliminary_primary_blocker_code": "PRELIMINARY_OOS_BELOW_THRESHOLD",
                "preliminary_oos_status": "FAIL",
                "preliminary_walk_forward_status": "FAIL",
                "preliminary_bootstrap_status": "FAIL",
                "preliminary_ranking_stability_status": "FAIL",
                "preliminary_in_sample_net_ev_after_cost_bps": -38.5,
                "preliminary_oos_net_ev_after_cost_bps": -26.6,
                "preliminary_bootstrap_confidence_lower_bps": -42.5,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
            diagnostic["diagnostic_hash"] = self._hash_payload(diagnostic)
            (diagnostic_dir / "overfit_diagnostic_report.json").write_text(
                json.dumps(diagnostic, sort_keys=True),
                encoding="utf-8",
            )

            loop = run_upbit_paper_persistent_loop(
                root=root,
                session_id="quality-feedback-session",
                loop_id="bounded-paper-loop-quality-feedback",
                symbol="KRW-WLFI",
                requested_cycle_count=1,
                market_data_universe_sequence=[[repeated_wlfi, strong_eth]],
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            latest_path = (
                root
                / "system/runtime/upbit/krw_spot/paper/quality-feedback-session/upbit_paper_runtime_cycle_report.json"
            )
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(loop["cycle_results"][0]["runtime_quality_feedback_count"], 1)
        self.assertEqual(
            loop["cycle_results"][0]["runtime_quality_feedback_candidate_ids"],
            ["KRW-WLFI-pullback-trend-long"],
        )
        self.assertEqual(latest["selected_symbol"], "KRW-ETH")
        wlfi_pullback = next(
            candidate
            for candidate in latest["strategy_candidates"]
            if candidate["candidate_id"] == "KRW-WLFI-pullback-trend-long"
        )
        self.assertEqual(wlfi_pullback["recent_failure_feedback_kind"], "PRELIMINARY_ROBUSTNESS_FAIL")
        self.assertEqual(wlfi_pullback["no_trade_reason"], "COOLDOWN")
        self.assertFalse(latest["live_order_allowed"])

    def test_persistent_loop_applies_recent_negative_exit_cooldown_from_prior_paper_cycle(self):
        entry_market = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp1_upbit_paper_launcher",
            profile="UPTREND_PULLBACK",
        )
        exit_market = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp1_upbit_paper_launcher",
            profile="DOWNTREND",
        )
        retry_market = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp1_upbit_paper_launcher",
            profile="UPTREND_PULLBACK",
        )
        for data in (entry_market, retry_market):
            for index, candle in enumerate(data["candles"], start=1):
                candle["volume"] = str(10 + index * 3)

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-recent-negative-exit-feedback",
                requested_cycle_count=3,
                symbol_universe=["KRW-BTC"],
                market_data_universe_sequence=[[entry_market], [exit_market], [retry_market]],
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            latest_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.status, "PASS")
        self.assertEqual(loop["completed_cycle_count"], 3)
        self.assertEqual(loop["cycle_results"][0]["final_decision"], "ENTER_LONG")
        self.assertEqual(loop["cycle_results"][1]["final_decision"], "EXIT_POSITION")
        self.assertEqual(loop["cycle_results"][2]["final_decision"], "NO_TRADE")
        self.assertEqual(loop["cycle_results"][2]["selected_candidate_recent_failure_cooldown_status"], "ACTIVE")
        self.assertGreater(loop["cycle_results"][2]["selected_candidate_recent_failure_cooldown_cycles_remaining"], 0)
        self.assertEqual(loop["cycle_results"][2]["selected_candidate_recent_failure_reason_code"], "REGIME_REVERSAL")
        self.assertEqual(latest["selected_candidate"]["recent_failure_cooldown_status"], "ACTIVE")
        self.assertEqual(latest["selected_candidate"]["recent_failure_reason_code"], "REGIME_REVERSAL")
        self.assertEqual(latest["selected_candidate"]["no_trade_reason"], "COOLDOWN")
        self.assertIn("COOLDOWN", latest["no_trade_reasons"])
        self.assertLess(float(latest["selected_candidate"]["recent_failure_realized_pnl_delta"]), 0)
        self.assertIsNone(latest["paper_fill"])
        self.assertFalse(loop["live_order_allowed"])
        self.assertFalse(latest["live_order_allowed"])

    def test_bounded_paper_loop_discovers_all_krw_markets_then_evaluates_ranked_public_candidates(self):
        def fake_market_symbols_fetcher(**_: object) -> dict[str, object]:
            return build_upbit_public_krw_symbol_discovery_report_from_payload(
                session_id="mvp1_upbit_paper_launcher",
                payload=[
                    {"market": "KRW-BTC"},
                    {"market": "KRW-ETH"},
                    {"market": "KRW-XRP"},
                    {"market": "KRW-SOL"},
                    {"market": "KRW-ADA"},
                    {"market": "BTC-USDT"},
                ],
            )

        def fake_ticker_fetcher(*, symbols: list[str], session_id: str, **_: object) -> dict[str, object]:
            payload = [
                {"market": "KRW-BTC", "trade_price": 100000000, "acc_trade_price_24h": 900000000, "signed_change_rate": "0.01", "acc_trade_volume_24h": 12},
                {"market": "KRW-ETH", "trade_price": 6000000, "acc_trade_price_24h": 1200000000, "signed_change_rate": "0.02", "acc_trade_volume_24h": 200},
                {"market": "KRW-XRP", "trade_price": 800, "acc_trade_price_24h": 70000000, "signed_change_rate": "0.01", "acc_trade_volume_24h": 90000},
                {"market": "KRW-SOL", "trade_price": 220000, "acc_trade_price_24h": 8000000000, "signed_change_rate": "0.04", "acc_trade_volume_24h": 50000},
                {"market": "KRW-ADA", "trade_price": 900, "acc_trade_price_24h": 30000000, "signed_change_rate": "0.03", "acc_trade_volume_24h": 20000},
            ]
            return build_upbit_public_ticker_snapshot_from_rest_payload(
                payload=payload,
                requested_symbols=symbols,
                session_id=session_id,
            )

        def fake_candle_fetcher(*, symbol: str, session_id: str, **_: object) -> dict[str, object]:
            profile = "UPTREND_PULLBACK" if symbol == "KRW-SOL" else "WEAK_RANGE"
            data = build_upbit_public_candle_fixture(symbol=symbol, session_id=session_id, profile=profile)
            if symbol == "KRW-SOL":
                for index, candle in enumerate(data["candles"], start=1):
                    candle["volume"] = str(10 + index * 4)
            return data

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-public-discovery",
                requested_cycle_count=1,
                attempt_public_symbol_discovery=True,
                attempt_network_market_data=True,
                max_symbol_evaluation_count=3,
                market_symbols_fetcher=fake_market_symbols_fetcher,
                public_ticker_fetcher=fake_ticker_fetcher,
                public_candle_fetcher=fake_candle_fetcher,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            latest_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.status, "PASS")
        self.assertEqual(loop["symbol_universe_source"], "PUBLIC_KRW_MARKET_DISCOVERY_TICKER_RANKED")
        self.assertEqual(loop["symbol_universe_discovery_status"], "PASS")
        self.assertTrue(loop["public_symbol_discovery_attempted"])
        self.assertEqual(loop["symbol_universe_total_count"], 5)
        self.assertEqual(loop["symbol_universe_evaluated_count"], 3)
        self.assertEqual(loop["symbol_universe"][0], "KRW-SOL")
        self.assertIn("KRW-ETH", loop["symbol_universe"])
        self.assertEqual(loop["public_ticker_eligible_symbol_count"], 4)
        self.assertEqual(latest["selected_symbol"], "KRW-SOL")
        self.assertEqual(loop["cycle_results"][0]["symbol_universe_source"], "PUBLIC_KRW_MARKET_DISCOVERY_TICKER_RANKED")
        self.assertEqual(loop["cycle_results"][0]["symbol_universe_evaluated_count"], 3)
        self.assertFalse(loop["live_order_allowed"])
        self.assertFalse(latest["live_order_allowed"])

    def test_bounded_paper_loop_skips_ranked_symbols_without_enough_public_candles(self):
        def fake_market_symbols_fetcher(**_: object) -> dict[str, object]:
            return build_upbit_public_krw_symbol_discovery_report_from_payload(
                session_id="mvp1_upbit_paper_launcher",
                payload=[
                    {"market": "KRW-NEW"},
                    {"market": "KRW-SOL"},
                    {"market": "KRW-ETH"},
                ],
            )

        def fake_ticker_fetcher(*, symbols: list[str], session_id: str, **_: object) -> dict[str, object]:
            return build_upbit_public_ticker_snapshot_from_rest_payload(
                payload=[
                    {"market": "KRW-NEW", "trade_price": 1000, "acc_trade_price_24h": 9000000000, "signed_change_rate": "0.09", "acc_trade_volume_24h": 900000},
                    {"market": "KRW-SOL", "trade_price": 220000, "acc_trade_price_24h": 8000000000, "signed_change_rate": "0.04", "acc_trade_volume_24h": 50000},
                    {"market": "KRW-ETH", "trade_price": 6000000, "acc_trade_price_24h": 1200000000, "signed_change_rate": "0.02", "acc_trade_volume_24h": 200},
                ],
                requested_symbols=symbols,
                session_id=session_id,
            )

        def fake_candle_fetcher(*, symbol: str, session_id: str, **_: object) -> dict[str, object]:
            profile = "UPTREND_PULLBACK" if symbol == "KRW-SOL" else "WEAK_RANGE"
            data = build_upbit_public_candle_fixture(symbol=symbol, session_id=session_id, profile=profile)
            if symbol == "KRW-NEW":
                data["candles"] = data["candles"][:2]
            if symbol == "KRW-SOL":
                for index, candle in enumerate(data["candles"], start=1):
                    candle["volume"] = str(10 + index * 4)
            return data

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-public-discovery-skip-short-candle-symbol",
                requested_cycle_count=1,
                attempt_public_symbol_discovery=True,
                attempt_network_market_data=True,
                max_symbol_evaluation_count=3,
                market_symbols_fetcher=fake_market_symbols_fetcher,
                public_ticker_fetcher=fake_ticker_fetcher,
                public_candle_fetcher=fake_candle_fetcher,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            latest_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

        cycle_result = loop["cycle_results"][0]
        self.assertEqual(result.status, "PASS")
        self.assertEqual(loop["symbol_universe"][0], "KRW-NEW")
        self.assertIn("KRW-NEW", cycle_result["collection_hashes_by_symbol"])
        self.assertNotIn("KRW-NEW", cycle_result["symbol_universe"])
        self.assertEqual(cycle_result["symbol_universe_evaluated_count"], 2)
        self.assertEqual(latest["selected_symbol"], "KRW-SOL")
        self.assertEqual(latest["paper_fill"]["symbol"], "KRW-SOL")
        self.assertFalse(loop["live_order_allowed"])
        self.assertFalse(latest["live_order_allowed"])

    def test_bounded_paper_loop_allows_clean_preflight_resume(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-clean-preflight-a",
                requested_cycle_count=1,
            )
            second = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-clean-preflight-b",
                requested_cycle_count=1,
            )

            self.assertEqual(validate_upbit_paper_persistent_loop_report(first).status, "PASS")
            self.assertEqual(validate_upbit_paper_persistent_loop_report(second).status, "PASS")
            self.assertTrue(second["preflight_existing_runtime_state_detected"])
            self.assertEqual(second["preflight_recovery_guard_status"], "PASS")
            self.assertTrue(second["preflight_paper_runtime_resume_allowed"])
            self.assertTrue(second["current_evidence_write_allowed"])
            self.assertEqual(second["completed_cycle_count"], 1)
            self.assertFalse(second["live_order_allowed"])

    def test_bounded_paper_loop_refreshes_stale_cash_guard_manifest_before_sizing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-stale-cash-manifest-a",
                requested_cycle_count=1,
            )
            self.assertEqual(validate_upbit_paper_persistent_loop_report(first).status, "PASS")

            manifest_path = (
                root
                / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/paper_ledger_input_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps({"schema_id": "stale-test-manifest"}), encoding="utf-8")

            second = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-stale-cash-manifest-b",
                requested_cycle_count=1,
            )
            latest_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

            self.assertEqual(validate_upbit_paper_persistent_loop_report(second).status, "PASS")
            self.assertEqual(second["completed_cycle_count"], 1)
            self.assertEqual(latest["sizing_decision"]["inputs"]["paper_cash_guard_source"], "PAPER_LEDGER_ROLLUP")
            self.assertNotEqual(latest["sizing_decision"]["inputs"]["paper_cash_available"], "-1")
            self.assertFalse(second["live_order_allowed"])

    def test_bounded_paper_loop_allows_paper_only_resume_from_legacy_quant_policy_cycle(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy_cycle = build_upbit_paper_runtime_cycle_report(
                cycle_id="bounded-paper-loop-legacy-quant-policy-cycle",
                session_id="mvp1_upbit_paper_launcher",
            )
            del legacy_cycle["summary"]["quantitative_policy_summary"]
            legacy_cycle["cycle_hash"] = upbit_paper_runtime_cycle_hash(legacy_cycle)
            latest_path = (
                root
                / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            )
            latest_path.parent.mkdir(parents=True, exist_ok=True)
            latest_path.write_text(json.dumps(legacy_cycle, indent=2), encoding="utf-8")

            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-legacy-quant-policy-resume",
                requested_cycle_count=1,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            guard = json.loads((root / loop["preflight_runtime_recovery_guard_path"]).read_text(encoding="utf-8"))
            guard_result = validate_upbit_paper_runtime_recovery_guard_report(guard)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(guard_result.status, "PASS")
            self.assertEqual(loop["preflight_recovery_guard_status"], "PASS")
            self.assertTrue(loop["current_evidence_write_allowed"])
            self.assertEqual(loop["completed_cycle_count"], 1)
            self.assertEqual(guard["latest_cycle_contract_mode"], "LEGACY_RECHECK_WITHOUT_QUANTITATIVE_POLICY_SUMMARY")
            self.assertTrue(guard["latest_cycle_schema_upgrade_required"])
            self.assertFalse(loop["live_order_allowed"])
            self.assertFalse(loop["can_live_trade"])
            self.assertFalse(loop["scale_up_allowed"])

    def test_bounded_paper_loop_allows_paper_only_resume_from_legacy_sizing_cap_cycle(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy_cycle = build_upbit_paper_runtime_cycle_report(
                cycle_id="bounded-paper-loop-legacy-sizing-cap-cycle",
                session_id="mvp1_upbit_paper_launcher",
            )
            del legacy_cycle["sizing_decision"]["caps"]["exposure_cap"]
            legacy_cycle["sizing_decision"]["sizing_decision_hash"] = sizing_decision_hash(legacy_cycle["sizing_decision"])
            legacy_cycle["cycle_hash"] = upbit_paper_runtime_cycle_hash(legacy_cycle)
            latest_path = (
                root
                / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            )
            latest_path.parent.mkdir(parents=True, exist_ok=True)
            latest_path.write_text(json.dumps(legacy_cycle, indent=2), encoding="utf-8")

            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-legacy-sizing-cap-resume",
                requested_cycle_count=1,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            guard = json.loads((root / loop["preflight_runtime_recovery_guard_path"]).read_text(encoding="utf-8"))
            guard_result = validate_upbit_paper_runtime_recovery_guard_report(guard)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(guard_result.status, "PASS")
            self.assertEqual(loop["preflight_recovery_guard_status"], "PASS")
            self.assertTrue(loop["current_evidence_write_allowed"])
            self.assertEqual(loop["completed_cycle_count"], 1)
            self.assertEqual(guard["latest_cycle_contract_mode"], "LEGACY_RECHECK_WITHOUT_CURRENT_SIZING_EXPOSURE_CAP")
            self.assertTrue(guard["latest_cycle_schema_upgrade_required"])
            self.assertFalse(loop["live_order_allowed"])
            self.assertFalse(loop["can_live_trade"])
            self.assertFalse(loop["scale_up_allowed"])

    def test_bounded_paper_loop_regenerates_legacy_symbol_scorecard_cycle(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy_cycle = build_upbit_paper_runtime_cycle_report(
                cycle_id="bounded-paper-loop-legacy-symbol-scorecard-cycle",
                session_id="mvp1_upbit_paper_launcher",
            )
            for field in (
                "symbol_selection_policy",
                "symbol_evidence_scorecards",
                "symbol_evidence_scorecard_count",
                "selected_symbol_evidence_scorecard",
            ):
                del legacy_cycle[field]
            legacy_cycle["cycle_hash"] = upbit_paper_runtime_cycle_hash(legacy_cycle)
            latest_path = (
                root
                / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            )
            latest_path.parent.mkdir(parents=True, exist_ok=True)
            latest_path.write_text(json.dumps(legacy_cycle, indent=2), encoding="utf-8")

            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-legacy-symbol-scorecard-resume",
                requested_cycle_count=1,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            guard = json.loads((root / loop["preflight_runtime_recovery_guard_path"]).read_text(encoding="utf-8"))
            guard_result = validate_upbit_paper_runtime_recovery_guard_report(guard)
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

            self.assertEqual(result.status, "PASS")
            self.assertEqual(guard_result.status, "PASS")
            self.assertEqual(loop["preflight_recovery_guard_status"], "PASS")
            self.assertTrue(loop["current_evidence_write_allowed"])
            self.assertEqual(loop["completed_cycle_count"], 1)
            self.assertEqual(guard["latest_cycle_contract_mode"], "LEGACY_RECHECK_WITHOUT_SYMBOL_EVIDENCE_SCORECARD")
            self.assertTrue(guard["latest_cycle_schema_upgrade_required"])
            self.assertGreaterEqual(latest["symbol_evidence_scorecard_count"], 1)
            self.assertIsInstance(latest["selected_symbol_evidence_scorecard"], dict)
            self.assertFalse(loop["live_order_allowed"])
            self.assertFalse(loop["can_live_trade"])
            self.assertFalse(loop["scale_up_allowed"])
            self.assertFalse(latest["live_order_allowed"])

    def test_bounded_paper_loop_regenerates_legacy_symbol_selection_policy_formula_cycle(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy_cycle = build_upbit_paper_runtime_cycle_report(
                cycle_id="bounded-paper-loop-legacy-symbol-policy-formula-cycle",
                session_id="mvp1_upbit_paper_launcher",
            )
            legacy_cycle["symbol_selection_policy"]["candidate_formula"] = "0.45*symbol_score+0.35*net_ev_score+0.20*signal_strength"
            legacy_cycle["cycle_hash"] = upbit_paper_runtime_cycle_hash(legacy_cycle)
            latest_path = (
                root
                / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            )
            latest_path.parent.mkdir(parents=True, exist_ok=True)
            latest_path.write_text(json.dumps(legacy_cycle, indent=2), encoding="utf-8")

            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-legacy-symbol-policy-formula-resume",
                requested_cycle_count=1,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            guard = json.loads((root / loop["preflight_runtime_recovery_guard_path"]).read_text(encoding="utf-8"))
            guard_result = validate_upbit_paper_runtime_recovery_guard_report(guard)
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

            self.assertEqual(result.status, "PASS")
            self.assertEqual(guard_result.status, "PASS")
            self.assertEqual(loop["preflight_recovery_guard_status"], "PASS")
            self.assertTrue(loop["current_evidence_write_allowed"])
            self.assertEqual(loop["completed_cycle_count"], 1)
            self.assertEqual(guard["latest_cycle_contract_mode"], "LEGACY_RECHECK_WITHOUT_SYMBOL_SELECTION_POLICY_FORMULA")
            self.assertTrue(guard["latest_cycle_schema_upgrade_required"])
            self.assertIn("trend_or_breakout_or_mean_reversion_confirmation", latest["symbol_selection_policy"]["candidate_formula"])
            self.assertFalse(loop["live_order_allowed"])
            self.assertFalse(loop["can_live_trade"])
            self.assertFalse(loop["scale_up_allowed"])
            self.assertFalse(latest["live_order_allowed"])

    def test_bounded_paper_loop_regenerates_legacy_trend_exhaustion_projection_cycle(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy_cycle = build_upbit_paper_runtime_cycle_report(
                cycle_id="bounded-paper-loop-legacy-trend-exhaustion-projection-cycle",
                session_id="mvp1_upbit_paper_launcher",
            )
            legacy_cycle["symbol_selection_policy"]["candidate_formula"] = "0.45*symbol_score+0.35*net_ev_score+0.20*signal_strength"
            for field in ("trend_exhaustion_status", "trend_exhaustion_score", "trend_exhaustion_formula"):
                legacy_cycle["feature_snapshot"].pop(field, None)
                for feature_snapshot in legacy_cycle["feature_snapshots_by_symbol"].values():
                    feature_snapshot.pop(field, None)
                for scorecard in legacy_cycle["symbol_evidence_scorecards"]:
                    scorecard.pop(field, None)
                legacy_cycle["selected_symbol_evidence_scorecard"].pop(field, None)
            legacy_cycle["feature_snapshot_hash"] = self._hash_payload(legacy_cycle["feature_snapshot"])
            legacy_cycle["strategy_regime_cost_linkage"]["feature_snapshot_hash"] = legacy_cycle["feature_snapshot_hash"]
            legacy_cycle["cycle_hash"] = upbit_paper_runtime_cycle_hash(legacy_cycle)
            latest_path = (
                root
                / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            )
            latest_path.parent.mkdir(parents=True, exist_ok=True)
            latest_path.write_text(json.dumps(legacy_cycle, indent=2), encoding="utf-8")

            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-legacy-trend-exhaustion-projection-resume",
                requested_cycle_count=1,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            guard = json.loads((root / loop["preflight_runtime_recovery_guard_path"]).read_text(encoding="utf-8"))
            guard_result = validate_upbit_paper_runtime_recovery_guard_report(guard)
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

            self.assertEqual(result.status, "PASS")
            self.assertEqual(guard_result.status, "PASS")
            self.assertEqual(loop["preflight_recovery_guard_status"], "PASS")
            self.assertTrue(loop["current_evidence_write_allowed"])
            self.assertEqual(loop["completed_cycle_count"], 1)
            self.assertEqual(
                guard["latest_cycle_contract_mode"],
                (
                    "LEGACY_RECHECK_WITHOUT_SYMBOL_SELECTION_POLICY_FORMULA"
                    "_AND_FEATURE_SNAPSHOT_PROJECTION_AND_SYMBOL_EVIDENCE_SCORECARD_PROJECTION"
                ),
            )
            self.assertTrue(guard["latest_cycle_schema_upgrade_required"])
            self.assertIn("trend_exhaustion_status", latest["feature_snapshot"])
            self.assertIn("trend_exhaustion_status", latest["selected_symbol_evidence_scorecard"])
            self.assertFalse(loop["live_order_allowed"])
            self.assertFalse(loop["can_live_trade"])
            self.assertFalse(loop["scale_up_allowed"])
            self.assertFalse(latest["live_order_allowed"])

    def test_bounded_paper_loop_blocks_partial_symbol_scorecard_schema_tamper(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            tampered_cycle = build_upbit_paper_runtime_cycle_report(
                cycle_id="bounded-paper-loop-partial-symbol-scorecard-tamper-cycle",
                session_id="mvp1_upbit_paper_launcher",
            )
            del tampered_cycle["selected_symbol_evidence_scorecard"]
            tampered_cycle["cycle_hash"] = upbit_paper_runtime_cycle_hash(tampered_cycle)
            latest_path = (
                root
                / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            )
            latest_path.parent.mkdir(parents=True, exist_ok=True)
            latest_path.write_text(json.dumps(tampered_cycle, indent=2), encoding="utf-8")

            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-partial-symbol-scorecard-tamper",
                requested_cycle_count=1,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            guard = json.loads((root / loop["preflight_runtime_recovery_guard_path"]).read_text(encoding="utf-8"))
            guard_result = validate_upbit_paper_runtime_recovery_guard_report(guard)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(guard_result.status, "BLOCKED")
            self.assertEqual(loop["preflight_recovery_guard_status"], "BLOCKED")
            self.assertFalse(loop["current_evidence_write_allowed"])
            self.assertEqual(loop["completed_cycle_count"], 0)
            self.assertEqual(guard["latest_cycle_contract_mode"], "CURRENT")
            self.assertFalse(guard["latest_cycle_schema_upgrade_required"])
            self.assertEqual(guard["primary_blocker_code"], "SCHEMA_IDENTITY_MISMATCH")
            self.assertFalse(loop["live_order_allowed"])
            self.assertFalse(loop["can_live_trade"])
            self.assertFalse(loop["scale_up_allowed"])

    def test_bounded_paper_loop_preflight_blocks_orphan_tmp_before_cycle_write(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            tmp_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/.orphan.tmp"
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_text("partial", encoding="utf-8")

            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-preflight-orphan-tmp",
                requested_cycle_count=1,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)

            self.assertEqual(result.status, "BLOCKED")
            self.assertTrue(loop["preflight_existing_runtime_state_detected"])
            self.assertEqual(loop["preflight_recovery_guard_status"], "BLOCKED")
            self.assertEqual(loop["preflight_recovery_guard_primary_blocker_code"], "PARTIAL_WRITE_RECOVERY_REQUIRED")
            self.assertFalse(loop["preflight_paper_runtime_resume_allowed"])
            self.assertFalse(loop["current_evidence_write_allowed"])
            self.assertEqual(loop["completed_cycle_count"], 0)
            self.assertEqual(loop["cycle_results"], [])
            latest_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            self.assertFalse(latest_path.exists())
            cycle_dir = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/cycles"
            self.assertFalse(any(cycle_dir.glob("*.runtime_cycle.json")) if cycle_dir.exists() else False)
            self.assertFalse(loop["live_order_allowed"])

    def test_bounded_paper_loop_preflight_blocks_corrupt_ledger_before_new_cycle_write(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-preflight-corrupt-ledger-a",
                requested_cycle_count=1,
            )
            ledger_path = None
            for artifact_path in first["cycle_results"][0]["artifact_paths"]:
                if artifact_path.endswith(".paper_ledger_events.jsonl"):
                    ledger_path = root / artifact_path
                    break
            self.assertIsNotNone(ledger_path)
            with ledger_path.open("a", encoding="utf-8", newline="") as handle:
                handle.write('{"partial":')

            second = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-preflight-corrupt-ledger-b",
                requested_cycle_count=1,
            )
            result = validate_upbit_paper_persistent_loop_report(second)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(second["preflight_recovery_guard_status"], "BLOCKED")
            self.assertEqual(second["preflight_recovery_guard_primary_blocker_code"], "PARTIAL_WRITE_RECOVERY_REQUIRED")
            self.assertFalse(second["current_evidence_write_allowed"])
            self.assertEqual(second["completed_cycle_count"], 0)
            new_cycle_path = (
                root
                / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/cycles"
                / "bounded-paper-loop-preflight-corrupt-ledger-b-cycle-1.runtime_cycle.json"
            )
            self.assertFalse(new_cycle_path.exists())
            self.assertFalse(second["live_order_allowed"])

    def test_recovery_guard_blocks_orphan_tmp_file_before_resume(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-orphan-tmp",
                requested_cycle_count=1,
            )
            tmp_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/.orphan.tmp"
            tmp_path.write_text("partial", encoding="utf-8")

            guard = build_upbit_paper_runtime_recovery_guard_report(
                root=root,
                loop_id="bounded-paper-loop-orphan-tmp",
            )
            result = validate_upbit_paper_runtime_recovery_guard_report(guard)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")
            self.assertFalse(guard["paper_runtime_resume_allowed"])

    def test_recovery_guard_quarantines_partial_canonical_jsonl(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-corrupt-jsonl",
                requested_cycle_count=1,
            )
            canonical_path = None
            for artifact_path in loop["cycle_results"][0]["artifact_paths"]:
                if artifact_path.endswith(".canonical_events.jsonl"):
                    canonical_path = root / artifact_path
                    break
            self.assertIsNotNone(canonical_path)
            with canonical_path.open("a", encoding="utf-8", newline="") as handle:
                handle.write('{"partial":')

            guard = build_upbit_paper_runtime_recovery_guard_report(
                root=root,
                loop_id="bounded-paper-loop-corrupt-jsonl",
            )
            result = validate_upbit_paper_runtime_recovery_guard_report(guard)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")
            self.assertEqual(guard["corrupted_jsonl_quarantined_count"], 1)
            self.assertFalse(guard["paper_runtime_resume_allowed"])

    def test_recovery_guard_quarantines_partial_paper_ledger_jsonl(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-corrupt-ledger-jsonl",
                requested_cycle_count=1,
            )
            ledger_path = None
            for artifact_path in loop["cycle_results"][0]["artifact_paths"]:
                if artifact_path.endswith(".paper_ledger_events.jsonl"):
                    ledger_path = root / artifact_path
                    break
            self.assertIsNotNone(ledger_path)
            with ledger_path.open("a", encoding="utf-8", newline="") as handle:
                handle.write('{"partial":')

            guard = build_upbit_paper_runtime_recovery_guard_report(
                root=root,
                loop_id="bounded-paper-loop-corrupt-ledger-jsonl",
            )
            result = validate_upbit_paper_runtime_recovery_guard_report(guard)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")
            self.assertEqual(guard["corrupted_ledger_jsonl_quarantined_count"], 1)
            self.assertFalse(guard["paper_runtime_resume_allowed"])

    def test_recovery_guard_blocks_live_permission_mutation(self):
        with TemporaryDirectory() as tmp:
            guard = build_upbit_paper_runtime_recovery_guard_report(
                root=Path(tmp),
                loop_id="bounded-paper-loop-missing-latest",
            )
        guard["live_order_allowed"] = True
        guard["guard_hash"] = upbit_paper_runtime_recovery_guard_hash(guard)

        result = validate_upbit_paper_runtime_recovery_guard_report(guard)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_recovery_guard_blocks_false_long_run_eligibility(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-false-long-run",
                requested_cycle_count=1,
            )
            guard = build_upbit_paper_runtime_recovery_guard_report(
                root=root,
                loop_id="bounded-paper-loop-false-long-run",
            )
        guard["long_run_evidence_eligible"] = True
        guard["guard_hash"] = upbit_paper_runtime_recovery_guard_hash(guard)

        result = validate_upbit_paper_runtime_recovery_guard_report(guard)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_persistent_loop_requires_visible_long_run_evidence_boundary(self):
        with TemporaryDirectory() as tmp:
            loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="bounded-paper-loop-missing-long-run-boundary",
                requested_cycle_count=1,
            )
        loop["runtime_evidence_role"] = "PAPER_RUNTIME_EVIDENCE"
        loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)

        result = validate_upbit_paper_persistent_loop_report(loop)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")

    def test_persistent_loop_hash_tamper_fails(self):
        with TemporaryDirectory() as tmp:
            loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="bounded-paper-loop-tamper",
                requested_cycle_count=1,
            )
            loop["completed_cycle_count"] = 0
            loop["actual_paper_runtime_executed"] = False
            loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)
            result = validate_upbit_paper_persistent_loop_report(loop)
            self.assertEqual(result.status, "FAIL")
            self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_persistent_loop_blocks_false_runtime_execution_flag(self):
        with TemporaryDirectory() as tmp:
            loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="bounded-paper-loop-false-runtime-flag",
                requested_cycle_count=1,
            )
            loop["actual_paper_runtime_executed"] = False
            loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)

            result = validate_upbit_paper_persistent_loop_report(loop)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")

    def test_persistent_loop_blocks_static_fixture_cycle_summary_role(self):
        with TemporaryDirectory() as tmp:
            loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="bounded-paper-loop-static-summary-role",
                requested_cycle_count=1,
            )
            loop["cycle_results"][0]["runtime_input_role"] = "STATIC_FIXTURE"
            loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)

            result = validate_upbit_paper_persistent_loop_report(loop)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")

    def test_persistent_loop_blocks_missing_cycle_summary_canonical_depth(self):
        with TemporaryDirectory() as tmp:
            loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="bounded-paper-loop-missing-summary-depth",
                requested_cycle_count=1,
            )
            loop["cycle_results"][0]["canonical_event_count"] = 0
            loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)

            result = validate_upbit_paper_persistent_loop_report(loop)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "MEASUREMENT_MISSING")

    def test_persistent_loop_blocks_summary_source_runtime_hash_mismatch(self):
        with TemporaryDirectory() as tmp:
            loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="bounded-paper-loop-summary-hash-mismatch",
                requested_cycle_count=1,
            )
            loop["cycle_results"][0]["source_public_market_data_hash"] = "A" * 64
            loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)

            result = validate_upbit_paper_persistent_loop_report(loop)

            self.assertEqual(result.status, "FAIL")
            self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_persistent_loop_blocks_strategy_regime_cost_linkage_live_flag(self):
        with TemporaryDirectory() as tmp:
            loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="bounded-paper-loop-summary-linkage-live-flag",
                requested_cycle_count=1,
            )
            loop["cycle_results"][0]["strategy_regime_cost_linkage"]["live_order_allowed"] = True
            loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)

            result = validate_upbit_paper_persistent_loop_report(loop)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_persistent_loop_blocks_duplicate_cycle_identity(self):
        with TemporaryDirectory() as tmp:
            loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="bounded-paper-loop-duplicate-cycle",
                requested_cycle_count=2,
            )
            loop["cycle_results"][1] = dict(loop["cycle_results"][0])
            loop["cycle_results"][1]["cycle_index"] = 2
            loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)

            result = validate_upbit_paper_persistent_loop_report(loop)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_persistent_loop_blocks_cross_namespace_artifact_path(self):
        with TemporaryDirectory() as tmp:
            loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="bounded-paper-loop-path-escape",
                requested_cycle_count=1,
            )
            loop["cycle_results"][0]["artifact_paths"].append(
                "system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/unsafe.json"
            )
            loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)

            result = validate_upbit_paper_persistent_loop_report(loop)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_new_validators_pass_current_contract(self):
        results = run_validators(
            [
                "upbit_public_market_data_collection_validator",
                "upbit_paper_persistent_loop_validator",
            ]
        )
        self.assertEqual([result["status"] for result in results], ["PASS", "PASS"])


if __name__ == "__main__":
    unittest.main()
