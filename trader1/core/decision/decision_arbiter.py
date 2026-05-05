from __future__ import annotations


BLOCKER_PRIORITY = [
    "KILL_SWITCH_ACTIVE",
    "LIVE_FINAL_GUARD_FAILED",
    "RECONCILIATION_REQUIRED",
    "LEDGER_INTEGRITY_FAIL",
    "LEDGER_UNAVAILABLE",
    "EXCHANGE_SYNC_REQUIRED",
    "BALANCE_MISMATCH",
    "ORPHAN_POSITION_REVIEW_REQUIRED",
    "ORPHAN_OPEN_ORDER_REVIEW_REQUIRED",
    "SNAPSHOT_SCOPE_MISMATCH",
    "RISK_VETO",
    "DRAWDOWN_FREEZE_ACTIVE",
    "SURVIVAL_LAYER_BLOCKED",
    "POSITION_LIMIT",
    "CLUSTER_RISK",
    "RESOURCE_LIMIT_BLOCK",
    "RESOURCE_LIMIT",
    "DATA_UNAVAILABLE",
    "DATA_QUALITY_INSUFFICIENT",
    "STALE_ORDERBOOK",
    "STALE_TICKER",
    "STALE_TRADE_TAPE",
    "STALE_CANDLE_15M",
    "STALE_CANDLE_60M",
    "STALE_BENCHMARK_CONTEXT",
    "MARKET_CONTEXT_LOAD_TIMEOUT",
    "API_TIMEOUT",
    "WEBSOCKET_GAP",
    "CLOCK_DRIFT",
    "SYMBOL_RULE_UNVERIFIED",
    "SYMBOL_RULE_BLOCK",
    "REGIME_MISMATCH",
    "MARKET_EVENT_RISK",
    "BREADTH_OFF_BLOCKED",
    "FEE_MODEL_UNVERIFIED",
    "FEE_EXCEEDS_EDGE",
    "MARKET_IMPACT_EXCEEDS_EDGE",
    "EXPECTED_SLIPPAGE_EXCEEDED",
    "DEPTH_TOO_THIN",
    "DEPTH_EXCHANGE_REJECT_RISK",
    "STRATEGY_NOT_ELIGIBLE",
    "STRATEGY_CONFIDENCE_LOW",
    "COOLDOWN",
    "MIN_EDGE_FAIL",
]

BLOCKER_ALIASES = {
    "KILL_SWITCH": "KILL_SWITCH_ACTIVE",
}

RECONCILIATION_BLOCKERS = {
    "RECONCILIATION_REQUIRED",
    "LEDGER_INTEGRITY_FAIL",
    "LEDGER_UNAVAILABLE",
    "EXCHANGE_SYNC_REQUIRED",
    "BALANCE_MISMATCH",
    "ORPHAN_POSITION_REVIEW_REQUIRED",
    "ORPHAN_OPEN_ORDER_REVIEW_REQUIRED",
}

TRADE_DISABLED_BLOCKERS = {
    "SESSION_PAUSE",
    "TRADE_DISABLED",
}


def normalize_blocker_code(code: object) -> str | None:
    if not isinstance(code, str):
        return None
    normalized = code.strip()
    if not normalized:
        return None
    return BLOCKER_ALIASES.get(normalized, normalized)


def order_blocker_codes(blockers: list[dict[str, str]]) -> list[str]:
    input_order: list[str] = []
    for blocker in blockers:
        if not isinstance(blocker, dict):
            continue
        code = normalize_blocker_code(blocker.get("code"))
        if code and code not in input_order:
            input_order.append(code)

    prioritized = [code for code in BLOCKER_PRIORITY if code in input_order]
    priority_set = set(prioritized)
    return prioritized + [code for code in input_order if code not in priority_set]


def select_primary_blocker(blockers: list[dict[str, str]]) -> str | None:
    ordered_codes = order_blocker_codes(blockers)
    return ordered_codes[0] if ordered_codes else None


def choose_paper_final_decision(*, requested_entry: bool, blockers: list[dict[str, str]]) -> str:
    if blockers:
        return "NO_TRADE"
    return "ENTER_LONG" if requested_entry else "NO_TRADE"


def choose_operational_paper_decision(*, requested_entry: bool, blockers: list[dict[str, str]]) -> tuple[str, str | None]:
    primary = select_primary_blocker(blockers)
    if primary == "KILL_SWITCH_ACTIVE":
        return "SAFE_MODE", primary
    if primary in RECONCILIATION_BLOCKERS:
        return "RECONCILE_REQUIRED", primary
    if primary in TRADE_DISABLED_BLOCKERS:
        return "TRADE_DISABLED", primary
    if blockers:
        return "NO_TRADE", primary
    return ("ENTER_LONG" if requested_entry else "NO_TRADE"), None
