from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.runtime.readiness.readiness_surface import blocker_object


UPBIT_READ_ONLY_RECONCILIATION_SCHEMA_ID = "trader1.upbit_read_only_reconciliation_path.v1"


@dataclass(frozen=True)
class UpbitReadOnlyReconciliationResult:
    status: str
    message: str
    blocker_code: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def upbit_read_only_reconciliation_path_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("reconciliation_path_hash", None)
    return _sha256_json(payload)


def build_upbit_read_only_reconciliation_path(
    *,
    authority: dict[str, str],
    reconciliation_path_id: str = "mvp4-upbit-read-only-reconciliation-path",
    session_id: str = "mvp4_upbit_live_review",
    account_snapshot_id: str = "mvp4-upbit-read-only-account-snapshot",
    private_stream_health_id: str = "mvp4-upbit-private-stream-health",
    reconciliation_path_status: str = "BLOCKED",
) -> dict[str, Any]:
    primary = None if reconciliation_path_status == "PASS" else "RECONCILIATION_REQUIRED"
    blockers = [] if primary is None else [blocker_object(primary, source_contract_id="REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD")]
    report = {
        "schema_id": UPBIT_READ_ONLY_RECONCILIATION_SCHEMA_ID,
        "reconciliation_path_id": reconciliation_path_id,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "READ_ONLY",
        "session_id": session_id,
        "account_snapshot_id": account_snapshot_id,
        "private_stream_health_id": private_stream_health_id,
        "same_identifier_reconciliation_required": True,
        "reconciliation_path_status": reconciliation_path_status,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_adapter_called": False,
        "primary_blocker_code": primary or "RECONCILIATION_REQUIRED",
        "blockers": blockers,
        "reconciliation_path_hash": "",
    }
    report["reconciliation_path_hash"] = upbit_read_only_reconciliation_path_hash(report)
    return report


def validate_upbit_read_only_reconciliation_path(report: dict[str, Any]) -> UpbitReadOnlyReconciliationResult:
    if report.get("schema_id") != UPBIT_READ_ONLY_RECONCILIATION_SCHEMA_ID:
        return UpbitReadOnlyReconciliationResult("FAIL", "Upbit reconciliation path schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("reconciliation_path_hash") != upbit_read_only_reconciliation_path_hash(report):
        return UpbitReadOnlyReconciliationResult("FAIL", "Upbit reconciliation path hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "READ_ONLY":
        return UpbitReadOnlyReconciliationResult("BLOCKED", "Upbit reconciliation path scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("order_adapter_called"):
        return UpbitReadOnlyReconciliationResult("BLOCKED", "Upbit reconciliation path cannot create live permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("reconciliation_path_status") != "PASS":
        return UpbitReadOnlyReconciliationResult("BLOCKED", "read-only reconciliation path is not PASS", "RECONCILIATION_REQUIRED")
    return UpbitReadOnlyReconciliationResult("PASS", "Upbit read-only reconciliation path is scoped and non-trading")
