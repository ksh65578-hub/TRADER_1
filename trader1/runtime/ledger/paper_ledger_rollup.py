from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from trader1.core.ledger.paper_ledger import (
    count_incomplete_upbit_paper_order_lifecycles,
    validate_upbit_paper_ledger,
)
from trader1.runtime.ledger.paper_ledger_input_manifest import (
    PAPER_LEDGER_INPUT_MANIFEST_SCOPE,
    load_paper_ledger_input_manifest,
    manifest_excluded_ledger_paths,
    paper_ledger_input_manifest_path,
    validate_paper_ledger_input_manifest,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json, recover_jsonl_records
from trader1.runtime.portfolio.paper_portfolio import (
    PAPER_PORTFOLIO_SCHEMA_ID,
    PAPER_STARTING_CASH_BY_SCOPE,
    paper_portfolio_hash,
    validate_paper_portfolio_snapshot,
)


PAPER_LEDGER_ROLLUP_SCHEMA_ID = "trader1.paper_ledger_rollup_report.v1"
PAPER_LEDGER_HEAD_SCHEMA_ID = "trader1.paper_ledger_head.v1"


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


def paper_ledger_head_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("head_report_hash", None)
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


def _latest_head_ledger_path(*, root: Path, ledger_dir: Path, cycle_dir: Path, session_id: str) -> Path | None:
    ledger_head_path = ledger_dir / "latest_paper_ledger_head.json"
    try:
        ledger_head = json.loads(ledger_head_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    if (
        ledger_head.get("schema_id") != PAPER_LEDGER_HEAD_SCHEMA_ID
        or ledger_head.get("project_id") != "TRADER_1"
        or ledger_head.get("exchange") != "UPBIT"
        or ledger_head.get("market_type") != "KRW_SPOT"
        or ledger_head.get("mode") != "PAPER"
        or ledger_head.get("session_id") != session_id
    ):
        return None
    ledger_events_path = ledger_head.get("ledger_events_path")
    if not isinstance(ledger_events_path, str) or not ledger_events_path:
        return None
    candidate = (root / ledger_events_path).resolve()
    try:
        candidate.relative_to(cycle_dir.resolve())
    except ValueError:
        return None
    if not candidate.name.endswith(".paper_ledger_events.jsonl"):
        return None
    return candidate


def _order_session_cycle_ledger_paths(*, root: Path, ledger_dir: Path, cycle_dir: Path, session_id: str, ledger_paths: list[Path]) -> list[Path]:
    ordered_paths = sorted(ledger_paths)
    latest_head_path = _latest_head_ledger_path(root=root, ledger_dir=ledger_dir, cycle_dir=cycle_dir, session_id=session_id)
    if latest_head_path is None:
        return ordered_paths
    latest_head_path = latest_head_path.resolve()
    head_matches = [path for path in ordered_paths if path.resolve() == latest_head_path]
    if not head_matches:
        return ordered_paths
    return [path for path in ordered_paths if path.resolve() != latest_head_path] + head_matches


def _ledger_paths_from_active_manifest(
    *,
    root: Path,
    ledger_dir: Path,
    cycle_dir: Path,
    session_id: str,
    blockers: list[dict[str, str]],
) -> tuple[list[Path] | None, list[str], bool]:
    manifest_path = paper_ledger_input_manifest_path(root, session_id)
    manifest, load_error = load_paper_ledger_input_manifest(root=root, session_id=session_id)
    if load_error == "MISSING":
        return None, [], False
    manifest_artifacts = [_relative_posix(manifest_path, root)]
    if manifest is None:
        blockers.append(_blocker("RECONCILIATION_REQUIRED", f"PAPER ledger input manifest could not be loaded: {load_error}"))
        return [], manifest_artifacts, False
    manifest_result = validate_paper_ledger_input_manifest(manifest)
    if manifest_result.status != "PASS":
        blockers.append(
            _blocker(
                manifest_result.blocker_code or "RECONCILIATION_REQUIRED",
                f"PAPER ledger input manifest did not validate PASS: {manifest_result.message}",
            )
        )
        return [], manifest_artifacts, False
    excluded = manifest_excluded_ledger_paths(manifest)
    all_paths = sorted(cycle_dir.glob("*.paper_ledger_events.jsonl")) if cycle_dir.exists() else []
    all_relative_paths = {_relative_posix(path, root): path for path in all_paths}
    missing_excluded = sorted(path for path in excluded if path not in all_relative_paths)
    if missing_excluded:
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "PAPER ledger input manifest excluded paths are missing from source scope"))
    included_paths = [path for relative_path, path in all_relative_paths.items() if relative_path not in excluded]
    ordered = _order_session_cycle_ledger_paths(
        root=root,
        ledger_dir=ledger_dir,
        cycle_dir=cycle_dir,
        session_id=session_id,
        ledger_paths=included_paths,
    )
    latest_head_path = _latest_head_ledger_path(root=root, ledger_dir=ledger_dir, cycle_dir=cycle_dir, session_id=session_id)
    require_head = latest_head_path is not None and _relative_posix(latest_head_path, root) not in excluded
    return ordered, manifest_artifacts, require_head


def _build_ledger_head_binding(
    *,
    root: Path,
    ledger_dir: Path,
    session_id: str,
    ledger_paths: list[Path],
    require_latest_head_report: bool,
    latest_source_runtime_cycle_id: str | None,
    latest_source_ledger_path: Path | None,
    latest_source_ledger_event_count: int,
    latest_ledger_head_hash: str | None,
    artifact_paths: list[str],
    blockers: list[dict[str, str]],
) -> dict[str, Any]:
    if not require_latest_head_report:
        return {
            "ledger_head_report_path": None,
            "ledger_head_report_hash": None,
            "ledger_head_cycle_id": None,
            "ledger_head_event_count": 0,
            "ledger_head_match_status": "NOT_APPLICABLE",
            "ledger_head_mismatch_count": 0,
        }
    if not ledger_paths:
        return {
            "ledger_head_report_path": None,
            "ledger_head_report_hash": None,
            "ledger_head_cycle_id": None,
            "ledger_head_event_count": 0,
            "ledger_head_match_status": "NOT_APPLICABLE",
            "ledger_head_mismatch_count": 0,
        }

    ledger_head_path = ledger_dir / "latest_paper_ledger_head.json"
    if not ledger_head_path.exists():
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "latest PAPER ledger head report is missing"))
        return {
            "ledger_head_report_path": None,
            "ledger_head_report_hash": None,
            "ledger_head_cycle_id": None,
            "ledger_head_event_count": 0,
            "ledger_head_match_status": "MISSING",
            "ledger_head_mismatch_count": 1,
        }

    artifact_paths.append(_relative_posix(ledger_head_path, root))
    mismatch_count = 0
    try:
        ledger_head = json.loads(ledger_head_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "latest PAPER ledger head report is not valid JSON"))
        return {
            "ledger_head_report_path": _relative_posix(ledger_head_path, root),
            "ledger_head_report_hash": None,
            "ledger_head_cycle_id": None,
            "ledger_head_event_count": 0,
            "ledger_head_match_status": "MISMATCH",
            "ledger_head_mismatch_count": 1,
        }

    if ledger_head.get("schema_id") != PAPER_LEDGER_HEAD_SCHEMA_ID or ledger_head.get("project_id") != "TRADER_1":
        mismatch_count += 1
    if (
        ledger_head.get("exchange") != "UPBIT"
        or ledger_head.get("market_type") != "KRW_SPOT"
        or ledger_head.get("mode") != "PAPER"
        or ledger_head.get("session_id") != session_id
    ):
        mismatch_count += 1
    if any(
        ledger_head.get(field)
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
    ):
        mismatch_count += 1
    if ledger_head.get("head_report_hash") != paper_ledger_head_report_hash(ledger_head):
        mismatch_count += 1
    if latest_source_runtime_cycle_id and ledger_head.get("cycle_id") != latest_source_runtime_cycle_id:
        mismatch_count += 1
    if latest_ledger_head_hash and ledger_head.get("ledger_head_hash") != latest_ledger_head_hash:
        mismatch_count += 1
    if latest_source_ledger_event_count > 0 and ledger_head.get("ledger_event_count") != latest_source_ledger_event_count:
        mismatch_count += 1
    if latest_source_ledger_path is not None and ledger_head.get("ledger_events_path") != _relative_posix(latest_source_ledger_path, root):
        mismatch_count += 1
    try:
        ledger_head_event_count = int(ledger_head.get("ledger_event_count", 0) or 0)
    except (TypeError, ValueError):
        ledger_head_event_count = 0
        mismatch_count += 1

    if mismatch_count:
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "latest PAPER ledger head report does not match rollup head"))
    return {
        "ledger_head_report_path": _relative_posix(ledger_head_path, root),
        "ledger_head_report_hash": ledger_head.get("head_report_hash"),
        "ledger_head_cycle_id": ledger_head.get("cycle_id"),
        "ledger_head_event_count": ledger_head_event_count,
        "ledger_head_match_status": "PASS" if mismatch_count == 0 else "MISMATCH",
        "ledger_head_mismatch_count": mismatch_count,
    }


def _portfolio_snapshot_from_fills(
    *,
    session_id: str,
    fill_events: list[dict[str, Any]],
    blockers: list[dict[str, str]],
    source_runtime_cycle_id: str | None,
    source_paper_ledger_head_hash: str | None,
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
    max_exposure = max(Decimal("0"), equity * Decimal("0.35"))
    if position_market_value > max_exposure:
        blockers.append(_blocker("RISK_VETO", "PAPER ledger rollup position exposure exceeds 35% of simulated equity"))
    return_pct = Decimal("0") if starting <= 0 else ((equity - starting) / starting * Decimal("100"))
    snapshot = {
        "schema_id": PAPER_PORTFOLIO_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "source_runtime_cycle_id": source_runtime_cycle_id,
        "source_paper_ledger_head_hash": source_paper_ledger_head_hash,
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
    ledger_paths: list[Path] | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    base = _runtime_base_dir(root, session_id)
    ledger_dir = base / "ledger"
    cycle_dir = ledger_dir / "cycles"
    blockers: list[dict[str, str]] = []
    ledger_input_artifact_paths: list[str] = []
    require_latest_head_report = False
    if ledger_paths is None:
        ledger_input_scope = "SESSION_CYCLE_GLOB"
        manifest_paths, manifest_artifacts, manifest_requires_head = _ledger_paths_from_active_manifest(
            root=root,
            ledger_dir=ledger_dir,
            cycle_dir=cycle_dir,
            session_id=session_id,
            blockers=blockers,
        )
        if manifest_paths is not None:
            ledger_input_scope = PAPER_LEDGER_INPUT_MANIFEST_SCOPE
            ledger_paths = manifest_paths
            ledger_input_artifact_paths.extend(manifest_artifacts)
            require_latest_head_report = manifest_requires_head
        else:
            ledger_paths = (
                _order_session_cycle_ledger_paths(
                    root=root,
                    ledger_dir=ledger_dir,
                    cycle_dir=cycle_dir,
                    session_id=session_id,
                    ledger_paths=list(cycle_dir.glob("*.paper_ledger_events.jsonl")),
                )
                if cycle_dir.exists()
                else []
            )
            require_latest_head_report = True
        duplicate_ledger_path_count = 0
    else:
        ledger_input_scope = "EXPLICIT_SCOPED_PATHS"
        scoped_paths: list[Path] = []
        cycle_dir_resolved = cycle_dir.resolve()
        for ledger_path in ledger_paths:
            resolved_path = Path(ledger_path).resolve()
            try:
                resolved_path.relative_to(cycle_dir_resolved)
            except ValueError:
                blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "scoped PAPER ledger rollup path escaped cycle ledger namespace"))
                continue
            if resolved_path.name.endswith(".paper_ledger_events.jsonl"):
                scoped_paths.append(resolved_path)
            else:
                blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "scoped PAPER ledger rollup path is not a cycle ledger JSONL artifact"))
        ledger_paths = sorted(scoped_paths)
        unique_scoped_paths = {str(path) for path in ledger_paths}
        duplicate_ledger_path_count = len(ledger_paths) - len(unique_scoped_paths)
        if duplicate_ledger_path_count:
            blockers.append(_blocker("RECONCILIATION_REQUIRED", "duplicate PAPER ledger JSONL path requires reconciliation"))
    artifact_paths: list[str] = []
    artifact_paths.extend(ledger_input_artifact_paths)
    all_events: list[dict[str, Any]] = []
    fill_events: list[dict[str, Any]] = []
    duplicate_event_count = 0
    duplicate_order_count = 0
    lifecycle_incomplete_order_count = 0
    corrupted_ledger_jsonl_quarantined_count = 0
    invalid_ledger_jsonl_count = 0
    seen_event_ids: set[str] = set()
    seen_dedup_keys: set[str] = set()
    seen_semantic_events: set[tuple[str, Any, Any, Any]] = set()
    seen_filled_order_keys: set[tuple[Any, Any]] = set()
    latest_ledger_head_hash: str | None = None
    latest_source_runtime_cycle_id: str | None = None
    latest_source_ledger_path: Path | None = None
    latest_source_ledger_event_count = 0

    if not ledger_paths:
        blockers.append(_blocker("LEDGER_UNAVAILABLE", "no PAPER ledger JSONL files are available for rollup"))

    for path in ledger_paths:
        artifact_paths.append(_relative_posix(path, root))
        source_runtime_cycle_id = path.name[: -len(".paper_ledger_events.jsonl")]
        records, quarantine_path = recover_jsonl_records(path)
        if quarantine_path is not None:
            corrupted_ledger_jsonl_quarantined_count += 1
            artifact_paths.append(_relative_posix(quarantine_path, root))
            blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "corrupted PAPER ledger JSONL was quarantined during rollup"))
        if not records:
            continue
        lifecycle_incomplete_order_count += count_incomplete_upbit_paper_order_lifecycles(records)
        ledger_status, ledger_blocker, ledger_message = validate_upbit_paper_ledger(records)
        if ledger_status != "PASS":
            invalid_ledger_jsonl_count += 1
            blockers.append(_blocker(ledger_blocker or "LEDGER_INTEGRITY_FAIL", ledger_message))
            continue
        latest_source_runtime_cycle_id = source_runtime_cycle_id
        latest_source_ledger_path = path
        latest_source_ledger_event_count = len(records)
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

    ledger_head_binding = _build_ledger_head_binding(
        root=root,
        ledger_dir=ledger_dir,
        session_id=session_id,
        ledger_paths=ledger_paths,
        require_latest_head_report=require_latest_head_report,
        latest_source_runtime_cycle_id=latest_source_runtime_cycle_id,
        latest_source_ledger_path=latest_source_ledger_path,
        latest_source_ledger_event_count=latest_source_ledger_event_count,
        latest_ledger_head_hash=latest_ledger_head_hash,
        artifact_paths=artifact_paths,
        blockers=blockers,
    )

    portfolio_snapshot = _portfolio_snapshot_from_fills(
        session_id=session_id,
        fill_events=fill_events,
        blockers=blockers,
        source_runtime_cycle_id=latest_source_runtime_cycle_id,
        source_paper_ledger_head_hash=latest_ledger_head_hash,
    )
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
        "ledger_input_scope": ledger_input_scope,
        "ledger_jsonl_count": len(ledger_paths),
        "ledger_event_count": len(all_events),
        "filled_order_count": len(fill_events),
        "duplicate_ledger_path_count": duplicate_ledger_path_count,
        "duplicate_event_count": duplicate_event_count,
        "duplicate_order_count": duplicate_order_count,
        "lifecycle_incomplete_order_count": lifecycle_incomplete_order_count,
        "corrupted_ledger_jsonl_quarantined_count": corrupted_ledger_jsonl_quarantined_count,
        "invalid_ledger_jsonl_count": invalid_ledger_jsonl_count,
        "latest_ledger_head_hash": latest_ledger_head_hash,
        **ledger_head_binding,
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
        "ledger_input_scope",
        "ledger_jsonl_count",
        "ledger_event_count",
        "filled_order_count",
        "duplicate_ledger_path_count",
        "duplicate_event_count",
        "duplicate_order_count",
        "lifecycle_incomplete_order_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "invalid_ledger_jsonl_count",
        "latest_ledger_head_hash",
        "ledger_head_report_path",
        "ledger_head_report_hash",
        "ledger_head_cycle_id",
        "ledger_head_event_count",
        "ledger_head_match_status",
        "ledger_head_mismatch_count",
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
        "duplicate_ledger_path_count",
        "duplicate_event_count",
        "duplicate_order_count",
        "lifecycle_incomplete_order_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "invalid_ledger_jsonl_count",
        "ledger_head_event_count",
        "ledger_head_mismatch_count",
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
    if report.get("ledger_head_match_status") not in {"PASS", "MISSING", "MISMATCH", "NOT_APPLICABLE"}:
        return PaperLedgerRollupValidationResult("FAIL", "paper ledger rollup head match status invalid", "SCHEMA_IDENTITY_MISMATCH")
    valid_input_scopes = {"SESSION_CYCLE_GLOB", "EXPLICIT_SCOPED_PATHS", PAPER_LEDGER_INPUT_MANIFEST_SCOPE}
    if report.get("ledger_input_scope") not in valid_input_scopes:
        return PaperLedgerRollupValidationResult("FAIL", "paper ledger rollup input scope invalid", "SCHEMA_IDENTITY_MISMATCH")
    if (
        report.get("ledger_jsonl_count") > 0
        and report.get("ledger_head_match_status") == "NOT_APPLICABLE"
        and report.get("ledger_input_scope") not in {"EXPLICIT_SCOPED_PATHS", PAPER_LEDGER_INPUT_MANIFEST_SCOPE}
    ):
        return PaperLedgerRollupValidationResult("FAIL", "PAPER ledger inputs require latest ledger head binding", "LEDGER_INTEGRITY_FAIL")
    if report.get("ledger_input_scope") == PAPER_LEDGER_INPUT_MANIFEST_SCOPE:
        expected_manifest_path = (
            f"system/runtime/upbit/krw_spot/paper/{report.get('session_id')}/ledger/paper_ledger_input_manifest.json"
        )
        if expected_manifest_path not in report.get("artifact_paths", []):
            return PaperLedgerRollupValidationResult("FAIL", "manifest-scoped rollup missing source input manifest", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("duplicate_ledger_path_count"):
        if report.get("rollup_status") != "BLOCKED":
            return PaperLedgerRollupValidationResult("BLOCKED", "duplicate PAPER ledger paths must block review", "RECONCILIATION_REQUIRED")
    if report.get("ledger_head_mismatch_count") and report.get("ledger_head_match_status") == "PASS":
        return PaperLedgerRollupValidationResult("FAIL", "PASS ledger head binding cannot carry mismatches", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("ledger_head_match_status") in {"MISSING", "MISMATCH"} and report.get("rollup_status") == "PASS":
        return PaperLedgerRollupValidationResult("BLOCKED", "PAPER ledger head binding mismatch must block rollup review", "LEDGER_INTEGRITY_FAIL")
    if report.get("rollup_status") == "PASS" and report.get("ledger_event_count") > 0:
        if not isinstance(report.get("latest_ledger_head_hash"), str) or len(report["latest_ledger_head_hash"]) != 64:
            return PaperLedgerRollupValidationResult("FAIL", "PASS paper ledger rollup requires latest ledger head hash", "LEDGER_INTEGRITY_FAIL")
        if report.get("ledger_input_scope") in {"SESSION_CYCLE_GLOB", PAPER_LEDGER_INPUT_MANIFEST_SCOPE} and report.get("ledger_head_match_status") == "PASS":
            if report.get("ledger_head_match_status") != "PASS" or report.get("ledger_head_mismatch_count") != 0:
                return PaperLedgerRollupValidationResult("FAIL", "PASS paper ledger rollup requires matching ledger head report", "LEDGER_INTEGRITY_FAIL")
            if not isinstance(report.get("ledger_head_report_path"), str) or not report.get("ledger_head_report_path"):
                return PaperLedgerRollupValidationResult("FAIL", "PASS paper ledger rollup requires ledger head report path", "LEDGER_INTEGRITY_FAIL")
            if not isinstance(report.get("ledger_head_report_hash"), str) or len(report["ledger_head_report_hash"]) != 64:
                return PaperLedgerRollupValidationResult("FAIL", "PASS paper ledger rollup requires ledger head report hash", "LEDGER_INTEGRITY_FAIL")
            if report.get("ledger_head_cycle_id") != report.get("portfolio_snapshot", {}).get("source_runtime_cycle_id"):
                return PaperLedgerRollupValidationResult("FAIL", "paper ledger head cycle does not match portfolio source cycle", "LEDGER_INTEGRITY_FAIL")
        elif report.get("ledger_input_scope") == PAPER_LEDGER_INPUT_MANIFEST_SCOPE and report.get("ledger_head_match_status") == "NOT_APPLICABLE":
            pass
        elif report.get("ledger_head_match_status") != "NOT_APPLICABLE":
            return PaperLedgerRollupValidationResult("FAIL", "explicit PAPER ledger rollup must not claim latest head binding", "LEDGER_INTEGRITY_FAIL")
    if report.get("duplicate_event_count") or report.get("duplicate_order_count"):
        if report.get("rollup_status") != "BLOCKED":
            return PaperLedgerRollupValidationResult("BLOCKED", "duplicate PAPER ledger rollup must block review", "RECONCILIATION_REQUIRED")
    if report.get("lifecycle_incomplete_order_count"):
        if report.get("rollup_status") != "BLOCKED":
            return PaperLedgerRollupValidationResult("BLOCKED", "incomplete PAPER order lifecycle must block rollup review", "RECONCILIATION_REQUIRED")
    if report.get("corrupted_ledger_jsonl_quarantined_count") or report.get("invalid_ledger_jsonl_count"):
        if report.get("rollup_status") != "BLOCKED":
            return PaperLedgerRollupValidationResult("BLOCKED", "corrupted or invalid PAPER ledger rollup must block review", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    artifact_prefix = f"system/runtime/upbit/krw_spot/paper/{report.get('session_id')}/ledger/"
    for artifact_path in report.get("artifact_paths", []):
        if not isinstance(artifact_path, str) or not artifact_path.startswith(artifact_prefix) or ".." in artifact_path.replace("\\", "/").split("/"):
            return PaperLedgerRollupValidationResult("BLOCKED", "paper ledger rollup artifact path escaped PAPER ledger namespace", "SNAPSHOT_SCOPE_MISMATCH")
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
        if not isinstance(portfolio.get("source_runtime_cycle_id"), str) or not portfolio.get("source_runtime_cycle_id"):
            return PaperLedgerRollupValidationResult("FAIL", "PASS paper ledger rollup portfolio missing source runtime cycle id", "SCHEMA_IDENTITY_MISMATCH")
        if portfolio.get("source_paper_ledger_head_hash") != report.get("latest_ledger_head_hash"):
            return PaperLedgerRollupValidationResult("FAIL", "paper ledger rollup portfolio ledger head provenance mismatch", "LEDGER_INTEGRITY_FAIL")
        position_count = int(portfolio.get("open_position_count", -1))
        filled_count = int(report.get("filled_order_count", -1))
        if filled_count > 0 and position_count < 1:
            return PaperLedgerRollupValidationResult("FAIL", "filled PAPER rollup requires at least one portfolio position", "SCHEMA_IDENTITY_MISMATCH")
        if position_count > filled_count:
            return PaperLedgerRollupValidationResult("FAIL", "paper rollup portfolio position count exceeds filled order count", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("rollup_status") == "PASS":
        return PaperLedgerRollupValidationResult("PASS", "PAPER ledger rollup is cumulative, scoped, and live-blocked", None)
    return PaperLedgerRollupValidationResult("BLOCKED", "PAPER ledger rollup is blocked", report.get("primary_blocker_code") or "UNKNOWN_BLOCKED")
