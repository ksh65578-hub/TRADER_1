from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.runtime.readiness.readiness_surface import blocker_object


PRIVATE_STREAM_SCHEMA_ID = "trader1.private_stream_health.v1"


@dataclass(frozen=True)
class PrivateStreamValidationResult:
    status: str
    message: str
    blocker_code: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def private_stream_health_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("stream_health_hash", None)
    return _sha256_json(payload)


def build_private_stream_health(
    *,
    authority: dict[str, str],
    stream_health_id: str = "mvp4-upbit-private-stream-health",
    session_id: str = "mvp4_upbit_live_review",
    private_ws_connected: bool = False,
    reconciliation_fallback_available: bool = True,
) -> dict[str, Any]:
    status = "PASS" if private_ws_connected else "FALLBACK_RECONCILIATION_REQUIRED"
    primary = None if status == "PASS" else "PRIVATE_WS_UNHEALTHY"
    blockers = [] if primary is None else [blocker_object(primary, source_contract_id="REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD")]
    report = {
        "schema_id": PRIVATE_STREAM_SCHEMA_ID,
        "stream_health_id": stream_health_id,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "READ_ONLY",
        "session_id": session_id,
        "private_stream_status": status,
        "private_ws_connected": private_ws_connected,
        "asset_probe_status": "PASS" if private_ws_connected else "UNVERIFIED",
        "order_probe_status": "PASS" if private_ws_connected else "UNVERIFIED",
        "reconciliation_fallback_available": reconciliation_fallback_available,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_adapter_called": False,
        "primary_blocker_code": primary or "PRIVATE_WS_UNHEALTHY",
        "blockers": blockers,
        "stream_health_hash": "",
    }
    report["stream_health_hash"] = private_stream_health_hash(report)
    return report


def validate_private_stream_health(report: dict[str, Any]) -> PrivateStreamValidationResult:
    if report.get("schema_id") != PRIVATE_STREAM_SCHEMA_ID:
        return PrivateStreamValidationResult("FAIL", "private stream schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("stream_health_hash") != private_stream_health_hash(report):
        return PrivateStreamValidationResult("FAIL", "private stream hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "READ_ONLY":
        return PrivateStreamValidationResult("BLOCKED", "private stream scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("order_adapter_called"):
        return PrivateStreamValidationResult("BLOCKED", "private stream health cannot create live permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("private_stream_status") != "PASS":
        if report.get("reconciliation_fallback_available") is True:
            return PrivateStreamValidationResult("BLOCKED", "private stream needs reconciliation fallback before live review can advance", "RECONCILIATION_REQUIRED")
        return PrivateStreamValidationResult("BLOCKED", "private stream is unhealthy", "PRIVATE_WS_UNHEALTHY")
    return PrivateStreamValidationResult("PASS", "private stream health is scoped and read-only")
