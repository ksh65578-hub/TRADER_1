import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trader1.runtime.paper.upbit_paper_long_runner import (
    DashboardOpenResult,
    LOCK_BLOCKER_CODE,
    RUNNER_STATUS_RUNNING,
    RUNNER_STATUS_LOCKED,
    RUNNER_STATUS_BLOCKED,
    RUNNER_STATUS_STOPPED,
    DISK_PRESSURE_BLOCKER_CODE,
    acquire_runner_lock,
    apply_runner_artifact_retention,
    build_runner_status_report,
    clear_runner_stop_file_for_operator_start,
    open_runner_dashboard,
    open_runner_dashboard_result,
    paper_candidate_scorecard_path,
    paper_candidate_scorecard_snapshot_path,
    paper_overfit_diagnostic_path,
    paper_runtime_sample_history_path,
    paper_shadow_evidence_accumulation_path,
    release_runner_lock,
    request_upbit_paper_runner_stop,
    root_upbit_paper_long_runner_main,
    root_upbit_paper_stop_main,
    run_upbit_paper_long_running_runner,
    runner_blocked_start_status_path,
    runner_dashboard_path,
    runner_runtime_base,
    runner_lock_path,
    runner_log_path,
    runner_retention_manifest_path,
    runner_start_reconciliation_path,
    runner_status_path,
    runner_stop_file_path,
    runner_stop_request_report_path,
    shadow_persistent_runtime_path,
    shadow_runtime_harness_path,
    shadow_runtime_orchestration_path,
    paper_shadow_harness_binding_path,
    upbit_paper_long_runner_status_hash,
    utc_now,
    validate_upbit_paper_long_runner_status_report,
    validate_upbit_paper_long_runner_retention_manifest,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.runtime.paper.upbit_paper_runtime import upbit_paper_runtime_cycle_hash


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class UpbitPaperLongRunnerTest(unittest.TestCase):
    def test_scope_focus_adapter_rejects_private_order_key_drift(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        focus = {
            "source": "CANDIDATE_GENERATION_PUBLIC_REPLAY_REHYDRATION",
            "candidate_id": "KRW-ETH-pullback-trend-long",
            "symbol": "KRW-ETH",
            "strategy_id": "trend_pullback",
            "parameter_hash": "A" * 64,
            "sample_count": 0,
            "sample_deficit": 30,
            "order_endpoint_called": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        self.assertIsNone(long_runner._paper_scope_focus_from_trade_intent_inputs({"paper_scope_focus": focus}))

    def test_scope_focus_arbitration_keeps_collecting_history_scope_over_provider_switch(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        history_focus = {
            "source": "PAPER_RUNTIME_SAMPLE_HISTORY_ACTIVE_CANDIDATE_SCOPE",
            "candidate_id": "KRW-AXL-pullback-trend-long",
            "symbol": "KRW-AXL",
            "strategy_id": "trend_pullback",
            "parameter_hash": "A" * 64,
            "sample_count": 4,
            "sample_deficit": 26,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        provider_focus = {
            "source": "CANDIDATE_GENERATION_PUBLIC_REPLAY_REHYDRATION",
            "candidate_id": "KRW-WIF-vwap-mean-reversion",
            "symbol": "KRW-WIF",
            "strategy_id": "vwap_mean_reversion",
            "parameter_hash": "B" * 64,
            "sample_count": 0,
            "sample_deficit": 30,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        selected, status = long_runner._select_paper_scope_focus_for_next_cycle(
            history_focus=history_focus,
            provider_focus=provider_focus,
        )

        self.assertEqual(status, "HISTORY_SCOPE_CONTINUITY_SUPPRESSED_PROVIDER_SWITCH")
        self.assertEqual(selected["candidate_id"], history_focus["candidate_id"])
        self.assertEqual(selected["suppressed_provider_focus_candidate_id"], provider_focus["candidate_id"])
        self.assertFalse(selected["live_order_allowed"])

    def test_scope_focus_arbitration_merges_provider_mutation_for_same_history_scope(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        history_focus = {
            "source": "PAPER_RUNTIME_SAMPLE_HISTORY_ACTIVE_CANDIDATE_SCOPE",
            "candidate_id": "KRW-AXL-pullback-trend-long",
            "symbol": "KRW-AXL",
            "strategy_id": "trend_pullback",
            "parameter_hash": "C" * 64,
            "sample_count": 6,
            "sample_deficit": 24,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        provider_focus = dict(history_focus)
        provider_focus.update(
            {
                "source": "CANDIDATE_GENERATION_PUBLIC_REPLAY_REHYDRATION_WITH_MUTATION",
                "sample_count": 0,
                "sample_deficit": 30,
                "mutated_paper_candidate_spec": {
                    "schema_id": "trader1.mutated_paper_candidate_spec.v1",
                    "mutation_id": "mutation-001",
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                    "order_adapter_called": False,
                    "private_endpoint_called": False,
                    "credential_load_attempted": False,
                    "live_key_loaded": False,
                    "order_endpoint_called": False,
                },
            }
        )

        selected, status = long_runner._select_paper_scope_focus_for_next_cycle(
            history_focus=history_focus,
            provider_focus=provider_focus,
        )

        self.assertEqual(status, "HISTORY_SCOPE_CONTINUITY_MERGED_PROVIDER_DETAILS")
        self.assertEqual(selected["sample_count"], 6)
        self.assertEqual(selected["sample_deficit"], 24)
        self.assertEqual(selected["mutated_paper_candidate_spec"]["mutation_id"], "mutation-001")
        self.assertFalse(selected["live_order_allowed"])

    def test_long_runner_uses_history_scope_when_provider_suggests_different_candidate(self):
        from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
            build_upbit_paper_runtime_sample_history,
            validate_upbit_paper_runtime_sample_history_sources,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="long-runner-history-scope-seed",
                requested_cycle_count=1,
            )
            self.assertEqual(first_loop["loop_status"], "PASS")
            history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
            self.assertEqual(
                validate_upbit_paper_runtime_sample_history_sources(root=root, history=history).status,
                "PASS",
            )
            active_scope = history["active_candidate_scope"]
            self.assertIsInstance(active_scope, dict)

            provider_focus = {
                "source": "CANDIDATE_GENERATION_PUBLIC_REPLAY_REHYDRATION",
                "candidate_id": "KRW-WIF-vwap-mean-reversion",
                "symbol": "KRW-WIF",
                "strategy_id": "vwap_mean_reversion",
                "parameter_hash": "D" * 64,
                "sample_count": 0,
                "sample_deficit": 30,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }

            def provider(**_kwargs):
                return {"paper_scope_focus": provider_focus}

            report = run_upbit_paper_long_running_runner(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                runner_id="long-runner-history-scope-continuity",
                max_cycles=1,
                cycle_interval_seconds=0,
                sleep_fn=lambda _seconds: None,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
                emit_console_status=False,
                paper_trade_intent_inputs_provider=provider,
            )

        self.assertEqual(report["runner_status"], RUNNER_STATUS_STOPPED)
        self.assertEqual(report["completed_cycle_count"], 1)
        self.assertTrue(report["paper_scope_continuity_requested"])
        self.assertEqual(report["paper_scope_continuity_requested_candidate_id"], active_scope["candidate_id"])
        self.assertNotEqual(report["paper_scope_continuity_requested_candidate_id"], provider_focus["candidate_id"])
        self.assertGreaterEqual(report["paper_scope_sample_count"], 2)
        self.assertFalse(report["live_order_allowed"])

    def test_scope_continuity_focus_persists_fresh_history_before_cycle(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner
        from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
            build_upbit_paper_runtime_sample_history,
            validate_upbit_paper_runtime_sample_history_sources,
            write_upbit_paper_runtime_sample_history,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "mvp1_upbit_paper_launcher"
            first_loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="scope-precycle-history-seed-a",
                requested_cycle_count=1,
            )
            self.assertEqual(first_loop["loop_status"], "PASS")
            stale_history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
            self.assertEqual(
                validate_upbit_paper_runtime_sample_history_sources(root=root, history=stale_history).status,
                "PASS",
            )
            focus = stale_history["active_candidate_scope"]
            self.assertIsInstance(focus, dict)
            stale_path = write_upbit_paper_runtime_sample_history(root=root, history=stale_history)

            second_loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="scope-precycle-history-seed-b",
                requested_cycle_count=1,
                paper_scope_focus=focus,
            )
            self.assertEqual(second_loop["loop_status"], "PASS")
            self.assertEqual(json.loads(stale_path.read_text(encoding="utf-8"))["active_candidate_scope_sample_count"], 1)

            selected = long_runner._paper_scope_continuity_focus_from_history(
                root,
                session_id,
                persist_fresh_history=True,
            )
            materialized = json.loads(paper_runtime_sample_history_path(root, session_id).read_text(encoding="utf-8"))

        self.assertIsInstance(selected, dict)
        self.assertEqual(selected["candidate_id"], focus["candidate_id"])
        self.assertEqual(selected["sample_count"], 2)
        self.assertEqual(materialized["active_candidate_scope"]["candidate_id"], focus["candidate_id"])
        self.assertEqual(materialized["active_candidate_scope_sample_count"], 2)
        self.assertEqual(materialized["active_candidate_scope_sample_deficit"], 28)
        self.assertFalse(selected["live_order_allowed"])
        self.assertFalse(materialized["live_order_allowed"])

    def test_runner_status_uses_source_derived_history_when_companion_is_stale(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner
        from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
            build_upbit_paper_runtime_sample_history,
            validate_upbit_paper_runtime_sample_history_sources,
            write_upbit_paper_runtime_sample_history,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "mvp1_upbit_paper_launcher"
            first_loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="source-derived-history-status-a",
                requested_cycle_count=1,
            )
            self.assertEqual(first_loop["loop_status"], "PASS")
            stale_history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
            self.assertEqual(
                validate_upbit_paper_runtime_sample_history_sources(root=root, history=stale_history).status,
                "PASS",
            )
            focus = stale_history["active_candidate_scope"]
            self.assertIsInstance(focus, dict)
            write_upbit_paper_runtime_sample_history(root=root, history=stale_history)

            second_loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="source-derived-history-status-b",
                requested_cycle_count=1,
                paper_scope_focus=focus,
            )
            self.assertEqual(second_loop["loop_status"], "PASS")

            report = long_runner.build_runner_status_report(
                root=root,
                runner_id="source-derived-history-status-runner",
                session_id=session_id,
                runner_status=RUNNER_STATUS_STOPPED,
                started_at_utc=utc_now(),
                completed_cycle_count=2,
                failed_cycle_count=0,
                cycle_interval_seconds=0,
                loop_report=second_loop,
                stop_reason="TEST",
            )
            materialized = _load_json(paper_runtime_sample_history_path(root, session_id))
            materialized_validation_status = validate_upbit_paper_runtime_sample_history_sources(
                root=root,
                history=materialized,
            ).status
            repeat_report = long_runner.build_runner_status_report(
                root=root,
                runner_id="source-derived-history-status-runner-repeat",
                session_id=session_id,
                runner_status=RUNNER_STATUS_STOPPED,
                started_at_utc=utc_now(),
                completed_cycle_count=2,
                failed_cycle_count=0,
                cycle_interval_seconds=0,
                loop_report=second_loop,
                stop_reason="TEST_REPEAT",
            )
            repeated_materialized = _load_json(paper_runtime_sample_history_path(root, session_id))

        self.assertEqual(report["runtime_sample_history_status"], "PASS")
        self.assertEqual(report["runtime_sample_history_effective_source"], "RUNTIME_SOURCE_DERIVED_SAMPLE_HISTORY")
        self.assertEqual(report["runtime_sample_history_source_consistency_status"], "PASS")
        self.assertEqual(report["runtime_sample_history_materialization_status"], "PASS")
        self.assertTrue(report["runtime_sample_history_materialized_from_source"])
        self.assertEqual(report["runtime_sample_history_materialized_accepted_cycle_sample_count"], 2)
        self.assertEqual(report["runtime_sample_history_materialized_active_candidate_id"], focus["candidate_id"])
        self.assertIn(
            "COMPANION_HISTORY_HASH_MISMATCH_SOURCE_REFRESH_USED",
            report["runtime_sample_history_source_consistency_issues"],
        )
        self.assertEqual(report["runtime_sample_history_companion_accepted_cycle_sample_count"], 1)
        self.assertEqual(report["runtime_sample_history_companion_active_sample_count"], 1)
        self.assertEqual(report["runtime_sample_count"], 2)
        self.assertEqual(report["paper_scope_candidate_id"], focus["candidate_id"])
        self.assertEqual(report["paper_scope_sample_count"], 2)
        self.assertEqual(materialized["accepted_cycle_sample_count"], 2)
        self.assertEqual(materialized["active_candidate_scope"]["candidate_id"], focus["candidate_id"])
        self.assertEqual(materialized["active_candidate_scope_sample_count"], 2)
        self.assertEqual(materialized["active_candidate_scope_sample_deficit"], 28)
        self.assertFalse(materialized["live_order_ready"])
        self.assertFalse(materialized["live_order_allowed"])
        self.assertFalse(materialized["can_live_trade"])
        self.assertFalse(materialized["scale_up_allowed"])
        self.assertEqual(materialized_validation_status, "PASS")
        self.assertEqual(repeat_report["runtime_sample_history_materialization_status"], "NOT_NEEDED")
        self.assertFalse(repeat_report["runtime_sample_history_materialized_from_source"])
        self.assertEqual(repeated_materialized["history_hash"], materialized["history_hash"])
        self.assertNotIn(
            "COMPANION_HISTORY_HASH_MISMATCH_SOURCE_REFRESH_USED",
            repeat_report["runtime_sample_history_source_consistency_issues"],
        )
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertNotEqual(long_runner.validate_upbit_paper_long_runner_status_report(report)["status"], "FAIL")

    def test_profitability_sample_selection_prefers_entry_review_over_later_no_trade(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        samples = [
            {
                "cycle_id": "cycle-entry-review",
                "source_runtime_cycle_path": "paper_runtime/cycles/cycle-entry-review.runtime_cycle.json",
                "source_runtime_cycle_hash": "A" * 64,
                "candidate_count": 60,
                "entry_reason_count": 2,
                "no_trade_reason_count": 2,
                "scorecard_candidate_identity_binding_status": "BOUND",
                "scorecard_candidate_live_flags_clear": True,
                "scorecard_candidate_decision": "PAPER_ENTRY_REVIEW",
                "scorecard_candidate_id": "KRW-ONDO-breakout-retest-long",
                "scorecard_strategy_id": "breakout_retest",
                "scorecard_parameter_hash": "B" * 64,
                "scorecard_candidate_net_ev_after_cost_bps": "28.12",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            {
                "cycle_id": "cycle-latest-no-trade",
                "source_runtime_cycle_path": "paper_runtime/cycles/cycle-latest-no-trade.runtime_cycle.json",
                "source_runtime_cycle_hash": "C" * 64,
                "candidate_count": 51,
                "entry_reason_count": 0,
                "no_trade_reason_count": 3,
                "scorecard_candidate_identity_binding_status": "BOUND",
                "scorecard_candidate_live_flags_clear": True,
                "scorecard_candidate_decision": "NO_TRADE",
                "scorecard_candidate_id": "KRW-BTC-vwap-mean-reversion",
                "scorecard_strategy_id": "vwap_mean_reversion",
                "scorecard_parameter_hash": "D" * 64,
                "scorecard_candidate_net_ev_after_cost_bps": "-14.25",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
        ]

        selected = long_runner._select_profitability_evidence_sample(samples)

        self.assertEqual(selected["cycle_id"], "cycle-entry-review")
        self.assertEqual(selected["scorecard_candidate_id"], "KRW-ONDO-breakout-retest-long")
        self.assertFalse(selected["live_order_allowed"])
        self.assertFalse(selected["can_live_trade"])

    def test_profitability_sample_selection_honors_active_scope_no_trade_sample(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        samples = [
            {
                "cycle_id": "cycle-entry-review",
                "source_runtime_cycle_path": "paper_runtime/cycles/cycle-entry-review.runtime_cycle.json",
                "source_runtime_cycle_hash": "A" * 64,
                "candidate_count": 60,
                "entry_reason_count": 2,
                "no_trade_reason_count": 2,
                "scorecard_candidate_identity_binding_status": "BOUND",
                "scorecard_candidate_live_flags_clear": True,
                "scorecard_candidate_decision": "PAPER_ENTRY_REVIEW",
                "scorecard_candidate_id": "KRW-ONDO-breakout-retest-long",
                "scorecard_strategy_id": "breakout_retest",
                "scorecard_parameter_hash": "B" * 64,
                "scorecard_candidate_net_ev_after_cost_bps": "28.12",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            {
                "cycle_id": "cycle-active-scope-no-trade",
                "source_runtime_cycle_path": "paper_runtime/cycles/cycle-active-scope-no-trade.runtime_cycle.json",
                "source_runtime_cycle_hash": "C" * 64,
                "candidate_count": 51,
                "entry_reason_count": 0,
                "no_trade_reason_count": 3,
                "scorecard_candidate_identity_binding_status": "BOUND",
                "scorecard_candidate_live_flags_clear": True,
                "scorecard_candidate_decision": "NO_TRADE",
                "scorecard_candidate_id": "KRW-PROS-pullback-trend-long",
                "scorecard_strategy_id": "trend_pullback",
                "scorecard_parameter_hash": "D" * 64,
                "scorecard_candidate_net_ev_after_cost_bps": "17.25",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
        ]

        selected = long_runner._select_profitability_evidence_sample(
            samples,
            active_scope={
                "candidate_id": "KRW-PROS-pullback-trend-long",
                "latest_runtime_cycle_hash": "C" * 64,
                "latest_cycle_id": "cycle-active-scope-no-trade",
            },
        )

        self.assertEqual(selected["cycle_id"], "cycle-active-scope-no-trade")
        self.assertEqual(selected["scorecard_candidate_id"], "KRW-PROS-pullback-trend-long")
        self.assertFalse(selected["live_order_allowed"])
        self.assertFalse(selected["can_live_trade"])

    def test_profitability_sample_selection_fails_closed_without_usable_sample(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        selected = long_runner._select_profitability_evidence_sample(
            [
                {
                    "cycle_id": "cycle-live-flagged",
                    "candidate_count": 12,
                    "source_runtime_cycle_path": "paper_runtime/cycles/cycle-live-flagged.runtime_cycle.json",
                    "source_runtime_cycle_hash": "E" * 64,
                    "scorecard_candidate_identity_binding_status": "BOUND",
                    "scorecard_candidate_live_flags_clear": False,
                    "scorecard_candidate_id": "KRW-BTC-vwap-mean-reversion",
                    "scorecard_strategy_id": "vwap_mean_reversion",
                    "scorecard_parameter_hash": "F" * 64,
                    "live_order_allowed": True,
                }
            ]
        )

        self.assertIsNone(selected)

    def test_profitability_refresh_materializes_candidate_generation_before_shadow_blocker(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner
        from trader1.research.profitability.candidate_scorecard import validate_candidate_generation_report

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "mvp1_upbit_paper_launcher"
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="candidate-generation-materialization",
                requested_cycle_count=1,
            )
            self.assertEqual(loop["loop_status"], "PASS")

            refresh = long_runner.refresh_non_live_profitability_evidence_from_runtime(root, session_id)
            generation_path = long_runner.paper_candidate_generation_report_path(root, session_id)
            generation_path_exists = generation_path.exists()
            generation_path_relative = str(generation_path.relative_to(root)).replace("\\", "/")
            generation_report = _load_json(generation_path)

        self.assertEqual(refresh["status"], long_runner.NON_LIVE_PROFITABILITY_REFRESH_BLOCKED)
        self.assertEqual(refresh["blocker_code"], "PAPER_SHADOW_RUNTIME_ARTIFACT_MISSING")
        self.assertTrue(generation_path_exists)
        self.assertEqual(refresh["candidate_generation_report_path"], generation_path_relative)
        self.assertNotEqual(refresh["candidate_generation_status"], "MISSING")
        self.assertEqual(validate_candidate_generation_report(generation_report)[0], "PASS")
        self.assertFalse(generation_report["live_order_ready"])
        self.assertFalse(generation_report["live_order_allowed"])
        self.assertFalse(generation_report["can_live_trade"])
        self.assertFalse(generation_report["scale_up_allowed"])

    def test_profitability_refresh_runs_bounded_public_discovery_for_retired_candidate(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner
        from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
        from trader1.research.profitability.candidate_scorecard import stable_hash, validate_candidate_generation_report
        from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
        from trader1.runtime.portfolio.paper_portfolio import build_paper_portfolio_snapshot_from_fill

        session_id = "mvp1_upbit_paper_launcher"
        weak_btc = build_upbit_public_candle_fixture(symbol="KRW-BTC", session_id=session_id, profile="WEAK_RANGE")
        for candle in weak_btc["candles"]:
            candle["volume"] = "1"
        strong_eth = build_upbit_public_candle_fixture(
            symbol="KRW-ETH",
            session_id=session_id,
            profile="UPTREND_PULLBACK",
        )
        for index, candle in enumerate(strong_eth["candles"], start=1):
            candle["volume"] = str(8 + index * 2)
        focus_orca = build_upbit_public_candle_fixture(
            symbol="KRW-ORCA",
            session_id=session_id,
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
            session_id=session_id,
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.005",
            fill_price=mark_price,
            mark_price=mark_price,
            fee_amount="2.5",
            starting_cash="1000000",
            source_runtime_cycle_id="previous-candidate-generation-runtime-discovery",
            source_paper_ledger_head_hash="D" * 64,
        )
        focus_candidate_id = "KRW-ORCA-pullback-trend-long"
        focus_parameter_hash = stable_hash(f"{focus_candidate_id}:PULLBACK_TREND_LONG:KRW-ORCA")
        discovery_runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="candidate-generation-runtime-discovery-alt",
            session_id=session_id,
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
        discovery_context = {
            "status": "PASS",
            "blocker_code": None,
            "message": "test discovery",
            "symbol_count": 1,
            "ranked_symbol_count": 1,
            "eligible_symbol_count": 1,
            "evaluated_candidate_count": 3,
            "paper_entry_review_candidate_count": 1,
            "adaptive_expansion_attempted": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        def fake_replay(**kwargs):
            self.assertEqual(kwargs["candidate_generation_report"]["generation_status"], "ALTERNATIVE_REVIEW_READY")
            return {
                "status": "BLOCKED",
                "blocker_code": "PUBLIC_REPLAY_ROBUSTNESS_FAILED",
                "message": "test replay blocked",
                "candidate_id": "KRW-ETH-pullback-trend-long",
                "symbol": "KRW-ETH",
                "replay_status": "BLOCKED",
                "sample_count": 0,
                "replay_closed_trade_sample_count": 0,
                "replay_closed_trade_deficit": 30,
                "replay_closed_trade_maturity_status": "BLOCKED",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="candidate-generation-runtime-discovery",
                requested_cycle_count=1,
            )
            self.assertEqual(loop["loop_status"], "PASS")

            with patch(
                "tools.run_upbit_paper_candidate_scorecard._build_bounded_public_discovery_runtime_cycle",
                return_value=(discovery_runtime, discovery_context),
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard._build_and_write_alternative_public_replay",
                side_effect=fake_replay,
            ):
                refresh = long_runner.refresh_non_live_profitability_evidence_from_runtime(root, session_id)

            generation_path = long_runner.paper_candidate_generation_report_path(root, session_id)
            discovery_path = long_runner.paper_candidate_generation_discovery_runtime_path(root, session_id)
            generation_report = _load_json(generation_path)
            written_discovery_runtime = _load_json(discovery_path)

        self.assertEqual(refresh["status"], long_runner.NON_LIVE_PROFITABILITY_REFRESH_BLOCKED)
        self.assertEqual(refresh["blocker_code"], "PAPER_SHADOW_RUNTIME_ARTIFACT_MISSING")
        self.assertEqual(refresh["candidate_discovery_status"], "PASS")
        self.assertEqual(refresh["candidate_discovery_runtime_cycle_path"], str(discovery_path.relative_to(root)).replace("\\", "/"))
        self.assertEqual(refresh["alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(generation_report["generation_status"], "ALTERNATIVE_REVIEW_READY")
        self.assertEqual(generation_report["best_alternative_candidate_id"], "KRW-ETH-pullback-trend-long")
        self.assertEqual(written_discovery_runtime["cycle_id"], discovery_runtime["cycle_id"])
        self.assertEqual(validate_candidate_generation_report(generation_report)[0], "PASS")
        self.assertFalse(generation_report["live_order_ready"])
        self.assertFalse(generation_report["live_order_allowed"])
        self.assertFalse(generation_report["can_live_trade"])
        self.assertFalse(generation_report["scale_up_allowed"])

    def test_profitability_refresh_runs_public_replay_for_existing_review_ready_alternative(self):
        import copy

        import trader1.runtime.paper.upbit_paper_long_runner as long_runner
        from trader1.research.profitability.candidate_scorecard import (
            candidate_generation_report_from_upbit_paper_runtime_cycle,
            candidate_scorecard_from_upbit_paper_runtime_cycle,
            stable_hash,
            validate_candidate_generation_report,
        )
        from trader1.research.replay.replay_runner import (
            PUBLIC_REPLAY_ROBUSTNESS_SCHEMA_ID,
            PUBLIC_REPLAY_VALUE_SOURCE,
            public_replay_robustness_report_hash,
        )
        from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report

        session_id = "mvp1_upbit_paper_launcher"
        runtime = build_upbit_paper_runtime_cycle_report(
            cycle_id="candidate-generation-existing-review-ready-alt",
            session_id=session_id,
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
                "public_replay_robustness:replay-candidate-generation-existing-review-ready-alt:" + "A" * 64,
                "public_market_data:KRW-BTC:" + "B" * 64,
            ],
        )
        selected = runtime["selected_candidate"]
        for index, symbol in enumerate(["KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-ADA", "KRW-AVAX"], start=1):
            alternative = copy.deepcopy(selected)
            alternative["candidate_id"] = f"{symbol}-pullback-trend-long"
            alternative["symbol"] = symbol
            alternative["candidate_selection_score"] = max(0.01, float(selected["candidate_selection_score"]) - index * 0.01)
            alternative["net_ev_after_cost_bps"] = float(selected["net_ev_after_cost_bps"]) + 6.0 - index * 0.1
            runtime["strategy_candidates"].append(alternative)
        generation_report = candidate_generation_report_from_upbit_paper_runtime_cycle(
            runtime,
            candidate_scorecard=scorecard,
        )
        self.assertEqual(generation_report["generation_status"], "ALTERNATIVE_REVIEW_READY")

        def fake_replay(**kwargs):
            self.assertEqual(kwargs["candidate_generation_report"]["generation_status"], "ALTERNATIVE_REVIEW_READY")
            self.assertIsNone(kwargs["candidate_discovery_runtime"])
            return {
                "status": "BLOCKED",
                "blocker_code": "REPLAY_CLOSED_TRADES_MISSING",
                "message": "test same-runtime replay blocked",
                "candidate_id": generation_report["best_alternative_candidate_id"],
                "symbol": generation_report["best_alternative_symbol"],
                "replay_status": "BLOCKED",
                "sample_count": 7,
                "replay_closed_trade_sample_count": 0,
                "replay_closed_trade_deficit": 30,
                "replay_closed_trade_maturity_status": "BLOCKED",
                "replay_closed_trade_maturity_blocker_code": "REPLAY_CLOSED_TRADES_MISSING",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "tools.run_upbit_paper_candidate_scorecard._build_bounded_public_discovery_runtime_cycle",
                side_effect=AssertionError("discovery should not run for an existing review-ready alternative"),
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard._build_and_write_alternative_public_replay",
                side_effect=fake_replay,
            ):
                updated_report, public_review_fields, discovery_runtime = (
                    long_runner._review_public_alternatives_for_candidate_generation(
                        root=root,
                        session_id=session_id,
                        runtime=runtime,
                        scorecard=scorecard,
                        history={"history_id": "existing-review-ready-history", "history_hash": "H" * 64, "samples": []},
                        candidate_generation_report=generation_report,
                    )
                )

        self.assertIsNone(discovery_runtime)
        self.assertEqual(updated_report["generation_status"], "ALTERNATIVE_REVIEW_READY")
        self.assertEqual(validate_candidate_generation_report(updated_report, candidate_scorecard=scorecard)[0], "PASS")
        self.assertEqual(public_review_fields["candidate_discovery_status"], "NOT_REQUESTED")
        self.assertEqual(public_review_fields["alternative_public_replay_status"], "BLOCKED")
        self.assertEqual(public_review_fields["alternative_public_replay_blocker_code"], "REPLAY_CLOSED_TRADES_MISSING")
        self.assertEqual(
            public_review_fields["alternative_public_replay_candidate_id"],
            generation_report["best_alternative_candidate_id"],
        )
        self.assertFalse(updated_report["live_order_ready"])
        self.assertFalse(updated_report["live_order_allowed"])
        self.assertFalse(updated_report["can_live_trade"])
        self.assertFalse(updated_report["scale_up_allowed"])

        mutation_context = {
            "status": "BLOCKED",
            "blocker_code": "OOS_MISSING",
            "path": "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/profitability/mutation/"
            "strategy_mutation_compiler_report.json",
            "candidate_id": generation_report["best_alternative_candidate_id"],
            "source": "BLOCKED_ALTERNATIVE_REPLAY_DIAGNOSTIC",
            "mutation_reason_code": "ROBUSTNESS_GUARD",
            "mutation_id": None,
            "mutated_paper_candidate_spec_id": None,
            "mutation_spec_hash": None,
            "mutated_parameter_hash": None,
            "exploration_budget_id": "mutation-budget:test",
            "ranking_eligible": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        def replay_context_with_report(**kwargs):
            self.assertEqual(kwargs["candidate_generation_report"]["generation_status"], "ALTERNATIVE_REVIEW_READY")
            return {
                "status": "BLOCKED",
                "blocker_code": "MEASUREMENT_MISSING",
                "message": "mature replay is available but robustness is still blocked",
                "candidate_id": generation_report["best_alternative_candidate_id"],
                "symbol": generation_report["best_alternative_symbol"],
                "replay_status": "PASS",
                "sample_count": 90,
                "replay_closed_trade_sample_count": 30,
                "replay_closed_trade_deficit": 0,
                "replay_closed_trade_maturity_status": "PASS",
                "replay_closed_trade_maturity_blocker_code": None,
                "contract_status": "PASS",
                "report": {"candidate_id": generation_report["best_alternative_candidate_id"]},
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "tools.run_upbit_paper_candidate_scorecard._build_bounded_public_discovery_runtime_cycle",
                side_effect=AssertionError("discovery should not run for an existing review-ready alternative"),
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard._build_and_write_alternative_public_replay",
                side_effect=replay_context_with_report,
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard._build_and_write_alternative_review_scorecard",
                return_value={"status": "BLOCKED", "blocker_code": "OOS_MISSING"},
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard._build_and_write_strategy_mutation_report",
                return_value=mutation_context,
            ) as mutation_writer:
                _, mutation_fields, _ = long_runner._review_public_alternatives_for_candidate_generation(
                    root=root,
                    session_id=session_id,
                    runtime=runtime,
                    scorecard=scorecard,
                    diagnostic={"diagnostic_id": "runtime-public-review-diagnostic"},
                    history={"history_id": "existing-review-ready-history", "history_hash": "H" * 64, "samples": []},
                    candidate_generation_report=generation_report,
                )

        self.assertEqual(mutation_fields["strategy_mutation_compiler_status"], "BLOCKED")
        self.assertEqual(mutation_fields["strategy_mutation_compiler_blocker_code"], "OOS_MISSING")
        self.assertEqual(
            mutation_fields["strategy_mutation_compiler_candidate_id"],
            generation_report["best_alternative_candidate_id"],
        )
        self.assertEqual(
            mutation_fields["strategy_mutation_compiler_source"],
            "BLOCKED_ALTERNATIVE_REPLAY_DIAGNOSTIC",
        )
        self.assertFalse(mutation_fields["strategy_mutation_ranking_eligible"])
        self.assertEqual(mutation_writer.call_count, 1)

        calls = []

        def pass_replay_report(candidate_id: str, symbol: str, strategy_id: str, strategy_family: str) -> dict:
            report = {
                "schema_id": PUBLIC_REPLAY_ROBUSTNESS_SCHEMA_ID,
                "generated_at_utc": "2026-05-09T00:00:00Z",
                "project_id": "TRADER_1",
                "replay_id": f"public-replay-expanded:{candidate_id}",
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "REPLAY",
                "session_id": session_id,
                "symbol": symbol,
                "candidate_id": candidate_id,
                "strategy_id": strategy_id,
                "strategy_build_id": "upbit_paper_runtime_cycle_v1",
                "parameter_hash": stable_hash(f"{candidate_id}:{strategy_family}:{symbol}"),
                "value_source": PUBLIC_REPLAY_VALUE_SOURCE,
                "public_market_data_source": "PUBLIC_REST_READ_ONLY",
                "public_market_data_hash": "C" * 64,
                "window_size": 6,
                "sample_count": 900,
                "min_required_sample_count": 300,
                "max_replay_windows": 900,
                "sample_rows": [],
                "replay_closed_trade_sample_count": 30,
                "replay_closed_trade_status": "PASS",
                "min_required_closed_trade_sample_count": 30,
                "replay_closed_trade_deficit": 0,
                "replay_closed_trade_maturity_status": "PASS",
                "replay_closed_trade_maturity_blocker_code": None,
                "replay_strategy_exit_policy_sample_count": 30,
                "replay_strategy_exit_policy_match_count": 30,
                "replay_strategy_exit_policy_mismatch_count": 0,
                "replay_strategy_exit_policy_status": "PASS",
                "replay_strategy_exit_reason_counts": [{"reason_code": "TREND_INVALIDATED", "count": 30}],
                "replay_profit_factor": 1.5,
                "replay_profit_factor_status": "PASS",
                "replay_max_drawdown_bps": 50.0,
                "replay_realized_vs_expected_edge_bps": 12.0,
                "replay_realized_vs_expected_edge_status": "PASS",
                "replay_fill_quality_score": 1.0,
                "replay_execution_cost_delta_bps": 0.0,
                "replay_execution_cost_status": "PASS",
                "replay_performance_scope": "PUBLIC_REPLAY_ONLY_NOT_PAPER_RANKING",
                "replay_status": "PASS",
                "primary_blocker_code": None,
                "blockers": [],
                "credential_load_attempted": False,
                "private_endpoint_called": False,
                "order_endpoint_called": False,
                "order_adapter_called": False,
                "live_key_loaded": False,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
                "report_hash": "",
            }
            report["report_hash"] = public_replay_robustness_report_hash(report)
            return report

        fallback_item = next(
            item
            for item in generation_report["candidate_items"]
            if item["candidate_status"] == "REVIEW_READY"
            and item["candidate_id"] != generation_report["best_alternative_candidate_id"]
        )

        def fake_replay_with_expansion(**kwargs):
            calls.append(kwargs)
            first_item = kwargs["candidate_generation_report"]["candidate_items"][0]
            if len(calls) == 1:
                return {
                    "status": "BLOCKED",
                    "blocker_code": "REPLAY_CLOSED_TRADES_BELOW_MIN",
                    "message": "initial closed trade maturity below floor",
                    "candidate_id": generation_report["best_alternative_candidate_id"],
                    "symbol": generation_report["best_alternative_symbol"],
                    "replay_status": "PASS",
                    "sample_count": 415,
                    "replay_closed_trade_sample_count": 3,
                    "min_required_closed_trade_sample_count": 30,
                    "replay_closed_trade_deficit": 27,
                    "replay_closed_trade_maturity_status": "BLOCKED",
                    "replay_closed_trade_maturity_blocker_code": "REPLAY_CLOSED_TRADES_BELOW_MIN",
                    "candidate_review_evaluations": [
                        {
                            "status": "BLOCKED",
                            "blocker_code": "REPLAY_CLOSED_TRADES_BELOW_MIN",
                            "candidate_id": generation_report["best_alternative_candidate_id"],
                            "sample_count": 415,
                            "replay_closed_trade_sample_count": 3,
                            "min_required_closed_trade_sample_count": 30,
                            "replay_closed_trade_deficit": 27,
                            "replay_closed_trade_maturity_status": "BLOCKED",
                            "replay_closed_trade_maturity_blocker_code": "REPLAY_CLOSED_TRADES_BELOW_MIN",
                        },
                        {
                            "status": "BLOCKED",
                            "blocker_code": "REPLAY_CLOSED_TRADES_BELOW_MIN",
                            "candidate_id": fallback_item["candidate_id"],
                            "sample_count": 420,
                            "replay_closed_trade_sample_count": 2,
                            "min_required_closed_trade_sample_count": 30,
                            "replay_closed_trade_deficit": 28,
                            "replay_closed_trade_maturity_status": "BLOCKED",
                            "replay_closed_trade_maturity_blocker_code": "REPLAY_CLOSED_TRADES_BELOW_MIN",
                        },
                    ],
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }
            if len(calls) == 2:
                self.assertEqual(str(first_item["candidate_id"]), generation_report["best_alternative_candidate_id"])
                return {
                    "status": "BLOCKED",
                    "blocker_code": "REPLAY_CLOSED_TRADES_BELOW_MIN",
                    "message": "preferred expanded replay still below maturity",
                    "candidate_id": str(first_item["candidate_id"]),
                    "symbol": str(first_item["symbol"]),
                    "replay_status": "PASS",
                    "sample_count": 6000,
                    "replay_closed_trade_sample_count": 24,
                    "min_required_closed_trade_sample_count": 30,
                    "replay_closed_trade_deficit": 6,
                    "replay_closed_trade_maturity_status": "BLOCKED",
                    "replay_closed_trade_maturity_blocker_code": "REPLAY_CLOSED_TRADES_BELOW_MIN",
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }
            self.assertEqual(str(first_item["candidate_id"]), str(fallback_item["candidate_id"]))
            report = pass_replay_report(
                candidate_id=str(first_item["candidate_id"]),
                symbol=str(first_item["symbol"]),
                strategy_id=str(first_item["strategy_id"]),
                strategy_family=str(first_item["strategy_family"]),
            )
            return {
                "status": "PASS",
                "blocker_code": None,
                "message": "expanded public replay passed closed-trade maturity",
                "candidate_id": report["candidate_id"],
                "symbol": report["symbol"],
                "replay_status": "PASS",
                "sample_count": report["sample_count"],
                "replay_closed_trade_sample_count": report["replay_closed_trade_sample_count"],
                "replay_closed_trade_deficit": report["replay_closed_trade_deficit"],
                "replay_closed_trade_maturity_status": report["replay_closed_trade_maturity_status"],
                "replay_closed_trade_maturity_blocker_code": report["replay_closed_trade_maturity_blocker_code"],
                "report": report,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "tools.run_upbit_paper_candidate_scorecard._build_bounded_public_discovery_runtime_cycle",
                side_effect=AssertionError("discovery should not run for an existing review-ready alternative"),
            ), patch(
                "tools.run_upbit_paper_candidate_scorecard._build_and_write_alternative_public_replay",
                side_effect=fake_replay_with_expansion,
            ):
                expanded_report, expanded_fields, _ = long_runner._review_public_alternatives_for_candidate_generation(
                    root=root,
                    session_id=session_id,
                    runtime=runtime,
                    scorecard=scorecard,
                    history={"history_id": "existing-review-ready-history", "history_hash": "H" * 64, "samples": []},
                    candidate_generation_report=generation_report,
                )

        self.assertEqual(len(calls), 3)
        expected_expansion_target = long_runner._alternative_replay_closed_trade_maturity_expansion_target(
            {
                "sample_count": 415,
                "replay_closed_trade_sample_count": 3,
                "min_required_closed_trade_sample_count": 30,
                "replay_closed_trade_deficit": 27,
            }
        )
        self.assertGreater(expected_expansion_target, 2400)
        self.assertLessEqual(
            expected_expansion_target,
            long_runner.DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_MAX_TARGET_COUNT,
        )
        self.assertEqual(calls[1]["target_count"], expected_expansion_target)
        self.assertEqual(calls[1]["max_replay_windows"], expected_expansion_target)
        self.assertEqual(calls[1]["candidate_limit"], 1)
        self.assertEqual(
            calls[1]["candidate_generation_report"]["candidate_items"][0]["candidate_id"],
            generation_report["best_alternative_candidate_id"],
        )
        self.assertEqual(calls[2]["target_count"], long_runner.DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_MAX_TARGET_COUNT)
        self.assertEqual(calls[2]["candidate_generation_report"]["candidate_items"][0]["candidate_id"], fallback_item["candidate_id"])
        self.assertEqual(expanded_report["generation_status"], "ALTERNATIVE_PUBLIC_REPLAY_VALIDATED")
        self.assertEqual(expanded_report["best_alternative_candidate_id"], fallback_item["candidate_id"])
        self.assertEqual(validate_candidate_generation_report(expanded_report, candidate_scorecard=scorecard)[0], "PASS")
        self.assertTrue(expanded_fields["alternative_public_replay_maturity_expansion_attempted"])
        self.assertEqual(expanded_fields["alternative_public_replay_maturity_expansion_status"], "PASS")
        self.assertEqual(expanded_fields["alternative_public_replay_maturity_expansion_rotation_count"], 2)
        self.assertEqual(expanded_fields["alternative_public_replay_closed_trade_maturity_status"], "PASS")
        self.assertFalse(expanded_report["live_order_ready"])
        self.assertFalse(expanded_report["live_order_allowed"])
        self.assertFalse(expanded_report["can_live_trade"])
        self.assertFalse(expanded_report["scale_up_allowed"])

    def test_paper_scope_progress_prefers_candidate_scope_over_general_evidence_count(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        fields = long_runner._paper_scope_progress_fields(
            history={
                "min_profitability_scope_sample_count": 30,
                "candidate_scope_sample_summary_count": 1,
                "active_candidate_scope_status": "COLLECT_PAPER_SCOPE_SAMPLES",
                "active_candidate_scope_sample_count": 3,
                "active_candidate_scope_sample_deficit": 27,
                "active_candidate_scope_next_action": "Collect 27 more PAPER samples for scoped candidate.",
                "active_candidate_scope": {
                    "candidate_id": "KRW-BTC-vwap-mean-reversion",
                    "strategy_id": "vwap_mean_reversion",
                    "parameter_hash": "A" * 64,
                    "symbol": "KRW-BTC",
                    "sample_count": 3,
                    "sample_deficit": 27,
                    "scope_progress_status": "COLLECT_PAPER_SCOPE_SAMPLES",
                    "next_collection_action": "RUN_MORE_PAPER_SAMPLE_WINDOWS",
                    "next_operator_action": "Collect 27 more PAPER samples for scoped candidate.",
                    "latest_sample_at_utc": "2026-05-07T00:00:00Z",
                },
            },
            evidence={
                "candidate_id": "KRW-BTC-vwap-mean-reversion",
                "strategy_id": "vwap_mean_reversion",
                "parameter_hash": "A" * 64,
                "paper_sample_count": 40,
                "min_required_sample_count": 30,
                "paper_sample_deficit": 0,
                "evidence_actionability_status": "PASS",
                "primary_collection_deficit_message": "General PAPER evidence already has enough samples.",
            },
        )

        self.assertEqual(fields["paper_scope_progress_status"], "COLLECT_PAPER_SCOPE_SAMPLES")
        self.assertEqual(fields["paper_scope_sample_count"], 3)
        self.assertEqual(fields["paper_scope_min_required_sample_count"], 30)
        self.assertEqual(fields["paper_scope_sample_deficit"], 27)
        self.assertEqual(fields["paper_scope_next_operator_action"], "Collect 27 more PAPER samples for scoped candidate.")
        self.assertEqual(fields["paper_scope_candidate_id"], "KRW-BTC-vwap-mean-reversion")

    def test_runner_portfolio_fields_prefer_source_bound_current_truth_snapshot(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "source_bound_portfolio"
            current_truth_path = long_runner.paper_portfolio_current_truth_path(root, session_id)
            current_truth_path.parent.mkdir(parents=True, exist_ok=True)
            current_truth_path.write_text(
                json.dumps(
                    {
                        "source_runtime_cycle_id": "cycle-1",
                        "snapshot_hash": "A" * 64,
                        "source_paper_ledger_head_hash": "B" * 64,
                        "open_position_count": 1,
                        "cash_available": "880000",
                        "equity": "990000",
                        "realized_pnl": "-10000",
                        "unrealized_pnl": "0",
                        "live_order_ready": False,
                        "live_order_allowed": False,
                        "can_live_trade": False,
                        "scale_up_allowed": False,
                        "order_adapter_called": False,
                        "private_endpoint_called": False,
                        "credential_load_attempted": False,
                        "live_key_loaded": False,
                    }
                ),
                encoding="utf-8",
            )
            runtime_cycle = {
                "cycle_id": "cycle-1",
                "paper_portfolio_snapshot": {
                    "open_position_count": 1,
                    "cash_available": "1000000",
                    "equity": "1005000",
                    "realized_pnl": "0",
                    "unrealized_pnl": "5000",
                    "snapshot_hash": "C" * 64,
                },
            }

            fields = long_runner._portfolio_fields(root, session_id, runtime_cycle)

            self.assertEqual(fields["cash"], "880000")
            self.assertEqual(fields["equity"], "990000")
            self.assertEqual(fields["realized_pnl"], "-10000")
            self.assertEqual(fields["portfolio_truth_source"], "paper_runtime/portfolio/paper_portfolio_snapshot.json")
            self.assertEqual(fields["portfolio_truth_binding_status"], "BOUND_TO_LATEST_RUNTIME_CYCLE")
            self.assertEqual(fields["portfolio_truth_source_runtime_cycle_id"], "cycle-1")
            self.assertEqual(fields["portfolio_truth_source_snapshot_hash"], "A" * 64)

    def test_runner_portfolio_fields_fall_back_when_current_truth_cycle_is_stale(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "stale_portfolio"
            current_truth_path = long_runner.paper_portfolio_current_truth_path(root, session_id)
            current_truth_path.parent.mkdir(parents=True, exist_ok=True)
            current_truth_path.write_text(
                json.dumps(
                    {
                        "source_runtime_cycle_id": "old-cycle",
                        "snapshot_hash": "A" * 64,
                        "cash_available": "880000",
                        "equity": "990000",
                        "live_order_allowed": False,
                    }
                ),
                encoding="utf-8",
            )
            runtime_cycle = {
                "cycle_id": "cycle-2",
                "paper_portfolio_snapshot": {
                    "open_position_count": 1,
                    "cash_available": "1000000",
                    "equity": "1005000",
                    "realized_pnl": "0",
                    "unrealized_pnl": "5000",
                    "snapshot_hash": "C" * 64,
                },
            }

            fields = long_runner._portfolio_fields(root, session_id, runtime_cycle)

            self.assertEqual(fields["cash"], "1000000")
            self.assertEqual(fields["equity"], "1005000")
            self.assertEqual(fields["portfolio_truth_source"], "runtime_cycle.paper_portfolio_snapshot")
            self.assertEqual(fields["portfolio_truth_binding_status"], "FALLBACK_RUNTIME_CYCLE_SNAPSHOT")
            self.assertEqual(fields["portfolio_truth_source_runtime_cycle_id"], "cycle-2")

    def test_dashboard_refresh_uses_public_rest_continuity_when_runner_uses_public_rest(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        calls = []

        def fake_build_launcher_report(name):
            self.assertEqual(name, "UPBIT_PAPER")
            return {"session_id": "old-session"}

        def fake_write_launcher_runtime_bundle(report, **kwargs):
            calls.append({"report": dict(report), **kwargs})
            return {}

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"TRADER1_UPBIT_PAPER_USE_PUBLIC_REST": "true"}):
                with patch(
                    "trader1.runtime.boot.safe_launcher.build_launcher_report",
                    side_effect=fake_build_launcher_report,
                ), patch(
                    "trader1.runtime.boot.safe_launcher.write_launcher_runtime_bundle",
                    side_effect=fake_write_launcher_runtime_bundle,
                ):
                    long_runner._maybe_refresh_dashboard(Path(tmp), session_id="test-public-rest-dashboard")

        self.assertEqual(calls[0]["report"]["session_id"], "test-public-rest-dashboard")
        self.assertTrue(calls[0]["refresh_upbit_public_rest_continuity"])
        self.assertFalse(calls[0]["refresh_paper_shadow_runtime"])

    def test_runner_executes_repeated_actual_paper_cycles_and_stays_live_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = run_upbit_paper_long_running_runner(
                root=root,
                session_id="test_long_runner",
                runner_id="test-runner",
                cycle_interval_seconds=0,
                max_cycles=2,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
            )
            self.assertEqual(report["runner_status"], RUNNER_STATUS_STOPPED)
            self.assertEqual(report["stop_reason"], "MAX_CYCLES_REACHED")
            self.assertEqual(report["completed_cycle_count"], 2)
            self.assertEqual(report["failed_cycle_count"], 0)
            self.assertTrue(report["actual_long_running_runner"])
            self.assertEqual(report["paper_shadow_runtime_collection_status"], "SHORT_WINDOW_EXECUTED")
            self.assertEqual(report["shadow_completed_cycle_count"], 1)
            self.assertGreater(report["shadow_observation_count"], 0)
            self.assertTrue(report["shadow_actual_persistent_runtime_executed"])
            self.assertIn(report["profitability_evidence_refresh_status"], {"PASS", "COLLECTING"})
            self.assertEqual(report["runtime_sample_history_status"], "PASS")
            self.assertGreater(report["runtime_sample_count"], 0)
            self.assertTrue(report["paper_scope_progress_status"])
            self.assertTrue(report["paper_scope_candidate_id"])
            self.assertTrue(report["paper_scope_strategy_id"])
            self.assertEqual(len(report["paper_scope_parameter_hash"]), 64)
            self.assertGreaterEqual(report["paper_scope_sample_count"], 0)
            self.assertGreaterEqual(report["paper_scope_min_required_sample_count"], 1)
            self.assertEqual(
                report["paper_scope_sample_deficit"],
                max(0, report["paper_scope_min_required_sample_count"] - report["paper_scope_sample_count"]),
            )
            self.assertIn("PAPER", report["paper_scope_next_operator_action"])
            self.assertEqual(report["candidate_scorecard_status"], "PASS")
            self.assertTrue(report["candidate_scorecard_candidate_id"])
            self.assertEqual(report["candidate_scorecard_snapshot_status"], "PASS")
            snapshot_path = Path(report["candidate_scorecard_snapshot_path"])
            self.assertTrue(snapshot_path.exists())
            snapshot = _load_json(snapshot_path)
            self.assertEqual(snapshot["candidate_id"], report["candidate_scorecard_candidate_id"])
            self.assertGreaterEqual(report["symbol_evidence_scorecard_count"], 1)
            self.assertIsInstance(report["symbol_evidence_scorecards_top"], list)
            self.assertIsInstance(report["selected_symbol_evidence_scorecard"], dict)
            self.assertEqual(report["selected_symbol_evidence_scorecard"]["live_order_allowed"], False)
            self.assertIn("last_price", report["selected_symbol_evidence_scorecard"])
            self.assertIn("momentum_pct", report["symbol_evidence_scorecards_top"][0])
            self.assertIn("source_public_market_data_hash", report["symbol_evidence_scorecards_top"][0])
            self.assertIn("best_recent_failure_feedback_kind", report["symbol_evidence_scorecards_top"][0])
            self.assertIsInstance(report["runtime_quality_feedback_count"], int)
            self.assertGreaterEqual(report["runtime_quality_feedback_count"], 0)
            self.assertIsInstance(report["runtime_quality_feedback_candidate_ids"], list)
            self.assertIsInstance(report["selected_candidate_recent_failure_feedback_kind"], str)
            self.assertTrue(report["paper_scope_continuity_requested"])
            self.assertIn(
                report["paper_scope_continuity_status"],
                {"SELECTED", "MANAGED_POSITION_OVERRIDES_SCOPE_FOCUS"},
            )
            self.assertEqual(report["paper_scope_continuity_requested_candidate_id"], report["paper_scope_candidate_id"])
            self.assertFalse(report["paper_scope_continuity_selected"] and report["live_order_allowed"])
            self.assertIn(report["paper_shadow_evidence_validation_status"], {"PASS", "BLOCKED"})
            self.assertFalse(report["long_run_evidence_eligible"])
            self.assertFalse(report["shadow_long_run_evidence_eligible"])
            for field in (
                "live_order_ready",
                "live_order_allowed",
                "can_live_trade",
                "scale_up_allowed",
                "order_adapter_called",
                "private_endpoint_called",
                "credential_load_attempted",
                "live_key_loaded",
            ):
                self.assertFalse(report[field], field)

            status_path = runner_status_path(root, "test_long_runner")
            self.assertTrue(status_path.exists())
            loaded = _load_json(status_path)
            self.assertEqual(loaded["status_hash"], upbit_paper_long_runner_status_hash(loaded))
            self.assertEqual(validate_upbit_paper_long_runner_status_report(loaded)["status"], "PASS")
            self.assertIsNotNone(loaded["current_cycle_id"])
            self.assertIn(loaded["last_decision"], {"ENTER_LONG", "NO_TRADE", "EXIT_LONG", "HOLD_POSITION"})
            self.assertEqual(loaded["artifact_retention_status"], "PASS")
            self.assertEqual(loaded["disk_pressure_status"], "PASS")
            self.assertFalse(loaded["dashboard_open_attempted"])
            self.assertFalse(loaded["dashboard_opened"])
            self.assertEqual(loaded["dashboard_open_method"], "NOT_ATTEMPTED")
            self.assertGreaterEqual(loaded["symbol_evidence_scorecard_count"], 1)
            self.assertEqual(loaded["symbol_evidence_scorecards_top"][0]["live_order_allowed"], False)
            self.assertIn("last_price", loaded["symbol_evidence_scorecards_top"][0])
            self.assertIn("best_recent_failure_feedback_kind", loaded["symbol_evidence_scorecards_top"][0])
            self.assertIsInstance(loaded["runtime_quality_feedback_count"], int)
            self.assertGreaterEqual(loaded["runtime_quality_feedback_count"], 0)
            self.assertIsInstance(loaded["runtime_quality_feedback_candidate_ids"], list)
            self.assertIsInstance(loaded["selected_candidate_recent_failure_feedback_kind"], str)
            self.assertEqual(loaded["paper_scope_continuity_status"], report["paper_scope_continuity_status"])
            self.assertTrue(loaded["paper_scope_continuity_requested"])
            self.assertEqual(
                loaded["paper_scope_continuity_requested_candidate_id"],
                report["paper_scope_continuity_requested_candidate_id"],
            )
            self.assertEqual(loaded["candidate_scorecard_candidate_id"], report["candidate_scorecard_candidate_id"])
            self.assertEqual(loaded["paper_scope_candidate_id"], report["paper_scope_candidate_id"])
            self.assertEqual(loaded["paper_scope_sample_deficit"], report["paper_scope_sample_deficit"])
            self.assertEqual(loaded["candidate_scorecard_snapshot_status"], "PASS")
            self.assertTrue(
                paper_candidate_scorecard_snapshot_path(
                    root,
                    "test_long_runner",
                    loaded["candidate_scorecard_candidate_id"],
                ).exists()
            )
            self.assertTrue(runner_retention_manifest_path(root, "test_long_runner").exists())
            self.assertTrue(shadow_persistent_runtime_path(root, "test_long_runner").exists())
            self.assertTrue(shadow_runtime_harness_path(root, "test_long_runner").exists())
            self.assertTrue(shadow_runtime_orchestration_path(root, "test_long_runner").exists())
            self.assertTrue(paper_shadow_harness_binding_path(root, "test_long_runner").exists())
            self.assertTrue(paper_runtime_sample_history_path(root, "test_long_runner").exists())
            self.assertTrue(paper_candidate_scorecard_path(root, "test_long_runner").exists())
            self.assertTrue(paper_overfit_diagnostic_path(root, "test_long_runner").exists())
            self.assertTrue(paper_shadow_evidence_accumulation_path(root, "test_long_runner").exists())
            self.assertFalse(runner_lock_path(root, "test_long_runner").exists())

    def test_runner_status_records_dashboard_open_result_while_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = DashboardOpenResult(
                attempted=True,
                opened=True,
                method="webbrowser.open",
                target="file:///tmp/dashboard/index.html",
                path=str(runner_dashboard_path(root, "test_dashboard_open_status")),
            )

            report = run_upbit_paper_long_running_runner(
                root=root,
                session_id="test_dashboard_open_status",
                runner_id="test-dashboard-open-status",
                cycle_interval_seconds=0,
                max_cycles=1,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
                dashboard_open_result=result,
            )

            self.assertEqual(report["runner_status"], RUNNER_STATUS_STOPPED)
            self.assertTrue(report["dashboard_open_attempted"])
            self.assertTrue(report["dashboard_opened"])
            self.assertEqual(report["dashboard_open_method"], "webbrowser.open")
            loaded = _load_json(runner_status_path(root, "test_dashboard_open_status"))
            self.assertTrue(loaded["dashboard_open_attempted"])
            self.assertTrue(loaded["dashboard_opened"])
            self.assertEqual(loaded["dashboard_open_target"], "file:///tmp/dashboard/index.html")
            self.assertEqual(validate_upbit_paper_long_runner_status_report(loaded)["status"], "PASS")
            self.assertFalse(loaded["live_order_allowed"])
            self.assertFalse(loaded["can_live_trade"])

    def test_runner_blocks_when_non_live_profitability_refresh_integrity_fails(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = long_runner.refresh_non_live_profitability_evidence_from_runtime
            try:
                long_runner.refresh_non_live_profitability_evidence_from_runtime = lambda root, session_id: {
                    "status": "BLOCKED",
                    "blocker_code": "SCHEMA_IDENTITY_MISMATCH",
                    "message": "test injected profitability evidence integrity failure",
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }
                report = run_upbit_paper_long_running_runner(
                    root=root,
                    session_id="test_profitability_refresh_blocked",
                    runner_id="test-profitability-refresh-blocked",
                    cycle_interval_seconds=0,
                    max_cycles=1,
                    attempt_public_symbol_discovery=False,
                    attempt_network_market_data=False,
                    refresh_dashboard=False,
                )
            finally:
                long_runner.refresh_non_live_profitability_evidence_from_runtime = original

            self.assertEqual(report["runner_status"], RUNNER_STATUS_BLOCKED)
            self.assertEqual(report["stop_reason"], "NON_LIVE_PROFITABILITY_EVIDENCE_REFRESH_BLOCKED")
            self.assertEqual(report["primary_blocker_code"], "SCHEMA_IDENTITY_MISMATCH")
            self.assertFalse(report["live_order_allowed"])

    def test_duplicate_runner_start_is_fail_closed_without_overwriting_canonical_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = acquire_runner_lock(root, "locked_session")
            try:
                self.assertTrue(lock.acquired)
                report = run_upbit_paper_long_running_runner(
                    root=root,
                    session_id="locked_session",
                    runner_id="duplicate-runner",
                    cycle_interval_seconds=0,
                    max_cycles=1,
                    attempt_public_symbol_discovery=False,
                    attempt_network_market_data=False,
                    refresh_dashboard=False,
                )
            finally:
                release_runner_lock(lock)

            self.assertEqual(report["runner_status"], RUNNER_STATUS_LOCKED)
            self.assertEqual(report["primary_blocker_code"], LOCK_BLOCKER_CODE)
            self.assertEqual(report["completed_cycle_count"], 0)
            self.assertFalse(report["live_order_allowed"])
            self.assertFalse(runner_status_path(root, "locked_session").exists())
            blocked_path = runner_blocked_start_status_path(root, "locked_session")
            self.assertTrue(blocked_path.exists())
            self.assertEqual(_load_json(blocked_path)["primary_blocker_code"], LOCK_BLOCKER_CODE)

    def test_dead_pid_lock_is_reclaimed_without_waiting_for_heartbeat_staleness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock_path = runner_lock_path(root, "dead_pid_session")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(
                json.dumps(
                    {
                        "schema_id": "trader1.upbit_paper_long_runner_lock.v1",
                        "owner_token": "dead-pid",
                        "pid": 99999999,
                        "session_id": "dead_pid_session",
                        "acquired_at": utc_now(),
                        "heartbeat_at": utc_now(),
                    }
                ),
                encoding="utf-8",
            )

            lock = acquire_runner_lock(root, "dead_pid_session", stale_after_seconds=3600)
            try:
                self.assertTrue(lock.acquired)
                self.assertNotEqual(lock.owner_token, "dead-pid")
            finally:
                release_runner_lock(lock)

    def test_stop_file_before_first_cycle_exits_cleanly_without_cycle_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stop_path = runner_stop_file_path(root, "stop_session")
            stop_path.parent.mkdir(parents=True, exist_ok=True)
            stop_path.write_text(f"stop requested at {utc_now()} by test pid {os.getpid()}\n", encoding="utf-8")
            report = run_upbit_paper_long_running_runner(
                root=root,
                session_id="stop_session",
                runner_id="stop-runner",
                cycle_interval_seconds=0,
                max_cycles=None,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
            )
            self.assertEqual(report["runner_status"], RUNNER_STATUS_STOPPED)
            self.assertEqual(report["stop_reason"], "STOP_FILE")
            self.assertEqual(report["completed_cycle_count"], 0)
            self.assertEqual(validate_upbit_paper_long_runner_status_report(report)["status"], "PASS")

    def test_operator_stop_request_writes_paper_only_stop_signal_for_active_runner(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "operator_stop_session"
            lock = acquire_runner_lock(root, session_id)
            self.assertTrue(lock.acquired)
            try:
                status = build_runner_status_report(
                    root=root,
                    runner_id="operator-stop-runner",
                    session_id=session_id,
                    runner_status=RUNNER_STATUS_RUNNING,
                    started_at_utc=utc_now(),
                    completed_cycle_count=0,
                    failed_cycle_count=0,
                    cycle_interval_seconds=30,
                )
                long_runner._write_runner_status(runner_status_path(root, session_id), status)

                stop_report = request_upbit_paper_runner_stop(
                    root,
                    session_id,
                    wait_timeout_seconds=0,
                    sleep_fn=lambda _seconds: None,
                )
                stop_signal = _load_json(runner_stop_file_path(root, session_id))
                persisted = _load_json(runner_stop_request_report_path(root, session_id))

                self.assertEqual(stop_report["stop_request_status"], "STOP_REQUESTED")
                self.assertTrue(stop_report["stop_file_written"])
                self.assertFalse(stop_report["stop_confirmed"])
                self.assertEqual(persisted["stop_request_hash"], stop_report["stop_request_hash"])
                self.assertEqual(stop_signal["mode"], "PAPER")
                for field in (
                    "live_order_ready",
                    "live_order_allowed",
                    "can_live_trade",
                    "scale_up_allowed",
                    "order_adapter_called",
                    "private_endpoint_called",
                    "credential_load_attempted",
                    "live_key_loaded",
                    "order_endpoint_called",
                ):
                    self.assertFalse(stop_report[field], field)
                    self.assertFalse(stop_signal[field], field)
            finally:
                release_runner_lock(lock)

    def test_operator_stop_request_without_runner_does_not_leave_future_stop_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "no_runner_stop_session"
            stop_path = runner_stop_file_path(root, session_id)
            stop_path.parent.mkdir(parents=True, exist_ok=True)
            stop_path.write_text("stale stop\n", encoding="utf-8")

            stop_report = request_upbit_paper_runner_stop(
                root,
                session_id,
                wait_timeout_seconds=0,
                sleep_fn=lambda _seconds: None,
            )

            self.assertEqual(stop_report["stop_request_status"], "NO_RUNNING_RUNNER")
            self.assertTrue(stop_report["stop_confirmed"])
            self.assertTrue(stop_report["stop_file_cleared_as_stale"])
            self.assertFalse(stop_path.exists())
            self.assertFalse(stop_report["live_order_allowed"])

    def test_operator_start_reconciliation_clears_stale_stop_file_before_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stop_path = runner_stop_file_path(root, "restart_session")
            stop_path.parent.mkdir(parents=True, exist_ok=True)
            stop_path.write_text(f"stop requested at {utc_now()} by test pid {os.getpid()}\n", encoding="utf-8")

            reconciliation = clear_runner_stop_file_for_operator_start(
                root,
                "restart_session",
                reason="TEST_OPERATOR_RESTART",
            )

            self.assertEqual(reconciliation["status"], "PASS")
            self.assertTrue(reconciliation["stop_file_present_before"])
            self.assertTrue(reconciliation["stop_file_cleared"])
            self.assertFalse(stop_path.exists())
            self.assertTrue(runner_start_reconciliation_path(root, "restart_session").exists())
            for field in (
                "live_order_ready",
                "live_order_allowed",
                "can_live_trade",
                "scale_up_allowed",
                "order_adapter_called",
                "private_endpoint_called",
                "credential_load_attempted",
                "live_key_loaded",
            ):
                self.assertFalse(reconciliation[field], field)

            report = run_upbit_paper_long_running_runner(
                root=root,
                session_id="restart_session",
                runner_id="restart-runner",
                cycle_interval_seconds=0,
                max_cycles=1,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
            )
            self.assertEqual(report["runner_status"], RUNNER_STATUS_STOPPED)
            self.assertEqual(report["stop_reason"], "MAX_CYCLES_REACHED")
            self.assertEqual(report["completed_cycle_count"], 1)
            self.assertEqual(report["failed_cycle_count"], 0)
            self.assertFalse(report["live_order_allowed"])

    def test_root_operator_start_clears_stale_stop_file_before_runner_call(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stop_path = runner_stop_file_path(root)
            stop_path.parent.mkdir(parents=True, exist_ok=True)
            stop_path.write_text(f"stop requested at {utc_now()} by test pid {os.getpid()}\n", encoding="utf-8")
            observed: dict[str, bool] = {}

            def fake_run(**kwargs):
                observed["stop_file_exists_at_runner_call"] = runner_stop_file_path(kwargs["root"]).exists()
                return {
                    "runner_status": RUNNER_STATUS_STOPPED,
                    "runner_status_path": str(runner_status_path(kwargs["root"])),
                    "dashboard_path": str(runner_dashboard_path(kwargs["root"])),
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }

            with patch.dict(
                os.environ,
                {
                    "TRADER1_UPBIT_PAPER_SAFE_CHECK_ONLY": "false",
                    "TRADER1_UPBIT_PAPER_REFRESH_DASHBOARD": "false",
                    "TRADER1_UPBIT_PAPER_OPEN_DASHBOARD": "false",
                    "TRADER1_UPBIT_PAPER_HOLD_ON_EXIT": "false",
                },
            ), patch.object(long_runner, "run_upbit_paper_long_running_runner", side_effect=fake_run):
                exit_code = long_runner.root_upbit_paper_long_runner_main(root)

            self.assertEqual(exit_code, 0)
            self.assertFalse(observed["stop_file_exists_at_runner_call"])
            self.assertFalse(stop_path.exists())
            self.assertTrue(runner_start_reconciliation_path(root).exists())

    def test_root_operator_duplicate_start_does_not_clear_active_stop_request(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stop_path = runner_stop_file_path(root)
            stop_path.parent.mkdir(parents=True, exist_ok=True)
            lock = acquire_runner_lock(root, "mvp1_upbit_paper_launcher")
            self.assertTrue(lock.acquired)
            try:
                status = build_runner_status_report(
                    root=root,
                    runner_id="already-running",
                    session_id="mvp1_upbit_paper_launcher",
                    runner_status=RUNNER_STATUS_RUNNING,
                    started_at_utc=utc_now(),
                    completed_cycle_count=0,
                    failed_cycle_count=0,
                    cycle_interval_seconds=30,
                )
                long_runner._write_runner_status(runner_status_path(root), status)
                stop_path.write_text("operator stop already requested\n", encoding="utf-8")
                observed: dict[str, bool] = {}

                def fake_run(**kwargs):
                    observed["stop_file_exists_at_runner_call"] = runner_stop_file_path(kwargs["root"]).exists()
                    return build_runner_status_report(
                        root=kwargs["root"],
                        runner_id="duplicate-start",
                        session_id="mvp1_upbit_paper_launcher",
                        runner_status=RUNNER_STATUS_LOCKED,
                        started_at_utc=utc_now(),
                        completed_cycle_count=0,
                        failed_cycle_count=0,
                        cycle_interval_seconds=30,
                        primary_blocker_code=LOCK_BLOCKER_CODE,
                        primary_blocker_message="Another runner owns this session lock.",
                    )

                with patch.dict(
                    os.environ,
                    {
                        "TRADER1_UPBIT_PAPER_SAFE_CHECK_ONLY": "false",
                        "TRADER1_UPBIT_PAPER_REFRESH_DASHBOARD": "false",
                        "TRADER1_UPBIT_PAPER_OPEN_DASHBOARD": "false",
                        "TRADER1_UPBIT_PAPER_HOLD_ON_EXIT": "false",
                    },
                ), patch.object(long_runner, "run_upbit_paper_long_running_runner", side_effect=fake_run):
                    exit_code = long_runner.root_upbit_paper_long_runner_main(root)

                self.assertEqual(exit_code, 0)
                self.assertTrue(observed["stop_file_exists_at_runner_call"])
                self.assertTrue(stop_path.exists())
                self.assertFalse(status["live_order_allowed"])
            finally:
                release_runner_lock(lock)

    def test_root_operator_start_does_not_open_stale_dashboard_when_preopen_refresh_fails(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            observed: dict[str, DashboardOpenResult | None] = {}

            def fake_run(**kwargs):
                observed["dashboard_open_result"] = kwargs.get("dashboard_open_result")
                report = long_runner.build_runner_status_report(
                    root=kwargs["root"],
                    runner_id="test-preopen-dashboard-refresh-failed",
                    session_id="mvp1_upbit_paper_launcher",
                    runner_status=RUNNER_STATUS_STOPPED,
                    started_at_utc=utc_now(),
                    completed_cycle_count=0,
                    failed_cycle_count=0,
                    cycle_interval_seconds=0,
                    stop_reason="TEST_PREOPEN_REFRESH_FAILED",
                    dashboard_open_result=kwargs.get("dashboard_open_result"),
                )
                status_path = runner_status_path(kwargs["root"])
                status_path.parent.mkdir(parents=True, exist_ok=True)
                status_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
                return report

            with patch.dict(
                os.environ,
                {
                    "TRADER1_UPBIT_PAPER_SAFE_CHECK_ONLY": "false",
                    "TRADER1_UPBIT_PAPER_REFRESH_DASHBOARD": "true",
                    "TRADER1_UPBIT_PAPER_OPEN_DASHBOARD": "true",
                    "TRADER1_UPBIT_PAPER_HOLD_ON_EXIT": "false",
                },
            ), patch.object(
                long_runner,
                "_maybe_refresh_dashboard",
                side_effect=RuntimeError("test refresh failure"),
            ), patch.object(
                long_runner,
                "open_runner_dashboard_result",
            ) as open_mock, patch.object(
                long_runner,
                "run_upbit_paper_long_running_runner",
                side_effect=fake_run,
            ):
                exit_code = long_runner.root_upbit_paper_long_runner_main(root)

            self.assertEqual(exit_code, 0)
            open_mock.assert_not_called()
            dashboard_open_result = observed["dashboard_open_result"]
            self.assertIsNotNone(dashboard_open_result)
            assert dashboard_open_result is not None
            self.assertTrue(dashboard_open_result.attempted)
            self.assertFalse(dashboard_open_result.opened)
            self.assertEqual(dashboard_open_result.method, "PRE_OPEN_REFRESH_FAILED")
            self.assertEqual(
                dashboard_open_result.blocker_code,
                long_runner.DASHBOARD_PREOPEN_REFRESH_FAILED_BLOCKER_CODE,
            )
            self.assertIn("test refresh failure", str(dashboard_open_result.blocker_message))

            loaded = _load_json(runner_status_path(root))
            self.assertEqual(validate_upbit_paper_long_runner_status_report(loaded)["status"], "PASS")
            self.assertTrue(loaded["dashboard_open_attempted"])
            self.assertFalse(loaded["dashboard_opened"])
            self.assertEqual(loaded["dashboard_open_method"], "PRE_OPEN_REFRESH_FAILED")
            self.assertEqual(
                loaded["dashboard_open_blocker_code"],
                long_runner.DASHBOARD_PREOPEN_REFRESH_FAILED_BLOCKER_CODE,
            )
            for field in (
                "live_order_ready",
                "live_order_allowed",
                "can_live_trade",
                "scale_up_allowed",
                "order_adapter_called",
                "private_endpoint_called",
                "credential_load_attempted",
                "live_key_loaded",
            ):
                self.assertFalse(loaded[field], field)

    def test_root_operator_start_treats_verified_running_runner_as_success(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = run_upbit_paper_long_running_runner(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                runner_id="canonical-running-seed",
                cycle_interval_seconds=0,
                max_cycles=0,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
            )
            canonical["runner_status"] = "RUNNING"
            canonical["running"] = True
            lock_path = runner_lock_path(root)
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(
                json.dumps(
                    {
                        "schema_id": "trader1.upbit_paper_long_runner_lock.v1",
                        "owner_token": f"canonical-running-{os.getpid()}",
                        "pid": os.getpid(),
                        "session_id": "mvp1_upbit_paper_launcher",
                        "acquired_at": utc_now(),
                        "heartbeat_at": utc_now(),
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            canonical["status_hash"] = upbit_paper_long_runner_status_hash(canonical)
            runner_status_path(root).write_text(json.dumps(canonical, sort_keys=True, indent=2), encoding="utf-8")

            def fake_run(**kwargs):
                return {
                    "runner_status": RUNNER_STATUS_LOCKED,
                    "runner_status_path": str(runner_status_path(kwargs["root"])),
                    "dashboard_path": str(runner_dashboard_path(kwargs["root"])),
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }

            with patch.dict(
                os.environ,
                {
                    "TRADER1_UPBIT_PAPER_SAFE_CHECK_ONLY": "false",
                    "TRADER1_UPBIT_PAPER_REFRESH_DASHBOARD": "false",
                    "TRADER1_UPBIT_PAPER_OPEN_DASHBOARD": "false",
                    "TRADER1_UPBIT_PAPER_HOLD_ON_EXIT": "false",
                },
            ), patch.object(long_runner, "run_upbit_paper_long_running_runner", side_effect=fake_run):
                exit_code = root_upbit_paper_long_runner_main(root)

            self.assertEqual(exit_code, 0)
            self.assertEqual(validate_upbit_paper_long_runner_status_report(_load_json(runner_status_path(root)))["status"], "PASS")
            self.assertFalse(_load_json(runner_status_path(root))["live_order_allowed"])

    def test_root_operator_start_does_not_accept_dead_pid_running_status_as_success(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = run_upbit_paper_long_running_runner(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                runner_id="canonical-dead-running-seed",
                cycle_interval_seconds=0,
                max_cycles=0,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
            )
            canonical["runner_status"] = "RUNNING"
            canonical["running"] = True
            lock_path = runner_lock_path(root)
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(
                json.dumps(
                    {
                        "schema_id": "trader1.upbit_paper_long_runner_lock.v1",
                        "owner_token": "canonical-dead-pid",
                        "pid": 99999999,
                        "session_id": "mvp1_upbit_paper_launcher",
                        "acquired_at": utc_now(),
                        "heartbeat_at": utc_now(),
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            canonical["status_hash"] = upbit_paper_long_runner_status_hash(canonical)
            runner_status_path(root).write_text(json.dumps(canonical, sort_keys=True, indent=2), encoding="utf-8")

            def fake_run(**kwargs):
                return {
                    "runner_status": RUNNER_STATUS_LOCKED,
                    "runner_status_path": str(runner_status_path(kwargs["root"])),
                    "dashboard_path": str(runner_dashboard_path(kwargs["root"])),
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }

            with patch.dict(
                os.environ,
                {
                    "TRADER1_UPBIT_PAPER_SAFE_CHECK_ONLY": "false",
                    "TRADER1_UPBIT_PAPER_REFRESH_DASHBOARD": "false",
                    "TRADER1_UPBIT_PAPER_OPEN_DASHBOARD": "false",
                    "TRADER1_UPBIT_PAPER_HOLD_ON_EXIT": "false",
                },
            ), patch.object(long_runner, "run_upbit_paper_long_running_runner", side_effect=fake_run):
                exit_code = root_upbit_paper_long_runner_main(root)

            self.assertEqual(exit_code, 1)
            self.assertEqual(validate_upbit_paper_long_runner_status_report(_load_json(runner_status_path(root)))["status"], "PASS")
            self.assertFalse(_load_json(runner_status_path(root))["live_order_allowed"])

    def test_runner_recovers_legacy_no_position_cycle_missing_runtime_risk_exit_lifecycle_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "legacy_no_position_session"
            seed = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="legacy-seed",
                session_id=session_id,
                requested_cycle_count=1,
                max_cycle_count=1,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
            )
            self.assertEqual(seed["loop_status"], "PASS")
            latest_path = root / "system/runtime/upbit/krw_spot/paper" / session_id / "upbit_paper_runtime_cycle_report.json"
            latest = _load_json(latest_path)
            for field in ("risk_state", "exit_plan", "position_management_decision"):
                latest.pop(field, None)
            latest["final_decision"] = "NO_TRADE"
            latest["paper_fill"] = None
            latest["paper_ledger_events"] = []
            latest["no_trade_reasons"] = ["LEGACY_NO_POSITION_SCHEMA_REGENERATION"]
            latest["entry_reasons"] = []
            latest["paper_portfolio_snapshot"]["open_position_count"] = 0
            latest["cycle_hash"] = upbit_paper_runtime_cycle_hash(latest)
            latest_path.write_text(json.dumps(latest, sort_keys=True, indent=2), encoding="utf-8")

            report = run_upbit_paper_long_running_runner(
                root=root,
                session_id=session_id,
                runner_id="legacy-recovery-runner",
                cycle_interval_seconds=0,
                max_cycles=1,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
            )
            self.assertEqual(report["runner_status"], RUNNER_STATUS_STOPPED)
            self.assertEqual(report["completed_cycle_count"], 1)
            self.assertEqual(report["failed_cycle_count"], 0)
            self.assertFalse(report["live_order_allowed"])

    def test_runner_status_validation_blocks_live_flag_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = run_upbit_paper_long_running_runner(
                root=root,
                session_id="mutation_session",
                runner_id="mutation-runner",
                cycle_interval_seconds=0,
                max_cycles=0,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
            )
            mutated = dict(report)
            mutated["live_order_allowed"] = True
            mutated["status_hash"] = upbit_paper_long_runner_status_hash(mutated)
            validation = validate_upbit_paper_long_runner_status_report(mutated)
            self.assertEqual(validation["status"], "BLOCKED")
            self.assertEqual(validation["blocker_code"], "RUNNER_STATUS_LIVE_FLAG_MUTATED")

    def test_runner_status_validation_blocks_missing_candidate_scorecard_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = run_upbit_paper_long_running_runner(
                root=root,
                session_id="snapshot_missing_session",
                runner_id="snapshot-missing-runner",
                cycle_interval_seconds=0,
                max_cycles=1,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
            )
            mutated = dict(report)
            mutated["candidate_scorecard_snapshot_status"] = "NOT_LOADED"
            mutated["candidate_scorecard_snapshot_blocker_code"] = "SCORECARD_SNAPSHOT_MISSING"
            mutated["status_hash"] = upbit_paper_long_runner_status_hash(mutated)
            validation = validate_upbit_paper_long_runner_status_report(mutated)
            self.assertEqual(validation["status"], "BLOCKED")
            self.assertEqual(validation["blocker_code"], "SCORECARD_SNAPSHOT_MISSING")

            startup_view = dict(mutated)
            startup_view["completed_cycle_count"] = 0
            startup_view["status_hash"] = upbit_paper_long_runner_status_hash(startup_view)
            self.assertEqual(validate_upbit_paper_long_runner_status_report(startup_view)["status"], "PASS")

    def test_runner_retention_archives_old_cycle_artifacts_and_rotates_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "retention_session"
            cycle_dir = root / "system/runtime/upbit/krw_spot/paper" / session_id / "paper_runtime" / "cycles"
            cycle_dir.mkdir(parents=True, exist_ok=True)
            for index in range(4):
                path = cycle_dir / f"upbit-paper-runner-old-cycle-{index:06d}-cycle-1.runtime_cycle.json"
                path.write_text(json.dumps({"index": index}), encoding="utf-8")
                os.utime(path, (1_700_000_000 + index, 1_700_000_000 + index))
            log_path = root / "system/runtime/upbit/krw_spot/paper" / session_id / "paper_runtime" / "runner" / "runner_events.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("x" * 128, encoding="utf-8")

            manifest = apply_runner_artifact_retention(
                root=root,
                session_id=session_id,
                max_active_artifacts_per_group=2,
                log_max_bytes=32,
                disk_pressure_max_runtime_bytes=1_000_000,
            )

            validation = validate_upbit_paper_long_runner_retention_manifest(manifest)
            remaining = sorted(cycle_dir.glob("*.runtime_cycle.json"))
            archived_paths = [root / item["archive_path"] for item in manifest["archived_artifacts"]]
            self.assertEqual(validation["status"], "PASS")
            self.assertEqual(manifest["retention_status"], "PASS")
            self.assertEqual(len(remaining), 2)
            self.assertLess(manifest["runtime_artifact_count_after"], manifest["runtime_artifact_count_before"])
            self.assertLess(manifest["runtime_artifact_bytes_after"], manifest["total_runtime_artifact_bytes_after"])
            self.assertGreaterEqual(manifest["archive_artifact_count_after"], 1)
            self.assertGreaterEqual(manifest["archived_artifact_count"], 3)
            self.assertTrue(all(path.exists() for path in archived_paths))
            self.assertFalse(log_path.exists())
            self.assertFalse(manifest["live_order_allowed"])

    def test_runner_retention_reports_managed_artifacts_separately_from_legacy_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "retention_managed_session"
            base = root / "system/runtime/upbit/krw_spot/paper" / session_id
            cycle_dir = base / "paper_runtime" / "cycles"
            cycle_dir.mkdir(parents=True, exist_ok=True)
            for index in range(3):
                path = cycle_dir / f"upbit-paper-runner-managed-cycle-{index:06d}.runtime_cycle.json"
                path.write_text(json.dumps({"index": index}), encoding="utf-8")
                os.utime(path, (1_700_000_000 + index, 1_700_000_000 + index))
            legacy_path = base / "dashboard" / "index.html"
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_path.write_text("<html>legacy tracked runtime snapshot</html>", encoding="utf-8")

            manifest = apply_runner_artifact_retention(
                root=root,
                session_id=session_id,
                max_active_artifacts_per_group=1,
                log_max_bytes=128,
                disk_pressure_max_runtime_bytes=1_000_000,
            )

            validation = validate_upbit_paper_long_runner_retention_manifest(manifest)
            self.assertEqual(validation["status"], "PASS")
            self.assertEqual(manifest["runtime_artifact_count_after"], 1)
            self.assertGreater(manifest["active_runtime_tree_artifact_count_after"], manifest["runtime_artifact_count_after"])
            self.assertEqual(manifest["unmanaged_runtime_artifact_count_after"], 1)
            self.assertEqual(manifest["active_group_counts"]["paper_runtime_cycles"], 1)
            self.assertGreaterEqual(manifest["archived_artifact_count"], 2)
            self.assertFalse(manifest["live_order_allowed"])

    def test_runner_retention_keeps_latest_public_collection_pointer_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "retention_public_pointer_session"
            public_base = root / "system/runtime/upbit/krw_spot/paper" / session_id / "market_data" / "public"
            protected_collector = "upbit-paper-runner-protected-cycle-000001-collector-1-1-KRW-BTC"
            protected_report = public_base / "collection" / f"{protected_collector}.collection_report.json"
            for directory in ("raw", "canonical", "collection"):
                (public_base / directory).mkdir(parents=True, exist_ok=True)

            for index in range(4):
                collector = protected_collector if index == 0 else f"upbit-paper-runner-public-cycle-00000{index}-collector-1-{index}-KRW-ALT"
                (public_base / "raw" / f"{collector}.raw_candles.json").write_text(json.dumps({"collector_id": collector}), encoding="utf-8")
                (public_base / "canonical" / f"{collector}.canonical_events.jsonl").write_text(
                    json.dumps({"collector_id": collector}) + "\n",
                    encoding="utf-8",
                )
                report_path = public_base / "collection" / f"{collector}.collection_report.json"
                report_path.write_text(json.dumps({"collector_id": collector}), encoding="utf-8")
                (public_base / "collection" / f"{collector}.writer_report.json").write_text(
                    json.dumps({"collector_id": collector}),
                    encoding="utf-8",
                )
                os.utime(report_path, (1_700_000_000 + index, 1_700_000_000 + index))

            (public_base / "latest_collection_report.json").write_text(
                json.dumps(
                    {
                        "collector_id": protected_collector,
                        "report_path": protected_report.relative_to(root).as_posix(),
                    }
                ),
                encoding="utf-8",
            )

            manifest = apply_runner_artifact_retention(
                root=root,
                session_id=session_id,
                max_active_artifacts_per_group=1,
                log_max_bytes=128,
                disk_pressure_max_runtime_bytes=1_000_000,
            )

            validation = validate_upbit_paper_long_runner_retention_manifest(manifest)
            protected_paths = [
                public_base / "raw" / f"{protected_collector}.raw_candles.json",
                public_base / "canonical" / f"{protected_collector}.canonical_events.jsonl",
                protected_report,
                public_base / "collection" / f"{protected_collector}.writer_report.json",
            ]
            self.assertEqual(validation["status"], "PASS")
            self.assertTrue(all(path.exists() for path in protected_paths))
            self.assertEqual(manifest["effective_active_group_limits"]["public_collection_reports"], 1)
            self.assertGreater(manifest["active_group_counts"]["public_collection_reports"], 1)
            self.assertGreater(manifest["archived_artifact_count"], 0)
            self.assertFalse(manifest["live_order_allowed"])

    def test_runner_retention_compacts_old_archive_batches_outside_active_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "retention_compaction_session"
            cycle_dir = root / "system/runtime/upbit/krw_spot/paper" / session_id / "paper_runtime" / "cycles"
            cycle_dir.mkdir(parents=True, exist_ok=True)
            for index in range(3):
                path = cycle_dir / f"upbit-paper-runner-live-cycle-{index:06d}-cycle-1.runtime_cycle.json"
                path.write_text(json.dumps({"index": index}), encoding="utf-8")
                os.utime(path, (1_700_000_100 + index, 1_700_000_100 + index))
            archive_root = (
                root
                / "system/runtime/upbit/krw_spot/paper"
                / session_id
                / "paper_runtime"
                / "runner"
                / "archive"
            )
            old_batch = archive_root / "runner-retention-20260501T000000Z"
            newer_batch = archive_root / "runner-retention-20260502T000000Z"
            old_batch.mkdir(parents=True, exist_ok=True)
            newer_batch.mkdir(parents=True, exist_ok=True)
            (old_batch / "old.json").write_text(json.dumps({"old": True}), encoding="utf-8")
            (newer_batch / "newer.json").write_text(json.dumps({"newer": True}), encoding="utf-8")
            os.utime(old_batch, (1_700_000_000, 1_700_000_000))
            os.utime(newer_batch, (1_700_000_010, 1_700_000_010))

            manifest = apply_runner_artifact_retention(
                root=root,
                session_id=session_id,
                max_active_artifacts_per_group=2,
                max_uncompacted_archive_batches=1,
                log_max_bytes=128,
                disk_pressure_max_runtime_bytes=1_000_000,
            )

            validation = validate_upbit_paper_long_runner_retention_manifest(manifest)
            remaining = sorted(cycle_dir.glob("*.runtime_cycle.json"))
            self.assertEqual(validation["status"], "PASS")
            self.assertEqual(len(remaining), 2)
            self.assertEqual(manifest["runtime_artifact_count_after"], 2)
            self.assertGreaterEqual(manifest["total_runtime_artifact_count_after"], manifest["runtime_artifact_count_after"])
            self.assertGreaterEqual(manifest["compacted_archive_count"], 1)
            self.assertFalse(old_batch.exists())
            compacted_paths = [root / item["compacted_archive_path"] for item in manifest["compacted_archives"]]
            self.assertTrue(all(path.suffix == ".zip" and path.exists() for path in compacted_paths))
            self.assertFalse(manifest["live_order_allowed"])

    def test_runner_blocks_when_runtime_disk_pressure_exceeds_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "disk_pressure_session"
            payload = root / "system/runtime/upbit/krw_spot/paper" / session_id / "paper_runtime" / "cycles" / "large.runtime_cycle.json"
            payload.parent.mkdir(parents=True, exist_ok=True)
            payload.write_text("x" * 128, encoding="utf-8")

            report = run_upbit_paper_long_running_runner(
                root=root,
                session_id=session_id,
                runner_id="disk-pressure-runner",
                cycle_interval_seconds=0,
                max_cycles=1,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=False,
                disk_pressure_max_runtime_bytes=1,
            )

            manifest = _load_json(runner_retention_manifest_path(root, session_id))
            self.assertEqual(report["runner_status"], RUNNER_STATUS_BLOCKED)
            self.assertEqual(report["primary_blocker_code"], DISK_PRESSURE_BLOCKER_CODE)
            self.assertEqual(report["completed_cycle_count"], 0)
            self.assertFalse(report["live_order_allowed"])
            self.assertEqual(manifest["disk_pressure_status"], "BLOCKED")

    def test_runner_continues_when_dashboard_current_writer_unavailable_without_live_drift(self):
        import trader1.runtime.paper.upbit_paper_long_runner as long_runner

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "writer-unavailable-nonblocking-session"
            stale_writer = (
                root
                / "system/runtime/upbit/krw_spot/paper"
                / session_id
                / "paper_runtime/current_evidence/paper_continuous_current_evidence_writer_report.json"
            )
            stale_writer.parent.mkdir(parents=True, exist_ok=True)
            stale_writer.write_text(
                json.dumps(
                    {
                        "schema_id": "trader1.paper_continuous_current_evidence_writer_report.v1",
                        "continuous_writer_status": "INVALID",
                        "primary_blocker_code": "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED",
                        "live_order_ready": False,
                        "live_order_allowed": False,
                        "can_live_trade": False,
                        "scale_up_allowed": False,
                        "order_adapter_called": False,
                        "private_endpoint_called": False,
                        "credential_load_attempted": False,
                        "live_key_loaded": False,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with patch.object(
                long_runner,
                "_maybe_refresh_dashboard",
                side_effect=RuntimeError(
                    "read-only dashboard failed closed validation: "
                    "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED; portfolio values remain UNVERIFIED"
                ),
            ):
                report = run_upbit_paper_long_running_runner(
                    root=root,
                    session_id=session_id,
                    runner_id="writer-unavailable-nonblocking-runner",
                    cycle_interval_seconds=0,
                    max_cycles=2,
                    sleep_fn=lambda _seconds: None,
                    attempt_public_symbol_discovery=False,
                    attempt_network_market_data=False,
                    refresh_dashboard=True,
                    emit_console_status=False,
                )

            events = runner_log_path(root, session_id).read_text(encoding="utf-8")

        self.assertEqual(report["runner_status"], RUNNER_STATUS_STOPPED)
        self.assertEqual(report["completed_cycle_count"], 2)
        self.assertEqual(report["failed_cycle_count"], 0)
        self.assertEqual(report["stop_reason"], "MAX_CYCLES_REACHED")
        self.assertIn("dashboard_refresh_writer_truth_unavailable_nonblocking", events)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_runner_real_dashboard_refresh_continues_with_invalid_writer_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "invalid-writer-real-dashboard-session"
            stale_writer = (
                runner_runtime_base(root, session_id)
                / "paper_runtime/current_evidence/paper_continuous_current_evidence_writer_report.json"
            )
            stale_writer.parent.mkdir(parents=True, exist_ok=True)
            stale_writer.write_text(
                json.dumps(
                    {
                        "schema_id": "trader1.paper_continuous_current_evidence_writer_report.v1",
                        "continuous_writer_status": "INVALID",
                        "primary_blocker_code": "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED",
                        "live_order_ready": False,
                        "live_order_allowed": False,
                        "can_live_trade": False,
                        "scale_up_allowed": False,
                        "order_adapter_called": False,
                        "private_endpoint_called": False,
                        "credential_load_attempted": False,
                        "live_key_loaded": False,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            report = run_upbit_paper_long_running_runner(
                root=root,
                session_id=session_id,
                runner_id="invalid-writer-real-dashboard-runner",
                cycle_interval_seconds=0,
                max_cycles=2,
                sleep_fn=lambda _seconds: None,
                attempt_public_symbol_discovery=False,
                attempt_network_market_data=False,
                refresh_dashboard=True,
                emit_console_status=False,
            )
            dashboard = _load_json(runner_runtime_base(root, session_id) / "dashboard_shell.json")

        self.assertEqual(report["runner_status"], RUNNER_STATUS_STOPPED)
        self.assertEqual(report["completed_cycle_count"], 2)
        self.assertEqual(report["failed_cycle_count"], 0)
        self.assertEqual(report["stop_reason"], "MAX_CYCLES_REACHED")
        self.assertEqual(dashboard["portfolio_snapshot"]["status"], "UNVERIFIED")
        self.assertEqual(
            dashboard["portfolio_snapshot"]["blocking_reason"],
            "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED",
        )
        self.assertEqual(dashboard["operation_status"]["portfolio_status"], "UNVERIFIED")
        runner_status = dashboard["paper_runner_operations_status"]
        self.assertNotIn("attempted live", json.dumps(runner_status).lower())
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["can_live_trade"])

    def test_runner_dashboard_opener_is_read_only_file_uri(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = runner_dashboard_path(root, "dashboard_session")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("<!doctype html><title>TRADER_1</title>", encoding="utf-8")
            opened: list[str] = []

            result = open_runner_dashboard(
                root,
                "dashboard_session",
                opener=lambda uri: opened.append(uri) is None or True,
            )

            self.assertTrue(result)
            self.assertEqual(len(opened), 1)
            self.assertTrue(opened[0].startswith("file:///"))
            self.assertIn("dashboard/index.html", opened[0].replace("%5C", "/").replace("\\", "/"))

    def test_runner_dashboard_open_result_reports_missing_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = open_runner_dashboard_result(root, "missing_dashboard_session")

            self.assertFalse(result.attempted)
            self.assertFalse(result.opened)
            self.assertEqual(result.method, "NOT_ATTEMPTED")
            self.assertEqual(result.blocker_code, "DASHBOARD_FILE_MISSING")

    def test_runner_dashboard_open_result_falls_back_to_startfile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = runner_dashboard_path(root, "fallback_dashboard_session")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("<!doctype html><title>TRADER_1</title>", encoding="utf-8")
            started: list[str] = []

            result = open_runner_dashboard_result(
                root,
                "fallback_dashboard_session",
                opener=lambda _uri: False,
                startfile=lambda target: started.append(target),
            )

            self.assertTrue(result.attempted)
            self.assertTrue(result.opened)
            self.assertEqual(result.method, "os.startfile")
            self.assertEqual(started, [str(path.resolve())])

    def test_runner_dashboard_open_result_exposes_failure_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = runner_dashboard_path(root, "failed_dashboard_session")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("<!doctype html><title>TRADER_1</title>", encoding="utf-8")

            result = open_runner_dashboard_result(
                root,
                "failed_dashboard_session",
                opener=lambda _uri: False,
                startfile=lambda _target: (_ for _ in ()).throw(RuntimeError("blocked")),
            )

            self.assertTrue(result.attempted)
            self.assertFalse(result.opened)
            self.assertEqual(result.method, "FAILED")
            self.assertEqual(result.blocker_code, "DASHBOARD_OPEN_FAILED")
            self.assertIn("fallback failed", result.blocker_message or "")


if __name__ == "__main__":
    unittest.main()
