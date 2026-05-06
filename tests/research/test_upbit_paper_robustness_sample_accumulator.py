import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.run_upbit_paper_robustness_sample_accumulator import (
    build_upbit_paper_robustness_sample_accumulation,
)


class UpbitPaperRobustnessSampleAccumulatorTest(unittest.TestCase):
    def test_accumulator_runs_bounded_paper_cycles_and_refreshes_scorecard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = build_upbit_paper_robustness_sample_accumulation(
                root=root,
                target_sample_count=5,
                max_new_cycles=5,
                cycles_per_loop=2,
                loop_id_prefix="accumulator-short",
            )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["accumulation_status"], "TARGET_SAMPLE_COUNT_REACHED")
        self.assertEqual(result["before_sample_count"], 0)
        self.assertEqual(result["after_sample_count"], 5)
        self.assertEqual(result["accepted_new_sample_count"], 5)
        self.assertEqual(result["missing_target_sample_count"], 0)
        self.assertEqual(result["missing_robustness_sample_count"], 295)
        self.assertFalse(result["robustness_sample_floor_met"])
        self.assertEqual(result["requested_new_cycle_count"], 5)
        self.assertEqual(result["loop_report_count"], 3)
        self.assertEqual([loop["requested_cycle_count"] for loop in result["loop_reports"]], [2, 2, 1])
        self.assertEqual(result["scorecard_status"], "PASS")
        self.assertFalse(result["ranking_eligible"])
        self.assertEqual(result["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertFalse(result["live_order_ready"])
        self.assertFalse(result["live_order_allowed"])
        self.assertFalse(result["can_live_trade"])
        self.assertFalse(result["scale_up_allowed"])

    def test_accumulator_collects_partially_when_cycle_budget_is_below_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = build_upbit_paper_robustness_sample_accumulation(
                root=root,
                target_sample_count=5,
                max_new_cycles=3,
                cycles_per_loop=2,
                loop_id_prefix="accumulator-partial",
            )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["accumulation_status"], "COLLECTING")
        self.assertEqual(result["after_sample_count"], 3)
        self.assertEqual(result["missing_sample_count"], 2)
        self.assertEqual(result["missing_target_sample_count"], 2)
        self.assertEqual(result["missing_robustness_sample_count"], 297)
        self.assertFalse(result["robustness_sample_floor_met"])
        self.assertEqual(result["blocker_code"], "SAMPLE_INSUFFICIENT")
        self.assertFalse(result["live_order_allowed"])

    def test_accumulator_refreshes_scorecard_after_loop_block_with_partial_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            with patch(
                "tools.run_upbit_paper_robustness_sample_accumulator.validate_upbit_paper_persistent_loop_report",
                return_value=SimpleNamespace(status="BLOCKED", blocker_code="RISK_VETO", message="forced loop block"),
            ):
                result = build_upbit_paper_robustness_sample_accumulation(
                    root=root,
                    target_sample_count=2,
                    max_new_cycles=1,
                    cycles_per_loop=1,
                    loop_id_prefix="accumulator-forced-block",
                )

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["blocker_code"], "RISK_VETO")
        self.assertEqual(result["after_sample_count"], 1)
        self.assertEqual(result["accepted_new_sample_count"], 1)
        self.assertEqual(result["scorecard_status"], "PASS")
        self.assertEqual(result["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertFalse(result["live_order_allowed"])

    def test_accumulator_rejects_unbounded_runtime_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = build_upbit_paper_robustness_sample_accumulation(
                root=root,
                target_sample_count=5,
                max_new_cycles=1,
                cycles_per_loop=21,
            )

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["blocker_code"], "RUNTIME_BUDGET_EXCEEDED")
        self.assertFalse(result["live_order_allowed"])


if __name__ == "__main__":
    unittest.main()
