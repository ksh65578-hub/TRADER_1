from __future__ import annotations

from typing import Any


def build_no_trade_panel(operation_report: dict[str, Any]) -> dict[str, Any]:
    paper = operation_report.get("paper_dry_run_report", {})
    return {
        "panel_id": "no_trade_panel",
        "display_only": True,
        "no_trade_reasons": paper.get("no_trade_reasons", []),
        "primary_blocker_code": operation_report.get("primary_blocker_code"),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_controls_present": False,
    }
