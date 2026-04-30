from __future__ import annotations


def validate_upbit_krw_symbol(symbol: str, *, market_type: str = "KRW_SPOT") -> tuple[str, str | None, str]:
    if market_type != "KRW_SPOT":
        return "BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "Upbit paper dry-run is scoped to KRW_SPOT"
    if not isinstance(symbol, str) or not symbol.startswith("KRW-") or len(symbol.split("-")) != 2:
        return "BLOCKED", "SYMBOL_RULE_UNVERIFIED", "Upbit KRW paper symbol must use KRW-* format"
    return "PASS", None, "Upbit KRW symbol rule scaffold passed"
