from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.adapters.upbit.market_data import build_upbit_public_candle_fixture, validate_upbit_public_candle_data


UPBIT_PUBLIC_MARKET_DATA_COLLECTION_SCHEMA_ID = "trader1.upbit_public_market_data_collection_report.v1"
CANONICAL_MARKET_EVENT_SCHEMA_ID = "trader1.canonical_market_event.v1"


@dataclass(frozen=True)
class UpbitPublicMarketDataCollectionValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def canonical_market_event_hash(event: dict[str, Any]) -> str:
    payload = dict(event)
    payload.pop("event_hash", None)
    return _sha256_json(payload)


def upbit_public_market_data_collection_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("collection_hash", None)
    return _sha256_json(payload)


def public_market_data_hash(market_data: dict[str, Any]) -> str:
    return _sha256_json(market_data)


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _fsync_directory(path: Path) -> None:
    try:
        directory_fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def durable_atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        _fsync_directory(path.parent)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def durable_atomic_write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = "".join(json.dumps(record, sort_keys=True, separators=(",", ":"), default=str) + "\n" for record in records)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        _fsync_directory(path.parent)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def recover_jsonl_records(path: Path) -> tuple[list[dict[str, Any]], Path | None]:
    if not path.exists():
        return [], None
    valid_records: list[dict[str, Any]] = []
    invalid_lines: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines.append({"line_number": index, "line": line})
            continue
        if isinstance(value, dict):
            valid_records.append(value)
        else:
            invalid_lines.append({"line_number": index, "line": line})
    if not invalid_lines:
        return valid_records, None
    quarantine_path = path.with_name(f"{path.name}.corrupt.{time.time_ns()}.jsonl")
    durable_atomic_write_jsonl(quarantine_path, invalid_lines)
    durable_atomic_write_jsonl(path, valid_records)
    return valid_records, quarantine_path


def build_canonical_market_events(market_data: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for index, candle in enumerate(market_data.get("candles", []), start=1):
        event = {
            "schema_id": CANONICAL_MARKET_EVENT_SCHEMA_ID,
            "event_id": f"{market_data.get('session_id')}:{market_data.get('symbol')}:1m:{index}:{candle.get('timestamp')}",
            "generated_at_utc": utc_now(),
            "exchange": market_data.get("exchange"),
            "market_type": market_data.get("market_type"),
            "mode": market_data.get("mode"),
            "session_id": market_data.get("session_id"),
            "symbol": market_data.get("symbol"),
            "event_type": "CANDLE_1M",
            "timeframe": market_data.get("interval", "1m"),
            "source": market_data.get("source", "UNAVAILABLE"),
            "source_sequence": index,
            "event_time_utc": candle.get("timestamp"),
            "open": candle.get("open"),
            "high": candle.get("high"),
            "low": candle.get("low"),
            "close": candle.get("close"),
            "volume": candle.get("volume"),
            "is_public": True,
            "private_account_fields_present": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "event_hash": "",
        }
        event["event_hash"] = canonical_market_event_hash(event)
        events.append(event)
    return events


def build_upbit_public_market_data_collection_report(
    *,
    collector_id: str,
    session_id: str = "mvp1_upbit_paper_launcher",
    symbol: str = "KRW-BTC",
    market_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    market_data = market_data or build_upbit_public_candle_fixture(symbol=symbol, session_id=session_id)
    status, blocker_code, message = validate_upbit_public_candle_data(market_data, symbol=symbol, session_id=session_id)
    blockers = [] if status == "PASS" else [_blocker(blocker_code or "DATA_UNAVAILABLE", message)]
    canonical_events = build_canonical_market_events(market_data) if status == "PASS" else []
    report = {
        "schema_id": UPBIT_PUBLIC_MARKET_DATA_COLLECTION_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "collector_id": collector_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "symbol": symbol,
        "collector_mode": "PUBLIC_MARKET_DATA_ONLY",
        "data_source": market_data.get("source", "UNAVAILABLE"),
        "public_market_data": market_data,
        "public_market_data_hash": public_market_data_hash(market_data),
        "raw_sample_count": len(market_data.get("candles", [])) if isinstance(market_data.get("candles"), list) else 0,
        "canonical_event_count": len(canonical_events),
        "canonical_events": canonical_events,
        "collection_status": status,
        "primary_blocker_code": blocker_code,
        "blockers": blockers,
        "private_account_fields_present": bool(market_data.get("private_account_fields_present")),
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "collection_hash": "",
    }
    report["collection_hash"] = upbit_public_market_data_collection_hash(report)
    return report


def validate_upbit_public_market_data_collection_report(
    report: dict[str, Any],
) -> UpbitPublicMarketDataCollectionValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "collector_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "collector_mode",
        "data_source",
        "public_market_data",
        "public_market_data_hash",
        "raw_sample_count",
        "canonical_event_count",
        "canonical_events",
        "collection_status",
        "primary_blocker_code",
        "blockers",
        "private_account_fields_present",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "collection_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPublicMarketDataCollectionValidationResult("FAIL", f"collection report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PUBLIC_MARKET_DATA_COLLECTION_SCHEMA_ID:
        return UpbitPublicMarketDataCollectionValidationResult("FAIL", "collection schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("collection_hash") != upbit_public_market_data_collection_hash(report):
        return UpbitPublicMarketDataCollectionValidationResult("FAIL", "collection hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("public_market_data_hash") != public_market_data_hash(report["public_market_data"]):
        return UpbitPublicMarketDataCollectionValidationResult("FAIL", "public market data hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPublicMarketDataCollectionValidationResult("BLOCKED", "collection scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    forbidden_fields = (
        "private_account_fields_present",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden_fields):
        return UpbitPublicMarketDataCollectionValidationResult("BLOCKED", "collection attempted private, live, order, or scale-up behavior", "LIVE_FINAL_GUARD_FAILED")
    if report.get("collector_mode") != "PUBLIC_MARKET_DATA_ONLY":
        return UpbitPublicMarketDataCollectionValidationResult("BLOCKED", "unsupported collector mode", "LIVE_FINAL_GUARD_FAILED")
    data_status, data_blocker, data_message = validate_upbit_public_candle_data(
        report["public_market_data"],
        symbol=report["symbol"],
        session_id=report["session_id"],
    )
    if report.get("collection_status") != data_status:
        return UpbitPublicMarketDataCollectionValidationResult("FAIL", "collection status does not match public data validation", "SCHEMA_IDENTITY_MISMATCH")
    if data_status != "PASS":
        if not report.get("blockers"):
            return UpbitPublicMarketDataCollectionValidationResult("BLOCKED", "blocked collection must expose blocker", data_blocker)
        return UpbitPublicMarketDataCollectionValidationResult(data_status, data_message, data_blocker)
    events = report.get("canonical_events")
    if not isinstance(events, list) or not events:
        return UpbitPublicMarketDataCollectionValidationResult("FAIL", "PASS collection requires canonical events", "MEASUREMENT_MISSING")
    if report.get("raw_sample_count") != len(report["public_market_data"].get("candles", [])):
        return UpbitPublicMarketDataCollectionValidationResult("FAIL", "raw sample count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("canonical_event_count") != len(events):
        return UpbitPublicMarketDataCollectionValidationResult("FAIL", "canonical event count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_sequence = 1
    seen_hashes: set[str] = set()
    for event in events:
        if event.get("schema_id") != CANONICAL_MARKET_EVENT_SCHEMA_ID:
            return UpbitPublicMarketDataCollectionValidationResult("FAIL", "canonical event schema mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if event.get("event_hash") != canonical_market_event_hash(event):
            return UpbitPublicMarketDataCollectionValidationResult("FAIL", "canonical event hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if event["event_hash"] in seen_hashes:
            return UpbitPublicMarketDataCollectionValidationResult("BLOCKED", "duplicate canonical market event requires recovery", "RECONCILIATION_REQUIRED")
        seen_hashes.add(event["event_hash"])
        for key in ("exchange", "market_type", "mode", "session_id", "symbol"):
            if event.get(key) != report.get(key):
                return UpbitPublicMarketDataCollectionValidationResult("BLOCKED", f"canonical event scope mismatch: {key}", "SNAPSHOT_SCOPE_MISMATCH")
        if event.get("source_sequence") != expected_sequence:
            return UpbitPublicMarketDataCollectionValidationResult("FAIL", "canonical event sequence mismatch", "SCHEMA_IDENTITY_MISMATCH")
        expected_sequence += 1
        if event.get("private_account_fields_present") or not event.get("is_public"):
            return UpbitPublicMarketDataCollectionValidationResult("BLOCKED", "canonical event mixed private or non-public data", "LIVE_FINAL_GUARD_FAILED")
        if event.get("live_order_ready") or event.get("live_order_allowed") or event.get("can_live_trade") or event.get("scale_up_allowed"):
            return UpbitPublicMarketDataCollectionValidationResult("BLOCKED", "canonical event attempted live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    return UpbitPublicMarketDataCollectionValidationResult("PASS", "Upbit public market data collection is scoped, canonicalized, and live-blocked", None)


def upbit_public_market_data_artifact_dir(root: Path, report: dict[str, Any]) -> Path:
    return (
        root
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(report["session_id"])
        / "market_data"
        / "public"
    )


def write_upbit_public_market_data_collection_artifacts(*, root: Path, report: dict[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    result = validate_upbit_public_market_data_collection_report(report)
    base = upbit_public_market_data_artifact_dir(root, report)
    collector_id = str(report.get("collector_id", "UNKNOWN"))
    raw_path = base / "raw" / f"{collector_id}.raw_candles.json"
    canonical_path = base / "canonical" / f"{collector_id}.canonical_events.jsonl"
    report_path = base / "collection" / f"{collector_id}.collection_report.json"
    latest_path = base / "latest_collection_report.json"
    writer_report_path = base / "collection" / f"{collector_id}.writer_report.json"
    if result.status != "PASS":
        writer = {
            "schema_id": "trader1.upbit_public_market_data_collection_writer_report.v1",
            "generated_at_utc": utc_now(),
            "project_id": "TRADER_1",
            "writer_status": "BLOCKED",
            "collector_id": collector_id,
            "exchange": report.get("exchange"),
            "market_type": report.get("market_type"),
            "mode": report.get("mode"),
            "session_id": report.get("session_id"),
            "primary_blocker_code": result.blocker_code,
            "blocker_message": result.message,
            "artifact_paths": [],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        durable_atomic_write_json(writer_report_path, writer)
        return writer
    durable_atomic_write_json(raw_path, report["public_market_data"])
    durable_atomic_write_jsonl(canonical_path, report["canonical_events"])
    recovered_events, quarantine_path = recover_jsonl_records(canonical_path)
    durable_atomic_write_json(report_path, report)
    latest = {
        "schema_id": "trader1.upbit_public_market_data_latest_pointer.v1",
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "collector_id": collector_id,
        "report_path": _relative_posix(report_path, root),
        "report_hash": report["collection_hash"],
        "public_market_data_hash": report["public_market_data_hash"],
        "canonical_event_count": len(recovered_events),
        "quarantine_path": _relative_posix(quarantine_path, root) if quarantine_path else None,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    durable_atomic_write_json(latest_path, latest)
    writer = {
        "schema_id": "trader1.upbit_public_market_data_collection_writer_report.v1",
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "writer_status": "PASS" if quarantine_path is None else "BLOCKED",
        "collector_id": collector_id,
        "exchange": report["exchange"],
        "market_type": report["market_type"],
        "mode": report["mode"],
        "session_id": report["session_id"],
        "public_market_data_hash": report["public_market_data_hash"],
        "primary_blocker_code": None if quarantine_path is None else "PARTIAL_WRITE_RECOVERY_REQUIRED",
        "blocker_message": "public market data artifacts written atomically" if quarantine_path is None else "canonical JSONL required recovery",
        "artifact_paths": [
            _relative_posix(raw_path, root),
            _relative_posix(canonical_path, root),
            _relative_posix(report_path, root),
            _relative_posix(latest_path, root),
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    durable_atomic_write_json(writer_report_path, writer)
    return writer
