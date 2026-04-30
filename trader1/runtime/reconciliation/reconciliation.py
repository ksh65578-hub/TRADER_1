from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


RECONCILIATION_REPORT_SCHEMA_ID = "trader1.reconciliation_report.v1"
RECONCILIATION_STATUSES = {"PASS", "FAIL", "STALE", "MISMATCH", "UNKNOWN", "NOT_APPLICABLE"}
SAFE_FINAL_DECISIONS = {"NO_TRADE", "SAFE_MODE", "RECONCILE_REQUIRED", "BLOCKED"}
LIVE_PERMISSION_KEYS = {"live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order"}
SCOPE_FIELDS = ("exchange", "market_type", "mode", "session_id")


@dataclass(frozen=True)
class ReconciliationValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def reconciliation_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("reconciliation_hash", None)
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest().upper()


def snapshot_hash(snapshot: dict[str, Any] | None) -> str | None:
    if snapshot is None:
        return None
    return hashlib.sha256(_canonical(snapshot).encode("utf-8")).hexdigest().upper()


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _snapshot_stale(snapshot: dict[str, Any] | None) -> bool:
    if snapshot is None:
        return False
    return bool(snapshot.get("is_stale")) or snapshot.get("snapshot_status") == "STALE"


def _scope_mismatch(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    exchange_snapshot: dict[str, Any] | None,
    internal_state: dict[str, Any] | None,
) -> bool:
    expected = {
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
    }
    for snapshot in (exchange_snapshot, internal_state):
        if not isinstance(snapshot, dict):
            continue
        for field, expected_value in expected.items():
            actual = snapshot.get(field)
            if actual is not None and actual != expected_value:
                return True
    return False


def _business_view(snapshot: dict[str, Any] | None) -> dict[str, Any]:
    if not snapshot:
        return {}
    ignored = {
        "snapshot_id",
        "snapshot_hash",
        "snapshot_status",
        "generated_at_utc",
        "created_at_utc",
        "updated_at_utc",
        "is_stale",
    }
    return {key: value for key, value in snapshot.items() if key not in ignored}


def _mismatches(exchange_snapshot: dict[str, Any] | None, internal_state: dict[str, Any] | None) -> list[dict[str, Any]]:
    exchange_view = _business_view(exchange_snapshot)
    internal_view = _business_view(internal_state)
    rows: list[dict[str, Any]] = []
    for field in sorted(set(exchange_view) | set(internal_view)):
        exchange_value = exchange_view.get(field)
        internal_value = internal_view.get(field)
        if exchange_value != internal_value:
            rows.append(
                {
                    "field": field,
                    "exchange_value": exchange_value,
                    "internal_value": internal_value,
                    "severity": "HIGH",
                    "message": "exchange snapshot and internal state disagree",
                }
            )
    return rows


def _contains_live_permission(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in LIVE_PERMISSION_KEYS and item is True:
                return True
            if key == "live_trading_status" and item == "LIVE_ACTIVE":
                return True
            if _contains_live_permission(item):
                return True
    if isinstance(value, list):
        return any(_contains_live_permission(item) for item in value)
    return False


def build_reconciliation_report(
    *,
    reconciliation_id: str,
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "PAPER",
    session_id: str = "mvp1_reconciliation",
    account_snapshot_id: str | None = "account-snapshot-1",
    ledger_head_hash: str | None = "LEDGER_HEAD_NOT_LIVE",
    exchange_snapshot: dict[str, Any] | None = None,
    internal_state: dict[str, Any] | None = None,
    fresh: bool = True,
) -> dict[str, Any]:
    if exchange_snapshot is None:
        exchange_snapshot = {
            "exchange": exchange,
            "market_type": market_type,
            "mode": mode,
            "session_id": session_id,
            "balances": {},
            "positions": [],
            "open_orders": [],
        }
    if internal_state is None:
        internal_state = {
            "exchange": exchange,
            "market_type": market_type,
            "mode": mode,
            "session_id": session_id,
            "balances": {},
            "positions": [],
            "open_orders": [],
        }

    blockers: list[dict[str, str]] = []
    mismatches: list[dict[str, Any]] = []
    status = "PASS"
    final_decision = "NO_TRADE"

    if exchange_snapshot is None or internal_state is None or not account_snapshot_id or not ledger_head_hash:
        status = "UNKNOWN"
        final_decision = "RECONCILE_REQUIRED"
        blockers.append(_blocker("HARD_TRUTH_MISSING", "reconciliation hard truth is missing", "CRITICAL"))
    elif _scope_mismatch(
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        exchange_snapshot=exchange_snapshot,
        internal_state=internal_state,
    ):
        status = "MISMATCH"
        final_decision = "RECONCILE_REQUIRED"
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "reconciliation snapshots are outside requested scope", "CRITICAL"))
    elif not fresh or _snapshot_stale(exchange_snapshot) or _snapshot_stale(internal_state):
        status = "STALE"
        final_decision = "RECONCILE_REQUIRED"
        blockers.append(_blocker("RECONCILIATION_REQUIRED", "reconciliation snapshots are stale", "HIGH"))
    else:
        mismatches = _mismatches(exchange_snapshot, internal_state)
        if mismatches:
            status = "MISMATCH"
            final_decision = "RECONCILE_REQUIRED"
            blockers.append(_blocker("RECONCILIATION_REQUIRED", "exchange and internal state require reconciliation", "HIGH"))

    report = {
        "schema_id": RECONCILIATION_REPORT_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "reconciliation_id": reconciliation_id,
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "account_snapshot_id": account_snapshot_id,
        "ledger_head_hash": ledger_head_hash,
        "exchange_snapshot_hash": snapshot_hash(exchange_snapshot),
        "internal_state_hash": snapshot_hash(internal_state),
        "exchange_snapshot": exchange_snapshot,
        "internal_state": internal_state,
        "reconciliation_status": status,
        "final_decision": final_decision,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "mismatches": mismatches,
        "new_entry_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "reconciliation_hash": "",
    }
    report["reconciliation_hash"] = reconciliation_report_hash(report)
    return report


def validate_reconciliation_report(
    report: dict[str, Any],
    allowed_blockers: set[str] | None = None,
) -> ReconciliationValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "reconciliation_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "account_snapshot_id",
        "ledger_head_hash",
        "exchange_snapshot_hash",
        "internal_state_hash",
        "exchange_snapshot",
        "internal_state",
        "reconciliation_status",
        "final_decision",
        "primary_blocker_code",
        "blockers",
        "mismatches",
        "new_entry_allowed",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "order_adapter_called",
        "reconciliation_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ReconciliationValidationResult("FAIL", f"reconciliation report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != RECONCILIATION_REPORT_SCHEMA_ID:
        return ReconciliationValidationResult("FAIL", "reconciliation schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("reconciliation_hash") != reconciliation_report_hash(report):
        return ReconciliationValidationResult("FAIL", "reconciliation hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("project_id") != "TRADER_1":
        return ReconciliationValidationResult("FAIL", "reconciliation project_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("reconciliation_status") not in RECONCILIATION_STATUSES:
        return ReconciliationValidationResult("FAIL", "unknown reconciliation status", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("final_decision") not in SAFE_FINAL_DECISIONS:
        return ReconciliationValidationResult("BLOCKED", "reconciliation final_decision is not fail-closed", "LIVE_FINAL_GUARD_FAILED")
    if report.get("new_entry_allowed") is not False:
        return ReconciliationValidationResult("BLOCKED", "MVP-1 reconciliation cannot allow new entries", "LIVE_FINAL_GUARD_FAILED")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("can_submit_order"):
        return ReconciliationValidationResult("BLOCKED", "reconciliation attempted to create live or order permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("order_adapter_called"):
        return ReconciliationValidationResult("BLOCKED", "reconciliation scaffold cannot call order adapter", "LIVE_FINAL_GUARD_FAILED")
    if _contains_live_permission(report.get("exchange_snapshot")) or _contains_live_permission(report.get("internal_state")):
        return ReconciliationValidationResult("BLOCKED", "reconciliation inputs attempted to create live permission", "LIVE_FINAL_GUARD_FAILED")

    blockers = report.get("blockers")
    mismatches = report.get("mismatches")
    if not isinstance(blockers, list) or not isinstance(mismatches, list):
        return ReconciliationValidationResult("FAIL", "reconciliation blockers and mismatches must be arrays", "SCHEMA_IDENTITY_MISMATCH")
    for blocker in blockers:
        code = blocker.get("code") if isinstance(blocker, dict) else None
        if allowed_blockers is not None and code not in allowed_blockers:
            return ReconciliationValidationResult("FAIL", f"unknown reconciliation blocker: {code}", "UNKNOWN_BLOCKED")

    primary = report.get("primary_blocker_code")
    blocker_codes = {blocker.get("code") for blocker in blockers if isinstance(blocker, dict)}
    if blockers and primary not in blocker_codes:
        return ReconciliationValidationResult("BLOCKED", "primary reconciliation blocker must match blockers", primary or "UNKNOWN_BLOCKED")
    if not blockers and primary is not None:
        return ReconciliationValidationResult("FAIL", "primary blocker set without blockers", "LIVE_FINAL_GUARD_FAILED")

    exchange_snapshot = report.get("exchange_snapshot")
    internal_state = report.get("internal_state")
    if report.get("exchange_snapshot_hash") != snapshot_hash(exchange_snapshot):
        return ReconciliationValidationResult("FAIL", "exchange snapshot hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("internal_state_hash") != snapshot_hash(internal_state):
        return ReconciliationValidationResult("FAIL", "internal state hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    hard_truth_missing = (
        exchange_snapshot is None
        or internal_state is None
        or not report.get("account_snapshot_id")
        or not report.get("ledger_head_hash")
    )
    scope_mismatch = _scope_mismatch(
        exchange=str(report.get("exchange")),
        market_type=str(report.get("market_type")),
        mode=str(report.get("mode")),
        session_id=str(report.get("session_id")),
        exchange_snapshot=exchange_snapshot,
        internal_state=internal_state,
    )
    snapshot_stale = _snapshot_stale(exchange_snapshot) or _snapshot_stale(internal_state)
    recomputed_mismatches = _mismatches(exchange_snapshot, internal_state)
    if hard_truth_missing:
        if report.get("reconciliation_status") == "PASS" or primary != "HARD_TRUTH_MISSING":
            return ReconciliationValidationResult("BLOCKED", "missing reconciliation hard truth cannot be reported as PASS", "HARD_TRUTH_MISSING")
    elif scope_mismatch:
        if report.get("reconciliation_status") == "PASS" or primary != "SNAPSHOT_SCOPE_MISMATCH":
            return ReconciliationValidationResult("BLOCKED", "snapshot scope mismatch cannot be reported as PASS", "SNAPSHOT_SCOPE_MISMATCH")
    elif snapshot_stale:
        if report.get("reconciliation_status") == "PASS" or primary != "RECONCILIATION_REQUIRED":
            return ReconciliationValidationResult("BLOCKED", "stale reconciliation input cannot be reported as PASS", "RECONCILIATION_REQUIRED")
    elif recomputed_mismatches:
        reported_fields = {item.get("field") for item in mismatches if isinstance(item, dict)}
        expected_fields = {item["field"] for item in recomputed_mismatches}
        if report.get("reconciliation_status") == "PASS" or not expected_fields.issubset(reported_fields):
            return ReconciliationValidationResult("BLOCKED", "snapshot mismatch cannot be reported as PASS or without mismatch details", "RECONCILIATION_REQUIRED")

    status = report.get("reconciliation_status")
    if status == "PASS":
        if blockers or mismatches:
            return ReconciliationValidationResult("BLOCKED", "PASS reconciliation cannot carry blockers or mismatches", "RECONCILIATION_REQUIRED")
        if report.get("final_decision") != "NO_TRADE":
            return ReconciliationValidationResult("BLOCKED", "MVP-1 PASS reconciliation still resolves to NO_TRADE", "LIVE_FINAL_GUARD_FAILED")
    elif status in {"STALE", "MISMATCH", "UNKNOWN", "FAIL"}:
        if not blockers:
            return ReconciliationValidationResult("BLOCKED", "non-pass reconciliation must expose a blocker", "RECONCILIATION_REQUIRED")
        if report.get("final_decision") not in {"RECONCILE_REQUIRED", "SAFE_MODE", "BLOCKED"}:
            return ReconciliationValidationResult("BLOCKED", "non-pass reconciliation must be fail-closed", "RECONCILIATION_REQUIRED")
        if status == "MISMATCH" and primary != "SNAPSHOT_SCOPE_MISMATCH" and not mismatches:
            return ReconciliationValidationResult("BLOCKED", "state mismatch requires mismatch details", "RECONCILIATION_REQUIRED")
    return ReconciliationValidationResult("PASS", "reconciliation report is scoped, hash-valid, and fail-closed", None)
