from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trader1.safety.live_order_gate import evaluate_live_order_gate


ENTRY_DECISIONS = {"ENTER_LONG", "ENTER_SHORT"}
AMBIGUOUS_IDEMPOTENCY_STATES = {"PENDING_CONFIRM", "RECONCILE_REQUIRED", "TRANSPORT_AMBIGUOUS"}


@dataclass(frozen=True)
class OrderPathDecision:
    final_decision: str
    order_adapter_called: bool
    live_order_ready: bool
    live_order_allowed: bool
    can_live_trade: bool
    primary_blocker_code: str
    blockers: tuple[str, ...]
    source_kind: str
    idempotency_action: str
    external_submit_attempted: bool
    direct_strategy_order_blocked: bool


def _add_blocker(blockers: list[str], code: str) -> None:
    if code not in blockers:
        blockers.append(code)


def _live_gate_payload(order_request: dict[str, Any]) -> dict[str, Any]:
    payload = dict(order_request.get("live_gate", {}))
    for key in ("live_order_ready", "live_order_allowed", "can_live_trade", "blocker_code", "blockers"):
        if key in order_request and key not in payload:
            payload[key] = order_request[key]
    return payload


def evaluate_live_order_path(order_request: dict[str, Any], order_adapter: Any | None = None) -> OrderPathDecision:
    """Evaluate the MVP-0 live order path without calling an order adapter.

    Strategy output is treated as a signal only. The only acceptable live-entry
    source is a FinalDecision flowing through a single-writer, idempotent path,
    and MVP-0 still blocks before any external order submission.
    """
    source_kind = str(order_request.get("source_kind", "UNKNOWN"))
    final_decision = str(order_request.get("final_decision", "BLOCKED"))
    blockers: list[str] = []

    direct_strategy_order_blocked = source_kind != "FinalDecision" or bool(
        order_request.get("strategy_attempted_exchange_call")
    )
    if direct_strategy_order_blocked:
        _add_blocker(blockers, "CANDIDATE_DIRECT_LIVE_FORBIDDEN")

    forbidden_submit_attempted = any(
        bool(order_request.get(key))
        for key in ("order_adapter_submit_attempted", "external_submit_attempted", "live_order_api_attempted")
    )
    if forbidden_submit_attempted:
        _add_blocker(blockers, "LIVE_FINAL_GUARD_FAILED")

    if bool(order_request.get("network_io_inside_transaction")):
        _add_blocker(blockers, "LIVE_FINAL_GUARD_FAILED")

    if final_decision in ENTRY_DECISIONS:
        if not (order_request.get("client_order_id") or order_request.get("intent_id")):
            _add_blocker(blockers, "LIVE_FINAL_GUARD_FAILED")
        if order_request.get("single_writer_available") is not True:
            _add_blocker(blockers, "LEDGER_UNAVAILABLE")
        if order_request.get("budget_reserved") is not True:
            _add_blocker(blockers, "HARD_TRUTH_MISSING")
        if order_request.get("local_reservation_committed") is not True:
            _add_blocker(blockers, "LIVE_FINAL_GUARD_FAILED")
        if order_request.get("ledger_reconciled") is not True:
            _add_blocker(blockers, "RECONCILIATION_REQUIRED")

    idempotency_state = str(order_request.get("idempotency_state", "NEW"))
    original_identifier = order_request.get("original_client_order_id") or order_request.get("original_intent_id")
    current_identifier = order_request.get("client_order_id") or order_request.get("intent_id")
    if idempotency_state in AMBIGUOUS_IDEMPOTENCY_STATES:
        _add_blocker(blockers, "RECONCILIATION_REQUIRED")

    live_gate_decision = evaluate_live_order_gate(_live_gate_payload(order_request))
    for code in live_gate_decision.blockers:
        _add_blocker(blockers, code)

    if not blockers:
        _add_blocker(blockers, "LIVE_ENABLING_EVIDENCE_MISSING")

    primary = blockers[0]
    final_status = "RECONCILE_REQUIRED" if primary == "RECONCILIATION_REQUIRED" else "BLOCKED"
    return OrderPathDecision(
        final_decision=final_status,
        order_adapter_called=False,
        live_order_ready=False,
        live_order_allowed=False,
        can_live_trade=False,
        primary_blocker_code=primary,
        blockers=tuple(blockers),
        source_kind=source_kind,
        idempotency_action="RECONCILE_SAME_IDENTIFIER_FIRST"
        if "RECONCILIATION_REQUIRED" in blockers
        else "BLOCK_BEFORE_SUBMIT",
        external_submit_attempted=forbidden_submit_attempted,
        direct_strategy_order_blocked=direct_strategy_order_blocked,
    )
