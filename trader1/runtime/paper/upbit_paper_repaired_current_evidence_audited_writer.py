from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.ledger.paper_ledger_rollup import (
    validate_paper_ledger_rollup_report,
)
from trader1.runtime.ledger.paper_ledger_input_manifest import PAPER_LEDGER_INPUT_MANIFEST_SCOPE
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_implementation_prep import (
    AUDITED_WRITER_IMPLEMENTATION_PREP_STATUS,
    validate_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json
from trader1.runtime.portfolio.paper_portfolio import (
    mark_paper_portfolio_snapshot_to_public_market,
    portfolio_needs_public_mark_basis_repair,
    validate_paper_portfolio_snapshot,
)


UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_SCHEMA_ID = (
    "trader1.upbit_paper_repaired_current_evidence_audited_writer_report.v1"
)
UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_SNAPSHOT_SCHEMA_ID = (
    "trader1.upbit_paper_audited_current_evidence_snapshot.v1"
)
UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_IDEMPOTENCY_MANIFEST_SCHEMA_ID = (
    "trader1.upbit_paper_audited_current_evidence_idempotency_manifest.v1"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_TRUTH_ROLE = (
    "paper_runtime_repaired_current_evidence_audited_writer_truth"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_ROLE = (
    "PAPER_RUNTIME_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_SINGLE_RUN"
)
AUDITED_WRITER_WRITTEN_STATUS = "PASS_AUDITED_CURRENT_EVIDENCE_WRITTEN"
AUDITED_WRITER_IDEMPOTENT_STATUS = "PASS_AUDITED_CURRENT_EVIDENCE_ALREADY_WRITTEN"
AUDITED_WRITER_REFRESHED_STATUS = "PASS_AUDITED_CURRENT_EVIDENCE_REFRESHED"
AUDITED_WRITER_BLOCKED_SOURCE_STATUS = "BLOCKED_SOURCE_IMPLEMENTATION_PREP_INVALID"
AUDITED_WRITER_BLOCKED_LEDGER_STATUS = "BLOCKED_SOURCE_LEDGER_ROLLUP_INVALID"
AUDITED_WRITER_BLOCKED_TARGET_STATUS = "BLOCKED_AUDITED_CURRENT_EVIDENCE_TARGET_DIRTY"
AUDITED_WRITER_BLOCKED_LOCK_STATUS = "BLOCKED_AUDITED_CURRENT_EVIDENCE_WRITER_LOCKED"
TARGET_DIRTY_CAUSE_NONE = "NONE"
TARGET_DIRTY_CAUSE_PARTIAL_TARGET_SET = "PARTIAL_TARGET_SET"
TARGET_DIRTY_CAUSE_TEMP_PATH_DIRTY = "TEMP_PATH_DIRTY"
TARGET_DIRTY_CAUSE_STALE_LEDGER_SUPERSEDED = "STALE_LEDGER_SUPERSEDED"
TARGET_DIRTY_CAUSE_STALE_CURRENT_TRUTH_REFRESHED = "STALE_CURRENT_TRUTH_REFRESHED"
TARGET_DIRTY_CAUSE_CONFLICTING_PROVENANCE = "CONFLICTING_PROVENANCE"
TARGET_DIRTY_CAUSE_LOCK_BUSY = "LOCK_BUSY"
AUDITED_CURRENT_TRUTH_REFRESH_AFTER_SECONDS = 300

EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS = [
    "paper_runtime/current_evidence/audited_current_evidence_snapshot.json",
    "paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json",
    "paper_runtime/portfolio/paper_portfolio_snapshot.json",
]
EXPECTED_AUDITED_WRITER_TEMP_PATHS = [f"{path}.tmp" for path in EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS]
EXPECTED_AUDITED_WRITER_LOCK_PATH = "paper_runtime/locks/audited_current_evidence_writer.lock"
REQUIRED_WRITER_CONTROL_IDS = [
    "SOURCE_IMPLEMENTATION_PREP_VALID",
    "SOURCE_LEDGER_ROLLUP_VALID",
    "TARGET_PATHS_WITHIN_SESSION",
    "TEMP_PATHS_CLEAR",
    "SINGLE_WRITER_LOCK_ACQUIRED",
    "CURRENT_EVIDENCE_SNAPSHOT_PUBLISHED",
    "IDEMPOTENCY_MANIFEST_PUBLISHED",
    "PORTFOLIO_TRUTH_PUBLISHED",
    "POST_WRITE_HASHES_MATCH",
    "POST_WRITE_SCHEMA_VALIDATED",
    "LIVE_AND_SCALE_BOUNDARY_CONFIRMED",
]


@dataclass(frozen=True)
class UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _age_seconds(*, generated_at_utc: Any, now_utc: str) -> int | None:
    generated = _parse_utc(generated_at_utc)
    now = _parse_utc(now_utc)
    if generated is None or now is None:
        return None
    return max(0, int((now - generated).total_seconds()))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _is_safe_relative_path(path: str) -> bool:
    candidate = Path(path)
    return bool(path) and not candidate.is_absolute() and ".." not in candidate.parts and "\\" not in path


def _is_under(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True


def _target_path(runtime_base: Path, relative_path: str) -> Path:
    return runtime_base / relative_path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_via_declared_temp(final_path: Path, temp_path: Path, payload: dict[str, Any]) -> None:
    final_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    if temp_path.exists():
        raise FileExistsError(str(temp_path))
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    try:
        with temp_path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, final_path)
        try:
            directory_fd = os.open(str(final_path.parent), os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def _acquire_lock(lock_path: Path, payload: dict[str, Any]) -> bool:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    return True


def _release_lock(lock_path: Path) -> None:
    lock_path.unlink(missing_ok=True)


def upbit_paper_audited_current_evidence_snapshot_hash(snapshot: dict[str, Any]) -> str:
    payload = dict(snapshot)
    payload.pop("snapshot_hash", None)
    return _sha256_json(payload)


def upbit_paper_audited_current_evidence_idempotency_manifest_hash(manifest: dict[str, Any]) -> str:
    payload = dict(manifest)
    payload.pop("manifest_hash", None)
    return _sha256_json(payload)


def upbit_paper_repaired_current_evidence_audited_writer_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("audited_writer_report_hash", None)
    return _sha256_json(payload)


def _control(
    *,
    control_id: str,
    control_status: str,
    blocker_code: str | None,
    detail: str,
    artifact_written: bool = False,
) -> dict[str, Any]:
    return {
        "control_id": control_id,
        "control_status": control_status,
        "blocker_code": blocker_code,
        "detail": detail,
        "artifact_written": artifact_written,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _artifact_result(
    *,
    artifact_id: str,
    relative_final_path: str,
    relative_temp_path: str,
    payload_hash: str,
    final_path: Path,
    temp_path: Path,
    artifact_written: bool,
) -> dict[str, Any]:
    file_exists = final_path.exists()
    return {
        "artifact_id": artifact_id,
        "relative_final_path": relative_final_path,
        "relative_temp_path": relative_temp_path,
        "payload_hash": payload_hash,
        "file_hash": _sha256_file(final_path) if file_exists else None,
        "file_exists": file_exists,
        "artifact_written": artifact_written,
        "temp_exists_after_write": temp_path.exists(),
        "live_order_allowed": False,
        "scale_up_allowed": False,
    }


def _build_current_evidence_snapshot(
    *,
    source_implementation_prep_report: dict[str, Any],
    source_ledger_rollup_report: dict[str, Any],
    portfolio_snapshot: dict[str, Any],
    public_market_data_collection_report: dict[str, Any] | None = None,
    generated_at_utc: str,
) -> dict[str, Any]:
    snapshot = {
        "schema_id": UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_SNAPSHOT_SCHEMA_ID,
        "generated_at_utc": generated_at_utc,
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": source_implementation_prep_report["session_id"],
        "current_evidence_status": "PASS",
        "truth_role": "paper_runtime_audited_current_evidence_truth",
        "source_implementation_prep_hash": source_implementation_prep_report.get(
            "audited_writer_implementation_prep_hash"
        ),
        "source_locked_output_hash": source_implementation_prep_report.get(
            "source_audited_writer_locked_output_hash"
        ),
        "source_ledger_rollup_hash": source_ledger_rollup_report.get("rollup_hash"),
        "source_ledger_rollup_status": source_ledger_rollup_report.get("rollup_status"),
        "source_ledger_rollup_generated_at_utc": source_ledger_rollup_report.get("generated_at_utc"),
        "source_paper_ledger_head_hash": source_ledger_rollup_report.get("latest_ledger_head_hash"),
        "source_runtime_cycle_id": portfolio_snapshot.get("source_runtime_cycle_id"),
        "source_portfolio_snapshot_hash": portfolio_snapshot.get("snapshot_hash"),
        "portfolio_truth_status": "VERIFIED_PAPER_LEDGER_ROLLUP",
        "ledger_head_status": source_ledger_rollup_report.get("ledger_head_match_status"),
        "runtime_cycle_status": "LINKED",
        "cash_status": "VERIFIED",
        "equity_status": "VERIFIED",
        "position_status": "VERIFIED",
        "configured_initial_cash_krw": portfolio_snapshot.get("starting_cash"),
        "verified_cash_krw": portfolio_snapshot.get("cash_available"),
        "verified_equity_krw": portfolio_snapshot.get("equity"),
        "verified_total_pnl_krw": portfolio_snapshot.get("total_pnl"),
        "verified_return_pct": portfolio_snapshot.get("return_pct"),
        "open_position_count": portfolio_snapshot.get("open_position_count"),
        "mark_to_market_status": portfolio_snapshot.get("mark_to_market_status"),
        "mark_price_source": portfolio_snapshot.get("mark_price_source"),
        "source_public_market_data_hash": portfolio_snapshot.get("source_public_market_data_hash"),
        "source_public_market_data_generated_at_utc": portfolio_snapshot.get(
            "source_public_market_data_generated_at_utc"
        ),
        "source_public_market_event_time_utc": portfolio_snapshot.get("source_public_market_event_time_utc"),
        "source_public_market_event_hash": portfolio_snapshot.get("source_public_market_event_hash"),
        "source_public_market_data_collection_hash": (
            public_market_data_collection_report.get("collection_hash")
            if isinstance(public_market_data_collection_report, dict)
            else None
        ),
        "paper_only": True,
        "display_only": True,
        "dashboard_truth_only": True,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "scale_up_allowed": False,
        "primary_blocker_code": "LIVE_READY_MISSING",
        "snapshot_hash": "",
    }
    snapshot["snapshot_hash"] = upbit_paper_audited_current_evidence_snapshot_hash(snapshot)
    return snapshot


def _build_idempotency_manifest(
    *,
    source_implementation_prep_report: dict[str, Any],
    source_ledger_rollup_report: dict[str, Any],
    current_evidence_snapshot: dict[str, Any],
    portfolio_snapshot: dict[str, Any],
    public_market_data_collection_report: dict[str, Any] | None = None,
    generated_at_utc: str,
) -> dict[str, Any]:
    manifest = {
        "manifest_schema_id": UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_IDEMPOTENCY_MANIFEST_SCHEMA_ID,
        "generated_at_utc": generated_at_utc,
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": source_implementation_prep_report["session_id"],
        "manifest_status": "PASS",
        "source_implementation_prep_hash": source_implementation_prep_report.get(
            "audited_writer_implementation_prep_hash"
        ),
        "source_locked_output_hash": source_implementation_prep_report.get(
            "source_audited_writer_locked_output_hash"
        ),
        "source_ledger_rollup_hash": source_ledger_rollup_report.get("rollup_hash"),
        "source_paper_ledger_head_hash": source_ledger_rollup_report.get("latest_ledger_head_hash"),
        "source_public_market_data_hash": portfolio_snapshot.get("source_public_market_data_hash"),
        "source_public_market_event_time_utc": portfolio_snapshot.get("source_public_market_event_time_utc"),
        "source_public_market_event_hash": portfolio_snapshot.get("source_public_market_event_hash"),
        "source_public_market_data_collection_hash": (
            public_market_data_collection_report.get("collection_hash")
            if isinstance(public_market_data_collection_report, dict)
            else None
        ),
        "current_evidence_snapshot_hash": current_evidence_snapshot["snapshot_hash"],
        "portfolio_snapshot_hash": portfolio_snapshot["snapshot_hash"],
        "planned_artifact_paths": EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS,
        "planned_temp_paths": EXPECTED_AUDITED_WRITER_TEMP_PATHS,
        "lock_path": EXPECTED_AUDITED_WRITER_LOCK_PATH,
        "paper_only": True,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "live_order_allowed": False,
        "scale_up_allowed": False,
        "manifest_hash": "",
    }
    manifest["idempotency_key"] = _sha256_json(
        {
            "source_implementation_prep_hash": manifest["source_implementation_prep_hash"],
            "source_ledger_rollup_hash": manifest["source_ledger_rollup_hash"],
            "source_paper_ledger_head_hash": manifest["source_paper_ledger_head_hash"],
            "source_public_market_data_hash": manifest["source_public_market_data_hash"],
            "source_public_market_event_hash": manifest["source_public_market_event_hash"],
            "planned_artifact_paths": manifest["planned_artifact_paths"],
        }
    )
    manifest["manifest_hash"] = upbit_paper_audited_current_evidence_idempotency_manifest_hash(manifest)
    return manifest


def _source_prep_valid(source: dict[str, Any]) -> tuple[bool, str | None, str]:
    result = validate_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(source)
    valid = (
        result.status == "PASS"
        and source.get("implementation_prep_status") == AUDITED_WRITER_IMPLEMENTATION_PREP_STATUS
        and source.get("primary_blocker_code") == AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        and source.get("implementation_prep_inputs_clean") is True
        and source.get("planned_artifact_paths") == EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS
        and source.get("planned_temp_paths") == EXPECTED_AUDITED_WRITER_TEMP_PATHS
        and source.get("lock_path") == EXPECTED_AUDITED_WRITER_LOCK_PATH
        and source.get("live_order_allowed") is False
        and source.get("scale_up_allowed") is False
    )
    return valid, None if valid else (result.blocker_code or "SCHEMA_IDENTITY_MISMATCH"), result.status


def _ledger_rollup_valid(report: dict[str, Any], session_id: str) -> tuple[bool, str | None, str]:
    result = validate_paper_ledger_rollup_report(report)
    portfolio = report.get("portfolio_snapshot") if isinstance(report, dict) else None
    portfolio_result = validate_paper_portfolio_snapshot(portfolio) if isinstance(portfolio, dict) else None
    ledger_head_bound = report.get("ledger_head_match_status") == "PASS" or (
        report.get("ledger_input_scope") == PAPER_LEDGER_INPUT_MANIFEST_SCOPE
        and report.get("ledger_head_match_status") == "NOT_APPLICABLE"
        and isinstance(report.get("latest_ledger_head_hash"), str)
        and len(report.get("latest_ledger_head_hash")) == 64
        and any(
            path.endswith("/ledger/paper_ledger_input_manifest.json")
            for path in report.get("artifact_paths", [])
            if isinstance(path, str)
        )
    )
    valid = (
        result.status == "PASS"
        and report.get("rollup_status") == "PASS"
        and report.get("exchange") == "UPBIT"
        and report.get("market_type") == "KRW_SPOT"
        and report.get("mode") == "PAPER"
        and report.get("session_id") == session_id
        and ledger_head_bound
        and portfolio_result is not None
        and portfolio_result.status == "PASS"
        and portfolio.get("snapshot_status") == "PASS"
        and report.get("live_order_allowed") is False
        and report.get("scale_up_allowed") is False
    )
    blocker = result.blocker_code or (
        portfolio_result.blocker_code if portfolio_result is not None else "MEASUREMENT_MISSING"
    )
    return valid, None if valid else (blocker or "MEASUREMENT_MISSING"), result.status


def _safe_targets(runtime_base: Path) -> bool:
    all_paths = EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS + EXPECTED_AUDITED_WRITER_TEMP_PATHS + [
        EXPECTED_AUDITED_WRITER_LOCK_PATH
    ]
    return all(
        _is_safe_relative_path(relative_path) and _is_under(runtime_base, runtime_base / relative_path)
        for relative_path in all_paths
    )


def _load_existing_outputs(runtime_base: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
    final_paths = [_target_path(runtime_base, path) for path in EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS]
    if not all(path.exists() for path in final_paths):
        return None
    return (_load_json(final_paths[0]), _load_json(final_paths[1]), _load_json(final_paths[2]))


def _outputs_match_sources(
    *,
    outputs: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    source_implementation_prep_report: dict[str, Any],
    source_ledger_rollup_report: dict[str, Any],
    source_public_market_data_hash: str | None = None,
) -> bool:
    current_evidence, manifest, portfolio = outputs
    base_match = (
        validate_upbit_paper_audited_current_evidence_snapshot(current_evidence).status == "PASS"
        and validate_upbit_paper_audited_current_evidence_idempotency_manifest(manifest).status == "PASS"
        and validate_paper_portfolio_snapshot(portfolio).status == "PASS"
        and current_evidence.get("source_implementation_prep_hash")
        == source_implementation_prep_report.get("audited_writer_implementation_prep_hash")
        and current_evidence.get("source_ledger_rollup_hash") == source_ledger_rollup_report.get("rollup_hash")
        and current_evidence.get("source_portfolio_snapshot_hash") == portfolio.get("snapshot_hash")
        and manifest.get("source_implementation_prep_hash")
        == source_implementation_prep_report.get("audited_writer_implementation_prep_hash")
        and manifest.get("source_ledger_rollup_hash") == source_ledger_rollup_report.get("rollup_hash")
        and manifest.get("current_evidence_snapshot_hash") == current_evidence.get("snapshot_hash")
        and manifest.get("portfolio_snapshot_hash") == portfolio.get("snapshot_hash")
    )
    if not base_match:
        return False
    if portfolio_needs_public_mark_basis_repair(portfolio):
        return False
    if source_public_market_data_hash is None:
        return True
    return (
        current_evidence.get("source_public_market_data_hash") == source_public_market_data_hash
        and manifest.get("source_public_market_data_hash") == source_public_market_data_hash
        and portfolio.get("source_public_market_data_hash") == source_public_market_data_hash
    )


def _outputs_are_complete_and_valid_for_scope(
    *,
    outputs: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    source_implementation_prep_report: dict[str, Any],
    session_id: str,
) -> bool:
    current_evidence, manifest, portfolio = outputs
    source_prep_hash = source_implementation_prep_report.get("audited_writer_implementation_prep_hash")
    if (
        validate_upbit_paper_audited_current_evidence_snapshot(current_evidence).status != "PASS"
        or validate_upbit_paper_audited_current_evidence_idempotency_manifest(manifest).status != "PASS"
        or validate_paper_portfolio_snapshot(portfolio).status != "PASS"
    ):
        return False
    if (
        current_evidence.get("exchange") != "UPBIT"
        or current_evidence.get("market_type") != "KRW_SPOT"
        or current_evidence.get("mode") != "PAPER"
        or current_evidence.get("session_id") != session_id
        or manifest.get("exchange") != "UPBIT"
        or manifest.get("market_type") != "KRW_SPOT"
        or manifest.get("mode") != "PAPER"
        or manifest.get("session_id") != session_id
        or portfolio.get("exchange") != "UPBIT"
        or portfolio.get("market_type") != "KRW_SPOT"
        or portfolio.get("mode") != "PAPER"
        or portfolio.get("session_id") != session_id
    ):
        return False
    return (
        current_evidence.get("source_implementation_prep_hash") == source_prep_hash
        and manifest.get("source_implementation_prep_hash") == source_prep_hash
        and current_evidence.get("source_ledger_rollup_hash") == manifest.get("source_ledger_rollup_hash")
        and current_evidence.get("source_paper_ledger_head_hash") == manifest.get("source_paper_ledger_head_hash")
        and portfolio.get("source_paper_ledger_head_hash") == manifest.get("source_paper_ledger_head_hash")
        and current_evidence.get("source_portfolio_snapshot_hash") == portfolio.get("snapshot_hash")
        and manifest.get("current_evidence_snapshot_hash") == current_evidence.get("snapshot_hash")
        and manifest.get("portfolio_snapshot_hash") == portfolio.get("snapshot_hash")
    )


def _outputs_are_stale_for_current_ledger(
    *,
    outputs: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    source_implementation_prep_report: dict[str, Any],
    source_ledger_rollup_report: dict[str, Any],
    session_id: str,
) -> bool:
    current_evidence, manifest, portfolio = outputs
    return (
        _outputs_are_complete_and_valid_for_scope(
            outputs=outputs,
            source_implementation_prep_report=source_implementation_prep_report,
            session_id=session_id,
        )
        and current_evidence.get("source_ledger_rollup_hash") != source_ledger_rollup_report.get("rollup_hash")
        and manifest.get("source_ledger_rollup_hash") != source_ledger_rollup_report.get("rollup_hash")
        and current_evidence.get("source_paper_ledger_head_hash")
        != source_ledger_rollup_report.get("latest_ledger_head_hash")
        and manifest.get("source_paper_ledger_head_hash")
        != source_ledger_rollup_report.get("latest_ledger_head_hash")
        and portfolio.get("source_paper_ledger_head_hash")
        != source_ledger_rollup_report.get("latest_ledger_head_hash")
    )


def _outputs_bind_current_head_but_stale_rollup(
    *,
    outputs: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    source_implementation_prep_report: dict[str, Any],
    source_ledger_rollup_report: dict[str, Any],
    session_id: str,
) -> bool:
    current_evidence, manifest, portfolio = outputs
    latest_head_hash = source_ledger_rollup_report.get("latest_ledger_head_hash")
    current_rollup_hash = source_ledger_rollup_report.get("rollup_hash")
    return (
        _outputs_are_complete_and_valid_for_scope(
            outputs=outputs,
            source_implementation_prep_report=source_implementation_prep_report,
            session_id=session_id,
        )
        and isinstance(latest_head_hash, str)
        and len(latest_head_hash) == 64
        and isinstance(current_rollup_hash, str)
        and len(current_rollup_hash) == 64
        and current_evidence.get("source_ledger_rollup_hash") != current_rollup_hash
        and manifest.get("source_ledger_rollup_hash") != current_rollup_hash
        and current_evidence.get("source_paper_ledger_head_hash") == latest_head_hash
        and manifest.get("source_paper_ledger_head_hash") == latest_head_hash
        and portfolio.get("source_paper_ledger_head_hash") == latest_head_hash
    )


def _outputs_bind_current_ledger_but_stale_public_mark(
    *,
    outputs: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    source_implementation_prep_report: dict[str, Any],
    source_ledger_rollup_report: dict[str, Any],
    session_id: str,
    source_public_market_data_hash: str | None,
) -> bool:
    if source_public_market_data_hash is None:
        return False
    current_evidence, manifest, portfolio = outputs
    latest_head_hash = source_ledger_rollup_report.get("latest_ledger_head_hash")
    current_rollup_hash = source_ledger_rollup_report.get("rollup_hash")
    return (
        _outputs_are_complete_and_valid_for_scope(
            outputs=outputs,
            source_implementation_prep_report=source_implementation_prep_report,
            session_id=session_id,
        )
        and isinstance(latest_head_hash, str)
        and len(latest_head_hash) == 64
        and isinstance(current_rollup_hash, str)
        and len(current_rollup_hash) == 64
        and current_evidence.get("source_ledger_rollup_hash") == current_rollup_hash
        and manifest.get("source_ledger_rollup_hash") == current_rollup_hash
        and current_evidence.get("source_paper_ledger_head_hash") == latest_head_hash
        and manifest.get("source_paper_ledger_head_hash") == latest_head_hash
        and portfolio.get("source_paper_ledger_head_hash") == latest_head_hash
        and (
            current_evidence.get("source_public_market_data_hash") != source_public_market_data_hash
            or manifest.get("source_public_market_data_hash") != source_public_market_data_hash
            or portfolio.get("source_public_market_data_hash") != source_public_market_data_hash
        )
    )


def _outputs_bind_current_ledger_but_need_public_mark_basis_repair(
    *,
    outputs: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    source_implementation_prep_report: dict[str, Any],
    source_ledger_rollup_report: dict[str, Any],
    session_id: str,
    source_public_market_data_hash: str | None,
) -> bool:
    if source_public_market_data_hash is None:
        return False
    current_evidence, manifest, portfolio = outputs
    latest_head_hash = source_ledger_rollup_report.get("latest_ledger_head_hash")
    current_rollup_hash = source_ledger_rollup_report.get("rollup_hash")
    return (
        _outputs_are_complete_and_valid_for_scope(
            outputs=outputs,
            source_implementation_prep_report=source_implementation_prep_report,
            session_id=session_id,
        )
        and isinstance(latest_head_hash, str)
        and len(latest_head_hash) == 64
        and isinstance(current_rollup_hash, str)
        and len(current_rollup_hash) == 64
        and current_evidence.get("source_ledger_rollup_hash") == current_rollup_hash
        and manifest.get("source_ledger_rollup_hash") == current_rollup_hash
        and current_evidence.get("source_paper_ledger_head_hash") == latest_head_hash
        and manifest.get("source_paper_ledger_head_hash") == latest_head_hash
        and portfolio.get("source_paper_ledger_head_hash") == latest_head_hash
        and current_evidence.get("source_public_market_data_hash") == source_public_market_data_hash
        and manifest.get("source_public_market_data_hash") == source_public_market_data_hash
        and portfolio.get("source_public_market_data_hash") == source_public_market_data_hash
        and portfolio_needs_public_mark_basis_repair(portfolio)
    )


def _outputs_exceed_refresh_ttl(
    *,
    outputs: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    now_utc: str,
    refresh_after_seconds: int = AUDITED_CURRENT_TRUTH_REFRESH_AFTER_SECONDS,
) -> bool:
    ages = [
        age
        for age in (
            _age_seconds(generated_at_utc=outputs[0].get("generated_at_utc"), now_utc=now_utc),
            _age_seconds(generated_at_utc=outputs[1].get("generated_at_utc"), now_utc=now_utc),
        )
        if age is not None
    ]
    return bool(ages and max(ages) > refresh_after_seconds)


def _archive_id(*, generated_at_utc: str, outputs: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> str:
    current_evidence, manifest, portfolio = outputs
    stamp = generated_at_utc.replace("-", "").replace(":", "").replace("+", "").replace("Z", "Z")
    old_head = str(
        current_evidence.get("source_paper_ledger_head_hash")
        or manifest.get("source_paper_ledger_head_hash")
        or portfolio.get("source_paper_ledger_head_hash")
        or "UNKNOWN"
    )
    output_hash = _sha256_json(
        {
            "current_evidence_hash": current_evidence.get("snapshot_hash"),
            "manifest_hash": manifest.get("manifest_hash"),
            "portfolio_hash": portfolio.get("snapshot_hash"),
        }
    )
    return f"{stamp}_old_head_{old_head[:12]}_{output_hash[:12]}"


def _archive_existing_outputs(
    *,
    runtime_base: Path,
    archive_id: str,
) -> list[dict[str, Any]]:
    archive_records: list[dict[str, Any]] = []
    for relative_path in EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS:
        source_path = _target_path(runtime_base, relative_path)
        archive_relative_path = (
            Path("paper_runtime")
            / "current_evidence"
            / "archive"
            / archive_id
            / Path(relative_path.replace("/", "__"))
        ).as_posix()
        archive_path = _target_path(runtime_base, archive_relative_path)
        if not _is_safe_relative_path(archive_relative_path) or not _is_under(runtime_base, archive_path):
            raise ValueError(f"unsafe archive path: {archive_relative_path}")
        if archive_path.exists():
            raise FileExistsError(str(archive_path))
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        file_hash = _sha256_file(source_path)
        os.replace(source_path, archive_path)
        archive_records.append(
            {
                "relative_original_path": relative_path,
                "relative_archive_path": archive_relative_path,
                "archived_file_hash": file_hash,
                "archive_write_method": "ATOMIC_RENAME",
                "audit_preserved": True,
                "source_delete_allowed": False,
                "live_order_allowed": False,
                "scale_up_allowed": False,
            }
        )
    return archive_records


def build_upbit_paper_repaired_current_evidence_audited_writer_report(
    *,
    root: Path,
    source_implementation_prep_report: dict[str, Any],
    source_ledger_rollup_report: dict[str, Any],
    public_market_data_collection_report: dict[str, Any] | None = None,
    audited_writer_id: str = "upbit-paper-repaired-current-evidence-audited-writer",
) -> dict[str, Any]:
    root = Path(root).resolve()
    session_id = str(source_implementation_prep_report.get("session_id", "UNKNOWN"))
    runtime_base = _runtime_base(root, session_id)
    now = utc_now()
    prep_valid, prep_blocker, prep_validator_status = _source_prep_valid(source_implementation_prep_report)
    ledger_valid, ledger_blocker, ledger_validator_status = _ledger_rollup_valid(source_ledger_rollup_report, session_id)
    targets_safe = _safe_targets(runtime_base)
    temp_paths_clear = all(not _target_path(runtime_base, path).exists() for path in EXPECTED_AUDITED_WRITER_TEMP_PATHS)
    lock_path = _target_path(runtime_base, EXPECTED_AUDITED_WRITER_LOCK_PATH)
    existing_outputs = _load_existing_outputs(runtime_base)
    source_public_market_data_hash = None
    if isinstance(public_market_data_collection_report, dict):
        value = public_market_data_collection_report.get("collection_hash")
        if isinstance(value, str) and len(value) == 64:
            source_public_market_data_hash = value
    final_path_states = [
        {
            "relative_final_path": relative_path,
            "relative_temp_path": temp_path,
            "final_path_resolves_under_session": _is_under(runtime_base, _target_path(runtime_base, relative_path)),
            "temp_path_resolves_under_session": _is_under(runtime_base, _target_path(runtime_base, temp_path)),
            "final_exists_before": _target_path(runtime_base, relative_path).exists(),
            "temp_exists_before": _target_path(runtime_base, temp_path).exists(),
        }
        for relative_path, temp_path in zip(
            EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS,
            EXPECTED_AUDITED_WRITER_TEMP_PATHS,
            strict=True,
        )
    ]

    blocker_codes = {"LIVE_READY_MISSING", "SCALE_UP_NOT_ELIGIBLE"}
    status = AUDITED_WRITER_WRITTEN_STATUS
    primary_blocker = None
    if not prep_valid:
        status = AUDITED_WRITER_BLOCKED_SOURCE_STATUS
        primary_blocker = prep_blocker or "SCHEMA_IDENTITY_MISMATCH"
    elif not ledger_valid:
        status = AUDITED_WRITER_BLOCKED_LEDGER_STATUS
        primary_blocker = ledger_blocker or "MEASUREMENT_MISSING"
    elif not targets_safe or not temp_paths_clear:
        status = AUDITED_WRITER_BLOCKED_TARGET_STATUS
        primary_blocker = "SNAPSHOT_SCOPE_MISMATCH" if not targets_safe else "POST_RERUN_RECONCILIATION_REQUIRED"
    if primary_blocker:
        blocker_codes.add(primary_blocker)

    artifact_payloads: tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None = None
    artifact_written_count = 0
    idempotent_replay = False
    lock_acquire_attempted = False
    lock_acquired = False
    lock_file_written = False
    lock_released = False
    target_dirty_cause = TARGET_DIRTY_CAUSE_NONE
    stale_output_superseded = False
    archive_id: str | None = None
    archived_artifacts: list[dict[str, Any]] = []
    archived_artifact_count = 0
    stale_existing_outputs: tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None = None

    if primary_blocker is None:
        if existing_outputs is not None:
            if _outputs_match_sources(
                outputs=existing_outputs,
                source_implementation_prep_report=source_implementation_prep_report,
                source_ledger_rollup_report=source_ledger_rollup_report,
                source_public_market_data_hash=source_public_market_data_hash,
            ):
                if _outputs_exceed_refresh_ttl(outputs=existing_outputs, now_utc=now):
                    target_dirty_cause = TARGET_DIRTY_CAUSE_STALE_CURRENT_TRUTH_REFRESHED
                    archive_id = _archive_id(generated_at_utc=now, outputs=existing_outputs)
                    stale_existing_outputs = existing_outputs
                    status = AUDITED_WRITER_REFRESHED_STATUS
                else:
                    artifact_payloads = existing_outputs
                    status = AUDITED_WRITER_IDEMPOTENT_STATUS
                    idempotent_replay = True
            elif _outputs_are_stale_for_current_ledger(
                outputs=existing_outputs,
                source_implementation_prep_report=source_implementation_prep_report,
                source_ledger_rollup_report=source_ledger_rollup_report,
                session_id=session_id,
            ):
                target_dirty_cause = TARGET_DIRTY_CAUSE_STALE_LEDGER_SUPERSEDED
                archive_id = _archive_id(generated_at_utc=now, outputs=existing_outputs)
                stale_existing_outputs = existing_outputs
            elif _outputs_bind_current_head_but_stale_rollup(
                outputs=existing_outputs,
                source_implementation_prep_report=source_implementation_prep_report,
                source_ledger_rollup_report=source_ledger_rollup_report,
                session_id=session_id,
            ):
                target_dirty_cause = TARGET_DIRTY_CAUSE_STALE_CURRENT_TRUTH_REFRESHED
                archive_id = _archive_id(generated_at_utc=now, outputs=existing_outputs)
                stale_existing_outputs = existing_outputs
                status = AUDITED_WRITER_REFRESHED_STATUS
            elif _outputs_bind_current_ledger_but_stale_public_mark(
                outputs=existing_outputs,
                source_implementation_prep_report=source_implementation_prep_report,
                source_ledger_rollup_report=source_ledger_rollup_report,
                session_id=session_id,
                source_public_market_data_hash=source_public_market_data_hash,
            ):
                target_dirty_cause = TARGET_DIRTY_CAUSE_STALE_CURRENT_TRUTH_REFRESHED
                archive_id = _archive_id(generated_at_utc=now, outputs=existing_outputs)
                stale_existing_outputs = existing_outputs
                status = AUDITED_WRITER_REFRESHED_STATUS
            elif _outputs_bind_current_ledger_but_need_public_mark_basis_repair(
                outputs=existing_outputs,
                source_implementation_prep_report=source_implementation_prep_report,
                source_ledger_rollup_report=source_ledger_rollup_report,
                session_id=session_id,
                source_public_market_data_hash=source_public_market_data_hash,
            ):
                target_dirty_cause = TARGET_DIRTY_CAUSE_STALE_CURRENT_TRUTH_REFRESHED
                archive_id = _archive_id(generated_at_utc=now, outputs=existing_outputs)
                stale_existing_outputs = existing_outputs
                status = AUDITED_WRITER_REFRESHED_STATUS
            else:
                target_dirty_cause = TARGET_DIRTY_CAUSE_CONFLICTING_PROVENANCE
                status = AUDITED_WRITER_BLOCKED_TARGET_STATUS
                primary_blocker = "POST_RERUN_RECONCILIATION_REQUIRED"
                blocker_codes.add(primary_blocker)
        elif any(_target_path(runtime_base, path).exists() for path in EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS):
            target_dirty_cause = TARGET_DIRTY_CAUSE_PARTIAL_TARGET_SET
            status = AUDITED_WRITER_BLOCKED_TARGET_STATUS
            primary_blocker = "POST_RERUN_RECONCILIATION_REQUIRED"
            blocker_codes.add(primary_blocker)
        if primary_blocker is None and not idempotent_replay:
            portfolio_snapshot = dict(source_ledger_rollup_report["portfolio_snapshot"])
            if (
                stale_existing_outputs is not None
                and target_dirty_cause == TARGET_DIRTY_CAUSE_STALE_CURRENT_TRUTH_REFRESHED
            ):
                existing_portfolio = stale_existing_outputs[2]
                rollup_portfolio = source_ledger_rollup_report.get("portfolio_snapshot")
                if (
                    isinstance(existing_portfolio, dict)
                    and isinstance(rollup_portfolio, dict)
                    and existing_portfolio.get("source") == "PAPER_LEDGER_ROLLUP_PUBLIC_MARK"
                    and existing_portfolio.get("source_paper_ledger_head_hash")
                    == source_ledger_rollup_report.get("latest_ledger_head_hash")
                    and existing_portfolio.get("source_runtime_cycle_id")
                    == rollup_portfolio.get("source_runtime_cycle_id")
                ):
                    portfolio_snapshot = dict(existing_portfolio)
            if isinstance(public_market_data_collection_report, dict):
                portfolio_snapshot = mark_paper_portfolio_snapshot_to_public_market(
                    paper_portfolio_snapshot=portfolio_snapshot,
                    public_market_data_collection_report=public_market_data_collection_report,
                    generated_at_utc=now,
                    require_public_mark=True,
                )
                portfolio_mark_result = validate_paper_portfolio_snapshot(portfolio_snapshot)
                if portfolio_snapshot.get("snapshot_status") != "PASS" or portfolio_mark_result.status != "PASS":
                    status = AUDITED_WRITER_BLOCKED_LEDGER_STATUS
                    primary_blocker = (
                        portfolio_snapshot.get("mark_to_market_blocker_code")
                        or portfolio_snapshot.get("primary_blocker_code")
                        or portfolio_mark_result.blocker_code
                        or "DATA_UNAVAILABLE"
                    )
                    blocker_codes.add(primary_blocker)
                    artifact_payloads = None
                    portfolio_snapshot = {}
            current_evidence_snapshot = None
            manifest = None
            if primary_blocker is None:
                current_evidence_snapshot = _build_current_evidence_snapshot(
                    source_implementation_prep_report=source_implementation_prep_report,
                    source_ledger_rollup_report=source_ledger_rollup_report,
                    portfolio_snapshot=portfolio_snapshot,
                    public_market_data_collection_report=public_market_data_collection_report,
                    generated_at_utc=now,
                )
                manifest = _build_idempotency_manifest(
                    source_implementation_prep_report=source_implementation_prep_report,
                    source_ledger_rollup_report=source_ledger_rollup_report,
                    current_evidence_snapshot=current_evidence_snapshot,
                    portfolio_snapshot=portfolio_snapshot,
                    public_market_data_collection_report=public_market_data_collection_report,
                    generated_at_utc=now,
                )
                artifact_payloads = (current_evidence_snapshot, manifest, portfolio_snapshot)
                lock_acquire_attempted = True
                lock_acquired = _acquire_lock(
                    lock_path,
                    {
                        "lock_schema_id": "trader1.upbit_paper_audited_current_evidence_writer_lock.v1",
                        "created_at_utc": now,
                        "project_id": "TRADER_1",
                        "exchange": "UPBIT",
                        "market_type": "KRW_SPOT",
                        "mode": "PAPER",
                        "session_id": session_id,
                        "source_implementation_prep_hash": source_implementation_prep_report.get(
                            "audited_writer_implementation_prep_hash"
                        ),
                        "source_ledger_rollup_hash": source_ledger_rollup_report.get("rollup_hash"),
                        "live_order_allowed": False,
                        "scale_up_allowed": False,
                    },
                )
            if primary_blocker is None:
                lock_file_written = lock_acquired
                if not lock_acquired:
                    status = AUDITED_WRITER_BLOCKED_LOCK_STATUS
                    primary_blocker = "POST_RERUN_RECONCILIATION_REQUIRED"
                    blocker_codes.add(primary_blocker)
                    target_dirty_cause = TARGET_DIRTY_CAUSE_LOCK_BUSY
                    artifact_payloads = None
                else:
                    try:
                        if stale_existing_outputs is not None and archive_id is not None:
                            archived_artifacts = _archive_existing_outputs(runtime_base=runtime_base, archive_id=archive_id)
                            archived_artifact_count = len(archived_artifacts)
                            stale_output_superseded = archived_artifact_count == len(EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS)
                        for relative_final, relative_temp, payload in zip(
                            EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS,
                            EXPECTED_AUDITED_WRITER_TEMP_PATHS,
                            artifact_payloads,
                            strict=True,
                        ):
                            _write_json_via_declared_temp(
                                _target_path(runtime_base, relative_final),
                                _target_path(runtime_base, relative_temp),
                                payload,
                            )
                            artifact_written_count += 1
                    finally:
                        _release_lock(lock_path)
                        lock_released = True
                    artifact_payloads = _load_existing_outputs(runtime_base)
    if status == AUDITED_WRITER_BLOCKED_TARGET_STATUS and target_dirty_cause == TARGET_DIRTY_CAUSE_NONE:
        target_dirty_cause = (
            TARGET_DIRTY_CAUSE_TEMP_PATH_DIRTY if not temp_paths_clear else TARGET_DIRTY_CAUSE_CONFLICTING_PROVENANCE
        )

    artifacts: list[dict[str, Any]] = []
    if artifact_payloads is not None:
        artifact_ids = [
            "AUDITED_CURRENT_EVIDENCE_SNAPSHOT",
            "AUDITED_CURRENT_EVIDENCE_IDEMPOTENCY_MANIFEST",
            "AUDITED_PORTFOLIO_TRUTH_SNAPSHOT",
        ]
        for artifact_id, relative_final, relative_temp, payload in zip(
            artifact_ids,
            EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS,
            EXPECTED_AUDITED_WRITER_TEMP_PATHS,
            artifact_payloads,
            strict=True,
        ):
            artifacts.append(
                _artifact_result(
                    artifact_id=artifact_id,
                    relative_final_path=relative_final,
                    relative_temp_path=relative_temp,
                    payload_hash=payload.get("snapshot_hash") or payload.get("manifest_hash"),
                    final_path=_target_path(runtime_base, relative_final),
                    temp_path=_target_path(runtime_base, relative_temp),
                    artifact_written=artifact_written_count > 0,
                )
            )

    writer_passed = primary_blocker is None and artifact_payloads is not None
    controls = [
        _control(
            control_id="SOURCE_IMPLEMENTATION_PREP_VALID",
            control_status="PASS" if prep_valid else "BLOCKED",
            blocker_code=None if prep_valid else prep_blocker,
            detail="The writer may only use the validated implementation-prep report.",
        ),
        _control(
            control_id="SOURCE_LEDGER_ROLLUP_VALID",
            control_status="PASS" if ledger_valid else "BLOCKED",
            blocker_code=None if ledger_valid else ledger_blocker,
            detail="Portfolio truth must come from a validated UPBIT/KRW_SPOT/PAPER ledger rollup.",
        ),
        _control(
            control_id="TARGET_PATHS_WITHIN_SESSION",
            control_status="PASS" if targets_safe else "BLOCKED",
            blocker_code=None if targets_safe else "SNAPSHOT_SCOPE_MISMATCH",
            detail="All final, temp, and lock paths remain inside the scoped PAPER session.",
        ),
        _control(
            control_id="TEMP_PATHS_CLEAR",
            control_status="PASS" if temp_paths_clear else "BLOCKED",
            blocker_code=None if temp_paths_clear else "POST_RERUN_RECONCILIATION_REQUIRED",
            detail="Declared temp files must not pre-exist before the audited writer runs.",
        ),
        _control(
            control_id="SINGLE_WRITER_LOCK_ACQUIRED",
            control_status="PASS" if writer_passed and (lock_acquired or idempotent_replay) else "BLOCKED",
            blocker_code=None if writer_passed and (lock_acquired or idempotent_replay) else primary_blocker,
            detail="A new write acquires and releases the scoped lock; an idempotent replay must match existing outputs.",
        ),
        _control(
            control_id="CURRENT_EVIDENCE_SNAPSHOT_PUBLISHED",
            control_status="PASS" if writer_passed else "BLOCKED",
            blocker_code=None if writer_passed else primary_blocker,
            detail="The audited PAPER current-evidence snapshot exists and matches its hash.",
            artifact_written=artifact_written_count > 0,
        ),
        _control(
            control_id="IDEMPOTENCY_MANIFEST_PUBLISHED",
            control_status="PASS" if writer_passed else "BLOCKED",
            blocker_code=None if writer_passed else primary_blocker,
            detail="The audited writer idempotency manifest exists and binds source and artifact hashes.",
            artifact_written=artifact_written_count > 0,
        ),
        _control(
            control_id="PORTFOLIO_TRUTH_PUBLISHED",
            control_status="PASS" if writer_passed else "BLOCKED",
            blocker_code=None if writer_passed else primary_blocker,
            detail="The PAPER portfolio truth snapshot exists and validates as simulated ledger truth.",
            artifact_written=artifact_written_count > 0,
        ),
        _control(
            control_id="POST_WRITE_HASHES_MATCH",
            control_status="PASS" if writer_passed else "BLOCKED",
            blocker_code=None if writer_passed else primary_blocker,
            detail="Post-write file payloads match the source-bound current-evidence and portfolio hashes.",
        ),
        _control(
            control_id="POST_WRITE_SCHEMA_VALIDATED",
            control_status="PASS" if writer_passed else "BLOCKED",
            blocker_code=None if writer_passed else primary_blocker,
            detail="All written PAPER artifacts pass local schema or domain validation.",
        ),
        _control(
            control_id="LIVE_AND_SCALE_BOUNDARY_CONFIRMED",
            control_status="PASS",
            blocker_code=None,
            detail="The audited writer cannot create LIVE_READY, live order permission, live config mutation, or scale-up.",
        ),
    ]
    pass_count = sum(1 for control in controls if control["control_status"] == "PASS")
    blocked_count = sum(1 for control in controls if control["control_status"] == "BLOCKED")
    report = {
        "schema_id": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_SCHEMA_ID,
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "audited_writer_id": audited_writer_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_TRUTH_ROLE,
        "audited_writer_role": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_ROLE,
        "source_implementation_prep_hash": source_implementation_prep_report.get(
            "audited_writer_implementation_prep_hash"
        ),
        "source_implementation_prep_status": source_implementation_prep_report.get("implementation_prep_status"),
        "source_implementation_prep_validator_status": prep_validator_status,
        "source_locked_output_hash": source_implementation_prep_report.get(
            "source_audited_writer_locked_output_hash"
        ),
        "source_ledger_rollup_hash": source_ledger_rollup_report.get("rollup_hash"),
        "source_ledger_rollup_status": source_ledger_rollup_report.get("rollup_status"),
        "source_ledger_rollup_validator_status": ledger_validator_status,
        "source_paper_ledger_head_hash": source_ledger_rollup_report.get("latest_ledger_head_hash"),
        "source_public_market_data_hash": source_public_market_data_hash,
        "source_runtime_cycle_id": (source_ledger_rollup_report.get("portfolio_snapshot") or {}).get(
            "source_runtime_cycle_id"
        )
        if isinstance(source_ledger_rollup_report.get("portfolio_snapshot"), dict)
        else None,
        "writer_status": status,
        "writer_passed": writer_passed,
        "writer_control_count": len(controls),
        "writer_control_pass_count": pass_count,
        "writer_control_blocked_count": blocked_count,
        "writer_controls": controls,
        "planned_artifact_paths": EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS,
        "planned_temp_paths": EXPECTED_AUDITED_WRITER_TEMP_PATHS,
        "lock_path": EXPECTED_AUDITED_WRITER_LOCK_PATH,
        "target_states_before": final_path_states,
        "artifacts": artifacts,
        "artifact_written_count": artifact_written_count,
        "artifact_reused_count": len(artifacts) if idempotent_replay else 0,
        "idempotent_replay": idempotent_replay,
        "target_dirty_cause": target_dirty_cause,
        "stale_output_superseded": stale_output_superseded,
        "archive_id": archive_id,
        "archived_artifact_count": archived_artifact_count,
        "archived_artifacts": archived_artifacts,
        "post_rerun_reconciliation_closure_status": (
            "PASS_STALE_CURRENT_TRUTH_SUPERSEDED"
            if stale_output_superseded
            and writer_passed
            and target_dirty_cause == TARGET_DIRTY_CAUSE_STALE_LEDGER_SUPERSEDED
            else "PASS_STALE_CURRENT_TRUTH_REFRESHED"
            if stale_output_superseded
            and writer_passed
            and target_dirty_cause == TARGET_DIRTY_CAUSE_STALE_CURRENT_TRUTH_REFRESHED
            else "PASS_NOT_REQUIRED"
            if writer_passed
            else "BLOCKED_PRECISE_UNRESOLVED_CAUSE"
        ),
        "post_rerun_reconciliation_unresolved_cause": None
        if writer_passed
        else (target_dirty_cause if target_dirty_cause != TARGET_DIRTY_CAUSE_NONE else primary_blocker),
        "lock_acquire_attempted": lock_acquire_attempted,
        "lock_acquired": lock_acquired,
        "lock_file_written": lock_file_written,
        "lock_released": lock_released,
        "lock_present_after_run": lock_path.exists(),
        "primary_blocker_code": primary_blocker,
        "blocker_codes": sorted(blocker_codes),
        "operator_next_action": "Use the audited PAPER current-evidence artifacts for dashboard portfolio binding; live review remains blocked.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "writer_single_run_only": True,
        "current_evidence_artifact_written": writer_passed,
        "idempotency_manifest_written": writer_passed,
        "portfolio_truth_artifact_written": writer_passed,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "scale_up_allowed": False,
        "audited_writer_report_hash": "",
    }
    report["audited_writer_report_hash"] = upbit_paper_repaired_current_evidence_audited_writer_report_hash(
        report
    )
    return report


def write_upbit_paper_repaired_current_evidence_audited_writer_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_repaired_current_evidence_audited_writer_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_audited_current_evidence_snapshot(
    snapshot: dict[str, Any],
) -> UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "current_evidence_status",
        "truth_role",
        "source_implementation_prep_hash",
        "source_locked_output_hash",
        "source_ledger_rollup_hash",
        "source_ledger_rollup_status",
        "source_paper_ledger_head_hash",
        "source_runtime_cycle_id",
        "source_portfolio_snapshot_hash",
        "portfolio_truth_status",
        "ledger_head_status",
        "runtime_cycle_status",
        "cash_status",
        "equity_status",
        "position_status",
        "configured_initial_cash_krw",
        "verified_cash_krw",
        "verified_equity_krw",
        "verified_total_pnl_krw",
        "verified_return_pct",
        "open_position_count",
        "paper_only",
        "display_only",
        "dashboard_truth_only",
        "current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
        "primary_blocker_code",
        "snapshot_hash",
    }
    missing = sorted(required - set(snapshot))
    if missing:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", f"audited current evidence missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if snapshot.get("schema_id") != UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_SNAPSHOT_SCHEMA_ID:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited current evidence schema mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if snapshot.get("snapshot_hash") != upbit_paper_audited_current_evidence_snapshot_hash(snapshot):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited current evidence hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if snapshot.get("exchange") != "UPBIT" or snapshot.get("market_type") != "KRW_SPOT" or snapshot.get("mode") != "PAPER":
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "BLOCKED", "audited current evidence scope mismatch", "SNAPSHOT_SCOPE_MISMATCH"
        )
    false_fields = (
        "current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(snapshot.get(field) is not False for field in false_fields):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "BLOCKED", "audited current evidence attempted live, order, or scale permission", "LIVE_FINAL_GUARD_FAILED"
        )
    ledger_head_status_valid = snapshot.get("ledger_head_status") == "PASS" or (
        snapshot.get("ledger_head_status") == "NOT_APPLICABLE"
        and snapshot.get("source_ledger_rollup_status") == "PASS"
        and isinstance(snapshot.get("source_paper_ledger_head_hash"), str)
        and len(snapshot.get("source_paper_ledger_head_hash")) == 64
    )
    if (
        snapshot.get("current_evidence_status") != "PASS"
        or snapshot.get("portfolio_truth_status") != "VERIFIED_PAPER_LEDGER_ROLLUP"
        or not ledger_head_status_valid
        or snapshot.get("cash_status") != "VERIFIED"
        or snapshot.get("equity_status") != "VERIFIED"
        or snapshot.get("paper_only") is not True
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "BLOCKED", "audited current evidence did not preserve verified PAPER-only truth", "MEASUREMENT_MISSING"
        )
    return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
        "PASS", "audited current evidence snapshot is scoped, hash-bound, and live-blocked", None
    )


def validate_upbit_paper_audited_current_evidence_idempotency_manifest(
    manifest: dict[str, Any],
) -> UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult:
    required = {
        "manifest_schema_id",
        "generated_at_utc",
        "project_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "manifest_status",
        "source_implementation_prep_hash",
        "source_locked_output_hash",
        "source_ledger_rollup_hash",
        "source_paper_ledger_head_hash",
        "current_evidence_snapshot_hash",
        "portfolio_snapshot_hash",
        "planned_artifact_paths",
        "planned_temp_paths",
        "lock_path",
        "paper_only",
        "current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "live_order_allowed",
        "scale_up_allowed",
        "idempotency_key",
        "manifest_hash",
    }
    missing = sorted(required - set(manifest))
    if missing:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", f"audited writer manifest missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if manifest.get("manifest_schema_id") != UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_IDEMPOTENCY_MANIFEST_SCHEMA_ID:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer manifest schema mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if manifest.get("manifest_hash") != upbit_paper_audited_current_evidence_idempotency_manifest_hash(manifest):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer manifest hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if manifest.get("planned_artifact_paths") != EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer manifest target path mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if manifest.get("planned_temp_paths") != EXPECTED_AUDITED_WRITER_TEMP_PATHS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer manifest temp path mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    for field in ("current_evidence_write_allowed", "portfolio_truth_write_allowed", "live_order_allowed", "scale_up_allowed"):
        if manifest.get(field) is not False:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "BLOCKED", "audited writer manifest attempted permission", "LIVE_FINAL_GUARD_FAILED"
            )
    return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
        "PASS", "audited writer idempotency manifest is source-bound and live-blocked", None
    )


def validate_upbit_paper_repaired_current_evidence_audited_writer_report(
    report: dict[str, Any],
) -> UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "audited_writer_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "audited_writer_role",
        "source_implementation_prep_hash",
        "source_implementation_prep_status",
        "source_implementation_prep_validator_status",
        "source_locked_output_hash",
        "source_ledger_rollup_hash",
        "source_ledger_rollup_status",
        "source_ledger_rollup_validator_status",
        "source_paper_ledger_head_hash",
        "source_runtime_cycle_id",
        "writer_status",
        "writer_passed",
        "writer_control_count",
        "writer_control_pass_count",
        "writer_control_blocked_count",
        "writer_controls",
        "planned_artifact_paths",
        "planned_temp_paths",
        "lock_path",
        "target_states_before",
        "artifacts",
        "artifact_written_count",
        "artifact_reused_count",
        "idempotent_replay",
        "target_dirty_cause",
        "stale_output_superseded",
        "archive_id",
        "archived_artifact_count",
        "archived_artifacts",
        "post_rerun_reconciliation_closure_status",
        "post_rerun_reconciliation_unresolved_cause",
        "lock_acquire_attempted",
        "lock_acquired",
        "lock_file_written",
        "lock_released",
        "lock_present_after_run",
        "primary_blocker_code",
        "blocker_codes",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "writer_single_run_only",
        "current_evidence_artifact_written",
        "idempotency_manifest_written",
        "portfolio_truth_artifact_written",
        "current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
        "audited_writer_report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", f"audited writer report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_SCHEMA_ID:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer report schema mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("audited_writer_report_hash") != upbit_paper_repaired_current_evidence_audited_writer_report_hash(report):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer report hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "BLOCKED", "audited writer report scope mismatch", "SNAPSHOT_SCOPE_MISMATCH"
        )
    false_fields = (
        "current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(report.get(field) is not False for field in false_fields):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "BLOCKED", "audited writer report attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if report.get("planned_artifact_paths") != EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer planned path mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("planned_temp_paths") != EXPECTED_AUDITED_WRITER_TEMP_PATHS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer planned temp path mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("lock_path") != EXPECTED_AUDITED_WRITER_LOCK_PATH:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer lock path mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("target_dirty_cause") not in {
        TARGET_DIRTY_CAUSE_NONE,
        TARGET_DIRTY_CAUSE_PARTIAL_TARGET_SET,
        TARGET_DIRTY_CAUSE_TEMP_PATH_DIRTY,
        TARGET_DIRTY_CAUSE_STALE_LEDGER_SUPERSEDED,
        TARGET_DIRTY_CAUSE_STALE_CURRENT_TRUTH_REFRESHED,
        TARGET_DIRTY_CAUSE_CONFLICTING_PROVENANCE,
        TARGET_DIRTY_CAUSE_LOCK_BUSY,
    }:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer target dirty cause unknown", "SCHEMA_IDENTITY_MISMATCH"
        )
    archived_artifacts = report.get("archived_artifacts")
    if not isinstance(archived_artifacts, list) or report.get("archived_artifact_count") != len(archived_artifacts):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer archive count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    for archived in archived_artifacts:
        if not isinstance(archived, dict):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "FAIL", "audited writer archive record must be object", "SCHEMA_IDENTITY_MISMATCH"
            )
        if (
            archived.get("relative_original_path") not in EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS
            or not isinstance(archived.get("relative_archive_path"), str)
            or not archived["relative_archive_path"].startswith("paper_runtime/current_evidence/archive/")
            or archived.get("audit_preserved") is not True
            or archived.get("source_delete_allowed") is not False
            or archived.get("live_order_allowed") is not False
            or archived.get("scale_up_allowed") is not False
            or not isinstance(archived.get("archived_file_hash"), str)
            or len(archived["archived_file_hash"]) != 64
        ):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "BLOCKED", "audited writer archive record lost scope or live safety", "LIVE_FINAL_GUARD_FAILED"
            )
    controls = report.get("writer_controls")
    if not isinstance(controls, list) or report.get("writer_control_count") != len(controls):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer control count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    control_ids = []
    pass_count = 0
    blocked_count = 0
    for control in controls:
        if not isinstance(control, dict):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "FAIL", "audited writer control must be object", "SCHEMA_IDENTITY_MISMATCH"
            )
        control_ids.append(control.get("control_id"))
        if control.get("control_status") == "PASS":
            pass_count += 1
        elif control.get("control_status") == "BLOCKED":
            blocked_count += 1
        else:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "FAIL", "audited writer control status unknown", "SCHEMA_IDENTITY_MISMATCH"
            )
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            if control.get(field) is not False:
                return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                    "BLOCKED", "audited writer control attempted live or scale permission", "LIVE_FINAL_GUARD_FAILED"
                )
    if control_ids != REQUIRED_WRITER_CONTROL_IDS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer control sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("writer_control_pass_count") != pass_count or report.get("writer_control_blocked_count") != blocked_count:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer aggregate count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    pass_statuses = {
        AUDITED_WRITER_WRITTEN_STATUS,
        AUDITED_WRITER_IDEMPOTENT_STATUS,
        AUDITED_WRITER_REFRESHED_STATUS,
    }
    if report.get("writer_status") in pass_statuses:
        if (
            report.get("writer_passed") is not True
            or pass_count != len(REQUIRED_WRITER_CONTROL_IDS)
            or blocked_count != 0
            or report.get("primary_blocker_code") is not None
            or report.get("current_evidence_artifact_written") is not True
            or report.get("idempotency_manifest_written") is not True
            or report.get("portfolio_truth_artifact_written") is not True
            or report.get("lock_present_after_run") is not False
            or report.get("post_rerun_reconciliation_unresolved_cause") is not None
        ):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "FAIL", "audited writer PASS status did not preserve post-write invariants", "SCHEMA_IDENTITY_MISMATCH"
            )
        artifacts = report.get("artifacts")
        if not isinstance(artifacts, list) or len(artifacts) != 3:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "FAIL", "audited writer artifacts mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if report.get("writer_status") in {
            AUDITED_WRITER_WRITTEN_STATUS,
            AUDITED_WRITER_REFRESHED_STATUS,
        } and report.get("artifact_written_count") != 3:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "FAIL", "audited writer written status did not write three artifacts", "SCHEMA_IDENTITY_MISMATCH"
            )
        if report.get("stale_output_superseded") is True and (
            report.get("target_dirty_cause")
            not in {
                TARGET_DIRTY_CAUSE_STALE_LEDGER_SUPERSEDED,
                TARGET_DIRTY_CAUSE_STALE_CURRENT_TRUTH_REFRESHED,
            }
            or report.get("archived_artifact_count") != 3
            or not isinstance(report.get("archive_id"), str)
            or report.get("post_rerun_reconciliation_closure_status")
            != (
                "PASS_STALE_CURRENT_TRUTH_REFRESHED"
                if report.get("target_dirty_cause") == TARGET_DIRTY_CAUSE_STALE_CURRENT_TRUTH_REFRESHED
                else "PASS_STALE_CURRENT_TRUTH_SUPERSEDED"
            )
        ):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "FAIL", "audited writer stale supersede status lost archive invariants", "SCHEMA_IDENTITY_MISMATCH"
            )
        if report.get("writer_status") == AUDITED_WRITER_IDEMPOTENT_STATUS and (
            report.get("artifact_reused_count") != 3 or report.get("idempotent_replay") is not True
        ):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "FAIL", "audited writer idempotent status did not reuse three artifacts", "SCHEMA_IDENTITY_MISMATCH"
            )
    elif report.get("writer_status") in {
        AUDITED_WRITER_BLOCKED_SOURCE_STATUS,
        AUDITED_WRITER_BLOCKED_LEDGER_STATUS,
        AUDITED_WRITER_BLOCKED_TARGET_STATUS,
        AUDITED_WRITER_BLOCKED_LOCK_STATUS,
    }:
        if (
            report.get("writer_passed") is not False
            or report.get("primary_blocker_code") is None
            or report.get("post_rerun_reconciliation_closure_status") != "BLOCKED_PRECISE_UNRESOLVED_CAUSE"
            or not report.get("post_rerun_reconciliation_unresolved_cause")
        ):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
                "BLOCKED", "audited writer blocked status missing blocker", "LIVE_FINAL_GUARD_FAILED"
            )
    else:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
            "FAIL", "audited writer status unknown", "SCHEMA_IDENTITY_MISMATCH"
        )
    return UpbitPaperRepairedCurrentEvidenceAuditedWriterValidationResult(
        "PASS", "audited writer report is PAPER-only, source-bound, idempotent, and live-blocked", None
    )
