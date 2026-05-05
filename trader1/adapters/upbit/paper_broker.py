from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.adapters.upbit.fee_model import build_upbit_fee_slippage_baseline
from trader1.adapters.upbit.market_data import build_upbit_public_market_data_fixture, validate_upbit_public_market_data
from trader1.adapters.upbit.symbol_rules import validate_upbit_krw_symbol
from trader1.core.decision.decision_arbiter import choose_paper_final_decision, order_blocker_codes, select_primary_blocker
from trader1.core.ledger.paper_ledger import build_upbit_paper_intent_chain, validate_upbit_paper_ledger
from trader1.core.risk.risk_veto import evaluate_paper_risk_veto
from trader1.reports.no_trade_reason import build_entry_reason


UPBIT_PAPER_DRY_RUN_SCHEMA_ID = "trader1.upbit_paper_dry_run_report.v1"
SAFE_FINAL_DECISIONS = {"ENTER_LONG", "NO_TRADE", "BLOCKED", "SAFE_MODE", "RECONCILE_REQUIRED"}


@dataclass(frozen=True)
class UpbitPaperDryRunValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def upbit_paper_dry_run_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("dry_run_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _paper_order_id(paper_run_id: str, symbol: str) -> str:
    return hashlib.sha256(f"{paper_run_id}:{symbol}:paper".encode("utf-8")).hexdigest()[:24].upper()


def build_upbit_paper_dry_run_report(
    *,
    paper_run_id: str,
    symbol: str = "KRW-BTC",
    session_id: str = "mvp2_upbit_paper",
    requested_entry: bool = True,
    risk_block: bool = False,
    public_market_data: dict[str, Any] | None = None,
    fee_rate: str = "0.0005",
    slippage_bps: str = "5",
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "PAPER",
) -> dict[str, Any]:
    public_market_data = public_market_data or build_upbit_public_market_data_fixture(
        symbol=symbol,
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
    )
    blockers: list[dict[str, str]] = []

    if exchange != "UPBIT" or market_type != "KRW_SPOT" or mode != "PAPER":
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "Upbit paper dry-run is scoped to UPBIT/KRW_SPOT/PAPER"))

    public_status, public_blocker, public_message = validate_upbit_public_market_data(public_market_data, symbol=symbol, session_id=session_id)
    if public_status != "PASS" and public_blocker:
        blockers.append(_blocker(public_blocker, public_message))

    symbol_status, symbol_blocker, symbol_message = validate_upbit_krw_symbol(symbol, market_type=market_type)
    if symbol_status != "PASS" and symbol_blocker:
        blockers.append(_blocker(symbol_blocker, symbol_message))

    fee_model = build_upbit_fee_slippage_baseline(fee_rate=fee_rate, slippage_bps=slippage_bps)
    if fee_model["fee_model_status"] != "PASS":
        blockers.append(_blocker("FEE_MODEL_UNVERIFIED", "Upbit paper fee model baseline missing"))
    if fee_model["slippage_model_status"] != "PASS":
        blockers.append(_blocker("MEASUREMENT_MISSING", "Upbit paper slippage baseline missing"))

    risk_veto, risk_blocker = evaluate_paper_risk_veto(requested_entry=requested_entry, risk_block=risk_block)
    if risk_veto and risk_blocker:
        blockers.append(_blocker(risk_blocker, "paper dry-run risk veto blocked entry"))

    final_decision = choose_paper_final_decision(requested_entry=requested_entry, blockers=blockers)
    paper_ledger_events: list[dict[str, Any]] = []
    paper_order_submitted = False
    paper_order_id: str | None = None
    paper_ledger_head_hash: str | None = None
    paper_ledger_write_status = "BLOCKED" if blockers else "SKIPPED_NO_TRADE"
    entry_reasons: list[dict[str, str]] = []
    no_trade_reasons: list[str] = []

    if final_decision == "ENTER_LONG":
        paper_order_id = _paper_order_id(paper_run_id, symbol)
        paper_ledger_events = build_upbit_paper_intent_chain(
            session_id=session_id,
            symbol=symbol,
            intent_id=f"{paper_run_id}-intent",
            client_order_id=paper_order_id,
        )
        paper_order_submitted = True
        paper_ledger_head_hash = paper_ledger_events[-1]["event_hash"]
        paper_ledger_write_status = "WRITTEN"
        entry_reasons = [
            build_entry_reason("PAPER_DRY_RUN_ENTRY", "paper-only entry intent created"),
            build_entry_reason("PUBLIC_DATA_AVAILABLE", "public Upbit fixture data loaded"),
            build_entry_reason("SYMBOL_RULE_PASS", "symbol rule scaffold passed"),
            build_entry_reason("FEE_SLIPPAGE_BASELINE_PASS", "fee and slippage baseline present"),
        ]
    elif blockers:
        no_trade_reasons = order_blocker_codes(blockers)
    else:
        no_trade_reasons = ["MIN_EDGE_FAIL"]

    report = {
        "schema_id": UPBIT_PAPER_DRY_RUN_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "paper_run_id": paper_run_id,
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "symbol": symbol,
        "public_data_source": public_market_data.get("source", "UNAVAILABLE"),
        "public_data_loaded": public_status == "PASS",
        "public_market_data": public_market_data,
        "symbol_rule_status": symbol_status,
        "fee_model_status": fee_model["fee_model_status"],
        "slippage_model_status": fee_model["slippage_model_status"],
        "fee_rate": fee_model["fee_rate"],
        "slippage_bps": fee_model["slippage_bps"],
        "paper_broker_status": "PASS" if not blockers else "BLOCKED",
        "paper_order_id": paper_order_id,
        "paper_order_submitted": paper_order_submitted,
        "final_decision": final_decision,
        "no_trade_reasons": no_trade_reasons,
        "entry_reasons": entry_reasons,
        "paper_ledger_events": paper_ledger_events,
        "paper_ledger_head_hash": paper_ledger_head_hash,
        "paper_ledger_write_status": paper_ledger_write_status,
        "paper_live_namespace_separated": mode == "PAPER",
        "live_key_loaded": False,
        "binance_live_touched": False,
        "strategy_promotion_attempted": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "primary_blocker_code": select_primary_blocker(blockers),
        "blockers": blockers,
        "dry_run_hash": "",
    }
    report["dry_run_hash"] = upbit_paper_dry_run_hash(report)
    return report


def validate_upbit_paper_dry_run_report(
    report: dict[str, Any],
    allowed_blockers: set[str] | None = None,
) -> UpbitPaperDryRunValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "paper_run_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "public_data_source",
        "public_data_loaded",
        "public_market_data",
        "symbol_rule_status",
        "fee_model_status",
        "slippage_model_status",
        "fee_rate",
        "slippage_bps",
        "paper_broker_status",
        "paper_order_id",
        "paper_order_submitted",
        "final_decision",
        "no_trade_reasons",
        "entry_reasons",
        "paper_ledger_events",
        "paper_ledger_head_hash",
        "paper_ledger_write_status",
        "paper_live_namespace_separated",
        "live_key_loaded",
        "binance_live_touched",
        "strategy_promotion_attempted",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "dry_run_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperDryRunValidationResult("FAIL", f"paper dry-run report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_DRY_RUN_SCHEMA_ID:
        return UpbitPaperDryRunValidationResult("FAIL", "paper dry-run schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("dry_run_hash") != upbit_paper_dry_run_hash(report):
        return UpbitPaperDryRunValidationResult("FAIL", "paper dry-run hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperDryRunValidationResult("BLOCKED", "paper dry-run scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_key_loaded") or report.get("binance_live_touched") or report.get("strategy_promotion_attempted"):
        return UpbitPaperDryRunValidationResult("BLOCKED", "MVP-2 paper dry-run attempted forbidden live or promotion behavior", "LIVE_FINAL_GUARD_FAILED")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("can_submit_order"):
        return UpbitPaperDryRunValidationResult("BLOCKED", "paper dry-run attempted to create live or order permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("order_adapter_called"):
        return UpbitPaperDryRunValidationResult("BLOCKED", "paper dry-run cannot call live order adapter", "LIVE_FINAL_GUARD_FAILED")
    if report.get("paper_live_namespace_separated") is not True:
        return UpbitPaperDryRunValidationResult("BLOCKED", "paper/live namespace separation is missing", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("final_decision") not in SAFE_FINAL_DECISIONS:
        return UpbitPaperDryRunValidationResult("BLOCKED", "paper dry-run final_decision is unknown", "LIVE_FINAL_GUARD_FAILED")

    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return UpbitPaperDryRunValidationResult("FAIL", "paper dry-run blockers must be an array", "SCHEMA_IDENTITY_MISMATCH")
    for blocker in blockers:
        code = blocker.get("code") if isinstance(blocker, dict) else None
        if allowed_blockers is not None and code not in allowed_blockers:
            return UpbitPaperDryRunValidationResult("FAIL", f"unknown paper dry-run blocker: {code}", "UNKNOWN_BLOCKED")
    primary = report.get("primary_blocker_code")
    blocker_codes = {blocker.get("code") for blocker in blockers if isinstance(blocker, dict)}
    if blockers and primary not in blocker_codes:
        return UpbitPaperDryRunValidationResult("BLOCKED", "primary blocker must match blockers", primary or "UNKNOWN_BLOCKED")
    if not blockers and primary is not None:
        return UpbitPaperDryRunValidationResult("FAIL", "primary blocker set without blockers", "LIVE_FINAL_GUARD_FAILED")

    market_data = report.get("public_market_data")
    data_status, data_blocker, data_message = validate_upbit_public_market_data(
        market_data,
        symbol=report["symbol"],
        session_id=report["session_id"],
    )
    if data_status != "PASS":
        return UpbitPaperDryRunValidationResult("BLOCKED", data_message, data_blocker or "DATA_UNAVAILABLE")

    if report.get("symbol_rule_status") != "PASS" or report.get("fee_model_status") != "PASS" or report.get("slippage_model_status") != "PASS":
        if not blockers:
            return UpbitPaperDryRunValidationResult("BLOCKED", "blocked paper dry-run component lacks blocker", "UNKNOWN_BLOCKED")

    ledger_events = report.get("paper_ledger_events")
    if report.get("paper_order_submitted"):
        if report.get("paper_order_id") is None:
            return UpbitPaperDryRunValidationResult("FAIL", "paper order submitted without paper_order_id", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("final_decision") != "ENTER_LONG":
            return UpbitPaperDryRunValidationResult("BLOCKED", "paper order submitted without paper entry decision", "LIVE_FINAL_GUARD_FAILED")
        if report.get("paper_ledger_write_status") != "WRITTEN":
            return UpbitPaperDryRunValidationResult("BLOCKED", "paper order requires paper ledger write", "LEDGER_UNAVAILABLE")
        status, blocker, message = validate_upbit_paper_ledger(ledger_events)
        if status != "PASS":
            return UpbitPaperDryRunValidationResult(status, message, blocker)
        if report.get("paper_ledger_head_hash") != ledger_events[-1]["event_hash"]:
            return UpbitPaperDryRunValidationResult("FAIL", "paper ledger head hash mismatch", "LEDGER_INTEGRITY_FAIL")
        if not report.get("entry_reasons"):
            return UpbitPaperDryRunValidationResult("BLOCKED", "paper entry lacks entry reason logging", "MEASUREMENT_MISSING")
    else:
        if ledger_events:
            return UpbitPaperDryRunValidationResult("BLOCKED", "no-trade dry-run cannot write order ledger events", "LIVE_FINAL_GUARD_FAILED")
        if report.get("paper_ledger_write_status") not in {"SKIPPED_NO_TRADE", "BLOCKED"}:
            return UpbitPaperDryRunValidationResult("FAIL", "paper ledger status inconsistent with no order", "SCHEMA_IDENTITY_MISMATCH")
        if not report.get("no_trade_reasons"):
            return UpbitPaperDryRunValidationResult("BLOCKED", "no-trade reason logging is required", "MEASUREMENT_MISSING")

    if report.get("paper_broker_status") == "PASS" and blockers:
        return UpbitPaperDryRunValidationResult("BLOCKED", "paper broker PASS cannot carry blockers", primary or "UNKNOWN_BLOCKED")
    return UpbitPaperDryRunValidationResult("PASS", "Upbit paper dry-run is scoped, simulated, ledger-backed, and live-blocked", None)
