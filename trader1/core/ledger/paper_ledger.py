from __future__ import annotations

from typing import Any

from trader1.runtime.ledger.execution_ledger import build_ledger_event, build_minimal_intent_chain, validate_ledger_chain


def build_upbit_paper_intent_chain(
    *,
    session_id: str,
    symbol: str,
    intent_id: str,
    client_order_id: str,
    side: str = "BUY",
) -> list[dict[str, Any]]:
    return build_minimal_intent_chain(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        intent_id=intent_id,
        client_order_id=client_order_id,
        symbol=symbol,
        side=side,
    )


def build_upbit_paper_fill_chain(
    *,
    session_id: str,
    symbol: str,
    intent_id: str,
    client_order_id: str,
    side: str,
    quantity: str,
    price: str,
    fee_amount: str,
) -> list[dict[str, Any]]:
    events = build_upbit_paper_intent_chain(
        session_id=session_id,
        symbol=symbol,
        intent_id=intent_id,
        client_order_id=client_order_id,
        side=side,
    )
    order_id = f"PAPER-{client_order_id}"
    submit_started = build_ledger_event(
        event_id=f"{session_id}-{client_order_id}-submit-started",
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        event_type="ORDER_SUBMIT_STARTED",
        source="LOCAL",
        dedup_key=f"paper-submit-started:{client_order_id}",
        previous_hash=events[-1]["event_hash"],
        intent_id=intent_id,
        client_order_id=client_order_id,
        order_id=order_id,
        symbol=symbol,
        side=side,
    )
    submitted = build_ledger_event(
        event_id=f"{session_id}-{client_order_id}-submitted",
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        event_type="ORDER_SUBMITTED",
        source="LOCAL",
        dedup_key=f"paper-submitted:{client_order_id}",
        previous_hash=submit_started["event_hash"],
        intent_id=intent_id,
        client_order_id=client_order_id,
        order_id=order_id,
        symbol=symbol,
        side=side,
    )
    ack = build_ledger_event(
        event_id=f"{session_id}-{client_order_id}-ack",
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        event_type="ORDER_ACK_RECEIVED",
        source="LOCAL",
        dedup_key=f"paper-ack:{client_order_id}",
        previous_hash=submitted["event_hash"],
        intent_id=intent_id,
        client_order_id=client_order_id,
        order_id=order_id,
        symbol=symbol,
        side=side,
    )
    filled = build_ledger_event(
        event_id=f"{session_id}-{client_order_id}-filled",
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        event_type="ORDER_FILLED",
        source="LOCAL",
        dedup_key=f"paper-filled:{client_order_id}",
        previous_hash=ack["event_hash"],
        intent_id=intent_id,
        client_order_id=client_order_id,
        order_id=order_id,
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        fee_amount=fee_amount,
        fee_asset="KRW",
        balance_delta={"KRW": f"-{fee_amount}"},
        position_delta={"symbol": symbol, "quantity": quantity, "side": side},
    )
    return [*events, submit_started, submitted, ack, filled]


def validate_upbit_paper_ledger(events: list[dict[str, Any]]) -> tuple[str, str | None, str]:
    result = validate_ledger_chain(events)
    if result.status != "PASS":
        return result.status, result.blocker_code, result.message
    for event in events:
        if event.get("exchange") != "UPBIT" or event.get("market_type") != "KRW_SPOT" or event.get("mode") != "PAPER":
            return "BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "paper ledger event scope mismatch"
    return "PASS", None, "paper ledger chain is scoped and hash-linked"
