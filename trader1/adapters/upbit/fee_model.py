from __future__ import annotations


UPBIT_KRW_PAPER_FEE_RATE = "0.0005"
UPBIT_KRW_PAPER_SLIPPAGE_BPS = "5"


def build_upbit_fee_slippage_baseline(*, fee_rate: str = UPBIT_KRW_PAPER_FEE_RATE, slippage_bps: str = UPBIT_KRW_PAPER_SLIPPAGE_BPS) -> dict[str, str]:
    return {
        "fee_model_status": "PASS" if fee_rate else "BLOCKED",
        "slippage_model_status": "PASS" if slippage_bps else "BLOCKED",
        "fee_rate": fee_rate,
        "slippage_bps": slippage_bps,
        "fee_model_scope": "UPBIT/KRW_SPOT/PAPER",
    }
