from __future__ import annotations


def evaluate_paper_risk_veto(*, requested_entry: bool, risk_block: bool = False) -> tuple[bool, str | None]:
    if risk_block:
        return True, "RISK_VETO"
    return False, None
