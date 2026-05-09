import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.run_upbit_paper_candidate_scorecard import (
    _build_and_write_alternative_public_replay,
    _select_scorecard_runtime_sample,
    build_current_upbit_paper_candidate_scorecard,
)
from trader1.adapters.upbit.market_data import (
    build_upbit_krw_market_symbols_from_rest_payload,
    build_upbit_public_candle_fixture,
    build_upbit_public_krw_symbol_discovery_report_from_payload,
    build_upbit_public_ticker_snapshot_from_rest_payload,
)
from trader1.research.profitability.candidate_scorecard import (
    PERFORMANCE_PASS,
    candidate_generation_report_from_upbit_paper_runtime_cycle,
    candidate_scorecard_from_upbit_paper_runtime_cycle,
    performance_source_evidence_id,
    robustness_source_evidence_id,
    safe_candidate_scorecard_filename,
    stable_hash,
)
from trader1.research.profitability.overfit_diagnostic import (
    overfit_diagnostic_from_upbit_paper_runtime,
    overfit_diagnostic_report_hash,
)
from trader1.research.replay.replay_runner import (
    build_public_replay_robustness_report,
    public_replay_robustness_report_hash,
    write_public_replay_robustness_report,
)
from trader1.research.shadow.shadow_runner import build_paper_shadow_evidence_accumulation_report
from trader1.runtime.portfolio.paper_portfolio import build_paper_portfolio_snapshot_from_fill
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
from trader1.validation.mvp0_validators import (
    _candidate_scorecard_net_ev_errors,
    _convergence_objective_profile_errors,
    _exploration_exploitation_policy_errors,
    _failure_analysis_errors,
    _optimizer_memory_state_errors,
    _overfit_diagnostic_errors,
    _profit_convergence_cycle_errors,
    _strategy_performance_memory_errors,
)


def _load_written(root: Path, result: dict, key: str) -> dict:
    value = json.loads((root / result[key]).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{key} did not point to a JSON object")
    return value


def _candidate_snapshot_path(root: Path, result: dict, scorecard: dict) -> Path:
    filename = f"{safe_candidate_scorecard_filename(scorecard['candidate_id'])}.candidate_scorecard.json"
    return (root / result["candidate_scorecard_path"]).parent / "candidate_scorecards" / filename


def _run_short_paper(root: Path) -> None:
    run_upbit_paper_persistent_loop(
        root=root,
        loop_id="current-scorecard-short-runtime",
        requested_cycle_count=2,
    )


def _public_replay_fixture(*, symbol: str, session_id: str, count: int) -> dict:
    market_data = build_upbit_public_candle_fixture(symbol=symbol, session_id=session_id)
    start = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    candles = []
    for index in range(count):
        price = 980000 + index * 900 + (index % 5) * 250
        candles.append(
            {
                "timestamp": (start + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"),
                "open": str(price - 700),
                "high": str(price + 1800),
                "low": str(price - 1400),
                "close": str(price),
                "volume": str(5 + (index % 7)),
            }
        )
    market_data["source"] = "PUBLIC_REST_READ_ONLY"
    market_data["profile"] = "TEST_PUBLIC_REPLAY_HISTORY"
    market_data["candles"] = candles
    market_data["raw_payload_private_fields_present"] = False
    market_data["public_endpoint_host"] = "api.upbit.com"
    market_data["public_endpoint_path"] = "/v1/candles/minutes/1"
    market_data["credential_load_attempted"] = False
    market_data["authorization_header_present"] = False
    market_data["private_endpoint_called"] = False
    market_data["order_endpoint_called"] = False
    return market_data


def _paper_shadow_evidence_path(root: Path) -> Path:
    return (
        root
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / "mvp1_upbit_paper_launcher"
        / "paper_shadow_evidence_accumulation_report.json"
    )


class CurrentCandidateScorecardToolTest(unittest.TestCase):
    def test_scorecard_runtime_selection_prefers_active_evidence_scope_over_latest_no_trade(self):
        entry_exit_sample = {
            "source_runtime_cycle_path": (
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/"
                "paper_runtime/cycles/active-exit.runtime_cycle.json"
            ),
            "source_runtime_cycle_hash": "A" * 64,
        }
        latest_no_trade_sample = {
            "source_runtime_cycle_path": (
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/"
                "paper_runtime/cycles/latest-no-trade.runtime_cycle.json"
            ),
            "source_runtime_cycle_hash": "B" * 64,
        }
        history = {
            "active_candidate_scope": {
                "candidate_id": "KRW-AXL-pullback-trend-long",
                "latest_cycle_id": "active-exit",
                "latest_runtime_cycle_hash": "A" * 64,
                "latest_candidate_decision": "PAPER_ENTRY_REVIEW",
                "latest_final_decision": "EXIT_POSITION",
                "entry_reason_count": 1,
                "exit_reason_count": 2,
            },
            "samples": [entry_exit_sample, latest_no_trade_sample],
        }

        selected, selection_source = _select_scorecard_runtime_sample(history)

        self.assertIs(selected, entry_exit_sample)
        self.assertEqual(selection_source, "ACTIVE_CANDIDATE_SCOPE")

    def test_scorecard_runtime_selection_uses_latest_when_active_scope_has_no_entry_or_exit_evidence(self):
        first_sample = {
            "source_runtime_cycle_path": (
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/"
                "paper_runtime/cycles/older-no-trade.runtime_cycle.json"
            ),
            "source_runtime_cycle_hash": "A" * 64,
        }
        latest_sample = {
            "source_runtime_cycle_path": (
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/"
                "paper_runtime/cycles/latest-no-trade.runtime_cycle.json"
            ),
            "source_runtime_cycle_hash": "B" * 64,
        }
        history = {
            "active_candidate_scope": {
                "candidate_id": "KRW-WIF-vwap-mean-reversion",
                "latest_cycle_id": "older-no-trade",
                "latest_runtime_cycle_hash": "A" * 64,
                "latest_candidate_decision": "NO_TRADE",
                "latest_final_decision": "NO_TRADE",
                "entry_reason_count": 0,
                "exit_reason_count": 0,
            },
            "samples": [first_sample, latest_sample],
        }

        selected, selection_source = _select_scorecard_runtime_sample(history)

        self.assertIs(selected, latest_sample)
        self.assertEqual(selection_source, "LATEST_RUNTIME_SAMPLE")

    def test_empty_runtime_history_blocks_without_live_permission(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
            )

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["blocker_code"], "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertFalse(result["live_order_ready"])
        self.assertFalse(result["live_order_allowed"])
        self.assertFalse(result["can_live_trade"])
        self.assertFalse(result["scale_up_allowed"])

    def test_short_runtime_writes_blocked_scorecard_and_overfit_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_short_paper(root)

            result = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
            )
            scorecard = _load_written(root, result, "candidate_scorecard_path")
            diagnostic = _load_written(root, result, "overfit_diagnostic_path")
            history = _load_written(root, result, "runtime_sample_history_path")
            strategy_memory = _load_written(root, result, "strategy_performance_memory_path")
            objective_profile = _load_written(root, result, "convergence_objective_profile_path")
            exploration_policy = _load_written(root, result, "exploration_exploitation_policy_path")
            optimizer_memory = _load_written(root, result, "optimizer_memory_state_path")
            failure_analysis = _load_written(root, result, "failure_analysis_path")
            profit_cycle = _load_written(root, result, "profit_convergence_cycle_report_path")
            scoped_scorecard = json.loads(
                _candidate_snapshot_path(root, result, scorecard).read_text(encoding="utf-8")
            )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(_candidate_scorecard_net_ev_errors(scorecard), [])
        self.assertEqual(_candidate_scorecard_net_ev_errors(scoped_scorecard), [])
        self.assertEqual(scoped_scorecard["candidate_id"], scorecard["candidate_id"])
        self.assertFalse(scoped_scorecard["live_order_allowed"])
        self.assertEqual(_overfit_diagnostic_errors(diagnostic), [])
        self.assertEqual(history["accepted_cycle_sample_count"], 2)
        self.assertEqual(diagnostic["sample_count"], 0)
        self.assertEqual(diagnostic["preliminary_exact_candidate_sample_count"], 2)
        self.assertEqual(_strategy_performance_memory_errors(strategy_memory), [])
        self.assertEqual(_convergence_objective_profile_errors(objective_profile), [])
        self.assertEqual(_exploration_exploitation_policy_errors(exploration_policy), [])
        self.assertEqual(_optimizer_memory_state_errors(optimizer_memory), [])
        self.assertEqual(_failure_analysis_errors(failure_analysis), [])
        self.assertEqual(_profit_convergence_cycle_errors(profit_cycle), [])
        self.assertEqual(strategy_memory["performance_scope"], "PAPER_RUNTIME_SCORECARD_ONLY")
        self.assertEqual(objective_profile["objective_status"], "BLOCKED")
        self.assertEqual(exploration_policy["policy_status"], "BLOCKED")
        self.assertEqual(exploration_policy["transition_decision"], "BLOCK_TRANSITION")
        self.assertFalse(exploration_policy["exploitation_allowed_for_paper_ranking"])
        self.assertFalse(strategy_memory["paper_shadow_separated"])
        self.assertEqual(optimizer_memory["blocked_candidate_count"], 1)
        self.assertEqual(failure_analysis["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertEqual(profit_cycle["cycle_status"], "BLOCKED")
        self.assertEqual(profit_cycle["exploration_exploitation_policy_validator_status"], "PASS")
        self.assertEqual(profit_cycle["convergence_claim"], "BLOCKED")
        self.assertFalse(profit_cycle["candidate_ranking_allowed_for_paper"])
        self.assertNotIn("CONVERGENCE_OBJECTIVE_MISSING", result["profit_convergence_cycle_blocker_codes"])
        self.assertNotIn("EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED", result["profit_convergence_cycle_blocker_codes"])
        self.assertIn("MEASUREMENT_MISSING", result["profit_convergence_cycle_blocker_codes"])
        self.assertEqual(diagnostic["diagnostic_status"], "BLOCKED_FOR_ROBUSTNESS")
        self.assertFalse(diagnostic["robustness_eligible"])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertEqual(scorecard["oos_status"], diagnostic["oos_status"])
        self.assertEqual(scorecard["walk_forward_status"], diagnostic["walk_forward_status"])
        self.assertEqual(scorecard["bootstrap_status"], diagnostic["bootstrap_status"])
        self.assertEqual(scorecard["overfit_status"], diagnostic["overfit_status"])
        self.assertFalse(scorecard["live_order_ready"])
        self.assertFalse(scorecard["live_order_allowed"])
        self.assertFalse(scorecard["can_live_trade"])
        self.assertFalse(scorecard["scale_up_allowed"])
        self.assertGreaterEqual(scorecard["evaluated_symbol_count"], 1)
        self.assertGreaterEqual(scorecard["paper_entry_review_symbol_count"], 0)
        self.assertIn("top_symbol_evidence_scorecards", scorecard)
        self.assertIn("rotation_review_required", scorecard)
        self.assertIn("rotation_review_reason_code", scorecard)
        self.assertFalse(result["live_order_allowed"])
        self.assertFalse(strategy_memory["live_order_allowed"])
        self.assertFalse(exploration_policy["live_order_allowed"])
        self.assertFalse(optimizer_memory["live_order_allowed"])
        self.assertFalse(failure_analysis["live_order_allowed"])
        self.assertFalse(profit_cycle["live_order_allowed"])
        blocker_codes = {blocker["code"] for blocker in scorecard["blockers"]}
        self.assertTrue({"OOS_MISSING", "WALK_FORWARD_MISSING", "BOOTSTRAP_UNSTABLE", "OVERFIT_RISK_HIGH"}.issubset(blocker_codes))

    def test_public_replay_status_distinguishes_contract_pass_from_profitability_gate_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_short_paper(root)
            initial_result = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
            )
            initial_scorecard = _load_written(root, initial_result, "candidate_scorecard_path")
            replay_report = build_public_replay_robustness_report(
                candidate_scorecard=initial_scorecard,
                market_data=_public_replay_fixture(
                    symbol=initial_scorecard["symbol"],
                    session_id=initial_scorecard["session_id"],
                    count=360,
                ),
                replay_id="current-scorecard-public-replay-profitability-fail",
                max_replay_windows=360,
                min_required_sample_count=300,
            )
            for row in replay_report["sample_rows"]:
                if row["decision"] == "PAPER_ENTRY_REVIEW":
                    row["net_ev_after_cost_bps"] = -25.0
                    row["gross_expected_edge_bps"] = -25.0
                    row["total_execution_cost_bps"] = 0.0
                    row["opportunity_net_ev_after_cost_bps"] = -25.0
                    row["opportunity_gross_expected_edge_bps"] = -25.0
                    row["opportunity_total_execution_cost_bps"] = 0.0
            replay_report["report_hash"] = public_replay_robustness_report_hash(replay_report)
            write_public_replay_robustness_report(root=root, report=replay_report)

            result = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
            )
            scorecard = _load_written(root, result, "candidate_scorecard_path")
            diagnostic = _load_written(root, result, "overfit_diagnostic_path")

        blocker_codes = set(result["scorecard_blocker_codes"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["public_replay_robustness_contract_status"], "PASS")
        self.assertEqual(result["public_replay_robustness_replay_status"], "PASS")
        self.assertEqual(result["public_replay_robustness_status"], "BLOCKED_ROBUSTNESS_GATE")
        self.assertEqual(result["public_replay_robustness_blocker_code"], "SAMPLE_INSUFFICIENT")
        self.assertEqual(result["public_replay_robustness_oos_status"], "BLOCKED")
        self.assertEqual(result["public_replay_robustness_walk_forward_status"], "BLOCKED")
        self.assertEqual(result["public_replay_robustness_bootstrap_status"], "BLOCKED")
        self.assertEqual(result["public_replay_robustness_overfit_status"], "HIGH")
        self.assertEqual(result["public_replay_robustness_sample_count"], replay_report["sample_count"])
        self.assertTrue(result["public_replay_robustness_source_bound"])
        self.assertFalse(result["ranking_eligible"])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertFalse(diagnostic["robustness_eligible"])
        self.assertIn("SAMPLE_INSUFFICIENT", blocker_codes)
        self.assertIn("OOS_MISSING", blocker_codes)
        self.assertFalse(result["credential_load_attempted"])
        self.assertFalse(result["private_endpoint_called"])
        self.assertFalse(result["order_endpoint_called"])
        self.assertFalse(result["order_adapter_called"])
        self.assertFalse(result["live_key_loaded"])
        self.assertFalse(result["live_order_allowed"])

    def test_bounded_public_discovery_can_supply_non_live_alternative_candidate(self):
        def fake_market_symbols_fetcher(*, session_id: str, timeout_seconds: float):
            payload = [{"market": "KRW-ETH"}, {"market": "KRW-XRP"}]
            return build_upbit_public_krw_symbol_discovery_report_from_payload(
                payload=payload,
                session_id=session_id,
            )

        def fake_ticker_fetcher(*, symbols: list[str], session_id: str, timeout_seconds: float):
            requested = build_upbit_krw_market_symbols_from_rest_payload([{"market": symbol} for symbol in symbols])
            return build_upbit_public_ticker_snapshot_from_rest_payload(
                requested_symbols=requested,
                session_id=session_id,
                payload=[
                    {
                        "market": "KRW-ETH",
                        "trade_price": "1000000",
                        "acc_trade_price_24h": "9000000000",
                        "signed_change_rate": "0.035",
                        "acc_trade_volume_24h": "9000",
                    }
                ],
            )

        def fake_candle_fetcher(*, symbol: str, session_id: str, timeout_seconds: float):
            return build_upbit_public_candle_fixture(
                symbol=symbol,
                session_id=session_id,
                profile="UPTREND_PULLBACK",
            )

        def fake_replay_history_fetcher(
            *,
            symbol: str,
            session_id: str,
            target_count: int,
            page_size: int,
            timeout_seconds: float,
        ):
            return build_upbit_public_candle_fixture(
                symbol=symbol,
                session_id=session_id,
                profile="UPTREND_PULLBACK",
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_short_paper(root)

            result = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                attempt_public_discovery=True,
                candidate_discovery_symbol_limit=1,
                market_symbols_fetcher=fake_market_symbols_fetcher,
                public_ticker_fetcher=fake_ticker_fetcher,
                public_candle_fetcher=fake_candle_fetcher,
                public_replay_history_fetcher=fake_replay_history_fetcher,
                alternative_replay_max_windows=10,
                alternative_replay_min_required_sample_count=1,
            )
            generation_report = _load_written(root, result, "candidate_generation_report_path")
            discovery_runtime = _load_written(root, result, "candidate_discovery_runtime_cycle_path")
            alternative_replay = _load_written(root, result, "alternative_public_replay_report_path")
            alternative_review_scorecard = _load_written(root, result, "alternative_review_scorecard_path")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["candidate_discovery_status"], "PASS")
        self.assertIn("read-only public KRW", result["candidate_discovery_message"])
        self.assertEqual(result["candidate_discovery_symbol_count"], 1)
        self.assertGreaterEqual(result["candidate_discovery_ranked_symbol_count"], 1)
        self.assertGreaterEqual(result["candidate_discovery_eligible_symbol_count"], 1)
        self.assertFalse(result["candidate_discovery_adaptive_expansion_attempted"])
        self.assertEqual(result["candidate_discovery_initial_symbol_count"], 1)
        self.assertEqual(result["candidate_discovery_expanded_symbol_count"], 1)
        self.assertEqual(result["candidate_discovery_max_expanded_symbol_count"], 1)
        self.assertGreaterEqual(result["candidate_discovery_evaluated_candidate_count"], 1)
        self.assertGreaterEqual(result["candidate_discovery_paper_entry_review_candidate_count"], 1)
        self.assertEqual(
            result["candidate_discovery_blocked_candidate_count"],
            result["candidate_discovery_evaluated_candidate_count"]
            - result["candidate_discovery_paper_entry_review_candidate_count"],
        )
        family_counts = {
            item["code"]: item["count"]
            for item in result["candidate_discovery_strategy_family_candidate_counts"]
        }
        self.assertIn("PULLBACK_TREND_LONG", family_counts)
        self.assertEqual(generation_report["generation_status"], "ALTERNATIVE_PUBLIC_REPLAY_BLOCKED")
        self.assertEqual(generation_report["best_alternative_symbol"], "KRW-ETH")
        self.assertEqual(generation_report["best_alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(generation_report["primary_blocker_code"], "REPLAY_CLOSED_TRADES_MISSING")
        self.assertIn("REPLAY_CLOSED_TRADES_MISSING", {blocker["code"] for blocker in generation_report["blockers"]})
        self.assertIn("Run bounded public replay robustness", generation_report["next_action"])
        self.assertEqual(generation_report["alternative_candidate_count"], 1)
        best_item = next(
            item
            for item in generation_report["candidate_items"]
            if item["candidate_id"] == generation_report["best_alternative_candidate_id"]
        )
        self.assertEqual(best_item["candidate_source_role"], "BOUNDED_PUBLIC_DISCOVERY_RUNTIME")
        self.assertEqual(best_item["source_runtime_cycle_id"], discovery_runtime["cycle_id"])
        self.assertEqual(result["alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(result["alternative_public_replay_blocker_code"], "REPLAY_CLOSED_TRADES_MISSING")
        self.assertEqual(result["alternative_public_replay_closed_trade_maturity_status"], "UNTESTED")
        self.assertEqual(result["alternative_public_replay_contract_status"], "PASS")
        self.assertIsNone(result["alternative_public_replay_contract_blocker_code"])
        self.assertEqual(result["alternative_public_replay_candidate_id"], generation_report["best_alternative_candidate_id"])
        self.assertEqual(result["alternative_public_replay_symbol"], "KRW-ETH")
        self.assertGreaterEqual(result["alternative_public_replay_sample_count"], 1)
        self.assertEqual(alternative_replay["candidate_id"], generation_report["best_alternative_candidate_id"])
        self.assertEqual(result["alternative_review_scorecard_status"], "BLOCKED")
        self.assertEqual(result["alternative_review_scorecard_blocker_code"], "REPLAY_CLOSED_TRADES_MISSING")
        self.assertIsNotNone(result["alternative_review_scorecard_path"])
        self.assertFalse(result["alternative_review_scorecard_ranking_eligible"])
        self.assertFalse(alternative_review_scorecard["ranking_eligible"])
        self.assertEqual(alternative_review_scorecard["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertEqual(
            generation_report["best_alternative_public_replay_closed_trade_sample_count"],
            alternative_replay["replay_closed_trade_sample_count"],
        )
        self.assertEqual(
            result["alternative_review_replay_closed_trade_sample_count"],
            alternative_replay["replay_closed_trade_sample_count"],
        )
        self.assertFalse(alternative_replay["live_order_allowed"])
        self.assertEqual(result["candidate_generation_status"], "ALTERNATIVE_PUBLIC_REPLAY_BLOCKED")
        self.assertEqual(result["candidate_generation_primary_blocker_code"], "REPLAY_CLOSED_TRADES_MISSING")
        self.assertEqual(result["candidate_generation_best_alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(
            result["candidate_generation_best_alternative_public_replay_closed_trade_maturity_blocker_code"],
            "REPLAY_CLOSED_TRADES_MISSING",
        )
        self.assertFalse(generation_report["live_order_allowed"])
        self.assertFalse(result["credential_load_attempted"])
        self.assertFalse(result["private_endpoint_called"])
        self.assertFalse(result["order_endpoint_called"])
        self.assertFalse(result["order_adapter_called"])
        self.assertFalse(result["live_key_loaded"])
        self.assertFalse(result["live_order_allowed"])

    def test_alternative_public_replay_runs_for_same_runtime_best_alternative_without_discovery_runtime(self):
        weak_btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="WEAK_RANGE",
        )
        for candle in weak_btc["candles"]:
            candle["volume"] = "1"
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)
        focus_orca = build_upbit_public_candle_fixture(
            symbol="KRW-ORCA",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        orca_closes = ["980000", "988000", "1004000", "997000", "1009000", "1002050"]
        for index, candle in enumerate(focus_orca["candles"], start=1):
            price = int(orca_closes[index - 1])
            candle["open"] = str(price - 1200)
            candle["high"] = str(price + 2500)
            candle["low"] = str(price - 2500)
            candle["close"] = orca_closes[index - 1]
            candle["volume"] = str(1 + index * 0.1)
        mark_price = weak_btc["candles"][-1]["close"]
        current_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.005",
            fill_price=mark_price,
            mark_price=mark_price,
            fee_amount="2.5",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-current-scorecard-same-runtime-alt",
            source_paper_ledger_head_hash="D" * 64,
        )
        focus_candidate_id = "KRW-ORCA-pullback-trend-long"
        focus_parameter_hash = stable_hash(f"{focus_candidate_id}:PULLBACK_TREND_LONG:KRW-ORCA")
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="current-scorecard-same-runtime-alt",
            symbol="KRW-BTC",
            market_data_universe=[weak_btc, strong_eth, focus_orca],
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
            paper_scope_focus={
                "source": "TEST_ACTIVE_CANDIDATE_SCOPE",
                "candidate_id": focus_candidate_id,
                "symbol": "KRW-ORCA",
                "strategy_id": "trend_pullback",
                "parameter_hash": focus_parameter_hash,
                "sample_count": 1,
                "sample_deficit": 29,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
        )
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses={
                "oos_status": "FAIL",
                "walk_forward_status": "FAIL",
                "bootstrap_status": "FAIL",
                "overfit_status": "HIGH",
            },
            robustness_source_evidence_ids=[
                "public_replay_robustness:replay-current-scorecard-same-runtime-alt:" + "A" * 64,
                "public_market_data:KRW-BTC:" + "B" * 64,
            ],
        )

        generation_report = candidate_generation_report_from_upbit_paper_runtime_cycle(
            runtime,
            candidate_scorecard=scorecard,
        )

        def fake_replay_history_fetcher(
            *,
            symbol: str,
            session_id: str,
            target_count: int,
            page_size: int,
            timeout_seconds: float,
        ):
            del target_count, page_size, timeout_seconds
            return _public_replay_fixture(symbol=symbol, session_id=session_id, count=70)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = _build_and_write_alternative_public_replay(
                root=root,
                session_id=runtime["session_id"],
                candidate_generation_report=generation_report,
                history={"history_id": "direct-alt-replay-history", "history_hash": "H" * 64, "samples": []},
                runtime_cycle_report=runtime,
                candidate_discovery_runtime=None,
                target_count=70,
                page_size=200,
                timeout_seconds=1.0,
                max_replay_windows=10,
                min_required_sample_count=1,
                candidate_limit=5,
                public_replay_history_fetcher=fake_replay_history_fetcher,
            )
            alternative_replay = _load_written(root, context, "report_path")

        self.assertEqual(generation_report["generation_status"], "ALTERNATIVE_REVIEW_READY")
        self.assertEqual(context["status"], "BLOCKED")
        self.assertEqual(context["blocker_code"], "REPLAY_CLOSED_TRADES_MISSING")
        self.assertEqual(context["contract_status"], "PASS")
        self.assertEqual(context["candidate_id"], generation_report["best_alternative_candidate_id"])
        self.assertEqual(context["symbol"], "KRW-ETH")
        self.assertGreaterEqual(context["sample_count"], 1)
        self.assertEqual(alternative_replay["candidate_id"], generation_report["best_alternative_candidate_id"])
        self.assertFalse(context["credential_load_attempted"])
        self.assertFalse(context["private_endpoint_called"])
        self.assertFalse(context["order_endpoint_called"])
        self.assertFalse(context["order_adapter_called"])
        self.assertFalse(context["live_key_loaded"])
        self.assertFalse(context["live_order_allowed"])

    def test_alternative_public_replay_prefers_robust_candidate_over_raw_ev(self):
        cycle_hash = "A" * 64
        generation_report = {
            "generation_status": "ALTERNATIVE_REVIEW_READY",
            "candidate_items": [
                {
                    "candidate_id": "KRW-ALPHA-pullback-trend-long",
                    "symbol": "KRW-ALPHA",
                    "candidate_status": "REVIEW_READY",
                    "source_runtime_cycle_id": "cycle-robust-selection",
                    "source_runtime_cycle_hash": cycle_hash,
                    "net_ev_after_cost_bps": 50.0,
                },
                {
                    "candidate_id": "KRW-BETA-pullback-trend-long",
                    "symbol": "KRW-BETA",
                    "candidate_status": "REVIEW_READY",
                    "source_runtime_cycle_id": "cycle-robust-selection",
                    "source_runtime_cycle_hash": cycle_hash,
                    "net_ev_after_cost_bps": 10.0,
                },
            ],
        }
        runtime = {
            "cycle_id": "cycle-robust-selection",
            "cycle_hash": cycle_hash,
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
        }
        history = {"history_id": "multi-candidate-selection-history", "history_hash": "H" * 64, "samples": []}

        def fake_scorecard(source_runtime: dict, *, candidate_id: str):
            del source_runtime
            symbol = candidate_id.split("-pullback", 1)[0]
            return {
                "candidate_id": candidate_id,
                "symbol": symbol,
                "session_id": "mvp1_upbit_paper_launcher",
                "source_runtime_cycle_id": "cycle-robust-selection",
                "source_runtime_cycle_hash": cycle_hash,
                "strategy_id": "trend_pullback",
                "strategy_build_id": "trend-pullback-v1",
                "parameter_hash": "P" * 64,
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "net_ev_after_cost_bps": 50.0 if "ALPHA" in candidate_id else 10.0,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }

        def fake_replay_report(*, candidate_scorecard: dict, market_data: dict, replay_id: str, **kwargs):
            del market_data, kwargs
            return {
                "schema_id": "trader1.public_replay_robustness_report.v1",
                "replay_id": replay_id,
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "REPLAY",
                "session_id": candidate_scorecard["session_id"],
                "symbol": candidate_scorecard["symbol"],
                "candidate_id": candidate_scorecard["candidate_id"],
                "strategy_id": candidate_scorecard["strategy_id"],
                "strategy_build_id": candidate_scorecard["strategy_build_id"],
                "parameter_hash": candidate_scorecard["parameter_hash"],
                "public_market_data_hash": "M" * 64,
                "sample_count": 12,
                "min_required_sample_count": 1,
                "replay_status": "PASS",
                "primary_blocker_code": None,
                "blockers": [],
                "replay_closed_trade_sample_count": 1,
                "replay_closed_trade_status": "PASS",
                "min_required_closed_trade_sample_count": 1,
                "replay_closed_trade_deficit": 0,
                "replay_closed_trade_maturity_status": "PASS",
                "replay_closed_trade_maturity_blocker_code": None,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
                "report_hash": ("B" if "BETA" in candidate_scorecard["candidate_id"] else "C") * 64,
            }

        diagnostic_thresholds = []

        def fake_overfit(*, candidate_scorecard: dict, **kwargs):
            diagnostic_thresholds.append(kwargs.get("min_required_sample_count"))
            robust = "BETA" in candidate_scorecard["candidate_id"]
            return {
                "candidate_id": candidate_scorecard["candidate_id"],
                "robustness_eligible": robust,
                "oos_status": "PASS" if robust else "FAIL",
                "walk_forward_status": "PASS" if robust else "FAIL",
                "bootstrap_status": "PASS" if robust else "FAIL",
                "overfit_status": "LOW" if robust else "HIGH",
                "concentration_risk_status": "LOW" if robust else "HIGH",
                "oos_net_ev_after_cost_bps": 8.0 if robust else 0.1,
                "bootstrap_confidence_lower_bps": 2.0 if robust else 0.1,
                "walk_forward_pass_rate": 0.8 if robust else 0.0,
                "ranking_stability_score": 0.9 if robust else 0.0,
                "blockers": [] if robust else [{"code": "OOS_FAILED"}],
                "source_evidence_ids": [],
                "diagnostic_hash": "D" * 64,
            }

        def fake_history_fetcher(*, symbol: str, session_id: str, target_count: int, page_size: int, timeout_seconds: float):
            del target_count, page_size, timeout_seconds
            return _public_replay_fixture(symbol=symbol, session_id=session_id, count=20)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("tools.run_upbit_paper_candidate_scorecard.candidate_scorecard_from_upbit_paper_runtime_cycle", side_effect=fake_scorecard), patch(
                "tools.run_upbit_paper_candidate_scorecard.build_public_replay_robustness_report",
                side_effect=fake_replay_report,
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard.validate_public_replay_robustness_report",
                return_value=SimpleNamespace(status="PASS", blocker_code=None, message="ok"),
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard.overfit_diagnostic_from_upbit_paper_runtime",
                side_effect=fake_overfit,
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard.performance_inputs_from_runtime_sample_history",
                return_value=({}, {}, ["performance_summary:multi-candidate-selection:" + "E" * 64]),
            ), patch("tools.run_upbit_paper_candidate_scorecard._overfit_diagnostic_errors", return_value=[]):
                context = _build_and_write_alternative_public_replay(
                    root=root,
                    session_id="mvp1_upbit_paper_launcher",
                    candidate_generation_report=generation_report,
                    history=history,
                    runtime_cycle_report=runtime,
                    candidate_discovery_runtime=None,
                    target_count=20,
                    page_size=20,
                    timeout_seconds=1.0,
                    max_replay_windows=10,
                    min_required_sample_count=1,
                    candidate_limit=2,
                    public_replay_history_fetcher=fake_history_fetcher,
                )

        self.assertEqual(context["status"], "PASS")
        self.assertEqual(context["candidate_id"], "KRW-BETA-pullback-trend-long")
        self.assertEqual(context["candidate_review_evaluated_count"], 2)
        self.assertEqual(context["candidate_review_robust_candidate_count"], 1)
        self.assertEqual(context["candidate_review_selection_reason"], "ROBUSTNESS_ELIGIBLE_SELECTED")
        self.assertEqual(diagnostic_thresholds, [1, 1])
        self.assertEqual(
            [item["candidate_id"] for item in context["candidate_review_evaluations"]],
            ["KRW-ALPHA-pullback-trend-long", "KRW-BETA-pullback-trend-long"],
        )
        self.assertFalse(context["live_order_allowed"])

    def test_alternative_public_replay_prefers_closed_trade_evidence_over_raw_ev_when_blocked(self):
        cycle_hash = "A" * 64
        generation_report = {
            "generation_status": "ALTERNATIVE_REVIEW_READY",
            "candidate_items": [
                {
                    "candidate_id": "KRW-ALPHA-pullback-trend-long",
                    "symbol": "KRW-ALPHA",
                    "candidate_status": "REVIEW_READY",
                    "source_runtime_cycle_id": "cycle-closed-trade-selection",
                    "source_runtime_cycle_hash": cycle_hash,
                    "net_ev_after_cost_bps": 80.0,
                },
                {
                    "candidate_id": "KRW-BETA-pullback-trend-long",
                    "symbol": "KRW-BETA",
                    "candidate_status": "REVIEW_READY",
                    "source_runtime_cycle_id": "cycle-closed-trade-selection",
                    "source_runtime_cycle_hash": cycle_hash,
                    "net_ev_after_cost_bps": 5.0,
                },
            ],
        }
        runtime = {
            "cycle_id": "cycle-closed-trade-selection",
            "cycle_hash": cycle_hash,
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
        }

        def fake_scorecard(source_runtime: dict, *, candidate_id: str):
            del source_runtime
            symbol = candidate_id.split("-pullback", 1)[0]
            return {
                "candidate_id": candidate_id,
                "symbol": symbol,
                "session_id": "mvp1_upbit_paper_launcher",
                "source_runtime_cycle_id": "cycle-closed-trade-selection",
                "source_runtime_cycle_hash": cycle_hash,
                "strategy_id": "trend_pullback",
                "strategy_build_id": "trend-pullback-v1",
                "parameter_hash": "P" * 64,
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "net_ev_after_cost_bps": 80.0 if "ALPHA" in candidate_id else 5.0,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }

        def fake_replay_report(*, candidate_scorecard: dict, market_data: dict, replay_id: str, **kwargs):
            del market_data, kwargs
            closed_candidate = "BETA" in candidate_scorecard["candidate_id"]
            return {
                "schema_id": "trader1.public_replay_robustness_report.v1",
                "replay_id": replay_id,
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "REPLAY",
                "session_id": candidate_scorecard["session_id"],
                "symbol": candidate_scorecard["symbol"],
                "candidate_id": candidate_scorecard["candidate_id"],
                "strategy_id": candidate_scorecard["strategy_id"],
                "strategy_build_id": candidate_scorecard["strategy_build_id"],
                "parameter_hash": candidate_scorecard["parameter_hash"],
                "public_market_data_hash": "M" * 64,
                "sample_count": 8 if closed_candidate else 12,
                "min_required_sample_count": 20,
                "replay_status": "BLOCKED",
                "primary_blocker_code": "SAMPLE_INSUFFICIENT",
                "blockers": [{"code": "SAMPLE_INSUFFICIENT", "message": "short public replay window"}],
                "replay_closed_trade_sample_count": 2 if closed_candidate else 0,
                "replay_closed_trade_status": "PASS" if closed_candidate else "UNTESTED",
                "replay_strategy_exit_policy_sample_count": 2 if closed_candidate else 0,
                "replay_strategy_exit_policy_match_count": 2 if closed_candidate else 0,
                "replay_strategy_exit_policy_mismatch_count": 0,
                "replay_strategy_exit_policy_status": "PASS" if closed_candidate else "UNTESTED",
                "replay_profit_factor": 1.6 if closed_candidate else 0.0,
                "replay_profit_factor_status": "PASS" if closed_candidate else "UNTESTED",
                "replay_realized_vs_expected_edge_bps": 3.0 if closed_candidate else 0.0,
                "replay_realized_vs_expected_edge_status": "PASS" if closed_candidate else "UNTESTED",
                "replay_execution_cost_delta_bps": 0.5 if closed_candidate else 0.0,
                "replay_execution_cost_status": "PASS" if closed_candidate else "UNTESTED",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
                "report_hash": ("B" if closed_candidate else "C") * 64,
            }

        def fake_history_fetcher(*, symbol: str, session_id: str, target_count: int, page_size: int, timeout_seconds: float):
            del target_count, page_size, timeout_seconds
            return _public_replay_fixture(symbol=symbol, session_id=session_id, count=20)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "tools.run_upbit_paper_candidate_scorecard.candidate_scorecard_from_upbit_paper_runtime_cycle",
                side_effect=fake_scorecard,
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard.build_public_replay_robustness_report",
                side_effect=fake_replay_report,
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard.validate_public_replay_robustness_report",
                return_value=SimpleNamespace(status="PASS", blocker_code=None, message="ok"),
            ):
                context = _build_and_write_alternative_public_replay(
                    root=root,
                    session_id="mvp1_upbit_paper_launcher",
                    candidate_generation_report=generation_report,
                    history={"history_id": "closed-trade-selection-history", "history_hash": "H" * 64, "samples": []},
                    runtime_cycle_report=runtime,
                    candidate_discovery_runtime=None,
                    target_count=20,
                    page_size=20,
                    timeout_seconds=1.0,
                    max_replay_windows=10,
                    min_required_sample_count=20,
                    candidate_limit=2,
                    public_replay_history_fetcher=fake_history_fetcher,
                )

        self.assertEqual(context["status"], "BLOCKED")
        self.assertEqual(context["blocker_code"], "SAMPLE_INSUFFICIENT")
        self.assertEqual(context["candidate_id"], "KRW-BETA-pullback-trend-long")
        self.assertEqual(context["candidate_review_selection_reason"], "BEST_CLOSED_TRADE_REPLAY_BLOCKED")
        self.assertEqual(context["replay_closed_trade_sample_count"], 2)
        self.assertEqual(context["min_required_closed_trade_sample_count"], 20)
        self.assertEqual(context["replay_closed_trade_deficit"], 18)
        self.assertEqual(context["replay_closed_trade_maturity_status"], "BLOCKED")
        self.assertEqual(context["replay_strategy_exit_policy_sample_count"], 2)
        review_rows = {
            row["candidate_id"]: row
            for row in context["candidate_review_evaluations"]
        }
        self.assertEqual(review_rows["KRW-BETA-pullback-trend-long"]["replay_closed_trade_sample_count"], 2)
        self.assertEqual(review_rows["KRW-BETA-pullback-trend-long"]["replay_closed_trade_deficit"], 18)
        self.assertEqual(
            review_rows["KRW-BETA-pullback-trend-long"]["replay_closed_trade_maturity_status"],
            "BLOCKED",
        )
        self.assertEqual(review_rows["KRW-ALPHA-pullback-trend-long"]["replay_closed_trade_sample_count"], 0)
        self.assertFalse(context["live_order_allowed"])

    def test_alternative_public_replay_status_distinguishes_contract_pass_from_replay_blocked(self):
        def fake_market_symbols_fetcher(*, session_id: str, timeout_seconds: float):
            del timeout_seconds
            return build_upbit_public_krw_symbol_discovery_report_from_payload(
                payload=[{"market": "KRW-ETH"}],
                session_id=session_id,
            )

        def fake_ticker_fetcher(*, symbols: list[str], session_id: str, timeout_seconds: float):
            del timeout_seconds
            requested = build_upbit_krw_market_symbols_from_rest_payload([{"market": symbol} for symbol in symbols])
            return build_upbit_public_ticker_snapshot_from_rest_payload(
                requested_symbols=requested,
                session_id=session_id,
                payload=[
                    {
                        "market": "KRW-ETH",
                        "trade_price": "1000000",
                        "acc_trade_price_24h": "9000000000",
                        "signed_change_rate": "0.035",
                        "acc_trade_volume_24h": "9000",
                    }
                ],
            )

        def fake_candle_fetcher(*, symbol: str, session_id: str, timeout_seconds: float):
            del timeout_seconds
            return build_upbit_public_candle_fixture(
                symbol=symbol,
                session_id=session_id,
                profile="UPTREND_PULLBACK",
            )

        def fake_replay_history_fetcher(
            *,
            symbol: str,
            session_id: str,
            target_count: int,
            page_size: int,
            timeout_seconds: float,
        ):
            del target_count, page_size, timeout_seconds
            return build_upbit_public_candle_fixture(
                symbol=symbol,
                session_id=session_id,
                profile="UPTREND_PULLBACK",
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_short_paper(root)

            result = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                attempt_public_discovery=True,
                candidate_discovery_symbol_limit=1,
                market_symbols_fetcher=fake_market_symbols_fetcher,
                public_ticker_fetcher=fake_ticker_fetcher,
                public_candle_fetcher=fake_candle_fetcher,
                public_replay_history_fetcher=fake_replay_history_fetcher,
                alternative_replay_max_windows=10,
                alternative_replay_min_required_sample_count=20,
            )
            generation_report = _load_written(root, result, "candidate_generation_report_path")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["alternative_public_replay_contract_status"], "PASS")
        self.assertIsNone(result["alternative_public_replay_contract_blocker_code"])
        self.assertEqual(result["alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(result["alternative_public_replay_replay_status"], "BLOCKED")
        self.assertEqual(result["alternative_public_replay_blocker_code"], "SAMPLE_INSUFFICIENT")
        self.assertEqual(result["candidate_generation_status"], "ALTERNATIVE_PUBLIC_REPLAY_BLOCKED")
        self.assertEqual(result["candidate_generation_best_alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(generation_report["best_alternative_public_replay_status"], "BLOCKED")
        self.assertFalse(generation_report["live_order_allowed"])
        self.assertFalse(result["credential_load_attempted"])
        self.assertFalse(result["private_endpoint_called"])
        self.assertFalse(result["order_endpoint_called"])
        self.assertFalse(result["order_adapter_called"])
        self.assertFalse(result["live_key_loaded"])
        self.assertFalse(result["live_order_allowed"])

    def test_alternative_public_replay_fetch_failure_is_written_and_bound_to_generation_report(self):
        def fake_market_symbols_fetcher(*, session_id: str, timeout_seconds: float):
            del timeout_seconds
            return build_upbit_public_krw_symbol_discovery_report_from_payload(
                payload=[{"market": "KRW-ETH"}],
                session_id=session_id,
            )

        def fake_ticker_fetcher(*, symbols: list[str], session_id: str, timeout_seconds: float):
            del timeout_seconds
            requested = build_upbit_krw_market_symbols_from_rest_payload([{"market": symbol} for symbol in symbols])
            return build_upbit_public_ticker_snapshot_from_rest_payload(
                requested_symbols=requested,
                session_id=session_id,
                payload=[
                    {
                        "market": "KRW-ETH",
                        "trade_price": "1000000",
                        "acc_trade_price_24h": "9000000000",
                        "signed_change_rate": "0.035",
                        "acc_trade_volume_24h": "9000",
                    }
                ],
            )

        def fake_candle_fetcher(*, symbol: str, session_id: str, timeout_seconds: float):
            del timeout_seconds
            return build_upbit_public_candle_fixture(
                symbol=symbol,
                session_id=session_id,
                profile="UPTREND_PULLBACK",
            )

        def failing_replay_history_fetcher(
            *,
            symbol: str,
            session_id: str,
            target_count: int,
            page_size: int,
            timeout_seconds: float,
        ):
            del symbol, session_id, target_count, page_size, timeout_seconds
            raise TimeoutError("public candle read timed out")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_short_paper(root)

            result = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                attempt_public_discovery=True,
                candidate_discovery_symbol_limit=1,
                market_symbols_fetcher=fake_market_symbols_fetcher,
                public_ticker_fetcher=fake_ticker_fetcher,
                public_candle_fetcher=fake_candle_fetcher,
                public_replay_history_fetcher=failing_replay_history_fetcher,
                alternative_replay_max_windows=10,
                alternative_replay_min_required_sample_count=1,
            )
            generation_report = _load_written(root, result, "candidate_generation_report_path")
            replay_report = _load_written(root, result, "alternative_public_replay_report_path")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(result["alternative_public_replay_blocker_code"], "DATA_QUALITY_INSUFFICIENT")
        self.assertEqual(result["alternative_public_replay_contract_status"], "PASS")
        self.assertEqual(result["alternative_public_replay_replay_status"], "BLOCKED")
        self.assertEqual(result["alternative_public_replay_sample_count"], 0)
        self.assertEqual(result["candidate_generation_status"], "ALTERNATIVE_PUBLIC_REPLAY_BLOCKED")
        self.assertEqual(result["candidate_generation_best_alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(generation_report["best_alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(generation_report["best_alternative_public_replay_primary_blocker_code"], "DATA_QUALITY_INSUFFICIENT")
        self.assertTrue(
            any(source_id.startswith("public_replay_robustness:") for source_id in generation_report["source_evidence_ids"])
        )
        self.assertTrue(
            any(source_id.startswith("public_market_data:") for source_id in generation_report["source_evidence_ids"])
        )
        self.assertEqual(replay_report["public_market_data_source"], "PUBLIC_REST_READ_ONLY_FETCH_FAILED")
        self.assertEqual(replay_report["public_market_data_fetch_status"], "FAILED")
        self.assertEqual(replay_report["public_market_data_error_type"], "TimeoutError")
        self.assertEqual(replay_report["primary_blocker_code"], "DATA_QUALITY_INSUFFICIENT")
        self.assertEqual(replay_report["sample_rows"], [])
        self.assertFalse(generation_report["live_order_allowed"])
        self.assertFalse(result["credential_load_attempted"])
        self.assertFalse(result["private_endpoint_called"])
        self.assertFalse(result["order_endpoint_called"])
        self.assertFalse(result["order_adapter_called"])
        self.assertFalse(result["live_key_loaded"])
        self.assertFalse(result["live_order_allowed"])

    def test_bounded_public_discovery_expands_once_when_initial_public_set_has_no_entry_candidate(self):
        def fake_market_symbols_fetcher(*, session_id: str, timeout_seconds: float):
            del timeout_seconds
            return build_upbit_public_krw_symbol_discovery_report_from_payload(
                session_id=session_id,
                payload=[
                    {"market": "KRW-BEAR", "korean_name": "Bear", "english_name": "Bear"},
                    {"market": "KRW-ALT", "korean_name": "Alt", "english_name": "Alt"},
                    {"market": "KRW-RISK", "korean_name": "Risk", "english_name": "Risk"},
                ],
            )

        def fake_ticker_fetcher(*, symbols: list[str], session_id: str, timeout_seconds: float):
            del timeout_seconds
            requested = build_upbit_krw_market_symbols_from_rest_payload([{"market": symbol} for symbol in symbols])
            return build_upbit_public_ticker_snapshot_from_rest_payload(
                requested_symbols=requested,
                session_id=session_id,
                payload=[
                    {
                        "market": "KRW-BEAR",
                        "trade_price": "1000",
                        "acc_trade_price_24h": "9000000000",
                        "signed_change_rate": "0.020",
                        "acc_trade_volume_24h": "9000000",
                    },
                    {
                        "market": "KRW-ALT",
                        "trade_price": "2000",
                        "acc_trade_price_24h": "1500000000",
                        "signed_change_rate": "0.050",
                        "acc_trade_volume_24h": "750000",
                    },
                    {
                        "market": "KRW-RISK",
                        "trade_price": "1500",
                        "acc_trade_price_24h": "1000000000",
                        "signed_change_rate": "-0.020",
                        "acc_trade_volume_24h": "600000",
                    },
                ],
            )

        def fake_candle_fetcher(*, symbol: str, session_id: str, timeout_seconds: float):
            del timeout_seconds
            profile = "UPTREND_PULLBACK" if symbol == "KRW-ALT" else "DOWNTREND"
            return build_upbit_public_candle_fixture(
                symbol=symbol,
                session_id=session_id,
                profile=profile,
            )

        def fake_replay_history_fetcher(
            *,
            symbol: str,
            session_id: str,
            target_count: int,
            page_size: int,
            timeout_seconds: float,
        ):
            del target_count, page_size, timeout_seconds
            return build_upbit_public_candle_fixture(
                symbol=symbol,
                session_id=session_id,
                profile="UPTREND_PULLBACK",
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_short_paper(root)

            result = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                attempt_public_discovery=True,
                candidate_discovery_symbol_limit=1,
                market_symbols_fetcher=fake_market_symbols_fetcher,
                public_ticker_fetcher=fake_ticker_fetcher,
                public_candle_fetcher=fake_candle_fetcher,
                public_replay_history_fetcher=fake_replay_history_fetcher,
                alternative_replay_max_windows=10,
                alternative_replay_min_required_sample_count=1,
            )
            generation_report = _load_written(root, result, "candidate_generation_report_path")
            discovery_runtime = _load_written(root, result, "candidate_discovery_runtime_cycle_path")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["candidate_discovery_status"], "PASS")
        self.assertTrue(result["candidate_discovery_adaptive_expansion_attempted"])
        self.assertIn("expanded once", result["candidate_discovery_message"])
        self.assertEqual(result["candidate_discovery_initial_symbol_count"], 1)
        self.assertEqual(result["candidate_discovery_expanded_symbol_count"], 3)
        self.assertEqual(result["candidate_discovery_max_expanded_symbol_count"], 3)
        self.assertEqual(result["candidate_discovery_symbol_count"], 3)
        self.assertEqual(discovery_runtime["symbol_evidence_scorecard_count"], 3)
        self.assertGreaterEqual(result["candidate_discovery_paper_entry_review_candidate_count"], 1)
        self.assertEqual(generation_report["generation_status"], "ALTERNATIVE_PUBLIC_REPLAY_BLOCKED")
        self.assertEqual(generation_report["best_alternative_symbol"], "KRW-ALT")
        self.assertEqual(result["alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(result["alternative_public_replay_blocker_code"], "REPLAY_CLOSED_TRADES_MISSING")
        self.assertEqual(result["alternative_public_replay_symbol"], "KRW-ALT")
        self.assertFalse(generation_report["live_order_allowed"])
        self.assertFalse(result["credential_load_attempted"])
        self.assertFalse(result["private_endpoint_called"])
        self.assertFalse(result["order_endpoint_called"])
        self.assertFalse(result["order_adapter_called"])
        self.assertFalse(result["live_key_loaded"])
        self.assertFalse(result["live_order_allowed"])

    def test_bounded_public_discovery_reports_no_trade_reason_coverage_when_no_alternative_is_ready(self):
        def fake_market_symbols_fetcher(*, session_id: str, timeout_seconds: float):
            del timeout_seconds
            return build_upbit_public_krw_symbol_discovery_report_from_payload(
                session_id=session_id,
                payload=[
                    {"market": "KRW-BEAR", "korean_name": "Bear", "english_name": "Bear"},
                    {"market": "KRW-RISK", "korean_name": "Risk", "english_name": "Risk"},
                ],
            )

        def fake_ticker_fetcher(*, symbols: list[str], session_id: str, timeout_seconds: float):
            del timeout_seconds
            requested = build_upbit_krw_market_symbols_from_rest_payload([{"market": symbol} for symbol in symbols])
            return build_upbit_public_ticker_snapshot_from_rest_payload(
                requested_symbols=requested,
                session_id=session_id,
                payload=[
                    {
                        "market": "KRW-BEAR",
                        "trade_price": "1000",
                        "acc_trade_price_24h": "9000000000",
                        "signed_change_rate": "-0.045",
                        "acc_trade_volume_24h": "9000000",
                    },
                    {
                        "market": "KRW-RISK",
                        "trade_price": "2000",
                        "acc_trade_price_24h": "8000000000",
                        "signed_change_rate": "-0.035",
                        "acc_trade_volume_24h": "4000000",
                    },
                ],
            )

        def fake_candle_fetcher(*, symbol: str, session_id: str, timeout_seconds: float):
            del timeout_seconds
            return build_upbit_public_candle_fixture(
                symbol=symbol,
                session_id=session_id,
                profile="DOWNTREND",
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_short_paper(root)

            result = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                attempt_public_discovery=True,
                candidate_discovery_symbol_limit=2,
                market_symbols_fetcher=fake_market_symbols_fetcher,
                public_ticker_fetcher=fake_ticker_fetcher,
                public_candle_fetcher=fake_candle_fetcher,
            )
            generation_report = _load_written(root, result, "candidate_generation_report_path")
            discovery_runtime = _load_written(root, result, "candidate_discovery_runtime_cycle_path")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["candidate_discovery_status"], "PASS")
        self.assertEqual(generation_report["generation_status"], "NO_ALTERNATIVE_READY")
        self.assertEqual(generation_report["primary_blocker_code"], "STRATEGY_NOT_ELIGIBLE")
        self.assertEqual(result["candidate_generation_status"], "NO_ALTERNATIVE_READY")
        self.assertEqual(result["candidate_generation_primary_blocker_code"], "STRATEGY_NOT_ELIGIBLE")
        self.assertEqual(result["candidate_discovery_symbol_count"], 2)
        self.assertFalse(result["candidate_discovery_adaptive_expansion_attempted"])
        self.assertEqual(result["candidate_discovery_initial_symbol_count"], 2)
        self.assertEqual(result["candidate_discovery_expanded_symbol_count"], 2)
        self.assertEqual(result["candidate_discovery_max_expanded_symbol_count"], 2)
        self.assertGreaterEqual(result["candidate_discovery_evaluated_candidate_count"], 2)
        self.assertEqual(result["candidate_discovery_paper_entry_review_candidate_count"], 0)
        self.assertEqual(
            result["candidate_discovery_blocked_candidate_count"],
            result["candidate_discovery_evaluated_candidate_count"],
        )
        no_trade_counts = {
            item["code"]: item["count"]
            for item in result["candidate_discovery_no_trade_reason_counts"]
        }
        self.assertIn("REGIME_MISMATCH", no_trade_counts)
        entry_block_counts = {
            item["code"]: item["count"]
            for item in result["candidate_discovery_entry_block_reason_counts"]
        }
        self.assertIn("DOWNTREND_SPOT_LONG_BLOCK", entry_block_counts)
        self.assertEqual(len(result["candidate_discovery_top_blocked_symbols"]), 2)
        self.assertEqual(discovery_runtime["symbol_evidence_scorecard_count"], 2)
        self.assertFalse(generation_report["live_order_allowed"])
        self.assertFalse(result["credential_load_attempted"])
        self.assertFalse(result["private_endpoint_called"])
        self.assertFalse(result["order_endpoint_called"])
        self.assertFalse(result["order_adapter_called"])
        self.assertFalse(result["live_key_loaded"])
        self.assertFalse(result["live_order_allowed"])

    def test_missing_bound_cycle_sources_overwrite_stale_history_with_blocked_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_short_paper(root)
            first_result = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
            )
            stale_history = _load_written(root, first_result, "runtime_sample_history_path")
            for sample in stale_history["samples"]:
                (root / sample["source_runtime_cycle_path"]).unlink()

            blocked = build_current_upbit_paper_candidate_scorecard(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
            )
            rewritten_history = _load_written(root, blocked, "runtime_sample_history_path")

        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["blocker_code"], "RECONCILIATION_REQUIRED")
        self.assertEqual(blocked["runtime_sample_history_status"], "BLOCKED")
        self.assertEqual(rewritten_history["runtime_sample_status"], "BLOCKED")
        self.assertEqual(rewritten_history["accepted_cycle_sample_count"], 0)
        self.assertGreater(rewritten_history["invalid_source_count"], 0)
        self.assertFalse(blocked["live_order_allowed"])
        self.assertFalse(blocked["scale_up_allowed"])

    def test_bridge_keeps_robust_diagnostic_blocked_until_performance_evidence_passes(self):
        def robust_diagnostic(*, candidate_scorecard: dict, runtime_sample_history: dict, root: Path) -> dict:
            report = overfit_diagnostic_from_upbit_paper_runtime(
                candidate_scorecard=candidate_scorecard,
                runtime_sample_history=runtime_sample_history,
                root=root,
            )
            robust = copy.deepcopy(report)
            source_ids = [
                robustness_source_evidence_id("oos", candidate_scorecard["source_runtime_cycle_id"], candidate_scorecard["source_runtime_cycle_hash"]),
                robustness_source_evidence_id(
                    "walk_forward",
                    candidate_scorecard["source_runtime_cycle_id"],
                    candidate_scorecard["source_runtime_cycle_hash"],
                ),
                robustness_source_evidence_id(
                    "bootstrap",
                    candidate_scorecard["source_runtime_cycle_id"],
                    candidate_scorecard["source_runtime_cycle_hash"],
                ),
            ]
            robust.update(
                {
                    "diagnostic_status": "ROBUST_FOR_PAPER_REVIEW",
                    "oos_status": "PASS",
                    "walk_forward_status": "PASS",
                    "bootstrap_status": "PASS",
                    "ranking_stability_status": "PASS",
                    "overfit_status": "LOW",
                    "sample_count": 300,
                    "train_window_count": 180,
                    "oos_window_count": 120,
                    "walk_forward_window_count": 6,
                    "bootstrap_iteration_count": 500,
                    "in_sample_net_ev_after_cost_bps": 14.0,
                    "oos_net_ev_after_cost_bps": 12.0,
                    "oos_degradation_bps": 2.0,
                    "walk_forward_pass_rate": 0.83,
                    "bootstrap_confidence_lower_bps": 4.0,
                    "ranking_stability_score": 0.88,
                    "concentration_risk_status": "LOW",
                    "survivorship_bias_check": "PASS",
                    "data_snooping_check": "PASS",
                    "robustness_eligible": True,
                    "blockers": [],
                    "source_evidence_ids": sorted(set(robust["source_evidence_ids"] + source_ids)),
                }
            )
            robust["diagnostic_hash"] = overfit_diagnostic_report_hash(robust)
            return robust

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_short_paper(root)

            with patch(
                "tools.run_upbit_paper_candidate_scorecard.overfit_diagnostic_from_upbit_paper_runtime",
                side_effect=robust_diagnostic,
            ):
                result = build_current_upbit_paper_candidate_scorecard(
                    root=root,
                    session_id="mvp1_upbit_paper_launcher",
            )
            scorecard = _load_written(root, result, "candidate_scorecard_path")
            diagnostic = _load_written(root, result, "overfit_diagnostic_path")
            scoped_scorecard = json.loads(
                _candidate_snapshot_path(root, result, scorecard).read_text(encoding="utf-8")
            )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(_overfit_diagnostic_errors(diagnostic), [])
        self.assertEqual(_candidate_scorecard_net_ev_errors(scorecard), [])
        self.assertEqual(_candidate_scorecard_net_ev_errors(scoped_scorecard), [])
        self.assertEqual(scoped_scorecard["candidate_id"], scorecard["candidate_id"])
        self.assertTrue(diagnostic["robustness_eligible"])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertIn("SAMPLE_INSUFFICIENT", {blocker["code"] for blocker in scorecard["blockers"]})
        self.assertIn("EXECUTION_FEEDBACK_DIVERGENT", {blocker["code"] for blocker in scorecard["blockers"]})
        self.assertEqual(scorecard["live_readiness_status"], "NOT_LIVE_READY")
        self.assertFalse(scorecard["live_order_ready"])
        self.assertFalse(scorecard["live_order_allowed"])
        self.assertFalse(scorecard["can_live_trade"])
        self.assertFalse(scorecard["scale_up_allowed"])
        self.assertFalse(result["live_order_allowed"])

    def test_bridge_requires_closed_trade_performance_before_ranking_eligible(self):
        def robust_diagnostic(*, candidate_scorecard: dict, runtime_sample_history: dict, root: Path) -> dict:
            report = overfit_diagnostic_from_upbit_paper_runtime(
                candidate_scorecard=candidate_scorecard,
                runtime_sample_history=runtime_sample_history,
                root=root,
            )
            robust = copy.deepcopy(report)
            source_ids = [
                robustness_source_evidence_id("oos", candidate_scorecard["source_runtime_cycle_id"], candidate_scorecard["source_runtime_cycle_hash"]),
                robustness_source_evidence_id(
                    "walk_forward",
                    candidate_scorecard["source_runtime_cycle_id"],
                    candidate_scorecard["source_runtime_cycle_hash"],
                ),
                robustness_source_evidence_id(
                    "bootstrap",
                    candidate_scorecard["source_runtime_cycle_id"],
                    candidate_scorecard["source_runtime_cycle_hash"],
                ),
            ]
            robust.update(
                {
                    "diagnostic_status": "ROBUST_FOR_PAPER_REVIEW",
                    "oos_status": "PASS",
                    "walk_forward_status": "PASS",
                    "bootstrap_status": "PASS",
                    "ranking_stability_status": "PASS",
                    "overfit_status": "LOW",
                    "sample_count": 300,
                    "train_window_count": 180,
                    "oos_window_count": 120,
                    "walk_forward_window_count": 6,
                    "bootstrap_iteration_count": 500,
                    "in_sample_net_ev_after_cost_bps": 14.0,
                    "oos_net_ev_after_cost_bps": 12.0,
                    "oos_degradation_bps": 2.0,
                    "walk_forward_pass_rate": 0.83,
                    "bootstrap_confidence_lower_bps": 4.0,
                    "ranking_stability_score": 0.88,
                    "concentration_risk_status": "LOW",
                    "survivorship_bias_check": "PASS",
                    "data_snooping_check": "PASS",
                    "robustness_eligible": True,
                    "blockers": [],
                    "source_evidence_ids": sorted(set(robust["source_evidence_ids"] + source_ids)),
                }
            )
            robust["diagnostic_hash"] = overfit_diagnostic_report_hash(robust)
            return robust

        def strong_performance(*, candidate_scorecard: dict, runtime_sample_history: dict, root: Path):
            history_id = str(runtime_sample_history.get("history_id") or "history")
            history_hash = str(runtime_sample_history.get("history_hash") or "H" * 64)
            return (
                dict(PERFORMANCE_PASS),
                {
                    "closed_trade_sample_count": 42,
                    "min_closed_trade_sample_count": 30,
                    "strategy_exit_policy_sample_count": 42,
                    "min_strategy_exit_policy_sample_count": 30,
                    "strategy_exit_policy_match_count": 42,
                    "strategy_exit_policy_mismatch_count": 0,
                    "strategy_exit_reason_count": 42,
                    "strategy_exit_reason_counts": [{"reason_code": "TRAILING_STOP", "count": 42}],
                    "regime_outcome_sample_count": 42,
                    "min_regime_outcome_sample_count": 4,
                    "regime_outcome_covered_count": 4,
                    "min_regime_outcome_covered_count": 4,
                    "regime_outcome_trade_count": 39,
                    "regime_outcome_no_trade_count": 3,
                    "regime_outcome_mismatch_count": 0,
                    "regime_outcome_counts": [
                        {
                            "regime": "UPTREND",
                            "sample_count": 39,
                            "trade_count": 39,
                            "no_trade_count": 0,
                            "mismatch_count": 0,
                            "trade_allowed": True,
                            "primary_blocker_code": None,
                        },
                        {
                            "regime": "RANGE",
                            "sample_count": 1,
                            "trade_count": 0,
                            "no_trade_count": 1,
                            "mismatch_count": 0,
                            "trade_allowed": True,
                            "primary_blocker_code": "REGIME_MISMATCH",
                        },
                        {
                            "regime": "DOWNTREND",
                            "sample_count": 1,
                            "trade_count": 0,
                            "no_trade_count": 1,
                            "mismatch_count": 0,
                            "trade_allowed": False,
                            "primary_blocker_code": "REGIME_MISMATCH",
                        },
                        {
                            "regime": "RISK_OFF",
                            "sample_count": 1,
                            "trade_count": 0,
                            "no_trade_count": 1,
                            "mismatch_count": 0,
                            "trade_allowed": False,
                            "primary_blocker_code": "RISK_VETO",
                        },
                    ],
                    "realized_vs_expected_sample_count": 42,
                    "fill_quality_sample_count": 42,
                    "execution_cost_sample_count": 42,
                    "profit_factor": 1.42,
                    "min_profit_factor": 1.25,
                    "max_drawdown_pct": 4.8,
                    "max_allowed_drawdown_pct": 8.0,
                    "realized_vs_expected_edge_bps": 2.5,
                    "min_realized_vs_expected_edge_bps": 0.0,
                    "fill_quality_score": 0.91,
                    "min_fill_quality_score": 0.80,
                    "realized_fee_bps": 5.0,
                    "realized_slippage_bps": 16.0,
                    "realized_impact_bps": 3.0,
                    "expected_total_execution_cost_bps": 20.0,
                    "realized_total_execution_cost_bps": 21.0,
                    "execution_cost_delta_bps": 1.0,
                    "max_allowed_execution_cost_delta_bps": 2.0,
                },
                [
                    performance_source_evidence_id(
                        "closed_trades",
                        history_id,
                        history_hash,
                        candidate_scorecard["candidate_id"],
                    ),
                    performance_source_evidence_id(
                        "execution_quality",
                        history_id,
                        history_hash,
                        candidate_scorecard["candidate_id"],
                    ),
                    performance_source_evidence_id(
                        "performance_summary",
                        history_id,
                        history_hash,
                        candidate_scorecard["candidate_id"],
                    ),
                ],
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _run_short_paper(root)

            with patch(
                "tools.run_upbit_paper_candidate_scorecard.overfit_diagnostic_from_upbit_paper_runtime",
                side_effect=robust_diagnostic,
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard.performance_inputs_from_runtime_sample_history",
                side_effect=strong_performance,
            ):
                result = build_current_upbit_paper_candidate_scorecard(
                    root=root,
                    session_id="mvp1_upbit_paper_launcher",
                )
            scorecard = _load_written(root, result, "candidate_scorecard_path")
            strategy_memory = _load_written(root, result, "strategy_performance_memory_path")
            objective_profile = _load_written(root, result, "convergence_objective_profile_path")
            exploration_policy = _load_written(root, result, "exploration_exploitation_policy_path")
            optimizer_memory = _load_written(root, result, "optimizer_memory_state_path")
            profit_cycle = _load_written(root, result, "profit_convergence_cycle_report_path")
            matched_shadow = build_paper_shadow_evidence_accumulation_report(
                evidence_report_id="matched-current-scorecard-shadow",
                candidate_id=scorecard["candidate_id"],
                strategy_id=scorecard["strategy_id"],
                strategy_build_id=scorecard["strategy_build_id"],
                parameter_hash=scorecard["parameter_hash"],
                exchange=scorecard["exchange"],
                market_type=scorecard["market_type"],
                paper_session_id="mvp1_upbit_paper_launcher",
                shadow_session_id="mvp1_upbit_paper_launcher_shadow",
                paper_sample_count=30,
                shadow_sample_count=30,
                evidence_window_count=2,
                evidence_span_hours=4,
                entry_reason_count=5,
                no_trade_reason_count=5,
                cost_evidence_count=5,
            )
            shadow_path = _paper_shadow_evidence_path(root)
            shadow_path.parent.mkdir(parents=True, exist_ok=True)
            shadow_path.write_text(json.dumps(matched_shadow, indent=2, sort_keys=True), encoding="utf-8")

            with patch(
                "tools.run_upbit_paper_candidate_scorecard.overfit_diagnostic_from_upbit_paper_runtime",
                side_effect=robust_diagnostic,
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard.performance_inputs_from_runtime_sample_history",
                side_effect=strong_performance,
            ):
                shadow_bound_result = build_current_upbit_paper_candidate_scorecard(
                    root=root,
                    session_id="mvp1_upbit_paper_launcher",
                )
            shadow_strategy_memory = _load_written(root, shadow_bound_result, "strategy_performance_memory_path")
            shadow_optimizer_memory = _load_written(root, shadow_bound_result, "optimizer_memory_state_path")
            shadow_exploration_policy = _load_written(root, shadow_bound_result, "exploration_exploitation_policy_path")
            shadow_profit_cycle = _load_written(root, shadow_bound_result, "profit_convergence_cycle_report_path")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(_candidate_scorecard_net_ev_errors(scorecard), [])
        self.assertEqual(_strategy_performance_memory_errors(strategy_memory), [])
        self.assertEqual(_convergence_objective_profile_errors(objective_profile), [])
        self.assertEqual(_exploration_exploitation_policy_errors(exploration_policy), [])
        self.assertEqual(_optimizer_memory_state_errors(optimizer_memory), [])
        self.assertEqual(_profit_convergence_cycle_errors(profit_cycle), [])
        self.assertTrue(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["scorecard_scope"], "PAPER_SCORECARD_INPUT_ONLY")
        self.assertEqual(strategy_memory["performance_scope"], "PAPER_RUNTIME_SCORECARD_ONLY")
        self.assertEqual(strategy_memory["performance_status"], "COLLECTING")
        self.assertEqual(objective_profile["objective_status"], "EVALUATION_ONLY")
        self.assertEqual(exploration_policy["policy_status"], "ACTIVE_ANALYSIS_ONLY")
        self.assertEqual(exploration_policy["transition_decision"], "KEEP_EXPLORING")
        self.assertIn("MEASUREMENT_MISSING", {blocker["code"] for blocker in exploration_policy["blockers"]})
        self.assertEqual(result["paper_shadow_scorecard_binding_status"], "MISSING")
        self.assertEqual(profit_cycle["cycle_status"], "COLLECTING")
        self.assertEqual(profit_cycle["exploration_exploitation_policy_validator_status"], "PASS")
        self.assertEqual(profit_cycle["convergence_claim"], "NO_CLAIM")
        self.assertFalse(profit_cycle["candidate_ranking_allowed_for_paper"])
        self.assertIsNone(result["failure_analysis_path"])
        self.assertEqual(result["failure_analysis_status"], "NOT_REQUIRED")
        self.assertEqual(scorecard["closed_trade_status"], "PASS")
        self.assertEqual(scorecard["realized_vs_expected_sample_count"], 42)
        self.assertEqual(scorecard["fill_quality_sample_count"], 42)
        self.assertEqual(scorecard["profit_factor_status"], "PASS")
        self.assertFalse(scorecard["live_order_allowed"])
        self.assertEqual(shadow_bound_result["status"], "PASS")
        self.assertEqual(shadow_bound_result["paper_shadow_scorecard_binding_status"], "PASS")
        self.assertEqual(_strategy_performance_memory_errors(shadow_strategy_memory), [])
        self.assertEqual(_optimizer_memory_state_errors(shadow_optimizer_memory), [])
        self.assertEqual(_exploration_exploitation_policy_errors(shadow_exploration_policy), [])
        self.assertEqual(_profit_convergence_cycle_errors(shadow_profit_cycle), [])
        self.assertEqual(shadow_strategy_memory["performance_scope"], "PAPER_SHADOW_RESEARCH_ONLY")
        self.assertEqual(shadow_strategy_memory["performance_status"], "IMPROVING_AFTER_COST")
        self.assertEqual(shadow_strategy_memory["source_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(shadow_optimizer_memory["source_modes"], ["PAPER", "SHADOW"])
        self.assertTrue(shadow_strategy_memory["paper_shadow_separated"])
        self.assertEqual(shadow_profit_cycle["paper_shadow_evidence_accumulation_validator_status"], "PASS")
        self.assertFalse(shadow_profit_cycle["candidate_ranking_allowed_for_paper"])
        self.assertFalse(shadow_profit_cycle["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
