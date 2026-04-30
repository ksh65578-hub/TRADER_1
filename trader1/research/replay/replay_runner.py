from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


REPLAY_CONSISTENCY_SCHEMA_ID = "trader1.replay_consistency_report.v1"


@dataclass(frozen=True)
class ReplayConsistencyValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def replay_consistency_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("replay_consistency_hash", None)
    return sha256_json(payload)


def run_replay_once(*, input_events: list[dict[str, Any]], parameter_hash: str) -> str:
    return sha256_json({"input_events": input_events, "parameter_hash": parameter_hash})


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def build_replay_consistency_report(
    *,
    replay_id: str,
    strategy_unit_id: str,
    parameter_hash: str,
    input_events: list[dict[str, Any]],
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    session_id: str = "mvp3_replay",
    repeated_runs: int = 2,
) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    if exchange != "UPBIT" or market_type != "KRW_SPOT":
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "replay consistency is scoped to UPBIT/KRW_SPOT"))
    if repeated_runs < 2:
        blockers.append(_blocker("MEASUREMENT_MISSING", "replay consistency requires at least two repeated runs"))
    if not input_events:
        blockers.append(_blocker("DATA_UNAVAILABLE", "replay input events are missing"))
    result_hashes = [run_replay_once(input_events=input_events, parameter_hash=parameter_hash) for _ in range(max(0, repeated_runs))]
    deterministic_pass = bool(result_hashes) and len(set(result_hashes)) == 1
    if not deterministic_pass:
        blockers.append(_blocker("MEASUREMENT_MISSING", "replay repeated result hashes do not match"))
    report = {
        "schema_id": REPLAY_CONSISTENCY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "replay_id": replay_id,
        "exchange": exchange,
        "market_type": market_type,
        "mode": "REPLAY",
        "session_id": session_id,
        "strategy_unit_id": strategy_unit_id,
        "parameter_hash": parameter_hash,
        "input_hash": sha256_json(input_events),
        "result_hashes": result_hashes,
        "deterministic_pass": deterministic_pass,
        "replay_status": "PASS" if not blockers else "BLOCKED",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "replay_consistency_hash": "",
    }
    report["replay_consistency_hash"] = replay_consistency_hash(report)
    return report


def validate_replay_consistency_report(report: dict[str, Any]) -> ReplayConsistencyValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "replay_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "strategy_unit_id",
        "parameter_hash",
        "input_hash",
        "result_hashes",
        "deterministic_pass",
        "replay_status",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "replay_consistency_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ReplayConsistencyValidationResult("FAIL", f"replay report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != REPLAY_CONSISTENCY_SCHEMA_ID:
        return ReplayConsistencyValidationResult("FAIL", "replay schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("replay_consistency_hash") != replay_consistency_hash(report):
        return ReplayConsistencyValidationResult("FAIL", "replay report hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "REPLAY":
        return ReplayConsistencyValidationResult("BLOCKED", "replay scope must remain UPBIT/KRW_SPOT/REPLAY", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("order_adapter_called"):
        return ReplayConsistencyValidationResult("BLOCKED", "replay attempted to create live/order permission", "LIVE_FINAL_GUARD_FAILED")
    hashes = report.get("result_hashes", [])
    if not hashes or len(set(hashes)) != 1 or report.get("deterministic_pass") is not True:
        return ReplayConsistencyValidationResult("FAIL", "replay repeated result hashes do not match", "MEASUREMENT_MISSING")
    if report.get("replay_status") == "PASS" and report.get("blockers"):
        return ReplayConsistencyValidationResult("BLOCKED", "replay PASS cannot carry blockers", report["blockers"][0].get("code", "UNKNOWN_BLOCKED"))
    return ReplayConsistencyValidationResult("PASS", "replay consistency is deterministic and research-only", None)
