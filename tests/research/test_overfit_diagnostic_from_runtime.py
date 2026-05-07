import copy
import json
import tempfile
import unittest
from pathlib import Path

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
from trader1.research.profitability.candidate_scorecard import candidate_scorecard_from_upbit_paper_runtime_cycle
from trader1.research.profitability.overfit_diagnostic import (
    _bootstrap_confidence_lower_bound,
    overfit_diagnostic_from_upbit_paper_runtime,
    overfit_diagnostic_report_hash,
    robustness_inputs_from_overfit_diagnostic,
    write_overfit_diagnostic_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
from trader1.runtime.paper import upbit_paper_runtime_sample_history as sample_history_module
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    build_upbit_paper_runtime_sample_history,
    upbit_paper_runtime_sample_hash,
    upbit_paper_runtime_sample_history_hash,
)
from trader1.research.profitability.candidate_scorecard import robustness_source_evidence_id
from trader1.validation.mvp0_validators import _candidate_scorecard_net_ev_errors, _overfit_diagnostic_errors


def _short_paper_runtime_inputs(root: Path):
    run_upbit_paper_persistent_loop(
        root=root,
        loop_id="overfit-diagnostic-short",
        requested_cycle_count=2,
    )
    history = build_upbit_paper_runtime_sample_history(root=root)
    latest_sample = history["samples"][-1]
    runtime = json.loads((root / latest_sample["source_runtime_cycle_path"]).read_text(encoding="utf-8"))
    scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
    return runtime, scorecard, history


def _strategy_regime_pool_inputs(root: Path, sample_count: int = 20):
    session_id = "mvp1_upbit_paper_launcher"
    runtime_dir = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id / "paper_runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    symbols = [
        "KRW-BTC",
        "KRW-ETH",
        "KRW-XRP",
        "KRW-SOL",
        "KRW-ADA",
        "KRW-DOGE",
        "KRW-AVAX",
        "KRW-DOT",
        "KRW-LINK",
        "KRW-NEAR",
        "KRW-APT",
        "KRW-ARB",
        "KRW-ONDO",
        "KRW-JTO",
        "KRW-ICP",
        "KRW-ALGO",
        "KRW-HIVE",
        "KRW-AXL",
        "KRW-ZIL",
        "KRW-PRL",
    ]
    samples = []
    source_hashes = []
    previous_sample_hash = None
    latest_runtime = None
    for index, symbol in enumerate(symbols[:sample_count], start=1):
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id=f"strategy-regime-pool-cycle-{index:03d}",
            session_id=session_id,
            symbol=symbol,
            market_data=build_upbit_public_candle_fixture(
                symbol=symbol,
                session_id=session_id,
                profile="UPTREND_PULLBACK",
            ),
        )
        runtime_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
        selected_candidate = runtime["selected_candidate"]
        entry_candidates = [
            candidate
            for candidate in runtime.get("strategy_candidates") or []
            if isinstance(candidate, dict) and candidate.get("decision") == "PAPER_ENTRY_REVIEW"
        ]
        entry_candidate_ids = [str(candidate["candidate_id"]) for candidate in entry_candidates]
        entry_symbols = sorted({str(candidate.get("symbol")) for candidate in entry_candidates if candidate.get("symbol")})
        runtime_path = runtime_dir / f"strategy-regime-pool-cycle-{index:03d}.runtime_cycle.json"
        runtime_path.write_text(json.dumps(runtime, sort_keys=True), encoding="utf-8")
        source_runtime_cycle_path = runtime_path.relative_to(root).as_posix()
        sample = {
            "schema_id": "trader1.upbit_paper_runtime_sample.v1",
            "generated_at_utc": runtime["generated_at_utc"],
            "project_id": "TRADER_1",
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": session_id,
            "loop_id": "strategy-regime-pool-loop",
            "cycle_id": runtime["cycle_id"],
            "source_loop_report_path": (
                f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/strategy-regime-pool-loop.persistent_loop_report.json"
            ),
            "source_loop_report_hash": "A" * 64,
            "source_runtime_cycle_path": source_runtime_cycle_path,
            "source_runtime_cycle_hash": runtime["cycle_hash"],
            "runtime_input_role": runtime["runtime_input_role"],
            "final_decision": runtime["final_decision"],
            "paper_ledger_head_hash": runtime.get("paper_ledger_head_hash"),
            "paper_portfolio_snapshot_hash": runtime.get("paper_portfolio_snapshot", {}).get("snapshot_hash"),
            "candidate_count": len(runtime.get("strategy_candidates") or []),
            "entry_reason_count": max(1, len(runtime.get("entry_reasons") or [])),
            "exit_reason_count": 0,
            "no_trade_reason_count": len(runtime.get("no_trade_reasons") or []),
            "scorecard_candidate_identity_binding_status": "BOUND",
            "scorecard_candidate_identity_source": "SELECTED_CANDIDATE",
            "scorecard_candidate_live_flags_clear": True,
            "scorecard_symbol": runtime_scorecard["symbol"],
            "scorecard_candidate_id": runtime_scorecard["candidate_id"],
            "scorecard_strategy_family": selected_candidate["strategy_family"],
            "scorecard_strategy_id": runtime_scorecard["strategy_id"],
            "scorecard_parameter_hash": runtime_scorecard["parameter_hash"],
            "scorecard_candidate_decision": selected_candidate["decision"],
            "scorecard_candidate_net_ev_after_cost_bps": selected_candidate["net_ev_after_cost_bps"],
            "paper_entry_review_candidate_count": len(entry_candidate_ids),
            "paper_entry_review_candidate_ids": entry_candidate_ids,
            "paper_entry_review_symbol_count": len(entry_symbols),
            "paper_entry_review_symbols": entry_symbols,
            "previous_sample_hash": previous_sample_hash,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "sample_hash": "",
        }
        sample["sample_hash"] = upbit_paper_runtime_sample_hash(sample)
        previous_sample_hash = sample["sample_hash"]
        samples.append(sample)
        source_hashes.append(runtime["cycle_hash"])
        latest_runtime = runtime

    assert latest_runtime is not None
    scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(latest_runtime)
    scope_summaries = sample_history_module._candidate_scope_sample_summaries(
        samples,
        min_required_sample_count=sample_history_module.DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT,
    )
    scope_fields = sample_history_module._active_candidate_scope_fields(
        scope_summaries,
        min_required_sample_count=sample_history_module.DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT,
    )
    history = {
        "schema_id": "trader1.upbit_paper_runtime_sample_history.v1",
        "generated_at_utc": latest_runtime["generated_at_utc"],
        "project_id": "TRADER_1",
        "history_id": "upbit-paper-runtime-sample-history",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": "paper_runtime_analysis_truth",
        "runtime_analysis_only": True,
        "execution_truth": False,
        "dashboard_truth_only": False,
        "history_evidence_role": "PAPER_RUNTIME_SAMPLE_HISTORY_NOT_LONG_RUN_EVIDENCE",
        "runtime_sample_status": "COLLECTING",
        "primary_blocker_code": "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
        "source_loop_report_count": 1,
        "accepted_loop_report_count": 1,
        "accepted_cycle_sample_count": len(samples),
        "unique_runtime_cycle_hash_count": len(set(source_hashes)),
        "duplicate_cycle_hash_count": 0,
        "invalid_source_count": 0,
        "invalid_sources": [],
        "first_sample_at_utc": samples[0]["generated_at_utc"],
        "latest_sample_at_utc": samples[-1]["generated_at_utc"],
        "observed_span_seconds": 0,
        "min_actual_long_run_span_seconds": 86400,
        "min_actual_long_run_cycle_count": 2880,
        "span_floor_met": False,
        "cycle_floor_met": False,
        "min_profitability_scope_sample_count": sample_history_module.DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT,
        **scope_fields,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "long_run_blocker_code": "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
        "long_run_next_action": "Collect validated PAPER history before live review.",
        "promotion_eligible": False,
        "source_loop_report_hashes": ["A" * 64],
        "source_runtime_cycle_hashes": source_hashes,
        "samples": samples,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "history_hash": "",
    }
    history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)
    return latest_runtime, scorecard, history


class OverfitDiagnosticFromRuntimeTest(unittest.TestCase):
    def test_bootstrap_lower_bound_uses_deterministic_resampling(self):
        values = [float(index) for index in range(1, 81)]

        lower_a, iterations_a = _bootstrap_confidence_lower_bound(
            values,
            min_required_sample_count=80,
            iteration_count=200,
            seed_material={"case": "bootstrap-a"},
        )
        lower_a_repeat, iterations_a_repeat = _bootstrap_confidence_lower_bound(
            values,
            min_required_sample_count=80,
            iteration_count=200,
            seed_material={"case": "bootstrap-a"},
        )
        lower_b, iterations_b = _bootstrap_confidence_lower_bound(
            values,
            min_required_sample_count=80,
            iteration_count=200,
            seed_material={"case": "bootstrap-b"},
        )
        blocked_lower, blocked_iterations = _bootstrap_confidence_lower_bound(
            values[:10],
            min_required_sample_count=80,
            iteration_count=200,
            seed_material={"case": "too-short"},
        )

        self.assertEqual(iterations_a, 200)
        self.assertEqual((lower_a, iterations_a), (lower_a_repeat, iterations_a_repeat))
        self.assertNotEqual(lower_a, lower_b)
        self.assertEqual(iterations_b, 200)
        self.assertEqual((blocked_lower, blocked_iterations), (0.0, 0))

    def test_short_runtime_history_builds_blocked_non_live_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, scorecard, history = _short_paper_runtime_inputs(root)

            report = overfit_diagnostic_from_upbit_paper_runtime(
                candidate_scorecard=scorecard,
                runtime_sample_history=history,
                root=root,
            )

        self.assertEqual(_overfit_diagnostic_errors(report), [])
        self.assertEqual(report["schema_id"], "trader1.overfit_diagnostic_report.v1")
        self.assertEqual(report["diagnostic_status"], "BLOCKED_FOR_ROBUSTNESS")
        self.assertFalse(report["robustness_eligible"])
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertEqual(report["sample_count"], 2)
        self.assertEqual(report["min_required_sample_count"], 300)
        self.assertEqual(report["preliminary_robustness_status"], "INSUFFICIENT_PRELIMINARY_SAMPLE")
        self.assertEqual(report["preliminary_min_required_sample_count"], 20)
        self.assertEqual(report["preliminary_oos_status"], "UNTESTED")
        self.assertEqual(report["diagnostic_hash"], overfit_diagnostic_report_hash(report))
        blocker_codes = {blocker["code"] for blocker in report["blockers"]}
        self.assertTrue(
            {
                "SAMPLE_INSUFFICIENT",
                "OOS_MISSING",
                "WALK_FORWARD_MISSING",
                "BOOTSTRAP_UNSTABLE",
                "OVERFIT_RISK_HIGH",
            }.issubset(blocker_codes)
        )
        self.assertTrue(any(source_id.startswith("runtime_sample_history:") for source_id in report["source_evidence_ids"]))
        self.assertTrue(any(source_id.startswith("upbit_paper_runtime_cycle:") for source_id in report["source_evidence_ids"]))

    def test_preliminary_diagnostic_measures_short_window_without_full_robustness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, scorecard, history = _short_paper_runtime_inputs(root)

            report = overfit_diagnostic_from_upbit_paper_runtime(
                candidate_scorecard=scorecard,
                runtime_sample_history=history,
                root=root,
                min_preliminary_sample_count=2,
            )

            statuses, source_ids = robustness_inputs_from_overfit_diagnostic(report)

        self.assertEqual(_overfit_diagnostic_errors(report), [])
        self.assertEqual(report["sample_count"], 2)
        self.assertEqual(report["min_required_sample_count"], 300)
        self.assertEqual(report["preliminary_min_required_sample_count"], 2)
        self.assertIn(
            report["preliminary_robustness_status"],
            {"FAVORABLE_BLOCKED_BY_MATURITY", "UNFAVORABLE_BLOCKED_BY_EVIDENCE"},
        )
        self.assertIn(report["preliminary_oos_status"], {"PASS", "FAIL"})
        self.assertIn(report["preliminary_walk_forward_status"], {"PASS", "FAIL"})
        self.assertIn(report["preliminary_bootstrap_status"], {"PASS", "FAIL"})
        self.assertGreaterEqual(report["preliminary_walk_forward_window_count"], 1)
        self.assertEqual(report["preliminary_bootstrap_iteration_count"], 500)
        self.assertIsInstance(report["preliminary_summary"], str)
        self.assertIsInstance(report["preliminary_next_action"], str)
        self.assertEqual(report["oos_status"], "UNTESTED")
        self.assertFalse(report["robustness_eligible"])
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(source_ids)
        self.assertEqual(statuses["oos_status"], "UNTESTED")
        self.assertFalse(report["live_order_allowed"])

    def test_preliminary_diagnostic_uses_strategy_regime_cycle_pool_without_live_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, scorecard, history = _strategy_regime_pool_inputs(root, sample_count=20)

            report = overfit_diagnostic_from_upbit_paper_runtime(
                candidate_scorecard=scorecard,
                runtime_sample_history=history,
                root=root,
            )

            statuses, source_ids = robustness_inputs_from_overfit_diagnostic(report)

        self.assertEqual(_overfit_diagnostic_errors(report), [])
        self.assertEqual(report["sample_count"], 1)
        self.assertEqual(report["preliminary_exact_candidate_sample_count"], 1)
        self.assertEqual(report["preliminary_sample_count"], 20)
        self.assertEqual(report["preliminary_evidence_scope"], "STRATEGY_REGIME_CYCLE_POOL")
        self.assertGreaterEqual(report["preliminary_distinct_symbol_count"], 20)
        self.assertGreaterEqual(report["preliminary_distinct_candidate_count"], 20)
        self.assertIn(report["preliminary_oos_status"], {"PASS", "FAIL"})
        self.assertIn(report["preliminary_walk_forward_status"], {"PASS", "FAIL"})
        self.assertIn(report["preliminary_bootstrap_status"], {"PASS", "FAIL"})
        self.assertEqual(report["oos_status"], "UNTESTED")
        self.assertEqual(report["walk_forward_status"], "UNTESTED")
        self.assertEqual(report["bootstrap_status"], "UNTESTED")
        self.assertEqual(report["diagnostic_status"], "BLOCKED_FOR_ROBUSTNESS")
        self.assertFalse(report["robustness_eligible"])
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(source_ids)
        self.assertEqual(statuses["oos_status"], "UNTESTED")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_diagnostic_matches_same_cycle_shadow_entry_when_runtime_symbol_is_managed_position(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "mvp1_upbit_paper_launcher"
            entry_btc = build_upbit_public_candle_fixture(
                symbol="KRW-BTC",
                session_id=session_id,
                profile="UPTREND_PULLBACK",
            )
            weak_btc = build_upbit_public_candle_fixture(
                symbol="KRW-BTC",
                session_id=session_id,
                profile="WEAK_RANGE",
            )
            for candle in weak_btc["candles"]:
                candle["volume"] = "1"
            strong_eth = build_upbit_public_candle_fixture(
                symbol="KRW-ETH",
                session_id=session_id,
                profile="UPTREND_PULLBACK",
            )
            for candle in strong_eth["candles"]:
                candle["volume"] = "5"
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="overfit-diagnostic-managed-position-shadow-entry",
                requested_cycle_count=2,
                market_data_universe_sequence=[
                    [entry_btc],
                    [weak_btc, strong_eth],
                ],
            )
            history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
            latest_sample = history["samples"][-1]
            runtime = json.loads((root / latest_sample["source_runtime_cycle_path"]).read_text(encoding="utf-8"))
            scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
            report = overfit_diagnostic_from_upbit_paper_runtime(
                candidate_scorecard=scorecard,
                runtime_sample_history=history,
                root=root,
                min_required_sample_count=1,
            )

        self.assertEqual(_overfit_diagnostic_errors(report), [])
        self.assertEqual(runtime["symbol"], "KRW-BTC")
        self.assertEqual(runtime["selected_candidate"]["decision"], "NO_TRADE")
        self.assertEqual(scorecard["symbol"], "KRW-ETH")
        self.assertEqual(scorecard["candidate_id"], "KRW-ETH-pullback-trend-long")
        self.assertEqual(report["sample_count"], 1)
        self.assertTrue(any(source_id.startswith("upbit_paper_runtime_cycle:") for source_id in report["source_evidence_ids"]))
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])

    def test_blocked_diagnostic_keeps_scorecard_in_evidence_collection_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime, scorecard, history = _short_paper_runtime_inputs(root)
            report = overfit_diagnostic_from_upbit_paper_runtime(
                candidate_scorecard=scorecard,
                runtime_sample_history=history,
                root=root,
            )

            statuses, source_ids = robustness_inputs_from_overfit_diagnostic(report)
            rescored = candidate_scorecard_from_upbit_paper_runtime_cycle(
                runtime,
                robustness_statuses=statuses,
                robustness_source_evidence_ids=source_ids,
            )

        self.assertEqual(_candidate_scorecard_net_ev_errors(rescored), [])
        self.assertFalse(rescored["ranking_eligible"])
        self.assertEqual(rescored["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertFalse(source_ids)
        blocker_codes = {blocker["code"] for blocker in rescored["blockers"]}
        self.assertTrue({"OOS_MISSING", "WALK_FORWARD_MISSING", "BOOTSTRAP_UNSTABLE", "OVERFIT_RISK_HIGH"}.issubset(blocker_codes))
        self.assertFalse(rescored["live_order_allowed"])

    def test_robust_diagnostic_input_can_rank_paper_only_when_source_ids_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime, scorecard, history = _short_paper_runtime_inputs(root)
            report = overfit_diagnostic_from_upbit_paper_runtime(
                candidate_scorecard=scorecard,
                runtime_sample_history=history,
                root=root,
            )

        robust = copy.deepcopy(report)
        robust_ids = [
            robustness_source_evidence_id("oos", runtime["cycle_id"], runtime["cycle_hash"]),
            robustness_source_evidence_id("walk_forward", runtime["cycle_id"], runtime["cycle_hash"]),
            robustness_source_evidence_id("bootstrap", runtime["cycle_id"], runtime["cycle_hash"]),
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
                "source_evidence_ids": sorted(set(robust["source_evidence_ids"] + robust_ids)),
            }
        )
        robust["diagnostic_hash"] = overfit_diagnostic_report_hash(robust)

        statuses, source_ids = robustness_inputs_from_overfit_diagnostic(robust)
        rescored = candidate_scorecard_from_upbit_paper_runtime_cycle(
            runtime,
            robustness_statuses=statuses,
            robustness_source_evidence_ids=source_ids,
        )

        self.assertEqual(_overfit_diagnostic_errors(robust), [])
        self.assertEqual(_candidate_scorecard_net_ev_errors(rescored), [])
        self.assertEqual(set(source_ids), set(robust_ids))
        self.assertTrue(rescored["ranking_eligible"])
        self.assertEqual(rescored["scorecard_scope"], "PAPER_SCORECARD_INPUT_ONLY")
        self.assertFalse(rescored["live_order_ready"])
        self.assertFalse(rescored["live_order_allowed"])
        self.assertFalse(rescored["can_live_trade"])
        self.assertFalse(rescored["scale_up_allowed"])

    def test_diagnostic_writer_stays_inside_paper_profitability_namespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, scorecard, history = _short_paper_runtime_inputs(root)
            report = overfit_diagnostic_from_upbit_paper_runtime(
                candidate_scorecard=scorecard,
                runtime_sample_history=history,
                root=root,
            )

            path = write_overfit_diagnostic_report(root=root, report=report)
            written = json.loads(path.read_text(encoding="utf-8"))
            candidate_path = (
                path.parent
                / "overfit_diagnostics"
                / f"{report['candidate_id']}.overfit_diagnostic_report.json"
            )
            candidate_written = json.loads(candidate_path.read_text(encoding="utf-8"))

        self.assertTrue(str(path).endswith("system\\runtime\\upbit\\krw_spot\\paper\\mvp1_upbit_paper_launcher\\profitability\\overfit_diagnostic_report.json"))
        self.assertTrue(str(candidate_path).endswith(f"profitability\\overfit_diagnostics\\{report['candidate_id']}.overfit_diagnostic_report.json"))
        self.assertEqual(written["diagnostic_hash"], overfit_diagnostic_report_hash(written))
        self.assertEqual(candidate_written["diagnostic_hash"], overfit_diagnostic_report_hash(candidate_written))
        self.assertEqual(candidate_written["candidate_id"], written["candidate_id"])
        self.assertFalse(written["live_order_allowed"])
        self.assertFalse(candidate_written["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
