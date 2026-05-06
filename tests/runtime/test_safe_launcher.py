from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
import json
import os
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import trader1.runtime.boot.safe_launcher as safe_launcher
from trader1.runtime.boot.launcher_guard import ALLOWED_ROOT_LAUNCHERS
from trader1.runtime.boot.safe_launcher import (
    DEFAULT_INTERACTIVE_HEARTBEAT_TICKS,
    ROOT_OPERATOR_HEARTBEAT_INTERVAL_ENV,
    ROOT_OPERATOR_HEARTBEAT_TICKS_ENV,
    build_launcher_report,
    console_heartbeat_line,
    console_safe_monitor_banner,
    emit_console_heartbeats,
    launcher_dashboard_paths,
    launcher_main,
    launcher_report_hash,
    launcher_status_message,
    load_json,
    refresh_launcher_monitor_artifacts,
    root_operator_launcher_main,
    runtime_write_lock,
    should_pause_for_operator,
    source_identity_files,
    validate_launcher_report,
    write_launcher_dashboard,
    write_launcher_report,
    write_launcher_runtime_bundle,
)
from trader1.core.ledger.restart_recovery import build_restart_recovery_report
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle
from trader1.runtime.ledger.paper_ledger_rollup import paper_ledger_rollup_hash
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer import (
    build_upbit_paper_repaired_current_evidence_audited_writer_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_report,
)
from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    build_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.runtime.reconciliation.reconciliation import build_reconciliation_report
from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    build_shadow_observation_actual_runtime_harness_report,
)
from trader1.research.shadow.shadow_observation import build_shadow_observation_report
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    build_shadow_observation_persistent_runtime_report,
)
from trader1.research.shadow.shadow_observation_runtime_orchestration import (
    build_shadow_observation_runtime_orchestration_report,
)
from trader1.research.shadow.shadow_observation_scheduler import build_shadow_observation_scheduler_guard_report
from trader1.research.shadow.shadow_observation_stream import build_shadow_observation_stream_report


def krw_display(value):
    return f"{Decimal(str(value)):,.0f} KRW"


class SafeLauncherTest(unittest.TestCase):
    def _shadow_scheduler_guard_report(self, seed: str) -> dict:
        observations = []
        for index in range(3):
            paper_gate = build_upbit_operational_paper_cycle(
                operation_gate_id=f"{seed}-paper-gate",
                session_id=f"{seed}-paper-{index}",
                requested_entry=True,
            )
            observations.append(
                build_shadow_observation_report(
                    observation_id=f"{seed}-observation-{index}",
                    paper_operation_gate_report=paper_gate,
                    shadow_session_id=f"{seed}-shadow-{index}",
                    shadow_sample_count=30,
                )
            )
        stream = build_shadow_observation_stream_report(
            stream_id=f"{seed}-stream",
            observations=observations,
            min_required_observation_count=3,
            min_required_evidence_span_hours=24,
            evidence_span_hours=24,
        )
        return build_shadow_observation_scheduler_guard_report(
            scheduler_id=f"{seed}-scheduler",
            stream_report=stream,
            writer_id=f"{seed}-writer",
            active_writer_id=f"{seed}-writer",
        )

    def test_all_launcher_reports_validate_and_block_live(self):
        for launcher_name in ALLOWED_ROOT_LAUNCHERS:
            report = build_launcher_report(launcher_name)
            result = validate_launcher_report(report)
            self.assertEqual(result.status, "PASS", launcher_name)
            self.assertFalse(report["live_order_ready"])
            self.assertFalse(report["live_order_allowed"])
            self.assertFalse(report["can_live_trade"])
            self.assertEqual(report["final_action"], "NO_TRADE")

    def test_live_launcher_is_hard_blocked(self):
        for launcher_name in ("UPBIT_LIVE", "BINANCE_LIVE"):
            report = build_launcher_report(launcher_name)
            self.assertTrue(report["live_launcher_hard_blocked"])
            self.assertTrue(report["live_path_hard_blocked"])

    def test_launcher_report_blocks_live_permission_mutation(self):
        report = build_launcher_report("UPBIT_LIVE")
        report["live_order_allowed"] = True
        report["can_live_trade"] = True
        report["report_hash"] = launcher_report_hash(report)
        result = validate_launcher_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_launcher_writes_operator_visible_report_without_live_permission(self):
        report = build_launcher_report("UPBIT_PAPER")
        result = validate_launcher_report(report)
        with TemporaryDirectory() as tmp:
            path = write_launcher_report(report, Path(tmp))
            dashboard_paths = write_launcher_dashboard(report, Path(tmp))
            self.assertTrue(path.exists())
            self.assertTrue(dashboard_paths["dashboard_html"].exists())
            self.assertTrue(dashboard_paths["dashboard_shell"].exists())
            self.assertTrue(dashboard_paths["paper_portfolio_snapshot"].exists())
            self.assertTrue(dashboard_paths["paper_current_truth_refresh_report"].exists())
            self.assertTrue(dashboard_paths["paper_runtime_truth_state_report"].exists())
            self.assertTrue(dashboard_paths["stability_history"].exists())
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            current_truth_refresh = load_json(dashboard_paths["paper_current_truth_refresh_report"])
            runtime_truth = load_json(dashboard_paths["paper_runtime_truth_state_report"])
            stability_history = load_json(dashboard_paths["stability_history"])
            self.assertEqual(dashboard_shell["portfolio_snapshot"]["status"], "VERIFIED")
            self.assertEqual(current_truth_refresh["refresh_status"], "PASS_PAPER_CURRENT_TRUTH_REFRESHED")
            self.assertEqual(runtime_truth["runtime_truth_status"], "MONITOR_ALIVE_ENGINE_NOT_PROVEN")
            self.assertIn("PAPER engine not proven", dashboard_shell["operation_status"]["message"])
            self.assertEqual(
                current_truth_refresh["source_portfolio_snapshot_hash"],
                load_json(dashboard_paths["paper_portfolio_snapshot"])["snapshot_hash"],
            )
            self.assertFalse(current_truth_refresh["current_evidence_write_allowed"])
            self.assertFalse(current_truth_refresh["audited_current_evidence_writer"])
            self.assertFalse(current_truth_refresh["live_order_allowed"])
            self.assertEqual(stability_history["schema_id"], "trader1.runtime_stability_history.v1")
            self.assertEqual(stability_history["sample_count"], 1)
            self.assertFalse(stability_history["live_order_allowed"])
            self.assertIn("Simulated PAPER ledger", dashboard_shell["portfolio_snapshot"]["cash"]["detail"])
            self.assertIn("system", path.parts)
            message = launcher_status_message(report, result, path, dashboard_paths["dashboard_html"], dashboard_opened=False)
            self.assertIn("live_order_allowed=false", message)
            self.assertIn(str(path), message)
            self.assertIn(str(dashboard_paths["dashboard_html"]), message)
            source_files = {source["filename"] for source in dashboard_shell["source_artifacts"]}
            self.assertIn("paper_current_truth_refresh_report.json", source_files)
            self.assertIn("paper_runtime_truth_state_report.json", source_files)

    def test_launcher_dashboard_loads_audited_current_evidence_portfolio_truth(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_paths = launcher_dashboard_paths(report)
            target_paths = launcher_dashboard_paths(report, root)
            implementation_prep = load_json(
                source_paths["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report"]
            )
            ledger_rollup = load_json(source_paths["paper_ledger_rollup_report"])
            target_paths[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report"
            ].parent.mkdir(parents=True, exist_ok=True)
            target_paths[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report"
            ].write_text(json.dumps(implementation_prep, sort_keys=True), encoding="utf-8")
            writer_report = build_upbit_paper_repaired_current_evidence_audited_writer_report(
                root=root,
                source_implementation_prep_report=implementation_prep,
                source_ledger_rollup_report=ledger_rollup,
                audited_writer_id="test-safe-launcher-audited-current-evidence-writer",
            )
            write_upbit_paper_repaired_current_evidence_audited_writer_report(
                root=root,
                report=writer_report,
            )
            audited_snapshot = load_json(target_paths["audited_current_evidence_snapshot"])
            expected_cash_display = krw_display(audited_snapshot["verified_cash_krw"])
            expected_equity_display = krw_display(audited_snapshot["verified_equity_krw"])
            expected_total_pnl_display = krw_display(audited_snapshot["verified_total_pnl_krw"])

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])

        portfolio = dashboard_shell["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "VERIFIED")
        self.assertEqual(portfolio["source"], "audited_current_evidence_snapshot.json")
        self.assertEqual(portfolio["configured_paper_capital"]["value_display"], "1,000,000 KRW")
        self.assertEqual(portfolio["cash"]["value_display"], expected_cash_display)
        self.assertEqual(portfolio["equity"]["value_display"], expected_equity_display)
        self.assertEqual(portfolio["total_pnl"]["value_display"], expected_total_pnl_display)
        self.assertFalse(dashboard_shell["live_order_ready"])
        self.assertFalse(dashboard_shell["live_order_allowed"])
        self.assertFalse(dashboard_shell["can_live_trade"])
        self.assertFalse(dashboard_shell["scale_up_allowed"])
        source_status = {
            source["artifact_id"]: source["freshness_status"]
            for source in dashboard_shell["source_artifacts"]
            if source["artifact_id"]
            in {
                "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER",
                "AUDITED_CURRENT_EVIDENCE_SNAPSHOT",
                "AUDITED_PAPER_PORTFOLIO_SNAPSHOT",
            }
        }
        self.assertEqual(
            source_status,
            {
                "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER": "PASS",
                "AUDITED_CURRENT_EVIDENCE_SNAPSHOT": "PASS",
                "AUDITED_PAPER_PORTFOLIO_SNAPSHOT": "PASS",
            },
        )

    def test_launcher_autowrites_paper_current_evidence_when_runtime_checks_pass(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-launcher-auto-current-evidence-writer",
                session_id=report["session_id"],
                requested_cycle_count=2,
            )
            source_paths = launcher_dashboard_paths(report)
            target_paths = launcher_dashboard_paths(report, root)
            implementation_prep = load_json(
                source_paths["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report"]
            )
            target_paths[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report"
            ].parent.mkdir(parents=True, exist_ok=True)
            target_paths[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report"
            ].write_text(json.dumps(implementation_prep, sort_keys=True), encoding="utf-8")

            ledger_rollup = load_json(target_paths["paper_ledger_rollup_report"])
            idempotency = build_upbit_paper_ledger_idempotency_runtime_evidence_report(
                root=root,
                session_id=report["session_id"],
            )
            target_paths["upbit_paper_ledger_idempotency_runtime_evidence_report"].parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            target_paths["upbit_paper_ledger_idempotency_runtime_evidence_report"].write_text(
                json.dumps(idempotency, indent=2),
                encoding="utf-8",
            )
            reconciliation = build_reconciliation_report(
                reconciliation_id="test-launcher-auto-current-evidence-reconciliation",
                exchange=report["exchange"],
                market_type=report["market_type"],
                mode=report["mode"],
                session_id=report["session_id"],
                ledger_head_hash=ledger_rollup["latest_ledger_head_hash"],
            )
            target_paths["reconciliation_report"].parent.mkdir(parents=True, exist_ok=True)
            target_paths["reconciliation_report"].write_text(
                json.dumps(reconciliation, indent=2),
                encoding="utf-8",
            )

            dashboard_paths = write_launcher_dashboard(report, root)
            writer_report = load_json(
                target_paths["upbit_paper_repaired_current_evidence_audited_writer_report"]
            )
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])

        self.assertEqual(
            writer_report["audited_writer_id"],
            "upbit-paper-continuous-dashboard-current-evidence-writer",
        )
        self.assertIn(
            writer_report["writer_status"],
            {
                "PASS_AUDITED_CURRENT_EVIDENCE_WRITTEN",
                "PASS_AUDITED_CURRENT_EVIDENCE_ALREADY_WRITTEN",
            },
        )
        self.assertTrue(writer_report["current_evidence_artifact_written"])
        self.assertTrue(writer_report["portfolio_truth_artifact_written"])
        self.assertFalse(writer_report["live_order_allowed"])
        self.assertFalse(writer_report["can_live_trade"])
        self.assertFalse(writer_report["scale_up_allowed"])
        self.assertEqual(
            dashboard_shell["portfolio_snapshot"]["source"],
            "audited_current_evidence_snapshot.json",
        )
        source_status = {
            source["artifact_id"]: source["freshness_status"]
            for source in dashboard_shell["source_artifacts"]
            if source["artifact_id"]
            in {
                "PAPER_CURRENT_TRUTH_REFRESH",
                "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER",
                "AUDITED_CURRENT_EVIDENCE_SNAPSHOT",
                "AUDITED_PAPER_PORTFOLIO_SNAPSHOT",
            }
        }
        self.assertEqual(source_status["PAPER_CURRENT_TRUTH_REFRESH"], "PASS")
        self.assertEqual(source_status["UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER"], "PASS")
        self.assertEqual(source_status["AUDITED_CURRENT_EVIDENCE_SNAPSHOT"], "PASS")
        self.assertEqual(source_status["AUDITED_PAPER_PORTFOLIO_SNAPSHOT"], "PASS")
        self.assertFalse(dashboard_shell["live_order_allowed"])
        self.assertFalse(dashboard_shell["can_live_trade"])
        self.assertFalse(dashboard_shell["scale_up_allowed"])

    def test_launcher_runtime_bundle_writes_under_single_session_lock(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            report_path, dashboard_paths = write_launcher_runtime_bundle(report, Path(tmp))
            runtime_dir = report_path.parents[1]
            self.assertFalse((runtime_dir / ".runtime_write.lock").exists())
            self.assertTrue(report_path.exists())
            self.assertTrue(dashboard_paths["summary"].exists())
            self.assertTrue(dashboard_paths["heartbeat"].exists())
            self.assertTrue(dashboard_paths["stability_history"].exists())
            self.assertTrue(dashboard_paths["dashboard_html"].exists())
            self.assertEqual(load_json(dashboard_paths["summary"])["session_id"], report["session_id"])
            heartbeat = load_json(dashboard_paths["heartbeat"])
            self.assertEqual(heartbeat["session_id"], report["session_id"])
            self.assertIn("Runtime artifact pressure", heartbeat["components"]["disk"]["message"])
            self.assertEqual(load_json(dashboard_paths["stability_history"])["session_id"], report["session_id"])

    def test_launcher_dashboard_uses_exact_scoped_paper_operation_gate_for_evidence_progress(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate_path = launcher_dashboard_paths(report, root)["paper_operation_gate_report"]
            gate_path.parent.mkdir(parents=True, exist_ok=True)
            gate = build_upbit_operational_paper_cycle(
                operation_gate_id="test-launcher-scoped-paper-gate",
                session_id=report["session_id"],
            )
            gate_path.write_text(json.dumps(gate, indent=2), encoding="utf-8")
            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            maturity = dashboard_shell["profitability_maturity"]
            self.assertEqual(maturity["status"], "COLLECTING")
            self.assertLess(maturity["evidence_progress_pct"], 100)
            self.assertEqual(maturity["evidence_progress_status"], "IN_PROGRESS")
            self.assertTrue(any(item["status"] == "MISSING" for item in maturity["evidence_checklist"]))
            self.assertEqual(maturity["optimizer_ranking_action"], "BLOCK_RANKING")
            self.assertEqual(maturity["primary_blocker_code"], "SAMPLE_INSUFFICIENT")
            self.assertFalse(maturity["live_order_allowed"])
            self.assertFalse(maturity["scale_up_allowed"])

    def test_launcher_dashboard_binds_fresh_scoped_upbit_paper_runtime_cycle(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_path = launcher_dashboard_paths(report, root)["upbit_paper_runtime_cycle_report"]
            runtime_path.parent.mkdir(parents=True, exist_ok=True)
            runtime_cycle = build_upbit_paper_runtime_cycle_report(
                cycle_id="test-launcher-upbit-runtime-cycle",
                session_id=report["session_id"],
            )
            runtime_path.write_text(json.dumps(runtime_cycle, indent=2), encoding="utf-8")

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            summary = load_json(dashboard_paths["summary"])
            portfolio = dashboard_shell["portfolio_snapshot"]

            self.assertEqual(portfolio["status"], "VERIFIED")
            self.assertEqual(summary["portfolio"]["source"], "LEDGER")
            self.assertEqual(summary["portfolio"]["freshness_status"], "PASS")
            self.assertEqual(summary["portfolio"]["open_position_count"], 1)
            self.assertEqual(len(summary["positions"]), 1)
            self.assertTrue(summary["positions"])
            self.assertTrue(summary["entry_candidates"])
            self.assertEqual(summary["entry_candidates"][0]["symbol"], "KRW-BTC")
            self.assertEqual(summary["market_context"]["regime"], runtime_cycle["regime"])
            self.assertFalse(summary["live_ready"]["live_order_ready"])
            self.assertFalse(summary["live_ready"]["live_order_allowed"])
            self.assertTrue(summary["live_ready"]["blocks_live_order"])
            self.assertFalse(dashboard_shell["live_order_ready"])
            self.assertFalse(dashboard_shell["live_order_allowed"])
            self.assertFalse(dashboard_shell["can_live_trade"])
            self.assertFalse(dashboard_shell["scale_up_allowed"])
            self.assertIn("Simulated PAPER ledger", portfolio["cash"]["detail"])

    def test_launcher_dashboard_prefers_scoped_paper_ledger_rollup_portfolio(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-launcher-paper-rollup-preferred",
                session_id=report["session_id"],
                requested_cycle_count=2,
            )

            dashboard_paths = write_launcher_dashboard(report, root)
            summary = load_json(dashboard_paths["summary"])
            portfolio_snapshot = load_json(dashboard_paths["paper_portfolio_snapshot"])

            self.assertEqual(portfolio_snapshot["source"], "PAPER_LEDGER_ROLLUP")
            self.assertEqual(
                portfolio_snapshot["source_runtime_cycle_id"],
                "test-launcher-paper-rollup-preferred-cycle-2",
            )
            self.assertEqual(
                portfolio_snapshot["source_paper_ledger_head_hash"],
                summary["portfolio"]["source_paper_ledger_head_hash"],
            )
            self.assertEqual(summary["portfolio"]["source"], "LEDGER")
            self.assertEqual(summary["portfolio"]["open_position_count"], 1)
            self.assertEqual(len(summary["positions"]), 1)
            self.assertEqual(summary["positions"][0]["source"], "PAPER_LEDGER_ROLLUP")
            self.assertFalse(summary["live_ready"]["live_order_allowed"])

    def test_launcher_dashboard_binds_scoped_upbit_paper_persistent_loop_status(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-launcher-paper-persistent-loop-status",
                session_id=report["session_id"],
                requested_cycle_count=1,
            )

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            canonical_path = launcher_dashboard_paths(report, root)["upbit_paper_persistent_loop_report"]

            self.assertTrue(canonical_path.exists())
            self.assertEqual(load_json(canonical_path)["loop_hash"], loop["loop_hash"])
            status = dashboard_shell["paper_persistent_loop_status"]
            self.assertEqual(status["status"], "PASS")
            self.assertEqual(status["source"], "upbit_paper_persistent_loop_report.json")
            self.assertEqual(status["completed_cycle_count"], 1)
            self.assertEqual(status["runtime_evidence_role"], "BOUNDED_PAPER_LOOP_NOT_LONG_RUN_EVIDENCE")
            self.assertFalse(status["long_run_evidence_eligible"])
            self.assertFalse(status["promotion_eligible"])
            self.assertFalse(status["live_order_allowed"])
            self.assertFalse(status["can_live_trade"])
            self.assertFalse(status["scale_up_allowed"])
            source_files = {source["filename"] for source in dashboard_shell["source_artifacts"]}
            self.assertIn("upbit_paper_persistent_loop_report.json", source_files)
            self.assertFalse(dashboard_shell["live_order_allowed"])

    def test_launcher_dashboard_does_not_prefer_stale_paper_ledger_rollup_as_verified_portfolio(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-launcher-paper-rollup-stale",
                session_id=report["session_id"],
                requested_cycle_count=2,
            )
            rollup_path = launcher_dashboard_paths(report, root)["paper_ledger_rollup_report"]
            rollup = json.loads(rollup_path.read_text(encoding="utf-8"))
            rollup["generated_at_utc"] = "2000-01-01T00:00:00Z"
            rollup["rollup_hash"] = paper_ledger_rollup_hash(rollup)
            rollup_path.write_text(json.dumps(rollup, indent=2), encoding="utf-8")

            dashboard_paths = write_launcher_dashboard(report, root)
            summary = load_json(dashboard_paths["summary"])
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            portfolio_snapshot = load_json(dashboard_paths["paper_portfolio_snapshot"])

            self.assertEqual(summary["portfolio"]["source"], "LEDGER")
            self.assertEqual(portfolio_snapshot["source"], "PAPER_LEDGER_SCAFFOLD")
            self.assertNotEqual(portfolio_snapshot["source"], "PAPER_LEDGER_ROLLUP")
            self.assertTrue(summary["positions"])
            self.assertNotEqual(summary["positions"][0]["source"], "PAPER_LEDGER_ROLLUP")
            self.assertEqual(dashboard_shell["portfolio_snapshot"]["status"], "VERIFIED")
            self.assertFalse(summary["live_ready"]["live_order_allowed"])
            self.assertFalse(dashboard_shell["live_order_allowed"])

    def test_launcher_dashboard_does_not_fallback_to_initial_portfolio_when_stale_rollup_exists(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-launcher-paper-rollup-stale-no-cycle",
                session_id=report["session_id"],
                requested_cycle_count=2,
            )
            rollup_path = launcher_dashboard_paths(report, root)["paper_ledger_rollup_report"]
            rollup = json.loads(rollup_path.read_text(encoding="utf-8"))
            rollup["generated_at_utc"] = "2000-01-01T00:00:00Z"
            rollup["rollup_hash"] = paper_ledger_rollup_hash(rollup)
            rollup_path.write_text(json.dumps(rollup, indent=2), encoding="utf-8")
            latest_runtime_path = launcher_dashboard_paths(report, root)["upbit_paper_runtime_cycle_report"]
            latest_runtime_path.unlink()

            dashboard_paths = write_launcher_dashboard(report, root)
            summary = load_json(dashboard_paths["summary"])
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])

            self.assertEqual(summary["portfolio"]["source"], "SUMMARY_BUILDER")
            self.assertEqual(summary["portfolio"]["freshness_status"], "UNTESTED")
            self.assertEqual(dashboard_shell["portfolio_snapshot"]["status"], "UNVERIFIED")
            self.assertFalse(dashboard_paths["paper_portfolio_snapshot"].exists())
            self.assertFalse(summary["live_ready"]["live_order_allowed"])
            self.assertFalse(dashboard_shell["live_order_allowed"])

    def test_launcher_dashboard_loads_shadow_runtime_harness_as_display_only(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            harness_path = paths["shadow_runtime_harness_report"]
            harness_path.parent.mkdir(parents=True, exist_ok=True)
            harness_report = build_shadow_observation_actual_runtime_harness_report(
                harness_id=report["session_id"],
                runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
                monotonic_timer_started=True,
                monotonic_timer_stopped=True,
                measured_runtime_seconds_verified=True,
            )
            harness_path.write_text(json.dumps(harness_report, indent=2), encoding="utf-8")

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            harness_status = dashboard_shell["shadow_runtime_harness_status"]

            self.assertEqual(harness_status["status"], "SHORT_WINDOW_EXECUTED")
            self.assertEqual(harness_status["runtime_evidence_status"], "BLOCKED_LONG_RUN_EVIDENCE_MISSING")
            self.assertEqual(harness_status["optimizer_input_role"], "BLOCKER_ONLY_NOT_RANKING_INPUT")
            self.assertFalse(harness_status["long_run_evidence_eligible"])
            self.assertFalse(harness_status["live_order_ready"])
            self.assertFalse(harness_status["live_order_allowed"])
            self.assertFalse(harness_status["can_live_trade"])
            self.assertFalse(harness_status["scale_up_allowed"])
            self.assertIn("PAPER/SHADOW check", dashboard_paths["dashboard_html"].read_text(encoding="utf-8"))

    def test_launcher_dashboard_loads_runtime_orchestration_guard_as_display_only(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            for artifact_path in (
                paths["shadow_persistent_runtime_report"],
                paths["shadow_runtime_harness_report"],
                paths["shadow_runtime_orchestration_report"],
            ):
                artifact_path.parent.mkdir(parents=True, exist_ok=True)

            persistent_report = build_shadow_observation_persistent_runtime_report(
                runtime_id=report["session_id"],
                scheduler_guard_report=self._shadow_scheduler_guard_report("test-launcher-runtime-orchestration"),
                requested_cycle_count=3,
                completed_cycle_count=3,
                max_cycle_count=20,
            )
            harness_report = build_shadow_observation_actual_runtime_harness_report(
                harness_id=report["session_id"],
                requested_cycle_count=3,
                completed_cycle_count=3,
                observations_per_cycle=2,
                measured_runtime_seconds=90,
                runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
                monotonic_timer_started=True,
                monotonic_timer_stopped=True,
                measured_runtime_seconds_verified=True,
                source_runtime_report=persistent_report,
            )
            orchestration_report = build_shadow_observation_runtime_orchestration_report(
                orchestration_id=report["session_id"],
                persistent_runtime_report=persistent_report,
                actual_runtime_harness_report=harness_report,
            )
            paths["shadow_persistent_runtime_report"].write_text(json.dumps(persistent_report, indent=2), encoding="utf-8")
            paths["shadow_runtime_harness_report"].write_text(json.dumps(harness_report, indent=2), encoding="utf-8")
            paths["shadow_runtime_orchestration_report"].write_text(json.dumps(orchestration_report, indent=2), encoding="utf-8")

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            orchestration_status = dashboard_shell["shadow_runtime_orchestration_status"]
            source_files = {source["filename"] for source in dashboard_shell["source_artifacts"]}

            self.assertIn("runtime_orchestration_report.json", source_files)
            self.assertEqual(dashboard_shell["shadow_persistent_runtime_status"]["status"], "STUB_ONLY")
            self.assertEqual(dashboard_shell["shadow_runtime_harness_status"]["status"], "SHORT_WINDOW_EXECUTED")
            self.assertEqual(orchestration_status["status"], "BOUNDARY_VERIFIED")
            self.assertEqual(orchestration_status["color_token"], "blue")
            self.assertEqual(orchestration_status["optimizer_ranking_action"], "BLOCK_RANKING")
            self.assertEqual(orchestration_status["observed_actual_runtime_seconds"], 0)
            self.assertFalse(orchestration_status["live_order_ready"])
            self.assertFalse(orchestration_status["live_order_allowed"])
            self.assertFalse(orchestration_status["can_live_trade"])
            self.assertFalse(orchestration_status["scale_up_allowed"])
            self.assertFalse(dashboard_shell["live_order_allowed"])
            html = dashboard_paths["dashboard_html"].read_text(encoding="utf-8")
            self.assertIn("Runtime Orchestration Guard", html)
            self.assertIn("BLOCK_RANKING", html)

    def test_launcher_dashboard_blocks_unsafe_shadow_runtime_harness_display(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            harness_path = paths["shadow_runtime_harness_report"]
            harness_path.parent.mkdir(parents=True, exist_ok=True)
            harness_report = build_shadow_observation_actual_runtime_harness_report(
                harness_id=report["session_id"],
                runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
                monotonic_timer_started=True,
                monotonic_timer_stopped=True,
                measured_runtime_seconds_verified=True,
            )
            harness_report["live_order_allowed"] = True
            harness_path.write_text(json.dumps(harness_report, indent=2), encoding="utf-8")

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            harness_status = dashboard_shell["shadow_runtime_harness_status"]

            self.assertEqual(harness_status["status"], "BLOCKED")
            self.assertEqual(harness_status["severity"], "ERROR")
            self.assertIn("unsafe", harness_status["one_line_summary"])
            self.assertFalse(harness_status["live_order_allowed"])
            self.assertFalse(dashboard_shell["live_order_allowed"])

    def test_launcher_dashboard_ignores_cross_session_paper_operation_gate(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate_path = launcher_dashboard_paths(report, root)["paper_operation_gate_report"]
            gate_path.parent.mkdir(parents=True, exist_ok=True)
            gate = build_upbit_operational_paper_cycle(
                operation_gate_id="test-launcher-cross-session-paper-gate",
                session_id="different_session",
            )
            gate_path.write_text(json.dumps(gate, indent=2), encoding="utf-8")
            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            maturity = dashboard_shell["profitability_maturity"]
            self.assertEqual(maturity["status"], "COLLECTING")
            self.assertEqual(maturity["evidence_source"], "NOT_LOADED")
            self.assertEqual(maturity["evidence_progress_pct"], 0)
            self.assertFalse(maturity["live_order_allowed"])
            self.assertFalse(maturity["scale_up_allowed"])

    def test_launcher_dashboard_uses_exact_scoped_paper_exposure_quality_report(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            exposure_path = launcher_dashboard_paths(report, root)["paper_exposure_quality_report"]
            exposure_path.parent.mkdir(parents=True, exist_ok=True)
            exposure_report = json.loads(
                (Path(__file__).resolve().parents[2] / "tests" / "validators" / "fixtures" / "paper_exposure_quality_pass.json").read_text(
                    encoding="utf-8"
                )
            )
            exposure_report["session_id"] = report["session_id"]
            exposure_report["exchange"] = report["exchange"]
            exposure_report["market_type"] = report["market_type"]
            exposure_report["mode"] = report["mode"]
            exposure_path.write_text(json.dumps(exposure_report, indent=2), encoding="utf-8")
            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            risk = dashboard_shell["risk_exposure_snapshot"]
            self.assertEqual(risk["paper_exposure_quality_status"], "PASS_PAPER_ONLY")
            self.assertEqual(risk["paper_exposure_quality_source"], "paper_exposure_quality_report.json")
            self.assertEqual(risk["paper_exposure_quality_recommendation"], "KEEP_PAPER")
            self.assertFalse(risk["live_order_allowed"])
            self.assertFalse(risk["scale_up_allowed"])

    def test_launcher_dashboard_ignores_cross_session_paper_exposure_quality_report(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            exposure_path = launcher_dashboard_paths(report, root)["paper_exposure_quality_report"]
            exposure_path.parent.mkdir(parents=True, exist_ok=True)
            exposure_report = json.loads(
                (Path(__file__).resolve().parents[2] / "tests" / "validators" / "fixtures" / "paper_exposure_quality_pass.json").read_text(
                    encoding="utf-8"
                )
            )
            exposure_report["session_id"] = "different_session"
            exposure_path.write_text(json.dumps(exposure_report, indent=2), encoding="utf-8")
            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            risk = dashboard_shell["risk_exposure_snapshot"]
            self.assertEqual(risk["paper_exposure_quality_status"], "UNAVAILABLE")
            self.assertEqual(risk["paper_exposure_quality_source"], "NOT_LOADED")
            self.assertFalse(risk["live_order_allowed"])
            self.assertFalse(risk["scale_up_allowed"])

    def test_launcher_dashboard_binds_exact_scoped_reconciliation_and_restart_reports(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paths["reconciliation_report"].parent.mkdir(parents=True, exist_ok=True)
            reconciliation_report = build_reconciliation_report(
                reconciliation_id="test-launcher-reconciliation-pass",
                exchange=report["exchange"],
                market_type=report["market_type"],
                mode=report["mode"],
                session_id=report["session_id"],
            )
            restart_report = build_restart_recovery_report(
                restart_id="test-launcher-restart-pass",
                exchange=report["exchange"],
                market_type=report["market_type"],
                mode=report["mode"],
                session_id=report["session_id"],
            )
            paths["reconciliation_report"].write_text(json.dumps(reconciliation_report, indent=2), encoding="utf-8")
            paths["restart_recovery_report"].write_text(json.dumps(restart_report, indent=2), encoding="utf-8")

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]
            self.assertEqual(reconciliation["status"], "PASS")
            self.assertEqual(reconciliation["color_token"], "green")
            self.assertEqual(reconciliation["reconciliation_status"], "PASS")
            self.assertEqual(reconciliation["restart_recovery_status"], "PASS")
            self.assertEqual(reconciliation["ledger_state"], "PAPER_LEDGER_MATCHED")
            self.assertEqual(reconciliation["single_writer_state"], "RECOVERED")
            self.assertEqual(reconciliation["idempotency_state"], "RECOVERED")
            self.assertEqual(reconciliation["primary_blocker_code"], "LIVE_READY_MISSING")
            self.assertFalse(reconciliation["live_order_allowed"])
            self.assertFalse(reconciliation["can_submit_order"])

    def test_launcher_dashboard_surfaces_reconciliation_mismatch_as_red_blocker(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paths["reconciliation_report"].parent.mkdir(parents=True, exist_ok=True)
            reconciliation_report = build_reconciliation_report(
                reconciliation_id="test-launcher-reconciliation-mismatch",
                exchange=report["exchange"],
                market_type=report["market_type"],
                mode=report["mode"],
                session_id=report["session_id"],
                exchange_snapshot={
                    "exchange": report["exchange"],
                    "market_type": report["market_type"],
                    "mode": report["mode"],
                    "session_id": report["session_id"],
                    "balances": {"KRW": "1000000"},
                    "positions": [],
                    "open_orders": [],
                },
                internal_state={
                    "exchange": report["exchange"],
                    "market_type": report["market_type"],
                    "mode": report["mode"],
                    "session_id": report["session_id"],
                    "balances": {"KRW": "900000"},
                    "positions": [],
                    "open_orders": [],
                },
            )
            restart_report = build_restart_recovery_report(
                restart_id="test-launcher-restart-for-mismatch",
                exchange=report["exchange"],
                market_type=report["market_type"],
                mode=report["mode"],
                session_id=report["session_id"],
            )
            paths["reconciliation_report"].write_text(json.dumps(reconciliation_report, indent=2), encoding="utf-8")
            paths["restart_recovery_report"].write_text(json.dumps(restart_report, indent=2), encoding="utf-8")

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]
            self.assertEqual(reconciliation["status"], "BLOCKED")
            self.assertEqual(reconciliation["severity"], "ERROR")
            self.assertEqual(reconciliation["color_token"], "red")
            self.assertEqual(reconciliation["mismatch_count"], 1)
            self.assertEqual(reconciliation["primary_blocker_code"], "RECONCILIATION_REQUIRED")
            self.assertFalse(reconciliation["live_order_allowed"])

    def test_launcher_dashboard_loads_post_rerun_review_guidance_as_red_blocker(self):
        report = build_launcher_report("UPBIT_PAPER")
        fixture_root = Path(__file__).resolve().parents[2]
        fixture_path = (
            fixture_root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json"
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paths["upbit_paper_post_rerun_operator_reconciliation_review_guidance_report"].parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            paths["upbit_paper_post_rerun_operator_reconciliation_review_guidance_report"].write_text(
                fixture_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]
            self.assertEqual(reconciliation["status"], "BLOCKED")
            self.assertEqual(reconciliation["severity"], "ERROR")
            self.assertEqual(reconciliation["color_token"], "red")
            self.assertEqual(
                reconciliation["source"],
                "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json",
            )
            self.assertEqual(
                reconciliation["post_rerun_review_guidance_status"],
                "BLOCKED_RECONCILIATION_REVIEW_REQUIRED",
            )
            self.assertEqual(reconciliation["post_rerun_review_step_count"], 4)
            self.assertEqual(reconciliation["post_rerun_forbidden_output_count"], 6)
            self.assertEqual(reconciliation["post_rerun_guidance_current_evidence_write_allowed_count"], 0)
            self.assertEqual(dashboard_shell["operator_action_summary"]["status"], "BLOCKED")
            self.assertFalse(dashboard_shell["operator_action_summary"]["safe_to_continue_paper"])
            self.assertFalse(dashboard_shell["live_order_allowed"])
            self.assertFalse(dashboard_shell["scale_up_allowed"])

    def test_launcher_dashboard_loads_post_rerun_operator_reconciliation_queue_as_red_blocker(self):
        report = build_launcher_report("UPBIT_PAPER")
        fixture_root = Path(__file__).resolve().parents[2]
        fixture_path = (
            fixture_root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_rerun_operator_reconciliation_queue_report.json"
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paths["upbit_paper_post_rerun_operator_reconciliation_queue_report"].parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            paths["upbit_paper_post_rerun_operator_reconciliation_queue_report"].write_text(
                fixture_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]

            self.assertEqual(reconciliation["status"], "BLOCKED")
            self.assertEqual(reconciliation["severity"], "ERROR")
            self.assertEqual(reconciliation["color_token"], "red")
            self.assertEqual(
                reconciliation["source"],
                "upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
            )
            self.assertEqual(reconciliation["post_rerun_operator_reconciliation_queue_status"], "BLOCKED")
            self.assertEqual(reconciliation["post_rerun_operator_reconciliation_queue_validation_status"], "PASS")
            self.assertEqual(reconciliation["post_rerun_operator_queue_item_count"], 8)
            self.assertEqual(reconciliation["post_rerun_operator_queue_review_ready_reconciliation_item_count"], 8)
            self.assertEqual(reconciliation["post_rerun_operator_queue_current_evidence_write_allowed_count"], 0)
            self.assertEqual(reconciliation["post_rerun_operator_queue_candidate_current_evidence_usable_count"], 0)
            self.assertEqual(dashboard_shell["operator_action_summary"]["status"], "BLOCKED")
            self.assertFalse(dashboard_shell["operator_action_summary"]["safe_to_continue_paper"])
            self.assertFalse(dashboard_shell["live_order_allowed"])
            self.assertFalse(dashboard_shell["scale_up_allowed"])

    def test_launcher_dashboard_loads_post_rerun_resolution_audit_as_red_blocker(self):
        report = build_launcher_report("UPBIT_PAPER")
        fixture_root = Path(__file__).resolve().parents[2]
        fixture_runtime = (
            fixture_root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paper_runtime = paths["upbit_paper_post_rerun_operator_resolution_audit_report"].parent
            paper_runtime.mkdir(parents=True, exist_ok=True)
            for filename in (
                "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json",
                "upbit_paper_post_rerun_reconciliation_decision_audit_report.json",
                "upbit_paper_post_rerun_operator_resolution_audit_report.json",
            ):
                (paper_runtime / filename).write_text(
                    (fixture_runtime / filename).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]
            self.assertEqual(reconciliation["status"], "BLOCKED")
            self.assertEqual(reconciliation["severity"], "ERROR")
            self.assertEqual(reconciliation["color_token"], "red")
            self.assertEqual(
                reconciliation["source"],
                "upbit_paper_post_rerun_operator_resolution_audit_report.json",
            )
            self.assertEqual(
                reconciliation["post_rerun_resolution_audit_status"],
                "UNRESOLVED_RECONCILIATION_REVIEW_ONLY",
            )
            self.assertEqual(reconciliation["post_rerun_resolution_audit_validation_status"], "PASS")
            self.assertEqual(reconciliation["post_rerun_resolution_unresolved_item_count"], 8)
            self.assertEqual(reconciliation["post_rerun_resolution_resolved_item_count"], 0)
            self.assertEqual(reconciliation["post_rerun_resolution_current_evidence_write_allowed_count"], 0)
            self.assertEqual(reconciliation["post_rerun_resolution_source_review_guidance_file_load_status"], "PASS")
            self.assertEqual(reconciliation["post_rerun_resolution_source_decision_audit_file_load_status"], "PASS")
            self.assertEqual(dashboard_shell["operator_action_summary"]["status"], "BLOCKED")
            self.assertFalse(dashboard_shell["operator_action_summary"]["safe_to_continue_paper"])
            self.assertFalse(dashboard_shell["live_order_allowed"])
            self.assertFalse(dashboard_shell["scale_up_allowed"])

    def test_launcher_dashboard_loads_post_rerun_resolution_closure_as_red_blocker(self):
        report = build_launcher_report("UPBIT_PAPER")
        fixture_root = Path(__file__).resolve().parents[2]
        fixture_runtime = (
            fixture_root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paper_runtime = paths["upbit_paper_post_rerun_resolution_current_evidence_closure_report"].parent
            paper_runtime.mkdir(parents=True, exist_ok=True)
            for filename in (
                "upbit_paper_post_rerun_operator_resolution_audit_report.json",
                "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json",
            ):
                (paper_runtime / filename).write_text(
                    (fixture_runtime / filename).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]
            self.assertEqual(reconciliation["status"], "BLOCKED")
            self.assertEqual(reconciliation["severity"], "ERROR")
            self.assertEqual(reconciliation["color_token"], "red")
            self.assertEqual(
                reconciliation["source"],
                "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json",
            )
            self.assertEqual(
                reconciliation["post_rerun_resolution_closure_status"],
                "CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED",
            )
            self.assertEqual(reconciliation["post_rerun_resolution_closure_validation_status"], "PASS")
            self.assertEqual(
                reconciliation["post_rerun_resolution_closure_source_resolution_audit_file_load_status"],
                "PASS",
            )
            self.assertEqual(reconciliation["post_rerun_resolution_closure_closed_item_count"], 8)
            self.assertEqual(reconciliation["post_rerun_resolution_closure_current_evidence_closed_count"], 8)
            self.assertEqual(reconciliation["post_rerun_resolution_closure_current_evidence_write_allowed_count"], 0)
            self.assertEqual(dashboard_shell["operator_action_summary"]["status"], "BLOCKED")
            self.assertFalse(dashboard_shell["operator_action_summary"]["safe_to_continue_paper"])
            self.assertFalse(dashboard_shell["live_order_allowed"])
            self.assertFalse(dashboard_shell["scale_up_allowed"])

    def test_launcher_dashboard_loads_post_repair_reconciliation_as_red_blocker(self):
        report = build_launcher_report("UPBIT_PAPER")
        fixture_root = Path(__file__).resolve().parents[2]
        fixture_path = (
            fixture_root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_repair_reconciliation_report.json"
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paths["upbit_paper_post_repair_reconciliation_report"].parent.mkdir(parents=True, exist_ok=True)
            paths["upbit_paper_post_repair_reconciliation_report"].write_text(
                fixture_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]

            self.assertEqual(reconciliation["status"], "BLOCKED")
            self.assertEqual(reconciliation["severity"], "ERROR")
            self.assertEqual(reconciliation["color_token"], "red")
            self.assertEqual(reconciliation["source"], "upbit_paper_post_repair_reconciliation_report.json")
            self.assertEqual(reconciliation["primary_blocker_code"], "POST_REPAIR_RECONCILIATION_REQUIRED")
            self.assertEqual(reconciliation["post_repair_reconciliation_status"], "BLOCKED")
            self.assertEqual(reconciliation["post_repair_reconciliation_validation_status"], "PASS")
            self.assertEqual(reconciliation["post_repair_candidate_current_evidence_usable_count"], 0)
            self.assertEqual(dashboard_shell["operator_action_summary"]["status"], "BLOCKED")
            self.assertFalse(dashboard_shell["operator_action_summary"]["safe_to_continue_paper"])
            self.assertFalse(dashboard_shell["live_order_allowed"])
            self.assertFalse(dashboard_shell["scale_up_allowed"])

    def test_launcher_dashboard_loads_repair_operator_queue_as_red_blocker(self):
        report = build_launcher_report("UPBIT_PAPER")
        fixture_root = Path(__file__).resolve().parents[2]
        fixture_path = (
            fixture_root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_repair_operator_queue_report.json"
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paths["upbit_paper_repair_operator_queue_report"].parent.mkdir(parents=True, exist_ok=True)
            paths["upbit_paper_repair_operator_queue_report"].write_text(
                fixture_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]

            self.assertEqual(reconciliation["status"], "BLOCKED")
            self.assertEqual(reconciliation["severity"], "ERROR")
            self.assertEqual(reconciliation["color_token"], "red")
            self.assertEqual(reconciliation["source"], "upbit_paper_repair_operator_queue_report.json")
            self.assertEqual(
                reconciliation["primary_blocker_code"],
                "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
            )
            self.assertEqual(reconciliation["repair_operator_queue_status"], "BLOCKED")
            self.assertEqual(reconciliation["repair_operator_queue_validation_status"], "PASS")
            self.assertEqual(reconciliation["repair_operator_queue_item_count"], 6)
            self.assertEqual(reconciliation["repair_operator_queue_ledger_candidate_review_ready_count"], 1)
            self.assertEqual(reconciliation["repair_operator_queue_runtime_cycle_rerun_required_count"], 5)
            self.assertEqual(reconciliation["repair_operator_queue_candidate_current_evidence_usable_count"], 0)
            self.assertEqual(dashboard_shell["operator_action_summary"]["status"], "BLOCKED")
            self.assertFalse(dashboard_shell["operator_action_summary"]["safe_to_continue_paper"])
            self.assertFalse(dashboard_shell["live_order_allowed"])
            self.assertFalse(dashboard_shell["scale_up_allowed"])

    def test_launcher_dashboard_loads_stale_loop_post_regeneration_reconciliation_as_red_blocker(self):
        report = build_launcher_report("UPBIT_PAPER")
        fixture_root = Path(__file__).resolve().parents[2]
        fixture_path = (
            fixture_root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json"
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paths["upbit_paper_stale_loop_post_regeneration_reconciliation_report"].parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            paths["upbit_paper_stale_loop_post_regeneration_reconciliation_report"].write_text(
                fixture_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]

            self.assertEqual(reconciliation["status"], "BLOCKED")
            self.assertEqual(reconciliation["severity"], "ERROR")
            self.assertEqual(reconciliation["color_token"], "red")
            self.assertEqual(
                reconciliation["source"],
                "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json",
            )
            self.assertEqual(
                reconciliation["primary_blocker_code"],
                "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
            )
            self.assertEqual(reconciliation["stale_loop_post_regeneration_reconciliation_status"], "BLOCKED")
            self.assertEqual(reconciliation["stale_loop_post_regeneration_reconciliation_validation_status"], "PASS")
            self.assertEqual(reconciliation["stale_loop_post_regeneration_accepted_count"], 10)
            self.assertEqual(reconciliation["stale_loop_post_regeneration_blocked_reconciliation_count"], 6)
            self.assertEqual(reconciliation["stale_loop_post_regeneration_current_evidence_usable_count"], 10)
            self.assertIn(
                "Reconcile BLOCKED regenerated replacements",
                reconciliation["next_operator_action"],
            )
            self.assertEqual(dashboard_shell["operator_action_summary"]["status"], "BLOCKED")
            self.assertFalse(dashboard_shell["operator_action_summary"]["safe_to_continue_paper"])
            self.assertFalse(dashboard_shell["live_order_allowed"])
            self.assertFalse(dashboard_shell["scale_up_allowed"])

    def test_launcher_dashboard_loads_stale_loop_operator_queue_closure_as_red_blocker(self):
        report = build_launcher_report("UPBIT_PAPER")
        fixture_root = Path(__file__).resolve().parents[2]
        fixture_path = (
            fixture_root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json"
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paths["upbit_paper_stale_loop_reconciliation_operator_queue_closure_report"].parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            paths["upbit_paper_stale_loop_reconciliation_operator_queue_closure_report"].write_text(
                fixture_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]
            source_files = {source["filename"] for source in dashboard_shell["source_artifacts"]}

            self.assertEqual(reconciliation["status"], "BLOCKED")
            self.assertEqual(reconciliation["severity"], "ERROR")
            self.assertEqual(reconciliation["color_token"], "red")
            self.assertEqual(
                reconciliation["source"],
                "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json",
            )
            self.assertEqual(
                reconciliation["primary_blocker_code"],
                "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING",
            )
            self.assertEqual(reconciliation["stale_loop_operator_queue_closure_status"], "BLOCKED")
            self.assertEqual(reconciliation["stale_loop_operator_queue_closure_validation_status"], "PASS")
            self.assertEqual(reconciliation["stale_loop_operator_queue_closure_item_count"], 6)
            self.assertEqual(reconciliation["stale_loop_operator_queue_closure_source_blocked_item_count"], 6)
            self.assertEqual(reconciliation["stale_loop_operator_queue_closure_ledger_recheck_ready_count"], 5)
            self.assertEqual(reconciliation["stale_loop_operator_queue_closure_recovery_guard_required_count"], 1)
            self.assertEqual(reconciliation["stale_loop_operator_queue_closure_current_evidence_write_allowed_count"], 0)
            self.assertEqual(
                reconciliation["stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count"],
                0,
            )
            self.assertIn(
                "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING",
                reconciliation["stale_loop_operator_queue_closure_blocker_codes"],
            )
            self.assertIn(
                "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json",
                source_files,
            )
            self.assertEqual(dashboard_shell["operator_action_summary"]["status"], "BLOCKED")
            self.assertFalse(dashboard_shell["operator_action_summary"]["safe_to_continue_paper"])
            self.assertFalse(dashboard_shell["live_order_allowed"])
            self.assertFalse(dashboard_shell["scale_up_allowed"])

    def test_launcher_dashboard_surfaces_cross_session_reconciliation_as_invalid(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paths["reconciliation_report"].parent.mkdir(parents=True, exist_ok=True)
            reconciliation_report = build_reconciliation_report(
                reconciliation_id="test-launcher-reconciliation-cross-session",
                exchange=report["exchange"],
                market_type=report["market_type"],
                mode=report["mode"],
                session_id="different_session",
            )
            restart_report = build_restart_recovery_report(
                restart_id="test-launcher-restart-cross-session",
                exchange=report["exchange"],
                market_type=report["market_type"],
                mode=report["mode"],
                session_id="different_session",
            )
            paths["reconciliation_report"].write_text(json.dumps(reconciliation_report, indent=2), encoding="utf-8")
            paths["restart_recovery_report"].write_text(json.dumps(restart_report, indent=2), encoding="utf-8")

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]
            self.assertEqual(reconciliation["status"], "INVALID")
            self.assertEqual(reconciliation["severity"], "ERROR")
            self.assertEqual(reconciliation["color_token"], "red")
            self.assertEqual(reconciliation["primary_blocker_code"], "SNAPSHOT_SCOPE_MISMATCH")
            self.assertFalse(reconciliation["live_order_allowed"])

    def test_launcher_dashboard_uses_restart_report_from_scoped_paper_operation_gate(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = launcher_dashboard_paths(report, root)
            paths["paper_operation_gate_report"].parent.mkdir(parents=True, exist_ok=True)
            gate = build_upbit_operational_paper_cycle(
                operation_gate_id="test-launcher-restart-from-gate",
                session_id=report["session_id"],
            )
            reconciliation_report = build_reconciliation_report(
                reconciliation_id="test-launcher-reconciliation-with-gate-restart",
                exchange=report["exchange"],
                market_type=report["market_type"],
                mode=report["mode"],
                session_id=report["session_id"],
            )
            paths["paper_operation_gate_report"].write_text(json.dumps(gate, indent=2), encoding="utf-8")
            paths["reconciliation_report"].write_text(json.dumps(reconciliation_report, indent=2), encoding="utf-8")

            dashboard_paths = write_launcher_dashboard(report, root)
            dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
            reconciliation = dashboard_shell["reconciliation_recovery_summary"]
            self.assertEqual(reconciliation["status"], "PASS")
            self.assertEqual(reconciliation["restart_recovery_status"], "PASS")
            self.assertEqual(reconciliation["single_writer_state"], "RECOVERED")
            self.assertFalse(reconciliation["live_order_allowed"])

    def test_runtime_write_lock_blocks_concurrent_same_session_writer(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            runtime_dir = launcher_dashboard_paths(report, Path(tmp))["summary"].parent
            with runtime_write_lock(runtime_dir, timeout_seconds=0.1):
                with self.assertRaises(RuntimeError):
                    with runtime_write_lock(runtime_dir, timeout_seconds=0.01):
                        pass
            self.assertFalse((runtime_dir / ".runtime_write.lock").exists())

    def test_runtime_write_lock_does_not_break_stale_lock_owned_by_live_process(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            runtime_dir = launcher_dashboard_paths(report, Path(tmp))["summary"].parent
            runtime_dir.mkdir(parents=True, exist_ok=True)
            lock_path = runtime_dir / ".runtime_write.lock"
            lock_path.write_text(f"{os.getpid()}:manual\nacquired_at_utc=2000-01-01T00:00:00Z\n", encoding="utf-8")
            old_time = time.time() - 120
            os.utime(lock_path, (old_time, old_time))

            with self.assertRaises(RuntimeError):
                with runtime_write_lock(runtime_dir, timeout_seconds=0.01, stale_seconds=0.0):
                    pass
            self.assertTrue(lock_path.exists())

    def test_runtime_write_lock_recovers_stale_lock_from_dead_owner(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            runtime_dir = launcher_dashboard_paths(report, Path(tmp))["summary"].parent
            runtime_dir.mkdir(parents=True, exist_ok=True)
            lock_path = runtime_dir / ".runtime_write.lock"
            lock_path.write_text("999999999:manual\nacquired_at_utc=2000-01-01T00:00:00Z\n", encoding="utf-8")
            old_time = time.time() - 120
            os.utime(lock_path, (old_time, old_time))

            with runtime_write_lock(runtime_dir, timeout_seconds=0.1, stale_seconds=0.0):
                self.assertTrue(lock_path.exists())
            self.assertFalse(lock_path.exists())

    def test_console_heartbeat_line_is_operator_visible_and_live_blocked(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            dashboard_paths = write_launcher_dashboard(report, Path(tmp))
            heartbeat = load_json(dashboard_paths["heartbeat"])
            line = console_heartbeat_line(report, heartbeat, 1, 3)
            self.assertIn("HEARTBEAT 1/3 PASS", line)
            self.assertIn("program_status=RUNNING_SAFE_MODE", line)
            self.assertIn("scope=UPBIT/KRW_SPOT/PAPER", line)
            self.assertIn("heartbeat_at=", line)
            self.assertIn("heartbeat_age=", line)
            self.assertIn("stale_after=", line)
            self.assertIn("recovery=none", line)
            self.assertIn("launcher_mode=SAFE_BOOT_OR_EXPLICIT_MONITOR", line)
            self.assertIn("runtime_presence=DASHBOARD_HEARTBEAT_ONLY", line)
            self.assertIn("final_action=NO_TRADE", line)
            self.assertIn("live_order_allowed=false", line)
            self.assertIn("can_live_trade=false", line)
            self.assertIn("scale_up_allowed=false", line)
            self.assertIn("order_adapter_submit_attempted=false", line)

    def test_console_safe_monitor_banner_prevents_exit_confusion(self):
        report = build_launcher_report("UPBIT_PAPER")
        banner = console_safe_monitor_banner(report, 10.0)
        self.assertIn("SAFE_MONITOR running", banner)
        self.assertIn("until Ctrl+C", banner)
        self.assertIn("final_action=NO_TRADE", banner)
        self.assertIn("live_order_allowed=false", banner)
        self.assertIn("scale_up_allowed=false", banner)

    def test_console_heartbeat_line_can_show_continuous_monitor(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            dashboard_paths = write_launcher_dashboard(report, Path(tmp))
            heartbeat = load_json(dashboard_paths["heartbeat"])
            line = console_heartbeat_line(report, heartbeat, 1, "continuous")
            self.assertIn("HEARTBEAT 1/continuous PASS", line)
            self.assertIn("program_status=RUNNING_SAFE_MODE", line)

    def test_console_heartbeat_blocks_live_mutation_display(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            dashboard_paths = write_launcher_dashboard(report, Path(tmp))
            heartbeat = load_json(dashboard_paths["heartbeat"])
            heartbeat["live_order_allowed"] = True
            line = console_heartbeat_line(report, heartbeat, 1, 1)
            self.assertIn("HEARTBEAT 1/1 BLOCKED", line)
            self.assertIn("live_order_allowed=false", line)

    def test_console_heartbeat_blocks_stale_artifact_display(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            dashboard_paths = write_launcher_dashboard(report, Path(tmp))
            heartbeat = load_json(dashboard_paths["heartbeat"])
            heartbeat["last_heartbeat_at_utc"] = "2000-01-01T00:00:00Z"
            heartbeat["generated_at_utc"] = "2000-01-01T00:00:00Z"
            line = console_heartbeat_line(report, heartbeat, 1, 1)
            self.assertIn("HEARTBEAT 1/1 BLOCKED", line)
            self.assertIn("program_status=STALE_HEARTBEAT", line)
            self.assertIn("blocker=LATENCY_TTL_EXPIRED", line)
            self.assertIn("recovery=rerun_paper_launcher_if_stale", line)
            self.assertIn("runtime_presence=HEARTBEAT_STALE_OR_SOURCE_ATTENTION_REQUIRED", line)
            self.assertIn("live_order_allowed=false", line)

    def test_emit_console_heartbeats_is_bounded_for_automation(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            dashboard_paths = write_launcher_dashboard(report, Path(tmp))
            heartbeat = load_json(dashboard_paths["heartbeat"])
            buffer = StringIO()
            lines = emit_console_heartbeats(report, heartbeat, ticks=2, interval_seconds=0.0, stream=buffer)
            self.assertEqual(len(lines), 2)
            output = buffer.getvalue()
            self.assertIn("HEARTBEAT 1/2 PASS", output)
            self.assertIn("HEARTBEAT 2/2 PASS", output)

    def test_emit_console_heartbeats_refreshes_status_between_ticks(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            dashboard_paths = write_launcher_dashboard(report, Path(tmp))
            heartbeat = load_json(dashboard_paths["heartbeat"])
            refreshed = []
            for stamp in ("2026-04-28T22:00:01Z", "2026-04-28T22:00:02Z"):
                item = dict(heartbeat)
                item["last_heartbeat_at_utc"] = stamp
                refreshed.append(item)

            def refresh():
                return refreshed.pop(0)

            buffer = StringIO()
            lines = emit_console_heartbeats(
                report,
                heartbeat,
                ticks=2,
                interval_seconds=0.0,
                stream=buffer,
                refresh_heartbeat=refresh,
            )
            self.assertIn("heartbeat_at=2026-04-28T22:00:01Z", lines[0])
            self.assertIn("heartbeat_at=2026-04-28T22:00:02Z", lines[1])

    def test_refresh_launcher_monitor_artifacts_writes_fresh_heartbeat(self):
        report = build_launcher_report("UPBIT_PAPER")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            heartbeat = refresh_launcher_monitor_artifacts(report, root)
            self.assertEqual(heartbeat["heartbeat_status"], "PASS")
            self.assertFalse(heartbeat["live_order_allowed"])
            self.assertFalse(heartbeat["can_live_trade"])
            paths = launcher_dashboard_paths(report, root)
            self.assertTrue(paths["heartbeat"].exists())
            self.assertTrue(paths["dashboard_html"].exists())

    def test_refresh_launcher_monitor_artifacts_blocks_stale_source_writer(self):
        report = build_launcher_report("UPBIT_PAPER")
        stale_report = dict(report)
        stale_report["source_tree_hash"] = "STALE_SOURCE_TREE_HASH"
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, dashboard_paths = write_launcher_runtime_bundle(report, root)
            before_dashboard = load_json(dashboard_paths["dashboard_shell"])
            heartbeat = refresh_launcher_monitor_artifacts(stale_report, root)
            after_dashboard = load_json(dashboard_paths["dashboard_shell"])
            self.assertEqual(heartbeat["heartbeat_status"], "BLOCKED")
            self.assertEqual(heartbeat["primary_blocker_code"], "SOURCE_IDENTITY_MISMATCH")
            self.assertEqual(before_dashboard["dashboard_hash"], after_dashboard["dashboard_hash"])
            self.assertFalse(heartbeat["live_order_allowed"])
            self.assertFalse(heartbeat["can_live_trade"])

    def test_launcher_dashboard_paths_are_session_scoped(self):
        report = build_launcher_report("UPBIT_PAPER")
        paths = launcher_dashboard_paths(report)
        self.assertIn(report["session_id"], paths["dashboard_html"].parts)
        self.assertEqual(paths["dashboard_html"].name, "index.html")

    def test_launcher_main_can_run_non_interactive_without_pause(self):
        self.assertFalse(should_pause_for_operator(False))
        buffer = StringIO()
        with TemporaryDirectory() as tmp, redirect_stdout(buffer):
            result = launcher_main("UPBIT_PAPER", pause=False, open_dashboard=False, root=Path(tmp))
        self.assertEqual(result, 0)
        self.assertIn("HEARTBEAT 1/1 PASS", buffer.getvalue())

    def test_launcher_main_operator_monitor_can_be_bounded_for_tests(self):
        buffer = StringIO()
        with TemporaryDirectory() as tmp, redirect_stdout(buffer):
            result = launcher_main(
                "UPBIT_PAPER",
                pause=True,
                open_dashboard=False,
                console_heartbeat_ticks=2,
                console_heartbeat_interval_seconds=0.0,
                root=Path(tmp),
            )
        output = buffer.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("HEARTBEAT 1/2 PASS", output)
        self.assertIn("HEARTBEAT 2/2 PASS", output)
        self.assertNotIn("Press Enter", output)

    def test_launcher_main_operator_pause_defaults_to_continuous_safe_monitor(self):
        buffer = StringIO()
        calls = []

        def fake_emit_console_heartbeats(report, heartbeat, *, ticks, interval_seconds, refresh_heartbeat):
            calls.append(
                {
                    "ticks": ticks,
                    "interval_seconds": interval_seconds,
                    "live_order_ready": report["live_order_ready"],
                    "live_order_allowed": report["live_order_allowed"],
                    "can_live_trade": report["can_live_trade"],
                }
            )
            return []

        self.assertIsNone(DEFAULT_INTERACTIVE_HEARTBEAT_TICKS)
        with TemporaryDirectory() as tmp, redirect_stdout(buffer), patch.object(
            safe_launcher,
            "emit_console_heartbeats",
            side_effect=fake_emit_console_heartbeats,
        ):
            result = safe_launcher.launcher_main(
                "UPBIT_PAPER",
                pause=True,
                open_dashboard=False,
                console_heartbeat_interval_seconds=0.0,
                root=Path(tmp),
            )
        output = buffer.getvalue()
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 1)
        self.assertIsNone(calls[0]["ticks"])
        self.assertEqual(calls[0]["interval_seconds"], 0.0)
        self.assertFalse(calls[0]["live_order_ready"])
        self.assertFalse(calls[0]["live_order_allowed"])
        self.assertFalse(calls[0]["can_live_trade"])
        self.assertIn("SAFE_MONITOR running", output)
        self.assertIn("until Ctrl+C", output)
        self.assertIn("live_order_allowed=false", output)
        self.assertNotIn("Press Enter", output)

    def test_root_operator_launcher_main_forces_console_hold_open(self):
        calls = []

        def fake_launcher_main(launcher_name, **kwargs):
            calls.append((launcher_name, kwargs))
            return 0

        with patch.dict(os.environ, {}, clear=True), patch.object(
            safe_launcher,
            "launcher_main",
            side_effect=fake_launcher_main,
        ):
            result = root_operator_launcher_main("UPBIT_PAPER")

        self.assertEqual(result, 0)
        self.assertEqual(calls[0][0], "UPBIT_PAPER")
        self.assertTrue(calls[0][1]["pause"])
        self.assertIsNone(calls[0][1]["console_heartbeat_ticks"])
        self.assertIsNone(calls[0][1]["console_heartbeat_interval_seconds"])

    def test_root_operator_launcher_main_can_be_bounded_for_automation(self):
        calls = []

        def fake_launcher_main(launcher_name, **kwargs):
            calls.append((launcher_name, kwargs))
            return 0

        with patch.dict(
            os.environ,
            {
                ROOT_OPERATOR_HEARTBEAT_TICKS_ENV: "2",
                ROOT_OPERATOR_HEARTBEAT_INTERVAL_ENV: "0",
            },
            clear=True,
        ), patch.object(safe_launcher, "launcher_main", side_effect=fake_launcher_main):
            result = root_operator_launcher_main("UPBIT_PAPER")

        self.assertEqual(result, 0)
        self.assertEqual(calls[0][0], "UPBIT_PAPER")
        self.assertTrue(calls[0][1]["pause"])
        self.assertEqual(calls[0][1]["console_heartbeat_ticks"], 2)
        self.assertEqual(calls[0][1]["console_heartbeat_interval_seconds"], 0.0)

    def test_source_identity_includes_root_launchers_and_contracts(self):
        relative_paths = {path.relative_to(Path(__file__).resolve().parents[2]).as_posix() for path in source_identity_files()}
        for required in (
            "UPBIT_PAPER.py",
            "UPBIT_LIVE.py",
            "BINANCE_PAPER.py",
            "BINANCE_LIVE.py",
            "TRADER_1.md",
            "AGENTS.md",
            "pyproject.toml",
            "contracts/registry.yaml",
        ):
            self.assertIn(required, relative_paths)
        self.assertNotIn("contracts/security/source_bundle_manifest.json", relative_paths)


if __name__ == "__main__":
    unittest.main()
