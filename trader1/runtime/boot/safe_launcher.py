from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import webbrowser
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

from trader1.adapters.binance.surface import binance_surface_blocker
from trader1.config.config_schema import build_runtime_config, validate_runtime_config
from trader1.core.ledger.restart_recovery import validate_restart_recovery_report
from trader1.dashboard.read_only_dashboard import (
    build_read_only_dashboard_shell,
    render_dashboard_html,
    validate_read_only_dashboard_shell,
)
from trader1.dashboard.summary_writer import build_summary_shell
from trader1.runtime.boot.startup_probe import build_startup_probe
from trader1.runtime.health.heartbeat import build_heartbeat, heartbeat_hash
from trader1.runtime.health.runtime_resource_pressure import inspect_runtime_resource_pressure
from trader1.runtime.health.stability_history import append_stability_history, validate_stability_history
from trader1.runtime.ledger.paper_ledger_rollup import validate_paper_ledger_rollup_report
from trader1.runtime.paper.operational_cycle import validate_paper_operation_gate_report
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    validate_upbit_paper_persistent_loop_report,
    validate_upbit_paper_runtime_recovery_guard_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_blocker_rollup import (
    validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_reconciliation_review_guidance import (
    validate_upbit_paper_post_rerun_operator_reconciliation_review_guidance_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_reconciliation_queue import (
    validate_upbit_paper_post_rerun_operator_reconciliation_queue_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_resolution_audit import (
    validate_upbit_paper_post_rerun_operator_resolution_audit_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_resolution_current_evidence_closure import (
    validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_current_evidence_closure_recheck import (
    validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_repair_path import (
    validate_upbit_paper_post_rerun_reconciliation_repair_path_report,
)
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import (
    validate_upbit_paper_post_repair_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_repair_operator_queue import (
    validate_upbit_paper_repair_operator_queue_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_post_regeneration_reconciliation import (
    validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation_operator_queue_closure import (
    validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard import (
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_dry_run import (
    validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report,
)
from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    validate_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.runtime.paper.upbit_paper_runtime import validate_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_public_rest_continuity_history import validate_upbit_public_rest_continuity_history_report
from trader1.runtime.portfolio.paper_portfolio import build_initial_paper_portfolio_snapshot
from trader1.runtime.readiness.readiness_surface import build_readiness_surface
from trader1.runtime.reconciliation.reconciliation import validate_reconciliation_report
from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    validate_shadow_observation_actual_runtime_harness_report,
)
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    validate_shadow_observation_persistent_runtime_report,
)
from trader1.research.shadow.shadow_observation_runtime_orchestration import (
    validate_shadow_observation_runtime_orchestration_report,
)
from tools.run_upbit_paper_runtime_evidence_collection_profile import (
    validate_upbit_paper_runtime_evidence_collection_profile_report,
)


ROOT = Path(__file__).resolve().parents[3]
ROOT_LAUNCHER_REPORT_SCHEMA_ID = "trader1.root_launcher_report.v1"
ORDER_AFFECTING_FINAL_ACTIONS = {
    "ENTER_LONG",
    "ENTER_SHORT",
    "EXIT_POSITION",
    "REDUCE_POSITION",
    "CANCEL_ORDER",
    "HOLD_POSITION",
}
DEFAULT_NON_INTERACTIVE_HEARTBEAT_TICKS = 1
DEFAULT_INTERACTIVE_HEARTBEAT_TICKS: int | None = None
DEFAULT_INTERACTIVE_HEARTBEAT_INTERVAL_SECONDS = 10.0
ROOT_OPERATOR_HEARTBEAT_TICKS_ENV = "TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS"
ROOT_OPERATOR_HEARTBEAT_INTERVAL_ENV = "TRADER1_ROOT_OPERATOR_HEARTBEAT_INTERVAL_SECONDS"
RUNTIME_WRITE_LOCK_FILENAME = ".runtime_write.lock"
RUNTIME_WRITE_LOCK_TIMEOUT_SECONDS = 5.0
RUNTIME_WRITE_LOCK_STALE_SECONDS = 30.0


@dataclass(frozen=True)
class LauncherSpec:
    launcher_name: str
    exchange: str
    market_type: str
    mode: str
    market_type_source: str
    session_id: str


@dataclass(frozen=True)
class LauncherReportValidationResult:
    status: str
    message: str
    blocker_code: str | None


ROOT_LAUNCHER_SPECS = {
    "UPBIT_PAPER": LauncherSpec("UPBIT_PAPER", "UPBIT", "KRW_SPOT", "PAPER", "NOT_APPLICABLE", "mvp1_upbit_paper_launcher"),
    "UPBIT_LIVE": LauncherSpec("UPBIT_LIVE", "UPBIT", "KRW_SPOT", "LIVE", "NOT_APPLICABLE", "mvp1_upbit_live_launcher"),
    "BINANCE_PAPER": LauncherSpec("BINANCE_PAPER", "BINANCE", "SPOT", "PAPER", "LAUNCHER_INTERNAL_UI", "mvp1_binance_paper_launcher"),
    "BINANCE_LIVE": LauncherSpec("BINANCE_LIVE", "BINANCE", "SPOT", "LIVE", "LAUNCHER_INTERNAL_UI", "mvp1_binance_live_launcher"),
}


def _launcher_surface_blocker(exchange: str, market_type: str, mode: str) -> tuple[str, str] | None:
    if exchange != "BINANCE":
        return None
    return binance_surface_blocker(market_type, mode)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _fsync_parent_directory(path: Path) -> None:
    try:
        directory_fd = os.open(str(path.parent), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(value, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)
        _fsync_parent_directory(path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)
        _fsync_parent_directory(path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def _runtime_lock_owner_pid(lock_path: Path) -> int | None:
    try:
        first_line = lock_path.read_text(encoding="utf-8").splitlines()[0]
    except (FileNotFoundError, IndexError, OSError, UnicodeDecodeError):
        return None
    pid_text = first_line.split(":", 1)[0]
    try:
        pid = int(pid_text)
    except ValueError:
        return None
    return pid if pid > 0 else None


def _process_is_running(pid: int) -> bool:
    if pid == os.getpid():
        return True
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@contextmanager
def runtime_write_lock(
    runtime_dir: Path,
    *,
    timeout_seconds: float = RUNTIME_WRITE_LOCK_TIMEOUT_SECONDS,
    stale_seconds: float = RUNTIME_WRITE_LOCK_STALE_SECONDS,
):
    runtime_dir.mkdir(parents=True, exist_ok=True)
    lock_path = runtime_dir / RUNTIME_WRITE_LOCK_FILENAME
    token = f"{os.getpid()}:{time.time_ns()}"
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, f"{token}\nacquired_at_utc={utc_now()}\n".encode("utf-8"))
            finally:
                os.close(fd)
            break
        except FileExistsError:
            try:
                age_seconds = time.time() - lock_path.stat().st_mtime
                if age_seconds > stale_seconds:
                    owner_pid = _runtime_lock_owner_pid(lock_path)
                    if owner_pid is not None and _process_is_running(owner_pid):
                        if time.monotonic() >= deadline:
                            raise RuntimeError(f"runtime artifact writer lock is busy: {lock_path}")
                        time.sleep(0.05)
                        continue
                    lock_path.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise RuntimeError(f"runtime artifact writer lock is busy: {lock_path}")
            time.sleep(0.05)
    try:
        yield lock_path
    finally:
        try:
            current = lock_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            current = ""
        if current.startswith(token):
            lock_path.unlink(missing_ok=True)


def schema_bundle_hash() -> str:
    return sha256_json(
        {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))}
    )


def source_identity_files() -> list[Path]:
    files: list[Path] = []
    for root in (ROOT / "trader1", ROOT / "contracts"):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT).as_posix()
            if "__pycache__" in path.parts:
                continue
            if relative.startswith("contracts/generated/"):
                continue
            if relative == "contracts/security/source_bundle_manifest.json":
                continue
            files.append(path)
    for filename in (
        "TRADER_1.md",
        "AGENTS.md",
        "pyproject.toml",
        "existing_code_audit.md",
        "UPBIT_PAPER.py",
        "UPBIT_LIVE.py",
        "BINANCE_PAPER.py",
        "BINANCE_LIVE.py",
    ):
        path = ROOT / filename
        if path.exists():
            files.append(path)
    return sorted(set(files))


def source_tree_hash() -> str:
    return sha256_json(
        {
            path.relative_to(ROOT).as_posix(): sha256_file(path)
            for path in source_identity_files()
        }
    )


def authority_hashes() -> dict[str, str]:
    return {
        "trader1_sha256": sha256_file(ROOT / "TRADER_1.md"),
        "agents_sha256": sha256_file(ROOT / "AGENTS.md"),
    }


def launcher_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("report_hash", None)
    return sha256_json(payload)


def build_launcher_report(launcher_name: str) -> dict[str, Any]:
    if launcher_name not in ROOT_LAUNCHER_SPECS:
        raise ValueError(f"unknown launcher: {launcher_name}")
    spec = ROOT_LAUNCHER_SPECS[launcher_name]
    registry = load_json(ROOT / "contracts" / "registry.yaml")
    registry_hash = sha256_file(ROOT / "contracts" / "registry.yaml")
    schemas_hash = schema_bundle_hash()
    sources_hash = source_tree_hash()
    config = build_runtime_config(
        exchange=spec.exchange,
        market_type=spec.market_type,
        mode=spec.mode,
        session_id=spec.session_id,
        registry_hash=registry_hash,
        market_type_source=spec.market_type_source,
    )
    config_result = validate_runtime_config(config, registry, expected_registry_hash=registry_hash)
    startup_probe = build_startup_probe(
        exchange=spec.exchange,
        market_type=spec.market_type,
        mode=spec.mode,
        session_id=spec.session_id,
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schemas_hash,
        source_tree_hash=sources_hash,
        ledger_write_status=None,
    )
    heartbeat = build_heartbeat(
        exchange=spec.exchange,
        market_type=spec.market_type,
        mode=spec.mode,
        session_id=spec.session_id,
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schemas_hash,
        source_tree_hash=sources_hash,
    )
    readiness = build_readiness_surface(
        authority=authority_hashes(),
        exchange=spec.exchange,
        market_type=spec.market_type,
        mode=spec.mode,
        session_id=spec.session_id,
        registry_hash=registry_hash,
        schema_bundle_hash=schemas_hash,
        source_tree_hash=sources_hash,
    )
    summary = build_summary_shell(
        exchange=spec.exchange,
        market_type=spec.market_type,
        mode=spec.mode,
        session_id=spec.session_id,
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness,
    )
    surface_blocker = _launcher_surface_blocker(spec.exchange, spec.market_type, spec.mode)
    blocking_reason = surface_blocker[0] if surface_blocker else summary["blocking_reason"]
    next_action = surface_blocker[1] if surface_blocker else "launcher emitted safe boot report only"
    report = {
        "schema_id": ROOT_LAUNCHER_REPORT_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "launcher_name": spec.launcher_name,
        "exchange": spec.exchange,
        "market_type": spec.market_type,
        "mode": spec.mode,
        "session_id": spec.session_id,
        "market_type_source": spec.market_type_source,
        "config_hash": config["config_hash"],
        "registry_hash": registry_hash,
        "schema_bundle_hash": schemas_hash,
        "source_tree_hash": sources_hash,
        "config_status": config_result.status,
        "startup_probe_status": "PASS" if startup_probe["startup_probe_passed"] else "BLOCKED",
        "heartbeat_status": heartbeat["heartbeat_status"],
        "summary_status": "PASS",
        "launcher_status": "SAFE_MODE",
        "live_launcher_hard_blocked": spec.mode == "LIVE",
        "live_path_hard_blocked": True,
        "forbidden_runtime_actions": {
            "live_key_load_attempted": False,
            "live_order_api_attempted": False,
            "order_adapter_submit_attempted": False,
            "strategy_direct_exchange_call_attempted": False,
        },
        "final_action": summary["final_action"],
        "blocking_reason": blocking_reason,
        "next_action": next_action,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "report_hash": "",
    }
    report["report_hash"] = launcher_report_hash(report)
    return report


def validate_launcher_report(report: dict[str, Any]) -> LauncherReportValidationResult:
    if report.get("schema_id") != ROOT_LAUNCHER_REPORT_SCHEMA_ID:
        return LauncherReportValidationResult("FAIL", "root launcher report schema mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("report_hash") != launcher_report_hash(report):
        return LauncherReportValidationResult("FAIL", "root launcher report hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    launcher_name = report.get("launcher_name")
    if launcher_name not in ROOT_LAUNCHER_SPECS:
        return LauncherReportValidationResult("FAIL", "unknown root launcher name", "CONTRACT_GAP_HIGH")
    spec = ROOT_LAUNCHER_SPECS[launcher_name]
    for key in ("exchange", "market_type", "mode", "session_id"):
        if report.get(key) != getattr(spec, key):
            return LauncherReportValidationResult("BLOCKED", f"launcher report scope mismatch: {key}", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade"):
        return LauncherReportValidationResult("BLOCKED", "root launcher attempted to create live permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("final_action") in ORDER_AFFECTING_FINAL_ACTIONS:
        return LauncherReportValidationResult("BLOCKED", "root launcher emitted order-affecting action", "LIVE_FINAL_GUARD_FAILED")
    if report.get("live_path_hard_blocked") is not True:
        return LauncherReportValidationResult("BLOCKED", "root launcher did not hard-block live path", "LIVE_FINAL_GUARD_FAILED")
    actions = report.get("forbidden_runtime_actions", {})
    if not isinstance(actions, dict) or any(actions.get(key) for key in actions):
        return LauncherReportValidationResult("BLOCKED", "root launcher attempted forbidden runtime action", "LIVE_FINAL_GUARD_FAILED")
    if launcher_name.startswith("BINANCE") and report.get("market_type_source") not in {"LAUNCHER_INTERNAL_UI", "EXPLICIT_COMMAND_OPTION", "SAFE_CONFIG_SCHEMA"}:
        return LauncherReportValidationResult("BLOCKED", "BINANCE launcher lacks explicit market_type source", "SNAPSHOT_SCOPE_MISMATCH")
    surface_blocker = _launcher_surface_blocker(spec.exchange, spec.market_type, spec.mode)
    if surface_blocker and report.get("blocking_reason") != surface_blocker[0]:
        return LauncherReportValidationResult("BLOCKED", "BINANCE launcher must expose surface-only blocker", "CONTRACT_GAP_HIGH")
    if launcher_name.endswith("LIVE") and report.get("live_launcher_hard_blocked") is not True:
        return LauncherReportValidationResult("BLOCKED", "live launcher is not hard-blocked in MVP-1", "LIVE_FINAL_GUARD_FAILED")
    if report.get("config_status") != "PASS":
        return LauncherReportValidationResult("BLOCKED", "root launcher config did not validate", "PREFLIGHT_FAILED")
    return LauncherReportValidationResult("PASS", "root launcher report is safe and fail-closed", None)


def launcher_report_path(report: dict[str, Any], root: Path = ROOT) -> Path:
    return (
        root
        / "system"
        / "runtime"
        / str(report["exchange"]).lower()
        / str(report["market_type"]).lower()
        / str(report["mode"]).lower()
        / str(report["session_id"])
        / "launcher"
        / "root_launcher_report.json"
    )


def _write_launcher_report_unlocked(report: dict[str, Any], root: Path = ROOT) -> Path:
    path = launcher_report_path(report, root)
    write_json(path, report)
    return path


def write_launcher_report(report: dict[str, Any], root: Path = ROOT) -> Path:
    with runtime_write_lock(launcher_runtime_dir(report, root)):
        return _write_launcher_report_unlocked(report, root)


def launcher_runtime_dir(report: dict[str, Any], root: Path = ROOT) -> Path:
    return (
        root
        / "system"
        / "runtime"
        / str(report["exchange"]).lower()
        / str(report["market_type"]).lower()
        / str(report["mode"]).lower()
        / str(report["session_id"])
    )


def launcher_dashboard_paths(report: dict[str, Any], root: Path = ROOT) -> dict[str, Path]:
    base = launcher_runtime_dir(report, root)
    return {
        "startup_probe": base / "startup_probe.json",
        "heartbeat": base / "heartbeat.json",
        "summary": base / "summary.json",
        "upbit_paper_runtime_cycle_report": base / "upbit_paper_runtime_cycle_report.json",
        "upbit_paper_persistent_loop_report": base
        / "paper_runtime"
        / "upbit_paper_persistent_loop_report.json",
        "upbit_paper_runtime_recovery_guard_report": base
        / "paper_runtime"
        / "upbit_paper_runtime_recovery_guard_report.json",
        "upbit_paper_runtime_evidence_collection_profile_report": root
        / "system"
        / "evidence"
        / "runtime_checks"
        / "MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.report.json",
        "upbit_paper_post_rerun_reconciliation_blocker_rollup_report": base
        / "paper_runtime"
        / "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json",
        "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report": base
        / "paper_runtime"
        / "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json",
        "upbit_paper_post_rerun_operator_reconciliation_queue_report": base
        / "paper_runtime"
        / "upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
        "upbit_paper_post_rerun_operator_resolution_audit_report": base
        / "paper_runtime"
        / "upbit_paper_post_rerun_operator_resolution_audit_report.json",
        "upbit_paper_post_rerun_resolution_current_evidence_closure_report": base
        / "paper_runtime"
        / "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json",
        "upbit_paper_post_rerun_current_evidence_closure_recheck_report": base
        / "paper_runtime"
        / "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json",
        "upbit_paper_post_rerun_reconciliation_repair_path_report": base
        / "paper_runtime"
        / "upbit_paper_post_rerun_reconciliation_repair_path_report.json",
        "upbit_paper_post_repair_reconciliation_report": base
        / "paper_runtime"
        / "upbit_paper_post_repair_reconciliation_report.json",
        "upbit_paper_repair_operator_queue_report": base
        / "paper_runtime"
        / "upbit_paper_repair_operator_queue_report.json",
        "upbit_paper_stale_loop_post_regeneration_reconciliation_report": base
        / "paper_runtime"
        / "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json",
        "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report": base
        / "paper_runtime"
        / "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json",
        "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report": base
        / "paper_runtime"
        / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json",
        "upbit_paper_repaired_current_evidence_audited_writer_precheck_report": base
        / "paper_runtime"
        / "upbit_paper_repaired_current_evidence_audited_writer_precheck_report.json",
        "upbit_paper_repaired_current_evidence_audited_writer_dry_run_report": base
        / "paper_runtime"
        / "upbit_paper_repaired_current_evidence_audited_writer_dry_run_report.json",
        "upbit_paper_ledger_idempotency_runtime_evidence_report": base
        / "ledger"
        / "upbit_paper_ledger_idempotency_runtime_evidence_report.json",
        "paper_ledger_rollup_report": base / "ledger" / "paper_ledger_rollup_report.json",
        "upbit_public_rest_continuity_history": base
        / "market_data"
        / "public"
        / "rest_continuity_history.json",
        "candidate_scorecard": base / "profitability" / "candidate_scorecard.json",
        "paper_operation_gate_report": base / "paper_operation_gate_report.json",
        "paper_exposure_quality_report": base / "paper_exposure_quality_report.json",
        "reconciliation_report": base / "reconciliation_report.json",
        "restart_recovery_report": base / "restart_recovery_report.json",
        "paper_portfolio_snapshot": base / "paper_portfolio_snapshot.json",
        "stability_history": base / "stability_history.json",
        "shadow_runtime_harness_report": root
        / "system"
        / "runtime"
        / str(report["exchange"]).lower()
        / str(report["market_type"]).lower()
        / "shadow"
        / str(report["session_id"])
        / "actual_runtime_harness_report.json",
        "shadow_persistent_runtime_report": root
        / "system"
        / "runtime"
        / str(report["exchange"]).lower()
        / str(report["market_type"]).lower()
        / "shadow"
        / str(report["session_id"])
        / "shadow_observation"
        / "shadow_observation_persistent_runtime_report.json",
        "shadow_runtime_orchestration_report": root
        / "system"
        / "runtime"
        / str(report["exchange"]).lower()
        / str(report["market_type"]).lower()
        / "shadow"
        / str(report["session_id"])
        / "runtime_orchestration_report.json",
        "dashboard_shell": base / "dashboard_shell.json",
        "dashboard_html": base / "dashboard" / "index.html",
    }


def _runtime_display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _dashboard_artifact_is_fresh(payload: dict[str, Any], max_age_seconds: int = 300) -> bool:
    generated_at = payload.get("generated_at_utc")
    if not isinstance(generated_at, str):
        return False
    try:
        parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()
    return 0 <= age_seconds <= max_age_seconds


def load_scoped_upbit_paper_runtime_cycle_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    path = launcher_dashboard_paths(report, root)["upbit_paper_runtime_cycle_report"]
    if not path.exists():
        return None
    try:
        runtime_cycle = load_json(path)
    except Exception:
        return None
    if (
        runtime_cycle.get("exchange") != report.get("exchange")
        or runtime_cycle.get("market_type") != report.get("market_type")
        or runtime_cycle.get("mode") != report.get("mode")
        or runtime_cycle.get("session_id") != report.get("session_id")
    ):
        return None
    if not _dashboard_artifact_is_fresh(runtime_cycle):
        return None
    result = validate_upbit_paper_runtime_cycle_report(runtime_cycle)
    if result.status != "PASS":
        return None
    return runtime_cycle


def load_scoped_paper_ledger_rollup_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    path = launcher_dashboard_paths(report, root)["paper_ledger_rollup_report"]
    if not path.exists():
        return None
    try:
        rollup = load_json(path)
    except Exception:
        return None
    if (
        rollup.get("exchange") != report.get("exchange")
        or rollup.get("market_type") != report.get("market_type")
        or rollup.get("mode") != report.get("mode")
        or rollup.get("session_id") != report.get("session_id")
    ):
        return None
    if not _dashboard_artifact_is_fresh(rollup):
        return rollup
    validation_result = validate_paper_ledger_rollup_report(rollup)
    if validation_result.status in {"PASS", "BLOCKED"}:
        return rollup
    return rollup


def load_scoped_upbit_paper_persistent_loop_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    canonical_path = paths["upbit_paper_persistent_loop_report"]
    candidates = [canonical_path]
    paper_runtime_dir = launcher_runtime_dir(report, root) / "paper_runtime"
    if paper_runtime_dir.exists():
        candidates.extend(
            sorted(
                paper_runtime_dir.glob("*.persistent_loop_report.json"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
        )
    seen: set[Path] = set()
    for path in candidates:
        resolved_path = path.resolve()
        if resolved_path in seen:
            continue
        seen.add(resolved_path)
        persistent_loop = _load_dashboard_json_artifact(path)
        if not isinstance(persistent_loop, dict):
            continue
        if not _dashboard_artifact_is_fresh(persistent_loop):
            return persistent_loop
        result = validate_upbit_paper_persistent_loop_report(persistent_loop)
        if result.status in {"PASS", "BLOCKED"}:
            return persistent_loop
    return None


def load_scoped_upbit_paper_runtime_recovery_guard_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    canonical_path = paths["upbit_paper_runtime_recovery_guard_report"]
    candidates = [canonical_path]
    paper_runtime_dir = launcher_runtime_dir(report, root) / "paper_runtime"
    if paper_runtime_dir.exists():
        candidates.extend(sorted(paper_runtime_dir.glob("*-recovery-guard.json"), key=lambda path: path.stat().st_mtime, reverse=True))
    for path in candidates:
        if not path.exists():
            continue
        try:
            recovery_guard = load_json(path)
        except Exception:
            continue
        if (
            recovery_guard.get("exchange") != report.get("exchange")
            or recovery_guard.get("market_type") != report.get("market_type")
            or recovery_guard.get("mode") != report.get("mode")
            or recovery_guard.get("session_id") != report.get("session_id")
        ):
            continue
        if path != canonical_path:
            write_json(canonical_path, recovery_guard)
        if not _dashboard_artifact_is_fresh(recovery_guard):
            return recovery_guard
        result = validate_upbit_paper_runtime_recovery_guard_report(recovery_guard)
        if result.status in {"PASS", "BLOCKED"}:
            return recovery_guard
    return None


def load_scoped_upbit_paper_runtime_evidence_collection_profile_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    path = launcher_dashboard_paths(report, root)["upbit_paper_runtime_evidence_collection_profile_report"]
    profile = _load_dashboard_json_artifact(path)
    if not isinstance(profile, dict):
        return None
    if (
        profile.get("exchange") != report.get("exchange")
        or profile.get("market_type") != report.get("market_type")
        or profile.get("mode") != report.get("mode")
        or profile.get("session_id") != report.get("session_id")
    ):
        return None
    result = validate_upbit_paper_runtime_evidence_collection_profile_report(profile)
    if result.status in {"PASS", "BLOCKED"}:
        return profile
    return None


def load_scoped_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    rollup = _load_dashboard_json_artifact(paths["upbit_paper_post_rerun_reconciliation_blocker_rollup_report"])
    if rollup is None:
        return None
    result = validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(rollup)
    if result.status == "PASS":
        return rollup
    return rollup


def load_scoped_upbit_paper_post_rerun_operator_reconciliation_review_guidance_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    guidance = _load_dashboard_json_artifact(
        paths["upbit_paper_post_rerun_operator_reconciliation_review_guidance_report"]
    )
    if guidance is None:
        return None
    result = validate_upbit_paper_post_rerun_operator_reconciliation_review_guidance_report(guidance)
    if result.status == "PASS":
        return guidance
    return guidance


def load_scoped_upbit_paper_post_rerun_operator_reconciliation_queue_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    queue = _load_dashboard_json_artifact(
        paths["upbit_paper_post_rerun_operator_reconciliation_queue_report"]
    )
    if queue is None:
        return None
    result = validate_upbit_paper_post_rerun_operator_reconciliation_queue_report(queue)
    if result.status == "PASS":
        return queue
    return queue


def load_scoped_upbit_paper_post_rerun_operator_resolution_audit_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    audit = _load_dashboard_json_artifact(
        paths["upbit_paper_post_rerun_operator_resolution_audit_report"]
    )
    if audit is None:
        return None
    result = validate_upbit_paper_post_rerun_operator_resolution_audit_report(audit)
    if result.status == "PASS":
        return audit
    return audit


def load_scoped_upbit_paper_post_rerun_resolution_current_evidence_closure_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    closure = _load_dashboard_json_artifact(
        paths["upbit_paper_post_rerun_resolution_current_evidence_closure_report"]
    )
    if closure is None:
        return None
    result = validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report(closure)
    if result.status == "PASS":
        return closure
    return closure


def load_scoped_upbit_paper_post_rerun_current_evidence_closure_recheck_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    recheck = _load_dashboard_json_artifact(
        paths["upbit_paper_post_rerun_current_evidence_closure_recheck_report"]
    )
    if recheck is None:
        return None
    result = validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report(recheck)
    if result.status == "PASS":
        return recheck
    return recheck


def load_scoped_upbit_paper_post_rerun_reconciliation_repair_path_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    repair_path = _load_dashboard_json_artifact(
        paths["upbit_paper_post_rerun_reconciliation_repair_path_report"]
    )
    if repair_path is None:
        return None
    result = validate_upbit_paper_post_rerun_reconciliation_repair_path_report(repair_path)
    if result.status == "PASS":
        return repair_path
    return repair_path


def load_scoped_upbit_paper_post_repair_reconciliation_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    post_repair = _load_dashboard_json_artifact(paths["upbit_paper_post_repair_reconciliation_report"])
    if post_repair is None:
        return None
    result = validate_upbit_paper_post_repair_reconciliation_report(post_repair)
    if result.status == "PASS":
        return post_repair
    return post_repair


def load_scoped_upbit_paper_repair_operator_queue_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    queue = _load_dashboard_json_artifact(paths["upbit_paper_repair_operator_queue_report"])
    if queue is None:
        return None
    result = validate_upbit_paper_repair_operator_queue_report(queue)
    if result.status == "PASS":
        return queue
    return queue


def load_scoped_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    post_regeneration = _load_dashboard_json_artifact(
        paths["upbit_paper_stale_loop_post_regeneration_reconciliation_report"]
    )
    if post_regeneration is None:
        return None
    result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(post_regeneration)
    if result.status == "PASS":
        return post_regeneration
    return post_regeneration


def load_scoped_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    closure = _load_dashboard_json_artifact(
        paths["upbit_paper_stale_loop_reconciliation_operator_queue_closure_report"]
    )
    if closure is None:
        return None
    result = validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(closure)
    if result.status in {"PASS", "BLOCKED"}:
        return closure
    return closure


def load_scoped_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    guard = _load_dashboard_json_artifact(
        paths["upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report"]
    )
    if guard is None:
        return None
    result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(guard)
    if result.status in {"PASS", "BLOCKED"}:
        return guard
    return guard


def load_scoped_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    precheck = _load_dashboard_json_artifact(
        paths["upbit_paper_repaired_current_evidence_audited_writer_precheck_report"]
    )
    if precheck is None:
        return None
    result = validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(precheck)
    if result.status in {"PASS", "BLOCKED"}:
        return precheck
    return precheck


def load_scoped_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    paths = launcher_dashboard_paths(report, root)
    dry_run = _load_dashboard_json_artifact(
        paths["upbit_paper_repaired_current_evidence_audited_writer_dry_run_report"]
    )
    if dry_run is None:
        return None
    result = validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(dry_run)
    if result.status in {"PASS", "BLOCKED"}:
        return dry_run
    return dry_run


def load_scoped_upbit_paper_ledger_idempotency_runtime_evidence_report(
    report: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    paths = launcher_dashboard_paths(report, root)
    evidence = _load_dashboard_json_artifact(paths["upbit_paper_ledger_idempotency_runtime_evidence_report"])
    if evidence is None:
        return None
    result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(evidence)
    if result.status in {"PASS", "BLOCKED"}:
        return evidence
    return evidence


def load_scoped_upbit_public_rest_continuity_history(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    path = launcher_dashboard_paths(report, root)["upbit_public_rest_continuity_history"]
    history = _load_dashboard_json_artifact(path)
    if not isinstance(history, dict):
        return None
    if (
        history.get("exchange") != report.get("exchange")
        or history.get("market_type") != report.get("market_type")
        or history.get("mode") != report.get("mode")
        or history.get("session_id") != report.get("session_id")
    ):
        return history
    validation_result = validate_upbit_public_rest_continuity_history_report(history)
    if validation_result.status in {"PASS", "BLOCKED"}:
        return history
    return history


def load_scoped_paper_operation_gate_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    path = launcher_dashboard_paths(report, root)["paper_operation_gate_report"]
    if not path.exists():
        return None
    try:
        gate = load_json(path)
    except Exception:
        return None
    if (
        gate.get("exchange") != report.get("exchange")
        or gate.get("market_type") != report.get("market_type")
        or gate.get("mode") != report.get("mode")
        or gate.get("session_id") != report.get("session_id")
    ):
        return None
    result = validate_paper_operation_gate_report(gate)
    if result.status != "PASS":
        return None
    return gate


def load_scoped_paper_exposure_quality_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("mode") != "PAPER":
        return None
    path = launcher_dashboard_paths(report, root)["paper_exposure_quality_report"]
    if not path.exists():
        return None
    try:
        exposure_report = load_json(path)
    except Exception:
        return None
    if (
        exposure_report.get("exchange") != report.get("exchange")
        or exposure_report.get("market_type") != report.get("market_type")
        or exposure_report.get("mode") != report.get("mode")
        or exposure_report.get("session_id") != report.get("session_id")
    ):
        return None
    forbidden_fields = (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "promotion_eligible",
        "order_adapter_called",
        "exchange_account_call_allowed",
        "live_config_mutation_allowed",
    )
    if any(exposure_report.get(field) is True for field in forbidden_fields):
        return None
    return exposure_report


def load_scoped_candidate_scorecard(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    path = launcher_dashboard_paths(report, root)["candidate_scorecard"]
    if not path.exists():
        return None
    scorecard = _load_dashboard_json_artifact(path)
    if not isinstance(scorecard, dict):
        return None
    if (
        scorecard.get("exchange") != report.get("exchange")
        or scorecard.get("market_type") != report.get("market_type")
        or scorecard.get("mode") != report.get("mode")
        or scorecard.get("session_id") != report.get("session_id")
    ):
        return scorecard
    forbidden_fields = (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "can_submit_order",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
    )
    if any(scorecard.get(field) is True for field in forbidden_fields):
        return scorecard
    return scorecard


def _load_dashboard_json_artifact(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = load_json(path)
    except Exception:
        return {
            "schema_id": "trader1.invalid_dashboard_input.v1",
            "artifact_path": path.name,
            "artifact_load_status": "INVALID_JSON",
        }
    return value if isinstance(value, dict) else {
        "schema_id": "trader1.invalid_dashboard_input.v1",
        "artifact_path": path.name,
        "artifact_load_status": "INVALID_JSON_SHAPE",
    }


def load_dashboard_reconciliation_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("mode") != "PAPER":
        return None
    reconciliation_report = _load_dashboard_json_artifact(launcher_dashboard_paths(report, root)["reconciliation_report"])
    if reconciliation_report is None:
        return None
    validation_result = validate_reconciliation_report(reconciliation_report)
    if validation_result.status == "PASS":
        return reconciliation_report
    return reconciliation_report


def load_dashboard_restart_recovery_report(
    report: dict[str, Any],
    paper_operation_gate_report: dict[str, Any] | None = None,
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if report.get("mode") != "PAPER":
        return None
    restart_report = _load_dashboard_json_artifact(launcher_dashboard_paths(report, root)["restart_recovery_report"])
    if restart_report is None and isinstance(paper_operation_gate_report, dict):
        nested_restart = paper_operation_gate_report.get("restart_recovery_report")
        restart_report = nested_restart if isinstance(nested_restart, dict) else None
    if restart_report is None:
        return None
    validation_result = validate_restart_recovery_report(restart_report)
    if validation_result.status == "PASS":
        return restart_report
    return restart_report


def load_profitability_maturity_rollup_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("mode") != "PAPER":
        return None
    path = root / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json"
    rollup = _load_dashboard_json_artifact(path)
    if not isinstance(rollup, dict):
        return None
    if rollup.get("schema_id") != "trader1.profitability_evidence_maturity_rollup.v1":
        return None
    if any(
        rollup.get(field) is True
        for field in (
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
            "live_permission_created",
            "profitability_guarantee_created",
            "optimizer_live_mutation_detected",
            "convergence_live_mutation_detected",
        )
    ):
        return None
    return rollup


def load_shadow_runtime_harness_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    harness_report = _load_dashboard_json_artifact(launcher_dashboard_paths(report, root)["shadow_runtime_harness_report"])
    if not isinstance(harness_report, dict):
        return None
    try:
        validation_result = validate_shadow_observation_actual_runtime_harness_report(harness_report)
    except Exception:
        return harness_report
    if validation_result.status == "PASS":
        return harness_report
    return harness_report


def load_shadow_persistent_runtime_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    persistent_report = _load_dashboard_json_artifact(launcher_dashboard_paths(report, root)["shadow_persistent_runtime_report"])
    if not isinstance(persistent_report, dict):
        return None
    try:
        validation_result = validate_shadow_observation_persistent_runtime_report(persistent_report)
    except Exception:
        return persistent_report
    if validation_result.status == "PASS":
        return persistent_report
    return persistent_report


def load_shadow_runtime_orchestration_report(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any] | None:
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return None
    orchestration_report = _load_dashboard_json_artifact(launcher_dashboard_paths(report, root)["shadow_runtime_orchestration_report"])
    if not isinstance(orchestration_report, dict):
        return None
    try:
        validation_result = validate_shadow_observation_runtime_orchestration_report(orchestration_report)
    except Exception:
        return orchestration_report
    if validation_result.status == "PASS":
        return orchestration_report
    return orchestration_report


def build_launcher_dashboard_artifacts(
    report: dict[str, Any],
    stability_history: dict[str, Any] | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    registry_hash = sha256_file(ROOT / "contracts" / "registry.yaml")
    schemas_hash = schema_bundle_hash()
    sources_hash = source_tree_hash()
    config = build_runtime_config(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=report["session_id"],
        registry_hash=registry_hash,
        market_type_source=report["market_type_source"],
    )
    startup_probe = build_startup_probe(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=report["session_id"],
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schemas_hash,
        source_tree_hash=sources_hash,
        ledger_write_status=None,
    )
    resource_pressure = inspect_runtime_resource_pressure(launcher_runtime_dir(report, root))
    heartbeat = build_heartbeat(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=report["session_id"],
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schemas_hash,
        source_tree_hash=sources_hash,
        component_overrides=resource_pressure.heartbeat_component_overrides(),
    )
    readiness = build_readiness_surface(
        authority=authority_hashes(),
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=report["session_id"],
        registry_hash=registry_hash,
        schema_bundle_hash=schemas_hash,
        source_tree_hash=sources_hash,
    )
    paper_runtime_cycle_report = load_scoped_upbit_paper_runtime_cycle_report(report, root)
    paper_ledger_rollup_report = load_scoped_paper_ledger_rollup_report(report, root)
    paper_ledger_rollup_loaded = isinstance(paper_ledger_rollup_report, dict)
    paper_ledger_rollup_usable = (
        paper_ledger_rollup_loaded
        and paper_ledger_rollup_report.get("rollup_status") == "PASS"
        and _dashboard_artifact_is_fresh(paper_ledger_rollup_report)
    )
    paper_portfolio = None
    entry_candidates: list[dict[str, Any]] | None = None
    recent_entry_context: list[dict[str, Any]] | None = None
    recent_no_trade_context: list[dict[str, Any]] | None = None
    market_context: dict[str, Any] | None = None
    if paper_ledger_rollup_usable:
        paper_portfolio = paper_ledger_rollup_report.get("portfolio_snapshot")
    if isinstance(paper_runtime_cycle_report, dict):
        if paper_portfolio is None:
            paper_portfolio = paper_runtime_cycle_report.get("paper_portfolio_snapshot")
        entry_candidates = paper_runtime_cycle_report.get("strategy_candidates")
        recent_entry_context = paper_runtime_cycle_report.get("entry_reasons")
        recent_no_trade_context = [
            {"reason_code": reason, "message": "PAPER runtime cycle did not enter"}
            for reason in paper_runtime_cycle_report.get("no_trade_reasons", [])
        ]
        feature_snapshot = paper_runtime_cycle_report.get("feature_snapshot", {})
        market_context = {
            "source": "MARKET_DATA",
            "freshness_status": "PASS",
            "regime": feature_snapshot.get("regime"),
            "liquidity_status": feature_snapshot.get("liquidity_status"),
            "volatility_status": feature_snapshot.get("volatility_status"),
        }
    if paper_portfolio is None and report["mode"] == "PAPER" and not paper_ledger_rollup_loaded:
        paper_portfolio = build_initial_paper_portfolio_snapshot(
            exchange=report["exchange"],
            market_type=report["market_type"],
            session_id=report["session_id"],
        )
    summary = build_summary_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=report["session_id"],
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness,
        paper_portfolio_snapshot=paper_portfolio,
        entry_candidates=entry_candidates,
        recent_entry_context=recent_entry_context,
        recent_no_trade_context=recent_no_trade_context,
        market_context=market_context,
    )
    surface_blocker = _launcher_surface_blocker(report["exchange"], report["market_type"], report["mode"])
    if surface_blocker:
        blocker_code, blocker_message = surface_blocker
        summary["blocking_reason"] = blocker_code
        summary["next_action"] = blocker_message
        summary["live_ready"]["primary_blocker_code"] = blocker_code
        summary["live_ready"]["primary_blocker_message"] = blocker_message
    paths = launcher_dashboard_paths(report, root)
    source_paths = {
        "summary": _runtime_display_path(paths["summary"], root),
        "heartbeat": _runtime_display_path(paths["heartbeat"], root),
        "startup_probe": _runtime_display_path(paths["startup_probe"], root),
        "reconciliation_report": _runtime_display_path(paths["reconciliation_report"], root),
        "restart_recovery_report": _runtime_display_path(paths["restart_recovery_report"], root),
        "paper_ledger_rollup_report": _runtime_display_path(paths["paper_ledger_rollup_report"], root),
        "upbit_paper_persistent_loop": _runtime_display_path(paths["upbit_paper_persistent_loop_report"], root),
        "upbit_paper_runtime_recovery_guard": _runtime_display_path(paths["upbit_paper_runtime_recovery_guard_report"], root),
        "upbit_paper_runtime_evidence_collection_profile": _runtime_display_path(
            paths["upbit_paper_runtime_evidence_collection_profile_report"], root
        ),
        "upbit_paper_post_rerun_reconciliation_blocker_rollup": _runtime_display_path(
            paths["upbit_paper_post_rerun_reconciliation_blocker_rollup_report"], root
        ),
        "upbit_paper_post_rerun_operator_reconciliation_review_guidance": _runtime_display_path(
            paths["upbit_paper_post_rerun_operator_reconciliation_review_guidance_report"], root
        ),
        "upbit_paper_post_rerun_operator_reconciliation_queue": _runtime_display_path(
            paths["upbit_paper_post_rerun_operator_reconciliation_queue_report"], root
        ),
        "upbit_paper_post_rerun_operator_resolution_audit": _runtime_display_path(
            paths["upbit_paper_post_rerun_operator_resolution_audit_report"], root
        ),
        "upbit_paper_post_rerun_resolution_current_evidence_closure": _runtime_display_path(
            paths["upbit_paper_post_rerun_resolution_current_evidence_closure_report"], root
        ),
        "upbit_paper_post_rerun_current_evidence_closure_recheck": _runtime_display_path(
            paths["upbit_paper_post_rerun_current_evidence_closure_recheck_report"], root
        ),
        "upbit_paper_post_rerun_reconciliation_repair_path": _runtime_display_path(
            paths["upbit_paper_post_rerun_reconciliation_repair_path_report"], root
        ),
        "upbit_paper_post_repair_reconciliation": _runtime_display_path(
            paths["upbit_paper_post_repair_reconciliation_report"], root
        ),
        "upbit_paper_repair_operator_queue": _runtime_display_path(
            paths["upbit_paper_repair_operator_queue_report"], root
        ),
        "upbit_paper_stale_loop_post_regeneration_reconciliation": _runtime_display_path(
            paths["upbit_paper_stale_loop_post_regeneration_reconciliation_report"], root
        ),
        "upbit_paper_stale_loop_reconciliation_operator_queue_closure": _runtime_display_path(
            paths["upbit_paper_stale_loop_reconciliation_operator_queue_closure_report"], root
        ),
        "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard": _runtime_display_path(
            paths["upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report"],
            root,
        ),
        "upbit_paper_repaired_current_evidence_audited_writer_precheck": _runtime_display_path(
            paths["upbit_paper_repaired_current_evidence_audited_writer_precheck_report"],
            root,
        ),
        "upbit_paper_repaired_current_evidence_audited_writer_dry_run": _runtime_display_path(
            paths["upbit_paper_repaired_current_evidence_audited_writer_dry_run_report"],
            root,
        ),
        "upbit_paper_ledger_idempotency_runtime_evidence": _runtime_display_path(
            paths["upbit_paper_ledger_idempotency_runtime_evidence_report"], root
        ),
        "upbit_public_rest_continuity_history": _runtime_display_path(paths["upbit_public_rest_continuity_history"], root),
        "candidate_scorecard": _runtime_display_path(paths["candidate_scorecard"], root),
        "shadow_runtime_harness": _runtime_display_path(paths["shadow_runtime_harness_report"], root),
        "shadow_persistent_runtime": _runtime_display_path(paths["shadow_persistent_runtime_report"], root),
        "shadow_runtime_orchestration": _runtime_display_path(paths["shadow_runtime_orchestration_report"], root),
    }
    paper_operation_gate_report = load_scoped_paper_operation_gate_report(report, root)
    paper_exposure_quality_report = load_scoped_paper_exposure_quality_report(report, root)
    candidate_scorecard = load_scoped_candidate_scorecard(report, root)
    profitability_maturity_rollup_report = load_profitability_maturity_rollup_report(report, root)
    reconciliation_report = load_dashboard_reconciliation_report(report, root)
    restart_recovery_report = load_dashboard_restart_recovery_report(
        report,
        paper_operation_gate_report=paper_operation_gate_report,
        root=root,
    )
    upbit_paper_persistent_loop_report = load_scoped_upbit_paper_persistent_loop_report(report, root)
    upbit_paper_runtime_recovery_guard_report = load_scoped_upbit_paper_runtime_recovery_guard_report(report, root)
    upbit_paper_runtime_evidence_collection_profile_report = (
        load_scoped_upbit_paper_runtime_evidence_collection_profile_report(report, root)
    )
    upbit_paper_post_rerun_reconciliation_blocker_rollup_report = (
        load_scoped_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(report, root)
    )
    upbit_paper_post_rerun_operator_reconciliation_review_guidance_report = (
        load_scoped_upbit_paper_post_rerun_operator_reconciliation_review_guidance_report(report, root)
    )
    upbit_paper_post_rerun_operator_reconciliation_queue_report = (
        load_scoped_upbit_paper_post_rerun_operator_reconciliation_queue_report(report, root)
    )
    upbit_paper_post_rerun_operator_resolution_audit_report = (
        load_scoped_upbit_paper_post_rerun_operator_resolution_audit_report(report, root)
    )
    upbit_paper_post_rerun_resolution_current_evidence_closure_report = (
        load_scoped_upbit_paper_post_rerun_resolution_current_evidence_closure_report(report, root)
    )
    upbit_paper_post_rerun_current_evidence_closure_recheck_report = (
        load_scoped_upbit_paper_post_rerun_current_evidence_closure_recheck_report(report, root)
    )
    upbit_paper_post_rerun_reconciliation_repair_path_report = (
        load_scoped_upbit_paper_post_rerun_reconciliation_repair_path_report(report, root)
    )
    upbit_paper_post_repair_reconciliation_report = (
        load_scoped_upbit_paper_post_repair_reconciliation_report(report, root)
    )
    upbit_paper_repair_operator_queue_report = (
        load_scoped_upbit_paper_repair_operator_queue_report(report, root)
    )
    upbit_paper_stale_loop_post_regeneration_reconciliation_report = (
        load_scoped_upbit_paper_stale_loop_post_regeneration_reconciliation_report(report, root)
    )
    upbit_paper_stale_loop_reconciliation_operator_queue_closure_report = (
        load_scoped_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(report, root)
    )
    upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report = (
        load_scoped_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(report, root)
    )
    upbit_paper_repaired_current_evidence_audited_writer_precheck_report = (
        load_scoped_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(report, root)
    )
    upbit_paper_repaired_current_evidence_audited_writer_dry_run_report = (
        load_scoped_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(report, root)
    )
    upbit_paper_ledger_idempotency_runtime_evidence_report = (
        load_scoped_upbit_paper_ledger_idempotency_runtime_evidence_report(report, root)
    )
    upbit_public_rest_continuity_history = load_scoped_upbit_public_rest_continuity_history(report, root)
    shadow_runtime_harness_report = load_shadow_runtime_harness_report(report, root)
    shadow_persistent_runtime_report = load_shadow_persistent_runtime_report(report, root)
    shadow_runtime_orchestration_report = load_shadow_runtime_orchestration_report(report, root)
    dashboard = build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=report["session_id"],
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        paper_operation_gate_report=paper_operation_gate_report,
        paper_exposure_quality_report=paper_exposure_quality_report,
        profitability_maturity_rollup_report=profitability_maturity_rollup_report,
        candidate_scorecard=candidate_scorecard,
        reconciliation_report=reconciliation_report,
        restart_recovery_report=restart_recovery_report,
        upbit_paper_post_rerun_reconciliation_blocker_rollup_report=upbit_paper_post_rerun_reconciliation_blocker_rollup_report,
        upbit_paper_post_rerun_operator_reconciliation_review_guidance_report=upbit_paper_post_rerun_operator_reconciliation_review_guidance_report,
        upbit_paper_post_rerun_operator_reconciliation_queue_report=upbit_paper_post_rerun_operator_reconciliation_queue_report,
        upbit_paper_post_rerun_operator_resolution_audit_report=upbit_paper_post_rerun_operator_resolution_audit_report,
        upbit_paper_post_rerun_resolution_current_evidence_closure_report=upbit_paper_post_rerun_resolution_current_evidence_closure_report,
        upbit_paper_post_rerun_current_evidence_closure_recheck_report=upbit_paper_post_rerun_current_evidence_closure_recheck_report,
        upbit_paper_post_rerun_reconciliation_repair_path_report=upbit_paper_post_rerun_reconciliation_repair_path_report,
        upbit_paper_post_repair_reconciliation_report=upbit_paper_post_repair_reconciliation_report,
        upbit_paper_repair_operator_queue_report=upbit_paper_repair_operator_queue_report,
        upbit_paper_stale_loop_post_regeneration_reconciliation_report=upbit_paper_stale_loop_post_regeneration_reconciliation_report,
        upbit_paper_stale_loop_reconciliation_operator_queue_closure_report=upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report=upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report,
        upbit_paper_repaired_current_evidence_audited_writer_precheck_report=upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
        upbit_paper_repaired_current_evidence_audited_writer_dry_run_report=upbit_paper_repaired_current_evidence_audited_writer_dry_run_report,
        upbit_paper_ledger_idempotency_runtime_evidence_report=upbit_paper_ledger_idempotency_runtime_evidence_report,
        upbit_paper_persistent_loop_report=upbit_paper_persistent_loop_report,
        upbit_paper_runtime_recovery_guard_report=upbit_paper_runtime_recovery_guard_report,
        upbit_paper_runtime_evidence_collection_profile_report=upbit_paper_runtime_evidence_collection_profile_report,
        upbit_public_rest_continuity_history=upbit_public_rest_continuity_history,
        stability_history=stability_history,
        shadow_runtime_harness_report=shadow_runtime_harness_report,
        shadow_persistent_runtime_report=shadow_persistent_runtime_report,
        shadow_runtime_orchestration_report=shadow_runtime_orchestration_report,
        source_paths=source_paths,
    )
    return {
        "startup_probe": startup_probe,
        "heartbeat": heartbeat,
        "paper_portfolio_snapshot": paper_portfolio,
        "summary": summary,
        "dashboard_shell": dashboard,
        "dashboard_html": render_dashboard_html(dashboard),
    }


def _write_launcher_dashboard_unlocked(report: dict[str, Any], root: Path = ROOT) -> dict[str, Path]:
    paths = launcher_dashboard_paths(report, root)
    artifacts = build_launcher_dashboard_artifacts(report, root=root)
    previous_history = None
    if paths["stability_history"].exists():
        try:
            previous_history = load_json(paths["stability_history"])
        except Exception:
            previous_history = None
    stability_history = append_stability_history(previous_history, artifacts["dashboard_shell"])
    history_result = validate_stability_history(
        stability_history,
        expected_exchange=report["exchange"],
        expected_market_type=report["market_type"],
        expected_mode=report["mode"],
        expected_session_id=report["session_id"],
    )
    if history_result.status != "PASS":
        raise RuntimeError(f"stability history failed closed validation: {history_result.message}")
    artifacts = build_launcher_dashboard_artifacts(report, stability_history=stability_history, root=root)
    dashboard_result = validate_read_only_dashboard_shell(artifacts["dashboard_shell"])
    if dashboard_result.status != "PASS":
        raise RuntimeError(f"read-only dashboard failed closed validation: {dashboard_result.message}")
    write_json(paths["startup_probe"], artifacts["startup_probe"])
    write_json(paths["heartbeat"], artifacts["heartbeat"])
    if artifacts["paper_portfolio_snapshot"] is not None:
        write_json(paths["paper_portfolio_snapshot"], artifacts["paper_portfolio_snapshot"])
    write_json(paths["stability_history"], stability_history)
    write_json(paths["summary"], artifacts["summary"])
    write_json(paths["dashboard_shell"], artifacts["dashboard_shell"])
    write_text(paths["dashboard_html"], artifacts["dashboard_html"])
    return paths


def write_launcher_dashboard(report: dict[str, Any], root: Path = ROOT) -> dict[str, Path]:
    with runtime_write_lock(launcher_runtime_dir(report, root)):
        return _write_launcher_dashboard_unlocked(report, root)


def write_launcher_runtime_bundle(report: dict[str, Any], root: Path = ROOT) -> tuple[Path, dict[str, Path]]:
    with runtime_write_lock(launcher_runtime_dir(report, root)):
        report_path = _write_launcher_report_unlocked(report, root)
        dashboard_paths = _write_launcher_dashboard_unlocked(report, root)
    return report_path, dashboard_paths


def should_open_dashboard_for_operator(open_dashboard: bool | None = None) -> bool:
    if open_dashboard is not None:
        return open_dashboard
    return should_pause_for_operator()


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _console_heartbeat_age_seconds(heartbeat: dict[str, Any]) -> float:
    explicit_age = heartbeat.get("heartbeat_age_seconds")
    age_candidates: list[float] = []
    if isinstance(explicit_age, (int, float)) and explicit_age >= 0:
        age_candidates.append(float(explicit_age))
    observed_at = _parse_utc(heartbeat.get("last_heartbeat_at_utc") or heartbeat.get("generated_at_utc"))
    if observed_at is not None:
        age_candidates.append(max(0.0, (datetime.now(timezone.utc) - observed_at).total_seconds()))
    return max(age_candidates) if age_candidates else 0.0


def open_dashboard_for_operator(dashboard_path: Path, open_dashboard: bool | None = None) -> bool:
    if not should_open_dashboard_for_operator(open_dashboard):
        return False
    try:
        return bool(webbrowser.open(dashboard_path.resolve().as_uri()))
    except Exception:
        return False


def launcher_status_message(
    report: dict[str, Any],
    validation: LauncherReportValidationResult,
    report_path: Path,
    dashboard_path: Path | None = None,
    dashboard_opened: bool = False,
) -> str:
    lines = [
        f"TRADER_1 {report['launcher_name']} launcher: {validation.status}",
        f"mode={report['mode']} exchange={report['exchange']} market_type={report['market_type']}",
        f"final_action={report['final_action']} blocking_reason={report['blocking_reason']}",
        "live_order_ready=false live_order_allowed=false can_live_trade=false",
        f"report_path={report_path}",
    ]
    if dashboard_path is not None:
        lines.append(f"dashboard_path={dashboard_path}")
        lines.append(f"dashboard_opened={str(dashboard_opened).lower()}")
    return "\n".join(lines)


def console_heartbeat_line(report: dict[str, Any], heartbeat: dict[str, Any], tick_index: int, tick_total: int | str) -> str:
    heartbeat_status = str(heartbeat.get("heartbeat_status", "BLOCKED"))
    heartbeat_age = _console_heartbeat_age_seconds(heartbeat)
    stale_after = heartbeat.get("stale_after_seconds", 30)
    heartbeat_is_stale = isinstance(stale_after, int) and heartbeat_age > stale_after
    program_status = "STALE_HEARTBEAT" if heartbeat_is_stale else "RUNNING_SAFE_MODE"
    recovery = "rerun_paper_launcher_if_stale" if heartbeat_is_stale else "none"
    if heartbeat_is_stale:
        heartbeat_status = "BLOCKED"
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade"):
        heartbeat_status = "BLOCKED"
    if heartbeat.get("live_order_ready") or heartbeat.get("live_order_allowed") or heartbeat.get("can_live_trade"):
        heartbeat_status = "BLOCKED"
    blocker = "LATENCY_TTL_EXPIRED" if heartbeat_is_stale else report.get("blocking_reason") or heartbeat.get("primary_blocker_code") or "NONE"
    return (
        f"HEARTBEAT {tick_index}/{tick_total} {heartbeat_status} "
        f"program_status={program_status} "
        f"engine={heartbeat.get('engine_state', 'UNKNOWN')} "
        f"scope={report.get('exchange')}/{report.get('market_type')}/{report.get('mode')} "
        f"session_id={report.get('session_id')} "
        f"heartbeat_at={heartbeat.get('last_heartbeat_at_utc', heartbeat.get('generated_at_utc', 'UNKNOWN'))} "
        f"heartbeat_age={heartbeat_age:.1f}s stale_after={stale_after}s recovery={recovery} "
        "launcher_mode=SAFE_BOOT_OR_EXPLICIT_MONITOR "
        f"runtime_presence={'HEARTBEAT_STALE_OR_SOURCE_ATTENTION_REQUIRED' if heartbeat_is_stale else 'DASHBOARD_HEARTBEAT_ONLY'} "
        f"final_action={report.get('final_action', 'NO_TRADE')} "
        f"blocker={blocker} "
        "live_order_ready=false live_order_allowed=false can_live_trade=false scale_up_allowed=false "
        "order_adapter_submit_attempted=false"
    )


def console_safe_monitor_banner(report: dict[str, Any], interval_seconds: float) -> str:
    return (
        "SAFE_MONITOR running: console heartbeat will repeat "
        f"every {interval_seconds:g}s until Ctrl+C. "
        f"scope={report.get('exchange')}/{report.get('market_type')}/{report.get('mode')} "
        f"session_id={report.get('session_id')} "
        "final_action=NO_TRADE live_order_ready=false live_order_allowed=false can_live_trade=false scale_up_allowed=false"
    )


def emit_console_heartbeats(
    report: dict[str, Any],
    heartbeat: dict[str, Any],
    *,
    ticks: int | None,
    interval_seconds: float,
    stream: TextIO | None = None,
    refresh_heartbeat: Any | None = None,
) -> list[str]:
    if ticks is not None and ticks < 1:
        return []
    output = stream or sys.stdout
    lines: list[str] = []
    tick_index = 1
    try:
        while ticks is None or tick_index <= ticks:
            if refresh_heartbeat is not None:
                heartbeat = refresh_heartbeat()
            tick_total: int | str = "continuous" if ticks is None else ticks
            line = console_heartbeat_line(report, heartbeat, tick_index, tick_total)
            print(line, file=output, flush=True)
            lines.append(line)
            tick_index += 1
            if interval_seconds > 0 and (ticks is None or tick_index <= ticks):
                time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("SAFE_MONITOR stopped by operator; final_action=NO_TRADE live_order_allowed=false", file=output, flush=True)
    return lines


def source_identity_mismatch_heartbeat(report: dict[str, Any], current_source_tree_hash: str) -> dict[str, Any]:
    message = "running launcher source is stale; restart launcher before refreshing dashboard artifacts"
    heartbeat = build_heartbeat(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=report["session_id"],
        config_hash=report.get("config_hash"),
        registry_hash=report.get("registry_hash"),
        schema_bundle_hash=report.get("schema_bundle_hash"),
        source_tree_hash=current_source_tree_hash,
        engine_state="SOURCE_IDENTITY_STALE",
        startup_probe_phase="STARTUP_PROBE_GATE_BLOCKED",
        component_overrides={"watchdog_heartbeat": {"status": "FAIL", "message": message}},
    )
    heartbeat["primary_blocker_code"] = "SOURCE_IDENTITY_MISMATCH"
    heartbeat["blockers"] = [
        {
            "code": "SOURCE_IDENTITY_MISMATCH",
            "severity": "HIGH",
            "message": message,
        }
    ]
    heartbeat["final_action"] = "NO_TRADE"
    heartbeat["next_action"] = "restart PAPER launcher to load current source before refreshing dashboard artifacts"
    heartbeat["heartbeat_hash"] = heartbeat_hash(heartbeat)
    return heartbeat


def refresh_launcher_monitor_artifacts(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    expected_source_hash = report.get("source_tree_hash")
    current_source_hash = source_tree_hash()
    if expected_source_hash and expected_source_hash != current_source_hash:
        return source_identity_mismatch_heartbeat(report, current_source_hash)
    paths = write_launcher_dashboard(report, root)
    return load_json(paths["heartbeat"])


def should_pause_for_operator(pause: bool | None = None) -> bool:
    if pause is not None:
        return pause
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def _optional_nonnegative_int_env(name: str) -> int | None:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a non-negative integer") from exc
    if value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _optional_nonnegative_float_env(name: str) -> float | None:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a non-negative number") from exc
    if value < 0:
        raise ValueError(f"{name} must be a non-negative number")
    return value


def root_operator_launcher_main(launcher_name: str, *, root: Path = ROOT) -> int:
    return launcher_main(
        launcher_name,
        pause=True,
        console_heartbeat_ticks=_optional_nonnegative_int_env(ROOT_OPERATOR_HEARTBEAT_TICKS_ENV),
        console_heartbeat_interval_seconds=_optional_nonnegative_float_env(ROOT_OPERATOR_HEARTBEAT_INTERVAL_ENV),
        root=root,
    )


def launcher_main(
    launcher_name: str,
    *,
    pause: bool | None = None,
    open_dashboard: bool | None = None,
    console_heartbeat_ticks: int | None = None,
    console_heartbeat_interval_seconds: float | None = None,
    root: Path = ROOT,
) -> int:
    report = build_launcher_report(launcher_name)
    result = validate_launcher_report(report)
    report_path, dashboard_paths = write_launcher_runtime_bundle(report, root)
    dashboard_opened = open_dashboard_for_operator(dashboard_paths["dashboard_html"], open_dashboard)
    heartbeat = load_json(dashboard_paths["heartbeat"])
    operator_pause = should_pause_for_operator(pause)
    heartbeat_ticks = (
        console_heartbeat_ticks
        if console_heartbeat_ticks is not None
        else DEFAULT_INTERACTIVE_HEARTBEAT_TICKS
        if operator_pause
        else DEFAULT_NON_INTERACTIVE_HEARTBEAT_TICKS
    )
    heartbeat_interval_seconds = (
        console_heartbeat_interval_seconds
        if console_heartbeat_interval_seconds is not None
        else DEFAULT_INTERACTIVE_HEARTBEAT_INTERVAL_SECONDS
        if operator_pause
        else 0.0
    )
    print(json.dumps(report, indent=2))
    print(launcher_status_message(report, result, report_path, dashboard_paths["dashboard_html"], dashboard_opened))
    if operator_pause and heartbeat_ticks is None:
        print(console_safe_monitor_banner(report, heartbeat_interval_seconds), flush=True)
    emit_console_heartbeats(
        report,
        heartbeat,
        ticks=heartbeat_ticks,
        interval_seconds=heartbeat_interval_seconds,
        refresh_heartbeat=lambda: refresh_launcher_monitor_artifacts(report, root) if operator_pause else heartbeat,
    )
    return 0 if result.status == "PASS" else 1
