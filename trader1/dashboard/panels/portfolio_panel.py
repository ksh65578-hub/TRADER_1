from __future__ import annotations

from typing import Any


def build_portfolio_panel(operation_report: dict[str, Any]) -> dict[str, Any]:
    sizing = operation_report.get("sizing_decision", {})
    return {
        "panel_id": "portfolio_panel",
        "display_only": True,
        "mode": "PAPER",
        "selected_notional": sizing.get("selected_notional", "0"),
        "paper_order_submitted": operation_report.get("paper_dry_run_report", {}).get("paper_order_submitted", False),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_controls_present": False,
    }
