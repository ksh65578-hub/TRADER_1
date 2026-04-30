from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.runtime.readiness.readiness_surface import blocker_object


API_KEY_PERMISSION_SCHEMA_ID = "trader1.api_key_permission_check_report.v1"


@dataclass(frozen=True)
class ApiKeyPermissionValidationResult:
    status: str
    message: str
    blocker_code: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def api_key_permission_check_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("permission_check_hash", None)
    return _sha256_json(payload)


def build_api_key_permission_check_report(
    *,
    authority: dict[str, str],
    permission_check_id: str = "mvp4-upbit-api-key-permission-check",
    api_key_present: bool = False,
    read_permission_verified: bool = False,
    trade_permission_detected: bool = False,
    withdrawal_permission_detected: bool = False,
) -> dict[str, Any]:
    status = "PASS" if api_key_present and read_permission_verified and not withdrawal_permission_detected else "UNVERIFIED"
    primary = None if status == "PASS" else "API_UNVERIFIED"
    blockers = [] if primary is None else [blocker_object(primary, source_contract_id="REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD")]
    report = {
        "schema_id": API_KEY_PERMISSION_SCHEMA_ID,
        "permission_check_id": permission_check_id,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "READ_ONLY",
        "api_key_id_hash": "masked-api-key-id" if api_key_present else None,
        "api_key_present": api_key_present,
        "read_permission_verified": read_permission_verified,
        "trade_permission_detected": trade_permission_detected,
        "withdrawal_permission_detected": withdrawal_permission_detected,
        "permission_check_status": status,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_adapter_called": False,
        "primary_blocker_code": primary or "API_UNVERIFIED",
        "blockers": blockers,
        "permission_check_hash": "",
    }
    report["permission_check_hash"] = api_key_permission_check_hash(report)
    return report


def validate_api_key_permission_check_report(report: dict[str, Any]) -> ApiKeyPermissionValidationResult:
    if report.get("schema_id") != API_KEY_PERMISSION_SCHEMA_ID:
        return ApiKeyPermissionValidationResult("FAIL", "API key permission check schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("permission_check_hash") != api_key_permission_check_hash(report):
        return ApiKeyPermissionValidationResult("FAIL", "API key permission check hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "READ_ONLY":
        return ApiKeyPermissionValidationResult("BLOCKED", "API key permission check scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("order_adapter_called"):
        return ApiKeyPermissionValidationResult("BLOCKED", "API key permission check cannot create live permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("withdrawal_permission_detected"):
        return ApiKeyPermissionValidationResult("BLOCKED", "withdrawal permission is forbidden", "API_UNVERIFIED")
    if report.get("permission_check_status") != "PASS":
        return ApiKeyPermissionValidationResult("BLOCKED", "API key read-only permission is unverified", "API_UNVERIFIED")
    if report.get("trade_permission_detected") and report.get("read_permission_verified") is not True:
        return ApiKeyPermissionValidationResult("BLOCKED", "trade permission cannot substitute for read verification", "API_UNVERIFIED")
    return ApiKeyPermissionValidationResult("PASS", "API key permission check is scoped and non-withdrawal")
