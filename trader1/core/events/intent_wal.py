from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


INTENT_WAL_EVENT_SCHEMA_ID = "trader1.intent_wal_event.v1"
HEX_CHARS = set("0123456789abcdefABCDEF")


@dataclass(frozen=True)
class IntentWalValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def intent_wal_event_hash(event: dict[str, Any]) -> str:
    payload = dict(event)
    payload.pop("wal_event_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in HEX_CHARS for char in value)


def build_intent_wal_event(
    *,
    wal_event_id: str,
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "PAPER",
    session_id: str = "mvp2_restart_recovery",
    intent_id: str,
    client_order_id: str,
    symbol: str,
    side: str,
    source_ledger_event_hash: str,
    previous_wal_hash: str | None = None,
) -> dict[str, Any]:
    event = {
        "schema_id": INTENT_WAL_EVENT_SCHEMA_ID,
        "wal_event_id": wal_event_id,
        "created_at_utc": utc_now(),
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "intent_id": intent_id,
        "client_order_id": client_order_id,
        "symbol": symbol,
        "side": side,
        "source_ledger_event_hash": source_ledger_event_hash,
        "previous_wal_hash": previous_wal_hash,
        "paper_live_namespace_separated": mode == "PAPER",
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "wal_event_hash": "",
    }
    event["wal_event_hash"] = intent_wal_event_hash(event)
    return event


def build_intent_wal_from_ledger_events(ledger_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wal_events: list[dict[str, Any]] = []
    previous_wal_hash: str | None = None
    for index, ledger_event in enumerate(ledger_events, start=1):
        intent_id = ledger_event.get("intent_id")
        client_order_id = ledger_event.get("client_order_id")
        if not intent_id or not client_order_id:
            continue
        wal_event = build_intent_wal_event(
            wal_event_id=f"{ledger_event['session_id']}-wal-{index}",
            exchange=ledger_event["exchange"],
            market_type=ledger_event["market_type"],
            mode=ledger_event["mode"],
            session_id=ledger_event["session_id"],
            intent_id=intent_id,
            client_order_id=client_order_id,
            symbol=ledger_event.get("symbol") or "UNKNOWN",
            side=ledger_event.get("side") or "UNKNOWN",
            source_ledger_event_hash=ledger_event["event_hash"],
            previous_wal_hash=previous_wal_hash,
        )
        previous_wal_hash = wal_event["wal_event_hash"]
        wal_events.append(wal_event)
    return wal_events


def validate_intent_wal_event(event: dict[str, Any]) -> IntentWalValidationResult:
    required = {
        "schema_id",
        "wal_event_id",
        "created_at_utc",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "intent_id",
        "client_order_id",
        "symbol",
        "side",
        "source_ledger_event_hash",
        "previous_wal_hash",
        "paper_live_namespace_separated",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "order_adapter_called",
        "wal_event_hash",
    }
    missing = sorted(required - set(event))
    if missing:
        return IntentWalValidationResult("FAIL", f"intent WAL event missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if event.get("schema_id") != INTENT_WAL_EVENT_SCHEMA_ID:
        return IntentWalValidationResult("FAIL", "intent WAL event schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    for field in ("wal_event_id", "created_at_utc", "session_id", "intent_id", "client_order_id", "symbol", "side"):
        if not _is_non_empty_string(event.get(field)):
            return IntentWalValidationResult("FAIL", f"intent WAL event has blank required field: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if not _is_sha256_hex(event.get("source_ledger_event_hash")):
        return IntentWalValidationResult("FAIL", "intent WAL source ledger hash is not a sha256 hex value", "LEDGER_INTEGRITY_FAIL")
    previous_wal_hash = event.get("previous_wal_hash")
    if previous_wal_hash is not None and not _is_sha256_hex(previous_wal_hash):
        return IntentWalValidationResult("FAIL", "intent WAL previous hash is not a sha256 hex value", "LEDGER_INTEGRITY_FAIL")
    if event.get("wal_event_hash") != intent_wal_event_hash(event):
        return IntentWalValidationResult("FAIL", "intent WAL hash mismatch", "LEDGER_INTEGRITY_FAIL")
    if event.get("exchange") != "UPBIT" or event.get("market_type") != "KRW_SPOT" or event.get("mode") != "PAPER":
        return IntentWalValidationResult("BLOCKED", "MVP-2 intent WAL is scoped to UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if event.get("live_key_loaded") or event.get("live_order_ready") or event.get("live_order_allowed") or event.get("can_live_trade") or event.get("can_submit_order"):
        return IntentWalValidationResult("BLOCKED", "intent WAL attempted to create live/order permission", "LIVE_FINAL_GUARD_FAILED")
    if event.get("order_adapter_called"):
        return IntentWalValidationResult("BLOCKED", "intent WAL cannot call an order adapter", "LIVE_FINAL_GUARD_FAILED")
    if event.get("paper_live_namespace_separated") is not True:
        return IntentWalValidationResult("BLOCKED", "intent WAL lacks paper/live namespace separation", "SNAPSHOT_SCOPE_MISMATCH")
    if not _is_non_empty_string(event.get("intent_id")) or not _is_non_empty_string(event.get("client_order_id")):
        return IntentWalValidationResult("BLOCKED", "intent WAL event lacks idempotency identifiers", "RECONCILIATION_REQUIRED")
    return IntentWalValidationResult("PASS", "intent WAL event is hash-linked and paper-scoped", None)


def validate_intent_wal_chain(events: list[dict[str, Any]]) -> IntentWalValidationResult:
    if not events:
        return IntentWalValidationResult("BLOCKED", "intent WAL is unavailable", "LEDGER_UNAVAILABLE")
    expected_previous: str | None = None
    first_scope: tuple[Any, Any, Any, Any] | None = None
    seen_ids: set[str] = set()
    seen_source_ledger_hashes: set[str] = set()
    for event in events:
        result = validate_intent_wal_event(event)
        if result.status != "PASS":
            return result
        scope = (event.get("exchange"), event.get("market_type"), event.get("mode"), event.get("session_id"))
        if first_scope is None:
            first_scope = scope
        elif scope != first_scope:
            return IntentWalValidationResult("BLOCKED", "cross-scope intent WAL chain is forbidden", "SNAPSHOT_SCOPE_MISMATCH")
        if event.get("previous_wal_hash") != expected_previous:
            return IntentWalValidationResult("FAIL", "intent WAL previous hash chain mismatch", "LEDGER_INTEGRITY_FAIL")
        wal_event_id = str(event.get("wal_event_id"))
        if wal_event_id in seen_ids:
            return IntentWalValidationResult("BLOCKED", "duplicate intent WAL event id requires reconciliation", "RECONCILIATION_REQUIRED")
        seen_ids.add(wal_event_id)
        source_ledger_hash = str(event.get("source_ledger_event_hash"))
        if source_ledger_hash in seen_source_ledger_hashes:
            return IntentWalValidationResult("BLOCKED", "duplicate source ledger event in intent WAL requires reconciliation", "RECONCILIATION_REQUIRED")
        seen_source_ledger_hashes.add(source_ledger_hash)
        expected_previous = event["wal_event_hash"]
    return IntentWalValidationResult("PASS", "intent WAL chain is append-auditable and namespace-scoped", None)
