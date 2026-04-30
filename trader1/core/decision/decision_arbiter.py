from __future__ import annotations


BLOCKER_PRIORITY = [
    "KILL_SWITCH",
    "RECONCILIATION_REQUIRED",
    "LEDGER_UNAVAILABLE",
    "SNAPSHOT_SCOPE_MISMATCH",
    "LIVE_FINAL_GUARD_FAILED",
    "RISK_VETO",
    "SYMBOL_RULE_UNVERIFIED",
    "MIN_EDGE_FAIL",
]


def select_primary_blocker(blockers: list[dict[str, str]]) -> str | None:
    codes = {blocker.get("code") for blocker in blockers if isinstance(blocker, dict)}
    for code in BLOCKER_PRIORITY:
        if code in codes:
            return code
    return next(iter(codes), None)


def choose_paper_final_decision(*, requested_entry: bool, blockers: list[dict[str, str]]) -> str:
    if blockers:
        return "NO_TRADE"
    return "ENTER_LONG" if requested_entry else "NO_TRADE"


def choose_operational_paper_decision(*, requested_entry: bool, blockers: list[dict[str, str]]) -> tuple[str, str | None]:
    primary = select_primary_blocker(blockers)
    if primary == "KILL_SWITCH":
        return "SAFE_MODE", primary
    if primary == "RECONCILIATION_REQUIRED":
        return "RECONCILE_REQUIRED", primary
    if blockers:
        return "NO_TRADE", primary
    return ("ENTER_LONG" if requested_entry else "NO_TRADE"), None
