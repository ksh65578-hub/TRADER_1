from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


UPBIT_KRW_PAPER_FEE_RATE = "0.0005"
UPBIT_KRW_PAPER_SLIPPAGE_FLOOR_BPS = "5"
UPBIT_KRW_PAPER_FEE_RATE_MIN = Decimal("0.0001")
UPBIT_KRW_PAPER_FEE_RATE_MAX = Decimal("0.0030")
UPBIT_KRW_PAPER_SLIPPAGE_FLOOR_MIN_BPS = Decimal("0.25")
UPBIT_KRW_PAPER_SLIPPAGE_FLOOR_MAX_BPS = Decimal("100")
UPBIT_KRW_PAPER_SLIPPAGE_MODEL_MAX_BPS = Decimal("150")
UPBIT_KRW_PAPER_LIQUIDITY_PENALTY_SCALE_BPS = Decimal("5")
UPBIT_KRW_PAPER_LIQUIDITY_PENALTY_CAP_BPS = Decimal("25")
UPBIT_KRW_PAPER_LAST_TRADE_DEVIATION_CAP_BPS = Decimal("20")


def _decimal(value: Any) -> Decimal | None:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if decimal.is_nan() or decimal.is_infinite():
        return None
    return decimal


def _decimal_text(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"))
    return format(rounded.normalize(), "f") if rounded != rounded.to_integral() else str(rounded.quantize(Decimal("1")))


def _status(condition: bool) -> str:
    return "PASS" if condition else "BLOCKED"


def build_upbit_fee_slippage_model(
    *,
    public_market_data: dict[str, Any] | None = None,
    fee_rate: str = UPBIT_KRW_PAPER_FEE_RATE,
    slippage_floor_bps: str = UPBIT_KRW_PAPER_SLIPPAGE_FLOOR_BPS,
) -> dict[str, str]:
    fee_decimal = _decimal(fee_rate)
    floor_decimal = _decimal(slippage_floor_bps)
    data = public_market_data or {}
    bid = _decimal(data.get("best_bid"))
    ask = _decimal(data.get("best_ask"))
    last = _decimal(data.get("last_trade_price"))
    volume_24h = _decimal(data.get("volume_24h"))

    fee_pass = fee_decimal is not None and UPBIT_KRW_PAPER_FEE_RATE_MIN <= fee_decimal <= UPBIT_KRW_PAPER_FEE_RATE_MAX
    floor_pass = floor_decimal is not None and UPBIT_KRW_PAPER_SLIPPAGE_FLOOR_MIN_BPS <= floor_decimal <= UPBIT_KRW_PAPER_SLIPPAGE_FLOOR_MAX_BPS
    market_pass = (
        bid is not None
        and ask is not None
        and last is not None
        and volume_24h is not None
        and bid > 0
        and ask > bid
        and last > 0
        and volume_24h > 0
    )

    spread_bps = Decimal("0")
    liquidity_penalty_bps = Decimal("0")
    last_trade_deviation_bps = Decimal("0")
    adaptive_slippage_bps = floor_decimal if floor_decimal is not None else Decimal("0")
    if floor_pass and market_pass and bid is not None and ask is not None and last is not None and volume_24h is not None and floor_decimal is not None:
        midpoint = (bid + ask) / Decimal("2")
        spread_bps = ((ask - bid) / midpoint) * Decimal("10000")
        liquidity_penalty_bps = min(
            UPBIT_KRW_PAPER_LIQUIDITY_PENALTY_CAP_BPS,
            UPBIT_KRW_PAPER_LIQUIDITY_PENALTY_SCALE_BPS / volume_24h,
        )
        last_trade_deviation_bps = min(
            UPBIT_KRW_PAPER_LAST_TRADE_DEVIATION_CAP_BPS,
            abs(last - midpoint) / midpoint * Decimal("10000"),
        )
        adaptive_slippage_bps = min(
            UPBIT_KRW_PAPER_SLIPPAGE_MODEL_MAX_BPS,
            max(floor_decimal, spread_bps + liquidity_penalty_bps + last_trade_deviation_bps),
        )

    slippage_pass = floor_pass and market_pass and Decimal("0") < adaptive_slippage_bps <= UPBIT_KRW_PAPER_SLIPPAGE_MODEL_MAX_BPS
    return {
        "fee_model_status": _status(fee_pass),
        "slippage_model_status": _status(slippage_pass),
        "fee_rate": fee_rate,
        "slippage_bps": _decimal_text(adaptive_slippage_bps),
        "spread_bps": _decimal_text(spread_bps),
        "liquidity_penalty_bps": _decimal_text(liquidity_penalty_bps),
        "last_trade_deviation_bps": _decimal_text(last_trade_deviation_bps),
        "slippage_floor_bps": slippage_floor_bps,
        "fee_model_scope": "UPBIT/KRW_SPOT/PAPER",
        "fee_model_formula": "fee_rate in [0.0001,0.0030]",
        "slippage_model_formula": (
            "min(150,max(configured_floor_bps,spread_bps+min(25,5/volume_24h)+"
            "min(20,abs(last-midpoint)/midpoint*10000)))"
        ),
        "fee_model_message": (
            "Upbit PAPER fee model uses configured fee_rate constrained to 0.0001-0.0030 and never implies live fees"
        ),
        "slippage_model_message": (
            "Upbit PAPER slippage uses public bid/ask spread, volume penalty, last-trade deviation, and configured floor"
        ),
    }
    return {
        "fee_model_status": "PASS" if fee_rate else "BLOCKED",
        "slippage_model_status": "PASS" if slippage_bps else "BLOCKED",
        "fee_rate": fee_rate,
        "slippage_bps": slippage_bps,
        "fee_model_scope": "UPBIT/KRW_SPOT/PAPER",
    }
