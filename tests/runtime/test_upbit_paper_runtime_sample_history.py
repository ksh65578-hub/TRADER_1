import json
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper import upbit_paper_runtime_sample_history as sample_history_module
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    build_upbit_paper_runtime_sample_history,
    upbit_paper_runtime_sample_hash,
    upbit_paper_runtime_sample_history_hash,
    validate_upbit_paper_runtime_sample_history,
    validate_upbit_paper_runtime_sample_history_sources,
    write_upbit_paper_runtime_sample_history,
)
from trader1.validation.schema_instance import load_schema_bundle, schema_for_instance, validate_instance_against_schema


ROOT = Path(__file__).resolve().parents[2]


class UpbitPaperRuntimeSampleHistoryTest(unittest.TestCase):
    def _history(self) -> tuple[dict, Path]:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        run_upbit_paper_persistent_loop(root=root, loop_id="sample-history-a", requested_cycle_count=1)
        run_upbit_paper_persistent_loop(root=root, loop_id="sample-history-b", requested_cycle_count=1)
        return build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher"), root

    def test_runtime_sample_history_binds_actual_cycle_files_and_remains_live_blocked(self):
        history, root = self._history()
        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["accepted_cycle_sample_count"], 2)
        self.assertEqual(history["unique_runtime_cycle_hash_count"], 2)
        self.assertEqual(history["runtime_sample_status"], "COLLECTING")
        self.assertEqual(history["history_evidence_role"], "PAPER_RUNTIME_SAMPLE_HISTORY_NOT_LONG_RUN_EVIDENCE")
        self.assertEqual(history["long_run_blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        self.assertEqual(history["min_profitability_scope_sample_count"], 30)
        self.assertGreaterEqual(history["candidate_scope_sample_summary_count"], 1)
        self.assertEqual(history["active_candidate_scope_sample_deficit"], 30 - history["active_candidate_scope_sample_count"])
        self.assertEqual(history["active_candidate_scope_status"], "COLLECT_PAPER_SCOPE_SAMPLES")
        self.assertIn("Collect", history["active_candidate_scope_next_action"])
        active_scope = history["active_candidate_scope"]
        self.assertIsInstance(active_scope, dict)
        self.assertEqual(active_scope["exchange"], "UPBIT")
        self.assertEqual(active_scope["market_type"], "KRW_SPOT")
        self.assertEqual(active_scope["mode"], "PAPER")
        self.assertEqual(active_scope["sample_count"], history["active_candidate_scope_sample_count"])
        self.assertEqual(active_scope["sample_deficit"], history["active_candidate_scope_sample_deficit"])
        self.assertFalse(active_scope["live_order_ready"])
        self.assertFalse(active_scope["live_order_allowed"])
        self.assertFalse(active_scope["can_live_trade"])
        self.assertFalse(active_scope["scale_up_allowed"])
        self.assertFalse(history["actual_long_run_evidence_created"])
        self.assertFalse(history["long_run_evidence_eligible"])
        self.assertFalse(history["promotion_eligible"])
        self.assertFalse(history["live_order_ready"])
        self.assertFalse(history["live_order_allowed"])
        self.assertFalse(history["can_live_trade"])
        self.assertFalse(history["scale_up_allowed"])
        first_sample = history["samples"][0]
        self.assertGreaterEqual(first_sample["candidate_count"], 1)
        self.assertGreaterEqual(first_sample["entry_reason_count"], 1)
        self.assertIn("exit_reason_count", first_sample)
        self.assertEqual(first_sample["scorecard_candidate_identity_binding_status"], "BOUND")
        self.assertEqual(first_sample["scorecard_candidate_live_flags_clear"], True)
        self.assertIsInstance(first_sample["scorecard_candidate_id"], str)
        self.assertIsInstance(first_sample["scorecard_symbol"], str)
        self.assertIsInstance(first_sample["scorecard_strategy_id"], str)
        self.assertEqual(len(first_sample["scorecard_parameter_hash"]), 64)
        self.assertEqual(
            first_sample["paper_entry_review_candidate_count"],
            len(first_sample["paper_entry_review_candidate_ids"]),
        )
        self.assertEqual(
            first_sample["paper_entry_review_symbol_count"],
            len(set(first_sample["paper_entry_review_symbols"])),
        )
        self.assertEqual(history["samples"][1]["previous_sample_hash"], history["samples"][0]["sample_hash"])

        written_path = write_upbit_paper_runtime_sample_history(root=root, history=history)
        written = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_upbit_paper_runtime_sample_history(written).status, "PASS")
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        schema = schema_for_instance(written, schema_bundle)
        self.assertIsNotNone(schema)
        schema_result = validate_instance_against_schema(written, schema, schema_bundle)
        self.assertEqual(schema_result.status, "PASS", schema_result.errors)

    def test_persistent_loop_reuses_active_scope_focus_to_accumulate_candidate_samples(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        first_loop = run_upbit_paper_persistent_loop(root=root, loop_id="sample-history-scope-focus-a", requested_cycle_count=1)
        self.assertEqual(first_loop["loop_status"], "PASS")
        history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        self.assertEqual(validate_upbit_paper_runtime_sample_history_sources(root=root, history=history).status, "PASS")
        focus = history["active_candidate_scope"]
        self.assertIsInstance(focus, dict)

        second_loop = run_upbit_paper_persistent_loop(
            root=root,
            loop_id="sample-history-scope-focus-b",
            requested_cycle_count=1,
            paper_scope_focus=focus,
        )
        self.assertEqual(validate_upbit_paper_persistent_loop_report(second_loop).status, "PASS")
        cycle_result = second_loop["cycle_results"][0]
        self.assertTrue(cycle_result["paper_scope_continuity_requested"])
        self.assertIn(
            cycle_result["paper_scope_continuity_status"],
            {"SELECTED", "MANAGED_POSITION_OVERRIDES_SCOPE_FOCUS"},
        )
        self.assertFalse(cycle_result["live_order_allowed"])

        focused_history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        focused_result = validate_upbit_paper_runtime_sample_history_sources(root=root, history=focused_history)
        self.assertEqual(focused_result.status, "PASS", focused_result.message)
        self.assertEqual(focused_history["active_candidate_scope"]["candidate_id"], focus["candidate_id"])
        self.assertEqual(focused_history["active_candidate_scope"]["strategy_id"], focus["strategy_id"])
        self.assertEqual(focused_history["active_candidate_scope"]["parameter_hash"], focus["parameter_hash"])
        self.assertEqual(focused_history["active_candidate_scope_sample_count"], 2)
        self.assertEqual(focused_history["active_candidate_scope_sample_deficit"], 28)
        self.assertFalse(focused_history["live_order_allowed"])

    def test_active_scope_prefers_latest_collectable_candidate_over_older_larger_scope(self):
        old_parameter_hash = "A" * 64
        new_parameter_hash = "B" * 64
        samples = [
            {
                "generated_at_utc": "2026-05-07T00:00:01Z",
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "scorecard_symbol": "KRW-OLD",
                "scorecard_candidate_id": "KRW-OLD-pullback-trend-long",
                "scorecard_strategy_id": "trend_pullback",
                "scorecard_parameter_hash": old_parameter_hash,
                "entry_reason_count": 1,
                "exit_reason_count": 0,
                "no_trade_reason_count": 0,
                "candidate_count": 3,
                "loop_id": "scope-a-1",
                "cycle_id": "cycle-a-1",
                "final_decision": "ENTER_LONG",
                "scorecard_candidate_decision": "PAPER_ENTRY_REVIEW",
                "sample_hash": "1" * 64,
                "source_runtime_cycle_hash": "2" * 64,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            {
                "generated_at_utc": "2026-05-07T00:00:02Z",
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "scorecard_symbol": "KRW-OLD",
                "scorecard_candidate_id": "KRW-OLD-pullback-trend-long",
                "scorecard_strategy_id": "trend_pullback",
                "scorecard_parameter_hash": old_parameter_hash,
                "entry_reason_count": 1,
                "exit_reason_count": 0,
                "no_trade_reason_count": 0,
                "candidate_count": 3,
                "loop_id": "scope-a-2",
                "cycle_id": "cycle-a-2",
                "final_decision": "ENTER_LONG",
                "scorecard_candidate_decision": "PAPER_ENTRY_REVIEW",
                "sample_hash": "3" * 64,
                "source_runtime_cycle_hash": "4" * 64,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            {
                "generated_at_utc": "2026-05-07T00:00:03Z",
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "scorecard_symbol": "KRW-NEW",
                "scorecard_candidate_id": "KRW-NEW-breakout-retest-long",
                "scorecard_strategy_id": "breakout_retest",
                "scorecard_parameter_hash": new_parameter_hash,
                "entry_reason_count": 1,
                "exit_reason_count": 0,
                "no_trade_reason_count": 0,
                "candidate_count": 3,
                "loop_id": "scope-b-1",
                "cycle_id": "cycle-b-1",
                "final_decision": "ENTER_LONG",
                "scorecard_candidate_decision": "PAPER_ENTRY_REVIEW",
                "sample_hash": "5" * 64,
                "source_runtime_cycle_hash": "6" * 64,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
        ]
        for sample in samples:
            sample["scorecard_candidate_identity_binding_status"] = "BOUND"
            sample["scorecard_candidate_live_flags_clear"] = True

        summaries = sample_history_module._candidate_scope_sample_summaries(
            samples,
            min_required_sample_count=30,
        )
        scope_fields = sample_history_module._active_candidate_scope_fields(
            summaries,
            min_required_sample_count=30,
        )

        active = scope_fields["active_candidate_scope"]
        self.assertEqual(active["candidate_id"], "KRW-NEW-breakout-retest-long")
        self.assertEqual(active["sample_count"], 1)
        self.assertEqual(active["sample_deficit"], 29)
        self.assertFalse(active["live_order_allowed"])

    def test_entry_reason_evidence_counts_blocked_candidate_entry_review(self):
        runtime_cycle = {
            "entry_reasons": [],
            "selected_candidate": {"decision": "PAPER_ENTRY_REVIEW"},
            "final_decision": "BLOCKED",
            "no_trade_reasons": ["RISK_VETO"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        self.assertEqual(sample_history_module._entry_reason_evidence_count(runtime_cycle), 1)

    def test_entry_reason_evidence_counts_review_candidates_when_position_management_overrides_final_decision(self):
        runtime_cycle = {
            "entry_reasons": [],
            "selected_candidate": {"decision": "NO_TRADE", "no_trade_reason": "REGIME_MISMATCH"},
            "strategy_candidates": [
                {"candidate_id": "candidate-1", "decision": "PAPER_ENTRY_REVIEW"},
                {"candidate_id": "candidate-2", "decision": "NO_TRADE"},
                {"candidate_id": "candidate-3", "decision": "PAPER_ENTRY_REVIEW"},
            ],
            "final_decision": "EXIT_POSITION",
            "no_trade_reasons": ["REGIME_ROTATION_EXIT"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        self.assertEqual(sample_history_module._entry_reason_evidence_count(runtime_cycle), 2)

    def test_exit_reason_evidence_counts_position_management_decision(self):
        runtime_cycle = {
            "final_decision": "REDUCE_POSITION",
            "no_trade_reasons": ["PARTIAL_EXIT_FILL", "REGIME_ROTATION_EXIT"],
            "position_management_decision": {
                "final_decision": "REDUCE_POSITION",
                "requested_position_decision": "EXIT_POSITION",
                "reason_code": "REGIME_ROTATION_EXIT",
                "execution_adjusted_position_decision_reason": "PARTIAL_EXIT_FILL",
            },
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        self.assertEqual(sample_history_module._exit_reason_evidence_count(runtime_cycle), 6)

    def test_candidate_identity_uses_scope_focus_when_managed_position_overrides_candidate_selection(self):
        focus_candidate = {
            "candidate_id": "KRW-ORCA-breakout-retest-long",
            "symbol": "KRW-ORCA",
            "strategy_family": "BREAKOUT_RETEST_LONG",
            "decision": "PAPER_ENTRY_REVIEW",
            "net_ev_after_cost_bps": "18.5",
            "candidate_selection_score": "72.0",
            "expected_edge_bps": "41.0",
            "expected_cost_bps": "22.5",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        requested_hash = sample_history_module._candidate_parameter_hash(focus_candidate)
        runtime_cycle = {
            "paper_scope_continuity_decision": {
                "requested": True,
                "selection_status": "MANAGED_POSITION_OVERRIDES_SCOPE_FOCUS",
                "requested_candidate_id": focus_candidate["candidate_id"],
                "requested_symbol": focus_candidate["symbol"],
                "requested_strategy_id": "breakout_retest",
                "requested_parameter_hash": requested_hash,
            },
            "selected_candidate": {
                "candidate_id": "KRW-BTC-vwap-mean-reversion",
                "symbol": "KRW-BTC",
                "strategy_family": "VWAP_MEAN_REVERSION",
                "decision": "PAPER_ENTRY_REVIEW",
                "net_ev_after_cost_bps": "11.0",
                "candidate_selection_score": "64.0",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            "strategy_candidates": [focus_candidate],
            "symbol_evidence_scorecards": [{"symbol": "KRW-ORCA"}],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        identity = sample_history_module._candidate_identity_fields(runtime_cycle)

        self.assertEqual(identity["scorecard_candidate_identity_source"], "PAPER_SCOPE_FOCUS_CANDIDATE")
        self.assertEqual(identity["scorecard_candidate_identity_binding_status"], "BOUND")
        self.assertEqual(identity["scorecard_candidate_id"], focus_candidate["candidate_id"])
        self.assertEqual(identity["scorecard_symbol"], focus_candidate["symbol"])
        self.assertEqual(identity["scorecard_strategy_id"], "breakout_retest")
        self.assertEqual(identity["scorecard_parameter_hash"], requested_hash)
        self.assertTrue(identity["scorecard_candidate_live_flags_clear"])

    def test_candidate_identity_counts_requested_scope_even_when_focus_is_no_trade(self):
        focus_candidate = {
            "candidate_id": "KRW-ADA-pullback-trend-long",
            "symbol": "KRW-ADA",
            "strategy_family": "PULLBACK_TREND_LONG",
            "decision": "NO_TRADE",
            "no_trade_reason": "STRATEGY_CONFIDENCE_LOW",
            "net_ev_after_cost_bps": "4.0",
            "candidate_selection_score": "51.0",
            "expected_edge_bps": "24.0",
            "expected_cost_bps": "20.0",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        requested_hash = sample_history_module._candidate_parameter_hash(focus_candidate)
        runtime_cycle = {
            "paper_scope_continuity_decision": {
                "requested": True,
                "selection_status": "FOCUS_CANDIDATE_NOT_ENTRY_REVIEW",
                "requested_candidate_id": focus_candidate["candidate_id"],
                "requested_symbol": focus_candidate["symbol"],
                "requested_strategy_id": "trend_pullback",
                "requested_parameter_hash": requested_hash,
            },
            "selected_candidate": {
                "candidate_id": "KRW-PROS-pullback-trend-long",
                "symbol": "KRW-PROS",
                "strategy_family": "PULLBACK_TREND_LONG",
                "decision": "PAPER_ENTRY_REVIEW",
                "net_ev_after_cost_bps": "17.0",
                "candidate_selection_score": "67.0",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            "strategy_candidates": [focus_candidate],
            "symbol_evidence_scorecards": [{"symbol": "KRW-ADA"}],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        identity = sample_history_module._candidate_identity_fields(runtime_cycle)

        self.assertEqual(identity["scorecard_candidate_identity_source"], "PAPER_SCOPE_FOCUS_CANDIDATE")
        self.assertEqual(identity["scorecard_candidate_identity_binding_status"], "BOUND")
        self.assertEqual(identity["scorecard_candidate_id"], focus_candidate["candidate_id"])
        self.assertEqual(identity["scorecard_candidate_decision"], "NO_TRADE")
        self.assertEqual(identity["scorecard_strategy_id"], "trend_pullback")
        self.assertEqual(identity["scorecard_parameter_hash"], requested_hash)
        self.assertFalse(identity["scorecard_candidate_id"] == runtime_cycle["selected_candidate"]["candidate_id"])
        self.assertTrue(identity["scorecard_candidate_live_flags_clear"])

    def test_candidate_identity_uses_explicit_mutated_parameter_hash_for_requested_scope(self):
        mutated_hash = "E" * 64
        focus_candidate = {
            "candidate_id": "KRW-ADA-pullback-trend-long",
            "symbol": "KRW-ADA",
            "strategy_family": "PULLBACK_TREND_LONG",
            "parameter_hash": mutated_hash,
            "decision": "NO_TRADE",
            "net_ev_after_cost_bps": "7.0",
            "candidate_selection_score": "56.0",
            "expected_edge_bps": "27.0",
            "expected_cost_bps": "20.0",
            "mutation_status": "APPLIED_TO_PAPER_CANDIDATE",
            "mutation_id": "mutation-explicit-hash",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        runtime_cycle = {
            "paper_scope_continuity_decision": {
                "requested": True,
                "selection_status": "FOCUS_CANDIDATE_NOT_ENTRY_REVIEW",
                "requested_candidate_id": focus_candidate["candidate_id"],
                "requested_symbol": focus_candidate["symbol"],
                "requested_strategy_id": "trend_pullback",
                "requested_parameter_hash": mutated_hash,
            },
            "selected_candidate": {"candidate_id": "KRW-OTHER", "decision": "NO_TRADE"},
            "strategy_candidates": [focus_candidate],
            "symbol_evidence_scorecards": [{"symbol": "KRW-ADA"}],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        identity = sample_history_module._candidate_identity_fields(runtime_cycle)

        self.assertEqual(identity["scorecard_candidate_identity_binding_status"], "BOUND")
        self.assertEqual(identity["scorecard_candidate_id"], focus_candidate["candidate_id"])
        self.assertEqual(identity["scorecard_parameter_hash"], mutated_hash)
        self.assertEqual(sample_history_module._candidate_parameter_hash(focus_candidate), mutated_hash)
        self.assertTrue(identity["scorecard_candidate_live_flags_clear"])

    def test_candidate_identity_blocks_requested_scope_with_live_flag_drift(self):
        focus_candidate = {
            "candidate_id": "KRW-ADA-pullback-trend-long",
            "symbol": "KRW-ADA",
            "strategy_family": "PULLBACK_TREND_LONG",
            "decision": "NO_TRADE",
            "net_ev_after_cost_bps": "7.0",
            "candidate_selection_score": "56.0",
            "live_order_ready": False,
            "live_order_allowed": True,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        requested_hash = sample_history_module._candidate_parameter_hash(focus_candidate)
        runtime_cycle = {
            "paper_scope_continuity_decision": {
                "requested": True,
                "selection_status": "FOCUS_CANDIDATE_NOT_ENTRY_REVIEW",
                "requested_candidate_id": focus_candidate["candidate_id"],
                "requested_symbol": focus_candidate["symbol"],
                "requested_strategy_id": "trend_pullback",
                "requested_parameter_hash": requested_hash,
            },
            "selected_candidate": {
                "candidate_id": "KRW-BTC-vwap-mean-reversion",
                "symbol": "KRW-BTC",
                "strategy_family": "VWAP_MEAN_REVERSION",
                "decision": "NO_TRADE",
                "net_ev_after_cost_bps": "2.0",
                "candidate_selection_score": "44.0",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            "strategy_candidates": [focus_candidate],
            "symbol_evidence_scorecards": [{"symbol": "KRW-ADA"}],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        identity = sample_history_module._candidate_identity_fields(runtime_cycle)

        self.assertNotEqual(identity["scorecard_candidate_id"], focus_candidate["candidate_id"])
        self.assertTrue(identity["scorecard_candidate_live_flags_clear"])

    def test_candidate_identity_blocks_requested_scope_with_unknown_continuity_status(self):
        focus_candidate = {
            "candidate_id": "KRW-ADA-pullback-trend-long",
            "symbol": "KRW-ADA",
            "strategy_family": "PULLBACK_TREND_LONG",
            "decision": "NO_TRADE",
            "net_ev_after_cost_bps": "7.0",
            "candidate_selection_score": "56.0",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        requested_hash = sample_history_module._candidate_parameter_hash(focus_candidate)
        runtime_cycle = {
            "paper_scope_continuity_decision": {
                "requested": True,
                "selection_status": "UNRECOGNIZED_STATUS",
                "requested_candidate_id": focus_candidate["candidate_id"],
                "requested_symbol": focus_candidate["symbol"],
                "requested_strategy_id": "trend_pullback",
                "requested_parameter_hash": requested_hash,
            },
            "selected_candidate": {
                "candidate_id": "KRW-BTC-vwap-mean-reversion",
                "symbol": "KRW-BTC",
                "strategy_family": "VWAP_MEAN_REVERSION",
                "decision": "NO_TRADE",
                "net_ev_after_cost_bps": "2.0",
                "candidate_selection_score": "44.0",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            "strategy_candidates": [focus_candidate],
            "symbol_evidence_scorecards": [{"symbol": "KRW-ADA"}],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

        identity = sample_history_module._candidate_identity_fields(runtime_cycle)

        self.assertNotEqual(identity["scorecard_candidate_id"], focus_candidate["candidate_id"])
        self.assertTrue(identity["scorecard_candidate_live_flags_clear"])

    def test_runtime_sample_history_excludes_invalid_legacy_loop_sources_while_collecting(self):
        history, root = self._history()
        paper_runtime_dir = (
            root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime"
        )
        invalid_legacy = paper_runtime_dir / "legacy-schema.invalid.persistent_loop_report.json"
        invalid_legacy.write_text("{}\n", encoding="utf-8")

        history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["runtime_sample_status"], "COLLECTING")
        self.assertEqual(history["primary_blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        self.assertEqual(history["accepted_cycle_sample_count"], 2)
        self.assertEqual(history["invalid_source_count"], 1)
        self.assertEqual(len(history["invalid_sources"]), 1)
        self.assertIn("schema", history["invalid_sources"][0]["reason"].lower())
        self.assertFalse(history["long_run_evidence_eligible"])
        self.assertFalse(history["live_order_allowed"])

    def test_runtime_sample_history_binds_runtime_hashes_after_timestamp_sorting(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        run_upbit_paper_persistent_loop(root=root, loop_id="zz-sample-history-sort-source", requested_cycle_count=1)
        time.sleep(1.1)
        run_upbit_paper_persistent_loop(root=root, loop_id="aa-sample-history-sort-source", requested_cycle_count=1)

        history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(
            history["source_runtime_cycle_hashes"],
            [sample["source_runtime_cycle_hash"] for sample in history["samples"]],
        )
        self.assertEqual(history["samples"][0]["loop_id"], "zz-sample-history-sort-source")
        self.assertEqual(history["samples"][1]["loop_id"], "aa-sample-history-sort-source")

    def test_runtime_sample_history_uses_numeric_cycle_order_for_same_second_cycles(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        run_upbit_paper_persistent_loop(root=root, loop_id="sample-history-natural-cycle-sort", requested_cycle_count=12)

        history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        result = validate_upbit_paper_runtime_sample_history(history)
        cycle_ids = [sample["cycle_id"] for sample in history["samples"]]

        self.assertEqual(result.status, "PASS")
        self.assertEqual(history["accepted_cycle_sample_count"], 12)
        self.assertLess(
            cycle_ids.index("sample-history-natural-cycle-sort-cycle-9"),
            cycle_ids.index("sample-history-natural-cycle-sort-cycle-10"),
        )
        self.assertEqual(cycle_ids[-1], "sample-history-natural-cycle-sort-cycle-12")

    def test_runtime_sample_history_blocks_duplicate_source_cycle_hash_from_copied_loop_report(self):
        history, root = self._history()
        paper_runtime_dir = (
            root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime"
        )
        source = paper_runtime_dir / "sample-history-a.persistent_loop_report.json"
        duplicate = paper_runtime_dir / "sample-history-a-copy.persistent_loop_report.json"
        duplicate.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")
        self.assertEqual(history["runtime_sample_status"], "BLOCKED")
        self.assertEqual(history["primary_blocker_code"], "RECONCILIATION_REQUIRED")
        self.assertEqual(history["accepted_cycle_sample_count"], 2)
        self.assertEqual(history["duplicate_cycle_hash_count"], 1)
        self.assertFalse(history["live_order_allowed"])

    def test_runtime_sample_history_blocks_false_long_run_claim(self):
        history, _ = self._history()
        history["long_run_evidence_eligible"] = True
        history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)

        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_runtime_sample_history_blocks_duplicate_runtime_cycle_hash(self):
        history, _ = self._history()
        duplicate_sample = dict(history["samples"][0])
        duplicate_sample["generated_at_utc"] = history["samples"][-1]["generated_at_utc"]
        duplicate_sample["previous_sample_hash"] = history["samples"][-1]["sample_hash"]
        duplicate_sample["sample_hash"] = upbit_paper_runtime_sample_hash(duplicate_sample)
        history["samples"].append(duplicate_sample)
        history["accepted_cycle_sample_count"] = len(history["samples"])
        history["unique_runtime_cycle_hash_count"] = len({item["source_runtime_cycle_hash"] for item in history["samples"]})
        history["duplicate_cycle_hash_count"] = history["accepted_cycle_sample_count"] - history["unique_runtime_cycle_hash_count"]
        history["source_runtime_cycle_hashes"] = [item["source_runtime_cycle_hash"] for item in history["samples"]]
        history["latest_sample_at_utc"] = history["samples"][-1]["generated_at_utc"]
        history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)

        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_runtime_sample_history_blocks_cross_namespace_source_path(self):
        history, _ = self._history()
        history["samples"][0]["source_runtime_cycle_path"] = "system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/unsafe.runtime_cycle.json"
        history["samples"][0]["sample_hash"] = upbit_paper_runtime_sample_hash(history["samples"][0])
        history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)

        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_runtime_sample_history_source_validator_blocks_missing_bound_cycle_file(self):
        history, root = self._history()
        result = validate_upbit_paper_runtime_sample_history(history)
        self.assertEqual(result.status, "PASS")

        missing_path = root / history["samples"][0]["source_runtime_cycle_path"]
        missing_path.unlink()

        source_result = validate_upbit_paper_runtime_sample_history_sources(root=root, history=history)

        self.assertEqual(source_result.status, "BLOCKED")
        self.assertEqual(source_result.blocker_code, "RECONCILIATION_REQUIRED")
        self.assertIn("source cycle is missing", source_result.message)

    def test_runtime_sample_history_reads_retained_archive_and_compacted_sources(self):
        from trader1.runtime.paper.upbit_paper_long_runner import apply_runner_artifact_retention

        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        session_id = "archive_bound_history"

        for index in range(3):
            run_upbit_paper_persistent_loop(
                root=root,
                session_id=session_id,
                loop_id=f"upbit-paper-runner-archive-bound-{index + 1:06d}",
                requested_cycle_count=1,
            )

        apply_runner_artifact_retention(
            root=root,
            session_id=session_id,
            max_active_artifacts_per_group=1,
            max_uncompacted_archive_batches=1,
            log_max_bytes=128,
            disk_pressure_max_runtime_bytes=1_000_000,
        )

        archived_history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
        archived_source_result = validate_upbit_paper_runtime_sample_history_sources(root=root, history=archived_history)
        archived_paths = [
            item
            for sample in archived_history["samples"]
            for item in (sample["source_loop_report_path"], sample["source_runtime_cycle_path"])
            if "/paper_runtime/runner/archive/" in item
        ]

        self.assertEqual(archived_source_result.status, "PASS")
        self.assertEqual(archived_history["accepted_cycle_sample_count"], 3)
        self.assertTrue(archived_paths)

        time.sleep(1.1)
        run_upbit_paper_persistent_loop(
            root=root,
            session_id=session_id,
            loop_id="upbit-paper-runner-archive-bound-000004",
            requested_cycle_count=1,
        )
        apply_runner_artifact_retention(
            root=root,
            session_id=session_id,
            max_active_artifacts_per_group=1,
            max_uncompacted_archive_batches=1,
            log_max_bytes=128,
            disk_pressure_max_runtime_bytes=1_000_000,
        )

        compacted_history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
        compacted_source_result = validate_upbit_paper_runtime_sample_history_sources(root=root, history=compacted_history)
        compacted_paths = [
            item
            for sample in compacted_history["samples"]
            for item in (sample["source_loop_report_path"], sample["source_runtime_cycle_path"])
            if ".zip#" in item
        ]

        self.assertEqual(compacted_source_result.status, "PASS")
        self.assertEqual(compacted_history["accepted_cycle_sample_count"], 4)
        self.assertTrue(compacted_paths)
        self.assertFalse(compacted_history["live_order_allowed"])
        self.assertFalse(compacted_history["can_live_trade"])

    def test_runtime_sample_history_detects_floor_flag_drift(self):
        history, _ = self._history()
        history["span_floor_met"] = True
        history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)

        result = validate_upbit_paper_runtime_sample_history(history)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
