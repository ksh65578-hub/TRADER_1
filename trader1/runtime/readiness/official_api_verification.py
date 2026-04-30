from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.runtime.readiness.readiness_surface import blocker_object


OFFICIAL_API_SCHEMA_ID = "trader1.official_api_verification_report.v1"
PASS_REQUIRED_FACTS = {
    "endpoints",
    "rate_limits",
    "symbol_rules",
    "fee_rules",
    "auth_requirements",
    "permission_requirements",
    "order_constraints",
    "margin_rules_if_futures",
}


@dataclass(frozen=True)
class OfficialApiVerificationResult:
    status: str
    message: str
    blocker_code: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def official_api_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("report_hash", None)
    return _sha256_json(payload)


def _empty_facts() -> dict[str, Any]:
    return {
        "endpoints": {},
        "rate_limits": {},
        "symbol_rules": {},
        "fee_rules": {},
        "auth_requirements": {},
        "permission_requirements": {},
        "order_constraints": {},
        "margin_rules_if_futures": None,
    }


def build_official_api_verification_report(
    *,
    authority: dict[str, str],
    verification_id: str = "mvp4-upbit-official-api-unverified",
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "READ_ONLY",
    result: str = "UNVERIFIED",
    official_sources: list[dict[str, Any]] | None = None,
    facts: dict[str, Any] | None = None,
    expires_at_utc: str | None = None,
) -> dict[str, Any]:
    primary = None if result == "PASS" else "API_UNVERIFIED"
    blockers = [] if primary is None else [blocker_object(primary, source_contract_id="REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD")]
    report = {
        "schema_id": OFFICIAL_API_SCHEMA_ID,
        "verification_id": verification_id,
        "generated_at_utc": utc_now(),
        "verified_at_utc": utc_now(),
        "expires_at_utc": expires_at_utc,
        "project_id": "TRADER_1",
        "authority": authority,
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "verified_by": "AI_COMPILER_SCAFFOLD",
        "verification_method": "manual_crosscheck",
        "official_sources": official_sources or [],
        "facts": facts or _empty_facts(),
        "result": result,
        "primary_blocker_code": primary,
        "blockers": blockers,
        "invalidated_by": [] if result == "PASS" else ["OFFICIAL_API_VERIFICATION_MISSING"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "report_hash": "",
        "signature": None,
    }
    report["report_hash"] = official_api_report_hash(report)
    return report


def _expired(expires_at_utc: str | None) -> bool:
    if not expires_at_utc:
        return True
    try:
        normalized = expires_at_utc.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized) <= datetime.now(timezone.utc)
    except ValueError:
        return True


def validate_official_api_verification_report(report: dict[str, Any]) -> OfficialApiVerificationResult:
    if report.get("schema_id") != OFFICIAL_API_SCHEMA_ID:
        return OfficialApiVerificationResult("FAIL", "official API report schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("report_hash") != official_api_report_hash(report):
        return OfficialApiVerificationResult("FAIL", "official API report hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return OfficialApiVerificationResult("BLOCKED", "official API report scope must be UPBIT/KRW_SPOT for MVP-4", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("mode") not in {"READ_ONLY", "LIVE"}:
        return OfficialApiVerificationResult("BLOCKED", "official API verification must be read-only or live-preflight scoped", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade"):
        return OfficialApiVerificationResult("BLOCKED", "official API verification cannot create live permission", "LIVE_FINAL_GUARD_FAILED")

    result = report.get("result")
    if result == "STALE" or (result == "PASS" and _expired(report.get("expires_at_utc"))):
        return OfficialApiVerificationResult("BLOCKED", "official API verification is stale or expired", "OFFICIAL_API_VERIFICATION_EXPIRED")
    if result != "PASS":
        return OfficialApiVerificationResult("BLOCKED", "official API verification is not PASS", "API_UNVERIFIED")

    if not report.get("official_sources"):
        return OfficialApiVerificationResult("BLOCKED", "official API PASS requires official sources", "API_UNVERIFIED")
    facts = report.get("facts")
    if not isinstance(facts, dict) or PASS_REQUIRED_FACTS - set(facts):
        return OfficialApiVerificationResult("BLOCKED", "official API PASS requires all fact groups", "API_UNVERIFIED")
    empty_fact_groups = [key for key in PASS_REQUIRED_FACTS - {"margin_rules_if_futures"} if not facts.get(key)]
    if empty_fact_groups:
        return OfficialApiVerificationResult("BLOCKED", f"official API PASS has empty fact groups: {empty_fact_groups}", "API_UNVERIFIED")
    return OfficialApiVerificationResult("PASS", "official API verification report is scoped and fresh")
