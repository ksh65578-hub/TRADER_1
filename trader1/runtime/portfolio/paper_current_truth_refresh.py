from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.runtime.portfolio.paper_portfolio import (
    PAPER_PORTFOLIO_SCHEMA_ID,
    paper_portfolio_hash,
    validate_paper_portfolio_snapshot,
)


PAPER_CURRENT_TRUTH_REFRESH_SCHEMA_ID = "trader1.paper_current_truth_refresh_report.v1"
PAPER_CURRENT_TRUTH_REFRESH_PASS_STATUS = "PASS_PAPER_CURRENT_TRUTH_REFRESHED"
PAPER_CURRENT_TRUTH_REFRESH_BLOCKED_STATUS = "BLOCKED_PAPER_CURRENT_TRUTH_UNAVAILABLE"
PAPER_CURRENT_TRUTH_REFRESH_UNSUPPORTED_STATUS = "BLOCKED_UNSUPPORTED_MODE"


@dataclass(frozen=True)
class PaperCurrentTruthRefreshValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def paper_current_truth_refresh_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("refresh_report_hash", None)
    return _sha256_json(payload)


def _source_hash(payload: dict[str, Any] | None, hash_field: str) -> str | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get(hash_field)
    return value if isinstance(value, str) and len(value) == 64 else None


def build_paper_current_truth_refresh_report(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    paper_portfolio_snapshot: dict[str, Any] | None,
    heartbeat: dict[str, Any] | None,
    startup_probe: dict[str, Any] | None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    now = generated_at_utc or utc_now()
    portfolio_result = (
        validate_paper_portfolio_snapshot(paper_portfolio_snapshot)
        if isinstance(paper_portfolio_snapshot, dict)
        else None
    )
    portfolio_valid = (
        portfolio_result is not None
        and portfolio_result.status == "PASS"
        and paper_portfolio_snapshot.get("snapshot_status") == "PASS"
        and paper_portfolio_snapshot.get("paper_only") is True
        and paper_portfolio_snapshot.get("live_order_allowed") is False
        and paper_portfolio_snapshot.get("can_live_trade") is False
    )
    heartbeat_pass = isinstance(heartbeat, dict) and heartbeat.get("heartbeat_status") == "PASS"
    startup_pass = isinstance(startup_probe, dict) and (
        startup_probe.get("startup_probe_passed") is True
        or startup_probe.get("startup_probe_phase") == "PASS"
    )
    mode_supported = mode == "PAPER"
    if not mode_supported:
        refresh_status = PAPER_CURRENT_TRUTH_REFRESH_UNSUPPORTED_STATUS
        primary_blocker_code = "LIVE_FINAL_GUARD_FAILED"
        refresh_passed = False
    elif not portfolio_valid:
        refresh_status = PAPER_CURRENT_TRUTH_REFRESH_BLOCKED_STATUS
        primary_blocker_code = (
            portfolio_result.blocker_code
            if portfolio_result is not None
            else "MEASUREMENT_MISSING"
        )
        refresh_passed = False
    else:
        refresh_status = PAPER_CURRENT_TRUTH_REFRESH_PASS_STATUS
        primary_blocker_code = "LIVE_READY_MISSING"
        refresh_passed = True

    portfolio_hash = (
        paper_portfolio_snapshot.get("snapshot_hash")
        if isinstance(paper_portfolio_snapshot, dict)
        else None
    )
    report = {
        "schema_id": PAPER_CURRENT_TRUTH_REFRESH_SCHEMA_ID,
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "refresh_status": refresh_status,
        "refresh_passed": refresh_passed,
        "truth_role": "paper_current_truth_refresh_not_audited_writer",
        "source_portfolio_schema_id": (
            paper_portfolio_snapshot.get("schema_id")
            if isinstance(paper_portfolio_snapshot, dict)
            else None
        ),
        "source_portfolio_snapshot_hash": portfolio_hash,
        "source_portfolio_snapshot_generated_at_utc": (
            paper_portfolio_snapshot.get("generated_at_utc")
            if isinstance(paper_portfolio_snapshot, dict)
            else None
        ),
        "source_portfolio_snapshot_status": (
            paper_portfolio_snapshot.get("snapshot_status")
            if isinstance(paper_portfolio_snapshot, dict)
            else "MISSING"
        ),
        "source_paper_ledger_head_hash": (
            paper_portfolio_snapshot.get("source_paper_ledger_head_hash")
            if isinstance(paper_portfolio_snapshot, dict)
            else None
        ),
        "source_runtime_cycle_id": (
            paper_portfolio_snapshot.get("source_runtime_cycle_id")
            if isinstance(paper_portfolio_snapshot, dict)
            else None
        ),
        "verified_currency": (
            paper_portfolio_snapshot.get("currency")
            if portfolio_valid
            else None
        ),
        "verified_starting_cash": (
            paper_portfolio_snapshot.get("starting_cash")
            if portfolio_valid
            else None
        ),
        "source_heartbeat_hash": _source_hash(heartbeat, "heartbeat_hash"),
        "source_startup_probe_hash": _source_hash(startup_probe, "probe_hash"),
        "source_balance_kind": (
            paper_portfolio_snapshot.get("display_balance_kind")
            if portfolio_valid
            else None
        ),
        "portfolio_refresh_key": _sha256_json(
            {
                "exchange": exchange,
                "market_type": market_type,
                "mode": mode,
                "session_id": session_id,
                "source_portfolio_snapshot_hash": portfolio_hash,
            }
        ),
        "verified_cash": (
            paper_portfolio_snapshot.get("cash_available")
            if portfolio_valid
            else None
        ),
        "verified_locked_cash": (
            paper_portfolio_snapshot.get("locked_balance")
            if portfolio_valid
            else None
        ),
        "verified_position_market_value": (
            paper_portfolio_snapshot.get("position_market_value")
            if portfolio_valid
            else None
        ),
        "verified_equity": (
            paper_portfolio_snapshot.get("equity")
            if portfolio_valid
            else None
        ),
        "verified_realized_pnl": (
            paper_portfolio_snapshot.get("realized_pnl")
            if portfolio_valid
            else None
        ),
        "verified_unrealized_pnl": (
            paper_portfolio_snapshot.get("unrealized_pnl")
            if portfolio_valid
            else None
        ),
        "verified_total_pnl": (
            paper_portfolio_snapshot.get("total_pnl")
            if portfolio_valid
            else None
        ),
        "verified_return_pct": (
            paper_portfolio_snapshot.get("return_pct")
            if portfolio_valid
            else None
        ),
        "open_position_count": (
            paper_portfolio_snapshot.get("open_position_count")
            if portfolio_valid
            else 0
        ),
        "positions": (
            paper_portfolio_snapshot.get("positions")
            if portfolio_valid and isinstance(paper_portfolio_snapshot.get("positions"), list)
            else []
        ),
        "heartbeat_pass": heartbeat_pass,
        "startup_probe_pass": startup_pass,
        "paper_only": True,
        "display_only": True,
        "dashboard_truth_only": True,
        "audited_current_evidence_writer": False,
        "continuous_audited_writer": False,
        "current_evidence_write_allowed": False,
        "audited_current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "live_ready_write_allowed": False,
        "live_config_mutation_allowed": False,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "scale_up_allowed": False,
        "primary_blocker_code": primary_blocker_code,
        "operator_next_action": (
            "Use this PAPER refresh as dashboard display truth only; audited continuous current-evidence writer remains blocked."
        ),
        "refresh_report_hash": "",
    }
    report["refresh_report_hash"] = paper_current_truth_refresh_report_hash(report)
    return report


def validate_paper_current_truth_refresh_report(
    report: dict[str, Any],
) -> PaperCurrentTruthRefreshValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "refresh_status",
        "refresh_passed",
        "truth_role",
        "source_portfolio_schema_id",
        "source_portfolio_snapshot_hash",
        "source_portfolio_snapshot_generated_at_utc",
        "source_portfolio_snapshot_status",
        "source_paper_ledger_head_hash",
        "source_runtime_cycle_id",
        "verified_currency",
        "verified_starting_cash",
        "source_heartbeat_hash",
        "source_startup_probe_hash",
        "source_balance_kind",
        "portfolio_refresh_key",
        "verified_cash",
        "verified_locked_cash",
        "verified_position_market_value",
        "verified_equity",
        "verified_realized_pnl",
        "verified_unrealized_pnl",
        "verified_total_pnl",
        "verified_return_pct",
        "open_position_count",
        "positions",
        "heartbeat_pass",
        "startup_probe_pass",
        "paper_only",
        "display_only",
        "dashboard_truth_only",
        "audited_current_evidence_writer",
        "continuous_audited_writer",
        "current_evidence_write_allowed",
        "audited_current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
        "primary_blocker_code",
        "operator_next_action",
        "refresh_report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return PaperCurrentTruthRefreshValidationResult(
            "FAIL",
            f"paper current truth refresh missing fields: {missing}",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("schema_id") != PAPER_CURRENT_TRUTH_REFRESH_SCHEMA_ID or report.get("project_id") != "TRADER_1":
        return PaperCurrentTruthRefreshValidationResult(
            "FAIL", "paper current truth refresh identity mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("refresh_report_hash") != paper_current_truth_refresh_report_hash(report):
        return PaperCurrentTruthRefreshValidationResult(
            "FAIL", "paper current truth refresh hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    false_fields = (
        "audited_current_evidence_writer",
        "continuous_audited_writer",
        "current_evidence_write_allowed",
        "audited_current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(report.get(field) is not False for field in false_fields):
        return PaperCurrentTruthRefreshValidationResult(
            "BLOCKED",
            "paper current truth refresh attempted live, audited writer, order, or scale permission",
            "LIVE_FINAL_GUARD_FAILED",
        )
    if report.get("paper_only") is not True or report.get("display_only") is not True or report.get("dashboard_truth_only") is not True:
        return PaperCurrentTruthRefreshValidationResult(
            "BLOCKED", "paper current truth refresh must remain display-only paper truth", "LIVE_FINAL_GUARD_FAILED"
        )
    if report.get("mode") != "PAPER":
        if report.get("refresh_status") != PAPER_CURRENT_TRUTH_REFRESH_UNSUPPORTED_STATUS:
            return PaperCurrentTruthRefreshValidationResult(
                "BLOCKED", "non-PAPER refresh must remain blocked", "LIVE_FINAL_GUARD_FAILED"
            )
        return PaperCurrentTruthRefreshValidationResult(
            "PASS", "paper current truth refresh blocked unsupported mode safely", None
        )
    if report.get("refresh_status") == PAPER_CURRENT_TRUTH_REFRESH_PASS_STATUS:
        if (
            report.get("refresh_passed") is not True
            or report.get("source_portfolio_schema_id") != PAPER_PORTFOLIO_SCHEMA_ID
            or report.get("source_portfolio_snapshot_status") != "PASS"
            or not isinstance(report.get("source_portfolio_snapshot_hash"), str)
            or len(report.get("source_portfolio_snapshot_hash")) != 64
            or not isinstance(report.get("portfolio_refresh_key"), str)
            or len(report.get("portfolio_refresh_key")) != 64
            or not isinstance(report.get("open_position_count"), int)
            or report.get("open_position_count") < 0
            or not isinstance(report.get("positions"), list)
            or report.get("source_balance_kind") != "SIMULATED_PAPER_LEDGER"
        ):
            return PaperCurrentTruthRefreshValidationResult(
                "FAIL", "paper current truth refresh PASS invariant mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
    elif report.get("refresh_status") == PAPER_CURRENT_TRUTH_REFRESH_BLOCKED_STATUS:
        if report.get("refresh_passed") is not False or not report.get("primary_blocker_code"):
            return PaperCurrentTruthRefreshValidationResult(
                "BLOCKED", "blocked paper current truth refresh missing blocker", "HARD_TRUTH_MISSING"
            )
    else:
        return PaperCurrentTruthRefreshValidationResult(
            "FAIL", "paper current truth refresh status unknown", "SCHEMA_IDENTITY_MISMATCH"
        )
    return PaperCurrentTruthRefreshValidationResult(
        "PASS", "paper current truth refresh is source-bound, display-only, and live-blocked", None
    )
