import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.run_upbit_paper_candidate_scorecard import (
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
    performance_source_evidence_id,
    robustness_source_evidence_id,
    safe_candidate_scorecard_filename,
)
from trader1.research.profitability.overfit_diagnostic import (
    overfit_diagnostic_from_upbit_paper_runtime,
    overfit_diagnostic_report_hash,
)
from trader1.research.shadow.shadow_runner import build_paper_shadow_evidence_accumulation_report
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
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
            )
            generation_report = _load_written(root, result, "candidate_generation_report_path")
            discovery_runtime = _load_written(root, result, "candidate_discovery_runtime_cycle_path")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["candidate_discovery_status"], "PASS")
        self.assertIn("read-only public KRW", result["candidate_discovery_message"])
        self.assertEqual(result["candidate_discovery_symbol_count"], 1)
        self.assertGreaterEqual(result["candidate_discovery_ranked_symbol_count"], 1)
        self.assertGreaterEqual(result["candidate_discovery_eligible_symbol_count"], 1)
        self.assertEqual(generation_report["generation_status"], "ALTERNATIVE_REVIEW_READY")
        self.assertEqual(generation_report["best_alternative_symbol"], "KRW-ETH")
        self.assertEqual(generation_report["alternative_candidate_count"], 1)
        best_item = next(
            item
            for item in generation_report["candidate_items"]
            if item["candidate_id"] == generation_report["best_alternative_candidate_id"]
        )
        self.assertEqual(best_item["candidate_source_role"], "BOUNDED_PUBLIC_DISCOVERY_RUNTIME")
        self.assertEqual(best_item["source_runtime_cycle_id"], discovery_runtime["cycle_id"])
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
