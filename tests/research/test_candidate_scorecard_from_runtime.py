import copy
import json
import tempfile
import unittest
from pathlib import Path

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
from trader1.research.profitability.candidate_scorecard import (
    PERFORMANCE_PASS,
    ROBUSTNESS_PASS,
    candidate_scorecard_from_upbit_paper_runtime_cycle,
    has_required_performance_source_ids,
    has_required_robustness_source_ids,
    robustness_source_evidence_id,
    safe_candidate_scorecard_filename,
    stable_hash,
    write_upbit_paper_candidate_scorecard,
)
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report, upbit_paper_runtime_cycle_hash
from trader1.runtime.portfolio.paper_portfolio import build_paper_portfolio_snapshot_from_fill
from trader1.validation.mvp0_validators import _candidate_scorecard_net_ev_errors


def performance_source_evidence_ids(runtime: dict[str, str]) -> list[str]:
    return [
        f"closed_trades:{runtime['cycle_id']}:{runtime['cycle_hash']}",
        f"execution_quality:{runtime['cycle_id']}:{runtime['cycle_hash']}",
        f"performance_summary:{runtime['cycle_id']}:{runtime['cycle_hash']}",
    ]


PASS_PERFORMANCE_METRICS = {
    "closed_trade_sample_count": 42,
    "min_closed_trade_sample_count": 30,
    "profit_factor": 1.42,
    "min_profit_factor": 1.25,
    "max_drawdown_pct": 4.8,
    "max_allowed_drawdown_pct": 8.0,
    "realized_vs_expected_edge_bps": 2.5,
    "min_realized_vs_expected_edge_bps": 0.0,
    "fill_quality_score": 0.91,
    "min_fill_quality_score": 0.80,
}


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
        for index, candle in enumerate(focus_orca["candles"], start=1):
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
        self.assertEqual(scorecard["paper_entry_review_symbol_count"], 2)
        self.assertEqual(len(scorecard["top_symbol_evidence_scorecards"]), 2)
        self.assertGreaterEqual(scorecard["alternative_candidate_count"], 1)
        self.assertNotEqual(scorecard["best_alternative_candidate_id"], scorecard["candidate_id"])
        self.assertIn(scorecard["best_alternative_symbol"], {"KRW-BTC", "KRW-ETH"})
        self.assertIsInstance(scorecard["best_alternative_net_ev_after_cost_bps"], float)
        self.assertTrue(scorecard["rotation_review_required"])
        self.assertEqual(
            scorecard["rotation_review_reason_code"],
            "SELECTED_CANDIDATE_ROBUSTNESS_BLOCKED_WITH_ALTERNATIVE",
        )
        for symbol_scorecard in scorecard["top_symbol_evidence_scorecards"]:
            self.assertFalse(symbol_scorecard["live_order_ready"])
            self.assertFalse(symbol_scorecard["live_order_allowed"])
            self.assertFalse(symbol_scorecard["can_live_trade"])
            self.assertFalse(symbol_scorecard["scale_up_allowed"])
        self.assertFalse(scorecard["live_order_allowed"])

    def test_robustness_pass_requires_source_evidence_before_paper_ranking(self):
        runtime = build_upbit_paper_runtime_cycle_report(cycle_id="scorecard-runtime-robust-no-source")

        scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=ROBUSTNESS_PASS,
        )
        errors = _candidate_scorecard_net_ev_errors(scorecard)

        self.assertEqual(errors, [])
        self.assertFalse(scorecard["ranking_eligible"])
        self.assertIn("SCORECARD_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})

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
        self.assertIn("SCORECARD_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})

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
        self.assertIn("SCORECARD_MISSING", {blocker["code"] for blocker in scorecard["blockers"]})

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
        self.assertTrue(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["scorecard_scope"], "PAPER_SCORECARD_INPUT_ONLY")
        self.assertEqual(scorecard["blockers"], [])
        self.assertEqual(scorecard["live_readiness_status"], "NOT_LIVE_READY")
        self.assertFalse(scorecard["live_order_allowed"])

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
