from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from trader1.runtime.paper.upbit_public_collector import (
    upbit_public_market_data_collection_hash,
    validate_upbit_public_market_data_collection_report,
)

PAPER_PORTFOLIO_SCHEMA_ID = "trader1.paper_portfolio_snapshot.v1"
PAPER_PORTFOLIO_SOURCES = {
    "PAPER_LEDGER_SCAFFOLD",
    "PAPER_LEDGER_ROLLUP",
    "PAPER_LEDGER_ROLLUP_PUBLIC_MARK",
}
PAPER_POSITION_STRATEGY_CONTEXT_FIELDS = {
    "entry_strategy_context_status",
    "entry_strategy_context_source",
    "entry_candidate_id",
    "entry_strategy_family",
    "entry_strategy_exit_policy_id",
    "entry_strategy_exit_variation",
    "entry_strategy_source_runtime_cycle_id",
    "entry_strategy_source_candidate_hash",
    "entry_strategy_source_exit_plan_hash",
    "entry_strategy_context_formula",
}
PAPER_POSITION_STRATEGY_FAMILIES = {
    "PULLBACK_TREND_LONG",
    "VWAP_MEAN_REVERSION",
    "BREAKOUT_RETEST_LONG",
}
PAPER_POSITION_STRATEGY_EXIT_VARIATIONS = {
    "trailing_tp",
    "fixed_tp",
    "invalidation_exit",
}
PUBLIC_MARK_PRICE_SOURCE = "PUBLIC_REST_READ_ONLY_1M_CLOSE"
MARK_TO_MARKET_PASS_STATUS = "PASS_PUBLIC_MARK_TO_MARKET"
MARK_TO_MARKET_NOT_REQUIRED_STATUS = "NOT_REQUIRED_NO_POSITION"
MARK_TO_MARKET_BLOCKED_STATUS = "BLOCKED_PUBLIC_MARK_UNAVAILABLE"
PUBLIC_MARK_PARENT_SNAPSHOT_HASH_FIELD = "source_mark_to_market_parent_snapshot_hash"
PUBLIC_MARK_PARENT_SNAPSHOT_GENERATED_AT_FIELD = "source_mark_to_market_parent_generated_at_utc"
PUBLIC_MARK_PRICE_BASIS_MISMATCH = "PUBLIC_MARK_PRICE_BASIS_MISMATCH"
PUBLIC_MARK_PRICE_BASIS_MIN_RATIO = Decimal("0.2")
PUBLIC_MARK_PRICE_BASIS_MAX_RATIO = Decimal("5")
PRICE_BASIS_REPAIR_STATUS_APPLIED = "APPLIED_PUBLIC_MARK_PRICE_BASIS_NORMALIZATION"
PRICE_BASIS_REPAIR_STATUS_NOT_REQUIRED = "NOT_REQUIRED"
PRICE_BASIS_REPAIR_STATUS_BLOCKED = "BLOCKED_PUBLIC_MARK_PRICE_BASIS_NORMALIZATION"
PRICE_BASIS_REPAIR_SOURCE = "LEGACY_STATIC_FIXTURE_PRICE_BASIS_TO_UPBIT_KRW_BTC_PUBLIC_MARK"
KRW_SPOT_PRICE_BASIS_REPAIR_SOURCE = "LEGACY_STATIC_FIXTURE_PRICE_BASIS_TO_UPBIT_KRW_SPOT_PUBLIC_MARK"
LEGACY_STATIC_KRW_BTC_MIN_PRICE = Decimal("900000")
LEGACY_STATIC_KRW_BTC_MAX_PRICE = Decimal("1200000")
UPBIT_KRW_BTC_PUBLIC_MARK_MIN_PRICE = Decimal("10000000")
UPBIT_KRW_BTC_PUBLIC_MARK_MAX_PRICE = Decimal("300000000")
PUBLIC_MARK_PRICE_BASIS_REPAIR_MIN_RATIO = Decimal("5")
PUBLIC_MARK_PRICE_BASIS_REPAIR_MAX_RATIO = Decimal("500")
LEGACY_STATIC_KRW_SPOT_PUBLIC_MARK_MIN_PRICE = Decimal("1")
LEGACY_STATIC_KRW_SPOT_PUBLIC_MARK_MAX_PRICE = Decimal("300000000")
LEGACY_STATIC_KRW_SPOT_PUBLIC_MARK_INVERSE_REPAIR_MIN_RATIO = Decimal("0.000001")
PAPER_STARTING_CASH_BY_SCOPE = {
    ("UPBIT", "KRW_SPOT"): ("KRW", Decimal("1000000")),
    ("BINANCE", "SPOT"): ("USDT", Decimal("10000")),
}


@dataclass(frozen=True)
class PaperPortfolioValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("-1")


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f") if value != value.to_integral() else str(value.quantize(Decimal("1")))


def _latest_public_close_by_symbol(
    public_market_data_collection_report: dict[str, Any],
) -> tuple[dict[str, dict[str, str]], str | None, str | None]:
    result = validate_upbit_public_market_data_collection_report(public_market_data_collection_report)
    if result.status != "PASS":
        return {}, result.blocker_code or "DATA_UNAVAILABLE", None
    if public_market_data_collection_report.get("collection_status") != "PASS":
        return {}, public_market_data_collection_report.get("primary_blocker_code") or "DATA_UNAVAILABLE", None
    public_market_data = public_market_data_collection_report.get("public_market_data")
    if not isinstance(public_market_data, dict) or public_market_data.get("source") != "PUBLIC_REST_READ_ONLY":
        return {}, "DATA_UNAVAILABLE", None
    latest_by_symbol: dict[str, dict[str, str]] = {}
    for event in public_market_data_collection_report.get("canonical_events", []):
        if not isinstance(event, dict):
            continue
        symbol = event.get("symbol")
        event_time = event.get("event_time_utc")
        close = event.get("close")
        event_hash = event.get("event_hash")
        if not all(isinstance(value, str) and value for value in (symbol, event_time, close, event_hash)):
            continue
        if _decimal(close) <= 0:
            continue
        current = latest_by_symbol.get(symbol)
        if current is None or str(event_time) > current["event_time_utc"]:
            latest_by_symbol[str(symbol)] = {
                "mark_price": str(close),
                "event_time_utc": str(event_time),
                "event_hash": str(event_hash),
            }
    if not latest_by_symbol:
        return {}, "MEASUREMENT_MISSING", None
    return latest_by_symbol, None, public_market_data_collection_report.get("collection_hash")


def _public_mark_price_basis_blockers(
    *,
    positions: list[dict[str, Any]],
    latest_by_symbol: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], dict[int, dict[str, str]]]:
    blockers: list[dict[str, str]] = []
    repairs: dict[int, dict[str, str]] = {}
    for index, position in enumerate(positions):
        symbol = str(position.get("symbol"))
        public_mark = latest_by_symbol.get(symbol)
        if not public_mark:
            continue
        mark = _decimal(public_mark.get("mark_price"))
        reference_candidates = (
            _decimal(position.get("average_entry_price")),
            _decimal(position.get("mark_price")),
        )
        valid_reference = next((candidate for candidate in reference_candidates if candidate > 0), Decimal("-1"))
        if mark <= 0 or valid_reference <= 0:
            blockers.append(
                {
                    "code": PUBLIC_MARK_PRICE_BASIS_MISMATCH,
                    "severity": "HIGH",
                    "message": f"public mark price basis cannot be compared for {symbol}",
                }
            )
            continue
        ratio = mark / valid_reference
        if ratio < PUBLIC_MARK_PRICE_BASIS_MIN_RATIO or ratio > PUBLIC_MARK_PRICE_BASIS_MAX_RATIO:
            repair = _legacy_static_krw_spot_price_basis_repair(
                position=position,
                public_mark_price=mark,
                valid_reference=valid_reference,
                ratio=ratio,
            )
            if repair is not None:
                repairs[index] = repair
                continue
            blockers.append(
                {
                    "code": PUBLIC_MARK_PRICE_BASIS_MISMATCH,
                    "severity": "HIGH",
                    "message": (
                        f"public mark price basis mismatch for {symbol}: mark/reference ratio={_decimal_text(ratio)} "
                        f"outside [{PUBLIC_MARK_PRICE_BASIS_MIN_RATIO}, {PUBLIC_MARK_PRICE_BASIS_MAX_RATIO}]"
                    ),
                }
            )
    return blockers, repairs


def _legacy_static_krw_btc_price_basis_repair(
    *,
    position: dict[str, Any],
    public_mark_price: Decimal,
    valid_reference: Decimal,
    ratio: Decimal,
) -> dict[str, str] | None:
    """Normalize old PAPER fixture-priced KRW-BTC quantity to the public-mark price basis.

    The repair is intentionally narrow: it only applies to KRW-BTC long PAPER positions whose
    ledger entry price is in the legacy 1,000,000 KRW fixture band while the public mark is in
    the real Upbit KRW-BTC band. It preserves ledger gross cost and fee, changes no cash, and
    keeps all live/scale flags false.
    """
    if str(position.get("symbol")) != "KRW-BTC" or str(position.get("side")) != "LONG":
        return None
    quantity = _decimal(position.get("quantity"))
    cost_basis = _decimal(position.get("cost_basis"))
    if quantity <= 0 or cost_basis <= 0 or public_mark_price <= 0 or valid_reference <= 0:
        return None
    if not (LEGACY_STATIC_KRW_BTC_MIN_PRICE <= valid_reference <= LEGACY_STATIC_KRW_BTC_MAX_PRICE):
        return None
    if not (UPBIT_KRW_BTC_PUBLIC_MARK_MIN_PRICE <= public_mark_price <= UPBIT_KRW_BTC_PUBLIC_MARK_MAX_PRICE):
        return None
    if not (PUBLIC_MARK_PRICE_BASIS_REPAIR_MIN_RATIO < ratio <= PUBLIC_MARK_PRICE_BASIS_REPAIR_MAX_RATIO):
        return None
    gross_entry_cost = quantity * valid_reference
    if gross_entry_cost <= 0 or cost_basis < gross_entry_cost:
        return None
    normalized_quantity = gross_entry_cost / public_mark_price
    if normalized_quantity <= 0:
        return None
    return {
        "price_basis_repair_status": PRICE_BASIS_REPAIR_STATUS_APPLIED,
        "price_basis_repair_source": PRICE_BASIS_REPAIR_SOURCE,
        "price_basis_original_quantity": _decimal_text(quantity),
        "price_basis_original_average_entry_price": _decimal_text(valid_reference),
        "price_basis_original_gross_entry_cost": _decimal_text(gross_entry_cost),
        "price_basis_scale_factor": _decimal_text(ratio),
        "price_basis_normalized_quantity": _decimal_text(normalized_quantity),
        "price_basis_normalized_average_entry_price": _decimal_text(public_mark_price),
    }


def _legacy_static_krw_spot_price_basis_repair(
    *,
    position: dict[str, Any],
    public_mark_price: Decimal,
    valid_reference: Decimal,
    ratio: Decimal,
) -> dict[str, str] | None:
    symbol = str(position.get("symbol") or "")
    if symbol == "KRW-BTC":
        return _legacy_static_krw_btc_price_basis_repair(
            position=position,
            public_mark_price=public_mark_price,
            valid_reference=valid_reference,
            ratio=ratio,
        )
    if not symbol.startswith("KRW-") or str(position.get("side")) != "LONG":
        return None
    quantity = _decimal(position.get("quantity"))
    cost_basis = _decimal(position.get("cost_basis"))
    if quantity <= 0 or cost_basis <= 0 or public_mark_price <= 0 or valid_reference <= 0:
        return None
    if not (LEGACY_STATIC_KRW_BTC_MIN_PRICE <= valid_reference <= LEGACY_STATIC_KRW_BTC_MAX_PRICE):
        return None
    if not (
        LEGACY_STATIC_KRW_SPOT_PUBLIC_MARK_MIN_PRICE
        <= public_mark_price
        <= LEGACY_STATIC_KRW_SPOT_PUBLIC_MARK_MAX_PRICE
    ):
        return None
    ratio_repairable = (
        LEGACY_STATIC_KRW_SPOT_PUBLIC_MARK_INVERSE_REPAIR_MIN_RATIO
        <= ratio
        < PUBLIC_MARK_PRICE_BASIS_MIN_RATIO
    ) or (
        PUBLIC_MARK_PRICE_BASIS_REPAIR_MIN_RATIO
        < ratio
        <= PUBLIC_MARK_PRICE_BASIS_REPAIR_MAX_RATIO
    )
    if not ratio_repairable:
        return None
    gross_entry_cost = quantity * valid_reference
    if gross_entry_cost <= 0 or cost_basis < gross_entry_cost:
        return None
    normalized_quantity = gross_entry_cost / public_mark_price
    if normalized_quantity <= 0:
        return None
    return {
        "price_basis_repair_status": PRICE_BASIS_REPAIR_STATUS_APPLIED,
        "price_basis_repair_source": KRW_SPOT_PRICE_BASIS_REPAIR_SOURCE,
        "price_basis_original_quantity": _decimal_text(quantity),
        "price_basis_original_average_entry_price": _decimal_text(valid_reference),
        "price_basis_original_gross_entry_cost": _decimal_text(gross_entry_cost),
        "price_basis_scale_factor": _decimal_text(ratio),
        "price_basis_normalized_quantity": _decimal_text(normalized_quantity),
        "price_basis_normalized_average_entry_price": _decimal_text(public_mark_price),
    }


def portfolio_needs_public_mark_basis_repair(snapshot: dict[str, Any]) -> bool:
    if not isinstance(snapshot, dict) or snapshot.get("source") != "PAPER_LEDGER_ROLLUP_PUBLIC_MARK":
        return False
    positions = snapshot.get("positions")
    if not isinstance(positions, list):
        return False
    for position in positions:
        if not isinstance(position, dict):
            continue
        mark = _decimal(position.get("mark_price"))
        reference = _decimal(position.get("average_entry_price"))
        if mark <= 0 or reference <= 0:
            continue
        ratio = mark / reference
        if PUBLIC_MARK_PRICE_BASIS_MIN_RATIO <= ratio <= PUBLIC_MARK_PRICE_BASIS_MAX_RATIO:
            continue
        if position.get("price_basis_repair_status") == PRICE_BASIS_REPAIR_STATUS_APPLIED:
            continue
        repair = _legacy_static_krw_spot_price_basis_repair(
            position=position,
            public_mark_price=mark,
            valid_reference=reference,
            ratio=ratio,
        )
        if repair is not None:
            return True
    return False


def mark_paper_portfolio_snapshot_to_public_market(
    *,
    paper_portfolio_snapshot: dict[str, Any],
    public_market_data_collection_report: dict[str, Any] | None,
    generated_at_utc: str | None = None,
    require_public_mark: bool = True,
) -> dict[str, Any]:
    """Revalue a PAPER ledger portfolio using scoped public market prices only."""
    base = dict(paper_portfolio_snapshot)
    base_positions = [dict(position) for position in base.get("positions", []) if isinstance(position, dict)]
    base["positions"] = base_positions
    base_result = validate_paper_portfolio_snapshot(base)
    if base_result.status != "PASS":
        blocked = dict(base)
        blockers = list(blocked.get("blockers", []))
        blockers.append(
            {
                "code": base_result.blocker_code or "MEASUREMENT_MISSING",
                "severity": "HIGH",
                "message": base_result.message,
            }
        )
        blocked["snapshot_status"] = "BLOCKED"
        blocked["primary_blocker_code"] = blockers[0]["code"]
        blocked["blockers"] = blockers
        blocked["mark_to_market_status"] = MARK_TO_MARKET_BLOCKED_STATUS
        blocked["mark_to_market_blocker_code"] = base_result.blocker_code or "MEASUREMENT_MISSING"
        blocked["live_order_ready"] = False
        blocked["live_order_allowed"] = False
        blocked["can_live_trade"] = False
        blocked["scale_up_allowed"] = False
        blocked["can_submit_order"] = False
        blocked["snapshot_hash"] = paper_portfolio_hash(blocked)
        return blocked

    parent_snapshot_hash = base.get("snapshot_hash") if isinstance(base.get("snapshot_hash"), str) else None
    parent_generated_at = base.get("generated_at_utc") if isinstance(base.get("generated_at_utc"), str) else None

    if not base_positions:
        marked = dict(base)
        marked["generated_at_utc"] = generated_at_utc or utc_now()
        marked[PUBLIC_MARK_PARENT_SNAPSHOT_HASH_FIELD] = parent_snapshot_hash
        marked[PUBLIC_MARK_PARENT_SNAPSHOT_GENERATED_AT_FIELD] = parent_generated_at
        marked["mark_to_market_status"] = MARK_TO_MARKET_NOT_REQUIRED_STATUS
        marked["mark_price_source"] = "NO_OPEN_POSITION"
        marked["source_public_market_data_hash"] = None
        marked["source_public_market_data_generated_at_utc"] = None
        marked["source_public_market_event_time_utc"] = None
        marked["source_public_market_event_hash"] = None
        marked["marked_to_market_position_count"] = 0
        marked["mark_to_market_blocker_code"] = None
        marked["live_order_ready"] = False
        marked["live_order_allowed"] = False
        marked["can_live_trade"] = False
        marked["scale_up_allowed"] = False
        marked["can_submit_order"] = False
        marked["snapshot_hash"] = paper_portfolio_hash(marked)
        return marked

    latest_by_symbol: dict[str, dict[str, str]] = {}
    blocker_code: str | None = "DATA_UNAVAILABLE"
    source_collection_hash: str | None = None
    if isinstance(public_market_data_collection_report, dict):
        latest_by_symbol, blocker_code, source_collection_hash = _latest_public_close_by_symbol(
            public_market_data_collection_report
        )
        if source_collection_hash is None:
            value = public_market_data_collection_report.get("collection_hash")
            if isinstance(value, str) and len(value) == 64:
                source_collection_hash = value
            else:
                source_collection_hash = upbit_public_market_data_collection_hash(public_market_data_collection_report)
    if require_public_mark and not latest_by_symbol:
        blocked = dict(base)
        blockers = list(blocked.get("blockers", []))
        blockers.append(
            {
                "code": blocker_code or "DATA_UNAVAILABLE",
                "severity": "HIGH",
                "message": "public REST mark price is required for current PAPER portfolio truth",
            }
        )
        blocked["snapshot_status"] = "BLOCKED"
        blocked["primary_blocker_code"] = blockers[0]["code"]
        blocked["blockers"] = blockers
        blocked["mark_to_market_status"] = MARK_TO_MARKET_BLOCKED_STATUS
        blocked["mark_to_market_blocker_code"] = blocker_code or "DATA_UNAVAILABLE"
        blocked["source_public_market_data_hash"] = source_collection_hash
        blocked["live_order_ready"] = False
        blocked["live_order_allowed"] = False
        blocked["can_live_trade"] = False
        blocked["scale_up_allowed"] = False
        blocked["can_submit_order"] = False
        blocked["snapshot_hash"] = paper_portfolio_hash(blocked)
        return blocked
    if not latest_by_symbol:
        return base

    missing_symbols = sorted(
        str(position.get("symbol"))
        for position in base_positions
        if str(position.get("symbol")) not in latest_by_symbol
    )
    if missing_symbols:
        blocked = dict(base)
        blockers = list(blocked.get("blockers", []))
        blockers.append(
            {
                "code": "MEASUREMENT_MISSING",
                "severity": "HIGH",
                "message": f"public REST mark price missing for open PAPER symbols: {', '.join(missing_symbols)}",
            }
        )
        blocked["snapshot_status"] = "BLOCKED"
        blocked["primary_blocker_code"] = blockers[0]["code"]
        blocked["blockers"] = blockers
        blocked["mark_to_market_status"] = MARK_TO_MARKET_BLOCKED_STATUS
        blocked["mark_to_market_blocker_code"] = "MEASUREMENT_MISSING"
        blocked["source_public_market_data_hash"] = source_collection_hash
        blocked["live_order_ready"] = False
        blocked["live_order_allowed"] = False
        blocked["can_live_trade"] = False
        blocked["scale_up_allowed"] = False
        blocked["can_submit_order"] = False
        blocked["snapshot_hash"] = paper_portfolio_hash(blocked)
        return blocked

    basis_blockers, basis_repairs = _public_mark_price_basis_blockers(
        positions=base_positions,
        latest_by_symbol=latest_by_symbol,
    )
    if basis_blockers:
        blocked = dict(base)
        blockers = list(blocked.get("blockers", [])) + basis_blockers
        blocked["snapshot_status"] = "BLOCKED"
        blocked["primary_blocker_code"] = blockers[0]["code"]
        blocked["blockers"] = blockers
        blocked["mark_to_market_status"] = MARK_TO_MARKET_BLOCKED_STATUS
        blocked["mark_to_market_blocker_code"] = PUBLIC_MARK_PRICE_BASIS_MISMATCH
        blocked["source_public_market_data_hash"] = source_collection_hash
        blocked["source_public_market_data_generated_at_utc"] = (
            public_market_data_collection_report.get("generated_at_utc")
            if isinstance(public_market_data_collection_report, dict)
            else None
        )
        blocked["price_basis_repair_status"] = PRICE_BASIS_REPAIR_STATUS_BLOCKED
        blocked["price_basis_repair_count"] = 0
        blocked["price_basis_repair_source"] = None
        blocked["live_order_ready"] = False
        blocked["live_order_allowed"] = False
        blocked["can_live_trade"] = False
        blocked["scale_up_allowed"] = False
        blocked["can_submit_order"] = False
        blocked["snapshot_hash"] = paper_portfolio_hash(blocked)
        return blocked

    marked_positions: list[dict[str, Any]] = []
    position_market_value = Decimal("0")
    unrealized_pnl = Decimal("0")
    latest_event_time: str | None = None
    latest_event_hash: str | None = None
    applied_repair_count = 0
    for index, position in enumerate(base_positions):
        symbol = str(position["symbol"])
        public_mark = latest_by_symbol[symbol]
        repair = basis_repairs.get(index)
        qty = _decimal(repair["price_basis_normalized_quantity"]) if repair else _decimal(position["quantity"])
        mark = _decimal(public_mark["mark_price"])
        cost_basis = _decimal(position["cost_basis"])
        market_value = qty * mark
        position_unrealized = market_value - cost_basis
        updated = dict(position)
        if repair:
            applied_repair_count += 1
            updated.update(repair)
            updated["quantity"] = repair["price_basis_normalized_quantity"]
            updated["average_entry_price"] = repair["price_basis_normalized_average_entry_price"]
        elif updated.get("price_basis_repair_status") == PRICE_BASIS_REPAIR_STATUS_APPLIED:
            applied_repair_count += 1
        else:
            updated["price_basis_repair_status"] = PRICE_BASIS_REPAIR_STATUS_NOT_REQUIRED
        updated["mark_price"] = _decimal_text(mark)
        updated["market_value"] = _decimal_text(market_value)
        updated["unrealized_pnl"] = _decimal_text(position_unrealized)
        updated["source"] = "PAPER_LEDGER_ROLLUP_PUBLIC_MARK"
        updated["mark_price_source"] = PUBLIC_MARK_PRICE_SOURCE
        updated["source_public_market_event_time_utc"] = public_mark["event_time_utc"]
        updated["source_public_market_event_hash"] = public_mark["event_hash"]
        marked_positions.append(updated)
        position_market_value += market_value
        unrealized_pnl += position_unrealized
        if latest_event_time is None or public_mark["event_time_utc"] > latest_event_time:
            latest_event_time = public_mark["event_time_utc"]
            latest_event_hash = public_mark["event_hash"]

    cash_available = _decimal(base["cash_available"])
    locked_balance = _decimal(base["locked_balance"])
    realized_pnl = _decimal(base["realized_pnl"])
    total_pnl = realized_pnl + unrealized_pnl
    equity = cash_available + locked_balance + position_market_value
    starting = _decimal(base["starting_cash"])
    return_pct = Decimal("0") if starting <= 0 else ((equity - starting) / starting * Decimal("100"))
    repair_sources = sorted(
        {
            str(position.get("price_basis_repair_source"))
            for position in marked_positions
            if position.get("price_basis_repair_status") == PRICE_BASIS_REPAIR_STATUS_APPLIED
            and isinstance(position.get("price_basis_repair_source"), str)
            and position.get("price_basis_repair_source")
        }
    )
    marked = dict(base)
    marked.update(
        {
            "generated_at_utc": generated_at_utc or utc_now(),
            "source": "PAPER_LEDGER_ROLLUP_PUBLIC_MARK",
            PUBLIC_MARK_PARENT_SNAPSHOT_HASH_FIELD: parent_snapshot_hash,
            PUBLIC_MARK_PARENT_SNAPSHOT_GENERATED_AT_FIELD: parent_generated_at,
            "position_market_value": _decimal_text(position_market_value),
            "equity": _decimal_text(equity),
            "unrealized_pnl": _decimal_text(unrealized_pnl),
            "total_pnl": _decimal_text(total_pnl),
            "return_pct": _decimal_text(return_pct),
            "positions": marked_positions,
            "mark_to_market_status": MARK_TO_MARKET_PASS_STATUS,
            "mark_price_source": PUBLIC_MARK_PRICE_SOURCE,
            "source_public_market_data_hash": source_collection_hash,
            "source_public_market_data_generated_at_utc": (
                public_market_data_collection_report.get("generated_at_utc")
                if isinstance(public_market_data_collection_report, dict)
                else None
            ),
            "source_public_market_event_time_utc": latest_event_time,
            "source_public_market_event_hash": latest_event_hash,
            "source_public_market_symbol_count": len(latest_by_symbol),
            "marked_to_market_position_count": len(marked_positions),
            "mark_to_market_blocker_code": None,
            "price_basis_repair_status": (
                PRICE_BASIS_REPAIR_STATUS_APPLIED if applied_repair_count else PRICE_BASIS_REPAIR_STATUS_NOT_REQUIRED
            ),
            "price_basis_repair_count": applied_repair_count,
            "price_basis_repair_source": (
                repair_sources[0]
                if applied_repair_count and len(repair_sources) == 1
                else "MIXED_PUBLIC_MARK_PRICE_BASIS_NORMALIZATION"
                if applied_repair_count and repair_sources
                else None
            ),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "can_submit_order": False,
        }
    )
    marked["snapshot_hash"] = paper_portfolio_hash(marked)
    return marked


def paper_portfolio_hash(snapshot: dict[str, Any]) -> str:
    payload = dict(snapshot)
    payload.pop("snapshot_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def build_initial_paper_portfolio_snapshot(
    *,
    exchange: str,
    market_type: str,
    session_id: str,
    starting_cash: str | int | float | Decimal | None = None,
    source_runtime_cycle_id: str | None = None,
    source_paper_ledger_head_hash: str | None = None,
) -> dict[str, Any]:
    currency, default_cash = PAPER_STARTING_CASH_BY_SCOPE.get((exchange, market_type), ("UNKNOWN", Decimal("0")))
    starting = _decimal(starting_cash if starting_cash is not None else default_cash)
    blockers: list[dict[str, str]] = []
    if (exchange, market_type) not in PAPER_STARTING_CASH_BY_SCOPE:
        blockers.append({"code": "SNAPSHOT_SCOPE_MISMATCH", "severity": "HIGH", "message": "paper portfolio scope is not supported"})
    if starting <= 0:
        blockers.append({"code": "MEASUREMENT_MISSING", "severity": "HIGH", "message": "paper starting cash must be positive"})
    cash_available = max(Decimal("0"), starting)
    locked_balance = Decimal("0")
    position_market_value = Decimal("0")
    realized_pnl = Decimal("0")
    unrealized_pnl = Decimal("0")
    total_pnl = realized_pnl + unrealized_pnl
    equity = cash_available + locked_balance + position_market_value
    return_pct = Decimal("0") if starting <= 0 else ((equity - starting) / starting * Decimal("100"))
    snapshot = {
        "schema_id": PAPER_PORTFOLIO_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": exchange,
        "market_type": market_type,
        "mode": "PAPER",
        "session_id": session_id,
        "source_runtime_cycle_id": source_runtime_cycle_id,
        "source_paper_ledger_head_hash": source_paper_ledger_head_hash,
        "snapshot_status": "PASS" if not blockers else "BLOCKED",
        "source": "PAPER_LEDGER_SCAFFOLD",
        "starting_cash_source": "MVP_PAPER_DEFAULT_NOT_LIVE_ACCOUNT",
        "currency": currency,
        "starting_cash": _decimal_text(starting),
        "cash_available": _decimal_text(cash_available),
        "locked_balance": _decimal_text(locked_balance),
        "position_market_value": _decimal_text(position_market_value),
        "equity": _decimal_text(equity),
        "realized_pnl": _decimal_text(realized_pnl),
        "unrealized_pnl": _decimal_text(unrealized_pnl),
        "total_pnl": _decimal_text(total_pnl),
        "return_pct": _decimal_text(return_pct),
        "open_position_count": 0,
        "positions": [],
        "paper_only": True,
        "display_balance_kind": "SIMULATED_PAPER_LEDGER",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "can_submit_order": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "snapshot_hash": "",
    }
    snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
    return snapshot


def build_paper_portfolio_snapshot_from_fill(
    *,
    exchange: str,
    market_type: str,
    session_id: str,
    symbol: str,
    side: str,
    quantity: str | int | float | Decimal,
    fill_price: str | int | float | Decimal,
    mark_price: str | int | float | Decimal,
    fee_amount: str | int | float | Decimal,
    starting_cash: str | int | float | Decimal | None = None,
    source_runtime_cycle_id: str | None = None,
    source_paper_ledger_head_hash: str | None = None,
    entry_strategy_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    currency, default_cash = PAPER_STARTING_CASH_BY_SCOPE.get((exchange, market_type), ("UNKNOWN", Decimal("0")))
    starting = _decimal(starting_cash if starting_cash is not None else default_cash)
    qty = _decimal(quantity)
    fill = _decimal(fill_price)
    mark = _decimal(mark_price)
    fee = _decimal(fee_amount)
    blockers: list[dict[str, str]] = []
    if (exchange, market_type) not in PAPER_STARTING_CASH_BY_SCOPE:
        blockers.append({"code": "SNAPSHOT_SCOPE_MISMATCH", "severity": "HIGH", "message": "paper portfolio scope is not supported"})
    if side != "BUY":
        blockers.append({"code": "LIVE_FINAL_GUARD_FAILED", "severity": "HIGH", "message": "Upbit KRW_SPOT paper portfolio only supports long spot fills"})
    if min(starting, qty, fill, mark, fee) < 0 or starting <= 0 or qty <= 0 or fill <= 0 or mark <= 0:
        blockers.append({"code": "MEASUREMENT_MISSING", "severity": "HIGH", "message": "paper fill values must be positive"})

    gross_cost = qty * fill
    position_market_value = qty * mark
    realized_pnl = Decimal("0")
    unrealized_pnl = position_market_value - gross_cost - fee
    total_pnl = realized_pnl + unrealized_pnl
    cash_available = starting - gross_cost - fee
    locked_balance = Decimal("0")
    equity = cash_available + locked_balance + position_market_value
    if cash_available < 0:
        blockers.append({"code": "RISK_VETO", "severity": "HIGH", "message": "paper fill would make simulated cash negative"})
    return_pct = Decimal("0") if starting <= 0 else ((equity - starting) / starting * Decimal("100"))
    position = {
        "symbol": symbol,
        "side": "LONG",
        "quantity": _decimal_text(qty),
        "average_entry_price": _decimal_text(fill),
        "mark_price": _decimal_text(mark),
        "cost_basis": _decimal_text(gross_cost + fee),
        "market_value": _decimal_text(position_market_value),
        "unrealized_pnl": _decimal_text(unrealized_pnl),
        "source": "PAPER_LEDGER_SCAFFOLD",
        "paper_only": True,
    }
    if entry_strategy_context is not None:
        missing_context = sorted(PAPER_POSITION_STRATEGY_CONTEXT_FIELDS - set(entry_strategy_context))
        if missing_context:
            blockers.append(
                {
                    "code": "SCHEMA_IDENTITY_MISMATCH",
                    "severity": "HIGH",
                    "message": f"paper entry strategy context missing fields: {missing_context}",
                }
            )
        else:
            position.update({field: entry_strategy_context[field] for field in sorted(PAPER_POSITION_STRATEGY_CONTEXT_FIELDS)})
    positions = [position]
    snapshot = {
        "schema_id": PAPER_PORTFOLIO_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": exchange,
        "market_type": market_type,
        "mode": "PAPER",
        "session_id": session_id,
        "source_runtime_cycle_id": source_runtime_cycle_id,
        "source_paper_ledger_head_hash": source_paper_ledger_head_hash,
        "snapshot_status": "PASS" if not blockers else "BLOCKED",
        "source": "PAPER_LEDGER_SCAFFOLD",
        "starting_cash_source": "MVP_PAPER_DEFAULT_NOT_LIVE_ACCOUNT",
        "currency": currency,
        "starting_cash": _decimal_text(starting),
        "cash_available": _decimal_text(cash_available),
        "locked_balance": _decimal_text(locked_balance),
        "position_market_value": _decimal_text(position_market_value),
        "equity": _decimal_text(equity),
        "realized_pnl": _decimal_text(realized_pnl),
        "unrealized_pnl": _decimal_text(unrealized_pnl),
        "total_pnl": _decimal_text(total_pnl),
        "return_pct": _decimal_text(return_pct),
        "open_position_count": 1 if not blockers else 0,
        "positions": positions if not blockers else [],
        "paper_only": True,
        "display_balance_kind": "SIMULATED_PAPER_LEDGER",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "can_submit_order": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "snapshot_hash": "",
    }
    snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
    return snapshot


def build_paper_portfolio_snapshot_after_sell_fill(
    *,
    current_snapshot: dict[str, Any],
    session_id: str,
    symbol: str,
    quantity: str | int | float | Decimal,
    fill_price: str | int | float | Decimal,
    fee_amount: str | int | float | Decimal,
    source_runtime_cycle_id: str | None = None,
    source_paper_ledger_head_hash: str | None = None,
) -> dict[str, Any]:
    base = dict(current_snapshot)
    base["positions"] = [dict(position) for position in current_snapshot.get("positions", []) if isinstance(position, dict)]
    blockers: list[dict[str, str]] = []
    base_result = validate_paper_portfolio_snapshot(base)
    if base_result.status != "PASS":
        blockers.append(
            {
                "code": base_result.blocker_code or "MEASUREMENT_MISSING",
                "severity": "HIGH",
                "message": base_result.message,
            }
        )

    qty_to_sell = _decimal(quantity)
    sell_price = _decimal(fill_price)
    sell_fee = _decimal(fee_amount)
    if qty_to_sell <= 0 or sell_price <= 0 or sell_fee < 0:
        blockers.append({"code": "MEASUREMENT_MISSING", "severity": "HIGH", "message": "paper sell fill values must be positive"})

    positions: list[dict[str, Any]] = []
    selected_found = False
    realized_delta = Decimal("0")
    for position in base.get("positions", []):
        current = dict(position)
        if str(current.get("symbol")) != symbol:
            positions.append(current)
            continue
        selected_found = True
        current_qty = _decimal(current.get("quantity"))
        current_cost_basis = _decimal(current.get("cost_basis"))
        if current_qty <= 0 or current_cost_basis <= 0:
            blockers.append({"code": "MEASUREMENT_MISSING", "severity": "HIGH", "message": "paper sell source position is invalid"})
            positions.append(current)
            continue
        if qty_to_sell > current_qty:
            blockers.append({"code": "RECONCILIATION_REQUIRED", "severity": "HIGH", "message": "paper sell fill exceeds open long quantity"})
            positions.append(current)
            continue

        sell_fraction = qty_to_sell / current_qty
        allocated_cost_basis = current_cost_basis * sell_fraction
        sell_proceeds = qty_to_sell * sell_price
        realized_delta += sell_proceeds - allocated_cost_basis - sell_fee
        remaining_qty = current_qty - qty_to_sell
        remaining_cost_basis = current_cost_basis - allocated_cost_basis
        if remaining_qty > 0:
            updated = dict(current)
            updated["quantity"] = _decimal_text(remaining_qty)
            updated["mark_price"] = _decimal_text(sell_price)
            updated["cost_basis"] = _decimal_text(remaining_cost_basis)
            updated["market_value"] = _decimal_text(remaining_qty * sell_price)
            updated["unrealized_pnl"] = _decimal_text((remaining_qty * sell_price) - remaining_cost_basis)
            updated["source"] = "PAPER_LEDGER_SCAFFOLD"
            updated["paper_only"] = True
            positions.append(updated)
    if not selected_found:
        blockers.append({"code": "MEASUREMENT_MISSING", "severity": "HIGH", "message": "paper sell fill source position is missing"})

    cash_available = _decimal(base.get("cash_available")) + (qty_to_sell * sell_price) - sell_fee
    locked_balance = _decimal(base.get("locked_balance"))
    realized_pnl = _decimal(base.get("realized_pnl")) + realized_delta
    position_market_value = sum((_decimal(position.get("market_value")) for position in positions), Decimal("0"))
    unrealized_pnl = sum((_decimal(position.get("unrealized_pnl")) for position in positions), Decimal("0"))
    total_pnl = realized_pnl + unrealized_pnl
    equity = cash_available + locked_balance + position_market_value
    starting = _decimal(base.get("starting_cash"))
    if cash_available < 0 or equity <= 0:
        blockers.append({"code": "RISK_VETO", "severity": "HIGH", "message": "paper sell fill produced invalid simulated cash or equity"})
    return_pct = Decimal("0") if starting <= 0 else ((equity - starting) / starting * Decimal("100"))
    snapshot = dict(base)
    snapshot.update(
        {
            "generated_at_utc": utc_now(),
            "session_id": session_id,
            "source_runtime_cycle_id": source_runtime_cycle_id,
            "source_paper_ledger_head_hash": source_paper_ledger_head_hash,
            "snapshot_status": "PASS" if not blockers else "BLOCKED",
            "source": "PAPER_LEDGER_SCAFFOLD",
            "cash_available": _decimal_text(cash_available),
            "locked_balance": _decimal_text(locked_balance),
            "position_market_value": _decimal_text(position_market_value),
            "equity": _decimal_text(equity),
            "realized_pnl": _decimal_text(realized_pnl),
            "unrealized_pnl": _decimal_text(unrealized_pnl),
            "total_pnl": _decimal_text(total_pnl),
            "return_pct": _decimal_text(return_pct),
            "open_position_count": len(positions) if not blockers else 0,
            "positions": positions if not blockers else [],
            "paper_only": True,
            "display_balance_kind": "SIMULATED_PAPER_LEDGER",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "can_submit_order": False,
            "primary_blocker_code": blockers[0]["code"] if blockers else None,
            "blockers": blockers,
            "snapshot_hash": "",
        }
    )
    snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
    return snapshot


def validate_paper_portfolio_snapshot(snapshot: dict[str, Any]) -> PaperPortfolioValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "source_runtime_cycle_id",
        "source_paper_ledger_head_hash",
        "snapshot_status",
        "source",
        "starting_cash_source",
        "currency",
        "starting_cash",
        "cash_available",
        "locked_balance",
        "position_market_value",
        "equity",
        "realized_pnl",
        "unrealized_pnl",
        "total_pnl",
        "return_pct",
        "open_position_count",
        "positions",
        "paper_only",
        "display_balance_kind",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "primary_blocker_code",
        "blockers",
        "snapshot_hash",
    }
    missing = sorted(required - set(snapshot))
    if missing:
        return PaperPortfolioValidationResult("FAIL", f"paper portfolio missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if snapshot.get("schema_id") != PAPER_PORTFOLIO_SCHEMA_ID or snapshot.get("project_id") != "TRADER_1":
        return PaperPortfolioValidationResult("FAIL", "paper portfolio identity mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if snapshot.get("snapshot_hash") != paper_portfolio_hash(snapshot):
        return PaperPortfolioValidationResult("FAIL", "paper portfolio hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    source_runtime_cycle_id = snapshot.get("source_runtime_cycle_id")
    if source_runtime_cycle_id is not None and (not isinstance(source_runtime_cycle_id, str) or not source_runtime_cycle_id):
        return PaperPortfolioValidationResult("FAIL", "paper portfolio source runtime cycle id is invalid", "SCHEMA_IDENTITY_MISMATCH")
    source_paper_ledger_head_hash = snapshot.get("source_paper_ledger_head_hash")
    if source_paper_ledger_head_hash is not None and (
        not isinstance(source_paper_ledger_head_hash, str) or len(source_paper_ledger_head_hash) != 64
    ):
        return PaperPortfolioValidationResult("FAIL", "paper portfolio source ledger head hash is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if snapshot.get("mode") != "PAPER" or snapshot.get("paper_only") is not True:
        return PaperPortfolioValidationResult("BLOCKED", "portfolio snapshot must remain PAPER-only", "LIVE_FINAL_GUARD_FAILED")
    if (snapshot.get("exchange"), snapshot.get("market_type")) not in PAPER_STARTING_CASH_BY_SCOPE:
        return PaperPortfolioValidationResult("BLOCKED", "paper portfolio scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    if (
        snapshot.get("live_order_ready")
        or snapshot.get("live_order_allowed")
        or snapshot.get("can_live_trade")
        or snapshot.get("scale_up_allowed")
        or snapshot.get("can_submit_order")
    ):
        return PaperPortfolioValidationResult("BLOCKED", "paper portfolio attempted live/order permission", "LIVE_FINAL_GUARD_FAILED")
    if snapshot.get("source") not in PAPER_PORTFOLIO_SOURCES or snapshot.get("display_balance_kind") != "SIMULATED_PAPER_LEDGER":
        return PaperPortfolioValidationResult("BLOCKED", "paper portfolio source cannot claim exchange truth", "LIVE_FINAL_GUARD_FAILED")
    starting = _decimal(snapshot.get("starting_cash"))
    cash = _decimal(snapshot.get("cash_available"))
    locked = _decimal(snapshot.get("locked_balance"))
    position_market_value = _decimal(snapshot.get("position_market_value"))
    equity = _decimal(snapshot.get("equity"))
    realized = _decimal(snapshot.get("realized_pnl"))
    unrealized = _decimal(snapshot.get("unrealized_pnl"))
    total_pnl = _decimal(snapshot.get("total_pnl"))
    reported_return = _decimal(snapshot.get("return_pct"))
    if min(starting, cash, locked, position_market_value) < 0 or equity <= 0:
        return PaperPortfolioValidationResult("BLOCKED", "paper portfolio values are invalid", "MEASUREMENT_MISSING")
    if equity != cash + locked + position_market_value:
        return PaperPortfolioValidationResult("FAIL", "paper portfolio equity arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if total_pnl != realized + unrealized:
        return PaperPortfolioValidationResult("FAIL", "paper portfolio total PnL arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_return = Decimal("0") if starting <= 0 else ((equity - starting) / starting * Decimal("100"))
    if reported_return != expected_return:
        return PaperPortfolioValidationResult("FAIL", "paper portfolio return arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH")
    positions = snapshot.get("positions")
    if not isinstance(positions, list) or snapshot.get("open_position_count") != len(positions):
        return PaperPortfolioValidationResult("FAIL", "paper portfolio position count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    position_required = {
        "symbol",
        "side",
        "quantity",
        "average_entry_price",
        "mark_price",
        "cost_basis",
        "market_value",
        "unrealized_pnl",
        "source",
        "paper_only",
    }
    position_value_sum = Decimal("0")
    position_unrealized_sum = Decimal("0")
    for position in positions:
        if not isinstance(position, dict):
            return PaperPortfolioValidationResult("FAIL", "paper portfolio position must be an object", "SCHEMA_IDENTITY_MISMATCH")
        missing_position_fields = sorted(position_required - set(position))
        if missing_position_fields:
            return PaperPortfolioValidationResult(
                "FAIL",
                f"paper portfolio position missing fields: {missing_position_fields}",
                "SCHEMA_IDENTITY_MISMATCH",
            )
        if position.get("paper_only") is not True or position.get("source") not in PAPER_PORTFOLIO_SOURCES:
            return PaperPortfolioValidationResult("BLOCKED", "paper position source cannot claim exchange truth", "LIVE_FINAL_GUARD_FAILED")
        if position.get("side") != "LONG":
            return PaperPortfolioValidationResult("BLOCKED", "paper position must remain long spot only", "LIVE_FINAL_GUARD_FAILED")
        if not isinstance(position.get("symbol"), str) or not position["symbol"]:
            return PaperPortfolioValidationResult("FAIL", "paper position symbol is missing", "SCHEMA_IDENTITY_MISMATCH")
        quantity = _decimal(position.get("quantity"))
        average_entry = _decimal(position.get("average_entry_price"))
        mark = _decimal(position.get("mark_price"))
        cost_basis = _decimal(position.get("cost_basis"))
        market_value = _decimal(position.get("market_value"))
        position_unrealized = _decimal(position.get("unrealized_pnl"))
        if min(quantity, average_entry, mark, cost_basis, market_value) < 0 or quantity <= 0 or average_entry <= 0 or mark <= 0:
            return PaperPortfolioValidationResult("BLOCKED", "paper position values are invalid", "MEASUREMENT_MISSING")
        if market_value != quantity * mark:
            return PaperPortfolioValidationResult("FAIL", "paper position market value arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if cost_basis < quantity * average_entry:
            return PaperPortfolioValidationResult("FAIL", "paper position cost basis is below gross entry cost", "SCHEMA_IDENTITY_MISMATCH")
        if position_unrealized != market_value - cost_basis:
            return PaperPortfolioValidationResult("FAIL", "paper position unrealized PnL arithmetic mismatch", "SCHEMA_IDENTITY_MISMATCH")
        context_fields_present = PAPER_POSITION_STRATEGY_CONTEXT_FIELDS.intersection(position)
        if context_fields_present:
            missing_context = sorted(PAPER_POSITION_STRATEGY_CONTEXT_FIELDS - set(position))
            if missing_context:
                return PaperPortfolioValidationResult(
                    "FAIL",
                    f"paper position entry strategy context missing fields: {missing_context}",
                    "SCHEMA_IDENTITY_MISMATCH",
                )
            if position.get("entry_strategy_context_status") != "BOUND_TO_ENTRY_CANDIDATE":
                return PaperPortfolioValidationResult("FAIL", "paper position entry strategy context status is invalid", "SCHEMA_IDENTITY_MISMATCH")
            if position.get("entry_strategy_context_source") != "PAPER_RUNTIME_ENTRY_FILL":
                return PaperPortfolioValidationResult("FAIL", "paper position entry strategy context source is invalid", "SCHEMA_IDENTITY_MISMATCH")
            if position.get("entry_strategy_family") not in PAPER_POSITION_STRATEGY_FAMILIES:
                return PaperPortfolioValidationResult("FAIL", "paper position entry strategy family is unsupported", "SCHEMA_IDENTITY_MISMATCH")
            if position.get("entry_strategy_exit_policy_id") != "UPBIT_KRW_SPOT_STRATEGY_EXIT_ROUTER_V1":
                return PaperPortfolioValidationResult("FAIL", "paper position entry exit policy id mismatch", "SCHEMA_IDENTITY_MISMATCH")
            if position.get("entry_strategy_exit_variation") not in PAPER_POSITION_STRATEGY_EXIT_VARIATIONS:
                return PaperPortfolioValidationResult("FAIL", "paper position entry exit variation is unsupported", "SCHEMA_IDENTITY_MISMATCH")
            for hash_field in ("entry_strategy_source_candidate_hash", "entry_strategy_source_exit_plan_hash"):
                if not isinstance(position.get(hash_field), str) or len(str(position.get(hash_field))) != 64:
                    return PaperPortfolioValidationResult("FAIL", f"paper position {hash_field} is invalid", "SCHEMA_IDENTITY_MISMATCH")
            for text_field in (
                "entry_candidate_id",
                "entry_strategy_source_runtime_cycle_id",
                "entry_strategy_context_formula",
            ):
                if not isinstance(position.get(text_field), str) or not position.get(text_field):
                    return PaperPortfolioValidationResult("FAIL", f"paper position {text_field} is invalid", "SCHEMA_IDENTITY_MISMATCH")
        position_value_sum += market_value
        position_unrealized_sum += position_unrealized
    if position_market_value != position_value_sum:
        return PaperPortfolioValidationResult("FAIL", "paper portfolio position market value rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if unrealized != position_unrealized_sum:
        return PaperPortfolioValidationResult("FAIL", "paper portfolio unrealized PnL rollup mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if snapshot.get("snapshot_status") == "PASS" and snapshot.get("blockers"):
        return PaperPortfolioValidationResult("BLOCKED", "paper portfolio PASS cannot carry blockers", snapshot["blockers"][0].get("code", "UNKNOWN_BLOCKED"))
    return PaperPortfolioValidationResult("PASS", "paper portfolio snapshot is simulated, scoped, and live-blocked", None)
