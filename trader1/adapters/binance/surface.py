from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


BINANCE_ADAPTER_SURFACE_SCHEMA_ID = "trader1.binance_adapter_surface_report.v1"
BINANCE_SURFACE_BLOCKER = "BINANCE_ADAPTER_SURFACE_ONLY"
BINANCE_FUTURES_BLOCKER = "BINANCE_FUTURES_SURFACE_ONLY"
SUPPORTED_BINANCE_MARKET_TYPES = {"SPOT", "FUTURES_USDT_M"}


@dataclass(frozen=True)
class BinanceAdapterSurfaceValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def binance_adapter_surface_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("report_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def binance_surface_blocker(market_type: str, mode: str) -> tuple[str, str]:
    if market_type == "FUTURES_USDT_M":
        return (
            BINANCE_FUTURES_BLOCKER,
            "Binance FUTURES_USDT_M is registered only as a blocked future MVP surface; paper and live futures runtime remain not implemented.",
        )
    if mode == "LIVE":
        return (
            BINANCE_SURFACE_BLOCKER,
            "Binance live is visible only as a blocked launcher surface; no Binance live adapter is implemented. FUTURES_USDT_M remains blocked and is not root-launchable in MVP-4.",
        )
    return (
        BINANCE_SURFACE_BLOCKER,
        "Binance SPOT is visible only as a surface; no Binance PAPER adapter or broker is implemented yet. FUTURES_USDT_M remains blocked and is not root-launchable in MVP-4.",
    )


def build_binance_adapter_surface_report(
    *,
    market_type: str = "SPOT",
    mode: str = "PAPER",
    session_id: str = "mvp1_binance_paper_launcher",
) -> dict[str, Any]:
    blocker_code, blocker_message = binance_surface_blocker(market_type, mode)
    supported_market_type = market_type in SUPPORTED_BINANCE_MARKET_TYPES
    status = "SURFACE_ONLY" if supported_market_type and mode == "PAPER" and market_type == "SPOT" else "BLOCKED"
    report = {
        "schema_id": BINANCE_ADAPTER_SURFACE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": "BINANCE",
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "adapter_namespace": "trader1.adapters.binance",
        "adapter_status": status,
        "implementation_status": "SURFACE_ONLY",
        "paper_runtime_status": "NOT_IMPLEMENTED",
        "live_runtime_status": "LIVE_BLOCKED",
        "futures_runtime_status": "NOT_IMPLEMENTED" if market_type == "FUTURES_USDT_M" else "NOT_REQUESTED",
        "primary_blocker_code": blocker_code if supported_market_type else "SNAPSHOT_SCOPE_MISMATCH",
        "primary_blocker_message": blocker_message
        if supported_market_type
        else "Unsupported Binance market_type is blocked before any adapter action.",
        "next_operator_action": "Use UPBIT PAPER for current MVP-4 runtime work; implement Binance PAPER only in a later non-live patch.",
        "public_market_data_supported": False,
        "paper_broker_supported": False,
        "private_account_supported": False,
        "live_order_supported": False,
        "futures_usdt_m_supported": False,
        "order_adapter_called": False,
        "private_api_called": False,
        "credentials_loaded": False,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = binance_adapter_surface_hash(report)
    return report


def validate_binance_adapter_surface_report(report: dict[str, Any]) -> BinanceAdapterSurfaceValidationResult:
    if report.get("schema_id") != BINANCE_ADAPTER_SURFACE_SCHEMA_ID:
        return BinanceAdapterSurfaceValidationResult("FAIL", "Binance adapter surface schema mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("report_hash") != binance_adapter_surface_hash(report):
        return BinanceAdapterSurfaceValidationResult("FAIL", "Binance adapter surface hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "BINANCE" or report.get("market_type") not in SUPPORTED_BINANCE_MARKET_TYPES:
        return BinanceAdapterSurfaceValidationResult("BLOCKED", "Binance adapter surface scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("implementation_status") != "SURFACE_ONLY":
        return BinanceAdapterSurfaceValidationResult("BLOCKED", "Binance adapter implementation status must remain SURFACE_ONLY", "CONTRACT_GAP_HIGH")
    forbidden_true_fields = (
        "public_market_data_supported",
        "paper_broker_supported",
        "private_account_supported",
        "live_order_supported",
        "futures_usdt_m_supported",
        "order_adapter_called",
        "private_api_called",
        "credentials_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    for field in forbidden_true_fields:
        if report.get(field):
            return BinanceAdapterSurfaceValidationResult("BLOCKED", f"Binance adapter surface attempted forbidden capability: {field}", "LIVE_FINAL_GUARD_FAILED")
    if report.get("display_only") is not True or report.get("dashboard_truth_only") is not True:
        return BinanceAdapterSurfaceValidationResult("BLOCKED", "Binance adapter surface must remain display-only dashboard truth", "LIVE_FINAL_GUARD_FAILED")
    expected_blocker, _ = binance_surface_blocker(str(report.get("market_type")), str(report.get("mode")))
    if report.get("primary_blocker_code") != expected_blocker:
        return BinanceAdapterSurfaceValidationResult("BLOCKED", "Binance adapter surface must expose explicit surface-only blocker", "CONTRACT_GAP_HIGH")
    if report.get("market_type") == "FUTURES_USDT_M" and report.get("futures_runtime_status") != "NOT_IMPLEMENTED":
        return BinanceAdapterSurfaceValidationResult("BLOCKED", "Binance futures runtime must remain explicitly not implemented before MVP-6/7", "CONTRACT_GAP_HIGH")
    return BinanceAdapterSurfaceValidationResult("PASS", "Binance adapter namespace is fail-closed surface-only", None)
