from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_runtime import validate_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


ROOT = Path(__file__).resolve().parents[3]
SCORECARD_SCHEMA_ID = "trader1.candidate_scorecard.v1"
COST_FIELD_MAP = {
    "expected_fee_bps": "fee_bps",
    "expected_spread_bps": "spread_bps",
    "expected_slippage_bps": "slippage_bps",
    "expected_impact_bps": "market_impact_bps",
    "expected_latency_penalty_bps": "latency_bps",
}
ROBUSTNESS_PASS = {
    "oos_status": "PASS",
    "walk_forward_status": "PASS",
    "bootstrap_status": "PASS",
    "overfit_status": "LOW",
}
ROBUSTNESS_SOURCE_PREFIXES = ("oos:", "walk_forward:", "bootstrap:")
RUNTIME_CYCLE_SOURCE_PREFIX = "upbit_paper_runtime_cycle:"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def current_authority_hashes() -> dict[str, str]:
    return {
        "trader1_sha256": sha256_file(ROOT / "TRADER_1.md"),
        "agents_sha256": sha256_file(ROOT / "AGENTS.md"),
    }


def decimal_value(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def number_value(value: Any) -> float:
    return float(decimal_value(value))


def blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def runtime_cycle_source_evidence_id(cycle_id: str, cycle_hash: str) -> str:
    return f"{RUNTIME_CYCLE_SOURCE_PREFIX}{cycle_id}:{cycle_hash}"


def robustness_source_evidence_id(prefix: str, cycle_id: str, cycle_hash: str) -> str:
    normalized = prefix[:-1] if prefix.endswith(":") else prefix
    return f"{normalized}:{cycle_id}:{cycle_hash}"


def runtime_cycle_binding_from_source_ids(source_evidence_ids: list[str] | None) -> tuple[str, str] | None:
    for source_id in source_evidence_ids or []:
        if not isinstance(source_id, str) or not source_id.startswith(RUNTIME_CYCLE_SOURCE_PREFIX):
            continue
        parts = source_id.split(":")
        if len(parts) == 3 and parts[1] and len(parts[2]) == 64:
            return parts[1], parts[2]
    return None


def has_required_robustness_source_ids(
    source_evidence_ids: list[str] | None,
    *,
    cycle_id: str | None = None,
    cycle_hash: str | None = None,
) -> bool:
    ids = source_evidence_ids or []
    if cycle_id and cycle_hash:
        required = {
            robustness_source_evidence_id(prefix, cycle_id, cycle_hash)
            for prefix in ROBUSTNESS_SOURCE_PREFIXES
        }
        return required.issubset(set(ids))
    return all(any(source_id.startswith(prefix) for source_id in ids) for prefix in ROBUSTNESS_SOURCE_PREFIXES)


def strategy_id_for_family(strategy_family: str) -> str:
    mapping = {
        "PULLBACK_TREND_LONG": "trend_pullback",
        "BREAKOUT_RETEST_LONG": "breakout_retest",
        "VWAP_MEAN_REVERSION": "vwap_mean_reversion",
    }
    return mapping.get(strategy_family, strategy_family.lower())


def regime_scope_for_runtime_regime(regime: str) -> str:
    mapping = {
        "UPTREND": "TRENDING",
        "RANGE": "RANGE",
        "RISK_OFF": "RISK_OFF",
    }
    return mapping.get(regime, "RISK_OFF")


def _candidate_scorecard_rank_key(candidate: dict[str, Any]) -> tuple[Decimal, Decimal, int, str]:
    return (
        decimal_value(candidate.get("candidate_selection_score")),
        decimal_value(candidate.get("net_ev_after_cost_bps")),
        -int(candidate.get("selection_priority", 999)),
        str(candidate.get("candidate_id") or ""),
    )


def _scorecard_candidate_from_runtime(runtime_cycle_report: dict[str, Any]) -> dict[str, Any]:
    selected = runtime_cycle_report["selected_candidate"]
    if selected.get("decision") == "PAPER_ENTRY_REVIEW":
        return selected

    entry_candidates = [
        candidate
        for candidate in runtime_cycle_report.get("strategy_candidates") or []
        if isinstance(candidate, dict)
        and candidate.get("decision") == "PAPER_ENTRY_REVIEW"
        and isinstance(candidate.get("candidate_id"), str)
        and candidate.get("live_order_ready") is False
        and candidate.get("live_order_allowed") is False
        and candidate.get("can_live_trade") is False
        and candidate.get("scale_up_allowed") is False
    ]
    if not entry_candidates:
        return selected
    return max(entry_candidates, key=_candidate_scorecard_rank_key)


def candidate_scorecard_from_upbit_paper_runtime_cycle(
    runtime_cycle_report: dict[str, Any],
    *,
    authority: dict[str, str] | None = None,
    scorecard_id: str | None = None,
    min_required_edge_bps: float = 10.0,
    robustness_statuses: dict[str, str] | None = None,
    robustness_source_evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    runtime_result = validate_upbit_paper_runtime_cycle_report(runtime_cycle_report)
    if runtime_result.status != "PASS":
        raise ValueError(f"runtime cycle is not valid for scorecard input: {runtime_result.status}:{runtime_result.blocker_code}")

    selected = _scorecard_candidate_from_runtime(runtime_cycle_report)
    selected_symbol = str(selected.get("symbol") or runtime_cycle_report["symbol"])
    cost_breakdown = selected["cost_breakdown_bps"]
    robustness = {
        "oos_status": "UNTESTED",
        "walk_forward_status": "UNTESTED",
        "bootstrap_status": "UNTESTED",
        "overfit_status": "UNTESTED",
    }
    if robustness_statuses:
        robustness.update(robustness_statuses)

    net_ev = number_value(selected["net_ev_after_cost_bps"])
    robustness_ready = all(robustness[field] == expected for field, expected in ROBUSTNESS_PASS.items())
    source_runtime_cycle_id = str(runtime_cycle_report["cycle_id"])
    source_runtime_cycle_hash = str(runtime_cycle_report["cycle_hash"])
    source_ids = [runtime_cycle_source_evidence_id(source_runtime_cycle_id, source_runtime_cycle_hash)]
    source_ids.extend(robustness_source_evidence_ids or [])
    enough_robustness_sources = has_required_robustness_source_ids(
        source_ids,
        cycle_id=source_runtime_cycle_id,
        cycle_hash=source_runtime_cycle_hash,
    )
    ranking_eligible = (
        selected.get("decision") == "PAPER_ENTRY_REVIEW"
        and net_ev >= min_required_edge_bps
        and robustness_ready
        and enough_robustness_sources
    )

    blockers: list[dict[str, str]] = []
    if selected.get("decision") != "PAPER_ENTRY_REVIEW":
        blockers.append(blocker(str(selected.get("no_trade_reason") or "MIN_EDGE_FAIL"), "selected PAPER candidate is not entry-review eligible"))
    if net_ev < min_required_edge_bps:
        blockers.append(blocker("MIN_EDGE_FAIL", "net EV after cost is below PAPER scorecard minimum"))
    if not robustness_ready:
        if robustness["oos_status"] != "PASS":
            blockers.append(blocker("OOS_MISSING", "OOS evidence is required before PAPER scorecard ranking"))
        if robustness["walk_forward_status"] != "PASS":
            blockers.append(blocker("WALK_FORWARD_MISSING", "walk-forward evidence is required before PAPER scorecard ranking"))
        if robustness["bootstrap_status"] != "PASS":
            blockers.append(blocker("BOOTSTRAP_UNSTABLE", "bootstrap robustness evidence is required before PAPER scorecard ranking"))
        if robustness["overfit_status"] != "LOW":
            blockers.append(blocker("OVERFIT_RISK_HIGH", "overfit risk must be LOW before PAPER scorecard ranking"))
    if robustness_ready and not enough_robustness_sources:
        blockers.append(
            blocker(
                "SCORECARD_MISSING",
                "OOS, walk-forward, and bootstrap source evidence ids are required before PAPER scorecard ranking",
            )
        )

    if ranking_eligible:
        blockers = []

    return {
        "schema_id": SCORECARD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority or current_authority_hashes(),
        "scorecard_id": scorecard_id or f"scorecard:{runtime_cycle_report['cycle_id']}:{selected['candidate_id']}",
        "candidate_id": selected["candidate_id"],
        "source_runtime_cycle_id": source_runtime_cycle_id,
        "source_runtime_cycle_hash": source_runtime_cycle_hash,
        "strategy_id": strategy_id_for_family(selected["strategy_family"]),
        "strategy_build_id": "upbit_paper_runtime_cycle_v1",
        "parameter_hash": stable_hash(f"{selected['candidate_id']}:{selected['strategy_family']}:{selected_symbol}"),
        "exchange": runtime_cycle_report["exchange"],
        "market_type": runtime_cycle_report["market_type"],
        "mode": runtime_cycle_report["mode"],
        "session_id": runtime_cycle_report["session_id"],
        "symbol": selected_symbol,
        "timeframe_scope": "runtime_cycle_fixture_or_public_collection",
        "regime_scope": regime_scope_for_runtime_regime(str(selected.get("regime") or runtime_cycle_report.get("regime"))),
        "objective_basis": "NET_EV_AFTER_COST",
        "gross_expected_edge_bps": number_value(selected["expected_edge_bps"]),
        "expected_fee_bps": number_value(cost_breakdown[COST_FIELD_MAP["expected_fee_bps"]]),
        "expected_spread_bps": number_value(cost_breakdown[COST_FIELD_MAP["expected_spread_bps"]]),
        "expected_slippage_bps": number_value(cost_breakdown[COST_FIELD_MAP["expected_slippage_bps"]]),
        "expected_impact_bps": number_value(cost_breakdown[COST_FIELD_MAP["expected_impact_bps"]]),
        "expected_latency_penalty_bps": number_value(cost_breakdown[COST_FIELD_MAP["expected_latency_penalty_bps"]]),
        "net_ev_after_cost_bps": net_ev,
        "min_required_edge_bps": float(min_required_edge_bps),
        "cost_model_status": "VALIDATED",
        "oos_status": robustness["oos_status"],
        "walk_forward_status": robustness["walk_forward_status"],
        "bootstrap_status": robustness["bootstrap_status"],
        "overfit_status": robustness["overfit_status"],
        "ranking_eligible": ranking_eligible,
        "scorecard_scope": "PAPER_SCORECARD_INPUT_ONLY" if ranking_eligible else "PAPER_EVIDENCE_COLLECTION_ONLY",
        "live_readiness_status": "NOT_LIVE_READY",
        "operator_warning": "PAPER candidate scorecard is not LIVE_READY and live orders remain blocked.",
        "source_evidence_ids": source_ids,
        "blockers": blockers,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "notes": "Generated from Upbit PAPER runtime cycle. It is PAPER scorecard evidence only and cannot create live permission.",
    }


def write_upbit_paper_candidate_scorecard(*, root: Path, scorecard: dict[str, Any]) -> Path:
    if (
        scorecard.get("exchange") != "UPBIT"
        or scorecard.get("market_type") != "KRW_SPOT"
        or scorecard.get("mode") != "PAPER"
    ):
        raise ValueError("candidate scorecard writer is scoped to UPBIT/KRW_SPOT/PAPER")
    forbidden_flags = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
    if any(scorecard.get(flag) is True for flag in forbidden_flags):
        raise ValueError("candidate scorecard writer refuses live or scale-up permission")
    path = (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(scorecard["session_id"])
        / "profitability"
        / "candidate_scorecard.json"
    )
    durable_atomic_write_json(path, scorecard)
    return path
