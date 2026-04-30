import copy
import unittest

from trader1.research.shadow.evidence_accumulator import (
    build_paper_shadow_evidence_accumulation_from_operation_reports,
)
from trader1.research.shadow.shadow_runner import (
    build_paper_shadow_evidence_accumulation_report,
    validate_paper_shadow_evidence_accumulation_report,
)
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle


class PaperShadowEvidenceAccumulatorTest(unittest.TestCase):
    def test_paper_only_evidence_accumulation_blocks_optimizer_ranking(self):
        reports = [
            build_upbit_operational_paper_cycle(
                operation_gate_id="paper-only-entry",
                session_id="paper-only-entry-session",
                requested_entry=True,
            ),
            build_upbit_operational_paper_cycle(
                operation_gate_id="paper-only-no-trade",
                session_id="paper-only-no-trade-session",
                requested_entry=False,
            ),
        ]

        report = build_paper_shadow_evidence_accumulation_from_operation_reports(
            evidence_report_id="paper-only-aggregate",
            paper_operation_reports=reports,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SAMPLE_INSUFFICIENT")
        self.assertGreater(report["paper_sample_count"], 0)
        self.assertLess(report["paper_sample_count"], report["min_required_sample_count"])
        self.assertEqual(report["shadow_sample_count"], 0)
        self.assertEqual(
            set(report["source_evidence_ids"]),
            {binding["source_evidence_id"] for binding in report["source_evidence_bindings"]},
        )
        self.assertEqual(report["evidence_span_hours"], 0)
        self.assertEqual(report["evidence_span_source"], "NOT_PROVIDED")
        self.assertEqual(report["evidence_span_source_status"], "MISSING")
        self.assertTrue(any(source_id.startswith("paper-operation:") for source_id in report["supporting_source_evidence_ids"]))
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_mixed_candidate_identity_blocks_even_with_sufficient_counts(self):
        base = build_upbit_operational_paper_cycle(
            operation_gate_id="aggregate-base",
            session_id="aggregate-base-session",
            requested_entry=True,
        )
        mismatched = copy.deepcopy(base)
        mismatched["operation_gate_id"] = "aggregate-mismatch"
        mismatched["session_id"] = "aggregate-mismatch-session"
        mismatched["paper_shadow_evidence_accumulation_report"]["candidate_id"] = "candidate-other"
        for source in (base, mismatched):
            source["paper_shadow_evidence_accumulation_report"]["paper_sample_count"] = 2
            source["paper_shadow_evidence_accumulation_report"]["entry_reason_count"] = 1
            source["paper_shadow_evidence_accumulation_report"]["no_trade_reason_count"] = 1
            source["paper_shadow_evidence_accumulation_report"]["cost_evidence_count"] = 1

        shadow = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="shadow-source",
            candidate_id=base["paper_shadow_evidence_accumulation_report"]["candidate_id"],
            strategy_id=base["paper_shadow_evidence_accumulation_report"]["strategy_id"],
            strategy_build_id=base["paper_shadow_evidence_accumulation_report"]["strategy_build_id"],
            parameter_hash=base["paper_shadow_evidence_accumulation_report"]["parameter_hash"],
            paper_sample_count=30,
            shadow_sample_count=60,
            entry_reason_count=3,
            no_trade_reason_count=3,
            cost_evidence_count=3,
        )

        report = build_paper_shadow_evidence_accumulation_from_operation_reports(
            evidence_report_id="mixed-identity-aggregate",
            paper_operation_reports=[base, mismatched],
            shadow_evidence_reports=[shadow],
            min_required_sample_count=1,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")
        self.assertFalse(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "BLOCK_RANKING")

    def test_matched_paper_shadow_short_window_can_feed_paper_scorecard_only(self):
        base = build_upbit_operational_paper_cycle(
            operation_gate_id="aggregate-scorecard",
            session_id="aggregate-scorecard-session",
            requested_entry=True,
        )
        evidence = base["paper_shadow_evidence_accumulation_report"]
        paper = copy.deepcopy(base)
        paper["paper_shadow_evidence_accumulation_report"]["paper_sample_count"] = 30
        paper["paper_shadow_evidence_accumulation_report"]["entry_reason_count"] = 5
        paper["paper_shadow_evidence_accumulation_report"]["no_trade_reason_count"] = 5
        paper["paper_shadow_evidence_accumulation_report"]["cost_evidence_count"] = 5
        shadow = build_paper_shadow_evidence_accumulation_report(
            evidence_report_id="matched-shadow-source",
            candidate_id=evidence["candidate_id"],
            strategy_id=evidence["strategy_id"],
            strategy_build_id=evidence["strategy_build_id"],
            parameter_hash=evidence["parameter_hash"],
            paper_sample_count=30,
            shadow_sample_count=30,
            entry_reason_count=5,
            no_trade_reason_count=5,
            cost_evidence_count=5,
        )

        report = build_paper_shadow_evidence_accumulation_from_operation_reports(
            evidence_report_id="matched-short-window-aggregate",
            paper_operation_reports=[paper],
            shadow_evidence_reports=[shadow],
            evidence_span_hours=4,
        )
        result = validate_paper_shadow_evidence_accumulation_report(report)

        self.assertEqual(result.status, "PASS")
        self.assertTrue(report["scorecard_input_eligible"])
        self.assertEqual(report["optimizer_ranking_action"], "ALLOW_RANKING")
        self.assertEqual(
            set(report["source_evidence_ids"]),
            {binding["source_evidence_id"] for binding in report["source_evidence_bindings"]},
        )
        self.assertTrue(any(source_id.startswith("paper-operation:") for source_id in report["supporting_source_evidence_ids"]))
        self.assertTrue(any(source_id.startswith("shadow-evidence:") for source_id in report["supporting_source_evidence_ids"]))
        self.assertEqual(report["evidence_span_source"], "EXPLICIT_OPERATOR_SUPPLIED")
        self.assertEqual(report["evidence_span_source_status"], "PASS")
        self.assertFalse(report["long_run_evidence_eligible"])
        self.assertEqual(
            report["long_run_blocker_code"],
            "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
        )
        self.assertFalse(report["promotion_eligible"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])


if __name__ == "__main__":
    unittest.main()
