import copy
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
from trader1.research.profitability.candidate_scorecard import (
    PERFORMANCE_PASS,
    ROBUSTNESS_PASS,
    candidate_generation_report_hash,
    candidate_generation_report_from_upbit_paper_runtime_cycle,
    candidate_scorecard_from_upbit_paper_runtime_cycle,
    has_required_performance_source_ids,
    has_required_robustness_source_ids,
    performance_inputs_from_runtime_sample_history,
    performance_source_binding_from_source_ids,
    performance_source_evidence_id,
    robustness_source_evidence_id,
    safe_candidate_scorecard_filename,
    source_role_semantics_errors,
    stable_hash,
    strict_robustness_triplet_binding_from_source_ids,
    validate_candidate_generation_report,
    write_upbit_paper_candidate_scorecard,
)
from trader1.research.replay.replay_runner import build_public_replay_robustness_report
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report, upbit_paper_runtime_cycle_hash
from trader1.runtime.portfolio.paper_portfolio import build_paper_portfolio_snapshot_from_fill
from trader1.validation.mvp0_validators import _candidate_scorecard_net_ev_errors


def performance_source_evidence_ids(runtime: dict[str, str], candidate_id: str | None = None) -> list[str]:
    candidate_key = candidate_id or str(runtime["selected_candidate"]["candidate_id"])
    return [
        performance_source_evidence_id("closed_trades", runtime["cycle_id"], runtime["cycle_hash"], candidate_key),
        performance_source_evidence_id("execution_quality", runtime["cycle_id"], runtime["cycle_hash"], candidate_key),
        performance_source_evidence_id("performance_summary", runtime["cycle_id"], runtime["cycle_hash"], candidate_key),
    ]


def _runtime_with_execution_cost_feedback(*, cycle_id: str, adjustment_bps: str = "10") -> dict:
    baseline = build_upbit_paper_runtime_cycle_report(cycle_id=f"{cycle_id}-feedback-target")
    feedback = [
        {
            "source": "PAPER_RUNTIME_EXECUTION_COST_FEEDBACK",
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "symbol": candidate["symbol"],
            "candidate_id": candidate["candidate_id"],
            "strategy_family": candidate["strategy_family"],
            "sample_count": 4,
            "realized_execution_cost_bps": "32",
            "expected_execution_cost_bps": "20",
            "partial_fill_rate": "0",
            "terminal_attempt_rate": "0",
            "adjustment_bps": adjustment_bps,
            "source_runtime_cycle_id": f"{cycle_id}-prior-paper-cost",
            "source_runtime_cycle_hash": "C" * 64,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "order_adapter_called": False,
            "private_endpoint_called": False,
            "credential_load_attempted": False,
            "live_key_loaded": False,
        }
        for candidate in baseline["strategy_candidates"]
    ]
    runtime = build_upbit_paper_runtime_cycle_report(
        cycle_id=cycle_id,
        execution_cost_feedback=feedback,
    )
    assert runtime["selected_candidate"]["execution_cost_feedback_status"] == "ACTIVE"
    return runtime


PASS_PERFORMANCE_METRICS = {
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
}


def _entry_strategy_context(candidate: dict[str, str], cycle_id: str) -> dict[str, str]:
    variation_by_family = {
        "PULLBACK_TREND_LONG": "trailing_tp",
        "VWAP_MEAN_REVERSION": "fixed_tp",
        "BREAKOUT_RETEST_LONG": "invalidation_exit",
    }
    strategy_family = str(candidate["strategy_family"])
    return {
        "entry_strategy_context_status": "BOUND_TO_ENTRY_CANDIDATE",
        "entry_strategy_context_source": "PAPER_RUNTIME_ENTRY_FILL",
        "entry_candidate_id": str(candidate["candidate_id"]),
        "entry_strategy_family": strategy_family,
        "entry_strategy_exit_policy_id": "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1",
        "entry_strategy_exit_variation": variation_by_family[strategy_family],
        "entry_strategy_source_runtime_cycle_id": cycle_id,
        "entry_strategy_source_candidate_hash": "A" * 64,
        "entry_strategy_source_exit_plan_hash": "B" * 64,
        "entry_strategy_context_formula": "bind exit policy to entry strategy at fill time",
    }


def _closed_trade_runtime_for_candidate(*, symbol: str, cycle_id: str) -> dict:
    market_data = build_upbit_public_candle_fixture(
        symbol=symbol,
        session_id="mvp4_upbit_paper_runtime",
        profile="UPTREND_PULLBACK",
    )
    entry_runtime = build_upbit_paper_runtime_cycle_report(
        cycle_id=f"{cycle_id}-entry-context",
        symbol=symbol,
        market_data=market_data,
    )
    candidate = entry_runtime["selected_candidate"]
    mark_price = Decimal(str(market_data["candles"][-1]["close"]))
    entry_price = mark_price * Decimal("1.08")
    current_portfolio = build_paper_portfolio_snapshot_from_fill(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        session_id="mvp4_upbit_paper_runtime",
        symbol=symbol,
        side="BUY",
        quantity="0.01",
        fill_price=str(entry_price),
        mark_price=str(mark_price),
        fee_amount="5",
        starting_cash="1000000",
        source_runtime_cycle_id=f"{cycle_id}-entry-context",
        source_paper_ledger_head_hash="C" * 64,
        entry_strategy_context=_entry_strategy_context(candidate, f"{cycle_id}-entry-context"),
    )
    return build_upbit_paper_runtime_cycle_report(
        cycle_id=cycle_id,
        symbol=symbol,
        market_data=market_data,
        paper_cash_available=current_portfolio["cash_available"],
        paper_equity=current_portfolio["equity"],
        paper_position_market_value=current_portfolio["position_market_value"],
        current_paper_portfolio_snapshot=current_portfolio,
    )


def _no_trade_runtime_for_candidate(*, symbol: str, cycle_id: str, profile: str) -> dict:
    return build_upbit_paper_runtime_cycle_report(
        cycle_id=cycle_id,
        symbol=symbol,
        market_data=build_upbit_public_candle_fixture(
            symbol=symbol,
            session_id="mvp4_upbit_paper_runtime",
            profile=profile,
        ),
    )


class CandidateScorecardFromRuntimeTest(unittest.TestCase):
    def test_runtime_cycle_builds_non_live_scorecard_with_robustness_blockers(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-positive")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertEqual(scorecard["schema_id"], "trader1.candidate_scorecard.v1")
        self.assertEqual(scorecard["candidate_id"], runtime["selected_candidate"]["candidate_id"])
        self.assertEqual(scorecard["source_runtime_cycle_id"], runtime["cycle_id"])
        self.assertEqual(scorecard["source_runtime_cycle_hash"], runtime["cycle_hash"])
        self.assertIn(
            f"upbit_paper_runtime_cycle:{runtime['cycle_id']}:{runtime['cycle_hash']}",
            scorecard["source_evidence_ids"],
        )
        self.assertEqual(scorecard["objective_basis"], "NET_EV_AFTER_COST")
        self.assertEqual(scorecard["mode"], "PAPER")
        self.assertEqual(scorecard["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn("OOS_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})
        self.assertIn("WALK_FORWARD_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})
        self.assertFalse(scorecard["live_order_ready"])
        self.assertFalse(scorecard["live_order_allowed"])
        self.assertFalse(scorecard["can_live_trade"])
        self.assertFalse(scorecard["scale_up_allowed"])

    def test_no_trade_runtime_builds_blocked_research_scorecard_without_fill_or_live_permission(self):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-runtime-negative",
            edge_profile="NEGATIVE",
        )

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn("MIN_EDGE_FAIL", {blocker["code"] for blocker in scorecard["blockers"]})
        self.assertLess(scorecard["net_ev_after_cost_bps"], scorecard["min_required_edge_bps"])
        self.assertFalse(scorecard["live_order_allowed"])

    def test_managed_position_no_trade_scores_best_same_cycle_entry_opportunity(self):
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
        for candle in strong_eth["candles"]:
            candle["volume"] = "5"
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
            source_runtime_cycle_id="previous-scorecard-managed-position",
            source_paper_ledger_head_hash="C" * 64,
        )
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-runtime-managed-position-shadow-entry",
            symbol="KRW-BTC",
            market_data_universe=[weak_btc, strong_eth],
            paper_cash_available=current_portfolio["cash_available"],
            paper_equity=current_portfolio["equity"],
            paper_position_market_value=current_portfolio["position_market_value"],
            current_paper_portfolio_snapshot=current_portfolio,
        )

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertEqual(runtime["selected_candidate"]["decision"], "NO_TRADE")
        self.assertEqual(scorecard["candidate_id"], "KRW-ETH-pullback-trend-long")
        self.assertEqual(scorecard["symbol"], "KRW-ETH")
        self.assertGreater(scorecard["net_ev_after_cost_bps"], scorecard["min_required_edge_bps"])
        self.assertIn(
            f"upbit_paper_runtime_cycle:{runtime['cycle_id']}:{runtime['cycle_hash']}",
            scorecard["source_evidence_ids"],
        )
        self.assertFalse(scorecard["live_order_ready"])
        self.assertFalse(scorecard["live_order_allowed"])
        self.assertFalse(scorecard["can_live_trade"])
        self.assertFalse(scorecard["scale_up_allowed"])

    def test_managed_position_scope_focus_scores_requested_candidate_without_live_permission(self):
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
            source_runtime_cycle_id="previous-scorecard-managed-scope-focus",
            source_paper_ledger_head_hash="D" * 64,
        )
        focus_candidate_id = "KRW-ORCA-pullback-trend-long"
        focus_parameter_hash = stable_hash(f"{focus_candidate_id}:PULLBACK_TREND_LONG:KRW-ORCA")
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-runtime-managed-position-scope-focus",
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
        focus_candidate = next(
            candidate for candidate in runtime["strategy_candidates"] if candidate["candidate_id"] == focus_candidate_id
        )
        best_entry_candidate = max(
            (
                candidate
                for candidate in runtime["strategy_candidates"]
                if candidate["decision"] == "PAPER_ENTRY_REVIEW"
            ),
            key=lambda candidate: float(candidate["candidate_selection_score"]),
        )

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)

        self.assertEqual(runtime["paper_scope_continuity_decision"]["selection_status"], "MANAGED_POSITION_OVERRIDES_SCOPE_FOCUS")
        self.assertEqual(focus_candidate["decision"], "PAPER_ENTRY_REVIEW")
        self.assertNotEqual(best_entry_candidate["candidate_id"], focus_candidate_id)
        self.assertEqual(scorecard["candidate_id"], focus_candidate_id)
        self.assertEqual(scorecard["symbol"], "KRW-ORCA")
        self.assertEqual(scorecard["parameter_hash"], focus_parameter_hash)
        self.assertFalse(scorecard["live_order_ready"])
        self.assertFalse(scorecard["live_order_allowed"])
        self.assertFalse(scorecard["can_live_trade"])
        self.assertFalse(scorecard["scale_up_allowed"])

    def test_requested_scope_candidate_no_trade_scores_fail_closed_without_promotion(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-scope-no-trade-binding")
        focus_candidate = next(
            candidate
            for candidate in runtime["strategy_candidates"]
            if candidate["decision"] == "NO_TRADE"
            and candidate["live_order_ready"] is False
            and candidate["live_order_allowed"] is False
            and candidate["can_live_trade"] is False
            and candidate["scale_up_allowed"] is False
        )

        with self.assertRaises(ValueError):
            candidate_scorecard_from_upbit_paper_runtime_cycle(
                runtime,
                candidate_id=focus_candidate["candidate_id"],
            )

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            candidate_id=focus_candidate["candidate_id"],
            allow_non_entry_review_candidate=True,
        )

        self.assertEqual(scorecard["candidate_id"], focus_candidate["candidate_id"])
        self.assertEqual(scorecard["symbol"], focus_candidate["symbol"])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn(focus_candidate["no_trade_reason"], {blocker["code"] for blocker in scorecard["blockers"]})
        self.assertFalse(scorecard["live_order_ready"])
        self.assertFalse(scorecard["live_order_allowed"])
        self.assertFalse(scorecard["can_live_trade"])
        self.assertFalse(scorecard["scale_up_allowed"])

    def test_multisymbol_runtime_persists_rotation_context_without_live_permission(self):
        market_data_universe = [
            build_upbit_public_candle_fixture(
                symbol=symbol,
                session_id="mvp4_upbit_paper_runtime",
                profile="UPTREND_PULLBACK",
            )
            for symbol in ("KRW-BTC", "KRW-ETH")
        ]
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-runtime-multisymbol-rotation-context",
            session_id="mvp4_upbit_paper_runtime",
            market_data_universe=market_data_universe,
        )

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertEqual(scorecard["evaluated_symbol_count"], 2)
        self.assertEqual(scorecard["paper_entry_review_symbol_count"], 1)
        self.assertEqual(len(scorecard["top_symbol_evidence_scorecards"]), 2)
        self.assertEqual(scorecard["alternative_candidate_count"], 0)
        self.assertIsNone(scorecard["best_alternative_candidate_id"])
        self.assertIsNone(scorecard["best_alternative_symbol"])
        self.assertIsNone(scorecard["best_alternative_net_ev_after_cost_bps"])
        self.assertFalse(scorecard["rotation_review_required"])
        self.assertEqual(scorecard["rotation_review_reason_code"], "NONE")
        top_by_symbol = {item["symbol"]: item for item in scorecard["top_symbol_evidence_scorecards"]}
        self.assertEqual(top_by_symbol["KRW-BTC"]["correlation_cluster_status"], "LEADER")
        self.assertEqual(top_by_symbol["KRW-ETH"]["correlation_cluster_status"], "DIVERSIFICATION_FILTERED")
        self.assertIn("CLUSTER_RISK", top_by_symbol["KRW-ETH"]["no_trade_reasons"])
        for symbol_scorecard in scorecard["top_symbol_evidence_scorecards"]:
            self.assertFalse(symbol_scorecard["live_order_ready"])
            self.assertFalse(symbol_scorecard["live_order_allowed"])
            self.assertFalse(symbol_scorecard["can_live_trade"])
            self.assertFalse(symbol_scorecard["scale_up_allowed"])
        self.assertFalse(scorecard["live_order_allowed"])

    def test_scorecard_records_all_runtime_strategy_family_evidence_without_live_permission(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-family-coverage")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        family_rows = {row["strategy_family"]: row for row in scorecard["strategy_family_evidence_scorecards"]}
        self.assertEqual(
            set(family_rows),
            {"PULLBACK_TREND_LONG", "VWAP_MEAN_REVERSION", "BREAKOUT_RETEST_LONG"},
        )
        self.assertEqual(len(scorecard["top_symbol_evidence_scorecards"]), 1)
        for row in family_rows.values():
            self.assertEqual(row["evaluated_candidate_count"], 1)
            self.assertTrue(row["strategy_id"])
            self.assertFalse(row["live_order_ready"])
            self.assertFalse(row["live_order_allowed"])
            self.assertFalse(row["can_live_trade"])
            self.assertFalse(row["scale_up_allowed"])

    def test_robustness_pass_requires_source_evidence_before_paper_ranking(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-robust-no-source")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn("ROBUSTNESS_TRIPLET_MISMATCH", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_public_replay_failed_robustness_blocks_as_failed_not_missing(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-public-replay-fail")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses={
                "oos_status": "FAIL",
                "walk_forward_status": "FAIL",
                "bootstrap_status": "FAIL",
                "overfit_status": "HIGH",
            },
            robustness_source_evidence_ids=[
                "public_replay_robustness:replay-scorecard-runtime-public-replay-fail:" + "A" * 64,
                "public_market_data:KRW-BTC:" + "B" * 64,
            ],
        )
        blocker_codes = {blocker["code"] for blocker in scorecard["blockers"]}

        self.assertEqual(_candidate_scorecard_net_ev_errors(scorecard), [])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertFalse(scorecard["rotation_review_required"])
        self.assertEqual(scorecard["rotation_review_reason_code"], "NONE")
        self.assertIn("PUBLIC_REPLAY_ROBUSTNESS_FAILED", blocker_codes)
        self.assertIn("OOS_FAILED", blocker_codes)
        self.assertIn("WALK_FORWARD_FAILED", blocker_codes)
        self.assertIn("BOOTSTRAP_FAILED", blocker_codes)
        self.assertNotIn("OOS_MISSING", blocker_codes)
        self.assertNotIn("WALK_FORWARD_MISSING", blocker_codes)
        self.assertTrue(
            any(source_id.startswith("public_replay_robustness:") for source_id in scorecard["source_evidence_ids"])
        )
        self.assertFalse(scorecard["live_order_allowed"])

    def test_candidate_generation_report_retreats_failed_candidate_without_live_permission(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-candidate-generation-no-alt")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses={
                "oos_status": "FAIL",
                "walk_forward_status": "FAIL",
                "bootstrap_status": "FAIL",
                "overfit_status": "HIGH",
            },
            robustness_source_evidence_ids=[
                "public_replay_robustness:replay-scorecard-runtime-candidate-generation-no-alt:" + "A" * 64,
                "public_market_data:KRW-BTC:" + "B" * 64,
            ],
        )

        report = candidate_generation_report_from_upbit_paper_runtime_cycle(runtime, candidate_scorecard=scorecard)
        validation_status, validation_message, blocker_code = validate_candidate_generation_report(
            report,
            candidate_scorecard=scorecard,
        )
        item_by_id = {item["candidate_id"]: item for item in report["candidate_items"]}

        self.assertEqual(validation_status, "PASS", validation_message)
        self.assertEqual(blocker_code, None)
        self.assertEqual(report["generation_status"], "NO_ALTERNATIVE_READY")
        self.assertEqual(report["status"], "BLOCKED")
        self.assertTrue(report["selected_candidate_retired_for_ranking"])
        self.assertEqual(item_by_id[scorecard["candidate_id"]]["candidate_status"], "RETIRED_FAILED_SOURCE")
        self.assertEqual(report["alternative_candidate_count"], 0)
        self.assertIsNone(report["best_alternative_candidate_id"])
        self.assertIn("bounded public discovery", report["next_action"])
        self.assertEqual(item_by_id[scorecard["candidate_id"]]["candidate_source_role"], "CURRENT_RUNTIME_CYCLE")
        self.assertEqual(item_by_id[scorecard["candidate_id"]]["source_runtime_cycle_id"], runtime["cycle_id"])
        self.assertEqual(item_by_id[scorecard["candidate_id"]]["source_runtime_cycle_hash"], runtime["cycle_hash"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(report["private_endpoint_called"])
        self.assertFalse(report["order_adapter_called"])

        missing_source_role = copy.deepcopy(report)
        missing_source_role["candidate_items"][0].pop("candidate_source_role")
        missing_source_role["generation_hash"] = candidate_generation_report_hash(missing_source_role)
        validation_status, validation_message, blocker_code = validate_candidate_generation_report(
            missing_source_role,
            candidate_scorecard=scorecard,
        )
        self.assertEqual(validation_status, "FAIL")
        self.assertEqual(blocker_code, "SCHEMA_IDENTITY_MISMATCH")
        self.assertIn("missing source", validation_message)

        missing_source_evidence = copy.deepcopy(report)
        missing_source_evidence["source_evidence_ids"] = [
            source_id
            for source_id in missing_source_evidence["source_evidence_ids"]
            if not source_id.startswith("upbit_paper_runtime_cycle:")
        ]
        missing_source_evidence["generation_hash"] = candidate_generation_report_hash(missing_source_evidence)
        validation_status, validation_message, blocker_code = validate_candidate_generation_report(
            missing_source_evidence,
            candidate_scorecard=scorecard,
        )
        self.assertEqual(validation_status, "FAIL")
        self.assertEqual(blocker_code, "SCHEMA_IDENTITY_MISMATCH")
        self.assertIn("source binding", validation_message)

    def test_candidate_generation_report_selects_different_entry_review_alternative(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-candidate-generation-alt")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses={
                "oos_status": "FAIL",
                "walk_forward_status": "FAIL",
                "bootstrap_status": "FAIL",
                "overfit_status": "HIGH",
            },
            robustness_source_evidence_ids=[
                "public_replay_robustness:replay-scorecard-runtime-candidate-generation-alt:" + "A" * 64,
                "public_market_data:KRW-BTC:" + "B" * 64,
            ],
        )
        selected = runtime["selected_candidate"]
        alternative = copy.deepcopy(selected)
        alternative["candidate_id"] = "KRW-ETH-pullback-trend-long"
        alternative["symbol"] = "KRW-ETH"
        alternative["candidate_selection_score"] = max(0.01, float(selected["candidate_selection_score"]) - 0.01)
        alternative["net_ev_after_cost_bps"] = float(selected["net_ev_after_cost_bps"]) + 5.0
        runtime["strategy_candidates"].append(alternative)

        report = candidate_generation_report_from_upbit_paper_runtime_cycle(runtime, candidate_scorecard=scorecard)
        validation_status, validation_message, blocker_code = validate_candidate_generation_report(
            report,
            candidate_scorecard=scorecard,
        )

        self.assertEqual(validation_status, "PASS", validation_message)
        self.assertEqual(blocker_code, None)
        self.assertEqual(report["generation_status"], "ALTERNATIVE_REVIEW_READY")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["best_alternative_candidate_id"], "KRW-ETH-pullback-trend-long")
        self.assertEqual(report["best_alternative_symbol"], "KRW-ETH")
        self.assertEqual(report["alternative_candidate_count"], 1)
        self.assertTrue(report["selected_candidate_retired_for_ranking"])
        best_item = next(item for item in report["candidate_items"] if item["candidate_id"] == "KRW-ETH-pullback-trend-long")
        self.assertEqual(best_item["candidate_source_role"], "CURRENT_RUNTIME_CYCLE")
        self.assertIn("bounded public replay robustness", report["next_action"])
        self.assertFalse(report["live_order_allowed"])

    def test_candidate_generation_report_can_prefer_replay_reviewed_alternative(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-candidate-generation-preferred-alt")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses={
                "oos_status": "FAIL",
                "walk_forward_status": "FAIL",
                "bootstrap_status": "FAIL",
                "overfit_status": "HIGH",
            },
            robustness_source_evidence_ids=[
                "public_replay_robustness:replay-scorecard-runtime-candidate-generation-preferred-alt:" + "A" * 64,
                "public_market_data:KRW-BTC:" + "B" * 64,
            ],
        )
        selected = runtime["selected_candidate"]
        high_raw_ev = copy.deepcopy(selected)
        high_raw_ev["candidate_id"] = "KRW-ETH-pullback-trend-long"
        high_raw_ev["symbol"] = "KRW-ETH"
        high_raw_ev["candidate_selection_score"] = max(0.01, float(selected["candidate_selection_score"]) - 0.01)
        high_raw_ev["net_ev_after_cost_bps"] = float(selected["net_ev_after_cost_bps"]) + 9.0
        preferred = copy.deepcopy(selected)
        preferred["candidate_id"] = "KRW-XRP-pullback-trend-long"
        preferred["symbol"] = "KRW-XRP"
        preferred["candidate_selection_score"] = max(0.01, float(selected["candidate_selection_score"]) - 0.02)
        preferred["net_ev_after_cost_bps"] = float(selected["net_ev_after_cost_bps"]) + 2.0
        runtime["strategy_candidates"].extend([high_raw_ev, preferred])

        report = candidate_generation_report_from_upbit_paper_runtime_cycle(
            runtime,
            candidate_scorecard=scorecard,
            preferred_alternative_candidate_id="KRW-XRP-pullback-trend-long",
        )
        validation_status, validation_message, blocker_code = validate_candidate_generation_report(
            report,
            candidate_scorecard=scorecard,
        )

        self.assertEqual(validation_status, "PASS", validation_message)
        self.assertEqual(blocker_code, None)
        self.assertEqual(report["generation_status"], "ALTERNATIVE_REVIEW_READY")
        self.assertEqual(report["best_alternative_candidate_id"], "KRW-XRP-pullback-trend-long")
        self.assertEqual(report["best_alternative_symbol"], "KRW-XRP")
        self.assertEqual(report["alternative_candidate_count"], 2)
        self.assertFalse(report["live_order_allowed"])

    def test_scorecard_can_target_same_runtime_alternative_candidate(self):
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
            source_runtime_cycle_id="previous-scorecard-target-alt",
            source_paper_ledger_head_hash="D" * 64,
        )
        focus_candidate_id = "KRW-ORCA-pullback-trend-long"
        focus_parameter_hash = stable_hash(f"{focus_candidate_id}:PULLBACK_TREND_LONG:KRW-ORCA")
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-runtime-target-alt",
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
        focused_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        target_candidate = max(
            (
                candidate
                for candidate in runtime["strategy_candidates"]
                if candidate["decision"] == "PAPER_ENTRY_REVIEW"
                and candidate["candidate_id"] != focused_scorecard["candidate_id"]
            ),
            key=lambda candidate: float(candidate["candidate_selection_score"]),
        )

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            candidate_id=target_candidate["candidate_id"],
        )

        self.assertEqual(scorecard["candidate_id"], target_candidate["candidate_id"])
        self.assertEqual(scorecard["symbol"], target_candidate["symbol"])
        self.assertEqual(scorecard["source_runtime_cycle_id"], runtime["cycle_id"])
        self.assertEqual(scorecard["source_runtime_cycle_hash"], runtime["cycle_hash"])
        self.assertFalse(scorecard["live_order_allowed"])

    def test_candidate_generation_report_uses_bounded_public_discovery_runtime_alternative(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-candidate-generation-discovery-base")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses={
                "oos_status": "FAIL",
                "walk_forward_status": "FAIL",
                "bootstrap_status": "FAIL",
                "overfit_status": "HIGH",
            },
            robustness_source_evidence_ids=[
                "public_replay_robustness:replay-scorecard-runtime-candidate-generation-discovery-base:" + "A" * 64,
                "public_market_data:KRW-BTC:" + "B" * 64,
            ],
        )
        discovery_runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-runtime-candidate-generation-discovery-alt",
            market_data=build_upbit_public_candle_fixture(
                symbol="KRW-ETH",
                session_id="mvp4_upbit_paper_runtime",
                profile="UPTREND_PULLBACK",
            ),
            symbol="KRW-ETH",
        )

        report = candidate_generation_report_from_upbit_paper_runtime_cycle(
            runtime,
            candidate_scorecard=scorecard,
            additional_runtime_cycle_reports=[discovery_runtime],
        )
        validation_status, validation_message, blocker_code = validate_candidate_generation_report(
            report,
            candidate_scorecard=scorecard,
        )
        best_item = next(item for item in report["candidate_items"] if item["candidate_id"] == "KRW-ETH-pullback-trend-long")

        self.assertEqual(validation_status, "PASS", validation_message)
        self.assertEqual(blocker_code, None)
        self.assertEqual(report["generation_status"], "ALTERNATIVE_REVIEW_READY")
        self.assertEqual(report["best_alternative_candidate_id"], "KRW-ETH-pullback-trend-long")
        self.assertEqual(best_item["candidate_source_role"], "BOUNDED_PUBLIC_DISCOVERY_RUNTIME")
        self.assertEqual(best_item["source_runtime_cycle_id"], discovery_runtime["cycle_id"])
        self.assertEqual(best_item["source_runtime_cycle_hash"], discovery_runtime["cycle_hash"])
        self.assertTrue(
            any(
                source_id == f"upbit_paper_runtime_cycle:{discovery_runtime['cycle_id']}:{discovery_runtime['cycle_hash']}"
                for source_id in report["source_evidence_ids"]
            )
        )
        self.assertFalse(report["live_order_allowed"])

    def test_candidate_generation_report_blocks_public_replay_without_closed_trade_profitability(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-candidate-generation-replay-base")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses={
                "oos_status": "FAIL",
                "walk_forward_status": "FAIL",
                "bootstrap_status": "FAIL",
                "overfit_status": "HIGH",
            },
            robustness_source_evidence_ids=[
                "public_replay_robustness:replay-scorecard-runtime-candidate-generation-replay-base:" + "A" * 64,
                "public_market_data:KRW-BTC:" + "B" * 64,
            ],
        )
        discovery_market_data = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        discovery_runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-runtime-candidate-generation-replay-alt",
            market_data=discovery_market_data,
            symbol="KRW-ETH",
        )
        alternative_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(discovery_runtime)
        replay_report = build_public_replay_robustness_report(
            candidate_scorecard=alternative_scorecard,
            market_data=discovery_market_data,
            replay_id="public-replay-alt-binding",
            max_replay_windows=10,
            min_required_sample_count=1,
        )

        report = candidate_generation_report_from_upbit_paper_runtime_cycle(
            runtime,
            candidate_scorecard=scorecard,
            additional_runtime_cycle_reports=[discovery_runtime],
            best_alternative_public_replay_report=replay_report,
        )
        validation_status, validation_message, blocker_code = validate_candidate_generation_report(
            report,
            candidate_scorecard=scorecard,
        )

        self.assertEqual(validation_status, "PASS", validation_message)
        self.assertEqual(blocker_code, None)
        self.assertEqual(report["generation_status"], "ALTERNATIVE_PUBLIC_REPLAY_BLOCKED")
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "REPLAY_CLOSED_TRADES_MISSING")
        self.assertIn("REPLAY_CLOSED_TRADES_MISSING", {blocker["code"] for blocker in report["blockers"]})
        self.assertEqual(report["best_alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(report["best_alternative_public_replay_sample_count"], replay_report["sample_count"])
        self.assertEqual(report["best_alternative_public_replay_closed_trade_sample_count"], 0)
        self.assertTrue(
            any(
                source_id.startswith(f"public_replay_robustness:{replay_report['replay_id']}:")
                for source_id in report["source_evidence_ids"]
            )
        )
        self.assertIn("Run bounded public replay robustness", report["next_action"])
        self.assertFalse(report["live_order_allowed"])

    def test_robustness_source_evidence_must_cover_required_kinds(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-robust-partial-source")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                "paper:missing-bootstrap-source",
            ],
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(has_required_robustness_source_ids(scorecard["source_evidence_ids"]))
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertIn("ROBUSTNESS_TRIPLET_MISMATCH", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_robustness_evidence_must_match_runtime_cycle_hash(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-robust-mismatch")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], "B" * 64),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIsNone(
            strict_robustness_triplet_binding_from_source_ids(
                scorecard["source_evidence_ids"],
                cycle_id=runtime["cycle_id"],
                cycle_hash=runtime["cycle_hash"],
            )
        )
        self.assertIn("ROBUSTNESS_TRIPLET_MISMATCH", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_robustness_evidence_triplet_rejects_cross_cycle_mix(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-robust-cross-cycle")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", "other-cycle", runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIsNone(
            strict_robustness_triplet_binding_from_source_ids(
                scorecard["source_evidence_ids"],
                cycle_id=runtime["cycle_id"],
                cycle_hash=runtime["cycle_hash"],
            )
        )
        self.assertIn("ROBUSTNESS_TRIPLET_MISMATCH", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_source_role_semantics_rejects_malformed_known_prefixes(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-source-role-format")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                "oos:",
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertTrue(source_role_semantics_errors(["oos:"]))
        self.assertFalse(scorecard["ranking_eligible"])
        blocker_codes = {blocker["code"] for blocker in scorecard["blockers"]}
        self.assertIn("SOURCE_ROLE_SEMANTICS_MISMATCH", blocker_codes)
        self.assertIn("ROBUSTNESS_TRIPLET_MISMATCH", blocker_codes)

    def test_robustness_pass_still_blocks_without_closed_trade_performance(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-robust-no-performance")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["performance_ready"])
        self.assertFalse(scorecard["ranking_eligible"])
        blocker_codes = {blocker["code"] for blocker in scorecard["blockers"]}
        self.assertIn("SAMPLE_INSUFFICIENT", blocker_codes)
        self.assertIn("EXECUTION_QUALITY_UNTESTED", blocker_codes)

    def test_raw_expected_edge_cannot_rank_when_realized_edge_after_cost_fails(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-raw-pnl-trap")
        weak_performance = dict(PASS_PERFORMANCE_METRICS)
        weak_performance["realized_vs_expected_edge_bps"] = -6.0

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
            performance_statuses={**PERFORMANCE_PASS, "realized_vs_expected_edge_status": "FAIL"},
            performance_metrics=weak_performance,
            performance_source_evidence_ids=performance_source_evidence_ids(runtime),
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn("EXECUTION_FEEDBACK_DIVERGENT", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_execution_cost_divergence_blocks_paper_ranking(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-cost-divergence")
        weak_performance = dict(PASS_PERFORMANCE_METRICS)
        weak_performance["execution_cost_delta_bps"] = 5.0
        weak_performance["max_allowed_execution_cost_delta_bps"] = 2.0

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
            performance_statuses={**PERFORMANCE_PASS, "execution_cost_comparison_status": "FAIL"},
            performance_metrics=weak_performance,
            performance_source_evidence_ids=performance_source_evidence_ids(runtime),
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["performance_ready"])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["execution_cost_comparison_status"], "FAIL")
        self.assertIn("EXECUTION_FEEDBACK_DIVERGENT", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_runtime_execution_cost_feedback_blocks_paper_ranking_even_with_pass_metrics(self):
        runtime = _runtime_with_execution_cost_feedback(cycle_id="scorecard-runtime-active-cost-feedback")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
            performance_statuses=PERFORMANCE_PASS,
            performance_metrics=PASS_PERFORMANCE_METRICS,
            performance_source_evidence_ids=performance_source_evidence_ids(runtime),
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertEqual(scorecard["runtime_execution_cost_feedback_status"], "ACTIVE")
        self.assertEqual(scorecard["runtime_execution_cost_feedback_binding_status"], "FAIL")
        self.assertEqual(scorecard["runtime_execution_cost_feedback_blocker_code"], "EXECUTION_FEEDBACK_DIVERGENT")
        self.assertEqual(scorecard["execution_cost_comparison_status"], "FAIL")
        self.assertGreater(scorecard["runtime_execution_cost_feedback_delta_bps"], scorecard["max_allowed_execution_cost_delta_bps"])
        self.assertFalse(scorecard["performance_ready"])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertFalse(scorecard["live_order_allowed"])
        self.assertFalse(scorecard["can_live_trade"])
        self.assertFalse(scorecard["scale_up_allowed"])
        self.assertIn("EXECUTION_FEEDBACK_DIVERGENT", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_generic_performance_sources_cannot_make_scorecard_rank(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-generic-performance-source")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
            performance_statuses=PERFORMANCE_PASS,
            performance_metrics=PASS_PERFORMANCE_METRICS,
            performance_source_evidence_ids=[
                f"closed_trades:{runtime['cycle_id']}:{runtime['cycle_hash']}",
                f"execution_quality:{runtime['cycle_id']}:{runtime['cycle_hash']}",
                f"performance_summary:{runtime['cycle_id']}:{runtime['cycle_hash']}",
            ],
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn("EXECUTION_FEEDBACK_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_performance_sources_must_share_one_history_binding_before_paper_ranking(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-performance-binding-mismatch")
        candidate_id = str(runtime["selected_candidate"]["candidate_id"])

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
            performance_statuses=PERFORMANCE_PASS,
            performance_metrics=PASS_PERFORMANCE_METRICS,
            performance_source_evidence_ids=[
                performance_source_evidence_id("closed_trades", "history-a", "A" * 64, candidate_id),
                performance_source_evidence_id("execution_quality", "history-a", "A" * 64, candidate_id),
                performance_source_evidence_id("performance_summary", "history-b", "B" * 64, candidate_id),
            ],
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertIsNone(
            performance_source_binding_from_source_ids(scorecard["source_evidence_ids"], candidate_id=candidate_id)
        )
        self.assertFalse(has_required_performance_source_ids(scorecard["source_evidence_ids"], candidate_id=candidate_id))
        self.assertEqual(scorecard["performance_source_binding_status"], "MISSING_OR_MISMATCHED")
        self.assertIsNone(scorecard["performance_source_history_id"])
        self.assertIsNone(scorecard["performance_source_history_hash"])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn("EXECUTION_FEEDBACK_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_robust_paper_scorecard_can_be_paper_ranking_input_only(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-robust")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
            performance_statuses=PERFORMANCE_PASS,
            performance_metrics=PASS_PERFORMANCE_METRICS,
            performance_source_evidence_ids=performance_source_evidence_ids(runtime),
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertTrue(has_required_performance_source_ids(scorecard["source_evidence_ids"]))
        self.assertEqual(scorecard["performance_source_binding_status"], "PASS")
        self.assertEqual(scorecard["performance_source_history_id"], runtime["cycle_id"])
        self.assertEqual(scorecard["performance_source_history_hash"], runtime["cycle_hash"])
        self.assertTrue(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["scorecard_scope"], "PAPER_SCORECARD_INPUT_ONLY")
        self.assertEqual(scorecard["blockers"], [])
        self.assertEqual(scorecard["live_readiness_status"], "NOT_LIVE_READY")
        self.assertFalse(scorecard["live_order_allowed"])

    def test_runtime_performance_inputs_are_candidate_scoped(self):
        target_entry_runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-performance-target-entry",
            symbol="KRW-BTC",
        )
        target_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(target_entry_runtime)
        target_runtime = _closed_trade_runtime_for_candidate(
            symbol="KRW-BTC",
            cycle_id="scorecard-performance-target-exit",
        )
        unrelated_runtime = _closed_trade_runtime_for_candidate(
            symbol="KRW-ETH",
            cycle_id="scorecard-performance-unrelated-exit",
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_dir = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp4_upbit_paper_runtime"
            runtime_dir.mkdir(parents=True)
            samples = []
            for runtime in (target_runtime, unrelated_runtime):
                runtime_path = runtime_dir / f"{runtime['cycle_id']}.runtime_cycle.json"
                runtime_path.write_text(json.dumps(runtime, sort_keys=True), encoding="utf-8")
                samples.append(
                    {
                        "source_runtime_cycle_path": runtime_path.relative_to(root).as_posix(),
                        "source_runtime_cycle_hash": runtime["cycle_hash"],
                    }
                )
            history = {
                "history_id": "candidate-scoped-performance-history",
                "history_hash": "D" * 64,
                "samples": samples,
            }

            statuses, metrics, source_ids = performance_inputs_from_runtime_sample_history(
                candidate_scorecard=target_scorecard,
                runtime_sample_history=history,
                root=root,
            )

        target_key = safe_candidate_scorecard_filename(target_scorecard["candidate_id"])
        self.assertEqual(target_runtime["final_decision"], "EXIT_POSITION")
        self.assertEqual(unrelated_runtime["final_decision"], "EXIT_POSITION")
        self.assertIsNotNone(target_runtime["position_management_decision"]["managed_position_cost_basis"])
        self.assertEqual(metrics["closed_trade_sample_count"], 1)
        self.assertEqual(metrics["strategy_exit_policy_sample_count"], 1)
        self.assertEqual(metrics["strategy_exit_policy_match_count"], 1)
        self.assertEqual(metrics["strategy_exit_policy_mismatch_count"], 0)
        self.assertEqual(metrics["strategy_exit_reason_count"], 1)
        self.assertGreaterEqual(len(metrics["strategy_exit_reason_counts"]), 1)
        self.assertEqual(metrics["realized_vs_expected_sample_count"], 1)
        self.assertEqual(statuses["strategy_exit_policy_status"], "FAIL")
        self.assertEqual(statuses["closed_trade_status"], "FAIL")
        self.assertEqual(statuses["profit_factor_status"], "FAIL")
        self.assertEqual(statuses["realized_vs_expected_edge_status"], "FAIL")
        self.assertGreater(metrics["fill_quality_score"], 0)
        self.assertEqual(metrics["fill_quality_sample_count"], 1)
        self.assertEqual(metrics["execution_cost_sample_count"], 1)
        self.assertIn(statuses["execution_cost_comparison_status"], {"PASS", "FAIL"})
        self.assertGreaterEqual(metrics["realized_fee_bps"], 0)
        self.assertGreater(metrics["realized_slippage_bps"], 0)
        self.assertGreaterEqual(metrics["expected_total_execution_cost_bps"], metrics["realized_fee_bps"])
        self.assertLessEqual(metrics["execution_cost_delta_bps"], metrics["max_allowed_execution_cost_delta_bps"])
        self.assertTrue(all(f":{target_key}:" in source_id for source_id in source_ids))

    def test_runtime_performance_closed_trade_pnl_is_order_invariant_for_candidate_scope(self):
        target_entry_runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-performance-order-target-entry",
            symbol="KRW-BTC",
        )
        target_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(target_entry_runtime)
        target_runtime = _closed_trade_runtime_for_candidate(
            symbol="KRW-BTC",
            cycle_id="scorecard-performance-order-target-exit",
        )
        unrelated_runtime = _closed_trade_runtime_for_candidate(
            symbol="KRW-ETH",
            cycle_id="scorecard-performance-order-unrelated-exit",
        )

        def metrics_for_order(runtimes: list[dict]) -> dict[str, float]:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                runtime_dir = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp4_upbit_paper_runtime"
                runtime_dir.mkdir(parents=True)
                samples = []
                for runtime in runtimes:
                    runtime_path = runtime_dir / f"{runtime['cycle_id']}.runtime_cycle.json"
                    runtime_path.write_text(json.dumps(runtime, sort_keys=True), encoding="utf-8")
                    samples.append(
                        {
                            "source_runtime_cycle_path": runtime_path.relative_to(root).as_posix(),
                            "source_runtime_cycle_hash": runtime["cycle_hash"],
                        }
                    )
                _statuses, metrics, _source_ids = performance_inputs_from_runtime_sample_history(
                    candidate_scorecard=target_scorecard,
                    runtime_sample_history={
                        "history_id": "candidate-order-invariance-history",
                        "history_hash": "F" * 64,
                        "samples": samples,
                    },
                    root=root,
                )
                return metrics

        target_only_metrics = metrics_for_order([target_runtime])
        unrelated_first_metrics = metrics_for_order([unrelated_runtime, target_runtime])
        target_first_metrics = metrics_for_order([target_runtime, unrelated_runtime])

        self.assertEqual(unrelated_first_metrics["closed_trade_sample_count"], 1)
        self.assertEqual(target_first_metrics["closed_trade_sample_count"], 1)
        self.assertAlmostEqual(
            unrelated_first_metrics["realized_vs_expected_edge_bps"],
            target_only_metrics["realized_vs_expected_edge_bps"],
        )
        self.assertAlmostEqual(
            target_first_metrics["realized_vs_expected_edge_bps"],
            target_only_metrics["realized_vs_expected_edge_bps"],
        )
        self.assertAlmostEqual(unrelated_first_metrics["max_drawdown_pct"], target_only_metrics["max_drawdown_pct"])
        self.assertAlmostEqual(target_first_metrics["max_drawdown_pct"], target_only_metrics["max_drawdown_pct"])

    def test_runtime_performance_unscoped_legacy_closed_trade_does_not_claim_pnl(self):
        target_entry_runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-performance-unscoped-target-entry",
            symbol="KRW-BTC",
        )
        target_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(target_entry_runtime)
        target_runtime = _closed_trade_runtime_for_candidate(
            symbol="KRW-BTC",
            cycle_id="scorecard-performance-unscoped-target-exit",
        )
        target_runtime["position_management_decision"].pop("managed_position_quantity", None)
        target_runtime["position_management_decision"].pop("managed_position_cost_basis", None)
        target_runtime["cycle_hash"] = upbit_paper_runtime_cycle_hash(target_runtime)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_dir = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp4_upbit_paper_runtime"
            runtime_dir.mkdir(parents=True)
            runtime_path = runtime_dir / f"{target_runtime['cycle_id']}.runtime_cycle.json"
            runtime_path.write_text(json.dumps(target_runtime, sort_keys=True), encoding="utf-8")
            statuses, metrics, source_ids = performance_inputs_from_runtime_sample_history(
                candidate_scorecard=target_scorecard,
                runtime_sample_history={
                    "history_id": "candidate-unscoped-legacy-history",
                    "history_hash": "C" * 64,
                    "samples": [
                        {
                            "source_runtime_cycle_path": runtime_path.relative_to(root).as_posix(),
                            "source_runtime_cycle_hash": target_runtime["cycle_hash"],
                        }
                    ],
                },
                root=root,
            )

        target_key = safe_candidate_scorecard_filename(target_scorecard["candidate_id"])
        self.assertEqual(metrics["closed_trade_sample_count"], 0)
        self.assertEqual(metrics["realized_vs_expected_sample_count"], 0)
        self.assertEqual(metrics["strategy_exit_policy_sample_count"], 1)
        self.assertEqual(metrics["fill_quality_sample_count"], 1)
        self.assertEqual(statuses["closed_trade_status"], "UNTESTED")
        self.assertEqual(statuses["profit_factor_status"], "UNTESTED")
        self.assertEqual(statuses["realized_vs_expected_edge_status"], "UNTESTED")
        self.assertTrue(all(f":{target_key}:" in source_id for source_id in source_ids))

    def test_partial_sell_counts_strategy_exit_policy_without_closed_trade_claim(self):
        weak_btc = build_upbit_public_candle_fixture(
            symbol="KRW-BTC",
            session_id="mvp4_upbit_paper_runtime",
            profile="WEAK_RANGE",
        )
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id="mvp4_upbit_paper_runtime",
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)
        mark_price = weak_btc["candles"][-1]["close"]
        portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id="mvp4_upbit_paper_runtime",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.3",
            fill_price=mark_price,
            mark_price=mark_price,
            fee_amount="150",
            source_runtime_cycle_id="prior-paper-entry",
            source_paper_ledger_head_hash="B" * 64,
        )
        partial_runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-performance-partial-strategy-exit",
            market_data_universe=[weak_btc, strong_eth],
            current_paper_portfolio_snapshot=portfolio,
            paper_cash_available=portfolio["cash_available"],
            paper_equity=portfolio["equity"],
            paper_position_market_value=portfolio["position_market_value"],
        )
        lifecycle = partial_runtime["position_management_decision"]
        target_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(partial_runtime)
        target_scorecard["candidate_id"] = lifecycle["entry_candidate_id"]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_dir = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp4_upbit_paper_runtime"
            runtime_dir.mkdir(parents=True)
            runtime_path = runtime_dir / f"{partial_runtime['cycle_id']}.runtime_cycle.json"
            runtime_path.write_text(json.dumps(partial_runtime, sort_keys=True), encoding="utf-8")
            history = {
                "history_id": "partial-strategy-exit-policy-history",
                "history_hash": "E" * 64,
                "samples": [
                    {
                        "source_runtime_cycle_path": runtime_path.relative_to(root).as_posix(),
                        "source_runtime_cycle_hash": partial_runtime["cycle_hash"],
                    }
                ],
            }

            statuses, metrics, _source_ids = performance_inputs_from_runtime_sample_history(
                candidate_scorecard=target_scorecard,
                runtime_sample_history=history,
                root=root,
            )

        self.assertEqual(partial_runtime["final_decision"], "REDUCE_POSITION")
        self.assertEqual(lifecycle["requested_position_decision"], "EXIT_POSITION")
        self.assertEqual(lifecycle["execution_adjusted_position_decision_reason"], "PARTIAL_EXIT_FILL")
        self.assertEqual(lifecycle["strategy_exit_action"], "FULL_EXIT")
        self.assertEqual(partial_runtime["paper_fill"]["side"], "SELL")
        self.assertEqual(metrics["closed_trade_sample_count"], 0)
        self.assertEqual(metrics["strategy_exit_policy_sample_count"], 1)
        self.assertEqual(metrics["strategy_exit_policy_match_count"], 1)
        self.assertEqual(metrics["strategy_exit_policy_mismatch_count"], 0)
        self.assertEqual(metrics["strategy_exit_reason_count"], 1)
        self.assertEqual(statuses["closed_trade_status"], "UNTESTED")
        self.assertEqual(statuses["strategy_exit_policy_status"], "FAIL")
        self.assertEqual(statuses["profit_factor_status"], "UNTESTED")

    def test_runtime_performance_inputs_collect_regime_outcome_coverage(self):
        target_entry_runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-regime-outcome-target-entry",
            symbol="KRW-BTC",
        )
        target_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(target_entry_runtime)
        runtimes = [
            _closed_trade_runtime_for_candidate(
                symbol="KRW-BTC",
                cycle_id="scorecard-regime-outcome-uptrend-exit",
            ),
            _no_trade_runtime_for_candidate(
                symbol="KRW-BTC",
                cycle_id="scorecard-regime-outcome-range-no-trade",
                profile="QUIET_RANGE",
            ),
            _no_trade_runtime_for_candidate(
                symbol="KRW-BTC",
                cycle_id="scorecard-regime-outcome-downtrend-no-trade",
                profile="DOWNTREND",
            ),
            _no_trade_runtime_for_candidate(
                symbol="KRW-BTC",
                cycle_id="scorecard-regime-outcome-risk-off-no-trade",
                profile="PANIC",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_dir = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp4_upbit_paper_runtime"
            runtime_dir.mkdir(parents=True)
            samples = []
            for runtime in runtimes:
                runtime_path = runtime_dir / f"{runtime['cycle_id']}.runtime_cycle.json"
                runtime_path.write_text(json.dumps(runtime, sort_keys=True), encoding="utf-8")
                samples.append(
                    {
                        "source_runtime_cycle_path": runtime_path.relative_to(root).as_posix(),
                        "source_runtime_cycle_hash": runtime["cycle_hash"],
                    }
                )
            history = {
                "history_id": "candidate-regime-outcome-history",
                "history_hash": "E" * 64,
                "samples": samples,
            }

            statuses, metrics, _ = performance_inputs_from_runtime_sample_history(
                candidate_scorecard=target_scorecard,
                runtime_sample_history=history,
                root=root,
            )

        regimes = {item["regime"]: item for item in metrics["regime_outcome_counts"]}
        self.assertEqual(metrics["regime_outcome_sample_count"], 4)
        self.assertEqual(metrics["regime_outcome_covered_count"], 4)
        self.assertEqual(metrics["regime_outcome_trade_count"], 1)
        self.assertEqual(metrics["regime_outcome_no_trade_count"], 3)
        self.assertEqual(metrics["regime_outcome_mismatch_count"], 0)
        self.assertEqual(statuses["regime_outcome_status"], "PASS")
        self.assertEqual(regimes["DOWNTREND"]["trade_count"], 0)
        self.assertFalse(regimes["DOWNTREND"]["trade_allowed"])
        self.assertEqual(regimes["RISK_OFF"]["trade_count"], 0)
        self.assertFalse(regimes["RISK_OFF"]["trade_allowed"])

    def test_strategy_exit_policy_mismatch_blocks_paper_ranking(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-exit-policy-mismatch")
        weak_performance = dict(PASS_PERFORMANCE_METRICS)
        weak_performance["strategy_exit_policy_match_count"] = 41
        weak_performance["strategy_exit_policy_mismatch_count"] = 1

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
            performance_statuses={**PERFORMANCE_PASS, "strategy_exit_policy_status": "FAIL"},
            performance_metrics=weak_performance,
            performance_source_evidence_ids=performance_source_evidence_ids(runtime),
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["performance_ready"])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["strategy_exit_policy_status"], "FAIL")
        self.assertIn("EXECUTION_FEEDBACK_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_regime_outcome_mismatch_blocks_paper_ranking(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-regime-outcome-mismatch")
        weak_performance = copy.deepcopy(PASS_PERFORMANCE_METRICS)
        weak_performance["regime_outcome_mismatch_count"] = 1
        weak_performance["regime_outcome_counts"][-1]["mismatch_count"] = 1

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
            robustness_source_evidence_ids=[
                robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
                robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
            ],
            performance_statuses={**PERFORMANCE_PASS, "regime_outcome_status": "FAIL"},
            performance_metrics=weak_performance,
            performance_source_evidence_ids=performance_source_evidence_ids(runtime),
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["performance_ready"])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["regime_outcome_status"], "FAIL")
        self.assertIn("REGIME_MISMATCH", {blocker["code"] for blocker in scorecard["blockers"]})

    def test_scorecard_writer_preserves_candidate_scoped_snapshots_without_live_permission(self):
        btc_runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-writer-btc-snapshot",
            symbol="KRW-BTC",
        )
        eth_runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="scorecard-writer-eth-snapshot",
            symbol="KRW-ETH",
        )
        btc_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(btc_runtime)
        eth_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(eth_runtime)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical_path = write_upbit_paper_candidate_scorecard(root=root, scorecard=btc_scorecard)
            btc_snapshot_path = (
                canonical_path.parent
                / "candidate_scorecards"
                / f"{safe_candidate_scorecard_filename(btc_scorecard['candidate_id'])}.candidate_scorecard.json"
            )

            second_canonical_path = write_upbit_paper_candidate_scorecard(root=root, scorecard=eth_scorecard)
            eth_snapshot_path = (
                canonical_path.parent
                / "candidate_scorecards"
                / f"{safe_candidate_scorecard_filename(eth_scorecard['candidate_id'])}.candidate_scorecard.json"
            )
            canonical = json.loads(second_canonical_path.read_text(encoding="utf-8"))
            btc_snapshot = json.loads(btc_snapshot_path.read_text(encoding="utf-8"))
            eth_snapshot = json.loads(eth_snapshot_path.read_text(encoding="utf-8"))

        self.assertEqual(canonical["candidate_id"], eth_scorecard["candidate_id"])
        self.assertEqual(btc_snapshot["candidate_id"], btc_scorecard["candidate_id"])
        self.assertEqual(eth_snapshot["candidate_id"], eth_scorecard["candidate_id"])
        self.assertEqual(_candidate_scorecard_net_ev_errors(btc_snapshot), [])
        self.assertEqual(_candidate_scorecard_net_ev_errors(eth_snapshot), [])
        self.assertFalse(btc_snapshot["live_order_ready"])
        self.assertFalse(btc_snapshot["live_order_allowed"])
        self.assertFalse(btc_snapshot["can_live_trade"])
        self.assertFalse(btc_snapshot["scale_up_allowed"])
        self.assertFalse(eth_snapshot["live_order_allowed"])

    def test_scorecard_live_flag_mutation_is_rejected(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-live-mutation")
        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        mutated = copy.deepcopy(scorecard)
        mutated["live_order_allowed"] = True

        errors = _candidate_scorecard_net_ev_errors(mutated)

        self.assertTrue(any("expected const False" in error for error in errors), errors)

    def test_invalid_runtime_cycle_cannot_become_scorecard(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-invalid-source")
        runtime["live_order_allowed"] = True
        runtime["cycle_hash"] = upbit_paper_runtime_cycle_hash(runtime)

        with self.assertRaises(ValueError):
            candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)


if __name__ == "__main__":
    unittest.main()
