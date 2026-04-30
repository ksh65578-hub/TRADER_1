from __future__ import annotations

from typing import Any


def build_status_panel(operation_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "panel_id": "status_panel",
        "display_only": True,
        "operation_gate_status": operation_report.get("operation_gate_status", "BLOCKED"),
        "stage_gate_status": operation_report.get("stage_gate_status", "BLOCKED"),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_controls_present": False,
        "forbidden_wording_present": False,
    }
