import unittest

from trader1.core.sizing.position_sizing import (
    build_position_sizing_decision,
    default_sizing_inputs,
    sizing_decision_hash,
    validate_position_sizing_decision,
)
from trader1.runtime.paper.operational_cycle import (
    build_upbit_operational_paper_cycle,
    operation_gate_hash,
    validate_paper_operation_gate_report,
)


class UpbitOperationalPaperCycleTest(unittest.TestCase):
    def test_operational_paper_cycle_passes_without_live_permission(self):
        report = build_upbit_operational_paper_cycle(operation_gate_id="mvp3-cycle-pass")
        result = validate_paper_operation_gate_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["operation_gate_status"], "PASS")
        self.assertEqual(report["stage_gate_status"], "PASS_FOR_MVP3_OPERATIONAL_PAPER_ONLY")
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["can_submit_order"])
        self.assertFalse(report["order_adapter_called"])
        self.assertFalse(report["dashboard_panels"]["status"]["order_controls_present"])
        evidence = report["paper_shadow_evidence_accumulation_report"]
        self.assertFalse(evidence["scorecard_input_eligible"])
        self.assertEqual(evidence["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertLess(evidence["paper_sample_count"], evidence["min_required_sample_count"])
        self.assertLess(evidence["shadow_sample_count"], evidence["min_required_sample_count"])
        self.assertEqual(evidence["primary_blocker_code"], "SAMPLE_INSUFFICIENT")
        self.assertEqual(
            evidence["long_run_blocker_code"],
            "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
        )
        self.assertIn("/paper/", evidence["paper_artifact_path"])
        self.assertIn("/shadow/", evidence["shadow_artifact_path"])
        self.assertEqual(evidence["paper_artifact_hash"], report["paper_dry_run_report"]["dry_run_hash"])
        self.assertFalse(evidence["live_order_allowed"])

    def test_risk_veto_blocks_operation_gate(self):
        report = build_upbit_operational_paper_cycle(operation_gate_id="mvp3-cycle-risk", risk_block=True)
        self.assertEqual(report["operation_gate_status"], "BLOCKED")
        self.assertEqual(report["primary_blocker_code"], "RISK_VETO")

    def test_sizing_min_of_caps(self):
        inputs = default_sizing_inputs()
        decision = build_position_sizing_decision(
            sizing_decision_id="sizing-pass",
            strategy_unit_id="strategy-1",
            inputs=inputs,
        )
        result = validate_position_sizing_decision(decision)
        self.assertEqual(result.status, "PASS")
        selected = float(decision["selected_notional"])
        self.assertLessEqual(selected, float(decision["caps"]["equity_cap"]))
        self.assertLessEqual(selected, float(decision["caps"]["cash_cap"]))
        self.assertLessEqual(selected, float(decision["caps"]["risk_cap"]))
        self.assertLessEqual(selected, float(decision["caps"]["liquidity_cap"]))
        self.assertLessEqual(selected, float(decision["caps"]["exposure_cap"]))
        self.assertLessEqual(selected, float(decision["caps"]["atr_risk_cap"]))
        self.assertLessEqual(selected, float(decision["caps"]["volatility_cap"]))
        self.assertEqual(decision["caps"]["drawdown_multiplier"], "1")
        self.assertEqual(decision["caps"]["regime_multiplier"], "1")
        self.assertEqual(decision["caps"]["correlation_multiplier"], "1")
        self.assertEqual(decision["caps"]["realized_performance_multiplier"], "1")
        self.assertIn("atr_risk_cap", decision["caps"]["sizing_formula"])

    def test_sizing_blocks_when_current_exposure_exceeds_paper_cap(self):
        inputs = default_sizing_inputs()
        inputs["current_exposure"] = "400000"
        decision = build_position_sizing_decision(
            sizing_decision_id="sizing-exposure-cap",
            strategy_unit_id="strategy-1",
            inputs=inputs,
        )
        result = validate_position_sizing_decision(decision)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(decision["sizing_status"], "BLOCKED")
        self.assertEqual(decision["primary_blocker_code"], "RISK_VETO")
        self.assertEqual(decision["selected_notional"], "0")
        self.assertFalse(decision["live_order_allowed"])

    def test_sizing_reduces_for_volatility_drawdown_correlation_and_performance_feedback(self):
        base = build_position_sizing_decision(
            sizing_decision_id="sizing-base",
            strategy_unit_id="strategy-1",
            inputs=default_sizing_inputs(),
        )
        base_selected = float(base["selected_notional"])

        high_volatility_inputs = default_sizing_inputs()
        high_volatility_inputs["volatility"] = "0.10"
        high_volatility_inputs["atr_rate"] = "0.10"
        high_volatility = build_position_sizing_decision(
            sizing_decision_id="sizing-high-volatility",
            strategy_unit_id="strategy-1",
            inputs=high_volatility_inputs,
        )
        self.assertEqual(validate_position_sizing_decision(high_volatility).status, "PASS")
        self.assertLess(float(high_volatility["selected_notional"]), base_selected)
        self.assertEqual(high_volatility["caps"]["volatility_multiplier"], "0.4")

        drawdown_inputs = default_sizing_inputs()
        drawdown_inputs["drawdown_pct"] = "0.05"
        drawdown = build_position_sizing_decision(
            sizing_decision_id="sizing-drawdown-freeze",
            strategy_unit_id="strategy-1",
            inputs=drawdown_inputs,
        )
        self.assertEqual(validate_position_sizing_decision(drawdown).status, "PASS")
        self.assertEqual(drawdown["sizing_status"], "BLOCKED")
        self.assertEqual(drawdown["primary_blocker_code"], "DRAWDOWN_FREEZE_ACTIVE")
        self.assertEqual(drawdown["selected_notional"], "0")

        correlated_inputs = default_sizing_inputs()
        correlated_inputs["correlation_cluster_status"] = "DIVERSIFICATION_FILTERED"
        correlated = build_position_sizing_decision(
            sizing_decision_id="sizing-correlation-cap",
            strategy_unit_id="strategy-1",
            inputs=correlated_inputs,
        )
        self.assertEqual(validate_position_sizing_decision(correlated).status, "PASS")
        self.assertEqual(correlated["sizing_status"], "BLOCKED")
        self.assertEqual(correlated["primary_blocker_code"], "CORRELATION_CAP")
        self.assertEqual(correlated["selected_notional"], "0")

        feedback_inputs = default_sizing_inputs()
        feedback_inputs["realized_performance_feedback_status"] = "ACTIVE"
        feedback_inputs["realized_performance_multiplier"] = "1"
        feedback = build_position_sizing_decision(
            sizing_decision_id="sizing-performance-feedback",
            strategy_unit_id="strategy-1",
            inputs=feedback_inputs,
        )
        self.assertEqual(validate_position_sizing_decision(feedback).status, "PASS")
        self.assertEqual(feedback["sizing_status"], "PASS")
        self.assertEqual(feedback["caps"]["realized_performance_multiplier"], "0.35")
        self.assertLess(float(feedback["selected_notional"]), base_selected)
        self.assertFalse(feedback["live_order_allowed"])

    def test_sizing_live_mutation_blocks(self):
        decision = build_position_sizing_decision(sizing_decision_id="sizing-live", strategy_unit_id="strategy-1")
        decision["can_submit_order"] = True
        decision["sizing_decision_hash"] = sizing_decision_hash(decision)
        result = validate_position_sizing_decision(decision)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_operation_gate_live_mutation_blocks(self):
        report = build_upbit_operational_paper_cycle(operation_gate_id="mvp3-cycle-live")
        report["live_order_ready"] = True
        report["live_order_allowed"] = True
        report["can_live_trade"] = True
        report["operation_gate_hash"] = operation_gate_hash(report)
        result = validate_paper_operation_gate_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_operation_gate_hash_tamper_fails(self):
        report = build_upbit_operational_paper_cycle(operation_gate_id="mvp3-cycle-tamper")
        report["session_id"] = "tampered"
        result = validate_paper_operation_gate_report(report)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
