from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.adapters.upbit.paper_broker import build_upbit_paper_dry_run_report, validate_upbit_paper_dry_run_report
from trader1.core.decision.decision_arbiter import choose_operational_paper_decision, select_primary_blocker
from trader1.core.ledger.restart_recovery import build_restart_recovery_report, validate_restart_recovery_report
from trader1.core.sizing.position_sizing import build_position_sizing_decision, validate_position_sizing_decision
from trader1.core.strategy.strategy_unit import build_basic_strategy_unit, validate_strategy_unit
from trader1.dashboard.panels.no_trade_panel import build_no_trade_panel
from trader1.dashboard.panels.portfolio_panel import build_portfolio_panel
from trader1.dashboard.panels.status_panel import build_status_panel
from trader1.research.replay.replay_runner import build_replay_consistency_report, validate_replay_consistency_report
from trader1.research.shadow.shadow_runner import (
    build_paper_shadow_evidence_accumulation_report,
    build_paper_shadow_separation_report,
    validate_paper_shadow_evidence_accumulation_report,
    validate_paper_shadow_separation_report,
)


PAPER_OPERATION_GATE_SCHEMA_ID = "trader1.paper_operation_gate_report.v1"


@dataclass(frozen=True)
class PaperOperationGateValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def operation_gate_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("operation_gate_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _collect_blocker(result: Any, label: str) -> dict[str, str] | None:
    if result.status == "PASS":
        return None
    return _blocker(result.blocker_code or "UNKNOWN_BLOCKED", f"{label}: {result.message}")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def _paper_evidence_sample_count(report: dict[str, Any]) -> int:
    event_count = len(report.get("paper_ledger_events") or [])
    reason_count = len(report.get("entry_reasons") or []) + len(report.get("no_trade_reasons") or [])
    return max(event_count, reason_count, 1)


def _cost_evidence_count(report: dict[str, Any]) -> int:
    return int(report.get("fee_model_status") == "PASS") + int(report.get("slippage_model_status") == "PASS")


def build_upbit_operational_paper_cycle(
    *,
    operation_gate_id: str,
    session_id: str = "mvp3_operational_paper",
    requested_entry: bool = True,
    risk_block: bool = False,
    symbol: str = "KRW-BTC",
    public_market_data: dict[str, Any] | None = None,
    strategy_unit_id: str | None = None,
    strategy_id: str = "basic_momentum_fixture",
    strategy_build_id: str = "mvp3_fixture_001",
    parameter_hash: str | None = None,
    timeframe_scope: str = "15m",
    regime_scope: str = "RANGE",
    signal_strength: str = "0.60",
    strategy_confidence: str = "0.55",
    regime_confidence: str = "0.55",
    source_evidence_ids: list[str] | None = None,
    paper_sample_count: int | None = None,
    shadow_sample_count: int = 0,
    evidence_window_count: int = 1,
    evidence_span_hours: int = 0,
    entry_reason_count: int | None = None,
    no_trade_reason_count: int | None = None,
    cost_evidence_count: int | None = None,
) -> dict[str, Any]:
    strategy_unit = build_basic_strategy_unit(
        strategy_unit_id=strategy_unit_id or f"{operation_gate_id}-strategy-unit",
        strategy_id=strategy_id,
        strategy_build_id=strategy_build_id,
        parameter_hash=parameter_hash,
        session_id=session_id,
        timeframe_scope=timeframe_scope,
        regime_scope=regime_scope,
        signal_intent="ENTER_LONG" if requested_entry else "NO_TRADE",
        signal_strength=signal_strength,
        strategy_confidence=strategy_confidence,
        regime_confidence=regime_confidence,
        source_evidence_ids=source_evidence_ids,
    )
    sizing_decision = build_position_sizing_decision(
        sizing_decision_id=f"{operation_gate_id}-sizing",
        strategy_unit_id=strategy_unit["strategy_unit_id"],
        session_id=session_id,
    )
    blockers: list[dict[str, str]] = []
    if risk_block:
        blockers.append(_blocker("RISK_VETO", "paper risk veto blocked the operational cycle"))
    for result, label in [
        (validate_strategy_unit(strategy_unit), "strategy_unit"),
        (validate_position_sizing_decision(sizing_decision), "sizing_decision"),
    ]:
        blocker = _collect_blocker(result, label)
        if blocker:
            blockers.append(blocker)
    final_decision, primary = choose_operational_paper_decision(requested_entry=requested_entry, blockers=blockers)
    paper_report = build_upbit_paper_dry_run_report(
        paper_run_id=f"{operation_gate_id}-paper",
        session_id=session_id,
        symbol=symbol,
        requested_entry=final_decision == "ENTER_LONG",
        risk_block=risk_block,
        public_market_data=public_market_data,
    )
    restart_report = build_restart_recovery_report(restart_id=f"{operation_gate_id}-restart", session_id=session_id)
    replay_report = build_replay_consistency_report(
        replay_id=f"{operation_gate_id}-replay",
        strategy_unit_id=strategy_unit["strategy_unit_id"],
        parameter_hash=strategy_unit["parameter_hash"],
        input_events=paper_report["paper_ledger_events"] or restart_report["ledger_events"],
        session_id=f"{session_id}_replay",
    )
    separation_report = build_paper_shadow_separation_report(
        separation_report_id=f"{operation_gate_id}-paper-shadow",
        paper_session_id=session_id,
        shadow_session_id=f"{session_id}_shadow",
    )
    measured_paper_sample_count = paper_sample_count
    if measured_paper_sample_count is None:
        measured_paper_sample_count = _paper_evidence_sample_count(paper_report)
    measured_entry_reason_count = (
        int(entry_reason_count)
        if entry_reason_count is not None
        else len(paper_report.get("entry_reasons") or [])
    )
    measured_no_trade_reason_count = (
        int(no_trade_reason_count)
        if no_trade_reason_count is not None
        else len(paper_report.get("no_trade_reasons") or [])
    )
    measured_cost_evidence_count = (
        int(cost_evidence_count)
        if cost_evidence_count is not None
        else _cost_evidence_count(paper_report)
    )
    paper_artifact_hash = paper_report["dry_run_hash"]
    shadow_artifact_hash = _sha256_text(f"{operation_gate_id}:{session_id}:shadow-observation-missing")
    paper_shadow_evidence_report = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id=f"{operation_gate_id}-paper-shadow-evidence",
        candidate_id=strategy_unit["strategy_unit_id"],
        strategy_id=strategy_unit["strategy_id"],
        strategy_build_id=strategy_unit["strategy_build_id"],
        parameter_hash=strategy_unit["parameter_hash"],
        paper_session_id=session_id,
        shadow_session_id=f"{session_id}_shadow",
        paper_artifact_hash=paper_artifact_hash,
        shadow_artifact_hash=shadow_artifact_hash,
        paper_sample_count=max(1, int(measured_paper_sample_count)),
        shadow_sample_count=shadow_sample_count,
        evidence_window_count=max(1, int(evidence_window_count)),
        evidence_span_hours=max(0, int(evidence_span_hours)),
        entry_reason_count=max(0, measured_entry_reason_count),
        no_trade_reason_count=max(0, measured_no_trade_reason_count),
        cost_evidence_count=max(0, measured_cost_evidence_count),
        source_evidence_ids=[
            paper_report["paper_run_id"],
            replay_report["replay_id"],
            separation_report["separation_report_id"],
            *(source_evidence_ids or []),
        ],
    )
    for result, label in [
        (validate_upbit_paper_dry_run_report(paper_report), "paper_dry_run"),
        (validate_restart_recovery_report(restart_report), "restart_recovery"),
        (validate_replay_consistency_report(replay_report), "replay_consistency"),
        (validate_paper_shadow_separation_report(separation_report), "paper_shadow_separation"),
        (validate_paper_shadow_evidence_accumulation_report(paper_shadow_evidence_report), "paper_shadow_evidence"),
    ]:
        if label == "paper_shadow_evidence" and result.status == "BLOCKED" and result.blocker_code in {
            "SAMPLE_INSUFFICIENT",
            "MEASUREMENT_MISSING",
            "EXECUTION_FEEDBACK_MISSING",
        }:
            continue
        blocker = _collect_blocker(result, label)
        if blocker:
            blockers.append(blocker)
    primary_code = select_primary_blocker(blockers) or primary
    report = {
        "schema_id": PAPER_OPERATION_GATE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "operation_gate_id": operation_gate_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "strategy_unit": strategy_unit,
        "sizing_decision": sizing_decision,
        "paper_dry_run_report": paper_report,
        "restart_recovery_report": restart_report,
        "replay_consistency_report": replay_report,
        "paper_shadow_separation_report": separation_report,
        "paper_shadow_evidence_accumulation_report": paper_shadow_evidence_report,
        "dashboard_panels": {},
        "operation_gate_status": "PASS" if not blockers else "BLOCKED",
        "stage_gate_status": "PASS_FOR_MVP3_OPERATIONAL_PAPER_ONLY" if not blockers else "BLOCKED",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "primary_blocker_code": primary_code,
        "blockers": blockers,
        "operation_gate_hash": "",
    }
    report["dashboard_panels"] = {
        "status": build_status_panel(report),
        "portfolio": build_portfolio_panel(report),
        "no_trade": build_no_trade_panel(report),
    }
    report["operation_gate_hash"] = operation_gate_hash(report)
    return report


def validate_paper_operation_gate_report(report: dict[str, Any]) -> PaperOperationGateValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "operation_gate_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "strategy_unit",
        "sizing_decision",
        "paper_dry_run_report",
        "restart_recovery_report",
        "replay_consistency_report",
        "paper_shadow_separation_report",
        "paper_shadow_evidence_accumulation_report",
        "dashboard_panels",
        "operation_gate_status",
        "stage_gate_status",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "operation_gate_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return PaperOperationGateValidationResult("FAIL", f"paper operation gate missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != PAPER_OPERATION_GATE_SCHEMA_ID:
        return PaperOperationGateValidationResult("FAIL", "paper operation gate schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("operation_gate_hash") != operation_gate_hash(report):
        return PaperOperationGateValidationResult("FAIL", "paper operation gate hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return PaperOperationGateValidationResult("BLOCKED", "paper operation gate scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("can_submit_order"):
        return PaperOperationGateValidationResult("BLOCKED", "paper operation gate attempted to create live/order permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("order_adapter_called"):
        return PaperOperationGateValidationResult("BLOCKED", "paper operation gate cannot call order adapter", "LIVE_FINAL_GUARD_FAILED")
    nested_checks = [
        (validate_strategy_unit(report["strategy_unit"]), "strategy_unit"),
        (validate_position_sizing_decision(report["sizing_decision"]), "sizing_decision"),
        (validate_upbit_paper_dry_run_report(report["paper_dry_run_report"]), "paper_dry_run"),
        (validate_restart_recovery_report(report["restart_recovery_report"]), "restart_recovery"),
        (validate_replay_consistency_report(report["replay_consistency_report"]), "replay_consistency"),
        (validate_paper_shadow_separation_report(report["paper_shadow_separation_report"]), "paper_shadow_separation"),
        (validate_paper_shadow_evidence_accumulation_report(report["paper_shadow_evidence_accumulation_report"]), "paper_shadow_evidence"),
    ]
    for result, label in nested_checks:
        if result.status != "PASS":
            if label == "paper_shadow_evidence" and result.status == "BLOCKED" and result.blocker_code in {
                "SAMPLE_INSUFFICIENT",
                "MEASUREMENT_MISSING",
                "EXECUTION_FEEDBACK_MISSING",
            }:
                evidence = report["paper_shadow_evidence_accumulation_report"]
                if (
                    evidence.get("scorecard_input_eligible") is False
                    and evidence.get("optimizer_ranking_action") == "BLOCK_RANKING"
                    and evidence.get("promotion_eligible") is False
                    and evidence.get("live_order_ready") is False
                    and evidence.get("live_order_allowed") is False
                    and evidence.get("can_live_trade") is False
                    and evidence.get("scale_up_allowed") is False
                ):
                    continue
            return PaperOperationGateValidationResult(result.status, f"{label}: {result.message}", result.blocker_code)
    panels = report.get("dashboard_panels", {})
    for panel in panels.values():
        if panel.get("order_controls_present") or panel.get("live_order_allowed") or panel.get("can_live_trade"):
            return PaperOperationGateValidationResult("BLOCKED", "dashboard panel attempted order controls or live permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("operation_gate_status") == "PASS" and report.get("blockers"):
        return PaperOperationGateValidationResult("BLOCKED", "paper operation gate PASS cannot carry blockers", report["blockers"][0].get("code", "UNKNOWN_BLOCKED"))
    if report.get("stage_gate_status") == "PASS_FOR_MVP3_OPERATIONAL_PAPER_ONLY" and report.get("live_order_ready"):
        return PaperOperationGateValidationResult("BLOCKED", "MVP-3 stage gate cannot create LIVE_READY", "LIVE_FINAL_GUARD_FAILED")
    return PaperOperationGateValidationResult("PASS", "operational Upbit paper gate is paper-only and evidence-backed", None)
