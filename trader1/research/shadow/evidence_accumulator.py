from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from trader1.research.shadow.shadow_runner import (
    build_paper_shadow_evidence_accumulation_report,
    paper_shadow_evidence_actionability_fields,
    paper_shadow_evidence_hash,
)


RUNTIME_COST_EVIDENCE_READY_STATUSES = {"PASS", "VALIDATED"}
RUNTIME_COST_EVIDENCE_REQUIRED_FIELDS = (
    "gross_expected_edge_bps",
    "expected_fee_bps",
    "expected_spread_bps",
    "expected_slippage_bps",
    "expected_impact_bps",
    "expected_latency_penalty_bps",
    "net_ev_after_cost_bps",
)


def build_paper_shadow_evidence_accumulation_from_operation_reports(
    *,
    evidence_report_id: str,
    paper_operation_reports: list[dict[str, Any]],
    shadow_evidence_reports: list[dict[str, Any]] | None = None,
    min_required_sample_count: int = 30,
    min_required_evidence_window_count: int = 20,
    min_required_evidence_span_hours: int = 120,
    max_artifact_age_seconds: int = 900,
    evidence_span_hours: int | None = None,
) -> dict[str, Any]:
    if not paper_operation_reports:
        raise ValueError("paper_operation_reports is required for scoped PAPER/SHADOW evidence accumulation")

    paper_sources = [_paper_source(report) for report in paper_operation_reports]
    shadow_sources = [_shadow_source(report) for report in shadow_evidence_reports or []]
    base_identity = paper_sources[0]["identity"]

    blockers: list[dict[str, str]] = []
    for source in [*paper_sources, *shadow_sources]:
        if source["identity"] != base_identity:
            blockers.append(
                _blocker(
                    "SNAPSHOT_SCOPE_MISMATCH",
                    "paper/shadow evidence accumulation contains mixed exchange, market, candidate, strategy, or parameter scope",
                )
            )
            break
        if source["live_flag_drift"]:
            blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "source evidence attempted live or scale-up state"))
            break

    paper_sample_count = sum(source["sample_count"] for source in paper_sources)
    shadow_sample_count = sum(source["sample_count"] for source in shadow_sources)
    entry_reason_count = sum(source["entry_reason_count"] for source in paper_sources)
    exit_reason_count = sum(source["exit_reason_count"] for source in paper_sources)
    no_trade_reason_count = sum(source["no_trade_reason_count"] for source in paper_sources)
    cost_evidence_count = sum(source["cost_evidence_count"] for source in paper_sources)

    paper_hashes = [source["artifact_hash"] for source in paper_sources]
    shadow_hashes = [source["artifact_hash"] for source in shadow_sources]
    paper_artifact_hash = _sha256_payload({"paper_hashes": paper_hashes})
    shadow_artifact_hash = _sha256_payload({"shadow_hashes": shadow_hashes or ["SHADOW_EVIDENCE_MISSING"]})
    if paper_artifact_hash == shadow_artifact_hash:
        shadow_artifact_hash = _sha256_payload({"shadow_hashes": shadow_hashes, "distinct_from_paper": paper_artifact_hash})

    evidence_window_count = min(len({source["session_id"] for source in paper_sources}), len({source["session_id"] for source in shadow_sources}))
    source_evidence_ids = [source["source_evidence_id"] for source in paper_sources + shadow_sources]
    if not source_evidence_ids:
        source_evidence_ids = ["paper-shadow-evidence-source-missing"]
    span_hours = int(evidence_span_hours if evidence_span_hours is not None else 0)

    report = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id=evidence_report_id,
        candidate_id=base_identity["candidate_id"],
        strategy_id=base_identity["strategy_id"],
        strategy_build_id=base_identity["strategy_build_id"],
        parameter_hash=base_identity["parameter_hash"],
        exchange=base_identity["exchange"],
        market_type=base_identity["market_type"],
        paper_session_id=f"{paper_sources[0]['session_id']}_aggregate",
        shadow_session_id=f"{paper_sources[0]['session_id']}_shadow_aggregate",
        paper_artifact_hash=paper_artifact_hash,
        shadow_artifact_hash=shadow_artifact_hash,
        paper_sample_count=paper_sample_count,
        shadow_sample_count=shadow_sample_count,
        min_required_sample_count=min_required_sample_count,
        evidence_window_count=evidence_window_count,
        min_required_evidence_window_count=min_required_evidence_window_count,
        evidence_span_hours=span_hours,
        min_required_evidence_span_hours=min_required_evidence_span_hours,
        evidence_span_source="EXPLICIT_OPERATOR_SUPPLIED" if evidence_span_hours is not None else "NOT_PROVIDED",
        paper_artifact_age_seconds=max(source["artifact_age_seconds"] for source in paper_sources),
        shadow_artifact_age_seconds=max([source["artifact_age_seconds"] for source in shadow_sources] or [0]),
        max_artifact_age_seconds=max_artifact_age_seconds,
        entry_reason_count=entry_reason_count,
        exit_reason_count=exit_reason_count,
        no_trade_reason_count=no_trade_reason_count,
        cost_evidence_count=cost_evidence_count,
        source_evidence_ids=source_evidence_ids,
    )
    if blockers:
        _force_blocked(report, blockers)
    return report


def build_paper_shadow_evidence_accumulation_from_runtime_artifacts(
    *,
    evidence_report_id: str,
    candidate_scorecard: dict[str, Any],
    overfit_diagnostic_report: dict[str, Any],
    paper_sample_history: dict[str, Any],
    shadow_runtime_harness_report: dict[str, Any],
    shadow_runtime_sample_history: dict[str, Any] | None = None,
    paper_session_id: str = "mvp1_upbit_paper_launcher",
    shadow_session_id: str = "mvp1_upbit_paper_launcher_shadow",
    min_required_sample_count: int = 30,
    min_required_evidence_window_count: int = 20,
    min_required_evidence_span_hours: int = 120,
    max_artifact_age_seconds: int = 900,
) -> dict[str, Any]:
    """Build a current PAPER/SHADOW accumulator from real non-live runtime artifacts."""

    identity = _runtime_identity(candidate_scorecard, overfit_diagnostic_report)
    paper_samples = _paper_candidate_sample_count(overfit_diagnostic_report, paper_sample_history)
    shadow_samples = _shadow_observation_count(
        shadow_runtime_harness_report,
        shadow_runtime_sample_history=shadow_runtime_sample_history,
    )
    paper_windows = _safe_int(
        paper_sample_history.get("accepted_loop_report_count"),
        len({str(sample.get("loop_id") or sample.get("cycle_id")) for sample in _history_samples(paper_sample_history)}),
    )
    shadow_windows = _shadow_runtime_window_count(
        shadow_runtime_harness_report,
        shadow_runtime_sample_history=shadow_runtime_sample_history,
    )
    evidence_windows = max(0, min(paper_windows, shadow_windows))
    paper_span_seconds = _safe_int(paper_sample_history.get("observed_span_seconds"), 0)
    shadow_span_seconds = _shadow_runtime_span_seconds(
        shadow_runtime_harness_report,
        shadow_runtime_sample_history=shadow_runtime_sample_history,
    )
    paired_span_seconds = min(paper_span_seconds, shadow_span_seconds)
    evidence_span_hours = paired_span_seconds // 3600
    span_source = "DERIVED_FROM_SUPPORTING_WINDOWS" if paired_span_seconds > 0 else "NOT_PROVIDED"
    runtime_statuses = _actual_runtime_requirement_statuses(
        shadow_runtime_harness_report,
        shadow_runtime_sample_history=shadow_runtime_sample_history,
    )
    shadow_artifact_hash = _runtime_shadow_artifact_hash(
        shadow_runtime_harness_report,
        shadow_runtime_sample_history=shadow_runtime_sample_history,
    )
    actual_runtime_source_ids = _actual_runtime_source_evidence_ids(
        paper_sample_history=paper_sample_history,
        overfit_diagnostic_report=overfit_diagnostic_report,
        shadow_runtime_harness_report=shadow_runtime_harness_report,
        shadow_runtime_sample_history=shadow_runtime_sample_history,
        shadow_artifact_hash=shadow_artifact_hash,
        exchange=identity["exchange"],
        market_type=identity["market_type"],
        paper_session_id=paper_session_id,
        shadow_session_id=shadow_session_id,
        paper_span_seconds=paper_span_seconds,
        shadow_span_seconds=shadow_span_seconds,
        paper_samples=paper_samples,
        shadow_samples=shadow_samples,
    )
    actual_runtime_source_status = _actual_runtime_source_status(
        actual_runtime_source_ids=actual_runtime_source_ids,
        runtime_statuses=runtime_statuses,
        shadow_samples=shadow_samples,
    )

    report = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id=evidence_report_id,
        candidate_id=identity["candidate_id"],
        strategy_id=identity["strategy_id"],
        strategy_build_id=identity["strategy_build_id"],
        parameter_hash=identity["parameter_hash"],
        exchange=identity["exchange"],
        market_type=identity["market_type"],
        paper_session_id=paper_session_id,
        shadow_session_id=shadow_session_id,
        paper_artifact_hash=_runtime_paper_artifact_hash(paper_sample_history, overfit_diagnostic_report),
        shadow_artifact_hash=shadow_artifact_hash,
        paper_sample_count=paper_samples,
        shadow_sample_count=shadow_samples,
        min_required_sample_count=min_required_sample_count,
        evidence_window_count=evidence_windows,
        min_required_evidence_window_count=min_required_evidence_window_count,
        evidence_span_hours=evidence_span_hours,
        min_required_evidence_span_hours=min_required_evidence_span_hours,
        evidence_span_source=span_source,
        paper_runtime_span_seconds=paper_span_seconds,
        shadow_runtime_span_seconds=shadow_span_seconds,
        paper_artifact_age_seconds=0,
        shadow_artifact_age_seconds=0,
        max_artifact_age_seconds=max_artifact_age_seconds,
        entry_reason_count=_history_reason_count(paper_sample_history, "entry_reason_count"),
        exit_reason_count=_history_reason_count(paper_sample_history, "exit_reason_count"),
        no_trade_reason_count=_history_reason_count(paper_sample_history, "no_trade_reason_count"),
        cost_evidence_count=_runtime_cost_evidence_count(candidate_scorecard, paper_sample_history, paper_samples),
        source_evidence_ids=_runtime_supporting_source_evidence_ids(
            paper_sample_history,
            shadow_runtime_harness_report,
            shadow_runtime_sample_history,
            evidence_windows,
        ),
        actual_runtime_source_evidence_ids=actual_runtime_source_ids,
        actual_runtime_source_status=actual_runtime_source_status,
        actual_runtime_requirement_statuses=runtime_statuses,
    )

    blockers: list[dict[str, str]] = []
    if _runtime_live_flag_drift(
        candidate_scorecard,
        overfit_diagnostic_report,
        paper_sample_history,
        shadow_runtime_harness_report,
        shadow_runtime_sample_history or {},
    ):
        blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "source runtime evidence attempted live or scale-up state"))
    if shadow_runtime_sample_history is not None and not _shadow_history_usable(shadow_runtime_sample_history):
        blockers.append(_blocker("MEASUREMENT_MISSING", "SHADOW runtime sample history is present but not validated as source-bound short-window evidence"))
    if identity["exchange"] != "UPBIT" or identity["market_type"] != "KRW_SPOT":
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "runtime PAPER/SHADOW evidence is MVP-4 scoped to UPBIT/KRW_SPOT"))
    if blockers:
        _force_blocked(report, blockers)
    return report


def _paper_source(report: dict[str, Any]) -> dict[str, Any]:
    evidence = report.get("paper_shadow_evidence_accumulation_report") or {}
    paper = report.get("paper_dry_run_report") or {}
    strategy = report.get("strategy_unit") or {}
    artifact_hash = str(report.get("operation_gate_hash") or paper.get("dry_run_hash") or _sha256_payload(report))
    session_id = str(report.get("session_id") or evidence.get("paper_session_id") or "paper-session-missing")
    return {
        "source_evidence_id": f"paper-operation:{report.get('operation_gate_id', session_id)}:{artifact_hash}",
        "session_id": session_id,
        "artifact_hash": artifact_hash,
        "artifact_age_seconds": int(evidence.get("paper_artifact_age_seconds", 0)),
        "sample_count": int(evidence.get("paper_sample_count", 0)),
        "entry_reason_count": int(evidence.get("entry_reason_count", len(paper.get("entry_reasons") or []))),
        "exit_reason_count": int(evidence.get("exit_reason_count", len(paper.get("exit_reasons") or []))),
        "no_trade_reason_count": int(evidence.get("no_trade_reason_count", len(paper.get("no_trade_reasons") or []))),
        "cost_evidence_count": int(evidence.get("cost_evidence_count", 0)),
        "identity": {
            "exchange": str(report.get("exchange") or evidence.get("exchange") or "UPBIT"),
            "market_type": str(report.get("market_type") or evidence.get("market_type") or "KRW_SPOT"),
            "candidate_id": str(evidence.get("candidate_id") or strategy.get("strategy_unit_id") or "candidate-missing"),
            "strategy_id": str(evidence.get("strategy_id") or strategy.get("strategy_id") or "strategy-missing"),
            "strategy_build_id": str(evidence.get("strategy_build_id") or strategy.get("strategy_build_id") or "strategy-build-missing"),
            "parameter_hash": str(evidence.get("parameter_hash") or strategy.get("parameter_hash") or "0" * 64),
        },
        "live_flag_drift": any(
            bool(_nested_flag(source, field))
            for source in (report, evidence, paper)
            for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called")
        ),
    }


def _shadow_source(report: dict[str, Any]) -> dict[str, Any]:
    artifact_hash = str(report.get("evidence_hash") or report.get("shadow_artifact_hash") or _sha256_payload(report))
    session_id = str(report.get("shadow_session_id") or report.get("session_id") or "shadow-session-missing")
    return {
        "source_evidence_id": f"shadow-evidence:{report.get('evidence_report_id', session_id)}:{artifact_hash}",
        "session_id": session_id,
        "artifact_hash": artifact_hash,
        "artifact_age_seconds": int(report.get("shadow_artifact_age_seconds", 0)),
        "sample_count": int(report.get("shadow_sample_count", 0)),
        "entry_reason_count": 0,
        "exit_reason_count": 0,
        "no_trade_reason_count": 0,
        "cost_evidence_count": 0,
        "identity": {
            "exchange": str(report.get("exchange") or "UPBIT"),
            "market_type": str(report.get("market_type") or "KRW_SPOT"),
            "candidate_id": str(report.get("candidate_id") or "candidate-missing"),
            "strategy_id": str(report.get("strategy_id") or "strategy-missing"),
            "strategy_build_id": str(report.get("strategy_build_id") or "strategy-build-missing"),
            "parameter_hash": str(report.get("parameter_hash") or "0" * 64),
        },
        "live_flag_drift": any(
            bool(report.get(field))
            for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called")
        ),
    }


def _force_blocked(report: dict[str, Any], blockers: Iterable[dict[str, str]]) -> None:
    merged: list[dict[str, str]] = []
    seen: set[tuple[str | None, str | None]] = set()
    for blocker in blockers:
        key = (blocker.get("code"), blocker.get("message"))
        if key not in seen:
            merged.append(blocker)
            seen.add(key)
    for blocker in report.get("blockers") or []:
        key = (blocker.get("code"), blocker.get("message"))
        if key not in seen:
            merged.append(blocker)
            seen.add(key)
    report["blockers"] = merged
    report["primary_blocker_code"] = merged[0]["code"] if merged else None
    report["evidence_chain_complete"] = False
    report["scorecard_input_eligible"] = False
    report["optimizer_ranking_action"] = "BLOCK_RANKING"
    report["promotion_eligible"] = False
    report["live_order_ready"] = False
    report["live_order_allowed"] = False
    report["can_live_trade"] = False
    report["scale_up_allowed"] = False
    report["order_adapter_called"] = False
    report.update(paper_shadow_evidence_actionability_fields(report))
    report["evidence_hash"] = paper_shadow_evidence_hash(report)


def _blocker(code: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": "HIGH", "message": message}


def _nested_flag(source: dict[str, Any], field: str) -> Any:
    return source.get(field) if isinstance(source, dict) else None


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def _runtime_identity(candidate_scorecard: dict[str, Any], overfit_diagnostic_report: dict[str, Any]) -> dict[str, str]:
    return {
        "exchange": str(candidate_scorecard.get("exchange") or overfit_diagnostic_report.get("exchange") or "UPBIT"),
        "market_type": str(candidate_scorecard.get("market_type") or overfit_diagnostic_report.get("market_type") or "KRW_SPOT"),
        "candidate_id": str(candidate_scorecard.get("candidate_id") or overfit_diagnostic_report.get("candidate_id") or "candidate-missing"),
        "strategy_id": str(candidate_scorecard.get("strategy_id") or overfit_diagnostic_report.get("strategy_id") or "strategy-missing"),
        "strategy_build_id": str(
            candidate_scorecard.get("strategy_build_id")
            or overfit_diagnostic_report.get("strategy_build_id")
            or "strategy-build-missing"
        ),
        "parameter_hash": str(candidate_scorecard.get("parameter_hash") or overfit_diagnostic_report.get("parameter_hash") or "0" * 64),
    }


def _history_samples(paper_sample_history: dict[str, Any]) -> list[dict[str, Any]]:
    return [sample for sample in paper_sample_history.get("samples") or [] if isinstance(sample, dict)]


def _paper_candidate_sample_count(overfit_diagnostic_report: dict[str, Any], paper_sample_history: dict[str, Any]) -> int:
    accepted = _safe_int(paper_sample_history.get("accepted_cycle_sample_count"), len(_history_samples(paper_sample_history)))
    overfit_samples = _safe_int(overfit_diagnostic_report.get("sample_count"), 0)
    if overfit_samples > 0 and accepted > 0:
        return min(overfit_samples, accepted)
    return max(overfit_samples, accepted)


def _shadow_observation_count(
    shadow_runtime_harness_report: dict[str, Any],
    *,
    shadow_runtime_sample_history: dict[str, Any] | None = None,
) -> int:
    if shadow_runtime_harness_report.get("harness_status") != "PASS":
        return 0
    if _any_live_flag(shadow_runtime_harness_report):
        return 0
    harness_count = _safe_int(shadow_runtime_harness_report.get("observation_count"), 0)
    if not _shadow_history_usable(shadow_runtime_sample_history):
        return harness_count
    observations_per_cycle = max(1, _safe_int(shadow_runtime_harness_report.get("observations_per_cycle"), 1))
    history_count = _shadow_history_cycle_count(shadow_runtime_sample_history) * observations_per_cycle
    return max(harness_count, history_count)


def _shadow_runtime_window_count(
    shadow_runtime_harness_report: dict[str, Any],
    *,
    shadow_runtime_sample_history: dict[str, Any] | None = None,
) -> int:
    harness_windows = _safe_int(shadow_runtime_harness_report.get("completed_cycle_count"), 0)
    if not _shadow_history_usable(shadow_runtime_sample_history):
        return harness_windows
    return max(harness_windows, _shadow_history_cycle_count(shadow_runtime_sample_history))


def _shadow_runtime_span_seconds(
    shadow_runtime_harness_report: dict[str, Any],
    *,
    shadow_runtime_sample_history: dict[str, Any] | None = None,
) -> int:
    harness_span = _safe_int(shadow_runtime_harness_report.get("measured_runtime_seconds"), 0)
    if not _shadow_history_usable(shadow_runtime_sample_history):
        return harness_span
    return max(harness_span, _safe_int(shadow_runtime_sample_history.get("observed_span_seconds"), 0))


def _actual_runtime_requirement_statuses(
    shadow_runtime_harness_report: dict[str, Any],
    *,
    shadow_runtime_sample_history: dict[str, Any] | None = None,
) -> dict[str, str]:
    completed = _safe_int(shadow_runtime_harness_report.get("completed_cycle_count"), 0)
    heartbeat = _safe_int(shadow_runtime_harness_report.get("heartbeat_count"), 0)
    measured = _safe_int(shadow_runtime_harness_report.get("measured_runtime_seconds"), 0)
    min_runtime = _safe_int(shadow_runtime_harness_report.get("minimum_runtime_window_seconds"), 86400)
    min_cycles = _safe_int(shadow_runtime_harness_report.get("minimum_actual_cycle_count"), 2880)
    blockers = {
        str(blocker.get("code"))
        for blocker in shadow_runtime_harness_report.get("blockers") or []
        if isinstance(blocker, dict) and blocker.get("code")
    }
    clean_recovery = not (blockers & {"PARTIAL_WRITE_RECOVERY_REQUIRED", "DUPLICATE_WRITER_RISK"})
    if _shadow_history_usable(shadow_runtime_sample_history):
        completed = max(completed, _shadow_history_cycle_count(shadow_runtime_sample_history))
        measured = max(measured, _safe_int(shadow_runtime_sample_history.get("observed_span_seconds"), 0))
        heartbeat = max(heartbeat, completed)
    return {
        # Short-window history is observable runtime input, but it cannot satisfy the long-run source gate by itself.
        "runtime_span": "PASS" if measured >= min_runtime and _shadow_history_long_run_eligible(shadow_runtime_sample_history) else "BLOCKED",
        "cycle_count": "PASS" if completed >= min_cycles and _shadow_history_long_run_eligible(shadow_runtime_sample_history) else "BLOCKED",
        "heartbeat_freshness": "PASS" if completed > 0 and heartbeat >= completed else "BLOCKED",
        "recovery_clean": "PASS" if clean_recovery else "BLOCKED",
        "partial_write_clean": "PASS" if clean_recovery else "BLOCKED",
    }


def _history_reason_count(paper_sample_history: dict[str, Any], field: str) -> int:
    return sum(_safe_int(sample.get(field), 0) for sample in _history_samples(paper_sample_history))


def _runtime_cost_evidence_count(
    candidate_scorecard: dict[str, Any],
    paper_sample_history: dict[str, Any],
    paper_sample_count: int,
) -> int:
    if candidate_scorecard.get("cost_model_status") not in RUNTIME_COST_EVIDENCE_READY_STATUSES:
        return 0
    if paper_sample_count <= 0:
        return 0
    for field in RUNTIME_COST_EVIDENCE_REQUIRED_FIELDS:
        if _safe_float(candidate_scorecard.get(field)) is None:
            return 0
    candidate_sample_count = sum(1 for sample in _history_samples(paper_sample_history) if _safe_int(sample.get("candidate_count"), 0) > 0)
    if candidate_sample_count <= 0:
        return 0
    return min(paper_sample_count, candidate_sample_count)


def _runtime_supporting_source_evidence_ids(
    paper_sample_history: dict[str, Any],
    shadow_runtime_harness_report: dict[str, Any],
    shadow_runtime_sample_history: dict[str, Any] | None,
    evidence_window_count: int,
) -> list[str]:
    if evidence_window_count <= 0:
        return []
    paper_windows = _paper_window_representative_samples(paper_sample_history)
    shadow_window_hashes = _shadow_window_hashes(
        shadow_runtime_harness_report,
        shadow_runtime_sample_history=shadow_runtime_sample_history,
    )
    shadow_windows = len(shadow_window_hashes)
    paired_count = min(evidence_window_count, len(paper_windows), shadow_windows)
    if paired_count <= 0:
        return []

    source_ids: list[str] = []
    for index, paper_sample in enumerate(paper_windows[:paired_count], start=1):
        window_key = f"runtime-window-{index:04d}"
        paper_hash = _runtime_sample_source_hash(paper_sample)
        shadow_hash = shadow_window_hashes[index - 1]
        source_ids.append(f"paper:{window_key}:{paper_hash}")
        source_ids.append(f"shadow:{window_key}:{shadow_hash}")
    return source_ids


def _actual_runtime_source_evidence_ids(
    *,
    paper_sample_history: dict[str, Any],
    overfit_diagnostic_report: dict[str, Any],
    shadow_runtime_harness_report: dict[str, Any],
    shadow_runtime_sample_history: dict[str, Any] | None = None,
    shadow_artifact_hash: str | None = None,
    exchange: str,
    market_type: str,
    paper_session_id: str,
    shadow_session_id: str,
    paper_span_seconds: int,
    shadow_span_seconds: int,
    paper_samples: int,
    shadow_samples: int,
) -> list[str]:
    if min(paper_samples, shadow_samples) <= 0 and min(paper_span_seconds, shadow_span_seconds) <= 0:
        return []
    if paper_span_seconds <= 0 or shadow_span_seconds <= 0:
        return []
    exchange_slug = exchange.lower()
    market_type_slug = market_type.lower()
    return [
        (
            "actual-runtime-source:"
            f"{exchange_slug}:{market_type_slug}:paper:{paper_session_id}:"
            f"{_runtime_paper_artifact_hash(paper_sample_history, overfit_diagnostic_report)}"
        ),
        (
            "actual-runtime-source:"
            f"{exchange_slug}:{market_type_slug}:shadow:{shadow_session_id}:"
            f"{shadow_artifact_hash or _runtime_shadow_artifact_hash(shadow_runtime_harness_report, shadow_runtime_sample_history=shadow_runtime_sample_history)}"
        ),
    ]


def _actual_runtime_source_status(
    *,
    actual_runtime_source_ids: list[str],
    runtime_statuses: dict[str, str],
    shadow_samples: int,
) -> str:
    if not actual_runtime_source_ids:
        return "STUB_ONLY" if shadow_samples > 0 else "MISSING"
    if all(runtime_statuses.get(key) == "PASS" for key in ("runtime_span", "cycle_count", "heartbeat_freshness", "recovery_clean", "partial_write_clean")):
        return "VALIDATED_NON_LIVE_RUNTIME"
    return "PARTIAL_NON_LIVE_RUNTIME"


def _paper_window_representative_samples(paper_sample_history: dict[str, Any]) -> list[dict[str, Any]]:
    representatives: list[dict[str, Any]] = []
    seen_loop_ids: set[str] = set()
    for sample in _history_samples(paper_sample_history):
        loop_id = str(sample.get("loop_id") or sample.get("cycle_id") or "")
        if not loop_id or loop_id in seen_loop_ids:
            continue
        if _safe_int(sample.get("candidate_count"), 0) <= 0:
            continue
        seen_loop_ids.add(loop_id)
        representatives.append(sample)
    return representatives


def _runtime_sample_source_hash(sample: dict[str, Any]) -> str:
    for field in ("source_runtime_cycle_hash", "sample_hash"):
        value = str(sample.get(field) or "")
        if _is_sha256_hex(value):
            return value.upper()
    return _sha256_payload(sample)


def _runtime_paper_artifact_hash(
    paper_sample_history: dict[str, Any],
    overfit_diagnostic_report: dict[str, Any],
) -> str:
    for field in ("history_hash",):
        value = str(paper_sample_history.get(field) or "")
        if _is_sha256_hex(value):
            return value.upper()
    value = str(overfit_diagnostic_report.get("diagnostic_hash") or "")
    if _is_sha256_hex(value):
        return value.upper()
    return _sha256_payload(
        {
            "history_id": paper_sample_history.get("history_id"),
            "accepted_cycle_sample_count": paper_sample_history.get("accepted_cycle_sample_count"),
            "overfit_diagnostic_id": overfit_diagnostic_report.get("diagnostic_id"),
            "overfit_sample_count": overfit_diagnostic_report.get("sample_count"),
        }
    )


def _runtime_shadow_artifact_hash(
    shadow_runtime_harness_report: dict[str, Any],
    *,
    shadow_runtime_sample_history: dict[str, Any] | None = None,
) -> str:
    if _shadow_history_usable(shadow_runtime_sample_history):
        value = str(shadow_runtime_sample_history.get("history_hash") or "")
        if _is_sha256_hex(value):
            return value.upper()
    for field in ("harness_report_hash", "source_runtime_report_hash", "source_actual_blocker_report_hash"):
        value = str(shadow_runtime_harness_report.get(field) or "")
        if _is_sha256_hex(value):
            return value.upper()
    return _sha256_payload(
        {
            "harness_id": shadow_runtime_harness_report.get("harness_id"),
            "observation_count": shadow_runtime_harness_report.get("observation_count"),
            "completed_cycle_count": shadow_runtime_harness_report.get("completed_cycle_count"),
        }
    )


def _shadow_history_usable(shadow_runtime_sample_history: dict[str, Any] | None) -> bool:
    if not isinstance(shadow_runtime_sample_history, dict):
        return False
    if shadow_runtime_sample_history.get("schema_id") != "trader1.shadow_runtime_sample_history.v1":
        return False
    if shadow_runtime_sample_history.get("exchange") != "UPBIT" or shadow_runtime_sample_history.get("market_type") != "KRW_SPOT":
        return False
    if shadow_runtime_sample_history.get("source_mode") != "PAPER" or shadow_runtime_sample_history.get("mode") != "SHADOW":
        return False
    if _any_live_flag(shadow_runtime_sample_history):
        return False
    if any(
        shadow_runtime_sample_history.get(field)
        for field in ("long_run_evidence_eligible", "actual_long_run_evidence_created", "promotion_eligible")
    ):
        return False
    value = str(shadow_runtime_sample_history.get("history_hash") or "")
    if not _is_sha256_hex(value):
        return False
    if _shadow_history_hash(shadow_runtime_sample_history) != value.upper():
        return False
    samples = _shadow_history_accepted_samples(shadow_runtime_sample_history)
    if not samples:
        return False
    return all(
        sample.get("source_validation_status") == "PASS"
        and sample.get("validation_status") == "PASS"
        and sample.get("source_hashes_verified") is True
        and sample.get("source_runtime_hash_pairing_verified") is True
        and sample.get("runtime_evidence_role") == "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN"
        and int(sample.get("observed_actual_cycle_count") or 0) > 0
        and not _any_live_flag(sample)
        and not any(
            sample.get(field)
            for field in ("long_run_evidence_eligible", "actual_long_run_runtime_present", "scorecard_input_eligible", "promotion_eligible")
        )
        for sample in samples
    )


def _shadow_history_hash(shadow_runtime_sample_history: dict[str, Any]) -> str:
    payload = dict(shadow_runtime_sample_history)
    payload.pop("history_hash", None)
    return _sha256_payload(payload)


def _shadow_history_accepted_samples(shadow_runtime_sample_history: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(shadow_runtime_sample_history, dict):
        return []
    return [
        sample
        for sample in shadow_runtime_sample_history.get("samples") or []
        if isinstance(sample, dict) and sample.get("accepted") is True
    ]


def _shadow_history_cycle_count(shadow_runtime_sample_history: dict[str, Any] | None) -> int:
    if not isinstance(shadow_runtime_sample_history, dict):
        return 0
    return max(
        _safe_int(shadow_runtime_sample_history.get("accepted_cycle_sample_count"), 0),
        sum(_safe_int(sample.get("observed_actual_cycle_count"), 0) for sample in _shadow_history_accepted_samples(shadow_runtime_sample_history)),
    )


def _shadow_history_long_run_eligible(shadow_runtime_sample_history: dict[str, Any] | None) -> bool:
    return isinstance(shadow_runtime_sample_history, dict) and shadow_runtime_sample_history.get("long_run_evidence_eligible") is True


def _shadow_window_hashes(
    shadow_runtime_harness_report: dict[str, Any],
    *,
    shadow_runtime_sample_history: dict[str, Any] | None = None,
) -> list[str]:
    if _shadow_history_usable(shadow_runtime_sample_history):
        hashes: list[str] = []
        history_hash = str(shadow_runtime_sample_history.get("history_hash") or "")
        for sample_index, sample in enumerate(_shadow_history_accepted_samples(shadow_runtime_sample_history), start=1):
            cycles = _safe_int(sample.get("observed_actual_cycle_count"), 0)
            for cycle_index in range(1, cycles + 1):
                hashes.append(
                    _sha256_payload(
                        {
                            "source": "shadow_runtime_sample_history_window",
                            "history_hash": history_hash,
                            "sample_id": sample.get("sample_id"),
                            "orchestration_report_hash": sample.get("orchestration_report_hash"),
                            "sample_index": sample_index,
                            "cycle_index": cycle_index,
                        }
                    )
                )
        return hashes

    shadow_anchor_hash = _runtime_shadow_artifact_hash(shadow_runtime_harness_report)
    observations_per_cycle = _safe_int(shadow_runtime_harness_report.get("observations_per_cycle"), 0)
    return [
        _sha256_payload(
            {
                "source": "shadow_runtime_harness_window",
                "harness_hash": shadow_anchor_hash,
                "completed_cycle_index": index,
                "observations_per_cycle": observations_per_cycle,
            }
        )
        for index in range(1, max(0, _safe_int(shadow_runtime_harness_report.get("completed_cycle_count"), 0)) + 1)
    ]


def _runtime_live_flag_drift(*reports: dict[str, Any]) -> bool:
    return any(_any_live_flag(report) for report in reports if isinstance(report, dict))


def _any_live_flag(report: dict[str, Any]) -> bool:
    return any(bool(report.get(field)) for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called"))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_sha256_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True
