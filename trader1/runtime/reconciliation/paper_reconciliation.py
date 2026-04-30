from __future__ import annotations

from trader1.runtime.reconciliation.reconciliation import build_reconciliation_report


def build_paper_reconciliation_report(*, session_id: str = "mvp3_operational_paper") -> dict:
    return build_reconciliation_report(
        reconciliation_id="mvp3-paper-reconciliation",
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
    )
