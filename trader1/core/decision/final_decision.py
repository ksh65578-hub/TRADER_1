from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_paper_final_decision(
    *,
    status: str,
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "PAPER",
    blockers: list[dict[str, Any]] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_id": "trader1.final_decision.v1",
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": "0" * 64,
            "agents_sha256": "0" * 64,
        },
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "status": status,
        "blockers": blockers or [],
        "notes": notes,
    }
