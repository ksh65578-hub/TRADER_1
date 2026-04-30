from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from trader1.research.shadow.shadow_runner import (
    build_paper_shadow_evidence_accumulation_report,
    paper_shadow_evidence_hash,
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
    report["evidence_hash"] = paper_shadow_evidence_hash(report)


def _blocker(code: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": "HIGH", "message": message}


def _nested_flag(source: dict[str, Any], field: str) -> Any:
    return source.get(field) if isinstance(source, dict) else None


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()
