from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


LIVE_BLOCKER_MESSAGES = {
    "LIVE_READY_MISSING": "LIVE_READY snapshot missing",
    "SNAPSHOT_SCOPE_MISMATCH": "LIVE_READY scope mismatch",
    "API_UNVERIFIED": "exchange official API validation required",
    "OFFICIAL_API_VERIFICATION_EXPIRED": "exchange official API validation expiry",
    "MANUAL_ORDER_TEST_MISSING": "manual order test evidence required",
    "OPERATOR_APPROVAL_MISSING": "operator approval required",
    "READ_ONLY_BURN_IN_MISSING": "read-only burn-in evidence required",
    "EMERGENCY_FLATTEN_UNAVAILABLE": "emergency flatten preparation required",
    "RECONCILIATION_REQUIRED": "account and internal status synchronization required",
    "BALANCE_MISMATCH": "balance mismatch check required",
    "SYMBOL_RULE_UNVERIFIED": "symbol rule validation required",
    "FEE_MODEL_UNVERIFIED": "fee model validation required",
    "STALE_ORDERBOOK": "orderbook data delay",
    "STALE_TICKER": "ticker data delay",
    "STALE_TRADE_TAPE": "trade tape data delay",
    "RISK_VETO": "risk veto active",
    "KILL_SWITCH_ACTIVE": "kill switch active",
    "LEDGER_UNAVAILABLE": "ledger record not allowed",
    "SOURCE_IDENTITY_MISMATCH": "source identity mismatch",
    "BUNDLE_HYGIENE_FAIL": "bundle hygiene fail",
    "CONTRACT_GAP_HIGH": "HIGH contract gap open",
    "CONTRACT_GAP_CRITICAL": "CRITICAL contract gap open",
    "LIVE_READY_SNAPSHOT_WRITER_UNTESTED": "LIVE_READY snapshot writer validator untested",
    "LIVE_ENABLING_EVIDENCE_MISSING": "live-enabling evidence missing",
    "UNKNOWN_BLOCKED": "unknown blocking condition",
}


@dataclass(frozen=True)
class ReadinessValidationResult:
    status: str
    blocker_code: str | None
    message: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def surface_hash(surface: dict[str, Any]) -> str:
    payload = dict(surface)
    payload.pop("surface_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def _message_for(code: str) -> str:
    return LIVE_BLOCKER_MESSAGES.get(code, LIVE_BLOCKER_MESSAGES["UNKNOWN_BLOCKED"])


def blocker_object(
    code: str,
    *,
    category: str = "READINESS",
    severity: str = "HIGH",
    blocks_start: bool = False,
    blocks_live_order: bool = True,
    detail: str | None = None,
    evidence_id: str | None = None,
    source_contract_id: str | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "category": category,
        "severity": severity,
        "message": _message_for(code),
        "detail": detail,
        "evidence_id": evidence_id,
        "source_contract_id": source_contract_id,
        "blocks_start": blocks_start,
        "blocks_live_order": blocks_live_order,
    }


def build_readiness_surface(
    *,
    authority: dict[str, str],
    exchange: str | None = "UPBIT",
    market_type: str | None = "KRW_SPOT",
    mode: str | None = "LIVE",
    session_id: str | None = None,
    build_id: str | None = None,
    registry_hash: str | None = None,
    schema_bundle_hash: str | None = None,
    source_tree_hash: str | None = None,
    release_package_status: str = "NOT_BUILT",
    bundle_readiness_status: str = "UNKNOWN",
    can_start: bool = False,
    can_collect_data: bool = False,
    can_evaluate_candidates: bool = False,
    can_paper_trade: bool = False,
    can_shadow_evaluate: bool = False,
    can_replay: bool = False,
    can_live_review: bool = False,
    blocker_codes: list[str] | None = None,
) -> dict[str, Any]:
    codes = blocker_codes or ["LIVE_READY_MISSING", "LIVE_READY_SNAPSHOT_WRITER_UNTESTED"]
    blockers = [blocker_object(code, source_contract_id="REQ-MVP0-READINESS-SURFACE") for code in codes]
    primary_code = codes[0] if codes else None
    primary_message = _message_for(primary_code) if primary_code else None
    surface = {
        "schema_id": "trader1.readiness_surface.v1",
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority,
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "build_id": build_id,
        "authority_document": "TRADER_1.md",
        "authority_sha256": authority.get("trader1_sha256"),
        "registry_hash": registry_hash,
        "schema_bundle_hash": schema_bundle_hash,
        "source_tree_hash": source_tree_hash,
        "release_package_status": release_package_status,
        "bundle_readiness_status": bundle_readiness_status,
        "can_start": bool(can_start),
        "can_collect_data": bool(can_collect_data),
        "can_evaluate_candidates": bool(can_evaluate_candidates),
        "can_paper_trade": bool(can_paper_trade),
        "can_shadow_evaluate": bool(can_shadow_evaluate),
        "can_replay": bool(can_replay),
        "can_live_review": bool(can_live_review),
        "can_live_trade": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "start_gate_status": "PASS" if can_start else "BLOCKED",
        "live_trading_status": "BLOCKED",
        "primary_blocker_code": primary_code,
        "primary_blocker_message": primary_message,
        "blockers": blockers,
    }
    surface["surface_hash"] = surface_hash(surface)
    return surface


def render_first_line(surface: dict[str, Any]) -> str:
    mode = surface.get("mode")
    status = surface.get("live_trading_status")
    message = surface.get("primary_blocker_message") or "live orders blocked"
    if status == "BLOCKED":
        return f"LIVE TRADING: BLOCKED - {message}"
    if status == "REVIEW_ONLY":
        return "LIVE TRADING: REVIEW ONLY - live orders blocked"
    if status == "SMALL_LIVE_BURN_IN":
        return f"LIVE TRADING: SMALL BURN-IN - {surface.get('exchange')}/{surface.get('market_type')}"
    if status == "LIVE_ACTIVE":
        return f"LIVE TRADING: ACTIVE - {surface.get('exchange')}/{surface.get('market_type')}"
    if mode == "PAPER":
        return "PAPER TRADING: READY - live orders blocked"
    if mode == "READ_ONLY":
        return "READ ONLY: READY - data collection only"
    return f"LIVE TRADING: BLOCKED - {message}"


def validate_readiness_surface(surface: dict[str, Any], allowed_codes: set[str] | None = None) -> ReadinessValidationResult:
    if surface.get("schema_id") != "trader1.readiness_surface.v1":
        return ReadinessValidationResult("FAIL", "SCHEMA_IDENTITY_MISMATCH", "readiness surface schema_id mismatch")
    if surface.get("surface_hash") != surface_hash(surface):
        return ReadinessValidationResult("FAIL", "SCHEMA_IDENTITY_MISMATCH", "readiness surface hash mismatch")

    blockers = surface.get("blockers", [])
    if not isinstance(blockers, list):
        return ReadinessValidationResult("FAIL", "SCHEMA_IDENTITY_MISMATCH", "readiness blockers must be a list")

    for blocker in blockers:
        code = blocker.get("code") if isinstance(blocker, dict) else None
        if allowed_codes is not None and code not in allowed_codes:
            return ReadinessValidationResult("FAIL", "UNKNOWN_BLOCKED", f"unknown readiness blocker code: {code}")

    live_blockers = [blocker for blocker in blockers if isinstance(blocker, dict) and blocker.get("blocks_live_order") is True]
    if live_blockers and (surface.get("live_order_ready") or surface.get("live_order_allowed")):
        return ReadinessValidationResult("BLOCKED", live_blockers[0]["code"], "live blocker present while live readiness is true")

    if surface.get("live_order_allowed") is True:
        if surface.get("live_order_ready") is not True or surface.get("can_live_trade") is not True:
            return ReadinessValidationResult("BLOCKED", "LIVE_FINAL_GUARD_FAILED", "live_order_allowed requires live_order_ready and can_live_trade")
        if surface.get("live_trading_status") not in {"SMALL_LIVE_BURN_IN", "LIVE_ACTIVE"}:
            return ReadinessValidationResult("BLOCKED", "LIVE_FINAL_GUARD_FAILED", "live_order_allowed requires live trading status")
        if live_blockers or surface.get("primary_blocker_code") is not None or surface.get("primary_blocker_message") is not None:
            return ReadinessValidationResult("BLOCKED", "LIVE_FINAL_GUARD_FAILED", "live_order_allowed cannot have live blockers")

    first_line = render_first_line(surface)
    if first_line in {"READY", "LIVE READY", "BUNDLE READY", "RELEASE READY"}:
        return ReadinessValidationResult("FAIL", "LIVE_FINAL_GUARD_FAILED", "standalone READY display is forbidden")

    if surface.get("can_live_review") is True and surface.get("live_order_ready") is True:
        return ReadinessValidationResult("BLOCKED", "LIVE_FINAL_GUARD_FAILED", "can_live_review must not imply live_order_ready")

    return ReadinessValidationResult("PASS", None, "readiness surface is fail-closed")

