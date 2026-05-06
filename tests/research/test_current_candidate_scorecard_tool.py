import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.run_upbit_paper_candidate_scorecard import build_current_upbit_paper_candidate_scorecard
from trader1.research.profitability.candidate_scorecard import robustness_source_evidence_id
from trader1.research.profitability.overfit_diagnostic import (
    overfit_diagnostic_from_upbit_paper_runtime,
    overfit_diagnostic_report_hash,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.validation.mvp0_validators import _candidate_scorecard_net_ev_errors, _overfit_diagnostic_errors


def _load_written(root: Path, result: dict, key: str) -> dict:
    value = json.loads((root / result[key]).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{key} did not point to a JSON object")
    return value


def _run_short_paper(root: Path) -> None:
    run_upbit_paper_persistent_loop(
        root=root,
        loop_id="current-scorecard-short-runtime",
        requested_cycle_count=2,
    )


class CurrentCandidateScorecardToolTest(unittest.TestCase):
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

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(_candidate_scorecard_net_ev_errors(scorecard), [])
        self.assertEqual(_overfit_diagnostic_errors(diagnostic), [])
        self.assertEqual(history["accepted_cycle_sample_count"], 2)
        self.assertEqual(diagnostic["sample_count"], 2)
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
        self.assertFalse(result["live_order_allowed"])
        blocker_codes = {blocker["code"] for blocker in scorecard["blockers"]}
        self.assertTrue({"OOS_MISSING", "WALK_FORWARD_MISSING", "BOOTSTRAP_UNSTABLE", "OVERFIT_RISK_HIGH"}.issubset(blocker_codes))

    def test_bridge_consumes_robust_diagnostic_as_paper_scorecard_input_only(self):
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

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(_overfit_diagnostic_errors(diagnostic), [])
        self.assertEqual(_candidate_scorecard_net_ev_errors(scorecard), [])
        self.assertTrue(diagnostic["robustness_eligible"])
        self.assertTrue(scorecard["ranking_eligible"])
        self.assertEqual(scorecard["scorecard_scope"], "PAPER_SCORECARD_INPUT_ONLY")
        self.assertEqual(scorecard["live_readiness_status"], "NOT_LIVE_READY")
        self.assertFalse(scorecard["live_order_ready"])
        self.assertFalse(scorecard["live_order_allowed"])
        self.assertFalse(scorecard["can_live_trade"])
        self.assertFalse(scorecard["scale_up_allowed"])
        self.assertFalse(result["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
