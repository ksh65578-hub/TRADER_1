from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.adapters.upbit.market_data import validate_upbit_public_candle_data
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


REPLAY_CONSISTENCY_SCHEMA_ID = "trader1.replay_consistency_report.v1"
PUBLIC_REPLAY_ROBUSTNESS_SCHEMA_ID = "trader1.public_replay_robustness_report.v1"
PUBLIC_REPLAY_VALUE_SOURCE = "PUBLIC_REST_REPLAY_DECISION_ADJUSTED_NET_EV_AFTER_COST_BPS"
PUBLIC_REPLAY_LEGACY_VALUE_SOURCE = "PUBLIC_REST_REPLAY_EXPECTED_NET_EV_AFTER_COST_BPS"
PUBLIC_REPLAY_FETCH_FAILED_SOURCE = "PUBLIC_REST_READ_ONLY_FETCH_FAILED"
PUBLIC_REPLAY_MIN_WINDOW_SIZE = 5
PUBLIC_REPLAY_DEFAULT_WINDOW_SIZE = 6
PUBLIC_REPLAY_DEFAULT_MAX_WINDOWS = 420
ROOT = Path(__file__).resolve().parents[3]


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


def public_replay_robustness_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("report_hash", None)
    return sha256_json(payload)


def run_replay_once(*, input_events: list[dict[str, Any]], parameter_hash: str) -> str:
    return sha256_json({"input_events": input_events, "parameter_hash": parameter_hash})


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _number(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    return result if math.isfinite(result) else 0.0


def _candidate_by_id(runtime_cycle: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
    selected = runtime_cycle.get("selected_candidate")
    if isinstance(selected, dict) and selected.get("candidate_id") == candidate_id:
        return selected
    for candidate in runtime_cycle.get("strategy_candidates") or []:
        if isinstance(candidate, dict) and candidate.get("candidate_id") == candidate_id:
            return candidate
    return None


def _public_replay_sample_row(
    *,
    replay_id: str,
    replay_index: int,
    window_candles: list[dict[str, Any]],
    runtime: dict[str, Any],
    candidate: dict[str, Any],
    strategy_id: Any,
) -> dict[str, Any]:
    opportunity_net_ev = _number(candidate.get("net_ev_after_cost_bps"))
    opportunity_gross_edge = _number(candidate.get("gross_expected_edge_bps"))
    opportunity_cost = _number(candidate.get("total_execution_cost_bps"))
    executed_trade = candidate.get("decision") == "PAPER_ENTRY_REVIEW"
    if executed_trade:
        net_ev_after_cost = opportunity_net_ev
        gross_expected_edge = opportunity_gross_edge
        total_execution_cost = opportunity_cost
        replay_return_basis = "EXECUTED_ENTRY_REVIEW_NET_EV_AFTER_COST"
    else:
        net_ev_after_cost = 0.0
        gross_expected_edge = 0.0
        total_execution_cost = 0.0
        replay_return_basis = "FLAT_NO_TRADE_CASH_RETURN"
    return {
        "sample_id": f"{replay_id}:sample:{replay_index:04d}",
        "sample_index": replay_index,
        "event_time_utc": window_candles[-1].get("timestamp"),
        "runtime_cycle_id": runtime["cycle_id"],
        "runtime_cycle_hash": runtime["cycle_hash"],
        "symbol": candidate.get("symbol"),
        "strategy_family": candidate.get("strategy_family"),
        "strategy_id": strategy_id,
        "candidate_id": candidate.get("candidate_id"),
        "decision": candidate.get("decision"),
        "executed_trade": executed_trade,
        "replay_return_basis": replay_return_basis,
        "regime": candidate.get("regime") or runtime.get("regime"),
        "strategy_policy_reason": candidate.get("strategy_policy_reason"),
        "no_trade_reason": candidate.get("no_trade_reason"),
        "net_ev_after_cost_bps": net_ev_after_cost,
        "gross_expected_edge_bps": gross_expected_edge,
        "total_execution_cost_bps": total_execution_cost,
        "opportunity_net_ev_after_cost_bps": opportunity_net_ev,
        "opportunity_gross_expected_edge_bps": opportunity_gross_edge,
        "opportunity_total_execution_cost_bps": opportunity_cost,
    }


def _safe_artifact_stem(value: Any) -> str:
    text = str(value or "unknown")
    safe = "".join(character if character.isalnum() or character in "-_." else "_" for character in text).strip("._")
    if not safe:
        safe = "unknown"
    if len(safe) > 96:
        safe = f"{safe[:80]}-{hashlib.sha256(text.encode('utf-8')).hexdigest().upper()[:16]}"
    return safe


def build_public_replay_robustness_report(
    *,
    candidate_scorecard: dict[str, Any],
    market_data: dict[str, Any],
    replay_id: str | None = None,
    window_size: int = PUBLIC_REPLAY_DEFAULT_WINDOW_SIZE,
    max_replay_windows: int = PUBLIC_REPLAY_DEFAULT_MAX_WINDOWS,
    min_required_sample_count: int = 300,
) -> dict[str, Any]:
    symbol = str(candidate_scorecard.get("symbol") or "")
    session_id = str(candidate_scorecard.get("session_id") or "mvp1_upbit_paper_launcher")
    safe_window_size = max(PUBLIC_REPLAY_MIN_WINDOW_SIZE, int(window_size))
    safe_max_windows = max(1, min(int(max_replay_windows), 1000))
    replay_id = replay_id or f"public-replay:{candidate_scorecard.get('source_runtime_cycle_id')}:{candidate_scorecard.get('candidate_id')}"
    data_status, data_blocker, data_message = validate_upbit_public_candle_data(
        market_data,
        symbol=symbol,
        session_id=session_id,
    )
    blockers: list[dict[str, str]] = []
    sample_rows: list[dict[str, Any]] = []
    source_hash = sha256_json(market_data)

    if data_status != "PASS":
        blockers.append(_blocker(data_blocker or "DATA_UNAVAILABLE", data_message))
    else:
        candles = [candle for candle in market_data.get("candles") or [] if isinstance(candle, dict)]
        if len(candles) < safe_window_size:
            blockers.append(_blocker("MEASUREMENT_MISSING", "public replay requires enough candle history for windowed evaluation"))
        window_count = max(0, len(candles) - safe_window_size + 1)
        start_index = max(0, window_count - safe_max_windows)
        for replay_index, candle_index in enumerate(range(start_index, window_count), start=1):
            window_candles = candles[candle_index : candle_index + safe_window_size]
            window_market_data = dict(market_data)
            window_market_data["candles"] = window_candles
            window_market_data["profile"] = "PUBLIC_REST_REPLAY_WINDOW"
            cycle_id = f"public-replay-{_safe_artifact_stem(symbol)}-{candle_index + 1:04d}"
            runtime = build_upbit_paper_runtime_cycle_report(
                cycle_id=cycle_id,
                session_id=session_id,
                symbol=symbol,
                market_data=window_market_data,
            )
            candidate = _candidate_by_id(runtime, str(candidate_scorecard.get("candidate_id") or ""))
            if not isinstance(candidate, dict):
                continue
            if any(candidate.get(flag) is True for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
                blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "public replay candidate attempted live or scale-up permission"))
                continue
            sample_rows.append(
                _public_replay_sample_row(
                    replay_id=replay_id,
                    replay_index=replay_index,
                    window_candles=window_candles,
                    runtime=runtime,
                    candidate=candidate,
                    strategy_id=candidate_scorecard.get("strategy_id"),
                )
            )

    sample_count = len(sample_rows)
    if sample_count < int(min_required_sample_count):
        blockers.append(
            _blocker(
                "SAMPLE_INSUFFICIENT",
                f"{sample_count} public replay robustness samples collected; {int(min_required_sample_count)} required",
            )
        )
    status = "PASS" if not blockers else "BLOCKED"
    report = {
        "schema_id": PUBLIC_REPLAY_ROBUSTNESS_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "replay_id": replay_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "REPLAY",
        "session_id": session_id,
        "symbol": symbol,
        "candidate_id": candidate_scorecard.get("candidate_id"),
        "strategy_id": candidate_scorecard.get("strategy_id"),
        "strategy_build_id": candidate_scorecard.get("strategy_build_id"),
        "parameter_hash": candidate_scorecard.get("parameter_hash"),
        "value_source": PUBLIC_REPLAY_VALUE_SOURCE,
        "public_market_data_source": market_data.get("source"),
        "public_market_data_hash": source_hash,
        "window_size": safe_window_size,
        "sample_count": sample_count,
        "min_required_sample_count": int(min_required_sample_count),
        "max_replay_windows": safe_max_windows,
        "sample_rows": sample_rows,
        "replay_status": status,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = public_replay_robustness_report_hash(report)
    return report


def build_public_replay_fetch_failure_report(
    *,
    candidate_scorecard: dict[str, Any],
    replay_id: str,
    error_type: str,
    error_message: str,
    target_count: int,
    page_size: int,
    timeout_seconds: float,
    window_size: int = PUBLIC_REPLAY_DEFAULT_WINDOW_SIZE,
    max_replay_windows: int = PUBLIC_REPLAY_DEFAULT_MAX_WINDOWS,
    min_required_sample_count: int = 300,
) -> dict[str, Any]:
    symbol = str(candidate_scorecard.get("symbol") or "")
    session_id = str(candidate_scorecard.get("session_id") or "mvp1_upbit_paper_launcher")
    safe_window_size = max(PUBLIC_REPLAY_MIN_WINDOW_SIZE, int(window_size))
    safe_max_windows = max(1, min(int(max_replay_windows), 1000))
    failure_source = {
        "source": PUBLIC_REPLAY_FETCH_FAILED_SOURCE,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "REPLAY",
        "session_id": session_id,
        "symbol": symbol,
        "target_count": max(0, int(target_count)),
        "page_size": max(0, int(page_size)),
        "timeout_seconds": max(0.0, float(timeout_seconds)),
        "error_type": str(error_type or "Exception")[:96],
        "error_message": str(error_message or "")[:240],
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
    }
    report = {
        "schema_id": PUBLIC_REPLAY_ROBUSTNESS_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "replay_id": replay_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "REPLAY",
        "session_id": session_id,
        "symbol": symbol,
        "candidate_id": candidate_scorecard.get("candidate_id"),
        "strategy_id": candidate_scorecard.get("strategy_id"),
        "strategy_build_id": candidate_scorecard.get("strategy_build_id"),
        "parameter_hash": candidate_scorecard.get("parameter_hash"),
        "value_source": PUBLIC_REPLAY_VALUE_SOURCE,
        "public_market_data_source": PUBLIC_REPLAY_FETCH_FAILED_SOURCE,
        "public_market_data_hash": sha256_json(failure_source),
        "public_market_data_fetch_status": "FAILED",
        "public_market_data_error_type": failure_source["error_type"],
        "public_market_data_error_message": failure_source["error_message"],
        "window_size": safe_window_size,
        "sample_count": 0,
        "min_required_sample_count": int(min_required_sample_count),
        "max_replay_windows": safe_max_windows,
        "sample_rows": [],
        "replay_status": "BLOCKED",
        "primary_blocker_code": "DATA_QUALITY_INSUFFICIENT",
        "blockers": [
            _blocker(
                "DATA_QUALITY_INSUFFICIENT",
                "public replay could not collect read-only public candles; candidate review remains blocked",
            )
        ],
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = public_replay_robustness_report_hash(report)
    return report


def validate_public_replay_robustness_report(
    report: dict[str, Any],
    *,
    candidate_scorecard: dict[str, Any] | None = None,
) -> ReplayConsistencyValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "replay_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "candidate_id",
        "strategy_id",
        "strategy_build_id",
        "parameter_hash",
        "value_source",
        "public_market_data_source",
        "public_market_data_hash",
        "window_size",
        "sample_count",
        "min_required_sample_count",
        "max_replay_windows",
        "sample_rows",
        "replay_status",
        "primary_blocker_code",
        "blockers",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ReplayConsistencyValidationResult("FAIL", f"public replay report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != PUBLIC_REPLAY_ROBUSTNESS_SCHEMA_ID:
        return ReplayConsistencyValidationResult("FAIL", "public replay schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("report_hash") != public_replay_robustness_report_hash(report):
        return ReplayConsistencyValidationResult("FAIL", "public replay report hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "REPLAY":
        return ReplayConsistencyValidationResult("BLOCKED", "public replay scope must remain UPBIT/KRW_SPOT/REPLAY", "SNAPSHOT_SCOPE_MISMATCH")
    forbidden = (
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
    if any(report.get(field) for field in forbidden):
        return ReplayConsistencyValidationResult("BLOCKED", "public replay attempted private, order, live, or scale-up behavior", "LIVE_FINAL_GUARD_FAILED")
    if report.get("value_source") not in {PUBLIC_REPLAY_VALUE_SOURCE, PUBLIC_REPLAY_LEGACY_VALUE_SOURCE}:
        return ReplayConsistencyValidationResult("FAIL", "public replay value source mismatch", "SCHEMA_IDENTITY_MISMATCH")
    allowed_market_sources = {"STATIC_FIXTURE", "PUBLIC_REST_READ_ONLY", PUBLIC_REPLAY_FETCH_FAILED_SOURCE}
    if report.get("public_market_data_source") not in allowed_market_sources:
        return ReplayConsistencyValidationResult("FAIL", "public replay public market data source mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("public_market_data_source") == PUBLIC_REPLAY_FETCH_FAILED_SOURCE:
        if report.get("replay_status") != "BLOCKED" or report.get("primary_blocker_code") != "DATA_QUALITY_INSUFFICIENT":
            return ReplayConsistencyValidationResult("FAIL", "failed public replay fetch must stay DATA_QUALITY_INSUFFICIENT/BLOCKED", "SCHEMA_IDENTITY_MISMATCH")
        if int(report.get("sample_count") or 0) != 0 or report.get("sample_rows"):
            return ReplayConsistencyValidationResult("FAIL", "failed public replay fetch cannot carry sample rows", "SCHEMA_IDENTITY_MISMATCH")
    strict_decision_adjusted_rows = report.get("value_source") == PUBLIC_REPLAY_VALUE_SOURCE
    sample_rows = report.get("sample_rows")
    if not isinstance(sample_rows, list) or int(report.get("sample_count") or 0) != len(sample_rows):
        return ReplayConsistencyValidationResult("FAIL", "public replay sample count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    for row in sample_rows:
        if not isinstance(row, dict):
            return ReplayConsistencyValidationResult("FAIL", "public replay sample row must be an object", "SCHEMA_IDENTITY_MISMATCH")
        decision = row.get("decision")
        if decision == "NO_TRADE":
            row_uses_decision_adjusted_fields = (
                strict_decision_adjusted_rows
                or "executed_trade" in row
                or "replay_return_basis" in row
                or "opportunity_net_ev_after_cost_bps" in row
            )
            if not row_uses_decision_adjusted_fields:
                continue
            if row.get("executed_trade") is not False:
                return ReplayConsistencyValidationResult("FAIL", "NO_TRADE replay row cannot be executed", "SCHEMA_IDENTITY_MISMATCH")
            if _number(row.get("net_ev_after_cost_bps")) != 0.0:
                return ReplayConsistencyValidationResult("FAIL", "NO_TRADE replay row must use flat-cash zero return", "SCHEMA_IDENTITY_MISMATCH")
            if _number(row.get("total_execution_cost_bps")) != 0.0:
                return ReplayConsistencyValidationResult("FAIL", "NO_TRADE replay row cannot carry execution cost", "SCHEMA_IDENTITY_MISMATCH")
        elif decision == "PAPER_ENTRY_REVIEW":
            if strict_decision_adjusted_rows and row.get("executed_trade") is not True:
                return ReplayConsistencyValidationResult("FAIL", "entry replay row must be marked executed", "SCHEMA_IDENTITY_MISMATCH")
            if row.get("executed_trade") is False:
                return ReplayConsistencyValidationResult("FAIL", "entry replay row must be marked executed", "SCHEMA_IDENTITY_MISMATCH")
        else:
            return ReplayConsistencyValidationResult("FAIL", "public replay decision is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("replay_status") == "PASS" and report.get("blockers"):
        return ReplayConsistencyValidationResult("BLOCKED", "public replay PASS cannot carry blockers", report["blockers"][0].get("code", "UNKNOWN_BLOCKED"))
    if candidate_scorecard is not None:
        for field in ("candidate_id", "strategy_id", "strategy_build_id", "parameter_hash", "session_id", "symbol"):
            if str(report.get(field) or "") != str(candidate_scorecard.get(field) or ""):
                return ReplayConsistencyValidationResult("BLOCKED", f"public replay candidate scope mismatch: {field}", "SNAPSHOT_SCOPE_MISMATCH")
    return ReplayConsistencyValidationResult("PASS", "public replay robustness report is scoped, hash-bound, and live-blocked", None)


def public_replay_robustness_values_from_report(
    report: dict[str, Any],
    *,
    candidate_scorecard: dict[str, Any],
) -> tuple[list[float], list[dict[str, Any]], list[str]]:
    result = validate_public_replay_robustness_report(report, candidate_scorecard=candidate_scorecard)
    if result.status != "PASS":
        return [], [], []
    values: list[float] = []
    samples: list[dict[str, Any]] = []
    for row in report.get("sample_rows") or []:
        if not isinstance(row, dict) or row.get("candidate_id") != report.get("candidate_id"):
            continue
        if row.get("decision") == "NO_TRADE":
            values.append(0.0)
        else:
            values.append(_number(row.get("net_ev_after_cost_bps")))
        samples.append(
            {
                "loop_id": report["replay_id"],
                "source_loop_report_hash": report["report_hash"],
                "source_runtime_cycle_hash": row.get("runtime_cycle_hash"),
                "source_runtime_cycle_id": row.get("runtime_cycle_id"),
            }
        )
    source_ids = [
        f"public_replay_robustness:{report['replay_id']}:{report['report_hash']}",
        f"public_market_data:{report['symbol']}:{report['public_market_data_hash']}",
    ]
    return values, samples, source_ids


def public_replay_robustness_report_path(*, root: Path = ROOT, report: dict[str, Any]) -> Path:
    return (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(report["session_id"])
        / "profitability"
        / "replay_robustness"
        / f"{_safe_artifact_stem(report.get('candidate_id'))}.public_replay_robustness_report.json"
    )


def write_public_replay_robustness_report(*, root: Path = ROOT, report: dict[str, Any]) -> Path:
    path = public_replay_robustness_report_path(root=root, report=report)
    durable_atomic_write_json(path, report)
    return path


def load_public_replay_robustness_report(
    *,
    root: Path = ROOT,
    session_id: str,
    candidate_id: str,
) -> dict[str, Any] | None:
    path = (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(session_id)
        / "profitability"
        / "replay_robustness"
        / f"{_safe_artifact_stem(candidate_id)}.public_replay_robustness_report.json"
    )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


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
