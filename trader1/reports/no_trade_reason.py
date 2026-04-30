from __future__ import annotations


NO_TRADE_REASONS = {
    "MIN_EDGE_FAIL",
    "DATA_UNAVAILABLE",
    "SYMBOL_RULE_UNVERIFIED",
    "FEE_MODEL_UNVERIFIED",
    "MEASUREMENT_MISSING",
    "RISK_VETO",
    "LIVE_FINAL_GUARD_FAILED",
    "SNAPSHOT_SCOPE_MISMATCH",
}


ENTRY_REASON_CODES = {
    "PAPER_DRY_RUN_ENTRY",
    "PUBLIC_DATA_AVAILABLE",
    "SYMBOL_RULE_PASS",
    "FEE_SLIPPAGE_BASELINE_PASS",
}


def build_no_trade_reason(code: str, message: str) -> dict[str, str]:
    if code not in NO_TRADE_REASONS:
        code = "LIVE_FINAL_GUARD_FAILED"
    return {"code": code, "message": message}


def build_entry_reason(code: str, message: str) -> dict[str, str]:
    if code not in ENTRY_REASON_CODES:
        code = "PAPER_DRY_RUN_ENTRY"
    return {"reason_code": code, "message": message}
