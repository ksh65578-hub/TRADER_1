from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.research.shadow.shadow_observation_persistent_runtime import (
    shadow_observation_persistent_runtime_hash,
    validate_shadow_observation_persistent_runtime_report,
)


SHADOW_OBSERVATION_ARTIFACT_WRITER_SCHEMA_ID = "trader1.shadow_observation_runtime_artifact_writer_report.v1"
WRITER_FILENAME = "shadow_observation_runtime_artifact_writer_report.json"
RUNTIME_REPORT_FILENAME = "shadow_observation_persistent_runtime_report.json"


@dataclass(frozen=True)
class ShadowObservationArtifactWriterValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def shadow_observation_artifact_writer_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("writer_report_hash", None)
    return sha256_json(payload)


def _scope_slug(value: str) -> str:
    return value.lower()


def shadow_runtime_artifact_dir(root: Path, runtime_report: dict[str, Any]) -> Path:
    return (
        root
        / "system"
        / "runtime"
        / _scope_slug(str(runtime_report.get("exchange", "UNKNOWN")))
        / _scope_slug(str(runtime_report.get("market_type", "UNKNOWN")))
        / "shadow"
        / str(runtime_report.get("session_id") or runtime_report.get("runtime_id", "UNKNOWN"))
        / "shadow_observation"
    )


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def _base_writer_report(
    *,
    writer_id: str,
    runtime_report: dict[str, Any],
    root: Path,
    artifact_path: Path,
    writer_report_path: Path,
    writer_status: str,
    artifact_hash: str | None,
    temp_artifact_count_after: int,
    primary_blocker_code: str | None,
    blocker_message: str,
) -> dict[str, Any]:
    report = {
        "schema_id": SHADOW_OBSERVATION_ARTIFACT_WRITER_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "writer_id": writer_id,
        "exchange": runtime_report.get("exchange"),
        "market_type": runtime_report.get("market_type"),
        "source_mode": runtime_report.get("source_mode"),
        "mode": "SHADOW",
        "session_id": runtime_report.get("session_id") or runtime_report.get("runtime_id"),
        "writer_mode": "ATOMIC_SHADOW_STUB_WRITER",
        "writer_status": writer_status,
        "artifact_truth_role": "shadow_runtime_stub_display_truth_only",
        "runtime_evidence_role": "PERSISTENT_RUNTIME_STUB_ONLY",
        "dashboard_visibility_status": "VISIBLE_AS_STUB_ONLY" if writer_status == "PASS" else "BLOCKED_FROM_DASHBOARD",
        "source_runtime_report_id": runtime_report.get("runtime_id"),
        "source_runtime_report_hash": runtime_report.get("runtime_report_hash"),
        "source_runtime_hash_verified": runtime_report.get("runtime_report_hash") == shadow_observation_persistent_runtime_hash(runtime_report),
        "artifact_path": _relative_posix(artifact_path, root),
        "writer_report_path": _relative_posix(writer_report_path, root),
        "artifact_hash": artifact_hash,
        "atomic_writer_status": "PASS" if writer_status == "PASS" else "BLOCKED",
        "temp_artifact_count_after": temp_artifact_count_after,
        "partial_write_detected": temp_artifact_count_after != 0,
        "actual_persistent_runtime_executed": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "primary_blocker_code": primary_blocker_code,
        "blocker_message": blocker_message,
        "next_operator_action": (
            "Show this artifact as SHADOW runtime stub visibility only; collect real long-run PAPER/SHADOW evidence separately."
            if writer_status == "PASS"
            else "Repair the blocked SHADOW runtime writer input before showing it on the dashboard."
        ),
        "writer_report_hash": "",
    }
    report["writer_report_hash"] = shadow_observation_artifact_writer_hash(report)
    return report


def write_shadow_observation_runtime_artifacts(
    *,
    root: Path,
    writer_id: str,
    runtime_report: dict[str, Any],
) -> dict[str, Any]:
    root = Path(root).resolve()
    artifact_dir = shadow_runtime_artifact_dir(root, runtime_report)
    artifact_path = artifact_dir / RUNTIME_REPORT_FILENAME
    writer_report_path = artifact_dir / WRITER_FILENAME
    runtime_result = validate_shadow_observation_persistent_runtime_report(runtime_report)
    if runtime_result.status != "PASS":
        report = _base_writer_report(
            writer_id=writer_id,
            runtime_report=runtime_report,
            root=root,
            artifact_path=artifact_path,
            writer_report_path=writer_report_path,
            writer_status="BLOCKED",
            artifact_hash=None,
            temp_artifact_count_after=0,
            primary_blocker_code=runtime_result.blocker_code or "DATA_QUALITY_INSUFFICIENT",
            blocker_message=f"Source SHADOW persistent runtime report is not PASS: {runtime_result.message}",
        )
        _atomic_write_json(writer_report_path, report)
        return report

    if runtime_report.get("mode") != "SHADOW" or runtime_report.get("source_mode") != "PAPER":
        report = _base_writer_report(
            writer_id=writer_id,
            runtime_report=runtime_report,
            root=root,
            artifact_path=artifact_path,
            writer_report_path=writer_report_path,
            writer_status="BLOCKED",
            artifact_hash=None,
            temp_artifact_count_after=0,
            primary_blocker_code="SNAPSHOT_SCOPE_MISMATCH",
            blocker_message="Runtime report must remain PAPER-source, SHADOW-output scoped before artifact write.",
        )
        _atomic_write_json(writer_report_path, report)
        return report

    _atomic_write_json(artifact_path, runtime_report)
    artifact_hash = sha256_file(artifact_path)
    temp_count = len(list(artifact_dir.glob(f".{artifact_path.name}.*.tmp"))) + len(list(artifact_dir.glob(f".{writer_report_path.name}.*.tmp")))
    report = _base_writer_report(
        writer_id=writer_id,
        runtime_report=runtime_report,
        root=root,
        artifact_path=artifact_path,
        writer_report_path=writer_report_path,
        writer_status="PASS" if temp_count == 0 else "BLOCKED",
        artifact_hash=artifact_hash,
        temp_artifact_count_after=temp_count,
        primary_blocker_code=None if temp_count == 0 else "PARTIAL_WRITE_RECOVERY_REQUIRED",
        blocker_message="No writer blocker; artifact is a SHADOW runtime stub, not long-run evidence."
        if temp_count == 0
        else "Temporary artifact remained after write and recovery review is required.",
    )
    _atomic_write_json(writer_report_path, report)
    return report


def validate_shadow_observation_artifact_writer_report(
    report: dict[str, Any],
    *,
    runtime_report: dict[str, Any] | None = None,
) -> ShadowObservationArtifactWriterValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "writer_id",
        "exchange",
        "market_type",
        "source_mode",
        "mode",
        "session_id",
        "writer_mode",
        "writer_status",
        "artifact_truth_role",
        "runtime_evidence_role",
        "dashboard_visibility_status",
        "source_runtime_report_id",
        "source_runtime_report_hash",
        "source_runtime_hash_verified",
        "artifact_path",
        "writer_report_path",
        "artifact_hash",
        "atomic_writer_status",
        "temp_artifact_count_after",
        "partial_write_detected",
        "actual_persistent_runtime_executed",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "order_adapter_called",
        "primary_blocker_code",
        "blocker_message",
        "next_operator_action",
        "writer_report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ShadowObservationArtifactWriterValidationResult("FAIL", f"writer report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != SHADOW_OBSERVATION_ARTIFACT_WRITER_SCHEMA_ID:
        return ShadowObservationArtifactWriterValidationResult("FAIL", "writer schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("writer_report_hash") != shadow_observation_artifact_writer_hash(report):
        return ShadowObservationArtifactWriterValidationResult("FAIL", "writer report hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return ShadowObservationArtifactWriterValidationResult("BLOCKED", "writer is MVP-4 scoped to UPBIT/KRW_SPOT", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_mode") != "PAPER" or report.get("mode") != "SHADOW":
        return ShadowObservationArtifactWriterValidationResult("BLOCKED", "writer must remain PAPER-source, SHADOW-output scoped", "SNAPSHOT_SCOPE_MISMATCH")
    artifact_path = str(report.get("artifact_path", "")).replace("\\", "/")
    writer_path = str(report.get("writer_report_path", "")).replace("\\", "/")
    if "/shadow/" not in artifact_path or "/shadow/" not in writer_path or "/paper/" in artifact_path or "/live/" in artifact_path:
        return ShadowObservationArtifactWriterValidationResult("BLOCKED", "writer artifact path is not SHADOW-only", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("writer_mode") != "ATOMIC_SHADOW_STUB_WRITER":
        return ShadowObservationArtifactWriterValidationResult("FAIL", "writer mode is unsupported", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("artifact_truth_role") != "shadow_runtime_stub_display_truth_only":
        return ShadowObservationArtifactWriterValidationResult("BLOCKED", "writer artifact cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if report.get("runtime_evidence_role") != "PERSISTENT_RUNTIME_STUB_ONLY":
        return ShadowObservationArtifactWriterValidationResult("BLOCKED", "writer cannot promote runtime stub into long-run evidence", "LIVE_FINAL_GUARD_FAILED")
    forbidden_true_fields = (
        "actual_persistent_runtime_executed",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "order_adapter_called",
    )
    if any(report.get(field) is True for field in forbidden_true_fields):
        return ShadowObservationArtifactWriterValidationResult("BLOCKED", "writer attempted live, promotion, order, or long-run evidence permission", "LIVE_FINAL_GUARD_FAILED")
    if runtime_report is not None:
        runtime_result = validate_shadow_observation_persistent_runtime_report(runtime_report)
        if runtime_result.status != "PASS":
            return ShadowObservationArtifactWriterValidationResult("BLOCKED", "source runtime report is not PASS", runtime_result.blocker_code)
        if report.get("source_runtime_report_hash") != runtime_report.get("runtime_report_hash"):
            return ShadowObservationArtifactWriterValidationResult("BLOCKED", "source runtime hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_runtime_hash_verified") is not True:
        return ShadowObservationArtifactWriterValidationResult("BLOCKED", "source runtime hash was not verified", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("writer_status") == "PASS":
        if report.get("atomic_writer_status") != "PASS" or report.get("temp_artifact_count_after") != 0 or report.get("partial_write_detected") is not False:
            return ShadowObservationArtifactWriterValidationResult("BLOCKED", "PASS writer report must have clean atomic write state", "PARTIAL_WRITE_RECOVERY_REQUIRED")
        if report.get("dashboard_visibility_status") != "VISIBLE_AS_STUB_ONLY":
            return ShadowObservationArtifactWriterValidationResult("BLOCKED", "PASS writer report must stay visible as stub only", "LIVE_FINAL_GUARD_FAILED")
        if report.get("primary_blocker_code") is not None:
            return ShadowObservationArtifactWriterValidationResult("BLOCKED", "PASS writer report cannot carry a primary blocker", report.get("primary_blocker_code"))
        return ShadowObservationArtifactWriterValidationResult("PASS", "SHADOW runtime artifact writer is atomic, display-only, and live-blocked", None)
    if report.get("writer_status") == "BLOCKED":
        if not report.get("primary_blocker_code"):
            return ShadowObservationArtifactWriterValidationResult("BLOCKED", "blocked writer report must expose blocker", "UNKNOWN_BLOCKED")
        return ShadowObservationArtifactWriterValidationResult("BLOCKED", "SHADOW runtime artifact writer remains blocked", str(report.get("primary_blocker_code")))
    return ShadowObservationArtifactWriterValidationResult("FAIL", "writer status is unknown", "SCHEMA_IDENTITY_MISMATCH")
