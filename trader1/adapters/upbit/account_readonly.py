from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.runtime.readiness.readiness_surface import blocker_object


READ_ONLY_ACCOUNT_SCHEMA_ID = "trader1.read_only_account_snapshot.v1"


@dataclass(frozen=True)
class ReadOnlyAccountSnapshotResult:
    status: str
    message: str
    blocker_code: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def read_only_account_snapshot_hash(snapshot: dict[str, Any]) -> str:
    payload = dict(snapshot)
    payload.pop("snapshot_hash", None)
    return _sha256_json(payload)


def build_read_only_account_snapshot(
    *,
    authority: dict[str, str],
    snapshot_id: str = "mvp4-upbit-read-only-account-snapshot",
    session_id: str = "mvp4_upbit_live_review",
    credential_loaded: bool = False,
    private_api_called: bool = False,
) -> dict[str, Any]:
    status = "PASS" if credential_loaded and private_api_called else "UNVERIFIED"
    primary = None if status == "PASS" else "API_UNVERIFIED"
    blockers = [] if primary is None else [blocker_object(primary, source_contract_id="REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD")]
    snapshot = {
        "schema_id": READ_ONLY_ACCOUNT_SCHEMA_ID,
        "snapshot_id": snapshot_id,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "READ_ONLY",
        "session_id": session_id,
        "account_snapshot_status": status,
        "balance_snapshot_status": status,
        "position_snapshot_status": status,
        "open_order_snapshot_status": status,
        "balances": [],
        "positions": [],
        "open_orders": [],
        "credential_loaded": credential_loaded,
        "private_api_called": private_api_called,
        "withdrawal_permission_detected": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "primary_blocker_code": primary or "API_UNVERIFIED",
        "blockers": blockers,
        "snapshot_hash": "",
    }
    snapshot["snapshot_hash"] = read_only_account_snapshot_hash(snapshot)
    return snapshot


def validate_read_only_account_snapshot(snapshot: dict[str, Any]) -> ReadOnlyAccountSnapshotResult:
    if snapshot.get("schema_id") != READ_ONLY_ACCOUNT_SCHEMA_ID:
        return ReadOnlyAccountSnapshotResult("FAIL", "read-only account snapshot schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if snapshot.get("snapshot_hash") != read_only_account_snapshot_hash(snapshot):
        return ReadOnlyAccountSnapshotResult("FAIL", "read-only account snapshot hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if snapshot.get("exchange") != "UPBIT" or snapshot.get("market_type") != "KRW_SPOT" or snapshot.get("mode") != "READ_ONLY":
        return ReadOnlyAccountSnapshotResult("BLOCKED", "read-only account snapshot scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    forbidden = ("live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order", "order_adapter_called")
    if any(snapshot.get(field) is True for field in forbidden):
        return ReadOnlyAccountSnapshotResult("BLOCKED", "read-only account snapshot attempted trading permission", "LIVE_FINAL_GUARD_FAILED")
    if snapshot.get("withdrawal_permission_detected"):
        return ReadOnlyAccountSnapshotResult("BLOCKED", "withdrawal permission detected", "API_UNVERIFIED")
    if snapshot.get("account_snapshot_status") != "PASS":
        return ReadOnlyAccountSnapshotResult("BLOCKED", "read-only account snapshot is not verified", "API_UNVERIFIED")
    return ReadOnlyAccountSnapshotResult("PASS", "read-only account snapshot is scoped and non-trading")
