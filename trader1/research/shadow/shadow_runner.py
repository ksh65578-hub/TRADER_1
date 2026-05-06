from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


PAPER_SHADOW_SEPARATION_SCHEMA_ID = "trader1.paper_shadow_separation_report.v1"
PAPER_SHADOW_EVIDENCE_SCHEMA_ID = "trader1.paper_shadow_evidence_accumulation_report.v1"
TRADER1_SHA256 = "FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B"
AGENTS_SHA256 = "21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D"
ACTUAL_RUNTIME_SOURCE_ID_PREFIX = "actual-runtime-source"
ACTUAL_RUNTIME_SOURCE_MODES = {"paper", "shadow"}
DISPLAY_ONLY_RUNTIME_SOURCE_MARKERS = (
    "dashboard",
    "dashboard_shell",
    "summary",
    "heartbeat",
    "startup_probe",
    "launcher",
    "stability_history",
)
ACTUAL_RUNTIME_REQUIREMENT_IDS = (
    "runtime_span",
    "cycle_count",
    "heartbeat_freshness",
    "recovery_clean",
    "partial_write_clean",
)
ACTUAL_RUNTIME_REQUIREMENT_PASS = "PASS"
ACTUAL_RUNTIME_REQUIREMENT_MISSING = "MISSING"
PAPER_SHADOW_ACTIONABILITY_VERSION = "paper_shadow_actionability.v1"


@dataclass(frozen=True)
class PaperShadowSeparationValidationResult:
    status: str
    message: str
    blocker_code: str | None


@dataclass(frozen=True)
class PaperShadowEvidenceValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def paper_shadow_separation_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("separation_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def paper_shadow_evidence_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("evidence_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def _hex_64(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdefABCDEF" for char in value)


def _actual_runtime_source_scope_errors(
    *,
    actual_runtime_source_ids: list[str],
    exchange: str,
    market_type: str,
    paper_session_id: str,
    shadow_session_id: str,
) -> list[str]:
    if not actual_runtime_source_ids:
        return []

    errors: list[str] = []
    modes_seen: set[str] = set()
    expected_exchange = exchange.lower()
    expected_market_type = market_type.lower()
    for source_id in actual_runtime_source_ids:
        source_text = str(source_id)
        lowered = source_text.lower()
        if any(marker in lowered for marker in DISPLAY_ONLY_RUNTIME_SOURCE_MARKERS):
            errors.append(f"actual runtime source id is display-only, not execution evidence: {source_id}")
            continue

        parts = source_text.split(":")
        if len(parts) != 6 or parts[0] != ACTUAL_RUNTIME_SOURCE_ID_PREFIX:
            errors.append(
                "actual runtime source ids must use "
                "actual-runtime-source:<exchange>:<market_type>:<paper|shadow>:<session_id>:<source_hash>"
            )
            continue

        _, source_exchange, source_market_type, source_mode, source_session_id, source_hash = parts
        source_mode_lower = source_mode.lower()
        if source_exchange.lower() != expected_exchange or source_market_type.lower() != expected_market_type:
            errors.append(f"actual runtime source id scope mismatch: {source_id}")
        if source_mode_lower not in ACTUAL_RUNTIME_SOURCE_MODES:
            errors.append(f"actual runtime source id must be non-live PAPER or SHADOW: {source_id}")
            continue
        expected_session = paper_session_id if source_mode_lower == "paper" else shadow_session_id
        if source_session_id != expected_session:
            errors.append(f"actual runtime source id session mismatch: {source_id}")
        if not _hex_64(source_hash):
            errors.append(f"actual runtime source id hash must be 64 hex chars: {source_id}")
        modes_seen.add(source_mode_lower)

    if not errors and not ACTUAL_RUNTIME_SOURCE_MODES.issubset(modes_seen):
        errors.append("actual runtime source ids require both PAPER and SHADOW persistent runtime sources")
    return errors


def paper_shadow_actual_runtime_source_id_errors(report: dict[str, Any]) -> list[str]:
    return _actual_runtime_source_scope_errors(
        actual_runtime_source_ids=list(report.get("actual_runtime_source_evidence_ids") or []),
        exchange=str(report.get("exchange") or ""),
        market_type=str(report.get("market_type") or ""),
        paper_session_id=str(report.get("paper_session_id") or ""),
        shadow_session_id=str(report.get("shadow_session_id") or ""),
    )


def paper_shadow_actual_runtime_requirement_status_errors(report: dict[str, Any]) -> list[str]:
    statuses = report.get("actual_runtime_requirement_statuses")
    if not isinstance(statuses, dict):
        return ["actual_runtime_requirement_statuses must be an object"]
    missing = sorted(set(ACTUAL_RUNTIME_REQUIREMENT_IDS) - set(statuses))
    extra = sorted(set(statuses) - set(ACTUAL_RUNTIME_REQUIREMENT_IDS))
    errors: list[str] = []
    if missing:
        errors.append(f"actual runtime requirement statuses missing keys: {missing}")
    if extra:
        errors.append(f"actual runtime requirement statuses contain unknown keys: {extra}")
    for key in ACTUAL_RUNTIME_REQUIREMENT_IDS:
        if statuses.get(key) != ACTUAL_RUNTIME_REQUIREMENT_PASS:
            errors.append(f"actual runtime requirement not PASS: {key}={statuses.get(key)}")
    return errors


def paper_shadow_paired_supporting_window_count(source_ids: list[str]) -> int:
    return _paired_supporting_window_count(source_ids)


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _scope_slugs(exchange: str, market_type: str) -> tuple[str, str]:
    return exchange.lower(), market_type.lower()


def _scope_supported(exchange: str, market_type: str) -> bool:
    return (exchange, market_type) == ("UPBIT", "KRW_SPOT")


def _default_artifact_paths(
    *,
    exchange: str,
    market_type: str,
    paper_session_id: str,
    shadow_session_id: str,
) -> tuple[str, str]:
    exchange_slug, market_slug = _scope_slugs(exchange, market_type)
    return (
        f"system/runtime/{exchange_slug}/{market_slug}/paper/{paper_session_id}/paper_operation_gate_report.json",
        f"system/runtime/{exchange_slug}/{market_slug}/shadow/{shadow_session_id}/shadow_projection.json",
    )


def paper_shadow_expected_artifact_paths(report: dict[str, Any]) -> tuple[str, str]:
    return _default_artifact_paths(
        exchange=str(report.get("exchange") or ""),
        market_type=str(report.get("market_type") or ""),
        paper_session_id=str(report.get("paper_session_id") or ""),
        shadow_session_id=str(report.get("shadow_session_id") or ""),
    )


def paper_shadow_evidence_actionability_fields(report: dict[str, Any]) -> dict[str, Any]:
    min_samples = _as_int(report.get("min_required_sample_count"), 1)
    paper_samples = _as_int(report.get("paper_sample_count"), 0)
    shadow_samples = _as_int(report.get("shadow_sample_count"), 0)
    min_windows = _as_int(report.get("min_required_evidence_window_count"), 1)
    windows = _as_int(report.get("evidence_window_count"), 0)
    supporting_windows = paper_shadow_paired_supporting_window_count(
        list(report.get("supporting_source_evidence_ids") or [])
    )
    min_span = _as_int(report.get("min_required_evidence_span_hours"), 1)
    span_hours = _as_int(report.get("evidence_span_hours"), 0)
    max_age = _as_int(report.get("max_artifact_age_seconds"), 1)
    paper_age = _as_int(report.get("paper_artifact_age_seconds"), 0)
    shadow_age = _as_int(report.get("shadow_artifact_age_seconds"), 0)
    paper_deficit = max(0, min_samples - paper_samples)
    shadow_deficit = max(0, min_samples - shadow_samples)
    window_deficit = max(0, min_windows - min(windows, supporting_windows))
    span_deficit = max(0, min_span - span_hours)
    stale_count = int(paper_age > max_age) + int(shadow_age > max_age)
    reason_deficit = sum(
        1
        for field in ("entry_reason_count", "no_trade_reason_count", "cost_evidence_count")
        if _as_int(report.get(field), 0) <= 0
    )
    actual_runtime_source_validated = (
        report.get("actual_runtime_source_status") == "VALIDATED_NON_LIVE_RUNTIME"
        and bool(report.get("actual_runtime_source_evidence_ids"))
        and not paper_shadow_actual_runtime_source_id_errors(report)
        and not paper_shadow_actual_runtime_requirement_status_errors(report)
    )
    actual_runtime_source_deficit = 0 if actual_runtime_source_validated else 2
    blocker_codes = {
        str(blocker.get("code"))
        for blocker in report.get("blockers", [])
        if isinstance(blocker, dict) and blocker.get("code")
    }
    scope_or_safety_blocked = bool(
        blocker_codes & {"LIVE_FINAL_GUARD_FAILED", "SNAPSHOT_SCOPE_MISMATCH"}
    ) or bool(report.get("raw_join_attempted"))

    if report.get("long_run_evidence_eligible"):
        scorecard_truth_status = "LONG_RUN_REVIEW_READY_NON_LIVE"
    elif report.get("scorecard_input_eligible"):
        scorecard_truth_status = "PAPER_SCORECARD_INPUT_READY_ONLY"
    else:
        scorecard_truth_status = "BLOCKED_NOT_SCORECARD_INPUT"

    if scope_or_safety_blocked:
        status = "BLOCKED_SCOPE_OR_SAFETY"
        deficit_code = "SCOPE_OR_LIVE_SAFETY_BLOCKED"
        next_action = "STOP_AND_INSPECT_SCOPE_OR_SAFETY"
        message = "Scope, namespace, raw join, or live-safety drift blocks PAPER/SHADOW evidence use."
    elif stale_count:
        status = "BLOCKED_DATA_FRESHNESS"
        deficit_code = "DATA_FRESHNESS_DEFICIT"
        next_action = "REFRESH_STALE_PAPER_SHADOW_ARTIFACTS"
        message = "PAPER/SHADOW evidence artifacts are stale and must be regenerated before scorecard use."
    elif paper_deficit > 0 and (shadow_deficit == 0 or paper_deficit >= shadow_deficit):
        status = "COLLECT_PAPER_SAMPLES"
        deficit_code = "PAPER_SAMPLE_DEFICIT"
        next_action = "RUN_MORE_PAPER_SAMPLE_WINDOWS"
        message = f"Collect {paper_deficit} more PAPER samples for the same candidate/strategy/parameter scope."
    elif shadow_deficit > 0:
        status = "COLLECT_SHADOW_SAMPLES"
        deficit_code = "SHADOW_SAMPLE_DEFICIT"
        next_action = "RUN_MORE_SHADOW_SAMPLE_WINDOWS"
        message = f"Collect {shadow_deficit} more SHADOW observations for the same candidate/strategy/parameter scope."
    elif reason_deficit > 0:
        status = "COLLECT_REASON_AND_COST_EVIDENCE"
        deficit_code = "REASON_OR_COST_EVIDENCE_DEFICIT"
        next_action = "RECORD_ENTRY_NO_TRADE_AND_COST_REASONS"
        message = "Record entry reason, no-trade reason, and cost evidence before scorecard input."
    elif window_deficit > 0:
        status = "SCORECARD_READY_COLLECT_PAIRED_WINDOWS"
        deficit_code = "PAIRED_WINDOW_DEFICIT"
        next_action = "RUN_PAIRED_PAPER_SHADOW_WINDOWS"
        message = f"Scorecard input can be PAPER-only, but {window_deficit} more paired PAPER/SHADOW windows are needed for long-run review."
    elif span_deficit > 0:
        status = "SCORECARD_READY_EXTEND_RUNTIME_SPAN"
        deficit_code = "EVIDENCE_SPAN_DEFICIT"
        next_action = "EXTEND_NON_LIVE_RUNTIME_SPAN"
        message = f"Scorecard input can be PAPER-only, but {span_deficit} more non-live span hours are needed for long-run review."
    elif actual_runtime_source_deficit > 0:
        status = "SCORECARD_READY_BIND_ACTUAL_RUNTIME_SOURCE"
        deficit_code = "ACTUAL_RUNTIME_SOURCE_DEFICIT"
        next_action = "ATTACH_VALIDATED_NON_LIVE_RUNTIME_SOURCE"
        message = "Bind validated non-live PAPER and SHADOW runtime source evidence before long-run review."
    elif report.get("long_run_evidence_eligible"):
        status = "LONG_RUN_REVIEW_READY"
        deficit_code = "NONE"
        next_action = "REVIEW_LONG_RUN_EVIDENCE_NON_LIVE"
        message = "PAPER/SHADOW long-run evidence is review-ready but still non-live and cannot write LIVE_READY."
    else:
        status = "SCORECARD_READY_COLLECT_PAIRED_WINDOWS"
        deficit_code = "PAIRED_WINDOW_DEFICIT"
        next_action = "USE_FOR_PAPER_SCORECARD_ONLY"
        message = "Use as PAPER scorecard input only; long-run review remains blocked."

    return {
        "paper_shadow_actionability_version": PAPER_SHADOW_ACTIONABILITY_VERSION,
        "evidence_actionability_status": status,
        "primary_collection_deficit_code": deficit_code,
        "primary_collection_deficit_message": message,
        "next_collection_action": next_action,
        "scorecard_input_truth_status": scorecard_truth_status,
        "paper_sample_deficit": paper_deficit,
        "shadow_sample_deficit": shadow_deficit,
        "evidence_window_deficit": window_deficit,
        "evidence_span_hours_deficit": span_deficit,
        "supporting_window_deficit": max(0, min_windows - supporting_windows),
        "reason_coverage_deficit_count": reason_deficit,
        "stale_artifact_count": stale_count,
        "actual_runtime_source_deficit": actual_runtime_source_deficit,
    }


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_paper_shadow_separation_report(
    *,
    separation_report_id: str,
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    paper_session_id: str = "mvp3_operational_paper",
    shadow_session_id: str = "mvp3_shadow_observation",
    raw_join_attempted: bool = False,
) -> dict[str, Any]:
    paper_path = f"system/runtime/upbit/krw_spot/paper/{paper_session_id}/paper_operation_gate_report.json"
    shadow_path = f"system/runtime/upbit/krw_spot/shadow/{shadow_session_id}/shadow_projection.json"
    blockers: list[dict[str, str]] = []
    if exchange != "UPBIT" or market_type != "KRW_SPOT":
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "paper/shadow separation is scoped to UPBIT/KRW_SPOT"))
    if paper_session_id == shadow_session_id:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "paper and shadow sessions must be distinct"))
    if raw_join_attempted:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "raw paper/shadow joins are forbidden"))
    report = {
        "schema_id": PAPER_SHADOW_SEPARATION_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "separation_report_id": separation_report_id,
        "exchange": exchange,
        "market_type": market_type,
        "paper_mode": "PAPER",
        "shadow_mode": "SHADOW",
        "paper_session_id": paper_session_id,
        "shadow_session_id": shadow_session_id,
        "paper_artifact_path": paper_path,
        "shadow_artifact_path": shadow_path,
        "raw_join_attempted": raw_join_attempted,
        "paper_shadow_separated": not blockers,
        "paper_live_namespace_separated": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "separation_hash": "",
    }
    report["separation_hash"] = paper_shadow_separation_hash(report)
    return report


def build_paper_shadow_evidence_accumulation_report(
    *,
    evidence_report_id: str,
    candidate_id: str = "candidate-vwap-pullback-001",
    strategy_id: str = "strategy-vwap-pullback",
    strategy_build_id: str = "strategy-build-mvp4",
    parameter_hash: str = "A" * 64,
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    paper_session_id: str = "mvp4_paper_evidence",
    shadow_session_id: str = "mvp4_shadow_evidence",
    paper_artifact_hash: str = "B" * 64,
    shadow_artifact_hash: str = "C" * 64,
    paper_sample_count: int = 64,
    shadow_sample_count: int = 64,
    min_required_sample_count: int = 30,
    evidence_window_count: int = 2,
    min_required_evidence_window_count: int = 20,
    evidence_span_hours: int = 4,
    min_required_evidence_span_hours: int = 120,
    evidence_span_source: str = "EXPLICIT_OPERATOR_SUPPLIED",
    paper_artifact_age_seconds: int = 120,
    shadow_artifact_age_seconds: int = 120,
    max_artifact_age_seconds: int = 900,
    entry_reason_count: int = 12,
    exit_reason_count: int = 6,
    no_trade_reason_count: int = 10,
    cost_evidence_count: int = 8,
    source_evidence_ids: list[str] | None = None,
    actual_runtime_source_evidence_ids: list[str] | None = None,
    actual_runtime_source_status: str = "MISSING",
    actual_runtime_requirement_statuses: dict[str, str] | None = None,
    raw_join_attempted: bool = False,
    long_run_evidence_eligible: bool | None = None,
) -> dict[str, Any]:
    paper_path, shadow_path = _default_artifact_paths(
        exchange=exchange,
        market_type=market_type,
        paper_session_id=paper_session_id,
        shadow_session_id=shadow_session_id,
    )
    default_source_ids = [
        f"paper:{paper_session_id}:{paper_artifact_hash}",
        f"shadow:{shadow_session_id}:{shadow_artifact_hash}",
    ]
    source_ids = list(dict.fromkeys(default_source_ids))
    supporting_source_ids = list(dict.fromkeys(source_evidence_ids or []))
    actual_runtime_source_ids = list(dict.fromkeys(actual_runtime_source_evidence_ids or []))
    runtime_requirement_statuses = {
        key: ACTUAL_RUNTIME_REQUIREMENT_MISSING
        for key in ACTUAL_RUNTIME_REQUIREMENT_IDS
    }
    if actual_runtime_requirement_statuses:
        runtime_requirement_statuses.update(actual_runtime_requirement_statuses)
    supporting_window_count = _paired_supporting_window_count(supporting_source_ids)
    evidence_span_source_status = "PASS" if evidence_span_source != "NOT_PROVIDED" and evidence_span_hours > 0 else "MISSING"
    actual_runtime_source_errors = _actual_runtime_source_scope_errors(
        actual_runtime_source_ids=actual_runtime_source_ids,
        exchange=exchange,
        market_type=market_type,
        paper_session_id=paper_session_id,
        shadow_session_id=shadow_session_id,
    )
    actual_runtime_requirement_errors = paper_shadow_actual_runtime_requirement_status_errors(
        {"actual_runtime_requirement_statuses": runtime_requirement_statuses}
    )
    actual_runtime_source_validated = (
        actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and bool(actual_runtime_source_ids)
        and not actual_runtime_source_errors
        and not actual_runtime_requirement_errors
    )
    source_bindings = [
        {
            "source_evidence_id": f"paper:{paper_session_id}:{paper_artifact_hash}",
            "source_role": "PAPER_OPERATION",
            "exchange": exchange,
            "market_type": market_type,
            "mode": "PAPER",
            "session_id": paper_session_id,
            "artifact_path": paper_path,
            "artifact_hash": paper_artifact_hash,
            "candidate_id": candidate_id,
            "strategy_id": strategy_id,
            "strategy_build_id": strategy_build_id,
            "parameter_hash": parameter_hash,
            "sample_count": paper_sample_count,
            "artifact_age_seconds": paper_artifact_age_seconds,
            "identity_match_status": "PASS",
        },
        {
            "source_evidence_id": f"shadow:{shadow_session_id}:{shadow_artifact_hash}",
            "source_role": "SHADOW_OBSERVATION",
            "exchange": exchange,
            "market_type": market_type,
            "mode": "SHADOW",
            "session_id": shadow_session_id,
            "artifact_path": shadow_path,
            "artifact_hash": shadow_artifact_hash,
            "candidate_id": candidate_id,
            "strategy_id": strategy_id,
            "strategy_build_id": strategy_build_id,
            "parameter_hash": parameter_hash,
            "sample_count": shadow_sample_count,
            "artifact_age_seconds": shadow_artifact_age_seconds,
            "identity_match_status": "PASS",
        },
    ]
    blockers: list[dict[str, str]] = []
    if not _scope_supported(exchange, market_type):
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "paper/shadow evidence scope must stay spot-only for MVP-4"))
    if paper_session_id == shadow_session_id:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "paper and shadow evidence sessions must be distinct"))
    if paper_artifact_hash == shadow_artifact_hash:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "paper and shadow artifact hashes must be distinct"))
    if raw_join_attempted:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "raw paper/shadow evidence joins are forbidden"))
    if paper_sample_count < min_required_sample_count or shadow_sample_count < min_required_sample_count:
        blockers.append(_blocker("SAMPLE_INSUFFICIENT", "paper and shadow samples must both meet the minimum count"))
    long_run_coverage_requirements_met = (
        paper_sample_count >= min_required_sample_count
        and shadow_sample_count >= min_required_sample_count
        and evidence_window_count >= min_required_evidence_window_count
        and evidence_span_hours >= min_required_evidence_span_hours
        and supporting_window_count >= min_required_evidence_window_count
    )
    long_run_requirements_met = long_run_coverage_requirements_met and actual_runtime_source_validated
    if long_run_evidence_eligible is None:
        long_run_evidence_eligible = long_run_requirements_met
    if long_run_evidence_eligible and not long_run_coverage_requirements_met:
        blockers.append(
            _blocker(
                "SAMPLE_INSUFFICIENT",
                "long-run paper/shadow evidence requires minimum sample count, window count, and elapsed span",
            )
        )
    if long_run_coverage_requirements_met and not actual_runtime_source_validated:
        blockers.append(
            _blocker(
                "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
                "long-run paper/shadow evidence requires validated non-live persistent runtime source evidence",
            )
        )
    if actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and not actual_runtime_source_ids:
        blockers.append(
            _blocker(
                "MEASUREMENT_MISSING",
                "validated actual runtime source status requires source evidence ids",
            )
        )
    if actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and actual_runtime_source_errors:
        blockers.append(
            _blocker(
                "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
                actual_runtime_source_errors[0],
            )
        )
    if actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and actual_runtime_requirement_errors:
        blockers.append(
            _blocker(
                "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
                actual_runtime_requirement_errors[0],
            )
        )
    if actual_runtime_source_status != "VALIDATED_NON_LIVE_RUNTIME" and actual_runtime_source_ids:
        blockers.append(
            _blocker(
                "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
                "actual runtime source ids cannot satisfy long-run evidence without validated non-live runtime status",
            )
        )
    if evidence_window_count >= min_required_evidence_window_count and supporting_window_count < min_required_evidence_window_count:
        blockers.append(
            _blocker(
                "MEASUREMENT_MISSING",
                "long-run paper/shadow evidence requires per-window PAPER and SHADOW supporting source ids",
            )
        )
    long_run_blocker_code = None
    if not long_run_evidence_eligible or not long_run_requirements_met:
        long_run_blocker_code = "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING"
    if paper_artifact_age_seconds > max_artifact_age_seconds or shadow_artifact_age_seconds > max_artifact_age_seconds:
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "paper/shadow evidence artifacts are stale"))
    if entry_reason_count <= 0 or no_trade_reason_count <= 0:
        blockers.append(_blocker("MEASUREMENT_MISSING", "entry and no-trade reason evidence are required"))
    if cost_evidence_count <= 0:
        blockers.append(_blocker("EXECUTION_FEEDBACK_MISSING", "cost evidence is required before scorecard input"))
    if not source_ids:
        blockers.append(_blocker("MEASUREMENT_MISSING", "source evidence ids are required"))

    eligible = not blockers
    report = {
        "schema_id": PAPER_SHADOW_EVIDENCE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": TRADER1_SHA256,
            "agents_sha256": AGENTS_SHA256,
        },
        "evidence_report_id": evidence_report_id,
        "candidate_id": candidate_id,
        "strategy_id": strategy_id,
        "strategy_build_id": strategy_build_id,
        "parameter_hash": parameter_hash,
        "exchange": exchange,
        "market_type": market_type,
        "paper_mode": "PAPER",
        "shadow_mode": "SHADOW",
        "paper_session_id": paper_session_id,
        "shadow_session_id": shadow_session_id,
        "paper_artifact_path": paper_path,
        "shadow_artifact_path": shadow_path,
        "paper_artifact_hash": paper_artifact_hash,
        "shadow_artifact_hash": shadow_artifact_hash,
        "paper_sample_count": paper_sample_count,
        "shadow_sample_count": shadow_sample_count,
        "min_required_sample_count": min_required_sample_count,
        "evidence_window_count": evidence_window_count,
        "min_required_evidence_window_count": min_required_evidence_window_count,
        "evidence_span_hours": evidence_span_hours,
        "min_required_evidence_span_hours": min_required_evidence_span_hours,
        "evidence_span_source": evidence_span_source,
        "evidence_span_source_status": evidence_span_source_status,
        "long_run_evidence_eligible": long_run_evidence_eligible,
        "long_run_blocker_code": long_run_blocker_code,
        "paper_artifact_age_seconds": paper_artifact_age_seconds,
        "shadow_artifact_age_seconds": shadow_artifact_age_seconds,
        "max_artifact_age_seconds": max_artifact_age_seconds,
        "entry_reason_count": entry_reason_count,
        "exit_reason_count": exit_reason_count,
        "no_trade_reason_count": no_trade_reason_count,
        "cost_evidence_count": cost_evidence_count,
        "source_evidence_ids": source_ids,
        "actual_runtime_source_evidence_ids": actual_runtime_source_ids,
        "actual_runtime_source_status": actual_runtime_source_status,
        "actual_runtime_requirement_statuses": runtime_requirement_statuses,
        "supporting_source_evidence_ids": supporting_source_ids,
        "supporting_source_window_count": supporting_window_count,
        "source_evidence_bindings": source_bindings,
        "raw_join_attempted": raw_join_attempted,
        "session_hashes_distinct": paper_session_id != shadow_session_id and paper_artifact_hash != shadow_artifact_hash,
        "evidence_chain_complete": eligible,
        "scorecard_input_eligible": eligible,
        "optimizer_ranking_action": "ALLOW_RANKING" if eligible else "BLOCK_RANKING",
        "dashboard_display_truth_only": True,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "evidence_hash": "",
    }
    report.update(paper_shadow_evidence_actionability_fields(report))
    report["evidence_hash"] = paper_shadow_evidence_hash(report)
    return report


def validate_paper_shadow_separation_report(report: dict[str, Any]) -> PaperShadowSeparationValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "separation_report_id",
        "exchange",
        "market_type",
        "paper_mode",
        "shadow_mode",
        "paper_session_id",
        "shadow_session_id",
        "paper_artifact_path",
        "shadow_artifact_path",
        "raw_join_attempted",
        "paper_shadow_separated",
        "paper_live_namespace_separated",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "separation_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return PaperShadowSeparationValidationResult("FAIL", f"paper/shadow report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != PAPER_SHADOW_SEPARATION_SCHEMA_ID:
        return PaperShadowSeparationValidationResult("FAIL", "paper/shadow schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("separation_hash") != paper_shadow_separation_hash(report):
        return PaperShadowSeparationValidationResult("FAIL", "paper/shadow hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return PaperShadowSeparationValidationResult("BLOCKED", "paper/shadow scope must remain UPBIT/KRW_SPOT", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("paper_mode") != "PAPER" or report.get("shadow_mode") != "SHADOW":
        return PaperShadowSeparationValidationResult("BLOCKED", "paper and shadow modes must stay separated", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("paper_session_id") == report.get("shadow_session_id"):
        return PaperShadowSeparationValidationResult("BLOCKED", "paper and shadow sessions must be distinct", "SNAPSHOT_SCOPE_MISMATCH")
    if "/paper/" not in report.get("paper_artifact_path", "") or "/shadow/" not in report.get("shadow_artifact_path", ""):
        return PaperShadowSeparationValidationResult("BLOCKED", "paper/shadow artifact paths lack namespace separation", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("raw_join_attempted") or report.get("paper_shadow_separated") is not True or report.get("paper_live_namespace_separated") is not True:
        return PaperShadowSeparationValidationResult("BLOCKED", "paper/shadow raw mixing is forbidden", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("order_adapter_called"):
        return PaperShadowSeparationValidationResult("BLOCKED", "paper/shadow separation attempted live/order behavior", "LIVE_FINAL_GUARD_FAILED")
    return PaperShadowSeparationValidationResult("PASS", "paper/shadow namespaces are separated", None)


def validate_paper_shadow_evidence_accumulation_report(report: dict[str, Any]) -> PaperShadowEvidenceValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "authority",
        "evidence_report_id",
        "candidate_id",
        "strategy_id",
        "strategy_build_id",
        "parameter_hash",
        "exchange",
        "market_type",
        "paper_mode",
        "shadow_mode",
        "paper_session_id",
        "shadow_session_id",
        "paper_artifact_path",
        "shadow_artifact_path",
        "paper_artifact_hash",
        "shadow_artifact_hash",
        "paper_sample_count",
        "shadow_sample_count",
        "min_required_sample_count",
        "evidence_window_count",
        "min_required_evidence_window_count",
        "evidence_span_hours",
        "min_required_evidence_span_hours",
        "evidence_span_source",
        "evidence_span_source_status",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "paper_artifact_age_seconds",
        "shadow_artifact_age_seconds",
        "max_artifact_age_seconds",
        "entry_reason_count",
        "exit_reason_count",
        "no_trade_reason_count",
        "cost_evidence_count",
        "source_evidence_ids",
        "actual_runtime_source_evidence_ids",
        "actual_runtime_source_status",
        "actual_runtime_requirement_statuses",
        "supporting_source_evidence_ids",
        "supporting_source_window_count",
        "source_evidence_bindings",
        "raw_join_attempted",
        "session_hashes_distinct",
        "evidence_chain_complete",
        "scorecard_input_eligible",
        "optimizer_ranking_action",
        "dashboard_display_truth_only",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "paper_shadow_actionability_version",
        "evidence_actionability_status",
        "primary_collection_deficit_code",
        "primary_collection_deficit_message",
        "next_collection_action",
        "scorecard_input_truth_status",
        "paper_sample_deficit",
        "shadow_sample_deficit",
        "evidence_window_deficit",
        "evidence_span_hours_deficit",
        "supporting_window_deficit",
        "reason_coverage_deficit_count",
        "stale_artifact_count",
        "actual_runtime_source_deficit",
        "evidence_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return PaperShadowEvidenceValidationResult("FAIL", f"paper/shadow evidence report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != PAPER_SHADOW_EVIDENCE_SCHEMA_ID:
        return PaperShadowEvidenceValidationResult("FAIL", "paper/shadow evidence schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("evidence_hash") != paper_shadow_evidence_hash(report):
        return PaperShadowEvidenceValidationResult("FAIL", "paper/shadow evidence hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_actionability = paper_shadow_evidence_actionability_fields(report)
    for field, expected_value in expected_actionability.items():
        if report.get(field) != expected_value:
            return PaperShadowEvidenceValidationResult(
                "BLOCKED",
                f"paper/shadow evidence actionability field drifted: {field}",
                "MEASUREMENT_MISSING",
            )
    if not _scope_supported(str(report.get("exchange")), str(report.get("market_type"))):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence scope must stay spot-only for MVP-4", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("paper_mode") != "PAPER" or report.get("shadow_mode") != "SHADOW":
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper and shadow modes must stay separated", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("paper_session_id") == report.get("shadow_session_id"):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper and shadow evidence sessions must be distinct", "SNAPSHOT_SCOPE_MISMATCH")
    if "/paper/" not in report.get("paper_artifact_path", "") or "/shadow/" not in report.get("shadow_artifact_path", ""):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence paths lack namespace separation", "SNAPSHOT_SCOPE_MISMATCH")
    expected_paper_path, expected_shadow_path = paper_shadow_expected_artifact_paths(report)
    if report.get("paper_artifact_path") != expected_paper_path or report.get("shadow_artifact_path") != expected_shadow_path:
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            "paper/shadow evidence artifact path scope mismatch",
            "SNAPSHOT_SCOPE_MISMATCH",
        )
    if report.get("paper_artifact_hash") == report.get("shadow_artifact_hash") or report.get("session_hashes_distinct") is not True:
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence hashes must be distinct", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("raw_join_attempted"):
        return PaperShadowEvidenceValidationResult("BLOCKED", "raw paper/shadow evidence joins are forbidden", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("scale_up_allowed") or report.get("order_adapter_called"):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence attempted live/order behavior", "LIVE_FINAL_GUARD_FAILED")

    blockers = report.get("blockers", [])
    if int(report.get("paper_sample_count", 0)) < int(report.get("min_required_sample_count", 1)) or int(report.get("shadow_sample_count", 0)) < int(report.get("min_required_sample_count", 1)):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence sample count is insufficient", "SAMPLE_INSUFFICIENT")
    long_run_coverage_requirements_met = (
        int(report.get("paper_sample_count", 0)) >= int(report.get("min_required_sample_count", 1))
        and int(report.get("shadow_sample_count", 0)) >= int(report.get("min_required_sample_count", 1))
        and int(report.get("evidence_window_count", 0)) >= int(report.get("min_required_evidence_window_count", 1))
        and int(report.get("evidence_span_hours", 0)) >= int(report.get("min_required_evidence_span_hours", 1))
    )
    supporting_source_ids = report.get("supporting_source_evidence_ids") or []
    supporting_window_count = _paired_supporting_window_count(supporting_source_ids)
    reported_supporting_window_count = int(report.get("supporting_source_window_count", -1))
    if reported_supporting_window_count != supporting_window_count:
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            "paper/shadow supporting source window count must match paired source ids",
            "MEASUREMENT_MISSING",
        )
    if report.get("evidence_span_source") == "NOT_PROVIDED" and int(report.get("evidence_span_hours", 0)) != 0:
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            "paper/shadow evidence span cannot be nonzero when span source is not provided",
            "MEASUREMENT_MISSING",
        )
    if report.get("evidence_span_source") != "NOT_PROVIDED" and int(report.get("evidence_span_hours", 0)) > 0:
        if report.get("evidence_span_source_status") != "PASS":
            return PaperShadowEvidenceValidationResult(
                "BLOCKED",
                "paper/shadow evidence span source status must PASS when span hours are supplied",
                "MEASUREMENT_MISSING",
            )
    if report.get("long_run_evidence_eligible") and report.get("evidence_span_source_status") != "PASS":
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            "long-run paper/shadow evidence requires PASS evidence span source status",
            "MEASUREMENT_MISSING",
        )
    actual_runtime_source_ids = report.get("actual_runtime_source_evidence_ids") or []
    actual_runtime_source_status = report.get("actual_runtime_source_status") or "MISSING"
    actual_runtime_source_errors = paper_shadow_actual_runtime_source_id_errors(report)
    actual_runtime_requirement_errors = paper_shadow_actual_runtime_requirement_status_errors(report)
    actual_runtime_source_validated = (
        actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and bool(actual_runtime_source_ids)
        and not actual_runtime_source_errors
        and not actual_runtime_requirement_errors
    )
    long_run_requirements_met = (
        long_run_coverage_requirements_met
        and supporting_window_count >= int(report.get("min_required_evidence_window_count", 1))
        and actual_runtime_source_validated
    )
    if report.get("long_run_evidence_eligible") and not long_run_coverage_requirements_met:
        return PaperShadowEvidenceValidationResult("BLOCKED", "long-run paper/shadow evidence was claimed before minimum window and span coverage", "SAMPLE_INSUFFICIENT")
    if report.get("long_run_evidence_eligible") and supporting_window_count < int(report.get("min_required_evidence_window_count", 1)):
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            "long-run paper/shadow evidence lacks per-window PAPER and SHADOW supporting source ids",
            "MEASUREMENT_MISSING",
        )
    if report.get("long_run_evidence_eligible") and int(report.get("evidence_window_count", 0)) > supporting_window_count:
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            "long-run paper/shadow evidence window count exceeds supporting source coverage",
            "MEASUREMENT_MISSING",
        )
    if report.get("long_run_evidence_eligible") and not actual_runtime_source_validated:
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            "long-run paper/shadow evidence lacks validated non-live persistent runtime source evidence",
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        )
    if actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and not actual_runtime_source_ids:
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            "validated actual runtime source status lacks source evidence ids",
            "MEASUREMENT_MISSING",
        )
    if actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and actual_runtime_source_errors:
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            actual_runtime_source_errors[0],
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        )
    if actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and actual_runtime_requirement_errors:
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            actual_runtime_requirement_errors[0],
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        )
    if actual_runtime_source_status != "VALIDATED_NON_LIVE_RUNTIME" and actual_runtime_source_ids:
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            "actual runtime source ids require validated non-live runtime status",
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        )
    if not report.get("long_run_evidence_eligible") and long_run_requirements_met:
        return PaperShadowEvidenceValidationResult(
            "BLOCKED",
            "long-run eligibility flag must match validated window, span, and actual runtime source evidence",
            "MEASUREMENT_MISSING",
        )
    if report.get("long_run_evidence_eligible") and report.get("long_run_blocker_code") is not None:
        return PaperShadowEvidenceValidationResult("BLOCKED", "long-run eligible paper/shadow evidence cannot carry a long-run blocker", "SAMPLE_INSUFFICIENT")
    if not report.get("long_run_evidence_eligible") and not report.get("long_run_blocker_code"):
        return PaperShadowEvidenceValidationResult("BLOCKED", "short-window paper/shadow evidence must expose the long-run evidence blocker", "MEASUREMENT_MISSING")
    if int(report.get("paper_artifact_age_seconds", 0)) > int(report.get("max_artifact_age_seconds", 1)) or int(report.get("shadow_artifact_age_seconds", 0)) > int(report.get("max_artifact_age_seconds", 1)):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence artifacts are stale", "DATA_QUALITY_INSUFFICIENT")
    if int(report.get("entry_reason_count", 0)) <= 0 or int(report.get("no_trade_reason_count", 0)) <= 0:
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence lacks entry or no-trade reasons", "MEASUREMENT_MISSING")
    if int(report.get("cost_evidence_count", 0)) <= 0:
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence lacks cost feedback", "EXECUTION_FEEDBACK_MISSING")
    if not report.get("source_evidence_ids"):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence lacks source evidence ids", "MEASUREMENT_MISSING")
    source_ids = report.get("source_evidence_ids") or []
    if len(source_ids) != len(set(source_ids)):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence source ids must be unique", "MEASUREMENT_MISSING")
    if len(supporting_source_ids) != len(set(supporting_source_ids)):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow supporting source ids must be unique", "MEASUREMENT_MISSING")
    if set(source_ids) & set(supporting_source_ids):
        return PaperShadowEvidenceValidationResult("BLOCKED", "bound source ids must not be duplicated as supporting source ids", "MEASUREMENT_MISSING")
    bindings = report.get("source_evidence_bindings") or []
    binding_by_id = {
        binding.get("source_evidence_id"): binding
        for binding in bindings
        if isinstance(binding, dict) and binding.get("source_evidence_id")
    }
    if set(binding_by_id) != set(source_ids):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow bound source ids must exactly match source evidence bindings", "MEASUREMENT_MISSING")
    roles = {binding.get("source_role") for binding in binding_by_id.values()}
    if not {"PAPER_OPERATION", "SHADOW_OBSERVATION"}.issubset(roles):
        return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow source evidence bindings must include paper and shadow roles", "MEASUREMENT_MISSING")
    for binding in binding_by_id.values():
        if binding.get("identity_match_status") != "PASS":
            return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow source evidence binding is not fresh and matched", "DATA_QUALITY_INSUFFICIENT")
        if (
            binding.get("exchange") != report.get("exchange")
            or binding.get("market_type") != report.get("market_type")
            or binding.get("candidate_id") != report.get("candidate_id")
            or binding.get("strategy_id") != report.get("strategy_id")
            or binding.get("strategy_build_id") != report.get("strategy_build_id")
            or binding.get("parameter_hash") != report.get("parameter_hash")
        ):
            return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow source evidence binding scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
        if binding.get("source_role") == "PAPER_OPERATION":
            expected = (
                "PAPER",
                report.get("paper_session_id"),
                report.get("paper_artifact_path"),
                report.get("paper_artifact_hash"),
                report.get("paper_sample_count"),
                report.get("paper_artifact_age_seconds"),
            )
        elif binding.get("source_role") == "SHADOW_OBSERVATION":
            expected = (
                "SHADOW",
                report.get("shadow_session_id"),
                report.get("shadow_artifact_path"),
                report.get("shadow_artifact_hash"),
                report.get("shadow_sample_count"),
                report.get("shadow_artifact_age_seconds"),
            )
        else:
            return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow source evidence binding role is unsupported", "MEASUREMENT_MISSING")
        actual = (
            binding.get("mode"),
            binding.get("session_id"),
            binding.get("artifact_path"),
            binding.get("artifact_hash"),
            binding.get("sample_count"),
            binding.get("artifact_age_seconds"),
        )
        if actual != expected:
            return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow source evidence binding does not match source artifact", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("scorecard_input_eligible"):
        if blockers:
            return PaperShadowEvidenceValidationResult("BLOCKED", "eligible paper/shadow evidence cannot carry blockers", blockers[0].get("code", "UNKNOWN_BLOCKED"))
        if report.get("optimizer_ranking_action") != "ALLOW_RANKING":
            return PaperShadowEvidenceValidationResult("BLOCKED", "eligible paper/shadow evidence must allow paper ranking only", "SCORECARD_MISSING")
        if report.get("evidence_chain_complete") is not True:
            return PaperShadowEvidenceValidationResult("BLOCKED", "eligible paper/shadow evidence must have a complete chain", "MEASUREMENT_MISSING")
        return PaperShadowEvidenceValidationResult("PASS", "paper/shadow evidence is session-hashed and eligible for paper scorecard input only", None)
    if not blockers:
        return PaperShadowEvidenceValidationResult("BLOCKED", "non-eligible paper/shadow evidence must carry explicit blockers", "MEASUREMENT_MISSING")
    if report.get("optimizer_ranking_action") == "ALLOW_RANKING":
        return PaperShadowEvidenceValidationResult("BLOCKED", "blocked paper/shadow evidence cannot allow ranking", blockers[0].get("code", "UNKNOWN_BLOCKED"))
    return PaperShadowEvidenceValidationResult("BLOCKED", "paper/shadow evidence is blocked for scorecard input", blockers[0].get("code", "UNKNOWN_BLOCKED"))


def _paired_supporting_window_count(source_ids: list[str]) -> int:
    paper_keys = {
        key
        for source_id in source_ids
        if str(source_id).startswith(("paper:", "paper-operation:"))
        for key in [_supporting_source_window_key(str(source_id))]
        if key
    }
    shadow_keys = {
        key
        for source_id in source_ids
        if str(source_id).startswith(("shadow:", "shadow-evidence:"))
        for key in [_supporting_source_window_key(str(source_id))]
        if key
    }
    return len(paper_keys & shadow_keys)


def _supporting_source_window_key(source_id: str) -> str | None:
    parts = source_id.split(":")
    if len(parts) < 3:
        return None
    if parts[0] not in {"paper", "paper-operation", "shadow", "shadow-evidence"}:
        return None
    return parts[1] or None
