from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


LEDGER_EVENT_SCHEMA_ID = "trader1.ledger_event.v1"
LEDGER_EVENT_TYPES = {
    "ORDER_INTENT_CREATED",
    "BUDGET_RESERVED",
    "ORDER_SUBMIT_STARTED",
    "ORDER_SUBMITTED",
    "ORDER_ACK_RECEIVED",
    "ORDER_OPENED",
    "PARTIAL_FILL_RECEIVED",
    "ORDER_FILLED",
    "ORDER_CANCEL_REQUESTED",
    "ORDER_CANCELED",
    "ORDER_REJECTED",
    "ORDER_EXPIRED",
    "ORDER_RECONCILE_REQUIRED",
    "ORDER_RECONCILED",
    "RESERVATION_RELEASED",
    "LEDGER_CORRECTION_RECORDED",
    "RISK_REDUCTION_ACTION_RECORDED",
}
LEDGER_SOURCES = {"LOCAL", "EXCHANGE_REST", "EXCHANGE_WS", "RECONCILIATION", "OPERATOR", "SYSTEM"}
ENTRY_EVENT_TYPES = {"ORDER_SUBMIT_STARTED", "ORDER_SUBMITTED", "ORDER_ACK_RECEIVED", "ORDER_OPENED"}
SPOT_SHORT_FORBIDDEN = {("UPBIT", "KRW_SPOT"), ("BINANCE", "SPOT")}


@dataclass(frozen=True)
class LedgerValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ledger_event_hash(event: dict[str, Any]) -> str:
    payload = dict(event)
    payload.pop("event_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def build_ledger_event(
    *,
    event_id: str,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    event_type: str,
    source: str,
    dedup_key: str,
    previous_hash: str | None = None,
    event_time_utc: str | None = None,
    exchange_time: str | None = None,
    order_id: str | None = None,
    client_order_id: str | None = None,
    intent_id: str | None = None,
    symbol: str | None = None,
    side: str | None = None,
    quantity: str | None = None,
    price: str | None = None,
    fee_amount: str | None = None,
    fee_asset: str | None = None,
    funding_fee_amount: str | None = None,
    realized_pnl: str | None = None,
    unrealized_pnl: str | None = None,
    balance_delta: dict[str, Any] | None = None,
    position_delta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "schema_id": LEDGER_EVENT_SCHEMA_ID,
        "event_id": event_id,
        "event_time_utc": event_time_utc or utc_now(),
        "exchange_time": exchange_time,
        "mode": mode,
        "exchange": exchange,
        "market_type": market_type,
        "session_id": session_id,
        "event_type": event_type,
        "order_id": order_id,
        "client_order_id": client_order_id,
        "intent_id": intent_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": price,
        "fee_amount": fee_amount,
        "fee_asset": fee_asset,
        "funding_fee_amount": funding_fee_amount,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
        "balance_delta": balance_delta,
        "position_delta": position_delta,
        "source": source,
        "dedup_key": dedup_key,
        "previous_hash": previous_hash,
        "event_hash": "",
    }
    event["event_hash"] = ledger_event_hash(event)
    return event


def build_minimal_intent_chain(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    intent_id: str,
    client_order_id: str,
    symbol: str,
    side: str,
) -> list[dict[str, Any]]:
    intent = build_ledger_event(
        event_id=f"{session_id}-{intent_id}-intent",
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        event_type="ORDER_INTENT_CREATED",
        source="LOCAL",
        dedup_key=f"intent:{intent_id}",
        intent_id=intent_id,
        client_order_id=client_order_id,
        symbol=symbol,
        side=side,
    )
    reservation = build_ledger_event(
        event_id=f"{session_id}-{intent_id}-reserve",
        exchange=exchange,
        market_type=market_type,
        mode=mode,
        session_id=session_id,
        event_type="BUDGET_RESERVED",
        source="LOCAL",
        dedup_key=f"reserve:{intent_id}",
        previous_hash=intent["event_hash"],
        intent_id=intent_id,
        client_order_id=client_order_id,
        symbol=symbol,
        side=side,
    )
    return [intent, reservation]


def validate_ledger_event(event: dict[str, Any]) -> LedgerValidationResult:
    required = {
        "schema_id",
        "event_id",
        "event_time_utc",
        "mode",
        "exchange",
        "market_type",
        "session_id",
        "event_type",
        "source",
        "dedup_key",
        "event_hash",
    }
    missing = sorted(required - set(event))
    if missing:
        return LedgerValidationResult("FAIL", f"ledger event missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if event.get("schema_id") != LEDGER_EVENT_SCHEMA_ID:
        return LedgerValidationResult("FAIL", "ledger event schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if event.get("event_hash") != ledger_event_hash(event):
        return LedgerValidationResult("FAIL", "ledger event hash mismatch", "LEDGER_INTEGRITY_FAIL")
    if event.get("event_type") not in LEDGER_EVENT_TYPES:
        return LedgerValidationResult("BLOCKED", "unknown ledger event type requires reconciliation", "RECONCILIATION_REQUIRED")
    if event.get("source") not in LEDGER_SOURCES:
        return LedgerValidationResult("BLOCKED", "unknown ledger source requires reconciliation", "RECONCILIATION_REQUIRED")
    if event.get("event_type") in ENTRY_EVENT_TYPES and not (event.get("client_order_id") or event.get("intent_id")):
        return LedgerValidationResult("BLOCKED", "entry event missing idempotency identifier", "RECONCILIATION_REQUIRED")
    if (event.get("exchange"), event.get("market_type")) in SPOT_SHORT_FORBIDDEN and event.get("side") == "SELL_SHORT":
        return LedgerValidationResult("BLOCKED", "spot ledger event cannot represent short entry", "LIVE_FINAL_GUARD_FAILED")
    return LedgerValidationResult("PASS", "ledger event is closed and hash-valid", None)


def validate_ledger_chain(events: list[dict[str, Any]]) -> LedgerValidationResult:
    if not events:
        return LedgerValidationResult("BLOCKED", "empty ledger cannot prove execution truth", "LEDGER_UNAVAILABLE")
    seen_event_ids: set[str] = set()
    seen_dedup_keys: set[str] = set()
    seen_semantic_events: set[tuple[str, str | None, str | None, str | None]] = set()
    expected_previous: str | None = None
    first_scope: tuple[Any, Any, Any, Any] | None = None
    for event in events:
        result = validate_ledger_event(event)
        if result.status != "PASS":
            return result
        scope = (event.get("exchange"), event.get("market_type"), event.get("mode"), event.get("session_id"))
        if first_scope is None:
            first_scope = scope
        elif scope != first_scope:
            return LedgerValidationResult("BLOCKED", "cross-scope ledger chain is forbidden", "SNAPSHOT_SCOPE_MISMATCH")
        if event.get("previous_hash") != expected_previous:
            return LedgerValidationResult("FAIL", "ledger previous_hash chain mismatch", "LEDGER_INTEGRITY_FAIL")
        event_id = str(event.get("event_id"))
        if event_id in seen_event_ids:
            return LedgerValidationResult("BLOCKED", "duplicate ledger event_id requires reconciliation", "RECONCILIATION_REQUIRED")
        seen_event_ids.add(event_id)
        dedup_key = str(event.get("dedup_key"))
        if dedup_key in seen_dedup_keys:
            return LedgerValidationResult("BLOCKED", "duplicate ledger dedup_key requires reconciliation", "RECONCILIATION_REQUIRED")
        seen_dedup_keys.add(dedup_key)
        semantic_key = (
            str(event.get("event_type")),
            event.get("intent_id"),
            event.get("client_order_id"),
            event.get("order_id"),
        )
        if (event.get("intent_id") or event.get("client_order_id") or event.get("order_id")) and semantic_key in seen_semantic_events:
            return LedgerValidationResult("BLOCKED", "duplicate semantic ledger event requires reconciliation", "RECONCILIATION_REQUIRED")
        seen_semantic_events.add(semantic_key)
        expected_previous = event["event_hash"]
    return LedgerValidationResult("PASS", "ledger chain is append-auditable and namespace-scoped", None)
