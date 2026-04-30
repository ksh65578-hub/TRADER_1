from __future__ import annotations

import hashlib
import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import PurePosixPath
from typing import Any

from trader1.core.ledger.restart_recovery import validate_restart_recovery_report
from trader1.runtime.health.stability_history import (
    DEFAULT_MIN_VALIDATED_SAMPLE_COUNT,
    DEFAULT_MIN_VALIDATED_SPAN_SECONDS,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import validate_upbit_paper_runtime_recovery_guard_report
from trader1.runtime.paper.upbit_public_rest_continuity_history import validate_upbit_public_rest_continuity_history_report
from trader1.runtime.reconciliation.reconciliation import validate_reconciliation_report


READ_ONLY_DASHBOARD_SCHEMA_ID = "trader1.read_only_dashboard_shell.v1"
REQUIRED_DISPLAY_SOURCE_FILENAMES = {"summary.json", "heartbeat.json", "startup_probe.json"}
OPTIONAL_DISPLAY_SOURCE_FILENAMES = {
    "shadow_observation_runtime_artifact_writer_report.json",
    "actual_runtime_harness_report.json",
    "shadow_observation_persistent_runtime_report.json",
    "runtime_orchestration_report.json",
    "upbit_paper_runtime_recovery_guard_report.json",
    "rest_continuity_history.json",
    "candidate_scorecard.json",
}
DISPLAY_SOURCE_FILENAMES = REQUIRED_DISPLAY_SOURCE_FILENAMES | OPTIONAL_DISPLAY_SOURCE_FILENAMES
RECONCILIATION_RECOVERY_SOURCES = {"summary.json", "reconciliation_report.json", "restart_recovery_report.json"}
ORDER_AFFECTING_FINAL_ACTIONS = {
    "ENTER_LONG",
    "ENTER_SHORT",
    "EXIT_POSITION",
    "REDUCE_POSITION",
    "CANCEL_ORDER",
    "HOLD_POSITION",
}
FORBIDDEN_DISPLAY_PHRASES = {
    "profit guaranteed",
    "automatic profit",
    "converged to profit",
    "self-optimizing live",
    "safe to scale automatically",
    "ready to size up",
}
FORBIDDEN_SOURCE_ROLES = {
    "execution_truth",
    "exchange_reconciliation_snapshot",
    "ledger",
    "intent_wal",
    "order_events",
    "fill_events",
    "balance_snapshots",
    "position_snapshots",
}
SAFE_FINAL_ACTIONS = {"NO_TRADE", "SAFE_MODE", "TRADE_DISABLED", "BLOCKED", "RECONCILE_REQUIRED"}
PORTFOLIO_CARD_IDS = (
    "cash",
    "equity",
    "locked_cash",
    "realized_pnl",
    "unrealized_pnl",
    "total_pnl",
    "positions",
    "entry_candidates",
    "return_pct",
)
SOURCE_FRESHNESS_MAX_AGE_SECONDS = 300
SOURCE_CLOCK_SKEW_ALLOWANCE_SECONDS = 60
DASHBOARD_AUTO_REFRESH_SECONDS = 10
ACTUAL_LONG_RUN_MIN_VALIDATED_SPAN_SECONDS = 86400
ACTUAL_LONG_RUN_MIN_ACTUAL_CYCLE_COUNT = 2880
OPERATION_STATUS_LEVELS = {"NORMAL", "WARNING", "ERROR"}
OPERATION_COLOR_TOKENS = {"green", "blue", "yellow", "red"}
POSITION_STATUS_VALUES = {"NONE", "OPEN", "STALE", "UNVERIFIED"}
RECENT_EVENT_TYPES = {"NO_TRADE", "ENTRY_REVIEW", "EXIT_REVIEW", "ERROR", "STATUS", "STALE_SOURCE"}
RECENT_EVENT_SEVERITIES = {"INFO", "WARNING", "ERROR"}
STABILITY_STATUSES = {"STABLE", "ATTENTION", "ERROR"}
STABILITY_METRIC_IDS = {
    "heartbeat_age",
    "source_freshness",
    "resource_health",
    "runtime_artifact_pressure",
    "event_latency",
    "queue_backlog",
    "rate_limit_pressure",
}
STABILITY_METRIC_STATUSES = {"PASS", "WARN", "FAIL", "STALE", "UNTESTED"}
LONG_RUN_SUMMARY_STATUSES = {"RUNNING_NOW", "DISPLAY_HISTORY_STABLE", "VALIDATED_STABLE", "ATTENTION", "STALE", "ERROR"}
LONG_RUN_SUMMARY_SOURCES = {"heartbeat.json", "stability_history.json"}
SHADOW_RUNTIME_HARNESS_STATUSES = {"NOT_LOADED", "SHORT_WINDOW_EXECUTED", "BLOCKED", "STALE"}
SHADOW_RUNTIME_HARNESS_SOURCES = {"NOT_LOADED", "actual_runtime_harness_report.json"}
SHADOW_RUNTIME_HARNESS_EVIDENCE_STATUSES = {"NOT_LOADED", "BLOCKED_LONG_RUN_EVIDENCE_MISSING"}
SHADOW_PERSISTENT_RUNTIME_STATUSES = {"NOT_LOADED", "STUB_ONLY", "BLOCKED", "STALE"}
SHADOW_PERSISTENT_RUNTIME_SOURCES = {"NOT_LOADED", "shadow_observation_persistent_runtime_report.json"}
SHADOW_PERSISTENT_RUNTIME_DURATION_SOURCES = {"NOT_LOADED", "STUB_ESTIMATE_ONLY"}
SHADOW_PERSISTENT_RUNTIME_DURATION_ROLES = {"NOT_LONG_RUN_EVIDENCE"}
SHADOW_RUNTIME_ORCHESTRATION_STATUSES = {"NOT_LOADED", "BOUNDARY_VERIFIED", "BLOCKED", "STALE"}
SHADOW_RUNTIME_ORCHESTRATION_SOURCES = {"NOT_LOADED", "runtime_orchestration_report.json"}
PAPER_RUNTIME_RECOVERY_GUARD_STATUSES = {"NOT_LOADED", "PASS", "BLOCKED", "STALE", "INVALID"}
PAPER_RUNTIME_RECOVERY_GUARD_SOURCES = {"NOT_LOADED", "upbit_paper_runtime_recovery_guard_report.json"}
MARKET_DATA_CONTINUITY_STATUSES = {"NOT_LOADED", "PASS", "BLOCKED", "STALE", "INVALID"}
MARKET_DATA_CONTINUITY_SOURCES = {"NOT_LOADED", "rest_continuity_history.json"}
MARKET_DATA_CONTINUITY_EVIDENCE_ROLES = {"PAPER_DATA_CONTINUITY_HISTORY_ONLY_NOT_LIVE_READY"}
RUNTIME_EVIDENCE_BOUNDARY_STATUSES = {
    "ACTUAL_LONG_RUN_MISSING",
    "ACTUAL_LONG_RUN_COLLECTING",
    "ACTUAL_LONG_RUN_VALIDATED",
    "BLOCKED",
    "STALE",
}
RUNTIME_EVIDENCE_ACTUAL_STATUSES = {"MISSING", "COLLECTING", "VALIDATED_STABLE", "BLOCKED", "STALE"}
RUNTIME_EVIDENCE_REQUIREMENT_IDS = (
    "PERSISTENT_RUNTIME_SOURCE",
    "SHORT_WINDOW_HARNESS_SOURCE",
    "RUNTIME_ORCHESTRATION_SOURCE_PAIRING",
    "ACTUAL_RUNTIME_DURATION",
    "ACTUAL_CYCLE_COUNT",
    "EVIDENCE_WINDOW_COUNT",
    "HEARTBEAT_FRESHNESS_HISTORY",
    "RECOVERY_AND_PARTIAL_WRITE_CLEAN",
)
RUNTIME_EVIDENCE_REQUIREMENT_STATUSES = {"MISSING", "COLLECTING", "PASS", "BLOCKED", "STALE"}
RECONCILIATION_RECOVERY_STATUSES = {"NOT_LOADED", "PASS", "RECONCILE_REQUIRED", "BLOCKED", "INVALID"}
RECONCILIATION_RECOVERY_REPORT_STATUSES = {
    "NOT_LOADED",
    "PASS",
    "FAIL",
    "STALE",
    "MISMATCH",
    "UNKNOWN",
    "BLOCKED",
    "INVALID",
}
RECONCILIATION_RECOVERY_VALIDATION_STATUSES = {"PASS", "FAIL", "BLOCKED", "UNTESTED"}
RECONCILIATION_RECOVERY_LEDGER_STATES = {"NOT_LOADED", "PAPER_LEDGER_MATCHED", "RECONCILE_REQUIRED", "INVALID"}
RECONCILIATION_RECOVERY_WRITER_STATES = {"NOT_LOADED", "RECOVERED", "RECONCILE_REQUIRED", "INVALID"}
OPERATOR_ACTION_STATUSES = {"PAPER_MONITORING", "PAPER_REVIEW_READY", "REFRESH_REQUIRED", "ACTION_REQUIRED", "BLOCKED"}
OPERATOR_ACTION_KINDS = {"CONTINUE_PAPER", "REFRESH_DASHBOARD", "REVIEW_PAPER_EVIDENCE", "RESOLVE_BLOCKER", "STOP_AND_INSPECT"}
OPERATOR_WORKFLOW_STEPS = {"RUN_PAPER", "INSPECT_DASHBOARD", "COLLECT_EVIDENCE", "LIVE_REVIEW_BLOCKED"}
OPERATOR_WORKFLOW_STATUSES = {"COLLECTING_EVIDENCE", "PAPER_REVIEW", "REFRESH_REQUIRED", "ACTION_REQUIRED", "BLOCKED"}
OPERATOR_WORKFLOW_STEP_STATUSES = {"DONE", "CURRENT", "WAITING", "BLOCKED"}
PROFITABILITY_MATURITY_STATUSES = {"COLLECTING", "SCORECARD_INPUT_READY", "BLOCKED", "STALE"}
PROFITABILITY_MATURITY_SOURCES = {"summary.json"}
PROFITABILITY_MATURITY_EVIDENCE_SOURCES = {
    "NOT_LOADED",
    "paper_operation_gate_report",
    "profitability_evidence_maturity_rollup.json",
    "candidate_scorecard.json",
}
PROFITABILITY_ACTUAL_RUNTIME_SOURCE_STATUSES = {"MISSING", "STUB_ONLY", "VALIDATED_NON_LIVE_RUNTIME"}
PROFITABILITY_RANKING_ACTIONS = {"ALLOW_RANKING", "BLOCK_RANKING"}
PROFITABILITY_PROGRESS_STATUSES = {"NOT_STARTED", "IN_PROGRESS", "READY", "BLOCKED", "STALE"}
PROFITABILITY_SCORECARD_SCOPES = {
    "PAPER_EVIDENCE_COLLECTION_ONLY",
    "PAPER_SCORECARD_INPUT_ONLY",
    "BLOCKED_DISPLAY_ONLY",
    "STALE_DISPLAY_ONLY",
}
PROFITABILITY_LIVE_READINESS_STATUSES = {"NOT_LIVE_READY"}
PROFITABILITY_EVIDENCE_CHECK_IDS = (
    "PAPER_SAMPLES",
    "SHADOW_SAMPLES",
    "COST_EVIDENCE",
    "ENTRY_REASON",
    "NO_TRADE_REASON",
)
PROFITABILITY_EVIDENCE_CHECK_STATUSES = {"PASS", "MISSING", "BLOCKED", "STALE"}
PROFITABILITY_MATURITY_COMPONENT_IDS = (
    "strategy_entry_exit_no_trade",
    "symbol_selection_regime",
    "vwap_trend_breakout",
    "risk_sizing_exposure",
    "execution_slippage_fee_impact",
    "optimizer_objective_net_ev_after_cost",
    "overfit_oos_walk_forward",
    "convergence_memory_failure_learning",
    "paper_shadow_evidence_accumulation",
    "dashboard_operator_profitability_visibility",
)
PROFITABILITY_MATURITY_NEXT_EVIDENCE = {
    "strategy_entry_exit_no_trade": "Collect PAPER entry, exit, and no-trade reason records from the operational cycle.",
    "symbol_selection_regime": "Collect scoped liquidity, volatility, spread, depth, and regime-fit evidence for each reviewed symbol.",
    "vwap_trend_breakout": "Collect regime-labeled VWAP reversion, trend pullback, and breakout/retest outcome samples.",
    "risk_sizing_exposure": "Review paper_exposure_quality_report with exposure, concentration, drawdown, idempotency, and recovery checks.",
    "execution_slippage_fee_impact": "Collect expected-vs-realized fee, spread, slippage, impact, and latency feedback.",
    "optimizer_objective_net_ev_after_cost": "Validate optimizer ranking against net EV after all costs, not raw PnL.",
    "overfit_oos_walk_forward": "Add OOS, walk-forward, bootstrap, and concentration diagnostics before ranking claims.",
    "convergence_memory_failure_learning": "Append failure analysis and repeated root-cause memory for blocked or retired candidates.",
    "paper_shadow_evidence_accumulation": "Keep collecting scoped PAPER and SHADOW samples until minimum sample counts and hashes pass.",
    "dashboard_operator_profitability_visibility": "Keep dashboard wording display-only and verify blockers remain visible before review.",
}
PROFITABILITY_MATURITY_COMPONENT_STATUSES = {
    "PAPER_SCORECARD_EVIDENCE_PASS",
    "PAPER_SCORECARD_INPUT_ONLY",
    "PARTIAL_PATCHED",
    "EVIDENCE_MISSING",
    "RECORDED_GAP",
    "BLOCKED_LONG_RUN_EVIDENCE",
    "BLOCKED",
    "STALE",
}
PROFITABILITY_MATURITY_GAP_STATUSES = {
    "OPEN_HIGH",
    "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
    "BLOCKED",
    "STALE",
}
PROFITABILITY_MATURITY_PRIORITIES = {"HIGH", "MEDIUM"}
CANDIDATE_SCORECARD_SOURCE_FILENAMES = {"NOT_LOADED", "candidate_scorecard.json"}
CANDIDATE_SCORECARD_STATUSES = {"NOT_LOADED", "PAPER_RANKING_BLOCKED", "PAPER_RANKING_REVIEW_ONLY", "BLOCKED", "STALE"}
RISK_EXPOSURE_STATUSES = {"LOW_RISK", "ATTENTION", "BLOCKED", "STALE", "UNVERIFIED"}
RISK_EXPOSURE_SOURCES = {"summary.json"}
RISK_EXPOSURE_NOTIONAL_DATA_STATUSES = {"COMPLETE", "PARTIAL", "UNVERIFIED"}
RISK_EXPOSURE_DRAWDOWN_DATA_STATUSES = {"VERIFIED", "UNVERIFIED"}
RISK_REVIEW_SCOPES = {"PAPER_DISPLAY_ONLY"}
PAPER_EXPOSURE_QUALITY_STATUSES = {
    "PASS_PAPER_ONLY",
    "INSUFFICIENT_EVIDENCE",
    "BLOCKED_EXPOSURE_BREACH",
    "BLOCKED_DRAWDOWN_BREACH",
    "BLOCKED_RECOVERY_REVIEW",
    "UNAVAILABLE",
}
PAPER_EXPOSURE_QUALITY_SOURCES = {"NOT_LOADED", "paper_exposure_quality_report.json"}
PAPER_EXPOSURE_QUALITY_RECOMMENDATIONS = {"KEEP_PAPER", "NO_SCALE_UP", "SCALE_DOWN_RECOMMENDED"}
EXECUTION_FEEDBACK_STATUSES = {"COLLECTING", "READY_FOR_PAPER_RANKING_REVIEW", "BLOCKED", "STALE"}
EXECUTION_FEEDBACK_SOURCES = {"summary.json"}
EXECUTION_FEEDBACK_RANKING_ACTIONS = {"ALLOW_RANKING", "PENALIZE_RANKING", "BLOCK_RANKING"}
EXECUTION_FEEDBACK_REVIEW_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "UNTESTED", "STALE"}
CONVERGENCE_ASSESSMENT_STATUSES = {
    "UNTESTED",
    "COLLECTING",
    "LOCALLY_IMPROVING",
    "ROBUSTLY_IMPROVING",
    "BLOCKED",
    "STALE",
}
CONVERGENCE_CLAIMS = {
    "NO_CLAIM",
    "LOCALLY_IMPROVING",
    "ROBUSTLY_IMPROVING",
    "WRITER_INPUT_ELIGIBLE",
    "BLOCKED",
}
CONVERGENCE_SCORE_BANDS = {
    "UNKNOWN",
    "NEGATIVE",
    "WEAK",
    "LOCAL_IMPROVING",
    "ROBUST_IMPROVING",
    "BLOCKED",
}
CONVERGENCE_DRIFT_STATUSES = {
    "NOT_EVALUATED",
    "NO_DRIFT",
    "DRIFT_SUSPECTED",
    "DRIFT_DETECTED",
    "BLOCKED",
}
EXPLORATION_POLICY_STATUSES = {
    "UNTESTED",
    "ACTIVE_ANALYSIS_ONLY",
    "PAPER_RANKING_REVIEW_ELIGIBLE",
    "BLOCKED",
    "STALE",
}
EXPLORATION_POLICY_CONTROLLER_STATES = {
    "EXPLORING",
    "BALANCED",
    "EXPLOITING_PAPER_ONLY",
    "BLOCKED",
}
EXPLORATION_POLICY_TRANSITIONS = {
    "KEEP_EXPLORING",
    "LIMITED_EXPLOITATION_REVIEW",
    "SCALE_DOWN_ONLY",
    "BLOCK_TRANSITION",
}
EXPLORATION_POLICY_RECOMMENDATION_SCOPES = {
    "ANALYSIS_ONLY",
    "PAPER_RANKING_REVIEW_ONLY",
    "RISK_REDUCTION_ONLY",
    "BLOCKED",
}
EXPLORATION_POLICY_OBJECTIVE_BASES = {
    "NET_EV_AFTER_COST",
    "BLOCKED_NO_VALID_OBJECTIVE",
}
EXPLORATION_POLICY_BUDGET_STATUSES = {"PASS", "WARN", "BLOCKED"}
PARAMETER_NARROWING_STATUSES = {
    "UNTESTED",
    "ACTIVE_ANALYSIS_ONLY",
    "PAPER_PARAMETER_REVIEW_ELIGIBLE",
    "BLOCKED",
    "STALE",
}
PARAMETER_NARROWING_RECOMMENDATION_SCOPES = {
    "ANALYSIS_ONLY",
    "PAPER_PARAMETER_REVIEW_ONLY",
    "RISK_REDUCTION_ONLY",
    "BLOCKED",
}
PARAMETER_NARROWING_WRITE_SCOPES = {"PROPOSAL_ONLY", "BLOCKED"}
PARAMETER_NARROWING_OBJECTIVE_BASES = {
    "NET_EV_AFTER_COST",
    "BLOCKED_NO_VALID_OBJECTIVE",
}
CONVERGENCE_ASSESSMENT_DEPENDENCY_FIELDS = (
    "convergence_objective_profile_validator_status",
    "optimizer_memory_state_validator_status",
    "strategy_performance_memory_validator_status",
    "overfit_diagnostic_validator_status",
    "execution_feedback_loop_validator_status",
    "failure_analysis_validator_status",
    "paper_shadow_evidence_accumulation_validator_status",
    "market_regime_adaptation_validator_status",
    "model_drift_validator_status",
    "coverage_index_validator_status",
)
EXPLORATION_POLICY_DEPENDENCY_FIELDS = (
    "ranking_stability_validator_status",
    "optimizer_resource_budget_validator_status",
    "overfit_diagnostic_validator_status",
    "convergence_assessment_validator_status",
    "exploration_resource_validator_status",
    "model_drift_validator_status",
)
PARAMETER_NARROWING_DEPENDENCY_FIELDS = (
    "candidate_scorecard_validator_status",
    "optimizer_run_report_validator_status",
    "optimizer_recommendation_validator_status",
    "exploration_exploitation_policy_validator_status",
    "overfit_diagnostic_validator_status",
    "execution_feedback_loop_validator_status",
    "live_final_guard_validator_status",
)
EXPOSURE_ATTENTION_PCT = Decimal("20")
EXPOSURE_BLOCK_PCT = Decimal("50")
DRAWDOWN_ATTENTION_PCT = Decimal("2")
DRAWDOWN_BLOCK_PCT = Decimal("5")


@dataclass(frozen=True)
class DashboardValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def dashboard_shell_hash(shell: dict[str, Any]) -> str:
    data = dict(shell)
    data.pop("dashboard_hash", None)
    return sha256_json(data)


def _source_artifact(artifact_id: str, path: str, loaded: bool, freshness_status: str) -> dict[str, Any]:
    filename = PurePosixPath(path.replace("\\", "/")).name
    return {
        "artifact_id": artifact_id,
        "path": path.replace("\\", "/"),
        "filename": filename,
        "truth_role": "dashboard_serving_truth",
        "loaded": loaded,
        "freshness_status": freshness_status,
    }


def _panel(title: str, status: str, source: str, message: str | None) -> dict[str, Any]:
    return {
        "title": title,
        "status": status,
        "source": source,
        "message": message,
    }


def _portfolio_card(card_id: str, label: str, value_display: str, detail: str) -> dict[str, Any]:
    return {
        "card_id": card_id,
        "label": label,
        "value_display": value_display,
        "detail": detail,
        "freshness_status": "UNTESTED",
    }


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


def _freshness_from_generated_at(payload: dict[str, Any] | None) -> str:
    if not isinstance(payload, dict):
        return "STALE"
    generated_at = _parse_utc(payload.get("generated_at_utc"))
    if generated_at is None:
        return "STALE"
    age_seconds = (datetime.now(timezone.utc) - generated_at).total_seconds()
    if age_seconds < -SOURCE_CLOCK_SKEW_ALLOWANCE_SECONDS:
        return "STALE"
    if age_seconds > SOURCE_FRESHNESS_MAX_AGE_SECONDS:
        return "STALE"
    return "PASS"


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _currency_for_scope(exchange: str, market_type: str) -> str:
    if exchange == "UPBIT" and market_type == "KRW_SPOT":
        return "KRW"
    if exchange == "BINANCE" and market_type == "SPOT":
        return "USDT"
    return "PAPER"


def _format_money(value: Any, currency: str) -> str:
    amount = _decimal(value)
    if amount is None:
        return "UNVERIFIED"
    if currency == "KRW":
        return f"{amount:,.0f} KRW"
    return f"{amount:,.2f} {currency}"


def _format_signed_money(value: Any, currency: str) -> str:
    amount = _decimal(value)
    if amount is None:
        return "UNVERIFIED"
    sign = "+" if amount >= 0 else "-"
    absolute = abs(amount)
    if currency == "KRW":
        return f"{sign}{absolute:,.0f} KRW"
    return f"{sign}{absolute:,.2f} {currency}"


def _format_total_pnl(realized: Any, unrealized: Any, currency: str) -> str:
    realized_value = _decimal(realized)
    unrealized_value = _decimal(unrealized)
    if realized_value is None or unrealized_value is None:
        return "UNVERIFIED"
    return _format_signed_money(realized_value + unrealized_value, currency)


def _format_return(realized: Any, unrealized: Any, equity: Any) -> str:
    realized_value = _decimal(realized) or Decimal("0")
    unrealized_value = _decimal(unrealized) or Decimal("0")
    equity_value = _decimal(equity)
    if equity_value is None:
        return "UNVERIFIED"
    starting_equity = equity_value - realized_value - unrealized_value
    if starting_equity <= 0:
        return "UNVERIFIED"
    return_pct = ((realized_value + unrealized_value) / starting_equity) * Decimal("100")
    return f"{return_pct:.2f}%"


def _candidate_symbols_from_summary(summary: dict[str, Any]) -> list[str]:
    symbols: list[str] = []
    for source_key in ("entry_candidates", "candidate_symbols", "strategy_candidates"):
        raw_items = summary.get(source_key, [])
        if not isinstance(raw_items, list):
            continue
        for item in raw_items:
            if isinstance(item, dict):
                symbol = item.get("symbol") or item.get("instrument") or item.get("market") or item.get("candidate_id")
            else:
                symbol = item
            if symbol:
                symbols.append(str(symbol))
    deduped: list[str] = []
    for symbol in symbols:
        if symbol not in deduped:
            deduped.append(symbol)
    return deduped


def _format_pct(value: Decimal | None) -> str:
    if value is None:
        return "UNVERIFIED"
    return f"{value:.2f}%"


def _format_bps(value: Any) -> str:
    amount = _decimal(value)
    if amount is None:
        return "UNVERIFIED"
    return f"{amount:.2f} bps"


def _optimizer_feedback_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("feedback_hash", None)
    return sha256_json(payload)


def _paper_exposure_quality_projection(
    *,
    report: dict[str, Any] | None,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
) -> dict[str, Any]:
    base = {
        "paper_exposure_quality_status": "UNAVAILABLE",
        "paper_exposure_quality_source": "NOT_LOADED",
        "paper_exposure_quality_message": "No paper exposure quality report is loaded; scale-up remains blocked.",
        "paper_exposure_quality_next_required_evidence": (
            "Generate a scoped paper_exposure_quality_report from the PAPER ledger before treating risk as low."
        ),
        "paper_exposure_quality_recommendation": "NO_SCALE_UP",
        "paper_exposure_quality_sample_display": "0/0",
        "paper_exposure_quality_report_id": None,
        "paper_exposure_quality_blocker_code": "HARD_TRUTH_MISSING",
    }
    if not isinstance(report, dict):
        return base

    paper_samples = report.get("paper_sample_count", 0)
    min_samples = report.get("min_required_sample_count", 0)
    sample_display = f"{paper_samples}/{min_samples}" if isinstance(paper_samples, int) and isinstance(min_samples, int) else "UNVERIFIED"
    projection = {
        **base,
        "paper_exposure_quality_source": "paper_exposure_quality_report.json",
        "paper_exposure_quality_report_id": report.get("exposure_report_id"),
        "paper_exposure_quality_sample_display": sample_display,
        "paper_exposure_quality_recommendation": report.get("recommendation", "NO_SCALE_UP")
        if report.get("recommendation") in PAPER_EXPOSURE_QUALITY_RECOMMENDATIONS
        else "NO_SCALE_UP",
        "paper_exposure_quality_next_required_evidence": report.get("next_operator_action")
        if isinstance(report.get("next_operator_action"), str) and report.get("next_operator_action")
        else "Review the scoped paper_exposure_quality_report before continuing strategy risk review.",
        "paper_exposure_quality_blocker_code": report.get("primary_blocker_code") or "SCALE_UP_NOT_ELIGIBLE",
        "paper_exposure_quality_message": report.get("operator_warning")
        if isinstance(report.get("operator_warning"), str) and report.get("operator_warning")
        else "Paper exposure quality report is loaded; live and scale-up remain blocked.",
    }

    forbidden_runtime_permission = any(
        report.get(field) is True
        for field in (
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
            "promotion_eligible",
            "order_adapter_called",
            "exchange_account_call_allowed",
            "live_config_mutation_allowed",
        )
    )
    if forbidden_runtime_permission:
        return {
            **projection,
            "paper_exposure_quality_status": "BLOCKED_RECOVERY_REVIEW",
            "paper_exposure_quality_recommendation": "NO_SCALE_UP",
            "paper_exposure_quality_blocker_code": "LIVE_FINAL_GUARD_FAILED",
            "paper_exposure_quality_message": "Paper exposure quality report attempted live, exchange, promotion, or scale permission; dashboard blocked it.",
            "paper_exposure_quality_next_required_evidence": (
                "Inspect and repair the paper exposure quality report; it attempted forbidden live or scale permission."
            ),
        }

    if (
        report.get("exchange") != exchange
        or report.get("market_type") != market_type
        or report.get("mode") != mode
        or report.get("session_id") != session_id
        or mode != "PAPER"
    ):
        return {
            **projection,
            "paper_exposure_quality_status": "BLOCKED_RECOVERY_REVIEW",
            "paper_exposure_quality_recommendation": "NO_SCALE_UP",
            "paper_exposure_quality_blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "paper_exposure_quality_message": "Paper exposure quality report scope does not match this dashboard; cross-scope risk display is blocked.",
            "paper_exposure_quality_next_required_evidence": (
                "Regenerate the paper exposure quality report for this exact exchange, market, mode, and session."
            ),
        }

    quality_status = report.get("risk_quality_status")
    if quality_status not in PAPER_EXPOSURE_QUALITY_STATUSES or quality_status == "UNAVAILABLE":
        return {
            **projection,
            "paper_exposure_quality_status": "BLOCKED_RECOVERY_REVIEW",
            "paper_exposure_quality_recommendation": "NO_SCALE_UP",
            "paper_exposure_quality_blocker_code": "SCHEMA_IDENTITY_MISMATCH",
            "paper_exposure_quality_message": "Paper exposure quality report has an unknown quality status; review is blocked.",
            "paper_exposure_quality_next_required_evidence": (
                "Regenerate the report with a valid paper_exposure_quality_report schema and validator result."
            ),
        }
    return {**projection, "paper_exposure_quality_status": quality_status}


def _verified_paper_portfolio_snapshot(exchange: str, market_type: str, summary: dict[str, Any]) -> dict[str, Any] | None:
    portfolio = summary.get("portfolio") if isinstance(summary, dict) else None
    if not isinstance(portfolio, dict):
        return None
    if portfolio.get("source") != "LEDGER" or portfolio.get("freshness_status") != "PASS":
        return None
    if any(portfolio.get(key) is None for key in ("equity", "cash_available", "locked_balance", "realized_pnl", "unrealized_pnl")):
        return None
    currency = _currency_for_scope(exchange, market_type)
    positions = summary.get("positions", [])
    position_count = len(positions) if isinstance(positions, list) else 0
    candidate_symbols = _candidate_symbols_from_summary(summary)
    candidate_preview = ", ".join(candidate_symbols[:4])
    if len(candidate_symbols) > 4:
        candidate_preview += f" +{len(candidate_symbols) - 4} more"
    realized_pnl = portfolio.get("realized_pnl")
    unrealized_pnl = portfolio.get("unrealized_pnl")
    snapshot = {
        "title": "Portfolio Snapshot",
        "status": "VERIFIED",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "source_runtime_cycle_id": portfolio.get("source_runtime_cycle_id"),
        "source_paper_ledger_head_hash": portfolio.get("source_paper_ledger_head_hash"),
        "source_snapshot_age_seconds": portfolio.get("source_snapshot_age_seconds"),
        "source_snapshot_stale_after_seconds": portfolio.get("source_snapshot_stale_after_seconds"),
        "source_snapshot_freshness_message": portfolio.get("source_snapshot_freshness_message"),
        "cash": _portfolio_card(
            "cash",
            "Cash",
            _format_money(portfolio["cash_available"], currency),
            "Simulated PAPER ledger, not exchange balance",
        ),
        "equity": _portfolio_card(
            "equity",
            "Equity",
            _format_money(portfolio["equity"], currency),
            "Simulated PAPER ledger, not exchange balance",
        ),
        "locked_cash": _portfolio_card(
            "locked_cash",
            "Locked Cash",
            _format_money(portfolio["locked_balance"], currency),
            "Simulated PAPER funds reserved by open orders",
        ),
        "realized_pnl": _portfolio_card(
            "realized_pnl",
            "Realized PnL",
            _format_signed_money(realized_pnl, currency),
            "Closed PAPER trade result from ledger summary",
        ),
        "unrealized_pnl": _portfolio_card(
            "unrealized_pnl",
            "Unrealized PnL",
            _format_signed_money(unrealized_pnl, currency),
            "Open PAPER position mark-to-market estimate",
        ),
        "total_pnl": _portfolio_card(
            "total_pnl",
            "Total PnL",
            _format_total_pnl(realized_pnl, unrealized_pnl, currency),
            "Realized plus unrealized PAPER PnL",
        ),
        "positions": _portfolio_card(
            "positions",
            "Open Positions",
            str(position_count),
            "Open PAPER positions from summary",
        ),
        "entry_candidates": _portfolio_card(
            "entry_candidates",
            "Entry Candidates",
            str(len(candidate_symbols)),
            f"Candidates: {candidate_preview}" if candidate_preview else "No entry candidates loaded from summary",
        ),
        "return_pct": _portfolio_card(
            "return_pct",
            "Return",
            _format_return(realized_pnl, unrealized_pnl, portfolio.get("equity")),
            "PAPER return from realized and unrealized PnL",
        ),
        "blocking_reason": "HARD_TRUTH_MISSING",
        "next_action": "PAPER portfolio is simulated; inspect orders and blockers before any live review",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    for card_id in PORTFOLIO_CARD_IDS:
        snapshot[card_id]["freshness_status"] = "PASS"
    return snapshot


def _stale_portfolio_snapshot() -> dict[str, Any]:
    snapshot = {
        "title": "Portfolio Snapshot",
        "status": "STALE",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "source_runtime_cycle_id": None,
        "source_paper_ledger_head_hash": None,
        "source_snapshot_age_seconds": None,
        "source_snapshot_stale_after_seconds": None,
        "source_snapshot_freshness_message": "Stale summary; rerun PAPER launcher",
        "cash": _portfolio_card("cash", "Cash", "UNVERIFIED", "Stale summary; rerun PAPER launcher"),
        "equity": _portfolio_card("equity", "Equity", "UNVERIFIED", "Stale summary; rerun PAPER launcher"),
        "locked_cash": _portfolio_card("locked_cash", "Locked Cash", "UNVERIFIED", "Stale summary; rerun PAPER launcher"),
        "realized_pnl": _portfolio_card("realized_pnl", "Realized PnL", "UNVERIFIED", "Stale summary; rerun PAPER launcher"),
        "unrealized_pnl": _portfolio_card("unrealized_pnl", "Unrealized PnL", "UNVERIFIED", "Stale summary; rerun PAPER launcher"),
        "total_pnl": _portfolio_card("total_pnl", "Total PnL", "UNVERIFIED", "Stale summary; rerun PAPER launcher"),
        "positions": _portfolio_card("positions", "Open Positions", "UNVERIFIED", "Stale summary; rerun PAPER launcher"),
        "entry_candidates": _portfolio_card("entry_candidates", "Entry Candidates", "UNVERIFIED", "Stale summary; rerun PAPER launcher"),
        "return_pct": _portfolio_card("return_pct", "Return", "UNVERIFIED", "Stale summary; rerun PAPER launcher"),
        "blocking_reason": "LATENCY_TTL_EXPIRED",
        "next_action": "Rerun PAPER to refresh dashboard portfolio values before review",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    for card_id in PORTFOLIO_CARD_IDS:
        snapshot[card_id]["freshness_status"] = "STALE"
    return snapshot


def _portfolio_snapshot(exchange: str, market_type: str, mode: str, summary: dict[str, Any] | None, summary_freshness: str) -> dict[str, Any]:
    if summary is not None and summary_freshness != "PASS":
        return _stale_portfolio_snapshot()
    if mode == "PAPER" and isinstance(summary, dict):
        verified = _verified_paper_portfolio_snapshot(exchange, market_type, summary)
        if verified is not None:
            return verified
    return {
        "title": "Portfolio Snapshot",
        "status": "UNVERIFIED",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "source_runtime_cycle_id": None,
        "source_paper_ledger_head_hash": None,
        "source_snapshot_age_seconds": None,
        "source_snapshot_stale_after_seconds": None,
        "source_snapshot_freshness_message": "No verified paper portfolio snapshot loaded",
        "cash": _portfolio_card("cash", "Cash", "UNVERIFIED", "No verified cash source loaded"),
        "equity": _portfolio_card("equity", "Equity", "UNVERIFIED", "No verified equity source loaded"),
        "locked_cash": _portfolio_card("locked_cash", "Locked Cash", "UNVERIFIED", "No verified locked-cash source loaded"),
        "realized_pnl": _portfolio_card("realized_pnl", "Realized PnL", "UNVERIFIED", "No verified realized PnL source loaded"),
        "unrealized_pnl": _portfolio_card("unrealized_pnl", "Unrealized PnL", "UNVERIFIED", "No verified unrealized PnL source loaded"),
        "total_pnl": _portfolio_card("total_pnl", "Total PnL", "UNVERIFIED", "No verified total PnL source loaded"),
        "positions": _portfolio_card("positions", "Open Positions", "UNVERIFIED", "No verified position source loaded"),
        "entry_candidates": _portfolio_card("entry_candidates", "Entry Candidates", "UNVERIFIED", "No verified candidate source loaded"),
        "return_pct": _portfolio_card("return_pct", "Return", "UNVERIFIED", "No verified return source loaded"),
        "blocking_reason": "HARD_TRUTH_MISSING",
        "next_action": "Run PAPER with a verified paper portfolio ledger"
        if mode == "PAPER"
        else "Provide read-only account snapshot evidence before portfolio values can be trusted",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _context_message(items: Any, fallback: str) -> str:
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                for key in ("reason", "message", "no_trade_reason", "entry_reason", "exit_reason", "detail"):
                    value = item.get(key)
                    if value:
                        return str(value)
            elif item:
                return str(item)
    return fallback


def _position_display_value(position: dict[str, Any], *keys: str, fallback: str = "UNKNOWN") -> str:
    for key in keys:
        value = position.get(key)
        if value is not None and value != "":
            return str(value)
    return fallback


def _position_row(position: dict[str, Any]) -> dict[str, str]:
    return {
        "symbol": _position_display_value(position, "symbol", "instrument"),
        "side": _position_display_value(position, "side", "direction"),
        "quantity": _position_display_value(position, "quantity", "qty", "size"),
        "avg_price": _position_display_value(position, "average_entry_price", "avg_price", "entry_price"),
        "mark_price": _position_display_value(position, "mark_price", "last_price"),
        "market_value": _position_display_value(position, "market_value", "position_market_value", "notional"),
        "cost_basis": _position_display_value(position, "cost_basis", "cost"),
        "unrealized_pnl": _position_display_value(position, "unrealized_pnl", "pnl"),
    }


def _position_snapshot(summary: dict[str, Any] | None, summary_freshness: str) -> dict[str, Any]:
    positions = summary.get("positions", []) if isinstance(summary, dict) else []
    if summary is not None and summary_freshness != "PASS":
        return {
            "title": "Open PAPER Positions",
            "status": "STALE",
            "truth_role": "dashboard_serving_truth",
            "source": "summary.json",
            "open_position_count": 0,
            "rows": [],
            "empty_message": "Position detail hidden because summary is stale; rerun PAPER.",
            "display_only": True,
            "dashboard_truth_only": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    if not isinstance(positions, list):
        rows: list[dict[str, str]] = []
        status = "UNVERIFIED"
        count = 0
    else:
        rows = [_position_row(position) for position in positions[:20] if isinstance(position, dict)]
        count = len(positions)
        status = "NONE" if count == 0 else "OPEN" if rows else "UNVERIFIED"
    return {
        "title": "Open PAPER Positions",
        "status": status,
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "open_position_count": count,
        "rows": rows,
        "empty_message": "No open PAPER positions",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _position_notional(position: dict[str, Any]) -> Decimal | None:
    quantity = _decimal(position.get("quantity") or position.get("qty") or position.get("size"))
    price = _decimal(
        position.get("mark_price")
        or position.get("last_price")
        or position.get("average_entry_price")
        or position.get("avg_price")
        or position.get("entry_price")
    )
    if quantity is None or price is None or quantity < 0 or price < 0:
        return None
    return abs(quantity * price)


def _risk_exposure_snapshot(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    summary: dict[str, Any] | None,
    summary_freshness: str,
    portfolio_snapshot: dict[str, Any],
    primary_blocker: str | None,
    paper_exposure_quality_report: dict[str, Any] | None,
) -> dict[str, Any]:
    currency = _currency_for_scope(exchange, market_type)
    quality = _paper_exposure_quality_projection(
        report=paper_exposure_quality_report,
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
    )
    base = {
        "title": "Risk Exposure",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "freshness_status": summary_freshness,
        "equity_display": "UNVERIFIED",
        "exposure_notional_display": "UNVERIFIED",
        "exposure_pct_display": "UNVERIFIED",
        "drawdown_pct_display": "UNVERIFIED",
        "exposure_review_cap_pct_display": f"{EXPOSURE_ATTENTION_PCT:.2f}% attention / {EXPOSURE_BLOCK_PCT:.2f}% block",
        "drawdown_review_cap_pct_display": f"{DRAWDOWN_ATTENTION_PCT:.2f}% attention / {DRAWDOWN_BLOCK_PCT:.2f}% block",
        "open_position_count": 0,
        "risk_review_scope": "PAPER_DISPLAY_ONLY",
        "exposure_data_status": "UNVERIFIED",
        "drawdown_data_status": "UNVERIFIED",
        **quality,
        "scale_up_blocker_code": "SCALE_UP_NOT_ELIGIBLE",
        "primary_blocker_code": primary_blocker or "HARD_TRUTH_MISSING",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    if summary is not None and summary_freshness != "PASS":
        return {
            **base,
            "status": "STALE",
            "severity": "WARNING",
            "color_token": "yellow",
            "primary_blocker_code": "LATENCY_TTL_EXPIRED",
            "primary_blocker_message": "Risk exposure display is stale because summary.json is stale.",
            "next_action": "Rerun PAPER before trusting exposure or drawdown values.",
        }
    if mode != "PAPER" or portfolio_snapshot.get("status") != "VERIFIED" or not isinstance(summary, dict):
        return {
            **base,
            "status": "UNVERIFIED",
            "severity": "WARNING",
            "color_token": "yellow",
            "primary_blocker_message": "No verified PAPER portfolio source is loaded for exposure review.",
            "next_action": "Run PAPER with a verified paper portfolio ledger before reviewing risk exposure.",
        }

    portfolio = summary.get("portfolio") if isinstance(summary.get("portfolio"), dict) else {}
    equity = _decimal(portfolio.get("equity"))
    if equity is None or equity <= 0:
        return {
            **base,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "primary_blocker_message": "Verified portfolio source has invalid equity; exposure review is blocked.",
            "next_action": "Regenerate PAPER portfolio ledger and reconciliation artifacts.",
        }

    raw_positions = summary.get("positions", [])
    positions = raw_positions if isinstance(raw_positions, list) else []
    exposure = Decimal("0")
    unknown_notional = False
    for position in positions:
        if not isinstance(position, dict):
            unknown_notional = True
            continue
        notional = _position_notional(position)
        if notional is None:
            unknown_notional = True
        else:
            exposure += notional
    exposure_pct = (exposure / equity) * Decimal("100")
    drawdown_pct = _decimal(portfolio.get("mdd"))
    drawdown_missing = drawdown_pct is None or drawdown_pct < 0
    drawdown_for_threshold = drawdown_pct if drawdown_pct is not None and drawdown_pct >= 0 else Decimal("0")

    status = "LOW_RISK"
    severity = "NORMAL"
    color_token = "green"
    message = "PAPER exposure and drawdown are within display review thresholds; live orders and scale-up remain blocked."
    next_action = "Continue PAPER monitoring; review blockers before any live-readiness process."
    if exposure_pct >= EXPOSURE_BLOCK_PCT or drawdown_for_threshold >= DRAWDOWN_BLOCK_PCT:
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        message = "PAPER exposure or drawdown breached the display block threshold."
        next_action = "Keep trading disabled; inspect ledger, positions, and risk controls before further review."
    elif unknown_notional or drawdown_missing or exposure_pct >= EXPOSURE_ATTENTION_PCT or drawdown_for_threshold >= DRAWDOWN_ATTENTION_PCT:
        status = "ATTENTION"
        severity = "WARNING"
        color_token = "yellow"
        if drawdown_missing:
            message = "PAPER drawdown hard truth is missing or invalid; risk review cannot be marked low risk."
            next_action = "Regenerate PAPER ledger/reconciliation so drawdown is verified before strategy review."
        else:
            message = "PAPER exposure, drawdown, or position notional needs operator review."
            next_action = "Inspect PAPER positions and ledger values before continuing strategy review."
    quality_status = quality["paper_exposure_quality_status"]
    if quality_status in {"BLOCKED_EXPOSURE_BREACH", "BLOCKED_DRAWDOWN_BREACH", "BLOCKED_RECOVERY_REVIEW"}:
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        message = quality["paper_exposure_quality_message"]
        next_action = "Keep scale-up blocked; inspect the paper exposure quality report before continuing strategy review."
    elif quality_status == "INSUFFICIENT_EVIDENCE" and status == "LOW_RISK":
        status = "ATTENTION"
        severity = "WARNING"
        color_token = "yellow"
        message = quality["paper_exposure_quality_message"]
        next_action = "Continue PAPER only; collect the missing paper exposure evidence before strategy review."
    elif quality_status == "UNAVAILABLE" and status == "LOW_RISK":
        status = "ATTENTION"
        severity = "WARNING"
        color_token = "yellow"
        message = quality["paper_exposure_quality_message"]
        next_action = "Generate a scoped paper exposure quality report before treating risk as low."

    return {
        **base,
        "status": status,
        "severity": severity,
        "color_token": color_token,
        "equity_display": _format_money(equity, currency),
        "exposure_notional_display": _format_money(exposure, currency) if not unknown_notional else "PARTIAL",
        "exposure_pct_display": _format_pct(exposure_pct) if not unknown_notional else "PARTIAL",
        "drawdown_pct_display": _format_pct(drawdown_pct) if not drawdown_missing else "UNVERIFIED",
        "open_position_count": len(positions),
        "exposure_data_status": "PARTIAL" if unknown_notional else "COMPLETE",
        "drawdown_data_status": "UNVERIFIED" if drawdown_missing else "VERIFIED",
        "primary_blocker_message": message,
        "next_action": next_action,
    }


def _decision_trace(summary: dict[str, Any] | None, primary_blocker: str | None, position_snapshot: dict[str, Any]) -> dict[str, Any]:
    final_action = summary.get("final_action", "NO_TRADE") if isinstance(summary, dict) else "NO_TRADE"
    summary_next_action = summary.get("next_action") if isinstance(summary, dict) else None
    entry_candidates = summary.get("entry_candidates", []) if isinstance(summary, dict) else []
    no_trade_context = summary.get("recent_no_trade_context", []) if isinstance(summary, dict) else []
    entry_context = summary.get("recent_entry_context", []) if isinstance(summary, dict) else []
    has_positions = bool(position_snapshot.get("open_position_count"))
    blocker = primary_blocker or (summary.get("blocking_reason") if isinstance(summary, dict) else None) or "HARD_TRUTH_MISSING"
    return {
        "title": "Trading Decision",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "final_action": final_action,
        "no_trade_reason": blocker,
        "entry_status": "BLOCKED" if blocker else "MONITORING",
        "entry_reason": _context_message(
            entry_context,
            "No entry accepted; live orders are blocked and PAPER review must resolve blockers first"
            if not entry_candidates
            else "Entry candidates exist but are display-only until validators pass",
        ),
        "exit_status": "MONITORING" if has_positions else "NO_POSITION",
        "exit_reason": "No open PAPER position requires exit review" if not has_positions else "Open PAPER position requires ledger-backed exit review",
        "next_action": summary_next_action or "resolve blocking reason before trading",
        "recent_no_trade": _context_message(no_trade_context, blocker),
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _recent_event(event_type: str, severity: str, label: str, message: str, source: str = "summary.json") -> dict[str, str]:
    return {
        "event_type": event_type,
        "severity": severity,
        "label": label,
        "message": message,
        "source": source,
    }


def _recent_events(
    summary: dict[str, Any] | None,
    summary_freshness: str,
    decision_trace: dict[str, Any],
    position_snapshot: dict[str, Any],
    operation_status: dict[str, Any],
) -> dict[str, Any]:
    items = []
    if summary_freshness != "PASS":
        items.append(_recent_event("STALE_SOURCE", "WARNING", "Summary stale", "Rerun PAPER before trusting dashboard values"))
    items.append(
        _recent_event(
            "NO_TRADE",
            "WARNING" if decision_trace.get("no_trade_reason") else "INFO",
            "No trade",
            f"{decision_trace.get('final_action', 'NO_TRADE')}: {decision_trace.get('no_trade_reason', 'HARD_TRUTH_MISSING')}",
        )
    )
    items.append(
        _recent_event(
            "ENTRY_REVIEW",
            "INFO",
            "Entry",
            f"{decision_trace.get('entry_status', 'BLOCKED')}: {decision_trace.get('entry_reason', 'No entry accepted')}",
        )
    )
    items.append(
        _recent_event(
            "EXIT_REVIEW",
            "INFO",
            "Exit",
            f"{decision_trace.get('exit_status', 'NO_POSITION')}: {decision_trace.get('exit_reason', 'No exit action pending')}",
        )
    )
    if position_snapshot.get("open_position_count"):
        items.append(
            _recent_event(
                "STATUS",
                "INFO",
                "Position",
                f"{position_snapshot.get('open_position_count')} open PAPER position(s) displayed from summary",
            )
        )
    if isinstance(summary, dict):
        for error in summary.get("recent_errors", [])[:5]:
            message = _context_message([error], "Recent error requires review")
            items.append(_recent_event("ERROR", "ERROR", "Recent error", message))
        for no_trade in summary.get("recent_no_trade_context", [])[:3]:
            message = _context_message([no_trade], str(decision_trace.get("no_trade_reason", "NO_TRADE")))
            items.append(_recent_event("NO_TRADE", "WARNING", "No trade context", message))
    return {
        "title": "Recent Activity",
        "status": "WARNING" if any(item["severity"] == "WARNING" for item in items) else "INFO",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "items": items[:10],
        "empty_message": "No recent PAPER activity",
        "operation_status": str(operation_status.get("status", "UNKNOWN")),
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _component_status(components: dict[str, Any], component_id: str) -> str:
    component = components.get(component_id)
    if not isinstance(component, dict):
        return "UNTESTED"
    status = str(component.get("status") or "UNTESTED").upper()
    return status if status in STABILITY_METRIC_STATUSES else "FAIL"


def _component_message(components: dict[str, Any], component_id: str, fallback: str) -> str:
    component = components.get(component_id)
    if isinstance(component, dict) and component.get("message"):
        return str(component["message"])
    return fallback


def _worst_status(statuses: list[str]) -> str:
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status == "STALE" for status in statuses):
        return "STALE"
    if any(status == "WARN" for status in statuses):
        return "WARN"
    if any(status == "UNTESTED" for status in statuses):
        return "UNTESTED"
    return "PASS"


def _stability_metric(metric_id: str, label: str, status: str, value_display: str, detail: str, source: str) -> dict[str, str]:
    return {
        "metric_id": metric_id,
        "label": label,
        "status": status,
        "value_display": value_display,
        "detail": detail,
        "source": source,
        "trend_direction": "CURRENT_ONLY",
    }


def _stability_trends(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    heartbeat: dict[str, Any] | None,
    source_artifacts: list[dict[str, Any]],
    operation_status: dict[str, Any],
    stability_history: dict[str, Any] | None,
) -> dict[str, Any]:
    heartbeat_loaded = isinstance(heartbeat, dict)
    heartbeat_status = heartbeat.get("heartbeat_status") if heartbeat_loaded else "STALE"
    heartbeat_age = heartbeat.get("heartbeat_age_seconds") if heartbeat_loaded else None
    stale_after = heartbeat.get("stale_after_seconds") if heartbeat_loaded else None
    heartbeat_metric_status = "PASS" if heartbeat_status == "PASS" and operation_status.get("heartbeat_status") == "PASS" else "STALE"
    heartbeat_value = (
        f"{heartbeat_age:.1f}s / {stale_after}s"
        if isinstance(heartbeat_age, (int, float)) and isinstance(stale_after, int)
        else "STALE"
    )

    source_statuses = [str(source.get("freshness_status") or "STALE").upper() for source in source_artifacts]
    source_metric_status = "PASS" if source_statuses and all(status == "PASS" for status in source_statuses) else "STALE"
    stale_sources = [str(source.get("artifact_id", "UNKNOWN")) for source in source_artifacts if source.get("freshness_status") != "PASS"]
    source_detail = "All dashboard display sources are fresh" if not stale_sources else "Refresh required: " + ", ".join(stale_sources)

    components = heartbeat.get("components", {}) if heartbeat_loaded and isinstance(heartbeat.get("components"), dict) else {}
    resource_status = _worst_status([_component_status(components, name) for name in ("cpu", "memory", "disk")])
    disk_detail = _component_message(components, "disk", "Runtime artifact count, disk usage, and writer lock are within safe thresholds")
    artifact_pressure_status = _component_status(components, "disk")
    event_latency_status = _component_status(components, "event_latency")
    queue_status = _component_status(components, "queue_backlog")
    rate_limit_status = _component_status(components, "rate_limit_pressure")

    metrics = [
        _stability_metric(
            "heartbeat_age",
            "Heartbeat age",
            heartbeat_metric_status,
            heartbeat_value,
            "Fresh heartbeat means the program is still reporting safe monitor state",
            "heartbeat.json",
        ),
        _stability_metric(
            "source_freshness",
            "Source freshness",
            source_metric_status,
            f"{source_statuses.count('PASS')}/{len(source_statuses)} PASS",
            source_detail,
            "summary.json",
        ),
        _stability_metric(
            "resource_health",
            "Resource health",
            resource_status,
            resource_status,
            "CPU, memory, and disk health from heartbeat components",
            "heartbeat.json",
        ),
        _stability_metric(
            "runtime_artifact_pressure",
            "Runtime artifact pressure",
            artifact_pressure_status,
            artifact_pressure_status,
            disk_detail,
            "heartbeat.json",
        ),
        _stability_metric(
            "event_latency",
            "Event latency",
            event_latency_status,
            event_latency_status,
            _component_message(components, "event_latency", "Heartbeat latency component is within the current safe threshold"),
            "heartbeat.json",
        ),
        _stability_metric(
            "queue_backlog",
            "Queue backlog",
            queue_status,
            queue_status,
            _component_message(components, "queue_backlog", "No queue backlog pressure reported by heartbeat"),
            "heartbeat.json",
        ),
        _stability_metric(
            "rate_limit_pressure",
            "Rate-limit pressure",
            rate_limit_status,
            rate_limit_status,
            _component_message(components, "rate_limit_pressure", "No rate-limit pressure reported by heartbeat"),
            "heartbeat.json",
        ),
    ]
    metric_statuses = [metric["status"] for metric in metrics]
    history_valid = (
        isinstance(stability_history, dict)
        and stability_history.get("schema_id") == "trader1.runtime_stability_history.v1"
        and stability_history.get("exchange") == exchange
        and stability_history.get("market_type") == market_type
        and stability_history.get("mode") == mode
        and stability_history.get("session_id") == session_id
        and stability_history.get("display_only") is True
        and stability_history.get("dashboard_truth_only") is True
        and not stability_history.get("live_order_ready")
        and not stability_history.get("live_order_allowed")
        and not stability_history.get("can_live_trade")
        and not stability_history.get("scale_up_allowed")
    )
    def safe_non_negative_int(value: Any, default: int = 0) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed >= 0 else default

    history_sample_count = safe_non_negative_int(stability_history.get("sample_count", 0)) if history_valid else 0
    history_status = str(stability_history.get("history_status", "INSUFFICIENT_HISTORY")) if history_valid else "INSUFFICIENT_HISTORY"
    observed_span_seconds = (
        safe_non_negative_int(stability_history.get("observed_span_seconds", 0))
        if history_valid
        else 0
    )
    min_validated_span_seconds = (
        safe_non_negative_int(stability_history.get("min_validated_span_seconds", DEFAULT_MIN_VALIDATED_SPAN_SECONDS), DEFAULT_MIN_VALIDATED_SPAN_SECONDS)
        if history_valid
        else DEFAULT_MIN_VALIDATED_SPAN_SECONDS
    )
    min_validated_sample_count = (
        safe_non_negative_int(stability_history.get("min_validated_sample_count", DEFAULT_MIN_VALIDATED_SAMPLE_COUNT), DEFAULT_MIN_VALIDATED_SAMPLE_COUNT)
        if history_valid
        else DEFAULT_MIN_VALIDATED_SAMPLE_COUNT
    )
    span_validation_status = (
        str(stability_history.get("span_validation_status", "INSUFFICIENT_SPAN"))
        if history_valid
        else "INSUFFICIENT_SPAN"
    )
    history_is_validated = (
        history_valid
        and history_status == "VALIDATED_HISTORY"
        and span_validation_status == "SPAN_VALIDATED"
        and history_sample_count >= min_validated_sample_count
        and observed_span_seconds >= min_validated_span_seconds
    )
    history_window_is_validated = (
        history_valid
        and span_validation_status == "SPAN_VALIDATED"
        and history_sample_count >= min_validated_sample_count
        and observed_span_seconds >= min_validated_span_seconds
    )
    degraded_sample_count = (
        int(stability_history.get("attention_sample_count", 0)) + int(stability_history.get("error_sample_count", 0))
        if history_valid
        else 0
    )
    stale_sample_count = int(stability_history.get("stale_metric_sample_count", 0)) if history_valid else 0
    history_source = "stability_history.json" if history_valid and history_sample_count else "CURRENT_SNAPSHOT_ONLY"

    if operation_status.get("severity") == "ERROR" or any(status == "FAIL" for status in metric_statuses) or history_status == "ERROR":
        status = "ERROR"
        severity = "ERROR"
        color_token = "red"
        summary = "A stability check failed; keep the system blocked and inspect heartbeat details."
    elif (
        all(status == "PASS" for status in metric_statuses)
        and operation_status.get("severity") == "NORMAL"
        and history_status not in {"ATTENTION", "ERROR"}
    ):
        status = "STABLE"
        severity = "NORMAL"
        color_token = "green"
        if history_is_validated:
            summary = (
                f"Validated stability history has {history_sample_count} sample(s) over "
                f"{observed_span_seconds}s; live orders remain blocked."
            )
        elif history_valid and history_sample_count >= min_validated_sample_count:
            summary = (
                f"Current checks are stable, but the observed span is {observed_span_seconds}s/"
                f"{min_validated_span_seconds}s. Live orders remain blocked."
            )
        else:
            summary = "Current heartbeat, source freshness, and resource checks are stable. Live orders remain blocked."
    else:
        status = "ATTENTION"
        severity = "WARNING"
        color_token = "yellow"
        summary = "One or more stability checks need attention before operator review."
    return {
        "title": "Stability Trends",
        "status": status,
        "severity": severity,
        "color_token": color_token,
        "truth_role": "dashboard_serving_truth",
        "source": "heartbeat.json",
        "history_window": "VALIDATED_HISTORY" if history_window_is_validated else "CURRENT_SNAPSHOT_ONLY",
        "history_source": history_source,
        "history_sample_count": history_sample_count,
        "observed_span_seconds": observed_span_seconds,
        "min_validated_span_seconds": min_validated_span_seconds,
        "span_validation_status": span_validation_status,
        "degraded_sample_count": degraded_sample_count,
        "stale_sample_count": stale_sample_count,
        "summary": summary,
        "metrics": metrics,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _metric_status(stability_trends: dict[str, Any], metric_id: str) -> str:
    metrics = stability_trends.get("metrics", []) if isinstance(stability_trends.get("metrics"), list) else []
    for metric in metrics:
        if isinstance(metric, dict) and metric.get("metric_id") == metric_id:
            status = str(metric.get("status", "UNTESTED"))
            return status if status in STABILITY_METRIC_STATUSES else "UNTESTED"
    return "UNTESTED"


def _count_ratio_display(count: int, total: int) -> str:
    if total <= 0:
        return "0/0 (0%)"
    pct = (Decimal(count) / Decimal(total) * Decimal("100")).quantize(Decimal("0.1"))
    return f"{count}/{total} ({pct}%)"


def _long_run_operator_summary(
    *,
    operation_status: dict[str, Any],
    stability_trends: dict[str, Any],
    source_artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    history_sample_count = int(stability_trends.get("history_sample_count", 0))
    observed_span_seconds = int(stability_trends.get("observed_span_seconds", 0))
    min_validated_span_seconds = int(stability_trends.get("min_validated_span_seconds", DEFAULT_MIN_VALIDATED_SPAN_SECONDS))
    span_validation_status = str(stability_trends.get("span_validation_status", "INSUFFICIENT_SPAN"))
    degraded_sample_count = int(stability_trends.get("degraded_sample_count", 0))
    stale_sample_count = int(stability_trends.get("stale_sample_count", 0))
    stable_sample_count = max(history_sample_count - degraded_sample_count, 0)
    history_is_validated = (
        stability_trends.get("history_window") == "VALIDATED_HISTORY"
        and span_validation_status == "SPAN_VALIDATED"
        and observed_span_seconds >= min_validated_span_seconds
    )
    metric_statuses = [
        _metric_status(stability_trends, metric_id)
        for metric_id in (
            "heartbeat_age",
            "source_freshness",
            "resource_health",
            "runtime_artifact_pressure",
            "event_latency",
            "queue_backlog",
            "rate_limit_pressure",
        )
    ]
    source_statuses = [str(source.get("freshness_status", "STALE")) for source in source_artifacts if isinstance(source, dict)]
    all_current_pass = (
        operation_status.get("severity") == "NORMAL"
        and metric_statuses
        and all(status == "PASS" for status in metric_statuses)
        and source_statuses
        and all(status == "PASS" for status in source_statuses)
    )
    if operation_status.get("severity") == "ERROR" or any(status == "FAIL" for status in metric_statuses):
        status = "ERROR"
        severity = "ERROR"
        color_token = "red"
        blocker_code = "RESOURCE_LIMIT"
        message = "A long-run safety input is failing. Keep the system blocked and inspect heartbeat details."
        next_action = "Pause review and inspect heartbeat resource or latency failure before continuing PAPER monitoring."
        source = "heartbeat.json"
    elif any(status == "STALE" for status in metric_statuses) or any(status != "PASS" for status in source_statuses):
        status = "STALE"
        severity = "WARNING"
        color_token = "yellow"
        blocker_code = "LATENCY_TTL_EXPIRED"
        message = "Dashboard sources are stale. The program cannot claim current normal operation until refreshed."
        next_action = "Rerun the PAPER launcher or refresh heartbeat before using this dashboard for review."
        source = "heartbeat.json"
    elif history_is_validated and degraded_sample_count == 0 and stale_sample_count == 0 and all_current_pass:
        status = "DISPLAY_HISTORY_STABLE"
        severity = "NORMAL"
        color_token = "green"
        blocker_code = "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
        message = (
            "Current run is normal and display stability history is clean. "
            "This is not actual 24h runtime evidence and live orders remain blocked."
        )
        next_action = (
            "Continue PAPER monitoring and collect dedicated persistent PAPER/SHADOW runtime evidence; "
            "the display history alone cannot satisfy live-review evidence."
        )
        source = "stability_history.json"
    elif all_current_pass:
        status = "RUNNING_NOW"
        severity = "NORMAL"
        color_token = "blue"
        blocker_code = "SAMPLE_INSUFFICIENT"
        message = "Program is running normally now. Long-run history is still collecting and cannot be treated as LIVE evidence."
        next_action = (
            f"Keep PAPER running until stability history reaches at least {min_validated_span_seconds}s "
            "with clean samples before long-run review."
        )
        source = "heartbeat.json"
    else:
        status = "ATTENTION"
        severity = "WARNING"
        color_token = "yellow"
        blocker_code = "HARD_TRUTH_MISSING"
        message = "One or more operation checks needs attention before operator review."
        next_action = "Resolve the displayed heartbeat, source, or resource warning before continuing review."
        source = "heartbeat.json"

    return {
        "title": "Long-Run Operation",
        "status": status,
        "severity": severity,
        "color_token": color_token,
        "truth_role": "dashboard_serving_truth",
        "source": source,
        "history_window": str(stability_trends.get("history_window", "CURRENT_SNAPSHOT_ONLY")),
        "history_sample_count": history_sample_count,
        "observed_span_seconds": observed_span_seconds,
        "min_validated_span_seconds": min_validated_span_seconds,
        "span_validation_status": span_validation_status,
        "stable_sample_count": stable_sample_count,
        "degraded_sample_count": degraded_sample_count,
        "stale_sample_count": stale_sample_count,
        "stable_sample_rate_display": _count_ratio_display(stable_sample_count, history_sample_count),
        "degraded_sample_rate_display": _count_ratio_display(degraded_sample_count, history_sample_count),
        "stale_sample_rate_display": _count_ratio_display(stale_sample_count, history_sample_count),
        "latency_trend_status": _metric_status(stability_trends, "event_latency"),
        "error_frequency_status": "FAIL" if degraded_sample_count or operation_status.get("severity") == "ERROR" else "PASS",
        "retry_trend_status": _metric_status(stability_trends, "rate_limit_pressure"),
        "dashboard_refresh_delay_status": _metric_status(stability_trends, "source_freshness"),
        "resource_pressure_status": _metric_status(stability_trends, "runtime_artifact_pressure"),
        "summary": message,
        "primary_blocker_code": blocker_code,
        "primary_blocker_message": "Live remains disabled; this panel is operator visibility only.",
        "next_action": next_action,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _shadow_runtime_harness_status(report: dict[str, Any] | None) -> dict[str, Any]:
    def safe_count(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return parsed if parsed >= 0 else 0

    def has_negative_count(*fields: str) -> bool:
        for field in fields:
            try:
                if int(report.get(field)) < 0:
                    return True
            except (AttributeError, TypeError, ValueError):
                continue
        return False

    base = {
        "title": "PAPER / SHADOW Runtime Harness",
        "status": "NOT_LOADED",
        "severity": "WARNING",
        "color_token": "yellow",
        "truth_role": "dashboard_serving_truth",
        "source": "NOT_LOADED",
        "harness_execution_mode": "NOT_LOADED",
        "runtime_evidence_status": "NOT_LOADED",
        "runtime_evidence_role": "NOT_LONG_RUN_EVIDENCE",
        "requested_cycle_count": 0,
        "completed_cycle_count": 0,
        "observation_count": 0,
        "heartbeat_count": 0,
        "measured_runtime_seconds": 0,
        "minimum_runtime_window_seconds": 0,
        "actual_non_live_runtime_harness_executed": False,
        "long_run_evidence_eligible": False,
        "optimizer_input_role": "BLOCKER_ONLY_NOT_RANKING_INPUT",
        "primary_blocker_code": "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        "one_line_summary": "No short-window PAPER/SHADOW harness report is loaded.",
        "next_operator_action": "Run the non-live PAPER/SHADOW harness before treating runtime evidence as checked.",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    if not isinstance(report, dict):
        return base

    unsafe_live_or_scale = any(
        report.get(field) is not False
        for field in (
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
            "promotion_eligible",
            "credential_access_attempted",
            "exchange_account_call_attempted",
            "live_order_api_attempted",
            "order_adapter_called",
            "optimizer_ranking_input_attempted",
            "scale_up_requested",
        )
    )
    expected_contract = (
        report.get("schema_id") == "trader1.shadow_observation_actual_runtime_harness_report.v1"
        and report.get("harness_execution_mode") == "NON_LIVE_LOCAL_PAPER_SHADOW_HARNESS"
        and report.get("data_source_role") == "DETERMINISTIC_PAPER_FIXTURE_NO_CREDENTIALS"
        and report.get("runtime_evidence_status") == "BLOCKED_LONG_RUN_EVIDENCE_MISSING"
        and report.get("runtime_evidence_role") == "EXECUTION_HARNESS_PROOF_ONLY_NOT_LONG_RUN"
        and report.get("dashboard_display_truth_only") is True
        and report.get("dashboard_visibility_status") == "VISIBLE_AS_SHORT_WINDOW_BLOCKED"
        and report.get("optimizer_input_role") == "BLOCKER_ONLY_NOT_RANKING_INPUT"
        and report.get("long_run_evidence_present") is False
        and report.get("long_run_evidence_eligible") is False
    )
    invalid_measurement = has_negative_count(
        "requested_cycle_count",
        "completed_cycle_count",
        "observations_per_cycle",
        "observation_count",
        "heartbeat_count",
        "measured_runtime_seconds",
        "minimum_runtime_window_seconds",
        "minimum_actual_cycle_count",
    )
    status = "SHORT_WINDOW_EXECUTED"
    severity = "NORMAL"
    color_token = "blue"
    summary = "Short non-live PAPER/SHADOW check passed. This is not long-run evidence and cannot enable live trading."
    next_action = str(report.get("next_operator_action") or "Keep collecting long-run PAPER/SHADOW evidence; live remains blocked.")
    if invalid_measurement:
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        summary = "Harness report has invalid negative runtime measurements; dashboard keeps live blocked."
        next_action = "Regenerate the non-live PAPER/SHADOW harness report with valid non-negative measurements."
    elif unsafe_live_or_scale or not expected_contract:
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        summary = "Harness report is unsafe or contract-mismatched; dashboard keeps live blocked."
        next_action = "Regenerate the non-live harness report and keep live disabled."
    elif _freshness_from_generated_at(report) != "PASS":
        status = "STALE"
        severity = "WARNING"
        color_token = "yellow"
        summary = "Harness report is stale. Short-window evidence must be refreshed before operator review."
        next_action = "Rerun the non-live PAPER/SHADOW harness before trusting this dashboard value."

    base.update(
        {
            "status": status,
            "severity": severity,
            "color_token": color_token,
            "source": "actual_runtime_harness_report.json",
            "harness_execution_mode": str(report.get("harness_execution_mode") or "UNKNOWN"),
            "runtime_evidence_status": str(report.get("runtime_evidence_status") or "NOT_LOADED"),
            "runtime_evidence_role": str(report.get("runtime_evidence_role") or "NOT_LONG_RUN_EVIDENCE"),
            "requested_cycle_count": safe_count(report.get("requested_cycle_count")),
            "completed_cycle_count": safe_count(report.get("completed_cycle_count")),
            "observation_count": safe_count(report.get("observation_count")),
            "heartbeat_count": safe_count(report.get("heartbeat_count")),
            "measured_runtime_seconds": safe_count(report.get("measured_runtime_seconds")),
            "minimum_runtime_window_seconds": safe_count(report.get("minimum_runtime_window_seconds")),
            "actual_non_live_runtime_harness_executed": bool(report.get("actual_non_live_runtime_harness_executed")),
            "long_run_evidence_eligible": False,
            "optimizer_input_role": str(report.get("optimizer_input_role") or "BLOCKER_ONLY_NOT_RANKING_INPUT"),
            "primary_blocker_code": "DATA_QUALITY_INSUFFICIENT"
            if invalid_measurement
            else str(report.get("primary_blocker_code") or "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING"),
            "one_line_summary": summary,
            "next_operator_action": next_action,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    return base


def _shadow_persistent_runtime_status(report: dict[str, Any] | None) -> dict[str, Any]:
    def safe_count(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return parsed if parsed >= 0 else 0

    def has_negative_count(*fields: str) -> bool:
        for field in fields:
            try:
                if int(report.get(field)) < 0:
                    return True
            except (AttributeError, TypeError, ValueError):
                continue
        return False

    base = {
        "title": "PAPER / SHADOW Persistent Runtime",
        "status": "NOT_LOADED",
        "severity": "WARNING",
        "color_token": "yellow",
        "truth_role": "dashboard_serving_truth",
        "source": "NOT_LOADED",
        "runtime_execution_mode": "NOT_LOADED",
        "runtime_duration_evidence_source": "NOT_LOADED",
        "duration_evidence_role": "NOT_LONG_RUN_EVIDENCE",
        "requested_cycle_count": 0,
        "completed_cycle_count": 0,
        "heartbeat_count": 0,
        "heartbeat_interval_seconds": 0,
        "estimated_runtime_seconds": 0,
        "observed_runtime_seconds": 0,
        "actual_persistent_runtime_executed": False,
        "long_run_evidence_eligible": False,
        "optimizer_input_role": "NOT_LOADED",
        "primary_blocker_code": "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        "one_line_summary": "No persistent PAPER/SHADOW runtime stub report is loaded.",
        "next_operator_action": "Run the bounded non-live persistent runtime stub; do not treat missing runtime evidence as live review evidence.",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    if not isinstance(report, dict):
        return base

    unsafe_live_or_scale = any(
        report.get(field) is not False
        for field in (
            "actual_persistent_runtime_executed",
            "long_run_evidence_eligible",
            "promotion_eligible",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
            "order_adapter_called",
        )
    )
    observed_raw = report.get("observed_runtime_seconds")
    observed_is_zero = isinstance(observed_raw, int) and observed_raw == 0
    expected_contract = (
        report.get("schema_id") == "trader1.shadow_observation_persistent_runtime_report.v1"
        and report.get("exchange") == "UPBIT"
        and report.get("market_type") == "KRW_SPOT"
        and report.get("source_mode") == "PAPER"
        and report.get("mode") == "SHADOW"
        and report.get("runtime_execution_mode") == "BOUNDED_SHADOW_STUB"
        and report.get("runtime_evidence_role") == "PERSISTENT_RUNTIME_STUB_ONLY"
        and report.get("runtime_status") == "PASS"
        and report.get("source_scheduler_guard_status") == "PASS"
        and report.get("source_scheduler_validation_status") == "PASS"
        and report.get("heartbeat_status") == "PASS"
        and report.get("cycle_identity_status") == "PASS"
        and report.get("recovery_action") == "NO_RECOVERY_NEEDED"
        and report.get("run_action") == "COLLECT_SHADOW_OBSERVATION_STUB_ONLY"
        and report.get("runtime_duration_evidence_source") == "STUB_ESTIMATE_ONLY"
        and report.get("duration_evidence_role") == "NOT_LONG_RUN_EVIDENCE"
        and report.get("actual_persistent_runtime_executed") is False
        and report.get("dashboard_display_truth_only") is True
        and report.get("long_run_evidence_eligible") is False
        and report.get("optimizer_input_role") == "SHADOW_PERSISTENT_RUNTIME_STUB_ONLY"
        and observed_is_zero
    )
    invalid_measurement = has_negative_count(
        "requested_cycle_count",
        "completed_cycle_count",
        "heartbeat_count",
        "heartbeat_interval_seconds",
        "estimated_runtime_seconds",
        "observed_runtime_seconds",
    )
    estimated_seconds = safe_count(report.get("estimated_runtime_seconds"))
    max_runtime_seconds = safe_count(report.get("max_runtime_seconds"))
    expected_estimated = safe_count(report.get("completed_cycle_count")) * safe_count(report.get("heartbeat_interval_seconds"))
    inconsistent_estimate = estimated_seconds != expected_estimated
    runtime_budget_exceeded = max_runtime_seconds > 0 and expected_estimated > max_runtime_seconds

    status = "STUB_ONLY"
    severity = "WARNING"
    color_token = "yellow"
    summary = "Persistent SHADOW runtime is a bounded stub estimate only. Observed long-run runtime evidence is still missing."
    next_action = str(
        report.get("next_operator_action")
        or "Collect real PAPER/SHADOW long-run evidence separately; this stub cannot support LIVE review."
    )
    blocker_code = "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
    if invalid_measurement:
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        summary = "Persistent runtime report has invalid negative duration or cycle measurements."
        next_action = "Regenerate the persistent runtime stub report with non-negative values."
        blocker_code = "DATA_QUALITY_INSUFFICIENT"
    elif not observed_is_zero:
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        summary = "Persistent runtime stub attempted to display observed wall-clock runtime duration."
        next_action = "Keep this report blocked and collect actual long-run PAPER/SHADOW evidence separately."
        blocker_code = "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
    elif unsafe_live_or_scale or not expected_contract or inconsistent_estimate or runtime_budget_exceeded:
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        summary = "Persistent runtime report is unsafe or contract-mismatched; dashboard keeps it blocked."
        next_action = "Regenerate the bounded SHADOW runtime stub and keep long-run evidence blocked."
        blocker_code = "RESOURCE_LIMIT_BLOCK" if runtime_budget_exceeded else str(report.get("primary_blocker_code") or "LIVE_FINAL_GUARD_FAILED")
    elif _freshness_from_generated_at(report) != "PASS":
        status = "STALE"
        severity = "WARNING"
        color_token = "yellow"
        summary = "Persistent runtime stub report is stale. It remains non-live, display-only evidence."
        next_action = "Rerun the bounded non-live persistent runtime stub before reviewing this panel."
        blocker_code = "LATENCY_TTL_EXPIRED"

    base.update(
        {
            "status": status,
            "severity": severity,
            "color_token": color_token,
            "source": "shadow_observation_persistent_runtime_report.json",
            "runtime_execution_mode": str(report.get("runtime_execution_mode") or "UNKNOWN"),
            "runtime_duration_evidence_source": str(report.get("runtime_duration_evidence_source") or "NOT_LOADED"),
            "duration_evidence_role": str(report.get("duration_evidence_role") or "NOT_LONG_RUN_EVIDENCE"),
            "requested_cycle_count": safe_count(report.get("requested_cycle_count")),
            "completed_cycle_count": safe_count(report.get("completed_cycle_count")),
            "heartbeat_count": safe_count(report.get("heartbeat_count")),
            "heartbeat_interval_seconds": safe_count(report.get("heartbeat_interval_seconds")),
            "estimated_runtime_seconds": estimated_seconds,
            "observed_runtime_seconds": safe_count(report.get("observed_runtime_seconds")),
            "actual_persistent_runtime_executed": False,
            "long_run_evidence_eligible": False,
            "optimizer_input_role": str(report.get("optimizer_input_role") or "SHADOW_PERSISTENT_RUNTIME_STUB_ONLY"),
            "primary_blocker_code": blocker_code,
            "one_line_summary": summary,
            "next_operator_action": next_action,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    return base


def _paper_runtime_recovery_guard_status(
    *,
    report: dict[str, Any] | None,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
) -> dict[str, Any]:
    def safe_count(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return parsed if parsed >= 0 else 0

    base = {
        "title": "PAPER Runtime Recovery Guard",
        "status": "NOT_LOADED",
        "severity": "WARNING",
        "color_token": "yellow",
        "truth_role": "dashboard_serving_truth",
        "source": "NOT_LOADED",
        "guard_id": "NOT_LOADED",
        "loop_id": "NOT_LOADED",
        "latest_cycle_status": "MISSING",
        "latest_cycle_recoverable": False,
        "canonical_jsonl_checked_count": 0,
        "corrupted_jsonl_quarantined_count": 0,
        "ledger_jsonl_checked_count": 0,
        "corrupted_ledger_jsonl_quarantined_count": 0,
        "ledger_jsonl_invalid_count": 0,
        "orphan_tmp_file_count": 0,
        "resume_action": "SAFE_MODE_RECONCILE",
        "paper_runtime_resume_allowed": False,
        "actual_long_run_evidence_created": False,
        "promotion_eligible": False,
        "primary_blocker_code": "RECONCILIATION_REQUIRED",
        "one_line_summary": "PAPER runtime recovery guard is not loaded; resume status is unverified.",
        "next_operator_action": "Run the bounded Upbit PAPER runtime recovery guard before relying on runtime resume status.",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    if not isinstance(report, dict):
        return base

    validation_result = validate_upbit_paper_runtime_recovery_guard_report(report)
    scope_matches = (
        report.get("exchange") == exchange
        and report.get("market_type") == market_type
        and report.get("mode") == mode
        and report.get("session_id") == session_id
    )
    freshness_status = _freshness_from_generated_at(report)
    unsafe_permission = any(
        report.get(field) is not False
        for field in (
            "actual_long_run_evidence_created",
            "promotion_eligible",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        )
    )

    status = "PASS"
    severity = "NORMAL"
    color_token = "green"
    primary_blocker = report.get("primary_blocker_code")
    summary = "PAPER runtime recovery guard is clean: latest cycle is recoverable, canonical JSONL is checked, and no orphan temp files are present."
    next_action = "Continue PAPER monitoring. This recovery check is not LIVE_READY, not promotion evidence, and not long-run evidence."
    paper_resume_allowed = report.get("paper_runtime_resume_allowed") is True

    if unsafe_permission:
        status = "INVALID"
        severity = "ERROR"
        color_token = "red"
        primary_blocker = "LIVE_FINAL_GUARD_FAILED"
        summary = "Recovery guard attempted to create live, promotion, long-run, or scale permission; dashboard blocked it."
        next_action = "Inspect and regenerate the recovery guard report; keep PAPER in SAFE_MODE until repaired."
        paper_resume_allowed = False
    elif validation_result.status == "FAIL" or not scope_matches:
        status = "INVALID"
        severity = "ERROR"
        color_token = "red"
        primary_blocker = validation_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH"
        summary = "Recovery guard is invalid or scoped to another runtime; dashboard blocks resume display."
        next_action = "Regenerate a scoped Upbit KRW_SPOT PAPER recovery guard report before continuing review."
        paper_resume_allowed = False
    elif validation_result.status == "BLOCKED":
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        primary_blocker = validation_result.blocker_code or report.get("primary_blocker_code") or "RECONCILIATION_REQUIRED"
        summary = "Recovery guard found partial-write or recoverability risk; PAPER resume requires reconcile review."
        next_action = "Stop strategy review, inspect quarantined or temp artifacts, and rerun PAPER recovery after reconciliation."
        paper_resume_allowed = False
    elif freshness_status != "PASS":
        status = "STALE"
        severity = "WARNING"
        color_token = "yellow"
        primary_blocker = "LATENCY_TTL_EXPIRED"
        summary = "Recovery guard is stale. It cannot prove current PAPER runtime resume status."
        next_action = "Rerun the bounded PAPER recovery guard before trusting runtime resume status."
        paper_resume_allowed = False

    base.update(
        {
            "status": status,
            "severity": severity,
            "color_token": color_token,
            "source": "upbit_paper_runtime_recovery_guard_report.json",
            "guard_id": str(report.get("guard_id") or "UNKNOWN"),
            "loop_id": str(report.get("loop_id") or "UNKNOWN"),
            "latest_cycle_status": str(report.get("latest_cycle_status") or "MISSING"),
            "latest_cycle_recoverable": report.get("latest_cycle_recoverable") is True,
            "canonical_jsonl_checked_count": safe_count(report.get("canonical_jsonl_checked_count")),
            "corrupted_jsonl_quarantined_count": safe_count(report.get("corrupted_jsonl_quarantined_count")),
            "ledger_jsonl_checked_count": safe_count(report.get("ledger_jsonl_checked_count")),
            "corrupted_ledger_jsonl_quarantined_count": safe_count(report.get("corrupted_ledger_jsonl_quarantined_count")),
            "ledger_jsonl_invalid_count": safe_count(report.get("ledger_jsonl_invalid_count")),
            "orphan_tmp_file_count": safe_count(report.get("orphan_tmp_file_count")),
            "resume_action": "RESUME_PAPER_ONLY" if paper_resume_allowed else "SAFE_MODE_RECONCILE",
            "paper_runtime_resume_allowed": paper_resume_allowed,
            "actual_long_run_evidence_created": False,
            "promotion_eligible": False,
            "primary_blocker_code": str(primary_blocker or "LIVE_READY_MISSING"),
            "one_line_summary": summary,
            "next_operator_action": next_action,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    return base


def _market_data_continuity_status(
    *,
    report: dict[str, Any] | None,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
) -> dict[str, Any]:
    def safe_count(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return parsed if parsed >= 0 else 0

    base = {
        "title": "Market Data Continuity",
        "status": "NOT_LOADED",
        "severity": "WARNING",
        "color_token": "yellow",
        "truth_role": "dashboard_serving_truth",
        "source": "NOT_LOADED",
        "evidence_role": "PAPER_DATA_CONTINUITY_HISTORY_ONLY_NOT_LIVE_READY",
        "symbol": "UNKNOWN",
        "history_window_label": "NOT_LOADED",
        "total_attempt_count": 0,
        "pass_attempt_count": 0,
        "blocked_attempt_count": 0,
        "duplicate_latest_event_block_count": 0,
        "non_advancing_block_count": 0,
        "data_unavailable_block_count": 0,
        "latest_attempt_status": "BLOCKED",
        "primary_blocker_code": "DATA_UNAVAILABLE",
        "one_line_summary": "No PAPER public market-data continuity history is loaded.",
        "next_operator_action": "Run PAPER public market-data continuity collection before relying on candidate or regime status.",
        "display_only": True,
        "dashboard_truth_only": True,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    if not isinstance(report, dict):
        return base

    validation_result = validate_upbit_public_rest_continuity_history_report(report)
    scope_matches = (
        report.get("exchange") == exchange
        and report.get("market_type") == market_type
        and report.get("mode") == mode
        and report.get("session_id") == session_id
    )
    freshness_status = _freshness_from_generated_at(report)
    unsafe_permission = any(
        report.get(field) is not False
        for field in (
            "long_run_evidence_eligible",
            "promotion_eligible",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        )
    )

    status = "PASS"
    severity = "NORMAL"
    color_token = "blue"
    primary_blocker = report.get("primary_blocker_code") or "LIVE_READY_MISSING"
    summary = "PAPER public market-data continuity is healthy for display review only; it is not LIVE_READY or long-run evidence."
    next_action = "Keep collecting PAPER continuity samples and review strategy/regime outputs as PAPER-only evidence."

    if unsafe_permission or report.get("evidence_role") != "PAPER_DATA_CONTINUITY_HISTORY_ONLY_NOT_LIVE_READY":
        status = "INVALID"
        severity = "ERROR"
        color_token = "red"
        primary_blocker = "LIVE_FINAL_GUARD_FAILED"
        summary = "Market-data continuity history attempted live, promotion, long-run, or scale permission; dashboard blocked it."
        next_action = "Regenerate PAPER-only market-data continuity history before using dashboard market-data status."
    elif validation_result.status == "FAIL" or not scope_matches:
        status = "INVALID"
        severity = "ERROR"
        color_token = "red"
        primary_blocker = validation_result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH"
        summary = "Market-data continuity history is invalid or scoped to a different runtime."
        next_action = "Regenerate a scoped UPBIT/KRW_SPOT/PAPER continuity history for this session."
    elif validation_result.status == "BLOCKED":
        status = "BLOCKED"
        severity = "WARNING"
        color_token = "yellow"
        primary_blocker = validation_result.blocker_code or report.get("primary_blocker_code") or "DATA_QUALITY_INSUFFICIENT"
        summary = "Market-data continuity is blocked, so candidate, entry, and regime signals remain review-only."
        next_action = "Collect additional public REST continuity attempts until latest data advances and enough PASS attempts exist."
    elif freshness_status != "PASS":
        status = "STALE"
        severity = "WARNING"
        color_token = "yellow"
        primary_blocker = "LATENCY_TTL_EXPIRED"
        summary = "Market-data continuity history is stale and cannot prove current PAPER data flow."
        next_action = "Refresh PAPER public market-data continuity before trusting candidate or regime values."

    base.update(
        {
            "status": status,
            "severity": severity,
            "color_token": color_token,
            "source": "rest_continuity_history.json",
            "symbol": str(report.get("symbol") or "UNKNOWN"),
            "history_window_label": str(report.get("history_window_label") or "UNKNOWN"),
            "total_attempt_count": safe_count(report.get("total_attempt_count")),
            "pass_attempt_count": safe_count(report.get("pass_attempt_count")),
            "blocked_attempt_count": safe_count(report.get("blocked_attempt_count")),
            "duplicate_latest_event_block_count": safe_count(report.get("duplicate_latest_event_block_count")),
            "non_advancing_block_count": safe_count(report.get("non_advancing_block_count")),
            "data_unavailable_block_count": safe_count(report.get("data_unavailable_block_count")),
            "latest_attempt_status": str(report.get("latest_attempt_status") or "BLOCKED"),
            "primary_blocker_code": str(primary_blocker or "LIVE_READY_MISSING"),
            "one_line_summary": summary,
            "next_operator_action": next_action,
            "long_run_evidence_eligible": False,
            "promotion_eligible": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    return base


def _runtime_evidence_boundary_status(
    *,
    long_run_operator_summary: dict[str, Any],
    shadow_runtime_harness_status: dict[str, Any],
    shadow_persistent_runtime_status: dict[str, Any],
    shadow_runtime_orchestration_status: dict[str, Any],
) -> dict[str, Any]:
    long_run_status = str(long_run_operator_summary.get("status", "ATTENTION"))
    harness_status = str(shadow_runtime_harness_status.get("status", "NOT_LOADED"))
    persistent_status = str(shadow_persistent_runtime_status.get("status", "NOT_LOADED"))
    orchestration_status = str(shadow_runtime_orchestration_status.get("status", "NOT_LOADED"))
    observed_span_seconds = int(long_run_operator_summary.get("observed_span_seconds", 0) or 0)
    history_sample_count = int(long_run_operator_summary.get("history_sample_count", 0) or 0)
    stable_sample_count = int(long_run_operator_summary.get("stable_sample_count", 0) or 0)
    degraded_sample_count = int(long_run_operator_summary.get("degraded_sample_count", 0) or 0)
    stale_sample_count = int(long_run_operator_summary.get("stale_sample_count", 0) or 0)
    duration_floor_met = observed_span_seconds >= ACTUAL_LONG_RUN_MIN_VALIDATED_SPAN_SECONDS
    cycle_floor_met = (
        history_sample_count >= ACTUAL_LONG_RUN_MIN_ACTUAL_CYCLE_COUNT
        and stable_sample_count >= ACTUAL_LONG_RUN_MIN_ACTUAL_CYCLE_COUNT
        and degraded_sample_count == 0
        and stale_sample_count == 0
    )
    actual_long_run_floor_met = duration_floor_met and cycle_floor_met

    if long_run_status == "VALIDATED_STABLE" and actual_long_run_floor_met:
        status = "ACTUAL_LONG_RUN_VALIDATED"
        actual_status = "VALIDATED_STABLE"
        severity = "NORMAL"
        color_token = "green"
        blocker_code = "LIVE_READY_MISSING"
        summary = "Actual long-run dashboard history is validated for operator review only. LIVE review evidence is still missing."
        next_action = "Continue PAPER monitoring and collect official live-review evidence before any LIVE step."
    elif long_run_status in {"DISPLAY_HISTORY_STABLE", "VALIDATED_STABLE"}:
        status = "ACTUAL_LONG_RUN_COLLECTING"
        actual_status = "COLLECTING"
        severity = "NORMAL"
        color_token = "blue"
        blocker_code = "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
        summary = (
            "Program stability history is clean, but actual long-run evidence still needs "
            f"{ACTUAL_LONG_RUN_MIN_VALIDATED_SPAN_SECONDS}s duration and "
            f"{ACTUAL_LONG_RUN_MIN_ACTUAL_CYCLE_COUNT} stable samples before review. "
            f"Current display history: {observed_span_seconds}s and {stable_sample_count} stable samples. "
            "Use dedicated persistent PAPER/SHADOW runtime evidence for the full proof; display history alone is not enough."
        )
        next_action = (
            "Run the persistent PAPER/SHADOW evidence path until it can prove at least "
            f"{ACTUAL_LONG_RUN_MIN_VALIDATED_SPAN_SECONDS}s and "
            f"{ACTUAL_LONG_RUN_MIN_ACTUAL_CYCLE_COUNT} stable runtime samples; do not rely on dashboard display history alone."
        )
    elif long_run_status == "RUNNING_NOW":
        status = "ACTUAL_LONG_RUN_COLLECTING"
        actual_status = "COLLECTING"
        severity = "NORMAL"
        color_token = "blue"
        blocker_code = "SAMPLE_INSUFFICIENT"
        summary = "Program is running now, but actual long-run history is still collecting."
        next_action = "Keep PAPER running until validated long-run samples exist; do not treat stub duration as long-run evidence."
    elif long_run_status == "STALE":
        status = "STALE"
        actual_status = "STALE"
        severity = "WARNING"
        color_token = "yellow"
        blocker_code = "LATENCY_TTL_EXPIRED"
        summary = "Runtime evidence is stale. Refresh PAPER sources before trusting the dashboard."
        next_action = "Rerun PAPER or refresh heartbeat before operator review."
    elif long_run_status == "ERROR":
        status = "BLOCKED"
        actual_status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        blocker_code = str(long_run_operator_summary.get("primary_blocker_code") or "RESOURCE_LIMIT")
        summary = "A runtime safety input is failing. Live review remains blocked."
        next_action = "Inspect the failing runtime or resource input before continuing PAPER monitoring."
    else:
        status = "ACTUAL_LONG_RUN_MISSING"
        actual_status = "MISSING"
        severity = "WARNING"
        color_token = "yellow"
        blocker_code = "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
        summary = "Actual long-run runtime evidence is missing. Short-window checks and stub estimates cannot replace it."
        next_action = "Collect real PAPER/SHADOW long-run runtime evidence; keep LIVE review blocked."

    if persistent_status == "STUB_ONLY" and status == "ACTUAL_LONG_RUN_VALIDATED":
        stub_boundary_message = "Persistent runtime remains stub-only and does not contribute to the validated long-run claim."
    elif persistent_status == "STUB_ONLY":
        stub_boundary_message = "Persistent runtime is a stub estimate only and is not actual long-run evidence."
    else:
        stub_boundary_message = "No validated persistent runtime source is loaded for long-run evidence."

    def requirement_status_from_source(source_status: str, pass_status: str) -> str:
        if source_status == pass_status:
            return "PASS"
        if source_status == "STALE":
            return "STALE"
        if source_status == "BLOCKED":
            return "BLOCKED"
        return "MISSING"

    def actual_requirement_status() -> str:
        if actual_status == "VALIDATED_STABLE":
            return "PASS"
        if actual_status == "COLLECTING":
            return "COLLECTING"
        if actual_status == "STALE":
            return "STALE"
        if actual_status == "BLOCKED":
            return "BLOCKED"
        return "MISSING"

    def requirement(
        requirement_id: str,
        label: str,
        requirement_status: str,
        source: str,
        detail: str,
        next_operator_action: str,
    ) -> dict[str, Any]:
        return {
            "requirement_id": requirement_id,
            "label": label,
            "status": requirement_status,
            "source": source,
            "detail": detail,
            "next_operator_action": next_operator_action,
            "blocking_for_live_review": True,
            "display_only": True,
            "dashboard_truth_only": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    actual_status_for_requirements = actual_requirement_status()
    heartbeat_requirement_status = (
        "PASS"
        if long_run_status in {"RUNNING_NOW", "DISPLAY_HISTORY_STABLE", "VALIDATED_STABLE"}
        else actual_status_for_requirements
    )
    recovery_requirement_status = "PASS" if actual_status == "VALIDATED_STABLE" else actual_status_for_requirements
    actual_duration_requirement_status = (
        "PASS"
        if long_run_status == "VALIDATED_STABLE" and duration_floor_met
        else actual_status_for_requirements
    )
    actual_cycle_requirement_status = (
        "PASS"
        if long_run_status == "VALIDATED_STABLE" and cycle_floor_met
        else actual_status_for_requirements
    )
    evidence_requirements = [
        requirement(
            "PERSISTENT_RUNTIME_SOURCE",
            "Persistent runtime source",
            requirement_status_from_source(persistent_status, "STUB_ONLY"),
            "shadow_observation_persistent_runtime_report.json"
            if persistent_status != "NOT_LOADED"
            else "NOT_LOADED",
            "Loads the persistent runtime source as stub-only evidence; it never becomes actual long-run proof.",
            "Generate or refresh the bounded non-live persistent runtime report.",
        ),
        requirement(
            "SHORT_WINDOW_HARNESS_SOURCE",
            "Short-window harness source",
            requirement_status_from_source(harness_status, "SHORT_WINDOW_EXECUTED"),
            "actual_runtime_harness_report.json" if harness_status != "NOT_LOADED" else "NOT_LOADED",
            "Confirms the short-window PAPER/SHADOW harness ran; it is not long-run or LIVE_READY evidence.",
            "Run the non-live PAPER/SHADOW harness and keep live review blocked.",
        ),
        requirement(
            "RUNTIME_ORCHESTRATION_SOURCE_PAIRING",
            "Runtime source pairing",
            requirement_status_from_source(orchestration_status, "BOUNDARY_VERIFIED"),
            "runtime_orchestration_report.json" if orchestration_status != "NOT_LOADED" else "NOT_LOADED",
            "Verifies stub and harness source hashes are paired; it still blocks long-run promotion.",
            "Generate the runtime orchestration guard after both non-live sources exist.",
        ),
        requirement(
            "ACTUAL_RUNTIME_DURATION",
            "Actual runtime duration",
            actual_duration_requirement_status,
            str(long_run_operator_summary.get("source") or "heartbeat.json"),
            f"Requires at least {ACTUAL_LONG_RUN_MIN_VALIDATED_SPAN_SECONDS}s observed PAPER/SHADOW duration, not stub estimates.",
            "Keep PAPER/SHADOW running until enough validated duration is accumulated.",
        ),
        requirement(
            "ACTUAL_CYCLE_COUNT",
            "Actual cycle count",
            actual_cycle_requirement_status,
            str(long_run_operator_summary.get("source") or "heartbeat.json"),
            f"Requires at least {ACTUAL_LONG_RUN_MIN_ACTUAL_CYCLE_COUNT} validated stable runtime samples from persistent PAPER/SHADOW evidence, not display-history samples or requested-cycle configuration.",
            "Collect observed PAPER/SHADOW cycles through the persistent runtime evidence path before review.",
        ),
        requirement(
            "EVIDENCE_WINDOW_COUNT",
            "Evidence windows",
            actual_cycle_requirement_status,
            str(long_run_operator_summary.get("source") or "heartbeat.json"),
            "Requires validated evidence windows over time; single startup checks are not enough.",
            "Continue PAPER monitoring until multiple stable evidence windows exist.",
        ),
        requirement(
            "HEARTBEAT_FRESHNESS_HISTORY",
            "Heartbeat freshness",
            heartbeat_requirement_status,
            str(long_run_operator_summary.get("source") or "heartbeat.json"),
            "Shows current heartbeat freshness and whether history is usable for operator review.",
            "Keep heartbeat fresh and append stability history during PAPER monitoring.",
        ),
        requirement(
            "RECOVERY_AND_PARTIAL_WRITE_CLEAN",
            "Recovery and partial-write clean",
            recovery_requirement_status,
            str(long_run_operator_summary.get("source") or "heartbeat.json"),
            "Requires clean long-run recovery signals before any live review evidence claim.",
            "Keep monitoring recovery and partial-write signals through validated runtime history.",
        ),
    ]
    evidence_requirements_blocking_count = sum(
        1 for item in evidence_requirements if item["status"] != "PASS"
    )
    evidence_requirement_summary = (
        f"{len(evidence_requirements) - evidence_requirements_blocking_count}/{len(evidence_requirements)} "
        "long-run evidence requirements currently pass for display-only review; "
        "LIVE review remains blocked."
    )

    return {
        "title": "Runtime Evidence Boundary",
        "status": status,
        "actual_long_run_evidence_status": actual_status,
        "short_window_evidence_status": harness_status,
        "stub_runtime_evidence_status": persistent_status,
        "long_run_operator_status": long_run_status,
        "runtime_orchestration_status": orchestration_status,
        "severity": severity,
        "color_token": color_token,
        "truth_role": "dashboard_serving_truth",
        "source": str(long_run_operator_summary.get("source") or "heartbeat.json"),
        "one_line_summary": summary,
        "stub_boundary_message": stub_boundary_message,
        "evidence_requirement_summary": evidence_requirement_summary,
        "evidence_requirements_blocking_count": evidence_requirements_blocking_count,
        "evidence_requirements": evidence_requirements,
        "primary_blocker_code": blocker_code,
        "next_operator_action": next_action,
        "live_review_evidence_eligible": False,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _shadow_runtime_orchestration_status(
    report: dict[str, Any] | None,
    *,
    shadow_runtime_harness_status: dict[str, Any],
    shadow_persistent_runtime_status: dict[str, Any],
) -> dict[str, Any]:
    def safe_count(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return parsed if parsed >= 0 else 0

    base = {
        "title": "Runtime Orchestration Guard",
        "status": "NOT_LOADED",
        "severity": "WARNING",
        "color_token": "yellow",
        "truth_role": "dashboard_serving_truth",
        "source": "NOT_LOADED",
        "orchestration_decision": "BLOCK_LONG_RUN_EVIDENCE",
        "source_validation_status": "NOT_LOADED",
        "source_runtime_hash_pairing_verified": False,
        "source_binding_count": 0,
        "persistent_runtime_status": shadow_persistent_runtime_status.get("status", "NOT_LOADED"),
        "short_window_harness_status": shadow_runtime_harness_status.get("status", "NOT_LOADED"),
        "observed_actual_runtime_seconds": 0,
        "observed_actual_cycle_count": 0,
        "observed_evidence_window_count": 0,
        "actual_long_run_runtime_present": False,
        "long_run_evidence_eligible": False,
        "scorecard_input_eligible": False,
        "promotion_eligible": False,
        "runtime_evidence_role": "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN",
        "optimizer_ranking_action": "BLOCK_RANKING",
        "primary_blocker_code": "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        "one_line_summary": "No runtime orchestration guard report is loaded. Long-run evidence remains missing.",
        "next_operator_action": "Generate the runtime orchestration guard report before treating PAPER/SHADOW runtime evidence as paired.",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
    }
    if not isinstance(report, dict):
        return base

    unsafe_live_or_scale = any(
        report.get(field) is not False
        for field in (
            "actual_long_run_runtime_present",
            "long_run_evidence_eligible",
            "scorecard_input_eligible",
            "promotion_eligible",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
            "order_adapter_called",
        )
    )
    invalid_counts = any(
        safe_count(report.get(field)) != 0
        for field in ("observed_actual_runtime_seconds", "observed_actual_cycle_count", "observed_evidence_window_count")
    )
    expected_contract = (
        report.get("schema_id") == "trader1.shadow_observation_runtime_orchestration_report.v1"
        and report.get("orchestration_status") == "BLOCKED"
        and report.get("orchestration_decision") == "BLOCK_LONG_RUN_EVIDENCE"
        and report.get("source_validation_status") == "PASS"
        and report.get("source_hashes_verified") is True
        and report.get("source_runtime_hash_pairing_verified") is True
        and report.get("source_scope_match") is True
        and report.get("source_binding_count") == 2
        and report.get("persistent_stub_not_long_run_confirmed") is True
        and report.get("short_window_harness_not_long_run_confirmed") is True
        and report.get("runtime_evidence_role") == "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN"
        and report.get("optimizer_ranking_action") == "BLOCK_RANKING"
        and report.get("dashboard_display_truth_only") is True
        and report.get("dashboard_visibility_status") == "VISIBLE_AS_BLOCKED_LONG_RUN_REQUIREMENTS"
        and report.get("primary_blocker_code") == "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
    )

    status = "BOUNDARY_VERIFIED"
    severity = "NORMAL"
    color_token = "blue"
    summary = "Runtime sources are paired and verified for display only. This is not long-run evidence and cannot enable LIVE."
    next_action = str(report.get("next_operator_action") or "Collect actual long-run PAPER/SHADOW evidence separately; live orders remain blocked.")
    blocker_code = "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
    if unsafe_live_or_scale:
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        summary = "Runtime orchestration attempted live, scorecard, promotion, order, or scale permission."
        next_action = "Keep live disabled and regenerate the runtime orchestration report from non-live sources."
        blocker_code = "LIVE_FINAL_GUARD_FAILED"
    elif invalid_counts:
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        summary = "Runtime orchestration tried to claim observed long-run runtime, cycles, or evidence windows."
        next_action = "Collect actual long-run PAPER/SHADOW evidence separately; this orchestration report must stay blocked."
        blocker_code = "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
    elif not expected_contract:
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        summary = "Runtime orchestration report is contract-mismatched or source pairing is not verified."
        next_action = "Regenerate the orchestration report from the exact persistent runtime and short-window harness sources."
        blocker_code = str(report.get("primary_blocker_code") or "SCHEMA_IDENTITY_MISMATCH")
    elif _freshness_from_generated_at(report) != "PASS":
        status = "STALE"
        severity = "WARNING"
        color_token = "yellow"
        summary = "Runtime orchestration guard is stale. It remains display-only and cannot support live review."
        next_action = "Regenerate the runtime orchestration guard before operator review."
        blocker_code = "LATENCY_TTL_EXPIRED"

    base.update(
        {
            "status": status,
            "severity": severity,
            "color_token": color_token,
            "source": "runtime_orchestration_report.json",
            "orchestration_decision": str(report.get("orchestration_decision") or "BLOCK_LONG_RUN_EVIDENCE"),
            "source_validation_status": str(report.get("source_validation_status") or "NOT_LOADED"),
            "source_runtime_hash_pairing_verified": report.get("source_runtime_hash_pairing_verified") is True,
            "source_binding_count": safe_count(report.get("source_binding_count")),
            "persistent_runtime_status": shadow_persistent_runtime_status.get("status", "NOT_LOADED"),
            "short_window_harness_status": shadow_runtime_harness_status.get("status", "NOT_LOADED"),
            "observed_actual_runtime_seconds": safe_count(report.get("observed_actual_runtime_seconds")),
            "observed_actual_cycle_count": safe_count(report.get("observed_actual_cycle_count")),
            "observed_evidence_window_count": safe_count(report.get("observed_evidence_window_count")),
            "actual_long_run_runtime_present": False,
            "long_run_evidence_eligible": False,
            "scorecard_input_eligible": False,
            "promotion_eligible": False,
            "runtime_evidence_role": str(report.get("runtime_evidence_role") or "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN"),
            "optimizer_ranking_action": str(report.get("optimizer_ranking_action") or "BLOCK_RANKING"),
            "primary_blocker_code": blocker_code,
            "one_line_summary": summary,
            "next_operator_action": next_action,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "order_adapter_called": False,
        }
    )
    return base


def _operator_action_summary(
    *,
    primary_blocker: str | None,
    operation_status: dict[str, Any],
    long_run_operator_summary: dict[str, Any],
    profitability_maturity: dict[str, Any],
    risk_exposure_snapshot: dict[str, Any],
    execution_feedback_snapshot: dict[str, Any],
    decision_trace: dict[str, Any],
) -> dict[str, Any]:
    blocker = primary_blocker or "LIVE_READY_MISSING"
    operation_severity = operation_status.get("severity")
    long_run_status = long_run_operator_summary.get("status")
    risk_status = risk_exposure_snapshot.get("status")
    maturity_status = profitability_maturity.get("status")
    feedback_status = execution_feedback_snapshot.get("status")

    if operation_severity == "ERROR" or risk_status == "BLOCKED" or feedback_status == "BLOCKED":
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        primary_action = "STOP_AND_INSPECT"
        workflow_step = "INSPECT_DASHBOARD"
        label = "Stop review and inspect the blocker"
        next_operator_action = "Keep trading disabled and inspect the red blocker before continuing PAPER review."
    elif long_run_status == "STALE" or risk_status == "STALE" or feedback_status == "STALE":
        status = "REFRESH_REQUIRED"
        severity = "WARNING"
        color_token = "yellow"
        primary_action = "REFRESH_DASHBOARD"
        workflow_step = "RUN_PAPER"
        label = "Refresh PAPER status"
        next_operator_action = "Rerun the PAPER launcher to refresh heartbeat, dashboard sources, and portfolio values."
    elif maturity_status == "SCORECARD_INPUT_READY" or feedback_status == "READY_FOR_PAPER_RANKING_REVIEW":
        status = "PAPER_REVIEW_READY"
        severity = "NORMAL"
        color_token = "blue"
        primary_action = "REVIEW_PAPER_EVIDENCE"
        workflow_step = "INSPECT_DASHBOARD"
        label = "Review PAPER evidence only"
        next_operator_action = "Review PAPER/SHADOW evidence and blockers. Live review remains blocked until external evidence exists."
    elif long_run_status in {"RUNNING_NOW", "DISPLAY_HISTORY_STABLE", "VALIDATED_STABLE"} and risk_status == "LOW_RISK":
        status = "PAPER_MONITORING"
        severity = "NORMAL"
        color_token = "green" if long_run_status in {"DISPLAY_HISTORY_STABLE", "VALIDATED_STABLE"} else "blue"
        primary_action = "CONTINUE_PAPER"
        workflow_step = "COLLECT_EVIDENCE"
        label = "Continue PAPER monitoring"
        next_operator_action = "Keep PAPER running, inspect dashboard evidence, and do not use LIVE until external live-review evidence is present."
    else:
        status = "ACTION_REQUIRED"
        severity = "WARNING"
        color_token = "yellow"
        primary_action = "RESOLVE_BLOCKER"
        workflow_step = "INSPECT_DASHBOARD"
        label = "Resolve dashboard blocker"
        next_operator_action = "Resolve the visible blocker, then rerun PAPER and recheck this dashboard."

    return {
        "title": "Operator Next Action",
        "status": status,
        "severity": severity,
        "color_token": color_token,
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "workflow_step": workflow_step,
        "primary_action": primary_action,
        "primary_action_label": label,
        "primary_blocker_code": blocker,
        "one_line_blocker": f"{blocker}: live orders remain blocked.",
        "next_operator_action": next_operator_action,
        "safe_to_continue_paper": status in {"PAPER_MONITORING", "PAPER_REVIEW_READY"},
        "paper_review_only": True,
        "live_review_blocked": True,
        "emergency_control_visible": True,
        "dangerous_controls_present": False,
        "decision_final_action": str(decision_trace.get("final_action", "NO_TRADE")),
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _workflow_step(
    step_id: str,
    label: str,
    status: str,
    detail: str,
    action_kind: str,
    current: bool,
) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "label": label,
        "status": status,
        "detail": detail,
        "action_kind": action_kind,
        "current": current,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _operator_workflow_summary(
    *,
    operator_action_summary: dict[str, Any],
    long_run_operator_summary: dict[str, Any],
    profitability_maturity: dict[str, Any],
    execution_feedback_snapshot: dict[str, Any],
) -> dict[str, Any]:
    action_status = operator_action_summary.get("status")
    current_step = str(operator_action_summary.get("workflow_step", "INSPECT_DASHBOARD"))
    if action_status == "BLOCKED":
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        summary = "Operator flow is blocked until the red dashboard issue is inspected."
    elif action_status == "REFRESH_REQUIRED":
        status = "REFRESH_REQUIRED"
        severity = "WARNING"
        color_token = "yellow"
        summary = "Refresh PAPER sources before continuing the dashboard review."
    elif action_status == "PAPER_REVIEW_READY":
        status = "PAPER_REVIEW"
        severity = "NORMAL"
        color_token = "blue"
        summary = "PAPER evidence can be reviewed, but LIVE remains blocked."
    elif action_status == "PAPER_MONITORING":
        status = "COLLECTING_EVIDENCE"
        severity = "NORMAL"
        color_token = "green" if long_run_operator_summary.get("status") in {"DISPLAY_HISTORY_STABLE", "VALIDATED_STABLE"} else "blue"
        summary = "PAPER is running; keep collecting evidence and reviewing blockers."
    else:
        status = "ACTION_REQUIRED"
        severity = "WARNING"
        color_token = "yellow"
        summary = "Resolve the visible dashboard blocker before continuing."

    run_paper_status = "CURRENT" if current_step == "RUN_PAPER" else "DONE"
    if status == "BLOCKED":
        inspect_status = "CURRENT"
    elif current_step == "INSPECT_DASHBOARD":
        inspect_status = "CURRENT"
    elif current_step in {"COLLECT_EVIDENCE", "LIVE_REVIEW_BLOCKED"}:
        inspect_status = "DONE"
    else:
        inspect_status = "WAITING"
    if current_step == "COLLECT_EVIDENCE":
        collect_status = "CURRENT"
    elif status == "PAPER_REVIEW":
        collect_status = "DONE"
    elif status == "BLOCKED":
        collect_status = "WAITING"
    else:
        collect_status = "WAITING"

    steps = [
        _workflow_step(
            "RUN_PAPER",
            "Run PAPER",
            run_paper_status,
            "Start or refresh the PAPER launcher and keep live orders blocked.",
            "REFRESH_DASHBOARD" if current_step == "RUN_PAPER" else "CONTINUE_PAPER",
            current_step == "RUN_PAPER",
        ),
        _workflow_step(
            "INSPECT_DASHBOARD",
            "Inspect Dashboard",
            inspect_status,
            "Check operation, portfolio, risk, no-trade reason, and source freshness.",
            "RESOLVE_BLOCKER" if status in {"ACTION_REQUIRED", "BLOCKED"} else "REVIEW_PAPER_EVIDENCE",
            current_step == "INSPECT_DASHBOARD" or status == "BLOCKED",
        ),
        _workflow_step(
            "COLLECT_EVIDENCE",
            "Collect Evidence",
            collect_status,
            "Accumulate PAPER/SHADOW samples, execution feedback, and strategy evidence.",
            "CONTINUE_PAPER",
            current_step == "COLLECT_EVIDENCE",
        ),
        _workflow_step(
            "LIVE_REVIEW_BLOCKED",
            "LIVE Review Blocked",
            "BLOCKED",
            "External approval, API verification, manual test evidence, and burn-in evidence are still required.",
            "RESOLVE_BLOCKER",
            False,
        ),
    ]

    return {
        "title": "Operator Workflow",
        "status": status,
        "severity": severity,
        "color_token": color_token,
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "current_step": current_step,
        "step_count": len(steps),
        "summary": summary,
        "paper_evidence_status": str(profitability_maturity.get("status", "COLLECTING")),
        "execution_feedback_status": str(execution_feedback_snapshot.get("status", "COLLECTING")),
        "live_review_blocked": True,
        "live_blocker_code": "LIVE_READY_MISSING",
        "steps": steps,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _profitability_check(
    *,
    check_id: str,
    label: str,
    observed_count: int,
    required_count: int,
    message: str,
    override_status: str | None = None,
) -> dict[str, Any]:
    status = override_status or ("PASS" if observed_count >= required_count else "MISSING")
    return {
        "check_id": check_id,
        "label": label,
        "status": status,
        "observed_count": max(observed_count, 0),
        "required_count": max(required_count, 0),
        "message": message,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _profitability_evidence_progress(
    *,
    paper_samples: int,
    shadow_samples: int,
    min_samples: int,
    cost_count: int,
    entry_count: int,
    no_trade_count: int,
    override_status: str | None = None,
) -> tuple[list[dict[str, Any]], int, str, str]:
    sample_required = max(min_samples, 1)
    checklist = [
        _profitability_check(
            check_id="PAPER_SAMPLES",
            label="PAPER samples",
            observed_count=paper_samples,
            required_count=sample_required,
            message="PAPER samples used only for paper/shadow scorecard review.",
            override_status=override_status,
        ),
        _profitability_check(
            check_id="SHADOW_SAMPLES",
            label="SHADOW samples",
            observed_count=shadow_samples,
            required_count=sample_required,
            message="SHADOW comparison must match the same scope before ranking.",
            override_status=override_status,
        ),
        _profitability_check(
            check_id="COST_EVIDENCE",
            label="Cost evidence",
            observed_count=cost_count,
            required_count=1,
            message="Fee, spread, slippage, and impact evidence must exist before ranking.",
            override_status=override_status,
        ),
        _profitability_check(
            check_id="ENTRY_REASON",
            label="Entry reasons",
            observed_count=entry_count,
            required_count=1,
            message="Accepted entries must have traceable reasons.",
            override_status=override_status,
        ),
        _profitability_check(
            check_id="NO_TRADE_REASON",
            label="No-trade reasons",
            observed_count=no_trade_count,
            required_count=1,
            message="Rejected entries must have visible no-trade reasons.",
            override_status=override_status,
        ),
    ]
    if override_status == "STALE":
        return checklist, 0, "STALE", "Evidence source is stale; progress is not trusted."
    if override_status == "BLOCKED":
        return checklist, 0, "BLOCKED", "Evidence source is blocked; fix scope or live-flag drift first."
    passed = sum(1 for check in checklist if check["status"] == "PASS")
    progress_pct = int((passed / len(checklist)) * 100)
    if progress_pct == 100:
        progress_status = "READY"
    elif progress_pct == 0:
        progress_status = "NOT_STARTED"
    else:
        progress_status = "IN_PROGRESS"
    return checklist, progress_pct, progress_status, f"{passed}/{len(checklist)} evidence checks complete"


def _actual_runtime_source_projection(evidence: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(evidence, dict):
        return {
            "actual_runtime_source_status": "MISSING",
            "actual_runtime_source_count": 0,
            "actual_runtime_source_summary": "No validated non-live persistent runtime source is loaded.",
            "long_run_evidence_eligible": False,
            "long_run_blocker_code": "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        }
    raw_status = str(evidence.get("actual_runtime_source_status") or "MISSING").upper()
    source_status = raw_status if raw_status in PROFITABILITY_ACTUAL_RUNTIME_SOURCE_STATUSES else "MISSING"
    source_ids = evidence.get("actual_runtime_source_evidence_ids") or []
    source_count = len(source_ids) if isinstance(source_ids, list) else 0
    long_run_eligible = evidence.get("long_run_evidence_eligible") is True
    blocker_code = evidence.get("long_run_blocker_code")
    if long_run_eligible:
        summary = "Validated non-live persistent runtime source is attached to long-run evidence."
    elif source_status == "VALIDATED_NON_LIVE_RUNTIME" and source_count > 0:
        summary = "Runtime source exists, but other long-run evidence requirements still block review."
    elif source_count > 0:
        summary = "Runtime source ids are present but not validated as non-live persistent runtime evidence."
    else:
        summary = "Long-run evidence is blocked until validated non-live persistent runtime source evidence is attached."
    return {
        "actual_runtime_source_status": source_status,
        "actual_runtime_source_count": source_count,
        "actual_runtime_source_summary": summary,
        "long_run_evidence_eligible": long_run_eligible,
        "long_run_blocker_code": blocker_code or "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
    }


def _profitability_maturity_component(
    component_id: str,
    status: str,
    priority: str,
    message: str,
    *,
    next_required_evidence: str | None = None,
    paper_scorecard_input_eligible: bool | None = None,
    long_run_evidence_eligible: bool = False,
    long_run_blocker_code: str | None = None,
) -> dict[str, Any]:
    if paper_scorecard_input_eligible is None:
        paper_scorecard_input_eligible = status in {"PAPER_SCORECARD_EVIDENCE_PASS", "PAPER_SCORECARD_INPUT_ONLY"}
    if not long_run_evidence_eligible and not long_run_blocker_code:
        long_run_blocker_code = "PROFITABILITY_EVIDENCE_MATURITY"
    return {
        "component_id": component_id,
        "status": status,
        "priority": priority,
        "operator_message": message,
        "next_required_evidence": next_required_evidence or PROFITABILITY_MATURITY_NEXT_EVIDENCE.get(
            component_id,
            "Collect scoped PAPER/SHADOW evidence and keep live disabled.",
        ),
        "paper_scorecard_input_eligible": bool(paper_scorecard_input_eligible),
        "long_run_evidence_eligible": bool(long_run_evidence_eligible),
        "long_run_blocker_code": long_run_blocker_code,
        "live_review_blocker": True,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _profitability_maturity_components(
    *,
    paper_samples: int,
    shadow_samples: int,
    min_samples: int,
    cost_count: int,
    entry_count: int,
    no_trade_count: int,
    scorecard_input_eligible: bool,
    optimizer_ranking_action: str,
    override_status: str | None = None,
) -> tuple[list[dict[str, Any]], int, int, str, str]:
    if override_status == "STALE":
        components = [
            _profitability_maturity_component(component_id, "STALE", "HIGH", "Refresh PAPER/SHADOW evidence before review.")
            for component_id in PROFITABILITY_MATURITY_COMPONENT_IDS
        ]
        return components, 0, len(components), "STALE", "Evidence source is stale; all profitability maturity components are blocked from review and live remains blocked."
    if override_status == "BLOCKED":
        components = [
            _profitability_maturity_component(component_id, "BLOCKED", "HIGH", "Fix scope, validator, or live-flag drift before review.")
            for component_id in PROFITABILITY_MATURITY_COMPONENT_IDS
        ]
        return components, 0, len(components), "BLOCKED", "Evidence source is blocked; all profitability maturity components remain fail-closed and live remains blocked."

    paper_shadow_pass = min_samples > 0 and paper_samples >= min_samples and shadow_samples >= min_samples
    reason_pass = entry_count > 0 and no_trade_count > 0
    cost_pass = cost_count > 0
    optimizer_objective_pass = scorecard_input_eligible and optimizer_ranking_action == "ALLOW_RANKING"
    rows = [
        _profitability_maturity_component(
            "strategy_entry_exit_no_trade",
            "PAPER_SCORECARD_EVIDENCE_PASS" if reason_pass else "EVIDENCE_MISSING",
            "HIGH",
            "Entry and no-trade reasons are present for PAPER scorecard review only."
            if reason_pass
            else "Entry, exit, and no-trade reason evidence is still missing or incomplete.",
        ),
        _profitability_maturity_component(
            "symbol_selection_regime",
            "EVIDENCE_MISSING",
            "HIGH",
            "Liquidity, volatility, spread, depth, and regime fit evidence is still required.",
        ),
        _profitability_maturity_component(
            "vwap_trend_breakout",
            "EVIDENCE_MISSING",
            "HIGH",
            "VWAP, trend pullback, and breakout/retest evidence is not yet regime-proven.",
        ),
        _profitability_maturity_component(
            "risk_sizing_exposure",
            "RECORDED_GAP",
            "HIGH",
            "Risk sizing quality remains recorded as a gap; scale-up is blocked.",
        ),
        _profitability_maturity_component(
            "execution_slippage_fee_impact",
            "PAPER_SCORECARD_EVIDENCE_PASS" if cost_pass else "EVIDENCE_MISSING",
            "HIGH",
            "Cost evidence is present for PAPER scorecard review only."
            if cost_pass
            else "Fee, spread, slippage, impact, and latency evidence is still missing.",
        ),
        _profitability_maturity_component(
            "optimizer_objective_net_ev_after_cost",
            "PAPER_SCORECARD_EVIDENCE_PASS" if optimizer_objective_pass else "EVIDENCE_MISSING",
            "HIGH",
            "Optimizer objective can be reviewed as PAPER scorecard input only."
            if optimizer_objective_pass
            else "Net EV after cost is not ready for optimizer ranking review.",
        ),
        _profitability_maturity_component(
            "overfit_oos_walk_forward",
            "EVIDENCE_MISSING",
            "HIGH",
            "OOS, walk-forward, bootstrap, and concentration evidence is still required.",
        ),
        _profitability_maturity_component(
            "convergence_memory_failure_learning",
            "EVIDENCE_MISSING",
            "HIGH",
            "Append-auditable convergence memory and repeated-failure evidence is still required.",
        ),
        _profitability_maturity_component(
            "paper_shadow_evidence_accumulation",
            "PAPER_SCORECARD_EVIDENCE_PASS" if paper_shadow_pass else "EVIDENCE_MISSING",
            "HIGH",
            "PAPER/SHADOW sample counts meet scorecard input minimums only."
            if paper_shadow_pass
            else "PAPER/SHADOW sample counts are still below the scorecard input minimum.",
        ),
        _profitability_maturity_component(
            "dashboard_operator_profitability_visibility",
            "PARTIAL_PATCHED",
            "MEDIUM",
            "Dashboard visibility is patched, but it remains display truth only.",
        ),
    ]
    paper_scorecard_pass_count = sum(1 for row in rows if row["status"] == "PAPER_SCORECARD_EVIDENCE_PASS")
    maturity_gap_count = len(rows) - paper_scorecard_pass_count
    if scorecard_input_eligible:
        gap_status = "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN"
        gap_summary = (
            f"{paper_scorecard_pass_count}/{len(rows)} components have PAPER scorecard evidence; "
            f"{maturity_gap_count} maturity gaps remain. This is not LIVE_READY."
        )
    else:
        gap_status = "OPEN_HIGH"
        gap_summary = (
            f"{paper_scorecard_pass_count}/{len(rows)} components have PAPER scorecard evidence; "
            f"{maturity_gap_count} maturity gaps remain before PAPER ranking review. Live remains blocked."
        )
    return rows, paper_scorecard_pass_count, maturity_gap_count, gap_status, gap_summary


def _rollup_component_status(raw_status: Any) -> str:
    status = str(raw_status or "EVIDENCE_MISSING").upper()
    if status in PROFITABILITY_MATURITY_COMPONENT_STATUSES:
        return status
    return "BLOCKED"


def _rollup_component_message(component: dict[str, Any]) -> str:
    maturity_status = str(component.get("maturity_status") or "EVIDENCE_MISSING").replace("_", " ").lower()
    evidence_status = str(component.get("evidence_status") or "UNTESTED")
    validator_status = str(component.get("validator_status") or "UNTESTED")
    samples = component.get("sample_count", 0)
    required = component.get("min_required_sample_count", 0)
    return (
        f"Rollup says {maturity_status}; evidence={evidence_status}, "
        f"validator={validator_status}, samples={samples}/{required}."
    )


def _profitability_maturity_from_rollup(
    *,
    base: dict[str, Any],
    rollup_report: dict[str, Any],
) -> dict[str, Any]:
    components = rollup_report.get("components", [])
    required_count = int(rollup_report.get("required_component_count", 0) or 0)
    component_count = int(rollup_report.get("component_count", 0) or 0)
    coverage_complete = rollup_report.get("coverage_complete") is True and rollup_report.get("all_component_ids_present") is True
    live_flag_drift = any(
        rollup_report.get(flag) is True
        for flag in (
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
            "live_permission_created",
            "profitability_guarantee_created",
            "optimizer_live_mutation_detected",
            "convergence_live_mutation_detected",
            "live_review_eligible",
            "scale_up_eligible",
        )
    )
    component_ids = [component.get("component_id") for component in components if isinstance(component, dict)]
    component_id_mismatch = component_ids != list(PROFITABILITY_MATURITY_COMPONENT_IDS)
    component_live_drift = any(
        isinstance(component, dict)
        and (
            component.get("live_review_eligible") is True
            or component.get("scale_up_allowed") is True
            or not component.get("next_required_evidence")
        )
        for component in components
    )
    blocked = (
        rollup_report.get("schema_id") != "trader1.profitability_evidence_maturity_rollup.v1"
        or required_count != len(PROFITABILITY_MATURITY_COMPONENT_IDS)
        or component_count != len(PROFITABILITY_MATURITY_COMPONENT_IDS)
        or not coverage_complete
        or component_id_mismatch
        or live_flag_drift
        or component_live_drift
    )

    if blocked:
        blocked_components, component_pass_count, gap_count, gap_status, gap_summary = _profitability_maturity_components(
            paper_samples=0,
            shadow_samples=0,
            min_samples=0,
            cost_count=0,
            entry_count=0,
            no_trade_count=0,
            scorecard_input_eligible=False,
            optimizer_ranking_action="BLOCK_RANKING",
            override_status="BLOCKED",
        )
        return {
            **base,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "evidence_source": "profitability_evidence_maturity_rollup.json",
            "rollup_source": "profitability_evidence_maturity_rollup.json",
            "rollup_source_status": "BLOCKED",
            "rollup_id": rollup_report.get("rollup_id"),
            "rollup_status": str(rollup_report.get("status") or "BLOCKED"),
            "rollup_component_count": component_count,
            "rollup_required_component_count": required_count,
            "rollup_coverage_complete": False,
            "evidence_status": "FAIL",
            "evidence_progress_status": "BLOCKED",
            "evidence_progress_pct": 0,
            "evidence_progress_summary": "Profitability rollup failed coverage, component, or live-flag safety checks.",
            "maturity_gap_status": gap_status,
            "maturity_gap_count": gap_count,
            "maturity_component_count": len(blocked_components),
            "paper_scorecard_component_pass_count": component_pass_count,
            "maturity_gap_summary": gap_summary,
            "maturity_components": blocked_components,
            "scorecard_scope": "BLOCKED_DISPLAY_ONLY",
            "operator_warning": "Blocked rollup is not LIVE_READY and cannot place or allow live orders.",
            "primary_blocker_code": "LIVE_FINAL_GUARD_FAILED",
            "primary_blocker_message": "Profitability maturity rollup is invalid or attempted forbidden live/scale permission.",
            "next_action": "Repair the rollup evidence before using it for dashboard review.",
        }

    projected_components = [
        _profitability_maturity_component(
            str(component["component_id"]),
            _rollup_component_status(component.get("maturity_status")),
            "HIGH" if component.get("primary_blocker_code") else "MEDIUM",
            _rollup_component_message(component),
            next_required_evidence=str(component.get("next_required_evidence")),
            paper_scorecard_input_eligible=component.get("paper_scorecard_input_eligible") is True,
            long_run_evidence_eligible=component.get("long_run_evidence_eligible") is True,
            long_run_blocker_code=component.get("long_run_blocker_code"),
        )
        for component in components
        if isinstance(component, dict)
    ]
    input_component_count = sum(
        1
        for component in projected_components
        if component.get("paper_scorecard_input_eligible") is True
    )
    gap_count = len(projected_components) - input_component_count
    gap_summary = (
        f"{input_component_count}/{len(projected_components)} components have PAPER scorecard input evidence; "
        f"{gap_count} maturity gaps remain. This is not LIVE_READY."
    )
    return {
        **base,
        "status": "COLLECTING",
        "severity": "WARNING",
        "color_token": "yellow",
        "evidence_source": "profitability_evidence_maturity_rollup.json",
        "rollup_source": "profitability_evidence_maturity_rollup.json",
        "rollup_source_status": "LOADED",
        "rollup_id": rollup_report.get("rollup_id"),
        "rollup_status": str(rollup_report.get("status") or "BLOCKED_FOR_PROFITABILITY_EVIDENCE_MATURITY"),
        "rollup_component_count": component_count,
        "rollup_required_component_count": required_count,
        "rollup_coverage_complete": True,
        "evidence_status": "WARN",
        "sample_summary": f"Rollup components {component_count}/{required_count}; PAPER/SHADOW evidence still maturing",
        "evidence_progress_status": "IN_PROGRESS" if input_component_count else "NOT_STARTED",
        "evidence_progress_pct": 0,
        "evidence_progress_summary": (
            f"Rollup loaded: {input_component_count}/{len(projected_components)} components have PAPER scorecard input only; "
            "runtime checklist counts still require PAPER/SHADOW evidence collection."
        ),
        "maturity_gap_status": "OPEN_HIGH",
        "maturity_gap_count": gap_count,
        "maturity_component_count": len(projected_components),
        "paper_scorecard_component_pass_count": input_component_count,
        "maturity_gap_summary": gap_summary,
        "maturity_components": projected_components,
        "scorecard_scope": "PAPER_EVIDENCE_COLLECTION_ONLY",
        "live_readiness_status": "NOT_LIVE_READY",
        "operator_warning": "Rollup evidence is not LIVE_READY and cannot place or allow live orders.",
        "scorecard_input_eligible": False,
        "optimizer_ranking_action": "BLOCK_RANKING",
        "primary_blocker_code": rollup_report.get("primary_blocker_code") or "PROFITABILITY_EVIDENCE_MATURITY",
        "primary_blocker_message": "Profitability evidence rollup is loaded for operator review only; live remains blocked.",
        "next_action": rollup_report.get("next_operator_action")
        or "Collect PAPER/SHADOW scorecard evidence while live and scale-up remain blocked.",
    }


def _candidate_scorecard_projection(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    candidate_scorecard: dict[str, Any] | None,
    summary_freshness: str,
) -> dict[str, Any]:
    base = {
        "candidate_scorecard_source": "NOT_LOADED",
        "candidate_scorecard_status": "NOT_LOADED",
        "candidate_scorecard_id": None,
        "candidate_scorecard_candidate_id": None,
        "candidate_scorecard_strategy_id": None,
        "candidate_scorecard_symbol": None,
        "candidate_scorecard_objective_basis": "NET_EV_AFTER_COST",
        "candidate_scorecard_net_ev_after_cost_bps": None,
        "candidate_scorecard_net_ev_after_cost_display": "UNVERIFIED",
        "candidate_scorecard_ranking_eligible": False,
        "candidate_scorecard_scope": "PAPER_EVIDENCE_COLLECTION_ONLY",
        "candidate_scorecard_primary_blocker_code": "SCORECARD_NOT_LOADED",
        "candidate_scorecard_blocker_summary": "No PAPER candidate scorecard is loaded for this dashboard.",
        "candidate_scorecard_next_action": "Run the Upbit PAPER runtime scorecard bridge, then refresh this dashboard.",
    }
    if summary_freshness != "PASS":
        return {
            **base,
            "candidate_scorecard_status": "STALE",
            "candidate_scorecard_scope": "STALE_DISPLAY_ONLY",
            "candidate_scorecard_primary_blocker_code": "LATENCY_TTL_EXPIRED",
            "candidate_scorecard_blocker_summary": "Dashboard summary is stale; candidate scorecard display is not trusted.",
            "candidate_scorecard_next_action": "Rerun PAPER to refresh dashboard sources before reviewing scorecard values.",
        }
    if not isinstance(candidate_scorecard, dict):
        return base

    blockers = candidate_scorecard.get("blockers", [])
    if not isinstance(blockers, list):
        blockers = []
    blocker_codes = [
        str(blocker.get("code"))
        for blocker in blockers
        if isinstance(blocker, dict) and blocker.get("code")
    ]
    first_blocker = blocker_codes[0] if blocker_codes else "LIVE_READY_MISSING"
    net_ev = candidate_scorecard.get("net_ev_after_cost_bps")
    try:
        net_ev_value = float(net_ev)
        net_ev_display = f"{net_ev_value:.2f} bps"
    except (TypeError, ValueError):
        net_ev_value = None
        net_ev_display = "UNVERIFIED"
    scorecard_scope = str(candidate_scorecard.get("scorecard_scope") or "PAPER_EVIDENCE_COLLECTION_ONLY")
    ranking_eligible = candidate_scorecard.get("ranking_eligible") is True
    live_flag_drift = any(
        candidate_scorecard.get(flag) is True
        for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "can_submit_order")
    )
    scope_matches = (
        candidate_scorecard.get("exchange") == exchange
        and candidate_scorecard.get("market_type") == market_type
        and candidate_scorecard.get("mode") == mode
        and candidate_scorecard.get("session_id") == session_id
    )
    freshness = _freshness_from_generated_at(candidate_scorecard)
    source_evidence_ids = candidate_scorecard.get("source_evidence_ids", [])
    source_evidence_ids = source_evidence_ids if isinstance(source_evidence_ids, list) else []
    projection = {
        **base,
        "candidate_scorecard_source": "candidate_scorecard.json",
        "candidate_scorecard_id": candidate_scorecard.get("scorecard_id"),
        "candidate_scorecard_candidate_id": candidate_scorecard.get("candidate_id"),
        "candidate_scorecard_strategy_id": candidate_scorecard.get("strategy_id"),
        "candidate_scorecard_symbol": candidate_scorecard.get("symbol"),
        "candidate_scorecard_objective_basis": str(candidate_scorecard.get("objective_basis") or "NET_EV_AFTER_COST"),
        "candidate_scorecard_net_ev_after_cost_bps": net_ev_value,
        "candidate_scorecard_net_ev_after_cost_display": net_ev_display,
        "candidate_scorecard_ranking_eligible": ranking_eligible,
        "candidate_scorecard_scope": scorecard_scope if scorecard_scope in PROFITABILITY_SCORECARD_SCOPES else "BLOCKED_DISPLAY_ONLY",
        "candidate_scorecard_primary_blocker_code": first_blocker,
        "candidate_scorecard_blocker_summary": ", ".join(blocker_codes[:4]) if blocker_codes else "PAPER ranking input only; live remains blocked.",
    }
    if live_flag_drift:
        return {
            **projection,
            "candidate_scorecard_status": "BLOCKED",
            "candidate_scorecard_scope": "BLOCKED_DISPLAY_ONLY",
            "candidate_scorecard_ranking_eligible": False,
            "candidate_scorecard_primary_blocker_code": "LIVE_FINAL_GUARD_FAILED",
            "candidate_scorecard_blocker_summary": "Candidate scorecard attempted to carry live, order, or scale-up permission.",
            "candidate_scorecard_next_action": "Block this artifact, inspect the scorecard writer, and keep live orders disabled.",
        }
    if not scope_matches:
        return {
            **projection,
            "candidate_scorecard_status": "BLOCKED",
            "candidate_scorecard_scope": "BLOCKED_DISPLAY_ONLY",
            "candidate_scorecard_ranking_eligible": False,
            "candidate_scorecard_primary_blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "candidate_scorecard_blocker_summary": "Candidate scorecard scope does not match this dashboard session.",
            "candidate_scorecard_next_action": "Regenerate the scorecard for the exact exchange, market, mode, and session shown here.",
        }
    if freshness != "PASS":
        return {
            **projection,
            "candidate_scorecard_status": "STALE",
            "candidate_scorecard_scope": "STALE_DISPLAY_ONLY",
            "candidate_scorecard_ranking_eligible": False,
            "candidate_scorecard_primary_blocker_code": "LATENCY_TTL_EXPIRED",
            "candidate_scorecard_blocker_summary": "Candidate scorecard is stale and cannot be trusted for review.",
            "candidate_scorecard_next_action": "Rerun the PAPER scorecard bridge before reviewing candidate quality.",
        }
    if candidate_scorecard.get("live_readiness_status") != "NOT_LIVE_READY":
        return {
            **projection,
            "candidate_scorecard_status": "BLOCKED",
            "candidate_scorecard_scope": "BLOCKED_DISPLAY_ONLY",
            "candidate_scorecard_ranking_eligible": False,
            "candidate_scorecard_primary_blocker_code": "LIVE_FINAL_GUARD_FAILED",
            "candidate_scorecard_blocker_summary": "Candidate scorecard tried to look live-ready.",
            "candidate_scorecard_next_action": "Reject this artifact and keep live review blocked.",
        }
    if candidate_scorecard.get("objective_basis") != "NET_EV_AFTER_COST" or net_ev_value is None or not source_evidence_ids:
        return {
            **projection,
            "candidate_scorecard_status": "BLOCKED",
            "candidate_scorecard_scope": "BLOCKED_DISPLAY_ONLY",
            "candidate_scorecard_ranking_eligible": False,
            "candidate_scorecard_primary_blocker_code": "SCORECARD_EVIDENCE_INCOMPLETE",
            "candidate_scorecard_blocker_summary": "Candidate scorecard lacks net EV after cost or source evidence ids.",
            "candidate_scorecard_next_action": "Regenerate scorecard from a validated PAPER runtime cycle.",
        }
    if ranking_eligible and not blocker_codes and scorecard_scope == "PAPER_SCORECARD_INPUT_ONLY":
        return {
            **projection,
            "candidate_scorecard_status": "PAPER_RANKING_REVIEW_ONLY",
            "candidate_scorecard_primary_blocker_code": "LIVE_READY_MISSING",
            "candidate_scorecard_next_action": "Review this candidate as PAPER ranking input only; live and scale-up remain blocked.",
        }
    return {
        **projection,
        "candidate_scorecard_status": "PAPER_RANKING_BLOCKED",
        "candidate_scorecard_ranking_eligible": False,
        "candidate_scorecard_next_action": "Resolve scorecard blockers before PAPER ranking review; do not treat this as LIVE_READY.",
    }


def _profitability_maturity(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    paper_operation_gate_report: dict[str, Any] | None,
    profitability_maturity_rollup_report: dict[str, Any] | None,
    candidate_scorecard: dict[str, Any] | None,
    summary_freshness: str,
) -> dict[str, Any]:
    scorecard_projection = _candidate_scorecard_projection(
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        candidate_scorecard=candidate_scorecard,
        summary_freshness=summary_freshness,
    )
    base_checklist, base_progress_pct, base_progress_status, base_progress_summary = _profitability_evidence_progress(
        paper_samples=0,
        shadow_samples=0,
        min_samples=0,
        cost_count=0,
        entry_count=0,
        no_trade_count=0,
    )
    base_components, base_component_pass_count, base_gap_count, base_gap_status, base_gap_summary = _profitability_maturity_components(
        paper_samples=0,
        shadow_samples=0,
        min_samples=0,
        cost_count=0,
        entry_count=0,
        no_trade_count=0,
        scorecard_input_eligible=False,
        optimizer_ranking_action="BLOCK_RANKING",
    )
    base = {
        "title": "Strategy Evidence Maturity",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "evidence_source": "NOT_LOADED",
        "rollup_source": "NOT_LOADED",
        "rollup_source_status": "NOT_LOADED",
        "rollup_id": None,
        "rollup_status": "NOT_LOADED",
        "rollup_component_count": 0,
        "rollup_required_component_count": len(PROFITABILITY_MATURITY_COMPONENT_IDS),
        "rollup_coverage_complete": False,
        "evidence_status": "UNTESTED",
        "candidate_id": None,
        "strategy_id": None,
        "parameter_hash": None,
        "paper_sample_count": 0,
        "shadow_sample_count": 0,
        "min_required_samples": 0,
        "sample_summary": "No paper/shadow evidence loaded",
        **_actual_runtime_source_projection(None),
        "cost_evidence_status": "UNTESTED",
        "entry_reason_status": "UNTESTED",
        "no_trade_reason_status": "UNTESTED",
        "evidence_progress_status": base_progress_status,
        "evidence_progress_pct": base_progress_pct,
        "evidence_progress_summary": base_progress_summary,
        "evidence_checklist": base_checklist,
        "maturity_gap_status": base_gap_status,
        "maturity_gap_count": base_gap_count,
        "maturity_component_count": len(base_components),
        "paper_scorecard_component_pass_count": base_component_pass_count,
        "maturity_gap_summary": base_gap_summary,
        "maturity_components": base_components,
        "scorecard_scope": "PAPER_EVIDENCE_COLLECTION_ONLY",
        "live_readiness_status": "NOT_LIVE_READY",
        "operator_warning": "PAPER evidence is not LIVE_READY and cannot place or allow live orders.",
        **scorecard_projection,
        "scorecard_input_eligible": False,
        "optimizer_ranking_action": "BLOCK_RANKING",
        "primary_blocker_code": "HARD_TRUTH_MISSING",
        "primary_blocker_message": "Run operational PAPER and SHADOW evidence collection before scorecard review.",
        "next_action": "Run PAPER operational cycle until paper/shadow evidence is fresh, scoped, and reason-backed.",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    if summary_freshness != "PASS":
        stale_components, stale_component_pass_count, stale_gap_count, stale_gap_status, stale_gap_summary = _profitability_maturity_components(
            paper_samples=0,
            shadow_samples=0,
            min_samples=0,
            cost_count=0,
            entry_count=0,
            no_trade_count=0,
            scorecard_input_eligible=False,
            optimizer_ranking_action="BLOCK_RANKING",
            override_status="STALE",
        )
        return {
            **base,
            "status": "STALE",
            "severity": "WARNING",
            "color_token": "yellow",
            "evidence_status": "STALE",
            "evidence_progress_status": "STALE",
            "evidence_progress_pct": 0,
            "evidence_progress_summary": "Evidence source is stale; progress is not trusted.",
            "maturity_gap_status": stale_gap_status,
            "maturity_gap_count": stale_gap_count,
            "maturity_component_count": len(stale_components),
            "paper_scorecard_component_pass_count": stale_component_pass_count,
            "maturity_gap_summary": stale_gap_summary,
            "maturity_components": stale_components,
            "scorecard_scope": "STALE_DISPLAY_ONLY",
            "live_readiness_status": "NOT_LIVE_READY",
            "operator_warning": "Stale PAPER evidence is not LIVE_READY and cannot place or allow live orders.",
            "evidence_checklist": _profitability_evidence_progress(
                paper_samples=0,
                shadow_samples=0,
                min_samples=0,
                cost_count=0,
                entry_count=0,
                no_trade_count=0,
                override_status="STALE",
            )[0],
            "primary_blocker_code": "LATENCY_TTL_EXPIRED",
            "primary_blocker_message": "Dashboard summary is stale; evidence maturity cannot be trusted.",
            "next_action": "Rerun PAPER to refresh dashboard sources before reviewing evidence maturity.",
        }
    if not isinstance(paper_operation_gate_report, dict):
        if isinstance(profitability_maturity_rollup_report, dict):
            return _profitability_maturity_from_rollup(
                base=base,
                rollup_report=profitability_maturity_rollup_report,
            )
        if scorecard_projection["candidate_scorecard_source"] == "candidate_scorecard.json":
            evidence_status = "PASS" if scorecard_projection["candidate_scorecard_status"] in {"PAPER_RANKING_BLOCKED", "PAPER_RANKING_REVIEW_ONLY"} else "FAIL"
            return {
                **base,
                "status": "BLOCKED" if scorecard_projection["candidate_scorecard_status"] == "BLOCKED" else "COLLECTING",
                "severity": "ERROR" if scorecard_projection["candidate_scorecard_status"] == "BLOCKED" else "WARNING",
                "color_token": "red" if scorecard_projection["candidate_scorecard_status"] == "BLOCKED" else "yellow",
                "evidence_source": "candidate_scorecard.json",
                "evidence_status": evidence_status,
                "candidate_id": scorecard_projection["candidate_scorecard_candidate_id"],
                "strategy_id": scorecard_projection["candidate_scorecard_strategy_id"],
                "sample_summary": (
                    f"{scorecard_projection['candidate_scorecard_symbol'] or 'UNKNOWN'} candidate; "
                    f"net EV after cost {scorecard_projection['candidate_scorecard_net_ev_after_cost_display']}; "
                    f"{scorecard_projection['candidate_scorecard_status']}"
                ),
                "scorecard_scope": scorecard_projection["candidate_scorecard_scope"],
                "primary_blocker_code": scorecard_projection["candidate_scorecard_primary_blocker_code"],
                "primary_blocker_message": scorecard_projection["candidate_scorecard_blocker_summary"],
                "next_action": scorecard_projection["candidate_scorecard_next_action"],
            }
        return {
            **base,
            "status": "COLLECTING",
            "severity": "WARNING",
            "color_token": "yellow",
        }

    evidence = paper_operation_gate_report.get("paper_shadow_evidence_accumulation_report")
    if not isinstance(evidence, dict):
        blocked_components, blocked_component_pass_count, blocked_gap_count, blocked_gap_status, blocked_gap_summary = _profitability_maturity_components(
            paper_samples=0,
            shadow_samples=0,
            min_samples=0,
            cost_count=0,
            entry_count=0,
            no_trade_count=0,
            scorecard_input_eligible=False,
            optimizer_ranking_action="BLOCK_RANKING",
            override_status="BLOCKED",
        )
        return {
            **base,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "evidence_source": "paper_operation_gate_report",
            "evidence_status": "FAIL",
            "evidence_progress_status": "BLOCKED",
            "evidence_progress_pct": 0,
            "evidence_progress_summary": "Evidence source is blocked; fix scope or live-flag drift first.",
            "maturity_gap_status": blocked_gap_status,
            "maturity_gap_count": blocked_gap_count,
            "maturity_component_count": len(blocked_components),
            "paper_scorecard_component_pass_count": blocked_component_pass_count,
            "maturity_gap_summary": blocked_gap_summary,
            "maturity_components": blocked_components,
            "scorecard_scope": "BLOCKED_DISPLAY_ONLY",
            "live_readiness_status": "NOT_LIVE_READY",
            "operator_warning": "Blocked PAPER evidence is not LIVE_READY and cannot place or allow live orders.",
            "evidence_checklist": _profitability_evidence_progress(
                paper_samples=0,
                shadow_samples=0,
                min_samples=0,
                cost_count=0,
                entry_count=0,
                no_trade_count=0,
                override_status="BLOCKED",
            )[0],
            "primary_blocker_code": "HARD_TRUTH_MISSING",
            "primary_blocker_message": "Paper operation gate did not include paper/shadow evidence accumulation.",
            "next_action": "Regenerate the PAPER operation gate with paper/shadow evidence accumulation enabled.",
        }

    scope_matches = (
        paper_operation_gate_report.get("exchange") == exchange
        and paper_operation_gate_report.get("market_type") == market_type
        and paper_operation_gate_report.get("mode") == mode
        and paper_operation_gate_report.get("session_id") == session_id
    )
    live_flag_drift = any(
        paper_operation_gate_report.get(flag) is True or evidence.get(flag) is True
        for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order", "scale_up_allowed")
    ) or paper_operation_gate_report.get("order_adapter_called") is True or evidence.get("order_adapter_called") is True
    candidate_id = evidence.get("candidate_id")
    strategy_id = evidence.get("strategy_id")
    parameter_hash = evidence.get("parameter_hash")
    paper_samples = int(evidence.get("paper_sample_count", 0) or 0)
    shadow_samples = int(evidence.get("shadow_sample_count", 0) or 0)
    min_samples = int(evidence.get("min_required_samples") or evidence.get("min_required_sample_count") or 0)
    entry_count = int(evidence.get("entry_reason_count", 0) or 0)
    no_trade_count = int(evidence.get("no_trade_reason_count", 0) or 0)
    cost_count = int(evidence.get("cost_evidence_count", 0) or 0)
    eligible = evidence.get("scorecard_input_eligible") is True
    optimizer_ranking_action = evidence.get("optimizer_ranking_action", "BLOCK_RANKING")
    runtime_source_projection = _actual_runtime_source_projection(evidence)
    blockers = evidence.get("blockers", [])
    first_blocker = blockers[0] if blockers and isinstance(blockers[0], dict) else {}
    checklist, progress_pct, progress_status, progress_summary = _profitability_evidence_progress(
        paper_samples=paper_samples,
        shadow_samples=shadow_samples,
        min_samples=min_samples,
        cost_count=cost_count,
        entry_count=entry_count,
        no_trade_count=no_trade_count,
    )

    if live_flag_drift:
        blocked_components, blocked_component_pass_count, blocked_gap_count, blocked_gap_status, blocked_gap_summary = _profitability_maturity_components(
            paper_samples=paper_samples,
            shadow_samples=shadow_samples,
            min_samples=min_samples,
            cost_count=cost_count,
            entry_count=entry_count,
            no_trade_count=no_trade_count,
            scorecard_input_eligible=False,
            optimizer_ranking_action="BLOCK_RANKING",
            override_status="BLOCKED",
        )
        blocked_checklist, _, blocked_progress_status, blocked_progress_summary = _profitability_evidence_progress(
            paper_samples=paper_samples,
            shadow_samples=shadow_samples,
            min_samples=min_samples,
            cost_count=cost_count,
            entry_count=entry_count,
            no_trade_count=no_trade_count,
            override_status="BLOCKED",
        )
        return {
            **base,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "evidence_source": "paper_operation_gate_report",
            "evidence_status": "FAIL",
            "candidate_id": candidate_id,
            "strategy_id": strategy_id,
            "parameter_hash": parameter_hash,
            "paper_sample_count": paper_samples,
            "shadow_sample_count": shadow_samples,
            "min_required_samples": min_samples,
            "sample_summary": f"PAPER {paper_samples} / SHADOW {shadow_samples}; min {min_samples}",
            **runtime_source_projection,
            "evidence_progress_status": blocked_progress_status,
            "evidence_progress_pct": 0,
            "evidence_progress_summary": blocked_progress_summary,
            "maturity_gap_status": blocked_gap_status,
            "maturity_gap_count": blocked_gap_count,
            "maturity_component_count": len(blocked_components),
            "paper_scorecard_component_pass_count": blocked_component_pass_count,
            "maturity_gap_summary": blocked_gap_summary,
            "maturity_components": blocked_components,
            "scorecard_scope": "BLOCKED_DISPLAY_ONLY",
            "live_readiness_status": "NOT_LIVE_READY",
            "operator_warning": "Rejected PAPER evidence is not LIVE_READY and cannot place or allow live orders.",
            "evidence_checklist": blocked_checklist,
            "primary_blocker_code": "LIVE_FINAL_GUARD_FAILED",
            "primary_blocker_message": "Evidence maturity attempted to carry live/order/scale permission.",
            "next_action": "Block the run, inspect evidence writer, and keep live orders disabled.",
        }
    if not scope_matches:
        blocked_components, blocked_component_pass_count, blocked_gap_count, blocked_gap_status, blocked_gap_summary = _profitability_maturity_components(
            paper_samples=paper_samples,
            shadow_samples=shadow_samples,
            min_samples=min_samples,
            cost_count=cost_count,
            entry_count=entry_count,
            no_trade_count=no_trade_count,
            scorecard_input_eligible=False,
            optimizer_ranking_action="BLOCK_RANKING",
            override_status="BLOCKED",
        )
        blocked_checklist, _, blocked_progress_status, blocked_progress_summary = _profitability_evidence_progress(
            paper_samples=paper_samples,
            shadow_samples=shadow_samples,
            min_samples=min_samples,
            cost_count=cost_count,
            entry_count=entry_count,
            no_trade_count=no_trade_count,
            override_status="BLOCKED",
        )
        return {
            **base,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "evidence_source": "paper_operation_gate_report",
            "evidence_status": "FAIL",
            "candidate_id": candidate_id,
            "strategy_id": strategy_id,
            "parameter_hash": parameter_hash,
            "paper_sample_count": paper_samples,
            "shadow_sample_count": shadow_samples,
            "min_required_samples": min_samples,
            "sample_summary": f"PAPER {paper_samples} / SHADOW {shadow_samples}; min {min_samples}",
            **runtime_source_projection,
            "evidence_progress_status": blocked_progress_status,
            "evidence_progress_pct": 0,
            "evidence_progress_summary": blocked_progress_summary,
            "maturity_gap_status": blocked_gap_status,
            "maturity_gap_count": blocked_gap_count,
            "maturity_component_count": len(blocked_components),
            "paper_scorecard_component_pass_count": blocked_component_pass_count,
            "maturity_gap_summary": blocked_gap_summary,
            "maturity_components": blocked_components,
            "scorecard_scope": "BLOCKED_DISPLAY_ONLY",
            "live_readiness_status": "NOT_LIVE_READY",
            "operator_warning": "Cross-session PAPER evidence is not LIVE_READY and cannot place or allow live orders.",
            "evidence_checklist": blocked_checklist,
            "primary_blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "primary_blocker_message": "Paper/shadow evidence scope does not match this dashboard session.",
            "next_action": "Regenerate evidence for the exact exchange, market, mode, and session shown on this dashboard.",
        }

    components, component_pass_count, maturity_gap_count, maturity_gap_status, maturity_gap_summary = _profitability_maturity_components(
        paper_samples=paper_samples,
        shadow_samples=shadow_samples,
        min_samples=min_samples,
        cost_count=cost_count,
        entry_count=entry_count,
        no_trade_count=no_trade_count,
        scorecard_input_eligible=eligible,
        optimizer_ranking_action=str(optimizer_ranking_action),
    )

    maturity = {
        **base,
        "evidence_source": "paper_operation_gate_report",
        "evidence_status": "PASS" if eligible else "WARN",
        "candidate_id": candidate_id,
        "strategy_id": strategy_id,
        "parameter_hash": parameter_hash,
        "paper_sample_count": paper_samples,
        "shadow_sample_count": shadow_samples,
        "min_required_samples": min_samples,
        "sample_summary": f"PAPER {paper_samples} / SHADOW {shadow_samples}; min {min_samples}",
        **runtime_source_projection,
        "cost_evidence_status": "PASS" if cost_count > 0 else "UNTESTED",
        "entry_reason_status": "PASS" if entry_count > 0 else "UNTESTED",
        "no_trade_reason_status": "PASS" if no_trade_count > 0 else "UNTESTED",
        "evidence_progress_status": progress_status,
        "evidence_progress_pct": progress_pct,
        "evidence_progress_summary": progress_summary,
        "evidence_checklist": checklist,
        "maturity_gap_status": maturity_gap_status,
        "maturity_gap_count": maturity_gap_count,
        "maturity_component_count": len(components),
        "paper_scorecard_component_pass_count": component_pass_count,
        "maturity_gap_summary": maturity_gap_summary,
        "maturity_components": components,
        "scorecard_scope": "PAPER_SCORECARD_INPUT_ONLY" if eligible else "PAPER_EVIDENCE_COLLECTION_ONLY",
        "live_readiness_status": "NOT_LIVE_READY",
        "operator_warning": "PAPER scorecard input is not LIVE_READY and cannot place or allow live orders.",
        "scorecard_input_eligible": eligible,
        "optimizer_ranking_action": optimizer_ranking_action,
        "primary_blocker_code": first_blocker.get("code") or paper_operation_gate_report.get("primary_blocker_code"),
        "primary_blocker_message": first_blocker.get("message")
        or "Paper/shadow evidence is available for analysis only; live remains blocked.",
    }
    if eligible:
        maturity.update(
            {
                "status": "SCORECARD_INPUT_READY",
                "severity": "NORMAL",
                "color_token": "blue",
                "next_action": "Review optimizer scorecard inputs in PAPER/SHADOW only. Live and scale-up remain blocked.",
            }
        )
    else:
        maturity.update(
            {
                "status": "COLLECTING",
                "severity": "WARNING",
                "color_token": "yellow",
                "next_action": "Collect more fresh paper/shadow samples, reasons, and cost evidence before ranking.",
            }
        )
    return maturity


def _convergence_dependency_statuses(report: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field in CONVERGENCE_ASSESSMENT_DEPENDENCY_FIELDS:
        raw_status = report.get(field) if isinstance(report, dict) else "UNTESTED"
        status = str(raw_status or "UNTESTED").upper()
        if status not in {"PASS", "FAIL", "BLOCKED", "UNTESTED", "STALE", "TIMEOUT"}:
            status = "UNTESTED"
        rows.append(
            {
                "validator_id": field.removesuffix("_status"),
                "status": status,
            }
        )
    return rows


def _convergence_assessment_status(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    convergence_assessment_report: dict[str, Any] | None,
    summary_freshness: str,
) -> dict[str, Any]:
    dependency_statuses = _convergence_dependency_statuses(convergence_assessment_report)
    dependency_pass_count = sum(1 for item in dependency_statuses if item["status"] == "PASS")
    required_dependency_count = len(CONVERGENCE_ASSESSMENT_DEPENDENCY_FIELDS)
    base = {
        "title": "Convergence Assessment",
        "status": "UNTESTED",
        "severity": "WARNING",
        "color_token": "yellow",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "assessment_id": None,
        "assessment_status": "UNTESTED",
        "convergence_claim": "NO_CLAIM",
        "objective_score_band": "UNKNOWN",
        "model_drift_status": "NOT_EVALUATED",
        "dependency_pass_count": dependency_pass_count,
        "required_dependency_count": required_dependency_count,
        "dependency_summary": f"{dependency_pass_count}/{required_dependency_count} dependency validators PASS",
        "dependency_statuses": dependency_statuses,
        "writer_input_eligible": False,
        "model_promotion_allowed": False,
        "scale_up_recommendation_allowed": False,
        "forbidden_input_detected": False,
        "primary_blocker_code": "CONVERGENCE_STATE_UNTESTED",
        "primary_blocker_message": "Convergence assessment report is not loaded for this dashboard.",
        "next_action": "Run PAPER/SHADOW convergence validators before any convergence review.",
        "operator_warning": "Convergence assessment is not LIVE_READY; live orders blocked and scale-up blocked.",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    if summary_freshness != "PASS":
        return {
            **base,
            "status": "STALE",
            "assessment_status": "STALE",
            "primary_blocker_code": "LATENCY_TTL_EXPIRED",
            "primary_blocker_message": "Dashboard summary is stale; convergence assessment display cannot be trusted.",
            "next_action": "Rerun PAPER to refresh dashboard sources before reviewing convergence assessment.",
        }
    if not isinstance(convergence_assessment_report, dict):
        return base

    blockers = convergence_assessment_report.get("blockers", [])
    first_blocker = blockers[0] if blockers and isinstance(blockers[0], dict) else {}
    scope_matches = (
        convergence_assessment_report.get("exchange") == exchange
        and convergence_assessment_report.get("market_type") == market_type
        and convergence_assessment_report.get("mode") == mode
        and convergence_assessment_report.get("session_id") == session_id
    )
    source_modes = convergence_assessment_report.get("source_modes", [])
    source_modes = source_modes if isinstance(source_modes, list) else []
    live_source_mode = any(str(item).upper() == "LIVE" for item in source_modes)
    forbidden_input_detected = (
        live_source_mode
        or convergence_assessment_report.get("mode") == "LIVE"
        or any(
            convergence_assessment_report.get(flag) is True
            for flag in (
                "live_permission_created",
                "live_config_mutation_allowed",
                "writes_live_ready_snapshot",
                "active_snapshot_mutation_allowed",
                "optimizer_winner_live_config_allowed",
                "paper_winner_live_config_allowed",
                "writer_input_eligible",
                "model_promotion_allowed",
                "scale_up_recommendation_allowed",
                "live_order_ready",
                "live_order_allowed",
                "can_live_trade",
                "scale_up_allowed",
            )
        )
    )
    raw_assessment_status = str(convergence_assessment_report.get("assessment_status", "UNTESTED")).upper()
    assessment_status = raw_assessment_status if raw_assessment_status in CONVERGENCE_ASSESSMENT_STATUSES else "UNTESTED"
    raw_claim = str(convergence_assessment_report.get("convergence_claim", "NO_CLAIM")).upper()
    convergence_claim = raw_claim if raw_claim in CONVERGENCE_CLAIMS else "NO_CLAIM"
    raw_band = str(convergence_assessment_report.get("objective_score_band", "UNKNOWN")).upper()
    score_band = raw_band if raw_band in CONVERGENCE_SCORE_BANDS else "UNKNOWN"
    raw_drift = str(convergence_assessment_report.get("model_drift_status", "NOT_EVALUATED")).upper()
    model_drift_status = raw_drift if raw_drift in CONVERGENCE_DRIFT_STATUSES else "NOT_EVALUATED"
    report_dependency_count = int(convergence_assessment_report.get("required_dependency_count", required_dependency_count) or 0)
    report_pass_count = int(convergence_assessment_report.get("dependency_pass_count", dependency_pass_count) or 0)
    dependency_count_mismatch = (
        report_dependency_count != required_dependency_count
        or report_pass_count != dependency_pass_count
        or len(dependency_statuses) != required_dependency_count
    )
    all_dependencies_pass = dependency_pass_count == required_dependency_count
    assessment = {
        **base,
        "assessment_id": convergence_assessment_report.get("assessment_id"),
        "assessment_status": assessment_status,
        "convergence_claim": convergence_claim,
        "objective_score_band": score_band,
        "model_drift_status": model_drift_status,
        "dependency_pass_count": dependency_pass_count,
        "required_dependency_count": required_dependency_count,
        "dependency_summary": f"{dependency_pass_count}/{required_dependency_count} dependency validators PASS",
        "dependency_statuses": dependency_statuses,
        "forbidden_input_detected": forbidden_input_detected,
        "primary_blocker_code": first_blocker.get("code")
        or convergence_assessment_report.get("primary_blocker_code")
        or "LIVE_READY_MISSING",
        "primary_blocker_message": first_blocker.get("message")
        or "Convergence assessment is analysis-only; live orders and scale-up remain blocked.",
        "next_action": convergence_assessment_report.get("next_operator_action")
        or "Continue PAPER/SHADOW convergence monitoring and keep live blocked.",
        "operator_warning": (
            "Convergence assessment is not LIVE_READY; live orders blocked and scale-up blocked. "
            "Dashboard display truth only."
        ),
    }
    if forbidden_input_detected:
        return {
            **assessment,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "convergence_claim": "BLOCKED",
            "objective_score_band": "BLOCKED",
            "model_drift_status": "BLOCKED",
            "primary_blocker_code": "LIVE_FINAL_GUARD_FAILED",
            "primary_blocker_message": "Convergence assessment attempted writer input, live permission, live source, or scale-up permission.",
            "next_action": "Block the run, inspect convergence writer, and keep live orders disabled.",
        }
    if not scope_matches:
        return {
            **assessment,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "primary_blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "primary_blocker_message": "Convergence assessment scope does not match this dashboard session.",
            "next_action": "Regenerate convergence assessment for the exact exchange, market, mode, and session shown here.",
        }
    if dependency_count_mismatch:
        return {
            **assessment,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "primary_blocker_code": "SCHEMA_IDENTITY_MISMATCH",
            "primary_blocker_message": "Convergence dependency counts do not match the validator dependency list.",
            "next_action": "Regenerate convergence assessment after dependency validator registry review.",
        }
    if not all_dependencies_pass:
        return {
            **assessment,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "convergence_claim": "BLOCKED",
            "objective_score_band": "BLOCKED",
            "primary_blocker_code": "CONVERGENCE_CLAIM_UNVERIFIED",
            "primary_blocker_message": "Convergence assessment has dependency validators that are not PASS.",
            "next_action": "Resolve FAIL/BLOCKED/UNTESTED/STALE/TIMEOUT dependency validators before convergence review.",
        }
    if model_drift_status in {"DRIFT_SUSPECTED", "DRIFT_DETECTED", "BLOCKED"}:
        return {
            **assessment,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "convergence_claim": "BLOCKED",
            "objective_score_band": "BLOCKED",
            "primary_blocker_code": "MODEL_DRIFT_BLOCKED",
            "primary_blocker_message": "Model drift is suspected or detected; convergence claim is blocked.",
            "next_action": "Review drift report and continue PAPER/SHADOW observation before ranking.",
        }
    if assessment_status in {"LOCALLY_IMPROVING", "ROBUSTLY_IMPROVING"}:
        return {
            **assessment,
            "status": assessment_status,
            "severity": "NORMAL",
            "color_token": "green" if assessment_status == "ROBUSTLY_IMPROVING" else "blue",
            "primary_blocker_code": "LIVE_READY_MISSING",
            "primary_blocker_message": "Convergence can be reviewed as PAPER/SHADOW analysis only; not LIVE_READY.",
            "next_action": "Review convergence evidence as analysis-only. Live orders and scale-up remain blocked.",
        }
    return {
        **assessment,
        "status": "COLLECTING",
        "severity": "WARNING",
        "color_token": "yellow",
        "primary_blocker_code": "CONVERGENCE_STATE_UNTESTED",
        "primary_blocker_message": "Convergence assessment is collecting or untested.",
        "next_action": "Continue PAPER/SHADOW collection before convergence claim review.",
    }


def _exploration_policy_dependency_statuses(policy: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field in EXPLORATION_POLICY_DEPENDENCY_FIELDS:
        raw_status = policy.get(field) if isinstance(policy, dict) else "UNTESTED"
        status = str(raw_status or "UNTESTED").upper()
        if status not in {"PASS", "FAIL", "BLOCKED", "UNTESTED", "STALE", "TIMEOUT"}:
            status = "UNTESTED"
        rows.append(
            {
                "validator_id": field.removesuffix("_status"),
                "status": status,
            }
        )
    return rows


def _exploration_policy_status(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    exploration_exploitation_policy: dict[str, Any] | None,
    summary_freshness: str,
) -> dict[str, Any]:
    dependency_statuses = _exploration_policy_dependency_statuses(exploration_exploitation_policy)
    dependency_pass_count = sum(1 for item in dependency_statuses if item["status"] == "PASS")
    required_dependency_count = len(EXPLORATION_POLICY_DEPENDENCY_FIELDS)
    base = {
        "title": "Exploration / Exploitation Policy",
        "status": "UNTESTED",
        "severity": "WARNING",
        "color_token": "yellow",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "policy_id": None,
        "policy_status": "UNTESTED",
        "controller_state": "BLOCKED",
        "transition_decision": "BLOCK_TRANSITION",
        "recommendation_scope": "BLOCKED",
        "objective_basis": "BLOCKED_NO_VALID_OBJECTIVE",
        "dependency_pass_count": dependency_pass_count,
        "required_dependency_count": required_dependency_count,
        "dependency_summary": f"{dependency_pass_count}/{required_dependency_count} dependency validators PASS",
        "dependency_statuses": dependency_statuses,
        "candidate_count": 0,
        "exploration_candidate_budget": 0,
        "candidate_budget_status": "BLOCKED",
        "exploitation_candidate_id": None,
        "exploitation_allowed_for_paper_ranking": False,
        "forbidden_input_detected": False,
        "primary_blocker_code": "EXPLORATION_POLICY_UNTESTED",
        "primary_blocker_message": "Exploration/exploitation policy is not loaded for this dashboard.",
        "next_action": "Run PAPER/SHADOW exploration policy validators before any ranking review.",
        "operator_warning": (
            "Exploration/exploitation policy is not LIVE_READY; live orders blocked and scale-up blocked. "
            "PAPER ranking review only when dependencies pass."
        ),
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "live_permission_created": False,
        "live_config_mutation_allowed": False,
        "writes_live_ready_snapshot": False,
        "active_snapshot_mutation_allowed": False,
        "order_submission_allowed": False,
        "exchange_account_call_allowed": False,
        "scale_up_recommendation_allowed": False,
    }
    if summary_freshness != "PASS":
        return {
            **base,
            "status": "STALE",
            "policy_status": "STALE",
            "primary_blocker_code": "LATENCY_TTL_EXPIRED",
            "primary_blocker_message": "Dashboard summary is stale; exploration policy display cannot be trusted.",
            "next_action": "Rerun PAPER to refresh dashboard sources before reviewing exploration policy.",
        }
    if not isinstance(exploration_exploitation_policy, dict):
        return base

    blockers = exploration_exploitation_policy.get("blockers", [])
    first_blocker = blockers[0] if blockers and isinstance(blockers[0], dict) else {}
    scope_matches = (
        exploration_exploitation_policy.get("exchange") == exchange
        and exploration_exploitation_policy.get("market_type") == market_type
        and exploration_exploitation_policy.get("mode") == mode
        and exploration_exploitation_policy.get("session_id") == session_id
    )
    source_modes = exploration_exploitation_policy.get("source_modes", [])
    source_modes = source_modes if isinstance(source_modes, list) else []
    live_source_mode = any(str(item).upper() == "LIVE" for item in source_modes)
    forbidden_input_detected = (
        live_source_mode
        or exploration_exploitation_policy.get("mode") == "LIVE"
        or any(
            exploration_exploitation_policy.get(flag) is True
            for flag in (
                "live_permission_created",
                "live_config_mutation_allowed",
                "writes_live_ready_snapshot",
                "active_snapshot_mutation_allowed",
                "optimizer_winner_live_config_allowed",
                "paper_winner_live_config_allowed",
                "order_submission_allowed",
                "exchange_account_call_allowed",
                "scale_up_recommendation_allowed",
                "live_order_ready",
                "live_order_allowed",
                "can_live_trade",
                "scale_up_allowed",
            )
        )
    )
    raw_policy_status = str(exploration_exploitation_policy.get("policy_status", "UNTESTED")).upper()
    policy_status = raw_policy_status if raw_policy_status in EXPLORATION_POLICY_STATUSES else "UNTESTED"
    raw_controller = str(exploration_exploitation_policy.get("controller_state", "BLOCKED")).upper()
    controller_state = raw_controller if raw_controller in EXPLORATION_POLICY_CONTROLLER_STATES else "BLOCKED"
    raw_transition = str(exploration_exploitation_policy.get("transition_decision", "BLOCK_TRANSITION")).upper()
    transition_decision = raw_transition if raw_transition in EXPLORATION_POLICY_TRANSITIONS else "BLOCK_TRANSITION"
    raw_scope = str(exploration_exploitation_policy.get("recommendation_scope", "BLOCKED")).upper()
    recommendation_scope = raw_scope if raw_scope in EXPLORATION_POLICY_RECOMMENDATION_SCOPES else "BLOCKED"
    raw_objective = str(exploration_exploitation_policy.get("objective_basis", "BLOCKED_NO_VALID_OBJECTIVE")).upper()
    objective_basis = raw_objective if raw_objective in EXPLORATION_POLICY_OBJECTIVE_BASES else "BLOCKED_NO_VALID_OBJECTIVE"
    raw_budget_status = str(exploration_exploitation_policy.get("candidate_budget_status", "BLOCKED")).upper()
    candidate_budget_status = (
        raw_budget_status if raw_budget_status in EXPLORATION_POLICY_BUDGET_STATUSES else "BLOCKED"
    )
    candidate_count = int(exploration_exploitation_policy.get("candidate_count", 0) or 0)
    exploration_candidate_budget = int(exploration_exploitation_policy.get("exploration_candidate_budget", 0) or 0)
    report_dependency_count = int(
        exploration_exploitation_policy.get("required_dependency_count", required_dependency_count) or 0
    )
    report_pass_count = int(exploration_exploitation_policy.get("dependency_pass_count", dependency_pass_count) or 0)
    dependency_count_mismatch = (
        report_dependency_count != required_dependency_count
        or report_pass_count != dependency_pass_count
        or len(dependency_statuses) != required_dependency_count
    )
    all_dependencies_pass = dependency_pass_count == required_dependency_count
    budget_breached = (
        exploration_candidate_budget < 0
        or candidate_count < 0
        or (exploration_candidate_budget > 0 and candidate_count > exploration_candidate_budget)
        or candidate_budget_status == "BLOCKED"
    )
    policy = {
        **base,
        "policy_id": exploration_exploitation_policy.get("policy_id"),
        "policy_status": policy_status,
        "controller_state": controller_state,
        "transition_decision": transition_decision,
        "recommendation_scope": recommendation_scope,
        "objective_basis": objective_basis,
        "dependency_pass_count": dependency_pass_count,
        "required_dependency_count": required_dependency_count,
        "dependency_summary": f"{dependency_pass_count}/{required_dependency_count} dependency validators PASS",
        "dependency_statuses": dependency_statuses,
        "candidate_count": candidate_count,
        "exploration_candidate_budget": exploration_candidate_budget,
        "candidate_budget_status": candidate_budget_status,
        "exploitation_candidate_id": exploration_exploitation_policy.get("exploitation_candidate_id"),
        "exploitation_allowed_for_paper_ranking": False,
        "forbidden_input_detected": forbidden_input_detected,
        "primary_blocker_code": first_blocker.get("code")
        or exploration_exploitation_policy.get("primary_blocker_code")
        or "LIVE_READY_MISSING",
        "primary_blocker_message": first_blocker.get("message")
        or "Exploration policy is analysis-only; live orders and scale-up remain blocked.",
        "next_action": exploration_exploitation_policy.get("next_operator_action")
        or "Review PAPER/SHADOW exploration policy only after dependencies pass.",
        "operator_warning": (
            "Exploration/exploitation policy is not LIVE_READY; live orders blocked and scale-up blocked. "
            "Dashboard display truth only."
        ),
    }
    if forbidden_input_detected:
        return {
            **policy,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "policy_status": "BLOCKED",
            "controller_state": "BLOCKED",
            "transition_decision": "BLOCK_TRANSITION",
            "recommendation_scope": "BLOCKED",
            "objective_basis": "BLOCKED_NO_VALID_OBJECTIVE",
            "candidate_budget_status": "BLOCKED",
            "primary_blocker_code": "LIVE_FINAL_GUARD_FAILED",
            "primary_blocker_message": "Exploration policy attempted live permission, live source, order submission, or scale-up permission.",
            "next_action": "Block the run, inspect exploration policy inputs, and keep live orders disabled.",
        }
    if not scope_matches:
        return {
            **policy,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "policy_status": "BLOCKED",
            "primary_blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "primary_blocker_message": "Exploration policy scope does not match this dashboard session.",
            "next_action": "Regenerate exploration policy for the exact exchange, market, mode, and session shown here.",
        }
    if dependency_count_mismatch:
        return {
            **policy,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "policy_status": "BLOCKED",
            "primary_blocker_code": "SCHEMA_IDENTITY_MISMATCH",
            "primary_blocker_message": "Exploration policy dependency counts do not match the validator dependency list.",
            "next_action": "Regenerate exploration policy after dependency validator registry review.",
        }
    if not all_dependencies_pass:
        return {
            **policy,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "policy_status": "BLOCKED",
            "controller_state": "BLOCKED",
            "transition_decision": "BLOCK_TRANSITION",
            "recommendation_scope": "BLOCKED",
            "primary_blocker_code": "EXPLORATION_POLICY_DEPENDENCY_UNVERIFIED",
            "primary_blocker_message": "Exploration policy has dependency validators that are not PASS.",
            "next_action": "Resolve FAIL/BLOCKED/UNTESTED/STALE/TIMEOUT dependency validators before ranking review.",
        }
    if budget_breached:
        return {
            **policy,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "policy_status": "BLOCKED",
            "controller_state": "BLOCKED",
            "transition_decision": "BLOCK_TRANSITION",
            "recommendation_scope": "BLOCKED",
            "exploitation_allowed_for_paper_ranking": False,
            "primary_blocker_code": "OPTIMIZER_RESOURCE_BUDGET_EXCEEDED",
            "primary_blocker_message": "Exploration candidate budget is missing, exceeded, or blocked.",
            "next_action": "Reduce PAPER/SHADOW candidate load before ranking review.",
        }
    if (
        policy_status == "PAPER_RANKING_REVIEW_ELIGIBLE"
        and transition_decision == "LIMITED_EXPLOITATION_REVIEW"
        and recommendation_scope == "PAPER_RANKING_REVIEW_ONLY"
        and exploration_exploitation_policy.get("exploitation_allowed_for_paper_ranking") is True
    ):
        return {
            **policy,
            "status": "PAPER_RANKING_REVIEW_ELIGIBLE",
            "severity": "NORMAL",
            "color_token": "blue",
            "primary_blocker_code": "LIVE_READY_MISSING",
            "primary_blocker_message": "Exploration policy can be reviewed for PAPER ranking only; not LIVE_READY.",
            "next_action": "Review PAPER ranking candidate only. Live orders and scale-up remain blocked.",
            "exploitation_allowed_for_paper_ranking": True,
        }
    return {
        **policy,
        "status": "ACTIVE_ANALYSIS_ONLY",
        "severity": "WARNING",
        "color_token": "yellow",
        "primary_blocker_code": "EXPLORATION_POLICY_ANALYSIS_ONLY",
        "primary_blocker_message": "Exploration policy remains analysis-only and is not eligible for PAPER ranking review.",
        "next_action": "Continue PAPER/SHADOW evidence collection before limited exploitation review.",
    }


def _parameter_narrowing_dependency_statuses(report: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field in PARAMETER_NARROWING_DEPENDENCY_FIELDS:
        raw_status = report.get(field) if isinstance(report, dict) else "UNTESTED"
        status = str(raw_status or "UNTESTED").upper()
        if status not in {"PASS", "FAIL", "BLOCKED", "UNTESTED", "STALE", "TIMEOUT"}:
            status = "UNTESTED"
        rows.append(
            {
                "validator_id": field.removesuffix("_status"),
                "status": status,
            }
        )
    return rows


def _int_or_zero(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float_or_zero(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _parameter_narrowing_status(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    parameter_narrowing_report: dict[str, Any] | None,
    summary_freshness: str,
) -> dict[str, Any]:
    dependency_statuses = _parameter_narrowing_dependency_statuses(parameter_narrowing_report)
    dependency_pass_count = sum(1 for item in dependency_statuses if item["status"] == "PASS")
    required_dependency_count = len(PARAMETER_NARROWING_DEPENDENCY_FIELDS)
    base = {
        "title": "Parameter Narrowing",
        "status": "UNTESTED",
        "severity": "WARNING",
        "color_token": "yellow",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "narrowing_id": None,
        "narrowing_status": "UNTESTED",
        "recommendation_scope": "BLOCKED",
        "parameter_write_scope": "BLOCKED",
        "objective_basis": "BLOCKED_NO_VALID_OBJECTIVE",
        "dependency_pass_count": dependency_pass_count,
        "required_dependency_count": required_dependency_count,
        "dependency_summary": f"{dependency_pass_count}/{required_dependency_count} dependency validators PASS",
        "dependency_statuses": dependency_statuses,
        "min_required_sample_count": 0,
        "paper_sample_count": 0,
        "shadow_sample_count": 0,
        "sample_summary": "0 PAPER / 0 SHADOW samples",
        "parameter_count_before": 0,
        "parameter_count_after": 0,
        "max_narrowing_pct": 0.0,
        "narrowing_pct": 0.0,
        "parameter_changes": [],
        "previous_parameter_hash": None,
        "proposed_parameter_hash": None,
        "narrowing_allowed_for_paper_ranking": False,
        "forbidden_input_detected": False,
        "primary_blocker_code": "PARAMETER_NARROWING_UNVERIFIED",
        "primary_blocker_message": "Parameter narrowing report is not loaded for this dashboard.",
        "next_action": "Run PAPER/SHADOW parameter narrowing validators before any parameter review.",
        "operator_warning": (
            "Parameter narrowing is proposal-only, not LIVE_READY; live orders blocked and scale-up blocked. "
            "It cannot mutate active or live config."
        ),
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "live_permission_created": False,
        "live_config_mutation_allowed": False,
        "writes_live_ready_snapshot": False,
        "active_snapshot_mutation_allowed": False,
        "active_config_mutation_allowed": False,
        "optimizer_winner_live_config_allowed": False,
        "paper_winner_live_config_allowed": False,
        "order_submission_allowed": False,
        "exchange_account_call_allowed": False,
        "scale_up_recommendation_allowed": False,
    }
    if summary_freshness != "PASS":
        return {
            **base,
            "status": "STALE",
            "narrowing_status": "STALE",
            "primary_blocker_code": "LATENCY_TTL_EXPIRED",
            "primary_blocker_message": "Dashboard summary is stale; parameter narrowing display cannot be trusted.",
            "next_action": "Rerun PAPER to refresh dashboard sources before reviewing parameter narrowing.",
        }
    if not isinstance(parameter_narrowing_report, dict):
        return base

    blockers = parameter_narrowing_report.get("blockers", [])
    first_blocker = blockers[0] if blockers and isinstance(blockers[0], dict) else {}
    scope_matches = (
        parameter_narrowing_report.get("exchange") == exchange
        and parameter_narrowing_report.get("market_type") == market_type
        and parameter_narrowing_report.get("mode") == mode
        and parameter_narrowing_report.get("session_id") == session_id
    )
    source_modes = parameter_narrowing_report.get("source_modes", [])
    source_modes = source_modes if isinstance(source_modes, list) else []
    live_source_mode = any(str(item).upper() == "LIVE" for item in source_modes)
    forbidden_input_detected = (
        live_source_mode
        or parameter_narrowing_report.get("mode") == "LIVE"
        or any(
            parameter_narrowing_report.get(flag) is True
            for flag in (
                "live_permission_created",
                "live_config_mutation_allowed",
                "writes_live_ready_snapshot",
                "active_snapshot_mutation_allowed",
                "active_config_mutation_allowed",
                "optimizer_winner_live_config_allowed",
                "paper_winner_live_config_allowed",
                "order_submission_allowed",
                "exchange_account_call_allowed",
                "scale_up_recommendation_allowed",
                "live_order_ready",
                "live_order_allowed",
                "can_live_trade",
                "scale_up_allowed",
            )
        )
    )
    raw_status = str(parameter_narrowing_report.get("narrowing_status", "UNTESTED")).upper()
    narrowing_status = raw_status if raw_status in PARAMETER_NARROWING_STATUSES else "UNTESTED"
    raw_scope = str(parameter_narrowing_report.get("recommendation_scope", "BLOCKED")).upper()
    recommendation_scope = (
        raw_scope if raw_scope in PARAMETER_NARROWING_RECOMMENDATION_SCOPES else "BLOCKED"
    )
    raw_write_scope = str(parameter_narrowing_report.get("parameter_write_scope", "BLOCKED")).upper()
    parameter_write_scope = raw_write_scope if raw_write_scope in PARAMETER_NARROWING_WRITE_SCOPES else "BLOCKED"
    raw_objective = str(parameter_narrowing_report.get("objective_basis", "BLOCKED_NO_VALID_OBJECTIVE")).upper()
    objective_basis = raw_objective if raw_objective in PARAMETER_NARROWING_OBJECTIVE_BASES else "BLOCKED_NO_VALID_OBJECTIVE"
    report_dependency_count = _int_or_zero(parameter_narrowing_report.get("required_dependency_count", required_dependency_count))
    report_pass_count = _int_or_zero(parameter_narrowing_report.get("dependency_pass_count", dependency_pass_count))
    dependency_count_mismatch = (
        report_dependency_count != required_dependency_count
        or report_pass_count != dependency_pass_count
        or len(dependency_statuses) != required_dependency_count
    )
    all_dependencies_pass = dependency_pass_count == required_dependency_count
    min_required_sample_count = _int_or_zero(parameter_narrowing_report.get("min_required_sample_count"))
    paper_sample_count = _int_or_zero(parameter_narrowing_report.get("paper_sample_count"))
    shadow_sample_count = _int_or_zero(parameter_narrowing_report.get("shadow_sample_count"))
    sample_insufficient = (
        min_required_sample_count > 0
        and (paper_sample_count < min_required_sample_count or shadow_sample_count < min_required_sample_count)
    )
    parameter_count_before = _int_or_zero(parameter_narrowing_report.get("parameter_count_before"))
    parameter_count_after = _int_or_zero(parameter_narrowing_report.get("parameter_count_after"))
    max_narrowing_pct = _float_or_zero(parameter_narrowing_report.get("max_narrowing_pct"))
    narrowing_pct = _float_or_zero(parameter_narrowing_report.get("narrowing_pct"))
    over_narrowing = (
        max_narrowing_pct <= 0.0
        or narrowing_pct <= 0.0
        or narrowing_pct > max_narrowing_pct
        or parameter_count_before <= 0
        or parameter_count_after <= 0
        or parameter_count_after >= parameter_count_before
    )
    changes = parameter_narrowing_report.get("parameter_changes")
    if not isinstance(changes, list):
        changes = []
    report = {
        **base,
        "narrowing_id": parameter_narrowing_report.get("narrowing_id"),
        "narrowing_status": narrowing_status,
        "recommendation_scope": recommendation_scope,
        "parameter_write_scope": parameter_write_scope,
        "objective_basis": objective_basis,
        "dependency_pass_count": dependency_pass_count,
        "required_dependency_count": required_dependency_count,
        "dependency_summary": f"{dependency_pass_count}/{required_dependency_count} dependency validators PASS",
        "dependency_statuses": dependency_statuses,
        "min_required_sample_count": min_required_sample_count,
        "paper_sample_count": paper_sample_count,
        "shadow_sample_count": shadow_sample_count,
        "sample_summary": f"{paper_sample_count} PAPER / {shadow_sample_count} SHADOW samples",
        "parameter_count_before": parameter_count_before,
        "parameter_count_after": parameter_count_after,
        "max_narrowing_pct": max_narrowing_pct,
        "narrowing_pct": narrowing_pct,
        "parameter_changes": changes,
        "previous_parameter_hash": parameter_narrowing_report.get("previous_parameter_hash"),
        "proposed_parameter_hash": parameter_narrowing_report.get("proposed_parameter_hash"),
        "narrowing_allowed_for_paper_ranking": False,
        "forbidden_input_detected": forbidden_input_detected,
        "primary_blocker_code": first_blocker.get("code")
        or parameter_narrowing_report.get("primary_blocker_code")
        or "LIVE_READY_MISSING",
        "primary_blocker_message": first_blocker.get("message")
        or "Parameter narrowing is proposal-only; live orders, active config mutation, and scale-up remain blocked.",
        "next_action": parameter_narrowing_report.get("next_operator_action")
        or "Review PAPER parameter proposal only after dependencies and sample bounds pass.",
        "operator_warning": (
            "Parameter narrowing is proposal-only, not LIVE_READY; live orders blocked and scale-up blocked. "
            "Dashboard display truth only; active and live config mutation are blocked."
        ),
    }
    if forbidden_input_detected:
        return {
            **report,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "narrowing_status": "BLOCKED",
            "recommendation_scope": "BLOCKED",
            "parameter_write_scope": "BLOCKED",
            "objective_basis": "BLOCKED_NO_VALID_OBJECTIVE",
            "primary_blocker_code": "LIVE_FINAL_GUARD_FAILED",
            "primary_blocker_message": "Parameter narrowing attempted live permission, live source, order submission, active config mutation, or scale-up permission.",
            "next_action": "Block the run, inspect parameter narrowing inputs, and keep live orders disabled.",
        }
    if not scope_matches:
        return {
            **report,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "narrowing_status": "BLOCKED",
            "primary_blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "primary_blocker_message": "Parameter narrowing scope does not match this dashboard session.",
            "next_action": "Regenerate parameter narrowing for the exact exchange, market, mode, and session shown here.",
        }
    if dependency_count_mismatch:
        return {
            **report,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "narrowing_status": "BLOCKED",
            "primary_blocker_code": "SCHEMA_IDENTITY_MISMATCH",
            "primary_blocker_message": "Parameter narrowing dependency counts do not match the validator dependency list.",
            "next_action": "Regenerate parameter narrowing after dependency validator registry review.",
        }
    if not all_dependencies_pass:
        return {
            **report,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "narrowing_status": "BLOCKED",
            "recommendation_scope": "BLOCKED",
            "parameter_write_scope": "BLOCKED",
            "primary_blocker_code": "PARAMETER_NARROWING_UNVERIFIED",
            "primary_blocker_message": "Parameter narrowing has dependency validators that are not PASS.",
            "next_action": "Resolve FAIL/BLOCKED/UNTESTED/STALE/TIMEOUT dependency validators before parameter review.",
        }
    if sample_insufficient:
        return {
            **report,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "narrowing_status": "BLOCKED",
            "recommendation_scope": "BLOCKED",
            "parameter_write_scope": "BLOCKED",
            "primary_blocker_code": "PARAMETER_NARROWING_UNVERIFIED",
            "primary_blocker_message": "Parameter narrowing lacks required PAPER or SHADOW sample coverage.",
            "next_action": "Collect more PAPER/SHADOW samples before narrowing parameter review.",
        }
    if over_narrowing:
        return {
            **report,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "narrowing_status": "BLOCKED",
            "recommendation_scope": "BLOCKED",
            "parameter_write_scope": "BLOCKED",
            "primary_blocker_code": "PARAMETER_NARROWING_UNVERIFIED",
            "primary_blocker_message": "Parameter narrowing is missing bounds, not actually narrower, or exceeds the maximum narrowing percentage.",
            "next_action": "Regenerate parameter narrowing with bounded paper/shadow proposal limits.",
        }
    if (
        narrowing_status == "PAPER_PARAMETER_REVIEW_ELIGIBLE"
        and recommendation_scope == "PAPER_PARAMETER_REVIEW_ONLY"
        and parameter_write_scope == "PROPOSAL_ONLY"
        and parameter_narrowing_report.get("narrowing_allowed_for_paper_ranking") is True
    ):
        return {
            **report,
            "status": "PAPER_PARAMETER_REVIEW_ELIGIBLE",
            "severity": "NORMAL",
            "color_token": "blue",
            "narrowing_allowed_for_paper_ranking": True,
            "primary_blocker_code": "LIVE_READY_MISSING",
            "primary_blocker_message": "Parameter narrowing can be reviewed for PAPER ranking only; not LIVE_READY.",
            "next_action": "Review PAPER parameter proposal only. Live orders, active config mutation, and scale-up remain blocked.",
        }
    return {
        **report,
        "status": "ACTIVE_ANALYSIS_ONLY",
        "severity": "WARNING",
        "color_token": "yellow",
        "primary_blocker_code": "PARAMETER_NARROWING_UNVERIFIED",
        "primary_blocker_message": "Parameter narrowing remains analysis-only and is not eligible for PAPER parameter review.",
        "next_action": "Continue PAPER/SHADOW evidence collection before parameter narrowing review.",
    }


def _execution_feedback_snapshot(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    optimizer_feedback_report: dict[str, Any] | None,
    summary_freshness: str,
) -> dict[str, Any]:
    base = {
        "title": "Execution Feedback",
        "truth_role": "dashboard_serving_truth",
        "source": "summary.json",
        "evidence_source": "NOT_LOADED",
        "feedback_report_id": None,
        "candidate_id": None,
        "strategy_id": None,
        "parameter_hash": None,
        "cost_basis": "UNVERIFIED",
        "execution_quality_status": "UNTESTED",
        "risk_review_status": "UNTESTED",
        "exposure_review_status": "UNTESTED",
        "drawdown_review_status": "UNTESTED",
        "net_ev_deviation_display": "UNVERIFIED",
        "slippage_deviation_display": "UNVERIFIED",
        "fee_deviation_display": "UNVERIFIED",
        "impact_deviation_display": "UNVERIFIED",
        "optimizer_ranking_action": "BLOCK_RANKING",
        "feedback_eligible": False,
        "promotion_eligible": False,
        "primary_blocker_code": "HARD_TRUTH_MISSING",
        "primary_blocker_message": "No expected-vs-realized PAPER/SHADOW execution feedback is loaded.",
        "next_action": "Collect PAPER/SHADOW execution feedback before using optimizer ranking.",
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    if summary_freshness != "PASS":
        return {
            **base,
            "status": "STALE",
            "severity": "WARNING",
            "color_token": "yellow",
            "primary_blocker_code": "LATENCY_TTL_EXPIRED",
            "primary_blocker_message": "Dashboard summary is stale; execution feedback display cannot be trusted.",
            "next_action": "Rerun PAPER to refresh dashboard sources before reviewing execution feedback.",
        }
    if not isinstance(optimizer_feedback_report, dict):
        return {
            **base,
            "status": "COLLECTING",
            "severity": "WARNING",
            "color_token": "yellow",
        }

    blockers = optimizer_feedback_report.get("blockers", [])
    first_blocker = blockers[0] if blockers and isinstance(blockers[0], dict) else {}
    scope_matches = (
        optimizer_feedback_report.get("exchange") == exchange
        and optimizer_feedback_report.get("market_type") == market_type
        and optimizer_feedback_report.get("mode") == mode
        and optimizer_feedback_report.get("session_id") == session_id
    )
    live_flag_drift = any(
        optimizer_feedback_report.get(flag) is True
        for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "promotion_eligible")
    ) or optimizer_feedback_report.get("mode") == "LIVE"
    hash_matches = optimizer_feedback_report.get("feedback_hash") == _optimizer_feedback_report_hash(optimizer_feedback_report)
    execution_status = optimizer_feedback_report.get("execution_quality_status", "UNTESTED")
    risk_status = optimizer_feedback_report.get("risk_review_status", "UNTESTED")
    exposure_status = optimizer_feedback_report.get("exposure_review_status", "UNTESTED")
    drawdown_status = optimizer_feedback_report.get("drawdown_review_status", "UNTESTED")
    ranking_action = optimizer_feedback_report.get("optimizer_ranking_action", "BLOCK_RANKING")
    feedback_eligible = optimizer_feedback_report.get("feedback_eligible") is True

    snapshot = {
        **base,
        "evidence_source": "optimizer_feedback_report",
        "feedback_report_id": optimizer_feedback_report.get("feedback_report_id"),
        "candidate_id": optimizer_feedback_report.get("candidate_id"),
        "strategy_id": optimizer_feedback_report.get("strategy_id"),
        "parameter_hash": optimizer_feedback_report.get("parameter_hash"),
        "cost_basis": optimizer_feedback_report.get("cost_basis", "UNVERIFIED"),
        "execution_quality_status": execution_status,
        "risk_review_status": risk_status,
        "exposure_review_status": exposure_status,
        "drawdown_review_status": drawdown_status,
        "net_ev_deviation_display": _format_bps(optimizer_feedback_report.get("net_ev_deviation_bps")),
        "slippage_deviation_display": _format_bps(optimizer_feedback_report.get("slippage_deviation_bps")),
        "fee_deviation_display": _format_bps(optimizer_feedback_report.get("fee_deviation_bps")),
        "impact_deviation_display": _format_bps(optimizer_feedback_report.get("impact_deviation_bps")),
        "optimizer_ranking_action": ranking_action,
        "feedback_eligible": feedback_eligible,
        "promotion_eligible": False,
        "primary_blocker_code": first_blocker.get("code")
        or optimizer_feedback_report.get("risk_review_blocker_code")
        or "HARD_TRUTH_MISSING",
        "primary_blocker_message": first_blocker.get("message")
        or "Execution feedback is analysis-only; live orders and scale-up remain blocked.",
    }
    if live_flag_drift:
        return {
            **snapshot,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "optimizer_ranking_action": "BLOCK_RANKING",
            "feedback_eligible": False,
            "primary_blocker_code": "LIVE_FINAL_GUARD_FAILED",
            "primary_blocker_message": "Execution feedback attempted to carry live, promotion, or scale permission.",
            "next_action": "Block the run, inspect feedback writer, and keep live orders disabled.",
        }
    if not hash_matches:
        return {
            **snapshot,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "optimizer_ranking_action": "BLOCK_RANKING",
            "feedback_eligible": False,
            "primary_blocker_code": "EVIDENCE_HASH_MISMATCH",
            "primary_blocker_message": "Execution feedback hash does not match its payload.",
            "next_action": "Regenerate optimizer feedback evidence before using ranking output.",
        }
    if not scope_matches:
        return {
            **snapshot,
            "status": "BLOCKED",
            "severity": "WARNING",
            "color_token": "yellow",
            "optimizer_ranking_action": "BLOCK_RANKING",
            "feedback_eligible": False,
            "primary_blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "primary_blocker_message": "Execution feedback scope does not match this dashboard session.",
            "next_action": "Regenerate feedback for the exact exchange, market, mode, and session shown here.",
        }

    review_pass = (
        execution_status == "PASS"
        and risk_status == "PASS"
        and exposure_status == "PASS"
        and drawdown_status == "PASS"
    )
    if feedback_eligible and review_pass and ranking_action == "ALLOW_RANKING":
        return {
            **snapshot,
            "status": "READY_FOR_PAPER_RANKING_REVIEW",
            "severity": "NORMAL",
            "color_token": "blue",
            "primary_blocker_code": "LIVE_READY_MISSING",
            "primary_blocker_message": "Execution feedback can inform PAPER ranking only; live orders and scale-up remain blocked.",
            "next_action": "Review PAPER ranking impact with cost, risk, exposure, and drawdown checks visible.",
        }
    if feedback_eligible or ranking_action == "ALLOW_RANKING":
        return {
            **snapshot,
            "status": "BLOCKED",
            "severity": "ERROR",
            "color_token": "red",
            "optimizer_ranking_action": "BLOCK_RANKING",
            "feedback_eligible": False,
            "primary_blocker_code": "HARD_TRUTH_MISSING",
            "primary_blocker_message": "Execution feedback tried to allow ranking without all execution and risk reviews PASS.",
            "next_action": "Regenerate feedback with execution quality, risk, exposure, and drawdown reviews.",
        }
    return {
        **snapshot,
        "status": "COLLECTING",
        "severity": "WARNING",
        "color_token": "yellow",
        "next_action": "Collect more expected-vs-realized cost and risk feedback before ranking.",
    }


def _operation_status(
    *,
    heartbeat: dict[str, Any] | None,
    summary_freshness: str,
    heartbeat_freshness: str,
    startup_freshness: str,
    portfolio_snapshot: dict[str, Any] | None,
    primary_blocker: str | None,
) -> dict[str, Any]:
    heartbeat_status = heartbeat.get("heartbeat_status") if isinstance(heartbeat, dict) else "STALE"
    engine_state = heartbeat.get("engine_state") if isinstance(heartbeat, dict) else "UNKNOWN"
    live_orders_blocked = True
    portfolio_status = portfolio_snapshot.get("status") if isinstance(portfolio_snapshot, dict) else "UNVERIFIED"
    portfolio_blocker = portfolio_snapshot.get("blocking_reason") if isinstance(portfolio_snapshot, dict) else None
    portfolio_next_action = portfolio_snapshot.get("next_action") if isinstance(portfolio_snapshot, dict) else None
    portfolio_next_action_text = str(
        portfolio_next_action or "Run PAPER with a verified paper portfolio ledger before trusting portfolio values."
    )
    if heartbeat_status == "PASS" and heartbeat_freshness == "PASS":
        if portfolio_status == "STALE":
            return {
                "status": "CHECKING_SAFE_MODE",
                "severity": "WARNING",
                "color_token": "yellow",
                "label": "Running with stale portfolio",
                "message": "Program heartbeat is fresh, but portfolio cash, equity, positions, or PnL are stale.",
                "recovery_hint": portfolio_next_action_text,
                "launcher_execution_mode": "SAFE_BOOT_OR_EXPLICIT_MONITOR",
                "runtime_presence": "DASHBOARD_HEARTBEAT_ONLY",
                "operator_meaning": "The dashboard heartbeat is fresh, but it does not prove a continuous PAPER engine is updating portfolio values.",
                "source": "summary.json",
                "engine_state": engine_state or "BOOTSTRAP_READ_ONLY",
                "heartbeat_status": "PASS",
                "summary_freshness_status": summary_freshness,
                "startup_freshness_status": startup_freshness,
                "portfolio_status": portfolio_status,
                "portfolio_blocking_reason": portfolio_blocker,
                "portfolio_next_action": portfolio_next_action_text,
                "primary_blocker": portfolio_blocker or primary_blocker or "LATENCY_TTL_EXPIRED",
                "live_orders_blocked": live_orders_blocked,
            }
        if portfolio_status != "VERIFIED":
            return {
                "status": "CHECKING_SAFE_MODE",
                "severity": "WARNING",
                "color_token": "yellow",
                "label": "Running without verified portfolio",
                "message": "Program heartbeat is fresh, but portfolio cash, equity, positions, and PnL are not verified yet.",
                "recovery_hint": portfolio_next_action_text,
                "launcher_execution_mode": "SAFE_BOOT_OR_EXPLICIT_MONITOR",
                "runtime_presence": "DASHBOARD_HEARTBEAT_ONLY",
                "operator_meaning": "The dashboard heartbeat is fresh, but it does not prove a continuous PAPER engine is updating portfolio values.",
                "source": "summary.json",
                "engine_state": engine_state or "BOOTSTRAP_READ_ONLY",
                "heartbeat_status": "PASS",
                "summary_freshness_status": summary_freshness,
                "startup_freshness_status": startup_freshness,
                "portfolio_status": portfolio_status,
                "portfolio_blocking_reason": portfolio_blocker,
                "portfolio_next_action": portfolio_next_action_text,
                "primary_blocker": portfolio_blocker or primary_blocker or "HARD_TRUTH_MISSING",
                "live_orders_blocked": live_orders_blocked,
            }
        return {
            "status": "RUNNING_SAFE_MODE",
            "severity": "NORMAL",
            "color_token": "green",
            "label": "Running safely",
            "message": "Program heartbeat is fresh for this safe boot; SAFE_MODE is active and live orders remain blocked.",
            "recovery_hint": "No recovery needed for the latest safe boot. Use explicit PAPER runtime evidence before treating portfolio or strategy output as continuously updated.",
            "launcher_execution_mode": "SAFE_BOOT_OR_EXPLICIT_MONITOR",
            "runtime_presence": "DASHBOARD_HEARTBEAT_ONLY",
            "operator_meaning": "This status means the latest launcher/dashboard heartbeat is fresh. It is not live readiness and it is not proof that a continuous PAPER engine is running.",
            "source": "heartbeat.json",
            "engine_state": engine_state or "BOOTSTRAP_READ_ONLY",
            "heartbeat_status": "PASS",
            "summary_freshness_status": summary_freshness,
            "startup_freshness_status": startup_freshness,
            "portfolio_status": portfolio_status,
            "portfolio_blocking_reason": portfolio_blocker,
            "portfolio_next_action": portfolio_next_action_text,
            "primary_blocker": primary_blocker,
            "live_orders_blocked": live_orders_blocked,
        }
    if heartbeat_freshness == "STALE" or heartbeat_status == "STALE":
        status = "STALE_HEARTBEAT"
        label = "Heartbeat needs refresh"
        message = "Heartbeat is stale or missing; dashboard values may be old."
        recovery_hint = "Rerun the PAPER launcher and wait for a fresh heartbeat before reviewing cash, equity, positions, or decisions."
    else:
        status = "CHECKING_SAFE_MODE"
        label = "Needs attention"
        message = "Program is in safe monitoring, but one or more dashboard sources need attention."
        recovery_hint = "Review the highlighted source artifact, rerun PAPER if it is stale, and keep live orders blocked."
    return {
        "status": status,
        "severity": "WARNING",
        "color_token": "yellow",
        "label": label,
        "message": message,
        "recovery_hint": recovery_hint,
        "launcher_execution_mode": "SAFE_BOOT_OR_EXPLICIT_MONITOR",
        "runtime_presence": "HEARTBEAT_STALE_OR_SOURCE_ATTENTION_REQUIRED",
        "operator_meaning": "The dashboard cannot prove current operation until the heartbeat and source artifacts are refreshed; it does not prove a continuous PAPER engine is running.",
        "source": "heartbeat.json",
        "engine_state": engine_state or "UNKNOWN",
        "heartbeat_status": heartbeat_status or "STALE",
        "summary_freshness_status": summary_freshness,
        "startup_freshness_status": startup_freshness,
        "portfolio_status": portfolio_status,
        "portfolio_blocking_reason": portfolio_blocker,
        "portfolio_next_action": portfolio_next_action_text,
        "primary_blocker": primary_blocker,
        "live_orders_blocked": live_orders_blocked,
    }


def _scope_matches(report: dict[str, Any], *, exchange: str, market_type: str, mode: str, session_id: str) -> bool:
    return (
        report.get("exchange") == exchange
        and report.get("market_type") == market_type
        and report.get("mode") == mode
        and report.get("session_id") == session_id
    )


def _reconciliation_recovery_summary(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    reconciliation_report: dict[str, Any] | None,
    restart_recovery_report: dict[str, Any] | None,
) -> dict[str, Any]:
    reconciliation_loaded = isinstance(reconciliation_report, dict)
    restart_loaded = isinstance(restart_recovery_report, dict)
    reconciliation_status = "NOT_LOADED"
    restart_status = "NOT_LOADED"
    reconciliation_validation_status = "UNTESTED"
    restart_validation_status = "UNTESTED"
    ledger_state = "NOT_LOADED"
    single_writer_state = "NOT_LOADED"
    idempotency_state = "NOT_LOADED"
    mismatch_count = 0
    primary_blocker = "RECONCILIATION_REQUIRED"
    source = "summary.json"
    issue_messages: list[str] = []

    if reconciliation_loaded:
        source = "reconciliation_report.json"
        reconciliation_status = str(reconciliation_report.get("reconciliation_status", "INVALID"))
        reconciliation_result = validate_reconciliation_report(reconciliation_report)
        reconciliation_validation_status = reconciliation_result.status
        if reconciliation_result.status != "PASS":
            reconciliation_status = "INVALID"
            ledger_state = "INVALID"
            primary_blocker = reconciliation_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH"
            issue_messages.append(f"Reconciliation report invalid: {reconciliation_result.message}")
        elif not _scope_matches(reconciliation_report, exchange=exchange, market_type=market_type, mode=mode, session_id=session_id):
            reconciliation_status = "INVALID"
            ledger_state = "INVALID"
            primary_blocker = "SNAPSHOT_SCOPE_MISMATCH"
            issue_messages.append("Reconciliation report scope does not match this dashboard.")
        else:
            mismatch_count = len(reconciliation_report.get("mismatches", [])) if isinstance(reconciliation_report.get("mismatches"), list) else 0
            primary_blocker = reconciliation_report.get("primary_blocker_code") or primary_blocker
            if reconciliation_status == "PASS":
                ledger_state = "PAPER_LEDGER_MATCHED"
            elif reconciliation_status in {"STALE", "UNKNOWN", "MISMATCH", "FAIL"}:
                ledger_state = "RECONCILE_REQUIRED"
                primary_blocker = reconciliation_report.get("primary_blocker_code") or "RECONCILIATION_REQUIRED"
                issue_messages.append("Reconciliation report requires operator review before any trading review.")
            else:
                reconciliation_status = "INVALID"
                ledger_state = "INVALID"
                primary_blocker = "SCHEMA_IDENTITY_MISMATCH"
                issue_messages.append("Reconciliation report status is unknown.")

    if restart_loaded:
        source = "restart_recovery_report.json" if not reconciliation_loaded else source
        restart_status = str(restart_recovery_report.get("restart_recovery_status", "INVALID"))
        restart_result = validate_restart_recovery_report(restart_recovery_report)
        restart_validation_status = restart_result.status
        if restart_result.status != "PASS":
            restart_status = "INVALID"
            single_writer_state = "INVALID"
            idempotency_state = "INVALID"
            primary_blocker = restart_result.blocker_code or primary_blocker
            issue_messages.append(f"Restart recovery report invalid: {restart_result.message}")
        elif not _scope_matches(restart_recovery_report, exchange=exchange, market_type=market_type, mode=mode, session_id=session_id):
            restart_status = "INVALID"
            single_writer_state = "INVALID"
            idempotency_state = "INVALID"
            primary_blocker = "SNAPSHOT_SCOPE_MISMATCH"
            issue_messages.append("Restart recovery report scope does not match this dashboard.")
        elif restart_status == "PASS":
            single_writer_state = "RECOVERED"
            idempotency_state = "RECOVERED"
        elif restart_status == "BLOCKED":
            single_writer_state = "RECONCILE_REQUIRED"
            idempotency_state = "RECONCILE_REQUIRED"
            primary_blocker = restart_recovery_report.get("primary_blocker_code") or "RECONCILIATION_REQUIRED"
            issue_messages.append("Restart recovery requires SAFE_MODE_RECONCILE before paper review.")
        else:
            restart_status = "INVALID"
            single_writer_state = "INVALID"
            idempotency_state = "INVALID"
            primary_blocker = "SCHEMA_IDENTITY_MISMATCH"
            issue_messages.append("Restart recovery status is unknown.")

    if not reconciliation_loaded and not restart_loaded:
        status = "NOT_LOADED"
        severity = "WARNING"
        color_token = "yellow"
        one_line_blocker = "RECONCILIATION_REQUIRED: ledger/reconciliation and restart recovery evidence are not loaded."
        next_action = "Run PAPER with reconciliation and restart recovery artifacts, then review this panel before live review."
        message = "Ledger/reconciliation evidence is not loaded; portfolio values remain display-only."
    elif (
        reconciliation_status == "PASS"
        and restart_status == "PASS"
        and reconciliation_validation_status == "PASS"
        and restart_validation_status == "PASS"
        and not issue_messages
    ):
        status = "PASS"
        severity = "NORMAL"
        color_token = "green"
        primary_blocker = "LIVE_READY_MISSING"
        one_line_blocker = "LIVE_READY_MISSING: PAPER ledger checks passed, but live review remains blocked."
        next_action = "Continue PAPER monitoring; keep live blocked until external live-review evidence exists."
        message = "PAPER ledger, reconciliation, restart recovery, and idempotency checks are aligned for display review."
    elif "INVALID" in {reconciliation_status, restart_status} or "FAIL" in {reconciliation_validation_status, restart_validation_status} or "BLOCKED" in {reconciliation_validation_status, restart_validation_status}:
        status = "INVALID"
        severity = "ERROR"
        color_token = "red"
        one_line_blocker = f"{primary_blocker}: ledger or recovery evidence is invalid for this dashboard."
        next_action = "Stop review, regenerate scoped PAPER reconciliation/restart artifacts, and rerun validators."
        message = issue_messages[0] if issue_messages else "Ledger/recovery evidence failed validation."
    elif reconciliation_status in {"MISMATCH", "FAIL"} or restart_status == "BLOCKED":
        status = "BLOCKED"
        severity = "ERROR"
        color_token = "red"
        one_line_blocker = f"{primary_blocker}: ledger/reconciliation is not safe for review."
        next_action = "Do not continue strategy review; reconcile PAPER ledger, snapshots, and restart recovery first."
        message = issue_messages[0] if issue_messages else "Ledger/reconciliation requires recovery before review."
    else:
        status = "RECONCILE_REQUIRED"
        severity = "WARNING"
        color_token = "yellow"
        one_line_blocker = f"{primary_blocker}: refresh or complete ledger/reconciliation evidence."
        next_action = "Refresh PAPER reconciliation and restart recovery artifacts before treating portfolio values as review-ready."
        message = issue_messages[0] if issue_messages else "Ledger/reconciliation evidence is incomplete or stale."

    return {
        "title": "Ledger & Reconciliation",
        "status": status,
        "severity": severity,
        "color_token": color_token,
        "truth_role": "dashboard_serving_truth",
        "source": source,
        "reconciliation_status": reconciliation_status,
        "reconciliation_validation_status": reconciliation_validation_status,
        "restart_recovery_status": restart_status,
        "restart_recovery_validation_status": restart_validation_status,
        "ledger_state": ledger_state,
        "single_writer_state": single_writer_state,
        "idempotency_state": idempotency_state,
        "mismatch_count": mismatch_count,
        "primary_blocker_code": primary_blocker,
        "one_line_blocker": one_line_blocker,
        "message": message,
        "next_operator_action": next_action,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "can_submit_order": False,
    }


def _first_blocker(*codes: str | None) -> str | None:
    for code in codes:
        if code:
            return code
    return None


def build_read_only_dashboard_shell(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    summary: dict[str, Any] | None,
    heartbeat: dict[str, Any] | None,
    startup_probe: dict[str, Any] | None,
    stability_history: dict[str, Any] | None = None,
    paper_operation_gate_report: dict[str, Any] | None = None,
    paper_exposure_quality_report: dict[str, Any] | None = None,
    reconciliation_report: dict[str, Any] | None = None,
    restart_recovery_report: dict[str, Any] | None = None,
    upbit_paper_runtime_recovery_guard_report: dict[str, Any] | None = None,
    upbit_public_rest_continuity_history: dict[str, Any] | None = None,
    optimizer_feedback_report: dict[str, Any] | None = None,
    convergence_assessment_report: dict[str, Any] | None = None,
    exploration_exploitation_policy: dict[str, Any] | None = None,
    parameter_narrowing_report: dict[str, Any] | None = None,
    profitability_maturity_rollup_report: dict[str, Any] | None = None,
    candidate_scorecard: dict[str, Any] | None = None,
    shadow_runtime_writer_report: dict[str, Any] | None = None,
    shadow_runtime_harness_report: dict[str, Any] | None = None,
    shadow_persistent_runtime_report: dict[str, Any] | None = None,
    shadow_runtime_orchestration_report: dict[str, Any] | None = None,
    source_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    generated_at_utc = utc_now()
    paths = source_paths or {
        "summary": "system/runtime/upbit/krw_spot/paper/summary.json",
        "heartbeat": "system/runtime/upbit/krw_spot/paper/heartbeat.json",
        "startup_probe": "system/runtime/upbit/krw_spot/paper/startup_probe.json",
        "shadow_runtime_writer": f"system/runtime/{exchange.lower()}/{market_type.lower()}/shadow/{session_id}/shadow_observation/shadow_observation_runtime_artifact_writer_report.json",
        "shadow_runtime_harness": f"system/runtime/{exchange.lower()}/{market_type.lower()}/shadow/{session_id}/actual_runtime_harness_report.json",
        "shadow_persistent_runtime": f"system/runtime/{exchange.lower()}/{market_type.lower()}/shadow/{session_id}/shadow_observation_persistent_runtime_report.json",
        "shadow_runtime_orchestration": f"system/runtime/{exchange.lower()}/{market_type.lower()}/shadow/{session_id}/runtime_orchestration_report.json",
        "upbit_paper_runtime_recovery_guard": f"system/runtime/{exchange.lower()}/{market_type.lower()}/paper/{session_id}/paper_runtime/upbit_paper_runtime_recovery_guard_report.json",
        "upbit_public_rest_continuity_history": f"system/runtime/{exchange.lower()}/{market_type.lower()}/paper/{session_id}/market_data/public/rest_continuity_history.json",
        "candidate_scorecard": f"system/runtime/{exchange.lower()}/{market_type.lower()}/paper/{session_id}/profitability/candidate_scorecard.json",
    }

    summary_live = summary.get("live_ready", {}) if isinstance(summary, dict) else {}
    startup_blocker = startup_probe.get("primary_blocker_code") if isinstance(startup_probe, dict) else "HARD_TRUTH_MISSING"
    heartbeat_blocker = heartbeat.get("primary_blocker_code") if isinstance(heartbeat, dict) else "LATENCY_TTL_EXPIRED"
    summary_blocker = summary.get("blocking_reason") if isinstance(summary, dict) else "HARD_TRUTH_MISSING"
    live_blocker = summary_live.get("primary_blocker_code") or "LIVE_READY_MISSING"
    primary_blocker = _first_blocker(summary_blocker, startup_blocker, heartbeat_blocker, live_blocker)

    summary_freshness = _freshness_from_generated_at(summary)
    heartbeat_freshness = (
        _freshness_from_generated_at(heartbeat)
        if heartbeat and heartbeat.get("heartbeat_status") == "PASS"
        else "STALE"
    )
    startup_freshness = _freshness_from_generated_at(startup_probe)

    source_artifacts = [
        _source_artifact("SUMMARY", paths["summary"], summary is not None, summary_freshness),
        _source_artifact(
            "HEARTBEAT",
            paths["heartbeat"],
            heartbeat is not None,
            heartbeat_freshness,
        ),
        _source_artifact("STARTUP_PROBE", paths["startup_probe"], startup_probe is not None, startup_freshness),
    ]
    if isinstance(candidate_scorecard, dict):
        source_artifacts.append(
            _source_artifact(
                "CANDIDATE_SCORECARD",
                paths.get(
                    "candidate_scorecard",
                    f"system/runtime/{exchange.lower()}/{market_type.lower()}/paper/{session_id}/profitability/candidate_scorecard.json",
                ),
                True,
                _freshness_from_generated_at(candidate_scorecard),
            )
        )
    if isinstance(shadow_runtime_writer_report, dict):
        writer_freshness = (
            _freshness_from_generated_at(shadow_runtime_writer_report)
            if shadow_runtime_writer_report.get("writer_status") == "PASS"
            and shadow_runtime_writer_report.get("dashboard_visibility_status") == "VISIBLE_AS_STUB_ONLY"
            and shadow_runtime_writer_report.get("artifact_truth_role") == "shadow_runtime_stub_display_truth_only"
            and shadow_runtime_writer_report.get("live_order_allowed") is False
            and shadow_runtime_writer_report.get("can_live_trade") is False
            and shadow_runtime_writer_report.get("scale_up_allowed") is False
            else "STALE"
        )
        source_artifacts.append(
            _source_artifact(
                "SHADOW_RUNTIME_WRITER",
                paths.get("shadow_runtime_writer", "system/runtime/upbit/krw_spot/shadow/unknown/shadow_observation/shadow_observation_runtime_artifact_writer_report.json"),
                True,
                writer_freshness,
            )
        )
    shadow_persistent_runtime_status = _shadow_persistent_runtime_status(shadow_persistent_runtime_report)
    if isinstance(shadow_persistent_runtime_report, dict):
        persistent_freshness = "PASS" if shadow_persistent_runtime_status["status"] == "STUB_ONLY" else "STALE"
        source_artifacts.append(
            _source_artifact(
                "SHADOW_PERSISTENT_RUNTIME",
                paths.get("shadow_persistent_runtime", "system/runtime/upbit/krw_spot/shadow/unknown/shadow_observation_persistent_runtime_report.json"),
                True,
                persistent_freshness,
            )
        )
    shadow_runtime_harness_status = _shadow_runtime_harness_status(shadow_runtime_harness_report)
    if isinstance(shadow_runtime_harness_report, dict):
        harness_freshness = "PASS" if shadow_runtime_harness_status["status"] == "SHORT_WINDOW_EXECUTED" else "STALE"
        source_artifacts.append(
            _source_artifact(
                "SHADOW_RUNTIME_HARNESS",
                paths.get("shadow_runtime_harness", "system/runtime/upbit/krw_spot/shadow/unknown/actual_runtime_harness_report.json"),
                True,
                harness_freshness,
            )
        )
    shadow_runtime_orchestration_status = _shadow_runtime_orchestration_status(
        shadow_runtime_orchestration_report,
        shadow_runtime_harness_status=shadow_runtime_harness_status,
        shadow_persistent_runtime_status=shadow_persistent_runtime_status,
    )
    if isinstance(shadow_runtime_orchestration_report, dict):
        orchestration_freshness = "PASS" if shadow_runtime_orchestration_status["status"] == "BOUNDARY_VERIFIED" else "STALE"
        source_artifacts.append(
            _source_artifact(
                "SHADOW_RUNTIME_ORCHESTRATION",
                paths.get("shadow_runtime_orchestration", "system/runtime/upbit/krw_spot/shadow/unknown/runtime_orchestration_report.json"),
                True,
                orchestration_freshness,
            )
        )
    paper_runtime_recovery_guard_status = _paper_runtime_recovery_guard_status(
        report=upbit_paper_runtime_recovery_guard_report,
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
    )
    if isinstance(upbit_paper_runtime_recovery_guard_report, dict):
        recovery_guard_freshness = (
            "PASS"
            if _freshness_from_generated_at(upbit_paper_runtime_recovery_guard_report) == "PASS"
            and paper_runtime_recovery_guard_status["status"] in {"PASS", "BLOCKED"}
            else "STALE"
        )
        source_artifacts.append(
            _source_artifact(
                "PAPER_RUNTIME_RECOVERY_GUARD",
                paths.get(
                    "upbit_paper_runtime_recovery_guard",
                    "system/runtime/upbit/krw_spot/paper/unknown/paper_runtime/upbit_paper_runtime_recovery_guard_report.json",
                ),
                True,
                recovery_guard_freshness,
            )
        )
    market_data_continuity_status = _market_data_continuity_status(
        report=upbit_public_rest_continuity_history,
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
    )
    if isinstance(upbit_public_rest_continuity_history, dict):
        continuity_freshness = (
            "PASS"
            if _freshness_from_generated_at(upbit_public_rest_continuity_history) == "PASS"
            and market_data_continuity_status["status"] in {"PASS", "BLOCKED"}
            else "STALE"
        )
        source_artifacts.append(
            _source_artifact(
                "MARKET_DATA_CONTINUITY_HISTORY",
                paths.get(
                    "upbit_public_rest_continuity_history",
                    "system/runtime/upbit/krw_spot/paper/unknown/market_data/public/rest_continuity_history.json",
                ),
                True,
                continuity_freshness,
            )
        )
    position_snapshot = _position_snapshot(summary, summary_freshness)
    portfolio_snapshot = _portfolio_snapshot(exchange, market_type, mode, summary, summary_freshness)
    decision_trace = _decision_trace(summary, primary_blocker, position_snapshot)
    operation_status = _operation_status(
        heartbeat=heartbeat,
        summary_freshness=summary_freshness,
        heartbeat_freshness=heartbeat_freshness,
        startup_freshness=startup_freshness,
        portfolio_snapshot=portfolio_snapshot,
        primary_blocker=primary_blocker,
    )
    reconciliation_recovery_summary = _reconciliation_recovery_summary(
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        reconciliation_report=reconciliation_report,
        restart_recovery_report=restart_recovery_report,
    )
    recent_events = _recent_events(summary, summary_freshness, decision_trace, position_snapshot, operation_status)
    stability_trends = _stability_trends(
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        heartbeat=heartbeat,
        source_artifacts=source_artifacts,
        operation_status=operation_status,
        stability_history=stability_history,
    )
    long_run_operator_summary = _long_run_operator_summary(
        operation_status=operation_status,
        stability_trends=stability_trends,
        source_artifacts=source_artifacts,
    )
    runtime_evidence_boundary = _runtime_evidence_boundary_status(
        long_run_operator_summary=long_run_operator_summary,
        shadow_runtime_harness_status=shadow_runtime_harness_status,
        shadow_persistent_runtime_status=shadow_persistent_runtime_status,
        shadow_runtime_orchestration_status=shadow_runtime_orchestration_status,
    )
    profitability_maturity = _profitability_maturity(
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        paper_operation_gate_report=paper_operation_gate_report,
        profitability_maturity_rollup_report=profitability_maturity_rollup_report,
        candidate_scorecard=candidate_scorecard,
        summary_freshness=summary_freshness,
    )
    convergence_assessment_status = _convergence_assessment_status(
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        convergence_assessment_report=convergence_assessment_report,
        summary_freshness=summary_freshness,
    )
    exploration_policy_status = _exploration_policy_status(
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        exploration_exploitation_policy=exploration_exploitation_policy,
        summary_freshness=summary_freshness,
    )
    parameter_narrowing_status = _parameter_narrowing_status(
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        parameter_narrowing_report=parameter_narrowing_report,
        summary_freshness=summary_freshness,
    )
    risk_exposure_snapshot = _risk_exposure_snapshot(
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        summary=summary,
        summary_freshness=summary_freshness,
        portfolio_snapshot=portfolio_snapshot,
        primary_blocker=primary_blocker,
        paper_exposure_quality_report=paper_exposure_quality_report,
    )
    execution_feedback_snapshot = _execution_feedback_snapshot(
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        optimizer_feedback_report=optimizer_feedback_report,
        summary_freshness=summary_freshness,
    )
    operator_action_summary = _operator_action_summary(
        primary_blocker=primary_blocker,
        operation_status=operation_status,
        long_run_operator_summary=long_run_operator_summary,
        profitability_maturity=profitability_maturity,
        risk_exposure_snapshot=risk_exposure_snapshot,
        execution_feedback_snapshot=execution_feedback_snapshot,
        decision_trace=decision_trace,
    )
    operator_workflow_summary = _operator_workflow_summary(
        operator_action_summary=operator_action_summary,
        long_run_operator_summary=long_run_operator_summary,
        profitability_maturity=profitability_maturity,
        execution_feedback_snapshot=execution_feedback_snapshot,
    )

    engine = summary.get("engine", {}) if isinstance(summary, dict) else {}
    startup_status = summary.get("startup", {}) if isinstance(summary, dict) else {}
    connectivity = summary.get("connectivity", {}) if isinstance(summary, dict) else {}
    resources = summary.get("resources", {}) if isinstance(summary, dict) else {}

    shell = {
        "schema_id": READ_ONLY_DASHBOARD_SCHEMA_ID,
        "project_id": "TRADER_1",
        "generated_at_utc": generated_at_utc,
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "dashboard_shell_status": "DISPLAY_ONLY_BLOCKED",
        "truth_role": "dashboard_serving_truth",
        "display_only": True,
        "dashboard_truth_only": True,
        "source_artifacts": source_artifacts,
        "dashboard_refresh_policy": {
            "title": "Dashboard Data Freshness",
            "status": "AUTO_REFRESH_ENABLED",
            "truth_role": "dashboard_serving_truth",
            "source": "heartbeat.json",
            "generated_at_utc": generated_at_utc,
            "auto_refresh_interval_seconds": DASHBOARD_AUTO_REFRESH_SECONDS,
            "stale_after_seconds": SOURCE_FRESHNESS_MAX_AGE_SECONDS,
            "client_stale_guard_enabled": True,
            "refresh_mode": "LOCAL_FILE_RELOAD",
            "next_action": "Keep the PAPER safe monitor running. If this page turns stale, rerun PAPER before trusting dashboard values.",
            "display_only": True,
            "dashboard_truth_only": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
        "operation_status": operation_status,
        "reconciliation_recovery_summary": reconciliation_recovery_summary,
        "stability_trends": stability_trends,
        "long_run_operator_summary": long_run_operator_summary,
        "market_data_continuity_status": market_data_continuity_status,
        "shadow_runtime_harness_status": shadow_runtime_harness_status,
        "shadow_persistent_runtime_status": shadow_persistent_runtime_status,
        "paper_runtime_recovery_guard_status": paper_runtime_recovery_guard_status,
        "runtime_evidence_boundary": runtime_evidence_boundary,
        "shadow_runtime_orchestration_status": shadow_runtime_orchestration_status,
        "operator_action_summary": operator_action_summary,
        "operator_workflow_summary": operator_workflow_summary,
        "profitability_maturity": profitability_maturity,
        "convergence_assessment_status": convergence_assessment_status,
        "exploration_policy_status": exploration_policy_status,
        "parameter_narrowing_status": parameter_narrowing_status,
        "risk_exposure_snapshot": risk_exposure_snapshot,
        "execution_feedback_snapshot": execution_feedback_snapshot,
        "decision_trace": decision_trace,
        "recent_events": recent_events,
        "portfolio_snapshot": portfolio_snapshot,
        "position_snapshot": position_snapshot,
        "panels": [
            _panel("Engine", engine.get("status", "SAFE_MODE"), "summary.json", engine.get("message")),
            _panel("Startup", startup_status.get("status", "BLOCKED"), "startup_probe.json", startup_status.get("message")),
            _panel("Heartbeat", connectivity.get("status", "STALE"), "heartbeat.json", connectivity.get("message")),
            _panel("Resources", resources.get("status", "UNTESTED"), "heartbeat.json", resources.get("message")),
            _panel("Live Orders", "BLOCKED", "summary.json", "LIVE ORDERS BLOCKED"),
        ],
        "primary_status_text": "RUNNING SAFE MODE - READ ONLY, LIVE ORDERS BLOCKED",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "can_submit_order": False,
        "final_action": "NO_TRADE" if primary_blocker else "SAFE_MODE",
        "blocking_reason": primary_blocker,
        "next_action": "continue read-only monitoring; resolve blockers before any trading review",
        "forbidden_wording_detected": False,
        "dashboard_hash": "",
    }
    shell["dashboard_hash"] = dashboard_shell_hash(shell)
    return shell


def _display_text(shell: dict[str, Any]) -> list[str]:
    values = [str(shell.get("primary_status_text", "")), str(shell.get("next_action", ""))]
    operation = shell.get("operation_status", {})
    if isinstance(operation, dict):
        values.extend(
            str(operation.get(key, ""))
            for key in (
                "status",
                "severity",
                "label",
                "message",
                "primary_blocker",
                "launcher_execution_mode",
                "runtime_presence",
                "operator_meaning",
            )
        )
    shadow_harness = shell.get("shadow_runtime_harness_status", {})
    if isinstance(shadow_harness, dict):
        values.extend(
            str(shadow_harness.get(key, ""))
            for key in (
                "status",
                "runtime_evidence_status",
                "optimizer_input_role",
                "primary_blocker_code",
                "one_line_summary",
                "next_operator_action",
            )
        )
    shadow_persistent = shell.get("shadow_persistent_runtime_status", {})
    if isinstance(shadow_persistent, dict):
        values.extend(
            str(shadow_persistent.get(key, ""))
            for key in (
                "status",
                "runtime_duration_evidence_source",
                "duration_evidence_role",
                "estimated_runtime_seconds",
                "observed_runtime_seconds",
                "optimizer_input_role",
                "primary_blocker_code",
                "one_line_summary",
                "next_operator_action",
            )
        )
    paper_recovery_guard = shell.get("paper_runtime_recovery_guard_status", {})
    if isinstance(paper_recovery_guard, dict):
        values.extend(
            str(paper_recovery_guard.get(key, ""))
            for key in (
                "status",
                "latest_cycle_status",
                "resume_action",
                "paper_runtime_resume_allowed",
                "primary_blocker_code",
                "one_line_summary",
                "next_operator_action",
            )
        )
    runtime_boundary = shell.get("runtime_evidence_boundary", {})
    if isinstance(runtime_boundary, dict):
        values.extend(
            str(runtime_boundary.get(key, ""))
            for key in (
                "status",
                "actual_long_run_evidence_status",
                "short_window_evidence_status",
                "stub_runtime_evidence_status",
                "one_line_summary",
                "stub_boundary_message",
                "primary_blocker_code",
                "next_operator_action",
            )
        )
    reconciliation = shell.get("reconciliation_recovery_summary", {})
    if isinstance(reconciliation, dict):
        values.extend(
            str(reconciliation.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "message",
                "one_line_blocker",
                "next_operator_action",
                "reconciliation_status",
                "restart_recovery_status",
            )
        )
    stability = shell.get("stability_trends", {})
    if isinstance(stability, dict):
        values.extend(str(stability.get(key, "")) for key in ("title", "status", "severity", "summary", "history_window"))
        for metric in stability.get("metrics", []):
            if isinstance(metric, dict):
                values.extend(str(metric.get(key, "")) for key in ("metric_id", "label", "status", "value_display", "detail", "source", "trend_direction"))
    long_run = shell.get("long_run_operator_summary", {})
    if isinstance(long_run, dict):
        values.extend(
            str(long_run.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "summary",
                "history_window",
                "stable_sample_rate_display",
                "degraded_sample_rate_display",
                "stale_sample_rate_display",
                "latency_trend_status",
                "error_frequency_status",
                "retry_trend_status",
                "dashboard_refresh_delay_status",
                "resource_pressure_status",
                "primary_blocker_code",
                "primary_blocker_message",
                "next_action",
            )
        )
    market_data = shell.get("market_data_continuity_status", {})
    if isinstance(market_data, dict):
        values.extend(
            str(market_data.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "source",
                "evidence_role",
                "symbol",
                "latest_attempt_status",
                "primary_blocker_code",
                "one_line_summary",
                "next_operator_action",
            )
        )
    operator_action = shell.get("operator_action_summary", {})
    if isinstance(operator_action, dict):
        values.extend(
            str(operator_action.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "workflow_step",
                "primary_action",
                "primary_action_label",
                "primary_blocker_code",
                "one_line_blocker",
                "next_operator_action",
                "decision_final_action",
            )
        )
    workflow = shell.get("operator_workflow_summary", {})
    if isinstance(workflow, dict):
        values.extend(
            str(workflow.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "current_step",
                "summary",
                "paper_evidence_status",
                "execution_feedback_status",
                "live_blocker_code",
            )
        )
        for step in workflow.get("steps", []):
            if isinstance(step, dict):
                values.extend(str(step.get(key, "")) for key in ("step_id", "label", "status", "detail", "action_kind"))
    maturity = shell.get("profitability_maturity", {})
    if isinstance(maturity, dict):
        values.extend(
            str(maturity.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "sample_summary",
                "cost_evidence_status",
                "entry_reason_status",
                "no_trade_reason_status",
                "maturity_gap_status",
                "maturity_gap_summary",
                "optimizer_ranking_action",
                "candidate_scorecard_source",
                "candidate_scorecard_status",
                "candidate_scorecard_candidate_id",
                "candidate_scorecard_strategy_id",
                "candidate_scorecard_symbol",
                "candidate_scorecard_objective_basis",
                "candidate_scorecard_net_ev_after_cost_display",
                "candidate_scorecard_scope",
                "candidate_scorecard_primary_blocker_code",
                "candidate_scorecard_blocker_summary",
                "candidate_scorecard_next_action",
                "primary_blocker_code",
                "primary_blocker_message",
                "next_action",
            )
        )
        for item in maturity.get("maturity_components", []):
            if isinstance(item, dict):
                values.extend(
                    str(item.get(key, ""))
                    for key in ("component_id", "status", "priority", "operator_message", "next_required_evidence")
                )
    convergence = shell.get("convergence_assessment_status", {})
    if isinstance(convergence, dict):
        values.extend(
            str(convergence.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "assessment_status",
                "convergence_claim",
                "objective_score_band",
                "model_drift_status",
                "dependency_summary",
                "primary_blocker_code",
                "primary_blocker_message",
                "next_action",
                "operator_warning",
            )
        )
        for item in convergence.get("dependency_statuses", []):
            if isinstance(item, dict):
                values.extend(str(item.get(key, "")) for key in ("validator_id", "status"))
    exploration = shell.get("exploration_policy_status", {})
    if isinstance(exploration, dict):
        values.extend(
            str(exploration.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "policy_status",
                "controller_state",
                "transition_decision",
                "recommendation_scope",
                "objective_basis",
                "dependency_summary",
                "candidate_budget_status",
                "primary_blocker_code",
                "primary_blocker_message",
                "next_action",
                "operator_warning",
            )
        )
        for item in exploration.get("dependency_statuses", []):
            if isinstance(item, dict):
                values.extend(str(item.get(key, "")) for key in ("validator_id", "status"))
    parameter_narrowing = shell.get("parameter_narrowing_status", {})
    if isinstance(parameter_narrowing, dict):
        values.extend(
            str(parameter_narrowing.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "narrowing_status",
                "recommendation_scope",
                "parameter_write_scope",
                "objective_basis",
                "dependency_summary",
                "sample_summary",
                "primary_blocker_code",
                "primary_blocker_message",
                "next_action",
                "operator_warning",
            )
        )
        for item in parameter_narrowing.get("dependency_statuses", []):
            if isinstance(item, dict):
                values.extend(str(item.get(key, "")) for key in ("validator_id", "status"))
    risk = shell.get("risk_exposure_snapshot", {})
    if isinstance(risk, dict):
        values.extend(
            str(risk.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "equity_display",
                "exposure_notional_display",
                "exposure_pct_display",
                "drawdown_pct_display",
                "paper_exposure_quality_status",
                "paper_exposure_quality_message",
                "paper_exposure_quality_next_required_evidence",
                "primary_blocker_code",
                "primary_blocker_message",
                "next_action",
            )
        )
    feedback = shell.get("execution_feedback_snapshot", {})
    if isinstance(feedback, dict):
        values.extend(
            str(feedback.get(key, ""))
            for key in (
                "title",
                "status",
                "severity",
                "cost_basis",
                "execution_quality_status",
                "risk_review_status",
                "exposure_review_status",
                "drawdown_review_status",
                "net_ev_deviation_display",
                "slippage_deviation_display",
                "fee_deviation_display",
                "impact_deviation_display",
                "optimizer_ranking_action",
                "primary_blocker_code",
                "primary_blocker_message",
                "next_action",
            )
        )
    decision = shell.get("decision_trace", {})
    if isinstance(decision, dict):
        values.extend(
            str(decision.get(key, ""))
            for key in ("title", "final_action", "no_trade_reason", "entry_status", "entry_reason", "exit_status", "exit_reason", "next_action")
        )
    recent_events = shell.get("recent_events", {})
    if isinstance(recent_events, dict):
        values.extend(str(recent_events.get(key, "")) for key in ("title", "status", "empty_message", "operation_status"))
        for item in recent_events.get("items", []):
            if isinstance(item, dict):
                values.extend(str(item.get(key, "")) for key in ("event_type", "severity", "label", "message", "source"))
    positions = shell.get("position_snapshot", {})
    if isinstance(positions, dict):
        values.extend(str(positions.get(key, "")) for key in ("title", "status", "empty_message"))
        for row in positions.get("rows", []):
            if isinstance(row, dict):
                values.extend(
                    str(row.get(key, ""))
                    for key in (
                        "symbol",
                        "side",
                        "quantity",
                        "avg_price",
                        "mark_price",
                        "market_value",
                        "cost_basis",
                        "unrealized_pnl",
                    )
                )
    portfolio = shell.get("portfolio_snapshot", {})
    if isinstance(portfolio, dict):
        values.extend(
            str(portfolio.get(key, ""))
            for key in ("title", "status", "source", "blocking_reason", "next_action")
        )
        for card_id in PORTFOLIO_CARD_IDS:
            card = portfolio.get(card_id, {})
            if isinstance(card, dict):
                values.extend(str(card.get(key, "")) for key in ("label", "value_display", "detail"))
    for panel in shell.get("panels", []):
        if isinstance(panel, dict):
            values.extend(str(panel.get(key, "")) for key in ("title", "status", "source", "message"))
    return values


def validate_read_only_dashboard_shell(
    shell: dict[str, Any],
    allowed_blockers: set[str] | None = None,
) -> DashboardValidationResult:
    if shell.get("schema_id") != READ_ONLY_DASHBOARD_SCHEMA_ID:
        return DashboardValidationResult("FAIL", "dashboard schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if shell.get("project_id") != "TRADER_1":
        return DashboardValidationResult("FAIL", "dashboard project mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if shell.get("truth_role") != "dashboard_serving_truth":
        return DashboardValidationResult("BLOCKED", "dashboard cannot claim higher truth role", "LIVE_FINAL_GUARD_FAILED")
    if shell.get("display_only") is not True or shell.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "dashboard must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        shell.get("live_order_ready")
        or shell.get("live_order_allowed")
        or shell.get("can_live_trade")
        or shell.get("can_submit_order")
        or shell.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "dashboard attempted to create live or order permission", "LIVE_FINAL_GUARD_FAILED")
    if shell.get("final_action") in ORDER_AFFECTING_FINAL_ACTIONS:
        return DashboardValidationResult("BLOCKED", "dashboard cannot emit order-affecting final_action", "LIVE_FINAL_GUARD_FAILED")
    if shell.get("final_action") not in SAFE_FINAL_ACTIONS:
        return DashboardValidationResult("FAIL", "dashboard final_action is not fail-closed", "LIVE_FINAL_GUARD_FAILED")

    source_artifacts = shell.get("source_artifacts")
    if not isinstance(source_artifacts, list) or not source_artifacts:
        return DashboardValidationResult("FAIL", "dashboard source_artifacts missing", "SCHEMA_IDENTITY_MISMATCH")
    source_filenames = set()
    missing_source = False
    for source in source_artifacts:
        if not isinstance(source, dict):
            return DashboardValidationResult("FAIL", "dashboard source artifact must be object", "SCHEMA_IDENTITY_MISMATCH")
        filename = source.get("filename")
        source_filenames.add(filename)
        if filename not in DISPLAY_SOURCE_FILENAMES:
            return DashboardValidationResult("BLOCKED", f"dashboard source is not allowed for MVP-1: {filename}", "LIVE_FINAL_GUARD_FAILED")
        role = source.get("truth_role")
        if role in FORBIDDEN_SOURCE_ROLES or role != "dashboard_serving_truth":
            return DashboardValidationResult("BLOCKED", "dashboard attempted to use non-dashboard truth as source", "LIVE_FINAL_GUARD_FAILED")
        if source.get("loaded") is not True:
            missing_source = True
    if not REQUIRED_DISPLAY_SOURCE_FILENAMES.issubset(source_filenames):
        return DashboardValidationResult("BLOCKED", "dashboard must project summary, heartbeat, and startup probe", "HARD_TRUTH_MISSING")
    if not source_filenames.issubset(DISPLAY_SOURCE_FILENAMES):
        return DashboardValidationResult("BLOCKED", "dashboard projected an unsupported source artifact", "LIVE_FINAL_GUARD_FAILED")
    if missing_source and shell.get("final_action") not in {"NO_TRADE", "SAFE_MODE", "BLOCKED"}:
        return DashboardValidationResult("BLOCKED", "missing dashboard source did not fail closed", "HARD_TRUTH_MISSING")
    if missing_source and shell.get("blocking_reason") is None:
        return DashboardValidationResult("BLOCKED", "missing dashboard source must expose a blocker", "HARD_TRUTH_MISSING")

    refresh_policy = shell.get("dashboard_refresh_policy")
    if not isinstance(refresh_policy, dict):
        return DashboardValidationResult("FAIL", "dashboard refresh policy missing", "SCHEMA_IDENTITY_MISMATCH")
    if refresh_policy.get("truth_role") != "dashboard_serving_truth" or refresh_policy.get("source") not in DISPLAY_SOURCE_FILENAMES:
        return DashboardValidationResult("BLOCKED", "dashboard refresh policy cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if refresh_policy.get("display_only") is not True or refresh_policy.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "dashboard refresh policy must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        refresh_policy.get("live_order_ready")
        or refresh_policy.get("live_order_allowed")
        or refresh_policy.get("can_live_trade")
        or refresh_policy.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "dashboard refresh policy attempted to create live or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if refresh_policy.get("status") != "AUTO_REFRESH_ENABLED" or refresh_policy.get("refresh_mode") != "LOCAL_FILE_RELOAD":
        return DashboardValidationResult("FAIL", "dashboard refresh policy must use local file reload", "SCHEMA_IDENTITY_MISMATCH")
    refresh_seconds = refresh_policy.get("auto_refresh_interval_seconds")
    stale_after = refresh_policy.get("stale_after_seconds")
    if not isinstance(refresh_seconds, int) or refresh_seconds < 5 or refresh_seconds > SOURCE_FRESHNESS_MAX_AGE_SECONDS:
        return DashboardValidationResult("FAIL", "dashboard refresh interval is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if stale_after != SOURCE_FRESHNESS_MAX_AGE_SECONDS or refresh_policy.get("client_stale_guard_enabled") is not True:
        return DashboardValidationResult("BLOCKED", "dashboard must expose a client-side stale guard", "LATENCY_TTL_EXPIRED")
    if refresh_policy.get("generated_at_utc") != shell.get("generated_at_utc"):
        return DashboardValidationResult("FAIL", "dashboard refresh generated_at must match shell generated_at", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(refresh_policy.get("next_action"), str) or not refresh_policy.get("next_action", "").strip():
        return DashboardValidationResult("FAIL", "dashboard refresh policy must expose next action", "SCHEMA_IDENTITY_MISMATCH")

    operation = shell.get("operation_status")
    if not isinstance(operation, dict):
        return DashboardValidationResult("FAIL", "dashboard operation_status missing", "SCHEMA_IDENTITY_MISMATCH")
    if operation.get("severity") not in OPERATION_STATUS_LEVELS:
        return DashboardValidationResult("FAIL", "dashboard operation severity is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if operation.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "dashboard operation color token is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if operation.get("live_orders_blocked") is not True:
        return DashboardValidationResult("BLOCKED", "operation status must keep live orders blocked", "LIVE_FINAL_GUARD_FAILED")
    if not isinstance(operation.get("recovery_hint"), str) or not operation.get("recovery_hint", "").strip():
        return DashboardValidationResult("FAIL", "operation status must expose recovery guidance", "SCHEMA_IDENTITY_MISMATCH")
    if operation.get("launcher_execution_mode") != "SAFE_BOOT_OR_EXPLICIT_MONITOR":
        return DashboardValidationResult("FAIL", "operation status must distinguish safe boot from runtime execution", "SCHEMA_IDENTITY_MISMATCH")
    if operation.get("runtime_presence") not in {"DASHBOARD_HEARTBEAT_ONLY", "HEARTBEAT_STALE_OR_SOURCE_ATTENTION_REQUIRED"}:
        return DashboardValidationResult("FAIL", "operation status runtime presence is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(operation.get("operator_meaning"), str) or "continuous PAPER engine" not in operation.get("operator_meaning", ""):
        return DashboardValidationResult("FAIL", "operation status must prevent continuous-runtime misunderstanding", "SCHEMA_IDENTITY_MISMATCH")
    if operation.get("severity") == "NORMAL" and operation.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal operation must use green or blue status color", "SCHEMA_IDENTITY_MISMATCH")
    if operation.get("severity") == "WARNING" and operation.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning operation must use yellow status color", "SCHEMA_IDENTITY_MISMATCH")
    if operation.get("severity") == "ERROR" and operation.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error operation must use red status color", "SCHEMA_IDENTITY_MISMATCH")
    portfolio = shell.get("portfolio_snapshot")
    if not isinstance(portfolio, dict):
        return DashboardValidationResult("FAIL", "dashboard portfolio_snapshot missing", "SCHEMA_IDENTITY_MISMATCH")
    portfolio_status = portfolio.get("status")
    if operation.get("portfolio_status") != portfolio_status:
        return DashboardValidationResult(
            "BLOCKED",
            "operation portfolio status must mirror portfolio snapshot status",
            "LATENCY_TTL_EXPIRED" if portfolio_status == "STALE" else "HARD_TRUTH_MISSING",
        )
    if operation.get("portfolio_blocking_reason") != portfolio.get("blocking_reason"):
        return DashboardValidationResult(
            "BLOCKED",
            "operation portfolio blocker must mirror portfolio snapshot blocker",
            "LATENCY_TTL_EXPIRED" if portfolio_status == "STALE" else "HARD_TRUTH_MISSING",
        )
    if operation.get("portfolio_next_action") != portfolio.get("next_action"):
        return DashboardValidationResult("FAIL", "operation portfolio next action must mirror portfolio snapshot next action", "SCHEMA_IDENTITY_MISMATCH")
    heartbeat_source = next((source for source in source_artifacts if source.get("artifact_id") == "HEARTBEAT"), {})
    if operation.get("severity") == "NORMAL":
        if heartbeat_source.get("freshness_status") != "PASS" or operation.get("heartbeat_status") != "PASS":
            return DashboardValidationResult("BLOCKED", "normal operation requires fresh PASS heartbeat", "LATENCY_TTL_EXPIRED")
        if portfolio_status != "VERIFIED":
            return DashboardValidationResult(
                "BLOCKED",
                "normal operation requires verified portfolio display truth",
                "HARD_TRUTH_MISSING" if portfolio_status != "STALE" else "LATENCY_TTL_EXPIRED",
            )
    if operation.get("color_token") == "red" and operation.get("severity") != "ERROR":
        return DashboardValidationResult("FAIL", "red dashboard color is reserved for error severity", "SCHEMA_IDENTITY_MISMATCH")

    reconciliation = shell.get("reconciliation_recovery_summary")
    if not isinstance(reconciliation, dict):
        return DashboardValidationResult("FAIL", "dashboard reconciliation recovery summary missing", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("truth_role") != "dashboard_serving_truth" or reconciliation.get("source") not in RECONCILIATION_RECOVERY_SOURCES:
        return DashboardValidationResult("BLOCKED", "reconciliation recovery summary cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if reconciliation.get("display_only") is not True or reconciliation.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "reconciliation recovery summary must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        reconciliation.get("live_order_ready")
        or reconciliation.get("live_order_allowed")
        or reconciliation.get("can_live_trade")
        or reconciliation.get("can_submit_order")
        or reconciliation.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "reconciliation recovery summary attempted to create live or order permission", "LIVE_FINAL_GUARD_FAILED")
    if reconciliation.get("status") not in RECONCILIATION_RECOVERY_STATUSES:
        return DashboardValidationResult("FAIL", "reconciliation recovery status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("reconciliation_status") not in RECONCILIATION_RECOVERY_REPORT_STATUSES:
        return DashboardValidationResult("FAIL", "reconciliation report status display is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("restart_recovery_status") not in RECONCILIATION_RECOVERY_REPORT_STATUSES:
        return DashboardValidationResult("FAIL", "restart recovery status display is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("reconciliation_validation_status") not in RECONCILIATION_RECOVERY_VALIDATION_STATUSES:
        return DashboardValidationResult("FAIL", "reconciliation validation status display is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("restart_recovery_validation_status") not in RECONCILIATION_RECOVERY_VALIDATION_STATUSES:
        return DashboardValidationResult("FAIL", "restart recovery validation status display is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("ledger_state") not in RECONCILIATION_RECOVERY_LEDGER_STATES:
        return DashboardValidationResult("FAIL", "ledger state display is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("single_writer_state") not in RECONCILIATION_RECOVERY_WRITER_STATES:
        return DashboardValidationResult("FAIL", "single-writer recovery display is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("idempotency_state") not in RECONCILIATION_RECOVERY_WRITER_STATES:
        return DashboardValidationResult("FAIL", "idempotency recovery display is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("severity") not in OPERATION_STATUS_LEVELS or reconciliation.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "reconciliation recovery severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("severity") == "NORMAL" and reconciliation.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal reconciliation recovery must use green or blue", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("severity") == "WARNING" and reconciliation.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning reconciliation recovery must use yellow", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("severity") == "ERROR" and reconciliation.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error reconciliation recovery must use red", "SCHEMA_IDENTITY_MISMATCH")
    for text_field in ("one_line_blocker", "message", "next_operator_action", "primary_blocker_code"):
        if not isinstance(reconciliation.get(text_field), str) or not reconciliation.get(text_field, "").strip():
            return DashboardValidationResult("FAIL", f"reconciliation recovery summary missing {text_field}", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(reconciliation.get("mismatch_count"), int) or reconciliation.get("mismatch_count") < 0:
        return DashboardValidationResult("FAIL", "reconciliation mismatch count is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("status") == "PASS":
        if (
            reconciliation.get("reconciliation_status") != "PASS"
            or reconciliation.get("restart_recovery_status") != "PASS"
            or reconciliation.get("primary_blocker_code") != "LIVE_READY_MISSING"
            or reconciliation.get("mismatch_count") != 0
        ):
            return DashboardValidationResult("BLOCKED", "PASS reconciliation display requires clean PAPER checks and live still blocked", "LIVE_FINAL_GUARD_FAILED")
    if reconciliation.get("status") in {"BLOCKED", "INVALID"} and reconciliation.get("severity") != "ERROR":
        return DashboardValidationResult("FAIL", "blocked or invalid reconciliation recovery must render as error", "SCHEMA_IDENTITY_MISMATCH")

    stability = shell.get("stability_trends")
    if not isinstance(stability, dict):
        return DashboardValidationResult("FAIL", "dashboard stability_trends missing", "SCHEMA_IDENTITY_MISMATCH")
    if stability.get("truth_role") != "dashboard_serving_truth" or stability.get("source") not in DISPLAY_SOURCE_FILENAMES:
        return DashboardValidationResult("BLOCKED", "stability trends cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if stability.get("display_only") is not True or stability.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "stability trends must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        stability.get("live_order_ready")
        or stability.get("live_order_allowed")
        or stability.get("can_live_trade")
        or stability.get("scale_up_allowed")
    ):
        return DashboardValidationResult(
            "BLOCKED",
            "stability trends attempted to create live, trade, or scale-up permission",
            "LIVE_FINAL_GUARD_FAILED",
        )
    if stability.get("status") not in STABILITY_STATUSES:
        return DashboardValidationResult("FAIL", "stability status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if stability.get("severity") not in OPERATION_STATUS_LEVELS:
        return DashboardValidationResult("FAIL", "stability severity is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if stability.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "stability color token is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if stability.get("severity") == "NORMAL" and stability.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal stability must use green or blue status color", "SCHEMA_IDENTITY_MISMATCH")
    if stability.get("severity") == "WARNING" and stability.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning stability must use yellow status color", "SCHEMA_IDENTITY_MISMATCH")
    if stability.get("severity") == "ERROR" and stability.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error stability must use red status color", "SCHEMA_IDENTITY_MISMATCH")
    if stability.get("history_window") not in {"CURRENT_SNAPSHOT_ONLY", "VALIDATED_HISTORY"}:
        return DashboardValidationResult("BLOCKED", "dashboard stability history window is invalid", "HARD_TRUTH_MISSING")
    history_sample_count = stability.get("history_sample_count")
    observed_span_seconds = stability.get("observed_span_seconds")
    min_validated_span_seconds = stability.get("min_validated_span_seconds")
    span_validation_status = stability.get("span_validation_status")
    degraded_sample_count = stability.get("degraded_sample_count")
    stale_sample_count = stability.get("stale_sample_count")
    if not all(
        isinstance(value, int) and value >= 0
        for value in (history_sample_count, observed_span_seconds, min_validated_span_seconds, degraded_sample_count, stale_sample_count)
    ):
        return DashboardValidationResult("FAIL", "stability history counts are invalid", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(span_validation_status, str) or span_validation_status not in {"INSUFFICIENT_SPAN", "SPAN_VALIDATED"}:
        return DashboardValidationResult("FAIL", "stability span validation status is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if stability.get("history_window") == "VALIDATED_HISTORY":
        if history_sample_count < 2 or span_validation_status != "SPAN_VALIDATED" or observed_span_seconds < min_validated_span_seconds:
            return DashboardValidationResult("BLOCKED", "validated stability history requires minimum samples and observed span", "HARD_TRUTH_MISSING")
    if stability.get("history_window") == "CURRENT_SNAPSHOT_ONLY" and span_validation_status == "SPAN_VALIDATED" and history_sample_count >= 2:
        return DashboardValidationResult("FAIL", "dashboard hid available validated stability history", "SCHEMA_IDENTITY_MISMATCH")
    metrics = stability.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        return DashboardValidationResult("FAIL", "stability metrics must be a non-empty list", "SCHEMA_IDENTITY_MISMATCH")
    metric_ids = set()
    has_non_pass_metric = False
    has_fail_metric = False
    for metric in metrics:
        if not isinstance(metric, dict):
            return DashboardValidationResult("FAIL", "stability metric must be an object", "SCHEMA_IDENTITY_MISMATCH")
        metric_id = metric.get("metric_id")
        metric_ids.add(metric_id)
        if metric_id not in STABILITY_METRIC_IDS or metric.get("status") not in STABILITY_METRIC_STATUSES:
            return DashboardValidationResult("FAIL", "stability metric enum mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if metric.get("source") not in DISPLAY_SOURCE_FILENAMES:
            return DashboardValidationResult("BLOCKED", "stability metric source must be dashboard display truth", "LIVE_FINAL_GUARD_FAILED")
        if metric.get("trend_direction") != "CURRENT_ONLY":
            return DashboardValidationResult("BLOCKED", "stability metric cannot claim historical trend without validated history", "HARD_TRUTH_MISSING")
        if metric.get("status") != "PASS":
            has_non_pass_metric = True
        if metric.get("status") == "FAIL":
            has_fail_metric = True
    if metric_ids != STABILITY_METRIC_IDS:
        return DashboardValidationResult("FAIL", "stability metric set mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if stability.get("status") == "STABLE" and (has_non_pass_metric or operation.get("severity") != "NORMAL"):
        return DashboardValidationResult("BLOCKED", "stable dashboard status requires PASS metrics and normal operation", "LATENCY_TTL_EXPIRED")
    if has_fail_metric and stability.get("severity") != "ERROR":
        return DashboardValidationResult("FAIL", "failed stability metric must render as error severity", "SCHEMA_IDENTITY_MISMATCH")

    long_run = shell.get("long_run_operator_summary")
    if not isinstance(long_run, dict):
        return DashboardValidationResult("FAIL", "dashboard long_run_operator_summary missing", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("truth_role") != "dashboard_serving_truth" or long_run.get("source") not in LONG_RUN_SUMMARY_SOURCES:
        return DashboardValidationResult("BLOCKED", "long-run summary cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if long_run.get("display_only") is not True or long_run.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "long-run summary must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        long_run.get("live_order_ready")
        or long_run.get("live_order_allowed")
        or long_run.get("can_live_trade")
        or long_run.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "long-run summary attempted to create live or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if long_run.get("status") not in LONG_RUN_SUMMARY_STATUSES:
        return DashboardValidationResult("FAIL", "long-run summary status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("severity") not in OPERATION_STATUS_LEVELS or long_run.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "long-run summary severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("severity") == "NORMAL" and long_run.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal long-run status must use green or blue", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("severity") == "WARNING" and long_run.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning long-run status must use yellow", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("severity") == "ERROR" and long_run.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error long-run status must use red", "SCHEMA_IDENTITY_MISMATCH")
    long_run_counts = (
        long_run.get("history_sample_count"),
        long_run.get("observed_span_seconds"),
        long_run.get("min_validated_span_seconds"),
        long_run.get("stable_sample_count"),
        long_run.get("degraded_sample_count"),
        long_run.get("stale_sample_count"),
    )
    if not all(isinstance(value, int) and value >= 0 for value in long_run_counts):
        return DashboardValidationResult("FAIL", "long-run history counts are invalid", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("history_sample_count") != stability.get("history_sample_count"):
        return DashboardValidationResult("FAIL", "long-run sample count must match stability history", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("observed_span_seconds") != stability.get("observed_span_seconds"):
        return DashboardValidationResult("FAIL", "long-run observed span must match stability history", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("min_validated_span_seconds") != stability.get("min_validated_span_seconds"):
        return DashboardValidationResult("FAIL", "long-run minimum span must match stability history", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("span_validation_status") != stability.get("span_validation_status"):
        return DashboardValidationResult("FAIL", "long-run span validation status must match stability history", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("degraded_sample_count") != stability.get("degraded_sample_count") or long_run.get("stale_sample_count") != stability.get("stale_sample_count"):
        return DashboardValidationResult("FAIL", "long-run degraded and stale counts must match stability history", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("stable_sample_count") + long_run.get("degraded_sample_count") != long_run.get("history_sample_count"):
        return DashboardValidationResult("FAIL", "long-run stable and degraded sample counts must cover the history window", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("stale_sample_count") > long_run.get("history_sample_count"):
        return DashboardValidationResult("FAIL", "long-run stale sample count cannot exceed history sample count", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("span_validation_status") not in {"INSUFFICIENT_SPAN", "SPAN_VALIDATED"}:
        return DashboardValidationResult("FAIL", "long-run span validation status is invalid", "SCHEMA_IDENTITY_MISMATCH")
    for field in (
        "latency_trend_status",
        "error_frequency_status",
        "retry_trend_status",
        "dashboard_refresh_delay_status",
        "resource_pressure_status",
    ):
        if long_run.get(field) not in STABILITY_METRIC_STATUSES:
            return DashboardValidationResult("FAIL", f"long-run metric status is unknown: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("status") == "DISPLAY_HISTORY_STABLE":
        if long_run.get("history_sample_count", 0) < 2 or long_run.get("degraded_sample_count") or long_run.get("stale_sample_count"):
            return DashboardValidationResult("BLOCKED", "display-history stable long-run status requires clean display history with at least two samples", "HARD_TRUTH_MISSING")
        if (
            long_run.get("history_window") != "VALIDATED_HISTORY"
            or long_run.get("span_validation_status") != "SPAN_VALIDATED"
            or long_run.get("observed_span_seconds", 0) < long_run.get("min_validated_span_seconds", 0)
        ):
            return DashboardValidationResult("BLOCKED", "display-history stable long-run status requires minimum-span display stability history", "HARD_TRUTH_MISSING")
        if long_run.get("source") != "stability_history.json" or long_run.get("severity") != "NORMAL":
            return DashboardValidationResult("FAIL", "display-history stable long-run status must cite stability history and normal severity", "SCHEMA_IDENTITY_MISMATCH")
        if long_run.get("primary_blocker_code") != "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING":
            return DashboardValidationResult("BLOCKED", "display-history stable status must keep actual persistent runtime evidence missing as the blocker", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        display_summary = f"{long_run.get('summary', '')} {long_run.get('next_action', '')}".lower()
        if "display" not in display_summary or "not actual" not in display_summary or "live-review evidence" not in display_summary:
            return DashboardValidationResult("BLOCKED", "display-history stable status must clearly say it is not actual long-run or live-review evidence", "HARD_TRUTH_MISSING")
    if long_run.get("status") == "VALIDATED_STABLE":
        if not (
            int(long_run.get("observed_span_seconds", 0) or 0) >= ACTUAL_LONG_RUN_MIN_VALIDATED_SPAN_SECONDS
            and int(long_run.get("history_sample_count", 0) or 0) >= ACTUAL_LONG_RUN_MIN_ACTUAL_CYCLE_COUNT
            and int(long_run.get("stable_sample_count", 0) or 0) >= ACTUAL_LONG_RUN_MIN_ACTUAL_CYCLE_COUNT
            and int(long_run.get("degraded_sample_count", 0) or 0) == 0
            and int(long_run.get("stale_sample_count", 0) or 0) == 0
        ):
            return DashboardValidationResult("BLOCKED", "validated stable long-run status requires actual duration and stable-sample floors", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if long_run.get("status") == "RUNNING_NOW":
        if long_run.get("history_window") == "VALIDATED_HISTORY":
            return DashboardValidationResult("FAIL", "long-run summary hid available validated stability history", "SCHEMA_IDENTITY_MISMATCH")
        if operation.get("severity") != "NORMAL" or has_non_pass_metric:
            return DashboardValidationResult("BLOCKED", "running-now long-run status requires current PASS checks", "LATENCY_TTL_EXPIRED")
    if long_run.get("status") == "STALE" and long_run.get("severity") != "WARNING":
        return DashboardValidationResult("FAIL", "stale long-run status must render as warning", "SCHEMA_IDENTITY_MISMATCH")
    if long_run.get("status") == "ERROR" and long_run.get("severity") != "ERROR":
        return DashboardValidationResult("FAIL", "error long-run status must render as error", "SCHEMA_IDENTITY_MISMATCH")

    market_data = shell.get("market_data_continuity_status")
    if not isinstance(market_data, dict):
        return DashboardValidationResult("FAIL", "dashboard market_data_continuity_status missing", "SCHEMA_IDENTITY_MISMATCH")
    if (
        market_data.get("truth_role") != "dashboard_serving_truth"
        or market_data.get("source") not in MARKET_DATA_CONTINUITY_SOURCES
        or market_data.get("evidence_role") not in MARKET_DATA_CONTINUITY_EVIDENCE_ROLES
    ):
        return DashboardValidationResult("BLOCKED", "market-data continuity display cannot claim execution or live-readiness truth", "LIVE_FINAL_GUARD_FAILED")
    if market_data.get("display_only") is not True or market_data.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "market-data continuity status must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        market_data.get("live_order_ready")
        or market_data.get("live_order_allowed")
        or market_data.get("can_live_trade")
        or market_data.get("scale_up_allowed")
        or market_data.get("long_run_evidence_eligible")
        or market_data.get("promotion_eligible")
    ):
        return DashboardValidationResult("BLOCKED", "market-data continuity attempted live, scale, long-run, or promotion permission", "LIVE_FINAL_GUARD_FAILED")
    if market_data.get("status") not in MARKET_DATA_CONTINUITY_STATUSES:
        return DashboardValidationResult("FAIL", "market-data continuity status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if market_data.get("severity") not in OPERATION_STATUS_LEVELS or market_data.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "market-data continuity severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if market_data.get("severity") == "NORMAL" and market_data.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal market-data continuity must use green or blue", "SCHEMA_IDENTITY_MISMATCH")
    if market_data.get("severity") == "WARNING" and market_data.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning market-data continuity must use yellow", "SCHEMA_IDENTITY_MISMATCH")
    if market_data.get("severity") == "ERROR" and market_data.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error market-data continuity must use red", "SCHEMA_IDENTITY_MISMATCH")
    continuity_source_loaded = market_data.get("source") == "rest_continuity_history.json"
    continuity_source_listed = "rest_continuity_history.json" in source_filenames
    if continuity_source_loaded and not continuity_source_listed:
        return DashboardValidationResult("BLOCKED", "market-data continuity status must be backed by a listed source artifact", "HARD_TRUTH_MISSING")
    if not continuity_source_loaded and continuity_source_listed:
        return DashboardValidationResult("BLOCKED", "market-data continuity source artifact is listed while status is not loaded", "SCHEMA_IDENTITY_MISMATCH")
    for count_field in (
        "total_attempt_count",
        "pass_attempt_count",
        "blocked_attempt_count",
        "duplicate_latest_event_block_count",
        "non_advancing_block_count",
        "data_unavailable_block_count",
    ):
        if not isinstance(market_data.get(count_field), int) or market_data.get(count_field) < 0:
            return DashboardValidationResult("FAIL", f"market-data continuity count is invalid: {count_field}", "SCHEMA_IDENTITY_MISMATCH")
    for text_field in ("title", "symbol", "history_window_label", "latest_attempt_status", "primary_blocker_code", "one_line_summary", "next_operator_action"):
        if not isinstance(market_data.get(text_field), str) or not market_data.get(text_field, "").strip():
            return DashboardValidationResult("FAIL", f"market-data continuity missing {text_field}", "SCHEMA_IDENTITY_MISMATCH")
    if market_data.get("status") == "PASS":
        if (
            market_data.get("source") != "rest_continuity_history.json"
            or market_data.get("pass_attempt_count", 0) < 2
            or market_data.get("latest_attempt_status") != "PASS"
            or market_data.get("primary_blocker_code") != "LIVE_READY_MISSING"
        ):
            return DashboardValidationResult("BLOCKED", "PASS market-data continuity requires repeated PAPER PASS attempts and live still blocked", "LIVE_FINAL_GUARD_FAILED")
    if market_data.get("status") == "NOT_LOADED" and market_data.get("source") != "NOT_LOADED":
        return DashboardValidationResult("FAIL", "not-loaded market-data continuity must not cite a report source", "SCHEMA_IDENTITY_MISMATCH")
    if market_data.get("status") in {"BLOCKED", "STALE"} and market_data.get("severity") != "WARNING":
        return DashboardValidationResult("FAIL", "blocked or stale market-data continuity must render as warning", "SCHEMA_IDENTITY_MISMATCH")
    if market_data.get("status") == "INVALID" and market_data.get("severity") != "ERROR":
        return DashboardValidationResult("FAIL", "invalid market-data continuity must render as error", "SCHEMA_IDENTITY_MISMATCH")

    shadow_harness = shell.get("shadow_runtime_harness_status")
    if not isinstance(shadow_harness, dict):
        return DashboardValidationResult("FAIL", "dashboard shadow_runtime_harness_status missing", "SCHEMA_IDENTITY_MISMATCH")
    if (
        shadow_harness.get("truth_role") != "dashboard_serving_truth"
        or shadow_harness.get("source") not in SHADOW_RUNTIME_HARNESS_SOURCES
    ):
        return DashboardValidationResult("BLOCKED", "shadow runtime harness cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if shadow_harness.get("display_only") is not True or shadow_harness.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "shadow runtime harness must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        shadow_harness.get("live_order_ready")
        or shadow_harness.get("live_order_allowed")
        or shadow_harness.get("can_live_trade")
        or shadow_harness.get("scale_up_allowed")
        or shadow_harness.get("long_run_evidence_eligible")
    ):
        return DashboardValidationResult("BLOCKED", "shadow runtime harness attempted to create live, scale, or long-run permission", "LIVE_FINAL_GUARD_FAILED")
    if shadow_harness.get("status") not in SHADOW_RUNTIME_HARNESS_STATUSES:
        return DashboardValidationResult("FAIL", "shadow runtime harness status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_harness.get("runtime_evidence_status") not in SHADOW_RUNTIME_HARNESS_EVIDENCE_STATUSES:
        return DashboardValidationResult("FAIL", "shadow runtime harness evidence status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    harness_source_loaded = shadow_harness.get("source") == "actual_runtime_harness_report.json"
    harness_source_listed = "actual_runtime_harness_report.json" in source_filenames
    if harness_source_loaded and not harness_source_listed:
        return DashboardValidationResult("BLOCKED", "shadow runtime harness status must be backed by a listed source artifact", "HARD_TRUTH_MISSING")
    if not harness_source_loaded and harness_source_listed:
        return DashboardValidationResult("BLOCKED", "shadow runtime harness source artifact is listed while harness status is not loaded", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_harness.get("severity") not in OPERATION_STATUS_LEVELS or shadow_harness.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "shadow runtime harness severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_harness.get("severity") == "NORMAL" and shadow_harness.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal shadow harness status must use green or blue", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_harness.get("severity") == "WARNING" and shadow_harness.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning shadow harness status must use yellow", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_harness.get("severity") == "ERROR" and shadow_harness.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error shadow harness status must use red", "SCHEMA_IDENTITY_MISMATCH")
    for count_field in (
        "requested_cycle_count",
        "completed_cycle_count",
        "observation_count",
        "heartbeat_count",
        "measured_runtime_seconds",
        "minimum_runtime_window_seconds",
    ):
        if not isinstance(shadow_harness.get(count_field), int) or shadow_harness.get(count_field) < 0:
            return DashboardValidationResult("FAIL", f"shadow runtime harness count is invalid: {count_field}", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_harness.get("status") == "SHORT_WINDOW_EXECUTED":
        if shadow_harness.get("actual_non_live_runtime_harness_executed") is not True:
            return DashboardValidationResult("BLOCKED", "short-window harness display requires an executed non-live harness", "HARD_TRUTH_MISSING")
        if shadow_harness.get("runtime_evidence_status") != "BLOCKED_LONG_RUN_EVIDENCE_MISSING":
            return DashboardValidationResult("BLOCKED", "short-window harness must keep long-run evidence blocked", "LIVE_FINAL_GUARD_FAILED")
        if shadow_harness.get("optimizer_input_role") != "BLOCKER_ONLY_NOT_RANKING_INPUT":
            return DashboardValidationResult("BLOCKED", "short-window harness cannot become optimizer ranking input", "LIVE_FINAL_GUARD_FAILED")
        if shadow_harness.get("completed_cycle_count") > shadow_harness.get("requested_cycle_count"):
            return DashboardValidationResult("FAIL", "shadow runtime harness cycle counts are inconsistent", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_harness.get("status") == "NOT_LOADED" and shadow_harness.get("source") != "NOT_LOADED":
        return DashboardValidationResult("FAIL", "not-loaded shadow harness must not cite a report source", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_harness.get("status") == "BLOCKED" and shadow_harness.get("severity") != "ERROR":
        return DashboardValidationResult("FAIL", "blocked shadow harness status must render as error", "SCHEMA_IDENTITY_MISMATCH")

    shadow_persistent = shell.get("shadow_persistent_runtime_status")
    if not isinstance(shadow_persistent, dict):
        return DashboardValidationResult("FAIL", "dashboard shadow_persistent_runtime_status missing", "SCHEMA_IDENTITY_MISMATCH")
    if (
        shadow_persistent.get("truth_role") != "dashboard_serving_truth"
        or shadow_persistent.get("source") not in SHADOW_PERSISTENT_RUNTIME_SOURCES
    ):
        return DashboardValidationResult("BLOCKED", "persistent runtime display cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if shadow_persistent.get("display_only") is not True or shadow_persistent.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "persistent runtime display must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        shadow_persistent.get("live_order_ready")
        or shadow_persistent.get("live_order_allowed")
        or shadow_persistent.get("can_live_trade")
        or shadow_persistent.get("scale_up_allowed")
        or shadow_persistent.get("long_run_evidence_eligible")
        or shadow_persistent.get("actual_persistent_runtime_executed")
    ):
        return DashboardValidationResult("BLOCKED", "persistent runtime attempted to create live, scale, or long-run permission", "LIVE_FINAL_GUARD_FAILED")
    if shadow_persistent.get("status") not in SHADOW_PERSISTENT_RUNTIME_STATUSES:
        return DashboardValidationResult("FAIL", "persistent runtime status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_persistent.get("runtime_duration_evidence_source") not in SHADOW_PERSISTENT_RUNTIME_DURATION_SOURCES:
        return DashboardValidationResult("FAIL", "persistent runtime duration source is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_persistent.get("duration_evidence_role") not in SHADOW_PERSISTENT_RUNTIME_DURATION_ROLES:
        return DashboardValidationResult("BLOCKED", "persistent runtime duration role must remain not long-run evidence", "LIVE_FINAL_GUARD_FAILED")
    persistent_source_loaded = shadow_persistent.get("source") == "shadow_observation_persistent_runtime_report.json"
    persistent_source_listed = "shadow_observation_persistent_runtime_report.json" in source_filenames
    if persistent_source_loaded and not persistent_source_listed:
        return DashboardValidationResult("BLOCKED", "persistent runtime status must be backed by a listed source artifact", "HARD_TRUTH_MISSING")
    if not persistent_source_loaded and persistent_source_listed:
        return DashboardValidationResult("BLOCKED", "persistent runtime source artifact is listed while status is not loaded", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_persistent.get("severity") not in OPERATION_STATUS_LEVELS or shadow_persistent.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "persistent runtime severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_persistent.get("severity") == "NORMAL" and shadow_persistent.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal persistent runtime must use green or blue", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_persistent.get("severity") == "WARNING" and shadow_persistent.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning persistent runtime must use yellow", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_persistent.get("severity") == "ERROR" and shadow_persistent.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error persistent runtime must use red", "SCHEMA_IDENTITY_MISMATCH")
    for count_field in (
        "requested_cycle_count",
        "completed_cycle_count",
        "heartbeat_count",
        "heartbeat_interval_seconds",
        "estimated_runtime_seconds",
        "observed_runtime_seconds",
    ):
        if not isinstance(shadow_persistent.get(count_field), int) or shadow_persistent.get(count_field) < 0:
            return DashboardValidationResult("FAIL", f"persistent runtime count is invalid: {count_field}", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_persistent.get("status") == "STUB_ONLY":
        if shadow_persistent.get("runtime_duration_evidence_source") != "STUB_ESTIMATE_ONLY":
            return DashboardValidationResult("BLOCKED", "persistent runtime stub must expose stub-only duration source", "HARD_TRUTH_MISSING")
        if shadow_persistent.get("observed_runtime_seconds") != 0:
            return DashboardValidationResult("BLOCKED", "persistent runtime stub cannot claim observed runtime seconds", "LIVE_FINAL_GUARD_FAILED")
        if shadow_persistent.get("estimated_runtime_seconds") != (
            shadow_persistent.get("completed_cycle_count") * shadow_persistent.get("heartbeat_interval_seconds")
        ):
            return DashboardValidationResult("FAIL", "persistent runtime estimated duration mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if shadow_persistent.get("optimizer_input_role") != "SHADOW_PERSISTENT_RUNTIME_STUB_ONLY":
            return DashboardValidationResult("BLOCKED", "persistent runtime stub cannot become optimizer ranking input", "LIVE_FINAL_GUARD_FAILED")
        if shadow_persistent.get("primary_blocker_code") != "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING":
            return DashboardValidationResult("BLOCKED", "persistent runtime stub must expose actual runtime blocker", "HARD_TRUTH_MISSING")
    if shadow_persistent.get("status") == "NOT_LOADED" and shadow_persistent.get("source") != "NOT_LOADED":
        return DashboardValidationResult("FAIL", "not-loaded persistent runtime must not cite a report source", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_persistent.get("status") == "BLOCKED" and shadow_persistent.get("severity") != "ERROR":
        return DashboardValidationResult("FAIL", "blocked persistent runtime status must render as error", "SCHEMA_IDENTITY_MISMATCH")

    paper_recovery_guard = shell.get("paper_runtime_recovery_guard_status")
    if not isinstance(paper_recovery_guard, dict):
        return DashboardValidationResult("FAIL", "dashboard paper_runtime_recovery_guard_status missing", "SCHEMA_IDENTITY_MISMATCH")
    if (
        paper_recovery_guard.get("truth_role") != "dashboard_serving_truth"
        or paper_recovery_guard.get("source") not in PAPER_RUNTIME_RECOVERY_GUARD_SOURCES
    ):
        return DashboardValidationResult("BLOCKED", "paper runtime recovery guard display cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if paper_recovery_guard.get("display_only") is not True or paper_recovery_guard.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "paper runtime recovery guard display must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        paper_recovery_guard.get("live_order_ready")
        or paper_recovery_guard.get("live_order_allowed")
        or paper_recovery_guard.get("can_live_trade")
        or paper_recovery_guard.get("scale_up_allowed")
        or paper_recovery_guard.get("actual_long_run_evidence_created")
        or paper_recovery_guard.get("promotion_eligible")
    ):
        return DashboardValidationResult("BLOCKED", "paper runtime recovery guard attempted live, scale, promotion, or long-run permission", "LIVE_FINAL_GUARD_FAILED")
    if paper_recovery_guard.get("status") not in PAPER_RUNTIME_RECOVERY_GUARD_STATUSES:
        return DashboardValidationResult("FAIL", "paper runtime recovery guard status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if paper_recovery_guard.get("severity") not in OPERATION_STATUS_LEVELS or paper_recovery_guard.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "paper runtime recovery guard severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if paper_recovery_guard.get("severity") == "NORMAL" and paper_recovery_guard.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal paper runtime recovery guard must use green or blue", "SCHEMA_IDENTITY_MISMATCH")
    if paper_recovery_guard.get("severity") == "WARNING" and paper_recovery_guard.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning paper runtime recovery guard must use yellow", "SCHEMA_IDENTITY_MISMATCH")
    if paper_recovery_guard.get("severity") == "ERROR" and paper_recovery_guard.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error paper runtime recovery guard must use red", "SCHEMA_IDENTITY_MISMATCH")
    recovery_guard_source_loaded = paper_recovery_guard.get("source") == "upbit_paper_runtime_recovery_guard_report.json"
    recovery_guard_source_listed = "upbit_paper_runtime_recovery_guard_report.json" in source_filenames
    if recovery_guard_source_loaded and not recovery_guard_source_listed:
        return DashboardValidationResult("BLOCKED", "paper runtime recovery guard status must be backed by a listed source artifact", "HARD_TRUTH_MISSING")
    if not recovery_guard_source_loaded and recovery_guard_source_listed:
        return DashboardValidationResult("BLOCKED", "paper runtime recovery guard source artifact is listed while status is not loaded", "SCHEMA_IDENTITY_MISMATCH")
    for count_field in (
        "canonical_jsonl_checked_count",
        "corrupted_jsonl_quarantined_count",
        "ledger_jsonl_checked_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "ledger_jsonl_invalid_count",
        "orphan_tmp_file_count",
    ):
        if not isinstance(paper_recovery_guard.get(count_field), int) or paper_recovery_guard.get(count_field) < 0:
            return DashboardValidationResult("FAIL", f"paper runtime recovery guard count is invalid: {count_field}", "SCHEMA_IDENTITY_MISMATCH")
    for text_field in ("guard_id", "loop_id", "latest_cycle_status", "resume_action", "primary_blocker_code", "one_line_summary", "next_operator_action"):
        if not isinstance(paper_recovery_guard.get(text_field), str) or not paper_recovery_guard.get(text_field, "").strip():
            return DashboardValidationResult("FAIL", f"paper runtime recovery guard missing {text_field}", "SCHEMA_IDENTITY_MISMATCH")
    if paper_recovery_guard.get("paper_runtime_resume_allowed") and paper_recovery_guard.get("status") != "PASS":
        return DashboardValidationResult("BLOCKED", "paper runtime resume cannot be allowed unless recovery guard PASS", "RECONCILIATION_REQUIRED")
    if paper_recovery_guard.get("status") == "PASS":
        if (
            paper_recovery_guard.get("source") != "upbit_paper_runtime_recovery_guard_report.json"
            or paper_recovery_guard.get("latest_cycle_status") != "PASS"
            or paper_recovery_guard.get("latest_cycle_recoverable") is not True
            or paper_recovery_guard.get("corrupted_jsonl_quarantined_count") != 0
            or paper_recovery_guard.get("corrupted_ledger_jsonl_quarantined_count") != 0
            or paper_recovery_guard.get("ledger_jsonl_invalid_count") != 0
            or paper_recovery_guard.get("orphan_tmp_file_count") != 0
            or paper_recovery_guard.get("resume_action") != "RESUME_PAPER_ONLY"
            or paper_recovery_guard.get("paper_runtime_resume_allowed") is not True
            or paper_recovery_guard.get("primary_blocker_code") != "LIVE_READY_MISSING"
        ):
            return DashboardValidationResult("BLOCKED", "PASS paper recovery guard requires clean bounded PAPER recovery and live still blocked", "LIVE_FINAL_GUARD_FAILED")
    if paper_recovery_guard.get("status") in {"BLOCKED", "INVALID"}:
        if paper_recovery_guard.get("severity") != "ERROR" or paper_recovery_guard.get("paper_runtime_resume_allowed"):
            return DashboardValidationResult("FAIL", "blocked or invalid paper recovery guard must render as error and block resume", "SCHEMA_IDENTITY_MISMATCH")
    if paper_recovery_guard.get("status") in {"NOT_LOADED", "STALE"} and paper_recovery_guard.get("paper_runtime_resume_allowed"):
        return DashboardValidationResult("BLOCKED", "not-loaded or stale paper recovery guard cannot allow resume", "RECONCILIATION_REQUIRED")

    runtime_boundary = shell.get("runtime_evidence_boundary")
    if not isinstance(runtime_boundary, dict):
        return DashboardValidationResult("FAIL", "dashboard runtime_evidence_boundary missing", "SCHEMA_IDENTITY_MISMATCH")
    if (
        runtime_boundary.get("truth_role") != "dashboard_serving_truth"
        or runtime_boundary.get("source") not in LONG_RUN_SUMMARY_SOURCES
    ):
        return DashboardValidationResult("BLOCKED", "runtime evidence boundary cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if runtime_boundary.get("display_only") is not True or runtime_boundary.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "runtime evidence boundary must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        runtime_boundary.get("live_review_evidence_eligible")
        or runtime_boundary.get("live_order_ready")
        or runtime_boundary.get("live_order_allowed")
        or runtime_boundary.get("can_live_trade")
        or runtime_boundary.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "runtime evidence boundary attempted live review, live order, or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if runtime_boundary.get("status") not in RUNTIME_EVIDENCE_BOUNDARY_STATUSES:
        return DashboardValidationResult("FAIL", "runtime evidence boundary status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_boundary.get("actual_long_run_evidence_status") not in RUNTIME_EVIDENCE_ACTUAL_STATUSES:
        return DashboardValidationResult("FAIL", "actual long-run evidence status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_boundary.get("short_window_evidence_status") != shadow_harness.get("status"):
        return DashboardValidationResult("FAIL", "runtime boundary short-window status drifted from harness status", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_boundary.get("stub_runtime_evidence_status") != shadow_persistent.get("status"):
        return DashboardValidationResult("FAIL", "runtime boundary stub status drifted from persistent runtime status", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_boundary.get("long_run_operator_status") != long_run.get("status"):
        return DashboardValidationResult("FAIL", "runtime boundary long-run status drifted from long-run summary", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_boundary.get("runtime_orchestration_status") not in SHADOW_RUNTIME_ORCHESTRATION_STATUSES:
        return DashboardValidationResult("FAIL", "runtime boundary orchestration status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    runtime_requirements = runtime_boundary.get("evidence_requirements")
    if (
        not isinstance(runtime_requirements, list)
        or len(runtime_requirements) != len(RUNTIME_EVIDENCE_REQUIREMENT_IDS)
        or not isinstance(runtime_boundary.get("evidence_requirement_summary"), str)
        or not isinstance(runtime_boundary.get("evidence_requirements_blocking_count"), int)
    ):
        return DashboardValidationResult("FAIL", "runtime evidence boundary requirements missing or malformed", "SCHEMA_IDENTITY_MISMATCH")
    runtime_requirement_ids = [item.get("requirement_id") for item in runtime_requirements if isinstance(item, dict)]
    if runtime_requirement_ids != list(RUNTIME_EVIDENCE_REQUIREMENT_IDS):
        return DashboardValidationResult("FAIL", "runtime evidence boundary requirements are incomplete or reordered", "SCHEMA_IDENTITY_MISMATCH")
    runtime_requirement_by_id = {item["requirement_id"]: item for item in runtime_requirements if isinstance(item, dict)}
    computed_blocking_count = 0
    for item in runtime_requirements:
        if not isinstance(item, dict):
            return DashboardValidationResult("FAIL", "runtime evidence boundary requirement entry is invalid", "SCHEMA_IDENTITY_MISMATCH")
        for field in ("label", "status", "source", "detail", "next_operator_action"):
            if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                return DashboardValidationResult("FAIL", f"runtime evidence requirement missing {field}", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("status") not in RUNTIME_EVIDENCE_REQUIREMENT_STATUSES:
            return DashboardValidationResult("FAIL", "runtime evidence requirement status is unknown", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("status") != "PASS":
            computed_blocking_count += 1
        if (
            item.get("blocking_for_live_review") is not True
            or item.get("display_only") is not True
            or item.get("dashboard_truth_only") is not True
            or item.get("live_order_ready")
            or item.get("live_order_allowed")
            or item.get("can_live_trade")
            or item.get("scale_up_allowed")
        ):
            return DashboardValidationResult("BLOCKED", "runtime evidence requirement attempted to hide live-review blocker or create permission", "LIVE_FINAL_GUARD_FAILED")
    if runtime_boundary.get("evidence_requirements_blocking_count") != computed_blocking_count:
        return DashboardValidationResult("FAIL", "runtime evidence boundary blocking count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    long_run_duration_floor_met = int(long_run.get("observed_span_seconds", 0) or 0) >= ACTUAL_LONG_RUN_MIN_VALIDATED_SPAN_SECONDS
    long_run_cycle_floor_met = (
        int(long_run.get("history_sample_count", 0) or 0) >= ACTUAL_LONG_RUN_MIN_ACTUAL_CYCLE_COUNT
        and int(long_run.get("stable_sample_count", 0) or 0) >= ACTUAL_LONG_RUN_MIN_ACTUAL_CYCLE_COUNT
        and int(long_run.get("degraded_sample_count", 0) or 0) == 0
        and int(long_run.get("stale_sample_count", 0) or 0) == 0
    )
    if runtime_requirement_by_id["ACTUAL_RUNTIME_DURATION"].get("status") == "PASS" and not long_run_duration_floor_met:
        return DashboardValidationResult("BLOCKED", "actual runtime duration cannot pass before the 86400s floor is met", "LIVE_FINAL_GUARD_FAILED")
    if (
        runtime_requirement_by_id["ACTUAL_CYCLE_COUNT"].get("status") == "PASS"
        or runtime_requirement_by_id["EVIDENCE_WINDOW_COUNT"].get("status") == "PASS"
    ) and not long_run_cycle_floor_met:
        return DashboardValidationResult("BLOCKED", "actual cycle and evidence-window requirements cannot pass before the stable-sample floor is met", "LIVE_FINAL_GUARD_FAILED")
    if (
        runtime_boundary.get("actual_long_run_evidence_status") != "VALIDATED_STABLE"
        and runtime_requirement_by_id["RECOVERY_AND_PARTIAL_WRITE_CLEAN"].get("status") == "PASS"
    ):
        return DashboardValidationResult("BLOCKED", "recovery-clean long-run proof cannot pass before validated actual long-run evidence exists", "LIVE_FINAL_GUARD_FAILED")
    if runtime_boundary.get("severity") not in OPERATION_STATUS_LEVELS or runtime_boundary.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "runtime boundary severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_boundary.get("severity") == "NORMAL" and runtime_boundary.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal runtime boundary must use green or blue", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_boundary.get("severity") == "WARNING" and runtime_boundary.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning runtime boundary must use yellow", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_boundary.get("severity") == "ERROR" and runtime_boundary.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error runtime boundary must use red", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_boundary.get("actual_long_run_evidence_status") == "VALIDATED_STABLE":
        if long_run.get("status") == "DISPLAY_HISTORY_STABLE":
            return DashboardValidationResult("BLOCKED", "display-history stability cannot claim validated actual long-run evidence", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        if long_run.get("status") != "VALIDATED_STABLE" or runtime_boundary.get("status") != "ACTUAL_LONG_RUN_VALIDATED":
            return DashboardValidationResult("BLOCKED", "runtime boundary cannot claim validated long-run evidence without validated long-run summary", "HARD_TRUTH_MISSING")
        if not (long_run_duration_floor_met and long_run_cycle_floor_met):
            return DashboardValidationResult("BLOCKED", "runtime boundary cannot claim validated actual long-run evidence before duration and stable-sample floors are met", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    elif runtime_boundary.get("status") == "ACTUAL_LONG_RUN_VALIDATED":
        return DashboardValidationResult("BLOCKED", "runtime boundary validated status conflicts with actual evidence status", "HARD_TRUTH_MISSING")
    if shadow_persistent.get("status") == "STUB_ONLY" and runtime_boundary.get("actual_long_run_evidence_status") != "VALIDATED_STABLE":
        boundary_message = str(runtime_boundary.get("stub_boundary_message", "")).lower()
        if "stub" not in boundary_message or "not actual long-run evidence" not in boundary_message:
            return DashboardValidationResult("BLOCKED", "runtime boundary must explain stub runtime is not actual long-run evidence", "HARD_TRUTH_MISSING")
    if shadow_harness.get("status") == "SHORT_WINDOW_EXECUTED" and runtime_boundary.get("actual_long_run_evidence_status") == "VALIDATED_STABLE":
        if long_run.get("source") != "stability_history.json":
            return DashboardValidationResult("BLOCKED", "short-window harness cannot create validated long-run evidence", "LIVE_FINAL_GUARD_FAILED")

    runtime_orchestration = shell.get("shadow_runtime_orchestration_status")
    if not isinstance(runtime_orchestration, dict):
        return DashboardValidationResult("FAIL", "dashboard shadow_runtime_orchestration_status missing", "SCHEMA_IDENTITY_MISMATCH")
    if (
        runtime_orchestration.get("truth_role") != "dashboard_serving_truth"
        or runtime_orchestration.get("source") not in SHADOW_RUNTIME_ORCHESTRATION_SOURCES
    ):
        return DashboardValidationResult("BLOCKED", "runtime orchestration display cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if runtime_orchestration.get("display_only") is not True or runtime_orchestration.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "runtime orchestration display must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        runtime_orchestration.get("actual_long_run_runtime_present")
        or runtime_orchestration.get("long_run_evidence_eligible")
        or runtime_orchestration.get("scorecard_input_eligible")
        or runtime_orchestration.get("promotion_eligible")
        or runtime_orchestration.get("live_order_ready")
        or runtime_orchestration.get("live_order_allowed")
        or runtime_orchestration.get("can_live_trade")
        or runtime_orchestration.get("scale_up_allowed")
        or runtime_orchestration.get("order_adapter_called")
    ):
        return DashboardValidationResult("BLOCKED", "runtime orchestration attempted live, scale, scorecard, promotion, or order permission", "LIVE_FINAL_GUARD_FAILED")
    if runtime_orchestration.get("status") not in SHADOW_RUNTIME_ORCHESTRATION_STATUSES:
        return DashboardValidationResult("FAIL", "runtime orchestration status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_boundary.get("runtime_orchestration_status") != runtime_orchestration.get("status"):
        return DashboardValidationResult("FAIL", "runtime boundary orchestration status drifted from orchestration guard", "SCHEMA_IDENTITY_MISMATCH")
    if (
        (runtime_requirement_by_id["PERSISTENT_RUNTIME_SOURCE"].get("status") == "PASS")
        != (shadow_persistent.get("status") == "STUB_ONLY")
    ):
        return DashboardValidationResult("FAIL", "runtime evidence persistent source requirement drifted from source status", "SCHEMA_IDENTITY_MISMATCH")
    if (
        (runtime_requirement_by_id["SHORT_WINDOW_HARNESS_SOURCE"].get("status") == "PASS")
        != (shadow_harness.get("status") == "SHORT_WINDOW_EXECUTED")
    ):
        return DashboardValidationResult("FAIL", "runtime evidence harness source requirement drifted from source status", "SCHEMA_IDENTITY_MISMATCH")
    if (
        (runtime_requirement_by_id["RUNTIME_ORCHESTRATION_SOURCE_PAIRING"].get("status") == "PASS")
        != (runtime_orchestration.get("status") == "BOUNDARY_VERIFIED")
    ):
        return DashboardValidationResult("FAIL", "runtime evidence orchestration requirement drifted from source status", "SCHEMA_IDENTITY_MISMATCH")
    orchestration_source_loaded = runtime_orchestration.get("source") == "runtime_orchestration_report.json"
    orchestration_source_listed = "runtime_orchestration_report.json" in source_filenames
    if orchestration_source_loaded and not orchestration_source_listed:
        return DashboardValidationResult("BLOCKED", "runtime orchestration status must be backed by a listed source artifact", "HARD_TRUTH_MISSING")
    if not orchestration_source_loaded and orchestration_source_listed:
        return DashboardValidationResult("BLOCKED", "runtime orchestration source artifact is listed while status is not loaded", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_orchestration.get("severity") not in OPERATION_STATUS_LEVELS or runtime_orchestration.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "runtime orchestration severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_orchestration.get("severity") == "NORMAL" and runtime_orchestration.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal runtime orchestration must use green or blue", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_orchestration.get("severity") == "WARNING" and runtime_orchestration.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning runtime orchestration must use yellow", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_orchestration.get("severity") == "ERROR" and runtime_orchestration.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error runtime orchestration must use red", "SCHEMA_IDENTITY_MISMATCH")
    for count_field in ("source_binding_count", "observed_actual_runtime_seconds", "observed_actual_cycle_count", "observed_evidence_window_count"):
        if not isinstance(runtime_orchestration.get(count_field), int) or runtime_orchestration.get(count_field) < 0:
            return DashboardValidationResult("FAIL", f"runtime orchestration count is invalid: {count_field}", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_orchestration.get("persistent_runtime_status") != shadow_persistent.get("status"):
        return DashboardValidationResult("FAIL", "runtime orchestration persistent source status drifted from dashboard", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_orchestration.get("short_window_harness_status") != shadow_harness.get("status"):
        return DashboardValidationResult("FAIL", "runtime orchestration harness source status drifted from dashboard", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_orchestration.get("status") == "BOUNDARY_VERIFIED":
        if runtime_orchestration.get("source_validation_status") != "PASS" or runtime_orchestration.get("source_runtime_hash_pairing_verified") is not True:
            return DashboardValidationResult("BLOCKED", "verified runtime orchestration requires PASS source validation and source hash pairing", "HARD_TRUTH_MISSING")
        if (
            runtime_orchestration.get("source_binding_count") != 2
            or runtime_orchestration.get("orchestration_decision") != "BLOCK_LONG_RUN_EVIDENCE"
            or runtime_orchestration.get("runtime_evidence_role") != "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN"
            or runtime_orchestration.get("optimizer_ranking_action") != "BLOCK_RANKING"
            or runtime_orchestration.get("primary_blocker_code") != "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
        ):
            return DashboardValidationResult("BLOCKED", "runtime orchestration boundary did not preserve long-run and optimizer blockers", "LIVE_FINAL_GUARD_FAILED")
        if (
            runtime_orchestration.get("observed_actual_runtime_seconds") != 0
            or runtime_orchestration.get("observed_actual_cycle_count") != 0
            or runtime_orchestration.get("observed_evidence_window_count") != 0
        ):
            return DashboardValidationResult("BLOCKED", "runtime orchestration cannot claim observed long-run runtime from stub or harness reports", "LIVE_FINAL_GUARD_FAILED")
    if runtime_orchestration.get("status") == "NOT_LOADED" and runtime_orchestration.get("source") != "NOT_LOADED":
        return DashboardValidationResult("FAIL", "not-loaded runtime orchestration must not cite a report source", "SCHEMA_IDENTITY_MISMATCH")
    if runtime_orchestration.get("status") == "BLOCKED" and runtime_orchestration.get("severity") != "ERROR":
        return DashboardValidationResult("FAIL", "blocked runtime orchestration status must render as error", "SCHEMA_IDENTITY_MISMATCH")

    operator_action = shell.get("operator_action_summary")
    if not isinstance(operator_action, dict):
        return DashboardValidationResult("FAIL", "dashboard operator_action_summary missing", "SCHEMA_IDENTITY_MISMATCH")
    if operator_action.get("truth_role") != "dashboard_serving_truth" or operator_action.get("source") not in DISPLAY_SOURCE_FILENAMES:
        return DashboardValidationResult("BLOCKED", "operator action summary cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if operator_action.get("display_only") is not True or operator_action.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "operator action summary must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        operator_action.get("live_order_ready")
        or operator_action.get("live_order_allowed")
        or operator_action.get("can_live_trade")
        or operator_action.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "operator action summary attempted to create live or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if operator_action.get("status") not in OPERATOR_ACTION_STATUSES:
        return DashboardValidationResult("FAIL", "operator action status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if operator_action.get("severity") not in OPERATION_STATUS_LEVELS or operator_action.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "operator action severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if operator_action.get("workflow_step") not in OPERATOR_WORKFLOW_STEPS or operator_action.get("primary_action") not in OPERATOR_ACTION_KINDS:
        return DashboardValidationResult("FAIL", "operator action workflow or action kind is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if operator_action.get("severity") == "NORMAL" and operator_action.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal operator action must use green or blue", "SCHEMA_IDENTITY_MISMATCH")
    if operator_action.get("severity") == "WARNING" and operator_action.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning operator action must use yellow", "SCHEMA_IDENTITY_MISMATCH")
    if operator_action.get("severity") == "ERROR" and operator_action.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error operator action must use red", "SCHEMA_IDENTITY_MISMATCH")
    for text_field in ("primary_action_label", "one_line_blocker", "next_operator_action", "decision_final_action"):
        if not isinstance(operator_action.get(text_field), str) or not operator_action.get(text_field, "").strip():
            return DashboardValidationResult("FAIL", f"operator action missing {text_field}", "SCHEMA_IDENTITY_MISMATCH")
    if operator_action.get("primary_blocker_code") != shell.get("blocking_reason"):
        return DashboardValidationResult("FAIL", "operator action blocker must match dashboard primary blocker", "SCHEMA_IDENTITY_MISMATCH")
    if operator_action.get("dangerous_controls_present") is not False:
        return DashboardValidationResult("BLOCKED", "operator action summary cannot expose dangerous controls", "LIVE_FINAL_GUARD_FAILED")
    if operator_action.get("live_review_blocked") is not True or operator_action.get("paper_review_only") is not True:
        return DashboardValidationResult("BLOCKED", "operator action summary must keep live review blocked and paper-only", "LIVE_FINAL_GUARD_FAILED")
    if operator_action.get("safe_to_continue_paper") is True and operator_action.get("status") not in {"PAPER_MONITORING", "PAPER_REVIEW_READY"}:
        return DashboardValidationResult("BLOCKED", "safe-to-continue flag is inconsistent with operator action status", "HARD_TRUTH_MISSING")
    risk_for_operator = shell.get("risk_exposure_snapshot") if isinstance(shell.get("risk_exposure_snapshot"), dict) else {}
    if operator_action.get("status") == "PAPER_MONITORING" and (
        operation.get("severity") != "NORMAL"
        or risk_for_operator.get("status") != "LOW_RISK"
        or long_run.get("status") not in {"RUNNING_NOW", "DISPLAY_HISTORY_STABLE", "VALIDATED_STABLE"}
    ):
        return DashboardValidationResult("BLOCKED", "paper monitoring action requires normal operation, low risk, and current long-run status", "HARD_TRUTH_MISSING")
    if operator_action.get("status") == "REFRESH_REQUIRED" and operator_action.get("primary_action") != "REFRESH_DASHBOARD":
        return DashboardValidationResult("FAIL", "refresh-required operator action must tell the user to refresh", "SCHEMA_IDENTITY_MISMATCH")
    if operator_action.get("status") == "BLOCKED" and operator_action.get("severity") != "ERROR":
        return DashboardValidationResult("FAIL", "blocked operator action must render as error", "SCHEMA_IDENTITY_MISMATCH")

    workflow = shell.get("operator_workflow_summary")
    if not isinstance(workflow, dict):
        return DashboardValidationResult("FAIL", "dashboard operator_workflow_summary missing", "SCHEMA_IDENTITY_MISMATCH")
    if workflow.get("truth_role") != "dashboard_serving_truth" or workflow.get("source") not in DISPLAY_SOURCE_FILENAMES:
        return DashboardValidationResult("BLOCKED", "operator workflow cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if workflow.get("display_only") is not True or workflow.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "operator workflow must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if workflow.get("live_order_ready") or workflow.get("live_order_allowed") or workflow.get("can_live_trade") or workflow.get("scale_up_allowed"):
        return DashboardValidationResult("BLOCKED", "operator workflow attempted to create live or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if workflow.get("status") not in OPERATOR_WORKFLOW_STATUSES:
        return DashboardValidationResult("FAIL", "operator workflow status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if workflow.get("severity") not in OPERATION_STATUS_LEVELS or workflow.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "operator workflow severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if workflow.get("severity") == "NORMAL" and workflow.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal operator workflow must use green or blue", "SCHEMA_IDENTITY_MISMATCH")
    if workflow.get("severity") == "WARNING" and workflow.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning operator workflow must use yellow", "SCHEMA_IDENTITY_MISMATCH")
    if workflow.get("severity") == "ERROR" and workflow.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error operator workflow must use red", "SCHEMA_IDENTITY_MISMATCH")
    if workflow.get("current_step") != operator_action.get("workflow_step"):
        return DashboardValidationResult("FAIL", "operator workflow current step must match operator action", "SCHEMA_IDENTITY_MISMATCH")
    if workflow.get("live_review_blocked") is not True or workflow.get("live_blocker_code") != "LIVE_READY_MISSING":
        return DashboardValidationResult("BLOCKED", "operator workflow must keep live review blocked", "LIVE_FINAL_GUARD_FAILED")
    steps = workflow.get("steps")
    if not isinstance(steps, list) or len(steps) != 4 or workflow.get("step_count") != 4:
        return DashboardValidationResult("FAIL", "operator workflow must expose exactly four steps", "SCHEMA_IDENTITY_MISMATCH")
    step_ids = [step.get("step_id") for step in steps if isinstance(step, dict)]
    if step_ids != ["RUN_PAPER", "INSPECT_DASHBOARD", "COLLECT_EVIDENCE", "LIVE_REVIEW_BLOCKED"]:
        return DashboardValidationResult("FAIL", "operator workflow step order mismatch", "SCHEMA_IDENTITY_MISMATCH")
    current_steps = []
    for step in steps:
        if not isinstance(step, dict):
            return DashboardValidationResult("FAIL", "operator workflow step must be an object", "SCHEMA_IDENTITY_MISMATCH")
        if step.get("status") not in OPERATOR_WORKFLOW_STEP_STATUSES or step.get("action_kind") not in OPERATOR_ACTION_KINDS:
            return DashboardValidationResult("FAIL", "operator workflow step enum mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if step.get("display_only") is not True or step.get("dashboard_truth_only") is not True:
            return DashboardValidationResult("BLOCKED", "operator workflow step must remain display-only", "LIVE_FINAL_GUARD_FAILED")
        if step.get("live_order_ready") or step.get("live_order_allowed") or step.get("can_live_trade") or step.get("scale_up_allowed"):
            return DashboardValidationResult("BLOCKED", "operator workflow step attempted to create live or scale permission", "LIVE_FINAL_GUARD_FAILED")
        if step.get("current") is True:
            current_steps.append(step.get("step_id"))
    if workflow.get("status") != "BLOCKED" and current_steps != [workflow.get("current_step")]:
        return DashboardValidationResult("FAIL", "operator workflow must have exactly one current step", "SCHEMA_IDENTITY_MISMATCH")
    live_step = steps[-1]
    if live_step.get("step_id") != "LIVE_REVIEW_BLOCKED" or live_step.get("status") != "BLOCKED" or live_step.get("current") is True:
        return DashboardValidationResult("BLOCKED", "live review workflow step must stay blocked and non-current", "LIVE_FINAL_GUARD_FAILED")
    if workflow.get("status") == "COLLECTING_EVIDENCE" and workflow.get("current_step") != "COLLECT_EVIDENCE":
        return DashboardValidationResult("FAIL", "collecting workflow must point to evidence collection", "SCHEMA_IDENTITY_MISMATCH")
    if workflow.get("status") == "REFRESH_REQUIRED" and workflow.get("current_step") != "RUN_PAPER":
        return DashboardValidationResult("FAIL", "refresh workflow must point to RUN_PAPER", "SCHEMA_IDENTITY_MISMATCH")

    maturity = shell.get("profitability_maturity")
    if not isinstance(maturity, dict):
        return DashboardValidationResult("FAIL", "dashboard profitability_maturity missing", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("truth_role") != "dashboard_serving_truth" or maturity.get("source") not in PROFITABILITY_MATURITY_SOURCES:
        return DashboardValidationResult("BLOCKED", "profitability maturity cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if maturity.get("evidence_source") not in PROFITABILITY_MATURITY_EVIDENCE_SOURCES:
        return DashboardValidationResult("FAIL", "profitability maturity evidence source is unknown", "SCHEMA_IDENTITY_MISMATCH")
    scorecard_source = maturity.get("candidate_scorecard_source")
    scorecard_status = maturity.get("candidate_scorecard_status")
    if scorecard_source not in CANDIDATE_SCORECARD_SOURCE_FILENAMES:
        return DashboardValidationResult("FAIL", "candidate scorecard source is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if scorecard_status not in CANDIDATE_SCORECARD_STATUSES:
        return DashboardValidationResult("FAIL", "candidate scorecard display status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    scorecard_source_loaded = scorecard_source == "candidate_scorecard.json"
    scorecard_source_listed = "candidate_scorecard.json" in source_filenames
    if scorecard_source_loaded and not scorecard_source_listed:
        return DashboardValidationResult("BLOCKED", "candidate scorecard display must be backed by a listed source artifact", "HARD_TRUTH_MISSING")
    if not scorecard_source_loaded and scorecard_source_listed:
        return DashboardValidationResult("BLOCKED", "candidate scorecard source artifact is listed while display is not loaded", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("candidate_scorecard_scope") not in PROFITABILITY_SCORECARD_SCOPES:
        return DashboardValidationResult("FAIL", "candidate scorecard scope is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(maturity.get("candidate_scorecard_ranking_eligible"), bool):
        return DashboardValidationResult("FAIL", "candidate scorecard ranking flag must be boolean", "SCHEMA_IDENTITY_MISMATCH")
    scorecard_net_ev = maturity.get("candidate_scorecard_net_ev_after_cost_bps")
    if scorecard_net_ev is not None and not isinstance(scorecard_net_ev, (int, float)):
        return DashboardValidationResult("FAIL", "candidate scorecard net EV must be numeric or null", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(maturity.get("candidate_scorecard_net_ev_after_cost_display"), str) or not maturity.get("candidate_scorecard_net_ev_after_cost_display", "").strip():
        return DashboardValidationResult("FAIL", "candidate scorecard must expose net EV display", "SCHEMA_IDENTITY_MISMATCH")
    for text_field in ("candidate_scorecard_primary_blocker_code", "candidate_scorecard_blocker_summary", "candidate_scorecard_next_action"):
        if not isinstance(maturity.get(text_field), str) or not maturity.get(text_field, "").strip():
            return DashboardValidationResult("FAIL", f"candidate scorecard missing {text_field}", "SCHEMA_IDENTITY_MISMATCH")
    if scorecard_status == "PAPER_RANKING_REVIEW_ONLY":
        if (
            maturity.get("candidate_scorecard_ranking_eligible") is not True
            or maturity.get("candidate_scorecard_scope") != "PAPER_SCORECARD_INPUT_ONLY"
            or maturity.get("candidate_scorecard_primary_blocker_code") != "LIVE_READY_MISSING"
        ):
            return DashboardValidationResult("BLOCKED", "PAPER ranking scorecard must stay review-only and live-blocked", "LIVE_FINAL_GUARD_FAILED")
    if scorecard_status in {"PAPER_RANKING_BLOCKED", "BLOCKED", "STALE"} and maturity.get("candidate_scorecard_ranking_eligible") is True:
        return DashboardValidationResult("BLOCKED", "blocked or stale candidate scorecard cannot show ranking eligibility", "HARD_TRUTH_MISSING")
    if scorecard_status == "BLOCKED" and maturity.get("candidate_scorecard_scope") != "BLOCKED_DISPLAY_ONLY":
        return DashboardValidationResult("FAIL", "blocked candidate scorecard must render as blocked display only", "SCHEMA_IDENTITY_MISMATCH")
    if scorecard_status == "STALE" and maturity.get("candidate_scorecard_scope") != "STALE_DISPLAY_ONLY":
        return DashboardValidationResult("FAIL", "stale candidate scorecard must render as stale display only", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("rollup_source") not in {"NOT_LOADED", "profitability_evidence_maturity_rollup.json"}:
        return DashboardValidationResult("FAIL", "profitability maturity rollup source is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("rollup_source_status") not in {"NOT_LOADED", "LOADED", "BLOCKED"}:
        return DashboardValidationResult("FAIL", "profitability maturity rollup source status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(maturity.get("rollup_component_count"), int) or not isinstance(maturity.get("rollup_required_component_count"), int):
        return DashboardValidationResult("FAIL", "profitability maturity rollup component counts must be integers", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("rollup_source_status") == "LOADED":
        if maturity.get("rollup_source") != "profitability_evidence_maturity_rollup.json":
            return DashboardValidationResult("FAIL", "loaded rollup must expose rollup source file", "SCHEMA_IDENTITY_MISMATCH")
        if maturity.get("rollup_required_component_count") != len(PROFITABILITY_MATURITY_COMPONENT_IDS):
            return DashboardValidationResult("FAIL", "loaded rollup required component count mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if maturity.get("rollup_component_count") != len(PROFITABILITY_MATURITY_COMPONENT_IDS):
            return DashboardValidationResult("FAIL", "loaded rollup component count mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if maturity.get("rollup_coverage_complete") is not True:
            return DashboardValidationResult("BLOCKED", "loaded rollup must prove component coverage", "HARD_TRUTH_MISSING")
        if maturity.get("scorecard_input_eligible") is True or maturity.get("optimizer_ranking_action") == "ALLOW_RANKING":
            return DashboardValidationResult("BLOCKED", "rollup display cannot enable optimizer ranking directly", "LIVE_FINAL_GUARD_FAILED")
    if maturity.get("display_only") is not True or maturity.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "profitability maturity must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        maturity.get("live_order_ready")
        or maturity.get("live_order_allowed")
        or maturity.get("can_live_trade")
        or maturity.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "profitability maturity attempted to create live or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if maturity.get("status") not in PROFITABILITY_MATURITY_STATUSES:
        return DashboardValidationResult("FAIL", "profitability maturity status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("severity") not in OPERATION_STATUS_LEVELS:
        return DashboardValidationResult("FAIL", "profitability maturity severity is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "profitability maturity color token is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("optimizer_ranking_action") not in PROFITABILITY_RANKING_ACTIONS:
        return DashboardValidationResult("FAIL", "profitability maturity ranking action is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("scorecard_scope") not in PROFITABILITY_SCORECARD_SCOPES:
        return DashboardValidationResult("FAIL", "profitability scorecard scope is unknown", "SCHEMA_IDENTITY_MISMATCH")
    actual_runtime_source_status = maturity.get("actual_runtime_source_status")
    actual_runtime_source_count = maturity.get("actual_runtime_source_count")
    actual_runtime_source_summary = maturity.get("actual_runtime_source_summary")
    if actual_runtime_source_status not in PROFITABILITY_ACTUAL_RUNTIME_SOURCE_STATUSES:
        return DashboardValidationResult("FAIL", "profitability actual runtime source status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(actual_runtime_source_count, int) or actual_runtime_source_count < 0:
        return DashboardValidationResult("FAIL", "profitability actual runtime source count must be non-negative", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(actual_runtime_source_summary, str) or not actual_runtime_source_summary.strip():
        return DashboardValidationResult("FAIL", "profitability actual runtime source summary is missing", "SCHEMA_IDENTITY_MISMATCH")
    maturity_long_run_eligible = maturity.get("long_run_evidence_eligible") is True
    maturity_long_run_blocker = maturity.get("long_run_blocker_code")
    if maturity_long_run_eligible and (
        actual_runtime_source_status != "VALIDATED_NON_LIVE_RUNTIME" or actual_runtime_source_count <= 0
    ):
        return DashboardValidationResult("BLOCKED", "profitability long-run evidence lacks validated actual runtime source", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and actual_runtime_source_count <= 0:
        return DashboardValidationResult("BLOCKED", "validated actual runtime source status lacks source ids", "HARD_TRUTH_MISSING")
    if not maturity_long_run_eligible and not maturity_long_run_blocker:
        return DashboardValidationResult("BLOCKED", "profitability maturity must expose long-run evidence blocker", "HARD_TRUTH_MISSING")
    if maturity.get("live_readiness_status") not in PROFITABILITY_LIVE_READINESS_STATUSES:
        return DashboardValidationResult("BLOCKED", "profitability maturity attempted to look live-ready", "LIVE_FINAL_GUARD_FAILED")
    warning_text = str(maturity.get("operator_warning", ""))
    warning_lower = warning_text.lower()
    if "not live_ready" not in warning_lower or "live orders" not in warning_lower:
        return DashboardValidationResult("BLOCKED", "profitability maturity warning must distinguish PAPER scorecard input from LIVE_READY", "HARD_TRUTH_MISSING")
    checklist = maturity.get("evidence_checklist")
    if not isinstance(checklist, list) or len(checklist) != len(PROFITABILITY_EVIDENCE_CHECK_IDS):
        return DashboardValidationResult("FAIL", "profitability maturity evidence checklist is incomplete", "SCHEMA_IDENTITY_MISMATCH")
    passed_checks = 0
    for expected_id, check in zip(PROFITABILITY_EVIDENCE_CHECK_IDS, checklist, strict=True):
        if not isinstance(check, dict) or check.get("check_id") != expected_id:
            return DashboardValidationResult("FAIL", "profitability maturity checklist order mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if check.get("status") not in PROFITABILITY_EVIDENCE_CHECK_STATUSES:
            return DashboardValidationResult("FAIL", "profitability maturity checklist status is unknown", "SCHEMA_IDENTITY_MISMATCH")
        if check.get("display_only") is not True or check.get("dashboard_truth_only") is not True:
            return DashboardValidationResult("BLOCKED", "profitability checklist must remain display-only", "LIVE_FINAL_GUARD_FAILED")
        if (
            check.get("live_order_ready")
            or check.get("live_order_allowed")
            or check.get("can_live_trade")
            or check.get("scale_up_allowed")
        ):
            return DashboardValidationResult("BLOCKED", "profitability checklist attempted to create live or scale permission", "LIVE_FINAL_GUARD_FAILED")
        observed = check.get("observed_count")
        required = check.get("required_count")
        if not isinstance(observed, int) or not isinstance(required, int) or observed < 0 or required < 0:
            return DashboardValidationResult("FAIL", "profitability checklist counts must be non-negative integers", "SCHEMA_IDENTITY_MISMATCH")
        if check.get("status") == "PASS":
            passed_checks += 1
            if observed < required:
                return DashboardValidationResult("BLOCKED", "profitability checklist PASS lacks required evidence count", "HARD_TRUTH_MISSING")
    expected_progress_pct = int((passed_checks / len(PROFITABILITY_EVIDENCE_CHECK_IDS)) * 100)
    if maturity.get("evidence_progress_pct") != expected_progress_pct and maturity.get("evidence_progress_status") not in {"BLOCKED", "STALE"}:
        if maturity.get("evidence_progress_status") == "READY" or maturity.get("evidence_progress_pct") == 100:
            return DashboardValidationResult("BLOCKED", "profitability evidence cannot look complete before checklist evidence passes", "HARD_TRUTH_MISSING")
        return DashboardValidationResult("FAIL", "profitability evidence progress percent mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("evidence_progress_status") not in PROFITABILITY_PROGRESS_STATUSES:
        return DashboardValidationResult("FAIL", "profitability evidence progress status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("evidence_progress_status") == "READY" and expected_progress_pct != 100:
        return DashboardValidationResult("BLOCKED", "profitability evidence cannot be READY before all checks pass", "HARD_TRUTH_MISSING")
    if maturity.get("maturity_gap_status") not in PROFITABILITY_MATURITY_GAP_STATUSES:
        return DashboardValidationResult("FAIL", "profitability maturity gap status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    components = maturity.get("maturity_components")
    if not isinstance(components, list) or len(components) != len(PROFITABILITY_MATURITY_COMPONENT_IDS):
        return DashboardValidationResult("FAIL", "profitability maturity component checklist is incomplete", "SCHEMA_IDENTITY_MISMATCH")
    component_pass_count = 0
    for expected_id, component in zip(PROFITABILITY_MATURITY_COMPONENT_IDS, components, strict=True):
        if not isinstance(component, dict) or component.get("component_id") != expected_id:
            return DashboardValidationResult("FAIL", "profitability maturity component order mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if component.get("status") not in PROFITABILITY_MATURITY_COMPONENT_STATUSES:
            return DashboardValidationResult("FAIL", "profitability maturity component status is unknown", "SCHEMA_IDENTITY_MISMATCH")
        if component.get("priority") not in PROFITABILITY_MATURITY_PRIORITIES:
            return DashboardValidationResult("FAIL", "profitability maturity component priority is unknown", "SCHEMA_IDENTITY_MISMATCH")
        next_required_evidence = component.get("next_required_evidence")
        if not isinstance(next_required_evidence, str) or not next_required_evidence.strip():
            return DashboardValidationResult("FAIL", "profitability maturity component next evidence is missing", "SCHEMA_IDENTITY_MISMATCH")
        if component.get("display_only") is not True or component.get("dashboard_truth_only") is not True:
            return DashboardValidationResult("BLOCKED", "profitability maturity component must remain display-only", "LIVE_FINAL_GUARD_FAILED")
        if (
            component.get("live_order_ready")
            or component.get("live_order_allowed")
            or component.get("can_live_trade")
            or component.get("scale_up_allowed")
        ):
            return DashboardValidationResult("BLOCKED", "profitability maturity component attempted live or scale permission", "LIVE_FINAL_GUARD_FAILED")
        paper_input_eligible = component.get("paper_scorecard_input_eligible") is True
        long_run_eligible = component.get("long_run_evidence_eligible") is True
        long_run_blocker = component.get("long_run_blocker_code")
        if paper_input_eligible and component.get("status") not in {
            "PAPER_SCORECARD_EVIDENCE_PASS",
            "PAPER_SCORECARD_INPUT_ONLY",
            "BLOCKED_LONG_RUN_EVIDENCE",
        }:
            return DashboardValidationResult("FAIL", "profitability maturity scorecard eligibility/status mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if not long_run_eligible and not long_run_blocker:
            return DashboardValidationResult("BLOCKED", "profitability maturity component must expose long-run blocker", "HARD_TRUTH_MISSING")
        if long_run_eligible and long_run_blocker:
            return DashboardValidationResult("BLOCKED", "long-run eligible profitability component cannot keep a long-run blocker", "HARD_TRUTH_MISSING")
        if paper_input_eligible:
            component_pass_count += 1
    if maturity.get("maturity_component_count") != len(PROFITABILITY_MATURITY_COMPONENT_IDS):
        return DashboardValidationResult("FAIL", "profitability maturity component count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("paper_scorecard_component_pass_count") != component_pass_count:
        return DashboardValidationResult("FAIL", "profitability maturity component pass count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_gap_count = len(PROFITABILITY_MATURITY_COMPONENT_IDS) - component_pass_count
    if maturity.get("maturity_gap_count") != expected_gap_count:
        return DashboardValidationResult("FAIL", "profitability maturity gap count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    gap_summary = str(maturity.get("maturity_gap_summary", "")).lower()
    if "not live_ready" not in gap_summary and "live gap" not in gap_summary and "live" not in gap_summary:
        return DashboardValidationResult("BLOCKED", "profitability maturity gap summary must expose live gap", "HARD_TRUTH_MISSING")
    if maturity.get("maturity_gap_count") == 0:
        return DashboardValidationResult("BLOCKED", "MVP-4 dashboard cannot claim zero profitability maturity gaps", "LIVE_FINAL_GUARD_FAILED")
    if maturity.get("scorecard_input_eligible") is True:
        if maturity.get("maturity_gap_status") != "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN":
            return DashboardValidationResult("BLOCKED", "scorecard input must still show open live maturity gap", "LIVE_FINAL_GUARD_FAILED")
        if component_pass_count == 0:
            return DashboardValidationResult("BLOCKED", "scorecard input cannot hide missing profitability component evidence", "HARD_TRUTH_MISSING")
    elif maturity.get("maturity_gap_status") == "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN":
        return DashboardValidationResult("BLOCKED", "paper scorecard maturity gap status requires explicit scorecard input eligibility", "HARD_TRUTH_MISSING")
    if maturity.get("severity") == "NORMAL" and maturity.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal profitability maturity must use green or blue status color", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("severity") == "WARNING" and maturity.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning profitability maturity must use yellow status color", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("severity") == "ERROR" and maturity.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error profitability maturity must use red status color", "SCHEMA_IDENTITY_MISMATCH")
    if maturity.get("scorecard_input_eligible") is True:
        if maturity.get("scorecard_scope") != "PAPER_SCORECARD_INPUT_ONLY":
            return DashboardValidationResult("BLOCKED", "scorecard-ready maturity must remain paper-scorecard-input only", "HARD_TRUTH_MISSING")
        if maturity.get("status") != "SCORECARD_INPUT_READY" or maturity.get("optimizer_ranking_action") != "ALLOW_RANKING":
            return DashboardValidationResult("BLOCKED", "scorecard-ready maturity must explicitly allow paper ranking only", "HARD_TRUTH_MISSING")
        for field in ("candidate_id", "strategy_id", "parameter_hash"):
            if not maturity.get(field):
                return DashboardValidationResult("FAIL", f"scorecard-ready maturity missing {field}", "SCHEMA_IDENTITY_MISMATCH")
        if maturity.get("paper_sample_count", 0) < maturity.get("min_required_samples", 0):
            return DashboardValidationResult("BLOCKED", "scorecard-ready maturity lacks enough paper samples", "HARD_TRUTH_MISSING")
        if maturity.get("shadow_sample_count", 0) < maturity.get("min_required_samples", 0):
            return DashboardValidationResult("BLOCKED", "scorecard-ready maturity lacks enough shadow samples", "HARD_TRUTH_MISSING")
        for field in ("cost_evidence_status", "entry_reason_status", "no_trade_reason_status"):
            if maturity.get(field) != "PASS":
                return DashboardValidationResult("BLOCKED", "scorecard-ready maturity lacks required reason or cost evidence", "HARD_TRUTH_MISSING")
        if maturity.get("evidence_progress_status") != "READY" or maturity.get("evidence_progress_pct") != 100:
            return DashboardValidationResult("BLOCKED", "scorecard-ready maturity lacks complete evidence checklist", "HARD_TRUTH_MISSING")
    elif maturity.get("optimizer_ranking_action") == "ALLOW_RANKING":
        return DashboardValidationResult("BLOCKED", "ranking cannot be allowed when scorecard input is ineligible", "HARD_TRUTH_MISSING")
    elif maturity.get("scorecard_scope") == "PAPER_SCORECARD_INPUT_ONLY":
        return DashboardValidationResult("BLOCKED", "paper scorecard input scope cannot be shown when scorecard input is ineligible", "HARD_TRUTH_MISSING")

    convergence = shell.get("convergence_assessment_status")
    if not isinstance(convergence, dict):
        return DashboardValidationResult("FAIL", "dashboard convergence_assessment_status missing", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("truth_role") != "dashboard_serving_truth" or convergence.get("source") != "summary.json":
        return DashboardValidationResult("BLOCKED", "convergence assessment display cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if convergence.get("display_only") is not True or convergence.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "convergence assessment display must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        convergence.get("live_order_ready")
        or convergence.get("live_order_allowed")
        or convergence.get("can_live_trade")
        or convergence.get("scale_up_allowed")
        or convergence.get("writer_input_eligible")
        or convergence.get("model_promotion_allowed")
        or convergence.get("scale_up_recommendation_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "convergence assessment attempted live, writer, promotion, or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if convergence.get("status") not in CONVERGENCE_ASSESSMENT_STATUSES:
        return DashboardValidationResult("FAIL", "convergence assessment display status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("assessment_status") not in CONVERGENCE_ASSESSMENT_STATUSES:
        return DashboardValidationResult("FAIL", "convergence assessment source status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("convergence_claim") not in CONVERGENCE_CLAIMS:
        return DashboardValidationResult("FAIL", "convergence claim display is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("convergence_claim") == "WRITER_INPUT_ELIGIBLE":
        return DashboardValidationResult("BLOCKED", "dashboard cannot display writer-input eligibility in MVP-4", "LIVE_FINAL_GUARD_FAILED")
    if convergence.get("objective_score_band") not in CONVERGENCE_SCORE_BANDS:
        return DashboardValidationResult("FAIL", "convergence objective score band is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("model_drift_status") not in CONVERGENCE_DRIFT_STATUSES:
        return DashboardValidationResult("FAIL", "convergence model drift status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("severity") not in OPERATION_STATUS_LEVELS or convergence.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "convergence assessment severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("severity") == "NORMAL" and convergence.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal convergence assessment must use green or blue status color", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("severity") == "WARNING" and convergence.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning convergence assessment must use yellow status color", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("severity") == "ERROR" and convergence.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error convergence assessment must use red status color", "SCHEMA_IDENTITY_MISMATCH")
    warning_text = str(convergence.get("operator_warning", ""))
    warning_lower = warning_text.lower()
    if "not live_ready" not in warning_lower or "live orders blocked" not in warning_lower or (
        "scale-up blocked" not in warning_lower and "scale up blocked" not in warning_lower
    ):
        return DashboardValidationResult(
            "BLOCKED",
            "convergence assessment warning must separate convergence from LIVE_READY and scale-up",
            "HARD_TRUTH_MISSING",
        )
    dependencies = convergence.get("dependency_statuses")
    if not isinstance(dependencies, list) or len(dependencies) != len(CONVERGENCE_ASSESSMENT_DEPENDENCY_FIELDS):
        return DashboardValidationResult("FAIL", "convergence dependency checklist is incomplete", "SCHEMA_IDENTITY_MISMATCH")
    pass_count = 0
    for field, item in zip(CONVERGENCE_ASSESSMENT_DEPENDENCY_FIELDS, dependencies, strict=True):
        expected_id = field.removesuffix("_status")
        if not isinstance(item, dict) or item.get("validator_id") != expected_id:
            return DashboardValidationResult("FAIL", "convergence dependency order mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("status") not in {"PASS", "FAIL", "BLOCKED", "UNTESTED", "STALE", "TIMEOUT"}:
            return DashboardValidationResult("FAIL", "convergence dependency status is unknown", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("status") == "PASS":
            pass_count += 1
    if convergence.get("required_dependency_count") != len(CONVERGENCE_ASSESSMENT_DEPENDENCY_FIELDS):
        return DashboardValidationResult("FAIL", "convergence required dependency count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("dependency_pass_count") != pass_count:
        return DashboardValidationResult("FAIL", "convergence dependency pass count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if convergence.get("forbidden_input_detected") is True:
        if convergence.get("status") != "BLOCKED" or convergence.get("severity") != "ERROR" or convergence.get("color_token") != "red":
            return DashboardValidationResult("BLOCKED", "forbidden convergence input must render as red BLOCKED", "LIVE_FINAL_GUARD_FAILED")
    if convergence.get("status") in {"LOCALLY_IMPROVING", "ROBUSTLY_IMPROVING"}:
        if pass_count != len(CONVERGENCE_ASSESSMENT_DEPENDENCY_FIELDS):
            return DashboardValidationResult("BLOCKED", "convergence cannot improve without dependency closure", "HARD_TRUTH_MISSING")
        if convergence.get("primary_blocker_code") != "LIVE_READY_MISSING":
            return DashboardValidationResult("BLOCKED", "improving convergence display must still expose live-readiness blocker", "LIVE_FINAL_GUARD_FAILED")
    elif convergence.get("convergence_claim") in {"LOCALLY_IMPROVING", "ROBUSTLY_IMPROVING"}:
        return DashboardValidationResult("BLOCKED", "convergence claim cannot be shown as improving while panel is blocked or stale", "HARD_TRUTH_MISSING")

    exploration = shell.get("exploration_policy_status")
    if not isinstance(exploration, dict):
        return DashboardValidationResult("FAIL", "dashboard exploration_policy_status missing", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("truth_role") != "dashboard_serving_truth" or exploration.get("source") != "summary.json":
        return DashboardValidationResult("BLOCKED", "exploration policy display cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if exploration.get("display_only") is not True or exploration.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "exploration policy display must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        exploration.get("live_order_ready")
        or exploration.get("live_order_allowed")
        or exploration.get("can_live_trade")
        or exploration.get("scale_up_allowed")
        or exploration.get("live_permission_created")
        or exploration.get("live_config_mutation_allowed")
        or exploration.get("writes_live_ready_snapshot")
        or exploration.get("active_snapshot_mutation_allowed")
        or exploration.get("order_submission_allowed")
        or exploration.get("exchange_account_call_allowed")
        or exploration.get("scale_up_recommendation_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "exploration policy attempted live, order, config, or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if exploration.get("status") not in EXPLORATION_POLICY_STATUSES:
        return DashboardValidationResult("FAIL", "exploration policy display status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("policy_status") not in EXPLORATION_POLICY_STATUSES:
        return DashboardValidationResult("FAIL", "exploration policy source status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("controller_state") not in EXPLORATION_POLICY_CONTROLLER_STATES:
        return DashboardValidationResult("FAIL", "exploration controller state is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("transition_decision") not in EXPLORATION_POLICY_TRANSITIONS:
        return DashboardValidationResult("FAIL", "exploration transition decision is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("recommendation_scope") not in EXPLORATION_POLICY_RECOMMENDATION_SCOPES:
        return DashboardValidationResult("FAIL", "exploration recommendation scope is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("objective_basis") not in EXPLORATION_POLICY_OBJECTIVE_BASES:
        return DashboardValidationResult("FAIL", "exploration objective basis is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("candidate_budget_status") not in EXPLORATION_POLICY_BUDGET_STATUSES:
        return DashboardValidationResult("FAIL", "exploration candidate budget status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("severity") not in OPERATION_STATUS_LEVELS or exploration.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "exploration policy severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("severity") == "NORMAL" and exploration.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal exploration policy must use green or blue status color", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("severity") == "WARNING" and exploration.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning exploration policy must use yellow status color", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("severity") == "ERROR" and exploration.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error exploration policy must use red status color", "SCHEMA_IDENTITY_MISMATCH")
    exploration_warning = str(exploration.get("operator_warning", "")).lower()
    if "not live_ready" not in exploration_warning or "live orders blocked" not in exploration_warning or (
        "scale-up blocked" not in exploration_warning and "scale up blocked" not in exploration_warning
    ):
        return DashboardValidationResult(
            "BLOCKED",
            "exploration policy warning must separate PAPER ranking from LIVE_READY and scale-up",
            "HARD_TRUTH_MISSING",
        )
    exploration_dependencies = exploration.get("dependency_statuses")
    if not isinstance(exploration_dependencies, list) or len(exploration_dependencies) != len(EXPLORATION_POLICY_DEPENDENCY_FIELDS):
        return DashboardValidationResult("FAIL", "exploration dependency checklist is incomplete", "SCHEMA_IDENTITY_MISMATCH")
    exploration_pass_count = 0
    for field, item in zip(EXPLORATION_POLICY_DEPENDENCY_FIELDS, exploration_dependencies, strict=True):
        expected_id = field.removesuffix("_status")
        if not isinstance(item, dict) or item.get("validator_id") != expected_id:
            return DashboardValidationResult("FAIL", "exploration dependency order mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("status") not in {"PASS", "FAIL", "BLOCKED", "UNTESTED", "STALE", "TIMEOUT"}:
            return DashboardValidationResult("FAIL", "exploration dependency status is unknown", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("status") == "PASS":
            exploration_pass_count += 1
    if exploration.get("required_dependency_count") != len(EXPLORATION_POLICY_DEPENDENCY_FIELDS):
        return DashboardValidationResult("FAIL", "exploration required dependency count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("dependency_pass_count") != exploration_pass_count:
        return DashboardValidationResult("FAIL", "exploration dependency pass count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if exploration.get("forbidden_input_detected") is True:
        if exploration.get("status") != "BLOCKED" or exploration.get("severity") != "ERROR" or exploration.get("color_token") != "red":
            return DashboardValidationResult("BLOCKED", "forbidden exploration input must render as red BLOCKED", "LIVE_FINAL_GUARD_FAILED")
    if exploration.get("exploitation_allowed_for_paper_ranking") is True:
        if exploration.get("status") != "PAPER_RANKING_REVIEW_ELIGIBLE":
            return DashboardValidationResult("BLOCKED", "paper exploitation cannot be allowed unless the panel is eligible", "HARD_TRUTH_MISSING")
        if exploration_pass_count != len(EXPLORATION_POLICY_DEPENDENCY_FIELDS):
            return DashboardValidationResult("BLOCKED", "paper ranking eligibility requires dependency closure", "HARD_TRUTH_MISSING")
        if exploration.get("recommendation_scope") != "PAPER_RANKING_REVIEW_ONLY":
            return DashboardValidationResult("BLOCKED", "exploration paper eligibility must stay paper-ranking-review only", "LIVE_FINAL_GUARD_FAILED")
        if exploration.get("transition_decision") != "LIMITED_EXPLOITATION_REVIEW":
            return DashboardValidationResult("BLOCKED", "paper ranking eligibility requires limited exploitation review state", "HARD_TRUTH_MISSING")
        if exploration.get("primary_blocker_code") != "LIVE_READY_MISSING":
            return DashboardValidationResult("BLOCKED", "exploration paper eligibility must still expose live-readiness blocker", "LIVE_FINAL_GUARD_FAILED")
    elif exploration.get("status") == "PAPER_RANKING_REVIEW_ELIGIBLE":
        return DashboardValidationResult("BLOCKED", "eligible exploration policy must explicitly state paper ranking permission", "HARD_TRUTH_MISSING")
    if exploration.get("status") == "PAPER_RANKING_REVIEW_ELIGIBLE" and exploration.get("candidate_budget_status") != "PASS":
        return DashboardValidationResult("BLOCKED", "eligible exploration policy requires PASS candidate budget", "HARD_TRUTH_MISSING")
    if (
        isinstance(exploration.get("candidate_count"), int)
        and isinstance(exploration.get("exploration_candidate_budget"), int)
        and exploration.get("exploration_candidate_budget", 0) > 0
        and exploration.get("candidate_count", 0) > exploration.get("exploration_candidate_budget", 0)
    ):
        if exploration.get("status") != "BLOCKED" or exploration.get("primary_blocker_code") != "OPTIMIZER_RESOURCE_BUDGET_EXCEEDED":
            return DashboardValidationResult("BLOCKED", "exploration policy candidate budget is exceeded", "OPTIMIZER_RESOURCE_BUDGET_EXCEEDED")

    parameter_narrowing = shell.get("parameter_narrowing_status")
    if not isinstance(parameter_narrowing, dict):
        return DashboardValidationResult("FAIL", "dashboard parameter_narrowing_status missing", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("truth_role") != "dashboard_serving_truth" or parameter_narrowing.get("source") != "summary.json":
        return DashboardValidationResult("BLOCKED", "parameter narrowing display cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if parameter_narrowing.get("display_only") is not True or parameter_narrowing.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "parameter narrowing display must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        parameter_narrowing.get("live_order_ready")
        or parameter_narrowing.get("live_order_allowed")
        or parameter_narrowing.get("can_live_trade")
        or parameter_narrowing.get("scale_up_allowed")
        or parameter_narrowing.get("live_permission_created")
        or parameter_narrowing.get("live_config_mutation_allowed")
        or parameter_narrowing.get("writes_live_ready_snapshot")
        or parameter_narrowing.get("active_snapshot_mutation_allowed")
        or parameter_narrowing.get("active_config_mutation_allowed")
        or parameter_narrowing.get("optimizer_winner_live_config_allowed")
        or parameter_narrowing.get("paper_winner_live_config_allowed")
        or parameter_narrowing.get("order_submission_allowed")
        or parameter_narrowing.get("exchange_account_call_allowed")
        or parameter_narrowing.get("scale_up_recommendation_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "parameter narrowing attempted live, order, config, or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if parameter_narrowing.get("status") not in PARAMETER_NARROWING_STATUSES:
        return DashboardValidationResult("FAIL", "parameter narrowing display status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("narrowing_status") not in PARAMETER_NARROWING_STATUSES:
        return DashboardValidationResult("FAIL", "parameter narrowing source status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("recommendation_scope") not in PARAMETER_NARROWING_RECOMMENDATION_SCOPES:
        return DashboardValidationResult("FAIL", "parameter narrowing recommendation scope is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("parameter_write_scope") not in PARAMETER_NARROWING_WRITE_SCOPES:
        return DashboardValidationResult("FAIL", "parameter narrowing write scope is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("objective_basis") not in PARAMETER_NARROWING_OBJECTIVE_BASES:
        return DashboardValidationResult("FAIL", "parameter narrowing objective basis is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("severity") not in OPERATION_STATUS_LEVELS or parameter_narrowing.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "parameter narrowing severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("severity") == "NORMAL" and parameter_narrowing.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal parameter narrowing must use green or blue status color", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("severity") == "WARNING" and parameter_narrowing.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning parameter narrowing must use yellow status color", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("severity") == "ERROR" and parameter_narrowing.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error parameter narrowing must use red status color", "SCHEMA_IDENTITY_MISMATCH")
    narrowing_warning = str(parameter_narrowing.get("operator_warning", "")).lower()
    if "not live_ready" not in narrowing_warning or "live orders blocked" not in narrowing_warning or (
        "scale-up blocked" not in narrowing_warning and "scale up blocked" not in narrowing_warning
    ) or "proposal-only" not in narrowing_warning:
        return DashboardValidationResult(
            "BLOCKED",
            "parameter narrowing warning must separate proposal-only review from LIVE_READY and scale-up",
            "HARD_TRUTH_MISSING",
        )
    narrowing_dependencies = parameter_narrowing.get("dependency_statuses")
    if not isinstance(narrowing_dependencies, list) or len(narrowing_dependencies) != len(PARAMETER_NARROWING_DEPENDENCY_FIELDS):
        return DashboardValidationResult("FAIL", "parameter narrowing dependency checklist is incomplete", "SCHEMA_IDENTITY_MISMATCH")
    narrowing_pass_count = 0
    for field, item in zip(PARAMETER_NARROWING_DEPENDENCY_FIELDS, narrowing_dependencies, strict=True):
        expected_id = field.removesuffix("_status")
        if not isinstance(item, dict) or item.get("validator_id") != expected_id:
            return DashboardValidationResult("FAIL", "parameter narrowing dependency order mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("status") not in {"PASS", "FAIL", "BLOCKED", "UNTESTED", "STALE", "TIMEOUT"}:
            return DashboardValidationResult("FAIL", "parameter narrowing dependency status is unknown", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("status") == "PASS":
            narrowing_pass_count += 1
    if parameter_narrowing.get("required_dependency_count") != len(PARAMETER_NARROWING_DEPENDENCY_FIELDS):
        return DashboardValidationResult("FAIL", "parameter narrowing required dependency count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("dependency_pass_count") != narrowing_pass_count:
        return DashboardValidationResult("FAIL", "parameter narrowing dependency pass count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if parameter_narrowing.get("forbidden_input_detected") is True:
        if parameter_narrowing.get("status") != "BLOCKED" or parameter_narrowing.get("severity") != "ERROR" or parameter_narrowing.get("color_token") != "red":
            return DashboardValidationResult("BLOCKED", "forbidden parameter narrowing input must render as red BLOCKED", "LIVE_FINAL_GUARD_FAILED")
    if parameter_narrowing.get("narrowing_allowed_for_paper_ranking") is True:
        if parameter_narrowing.get("status") != "PAPER_PARAMETER_REVIEW_ELIGIBLE":
            return DashboardValidationResult("BLOCKED", "parameter review cannot be allowed unless the panel is eligible", "HARD_TRUTH_MISSING")
        if narrowing_pass_count != len(PARAMETER_NARROWING_DEPENDENCY_FIELDS):
            return DashboardValidationResult("BLOCKED", "parameter review eligibility requires dependency closure", "HARD_TRUTH_MISSING")
        if parameter_narrowing.get("recommendation_scope") != "PAPER_PARAMETER_REVIEW_ONLY":
            return DashboardValidationResult("BLOCKED", "parameter review eligibility must stay paper-parameter-review only", "LIVE_FINAL_GUARD_FAILED")
        if parameter_narrowing.get("parameter_write_scope") != "PROPOSAL_ONLY":
            return DashboardValidationResult("BLOCKED", "parameter review eligibility must stay proposal-only", "LIVE_FINAL_GUARD_FAILED")
        if parameter_narrowing.get("primary_blocker_code") != "LIVE_READY_MISSING":
            return DashboardValidationResult("BLOCKED", "parameter review eligibility must still expose live-readiness blocker", "LIVE_FINAL_GUARD_FAILED")
        if parameter_narrowing.get("paper_sample_count", 0) < parameter_narrowing.get("min_required_sample_count", 0):
            return DashboardValidationResult("BLOCKED", "parameter review eligibility lacks PAPER sample coverage", "HARD_TRUTH_MISSING")
        if parameter_narrowing.get("shadow_sample_count", 0) < parameter_narrowing.get("min_required_sample_count", 0):
            return DashboardValidationResult("BLOCKED", "parameter review eligibility lacks SHADOW sample coverage", "HARD_TRUTH_MISSING")
        if parameter_narrowing.get("parameter_count_after", 0) >= parameter_narrowing.get("parameter_count_before", 0):
            return DashboardValidationResult("BLOCKED", "parameter review eligibility must narrow the parameter set", "HARD_TRUTH_MISSING")
        if parameter_narrowing.get("narrowing_pct", 0.0) > parameter_narrowing.get("max_narrowing_pct", 0.0):
            return DashboardValidationResult("BLOCKED", "parameter review eligibility exceeds max narrowing percentage", "HARD_TRUTH_MISSING")
    elif parameter_narrowing.get("status") == "PAPER_PARAMETER_REVIEW_ELIGIBLE":
        return DashboardValidationResult("BLOCKED", "eligible parameter narrowing must explicitly state paper review permission", "HARD_TRUTH_MISSING")

    decision = shell.get("decision_trace")
    if not isinstance(decision, dict):
        return DashboardValidationResult("FAIL", "dashboard decision_trace missing", "SCHEMA_IDENTITY_MISMATCH")
    if decision.get("truth_role") != "dashboard_serving_truth" or decision.get("source") not in DISPLAY_SOURCE_FILENAMES:
        return DashboardValidationResult("BLOCKED", "decision trace cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if decision.get("display_only") is not True or decision.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "decision trace must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        decision.get("live_order_ready")
        or decision.get("live_order_allowed")
        or decision.get("can_live_trade")
        or decision.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "decision trace attempted to create live, trade, or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    if decision.get("final_action") in ORDER_AFFECTING_FINAL_ACTIONS:
        return DashboardValidationResult("BLOCKED", "decision trace cannot emit order-affecting final_action", "LIVE_FINAL_GUARD_FAILED")
    if shell.get("blocking_reason") and decision.get("no_trade_reason") != shell.get("blocking_reason"):
        return DashboardValidationResult("FAIL", "decision trace no_trade_reason must match primary blocker", "SCHEMA_IDENTITY_MISMATCH")
    if shell.get("final_action") == "NO_TRADE" and not decision.get("no_trade_reason"):
        return DashboardValidationResult("BLOCKED", "NO_TRADE display must expose no_trade_reason", "HARD_TRUTH_MISSING")

    recent_events = shell.get("recent_events")
    if not isinstance(recent_events, dict):
        return DashboardValidationResult("FAIL", "dashboard recent_events missing", "SCHEMA_IDENTITY_MISMATCH")
    if recent_events.get("truth_role") != "dashboard_serving_truth" or recent_events.get("source") not in DISPLAY_SOURCE_FILENAMES:
        return DashboardValidationResult("BLOCKED", "recent events cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if recent_events.get("display_only") is not True or recent_events.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "recent events must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        recent_events.get("live_order_ready")
        or recent_events.get("live_order_allowed")
        or recent_events.get("can_live_trade")
        or recent_events.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "recent events attempted to create live, trade, or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    items = recent_events.get("items")
    if not isinstance(items, list):
        return DashboardValidationResult("FAIL", "recent event items must be a list", "SCHEMA_IDENTITY_MISMATCH")
    if shell.get("final_action") == "NO_TRADE" and not any(isinstance(item, dict) and item.get("event_type") == "NO_TRADE" for item in items):
        return DashboardValidationResult("BLOCKED", "NO_TRADE dashboard must include a recent no-trade event", "HARD_TRUTH_MISSING")
    for item in items:
        if not isinstance(item, dict):
            return DashboardValidationResult("FAIL", "recent event item must be an object", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("event_type") not in RECENT_EVENT_TYPES or item.get("severity") not in RECENT_EVENT_SEVERITIES:
            return DashboardValidationResult("FAIL", "recent event enum mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("event_type") in ORDER_AFFECTING_FINAL_ACTIONS:
            return DashboardValidationResult("BLOCKED", "recent events cannot emit order-affecting action", "LIVE_FINAL_GUARD_FAILED")
        if item.get("source") not in DISPLAY_SOURCE_FILENAMES:
            return DashboardValidationResult("BLOCKED", "recent event source must be dashboard display truth", "LIVE_FINAL_GUARD_FAILED")

    portfolio = shell.get("portfolio_snapshot")
    if not isinstance(portfolio, dict):
        return DashboardValidationResult("FAIL", "dashboard portfolio snapshot missing", "SCHEMA_IDENTITY_MISMATCH")
    if portfolio.get("truth_role") != "dashboard_serving_truth" or portfolio.get("source") not in DISPLAY_SOURCE_FILENAMES:
        return DashboardValidationResult("BLOCKED", "portfolio snapshot cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if portfolio.get("display_only") is not True or portfolio.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "portfolio snapshot must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        portfolio.get("live_order_ready")
        or portfolio.get("live_order_allowed")
        or portfolio.get("can_live_trade")
        or portfolio.get("scale_up_allowed")
    ):
        return DashboardValidationResult(
            "BLOCKED",
            "portfolio snapshot attempted to create live, trade, or scale-up permission",
            "LIVE_FINAL_GUARD_FAILED",
        )
    if portfolio.get("status") == "VERIFIED" and shell.get("mode") != "PAPER":
        return DashboardValidationResult("BLOCKED", "verified portfolio display is PAPER-only without live evidence", "LIVE_FINAL_GUARD_FAILED")
    if portfolio.get("status") == "VERIFIED":
        source_cycle_id = portfolio.get("source_runtime_cycle_id")
        source_ledger_head = portfolio.get("source_paper_ledger_head_hash")
        source_age_seconds = portfolio.get("source_snapshot_age_seconds")
        source_stale_after_seconds = portfolio.get("source_snapshot_stale_after_seconds")
        source_freshness_message = portfolio.get("source_snapshot_freshness_message")
        if source_cycle_id is not None and (not isinstance(source_cycle_id, str) or not source_cycle_id):
            return DashboardValidationResult("FAIL", "portfolio runtime cycle provenance is invalid", "SCHEMA_IDENTITY_MISMATCH")
        if source_ledger_head is not None and (not isinstance(source_ledger_head, str) or len(source_ledger_head) != 64):
            return DashboardValidationResult("FAIL", "portfolio ledger head provenance is invalid", "SCHEMA_IDENTITY_MISMATCH")
        if not isinstance(source_age_seconds, int) or source_age_seconds < 0:
            return DashboardValidationResult("FAIL", "portfolio source age is invalid", "SCHEMA_IDENTITY_MISMATCH")
        if not isinstance(source_stale_after_seconds, int) or source_stale_after_seconds <= 0:
            return DashboardValidationResult("FAIL", "portfolio source stale threshold is invalid", "SCHEMA_IDENTITY_MISMATCH")
        if source_age_seconds > source_stale_after_seconds:
            return DashboardValidationResult("BLOCKED", "verified portfolio source is stale", "LATENCY_TTL_EXPIRED")
        if not isinstance(source_freshness_message, str) or not source_freshness_message:
            return DashboardValidationResult("FAIL", "portfolio source freshness message is missing", "SCHEMA_IDENTITY_MISMATCH")
    for card_id in PORTFOLIO_CARD_IDS:
        card = portfolio.get(card_id)
        if not isinstance(card, dict):
            return DashboardValidationResult("FAIL", f"portfolio card missing: {card_id}", "SCHEMA_IDENTITY_MISMATCH")
        if card.get("card_id") != card_id:
            return DashboardValidationResult("FAIL", f"portfolio card id mismatch: {card_id}", "SCHEMA_IDENTITY_MISMATCH")
        if card.get("freshness_status") == "PASS" and portfolio.get("status") != "VERIFIED":
            return DashboardValidationResult("BLOCKED", "unverified portfolio cannot show fresh values", "HARD_TRUTH_MISSING")
        if portfolio.get("status") == "VERIFIED" and card.get("value_display") == "UNVERIFIED":
            return DashboardValidationResult("FAIL", "verified portfolio cannot show unverified card values", "SCHEMA_IDENTITY_MISMATCH")

    positions = shell.get("position_snapshot")
    if not isinstance(positions, dict):
        return DashboardValidationResult("FAIL", "dashboard position_snapshot missing", "SCHEMA_IDENTITY_MISMATCH")
    if positions.get("truth_role") != "dashboard_serving_truth" or positions.get("source") not in DISPLAY_SOURCE_FILENAMES:
        return DashboardValidationResult("BLOCKED", "position snapshot cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if positions.get("display_only") is not True or positions.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "position snapshot must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        positions.get("live_order_ready")
        or positions.get("live_order_allowed")
        or positions.get("can_live_trade")
        or positions.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "position snapshot attempted to create live, trade, or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    if positions.get("status") not in POSITION_STATUS_VALUES:
        return DashboardValidationResult("FAIL", "position snapshot status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    rows = positions.get("rows")
    if not isinstance(rows, list):
        return DashboardValidationResult("FAIL", "position rows must be a list", "SCHEMA_IDENTITY_MISMATCH")
    if positions.get("status") == "OPEN" and not rows:
        return DashboardValidationResult("FAIL", "open position snapshot must include rows", "SCHEMA_IDENTITY_MISMATCH")
    if positions.get("status") == "OPEN" and shell.get("mode") != "PAPER":
        return DashboardValidationResult("BLOCKED", "open dashboard positions are PAPER-only without live evidence", "LIVE_FINAL_GUARD_FAILED")
    for row in rows:
        expected_row_keys = {
            "symbol",
            "side",
            "quantity",
            "avg_price",
            "mark_price",
            "market_value",
            "cost_basis",
            "unrealized_pnl",
        }
        if not isinstance(row, dict) or set(row) != expected_row_keys:
            return DashboardValidationResult("FAIL", "position row shape mismatch", "SCHEMA_IDENTITY_MISMATCH")

    risk = shell.get("risk_exposure_snapshot")
    if not isinstance(risk, dict):
        return DashboardValidationResult("FAIL", "dashboard risk_exposure_snapshot missing", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("truth_role") != "dashboard_serving_truth" or risk.get("source") not in RISK_EXPOSURE_SOURCES:
        return DashboardValidationResult("BLOCKED", "risk exposure cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if risk.get("display_only") is not True or risk.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "risk exposure must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        risk.get("live_order_ready")
        or risk.get("live_order_allowed")
        or risk.get("can_live_trade")
        or risk.get("scale_up_allowed")
    ):
        return DashboardValidationResult("BLOCKED", "risk exposure attempted to create live or scale permission", "LIVE_FINAL_GUARD_FAILED")
    if risk.get("status") not in RISK_EXPOSURE_STATUSES:
        return DashboardValidationResult("FAIL", "risk exposure status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("risk_review_scope") not in RISK_REVIEW_SCOPES:
        return DashboardValidationResult("BLOCKED", "risk exposure scope must remain PAPER display-only", "LIVE_FINAL_GUARD_FAILED")
    if risk.get("exposure_data_status") not in RISK_EXPOSURE_NOTIONAL_DATA_STATUSES:
        return DashboardValidationResult("FAIL", "risk exposure notional data status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("drawdown_data_status") not in RISK_EXPOSURE_DRAWDOWN_DATA_STATUSES:
        return DashboardValidationResult("FAIL", "risk exposure data quality status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("paper_exposure_quality_status") not in PAPER_EXPOSURE_QUALITY_STATUSES:
        return DashboardValidationResult("FAIL", "paper exposure quality status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("paper_exposure_quality_source") not in PAPER_EXPOSURE_QUALITY_SOURCES:
        return DashboardValidationResult("BLOCKED", "paper exposure quality source must remain display-safe", "LIVE_FINAL_GUARD_FAILED")
    if risk.get("paper_exposure_quality_recommendation") not in PAPER_EXPOSURE_QUALITY_RECOMMENDATIONS:
        return DashboardValidationResult("FAIL", "paper exposure quality recommendation is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(risk.get("paper_exposure_quality_message"), str) or not risk.get("paper_exposure_quality_message", "").strip():
        return DashboardValidationResult("FAIL", "paper exposure quality message is missing", "SCHEMA_IDENTITY_MISMATCH")
    if (
        not isinstance(risk.get("paper_exposure_quality_next_required_evidence"), str)
        or not risk.get("paper_exposure_quality_next_required_evidence", "").strip()
    ):
        return DashboardValidationResult("FAIL", "paper exposure quality next evidence is missing", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(risk.get("paper_exposure_quality_sample_display"), str) or not risk.get("paper_exposure_quality_sample_display", "").strip():
        return DashboardValidationResult("FAIL", "paper exposure quality sample display is missing", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("paper_exposure_quality_status") in {"BLOCKED_EXPOSURE_BREACH", "BLOCKED_DRAWDOWN_BREACH", "BLOCKED_RECOVERY_REVIEW"} and risk.get("status") != "BLOCKED":
        return DashboardValidationResult("BLOCKED", "blocked paper exposure quality must block the risk panel", "LIVE_FINAL_GUARD_FAILED")
    if risk.get("paper_exposure_quality_status") == "INSUFFICIENT_EVIDENCE" and risk.get("status") == "LOW_RISK":
        return DashboardValidationResult("BLOCKED", "insufficient paper exposure evidence cannot render as overall low risk", "HARD_TRUTH_MISSING")
    if risk.get("paper_exposure_quality_status") == "UNAVAILABLE" and risk.get("status") == "LOW_RISK":
        return DashboardValidationResult("BLOCKED", "missing paper exposure quality report cannot render as overall low risk", "HARD_TRUTH_MISSING")
    if risk.get("paper_exposure_quality_status") == "PASS_PAPER_ONLY" and risk.get("paper_exposure_quality_recommendation") != "KEEP_PAPER":
        return DashboardValidationResult("FAIL", "passing paper exposure quality must recommend KEEP_PAPER only", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("scale_up_blocker_code") != "SCALE_UP_NOT_ELIGIBLE":
        return DashboardValidationResult("BLOCKED", "risk exposure must keep scale-up blocked", "LIVE_FINAL_GUARD_FAILED")
    if risk.get("severity") not in OPERATION_STATUS_LEVELS or risk.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "risk exposure severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("severity") == "NORMAL" and risk.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal risk exposure must use green or blue status color", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("severity") == "WARNING" and risk.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning risk exposure must use yellow status color", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("severity") == "ERROR" and risk.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error risk exposure must use red status color", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("status") == "LOW_RISK":
        if portfolio.get("status") != "VERIFIED" or risk.get("freshness_status") != "PASS":
            return DashboardValidationResult("BLOCKED", "low risk display requires fresh verified PAPER portfolio", "HARD_TRUTH_MISSING")
        if risk.get("open_position_count") != positions.get("open_position_count"):
            return DashboardValidationResult("FAIL", "risk exposure position count must match position snapshot", "SCHEMA_IDENTITY_MISMATCH")
        if risk.get("exposure_pct_display") in {"UNVERIFIED", "PARTIAL"} or risk.get("drawdown_pct_display") == "UNVERIFIED":
            return DashboardValidationResult("BLOCKED", "low risk display cannot hide exposure or drawdown values", "HARD_TRUTH_MISSING")
        if risk.get("exposure_data_status") != "COMPLETE" or risk.get("drawdown_data_status") != "VERIFIED":
            return DashboardValidationResult("BLOCKED", "low risk display requires complete exposure and verified drawdown data", "HARD_TRUTH_MISSING")
    if risk.get("drawdown_data_status") == "UNVERIFIED" and risk.get("drawdown_pct_display") != "UNVERIFIED":
        return DashboardValidationResult("FAIL", "unverified drawdown must not render as numeric low-risk data", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("drawdown_pct_display") == "UNVERIFIED" and risk.get("status") == "LOW_RISK":
        return DashboardValidationResult("BLOCKED", "missing drawdown hard truth cannot be low risk", "HARD_TRUTH_MISSING")
    if risk.get("exposure_data_status") == "PARTIAL" and risk.get("exposure_pct_display") != "PARTIAL":
        return DashboardValidationResult("FAIL", "partial exposure data must render as PARTIAL", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("status") in {"STALE", "UNVERIFIED"} and risk.get("severity") != "WARNING":
        return DashboardValidationResult("FAIL", "stale or unverified risk exposure must be a warning", "SCHEMA_IDENTITY_MISMATCH")
    if risk.get("status") == "BLOCKED" and risk.get("severity") != "ERROR":
        return DashboardValidationResult("FAIL", "blocked risk exposure must render as error severity", "SCHEMA_IDENTITY_MISMATCH")

    feedback = shell.get("execution_feedback_snapshot")
    if not isinstance(feedback, dict):
        return DashboardValidationResult("FAIL", "dashboard execution_feedback_snapshot missing", "SCHEMA_IDENTITY_MISMATCH")
    if feedback.get("truth_role") != "dashboard_serving_truth" or feedback.get("source") not in EXECUTION_FEEDBACK_SOURCES:
        return DashboardValidationResult("BLOCKED", "execution feedback cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if feedback.get("display_only") is not True or feedback.get("dashboard_truth_only") is not True:
        return DashboardValidationResult("BLOCKED", "execution feedback must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if (
        feedback.get("live_order_ready")
        or feedback.get("live_order_allowed")
        or feedback.get("can_live_trade")
        or feedback.get("scale_up_allowed")
        or feedback.get("promotion_eligible")
    ):
        return DashboardValidationResult("BLOCKED", "execution feedback attempted to create live, scale, or promotion permission", "LIVE_FINAL_GUARD_FAILED")
    if feedback.get("status") not in EXECUTION_FEEDBACK_STATUSES:
        return DashboardValidationResult("FAIL", "execution feedback status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if feedback.get("severity") not in OPERATION_STATUS_LEVELS or feedback.get("color_token") not in OPERATION_COLOR_TOKENS:
        return DashboardValidationResult("FAIL", "execution feedback severity or color is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if feedback.get("optimizer_ranking_action") not in EXECUTION_FEEDBACK_RANKING_ACTIONS:
        return DashboardValidationResult("FAIL", "execution feedback ranking action is unknown", "SCHEMA_IDENTITY_MISMATCH")
    for field in ("execution_quality_status", "risk_review_status", "exposure_review_status", "drawdown_review_status"):
        if feedback.get(field) not in EXECUTION_FEEDBACK_REVIEW_STATUSES:
            return DashboardValidationResult("FAIL", f"execution feedback review status is unknown: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if feedback.get("severity") == "NORMAL" and feedback.get("color_token") not in {"green", "blue"}:
        return DashboardValidationResult("FAIL", "normal execution feedback must use green or blue status color", "SCHEMA_IDENTITY_MISMATCH")
    if feedback.get("severity") == "WARNING" and feedback.get("color_token") != "yellow":
        return DashboardValidationResult("FAIL", "warning execution feedback must use yellow status color", "SCHEMA_IDENTITY_MISMATCH")
    if feedback.get("severity") == "ERROR" and feedback.get("color_token") != "red":
        return DashboardValidationResult("FAIL", "error execution feedback must use red status color", "SCHEMA_IDENTITY_MISMATCH")
    if feedback.get("status") == "READY_FOR_PAPER_RANKING_REVIEW":
        if feedback.get("feedback_eligible") is not True or feedback.get("optimizer_ranking_action") != "ALLOW_RANKING":
            return DashboardValidationResult("BLOCKED", "paper ranking review requires explicit eligible feedback and ranking action", "HARD_TRUTH_MISSING")
        for field in ("feedback_report_id", "candidate_id", "strategy_id", "parameter_hash"):
            if not feedback.get(field):
                return DashboardValidationResult("FAIL", f"paper-ranking feedback missing {field}", "SCHEMA_IDENTITY_MISMATCH")
        for field in ("execution_quality_status", "risk_review_status", "exposure_review_status", "drawdown_review_status"):
            if feedback.get(field) != "PASS":
                return DashboardValidationResult("BLOCKED", "paper-ranking feedback requires execution, risk, exposure, and drawdown PASS", "HARD_TRUTH_MISSING")
        if feedback.get("primary_blocker_code") != "LIVE_READY_MISSING":
            return DashboardValidationResult("BLOCKED", "paper-ranking feedback must still expose live-readiness blocker", "LIVE_FINAL_GUARD_FAILED")
    elif feedback.get("optimizer_ranking_action") == "ALLOW_RANKING" or feedback.get("feedback_eligible") is True:
        return DashboardValidationResult("BLOCKED", "execution feedback cannot allow ranking unless paper review status is ready", "HARD_TRUTH_MISSING")
    if feedback.get("status") == "STALE" and feedback.get("severity") != "WARNING":
        return DashboardValidationResult("FAIL", "stale execution feedback must render as a warning", "SCHEMA_IDENTITY_MISMATCH")
    if feedback.get("status") == "BLOCKED" and feedback.get("severity") not in {"WARNING", "ERROR"}:
        return DashboardValidationResult("FAIL", "blocked execution feedback must render as warning or error severity", "SCHEMA_IDENTITY_MISMATCH")

    blocker = shell.get("blocking_reason")
    if allowed_blockers is not None and blocker is not None and blocker not in allowed_blockers:
        return DashboardValidationResult("FAIL", f"unknown dashboard blocker: {blocker}", "UNKNOWN_BLOCKED")

    joined_text = " ".join(_display_text(shell)).lower()
    if any(phrase in joined_text for phrase in FORBIDDEN_DISPLAY_PHRASES):
        return DashboardValidationResult("BLOCKED", "dashboard display text contains forbidden wording", "LIVE_FINAL_GUARD_FAILED")
    if shell.get("forbidden_wording_detected") is True:
        return DashboardValidationResult("BLOCKED", "dashboard marked forbidden wording detected", "LIVE_FINAL_GUARD_FAILED")
    if shell.get("dashboard_hash") != dashboard_shell_hash(shell):
        return DashboardValidationResult("FAIL", "dashboard hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    return DashboardValidationResult("PASS", "read-only dashboard shell is display-only and fail-closed", None)


def render_dashboard_html(shell: dict[str, Any]) -> str:
    def safe_text(value: Any) -> str:
        return html.escape(str(value if value is not None else ""))

    def flag_text(name: str) -> str:
        return f"{name}=false" if shell.get(name) is False else f"{name}=BLOCKED"

    def status_class(status: Any) -> str:
        normalized = str(status or "").upper()
        if normalized in {
            "PASS",
            "VERIFIED",
            "RUNNING_SAFE_MODE",
            "BOOTSTRAP_READ_ONLY",
            "SAFE_MODE",
            "NORMAL",
            "STABLE",
            "RUNNING_NOW",
            "DISPLAY_HISTORY_STABLE",
            "VALIDATED_STABLE",
            "LOW_RISK",
            "READY_FOR_PAPER_RANKING_REVIEW",
            "LOCALLY_IMPROVING",
            "ROBUSTLY_IMPROVING",
            "PAPER_RANKING_REVIEW_ELIGIBLE",
            "PAPER_PARAMETER_REVIEW_ELIGIBLE",
            "PAPER_SCORECARD_EVIDENCE_PASS",
            "SHORT_WINDOW_EXECUTED",
            "ACTUAL_LONG_RUN_COLLECTING",
            "ACTUAL_LONG_RUN_VALIDATED",
        }:
            return "ok"
        if normalized in {
            "WARN",
            "WARNING",
            "ATTENTION",
            "BLOCKED",
            "STALE",
            "UNVERIFIED",
            "NO_TRADE",
            "TRADE_DISABLED",
            "RECONCILE_REQUIRED",
            "COLLECTING",
            "MISSING",
            "IN_PROGRESS",
            "NOT_STARTED",
            "UNTESTED",
            "ACTIVE_ANALYSIS_ONLY",
            "PARTIAL_PATCHED",
            "EVIDENCE_MISSING",
            "RECORDED_GAP",
            "OPEN_HIGH",
            "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "NOT_LOADED",
            "BLOCKED_LONG_RUN_EVIDENCE_MISSING",
            "STUB_ONLY",
            "STUB_ESTIMATE_ONLY",
            "NOT_LONG_RUN_EVIDENCE",
            "ACTUAL_LONG_RUN_MISSING",
        }:
            return "warn"
        if normalized in {"FAIL", "ERROR", "CRITICAL", "KILL_SWITCH"}:
            return "danger"
        return "neutral"

    scope_items = [
        ("Exchange", shell.get("exchange", "")),
        ("Market", shell.get("market_type", "")),
        ("Mode", shell.get("mode", "")),
        ("Session", shell.get("session_id", "")),
    ]
    scope_html = "\n      ".join(
        f"<span class=\"scope-item\"><strong>{safe_text(label)}</strong>{safe_text(value)}</span>" for label, value in scope_items
    )

    guard_items = [
        ("Live Ready", flag_text("live_order_ready")),
        ("Live Orders", flag_text("live_order_allowed")),
        ("Live Trading", flag_text("can_live_trade")),
        ("Risk Scale-Up", flag_text("scale_up_allowed")),
        ("Final Action", shell.get("final_action", "NO_TRADE")),
    ]
    guard_html = "\n      ".join(
        "<section class=\"guard\">"
        f"<h2>{safe_text(label)}</h2>"
        f"<p>{safe_text(value)}</p>"
        "</section>"
        for label, value in guard_items
    )

    def positive_int(value: Any, default: int) -> int:
        return value if isinstance(value, int) and value > 0 else default

    refresh_policy = shell.get("dashboard_refresh_policy", {}) if isinstance(shell.get("dashboard_refresh_policy"), dict) else {}
    refresh_seconds = positive_int(refresh_policy.get("auto_refresh_interval_seconds"), DASHBOARD_AUTO_REFRESH_SECONDS)
    stale_after_seconds = positive_int(refresh_policy.get("stale_after_seconds"), SOURCE_FRESHNESS_MAX_AGE_SECONDS)
    source_status_text = ", ".join(
        f"{source.get('artifact_id', 'UNKNOWN')}={source.get('freshness_status', 'STALE')}"
        for source in shell.get("source_artifacts", [])
        if isinstance(source, dict)
    )
    freshness_html = (
        "<section class=\"freshness-strip\" data-dashboard-freshness "
        f"data-generated-at=\"{safe_text(shell.get('generated_at_utc', ''))}\" "
        f"data-stale-after=\"{safe_text(stale_after_seconds)}\" "
        f"data-refresh-seconds=\"{safe_text(refresh_seconds)}\" "
        "aria-label=\"dashboard data freshness\">"
        "<div>"
        f"<span class=\"eyebrow\">{safe_text(refresh_policy.get('title', 'Dashboard Data Freshness'))}</span>"
        f"<h2><span class=\"pill ok\" data-client-freshness-pill>Fresh snapshot</span></h2>"
        "</div>"
        "<dl>"
        f"<div><dt>Updated</dt><dd>{safe_text(shell.get('generated_at_utc', 'UNKNOWN'))}</dd></div>"
        "<div><dt>Age</dt><dd data-dashboard-age>0s</dd></div>"
        f"<div><dt>Auto Refresh</dt><dd>{safe_text(refresh_seconds)}s</dd></div>"
        f"<div><dt>Sources</dt><dd>{safe_text(source_status_text or 'STALE')}</dd></div>"
        "</dl>"
        f"<p data-stale-warning>{safe_text(refresh_policy.get('next_action', 'Keep PAPER safe monitor running before trusting dashboard values.'))}</p>"
        "</section>"
    )

    operation = shell.get("operation_status", {}) if isinstance(shell.get("operation_status"), dict) else {}
    shadow_harness = shell.get("shadow_runtime_harness_status", {}) if isinstance(shell.get("shadow_runtime_harness_status"), dict) else {}
    shadow_harness_status_display = str(shadow_harness.get("status", "NOT_LOADED")).replace("_", " ").title()
    shadow_persistent = shell.get("shadow_persistent_runtime_status", {}) if isinstance(shell.get("shadow_persistent_runtime_status"), dict) else {}
    shadow_persistent_status_display = str(shadow_persistent.get("status", "NOT_LOADED")).replace("_", " ").title()
    paper_recovery_guard = shell.get("paper_runtime_recovery_guard_status", {}) if isinstance(shell.get("paper_runtime_recovery_guard_status"), dict) else {}
    paper_recovery_guard_status_display = str(paper_recovery_guard.get("status", "NOT_LOADED")).replace("_", " ").title()
    market_data = shell.get("market_data_continuity_status", {}) if isinstance(shell.get("market_data_continuity_status"), dict) else {}
    market_data_status_display = str(market_data.get("status", "NOT_LOADED")).replace("_", " ").title()
    runtime_boundary = shell.get("runtime_evidence_boundary", {}) if isinstance(shell.get("runtime_evidence_boundary"), dict) else {}
    runtime_boundary_status_display = str(runtime_boundary.get("actual_long_run_evidence_status", "MISSING")).replace("_", " ").title()
    runtime_orchestration = shell.get("shadow_runtime_orchestration_status", {}) if isinstance(shell.get("shadow_runtime_orchestration_status"), dict) else {}
    runtime_orchestration_status_display = str(runtime_orchestration.get("status", "NOT_LOADED")).replace("_", " ").title()
    operation_color = safe_text(operation.get("color_token", "yellow"))
    operation_html = (
        f"<section class=\"operation operation-{operation_color}\" aria-label=\"system operation status\">"
        "<div class=\"operation-copy\">"
        "<span class=\"eyebrow\">System Status</span>"
        f"<h2>{safe_text(operation.get('label', 'Needs attention'))}</h2>"
        f"<p>{safe_text(operation.get('message', 'Dashboard source needs attention'))}</p>"
        f"<p>{safe_text(operation.get('operator_meaning', 'This status is dashboard display truth only.'))}</p>"
        f"<p class=\"recovery\"><strong>Recovery:</strong> {safe_text(operation.get('recovery_hint', 'Rerun PAPER if dashboard sources are stale.'))}</p>"
        "</div>"
        "<dl>"
        f"<div><dt>Heartbeat</dt><dd class=\"pill {status_class(operation.get('heartbeat_status'))}\">{safe_text(operation.get('heartbeat_status', 'STALE'))}</dd></div>"
        f"<div><dt>Engine</dt><dd>{safe_text(operation.get('engine_state', 'UNKNOWN'))}</dd></div>"
        f"<div><dt>Launcher mode</dt><dd>{safe_text(operation.get('launcher_execution_mode', 'SAFE_BOOT_OR_EXPLICIT_MONITOR'))}</dd></div>"
        f"<div><dt>Runtime presence</dt><dd>{safe_text(operation.get('runtime_presence', 'DASHBOARD_HEARTBEAT_ONLY'))}</dd></div>"
        f"<div><dt>Market data</dt><dd class=\"pill {status_class(market_data.get('status'))}\">{safe_text(market_data_status_display)}</dd></div>"
        f"<div><dt>PAPER/SHADOW check</dt><dd class=\"pill {status_class(shadow_harness.get('status'))}\">{safe_text(shadow_harness_status_display)}</dd></div>"
        f"<div><dt>Persistent runtime</dt><dd class=\"pill {status_class(shadow_persistent.get('status'))}\">{safe_text(shadow_persistent_status_display)}</dd></div>"
        f"<div><dt>PAPER recovery</dt><dd class=\"pill {status_class(paper_recovery_guard.get('status'))}\">{safe_text(paper_recovery_guard_status_display)}</dd></div>"
        f"<div><dt>Source pairing</dt><dd class=\"pill {status_class(runtime_orchestration.get('status'))}\">{safe_text(runtime_orchestration_status_display)}</dd></div>"
        f"<div><dt>Actual long-run evidence</dt><dd class=\"pill {status_class(runtime_boundary.get('status'))}\">{safe_text(runtime_boundary_status_display)}</dd></div>"
        f"<div><dt>Live orders</dt><dd class=\"pill safe-lock\">blocked</dd></div>"
        "</dl>"
        "</section>"
    )

    operator_action = shell.get("operator_action_summary", {}) if isinstance(shell.get("operator_action_summary"), dict) else {}
    operator_color = safe_text(operator_action.get("color_token", "yellow"))
    operator_status_display = str(operator_action.get("status", "ACTION_REQUIRED")).replace("_", " ").title()
    operator_html = (
        f"<section class=\"operator-action operator-action-{operator_color}\" aria-label=\"operator next action\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">What To Do Now</span>"
        f"<h2>{safe_text(operator_action.get('primary_action_label', 'Resolve dashboard blocker'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(operator_action.get('status'))}\">{safe_text(operator_status_display)}</span></p>"
        "</div>"
        "<section class=\"decision-grid\">"
        "<div><strong>Next Action</strong>"
        f"<p>{safe_text(operator_action.get('next_operator_action', 'Resolve visible blocker and rerun PAPER.'))}</p></div>"
        "<div><strong>Primary Blocker</strong>"
        f"<p>{safe_text(operator_action.get('one_line_blocker', 'LIVE_READY_MISSING: live orders remain blocked.'))}</p></div>"
        "<div><strong>Workflow Step</strong>"
        f"<p>{safe_text(operator_action.get('workflow_step', 'INSPECT_DASHBOARD')).replace('_', ' ').title()}</p></div>"
        "<div><strong>Safety</strong>"
        "<p><span class=\"pill safe-lock\">PAPER review only</span><br><span class=\"pill safe-lock\">LIVE blocked</span></p></div>"
        "</section>"
        "<small>Emergency controls stay visible, but this dashboard has no order buttons, no forms, and no live permission.</small>"
        "</section>"
    )

    reconciliation = shell.get("reconciliation_recovery_summary", {}) if isinstance(shell.get("reconciliation_recovery_summary"), dict) else {}
    reconciliation_color = safe_text(reconciliation.get("color_token", "yellow"))
    reconciliation_status_display = str(reconciliation.get("status", "NOT_LOADED")).replace("_", " ").title()
    reconciliation_html = (
        f"<section class=\"reconciliation reconciliation-{reconciliation_color}\" aria-label=\"ledger reconciliation and recovery\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Ledger Safety</span>"
        f"<h2>{safe_text(reconciliation.get('title', 'Ledger & Reconciliation'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(reconciliation.get('status'))}\">{safe_text(reconciliation_status_display)}</span></p>"
        "</div>"
        f"<p>{safe_text(reconciliation.get('message', 'Ledger and recovery evidence needs review.'))}</p>"
        "<section class=\"decision-grid\">"
        "<div><strong>Reconciliation</strong>"
        f"<p>report={safe_text(reconciliation.get('reconciliation_status', 'NOT_LOADED'))}<br>validator={safe_text(reconciliation.get('reconciliation_validation_status', 'UNTESTED'))}<br>mismatches={safe_text(reconciliation.get('mismatch_count', 0))}</p></div>"
        "<div><strong>Restart Recovery</strong>"
        f"<p>report={safe_text(reconciliation.get('restart_recovery_status', 'NOT_LOADED'))}<br>validator={safe_text(reconciliation.get('restart_recovery_validation_status', 'UNTESTED'))}</p></div>"
        "<div><strong>Ledger / Writer</strong>"
        f"<p>ledger={safe_text(reconciliation.get('ledger_state', 'NOT_LOADED'))}<br>single-writer={safe_text(reconciliation.get('single_writer_state', 'NOT_LOADED'))}<br>idempotency={safe_text(reconciliation.get('idempotency_state', 'NOT_LOADED'))}</p></div>"
        "<div><strong>Live Boundary</strong>"
        "<p><span class=\"pill safe-lock\">live_order_allowed=false</span><br><span class=\"pill safe-lock\">can_live_trade=false</span><br><span class=\"pill safe-lock\">scale_up_allowed=false</span></p></div>"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(reconciliation.get('next_operator_action', 'Refresh PAPER reconciliation before review.'))}</p>"
        f"<small>Blocker={safe_text(reconciliation.get('one_line_blocker', 'RECONCILIATION_REQUIRED'))}. Source={safe_text(reconciliation.get('source', 'summary.json'))}. Display-only ledger safety; this panel cannot approve or place orders.</small>"
        "</section>"
    )

    workflow = shell.get("operator_workflow_summary", {}) if isinstance(shell.get("operator_workflow_summary"), dict) else {}
    workflow_color = safe_text(workflow.get("color_token", "yellow"))
    workflow_status_display = str(workflow.get("status", "ACTION_REQUIRED")).replace("_", " ").title()
    workflow_steps = workflow.get("steps", []) if isinstance(workflow.get("steps"), list) else []
    workflow_step_html = "\n".join(
        "<section class=\"workflow-step\">"
        f"<h3>{safe_text(step.get('label', 'Step'))}</h3>"
        f"<p><span class=\"pill {status_class(step.get('status'))}\">{safe_text(step.get('status', 'WAITING'))}</span></p>"
        f"<small>{safe_text(step.get('detail', 'Display-only workflow step'))}</small>"
        "</section>"
        for step in workflow_steps
        if isinstance(step, dict)
    )
    workflow_html = (
        f"<section class=\"workflow workflow-{workflow_color}\" aria-label=\"operator workflow\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Operator Workflow</span>"
        f"<h2>{safe_text(workflow.get('title', 'Operator Workflow'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(workflow.get('status'))}\">{safe_text(workflow_status_display)}</span></p>"
        "</div>"
        f"<p>{safe_text(workflow.get('summary', 'Follow the PAPER review workflow.'))}</p>"
        f"<section class=\"workflow-grid\">{workflow_step_html}</section>"
        f"<small>Current step={safe_text(workflow.get('current_step', 'INSPECT_DASHBOARD'))}. LIVE review is blocked until external evidence exists; this workflow cannot place or prepare orders.</small>"
        "</section>"
    )

    long_run = shell.get("long_run_operator_summary", {}) if isinstance(shell.get("long_run_operator_summary"), dict) else {}
    long_run_color = safe_text(long_run.get("color_token", "yellow"))
    long_run_raw_status = str(long_run.get("status", "ATTENTION"))
    long_run_status_display = (
        "Display History Stable"
        if long_run_raw_status == "DISPLAY_HISTORY_STABLE"
        else "Actual Long-Run Validated"
        if long_run_raw_status == "VALIDATED_STABLE"
        else long_run_raw_status.replace("_", " ").title()
    )
    long_run_html = (
        f"<section class=\"longrun longrun-{long_run_color}\" aria-label=\"long-run operation summary\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Long-Run Operation</span>"
        f"<h2>{safe_text(long_run.get('title', 'Long-Run Operation'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(long_run.get('status'))}\">{safe_text(long_run_status_display)}</span></p>"
        "</div>"
        f"<p>{safe_text(long_run.get('summary', 'Long-run operating status is collecting.'))}</p>"
        "<section class=\"decision-grid\">"
        "<div><strong>History Samples</strong>"
        f"<p>stable={safe_text(long_run.get('stable_sample_rate_display', '0/0 (0%)'))}<br>degraded={safe_text(long_run.get('degraded_sample_rate_display', '0/0 (0%)'))}<br>stale={safe_text(long_run.get('stale_sample_rate_display', '0/0 (0%)'))}</p></div>"
        "<div><strong>Observed Span</strong>"
        f"<p>{safe_text(long_run.get('observed_span_seconds', 0))}s / {safe_text(long_run.get('min_validated_span_seconds', DEFAULT_MIN_VALIDATED_SPAN_SECONDS))}s<br>{safe_text(long_run.get('span_validation_status', 'INSUFFICIENT_SPAN')).replace('_', ' ').title()}</p></div>"
        "<div><strong>Latency / Refresh</strong>"
        f"<p>latency={safe_text(long_run.get('latency_trend_status', 'UNTESTED'))}, refresh={safe_text(long_run.get('dashboard_refresh_delay_status', 'UNTESTED'))}</p></div>"
        "<div><strong>Resources / Retry</strong>"
        f"<p>resources={safe_text(long_run.get('resource_pressure_status', 'UNTESTED'))}, retry={safe_text(long_run.get('retry_trend_status', 'UNTESTED'))}</p></div>"
        "<div><strong>Live Safety</strong>"
        "<p><span class=\"pill safe-lock\">live_order_allowed=false</span><br><span class=\"pill safe-lock\">scale_up_allowed=false</span></p></div>"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(long_run.get('next_action', 'Continue PAPER monitoring.'))}</p>"
        f"<small>Source={safe_text(long_run.get('source', 'heartbeat.json'))} | samples={safe_text(long_run.get('history_sample_count', 0))} | blocker={safe_text(long_run.get('primary_blocker_code', 'LIVE_READY_MISSING'))}. Display-only operating summary; execution, ledger, and exchange truth remain separate.</small>"
        "</section>"
    )

    market_data_color = safe_text(market_data.get("color_token", "yellow"))
    market_data_html = (
        f"<section class=\"market-data market-data-{market_data_color}\" aria-label=\"market data continuity status\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Market Data</span>"
        f"<h2>{safe_text(market_data.get('title', 'Market Data Continuity'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(market_data.get('status'))}\">{safe_text(market_data_status_display)}</span></p>"
        "</div>"
        f"<p>{safe_text(market_data.get('one_line_summary', 'Market-data continuity is not loaded.'))}</p>"
        "<section class=\"decision-grid\">"
        "<div><strong>Attempts</strong>"
        f"<p>pass={safe_text(market_data.get('pass_attempt_count', 0))}/{safe_text(market_data.get('total_attempt_count', 0))}<br>blocked={safe_text(market_data.get('blocked_attempt_count', 0))}</p></div>"
        "<div><strong>Latest Data</strong>"
        f"<p><span class=\"pill {status_class(market_data.get('latest_attempt_status'))}\">{safe_text(market_data.get('latest_attempt_status', 'BLOCKED'))}</span><br>symbol={safe_text(market_data.get('symbol', 'UNKNOWN'))}</p></div>"
        "<div><strong>Data Quality Blocks</strong>"
        f"<p>duplicate={safe_text(market_data.get('duplicate_latest_event_block_count', 0))}<br>non-advancing={safe_text(market_data.get('non_advancing_block_count', 0))}<br>unavailable={safe_text(market_data.get('data_unavailable_block_count', 0))}</p></div>"
        "<div><strong>Evidence Boundary</strong>"
        "<p><span class=\"pill safe-lock\">PAPER data only</span><br><span class=\"pill safe-lock\">not LIVE_READY</span><br><span class=\"pill safe-lock\">live_order_allowed=false</span></p></div>"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(market_data.get('next_operator_action', 'Collect PAPER public market-data continuity.'))}</p>"
        f"<small>Source={safe_text(market_data.get('source', 'NOT_LOADED'))} | window={safe_text(market_data.get('history_window_label', 'NOT_LOADED'))} | blocker={safe_text(market_data.get('primary_blocker_code', 'DATA_UNAVAILABLE'))}. Display-only market-data status; execution, ledger, exchange, optimizer, and live-readiness truth remain separate.</small>"
        "</section>"
    )

    paper_recovery_guard_color = safe_text(paper_recovery_guard.get("color_token", "yellow"))
    paper_recovery_guard_html = (
        f"<section class=\"paper-recovery paper-recovery-{paper_recovery_guard_color}\" aria-label=\"paper runtime recovery guard\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">PAPER Runtime Recovery</span>"
        f"<h2>{safe_text(paper_recovery_guard.get('title', 'PAPER Runtime Recovery Guard'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(paper_recovery_guard.get('status'))}\">{safe_text(paper_recovery_guard_status_display)}</span></p>"
        "</div>"
        f"<p>{safe_text(paper_recovery_guard.get('one_line_summary', 'PAPER runtime recovery guard is not loaded.'))}</p>"
        "<section class=\"decision-grid\">"
        "<div><strong>Latest Cycle</strong>"
        f"<p><span class=\"pill {status_class(paper_recovery_guard.get('latest_cycle_status'))}\">{safe_text(paper_recovery_guard.get('latest_cycle_status', 'MISSING'))}</span><br>recoverable={safe_text(paper_recovery_guard.get('latest_cycle_recoverable', False))}</p></div>"
        "<div><strong>Partial Write Check</strong>"
        f"<p>market JSONL={safe_text(paper_recovery_guard.get('canonical_jsonl_checked_count', 0))}<br>ledger JSONL={safe_text(paper_recovery_guard.get('ledger_jsonl_checked_count', 0))}<br>quarantined={safe_text(paper_recovery_guard.get('corrupted_jsonl_quarantined_count', 0))}/{safe_text(paper_recovery_guard.get('corrupted_ledger_jsonl_quarantined_count', 0))}<br>invalid ledger={safe_text(paper_recovery_guard.get('ledger_jsonl_invalid_count', 0))}<br>tmp files={safe_text(paper_recovery_guard.get('orphan_tmp_file_count', 0))}</p></div>"
        "<div><strong>Resume Decision</strong>"
        f"<p>{safe_text(paper_recovery_guard.get('resume_action', 'SAFE_MODE_RECONCILE'))}<br>resume_allowed={safe_text(paper_recovery_guard.get('paper_runtime_resume_allowed', False))}</p></div>"
        "<div><strong>Evidence Boundary</strong>"
        "<p><span class=\"pill safe-lock\">not LIVE_READY</span><br><span class=\"pill safe-lock\">not long-run evidence</span><br><span class=\"pill safe-lock\">scale-up blocked</span></p></div>"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(paper_recovery_guard.get('next_operator_action', 'Run PAPER recovery guard before review.'))}</p>"
        f"<small>Source={safe_text(paper_recovery_guard.get('source', 'NOT_LOADED'))} | Guard={safe_text(paper_recovery_guard.get('guard_id', 'NOT_LOADED'))} | Loop={safe_text(paper_recovery_guard.get('loop_id', 'NOT_LOADED'))} | Blocker={safe_text(paper_recovery_guard.get('primary_blocker_code', 'RECONCILIATION_REQUIRED'))}. Display-only recovery status; it cannot approve live orders, promotion, long-run evidence, or risk scale-up.</small>"
        "</section>"
    )

    runtime_boundary_color = safe_text(runtime_boundary.get("color_token", "yellow"))
    runtime_requirement_cards = []
    runtime_requirements = (
        runtime_boundary.get("evidence_requirements", [])
        if isinstance(runtime_boundary.get("evidence_requirements"), list)
        else []
    )
    for requirement in runtime_requirements:
        if not isinstance(requirement, dict):
            continue
        requirement_status = safe_text(requirement.get("status", "MISSING"))
        runtime_requirement_cards.append(
            "<div class=\"evidence-requirement\">"
            f"<strong>{safe_text(requirement.get('label', 'Evidence requirement'))}</strong>"
            f"<p><span class=\"pill {status_class(requirement_status)}\">{requirement_status.replace('_', ' ').title()}</span></p>"
            f"<p>{safe_text(requirement.get('detail', 'Long-run evidence requirement is missing.'))}</p>"
            f"<small>Source={safe_text(requirement.get('source', 'NOT_LOADED'))}. Next: {safe_text(requirement.get('next_operator_action', 'Continue PAPER monitoring.'))}</small>"
            "</div>"
        )
    runtime_requirement_html = "\n".join(runtime_requirement_cards)
    runtime_boundary_html = (
        f"<section class=\"runtime-boundary runtime-boundary-{runtime_boundary_color}\" aria-label=\"runtime evidence boundary\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Runtime Evidence Boundary</span>"
        f"<h2>{safe_text(runtime_boundary.get('title', 'Runtime Evidence Boundary'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(runtime_boundary.get('status'))}\">{safe_text(str(runtime_boundary.get('status', 'ACTUAL_LONG_RUN_MISSING')).replace('_', ' ').title())}</span></p>"
        "</div>"
        f"<p>{safe_text(runtime_boundary.get('one_line_summary', 'Actual long-run runtime evidence is missing.'))}</p>"
        "<section class=\"decision-grid\">"
        "<div><strong>Actual Long-Run</strong>"
        f"<p><span class=\"pill {status_class(runtime_boundary.get('actual_long_run_evidence_status'))}\">{safe_text(runtime_boundary_status_display)}</span><br>source={safe_text(runtime_boundary.get('source', 'heartbeat.json'))}</p></div>"
        "<div><strong>Short-Window Check</strong>"
        f"<p>{safe_text(runtime_boundary.get('short_window_evidence_status', 'NOT_LOADED')).replace('_', ' ').title()}<br>not LIVE_READY evidence</p></div>"
        "<div><strong>Persistent Stub</strong>"
        f"<p>{safe_text(runtime_boundary.get('stub_runtime_evidence_status', 'NOT_LOADED')).replace('_', ' ').title()}<br>{safe_text(runtime_boundary.get('stub_boundary_message', 'Stub evidence cannot replace actual runtime.'))}</p></div>"
        "<div><strong>Live Review</strong>"
        "<p><span class=\"pill safe-lock\">live_review_evidence_eligible=false</span><br><span class=\"pill safe-lock\">live_order_allowed=false</span></p></div>"
        "</section>"
        "<div class=\"evidence-requirement-head\">"
        "<strong>Long-Run Evidence Requirements</strong>"
        f"<span>{safe_text(runtime_boundary.get('evidence_requirement_summary', 'Long-run evidence requirements are not loaded.'))}</span>"
        "</div>"
        f"<section class=\"evidence-requirement-grid\" aria-label=\"long-run evidence requirements\">{runtime_requirement_html}</section>"
        f"<p class=\"next\">Next: {safe_text(runtime_boundary.get('next_operator_action', 'Collect real long-run PAPER/SHADOW evidence.'))}</p>"
        f"<small>Blocker={safe_text(runtime_boundary.get('primary_blocker_code', 'ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING'))}. This panel separates actual long-run evidence from short-window checks and stub estimates; it is dashboard display truth only.</small>"
        "</section>"
    )

    runtime_orchestration_color = safe_text(runtime_orchestration.get("color_token", "yellow"))
    runtime_orchestration_html = (
        f"<section class=\"runtime-boundary runtime-orchestration runtime-boundary-{runtime_orchestration_color}\" aria-label=\"runtime orchestration guard\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Runtime Orchestration</span>"
        f"<h2>{safe_text(runtime_orchestration.get('title', 'Runtime Orchestration Guard'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(runtime_orchestration.get('status'))}\">{safe_text(runtime_orchestration_status_display)}</span></p>"
        "</div>"
        f"<p>{safe_text(runtime_orchestration.get('one_line_summary', 'Runtime orchestration guard is not loaded.'))}</p>"
        "<section class=\"decision-grid\">"
        "<div><strong>Source Pairing</strong>"
        f"<p>pairing={safe_text(runtime_orchestration.get('source_runtime_hash_pairing_verified', False))}<br>sources={safe_text(runtime_orchestration.get('source_binding_count', 0))}<br>validation={safe_text(runtime_orchestration.get('source_validation_status', 'NOT_LOADED'))}</p></div>"
        "<div><strong>Observed Long-Run</strong>"
        f"<p>runtime={safe_text(runtime_orchestration.get('observed_actual_runtime_seconds', 0))}s<br>cycles={safe_text(runtime_orchestration.get('observed_actual_cycle_count', 0))}<br>windows={safe_text(runtime_orchestration.get('observed_evidence_window_count', 0))}</p></div>"
        "<div><strong>Evidence Role</strong>"
        f"<p>{safe_text(runtime_orchestration.get('runtime_evidence_role', 'ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN'))}<br>{safe_text(runtime_orchestration.get('orchestration_decision', 'BLOCK_LONG_RUN_EVIDENCE'))}</p></div>"
        "<div><strong>Optimizer / Live</strong>"
        f"<p>optimizer ranking {safe_text(runtime_orchestration.get('optimizer_ranking_action', 'BLOCK_RANKING')).replace('_', ' ').lower()}<br><span class=\"pill safe-lock\">scorecard_input_eligible=false</span><br><span class=\"pill safe-lock\">live_order_allowed=false</span></p></div>"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(runtime_orchestration.get('next_operator_action', 'Generate runtime orchestration guard and keep LIVE blocked.'))}</p>"
        f"<small>Source={safe_text(runtime_orchestration.get('source', 'NOT_LOADED'))} | blocker={safe_text(runtime_orchestration.get('primary_blocker_code', 'ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING'))}. Display-only source pairing guard; it cannot create long-run evidence, LIVE_READY, optimizer ranking, or orders.</small>"
        "</section>"
    )

    shadow_harness_color = safe_text(shadow_harness.get("color_token", "yellow"))
    shadow_harness_html = (
        f"<section class=\"shadow-harness shadow-harness-{shadow_harness_color}\" aria-label=\"paper shadow runtime harness status\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">PAPER/SHADOW Check</span>"
        f"<h2>{safe_text(shadow_harness.get('title', 'PAPER / SHADOW Runtime Harness'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(shadow_harness.get('status'))}\">{safe_text(shadow_harness_status_display)}</span></p>"
        "</div>"
        f"<p>{safe_text(shadow_harness.get('one_line_summary', 'No runtime harness report is loaded.'))}</p>"
        "<section class=\"decision-grid\">"
        "<div><strong>Cycles</strong>"
        f"<p>completed={safe_text(shadow_harness.get('completed_cycle_count', 0))}/{safe_text(shadow_harness.get('requested_cycle_count', 0))}<br>observations={safe_text(shadow_harness.get('observation_count', 0))}<br>heartbeats={safe_text(shadow_harness.get('heartbeat_count', 0))}</p></div>"
        "<div><strong>Evidence Role</strong>"
        f"<p>{safe_text(shadow_harness.get('runtime_evidence_role', 'NOT_LONG_RUN_EVIDENCE'))}<br>{safe_text(shadow_harness.get('runtime_evidence_status', 'NOT_LOADED'))}</p></div>"
        "<div><strong>Long-Run Minimum</strong>"
        f"<p>runtime={safe_text(shadow_harness.get('measured_runtime_seconds', 0))}/{safe_text(shadow_harness.get('minimum_runtime_window_seconds', 0))}s<br><span class=\"pill safe-lock\">long_run_evidence_eligible=false</span></p></div>"
        "<div><strong>Optimizer / Live</strong>"
        f"<p>{safe_text(shadow_harness.get('optimizer_input_role', 'BLOCKER_ONLY_NOT_RANKING_INPUT'))}<br><span class=\"pill safe-lock\">live_order_allowed=false</span></p></div>"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(shadow_harness.get('next_operator_action', 'Run the non-live PAPER/SHADOW harness.'))}</p>"
        f"<small>Source={safe_text(shadow_harness.get('source', 'NOT_LOADED'))} | blocker={safe_text(shadow_harness.get('primary_blocker_code', 'ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING'))}. Display-only harness summary; not execution truth and not LIVE_READY evidence.</small>"
        "</section>"
    )

    shadow_persistent_color = safe_text(shadow_persistent.get("color_token", "yellow"))
    shadow_persistent_html = (
        f"<section class=\"shadow-harness shadow-persistent-runtime shadow-harness-{shadow_persistent_color}\" aria-label=\"paper shadow persistent runtime status\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Persistent Runtime Evidence</span>"
        f"<h2>{safe_text(shadow_persistent.get('title', 'PAPER / SHADOW Persistent Runtime'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(shadow_persistent.get('status'))}\">{safe_text(shadow_persistent_status_display)}</span></p>"
        "</div>"
        f"<p>{safe_text(shadow_persistent.get('one_line_summary', 'No persistent runtime report is loaded.'))}</p>"
        "<section class=\"decision-grid\">"
        "<div><strong>Duration Source</strong>"
        f"<p>{safe_text(shadow_persistent.get('runtime_duration_evidence_source', 'NOT_LOADED'))}<br>{safe_text(shadow_persistent.get('duration_evidence_role', 'NOT_LONG_RUN_EVIDENCE'))}</p></div>"
        "<div><strong>Estimated vs Observed</strong>"
        f"<p>estimated={safe_text(shadow_persistent.get('estimated_runtime_seconds', 0))}s<br>observed={safe_text(shadow_persistent.get('observed_runtime_seconds', 0))}s</p></div>"
        "<div><strong>Cycles / Heartbeat</strong>"
        f"<p>completed={safe_text(shadow_persistent.get('completed_cycle_count', 0))}/{safe_text(shadow_persistent.get('requested_cycle_count', 0))}<br>heartbeats={safe_text(shadow_persistent.get('heartbeat_count', 0))}<br>interval={safe_text(shadow_persistent.get('heartbeat_interval_seconds', 0))}s</p></div>"
        "<div><strong>Live / Optimizer Boundary</strong>"
        f"<p>{safe_text(shadow_persistent.get('optimizer_input_role', 'NOT_LOADED'))}<br><span class=\"pill safe-lock\">long_run_evidence_eligible=false</span><br><span class=\"pill safe-lock\">live_order_allowed=false</span></p></div>"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(shadow_persistent.get('next_operator_action', 'Collect actual long-run PAPER/SHADOW evidence separately.'))}</p>"
        f"<small>Source={safe_text(shadow_persistent.get('source', 'NOT_LOADED'))} | blocker={safe_text(shadow_persistent.get('primary_blocker_code', 'ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING'))}. Estimated runtime is a stub calculation only; observed runtime remains 0s and is not LIVE_READY evidence.</small>"
        "</section>"
    )

    risk = shell.get("risk_exposure_snapshot", {}) if isinstance(shell.get("risk_exposure_snapshot"), dict) else {}
    risk_color = safe_text(risk.get("color_token", "yellow"))
    risk_status_display = str(risk.get("status", "UNVERIFIED")).replace("_", " ").title()
    risk_html = (
        f"<section class=\"risk risk-{risk_color}\" aria-label=\"risk exposure snapshot\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Risk Exposure</span>"
        f"<h2>{safe_text(risk.get('title', 'Risk Exposure'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(risk.get('status'))}\">{safe_text(risk_status_display)}</span></p>"
        "</div>"
        "<section class=\"decision-grid\">"
        "<div><strong>Equity</strong>"
        f"<p>{safe_text(risk.get('equity_display', 'UNVERIFIED'))}</p></div>"
        "<div><strong>Exposure</strong>"
        f"<p>{safe_text(risk.get('exposure_notional_display', 'UNVERIFIED'))} | {safe_text(risk.get('exposure_pct_display', 'UNVERIFIED'))}</p></div>"
        "<div><strong>Drawdown</strong>"
        f"<p>{safe_text(risk.get('drawdown_pct_display', 'UNVERIFIED'))}</p></div>"
        "<div><strong>Scale-Up</strong>"
        f"<p><span class=\"pill safe-lock\">scale_up_allowed=false</span></p></div>"
        "<div><strong>Data Quality</strong>"
        f"<p>exposure={safe_text(risk.get('exposure_data_status', 'UNVERIFIED'))}<br>drawdown={safe_text(risk.get('drawdown_data_status', 'UNVERIFIED'))}</p></div>"
        "<div><strong>Paper Quality</strong>"
        f"<p><span class=\"pill {status_class(risk.get('paper_exposure_quality_status'))}\">{safe_text(risk.get('paper_exposure_quality_status', 'UNAVAILABLE'))}</span><br>samples={safe_text(risk.get('paper_exposure_quality_sample_display', '0/0'))}</p></div>"
        "<div><strong>Risk Recommendation</strong>"
        f"<p>{safe_text(risk.get('paper_exposure_quality_recommendation', 'NO_SCALE_UP'))}<br>{safe_text(risk.get('paper_exposure_quality_source', 'NOT_LOADED'))}</p></div>"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(risk.get('next_action', 'Run PAPER with a verified paper ledger before review.'))}</p>"
        f"<small>Positions={safe_text(risk.get('open_position_count', 0))} | Exposure cap={safe_text(risk.get('exposure_review_cap_pct_display', 'UNVERIFIED'))} | Drawdown cap={safe_text(risk.get('drawdown_review_cap_pct_display', 'UNVERIFIED'))}. {safe_text(risk.get('primary_blocker_message', 'Display-only risk review; live orders remain blocked.'))} Paper quality: {safe_text(risk.get('paper_exposure_quality_message', 'No paper exposure quality report is loaded.'))} Next evidence: {safe_text(risk.get('paper_exposure_quality_next_required_evidence', 'Generate a scoped paper exposure quality report.'))}</small>"
        "</section>"
    )

    feedback = shell.get("execution_feedback_snapshot", {}) if isinstance(shell.get("execution_feedback_snapshot"), dict) else {}
    feedback_color = safe_text(feedback.get("color_token", "yellow"))
    feedback_status_display = str(feedback.get("status", "COLLECTING")).replace("_", " ").title()
    feedback_html = (
        f"<section class=\"feedback feedback-{feedback_color}\" aria-label=\"execution feedback snapshot\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Execution Feedback</span>"
        f"<h2>{safe_text(feedback.get('title', 'Execution Feedback'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(feedback.get('status'))}\">{safe_text(feedback_status_display)}</span></p>"
        "</div>"
        "<section class=\"decision-grid\">"
        "<div><strong>Execution Quality</strong>"
        f"<p><span class=\"pill {status_class(feedback.get('execution_quality_status'))}\">{safe_text(feedback.get('execution_quality_status', 'UNTESTED'))}</span></p></div>"
        "<div><strong>Risk Review</strong>"
        f"<p>risk={safe_text(feedback.get('risk_review_status', 'UNTESTED'))}, exposure={safe_text(feedback.get('exposure_review_status', 'UNTESTED'))}, drawdown={safe_text(feedback.get('drawdown_review_status', 'UNTESTED'))}</p></div>"
        "<div><strong>Net EV Drift</strong>"
        f"<p>{safe_text(feedback.get('net_ev_deviation_display', 'UNVERIFIED'))}</p></div>"
        "<div><strong>Cost Drift</strong>"
        f"<p>slippage={safe_text(feedback.get('slippage_deviation_display', 'UNVERIFIED'))}, fee={safe_text(feedback.get('fee_deviation_display', 'UNVERIFIED'))}, impact={safe_text(feedback.get('impact_deviation_display', 'UNVERIFIED'))}</p></div>"
        "<div><strong>Optimizer Ranking</strong>"
        f"<p><span class=\"pill {status_class(feedback.get('optimizer_ranking_action'))}\">{safe_text(feedback.get('optimizer_ranking_action', 'BLOCK_RANKING'))}</span></p></div>"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(feedback.get('next_action', 'Collect expected-vs-realized execution feedback before ranking.'))}</p>"
        f"<small>Candidate={safe_text(feedback.get('candidate_id') or 'none')} | Strategy={safe_text(feedback.get('strategy_id') or 'none')} | Blocker={safe_text(feedback.get('primary_blocker_code') or 'none')}. Execution feedback is PAPER/SHADOW analysis-only; live and scale-up remain blocked.</small>"
        "</section>"
    )

    stability = shell.get("stability_trends", {}) if isinstance(shell.get("stability_trends"), dict) else {}
    stability_color = safe_text(stability.get("color_token", "yellow"))
    stability_metrics = stability.get("metrics", []) if isinstance(stability.get("metrics"), list) else []
    stability_metric_html = "\n".join(
        "<section class=\"stability-metric\">"
        f"<h3>{safe_text(metric.get('label', 'Metric'))}</h3>"
        f"<p class=\"metric-value\"><span class=\"pill {status_class(metric.get('status'))}\">{safe_text(metric.get('value_display', metric.get('status', 'UNTESTED')))}</span></p>"
        f"<small>{safe_text(metric.get('detail', 'Current snapshot only'))}</small>"
        "</section>"
        for metric in stability_metrics
        if isinstance(metric, dict)
    )
    stability_html = (
        f"<section class=\"stability stability-{stability_color}\" aria-label=\"stability trends\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Stability</span>"
        f"<h2>{safe_text(stability.get('title', 'Stability Trends'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(stability.get('severity'))}\">{safe_text(stability.get('status', 'ATTENTION'))}</span></p>"
        "</div>"
        f"<p>{safe_text(stability.get('summary', 'Current stability checks need attention'))}</p>"
        f"<small>{safe_text(stability.get('history_window', 'CURRENT_SNAPSHOT_ONLY')).replace('_', ' ').title()}: samples={safe_text(stability.get('history_sample_count', 0))}, degraded={safe_text(stability.get('degraded_sample_count', 0))}, stale={safe_text(stability.get('stale_sample_count', 0))}. No live permission is created.</small>"
        f"<section class=\"stability-grid\">{stability_metric_html}</section>"
        "</section>"
    )

    maturity = shell.get("profitability_maturity", {}) if isinstance(shell.get("profitability_maturity"), dict) else {}
    maturity_color = safe_text(maturity.get("color_token", "yellow"))
    maturity_status_display = str(maturity.get("status", "COLLECTING")).replace("_", " ").title()
    maturity_check_items = maturity.get("evidence_checklist", []) if isinstance(maturity.get("evidence_checklist"), list) else []
    maturity_component_items = maturity.get("maturity_components", []) if isinstance(maturity.get("maturity_components"), list) else []
    maturity_check_html = "\n".join(
        (
            "<section class=\"evidence-check\">"
            f"<h3>{safe_text(check.get('label', 'Evidence check'))}</h3>"
            f"<p><span class=\"pill {status_class(check.get('status'))}\">{safe_text(check.get('status', 'MISSING'))}</span></p>"
            f"<small>{safe_text(check.get('observed_count', 0))}/{safe_text(check.get('required_count', 0))} | "
            f"{safe_text(check.get('message', 'Evidence required before ranking.'))}</small>"
            "</section>"
        )
        for check in maturity_check_items
        if isinstance(check, dict)
    )
    maturity_component_html = "\n".join(
        (
            "<section class=\"maturity-component\">"
            f"<h3>{safe_text(str(component.get('component_id', 'component')).replace('_', ' ').title())}</h3>"
            f"<p><span class=\"pill {status_class(component.get('status'))}\">{safe_text(component.get('status', 'EVIDENCE_MISSING'))}</span></p>"
            f"<small>{safe_text(component.get('operator_message', 'Evidence still required.'))}</small>"
            f"<small class=\"component-next\">Next: {safe_text(component.get('next_required_evidence', 'Collect scoped PAPER/SHADOW evidence.'))}</small>"
            "</section>"
        )
        for component in maturity_component_items
        if isinstance(component, dict)
    )
    maturity_html = (
        f"<section class=\"maturity maturity-{maturity_color}\" aria-label=\"strategy evidence maturity\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Strategy Evidence</span>"
        f"<h2>{safe_text(maturity.get('title', 'Strategy Evidence Maturity'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(maturity.get('severity'))}\">{safe_text(maturity_status_display)}</span></p>"
        "</div>"
        "<section class=\"decision-grid\">"
        "<div><strong>Paper / Shadow Samples</strong>"
        f"<p>{safe_text(maturity.get('sample_summary', 'No paper/shadow evidence loaded'))}</p></div>"
        "<div><strong>Optimizer Input</strong>"
        f"<p><span class=\"pill {status_class(maturity.get('severity'))}\">{safe_text(maturity.get('optimizer_ranking_action', 'BLOCK_RANKING'))}</span></p></div>"
        "<div><strong>PAPER Scorecard</strong>"
        f"<p>{safe_text(maturity.get('candidate_scorecard_candidate_id') or 'none')} | {safe_text(maturity.get('candidate_scorecard_symbol') or 'UNKNOWN')}<br>"
        f"net EV={safe_text(maturity.get('candidate_scorecard_net_ev_after_cost_display', 'UNVERIFIED'))}<br>"
        f"<span class=\"pill {status_class(maturity.get('candidate_scorecard_status'))}\">{safe_text(maturity.get('candidate_scorecard_status', 'NOT_LOADED'))}</span></p>"
        f"<small>{safe_text(maturity.get('candidate_scorecard_blocker_summary', 'No PAPER candidate scorecard is loaded.'))}</small></div>"
        "<div><strong>Evidence Quality</strong>"
        f"<p>cost={safe_text(maturity.get('cost_evidence_status', 'UNTESTED'))}, entry={safe_text(maturity.get('entry_reason_status', 'UNTESTED'))}, no-trade={safe_text(maturity.get('no_trade_reason_status', 'UNTESTED'))}</p></div>"
        "<div><strong>Long-Run Evidence</strong>"
        f"<p><span class=\"pill {status_class(maturity.get('actual_runtime_source_status'))}\">{safe_text(maturity.get('actual_runtime_source_status', 'MISSING'))}</span><br>"
        f"{safe_text(maturity.get('actual_runtime_source_count', 0))} runtime sources</p>"
        f"<small>{safe_text(maturity.get('actual_runtime_source_summary', 'Validated non-live persistent runtime source evidence is required.'))}</small></div>"
        "<div><strong>Readiness Scope</strong>"
        f"<p><span class=\"pill safe-lock\">{safe_text(maturity.get('scorecard_scope', 'PAPER_EVIDENCE_COLLECTION_ONLY'))}</span><br>"
        f"<span class=\"pill safe-lock\">{safe_text(maturity.get('live_readiness_status', 'NOT_LIVE_READY'))}</span></p></div>"
        "<div><strong>Evidence Rollup</strong>"
        f"<p><span class=\"pill {status_class(maturity.get('rollup_source_status'))}\">{safe_text(maturity.get('rollup_source_status', 'NOT_LOADED'))}</span></p>"
        f"<small>{safe_text(maturity.get('rollup_component_count', 0))}/{safe_text(maturity.get('rollup_required_component_count', 10))} components | {safe_text(maturity.get('rollup_status', 'NOT_LOADED'))}</small></div>"
        "</section>"
        "<section class=\"evidence-progress\" aria-label=\"strategy evidence progress\">"
        f"<h3>Evidence Progress: {safe_text(maturity.get('evidence_progress_pct', 0))}%</h3>"
        f"<p>{safe_text(maturity.get('evidence_progress_summary', 'Evidence checks not started'))}</p>"
        f"<section class=\"evidence-check-grid\">{maturity_check_html}</section>"
        "</section>"
        "<section class=\"evidence-progress\" aria-label=\"profitability maturity gap checklist\">"
        f"<h3>Maturity Gap: {safe_text(maturity.get('maturity_gap_status', 'OPEN_HIGH'))}</h3>"
        f"<p>{safe_text(maturity.get('maturity_gap_summary', 'Profitability maturity gaps remain.'))}</p>"
        "<section class=\"maturity-component-grid\">"
        f"{maturity_component_html}"
        "</section>"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(maturity.get('next_action', 'Run PAPER operational cycle before scorecard review.'))}</p>"
        f"<small>{safe_text(maturity.get('operator_warning', 'PAPER evidence is not LIVE_READY and cannot place or allow live orders.'))} Candidate={safe_text(maturity.get('candidate_id') or 'none')} | Strategy={safe_text(maturity.get('strategy_id') or 'none')} | Blocker={safe_text(maturity.get('primary_blocker_code') or 'none')}. This panel is analysis-only; live and scale-up remain blocked.</small>"
        "</section>"
    )

    convergence = shell.get("convergence_assessment_status", {}) if isinstance(shell.get("convergence_assessment_status"), dict) else {}
    convergence_color = safe_text(convergence.get("color_token", "yellow"))
    convergence_status_display = str(convergence.get("status", "UNTESTED")).replace("_", " ").title()
    convergence_dependencies = convergence.get("dependency_statuses", []) if isinstance(convergence.get("dependency_statuses"), list) else []
    convergence_dependency_html = "\n".join(
        (
            "<section class=\"dependency-check\">"
            f"<h3>{safe_text(str(item.get('validator_id', 'dependency')).replace('_validator', '').replace('_', ' ').title())}</h3>"
            f"<p><span class=\"pill {status_class(item.get('status'))}\">{safe_text(item.get('status', 'UNTESTED'))}</span></p>"
            "</section>"
        )
        for item in convergence_dependencies
        if isinstance(item, dict)
    )
    convergence_html = (
        f"<section class=\"convergence convergence-{convergence_color}\" aria-label=\"convergence assessment status\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Convergence Review</span>"
        f"<h2>{safe_text(convergence.get('title', 'Convergence Assessment'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(convergence.get('status'))}\">{safe_text(convergence_status_display)}</span></p>"
        "</div>"
        "<section class=\"decision-grid\">"
        "<div><strong>Assessment</strong>"
        f"<p>{safe_text(convergence.get('assessment_status', 'UNTESTED'))}<br>claim={safe_text(convergence.get('convergence_claim', 'NO_CLAIM'))}</p></div>"
        "<div><strong>Dependency Closure</strong>"
        f"<p>{safe_text(convergence.get('dependency_summary', '0/10 dependency validators PASS'))}</p></div>"
        "<div><strong>Model Drift</strong>"
        f"<p>{safe_text(convergence.get('model_drift_status', 'NOT_EVALUATED'))}</p></div>"
        "<div><strong>Live Boundary</strong>"
        "<p><span class=\"pill safe-lock\">not LIVE_READY</span><br><span class=\"pill safe-lock\">live orders blocked</span><br><span class=\"pill safe-lock\">scale-up blocked</span></p></div>"
        "</section>"
        "<section class=\"dependency-grid\" aria-label=\"convergence validator dependencies\">"
        f"{convergence_dependency_html}"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(convergence.get('next_action', 'Continue PAPER/SHADOW convergence monitoring.'))}</p>"
        f"<small>{safe_text(convergence.get('operator_warning', 'Convergence assessment is not LIVE_READY; live orders blocked and scale-up blocked.'))} Score band={safe_text(convergence.get('objective_score_band', 'UNKNOWN'))} | Writer Input={safe_text(convergence.get('writer_input_eligible', False))} | Model Promotion={safe_text(convergence.get('model_promotion_allowed', False))} | Scale-Up Recommendation={safe_text(convergence.get('scale_up_recommendation_allowed', False))} | Blocker={safe_text(convergence.get('primary_blocker_code', 'CONVERGENCE_STATE_UNTESTED'))}. Display-only convergence review; execution truth remains separate.</small>"
        "</section>"
    )

    exploration = shell.get("exploration_policy_status", {}) if isinstance(shell.get("exploration_policy_status"), dict) else {}
    exploration_color = safe_text(exploration.get("color_token", "yellow"))
    exploration_status_display = str(exploration.get("status", "UNTESTED")).replace("_", " ").title()
    exploration_dependencies = exploration.get("dependency_statuses", []) if isinstance(exploration.get("dependency_statuses"), list) else []
    exploration_dependency_html = "\n".join(
        (
            "<section class=\"dependency-check\">"
            f"<h3>{safe_text(str(item.get('validator_id', 'dependency')).replace('_validator', '').replace('_', ' ').title())}</h3>"
            f"<p><span class=\"pill {status_class(item.get('status'))}\">{safe_text(item.get('status', 'UNTESTED'))}</span></p>"
            "</section>"
        )
        for item in exploration_dependencies
        if isinstance(item, dict)
    )
    exploration_html = (
        f"<section class=\"exploration-policy exploration-policy-{exploration_color}\" aria-label=\"exploration exploitation policy status\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Optimizer Policy</span>"
        f"<h2>{safe_text(exploration.get('title', 'Exploration / Exploitation Policy'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(exploration.get('status'))}\">{safe_text(exploration_status_display)}</span></p>"
        "</div>"
        "<section class=\"decision-grid\">"
        "<div><strong>Transition</strong>"
        f"<p>{safe_text(exploration.get('transition_decision', 'BLOCK_TRANSITION'))}<br>state={safe_text(exploration.get('controller_state', 'BLOCKED'))}</p></div>"
        "<div><strong>Dependency Closure</strong>"
        f"<p>{safe_text(exploration.get('dependency_summary', '0/6 dependency validators PASS'))}</p></div>"
        "<div><strong>Candidate Budget</strong>"
        f"<p><span class=\"pill {status_class(exploration.get('candidate_budget_status'))}\">{safe_text(exploration.get('candidate_budget_status', 'BLOCKED'))}</span> "
        f"{safe_text(exploration.get('candidate_count', 0))}/{safe_text(exploration.get('exploration_candidate_budget', 0))}</p></div>"
        "<div><strong>PAPER Ranking</strong>"
        f"<p>{safe_text(exploration.get('recommendation_scope', 'BLOCKED'))}<br>allowed={safe_text(exploration.get('exploitation_allowed_for_paper_ranking', False))}</p></div>"
        "<div><strong>Live Boundary</strong>"
        "<p><span class=\"pill safe-lock\">not LIVE_READY</span><br><span class=\"pill safe-lock\">live orders blocked</span><br><span class=\"pill safe-lock\">scale-up blocked</span></p></div>"
        "</section>"
        "<section class=\"dependency-grid\" aria-label=\"exploration policy validator dependencies\">"
        f"{exploration_dependency_html}"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(exploration.get('next_action', 'Continue PAPER/SHADOW exploration policy monitoring.'))}</p>"
        f"<small>{safe_text(exploration.get('operator_warning', 'Exploration policy is not LIVE_READY; live orders blocked and scale-up blocked.'))} Objective={safe_text(exploration.get('objective_basis', 'BLOCKED_NO_VALID_OBJECTIVE'))} | Policy={safe_text(exploration.get('policy_status', 'UNTESTED'))} | Candidate={safe_text(exploration.get('exploitation_candidate_id') or 'none')} | Blocker={safe_text(exploration.get('primary_blocker_code', 'EXPLORATION_POLICY_UNTESTED'))}. PAPER ranking review only; execution truth remains separate.</small>"
        "</section>"
    )

    parameter = shell.get("parameter_narrowing_status", {}) if isinstance(shell.get("parameter_narrowing_status"), dict) else {}
    parameter_color = safe_text(parameter.get("color_token", "yellow"))
    parameter_status_display = str(parameter.get("status", "UNTESTED")).replace("_", " ").title()
    parameter_dependencies = parameter.get("dependency_statuses", []) if isinstance(parameter.get("dependency_statuses"), list) else []
    parameter_dependency_html = "\n".join(
        (
            "<section class=\"dependency-check\">"
            f"<h3>{safe_text(str(item.get('validator_id', 'dependency')).replace('_validator', '').replace('_', ' ').title())}</h3>"
            f"<p><span class=\"pill {status_class(item.get('status'))}\">{safe_text(item.get('status', 'UNTESTED'))}</span></p>"
            "</section>"
        )
        for item in parameter_dependencies
        if isinstance(item, dict)
    )
    parameter_html = (
        f"<section class=\"parameter-narrowing parameter-narrowing-{parameter_color}\" aria-label=\"parameter narrowing status\">"
        "<div class=\"portfolio-head\">"
        "<div>"
        "<span class=\"eyebrow\">Parameter Proposal</span>"
        f"<h2>{safe_text(parameter.get('title', 'Parameter Narrowing'))}</h2>"
        "</div>"
        f"<p><span class=\"pill {status_class(parameter.get('status'))}\">{safe_text(parameter_status_display)}</span></p>"
        "</div>"
        "<section class=\"decision-grid\">"
        "<div><strong>Review Scope</strong>"
        f"<p>{safe_text(parameter.get('recommendation_scope', 'BLOCKED'))}<br>write={safe_text(parameter.get('parameter_write_scope', 'BLOCKED'))}</p></div>"
        "<div><strong>Dependency Closure</strong>"
        f"<p>{safe_text(parameter.get('dependency_summary', '0/7 dependency validators PASS'))}</p></div>"
        "<div><strong>Sample Coverage</strong>"
        f"<p>{safe_text(parameter.get('sample_summary', '0 PAPER / 0 SHADOW samples'))}<br>required={safe_text(parameter.get('min_required_sample_count', 0))}</p></div>"
        "<div><strong>Parameter Set</strong>"
        f"<p>{safe_text(parameter.get('parameter_count_before', 0))} -> {safe_text(parameter.get('parameter_count_after', 0))}<br>narrowing={safe_text(parameter.get('narrowing_pct', 0.0))}% / max {safe_text(parameter.get('max_narrowing_pct', 0.0))}%</p></div>"
        "<div><strong>Live Boundary</strong>"
        "<p><span class=\"pill safe-lock\">proposal-only</span><br><span class=\"pill safe-lock\">not LIVE_READY</span><br><span class=\"pill safe-lock\">live orders blocked</span><br><span class=\"pill safe-lock\">scale-up blocked</span></p></div>"
        "</section>"
        "<section class=\"dependency-grid\" aria-label=\"parameter narrowing validator dependencies\">"
        f"{parameter_dependency_html}"
        "</section>"
        f"<p class=\"next\">Next: {safe_text(parameter.get('next_action', 'Continue PAPER/SHADOW parameter narrowing monitoring.'))}</p>"
        f"<small>{safe_text(parameter.get('operator_warning', 'Parameter narrowing is proposal-only, not LIVE_READY; live orders blocked and scale-up blocked.'))} Objective={safe_text(parameter.get('objective_basis', 'BLOCKED_NO_VALID_OBJECTIVE'))} | Status={safe_text(parameter.get('narrowing_status', 'UNTESTED'))} | Previous={safe_text(parameter.get('previous_parameter_hash') or 'none')} | Proposed={safe_text(parameter.get('proposed_parameter_hash') or 'none')} | Allowed For PAPER Review={safe_text(parameter.get('narrowing_allowed_for_paper_ranking', False))} | Blocker={safe_text(parameter.get('primary_blocker_code', 'PARAMETER_NARROWING_UNVERIFIED'))}. Display-only parameter proposal; active config, live config, execution truth, and scale-up remain separate.</small>"
        "</section>"
    )

    decision = shell.get("decision_trace", {}) if isinstance(shell.get("decision_trace"), dict) else {}
    decision_html = (
        "<section class=\"decision\" aria-label=\"trading decision trace\">"
        "<div class=\"decision-head\">"
        "<h2>Trading Decision</h2>"
        f"<span class=\"pill {status_class(decision.get('final_action'))}\">{safe_text(decision.get('final_action', 'NO_TRADE'))}</span>"
        "</div>"
        "<section class=\"decision-grid\">"
        "<div><strong>No-trade reason</strong>"
        f"<p>{safe_text(decision.get('no_trade_reason', 'HARD_TRUTH_MISSING'))}</p></div>"
        "<div><strong>Entry</strong>"
        f"<p><span class=\"pill {status_class(decision.get('entry_status'))}\">{safe_text(decision.get('entry_status', 'BLOCKED'))}</span> {safe_text(decision.get('entry_reason', 'No entry accepted'))}</p></div>"
        "<div><strong>Exit</strong>"
        f"<p><span class=\"pill {status_class(decision.get('exit_status'))}\">{safe_text(decision.get('exit_status', 'NO_POSITION'))}</span> {safe_text(decision.get('exit_reason', 'No exit action pending'))}</p></div>"
        "</section>"
        f"<small>Next: {safe_text(decision.get('next_action', 'resolve blocking reason before trading'))}</small>"
        "</section>"
    )

    recent_events = shell.get("recent_events", {}) if isinstance(shell.get("recent_events"), dict) else {}
    event_items = recent_events.get("items", []) if isinstance(recent_events.get("items"), list) else []
    if event_items:
        events_html = "\n".join(
            "<li>"
            f"<span class=\"pill {status_class(item.get('severity'))}\">{safe_text(item.get('severity', 'INFO'))}</span>"
            f"<strong>{safe_text(item.get('label', 'Event'))}</strong>"
            f"<p>{safe_text(item.get('message', 'No detail'))}</p>"
            "</li>"
            for item in event_items
            if isinstance(item, dict)
        )
    else:
        events_html = f"<li><p>{safe_text(recent_events.get('empty_message', 'No recent PAPER activity'))}</p></li>"
    recent_events_html = (
        "<section class=\"activity\" aria-label=\"recent paper activity\">"
        "<div class=\"portfolio-head\">"
        "<h2>Recent Activity</h2>"
        f"<p>Status: {safe_text(recent_events.get('status', 'INFO'))}</p>"
        "</div>"
        f"<ol>{events_html}</ol>"
        "<small>Recent dashboard activity is display-only. It cannot approve, prepare, or place live orders.</small>"
        "</section>"
    )

    portfolio = shell.get("portfolio_snapshot", {})
    portfolio_status = portfolio.get("status", "UNVERIFIED") if isinstance(portfolio, dict) else "UNVERIFIED"
    portfolio_cycle_source = portfolio.get("source_runtime_cycle_id") if isinstance(portfolio, dict) else None
    portfolio_ledger_source = portfolio.get("source_paper_ledger_head_hash") if isinstance(portfolio, dict) else None
    portfolio_age_seconds = portfolio.get("source_snapshot_age_seconds") if isinstance(portfolio, dict) else None
    portfolio_stale_after_seconds = portfolio.get("source_snapshot_stale_after_seconds") if isinstance(portfolio, dict) else None
    portfolio_age_line = (
        f"Age: {portfolio_age_seconds}s / stale after {portfolio_stale_after_seconds}s"
        if isinstance(portfolio_age_seconds, int) and isinstance(portfolio_stale_after_seconds, int)
        else "Age: not verified"
    )
    portfolio_source_line = (
        f"Runtime cycle: {portfolio_cycle_source or 'not linked'} | Ledger head: "
        f"{str(portfolio_ledger_source)[:12] + '...' if portfolio_ledger_source else 'not linked'} | {portfolio_age_line}"
    )
    if portfolio_status == "VERIFIED" and shell.get("mode") == "PAPER":
        portfolio_status = "PAPER LEDGER VERIFIED (SIMULATED)"
    elif portfolio_status == "STALE":
        portfolio_status = "STALE - RERUN PAPER"
    portfolio_kpi_ids = ("cash", "equity", "total_pnl", "return_pct")
    portfolio_detail_ids = ("locked_cash", "realized_pnl", "unrealized_pnl", "positions", "entry_candidates")
    portfolio_kpi_cards = []
    portfolio_detail_cards = []
    for card_id in PORTFOLIO_CARD_IDS:
        card = portfolio.get(card_id, {}) if isinstance(portfolio, dict) else {}
        card_html = (
            "<section class=\"metric\">"
            f"<h2>{safe_text(card.get('label', card_id))}</h2>"
            f"<p class=\"metric-value\">{safe_text(card.get('value_display', 'UNVERIFIED'))}</p>"
            f"<small>{safe_text(card.get('detail', 'No verified source loaded'))}</small>"
            "</section>"
        )
        if card_id in portfolio_kpi_ids:
            portfolio_kpi_cards.append(card_html)
        if card_id in portfolio_detail_ids:
            portfolio_detail_cards.append(card_html)
    portfolio_kpi_html = "\n      ".join(portfolio_kpi_cards)
    portfolio_detail_html = "\n      ".join(portfolio_detail_cards)

    def portfolio_value(card_id: str, fallback: str = "UNVERIFIED") -> str:
        card = portfolio.get(card_id, {}) if isinstance(portfolio, dict) else {}
        return safe_text(card.get("value_display", fallback))

    portfolio_ledger_html = (
        "<dl class=\"portfolio-ledger\" aria-label=\"portfolio compact ledger\">"
        "<div><dt>Locked</dt><dd>" + portfolio_value("locked_cash") + "</dd></div>"
        "<div><dt>Realized PnL</dt><dd>" + portfolio_value("realized_pnl") + "</dd></div>"
        "<div><dt>Unrealized PnL</dt><dd>" + portfolio_value("unrealized_pnl") + "</dd></div>"
        "<div><dt>Positions</dt><dd>" + portfolio_value("positions") + "</dd></div>"
        "<div><dt>Candidates</dt><dd>" + portfolio_value("entry_candidates") + "</dd></div>"
        "</dl>"
    )

    positions = shell.get("position_snapshot", {}) if isinstance(shell.get("position_snapshot"), dict) else {}
    position_rows = positions.get("rows", []) if isinstance(positions.get("rows"), list) else []
    if position_rows:
        position_preview_items = [
            (
                f"{row.get('symbol', 'UNKNOWN')} | {row.get('side', 'UNKNOWN')} | "
                f"qty {row.get('quantity', 'UNKNOWN')} | avg {row.get('avg_price', 'UNKNOWN')} | "
                f"mark {row.get('mark_price', 'UNKNOWN')} | value {row.get('market_value', 'UNKNOWN')} | "
                f"PnL {row.get('unrealized_pnl', 'UNKNOWN')}"
            )
            for row in position_rows[:4]
            if isinstance(row, dict)
        ]
    else:
        position_preview_items = [str(positions.get("empty_message", "No open PAPER positions"))]
    position_preview_html = "\n".join(f"<li>{safe_text(item)}</li>" for item in position_preview_items)

    entry_card = portfolio.get("entry_candidates", {}) if isinstance(portfolio, dict) else {}
    candidate_detail = str(entry_card.get("detail", "No entry candidates loaded from summary"))
    candidate_items: list[str] = []
    if candidate_detail.startswith("Candidates: "):
        candidate_items.extend(item.strip() for item in candidate_detail.removeprefix("Candidates: ").split(",") if item.strip())
    exploration = shell.get("exploration_policy_status", {}) if isinstance(shell.get("exploration_policy_status"), dict) else {}
    exploitation_candidate = exploration.get("exploitation_candidate_id")
    if exploitation_candidate and str(exploitation_candidate) not in candidate_items:
        candidate_items.append(f"Review candidate: {exploitation_candidate}")
    if maturity.get("candidate_scorecard_source") == "candidate_scorecard.json":
        scorecard_candidate = maturity.get("candidate_scorecard_candidate_id") or "candidate loaded"
        scorecard_symbol = maturity.get("candidate_scorecard_symbol") or "UNKNOWN"
        scorecard_ev = maturity.get("candidate_scorecard_net_ev_after_cost_display", "UNVERIFIED")
        candidate_items.insert(0, f"{scorecard_symbol}: {scorecard_candidate} | net EV {scorecard_ev}")
    if not candidate_items:
        candidate_items = [candidate_detail]
    candidate_preview_html = "\n".join(f"<li>{safe_text(item)}</li>" for item in candidate_items[:5])
    scorecard_status_display = str(maturity.get("candidate_scorecard_status", "NOT_LOADED")).replace("_", " ").title()
    scorecard_quicklook_items = [
        f"Status: {scorecard_status_display}",
        f"Net EV after cost: {maturity.get('candidate_scorecard_net_ev_after_cost_display', 'UNVERIFIED')}",
        f"Blocker: {maturity.get('candidate_scorecard_primary_blocker_code', 'SCORECARD_NOT_LOADED')}",
    ]
    scorecard_quicklook_html = "\n".join(f"<li>{safe_text(item)}</li>" for item in scorecard_quicklook_items)
    if position_rows:
        rows_html = "\n".join(
            "<tr>"
            f"<td>{safe_text(row.get('symbol', 'UNKNOWN'))}</td>"
            f"<td>{safe_text(row.get('side', 'UNKNOWN'))}</td>"
            f"<td>{safe_text(row.get('quantity', 'UNKNOWN'))}</td>"
            f"<td>{safe_text(row.get('avg_price', 'UNKNOWN'))}</td>"
            f"<td>{safe_text(row.get('mark_price', 'UNKNOWN'))}</td>"
            f"<td>{safe_text(row.get('market_value', 'UNKNOWN'))}</td>"
            f"<td>{safe_text(row.get('cost_basis', 'UNKNOWN'))}</td>"
            f"<td>{safe_text(row.get('unrealized_pnl', 'UNKNOWN'))}</td>"
            "</tr>"
            for row in position_rows
            if isinstance(row, dict)
        )
    else:
        rows_html = (
            "<tr><td colspan=\"8\" class=\"empty-row\">"
            + safe_text(positions.get("empty_message", "No open PAPER positions"))
            + "</td></tr>"
        )
    position_html = (
        "<section class=\"positions\" aria-label=\"open paper positions\">"
        "<div class=\"portfolio-head\">"
        "<h2>Open PAPER Positions</h2>"
        f"<p>Status: {safe_text(positions.get('status', 'NONE'))} | Count: {safe_text(positions.get('open_position_count', 0))}</p>"
        "</div>"
        "<div class=\"table-wrap\"><table>"
        "<thead><tr><th>Symbol</th><th>Side</th><th>Qty</th><th>Avg Price</th><th>Mark Price</th><th>Market Value</th><th>Cost Basis</th><th>Unrealized PnL</th></tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table></div>"
        "<small>Display-only PAPER position view. Ledger and reconciliation remain separate execution truth.</small>"
        "</section>"
    )

    panel_html = []
    for panel in shell.get("panels", []):
        panel_status = str(panel.get("status", ""))
        panel_html.append(
            f"<section class=\"panel panel-{status_class(panel_status)}\">"
            f"<h2>{html.escape(str(panel.get('title', '')))}</h2>"
            f"<p class=\"status {status_class(panel_status)}\">{html.escape(panel_status)}</p>"
            f"<p>{html.escape(str(panel.get('message') or ''))}</p>"
            f"<small>{html.escape(str(panel.get('source', '')))}</small>"
            "</section>"
        )
    source_html = []
    for source in shell.get("source_artifacts", []):
        source_html.append(
            "<tr>"
            f"<td>{safe_text(source.get('artifact_id', ''))}</td>"
            f"<td>{safe_text(source.get('filename', ''))}</td>"
            f"<td>{safe_text(source.get('freshness_status', ''))}</td>"
            f"<td>{safe_text(source.get('truth_role', ''))}</td>"
            "</tr>"
        )
    blocker = shell.get("blocking_reason") or "HARD_TRUTH_MISSING"
    next_action = shell.get("next_action") or "continue read-only monitoring; resolve blockers before any trading review"
    blocker_class = status_class(shell.get("final_action"))
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TRADER_1 Read Only Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Arial, sans-serif;
      --ok: #15803d;
      --ok-bg: #ecfdf3;
      --safe: #0f6fb3;
      --safe-bg: #eff6ff;
      --warn: #b7791f;
      --warn-bg: #fffbeb;
      --danger: #b42318;
      --danger-bg: #fef3f2;
      --line: #d7dce2;
      --ink: #1d2430;
      --muted: #5c6673;
    }
    html { box-sizing: border-box; max-width: 100%; overflow-x: hidden; }
    *, *::before, *::after { box-sizing: inherit; }
    body { margin: 0; max-width: 100%; overflow-x: hidden; background: #f7f8fa; color: #1d2430; line-height: 1.45; }
    header { padding: 22px 24px; background: #102235; color: white; border-bottom: 5px solid var(--safe); }
    main { display: grid; gap: 16px; padding: 16px; width: 100%; max-width: 1440px; margin: 0 auto; }
    h1, h2, h3, p, dl, dd, small, strong, span { overflow-wrap: anywhere; word-break: normal; }
    p, small, li, dd, td { line-height: 1.5; }
    .summary-card, .live-readiness, .operation, .operator-action, .reconciliation, .workflow, .longrun, .market-data, .paper-recovery, .runtime-boundary, .shadow-harness, .stability, .risk, .feedback, .maturity, .convergence, .exploration-policy, .parameter-narrowing, .activity, .portfolio, .positions, .panel, .decision, .alert { min-width: 0; }
    .operator-action, .reconciliation, .workflow, .longrun, .market-data, .paper-recovery, .runtime-boundary, .shadow-harness, .stability, .risk, .feedback, .maturity, .convergence, .exploration-policy, .parameter-narrowing, .activity, .portfolio, .positions, .panel, .decision, .alert { display: grid; align-content: start; gap: 12px; }
    .metric, .scope-item, .guard, .decision-grid div, .workflow-step, .dependency-check, .evidence-check, .maturity-component, .stability-metric { display: grid; align-content: start; gap: 6px; }
    .freshness-strip { display: grid; gap: 12px; grid-template-columns: minmax(220px, .8fr) minmax(0, 1.8fr); align-items: center; background: var(--ok-bg); border: 1px solid #b9dfca; border-left: 8px solid var(--ok); border-radius: 8px; padding: 14px 16px; min-width: 0; }
    .freshness-strip h2 { margin-top: 4px; }
    .freshness-strip dl { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); margin: 0; min-width: 0; }
    .freshness-strip dt { color: var(--muted); font-size: 12px; font-weight: 700; }
    .freshness-strip dd { margin: 4px 0 0; font-weight: 700; overflow-wrap: anywhere; }
    .freshness-strip p { grid-column: 1 / -1; color: #354153; }
    .freshness-fresh { background: var(--ok-bg); border-left-color: var(--ok); }
    .freshness-stale { background: var(--warn-bg); border-color: #f2c75c; border-left-color: var(--warn); }
    .summary-grid { display: grid; gap: 16px; grid-template-columns: minmax(420px, 1.35fr) minmax(320px, 1fr); align-items: stretch; }
    .portfolio-summary { grid-row: span 2; }
    .summary-card, .live-readiness { background: white; border: 1px solid var(--line); border-radius: 8px; padding: 16px; min-height: 236px; min-width: 0; overflow-wrap: anywhere; }
    .summary-card h2, .live-readiness h2 { font-size: 22px; margin: 2px 0 8px; }
    .summary-card .portfolio-kpi-grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 128px), 1fr)); margin-top: 12px; }
    .summary-card .metric { min-height: 78px; padding: 10px; }
    .summary-card .metric h2 { font-size: 13px; margin: 0; color: var(--muted); }
    .summary-card .metric-value { font-size: 18px; }
    .source-line { margin-top: -4px; color: var(--muted); font-size: 12px; overflow-wrap: anywhere; line-height: 1.45; }
    .portfolio-ledger { display: grid; gap: 0; grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr)); margin: 12px 0 0; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; background: #ffffff; }
    .portfolio-ledger div { display: grid; gap: 4px; padding: 9px 10px; border-right: 1px solid var(--line); min-width: 0; }
    .portfolio-ledger div:last-child { border-right: 0; }
    .portfolio-ledger dt { color: var(--muted); font-size: 11px; font-weight: 700; }
    .portfolio-ledger dd { margin: 0; font-size: 13px; font-weight: 700; overflow-wrap: anywhere; }
    .portfolio-quicklook { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); margin-top: 12px; }
    .portfolio-quicklook section { background: #f8fafc; border: 1px solid var(--line); border-radius: 6px; padding: 10px; min-width: 0; }
    .portfolio-quicklook h3 { margin: 0; font-size: 13px; color: var(--muted); }
    .portfolio-quicklook ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
    .portfolio-quicklook li { font-size: 13px; line-height: 1.35; overflow-wrap: anywhere; color: var(--ink); }
    .live-readiness { border-left: 8px solid var(--warn); background: var(--warn-bg); }
    .live-readiness-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .live-readiness-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .live-readiness-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .live-readiness-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .readiness-list { display: grid; gap: 8px; margin-top: 12px; }
    .readiness-row { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px; align-items: center; border-top: 1px solid rgba(0,0,0,.08); padding-top: 8px; min-width: 0; }
    .readiness-row strong { font-size: 12px; color: var(--muted); }
    .readiness-row .pill { flex: 0 1 auto; white-space: normal; }
    .summary-note { margin-top: 10px; color: var(--muted); font-size: 12px; line-height: 1.35; }
    .detail-stack { display: grid; gap: 14px; margin-top: 12px; }
    .scopebar, .guard-grid, .panel-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); }
    .portfolio-grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); }
    .portfolio-detail-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 190px), 1fr)); }
    .scope-item { background: #eef1f4; border: 1px solid #d0d6de; border-radius: 6px; padding: 10px; }
    .scope-item strong { display: block; color: #4b5664; font-size: 12px; margin-bottom: 0; }
    .operation { display: grid; gap: 16px; grid-template-columns: 1fr; align-items: start; border-radius: 8px; padding: 18px; border: 1px solid var(--line); border-left: 8px solid var(--ok); background: var(--ok-bg); min-width: 0; }
    .operation-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .operation-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .operation-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .operation-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .operation-copy { min-width: 0; max-width: none; }
    .operation h2 { font-size: 22px; line-height: 1.14; margin: 4px 0 8px; }
    .operation p { line-height: 1.5; max-width: 62ch; overflow-wrap: anywhere; word-break: normal; }
    .operation .recovery { margin-top: 10px; color: var(--ink); }
    .operation dl { display: grid; column-gap: 36px; row-gap: 16px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 210px), 1fr)); width: 100%; margin: 0; padding-top: 14px; border-top: 1px solid rgba(0,0,0,.08); }
    .operation dl div { min-width: 0; }
    .operation dt { color: var(--muted); font-size: 12px; }
    .operation dd { margin: 5px 0 0; font-weight: 700; overflow-wrap: anywhere; }
    .operation dd:not(.pill) { font-size: 14px; line-height: 1.4; white-space: normal; overflow-wrap: anywhere; word-break: normal; }
    .eyebrow { color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .alert { background: var(--warn-bg); border: 1px solid #f2c75c; border-left: 6px solid var(--warn); border-radius: 6px; padding: 14px; }
    .decision { background: white; border: 1px solid var(--line); border-left: 6px solid var(--safe); border-radius: 8px; padding: 14px; }
    .decision-head { display: flex; flex-wrap: wrap; gap: 8px; align-items: flex-start; justify-content: space-between; margin-bottom: 0; }
    .decision-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr)); }
    .decision-grid div { background: #f8fafc; border: 1px solid var(--line); border-radius: 6px; padding: 10px; min-height: 76px; min-width: 0; overflow-wrap: anywhere; }
    .decision-grid strong { display: block; color: var(--muted); font-size: 12px; margin-bottom: 0; }
    .decision-grid p, .decision-grid small, .evidence-requirement p, .evidence-requirement small { overflow-wrap: anywhere; word-break: normal; }
    .evidence-requirement-head { display: grid; gap: 4px; grid-template-columns: minmax(180px, max-content) minmax(0, 1fr); align-items: baseline; padding-top: 2px; }
    .evidence-requirement-head strong { color: var(--text); font-size: 14px; }
    .evidence-requirement-head span { color: var(--muted); line-height: 1.55; overflow-wrap: anywhere; }
    .evidence-requirement-grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); }
    .evidence-requirement { display: grid; align-content: start; gap: 8px; min-width: 0; min-height: 132px; padding: 11px; background: #ffffff; border: 1px solid var(--line); border-radius: 6px; overflow-wrap: anywhere; }
    .evidence-requirement strong { color: var(--muted); font-size: 12px; }
    .evidence-requirement p, .evidence-requirement small { margin: 0; line-height: 1.55; }
    .operator-action { background: white; border: 1px solid var(--line); border-left: 6px solid var(--safe); border-radius: 8px; padding: 14px; }
    .operator-action-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .operator-action-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .operator-action-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .operator-action-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .shadow-harness { background: white; border: 1px solid var(--line); border-left: 6px solid var(--safe); border-radius: 8px; padding: 14px; }
    .shadow-harness-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .shadow-harness-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .shadow-harness-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .shadow-harness-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .reconciliation { background: white; border: 1px solid var(--line); border-left: 6px solid var(--warn); border-radius: 8px; padding: 14px; }
    .reconciliation-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .reconciliation-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .reconciliation-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .reconciliation-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .workflow { background: white; border: 1px solid var(--line); border-left: 6px solid var(--safe); border-radius: 8px; padding: 14px; }
    .workflow-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .workflow-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .workflow-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .workflow-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .workflow-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr)); margin-top: 12px; }
    .workflow-step { background: rgba(255,255,255,.76); border: 1px solid var(--line); border-radius: 6px; padding: 10px; min-height: 104px; }
    .workflow-step h3 { margin: 0; font-size: 13px; color: var(--muted); }
    .longrun { background: white; border: 1px solid var(--line); border-left: 6px solid var(--safe); border-radius: 8px; padding: 14px; }
    .longrun-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .longrun-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .longrun-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .longrun-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .market-data { background: white; border: 1px solid var(--line); border-left: 6px solid var(--safe); border-radius: 8px; padding: 14px; }
    .market-data-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .market-data-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .market-data-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .market-data-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .paper-recovery { background: white; border: 1px solid var(--line); border-left: 6px solid var(--safe); border-radius: 8px; padding: 14px; }
    .paper-recovery-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .paper-recovery-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .paper-recovery-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .paper-recovery-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .runtime-boundary { background: white; border: 1px solid var(--line); border-left: 6px solid var(--safe); border-radius: 8px; padding: 14px; }
    .runtime-boundary-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .runtime-boundary-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .runtime-boundary-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .runtime-boundary-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .stability { background: white; border: 1px solid var(--line); border-left: 6px solid var(--warn); border-radius: 8px; padding: 14px; }
    .stability-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .stability-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .stability-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .stability-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .risk { background: white; border: 1px solid var(--line); border-left: 6px solid var(--warn); border-radius: 8px; padding: 14px; }
    .risk-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .risk-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .risk-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .risk-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .feedback { background: white; border: 1px solid var(--line); border-left: 6px solid var(--warn); border-radius: 8px; padding: 14px; }
    .feedback-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .feedback-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .feedback-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .feedback-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .maturity { background: white; border: 1px solid var(--line); border-left: 6px solid var(--warn); border-radius: 8px; padding: 14px; }
    .maturity-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .maturity-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .maturity-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .maturity-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .convergence { background: white; border: 1px solid var(--line); border-left: 6px solid var(--warn); border-radius: 8px; padding: 14px; }
    .convergence-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .convergence-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .convergence-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .convergence-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .exploration-policy { background: white; border: 1px solid var(--line); border-left: 6px solid var(--warn); border-radius: 8px; padding: 14px; }
    .exploration-policy-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .exploration-policy-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .exploration-policy-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .exploration-policy-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .parameter-narrowing { background: white; border: 1px solid var(--line); border-left: 6px solid var(--warn); border-radius: 8px; padding: 14px; }
    .parameter-narrowing-green { border-left-color: var(--ok); background: var(--ok-bg); }
    .parameter-narrowing-blue { border-left-color: var(--safe); background: var(--safe-bg); }
    .parameter-narrowing-yellow { border-left-color: var(--warn); background: var(--warn-bg); }
    .parameter-narrowing-red { border-left-color: var(--danger); background: var(--danger-bg); }
    .dependency-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 250px), 1fr)); gap: 12px; margin-top: 12px; }
    .dependency-check { padding: 12px; border: 1px solid var(--line); border-radius: 8px; background: rgba(255,255,255,0.78); min-height: 78px; overflow-wrap: anywhere; }
    .dependency-check h3 { margin: 0; font-size: 13px; line-height: 1.35; color: var(--muted); }
    .dependency-check p { margin: 0; }
    .evidence-progress { margin-top: 14px; padding: 12px; border: 1px solid var(--line); border-radius: 8px; background: rgba(255,255,255,0.72); }
    .evidence-progress h3 { margin: 0 0 4px; font-size: 15px; }
    .evidence-progress p { margin: 0 0 10px; color: var(--muted); }
    .evidence-check-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 12px; }
    .evidence-check { padding: 12px; border: 1px solid var(--line); border-radius: 8px; background: white; overflow-wrap: anywhere; }
    .evidence-check h3 { margin: 0; font-size: 13px; line-height: 1.35; }
    .evidence-check p { margin: 0; }
    .evidence-check small { color: var(--muted); line-height: 1.35; }
    .maturity-component-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 340px), 1fr)); gap: 14px; align-items: stretch; }
    .maturity-component { padding: 14px; border: 1px solid var(--line); border-radius: 8px; background: white; min-height: 104px; overflow-wrap: anywhere; }
    .maturity-component h3 { margin: 0; font-size: 13px; line-height: 1.35; color: var(--muted); }
    .maturity-component p { margin: 0; }
    .maturity-component small { color: var(--muted); line-height: 1.35; }
    .stability-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); margin-top: 12px; }
    .stability-metric { background: rgba(255,255,255,.74); border: 1px solid var(--line); border-radius: 6px; padding: 12px; min-height: 96px; overflow-wrap: anywhere; }
    .stability-metric h3 { margin: 0; font-size: 13px; line-height: 1.35; color: var(--muted); }
    .activity { background: white; border: 1px solid var(--line); border-radius: 8px; padding: 14px; }
    .activity ol { display: grid; gap: 8px; list-style: none; margin: 0; padding: 0; }
    .activity li { display: grid; grid-template-columns: auto minmax(90px, 160px) 1fr; gap: 10px; align-items: start; background: #f8fafc; border: 1px solid var(--line); border-radius: 6px; padding: 10px; }
    .activity li p { color: var(--ink); }
    .guard { background: #ffffff; border: 1px solid #cfd6df; border-radius: 6px; padding: 12px; min-height: 72px; }
    .portfolio { background: #ffffff; border: 1px solid #cfd6df; border-radius: 8px; padding: 14px; }
    .positions { background: #ffffff; border: 1px solid #cfd6df; border-radius: 8px; padding: 14px; }
    .portfolio-head { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-start; justify-content: space-between; margin-bottom: 0; }
    .portfolio-head > div { min-width: 0; }
    .portfolio-head p { color: #5c6673; font-size: 13px; text-align: right; line-height: 1.55; }
    .metric { background: #f8fafc; border: 1px solid #d7dce2; border-radius: 6px; padding: 12px; min-height: 94px; }
    .metric-value { font-size: 20px; font-weight: 700; color: #1d2430; overflow-wrap: anywhere; }
    .panel { background: white; border: 1px solid #d7dce2; border-radius: 8px; padding: 14px; }
    .panel-ok { border-left: 5px solid var(--ok); }
    .panel-warn { border-left: 5px solid var(--warn); }
    .panel-danger { border-left: 5px solid var(--danger); }
    .panel-neutral { border-left: 5px solid #98a2b3; }
    details { background: white; border: 1px solid #d7dce2; border-radius: 8px; padding: 12px; }
    details.detail-drawer { border-color: #c8d1dc; background: #ffffff; }
    details.detail-drawer > summary { font-size: 16px; }
    summary { cursor: pointer; font-weight: 700; }
    .table-wrap { width: 100%; max-width: 100%; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 860px; }
    th, td { border-bottom: 1px solid #e2e6eb; padding: 8px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
    .empty-row { color: var(--muted); text-align: center; }
    h1, h2, p { margin: 0; }
    h1 { font-size: 24px; }
    h2 { font-size: 15px; margin-bottom: 8px; }
    .status { font-weight: 700; margin-bottom: 8px; }
    .status.ok { color: var(--ok); }
    .status.warn { color: var(--warn); }
    .status.danger { color: var(--danger); }
    .pill { display: inline-flex; align-items: center; max-width: 100%; border-radius: 999px; padding: 4px 8px; min-height: 22px; background: #eef1f4; color: var(--ink); font-size: 12px; line-height: 1.25; white-space: normal; overflow-wrap: anywhere; text-align: left; }
    .pill.ok { background: var(--ok-bg); color: var(--ok); }
    .pill.warn { background: var(--warn-bg); color: var(--warn); }
    .pill.danger { background: var(--danger-bg); color: var(--danger); }
    .pill.neutral { background: #eef1f4; color: var(--ink); }
    .pill.safe-lock { background: var(--safe-bg); color: var(--safe); }
    .next { margin-top: 8px; color: #354153; }
    small { display: block; margin-top: 12px; color: #5c6673; }
    @media (max-width: 980px) { .summary-grid { grid-template-columns: 1fr; } .portfolio-summary { grid-row: auto; } }
    @media (max-width: 720px) { .freshness-strip { grid-template-columns: 1fr; } .operation { grid-template-columns: 1fr; } .operation dl { grid-template-columns: 1fr; } .activity li { grid-template-columns: 1fr; } .portfolio-head p { text-align: left; } .summary-card .portfolio-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .portfolio-ledger { grid-template-columns: 1fr; } .portfolio-ledger div { border-right: 0; border-bottom: 1px solid var(--line); grid-template-columns: minmax(88px, .7fr) minmax(0, 1fr); align-items: baseline; } .portfolio-ledger div:last-child { border-bottom: 0; } .evidence-requirement-head { grid-template-columns: 1fr; } }
  </style>
  <script>
    (function () {
      function formatAge(seconds) {
        if (!Number.isFinite(seconds) || seconds < 0) {
          return "unknown";
        }
        if (seconds < 60) {
          return String(seconds) + "s";
        }
        var minutes = Math.floor(seconds / 60);
        var rest = seconds % 60;
        return String(minutes) + "m " + String(rest) + "s";
      }
      function updateDashboardFreshness() {
        var box = document.querySelector("[data-dashboard-freshness]");
        if (!box) {
          return;
        }
        var generatedAt = Date.parse(box.getAttribute("data-generated-at") || "");
        var staleAfter = Number(box.getAttribute("data-stale-after") || "300");
        var ageNode = box.querySelector("[data-dashboard-age]");
        var pill = box.querySelector("[data-client-freshness-pill]");
        var warning = box.querySelector("[data-stale-warning]");
        var ageSeconds = Number.isFinite(generatedAt) ? Math.max(0, Math.floor((Date.now() - generatedAt) / 1000)) : staleAfter + 1;
        var stale = ageSeconds > staleAfter;
        if (ageNode) {
          ageNode.textContent = formatAge(ageSeconds);
        }
        if (pill) {
          pill.textContent = stale ? "STALE - refresh PAPER" : "Fresh snapshot";
          pill.className = stale ? "pill warn" : "pill ok";
        }
        if (warning) {
          warning.textContent = stale
            ? "This dashboard page is older than the freshness limit. Keep the safe monitor running or rerun PAPER before trusting values."
            : "This page reloads the local dashboard file while the safe monitor writes new snapshots.";
        }
        box.className = stale ? "freshness-strip freshness-stale" : "freshness-strip freshness-fresh";
      }
      function detailStateKey(detail, index) {
        var stableKey = detail.getAttribute("data-detail-key");
        if (stableKey) {
          return "trader1.dashboard.detailsOpen." + stableKey;
        }
        var summary = detail.querySelector("summary");
        var label = summary ? summary.textContent.replace(/\\s+/g, " ").trim() : "detail";
        return "trader1.dashboard.detailsOpen." + String(index) + "." + label.slice(0, 80);
      }
      function restoreDetailState() {
        var detailNodes = document.querySelectorAll("details");
        Array.prototype.forEach.call(detailNodes, function (detail, index) {
          try {
            var key = detailStateKey(detail, index);
            var stored = window.localStorage.getItem(key);
            if (stored === "true") {
              detail.open = true;
            }
            if (stored === "false") {
              detail.open = false;
            }
            detail.addEventListener("toggle", function () {
              window.localStorage.setItem(key, detail.open ? "true" : "false");
            });
          } catch (error) {
            /* Local file dashboards may run with storage unavailable; keep refresh fail-open for display only. */
          }
        });
      }
      function initializeDashboardClient() {
        updateDashboardFreshness();
        restoreDetailState();
        window.setInterval(updateDashboardFreshness, 1000);
        var box = document.querySelector("[data-dashboard-freshness]");
        var refreshSeconds = box ? Number(box.getAttribute("data-refresh-seconds") || "10") : 10;
        if (Number.isFinite(refreshSeconds) && refreshSeconds >= 5) {
          window.setTimeout(function () { window.location.reload(); }, refreshSeconds * 1000);
        }
      }
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeDashboardClient, { once: true });
      } else {
        initializeDashboardClient();
      }
    }());
  </script>
</head>
<body>
  <header>
    <h1>TRADER_1</h1>
    <p>""" + safe_text(shell.get("primary_status_text", "")) + """</p>
  </header>
  <main>
    """ + freshness_html + """
    <section class="summary-grid" aria-label="first screen summary">
      <section class="summary-card portfolio-summary" aria-label="real-time portfolio snapshot">
        <span class="eyebrow">Real-Time Portfolio</span>
        <h2>Portfolio Snapshot</h2>
        <p>Status: """ + safe_text(portfolio_status) + """ | Source: """ + safe_text(portfolio.get("source", "summary.json")) + """</p>
        <p class="source-line">""" + safe_text(portfolio_source_line) + """</p>
        <section class="portfolio-kpi-grid">
          """ + portfolio_kpi_html + """
        </section>
        """ + portfolio_ledger_html + """
        <section class="portfolio-quicklook" aria-label="portfolio positions and entry candidates">
          <section>
            <h3>Held Positions</h3>
            <ul>""" + position_preview_html + """</ul>
          </section>
          <section>
            <h3>Entry Candidates</h3>
            <ul>""" + candidate_preview_html + """</ul>
          </section>
          <section>
            <h3>PAPER Scorecard</h3>
            <ul>""" + scorecard_quicklook_html + """</ul>
          </section>
        </section>
        <p class="summary-note">""" + safe_text(portfolio.get("next_action", "Provide verified portfolio evidence before values can be trusted")) + """</p>
      </section>
      """ + operation_html + """
      <section class="live-readiness live-readiness-yellow" aria-label="live readiness summary">
        <span class="eyebrow">Live Readiness</span>
        <h2>Blocked Before Live</h2>
        <p class="status warn">""" + safe_text(blocker) + """</p>
        <p class="next">""" + safe_text(next_action) + """</p>
        <section class="readiness-list">
          <div class="readiness-row"><strong>Live Ready</strong><span class="pill safe-lock" title="live_order_ready=false" aria-label="live_order_ready false">false</span></div>
          <div class="readiness-row"><strong>Live Orders</strong><span class="pill safe-lock" title="live_order_allowed=false" aria-label="live_order_allowed false">false</span></div>
          <div class="readiness-row"><strong>Live Trading</strong><span class="pill safe-lock" title="can_live_trade=false" aria-label="can_live_trade false">false</span></div>
          <div class="readiness-row"><strong>Risk Scale-Up</strong><span class="pill safe-lock" title="scale_up_allowed=false" aria-label="scale_up_allowed false">false</span></div>
        </section>
        <p class="summary-note">Dashboard display truth only. Engine, ledger, and exchange truth remain separate.</p>
      </section>
    </section>
    <section class="scopebar" aria-label="runtime scope">
      """ + scope_html + """
    </section>
    <details class="detail-drawer" data-detail-key="main-detail-drawer">
      <summary>Detailed status, evidence, and validator logs</summary>
      <section class="detail-stack">
        """ + operator_html + """
        """ + reconciliation_html + """
        """ + workflow_html + """
        """ + long_run_html + """
        """ + market_data_html + """
        """ + paper_recovery_guard_html + """
        """ + runtime_boundary_html + """
        """ + runtime_orchestration_html + """
        """ + shadow_harness_html + """
        """ + shadow_persistent_html + """
        """ + risk_html + """
        """ + feedback_html + """
        """ + stability_html + """
        """ + maturity_html + """
        """ + convergence_html + """
        """ + exploration_html + """
        """ + parameter_html + """
        <section class="alert alert-""" + safe_text(blocker_class) + """" aria-label="primary blocker">
          <h2>Primary Blocker</h2>
          <p class="status">""" + safe_text(blocker) + """</p>
          <p class="next">Next operator action: """ + safe_text(next_action) + """</p>
          <small>Dashboard display truth only. Engine, ledger, and exchange truth remain separate.</small>
        </section>
        """ + decision_html + """
        """ + recent_events_html + """
        <section class="portfolio" aria-label="portfolio detail metrics">
          <div class="portfolio-head">
            <h2>Portfolio Details</h2>
            <p>Secondary PAPER metrics are kept here so the first screen stays readable.</p>
          </div>
          <section class="portfolio-detail-grid">
            """ + portfolio_detail_html + """
          </section>
        </section>
        """ + position_html + """
        <section class="guard-grid" aria-label="live safety flags">
          """ + guard_html + """
        </section>
        <details data-detail-key="status-panels">
          <summary>Status Panels</summary>
          <section class="panel-grid">
            """ + "\n        ".join(panel_html) + """
          </section>
        </details>
        <details data-detail-key="source-artifacts">
          <summary>Source Artifacts</summary>
          <div class="table-wrap"><table>
            <thead><tr><th>Artifact</th><th>File</th><th>Freshness</th><th>Truth Role</th></tr></thead>
            <tbody>
              """ + "\n          ".join(source_html) + """
            </tbody>
          </table></div>
        </details>
      </section>
    </details>
  </main>
</body>
</html>
"""


def validate_dashboard_visual_layout_contract(html: str) -> DashboardValidationResult:
    required_fragments = {
        "page_width_bound": "main { display: grid; gap: 16px; padding: 16px; width: 100%; max-width: 1440px; margin: 0 auto; }",
        "comfortable_line_height": "p, small, li, dd, td { line-height: 1.5; }",
        "two_column_first_screen": ".summary-grid { display: grid; gap: 16px; grid-template-columns: minmax(420px, 1.35fr) minmax(320px, 1fr);",
        "portfolio_summary_span": ".portfolio-summary { grid-row: span 2; }",
        "kpi_auto_fit": "grid-template-columns: repeat(auto-fit, minmax(min(100%, 128px), 1fr));",
        "ledger_auto_fit": "grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr));",
        "quicklook_auto_fit": "grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));",
        "operation_spacing": ".operation dl { display: grid; column-gap: 36px; row-gap: 16px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 210px), 1fr));",
        "operation_text_spacing": ".operation dd:not(.pill) { font-size: 14px; line-height: 1.4;",
        "detail_stable_key_js": 'detail.getAttribute("data-detail-key")',
        "detail_main_key": 'data-detail-key="main-detail-drawer"',
        "detail_status_key": 'data-detail-key="status-panels"',
        "detail_source_key": 'data-detail-key="source-artifacts"',
        "paper_scorecard_quicklook": "PAPER Scorecard",
        "position_mark_price_column": "Mark Price",
        "position_market_value_column": "Market Value",
        "position_cost_basis_column": "Cost Basis",
        "market_data_continuity": "Market Data Continuity",
        "market_data_color_class": ".market-data-blue",
        "detail_state_storage": "trader1.dashboard.detailsOpen.",
        "no_horizontal_body_scroll": "overflow-x: hidden",
        "table_scroll_wrapper": ".table-wrap { width: 100%; max-width: 100%; overflow-x: auto; }",
        "position_table_width": "min-width: 860px;",
        "no_default_open_details": '<details class="detail-drawer" data-detail-key="main-detail-drawer">',
    }
    missing = [name for name, fragment in required_fragments.items() if fragment not in html]
    if missing:
        return DashboardValidationResult(
            "FAIL",
            f"dashboard visual layout contract missing: {', '.join(missing)}",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    forbidden_fragments = [
        "grid-template-columns: repeat(4, minmax(0, 1fr));",
        "grid-template-columns: repeat(5, minmax(0, 1fr));",
        "grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));",
        "<details open>",
        "max-width: 66ch",
    ]
    forbidden = [fragment for fragment in forbidden_fragments if fragment in html]
    if forbidden:
        return DashboardValidationResult(
            "FAIL",
            f"dashboard visual layout contract found cramped or nonpersistent layout fragment: {forbidden[0]}",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    return DashboardValidationResult("PASS", "dashboard visual layout contract preserves readable first screen and persisted details", None)
