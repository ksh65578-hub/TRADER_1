from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_persistent_loop import (
    LONG_RUN_EVIDENCE_BLOCKER_CODE,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_paper_runtime import validate_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY_SCHEMA_ID = "trader1.upbit_paper_runtime_sample_history.v1"
UPBIT_PAPER_RUNTIME_SAMPLE_SCHEMA_ID = "trader1.upbit_paper_runtime_sample.v1"
RUNTIME_SAMPLE_HISTORY_ROLE = "PAPER_RUNTIME_SAMPLE_HISTORY_NOT_LONG_RUN_EVIDENCE"
RUNTIME_SAMPLE_TRUTH_ROLE = "paper_runtime_analysis_truth"
DEFAULT_MIN_ACTUAL_LONG_RUN_SPAN_SECONDS = 86400
DEFAULT_MIN_ACTUAL_LONG_RUN_CYCLE_COUNT = 2880


@dataclass(frozen=True)
class UpbitPaperRuntimeSampleHistoryValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_runtime_sample_hash(sample: dict[str, Any]) -> str:
    payload = dict(sample)
    payload.pop("sample_hash", None)
    return _sha256_json(payload)


def upbit_paper_runtime_sample_history_hash(history: dict[str, Any]) -> str:
    payload = dict(history)
    payload.pop("history_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(value, dict):
        return None, "not_object"
    return value, None


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _span_seconds(samples: list[dict[str, Any]]) -> int:
    timestamps = [_parse_utc(sample.get("generated_at_utc")) for sample in samples]
    valid = sorted(timestamp for timestamp in timestamps if timestamp is not None)
    if len(valid) < 2:
        return 0
    return int((valid[-1] - valid[0]).total_seconds())


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    prefix = f"system/runtime/upbit/krw_spot/paper/{session_id}/"
    parts = path.replace("\\", "/").split("/")
    return path.startswith(prefix) and ".." not in parts and "live" not in parts


def _runtime_cycle_path(cycle_result: dict[str, Any], root: Path) -> Path | None:
    for artifact_path in cycle_result.get("artifact_paths") or []:
        if isinstance(artifact_path, str) and artifact_path.endswith(".runtime_cycle.json"):
            return root / artifact_path
    return None


def _build_sample(
    *,
    loop_report_path: Path,
    loop_report: dict[str, Any],
    cycle_result: dict[str, Any],
    runtime_cycle_path: Path,
    runtime_cycle: dict[str, Any],
    root: Path,
    previous_sample_hash: str | None,
) -> dict[str, Any]:
    sample = {
        "schema_id": UPBIT_PAPER_RUNTIME_SAMPLE_SCHEMA_ID,
        "generated_at_utc": runtime_cycle["generated_at_utc"],
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": loop_report["session_id"],
        "loop_id": loop_report["loop_id"],
        "cycle_id": cycle_result["cycle_id"],
        "source_loop_report_path": _relative_posix(loop_report_path, root),
        "source_loop_report_hash": loop_report["loop_hash"],
        "source_runtime_cycle_path": _relative_posix(runtime_cycle_path, root),
        "source_runtime_cycle_hash": runtime_cycle["cycle_hash"],
        "runtime_input_role": runtime_cycle["runtime_input_role"],
        "final_decision": runtime_cycle["final_decision"],
        "paper_ledger_head_hash": runtime_cycle.get("paper_ledger_head_hash"),
        "paper_portfolio_snapshot_hash": runtime_cycle.get("paper_portfolio_snapshot", {}).get("snapshot_hash"),
        "candidate_count": len(runtime_cycle.get("strategy_candidates") or []),
        "entry_reason_count": len(runtime_cycle.get("entry_reasons") or []),
        "no_trade_reason_count": len(runtime_cycle.get("no_trade_reasons") or []),
        "previous_sample_hash": previous_sample_hash,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "sample_hash": "",
    }
    sample["sample_hash"] = upbit_paper_runtime_sample_hash(sample)
    return sample


def build_upbit_paper_runtime_sample_history(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    history_id: str = "upbit-paper-runtime-sample-history",
    min_actual_long_run_span_seconds: int = DEFAULT_MIN_ACTUAL_LONG_RUN_SPAN_SECONDS,
    min_actual_long_run_cycle_count: int = DEFAULT_MIN_ACTUAL_LONG_RUN_CYCLE_COUNT,
    max_samples: int = 3000,
) -> dict[str, Any]:
    root = Path(root).resolve()
    base = _runtime_base(root, session_id)
    loop_report_paths = sorted((base / "paper_runtime").glob("*.persistent_loop_report.json")) if base.exists() else []
    samples: list[dict[str, Any]] = []
    accepted_loop_report_count = 0
    invalid_source_count = 0
    invalid_sources: list[dict[str, str]] = []
    seen_runtime_hashes: set[str] = set()
    duplicate_cycle_hash_count = 0
    source_loop_hashes: list[str] = []
    source_runtime_cycle_hashes: list[str] = []

    for loop_report_path in loop_report_paths:
        loop_report, load_error = _safe_read_json(loop_report_path)
        if load_error or loop_report is None:
            invalid_source_count += 1
            invalid_sources.append({"path": _relative_posix(loop_report_path, root), "reason": load_error or "unknown"})
            continue
        loop_result = validate_upbit_paper_persistent_loop_report(loop_report)
        if loop_result.status != "PASS":
            invalid_source_count += 1
            invalid_sources.append({"path": _relative_posix(loop_report_path, root), "reason": loop_result.blocker_code or loop_result.message})
            continue
        accepted_loop_report_count += 1
        source_loop_hashes.append(loop_report["loop_hash"])
        for cycle_result in loop_report.get("cycle_results") or []:
            runtime_hash = cycle_result.get("runtime_cycle_hash")
            if runtime_hash in seen_runtime_hashes:
                duplicate_cycle_hash_count += 1
                continue
            runtime_path = _runtime_cycle_path(cycle_result, root)
            if runtime_path is None:
                invalid_source_count += 1
                invalid_sources.append({"path": _relative_posix(loop_report_path, root), "reason": "runtime_cycle_path_missing"})
                continue
            runtime_cycle, runtime_error = _safe_read_json(runtime_path)
            if runtime_error or runtime_cycle is None:
                invalid_source_count += 1
                invalid_sources.append({"path": _relative_posix(runtime_path, root), "reason": runtime_error or "unknown"})
                continue
            runtime_result = validate_upbit_paper_runtime_cycle_report(runtime_cycle)
            if runtime_result.status != "PASS":
                invalid_source_count += 1
                invalid_sources.append({"path": _relative_posix(runtime_path, root), "reason": runtime_result.blocker_code or runtime_result.message})
                continue
            if runtime_cycle.get("cycle_hash") != runtime_hash:
                invalid_source_count += 1
                invalid_sources.append({"path": _relative_posix(runtime_path, root), "reason": "runtime_cycle_hash_mismatch"})
                continue
            seen_runtime_hashes.add(str(runtime_hash))
            previous_hash = samples[-1]["sample_hash"] if samples else None
            sample = _build_sample(
                loop_report_path=loop_report_path,
                loop_report=loop_report,
                cycle_result=cycle_result,
                runtime_cycle_path=runtime_path,
                runtime_cycle=runtime_cycle,
                root=root,
                previous_sample_hash=previous_hash,
            )
            samples.append(sample)
            source_runtime_cycle_hashes.append(runtime_cycle["cycle_hash"])
            if len(samples) >= max_samples:
                break
        if len(samples) >= max_samples:
            break

    samples.sort(key=lambda item: (item["generated_at_utc"], item["cycle_id"]))
    previous_hash: str | None = None
    for sample in samples:
        sample["previous_sample_hash"] = previous_hash
        sample["sample_hash"] = upbit_paper_runtime_sample_hash(sample)
        previous_hash = sample["sample_hash"]

    observed_span_seconds = _span_seconds(samples)
    span_floor_met = observed_span_seconds >= min_actual_long_run_span_seconds
    cycle_floor_met = len(samples) >= min_actual_long_run_cycle_count
    if invalid_source_count > 0 or duplicate_cycle_hash_count > 0:
        status = "BLOCKED"
        primary_blocker_code = "RECONCILIATION_REQUIRED"
    elif not samples:
        status = "INSUFFICIENT_HISTORY"
        primary_blocker_code = "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
    else:
        status = "COLLECTING"
        primary_blocker_code = LONG_RUN_EVIDENCE_BLOCKER_CODE

    history = {
        "schema_id": UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "history_id": history_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": RUNTIME_SAMPLE_TRUTH_ROLE,
        "runtime_analysis_only": True,
        "execution_truth": False,
        "dashboard_truth_only": False,
        "history_evidence_role": RUNTIME_SAMPLE_HISTORY_ROLE,
        "runtime_sample_status": status,
        "primary_blocker_code": primary_blocker_code,
        "source_loop_report_count": len(loop_report_paths),
        "accepted_loop_report_count": accepted_loop_report_count,
        "accepted_cycle_sample_count": len(samples),
        "unique_runtime_cycle_hash_count": len({sample["source_runtime_cycle_hash"] for sample in samples}),
        "duplicate_cycle_hash_count": duplicate_cycle_hash_count,
        "invalid_source_count": invalid_source_count,
        "invalid_sources": invalid_sources,
        "first_sample_at_utc": samples[0]["generated_at_utc"] if samples else None,
        "latest_sample_at_utc": samples[-1]["generated_at_utc"] if samples else None,
        "observed_span_seconds": observed_span_seconds,
        "min_actual_long_run_span_seconds": min_actual_long_run_span_seconds,
        "min_actual_long_run_cycle_count": min_actual_long_run_cycle_count,
        "span_floor_met": span_floor_met,
        "cycle_floor_met": cycle_floor_met,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "long_run_blocker_code": LONG_RUN_EVIDENCE_BLOCKER_CODE,
        "long_run_next_action": "Collect validated, non-duplicated PAPER and SHADOW runtime history over the required wall-clock span before live review.",
        "promotion_eligible": False,
        "source_loop_report_hashes": source_loop_hashes,
        "source_runtime_cycle_hashes": source_runtime_cycle_hashes,
        "samples": samples,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "history_hash": "",
    }
    history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)
    return history


def write_upbit_paper_runtime_sample_history(*, root: Path, history: dict[str, Any]) -> Path:
    path = _runtime_base(root, str(history["session_id"])) / "paper_runtime" / "upbit_paper_runtime_sample_history.json"
    durable_atomic_write_json(path, history)
    return path


def validate_upbit_paper_runtime_sample_history(history: dict[str, Any]) -> UpbitPaperRuntimeSampleHistoryValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "history_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "runtime_analysis_only",
        "execution_truth",
        "dashboard_truth_only",
        "history_evidence_role",
        "runtime_sample_status",
        "primary_blocker_code",
        "source_loop_report_count",
        "accepted_loop_report_count",
        "accepted_cycle_sample_count",
        "unique_runtime_cycle_hash_count",
        "duplicate_cycle_hash_count",
        "invalid_source_count",
        "invalid_sources",
        "first_sample_at_utc",
        "latest_sample_at_utc",
        "observed_span_seconds",
        "min_actual_long_run_span_seconds",
        "min_actual_long_run_cycle_count",
        "span_floor_met",
        "cycle_floor_met",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "long_run_next_action",
        "promotion_eligible",
        "source_loop_report_hashes",
        "source_runtime_cycle_hashes",
        "samples",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "history_hash",
    }
    missing = sorted(required - set(history))
    if missing:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", f"runtime sample history missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("schema_id") != UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY_SCHEMA_ID:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample history schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("history_hash") != upbit_paper_runtime_sample_history_hash(history):
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample history hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("exchange") != "UPBIT" or history.get("market_type") != "KRW_SPOT" or history.get("mode") != "PAPER":
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample history scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if history.get("truth_role") != RUNTIME_SAMPLE_TRUTH_ROLE or history.get("history_evidence_role") != RUNTIME_SAMPLE_HISTORY_ROLE:
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample history evidence role cannot claim live, dashboard, or execution truth", LONG_RUN_EVIDENCE_BLOCKER_CODE)
    if history.get("runtime_analysis_only") is not True or history.get("execution_truth") or history.get("dashboard_truth_only"):
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample history must remain analysis-only", "LIVE_FINAL_GUARD_FAILED")
    forbidden_fields = (
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
        "scale_up_allowed",
    )
    if any(history.get(field) for field in forbidden_fields):
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample history attempted live, order, promotion, long-run, or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    if history.get("long_run_blocker_code") != LONG_RUN_EVIDENCE_BLOCKER_CODE or not history.get("long_run_next_action"):
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample history must expose the long-run evidence blocker", LONG_RUN_EVIDENCE_BLOCKER_CODE)

    samples = history.get("samples")
    if not isinstance(samples, list):
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample history samples must be a list", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("accepted_cycle_sample_count") != len(samples):
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "accepted cycle sample count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    runtime_hashes: list[str] = []
    previous_hash: str | None = None
    previous_timestamp: datetime | None = None
    session_id = str(history.get("session_id"))
    for sample in samples:
        if not isinstance(sample, dict):
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample must be an object", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("schema_id") != UPBIT_PAPER_RUNTIME_SAMPLE_SCHEMA_ID:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("sample_hash") != upbit_paper_runtime_sample_hash(sample):
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("previous_sample_hash") != previous_hash:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample hash chain mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("exchange") != "UPBIT" or sample.get("market_type") != "KRW_SPOT" or sample.get("mode") != "PAPER" or sample.get("session_id") != session_id:
            return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
        for path_field in ("source_loop_report_path", "source_runtime_cycle_path"):
            path_value = sample.get(path_field)
            if not isinstance(path_value, str) or not _artifact_path_allowed(path_value, session_id):
                return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample source path escaped UPBIT PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if sample.get("live_order_ready") or sample.get("live_order_allowed") or sample.get("can_live_trade") or sample.get("scale_up_allowed"):
            return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample created live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
        timestamp = _parse_utc(sample.get("generated_at_utc"))
        if timestamp is None:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample timestamp is invalid", "SCHEMA_IDENTITY_MISMATCH")
        if previous_timestamp is not None and timestamp < previous_timestamp:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample timestamps are not monotonic", "SCHEMA_IDENTITY_MISMATCH")
        runtime_hashes.append(str(sample.get("source_runtime_cycle_hash")))
        previous_hash = sample["sample_hash"]
        previous_timestamp = timestamp

    unique_count = len(set(runtime_hashes))
    duplicate_count = len(runtime_hashes) - unique_count
    if history.get("unique_runtime_cycle_hash_count") != unique_count or history.get("duplicate_cycle_hash_count") != duplicate_count:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample duplicate count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if duplicate_count:
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "duplicate runtime cycle samples require reconciliation", "RECONCILIATION_REQUIRED")
    if history.get("source_runtime_cycle_hashes") != runtime_hashes:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime cycle hash list is not bound to samples", "SCHEMA_IDENTITY_MISMATCH")
    observed_span_seconds = _span_seconds(samples)
    if history.get("observed_span_seconds") != observed_span_seconds:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample observed span mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_span_floor_met = observed_span_seconds >= int(history.get("min_actual_long_run_span_seconds", -1))
    expected_cycle_floor_met = len(samples) >= int(history.get("min_actual_long_run_cycle_count", -1))
    if history.get("span_floor_met") is not expected_span_floor_met or history.get("cycle_floor_met") is not expected_cycle_floor_met:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample floor flag mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if samples:
        if history.get("first_sample_at_utc") != samples[0]["generated_at_utc"] or history.get("latest_sample_at_utc") != samples[-1]["generated_at_utc"]:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample first/latest timestamp mismatch", "SCHEMA_IDENTITY_MISMATCH")
    elif history.get("first_sample_at_utc") is not None or history.get("latest_sample_at_utc") is not None:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "empty runtime sample history cannot carry first/latest timestamps", "SCHEMA_IDENTITY_MISMATCH")
    if int(history.get("invalid_source_count", -1)) > 0 and history.get("runtime_sample_status") != "BLOCKED":
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "invalid runtime source must block sample history", "RECONCILIATION_REQUIRED")
    if not samples and history.get("runtime_sample_status") != "INSUFFICIENT_HISTORY":
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "empty runtime sample history must be insufficient", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if samples and history.get("runtime_sample_status") not in {"COLLECTING", "BLOCKED"}:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample history status is inconsistent", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperRuntimeSampleHistoryValidationResult("PASS", "Upbit PAPER runtime sample history is hash-linked, scoped, and live-blocked", None)
