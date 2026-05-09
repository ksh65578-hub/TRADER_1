import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture
from trader1.research.profitability.candidate_scorecard import (
    candidate_generation_report_from_upbit_paper_runtime_cycle,
    candidate_scorecard_from_upbit_paper_runtime_cycle,
    write_upbit_paper_candidate_generation_report,
)
from trader1.research.replay.replay_runner import (
    build_public_replay_robustness_report,
    public_replay_robustness_report_hash,
    write_public_replay_robustness_report,
)
from trader1.runtime.paper.candidate_generation_intent_provider import (
    CandidateGenerationPaperIntentProvider,
    PaperTradeIntentInputs,
    paper_candidate_rehydration_report_path,
    validate_paper_candidate_rehydration_report,
)
from trader1.runtime.paper.upbit_paper_long_runner import (
    _paper_scope_focus_from_trade_intent_inputs,
)
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


SESSION_ID = "mvp1_upbit_paper_launcher"


def _profitability_dir(root: Path, session_id: str = SESSION_ID) -> Path:
    return (
        root
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / session_id
        / "profitability"
    )


def _make_public_replay_pass(replay_report: dict, runtime_cycle: dict, candidate_scorecard: dict) -> dict:
    rows = [
        {
            "sample_id": f"{replay_report['replay_id']}:sample:{index:04d}",
            "sample_index": index,
            "event_time_utc": f"2026-05-09T00:00:0{index}Z",
            "runtime_cycle_id": runtime_cycle["cycle_id"],
            "runtime_cycle_hash": runtime_cycle["cycle_hash"],
            "candidate_id": candidate_scorecard["candidate_id"],
            "decision": "PAPER_ENTRY_REVIEW",
            "executed_trade": True,
            "net_ev_after_cost_bps": candidate_scorecard["net_ev_after_cost_bps"],
            "total_execution_cost_bps": candidate_scorecard.get("total_execution_cost_bps", 0.0),
            "closed_trade": True,
            "realized_trade_pnl_bps": 14.0 + index,
            "realized_vs_expected_edge_bps": 2.0,
            "strategy_exit_policy_observed": True,
            "strategy_exit_policy_matched": True,
            "execution_cost_delta_bps": 0.2,
        }
        for index in range(1, 3)
    ]
    replay = dict(replay_report)
    replay.update(
        {
            "sample_count": len(rows),
            "min_required_sample_count": 1,
            "sample_rows": rows,
            "replay_closed_trade_sample_count": len(rows),
            "replay_closed_trade_status": "PASS",
            "min_required_closed_trade_sample_count": 1,
            "replay_closed_trade_deficit": 0,
            "replay_closed_trade_maturity_status": "PASS",
            "replay_closed_trade_maturity_blocker_code": None,
            "replay_strategy_exit_policy_sample_count": len(rows),
            "replay_strategy_exit_policy_match_count": len(rows),
            "replay_strategy_exit_policy_mismatch_count": 0,
            "replay_strategy_exit_policy_status": "PASS",
            "replay_profit_factor": 2.4,
            "replay_profit_factor_status": "PASS",
            "replay_max_drawdown_bps": 8.0,
            "replay_realized_vs_expected_edge_bps": 2.0,
            "replay_realized_vs_expected_edge_status": "PASS",
            "replay_fill_quality_score": 0.95,
            "replay_execution_cost_delta_bps": 0.2,
            "replay_execution_cost_status": "PASS",
            "replay_status": "PASS",
            "primary_blocker_code": None,
            "blockers": [],
        }
    )
    replay["report_hash"] = public_replay_robustness_report_hash(replay)
    return replay


def _write_validated_generation_fixture(root: Path) -> dict:
    runtime = build_upbit_paper_runtime_cycle_report(
        cycle_id="provider-candidate-generation-base",
        session_id=SESSION_ID,
    )
    source_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
        runtime,
        robustness_statuses={
            "oos_status": "FAIL",
            "walk_forward_status": "FAIL",
            "bootstrap_status": "FAIL",
            "overfit_status": "HIGH",
        },
        robustness_source_evidence_ids=[
            "public_replay_robustness:provider-candidate-generation-base:" + "A" * 64,
            "public_market_data:KRW-BTC:" + "B" * 64,
        ],
    )
    discovery_market_data = build_upbit_public_candle_fixture(
        symbol="KRW-ETH",
        session_id=SESSION_ID,
        profile="UPTREND_PULLBACK",
    )
    discovery_runtime = build_upbit_paper_runtime_cycle_report(
        cycle_id="provider-candidate-generation-discovery-alt",
        session_id=SESSION_ID,
        market_data=discovery_market_data,
        symbol="KRW-ETH",
    )
    alternative_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(discovery_runtime)
    replay_report = build_public_replay_robustness_report(
        candidate_scorecard=alternative_scorecard,
        market_data=discovery_market_data,
        replay_id="provider-public-replay-alt",
        max_replay_windows=2,
        min_required_sample_count=1,
    )
    replay_report = _make_public_replay_pass(replay_report, discovery_runtime, alternative_scorecard)
    generation_report = candidate_generation_report_from_upbit_paper_runtime_cycle(
        runtime,
        candidate_scorecard=source_scorecard,
        additional_runtime_cycle_reports=[discovery_runtime],
        best_alternative_public_replay_report=replay_report,
    )
    write_public_replay_robustness_report(root=root, report=replay_report)
    write_upbit_paper_candidate_generation_report(root=root, report=generation_report)
    durable_atomic_write_json(
        _profitability_dir(root) / "candidate_generation_discovery_runtime_cycle.json",
        discovery_runtime,
    )
    return {
        "generation_report": generation_report,
        "replay_report": replay_report,
        "discovery_runtime": discovery_runtime,
        "alternative_scorecard": alternative_scorecard,
    }


class CandidateGenerationPaperIntentProviderTests(unittest.TestCase):
    def test_validated_generation_rehydrates_public_replay_candidate_into_paper_scope_focus(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = _write_validated_generation_fixture(root)

            intent = CandidateGenerationPaperIntentProvider().provide(
                root=root,
                current_paper_portfolio_snapshot={"open_position_count": 0, "positions": []},
            )
            report = json.loads(paper_candidate_rehydration_report_path(root).read_text(encoding="utf-8"))
            status, message, blocker_code = validate_paper_candidate_rehydration_report(report)

        self.assertIsInstance(intent, PaperTradeIntentInputs)
        self.assertEqual(status, "PASS", message)
        self.assertIsNone(blocker_code)
        self.assertEqual(report["rehydration_status"], "PASS")
        self.assertEqual(report["generation_status"], "ALTERNATIVE_PUBLIC_REPLAY_VALIDATED")
        self.assertEqual(report["replay_status"], "PASS")
        self.assertEqual(report["runtime_linkage_status"], "PASS")
        self.assertTrue(report["generation_hash_checked"])
        self.assertTrue(report["replay_hash_checked"])
        self.assertTrue(report["runtime_hash_checked"])
        self.assertEqual(intent.paper_scope_focus["candidate_id"], fixture["generation_report"]["best_alternative_candidate_id"])
        self.assertEqual(intent.paper_scope_focus["source"], "CANDIDATE_GENERATION_PUBLIC_REPLAY_REHYDRATION")
        self.assertEqual(intent.paper_scope_focus["sample_deficit"], 30)
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(intent.paper_scope_focus["live_order_allowed"])

    def test_provider_fails_closed_until_generation_is_public_replay_validated(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = build_upbit_paper_runtime_cycle_report(
                cycle_id="provider-generation-review-ready",
                session_id=SESSION_ID,
            )
            source_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
                runtime,
                robustness_statuses={
                    "oos_status": "FAIL",
                    "walk_forward_status": "FAIL",
                    "bootstrap_status": "FAIL",
                    "overfit_status": "HIGH",
                },
                robustness_source_evidence_ids=[
                    "public_replay_robustness:provider-generation-review-ready:" + "A" * 64,
                    "public_market_data:KRW-BTC:" + "B" * 64,
                ],
            )
            alternative = dict(runtime["selected_candidate"])
            alternative["candidate_id"] = "KRW-ETH-pullback-trend-long"
            alternative["symbol"] = "KRW-ETH"
            alternative["net_ev_after_cost_bps"] = float(alternative["net_ev_after_cost_bps"]) + 6.0
            runtime["strategy_candidates"].append(alternative)
            generation_report = candidate_generation_report_from_upbit_paper_runtime_cycle(
                runtime,
                candidate_scorecard=source_scorecard,
            )
            write_upbit_paper_candidate_generation_report(root=root, report=generation_report)

            intent = CandidateGenerationPaperIntentProvider().provide(root=root)
            report = json.loads(paper_candidate_rehydration_report_path(root).read_text(encoding="utf-8"))

        self.assertIsNone(intent)
        self.assertEqual(report["rehydration_status"], "BLOCKED")
        self.assertEqual(report["blocker_code"], "CANDIDATE_GENERATION_NOT_PUBLIC_REPLAY_VALIDATED")
        self.assertFalse(report["live_order_allowed"])

    def test_provider_blocks_candidate_switch_when_current_paper_position_is_open(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_validated_generation_fixture(root)

            intent = CandidateGenerationPaperIntentProvider().provide(
                root=root,
                current_paper_portfolio_snapshot={
                    "open_position_count": 1,
                    "positions": [{"symbol": "KRW-BTC", "quantity": "0.1"}],
                },
            )
            report = json.loads(paper_candidate_rehydration_report_path(root).read_text(encoding="utf-8"))

        self.assertIsNone(intent)
        self.assertEqual(report["rehydration_status"], "BLOCKED")
        self.assertEqual(report["blocker_code"], "OPEN_POSITION_BLOCKS_REHYDRATION")
        self.assertFalse(report["live_order_allowed"])

    def test_long_runner_focus_adapter_accepts_provider_inputs_and_keeps_live_flags_false(self):
        focus = {
            "source": "CANDIDATE_GENERATION_PUBLIC_REPLAY_REHYDRATION",
            "candidate_id": "KRW-ETH-pullback-trend-long",
            "symbol": "krw-eth",
            "strategy_id": "trend_pullback",
            "parameter_hash": "A" * 64,
            "sample_count": 0,
            "sample_deficit": 30,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        intent = PaperTradeIntentInputs(
            paper_scope_focus=focus,
            paper_candidate_rehydration_report={},
            candidate_item={},
        )

        normalized = _paper_scope_focus_from_trade_intent_inputs(intent)

        self.assertEqual(normalized["symbol"], "KRW-ETH")
        self.assertEqual(normalized["candidate_id"], "KRW-ETH-pullback-trend-long")
        self.assertFalse(normalized["live_order_allowed"])
        self.assertEqual(normalized["sample_deficit"], 30)


if __name__ == "__main__":
    unittest.main()
