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
CONVERGENCE_OBJECTIVE_PROFILE_SCHEMA_ID = "trader1.convergence_objective_profile.v1"
EXPLORATION_POLICY_SCHEMA_ID = "trader1.exploration_exploitation_policy.v1"
OPTIMIZER_MEMORY_STATE_SCHEMA_ID = "trader1.optimizer_memory_state.v1"
FAILURE_ANALYSIS_SCHEMA_ID = "trader1.failure_analysis_report.v1"
PROFIT_CONVERGENCE_CYCLE_SCHEMA_ID = "trader1.profit_convergence_cycle_report.v1"

EXPLORATION_POLICY_DEPENDENCY_FIELDS = (
    "ranking_stability_validator_status",
    "optimizer_resource_budget_validator_status",
    "overfit_diagnostic_validator_status",
    "convergence_assessment_validator_status",
    "exploration_resource_validator_status",
    "model_drift_validator_status",
)

DEFAULT_EXPLORATION_POLICY_DEPENDENCY_STATUSES = {
    "ranking_stability_validator_status": "UNTESTED",
    "optimizer_resource_budget_validator_status": "UNTESTED",
    "overfit_diagnostic_validator_status": "UNTESTED",
    "convergence_assessment_validator_status": "UNTESTED",
    "exploration_resource_validator_status": "UNTESTED",
    "model_drift_validator_status": "UNTESTED",
}

EXPLORATION_POLICY_DEPENDENCY_BLOCKER_BY_FIELD = {
    "ranking_stability_validator_status": "RANKING_UNSTABLE",
    "optimizer_resource_budget_validator_status": "OPTIMIZER_RESOURCE_LIMIT",
    "overfit_diagnostic_validator_status": "OVERFIT_RISK_HIGH",
    "convergence_assessment_validator_status": "CONVERGENCE_STATE_UNTESTED",
    "exploration_resource_validator_status": "EXPLORATION_RESOURCE_LIMIT",
    "model_drift_validator_status": "CONVERGENCE_CLAIM_UNVERIFIED",
}

PROFIT_CONVERGENCE_CYCLE_DEPENDENCY_FIELDS = (
    "convergence_objective_profile_validator_status",
    "optimizer_memory_state_validator_status",
    "strategy_performance_memory_validator_status",
    "failure_analysis_validator_status",
    "exploration_exploitation_policy_validator_status",
    "market_regime_adaptation_validator_status",
    "model_drift_validator_status",
    "execution_feedback_loop_validator_status",
    "paper_shadow_evidence_accumulation_validator_status",
    "coverage_index_validator_status",
)

DEFAULT_PROFIT_CYCLE_DEPENDENCY_STATUSES = {
    "convergence_objective_profile_validator_status": "UNTESTED",
    "optimizer_memory_state_validator_status": "UNTESTED",
    "strategy_performance_memory_validator_status": "UNTESTED",
    "failure_analysis_validator_status": "UNTESTED",
    "exploration_exploitation_policy_validator_status": "UNTESTED",
    "market_regime_adaptation_validator_status": "UNTESTED",
    "model_drift_validator_status": "UNTESTED",
    "execution_feedback_loop_validator_status": "UNTESTED",
    "paper_shadow_evidence_accumulation_validator_status": "UNTESTED",
    "coverage_index_validator_status": "UNTESTED",
}

DEPENDENCY_BLOCKER_BY_FIELD = {
    "convergence_objective_profile_validator_status": "CONVERGENCE_OBJECTIVE_MISSING",
    "optimizer_memory_state_validator_status": "CONVERGENCE_MEMORY_MISSING",
    "strategy_performance_memory_validator_status": "CONVERGENCE_MEMORY_MISSING",
    "failure_analysis_validator_status": "CONVERGENCE_CLAIM_UNVERIFIED",
    "exploration_exploitation_policy_validator_status": "EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED",
    "market_regime_adaptation_validator_status": "REGIME_ADAPTATION_UNTESTED",
    "model_drift_validator_status": "CONVERGENCE_CLAIM_UNVERIFIED",
    "execution_feedback_loop_validator_status": "EXECUTION_QUALITY_UNTESTED",
    "paper_shadow_evidence_accumulation_validator_status": "MEASUREMENT_MISSING",
    "coverage_index_validator_status": "CONVERGENCE_STATE_UNTESTED",
}

VALIDATOR_STATUSES = {"PASS", "FAIL", "WARN", "BLOCKED", "UNTESTED", "STALE", "SKIPPED_NOT_APPLICABLE", "TIMEOUT"}

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


def _parse_utc_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _reason_counts_from_blockers(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not blockers:
        return [{"reason_code": "NO_BLOCKER_RECORDED", "count": 0}]
    counts: dict[str, int] = {}
    for item in blockers:
        code = str(item.get("code") or "UNKNOWN_BLOCKED")
        counts[code] = counts.get(code, 0) + 1
    return [{"reason_code": code, "count": count} for code, count in sorted(counts.items())]


def _dedupe_blockers(blockers: list[dict[str, Any]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in blockers:
        code = str(item.get("code") or "CONVERGENCE_CLAIM_UNVERIFIED")
        message = str(item.get("message") or "Convergence blocker requires review.")
        key = (code, message)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(
            {
                "code": code,
                "severity": str(item.get("severity") or "HIGH"),
                "message": message,
            }
        )
    return deduped


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


def convergence_objective_profile_from_scorecard(
    scorecard: dict[str, Any],
    *,
    strategy_memory: dict[str, Any] | None = None,
    authority: dict[str, str] | None = None,
) -> dict[str, Any]:
    source_modes = sorted(
        set(str(item) for item in (strategy_memory or {}).get("source_modes", [scorecard.get("mode", "PAPER")]) if item != "LIVE")
    )
    source_modes = source_modes or ["PAPER"]
    net_ev = _bounded_float(scorecard.get("net_ev_after_cost_bps"))
    raw_edge = _bounded_float(scorecard.get("gross_expected_edge_bps"))
    blockers = _dedupe_blockers(
        [
            *[blocker(str(item.get("code")), str(item.get("message")), str(item.get("severity") or "HIGH")) for item in scorecard.get("blockers", [])],
            *[blocker(str(item.get("code")), str(item.get("message")), str(item.get("severity") or "HIGH")) for item in (strategy_memory or {}).get("blockers", [])],
        ]
    )
    if "SHADOW" not in set(source_modes) and not any(item["code"] == "MEASUREMENT_MISSING" for item in blockers):
        blockers.append(
            blocker(
                "MEASUREMENT_MISSING",
                "Objective profile is derived from PAPER scorecard evidence only; SHADOW evidence is still required.",
                "MEDIUM",
            )
        )
    if raw_edge > 0 and net_ev <= 0 and not {"COST_AFTER_EDGE_UNVERIFIED", "FEE_EXCEEDS_EDGE"} & {item["code"] for item in blockers}:
        blockers.append(
            blocker(
                "COST_AFTER_EDGE_UNVERIFIED",
                "Objective profile blocks raw-PnL-only improvement because net EV after fee, slippage, and impact is not positive.",
            )
        )
    hard_codes = {
        "MIN_EDGE_FAIL",
        "FEE_EXCEEDS_EDGE",
        "COST_AFTER_EDGE_UNVERIFIED",
        "DRAWDOWN_FREEZE_ACTIVE",
        "OVERFIT_RISK_HIGH",
        "EXECUTION_FEEDBACK_DIVERGENT",
        "REGIME_MISMATCH",
        "RISK_VETO",
    }
    objective_status = "BLOCKED" if ({item["code"] for item in blockers} & hard_codes or net_ev <= 0) else "EVALUATION_ONLY"
    profile = {
        "schema_id": CONVERGENCE_OBJECTIVE_PROFILE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority or current_authority_hashes(),
        "exchange": scorecard["exchange"],
        "market_type": scorecard["market_type"],
        "mode": scorecard["mode"],
        "status": objective_status,
        "objective_profile_id": f"convergence_objective_profile:{scorecard.get('scorecard_id')}",
        "objective_profile_version": "scorecard_runtime_v1",
        "objective_status": objective_status,
        "source_modes": source_modes,
        "objective_components": [
            {"component_id": "net_ev_after_cost", "component_kind": "NET_EV_AFTER_COST", "weight": 1.0, "required": True},
            {"component_id": "drawdown_penalty", "component_kind": "DRAWDOWN_PENALTY", "weight": 0.35, "required": True},
            {"component_id": "slippage_penalty", "component_kind": "SLIPPAGE_PENALTY", "weight": 0.25, "required": True},
            {"component_id": "fee_penalty", "component_kind": "FEE_PENALTY", "weight": 0.25, "required": True},
            {"component_id": "impact_penalty", "component_kind": "IMPACT_PENALTY", "weight": 0.2, "required": True},
            {"component_id": "oos_robustness", "component_kind": "OOS_ROBUSTNESS", "weight": 0.4, "required": True},
            {"component_id": "regime_fit", "component_kind": "REGIME_FIT", "weight": 0.25, "required": True},
        ],
        "net_ev_after_cost_required": True,
        "raw_pnl_only_allowed": False,
        "live_permission_created": False,
        "live_config_mutation_allowed": False,
        "writes_live_ready_snapshot": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "operator_warning": "Objective profile is evaluation-only, not LIVE_READY, and live orders blocked.",
        "blockers": blockers,
        "notes": "Generated from non-live scorecard evidence; objective remains research-only and cannot promote or write live config.",
        "profile_hash": "0" * 64,
    }
    profile["profile_hash"] = sha256_json({key: value for key, value in profile.items() if key != "profile_hash"})
    return profile


def _normalized_dependency_statuses(
    dependency_statuses: dict[str, str] | None,
    *,
    objective_profile: dict[str, Any] | None,
    strategy_memory: dict[str, Any] | None,
    optimizer_memory: dict[str, Any] | None,
    exploration_policy: dict[str, Any] | None,
    failure_analysis: dict[str, Any] | None,
) -> dict[str, str]:
    statuses = dict(DEFAULT_PROFIT_CYCLE_DEPENDENCY_STATUSES)
    if objective_profile is not None:
        statuses["convergence_objective_profile_validator_status"] = "PASS"
    if strategy_memory is not None:
        statuses["strategy_performance_memory_validator_status"] = "PASS"
    if optimizer_memory is not None:
        statuses["optimizer_memory_state_validator_status"] = "PASS"
    if exploration_policy is not None:
        statuses["exploration_exploitation_policy_validator_status"] = "PASS"
    if failure_analysis is not None:
        statuses["failure_analysis_validator_status"] = "PASS"
    else:
        statuses["failure_analysis_validator_status"] = "SKIPPED_NOT_APPLICABLE"
    for field, status in (dependency_statuses or {}).items():
        if field not in statuses:
            continue
        statuses[field] = status if status in VALIDATOR_STATUSES else "UNTESTED"
    return statuses


def _dependency_blockers(statuses: dict[str, str]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for field in PROFIT_CONVERGENCE_CYCLE_DEPENDENCY_FIELDS:
        status = statuses[field]
        if status == "PASS":
            continue
        blockers.append(
            blocker(
                DEPENDENCY_BLOCKER_BY_FIELD[field],
                f"{field} is {status}; convergence cycle remains non-promotional and live orders stay blocked.",
                "MEDIUM",
            )
        )
    return blockers


def _source_ids_for_cycle(
    scorecard: dict[str, Any],
    objective_profile: dict[str, Any] | None,
    strategy_memory: dict[str, Any] | None,
    optimizer_memory: dict[str, Any] | None,
    exploration_policy: dict[str, Any] | None,
    failure_analysis: dict[str, Any] | None,
) -> list[str]:
    source_ids = [scorecard_artifact_id(scorecard), *[str(item) for item in scorecard.get("source_evidence_ids", [])]]
    if objective_profile is not None:
        source_ids.append(f"convergence_objective_profile:{objective_profile.get('objective_profile_id')}:{objective_profile.get('profile_hash')}")
    if strategy_memory is not None:
        source_ids.append(
            f"strategy_performance_memory:{strategy_memory.get('strategy_performance_memory_id')}:{sha256_json(strategy_memory)}"
        )
        source_ids.extend(str(item) for item in strategy_memory.get("source_artifact_ids", []))
    if optimizer_memory is not None:
        source_ids.append(f"optimizer_memory_state:{optimizer_memory.get('optimizer_memory_state_id')}:{sha256_json(optimizer_memory)}")
        source_ids.extend(str(item) for item in optimizer_memory.get("source_artifact_ids", []))
    if exploration_policy is not None:
        source_ids.append(f"exploration_exploitation_policy:{exploration_policy.get('policy_id')}:{sha256_json(exploration_policy)}")
        source_ids.extend(str(item) for item in exploration_policy.get("source_evidence_ids", []))
    if failure_analysis is not None:
        source_ids.append(f"failure_analysis:{failure_analysis.get('failure_analysis_id')}:{failure_analysis.get('audit_hash')}")
        source_ids.extend(str(item) for item in failure_analysis.get("source_evidence_ids", []))
    return sorted(set(source_ids))


def _scorecard_robustness_passes(scorecard: dict[str, Any]) -> bool:
    return (
        scorecard.get("robustness_ready") is True
        and scorecard.get("oos_status") == "PASS"
        and scorecard.get("walk_forward_status") == "PASS"
        and scorecard.get("bootstrap_status") == "PASS"
        and scorecard.get("overfit_status") == "LOW"
    )


def _exploration_candidate_count(scorecard: dict[str, Any]) -> int:
    evaluated = _int_value(scorecard.get("evaluated_symbol_count"), 0)
    paper_review = _int_value(scorecard.get("paper_entry_review_symbol_count"), 0)
    alternatives = _int_value(scorecard.get("alternative_candidate_count"), 0)
    return max(1, evaluated, paper_review + alternatives + 1)


def _exploration_policy_dependency_statuses(
    scorecard: dict[str, Any],
    *,
    candidate_count: int,
    candidate_budget: int,
    dependency_statuses: dict[str, str] | None = None,
) -> dict[str, str]:
    statuses = dict(DEFAULT_EXPLORATION_POLICY_DEPENDENCY_STATUSES)
    statuses["ranking_stability_validator_status"] = "PASS" if _scorecard_robustness_passes(scorecard) else "BLOCKED"
    statuses["optimizer_resource_budget_validator_status"] = "PASS" if candidate_count <= candidate_budget else "BLOCKED"
    statuses["overfit_diagnostic_validator_status"] = "PASS" if _scorecard_robustness_passes(scorecard) else "BLOCKED"
    statuses["exploration_resource_validator_status"] = "PASS" if 0 < candidate_count <= candidate_budget else "BLOCKED"
    for field, status in (dependency_statuses or {}).items():
        if field not in statuses:
            continue
        statuses[field] = status if status in VALIDATOR_STATUSES else "UNTESTED"
    return statuses


def _exploration_policy_dependency_blockers(statuses: dict[str, str]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for field in EXPLORATION_POLICY_DEPENDENCY_FIELDS:
        status = statuses[field]
        if status == "PASS":
            continue
        blockers.append(
            blocker(
                EXPLORATION_POLICY_DEPENDENCY_BLOCKER_BY_FIELD[field],
                f"{field} is {status}; exploration-to-exploitation transition remains analysis-only.",
                "MEDIUM",
            )
        )
    return blockers


def exploration_exploitation_policy_from_scorecard(
    scorecard: dict[str, Any],
    *,
    objective_profile: dict[str, Any] | None = None,
    strategy_memory: dict[str, Any] | None = None,
    optimizer_memory: dict[str, Any] | None = None,
    failure_analysis: dict[str, Any] | None = None,
    dependency_statuses: dict[str, str] | None = None,
    authority: dict[str, str] | None = None,
) -> dict[str, Any]:
    if any(scorecard.get(field) is True for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        raise ValueError("exploration/exploitation policy refuses scorecard live or scale-up permission")

    source_modes = sorted(
        set(str(item) for item in (strategy_memory or {}).get("source_modes", [scorecard.get("mode", "PAPER")]) if item != "LIVE")
    )
    source_modes = source_modes or ["PAPER"]
    source_mode_set = set(source_modes)
    candidate_count = _exploration_candidate_count(scorecard)
    candidate_budget = 20
    statuses = _exploration_policy_dependency_statuses(
        scorecard,
        candidate_count=candidate_count,
        candidate_budget=candidate_budget,
        dependency_statuses=dependency_statuses,
    )
    pass_count = sum(1 for status in statuses.values() if status == "PASS")
    all_dependencies_pass = pass_count == len(EXPLORATION_POLICY_DEPENDENCY_FIELDS)
    candidate_budget_status = "PASS" if candidate_count <= candidate_budget else "BLOCKED"
    net_ev = min(
        _bounded_float(scorecard.get("net_ev_after_cost_bps")),
        _bounded_float((strategy_memory or {}).get("net_ev_after_cost"), default=_bounded_float(scorecard.get("net_ev_after_cost_bps"))),
    )
    objective_valid = (
        net_ev > 0
        and (objective_profile or {}).get("objective_status") != "BLOCKED"
        and not any(item.get("code") in {"COST_AFTER_EDGE_UNVERIFIED", "FEE_EXCEEDS_EDGE"} for item in scorecard.get("blockers", []))
    )
    cooldown_cycles = min(5, max(1, _int_value((failure_analysis or {}).get("repeated_failure_count"), 0))) if failure_analysis else 0
    blockers = _dedupe_blockers(
        [
            *[blocker(str(item.get("code")), str(item.get("message")), str(item.get("severity") or "HIGH")) for item in scorecard.get("blockers", [])],
            *[blocker(str(item.get("code")), str(item.get("message")), str(item.get("severity") or "HIGH")) for item in (strategy_memory or {}).get("blockers", [])],
            *[blocker(str(item.get("code")), str(item.get("message")), str(item.get("severity") or "HIGH")) for item in (objective_profile or {}).get("blockers", [])],
            *[blocker(str(item.get("code")), str(item.get("message")), str(item.get("severity") or "HIGH")) for item in (failure_analysis or {}).get("blockers", [])],
            *_exploration_policy_dependency_blockers(statuses),
        ]
    )
    if "SHADOW" not in source_mode_set and not any(item["code"] == "MEASUREMENT_MISSING" for item in blockers):
        blockers.append(
            blocker(
                "MEASUREMENT_MISSING",
                "Exploration policy requires SHADOW evidence before limited PAPER ranking exploitation review.",
                "MEDIUM",
            )
        )
    if candidate_budget_status != "PASS":
        blockers.append(
            blocker(
                "CANDIDATE_BUDGET_EXCEEDED",
                f"Exploration candidate count {candidate_count} exceeds budget {candidate_budget}; transition is blocked.",
            )
        )
    if cooldown_cycles > 0 and not any(item["code"] == "COOLDOWN" for item in blockers):
        blockers.append(
            blocker(
                "COOLDOWN",
                f"Candidate remains in cooldown for {cooldown_cycles} convergence cycle(s) after blocked scorecard evidence.",
                "MEDIUM",
            )
        )

    limited_exploitation_allowed = (
        all_dependencies_pass
        and candidate_budget_status == "PASS"
        and objective_valid
        and scorecard.get("ranking_eligible") is True
        and {"PAPER", "SHADOW"}.issubset(source_mode_set)
        and cooldown_cycles == 0
        and not blockers
    )
    if limited_exploitation_allowed:
        policy_scope = "PAPER_RANKING_REVIEW_ONLY"
        policy_status = "PAPER_RANKING_REVIEW_ELIGIBLE"
        controller_state = "EXPLOITING_PAPER_ONLY"
        transition_decision = "LIMITED_EXPLOITATION_REVIEW"
        recommendation_scope = "PAPER_RANKING_REVIEW_ONLY"
        objective_basis = "NET_EV_AFTER_COST"
        exploration_rate_pct = 40.0
        exploitation_rate_pct = 60.0
        exploitation_candidate_id = str(scorecard["candidate_id"])
        status = "PASS"
        blocks_promotion = False
    elif not objective_valid or failure_analysis is not None or cooldown_cycles > 0 or candidate_budget_status != "PASS":
        policy_scope = "RESEARCH_BLOCKED"
        policy_status = "BLOCKED"
        controller_state = "BLOCKED"
        transition_decision = "BLOCK_TRANSITION"
        recommendation_scope = "BLOCKED"
        objective_basis = "BLOCKED_NO_VALID_OBJECTIVE" if not objective_valid else "NET_EV_AFTER_COST"
        exploration_rate_pct = 100.0
        exploitation_rate_pct = 0.0
        exploitation_candidate_id = None
        status = "BLOCKED"
        blocks_promotion = True
    else:
        policy_scope = "REPLAY_PAPER_SHADOW_READ_ONLY_ONLY"
        policy_status = "ACTIVE_ANALYSIS_ONLY"
        controller_state = "EXPLORING"
        transition_decision = "KEEP_EXPLORING"
        recommendation_scope = "ANALYSIS_ONLY"
        objective_basis = "NET_EV_AFTER_COST"
        exploration_rate_pct = 100.0
        exploitation_rate_pct = 0.0
        exploitation_candidate_id = None
        status = "BLOCKED"
        blocks_promotion = True

    dependency_summary_status = "PASS" if all_dependencies_pass else "BLOCKED" if "BLOCKED" in set(statuses.values()) else "UNTESTED"
    source_ids = [
        scorecard_artifact_id(scorecard),
        *[str(item) for item in scorecard.get("source_evidence_ids", [])],
    ]
    for artifact in (objective_profile, strategy_memory, optimizer_memory, failure_analysis):
        if artifact is None:
            continue
        source_ids.append(sha256_json(artifact))
        source_ids.extend(str(item) for item in artifact.get("source_evidence_ids", []))
        source_ids.extend(str(item) for item in artifact.get("source_artifact_ids", []))

    return {
        "schema_id": EXPLORATION_POLICY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority or current_authority_hashes(),
        "policy_id": f"exploration_exploitation_policy:{scorecard.get('scorecard_id')}",
        "exchange": scorecard["exchange"],
        "market_type": scorecard["market_type"],
        "mode": scorecard["mode"],
        "session_id": scorecard["session_id"],
        "strategy_id": scorecard["strategy_id"],
        "parameter_hash": scorecard["parameter_hash"],
        "timeframe_scope": scorecard["timeframe_scope"],
        "regime_scope": scorecard["regime_scope"],
        "policy_scope": policy_scope,
        "policy_status": policy_status,
        "controller_state": controller_state,
        "transition_decision": transition_decision,
        "recommendation_scope": recommendation_scope,
        "objective_basis": objective_basis,
        "source_modes": source_modes,
        "source_evidence_ids": sorted(set(source_ids)),
        "dependency_summary_status": dependency_summary_status,
        **statuses,
        "required_dependency_count": len(EXPLORATION_POLICY_DEPENDENCY_FIELDS),
        "dependency_pass_count": pass_count,
        "exploration_candidate_budget": candidate_budget,
        "candidate_count": candidate_count,
        "candidate_budget_status": candidate_budget_status,
        "exploitation_candidate_id": exploitation_candidate_id,
        "exploitation_allowed_for_paper_ranking": limited_exploitation_allowed,
        "exploration_rate_pct": exploration_rate_pct,
        "exploitation_rate_pct": exploitation_rate_pct,
        "min_exploration_rate_pct": 20.0,
        "max_exploitation_rate_pct": 70.0,
        "cooldown_cycles_remaining": cooldown_cycles,
        "blocks_promotion": blocks_promotion,
        "blocks_live_order": True,
        "live_readiness_status": "NOT_LIVE_READY",
        "operator_warning": "exploration/exploitation policy is not LIVE_READY; live orders blocked and scale-up blocked",
        "status": status,
        "blockers": blockers,
        "notes": "Generated from non-live Upbit PAPER scorecard and convergence memory; policy cannot mutate live config or submit orders.",
        "dashboard_display_truth_only": True,
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
        "scale_up_recommendation_allowed": False,
    }


def profit_convergence_cycle_from_scorecard(
    scorecard: dict[str, Any],
    *,
    objective_profile: dict[str, Any] | None = None,
    strategy_memory: dict[str, Any] | None,
    optimizer_memory: dict[str, Any] | None,
    exploration_policy: dict[str, Any] | None = None,
    failure_analysis: dict[str, Any] | None = None,
    dependency_statuses: dict[str, str] | None = None,
    previous_cycle_report: dict[str, Any] | None = None,
    authority: dict[str, str] | None = None,
    max_data_age_seconds: float = 180.0,
) -> dict[str, Any]:
    if any(scorecard.get(field) is True for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        raise ValueError("profit convergence cycle refuses scorecard live or scale-up permission")

    statuses = _normalized_dependency_statuses(
        dependency_statuses,
        objective_profile=objective_profile,
        strategy_memory=strategy_memory,
        optimizer_memory=optimizer_memory,
        exploration_policy=exploration_policy,
        failure_analysis=failure_analysis,
    )
    source_modes = sorted(set(str(item) for item in (strategy_memory or {}).get("source_modes", [scorecard.get("mode", "PAPER")]) if item != "LIVE"))
    source_modes = source_modes or ["PAPER"]
    now = utc_now()
    scorecard_time = _parse_utc_datetime(scorecard.get("generated_at_utc"))
    generated_time = _parse_utc_datetime(now) or datetime.now(timezone.utc)
    data_age_seconds = 0.0
    if scorecard_time is not None:
        data_age_seconds = max(0.0, (generated_time - scorecard_time).total_seconds())
    data_fresh = data_age_seconds <= max_data_age_seconds
    gross_bps = _bounded_float(scorecard.get("gross_expected_edge_bps"))
    net_bps = min(
        _bounded_float(scorecard.get("net_ev_after_cost_bps")),
        _bounded_float((strategy_memory or {}).get("net_ev_after_cost"), default=_bounded_float(scorecard.get("net_ev_after_cost_bps"))),
    )
    raw_pnl_improved = gross_bps > 0
    net_ev_positive = net_bps > 0
    raw_positive_net_negative = raw_pnl_improved and not net_ev_positive
    pass_count = sum(1 for status in statuses.values() if status == "PASS")
    dependency_all_pass = pass_count == len(PROFIT_CONVERGENCE_CYCLE_DEPENDENCY_FIELDS)
    model_drift_status = "NO_DRIFT" if statuses["model_drift_validator_status"] == "PASS" else "NOT_EVALUATED"
    blockers = _dedupe_blockers(
        [
            *[blocker(str(item.get("code")), str(item.get("message")), str(item.get("severity") or "HIGH")) for item in scorecard.get("blockers", [])],
            *[blocker(str(item.get("code")), str(item.get("message")), str(item.get("severity") or "HIGH")) for item in (strategy_memory or {}).get("blockers", [])],
            *[blocker(str(item.get("code")), str(item.get("message")), str(item.get("severity") or "HIGH")) for item in (exploration_policy or {}).get("blockers", [])],
            *[blocker(str(item.get("code")), str(item.get("message")), str(item.get("severity") or "HIGH")) for item in (failure_analysis or {}).get("blockers", [])],
            *_dependency_blockers(statuses),
        ]
    )
    if raw_positive_net_negative and not {"COST_AFTER_EDGE_UNVERIFIED", "FEE_EXCEEDS_EDGE"} & {item["code"] for item in blockers}:
        blockers.append(
            blocker(
                "COST_AFTER_EDGE_UNVERIFIED",
                "Raw PnL is positive but net EV after cost is not positive; cost-adjusted convergence is blocked.",
            )
        )
    if not data_fresh:
        blockers.append(
            blocker(
                "CONVERGENCE_MEMORY_STALE",
                "Profit convergence cycle input is stale; ranking and promotion remain blocked.",
                "HIGH",
            )
        )
    local_review_allowed = (
        dependency_all_pass
        and data_fresh
        and net_ev_positive
        and not blockers
        and scorecard.get("ranking_eligible") is True
        and model_drift_status == "NO_DRIFT"
    )
    if local_review_allowed:
        cycle_status = "LOCAL_IMPROVEMENT_REVIEW"
        convergence_claim = "LOCALLY_IMPROVING"
        objective_basis = "NET_EV_AFTER_COST"
        ranking_allowed = True
        blocks_promotion = False
    else:
        cycle_status = "BLOCKED" if scorecard.get("blockers") or failure_analysis is not None or raw_positive_net_negative else "COLLECTING"
        convergence_claim = "BLOCKED" if cycle_status == "BLOCKED" else "NO_CLAIM"
        objective_basis = "NET_EV_AFTER_COST" if net_ev_positive else "BLOCKED_NO_VALID_OBJECTIVE"
        ranking_allowed = False
        blocks_promotion = True
    cycle_index = _int_value((optimizer_memory or {}).get("memory_sequence_number"), 0)
    previous_hash = (previous_cycle_report or {}).get("cycle_hash")
    report = {
        "schema_id": PROFIT_CONVERGENCE_CYCLE_SCHEMA_ID,
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": authority or current_authority_hashes(),
        "cycle_id": f"profit_convergence_cycle:{scorecard.get('scorecard_id')}:{cycle_index}",
        "cycle_index": cycle_index,
        "previous_cycle_hash": previous_hash if isinstance(previous_hash, str) else None,
        "exchange": scorecard["exchange"],
        "market_type": scorecard["market_type"],
        "mode": scorecard["mode"],
        "session_id": scorecard["session_id"],
        "strategy_id": scorecard["strategy_id"],
        "strategy_build_id": scorecard["strategy_build_id"],
        "parameter_hash": scorecard["parameter_hash"],
        "timeframe_scope": scorecard["timeframe_scope"],
        "regime_scope": scorecard["regime_scope"],
        "source_modes": source_modes,
        "source_evidence_ids": _source_ids_for_cycle(scorecard, objective_profile, strategy_memory, optimizer_memory, exploration_policy, failure_analysis),
        **statuses,
        "required_dependency_count": len(PROFIT_CONVERGENCE_CYCLE_DEPENDENCY_FIELDS),
        "dependency_pass_count": pass_count,
        "cycle_status": cycle_status,
        "convergence_claim": convergence_claim,
        "objective_basis": objective_basis,
        "objective_score_delta_bps": net_bps,
        "net_ev_after_cost_delta_bps": net_bps,
        "raw_pnl_improved": raw_pnl_improved,
        "net_ev_after_cost_positive": net_ev_positive,
        "raw_pnl_positive_net_ev_negative": raw_positive_net_negative,
        "data_freshness_status": "FRESH" if data_fresh else "STALE",
        "data_age_seconds": data_age_seconds,
        "max_data_age_seconds": max_data_age_seconds,
        "model_drift_status": model_drift_status,
        "candidate_ranking_allowed_for_paper": ranking_allowed,
        "blocks_promotion": blocks_promotion,
        "blocks_live_order": True,
        "dashboard_display_truth_only": True,
        "operator_warning": "profit convergence cycle is not LIVE_READY; live orders blocked; no profit guarantee",
        "next_operator_action": "continue implementation and bounded non-live validation; do not start long PAPER until convergence gates pass",
        "live_permission_created": False,
        "live_config_mutation_allowed": False,
        "writes_live_ready_snapshot": False,
        "active_snapshot_mutation_allowed": False,
        "optimizer_winner_live_config_allowed": False,
        "paper_winner_live_config_allowed": False,
        "model_promotion_allowed": False,
        "scale_up_recommendation_allowed": False,
        "order_submission_allowed": False,
        "exchange_account_call_allowed": False,
        "profitability_guarantee_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "blockers": blockers,
        "cycle_hash": "0" * 64,
        "status": "PASS" if local_review_allowed else "BLOCKED",
        "notes": "Generated from non-live scorecard, strategy performance memory, optimizer memory, and failure analysis artifacts.",
    }
    report["cycle_hash"] = sha256_json({key: value for key, value in report.items() if key != "cycle_hash"})
    return report


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
        "exit_reason_counts": (
            [
                {"reason_code": str(item.get("reason_code") or ""), "count": _int_value(item.get("count"))}
                for item in scorecard.get("strategy_exit_reason_counts", [])
                if isinstance(item, dict) and item.get("reason_code")
            ]
            or [{"reason_code": "SCORECARD_CLOSED_TRADE_EVIDENCE", "count": trade_count}]
        ),
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
    extra_source_modes: list[str] | None = None,
    extra_source_artifact_ids: list[str] | None = None,
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
    source_modes = _source_modes(scorecard, extra_source_modes)
    source_artifact_ids = [
        scorecard_artifact_id(scorecard),
        *[str(item) for item in scorecard.get("source_evidence_ids", [])],
        *[str(item) for item in extra_source_artifact_ids or []],
    ]
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
        "source_modes": source_modes,
        "source_artifact_ids": sorted(set(source_artifact_ids)),
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
    extra_source_modes: list[str] | None = None,
    extra_source_artifact_ids: list[str] | None = None,
    exploration_policy_dependency_statuses: dict[str, str] | None = None,
    profit_cycle_dependency_statuses: dict[str, str] | None = None,
) -> dict[str, Any]:
    if scorecard.get("exchange") != "UPBIT" or scorecard.get("market_type") != "KRW_SPOT" or scorecard.get("mode") != "PAPER":
        raise ValueError("convergence memory writer is scoped to UPBIT/KRW_SPOT/PAPER")
    if any(scorecard.get(field) is True for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        raise ValueError("convergence memory writer refuses live or scale-up permission")

    memory = strategy_performance_memory_from_scorecard(
        scorecard,
        extra_source_modes=extra_source_modes,
        extra_source_artifact_ids=extra_source_artifact_ids,
    )
    objective_profile = convergence_objective_profile_from_scorecard(scorecard, strategy_memory=memory)
    failure = failure_analysis_from_scorecard(scorecard, previous_failure_reports=previous_failure_reports)
    optimizer_memory = optimizer_memory_state_from_scorecard(
        scorecard,
        previous_memory_state=previous_memory_state,
        failure_analysis=failure,
        extra_source_modes=extra_source_modes,
        extra_source_artifact_ids=extra_source_artifact_ids,
    )
    exploration_policy = exploration_exploitation_policy_from_scorecard(
        scorecard,
        objective_profile=objective_profile,
        strategy_memory=memory,
        optimizer_memory=optimizer_memory,
        failure_analysis=failure,
        dependency_statuses=exploration_policy_dependency_statuses,
    )
    profit_cycle = profit_convergence_cycle_from_scorecard(
        scorecard,
        objective_profile=objective_profile,
        strategy_memory=memory,
        optimizer_memory=optimizer_memory,
        exploration_policy=exploration_policy,
        failure_analysis=failure,
        dependency_statuses=profit_cycle_dependency_statuses,
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
    objective_profile_path = base / "convergence_objective_profile.json"
    exploration_policy_path = base / "exploration_exploitation_policy.json"
    optimizer_memory_path = base / "optimizer_memory_state.json"
    profit_cycle_path = base / "profit_convergence_cycle_report.json"
    durable_atomic_write_json(strategy_memory_path, memory)
    durable_atomic_write_json(objective_profile_path, objective_profile)
    durable_atomic_write_json(exploration_policy_path, exploration_policy)
    durable_atomic_write_json(optimizer_memory_path, optimizer_memory)
    durable_atomic_write_json(profit_cycle_path, profit_cycle)
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
        "convergence_objective_profile": objective_profile,
        "exploration_exploitation_policy": exploration_policy,
        "optimizer_memory_state": optimizer_memory,
        "failure_analysis": failure,
        "profit_convergence_cycle_report": profit_cycle,
        "strategy_performance_memory_path": strategy_memory_path,
        "convergence_objective_profile_path": objective_profile_path,
        "exploration_exploitation_policy_path": exploration_policy_path,
        "optimizer_memory_state_path": optimizer_memory_path,
        "failure_analysis_path": failure_path,
        "profit_convergence_cycle_report_path": profit_cycle_path,
    }
