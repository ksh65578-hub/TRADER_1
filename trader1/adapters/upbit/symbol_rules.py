from __future__ import annotations


UPBIT_KRW_SYMBOL_RULE_ID = "UPBIT_KRW_SPOT_SYMBOL_RULE_V1"
UPBIT_KRW_BASE_MIN_LEN = 2
UPBIT_KRW_BASE_MAX_LEN = 12
UPBIT_KRW_BASE_ALLOWED_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def _blocked(message: str) -> tuple[str, str, str]:
    return "BLOCKED", "SYMBOL_RULE_UNVERIFIED", message


def validate_upbit_krw_symbol(symbol: str, *, market_type: str = "KRW_SPOT") -> tuple[str, str | None, str]:
    if market_type != "KRW_SPOT":
        return "BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "Upbit paper dry-run is scoped to KRW_SPOT"
    if not isinstance(symbol, str):
        return _blocked("Upbit KRW symbol must be a string")
    if symbol != symbol.strip():
        return _blocked("Upbit KRW symbol must not contain leading or trailing whitespace")

    parts = symbol.split("-")
    if len(parts) != 2:
        return _blocked("Upbit KRW symbol must match QUOTE-BASE with exactly one dash")

    quote, base = parts
    if quote != "KRW":
        return _blocked("Upbit KRW spot symbol must use KRW quote currency")
    if not (UPBIT_KRW_BASE_MIN_LEN <= len(base) <= UPBIT_KRW_BASE_MAX_LEN):
        return _blocked(
            f"Upbit KRW base asset length must be {UPBIT_KRW_BASE_MIN_LEN}-{UPBIT_KRW_BASE_MAX_LEN} characters"
        )
    if base == "KRW":
        return _blocked("Upbit KRW base asset cannot also be KRW")
    if any(character not in UPBIT_KRW_BASE_ALLOWED_CHARS for character in base):
        return _blocked("Upbit KRW base asset must use uppercase A-Z or 0-9 only")

    return (
        "PASS",
        None,
        (
            f"{UPBIT_KRW_SYMBOL_RULE_ID}: quote=KRW, base_length={UPBIT_KRW_BASE_MIN_LEN}-{UPBIT_KRW_BASE_MAX_LEN}, "
            "base_charset=A-Z0-9, exactly_one_dash=true"
        ),
    )
