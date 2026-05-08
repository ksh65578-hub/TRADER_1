from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.research.profitability.candidate_scorecard import (
    safe_candidate_scorecard_filename,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


ROOT = Path(__file__).resolve().parents[3]
STRATEGY_PERFORMANCE_MEMORY_SCHEMA_ID = "trader1.strategy_performance_memory.v1"
OPTIMIZER_MEMORY_STATE_SCHEMA_ID = "trader1.optimizer_memory_state.v1"
FAILURE_ANALYSIS_SCHEMA_ID = "trader1.failure_analysis_report.v1"

ROOT_CAUSE_BY_BLOCKER = {
    "MIN_EDGE_FAIL": "STRATEGY_RULE_GAP",
    "FEE_EXCEEDS_EDGE": "FEE_MODEL_MISMATCH",
    "FEE_MODEL_UNVERIFIED": "FEE_MODEL_MISMATCH",
    "COST_AFTER_EDGE_UNVERIFIED": "FEE_MODEL_MISMATCH",
    "DRAWDOWN_FREEZE_ACTIVE": "RISK_EXPOSURE_BREACH",
    "RISK_VETO": "RISK_EXPOSURE_BREACH",
    "REGIME_MISMATCH": "REGIME_MISMATCH",
    "OVERFIT_RISK_HIGH": "OVERFIT_RISK_HIGH",
    "BOOTSTRAP_UNSTABLE": "OVERFIT_RISK_HIGH",
    "OOS_MISSING": "OVERFIT_RISK_HIGH",
    "WALK_FORWARD_MISSING": "OVERFIT_RISK_HIGH",
    "DEPTH_TOO_THIN": "LIQUIDITY_DEPTH_THIN",
    "EXECUTION_FEEDBACK_DIVERGENT": "EXECUTION_FEEDBACK_DIVERGENT",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def current_authority_hashes() -> dict[str, str]:
    return {
        "trader1_sha256": sha256_file(ROOT / "TRADER_1.md"),
        "agents_sha256": sha256_file(ROOT / "AGENTS.md"),
    }


def blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def scorecard_artifact_id(scorecard: dict[str, Any]) -> str:
    return f"candidate_scorecard:{scorecard.get('scorecard_id')}:{sha256_json(scorecard)}"


def _bounded_float(value: Any, default: float = 0.0, lower: float | None = None, upper: float | None = None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = default
    if lower is not None:
        result = max(lower, result)
    if upper is not None:
        result = min(upper, result)
    return result


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _reason_counts_from_blockers(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not blockers:
        return [{"reason_code": "NO_BLOCKER_RECORDED", "count": 0}]
    counts: dict[str, int] = {}
    for item in blockers:
        code = str(item.get("code") or "UNKNOWN_BLOCKED")
        counts[code] = counts.get(code, 0) + 1
    return [{"reason_code": code, "count": count} for code, count in sorted(counts.items())]


def _source_modes(scorecard: dict[str, Any], extra_source_modes: list[str] | None) -> list[str]:
    modes = {str(scorecard.get("mode") or "PAPER")}
    for mode in extra_source_modes or []:
        modes.add(str(mode))
    modes.discard("LIVE")
    return sorted(modes)


def _performance_scope(source_modes: list[str]) -> str:
    if {"PAPER", "SHADOW"}.issubset(set(source_modes)):
        return "PAPER_SHADOW_RESEARCH_ONLY"
    if source_modes == ["READ_ONLY"]:
        return "READ_ONLY_ANALYSIS_ONLY"
    if source_modes == ["REPLAY"]:
        return "REPLAY_RESEARCH_ONLY"
    return "PAPER_RUNTIME_SCORECARD_ONLY"


def _strategy_memory_blockers(scorecard: dict[str, Any], source_modes: list[str]) -> list[dict[str, str]]:
    blockers = [blocker(str(item["code"]), str(item["message"]), str(item.get("severity") or "HIGH")) for item in scorecard.get("blockers", [])]
    if "SHADOW" not in set(source_modes):
        blockers.append(
            blocker(
                "MEASUREMENT_MISSING",
                "Strategy performance memory is bound to PAPER scorecard evidence only; SHADOW evidence is still required.",
                "MEDIUM",
            )
        )
    return blockers


def _strategy_performance_status(scorecard: dict[str, Any], blockers: list[dict[str, str]]) -> str:
    hard_blockers = {
        "MIN_EDGE_FAIL",
        "FEE_EXCEEDS_EDGE",
        "COST_AFTER_EDGE_UNVERIFIED",
        "DRAWDOWN_FREEZE_ACTIVE",
        "EXECUTION_FEEDBACK_DIVERGENT",
        "OVERFIT_RISK_HIGH",
        "REGIME_MISMATCH",
        "RISK_VETO",
    }
    blocker_codes = {item["code"] for item in blockers}
    sample_count = _int_value(scorecard.get("closed_trade_sample_count"))
    min_samples = _int_value(scorecard.get("min_closed_trade_sample_count"), 1)
    net_ev = _bounded_float(scorecard.get("net_ev_after_cost_bps"))
    if blocker_codes & hard_blockers or net_ev <= 0:
        return "BLOCKED"
    if sample_count >= min_samples and scorecard.get("performance_ready") is True and scorecard.get("ranking_eligible") is True:
        return "IMPROVING_AFTER_COST" if not blockers else "COLLECTING"
    return "COLLECTING"


def strategy_performance_memory_from_scorecard(
    scorecard: dict[str, Any],
    *,
    authority: dict[str, str] | None = None,
    extra_source_modes: list[str] | None = None,
    extra_source_artifact_ids: list[str] | None = None,
) -> dict[str, Any]:
    source_modes = _source_modes(scorecard, extra_source_modes)
    blockers = _strategy_memory_blockers(scorecard, source_modes)
    performance_status = _strategy_performance_status(scorecard, blockers)
    trade_count = _int_value(scorecard.get("closed_trade_sample_count"))
    no_trade_count = max(1 if blockers else 0, len(blockers))
    sample_count = trade_count + no_trade_count
    fee_cost = _bounded_float(scorecard.get("expected_fee_bps"), lower=0.0)
    spread_cost = _bounded_float(scorecard.get("expected_spread_bps"), lower=0.0)
    slippage_cost = _bounded_float(scorecard.get("expected_slippage_bps"), lower=0.0)
    impact_cost = _bounded_float(scorecard.get("expected_impact_bps"), lower=0.0)
    gross_pnl = _bounded_float(scorecard.get("gross_expected_edge_bps"))
    net_ev = min(_bounded_float(scorecard.get("net_ev_after_cost_bps")), gross_pnl - fee_cost - spread_cost - slippage_cost - impact_cost)
    regime_scope = str(scorecard.get("regime_scope") or "RISK_OFF")
    allowed_regime = "UPTREND" if regime_scope == "TRENDING" else "RANGE" if regime_scope == "RANGE" else None
    profit_factor = _bounded_float(scorecard.get("profit_factor"), lower=0.0)
    win_rate = profit_factor / (profit_factor + 1.0) if profit_factor > 0 else 0.0
    source_ids = [scorecard_artifact_id(scorecard), *[str(item) for item in scorecard.get("source_evidence_ids", [])]]
    source_ids.extend(str(item) for item in extra_source_artifact_ids or [])

    return {
        "schema_id": STRATEGY_PERFORMANCE_MEMORY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority or current_authority_hashes(),
        "strategy_performance_memory_id": f"strategy_performance_memory:{scorecard.get('scorecard_id')}",
        "exchange": scorecard["exchange"],
        "market_type": scorecard["market_type"],
        "mode": scorecard["mode"],
        "session_id": scorecard["session_id"],
        "strategy_id": scorecard["strategy_id"],
        "strategy_build_id": scorecard["strategy_build_id"],
        "parameter_hash": scorecard["parameter_hash"],
        "timeframe_scope": scorecard["timeframe_scope"],
        "regime_scope": "UPTREND_RANGE_DOWNTREND_RISK_OFF",
        "performance_scope": _performance_scope(source_modes),
        "performance_status": performance_status,
        "source_modes": source_modes,
        "source_artifact_ids": sorted(set(source_ids)),
        "sample_count": sample_count,
        "min_required_sample_count": _int_value(scorecard.get("min_closed_trade_sample_count"), 1),
        "trade_count": trade_count,
        "no_trade_count": no_trade_count,
        "entry_reason_counts": [{"reason_code": "SCORECARD_ENTRY_EVIDENCE", "count": trade_count}],
        "exit_reason_counts": [{"reason_code": "SCORECARD_CLOSED_TRADE_EVIDENCE", "count": trade_count}],
        "no_trade_reason_counts": _reason_counts_from_blockers(blockers),
        "gross_pnl": gross_pnl,
        "fee_cost": fee_cost,
        "spread_cost": spread_cost,
        "slippage_cost": slippage_cost,
        "market_impact_cost": impact_cost,
        "net_ev_after_cost": net_ev,
        "max_drawdown_pct": _bounded_float(scorecard.get("max_drawdown_pct"), lower=0.0, upper=100.0),
        "win_rate": _bounded_float(win_rate, lower=0.0, upper=1.0),
        "profit_factor": profit_factor,
        "regime_performance": [
            {
                "regime": regime,
                "sample_count": sample_count if regime == allowed_regime else 0,
                "trade_count": trade_count if regime == allowed_regime else 0,
                "no_trade_count": no_trade_count if regime != allowed_regime else 0,
                "net_ev_after_cost": net_ev if regime == allowed_regime else 0.0,
                "max_drawdown_pct": _bounded_float(scorecard.get("max_drawdown_pct"), lower=0.0, upper=100.0) if regime == allowed_regime else 0.0,
                "trade_allowed": regime in {"UPTREND", "RANGE"} and regime == allowed_regime,
                "primary_blocker_code": None if regime == allowed_regime else ("RISK_VETO" if regime == "RISK_OFF" else "REGIME_MISMATCH"),
            }
            for regime in ("UPTREND", "RANGE", "DOWNTREND", "RISK_OFF")
        ],
        "downtrend_avoidance_enforced": True,
        "risk_off_no_trade_enforced": True,
        "cost_model_included": True,
        "slippage_fee_impact_included": True,
        "paper_shadow_separated": "SHADOW" in set(source_modes),
        "exchange_market_type_scoped": True,
        "dashboard_display_truth_only": True,
        "operator_warning": "Strategy performance memory is not LIVE_READY and live orders remain blocked.",
        "blockers": blockers,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "live_permission_created": False,
        "live_config_mutation_allowed": False,
        "writes_live_ready_snapshot": False,
        "active_snapshot_mutation_allowed": False,
        "optimizer_winner_live_config_allowed": False,
        "paper_winner_live_config_allowed": False,
        "order_submission_allowed": False,
        "exchange_account_call_allowed": False,
        "scale_up_from_performance_allowed": False,
    }


def _root_cause_from_scorecard(scorecard: dict[str, Any]) -> str:
    for item in scorecard.get("blockers", []):
        code = str(item.get("code") or "")
        if code in ROOT_CAUSE_BY_BLOCKER:
            return ROOT_CAUSE_BY_BLOCKER[code]
    if scorecard.get("performance_source_binding_status") != "PASS":
        return "UNKNOWN_ROOT_CAUSE"
    if scorecard.get("ranking_eligible") is not True:
        return "UNKNOWN_ROOT_CAUSE"
    return "UNKNOWN_ROOT_CAUSE"


def failure_analysis_from_scorecard(
    scorecard: dict[str, Any],
    *,
    authority: dict[str, str] | None = None,
    previous_failure_reports: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    if scorecard.get("ranking_eligible") is True and not scorecard.get("blockers"):
        return None
    previous = [
        item
        for item in previous_failure_reports or []
        if item.get("candidate_id") == scorecard.get("candidate_id")
    ]
    primary_root = _root_cause_from_scorecard(scorecard)
    same_root_previous = [item for item in previous if item.get("primary_root_cause_code") == primary_root]
    repeated_count = len(same_root_previous) + 1
    repeated_same_root = repeated_count >= 2
    root_status = "UNKNOWN" if primary_root == "UNKNOWN_ROOT_CAUSE" else "KNOWN"
    blocker_code = "ROOT_CAUSE_UNKNOWN_LIVE_AFFECTING" if primary_root == "UNKNOWN_ROOT_CAUSE" else str((scorecard.get("blockers") or [{"code": "FAILURE_ANALYSIS_MISSING"}])[0]["code"])
    report = {
        "schema_id": FAILURE_ANALYSIS_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority or current_authority_hashes(),
        "failure_analysis_id": f"failure_analysis:{scorecard.get('scorecard_id')}:{repeated_count}",
        "candidate_id": scorecard["candidate_id"],
        "strategy_id": scorecard["strategy_id"],
        "strategy_build_id": scorecard["strategy_build_id"],
        "parameter_hash": scorecard["parameter_hash"],
        "exchange": scorecard["exchange"],
        "market_type": scorecard["market_type"],
        "mode": scorecard["mode"],
        "session_id": scorecard["session_id"],
        "symbol": scorecard["symbol"],
        "timeframe_scope": scorecard["timeframe_scope"],
        "regime_scope": scorecard["regime_scope"],
        "failure_event_id": f"scorecard_failure:{scorecard.get('scorecard_id')}",
        "failure_status": "BLOCKED_UNKNOWN_ROOT_CAUSE" if root_status == "UNKNOWN" else "BLOCKED_REPEATED_FAILURE" if repeated_same_root else "ANALYZED",
        "primary_root_cause_code": primary_root,
        "secondary_root_cause_codes": [
            ROOT_CAUSE_BY_BLOCKER[str(item.get("code"))]
            for item in scorecard.get("blockers", [])
            if str(item.get("code")) in ROOT_CAUSE_BY_BLOCKER and ROOT_CAUSE_BY_BLOCKER[str(item.get("code"))] != primary_root
        ],
        "root_cause_status": root_status,
        "live_affecting": True,
        "repeated_failure_count": repeated_count,
        "repeated_failure_same_root_cause": repeated_same_root,
        "previous_failure_analysis_ids": [str(item.get("failure_analysis_id")) for item in same_root_previous],
        "recommended_response": "REQUIRE_MORE_EVIDENCE" if root_status == "UNKNOWN" else "RETIRE_CANDIDATE" if repeated_same_root else "PENALIZE_RANKING",
        "blocks_promotion": True,
        "blocks_live_order": True,
        "optimizer_ranking_action": "BLOCK_RANKING",
        "memory_write_required": True,
        "memory_write_status": "APPEND_ONLY_RECORDED",
        "source_evidence_ids": sorted(set([scorecard_artifact_id(scorecard), *[str(item) for item in scorecard.get("source_evidence_ids", [])]])),
        "dashboard_display_truth_only": True,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "blockers": [
            blocker(
                blocker_code,
                "Candidate scorecard cannot promote; failure analysis keeps ranking, live orders, and scale-up blocked.",
            )
        ],
        "audit_prev_hash": same_root_previous[-1].get("audit_hash") if same_root_previous else None,
        "audit_hash": "0" * 64,
        "notes": "Generated from non-live candidate scorecard evidence only.",
    }
    report["audit_hash"] = sha256_json({key: value for key, value in report.items() if key != "audit_hash"})
    return report


def optimizer_memory_state_from_scorecard(
    scorecard: dict[str, Any],
    *,
    authority: dict[str, str] | None = None,
    previous_memory_state: dict[str, Any] | None = None,
    failure_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    previous_records = list((previous_memory_state or {}).get("candidate_memory_records") or [])
    previous_count = sum(1 for item in previous_records if item.get("candidate_id") == scorecard.get("candidate_id"))
    blocked = scorecard.get("ranking_eligible") is not True or bool(scorecard.get("blockers"))
    primary_root = (failure_analysis or {}).get("primary_root_cause_code") or ("NONE" if not blocked else _root_cause_from_scorecard(scorecard))
    if scorecard.get("ranking_eligible") is True and not scorecard.get("blockers"):
        memory_status = "ACTIVE"
        outcome_status = "IMPROVED_AFTER_COST"
        failure_count = 0
        promotion_blocked = False
    else:
        memory_status = "BLOCKED" if primary_root == "UNKNOWN_ROOT_CAUSE" or blocked else "FAILED"
        outcome_status = "BLOCKED_BY_GUARDRAIL" if memory_status == "BLOCKED" else "FAILED_AFTER_COST"
        failure_count = previous_count + 1
        promotion_blocked = True
    audit_event_id = (failure_analysis or {}).get("failure_analysis_id") or f"scorecard_memory:{scorecard.get('scorecard_id')}"
    record = {
        "candidate_id": scorecard["candidate_id"],
        "strategy_id": scorecard["strategy_id"],
        "parameter_hash": scorecard["parameter_hash"],
        "source_mode": scorecard["mode"],
        "memory_record_status": memory_status,
        "last_outcome_status": outcome_status,
        "primary_root_cause_code": primary_root,
        "failure_count": failure_count,
        "promotion_blocked": promotion_blocked,
        "live_order_blocked": True,
        "audit_event_id": str(audit_event_id),
    }
    records = previous_records + [record]
    sequence = _int_value((previous_memory_state or {}).get("memory_sequence_number"), 0) + 1
    state = {
        "schema_id": OPTIMIZER_MEMORY_STATE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority or current_authority_hashes(),
        "optimizer_memory_state_id": f"optimizer_memory_state:{scorecard.get('scorecard_id')}:{sequence}",
        "exchange": scorecard["exchange"],
        "market_type": scorecard["market_type"],
        "mode": scorecard["mode"],
        "session_id": scorecard["session_id"],
        "strategy_id": scorecard["strategy_id"],
        "strategy_build_id": scorecard["strategy_build_id"],
        "parameter_hash": scorecard["parameter_hash"],
        "timeframe_scope": scorecard["timeframe_scope"],
        "regime_scope": scorecard["regime_scope"],
        "memory_scope": "CONVERGENCE_MEMORY_ONLY",
        "memory_status": "ACTIVE_APPEND_ONLY",
        "memory_sequence_number": sequence,
        "previous_memory_state_hash": (previous_memory_state or {}).get("memory_state_hash"),
        "memory_state_hash": "0" * 64,
        "source_modes": [scorecard["mode"]],
        "source_artifact_ids": sorted(set([scorecard_artifact_id(scorecard), *[str(item) for item in scorecard.get("source_evidence_ids", [])]])),
        "last_write_kind": "INIT" if sequence == 1 else "APPEND",
        "state_write_policy": "APPEND_AUDIT_ONLY",
        "candidate_memory_records": records,
        "failed_candidate_count": sum(1 for item in records if item.get("memory_record_status") == "FAILED"),
        "blocked_candidate_count": sum(1 for item in records if item.get("memory_record_status") == "BLOCKED"),
        "retired_candidate_count": sum(1 for item in records if item.get("memory_record_status") == "RETIRED"),
        "failed_candidates_retained": True,
        "retired_candidates_retained": True,
        "blocked_candidates_retained": True,
        "previous_search_space_retained": True,
        "previous_objective_profile_retained": True,
        "root_cause_history_retained": True,
        "risk_scaling_history_retained": True,
        "model_drift_history_retained": True,
        "dashboard_display_truth_only": True,
        "operator_warning": "Optimizer memory is not LIVE_READY and live orders remain blocked.",
        "blockers": [],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "live_permission_created": False,
        "live_config_mutation_allowed": False,
        "writes_live_ready_snapshot": False,
        "active_snapshot_mutation_allowed": False,
        "optimizer_winner_live_config_allowed": False,
        "paper_winner_live_config_allowed": False,
        "memory_reset_without_audit_allowed": False,
        "forget_failed_candidate_allowed": False,
        "cross_scope_memory_reuse_allowed": False,
        "scale_up_from_memory_allowed": False,
        "order_submission_allowed": False,
        "exchange_account_call_allowed": False,
    }
    state["memory_state_hash"] = sha256_json({key: value for key, value in state.items() if key != "memory_state_hash"})
    return state


def write_upbit_paper_convergence_memory_artifacts(
    *,
    root: Path,
    scorecard: dict[str, Any],
    previous_memory_state: dict[str, Any] | None = None,
    previous_failure_reports: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if scorecard.get("exchange") != "UPBIT" or scorecard.get("market_type") != "KRW_SPOT" or scorecard.get("mode") != "PAPER":
        raise ValueError("convergence memory writer is scoped to UPBIT/KRW_SPOT/PAPER")
    if any(scorecard.get(field) is True for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        raise ValueError("convergence memory writer refuses live or scale-up permission")

    memory = strategy_performance_memory_from_scorecard(scorecard)
    failure = failure_analysis_from_scorecard(scorecard, previous_failure_reports=previous_failure_reports)
    optimizer_memory = optimizer_memory_state_from_scorecard(
        scorecard,
        previous_memory_state=previous_memory_state,
        failure_analysis=failure,
    )
    base = (
        Path(root)
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / str(scorecard["session_id"])
        / "convergence"
    )
    strategy_memory_path = base / "strategy_performance_memory.json"
    optimizer_memory_path = base / "optimizer_memory_state.json"
    durable_atomic_write_json(strategy_memory_path, memory)
    durable_atomic_write_json(optimizer_memory_path, optimizer_memory)
    failure_path = None
    if failure is not None:
        failure_path = (
            base
            / "failure_analysis"
            / f"{safe_candidate_scorecard_filename(scorecard.get('candidate_id'))}.failure_analysis.json"
        )
        durable_atomic_write_json(failure_path, failure)
    return {
        "strategy_performance_memory": memory,
        "optimizer_memory_state": optimizer_memory,
        "failure_analysis": failure,
        "strategy_performance_memory_path": strategy_memory_path,
        "optimizer_memory_state_path": optimizer_memory_path,
        "failure_analysis_path": failure_path,
    }
