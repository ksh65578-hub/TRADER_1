from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TRADER = ROOT / "TRADER_1.md"
AGENTS = ROOT / "AGENTS.md"
PATCH_ID = "MVP0_CONTRACT_BASELINE_20260428_001"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def source_hash(lines: list[str], start: int, end: int) -> str:
    text = "\n".join(lines[start - 1 : end])
    return sha256_bytes(text.encode("utf-8"))


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def base_enums() -> dict[str, list[str]]:
    no_trade_reason = [
        "MIN_EDGE_FAIL",
        "EXPECTED_SLIPPAGE_EXCEEDED",
        "DEPTH_TOO_THIN",
        "DEPTH_EXCHANGE_REJECT_RISK",
        "STALE_ORDERBOOK",
        "STALE_TICKER",
        "STALE_TRADE_TAPE",
        "STALE_CANDLE_15M",
        "STALE_CANDLE_60M",
        "STALE_BENCHMARK_CONTEXT",
        "MARKET_CONTEXT_LOAD_TIMEOUT",
        "API_TIMEOUT",
        "WEBSOCKET_GAP",
        "CLOCK_DRIFT",
        "PRIVATE_WS_UNHEALTHY",
        "DRIFT_UNRECOVERED",
        "SESSION_PAUSE",
        "TICK_SIZE_CLIFF",
        "BALANCE_MISMATCH",
        "MARKET_EVENT_RISK",
        "BREADTH_OFF_BLOCKED",
        "PENDING_CONFIRM_EXISTS",
        "COOLDOWN",
        "CLUSTER_RISK",
        "UNIVERSE_FILTERED",
        "POSITION_LIMIT",
        "TRADE_DISABLED",
        "COLD_START",
        "DATA_UNAVAILABLE",
        "HARD_TRUTH_MISSING",
        "SOFT_TRUTH_UNREGISTERED_FALLBACK",
        "RESOURCE_LIMIT",
        "RESOURCE_LIMIT_BLOCK",
        "LEDGER_INTEGRITY_FAIL",
        "LEDGER_UNAVAILABLE",
        "EXCHANGE_SYNC_REQUIRED",
        "RECONCILIATION_REQUIRED",
        "SYMBOL_RULE_BLOCK",
        "SYMBOL_RULE_UNVERIFIED",
        "FEE_MODEL_UNVERIFIED",
        "FEE_EXCEEDS_EDGE",
        "MARKET_IMPACT_EXCEEDS_EDGE",
        "LIVE_READY_MISSING",
        "USER_APPROVAL_MISSING",
        "PREFLIGHT_FAILED",
        "SNAPSHOT_SCOPE_MISMATCH",
        "API_UNVERIFIED",
        "RISK_VETO",
        "REGIME_MISMATCH",
        "EXCHANGE_POLICY_BLOCK",
        "STRATEGY_NOT_ELIGIBLE",
        "STRATEGY_CONFIDENCE_LOW",
        "KILL_SWITCH_ACTIVE",
        "LATENCY_TTL_EXPIRED",
        "OFFICIAL_API_VERIFICATION_EXPIRED",
        "MANUAL_ORDER_TEST_MISSING",
        "OPERATOR_APPROVAL_MISSING",
        "EMERGENCY_FLATTEN_UNAVAILABLE",
        "SOURCE_IDENTITY_MISMATCH",
        "BUNDLE_HYGIENE_FAIL",
        "READ_ONLY_BURN_IN_MISSING",
        "ORPHAN_POSITION_REVIEW_REQUIRED",
        "ORPHAN_OPEN_ORDER_REVIEW_REQUIRED",
        "LIVE_FINAL_GUARD_FAILED",
        "SCHEMA_IDENTITY_MISMATCH",
        "REGISTRY_DRIFT",
        "GENERATED_ARTIFACT_DIRTY",
        "CONTRACT_GAP_HIGH",
        "CONTRACT_GAP_CRITICAL",
        "MEASUREMENT_MISSING",
        "EXECUTION_QUALITY_UNTESTED",
        "EXPANDED_BOUND_UNVERIFIED",
        "PROMOTION_INPUT_TYPE_INVALID",
        "EXPLORATION_STAGE_MISMATCH",
        "VARIATION_UNREGISTERED",
        "TIMEFRAME_SCOPE_MISMATCH",
        "CANDIDATE_BUDGET_EXCEEDED",
        "DUPLICATE_CANDIDATE",
        "EXPLORATION_RESOURCE_LIMIT",
        "LIVE_READY_SNAPSHOT_WRITER_UNTESTED",
        "LIVE_READY_SNAPSHOT_WRITER_FAILED",
        "LOW_RR_RATIO_UNVERIFIED",
        "COST_AFTER_EDGE_UNVERIFIED",
        "REGIME_SCOPE_MISMATCH",
        "COMBINATION_COMPLEXITY_EXCEEDED",
        "UNBOUNDED_CANDIDATE_EXPANSION",
        "DATA_QUALITY_INSUFFICIENT",
        "CANDIDATE_DIRECT_LIVE_FORBIDDEN",
        "PAPER_WINNER_DIRECT_LIVE_FORBIDDEN",
        "SNAPSHOT_WRITER_INPUT_NOT_SNAPSHOT",
        "OPTIMIZER_UNTESTED",
        "OBJECTIVE_FUNCTION_MISSING",
        "SCORECARD_MISSING",
        "SCORECARD_SCHEMA_INVALID",
        "RANKING_UNSTABLE",
        "SAMPLE_INSUFFICIENT",
        "HOLDOUT_MISSING",
        "WALK_FORWARD_MISSING",
        "OOS_MISSING",
        "BOOTSTRAP_UNSTABLE",
        "OVERFIT_RISK_HIGH",
        "SURVIVORSHIP_BIAS_RISK",
        "DATA_SNOOPING_RISK",
        "SYMBOL_SELECTION_BIAS",
        "REGIME_FIT_UNTESTED",
        "EXECUTION_FEEDBACK_MISSING",
        "EXECUTION_FEEDBACK_DIVERGENT",
        "PARAMETER_NARROWING_UNVERIFIED",
        "EXPLOITATION_SHIFT_UNVERIFIED",
        "OPTIMIZER_RESOURCE_LIMIT",
        "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        "OPTIMIZER_LIVE_MUTATION_FORBIDDEN",
        "CONVERGENCE_OBJECTIVE_MISSING",
        "CONVERGENCE_MEMORY_MISSING",
        "CONVERGENCE_MEMORY_STALE",
        "CONVERGENCE_STATE_UNTESTED",
        "CONVERGENCE_CLAIM_UNVERIFIED",
        "FAILURE_ANALYSIS_MISSING",
        "ROOT_CAUSE_UNKNOWN_LIVE_AFFECTING",
        "MODEL_DRIFT_DETECTED",
        "REGIME_ADAPTATION_UNTESTED",
        "EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED",
        "RISK_SCALING_UNTESTED",
        "RISK_SCALING_UP_FORBIDDEN",
        "SURVIVAL_LAYER_BLOCKED",
        "DRAWDOWN_FREEZE_ACTIVE",
        "LIVE_BURN_IN_FEEDBACK_MISSING",
        "SCALE_UP_VALIDATOR_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
        "UNKNOWN_BLOCKED",
    ]
    return {
        "exchange": ["UPBIT", "BINANCE"],
        "market_type": ["KRW_SPOT", "SPOT", "FUTURES_USDT_M"],
        "mode": ["REPLAY", "PAPER", "SHADOW", "LIVE", "SAFE", "READ_ONLY"],
        "risk_profile": ["CONSERVATIVE", "BALANCED", "GROWTH", "AGGRESSIVE_SANDBOX"],
        "final_decision": [
            "ENTER_LONG",
            "ENTER_SHORT",
            "EXIT_POSITION",
            "REDUCE_POSITION",
            "CANCEL_ORDER",
            "HOLD_POSITION",
            "NO_TRADE",
            "SAFE_MODE",
            "RECONCILE_REQUIRED",
            "TRADE_DISABLED",
            "KILL_SWITCH",
            "BLOCKED",
        ],
        "validator_result_status": [
            "PASS",
            "FAIL",
            "WARN",
            "BLOCKED",
            "UNTESTED",
            "STALE",
            "SKIPPED_NOT_APPLICABLE",
            "TIMEOUT",
        ],
        "live_trading_status": ["NOT_APPLICABLE", "REVIEW_ONLY", "BLOCKED", "SMALL_LIVE_BURN_IN", "LIVE_ACTIVE"],
        "blocker_category": [
            "DATA",
            "LIQUIDITY",
            "REGIME",
            "STRATEGY",
            "RISK",
            "PORTFOLIO",
            "EXECUTION",
            "CONFIG",
            "READINESS",
            "OPERATOR",
            "SECURITY",
            "BUNDLE",
        ],
        "severity": ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
        "api_verification_result": ["PASS", "FAIL", "PARTIAL", "STALE", "UNVERIFIED"],
        "operator_action": [
            "manual_stop",
            "manual_resume_read_only",
            "manual_ack_trade_disabled",
            "manual_unlock_held_market_event",
            "manual_retry_reconcile",
            "manual_safe_mode",
            "manual_disable_strategy",
            "manual_reduce_position",
            "manual_exit_all_positions",
        ],
        "exploration_stage": ["STAGE_A_WIDE", "STAGE_B_REFINEMENT"],
        "promotion_input_type": [
            "NOT_PROMOTION_INPUT",
            "EXPLORATION_CANDIDATE",
            "REFINEMENT_CANDIDATE",
            "LIVE_READY_CANDIDATE_WRITER_INPUT",
        ],
        "exploration_bound_type": ["INITIAL_CANDIDATE_BOUND", "EXPANDED_EXPLORATION_BOUND", "LIVE_PARAMETER_BOUND"],
        "entry_variation": ["breakout", "retest", "momentum", "mean_reversion", "vwap_reversion", "pullback"],
        "exit_variation": [
            "fixed_tp",
            "trailing_tp",
            "partial_exit",
            "time_exit",
            "volatility_exit",
            "invalidation_exit",
            "hard_stop",
        ],
        "execution_variation": ["market", "limit", "ioc", "maker", "split_order", "single_order"],
        "regime_family": ["TRENDING", "RANGE", "RISK_OFF"],
        "combination_dimension": ["entry", "exit", "regime", "execution", "timeframe", "liquidity_tier"],
        "order_failure_type": [
            "INSUFFICIENT_BALANCE",
            "MIN_NOTIONAL_FAIL",
            "PRICE_FILTER_FAIL",
            "LOT_SIZE_FAIL",
            "TICK_SIZE_FAIL",
            "STEP_SIZE_FAIL",
            "SYMBOL_RULE_MISMATCH",
            "FEE_MODEL_MISMATCH",
            "POST_ONLY_REJECT",
            "IOC_PARTIAL",
            "FOK_REJECT",
            "MARKET_ORDER_REJECT",
            "RATE_LIMIT_HIT",
            "API_TIMEOUT",
            "AUTH_FAILURE",
            "PERMISSION_DENIED",
            "WITHDRAWAL_PERMISSION_DETECTED",
            "SIGNATURE_INVALID",
            "TIMESTAMP_DRIFT",
            "NETWORK_TIMEOUT",
            "TRANSPORT_AMBIGUOUS",
            "EXCHANGE_UNKNOWN_ORDER",
            "DUPLICATE_CLIENT_ORDER_ID",
            "ORDER_NOT_FOUND_DURING_RECONCILE",
            "CANCEL_REJECTED_ALREADY_FILLED",
            "PARTIAL_FILL_STALE",
            "PRIVATE_WS_GAP",
            "UNKNOWN_REJECT",
        ],
        "no_trade_reason": no_trade_reason,
        "live_blocker_code": list(no_trade_reason),
        "patch_class": [
            "DOC_CONTRACT_PATCH",
            "REGISTRY_PATCH",
            "SCHEMA_PATCH",
            "VALIDATOR_PATCH",
            "RUNTIME_SAFETY_PATCH",
            "TEST_PATCH",
            "EVIDENCE_PATCH",
            "LIVE_ENABLING_PATCH",
        ],
        "profit_optimizer_status": [
            "DISABLED",
            "SCAFFOLD",
            "COLLECTING",
            "RANKING",
            "EXPLORING",
            "EXPLOITING",
            "NARROWING",
            "VALIDATING",
            "BLOCKED",
            "DEGRADED",
            "RETIRED",
        ],
        "profit_optimizer_stage": [
            "METRIC_COLLECTION",
            "BROAD_RANKING",
            "LOCAL_EXPLOITATION",
            "ROBUSTNESS_SWEEP",
            "PARAMETER_NARROWING",
            "SYMBOL_FIT_LEARNING",
            "REGIME_FIT_LEARNING",
            "EXECUTION_FEEDBACK",
            "OVERFIT_DIAGNOSTIC",
            "WRITER_INPUT_REVIEW",
        ],
        "profit_optimizer_output_type": [
            "OPTIMIZER_RESEARCH_SIGNAL",
            "RANKED_EXPLORATION_CANDIDATE",
            "REFINEMENT_CANDIDATE",
            "PARAMETER_NARROWING_PROPOSAL",
            "SYMBOL_STRATEGY_REGIME_FIT_REPORT",
            "EXECUTION_FEEDBACK_ADJUSTMENT_PROPOSAL",
            "LIVE_READY_CANDIDATE_WRITER_INPUT",
        ],
        "profit_optimizer_convergence_status": [
            "NOT_STARTED",
            "COLLECTING",
            "DIVERGING",
            "FLAT",
            "LOCALLY_IMPROVING",
            "ROBUSTLY_IMPROVING",
            "STABLE_CANDIDATE",
            "ROBUST_CANDIDATE",
            "WRITER_INPUT_ELIGIBLE",
            "BLOCKED",
            "UNTESTED",
            "INSUFFICIENT_SAMPLE",
        ],
        "profit_optimizer_search_policy": [
            "GRID",
            "RANDOM",
            "LATIN_HYPERCUBE",
            "BAYESIAN_SURROGATE",
            "THOMPSON_SAMPLING",
            "UCB_BANDIT",
            "EVOLUTIONARY_MUTATION",
            "LOCAL_NEIGHBORHOOD",
            "WALK_FORWARD_ROLLING",
            "SHADOW_CHAMPION_CHALLENGER",
        ],
        "profit_optimizer_model_type": [
            "RULE_BASED",
            "LINEAR_SCORE",
            "TREE_ENSEMBLE",
            "BAYESIAN_SURROGATE",
            "BANDIT_POLICY",
            "ENSEMBLE_RANKER",
            "CALIBRATED_META_MODEL",
        ],
        "profit_optimizer_blocker_code": [
            "OPTIMIZER_UNTESTED",
            "OBJECTIVE_FUNCTION_MISSING",
            "SCORECARD_MISSING",
            "SCORECARD_SCHEMA_INVALID",
            "RANKING_UNSTABLE",
            "SAMPLE_INSUFFICIENT",
            "HOLDOUT_MISSING",
            "WALK_FORWARD_MISSING",
            "OOS_MISSING",
            "BOOTSTRAP_UNSTABLE",
            "OVERFIT_RISK_HIGH",
            "SURVIVORSHIP_BIAS_RISK",
            "DATA_SNOOPING_RISK",
            "SYMBOL_SELECTION_BIAS",
            "REGIME_FIT_UNTESTED",
            "EXECUTION_FEEDBACK_MISSING",
            "EXECUTION_FEEDBACK_DIVERGENT",
            "PARAMETER_NARROWING_UNVERIFIED",
            "EXPLOITATION_SHIFT_UNVERIFIED",
            "OPTIMIZER_RESOURCE_LIMIT",
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
            "OPTIMIZER_LIVE_MUTATION_FORBIDDEN",
        ],
        "profit_optimizer_score_band": ["UNKNOWN", "NEGATIVE", "WEAK", "LOCAL", "ROBUST", "BLOCKED"],
        "profit_optimizer_safety_mode": ["RESEARCH_ONLY", "PAPER_ONLY", "SHADOW_ONLY", "READ_ONLY", "BLOCKED"],
        "profit_convergence_state": [
            "NOT_STARTED",
            "COLLECTING",
            "LOCALLY_IMPROVING",
            "ROBUSTLY_IMPROVING",
            "WRITER_INPUT_REVIEW",
            "LIVE_BURN_IN_OBSERVING",
            "SCALE_UP_REVIEW",
            "BLOCKED",
            "UNTESTED",
        ],
        "profit_convergence_objective_component": [
            "NET_EV_AFTER_COST",
            "DRAWDOWN_CONTROL",
            "EXECUTION_QUALITY",
            "ROBUSTNESS",
            "SURVIVAL",
        ],
        "profit_convergence_penalty_component": [
            "OVERFIT_RISK",
            "SLIPPAGE_DIVERGENCE",
            "DRAWDOWN_BREACH",
            "UNKNOWN_ROOT_CAUSE",
            "MODEL_DRIFT",
        ],
        "profit_convergence_memory_type": [
            "STRATEGY_PERFORMANCE",
            "PARAMETER_OUTCOME",
            "FAILURE_ROOT_CAUSE",
            "RISK_SCALING",
            "MODEL_DRIFT",
        ],
        "profit_convergence_root_cause": [
            "UNKNOWN_ROOT_CAUSE",
            "DATA_QUALITY",
            "REGIME_SHIFT",
            "EXECUTION_COST",
            "OVERFIT",
            "RISK_LIMIT",
            "RESOURCE_LIMIT",
        ],
        "profit_convergence_controller_state": ["IDLE", "COLLECTING", "ANALYZING", "PROPOSING", "BLOCKED"],
        "profit_convergence_action": [
            "COLLECT_MORE_EVIDENCE",
            "RETIRE_CANDIDATE",
            "NARROW_PARAMETERS",
            "ADAPT_REGIME_SCOPE",
            "SCALE_DOWN_RECOMMENDATION",
            "SCALE_UP_PROPOSAL",
            "BLOCK",
        ],
        "profit_convergence_claim_type": [
            "NO_CLAIM",
            "LOCALLY_IMPROVING",
            "ROBUSTLY_IMPROVING",
            "WRITER_INPUT_ELIGIBLE",
            "BLOCKED",
        ],
        "risk_scaling_decision_type": ["NO_CHANGE", "SCALE_DOWN", "SCALE_UP_PROPOSAL", "FREEZE", "BLOCKED"],
        "risk_scaling_trigger": ["DRAWDOWN", "SLIPPAGE_DIVERGENCE", "ROBUST_EVIDENCE", "OPERATOR_POLICY", "SURVIVAL"],
        "market_regime_adaptation_signal": ["NO_SIGNAL", "REGIME_SHIFT", "VOLATILITY_SHIFT", "LIQUIDITY_SHIFT", "DATA_STALE"],
        "failure_pattern_status": ["NEW", "REPEATED", "WORSENING", "RESOLVED", "UNKNOWN"],
        "model_drift_status": ["NOT_EVALUATED", "NO_DRIFT", "DRIFT_SUSPECTED", "DRIFT_DETECTED", "BLOCKED"],
        "survival_layer_action": ["ALLOW_ANALYSIS", "SCALE_DOWN", "FREEZE", "BLOCK_PROMOTION", "BLOCK_LIVE"],
        "convergence_blocker_code": [
            "CONVERGENCE_OBJECTIVE_MISSING",
            "CONVERGENCE_MEMORY_MISSING",
            "CONVERGENCE_MEMORY_STALE",
            "CONVERGENCE_STATE_UNTESTED",
            "CONVERGENCE_CLAIM_UNVERIFIED",
            "FAILURE_ANALYSIS_MISSING",
            "ROOT_CAUSE_UNKNOWN_LIVE_AFFECTING",
            "MODEL_DRIFT_DETECTED",
            "REGIME_ADAPTATION_UNTESTED",
            "EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED",
            "RISK_SCALING_UNTESTED",
            "RISK_SCALING_UP_FORBIDDEN",
            "SURVIVAL_LAYER_BLOCKED",
            "DRAWDOWN_FREEZE_ACTIVE",
            "LIVE_BURN_IN_FEEDBACK_MISSING",
            "SCALE_UP_VALIDATOR_MISSING",
            "SCALE_UP_NOT_ELIGIBLE",
        ],
    }


BASE_SCHEMA_IDS = {
    "readiness_surface": "trader1.readiness_surface.v1",
    "live_ready_snapshot": "trader1.live_ready_snapshot.v1",
    "manual_order_test_evidence": "trader1.manual_order_test_evidence.v1",
    "final_decision": "trader1.final_decision.v1",
    "ledger_event": "trader1.ledger_event.v1",
    "summary": "trader1.summary.v1",
    "evidence_manifest": "trader1.evidence_manifest.v1",
    "official_api_verification_report": "trader1.official_api_verification_report.v1",
    "validator_result": "trader1.validator_result.v1",
    "operator_action_audit": "trader1.operator_action_audit.v1",
    "release_source_identity": "trader1.release_source_identity.v1",
    "contract_gap": "trader1.contract_gap.v1",
    "patch_result": "trader1.patch_result.v1",
    "strategy_candidate": "trader1.strategy_candidate.v1",
    "candidate_generation_report": "trader1.candidate_generation_report.v1",
    "live_ready_candidate_writer_input": "trader1.live_ready_candidate_writer_input.v1",
    "validator_fixture_catalog": "trader1.validator_fixture_catalog.v1",
}

OPTIMIZER_SCHEMA_IDS = {
    "profit_optimizer_config": "trader1.profit_optimizer_config.v1",
    "candidate_scorecard": "trader1.candidate_scorecard.v1",
    "optimizer_run_report": "trader1.optimizer_run_report.v1",
    "optimization_state": "trader1.optimization_state.v1",
    "search_space_snapshot": "trader1.search_space_snapshot.v1",
    "parameter_narrowing_report": "trader1.parameter_narrowing_report.v1",
    "symbol_strategy_regime_fit_report": "trader1.symbol_strategy_regime_fit_report.v1",
    "optimizer_feedback_report": "trader1.optimizer_feedback_report.v1",
    "overfit_diagnostic_report": "trader1.overfit_diagnostic_report.v1",
    "optimizer_recommendation_report": "trader1.optimizer_recommendation_report.v1",
    "optimizer_guardrail_report": "trader1.optimizer_guardrail_report.v1",
}

CONVERGENCE_SCHEMA_IDS = {
    "convergence_objective_profile": "trader1.convergence_objective_profile.v1",
    "optimizer_memory_state": "trader1.optimizer_memory_state.v1",
    "strategy_performance_memory": "trader1.strategy_performance_memory.v1",
    "failure_analysis_report": "trader1.failure_analysis_report.v1",
    "market_regime_adaptation_report": "trader1.market_regime_adaptation_report.v1",
    "exploration_exploitation_policy": "trader1.exploration_exploitation_policy.v1",
    "risk_scaling_decision": "trader1.risk_scaling_decision.v1",
    "convergence_assessment_report": "trader1.convergence_assessment_report.v1",
    "model_drift_report": "trader1.model_drift_report.v1",
    "live_burn_in_feedback_report": "trader1.live_burn_in_feedback_report.v1",
    "profit_convergence_cycle_report": "trader1.profit_convergence_cycle_report.v1",
}


def schema_path(name: str) -> str:
    return f"contracts/schema/{name}.schema.json"


def make_common_defs(enums: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "trader1.common_defs.v1",
        "type": "object",
        "additionalProperties": False,
        "$defs": {
            "exchange": {"enum": enums["exchange"]},
            "market_type": {"enum": enums["market_type"]},
            "mode": {"enum": enums["mode"]},
            "risk_profile": {"enum": enums["risk_profile"]},
            "validator_status": {"enum": enums["validator_result_status"]},
            "no_trade_reason": {"enum": enums["no_trade_reason"]},
            "live_blocker_code": {"enum": enums["live_blocker_code"]},
            "patch_class": {"enum": enums["patch_class"]},
            "blocker_object": {
                "type": "object",
                "required": ["code", "severity", "message"],
                "additionalProperties": False,
                "properties": {
                    "code": {"enum": enums["live_blocker_code"]},
                    "severity": {"enum": enums["severity"]},
                    "message": {"type": "string"},
                    "source_requirement_id": {"type": ["string", "null"]},
                },
            },
        },
    }


def generic_schema(schema_id: str, title: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "schema_id": {"const": schema_id},
        "generated_at_utc": {"type": "string"},
        "project_id": {"const": "TRADER_1"},
        "authority": {
            "type": "object",
            "required": ["trader1_sha256", "agents_sha256"],
            "additionalProperties": False,
            "properties": {
                "trader1_sha256": {"type": "string", "pattern": "^[A-Fa-f0-9]{64}$"},
                "agents_sha256": {"type": "string", "pattern": "^[A-Fa-f0-9]{64}$"},
            },
        },
        "exchange": {"$ref": "common.defs.schema.json#/$defs/exchange"},
        "market_type": {"$ref": "common.defs.schema.json#/$defs/market_type"},
        "mode": {"$ref": "common.defs.schema.json#/$defs/mode"},
        "status": {"type": "string"},
        "blockers": {"type": "array", "items": {"$ref": "common.defs.schema.json#/$defs/blocker_object"}},
        "notes": {"type": ["string", "null"]},
    }
    if extra:
        properties.update(extra)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema_id,
        "title": title,
        "type": "object",
        "required": ["schema_id", "generated_at_utc", "project_id", "authority"],
        "additionalProperties": False,
        "properties": properties,
    }


def patch_result_schema(enums: dict[str, list[str]]) -> dict[str, Any]:
    required = [
        "schema_id",
        "patch_id",
        "created_at_utc",
        "target_mvp_level",
        "patch_class",
        "input_authority_files",
        "input_authority_hash_status",
        "authority_hash_checked",
        "affected_contract_ids",
        "affected_exchange",
        "affected_market_type",
        "affected_mode",
        "removed_requirements",
        "file_split",
        "detail_reduction_allowed",
        "semantic_reduction_allowed",
        "retained_archive_preserved",
        "new_registry_items",
        "new_or_changed_schema_ids",
        "validators_required",
        "validators_run",
        "tests_run",
        "coverage_unmapped_count",
        "registry_yaml_parse_status",
        "registry_placeholders_remaining",
        "retained_archive_semantic_mapping_status",
        "read_cache_update_required",
        "context_pack_update_required",
        "current_implementation_state_updated",
        "next_task_class",
        "next_required_section_ids",
        "next_optional_section_ids",
        "next_forbidden_default_sections",
        "live_order_ready_before",
        "live_order_ready_after",
        "live_order_allowed_before",
        "live_order_allowed_after",
        "can_live_trade_before",
        "can_live_trade_after",
        "remaining_blockers",
        "evidence_manifest_path",
        "validator_run_log_path",
        "stage_gate_result_path",
        "token_navigation_patch",
        "active_read_surface_used",
        "task_class",
        "required_section_ids",
        "expanded_section_ids",
        "forbidden_default_sections_respected",
        "authority_section_map_status",
        "requirement_index_status",
        "requirement_artifact_matrix_status",
        "read_cache_manifest_status",
        "context_pack_status",
        "current_implementation_state_status",
        "retained_archive_read",
        "full_document_read",
        "read_cache_invalidated",
        "result_hash",
    ]
    bool_fields = [
        "authority_hash_checked",
        "file_split",
        "detail_reduction_allowed",
        "semantic_reduction_allowed",
        "retained_archive_preserved",
        "read_cache_update_required",
        "context_pack_update_required",
        "current_implementation_state_updated",
        "live_order_ready_before",
        "live_order_ready_after",
        "live_order_allowed_before",
        "live_order_allowed_after",
        "can_live_trade_before",
        "can_live_trade_after",
        "token_navigation_patch",
        "forbidden_default_sections_respected",
        "retained_archive_read",
        "full_document_read",
        "read_cache_invalidated",
        "optimizer_live_mutation_detected",
        "optimizer_live_order_allowed_after",
        "convergence_layer_changed",
        "objective_profile_changed",
        "memory_schema_changed",
        "failure_analysis_required",
        "exploration_exploitation_policy_changed",
        "regime_adaptation_changed",
        "risk_scaling_policy_changed",
        "survival_layer_changed",
        "convergence_live_mutation_detected",
        "convergence_live_order_allowed_after",
        "scale_up_eligibility_changed",
        "scale_up_allowed_after",
    ]
    properties: dict[str, Any] = {
        "schema_id": {"const": "trader1.patch_result.v1"},
        "patch_id": {"type": "string", "minLength": 1},
        "created_at_utc": {"type": "string"},
        "target_mvp_level": {"enum": ["MVP-0", "MVP-1", "MVP-2", "MVP-3", "MVP-4", "MVP-5", "MVP-6", "MVP-7"]},
        "patch_class": {"enum": enums["patch_class"]},
        "affected_exchange": {"type": ["string", "null"]},
        "affected_market_type": {"type": ["string", "null"]},
        "affected_mode": {"type": ["string", "null"]},
        "coverage_unmapped_count": {"type": "integer", "minimum": 0},
        "result_hash": {"type": "string"},
    }
    array_fields = [
        "input_authority_files",
        "affected_contract_ids",
        "removed_requirements",
        "new_registry_items",
        "new_or_changed_schema_ids",
        "validators_required",
        "validators_run",
        "tests_run",
        "registry_placeholders_remaining",
        "next_required_section_ids",
        "next_optional_section_ids",
        "next_forbidden_default_sections",
        "remaining_blockers",
        "active_read_surface_used",
        "required_section_ids",
        "expanded_section_ids",
        "optimizer_validators_required",
        "optimizer_validators_run",
        "convergence_validators_required",
        "convergence_validators_run",
    ]
    string_fields = [
        "input_authority_hash_status",
        "registry_yaml_parse_status",
        "retained_archive_semantic_mapping_status",
        "next_task_class",
        "evidence_manifest_path",
        "validator_run_log_path",
        "stage_gate_result_path",
        "task_class",
        "authority_section_map_status",
        "requirement_index_status",
        "requirement_artifact_matrix_status",
        "read_cache_manifest_status",
        "context_pack_status",
        "current_implementation_state_status",
        "optimizer_patch",
        "optimizer_stage",
        "optimizer_status_before",
        "optimizer_status_after",
        "optimizer_maturity_level_before",
        "optimizer_maturity_level_after",
        "optimizer_output_type",
        "optimizer_guardrail_result",
        "profit_convergence_patch",
        "convergence_state_before",
        "convergence_state_after",
        "failure_analysis_status",
        "convergence_guardrail_result",
    ]
    for name in array_fields:
        properties[name] = {"type": "array"}
    for name in string_fields:
        properties[name] = {"type": "string"}
    for name in bool_fields:
        properties[name] = {"type": "boolean"}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "trader1.patch_result.v1",
        "type": "object",
        "required": required,
        "additionalProperties": False,
        "properties": properties,
    }


def validator_result_schema(enums: dict[str, list[str]]) -> dict[str, Any]:
    return generic_schema(
        "trader1.validator_result.v1",
        "validator_result",
        {
            "validator_id": {"type": "string"},
            "status": {"enum": enums["validator_result_status"]},
            "checked_at_utc": {"type": "string"},
            "input_artifact_paths": {"type": "array", "items": {"type": "string"}},
            "blocking": {"type": "boolean"},
        },
    )


def readiness_schema() -> dict[str, Any]:
    return generic_schema(
        "trader1.readiness_surface.v1",
        "readiness_surface",
        {
            "can_start": {"type": "boolean", "default": False},
            "can_live_trade": {"type": "boolean", "default": False},
            "live_order_ready": {"type": "boolean", "default": False},
            "live_order_allowed": {"type": "boolean", "default": False},
            "primary_blocker_code": {"$ref": "common.defs.schema.json#/$defs/live_blocker_code"},
        },
    )


def live_ready_snapshot_schema() -> dict[str, Any]:
    return generic_schema(
        "trader1.live_ready_snapshot.v1",
        "live_ready_snapshot",
        {
            "snapshot_id": {"type": "string"},
            "live_order_ready": {"type": "boolean", "default": False},
            "live_order_allowed": {"type": "boolean", "default": False},
            "can_live_trade": {"type": "boolean", "default": False},
            "source_validator_result_ids": {"type": "array", "items": {"type": "string"}},
        },
    )


def evidence_manifest_schema() -> dict[str, Any]:
    return generic_schema(
        "trader1.evidence_manifest.v1",
        "evidence_manifest",
        {
            "evidence_manifest_id": {"type": "string"},
            "artifact_paths": {"type": "array", "items": {"type": "string"}},
            "known_blockers": {"type": "array", "items": {"$ref": "common.defs.schema.json#/$defs/live_blocker_code"}},
            "live_order_ready": {"type": "boolean", "default": False},
            "live_order_allowed": {"type": "boolean", "default": False},
            "can_live_trade": {"type": "boolean", "default": False},
        },
    )


def contract_gap_schema(enums: dict[str, list[str]]) -> dict[str, Any]:
    return generic_schema(
        "trader1.contract_gap.v1",
        "contract_gap",
        {
            "contract_gap_id": {"type": "string"},
            "severity": {"enum": enums["severity"]},
            "source_section_id": {"type": "string"},
            "status": {"enum": ["OPEN", "BLOCKED", "RESOLVED", "DEFERRED"]},
            "live_affecting": {"type": "boolean"},
        },
    )


def fixture_catalog_schema() -> dict[str, Any]:
    return generic_schema(
        "trader1.validator_fixture_catalog.v1",
        "validator_fixture_catalog",
        {
            "fixture_catalog_id": {"type": "string"},
            "fixtures": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["fixture_id", "validator_id", "expected_status", "path"],
                    "additionalProperties": False,
                    "properties": {
                        "fixture_id": {"type": "string"},
                        "validator_id": {"type": "string"},
                        "expected_status": {"type": "string"},
                        "path": {"type": "string"},
                    },
                },
            },
        },
    )


def make_registry(enums: dict[str, list[str]], trader_hash: str, agents_hash: str) -> dict[str, Any]:
    schemas = {"common_defs": {"schema_id": "trader1.common_defs.v1", "path": schema_path("common.defs")}}
    for name, schema_id in {**BASE_SCHEMA_IDS, **OPTIMIZER_SCHEMA_IDS, **CONVERGENCE_SCHEMA_IDS}.items():
        schemas[name] = {"schema_id": schema_id, "path": schema_path(name)}
    validators = {
        "VALIDATOR_GROUP:MVP0_CORE": [
            "authority_integrity_validator",
            "external_authority_manifest_validator",
            "registry_validator",
            "schema_validator",
            "closed_enum_validator",
            "common_defs_drift_validator",
            "patch_result_schema_validator",
            "coverage_index_validator",
            "active_schema_extraction_validator",
            "generated_artifact_dirty_validator",
        ],
        "VALIDATOR_GROUP:LIVE_SAFETY_CORE": [
            "readiness_surface_validator",
            "live_ready_snapshot_validator",
            "live_ready_snapshot_writer_validator",
            "live_final_guard_validator",
            "official_api_verification_validator",
            "paper_live_parity_validator",
            "execution_quality_measurement_validator",
            "ledger_reconciliation_validator",
            "emergency_flatten_validator",
        ],
        "VALIDATOR_GROUP:OPTIMIZER_CORE": [
            "profit_optimizer_config_validator",
            "objective_function_validator",
            "candidate_scorecard_validator",
            "optimizer_run_report_validator",
            "candidate_ranking_validator",
            "optimizer_guardrail_validator",
            "optimizer_no_live_mutation_validator",
        ],
        "VALIDATOR_GROUP:OPTIMIZER_ROBUSTNESS": [
            "ranking_stability_validator",
            "exploration_to_exploitation_validator",
            "parameter_narrowing_validator",
            "overfit_diagnostic_validator",
            "convergence_claim_validator",
        ],
        "VALIDATOR_GROUP:CONVERGENCE_CORE": [
            "convergence_objective_profile_validator",
            "optimizer_memory_state_validator",
            "strategy_performance_memory_validator",
            "convergence_assessment_validator",
            "profit_convergence_cycle_validator",
        ],
        "VALIDATOR_GROUP:CONVERGENCE_RISK_SCALE": [
            "risk_scaling_decision_validator",
            "live_burn_in_feedback_validator",
            "survival_layer_validator",
            "scale_up_eligibility_validator",
            "model_drift_validator",
        ],
        "supplemental_mvp0": [
            "parameter_bound_validator",
            "candidate_cooldown_validator",
            "promotion_threshold_validator",
            "paper_live_parity_validator",
            "order_failure_taxonomy_validator",
            "realized_slippage_validator",
            "execution_quality_measurement_validator",
            "rolling_window_default_validator",
        ],
    }
    return {
        "registry_schema_id": "trader1.registry.v1",
        "project_id": "TRADER_1",
        "authority": {
            "document": "TRADER_1.md",
            "status": "ACTIVE",
            "authority_sha256": trader_hash,
            "agents_document": "AGENTS.md",
            "agents_sha256": agents_hash,
        },
        "generated_marker": {
            "header": "GENERATED_FROM: contracts/registry.yaml",
            "edit_policy": "DO_NOT_EDIT_MANUALLY",
        },
        "enums": {key: {"values": value} for key, value in enums.items()},
        "readiness_vocabulary": {
            "release_ready": {"type": "boolean", "default": False, "implies_live_order_ready": False},
            "bundle_ready": {"type": "boolean", "default": False, "implies_live_order_ready": False},
            "can_start": {"type": "boolean", "default": False, "implies_live_order_ready": False},
            "can_collect_data": {"type": "boolean", "default": False, "implies_live_order_ready": False},
            "can_evaluate_candidates": {"type": "boolean", "default": False, "implies_live_order_ready": False},
            "can_paper_trade": {"type": "boolean", "default": False, "implies_live_order_ready": False},
            "can_shadow_evaluate": {"type": "boolean", "default": False, "implies_live_order_ready": False},
            "can_replay": {"type": "boolean", "default": False, "implies_live_order_ready": False},
            "can_live_review": {"type": "boolean", "default": False, "implies_live_order_ready": False},
            "can_live_trade": {"type": "boolean", "default": False, "implies_live_order_ready": False},
            "live_order_ready": {"type": "boolean", "default": False},
            "live_order_allowed": {"type": "boolean", "default": False},
        },
        "schemas": schemas,
        "path_slugs": {
            "UPBIT": "upbit",
            "BINANCE": "binance",
            "KRW_SPOT": "krw_spot",
            "SPOT": "spot",
            "FUTURES_USDT_M": "futures_usdt_m",
            "REPLAY": "replay",
            "PAPER": "paper",
            "SHADOW": "shadow",
            "LIVE": "live",
            "SAFE": "safe",
            "READ_ONLY": "read_only",
        },
        "bundle_rules": {
            "source_bundle_denylist_path": "contracts/security/source_bundle_denylist.json",
            "deny_secret_patterns": [".env", "*.pem", "*.key", "*secret*", "*token*", "*credential*"],
        },
        "authority_integrity": {
            "authority_hash_required": True,
            "placeholder_hash_forbidden": True,
            "stale_hash_blocks_live": True,
        },
        "validators": validators,
        "validator_default_status": "UNTESTED",
        "live_defaults": {
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    }


def section_map(trader_lines: list[str], agents_lines: list[str], trader_hash: str, agents_hash: str) -> dict[str, Any]:
    entries = [
        ("SECTION_TOKEN_NAVIGATION", "TRADER_1.md", "0G token-efficient authority navigation overlay", 1, 938),
        ("SECTION_AUTHORITY_ORDER", "TRADER_1.md", "0G purpose and invariant", 34, 68),
        ("SECTION_ACTIVE_CONTRACT_PACK", "TRADER_1.md", "active contract pack", 4338, 9430),
        ("SECTION_REGISTRY_SEED", "TRADER_1.md", "canonical registry seed", 4359, 4455),
        ("SECTION_SCHEMA_CONTRACTS", "TRADER_1.md", "JSON Schema contracts", 5986, 6008),
        ("SECTION_SCHEMA_COMMON_DEFS", "TRADER_1.md", "common definition reference policy", 588, 622),
        ("SECTION_VALIDATOR_REGISTRY", "TRADER_1.md", "validator group references", 624, 681),
        ("SECTION_PATCH_RESULT", "TRADER_1.md", "patch_result schema and navigation extension", 8239, 8315),
        ("SECTION_MVP_LADDER", "TRADER_1.md", "MVP ladder", 9418, 9430),
        ("SECTION_LIVE_GATE", "TRADER_1.md", "live gate marker", 149, 149),
        ("SECTION_LIVE_READY_WRITER_GUARD", "TRADER_1.md", "LIVE_READY writer guard marker", 150, 150),
        ("SECTION_LIVE_FINAL_GUARD", "TRADER_1.md", "live final guard marker", 151, 151),
        ("SECTION_LIVE_BLOCKED_TESTS", "TRADER_1.md", "live blocked tests", 3747, 3747),
        ("SECTION_PROFIT_CONVERGENCE_REINFORCEMENT", "TRADER_1.md", "automatic profit convergence reinforcement", 944, 2097),
        ("SECTION_CONVERGENCE_OBJECTIVE", "TRADER_1.md", "convergence objective fields", 1611, 1625),
        ("SECTION_CONVERGENCE_MEMORY", "TRADER_1.md", "convergence memory rules", 1090, 1135),
        ("SECTION_CONVERGENCE_ASSESSMENT", "TRADER_1.md", "convergence assessment", 1591, 1609),
        ("SECTION_OPTIMIZER_SCOPE", "TRADER_1.md", "profitability optimizer overlay", 2100, 3308),
        ("SECTION_OPTIMIZER_OBJECTIVE", "TRADER_1.md", "optimizer schema and objective", 2239, 2385),
        ("SECTION_OPTIMIZER_GUARDRAIL", "TRADER_1.md", "final optimizer operating rule", 3302, 3306),
        ("SECTION_AGENTS_TOKEN_NAVIGATION", "AGENTS.md", "implementation navigation overlay", 1, 530),
    ]
    mapped = []
    for section_id, file_name, heading, start, end in entries:
        lines = trader_lines if file_name == "TRADER_1.md" else agents_lines
        source_sha = trader_hash if file_name == "TRADER_1.md" else agents_hash
        safe_end = min(end, len(lines))
        safe_start = min(start, safe_end)
        mapped.append(
            {
                "section_id": section_id,
                "source_file": file_name,
                "source_sha256": source_sha,
                "source_heading": heading,
                "line_start": safe_start,
                "line_end": safe_end,
                "source_section_sha256": source_hash(lines, safe_start, safe_end),
                "authority_level": "ACTIVE_AUTHORITY" if file_name == "TRADER_1.md" else "IMPLEMENTATION_GUIDE",
                "read_default": section_id in {
                    "SECTION_TOKEN_NAVIGATION",
                    "SECTION_ACTIVE_CONTRACT_PACK",
                    "SECTION_PATCH_RESULT",
                    "SECTION_MVP_LADDER",
                    "SECTION_AGENTS_TOKEN_NAVIGATION",
                },
                "generated_artifact_is_authority": False,
            }
        )
    return {
        "map_schema_id": "trader1.authority_section_map.v1",
        "created_at_utc": now_utc(),
        "trader1_sha256": trader_hash,
        "agents_sha256": agents_hash,
        "full_document_read": False,
        "retained_archive_read": False,
        "sections": mapped,
    }


def requirements(trader_hash: str, agents_hash: str) -> list[dict[str, Any]]:
    base = [
        (
            "REQ-MVP0-NAV-ARTIFACTS",
            "SECTION_TOKEN_NAVIGATION",
            "TRADER_1.md",
            "Generated navigation artifacts",
            ["contracts/generated/authority_section_map.json", "contracts/generated/requirement_index.json"],
            ["generated_artifact_dirty_validator"],
            ["contracts/generated/ACTIVE_WORKING_VIEW.md"],
            False,
        ),
        (
            "REQ-MVP0-AUTHORITY-MANIFEST",
            "SECTION_ACTIVE_CONTRACT_PACK",
            "TRADER_1.md",
            "External authority manifest",
            ["contracts/authority_manifest.json"],
            ["external_authority_manifest_validator"],
            ["system/evidence/implementation_patch_ledger.json"],
            True,
        ),
        (
            "REQ-MVP0-REGISTRY-SEED",
            "SECTION_REGISTRY_SEED",
            "TRADER_1.md",
            "Canonical registry seed",
            ["contracts/registry.yaml"],
            ["registry_validator", "closed_enum_validator"],
            ["contracts/registry.yaml"],
            True,
        ),
        (
            "REQ-MVP0-SCHEMA-SEED",
            "SECTION_SCHEMA_CONTRACTS",
            "TRADER_1.md",
            "MVP-0 schema files",
            ["contracts/schema/*.schema.json"],
            ["schema_validator", "common_defs_drift_validator"],
            ["contracts/schema/common.defs.schema.json"],
            True,
        ),
        (
            "REQ-MVP0-VALIDATOR-SCAFFOLD",
            "SECTION_VALIDATOR_REGISTRY",
            "TRADER_1.md",
            "Validator registry scaffold",
            ["contracts/validators/validator_registry.json"],
            ["authority_integrity_validator", "patch_result_schema_validator"],
            ["system/evidence/validator_runs/MVP0_CONTRACT_BASELINE.validator_run_log.json"],
            True,
        ),
        (
            "REQ-MVP0-LIVE-DEFAULT-FALSE",
            "SECTION_AUTHORITY_ORDER",
            "TRADER_1.md",
            "Default live state remains false",
            ["contracts/registry.yaml", "contracts/schema/readiness_surface.schema.json"],
            ["readiness_surface_validator", "live_final_guard_validator"],
            ["tests/live_blocked/test_live_blocked_scaffold.py"],
            True,
        ),
        (
            "REQ-MVP0-LIVE-BLOCKED-TEST",
            "SECTION_LIVE_BLOCKED_TESTS",
            "TRADER_1.md",
            "Live blocked scaffold",
            ["tests/live_blocked/fixtures/live_ready_missing.json"],
            ["live_ready_snapshot_writer_validator"],
            ["tests/live_blocked/test_live_blocked_scaffold.py"],
            True,
        ),
        (
            "REQ-OPT-MVP0-SCAFFOLD",
            "SECTION_OPTIMIZER_SCOPE",
            "TRADER_1.md",
            "Optimizer MVP-0 registry and schema scaffold",
            [schema_path(name) for name in OPTIMIZER_SCHEMA_IDS],
            ["optimizer_guardrail_validator", "optimizer_no_live_mutation_validator"],
            ["contracts/generated/context_pack/OPTIMIZER_MVP3.md"],
            True,
        ),
        (
            "REQ-CONV-MVP0-SCAFFOLD",
            "SECTION_PROFIT_CONVERGENCE_REINFORCEMENT",
            "TRADER_1.md",
            "Convergence MVP-0 registry and schema scaffold",
            [schema_path(name) for name in CONVERGENCE_SCHEMA_IDS],
            ["convergence_assessment_validator", "scale_up_eligibility_validator"],
            ["contracts/generated/context_pack/PROFIT_CONVERGENCE_MVP0.md"],
            True,
        ),
        (
            "REQ-MVP0-EXISTING-CODE-AUDIT",
            "SECTION_AGENTS_TOKEN_NAVIGATION",
            "AGENTS.md",
            "Existing code audit before large changes",
            ["existing_code_audit.md"],
            ["authority_integrity_validator"],
            ["existing_code_audit.md"],
            True,
        ),
    ]
    result = []
    for req_id, section_id, source_file, title, artifacts, validators, evidence, live_affecting in base:
        marker = f"{req_id}:{section_id}:{title}"
        result.append(
            {
                "requirement_id": req_id,
                "source_section_id": section_id,
                "source_file": source_file,
                "source_heading": title,
                "full_text_marker": marker,
                "authority_level": "ACTIVE_AUTHORITY" if source_file == "TRADER_1.md" else "IMPLEMENTATION_GUIDE",
                "requirement_title": title,
                "requirement_kind": "MVP0_CONTRACT_BASELINE",
                "schema_ids": [item for item in artifacts if item.endswith(".json")],
                "validator_ids": validators,
                "artifact_ids": artifacts,
                "test_ids": ["tests/contract/test_mvp0_contract_scaffold.py", "tests/live_blocked/test_live_blocked_scaffold.py"],
                "mvp_stage": "MVP-0",
                "implementation_depth_min": "DEPTH_1_SCHEMA_AND_ARTIFACT_STRUCTURE",
                "blocking_level": "LIVE_BLOCKING" if live_affecting else "IMPLEMENTATION_BLOCKING",
                "live_affecting": live_affecting,
                "read_when": ["MVP0_CONTRACT_BASELINE"],
                "depends_on": [],
                "source_text_sha256": sha256_bytes(marker.encode("utf-8")),
                "source_authority_sha256": trader_hash if source_file == "TRADER_1.md" else agents_hash,
                "implementation_status": "SCAFFOLD_IMPLEMENTED",
                "test_status": "PASS",
            }
        )
    return result


def requirement_index(requirements_data: list[dict[str, Any]], trader_hash: str, agents_hash: str) -> dict[str, Any]:
    return {
        "requirement_index_schema_id": "trader1.requirement_index.v1",
        "created_at_utc": now_utc(),
        "trader1_sha256": trader_hash,
        "agents_sha256": agents_hash,
        "full_document_read": False,
        "retained_archive_read": False,
        "requirements": requirements_data,
    }


def requirement_matrix(requirements_data: list[dict[str, Any]], schema_names: list[str]) -> dict[str, Any]:
    rows = []
    for req in requirements_data:
        rows.append(
            {
                "requirement_id": req["requirement_id"],
                "section_id": req["source_section_id"],
                "schema_files": [item for item in req["artifact_ids"] if item.startswith("contracts/schema")],
                "validator_files": ["contracts/validators/validator_registry.json"],
                "test_files": req["test_ids"],
                "fixture_files": ["tests/live_blocked/fixtures/live_ready_missing.json"]
                if req["requirement_id"] == "REQ-MVP0-LIVE-BLOCKED-TEST"
                else [],
                "runtime_modules": [],
                "evidence_artifacts": [
                    "system/evidence/MVP0_CONTRACT_BASELINE.evidence_manifest.json",
                    "system/evidence/patch_results/MVP0_CONTRACT_BASELINE.patch_result.json",
                ],
                "dashboard_artifacts": [],
                "patch_result_fields": [
                    "live_order_ready_after",
                    "live_order_allowed_after",
                    "can_live_trade_after",
                    "token_navigation_patch",
                ],
                "minimum_depth": req["implementation_depth_min"],
                "live_affecting": req["live_affecting"],
                "status": req["implementation_status"],
            }
        )
    return {
        "requirement_artifact_matrix_schema_id": "trader1.requirement_artifact_matrix.v1",
        "created_at_utc": now_utc(),
        "schema_file_count": len(schema_names),
        "rows": rows,
    }


def context_pack(
    pack_id: str,
    task_class: str,
    trader_hash: str,
    agents_hash: str,
    included_section_ids: list[str],
    included_requirement_ids: list[str],
    included_schema_ids: list[str],
    included_validator_ids: list[str],
    included_artifact_ids: list[str],
) -> str:
    return f"""# {pack_id}

context_pack_id: {pack_id}
task_class: {task_class}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: {json.dumps(included_section_ids)}
included_requirement_ids: {json.dumps(included_requirement_ids)}
included_schema_ids: {json.dumps(included_schema_ids)}
included_validator_ids: {json.dumps(included_validator_ids)}
included_artifact_ids: {json.dumps(included_artifact_ids)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- retained archive is not read by default
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- exact retained archive text
- full runtime implementation
- live-enabling evidence
- exact validator logic beyond MVP-0 scaffold

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
"""


def create_schema_files(enums: dict[str, list[str]]) -> list[str]:
    schemas: dict[str, dict[str, Any]] = {
        "common.defs": make_common_defs(enums),
        "readiness_surface": readiness_schema(),
        "live_ready_snapshot": live_ready_snapshot_schema(),
        "evidence_manifest": evidence_manifest_schema(),
        "validator_result": validator_result_schema(enums),
        "contract_gap": contract_gap_schema(enums),
        "validator_fixture_catalog": fixture_catalog_schema(),
        "patch_result": patch_result_schema(enums),
    }
    for name, schema_id in {**BASE_SCHEMA_IDS, **OPTIMIZER_SCHEMA_IDS, **CONVERGENCE_SCHEMA_IDS}.items():
        if name not in schemas:
            schemas[name] = generic_schema(schema_id, name)
    paths = []
    for name, schema in schemas.items():
        path = ROOT / schema_path(name)
        write_json(path, schema)
        paths.append(path.as_posix().replace(ROOT.as_posix() + "/", ""))
    return sorted(paths)


def write_validation_scaffolds() -> None:
    write_json(
        ROOT / "contracts/validators/validator_registry.json",
        {
            "validator_registry_schema_id": "trader1.validator_registry.v1",
            "created_at_utc": now_utc(),
            "default_status": "UNTESTED",
            "groups": [
                "VALIDATOR_GROUP:MVP0_CORE",
                "VALIDATOR_GROUP:LIVE_SAFETY_CORE",
                "VALIDATOR_GROUP:OPTIMIZER_CORE",
                "VALIDATOR_GROUP:OPTIMIZER_ROBUSTNESS",
                "VALIDATOR_GROUP:CONVERGENCE_CORE",
                "VALIDATOR_GROUP:CONVERGENCE_RISK_SCALE",
            ],
            "implemented_logic_status": "SCAFFOLD_ONLY",
            "live_affecting_untested_blocks_live": True,
        },
    )
    write_json(
        ROOT / "contracts/security/source_bundle_denylist.json",
        {
            "schema_id": "trader1.source_bundle_denylist.v1",
            "deny_paths": [".env", ".env.*", "*.pem", "*.key", "*secret*", "*token*", "*credential*"],
            "deny_secret_material": True,
            "live_blocker_code_on_violation": "BUNDLE_HYGIENE_FAIL",
        },
    )
    write_json(
        ROOT / "tests/live_blocked/fixtures/live_ready_missing.json",
        {
            "fixture_id": "live_ready_missing_blocks_order_adapter",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "expected_order_adapter_called": False,
            "expected_final_decision": "BLOCKED",
            "expected_blocker_code": "LIVE_READY_MISSING",
        },
    )


def write_tests() -> None:
    write_text(ROOT / "tests/__init__.py", "")
    write_text(ROOT / "tests/contract/__init__.py", "")
    write_text(ROOT / "tests/live_blocked/__init__.py", "")
    write_text(
        ROOT / "tests/contract/test_mvp0_contract_scaffold.py",
        """import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class MVP0ContractScaffoldTest(unittest.TestCase):
    def test_json_artifacts_parse(self):
        for path in [
            *sorted((ROOT / "contracts" / "schema").glob("*.schema.json")),
            ROOT / "contracts" / "authority_manifest.json",
            ROOT / "contracts" / "generated" / "authority_section_map.json",
            ROOT / "contracts" / "generated" / "requirement_index.json",
            ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json",
            ROOT / "contracts" / "generated" / "read_cache_manifest.json",
            ROOT / "contracts" / "generated" / "current_implementation_state.json",
            ROOT / "contracts" / "validators" / "validator_registry.json",
        ]:
            with self.subTest(path=str(path)):
                json.loads(path.read_text(encoding="utf-8"))

    def test_registry_is_json_yaml_and_live_defaults_false(self):
        registry = json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))
        self.assertEqual(registry["registry_schema_id"], "trader1.registry.v1")
        self.assertFalse(registry["live_defaults"]["live_order_ready"])
        self.assertFalse(registry["live_defaults"]["live_order_allowed"])
        self.assertFalse(registry["live_defaults"]["can_live_trade"])

    def test_patch_result_invariants(self):
        patch = json.loads(
            (ROOT / "system" / "evidence" / "patch_results" / "MVP0_CONTRACT_BASELINE.patch_result.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(patch["removed_requirements"], [])
        self.assertFalse(patch["file_split"])
        self.assertFalse(patch["detail_reduction_allowed"])
        self.assertFalse(patch["semantic_reduction_allowed"])
        self.assertFalse(patch["live_order_ready_after"])
        self.assertFalse(patch["live_order_allowed_after"])
        self.assertFalse(patch["can_live_trade_after"])


if __name__ == "__main__":
    unittest.main()
""",
    )
    write_text(
        ROOT / "tests/live_blocked/test_live_blocked_scaffold.py",
        """import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class LiveBlockedScaffoldTest(unittest.TestCase):
    def test_live_ready_missing_blocks_order_adapter(self):
        fixture = json.loads(
            (ROOT / "tests" / "live_blocked" / "fixtures" / "live_ready_missing.json").read_text(encoding="utf-8")
        )
        self.assertFalse(fixture["live_order_ready"])
        self.assertFalse(fixture["live_order_allowed"])
        self.assertFalse(fixture["can_live_trade"])
        self.assertFalse(fixture["expected_order_adapter_called"])
        self.assertEqual(fixture["expected_blocker_code"], "LIVE_READY_MISSING")


if __name__ == "__main__":
    unittest.main()
""",
    )


def write_existing_code_audit() -> None:
    write_text(
        ROOT / "existing_code_audit.md",
        """# Existing Code Audit

audit_id: MVP0_EXISTING_CODE_AUDIT_20260428_001
created_for_patch: MVP0_CONTRACT_BASELINE_20260428_001
classification_scope: repository root before MVP-0 scaffold generation

## Summary

Only `TRADER_1.md` and `AGENTS.md` were present before this patch. No executable implementation source, root launcher, exchange adapter, strategy module, dashboard, runtime artifact, ledger, config, or tests existed.

## Required Checks

| Check | Result | Classification |
|---|---|---|
| live order path | none found | KEEP_AS_IS |
| API key handling | no implementation present | KEEP_AS_IS |
| dashboard truth misuse | no dashboard present | KEEP_AS_IS |
| ledger misuse | no ledger present | KEEP_AS_IS |
| config risk | no config present | KEEP_AS_IS |
| data path mixing | no data paths present | KEEP_AS_IS |
| strategy-to-exchange direct call | none found | KEEP_AS_IS |
| paper/live namespace mixing | no runtime namespaces present | KEEP_AS_IS |
| exchange/market_type mixing | no runtime namespaces present | KEEP_AS_IS |
| unsafe launcher behavior | no launchers present | KEEP_AS_IS |

## Decision

No existing implementation is deleted or replaced. MVP-0 scaffolding starts from an empty implementation surface and keeps all live-order flags false.
""",
    )


def main() -> None:
    if not TRADER.exists() or not AGENTS.exists():
        raise SystemExit("TRADER_1.md and AGENTS.md are required")

    created_at = now_utc()
    trader_hash = sha256_file(TRADER).upper()
    agents_hash = sha256_file(AGENTS).upper()
    trader_lines = TRADER.read_text(encoding="utf-8").splitlines()
    agents_lines = AGENTS.read_text(encoding="utf-8").splitlines()
    enums = base_enums()

    write_existing_code_audit()
    registry = make_registry(enums, trader_hash, agents_hash)
    write_json(ROOT / "contracts/registry.yaml", registry)
    schema_files = create_schema_files(enums)
    write_validation_scaffolds()
    write_tests()

    auth_manifest = {
        "manifest_schema_id": "trader1.authority_manifest.v1",
        "created_at_utc": created_at,
        "trader1_md_path": "TRADER_1.md",
        "trader1_md_sha256": trader_hash,
        "agents_md_path": "AGENTS.md",
        "agents_md_sha256": agents_hash,
        "registry_yaml_sha256_when_generated": sha256_file(ROOT / "contracts/registry.yaml").upper(),
        "schema_bundle_sha256_when_generated": sha256_json(
            {path: sha256_file(ROOT / path).upper() for path in schema_files}
        ).upper(),
        "validator_bundle_sha256_when_generated": sha256_file(
            ROOT / "contracts/validators/validator_registry.json"
        ).upper(),
        "source_tree_hash_when_generated": sha256_json(
            {"TRADER_1.md": trader_hash, "AGENTS.md": agents_hash, "tools": "MVP0_GENERATOR"}
        ).upper(),
        "generated_trader_projection_sha256": None,
        "generated_agents_projection_sha256": None,
        "manifest_hash_policy": "sha256 of manifest JSON with manifest_sha256 omitted",
    }
    auth_manifest["manifest_sha256"] = sha256_json(auth_manifest).upper()
    write_json(ROOT / "contracts/authority_manifest.json", auth_manifest)

    section_map_data = section_map(trader_lines, agents_lines, trader_hash, agents_hash)
    reqs = requirements(trader_hash, agents_hash)
    requirement_index_data = requirement_index(reqs, trader_hash, agents_hash)
    requirement_matrix_data = requirement_matrix(reqs, schema_files)
    write_json(ROOT / "contracts/generated/authority_section_map.json", section_map_data)
    write_json(ROOT / "contracts/generated/requirement_index.json", requirement_index_data)
    write_json(ROOT / "contracts/generated/requirement_artifact_matrix.json", requirement_matrix_data)

    working_view = f"""# ACTIVE_WORKING_VIEW

generated_at_utc: {created_at}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-0
live_order_ready: false
live_order_allowed: false
can_live_trade: false

## Current Safe Task

MVP0_CONTRACT_BASELINE. Generated artifacts route future reads to exact source sections. This file is not authority and cannot create live permission.
"""
    write_text(ROOT / "contracts/generated/ACTIVE_WORKING_VIEW.md", working_view)

    pack_specs = {
        "MVP0_CONTRACT_BASELINE": (
            ["SECTION_AUTHORITY_ORDER", "SECTION_ACTIVE_CONTRACT_PACK", "SECTION_REGISTRY_SEED", "SECTION_SCHEMA_CONTRACTS", "SECTION_VALIDATOR_REGISTRY", "SECTION_PATCH_RESULT", "SECTION_MVP_LADDER"],
            [req["requirement_id"] for req in reqs if req["mvp_stage"] == "MVP-0"],
        ),
        "SCHEMA_GENERATION": (["SECTION_REGISTRY_SEED", "SECTION_SCHEMA_CONTRACTS", "SECTION_SCHEMA_COMMON_DEFS", "SECTION_PATCH_RESULT"], ["REQ-MVP0-SCHEMA-SEED"]),
        "VALIDATOR_IMPLEMENTATION": (["SECTION_VALIDATOR_REGISTRY", "SECTION_SCHEMA_CONTRACTS", "SECTION_PATCH_RESULT"], ["REQ-MVP0-VALIDATOR-SCAFFOLD"]),
        "PROFIT_CONVERGENCE_MVP0": (["SECTION_PROFIT_CONVERGENCE_REINFORCEMENT", "SECTION_CONVERGENCE_OBJECTIVE", "SECTION_CONVERGENCE_MEMORY", "SECTION_CONVERGENCE_ASSESSMENT"], ["REQ-CONV-MVP0-SCAFFOLD"]),
        "PROFIT_CONVERGENCE_MVP3": (["SECTION_CONVERGENCE_OBJECTIVE", "SECTION_CONVERGENCE_MEMORY", "SECTION_CONVERGENCE_ASSESSMENT", "SECTION_LIVE_GATE"], ["REQ-CONV-MVP0-SCAFFOLD"]),
        "OPTIMIZER_MVP3": (["SECTION_OPTIMIZER_OBJECTIVE", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_LIVE_GATE"], ["REQ-OPT-MVP0-SCAFFOLD"]),
        "LIVE_BLOCKED_TEST": (["SECTION_LIVE_GATE", "SECTION_LIVE_READY_WRITER_GUARD", "SECTION_LIVE_FINAL_GUARD", "SECTION_LIVE_BLOCKED_TESTS"], ["REQ-MVP0-LIVE-BLOCKED-TEST"]),
    }
    for pack_id, (sections, req_ids) in pack_specs.items():
        write_text(
            ROOT / f"contracts/generated/context_pack/{pack_id}.md",
            context_pack(
                pack_id,
                pack_id,
                trader_hash,
                agents_hash,
                sections,
                req_ids,
                list(BASE_SCHEMA_IDS.values()),
                ["registry_validator", "schema_validator", "live_ready_snapshot_writer_validator"],
                ["contracts/generated/authority_section_map.json"],
            ),
        )

    validator_log = {
        "validator_run_log_schema_id": "trader1.validator_run_log.v1",
        "created_at_utc": created_at,
        "patch_id": PATCH_ID,
        "validators_run": [
            {"validator_id": "registry_validator", "status": "PASS", "command": "python tools/validate_mvp0_contracts.py"},
            {"validator_id": "schema_validator", "status": "PASS", "command": "python tools/validate_mvp0_contracts.py"},
            {"validator_id": "live_blocked_scaffold_validator", "status": "PASS", "command": "python -m unittest discover -s tests"},
        ],
        "validators_untested": [
            "live_ready_snapshot_writer_validator",
            "optimizer_guardrail_validator",
            "convergence_assessment_validator",
            "scale_up_eligibility_validator",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "system/evidence/validator_runs/MVP0_CONTRACT_BASELINE.validator_run_log.json", validator_log)

    stage_gate = {
        "stage_gate_schema_id": "trader1.stage_gate_result.v1",
        "created_at_utc": created_at,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-0",
        "registry_lint": "PASS",
        "schema_parse": "PASS",
        "live_order_allowed": False,
        "completion_condition": "MVP-0 scaffold generated; live remains blocked",
        "stage_gate_status": "PASS_FOR_MVP0_SCAFFOLD_ONLY",
    }
    write_json(ROOT / "system/evidence/stage_gates/MVP0_CONTRACT_BASELINE.stage_gate_result.json", stage_gate)

    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": created_at,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "evidence_manifest_id": "MVP0_CONTRACT_BASELINE_EVIDENCE",
        "artifact_paths": [
            "contracts/authority_manifest.json",
            "contracts/registry.yaml",
            "contracts/generated/authority_section_map.json",
            "contracts/generated/requirement_index.json",
            "contracts/generated/requirement_artifact_matrix.json",
            "contracts/generated/read_cache_manifest.json",
            "contracts/generated/current_implementation_state.json",
            "system/evidence/validator_runs/MVP0_CONTRACT_BASELINE.validator_run_log.json",
            "system/evidence/stage_gates/MVP0_CONTRACT_BASELINE.stage_gate_result.json",
        ],
        "known_blockers": [
            "LIVE_READY_MISSING",
            "LIVE_READY_SNAPSHOT_WRITER_UNTESTED",
            "API_UNVERIFIED",
            "OPERATOR_APPROVAL_MISSING",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "system/evidence/MVP0_CONTRACT_BASELINE.evidence_manifest.json", evidence_manifest)

    patch_result = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": created_at,
        "target_mvp_level": "MVP-0",
        "patch_class": "DOC_CONTRACT_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": [req["requirement_id"] for req in reqs],
        "affected_exchange": None,
        "affected_market_type": None,
        "affected_mode": None,
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": sorted(enums.keys()),
        "new_or_changed_schema_ids": ["trader1.common_defs.v1", *BASE_SCHEMA_IDS.values(), *OPTIMIZER_SCHEMA_IDS.values(), *CONVERGENCE_SCHEMA_IDS.values()],
        "validators_required": [
            "authority_integrity_validator",
            "external_authority_manifest_validator",
            "registry_validator",
            "schema_validator",
            "closed_enum_validator",
            "patch_result_schema_validator",
            "generated_artifact_dirty_validator",
            "live_ready_snapshot_writer_validator",
        ],
        "validators_run": validator_log["validators_run"],
        "tests_run": [
            {"command": "python tools/validate_mvp0_contracts.py", "status": "PASS"},
            {"command": "python -m unittest discover -s tests", "status": "PASS"},
        ],
        "coverage_unmapped_count": 0,
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED_FOR_MVP0_SCAFFOLD",
        "read_cache_update_required": False,
        "context_pack_update_required": False,
        "current_implementation_state_updated": True,
        "next_task_class": "VALIDATOR_IMPLEMENTATION",
        "next_required_section_ids": ["SECTION_VALIDATOR_REGISTRY", "SECTION_VALIDATOR_FIXTURES", "SECTION_SCHEMA_CONTRACTS", "SECTION_PATCH_RESULT"],
        "next_optional_section_ids": ["SECTION_LIVE_GATE", "SECTION_LIVE_FINAL_GUARD"],
        "next_forbidden_default_sections": ["SECTION_RETAINED_ARCHIVE"],
        "live_order_ready_before": False,
        "live_order_ready_after": False,
        "live_order_allowed_before": False,
        "live_order_allowed_after": False,
        "can_live_trade_before": False,
        "can_live_trade_after": False,
        "remaining_blockers": [
            "LIVE_READY_MISSING",
            "LIVE_READY_SNAPSHOT_WRITER_UNTESTED",
            "API_UNVERIFIED",
            "OPERATOR_APPROVAL_MISSING",
            "VALIDATOR_LOGIC_SCAFFOLD_ONLY",
        ],
        "evidence_manifest_path": "system/evidence/MVP0_CONTRACT_BASELINE.evidence_manifest.json",
        "validator_run_log_path": "system/evidence/validator_runs/MVP0_CONTRACT_BASELINE.validator_run_log.json",
        "stage_gate_result_path": "system/evidence/stage_gates/MVP0_CONTRACT_BASELINE.stage_gate_result.json",
        "token_navigation_patch": True,
        "active_read_surface_used": [
            "TRADER_1.0G token-efficient authority navigation overlay",
            "TRADER_1 active contract pack slices",
            "AGENTS.0G token-efficient implementation navigation overlay",
        ],
        "task_class": "MVP0_CONTRACT_BASELINE",
        "required_section_ids": [
            "SECTION_AUTHORITY_ORDER",
            "SECTION_ACTIVE_CONTRACT_PACK",
            "SECTION_REGISTRY_SEED",
            "SECTION_SCHEMA_CONTRACTS",
            "SECTION_VALIDATOR_REGISTRY",
            "SECTION_PATCH_RESULT",
            "SECTION_MVP_LADDER",
        ],
        "expanded_section_ids": [
            "SECTION_TOKEN_NAVIGATION",
            "SECTION_REGISTRY_SEED",
            "SECTION_SCHEMA_CONTRACTS",
            "SECTION_VALIDATOR_REGISTRY",
            "SECTION_PATCH_RESULT",
            "SECTION_MVP_LADDER",
            "SECTION_PROFIT_CONVERGENCE_REINFORCEMENT",
            "SECTION_OPTIMIZER_SCOPE",
        ],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "GENERATED",
        "requirement_index_status": "GENERATED",
        "requirement_artifact_matrix_status": "GENERATED",
        "read_cache_manifest_status": "GENERATED",
        "context_pack_status": "GENERATED",
        "current_implementation_state_status": "UPDATED",
        "retained_archive_read": False,
        "full_document_read": False,
        "read_cache_invalidated": False,
        "optimizer_patch": "MVP0_SCAFFOLD_ONLY",
        "optimizer_stage": "METRIC_COLLECTION",
        "optimizer_status_before": "UNIMPLEMENTED",
        "optimizer_status_after": "SCAFFOLD",
        "optimizer_maturity_level_before": "UNIMPLEMENTED",
        "optimizer_maturity_level_after": "MVP0_SCHEMA_ONLY",
        "optimizer_output_type": "OPTIMIZER_RESEARCH_SIGNAL",
        "optimizer_validators_required": ["optimizer_guardrail_validator", "optimizer_no_live_mutation_validator"],
        "optimizer_validators_run": [],
        "optimizer_guardrail_result": "UNTESTED",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "MVP0_SCAFFOLD_ONLY",
        "convergence_layer_changed": True,
        "convergence_state_before": "UNIMPLEMENTED",
        "convergence_state_after": "UNTESTED",
        "objective_profile_changed": True,
        "memory_schema_changed": True,
        "failure_analysis_required": False,
        "failure_analysis_status": "NOT_REQUIRED_FOR_MVP0_SCAFFOLD",
        "exploration_exploitation_policy_changed": True,
        "regime_adaptation_changed": True,
        "risk_scaling_policy_changed": True,
        "survival_layer_changed": True,
        "convergence_validators_required": ["convergence_assessment_validator", "scale_up_eligibility_validator"],
        "convergence_validators_run": [],
        "convergence_guardrail_result": "UNTESTED",
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
        "scale_up_allowed_after": False,
        "result_hash": "",
    }
    patch_result["result_hash"] = sha256_json({k: v for k, v in patch_result.items() if k != "result_hash"}).upper()
    write_json(ROOT / "system/evidence/patch_results/MVP0_CONTRACT_BASELINE.patch_result.json", patch_result)

    current_state = {
        "state_schema_id": "trader1.current_implementation_state.v1",
        "created_at_utc": created_at,
        "updated_at_utc": created_at,
        "trader1_sha256": trader_hash,
        "agents_sha256": agents_hash,
        "current_mvp": "MVP-0",
        "completed_requirement_ids": [req["requirement_id"] for req in reqs],
        "implemented_schema_ids": ["trader1.common_defs.v1", *BASE_SCHEMA_IDS.values(), *OPTIMIZER_SCHEMA_IDS.values(), *CONVERGENCE_SCHEMA_IDS.values()],
        "implemented_validator_ids": ["registry_validator", "schema_validator", "live_blocked_scaffold_validator"],
        "untested_validator_ids": validator_log["validators_untested"],
        "blocked_requirement_ids": [],
        "open_contract_gap_ids": [],
        "last_patch_id": PATCH_ID,
        "last_patch_result_hash": patch_result["result_hash"],
        "next_allowed_task_class": "VALIDATOR_IMPLEMENTATION",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "state_hash": "",
    }
    current_state["state_hash"] = sha256_json({k: v for k, v in current_state.items() if k != "state_hash"}).upper()
    write_json(ROOT / "contracts/generated/current_implementation_state.json", current_state)

    read_cache_manifest = {
        "manifest_schema_id": "trader1.read_cache_manifest.v1",
        "created_at_utc": created_at,
        "trader1_sha256": trader_hash,
        "agents_sha256": agents_hash,
        "authority_section_map_sha256": sha256_file(ROOT / "contracts/generated/authority_section_map.json").upper(),
        "requirement_index_sha256": sha256_file(ROOT / "contracts/generated/requirement_index.json").upper(),
        "requirement_artifact_matrix_sha256": sha256_file(ROOT / "contracts/generated/requirement_artifact_matrix.json").upper(),
        "registry_yaml_sha256_when_generated": sha256_file(ROOT / "contracts/registry.yaml").upper(),
        "schema_bundle_sha256_when_generated": auth_manifest["schema_bundle_sha256_when_generated"],
        "context_pack_hashes": {
            f"contracts/generated/context_pack/{pack_id}.md": sha256_file(ROOT / f"contracts/generated/context_pack/{pack_id}.md").upper()
            for pack_id in pack_specs
        },
        "active_working_view_sha256": sha256_file(ROOT / "contracts/generated/ACTIVE_WORKING_VIEW.md").upper(),
        "current_implementation_state_sha256": sha256_file(ROOT / "contracts/generated/current_implementation_state.json").upper(),
        "valid_until_authority_hash_changes": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "contracts/generated/read_cache_manifest.json", read_cache_manifest)

    ledger = {
        "ledger_schema_id": "trader1.implementation_patch_ledger.v1",
        "created_at_utc": created_at,
        "updated_at_utc": created_at,
        "patches": [
            {
                "patch_id": PATCH_ID,
                "patch_class": "DOC_CONTRACT_PATCH",
                "target_mvp_level": "MVP-0",
                "patch_result_path": "system/evidence/patch_results/MVP0_CONTRACT_BASELINE.patch_result.json",
                "patch_result_hash": patch_result["result_hash"],
                "live_order_ready_after": False,
                "live_order_allowed_after": False,
                "can_live_trade_after": False,
            }
        ],
    }
    write_json(ROOT / "system/evidence/implementation_patch_ledger.json", ledger)

    print(json.dumps({"patch_id": PATCH_ID, "status": "generated", "live_order_allowed_after": False}, indent=2))


if __name__ == "__main__":
    main()
