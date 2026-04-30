from __future__ import annotations

from typing import Any


def classify_strategy_level(strategy_unit: dict[str, Any]) -> str:
    if strategy_unit.get("mode") == "PAPER" and strategy_unit.get("strategy_level") == "LEVEL_2_OPERATIONAL_PAPER":
        return "LEVEL_2_OPERATIONAL_PAPER"
    return "LEVEL_1_PAPER_DRY_RUN"
