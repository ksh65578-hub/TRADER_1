import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trader1.runtime.paper.upbit_paper_long_runner import (
    DashboardOpenResult,
    LOCK_BLOCKER_CODE,
    RUNNER_STATUS_LOCKED,
    RUNNER_STATUS_BLOCKED,
    RUNNER_STATUS_STOPPED,
    DISK_PRESSURE_BLOCKER_CODE,
    acquire_runner_lock,
    apply_runner_artifact_retention,
    clear_runner_stop_file_for_operator_start,
    open_runner_dashboard,
    open_runner_dashboard_result,
    paper_candidate_scorecard_path,
    paper_overfit_diagnostic_path,
    paper_runtime_sample_history_path,
    paper_shadow_evidence_accumulation_path,
    release_runner_lock,
    root_upbit_paper_long_runner_main,
    run_upbit_paper_long_running_runner,
    runner_blocked_start_status_path,
    runner_dashboard_path,
    runner_lock_path,
    runner_retention_manifest_path,
    runner_start_reconciliation_path,
    runner_status_path,
    runner_stop_file_path,
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
            self.assertEqual(report["candidate_scorecard_status"], "PASS")
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
