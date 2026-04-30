from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from trader1.core.ledger.paper_ledger import validate_upbit_paper_ledger
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json, recover_jsonl_records
from trader1.runtime.portfolio.paper_portfolio import (
    PAPER_PORTFOLIO_SCHEMA_ID,
    PAPER_STARTING_CASH_BY_SCOPE,
    paper_portfolio_hash,
    validate_paper_portfolio_snapshot,
)


PAPER_LEDGER_ROLLUP_SCHEMA_ID = "trader1.paper_ledger_rollup_report.v1"


@dataclass(frozen=True)
class PaperLedgerRollupValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def paper_ledger_rollup_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("rollup_hash", None)
    return _sha256_json(payload)


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("-1")


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f") if value != value.to_integral() else str(value.quantize(Decimal("1")))


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _runtime_base_dir(root: Path, session_id: str) -> Path:
    return root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _portfolio_snapshot_from_fills(
    *,
    session_id: str,
    fill_events: list[dict[str, Any]],
    blockers: list[dict[str, str]],
) -> dict[str, Any]:
    currency, starting = PAPER_STARTING_CASH_BY_SCOPE[("UPBIT", "KRW_SPOT")]
    positions_by_symbol: dict[str, dict[str, Decimal | str]] = {}
    gross_cost_total = Decimal("0")
    fee_total = Decimal("0")

    for event in fill_events:
        symbol = str(event.get("symbol") or "UNKNOWN")
        side = str(event.get("side") or "")
        qty = _decimal(event.get("quantity"))
        price = _decimal(event.get("price"))
        fee = _decimal(event.get("fee_amount") or "0")
        if side != "BUY" or qty <= 0 or price <= 0 or fee < 0:
            blockers.append(_blocker("RECONCILIATION_REQUIRED", "PAPER ledger rollup only supports valid long spot fill events"))
            continue
        current = positions_by_symbol.setdefault(
            symbol,
            {"quantity": Decimal("0"), "gross_cost": Decimal("0"), "fee": Decimal("0"), "mark_price": price},
        )
        current["quantity"] = Decimal(current["quantity"]) + qty
        current["gross_cost"] = Decimal(current["gross_cost"]) + (qty * price)
        current["fee"] = Decimal(current["fee"]) + fee
        current["mark_price"] = price
        gross_cost_total += qty * price
        fee_total += fee

    positions: list[dict[str, Any]] = []
    position_market_value = Decimal("0")
    unrealized_pnl = Decimal("0")
    for symbol, state in sorted(positions_by_symbol.items()):
        qty = Decimal(state["quantity"])
        gross_cost = Decimal(state["gross_cost"])
        fee = Decimal(state["fee"])
        mark_price = Decimal(state["mark_price"])
        average_entry = Decimal("0") if qty <= 0 else gross_cost / qty
        market_value = qty * mark_price
        position_unrealized = market_value - gross_cost - fee
        position_market_value += market_value
        unrealized_pnl += position_unrealized
        positions.append(
            {
                "symbol": symbol,
                "side": "LONG",
                "quantity": _decimal_text(qty),
                "average_entry_price": _decimal_text(average_entry),
                "mark_price": _decimal_text(mark_price),
                "cost_basis": _decimal_text(gross_cost + fee),
                "market_value": _decimal_text(market_value),
                "unrealized_pnl": _decimal_text(position_unrealized),
                "source": "PAPER_LEDGER_ROLLUP",
                "paper_only": True,
            }
        )

    realized_pnl = Decimal("0")
    total_pnl = realized_pnl + unrealized_pnl
    cash_available = starting - gross_cost_total - fee_total
    locked_balance = Decimal("0")
    equity = cash_available + locked_balance + position_market_value
    if cash_available < 0:
        blockers.append(_blocker("RISK_VETO", "PAPER ledger rollup would make simulated cash negative"))
    return_pct = Decimal("0") if starting <= 0 else ((equity - starting) / starting * Decimal("100"))
    snapshot = {
        "schema_id": PAPER_PORTFOLIO_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "snapshot_status": "PASS" if not blockers else "BLOCKED",
        "source": "PAPER_LEDGER_ROLLUP",
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
        "open_position_count": len(positions) if not blockers else 0,
        "positions": positions if not blockers else [],
        "paper_only": True,
        "display_balance_kind": "SIMULATED_PAPER_LEDGER",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "snapshot_hash": "",
    }
    snapshot["snapshot_hash"] = paper_portfolio_hash(snapshot)
    return snapshot


def build_paper_ledger_rollup_report(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    rollup_id: str = "paper-ledger-rollup",
) -> dict[str, Any]:
    root = Path(root).resolve()
    base = _runtime_base_dir(root, session_id)
    ledger_dir = base / "ledger"
    cycle_dir = ledger_dir / "cycles"
    ledger_paths = sorted(cycle_dir.glob("*.paper_ledger_events.jsonl")) if cycle_dir.exists() else []
    blockers: list[dict[str, str]] = []
    artifact_paths: list[str] = []
    all_events: list[dict[str, Any]] = []
    fill_events: list[dict[str, Any]] = []
    duplicate_event_count = 0
    duplicate_order_count = 0
    corrupted_ledger_jsonl_quarantined_count = 0
    invalid_ledger_jsonl_count = 0
    seen_event_ids: set[str] = set()
    seen_dedup_keys: set[str] = set()
    seen_semantic_events: set[tuple[str, Any, Any, Any]] = set()
    seen_filled_order_keys: set[tuple[Any, Any]] = set()
    latest_ledger_head_hash: str | None = None

    if not ledger_paths:
        blockers.append(_blocker("LEDGER_UNAVAILABLE", "no PAPER ledger JSONL files are available for rollup"))

    for path in ledger_paths:
        artifact_paths.append(_relative_posix(path, root))
        records, quarantine_path = recover_jsonl_records(path)
        if quarantine_path is not None:
            corrupted_ledger_jsonl_quarantined_count += 1
            artifact_paths.append(_relative_posix(quarantine_path, root))
            blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "corrupted PAPER ledger JSONL was quarantined during rollup"))
        if not records:
            continue
        ledger_status, ledger_blocker, ledger_message = validate_upbit_paper_ledger(records)
        if ledger_status != "PASS":
            invalid_ledger_jsonl_count += 1
            blockers.append(_blocker(ledger_blocker or "LEDGER_INTEGRITY_FAIL", ledger_message))
            continue
        for event in records:
            if event.get("exchange") != "UPBIT" or event.get("market_type") != "KRW_SPOT" or event.get("mode") != "PAPER" or event.get("session_id") != session_id:
                blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "PAPER ledger rollup detected cross-scope ledger data"))
                continue
            event_id = str(event.get("event_id"))
            if event_id in seen_event_ids:
                duplicate_event_count += 1
                blockers.append(_blocker("RECONCILIATION_REQUIRED", f"duplicate ledger event_id requires reconciliation: {event_id}"))
            seen_event_ids.add(event_id)
            dedup_key = str(event.get("dedup_key"))
            if dedup_key in seen_dedup_keys:
                duplicate_event_count += 1
                blockers.append(_blocker("RECONCILIATION_REQUIRED", f"duplicate ledger dedup_key requires reconciliation: {dedup_key}"))
            seen_dedup_keys.add(dedup_key)
            semantic_key = (str(event.get("event_type")), event.get("intent_id"), event.get("client_order_id"), event.get("order_id"))
            if (event.get("intent_id") or event.get("client_order_id") or event.get("order_id")) and semantic_key in seen_semantic_events:
                duplicate_event_count += 1
                blockers.append(_blocker("RECONCILIATION_REQUIRED", "duplicate semantic ledger event requires reconciliation"))
            seen_semantic_events.add(semantic_key)
            if event.get("event_type") == "ORDER_FILLED":
                filled_order_key = (event.get("client_order_id"), event.get("order_id"))
                if filled_order_key in seen_filled_order_keys:
                    duplicate_order_count += 1
                    blockers.append(_blocker("RECONCILIATION_REQUIRED", "duplicate filled PAPER order requires reconciliation"))
                seen_filled_order_keys.add(filled_order_key)
                fill_events.append(event)
            all_events.append(event)
            latest_ledger_head_hash = event.get("event_hash")

    portfolio_snapshot = _portfolio_snapshot_from_fills(session_id=session_id, fill_events=fill_events, blockers=blockers)
    portfolio_result = validate_paper_portfolio_snapshot(portfolio_snapshot)
    if portfolio_result.status != "PASS":
        if not blockers:
            blockers.append(_blocker(portfolio_result.blocker_code or "MEASUREMENT_MISSING", portfolio_result.message))
        portfolio_snapshot["snapshot_status"] = "BLOCKED"
        portfolio_snapshot["primary_blocker_code"] = blockers[0]["code"]
        portfolio_snapshot["blockers"] = blockers
        portfolio_snapshot["open_position_count"] = 0
        portfolio_snapshot["positions"] = []
        portfolio_snapshot["snapshot_hash"] = paper_portfolio_hash(portfolio_snapshot)

    status = "PASS" if not blockers else "BLOCKED"
    report = {
        "schema_id": PAPER_LEDGER_ROLLUP_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "rollup_id": rollup_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "ledger_source_dir": _relative_posix(cycle_dir, root),
        "ledger_jsonl_count": len(ledger_paths),
        "ledger_event_count": len(all_events),
        "filled_order_count": len(fill_events),
        "duplicate_event_count": duplicate_event_count,
        "duplicate_order_count": duplicate_order_count,
        "corrupted_ledger_jsonl_quarantined_count": corrupted_ledger_jsonl_quarantined_count,
        "invalid_ledger_jsonl_count": invalid_ledger_jsonl_count,
        "latest_ledger_head_hash": latest_ledger_head_hash,
        "portfolio_snapshot": portfolio_snapshot,
        "rollup_status": status,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "artifact_paths": sorted(set(artifact_paths)),
        "display_only": True,
        "dashboard_truth_only": True,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "rollup_hash": "",
    }
    report["rollup_hash"] = paper_ledger_rollup_hash(report)
    return report


def write_paper_ledger_rollup_report(*, root: Path, report: dict[str, Any]) -> Path:
    root = Path(root).resolve()
    base = _runtime_base_dir(root, str(report["session_id"])) / "ledger"
    path = base / f"{report['rollup_id']}.paper_ledger_rollup_report.json"
    durable_atomic_write_json(path, report)
    canonical_path = base / "paper_ledger_rollup_report.json"
    if canonical_path != path:
        durable_atomic_write_json(canonical_path, report)
    return path


def validate_paper_ledger_rollup_report(report: dict[str, Any]) -> PaperLedgerRollupValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "rollup_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "ledger_source_dir",
        "ledger_jsonl_count",
        "ledger_event_count",
        "filled_order_count",
        "duplicate_event_count",
        "duplicate_order_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "invalid_ledger_jsonl_count",
        "latest_ledger_head_hash",
        "portfolio_snapshot",
        "rollup_status",
        "primary_blocker_code",
        "blockers",
        "artifact_paths",
        "display_only",
        "dashboard_truth_only",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "rollup_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return PaperLedgerRollupValidationResult("FAIL", f"paper ledger rollup missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != PAPER_LEDGER_ROLLUP_SCHEMA_ID or report.get("project_id") != "TRADER_1":
        return PaperLedgerRollupValidationResult("FAIL", "paper ledger rollup identity mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("rollup_hash") != paper_ledger_rollup_hash(report):
        return PaperLedgerRollupValidationResult("FAIL", "paper ledger rollup hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return PaperLedgerRollupValidationResult("BLOCKED", "paper ledger rollup scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    forbidden = (
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden):
        return PaperLedgerRollupValidationResult("BLOCKED", "paper ledger rollup attempted live, promotion, or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    for count_field in (
        "ledger_jsonl_count",
        "ledger_event_count",
        "filled_order_count",
        "duplicate_event_count",
        "duplicate_order_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "invalid_ledger_jsonl_count",
    ):
        if not isinstance(report.get(count_field), int) or report.get(count_field) < 0:
            return PaperLedgerRollupValidationResult("FAIL", f"paper ledger rollup count invalid: {count_field}", "SCHEMA_IDENTITY_MISMATCH")
    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return PaperLedgerRollupValidationResult("FAIL", "paper ledger rollup blockers must be an array", "SCHEMA_IDENTITY_MISMATCH")
    blocker_codes = {item.get("code") for item in blockers if isinstance(item, dict)}
    if blockers and report.get("primary_blocker_code") not in blocker_codes:
        return PaperLedgerRollupValidationResult("BLOCKED", "paper ledger rollup primary blocker mismatch", report.get("primary_blocker_code") or "UNKNOWN_BLOCKED")
    if not blockers and report.get("primary_blocker_code") is not None:
        return PaperLedgerRollupValidationResult("FAIL", "paper ledger rollup primary blocker set without blockers", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("rollup_status") == "PASS" and blockers:
        return PaperLedgerRollupValidationResult("FAIL", "PASS paper ledger rollup cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("rollup_status") == "PASS" and report.get("ledger_jsonl_count") < 1:
        return PaperLedgerRollupValidationResult("BLOCKED", "PASS paper ledger rollup requires ledger JSONL input", "LEDGER_UNAVAILABLE")
    if report.get("ledger_event_count") < report.get("filled_order_count"):
        return PaperLedgerRollupValidationResult("FAIL", "paper ledger rollup event counts are inconsistent", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("rollup_status") == "PASS" and report.get("ledger_event_count") > 0:
        if not isinstance(report.get("latest_ledger_head_hash"), str) or len(report["latest_ledger_head_hash"]) != 64:
            return PaperLedgerRollupValidationResult("FAIL", "PASS paper ledger rollup requires latest ledger head hash", "LEDGER_INTEGRITY_FAIL")
    if report.get("duplicate_event_count") or report.get("duplicate_order_count"):
        if report.get("rollup_status") != "BLOCKED":
            return PaperLedgerRollupValidationResult("BLOCKED", "duplicate PAPER ledger rollup must block review", "RECONCILIATION_REQUIRED")
    if report.get("corrupted_ledger_jsonl_quarantined_count") or report.get("invalid_ledger_jsonl_count"):
        if report.get("rollup_status") != "BLOCKED":
            return PaperLedgerRollupValidationResult("BLOCKED", "corrupted or invalid PAPER ledger rollup must block review", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    portfolio = report.get("portfolio_snapshot")
    if not isinstance(portfolio, dict):
        return PaperLedgerRollupValidationResult("FAIL", "paper ledger rollup portfolio snapshot missing", "SCHEMA_IDENTITY_MISMATCH")
    portfolio_result = validate_paper_portfolio_snapshot(portfolio)
    if report.get("rollup_status") == "PASS" and portfolio_result.status != "PASS":
        return PaperLedgerRollupValidationResult(portfolio_result.status, portfolio_result.message, portfolio_result.blocker_code)
    if (
        portfolio.get("exchange") != report.get("exchange")
        or portfolio.get("market_type") != report.get("market_type")
        or portfolio.get("mode") != report.get("mode")
        or portfolio.get("session_id") != report.get("session_id")
    ):
        return PaperLedgerRollupValidationResult("BLOCKED", "paper ledger rollup portfolio scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    if portfolio.get("source") != "PAPER_LEDGER_ROLLUP":
        return PaperLedgerRollupValidationResult("BLOCKED", "paper ledger rollup portfolio source mismatch", "LIVE_FINAL_GUARD_FAILED")
    if report.get("rollup_status") == "PASS":
        position_count = int(portfolio.get("open_position_count", -1))
        filled_count = int(report.get("filled_order_count", -1))
        if filled_count > 0 and position_count < 1:
            return PaperLedgerRollupValidationResult("FAIL", "filled PAPER rollup requires at least one portfolio position", "SCHEMA_IDENTITY_MISMATCH")
        if position_count > filled_count:
            return PaperLedgerRollupValidationResult("FAIL", "paper rollup portfolio position count exceeds filled order count", "SCHEMA_IDENTITY_MISMATCH")
        artifact_prefix = f"system/runtime/upbit/krw_spot/paper/{report.get('session_id')}/ledger/"
        for artifact_path in report.get("artifact_paths", []):
            if not isinstance(artifact_path, str) or not artifact_path.startswith(artifact_prefix) or ".." in artifact_path.replace("\\", "/").split("/"):
                return PaperLedgerRollupValidationResult("BLOCKED", "paper ledger rollup artifact path escaped PAPER ledger namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("rollup_status") == "PASS":
        return PaperLedgerRollupValidationResult("PASS", "PAPER ledger rollup is cumulative, scoped, and live-blocked", None)
    return PaperLedgerRollupValidationResult("BLOCKED", "PAPER ledger rollup is blocked", report.get("primary_blocker_code") or "UNKNOWN_BLOCKED")
