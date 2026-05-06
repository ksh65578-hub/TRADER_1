import copy
import json
import tempfile
import unittest
from pathlib import Path

from trader1.research.profitability.candidate_scorecard import candidate_scorecard_from_upbit_paper_runtime_cycle
from trader1.research.profitability.overfit_diagnostic import (
    _bootstrap_confidence_lower_bound,
    overfit_diagnostic_from_upbit_paper_runtime,
    overfit_diagnostic_report_hash,
    robustness_inputs_from_overfit_diagnostic,
    write_overfit_diagnostic_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.runtime.paper.upbit_paper_runtime_sample_history import build_upbit_paper_runtime_sample_history
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

        self.assertTrue(str(path).endswith("system\\runtime\\upbit\\krw_spot\\paper\\mvp1_upbit_paper_launcher\\profitability\\overfit_diagnostic_report.json"))
        self.assertEqual(written["diagnostic_hash"], overfit_diagnostic_report_hash(written))
        self.assertFalse(written["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
