from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from trader1.core.ledger.paper_ledger import validate_upbit_paper_ledger
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json
from trader1.runtime.portfolio.paper_portfolio import (
    LEGACY_STATIC_KRW_BTC_MAX_PRICE,
    LEGACY_STATIC_KRW_BTC_MIN_PRICE,
    PAPER_STARTING_CASH_BY_SCOPE,
    PUBLIC_MARK_PRICE_BASIS_REPAIR_MAX_RATIO,
    PUBLIC_MARK_PRICE_BASIS_REPAIR_MIN_RATIO,
    UPBIT_KRW_BTC_PUBLIC_MARK_MAX_PRICE,
    UPBIT_KRW_BTC_PUBLIC_MARK_MIN_PRICE,
)


PAPER_LEDGER_INPUT_MANIFEST_SCHEMA_ID = "trader1.paper_ledger_input_manifest.v1"
PAPER_LEDGER_INPUT_MANIFEST_FILENAME = "paper_ledger_input_manifest.json"
PAPER_LEDGER_INPUT_MANIFEST_REASON = "CASH_OVERRUN_AND_EXPOSURE_REPAIR"
PAPER_LEDGER_INPUT_MANIFEST_SCOPE = "SESSION_REPAIR_MANIFEST"
MAX_EXPOSURE_TO_EQUITY_RATIO = Decimal("0.35")
MIN_CASH_AFTER_FILL = Decimal("0")
EXCLUDED_REASON_CODES = {
    "CASH_BELOW_ZERO",
    "EXPOSURE_CAP_EXCEEDED",
    "LEDGER_LOAD_FAILED",
    "INVALID_LEDGER_INPUT",
}


@dataclass(frozen=True)
class PaperLedgerInputManifestValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def paper_ledger_input_manifest_hash(manifest: dict[str, Any]) -> str:
    payload = dict(manifest)
    payload.pop("manifest_hash", None)
    return _sha256_json(payload)


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("-1")


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f") if value != value.to_integral() else str(value.quantize(Decimal("1")))


def _runtime_base_dir(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def paper_ledger_input_manifest_path(root: Path, session_id: str) -> Path:
    return _runtime_base_dir(root, session_id) / "ledger" / PAPER_LEDGER_INPUT_MANIFEST_FILENAME


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _ledger_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/cycles/")
        and normalized.endswith(".paper_ledger_events.jsonl")
        and ".." not in normalized.split("/")
        and "/live/" not in normalized
    )


def _safe_read_jsonl(path: Path) -> tuple[list[dict[str, Any]] | None, str, str | None]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None, "MISSING", None
    except OSError:
        return None, "UNREADABLE", None
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return None, "INVALID_UTF8", _sha256_bytes(raw)
    records: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            return None, "INVALID_JSON", _sha256_bytes(raw)
        if not isinstance(value, dict):
            return None, "NOT_OBJECT", _sha256_bytes(raw)
        records.append(value)
    return records, "PASS", _sha256_bytes(raw)


def _ledger_sort_key(path: Path) -> tuple[str, str]:
    records, status, _ = _safe_read_jsonl(path)
    if status != "PASS" or not records:
        return ("9999-12-31T23:59:59Z", path.name)
    times = [str(event.get("event_time_utc") or "") for event in records if isinstance(event, dict)]
    return (max(times) if times else "9999-12-31T23:59:59Z", path.name)


def _fill_cost(event: dict[str, Any]) -> tuple[Decimal, Decimal, Decimal]:
    qty = _decimal(event.get("quantity"))
    price = _decimal(event.get("price"))
    fee = _decimal(event.get("fee_amount") or "0")
    if qty <= 0 or price <= 0 or fee < 0:
        return Decimal("-1"), Decimal("-1"), Decimal("-1")
    notional = qty * price
    return notional, fee, notional + fee


def _position_market_value(positions_by_symbol: dict[str, dict[str, Decimal]]) -> Decimal:
    return sum(
        (state["quantity"] * state["mark_price"] for state in positions_by_symbol.values() if state["quantity"] > 0),
        Decimal("0"),
    )


def _copy_position_state(positions_by_symbol: dict[str, dict[str, Decimal]]) -> dict[str, dict[str, Decimal]]:
    return {symbol: dict(state) for symbol, state in positions_by_symbol.items()}


def _repair_legacy_public_sell_state(
    *,
    symbol: str,
    state: dict[str, Decimal],
    public_sell_price: Decimal,
) -> None:
    if symbol != "KRW-BTC" or public_sell_price <= 0:
        return
    current_qty = state["quantity"]
    current_gross_cost = state["gross_cost"]
    if current_qty <= 0 or current_gross_cost <= 0:
        return
    average_entry = current_gross_cost / current_qty
    if not (LEGACY_STATIC_KRW_BTC_MIN_PRICE <= average_entry <= LEGACY_STATIC_KRW_BTC_MAX_PRICE):
        return
    if not (UPBIT_KRW_BTC_PUBLIC_MARK_MIN_PRICE <= public_sell_price <= UPBIT_KRW_BTC_PUBLIC_MARK_MAX_PRICE):
        return
    ratio = public_sell_price / average_entry
    if not (PUBLIC_MARK_PRICE_BASIS_REPAIR_MIN_RATIO < ratio <= PUBLIC_MARK_PRICE_BASIS_REPAIR_MAX_RATIO):
        return
    normalized_quantity = current_gross_cost / public_sell_price
    if normalized_quantity <= 0:
        return
    state["quantity"] = normalized_quantity
    state["mark_price"] = public_sell_price


def _apply_paper_fill_to_manifest_state(
    *,
    positions_by_symbol: dict[str, dict[str, Decimal]],
    cash_available: Decimal,
    event: dict[str, Any],
) -> tuple[Decimal, str | None]:
    side = str(event.get("side") or "")
    symbol = str(event.get("symbol") or "UNKNOWN")
    qty = _decimal(event.get("quantity"))
    price = _decimal(event.get("price"))
    fee = _decimal(event.get("fee_amount") or "0")
    if side not in {"BUY", "SELL"} or qty <= 0 or price <= 0 or fee < 0:
        return cash_available, "INVALID_LEDGER_INPUT"
    notional = qty * price
    state = positions_by_symbol.setdefault(symbol, {"quantity": Decimal("0"), "gross_cost": Decimal("0"), "mark_price": price})
    current_qty = state["quantity"]
    current_gross_cost = state["gross_cost"]
    if side == "BUY":
        state["quantity"] = current_qty + qty
        state["gross_cost"] = current_gross_cost + notional
        state["mark_price"] = price
        return cash_available - notional - fee, None
    _repair_legacy_public_sell_state(symbol=symbol, state=state, public_sell_price=price)
    current_qty = state["quantity"]
    current_gross_cost = state["gross_cost"]
    if current_qty <= 0 or qty > current_qty:
        return cash_available, "INVALID_LEDGER_INPUT"
    sell_fraction = qty / current_qty
    state["quantity"] = current_qty - qty
    state["gross_cost"] = current_gross_cost - (current_gross_cost * sell_fraction)
    state["mark_price"] = price
    return cash_available + notional - fee, None


def _build_source_file(path: Path, root: Path, session_id: str) -> dict[str, Any]:
    records, load_status, file_hash = _safe_read_jsonl(path)
    rel = _relative_posix(path, root)
    ledger_status = "NOT_LOADED"
    ledger_blocker = "LEDGER_LOAD_FAILED"
    ledger_message = f"ledger load status: {load_status}"
    if records is not None:
        ledger_status, ledger_blocker, ledger_message = validate_upbit_paper_ledger(records)
    return {
        "path": rel,
        "path_allowed": _ledger_path_allowed(rel, session_id),
        "file_sha256": file_hash,
        "load_status": load_status,
        "ledger_validator_status": ledger_status,
        "ledger_validator_blocker_code": ledger_blocker,
        "ledger_validator_message": ledger_message,
        "event_count": len(records or []),
    }


def build_paper_ledger_input_manifest(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    manifest_id: str = "paper-ledger-cash-overrun-input-manifest",
) -> dict[str, Any]:
    root = Path(root).resolve()
    ledger_dir = _runtime_base_dir(root, session_id) / "ledger"
    cycle_dir = ledger_dir / "cycles"
    ledger_paths = sorted(cycle_dir.glob("*.paper_ledger_events.jsonl"), key=_ledger_sort_key) if cycle_dir.exists() else []
    _, starting_cash = PAPER_STARTING_CASH_BY_SCOPE[("UPBIT", "KRW_SPOT")]
    cash_available = starting_cash
    positions_by_symbol: dict[str, dict[str, Decimal]] = {}
    accepted: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []

    for path in ledger_paths:
        source = _build_source_file(path, root, session_id)
        source_files.append(source)
        records, load_status, _ = _safe_read_jsonl(path)
        rel = source["path"]
        if not source["path_allowed"] or load_status != "PASS" or records is None:
            excluded.append(
                {
                    "path": rel,
                    "file_sha256": source["file_sha256"],
                    "exclude_reason_code": "LEDGER_LOAD_FAILED",
                    "cash_available_before": _decimal_text(cash_available),
                    "cash_available_after": _decimal_text(cash_available),
                    "position_market_value_before": _decimal_text(_position_market_value(positions_by_symbol)),
                    "position_market_value_after": _decimal_text(_position_market_value(positions_by_symbol)),
                    "exposure_to_equity_after": "0",
                    "source_event_count": source["event_count"],
                    "source_ledger_head_hash": None,
                }
            )
            continue
        if source["ledger_validator_status"] != "PASS":
            excluded.append(
                {
                    "path": rel,
                    "file_sha256": source["file_sha256"],
                    "exclude_reason_code": "INVALID_LEDGER_INPUT",
                    "cash_available_before": _decimal_text(cash_available),
                    "cash_available_after": _decimal_text(cash_available),
                    "position_market_value_before": _decimal_text(_position_market_value(positions_by_symbol)),
                    "position_market_value_after": _decimal_text(_position_market_value(positions_by_symbol)),
                    "exposure_to_equity_after": "0",
                    "source_event_count": source["event_count"],
                    "source_ledger_head_hash": records[-1].get("event_hash") if records else None,
                }
            )
            continue

        next_cash = cash_available
        next_positions_by_symbol = _copy_position_state(positions_by_symbol)
        exclude_reason: str | None = None
        for event in records:
            if event.get("event_type") != "ORDER_FILLED":
                continue
            next_cash, exclude_reason = _apply_paper_fill_to_manifest_state(
                positions_by_symbol=next_positions_by_symbol,
                cash_available=next_cash,
                event=event,
            )
            if exclude_reason is not None:
                break
            next_position_market_value = _position_market_value(next_positions_by_symbol)
            next_equity = next_cash + next_position_market_value
            max_exposure = max(Decimal("0"), next_equity * MAX_EXPOSURE_TO_EQUITY_RATIO)
            if next_cash < MIN_CASH_AFTER_FILL:
                exclude_reason = "CASH_BELOW_ZERO"
                break
            if next_position_market_value > max_exposure:
                exclude_reason = "EXPOSURE_CAP_EXCEEDED"
                break

        next_position_market_value = _position_market_value(next_positions_by_symbol)
        next_equity = next_cash + next_position_market_value
        exposure_ratio = Decimal("0") if next_equity <= 0 else next_position_market_value / next_equity
        position_market_value = _position_market_value(positions_by_symbol)
        item = {
            "path": rel,
            "file_sha256": source["file_sha256"],
            "cash_available_before": _decimal_text(cash_available),
            "cash_available_after": _decimal_text(next_cash),
            "position_market_value_before": _decimal_text(position_market_value),
            "position_market_value_after": _decimal_text(next_position_market_value),
            "exposure_to_equity_after": _decimal_text(exposure_ratio),
            "source_event_count": source["event_count"],
            "source_ledger_head_hash": records[-1].get("event_hash") if records else None,
        }
        if exclude_reason is None:
            accepted.append(item)
            cash_available = next_cash
            positions_by_symbol = next_positions_by_symbol
        else:
            excluded.append({"exclude_reason_code": exclude_reason, **item})

    all_path_hash = _sha256_json(
        [{"path": item["path"], "file_sha256": item.get("file_sha256")} for item in source_files]
    )
    source_event_count = sum(int(item.get("event_count") or 0) for item in source_files)
    status = "NO_REPAIR_NEEDED"
    primary_blocker_code = None
    if excluded and accepted:
        status = "PASS"
    elif excluded and not accepted:
        status = "BLOCKED"
        primary_blocker_code = "RISK_VETO"
    manifest = {
        "schema_id": PAPER_LEDGER_INPUT_MANIFEST_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "manifest_id": manifest_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "manifest_reason": PAPER_LEDGER_INPUT_MANIFEST_REASON,
        "ledger_input_scope": PAPER_LEDGER_INPUT_MANIFEST_SCOPE,
        "ledger_source_dir": _relative_posix(cycle_dir, root),
        "all_ledger_path_count_at_manifest": len(source_files),
        "accepted_ledger_path_count_at_manifest": len(accepted),
        "excluded_ledger_path_count": len(excluded),
        "source_ledger_event_count_at_manifest": source_event_count,
        "source_all_ledger_path_hash": all_path_hash,
        "starting_cash": _decimal_text(starting_cash),
        "min_cash_after_fill": _decimal_text(MIN_CASH_AFTER_FILL),
        "max_exposure_to_equity_ratio": _decimal_text(MAX_EXPOSURE_TO_EQUITY_RATIO),
        "final_cash_available_after_accepted": _decimal_text(cash_available),
        "final_position_market_value_after_accepted": _decimal_text(_position_market_value(positions_by_symbol)),
        "source_ledger_files": source_files,
        "accepted_ledger_paths": accepted,
        "excluded_ledger_paths": excluded,
        "manifest_status": status,
        "primary_blocker_code": primary_blocker_code,
        "current_ledger_input_filter_active": True,
        "source_delete_allowed": False,
        "current_canonical_ledger_write_allowed": False,
        "current_evidence_write_allowed": False,
        "display_only": True,
        "dashboard_truth_only": True,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "manifest_hash": "",
    }
    manifest["manifest_hash"] = paper_ledger_input_manifest_hash(manifest)
    return manifest


def write_paper_ledger_input_manifest(*, root: Path, manifest: dict[str, Any]) -> Path:
    path = paper_ledger_input_manifest_path(Path(root), str(manifest["session_id"]))
    durable_atomic_write_json(path, manifest)
    return path


def load_paper_ledger_input_manifest(*, root: Path, session_id: str) -> tuple[dict[str, Any] | None, str | None]:
    path = paper_ledger_input_manifest_path(root, session_id)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "MISSING"
    except (OSError, json.JSONDecodeError):
        return None, "INVALID_JSON"
    if not isinstance(value, dict):
        return None, "NOT_OBJECT"
    return value, None


def manifest_excluded_ledger_paths(manifest: dict[str, Any]) -> set[str]:
    return {
        str(item.get("path"))
        for item in manifest.get("excluded_ledger_paths", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }


def validate_paper_ledger_input_manifest(manifest: dict[str, Any]) -> PaperLedgerInputManifestValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "manifest_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "manifest_reason",
        "ledger_input_scope",
        "ledger_source_dir",
        "all_ledger_path_count_at_manifest",
        "accepted_ledger_path_count_at_manifest",
        "excluded_ledger_path_count",
        "source_ledger_event_count_at_manifest",
        "source_all_ledger_path_hash",
        "starting_cash",
        "min_cash_after_fill",
        "max_exposure_to_equity_ratio",
        "final_cash_available_after_accepted",
        "final_position_market_value_after_accepted",
        "source_ledger_files",
        "accepted_ledger_paths",
        "excluded_ledger_paths",
        "manifest_status",
        "primary_blocker_code",
        "current_ledger_input_filter_active",
        "source_delete_allowed",
        "current_canonical_ledger_write_allowed",
        "current_evidence_write_allowed",
        "display_only",
        "dashboard_truth_only",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "manifest_hash",
    }
    missing = sorted(required - set(manifest))
    if missing:
        return PaperLedgerInputManifestValidationResult("FAIL", f"paper ledger input manifest missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if manifest.get("schema_id") != PAPER_LEDGER_INPUT_MANIFEST_SCHEMA_ID or manifest.get("project_id") != "TRADER_1":
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest identity mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if manifest.get("manifest_hash") != paper_ledger_input_manifest_hash(manifest):
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if manifest.get("exchange") != "UPBIT" or manifest.get("market_type") != "KRW_SPOT" or manifest.get("mode") != "PAPER":
        return PaperLedgerInputManifestValidationResult("BLOCKED", "paper ledger input manifest scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    if manifest.get("manifest_reason") != PAPER_LEDGER_INPUT_MANIFEST_REASON or manifest.get("ledger_input_scope") != PAPER_LEDGER_INPUT_MANIFEST_SCOPE:
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest reason or scope mismatch", "SCHEMA_IDENTITY_MISMATCH")
    forbidden = (
        "source_delete_allowed",
        "current_canonical_ledger_write_allowed",
        "current_evidence_write_allowed",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    if any(manifest.get(field) for field in forbidden):
        return PaperLedgerInputManifestValidationResult("BLOCKED", "paper ledger input manifest attempted forbidden mutation or live permission", "LIVE_FINAL_GUARD_FAILED")
    if manifest.get("current_ledger_input_filter_active") is not True or manifest.get("display_only") is not True or manifest.get("dashboard_truth_only") is not True:
        return PaperLedgerInputManifestValidationResult("BLOCKED", "paper ledger input manifest must stay an active display/current-input filter", "LIVE_FINAL_GUARD_FAILED")
    source_files = manifest.get("source_ledger_files")
    accepted = manifest.get("accepted_ledger_paths")
    excluded = manifest.get("excluded_ledger_paths")
    if not isinstance(source_files, list) or not isinstance(accepted, list) or not isinstance(excluded, list):
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest path lists must be arrays", "SCHEMA_IDENTITY_MISMATCH")
    if manifest.get("all_ledger_path_count_at_manifest") != len(source_files):
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest source count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if manifest.get("accepted_ledger_path_count_at_manifest") != len(accepted) or manifest.get("excluded_ledger_path_count") != len(excluded):
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest accepted/excluded count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    session_id = str(manifest.get("session_id"))
    source_paths = {str(item.get("path")) for item in source_files if isinstance(item, dict)}
    accepted_paths = {str(item.get("path")) for item in accepted if isinstance(item, dict)}
    excluded_paths = {str(item.get("path")) for item in excluded if isinstance(item, dict)}
    if len(source_paths) != len(source_files) or len(accepted_paths) != len(accepted) or len(excluded_paths) != len(excluded):
        return PaperLedgerInputManifestValidationResult("BLOCKED", "paper ledger input manifest duplicate paths require reconciliation", "RECONCILIATION_REQUIRED")
    if accepted_paths & excluded_paths or accepted_paths | excluded_paths != source_paths:
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest path partition mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_path_hash = _sha256_json(
        [{"path": item.get("path"), "file_sha256": item.get("file_sha256")} for item in source_files]
    )
    if manifest.get("source_all_ledger_path_hash") != expected_path_hash:
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest source path hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    event_count = sum(int(item.get("event_count") or 0) for item in source_files if isinstance(item, dict))
    if manifest.get("source_ledger_event_count_at_manifest") != event_count:
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest source event count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    for item in [*source_files, *accepted, *excluded]:
        if not isinstance(item, dict) or not _ledger_path_allowed(str(item.get("path") or ""), session_id):
            return PaperLedgerInputManifestValidationResult("BLOCKED", "paper ledger input manifest path escaped ledger namespace", "SNAPSHOT_SCOPE_MISMATCH")
    for item in excluded:
        if item.get("exclude_reason_code") not in EXCLUDED_REASON_CODES:
            return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest exclude reason mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if manifest.get("min_cash_after_fill") != _decimal_text(MIN_CASH_AFTER_FILL) or manifest.get("max_exposure_to_equity_ratio") != _decimal_text(MAX_EXPOSURE_TO_EQUITY_RATIO):
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest threshold mismatch", "SCHEMA_IDENTITY_MISMATCH")
    accepted_count = len(accepted)
    excluded_count = len(excluded)
    if accepted_count == 0 and excluded_count > 0:
        expected_status = "BLOCKED"
        expected_blocker = "RISK_VETO"
    elif excluded_count > 0:
        expected_status = "PASS"
        expected_blocker = None
    else:
        expected_status = "NO_REPAIR_NEEDED"
        expected_blocker = None
    if manifest.get("manifest_status") != expected_status or manifest.get("primary_blocker_code") != expected_blocker:
        return PaperLedgerInputManifestValidationResult("FAIL", "paper ledger input manifest status mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if expected_status == "BLOCKED":
        return PaperLedgerInputManifestValidationResult("BLOCKED", "paper ledger input manifest has no accepted current ledger paths", "RISK_VETO")
    return PaperLedgerInputManifestValidationResult("PASS", "paper ledger input manifest is scoped, auditable, and live-blocked", None)
