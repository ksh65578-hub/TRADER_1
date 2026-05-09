"""Operator-facing long running UPBIT PAPER runner.

This module intentionally stays non-live.  It repeatedly executes the existing
bounded PAPER loop, writes a crash-recoverable runner status artifact, and keeps
all live/order/credential flags fail-closed.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from trader1.research.profitability.candidate_scorecard import (
    candidate_generation_report_hash,
    candidate_generation_report_from_upbit_paper_runtime_cycle,
    candidate_scorecard_from_upbit_paper_runtime_cycle,
    performance_inputs_from_runtime_sample_history,
    safe_candidate_scorecard_filename,
    validate_candidate_generation_report,
    write_upbit_paper_candidate_generation_report,
    write_upbit_paper_candidate_scorecard,
)
from trader1.research.profitability.overfit_diagnostic import (
    overfit_diagnostic_from_upbit_paper_runtime,
    robustness_inputs_from_overfit_diagnostic,
    write_overfit_diagnostic_report,
)
from trader1.research.shadow.evidence_accumulator import (
    build_paper_shadow_evidence_accumulation_from_runtime_artifacts,
)
from trader1.research.shadow.evidence_refresh_policy import choose_paper_shadow_evidence_refresh_report
from trader1.research.shadow.paper_shadow_harness_binding import (
    build_paper_shadow_harness_binding_report,
    paper_shadow_harness_binding_hash,
    validate_paper_shadow_harness_binding_report,
)
from trader1.research.shadow.shadow_runner import validate_paper_shadow_evidence_accumulation_report
from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    shadow_observation_actual_runtime_harness_hash,
    validate_shadow_observation_actual_runtime_harness_report,
)
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    shadow_observation_persistent_runtime_hash,
    validate_shadow_observation_persistent_runtime_report,
)
from trader1.research.shadow.shadow_observation_runtime_orchestration import (
    build_shadow_observation_runtime_orchestration_report,
    shadow_observation_runtime_orchestration_hash,
    validate_shadow_observation_runtime_orchestration_report,
)
from trader1.runtime.paper.candidate_generation_intent_provider import (
    default_candidate_generation_paper_intent_provider,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    LONG_RUN_EVIDENCE_BLOCKER_CODE,
    run_upbit_paper_persistent_loop,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_paper_runtime import validate_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT,
    build_upbit_paper_runtime_sample_history,
    validate_upbit_paper_runtime_sample_history_sources,
    write_upbit_paper_runtime_sample_history,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json

ROOT = Path(__file__).resolve().parents[3]

UPBIT_PAPER_LONG_RUNNER_STATUS_SCHEMA_ID = "trader1.upbit_paper_long_runner_status.v1"
UPBIT_PAPER_LONG_RUNNER_RETENTION_SCHEMA_ID = "trader1.upbit_paper_long_runner_retention_manifest.v1"
UPBIT_PAPER_RUNNER_START_RECONCILIATION_SCHEMA_ID = "trader1.upbit_paper_runner_start_reconciliation.v1"
UPBIT_PAPER_LONG_RUNNER_LOCK_SCHEMA_ID = "trader1.upbit_paper_long_runner_lock.v1"
UPBIT_PAPER_OPERATOR_STOP_SCHEMA_ID = "trader1.upbit_paper_operator_stop_request.v1"
UPBIT_PAPER_BACKGROUND_LAUNCH_SCHEMA_ID = "trader1.upbit_paper_background_launch.v1"

DEFAULT_SESSION_ID = "mvp1_upbit_paper_launcher"
BACKGROUND_LAUNCH_ENV = "TRADER1_UPBIT_PAPER_BACKGROUND_LAUNCH"
FOREGROUND_RUNNER_ENV = "TRADER1_UPBIT_PAPER_FOREGROUND_RUNNER"
DEFAULT_CYCLE_INTERVAL_SECONDS = 30.0
DEFAULT_LOCK_STALE_AFTER_SECONDS = 15 * 60
DEFAULT_RETENTION_MAX_ACTIVE_ARTIFACTS_PER_GROUP = 500
DEFAULT_CANDIDATE_DISCOVERY_SYMBOL_LIMIT = 12
DEFAULT_CANDIDATE_DISCOVERY_TIMEOUT_SECONDS = 3.0
DEFAULT_ALTERNATIVE_REPLAY_TARGET_COUNT = 420
DEFAULT_ALTERNATIVE_REPLAY_PAGE_SIZE = 200
DEFAULT_ALTERNATIVE_REPLAY_TIMEOUT_SECONDS = 3.0
DEFAULT_ALTERNATIVE_REPLAY_MAX_WINDOWS = 420
DEFAULT_ALTERNATIVE_REPLAY_MIN_REQUIRED_SAMPLE_COUNT = 300
DEFAULT_ALTERNATIVE_REPLAY_CANDIDATE_LIMIT = 5
DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_MIN_TARGET_COUNT = 2400
DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_MAX_TARGET_COUNT = 6000
DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_TIMEOUT_SECONDS = 10.0
DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_MAX_WINDOWS = 6000
DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_CANDIDATE_LIMIT = 1
DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_ROTATION_LIMIT = 3
DEFAULT_RETENTION_MAX_ACTIVE_ARTIFACTS_BY_GROUP = {
    "paper_runtime_cycles": 240,
    "persistent_loop_reports": 120,
    "recovery_guard_reports": 120,
    "ledger_rollups": 120,
    "public_raw_candles": 40,
    "public_canonical_events": 40,
    "public_collection_reports": 80,
}
DEFAULT_RETENTION_MAX_UNCOMPACTED_ARCHIVE_BATCHES = 3
DEFAULT_RUNNER_LOG_MAX_BYTES = 2_000_000
DEFAULT_RUNTIME_DISK_PRESSURE_MAX_BYTES = 5_000_000_000

RUNNER_STATUS_RUNNING = "RUNNING"
RUNNER_STATUS_STOPPING = "STOPPING"
RUNNER_STATUS_STOPPED = "STOPPED"
RUNNER_STATUS_BLOCKED = "BLOCKED"
RUNNER_STATUS_LOCKED = "LOCKED"
STOP_REQUEST_SUPERSEDED_BY_START = "SUPERSEDED_BY_OPERATOR_START"

RUNNER_STATUS_SET = {
    RUNNER_STATUS_RUNNING,
    RUNNER_STATUS_STOPPING,
    RUNNER_STATUS_STOPPED,
    RUNNER_STATUS_BLOCKED,
    RUNNER_STATUS_LOCKED,
}

LOCK_BLOCKER_CODE = "RUNTIME_SINGLE_WRITER_LOCK_ACTIVE"
STOP_FILE_METHOD = "STOP_UPBIT_PAPER.py_OR_STOP_FILE_OR_CTRL_C"
DISK_PRESSURE_BLOCKER_CODE = "RUNTIME_DISK_PRESSURE_GUARD"
RETENTION_ARCHIVE_WRITE_METHOD = "SAME_FILESYSTEM_RENAME"
PAPER_SHADOW_RUNTIME_REFRESH_FAILED_BLOCKER_CODE = "PAPER_SHADOW_RUNTIME_REFRESH_FAILED"
PAPER_SHADOW_RUNTIME_REFRESH_EXECUTED = "SHORT_WINDOW_EXECUTED"
PAPER_SHADOW_RUNTIME_REFRESH_NOT_RUN = "NOT_RUN"
PAPER_SHADOW_RUNTIME_REFRESH_BLOCKED = "BLOCKED"
NON_LIVE_PROFITABILITY_REFRESH_FAILED_BLOCKER_CODE = "NON_LIVE_PROFITABILITY_EVIDENCE_REFRESH_FAILED"
NON_LIVE_PROFITABILITY_REFRESH_NOT_RUN = "NOT_RUN"
NON_LIVE_PROFITABILITY_REFRESH_PASS = "PASS"
NON_LIVE_PROFITABILITY_REFRESH_COLLECTING = "COLLECTING"
NON_LIVE_PROFITABILITY_REFRESH_BLOCKED = "BLOCKED"
NON_LIVE_PROFITABILITY_REFRESH_CRITICAL_BLOCKERS = {
    "LIVE_FINAL_GUARD_FAILED",
    "SNAPSHOT_SCOPE_MISMATCH",
    "SCHEMA_IDENTITY_MISMATCH",
    "SOURCE_IDENTITY_MISMATCH",
    "API_UNVERIFIED",
    "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
}
NON_LIVE_PROFITABILITY_REFRESH_COLLECTION_BLOCKERS = {
    "ACTUAL_PAPER_RUNTIME_SAMPLE_MISSING",
    "NON_LIVE_PROFITABILITY_EVIDENCE_INCOMPLETE",
    "PAPER_SAMPLE_DEFICIT",
    "PAPER_SHADOW_EVIDENCE_MISSING",
    "PAPER_SHADOW_RUNTIME_ARTIFACT_MISSING",
    "PRELIMINARY_SAMPLE_INSUFFICIENT",
    "SAMPLE_INSUFFICIENT",
}
DASHBOARD_FILE_MISSING_BLOCKER_CODE = "DASHBOARD_FILE_MISSING"
DASHBOARD_OPEN_FAILED_BLOCKER_CODE = "DASHBOARD_OPEN_FAILED"
DASHBOARD_PREOPEN_REFRESH_FAILED_BLOCKER_CODE = "DASHBOARD_PREOPEN_REFRESH_FAILED"
DASHBOARD_STATUS_CHANNEL_HOST = "127.0.0.1"
DASHBOARD_STATUS_CHANNEL_MODE = "LOCAL_READ_ONLY_HTTP_SSE"
DASHBOARD_STATUS_CHANNEL_SCHEMA_ID = "trader1.dashboard_status_channel.v1"
DASHBOARD_STATUS_CHANNEL_PAYLOAD_SCHEMA_ID = "trader1.dashboard_status_channel_payload.v1"
DEFAULT_DASHBOARD_STATUS_CHANNEL_SHUTDOWN_GRACE_SECONDS = 1.0
DEFAULT_DASHBOARD_STATUS_CHANNEL_STOP_POLL_SECONDS = 0.25

LIVE_FALSE_FLAGS = (
    "live_order_ready",
    "live_order_allowed",
    "can_live_trade",
    "scale_up_allowed",
    "order_adapter_called",
    "private_endpoint_called",
    "credential_load_attempted",
    "live_key_loaded",
)
PAPER_SCOPE_FOCUS_DRIFT_FLAGS = (*LIVE_FALSE_FLAGS, "order_endpoint_called")
DASHBOARD_REFRESH_NONBLOCKING_WRITER_MARKERS = (
    "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED",
    "BLOCKED_PAPER_CURRENT_TRUTH_UNAVAILABLE",
    "audited current-evidence writer",
    "audited PAPER current-evidence writer",
    "portfolio values remain UNVERIFIED",
    "paper runner operations attempted live or scale permission",
)
RUNTIME_DRIFT_TRUE_FIELDS = (
    *LIVE_FALSE_FLAGS,
    "order_endpoint_called",
    "can_submit_order",
)


@dataclass(frozen=True)
class DashboardOpenResult:
    attempted: bool
    opened: bool
    method: str
    target: str
    path: str
    blocker_code: str | None = None
    blocker_message: str | None = None


@dataclass
class DashboardStatusChannelHandle:
    server: ThreadingHTTPServer
    thread: threading.Thread
    url: str
    report_path: Path
    stop_watcher: threading.Thread | None = None


class _QuietDashboardStatusChannelServer(ThreadingHTTPServer):
    def handle_error(self, request: Any, client_address: Any) -> None:
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError)):
            return
        super().handle_error(request, client_address)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def runner_runtime_base(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def runner_dir(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_runtime_base(root, session_id) / "paper_runtime" / "runner"


def runner_status_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "runner_status.json"


def runner_dashboard_status_channel_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "dashboard_status_channel.json"


def runner_blocked_start_status_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "runner_status.blocked_start.json"


def runner_stop_file_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "STOP_UPBIT_PAPER.signal"


def runner_stop_request_report_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "operator_stop_request.json"


def runner_background_launch_report_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "background_launch_report.json"


def runner_background_console_log_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "background_runner_console.log"


def runner_start_reconciliation_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "runner_start_reconciliation.json"


def runner_lock_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "session.lock"


def runner_log_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "runner_events.jsonl"


def runner_retention_manifest_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_dir(root, session_id) / "runner_retention_manifest.json"


def _json_hash(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def upbit_paper_long_runner_status_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("status_hash", None)
    return _json_hash(payload)


def upbit_paper_operator_stop_request_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("stop_request_hash", None)
    return _json_hash(payload)


def _root_stop_request_report_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_runtime_base(root, session_id) / "launcher" / "root_stop_request_report.json"


def _root_stop_request_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("stop_request_hash", None)
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest().upper()


def _confirm_operator_stop_reports_from_final_status(
    root: Path,
    session_id: str,
    final_status: dict[str, Any],
) -> None:
    if final_status.get("runner_status") != RUNNER_STATUS_STOPPED or final_status.get("stop_reason") != "STOP_FILE":
        return
    generated_at = utc_now()
    runner_report_path = runner_stop_request_report_path(root, session_id)
    runner_report = _read_json(runner_report_path)
    if isinstance(runner_report, dict) and runner_report.get("stop_request_status") == "STOP_REQUESTED":
        updated_runner_report = dict(runner_report)
        updated_runner_report.update(
            {
                "updated_at_utc": generated_at,
                "stop_request_status": "STOP_CONFIRMED",
                "stop_confirmed": True,
                "runner_status_after": RUNNER_STATUS_STOPPED,
                "runner_running_after": False,
                "primary_blocker_code": None,
                "primary_blocker_message": None,
            }
        )
        for flag in LIVE_FALSE_FLAGS:
            updated_runner_report[flag] = False
        updated_runner_report["order_endpoint_called"] = False
        updated_runner_report["stop_request_hash"] = upbit_paper_operator_stop_request_hash(updated_runner_report)
        durable_atomic_write_json(runner_report_path, updated_runner_report)

    root_report_path = _root_stop_request_report_path(root, session_id)
    root_report = _read_json(root_report_path)
    if not isinstance(root_report, dict):
        return
    scope_matches = (
        root_report.get("target_launcher_name") == "UPBIT_PAPER"
        and root_report.get("exchange") == "UPBIT"
        and root_report.get("market_type") == "KRW_SPOT"
        and root_report.get("mode") == "PAPER"
        and root_report.get("session_id") == session_id
    )
    if not scope_matches or root_report.get("stop_request_status") != "STOP_REQUESTED":
        return
    updated_root_report = dict(root_report)
    updated_root_report.update(
        {
            "updated_at_utc": generated_at,
            "stop_request_status": "STOP_CONFIRMED",
            "stop_confirmed": True,
            "stop_result_summary": "UPBIT PAPER runner stopped by operator stop launcher.",
            "runner_status_after": RUNNER_STATUS_STOPPED,
            "runner_running_after": False,
            "dashboard_refresh_requested": True,
            "dashboard_refresh_status": "PASS",
            "dashboard_refresh_deferred": False,
            "dashboard_should_show_stopped": True,
            "primary_blocker_code": None,
            "primary_blocker_message": None,
        }
    )
    for flag in LIVE_FALSE_FLAGS:
        updated_root_report[flag] = False
    updated_root_report["order_endpoint_called"] = False
    updated_root_report["stop_request_hash"] = _root_stop_request_report_hash(updated_root_report)
    durable_atomic_write_json(root_report_path, updated_root_report)


def upbit_paper_background_launch_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("background_launch_hash", None)
    return _json_hash(payload)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _safe_local_dashboard_url(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme != "http":
        return None
    if parsed.hostname not in {DASHBOARD_STATUS_CHANNEL_HOST, "localhost"}:
        return None
    if parsed.port is None or parsed.port <= 0:
        return None
    path = parsed.path or "/"
    if path not in {"/", "/index.html"}:
        return None
    return value.strip()


def _dashboard_status_channel_report(root: Path, session_id: str = DEFAULT_SESSION_ID) -> dict[str, Any] | None:
    report = _read_json(runner_dashboard_status_channel_path(root, session_id))
    if not isinstance(report, dict):
        return None
    if (report.get("exchange"), report.get("market_type"), report.get("mode")) != ("UPBIT", "KRW_SPOT", "PAPER"):
        return None
    if report.get("session_id") != session_id:
        return None
    return report


def _runner_status_matches_expected_pid(status: dict[str, Any], expected_runner_pid: int | None) -> bool:
    if expected_runner_pid is None:
        return True
    runner_lock_pid = status.get("runner_lock_pid")
    if isinstance(runner_lock_pid, int) and runner_lock_pid == expected_runner_pid:
        return True
    runner_id = str(status.get("runner_id") or "")
    return runner_id.endswith(f"-{expected_runner_pid}")


def _dashboard_status_channel_matches_expected_pid(
    channel: dict[str, Any],
    expected_runner_pid: int | None,
) -> bool:
    if expected_runner_pid is None:
        return True
    return _int_value(channel.get("dashboard_status_channel_runner_pid"), -1) == expected_runner_pid


def _dashboard_status_channel_fields(root: Path, session_id: str = DEFAULT_SESSION_ID) -> dict[str, Any]:
    channel = _dashboard_status_channel_report(root, session_id)
    if not isinstance(channel, dict):
        return {
            "dashboard_status_channel_enabled": False,
            "dashboard_status_channel_status": "NOT_STARTED",
            "dashboard_status_channel_mode": DASHBOARD_STATUS_CHANNEL_MODE,
            "dashboard_status_channel_url": None,
            "dashboard_status_channel_source": "runner_status.json",
            "dashboard_status_channel_path": str(runner_dashboard_status_channel_path(root, session_id)),
            "dashboard_status_channel_live_order_ready": False,
            "dashboard_status_channel_live_order_allowed": False,
            "dashboard_status_channel_can_live_trade": False,
            "dashboard_status_channel_scale_up_allowed": False,
        }
    return {
        "dashboard_status_channel_enabled": channel.get("dashboard_status_channel_status") == "RUNNING",
        "dashboard_status_channel_status": str(channel.get("dashboard_status_channel_status") or "NOT_STARTED"),
        "dashboard_status_channel_mode": str(channel.get("dashboard_status_channel_mode") or DASHBOARD_STATUS_CHANNEL_MODE),
        "dashboard_status_channel_url": _safe_local_dashboard_url(channel.get("dashboard_status_channel_url")),
        "dashboard_status_channel_source": "runner_status.json",
        "dashboard_status_channel_path": str(runner_dashboard_status_channel_path(root, session_id)),
        "dashboard_status_channel_live_order_ready": False,
        "dashboard_status_channel_live_order_allowed": False,
        "dashboard_status_channel_can_live_trade": False,
        "dashboard_status_channel_scale_up_allowed": False,
    }


def _dashboard_status_channel_url_from_artifacts(
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
    *,
    expected_runner_pid: int | None = None,
) -> str | None:
    status = _read_json(runner_status_path(root, session_id))
    if isinstance(status, dict):
        url = _safe_local_dashboard_url(status.get("dashboard_status_channel_url"))
        if (
            url
            and status.get("dashboard_status_channel_enabled") is True
            and status.get("runner_status") == RUNNER_STATUS_RUNNING
            and status.get("running") is True
            and _runner_status_matches_expected_pid(status, expected_runner_pid)
        ):
            return url
    channel = _dashboard_status_channel_report(root, session_id)
    if isinstance(channel, dict):
        url = _safe_local_dashboard_url(channel.get("dashboard_status_channel_url"))
        if (
            url
            and channel.get("dashboard_status_channel_status") == "RUNNING"
            and _dashboard_status_channel_matches_expected_pid(channel, expected_runner_pid)
        ):
            return url
    return None


def _local_dashboard_url_is_reachable(url: str, *, timeout: float = 0.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout):
            return True
    except Exception:
        return False


def _json_has_runtime_permission_drift(value: Any) -> tuple[bool, str | None]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in RUNTIME_DRIFT_TRUE_FIELDS and child is True:
                return True, key
            detected, field = _json_has_runtime_permission_drift(child)
            if detected:
                return True, field
    elif isinstance(value, list):
        for child in value:
            detected, field = _json_has_runtime_permission_drift(child)
            if detected:
                return True, field
    return False, None


def _runtime_current_artifacts_have_permission_drift(root: Path, session_id: str) -> tuple[bool, str | None, str | None]:
    runtime_base = runner_runtime_base(root, session_id)
    if not runtime_base.exists():
        return False, None, None
    current_json_paths = [
        runner_status_path(root, session_id),
        runner_retention_manifest_path(root, session_id),
        runtime_base / "dashboard_shell.json",
        runtime_base / "paper_runtime" / "paper_runtime_truth_state_report.json",
        runtime_base / "paper_runtime" / "upbit_paper_persistent_loop_report.json",
        runtime_base / "paper_runtime" / "upbit_paper_repaired_current_evidence_audited_writer_report.json",
        runtime_base / "paper_runtime" / "current_evidence" / "audited_current_evidence_snapshot.json",
        runtime_base / "paper_runtime" / "current_evidence" / "audited_current_evidence_idempotency_manifest.json",
        runtime_base / "paper_runtime" / "current_evidence" / "paper_current_truth_refresh_report.json",
        runtime_base / "paper_runtime" / "current_evidence" / "paper_continuous_current_evidence_writer_report.json",
        runtime_base / "paper_runtime" / "portfolio" / "paper_portfolio_snapshot.json",
    ]
    for path in current_json_paths:
        payload = _read_json(path)
        if payload is None:
            continue
        detected, field = _json_has_runtime_permission_drift(payload)
        if detected:
            return True, field, str(path)
    return False, None, None


def _dashboard_refresh_error_is_nonblocking_writer_unavailable(
    error: BaseException,
    *,
    root: Path,
    session_id: str,
) -> bool:
    message = str(error)
    if not any(marker in message for marker in DASHBOARD_REFRESH_NONBLOCKING_WRITER_MARKERS):
        return False
    drifted, _, _ = _runtime_current_artifacts_have_permission_drift(root, session_id)
    return not drifted


def _runner_status_source_age_seconds(status: dict[str, Any], source_path: Path) -> int | None:
    generated_at = _parse_utc(status.get("generated_at_utc"))
    now = datetime.now(timezone.utc)
    if generated_at is not None:
        return int(max(0.0, (now - generated_at.astimezone(timezone.utc)).total_seconds()))
    try:
        return int(max(0.0, now.timestamp() - source_path.stat().st_mtime))
    except OSError:
        return None


def _dashboard_next_cycle_channel_fields(status: dict[str, Any], *, running: bool) -> dict[str, Any]:
    raw_next_eta = status.get("next_cycle_eta")
    now = datetime.now(timezone.utc)
    parsed_next_eta = _parse_utc(raw_next_eta)
    interval_seconds = _float_value(status.get("cycle_interval_seconds"), 0.0)
    if not running:
        return {
            "next_cycle_eta": raw_next_eta,
            "next_cycle_eta_display": raw_next_eta or "not scheduled",
            "next_cycle_eta_status": "NOT_RUNNING",
            "seconds_until_next_cycle": None,
            "cycle_in_progress": False,
        }
    if parsed_next_eta is None:
        return {
            "next_cycle_eta": raw_next_eta,
            "next_cycle_eta_display": "current cycle running",
            "next_cycle_eta_status": "CURRENT_CYCLE_RUNNING",
            "seconds_until_next_cycle": None,
            "cycle_in_progress": True,
        }
    seconds_until_next = int((parsed_next_eta.astimezone(timezone.utc) - now).total_seconds())
    if seconds_until_next < 0:
        return {
            "next_cycle_eta": raw_next_eta,
            "next_cycle_eta_display": "current cycle running; next ETA updates after cycle completes",
            "next_cycle_eta_status": "CURRENT_CYCLE_RUNNING",
            "seconds_until_next_cycle": None,
            "cycle_in_progress": True,
            "next_cycle_eta_overdue_seconds": abs(seconds_until_next),
        }
    return {
        "next_cycle_eta": raw_next_eta,
        "next_cycle_eta_display": raw_next_eta,
        "next_cycle_eta_status": "SCHEDULED" if interval_seconds > 0 else "NO_INTERVAL",
        "seconds_until_next_cycle": seconds_until_next,
        "cycle_in_progress": False,
    }


def _dashboard_status_channel_payload(root: Path, session_id: str = DEFAULT_SESSION_ID) -> dict[str, Any]:
    source_path = runner_status_path(root, session_id)
    stop_path = runner_stop_file_path(root, session_id)
    status = _read_json(source_path)
    status = status if isinstance(status, dict) else {}
    channel_report = _dashboard_status_channel_report(root, session_id)
    channel_report = channel_report if isinstance(channel_report, dict) else {}
    drift_fields = [
        field
        for field in (*LIVE_FALSE_FLAGS, "order_endpoint_called", "can_submit_order")
        if status.get(field) is True
    ]
    drift_fields.extend(
        f"dashboard_status_channel.{field}"
        for field in LIVE_FALSE_FLAGS
        if channel_report.get(field) is True or channel_report.get(f"dashboard_status_channel_{field}") is True
    )
    stop_requested = stop_path.exists()
    source_age_seconds = _runner_status_source_age_seconds(status, source_path)
    raw_runner_status = str(status.get("runner_status") or "NOT_LOADED")
    raw_running = status.get("running") is True and raw_runner_status == RUNNER_STATUS_RUNNING
    stop_confirmed = raw_runner_status == RUNNER_STATUS_STOPPED
    stop_signal_active = stop_requested and not stop_confirmed
    channel_running = (
        channel_report.get("dashboard_status_channel_status") == RUNNER_STATUS_RUNNING
        and _safe_local_dashboard_url(channel_report.get("dashboard_status_channel_url")) is not None
        and not any(channel_report.get(field) is True for field in LIVE_FALSE_FLAGS)
    )
    channel_runner_pid = _int_value(channel_report.get("dashboard_status_channel_runner_pid"), -1)
    source_belongs_to_running_channel = _runner_status_matches_expected_pid(
        status,
        channel_runner_pid if channel_runner_pid > 0 else None,
    )
    source_is_previous_runner_stop = (
        raw_runner_status == RUNNER_STATUS_STOPPED
        and str(status.get("runner_id") or "").startswith("upbit-paper-runner-")
        and channel_runner_pid > 0
        and not source_belongs_to_running_channel
    )
    status_file_pending = (
        channel_running
        and not raw_running
        and not stop_signal_active
        and (raw_runner_status == "NOT_LOADED" or source_is_previous_runner_stop)
    )
    running = (raw_running or status_file_pending) and not stop_signal_active
    effective_runner_status = RUNNER_STATUS_STOPPING if stop_signal_active else raw_runner_status
    if status_file_pending:
        effective_runner_status = RUNNER_STATUS_RUNNING
    if stop_signal_active:
        channel_status = "STOPPING"
    elif running:
        channel_status = "RUNNING"
    else:
        channel_status = raw_runner_status
    next_cycle_fields = _dashboard_next_cycle_channel_fields(status, running=running)
    if status_file_pending:
        next_cycle_fields.update(
            {
                "next_cycle_eta_display": "runner starting; first cycle status will appear shortly",
                "next_cycle_eta_status": "RUNNER_STARTING_STATUS_FILE_PENDING",
                "cycle_in_progress": True,
                "seconds_until_next_cycle": None,
            }
        )
    payload = {
        "schema_id": DASHBOARD_STATUS_CHANNEL_PAYLOAD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "channel_status": channel_status,
        "channel_mode": DASHBOARD_STATUS_CHANNEL_MODE,
        "status_channel_heartbeat_status": "FRESH",
        "status_channel_primary_truth": True,
        "file_freshness_is_fallback": True,
        "source": "runner_status.json",
        "source_path": str(source_path),
        "runner_status_source_generated_at_utc": status.get("generated_at_utc"),
        "runner_status_source_age_seconds": source_age_seconds,
        "runner_status_source_status": raw_runner_status,
        "runner_status_channel_transition_status": (
            "RUNNER_STARTING_STATUS_FILE_PENDING" if status_file_pending else "SOURCE_STATUS_CURRENT"
        ),
        "runner_status": effective_runner_status,
        "running": running,
        "completed_cycle_count": _int_value(status.get("completed_cycle_count"), 0),
        "failed_cycle_count": _int_value(status.get("failed_cycle_count"), 0),
        "current_symbol": status.get("current_symbol"),
        "current_position_count": _int_value(status.get("current_position_count"), 0),
        "last_decision": status.get("last_decision"),
        "last_cycle_time": status.get("last_cycle_time"),
        **next_cycle_fields,
        "stop_reason": status.get("stop_reason"),
        "primary_blocker_code": status.get("primary_blocker_code"),
        "primary_blocker_message": status.get("primary_blocker_message"),
        "cash": status.get("cash"),
        "equity": status.get("equity"),
        "realized_pnl": status.get("realized_pnl"),
        "unrealized_pnl": status.get("unrealized_pnl"),
        "runtime_sample_count": _int_value(status.get("runtime_sample_count"), 0),
        "paper_scope_candidate_id": status.get("paper_scope_candidate_id"),
        "paper_scope_sample_count": _int_value(status.get("paper_scope_sample_count"), 0),
        "paper_scope_min_required_sample_count": _int_value(
            status.get("paper_scope_min_required_sample_count"),
            DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT,
        ),
        "paper_scope_sample_deficit": _int_value(status.get("paper_scope_sample_deficit"), 0),
        "stop_launcher_path": str(root / "STOP_UPBIT_PAPER.py"),
        "stop_file_path": str(stop_path),
        "stop_requested": stop_requested,
        "stop_confirmed": stop_confirmed,
        "stop_signal_active": stop_signal_active,
        "dashboard_shutdown_expected": stop_requested and not running,
        "live_flag_drift_detected": bool(drift_fields),
        "live_flag_drift_fields": drift_fields,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "private_endpoint_called": False,
        "credential_load_attempted": False,
        "live_key_loaded": False,
    }
    return payload


def _dashboard_status_channel_report_payload(
    *,
    root: Path,
    session_id: str,
    url: str | None,
    status: str,
    blocker_code: str | None = None,
    blocker_message: str | None = None,
) -> dict[str, Any]:
    report = {
        "schema_id": DASHBOARD_STATUS_CHANNEL_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "dashboard_status_channel_status": status,
        "dashboard_status_channel_mode": DASHBOARD_STATUS_CHANNEL_MODE,
        "dashboard_status_channel_url": url,
        "dashboard_status_channel_host": DASHBOARD_STATUS_CHANNEL_HOST,
        "dashboard_status_channel_source": "runner_status.json",
        "dashboard_status_channel_path": str(runner_dashboard_status_channel_path(root, session_id)),
        "dashboard_status_channel_runner_pid": os.getpid(),
        "primary_blocker_code": blocker_code,
        "primary_blocker_message": blocker_message,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "private_endpoint_called": False,
        "credential_load_attempted": False,
        "live_key_loaded": False,
    }
    report["dashboard_status_channel_hash"] = _json_hash(report)
    return report


def _write_dashboard_status_channel_stopping_report(
    root: Path,
    session_id: str,
    *,
    blocker_message: str = "Operator stop requested; local runner status channel is shutting down.",
) -> None:
    channel = _dashboard_status_channel_report(root, session_id)
    channel_url = None
    if isinstance(channel, dict):
        channel_url = _safe_local_dashboard_url(channel.get("dashboard_status_channel_url"))
    durable_atomic_write_json(
        runner_dashboard_status_channel_path(root, session_id),
        _dashboard_status_channel_report_payload(
            root=root,
            session_id=session_id,
            url=channel_url,
            status=RUNNER_STATUS_STOPPING,
            blocker_code=None,
            blocker_message=blocker_message,
        ),
    )


def _write_dashboard_status_channel_starting_report(
    root: Path,
    session_id: str,
    *,
    blocker_message: str = "Operator start superseded a pending stop request; runner status is primary again.",
) -> tuple[str | None, str | None]:
    channel = _dashboard_status_channel_report(root, session_id)
    channel_url = None
    if isinstance(channel, dict):
        channel_url = _safe_local_dashboard_url(channel.get("dashboard_status_channel_url"))
    status = RUNNER_STATUS_RUNNING if channel_url else "STARTING"
    durable_atomic_write_json(
        runner_dashboard_status_channel_path(root, session_id),
        _dashboard_status_channel_report_payload(
            root=root,
            session_id=session_id,
            url=channel_url,
            status=status,
            blocker_code=None if channel_url else "DASHBOARD_STATUS_CHANNEL_RESTART_PENDING",
            blocker_message=None if channel_url else blocker_message,
        ),
    )
    return status, channel_url


def _write_runner_status_stop_requested(
    root: Path,
    session_id: str,
    *,
    reason: str,
    generated_at_utc: str,
) -> dict[str, Any] | None:
    status_path = runner_status_path(root, session_id)
    status = _read_json(status_path)
    if not isinstance(status, dict):
        return None
    updated = dict(status)
    updated.update(
        {
            "generated_at_utc": generated_at_utc,
            "updated_at_utc": generated_at_utc,
            "runner_status": RUNNER_STATUS_STOPPING,
            "running": False,
            "next_cycle_eta": None,
            "stop_reason": "STOP_FILE_REQUESTED",
            "primary_blocker_code": None,
            "primary_blocker_message": (
                "Operator stop requested; waiting for the PAPER runner to confirm STOPPED."
            ),
            "dashboard_status_channel_enabled": False,
            "dashboard_status_channel_status": RUNNER_STATUS_STOPPING,
            "dashboard_status_channel_mode": DASHBOARD_STATUS_CHANNEL_MODE,
            "dashboard_status_channel_source": "runner_status.json",
            "dashboard_status_channel_path": str(runner_dashboard_status_channel_path(root, session_id)),
            "dashboard_status_channel_live_order_ready": False,
            "dashboard_status_channel_live_order_allowed": False,
            "dashboard_status_channel_can_live_trade": False,
            "dashboard_status_channel_scale_up_allowed": False,
            "operator_stop_reason": reason,
        }
    )
    if _safe_local_dashboard_url(updated.get("dashboard_status_channel_url")) is None:
        updated["dashboard_status_channel_url"] = None
    for flag in LIVE_FALSE_FLAGS:
        updated[flag] = False
    updated["order_endpoint_called"] = False
    updated["status_hash"] = upbit_paper_long_runner_status_hash(updated)
    try:
        _write_runner_status(status_path, updated)
    except RuntimeError:
        return None
    return updated


def start_runner_dashboard_status_channel(
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
) -> DashboardStatusChannelHandle | None:
    root = Path(root)
    report_path = runner_dashboard_status_channel_path(root, session_id)

    def stop_file_watcher(server: ThreadingHTTPServer, url: str) -> None:
        stop_path = runner_stop_file_path(root, session_id)
        while not getattr(server, "dashboard_channel_stop", False):
            if stop_path.exists():
                if not getattr(server, "dashboard_channel_stop_signal_seen", False):
                    _write_dashboard_status_channel_stopping_report(root, session_id)
                    setattr(server, "dashboard_channel_stop_signal_seen", True)
            time.sleep(DEFAULT_DASHBOARD_STATUS_CHANNEL_STOP_POLL_SECONDS)

    def handler_factory() -> type[BaseHTTPRequestHandler]:
        channel_root = root
        channel_session_id = session_id

        class DashboardStatusChannelHandler(BaseHTTPRequestHandler):
            server_version = "TRADER1DashboardStatus/1.0"

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                return

            def _send_json(self, payload: dict[str, Any]) -> None:
                body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_dashboard_html(self) -> None:
                path = runner_dashboard_path(channel_root, channel_session_id)
                if path.exists():
                    body = path.read_bytes()
                else:
                    body = b"<!doctype html><title>TRADER_1</title><p>Dashboard file not generated yet.</p>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_events(self) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                while not getattr(self.server, "dashboard_channel_stop", False):
                    payload = _dashboard_status_channel_payload(channel_root, channel_session_id)
                    body = "event: runner_status\n" f"data: {json.dumps(payload, ensure_ascii=False, sort_keys=True)}\n\n"
                    try:
                        self.wfile.write(body.encode("utf-8"))
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        break
                    time.sleep(DEFAULT_DASHBOARD_STATUS_CHANNEL_STOP_POLL_SECONDS)

            def do_GET(self) -> None:
                path = urlparse(self.path).path
                if path in {"/", "/index.html"}:
                    self._send_dashboard_html()
                elif path in {"/api/runner-status", "/runner_status.json"}:
                    self._send_json(_dashboard_status_channel_payload(channel_root, channel_session_id))
                elif path == "/events":
                    self._send_events()
                elif path == "/health":
                    self._send_json(
                        {
                            "status": "PASS",
                            "channel_mode": DASHBOARD_STATUS_CHANNEL_MODE,
                            "live_order_ready": False,
                            "live_order_allowed": False,
                            "can_live_trade": False,
                            "scale_up_allowed": False,
                        }
                    )
                else:
                    self.send_response(404)
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()

        return DashboardStatusChannelHandler

    try:
        server = _QuietDashboardStatusChannelServer((DASHBOARD_STATUS_CHANNEL_HOST, 0), handler_factory())
        server.daemon_threads = True
        setattr(server, "dashboard_channel_stop", False)
        url = f"http://{DASHBOARD_STATUS_CHANNEL_HOST}:{server.server_port}/"
        thread = threading.Thread(target=server.serve_forever, name="trader1-dashboard-status-channel", daemon=True)
        thread.start()
        stop_watcher = threading.Thread(
            target=stop_file_watcher,
            args=(server, url),
            name="trader1-dashboard-status-channel-stop-watcher",
            daemon=True,
        )
        stop_watcher.start()
        durable_atomic_write_json(
            report_path,
            _dashboard_status_channel_report_payload(
                root=root,
                session_id=session_id,
                url=url,
                status="RUNNING",
            ),
        )
        return DashboardStatusChannelHandle(
            server=server,
            thread=thread,
            url=url,
            report_path=report_path,
            stop_watcher=stop_watcher,
        )
    except Exception as exc:
        durable_atomic_write_json(
            report_path,
            _dashboard_status_channel_report_payload(
                root=root,
                session_id=session_id,
                url=None,
                status="BLOCKED",
                blocker_code="DASHBOARD_STATUS_CHANNEL_START_FAILED",
                blocker_message=str(exc),
            ),
        )
        return None


def stop_runner_dashboard_status_channel(
    handle: DashboardStatusChannelHandle | None,
    *,
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
    final_status: str = "STOPPED",
    grace_seconds: float = 0.0,
) -> None:
    if handle is None:
        return
    try:
        durable_atomic_write_json(
            handle.report_path,
            _dashboard_status_channel_report_payload(
                root=root,
                session_id=session_id,
                url=handle.url,
                status=final_status,
            ),
        )
        if grace_seconds > 0:
            time.sleep(grace_seconds)
    finally:
        try:
            setattr(handle.server, "dashboard_channel_stop", True)
            handle.server.shutdown()
        finally:
            handle.server.server_close()
            handle.thread.join(timeout=1.0)
            if handle.stop_watcher is not None and handle.stop_watcher is not threading.current_thread():
                handle.stop_watcher.join(timeout=1.0)


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float_value(value: Any, default: float = -1_000_000_000.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _sample_live_flags_clear(sample: dict[str, Any]) -> bool:
    return all(
        sample.get(field) is not True
        for field in (
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
            "order_adapter_called",
            "private_endpoint_called",
            "credential_load_attempted",
            "live_key_loaded",
        )
    ) and sample.get("scorecard_candidate_live_flags_clear") is not False


def _profitability_sample_usable(sample: dict[str, Any]) -> bool:
    return (
        _sample_live_flags_clear(sample)
        and sample.get("scorecard_candidate_identity_binding_status") == "BOUND"
        and bool(sample.get("source_runtime_cycle_path"))
        and bool(sample.get("source_runtime_cycle_hash"))
        and bool(sample.get("scorecard_candidate_id"))
        and bool(sample.get("scorecard_strategy_id"))
        and bool(sample.get("scorecard_parameter_hash"))
        and _int_value(sample.get("candidate_count")) > 0
    )


def _runtime_sample_history_source_identity(history: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(history, dict):
        return None
    samples = history.get("samples")
    if not isinstance(samples, list):
        samples = []
    active = history.get("active_candidate_scope")
    return {
        "accepted_cycle_sample_count": _int_value(history.get("accepted_cycle_sample_count")),
        "unique_runtime_cycle_hash_count": _int_value(history.get("unique_runtime_cycle_hash_count")),
        "source_loop_report_hashes": (
            list(history.get("source_loop_report_hashes"))
            if isinstance(history.get("source_loop_report_hashes"), list)
            else []
        ),
        "source_runtime_cycle_hashes": (
            list(history.get("source_runtime_cycle_hashes"))
            if isinstance(history.get("source_runtime_cycle_hashes"), list)
            else []
        ),
        "sample_hashes": [
            str(sample.get("sample_hash"))
            for sample in samples
            if isinstance(sample, dict) and sample.get("sample_hash")
        ],
        "active_candidate_scope": active if isinstance(active, dict) else None,
        "active_candidate_scope_sample_count": _int_value(history.get("active_candidate_scope_sample_count")),
        "active_candidate_scope_sample_deficit": _int_value(history.get("active_candidate_scope_sample_deficit")),
    }


def _sample_history_live_private_drift(history: dict[str, Any]) -> bool:
    drift_flags = (*LIVE_FALSE_FLAGS, "order_endpoint_called")
    if any(history.get(flag) is True for flag in drift_flags):
        return True
    active = history.get("active_candidate_scope")
    if isinstance(active, dict) and _paper_scope_focus_has_live_private_drift(active):
        return True
    for summary in history.get("candidate_scope_sample_summaries") or []:
        if isinstance(summary, dict) and _paper_scope_focus_has_live_private_drift(summary):
            return True
    for sample in history.get("samples") or []:
        if isinstance(sample, dict) and any(sample.get(flag) is True for flag in drift_flags):
            return True
    return False


def _materialize_source_runtime_sample_history(
    *,
    root: Path,
    history_path: Path,
    source_history: dict[str, Any] | None,
    companion_history: dict[str, Any] | None,
    companion_status: str,
) -> dict[str, Any]:
    base = {
        "runtime_sample_history_materialization_status": "NOT_RUN",
        "runtime_sample_history_materialized_from_source": False,
        "runtime_sample_history_materialized_path": str(history_path),
        "runtime_sample_history_materialized_accepted_cycle_sample_count": 0,
        "runtime_sample_history_materialized_active_candidate_id": None,
        "runtime_sample_history_materialization_blocker_code": None,
        "runtime_sample_history_materialization_message": "No validated source-derived runtime sample history was available.",
    }
    if not isinstance(source_history, dict):
        return base

    source_identity = _runtime_sample_history_source_identity(source_history)
    companion_identity = _runtime_sample_history_source_identity(companion_history)
    source_accepted_count = _int_value(source_history.get("accepted_cycle_sample_count"))
    active = source_history.get("active_candidate_scope")
    active_candidate_id = (
        str(active.get("candidate_id"))
        if isinstance(active, dict) and active.get("candidate_id")
        else None
    )
    base.update(
        {
            "runtime_sample_history_materialized_accepted_cycle_sample_count": source_accepted_count,
            "runtime_sample_history_materialized_active_candidate_id": active_candidate_id,
        }
    )
    if source_accepted_count <= 0:
        base.update(
            {
                "runtime_sample_history_materialization_status": "NOT_NEEDED",
                "runtime_sample_history_materialization_message": (
                    "Validated source-derived runtime sample history has no accepted PAPER samples to materialize."
                ),
            }
        )
        return base
    if companion_status == "PASS" and companion_identity == source_identity:
        base.update(
            {
                "runtime_sample_history_materialization_status": "NOT_NEEDED",
                "runtime_sample_history_materialization_message": (
                    "Canonical runtime sample history already matches validated source-derived PAPER samples."
                ),
            }
        )
        return base
    if _sample_history_live_private_drift(source_history):
        base.update(
            {
                "runtime_sample_history_materialization_status": "BLOCKED",
                "runtime_sample_history_materialization_blocker_code": "LIVE_FINAL_GUARD_FAILED",
                "runtime_sample_history_materialization_message": (
                    "Source-derived runtime sample history attempted live/private/order/key state."
                ),
            }
        )
        return base

    try:
        written_path = write_upbit_paper_runtime_sample_history(root=root, history=source_history)
        materialized = _read_json(written_path)
        materialized_result = (
            validate_upbit_paper_runtime_sample_history_sources(root=root, history=materialized)
            if isinstance(materialized, dict)
            else None
        )
    except Exception as exc:  # pragma: no cover - filesystem failure must fail closed.
        base.update(
            {
                "runtime_sample_history_materialization_status": "BLOCKED",
                "runtime_sample_history_materialization_blocker_code": "RUNTIME_SAMPLE_HISTORY_MATERIALIZATION_FAILED",
                "runtime_sample_history_materialization_message": str(exc),
            }
        )
        return base
    if materialized_result is None or _result_status(materialized_result) != "PASS":
        base.update(
            {
                "runtime_sample_history_materialization_status": "BLOCKED",
                "runtime_sample_history_materialization_blocker_code": (
                    _result_blocker_code(materialized_result)
                    if materialized_result is not None
                    else "RUNTIME_SAMPLE_HISTORY_MATERIALIZATION_FAILED"
                ),
                "runtime_sample_history_materialization_message": (
                    str(getattr(materialized_result, "message", "") or "")
                    if materialized_result is not None
                    else "Materialized runtime sample history was not readable."
                ),
            }
        )
        return base
    if _runtime_sample_history_source_identity(materialized) != source_identity:
        base.update(
            {
                "runtime_sample_history_materialization_status": "BLOCKED",
                "runtime_sample_history_materialization_blocker_code": "SOURCE_IDENTITY_MISMATCH",
                "runtime_sample_history_materialization_message": (
                    "Materialized runtime sample history no longer matches source-derived PAPER sample identity."
                ),
            }
        )
        return base

    base.update(
        {
            "runtime_sample_history_materialization_status": "PASS",
            "runtime_sample_history_materialized_from_source": True,
            "runtime_sample_history_materialized_path": str(written_path),
            "runtime_sample_history_materialization_message": (
                "Canonical runtime sample history was refreshed from validated source-derived PAPER samples."
            ),
        }
    )
    return base


def _profitability_sample_rank_key(index: int, sample: dict[str, Any]) -> tuple[int, int, int, float, int, int, int, int]:
    decision = str(sample.get("scorecard_candidate_decision") or "")
    net_ev = _float_value(sample.get("scorecard_candidate_net_ev_after_cost_bps"))
    return (
        1 if _profitability_sample_usable(sample) else 0,
        1 if decision == "PAPER_ENTRY_REVIEW" else 0,
        1 if net_ev > 0 else 0,
        net_ev,
        1 if _int_value(sample.get("entry_reason_count")) > 0 else 0,
        1 if _int_value(sample.get("no_trade_reason_count")) > 0 else 0,
        _int_value(sample.get("candidate_count")),
        index,
    )


def _select_profitability_evidence_sample(
    samples: list[dict[str, Any]],
    *,
    active_scope: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prefer actionable non-live entry-review evidence over a later passive no-trade sample."""
    valid_samples = [sample for sample in samples if isinstance(sample, dict)]
    if not valid_samples:
        return None
    if isinstance(active_scope, dict):
        active_candidate_id = str(active_scope.get("candidate_id") or "")
        active_cycle_hash = str(active_scope.get("latest_runtime_cycle_hash") or "")
        active_cycle_id = str(active_scope.get("latest_cycle_id") or "")
        for sample in reversed(valid_samples):
            if not _profitability_sample_usable(sample):
                continue
            if active_candidate_id and str(sample.get("scorecard_candidate_id") or "") != active_candidate_id:
                continue
            sample_hash = str(sample.get("source_runtime_cycle_hash") or "")
            sample_path = str(sample.get("source_runtime_cycle_path") or "")
            if (active_cycle_hash and sample_hash == active_cycle_hash) or (
                active_cycle_id and active_cycle_id in sample_path
            ):
                return sample
    ranked = [
        (index, sample)
        for index, sample in enumerate(valid_samples)
        if _profitability_sample_usable(sample)
    ]
    if not ranked:
        return None
    return max(ranked, key=lambda item: _profitability_sample_rank_key(item[0], item[1]))[1]


def _scorecard_candidate_id_from_runtime_sample(sample: dict[str, Any]) -> str | None:
    if sample.get("scorecard_candidate_identity_binding_status") != "BOUND":
        return None
    if sample.get("scorecard_candidate_live_flags_clear") is False:
        return None
    candidate_id = str(sample.get("scorecard_candidate_id") or "")
    return candidate_id or None


def _runner_start_reconciliation_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("reconciliation_hash", None)
    return _json_hash(payload)


def _supersede_operator_stop_reports_for_start(
    root: Path,
    session_id: str,
    *,
    reason: str,
    generated_at_utc: str,
) -> dict[str, Any]:
    current_status = _read_json(runner_status_path(root, session_id))
    runner_status_after = current_status.get("runner_status") if isinstance(current_status, dict) else None
    runner_running_after = current_status.get("running") if isinstance(current_status, dict) else None
    result: dict[str, Any] = {
        "operator_stop_request_superseded": False,
        "runner_stop_request_status_before": None,
        "runner_stop_request_status_after": None,
        "root_stop_request_status_before": None,
        "root_stop_request_status_after": None,
        "dashboard_status_channel_status_before": None,
        "dashboard_status_channel_status_after": None,
        "dashboard_status_channel_url_preserved": False,
    }

    runner_report_path = runner_stop_request_report_path(root, session_id)
    runner_report = _read_json(runner_report_path)
    if isinstance(runner_report, dict):
        result["runner_stop_request_status_before"] = runner_report.get("stop_request_status")
        if runner_report.get("stop_request_status") in {"STOP_REQUESTED", "STOP_CONFIRMED"}:
            updated_runner_report = dict(runner_report)
            updated_runner_report.update(
                {
                    "updated_at_utc": generated_at_utc,
                    "stop_request_status": STOP_REQUEST_SUPERSEDED_BY_START,
                    "stop_confirmed": False,
                    "runner_status_after": runner_status_after,
                    "runner_running_after": runner_running_after,
                    "primary_blocker_code": None,
                    "primary_blocker_message": (
                        f"Pending operator stop request was superseded by {reason}; PAPER runner status is primary."
                    ),
                }
            )
            for flag in LIVE_FALSE_FLAGS:
                updated_runner_report[flag] = False
            updated_runner_report["order_endpoint_called"] = False
            updated_runner_report["stop_request_hash"] = upbit_paper_operator_stop_request_hash(
                updated_runner_report
            )
            durable_atomic_write_json(runner_report_path, updated_runner_report)
            result["operator_stop_request_superseded"] = True
            result["runner_stop_request_status_after"] = STOP_REQUEST_SUPERSEDED_BY_START

    root_report_path = _root_stop_request_report_path(root, session_id)
    root_report = _read_json(root_report_path)
    if isinstance(root_report, dict):
        result["root_stop_request_status_before"] = root_report.get("stop_request_status")
        scope_matches = (
            root_report.get("target_launcher_name") == "UPBIT_PAPER"
            and root_report.get("exchange") == "UPBIT"
            and root_report.get("market_type") == "KRW_SPOT"
            and root_report.get("mode") == "PAPER"
            and root_report.get("session_id") == session_id
        )
        if scope_matches and root_report.get("stop_request_status") in {"STOP_REQUESTED", "STOP_CONFIRMED"}:
            updated_root_report = dict(root_report)
            updated_root_report.update(
                {
                    "updated_at_utc": generated_at_utc,
                    "stop_request_status": STOP_REQUEST_SUPERSEDED_BY_START,
                    "stop_confirmed": False,
                    "stop_result_summary": (
                        "Previous UPBIT PAPER stop request was superseded by a later operator start."
                    ),
                    "runner_status_after": runner_status_after,
                    "runner_running_after": runner_running_after,
                    "dashboard_refresh_requested": True,
                    "dashboard_refresh_status": "PASS",
                    "dashboard_refresh_deferred": False,
                    "dashboard_should_show_stopped": False,
                    "primary_blocker_code": None,
                    "primary_blocker_message": (
                        f"Pending operator stop request was superseded by {reason}; PAPER runner status is primary."
                    ),
                }
            )
            for flag in LIVE_FALSE_FLAGS:
                updated_root_report[flag] = False
            updated_root_report["order_endpoint_called"] = False
            updated_root_report["stop_request_hash"] = _root_stop_request_report_hash(updated_root_report)
            durable_atomic_write_json(root_report_path, updated_root_report)
            result["operator_stop_request_superseded"] = True
            result["root_stop_request_status_after"] = STOP_REQUEST_SUPERSEDED_BY_START

    channel = _dashboard_status_channel_report(root, session_id)
    if isinstance(channel, dict):
        result["dashboard_status_channel_status_before"] = channel.get("dashboard_status_channel_status")
        if (
            channel.get("dashboard_status_channel_status") == RUNNER_STATUS_STOPPING
            or result["operator_stop_request_superseded"]
        ):
            status_after, channel_url = _write_dashboard_status_channel_starting_report(root, session_id)
            result["dashboard_status_channel_status_after"] = status_after
            result["dashboard_status_channel_url_preserved"] = bool(channel_url)
    return result


def clear_runner_stop_file_for_operator_start(
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
    *,
    reason: str = "EXPLICIT_OPERATOR_START",
) -> dict[str, Any]:
    """Consume a stale stop signal only for an explicit operator start path."""
    root = Path(root)
    stop_path = runner_stop_file_path(root, session_id)
    generated_at = utc_now()
    report: dict[str, Any] = {
        "schema_id": UPBIT_PAPER_RUNNER_START_RECONCILIATION_SCHEMA_ID,
        "generated_at_utc": generated_at,
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "status": "PASS",
        "reason": reason,
        "stop_file_path": str(stop_path),
        "stop_file_present_before": False,
        "stop_file_cleared": False,
        "stop_file_size_bytes": 0,
        "stop_file_sha256": None,
        "operator_stop_request_superseded": False,
        "runner_stop_request_status_before": None,
        "runner_stop_request_status_after": None,
        "root_stop_request_status_before": None,
        "root_stop_request_status_after": None,
        "dashboard_status_channel_status_before": None,
        "dashboard_status_channel_status_after": None,
        "dashboard_status_channel_url_preserved": False,
        "blocker_code": None,
        "blocker_message": None,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "private_endpoint_called": False,
        "credential_load_attempted": False,
        "live_key_loaded": False,
    }
    if not _is_relative_to(stop_path, root):
        report.update(
            {
                "status": "BLOCKED",
                "blocker_code": "STOP_FILE_PATH_ESCAPED_WORKSPACE",
                "blocker_message": "Runner stop file path is outside the configured workspace root.",
            }
        )
    elif stop_path.exists():
        report["stop_file_present_before"] = True
        try:
            body = stop_path.read_bytes()
            report["stop_file_size_bytes"] = len(body)
            report["stop_file_sha256"] = hashlib.sha256(body).hexdigest()
            stop_path.unlink()
            report["stop_file_cleared"] = True
        except OSError as exc:
            report.update(
                {
                    "status": "BLOCKED",
                    "blocker_code": "STOP_FILE_CLEAR_FAILED",
                    "blocker_message": str(exc),
                }
            )
    if report["status"] == "PASS":
        report.update(
            _supersede_operator_stop_reports_for_start(
                root,
                session_id,
                reason=reason,
                generated_at_utc=generated_at,
            )
        )
    report["reconciliation_hash"] = _runner_start_reconciliation_hash(report)
    durable_atomic_write_json(runner_start_reconciliation_path(root, session_id), report)
    _append_log(
        root,
        session_id,
        {
            "event": "runner_start_reconciliation",
            "status": report["status"],
            "reason": reason,
            "stop_file_present_before": report["stop_file_present_before"],
            "stop_file_cleared": report["stop_file_cleared"],
            "operator_stop_request_superseded": report["operator_stop_request_superseded"],
            "blocker_code": report["blocker_code"],
            "at": generated_at,
        },
    )
    return report


def request_upbit_paper_runner_stop(
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
    *,
    reason: str = "ROOT_OPERATOR_STOP",
    wait_timeout_seconds: float = 90.0,
    poll_interval_seconds: float = 1.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Write the PAPER-only stop signal and optionally wait for confirmation."""

    root = Path(root)
    generated_at = utc_now()
    status_path = runner_status_path(root, session_id)
    stop_path = runner_stop_file_path(root, session_id)
    report_path = runner_stop_request_report_path(root, session_id)
    status_before = _read_json(status_path)
    liveness_before = runner_lock_liveness_from_status_report(status_before)
    lock_payload = _read_json(runner_lock_path(root, session_id))
    lock_pid = lock_payload.get("pid") if isinstance(lock_payload, dict) else None
    lock_pid_alive = _pid_is_running(lock_pid if isinstance(lock_pid, int) else None)
    active_runner_detected = bool(
        _canonical_runner_already_running(root, session_id)
        or liveness_before.get("runner_liveness_proven") is True
        or lock_pid_alive
    )
    report: dict[str, Any] = {
        "schema_id": UPBIT_PAPER_OPERATOR_STOP_SCHEMA_ID,
        "generated_at_utc": generated_at,
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "reason": reason,
        "stop_request_status": "NOT_REQUESTED",
        "stop_request_method": "STOP_FILE",
        "runner_status_path": str(status_path),
        "stop_file_path": str(stop_path),
        "stop_request_report_path": str(report_path),
        "runner_status_before": status_before.get("runner_status") if isinstance(status_before, dict) else None,
        "runner_running_before": status_before.get("running") if isinstance(status_before, dict) else None,
        "runner_pid_before": liveness_before.get("runner_lock_pid") or (lock_pid if isinstance(lock_pid, int) else None),
        "runner_liveness_proven_before": bool(liveness_before.get("runner_liveness_proven") or lock_pid_alive),
        "stop_file_written": False,
        "stop_file_cleared_as_stale": False,
        "wait_timeout_seconds": wait_timeout_seconds,
        "poll_interval_seconds": poll_interval_seconds,
        "stop_confirmed": False,
        "runner_status_after": None,
        "runner_running_after": None,
        "primary_blocker_code": None,
        "primary_blocker_message": None,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "private_endpoint_called": False,
        "credential_load_attempted": False,
        "live_key_loaded": False,
        "order_endpoint_called": False,
    }

    if not _is_relative_to(stop_path, root) or not _is_relative_to(report_path, root):
        report.update(
            {
                "stop_request_status": "BLOCKED",
                "primary_blocker_code": "STOP_FILE_PATH_ESCAPED_WORKSPACE",
                "primary_blocker_message": "Runner stop file path is outside the configured workspace root.",
            }
        )
    elif not active_runner_detected:
        if stop_path.exists():
            try:
                stop_path.unlink()
                report["stop_file_cleared_as_stale"] = True
            except OSError as exc:
                report.update(
                    {
                        "stop_request_status": "BLOCKED",
                        "primary_blocker_code": "STALE_STOP_FILE_CLEAR_FAILED",
                        "primary_blocker_message": str(exc),
                    }
                )
        if report["stop_request_status"] != "BLOCKED":
            report.update(
                {
                    "stop_request_status": "NO_RUNNING_RUNNER",
                    "stop_confirmed": True,
                    "primary_blocker_message": "No active UPBIT PAPER runner was detected.",
                }
            )
            completed_cycles = (
                status_before.get("completed_cycle_count")
                if isinstance(status_before, dict) and isinstance(status_before.get("completed_cycle_count"), int)
                else 0
            )
            failed_cycles = (
                status_before.get("failed_cycle_count")
                if isinstance(status_before, dict) and isinstance(status_before.get("failed_cycle_count"), int)
                else 0
            )
            stopped_status = build_runner_status_report(
                root=root,
                runner_id="operator-stop-no-running-runner",
                session_id=session_id,
                runner_status=RUNNER_STATUS_STOPPED,
                started_at_utc=generated_at,
                completed_cycle_count=max(0, completed_cycles),
                failed_cycle_count=max(0, failed_cycles),
                cycle_interval_seconds=0,
                primary_blocker_code="NO_RUNNING_RUNNER",
                primary_blocker_message="No active UPBIT PAPER runner was detected.",
                stop_reason="NO_RUNNING_RUNNER",
                next_cycle_eta=None,
            )
            _write_runner_status(status_path, stopped_status)
            report["runner_status_after"] = stopped_status.get("runner_status")
            report["runner_running_after"] = stopped_status.get("running")
    else:
        stop_signal = {
            "schema_id": "trader1.upbit_paper_runner_stop_signal.v1",
            "generated_at_utc": generated_at,
            "project_id": "TRADER_1",
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": session_id,
            "reason": reason,
            "runner_status_path": str(status_path),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "order_adapter_called": False,
            "private_endpoint_called": False,
            "credential_load_attempted": False,
            "live_key_loaded": False,
            "order_endpoint_called": False,
        }
        stop_signal["stop_signal_hash"] = _json_hash(stop_signal)
        try:
            durable_atomic_write_json(stop_path, stop_signal)
            report["stop_file_written"] = True
            report["stop_request_status"] = "STOP_REQUESTED"
            _write_dashboard_status_channel_stopping_report(
                root,
                session_id,
                blocker_message="Operator stop requested; dashboard should show STOPPING immediately.",
            )
            stopping_status = _write_runner_status_stop_requested(
                root,
                session_id,
                reason=reason,
                generated_at_utc=generated_at,
            )
            if isinstance(stopping_status, dict):
                report["runner_status_after"] = stopping_status.get("runner_status")
                report["runner_running_after"] = stopping_status.get("running")
        except OSError as exc:
            report.update(
                {
                    "stop_request_status": "BLOCKED",
                    "primary_blocker_code": "STOP_FILE_WRITE_FAILED",
                    "primary_blocker_message": str(exc),
                }
            )

    if report["stop_request_status"] == "STOP_REQUESTED":
        deadline = time.monotonic() + max(0.0, float(wait_timeout_seconds))
        while True:
            status_after = _read_json(status_path)
            report["runner_status_after"] = (
                status_after.get("runner_status") if isinstance(status_after, dict) else None
            )
            report["runner_running_after"] = status_after.get("running") if isinstance(status_after, dict) else None
            if (
                isinstance(status_after, dict)
                and status_after.get("runner_status") == RUNNER_STATUS_STOPPED
                and status_after.get("stop_reason") == "STOP_FILE"
            ):
                report["stop_request_status"] = "STOP_CONFIRMED"
                report["stop_confirmed"] = True
                break
            if (
                isinstance(status_after, dict)
                and status_after.get("runner_status") == RUNNER_STATUS_STOPPING
                and wait_timeout_seconds <= 0
            ):
                break
            if time.monotonic() >= deadline:
                if wait_timeout_seconds <= 0:
                    break
                report.update(
                    {
                        "stop_request_status": "STOP_REQUEST_TIMEOUT",
                        "primary_blocker_code": "STOP_CONFIRMATION_TIMEOUT",
                        "primary_blocker_message": (
                            "Stop signal was written, but the runner has not confirmed STOPPED yet."
                        ),
                    }
                )
                break
            sleep_fn(max(0.05, float(poll_interval_seconds)))

    report["stop_request_hash"] = upbit_paper_operator_stop_request_hash(report)
    durable_atomic_write_json(report_path, report)
    _append_log(
        root,
        session_id,
        {
            "event": "operator_stop_request",
            "status": report["stop_request_status"],
            "stop_file_written": report["stop_file_written"],
            "stop_confirmed": report["stop_confirmed"],
            "blocker_code": report["primary_blocker_code"],
            "at": generated_at,
        },
    )
    return report


def _background_runner_creation_flags() -> int:
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)) | int(
        getattr(subprocess, "DETACHED_PROCESS", 0)
    )


def start_upbit_paper_background_runner(
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
    *,
    dashboard_open_result: DashboardOpenResult | None = None,
    popen_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    generated_at = utc_now()
    launcher_path = root / "UPBIT_PAPER.py"
    log_path = runner_background_console_log_path(root, session_id)
    report_path = runner_background_launch_report_path(root, session_id)
    status_path = runner_status_path(root, session_id)
    command = [sys.executable, "-B", str(launcher_path)]
    env = os.environ.copy()
    env[FOREGROUND_RUNNER_ENV] = "1"
    env["TRADER1_UPBIT_PAPER_OPEN_DASHBOARD"] = "0"
    env.setdefault("PYTHONUNBUFFERED", "1")
    report: dict[str, Any] = {
        "schema_id": UPBIT_PAPER_BACKGROUND_LAUNCH_SCHEMA_ID,
        "generated_at_utc": generated_at,
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "background_launch_status": "NOT_STARTED",
        "background_runner_started": False,
        "background_runner_policy": "BACKGROUND_RUNNER_STATUS_DASHBOARD",
        "operator_console_auto_closes": True,
        "console_close_does_not_stop_runner": True,
        "dashboard_close_does_not_stop_runner": True,
        "runner_pid": None,
        "runner_status_path": str(status_path),
        "dashboard_path": str(runner_dashboard_path(root, session_id)),
        "stop_launcher_path": str(root / "STOP_UPBIT_PAPER.py"),
        "stop_file_path": str(runner_stop_file_path(root, session_id)),
        "background_console_log_path": str(log_path),
        "background_launch_report_path": str(report_path),
        "dashboard_open_attempted": dashboard_open_result.attempted if dashboard_open_result else False,
        "dashboard_opened": dashboard_open_result.opened if dashboard_open_result else False,
        "dashboard_open_method": dashboard_open_result.method if dashboard_open_result else "NOT_ATTEMPTED",
        "dashboard_open_target": dashboard_open_result.target if dashboard_open_result else None,
        "primary_blocker_code": None,
        "primary_blocker_message": None,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "private_endpoint_called": False,
        "credential_load_attempted": False,
        "live_key_loaded": False,
        "order_endpoint_called": False,
    }
    if not _is_relative_to(launcher_path, root):
        report.update(
            {
                "background_launch_status": "BLOCKED",
                "primary_blocker_code": "BACKGROUND_LAUNCHER_PATH_ESCAPED_WORKSPACE",
                "primary_blocker_message": "UPBIT_PAPER launcher path is outside the configured workspace root.",
            }
        )
    elif not launcher_path.exists():
        report.update(
            {
                "background_launch_status": "BLOCKED",
                "primary_blocker_code": "BACKGROUND_LAUNCHER_MISSING",
                "primary_blocker_message": "UPBIT_PAPER launcher file is missing.",
            }
        )
    else:
        popen = popen_fn or subprocess.Popen
        log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with log_path.open("ab") as log_handle:
                process = popen(
                    command,
                    cwd=str(root),
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log_handle,
                    stderr=log_handle,
                    creationflags=_background_runner_creation_flags(),
                )
            report.update(
                {
                    "background_launch_status": "STARTED",
                    "background_runner_started": True,
                    "runner_pid": int(getattr(process, "pid", 0) or 0) or None,
                }
            )
        except Exception as exc:
            report.update(
                {
                    "background_launch_status": "BLOCKED",
                    "primary_blocker_code": "BACKGROUND_RUNNER_START_FAILED",
                    "primary_blocker_message": str(exc),
                }
            )
    report["background_launch_hash"] = upbit_paper_background_launch_hash(report)
    durable_atomic_write_json(report_path, report)
    _append_log(
        root,
        session_id,
        {
            "event": "background_runner_launch",
            "status": report["background_launch_status"],
            "runner_pid": report["runner_pid"],
            "blocker_code": report["primary_blocker_code"],
            "at": generated_at,
        },
    )
    return report


def _candidate_scorecard_contract_errors(scorecard: dict[str, Any]) -> list[str]:
    from trader1.validation.mvp0_validators import _candidate_scorecard_net_ev_errors

    return _candidate_scorecard_net_ev_errors(scorecard)


def _overfit_diagnostic_contract_errors(diagnostic: dict[str, Any]) -> list[str]:
    from trader1.validation.mvp0_validators import _overfit_diagnostic_errors

    return _overfit_diagnostic_errors(diagnostic)


def _load_latest_runtime_cycle(root: Path, session_id: str) -> dict[str, Any] | None:
    return _read_json(runner_runtime_base(root, session_id) / "upbit_paper_runtime_cycle_report.json")


def _load_latest_retention_manifest(root: Path, session_id: str) -> dict[str, Any] | None:
    return _read_json(runner_retention_manifest_path(root, session_id))


def shadow_runtime_base(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return root / "system" / "runtime" / "upbit" / "krw_spot" / "shadow" / session_id


def shadow_runtime_harness_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return shadow_runtime_base(root, session_id) / "actual_runtime_harness_report.json"


def paper_shadow_harness_binding_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return shadow_runtime_base(root, session_id) / "paper_shadow_harness_binding_report.json"


def shadow_persistent_runtime_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return shadow_runtime_base(root, session_id) / "shadow_observation" / "shadow_observation_persistent_runtime_report.json"


def shadow_runtime_orchestration_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return shadow_runtime_base(root, session_id) / "runtime_orchestration_report.json"


def paper_runtime_sample_history_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_runtime_base(root, session_id) / "paper_runtime" / "upbit_paper_runtime_sample_history.json"


def paper_portfolio_current_truth_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_runtime_base(root, session_id) / "paper_runtime" / "portfolio" / "paper_portfolio_snapshot.json"


def paper_candidate_scorecard_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_runtime_base(root, session_id) / "profitability" / "candidate_scorecard.json"


def paper_candidate_scorecard_snapshot_path(
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
    candidate_id: Any = None,
) -> Path:
    filename = f"{safe_candidate_scorecard_filename(candidate_id)}.candidate_scorecard.json"
    return runner_runtime_base(root, session_id) / "profitability" / "candidate_scorecards" / filename


def paper_candidate_generation_report_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_runtime_base(root, session_id) / "profitability" / "candidate_generation_report.json"


def paper_candidate_generation_discovery_runtime_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_runtime_base(root, session_id) / "profitability" / "candidate_generation_discovery_runtime_cycle.json"


def paper_overfit_diagnostic_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_runtime_base(root, session_id) / "profitability" / "overfit_diagnostic_report.json"


def paper_shadow_evidence_accumulation_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_runtime_base(root, session_id) / "paper_shadow_evidence_accumulation_report.json"


def shadow_runtime_sample_history_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return shadow_runtime_base(root, session_id) / "shadow_runtime_sample_history.json"


def _validation_status_and_blocker(
    report: dict[str, Any] | None,
    validator: Callable[[dict[str, Any]], Any],
) -> tuple[str, str | None]:
    if not isinstance(report, dict):
        return "NOT_LOADED", "PAPER_SHADOW_RUNTIME_ARTIFACT_MISSING"
    try:
        result = validator(report)
    except Exception:
        return "FAIL", "PAPER_SHADOW_RUNTIME_VALIDATION_ERROR"
    return str(getattr(result, "status", "FAIL")), getattr(result, "blocker_code", None)


def _max_generated_at(*reports: dict[str, Any] | None) -> str | None:
    generated = [
        str(report.get("generated_at_utc"))
        for report in reports
        if isinstance(report, dict) and isinstance(report.get("generated_at_utc"), str)
    ]
    return max(generated) if generated else None


def _shadow_runtime_collection_fields(root: Path, session_id: str) -> dict[str, Any]:
    persistent = _read_json(shadow_persistent_runtime_path(root, session_id))
    harness = _read_json(shadow_runtime_harness_path(root, session_id))
    orchestration = _read_json(shadow_runtime_orchestration_path(root, session_id))
    binding = _read_json(paper_shadow_harness_binding_path(root, session_id))

    persistent_status, persistent_blocker = _validation_status_and_blocker(
        persistent,
        validate_shadow_observation_persistent_runtime_report,
    )
    harness_status, harness_blocker = _validation_status_and_blocker(
        harness,
        validate_shadow_observation_actual_runtime_harness_report,
    )
    orchestration_status, orchestration_blocker = _validation_status_and_blocker(
        orchestration,
        validate_shadow_observation_runtime_orchestration_report,
    )
    binding_status, binding_blocker = _validation_status_and_blocker(
        binding,
        validate_paper_shadow_harness_binding_report,
    )
    reports_present = all(isinstance(item, dict) for item in (persistent, harness, orchestration, binding))
    validations_pass = all(
        status == "PASS" for status in (persistent_status, harness_status, orchestration_status, binding_status)
    )
    short_window_executed = (
        reports_present
        and validations_pass
        and persistent.get("runtime_execution_mode") == "ACTUAL_PAPER_SHADOW_SHORT_WINDOW"
        and persistent.get("actual_persistent_runtime_executed") is True
        and harness.get("actual_non_live_runtime_harness_executed") is True
        and orchestration.get("source_hashes_verified") is True
        and binding.get("harness_hash_verified") is True
    )
    if short_window_executed:
        collection_status = PAPER_SHADOW_RUNTIME_REFRESH_EXECUTED
    elif reports_present:
        collection_status = PAPER_SHADOW_RUNTIME_REFRESH_BLOCKED
    else:
        collection_status = PAPER_SHADOW_RUNTIME_REFRESH_NOT_RUN
    primary_blocker = next(
        (
            blocker
            for blocker in (persistent_blocker, harness_blocker, orchestration_blocker, binding_blocker)
            if blocker
        ),
        None,
    )
    if collection_status == PAPER_SHADOW_RUNTIME_REFRESH_BLOCKED and primary_blocker is None:
        primary_blocker = PAPER_SHADOW_RUNTIME_REFRESH_FAILED_BLOCKER_CODE

    return {
        "paper_shadow_runtime_collection_status": collection_status,
        "paper_shadow_runtime_collection_at_utc": _max_generated_at(persistent, harness, orchestration, binding),
        "shadow_persistent_runtime_path": str(shadow_persistent_runtime_path(root, session_id)),
        "shadow_runtime_harness_path": str(shadow_runtime_harness_path(root, session_id)),
        "shadow_runtime_orchestration_path": str(shadow_runtime_orchestration_path(root, session_id)),
        "paper_shadow_harness_binding_path": str(paper_shadow_harness_binding_path(root, session_id)),
        "shadow_persistent_runtime_hash": (
            persistent.get("runtime_report_hash")
            if isinstance(persistent, dict)
            and persistent.get("runtime_report_hash") == shadow_observation_persistent_runtime_hash(persistent)
            else None
        ),
        "shadow_runtime_harness_hash": (
            harness.get("harness_report_hash")
            if isinstance(harness, dict)
            and harness.get("harness_report_hash") == shadow_observation_actual_runtime_harness_hash(harness)
            else None
        ),
        "shadow_runtime_orchestration_hash": (
            orchestration.get("orchestration_report_hash")
            if isinstance(orchestration, dict)
            and orchestration.get("orchestration_report_hash") == shadow_observation_runtime_orchestration_hash(orchestration)
            else None
        ),
        "paper_shadow_harness_binding_hash": (
            binding.get("binding_report_hash")
            if isinstance(binding, dict)
            and binding.get("binding_report_hash") == paper_shadow_harness_binding_hash(binding)
            else None
        ),
        "shadow_persistent_runtime_validation_status": persistent_status,
        "shadow_runtime_harness_validation_status": harness_status,
        "shadow_runtime_orchestration_validation_status": orchestration_status,
        "paper_shadow_harness_binding_validation_status": binding_status,
        "shadow_completed_cycle_count": int(persistent.get("completed_cycle_count") or 0) if isinstance(persistent, dict) else 0,
        "shadow_observation_count": int(harness.get("observation_count") or 0) if isinstance(harness, dict) else 0,
        "shadow_observed_runtime_seconds": (
            int(persistent.get("observed_runtime_seconds") or 0) if isinstance(persistent, dict) else 0
        ),
        "shadow_actual_persistent_runtime_executed": (
            bool(persistent.get("actual_persistent_runtime_executed")) if isinstance(persistent, dict) else False
        ),
        "shadow_long_run_evidence_eligible": False,
        "paper_shadow_primary_blocker_code": primary_blocker,
    }


def _result_status(result: Any) -> str:
    return str(getattr(result, "status", "NOT_RUN") or "NOT_RUN")


def _result_blocker_code(result: Any) -> str | None:
    blocker = getattr(result, "blocker_code", None)
    return str(blocker) if blocker else None


def _paper_scope_progress_fields(
    *,
    history: dict[str, Any] | None,
    evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    active_scope = history.get("active_candidate_scope") if isinstance(history, dict) else None
    active = active_scope if isinstance(active_scope, dict) else {}
    history_scope_status = history.get("active_candidate_scope_status") if isinstance(history, dict) else None
    active_scope_status = active.get("scope_progress_status")
    history_scope_next_action = history.get("active_candidate_scope_next_action") if isinstance(history, dict) else None
    active_scope_next_action = active.get("next_operator_action")
    history_scope_sample_count = (
        history.get("active_candidate_scope_sample_count") if isinstance(history, dict) else None
    )
    history_scope_sample_deficit = (
        history.get("active_candidate_scope_sample_deficit") if isinstance(history, dict) else None
    )
    min_required = _int_value(
        history.get("min_profitability_scope_sample_count") if isinstance(history, dict) else None,
        _int_value(
            evidence.get("min_required_sample_count") if isinstance(evidence, dict) else None,
            DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT,
        ),
    )
    sample_count = _int_value(
        history_scope_sample_count,
        _int_value(
            active.get("sample_count"),
            _int_value(evidence.get("paper_sample_count") if isinstance(evidence, dict) else None, 0),
        ),
    )
    sample_deficit = _int_value(
        history_scope_sample_deficit,
        _int_value(
            active.get("sample_deficit"),
            _int_value(
                evidence.get("paper_sample_deficit") if isinstance(evidence, dict) else None,
                max(0, min_required - sample_count),
            ),
        ),
    )
    status = (
        str(
            history_scope_status
            or active_scope_status
            or (evidence.get("evidence_actionability_status") if isinstance(evidence, dict) else None)
            or "NO_CANDIDATE_SCOPE"
        )
    )
    next_action = (
        str(
            history_scope_next_action
            or active_scope_next_action
            or (evidence.get("primary_collection_deficit_message") if isinstance(evidence, dict) else None)
            or "Keep PAPER running until a source-bound candidate scope appears."
        )
    )
    return {
        "paper_scope_progress_status": status,
        "paper_scope_candidate_id": (
            active.get("candidate_id")
            or (str(evidence.get("candidate_id")) if isinstance(evidence, dict) and evidence.get("candidate_id") else None)
        ),
        "paper_scope_strategy_id": (
            active.get("strategy_id")
            or (str(evidence.get("strategy_id")) if isinstance(evidence, dict) and evidence.get("strategy_id") else None)
        ),
        "paper_scope_parameter_hash": (
            active.get("parameter_hash")
            or (
                str(evidence.get("parameter_hash"))
                if isinstance(evidence, dict) and evidence.get("parameter_hash")
                else None
            )
        ),
        "paper_scope_symbol": active.get("symbol"),
        "paper_scope_sample_count": sample_count,
        "paper_scope_min_required_sample_count": min_required,
        "paper_scope_sample_deficit": sample_deficit,
        "paper_scope_next_collection_action": (
            active.get("next_collection_action")
            or (
                str(evidence.get("next_collection_action"))
                if isinstance(evidence, dict) and evidence.get("next_collection_action")
                else None
            )
            or "RUN_MORE_PAPER_SAMPLE_WINDOWS"
        ),
        "paper_scope_next_operator_action": next_action,
        "paper_scope_latest_sample_at_utc": active.get("latest_sample_at_utc"),
        "paper_scope_summary_count": (
            _int_value(history.get("candidate_scope_sample_summary_count"), 0)
            if isinstance(history, dict)
            else 0
        ),
    }


def _strategy_mutation_public_review_fields(context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context if isinstance(context, dict) else {}
    return {
        "strategy_mutation_compiler_status": str(context.get("status") or "NOT_RUN"),
        "strategy_mutation_compiler_blocker_code": context.get("blocker_code"),
        "strategy_mutation_compiler_path": context.get("path"),
        "strategy_mutation_compiler_candidate_id": context.get("candidate_id"),
        "strategy_mutation_compiler_source": context.get("source"),
        "strategy_mutation_reason_code": context.get("mutation_reason_code"),
        "strategy_mutation_id": context.get("mutation_id"),
        "strategy_mutated_paper_candidate_spec_id": context.get("mutated_paper_candidate_spec_id"),
        "strategy_mutation_spec_hash": context.get("mutation_spec_hash"),
        "strategy_mutated_parameter_hash": context.get("mutated_parameter_hash"),
        "strategy_mutation_exploration_budget_id": context.get("exploration_budget_id"),
        "strategy_mutation_ranking_eligible": False,
    }


def _strategy_mutation_compiler_artifact_fields(
    *,
    root: Path,
    session_id: str,
    active_candidate_id: str | None,
) -> dict[str, Any]:
    base = _strategy_mutation_public_review_fields(
        {
            "status": "NOT_RUN",
            "blocker_code": None,
            "candidate_id": active_candidate_id,
            "source": "NO_CURRENT_MUTATION_REPORT",
        }
    )
    base.update(
        {
            "strategy_mutation_compiler_report_current": False,
            "strategy_mutation_compiler_report_ignored_candidate_id": None,
            "strategy_mutation_compiler_message": (
                "No current mutation compiler report has been written for this PAPER candidate yet."
            ),
        }
    )
    try:
        from trader1.research.profitability.strategy_mutation_compiler import (
            strategy_mutation_compiler_report_path,
            validate_strategy_mutation_compiler_report,
        )
    except Exception as exc:
        base.update(
            {
                "strategy_mutation_compiler_status": "BLOCKED",
                "strategy_mutation_compiler_blocker_code": "STRATEGY_MUTATION_COMPILER_UNAVAILABLE",
                "strategy_mutation_compiler_source": "MUTATION_COMPILER_IMPORT_FAILED",
                "strategy_mutation_compiler_message": str(exc),
            }
        )
        return base

    path = strategy_mutation_compiler_report_path(root=root, session_id=session_id)
    base["strategy_mutation_compiler_path"] = _relative_runtime_path(path, root)
    if not path.exists():
        return base
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        base.update(
            {
                "strategy_mutation_compiler_status": "BLOCKED",
                "strategy_mutation_compiler_blocker_code": "SCHEMA_IDENTITY_MISMATCH",
                "strategy_mutation_compiler_source": "MUTATION_REPORT_UNREADABLE",
                "strategy_mutation_compiler_message": str(exc),
            }
        )
        return base

    status, message, blocker_code = validate_strategy_mutation_compiler_report(report)
    report_candidate_id = report.get("candidate_id") if isinstance(report, dict) else None
    if status != "PASS":
        base.update(
            {
                "strategy_mutation_compiler_status": "BLOCKED",
                "strategy_mutation_compiler_blocker_code": blocker_code or "SCHEMA_IDENTITY_MISMATCH",
                "strategy_mutation_compiler_candidate_id": active_candidate_id or report_candidate_id,
                "strategy_mutation_compiler_source": "MUTATION_REPORT_INVALID",
                "strategy_mutation_compiler_message": message,
            }
        )
        return base

    if active_candidate_id and report_candidate_id and str(report_candidate_id) != str(active_candidate_id):
        base.update(
            {
                "strategy_mutation_compiler_report_ignored_candidate_id": str(report_candidate_id),
                "strategy_mutation_compiler_source": "STALE_MUTATION_REPORT_IGNORED",
                "strategy_mutation_compiler_message": (
                    "Existing mutation report belongs to a different PAPER candidate and is ignored for current "
                    "runner status."
                ),
            }
        )
        return base

    spec = report.get("mutated_paper_candidate_spec") if isinstance(report, dict) else None
    budget = report.get("mutation_budget_state") if isinstance(report, dict) else None
    base.update(
        _strategy_mutation_public_review_fields(
            {
                "status": str(report.get("compile_status") or "BLOCKED"),
                "blocker_code": report.get("primary_blocker_code"),
                "path": _relative_runtime_path(path, root),
                "candidate_id": report_candidate_id or active_candidate_id,
                "source": "CURRENT_MUTATION_REPORT",
                "mutation_reason_code": report.get("mutation_reason_code"),
                "mutation_id": spec.get("mutation_id") if isinstance(spec, dict) else None,
                "mutated_paper_candidate_spec_id": spec.get("spec_id") if isinstance(spec, dict) else None,
                "mutation_spec_hash": spec.get("spec_hash") if isinstance(spec, dict) else None,
                "mutated_parameter_hash": spec.get("parameter_hash") if isinstance(spec, dict) else None,
                "exploration_budget_id": budget.get("exploration_budget_id") if isinstance(budget, dict) else None,
            }
        )
    )
    base.update(
        {
            "strategy_mutation_compiler_report_current": True,
            "strategy_mutation_compiler_report_ignored_candidate_id": None,
            "strategy_mutation_compiler_message": message,
        }
    )
    return base


def _candidate_generation_public_review_blocked_fields(
    *,
    discovery_status: str = "NOT_REQUESTED",
    discovery_blocker_code: str | None = None,
    discovery_message: str = "bounded public candidate discovery was not requested",
    discovery_symbol_count: int = 0,
    alternative_replay_status: str = "NOT_REQUIRED",
    alternative_replay_blocker_code: str | None = None,
    alternative_replay_message: str = "alternative public replay is not required until a bounded candidate is review-ready",
    candidate_discovery_runtime_path: str | None = None,
    alternative_replay_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    replay = alternative_replay_context if isinstance(alternative_replay_context, dict) else {}
    return {
        "candidate_discovery_status": discovery_status,
        "candidate_discovery_blocker_code": discovery_blocker_code,
        "candidate_discovery_message": discovery_message,
        "candidate_discovery_runtime_cycle_path": candidate_discovery_runtime_path,
        "candidate_discovery_symbol_count": _int_value(discovery_symbol_count, 0),
        "alternative_public_replay_status": alternative_replay_status,
        "alternative_public_replay_blocker_code": alternative_replay_blocker_code,
        "alternative_public_replay_message": alternative_replay_message,
        "alternative_public_replay_report_path": replay.get("report_path"),
        "alternative_public_replay_candidate_id": replay.get("candidate_id"),
        "alternative_public_replay_symbol": replay.get("symbol"),
        "alternative_public_replay_replay_status": replay.get("replay_status"),
        "alternative_public_replay_sample_count": _int_value(replay.get("sample_count"), 0),
        "alternative_public_replay_closed_trade_sample_count": _int_value(
            replay.get("replay_closed_trade_sample_count"), 0
        ),
        "alternative_public_replay_closed_trade_deficit": _int_value(replay.get("replay_closed_trade_deficit"), 0),
        "alternative_public_replay_closed_trade_maturity_status": replay.get("replay_closed_trade_maturity_status"),
        "alternative_public_replay_closed_trade_maturity_blocker_code": replay.get(
            "replay_closed_trade_maturity_blocker_code"
        ),
        "alternative_public_replay_maturity_expansion_attempted": bool(
            replay.get("maturity_expansion_attempted")
        ),
        "alternative_public_replay_maturity_expansion_status": replay.get("maturity_expansion_status"),
        "alternative_public_replay_maturity_expansion_reason": replay.get("maturity_expansion_reason"),
        "alternative_public_replay_maturity_expansion_candidate_id": replay.get("maturity_expansion_candidate_id"),
        "alternative_public_replay_maturity_expansion_rotation_count": _int_value(
            replay.get("maturity_expansion_rotation_count"), 0
        ),
        "alternative_public_replay_maturity_expansion_target_count": _int_value(
            replay.get("maturity_expansion_target_count"), 0
        ),
        "alternative_public_replay_maturity_expansion_max_windows": _int_value(
            replay.get("maturity_expansion_max_windows"), 0
        ),
        **_strategy_mutation_public_review_fields(),
    }


def _candidate_generation_public_review_fields(
    *,
    discovery_context: dict[str, Any],
    alternative_replay_context: dict[str, Any],
    candidate_discovery_runtime_path: Path | None,
    root: Path,
    strategy_mutation_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        **_candidate_generation_public_review_blocked_fields(
            discovery_status=str(discovery_context.get("status") or "NOT_REQUESTED"),
            discovery_blocker_code=discovery_context.get("blocker_code"),
            discovery_message=str(discovery_context.get("message") or ""),
            discovery_symbol_count=_int_value(discovery_context.get("symbol_count"), 0),
            alternative_replay_status=str(alternative_replay_context.get("status") or "NOT_REQUIRED"),
            alternative_replay_blocker_code=alternative_replay_context.get("blocker_code"),
            alternative_replay_message=str(alternative_replay_context.get("message") or ""),
            candidate_discovery_runtime_path=(
                _relative_runtime_path(candidate_discovery_runtime_path, root)
                if candidate_discovery_runtime_path is not None
                else None
            ),
            alternative_replay_context=alternative_replay_context,
        ),
        "candidate_discovery_ranked_symbol_count": _int_value(discovery_context.get("ranked_symbol_count"), 0),
        "candidate_discovery_eligible_symbol_count": _int_value(discovery_context.get("eligible_symbol_count"), 0),
        "candidate_discovery_evaluated_candidate_count": _int_value(
            discovery_context.get("evaluated_candidate_count"), 0
        ),
        "candidate_discovery_paper_entry_review_candidate_count": _int_value(
            discovery_context.get("paper_entry_review_candidate_count"), 0
        ),
        "candidate_discovery_adaptive_expansion_attempted": bool(
            discovery_context.get("adaptive_expansion_attempted")
        ),
        "alternative_public_replay_primary_blocker_code": alternative_replay_context.get("primary_blocker_code"),
        "alternative_public_replay_strategy_exit_policy_sample_count": _int_value(
            alternative_replay_context.get("replay_strategy_exit_policy_sample_count"), 0
        ),
        "alternative_public_replay_profit_factor": _float_value(
            alternative_replay_context.get("replay_profit_factor"), 0.0
        ),
        "alternative_public_replay_profit_factor_status": alternative_replay_context.get("replay_profit_factor_status"),
        "alternative_public_replay_realized_vs_expected_edge_bps": _float_value(
            alternative_replay_context.get("replay_realized_vs_expected_edge_bps"), 0.0
        ),
        "alternative_public_replay_realized_vs_expected_edge_status": alternative_replay_context.get(
            "replay_realized_vs_expected_edge_status"
        ),
        **_strategy_mutation_public_review_fields(strategy_mutation_context),
    }


def _alternative_replay_closed_trade_maturity_expansion_needed(context: dict[str, Any]) -> bool:
    if str(context.get("status") or "") != "BLOCKED":
        return False
    blocker = str(
        context.get("replay_closed_trade_maturity_blocker_code")
        or context.get("blocker_code")
        or context.get("primary_blocker_code")
        or ""
    )
    if blocker != "REPLAY_CLOSED_TRADES_BELOW_MIN":
        return False
    closed_count = _int_value(context.get("replay_closed_trade_sample_count"), 0)
    deficit = _int_value(context.get("replay_closed_trade_deficit"), 0)
    sample_count = _int_value(context.get("sample_count"), 0)
    return closed_count > 0 and deficit > 0 and sample_count < DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_MAX_WINDOWS


def _alternative_replay_closed_trade_maturity_expansion_target(context: dict[str, Any]) -> int:
    closed_count = _int_value(context.get("replay_closed_trade_sample_count"), 0)
    sample_count = _int_value(context.get("sample_count"), 0)
    deficit = _int_value(context.get("replay_closed_trade_deficit"), 0)
    min_required = _int_value(
        context.get("min_required_closed_trade_sample_count"),
        closed_count + max(deficit, 0),
    )
    if deficit > 0:
        min_required = max(min_required, closed_count + deficit)
    if closed_count <= 0 or sample_count <= 0 or min_required <= 0:
        return DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_MIN_TARGET_COUNT
    density_adjusted_target = math.ceil((sample_count * min_required / closed_count) * 1.25)
    return max(
        DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_MIN_TARGET_COUNT,
        min(DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_MAX_TARGET_COUNT, density_adjusted_target),
    )


def _alternative_replay_closed_trade_priority(context: dict[str, Any]) -> tuple[int, int, int, float]:
    status_score = 2 if str(context.get("status") or "") == "PASS" else 1 if str(context.get("status") or "") == "BLOCKED" else 0
    maturity_score = 1 if str(context.get("replay_closed_trade_maturity_status") or "") == "PASS" else 0
    return (
        status_score,
        maturity_score,
        _int_value(context.get("replay_closed_trade_sample_count"), 0),
        _float_value(context.get("replay_realized_vs_expected_edge_bps"), -999.0),
    )


def _alternative_replay_closed_trade_maturity_expansion_candidates(
    context: dict[str, Any],
    *,
    limit: int = DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_ROTATION_LIMIT,
) -> list[dict[str, Any]]:
    primary_candidate_id = str(context.get("candidate_id") or "")
    candidates_by_id: dict[str, dict[str, Any]] = {}

    def add_candidate(item: dict[str, Any]) -> None:
        candidate_id = str(item.get("candidate_id") or "")
        if not candidate_id or not _alternative_replay_closed_trade_maturity_expansion_needed(item):
            return
        candidates_by_id[candidate_id] = dict(item)

    add_candidate(context)
    evaluations = context.get("candidate_review_evaluations")
    if isinstance(evaluations, list):
        for item in evaluations:
            if isinstance(item, dict):
                add_candidate(item)

    primary = [candidates_by_id.pop(primary_candidate_id)] if primary_candidate_id in candidates_by_id else []
    remaining = sorted(
        candidates_by_id.values(),
        key=_alternative_replay_closed_trade_priority,
        reverse=True,
    )
    return (primary + remaining)[: max(1, int(limit))]


def _candidate_generation_report_preferred_replay_candidate(
    report: dict[str, Any],
    *,
    candidate_id: str,
) -> dict[str, Any]:
    if not candidate_id:
        return report
    items = report.get("candidate_items")
    if not isinstance(items, list):
        return report
    preferred = [item for item in items if isinstance(item, dict) and str(item.get("candidate_id") or "") == candidate_id]
    if not preferred:
        return report
    reordered = preferred + [
        item for item in items if not (isinstance(item, dict) and str(item.get("candidate_id") or "") == candidate_id)
    ]
    updated = dict(report)
    updated["candidate_items"] = reordered
    updated["generation_hash"] = candidate_generation_report_hash(updated)
    return updated


def _build_strategy_mutation_context_for_public_review(
    *,
    root: Path,
    session_id: str,
    scorecard: dict[str, Any],
    diagnostic: dict[str, Any] | None,
    history: dict[str, Any],
    alternative_replay_context: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(diagnostic, dict):
        return {
            "status": "NOT_RUN",
            "blocker_code": None,
            "path": None,
            "candidate_id": scorecard.get("candidate_id"),
            "source": "DIAGNOSTIC_NOT_AVAILABLE",
            "ranking_eligible": False,
        }
    try:
        from trader1.research.profitability.convergence_memory import (
            optimizer_memory_state_from_scorecard,
            strategy_performance_memory_from_scorecard,
        )
        from tools.run_upbit_paper_candidate_scorecard import (
            _build_and_write_alternative_review_scorecard,
            _build_and_write_strategy_mutation_report,
        )

        alternative_review = _build_and_write_alternative_review_scorecard(
            root=root,
            history=history,
            alternative_replay_context=alternative_replay_context,
        )
        convergence_memory = {
            "strategy_performance_memory": strategy_performance_memory_from_scorecard(scorecard),
            "optimizer_memory_state": optimizer_memory_state_from_scorecard(scorecard),
        }
        return _build_and_write_strategy_mutation_report(
            root=root,
            session_id=session_id,
            candidate_scorecard=scorecard,
            overfit_diagnostic=diagnostic,
            convergence_memory=convergence_memory,
            replay_robustness_report=None,
            alternative_replay_context=alternative_replay_context,
            alternative_review_scorecard_context=alternative_review,
        )
    except Exception as exc:  # pragma: no cover - defensive runtime artifact path.
        message = str(exc)
        lowered = message.lower()
        blocker_code = (
            "LIVE_FINAL_GUARD_FAILED"
            if any(
                token in lowered
                for token in (
                    "live_order",
                    "order_endpoint",
                    "order_adapter",
                    "credential",
                    "private_endpoint",
                    "live key",
                )
            )
            else "STRATEGY_MUTATION_COMPILER_UNAVAILABLE"
        )
        return {
            "status": "BLOCKED",
            "blocker_code": blocker_code,
            "path": None,
            "candidate_id": scorecard.get("candidate_id"),
            "source": "PUBLIC_REVIEW_MUTATION_RUNTIME",
            "mutation_reason_code": None,
            "mutation_id": None,
            "mutated_paper_candidate_spec_id": None,
            "mutation_spec_hash": None,
            "mutated_parameter_hash": None,
            "exploration_budget_id": None,
            "ranking_eligible": False,
            "message": message,
        }


def _review_public_alternatives_for_candidate_generation(
    *,
    root: Path,
    session_id: str,
    runtime: dict[str, Any],
    scorecard: dict[str, Any],
    diagnostic: dict[str, Any] | None = None,
    history: dict[str, Any],
    candidate_generation_report: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    generation_status = str(candidate_generation_report.get("generation_status") or "")
    current_alternative_count = _int_value(candidate_generation_report.get("alternative_candidate_count"), 0)
    min_candidate_review_pool = max(2, min(DEFAULT_ALTERNATIVE_REPLAY_CANDIDATE_LIMIT, 12))
    discovery_needed = (
        candidate_generation_report.get("selected_candidate_retired_for_ranking") is True
        and (
            generation_status == "NO_ALTERNATIVE_READY"
            or current_alternative_count < min_candidate_review_pool
        )
    )
    public_replay_needed = (
        candidate_generation_report.get("selected_candidate_retired_for_ranking") is True
        and generation_status == "ALTERNATIVE_REVIEW_READY"
    )
    if not discovery_needed and not public_replay_needed:
        return (
            candidate_generation_report,
            _candidate_generation_public_review_blocked_fields(),
            None,
        )

    try:
        from tools.run_upbit_paper_candidate_scorecard import (
            _build_and_write_alternative_public_replay,
            _build_bounded_public_discovery_runtime_cycle,
        )
    except Exception as exc:  # pragma: no cover - import failure is environment-specific.
        return (
            candidate_generation_report,
            _candidate_generation_public_review_blocked_fields(
                discovery_status="BLOCKED",
                discovery_blocker_code="CANDIDATE_PUBLIC_DISCOVERY_UNAVAILABLE",
                discovery_message=str(exc),
            ),
            None,
        )

    candidate_discovery_runtime = None
    discovery_context = {
        "status": "NOT_REQUESTED",
        "blocker_code": None,
        "message": "bounded public candidate discovery was not requested",
        "symbol_count": 0,
    }
    if discovery_needed:
        candidate_discovery_runtime, discovery_context = _build_bounded_public_discovery_runtime_cycle(
            session_id=session_id,
            symbol_limit=DEFAULT_CANDIDATE_DISCOVERY_SYMBOL_LIMIT,
            timeout_seconds=DEFAULT_CANDIDATE_DISCOVERY_TIMEOUT_SECONDS,
            min_review_ready_candidate_count=min_candidate_review_pool,
        )
        if candidate_discovery_runtime is not None:
            discovered_generation = candidate_generation_report_from_upbit_paper_runtime_cycle(
                runtime,
                candidate_scorecard=scorecard,
                additional_runtime_cycle_reports=[candidate_discovery_runtime],
            )
            validation_status, generation_message, generation_blocker = validate_candidate_generation_report(
                discovered_generation,
                candidate_scorecard=scorecard,
            )
            if validation_status == "PASS":
                candidate_generation_report = discovered_generation
            else:
                return (
                    candidate_generation_report,
                    _candidate_generation_public_review_blocked_fields(
                        discovery_status="BLOCKED",
                        discovery_blocker_code=generation_blocker or "CANDIDATE_GENERATION_CONTRACT_FAILED",
                        discovery_message=generation_message,
                    ),
                    candidate_discovery_runtime,
                )

    if candidate_generation_report.get("generation_status") != "ALTERNATIVE_REVIEW_READY":
        discovery_path = (
            paper_candidate_generation_discovery_runtime_path(root, session_id)
            if candidate_discovery_runtime is not None
            else None
        )
        fields = _candidate_generation_public_review_fields(
            discovery_context=discovery_context,
            alternative_replay_context={
                "status": "NOT_REQUIRED",
                "blocker_code": None,
                "message": "alternative public replay is not required until a bounded candidate is review-ready",
            },
            candidate_discovery_runtime_path=discovery_path,
            root=root,
        )
        return candidate_generation_report, fields, candidate_discovery_runtime

    alternative_replay_context = _build_and_write_alternative_public_replay(
        root=root,
        session_id=session_id,
        candidate_generation_report=candidate_generation_report,
        history=history,
        runtime_cycle_report=runtime,
        candidate_discovery_runtime=candidate_discovery_runtime,
        target_count=DEFAULT_ALTERNATIVE_REPLAY_TARGET_COUNT,
        page_size=DEFAULT_ALTERNATIVE_REPLAY_PAGE_SIZE,
        timeout_seconds=DEFAULT_ALTERNATIVE_REPLAY_TIMEOUT_SECONDS,
        max_replay_windows=DEFAULT_ALTERNATIVE_REPLAY_MAX_WINDOWS,
        min_required_sample_count=DEFAULT_ALTERNATIVE_REPLAY_MIN_REQUIRED_SAMPLE_COUNT,
        candidate_limit=DEFAULT_ALTERNATIVE_REPLAY_CANDIDATE_LIMIT,
    )
    expansion_candidates = _alternative_replay_closed_trade_maturity_expansion_candidates(
        alternative_replay_context
    )
    if expansion_candidates:
        expanded_contexts: list[dict[str, Any]] = []
        for expansion_candidate in expansion_candidates:
            expansion_target_count = _alternative_replay_closed_trade_maturity_expansion_target(
                expansion_candidate
            )
            expansion_generation_report = _candidate_generation_report_preferred_replay_candidate(
                candidate_generation_report,
                candidate_id=str(expansion_candidate.get("candidate_id") or ""),
            )
            expanded_context = _build_and_write_alternative_public_replay(
                root=root,
                session_id=session_id,
                candidate_generation_report=expansion_generation_report,
                history=history,
                runtime_cycle_report=runtime,
                candidate_discovery_runtime=candidate_discovery_runtime,
                target_count=expansion_target_count,
                page_size=DEFAULT_ALTERNATIVE_REPLAY_PAGE_SIZE,
                timeout_seconds=DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_TIMEOUT_SECONDS,
                max_replay_windows=expansion_target_count,
                min_required_sample_count=DEFAULT_ALTERNATIVE_REPLAY_MIN_REQUIRED_SAMPLE_COUNT,
                candidate_limit=DEFAULT_ALTERNATIVE_REPLAY_MATURITY_EXPANSION_CANDIDATE_LIMIT,
            )
            expanded_context = dict(expanded_context)
            expanded_context["maturity_expansion_attempted"] = True
            expanded_context["maturity_expansion_candidate_id"] = str(expansion_candidate.get("candidate_id") or "")
            expanded_context["maturity_expansion_rotation_count"] = len(expansion_candidates)
            expanded_context["maturity_expansion_target_count"] = expansion_target_count
            expanded_context["maturity_expansion_max_windows"] = expansion_target_count
            expanded_contexts.append(expanded_context)
        best_expanded_context = max(expanded_contexts, key=_alternative_replay_closed_trade_priority)
        if _alternative_replay_closed_trade_priority(best_expanded_context) >= _alternative_replay_closed_trade_priority(
            alternative_replay_context
        ):
            best_expanded_context["maturity_expansion_status"] = str(best_expanded_context.get("status") or "BLOCKED")
            best_expanded_context["maturity_expansion_reason"] = "ADAPTIVE_CLOSED_TRADE_MATURITY_EXPANSION_SELECTED"
            alternative_replay_context = best_expanded_context
        else:
            alternative_replay_context = dict(alternative_replay_context)
            alternative_replay_context["maturity_expansion_attempted"] = True
            alternative_replay_context["maturity_expansion_status"] = str(best_expanded_context.get("status") or "BLOCKED")
            alternative_replay_context["maturity_expansion_reason"] = "INITIAL_REPLAY_RETAINED_HIGHER_CLOSED_TRADE_PRIORITY"
            alternative_replay_context["maturity_expansion_target_count"] = best_expanded_context.get(
                "maturity_expansion_target_count"
            )
            alternative_replay_context["maturity_expansion_max_windows"] = best_expanded_context.get(
                "maturity_expansion_max_windows"
            )
    if isinstance(alternative_replay_context.get("report"), dict):
        reviewed_generation = candidate_generation_report_from_upbit_paper_runtime_cycle(
            runtime,
            candidate_scorecard=scorecard,
            additional_runtime_cycle_reports=(
                [candidate_discovery_runtime] if candidate_discovery_runtime is not None else None
            ),
            best_alternative_public_replay_report=alternative_replay_context["report"],
            preferred_alternative_candidate_id=str(alternative_replay_context.get("candidate_id") or ""),
        )
        generation_status, generation_message, generation_blocker = validate_candidate_generation_report(
            reviewed_generation,
            candidate_scorecard=scorecard,
        )
        if generation_status == "PASS":
            candidate_generation_report = reviewed_generation
        else:
            alternative_replay_context = dict(alternative_replay_context)
            alternative_replay_context["status"] = "BLOCKED"
            alternative_replay_context["blocker_code"] = generation_blocker or "CANDIDATE_GENERATION_CONTRACT_FAILED"
            alternative_replay_context["message"] = generation_message

    strategy_mutation_context = _build_strategy_mutation_context_for_public_review(
        root=root,
        session_id=session_id,
        scorecard=scorecard,
        diagnostic=diagnostic,
        history=history,
        alternative_replay_context=alternative_replay_context,
    )

    discovery_path = (
        paper_candidate_generation_discovery_runtime_path(root, session_id)
        if candidate_discovery_runtime is not None
        else None
    )
    fields = _candidate_generation_public_review_fields(
        discovery_context=discovery_context,
        alternative_replay_context=alternative_replay_context,
        candidate_discovery_runtime_path=discovery_path,
        root=root,
        strategy_mutation_context=strategy_mutation_context,
    )
    return candidate_generation_report, fields, candidate_discovery_runtime


def _paper_scope_continuity_focus_from_history(
    root: Path,
    session_id: str,
    *,
    persist_fresh_history: bool = False,
) -> dict[str, Any] | None:
    try:
        history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
        history_result = validate_upbit_paper_runtime_sample_history_sources(root=root, history=history)
    except Exception:  # pragma: no cover - runtime artifact discovery must fail closed.
        return None
    if _result_status(history_result) != "PASS":
        return None
    active = history.get("active_candidate_scope")
    if isinstance(active, dict) and _paper_scope_focus_has_live_private_drift(active):
        return None
    if persist_fresh_history:
        write_upbit_paper_runtime_sample_history(root=root, history=history)
    if not isinstance(active, dict):
        return None
    sample_deficit = _int_value(active.get("sample_deficit"), 0)
    if sample_deficit <= 0:
        return None
    candidate_id = str(active.get("candidate_id") or "")
    symbol = str(active.get("symbol") or "")
    strategy_id = str(active.get("strategy_id") or "")
    parameter_hash = str(active.get("parameter_hash") or "").upper()
    if not candidate_id or not symbol.startswith("KRW-") or not strategy_id or len(parameter_hash) != 64:
        return None
    return {
        "source": "PAPER_RUNTIME_SAMPLE_HISTORY_ACTIVE_CANDIDATE_SCOPE",
        "candidate_id": candidate_id,
        "symbol": symbol,
        "strategy_id": strategy_id,
        "parameter_hash": parameter_hash,
        "sample_count": _int_value(active.get("sample_count"), 0),
        "sample_deficit": sample_deficit,
        "scope_progress_status": str(active.get("scope_progress_status") or "COLLECT_PAPER_SCOPE_SAMPLES"),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _paper_scope_focus_has_live_private_drift(focus: dict[str, Any]) -> bool:
    if any(focus.get(flag) is True for flag in PAPER_SCOPE_FOCUS_DRIFT_FLAGS):
        return True
    spec = focus.get("mutated_paper_candidate_spec")
    if isinstance(spec, dict) and any(spec.get(flag) is True for flag in PAPER_SCOPE_FOCUS_DRIFT_FLAGS):
        return True
    return False


def _paper_scope_focus_from_trade_intent_inputs(intent_inputs: Any) -> dict[str, Any] | None:
    if intent_inputs is None:
        return None
    focus = intent_inputs.get("paper_scope_focus") if isinstance(intent_inputs, dict) else getattr(
        intent_inputs,
        "paper_scope_focus",
        None,
    )
    if not isinstance(focus, dict):
        return None
    if _paper_scope_focus_has_live_private_drift(focus):
        return None
    candidate_id = str(focus.get("candidate_id") or "")
    symbol = str(focus.get("symbol") or "").upper()
    strategy_id = str(focus.get("strategy_id") or "")
    parameter_hash = str(focus.get("parameter_hash") or "").upper()
    sample_deficit = _int_value(focus.get("sample_deficit"), 0)
    if not candidate_id or not symbol.startswith("KRW-") or not strategy_id or len(parameter_hash) != 64:
        return None
    if sample_deficit <= 0:
        return None
    normalized = dict(focus)
    normalized.update(
        {
            "source": str(focus.get("source") or "CANDIDATE_GENERATION_PUBLIC_REPLAY_REHYDRATION"),
            "candidate_id": candidate_id,
            "symbol": symbol,
            "strategy_id": strategy_id,
            "parameter_hash": parameter_hash,
            "sample_count": _int_value(focus.get("sample_count"), 0),
            "sample_deficit": sample_deficit,
            "scope_progress_status": str(focus.get("scope_progress_status") or "COLLECT_PAPER_SCOPE_SAMPLES"),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    return normalized


def _paper_scope_focus_identity(focus: dict[str, Any] | None) -> tuple[str, str, str, str] | None:
    if not isinstance(focus, dict):
        return None
    candidate_id = str(focus.get("candidate_id") or "")
    symbol = str(focus.get("symbol") or "").upper()
    strategy_id = str(focus.get("strategy_id") or "")
    parameter_hash = str(focus.get("parameter_hash") or "").upper()
    if not candidate_id or not symbol.startswith("KRW-") or not strategy_id or len(parameter_hash) != 64:
        return None
    return candidate_id, symbol, strategy_id, parameter_hash


def _select_paper_scope_focus_for_next_cycle(
    *,
    history_focus: dict[str, Any] | None,
    provider_focus: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, str]:
    if history_focus is not None and _paper_scope_focus_has_live_private_drift(history_focus):
        history_focus = None
    if provider_focus is not None and _paper_scope_focus_has_live_private_drift(provider_focus):
        provider_focus = None

    history_identity = _paper_scope_focus_identity(history_focus)
    provider_identity = _paper_scope_focus_identity(provider_focus)
    if history_identity is None:
        if provider_identity is None:
            return None, "NO_SAFE_PAPER_SCOPE_FOCUS"
        return provider_focus, "PROVIDER_SCOPE_SELECTED"
    if provider_identity is None:
        return history_focus, "HISTORY_SCOPE_CONTINUITY_SELECTED"
    if history_identity == provider_identity:
        merged_focus = dict(provider_focus or {})
        merged_focus.update(
            {
                "source": "PAPER_RUNTIME_SAMPLE_HISTORY_CONTINUITY_WITH_PROVIDER_DETAILS",
                "candidate_id": history_focus["candidate_id"],
                "symbol": history_focus["symbol"],
                "strategy_id": history_focus["strategy_id"],
                "parameter_hash": history_focus["parameter_hash"],
                "sample_count": _int_value(history_focus.get("sample_count"), 0),
                "sample_deficit": _int_value(history_focus.get("sample_deficit"), 0),
                "scope_progress_status": str(
                    history_focus.get("scope_progress_status") or "COLLECT_PAPER_SCOPE_SAMPLES"
                ),
                "provider_focus_source": provider_focus.get("source"),
                "history_focus_source": history_focus.get("source"),
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
        return merged_focus, "HISTORY_SCOPE_CONTINUITY_MERGED_PROVIDER_DETAILS"
    if _int_value(history_focus.get("sample_deficit"), 0) > 0 and _int_value(history_focus.get("sample_count"), 0) > 0:
        selected = dict(history_focus)
        selected["suppressed_provider_focus_candidate_id"] = provider_focus.get("candidate_id")
        selected["suppressed_provider_focus_source"] = provider_focus.get("source")
        return selected, "HISTORY_SCOPE_CONTINUITY_SUPPRESSED_PROVIDER_SWITCH"
    return provider_focus, "PROVIDER_SCOPE_SELECTED"


def _candidate_scorecard_snapshot_fields(
    root: Path,
    session_id: str,
    scorecard: dict[str, Any] | None,
    scorecard_status: str,
) -> dict[str, Any]:
    candidate_id = None
    if isinstance(scorecard, dict) and scorecard.get("candidate_id"):
        candidate_id = str(scorecard.get("candidate_id"))
    snapshot_path = paper_candidate_scorecard_snapshot_path(root, session_id, candidate_id)
    snapshot = _read_json(snapshot_path) if candidate_id else None
    snapshot_errors = _candidate_scorecard_contract_errors(snapshot) if isinstance(snapshot, dict) else []

    if not candidate_id or not isinstance(snapshot, dict):
        snapshot_status = "NOT_LOADED"
        snapshot_blocker = "SCORECARD_SNAPSHOT_MISSING" if scorecard_status == "PASS" else None
    elif snapshot_errors:
        snapshot_status = "FAIL"
        snapshot_blocker = "SCORECARD_SNAPSHOT_INVALID"
    elif snapshot.get("candidate_id") != candidate_id:
        snapshot_status = "FAIL"
        snapshot_blocker = "SCORECARD_SNAPSHOT_CANDIDATE_MISMATCH"
    elif isinstance(scorecard, dict) and snapshot.get("scorecard_id") != scorecard.get("scorecard_id"):
        snapshot_status = "FAIL"
        snapshot_blocker = "SCORECARD_SNAPSHOT_ID_MISMATCH"
    elif isinstance(scorecard, dict) and snapshot.get("source_runtime_cycle_hash") != scorecard.get(
        "source_runtime_cycle_hash"
    ):
        snapshot_status = "FAIL"
        snapshot_blocker = "SCORECARD_SNAPSHOT_SOURCE_MISMATCH"
    else:
        snapshot_status = "PASS"
        snapshot_blocker = None

    return {
        "candidate_scorecard_candidate_id": candidate_id,
        "candidate_scorecard_snapshot_path": str(snapshot_path),
        "candidate_scorecard_snapshot_status": snapshot_status,
        "candidate_scorecard_snapshot_blocker_code": snapshot_blocker,
    }


def _profitability_evidence_refresh_fields(root: Path, session_id: str) -> dict[str, Any]:
    history_path = paper_runtime_sample_history_path(root, session_id)
    scorecard_path = paper_candidate_scorecard_path(root, session_id)
    overfit_path = paper_overfit_diagnostic_path(root, session_id)
    evidence_path = paper_shadow_evidence_accumulation_path(root, session_id)

    companion_history = _read_json(history_path)
    scorecard = _read_json(scorecard_path)
    overfit = _read_json(overfit_path)
    evidence = _read_json(evidence_path)

    source_history: dict[str, Any] | None = None
    source_history_status = "NOT_LOADED"
    source_history_blocker: str | None = "RUNTIME_SAMPLE_HISTORY_SOURCE_BUILD_MISSING"
    source_history_message = "Runtime sample history has not been built from source cycle artifacts."
    try:
        candidate_source_history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
        source_history_result = validate_upbit_paper_runtime_sample_history_sources(
            root=root,
            history=candidate_source_history,
        )
        source_history_status = _result_status(source_history_result)
        source_history_blocker = _result_blocker_code(source_history_result)
        source_history_message = str(getattr(source_history_result, "message", "") or "")
        if source_history_status == "PASS":
            source_history = candidate_source_history
    except Exception as exc:  # pragma: no cover - runtime artifact discovery must fail closed.
        source_history_status = "BLOCKED"
        source_history_blocker = "RUNTIME_SAMPLE_HISTORY_SOURCE_BUILD_FAILED"
        source_history_message = str(exc)

    companion_generated_at = None
    companion_accepted_count = 0
    companion_active_candidate_id = None
    companion_active_sample_count = 0
    companion_history_hash = None
    companion_issues: list[str] = []
    if isinstance(companion_history, dict):
        companion_result = validate_upbit_paper_runtime_sample_history_sources(root=root, history=companion_history)
        companion_status = _result_status(companion_result)
        companion_blocker = _result_blocker_code(companion_result)
        companion_generated_at = companion_history.get("generated_at_utc")
        companion_accepted_count = int(companion_history.get("accepted_cycle_sample_count") or 0)
        companion_active = companion_history.get("active_candidate_scope")
        companion_active_candidate_id = (
            str(companion_active.get("candidate_id"))
            if isinstance(companion_active, dict) and companion_active.get("candidate_id")
            else None
        )
        companion_active_sample_count = int(companion_history.get("active_candidate_scope_sample_count") or 0)
        companion_history_hash = companion_history.get("history_hash")
        if companion_status != "PASS":
            companion_issues.append(f"COMPANION_{companion_status}:{companion_blocker or 'UNKNOWN'}")
    else:
        companion_status = "NOT_LOADED"
        companion_blocker = "RUNTIME_SAMPLE_HISTORY_COMPANION_MISSING"
        companion_issues.append("COMPANION_NOT_LOADED")

    history = source_history if isinstance(source_history, dict) else companion_history
    consistency_issues = list(companion_issues)
    source_identity = _runtime_sample_history_source_identity(source_history)
    companion_identity = _runtime_sample_history_source_identity(companion_history)
    source_identity_mismatch = source_identity != companion_identity
    if isinstance(source_history, dict) and isinstance(companion_history, dict) and source_identity_mismatch:
        if companion_history_hash != source_history.get("history_hash"):
            consistency_issues.append("COMPANION_HISTORY_HASH_MISMATCH_SOURCE_REFRESH_USED")
        if companion_accepted_count != int(source_history.get("accepted_cycle_sample_count") or 0):
            consistency_issues.append("COMPANION_ACCEPTED_SAMPLE_COUNT_MISMATCH_SOURCE_REFRESH_USED")
        source_active = source_history.get("active_candidate_scope")
        source_active_candidate_id = (
            str(source_active.get("candidate_id"))
            if isinstance(source_active, dict) and source_active.get("candidate_id")
            else None
        )
        if companion_active_candidate_id != source_active_candidate_id:
            consistency_issues.append("COMPANION_ACTIVE_CANDIDATE_MISMATCH_SOURCE_REFRESH_USED")
        if companion_active_sample_count != int(source_history.get("active_candidate_scope_sample_count") or 0):
            consistency_issues.append("COMPANION_ACTIVE_SAMPLE_COUNT_MISMATCH_SOURCE_REFRESH_USED")

    materialization_fields = _materialize_source_runtime_sample_history(
        root=root,
        history_path=history_path,
        source_history=source_history,
        companion_history=companion_history,
        companion_status=companion_status,
    )
    materialization_status = str(
        materialization_fields.get("runtime_sample_history_materialization_status") or "NOT_RUN"
    )
    materialization_blocker = materialization_fields.get("runtime_sample_history_materialization_blocker_code")
    if materialization_status == "BLOCKED":
        consistency_issues.append(str(materialization_blocker or "RUNTIME_SAMPLE_HISTORY_MATERIALIZATION_BLOCKED"))

    if isinstance(source_history, dict):
        history_status = "PASS"
        history_blocker = None
        history_effective_source = "RUNTIME_SOURCE_DERIVED_SAMPLE_HISTORY"
        consistency_status = "BLOCKED" if materialization_status == "BLOCKED" else "PASS"
        consistency_blocker = materialization_blocker if materialization_status == "BLOCKED" else None
    elif isinstance(companion_history, dict):
        history_result = validate_upbit_paper_runtime_sample_history_sources(root=root, history=companion_history)
        history_status = _result_status(history_result)
        history_blocker = _result_blocker_code(history_result)
        history_effective_source = "COMPANION_SAMPLE_HISTORY_ARTIFACT"
        consistency_status = "BLOCKED" if source_history_status not in {"NOT_LOADED", "PASS"} else companion_status
        consistency_blocker = source_history_blocker or companion_blocker
    else:
        history_status = "NOT_LOADED"
        history_blocker = "RUNTIME_SAMPLE_HISTORY_MISSING"
        history_effective_source = "NOT_LOADED"
        consistency_status = "NOT_LOADED"
        consistency_blocker = history_blocker

    scorecard_errors = _candidate_scorecard_contract_errors(scorecard) if isinstance(scorecard, dict) else []
    if not isinstance(scorecard, dict):
        scorecard_status = "NOT_LOADED"
    elif scorecard_errors:
        scorecard_status = "FAIL"
    else:
        scorecard_status = "PASS"
    scorecard_snapshot_fields = _candidate_scorecard_snapshot_fields(
        root=root,
        session_id=session_id,
        scorecard=scorecard if isinstance(scorecard, dict) else None,
        scorecard_status=scorecard_status,
    )

    overfit_errors = _overfit_diagnostic_contract_errors(overfit) if isinstance(overfit, dict) else []
    if not isinstance(overfit, dict):
        overfit_contract_status = "NOT_LOADED"
    elif overfit_errors:
        overfit_contract_status = "FAIL"
    else:
        overfit_contract_status = "PASS"

    if isinstance(evidence, dict):
        evidence_result = validate_paper_shadow_evidence_accumulation_report(evidence)
        evidence_status = _result_status(evidence_result)
        evidence_blocker = _result_blocker_code(evidence_result)
    else:
        evidence_status = "BLOCKED"
        evidence_blocker = "PAPER_SHADOW_EVIDENCE_MISSING"

    blocker = next(
        (
            item
            for item in (
                history_blocker if history_status not in {"PASS"} else None,
                materialization_blocker if materialization_status == "BLOCKED" else None,
                "SCORECARD_SCHEMA_INVALID" if scorecard_status == "FAIL" else None,
                scorecard_snapshot_fields.get("candidate_scorecard_snapshot_blocker_code"),
                "SCHEMA_IDENTITY_MISMATCH" if overfit_contract_status == "FAIL" else None,
                evidence_blocker if evidence_status in {"FAIL"} or evidence_blocker in NON_LIVE_PROFITABILITY_REFRESH_CRITICAL_BLOCKERS else None,
            )
            if item
        ),
        None,
    )
    if blocker:
        refresh_status = NON_LIVE_PROFITABILITY_REFRESH_BLOCKED
    elif evidence_status == "PASS":
        refresh_status = NON_LIVE_PROFITABILITY_REFRESH_PASS
    elif (
        history_status == "PASS"
        and scorecard_status in {"PASS", "NOT_LOADED"}
        and overfit_contract_status in {"PASS", "NOT_LOADED"}
        and evidence_status == "BLOCKED"
    ):
        refresh_status = NON_LIVE_PROFITABILITY_REFRESH_COLLECTING
        blocker = evidence_blocker
    elif any(isinstance(item, dict) for item in (history, scorecard, overfit, evidence)):
        refresh_status = NON_LIVE_PROFITABILITY_REFRESH_BLOCKED
        blocker = blocker or evidence_blocker or "NON_LIVE_PROFITABILITY_EVIDENCE_INCOMPLETE"
    else:
        refresh_status = NON_LIVE_PROFITABILITY_REFRESH_NOT_RUN

    paper_scope_fields = _paper_scope_progress_fields(
        history=history if isinstance(history, dict) else None,
        evidence=evidence if isinstance(evidence, dict) else None,
    )
    strategy_mutation_fields = _strategy_mutation_compiler_artifact_fields(
        root=root,
        session_id=session_id,
        active_candidate_id=paper_scope_fields.get("paper_scope_candidate_id"),
    )

    return {
        "profitability_evidence_refresh_status": refresh_status,
        "profitability_evidence_primary_blocker_code": blocker,
        "runtime_sample_history_path": str(history_path),
        "runtime_sample_history_status": history_status,
        "runtime_sample_history_effective_source": history_effective_source,
        "runtime_sample_history_source_status": source_history_status,
        "runtime_sample_history_source_blocker_code": source_history_blocker,
        "runtime_sample_history_source_message": source_history_message,
        "runtime_sample_history_source_consistency_status": consistency_status,
        "runtime_sample_history_source_consistency_issues": sorted(set(consistency_issues)),
        "runtime_sample_history_source_consistency_blocker_code": consistency_blocker,
        **materialization_fields,
        "runtime_sample_history_companion_path": str(history_path),
        "runtime_sample_history_companion_status": companion_status,
        "runtime_sample_history_companion_blocker_code": companion_blocker,
        "runtime_sample_history_companion_generated_at_utc": companion_generated_at,
        "runtime_sample_history_companion_accepted_cycle_sample_count": companion_accepted_count,
        "runtime_sample_history_companion_active_candidate_id": companion_active_candidate_id,
        "runtime_sample_history_companion_active_sample_count": companion_active_sample_count,
        "runtime_sample_count": int(history.get("accepted_cycle_sample_count") or 0) if isinstance(history, dict) else 0,
        "runtime_sample_invalid_source_count": int(history.get("invalid_source_count") or 0) if isinstance(history, dict) else 0,
        **paper_scope_fields,
        **strategy_mutation_fields,
        "candidate_scorecard_path": str(scorecard_path),
        "candidate_scorecard_status": scorecard_status,
        "candidate_scorecard_ranking_eligible": (
            bool(scorecard.get("ranking_eligible")) if isinstance(scorecard, dict) else False
        ),
        "candidate_scorecard_primary_blocker_code": (
            str(scorecard.get("primary_blocker_code") or "")
            if isinstance(scorecard, dict) and scorecard.get("primary_blocker_code")
            else None
        ),
        **scorecard_snapshot_fields,
        "overfit_diagnostic_path": str(overfit_path),
        "overfit_diagnostic_contract_status": overfit_contract_status,
        "overfit_diagnostic_status": str(overfit.get("diagnostic_status") or "NOT_LOADED") if isinstance(overfit, dict) else "NOT_LOADED",
        "overfit_diagnostic_sample_count": int(overfit.get("sample_count") or 0) if isinstance(overfit, dict) else 0,
        "overfit_preliminary_robustness_status": (
            str(overfit.get("preliminary_robustness_status") or "INSUFFICIENT_PRELIMINARY_SAMPLE")
            if isinstance(overfit, dict)
            else "INSUFFICIENT_PRELIMINARY_SAMPLE"
        ),
        "overfit_preliminary_oos_status": (
            str(overfit.get("preliminary_oos_status") or "UNTESTED") if isinstance(overfit, dict) else "UNTESTED"
        ),
        "overfit_preliminary_walk_forward_status": (
            str(overfit.get("preliminary_walk_forward_status") or "UNTESTED")
            if isinstance(overfit, dict)
            else "UNTESTED"
        ),
        "overfit_preliminary_bootstrap_status": (
            str(overfit.get("preliminary_bootstrap_status") or "UNTESTED") if isinstance(overfit, dict) else "UNTESTED"
        ),
        "overfit_preliminary_oos_net_ev_after_cost_bps": (
            overfit.get("preliminary_oos_net_ev_after_cost_bps") if isinstance(overfit, dict) else None
        ),
        "overfit_preliminary_bootstrap_confidence_lower_bps": (
            overfit.get("preliminary_bootstrap_confidence_lower_bps") if isinstance(overfit, dict) else None
        ),
        "overfit_preliminary_primary_blocker_code": (
            str(overfit.get("preliminary_primary_blocker_code") or "PRELIMINARY_SAMPLE_INSUFFICIENT")
            if isinstance(overfit, dict)
            else "PRELIMINARY_SAMPLE_INSUFFICIENT"
        ),
        "paper_shadow_evidence_accumulation_path": str(evidence_path),
        "paper_shadow_evidence_validation_status": evidence_status,
        "paper_shadow_evidence_blocker_code": evidence_blocker,
        "paper_shadow_evidence_actionability_status": (
            str(evidence.get("evidence_actionability_status") or "NOT_LOADED")
            if isinstance(evidence, dict)
            else "NOT_LOADED"
        ),
        "paper_shadow_evidence_paper_sample_count": (
            int(evidence.get("paper_sample_count") or 0) if isinstance(evidence, dict) else 0
        ),
        "paper_shadow_evidence_shadow_sample_count": (
            int(evidence.get("shadow_sample_count") or 0) if isinstance(evidence, dict) else 0
        ),
    }


def refresh_non_live_profitability_evidence_from_runtime(root: Path, session_id: str) -> dict[str, Any]:
    root = Path(root).resolve()
    history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
    history_result = validate_upbit_paper_runtime_sample_history_sources(root=root, history=history)
    if history_result.status != "PASS":
        history_path = write_upbit_paper_runtime_sample_history(root=root, history=history)
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": history_result.blocker_code or "RUNTIME_SAMPLE_HISTORY_INVALID",
            "message": history_result.message,
            "runtime_sample_history_path": _relative_runtime_path(history_path, root),
            "runtime_sample_history_status": history_result.status,
            "runtime_sample_status": history.get("runtime_sample_status"),
            "accepted_cycle_sample_count": history.get("accepted_cycle_sample_count"),
            "invalid_source_count": history.get("invalid_source_count"),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    if not history.get("samples"):
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": "ACTUAL_PAPER_RUNTIME_SAMPLE_MISSING",
            "message": "No validated PAPER runtime sample exists after the completed runner cycle.",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    active_scope = history.get("active_candidate_scope")
    selected_sample = _select_profitability_evidence_sample(
        history["samples"],
        active_scope=active_scope if isinstance(active_scope, dict) else None,
    )
    if not isinstance(selected_sample, dict):
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": "ACTUAL_PAPER_RUNTIME_SAMPLE_MISSING",
            "message": "No usable PAPER runtime sample exists for profitability evidence refresh.",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    runtime_path = root / str(selected_sample["source_runtime_cycle_path"])
    runtime = _read_json(runtime_path)
    if not isinstance(runtime, dict):
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": "ACTUAL_PAPER_RUNTIME_SAMPLE_MISSING",
            "message": "Selected PAPER runtime cycle sample cannot be loaded.",
            "source_runtime_cycle_path": str(selected_sample.get("source_runtime_cycle_path")),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    runtime_result = validate_upbit_paper_runtime_cycle_report(runtime)
    if runtime_result.status != "PASS":
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": runtime_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
            "message": runtime_result.message,
            "source_runtime_cycle_path": str(selected_sample.get("source_runtime_cycle_path")),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    if runtime.get("cycle_hash") != selected_sample.get("source_runtime_cycle_hash"):
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": "RECONCILIATION_REQUIRED",
            "message": "Selected PAPER runtime sample hash does not match its runtime cycle artifact.",
            "source_runtime_cycle_path": str(selected_sample.get("source_runtime_cycle_path")),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    scorecard_sample_candidate_id = _scorecard_candidate_id_from_runtime_sample(selected_sample)
    base_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
        runtime,
        candidate_id=scorecard_sample_candidate_id,
        allow_non_entry_review_candidate=scorecard_sample_candidate_id is not None,
    )
    diagnostic = overfit_diagnostic_from_upbit_paper_runtime(
        candidate_scorecard=base_scorecard,
        runtime_sample_history=history,
        root=root,
    )
    diagnostic_errors = _overfit_diagnostic_contract_errors(diagnostic)
    if diagnostic_errors:
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": "SCHEMA_IDENTITY_MISMATCH",
            "message": "Overfit diagnostic failed contract validation.",
            "diagnostic_errors": diagnostic_errors,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    robustness_statuses, robustness_source_ids = robustness_inputs_from_overfit_diagnostic(diagnostic)
    performance_statuses, performance_metrics, performance_source_ids = performance_inputs_from_runtime_sample_history(
        candidate_scorecard=base_scorecard,
        runtime_sample_history=history,
        root=root,
    )
    scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
        runtime,
        candidate_id=scorecard_sample_candidate_id,
        allow_non_entry_review_candidate=scorecard_sample_candidate_id is not None,
        robustness_statuses=robustness_statuses,
        robustness_source_evidence_ids=robustness_source_ids,
        performance_statuses=performance_statuses,
        performance_metrics=performance_metrics,
        performance_source_evidence_ids=performance_source_ids,
    )
    scorecard_errors = _candidate_scorecard_contract_errors(scorecard)
    if scorecard_errors:
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": "SCORECARD_SCHEMA_INVALID",
            "message": "Candidate scorecard failed contract validation.",
            "scorecard_errors": scorecard_errors,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    candidate_generation_report = candidate_generation_report_from_upbit_paper_runtime_cycle(
        runtime,
        candidate_scorecard=scorecard,
    )
    generation_status, generation_message, generation_blocker = validate_candidate_generation_report(
        candidate_generation_report,
        candidate_scorecard=scorecard,
    )
    if generation_status != "PASS":
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": generation_blocker or "CANDIDATE_GENERATION_CONTRACT_FAILED",
            "message": generation_message,
            "candidate_generation_status": candidate_generation_report.get("generation_status"),
            "candidate_generation_primary_blocker_code": candidate_generation_report.get("primary_blocker_code"),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    candidate_generation_report, public_review_fields, candidate_discovery_runtime = (
        _review_public_alternatives_for_candidate_generation(
            root=root,
            session_id=session_id,
            runtime=runtime,
            scorecard=scorecard,
            diagnostic=diagnostic,
            history=history,
            candidate_generation_report=candidate_generation_report,
        )
    )

    history_path = write_upbit_paper_runtime_sample_history(root=root, history=history)
    diagnostic_path = write_overfit_diagnostic_report(root=root, report=diagnostic)
    scorecard_path = write_upbit_paper_candidate_scorecard(root=root, scorecard=scorecard)
    candidate_generation_path = write_upbit_paper_candidate_generation_report(
        root=root,
        report=candidate_generation_report,
    )
    candidate_discovery_runtime_path = None
    if candidate_discovery_runtime is not None:
        candidate_discovery_runtime_path = paper_candidate_generation_discovery_runtime_path(root, session_id)
        durable_atomic_write_json(candidate_discovery_runtime_path, candidate_discovery_runtime)
        public_review_fields = dict(public_review_fields)
        public_review_fields["candidate_discovery_runtime_cycle_path"] = _relative_runtime_path(
            candidate_discovery_runtime_path,
            root,
        )
    candidate_generation_fields = {
        "candidate_generation_report_path": _relative_runtime_path(candidate_generation_path, root),
        "candidate_generation_status": candidate_generation_report.get("generation_status"),
        "candidate_generation_primary_blocker_code": candidate_generation_report.get("primary_blocker_code"),
        "candidate_generation_alternative_candidate_count": candidate_generation_report.get(
            "alternative_candidate_count"
        ),
        "candidate_generation_best_alternative_candidate_id": candidate_generation_report.get(
            "best_alternative_candidate_id"
        ),
        "candidate_generation_best_alternative_symbol": candidate_generation_report.get("best_alternative_symbol"),
        "candidate_generation_next_action": candidate_generation_report.get("next_action"),
        **public_review_fields,
    }
    scorecard_candidate_id = str(scorecard.get("candidate_id") or "")
    scorecard_snapshot_path = paper_candidate_scorecard_snapshot_path(root, session_id, scorecard_candidate_id)

    shadow_harness = _read_json(shadow_runtime_harness_path(root, session_id))
    shadow_persistent_runtime = _read_json(shadow_persistent_runtime_path(root, session_id))
    if not isinstance(shadow_harness, dict) or not isinstance(shadow_persistent_runtime, dict):
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": "PAPER_SHADOW_RUNTIME_ARTIFACT_MISSING",
            "message": "PAPER scorecard was written, but paired SHADOW runtime artifacts are missing.",
            "runtime_sample_history_path": _relative_runtime_path(history_path, root),
            "overfit_diagnostic_path": _relative_runtime_path(diagnostic_path, root),
            "candidate_scorecard_path": _relative_runtime_path(scorecard_path, root),
            "candidate_scorecard_candidate_id": scorecard_candidate_id,
            "candidate_scorecard_snapshot_path": _relative_runtime_path(scorecard_snapshot_path, root),
            "candidate_scorecard_snapshot_status": "PASS",
            **candidate_generation_fields,
            **_paper_scope_progress_fields(history=history, evidence=None),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    orchestration = build_shadow_observation_runtime_orchestration_report(
        orchestration_id=session_id,
        persistent_runtime_report=shadow_persistent_runtime,
        actual_runtime_harness_report=shadow_harness,
    )
    orchestration_result = validate_shadow_observation_runtime_orchestration_report(orchestration)
    if orchestration_result.status != "PASS":
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": orchestration_result.blocker_code or "PAPER_SHADOW_RUNTIME_REFRESH_FAILED",
            "message": orchestration_result.message,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    shadow_sample_history = _read_json(shadow_runtime_sample_history_path(root, session_id))
    evidence = build_paper_shadow_evidence_accumulation_from_runtime_artifacts(
        evidence_report_id=f"paper-shadow-runtime-evidence:{scorecard.get('source_runtime_cycle_id', 'current')}",
        candidate_scorecard=scorecard,
        overfit_diagnostic_report=diagnostic,
        paper_sample_history=history,
        shadow_runtime_harness_report=shadow_harness,
        shadow_runtime_sample_history=shadow_sample_history,
        paper_session_id=session_id,
        shadow_session_id=f"{session_id}_shadow",
    )
    evidence_result = validate_paper_shadow_evidence_accumulation_report(evidence)
    evidence_status = _result_status(evidence_result)
    evidence_blocker = _result_blocker_code(evidence_result)
    if evidence_status == "FAIL" or evidence_blocker in NON_LIVE_PROFITABILITY_REFRESH_CRITICAL_BLOCKERS:
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": evidence_blocker or "PAPER_SHADOW_EVIDENCE_INVALID",
            "message": getattr(evidence_result, "message", "PAPER/SHADOW evidence validation failed."),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    evidence_path = paper_shadow_evidence_accumulation_path(root, session_id)
    existing_evidence = _read_json(evidence_path)
    existing_evidence_result = (
        validate_paper_shadow_evidence_accumulation_report(existing_evidence)
        if isinstance(existing_evidence, dict)
        else None
    )
    existing_binding = _read_json(paper_shadow_harness_binding_path(root, session_id))
    existing_binding_result = (
        validate_paper_shadow_harness_binding_report(existing_binding) if isinstance(existing_binding, dict) else None
    )
    refresh_decision = choose_paper_shadow_evidence_refresh_report(
        existing_report=existing_evidence,
        existing_validation_result=existing_evidence_result,
        existing_binding_report=existing_binding,
        existing_binding_validation_result=existing_binding_result,
        latest_report=evidence,
        latest_validation_result=evidence_result,
    )
    selected_evidence = refresh_decision.selected_report
    selected_evidence_result = validate_paper_shadow_evidence_accumulation_report(selected_evidence)
    if refresh_decision.selected_source == "existing":
        binding = existing_binding
        binding_result = existing_binding_result
    else:
        binding = build_paper_shadow_harness_binding_report(
            binding_report_id=session_id,
            shadow_runtime_harness_report=shadow_harness,
            paper_shadow_evidence_accumulation_report=selected_evidence,
        )
        binding_result = validate_paper_shadow_harness_binding_report(binding)
    binding_status = _result_status(binding_result)
    binding_blocker = _result_blocker_code(binding_result)
    if binding_status not in {"PASS", "BLOCKED"} or binding_blocker in NON_LIVE_PROFITABILITY_REFRESH_CRITICAL_BLOCKERS:
        return {
            "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
            "blocker_code": binding_blocker or "PAPER_SHADOW_HARNESS_BINDING_INVALID",
            "message": getattr(binding_result, "message", "PAPER/SHADOW harness binding validation failed."),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    orchestration_path = shadow_runtime_orchestration_path(root, session_id)
    durable_atomic_write_json(orchestration_path, orchestration)
    if refresh_decision.selected_source != "existing":
        durable_atomic_write_json(evidence_path, selected_evidence)
        durable_atomic_write_json(paper_shadow_harness_binding_path(root, session_id), binding)

    selected_status = _result_status(selected_evidence_result)
    selected_blocker = _result_blocker_code(selected_evidence_result)
    status = NON_LIVE_PROFITABILITY_REFRESH_PASS if selected_status == "PASS" else NON_LIVE_PROFITABILITY_REFRESH_COLLECTING
    return {
        "status": status,
        "blocker_code": selected_blocker,
        "message": "Non-live profitability and PAPER/SHADOW evidence refreshed from actual PAPER runner artifacts.",
        "runtime_sample_history_path": _relative_runtime_path(history_path, root),
        "overfit_diagnostic_path": _relative_runtime_path(diagnostic_path, root),
        "candidate_scorecard_path": _relative_runtime_path(scorecard_path, root),
        "candidate_scorecard_candidate_id": scorecard_candidate_id,
        "candidate_scorecard_snapshot_path": _relative_runtime_path(scorecard_snapshot_path, root),
        "candidate_scorecard_snapshot_status": "PASS",
        **candidate_generation_fields,
        "paper_shadow_evidence_path": _relative_runtime_path(evidence_path, root),
        "paper_shadow_binding_path": _relative_runtime_path(paper_shadow_harness_binding_path(root, session_id), root),
        "orchestration_path": _relative_runtime_path(orchestration_path, root),
        "evidence_refresh_action": refresh_decision.evidence_refresh_action,
        "evidence_refresh_reason_code": refresh_decision.evidence_refresh_reason_code,
        "evidence_refresh_selected_source": refresh_decision.selected_source,
        "runtime_sample_count": int(history.get("accepted_cycle_sample_count") or 0),
        **_paper_scope_progress_fields(history=history, evidence=selected_evidence),
        "candidate_scorecard_status": "PASS",
        "candidate_scorecard_ranking_eligible": bool(scorecard.get("ranking_eligible")),
        "overfit_diagnostic_status": str(diagnostic.get("diagnostic_status") or "NOT_LOADED"),
        "overfit_preliminary_robustness_status": str(
            diagnostic.get("preliminary_robustness_status") or "INSUFFICIENT_PRELIMINARY_SAMPLE"
        ),
        "overfit_preliminary_oos_status": str(diagnostic.get("preliminary_oos_status") or "UNTESTED"),
        "overfit_preliminary_walk_forward_status": str(
            diagnostic.get("preliminary_walk_forward_status") or "UNTESTED"
        ),
        "overfit_preliminary_bootstrap_status": str(diagnostic.get("preliminary_bootstrap_status") or "UNTESTED"),
        "overfit_preliminary_oos_net_ev_after_cost_bps": diagnostic.get(
            "preliminary_oos_net_ev_after_cost_bps"
        ),
        "overfit_preliminary_bootstrap_confidence_lower_bps": diagnostic.get(
            "preliminary_bootstrap_confidence_lower_bps"
        ),
        "overfit_preliminary_primary_blocker_code": str(
            diagnostic.get("preliminary_primary_blocker_code") or "PRELIMINARY_SAMPLE_INSUFFICIENT"
        ),
        "paper_shadow_evidence_validation_status": selected_status,
        "paper_shadow_evidence_actionability_status": str(
            selected_evidence.get("evidence_actionability_status") or "NOT_LOADED"
        ),
        "paper_sample_count": int(selected_evidence.get("paper_sample_count") or 0),
        "shadow_sample_count": int(selected_evidence.get("shadow_sample_count") or 0),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _append_log(root: Path, session_id: str, event: dict[str, Any]) -> None:
    path = runner_log_path(root, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")


def _pid_is_running(pid: int | None) -> bool:
    if not pid:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        still_active = 259
        handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, int(pid))
        if not handle:
            return False
        try:
            exit_code = wintypes.DWORD()
            if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _lock_is_stale(lock: dict[str, Any], now: datetime, stale_after_seconds: int) -> bool:
    pid = lock.get("pid")
    pid_int = pid if isinstance(pid, int) else None
    if pid_int is not None:
        return not _pid_is_running(pid_int)
    heartbeat_at = _parse_utc(lock.get("heartbeat_at")) or _parse_utc(lock.get("acquired_at"))
    if heartbeat_at is None:
        return True
    return (now - heartbeat_at).total_seconds() >= stale_after_seconds


def runner_lock_liveness_from_status_report(
    report: dict[str, Any] | None,
    *,
    now: datetime | None = None,
    fresh_after_seconds: float = 300.0,
) -> dict[str, Any]:
    generated_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    base: dict[str, Any] = {
        "runner_lock_loaded": False,
        "runner_lock_session_match": False,
        "runner_lock_fresh": False,
        "runner_lock_pid_alive": False,
        "runner_liveness_proven": False,
        "runner_lock_pid": None,
        "runner_lock_heartbeat_at_utc": None,
        "source_runner_lock_hash": None,
        "runner_liveness_blocker_code": "DATA_QUALITY_INSUFFICIENT",
        "runner_liveness_blocker_message": "PAPER runner lock is not loaded.",
    }
    if not isinstance(report, dict):
        return base
    if report.get("runner_status") != RUNNER_STATUS_RUNNING or report.get("running") is not True:
        base.update(
            {
                "runner_liveness_blocker_code": "DATA_QUALITY_INSUFFICIENT",
                "runner_liveness_blocker_message": "PAPER runner status does not claim a running process.",
            }
        )
        return base

    raw_lock_path = report.get("lock_path")
    if not isinstance(raw_lock_path, str) or not raw_lock_path.strip():
        base.update(
            {
                "runner_liveness_blocker_code": "LATENCY_TTL_EXPIRED",
                "runner_liveness_blocker_message": "PAPER runner status has no session lock path.",
            }
        )
        return base
    lock = _read_json(Path(raw_lock_path))
    if not isinstance(lock, dict):
        base.update(
            {
                "runner_liveness_blocker_code": "LATENCY_TTL_EXPIRED",
                "runner_liveness_blocker_message": "PAPER runner session lock is missing or unreadable.",
            }
        )
        return base

    pid = lock.get("pid")
    pid_int = pid if isinstance(pid, int) else None
    heartbeat_at = _parse_utc(lock.get("heartbeat_at")) or _parse_utc(lock.get("acquired_at"))
    heartbeat_text = (
        heartbeat_at.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if heartbeat_at is not None
        else None
    )
    session_match = bool(lock.get("session_id") == report.get("session_id"))
    schema_match = lock.get("schema_id") == UPBIT_PAPER_LONG_RUNNER_LOCK_SCHEMA_ID
    pid_alive = _pid_is_running(pid_int)
    lock_fresh = bool(
        heartbeat_at is not None and max(0.0, (generated_at - heartbeat_at).total_seconds()) <= fresh_after_seconds
    )
    base.update(
        {
            "runner_lock_loaded": True,
            "runner_lock_session_match": session_match,
            "runner_lock_fresh": lock_fresh,
            "runner_lock_pid_alive": pid_alive,
            "runner_lock_pid": pid_int,
            "runner_lock_heartbeat_at_utc": heartbeat_text,
            "source_runner_lock_hash": _json_hash(lock),
        }
    )
    if not schema_match:
        base.update(
            {
                "runner_liveness_blocker_code": "SCHEMA_IDENTITY_MISMATCH",
                "runner_liveness_blocker_message": "PAPER runner session lock schema is invalid.",
            }
        )
    elif not session_match:
        base.update(
            {
                "runner_liveness_blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
                "runner_liveness_blocker_message": "PAPER runner session lock is scoped to another session.",
            }
        )
    elif not pid_alive:
        base.update(
            {
                "runner_liveness_blocker_code": "LATENCY_TTL_EXPIRED",
                "runner_liveness_blocker_message": "PAPER runner status says RUNNING but the session lock owner PID is not alive.",
            }
        )
    elif not lock_fresh:
        base.update(
            {
                "runner_liveness_blocker_code": "LATENCY_TTL_EXPIRED",
                "runner_liveness_blocker_message": "PAPER runner session lock heartbeat is stale.",
            }
        )
    else:
        base.update(
            {
                "runner_liveness_proven": True,
                "runner_liveness_blocker_code": None,
                "runner_liveness_blocker_message": None,
            }
        )
    return base


@dataclass(frozen=True)
class RunnerLock:
    acquired: bool
    path: Path
    owner_token: str
    blocker_code: str | None = None
    blocker_message: str | None = None


def _write_lock_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, body)
    finally:
        os.close(fd)


def acquire_runner_lock(
    root: Path,
    session_id: str,
    *,
    stale_after_seconds: int = DEFAULT_LOCK_STALE_AFTER_SECONDS,
) -> RunnerLock:
    path = runner_lock_path(root, session_id)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    owner_token = f"{os.getpid()}-{int(time.time() * 1000)}"
    payload = {
        "schema_id": UPBIT_PAPER_LONG_RUNNER_LOCK_SCHEMA_ID,
        "owner_token": owner_token,
        "pid": os.getpid(),
        "session_id": session_id,
        "acquired_at": now.isoformat().replace("+00:00", "Z"),
        "heartbeat_at": now.isoformat().replace("+00:00", "Z"),
    }
    for _ in range(2):
        try:
            _write_lock_file(path, payload)
            return RunnerLock(acquired=True, path=path, owner_token=owner_token)
        except FileExistsError:
            existing = _read_json(path) or {}
            if _lock_is_stale(existing, now, stale_after_seconds):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
                continue
            return RunnerLock(
                acquired=False,
                path=path,
                owner_token=owner_token,
                blocker_code=LOCK_BLOCKER_CODE,
                blocker_message="Another UPBIT PAPER runner owns this session lock.",
            )
    return RunnerLock(
        acquired=False,
        path=path,
        owner_token=owner_token,
        blocker_code=LOCK_BLOCKER_CODE,
        blocker_message="Could not acquire UPBIT PAPER runner session lock.",
    )


def heartbeat_runner_lock(lock: RunnerLock, session_id: str) -> None:
    if not lock.acquired:
        return
    current = _read_json(lock.path)
    if not current or current.get("owner_token") != lock.owner_token:
        return
    current["heartbeat_at"] = utc_now()
    durable_atomic_write_json(lock.path, current)


def release_runner_lock(lock: RunnerLock) -> None:
    if not lock.acquired:
        return
    current = _read_json(lock.path)
    if current and current.get("owner_token") != lock.owner_token:
        return
    try:
        lock.path.unlink()
    except FileNotFoundError:
        pass


def _relative_runtime_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _archive_batches_root(root: Path, session_id: str) -> Path:
    return runner_dir(root, session_id) / "archive"


def _tree_stats(base: Path, *, exclude: tuple[Path, ...] = ()) -> dict[str, int]:
    count = 0
    total_bytes = 0
    resolved_exclude = tuple(path.resolve() for path in exclude if path.exists())
    if not base.exists():
        return {"artifact_count": 0, "artifact_bytes": 0}
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        resolved_path = path.resolve()
        if any(_is_relative_to(resolved_path, excluded) for excluded in resolved_exclude):
            continue
        count += 1
        try:
            total_bytes += path.stat().st_size
        except OSError:
            continue
    return {"artifact_count": count, "artifact_bytes": total_bytes}


def _runtime_tree_stats(root: Path, session_id: str, *, include_archive: bool = False) -> dict[str, int]:
    base = runner_runtime_base(root, session_id)
    exclude = () if include_archive else (_archive_batches_root(root, session_id),)
    stats = _tree_stats(base, exclude=exclude)
    return {"runtime_artifact_count": stats["artifact_count"], "runtime_artifact_bytes": stats["artifact_bytes"]}


def _archive_tree_stats(root: Path, session_id: str) -> dict[str, int]:
    stats = _tree_stats(_archive_batches_root(root, session_id))
    return {"archive_artifact_count": stats["artifact_count"], "archive_artifact_bytes": stats["artifact_bytes"]}


def _retention_group_patterns() -> dict[str, tuple[str, ...]]:
    return {
        "paper_runtime_cycles": (
            "paper_runtime/cycles/upbit-paper-runner-*.runtime_cycle.json",
            "paper_runtime/cycles/upbit-paper-runner-*.writer_report.json",
        ),
        "persistent_loop_reports": ("paper_runtime/upbit-paper-runner-*.persistent_loop_report.json",),
        "recovery_guard_reports": ("paper_runtime/upbit-paper-runner-*-recovery-guard.json", "paper_runtime/upbit-paper-runner-*-preflight-recovery-guard.json"),
        "ledger_rollups": ("ledger/upbit-paper-runner-*-ledger-rollup.paper_ledger_rollup_report.json",),
        "public_raw_candles": ("market_data/public/raw/upbit-paper-runner-*.raw_candles.json",),
        "public_canonical_events": ("market_data/public/canonical/upbit-paper-runner-*.canonical_events.jsonl",),
        "public_collection_reports": ("market_data/public/collection/upbit-paper-runner-*.collection_report.json", "market_data/public/collection/upbit-paper-runner-*.writer_report.json"),
    }


def _unique_retention_group_paths(runtime_base: Path, patterns: tuple[str, ...]) -> list[Path]:
    group_paths: list[Path] = []
    for pattern in patterns:
        group_paths.extend(path for path in runtime_base.glob(pattern) if path.is_file())
    return sorted(set(group_paths), key=lambda path: (path.stat().st_mtime_ns, path.name), reverse=True)


def _retention_group_limit(group: str, max_active_artifacts_per_group: int) -> int:
    return min(
        max_active_artifacts_per_group,
        DEFAULT_RETENTION_MAX_ACTIVE_ARTIFACTS_BY_GROUP.get(group, max_active_artifacts_per_group),
    )


def _retention_active_artifact_paths(root: Path, session_id: str) -> set[Path]:
    runtime_base = runner_runtime_base(root, session_id)
    paths: set[Path] = set()
    for patterns in _retention_group_patterns().values():
        paths.update(_unique_retention_group_paths(runtime_base, patterns))
    log_path = runner_log_path(root, session_id)
    if log_path.exists() and log_path.is_file():
        paths.add(log_path)
    return paths


def _managed_runtime_artifact_stats(root: Path, session_id: str) -> dict[str, int]:
    count = 0
    total_bytes = 0
    for path in _retention_active_artifact_paths(root, session_id):
        if not path.exists() or not path.is_file():
            continue
        count += 1
        try:
            total_bytes += path.stat().st_size
        except OSError:
            continue
    return {"runtime_artifact_count": count, "runtime_artifact_bytes": total_bytes}


def _latest_public_collection_protected_paths(*, root: Path, session_id: str) -> set[Path]:
    runtime_base = runner_runtime_base(root, session_id)
    public_base = runtime_base / "market_data" / "public"
    latest_path = public_base / "latest_collection_report.json"
    if not latest_path.exists() or not latest_path.is_file():
        return set()
    protected = {latest_path}
    latest = _read_json(latest_path)
    if not isinstance(latest, dict):
        return protected
    report_path = latest.get("report_path")
    if isinstance(report_path, str):
        candidate = root / report_path
        if candidate.exists() and _is_relative_to(candidate, runtime_base):
            protected.add(candidate)
            report = _read_json(candidate)
            if isinstance(report, dict):
                collector_id = str(report.get("collector_id") or "")
                if collector_id:
                    protected.update(
                        path
                        for path in (
                            public_base / "raw" / f"{collector_id}.raw_candles.json",
                            public_base / "canonical" / f"{collector_id}.canonical_events.jsonl",
                            public_base / "collection" / f"{collector_id}.collection_report.json",
                            public_base / "collection" / f"{collector_id}.writer_report.json",
                        )
                        if path.exists() and _is_relative_to(path, runtime_base)
                    )
    return protected


def _active_retention_group_counts(root: Path, session_id: str) -> dict[str, int]:
    runtime_base = runner_runtime_base(root, session_id)
    return {
        group: len(_unique_retention_group_paths(runtime_base, patterns))
        for group, patterns in _retention_group_patterns().items()
    }


def _safe_archive_relative_path(relative_path: str) -> str:
    return relative_path.replace("\\", "/").replace("/", "__").replace(":", "_")


def _archive_file(
    *,
    root: Path,
    session_id: str,
    source: Path,
    archive_dir: Path,
    group: str,
) -> dict[str, Any]:
    relative_source = _relative_runtime_path(source, root)
    source_size = source.stat().st_size
    source_hash = _sha256_file(source)
    destination = archive_dir / group / _safe_archive_relative_path(relative_source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = 1
    base_destination = destination
    while destination.exists():
        destination = base_destination.with_name(f"{base_destination.name}.{suffix}")
        suffix += 1
    shutil.move(str(source), str(destination))
    return {
        "source_path": relative_source,
        "archive_path": _relative_runtime_path(destination, root),
        "artifact_hash": source_hash,
        "artifact_bytes": source_size,
        "archive_write_method": RETENTION_ARCHIVE_WRITE_METHOD,
        "group": group,
        "session_id": session_id,
    }


def _rotate_runner_log(
    *,
    root: Path,
    session_id: str,
    archive_dir: Path,
    log_max_bytes: int,
) -> list[dict[str, Any]]:
    path = runner_log_path(root, session_id)
    if log_max_bytes <= 0 or not path.exists() or path.stat().st_size <= log_max_bytes:
        return []
    return [_archive_file(root=root, session_id=session_id, source=path, archive_dir=archive_dir, group="runner_logs")]


def _compact_archive_batch(*, root: Path, batch_dir: Path) -> dict[str, Any]:
    archive_root = batch_dir.parent
    if not _is_relative_to(batch_dir, archive_root) or batch_dir.resolve() == archive_root.resolve():
        raise ValueError("archive batch path must stay inside the archive root")
    batch_files = [path for path in batch_dir.rglob("*") if path.is_file()]
    source_bytes = sum(path.stat().st_size for path in batch_files)
    destination = batch_dir.with_suffix(".zip")
    suffix = 1
    base_destination = destination
    while destination.exists():
        destination = base_destination.with_name(f"{base_destination.stem}.{suffix}{base_destination.suffix}")
        suffix += 1
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in batch_files:
            archive.write(path, path.relative_to(batch_dir).as_posix())
    shutil.rmtree(batch_dir)
    return {
        "archive_batch_id": batch_dir.name,
        "compacted_archive_path": _relative_runtime_path(destination, root),
        "source_artifact_count": len(batch_files),
        "source_artifact_bytes": source_bytes,
        "compacted_archive_bytes": destination.stat().st_size,
        "archive_write_method": "ZIP_DEFLATED_THEN_REMOVE_BATCH_DIR",
    }


def _compact_old_archive_batches(
    *,
    root: Path,
    session_id: str,
    max_uncompacted_archive_batches: int,
) -> list[dict[str, Any]]:
    if max_uncompacted_archive_batches < 1:
        raise ValueError("max_uncompacted_archive_batches must be >= 1")
    archive_root = _archive_batches_root(root, session_id)
    if not archive_root.exists():
        return []
    batches = [
        path
        for path in archive_root.iterdir()
        if path.is_dir() and path.name.startswith("runner-retention-") and _is_relative_to(path, archive_root)
    ]
    batches.sort(key=lambda path: (path.stat().st_mtime_ns, path.name), reverse=True)
    compacted: list[dict[str, Any]] = []
    for batch in batches[max_uncompacted_archive_batches:]:
        compacted.append(_compact_archive_batch(root=root, batch_dir=batch))
    return compacted


def upbit_paper_long_runner_retention_manifest_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("manifest_hash", None)
    return _json_hash(payload)


def apply_runner_artifact_retention(
    *,
    root: Path,
    session_id: str,
    max_active_artifacts_per_group: int = DEFAULT_RETENTION_MAX_ACTIVE_ARTIFACTS_PER_GROUP,
    log_max_bytes: int = DEFAULT_RUNNER_LOG_MAX_BYTES,
    disk_pressure_max_runtime_bytes: int = DEFAULT_RUNTIME_DISK_PRESSURE_MAX_BYTES,
    max_uncompacted_archive_batches: int = DEFAULT_RETENTION_MAX_UNCOMPACTED_ARCHIVE_BATCHES,
) -> dict[str, Any]:
    if max_active_artifacts_per_group < 1:
        raise ValueError("max_active_artifacts_per_group must be >= 1")
    if log_max_bytes < 0:
        raise ValueError("log_max_bytes must be >= 0")
    if disk_pressure_max_runtime_bytes < 1:
        raise ValueError("disk_pressure_max_runtime_bytes must be >= 1")
    if max_uncompacted_archive_batches < 1:
        raise ValueError("max_uncompacted_archive_batches must be >= 1")

    root = Path(root)
    runtime_base = runner_runtime_base(root, session_id)
    runner = runner_dir(root, session_id)
    retention_id = datetime.now(timezone.utc).strftime("runner-retention-%Y%m%dT%H%M%SZ")
    archive_dir = runner / "archive" / retention_id
    before_tree_stats = _runtime_tree_stats(root, session_id)
    before_stats = _managed_runtime_artifact_stats(root, session_id)
    total_before_stats = _runtime_tree_stats(root, session_id, include_archive=True)
    archive_before_stats = _archive_tree_stats(root, session_id)
    archived: list[dict[str, Any]] = []
    compacted_archives: list[dict[str, Any]] = []
    active_group_counts: dict[str, int] = {}
    effective_active_group_limits = {
        group: _retention_group_limit(group, max_active_artifacts_per_group)
        for group in _retention_group_patterns()
    }
    protected_paths = {path.resolve() for path in _latest_public_collection_protected_paths(root=root, session_id=session_id)}

    archived.extend(_rotate_runner_log(root=root, session_id=session_id, archive_dir=archive_dir, log_max_bytes=log_max_bytes))
    for group, patterns in _retention_group_patterns().items():
        unique_paths = _unique_retention_group_paths(runtime_base, patterns)
        protected_in_group = [path for path in unique_paths if path.resolve() in protected_paths]
        archiveable_paths = [path for path in unique_paths if path.resolve() not in protected_paths]
        active_limit = effective_active_group_limits[group]
        archive_start_index = max(0, active_limit - len(protected_in_group))
        for source in archiveable_paths[archive_start_index:]:
            archived.append(_archive_file(root=root, session_id=session_id, source=source, archive_dir=archive_dir, group=group))
    compacted_archives = _compact_old_archive_batches(
        root=root,
        session_id=session_id,
        max_uncompacted_archive_batches=max_uncompacted_archive_batches,
    )
    after_tree_stats = _runtime_tree_stats(root, session_id)
    after_stats = _managed_runtime_artifact_stats(root, session_id)
    total_after_stats = _runtime_tree_stats(root, session_id, include_archive=True)
    archive_after_stats = _archive_tree_stats(root, session_id)
    active_group_counts = _active_retention_group_counts(root, session_id)
    disk_pressure_status = "PASS" if total_after_stats["runtime_artifact_bytes"] <= disk_pressure_max_runtime_bytes else "BLOCKED"
    report = {
        "schema_id": UPBIT_PAPER_LONG_RUNNER_RETENTION_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "retention_id": retention_id,
        "retention_status": "PASS" if disk_pressure_status == "PASS" else "BLOCKED",
        "primary_blocker_code": None if disk_pressure_status == "PASS" else DISK_PRESSURE_BLOCKER_CODE,
        "max_active_artifacts_per_group": max_active_artifacts_per_group,
        "max_active_artifacts_by_group": dict(DEFAULT_RETENTION_MAX_ACTIVE_ARTIFACTS_BY_GROUP),
        "effective_active_group_limits": effective_active_group_limits,
        "log_max_bytes": log_max_bytes,
        "disk_pressure_max_runtime_bytes": disk_pressure_max_runtime_bytes,
        "disk_pressure_status": disk_pressure_status,
        "runtime_artifact_count_before": before_stats["runtime_artifact_count"],
        "runtime_artifact_bytes_before": before_stats["runtime_artifact_bytes"],
        "runtime_artifact_count_after": after_stats["runtime_artifact_count"],
        "runtime_artifact_bytes_after": after_stats["runtime_artifact_bytes"],
        "active_runtime_tree_artifact_count_before": before_tree_stats["runtime_artifact_count"],
        "active_runtime_tree_artifact_bytes_before": before_tree_stats["runtime_artifact_bytes"],
        "active_runtime_tree_artifact_count_after": after_tree_stats["runtime_artifact_count"],
        "active_runtime_tree_artifact_bytes_after": after_tree_stats["runtime_artifact_bytes"],
        "unmanaged_runtime_artifact_count_before": max(
            0, before_tree_stats["runtime_artifact_count"] - before_stats["runtime_artifact_count"]
        ),
        "unmanaged_runtime_artifact_bytes_before": max(
            0, before_tree_stats["runtime_artifact_bytes"] - before_stats["runtime_artifact_bytes"]
        ),
        "unmanaged_runtime_artifact_count_after": max(
            0, after_tree_stats["runtime_artifact_count"] - after_stats["runtime_artifact_count"]
        ),
        "unmanaged_runtime_artifact_bytes_after": max(
            0, after_tree_stats["runtime_artifact_bytes"] - after_stats["runtime_artifact_bytes"]
        ),
        "total_runtime_artifact_count_before": total_before_stats["runtime_artifact_count"],
        "total_runtime_artifact_bytes_before": total_before_stats["runtime_artifact_bytes"],
        "total_runtime_artifact_count_after": total_after_stats["runtime_artifact_count"],
        "total_runtime_artifact_bytes_after": total_after_stats["runtime_artifact_bytes"],
        "archive_artifact_count_before": archive_before_stats["archive_artifact_count"],
        "archive_artifact_bytes_before": archive_before_stats["archive_artifact_bytes"],
        "archive_artifact_count_after": archive_after_stats["archive_artifact_count"],
        "archive_artifact_bytes_after": archive_after_stats["archive_artifact_bytes"],
        "active_group_counts": active_group_counts,
        "archived_artifact_count": len(archived),
        "archived_artifact_bytes": sum(int(item["artifact_bytes"]) for item in archived),
        "archived_artifacts": archived,
        "max_uncompacted_archive_batches": max_uncompacted_archive_batches,
        "compacted_archive_count": len(compacted_archives),
        "compacted_archives": compacted_archives,
        "archive_root": _relative_runtime_path(archive_dir, root),
    }
    for flag in LIVE_FALSE_FLAGS:
        report[flag] = False
    report["manifest_hash"] = upbit_paper_long_runner_retention_manifest_hash(report)
    durable_atomic_write_json(runner_retention_manifest_path(root, session_id), report)
    return report


def validate_upbit_paper_long_runner_retention_manifest(report: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_id",
        "generated_at_utc",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "retention_status",
        "disk_pressure_status",
        "runtime_artifact_count_after",
        "runtime_artifact_bytes_after",
        "total_runtime_artifact_count_after",
        "total_runtime_artifact_bytes_after",
        "archive_artifact_count_after",
        "archive_artifact_bytes_after",
        "archived_artifact_count",
        "archived_artifacts",
        "compacted_archive_count",
        "compacted_archives",
        "manifest_hash",
    }
    missing = sorted(field for field in required if field not in report)
    if missing:
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_MISSING_REQUIRED_FIELDS", "missing": missing}
    if report.get("manifest_hash") != upbit_paper_long_runner_retention_manifest_hash(report):
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_HASH_MISMATCH"}
    if report.get("schema_id") != UPBIT_PAPER_LONG_RUNNER_RETENTION_SCHEMA_ID:
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_SCHEMA_MISMATCH"}
    if (report.get("exchange"), report.get("market_type"), report.get("mode")) != ("UPBIT", "KRW_SPOT", "PAPER"):
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_SCOPE_MISMATCH"}
    for flag in LIVE_FALSE_FLAGS:
        if report.get(flag) is not False:
            return {"status": "BLOCKED", "blocker_code": "RETENTION_MANIFEST_LIVE_FLAG_MUTATED", "field": flag}
    if report.get("disk_pressure_status") == "BLOCKED" and report.get("primary_blocker_code") != DISK_PRESSURE_BLOCKER_CODE:
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_DISK_PRESSURE_BLOCKER_MISSING"}
    if report.get("retention_status") not in {"PASS", "BLOCKED"}:
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_UNKNOWN_STATUS"}
    for field in (
        "runtime_artifact_count_after",
        "runtime_artifact_bytes_after",
        "total_runtime_artifact_count_after",
        "total_runtime_artifact_bytes_after",
        "archive_artifact_count_after",
        "archive_artifact_bytes_after",
        "archived_artifact_count",
        "compacted_archive_count",
    ):
        if not isinstance(report.get(field), int) or report[field] < 0:
            return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_COUNT_INVALID", "field": field}
    if report["runtime_artifact_count_after"] > report["total_runtime_artifact_count_after"]:
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_ACTIVE_COUNT_EXCEEDS_TOTAL"}
    if report["runtime_artifact_bytes_after"] > report["total_runtime_artifact_bytes_after"]:
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_ACTIVE_BYTES_EXCEEDS_TOTAL"}
    if (
        report.get("disk_pressure_status") == "PASS"
        and isinstance(report.get("disk_pressure_max_runtime_bytes"), int)
        and report["total_runtime_artifact_bytes_after"] > report["disk_pressure_max_runtime_bytes"]
    ):
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_DISK_PRESSURE_FALSE_PASS"}
    artifacts = report.get("archived_artifacts")
    if not isinstance(artifacts, list):
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_ARCHIVED_ARTIFACTS_INVALID"}
    if report.get("archived_artifact_count") != len(artifacts):
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_ARCHIVED_COUNT_MISMATCH"}
    compacted_archives = report.get("compacted_archives")
    if not isinstance(compacted_archives, list):
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_COMPACTED_ARCHIVES_INVALID"}
    if report.get("compacted_archive_count") != len(compacted_archives):
        return {"status": "FAIL", "blocker_code": "RETENTION_MANIFEST_COMPACTED_ARCHIVE_COUNT_MISMATCH"}
    return {"status": "PASS" if report.get("retention_status") == "PASS" else "BLOCKED", "blocker_code": report.get("primary_blocker_code")}


def _portfolio_snapshot_live_flags_clear(snapshot: dict[str, Any]) -> bool:
    return all(snapshot.get(field) is not True for field in LIVE_FALSE_FLAGS)


def _non_live_profitability_refresh_should_stop_runner(refresh: dict[str, Any]) -> bool:
    if refresh.get("status") != NON_LIVE_PROFITABILITY_REFRESH_BLOCKED:
        return False
    if any(refresh.get(field) is True for field in LIVE_FALSE_FLAGS):
        return True
    blocker_code = str(refresh.get("blocker_code") or "")
    if blocker_code in NON_LIVE_PROFITABILITY_REFRESH_CRITICAL_BLOCKERS:
        return True
    if blocker_code in NON_LIVE_PROFITABILITY_REFRESH_COLLECTION_BLOCKERS:
        return False
    return True


def _portfolio_fields(root: Path, session_id: str, runtime_cycle: dict[str, Any] | None) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    source = "NOT_LOADED"
    binding_status = "MISSING"
    source_runtime_cycle_id = None
    source_snapshot_hash = None
    source_paper_ledger_head_hash = None
    runtime_cycle_id = (
        str(runtime_cycle.get("cycle_id"))
        if isinstance(runtime_cycle, dict) and runtime_cycle.get("cycle_id")
        else None
    )
    current_truth = _read_json(paper_portfolio_current_truth_path(root, session_id))
    if isinstance(current_truth, dict):
        current_truth_cycle_id = current_truth.get("source_runtime_cycle_id")
        if (
            runtime_cycle_id
            and current_truth_cycle_id == runtime_cycle_id
            and current_truth.get("snapshot_hash")
            and _portfolio_snapshot_live_flags_clear(current_truth)
        ):
            snapshot = current_truth
            source = "paper_runtime/portfolio/paper_portfolio_snapshot.json"
            binding_status = "BOUND_TO_LATEST_RUNTIME_CYCLE"
            source_runtime_cycle_id = current_truth_cycle_id
            source_snapshot_hash = current_truth.get("snapshot_hash")
            source_paper_ledger_head_hash = current_truth.get("source_paper_ledger_head_hash")
        else:
            binding_status = "CURRENT_TRUTH_STALE_OR_UNBOUND"
    if not snapshot and runtime_cycle:
        raw_snapshot = runtime_cycle.get("paper_portfolio_snapshot")
        if isinstance(raw_snapshot, dict):
            snapshot = raw_snapshot
            source = "runtime_cycle.paper_portfolio_snapshot"
            binding_status = "FALLBACK_RUNTIME_CYCLE_SNAPSHOT"
            source_runtime_cycle_id = runtime_cycle_id
            source_snapshot_hash = raw_snapshot.get("snapshot_hash")
            source_paper_ledger_head_hash = raw_snapshot.get("source_paper_ledger_head_hash")
    return {
        "current_position_count": int(snapshot.get("open_position_count") or 0),
        "cash": snapshot.get("cash_available"),
        "equity": snapshot.get("equity"),
        "realized_pnl": snapshot.get("realized_pnl"),
        "unrealized_pnl": snapshot.get("unrealized_pnl"),
        "portfolio_truth_source": source,
        "portfolio_truth_binding_status": binding_status,
        "portfolio_truth_source_runtime_cycle_id": source_runtime_cycle_id,
        "portfolio_truth_source_snapshot_hash": source_snapshot_hash,
        "portfolio_truth_source_paper_ledger_head_hash": source_paper_ledger_head_hash,
    }


def _last_cycle_fields(loop_report: dict[str, Any] | None, runtime_cycle: dict[str, Any] | None) -> dict[str, Any]:
    def safe_count(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return parsed if parsed >= 0 else 0

    def safe_string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str) and item]

    last_cycle: dict[str, Any] = {}
    if loop_report:
        cycle_results = loop_report.get("cycle_results")
        if isinstance(cycle_results, list) and cycle_results:
            candidate = cycle_results[-1]
            if isinstance(candidate, dict):
                last_cycle = candidate
    last_decision = last_cycle.get("final_decision")
    if not last_decision and runtime_cycle:
        last_decision = runtime_cycle.get("final_decision")
    return {
        "current_cycle_id": last_cycle.get("cycle_id") or (runtime_cycle or {}).get("cycle_id"),
        "last_cycle_time": last_cycle.get("completed_at_utc") or (runtime_cycle or {}).get("generated_at_utc"),
        "last_decision": last_decision or "NOT_AVAILABLE",
        "last_blocker": last_cycle.get("blocker_code") or (runtime_cycle or {}).get("blocker_code"),
        "current_symbol": last_cycle.get("selected_symbol") or (runtime_cycle or {}).get("symbol") or "UNKNOWN",
        "runtime_quality_feedback_count": safe_count(last_cycle.get("runtime_quality_feedback_count")),
        "runtime_quality_feedback_candidate_ids": safe_string_list(
            last_cycle.get("runtime_quality_feedback_candidate_ids")
        ),
        "selected_candidate_recent_failure_feedback_kind": str(
            last_cycle.get("selected_candidate_recent_failure_feedback_kind") or "NONE"
        ),
        "paper_scope_continuity_status": str(last_cycle.get("paper_scope_continuity_status") or "NOT_REQUESTED"),
        "paper_scope_continuity_requested": bool(last_cycle.get("paper_scope_continuity_requested")),
        "paper_scope_continuity_selected": bool(last_cycle.get("paper_scope_continuity_selected")),
        "paper_scope_continuity_requested_candidate_id": last_cycle.get(
            "paper_scope_continuity_requested_candidate_id"
        ),
        "paper_scope_continuity_selected_candidate_id": last_cycle.get(
            "paper_scope_continuity_selected_candidate_id"
        ),
        "paper_scope_continuity_best_candidate_id": last_cycle.get("paper_scope_continuity_best_candidate_id"),
        "paper_scope_continuity_score_gap": last_cycle.get("paper_scope_continuity_score_gap"),
        "paper_scope_continuity_net_ev_gap_bps": last_cycle.get("paper_scope_continuity_net_ev_gap_bps"),
    }


def _symbol_evidence_scorecard_fields(runtime_cycle: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(runtime_cycle, dict):
        return {
            "symbol_evidence_scorecard_count": 0,
            "selected_symbol_evidence_scorecard": None,
            "symbol_evidence_scorecards_top": [],
        }
    raw_scorecards = runtime_cycle.get("symbol_evidence_scorecards")
    scorecards = [item for item in raw_scorecards if isinstance(item, dict)] if isinstance(raw_scorecards, list) else []

    def compact_scorecard(scorecard: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": str(scorecard.get("symbol") or "UNKNOWN"),
            "rank_input_order": scorecard.get("rank_input_order"),
            "regime": str(scorecard.get("regime") or "UNKNOWN"),
            "last_price": scorecard.get("last_price"),
            "momentum_pct": scorecard.get("momentum_pct"),
            "volatility_pct": scorecard.get("volatility_pct"),
            "volume_expansion_ratio": scorecard.get("volume_expansion_ratio"),
            "spread_bps": scorecard.get("spread_bps"),
            "total_quote_volume": scorecard.get("total_quote_volume"),
            "source_public_market_data_hash": scorecard.get("source_public_market_data_hash"),
            "symbol_selection_score": scorecard.get("symbol_selection_score"),
            "best_candidate_id": scorecard.get("best_candidate_id"),
            "best_strategy_family": scorecard.get("best_strategy_family"),
            "best_candidate_selection_score": scorecard.get("best_candidate_selection_score"),
            "best_net_ev_after_cost_bps": scorecard.get("best_net_ev_after_cost_bps"),
            "best_decision": scorecard.get("best_decision"),
            "best_no_trade_reason": scorecard.get("best_no_trade_reason"),
            "best_recent_failure_feedback_kind": scorecard.get("best_recent_failure_feedback_kind", "NONE"),
            "paper_entry_review_candidate_count": scorecard.get("paper_entry_review_candidate_count"),
            "candidate_count": scorecard.get("candidate_count"),
            "evidence_scope": "PAPER_SYMBOL_EVIDENCE_ONLY",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    compact_scorecards = [compact_scorecard(item) for item in scorecards]
    def safe_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def safe_int(value: Any, default: int = 999) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    compact_scorecards.sort(
        key=lambda item: (
            safe_float(item.get("best_candidate_selection_score")),
            safe_float(item.get("best_net_ev_after_cost_bps")),
            -safe_int(item.get("rank_input_order")),
        ),
        reverse=True,
    )
    selected = runtime_cycle.get("selected_symbol_evidence_scorecard")
    selected_compact = compact_scorecard(selected) if isinstance(selected, dict) else None
    return {
        "symbol_evidence_scorecard_count": int(runtime_cycle.get("symbol_evidence_scorecard_count") or len(scorecards)),
        "selected_symbol_evidence_scorecard": selected_compact,
        "symbol_evidence_scorecards_top": compact_scorecards[:5],
    }


def build_runner_status_report(
    *,
    root: Path,
    runner_id: str,
    session_id: str,
    runner_status: str,
    started_at_utc: str,
    completed_cycle_count: int,
    failed_cycle_count: int,
    cycle_interval_seconds: float,
    loop_report: dict[str, Any] | None = None,
    primary_blocker_code: str | None = None,
    primary_blocker_message: str | None = None,
    stop_reason: str | None = None,
    next_cycle_eta: str | None = None,
    dashboard_open_result: DashboardOpenResult | None = None,
) -> dict[str, Any]:
    runtime_cycle = _load_latest_runtime_cycle(root, session_id)
    retention_manifest = _load_latest_retention_manifest(root, session_id)
    last_cycle_fields = _last_cycle_fields(loop_report, runtime_cycle)
    symbol_scorecard_fields = _symbol_evidence_scorecard_fields(runtime_cycle)
    portfolio_fields = _portfolio_fields(root, session_id, runtime_cycle)
    shadow_fields = _shadow_runtime_collection_fields(root, session_id)
    profitability_fields = _profitability_evidence_refresh_fields(root, session_id)
    generated_at = utc_now()
    if runner_status == RUNNER_STATUS_RUNNING and next_cycle_eta is None:
        next_cycle_eta = generated_at
    loop_hash = loop_report.get("loop_report_hash") if isinstance(loop_report, dict) else None
    cycle_hash = runtime_cycle.get("runtime_cycle_hash") if isinstance(runtime_cycle, dict) else None
    effective_dashboard_open_result = dashboard_open_result or _dashboard_open_result_from_background_launch(
        root,
        session_id,
        runner_id,
    )
    report = {
        "schema_id": UPBIT_PAPER_LONG_RUNNER_STATUS_SCHEMA_ID,
        "generated_at_utc": generated_at,
        "project_id": "TRADER_1",
        "runner_id": runner_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "runner_status": runner_status,
        "running": runner_status == RUNNER_STATUS_RUNNING,
        "started_at_utc": started_at_utc,
        "updated_at_utc": generated_at,
        "completed_cycle_count": completed_cycle_count,
        "failed_cycle_count": failed_cycle_count,
        "cycle_interval_seconds": cycle_interval_seconds,
        "next_cycle_eta": next_cycle_eta,
        "stop_method": STOP_FILE_METHOD,
        "stop_launcher_path": str(root / "STOP_UPBIT_PAPER.py"),
        "stop_reason": stop_reason,
        "background_runner_policy": "BACKGROUND_RUNNER_STATUS_DASHBOARD",
        "operator_console_auto_closes": True,
        "console_lifecycle_policy": "BACKGROUND_RUNNER_STATUS_DASHBOARD",
        "console_close_does_not_stop_runner": True,
        "dashboard_close_does_not_stop_runner": True,
        "primary_blocker_code": primary_blocker_code,
        "primary_blocker_message": primary_blocker_message,
        "actual_long_running_runner": True,
        "long_run_evidence_eligible": False,
        "long_run_blocker_code": LONG_RUN_EVIDENCE_BLOCKER_CODE,
        "runner_status_path": str(runner_status_path(root, session_id)),
        "stop_file_path": str(runner_stop_file_path(root, session_id)),
        "lock_path": str(runner_lock_path(root, session_id)),
        "log_path": str(runner_log_path(root, session_id)),
        "dashboard_path": str(runner_runtime_base(root, session_id) / "dashboard" / "index.html"),
        **_dashboard_status_channel_fields(root, session_id),
        **_dashboard_open_status_fields(effective_dashboard_open_result, root=root, session_id=session_id),
        "last_loop_report_path": str(
            runner_runtime_base(root, session_id) / "paper_runtime" / "upbit_paper_persistent_loop_report.json"
        ),
        "last_loop_hash": loop_hash,
        "last_runtime_cycle_hash": cycle_hash,
        "retention_manifest_path": str(runner_retention_manifest_path(root, session_id)),
        "artifact_retention_status": (
            retention_manifest.get("retention_status") if isinstance(retention_manifest, dict) else "NOT_RUN"
        ),
        "runtime_artifact_count": (
            retention_manifest.get("runtime_artifact_count_after") if isinstance(retention_manifest, dict) else None
        ),
        "runtime_artifact_bytes": (
            retention_manifest.get("runtime_artifact_bytes_after") if isinstance(retention_manifest, dict) else None
        ),
        "archived_artifact_count": (
            retention_manifest.get("archived_artifact_count") if isinstance(retention_manifest, dict) else 0
        ),
        "disk_pressure_status": (
            retention_manifest.get("disk_pressure_status") if isinstance(retention_manifest, dict) else "NOT_RUN"
        ),
        "disk_pressure_max_runtime_bytes": (
            retention_manifest.get("disk_pressure_max_runtime_bytes") if isinstance(retention_manifest, dict) else None
        ),
        **shadow_fields,
        **profitability_fields,
        **last_cycle_fields,
        **symbol_scorecard_fields,
        **portfolio_fields,
    }
    report.update(runner_lock_liveness_from_status_report(report))
    for flag in LIVE_FALSE_FLAGS:
        report[flag] = False
    report["status_hash"] = upbit_paper_long_runner_status_hash(report)
    return report


def validate_upbit_paper_long_runner_status_report(report: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_id",
        "generated_at_utc",
        "runner_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "runner_status",
        "running",
        "completed_cycle_count",
        "failed_cycle_count",
        "cycle_interval_seconds",
        "actual_long_running_runner",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "status_hash",
        "artifact_retention_status",
        "disk_pressure_status",
        "paper_shadow_runtime_collection_status",
        "shadow_completed_cycle_count",
        "shadow_observation_count",
        "shadow_actual_persistent_runtime_executed",
        "shadow_long_run_evidence_eligible",
        "profitability_evidence_refresh_status",
        "profitability_evidence_primary_blocker_code",
        "runtime_sample_history_status",
        "runtime_sample_count",
        "paper_scope_progress_status",
        "paper_scope_candidate_id",
        "paper_scope_strategy_id",
        "paper_scope_parameter_hash",
        "paper_scope_symbol",
        "paper_scope_sample_count",
        "paper_scope_min_required_sample_count",
        "paper_scope_sample_deficit",
        "paper_scope_next_collection_action",
        "paper_scope_next_operator_action",
        "paper_scope_latest_sample_at_utc",
        "paper_scope_summary_count",
        "candidate_scorecard_status",
        "candidate_scorecard_ranking_eligible",
        "candidate_scorecard_candidate_id",
        "candidate_scorecard_snapshot_path",
        "candidate_scorecard_snapshot_status",
        "overfit_diagnostic_contract_status",
        "overfit_diagnostic_status",
        "paper_shadow_evidence_validation_status",
        "paper_shadow_evidence_blocker_code",
        "paper_shadow_evidence_actionability_status",
        "symbol_evidence_scorecard_count",
        "selected_symbol_evidence_scorecard",
        "symbol_evidence_scorecards_top",
        "runtime_quality_feedback_count",
        "runtime_quality_feedback_candidate_ids",
        "selected_candidate_recent_failure_feedback_kind",
        "paper_scope_continuity_status",
        "paper_scope_continuity_requested",
        "paper_scope_continuity_selected",
        "paper_scope_continuity_requested_candidate_id",
        "paper_scope_continuity_selected_candidate_id",
        "paper_scope_continuity_best_candidate_id",
        "paper_scope_continuity_score_gap",
        "paper_scope_continuity_net_ev_gap_bps",
        "dashboard_open_attempted",
        "dashboard_opened",
        "dashboard_open_method",
        "dashboard_open_target",
        "dashboard_open_blocker_code",
        "dashboard_open_blocker_message",
    }
    missing = sorted(field for field in required if field not in report)
    if missing:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_MISSING_REQUIRED_FIELDS", "missing": missing}
    expected_hash = upbit_paper_long_runner_status_hash(report)
    if report.get("status_hash") != expected_hash:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_HASH_MISMATCH"}
    if report.get("schema_id") != UPBIT_PAPER_LONG_RUNNER_STATUS_SCHEMA_ID:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SCHEMA_MISMATCH"}
    if (report.get("exchange"), report.get("market_type"), report.get("mode")) != ("UPBIT", "KRW_SPOT", "PAPER"):
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SCOPE_MISMATCH"}
    if report.get("runner_status") not in RUNNER_STATUS_SET:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_UNKNOWN"}
    if report.get("running") is not (report.get("runner_status") == RUNNER_STATUS_RUNNING):
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_RUNNING_FLAG_MISMATCH"}
    for counter in ("completed_cycle_count", "failed_cycle_count"):
        if not isinstance(report.get(counter), int) or report[counter] < 0:
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_COUNTER_INVALID", "field": counter}
    if report.get("cycle_interval_seconds") < 0:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_INTERVAL_INVALID"}
    if report.get("long_run_evidence_eligible") is not False:
        return {"status": "BLOCKED", "blocker_code": "RUNNER_STATUS_CANNOT_CLAIM_LONG_RUN_MATURITY"}
    if report.get("long_run_blocker_code") != LONG_RUN_EVIDENCE_BLOCKER_CODE:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_LONG_RUN_BLOCKER_MISMATCH"}
    if report.get("disk_pressure_status") == "BLOCKED" and report.get("runner_status") != RUNNER_STATUS_BLOCKED:
        return {"status": "BLOCKED", "blocker_code": DISK_PRESSURE_BLOCKER_CODE}
    if report.get("shadow_long_run_evidence_eligible") is not False:
        return {"status": "BLOCKED", "blocker_code": "RUNNER_STATUS_SHADOW_CANNOT_CLAIM_LONG_RUN_MATURITY"}
    if not isinstance(report.get("symbol_evidence_scorecard_count"), int) or report["symbol_evidence_scorecard_count"] < 0:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SYMBOL_SCORECARD_COUNT_INVALID"}
    if (
        not isinstance(report.get("runtime_quality_feedback_count"), int)
        or report["runtime_quality_feedback_count"] < 0
    ):
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_QUALITY_FEEDBACK_COUNT_INVALID"}
    candidate_scorecard_candidate_id = report.get("candidate_scorecard_candidate_id")
    if candidate_scorecard_candidate_id is not None and not isinstance(candidate_scorecard_candidate_id, str):
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SCORECARD_CANDIDATE_INVALID"}
    if report.get("paper_scope_candidate_id") is not None and not isinstance(report.get("paper_scope_candidate_id"), str):
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_PAPER_SCOPE_INVALID"}
    for counter in (
        "paper_scope_sample_count",
        "paper_scope_min_required_sample_count",
        "paper_scope_sample_deficit",
        "paper_scope_summary_count",
    ):
        if not isinstance(report.get(counter), int) or report[counter] < 0:
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_PAPER_SCOPE_COUNTER_INVALID", "field": counter}
    if report.get("paper_scope_min_required_sample_count") < 1:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_PAPER_SCOPE_COUNTER_INVALID"}
    if not isinstance(report.get("paper_scope_progress_status"), str) or not report["paper_scope_progress_status"]:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_PAPER_SCOPE_INVALID"}
    if not isinstance(report.get("paper_scope_next_operator_action"), str) or not report[
        "paper_scope_next_operator_action"
    ]:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_PAPER_SCOPE_INVALID"}
    if not isinstance(report.get("candidate_scorecard_snapshot_path"), str) or not report[
        "candidate_scorecard_snapshot_path"
    ]:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SCORECARD_SNAPSHOT_PATH_INVALID"}
    if report.get("candidate_scorecard_snapshot_status") not in {"PASS", "FAIL", "NOT_LOADED"}:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SCORECARD_SNAPSHOT_STATUS_INVALID"}
    if (
        report.get("completed_cycle_count", 0) > 0
        and report.get("candidate_scorecard_status") == "PASS"
        and report.get("candidate_scorecard_snapshot_status") != "PASS"
    ):
        return {
            "status": "BLOCKED",
            "blocker_code": report.get("candidate_scorecard_snapshot_blocker_code") or "SCORECARD_SNAPSHOT_MISSING",
        }
    runtime_quality_feedback_candidate_ids = report.get("runtime_quality_feedback_candidate_ids")
    if not isinstance(runtime_quality_feedback_candidate_ids, list) or any(
        not isinstance(item, str) or not item for item in runtime_quality_feedback_candidate_ids
    ):
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_QUALITY_FEEDBACK_CANDIDATES_INVALID"}
    if not isinstance(report.get("selected_candidate_recent_failure_feedback_kind"), str) or not report[
        "selected_candidate_recent_failure_feedback_kind"
    ]:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SELECTED_FEEDBACK_KIND_INVALID"}
    if report.get("paper_scope_continuity_status") not in {
        "NOT_REQUESTED",
        "SELECTED",
        "FOCUS_CANDIDATE_MISSING",
        "FOCUS_CANDIDATE_NOT_ENTRY_REVIEW",
        "FOCUS_CANDIDATE_LIVE_FLAG_UNSAFE",
        "SCORE_GAP_TOO_WIDE",
        "NET_EV_GAP_TOO_WIDE",
        "MANAGED_POSITION_OVERRIDES_SCOPE_FOCUS",
    }:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SCOPE_CONTINUITY_INVALID"}
    for field in ("paper_scope_continuity_requested", "paper_scope_continuity_selected"):
        if not isinstance(report.get(field), bool):
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SCOPE_CONTINUITY_INVALID", "field": field}
    mutation_status_fields = (
        "strategy_mutation_compiler_status",
        "strategy_mutation_compiler_blocker_code",
        "strategy_mutation_compiler_path",
        "strategy_mutation_compiler_candidate_id",
        "strategy_mutation_compiler_source",
        "strategy_mutation_reason_code",
        "strategy_mutation_id",
        "strategy_mutated_paper_candidate_spec_id",
        "strategy_mutation_spec_hash",
        "strategy_mutated_parameter_hash",
        "strategy_mutation_exploration_budget_id",
        "strategy_mutation_ranking_eligible",
        "strategy_mutation_compiler_report_current",
        "strategy_mutation_compiler_report_ignored_candidate_id",
        "strategy_mutation_compiler_message",
    )
    if any(field in report for field in mutation_status_fields):
        missing_mutation_fields = [field for field in mutation_status_fields if field not in report]
        if missing_mutation_fields:
            return {
                "status": "FAIL",
                "blocker_code": "RUNNER_STATUS_MUTATION_FIELDS_INCOMPLETE",
                "missing_fields": missing_mutation_fields,
            }
        if report.get("strategy_mutation_compiler_status") not in {"NOT_RUN", "PASS", "BLOCKED", "FAIL"}:
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_MUTATION_STATUS_INVALID"}
        if report.get("strategy_mutation_ranking_eligible") is not False:
            return {"status": "BLOCKED", "blocker_code": "RUNNER_STATUS_MUTATION_RANKING_ENABLED"}
        if not isinstance(report.get("strategy_mutation_compiler_report_current"), bool):
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_MUTATION_CURRENT_FLAG_INVALID"}
        if not isinstance(report.get("strategy_mutation_compiler_message"), str) or not report[
            "strategy_mutation_compiler_message"
        ]:
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_MUTATION_MESSAGE_INVALID"}
        if report.get("strategy_mutation_compiler_report_current") is True:
            mutation_candidate_id = report.get("strategy_mutation_compiler_candidate_id")
            if not mutation_candidate_id:
                return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_MUTATION_CURRENT_CANDIDATE_MISSING"}
            if report.get("paper_scope_candidate_id") and mutation_candidate_id != report.get("paper_scope_candidate_id"):
                return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_MUTATION_CANDIDATE_MISMATCH"}
    symbol_scorecards_top = report.get("symbol_evidence_scorecards_top")
    if not isinstance(symbol_scorecards_top, list):
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SYMBOL_SCORECARDS_INVALID"}
    for scorecard in symbol_scorecards_top:
        if not isinstance(scorecard, dict) or not scorecard.get("symbol"):
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SYMBOL_SCORECARD_INVALID"}
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            if scorecard.get(field) is not False:
                return {"status": "BLOCKED", "blocker_code": "RUNNER_STATUS_SYMBOL_SCORECARD_LIVE_FLAG_MUTATED"}
    selected_symbol_scorecard = report.get("selected_symbol_evidence_scorecard")
    if selected_symbol_scorecard is not None:
        if not isinstance(selected_symbol_scorecard, dict) or not selected_symbol_scorecard.get("symbol"):
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_SELECTED_SYMBOL_SCORECARD_INVALID"}
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            if selected_symbol_scorecard.get(field) is not False:
                return {"status": "BLOCKED", "blocker_code": "RUNNER_STATUS_SYMBOL_SCORECARD_LIVE_FLAG_MUTATED"}
    if report.get("completed_cycle_count", 0) > 0:
        if report.get("paper_shadow_runtime_collection_status") != PAPER_SHADOW_RUNTIME_REFRESH_EXECUTED:
            if (
                report.get("runner_status") == RUNNER_STATUS_BLOCKED
                and report.get("stop_reason") == "PAPER_SHADOW_RUNTIME_REFRESH_BLOCKED"
                and report.get("primary_blocker_code")
            ):
                pass
            else:
                return {
                    "status": "BLOCKED",
                    "blocker_code": report.get("paper_shadow_primary_blocker_code")
                    or PAPER_SHADOW_RUNTIME_REFRESH_FAILED_BLOCKER_CODE,
                }
        elif report.get("shadow_actual_persistent_runtime_executed") is not True:
            return {"status": "BLOCKED", "blocker_code": PAPER_SHADOW_RUNTIME_REFRESH_FAILED_BLOCKER_CODE}
        elif report.get("shadow_completed_cycle_count", 0) <= 0 or report.get("shadow_observation_count", 0) <= 0:
            return {"status": "BLOCKED", "blocker_code": PAPER_SHADOW_RUNTIME_REFRESH_FAILED_BLOCKER_CODE}
        refresh_status = report.get("profitability_evidence_refresh_status")
        profitability_collecting_nonblocking = (
            refresh_status == NON_LIVE_PROFITABILITY_REFRESH_COLLECTING
            and report.get("profitability_evidence_primary_blocker_code")
            in NON_LIVE_PROFITABILITY_REFRESH_COLLECTION_BLOCKERS
        )
        if refresh_status not in {
            NON_LIVE_PROFITABILITY_REFRESH_PASS,
            NON_LIVE_PROFITABILITY_REFRESH_COLLECTING,
        }:
            if (
                report.get("runner_status") == RUNNER_STATUS_BLOCKED
                and report.get("stop_reason") == "NON_LIVE_PROFITABILITY_EVIDENCE_REFRESH_BLOCKED"
                and report.get("primary_blocker_code")
            ):
                pass
            else:
                return {
                    "status": "BLOCKED",
                    "blocker_code": report.get("profitability_evidence_primary_blocker_code")
                    or NON_LIVE_PROFITABILITY_REFRESH_FAILED_BLOCKER_CODE,
                }
        elif report.get("runtime_sample_count", 0) <= 0:
            return {"status": "BLOCKED", "blocker_code": "ACTUAL_PAPER_RUNTIME_SAMPLE_MISSING"}
        elif report.get("runtime_sample_history_status") != "PASS":
            return {
                "status": "BLOCKED",
                "blocker_code": report.get("profitability_evidence_primary_blocker_code")
                or "RUNTIME_SAMPLE_HISTORY_INVALID",
            }
        elif report.get("candidate_scorecard_status") != "PASS":
            if profitability_collecting_nonblocking and report.get("candidate_scorecard_status") == "NOT_LOADED":
                pass
            else:
                return {"status": "BLOCKED", "blocker_code": "SCORECARD_SCHEMA_INVALID"}
        if report.get("overfit_diagnostic_contract_status") != "PASS":
            if profitability_collecting_nonblocking and report.get("overfit_diagnostic_contract_status") == "NOT_LOADED":
                pass
            else:
                return {"status": "BLOCKED", "blocker_code": "SCHEMA_IDENTITY_MISMATCH"}
        elif report.get("paper_shadow_evidence_validation_status") not in {"PASS", "BLOCKED"}:
            return {
                "status": "BLOCKED",
                "blocker_code": report.get("paper_shadow_evidence_blocker_code")
                or NON_LIVE_PROFITABILITY_REFRESH_FAILED_BLOCKER_CODE,
            }
    for flag in LIVE_FALSE_FLAGS:
        if report.get(flag) is not False:
            return {"status": "BLOCKED", "blocker_code": "RUNNER_STATUS_LIVE_FLAG_MUTATED", "field": flag}
    dashboard_status_channel_fields = (
        "dashboard_status_channel_enabled",
        "dashboard_status_channel_status",
        "dashboard_status_channel_mode",
        "dashboard_status_channel_url",
        "dashboard_status_channel_source",
        "dashboard_status_channel_path",
        "dashboard_status_channel_live_order_ready",
        "dashboard_status_channel_live_order_allowed",
        "dashboard_status_channel_can_live_trade",
        "dashboard_status_channel_scale_up_allowed",
    )
    if any(field in report for field in dashboard_status_channel_fields):
        missing_channel_fields = [field for field in dashboard_status_channel_fields if field not in report]
        if missing_channel_fields:
            return {
                "status": "FAIL",
                "blocker_code": "RUNNER_STATUS_DASHBOARD_CHANNEL_FIELDS_INCOMPLETE",
                "missing_fields": missing_channel_fields,
            }
        if report.get("dashboard_status_channel_mode") != DASHBOARD_STATUS_CHANNEL_MODE:
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_DASHBOARD_CHANNEL_MODE_INVALID"}
        if report.get("dashboard_status_channel_source") != "runner_status.json":
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_DASHBOARD_CHANNEL_SOURCE_INVALID"}
        for field in (
            "dashboard_status_channel_live_order_ready",
            "dashboard_status_channel_live_order_allowed",
            "dashboard_status_channel_can_live_trade",
            "dashboard_status_channel_scale_up_allowed",
        ):
            if report.get(field) is not False:
                return {
                    "status": "BLOCKED",
                    "blocker_code": "RUNNER_STATUS_DASHBOARD_CHANNEL_LIVE_FLAG_MUTATED",
                    "field": field,
                }
        if report.get("dashboard_status_channel_enabled") is True:
            if report.get("dashboard_status_channel_status") != "RUNNING":
                return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_DASHBOARD_CHANNEL_STATUS_INVALID"}
            if _safe_local_dashboard_url(report.get("dashboard_status_channel_url")) is None:
                return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_DASHBOARD_CHANNEL_URL_INVALID"}
    if report.get("runner_status") == RUNNER_STATUS_LOCKED and report.get("primary_blocker_code") != LOCK_BLOCKER_CODE:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_LOCKED_WITHOUT_LOCK_BLOCKER"}
    if report.get("dashboard_open_attempted") is not True:
        if report.get("dashboard_opened") is not False or report.get("dashboard_open_method") != "NOT_ATTEMPTED":
            return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_DASHBOARD_OPEN_STATE_INVALID"}
    elif report.get("dashboard_opened") is not True and report.get("dashboard_open_blocker_code") not in {
        DASHBOARD_FILE_MISSING_BLOCKER_CODE,
        DASHBOARD_OPEN_FAILED_BLOCKER_CODE,
        DASHBOARD_PREOPEN_REFRESH_FAILED_BLOCKER_CODE,
    }:
        return {"status": "FAIL", "blocker_code": "RUNNER_STATUS_DASHBOARD_OPEN_BLOCKER_MISSING"}
    return {"status": "PASS", "blocker_code": None}


def _write_runner_status(path: Path, report: dict[str, Any]) -> None:
    validation = validate_upbit_paper_long_runner_status_report(report)
    if validation.get("status") not in {"PASS"}:
        raise RuntimeError(f"invalid UPBIT PAPER runner status: {validation}")
    durable_atomic_write_json(path, report)


def _persist_dashboard_open_result(
    report: dict[str, Any],
    result: DashboardOpenResult,
    *,
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
) -> dict[str, Any]:
    if report.get("runner_status") == RUNNER_STATUS_LOCKED:
        return report
    status_path = runner_status_path(root, session_id)
    if not status_path.exists():
        return report
    updated = dict(report)
    updated.update(_dashboard_open_status_fields(result, root=root, session_id=session_id))
    updated["status_hash"] = upbit_paper_long_runner_status_hash(updated)
    _write_runner_status(status_path, updated)
    return updated


def _emit_console_status(report: dict[str, Any]) -> None:
    print(
        "TRADER_1 UPBIT_PAPER "
        f"status={report.get('runner_status')} "
        f"cycles={report.get('completed_cycle_count')} "
        f"shadow={report.get('paper_shadow_runtime_collection_status')} "
        f"evidence={report.get('profitability_evidence_refresh_status')} "
        f"fails={report.get('failed_cycle_count')} "
        f"decision={report.get('last_decision')} "
        f"next={report.get('next_cycle_eta') or 'not_scheduled'} "
        "live_order_allowed=false",
        flush=True,
    )


def _maybe_refresh_dashboard(
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
    *,
    refresh_paper_shadow_runtime: bool = False,
) -> None:
    from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle

    launcher_report = build_launcher_report("UPBIT_PAPER")
    launcher_report["session_id"] = session_id
    refresh_public_rest_continuity = _bool_env("TRADER1_UPBIT_PAPER_USE_PUBLIC_REST", True)
    write_launcher_runtime_bundle(
        launcher_report,
        root=root,
        refresh_upbit_public_rest_continuity=refresh_public_rest_continuity,
        refresh_paper_shadow_runtime=refresh_paper_shadow_runtime,
    )


def _refresh_dashboard_after_runner_status(root: Path, session_id: str, *, refresh_dashboard: bool) -> None:
    if not refresh_dashboard:
        return
    try:
        _maybe_refresh_dashboard(root, session_id=session_id)
    except Exception as exc:  # pragma: no cover - depends on operator filesystem/browser environment.
        _append_log(
            root,
            session_id,
            {
                "event": "dashboard_refresh_after_runner_status_failed",
                "error": str(exc),
                "at": utc_now(),
            },
        )


def _finalize_runner_stop_file(
    *,
    root: Path,
    session_id: str,
    status_path: Path,
    runner_id: str,
    started_at_utc: str,
    completed_cycle_count: int,
    failed_cycle_count: int,
    cycle_interval_seconds: float,
    loop_report: dict[str, Any] | None,
    refresh_dashboard: bool,
    emit_console_status: bool,
    dashboard_open_result: DashboardOpenResult | None,
) -> dict[str, Any]:
    final = build_runner_status_report(
        root=root,
        runner_id=runner_id,
        session_id=session_id,
        runner_status=RUNNER_STATUS_STOPPED,
        started_at_utc=started_at_utc,
        completed_cycle_count=completed_cycle_count,
        failed_cycle_count=failed_cycle_count,
        cycle_interval_seconds=cycle_interval_seconds,
        loop_report=loop_report,
        stop_reason="STOP_FILE",
        dashboard_open_result=dashboard_open_result,
    )
    _write_runner_status(status_path, final)
    _confirm_operator_stop_reports_from_final_status(root, session_id, final)
    _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
    if emit_console_status:
        _emit_console_status(final)
    _append_log(root, session_id, {"event": "runner_stopped", "reason": "STOP_FILE", "at": utc_now()})
    return final


def _sleep_until_next_cycle_or_stop_requested(
    *,
    root: Path,
    session_id: str,
    cycle_interval_seconds: float,
    sleep_fn: Callable[[float], None],
) -> bool:
    stop_path = runner_stop_file_path(root, session_id)
    if stop_path.exists():
        return True
    if cycle_interval_seconds <= 0 or not math.isfinite(cycle_interval_seconds):
        return stop_path.exists()
    remaining = float(cycle_interval_seconds)
    poll_seconds = max(0.05, min(DEFAULT_DASHBOARD_STATUS_CHANNEL_STOP_POLL_SECONDS, remaining))
    while remaining > 0:
        if stop_path.exists():
            return True
        step = min(poll_seconds, remaining)
        sleep_fn(step)
        remaining -= step
        if stop_path.exists():
            return True
    return stop_path.exists()


def refresh_paper_shadow_runtime_from_latest_loop(root: Path, session_id: str) -> dict[str, dict[str, Any]] | None:
    from trader1.runtime.boot.safe_launcher import refresh_scoped_paper_shadow_runtime_harness_if_safe

    launcher_scope = {
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
    }
    return refresh_scoped_paper_shadow_runtime_harness_if_safe(launcher_scope, root, refresh=True)


def runner_dashboard_path(root: Path, session_id: str = DEFAULT_SESSION_ID) -> Path:
    return runner_runtime_base(root, session_id) / "dashboard" / "index.html"


def _dashboard_open_status_fields(
    result: DashboardOpenResult | None,
    *,
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
) -> dict[str, Any]:
    if result is None:
        return {
            "dashboard_open_attempted": False,
            "dashboard_opened": False,
            "dashboard_open_method": "NOT_ATTEMPTED",
            "dashboard_open_target": str(runner_dashboard_path(root, session_id)),
            "dashboard_open_blocker_code": None,
            "dashboard_open_blocker_message": None,
        }
    return {
        "dashboard_open_attempted": result.attempted,
        "dashboard_opened": result.opened,
        "dashboard_open_method": result.method,
        "dashboard_open_target": result.target,
        "dashboard_open_blocker_code": result.blocker_code,
        "dashboard_open_blocker_message": result.blocker_message,
    }


def _dashboard_open_result_from_background_launch(
    root: Path,
    session_id: str,
    runner_id: str,
) -> DashboardOpenResult | None:
    report = _read_json(runner_background_launch_report_path(root, session_id))
    if not isinstance(report, dict):
        return None
    if (report.get("exchange"), report.get("market_type"), report.get("mode")) != ("UPBIT", "KRW_SPOT", "PAPER"):
        return None
    if report.get("background_launch_status") != "STARTED":
        return None
    runner_pid = report.get("runner_pid")
    if isinstance(runner_pid, int) and not str(runner_id).endswith(f"-{runner_pid}"):
        return None
    if report.get("dashboard_open_attempted") is not True:
        return None
    return DashboardOpenResult(
        attempted=True,
        opened=report.get("dashboard_opened") is True,
        method=str(report.get("dashboard_open_method") or "NOT_ATTEMPTED"),
        target=str(report.get("dashboard_open_target") or runner_dashboard_path(root, session_id).resolve()),
        path=str(runner_dashboard_path(root, session_id)),
        blocker_code=report.get("dashboard_open_blocker_code"),
        blocker_message=report.get("dashboard_open_blocker_message"),
    )


def open_runner_dashboard_result(
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
    *,
    opener: Callable[[str], bool] | None = None,
    startfile: Callable[[str], Any] | None = None,
    expected_runner_pid: int | None = None,
    channel_probe: Callable[[str], bool] | None = None,
) -> DashboardOpenResult:
    channel_url = _dashboard_status_channel_url_from_artifacts(
        root,
        session_id,
        expected_runner_pid=expected_runner_pid,
    )
    if channel_url:
        probe = channel_probe or _local_dashboard_url_is_reachable
        if probe(channel_url):
            try:
                if bool((opener or webbrowser.open)(channel_url)):
                    return DashboardOpenResult(
                        attempted=True,
                        opened=True,
                        method="local_status_channel",
                        target=channel_url,
                        path=str(runner_dashboard_path(root, session_id)),
                    )
            except Exception:
                pass

    path = runner_dashboard_path(root, session_id)
    resolved = path.resolve()
    if not path.exists():
        return DashboardOpenResult(
            attempted=False,
            opened=False,
            method="NOT_ATTEMPTED",
            target=str(resolved),
            path=str(path),
            blocker_code=DASHBOARD_FILE_MISSING_BLOCKER_CODE,
            blocker_message="Dashboard file is not present yet. Refresh the PAPER dashboard before opening it.",
        )

    uri = resolved.as_uri()
    browser_error: str | None = None
    startfile_error: str | None = None
    fallback = startfile or getattr(os, "startfile", None)
    if opener is None and os.name == "nt" and fallback is not None:
        try:
            fallback(str(resolved))
            return DashboardOpenResult(
                attempted=True,
                opened=True,
                method="os.startfile",
                target=str(resolved),
                path=str(path),
            )
        except Exception as exc:
            startfile_error = f"{type(exc).__name__}: {exc}"

    try:
        if bool((opener or webbrowser.open)(uri)):
            return DashboardOpenResult(
                attempted=True,
                opened=True,
                method="webbrowser.open",
                target=uri,
                path=str(path),
            )
    except Exception as exc:
        browser_error = f"{type(exc).__name__}: {exc}"

    if fallback is not None:
        try:
            fallback(str(resolved))
            return DashboardOpenResult(
                attempted=True,
                opened=True,
                method="os.startfile",
                target=str(resolved),
                path=str(path),
            )
        except Exception as exc:
            fallback_error = f"{type(exc).__name__}: {exc}"
        else:  # pragma: no cover - kept for type checkers; fallback returns above.
            fallback_error = None
    else:
        fallback_error = "os.startfile unavailable"

    detail = "webbrowser.open returned false"
    if startfile_error:
        detail = f"os.startfile failed: {startfile_error}; {detail}"
    if browser_error:
        detail = f"webbrowser.open failed: {browser_error}"
    if fallback_error:
        detail = f"{detail}; fallback failed: {fallback_error}"
    return DashboardOpenResult(
        attempted=True,
        opened=False,
        method="FAILED",
        target=uri,
        path=str(path),
        blocker_code=DASHBOARD_OPEN_FAILED_BLOCKER_CODE,
        blocker_message=detail,
    )


def open_runner_dashboard(
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
    *,
    opener: Callable[[str], bool] | None = None,
) -> bool:
    return open_runner_dashboard_result(root, session_id, opener=opener).opened


def dashboard_preopen_refresh_failed_result(
    root: Path,
    session_id: str = DEFAULT_SESSION_ID,
    *,
    error: str,
) -> DashboardOpenResult:
    path = runner_dashboard_path(root, session_id)
    return DashboardOpenResult(
        attempted=True,
        opened=False,
        method="PRE_OPEN_REFRESH_FAILED",
        target=str(path.resolve()),
        path=str(path),
        blocker_code=DASHBOARD_PREOPEN_REFRESH_FAILED_BLOCKER_CODE,
        blocker_message=(
            "Dashboard refresh failed before opening, so the launcher did not open a possibly stale dashboard: "
            f"{error}"
        ),
    )


def run_upbit_paper_long_running_runner(
    *,
    root: Path = ROOT,
    session_id: str = DEFAULT_SESSION_ID,
    runner_id: str | None = None,
    cycle_interval_seconds: float = DEFAULT_CYCLE_INTERVAL_SECONDS,
    max_cycles: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    attempt_public_symbol_discovery: bool = True,
    attempt_network_market_data: bool = True,
    public_discovery_timeout_seconds: float = 3.0,
    refresh_dashboard: bool = True,
    stale_lock_after_seconds: int = DEFAULT_LOCK_STALE_AFTER_SECONDS,
    emit_console_status: bool = False,
    dashboard_open_result: DashboardOpenResult | None = None,
    dashboard_status_channel_enabled: bool = False,
    dashboard_status_channel_shutdown_grace_seconds: float = DEFAULT_DASHBOARD_STATUS_CHANNEL_SHUTDOWN_GRACE_SECONDS,
    retention_max_active_artifacts_per_group: int = DEFAULT_RETENTION_MAX_ACTIVE_ARTIFACTS_PER_GROUP,
    retention_max_uncompacted_archive_batches: int = DEFAULT_RETENTION_MAX_UNCOMPACTED_ARCHIVE_BATCHES,
    retention_log_max_bytes: int = DEFAULT_RUNNER_LOG_MAX_BYTES,
    disk_pressure_max_runtime_bytes: int = DEFAULT_RUNTIME_DISK_PRESSURE_MAX_BYTES,
    paper_trade_intent_inputs_provider: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    if cycle_interval_seconds < 0:
        raise ValueError("cycle_interval_seconds must be >= 0")
    if max_cycles is not None and max_cycles < 0:
        raise ValueError("max_cycles must be >= 0 when provided")

    root = Path(root)
    runner_id = runner_id or f"upbit-paper-runner-{int(time.time())}-{os.getpid()}"
    status_path = runner_status_path(root, session_id)
    started_at = utc_now()
    completed = 0
    failed = 0
    last_loop_report: dict[str, Any] | None = None
    dashboard_status_channel_handle: DashboardStatusChannelHandle | None = None
    dashboard_status_channel_final_status = "STOPPED"

    lock = acquire_runner_lock(root, session_id, stale_after_seconds=stale_lock_after_seconds)
    if not lock.acquired:
        report = build_runner_status_report(
            root=root,
            runner_id=runner_id,
            session_id=session_id,
            runner_status=RUNNER_STATUS_LOCKED,
            started_at_utc=started_at,
            completed_cycle_count=0,
            failed_cycle_count=0,
            cycle_interval_seconds=cycle_interval_seconds,
            primary_blocker_code=lock.blocker_code,
            primary_blocker_message=lock.blocker_message,
            stop_reason="DUPLICATE_START_BLOCKED",
            dashboard_open_result=dashboard_open_result,
        )
        durable_atomic_write_json(runner_blocked_start_status_path(root, session_id), report)
        if emit_console_status:
            _emit_console_status(report)
        return report

    try:
        if dashboard_status_channel_enabled:
            dashboard_status_channel_handle = start_runner_dashboard_status_channel(root, session_id)
        _append_log(root, session_id, {"event": "runner_started", "runner_id": runner_id, "at": started_at})
        retention = apply_runner_artifact_retention(
            root=root,
            session_id=session_id,
            max_active_artifacts_per_group=retention_max_active_artifacts_per_group,
            max_uncompacted_archive_batches=retention_max_uncompacted_archive_batches,
            log_max_bytes=retention_log_max_bytes,
            disk_pressure_max_runtime_bytes=disk_pressure_max_runtime_bytes,
        )
        retention_validation = validate_upbit_paper_long_runner_retention_manifest(retention)
        if retention_validation.get("status") != "PASS":
            failed += 1
            blocked = build_runner_status_report(
                root=root,
                runner_id=runner_id,
                session_id=session_id,
                runner_status=RUNNER_STATUS_BLOCKED,
                started_at_utc=started_at,
                completed_cycle_count=0,
                failed_cycle_count=failed,
                cycle_interval_seconds=cycle_interval_seconds,
                primary_blocker_code=retention_validation.get("blocker_code") or DISK_PRESSURE_BLOCKER_CODE,
                primary_blocker_message="Runtime artifact retention or disk pressure guard blocked PAPER runner startup.",
                stop_reason="RUNTIME_DISK_PRESSURE_BLOCKED",
                dashboard_open_result=dashboard_open_result,
            )
            _write_runner_status(status_path, blocked)
            _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
            if emit_console_status:
                _emit_console_status(blocked)
            _append_log(root, session_id, {"event": "runner_blocked", "reason": "RUNTIME_DISK_PRESSURE_BLOCKED", "at": utc_now()})
            dashboard_status_channel_final_status = "BLOCKED"
            return blocked
        if emit_console_status:
            print("TRADER_1 UPBIT_PAPER runner started", flush=True)
            print(f"runner_status_path={runner_status_path(root, session_id)}", flush=True)
            print(f"dashboard_path={runner_runtime_base(root, session_id) / 'dashboard' / 'index.html'}", flush=True)
            print(f"stop_launcher_path={root / 'STOP_UPBIT_PAPER.py'}", flush=True)
            print(f"stop_file_path={runner_stop_file_path(root, session_id)}", flush=True)
            print("background_runner_policy=dashboard_status_plus_STOP_UPBIT_PAPER", flush=True)
            print("live_order_ready=false live_order_allowed=false can_live_trade=false scale_up_allowed=false", flush=True)
        while True:
            heartbeat_runner_lock(lock, session_id)
            stop_file = runner_stop_file_path(root, session_id)
            if stop_file.exists():
                return _finalize_runner_stop_file(
                    root=root,
                    session_id=session_id,
                    status_path=status_path,
                    runner_id=runner_id,
                    started_at_utc=started_at,
                    completed_cycle_count=completed,
                    failed_cycle_count=failed,
                    cycle_interval_seconds=cycle_interval_seconds,
                    loop_report=last_loop_report,
                    refresh_dashboard=refresh_dashboard,
                    emit_console_status=emit_console_status,
                    dashboard_open_result=dashboard_open_result,
                )
            if max_cycles is not None and completed >= max_cycles:
                final = build_runner_status_report(
                    root=root,
                    runner_id=runner_id,
                    session_id=session_id,
                    runner_status=RUNNER_STATUS_STOPPED,
                    started_at_utc=started_at,
                    completed_cycle_count=completed,
                    failed_cycle_count=failed,
                    cycle_interval_seconds=cycle_interval_seconds,
                    loop_report=last_loop_report,
                    stop_reason="MAX_CYCLES_REACHED",
                    dashboard_open_result=dashboard_open_result,
                )
                _write_runner_status(status_path, final)
                _confirm_operator_stop_reports_from_final_status(root, session_id, final)
                _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
                if emit_console_status:
                    _emit_console_status(final)
                _append_log(root, session_id, {"event": "runner_stopped", "reason": "MAX_CYCLES_REACHED", "at": utc_now()})
                return final

            running = build_runner_status_report(
                root=root,
                runner_id=runner_id,
                session_id=session_id,
                runner_status=RUNNER_STATUS_RUNNING,
                started_at_utc=started_at,
                completed_cycle_count=completed,
                failed_cycle_count=failed,
                cycle_interval_seconds=cycle_interval_seconds,
                loop_report=last_loop_report,
                next_cycle_eta=utc_now(),
                dashboard_open_result=dashboard_open_result,
            )
            _write_runner_status(status_path, running)
            _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
            if emit_console_status:
                _emit_console_status(running)

            cycle_loop_id = f"{runner_id}-cycle-{completed + 1:06d}"
            history_paper_scope_focus = _paper_scope_continuity_focus_from_history(
                root,
                session_id,
                persist_fresh_history=True,
            )
            provider_paper_scope_focus: dict[str, Any] | None = None
            if paper_trade_intent_inputs_provider is not None:
                try:
                    latest_runtime_cycle = _load_latest_runtime_cycle(root, session_id)
                    current_snapshot = (
                        latest_runtime_cycle.get("paper_portfolio_snapshot")
                        if isinstance(latest_runtime_cycle, dict)
                        else None
                    )
                    intent_inputs = paper_trade_intent_inputs_provider(
                        root=root,
                        session_id=session_id,
                        current_paper_portfolio_snapshot=current_snapshot,
                        current_runtime_cycle_report=latest_runtime_cycle,
                    )
                    provider_focus = _paper_scope_focus_from_trade_intent_inputs(intent_inputs)
                    if provider_focus is not None:
                        provider_paper_scope_focus = provider_focus
                        _append_log(
                            root,
                            session_id,
                            {
                                "event": "paper_trade_intent_inputs_provider_selected_candidate",
                                "candidate_id": provider_focus.get("candidate_id"),
                                "symbol": provider_focus.get("symbol"),
                                "source": provider_focus.get("source"),
                                "at": utc_now(),
                                "live_order_ready": False,
                                "live_order_allowed": False,
                                "can_live_trade": False,
                                "scale_up_allowed": False,
                            },
                        )
                except Exception as exc:  # pragma: no cover - provider failures must fail closed.
                    _append_log(
                        root,
                        session_id,
                        {
                            "event": "paper_trade_intent_inputs_provider_blocked",
                            "error": str(exc),
                            "at": utc_now(),
                            "live_order_ready": False,
                            "live_order_allowed": False,
                            "can_live_trade": False,
                            "scale_up_allowed": False,
                        },
                    )
            paper_scope_focus, paper_scope_focus_arbitration_status = _select_paper_scope_focus_for_next_cycle(
                history_focus=history_paper_scope_focus,
                provider_focus=provider_paper_scope_focus,
            )
            if history_paper_scope_focus is not None or provider_paper_scope_focus is not None:
                _append_log(
                    root,
                    session_id,
                    {
                        "event": "paper_scope_focus_arbitrated",
                        "status": paper_scope_focus_arbitration_status,
                        "selected_candidate_id": (
                            paper_scope_focus.get("candidate_id") if isinstance(paper_scope_focus, dict) else None
                        ),
                        "history_candidate_id": (
                            history_paper_scope_focus.get("candidate_id")
                            if isinstance(history_paper_scope_focus, dict)
                            else None
                        ),
                        "provider_candidate_id": (
                            provider_paper_scope_focus.get("candidate_id")
                            if isinstance(provider_paper_scope_focus, dict)
                            else None
                        ),
                        "at": utc_now(),
                        "live_order_ready": False,
                        "live_order_allowed": False,
                        "can_live_trade": False,
                        "scale_up_allowed": False,
                    },
                )
            loop_result = run_upbit_paper_persistent_loop(
                root=root,
                loop_id=cycle_loop_id,
                session_id=session_id,
                requested_cycle_count=1,
                max_cycle_count=1,
                attempt_public_symbol_discovery=attempt_public_symbol_discovery,
                require_public_symbol_discovery=False,
                attempt_network_market_data=attempt_network_market_data,
                public_discovery_timeout_seconds=public_discovery_timeout_seconds,
                paper_scope_focus=paper_scope_focus,
            )
            last_loop_report = loop_result
            loop_validation = validate_upbit_paper_persistent_loop_report(loop_result)
            loop_validation_status = getattr(loop_validation, "status", None)
            loop_validation_blocker = getattr(loop_validation, "blocker_code", None)
            if loop_validation_status != "PASS" or loop_result.get("loop_status") != "PASS":
                failed += 1
                blocked = build_runner_status_report(
                    root=root,
                    runner_id=runner_id,
                    session_id=session_id,
                    runner_status=RUNNER_STATUS_BLOCKED,
                    started_at_utc=started_at,
                    completed_cycle_count=completed,
                    failed_cycle_count=failed,
                    cycle_interval_seconds=cycle_interval_seconds,
                    loop_report=last_loop_report,
                    primary_blocker_code=loop_validation_blocker or loop_result.get("blocker_code"),
                    primary_blocker_message="Bounded PAPER cycle failed validation.",
                    stop_reason="PAPER_CYCLE_BLOCKED",
                    dashboard_open_result=dashboard_open_result,
                )
                _write_runner_status(status_path, blocked)
                _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
                if emit_console_status:
                    _emit_console_status(blocked)
                _append_log(
                    root,
                    session_id,
                    {
                        "event": "runner_blocked",
                        "validation": {
                            "status": loop_validation_status,
                            "blocker_code": loop_validation_blocker,
                        },
                        "at": utc_now(),
                    },
                )
                dashboard_status_channel_final_status = "BLOCKED"
                return blocked

            completed += 1
            try:
                refreshed_shadow = refresh_paper_shadow_runtime_from_latest_loop(root, session_id)
            except Exception as exc:  # pragma: no cover - depends on operator runtime artifacts.
                refreshed_shadow = None
                shadow_refresh_error = str(exc)
            else:
                shadow_refresh_error = None
            shadow_fields = _shadow_runtime_collection_fields(root, session_id)
            if (
                not isinstance(refreshed_shadow, dict)
                or shadow_fields.get("paper_shadow_runtime_collection_status") != PAPER_SHADOW_RUNTIME_REFRESH_EXECUTED
            ):
                failed += 1
                blocked = build_runner_status_report(
                    root=root,
                    runner_id=runner_id,
                    session_id=session_id,
                    runner_status=RUNNER_STATUS_BLOCKED,
                    started_at_utc=started_at,
                    completed_cycle_count=completed,
                    failed_cycle_count=failed,
                    cycle_interval_seconds=cycle_interval_seconds,
                    loop_report=last_loop_report,
                    primary_blocker_code=shadow_fields.get("paper_shadow_primary_blocker_code")
                    or PAPER_SHADOW_RUNTIME_REFRESH_FAILED_BLOCKER_CODE,
                    primary_blocker_message=shadow_refresh_error
                    or "PAPER cycle passed, but paired non-live SHADOW runtime evidence was not refreshed.",
                    stop_reason="PAPER_SHADOW_RUNTIME_REFRESH_BLOCKED",
                    dashboard_open_result=dashboard_open_result,
                )
                _write_runner_status(status_path, blocked)
                _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
                if emit_console_status:
                    _emit_console_status(blocked)
                _append_log(
                    root,
                    session_id,
                    {
                        "event": "runner_blocked",
                        "reason": "PAPER_SHADOW_RUNTIME_REFRESH_BLOCKED",
                        "blocker_code": blocked.get("primary_blocker_code"),
                        "at": utc_now(),
                    },
                )
                dashboard_status_channel_final_status = "BLOCKED"
                return blocked
            _append_log(
                root,
                session_id,
                {
                    "event": "paper_shadow_runtime_refreshed",
                    "loop_id": cycle_loop_id,
                    "completed_cycle_count": completed,
                    "shadow_completed_cycle_count": shadow_fields.get("shadow_completed_cycle_count"),
                    "shadow_observation_count": shadow_fields.get("shadow_observation_count"),
                    "at": utc_now(),
                },
            )
            try:
                profitability_refresh = refresh_non_live_profitability_evidence_from_runtime(root, session_id)
            except Exception as exc:  # pragma: no cover - depends on operator runtime artifacts.
                profitability_refresh = {
                    "status": NON_LIVE_PROFITABILITY_REFRESH_BLOCKED,
                    "blocker_code": NON_LIVE_PROFITABILITY_REFRESH_FAILED_BLOCKER_CODE,
                    "message": str(exc),
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }
            if _non_live_profitability_refresh_should_stop_runner(profitability_refresh):
                failed += 1
                blocked = build_runner_status_report(
                    root=root,
                    runner_id=runner_id,
                    session_id=session_id,
                    runner_status=RUNNER_STATUS_BLOCKED,
                    started_at_utc=started_at,
                    completed_cycle_count=completed,
                    failed_cycle_count=failed,
                    cycle_interval_seconds=cycle_interval_seconds,
                    loop_report=last_loop_report,
                    primary_blocker_code=profitability_refresh.get("blocker_code")
                    or NON_LIVE_PROFITABILITY_REFRESH_FAILED_BLOCKER_CODE,
                    primary_blocker_message=str(
                        profitability_refresh.get("message")
                        or "PAPER cycle passed, but non-live profitability evidence refresh failed."
                    ),
                    stop_reason="NON_LIVE_PROFITABILITY_EVIDENCE_REFRESH_BLOCKED",
                    dashboard_open_result=dashboard_open_result,
                )
                _write_runner_status(status_path, blocked)
                _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
                if emit_console_status:
                    _emit_console_status(blocked)
                _append_log(
                    root,
                    session_id,
                    {
                        "event": "runner_blocked",
                        "reason": "NON_LIVE_PROFITABILITY_EVIDENCE_REFRESH_BLOCKED",
                        "blocker_code": blocked.get("primary_blocker_code"),
                        "at": utc_now(),
                    },
                )
                dashboard_status_channel_final_status = "BLOCKED"
                return blocked
            if profitability_refresh.get("status") == NON_LIVE_PROFITABILITY_REFRESH_BLOCKED:
                _append_log(
                    root,
                    session_id,
                    {
                        "event": "non_live_profitability_evidence_collecting_nonblocking",
                        "loop_id": cycle_loop_id,
                        "completed_cycle_count": completed,
                        "refresh_status": profitability_refresh.get("status"),
                        "blocker_code": profitability_refresh.get("blocker_code"),
                        "message": profitability_refresh.get("message"),
                        "at": utc_now(),
                    },
                )
            _append_log(
                root,
                session_id,
                {
                    "event": "non_live_profitability_evidence_refreshed",
                    "loop_id": cycle_loop_id,
                    "completed_cycle_count": completed,
                    "refresh_status": profitability_refresh.get("status"),
                    "runtime_sample_count": profitability_refresh.get("runtime_sample_count"),
                    "candidate_scorecard_candidate_id": profitability_refresh.get("candidate_scorecard_candidate_id"),
                    "candidate_scorecard_snapshot_status": profitability_refresh.get(
                        "candidate_scorecard_snapshot_status"
                    ),
                    "candidate_scorecard_ranking_eligible": profitability_refresh.get(
                        "candidate_scorecard_ranking_eligible"
                    ),
                    "strategy_mutation_compiler_status": profitability_refresh.get(
                        "strategy_mutation_compiler_status"
                    ),
                    "strategy_mutation_compiler_blocker_code": profitability_refresh.get(
                        "strategy_mutation_compiler_blocker_code"
                    ),
                    "strategy_mutation_compiler_candidate_id": profitability_refresh.get(
                        "strategy_mutation_compiler_candidate_id"
                    ),
                    "strategy_mutation_id": profitability_refresh.get("strategy_mutation_id"),
                    "paper_shadow_evidence_validation_status": profitability_refresh.get(
                        "paper_shadow_evidence_validation_status"
                    ),
                    "paper_shadow_evidence_actionability_status": profitability_refresh.get(
                        "paper_shadow_evidence_actionability_status"
                    ),
                    "at": utc_now(),
                },
            )
            retention = apply_runner_artifact_retention(
                root=root,
                session_id=session_id,
                max_active_artifacts_per_group=retention_max_active_artifacts_per_group,
                max_uncompacted_archive_batches=retention_max_uncompacted_archive_batches,
                log_max_bytes=retention_log_max_bytes,
                disk_pressure_max_runtime_bytes=disk_pressure_max_runtime_bytes,
            )
            retention_validation = validate_upbit_paper_long_runner_retention_manifest(retention)
            if retention_validation.get("status") != "PASS":
                failed += 1
                blocked = build_runner_status_report(
                    root=root,
                    runner_id=runner_id,
                    session_id=session_id,
                    runner_status=RUNNER_STATUS_BLOCKED,
                    started_at_utc=started_at,
                    completed_cycle_count=completed,
                    failed_cycle_count=failed,
                    cycle_interval_seconds=cycle_interval_seconds,
                    loop_report=last_loop_report,
                    primary_blocker_code=retention_validation.get("blocker_code") or DISK_PRESSURE_BLOCKER_CODE,
                    primary_blocker_message="Runtime artifact retention or disk pressure guard blocked continued PAPER execution.",
                    stop_reason="RUNTIME_DISK_PRESSURE_BLOCKED",
                    dashboard_open_result=dashboard_open_result,
                )
                _write_runner_status(status_path, blocked)
                _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
                if emit_console_status:
                    _emit_console_status(blocked)
                _append_log(root, session_id, {"event": "runner_blocked", "reason": "RUNTIME_DISK_PRESSURE_BLOCKED", "at": utc_now()})
                dashboard_status_channel_final_status = "BLOCKED"
                return blocked
            _append_log(
                root,
                session_id,
                {
                    "event": "paper_cycle_completed",
                    "loop_id": cycle_loop_id,
                    "completed_cycle_count": completed,
                    "at": utc_now(),
                },
            )
            post_cycle_next_eta_text = None
            if cycle_interval_seconds:
                post_cycle_next_eta = datetime.now(timezone.utc).timestamp() + cycle_interval_seconds
                post_cycle_next_eta_text = (
                    datetime.fromtimestamp(post_cycle_next_eta, tz=timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
            post_cycle_running = build_runner_status_report(
                root=root,
                runner_id=runner_id,
                session_id=session_id,
                runner_status=RUNNER_STATUS_RUNNING,
                started_at_utc=started_at,
                completed_cycle_count=completed,
                failed_cycle_count=failed,
                cycle_interval_seconds=cycle_interval_seconds,
                loop_report=last_loop_report,
                next_cycle_eta=post_cycle_next_eta_text,
                dashboard_open_result=dashboard_open_result,
            )
            _write_runner_status(status_path, post_cycle_running)
            if runner_stop_file_path(root, session_id).exists():
                return _finalize_runner_stop_file(
                    root=root,
                    session_id=session_id,
                    status_path=status_path,
                    runner_id=runner_id,
                    started_at_utc=started_at,
                    completed_cycle_count=completed,
                    failed_cycle_count=failed,
                    cycle_interval_seconds=cycle_interval_seconds,
                    loop_report=last_loop_report,
                    refresh_dashboard=refresh_dashboard,
                    emit_console_status=emit_console_status,
                    dashboard_open_result=dashboard_open_result,
                )
            if refresh_dashboard:
                try:
                    _maybe_refresh_dashboard(root, session_id=session_id)
                except Exception as exc:  # pragma: no cover - exercised by operator environments.
                    if _dashboard_refresh_error_is_nonblocking_writer_unavailable(
                        exc,
                        root=root,
                        session_id=session_id,
                    ):
                        _append_log(
                            root,
                            session_id,
                            {
                                "event": "dashboard_refresh_writer_truth_unavailable_nonblocking",
                                "reason": "AUDITED_CURRENT_EVIDENCE_WRITER_UNAVAILABLE",
                                "error": str(exc),
                                "completed_cycle_count": completed,
                                "at": utc_now(),
                                "live_order_ready": False,
                                "live_order_allowed": False,
                                "can_live_trade": False,
                                "scale_up_allowed": False,
                            },
                        )
                    else:
                        drifted, drift_field, drift_path = _runtime_current_artifacts_have_permission_drift(
                            root,
                            session_id,
                        )
                        blocker_code = "LIVE_FINAL_GUARD_FAILED" if drifted else "DASHBOARD_REFRESH_FAILED"
                        blocker_message = (
                            f"Dashboard refresh detected {drift_field}=true in {drift_path}."
                            if drifted
                            else str(exc)
                        )
                        failed += 1
                        blocked = build_runner_status_report(
                            root=root,
                            runner_id=runner_id,
                            session_id=session_id,
                            runner_status=RUNNER_STATUS_BLOCKED,
                            started_at_utc=started_at,
                            completed_cycle_count=completed,
                            failed_cycle_count=failed,
                            cycle_interval_seconds=cycle_interval_seconds,
                            loop_report=last_loop_report,
                            primary_blocker_code=blocker_code,
                            primary_blocker_message=blocker_message,
                            stop_reason="DASHBOARD_REFRESH_BLOCKED",
                            dashboard_open_result=dashboard_open_result,
                        )
                        _write_runner_status(status_path, blocked)
                        _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
                        if emit_console_status:
                            _emit_console_status(blocked)
                        dashboard_status_channel_final_status = "BLOCKED"
                        return blocked
            if cycle_interval_seconds:
                next_eta = datetime.now(timezone.utc).timestamp() + cycle_interval_seconds
                next_eta_text = (
                    datetime.fromtimestamp(next_eta, tz=timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
                running = build_runner_status_report(
                    root=root,
                    runner_id=runner_id,
                    session_id=session_id,
                    runner_status=RUNNER_STATUS_RUNNING,
                    started_at_utc=started_at,
                    completed_cycle_count=completed,
                    failed_cycle_count=failed,
                    cycle_interval_seconds=cycle_interval_seconds,
                    loop_report=last_loop_report,
                    next_cycle_eta=next_eta_text,
                    dashboard_open_result=dashboard_open_result,
                )
                _write_runner_status(status_path, running)
                _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
                if emit_console_status:
                    _emit_console_status(running)
                if _sleep_until_next_cycle_or_stop_requested(
                    root=root,
                    session_id=session_id,
                    cycle_interval_seconds=cycle_interval_seconds,
                    sleep_fn=sleep_fn,
                ):
                    return _finalize_runner_stop_file(
                        root=root,
                        session_id=session_id,
                        status_path=status_path,
                        runner_id=runner_id,
                        started_at_utc=started_at,
                        completed_cycle_count=completed,
                        failed_cycle_count=failed,
                        cycle_interval_seconds=cycle_interval_seconds,
                        loop_report=last_loop_report,
                        refresh_dashboard=refresh_dashboard,
                        emit_console_status=emit_console_status,
                        dashboard_open_result=dashboard_open_result,
                    )
    except KeyboardInterrupt:
        final = build_runner_status_report(
            root=root,
            runner_id=runner_id,
            session_id=session_id,
            runner_status=RUNNER_STATUS_STOPPED,
            started_at_utc=started_at,
            completed_cycle_count=completed,
            failed_cycle_count=failed,
            cycle_interval_seconds=cycle_interval_seconds,
            loop_report=last_loop_report,
            stop_reason="KEYBOARD_INTERRUPT",
            dashboard_open_result=dashboard_open_result,
        )
        _write_runner_status(status_path, final)
        _refresh_dashboard_after_runner_status(root, session_id, refresh_dashboard=refresh_dashboard)
        if emit_console_status:
            _emit_console_status(final)
        _append_log(root, session_id, {"event": "runner_stopped", "reason": "KEYBOARD_INTERRUPT", "at": utc_now()})
        return final
    finally:
        stop_runner_dashboard_status_channel(
            dashboard_status_channel_handle,
            root=root,
            session_id=session_id,
            final_status=dashboard_status_channel_final_status,
            grace_seconds=max(0.0, dashboard_status_channel_shutdown_grace_seconds),
        )
        release_runner_lock(lock)


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _optional_int_env(name: str) -> int | None:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return None
    return int(raw)


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _should_hold_on_exit(report: dict[str, Any]) -> bool:
    raw = os.environ.get("TRADER1_UPBIT_PAPER_HOLD_ON_EXIT")
    if raw is not None:
        return raw.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _hold_console_on_exit_if_needed(report: dict[str, Any], *, already_running: bool = False) -> None:
    if not _should_hold_on_exit(report):
        return
    if already_running:
        message = (
            "UPBIT_PAPER is already running in the background. "
            "Use STOP_UPBIT_PAPER.py to stop it. Press Enter to close this duplicate window."
        )
    elif report.get("runner_status") == RUNNER_STATUS_LOCKED:
        message = (
            "UPBIT_PAPER did not start because another runner lock is active. "
            "Check runner_status_path above. Press Enter to close this window."
        )
    else:
        message = (
            "UPBIT_PAPER stopped. Check runner_status_path above. "
            "Press Enter to close this window."
        )
    if sys.stdin is not None and sys.stdin.isatty():
        try:
            input(message)
        except EOFError:
            pass
    else:
        print(message, flush=True)


def _canonical_runner_already_running(root: Path, session_id: str = DEFAULT_SESSION_ID) -> bool:
    canonical = _read_json(runner_status_path(root, session_id))
    if not isinstance(canonical, dict):
        return False
    if validate_upbit_paper_long_runner_status_report(canonical).get("status") != "PASS":
        return False
    liveness = runner_lock_liveness_from_status_report(canonical)
    return (
        canonical.get("runner_status") == RUNNER_STATUS_RUNNING
        and canonical.get("running") is True
        and liveness.get("runner_liveness_proven") is True
    )


def root_upbit_paper_stop_main(root: Path = ROOT) -> int:
    wait_timeout = _float_env("TRADER1_UPBIT_PAPER_STOP_WAIT_SECONDS", 0.0)
    poll_interval = _float_env("TRADER1_UPBIT_PAPER_STOP_POLL_SECONDS", DEFAULT_DASHBOARD_STATUS_CHANNEL_STOP_POLL_SECONDS)
    report = request_upbit_paper_runner_stop(
        root=root,
        wait_timeout_seconds=wait_timeout,
        poll_interval_seconds=poll_interval,
    )
    print(f"TRADER_1 STOP_UPBIT_PAPER status={report.get('stop_request_status')}", flush=True)
    print(f"runner_status_path={report.get('runner_status_path')}", flush=True)
    print(f"stop_file_path={report.get('stop_file_path')}", flush=True)
    print(f"stop_request_report_path={report.get('stop_request_report_path')}", flush=True)
    print(f"runner_pid={report.get('runner_pid_before')}", flush=True)
    print(f"stop_file_written={str(report.get('stop_file_written') is True).lower()}", flush=True)
    print(f"stop_confirmed={str(report.get('stop_confirmed') is True).lower()}", flush=True)
    if report.get("primary_blocker_code"):
        print(f"primary_blocker_code={report.get('primary_blocker_code')}", flush=True)
        print(str(report.get("primary_blocker_message") or ""), flush=True)
    print("live_order_ready=false live_order_allowed=false can_live_trade=false scale_up_allowed=false", flush=True)
    if _bool_env("TRADER1_UPBIT_PAPER_STOP_HOLD_ON_EXIT", False) and sys.stdin is not None and sys.stdin.isatty():
        try:
            input("STOP_UPBIT_PAPER finished. Press Enter to close this window.")
        except EOFError:
            pass
    return 0 if report.get("stop_request_status") in {"STOP_CONFIRMED", "NO_RUNNING_RUNNER"} else 1


def root_upbit_paper_long_runner_main(root: Path = ROOT) -> int:
    if _bool_env("TRADER1_UPBIT_PAPER_SAFE_CHECK_ONLY", False):
        from trader1.runtime.boot.safe_launcher import root_operator_launcher_main

        return int(root_operator_launcher_main("UPBIT_PAPER", root=root))

    max_cycles = _optional_int_env("TRADER1_UPBIT_PAPER_RUNNER_MAX_CYCLES")
    interval = _float_env("TRADER1_UPBIT_PAPER_RUNNER_INTERVAL_SECONDS", DEFAULT_CYCLE_INTERVAL_SECONDS)
    use_public_rest = _bool_env("TRADER1_UPBIT_PAPER_USE_PUBLIC_REST", True)
    timeout = _float_env("TRADER1_UPBIT_PAPER_PUBLIC_TIMEOUT_SECONDS", 3.0)
    refresh_dashboard = _bool_env("TRADER1_UPBIT_PAPER_REFRESH_DASHBOARD", True)
    open_dashboard = _bool_env("TRADER1_UPBIT_PAPER_OPEN_DASHBOARD", True)
    dashboard_status_channel_enabled = _bool_env("TRADER1_UPBIT_PAPER_DASHBOARD_STATUS_CHANNEL", True)
    dashboard_status_channel_shutdown_grace_seconds = _float_env(
        "TRADER1_UPBIT_PAPER_DASHBOARD_STATUS_CHANNEL_GRACE_SECONDS",
        DEFAULT_DASHBOARD_STATUS_CHANNEL_SHUTDOWN_GRACE_SECONDS,
    )
    retention_max_active = _int_env(
        "TRADER1_UPBIT_PAPER_RETENTION_MAX_ACTIVE_ARTIFACTS_PER_GROUP",
        DEFAULT_RETENTION_MAX_ACTIVE_ARTIFACTS_PER_GROUP,
    )
    retention_max_uncompacted_archives = _int_env(
        "TRADER1_UPBIT_PAPER_RETENTION_MAX_UNCOMPACTED_ARCHIVE_BATCHES",
        DEFAULT_RETENTION_MAX_UNCOMPACTED_ARCHIVE_BATCHES,
    )
    retention_log_max_bytes = _int_env("TRADER1_UPBIT_PAPER_LOG_MAX_BYTES", DEFAULT_RUNNER_LOG_MAX_BYTES)
    disk_pressure_max_bytes = _int_env(
        "TRADER1_UPBIT_PAPER_RUNTIME_DISK_PRESSURE_MAX_BYTES",
        DEFAULT_RUNTIME_DISK_PRESSURE_MAX_BYTES,
    )
    root_is_default_workspace = Path(root).resolve() == ROOT.resolve()
    background_launch = (
        not _bool_env(FOREGROUND_RUNNER_ENV, False)
        and _bool_env(BACKGROUND_LAUNCH_ENV, root_is_default_workspace)
    )
    canonical_running_before_start = _canonical_runner_already_running(root)
    if canonical_running_before_start:
        print("TRADER_1 UPBIT_PAPER background_runner_active=true", flush=True)
        print(f"runner_status_path={runner_status_path(root)}", flush=True)
        print(f"stop_launcher_path={root / 'STOP_UPBIT_PAPER.py'}", flush=True)
        print(f"stop_file_path={runner_stop_file_path(root)}", flush=True)
        print("operator_console_auto_closes=true", flush=True)
        print("dashboard_close_does_not_stop_runner=true console_close_does_not_stop_runner=true", flush=True)
    if (
        not canonical_running_before_start
        and not _bool_env("TRADER1_UPBIT_PAPER_RESPECT_EXISTING_STOP_FILE", False)
    ):
        start_reconciliation = clear_runner_stop_file_for_operator_start(
            root,
            DEFAULT_SESSION_ID,
            reason="ROOT_OPERATOR_START",
        )
        if start_reconciliation.get("stop_file_cleared"):
            print("TRADER_1 UPBIT_PAPER stale_stop_file_cleared=true", flush=True)
            print(f"stop_file_path={start_reconciliation.get('stop_file_path')}", flush=True)
        if start_reconciliation.get("status") != "PASS":
            print(
                f"TRADER_1 UPBIT_PAPER start_blocked={start_reconciliation.get('blocker_code')}",
                flush=True,
            )
            print(str(start_reconciliation.get("blocker_message") or ""), flush=True)
            print("live_order_ready=false live_order_allowed=false can_live_trade=false scale_up_allowed=false")
            return 1
    dashboard_open_result: DashboardOpenResult | None = None
    dashboard_opened = False
    dashboard_refresh_error: str | None = None
    if refresh_dashboard and not background_launch:
        try:
            _maybe_refresh_dashboard(root)
        except Exception as exc:
            dashboard_refresh_error = str(exc)
            print(f"TRADER_1 UPBIT_PAPER dashboard_refresh_failed={exc}", flush=True)
    if open_dashboard and not background_launch:
        if dashboard_refresh_error:
            dashboard_open_result = dashboard_preopen_refresh_failed_result(
                root,
                DEFAULT_SESSION_ID,
                error=dashboard_refresh_error,
            )
        else:
            dashboard_open_result = open_runner_dashboard_result(root)
        dashboard_opened = dashboard_open_result.opened
        print(f"TRADER_1 UPBIT_PAPER dashboard_opened={str(dashboard_opened).lower()}", flush=True)
        print(f"dashboard_open_method={dashboard_open_result.method}", flush=True)
        print(f"dashboard_open_target={dashboard_open_result.target}", flush=True)
        if dashboard_open_result.blocker_code:
            print(f"dashboard_open_blocker_code={dashboard_open_result.blocker_code}", flush=True)
            print(f"dashboard_open_blocker_message={dashboard_open_result.blocker_message}", flush=True)
        print(f"dashboard_path={runner_dashboard_path(root)}", flush=True)
    if background_launch and canonical_running_before_start:
        if refresh_dashboard:
            try:
                _maybe_refresh_dashboard(root)
            except Exception as exc:
                dashboard_refresh_error = str(exc)
                print(f"TRADER_1 UPBIT_PAPER dashboard_refresh_failed={exc}", flush=True)
        if open_dashboard:
            if dashboard_refresh_error:
                dashboard_open_result = dashboard_preopen_refresh_failed_result(
                    root,
                    DEFAULT_SESSION_ID,
                    error=dashboard_refresh_error,
                )
            else:
                dashboard_open_result = open_runner_dashboard_result(root)
            status_after_open = _read_json(runner_status_path(root))
            if isinstance(status_after_open, dict):
                try:
                    _persist_dashboard_open_result(status_after_open, dashboard_open_result, root=root)
                except Exception as exc:
                    print(f"TRADER_1 UPBIT_PAPER dashboard_status_persist_failed={exc}", flush=True)
            dashboard_opened = dashboard_open_result.opened
            print(f"TRADER_1 UPBIT_PAPER dashboard_opened={str(dashboard_opened).lower()}", flush=True)
            print(f"dashboard_open_method={dashboard_open_result.method}", flush=True)
            print(f"dashboard_open_target={dashboard_open_result.target}", flush=True)
            if dashboard_open_result.blocker_code:
                print(f"dashboard_open_blocker_code={dashboard_open_result.blocker_code}", flush=True)
                print(f"dashboard_open_blocker_message={dashboard_open_result.blocker_message}", flush=True)
            print(f"dashboard_path={runner_dashboard_path(root)}", flush=True)
        print("TRADER_1 UPBIT_PAPER already_running=true", flush=True)
        print("background_runner_active=true", flush=True)
        print("operator_console_auto_closes=true", flush=True)
        print(f"stop_launcher_path={root / 'STOP_UPBIT_PAPER.py'}", flush=True)
        print(f"stop_file_path={runner_stop_file_path(root)}", flush=True)
        print("dashboard_is_status_only=true dashboard_close_does_not_stop_runner=true", flush=True)
        print("live_order_ready=false live_order_allowed=false can_live_trade=false scale_up_allowed=false", flush=True)
        return 0
    if background_launch:
        launch_report = start_upbit_paper_background_runner(
            root,
            DEFAULT_SESSION_ID,
            dashboard_open_result=dashboard_open_result,
        )
        if launch_report.get("background_launch_status") == "STARTED" and refresh_dashboard:
            deadline = time.monotonic() + 10.0
            while time.monotonic() < deadline:
                status_after_launch = _read_json(runner_status_path(root))
                if (
                    isinstance(status_after_launch, dict)
                    and status_after_launch.get("runner_status") == RUNNER_STATUS_RUNNING
                    and status_after_launch.get("runner_lock_pid") == launch_report.get("runner_pid")
                ):
                    break
                time.sleep(0.1)
            try:
                _maybe_refresh_dashboard(root)
            except Exception as exc:
                dashboard_refresh_error = str(exc)
                print(f"TRADER_1 UPBIT_PAPER dashboard_refresh_failed={exc}", flush=True)
        if open_dashboard:
            if dashboard_open_result is None and dashboard_refresh_error:
                dashboard_open_result = dashboard_preopen_refresh_failed_result(
                    root,
                    DEFAULT_SESSION_ID,
                    error=dashboard_refresh_error,
                )
            elif dashboard_open_result is None or (
                dashboard_open_result.opened is False
                and dashboard_open_result.blocker_code == DASHBOARD_PREOPEN_REFRESH_FAILED_BLOCKER_CODE
                and dashboard_refresh_error is None
            ):
                dashboard_open_result = open_runner_dashboard_result(
                    root,
                    expected_runner_pid=launch_report.get("runner_pid")
                    if isinstance(launch_report.get("runner_pid"), int)
                    else None,
                )
            if dashboard_open_result is not None:
                status_after_launch = _read_json(runner_status_path(root))
                if isinstance(status_after_launch, dict):
                    try:
                        _persist_dashboard_open_result(status_after_launch, dashboard_open_result, root=root)
                    except Exception as exc:
                        print(f"TRADER_1 UPBIT_PAPER dashboard_status_persist_failed={exc}", flush=True)
            print(f"TRADER_1 UPBIT_PAPER dashboard_opened={str(dashboard_open_result.opened).lower()}", flush=True)
            print(f"dashboard_open_method={dashboard_open_result.method}", flush=True)
            print(f"dashboard_open_target={dashboard_open_result.target}", flush=True)
            if dashboard_open_result.blocker_code:
                print(f"dashboard_open_blocker_code={dashboard_open_result.blocker_code}", flush=True)
                print(f"dashboard_open_blocker_message={dashboard_open_result.blocker_message}", flush=True)
            launch_report["dashboard_open_attempted"] = dashboard_open_result.attempted
            launch_report["dashboard_opened"] = dashboard_open_result.opened
            launch_report["dashboard_open_method"] = dashboard_open_result.method
            launch_report["dashboard_open_target"] = dashboard_open_result.target
            launch_report["background_launch_hash"] = upbit_paper_background_launch_hash(launch_report)
            durable_atomic_write_json(runner_background_launch_report_path(root), launch_report)
        print(
            f"TRADER_1 UPBIT_PAPER background_launch_status={launch_report.get('background_launch_status')}",
            flush=True,
        )
        print(
            f"background_runner_started={str(launch_report.get('background_runner_started') is True).lower()}",
            flush=True,
        )
        print(f"runner_pid={launch_report.get('runner_pid')}", flush=True)
        print(f"runner_status_path={launch_report.get('runner_status_path')}", flush=True)
        print(f"dashboard_path={launch_report.get('dashboard_path')}", flush=True)
        print(f"stop_launcher_path={launch_report.get('stop_launcher_path')}", flush=True)
        print("operator_console_auto_closes=true", flush=True)
        print("dashboard_close_does_not_stop_runner=true console_close_does_not_stop_runner=true", flush=True)
        if launch_report.get("primary_blocker_code"):
            print(f"primary_blocker_code={launch_report.get('primary_blocker_code')}", flush=True)
            print(str(launch_report.get("primary_blocker_message") or ""), flush=True)
        print("live_order_ready=false live_order_allowed=false can_live_trade=false scale_up_allowed=false", flush=True)
        return 0 if launch_report.get("background_launch_status") == "STARTED" else 1
    report = run_upbit_paper_long_running_runner(
        root=root,
        cycle_interval_seconds=interval,
        max_cycles=max_cycles,
        attempt_public_symbol_discovery=use_public_rest,
        attempt_network_market_data=use_public_rest,
        public_discovery_timeout_seconds=timeout,
        refresh_dashboard=refresh_dashboard,
        emit_console_status=True,
        dashboard_open_result=dashboard_open_result,
        dashboard_status_channel_enabled=dashboard_status_channel_enabled,
        dashboard_status_channel_shutdown_grace_seconds=dashboard_status_channel_shutdown_grace_seconds,
        retention_max_active_artifacts_per_group=retention_max_active,
        retention_max_uncompacted_archive_batches=retention_max_uncompacted_archives,
        retention_log_max_bytes=retention_log_max_bytes,
        disk_pressure_max_runtime_bytes=disk_pressure_max_bytes,
        paper_trade_intent_inputs_provider=default_candidate_generation_paper_intent_provider,
    )
    if dashboard_open_result is not None:
        report = _persist_dashboard_open_result(report, dashboard_open_result, root=root)
    print(f"TRADER_1 UPBIT_PAPER runner_status={report.get('runner_status')}")
    print(f"runner_status_path={report.get('runner_status_path')}")
    print(f"dashboard_path={report.get('dashboard_path')}")
    print(f"dashboard_opened={str(report.get('dashboard_opened') is True).lower()}")
    if dashboard_open_result is not None:
        print(f"dashboard_open_method={dashboard_open_result.method}")
        print(f"dashboard_open_target={dashboard_open_result.target}")
        if dashboard_open_result.blocker_code:
            print(f"dashboard_open_blocker_code={dashboard_open_result.blocker_code}")
            print(f"dashboard_open_blocker_message={dashboard_open_result.blocker_message}")
    elif report.get("dashboard_open_attempted") is True:
        print(f"dashboard_open_method={report.get('dashboard_open_method')}")
        print(f"dashboard_open_target={report.get('dashboard_open_target')}")
        if report.get("dashboard_open_blocker_code"):
            print(f"dashboard_open_blocker_code={report.get('dashboard_open_blocker_code')}")
            print(f"dashboard_open_blocker_message={report.get('dashboard_open_blocker_message')}")
    print("live_order_ready=false live_order_allowed=false can_live_trade=false scale_up_allowed=false")
    already_running = report.get("runner_status") == RUNNER_STATUS_LOCKED and _canonical_runner_already_running(root)
    if already_running:
        print("already_running=true")
        print("background_runner_active=true")
        print(f"stop_launcher_path={root / 'STOP_UPBIT_PAPER.py'}")
        print(f"stop_file_path={runner_stop_file_path(root)}")
        print("dashboard_is_status_only=true dashboard_close_does_not_stop_runner=true")
    _hold_console_on_exit_if_needed(report, already_running=already_running)
    if report.get("runner_status") in {RUNNER_STATUS_STOPPED}:
        return 0
    if already_running:
        return 0
    return 1
