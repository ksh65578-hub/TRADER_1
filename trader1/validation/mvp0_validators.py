from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable

from trader1.adapters.upbit.market_data import (
    build_upbit_public_candle_data_from_rest_payload,
    build_upbit_public_market_data_fixture,
)
from trader1.adapters.upbit.paper_broker import (
    build_upbit_paper_dry_run_report,
    upbit_paper_dry_run_hash,
    validate_upbit_paper_dry_run_report,
)
from trader1.adapters.upbit.account_readonly import (
    build_read_only_account_snapshot,
    read_only_account_snapshot_hash,
    validate_read_only_account_snapshot,
)
from trader1.adapters.upbit.private_stream import (
    build_private_stream_health,
    private_stream_health_hash,
    validate_private_stream_health,
)
from trader1.adapters.upbit.reconciliation import (
    build_upbit_read_only_reconciliation_path,
    upbit_read_only_reconciliation_path_hash,
    validate_upbit_read_only_reconciliation_path,
)
from trader1.adapters.binance.surface import (
    build_binance_adapter_surface_report,
    binance_adapter_surface_hash,
    validate_binance_adapter_surface_report,
)
from trader1.config.config_schema import (
    attach_config_hash,
    build_runtime_config,
    validate_runtime_config,
)
from trader1.core.events.intent_wal import intent_wal_event_hash
from trader1.core.ledger.restart_recovery import (
    build_restart_recovery_report,
    restart_recovery_hash,
    validate_restart_recovery_report,
)
from trader1.core.sizing.position_sizing import (
    build_position_sizing_decision,
    sizing_decision_hash,
    validate_position_sizing_decision,
)
from trader1.core.strategy.strategy_unit import (
    build_basic_strategy_unit,
    strategy_unit_hash,
    validate_strategy_unit,
)
from trader1.dashboard.read_only_dashboard import (
    build_read_only_dashboard_shell,
    dashboard_shell_hash,
    render_dashboard_html,
    validate_dashboard_visual_layout_contract,
    validate_read_only_dashboard_shell,
)
from trader1.dashboard.live_review_dashboard import (
    build_live_review_dashboard,
    live_review_dashboard_hash,
    validate_live_review_dashboard,
)
from trader1.dashboard.summary_writer import build_summary_shell, validate_summary_shell
from trader1.execution.live_order_gateway import evaluate_live_order_path
from trader1.runtime.artifact_hygiene import (
    build_runtime_dashboard_artifact_hygiene_report,
    validate_runtime_dashboard_artifact_hygiene_report,
)
from trader1.runtime.readiness.readiness_surface import (
    build_readiness_surface,
    surface_hash,
    validate_readiness_surface,
)
from trader1.runtime.readiness.live_preflight import (
    build_upbit_live_review_preflight,
    live_preflight_hash,
    validate_live_preflight_report,
)
from trader1.runtime.readiness.live_ready_snapshot import (
    attach_writer_input_hash,
    build_blocked_live_ready_snapshot,
    build_writer_input,
    evaluate_live_ready_snapshot_writer,
    validate_live_ready_snapshot,
)
from trader1.runtime.readiness.manual_order_test_evidence import (
    build_missing_manual_order_test_evidence,
    manual_order_test_hash,
    validate_manual_order_test_evidence,
)
from trader1.runtime.readiness.official_api_verification import (
    PASS_REQUIRED_FACTS,
    build_official_api_verification_report,
    official_api_report_hash,
    validate_official_api_verification_report,
)
from trader1.runtime.boot.launcher_guard import ALLOWED_ROOT_LAUNCHERS, inspect_root_launchers
from trader1.runtime.boot.safe_launcher import (
    build_launcher_report,
    launcher_dashboard_paths,
    validate_launcher_report,
    write_launcher_dashboard,
)
from trader1.runtime.boot.startup_probe import build_startup_probe, startup_probe_hash, validate_startup_probe
from trader1.runtime.health.heartbeat import build_heartbeat, heartbeat_hash, validate_heartbeat
from trader1.runtime.health.runtime_resource_pressure import inspect_runtime_resource_pressure
from trader1.runtime.health.stability_history import validate_stability_history
from trader1.runtime.ledger.execution_ledger import (
    build_ledger_event,
    build_minimal_intent_chain,
    ledger_event_hash,
    validate_ledger_chain,
    validate_ledger_event,
)
from trader1.runtime.ledger.paper_ledger_rollup import (
    build_paper_ledger_rollup_report,
    paper_ledger_rollup_hash,
    validate_paper_ledger_rollup_report,
)
from trader1.runtime.operator_control.operator_control import (
    build_operator_action_audit,
    operator_action_hash,
    validate_operator_action_audit,
)
from trader1.runtime.portfolio.paper_portfolio import (
    build_initial_paper_portfolio_snapshot,
    build_paper_portfolio_snapshot_from_fill,
    paper_portfolio_hash,
    validate_paper_portfolio_snapshot,
)
from trader1.runtime.paper.operational_cycle import (
    build_upbit_operational_paper_cycle,
    operation_gate_hash,
    validate_paper_operation_gate_report,
)
from trader1.runtime.paper.upbit_paper_runtime import (
    build_upbit_paper_runtime_cycle_report,
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import (
    build_upbit_public_market_data_collection_report,
    upbit_public_market_data_collection_hash,
    validate_upbit_public_market_data_collection_report,
    validate_upbit_public_market_data_collection_writer_report,
    validate_upbit_public_market_data_latest_pointer,
    write_upbit_public_market_data_collection_artifacts,
)
from trader1.runtime.paper.upbit_public_rest_sample import (
    build_upbit_public_rest_sample_report,
    upbit_public_rest_sample_hash,
    validate_upbit_public_rest_sample_report,
)
from trader1.runtime.paper.upbit_public_rest_continuity import (
    build_upbit_public_rest_continuity_report,
    upbit_public_rest_continuity_hash,
    validate_upbit_public_rest_continuity_report,
)
from trader1.runtime.paper.upbit_public_rest_continuity_history import (
    build_upbit_public_rest_continuity_history_report,
    upbit_public_rest_continuity_history_hash,
    validate_upbit_public_rest_continuity_history_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    build_upbit_paper_runtime_recovery_guard_report,
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
    upbit_paper_runtime_recovery_guard_hash,
    validate_upbit_paper_persistent_loop_report,
    validate_upbit_paper_runtime_recovery_guard_report,
)
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    build_upbit_paper_runtime_sample_history,
    upbit_paper_runtime_sample_hash,
    upbit_paper_runtime_sample_history_hash,
    validate_upbit_paper_runtime_sample_history,
    write_upbit_paper_runtime_sample_history,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import (
    build_upbit_paper_stale_loop_reconciliation_report,
    stale_loop_reconciliation_hash,
    validate_upbit_paper_stale_loop_reconciliation_report,
    write_upbit_paper_stale_loop_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import (
    build_upbit_paper_stale_loop_regeneration_plan,
    stale_loop_regeneration_plan_hash,
    validate_upbit_paper_stale_loop_regeneration_plan,
    write_upbit_paper_stale_loop_regeneration_plan,
)
from trader1.runtime.paper.upbit_paper_stale_loop_execution_guard import (
    build_upbit_paper_stale_loop_execution_guard,
    stale_loop_execution_guard_hash,
    validate_upbit_paper_stale_loop_execution_guard,
    write_upbit_paper_stale_loop_execution_guard,
)
from trader1.runtime.paper.upbit_paper_stale_loop_safe_regeneration_executor import (
    build_upbit_paper_stale_loop_safe_regeneration_executor_report,
    stale_loop_safe_regeneration_executor_hash,
    validate_upbit_paper_stale_loop_safe_regeneration_executor_report,
    write_upbit_paper_stale_loop_safe_regeneration_executor_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_post_regeneration_reconciliation import (
    build_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
    stale_loop_post_regeneration_reconciliation_hash,
    validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
    write_upbit_paper_stale_loop_post_regeneration_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_blocked_repair_plan import (
    build_upbit_paper_blocked_repair_plan_report,
    upbit_paper_blocked_repair_plan_hash,
    validate_upbit_paper_blocked_repair_plan_report,
    write_upbit_paper_blocked_repair_plan_report,
)
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import (
    build_upbit_paper_ledger_rollup_repair_report,
    upbit_paper_ledger_rollup_repair_hash,
    validate_upbit_paper_ledger_rollup_repair_report,
    write_upbit_paper_ledger_rollup_repair_report,
)
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import (
    REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE,
    build_upbit_paper_post_repair_reconciliation_report,
    upbit_paper_post_repair_reconciliation_hash,
    validate_upbit_paper_post_repair_reconciliation_report,
    write_upbit_paper_post_repair_reconciliation_report,
)
from trader1.research.replay.replay_runner import (
    build_replay_consistency_report,
    replay_consistency_hash,
    validate_replay_consistency_report,
)
from trader1.research.profitability.candidate_scorecard import (
    ROBUSTNESS_SOURCE_PREFIXES,
    candidate_scorecard_from_upbit_paper_runtime_cycle,
    has_required_robustness_source_ids,
    runtime_cycle_binding_from_source_ids,
    runtime_cycle_source_evidence_id,
)
from trader1.research.shadow.shadow_runner import (
    build_paper_shadow_evidence_accumulation_report,
    build_paper_shadow_separation_report,
    paper_shadow_actual_runtime_source_id_errors,
    paper_shadow_actual_runtime_requirement_status_errors,
    paper_shadow_evidence_hash,
    paper_shadow_paired_supporting_window_count,
    paper_shadow_separation_hash,
    validate_paper_shadow_evidence_accumulation_report,
    validate_paper_shadow_separation_report,
)
from trader1.research.shadow.shadow_observation import (
    build_shadow_observation_report,
    shadow_observation_hash,
    validate_shadow_observation_report,
)
from trader1.research.shadow.shadow_observation_stream import (
    build_shadow_observation_stream_report,
    shadow_observation_stream_hash,
    validate_shadow_observation_stream_report,
)
from trader1.research.shadow.shadow_observation_scheduler import (
    build_shadow_observation_scheduler_guard_report,
    shadow_observation_scheduler_guard_hash,
    validate_shadow_observation_scheduler_guard_report,
)
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    build_shadow_observation_persistent_runtime_report,
    shadow_observation_persistent_runtime_hash,
    validate_shadow_observation_persistent_runtime_report,
)
from trader1.research.shadow.shadow_observation_actual_runtime_blocker import (
    build_shadow_observation_actual_runtime_blocker_report,
    shadow_observation_actual_runtime_blocker_hash,
    validate_shadow_observation_actual_runtime_blocker_report,
)
from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    build_shadow_observation_actual_runtime_harness_report,
    shadow_observation_actual_runtime_harness_hash,
    validate_shadow_observation_actual_runtime_harness_report,
)
from trader1.research.shadow.shadow_observation_artifact_writer import (
    shadow_observation_artifact_writer_hash,
    validate_shadow_observation_artifact_writer_report,
    write_shadow_observation_runtime_artifacts,
)
from trader1.research.shadow.shadow_observation_runtime_orchestration import (
    build_shadow_observation_runtime_orchestration_report,
    shadow_observation_runtime_orchestration_hash,
    validate_shadow_observation_runtime_orchestration_report,
)
from trader1.runtime.protection.emergency_flatten import (
    build_emergency_flatten_report,
    emergency_flatten_hash,
    validate_emergency_flatten_report,
)
from trader1.runtime.reconciliation.reconciliation import (
    build_reconciliation_report,
    reconciliation_report_hash,
    snapshot_hash,
    validate_reconciliation_report,
)
from trader1.runtime.resource_guard.safety_control import (
    build_safety_control_report,
    safety_control_hash,
    validate_safety_control_report,
)
from trader1.safety.live_order_gate import BLOCKED_CASES, evaluate_live_order_gate
from trader1.security.source_bundle import (
    classify_path,
    load_denylist,
    load_source_bundle_manifest,
    write_source_bundle_manifest,
)
from trader1.security.api_key_permission_check import (
    build_api_key_permission_check_report,
    api_key_permission_check_hash,
    validate_api_key_permission_check_report,
)
from trader1.validation.namespace import (
    NamespaceScope,
    artifact_path,
    classify_dashboard_artifact,
    validate_artifact_path,
    validate_namespace_join,
    validate_truth_override,
)
from trader1.validation.schema_instance import (
    load_schema_bundle,
    schema_for_instance,
    validate_instance_against_schema,
)
from trader1.validation.bytecode_free_syntax import (
    build_bytecode_free_syntax_report,
    validate_bytecode_free_syntax_report,
)


ROOT = Path(__file__).resolve().parents[2]
MVP0_CORE_VALIDATORS = [
    "authority_integrity_validator",
    "external_authority_manifest_validator",
    "registry_validator",
    "schema_validator",
    "closed_enum_validator",
    "common_defs_drift_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "coverage_index_validator",
    "active_schema_extraction_validator",
    "generated_artifact_dirty_validator",
    "root_launcher_guard_validator",
    "root_launcher_surface_validator",
    "binance_adapter_surface_validator",
    "runtime_config_validator",
    "live_ready_snapshot_writer_validator",
    "startup_probe_validator",
    "heartbeat_validator",
    "summary_shell_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "runtime_schema_instance_validator",
    "runtime_dashboard_artifact_hygiene_validator",
    "runtime_stability_history_validator",
    "runtime_resource_pressure_validator",
    "bytecode_free_syntax_validator",
    "paper_portfolio_snapshot_validator",
    "safety_control_validator",
    "ledger_durability_validator",
    "paper_ledger_rollup_validator",
    "reconciliation_validator",
    "ledger_reconciliation_validator",
    "emergency_flatten_validator",
    "operator_action_audit_validator",
    "operator_control_validator",
    "upbit_paper_dry_run_validator",
    "upbit_paper_runtime_cycle_validator",
    "upbit_public_market_data_collection_validator",
    "upbit_public_rest_sample_validator",
    "upbit_public_rest_continuity_validator",
    "upbit_public_rest_continuity_history_validator",
    "upbit_paper_persistent_loop_validator",
    "upbit_paper_runtime_sample_history_validator",
    "upbit_paper_stale_loop_reconciliation_validator",
    "upbit_paper_stale_loop_regeneration_plan_validator",
    "upbit_paper_stale_loop_execution_guard_validator",
    "upbit_paper_stale_loop_safe_regeneration_executor_validator",
    "upbit_paper_stale_loop_post_regeneration_reconciliation_validator",
    "upbit_paper_blocked_repair_plan_validator",
    "upbit_paper_ledger_rollup_repair_validator",
    "upbit_paper_post_repair_reconciliation_validator",
    "upbit_paper_runtime_recovery_guard_validator",
    "restart_recovery_validator",
    "upbit_operational_paper_gate_validator",
    "upbit_live_review_preflight_validator",
]
OPTIMIZER_CONVERGENCE_GUARDRAIL_VALIDATORS = [
    "optimizer_no_live_mutation_validator",
    "exploration_exploitation_policy_validator",
    "exploration_to_exploitation_validator",
    "candidate_cooldown_validator",
    "rolling_window_default_validator",
    "parameter_narrowing_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "scale_up_eligibility_validator",
]
LIVE_FINAL_GUARD_VALIDATORS = ["live_final_guard_validator"]
CONVERGENCE_FOUNDATION_VALIDATORS = [
    "convergence_objective_profile_validator",
    "optimizer_memory_state_validator",
    "strategy_performance_memory_validator",
]
CONVERGENCE_ASSESSMENT_DEPENDENCY_VALIDATORS = [
    "convergence_objective_profile_validator",
    "optimizer_memory_state_validator",
    "strategy_performance_memory_validator",
    "overfit_diagnostic_validator",
    "rolling_window_default_validator",
    "execution_feedback_loop_validator",
    "failure_analysis_validator",
    "shadow_observation_runtime_validator",
    "shadow_observation_stream_validator",
    "shadow_observation_scheduler_guard_validator",
    "shadow_observation_persistent_runtime_validator",
    "shadow_observation_actual_runtime_blocker_validator",
    "shadow_observation_actual_runtime_harness_validator",
    "shadow_observation_artifact_writer_validator",
    "shadow_observation_runtime_orchestration_validator",
    "paper_shadow_evidence_accumulation_validator",
    "market_regime_adaptation_validator",
    "model_drift_validator",
    "coverage_index_validator",
]
CONVERGENCE_RISK_SCALE_VALIDATORS = [
    "risk_scaling_decision_validator",
    "live_burn_in_feedback_validator",
    "paper_live_parity_validator",
    "execution_quality_measurement_validator",
    "survival_layer_validator",
]
PROFITABILITY_OPTIMIZER_EVIDENCE_VALIDATORS = [
    "candidate_scorecard_validator",
    "candidate_scorecard_net_ev_validator",
    "ranking_stability_validator",
    "rolling_window_default_validator",
    "parameter_bound_validator",
    "promotion_threshold_validator",
    "optimizer_run_report_validator",
    "optimizer_recommendation_validator",
    "optimizer_guardrail_report_validator",
    "optimization_state_validator",
    "exploration_exploitation_policy_validator",
    "exploration_to_exploitation_validator",
    "candidate_cooldown_validator",
    "parameter_narrowing_validator",
    "optimizer_memory_state_validator",
    "strategy_performance_memory_validator",
    "strategy_condition_matrix_validator",
    "symbol_strategy_regime_fit_validator",
    "market_regime_adaptation_validator",
    "overfit_diagnostic_validator",
    "execution_feedback_loop_validator",
    "shadow_observation_runtime_validator",
    "shadow_observation_stream_validator",
    "shadow_observation_scheduler_guard_validator",
    "shadow_observation_persistent_runtime_validator",
    "shadow_observation_actual_runtime_blocker_validator",
    "shadow_observation_actual_runtime_harness_validator",
    "shadow_observation_artifact_writer_validator",
    "shadow_observation_runtime_orchestration_validator",
    "realized_slippage_validator",
    "failure_analysis_validator",
    "order_failure_taxonomy_validator",
    "profit_convergence_cycle_validator",
    "shadow_observation_runtime_validator",
    "shadow_observation_stream_validator",
    "shadow_observation_scheduler_guard_validator",
    "shadow_observation_persistent_runtime_validator",
    "shadow_observation_actual_runtime_blocker_validator",
    "shadow_observation_actual_runtime_harness_validator",
    "shadow_observation_artifact_writer_validator",
    "shadow_observation_runtime_orchestration_validator",
    "paper_shadow_evidence_accumulation_validator",
    "paper_exposure_quality_report_validator",
    "profitability_evidence_maturity_rollup_validator",
    "profitability_optimizer_evidence_gap_validator",
]
PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS = {
    "strategy_entry_exit_no_trade",
    "symbol_selection_regime",
    "vwap_trend_breakout",
    "risk_sizing_exposure",
    "execution_slippage_fee_impact",
    "optimizer_objective_net_ev_after_cost",
    "overfit_oos_walk_forward",
    "convergence_memory_failure_learning",
    "paper_shadow_evidence_accumulation",
    "dashboard_operator_profitability_visibility",
}
PROFITABILITY_EVIDENCE_FORBIDDEN_PHRASES = {
    "profit guaranteed",
    "guaranteed profit",
    "automatic profit",
    "converged to profit",
    "self-optimizing live",
    "ready to size up",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text_file_canonical(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return sha256_bytes(normalized.encode("utf-8"))


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def latest_patch_result_path() -> Path:
    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    if ledger_path.exists():
        ledger = load_json(ledger_path)
        patches = ledger.get("patches", [])
        if patches:
            return ROOT / patches[-1]["patch_result_path"]
    return ROOT / "system" / "evidence" / "patch_results" / "MVP0_CONTRACT_BASELINE.patch_result.json"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


@dataclass
class ValidatorResult:
    validator_id: str
    status: str
    message: str
    blocking: bool
    checked_at_utc: str = field(default_factory=utc_now)
    input_artifact_paths: list[str] = field(default_factory=list)
    blocker_code: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_id": "trader1.validator_result.v1",
            "generated_at_utc": self.checked_at_utc,
            "project_id": "TRADER_1",
            "authority": current_authority_hashes(),
            "exchange": None,
            "market_type": None,
            "mode": None,
            "status": self.status,
            "blockers": []
            if self.blocker_code is None
            else [{"code": self.blocker_code, "severity": "HIGH", "message": self.message, "source_requirement_id": None}],
            "notes": self.message,
            "validator_id": self.validator_id,
            "checked_at_utc": self.checked_at_utc,
            "input_artifact_paths": self.input_artifact_paths,
            "blocking": self.blocking,
        }


def current_authority_hashes() -> dict[str, str]:
    return {
        "trader1_sha256": sha256_file(ROOT / "TRADER_1.md"),
        "agents_sha256": sha256_file(ROOT / "AGENTS.md"),
    }


def pass_result(validator_id: str, message: str, paths: list[Path]) -> ValidatorResult:
    return ValidatorResult(validator_id, "PASS", message, False, input_artifact_paths=[rel(path) for path in paths])


def fail_result(validator_id: str, message: str, paths: list[Path], blocker_code: str = "UNKNOWN_BLOCKED") -> ValidatorResult:
    return ValidatorResult(validator_id, "FAIL", message, True, input_artifact_paths=[rel(path) for path in paths], blocker_code=blocker_code)


def blocked_result(validator_id: str, message: str, paths: list[Path], blocker_code: str) -> ValidatorResult:
    return ValidatorResult(validator_id, "BLOCKED", message, True, input_artifact_paths=[rel(path) for path in paths], blocker_code=blocker_code)


def _is_hash(value: str | None) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdefABCDEF" for char in value)


def authority_integrity_validator() -> ValidatorResult:
    paths = [ROOT / "TRADER_1.md", ROOT / "AGENTS.md", ROOT / "contracts" / "registry.yaml"]
    registry = load_json(paths[2])
    hashes = current_authority_hashes()
    authority = registry.get("authority", {})
    if authority.get("authority_sha256") != hashes["trader1_sha256"]:
        return fail_result("authority_integrity_validator", "registry TRADER_1 hash does not match current authority", paths, "SOURCE_IDENTITY_MISMATCH")
    if authority.get("agents_sha256") != hashes["agents_sha256"]:
        return fail_result("authority_integrity_validator", "registry AGENTS hash does not match current authority", paths, "SOURCE_IDENTITY_MISMATCH")
    if not _is_hash(authority.get("authority_sha256")) or not _is_hash(authority.get("agents_sha256")):
        return fail_result("authority_integrity_validator", "authority hash is missing or not a real sha256", paths, "SOURCE_IDENTITY_MISMATCH")
    return pass_result("authority_integrity_validator", "authority hashes match registry", paths)


def external_authority_manifest_validator() -> ValidatorResult:
    path = ROOT / "contracts" / "authority_manifest.json"
    manifest = load_json(path)
    hashes = current_authority_hashes()
    if manifest.get("trader1_md_sha256") != hashes["trader1_sha256"]:
        return fail_result("external_authority_manifest_validator", "manifest TRADER_1 hash is stale", [path], "SOURCE_IDENTITY_MISMATCH")
    if manifest.get("agents_md_sha256") != hashes["agents_sha256"]:
        return fail_result("external_authority_manifest_validator", "manifest AGENTS hash is stale", [path], "SOURCE_IDENTITY_MISMATCH")
    stored_hash = manifest.get("manifest_sha256")
    manifest_without_hash = dict(manifest)
    manifest_without_hash.pop("manifest_sha256", None)
    if stored_hash != sha256_json(manifest_without_hash):
        return fail_result("external_authority_manifest_validator", "manifest self hash does not match policy", [path], "GENERATED_ARTIFACT_DIRTY")
    return pass_result("external_authority_manifest_validator", "external authority manifest is current", [path])


def registry_validator() -> ValidatorResult:
    path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(path)
    required_top = ["registry_schema_id", "project_id", "authority", "enums", "schemas", "validators", "live_defaults"]
    missing = [key for key in required_top if key not in registry]
    if missing:
        return fail_result("registry_validator", f"registry missing keys: {missing}", [path], "REGISTRY_DRIFT")
    live_defaults = registry["live_defaults"]
    if live_defaults.get("live_order_ready") or live_defaults.get("live_order_allowed") or live_defaults.get("can_live_trade"):
        return fail_result("registry_validator", "registry live defaults are not fail-closed", [path], "REGISTRY_DRIFT")
    for enum_name, enum_def in registry["enums"].items():
        if not isinstance(enum_def.get("values"), list) or not enum_def["values"]:
            return fail_result("registry_validator", f"enum has no concrete values: {enum_name}", [path], "REGISTRY_DRIFT")
        for value in enum_def["values"]:
            if not isinstance(value, str) or value in {"TBD", "TODO", "fill_me", "not_set"} or value.startswith("__"):
                return fail_result("registry_validator", f"enum contains placeholder: {enum_name}", [path], "REGISTRY_DRIFT")
    return pass_result("registry_validator", "registry parsed and fail-closed defaults are intact", [path])


def schema_validator() -> ValidatorResult:
    schema_dir = ROOT / "contracts" / "schema"
    paths = sorted(schema_dir.glob("*.schema.json"))
    if not paths:
        return fail_result("schema_validator", "schema bundle is missing", [schema_dir], "SCHEMA_IDENTITY_MISMATCH")
    for path in paths:
        schema = load_json(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            return fail_result("schema_validator", f"schema draft mismatch: {rel(path)}", [path], "SCHEMA_IDENTITY_MISMATCH")
        if schema.get("additionalProperties") is not False:
            return fail_result("schema_validator", f"schema is not closed by default: {rel(path)}", [path], "SCHEMA_IDENTITY_MISMATCH")
        if not schema.get("$id"):
            return fail_result("schema_validator", f"schema id missing: {rel(path)}", [path], "SCHEMA_IDENTITY_MISMATCH")
    return pass_result("schema_validator", f"{len(paths)} schema files parsed", paths)


def _registry_and_common_defs() -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    registry_path = ROOT / "contracts" / "registry.yaml"
    defs_path = ROOT / "contracts" / "schema" / "common.defs.schema.json"
    return load_json(registry_path), load_json(defs_path), registry_path, defs_path


def closed_enum_validator() -> ValidatorResult:
    registry, common_defs, registry_path, defs_path = _registry_and_common_defs()
    required = ["exchange", "market_type", "mode", "risk_profile", "no_trade_reason", "live_blocker_code", "patch_class"]
    defs = common_defs.get("$defs", {})
    for enum_name in required:
        registry_values = registry["enums"][enum_name]["values"]
        schema_values = defs.get(enum_name if enum_name != "validator_result_status" else "validator_status", {}).get("enum")
        if schema_values is None:
            return fail_result("closed_enum_validator", f"common defs missing enum: {enum_name}", [registry_path, defs_path], "REGISTRY_DRIFT")
        if set(schema_values) != set(registry_values):
            return fail_result("closed_enum_validator", f"common defs enum drift: {enum_name}", [registry_path, defs_path], "REGISTRY_DRIFT")
    return pass_result("closed_enum_validator", "registry-backed common enums are closed and synchronized", [registry_path, defs_path])


def common_defs_drift_validator() -> ValidatorResult:
    registry, common_defs, registry_path, defs_path = _registry_and_common_defs()
    blockers = registry["enums"]["live_blocker_code"]["values"]
    no_trade = registry["enums"]["no_trade_reason"]["values"]
    if blockers != no_trade:
        return fail_result("common_defs_drift_validator", "live blocker and no-trade projections diverged", [registry_path, defs_path], "REGISTRY_DRIFT")
    blocker_object = common_defs.get("$defs", {}).get("blocker_object", {})
    code = blocker_object.get("properties", {}).get("code", {})
    if code.get("enum") != blockers:
        return fail_result("common_defs_drift_validator", "blocker object code enum drifted from registry", [registry_path, defs_path], "REGISTRY_DRIFT")
    return pass_result("common_defs_drift_validator", "common blocker definitions match registry projections", [registry_path, defs_path])


def _schema_type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "null":
        return value is None
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "string":
        return isinstance(value, str)
    return True


def _path_label(path: Path) -> str:
    try:
        return rel(path)
    except ValueError:
        return path.as_posix()


def _patch_result_schema_error(schema: dict[str, Any], patch: dict[str, Any], patch_path: Path) -> str | None:
    label = _path_label(patch_path)
    required = set(schema.get("required", []))
    missing = sorted(required - set(patch))
    if missing:
        return f"{label} missing required fields: {missing}"
    properties = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        extra = sorted(set(patch) - set(properties))
        if extra:
            return f"{label} contains fields outside patch_result schema: {extra}"
    for key, value in patch.items():
        definition = properties.get(key)
        if definition is None:
            continue
        if "const" in definition and value != definition["const"]:
            return f"{label}::{key} const mismatch"
        if "enum" in definition and value not in definition["enum"]:
            return f"{label}::{key} enum mismatch"
        expected_type = definition.get("type")
        if expected_type is not None:
            expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
            if not any(_schema_type_matches(value, item) for item in expected_types):
                return f"{label}::{key} type mismatch"
        if isinstance(value, str) and "minLength" in definition and len(value) < definition["minLength"]:
            return f"{label}::{key} minLength mismatch"
        if isinstance(value, int) and not isinstance(value, bool) and "minimum" in definition and value < definition["minimum"]:
            return f"{label}::{key} minimum mismatch"
    return None


def patch_result_schema_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "patch_result.schema.json"
    schema = load_json(schema_path)
    patch_paths = _patch_result_paths()
    if not patch_paths:
        return fail_result("patch_result_schema_validator", "no patch_result artifacts found", [schema_path], "SCHEMA_IDENTITY_MISMATCH")
    invariant_checks = {
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "live_order_ready_after": False,
        "live_order_allowed_after": False,
        "can_live_trade_after": False,
    }
    forbidden_true_fields = (
        "optimizer_live_mutation_detected",
        "optimizer_live_order_allowed_after",
        "convergence_live_mutation_detected",
        "convergence_live_order_allowed_after",
        "scale_up_allowed_after",
    )
    for patch_path in patch_paths:
        patch = load_json(patch_path)
        schema_error = _patch_result_schema_error(schema, patch, patch_path)
        if schema_error is not None:
            return fail_result(
                "patch_result_schema_validator",
                f"patch result schema mismatch: {schema_error}",
                [schema_path, patch_path],
                "SCHEMA_IDENTITY_MISMATCH",
            )
        if patch.get("patch_class") == "LIVE_ENABLING_PATCH":
            return fail_result(
                "patch_result_schema_validator",
                f"unexpected LIVE_ENABLING_PATCH in current patch history: {rel(patch_path)}",
                [schema_path, patch_path],
                "LIVE_FINAL_GUARD_FAILED",
            )
        for key, expected in invariant_checks.items():
            if patch.get(key) != expected:
                return fail_result(
                    "patch_result_schema_validator",
                    f"patch invariant failed: {rel(patch_path)}::{key}",
                    [schema_path, patch_path],
                    "LIVE_FINAL_GUARD_FAILED",
                )
        for key in forbidden_true_fields:
            if _live_flag_is_true(patch.get(key)):
                return fail_result(
                    "patch_result_schema_validator",
                    f"patch live/scale guard invariant failed: {rel(patch_path)}::{key}",
                    [schema_path, patch_path],
                    "LIVE_FINAL_GUARD_FAILED",
                )
    return pass_result(
        "patch_result_schema_validator",
        f"{len(patch_paths)} patch_result artifacts satisfy schema, required fields, and non-live invariants",
        [schema_path] + patch_paths,
    )


def _patch_result_instance_errors(
    patch: dict[str, Any],
    patch_path: Path,
    schema_bundle: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    schema = schema_for_instance(patch, schema_bundle)
    label = _path_label(patch_path)
    if schema is None or schema.get("$id") != "trader1.patch_result.v1":
        return [f"{label}: no patch_result schema matched schema_id"]

    result = validate_instance_against_schema(patch, schema, schema_bundle)
    if result.status != "PASS":
        return [f"{label}: {item}" for item in result.errors]

    invariant_checks = {
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "live_order_ready_after": False,
        "live_order_allowed_after": False,
        "can_live_trade_after": False,
        "scale_up_allowed_after": False,
    }
    if patch.get("patch_class") == "LIVE_ENABLING_PATCH":
        errors.append(f"{label}: LIVE_ENABLING_PATCH is forbidden in MVP-4 audit scope")
    for key, expected in invariant_checks.items():
        if patch.get(key) != expected:
            errors.append(f"{label}: invariant mismatch for {key}")
    for key in (
        "optimizer_live_mutation_detected",
        "optimizer_live_order_allowed_after",
        "convergence_live_mutation_detected",
        "convergence_live_order_allowed_after",
    ):
        if _live_flag_is_true(patch.get(key)):
            errors.append(f"{label}: forbidden true value for {key}")
    return errors


def _patch_result_validator_run_gaps(patch: dict[str, Any], patch_path: Path) -> list[dict[str, Any]]:
    required = [item for item in patch.get("validators_required", []) if isinstance(item, str)]
    run_entries = patch.get("validators_run", [])
    run_status_by_id: dict[str, str] = {}
    if isinstance(run_entries, list):
        for entry in run_entries:
            if isinstance(entry, dict) and isinstance(entry.get("validator_id"), str):
                run_status_by_id[entry["validator_id"]] = str(entry.get("status", "UNKNOWN"))

    gaps: list[dict[str, Any]] = []
    for validator_id in sorted(set(required)):
        status = run_status_by_id.get(validator_id)
        if status is None:
            gaps.append({"patch_result_path": rel(patch_path), "validator_id": validator_id, "gap_type": "MISSING_VALIDATOR_RUN"})
        elif status in {"UNTESTED", "STALE", "TIMEOUT"}:
            gaps.append(
                {
                    "patch_result_path": rel(patch_path),
                    "validator_id": validator_id,
                    "gap_type": f"UNUSABLE_VALIDATOR_STATUS:{status}",
                }
            )
    return gaps


def _load_patch_result_gap_audit(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        audit = load_json(path)
    except Exception:
        return None
    return audit if isinstance(audit, dict) else None


def _audit_gap_key(gap: dict[str, Any]) -> tuple[str, str, str]:
    return (str(gap.get("patch_result_path")), str(gap.get("validator_id")), str(gap.get("gap_type")))


def _patch_result_unbaselined_gaps(gaps: list[dict[str, Any]], baseline_gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline_keys = {
        _audit_gap_key(item)
        for item in baseline_gaps
        if isinstance(item, dict)
    }
    return [gap for gap in gaps if _audit_gap_key(gap) not in baseline_keys]


def patch_result_runtime_schema_instance_validator() -> ValidatorResult:
    schema_dir = ROOT / "contracts" / "schema"
    schema_path = schema_dir / "patch_result.schema.json"
    audit_path = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json"
    baseline_path = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE.json"
    contract_gap_path = ROOT / "system" / "evidence" / "contract_gaps" / "PATCH_RESULT_VALIDATOR_RUN_GAP.contract_gap.json"
    patch_paths = _patch_result_paths()
    paths = [schema_path, audit_path, baseline_path, contract_gap_path] + patch_paths
    if not patch_paths:
        return fail_result(
            "patch_result_runtime_schema_instance_validator",
            "no patch_result artifacts found for runtime schema validation",
            [schema_path],
            "SCHEMA_IDENTITY_MISMATCH",
        )

    schema_bundle = load_schema_bundle(schema_dir)
    gaps: list[dict[str, Any]] = []
    for patch_path in patch_paths:
        patch = load_json(patch_path)
        instance_errors = _patch_result_instance_errors(patch, patch_path, schema_bundle)
        if instance_errors:
            return fail_result(
                "patch_result_runtime_schema_instance_validator",
                instance_errors[0],
                paths,
                "SCHEMA_IDENTITY_MISMATCH",
            )
        gaps.extend(_patch_result_validator_run_gaps(patch, patch_path))

    if gaps:
        audit = _load_patch_result_gap_audit(audit_path)
        baseline = _load_patch_result_gap_audit(baseline_path)
        contract_gap = _load_patch_result_gap_audit(contract_gap_path)
        if audit is None or baseline is None or contract_gap is None:
            return blocked_result(
                "patch_result_runtime_schema_instance_validator",
                f"{len(gaps)} patch_result validator-run gaps require audit, baseline, and contract_gap artifacts",
                paths,
                "CONTRACT_GAP_HIGH",
            )
        baseline_gaps = [item for item in baseline.get("gaps", []) if isinstance(item, dict)]
        unbaselined = _patch_result_unbaselined_gaps(gaps, baseline_gaps)
        if unbaselined:
            return blocked_result(
                "patch_result_runtime_schema_instance_validator",
                f"{len(unbaselined)} patch_result validator-run gaps are not in the sealed historical baseline",
                paths,
                "CONTRACT_GAP_HIGH",
            )
        documented = {
            _audit_gap_key(item)
            for item in audit.get("gaps", [])
            if isinstance(item, dict) and item.get("resolution") == "AUDIT_PRESERVED_NOT_BACKFILLED"
        }
        discovered = {_audit_gap_key(item) for item in gaps}
        if discovered != documented:
            return blocked_result(
                "patch_result_runtime_schema_instance_validator",
                "patch_result validator-run gap audit is stale or incomplete",
                paths,
                "CONTRACT_GAP_HIGH",
            )
        baseline_keys = {_audit_gap_key(item) for item in baseline_gaps}
        if discovered != baseline_keys:
            return blocked_result(
                "patch_result_runtime_schema_instance_validator",
                "patch_result validator-run baseline does not match discovered preserved gaps",
                paths,
                "CONTRACT_GAP_HIGH",
            )
        if contract_gap.get("status") not in {"OPEN", "BLOCKED"} or contract_gap.get("severity") not in {"MEDIUM", "HIGH", "CRITICAL"}:
            return blocked_result(
                "patch_result_runtime_schema_instance_validator",
                "patch_result validator-run contract_gap is not active",
                paths,
                "CONTRACT_GAP_HIGH",
            )

    return pass_result(
        "patch_result_runtime_schema_instance_validator",
        f"{len(patch_paths)} patch_result artifacts match schema; {len(gaps)} legacy validator-run gaps are audit-preserved and live-blocking",
        paths,
    )


def coverage_index_validator() -> ValidatorResult:
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    index = load_json(index_path)
    matrix = load_json(matrix_path)
    rows_by_requirement = {row["requirement_id"]: row for row in matrix.get("rows", [])}
    for req in index.get("requirements", []):
        row = rows_by_requirement.get(req["requirement_id"])
        if row is None:
            return fail_result("coverage_index_validator", f"requirement lacks artifact matrix row: {req['requirement_id']}", [index_path, matrix_path], "CONTRACT_GAP_HIGH")
        if req.get("live_affecting") and (not req.get("validator_ids") or not req.get("test_ids")):
            return blocked_result("coverage_index_validator", f"live-affecting requirement lacks validator or test: {req['requirement_id']}", [index_path, matrix_path], "CONTRACT_GAP_HIGH")
    return pass_result("coverage_index_validator", "mapped requirements have artifact rows and live-affecting entries keep validators/tests", [index_path, matrix_path])


def active_schema_extraction_validator() -> ValidatorResult:
    map_path = ROOT / "contracts" / "generated" / "authority_section_map.json"
    section_map = load_json(map_path)
    section_ids = {section["section_id"]: section for section in section_map.get("sections", [])}
    required = {"SECTION_SCHEMA_CONTRACTS", "SECTION_SCHEMA_COMMON_DEFS", "SECTION_REGISTRY_SEED"}
    if missing := sorted(required - set(section_ids)):
        return fail_result("active_schema_extraction_validator", f"schema extraction section map missing: {missing}", [map_path], "GENERATED_ARTIFACT_DIRTY")
    if section_map.get("retained_archive_read") or section_map.get("full_document_read"):
        return fail_result("active_schema_extraction_validator", "schema extraction used forbidden broad read state", [map_path], "GENERATED_ARTIFACT_DIRTY")
    return pass_result("active_schema_extraction_validator", "schema extraction is mapped to active sections only", [map_path])


def generated_artifact_dirty_validator() -> ValidatorResult:
    manifest_path = ROOT / "contracts" / "generated" / "read_cache_manifest.json"
    manifest = load_json(manifest_path)
    hashes = current_authority_hashes()
    if manifest.get("trader1_sha256") != hashes["trader1_sha256"] or manifest.get("agents_sha256") != hashes["agents_sha256"]:
        return fail_result("generated_artifact_dirty_validator", "read cache authority hashes are stale", [manifest_path], "GENERATED_ARTIFACT_DIRTY")
    checks = {
        "authority_section_map_sha256": ROOT / "contracts" / "generated" / "authority_section_map.json",
        "requirement_index_sha256": ROOT / "contracts" / "generated" / "requirement_index.json",
        "requirement_artifact_matrix_sha256": ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json",
        "registry_yaml_sha256_when_generated": ROOT / "contracts" / "registry.yaml",
        "active_working_view_sha256": ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
        "current_implementation_state_sha256": ROOT / "contracts" / "generated" / "current_implementation_state.json",
    }
    for key, path in checks.items():
        current_hash = sha256_file(path) if key == "registry_yaml_sha256_when_generated" else sha256_text_file_canonical(path)
        if manifest.get(key) != current_hash:
            return fail_result("generated_artifact_dirty_validator", f"read cache hash mismatch: {key}", [manifest_path, path], "GENERATED_ARTIFACT_DIRTY")
    for pack_path, expected_hash in manifest.get("context_pack_hashes", {}).items():
        path = ROOT / pack_path
        if expected_hash != sha256_text_file_canonical(path):
            return fail_result("generated_artifact_dirty_validator", f"context pack hash mismatch: {pack_path}", [manifest_path, path], "GENERATED_ARTIFACT_DIRTY")
    return pass_result("generated_artifact_dirty_validator", "generated read cache hashes match current artifacts", [manifest_path])


def live_blocked_negative_matrix_validator() -> ValidatorResult:
    matrix_path = ROOT / "tests" / "live_blocked" / "fixtures" / "live_blocked_matrix.json"
    matrix = load_json(matrix_path)
    cases = matrix.get("cases", [])
    case_ids = {case.get("case_id") for case in cases}
    if case_ids != set(BLOCKED_CASES):
        return fail_result("live_blocked_negative_matrix_validator", "live-blocked matrix does not cover required blocker cases", [matrix_path], "LIVE_FINAL_GUARD_FAILED")
    for case in cases:
        decision = evaluate_live_order_gate(
            {
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "blocker_code": case["blocker_code"],
            }
        )
        if decision.order_adapter_called:
            return fail_result("live_blocked_negative_matrix_validator", f"order adapter would be called for {case['case_id']}", [matrix_path], case["blocker_code"])
        if decision.primary_blocker_code != case["blocker_code"]:
            return fail_result("live_blocked_negative_matrix_validator", f"blocker mismatch for {case['case_id']}", [matrix_path], "LIVE_FINAL_GUARD_FAILED")
    return pass_result("live_blocked_negative_matrix_validator", f"{len(cases)} live-blocked cases keep order adapter uncalled", [matrix_path])


def live_blocked_scaffold_validator() -> ValidatorResult:
    fixture_path = ROOT / "tests" / "live_blocked" / "fixtures" / "live_ready_missing.json"
    matrix_path = ROOT / "tests" / "live_blocked" / "fixtures" / "live_blocked_matrix.json"
    fixture = load_json(fixture_path)
    required = {
        "fixture_id",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "expected_order_adapter_called",
        "expected_final_decision",
        "expected_blocker_code",
    }
    missing = sorted(required - set(fixture))
    if missing:
        return fail_result("live_blocked_scaffold_validator", f"live blocked fixture missing fields: {missing}", [fixture_path], "SCHEMA_IDENTITY_MISMATCH")
    decision = evaluate_live_order_gate(
        {
            "live_order_ready": fixture["live_order_ready"],
            "live_order_allowed": fixture["live_order_allowed"],
            "can_live_trade": fixture["can_live_trade"],
            "blocker_code": fixture["expected_blocker_code"],
        }
    )
    if decision.order_adapter_called or fixture["expected_order_adapter_called"]:
        return fail_result("live_blocked_scaffold_validator", "live blocked scaffold allowed order adapter call", [fixture_path], "LIVE_FINAL_GUARD_FAILED")
    if decision.final_decision != fixture["expected_final_decision"]:
        return fail_result("live_blocked_scaffold_validator", "live blocked scaffold final decision mismatch", [fixture_path], "LIVE_FINAL_GUARD_FAILED")
    if decision.primary_blocker_code != fixture["expected_blocker_code"]:
        return fail_result("live_blocked_scaffold_validator", "live blocked scaffold blocker mismatch", [fixture_path], "LIVE_FINAL_GUARD_FAILED")
    matrix_result = live_blocked_negative_matrix_validator()
    if matrix_result.status != "PASS":
        return ValidatorResult(
            "live_blocked_scaffold_validator",
            matrix_result.status,
            f"negative matrix dependency failed: {matrix_result.message}",
            True,
            input_artifact_paths=[rel(fixture_path), rel(matrix_path)],
            blocker_code=matrix_result.blocker_code,
        )
    return pass_result("live_blocked_scaffold_validator", "live blocked scaffold and negative matrix block order adapter", [fixture_path, matrix_path])


def source_bundle_hygiene_validator() -> ValidatorResult:
    manifest = write_source_bundle_manifest()
    denylist = load_denylist()
    paths = [ROOT / "contracts" / "security" / "source_bundle_denylist.json", ROOT / "contracts" / "security" / "source_bundle_manifest.json"]
    if manifest.get("forbidden_count") != denylist.get("source_forbidden_count_required", 0):
        return fail_result("source_bundle_hygiene_validator", "source bundle forbidden_count is not zero", paths, "BUNDLE_HYGIENE_FAIL")
    if manifest.get("live_order_ready") or manifest.get("live_order_allowed") or manifest.get("can_live_trade"):
        return fail_result("source_bundle_hygiene_validator", "source bundle manifest attempted to set live readiness", paths, "BUNDLE_HYGIENE_FAIL")
    for item in manifest.get("included_files", []):
        decision = classify_path(item["path"], denylist)
        if not decision.include:
            return fail_result("source_bundle_hygiene_validator", f"source bundle includes forbidden path: {item['path']}", paths, "BUNDLE_HYGIENE_FAIL")
    return pass_result("source_bundle_hygiene_validator", f"source bundle candidate excludes forbidden paths; included={len(manifest.get('included_files', []))}", paths)


def shipped_package_hygiene_validator() -> ValidatorResult:
    manifest = write_source_bundle_manifest()
    paths = [ROOT / "contracts" / "security" / "source_bundle_denylist.json", ROOT / "contracts" / "security" / "source_bundle_manifest.json"]
    shipped_forbidden_files = manifest.get("shipped_forbidden_files", [])
    if manifest.get("shipped_forbidden_count", manifest.get("forbidden_count", 0)) != 0 or shipped_forbidden_files:
        sample = ", ".join(item.get("path", "<unknown>") for item in shipped_forbidden_files[:5] if isinstance(item, dict))
        message = "shipped package contains forbidden cache/secret-shaped files"
        if sample:
            message = f"{message}: {sample}"
        return fail_result("shipped_package_hygiene_validator", message, paths, "BUNDLE_HYGIENE_FAIL")
    return pass_result("shipped_package_hygiene_validator", "shipped package has no bytecode cache or secret-shaped forbidden files", paths)


def secret_scan_validator() -> ValidatorResult:
    manifest = load_source_bundle_manifest()
    path = ROOT / "contracts" / "security" / "source_bundle_manifest.json"
    if manifest.get("contains_secret") or manifest.get("secret_findings"):
        return fail_result("secret_scan_validator", "source bundle candidate contains credential-like material", [path], "BUNDLE_HYGIENE_FAIL")
    return pass_result("secret_scan_validator", "source bundle candidate has no credential-like findings", [path])


def bytecode_free_syntax_validator() -> ValidatorResult:
    paths = [
        ROOT / "trader1" / "validation" / "bytecode_free_syntax.py",
        ROOT / "tools" / "run_bytecode_free_syntax_check.py",
        ROOT / "contracts" / "schema" / "bytecode_free_syntax_report.schema.json",
    ]
    report = build_bytecode_free_syntax_report(root=ROOT, scan_paths=["trader1", "tools", "tests"])
    result = validate_bytecode_free_syntax_report(report)
    if result.status != "PASS":
        return fail_result("bytecode_free_syntax_validator", result.message, paths, result.blocker_code or "RUNTIME_REPRODUCIBILITY_GAP")
    return pass_result(
        "bytecode_free_syntax_validator",
        f"bytecode-free syntax check passed for {report.get('files_checked')} Python files without __pycache__ writes",
        paths,
    )


def path_namespace_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(registry_path)
    scope = NamespaceScope(exchange="UPBIT", market_type="KRW_SPOT", mode="PAPER", session_id="session_mvp0")
    paths = [
        artifact_path("data", scope, registry, "ticks.jsonl"),
        artifact_path("runtime", scope, registry, "engine_state.json"),
        artifact_path("reports", scope, registry, "summary.json"),
        artifact_path("validation", scope, registry, "validator_result.json"),
        artifact_path("evidence", scope, registry, "evidence_manifest.json"),
        artifact_path("snapshots", scope, registry, "live_ready_snapshot.json"),
    ]
    for candidate in paths:
        result = validate_artifact_path(candidate, scope, registry)
        if result.status != "PASS":
            return fail_result("path_namespace_validator", result.message, [registry_path], result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH")
    mixed_mode = validate_namespace_join(scope, NamespaceScope(exchange="UPBIT", market_type="KRW_SPOT", mode="LIVE", session_id="session_mvp0"))
    if mixed_mode.status != "BLOCKED":
        return fail_result("path_namespace_validator", "paper/live namespace join was not blocked", [registry_path], "SNAPSHOT_SCOPE_MISMATCH")
    mixed_exchange = validate_namespace_join(scope, NamespaceScope(exchange="BINANCE", market_type="KRW_SPOT", mode="PAPER", session_id="session_mvp0"))
    if mixed_exchange.status != "BLOCKED":
        return fail_result("path_namespace_validator", "upbit/binance namespace join was not blocked", [registry_path], "SNAPSHOT_SCOPE_MISMATCH")
    return pass_result("path_namespace_validator", "artifact paths are namespace scoped and cross-scope joins are blocked", [registry_path])


def truth_hierarchy_validator() -> ValidatorResult:
    summary_role = classify_dashboard_artifact("summary.json")
    if summary_role != "dashboard_serving_truth":
        return fail_result("truth_hierarchy_validator", "summary.json was not classified as dashboard serving truth", [], "LIVE_FINAL_GUARD_FAILED")
    blocked = validate_truth_override("dashboard_serving_truth", "execution_truth")
    if blocked.status != "BLOCKED":
        return fail_result("truth_hierarchy_validator", "dashboard truth override of execution truth was not blocked", [], "LIVE_FINAL_GUARD_FAILED")
    allowed = validate_truth_override("execution_truth", "dashboard_serving_truth")
    if allowed.status != "PASS":
        return fail_result("truth_hierarchy_validator", "execution truth could not feed dashboard serving truth", [], "LIVE_FINAL_GUARD_FAILED")
    return pass_result("truth_hierarchy_validator", "truth hierarchy blocks dashboard override of execution truth", [])


def single_writer_order_path_validator() -> ValidatorResult:
    paths = [ROOT / "trader1" / "execution" / "live_order_gateway.py"]
    safe_request = {
        "source_kind": "FinalDecision",
        "final_decision": "ENTER_LONG",
        "client_order_id": "mvp0-validator-client",
        "single_writer_available": True,
        "budget_reserved": True,
        "local_reservation_committed": True,
        "ledger_reconciled": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    blocked = evaluate_live_order_path(safe_request)
    if blocked.order_adapter_called or blocked.external_submit_attempted:
        return fail_result("single_writer_order_path_validator", "order path attempted adapter call without live readiness", paths, "LIVE_FINAL_GUARD_FAILED")
    if blocked.primary_blocker_code != "LIVE_READY_MISSING":
        return fail_result("single_writer_order_path_validator", "live-ready missing did not remain the primary blocker", paths, "LIVE_READY_MISSING")

    ambiguous = evaluate_live_order_path(
        {
            **safe_request,
            "original_client_order_id": "original-id",
            "client_order_id": "new-id",
            "idempotency_state": "PENDING_CONFIRM",
            "new_identifier_proposed": True,
        }
    )
    if "RECONCILIATION_REQUIRED" not in ambiguous.blockers or ambiguous.order_adapter_called:
        return fail_result("single_writer_order_path_validator", "ambiguous submit did not force same-identifier reconciliation", paths, "RECONCILIATION_REQUIRED")
    ambiguous_same_identifier = evaluate_live_order_path(
        {
            **safe_request,
            "original_client_order_id": "same-id",
            "client_order_id": "same-id",
            "idempotency_state": "TRANSPORT_AMBIGUOUS",
        }
    )
    if (
        ambiguous_same_identifier.primary_blocker_code != "RECONCILIATION_REQUIRED"
        or ambiguous_same_identifier.final_decision != "RECONCILE_REQUIRED"
        or ambiguous_same_identifier.order_adapter_called
    ):
        return fail_result(
            "single_writer_order_path_validator",
            "ambiguous same-identifier transport state did not force reconciliation before submit",
            paths,
            "RECONCILIATION_REQUIRED",
        )
    ambiguous_missing_original = evaluate_live_order_path(
        {
            **safe_request,
            "client_order_id": "missing-original-id",
            "idempotency_state": "PENDING_CONFIRM",
        }
    )
    if (
        ambiguous_missing_original.primary_blocker_code != "RECONCILIATION_REQUIRED"
        or ambiguous_missing_original.final_decision != "RECONCILE_REQUIRED"
        or ambiguous_missing_original.order_adapter_called
    ):
        return fail_result(
            "single_writer_order_path_validator",
            "ambiguous transport state without original identifier did not force reconciliation before submit",
            paths,
            "RECONCILIATION_REQUIRED",
        )
    prior_submit_attempt = evaluate_live_order_path({**safe_request, "order_adapter_submit_attempted": True})
    if (
        not prior_submit_attempt.external_submit_attempted
        or "LIVE_FINAL_GUARD_FAILED" not in prior_submit_attempt.blockers
        or prior_submit_attempt.order_adapter_called
    ):
        return fail_result(
            "single_writer_order_path_validator",
            "prior adapter submit attempt evidence was not surfaced as live-final-guard failure",
            paths,
            "LIVE_FINAL_GUARD_FAILED",
        )
    return pass_result("single_writer_order_path_validator", "single-writer/idempotent order path blocks before adapter submit", paths)


def strategy_direct_order_validator() -> ValidatorResult:
    paths = [ROOT / "trader1" / "execution" / "live_order_gateway.py"]
    decision = evaluate_live_order_path(
        {
            "source_kind": "StrategySignal",
            "final_decision": "ENTER_LONG",
            "strategy_attempted_exchange_call": True,
            "client_order_id": "strategy-direct-attempt",
            "single_writer_available": True,
            "budget_reserved": True,
            "local_reservation_committed": True,
            "ledger_reconciled": True,
        }
    )
    if decision.order_adapter_called:
        return fail_result("strategy_direct_order_validator", "strategy-originated signal reached order adapter", paths, "CANDIDATE_DIRECT_LIVE_FORBIDDEN")
    if not decision.direct_strategy_order_blocked or decision.primary_blocker_code != "CANDIDATE_DIRECT_LIVE_FORBIDDEN":
        return fail_result("strategy_direct_order_validator", "strategy direct order attempt was not blocked", paths, "CANDIDATE_DIRECT_LIVE_FORBIDDEN")
    return pass_result("strategy_direct_order_validator", "strategy signals cannot place orders or call exchange APIs directly", paths)


def readiness_surface_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    module_path = ROOT / "trader1" / "runtime" / "readiness" / "readiness_surface.py"
    registry = load_json(registry_path)
    allowed_codes = set(registry["enums"]["live_blocker_code"]["values"])
    surface = build_readiness_surface(
        authority=current_authority_hashes(),
        registry_hash=sha256_file(registry_path),
        can_start=True,
        can_collect_data=True,
        can_live_review=True,
    )
    result = validate_readiness_surface(surface, allowed_codes)
    if result.status != "PASS":
        return fail_result("readiness_surface_validator", result.message, [registry_path, module_path], result.blocker_code or "LIVE_FINAL_GUARD_FAILED")
    if surface.get("live_order_ready") or surface.get("live_order_allowed") or surface.get("can_live_trade"):
        return fail_result("readiness_surface_validator", "readiness surface created live permission", [module_path], "LIVE_FINAL_GUARD_FAILED")
    if surface.get("primary_blocker_code") != "LIVE_READY_MISSING":
        return fail_result("readiness_surface_validator", "default readiness surface did not expose LIVE_READY_MISSING", [module_path], "LIVE_READY_MISSING")

    invalid = dict(surface)
    invalid["live_order_ready"] = True
    invalid["live_order_allowed"] = True
    invalid["can_live_trade"] = True
    invalid["live_trading_status"] = "LIVE_ACTIVE"
    invalid["surface_hash"] = surface_hash(invalid)
    invalid_result = validate_readiness_surface(invalid, allowed_codes)
    if invalid_result.status != "BLOCKED":
        return fail_result("readiness_surface_validator", "live blocker did not block live_order_allowed=true", [module_path], "LIVE_FINAL_GUARD_FAILED")
    return pass_result("readiness_surface_validator", "readiness surface stays fail-closed and scoped blocker text is present", [module_path])


def root_launcher_guard_validator() -> ValidatorResult:
    paths = [ROOT, ROOT / "trader1" / "runtime" / "boot" / "launcher_guard.py"]
    result = inspect_root_launchers(ROOT)
    if result.status == "PASS":
        return pass_result("root_launcher_guard_validator", result.message, paths)
    if result.status == "BLOCKED":
        return blocked_result(
            "root_launcher_guard_validator",
            result.message,
            paths,
            result.primary_blocker_code or "CONTRACT_GAP_HIGH",
        )
    return fail_result(
        "root_launcher_guard_validator",
        result.message,
        paths,
        result.primary_blocker_code or "CONTRACT_GAP_HIGH",
    )


def root_launcher_surface_validator() -> ValidatorResult:
    paths = [
        ROOT,
        ROOT / "UPBIT_PAPER.py",
        ROOT / "UPBIT_LIVE.py",
        ROOT / "BINANCE_PAPER.py",
        ROOT / "BINANCE_LIVE.py",
        ROOT / "trader1" / "runtime" / "boot" / "safe_launcher.py",
        ROOT / "contracts" / "schema" / "root_launcher_report.schema.json",
    ]
    result = inspect_root_launchers(ROOT, require_exact_four=True)
    if result.status != "PASS":
        return blocked_result(
            "root_launcher_surface_validator",
            result.message,
            paths,
            result.primary_blocker_code or "CONTRACT_GAP_HIGH",
        )
    if set(result.root_launchers_found) != set(ALLOWED_ROOT_LAUNCHERS):
        return fail_result("root_launcher_surface_validator", "root launcher surface is not exactly four launchers", paths, "CONTRACT_GAP_HIGH")

    for launcher_name in sorted(ALLOWED_ROOT_LAUNCHERS):
        report = build_launcher_report(launcher_name)
        report_result = validate_launcher_report(report)
        if report_result.status != "PASS":
            return blocked_result(
                "root_launcher_surface_validator",
                report_result.message,
                paths,
                report_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
            )
        if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade"):
            return fail_result("root_launcher_surface_validator", f"launcher report created live permission: {launcher_name}", paths, "LIVE_FINAL_GUARD_FAILED")
    return pass_result("root_launcher_surface_validator", "root launcher surface exposes exactly four safe fail-closed launchers", paths)


def binance_adapter_surface_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "binance_adapter_surface_report.schema.json"
    module_path = ROOT / "trader1" / "adapters" / "binance" / "surface.py"
    test_path = ROOT / "tests" / "adapter" / "test_binance_adapter_surface.py"
    paths = [schema_path, module_path, test_path, ROOT / "trader1" / "runtime" / "boot" / "safe_launcher.py"]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.binance_adapter_surface_report.v1":
        return fail_result("binance_adapter_surface_validator", "Binance adapter surface schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("binance_adapter_surface_validator", "Binance adapter surface schema must reject unknown fields", paths, "SCHEMA_IDENTITY_MISMATCH")

    spot_paper = build_binance_adapter_surface_report(market_type="SPOT", mode="PAPER", session_id="validator-binance-spot-paper")
    spot_result = validate_binance_adapter_surface_report(spot_paper)
    if spot_result.status != "PASS" or spot_paper.get("adapter_status") != "SURFACE_ONLY":
        return fail_result("binance_adapter_surface_validator", "Binance SPOT PAPER surface did not validate as surface-only", paths, spot_result.blocker_code or "CONTRACT_GAP_HIGH")

    futures_paper = build_binance_adapter_surface_report(market_type="FUTURES_USDT_M", mode="PAPER", session_id="validator-binance-futures-paper")
    futures_result = validate_binance_adapter_surface_report(futures_paper)
    if futures_result.status != "PASS" or futures_paper.get("adapter_status") != "BLOCKED":
        return fail_result("binance_adapter_surface_validator", "Binance futures surface did not remain blocked/not implemented", paths, futures_result.blocker_code or "CONTRACT_GAP_HIGH")

    live_mutation = dict(spot_paper)
    live_mutation["live_order_allowed"] = True
    live_mutation["report_hash"] = binance_adapter_surface_hash(live_mutation)
    live_result = validate_binance_adapter_surface_report(live_mutation)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("binance_adapter_surface_validator", "Binance surface live mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    credential_mutation = dict(spot_paper)
    credential_mutation["credentials_loaded"] = True
    credential_mutation["report_hash"] = binance_adapter_surface_hash(credential_mutation)
    credential_result = validate_binance_adapter_surface_report(credential_mutation)
    if credential_result.status != "BLOCKED" or credential_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("binance_adapter_surface_validator", "Binance surface credential mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    for launcher_name in ("BINANCE_PAPER", "BINANCE_LIVE"):
        launcher_report = build_launcher_report(launcher_name)
        launcher_result = validate_launcher_report(launcher_report)
        if launcher_result.status != "PASS":
            return fail_result("binance_adapter_surface_validator", f"{launcher_name} launcher did not validate", paths, launcher_result.blocker_code or "CONTRACT_GAP_HIGH")
        if launcher_report.get("blocking_reason") != "BINANCE_ADAPTER_SURFACE_ONLY":
            return fail_result("binance_adapter_surface_validator", f"{launcher_name} does not surface Binance adapter blocker", paths, "CONTRACT_GAP_HIGH")
        if "FUTURES_USDT_M remains blocked" not in launcher_report.get("next_action", ""):
            return fail_result("binance_adapter_surface_validator", f"{launcher_name} does not disclose blocked futures market_type boundary", paths, "CONTRACT_GAP_HIGH")
        if launcher_report.get("live_order_allowed") or launcher_report.get("can_live_trade"):
            return fail_result("binance_adapter_surface_validator", f"{launcher_name} created live capability", paths, "LIVE_FINAL_GUARD_FAILED")

    return pass_result("binance_adapter_surface_validator", "Binance adapter namespace is explicit surface-only and live-blocked", paths)


def runtime_config_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    schema_path = ROOT / "contracts" / "schema" / "runtime_config.schema.json"
    module_path = ROOT / "trader1" / "config" / "config_schema.py"
    paths = [registry_path, schema_path, module_path]
    registry = load_json(registry_path)
    registry_hash = sha256_file(registry_path)
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp0_config_validator",
        registry_hash=registry_hash,
    )
    result = validate_runtime_config(config, registry, expected_registry_hash=registry_hash)
    if result.status != "PASS":
        return blocked_result(
            "runtime_config_validator",
            result.message,
            paths,
            result.primary_blocker_code or "PREFLIGHT_FAILED",
        )

    unsafe = dict(config)
    unsafe["live_order_allowed"] = True
    unsafe = attach_config_hash(unsafe)
    unsafe_result = validate_runtime_config(unsafe, registry, expected_registry_hash=registry_hash)
    if unsafe_result.status != "BLOCKED" or unsafe_result.primary_blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("runtime_config_validator", "live-enabling config mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")
    return pass_result("runtime_config_validator", "runtime config schema scaffold is fail-closed", paths)


def live_ready_snapshot_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    schema_path = ROOT / "contracts" / "schema" / "live_ready_snapshot.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "readiness" / "live_ready_snapshot.py"
    paths = [registry_path, schema_path, module_path]
    registry_hash = sha256_file(registry_path)
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    schema_bundle_hash = sha256_json({rel(path): sha256_file(path) for path in schema_files})
    source_tree_hash = sha256_json(
        {
            rel(path): sha256_file(path)
            for path in sorted((ROOT / "trader1").rglob("*.py"))
            if "__pycache__" not in path.parts
        }
    )
    snapshot = build_blocked_live_ready_snapshot(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        snapshot_id="validator-live-ready-blocked-snapshot",
    )
    result = validate_live_ready_snapshot(snapshot)
    if result.status != "PASS":
        return fail_result("live_ready_snapshot_validator", f"blocked snapshot scaffold did not validate: {result.message}", paths, result.blocker_code or "LIVE_READY_SNAPSHOT_WRITER_FAILED")
    if result.live_order_ready or result.live_order_allowed or result.can_live_trade:
        return fail_result("live_ready_snapshot_validator", "blocked snapshot scaffold drifted into live permission", paths, "LIVE_FINAL_GUARD_FAILED")

    missing_field = dict(snapshot)
    missing_field.pop("snapshot_id", None)
    missing_result = validate_live_ready_snapshot(missing_field)
    if missing_result.status != "BLOCKED" or missing_result.blocker_code != "LIVE_READY_SNAPSHOT_WRITER_FAILED":
        return fail_result("live_ready_snapshot_validator", "missing required snapshot field was not blocked", paths, missing_result.blocker_code or "LIVE_READY_SNAPSHOT_WRITER_FAILED")

    allowed_without_ready = dict(snapshot)
    allowed_without_ready["live_order_allowed"] = True
    allowed_without_ready_result = validate_live_ready_snapshot(allowed_without_ready)
    if allowed_without_ready_result.status != "BLOCKED" or allowed_without_ready_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("live_ready_snapshot_validator", "live_order_allowed without live_ready=true was not blocked", paths, allowed_without_ready_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    missing_official_api = dict(snapshot)
    missing_official_api["live_ready"] = True
    missing_official_api["live_order_allowed"] = True
    missing_official_api_result = validate_live_ready_snapshot(missing_official_api)
    if missing_official_api_result.status != "BLOCKED" or missing_official_api_result.blocker_code != "API_UNVERIFIED":
        return fail_result("live_ready_snapshot_validator", "snapshot without official API evidence was not blocked", paths, missing_official_api_result.blocker_code or "API_UNVERIFIED")

    ready_without_order_permission = dict(snapshot)
    ready_without_order_permission["live_ready"] = True
    ready_without_order_permission["live_order_allowed"] = False
    ready_without_order_permission_result = validate_live_ready_snapshot(ready_without_order_permission)
    if ready_without_order_permission_result.status != "BLOCKED" or ready_without_order_permission_result.blocker_code != "API_UNVERIFIED":
        return fail_result("live_ready_snapshot_validator", "live_ready=true without live_order_allowed still bypassed evidence checks", paths, ready_without_order_permission_result.blocker_code or "API_UNVERIFIED")

    stale_rollup = dict(snapshot)
    stale_rollup.update(
        {
            "live_ready": True,
            "live_order_allowed": True,
            "official_api_verification_id": "official-api-placeholder",
            "manual_order_test_required": False,
            "operator_approval_required": False,
            "read_only_burn_in_id": "read-only-burn-in-placeholder",
            "emergency_protection_evidence_id": "emergency-protection-placeholder",
            "invalidated_by": [],
            "validator_rollup_status": "UNTESTED",
        }
    )
    stale_rollup_result = validate_live_ready_snapshot(stale_rollup)
    if stale_rollup_result.status != "BLOCKED" or stale_rollup_result.blocker_code != "LIVE_READY_SNAPSHOT_WRITER_FAILED":
        return fail_result("live_ready_snapshot_validator", "UNTESTED validator rollup did not block live_order_allowed snapshot", paths, stale_rollup_result.blocker_code or "LIVE_READY_SNAPSHOT_WRITER_FAILED")

    invalidated = dict(stale_rollup)
    invalidated["validator_rollup_status"] = "PASS"
    invalidated["invalidated_by"] = ["CONTRACT_GAP_HIGH"]
    invalidated_result = validate_live_ready_snapshot(invalidated)
    if invalidated_result.status != "BLOCKED" or invalidated_result.blocker_code != "LIVE_READY_SNAPSHOT_WRITER_FAILED":
        return fail_result("live_ready_snapshot_validator", "invalidated snapshot did not block live_order_allowed", paths, invalidated_result.blocker_code or "LIVE_READY_SNAPSHOT_WRITER_FAILED")

    return pass_result(
        "live_ready_snapshot_validator",
        "LIVE_READY snapshot validator accepts blocked snapshots and rejects missing fields, live flag drift, missing evidence, stale rollups, and invalidated snapshots",
        paths,
    )


def live_ready_snapshot_writer_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    snapshot_schema_path = ROOT / "contracts" / "schema" / "live_ready_snapshot.schema.json"
    writer_schema_path = ROOT / "contracts" / "schema" / "live_ready_candidate_writer_input.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "readiness" / "live_ready_snapshot.py"
    paths = [registry_path, snapshot_schema_path, writer_schema_path, module_path]
    registry_hash = sha256_file(registry_path)
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    schema_bundle_hash = sha256_json({rel(path): sha256_file(path) for path in schema_files})
    source_tree_hash = sha256_json(
        {
            rel(path): sha256_file(path)
            for path in sorted((ROOT / "trader1").rglob("*.py"))
            if "__pycache__" not in path.parts
        }
    )
    writer_input = build_writer_input(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        strategy_id="mvp0_strategy",
        strategy_build_id="mvp0_strategy_build",
        parameter_hash="mvp0_parameter_hash",
        risk_profile="CONSERVATIVE",
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )

    blocked = evaluate_live_ready_snapshot_writer(writer_input, evidence_manifest_present=False)
    if blocked.status != "BLOCKED" or blocked.would_write_snapshot:
        return fail_result("live_ready_snapshot_writer_validator", "writer input was allowed without evidence manifest", paths, "LIVE_READY_SNAPSHOT_WRITER_FAILED")
    if blocked.blocker_code != "LIVE_READY_SNAPSHOT_WRITER_UNTESTED":
        return fail_result("live_ready_snapshot_writer_validator", "UNTESTED writer status did not block snapshot generation", paths, "LIVE_READY_SNAPSHOT_WRITER_UNTESTED")

    stage_b = dict(writer_input)
    stage_b["promotion_input_type"] = "REFINEMENT_CANDIDATE"
    stage_b["live_ready_snapshot_writer_status"] = "PASS"
    stage_b["blockers"] = []
    stage_b = attach_writer_input_hash(stage_b)
    stage_b_result = evaluate_live_ready_snapshot_writer(stage_b, evidence_manifest_present=True)
    if stage_b_result.blocker_code != "PROMOTION_INPUT_TYPE_INVALID":
        return fail_result("live_ready_snapshot_writer_validator", "Stage B/REFINEMENT_CANDIDATE was not blocked as writer input", paths, "PROMOTION_INPUT_TYPE_INVALID")

    stale = dict(writer_input)
    stale["live_ready_snapshot_writer_status"] = "STALE"
    stale["blockers"] = []
    stale = attach_writer_input_hash(stale)
    stale_result = evaluate_live_ready_snapshot_writer(stale, evidence_manifest_present=True)
    if stale_result.blocker_code != "LIVE_READY_SNAPSHOT_WRITER_UNTESTED":
        return fail_result("live_ready_snapshot_writer_validator", "STALE validator result did not block snapshot generation", paths, "LIVE_READY_SNAPSHOT_WRITER_UNTESTED")

    scoped = dict(writer_input)
    scoped["live_ready_snapshot_writer_status"] = "PASS"
    scoped["blockers"] = []
    scoped["evidence_manifest_hash"] = "E" * 64
    scoped = attach_writer_input_hash(scoped)
    scope_result = evaluate_live_ready_snapshot_writer(
        scoped,
        expected_scope={"exchange": "BINANCE", "market_type": "SPOT", "strategy_id": "mvp0_strategy", "risk_profile": "CONSERVATIVE", "parameter_hash": "mvp0_parameter_hash"},
        evidence_manifest_present=True,
    )
    if scope_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("live_ready_snapshot_writer_validator", "scope mismatch did not block snapshot generation", paths, "SNAPSHOT_SCOPE_MISMATCH")

    placeholder_writer = dict(writer_input)
    placeholder_writer["live_ready_snapshot_writer_status"] = "PASS"
    placeholder_writer["blockers"] = []
    placeholder_writer = attach_writer_input_hash(placeholder_writer)
    placeholder_result = evaluate_live_ready_snapshot_writer(placeholder_writer, evidence_manifest_present=True)
    if placeholder_result.blocker_code != "LIVE_READY_SNAPSHOT_WRITER_FAILED" or placeholder_result.would_write_snapshot:
        return fail_result("live_ready_snapshot_writer_validator", "placeholder evidence hash did not block snapshot generation", paths, "LIVE_READY_SNAPSHOT_WRITER_FAILED")

    snapshot = build_blocked_live_ready_snapshot(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    snapshot_result = validate_live_ready_snapshot(snapshot)
    if snapshot_result.status != "PASS" or snapshot_result.live_order_allowed:
        return fail_result("live_ready_snapshot_writer_validator", "blocked snapshot scaffold did not remain fail-closed", paths, "LIVE_FINAL_GUARD_FAILED")
    unsafe_snapshot = dict(snapshot)
    unsafe_snapshot["live_ready"] = True
    unsafe_snapshot["live_order_allowed"] = True
    unsafe_result = validate_live_ready_snapshot(unsafe_snapshot)
    if unsafe_result.status != "BLOCKED" or unsafe_result.blocker_code not in {"API_UNVERIFIED", "MANUAL_ORDER_TEST_MISSING"}:
        return fail_result("live_ready_snapshot_writer_validator", "live_order_allowed snapshot was not blocked by missing evidence", paths, "LIVE_FINAL_GUARD_FAILED")
    return pass_result("live_ready_snapshot_writer_validator", "LIVE_READY writer guard blocks writer input, stale validators, scope mismatch, and unevidenced snapshots", paths)


def official_api_verification_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "official_api_verification_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "readiness" / "official_api_verification.py"
    paths = [schema_path, module_path]
    authority = current_authority_hashes()

    unverified = build_official_api_verification_report(authority=authority)
    unverified_result = validate_official_api_verification_report(unverified)
    if unverified_result.status != "BLOCKED" or unverified_result.blocker_code != "API_UNVERIFIED":
        return fail_result("official_api_verification_validator", "unverified official API report did not block live review", paths, unverified_result.blocker_code or "API_UNVERIFIED")
    if unverified.get("live_order_ready") or unverified.get("live_order_allowed") or unverified.get("can_live_trade"):
        return fail_result("official_api_verification_validator", "unverified official API report drifted into live permission", paths, "LIVE_FINAL_GUARD_FAILED")

    tampered = dict(unverified)
    tampered["exchange"] = "BINANCE"
    tampered_result = validate_official_api_verification_report(tampered)
    if tampered_result.status != "FAIL" or tampered_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("official_api_verification_validator", "official API hash tamper was not detected", paths, tampered_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

    live_mutation = dict(unverified)
    live_mutation["live_order_allowed"] = True
    live_mutation["report_hash"] = official_api_report_hash(live_mutation)
    live_mutation_result = validate_official_api_verification_report(live_mutation)
    if live_mutation_result.status != "BLOCKED" or live_mutation_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("official_api_verification_validator", "official API report live permission drift was not blocked", paths, live_mutation_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    stale_facts = {key: {"verified": True} for key in PASS_REQUIRED_FACTS}
    stale_facts["margin_rules_if_futures"] = None
    stale_pass = build_official_api_verification_report(
        authority=authority,
        verification_id="validator-stale-official-api-pass",
        result="PASS",
        official_sources=[{"name": "official-doc-placeholder", "url": "https://example.invalid/upbit", "checked_at_utc": "2000-01-01T00:00:00Z"}],
        facts=stale_facts,
        expires_at_utc="2000-01-01T00:00:00Z",
    )
    stale_result = validate_official_api_verification_report(stale_pass)
    if stale_result.status != "BLOCKED" or stale_result.blocker_code != "OFFICIAL_API_VERIFICATION_EXPIRED":
        return fail_result("official_api_verification_validator", "expired official API PASS fixture was not blocked", paths, stale_result.blocker_code or "OFFICIAL_API_VERIFICATION_EXPIRED")

    missing_sources = build_official_api_verification_report(
        authority=authority,
        verification_id="validator-missing-source-official-api-pass",
        result="PASS",
        facts=stale_facts,
        expires_at_utc="2999-01-01T00:00:00Z",
    )
    missing_sources_result = validate_official_api_verification_report(missing_sources)
    if missing_sources_result.status != "BLOCKED" or missing_sources_result.blocker_code != "API_UNVERIFIED":
        return fail_result("official_api_verification_validator", "official API PASS without official sources was not blocked", paths, missing_sources_result.blocker_code or "API_UNVERIFIED")

    return pass_result(
        "official_api_verification_validator",
        "official API validator blocks missing evidence, hash tamper, live flag drift, stale PASS reports, and source-free PASS reports without external calls",
        paths,
    )


def startup_probe_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    schema_path = ROOT / "contracts" / "schema" / "startup_probe.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "boot" / "startup_probe.py"
    paths = [registry_path, schema_path, module_path]
    registry = load_json(registry_path)
    registry_hash = sha256_file(registry_path)
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    schema_bundle_hash = sha256_json({rel(path): sha256_file(path) for path in schema_files})
    source_tree_hash = sha256_json(
        {
            rel(path): sha256_file(path)
            for path in sorted((ROOT / "trader1").rglob("*.py"))
            if "__pycache__" not in path.parts
        }
    )
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_startup_probe",
        registry_hash=registry_hash,
    )
    probe = build_startup_probe(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_startup_probe",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        ledger_write_status=None,
    )
    allowed_blockers = set(registry["enums"]["live_blocker_code"]["values"])
    result = validate_startup_probe(probe, allowed_blockers)
    if result.status != "PASS":
        return fail_result("startup_probe_validator", result.message, paths, result.blocker_code or "PREFLIGHT_FAILED")
    if probe.get("startup_probe_passed") or probe.get("can_trade") or probe.get("live_order_allowed"):
        return fail_result("startup_probe_validator", "startup probe created readiness without hard truth", paths, "LIVE_FINAL_GUARD_FAILED")

    running_probe = dict(probe)
    running_probe["engine_state_after_probe"] = "RUNNING"
    running_probe["probe_hash"] = startup_probe_hash(running_probe)
    running_result = validate_startup_probe(running_probe, allowed_blockers)
    if running_result.status != "BLOCKED" or running_result.blocker_code != "PREFLIGHT_FAILED":
        return fail_result("startup_probe_validator", "RUNNING before startup_probe PASS was not blocked", paths, "PREFLIGHT_FAILED")

    live_probe = dict(probe)
    live_probe["live_order_allowed"] = True
    live_probe["can_live_trade"] = True
    live_probe["probe_hash"] = startup_probe_hash(live_probe)
    live_result = validate_startup_probe(live_probe, allowed_blockers)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("startup_probe_validator", "startup probe live permission was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")
    return pass_result("startup_probe_validator", "startup probe remains dashboard-only and fail-closed", paths)


def heartbeat_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    schema_path = ROOT / "contracts" / "schema" / "heartbeat.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "health" / "heartbeat.py"
    paths = [registry_path, schema_path, module_path]
    registry = load_json(registry_path)
    registry_hash = sha256_file(registry_path)
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    schema_bundle_hash = sha256_json({rel(path): sha256_file(path) for path in schema_files})
    source_tree_hash = sha256_json(
        {
            rel(path): sha256_file(path)
            for path in sorted((ROOT / "trader1").rglob("*.py"))
            if "__pycache__" not in path.parts
        }
    )
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_heartbeat",
        registry_hash=registry_hash,
    )
    heartbeat = build_heartbeat(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_heartbeat",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    allowed_blockers = set(registry["enums"]["live_blocker_code"]["values"])
    result = validate_heartbeat(heartbeat, allowed_blockers)
    if result.status != "PASS":
        return fail_result("heartbeat_validator", result.message, paths, result.blocker_code or "PREFLIGHT_FAILED")
    if heartbeat.get("can_trade") or heartbeat.get("live_order_allowed") or heartbeat.get("can_live_trade"):
        return fail_result("heartbeat_validator", "heartbeat created trading permission", paths, "LIVE_FINAL_GUARD_FAILED")

    live_heartbeat = dict(heartbeat)
    live_heartbeat["live_order_allowed"] = True
    live_heartbeat["can_live_trade"] = True
    live_heartbeat["heartbeat_hash"] = heartbeat_hash(live_heartbeat)
    live_result = validate_heartbeat(live_heartbeat, allowed_blockers)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("heartbeat_validator", "heartbeat live permission was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    stale_heartbeat = dict(heartbeat)
    stale_heartbeat["heartbeat_age_seconds"] = stale_heartbeat["stale_after_seconds"] + 1
    stale_heartbeat["heartbeat_hash"] = heartbeat_hash(stale_heartbeat)
    stale_result = validate_heartbeat(stale_heartbeat, allowed_blockers)
    if stale_result.status != "BLOCKED" or stale_result.blocker_code != "LATENCY_TTL_EXPIRED":
        return fail_result("heartbeat_validator", "stale heartbeat was not blocked", paths, "LATENCY_TTL_EXPIRED")

    component_heartbeat = dict(heartbeat)
    component_heartbeat["components"] = {name: dict(value) for name, value in heartbeat["components"].items()}
    component_heartbeat["components"]["disk"]["status"] = "FAIL"
    component_heartbeat["components"]["disk"]["message"] = "disk full"
    component_heartbeat["heartbeat_hash"] = heartbeat_hash(component_heartbeat)
    component_result = validate_heartbeat(component_heartbeat, allowed_blockers)
    if component_result.status != "BLOCKED" or component_result.blocker_code != "RESOURCE_LIMIT":
        return fail_result("heartbeat_validator", "component failure was not blocked", paths, "RESOURCE_LIMIT")

    return pass_result("heartbeat_validator", "heartbeat remains dashboard-only and fail-closed", paths)


def summary_shell_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    schema_path = ROOT / "contracts" / "schema" / "summary.schema.json"
    module_path = ROOT / "trader1" / "dashboard" / "summary_writer.py"
    paths = [registry_path, schema_path, module_path]
    registry = load_json(registry_path)
    registry_hash = sha256_file(registry_path)
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    schema_bundle_hash = sha256_json({rel(path): sha256_file(path) for path in schema_files})
    source_tree_hash = sha256_json(
        {
            rel(path): sha256_file(path)
            for path in sorted((ROOT / "trader1").rglob("*.py"))
            if "__pycache__" not in path.parts
        }
    )
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_summary_shell",
        registry_hash=registry_hash,
    )
    startup_probe = build_startup_probe(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_summary_shell",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        ledger_write_status=None,
    )
    heartbeat = build_heartbeat(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_summary_shell",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    readiness_surface = build_readiness_surface(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_summary_shell",
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_summary_shell",
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
    )
    allowed_blockers = set(registry["enums"]["live_blocker_code"]["values"])
    result = validate_summary_shell(summary, allowed_blockers)
    if result.status != "PASS":
        return fail_result("summary_shell_validator", result.message, paths, result.blocker_code or "LIVE_FINAL_GUARD_FAILED")
    if summary["live_ready"]["live_order_ready"] or summary["live_ready"]["live_order_allowed"]:
        return fail_result("summary_shell_validator", "summary shell created live readiness", paths, "LIVE_FINAL_GUARD_FAILED")

    live_summary = dict(summary)
    live_summary["live_ready"] = dict(summary["live_ready"])
    live_summary["live_ready"]["live_order_ready"] = True
    live_summary["live_ready"]["live_order_allowed"] = True
    live_result = validate_summary_shell(live_summary, allowed_blockers)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("summary_shell_validator", "summary live readiness mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    order_summary = dict(summary)
    order_summary["final_action"] = "ENTER_LONG"
    order_result = validate_summary_shell(order_summary, allowed_blockers)
    if order_result.status != "BLOCKED" or order_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("summary_shell_validator", "summary order-affecting final_action was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    portfolio_summary = dict(summary)
    portfolio_summary["portfolio"] = dict(summary["portfolio"])
    portfolio_summary["portfolio"]["equity"] = 1000.0
    portfolio_result = validate_summary_shell(portfolio_summary, allowed_blockers)
    if portfolio_result.status != "BLOCKED" or portfolio_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("summary_shell_validator", "summary builder portfolio truth invention was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    paper_portfolio = build_initial_paper_portfolio_snapshot(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        session_id="mvp1_summary_shell",
    )
    ledger_summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_summary_shell",
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
        paper_portfolio_snapshot=paper_portfolio,
    )
    ledger_result = validate_summary_shell(ledger_summary, allowed_blockers)
    if ledger_result.status != "PASS":
        return fail_result("summary_shell_validator", ledger_result.message, paths, ledger_result.blocker_code or "UNKNOWN_BLOCKED")
    if ledger_summary["portfolio"].get("source_snapshot_generated_at_utc") is None:
        return fail_result("summary_shell_validator", "verified portfolio snapshot time provenance is missing", paths, "HARD_TRUTH_MISSING")

    filled_portfolio = build_paper_portfolio_snapshot_from_fill(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        session_id="mvp1_summary_shell",
        symbol="KRW-BTC",
        side="BUY",
        quantity="0.01",
        fill_price="1000500",
        mark_price="1000000",
        fee_amount="5",
        source_runtime_cycle_id="validator-dashboard-filled-cycle",
        source_paper_ledger_head_hash="E" * 64,
    )
    filled_summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_summary_shell",
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
        paper_portfolio_snapshot=filled_portfolio,
    )
    filled_result = validate_summary_shell(filled_summary, allowed_blockers)
    if filled_result.status != "PASS":
        return fail_result("summary_shell_validator", filled_result.message, paths, filled_result.blocker_code or "UNKNOWN_BLOCKED")
    if filled_summary["portfolio"]["open_position_count"] != 1 or len(filled_summary["positions"]) != 1:
        return fail_result("summary_shell_validator", "filled paper position detail did not reach summary", paths, "SCHEMA_IDENTITY_MISMATCH")

    position_tamper_summary = json.loads(json.dumps(filled_summary))
    position_tamper_summary["positions"][0]["market_value"] = "9999"
    position_tamper_result = validate_summary_shell(position_tamper_summary, allowed_blockers)
    if position_tamper_result.status != "FAIL" or position_tamper_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("summary_shell_validator", "summary position detail tamper was not detected", paths, "SCHEMA_IDENTITY_MISMATCH")

    position_side_summary = json.loads(json.dumps(filled_summary))
    position_side_summary["positions"][0]["side"] = "SHORT"
    position_side_result = validate_summary_shell(position_side_summary, allowed_blockers)
    if position_side_result.status != "BLOCKED" or position_side_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("summary_shell_validator", "summary position side drift was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    position_rollup_summary = json.loads(json.dumps(filled_summary))
    position_rollup_summary["portfolio"]["position_market_value"] = position_rollup_summary["portfolio"]["position_market_value"] + 1.0
    position_rollup_result = validate_summary_shell(position_rollup_summary, allowed_blockers)
    if position_rollup_result.status != "FAIL" or position_rollup_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("summary_shell_validator", "summary position rollup mismatch was not detected", paths, "SCHEMA_IDENTITY_MISMATCH")

    stale_portfolio = dict(filled_portfolio)
    stale_portfolio["generated_at_utc"] = "2020-01-01T00:00:00Z"
    stale_portfolio["snapshot_hash"] = paper_portfolio_hash(stale_portfolio)
    stale_summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_summary_shell",
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
        paper_portfolio_snapshot=stale_portfolio,
    )
    stale_result = validate_summary_shell(stale_summary, allowed_blockers)
    if stale_result.status != "PASS" or stale_summary["portfolio"]["source"] != "SUMMARY_BUILDER":
        return fail_result("summary_shell_validator", "stale paper portfolio snapshot was not downgraded before dashboard display", paths, "LATENCY_TTL_EXPIRED")

    stale_claim_summary = json.loads(json.dumps(ledger_summary))
    stale_claim_summary["portfolio"]["source_snapshot_age_seconds"] = stale_claim_summary["portfolio"]["source_snapshot_stale_after_seconds"] + 1
    stale_claim_result = validate_summary_shell(stale_claim_summary, allowed_blockers)
    if stale_claim_result.status != "BLOCKED" or stale_claim_result.blocker_code != "LATENCY_TTL_EXPIRED":
        return fail_result("summary_shell_validator", "verified portfolio stale age claim was not blocked", paths, "LATENCY_TTL_EXPIRED")

    unbound_summary = dict(ledger_summary)
    unbound_summary["portfolio"] = dict(ledger_summary["portfolio"])
    unbound_summary["portfolio"]["source_snapshot_hash"] = None
    unbound_result = validate_summary_shell(unbound_summary, allowed_blockers)
    if unbound_result.status != "BLOCKED" or unbound_result.blocker_code != "HARD_TRUTH_MISSING":
        return fail_result("summary_shell_validator", "verified portfolio without source snapshot provenance was not blocked", paths, "HARD_TRUTH_MISSING")

    arithmetic_summary = dict(ledger_summary)
    arithmetic_summary["portfolio"] = dict(ledger_summary["portfolio"])
    arithmetic_summary["portfolio"]["equity"] = arithmetic_summary["portfolio"]["equity"] + 1.0
    arithmetic_result = validate_summary_shell(arithmetic_summary, allowed_blockers)
    if arithmetic_result.status != "FAIL" or arithmetic_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("summary_shell_validator", "verified portfolio arithmetic drift was not detected", paths, "SCHEMA_IDENTITY_MISMATCH")

    return pass_result("summary_shell_validator", "summary shell remains dashboard-only and fail-closed", paths)


def read_only_dashboard_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    schema_path = ROOT / "contracts" / "schema" / "read_only_dashboard_shell.schema.json"
    module_path = ROOT / "trader1" / "dashboard" / "read_only_dashboard.py"
    launcher_module_path = ROOT / "trader1" / "runtime" / "boot" / "safe_launcher.py"
    stale_rollup_test_path = ROOT / "tests" / "runtime" / "test_safe_launcher.py"
    dashboard_test_path = ROOT / "tests" / "dashboard" / "test_read_only_dashboard.py"
    paths = [registry_path, schema_path, module_path, launcher_module_path, stale_rollup_test_path, dashboard_test_path]
    registry = load_json(registry_path)
    registry_hash = sha256_file(registry_path)
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    schema_bundle_hash = sha256_json({rel(path): sha256_file(path) for path in schema_files})
    source_tree_hash = sha256_json(
        {
            rel(path): sha256_file(path)
            for path in sorted((ROOT / "trader1").rglob("*.py"))
            if "__pycache__" not in path.parts
        }
    )
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_read_only_dashboard",
        registry_hash=registry_hash,
    )
    startup_probe = build_startup_probe(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_read_only_dashboard",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        ledger_write_status=None,
    )
    heartbeat = build_heartbeat(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_read_only_dashboard",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    readiness_surface = build_readiness_surface(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_read_only_dashboard",
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_read_only_dashboard",
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
    )
    dashboard = build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_read_only_dashboard",
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
    )
    allowed_blockers = set(registry["enums"]["live_blocker_code"]["values"])
    result = validate_read_only_dashboard_shell(dashboard, allowed_blockers)
    if result.status != "PASS":
        return fail_result("read_only_dashboard_validator", result.message, paths, result.blocker_code or "LIVE_FINAL_GUARD_FAILED")
    if dashboard.get("portfolio_snapshot", {}).get("status") != "VERIFIED":
        operation = dashboard.get("operation_status", {})
        if operation.get("severity") == "NORMAL" or operation.get("color_token") != "yellow":
            return fail_result(
                "read_only_dashboard_validator",
                "unverified portfolio display truth was shown as normal operation",
                paths,
                "HARD_TRUTH_MISSING",
            )
        if operation.get("portfolio_status") != dashboard.get("portfolio_snapshot", {}).get("status"):
            return fail_result(
                "read_only_dashboard_validator",
                "operation status did not expose the dashboard portfolio trust state",
                paths,
                "HARD_TRUTH_MISSING",
            )
    dashboard_schema = load_json(schema_path)
    metric_schema = dashboard_schema["$defs"]["stability_trends"]["properties"]["metrics"]
    runtime_metric_count = len(dashboard["stability_trends"]["metrics"])
    if metric_schema.get("minItems") != runtime_metric_count or metric_schema.get("maxItems") != runtime_metric_count:
        return fail_result(
            "read_only_dashboard_validator",
            "dashboard stability metric schema count does not match runtime output",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if not dashboard["operation_status"].get("recovery_hint"):
        return fail_result("read_only_dashboard_validator", "operation status recovery guidance is missing", paths, "SCHEMA_IDENTITY_MISMATCH")
    reconciliation = dashboard.get("reconciliation_recovery_summary")
    if not isinstance(reconciliation, dict):
        return fail_result("read_only_dashboard_validator", "reconciliation recovery summary is missing", paths, "SCHEMA_IDENTITY_MISMATCH")
    if reconciliation.get("status") != "NOT_LOADED" or reconciliation.get("color_token") != "yellow":
        return fail_result("read_only_dashboard_validator", "missing reconciliation evidence must be visible as a yellow operator warning", paths, "RECONCILIATION_REQUIRED")
    if reconciliation.get("live_order_allowed") or reconciliation.get("can_live_trade") or reconciliation.get("scale_up_allowed"):
        return fail_result("read_only_dashboard_validator", "reconciliation recovery summary created forbidden live or scale permission", paths, "LIVE_FINAL_GUARD_FAILED")
    market_data = dashboard.get("market_data_continuity_status")
    if not isinstance(market_data, dict):
        return fail_result("read_only_dashboard_validator", "market-data continuity status is missing", paths, "SCHEMA_IDENTITY_MISMATCH")
    if market_data.get("status") != "NOT_LOADED" or market_data.get("color_token") != "yellow":
        return fail_result("read_only_dashboard_validator", "missing market-data continuity evidence must be visible as a yellow operator warning", paths, "DATA_UNAVAILABLE")
    if (
        market_data.get("live_order_ready")
        or market_data.get("live_order_allowed")
        or market_data.get("can_live_trade")
        or market_data.get("scale_up_allowed")
        or market_data.get("long_run_evidence_eligible")
        or market_data.get("promotion_eligible")
    ):
        return fail_result("read_only_dashboard_validator", "market-data continuity status created forbidden live, long-run, promotion, or scale permission", paths, "LIVE_FINAL_GUARD_FAILED")
    if dashboard.get("live_order_ready") or dashboard.get("live_order_allowed") or dashboard.get("can_live_trade") or dashboard.get("can_submit_order"):
        return fail_result("read_only_dashboard_validator", "dashboard created live or order permission", paths, "LIVE_FINAL_GUARD_FAILED")

    live_dashboard = dict(dashboard)
    live_dashboard["live_order_ready"] = True
    live_dashboard["live_order_allowed"] = True
    live_dashboard["can_submit_order"] = True
    live_dashboard["dashboard_hash"] = dashboard_shell_hash(live_dashboard)
    live_result = validate_read_only_dashboard_shell(live_dashboard, allowed_blockers)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("read_only_dashboard_validator", "dashboard live permission mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    order_dashboard = dict(dashboard)
    order_dashboard["final_action"] = "ENTER_LONG"
    order_dashboard["dashboard_hash"] = dashboard_shell_hash(order_dashboard)
    order_result = validate_read_only_dashboard_shell(order_dashboard, allowed_blockers)
    if order_result.status != "BLOCKED" or order_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("read_only_dashboard_validator", "dashboard order-affecting final_action was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    source_dashboard = dict(dashboard)
    source_dashboard["source_artifacts"] = [dict(item) for item in dashboard["source_artifacts"]]
    source_dashboard["source_artifacts"][0]["truth_role"] = "ledger"
    source_dashboard["dashboard_hash"] = dashboard_shell_hash(source_dashboard)
    source_result = validate_read_only_dashboard_shell(source_dashboard, allowed_blockers)
    if source_result.status != "BLOCKED" or source_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("read_only_dashboard_validator", "dashboard non-dashboard truth source was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    wording_dashboard = dict(dashboard)
    wording_dashboard["panels"] = [dict(item) for item in dashboard["panels"]]
    wording_dashboard["panels"][0]["message"] = "profit guaranteed"
    wording_dashboard["dashboard_hash"] = dashboard_shell_hash(wording_dashboard)
    wording_result = validate_read_only_dashboard_shell(wording_dashboard, allowed_blockers)
    if wording_result.status != "BLOCKED" or wording_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("read_only_dashboard_validator", "dashboard forbidden wording was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    missing_dashboard = build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_read_only_dashboard",
        summary=summary,
        heartbeat=None,
        startup_probe=startup_probe,
    )
    missing_result = validate_read_only_dashboard_shell(missing_dashboard, allowed_blockers)
    if missing_result.status != "PASS" or missing_dashboard["final_action"] != "NO_TRADE" or missing_dashboard["blocking_reason"] is None:
        return fail_result("read_only_dashboard_validator", "missing dashboard source did not stay fail-closed", paths, "HARD_TRUTH_MISSING")
    if "Rerun the PAPER launcher" not in missing_dashboard["operation_status"].get("recovery_hint", ""):
        return fail_result("read_only_dashboard_validator", "stale heartbeat recovery guidance is not operator-visible", paths, "LATENCY_TTL_EXPIRED")

    unverified_normal_dashboard = dict(dashboard)
    unverified_normal_dashboard["operation_status"] = dict(dashboard["operation_status"])
    unverified_normal_dashboard["operation_status"]["status"] = "RUNNING_SAFE_MODE"
    unverified_normal_dashboard["operation_status"]["severity"] = "NORMAL"
    unverified_normal_dashboard["operation_status"]["color_token"] = "green"
    unverified_normal_dashboard["operation_status"]["label"] = "Running safely"
    unverified_normal_dashboard["dashboard_hash"] = dashboard_shell_hash(unverified_normal_dashboard)
    unverified_normal_result = validate_read_only_dashboard_shell(unverified_normal_dashboard, allowed_blockers)
    if unverified_normal_result.status != "BLOCKED" or unverified_normal_result.blocker_code != "HARD_TRUTH_MISSING":
        return fail_result(
            "read_only_dashboard_validator",
            "normal operation was not blocked when portfolio display truth was unverified",
            paths,
            "HARD_TRUTH_MISSING",
        )

    operation_mismatch_dashboard = dict(dashboard)
    operation_mismatch_dashboard["operation_status"] = dict(dashboard["operation_status"])
    operation_mismatch_dashboard["operation_status"]["portfolio_status"] = "VERIFIED"
    operation_mismatch_dashboard["dashboard_hash"] = dashboard_shell_hash(operation_mismatch_dashboard)
    operation_mismatch_result = validate_read_only_dashboard_shell(operation_mismatch_dashboard, allowed_blockers)
    if operation_mismatch_result.status != "BLOCKED" or operation_mismatch_result.blocker_code != "HARD_TRUTH_MISSING":
        return fail_result(
            "read_only_dashboard_validator",
            "operation portfolio status mismatch was not blocked",
            paths,
            "HARD_TRUTH_MISSING",
        )

    filled_portfolio = build_paper_portfolio_snapshot_from_fill(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        session_id="mvp1_read_only_dashboard",
        symbol="KRW-BTC",
        side="BUY",
        quantity="0.01",
        fill_price="1000500",
        mark_price="1000000",
        fee_amount="5",
        source_runtime_cycle_id="validator-dashboard-filled-cycle",
        source_paper_ledger_head_hash="E" * 64,
    )
    filled_summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_read_only_dashboard",
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
        paper_portfolio_snapshot=filled_portfolio,
    )
    filled_dashboard = build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_read_only_dashboard",
        summary=filled_summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
    )
    filled_result = validate_read_only_dashboard_shell(filled_dashboard, allowed_blockers)
    if filled_result.status != "PASS":
        return fail_result(
            "read_only_dashboard_validator",
            f"filled paper position dashboard did not validate: {filled_result.message}",
            paths,
            filled_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )
    if filled_dashboard.get("portfolio_snapshot", {}).get("source_runtime_cycle_id") != "validator-dashboard-filled-cycle":
        return fail_result(
            "read_only_dashboard_validator",
            "filled paper portfolio dashboard omitted runtime cycle provenance",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if filled_dashboard.get("portfolio_snapshot", {}).get("source_paper_ledger_head_hash") != "E" * 64:
        return fail_result(
            "read_only_dashboard_validator",
            "filled paper portfolio dashboard omitted ledger head provenance",
            paths,
            "LEDGER_INTEGRITY_FAIL",
        )
    if not isinstance(filled_dashboard.get("portfolio_snapshot", {}).get("source_snapshot_age_seconds"), int):
        return fail_result(
            "read_only_dashboard_validator",
            "filled paper portfolio dashboard omitted source snapshot age",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if filled_dashboard.get("portfolio_snapshot", {}).get("source_snapshot_stale_after_seconds") != 300:
        return fail_result(
            "read_only_dashboard_validator",
            "filled paper portfolio dashboard omitted source snapshot stale threshold",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    stale_source_dashboard = json.loads(json.dumps(filled_dashboard))
    stale_source_dashboard["portfolio_snapshot"]["source_snapshot_age_seconds"] = 301
    stale_source_dashboard["dashboard_hash"] = dashboard_shell_hash(stale_source_dashboard)
    stale_source_result = validate_read_only_dashboard_shell(stale_source_dashboard, allowed_blockers)
    if stale_source_result.status != "BLOCKED" or stale_source_result.blocker_code != "LATENCY_TTL_EXPIRED":
        return fail_result(
            "read_only_dashboard_validator",
            "stale paper portfolio source age was not blocked",
            paths,
            stale_source_result.blocker_code or "LATENCY_TTL_EXPIRED",
        )
    filled_rows = filled_dashboard.get("position_snapshot", {}).get("rows", [])
    if not filled_rows:
        return fail_result(
            "read_only_dashboard_validator",
            "filled paper portfolio position did not reach dashboard position rows",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    filled_row = filled_rows[0]
    expected_position_fields = {
        "avg_price": "1000500",
        "mark_price": "1000000",
        "market_value": "10000",
        "cost_basis": "10010",
        "unrealized_pnl": "-10",
    }
    missing_position_fields = [
        key for key, expected in expected_position_fields.items() if str(filled_row.get(key)) != expected
    ]
    if missing_position_fields:
        return fail_result(
            "read_only_dashboard_validator",
            f"filled paper position dashboard lost source position detail fields: {missing_position_fields}",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    filled_html = render_dashboard_html(filled_dashboard)
    for fragment in (
        "Mark Price",
        "Market Value",
        "Cost Basis",
        "avg 1000500",
        "mark 1000000",
        "value 10000",
        "Runtime cycle: validator-dashboard-filled-cycle",
        "Ledger head: EEEEEEEEEEEE...",
        "Age:",
    ):
        if fragment not in filled_html:
            return fail_result(
                "read_only_dashboard_validator",
                f"filled paper position dashboard HTML omitted operator-visible position detail: {fragment}",
                paths,
                "SCHEMA_IDENTITY_MISMATCH",
            )

    with TemporaryDirectory() as tmp:
        stale_root = Path(tmp)
        stale_report = build_launcher_report("UPBIT_PAPER")
        run_upbit_paper_persistent_loop(
            root=stale_root,
            loop_id="validator-dashboard-stale-rollup",
            session_id=stale_report["session_id"],
            requested_cycle_count=2,
        )
        stale_paths = launcher_dashboard_paths(stale_report, stale_root)
        rollup_path = stale_paths["paper_ledger_rollup_report"]
        rollup_report = load_json(rollup_path)
        rollup_report["generated_at_utc"] = "2000-01-01T00:00:00Z"
        rollup_report["rollup_hash"] = paper_ledger_rollup_hash(rollup_report)
        rollup_path.write_text(json.dumps(rollup_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        latest_runtime_path = stale_paths["upbit_paper_runtime_cycle_report"]
        if latest_runtime_path.exists():
            latest_runtime_path.unlink()
        dashboard_paths = write_launcher_dashboard(stale_report, stale_root)
        stale_summary = load_json(dashboard_paths["summary"])
        stale_dashboard = load_json(dashboard_paths["dashboard_shell"])
        stale_portfolio = stale_summary.get("portfolio", {})
        if stale_portfolio.get("source") == "LEDGER" or stale_portfolio.get("freshness") == "PASS":
            return fail_result(
                "read_only_dashboard_validator",
                "stale paper ledger rollup was accepted as verified dashboard portfolio truth",
                paths,
                "LATENCY_TTL_EXPIRED",
            )
        if stale_dashboard.get("portfolio_snapshot", {}).get("status") == "VERIFIED":
            return fail_result(
                "read_only_dashboard_validator",
                "dashboard rendered stale paper ledger rollup as a verified portfolio snapshot",
                paths,
                "LATENCY_TTL_EXPIRED",
            )
        if (
            stale_summary.get("live_order_ready")
            or stale_summary.get("live_order_allowed")
            or stale_summary.get("can_live_trade")
            or stale_dashboard.get("live_order_ready")
            or stale_dashboard.get("live_order_allowed")
            or stale_dashboard.get("can_live_trade")
        ):
            return fail_result(
                "read_only_dashboard_validator",
                "stale paper ledger rollup path created forbidden live permission",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    return pass_result("read_only_dashboard_validator", "read-only dashboard shell remains display-only, stale-safe, and fail-closed", paths)


def dashboard_visual_layout_validator() -> ValidatorResult:
    module_path = ROOT / "trader1" / "dashboard" / "read_only_dashboard.py"
    test_path = ROOT / "tests" / "dashboard" / "test_read_only_dashboard.py"
    runtime_paths = sorted((ROOT / "system" / "runtime").glob("**/dashboard/index.html"))
    paths = [module_path, test_path] + runtime_paths

    registry_path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(registry_path)
    allowed_blockers = set(registry["enums"]["live_blocker_code"]["values"])
    registry_hash = sha256_file(registry_path)
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    schema_bundle_hash = sha256_json({rel(path): sha256_file(path) for path in schema_files})
    source_tree_hash = sha256_json(
        {
            rel(path): sha256_file(path)
            for path in sorted((ROOT / "trader1").rglob("*.py"))
            if "__pycache__" not in path.parts
        }
    )
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp4_dashboard_visual_layout_validator",
        registry_hash=registry_hash,
    )
    startup_probe = build_startup_probe(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp4_dashboard_visual_layout_validator",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        ledger_write_status=None,
    )
    heartbeat = build_heartbeat(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp4_dashboard_visual_layout_validator",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    readiness_surface = build_readiness_surface(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp4_dashboard_visual_layout_validator",
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp4_dashboard_visual_layout_validator",
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
    )
    dashboard = build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp4_dashboard_visual_layout_validator",
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
    )
    shell_result = validate_read_only_dashboard_shell(dashboard, allowed_blockers)
    if shell_result.status != "PASS":
        return fail_result(
            "dashboard_visual_layout_validator",
            f"dashboard shell did not validate before visual layout check: {shell_result.message}",
            paths,
            shell_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )
    html = render_dashboard_html(dashboard)
    layout_result = validate_dashboard_visual_layout_contract(html)
    if layout_result.status != "PASS":
        return fail_result(
            "dashboard_visual_layout_validator",
            layout_result.message,
            paths,
            layout_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )
    for runtime_path in runtime_paths:
        runtime_result = validate_dashboard_visual_layout_contract(runtime_path.read_text(encoding="utf-8"))
        if runtime_result.status != "PASS":
            return fail_result(
                "dashboard_visual_layout_validator",
                f"runtime dashboard visual layout failed for {rel(runtime_path)}: {runtime_result.message}",
                paths,
                runtime_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
            )
    return pass_result(
        "dashboard_visual_layout_validator",
        "dashboard HTML uses readable first-screen layout, stable detail persistence keys, and overflow-safe grids",
        paths,
    )


def runtime_schema_instance_validator() -> ValidatorResult:
    schema_dir = ROOT / "contracts" / "schema"
    module_path = ROOT / "trader1" / "validation" / "schema_instance.py"
    dashboard_module_path = ROOT / "trader1" / "dashboard" / "read_only_dashboard.py"
    launcher_module_path = ROOT / "trader1" / "runtime" / "boot" / "safe_launcher.py"
    paths = [schema_dir, module_path, dashboard_module_path, launcher_module_path]
    schema_bundle = load_schema_bundle(schema_dir)
    registry_hash = sha256_file(ROOT / "contracts" / "registry.yaml")
    schema_bundle_hash = sha256_json({rel(path): sha256_file(path) for path in sorted(schema_dir.glob("*.schema.json"))})
    source_tree_hash = sha256_json(
        {
            rel(path): sha256_file(path)
            for path in sorted((ROOT / "trader1").rglob("*.py"))
            if "__pycache__" not in path.parts
        }
    )

    instances: list[tuple[str, dict[str, Any]]] = []
    for launcher_name in sorted(ALLOWED_ROOT_LAUNCHERS):
        instances.append((f"build_launcher_report:{launcher_name}", build_launcher_report(launcher_name)))

    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="runtime_schema_instance_validator",
        registry_hash=registry_hash,
    )
    startup_probe = build_startup_probe(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="runtime_schema_instance_validator",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        ledger_write_status=None,
    )
    heartbeat = build_heartbeat(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="runtime_schema_instance_validator",
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    readiness_surface = build_readiness_surface(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="runtime_schema_instance_validator",
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    paper_portfolio = build_initial_paper_portfolio_snapshot(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        session_id="runtime_schema_instance_validator",
    )
    summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="runtime_schema_instance_validator",
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
        paper_portfolio_snapshot=paper_portfolio,
    )
    dashboard = build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="runtime_schema_instance_validator",
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
    )
    instances.extend(
        [
            ("build_startup_probe:UPBIT/PAPER", startup_probe),
            ("build_heartbeat:UPBIT/PAPER", heartbeat),
            ("build_summary_shell:UPBIT/PAPER", summary),
            ("build_read_only_dashboard_shell:UPBIT/PAPER", dashboard),
            ("build_initial_paper_portfolio_snapshot:UPBIT/PAPER", paper_portfolio),
            (
                "build_upbit_public_rest_sample_report:no-network",
                build_upbit_public_rest_sample_report(
                    sample_id="runtime-schema-instance-no-network",
                    session_id="runtime_schema_instance_validator",
                    attempt_network=False,
                ),
            ),
            (
                "build_upbit_public_rest_continuity_report:no-network",
                build_upbit_public_rest_continuity_report(
                    continuity_id="runtime-schema-instance-continuity-no-network",
                    session_id="runtime_schema_instance_validator",
                    attempt_network=False,
                ),
            ),
            (
                "build_upbit_public_rest_continuity_history_report:empty",
                build_upbit_public_rest_continuity_history_report(
                    history_id="runtime-schema-instance-continuity-history-empty",
                    session_id="runtime_schema_instance_validator",
                    continuity_attempts=[],
                ),
            ),
        ]
    )
    collection_report = build_upbit_public_market_data_collection_report(
        collector_id="runtime-schema-instance-public-collection",
        session_id="runtime_schema_instance_validator",
    )
    instances.append(("build_upbit_public_market_data_collection_report", collection_report))
    with TemporaryDirectory() as tmp:
        collection_writer = write_upbit_public_market_data_collection_artifacts(root=Path(tmp), report=collection_report)
        latest_pointer = load_json(Path(tmp) / collection_writer["artifact_paths"][3])
        run_upbit_paper_persistent_loop(root=Path(tmp), loop_id="runtime-schema-instance-sample-history", requested_cycle_count=1)
        sample_history = build_upbit_paper_runtime_sample_history(root=Path(tmp), session_id="mvp1_upbit_paper_launcher")
        stale_reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=Path(tmp), session_id="mvp1_upbit_paper_launcher")
        stale_regeneration_plan = build_upbit_paper_stale_loop_regeneration_plan(root=Path(tmp), reconciliation_report=stale_reconciliation)
        stale_execution_guard = build_upbit_paper_stale_loop_execution_guard(root=Path(tmp), plan=stale_regeneration_plan)
        stale_safe_regeneration_executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=Path(tmp), guard=stale_execution_guard)
        stale_post_regeneration_reconciliation = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(
            root=Path(tmp),
            executor_report=stale_safe_regeneration_executor,
        )
        blocked_repair_plan = build_upbit_paper_blocked_repair_plan_report(
            root=Path(tmp),
            post_reconciliation_report=stale_post_regeneration_reconciliation,
        )
        ledger_rollup_repair = build_upbit_paper_ledger_rollup_repair_report(
            root=Path(tmp),
            repair_plan_report=blocked_repair_plan,
        )
        post_repair_reconciliation = build_upbit_paper_post_repair_reconciliation_report(
            ledger_rollup_repair_report=ledger_rollup_repair,
        )
        instances.extend(
            [
                ("write_upbit_public_market_data_collection_artifacts:writer", collection_writer),
                ("write_upbit_public_market_data_collection_artifacts:latest_pointer", latest_pointer),
                ("build_upbit_paper_runtime_sample_history", sample_history),
                ("build_upbit_paper_stale_loop_reconciliation_report", stale_reconciliation),
                ("build_upbit_paper_stale_loop_regeneration_plan", stale_regeneration_plan),
                ("build_upbit_paper_stale_loop_execution_guard", stale_execution_guard),
                ("build_upbit_paper_stale_loop_safe_regeneration_executor_report", stale_safe_regeneration_executor),
                ("build_upbit_paper_stale_loop_post_regeneration_reconciliation_report", stale_post_regeneration_reconciliation),
                ("build_upbit_paper_blocked_repair_plan_report", blocked_repair_plan),
                ("build_upbit_paper_ledger_rollup_repair_report", ledger_rollup_repair),
                ("build_upbit_paper_post_repair_reconciliation_report", post_repair_reconciliation),
            ]
        )

    current_artifact_paths = sorted((ROOT / "system" / "runtime").glob("*/*/paper/*/dashboard_shell.json"))
    current_artifact_paths.extend(sorted((ROOT / "system" / "runtime").glob("*/*/paper/*/heartbeat.json")))
    current_artifact_paths.extend(sorted((ROOT / "system" / "runtime").glob("*/*/paper/*/summary.json")))
    current_artifact_paths.extend(sorted((ROOT / "system" / "runtime").glob("*/*/paper/*/startup_probe.json")))
    current_artifact_paths.extend(sorted((ROOT / "system" / "runtime").glob("*/*/paper/*/launcher/root_launcher_report.json")))
    for artifact_path_item in current_artifact_paths:
        try:
            loaded = load_json(artifact_path_item)
        except Exception as exc:
            return fail_result(
                "runtime_schema_instance_validator",
                f"runtime artifact is not valid json: {rel(artifact_path_item)}: {exc}",
                [*paths, artifact_path_item],
                "SCHEMA_IDENTITY_MISMATCH",
            )
        if isinstance(loaded, dict):
            instances.append((rel(artifact_path_item), loaded))

    for label, instance in instances:
        schema = schema_for_instance(instance, schema_bundle)
        if schema is None:
            return fail_result(
                "runtime_schema_instance_validator",
                f"no schema found for runtime instance {label}",
                paths,
                "SCHEMA_IDENTITY_MISMATCH",
            )
        result = validate_instance_against_schema(instance, schema, schema_bundle)
        if result.status != "PASS":
            return fail_result(
                "runtime_schema_instance_validator",
                f"{label}: {result.message}",
                paths,
                "SCHEMA_IDENTITY_MISMATCH",
            )
        if instance.get("live_order_ready") or instance.get("live_order_allowed") or instance.get("can_live_trade") or instance.get("can_submit_order"):
            return fail_result(
                "runtime_schema_instance_validator",
                f"{label}: runtime schema instance attempted live/order permission",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    return pass_result(
        "runtime_schema_instance_validator",
        f"{len(instances)} generated/current runtime instances match their schemas and remain live-blocked",
        paths + current_artifact_paths,
    )


def runtime_dashboard_artifact_hygiene_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "runtime_dashboard_artifact_hygiene_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "artifact_hygiene.py"
    runtime_paths = sorted((ROOT / "system" / "runtime").glob("**/dashboard_shell.json"))
    report_path = ROOT / "system" / "evidence" / "runtime_artifact_hygiene" / "runtime_dashboard_artifact_hygiene_report.json"
    paths = [schema_path, module_path, report_path, *runtime_paths]

    report = build_runtime_dashboard_artifact_hygiene_report(ROOT)
    result = validate_runtime_dashboard_artifact_hygiene_report(report)
    if result.status != "PASS":
        return blocked_result(
            "runtime_dashboard_artifact_hygiene_validator",
            f"{result.message}: {', '.join(result.blocking_reasons)}",
            paths,
            "SNAPSHOT_SCOPE_MISMATCH",
        )

    legacy_count = int(report.get("legacy_retained_count", 0))
    active_count = int(report.get("active_count", 0))
    unknown_count = int(report.get("unknown_count", 0))
    if active_count < len(ALLOWED_ROOT_LAUNCHERS):
        return blocked_result(
            "runtime_dashboard_artifact_hygiene_validator",
            "not all active root launchers have session-scoped dashboard shells",
            paths,
            "SNAPSHOT_SCOPE_MISMATCH",
        )
    if unknown_count:
        return blocked_result(
            "runtime_dashboard_artifact_hygiene_validator",
            "unknown dashboard shell artifacts require explicit ownership classification",
            paths,
            "SNAPSHOT_SCOPE_MISMATCH",
        )
    return pass_result(
        "runtime_dashboard_artifact_hygiene_validator",
        f"{active_count} session-scoped dashboard shells are active; {legacy_count} legacy unscoped shells are retained as non-authoritative audit artifacts",
        paths,
    )


def runtime_stability_history_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "runtime_stability_history.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "health" / "stability_history.py"
    runtime_paths = sorted((ROOT / "system" / "runtime").glob("*/*/*/*/stability_history.json"))
    paths = [schema_path, module_path, *runtime_paths]
    if not runtime_paths:
        return blocked_result(
            "runtime_stability_history_validator",
            "no runtime stability history artifacts were found",
            [schema_path, module_path],
            "HARD_TRUTH_MISSING",
        )

    for path in runtime_paths:
        try:
            history = load_json(path)
        except Exception as exc:
            return fail_result(
                "runtime_stability_history_validator",
                f"runtime stability history is not valid json: {rel(path)}: {exc}",
                paths,
                "SCHEMA_IDENTITY_MISMATCH",
            )

        try:
            parts = path.relative_to(ROOT / "system" / "runtime").parts
        except ValueError:
            return blocked_result(
                "runtime_stability_history_validator",
                f"runtime stability history path is outside runtime namespace: {rel(path)}",
                paths,
                "SNAPSHOT_SCOPE_MISMATCH",
            )
        if len(parts) != 5:
            return blocked_result(
                "runtime_stability_history_validator",
                f"runtime stability history path has unexpected namespace shape: {rel(path)}",
                paths,
                "SNAPSHOT_SCOPE_MISMATCH",
            )
        exchange_slug, market_type_slug, mode_slug, session_id, filename = parts
        if filename != "stability_history.json":
            return blocked_result(
                "runtime_stability_history_validator",
                f"runtime stability history path has unexpected filename: {rel(path)}",
                paths,
                "SNAPSHOT_SCOPE_MISMATCH",
            )

        result = validate_stability_history(
            history,
            expected_exchange=exchange_slug.upper(),
            expected_market_type=market_type_slug.upper(),
            expected_mode=mode_slug.upper(),
            expected_session_id=session_id,
        )
        if result.status == "PASS":
            continue
        if result.status == "BLOCKED":
            return blocked_result(
                "runtime_stability_history_validator",
                f"{result.message}: {rel(path)}",
                paths,
                result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
            )
        return fail_result(
            "runtime_stability_history_validator",
            f"{result.message}: {rel(path)}",
            paths,
            result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )

    return pass_result(
        "runtime_stability_history_validator",
        f"{len(runtime_paths)} runtime stability histories are display-only, scoped, and hash-linked",
        paths,
    )


def runtime_resource_pressure_validator() -> ValidatorResult:
    module_path = ROOT / "trader1" / "runtime" / "health" / "runtime_resource_pressure.py"
    runtime_dirs = sorted({path.parent for path in (ROOT / "system" / "runtime").glob("*/*/*/*/summary.json")})
    paths = [module_path, *runtime_dirs]
    if not runtime_dirs:
        return blocked_result(
            "runtime_resource_pressure_validator",
            "no runtime session directories were found for resource pressure inspection",
            [module_path],
            "HARD_TRUTH_MISSING",
        )
    for runtime_dir in runtime_dirs:
        pressure = inspect_runtime_resource_pressure(runtime_dir)
        if pressure.status == "FAIL":
            return blocked_result(
                "runtime_resource_pressure_validator",
                f"{pressure.message}: {rel(runtime_dir)}",
                paths,
                pressure.blocker_code or "RESOURCE_LIMIT_BLOCK",
            )
        if pressure.status not in {"PASS", "WARN"}:
            return fail_result(
                "runtime_resource_pressure_validator",
                f"unknown runtime resource pressure status: {pressure.status}",
                paths,
                "SCHEMA_IDENTITY_MISMATCH",
            )
    return pass_result(
        "runtime_resource_pressure_validator",
        f"{len(runtime_dirs)} runtime session directories are below hard resource pressure limits",
        paths,
    )


def paper_portfolio_snapshot_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "paper_portfolio_snapshot.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "portfolio" / "paper_portfolio.py"
    test_path = ROOT / "tests" / "runtime" / "test_paper_portfolio.py"
    paths = [schema_path, module_path, test_path]
    upbit = build_initial_paper_portfolio_snapshot(exchange="UPBIT", market_type="KRW_SPOT", session_id="validator-upbit-paper")
    upbit_result = validate_paper_portfolio_snapshot(upbit)
    if upbit_result.status != "PASS":
        return fail_result("paper_portfolio_snapshot_validator", upbit_result.message, paths, upbit_result.blocker_code or "UNKNOWN_BLOCKED")
    binance = build_initial_paper_portfolio_snapshot(exchange="BINANCE", market_type="SPOT", session_id="validator-binance-paper")
    binance_result = validate_paper_portfolio_snapshot(binance)
    if binance_result.status != "PASS":
        return fail_result("paper_portfolio_snapshot_validator", binance_result.message, paths, binance_result.blocker_code or "UNKNOWN_BLOCKED")
    filled = build_paper_portfolio_snapshot_from_fill(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        session_id="validator-upbit-paper-filled",
        symbol="KRW-BTC",
        side="BUY",
        quantity="0.01",
        fill_price="1000500",
        mark_price="1000000",
        fee_amount="5",
    )
    filled_result = validate_paper_portfolio_snapshot(filled)
    if filled_result.status != "PASS":
        return fail_result("paper_portfolio_snapshot_validator", filled_result.message, paths, filled_result.blocker_code or "UNKNOWN_BLOCKED")
    live_mutation = dict(upbit)
    live_mutation["live_order_allowed"] = True
    live_mutation["snapshot_hash"] = paper_portfolio_hash(live_mutation)
    live_result = validate_paper_portfolio_snapshot(live_mutation)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("paper_portfolio_snapshot_validator", "paper portfolio live mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")
    tampered = dict(upbit)
    tampered["equity"] = "2000000"
    tampered["snapshot_hash"] = paper_portfolio_hash(tampered)
    tampered_result = validate_paper_portfolio_snapshot(tampered)
    if tampered_result.status != "FAIL" or tampered_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("paper_portfolio_snapshot_validator", "paper portfolio arithmetic tamper was not detected", paths, "SCHEMA_IDENTITY_MISMATCH")
    position_tampered = json.loads(json.dumps(filled))
    position_tampered["positions"][0]["market_value"] = "9999"
    position_tampered["snapshot_hash"] = paper_portfolio_hash(position_tampered)
    position_tampered_result = validate_paper_portfolio_snapshot(position_tampered)
    if position_tampered_result.status != "FAIL" or position_tampered_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("paper_portfolio_snapshot_validator", "paper portfolio position detail tamper was not detected", paths, "SCHEMA_IDENTITY_MISMATCH")
    bad_scope = build_initial_paper_portfolio_snapshot(exchange="BINANCE", market_type="FUTURES_USDT_M", session_id="validator-bad-scope")
    bad_scope_result = validate_paper_portfolio_snapshot(bad_scope)
    if bad_scope_result.status != "BLOCKED" or bad_scope_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("paper_portfolio_snapshot_validator", "paper portfolio unsupported scope was not blocked", paths, "SNAPSHOT_SCOPE_MISMATCH")
    return pass_result("paper_portfolio_snapshot_validator", "paper portfolio snapshots are scoped, simulated, and live-blocked", paths)


def safety_control_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    schema_path = ROOT / "contracts" / "schema" / "safety_control_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "resource_guard" / "safety_control.py"
    paths = [registry_path, schema_path, module_path]
    registry = load_json(registry_path)
    allowed_blockers = set(registry["enums"]["live_blocker_code"]["values"])

    base = build_safety_control_report(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_safety_control",
    )
    result = validate_safety_control_report(base, allowed_blockers)
    if result.status != "PASS":
        return fail_result("safety_control_validator", result.message, paths, result.blocker_code or "LIVE_FINAL_GUARD_FAILED")
    if base.get("live_order_ready") or base.get("live_order_allowed") or base.get("can_live_trade") or base.get("can_submit_order"):
        return fail_result("safety_control_validator", "safety controls created live or order permission", paths, "LIVE_FINAL_GUARD_FAILED")

    manual_stop = build_safety_control_report(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_safety_control",
        operator_action="manual_stop",
    )
    manual_result = validate_safety_control_report(manual_stop, allowed_blockers)
    if manual_result.status != "PASS" or manual_stop["final_decision"] != "KILL_SWITCH" or manual_stop["primary_blocker_code"] != "KILL_SWITCH_ACTIVE":
        return fail_result("safety_control_validator", "manual_stop did not force kill switch block", paths, "KILL_SWITCH_ACTIVE")

    resource_critical = build_safety_control_report(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_safety_control",
        resource_metrics={"critical": True},
    )
    critical_result = validate_safety_control_report(resource_critical, allowed_blockers)
    critical_codes = {blocker["code"] for blocker in resource_critical["blockers"]}
    if critical_result.status != "PASS" or "RESOURCE_LIMIT_BLOCK" not in critical_codes or not resource_critical["resource_block_new_entries"]:
        return fail_result("safety_control_validator", "critical resource state did not block new entries", paths, "RESOURCE_LIMIT_BLOCK")

    unavailable = build_safety_control_report(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_safety_control",
        kill_switch_available=False,
    )
    unavailable_result = validate_safety_control_report(unavailable, allowed_blockers)
    if unavailable_result.status != "PASS" or unavailable["primary_blocker_code"] != "KILL_SWITCH_ACTIVE":
        return fail_result("safety_control_validator", "unavailable kill switch did not block readiness", paths, "KILL_SWITCH_ACTIVE")

    live_mutation = dict(base)
    live_mutation["live_order_allowed"] = True
    live_mutation["can_live_trade"] = True
    live_mutation["can_submit_order"] = True
    live_mutation["safety_control_hash"] = safety_control_hash(live_mutation)
    live_result = validate_safety_control_report(live_mutation, allowed_blockers)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("safety_control_validator", "safety control live permission mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    adapter_mutation = dict(base)
    adapter_mutation["order_adapter_called"] = True
    adapter_mutation["safety_control_hash"] = safety_control_hash(adapter_mutation)
    adapter_result = validate_safety_control_report(adapter_mutation, allowed_blockers)
    if adapter_result.status != "BLOCKED" or adapter_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("safety_control_validator", "safety control order adapter call was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    inconsistent = dict(resource_critical)
    inconsistent["resource_block_new_entries"] = False
    inconsistent["safety_control_hash"] = safety_control_hash(inconsistent)
    inconsistent_result = validate_safety_control_report(inconsistent, allowed_blockers)
    if inconsistent_result.status != "BLOCKED" or inconsistent_result.blocker_code != "RESOURCE_LIMIT_BLOCK":
        return fail_result("safety_control_validator", "critical resource inconsistency was not blocked", paths, "RESOURCE_LIMIT_BLOCK")

    return pass_result("safety_control_validator", "kill switch and resource guard scaffold remains fail-closed", paths)


def ledger_durability_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "ledger_event.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "ledger" / "execution_ledger.py"
    paths = [schema_path, module_path]
    chain = build_minimal_intent_chain(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_execution_ledger",
        intent_id="mvp1-intent",
        client_order_id="mvp1-client-order",
        symbol="KRW-BTC",
        side="BUY",
    )
    chain_result = validate_ledger_chain(chain)
    if chain_result.status != "PASS":
        return fail_result("ledger_durability_validator", chain_result.message, paths, chain_result.blocker_code or "LEDGER_INTEGRITY_FAIL")

    unknown_event = dict(chain[0])
    unknown_event["event_type"] = "UNKNOWN_EVENT"
    unknown_event["event_hash"] = ledger_event_hash(unknown_event)
    unknown_result = validate_ledger_event(unknown_event)
    if unknown_result.status != "BLOCKED" or unknown_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result("ledger_durability_validator", "unknown ledger event type did not require reconciliation", paths, "RECONCILIATION_REQUIRED")

    tampered = dict(chain[0])
    tampered["symbol"] = "KRW-ETH"
    tampered_result = validate_ledger_event(tampered)
    if tampered_result.status != "FAIL" or tampered_result.blocker_code != "LEDGER_INTEGRITY_FAIL":
        return fail_result("ledger_durability_validator", "ledger hash tamper did not fail integrity", paths, "LEDGER_INTEGRITY_FAIL")

    duplicate = [dict(event) for event in chain]
    duplicate[1]["dedup_key"] = duplicate[0]["dedup_key"]
    duplicate[1]["event_hash"] = ledger_event_hash(duplicate[1])
    duplicate_result = validate_ledger_chain(duplicate)
    if duplicate_result.status != "BLOCKED" or duplicate_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result("ledger_durability_validator", "duplicate ledger dedup_key did not require reconciliation", paths, "RECONCILIATION_REQUIRED")

    cross_scope = [dict(event) for event in chain]
    cross_scope[1]["market_type"] = "SPOT"
    cross_scope[1]["event_hash"] = ledger_event_hash(cross_scope[1])
    cross_result = validate_ledger_chain(cross_scope)
    if cross_result.status != "BLOCKED" or cross_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("ledger_durability_validator", "cross-scope ledger chain was not blocked", paths, "SNAPSHOT_SCOPE_MISMATCH")

    return pass_result("ledger_durability_validator", "ledger events are hash-linked, closed-enum, and namespace-scoped", paths)


def paper_ledger_rollup_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "paper_ledger_rollup_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "ledger" / "paper_ledger_rollup.py"
    loop_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_persistent_loop.py"
    test_path = ROOT / "tests" / "runtime" / "test_paper_ledger_rollup.py"
    paths = [schema_path, module_path, loop_path, test_path]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.paper_ledger_rollup_report.v1":
        return fail_result("paper_ledger_rollup_validator", "paper ledger rollup schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("paper_ledger_rollup_validator", "paper ledger rollup schema must reject unknown fields", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "ledger_jsonl_count",
        "ledger_event_count",
        "filled_order_count",
        "duplicate_event_count",
        "duplicate_order_count",
        "lifecycle_incomplete_order_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "invalid_ledger_jsonl_count",
        "portfolio_snapshot",
        "display_only",
        "dashboard_truth_only",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("paper_ledger_rollup_validator", f"paper ledger rollup schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        loop = run_upbit_paper_persistent_loop(
            root=root,
            loop_id="validator-paper-ledger-rollup",
            requested_cycle_count=2,
        )
        result = validate_upbit_paper_persistent_loop_report(loop)
        if result.status != "PASS":
            return fail_result("paper_ledger_rollup_validator", f"persistent loop failed before rollup validation: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
        rollup_path = root / str(loop["paper_ledger_rollup_path"])
        if not rollup_path.exists():
            return fail_result("paper_ledger_rollup_validator", "persistent loop did not write paper ledger rollup artifact", paths, "MEASUREMENT_MISSING")
        rollup = load_json(rollup_path)
        rollup_result = validate_paper_ledger_rollup_report(rollup)
        if rollup_result.status != "PASS":
            return fail_result("paper_ledger_rollup_validator", f"valid paper ledger rollup failed: {rollup_result.message}", paths, rollup_result.blocker_code or "UNKNOWN_BLOCKED")
        if rollup.get("ledger_jsonl_count") != 2 or rollup.get("filled_order_count") != 2:
            return fail_result("paper_ledger_rollup_validator", "paper ledger rollup did not aggregate both cycle ledgers", paths, "MEASUREMENT_MISSING")
        if rollup.get("lifecycle_incomplete_order_count") != 0:
            return fail_result("paper_ledger_rollup_validator", "valid paper ledger rollup reported incomplete order lifecycle", paths, "RECONCILIATION_REQUIRED")
        if rollup.get("portfolio_snapshot", {}).get("source") != "PAPER_LEDGER_ROLLUP":
            return fail_result("paper_ledger_rollup_validator", "paper ledger rollup portfolio source is not explicit", paths, "LIVE_FINAL_GUARD_FAILED")
        if rollup.get("live_order_allowed") or rollup.get("can_live_trade") or rollup.get("scale_up_allowed"):
            return fail_result("paper_ledger_rollup_validator", "paper ledger rollup created live or scale-up permission", paths, "LIVE_FINAL_GUARD_FAILED")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        loop = run_upbit_paper_persistent_loop(
            root=root,
            loop_id="validator-paper-ledger-rollup-duplicate",
            requested_cycle_count=1,
        )
        first_path = None
        for artifact_path in loop["cycle_results"][0]["artifact_paths"]:
            if str(artifact_path).endswith(".paper_ledger_events.jsonl"):
                first_path = root / str(artifact_path)
                break
        if first_path is None:
            return fail_result("paper_ledger_rollup_validator", "test loop did not write ledger JSONL for duplicate guard", paths, "LEDGER_UNAVAILABLE")
        duplicate_path = first_path.with_name("duplicate-cross-cycle.paper_ledger_events.jsonl")
        duplicate_path.write_text(first_path.read_text(encoding="utf-8"), encoding="utf-8")
        duplicate_rollup = build_paper_ledger_rollup_report(
            root=root,
            session_id="mvp1_upbit_paper_launcher",
            rollup_id="validator-paper-ledger-rollup-duplicate",
        )
        duplicate_result = validate_paper_ledger_rollup_report(duplicate_rollup)
        if duplicate_result.status != "BLOCKED" or duplicate_result.blocker_code != "RECONCILIATION_REQUIRED":
            return fail_result("paper_ledger_rollup_validator", "cross-cycle duplicate ledger event was not blocked", paths, "RECONCILIATION_REQUIRED")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        ledger_dir = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "ledger" / "cycles"
        ledger_dir.mkdir(parents=True)
        intent = build_ledger_event(
            event_id="validator-incomplete-intent",
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="mvp1_upbit_paper_launcher",
            event_type="ORDER_INTENT_CREATED",
            source="LOCAL",
            dedup_key="intent:validator-incomplete",
            intent_id="intent-validator-incomplete",
            client_order_id="client-validator-incomplete",
            symbol="KRW-BTC",
            side="BUY",
        )
        reservation = build_ledger_event(
            event_id="validator-incomplete-reserve",
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="mvp1_upbit_paper_launcher",
            event_type="BUDGET_RESERVED",
            source="LOCAL",
            dedup_key="reserve:validator-incomplete",
            previous_hash=intent["event_hash"],
            intent_id="intent-validator-incomplete",
            client_order_id="client-validator-incomplete",
            symbol="KRW-BTC",
            side="BUY",
        )
        filled = build_ledger_event(
            event_id="validator-incomplete-filled",
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="mvp1_upbit_paper_launcher",
            event_type="ORDER_FILLED",
            source="LOCAL",
            dedup_key="filled:validator-incomplete",
            previous_hash=reservation["event_hash"],
            intent_id="intent-validator-incomplete",
            client_order_id="client-validator-incomplete",
            order_id="PAPER-client-validator-incomplete",
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.001",
            price="100000000",
            fee_amount="50",
            fee_asset="KRW",
            balance_delta={"KRW": "-50"},
            position_delta={"symbol": "KRW-BTC", "quantity": "0.001", "side": "BUY"},
        )
        incomplete_path = ledger_dir / "validator-incomplete.paper_ledger_events.jsonl"
        incomplete_path.write_text(
            "\n".join(json.dumps(event, sort_keys=True) for event in (intent, reservation, filled)) + "\n",
            encoding="utf-8",
        )
        incomplete_rollup = build_paper_ledger_rollup_report(
            root=root,
            session_id="mvp1_upbit_paper_launcher",
            rollup_id="validator-paper-ledger-rollup-incomplete-lifecycle",
        )
        incomplete_result = validate_paper_ledger_rollup_report(incomplete_rollup)
        if (
            incomplete_result.status != "BLOCKED"
            or incomplete_result.blocker_code != "RECONCILIATION_REQUIRED"
            or incomplete_rollup.get("lifecycle_incomplete_order_count") != 1
        ):
            return fail_result("paper_ledger_rollup_validator", "incomplete filled order lifecycle was not blocked", paths, "RECONCILIATION_REQUIRED")

    with TemporaryDirectory() as tmp:
        empty_rollup = build_paper_ledger_rollup_report(
            root=Path(tmp),
            session_id="mvp1_upbit_paper_launcher",
            rollup_id="validator-paper-ledger-rollup-empty",
        )
        empty_result = validate_paper_ledger_rollup_report(empty_rollup)
        if empty_result.status != "BLOCKED" or empty_result.blocker_code != "LEDGER_UNAVAILABLE":
            return fail_result("paper_ledger_rollup_validator", "empty paper ledger rollup was not blocked", paths, "LEDGER_UNAVAILABLE")

    live_mutation = dict(rollup)
    live_mutation["live_order_allowed"] = True
    live_mutation["rollup_hash"] = paper_ledger_rollup_hash(live_mutation)
    live_result = validate_paper_ledger_rollup_report(live_mutation)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("paper_ledger_rollup_validator", "paper ledger rollup live mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    portfolio_scope = json.loads(json.dumps(rollup))
    portfolio_scope["portfolio_snapshot"]["exchange"] = "BINANCE"
    portfolio_scope["portfolio_snapshot"]["market_type"] = "SPOT"
    portfolio_scope["portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(portfolio_scope["portfolio_snapshot"])
    portfolio_scope["rollup_hash"] = paper_ledger_rollup_hash(portfolio_scope)
    portfolio_scope_result = validate_paper_ledger_rollup_report(portfolio_scope)
    if portfolio_scope_result.status != "BLOCKED" or portfolio_scope_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("paper_ledger_rollup_validator", "paper ledger rollup cross-scope portfolio snapshot was not blocked", paths, "SNAPSHOT_SCOPE_MISMATCH")

    count_mismatch = json.loads(json.dumps(rollup))
    count_mismatch["filled_order_count"] = 0
    count_mismatch["rollup_hash"] = paper_ledger_rollup_hash(count_mismatch)
    count_mismatch_result = validate_paper_ledger_rollup_report(count_mismatch)
    if count_mismatch_result.status != "FAIL" or count_mismatch_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("paper_ledger_rollup_validator", "paper ledger rollup filled count mismatch was not failed closed", paths, "SCHEMA_IDENTITY_MISMATCH")

    path_escape = json.loads(json.dumps(rollup))
    path_escape["artifact_paths"].append("system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/ledger/unsafe.json")
    path_escape["rollup_hash"] = paper_ledger_rollup_hash(path_escape)
    path_escape_result = validate_paper_ledger_rollup_report(path_escape)
    if path_escape_result.status != "BLOCKED" or path_escape_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("paper_ledger_rollup_validator", "paper ledger rollup artifact path escape was not blocked", paths, "SNAPSHOT_SCOPE_MISMATCH")
    return pass_result("paper_ledger_rollup_validator", "PAPER ledger rollup aggregates cycle ledgers, blocks duplicates, and stays live-blocked", paths)


def reconciliation_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    schema_path = ROOT / "contracts" / "schema" / "reconciliation_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "reconciliation" / "reconciliation.py"
    paths = [schema_path, module_path]
    registry = load_json(registry_path)
    allowed_blockers = set(registry["enums"]["live_blocker_code"]["values"])
    schema = load_json(schema_path)
    required = set(schema.get("required", []))
    expected_required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "reconciliation_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "ledger_head_hash",
        "exchange_snapshot_hash",
        "internal_state_hash",
        "reconciliation_status",
        "final_decision",
        "primary_blocker_code",
        "blockers",
        "mismatches",
        "new_entry_allowed",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "order_adapter_called",
        "reconciliation_hash",
    }
    if not expected_required.issubset(required):
        return fail_result("reconciliation_validator", "reconciliation report schema lost required safety fields", paths, "SCHEMA_IDENTITY_MISMATCH")

    base = build_reconciliation_report(reconciliation_id="validator-pass")
    base_result = validate_reconciliation_report(base, allowed_blockers)
    if base_result.status != "PASS":
        return fail_result("reconciliation_validator", base_result.message, paths, base_result.blocker_code or "RECONCILIATION_REQUIRED")
    if base.get("new_entry_allowed") or base.get("live_order_ready") or base.get("live_order_allowed") or base.get("can_live_trade") or base.get("can_submit_order"):
        return fail_result("reconciliation_validator", "PASS reconciliation created live or entry permission", paths, "LIVE_FINAL_GUARD_FAILED")

    stale = build_reconciliation_report(reconciliation_id="validator-stale", fresh=False)
    stale_result = validate_reconciliation_report(stale, allowed_blockers)
    if stale_result.status != "PASS" or stale["reconciliation_status"] != "STALE" or stale["primary_blocker_code"] != "RECONCILIATION_REQUIRED":
        return fail_result("reconciliation_validator", "stale reconciliation did not require reconciliation", paths, "RECONCILIATION_REQUIRED")

    mismatch = build_reconciliation_report(
        reconciliation_id="validator-mismatch",
        exchange_snapshot={"balances": {"KRW": "1000"}, "positions": [], "open_orders": []},
        internal_state={"balances": {"KRW": "900"}, "positions": [], "open_orders": []},
    )
    mismatch_result = validate_reconciliation_report(mismatch, allowed_blockers)
    if mismatch_result.status != "PASS" or mismatch["reconciliation_status"] != "MISMATCH" or not mismatch["mismatches"]:
        return fail_result("reconciliation_validator", "balance mismatch did not produce reconciliation blocker details", paths, "RECONCILIATION_REQUIRED")
    crafted_mismatch = build_reconciliation_report(reconciliation_id="validator-crafted-mismatch")
    crafted_mismatch["internal_state"] = {
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": "mvp1_reconciliation",
        "balances": {"KRW": "900"},
        "positions": [],
        "open_orders": [],
    }
    crafted_mismatch["reconciliation_status"] = "PASS"
    crafted_mismatch["final_decision"] = "NO_TRADE"
    crafted_mismatch["primary_blocker_code"] = None
    crafted_mismatch["blockers"] = []
    crafted_mismatch["mismatches"] = []
    crafted_mismatch["internal_state_hash"] = snapshot_hash(crafted_mismatch["internal_state"])
    crafted_mismatch["reconciliation_hash"] = reconciliation_report_hash(crafted_mismatch)
    crafted_mismatch_result = validate_reconciliation_report(crafted_mismatch, allowed_blockers)
    if crafted_mismatch_result.status != "BLOCKED" or crafted_mismatch_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result(
            "reconciliation_validator",
            "crafted PASS reconciliation with mismatched snapshots was not blocked",
            paths,
            "RECONCILIATION_REQUIRED",
        )
    snapshot_hash_mismatch = build_reconciliation_report(reconciliation_id="validator-snapshot-hash-mismatch")
    snapshot_hash_mismatch["internal_state"] = {
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": "mvp1_reconciliation",
        "balances": {"KRW": "900"},
        "positions": [],
        "open_orders": [],
    }
    snapshot_hash_mismatch["reconciliation_hash"] = reconciliation_report_hash(snapshot_hash_mismatch)
    snapshot_hash_mismatch_result = validate_reconciliation_report(snapshot_hash_mismatch, allowed_blockers)
    if snapshot_hash_mismatch_result.status != "FAIL" or snapshot_hash_mismatch_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result(
            "reconciliation_validator",
            "snapshot body/hash mismatch was not failed closed",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )

    scope_mismatch = build_reconciliation_report(
        reconciliation_id="validator-scope",
        exchange_snapshot={"exchange": "UPBIT", "market_type": "KRW_SPOT", "mode": "PAPER", "session_id": "other"},
        internal_state={"exchange": "UPBIT", "market_type": "KRW_SPOT", "mode": "PAPER", "session_id": "mvp1_reconciliation"},
    )
    scope_result = validate_reconciliation_report(scope_mismatch, allowed_blockers)
    if scope_result.status != "PASS" or scope_mismatch["primary_blocker_code"] != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("reconciliation_validator", "namespace mismatch did not block reconciliation", paths, "SNAPSHOT_SCOPE_MISMATCH")

    missing = build_reconciliation_report(reconciliation_id="validator-missing", ledger_head_hash=None)
    missing_result = validate_reconciliation_report(missing, allowed_blockers)
    if missing_result.status != "PASS" or missing["primary_blocker_code"] != "HARD_TRUTH_MISSING":
        return fail_result("reconciliation_validator", "missing hard truth did not block reconciliation", paths, "HARD_TRUTH_MISSING")

    live_mutation = dict(base)
    live_mutation["live_order_allowed"] = True
    live_mutation["can_live_trade"] = True
    live_mutation["can_submit_order"] = True
    live_mutation["reconciliation_hash"] = reconciliation_report_hash(live_mutation)
    live_result = validate_reconciliation_report(live_mutation, allowed_blockers)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("reconciliation_validator", "reconciliation live permission mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    adapter_mutation = dict(base)
    adapter_mutation["order_adapter_called"] = True
    adapter_mutation["reconciliation_hash"] = reconciliation_report_hash(adapter_mutation)
    adapter_result = validate_reconciliation_report(adapter_mutation, allowed_blockers)
    if adapter_result.status != "BLOCKED" or adapter_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("reconciliation_validator", "reconciliation order adapter call was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    tampered = dict(base)
    tampered["session_id"] = "tampered"
    tampered_result = validate_reconciliation_report(tampered, allowed_blockers)
    if tampered_result.status != "FAIL" or tampered_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("reconciliation_validator", "reconciliation hash tamper did not fail", paths, "SCHEMA_IDENTITY_MISMATCH")

    return pass_result("reconciliation_validator", "reconciliation reports are scoped, hash-checked, and fail-closed", paths)


def ledger_reconciliation_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "reconciliation_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "reconciliation" / "reconciliation.py"
    ledger_path = ROOT / "trader1" / "runtime" / "ledger" / "execution_ledger.py"
    paths = [schema_path, module_path, ledger_path]

    chain = build_minimal_intent_chain(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_reconciliation",
        intent_id="reconcile-intent",
        client_order_id="reconcile-client-order",
        symbol="KRW-BTC",
        side="BUY",
    )
    chain_result = validate_ledger_chain(chain)
    if chain_result.status != "PASS":
        return fail_result("ledger_reconciliation_validator", chain_result.message, paths, chain_result.blocker_code or "LEDGER_INTEGRITY_FAIL")

    report = build_reconciliation_report(
        reconciliation_id="validator-ledger-reconcile",
        ledger_head_hash=chain[-1]["event_hash"],
    )
    report_result = validate_reconciliation_report(report)
    if report_result.status != "PASS" or report["ledger_head_hash"] != chain[-1]["event_hash"]:
        return fail_result("ledger_reconciliation_validator", "ledger head was not preserved in reconciliation report", paths, "LEDGER_INTEGRITY_FAIL")
    if report.get("new_entry_allowed") or report.get("live_order_allowed") or report.get("can_live_trade"):
        return fail_result("ledger_reconciliation_validator", "ledger reconciliation created live or entry permission", paths, "LIVE_FINAL_GUARD_FAILED")

    missing_ledger = build_reconciliation_report(
        reconciliation_id="validator-ledger-missing",
        ledger_head_hash=None,
    )
    missing_result = validate_reconciliation_report(missing_ledger)
    if missing_result.status != "PASS" or missing_ledger["primary_blocker_code"] != "HARD_TRUTH_MISSING":
        return fail_result("ledger_reconciliation_validator", "missing ledger head did not block reconciliation", paths, "HARD_TRUTH_MISSING")

    stale = build_reconciliation_report(
        reconciliation_id="validator-ledger-stale",
        ledger_head_hash=chain[-1]["event_hash"],
        fresh=False,
    )
    stale_result = validate_reconciliation_report(stale)
    if stale_result.status != "PASS" or stale["primary_blocker_code"] != "RECONCILIATION_REQUIRED":
        return fail_result("ledger_reconciliation_validator", "stale ledger reconciliation did not block entries", paths, "RECONCILIATION_REQUIRED")

    return pass_result("ledger_reconciliation_validator", "ledger reconciliation remains hard-truth-gated and fail-closed", paths)


def emergency_flatten_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    schema_path = ROOT / "contracts" / "schema" / "emergency_flatten_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "protection" / "emergency_flatten.py"
    operator_path = ROOT / "trader1" / "runtime" / "operator_control" / "operator_control.py"
    paths = [schema_path, module_path, operator_path]
    registry = load_json(registry_path)
    allowed_blockers = set(registry["enums"]["live_blocker_code"]["values"])
    schema = load_json(schema_path)
    required = set(schema.get("required", []))
    expected_required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "emergency_flatten_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "emergency_protection_available",
        "emergency_flatten_available",
        "manual_exit_all_positions_available",
        "manual_reduce_position_available",
        "cancel_all_open_orders_available",
        "reduce_only_path_available_for_futures",
        "reconciliation_path_available",
        "operator_alert_available",
        "ledger_recording_available",
        "dry_run",
        "dry_run_status",
        "dry_run_actions",
        "component_checks",
        "new_entry_allowed",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "order_adapter_called",
        "emergency_flatten_hash",
    }
    if not expected_required.issubset(required):
        return fail_result("emergency_flatten_validator", "emergency flatten schema lost required safety fields", paths, "SCHEMA_IDENTITY_MISMATCH")

    base = build_emergency_flatten_report(emergency_flatten_id="validator-pass")
    base_result = validate_emergency_flatten_report(base, allowed_blockers)
    if base_result.status != "PASS":
        return fail_result("emergency_flatten_validator", base_result.message, paths, base_result.blocker_code or "EMERGENCY_FLATTEN_UNAVAILABLE")
    if base.get("live_order_ready") or base.get("live_order_allowed") or base.get("can_live_trade") or base.get("can_submit_order") or base.get("new_entry_allowed"):
        return fail_result("emergency_flatten_validator", "emergency flatten created live or entry permission", paths, "LIVE_FINAL_GUARD_FAILED")

    missing_cancel = build_emergency_flatten_report(
        emergency_flatten_id="validator-missing-cancel",
        cancel_all_open_orders_available=False,
    )
    missing_cancel_result = validate_emergency_flatten_report(missing_cancel, allowed_blockers)
    if missing_cancel_result.status != "PASS" or missing_cancel["primary_blocker_code"] != "EMERGENCY_FLATTEN_UNAVAILABLE":
        return fail_result("emergency_flatten_validator", "missing cancel-all path did not block emergency protection", paths, "EMERGENCY_FLATTEN_UNAVAILABLE")

    missing_reconcile = build_emergency_flatten_report(
        emergency_flatten_id="validator-missing-reconcile",
        reconciliation_path_available=False,
    )
    missing_reconcile_result = validate_emergency_flatten_report(missing_reconcile, allowed_blockers)
    if missing_reconcile_result.status != "PASS" or missing_reconcile["primary_blocker_code"] != "RECONCILIATION_REQUIRED":
        return fail_result("emergency_flatten_validator", "missing reconciliation path did not block emergency protection", paths, "RECONCILIATION_REQUIRED")

    orphan_position = build_emergency_flatten_report(
        emergency_flatten_id="validator-orphan-position",
        orphan_position_state="PRESENT",
    )
    orphan_position_result = validate_emergency_flatten_report(orphan_position, allowed_blockers)
    if orphan_position_result.status != "PASS" or orphan_position["primary_blocker_code"] != "ORPHAN_POSITION_REVIEW_REQUIRED":
        return fail_result("emergency_flatten_validator", "orphan position state did not block emergency protection", paths, "ORPHAN_POSITION_REVIEW_REQUIRED")

    orphan_order = build_emergency_flatten_report(
        emergency_flatten_id="validator-orphan-order",
        orphan_open_order_state="UNKNOWN",
    )
    orphan_order_result = validate_emergency_flatten_report(orphan_order, allowed_blockers)
    if orphan_order_result.status != "PASS" or orphan_order["primary_blocker_code"] != "ORPHAN_OPEN_ORDER_REVIEW_REQUIRED":
        return fail_result("emergency_flatten_validator", "orphan open order state did not block emergency protection", paths, "ORPHAN_OPEN_ORDER_REVIEW_REQUIRED")

    futures_missing = build_emergency_flatten_report(
        emergency_flatten_id="validator-futures",
        exchange="BINANCE",
        market_type="FUTURES_USDT_M",
        reduce_only_path_available_for_futures=False,
    )
    futures_result = validate_emergency_flatten_report(futures_missing, allowed_blockers)
    if futures_result.status != "PASS" or futures_missing["primary_blocker_code"] != "EMERGENCY_FLATTEN_UNAVAILABLE":
        return fail_result("emergency_flatten_validator", "futures missing reduce-only path did not block emergency protection", paths, "EMERGENCY_FLATTEN_UNAVAILABLE")

    scope_mismatch = build_emergency_flatten_report(
        emergency_flatten_id="validator-scope",
        component_scope_overrides={"ledger_recording": {"session_id": "wrong-session"}},
    )
    scope_result = validate_emergency_flatten_report(scope_mismatch, allowed_blockers)
    if scope_result.status != "PASS" or scope_mismatch["primary_blocker_code"] != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("emergency_flatten_validator", "component scope mismatch did not block emergency protection", paths, "SNAPSHOT_SCOPE_MISMATCH")

    live_mutation = dict(base)
    live_mutation["live_order_allowed"] = True
    live_mutation["can_live_trade"] = True
    live_mutation["can_submit_order"] = True
    live_mutation["emergency_flatten_hash"] = emergency_flatten_hash(live_mutation)
    live_result = validate_emergency_flatten_report(live_mutation, allowed_blockers)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("emergency_flatten_validator", "emergency live permission mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    adapter_mutation = dict(base)
    adapter_mutation["order_adapter_called"] = True
    adapter_mutation["emergency_flatten_hash"] = emergency_flatten_hash(adapter_mutation)
    adapter_result = validate_emergency_flatten_report(adapter_mutation, allowed_blockers)
    if adapter_result.status != "BLOCKED" or adapter_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("emergency_flatten_validator", "emergency adapter call mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    real_run = build_emergency_flatten_report(emergency_flatten_id="validator-real-run", dry_run=False)
    real_result = validate_emergency_flatten_report(real_run, allowed_blockers)
    if real_result.status != "BLOCKED" or real_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("emergency_flatten_validator", "MVP-1 non-dry-run emergency flatten was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    tampered = dict(base)
    tampered["session_id"] = "tampered"
    tampered_result = validate_emergency_flatten_report(tampered, allowed_blockers)
    if tampered_result.status != "FAIL" or tampered_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("emergency_flatten_validator", "emergency flatten hash tamper did not fail", paths, "SCHEMA_IDENTITY_MISMATCH")

    manual_exit = build_operator_action_audit(
        action_id="emergency-manual-exit",
        operator_id_hash="operator-hash",
        action_code="manual_exit_all_positions",
        session_id="mvp1_emergency_flatten",
        target_symbol="KRW-BTC",
    )
    manual_exit_result = validate_operator_action_audit(manual_exit)
    if manual_exit_result.status != "BLOCKED" or manual_exit_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result("emergency_flatten_validator", "manual emergency exit did not require reconciliation", paths, "RECONCILIATION_REQUIRED")

    return pass_result("emergency_flatten_validator", "emergency flatten dry-run is auditable, scoped, and live-blocked", paths)


def operator_action_audit_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "operator_action_audit.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "operator_control" / "operator_control.py"
    paths = [schema_path, module_path]
    schema = load_json(schema_path)
    required = set(schema.get("required", []))
    expected_required = {
        "schema_id",
        "action_id",
        "created_at_utc",
        "operator_id_hash",
        "action_code",
        "confirmation_required",
        "confirmation_method",
        "result",
        "event_hash",
    }
    if not expected_required.issubset(required):
        return fail_result("operator_action_audit_validator", "operator action audit schema lost required audit fields", paths, "SCHEMA_IDENTITY_MISMATCH")

    record = build_operator_action_audit(
        action_id="audit-1",
        operator_id_hash="operator-hash",
        action_code="manual_stop",
        session_id="mvp1_operator_control",
    )
    result = validate_operator_action_audit(record)
    if result.status != "PASS":
        return fail_result("operator_action_audit_validator", result.message, paths, result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    tampered = dict(record)
    tampered["target_symbol"] = "KRW-ETH"
    tampered_result = validate_operator_action_audit(tampered)
    if tampered_result.status != "FAIL" or tampered_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("operator_action_audit_validator", "operator audit hash tamper did not fail", paths, "SCHEMA_IDENTITY_MISMATCH")

    missing_confirmation = build_operator_action_audit(
        action_id="audit-2",
        operator_id_hash="operator-hash",
        action_code="manual_safe_mode",
        session_id="mvp1_operator_control",
    )
    missing_confirmation["confirmation_required"] = False
    missing_confirmation["event_hash"] = operator_action_hash(missing_confirmation)
    missing_result = validate_operator_action_audit(missing_confirmation)
    if missing_result.status != "BLOCKED" or missing_result.blocker_code != "OPERATOR_APPROVAL_MISSING":
        return fail_result("operator_action_audit_validator", "high-risk operator action without confirmation was not blocked", paths, "OPERATOR_APPROVAL_MISSING")

    return pass_result("operator_action_audit_validator", "operator action audits are closed, hash-checked, and confirmation-gated", paths)


def operator_control_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "operator_action_audit.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "operator_control" / "operator_control.py"
    paths = [schema_path, module_path]

    manual_stop = build_operator_action_audit(
        action_id="operator-1",
        operator_id_hash="operator-hash",
        action_code="manual_stop",
        session_id="mvp1_operator_control",
    )
    manual_stop_result = validate_operator_action_audit(manual_stop)
    if manual_stop_result.status != "PASS" or manual_stop["final_decision_id"] != "KILL_SWITCH" or manual_stop["result"] != "BLOCKED":
        return fail_result("operator_control_validator", "manual_stop did not force kill switch blocked audit", paths, "KILL_SWITCH_ACTIVE")

    safe_mode = build_operator_action_audit(
        action_id="operator-2",
        operator_id_hash="operator-hash",
        action_code="manual_safe_mode",
        session_id="mvp1_operator_control",
    )
    safe_mode_result = validate_operator_action_audit(safe_mode)
    if safe_mode_result.status != "PASS" or safe_mode["final_decision_id"] != "SAFE_MODE":
        return fail_result("operator_control_validator", "manual_safe_mode did not keep safe mode blocked audit", paths, "LIVE_FINAL_GUARD_FAILED")

    read_only = build_operator_action_audit(
        action_id="operator-3",
        operator_id_hash="operator-hash",
        action_code="manual_resume_read_only",
        session_id="mvp1_operator_control",
    )
    read_only_result = validate_operator_action_audit(read_only)
    if read_only_result.status != "PASS" or read_only["requested_state"].get("mode") != "READ_ONLY":
        return fail_result("operator_control_validator", "manual_resume_read_only did not remain read-only", paths, "LIVE_FINAL_GUARD_FAILED")

    reduce_without_reconcile = build_operator_action_audit(
        action_id="operator-4",
        operator_id_hash="operator-hash",
        action_code="manual_reduce_position",
        session_id="mvp1_operator_control",
        target_symbol="KRW-BTC",
    )
    reduce_result = validate_operator_action_audit(reduce_without_reconcile)
    if reduce_result.status != "BLOCKED" or reduce_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result("operator_control_validator", "manual_reduce_position without reconciliation was not blocked", paths, "RECONCILIATION_REQUIRED")

    live_mutation = build_operator_action_audit(
        action_id="operator-5",
        operator_id_hash="operator-hash",
        action_code="manual_resume_read_only",
        session_id="mvp1_operator_control",
        requested_state={"live_order_allowed": True, "can_live_trade": True, "can_submit_order": True},
    )
    live_mutation["event_hash"] = operator_action_hash(live_mutation)
    live_result = validate_operator_action_audit(live_mutation)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("operator_control_validator", "manual live permission mutation was not blocked", paths, "LIVE_FINAL_GUARD_FAILED")

    unknown = build_operator_action_audit(
        action_id="operator-6",
        operator_id_hash="operator-hash",
        action_code="manual_reduce_or_close_position",
        session_id="mvp1_operator_control",
    )
    unknown_result = validate_operator_action_audit(unknown)
    if unknown_result.status != "BLOCKED" or unknown_result.blocker_code != "UNKNOWN_BLOCKED":
        return fail_result("operator_control_validator", "unknown operator action was not blocked", paths, "UNKNOWN_BLOCKED")

    return pass_result("operator_control_validator", "operator controls remain audit-only and cannot create live permission", paths)


def upbit_paper_dry_run_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_dry_run_report.schema.json"
    broker_path = ROOT / "trader1" / "adapters" / "upbit" / "paper_broker.py"
    market_data_path = ROOT / "trader1" / "adapters" / "upbit" / "market_data.py"
    symbol_rules_path = ROOT / "trader1" / "adapters" / "upbit" / "symbol_rules.py"
    fee_model_path = ROOT / "trader1" / "adapters" / "upbit" / "fee_model.py"
    paper_ledger_path = ROOT / "trader1" / "core" / "ledger" / "paper_ledger.py"
    paths = [schema_path, broker_path, market_data_path, symbol_rules_path, fee_model_path, paper_ledger_path]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_dry_run_report.v1":
        return fail_result("upbit_paper_dry_run_validator", "Upbit paper dry-run schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    expected_required = {
        "paper_run_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "public_market_data",
        "paper_order_submitted",
        "final_decision",
        "no_trade_reasons",
        "entry_reasons",
        "paper_ledger_events",
        "paper_ledger_write_status",
        "paper_live_namespace_separated",
        "live_key_loaded",
        "binance_live_touched",
        "strategy_promotion_attempted",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "order_adapter_called",
        "dry_run_hash",
    }
    missing = sorted(expected_required - required)
    if missing:
        return fail_result("upbit_paper_dry_run_validator", f"Upbit paper dry-run schema missing required fields: {missing}", paths, "SCHEMA_IDENTITY_MISMATCH")

    registry = load_json(ROOT / "contracts" / "registry.yaml")
    allowed_blockers = set(registry["enums"]["live_blocker_code"]["values"])

    entry = build_upbit_paper_dry_run_report(paper_run_id="validator-paper-entry")
    entry_result = validate_upbit_paper_dry_run_report(entry, allowed_blockers)
    if entry_result.status != "PASS":
        return fail_result("upbit_paper_dry_run_validator", f"valid paper entry dry-run failed: {entry_result.message}", paths, entry_result.blocker_code or "UNKNOWN_BLOCKED")
    if entry.get("final_decision") != "ENTER_LONG" or entry.get("paper_order_submitted") is not True:
        return fail_result("upbit_paper_dry_run_validator", "paper entry dry-run did not create simulated entry intent", paths, "MEASUREMENT_MISSING")
    if entry.get("paper_ledger_write_status") != "WRITTEN" or not entry.get("paper_ledger_events"):
        return fail_result("upbit_paper_dry_run_validator", "paper entry dry-run did not write the paper ledger", paths, "LEDGER_UNAVAILABLE")
    if entry.get("live_order_ready") or entry.get("live_order_allowed") or entry.get("can_live_trade") or entry.get("can_submit_order") or entry.get("order_adapter_called"):
        return fail_result("upbit_paper_dry_run_validator", "paper entry dry-run created forbidden live/order permission", paths, "LIVE_FINAL_GUARD_FAILED")

    no_trade = build_upbit_paper_dry_run_report(paper_run_id="validator-paper-no-trade", requested_entry=False)
    no_trade_result = validate_upbit_paper_dry_run_report(no_trade, allowed_blockers)
    if no_trade_result.status != "PASS" or "MIN_EDGE_FAIL" not in no_trade.get("no_trade_reasons", []):
        return fail_result("upbit_paper_dry_run_validator", "no-trade dry-run did not preserve no-trade reason logging", paths, no_trade_result.blocker_code or "MEASUREMENT_MISSING")

    bad_symbol = build_upbit_paper_dry_run_report(paper_run_id="validator-paper-bad-symbol", symbol="BTC-USDT")
    bad_symbol_result = validate_upbit_paper_dry_run_report(bad_symbol, allowed_blockers)
    if bad_symbol_result.status != "PASS" or bad_symbol.get("primary_blocker_code") != "SYMBOL_RULE_UNVERIFIED":
        return fail_result("upbit_paper_dry_run_validator", "bad symbol did not remain blocked with a symbol-rule reason", paths, bad_symbol_result.blocker_code or "SYMBOL_RULE_UNVERIFIED")

    wrong_scope = build_upbit_paper_dry_run_report(
        paper_run_id="validator-paper-wrong-scope",
        exchange="BINANCE",
        market_type="SPOT",
    )
    wrong_scope_result = validate_upbit_paper_dry_run_report(wrong_scope, allowed_blockers)
    if wrong_scope_result.status != "BLOCKED" or wrong_scope_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("upbit_paper_dry_run_validator", "non-Upbit paper scope was not blocked", paths, wrong_scope_result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH")

    private_data = build_upbit_public_market_data_fixture(symbol="KRW-BTC", session_id="mvp2_upbit_paper")
    private_data["private_account_fields_present"] = True
    private_mix = build_upbit_paper_dry_run_report(paper_run_id="validator-paper-private-data", public_market_data=private_data)
    private_result = validate_upbit_paper_dry_run_report(private_mix, allowed_blockers)
    if private_result.status != "BLOCKED" or private_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_paper_dry_run_validator", "paper public data path allowed private-field mixing", paths, private_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    for field in ("live_order_allowed", "can_live_trade", "can_submit_order", "order_adapter_called", "strategy_promotion_attempted"):
        mutated = build_upbit_paper_dry_run_report(paper_run_id=f"validator-paper-mutated-{field}")
        mutated[field] = True
        mutated["dry_run_hash"] = upbit_paper_dry_run_hash(mutated)
        mutated_result = validate_upbit_paper_dry_run_report(mutated, allowed_blockers)
        if mutated_result.status != "BLOCKED" or mutated_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("upbit_paper_dry_run_validator", f"forbidden mutation was not blocked: {field}", paths, mutated_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    tampered = build_upbit_paper_dry_run_report(paper_run_id="validator-paper-tampered")
    tampered["symbol"] = "KRW-ETH"
    tampered_result = validate_upbit_paper_dry_run_report(tampered, allowed_blockers)
    if tampered_result.status != "FAIL" or tampered_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("upbit_paper_dry_run_validator", "paper dry-run hash tamper was not failed closed", paths, tampered_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

    return pass_result("upbit_paper_dry_run_validator", "Upbit paper dry-run is simulated, ledger-backed, namespace-separated, and live-blocked", paths)


def upbit_paper_runtime_cycle_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_runtime_cycle_report.schema.json"
    runtime_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_runtime.py"
    market_data_path = ROOT / "trader1" / "adapters" / "upbit" / "market_data.py"
    paper_ledger_path = ROOT / "trader1" / "core" / "ledger" / "paper_ledger.py"
    portfolio_path = ROOT / "trader1" / "runtime" / "portfolio" / "paper_portfolio.py"
    test_path = ROOT / "tests" / "integration" / "test_upbit_paper_runtime_cycle.py"
    paths = [schema_path, runtime_path, market_data_path, paper_ledger_path, portfolio_path, test_path]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_runtime_cycle_report.v1":
        return fail_result("upbit_paper_runtime_cycle_validator", "Upbit PAPER runtime cycle schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_runtime_cycle_validator", "Upbit PAPER runtime cycle schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    if "source_public_market_data_hash" not in required:
        return fail_result("upbit_paper_runtime_cycle_validator", "Upbit PAPER runtime cycle schema missing source market data hash", paths, "SCHEMA_IDENTITY_MISMATCH")

    entry = build_upbit_paper_runtime_cycle_report(cycle_id="validator-upbit-runtime-entry")
    entry_result = validate_upbit_paper_runtime_cycle_report(entry)
    if entry_result.status != "PASS":
        return fail_result("upbit_paper_runtime_cycle_validator", f"valid PAPER runtime cycle failed: {entry_result.message}", paths, entry_result.blocker_code or "UNKNOWN_BLOCKED")
    if entry.get("final_decision") != "ENTER_LONG" or not entry.get("paper_fill"):
        return fail_result("upbit_paper_runtime_cycle_validator", "PAPER runtime did not create a simulated fill for positive net EV", paths, "MEASUREMENT_MISSING")
    if entry.get("live_order_ready") or entry.get("live_order_allowed") or entry.get("can_live_trade") or entry.get("can_submit_order") or entry.get("scale_up_allowed"):
        return fail_result("upbit_paper_runtime_cycle_validator", "PAPER runtime created forbidden live/order permission", paths, "LIVE_FINAL_GUARD_FAILED")
    if entry["paper_portfolio_snapshot"].get("open_position_count") != 1:
        return fail_result("upbit_paper_runtime_cycle_validator", "PAPER fill did not update portfolio position count", paths, "SCHEMA_IDENTITY_MISMATCH")

    no_trade = build_upbit_paper_runtime_cycle_report(cycle_id="validator-upbit-runtime-no-trade", edge_profile="NEGATIVE")
    no_trade_result = validate_upbit_paper_runtime_cycle_report(no_trade)
    if no_trade_result.status != "PASS" or no_trade.get("final_decision") != "NO_TRADE":
        return fail_result("upbit_paper_runtime_cycle_validator", "negative net EV PAPER cycle did not remain no-trade", paths, no_trade_result.blocker_code or "MIN_EDGE_FAIL")
    if no_trade.get("paper_fill") is not None or no_trade.get("paper_ledger_events"):
        return fail_result("upbit_paper_runtime_cycle_validator", "no-trade PAPER cycle wrote fill ledger events", paths, "LIVE_FINAL_GUARD_FAILED")

    source_collection = build_upbit_public_market_data_collection_report(
        collector_id="validator-upbit-runtime-source-collection",
        session_id="mvp4_upbit_paper_runtime",
    )
    collection_bound = build_upbit_paper_runtime_cycle_report(
        cycle_id="validator-upbit-runtime-source-bound",
        source_collection_report=source_collection,
    )
    collection_bound_result = validate_upbit_paper_runtime_cycle_report(collection_bound)
    if collection_bound_result.status != "PASS":
        return fail_result(
            "upbit_paper_runtime_cycle_validator",
            f"collection-bound PAPER runtime cycle failed: {collection_bound_result.message}",
            paths,
            collection_bound_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )
    if collection_bound.get("source_public_market_data_hash") != source_collection.get("public_market_data_hash"):
        return fail_result(
            "upbit_paper_runtime_cycle_validator",
            "collection-bound PAPER runtime cycle did not preserve source market data hash",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    payload_mismatch = json.loads(json.dumps(collection_bound))
    payload_mismatch["public_market_data"]["candles"][0]["close"] = "1234567"
    payload_mismatch["cycle_hash"] = upbit_paper_runtime_cycle_hash(payload_mismatch)
    payload_mismatch_result = validate_upbit_paper_runtime_cycle_report(payload_mismatch)
    if payload_mismatch_result.status != "FAIL" or payload_mismatch_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result(
            "upbit_paper_runtime_cycle_validator",
            "collection-bound PAPER runtime allowed market data payload mutation",
            paths,
            payload_mismatch_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )

    mutated = build_upbit_paper_runtime_cycle_report(cycle_id="validator-upbit-runtime-live-mutation")
    mutated["live_order_allowed"] = True
    mutated["cycle_hash"] = upbit_paper_runtime_cycle_hash(mutated)
    mutated_result = validate_upbit_paper_runtime_cycle_report(mutated)
    if mutated_result.status != "BLOCKED" or mutated_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_paper_runtime_cycle_validator", "live permission mutation was not blocked", paths, mutated_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    tampered = build_upbit_paper_runtime_cycle_report(cycle_id="validator-upbit-runtime-tamper")
    tampered["symbol"] = "KRW-ETH"
    tampered_result = validate_upbit_paper_runtime_cycle_report(tampered)
    if tampered_result.status != "FAIL" or tampered_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("upbit_paper_runtime_cycle_validator", "PAPER runtime hash tamper was not failed closed", paths, tampered_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

    return pass_result("upbit_paper_runtime_cycle_validator", "Upbit PAPER runtime cycle connects fixture market data, candidate selection, simulated fill, ledger, portfolio, and summary while live-blocked", paths)


def upbit_public_market_data_collection_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_public_market_data_collection_report.schema.json"
    latest_pointer_schema_path = ROOT / "contracts" / "schema" / "upbit_public_market_data_latest_pointer.schema.json"
    writer_schema_path = ROOT / "contracts" / "schema" / "upbit_public_market_data_collection_writer_report.schema.json"
    collector_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_public_collector.py"
    market_data_path = ROOT / "trader1" / "adapters" / "upbit" / "market_data.py"
    test_path = ROOT / "tests" / "integration" / "test_upbit_public_collection_persistent_loop.py"
    paths = [schema_path, latest_pointer_schema_path, writer_schema_path, collector_path, market_data_path, test_path]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_public_market_data_collection_report.v1":
        return fail_result("upbit_public_market_data_collection_validator", "Upbit public collection schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_public_market_data_collection_validator", "Upbit public collection schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    latest_pointer_schema = load_json(latest_pointer_schema_path)
    if latest_pointer_schema.get("$id") != "trader1.upbit_public_market_data_latest_pointer.v1":
        return fail_result("upbit_public_market_data_collection_validator", "Upbit public latest pointer schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if latest_pointer_schema.get("additionalProperties") is not False:
        return fail_result("upbit_public_market_data_collection_validator", "Upbit public latest pointer schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    writer_schema = load_json(writer_schema_path)
    if writer_schema.get("$id") != "trader1.upbit_public_market_data_collection_writer_report.v1":
        return fail_result("upbit_public_market_data_collection_validator", "Upbit public collection writer schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if writer_schema.get("additionalProperties") is not False:
        return fail_result("upbit_public_market_data_collection_validator", "Upbit public collection writer schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "collector_mode",
        "public_market_data",
        "public_market_data_hash",
        "canonical_events",
        "canonical_event_count",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_public_market_data_collection_validator", f"collection schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    report = build_upbit_public_market_data_collection_report(
        collector_id="validator-upbit-public-collection",
        session_id="mvp1_upbit_paper_launcher",
    )
    result = validate_upbit_public_market_data_collection_report(report)
    if result.status != "PASS":
        return fail_result("upbit_public_market_data_collection_validator", f"valid public collection failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
    if report.get("canonical_event_count", 0) < 5 or report.get("raw_sample_count") != report.get("canonical_event_count"):
        return fail_result("upbit_public_market_data_collection_validator", "public collection did not preserve canonical event count", paths, "MEASUREMENT_MISSING")
    if not isinstance(report.get("public_market_data_hash"), str) or len(report["public_market_data_hash"]) != 64:
        return fail_result("upbit_public_market_data_collection_validator", "public collection did not bind market data hash", paths, "SCHEMA_IDENTITY_MISMATCH")
    if report.get("credential_load_attempted") or report.get("private_endpoint_called") or report.get("order_endpoint_called") or report.get("live_order_allowed"):
        return fail_result("upbit_public_market_data_collection_validator", "public collection attempted forbidden private/live behavior", paths, "LIVE_FINAL_GUARD_FAILED")

    schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
    with TemporaryDirectory() as tmp:
        writer = write_upbit_public_market_data_collection_artifacts(root=Path(tmp), report=report)
        latest_pointer = load_json(Path(tmp) / writer["artifact_paths"][3])
        for label, instance, expected_schema_id in (
            ("collection writer report", writer, "trader1.upbit_public_market_data_collection_writer_report.v1"),
            ("latest collection pointer", latest_pointer, "trader1.upbit_public_market_data_latest_pointer.v1"),
        ):
            instance_schema = schema_for_instance(instance, schema_bundle)
            if instance_schema is None or instance_schema.get("$id") != expected_schema_id:
                return fail_result(
                    "upbit_public_market_data_collection_validator",
                    f"{label} did not map to expected schema",
                    paths,
                    "SCHEMA_IDENTITY_MISMATCH",
                )
            instance_result = validate_instance_against_schema(instance, instance_schema, schema_bundle)
            if instance_result.status != "PASS":
                return fail_result(
                    "upbit_public_market_data_collection_validator",
                    f"{label} schema validation failed: {instance_result.errors[0]}",
                    paths,
                    "SCHEMA_IDENTITY_MISMATCH",
                )
        writer_result = validate_upbit_public_market_data_collection_writer_report(writer, source_report=report)
        if writer_result.status != "PASS":
            return fail_result("upbit_public_market_data_collection_validator", f"writer report failed validation: {writer_result.message}", paths, writer_result.blocker_code or "UNKNOWN_BLOCKED")
        pointer_result = validate_upbit_public_market_data_latest_pointer(latest_pointer, source_report=report)
        if pointer_result.status != "PASS":
            return fail_result("upbit_public_market_data_collection_validator", f"latest pointer failed validation: {pointer_result.message}", paths, pointer_result.blocker_code or "UNKNOWN_BLOCKED")
        latest_pointer["public_market_data_hash"] = "0" * 64
        pointer_mismatch_result = validate_upbit_public_market_data_latest_pointer(latest_pointer, source_report=report)
        if pointer_mismatch_result.status != "FAIL" or pointer_mismatch_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
            return fail_result(
                "upbit_public_market_data_collection_validator",
                "latest pointer hash mismatch was not failed closed",
                paths,
                pointer_mismatch_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
            )
        writer_live_mutation = dict(writer)
        writer_live_mutation["live_order_allowed"] = True
        writer_live_result = validate_upbit_public_market_data_collection_writer_report(writer_live_mutation, source_report=report)
        if writer_live_result.status != "BLOCKED" or writer_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result(
                "upbit_public_market_data_collection_validator",
                "collection writer live flag mutation was not blocked",
                paths,
                writer_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
            )

    payload_mismatch = build_upbit_public_market_data_collection_report(
        collector_id="validator-upbit-public-payload-mismatch",
        session_id="mvp1_upbit_paper_launcher",
    )
    payload_mismatch["public_market_data"]["candles"][0]["close"] = "1234567"
    payload_mismatch["collection_hash"] = upbit_public_market_data_collection_hash(payload_mismatch)
    payload_mismatch_result = validate_upbit_public_market_data_collection_report(payload_mismatch)
    if payload_mismatch_result.status != "FAIL" or payload_mismatch_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result(
            "upbit_public_market_data_collection_validator",
            "public collection allowed market data payload mutation after data hash binding",
            paths,
            payload_mismatch_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )

    rest_payload = [
        {
            "market": "KRW-BTC",
            "candle_date_time_utc": f"2026-04-30T09:{index:02d}:00",
            "opening_price": 1000000 + index * 1000,
            "high_price": 1002500 + index * 1000,
            "low_price": 998000 + index * 1000,
            "trade_price": 1000500 + index * 1000,
            "candle_acc_trade_volume": 2 + index,
        }
        for index in range(5, -1, -1)
    ]
    rest_data = build_upbit_public_candle_data_from_rest_payload(
        payload=rest_payload,
        session_id="mvp1_upbit_paper_launcher",
    )
    rest_report = build_upbit_public_market_data_collection_report(
        collector_id="validator-upbit-public-rest-read-only",
        session_id="mvp1_upbit_paper_launcher",
        market_data=rest_data,
    )
    rest_result = validate_upbit_public_market_data_collection_report(rest_report)
    if rest_result.status != "PASS" or rest_report.get("data_source") != "PUBLIC_REST_READ_ONLY":
        return fail_result("upbit_public_market_data_collection_validator", "public REST read-only payload was not accepted safely", paths, rest_result.blocker_code or "DATA_UNAVAILABLE")
    rest_data["authorization_header_present"] = True
    rest_auth_report = build_upbit_public_market_data_collection_report(
        collector_id="validator-upbit-public-rest-auth-header",
        session_id="mvp1_upbit_paper_launcher",
        market_data=rest_data,
    )
    rest_auth_result = validate_upbit_public_market_data_collection_report(rest_auth_report)
    if rest_auth_result.status != "BLOCKED" or rest_auth_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_public_market_data_collection_validator", "public REST collector allowed authorization header use", paths, rest_auth_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")
    rest_out_of_order_data = build_upbit_public_candle_data_from_rest_payload(
        payload=rest_payload,
        session_id="mvp1_upbit_paper_launcher",
    )
    rest_out_of_order_data["candles"][3]["timestamp"] = "2026-04-30T08:59:00Z"
    rest_out_of_order_report = build_upbit_public_market_data_collection_report(
        collector_id="validator-upbit-public-rest-out-of-order",
        session_id="mvp1_upbit_paper_launcher",
        market_data=rest_out_of_order_data,
    )
    rest_out_of_order_result = validate_upbit_public_market_data_collection_report(rest_out_of_order_report)
    if rest_out_of_order_result.status != "BLOCKED" or rest_out_of_order_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result("upbit_public_market_data_collection_validator", "public REST collector allowed out-of-order candles", paths, rest_out_of_order_result.blocker_code or "RECONCILIATION_REQUIRED")

    private_data = build_upbit_public_market_data_fixture(symbol="KRW-BTC", session_id="mvp1_upbit_paper_launcher")
    private_data["private_account_fields_present"] = True
    private_mix = build_upbit_public_market_data_collection_report(
        collector_id="validator-upbit-public-private-mix",
        session_id="mvp1_upbit_paper_launcher",
        market_data=private_data,
    )
    private_result = validate_upbit_public_market_data_collection_report(private_mix)
    if private_result.status != "BLOCKED" or private_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_public_market_data_collection_validator", "public collection allowed private-field mixing", paths, private_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    mutated = build_upbit_public_market_data_collection_report(
        collector_id="validator-upbit-public-live-mutation",
        session_id="mvp1_upbit_paper_launcher",
    )
    mutated["live_order_allowed"] = True
    mutated["collection_hash"] = upbit_public_market_data_collection_hash(mutated)
    mutated_result = validate_upbit_public_market_data_collection_report(mutated)
    if mutated_result.status != "BLOCKED" or mutated_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_public_market_data_collection_validator", "public collection live mutation was not blocked", paths, mutated_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    duplicate = build_upbit_public_market_data_collection_report(
        collector_id="validator-upbit-public-duplicate-event",
        session_id="mvp1_upbit_paper_launcher",
    )
    duplicate["canonical_events"][1] = dict(duplicate["canonical_events"][0])
    duplicate["collection_hash"] = upbit_public_market_data_collection_hash(duplicate)
    duplicate_result = validate_upbit_public_market_data_collection_report(duplicate)
    if duplicate_result.status != "BLOCKED" or duplicate_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result("upbit_public_market_data_collection_validator", "duplicate canonical event was not reconcile-blocked", paths, duplicate_result.blocker_code or "RECONCILIATION_REQUIRED")

    return pass_result("upbit_public_market_data_collection_validator", "Upbit public market data collection, writer report, and latest pointer are strict, scoped, hash-bound, and live-blocked", paths)


def upbit_public_rest_sample_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_public_rest_sample_report.schema.json"
    sample_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_public_rest_sample.py"
    tool_path = ROOT / "tools" / "run_upbit_public_rest_read_only_sample.py"
    test_path = ROOT / "tests" / "integration" / "test_upbit_public_rest_sample.py"
    paths = [schema_path, sample_path, tool_path, test_path]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_public_rest_sample_report.v1":
        return fail_result("upbit_public_rest_sample_validator", "Upbit public REST sample schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_public_rest_sample_validator", "Upbit public REST sample schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "network_call_attempted",
        "evidence_role",
        "credential_load_attempted",
        "authorization_header_present",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_public_rest_sample_validator", f"sample schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    rest_payload = [
        {
            "market": "KRW-BTC",
            "candle_date_time_utc": f"2026-04-30T09:{index:02d}:00",
            "opening_price": 1000000 + index * 1000,
            "high_price": 1002500 + index * 1000,
            "low_price": 998000 + index * 1000,
            "trade_price": 1000500 + index * 1000,
            "candle_acc_trade_volume": 2 + index,
        }
        for index in range(5, -1, -1)
    ]

    def fetcher(*, symbol: str, session_id: str, timeout_seconds: float) -> dict[str, Any]:
        return build_upbit_public_candle_data_from_rest_payload(
            payload=rest_payload,
            symbol=symbol,
            session_id=session_id,
        )

    pass_report = build_upbit_public_rest_sample_report(
        sample_id="validator-upbit-public-rest-sample-pass",
        session_id="mvp1_upbit_paper_launcher",
        fetcher=fetcher,
    )
    pass_result_value = validate_upbit_public_rest_sample_report(pass_report)
    if pass_result_value.status != "PASS":
        return fail_result("upbit_public_rest_sample_validator", f"valid public REST sample failed: {pass_result_value.message}", paths, pass_result_value.blocker_code or "DATA_UNAVAILABLE")
    if pass_report.get("evidence_role") != "PAPER_INPUT_QUALITY_SAMPLE_ONLY_NOT_LIVE_READY":
        return fail_result("upbit_public_rest_sample_validator", "public REST sample role could be mistaken for live readiness", paths, "LIVE_FINAL_GUARD_FAILED")

    no_network = build_upbit_public_rest_sample_report(
        sample_id="validator-upbit-public-rest-sample-no-network",
        session_id="mvp1_upbit_paper_launcher",
        attempt_network=False,
    )
    no_network_result = validate_upbit_public_rest_sample_report(no_network)
    if no_network_result.status != "BLOCKED" or no_network_result.blocker_code != "DATA_UNAVAILABLE":
        return fail_result("upbit_public_rest_sample_validator", "no-network sample did not fail closed", paths, no_network_result.blocker_code or "DATA_UNAVAILABLE")

    auth_report = build_upbit_public_rest_sample_report(
        sample_id="validator-upbit-public-rest-sample-auth-header",
        session_id="mvp1_upbit_paper_launcher",
        fetcher=fetcher,
    )
    auth_report["authorization_header_present"] = True
    auth_report["sample_hash"] = upbit_public_rest_sample_hash(auth_report)
    auth_result = validate_upbit_public_rest_sample_report(auth_report)
    if auth_result.status != "BLOCKED" or auth_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_public_rest_sample_validator", "public REST sample allowed authorization header marker", paths, auth_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    live_mutation = build_upbit_public_rest_sample_report(
        sample_id="validator-upbit-public-rest-sample-live-mutation",
        session_id="mvp1_upbit_paper_launcher",
        fetcher=fetcher,
    )
    live_mutation["live_order_allowed"] = True
    live_mutation["sample_hash"] = upbit_public_rest_sample_hash(live_mutation)
    live_result = validate_upbit_public_rest_sample_report(live_mutation)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_public_rest_sample_validator", "public REST sample live mutation was not blocked", paths, live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    return pass_result("upbit_public_rest_sample_validator", "Upbit public REST sample is PAPER-only, operator-visible, credential-free, and live-blocked", paths)


def upbit_public_rest_continuity_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_public_rest_continuity_report.schema.json"
    continuity_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_public_rest_continuity.py"
    tool_path = ROOT / "tools" / "run_upbit_public_rest_continuity_check.py"
    test_path = ROOT / "tests" / "integration" / "test_upbit_public_rest_continuity.py"
    paths = [schema_path, continuity_path, tool_path, test_path]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_public_rest_continuity_report.v1":
        return fail_result("upbit_public_rest_continuity_validator", "Upbit public REST continuity schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_public_rest_continuity_validator", "Upbit public REST continuity schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "sample_reports",
        "sample_hashes",
        "latest_event_times_utc",
        "duplicate_latest_event_time_detected",
        "non_advancing_sample_detected",
        "evidence_role",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_public_rest_continuity_validator", f"continuity schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    def payload(start_minute: int) -> list[dict[str, Any]]:
        return [
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": f"2026-04-30T09:{start_minute + index:02d}:00",
                "opening_price": 1000000 + (start_minute + index) * 1000,
                "high_price": 1002500 + (start_minute + index) * 1000,
                "low_price": 998000 + (start_minute + index) * 1000,
                "trade_price": 1000500 + (start_minute + index) * 1000,
                "candle_acc_trade_volume": 2 + index,
            }
            for index in range(5, -1, -1)
        ]

    def sequence_fetcher(starts: list[int]) -> Callable[..., dict[str, Any]]:
        calls = {"count": 0}

        def fetcher(*, symbol: str, session_id: str, timeout_seconds: float) -> dict[str, Any]:
            index = min(calls["count"], len(starts) - 1)
            calls["count"] += 1
            return build_upbit_public_candle_data_from_rest_payload(
                payload=payload(starts[index]),
                symbol=symbol,
                session_id=session_id,
            )

        return fetcher

    pass_report = build_upbit_public_rest_continuity_report(
        continuity_id="validator-upbit-public-rest-continuity-pass",
        session_id="mvp1_upbit_paper_launcher",
        fetcher=sequence_fetcher([0, 1]),
    )
    pass_result_value = validate_upbit_public_rest_continuity_report(pass_report)
    if pass_result_value.status != "PASS":
        return fail_result("upbit_public_rest_continuity_validator", f"valid public REST continuity failed: {pass_result_value.message}", paths, pass_result_value.blocker_code or "DATA_QUALITY_INSUFFICIENT")
    if pass_report.get("evidence_role") != "PAPER_DATA_CONTINUITY_ONLY_NOT_LIVE_READY":
        return fail_result("upbit_public_rest_continuity_validator", "public REST continuity role could be mistaken for live readiness", paths, "LIVE_FINAL_GUARD_FAILED")

    duplicate = build_upbit_public_rest_continuity_report(
        continuity_id="validator-upbit-public-rest-continuity-duplicate",
        session_id="mvp1_upbit_paper_launcher",
        fetcher=sequence_fetcher([0, 0]),
    )
    duplicate_result = validate_upbit_public_rest_continuity_report(duplicate)
    if duplicate_result.status != "BLOCKED" or duplicate_result.blocker_code != "DATA_QUALITY_INSUFFICIENT":
        return fail_result("upbit_public_rest_continuity_validator", "duplicate latest timestamp did not block continuity", paths, duplicate_result.blocker_code or "DATA_QUALITY_INSUFFICIENT")

    no_network = build_upbit_public_rest_continuity_report(
        continuity_id="validator-upbit-public-rest-continuity-no-network",
        session_id="mvp1_upbit_paper_launcher",
        attempt_network=False,
    )
    no_network_result = validate_upbit_public_rest_continuity_report(no_network)
    if no_network_result.status != "BLOCKED" or no_network_result.blocker_code != "DATA_UNAVAILABLE":
        return fail_result("upbit_public_rest_continuity_validator", "no-network continuity did not fail closed", paths, no_network_result.blocker_code or "DATA_UNAVAILABLE")

    live_mutation = build_upbit_public_rest_continuity_report(
        continuity_id="validator-upbit-public-rest-continuity-live-mutation",
        session_id="mvp1_upbit_paper_launcher",
        fetcher=sequence_fetcher([0, 1]),
    )
    live_mutation["live_order_allowed"] = True
    live_mutation["continuity_hash"] = upbit_public_rest_continuity_hash(live_mutation)
    live_result = validate_upbit_public_rest_continuity_report(live_mutation)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_public_rest_continuity_validator", "public REST continuity live mutation was not blocked", paths, live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    return pass_result("upbit_public_rest_continuity_validator", "Upbit public REST continuity requires advancing PAPER-only samples and remains live-blocked", paths)


def upbit_public_rest_continuity_history_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_public_rest_continuity_history.schema.json"
    history_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_public_rest_continuity_history.py"
    tool_path = ROOT / "tools" / "update_upbit_public_rest_continuity_history.py"
    test_path = ROOT / "tests" / "integration" / "test_upbit_public_rest_continuity_history.py"
    paths = [schema_path, history_path, tool_path, test_path]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_public_rest_continuity_history.v1":
        return fail_result("upbit_public_rest_continuity_history_validator", "Upbit public REST continuity history schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_public_rest_continuity_history_validator", "Upbit public REST continuity history schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "continuity_attempts",
        "attempt_hashes",
        "total_attempt_count",
        "pass_attempt_count",
        "blocked_attempt_count",
        "latest_attempt_status",
        "continuity_health_status",
        "evidence_role",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_public_rest_continuity_history_validator", f"continuity history schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    def payload(start_minute: int) -> list[dict[str, Any]]:
        return [
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": f"2026-04-30T09:{start_minute + index:02d}:00",
                "opening_price": 1000000 + (start_minute + index) * 1000,
                "high_price": 1002500 + (start_minute + index) * 1000,
                "low_price": 998000 + (start_minute + index) * 1000,
                "trade_price": 1000500 + (start_minute + index) * 1000,
                "candle_acc_trade_volume": 2 + index,
            }
            for index in range(5, -1, -1)
        ]

    def sequence_fetcher(starts: list[int]) -> Callable[..., dict[str, Any]]:
        calls = {"count": 0}

        def fetcher(*, symbol: str, session_id: str, timeout_seconds: float) -> dict[str, Any]:
            index = min(calls["count"], len(starts) - 1)
            calls["count"] += 1
            return build_upbit_public_candle_data_from_rest_payload(
                payload=payload(starts[index]),
                symbol=symbol,
                session_id=session_id,
            )

        return fetcher

    pass_history = build_upbit_public_rest_continuity_history_report(
        history_id="validator-upbit-public-rest-continuity-history-pass",
        session_id="mvp1_upbit_paper_launcher",
        continuity_attempts=[
            build_upbit_public_rest_continuity_report(
                continuity_id="validator-upbit-public-rest-continuity-history-pass-1",
                session_id="mvp1_upbit_paper_launcher",
                fetcher=sequence_fetcher([0, 1]),
            ),
            build_upbit_public_rest_continuity_report(
                continuity_id="validator-upbit-public-rest-continuity-history-pass-2",
                session_id="mvp1_upbit_paper_launcher",
                fetcher=sequence_fetcher([1, 2]),
            ),
        ],
    )
    pass_result_value = validate_upbit_public_rest_continuity_history_report(pass_history)
    if pass_result_value.status != "PASS":
        return fail_result("upbit_public_rest_continuity_history_validator", f"valid public REST continuity history failed: {pass_result_value.message}", paths, pass_result_value.blocker_code or "DATA_QUALITY_INSUFFICIENT")
    if pass_history.get("evidence_role") != "PAPER_DATA_CONTINUITY_HISTORY_ONLY_NOT_LIVE_READY":
        return fail_result("upbit_public_rest_continuity_history_validator", "continuity history role could be mistaken for live readiness", paths, "LIVE_FINAL_GUARD_FAILED")
    if pass_history.get("long_run_evidence_eligible") or pass_history.get("promotion_eligible"):
        return fail_result("upbit_public_rest_continuity_history_validator", "short continuity history became long-run or promotion evidence", paths, "LIVE_FINAL_GUARD_FAILED")

    blocked_history = build_upbit_public_rest_continuity_history_report(
        history_id="validator-upbit-public-rest-continuity-history-blocked",
        session_id="mvp1_upbit_paper_launcher",
        continuity_attempts=[
            build_upbit_public_rest_continuity_report(
                continuity_id="validator-upbit-public-rest-continuity-history-blocked-pass",
                session_id="mvp1_upbit_paper_launcher",
                fetcher=sequence_fetcher([0, 1]),
            ),
            build_upbit_public_rest_continuity_report(
                continuity_id="validator-upbit-public-rest-continuity-history-blocked-duplicate",
                session_id="mvp1_upbit_paper_launcher",
                fetcher=sequence_fetcher([1, 1]),
            ),
        ],
    )
    blocked_result = validate_upbit_public_rest_continuity_history_report(blocked_history)
    if blocked_result.status != "BLOCKED" or blocked_result.blocker_code != "DATA_QUALITY_INSUFFICIENT":
        return fail_result("upbit_public_rest_continuity_history_validator", "duplicate latest timestamp did not block continuity history", paths, blocked_result.blocker_code or "DATA_QUALITY_INSUFFICIENT")

    empty_history = build_upbit_public_rest_continuity_history_report(
        history_id="validator-upbit-public-rest-continuity-history-empty",
        session_id="mvp1_upbit_paper_launcher",
        continuity_attempts=[],
    )
    empty_result = validate_upbit_public_rest_continuity_history_report(empty_history)
    if empty_result.status != "BLOCKED" or empty_result.blocker_code != "DATA_UNAVAILABLE":
        return fail_result("upbit_public_rest_continuity_history_validator", "empty continuity history did not fail closed", paths, empty_result.blocker_code or "DATA_UNAVAILABLE")

    live_mutation = build_upbit_public_rest_continuity_history_report(
        history_id="validator-upbit-public-rest-continuity-history-live-mutation",
        session_id="mvp1_upbit_paper_launcher",
        continuity_attempts=[
            build_upbit_public_rest_continuity_report(
                continuity_id="validator-upbit-public-rest-continuity-history-live-mutation-1",
                session_id="mvp1_upbit_paper_launcher",
                fetcher=sequence_fetcher([0, 1]),
            ),
            build_upbit_public_rest_continuity_report(
                continuity_id="validator-upbit-public-rest-continuity-history-live-mutation-2",
                session_id="mvp1_upbit_paper_launcher",
                fetcher=sequence_fetcher([1, 2]),
            ),
        ],
    )
    live_mutation["live_order_allowed"] = True
    live_mutation["history_hash"] = upbit_public_rest_continuity_history_hash(live_mutation)
    live_result = validate_upbit_public_rest_continuity_history_report(live_mutation)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_public_rest_continuity_history_validator", "public REST continuity history live mutation was not blocked", paths, live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    return pass_result("upbit_public_rest_continuity_history_validator", "Upbit public REST continuity history accumulates PAPER-only attempts, blocks stale data, and remains live-blocked", paths)


def upbit_paper_persistent_loop_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_persistent_loop_report.schema.json"
    recovery_schema_path = ROOT / "contracts" / "schema" / "upbit_paper_runtime_recovery_guard_report.schema.json"
    rollup_schema_path = ROOT / "contracts" / "schema" / "paper_ledger_rollup_report.schema.json"
    loop_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_persistent_loop.py"
    collector_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_public_collector.py"
    runtime_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_runtime.py"
    test_path = ROOT / "tests" / "integration" / "test_upbit_public_collection_persistent_loop.py"
    paths = [schema_path, recovery_schema_path, rollup_schema_path, loop_path, collector_path, runtime_path, test_path]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_persistent_loop_report.v1":
        return fail_result("upbit_paper_persistent_loop_validator", "Upbit PAPER persistent loop schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    recovery_schema = load_json(recovery_schema_path)
    if recovery_schema.get("$id") != "trader1.upbit_paper_runtime_recovery_guard_report.v1":
        return fail_result("upbit_paper_persistent_loop_validator", "Upbit PAPER recovery guard schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_persistent_loop_validator", "Upbit PAPER persistent loop schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    if recovery_schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_persistent_loop_validator", "Upbit PAPER recovery guard schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "requested_cycle_count",
        "completed_cycle_count",
        "cycle_results",
        "recovery_guard_status",
        "recovery_guard_hash",
        "runtime_recovery_guard_path",
        "paper_ledger_rollup_status",
        "paper_ledger_rollup_hash",
        "paper_ledger_rollup_path",
        "paper_runtime_resume_allowed",
        "partial_write_recovery_required",
        "runtime_evidence_role",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "long_run_next_action",
        "promotion_eligible",
        "data_source_policy",
        "credential_load_attempted",
        "order_endpoint_called",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_paper_persistent_loop_validator", f"persistent loop schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")
    cycle_item_schema = schema.get("properties", {}).get("cycle_results", {}).get("items", {})
    if cycle_item_schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_persistent_loop_validator", "persistent loop cycle result schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    cycle_item_required = set(cycle_item_schema.get("required", []))
    for field in (
        "cycle_index",
        "collector_id",
        "cycle_id",
        "collection_status",
        "collection_hash",
        "collection_writer_status",
        "runtime_status",
        "runtime_cycle_hash",
        "runtime_writer_status",
        "final_decision",
        "artifact_paths",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in cycle_item_required:
            return fail_result("upbit_paper_persistent_loop_validator", f"persistent loop cycle item schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")
    recovery_required = set(recovery_schema.get("required", []))
    for field in (
        "latest_cycle_recoverable",
        "canonical_jsonl_checked_count",
        "corrupted_jsonl_quarantined_count",
        "orphan_tmp_file_count",
        "paper_runtime_resume_allowed",
        "runtime_evidence_role",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "long_run_next_action",
        "promotion_eligible",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in recovery_required:
            return fail_result("upbit_paper_persistent_loop_validator", f"recovery guard schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        loop = run_upbit_paper_persistent_loop(
            root=Path(tmp),
            loop_id="validator-upbit-paper-loop",
            session_id="mvp1_upbit_paper_launcher",
            requested_cycle_count=2,
        )
        result = validate_upbit_paper_persistent_loop_report(loop)
        if result.status != "PASS":
            return fail_result("upbit_paper_persistent_loop_validator", f"valid persistent PAPER loop failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
        if loop.get("completed_cycle_count") != 2 or not loop.get("actual_paper_runtime_executed"):
            return fail_result("upbit_paper_persistent_loop_validator", "persistent loop did not execute requested PAPER cycles", paths, "MEASUREMENT_MISSING")
        if loop.get("long_run_evidence_eligible") or loop.get("promotion_eligible") or loop.get("live_order_allowed"):
            return fail_result("upbit_paper_persistent_loop_validator", "bounded persistent loop created promotion or live permission", paths, "LIVE_FINAL_GUARD_FAILED")
        if (
            loop.get("runtime_evidence_role") != "BOUNDED_PAPER_LOOP_NOT_LONG_RUN_EVIDENCE"
            or loop.get("long_run_blocker_code") != "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT"
        ):
            return fail_result("upbit_paper_persistent_loop_validator", "bounded persistent loop did not expose long-run evidence boundary", paths, "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        if loop.get("recovery_guard_status") != "PASS" or loop.get("partial_write_recovery_required"):
            return fail_result("upbit_paper_persistent_loop_validator", "valid persistent loop did not pass recovery guard", paths, "RECONCILIATION_REQUIRED")
        if loop.get("paper_ledger_rollup_status") != "PASS" or loop.get("paper_ledger_rollup_primary_blocker_code") is not None:
            return fail_result("upbit_paper_persistent_loop_validator", "valid persistent loop did not pass ledger rollup", paths, "RECONCILIATION_REQUIRED")
        guard_path = Path(tmp) / str(loop["runtime_recovery_guard_path"])
        if not guard_path.exists():
            return fail_result("upbit_paper_persistent_loop_validator", "persistent loop did not write recovery guard artifact", paths, "MEASUREMENT_MISSING")
        rollup_path = Path(tmp) / str(loop["paper_ledger_rollup_path"])
        if not rollup_path.exists():
            return fail_result("upbit_paper_persistent_loop_validator", "persistent loop did not write paper ledger rollup artifact", paths, "MEASUREMENT_MISSING")
        guard = load_json(guard_path)
        guard_result = validate_upbit_paper_runtime_recovery_guard_report(guard)
        if guard_result.status != "PASS":
            return fail_result("upbit_paper_persistent_loop_validator", f"valid recovery guard failed: {guard_result.message}", paths, guard_result.blocker_code or "RECONCILIATION_REQUIRED")
        if (
            guard.get("runtime_evidence_role") != "PAPER_RECOVERY_GUARD_ONLY_NOT_LONG_RUN_EVIDENCE"
            or guard.get("long_run_evidence_eligible")
            or guard.get("long_run_blocker_code") != "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT"
        ):
            return fail_result("upbit_paper_persistent_loop_validator", "recovery guard did not expose resume-only long-run evidence boundary", paths, "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        rollup = load_json(rollup_path)
        rollup_result = validate_paper_ledger_rollup_report(rollup)
        if rollup_result.status != "PASS":
            return fail_result("upbit_paper_persistent_loop_validator", f"valid ledger rollup failed: {rollup_result.message}", paths, rollup_result.blocker_code or "RECONCILIATION_REQUIRED")
        latest_path = Path(tmp) / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "upbit_paper_runtime_cycle_report.json"
        if not latest_path.exists():
            return fail_result("upbit_paper_persistent_loop_validator", "persistent loop did not write latest PAPER runtime cycle", paths, "MEASUREMENT_MISSING")
        latest_cycle = load_json(latest_path)
        if latest_cycle.get("runtime_input_role") != "PUBLIC_MARKET_DATA_COLLECTION":
            return fail_result("upbit_paper_persistent_loop_validator", "latest cycle is not bound to public collection input", paths, "SCHEMA_IDENTITY_MISMATCH")
        if latest_cycle.get("live_order_allowed") or latest_cycle.get("can_live_trade") or latest_cycle.get("scale_up_allowed"):
            return fail_result("upbit_paper_persistent_loop_validator", "latest cycle drifted into live or scale-up permission", paths, "LIVE_FINAL_GUARD_FAILED")

    with TemporaryDirectory() as tmp:
        mutated = run_upbit_paper_persistent_loop(
            root=Path(tmp),
            loop_id="validator-upbit-paper-loop-live-mutation-dry",
            session_id="mvp1_upbit_paper_launcher",
            requested_cycle_count=1,
        )
    mutated["live_order_allowed"] = True
    mutated["loop_hash"] = upbit_paper_persistent_loop_hash(mutated)
    mutated_result = validate_upbit_paper_persistent_loop_report(mutated)
    if mutated_result.status != "BLOCKED" or mutated_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_paper_persistent_loop_validator", "persistent loop live mutation was not blocked", paths, mutated_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    with TemporaryDirectory() as tmp:
        false_runtime = run_upbit_paper_persistent_loop(
            root=Path(tmp),
            loop_id="validator-upbit-paper-loop-false-runtime-flag",
            session_id="mvp1_upbit_paper_launcher",
            requested_cycle_count=1,
        )
    false_runtime["actual_paper_runtime_executed"] = False
    false_runtime["loop_hash"] = upbit_paper_persistent_loop_hash(false_runtime)
    false_runtime_result = validate_upbit_paper_persistent_loop_report(false_runtime)
    if false_runtime_result.status != "BLOCKED" or false_runtime_result.blocker_code != "MEASUREMENT_MISSING":
        return fail_result("upbit_paper_persistent_loop_validator", "persistent loop false runtime execution flag was not blocked", paths, false_runtime_result.blocker_code or "MEASUREMENT_MISSING")

    with TemporaryDirectory() as tmp:
        false_boundary = run_upbit_paper_persistent_loop(
            root=Path(tmp),
            loop_id="validator-upbit-paper-loop-false-long-run-boundary",
            session_id="mvp1_upbit_paper_launcher",
            requested_cycle_count=1,
        )
    false_boundary["runtime_evidence_role"] = "PAPER_RUNTIME_EVIDENCE"
    false_boundary["loop_hash"] = upbit_paper_persistent_loop_hash(false_boundary)
    false_boundary_result = validate_upbit_paper_persistent_loop_report(false_boundary)
    if false_boundary_result.status != "BLOCKED" or false_boundary_result.blocker_code != "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT":
        return fail_result(
            "upbit_paper_persistent_loop_validator",
            "persistent loop long-run evidence boundary mutation was not blocked",
            paths,
            false_boundary_result.blocker_code or "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
        )

    with TemporaryDirectory() as tmp:
        duplicate_cycle = run_upbit_paper_persistent_loop(
            root=Path(tmp),
            loop_id="validator-upbit-paper-loop-duplicate-cycle",
            session_id="mvp1_upbit_paper_launcher",
            requested_cycle_count=2,
        )
    duplicate_cycle["cycle_results"][1] = dict(duplicate_cycle["cycle_results"][0])
    duplicate_cycle["cycle_results"][1]["cycle_index"] = 2
    duplicate_cycle["loop_hash"] = upbit_paper_persistent_loop_hash(duplicate_cycle)
    duplicate_cycle_result = validate_upbit_paper_persistent_loop_report(duplicate_cycle)
    if duplicate_cycle_result.status != "BLOCKED" or duplicate_cycle_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result("upbit_paper_persistent_loop_validator", "persistent loop duplicate cycle identity was not blocked", paths, duplicate_cycle_result.blocker_code or "RECONCILIATION_REQUIRED")

    with TemporaryDirectory() as tmp:
        path_escape = run_upbit_paper_persistent_loop(
            root=Path(tmp),
            loop_id="validator-upbit-paper-loop-path-escape",
            session_id="mvp1_upbit_paper_launcher",
            requested_cycle_count=1,
        )
    path_escape["cycle_results"][0]["artifact_paths"].append("system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/unsafe.json")
    path_escape["loop_hash"] = upbit_paper_persistent_loop_hash(path_escape)
    path_escape_result = validate_upbit_paper_persistent_loop_report(path_escape)
    if path_escape_result.status != "BLOCKED" or path_escape_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("upbit_paper_persistent_loop_validator", "persistent loop cross-namespace artifact path was not blocked", paths, path_escape_result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH")

    with TemporaryDirectory() as tmp:
        over_budget = run_upbit_paper_persistent_loop(
            root=Path(tmp),
            loop_id="validator-upbit-paper-loop-over-budget-dry",
            session_id="mvp1_upbit_paper_launcher",
            requested_cycle_count=99,
        )
    over_budget["requested_cycle_count"] = 99
    over_budget["loop_hash"] = upbit_paper_persistent_loop_hash(over_budget)
    over_budget_result = validate_upbit_paper_persistent_loop_report(over_budget)
    if over_budget_result.status != "BLOCKED" or over_budget_result.blocker_code != "RUNTIME_BUDGET_EXCEEDED":
        return fail_result("upbit_paper_persistent_loop_validator", "persistent loop budget overrun was not blocked", paths, over_budget_result.blocker_code or "RUNTIME_BUDGET_EXCEEDED")

    return pass_result("upbit_paper_persistent_loop_validator", "Upbit PAPER persistent loop runs bounded public-data-backed PAPER cycles, writes recovery guard artifacts, and remains live-blocked", paths)


def upbit_paper_runtime_sample_history_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_runtime_sample_history.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_runtime_sample_history.py"
    loop_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_persistent_loop.py"
    test_path = ROOT / "tests" / "runtime" / "test_upbit_paper_runtime_sample_history.py"
    runtime_history_paths = sorted(
        (ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper").glob("*/paper_runtime/upbit_paper_runtime_sample_history.json")
    )
    paths = [schema_path, module_path, loop_module_path, test_path, *runtime_history_paths]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_runtime_sample_history.v1":
        return fail_result("upbit_paper_runtime_sample_history_validator", "runtime sample history schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_runtime_sample_history_validator", "runtime sample history schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "truth_role",
        "runtime_analysis_only",
        "execution_truth",
        "history_evidence_role",
        "accepted_cycle_sample_count",
        "unique_runtime_cycle_hash_count",
        "duplicate_cycle_hash_count",
        "invalid_source_count",
        "observed_span_seconds",
        "min_actual_long_run_span_seconds",
        "min_actual_long_run_cycle_count",
        "span_floor_met",
        "cycle_floor_met",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "promotion_eligible",
        "credential_load_attempted",
        "order_endpoint_called",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_paper_runtime_sample_history_validator", f"runtime sample history schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")
    sample_schema = schema.get("$defs", {}).get("runtime_sample", {})
    if sample_schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_runtime_sample_history_validator", "runtime sample schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        run_upbit_paper_persistent_loop(root=root, loop_id="validator-runtime-sample-history-a", requested_cycle_count=1)
        run_upbit_paper_persistent_loop(root=root, loop_id="validator-runtime-sample-history-b", requested_cycle_count=1)
        history = build_upbit_paper_runtime_sample_history(root=root, session_id="mvp1_upbit_paper_launcher")
        result = validate_upbit_paper_runtime_sample_history(history)
        if result.status != "PASS":
            return fail_result("upbit_paper_runtime_sample_history_validator", f"valid runtime sample history failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
        if history.get("accepted_cycle_sample_count") != 2 or history.get("unique_runtime_cycle_hash_count") != 2:
            return fail_result("upbit_paper_runtime_sample_history_validator", "runtime sample history did not bind two unique PAPER runtime cycles", paths, "MEASUREMENT_MISSING")
        if history.get("actual_long_run_evidence_created") or history.get("long_run_evidence_eligible") or history.get("promotion_eligible"):
            return fail_result("upbit_paper_runtime_sample_history_validator", "runtime sample history created long-run or promotion evidence", paths, "LIVE_FINAL_GUARD_FAILED")
        if history.get("long_run_blocker_code") != "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT":
            return fail_result("upbit_paper_runtime_sample_history_validator", "runtime sample history did not expose long-run blocker", paths, "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        written_path = write_upbit_paper_runtime_sample_history(root=root, history=history)
        if not written_path.exists():
            return fail_result("upbit_paper_runtime_sample_history_validator", "runtime sample history writer did not create artifact", paths, "MEASUREMENT_MISSING")

    live_mutation = json.loads(json.dumps(history))
    live_mutation["long_run_evidence_eligible"] = True
    live_mutation["history_hash"] = upbit_paper_runtime_sample_history_hash(live_mutation)
    live_result = validate_upbit_paper_runtime_sample_history(live_mutation)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_paper_runtime_sample_history_validator", "runtime sample history false long-run claim was not blocked", paths, live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    duplicate = json.loads(json.dumps(history))
    duplicate_sample = dict(duplicate["samples"][0])
    duplicate_sample["generated_at_utc"] = duplicate["samples"][-1]["generated_at_utc"]
    duplicate_sample["previous_sample_hash"] = duplicate["samples"][-1]["sample_hash"]
    duplicate_sample["sample_hash"] = upbit_paper_runtime_sample_hash(duplicate_sample)
    duplicate["samples"].append(duplicate_sample)
    duplicate["accepted_cycle_sample_count"] = len(duplicate["samples"])
    duplicate["unique_runtime_cycle_hash_count"] = len({item["source_runtime_cycle_hash"] for item in duplicate["samples"]})
    duplicate["duplicate_cycle_hash_count"] = duplicate["accepted_cycle_sample_count"] - duplicate["unique_runtime_cycle_hash_count"]
    duplicate["source_runtime_cycle_hashes"] = [item["source_runtime_cycle_hash"] for item in duplicate["samples"]]
    duplicate["latest_sample_at_utc"] = duplicate["samples"][-1]["generated_at_utc"]
    duplicate["history_hash"] = upbit_paper_runtime_sample_history_hash(duplicate)
    duplicate_result = validate_upbit_paper_runtime_sample_history(duplicate)
    if duplicate_result.status != "BLOCKED" or duplicate_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result("upbit_paper_runtime_sample_history_validator", "duplicate runtime cycle sample was not blocked", paths, duplicate_result.blocker_code or "RECONCILIATION_REQUIRED")

    path_escape = json.loads(json.dumps(history))
    path_escape["samples"][0]["source_runtime_cycle_path"] = "system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/unsafe.runtime_cycle.json"
    path_escape["samples"][0]["sample_hash"] = upbit_paper_runtime_sample_hash(path_escape["samples"][0])
    path_escape["history_hash"] = upbit_paper_runtime_sample_history_hash(path_escape)
    path_result = validate_upbit_paper_runtime_sample_history(path_escape)
    if path_result.status != "BLOCKED" or path_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("upbit_paper_runtime_sample_history_validator", "runtime sample cross-namespace source path was not blocked", paths, path_result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH")

    floor_mismatch = json.loads(json.dumps(history))
    floor_mismatch["span_floor_met"] = True
    floor_mismatch["history_hash"] = upbit_paper_runtime_sample_history_hash(floor_mismatch)
    floor_result = validate_upbit_paper_runtime_sample_history(floor_mismatch)
    if floor_result.status != "FAIL" or floor_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("upbit_paper_runtime_sample_history_validator", "runtime sample floor flag mismatch was not detected", paths, floor_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

    for runtime_path in runtime_history_paths:
        try:
            runtime_history = load_json(runtime_path)
        except Exception as exc:
            return fail_result("upbit_paper_runtime_sample_history_validator", f"runtime sample history artifact is not valid json: {rel(runtime_path)}: {exc}", paths, "SCHEMA_IDENTITY_MISMATCH")
        runtime_result = validate_upbit_paper_runtime_sample_history(runtime_history)
        if runtime_result.status != "PASS":
            return fail_result(
                "upbit_paper_runtime_sample_history_validator",
                f"runtime sample history artifact failed validation: {rel(runtime_path)}: {runtime_result.message}",
                paths,
                runtime_result.blocker_code or "UNKNOWN_BLOCKED",
            )

    return pass_result("upbit_paper_runtime_sample_history_validator", "Upbit PAPER runtime sample history binds actual cycle files, blocks duplicate/source drift, and cannot create live or long-run evidence", paths)


def upbit_paper_stale_loop_reconciliation_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_stale_loop_reconciliation_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_reconciliation.py"
    loop_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_persistent_loop.py"
    test_path = ROOT / "tests" / "runtime" / "test_upbit_paper_stale_loop_reconciliation.py"
    runtime_report_paths = sorted(
        (ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper").glob("*/paper_runtime/upbit_paper_stale_loop_reconciliation_report.json")
    )
    paths = [schema_path, module_path, loop_module_path, test_path, *runtime_report_paths]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_stale_loop_reconciliation_report.v1":
        return fail_result("upbit_paper_stale_loop_reconciliation_validator", "stale loop reconciliation schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_stale_loop_reconciliation_validator", "stale loop reconciliation schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "evidence_use_policy",
        "current_accepted_count",
        "legacy_schema_drift_count",
        "unsafe_blocked_count",
        "invalid_json_count",
        "duplicate_runtime_cycle_hash_count",
        "current_evidence_usable_count",
        "legacy_reference_retained_count",
        "delete_performed",
        "safe_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_paper_stale_loop_reconciliation_validator", f"stale loop reconciliation schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")
    item_schema = schema.get("$defs", {}).get("reconciliation_item", {})
    if item_schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_stale_loop_reconciliation_validator", "stale loop reconciliation item schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-current-loop", requested_cycle_count=1)
        clean_report = build_upbit_paper_stale_loop_reconciliation_report(root=root, session_id="mvp1_upbit_paper_launcher")
        clean_result = validate_upbit_paper_stale_loop_reconciliation_report(clean_report)
        if clean_result.status != "PASS":
            return fail_result("upbit_paper_stale_loop_reconciliation_validator", f"clean reconciliation report failed: {clean_result.message}", paths, clean_result.blocker_code or "UNKNOWN_BLOCKED")
        if clean_report.get("reconciliation_status") != "PASS" or clean_report.get("current_evidence_usable_count") != 1:
            return fail_result("upbit_paper_stale_loop_reconciliation_validator", "clean reconciliation did not accept the current loop source", paths, "MEASUREMENT_MISSING")

        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-legacy-loop"
        legacy.pop("paper_ledger_rollup_hash", None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        legacy_path = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / "validator-legacy-loop.persistent_loop_report.json"
        legacy_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")

        unsafe = json.loads(json.dumps(current))
        unsafe["loop_id"] = "validator-unsafe-loop"
        unsafe["live_order_allowed"] = True
        unsafe["loop_hash"] = upbit_paper_persistent_loop_hash(unsafe)
        unsafe_path = legacy_path.with_name("validator-unsafe-loop.persistent_loop_report.json")
        unsafe_path.write_text(json.dumps(unsafe, indent=2), encoding="utf-8")

        invalid_path = legacy_path.with_name("validator-invalid-loop.persistent_loop_report.json")
        invalid_path.write_text("{not-json", encoding="utf-8")

        blocked_report = build_upbit_paper_stale_loop_reconciliation_report(root=root, session_id="mvp1_upbit_paper_launcher")
        blocked_result = validate_upbit_paper_stale_loop_reconciliation_report(blocked_report)
        if blocked_result.status != "PASS":
            return fail_result("upbit_paper_stale_loop_reconciliation_validator", f"blocked reconciliation structure failed: {blocked_result.message}", paths, blocked_result.blocker_code or "UNKNOWN_BLOCKED")
        if blocked_report.get("reconciliation_status") != "BLOCKED" or blocked_report.get("primary_blocker_code") != "STALE_PERSISTENT_LOOP_REPORTS_REQUIRE_RECONCILIATION":
            return fail_result("upbit_paper_stale_loop_reconciliation_validator", "stale or unsafe loop sources did not block reconciliation", paths, "STALE_PERSISTENT_LOOP_REPORTS_REQUIRE_RECONCILIATION")
        if blocked_report.get("legacy_schema_drift_count") < 1 or blocked_report.get("invalid_json_count") < 1 or blocked_report.get("unsafe_blocked_count") < 1:
            return fail_result("upbit_paper_stale_loop_reconciliation_validator", "stale loop reconciliation did not classify legacy, invalid, and unsafe sources", paths, "MEASUREMENT_MISSING")

        deletion_mutation = json.loads(json.dumps(blocked_report))
        deletion_mutation["delete_performed"] = True
        deletion_mutation["reconciliation_hash"] = stale_loop_reconciliation_hash(deletion_mutation)
        deletion_result = validate_upbit_paper_stale_loop_reconciliation_report(deletion_mutation)
        if deletion_result.status != "BLOCKED" or deletion_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("upbit_paper_stale_loop_reconciliation_validator", "stale loop reconciliation allowed deletion or live mutation", paths, deletion_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

        false_usable = json.loads(json.dumps(blocked_report))
        legacy_item = next(item for item in false_usable["items"] if item["classification"] == "LEGACY_SCHEMA_DRIFT")
        legacy_item["evidence_usable_current"] = True
        false_usable["current_evidence_usable_count"] += 1
        false_usable["excluded_from_current_evidence_count"] -= 1
        false_usable["reconciliation_hash"] = stale_loop_reconciliation_hash(false_usable)
        false_usable_result = validate_upbit_paper_stale_loop_reconciliation_report(false_usable)
        if false_usable_result.status != "BLOCKED" or false_usable_result.blocker_code != "STALE_PERSISTENT_LOOP_REPORTS_REQUIRE_RECONCILIATION":
            return fail_result("upbit_paper_stale_loop_reconciliation_validator", "legacy schema drift source was allowed as current evidence", paths, false_usable_result.blocker_code or "STALE_PERSISTENT_LOOP_REPORTS_REQUIRE_RECONCILIATION")

        written_path = write_upbit_paper_stale_loop_reconciliation_report(root=root, report=blocked_report)
        if not written_path.exists():
            return fail_result("upbit_paper_stale_loop_reconciliation_validator", "stale loop reconciliation writer did not create artifact", paths, "MEASUREMENT_MISSING")

    for runtime_path in runtime_report_paths:
        try:
            runtime_report = load_json(runtime_path)
        except Exception as exc:
            return fail_result("upbit_paper_stale_loop_reconciliation_validator", f"runtime stale loop reconciliation artifact is not valid json: {rel(runtime_path)}: {exc}", paths, "SCHEMA_IDENTITY_MISMATCH")
        runtime_result = validate_upbit_paper_stale_loop_reconciliation_report(runtime_report)
        if runtime_result.status != "PASS":
            return fail_result(
                "upbit_paper_stale_loop_reconciliation_validator",
                f"runtime stale loop reconciliation artifact failed validation: {rel(runtime_path)}: {runtime_result.message}",
                paths,
                runtime_result.blocker_code or "UNKNOWN_BLOCKED",
            )

    return pass_result(
        "upbit_paper_stale_loop_reconciliation_validator",
        "Upbit PAPER stale loop reconciliation excludes legacy/unsafe/corrupt reports, blocks deletion/live permission, and keeps only current schema PASS sources usable",
        paths,
    )


def upbit_paper_stale_loop_regeneration_plan_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_stale_loop_regeneration_plan.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_regeneration.py"
    reconciliation_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_reconciliation.py"
    test_path = ROOT / "tests" / "runtime" / "test_upbit_paper_stale_loop_regeneration.py"
    runtime_plan_paths = sorted(
        (ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper").glob("*/paper_runtime/upbit_paper_stale_loop_regeneration_plan.json")
    )
    paths = [schema_path, module_path, reconciliation_module_path, test_path, *runtime_plan_paths]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_stale_loop_regeneration_plan.v1":
        return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", "stale loop regeneration plan schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", "stale loop regeneration plan schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "plan_role",
        "source_reconciliation_hash",
        "source_excluded_count",
        "regeneration_item_count",
        "operator_review_item_count",
        "duplicate_replacement_path_count",
        "overwrite_or_delete_count",
        "automatic_regeneration_allowed",
        "actual_regeneration_performed",
        "delete_source_allowed",
        "overwrite_source_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", f"stale loop regeneration plan schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")
    item_schema = schema.get("$defs", {}).get("plan_item", {})
    if item_schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", "stale loop regeneration plan item schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-regeneration-current", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-regeneration-legacy"
        legacy.pop("paper_ledger_rollup_hash", None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        legacy_path = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / "validator-regeneration-legacy.persistent_loop_report.json"
        legacy_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root, session_id="mvp1_upbit_paper_launcher")
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        result = validate_upbit_paper_stale_loop_regeneration_plan(plan)
        if result.status != "PASS":
            return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", f"valid regeneration plan failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
        if plan.get("plan_status") != "READY_FOR_SAFE_PAPER_REGENERATION" or plan.get("regeneration_item_count") != 1:
            return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", "legacy schema drift source was not mapped to safe PAPER regeneration", paths, "STALE_LOOP_REGENERATION_REQUIRED")
        if plan.get("automatic_regeneration_allowed") or plan.get("actual_regeneration_performed") or plan.get("delete_source_allowed") or plan.get("overwrite_source_allowed"):
            return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", "regeneration plan created execution, delete, or overwrite permission", paths, "LIVE_FINAL_GUARD_FAILED")
        if plan.get("live_order_allowed") or plan.get("can_live_trade") or plan.get("scale_up_allowed"):
            return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", "regeneration plan created live/order/scale permission", paths, "LIVE_FINAL_GUARD_FAILED")

        overwrite_mutation = json.loads(json.dumps(plan))
        overwrite_mutation["items"][0]["overwrite_source_allowed"] = True
        overwrite_mutation["plan_hash"] = stale_loop_regeneration_plan_hash(overwrite_mutation)
        overwrite_result = validate_upbit_paper_stale_loop_regeneration_plan(overwrite_mutation)
        if overwrite_result.status != "BLOCKED" or overwrite_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", "overwrite mutation was not blocked", paths, overwrite_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

        false_current = json.loads(json.dumps(plan))
        false_current["items"][0]["source_evidence_usable_current"] = True
        false_current["plan_hash"] = stale_loop_regeneration_plan_hash(false_current)
        false_current_result = validate_upbit_paper_stale_loop_regeneration_plan(false_current)
        if false_current_result.status != "BLOCKED" or false_current_result.blocker_code != "STALE_LOOP_REGENERATION_REQUIRED":
            return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", "current source inclusion mutation was not blocked", paths, false_current_result.blocker_code or "STALE_LOOP_REGENERATION_REQUIRED")

        operator_review_reconciliation = json.loads(json.dumps(reconciliation))
        legacy_index = next(
            index
            for index, item in enumerate(operator_review_reconciliation["items"])
            if item["classification"] == "LEGACY_SCHEMA_DRIFT"
        )
        operator_review_reconciliation["items"][legacy_index]["classification"] = "RECONCILIATION_REQUIRED"
        operator_review_reconciliation["items"][legacy_index]["recommended_action"] = "REGENERATE_WITH_CURRENT_SCHEMA"
        operator_review_reconciliation["legacy_schema_drift_count"] = 0
        operator_review_reconciliation["legacy_reference_retained_count"] = 0
        operator_review_reconciliation["reconciliation_hash"] = stale_loop_reconciliation_hash(operator_review_reconciliation)
        operator_review_plan = build_upbit_paper_stale_loop_regeneration_plan(
            root=root,
            reconciliation_report=operator_review_reconciliation,
        )
        operator_review_result = validate_upbit_paper_stale_loop_regeneration_plan(operator_review_plan)
        if (
            operator_review_result.status != "PASS"
            or operator_review_plan.get("plan_status") != "BLOCKED"
            or operator_review_plan.get("primary_blocker_code") != "STALE_LOOP_REGENERATION_OPERATOR_REVIEW_REQUIRED"
        ):
            return fail_result(
                "upbit_paper_stale_loop_regeneration_plan_validator",
                "reconciliation-required source was not mapped to operator review",
                paths,
                operator_review_result.blocker_code or "STALE_LOOP_REGENERATION_REQUIRED",
            )

        long_run_mutation = json.loads(json.dumps(plan))
        long_run_mutation["actual_long_run_evidence_created"] = True
        long_run_mutation["plan_hash"] = stale_loop_regeneration_plan_hash(long_run_mutation)
        long_run_result = validate_upbit_paper_stale_loop_regeneration_plan(long_run_mutation)
        if long_run_result.status != "BLOCKED" or long_run_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", "long-run evidence mutation was not blocked", paths, long_run_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

        written_path = write_upbit_paper_stale_loop_regeneration_plan(root=root, plan=plan)
        if not written_path.exists():
            return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", "stale loop regeneration plan writer did not create artifact", paths, "MEASUREMENT_MISSING")

    for runtime_path in runtime_plan_paths:
        try:
            runtime_plan = load_json(runtime_path)
        except Exception as exc:
            return fail_result("upbit_paper_stale_loop_regeneration_plan_validator", f"runtime stale loop regeneration plan artifact is not valid json: {rel(runtime_path)}: {exc}", paths, "SCHEMA_IDENTITY_MISMATCH")
        runtime_result = validate_upbit_paper_stale_loop_regeneration_plan(runtime_plan)
        if runtime_result.status != "PASS":
            return fail_result(
                "upbit_paper_stale_loop_regeneration_plan_validator",
                f"runtime stale loop regeneration plan artifact failed validation: {rel(runtime_path)}: {runtime_result.message}",
                paths,
                runtime_result.blocker_code or "UNKNOWN_BLOCKED",
            )

    return pass_result(
        "upbit_paper_stale_loop_regeneration_plan_validator",
        "Upbit PAPER stale loop regeneration plan maps legacy drift sources to new PAPER-only replacements without deleting, overwriting, executing, or creating live/long-run permission",
        paths,
    )


def upbit_paper_stale_loop_execution_guard_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_stale_loop_regeneration_execution_guard.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_execution_guard.py"
    plan_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_regeneration.py"
    reconciliation_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_reconciliation.py"
    test_path = ROOT / "tests" / "runtime" / "test_upbit_paper_stale_loop_execution_guard.py"
    runtime_guard_paths = sorted(
        (ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper").glob("*/paper_runtime/upbit_paper_stale_loop_regeneration_execution_guard.json")
    )
    paths = [schema_path, module_path, plan_module_path, reconciliation_module_path, test_path, *runtime_guard_paths]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_stale_loop_regeneration_execution_guard.v1":
        return fail_result("upbit_paper_stale_loop_execution_guard_validator", "stale loop execution guard schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_stale_loop_execution_guard_validator", "stale loop execution guard schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "guard_role",
        "source_plan_hash",
        "source_plan_status",
        "planned_regeneration_item_count",
        "guard_status",
        "paper_regeneration_preconditions_passed",
        "separate_safe_executor_required",
        "replacement_write_mode",
        "source_retention_required",
        "delete_source_allowed",
        "overwrite_source_allowed",
        "execution_performed",
        "actual_regeneration_performed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", f"stale loop execution guard schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")
    item_schema = schema.get("$defs", {}).get("guard_item", {})
    if item_schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_stale_loop_execution_guard_validator", "stale loop execution guard item schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-execution-guard-current", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-execution-guard-legacy"
        legacy.pop("paper_ledger_rollup_hash", None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        legacy_path = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / "validator-execution-guard-legacy.persistent_loop_report.json"
        legacy_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root, session_id="mvp1_upbit_paper_launcher")
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        result = validate_upbit_paper_stale_loop_execution_guard(guard)
        if result.status != "PASS":
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", f"valid execution guard failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
        if guard.get("guard_status") != "PASS" or not guard.get("paper_regeneration_preconditions_passed"):
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", "clean regeneration plan did not pass execution preconditions", paths, "STALE_LOOP_REGENERATION_REQUIRED")
        if guard.get("execution_performed") or guard.get("actual_regeneration_performed") or guard.get("delete_source_allowed") or guard.get("overwrite_source_allowed"):
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", "execution guard created execution, delete, or overwrite permission", paths, "LIVE_FINAL_GUARD_FAILED")
        if guard.get("live_order_ready") or guard.get("live_order_allowed") or guard.get("can_live_trade") or guard.get("scale_up_allowed"):
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", "execution guard created live/order/scale permission", paths, "LIVE_FINAL_GUARD_FAILED")

        replacement_path = root.joinpath(*plan["items"][0]["planned_replacement_path"].split("/"))
        replacement_path.parent.mkdir(parents=True, exist_ok=True)
        replacement_path.write_text("{}", encoding="utf-8")
        replacement_guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        replacement_result = validate_upbit_paper_stale_loop_execution_guard(replacement_guard)
        if (
            replacement_result.status != "PASS"
            or replacement_guard.get("guard_status") != "BLOCKED"
            or "STALE_LOOP_REPLACEMENT_ALREADY_EXISTS" not in replacement_guard.get("blocker_codes", [])
        ):
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", "existing replacement path did not block stale loop regeneration execution preconditions", paths, "STALE_LOOP_REPLACEMENT_ALREADY_EXISTS")
        replacement_path.unlink()

        source_hash_mismatch = json.loads(json.dumps(plan))
        source_hash_mismatch["items"][0]["source_hash"] = "0" * 64
        source_hash_mismatch["plan_hash"] = stale_loop_regeneration_plan_hash(source_hash_mismatch)
        mismatch_guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=source_hash_mismatch)
        mismatch_result = validate_upbit_paper_stale_loop_execution_guard(mismatch_guard)
        if (
            mismatch_result.status != "PASS"
            or mismatch_guard.get("guard_status") != "BLOCKED"
            or "STALE_LOOP_SOURCE_HASH_MISMATCH" not in mismatch_guard.get("blocker_codes", [])
        ):
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", "source hash mismatch did not block stale loop execution preconditions", paths, "STALE_LOOP_SOURCE_HASH_MISMATCH")

        scope_escape = json.loads(json.dumps(plan))
        scope_escape["items"][0]["planned_replacement_path"] = "system/runtime/upbit/krw_spot/live/mvp1/paper_runtime/escape.json"
        scope_escape["plan_hash"] = stale_loop_regeneration_plan_hash(scope_escape)
        scope_guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=scope_escape)
        scope_result = validate_upbit_paper_stale_loop_execution_guard(scope_guard)
        if scope_result.status != "PASS" or scope_guard.get("guard_status") != "BLOCKED" or "SNAPSHOT_SCOPE_MISMATCH" not in scope_guard.get("blocker_codes", []):
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", "replacement scope escape did not block stale loop execution preconditions", paths, "SNAPSHOT_SCOPE_MISMATCH")

        live_mutation = json.loads(json.dumps(guard))
        live_mutation["execution_performed"] = True
        live_mutation["guard_hash"] = stale_loop_execution_guard_hash(live_mutation)
        live_result = validate_upbit_paper_stale_loop_execution_guard(live_mutation)
        if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", "execution mutation was not blocked", paths, live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

        operator_plan = json.loads(json.dumps(plan))
        operator_plan["plan_status"] = "BLOCKED"
        operator_plan["primary_blocker_code"] = "STALE_LOOP_REGENERATION_OPERATOR_REVIEW_REQUIRED"
        operator_plan["operator_review_item_count"] = 1
        operator_plan["regeneration_item_count"] = 0
        operator_plan["plan_hash"] = stale_loop_regeneration_plan_hash(operator_plan)
        operator_guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=operator_plan)
        operator_result = validate_upbit_paper_stale_loop_execution_guard(operator_guard)
        if (
            operator_result.status != "PASS"
            or operator_guard.get("guard_status") != "BLOCKED"
            or "STALE_LOOP_REGENERATION_OPERATOR_REVIEW_REQUIRED" not in operator_guard.get("blocker_codes", [])
        ):
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", "operator-review plan did not block execution preconditions", paths, "STALE_LOOP_REGENERATION_OPERATOR_REVIEW_REQUIRED")

        written_path = write_upbit_paper_stale_loop_execution_guard(root=root, report=guard)
        if not written_path.exists():
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", "stale loop execution guard writer did not create artifact", paths, "MEASUREMENT_MISSING")

    for runtime_path in runtime_guard_paths:
        try:
            runtime_guard = load_json(runtime_path)
        except Exception as exc:
            return fail_result("upbit_paper_stale_loop_execution_guard_validator", f"runtime stale loop execution guard artifact is not valid json: {rel(runtime_path)}: {exc}", paths, "SCHEMA_IDENTITY_MISMATCH")
        runtime_result = validate_upbit_paper_stale_loop_execution_guard(runtime_guard)
        if runtime_result.status != "PASS":
            return fail_result(
                "upbit_paper_stale_loop_execution_guard_validator",
                f"runtime stale loop execution guard artifact failed validation: {rel(runtime_path)}: {runtime_result.message}",
                paths,
                runtime_result.blocker_code or "UNKNOWN_BLOCKED",
            )

    return pass_result(
        "upbit_paper_stale_loop_execution_guard_validator",
        "Upbit PAPER stale loop execution guard verifies source hashes, scoped create-new replacement paths, and blocks execution/live/long-run/scale mutations before any regeneration executor exists",
        paths,
    )


def upbit_paper_stale_loop_safe_regeneration_executor_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_stale_loop_safe_regeneration_executor_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_safe_regeneration_executor.py"
    guard_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_execution_guard.py"
    persistent_loop_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_persistent_loop.py"
    test_path = ROOT / "tests" / "runtime" / "test_upbit_paper_stale_loop_safe_regeneration_executor.py"
    runtime_executor_paths = sorted(
        (ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper").glob("*/paper_runtime/upbit_paper_stale_loop_safe_regeneration_executor_report.json")
    )
    paths = [schema_path, module_path, guard_module_path, persistent_loop_module_path, test_path, *runtime_executor_paths]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_stale_loop_safe_regeneration_executor_report.v1":
        return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "safe regeneration executor schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "safe regeneration executor schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "executor_role",
        "source_guard_hash",
        "source_guard_status",
        "planned_regeneration_item_count",
        "regenerated_item_count",
        "skipped_item_count",
        "source_retention_required",
        "replacement_write_mode",
        "actual_regeneration_performed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", f"safe regeneration executor schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")
    item_schema = schema.get("$defs", {}).get("executor_item", {})
    if item_schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "safe regeneration executor item schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-safe-executor-current", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-safe-executor-legacy"
        legacy.pop("paper_ledger_rollup_hash", None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        legacy_path = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / "validator-safe-executor-legacy.persistent_loop_report.json"
        legacy_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root, session_id="mvp1_upbit_paper_launcher")
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        report = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        result = validate_upbit_paper_stale_loop_safe_regeneration_executor_report(report)
        if result.status != "PASS":
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", f"valid safe regeneration executor failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
        if report.get("executor_status") != "PASS" or report.get("regenerated_item_count") != 1 or report.get("actual_regeneration_performed") is not True:
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "safe executor did not create exactly one current-schema PAPER replacement in fixture", paths, "STALE_LOOP_REGENERATION_REQUIRED")
        if report.get("delete_source_allowed") or report.get("overwrite_source_allowed") or report.get("actual_long_run_evidence_created") or report.get("long_run_evidence_eligible"):
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "safe executor created delete, overwrite, or long-run permission", paths, "LIVE_FINAL_GUARD_FAILED")
        if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("scale_up_allowed"):
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "safe executor created live/order/scale permission", paths, "LIVE_FINAL_GUARD_FAILED")
        replacement_path = root.joinpath(*report["items"][0]["planned_replacement_path"].split("/"))
        if not replacement_path.exists():
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "safe executor did not create replacement artifact", paths, "MEASUREMENT_MISSING")
        replacement_report = load_json(replacement_path)
        replacement_result = validate_upbit_paper_persistent_loop_report(replacement_report)
        if replacement_result.status != "PASS":
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", f"replacement persistent loop report failed validation: {replacement_result.message}", paths, replacement_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

        second_report = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        second_result = validate_upbit_paper_stale_loop_safe_regeneration_executor_report(second_report)
        if (
            second_result.status != "PASS"
            or second_report.get("executor_status") != "BLOCKED"
            or "STALE_LOOP_REPLACEMENT_ALREADY_EXISTS" not in second_report.get("blocker_codes", [])
            or second_report.get("actual_regeneration_performed")
        ):
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "second safe executor run did not block create-new collision", paths, "STALE_LOOP_REPLACEMENT_ALREADY_EXISTS")

        live_guard = json.loads(json.dumps(guard))
        live_guard["live_order_allowed"] = True
        live_guard["guard_hash"] = stale_loop_execution_guard_hash(live_guard)
        live_report = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=live_guard)
        live_result = validate_upbit_paper_stale_loop_safe_regeneration_executor_report(live_report)
        if live_result.status != "PASS" or live_report.get("executor_status") != "BLOCKED" or "LIVE_FINAL_GUARD_FAILED" not in live_report.get("blocker_codes", []):
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "live-mutated guard did not block safe executor", paths, "LIVE_FINAL_GUARD_FAILED")

        mutation = json.loads(json.dumps(report))
        mutation["live_order_allowed"] = True
        mutation["executor_hash"] = stale_loop_safe_regeneration_executor_hash(mutation)
        mutation_result = validate_upbit_paper_stale_loop_safe_regeneration_executor_report(mutation)
        if mutation_result.status != "BLOCKED" or mutation_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "safe executor live mutation was not blocked", paths, mutation_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

        written_path = write_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, report=report)
        if not written_path.exists():
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", "safe regeneration executor writer did not create report artifact", paths, "MEASUREMENT_MISSING")

    for runtime_path in runtime_executor_paths:
        try:
            runtime_report = load_json(runtime_path)
        except Exception as exc:
            return fail_result("upbit_paper_stale_loop_safe_regeneration_executor_validator", f"runtime safe regeneration executor artifact is not valid json: {rel(runtime_path)}: {exc}", paths, "SCHEMA_IDENTITY_MISMATCH")
        runtime_result = validate_upbit_paper_stale_loop_safe_regeneration_executor_report(runtime_report)
        if runtime_result.status != "PASS":
            return fail_result(
                "upbit_paper_stale_loop_safe_regeneration_executor_validator",
                f"runtime safe regeneration executor artifact failed validation: {rel(runtime_path)}: {runtime_result.message}",
                paths,
                runtime_result.blocker_code or "UNKNOWN_BLOCKED",
            )

    return pass_result(
        "upbit_paper_stale_loop_safe_regeneration_executor_validator",
        "Upbit PAPER stale loop safe regeneration executor writes current-schema replacements create-new-only, preserves sources, blocks overwrite/live/long-run/scale mutations, and keeps MVP-5 blocked",
        paths,
    )


def upbit_paper_stale_loop_post_regeneration_reconciliation_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_stale_loop_post_regeneration_reconciliation_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_post_regeneration_reconciliation.py"
    executor_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_safe_regeneration_executor.py"
    persistent_loop_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_persistent_loop.py"
    test_path = ROOT / "tests" / "runtime" / "test_upbit_paper_stale_loop_post_regeneration_reconciliation.py"
    runtime_report_paths = sorted(
        (ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper").glob("*/paper_runtime/upbit_paper_stale_loop_post_regeneration_reconciliation_report.json")
    )
    paths = [schema_path, module_path, executor_module_path, persistent_loop_module_path, test_path, *runtime_report_paths]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_stale_loop_post_regeneration_reconciliation_report.v1":
        return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "post-regeneration reconciliation schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "post-regeneration reconciliation schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "post_reconciliation_role",
        "evidence_use_policy",
        "source_executor_hash",
        "source_executor_status",
        "planned_regeneration_item_count",
        "source_retained_count",
        "replacement_found_count",
        "regenerated_current_accepted_count",
        "regenerated_current_blocked_reconciliation_count",
        "blocked_repair_reason_counts",
        "current_evidence_usable_count",
        "excluded_from_current_evidence_count",
        "unpaired_regenerated_artifact_count",
        "delete_source_allowed",
        "overwrite_source_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", f"post-regeneration reconciliation schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")
    item_schema = schema.get("$defs", {}).get("post_reconciliation_item", {})
    if item_schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "post-regeneration reconciliation item schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-post-regeneration-current", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-post-regeneration-legacy"
        legacy.pop("paper_ledger_rollup_hash", None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        legacy_path = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / "validator-post-regeneration-legacy.persistent_loop_report.json"
        legacy_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root, session_id="mvp1_upbit_paper_launcher")
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        report = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(root=root, executor_report=executor)
        result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(report)
        if result.status != "PASS":
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", f"valid post-regeneration reconciliation failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
        if report.get("post_reconciliation_status") != "PASS" or report.get("regenerated_current_accepted_count") != 1 or report.get("current_evidence_usable_count") != 1:
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "post-regeneration reconciliation did not accept the PASS replacement", paths, "MEASUREMENT_MISSING")
        if report.get("blocked_repair_reason_counts") != [] or report.get("items", [{}])[0].get("blocked_repair_reason_codes") != []:
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "accepted replacement carried blocked repair reasons", paths, "SCHEMA_IDENTITY_MISMATCH")
        if report.get("delete_source_allowed") or report.get("overwrite_source_allowed") or report.get("actual_long_run_evidence_created") or report.get("long_run_evidence_eligible"):
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "post-regeneration reconciliation created delete, overwrite, or long-run permission", paths, "LIVE_FINAL_GUARD_FAILED")
        if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("scale_up_allowed"):
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "post-regeneration reconciliation created live/order/scale permission", paths, "LIVE_FINAL_GUARD_FAILED")

        blocked_root = root / "blocked_fixture"
        older_current = run_upbit_paper_persistent_loop(root=blocked_root, loop_id="validator-post-regeneration-older-current", requested_cycle_count=1)
        older = json.loads(json.dumps(older_current))
        older["loop_id"] = "validator-post-regeneration-older-legacy"
        for field in (
            "recovery_guard_status",
            "recovery_guard_hash",
            "recovery_guard_primary_blocker_code",
            "runtime_recovery_guard_path",
            "paper_runtime_resume_allowed",
            "partial_write_recovery_required",
            "paper_ledger_rollup_status",
            "paper_ledger_rollup_hash",
            "paper_ledger_rollup_primary_blocker_code",
            "paper_ledger_rollup_path",
        ):
            older.pop(field, None)
        older["loop_hash"] = upbit_paper_persistent_loop_hash(older)
        older_path = blocked_root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / "validator-post-regeneration-older-legacy.persistent_loop_report.json"
        older_path.write_text(json.dumps(older, indent=2), encoding="utf-8")
        older_reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=blocked_root, session_id="mvp1_upbit_paper_launcher")
        older_plan = build_upbit_paper_stale_loop_regeneration_plan(root=blocked_root, reconciliation_report=older_reconciliation)
        older_guard = build_upbit_paper_stale_loop_execution_guard(root=blocked_root, plan=older_plan)
        older_executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=blocked_root, guard=older_guard)
        blocked_report = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(root=blocked_root, executor_report=older_executor)
        blocked_result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(blocked_report)
        if (
            blocked_result.status != "PASS"
            or blocked_report.get("post_reconciliation_status") != "BLOCKED"
            or blocked_report.get("regenerated_current_blocked_reconciliation_count") != 1
            or "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED" not in blocked_report.get("blocker_codes", [])
        ):
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "post-regeneration reconciliation did not block a schema-repaired ledger/recovery gap", paths, "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED")
        blocked_item = blocked_report.get("items", [{}])[0]
        if (
            "LEDGER_ROLLUP_BLOCKED" not in blocked_item.get("blocked_repair_reason_codes", [])
            or blocked_item.get("ledger_reconciliation_status") != "BLOCKED"
            or {"reason_code": "LEDGER_ROLLUP_BLOCKED", "count": 1} not in blocked_report.get("blocked_repair_reason_counts", [])
        ):
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "blocked repair reason rollup did not expose the ledger reconciliation gap", paths, "MEASUREMENT_MISSING")

        false_usable = json.loads(json.dumps(blocked_report))
        false_usable["items"][0]["evidence_usable_current"] = True
        false_usable["current_evidence_usable_count"] = 1
        false_usable["excluded_from_current_evidence_count"] = 0
        false_usable["post_reconciliation_hash"] = stale_loop_post_regeneration_reconciliation_hash(false_usable)
        false_usable_result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(false_usable)
        if false_usable_result.status != "BLOCKED" or false_usable_result.blocker_code != "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED":
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "blocked replacement was allowed as current evidence", paths, false_usable_result.blocker_code or "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED")

        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["post_reconciliation_hash"] = stale_loop_post_regeneration_reconciliation_hash(live_mutation)
        live_result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(live_mutation)
        if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "post-regeneration reconciliation live mutation was not blocked", paths, live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

        written_path = write_upbit_paper_stale_loop_post_regeneration_reconciliation_report(root=root, report=report)
        if not written_path.exists():
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "post-regeneration reconciliation writer did not create report artifact", paths, "MEASUREMENT_MISSING")

    for runtime_path in runtime_report_paths:
        try:
            runtime_report = load_json(runtime_path)
        except Exception as exc:
            return fail_result("upbit_paper_stale_loop_post_regeneration_reconciliation_validator", f"runtime post-regeneration reconciliation artifact is not valid json: {rel(runtime_path)}: {exc}", paths, "SCHEMA_IDENTITY_MISMATCH")
        runtime_result = validate_upbit_paper_stale_loop_post_regeneration_reconciliation_report(runtime_report)
        if runtime_result.status != "PASS":
            return fail_result(
                "upbit_paper_stale_loop_post_regeneration_reconciliation_validator",
                f"runtime post-regeneration reconciliation artifact failed validation: {rel(runtime_path)}: {runtime_result.message}",
                paths,
                runtime_result.blocker_code or "UNKNOWN_BLOCKED",
            )

    return pass_result(
        "upbit_paper_stale_loop_post_regeneration_reconciliation_validator",
        "Upbit PAPER post-regeneration reconciliation accepts only PASS regenerated current-schema replacements, excludes sources and blocked repairs, and keeps live/scale permissions false",
        paths,
    )


def upbit_paper_blocked_repair_plan_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_blocked_repair_plan_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_blocked_repair_plan.py"
    post_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_post_regeneration_reconciliation.py"
    test_path = ROOT / "tests" / "runtime" / "test_upbit_paper_blocked_repair_plan.py"
    runtime_report_paths = sorted(
        (ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper").glob("*/paper_runtime/upbit_paper_blocked_repair_plan_report.json")
    )
    paths = [schema_path, module_path, post_module_path, test_path, *runtime_report_paths]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_blocked_repair_plan_report.v1":
        return fail_result("upbit_paper_blocked_repair_plan_validator", "blocked repair plan schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_blocked_repair_plan_validator", "blocked repair plan schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "repair_plan_role",
        "source_post_reconciliation_hash",
        "source_blocked_reconciliation_count",
        "repair_lane_counts",
        "ledger_rollup_rebuild_ready_count",
        "runtime_cycle_rerun_required_count",
        "recovery_guard_rerun_required_count",
        "missing_cycle_ledger_jsonl_total_count",
        "current_evidence_mutation_allowed",
        "generated_artifact_mutation_allowed",
        "source_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_paper_blocked_repair_plan_validator", f"blocked repair plan schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-blocked-repair-current", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-blocked-repair-legacy"
        for field in (
            "paper_ledger_rollup_status",
            "paper_ledger_rollup_hash",
            "paper_ledger_rollup_primary_blocker_code",
            "paper_ledger_rollup_path",
        ):
            legacy.pop(field, None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        legacy_path = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / "validator-blocked-repair-legacy.persistent_loop_report.json"
        legacy_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root, session_id="mvp1_upbit_paper_launcher")
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        post_reconciliation = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(root=root, executor_report=executor)
        report = build_upbit_paper_blocked_repair_plan_report(root=root, post_reconciliation_report=post_reconciliation)
        result = validate_upbit_paper_blocked_repair_plan_report(report)
        if result.status != "PASS":
            return fail_result("upbit_paper_blocked_repair_plan_validator", f"valid blocked repair plan failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
        if (
            report.get("repair_plan_status") != "BLOCKED"
            or report.get("repair_item_count") != 1
            or report.get("ledger_rollup_rebuild_ready_count") != 1
            or report.get("runtime_cycle_rerun_required_count") != 0
            or report.get("current_evidence_mutation_allowed")
            or report.get("live_order_allowed")
            or report.get("scale_up_allowed")
        ):
            return fail_result("upbit_paper_blocked_repair_plan_validator", "blocked repair plan did not expose a safe ledger-only repair lane while staying live-blocked", paths, "MEASUREMENT_MISSING")
        written_path = write_upbit_paper_blocked_repair_plan_report(root=root, report=report)
        if not written_path.exists():
            return fail_result("upbit_paper_blocked_repair_plan_validator", "blocked repair plan writer did not create report artifact", paths, "MEASUREMENT_MISSING")

        cycle_id = report["items"][0]["replacement_loop_id"]
        missing = json.loads(json.dumps(report))
        missing["ledger_rollup_rebuild_ready_count"] = 0
        missing["repair_plan_hash"] = upbit_paper_blocked_repair_plan_hash(missing)
        missing_result = validate_upbit_paper_blocked_repair_plan_report(missing)
        if missing_result.status != "FAIL" or missing_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
            return fail_result("upbit_paper_blocked_repair_plan_validator", f"blocked repair plan count tamper was not rejected for {cycle_id}", paths, missing_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["repair_plan_hash"] = upbit_paper_blocked_repair_plan_hash(live_mutation)
        live_result = validate_upbit_paper_blocked_repair_plan_report(live_mutation)
        if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("upbit_paper_blocked_repair_plan_validator", "blocked repair plan live mutation was not blocked", paths, live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    for runtime_path in runtime_report_paths:
        try:
            runtime_report = load_json(runtime_path)
        except Exception as exc:
            return fail_result("upbit_paper_blocked_repair_plan_validator", f"runtime blocked repair plan artifact is not valid json: {rel(runtime_path)}: {exc}", paths, "SCHEMA_IDENTITY_MISMATCH")
        runtime_result = validate_upbit_paper_blocked_repair_plan_report(runtime_report)
        if runtime_result.status != "PASS":
            return fail_result(
                "upbit_paper_blocked_repair_plan_validator",
                f"runtime blocked repair plan artifact failed validation: {rel(runtime_path)}: {runtime_result.message}",
                paths,
                runtime_result.blocker_code or "UNKNOWN_BLOCKED",
            )

    return pass_result(
        "upbit_paper_blocked_repair_plan_validator",
        "Upbit PAPER blocked repair plan separates ledger-ready repairs from rerun/recovery blockers without mutating evidence or live state",
        paths,
    )


def upbit_paper_ledger_rollup_repair_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_ledger_rollup_repair_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_ledger_rollup_repair.py"
    plan_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_blocked_repair_plan.py"
    test_path = ROOT / "tests" / "runtime" / "test_upbit_paper_ledger_rollup_repair.py"
    runtime_report_paths = sorted(
        (ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper").glob("*/paper_runtime/upbit_paper_ledger_rollup_repair_report.json")
    )
    paths = [schema_path, module_path, plan_module_path, test_path, *runtime_report_paths]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_ledger_rollup_repair_report.v1":
        return fail_result("upbit_paper_ledger_rollup_repair_validator", "ledger rollup repair schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_ledger_rollup_repair_validator", "ledger rollup repair schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "repair_artifact_role",
        "source_repair_plan_hash",
        "ledger_rollup_rebuild_ready_source_count",
        "repair_candidate_count",
        "candidate_rollup_pass_count",
        "candidate_rollup_blocked_count",
        "hash_reconciliation_status_counts",
        "hash_reconciliation_operator_action_required_count",
        "remaining_non_ready_repair_item_count",
        "current_evidence_mutation_allowed",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_paper_ledger_rollup_repair_validator", f"ledger rollup repair schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-ledger-rollup-repair-current", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-ledger-rollup-repair-legacy"
        for field in (
            "paper_ledger_rollup_status",
            "paper_ledger_rollup_hash",
            "paper_ledger_rollup_primary_blocker_code",
            "paper_ledger_rollup_path",
        ):
            legacy.pop(field, None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        legacy_path = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / "validator-ledger-rollup-repair-legacy.persistent_loop_report.json"
        legacy_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root, session_id="mvp1_upbit_paper_launcher")
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        post_reconciliation = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(root=root, executor_report=executor)
        repair_plan = build_upbit_paper_blocked_repair_plan_report(root=root, post_reconciliation_report=post_reconciliation)
        report = build_upbit_paper_ledger_rollup_repair_report(root=root, repair_plan_report=repair_plan)
        result = validate_upbit_paper_ledger_rollup_repair_report(report)
        if result.status != "PASS":
            return fail_result("upbit_paper_ledger_rollup_repair_validator", f"valid ledger rollup repair report failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
        if (
            report.get("repair_report_status") != "BLOCKED"
            or report.get("repair_candidate_count") != 1
            or report.get("candidate_rollup_pass_count") != 1
            or report.get("current_evidence_mutation_allowed")
            or report.get("live_order_allowed")
            or report.get("scale_up_allowed")
            or not report["items"][0].get("post_repair_reconciliation_required")
            or report["items"][0].get("candidate_artifact_is_current_evidence")
            or not report["items"][0].get("hash_reconciliation_requires_operator_action")
            or report["items"][0].get("hash_reconciliation_blocker_code") != "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED"
            or report["items"][0].get("candidate_rollup_hash_self_check") != "PASS"
        ):
            return fail_result("upbit_paper_ledger_rollup_repair_validator", "ledger rollup repair did not create a blocked scoped candidate", paths, "MEASUREMENT_MISSING")
        written_path = write_upbit_paper_ledger_rollup_repair_report(root=root, report=report)
        candidate_path = root / report["items"][0]["candidate_rollup_artifact_path"]
        if not written_path.exists() or not candidate_path.exists():
            return fail_result("upbit_paper_ledger_rollup_repair_validator", "ledger rollup repair writer did not create report and candidate artifacts", paths, "MEASUREMENT_MISSING")

        count_tamper = json.loads(json.dumps(report))
        count_tamper["candidate_rollup_pass_count"] = 0
        count_tamper["repair_report_hash"] = upbit_paper_ledger_rollup_repair_hash(count_tamper)
        count_result = validate_upbit_paper_ledger_rollup_repair_report(count_tamper)
        if count_result.status != "FAIL" or count_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
            return fail_result("upbit_paper_ledger_rollup_repair_validator", "ledger rollup repair count tamper was not rejected", paths, count_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

        live_mutation = json.loads(json.dumps(report))
        live_mutation["live_order_allowed"] = True
        live_mutation["repair_report_hash"] = upbit_paper_ledger_rollup_repair_hash(live_mutation)
        live_result = validate_upbit_paper_ledger_rollup_repair_report(live_mutation)
        if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("upbit_paper_ledger_rollup_repair_validator", "ledger rollup repair live mutation was not blocked", paths, live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    for runtime_path in runtime_report_paths:
        try:
            runtime_report = load_json(runtime_path)
        except Exception as exc:
            return fail_result("upbit_paper_ledger_rollup_repair_validator", f"runtime ledger rollup repair artifact is not valid json: {rel(runtime_path)}: {exc}", paths, "SCHEMA_IDENTITY_MISMATCH")
        runtime_result = validate_upbit_paper_ledger_rollup_repair_report(runtime_report)
        if runtime_result.status != "PASS":
            return fail_result(
                "upbit_paper_ledger_rollup_repair_validator",
                f"runtime ledger rollup repair artifact failed validation: {rel(runtime_path)}: {runtime_result.message}",
                paths,
                runtime_result.blocker_code or "UNKNOWN_BLOCKED",
            )

    return pass_result(
        "upbit_paper_ledger_rollup_repair_validator",
        "Upbit PAPER ledger-ready repair builds scoped rollup candidates while keeping post-repair reconciliation, live, and scale-up blocked",
        paths,
    )


def upbit_paper_post_repair_reconciliation_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_post_repair_reconciliation_report.schema.json"
    module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_post_repair_reconciliation.py"
    repair_module_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_ledger_rollup_repair.py"
    test_path = ROOT / "tests" / "runtime" / "test_upbit_paper_post_repair_reconciliation.py"
    runtime_report_paths = sorted(
        (ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper").glob("*/paper_runtime/upbit_paper_post_repair_reconciliation_report.json")
    )
    paths = [schema_path, module_path, repair_module_path, test_path, *runtime_report_paths]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_post_repair_reconciliation_report.v1":
        return fail_result("upbit_paper_post_repair_reconciliation_validator", "post-repair reconciliation schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_post_repair_reconciliation_validator", "post-repair reconciliation schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    for field in (
        "source_repair_report_hash",
        "candidate_current_evidence_usable_count",
        "candidate_current_evidence_blocked_count",
        "hash_reconciliation_status_counts",
        "hash_reconciliation_operator_action_required_count",
        "post_repair_reconciliation_status",
        "current_evidence_mutation_allowed",
        "persistent_loop_mutation_allowed",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in required:
            return fail_result("upbit_paper_post_repair_reconciliation_validator", f"post-repair reconciliation schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        current = run_upbit_paper_persistent_loop(root=root, loop_id="validator-post-repair-current", requested_cycle_count=1)
        legacy = json.loads(json.dumps(current))
        legacy["loop_id"] = "validator-post-repair-legacy"
        for field in (
            "paper_ledger_rollup_status",
            "paper_ledger_rollup_hash",
            "paper_ledger_rollup_primary_blocker_code",
            "paper_ledger_rollup_path",
        ):
            legacy.pop(field, None)
        legacy["loop_hash"] = upbit_paper_persistent_loop_hash(legacy)
        loop_path = (
            root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "validator-post-repair-legacy.persistent_loop_report.json"
        )
        loop_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")
        reconciliation = build_upbit_paper_stale_loop_reconciliation_report(root=root)
        plan = build_upbit_paper_stale_loop_regeneration_plan(root=root, reconciliation_report=reconciliation)
        guard = build_upbit_paper_stale_loop_execution_guard(root=root, plan=plan)
        executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(root=root, guard=guard)
        post_reconciliation = build_upbit_paper_stale_loop_post_regeneration_reconciliation_report(root=root, executor_report=executor)
        repair_plan = build_upbit_paper_blocked_repair_plan_report(root=root, post_reconciliation_report=post_reconciliation)
        repair_report = build_upbit_paper_ledger_rollup_repair_report(root=root, repair_plan_report=repair_plan)
        report = build_upbit_paper_post_repair_reconciliation_report(ledger_rollup_repair_report=repair_report)
        result = validate_upbit_paper_post_repair_reconciliation_report(report)
        if result.status != "PASS":
            return fail_result("upbit_paper_post_repair_reconciliation_validator", f"valid post-repair reconciliation failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
        if (
            report.get("post_repair_reconciliation_status") != "BLOCKED"
            or report.get("repair_candidate_count") != 1
            or report.get("candidate_rollup_pass_count") != 1
            or report.get("candidate_current_evidence_usable_count") != 0
            or report.get("current_evidence_mutation_allowed")
            or report.get("live_order_allowed")
            or report.get("scale_up_allowed")
            or REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE not in report.get("blocker_codes", [])
            or report.get("hash_reconciliation_operator_action_required_count") != 1
            or not report["items"][0].get("hash_reconciliation_requires_operator_action")
            or report["items"][0].get("hash_reconciliation_blocker_code") != REPAIR_CANDIDATE_HASH_MISMATCH_BLOCKER_CODE
            or report["items"][0].get("candidate_rollup_hash_self_check") != "PASS"
        ):
            return fail_result("upbit_paper_post_repair_reconciliation_validator", "post-repair reconciliation did not stay hash-aware and blocked", paths, "MEASUREMENT_MISSING")
        written_path = write_upbit_paper_post_repair_reconciliation_report(root=root, report=report)
        if not written_path.exists():
            return fail_result("upbit_paper_post_repair_reconciliation_validator", "post-repair reconciliation writer did not create report", paths, "MEASUREMENT_MISSING")

        current_evidence_mutation = json.loads(json.dumps(report))
        current_evidence_mutation["items"][0]["candidate_current_evidence_usable"] = True
        current_evidence_mutation["candidate_current_evidence_usable_count"] = 1
        current_evidence_mutation["candidate_current_evidence_blocked_count"] = 0
        current_evidence_mutation["post_repair_reconciliation_hash"] = upbit_paper_post_repair_reconciliation_hash(current_evidence_mutation)
        mutation_result = validate_upbit_paper_post_repair_reconciliation_report(current_evidence_mutation)
        if mutation_result.status != "BLOCKED" or mutation_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("upbit_paper_post_repair_reconciliation_validator", "post-repair reconciliation current-evidence mutation was not blocked", paths, mutation_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

        count_tamper = json.loads(json.dumps(report))
        count_tamper["source_loop_expected_rollup_hash_mismatch_count"] = 0
        count_tamper["post_repair_reconciliation_hash"] = upbit_paper_post_repair_reconciliation_hash(count_tamper)
        count_result = validate_upbit_paper_post_repair_reconciliation_report(count_tamper)
        if count_result.status != "FAIL" or count_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
            return fail_result("upbit_paper_post_repair_reconciliation_validator", "post-repair reconciliation count tamper was not rejected", paths, count_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

    for runtime_path in runtime_report_paths:
        try:
            runtime_report = load_json(runtime_path)
        except Exception as exc:
            return fail_result("upbit_paper_post_repair_reconciliation_validator", f"runtime post-repair reconciliation artifact is not valid json: {rel(runtime_path)}: {exc}", paths, "SCHEMA_IDENTITY_MISMATCH")
        runtime_result = validate_upbit_paper_post_repair_reconciliation_report(runtime_report)
        if runtime_result.status != "PASS":
            return fail_result(
                "upbit_paper_post_repair_reconciliation_validator",
                f"runtime post-repair reconciliation artifact failed validation: {rel(runtime_path)}: {runtime_result.message}",
                paths,
                runtime_result.blocker_code or "UNKNOWN_BLOCKED",
            )

    return pass_result(
        "upbit_paper_post_repair_reconciliation_validator",
        "Upbit PAPER post-repair reconciliation keeps repair candidates hash-aware, operator-blocked, and out of current evidence",
        paths,
    )


def upbit_paper_runtime_recovery_guard_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "upbit_paper_runtime_recovery_guard_report.schema.json"
    loop_path = ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_persistent_loop.py"
    test_path = ROOT / "tests" / "integration" / "test_upbit_public_collection_persistent_loop.py"
    paths = [schema_path, loop_path, test_path]
    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.upbit_paper_runtime_recovery_guard_report.v1":
        return fail_result("upbit_paper_runtime_recovery_guard_validator", "recovery guard schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("upbit_paper_runtime_recovery_guard_validator", "recovery guard schema must be strict", paths, "SCHEMA_IDENTITY_MISMATCH")
    recovery_required = set(schema.get("required", []))
    for field in (
        "runtime_evidence_role",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "long_run_next_action",
        "promotion_eligible",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if field not in recovery_required:
            return fail_result("upbit_paper_runtime_recovery_guard_validator", f"recovery guard schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        loop = run_upbit_paper_persistent_loop(root=root, loop_id="validator-upbit-paper-recovery-guard", requested_cycle_count=1)
        guard = load_json(root / str(loop["runtime_recovery_guard_path"]))
        result = validate_upbit_paper_runtime_recovery_guard_report(guard)
        if result.status != "PASS":
            return fail_result("upbit_paper_runtime_recovery_guard_validator", f"valid recovery guard failed: {result.message}", paths, result.blocker_code or "RECONCILIATION_REQUIRED")
        if guard.get("actual_long_run_evidence_created") or guard.get("long_run_evidence_eligible") or guard.get("promotion_eligible") or guard.get("live_order_allowed"):
            return fail_result("upbit_paper_runtime_recovery_guard_validator", "recovery guard created long-run, promotion, or live permission", paths, "LIVE_FINAL_GUARD_FAILED")
        if (
            guard.get("runtime_evidence_role") != "PAPER_RECOVERY_GUARD_ONLY_NOT_LONG_RUN_EVIDENCE"
            or guard.get("long_run_blocker_code") != "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT"
        ):
            return fail_result("upbit_paper_runtime_recovery_guard_validator", "recovery guard did not expose resume-only long-run evidence boundary", paths, "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")

        tmp_path = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / ".orphan.tmp"
        tmp_path.write_text("partial", encoding="utf-8")
        orphan = build_upbit_paper_runtime_recovery_guard_report(root=root, loop_id="validator-upbit-paper-recovery-guard")
        orphan_result = validate_upbit_paper_runtime_recovery_guard_report(orphan)
        if orphan_result.status != "BLOCKED" or orphan_result.blocker_code != "PARTIAL_WRITE_RECOVERY_REQUIRED":
            return fail_result("upbit_paper_runtime_recovery_guard_validator", "orphan temp file was not recovery-blocked", paths, orphan_result.blocker_code or "PARTIAL_WRITE_RECOVERY_REQUIRED")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        loop = run_upbit_paper_persistent_loop(root=root, loop_id="validator-upbit-paper-recovery-jsonl", requested_cycle_count=1)
        canonical_path = None
        for artifact_path in loop["cycle_results"][0]["artifact_paths"]:
            if str(artifact_path).endswith(".canonical_events.jsonl"):
                canonical_path = root / str(artifact_path)
                break
        if canonical_path is None:
            return fail_result("upbit_paper_runtime_recovery_guard_validator", "test loop did not expose canonical JSONL artifact", paths, "MEASUREMENT_MISSING")
        with canonical_path.open("a", encoding="utf-8", newline="") as handle:
            handle.write('{"partial":')
        recovered = build_upbit_paper_runtime_recovery_guard_report(root=root, loop_id="validator-upbit-paper-recovery-jsonl")
        recovered_result = validate_upbit_paper_runtime_recovery_guard_report(recovered)
        if recovered_result.status != "BLOCKED" or recovered_result.blocker_code != "PARTIAL_WRITE_RECOVERY_REQUIRED":
            return fail_result("upbit_paper_runtime_recovery_guard_validator", "partial JSONL was not quarantine-blocked", paths, recovered_result.blocker_code or "PARTIAL_WRITE_RECOVERY_REQUIRED")
        if recovered.get("corrupted_jsonl_quarantined_count") != 1 or recovered.get("paper_runtime_resume_allowed"):
            return fail_result("upbit_paper_runtime_recovery_guard_validator", "partial JSONL recovery did not block resume exactly once", paths, "RECONCILIATION_REQUIRED")

    mutated = build_upbit_paper_runtime_recovery_guard_report(root=ROOT, loop_id="validator-upbit-paper-recovery-missing")
    mutated["live_order_allowed"] = True
    mutated["guard_hash"] = upbit_paper_runtime_recovery_guard_hash(mutated)
    mutated_result = validate_upbit_paper_runtime_recovery_guard_report(mutated)
    if mutated_result.status != "BLOCKED" or mutated_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_paper_runtime_recovery_guard_validator", "recovery guard live mutation was not blocked", paths, mutated_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    false_long_run = build_upbit_paper_runtime_recovery_guard_report(root=ROOT, loop_id="validator-upbit-paper-recovery-false-long-run")
    false_long_run["long_run_evidence_eligible"] = True
    false_long_run["guard_hash"] = upbit_paper_runtime_recovery_guard_hash(false_long_run)
    false_long_run_result = validate_upbit_paper_runtime_recovery_guard_report(false_long_run)
    if false_long_run_result.status != "BLOCKED" or false_long_run_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "upbit_paper_runtime_recovery_guard_validator",
            "recovery guard false long-run eligibility mutation was not blocked",
            paths,
            false_long_run_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    return pass_result("upbit_paper_runtime_recovery_guard_validator", "Upbit PAPER recovery guard verifies latest cycle recoverability, quarantines partial JSONL, blocks orphan temp files, and stays live-blocked", paths)


def restart_recovery_validator() -> ValidatorResult:
    intent_wal_schema_path = ROOT / "contracts" / "schema" / "intent_wal_event.schema.json"
    restart_schema_path = ROOT / "contracts" / "schema" / "restart_recovery_report.schema.json"
    intent_wal_path = ROOT / "trader1" / "core" / "events" / "intent_wal.py"
    restart_path = ROOT / "trader1" / "core" / "ledger" / "restart_recovery.py"
    ledger_path = ROOT / "trader1" / "runtime" / "ledger" / "execution_ledger.py"
    paths = [intent_wal_schema_path, restart_schema_path, intent_wal_path, restart_path, ledger_path]
    intent_schema = load_json(intent_wal_schema_path)
    restart_schema = load_json(restart_schema_path)
    if intent_schema.get("$id") != "trader1.intent_wal_event.v1":
        return fail_result("restart_recovery_validator", "intent WAL schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if restart_schema.get("$id") != "trader1.restart_recovery_report.v1":
        return fail_result("restart_recovery_validator", "restart recovery schema_id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    intent_required = set(intent_schema.get("required", []))
    restart_required = set(restart_schema.get("required", []))
    for field in ("source_ledger_event_hash", "previous_wal_hash", "paper_live_namespace_separated", "live_order_allowed", "order_adapter_called"):
        if field not in intent_required:
            return fail_result("restart_recovery_validator", f"intent WAL schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")
    for field in ("ledger_events", "intent_wal_events", "single_writer_recovered", "recovery_action", "live_order_allowed", "order_adapter_called"):
        if field not in restart_required:
            return fail_result("restart_recovery_validator", f"restart recovery schema missing required field: {field}", paths, "SCHEMA_IDENTITY_MISMATCH")

    registry = load_json(ROOT / "contracts" / "registry.yaml")
    allowed_blockers = set(registry["enums"]["live_blocker_code"]["values"])

    report = build_restart_recovery_report(restart_id="validator-restart-pass")
    result = validate_restart_recovery_report(report, allowed_blockers)
    if result.status != "PASS":
        return fail_result("restart_recovery_validator", f"valid paper restart recovery failed: {result.message}", paths, result.blocker_code or "UNKNOWN_BLOCKED")
    if report.get("recovery_action") != "RESUME_PAPER_ONLY":
        return fail_result("restart_recovery_validator", "paper restart recovery did not stay paper-only", paths, "LIVE_FINAL_GUARD_FAILED")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("can_submit_order") or report.get("order_adapter_called"):
        return fail_result("restart_recovery_validator", "restart recovery created forbidden live/order permission", paths, "LIVE_FINAL_GUARD_FAILED")
    if not report.get("ledger_recovered") or not report.get("intent_wal_recovered"):
        return fail_result("restart_recovery_validator", "restart recovery did not recover ledger and intent WAL", paths, "LEDGER_UNAVAILABLE")

    missing_wal = build_restart_recovery_report(restart_id="validator-restart-missing-wal", intent_wal_events=[])
    missing_wal_result = validate_restart_recovery_report(missing_wal, allowed_blockers)
    if missing_wal_result.status != "BLOCKED" or missing_wal_result.blocker_code != "LEDGER_UNAVAILABLE":
        return fail_result("restart_recovery_validator", "missing intent WAL was not blocked", paths, missing_wal_result.blocker_code or "LEDGER_UNAVAILABLE")

    missing_ledger = build_restart_recovery_report(restart_id="validator-restart-missing-ledger", ledger_events=[], intent_wal_events=[])
    missing_ledger_result = validate_restart_recovery_report(missing_ledger, allowed_blockers)
    if missing_ledger_result.status != "BLOCKED" or missing_ledger_result.blocker_code != "LEDGER_UNAVAILABLE":
        return fail_result("restart_recovery_validator", "missing ledger was not blocked", paths, missing_ledger_result.blocker_code or "LEDGER_UNAVAILABLE")
    missing_single_writer = build_restart_recovery_report(restart_id="validator-restart-no-single-writer")
    missing_single_writer["single_writer_recovered"] = False
    missing_single_writer["restart_recovery_status"] = "PASS"
    missing_single_writer["recovery_action"] = "RESUME_PAPER_ONLY"
    missing_single_writer["primary_blocker_code"] = None
    missing_single_writer["blockers"] = []
    missing_single_writer["restart_recovery_hash"] = restart_recovery_hash(missing_single_writer)
    missing_single_writer_result = validate_restart_recovery_report(missing_single_writer, allowed_blockers)
    if missing_single_writer_result.status != "BLOCKED" or missing_single_writer_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result(
            "restart_recovery_validator",
            "single-writer recovery false-safe report was not blocked",
            paths,
            "RECONCILIATION_REQUIRED",
        )
    recovered_flag_mismatch = build_restart_recovery_report(restart_id="validator-restart-flag-mismatch")
    recovered_flag_mismatch["ledger_recovered"] = False
    recovered_flag_mismatch["restart_recovery_hash"] = restart_recovery_hash(recovered_flag_mismatch)
    recovered_flag_mismatch_result = validate_restart_recovery_report(recovered_flag_mismatch, allowed_blockers)
    if recovered_flag_mismatch_result.status != "FAIL" or recovered_flag_mismatch_result.blocker_code != "LEDGER_INTEGRITY_FAIL":
        return fail_result(
            "restart_recovery_validator",
            "recovered flag mismatch was not failed closed",
            paths,
            "LEDGER_INTEGRITY_FAIL",
        )

    wrong_scope = build_restart_recovery_report(restart_id="validator-restart-wrong-scope", exchange="BINANCE", market_type="SPOT")
    wrong_scope_result = validate_restart_recovery_report(wrong_scope, allowed_blockers)
    if wrong_scope_result.status != "BLOCKED" or wrong_scope_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("restart_recovery_validator", "wrong recovery scope was not blocked", paths, wrong_scope_result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH")

    cross_scope = build_restart_recovery_report(restart_id="validator-restart-cross-scope")
    cross_scope["intent_wal_events"][1]["exchange"] = "BINANCE"
    cross_scope["intent_wal_events"][1]["wal_event_hash"] = intent_wal_event_hash(cross_scope["intent_wal_events"][1])
    cross_scope["restart_recovery_hash"] = restart_recovery_hash(cross_scope)
    cross_scope_result = validate_restart_recovery_report(cross_scope, allowed_blockers)
    if cross_scope_result.status != "BLOCKED" or cross_scope_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("restart_recovery_validator", "cross-scope intent WAL was not blocked", paths, cross_scope_result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH")

    for field in ("live_order_allowed", "can_live_trade", "can_submit_order", "order_adapter_called"):
        mutated = build_restart_recovery_report(restart_id=f"validator-restart-mutated-{field}")
        mutated[field] = True
        mutated["restart_recovery_hash"] = restart_recovery_hash(mutated)
        mutated_result = validate_restart_recovery_report(mutated, allowed_blockers)
        if mutated_result.status != "BLOCKED" or mutated_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result("restart_recovery_validator", f"forbidden restart mutation was not blocked: {field}", paths, mutated_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    tampered = build_restart_recovery_report(restart_id="validator-restart-tampered")
    tampered["session_id"] = "tampered-session"
    tampered_result = validate_restart_recovery_report(tampered, allowed_blockers)
    if tampered_result.status != "FAIL" or tampered_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result("restart_recovery_validator", "restart recovery hash tamper was not failed closed", paths, tampered_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

    return pass_result("restart_recovery_validator", "paper restart recovery is WAL-backed, ledger-checked, and live-blocked", paths)


def upbit_operational_paper_gate_validator() -> ValidatorResult:
    paths = [
        ROOT / "contracts" / "schema" / "strategy_unit.schema.json",
        ROOT / "contracts" / "schema" / "position_sizing_decision.schema.json",
        ROOT / "contracts" / "schema" / "replay_consistency_report.schema.json",
        ROOT / "contracts" / "schema" / "paper_shadow_separation_report.schema.json",
        ROOT / "contracts" / "schema" / "paper_shadow_evidence_accumulation_report.schema.json",
        ROOT / "contracts" / "schema" / "paper_operation_gate_report.schema.json",
        ROOT / "trader1" / "core" / "strategy" / "strategy_unit.py",
        ROOT / "trader1" / "core" / "sizing" / "position_sizing.py",
        ROOT / "trader1" / "research" / "replay" / "replay_runner.py",
        ROOT / "trader1" / "research" / "shadow" / "shadow_runner.py",
        ROOT / "trader1" / "runtime" / "paper" / "operational_cycle.py",
    ]
    expected_schema_ids = {
        "strategy_unit.schema.json": "trader1.strategy_unit.v1",
        "position_sizing_decision.schema.json": "trader1.position_sizing_decision.v1",
        "replay_consistency_report.schema.json": "trader1.replay_consistency_report.v1",
        "paper_shadow_separation_report.schema.json": "trader1.paper_shadow_separation_report.v1",
        "paper_shadow_evidence_accumulation_report.schema.json": "trader1.paper_shadow_evidence_accumulation_report.v1",
        "paper_operation_gate_report.schema.json": "trader1.paper_operation_gate_report.v1",
    }
    for schema_file, schema_id in expected_schema_ids.items():
        schema = load_json(ROOT / "contracts" / "schema" / schema_file)
        if schema.get("$id") != schema_id:
            return fail_result("upbit_operational_paper_gate_validator", f"schema id mismatch: {schema_file}", paths, "SCHEMA_IDENTITY_MISMATCH")
        if schema.get("additionalProperties") is not False:
            return fail_result("upbit_operational_paper_gate_validator", f"schema is not closed: {schema_file}", paths, "SCHEMA_IDENTITY_MISMATCH")

    strategy = build_basic_strategy_unit(strategy_unit_id="validator-operational-strategy")
    strategy_result = validate_strategy_unit(strategy)
    if strategy_result.status != "PASS":
        return fail_result("upbit_operational_paper_gate_validator", f"strategy unit failed: {strategy_result.message}", paths, strategy_result.blocker_code or "UNKNOWN_BLOCKED")

    strategy_scope = build_basic_strategy_unit(strategy_unit_id="validator-operational-strategy-scope", exchange="BINANCE", market_type="SPOT")
    strategy_scope_result = validate_strategy_unit(strategy_scope)
    if strategy_scope_result.status != "BLOCKED" or strategy_scope_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("upbit_operational_paper_gate_validator", "wrong strategy scope was not blocked", paths, strategy_scope_result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH")

    strategy_direct_order = build_basic_strategy_unit(strategy_unit_id="validator-operational-strategy-adapter")
    strategy_direct_order["strategy_order_adapter_called"] = True
    strategy_direct_order["strategy_unit_hash"] = strategy_unit_hash(strategy_direct_order)
    direct_order_result = validate_strategy_unit(strategy_direct_order)
    if direct_order_result.status != "BLOCKED" or direct_order_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_operational_paper_gate_validator", "strategy direct adapter call was not blocked", paths, direct_order_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    sizing = build_position_sizing_decision(sizing_decision_id="validator-operational-sizing", strategy_unit_id=strategy["strategy_unit_id"])
    sizing_result = validate_position_sizing_decision(sizing)
    if sizing_result.status != "PASS":
        return fail_result("upbit_operational_paper_gate_validator", f"sizing failed: {sizing_result.message}", paths, sizing_result.blocker_code or "UNKNOWN_BLOCKED")
    selected = float(sizing["selected_notional"])
    for cap_name in ("equity_cap", "cash_cap", "risk_cap", "liquidity_cap"):
        if selected > float(sizing["caps"][cap_name]):
            return fail_result("upbit_operational_paper_gate_validator", f"sizing exceeded {cap_name}", paths, "RISK_VETO")

    sizing_live = build_position_sizing_decision(sizing_decision_id="validator-operational-sizing-live", strategy_unit_id=strategy["strategy_unit_id"])
    sizing_live["can_submit_order"] = True
    sizing_live["sizing_decision_hash"] = sizing_decision_hash(sizing_live)
    sizing_live_result = validate_position_sizing_decision(sizing_live)
    if sizing_live_result.status != "BLOCKED" or sizing_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_operational_paper_gate_validator", "sizing live mutation was not blocked", paths, sizing_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    replay = build_replay_consistency_report(
        replay_id="validator-operational-replay",
        strategy_unit_id=strategy["strategy_unit_id"],
        parameter_hash=strategy["parameter_hash"],
        input_events=[{"event_id": "event-1", "price": "100"}],
    )
    replay_result = validate_replay_consistency_report(replay)
    if replay_result.status != "PASS":
        return fail_result("upbit_operational_paper_gate_validator", f"replay failed: {replay_result.message}", paths, replay_result.blocker_code or "UNKNOWN_BLOCKED")
    replay_bad = build_replay_consistency_report(
        replay_id="validator-operational-replay-bad",
        strategy_unit_id=strategy["strategy_unit_id"],
        parameter_hash=strategy["parameter_hash"],
        input_events=[{"event_id": "event-1", "price": "100"}],
    )
    replay_bad["result_hashes"][1] = "B" * 64
    replay_bad["deterministic_pass"] = False
    replay_bad["replay_consistency_hash"] = replay_consistency_hash(replay_bad)
    replay_bad_result = validate_replay_consistency_report(replay_bad)
    if replay_bad_result.status != "FAIL" or replay_bad_result.blocker_code != "MEASUREMENT_MISSING":
        return fail_result("upbit_operational_paper_gate_validator", "nondeterministic replay was not failed closed", paths, replay_bad_result.blocker_code or "MEASUREMENT_MISSING")

    separation = build_paper_shadow_separation_report(separation_report_id="validator-operational-separation")
    separation_result = validate_paper_shadow_separation_report(separation)
    if separation_result.status != "PASS":
        return fail_result("upbit_operational_paper_gate_validator", f"paper/shadow separation failed: {separation_result.message}", paths, separation_result.blocker_code or "UNKNOWN_BLOCKED")
    raw_join = build_paper_shadow_separation_report(separation_report_id="validator-operational-raw-join", raw_join_attempted=True)
    raw_join_result = validate_paper_shadow_separation_report(raw_join)
    if raw_join_result.status != "BLOCKED" or raw_join_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result("upbit_operational_paper_gate_validator", "paper/shadow raw join was not blocked", paths, raw_join_result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH")
    separation_live = build_paper_shadow_separation_report(separation_report_id="validator-operational-separation-live")
    separation_live["live_order_allowed"] = True
    separation_live["separation_hash"] = paper_shadow_separation_hash(separation_live)
    separation_live_result = validate_paper_shadow_separation_report(separation_live)
    if separation_live_result.status != "BLOCKED" or separation_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_operational_paper_gate_validator", "paper/shadow live mutation was not blocked", paths, separation_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    paper_shadow_evidence = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id="validator-operational-paper-shadow-evidence",
        candidate_id=strategy["strategy_unit_id"],
        strategy_id=strategy["strategy_id"],
        strategy_build_id=strategy["strategy_build_id"],
        parameter_hash=strategy["parameter_hash"],
    )
    paper_shadow_evidence_result = validate_paper_shadow_evidence_accumulation_report(paper_shadow_evidence)
    if paper_shadow_evidence_result.status != "PASS":
        return fail_result(
            "upbit_operational_paper_gate_validator",
            f"paper/shadow evidence accumulation failed: {paper_shadow_evidence_result.message}",
            paths,
            paper_shadow_evidence_result.blocker_code or "UNKNOWN_BLOCKED",
        )
    insufficient_evidence = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id="validator-operational-paper-shadow-evidence-insufficient",
        paper_sample_count=3,
        shadow_sample_count=3,
    )
    insufficient_evidence_result = validate_paper_shadow_evidence_accumulation_report(insufficient_evidence)
    if insufficient_evidence_result.status != "BLOCKED" or insufficient_evidence_result.blocker_code != "SAMPLE_INSUFFICIENT":
        return fail_result(
            "upbit_operational_paper_gate_validator",
            "insufficient paper/shadow samples were not blocked",
            paths,
            insufficient_evidence_result.blocker_code or "SAMPLE_INSUFFICIENT",
        )

    gate = build_upbit_operational_paper_cycle(operation_gate_id="validator-operational-gate")
    gate_result = validate_paper_operation_gate_report(gate)
    if gate_result.status != "PASS":
        return fail_result("upbit_operational_paper_gate_validator", f"paper operation gate failed: {gate_result.message}", paths, gate_result.blocker_code or "UNKNOWN_BLOCKED")
    if gate.get("live_order_ready") or gate.get("live_order_allowed") or gate.get("can_live_trade") or gate.get("can_submit_order") or gate.get("order_adapter_called"):
        return fail_result("upbit_operational_paper_gate_validator", "paper operation gate created live/order permission", paths, "LIVE_FINAL_GUARD_FAILED")
    if gate["dashboard_panels"]["status"].get("order_controls_present"):
        return fail_result("upbit_operational_paper_gate_validator", "paper dashboard exposed order controls", paths, "LIVE_FINAL_GUARD_FAILED")
    gate_evidence = gate["paper_shadow_evidence_accumulation_report"]
    if gate_evidence.get("scorecard_input_eligible") or gate_evidence.get("optimizer_ranking_action") != "BLOCK_RANKING":
        return fail_result(
            "upbit_operational_paper_gate_validator",
            "single operational paper cycle overstated paper/shadow scorecard evidence maturity",
            paths,
            "HARD_TRUTH_MISSING",
        )
    if gate_evidence.get("paper_artifact_hash") != gate["paper_dry_run_report"].get("dry_run_hash"):
        return fail_result(
            "upbit_operational_paper_gate_validator",
            "paper operation gate evidence does not bind to the dry-run artifact hash",
            paths,
            "SNAPSHOT_SCOPE_MISMATCH",
        )

    gate_risk = build_upbit_operational_paper_cycle(operation_gate_id="validator-operational-gate-risk", risk_block=True)
    if gate_risk.get("operation_gate_status") != "BLOCKED" or gate_risk.get("primary_blocker_code") != "RISK_VETO":
        return fail_result("upbit_operational_paper_gate_validator", "risk veto did not block paper operation gate", paths, "RISK_VETO")

    gate_live = build_upbit_operational_paper_cycle(operation_gate_id="validator-operational-gate-live")
    gate_live["live_order_ready"] = True
    gate_live["live_order_allowed"] = True
    gate_live["can_live_trade"] = True
    gate_live["operation_gate_hash"] = operation_gate_hash(gate_live)
    gate_live_result = validate_paper_operation_gate_report(gate_live)
    if gate_live_result.status != "BLOCKED" or gate_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_operational_paper_gate_validator", "paper operation gate live mutation was not blocked", paths, gate_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    return pass_result("upbit_operational_paper_gate_validator", "operational Upbit paper foundation is paper/shadow scoped, deterministic, and live-blocked", paths)


def upbit_live_review_preflight_validator() -> ValidatorResult:
    paths = [
        ROOT / "contracts" / "schema" / "official_api_verification_report.schema.json",
        ROOT / "contracts" / "schema" / "manual_order_test_evidence.schema.json",
        ROOT / "contracts" / "schema" / "read_only_account_snapshot.schema.json",
        ROOT / "contracts" / "schema" / "private_stream_health.schema.json",
        ROOT / "contracts" / "schema" / "upbit_read_only_reconciliation_path.schema.json",
        ROOT / "contracts" / "schema" / "api_key_permission_check_report.schema.json",
        ROOT / "contracts" / "schema" / "live_preflight_report.schema.json",
        ROOT / "contracts" / "schema" / "live_review_dashboard.schema.json",
        ROOT / "trader1" / "runtime" / "readiness" / "official_api_verification.py",
        ROOT / "trader1" / "runtime" / "readiness" / "manual_order_test_evidence.py",
        ROOT / "trader1" / "runtime" / "readiness" / "live_preflight.py",
        ROOT / "trader1" / "adapters" / "upbit" / "account_readonly.py",
        ROOT / "trader1" / "adapters" / "upbit" / "private_stream.py",
        ROOT / "trader1" / "adapters" / "upbit" / "reconciliation.py",
        ROOT / "trader1" / "security" / "api_key_permission_check.py",
        ROOT / "trader1" / "dashboard" / "live_review_dashboard.py",
    ]
    expected_schema_ids = {
        "official_api_verification_report.schema.json": "trader1.official_api_verification_report.v1",
        "manual_order_test_evidence.schema.json": "trader1.manual_order_test_evidence.v1",
        "read_only_account_snapshot.schema.json": "trader1.read_only_account_snapshot.v1",
        "private_stream_health.schema.json": "trader1.private_stream_health.v1",
        "upbit_read_only_reconciliation_path.schema.json": "trader1.upbit_read_only_reconciliation_path.v1",
        "api_key_permission_check_report.schema.json": "trader1.api_key_permission_check_report.v1",
        "live_preflight_report.schema.json": "trader1.live_preflight_report.v1",
        "live_review_dashboard.schema.json": "trader1.live_review_dashboard.v1",
    }
    for schema_file, schema_id in expected_schema_ids.items():
        schema = load_json(ROOT / "contracts" / "schema" / schema_file)
        if schema.get("$id") != schema_id:
            return fail_result("upbit_live_review_preflight_validator", f"schema id mismatch: {schema_file}", paths, "SCHEMA_IDENTITY_MISMATCH")
        if schema.get("additionalProperties") is not False:
            return fail_result("upbit_live_review_preflight_validator", f"schema is not closed: {schema_file}", paths, "SCHEMA_IDENTITY_MISMATCH")

    authority = current_authority_hashes()
    official = build_official_api_verification_report(authority=authority)
    official_result = validate_official_api_verification_report(official)
    if official_result.status != "BLOCKED" or official_result.blocker_code != "API_UNVERIFIED":
        return fail_result("upbit_live_review_preflight_validator", "unverified official API report was not blocked", paths, official_result.blocker_code or "API_UNVERIFIED")

    official_live = build_official_api_verification_report(authority=authority, verification_id="validator-official-live-mutation")
    official_live["live_order_ready"] = True
    official_live["report_hash"] = official_api_report_hash(official_live)
    official_live_result = validate_official_api_verification_report(official_live)
    if official_live_result.status != "BLOCKED" or official_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_live_review_preflight_validator", "official API live mutation was not blocked", paths, official_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    account = build_read_only_account_snapshot(authority=authority)
    account_result = validate_read_only_account_snapshot(account)
    if account_result.status != "BLOCKED" or account_result.blocker_code != "API_UNVERIFIED":
        return fail_result("upbit_live_review_preflight_validator", "unverified read-only account snapshot was not blocked", paths, account_result.blocker_code or "API_UNVERIFIED")
    account_live = build_read_only_account_snapshot(authority=authority, snapshot_id="validator-account-live")
    account_live["can_submit_order"] = True
    account_live["snapshot_hash"] = read_only_account_snapshot_hash(account_live)
    account_live_result = validate_read_only_account_snapshot(account_live)
    if account_live_result.status != "BLOCKED" or account_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_live_review_preflight_validator", "read-only account live mutation was not blocked", paths, account_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    stream = build_private_stream_health(authority=authority)
    stream_result = validate_private_stream_health(stream)
    if stream_result.status != "BLOCKED" or stream_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result("upbit_live_review_preflight_validator", "private stream fallback did not require reconciliation", paths, stream_result.blocker_code or "RECONCILIATION_REQUIRED")
    stream_live = build_private_stream_health(authority=authority, stream_health_id="validator-stream-live")
    stream_live["order_adapter_called"] = True
    stream_live["stream_health_hash"] = private_stream_health_hash(stream_live)
    stream_live_result = validate_private_stream_health(stream_live)
    if stream_live_result.status != "BLOCKED" or stream_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_live_review_preflight_validator", "private stream live mutation was not blocked", paths, stream_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    reconciliation = build_upbit_read_only_reconciliation_path(authority=authority)
    reconciliation_result = validate_upbit_read_only_reconciliation_path(reconciliation)
    if reconciliation_result.status != "BLOCKED" or reconciliation_result.blocker_code != "RECONCILIATION_REQUIRED":
        return fail_result("upbit_live_review_preflight_validator", "read-only reconciliation path was not blocked when incomplete", paths, reconciliation_result.blocker_code or "RECONCILIATION_REQUIRED")
    reconciliation_live = build_upbit_read_only_reconciliation_path(authority=authority, reconciliation_path_id="validator-reconciliation-live")
    reconciliation_live["live_order_allowed"] = True
    reconciliation_live["reconciliation_path_hash"] = upbit_read_only_reconciliation_path_hash(reconciliation_live)
    reconciliation_live_result = validate_upbit_read_only_reconciliation_path(reconciliation_live)
    if reconciliation_live_result.status != "BLOCKED" or reconciliation_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_live_review_preflight_validator", "reconciliation path live mutation was not blocked", paths, reconciliation_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    permission = build_api_key_permission_check_report(authority=authority)
    permission_result = validate_api_key_permission_check_report(permission)
    if permission_result.status != "BLOCKED" or permission_result.blocker_code != "API_UNVERIFIED":
        return fail_result("upbit_live_review_preflight_validator", "unverified API key permission check was not blocked", paths, permission_result.blocker_code or "API_UNVERIFIED")
    permission_withdrawal = build_api_key_permission_check_report(
        authority=authority,
        permission_check_id="validator-permission-withdrawal",
        api_key_present=True,
        read_permission_verified=True,
        withdrawal_permission_detected=True,
    )
    permission_withdrawal_result = validate_api_key_permission_check_report(permission_withdrawal)
    if permission_withdrawal_result.status != "BLOCKED" or permission_withdrawal_result.blocker_code != "API_UNVERIFIED":
        return fail_result("upbit_live_review_preflight_validator", "withdrawal permission was not blocked", paths, permission_withdrawal_result.blocker_code or "API_UNVERIFIED")

    manual = build_missing_manual_order_test_evidence(authority=authority)
    manual_result = validate_manual_order_test_evidence(manual)
    if manual_result.status != "BLOCKED" or manual_result.blocker_code != "MANUAL_ORDER_TEST_MISSING":
        return fail_result("upbit_live_review_preflight_validator", "missing manual order test evidence was not blocked", paths, manual_result.blocker_code or "MANUAL_ORDER_TEST_MISSING")
    manual_live = build_missing_manual_order_test_evidence(authority=authority, test_id="validator-manual-live")
    manual_live["order_adapter_called"] = True
    manual_live["evidence_hash"] = manual_order_test_hash(manual_live)
    manual_live_result = validate_manual_order_test_evidence(manual_live)
    if manual_live_result.status != "BLOCKED" or manual_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_live_review_preflight_validator", "manual order test live mutation was not blocked", paths, manual_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    preflight = build_upbit_live_review_preflight(authority=authority)
    preflight_result = validate_live_preflight_report(preflight)
    if preflight_result.status != "PASS":
        return fail_result("upbit_live_review_preflight_validator", f"review-only live preflight failed: {preflight_result.message}", paths, preflight_result.blocker_code or "UNKNOWN_BLOCKED")
    if not preflight.get("can_live_review"):
        return fail_result("upbit_live_review_preflight_validator", "MVP-4 preflight did not expose can_live_review", paths, "PREFLIGHT_FAILED")
    if preflight.get("live_order_ready") or preflight.get("live_order_allowed") or preflight.get("can_live_trade") or preflight.get("can_submit_order") or preflight.get("order_adapter_called"):
        return fail_result("upbit_live_review_preflight_validator", "MVP-4 preflight created forbidden live/order permission", paths, "LIVE_FINAL_GUARD_FAILED")
    codes = {blocker.get("code") for blocker in preflight["blockers"]}
    for required_code in ("LIVE_READY_MISSING", "API_UNVERIFIED", "MANUAL_ORDER_TEST_MISSING", "OPERATOR_APPROVAL_MISSING", "READ_ONLY_BURN_IN_MISSING"):
        if required_code not in codes:
            return fail_result("upbit_live_review_preflight_validator", f"preflight omitted blocker: {required_code}", paths, required_code)

    burn_in_only = build_upbit_live_review_preflight(
        authority=authority,
        preflight_id="validator-burn-in-only",
        read_only_burn_in_status="PASS",
    )
    burn_in_only_result = validate_live_preflight_report(burn_in_only)
    if burn_in_only_result.status != "PASS":
        return fail_result("upbit_live_review_preflight_validator", "burn-in-only preflight scaffold failed validation", paths, burn_in_only_result.blocker_code or "UNKNOWN_BLOCKED")
    if burn_in_only.get("live_order_ready") or "LIVE_READY_MISSING" not in {blocker.get("code") for blocker in burn_in_only["blockers"]}:
        return fail_result("upbit_live_review_preflight_validator", "read-only burn-in was treated as live readiness", paths, "LIVE_FINAL_GUARD_FAILED")

    preflight_live = build_upbit_live_review_preflight(authority=authority, preflight_id="validator-preflight-live")
    preflight_live["live_order_ready"] = True
    preflight_live["live_order_allowed"] = True
    preflight_live["can_submit_order"] = True
    preflight_live["preflight_hash"] = live_preflight_hash(preflight_live)
    preflight_live_result = validate_live_preflight_report(preflight_live)
    if preflight_live_result.status != "BLOCKED" or preflight_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_live_review_preflight_validator", "live preflight mutation was not blocked", paths, preflight_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    dashboard = build_live_review_dashboard(authority=authority, preflight_report=preflight)
    dashboard_result = validate_live_review_dashboard(dashboard)
    if dashboard_result.status != "PASS":
        return fail_result("upbit_live_review_preflight_validator", f"live review dashboard failed: {dashboard_result.message}", paths, dashboard_result.blocker_code or "UNKNOWN_BLOCKED")
    if dashboard.get("order_controls_present") or dashboard.get("live_order_ready") or dashboard.get("live_order_allowed") or dashboard.get("can_live_trade"):
        return fail_result("upbit_live_review_preflight_validator", "live review dashboard created order controls or live permission", paths, "LIVE_FINAL_GUARD_FAILED")
    dashboard_live = build_live_review_dashboard(authority=authority, preflight_report=preflight, dashboard_id="validator-dashboard-live")
    dashboard_live["live_order_ready"] = True
    dashboard_live["dashboard_hash"] = live_review_dashboard_hash(dashboard_live)
    dashboard_live_result = validate_live_review_dashboard(dashboard_live)
    if dashboard_live_result.status != "BLOCKED" or dashboard_live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result("upbit_live_review_preflight_validator", "dashboard live mutation was not blocked", paths, dashboard_live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED")

    return pass_result("upbit_live_review_preflight_validator", "Upbit live review scaffold is review-only and blocks all live orders", paths)


def _patch_result_paths() -> list[Path]:
    return sorted((ROOT / "system" / "evidence" / "patch_results").glob("*.patch_result.json"))


def _live_flag_is_true(value: Any) -> bool:
    return value is True or value == "true" or value == "TRUE"


def _schema_scaffold_validator(validator_id: str, schema_filename: str, expected_schema_id: str) -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / schema_filename
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    registry_path = ROOT / "contracts" / "registry.yaml"
    paths = [schema_path, state_path, registry_path]
    schema = load_json(schema_path)
    if schema.get("$id") != expected_schema_id:
        return fail_result(validator_id, f"schema id mismatch: {schema_filename}", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result(validator_id, f"schema is not closed: {schema_filename}", paths, "SCHEMA_IDENTITY_MISMATCH")
    required = set(schema.get("required", []))
    if not {"schema_id", "generated_at_utc", "project_id", "authority"}.issubset(required):
        return fail_result(validator_id, f"schema missing baseline required fields: {schema_filename}", paths, "SCHEMA_IDENTITY_MISMATCH")
    authority = schema.get("properties", {}).get("authority", {})
    if authority.get("additionalProperties") is not False:
        return fail_result(validator_id, f"authority block is not closed: {schema_filename}", paths, "SCHEMA_IDENTITY_MISMATCH")
    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(validator_id, f"current state has forbidden live flag: {field}", paths, "LIVE_FINAL_GUARD_FAILED")
    return pass_result(validator_id, f"{expected_schema_id} scaffold is closed, authority-bound, and non-live", paths)


def _convergence_objective_profile_hash(profile: dict[str, Any]) -> str:
    normalized = dict(profile)
    normalized.pop("profile_hash", None)
    return sha256_json(normalized)


def _build_convergence_objective_profile(**overrides: Any) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "schema_id": "trader1.convergence_objective_profile.v1",
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": current_authority_hashes(),
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "status": "COLLECTING",
        "objective_profile_id": "mvp4_convergence_objective_profile",
        "objective_profile_version": "v1",
        "objective_status": "EVALUATION_ONLY",
        "source_modes": ["REPLAY", "PAPER", "SHADOW"],
        "objective_components": [
            {"component_id": "net_ev_after_cost", "component_kind": "NET_EV_AFTER_COST", "weight": 1.0, "required": True},
            {"component_id": "drawdown_penalty", "component_kind": "DRAWDOWN_PENALTY", "weight": 0.35, "required": True},
            {"component_id": "slippage_penalty", "component_kind": "SLIPPAGE_PENALTY", "weight": 0.25, "required": True},
            {"component_id": "fee_penalty", "component_kind": "FEE_PENALTY", "weight": 0.25, "required": True},
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
        "blockers": [],
        "notes": "Scores are research-only until independent live-enabling evidence exists.",
    }
    profile.update(overrides)
    profile["profile_hash"] = _convergence_objective_profile_hash(profile)
    return profile


def _convergence_objective_profile_errors(profile: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.convergence_objective_profile.v1")
    if schema is None:
        return ["convergence objective profile schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(profile, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    if profile.get("profile_hash") != _convergence_objective_profile_hash(profile):
        errors.append("convergence objective profile hash mismatch")
    if profile.get("mode") == "LIVE" or "LIVE" in set(profile.get("source_modes", [])):
        errors.append("convergence objective profile must not use LIVE mode or LIVE source evidence in MVP-4")
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
    ):
        if _live_flag_is_true(profile.get(field)):
            errors.append(f"convergence objective profile has forbidden true field: {field}")
    if profile.get("raw_pnl_only_allowed"):
        errors.append("raw PnL only objective is forbidden; net EV after cost is required")
    if profile.get("net_ev_after_cost_required") is not True:
        errors.append("net_ev_after_cost_required must be true")

    component_kinds = {
        component.get("component_kind")
        for component in profile.get("objective_components", [])
        if isinstance(component, dict)
    }
    required_components = {"NET_EV_AFTER_COST", "FEE_PENALTY", "SLIPPAGE_PENALTY", "DRAWDOWN_PENALTY", "OOS_ROBUSTNESS"}
    missing_components = sorted(required_components - component_kinds)
    if missing_components:
        errors.append(f"convergence objective profile missing required objective components: {missing_components}")
    for component in profile.get("objective_components", []):
        if isinstance(component, dict) and component.get("required") and component.get("weight", 0) <= 0:
            errors.append(f"required objective component must have positive weight: {component.get('component_id')}")

    warning = str(profile.get("operator_warning", "")).lower()
    if "not live_ready" not in warning or "live orders blocked" not in warning:
        errors.append("operator_warning must say not LIVE_READY and live orders blocked")
    return errors


def convergence_objective_profile_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "convergence_objective_profile.schema.json"
    module_path = ROOT / "trader1" / "validation" / "mvp0_validators.py"
    test_path = ROOT / "tests" / "validators" / "test_convergence_foundation_validators.py"
    paths = [schema_path, module_path, test_path]

    valid_profile = _build_convergence_objective_profile()
    errors = _convergence_objective_profile_errors(valid_profile)
    if errors:
        return fail_result("convergence_objective_profile_validator", errors[0], paths, "SCHEMA_IDENTITY_MISMATCH")

    raw_pnl_only = _build_convergence_objective_profile(raw_pnl_only_allowed=True)
    if not any("raw PnL only" in error for error in _convergence_objective_profile_errors(raw_pnl_only)):
        return fail_result("convergence_objective_profile_validator", "raw PnL only objective was not rejected", paths, "CONVERGENCE_STATE_UNTESTED")

    missing_net_ev = _build_convergence_objective_profile(net_ev_after_cost_required=False)
    if not any("net_ev_after_cost_required" in error for error in _convergence_objective_profile_errors(missing_net_ev)):
        return fail_result("convergence_objective_profile_validator", "missing net EV after cost requirement was not rejected", paths, "CONVERGENCE_STATE_UNTESTED")

    live_source = _build_convergence_objective_profile(mode="LIVE", source_modes=["PAPER", "LIVE"])
    if not any("LIVE mode or LIVE source" in error for error in _convergence_objective_profile_errors(live_source)):
        return fail_result("convergence_objective_profile_validator", "LIVE source evidence was not rejected", paths, "LIVE_FINAL_GUARD_FAILED")

    live_flags = _build_convergence_objective_profile(live_order_allowed=True, can_live_trade=True, scale_up_allowed=True)
    if not any("forbidden true field" in error for error in _convergence_objective_profile_errors(live_flags)):
        return fail_result("convergence_objective_profile_validator", "objective profile live/scale mutation was not rejected", paths, "LIVE_FINAL_GUARD_FAILED")

    missing_cost_component = _build_convergence_objective_profile(
        objective_components=[
            {"component_id": "net_ev_after_cost", "component_kind": "NET_EV_AFTER_COST", "weight": 1.0, "required": True},
            {"component_id": "drawdown_penalty", "component_kind": "DRAWDOWN_PENALTY", "weight": 0.35, "required": True},
            {"component_id": "oos_robustness", "component_kind": "OOS_ROBUSTNESS", "weight": 0.4, "required": True},
        ]
    )
    if not any("missing required objective components" in error for error in _convergence_objective_profile_errors(missing_cost_component)):
        return fail_result("convergence_objective_profile_validator", "missing fee/slippage objective components were not rejected", paths, "CONVERGENCE_STATE_UNTESTED")

    tampered = dict(valid_profile)
    tampered["operator_warning"] = "ready"
    if not any("hash mismatch" in error for error in _convergence_objective_profile_errors(tampered)):
        return fail_result("convergence_objective_profile_validator", "objective profile hash tamper was not rejected", paths, "SCHEMA_IDENTITY_MISMATCH")

    return pass_result(
        "convergence_objective_profile_validator",
        "convergence objective profile requires net EV after cost, cost penalties, non-live sources, and live/scale blockers",
        paths,
    )


def _optimizer_memory_state_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.optimizer_memory_state.v1")
    if schema is None:
        return ["optimizer_memory_state schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "active_snapshot_mutation_allowed",
        "optimizer_winner_live_config_allowed",
        "paper_winner_live_config_allowed",
        "memory_reset_without_audit_allowed",
        "forget_failed_candidate_allowed",
        "cross_scope_memory_reuse_allowed",
        "scale_up_from_memory_allowed",
        "order_submission_allowed",
        "exchange_account_call_allowed",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"optimizer memory has forbidden live, reset, cross-scope, exchange, or scale field: {field}")

    if report.get("mode") == "LIVE":
        errors.append("optimizer memory mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("optimizer memory source_modes must not include LIVE")

    warning_lower = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning_lower or "live orders" not in warning_lower:
        errors.append("optimizer memory warning must state not LIVE_READY and live orders blocked")

    sequence = report.get("memory_sequence_number")
    previous_hash = report.get("previous_memory_state_hash")
    if isinstance(sequence, int) and sequence > 1 and not previous_hash:
        errors.append("memory_sequence_number greater than 1 requires previous_memory_state_hash")
    if report.get("last_write_kind") == "APPEND" and not previous_hash:
        errors.append("APPEND memory write requires previous_memory_state_hash")

    records = report.get("candidate_memory_records", [])
    failed_count = sum(1 for record in records if record.get("memory_record_status") == "FAILED")
    blocked_count = sum(1 for record in records if record.get("memory_record_status") == "BLOCKED")
    retired_count = sum(1 for record in records if record.get("memory_record_status") == "RETIRED")
    if report.get("failed_candidate_count") != failed_count:
        errors.append("failed_candidate_count must match FAILED candidate records")
    if report.get("blocked_candidate_count") != blocked_count:
        errors.append("blocked_candidate_count must match BLOCKED candidate records")
    if report.get("retired_candidate_count") != retired_count:
        errors.append("retired_candidate_count must match RETIRED candidate records")

    for record in records:
        status = record.get("memory_record_status")
        candidate_id = record.get("candidate_id", "UNKNOWN_CANDIDATE")
        if status in {"FAILED", "BLOCKED", "RETIRED"}:
            if not record.get("promotion_blocked"):
                errors.append(f"{status} candidate must remain promotion_blocked: {candidate_id}")
            if not record.get("live_order_blocked"):
                errors.append(f"{status} candidate must remain live_order_blocked: {candidate_id}")
        if status == "FAILED" and int(record.get("failure_count", 0)) <= 0:
            errors.append(f"FAILED candidate must preserve positive failure_count: {candidate_id}")
        if status == "FAILED" and record.get("primary_root_cause_code") == "UNKNOWN_ROOT_CAUSE":
            errors.append(f"FAILED candidate must not be promoted with UNKNOWN_ROOT_CAUSE: {candidate_id}")

    if report.get("memory_status") == "ACTIVE_APPEND_ONLY":
        if report.get("blockers"):
            errors.append("ACTIVE_APPEND_ONLY memory state must not carry blockers")
        if report.get("state_write_policy") != "APPEND_AUDIT_ONLY":
            errors.append("ACTIVE_APPEND_ONLY memory state requires APPEND_AUDIT_ONLY")
    elif not report.get("blockers"):
        errors.append("non-active optimizer memory state must carry explicit blocker evidence")

    return errors


def optimizer_memory_state_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "optimizer_memory_state.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "optimizer_memory_state_pass.json"
    live_flag_path = fixture_dir / "optimizer_memory_state_live_flag_fail.json"
    reset_path = fixture_dir / "optimizer_memory_state_reset_without_audit_fail.json"
    forget_path = fixture_dir / "optimizer_memory_state_forget_failed_candidate_fail.json"
    cross_scope_path = fixture_dir / "optimizer_memory_state_cross_scope_reuse_fail.json"
    failed_unblocked_path = fixture_dir / "optimizer_memory_state_failed_candidate_unblocked_fail.json"
    append_hash_path = fixture_dir / "optimizer_memory_state_append_without_hash_fail.json"
    live_source_path = fixture_dir / "optimizer_memory_state_live_source_mode_fail.json"
    paths = [
        schema_path,
        pass_path,
        live_flag_path,
        reset_path,
        forget_path,
        cross_scope_path,
        failed_unblocked_path,
        append_hash_path,
        live_source_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "optimizer_memory_state_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _optimizer_memory_state_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "optimizer_memory_state_validator",
            f"PASS fixture failed optimizer memory validation: {pass_errors[0]}",
            paths,
            "OPTIMIZER_MEMORY_UNSAFE",
        )

    negative_expectations = {
        live_flag_path: "expected const False",
        reset_path: "expected const False",
        forget_path: "expected const True",
        cross_scope_path: "expected const False",
        failed_unblocked_path: "FAILED candidate must remain promotion_blocked",
        append_hash_path: "APPEND memory write requires previous_memory_state_hash",
        live_source_path: "LIVE",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _optimizer_memory_state_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "optimizer_memory_state_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "OPTIMIZER_MEMORY_UNSAFE",
            )

    return pass_result(
        "optimizer_memory_state_validator",
        "optimizer memory is append-audit-only, hash-linked, scoped, failed-candidate-preserving, and cannot create live, scale-up, exchange, or cross-scope permission",
        paths,
    )


def _strategy_performance_memory_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.strategy_performance_memory.v1")
    if schema is None:
        return ["strategy_performance_memory schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "active_snapshot_mutation_allowed",
        "optimizer_winner_live_config_allowed",
        "paper_winner_live_config_allowed",
        "order_submission_allowed",
        "exchange_account_call_allowed",
        "scale_up_from_performance_allowed",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"strategy performance memory has forbidden live, exchange, active, or scale field: {field}")

    if report.get("mode") == "LIVE":
        errors.append("strategy performance memory mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("strategy performance memory source_modes must not include LIVE")

    warning_lower = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning_lower or "live orders" not in warning_lower:
        errors.append("strategy performance memory warning must state not LIVE_READY and live orders blocked")

    sample_count = int(report.get("sample_count", 0))
    min_required = int(report.get("min_required_sample_count", 0))
    trade_count = int(report.get("trade_count", 0))
    no_trade_count = int(report.get("no_trade_count", 0))
    performance_status = report.get("performance_status")
    blockers = report.get("blockers", [])

    if sample_count < min_required and performance_status == "IMPROVING_AFTER_COST":
        errors.append("IMPROVING_AFTER_COST requires sample_count >= min_required_sample_count")
    if trade_count + no_trade_count > sample_count:
        errors.append("trade_count plus no_trade_count must not exceed sample_count")

    total_cost = (
        float(report.get("fee_cost", 0))
        + float(report.get("spread_cost", 0))
        + float(report.get("slippage_cost", 0))
        + float(report.get("market_impact_cost", 0))
    )
    gross_pnl = float(report.get("gross_pnl", 0))
    net_ev = float(report.get("net_ev_after_cost", 0))
    if net_ev > gross_pnl - total_cost + 1e-9:
        errors.append("net_ev_after_cost must not exceed gross_pnl minus fee, spread, slippage, and market impact costs")
    if performance_status == "IMPROVING_AFTER_COST" and net_ev <= 0:
        errors.append("IMPROVING_AFTER_COST requires positive net_ev_after_cost")
    if performance_status in {"BLOCKED", "STALE_SAFE_MODE"} and not blockers:
        errors.append("blocked or stale strategy performance memory must carry explicit blocker evidence")
    if performance_status == "COLLECTING" and not blockers:
        errors.append("COLLECTING strategy performance memory must carry collection blocker evidence")

    if not report.get("entry_reason_counts"):
        errors.append("entry_reason_counts are required")
    if not report.get("exit_reason_counts"):
        errors.append("exit_reason_counts are required")
    if not report.get("no_trade_reason_counts"):
        errors.append("no_trade_reason_counts are required")

    regimes = {item.get("regime"): item for item in report.get("regime_performance", []) if isinstance(item, dict)}
    for required_regime in ("UPTREND", "RANGE", "DOWNTREND", "RISK_OFF"):
        if required_regime not in regimes:
            errors.append(f"regime_performance must include {required_regime}")
    for regime_name in ("DOWNTREND", "RISK_OFF"):
        regime = regimes.get(regime_name)
        if regime and regime.get("trade_allowed"):
            errors.append(f"{regime_name} regime must not allow trading in MVP-4 strategy performance memory")
        if regime and regime.get("primary_blocker_code") is None:
            errors.append(f"{regime_name} regime requires primary_blocker_code")

    if report.get("performance_scope") == "PAPER_SHADOW_RESEARCH_ONLY":
        source_modes = set(report.get("source_modes", []))
        if not {"PAPER", "SHADOW"}.issubset(source_modes):
            errors.append("PAPER_SHADOW_RESEARCH_ONLY requires PAPER and SHADOW source modes")

    return errors


def strategy_performance_memory_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "strategy_performance_memory.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "strategy_performance_memory_pass.json"
    live_flag_path = fixture_dir / "strategy_performance_memory_live_flag_fail.json"
    raw_pnl_path = fixture_dir / "strategy_performance_memory_raw_pnl_positive_net_negative_fail.json"
    sample_path = fixture_dir / "strategy_performance_memory_insufficient_sample_fail.json"
    reason_path = fixture_dir / "strategy_performance_memory_missing_reason_fail.json"
    downtrend_path = fixture_dir / "strategy_performance_memory_downtrend_trade_allowed_fail.json"
    mixed_source_path = fixture_dir / "strategy_performance_memory_live_source_mixing_fail.json"
    unscoped_path = fixture_dir / "strategy_performance_memory_unscoped_fail.json"
    paths = [
        schema_path,
        pass_path,
        live_flag_path,
        raw_pnl_path,
        sample_path,
        reason_path,
        downtrend_path,
        mixed_source_path,
        unscoped_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "strategy_performance_memory_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _strategy_performance_memory_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "strategy_performance_memory_validator",
            f"PASS fixture failed strategy performance memory validation: {pass_errors[0]}",
            paths,
            "CONVERGENCE_MEMORY_MISSING",
        )

    negative_expectations = {
        live_flag_path: "expected const False",
        raw_pnl_path: "IMPROVING_AFTER_COST requires positive net_ev_after_cost",
        sample_path: "sample_count >= min_required_sample_count",
        reason_path: "minItems",
        downtrend_path: "DOWNTREND regime must not allow trading",
        mixed_source_path: "LIVE",
        unscoped_path: "expected const True",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _strategy_performance_memory_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "strategy_performance_memory_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "CONVERGENCE_MEMORY_MISSING",
            )

    return pass_result(
        "strategy_performance_memory_validator",
        "strategy performance memory requires net EV after cost, scoped paper/shadow evidence, regime coverage, downtrend/risk-off blocking, reasons, and false live flags",
        paths,
    )


def overfit_diagnostic_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "overfit_diagnostic_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "overfit_diagnostic_pass.json"
    short_window_fail_path = fixture_dir / "overfit_diagnostic_short_window_fail.json"
    bootstrap_fail_path = fixture_dir / "overfit_diagnostic_bootstrap_unstable_fail.json"
    live_flag_fail_path = fixture_dir / "overfit_diagnostic_live_flag_fail.json"
    paths = [schema_path, pass_path, short_window_fail_path, bootstrap_fail_path, live_flag_fail_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "overfit_diagnostic_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _overfit_diagnostic_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "overfit_diagnostic_validator",
            f"PASS fixture failed overfit diagnostic validation: {pass_errors[0]}",
            paths,
            "OVERFIT_RISK_HIGH",
        )

    negative_expectations = {
        short_window_fail_path: "sample_count below min_required_sample_count",
        bootstrap_fail_path: "bootstrap_status must be PASS",
        live_flag_fail_path: "expected const False",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _overfit_diagnostic_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "overfit_diagnostic_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "OVERFIT_RISK_HIGH",
            )

    return pass_result(
        "overfit_diagnostic_validator",
        "overfit diagnostics require OOS, walk-forward, bootstrap, bias, concentration, and false live flags",
        paths,
    )


def execution_feedback_loop_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "optimizer_feedback_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "optimizer_feedback_pass.json"
    slippage_fail_path = fixture_dir / "optimizer_feedback_slippage_divergent_fail.json"
    missing_blocker_path = fixture_dir / "optimizer_feedback_missing_blocker_fail.json"
    live_flag_fail_path = fixture_dir / "optimizer_feedback_live_flag_fail.json"
    missing_risk_review_path = fixture_dir / "optimizer_feedback_missing_risk_review_fail.json"
    paths = [schema_path, pass_path, slippage_fail_path, missing_blocker_path, live_flag_fail_path, missing_risk_review_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "execution_feedback_loop_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _optimizer_feedback_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "execution_feedback_loop_validator",
            f"PASS fixture failed optimizer feedback validation: {pass_errors[0]}",
            paths,
            "EXECUTION_FEEDBACK_DIVERGENT",
        )

    negative_expectations = {
        slippage_fail_path: "slippage_deviation_bps above max_allowed_slippage_deviation_bps",
        missing_blocker_path: "non-eligible optimizer feedback must carry explicit blocker evidence",
        live_flag_fail_path: "expected const False",
        missing_risk_review_path: "feedback_eligible requires risk_review_status=PASS",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _optimizer_feedback_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "execution_feedback_loop_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "EXECUTION_FEEDBACK_DIVERGENT",
            )

    return pass_result(
        "execution_feedback_loop_validator",
        "execution feedback requires expected-vs-realized cost checks, risk review linkage, hash integrity, ranking action, and false live flags",
        paths,
    )


def _actual_runtime_requirement_pass_statuses() -> dict[str, str]:
    return {
        "runtime_span": "PASS",
        "cycle_count": "PASS",
        "heartbeat_freshness": "PASS",
        "recovery_clean": "PASS",
        "partial_write_clean": "PASS",
    }


def paper_shadow_evidence_accumulation_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "paper_shadow_evidence_accumulation_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "paper_shadow_evidence_accumulation_pass.json"
    insufficient_path = fixture_dir / "paper_shadow_evidence_accumulation_insufficient_sample_fail.json"
    stale_path = fixture_dir / "paper_shadow_evidence_accumulation_stale_fail.json"
    missing_reason_path = fixture_dir / "paper_shadow_evidence_accumulation_missing_reason_fail.json"
    live_flag_path = fixture_dir / "paper_shadow_evidence_accumulation_live_flag_fail.json"
    identity_mismatch_path = fixture_dir / "paper_shadow_evidence_accumulation_identity_mismatch_fail.json"
    identity_stale_path = fixture_dir / "paper_shadow_evidence_accumulation_identity_stale_fail.json"
    long_run_claim_path = fixture_dir / "paper_shadow_evidence_accumulation_false_long_run_claim_fail.json"
    paths = [
        schema_path,
        pass_path,
        insufficient_path,
        stale_path,
        missing_reason_path,
        live_flag_path,
        identity_mismatch_path,
        identity_stale_path,
        long_run_claim_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "paper_shadow_evidence_accumulation_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _paper_shadow_evidence_accumulation_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "paper_shadow_evidence_accumulation_validator",
            f"PASS fixture failed paper/shadow evidence validation: {pass_errors[0]}",
            paths,
            "MEASUREMENT_MISSING",
        )

    negative_expectations = {
        insufficient_path: "sample count below min_required_sample_count",
        stale_path: "artifact age exceeds max_artifact_age_seconds",
        missing_reason_path: "entry and no-trade reason counts are required",
        live_flag_path: "expected const False",
        identity_mismatch_path: "source evidence binding mismatch for artifact_hash",
        identity_stale_path: "source evidence binding status is not PASS",
        long_run_claim_path: "long-run evidence eligibility claimed before minimum window/span coverage",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _paper_shadow_evidence_accumulation_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "paper_shadow_evidence_accumulation_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "MEASUREMENT_MISSING",
            )

    supporting_window_ids = [
        source_id
        for index in range(20)
        for source_id in (
            f"paper-operation:window-{index:03d}:paper-hash-{index:03d}",
            f"shadow-evidence:window-{index:03d}:shadow-hash-{index:03d}",
        )
    ]
    display_truth_runtime = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id="validator-paper-shadow-display-truth-runtime-source",
        evidence_window_count=20,
        min_required_evidence_window_count=20,
        evidence_span_hours=120,
        min_required_evidence_span_hours=120,
        source_evidence_ids=supporting_window_ids,
        actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
        actual_runtime_requirement_statuses=_actual_runtime_requirement_pass_statuses(),
        actual_runtime_source_evidence_ids=[
            "dashboard_shell:summary.json:" + "D" * 64,
            "heartbeat:heartbeat.json:" + "E" * 64,
        ],
    )
    display_truth_errors = _paper_shadow_evidence_accumulation_errors(display_truth_runtime)
    if not any("display-only, not execution evidence" in error for error in display_truth_errors):
        return fail_result(
            "paper_shadow_evidence_accumulation_validator",
            "display/dashboard/heartbeat source ids were not rejected as actual runtime evidence",
            paths,
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        )

    paper_only_runtime = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id="validator-paper-shadow-paper-only-runtime-source",
        evidence_window_count=20,
        min_required_evidence_window_count=20,
        evidence_span_hours=120,
        min_required_evidence_span_hours=120,
        source_evidence_ids=supporting_window_ids,
        actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
        actual_runtime_requirement_statuses=_actual_runtime_requirement_pass_statuses(),
        actual_runtime_source_evidence_ids=[
            "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "D" * 64,
            "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "E" * 64,
        ],
    )
    paper_only_errors = _paper_shadow_evidence_accumulation_errors(paper_only_runtime)
    if not any("both PAPER and SHADOW persistent runtime sources" in error for error in paper_only_errors):
        return fail_result(
            "paper_shadow_evidence_accumulation_validator",
            "single-sided PAPER runtime source id was not rejected as incomplete PAPER/SHADOW evidence",
            paths,
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        )

    long_run_state_drift = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id="validator-paper-shadow-long-run-state-drift",
        evidence_window_count=20,
        min_required_evidence_window_count=20,
        evidence_span_hours=120,
        min_required_evidence_span_hours=120,
        source_evidence_ids=supporting_window_ids,
        actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
        actual_runtime_requirement_statuses=_actual_runtime_requirement_pass_statuses(),
        actual_runtime_source_evidence_ids=[
            "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "D" * 64,
            "actual-runtime-source:upbit:krw_spot:shadow:mvp4_shadow_evidence:" + "E" * 64,
        ],
    )
    long_run_state_drift["long_run_evidence_eligible"] = False
    long_run_state_drift["long_run_blocker_code"] = "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING"
    long_run_state_drift["scorecard_input_eligible"] = True
    long_run_state_drift["evidence_chain_complete"] = True
    long_run_state_drift["optimizer_ranking_action"] = "ALLOW_RANKING"
    long_run_state_drift["blockers"] = []
    long_run_state_drift["primary_blocker_code"] = None
    long_run_state_drift["evidence_hash"] = paper_shadow_evidence_hash(long_run_state_drift)
    long_run_state_errors = _paper_shadow_evidence_accumulation_errors(long_run_state_drift)
    if not any("long-run eligibility flag must match" in error for error in long_run_state_errors):
        return fail_result(
            "paper_shadow_evidence_accumulation_validator",
            "long-run eligibility state drift was not rejected",
            paths,
            "MEASUREMENT_MISSING",
        )

    unpaired_supporting_windows = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id="validator-paper-shadow-unpaired-supporting-windows",
        evidence_window_count=20,
        min_required_evidence_window_count=20,
        evidence_span_hours=120,
        min_required_evidence_span_hours=120,
        source_evidence_ids=[
            *[f"paper-operation:paper-window-{index:03d}:paper-hash-{index:03d}" for index in range(20)],
            *[f"shadow-evidence:shadow-window-{index:03d}:shadow-hash-{index:03d}" for index in range(20)],
        ],
        actual_runtime_source_status="VALIDATED_NON_LIVE_RUNTIME",
        actual_runtime_requirement_statuses=_actual_runtime_requirement_pass_statuses(),
        actual_runtime_source_evidence_ids=[
            "actual-runtime-source:upbit:krw_spot:paper:mvp4_paper_evidence:" + "D" * 64,
            "actual-runtime-source:upbit:krw_spot:shadow:mvp4_shadow_evidence:" + "E" * 64,
        ],
    )
    unpaired_window_errors = _paper_shadow_evidence_accumulation_errors(unpaired_supporting_windows)
    if not any("per-window PAPER and SHADOW supporting source ids" in error for error in unpaired_window_errors):
        return fail_result(
            "paper_shadow_evidence_accumulation_validator",
            "unpaired PAPER/SHADOW supporting window ids were not rejected",
            paths,
            "MEASUREMENT_MISSING",
        )

    legacy_partial_report = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id="validator-paper-shadow-legacy-partial-runtime-fields"
    )
    for required_field in (
        "actual_runtime_source_evidence_ids",
        "actual_runtime_source_status",
        "actual_runtime_requirement_statuses",
        "supporting_source_evidence_ids",
    ):
        legacy_partial = dict(legacy_partial_report)
        legacy_partial.pop(required_field, None)
        legacy_errors = _paper_shadow_evidence_accumulation_errors(legacy_partial)
        if not any(required_field in error for error in legacy_errors):
            return fail_result(
                "paper_shadow_evidence_accumulation_validator",
                f"legacy partial paper/shadow evidence missing {required_field} was not rejected",
                paths,
                "SCHEMA_IDENTITY_MISMATCH",
            )

    return pass_result(
        "paper_shadow_evidence_accumulation_validator",
        "paper/shadow evidence requires source identity bindings, session hashes, samples, freshness, reasons, cost evidence, explicit long-run maturity status, and false live flags",
        paths,
    )


def shadow_observation_runtime_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "shadow_observation_report.schema.json"
    module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation.py"
    paper_module_path = ROOT / "trader1" / "runtime" / "paper" / "operational_cycle.py"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    paths = [schema_path, module_path, paper_module_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "shadow_observation_runtime_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.shadow_observation_report.v1":
        return fail_result("shadow_observation_runtime_validator", "shadow observation schema id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("shadow_observation_runtime_validator", "shadow observation schema is not closed", paths, "SCHEMA_IDENTITY_MISMATCH")

    paper_gate = build_upbit_operational_paper_cycle(
        operation_gate_id="validator-shadow-observation-source",
        session_id="validator-shadow-observation-paper",
        requested_entry=True,
    )
    report = build_shadow_observation_report(
        observation_id="validator-shadow-observation",
        paper_operation_gate_report=paper_gate,
        shadow_session_id="validator-shadow-observation-shadow",
        shadow_sample_count=30,
    )
    schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
    instance_schema = schema_for_instance(report, schema_bundle)
    if instance_schema is None:
        return fail_result("shadow_observation_runtime_validator", "shadow observation instance did not map to schema", paths, "SCHEMA_IDENTITY_MISMATCH")
    instance_result = validate_instance_against_schema(report, instance_schema, schema_bundle)
    if instance_result.status != "PASS":
        return fail_result(
            "shadow_observation_runtime_validator",
            f"shadow observation instance schema failed: {instance_result.errors[0]}",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    result = validate_shadow_observation_report(report)
    if result.status != "PASS":
        return fail_result(
            "shadow_observation_runtime_validator",
            f"valid shadow observation was not accepted: {result.message}",
            paths,
            result.blocker_code or "UNKNOWN_BLOCKED",
        )

    live_mutation = dict(report)
    live_mutation["live_order_allowed"] = True
    live_mutation["observation_hash"] = shadow_observation_hash(live_mutation)
    live_result = validate_shadow_observation_report(live_mutation)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_runtime_validator",
            "shadow observation live flag mutation was not blocked",
            paths,
            live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    same_session = build_shadow_observation_report(
        observation_id="validator-shadow-observation-same-session",
        paper_operation_gate_report=paper_gate,
        shadow_session_id=paper_gate["session_id"],
        shadow_sample_count=30,
    )
    same_session_result = validate_shadow_observation_report(same_session)
    if same_session_result.status != "BLOCKED" or same_session_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result(
            "shadow_observation_runtime_validator",
            "same PAPER/SHADOW session was not blocked",
            paths,
            same_session_result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH",
        )

    stale = build_shadow_observation_report(
        observation_id="validator-shadow-observation-stale",
        paper_operation_gate_report=paper_gate,
        shadow_session_id="validator-shadow-observation-stale-shadow",
        shadow_sample_count=30,
        shadow_artifact_age_seconds=901,
        max_artifact_age_seconds=900,
    )
    stale_result = validate_shadow_observation_report(stale)
    if stale_result.status != "BLOCKED" or stale_result.blocker_code != "DATA_QUALITY_INSUFFICIENT":
        return fail_result(
            "shadow_observation_runtime_validator",
            "stale SHADOW observation was not blocked",
            paths,
            stale_result.blocker_code or "DATA_QUALITY_INSUFFICIENT",
        )

    tampered_source = dict(paper_gate)
    tampered_source["operation_gate_id"] = "validator-shadow-observation-tampered-source"
    tampered = build_shadow_observation_report(
        observation_id="validator-shadow-observation-tampered-source",
        paper_operation_gate_report=tampered_source,
        shadow_sample_count=30,
    )
    tampered_result = validate_shadow_observation_report(tampered)
    if tampered_result.status != "BLOCKED" or tampered_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result(
            "shadow_observation_runtime_validator",
            "tampered PAPER source was not blocked",
            paths,
            tampered_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )

    return pass_result(
        "shadow_observation_runtime_validator",
        "SHADOW observation runtime scaffold is schema-bound, paper-source-hash-bound, namespace-separated, stale-guarded, and live-blocked",
        paths,
    )


def shadow_observation_stream_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "shadow_observation_stream_report.schema.json"
    module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_stream.py"
    observation_module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation.py"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    paths = [schema_path, module_path, observation_module_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "shadow_observation_stream_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.shadow_observation_stream_report.v1":
        return fail_result("shadow_observation_stream_validator", "shadow observation stream schema id mismatch", paths, "SCHEMA_IDENTITY_MISMATCH")
    if schema.get("additionalProperties") is not False:
        return fail_result("shadow_observation_stream_validator", "shadow observation stream schema is not closed", paths, "SCHEMA_IDENTITY_MISMATCH")

    observations: list[dict[str, Any]] = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="validator-shadow-stream-source",
            session_id=f"validator-shadow-stream-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"validator-shadow-stream-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"validator-shadow-stream-shadow-{index}",
                shadow_sample_count=30,
            )
        )

    report = build_shadow_observation_stream_report(
        stream_id="validator-shadow-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
    instance_schema = schema_for_instance(report, schema_bundle)
    if instance_schema is None:
        return fail_result("shadow_observation_stream_validator", "shadow stream instance did not map to schema", paths, "SCHEMA_IDENTITY_MISMATCH")
    instance_result = validate_instance_against_schema(report, instance_schema, schema_bundle)
    if instance_result.status != "PASS":
        return fail_result(
            "shadow_observation_stream_validator",
            f"shadow stream instance schema failed: {instance_result.errors[0]}",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    result = validate_shadow_observation_stream_report(report)
    if result.status != "PASS":
        return fail_result(
            "shadow_observation_stream_validator",
            f"valid shadow stream was not accepted: {result.message}",
            paths,
            result.blocker_code or "UNKNOWN_BLOCKED",
        )

    duplicate = build_shadow_observation_stream_report(
        stream_id="validator-shadow-stream-duplicate",
        observations=[observations[0], observations[0], observations[1]],
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    duplicate_result = validate_shadow_observation_stream_report(duplicate)
    if duplicate_result.status != "BLOCKED" or duplicate_result.blocker_code != "DUPLICATE_WRITER_RISK":
        return fail_result(
            "shadow_observation_stream_validator",
            "duplicate SHADOW stream observation was not blocked",
            paths,
            duplicate_result.blocker_code or "DUPLICATE_WRITER_RISK",
        )

    duplicate_summary_drift = dict(report)
    duplicate_summary_drift["paper_operation_gate_hashes"] = list(report["paper_operation_gate_hashes"])
    duplicate_summary_drift["source_binding_hashes"] = list(report["source_binding_hashes"])
    duplicate_summary_drift["observation_bindings"] = [dict(item) for item in report["observation_bindings"]]
    duplicate_hash = duplicate_summary_drift["paper_operation_gate_hashes"][0]
    duplicate_summary_drift["paper_operation_gate_hashes"][1] = duplicate_hash
    duplicate_summary_drift["source_binding_hashes"][1] = duplicate_hash
    duplicate_summary_drift["observation_bindings"][1]["paper_operation_gate_hash"] = duplicate_hash
    duplicate_summary_drift["duplicate_paper_source_count"] = 0
    duplicate_summary_drift["stream_hash"] = shadow_observation_stream_hash(duplicate_summary_drift)
    duplicate_summary_result = validate_shadow_observation_stream_report(duplicate_summary_drift)
    if duplicate_summary_result.status != "BLOCKED" or duplicate_summary_result.blocker_code != "DUPLICATE_WRITER_RISK":
        return fail_result(
            "shadow_observation_stream_validator",
            "false-safe SHADOW stream duplicate summary drift was not blocked",
            paths,
            duplicate_summary_result.blocker_code or "DUPLICATE_WRITER_RISK",
        )

    evidence_window_drift = dict(report)
    evidence_window_drift["evidence_window_count"] = 99
    evidence_window_drift["stream_hash"] = shadow_observation_stream_hash(evidence_window_drift)
    evidence_window_result = validate_shadow_observation_stream_report(evidence_window_drift)
    if evidence_window_result.status != "BLOCKED" or evidence_window_result.blocker_code != "DATA_QUALITY_INSUFFICIENT":
        return fail_result(
            "shadow_observation_stream_validator",
            "false-safe SHADOW stream evidence window drift was not blocked",
            paths,
            evidence_window_result.blocker_code or "DATA_QUALITY_INSUFFICIENT",
        )

    non_monotonic_observations = [dict(item) for item in observations]
    for sequence, item in zip((1, 3, 2), non_monotonic_observations):
        item["stream_sequence_number"] = sequence
        item["observation_hash"] = shadow_observation_hash(item)
    non_monotonic = build_shadow_observation_stream_report(
        stream_id="validator-shadow-stream-non-monotonic",
        observations=non_monotonic_observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    non_monotonic_result = validate_shadow_observation_stream_report(non_monotonic)
    if non_monotonic_result.status != "BLOCKED" or non_monotonic_result.blocker_code != "PARTIAL_WRITE_RECOVERY_REQUIRED":
        return fail_result(
            "shadow_observation_stream_validator",
            "non-monotonic SHADOW stream sequence was not blocked",
            paths,
            non_monotonic_result.blocker_code or "PARTIAL_WRITE_RECOVERY_REQUIRED",
        )

    live_mutation_observations = [dict(item) for item in observations]
    live_mutation_observations[0]["live_order_allowed"] = True
    live_mutation_observations[0]["observation_hash"] = shadow_observation_hash(live_mutation_observations[0])
    live_mutation = build_shadow_observation_stream_report(
        stream_id="validator-shadow-stream-live-mutation",
        observations=live_mutation_observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    live_mutation_result = validate_shadow_observation_stream_report(live_mutation)
    if live_mutation_result.status != "BLOCKED" or live_mutation_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_stream_validator",
            "SHADOW stream live flag mutation was not blocked",
            paths,
            live_mutation_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    long_run_mutation = dict(report)
    long_run_mutation["long_run_evidence_eligible"] = True
    long_run_mutation["stream_hash"] = shadow_observation_stream_hash(long_run_mutation)
    long_run_result = validate_shadow_observation_stream_report(long_run_mutation)
    if long_run_result.status != "BLOCKED" or long_run_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_stream_validator",
            "SHADOW stream long-run eligibility mutation was not blocked",
            paths,
            long_run_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    return pass_result(
        "shadow_observation_stream_validator",
        "SHADOW observation stream is ordered, duplicate-guarded, source-hash-bound, stale-guarded, and live-blocked",
        paths,
    )


def shadow_observation_scheduler_guard_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "shadow_observation_scheduler_guard_report.schema.json"
    module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_scheduler.py"
    stream_module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_stream.py"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    paths = [schema_path, module_path, stream_module_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "shadow_observation_scheduler_guard_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.shadow_observation_scheduler_guard_report.v1":
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            "shadow observation scheduler guard schema id mismatch",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if schema.get("additionalProperties") is not False:
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            "shadow observation scheduler guard schema is not closed",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )

    observations: list[dict[str, Any]] = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="validator-shadow-scheduler-source",
            session_id=f"validator-shadow-scheduler-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"validator-shadow-scheduler-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"validator-shadow-scheduler-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream_report = build_shadow_observation_stream_report(
        stream_id="validator-shadow-scheduler-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    scheduler_report = build_shadow_observation_scheduler_guard_report(
        scheduler_id="validator-shadow-scheduler-pass",
        stream_report=stream_report,
        writer_id="validator-writer",
        active_writer_id="validator-writer",
    )

    schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
    instance_schema = schema_for_instance(scheduler_report, schema_bundle)
    if instance_schema is None:
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            "shadow scheduler guard instance did not map to schema",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    instance_result = validate_instance_against_schema(scheduler_report, instance_schema, schema_bundle)
    if instance_result.status != "PASS":
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            f"shadow scheduler guard instance schema failed: {instance_result.errors[0]}",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    result = validate_shadow_observation_scheduler_guard_report(scheduler_report)
    if result.status != "PASS":
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            f"valid shadow scheduler guard was not accepted: {result.message}",
            paths,
            result.blocker_code or "UNKNOWN_BLOCKED",
        )

    concurrent = build_shadow_observation_scheduler_guard_report(
        scheduler_id="validator-shadow-scheduler-concurrent",
        stream_report=stream_report,
        writer_id="validator-writer",
        active_writer_id="other-writer",
    )
    concurrent_result = validate_shadow_observation_scheduler_guard_report(concurrent)
    if concurrent_result.status != "BLOCKED" or concurrent_result.blocker_code != "DUPLICATE_WRITER_RISK":
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            "concurrent SHADOW scheduler writer was not blocked",
            paths,
            concurrent_result.blocker_code or "DUPLICATE_WRITER_RISK",
        )

    zero_lease = build_shadow_observation_scheduler_guard_report(
        scheduler_id="validator-shadow-scheduler-zero-lease",
        stream_report=stream_report,
        writer_id="validator-writer",
        active_writer_id="validator-writer",
        lock_lease_seconds=0,
    )
    zero_lease_result = validate_shadow_observation_scheduler_guard_report(zero_lease)
    if zero_lease_result.status != "BLOCKED" or zero_lease_result.blocker_code != "DUPLICATE_WRITER_RISK":
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            "zero-lease SHADOW scheduler lock was not blocked",
            paths,
            zero_lease_result.blocker_code or "DUPLICATE_WRITER_RISK",
        )

    lock_summary_drift = dict(scheduler_report)
    lock_summary_drift["active_writer_id"] = "other-writer"
    lock_summary_drift["lock_owner_match"] = True
    lock_summary_drift["concurrent_writer_detected"] = False
    lock_summary_drift["scheduler_guard_hash"] = shadow_observation_scheduler_guard_hash(lock_summary_drift)
    lock_summary_result = validate_shadow_observation_scheduler_guard_report(lock_summary_drift)
    if lock_summary_result.status != "BLOCKED" or lock_summary_result.blocker_code != "DUPLICATE_WRITER_RISK":
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            "false-safe SHADOW scheduler lock summary drift was not blocked",
            paths,
            lock_summary_result.blocker_code or "DUPLICATE_WRITER_RISK",
        )

    partial = build_shadow_observation_scheduler_guard_report(
        scheduler_id="validator-shadow-scheduler-partial",
        stream_report=stream_report,
        writer_id="validator-writer",
        partial_temp_artifact_count=1,
    )
    partial_result = validate_shadow_observation_scheduler_guard_report(partial)
    if partial_result.status != "BLOCKED" or partial_result.blocker_code != "PARTIAL_WRITE_RECOVERY_REQUIRED":
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            "partial SHADOW scheduler write was not blocked",
            paths,
            partial_result.blocker_code or "PARTIAL_WRITE_RECOVERY_REQUIRED",
        )

    sequence_gap = build_shadow_observation_scheduler_guard_report(
        scheduler_id="validator-shadow-scheduler-sequence-gap",
        stream_report=stream_report,
        writer_id="validator-writer",
        next_sequence_number=99,
    )
    sequence_gap_result = validate_shadow_observation_scheduler_guard_report(sequence_gap)
    if sequence_gap_result.status != "BLOCKED" or sequence_gap_result.blocker_code != "PARTIAL_WRITE_RECOVERY_REQUIRED":
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            "SHADOW scheduler sequence gap was not blocked",
            paths,
            sequence_gap_result.blocker_code or "PARTIAL_WRITE_RECOVERY_REQUIRED",
        )

    hash_drift = build_shadow_observation_scheduler_guard_report(
        scheduler_id="validator-shadow-scheduler-hash-drift",
        stream_report=stream_report,
        writer_id="validator-writer",
        persisted_stream_hash="A" * 64,
    )
    hash_drift_result = validate_shadow_observation_scheduler_guard_report(hash_drift)
    if hash_drift_result.status != "BLOCKED" or hash_drift_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            "SHADOW scheduler persisted hash drift was not blocked",
            paths,
            hash_drift_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )

    live_mutation = dict(scheduler_report)
    live_mutation["live_order_allowed"] = True
    live_mutation["scheduler_guard_hash"] = shadow_observation_scheduler_guard_hash(live_mutation)
    live_mutation_result = validate_shadow_observation_scheduler_guard_report(live_mutation)
    if live_mutation_result.status != "BLOCKED" or live_mutation_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_scheduler_guard_validator",
            "SHADOW scheduler live flag mutation was not blocked",
            paths,
            live_mutation_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    return pass_result(
        "shadow_observation_scheduler_guard_validator",
        "SHADOW observation scheduler guard is single-writer, sequence-safe, recovery-clean, and live-blocked",
        paths,
    )


def shadow_observation_persistent_runtime_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "shadow_observation_persistent_runtime_report.schema.json"
    module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_persistent_runtime.py"
    scheduler_module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_scheduler.py"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    paths = [schema_path, module_path, scheduler_module_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "shadow_observation_persistent_runtime_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.shadow_observation_persistent_runtime_report.v1":
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "shadow observation persistent runtime schema id mismatch",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if schema.get("additionalProperties") is not False:
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "shadow observation persistent runtime schema is not closed",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )

    observations: list[dict[str, Any]] = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="validator-shadow-persistent-runtime-source",
            session_id=f"validator-shadow-persistent-runtime-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"validator-shadow-persistent-runtime-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"validator-shadow-persistent-runtime-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream_report = build_shadow_observation_stream_report(
        stream_id="validator-shadow-persistent-runtime-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    scheduler_report = build_shadow_observation_scheduler_guard_report(
        scheduler_id="validator-shadow-persistent-runtime-scheduler",
        stream_report=stream_report,
        writer_id="validator-writer",
        active_writer_id="validator-writer",
    )
    runtime_report = build_shadow_observation_persistent_runtime_report(
        runtime_id="validator-shadow-persistent-runtime-pass",
        scheduler_guard_report=scheduler_report,
        requested_cycle_count=3,
        completed_cycle_count=3,
        max_cycle_count=10,
    )

    schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
    instance_schema = schema_for_instance(runtime_report, schema_bundle)
    if instance_schema is None:
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "shadow persistent runtime instance did not map to schema",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    instance_result = validate_instance_against_schema(runtime_report, instance_schema, schema_bundle)
    if instance_result.status != "PASS":
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            f"shadow persistent runtime instance schema failed: {instance_result.errors[0]}",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    result = validate_shadow_observation_persistent_runtime_report(runtime_report)
    if result.status != "PASS":
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            f"valid shadow persistent runtime was not accepted: {result.message}",
            paths,
            result.blocker_code or "UNKNOWN_BLOCKED",
        )

    over_limit = build_shadow_observation_persistent_runtime_report(
        runtime_id="validator-shadow-persistent-runtime-over-limit",
        scheduler_guard_report=scheduler_report,
        requested_cycle_count=11,
        max_cycle_count=10,
    )
    over_limit_result = validate_shadow_observation_persistent_runtime_report(over_limit)
    if over_limit_result.status != "BLOCKED" or over_limit_result.blocker_code != "RESOURCE_LIMIT_BLOCK":
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "persistent SHADOW runtime over-limit cycle request was not blocked",
            paths,
            over_limit_result.blocker_code or "RESOURCE_LIMIT_BLOCK",
        )

    partial = build_shadow_observation_persistent_runtime_report(
        runtime_id="validator-shadow-persistent-runtime-partial",
        scheduler_guard_report=scheduler_report,
        requested_cycle_count=3,
        completed_cycle_count=2,
        atomic_commit_count=1,
        partial_temp_artifact_count=1,
        graceful_shutdown=False,
    )
    partial_result = validate_shadow_observation_persistent_runtime_report(partial)
    if partial_result.status != "BLOCKED" or partial_result.blocker_code != "PARTIAL_WRITE_RECOVERY_REQUIRED":
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "persistent SHADOW runtime partial execution was not blocked",
            paths,
            partial_result.blocker_code or "PARTIAL_WRITE_RECOVERY_REQUIRED",
        )

    duplicate_commit_id = "A" * 64
    duplicate_cycle_identity = build_shadow_observation_persistent_runtime_report(
        runtime_id="validator-shadow-persistent-runtime-duplicate-cycle",
        scheduler_guard_report=scheduler_report,
        requested_cycle_count=3,
        completed_cycle_count=3,
        atomic_commit_count=3,
        cycle_commit_ids=[duplicate_commit_id, duplicate_commit_id, duplicate_commit_id],
    )
    duplicate_cycle_result = validate_shadow_observation_persistent_runtime_report(duplicate_cycle_identity)
    if duplicate_cycle_result.status != "BLOCKED" or duplicate_cycle_result.blocker_code != "DUPLICATE_WRITER_RISK":
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "persistent SHADOW runtime duplicate cycle identity was not blocked",
            paths,
            duplicate_cycle_result.blocker_code or "DUPLICATE_WRITER_RISK",
        )

    false_safe_cycle_summary = dict(duplicate_cycle_identity)
    false_safe_cycle_summary["duplicate_cycle_commit_count"] = 0
    false_safe_cycle_summary["cycle_identity_status"] = "PASS"
    false_safe_cycle_summary["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(false_safe_cycle_summary)
    false_safe_cycle_result = validate_shadow_observation_persistent_runtime_report(false_safe_cycle_summary)
    if false_safe_cycle_result.status != "BLOCKED" or false_safe_cycle_result.blocker_code != "DUPLICATE_WRITER_RISK":
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "persistent SHADOW runtime false-safe cycle identity summary drift was not blocked",
            paths,
            false_safe_cycle_result.blocker_code or "DUPLICATE_WRITER_RISK",
        )

    observed_duration = build_shadow_observation_persistent_runtime_report(
        runtime_id="validator-shadow-persistent-runtime-observed-duration",
        scheduler_guard_report=scheduler_report,
        requested_cycle_count=3,
        completed_cycle_count=3,
        atomic_commit_count=3,
        observed_runtime_seconds=90,
    )
    observed_duration_result = validate_shadow_observation_persistent_runtime_report(observed_duration)
    if (
        observed_duration_result.status != "BLOCKED"
        or observed_duration_result.blocker_code != "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
    ):
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "persistent SHADOW runtime observed duration claim was not blocked",
            paths,
            observed_duration_result.blocker_code or "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        )

    false_safe_duration = dict(runtime_report)
    false_safe_duration["runtime_duration_evidence_source"] = "OBSERVED_WALL_CLOCK"
    false_safe_duration["duration_evidence_role"] = "LONG_RUN_EVIDENCE"
    false_safe_duration["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(false_safe_duration)
    false_safe_duration_result = validate_shadow_observation_persistent_runtime_report(false_safe_duration)
    if (
        false_safe_duration_result.status != "BLOCKED"
        or false_safe_duration_result.blocker_code != "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
    ):
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "persistent SHADOW runtime false-safe duration evidence role was not blocked",
            paths,
            false_safe_duration_result.blocker_code or "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        )

    order_adapter = build_shadow_observation_persistent_runtime_report(
        runtime_id="validator-shadow-persistent-runtime-order-adapter",
        scheduler_guard_report=scheduler_report,
        order_adapter_called=True,
    )
    order_adapter_result = validate_shadow_observation_persistent_runtime_report(order_adapter)
    if order_adapter_result.status != "BLOCKED" or order_adapter_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "persistent SHADOW runtime order adapter attempt was not blocked",
            paths,
            order_adapter_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    live_mutation = dict(runtime_report)
    live_mutation["live_order_allowed"] = True
    live_mutation["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(live_mutation)
    live_mutation_result = validate_shadow_observation_persistent_runtime_report(live_mutation)
    if live_mutation_result.status != "BLOCKED" or live_mutation_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "persistent SHADOW runtime live flag mutation was not blocked",
            paths,
            live_mutation_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    false_long_run = dict(runtime_report)
    false_long_run["long_run_evidence_eligible"] = True
    false_long_run["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(false_long_run)
    false_long_run_result = validate_shadow_observation_persistent_runtime_report(false_long_run)
    if false_long_run_result.status != "BLOCKED" or false_long_run_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_persistent_runtime_validator",
            "persistent SHADOW runtime false long-run evidence claim was not blocked",
            paths,
            false_long_run_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    return pass_result(
        "shadow_observation_persistent_runtime_validator",
        "persistent SHADOW runtime stub is bounded, recovery-clean, heartbeat-visible, and live-blocked",
        paths,
    )


def shadow_observation_actual_runtime_blocker_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "shadow_observation_actual_runtime_blocker_report.schema.json"
    module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_actual_runtime_blocker.py"
    runtime_module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_persistent_runtime.py"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    test_path = ROOT / "tests" / "research" / "test_shadow_observation_actual_runtime_blocker.py"
    paths = [schema_path, module_path, runtime_module_path, state_path, test_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "shadow_observation_actual_runtime_blocker_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.shadow_observation_actual_runtime_blocker_report.v1":
        return fail_result(
            "shadow_observation_actual_runtime_blocker_validator",
            "shadow observation actual runtime blocker schema id mismatch",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if schema.get("additionalProperties") is not False:
        return fail_result(
            "shadow_observation_actual_runtime_blocker_validator",
            "shadow observation actual runtime blocker schema is not closed",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )

    observations: list[dict[str, Any]] = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="validator-shadow-actual-runtime-blocker-source",
            session_id=f"validator-shadow-actual-runtime-blocker-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"validator-shadow-actual-runtime-blocker-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"validator-shadow-actual-runtime-blocker-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream_report = build_shadow_observation_stream_report(
        stream_id="validator-shadow-actual-runtime-blocker-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    scheduler_report = build_shadow_observation_scheduler_guard_report(
        scheduler_id="validator-shadow-actual-runtime-blocker-scheduler",
        stream_report=stream_report,
        writer_id="validator-writer",
        active_writer_id="validator-writer",
    )
    runtime_report = build_shadow_observation_persistent_runtime_report(
        runtime_id="validator-shadow-actual-runtime-blocker-runtime",
        scheduler_guard_report=scheduler_report,
        requested_cycle_count=3,
        completed_cycle_count=3,
        max_cycle_count=10,
    )
    blocker_report = build_shadow_observation_actual_runtime_blocker_report(
        blocker_report_id="validator-shadow-actual-runtime-blocker-pass",
        runtime_report=runtime_report,
    )

    schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
    instance_schema = schema_for_instance(blocker_report, schema_bundle)
    if instance_schema is None:
        return fail_result(
            "shadow_observation_actual_runtime_blocker_validator",
            "shadow actual runtime blocker instance did not map to schema",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    instance_result = validate_instance_against_schema(blocker_report, instance_schema, schema_bundle)
    if instance_result.status != "PASS":
        return fail_result(
            "shadow_observation_actual_runtime_blocker_validator",
            f"shadow actual runtime blocker instance schema failed: {instance_result.errors[0]}",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    result = validate_shadow_observation_actual_runtime_blocker_report(blocker_report, runtime_report=runtime_report)
    if result.status != "PASS":
        return fail_result(
            "shadow_observation_actual_runtime_blocker_validator",
            f"valid shadow actual runtime blocker was not accepted: {result.message}",
            paths,
            result.blocker_code or "UNKNOWN_BLOCKED",
        )

    false_long_run = dict(blocker_report)
    false_long_run["long_run_evidence_present"] = True
    false_long_run["blocker_report_hash"] = shadow_observation_actual_runtime_blocker_hash(false_long_run)
    false_long_run_result = validate_shadow_observation_actual_runtime_blocker_report(false_long_run, runtime_report=runtime_report)
    if false_long_run_result.status != "BLOCKED" or false_long_run_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_actual_runtime_blocker_validator",
            "actual runtime blocker false long-run evidence claim was not blocked",
            paths,
            false_long_run_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    false_threshold = dict(blocker_report)
    false_threshold["minimum_evidence_window_met"] = True
    false_threshold["blocker_report_hash"] = shadow_observation_actual_runtime_blocker_hash(false_threshold)
    false_threshold_result = validate_shadow_observation_actual_runtime_blocker_report(false_threshold, runtime_report=runtime_report)
    if false_threshold_result.status != "BLOCKED" or false_threshold_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_actual_runtime_blocker_validator",
            "actual runtime blocker false threshold claim was not blocked",
            paths,
            false_threshold_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    live_mutation = dict(blocker_report)
    live_mutation["live_order_allowed"] = True
    live_mutation["blocker_report_hash"] = shadow_observation_actual_runtime_blocker_hash(live_mutation)
    live_mutation_result = validate_shadow_observation_actual_runtime_blocker_report(live_mutation, runtime_report=runtime_report)
    if live_mutation_result.status != "BLOCKED" or live_mutation_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_actual_runtime_blocker_validator",
            "actual runtime blocker live flag mutation was not blocked",
            paths,
            live_mutation_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    invalid_runtime = dict(runtime_report)
    invalid_runtime["live_order_allowed"] = True
    invalid_runtime["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(invalid_runtime)
    invalid_source_report = build_shadow_observation_actual_runtime_blocker_report(
        blocker_report_id="validator-shadow-actual-runtime-blocker-source-drift",
        runtime_report=invalid_runtime,
    )
    invalid_source_result = validate_shadow_observation_actual_runtime_blocker_report(
        invalid_source_report,
        runtime_report=invalid_runtime,
    )
    if invalid_source_result.status != "BLOCKED" or invalid_source_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_actual_runtime_blocker_validator",
            "actual runtime blocker did not block source runtime live drift",
            paths,
            invalid_source_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    return pass_result(
        "shadow_observation_actual_runtime_blocker_validator",
        "actual SHADOW runtime evidence is explicitly blocked until real long-run non-live execution evidence exists",
        paths,
    )


def shadow_observation_actual_runtime_harness_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "shadow_observation_actual_runtime_harness_report.schema.json"
    module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_actual_runtime_harness.py"
    blocker_module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_actual_runtime_blocker.py"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    test_path = ROOT / "tests" / "research" / "test_shadow_observation_actual_runtime_harness.py"
    paths = [schema_path, module_path, blocker_module_path, state_path, test_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "shadow_observation_actual_runtime_harness_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.shadow_observation_actual_runtime_harness_report.v1":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "shadow observation actual runtime harness schema id mismatch",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if schema.get("additionalProperties") is not False:
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "shadow observation actual runtime harness schema is not closed",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )

    report = build_shadow_observation_actual_runtime_harness_report(
        harness_id="validator-shadow-actual-runtime-harness",
        requested_cycle_count=3,
        completed_cycle_count=3,
        observations_per_cycle=2,
        measured_runtime_seconds=90,
        runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
        monotonic_timer_started=True,
        monotonic_timer_stopped=True,
        measured_runtime_seconds_verified=True,
    )
    schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
    instance_schema = schema_for_instance(report, schema_bundle)
    if instance_schema is None:
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "shadow actual runtime harness instance did not map to schema",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    instance_result = validate_instance_against_schema(report, instance_schema, schema_bundle)
    if instance_result.status != "PASS":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            f"shadow actual runtime harness instance schema failed: {instance_result.errors[0]}",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    result = validate_shadow_observation_actual_runtime_harness_report(report)
    if result.status != "PASS":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            f"valid shadow actual runtime harness was not accepted: {result.message}",
            paths,
            result.blocker_code or "UNKNOWN_BLOCKED",
        )

    false_long_run = dict(report)
    false_long_run["long_run_evidence_present"] = True
    false_long_run["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(false_long_run)
    false_long_run_result = validate_shadow_observation_actual_runtime_harness_report(false_long_run)
    if false_long_run_result.status != "BLOCKED" or false_long_run_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "actual runtime harness false long-run evidence claim was not blocked",
            paths,
            false_long_run_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    execution_summary_drift = dict(report)
    execution_summary_drift["actual_non_live_runtime_harness_executed"] = False
    execution_summary_drift["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(execution_summary_drift)
    execution_summary_result = validate_shadow_observation_actual_runtime_harness_report(execution_summary_drift)
    if execution_summary_result.status != "BLOCKED" or execution_summary_result.blocker_code != "MEASUREMENT_MISSING":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "actual runtime harness execution summary drift was not blocked",
            paths,
            execution_summary_result.blocker_code or "MEASUREMENT_MISSING",
        )

    unverified_measurement = build_shadow_observation_actual_runtime_harness_report(
        harness_id="validator-shadow-actual-runtime-unverified-measurement",
        requested_cycle_count=3,
        completed_cycle_count=3,
        observations_per_cycle=2,
        measured_runtime_seconds=90,
    )
    unverified_result = validate_shadow_observation_actual_runtime_harness_report(unverified_measurement)
    if unverified_result.status != "BLOCKED" or unverified_result.blocker_code != "MEASUREMENT_MISSING":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "actual runtime harness unverified runtime measurement source was not blocked",
            paths,
            unverified_result.blocker_code or "MEASUREMENT_MISSING",
        )

    live_mutation = dict(report)
    live_mutation["live_order_allowed"] = True
    live_mutation["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(live_mutation)
    live_mutation_result = validate_shadow_observation_actual_runtime_harness_report(live_mutation)
    if live_mutation_result.status != "BLOCKED" or live_mutation_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "actual runtime harness live flag mutation was not blocked",
            paths,
            live_mutation_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    credential_mutation = dict(report)
    credential_mutation["credential_access_attempted"] = True
    credential_mutation["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(credential_mutation)
    credential_result = validate_shadow_observation_actual_runtime_harness_report(credential_mutation)
    if credential_result.status != "BLOCKED" or credential_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "actual runtime harness credential attempt was not blocked",
            paths,
            credential_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    negative_runtime = build_shadow_observation_actual_runtime_harness_report(
        harness_id="validator-shadow-actual-runtime-negative-runtime",
        requested_cycle_count=3,
        completed_cycle_count=3,
        observations_per_cycle=2,
        measured_runtime_seconds=-1,
        runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
        monotonic_timer_started=True,
        monotonic_timer_stopped=True,
        measured_runtime_seconds_verified=True,
    )
    negative_runtime_result = validate_shadow_observation_actual_runtime_harness_report(negative_runtime)
    if negative_runtime_result.status != "BLOCKED" or negative_runtime_result.blocker_code != "DATA_QUALITY_INSUFFICIENT":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "actual runtime harness negative runtime measurement was not blocked",
            paths,
            negative_runtime_result.blocker_code or "DATA_QUALITY_INSUFFICIENT",
        )

    partial = build_shadow_observation_actual_runtime_harness_report(
        harness_id="validator-shadow-actual-runtime-harness-partial",
        requested_cycle_count=3,
        completed_cycle_count=2,
        runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
        monotonic_timer_started=True,
        monotonic_timer_stopped=True,
        measured_runtime_seconds_verified=True,
    )
    partial_result = validate_shadow_observation_actual_runtime_harness_report(partial)
    if partial_result.status != "BLOCKED" or partial_result.blocker_code != "PARTIAL_WRITE_RECOVERY_REQUIRED":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "actual runtime harness partial execution was not blocked",
            paths,
            partial_result.blocker_code or "PARTIAL_WRITE_RECOVERY_REQUIRED",
        )

    hash_drift = dict(report)
    hash_drift["source_runtime_report_hash"] = "0" * 64
    hash_drift["harness_report_hash"] = shadow_observation_actual_runtime_harness_hash(hash_drift)
    hash_result = validate_shadow_observation_actual_runtime_harness_report(hash_drift)
    if hash_result.status != "BLOCKED" or hash_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result(
            "shadow_observation_actual_runtime_harness_validator",
            "actual runtime harness source hash drift was not blocked",
            paths,
            hash_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )

    return pass_result(
        "shadow_observation_actual_runtime_harness_validator",
        "non-live PAPER/SHADOW harness runs short-window checks while long-run and live evidence remain blocked",
        paths,
    )


def shadow_observation_artifact_writer_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "shadow_observation_runtime_artifact_writer_report.schema.json"
    module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_artifact_writer.py"
    runtime_module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_persistent_runtime.py"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    test_path = ROOT / "tests" / "research" / "test_shadow_observation_artifact_writer.py"
    paths = [schema_path, module_path, runtime_module_path, state_path, test_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "shadow_observation_artifact_writer_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.shadow_observation_runtime_artifact_writer_report.v1":
        return fail_result(
            "shadow_observation_artifact_writer_validator",
            "shadow observation artifact writer schema id mismatch",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if schema.get("additionalProperties") is not False:
        return fail_result(
            "shadow_observation_artifact_writer_validator",
            "shadow observation artifact writer schema is not closed",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )

    observations: list[dict[str, Any]] = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="validator-shadow-artifact-writer-source",
            session_id=f"validator-shadow-artifact-writer-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"validator-shadow-artifact-writer-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"validator-shadow-artifact-writer-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream_report = build_shadow_observation_stream_report(
        stream_id="validator-shadow-artifact-writer-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    scheduler_report = build_shadow_observation_scheduler_guard_report(
        scheduler_id="validator-shadow-artifact-writer-scheduler",
        stream_report=stream_report,
        writer_id="validator-writer",
        active_writer_id="validator-writer",
    )
    runtime_report = build_shadow_observation_persistent_runtime_report(
        runtime_id="validator-shadow-artifact-writer-runtime",
        scheduler_guard_report=scheduler_report,
        requested_cycle_count=3,
        completed_cycle_count=3,
        max_cycle_count=10,
    )

    with TemporaryDirectory() as tmp:
        writer_report = write_shadow_observation_runtime_artifacts(
            root=Path(tmp),
            writer_id="validator-shadow-artifact-writer-pass",
            runtime_report=runtime_report,
        )
        schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
        instance_schema = schema_for_instance(writer_report, schema_bundle)
        if instance_schema is None:
            return fail_result(
                "shadow_observation_artifact_writer_validator",
                "shadow artifact writer instance did not map to schema",
                paths,
                "SCHEMA_IDENTITY_MISMATCH",
            )
        instance_result = validate_instance_against_schema(writer_report, instance_schema, schema_bundle)
        if instance_result.status != "PASS":
            return fail_result(
                "shadow_observation_artifact_writer_validator",
                f"shadow artifact writer instance schema failed: {instance_result.errors[0]}",
                paths,
                "SCHEMA_IDENTITY_MISMATCH",
            )
        result = validate_shadow_observation_artifact_writer_report(writer_report, runtime_report=runtime_report)
        if result.status != "PASS":
            return fail_result(
                "shadow_observation_artifact_writer_validator",
                f"valid shadow artifact writer was not accepted: {result.message}",
                paths,
                result.blocker_code or "UNKNOWN_BLOCKED",
            )

    invalid_runtime = dict(runtime_report)
    invalid_runtime["live_order_allowed"] = True
    invalid_runtime["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(invalid_runtime)
    with TemporaryDirectory() as tmp:
        blocked_writer = write_shadow_observation_runtime_artifacts(
            root=Path(tmp),
            writer_id="validator-shadow-artifact-writer-blocked",
            runtime_report=invalid_runtime,
        )
        blocked_result = validate_shadow_observation_artifact_writer_report(blocked_writer)
        if blocked_result.status != "BLOCKED" or blocked_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
            return fail_result(
                "shadow_observation_artifact_writer_validator",
                "writer did not block invalid runtime live flag drift",
                paths,
                blocked_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
            )

    live_mutation = dict(writer_report)
    live_mutation["live_order_allowed"] = True
    live_mutation["writer_report_hash"] = shadow_observation_artifact_writer_hash(live_mutation)
    live_mutation_result = validate_shadow_observation_artifact_writer_report(live_mutation, runtime_report=runtime_report)
    if live_mutation_result.status != "BLOCKED" or live_mutation_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_artifact_writer_validator",
            "writer report live flag mutation was not blocked",
            paths,
            live_mutation_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    long_run_mutation = dict(writer_report)
    long_run_mutation["long_run_evidence_eligible"] = True
    long_run_mutation["writer_report_hash"] = shadow_observation_artifact_writer_hash(long_run_mutation)
    long_run_result = validate_shadow_observation_artifact_writer_report(long_run_mutation, runtime_report=runtime_report)
    if long_run_result.status != "BLOCKED" or long_run_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_artifact_writer_validator",
            "writer report false long-run claim was not blocked",
            paths,
            long_run_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    partial = dict(writer_report)
    partial["temp_artifact_count_after"] = 1
    partial["partial_write_detected"] = True
    partial["primary_blocker_code"] = "PARTIAL_WRITE_RECOVERY_REQUIRED"
    partial["writer_report_hash"] = shadow_observation_artifact_writer_hash(partial)
    partial_result = validate_shadow_observation_artifact_writer_report(partial, runtime_report=runtime_report)
    if partial_result.status != "BLOCKED" or partial_result.blocker_code != "PARTIAL_WRITE_RECOVERY_REQUIRED":
        return fail_result(
            "shadow_observation_artifact_writer_validator",
            "writer report partial write drift was not blocked",
            paths,
            partial_result.blocker_code or "PARTIAL_WRITE_RECOVERY_REQUIRED",
        )

    path_mutation = dict(writer_report)
    path_mutation["artifact_path"] = path_mutation["artifact_path"].replace("/shadow/", "/live/")
    path_mutation["writer_report_hash"] = shadow_observation_artifact_writer_hash(path_mutation)
    path_result = validate_shadow_observation_artifact_writer_report(path_mutation, runtime_report=runtime_report)
    if path_result.status != "BLOCKED" or path_result.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        return fail_result(
            "shadow_observation_artifact_writer_validator",
            "writer report live path mutation was not blocked",
            paths,
            path_result.blocker_code or "SNAPSHOT_SCOPE_MISMATCH",
        )

    return pass_result(
        "shadow_observation_artifact_writer_validator",
        "SHADOW runtime artifact writer is atomic, display-only, stub-only, and live-blocked",
        paths,
    )


def shadow_observation_runtime_orchestration_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "shadow_observation_runtime_orchestration_report.schema.json"
    module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_runtime_orchestration.py"
    persistent_module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_persistent_runtime.py"
    harness_module_path = ROOT / "trader1" / "research" / "shadow" / "shadow_observation_actual_runtime_harness.py"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    test_path = ROOT / "tests" / "research" / "test_shadow_observation_runtime_orchestration.py"
    paths = [schema_path, module_path, persistent_module_path, harness_module_path, state_path, test_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "shadow_observation_runtime_orchestration_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    schema = load_json(schema_path)
    if schema.get("$id") != "trader1.shadow_observation_runtime_orchestration_report.v1":
        return fail_result(
            "shadow_observation_runtime_orchestration_validator",
            "shadow observation runtime orchestration schema id mismatch",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if schema.get("additionalProperties") is not False:
        return fail_result(
            "shadow_observation_runtime_orchestration_validator",
            "shadow observation runtime orchestration schema is not closed",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )

    observations: list[dict[str, Any]] = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="validator-shadow-runtime-orchestration-source",
            session_id=f"validator-shadow-runtime-orchestration-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"validator-shadow-runtime-orchestration-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"validator-shadow-runtime-orchestration-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream_report = build_shadow_observation_stream_report(
        stream_id="validator-shadow-runtime-orchestration-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    scheduler_report = build_shadow_observation_scheduler_guard_report(
        scheduler_id="validator-shadow-runtime-orchestration-scheduler",
        stream_report=stream_report,
        writer_id="validator-shadow-runtime-orchestration-writer",
        active_writer_id="validator-shadow-runtime-orchestration-writer",
    )
    persistent_report = build_shadow_observation_persistent_runtime_report(
        runtime_id="validator-shadow-runtime-orchestration-persistent",
        scheduler_guard_report=scheduler_report,
        requested_cycle_count=3,
        completed_cycle_count=3,
        max_cycle_count=20,
    )
    harness_report = build_shadow_observation_actual_runtime_harness_report(
        harness_id="validator-shadow-runtime-orchestration-harness",
        requested_cycle_count=3,
        completed_cycle_count=3,
        observations_per_cycle=2,
        measured_runtime_seconds=90,
        runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
        monotonic_timer_started=True,
        monotonic_timer_stopped=True,
        measured_runtime_seconds_verified=True,
        source_runtime_report=persistent_report,
    )
    orchestration = build_shadow_observation_runtime_orchestration_report(
        orchestration_id="validator-shadow-runtime-orchestration",
        persistent_runtime_report=persistent_report,
        actual_runtime_harness_report=harness_report,
    )
    schema_bundle = load_schema_bundle(ROOT / "contracts" / "schema")
    instance_schema = schema_for_instance(orchestration, schema_bundle)
    if instance_schema is None:
        return fail_result(
            "shadow_observation_runtime_orchestration_validator",
            "shadow runtime orchestration instance did not map to schema",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    instance_result = validate_instance_against_schema(orchestration, instance_schema, schema_bundle)
    if instance_result.status != "PASS":
        return fail_result(
            "shadow_observation_runtime_orchestration_validator",
            f"shadow runtime orchestration instance schema failed: {instance_result.errors[0]}",
            paths,
            "SCHEMA_IDENTITY_MISMATCH",
        )
    result = validate_shadow_observation_runtime_orchestration_report(orchestration)
    if result.status != "PASS":
        return fail_result(
            "shadow_observation_runtime_orchestration_validator",
            f"valid blocked shadow runtime orchestration was not accepted: {result.message}",
            paths,
            result.blocker_code or "UNKNOWN_BLOCKED",
        )

    mismatched_persistent = build_shadow_observation_persistent_runtime_report(
        runtime_id="validator-shadow-runtime-orchestration-mismatched-persistent",
        scheduler_guard_report=scheduler_report,
        requested_cycle_count=2,
        completed_cycle_count=2,
        max_cycle_count=20,
    )
    mismatch_report = build_shadow_observation_runtime_orchestration_report(
        orchestration_id="validator-shadow-runtime-orchestration-mismatch",
        persistent_runtime_report=mismatched_persistent,
        actual_runtime_harness_report=harness_report,
    )
    mismatch_result = validate_shadow_observation_runtime_orchestration_report(mismatch_report)
    if mismatch_result.status != "BLOCKED" or mismatch_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return fail_result(
            "shadow_observation_runtime_orchestration_validator",
            "runtime orchestration source pairing mismatch was not blocked",
            paths,
            mismatch_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
        )

    long_run_mutation = dict(orchestration)
    long_run_mutation["actual_long_run_runtime_present"] = True
    long_run_mutation["orchestration_report_hash"] = shadow_observation_runtime_orchestration_hash(long_run_mutation)
    long_run_result = validate_shadow_observation_runtime_orchestration_report(long_run_mutation)
    if long_run_result.status != "BLOCKED" or long_run_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_runtime_orchestration_validator",
            "runtime orchestration false long-run claim was not blocked",
            paths,
            long_run_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    live_mutation = dict(orchestration)
    live_mutation["live_order_allowed"] = True
    live_mutation["orchestration_report_hash"] = shadow_observation_runtime_orchestration_hash(live_mutation)
    live_result = validate_shadow_observation_runtime_orchestration_report(live_mutation)
    if live_result.status != "BLOCKED" or live_result.blocker_code != "LIVE_FINAL_GUARD_FAILED":
        return fail_result(
            "shadow_observation_runtime_orchestration_validator",
            "runtime orchestration live flag mutation was not blocked",
            paths,
            live_result.blocker_code or "LIVE_FINAL_GUARD_FAILED",
        )

    optimizer_mutation = dict(orchestration)
    optimizer_mutation["optimizer_ranking_action"] = "ALLOW_RANKING"
    optimizer_mutation["orchestration_report_hash"] = shadow_observation_runtime_orchestration_hash(optimizer_mutation)
    optimizer_result = validate_shadow_observation_runtime_orchestration_report(optimizer_mutation)
    if optimizer_result.status != "BLOCKED" or optimizer_result.blocker_code != "OPTIMIZER_DIRECT_LIVE_FORBIDDEN":
        return fail_result(
            "shadow_observation_runtime_orchestration_validator",
            "runtime orchestration optimizer ranking mutation was not blocked",
            paths,
            optimizer_result.blocker_code or "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    return pass_result(
        "shadow_observation_runtime_orchestration_validator",
        "SHADOW runtime orchestration blocks long-run evidence, optimizer ranking, live orders, and scale-up until exact evidence exists",
        paths,
    )


def failure_analysis_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "failure_analysis_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "failure_analysis_pass.json"
    unknown_root_path = fixture_dir / "failure_analysis_unknown_root_live_affecting_fail.json"
    repeated_path = fixture_dir / "failure_analysis_repeated_unblocked_fail.json"
    live_flag_path = fixture_dir / "failure_analysis_live_flag_fail.json"
    paths = [schema_path, pass_path, unknown_root_path, repeated_path, live_flag_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "failure_analysis_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _failure_analysis_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "failure_analysis_validator",
            f"PASS fixture failed failure analysis validation: {pass_errors[0]}",
            paths,
            "FAILURE_ANALYSIS_MISSING",
        )

    negative_expectations = {
        unknown_root_path: "UNKNOWN_ROOT_CAUSE in live-affecting failure must block live order",
        repeated_path: "repeated same-root-cause failure must block ranking",
        live_flag_path: "expected const False",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _failure_analysis_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "failure_analysis_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "FAILURE_ANALYSIS_MISSING",
            )

    return pass_result(
        "failure_analysis_validator",
        "failure analysis requires root-cause status, repeated-failure blocking, append-only memory write status, and false live flags",
        paths,
    )


def realized_slippage_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "optimizer_feedback_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "optimizer_feedback_pass.json"
    slippage_fail_path = fixture_dir / "optimizer_feedback_slippage_divergent_fail.json"
    paths = [schema_path, pass_path, slippage_fail_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "realized_slippage_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_report = load_json(pass_path)
    pass_errors = _optimizer_feedback_errors(pass_report)
    if pass_errors:
        return fail_result(
            "realized_slippage_validator",
            f"PASS fixture failed realized slippage validation: {pass_errors[0]}",
            paths,
            "EXECUTION_FEEDBACK_DIVERGENT",
        )

    expected_deviation = max(0.0, float(pass_report["realized_slippage_bps"]) - float(pass_report["expected_slippage_bps"]))
    if abs(float(pass_report["slippage_deviation_bps"]) - expected_deviation) > 0.000001:
        return fail_result(
            "realized_slippage_validator",
            "PASS fixture slippage_deviation_bps does not match positive realized-minus-expected slippage",
            paths,
            "EXECUTION_FEEDBACK_DIVERGENT",
        )

    slippage_errors = _optimizer_feedback_errors(load_json(slippage_fail_path))
    if not any("slippage_deviation_bps above max_allowed_slippage_deviation_bps" in error for error in slippage_errors):
        return fail_result(
            "realized_slippage_validator",
            "slippage divergence fixture was not rejected",
            paths,
            "EXECUTION_FEEDBACK_DIVERGENT",
        )

    tampered_negative_cost = json.loads(json.dumps(pass_report))
    tampered_negative_cost["realized_slippage_bps"] = float(tampered_negative_cost["expected_slippage_bps"]) - 1.0
    tampered_negative_cost["slippage_deviation_bps"] = 1.0
    tampered_negative_cost["feedback_hash"] = optimizer_feedback_hash(tampered_negative_cost)
    if "slippage_deviation_bps must equal positive realized-minus-expected cost difference" not in _optimizer_feedback_errors(
        tampered_negative_cost
    ):
        return fail_result(
            "realized_slippage_validator",
            "negative realized-minus-expected slippage was not normalized to zero deviation",
            paths,
            "EXECUTION_FEEDBACK_DIVERGENT",
        )

    dependency = execution_feedback_loop_validator().as_dict()
    if dependency["status"] != "PASS":
        return blocked_result(
            "realized_slippage_validator",
            f"execution feedback dependency did not pass: {dependency['status']}",
            paths,
            "EXECUTION_FEEDBACK_DIVERGENT",
        )

    return pass_result(
        "realized_slippage_validator",
        "realized slippage is bounded against expected slippage, divergent slippage blocks ranking, and live flags remain false",
        paths,
    )


def order_failure_taxonomy_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "failure_analysis_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "failure_analysis_pass.json"
    unknown_root_path = fixture_dir / "failure_analysis_unknown_root_live_affecting_fail.json"
    repeated_path = fixture_dir / "failure_analysis_repeated_unblocked_fail.json"
    paths = [schema_path, pass_path, unknown_root_path, repeated_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "order_failure_taxonomy_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_report = load_json(pass_path)
    pass_errors = _order_failure_taxonomy_errors(pass_report)
    if pass_errors:
        return fail_result(
            "order_failure_taxonomy_validator",
            f"PASS fixture failed order failure taxonomy validation: {pass_errors[0]}",
            paths,
            "FAILURE_ANALYSIS_MISSING",
        )

    unknown_execution = json.loads(json.dumps(pass_report))
    unknown_execution["primary_root_cause_code"] = "UNKNOWN_ROOT_CAUSE"
    unknown_execution["root_cause_status"] = "UNKNOWN"
    unknown_execution["failure_status"] = "BLOCKED_UNKNOWN_ROOT_CAUSE"
    unknown_execution["recommended_response"] = "REQUIRE_MORE_EVIDENCE"
    unknown_execution["blockers"] = [
        {
            "code": "ROOT_CAUSE_UNKNOWN_LIVE_AFFECTING",
            "severity": "HIGH",
            "message": "Known execution feedback evidence cannot be left as unknown root cause.",
        }
    ]
    unknown_errors = _order_failure_taxonomy_errors(unknown_execution)
    if not any("known execution failure evidence cannot remain outside execution failure taxonomy" in error for error in unknown_errors):
        return fail_result(
            "order_failure_taxonomy_validator",
            "known execution feedback evidence left as UNKNOWN_ROOT_CAUSE was not rejected",
            paths,
            "ROOT_CAUSE_UNKNOWN_LIVE_AFFECTING",
        )

    unblocked_execution = json.loads(json.dumps(pass_report))
    unblocked_execution["blocks_promotion"] = False
    unblocked_errors = _order_failure_taxonomy_errors(unblocked_execution)
    if not any("known execution failure evidence must block promotion" in error for error in unblocked_errors):
        return fail_result(
            "order_failure_taxonomy_validator",
            "known execution feedback failure without promotion block was not rejected",
            paths,
            "FAILURE_ANALYSIS_MISSING",
        )

    missing_blocker = json.loads(json.dumps(pass_report))
    missing_blocker["blockers"] = []
    missing_blocker_errors = _order_failure_taxonomy_errors(missing_blocker)
    if not any(
        "SLIPPAGE_DIVERGENCE failure must carry EXECUTION_FEEDBACK_DIVERGENT blocker" in error
        or "blocking failure analysis must carry explicit blocker evidence" in error
        for error in missing_blocker_errors
    ):
        return fail_result(
            "order_failure_taxonomy_validator",
            "slippage taxonomy without execution feedback blocker was not rejected",
            paths,
            "FAILURE_ANALYSIS_MISSING",
        )

    dependency = failure_analysis_validator().as_dict()
    if dependency["status"] != "PASS":
        return blocked_result(
            "order_failure_taxonomy_validator",
            f"failure analysis dependency did not pass: {dependency['status']}",
            paths,
            "FAILURE_ANALYSIS_MISSING",
        )

    return pass_result(
        "order_failure_taxonomy_validator",
        "order failure taxonomy maps execution/slippage failures to explicit root causes, blockers, memory writes, and blocked promotion/live state",
        paths,
    )


def _model_drift_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    if schema is None:
        return ["model drift report schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "active_snapshot_mutation_allowed",
        "optimizer_winner_live_config_allowed",
        "paper_winner_live_config_allowed",
        "model_promotion_allowed",
        "scale_up_recommendation_allowed",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"model drift report has forbidden true field: {field}")

    if report.get("mode") == "LIVE":
        errors.append("model drift report mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("model drift report source_modes must not include LIVE")

    warning = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning or "live orders blocked" not in warning:
        errors.append("model drift operator_warning must say not live_ready and live orders blocked")

    blockers = report.get("blockers", [])
    blocker_codes = {item.get("code") for item in blockers if isinstance(item, dict)}
    data_status = report.get("data_freshness_status")
    data_age = float(report.get("data_age_seconds", 0))
    max_data_age = float(report.get("max_data_age_seconds", 0))
    drift_status = report.get("drift_status")
    convergence_claim_after = report.get("convergence_claim_after")

    if data_status != "FRESH" or data_age > max_data_age:
        if drift_status == "NO_DRIFT":
            errors.append("NO_DRIFT requires fresh model drift input within max_data_age_seconds")
        if convergence_claim_after in {"ROBUSTLY_IMPROVING", "WRITER_INPUT_ELIGIBLE"}:
            errors.append("stale or missing model drift input cannot keep robust convergence claim")
        if not blockers:
            errors.append("stale or missing model drift input requires blockers")

    min_required = int(report.get("min_required_sample_count", 0))
    if drift_status == "NO_DRIFT":
        if int(report.get("baseline_sample_count", 0)) < min_required:
            errors.append("NO_DRIFT requires baseline_sample_count >= min_required_sample_count")
        if int(report.get("evaluation_sample_count", 0)) < min_required:
            errors.append("NO_DRIFT requires evaluation_sample_count >= min_required_sample_count")
        if float(report.get("drift_score", 0)) > float(report.get("max_allowed_drift_score", 0)):
            errors.append("NO_DRIFT requires drift_score <= max_allowed_drift_score")

    if drift_status in {"DRIFT_SUSPECTED", "DRIFT_DETECTED", "BLOCKED"}:
        if report.get("blocks_promotion") is not True:
            errors.append(f"{drift_status} requires blocks_promotion=true")
        if convergence_claim_after not in {"BLOCKED", "NO_CLAIM"}:
            errors.append(f"{drift_status} cannot keep convergence_claim_after={convergence_claim_after}")
        if "MODEL_DRIFT_DETECTED" not in blocker_codes and "CONVERGENCE_CLAIM_UNVERIFIED" not in blocker_codes:
            errors.append(f"{drift_status} requires MODEL_DRIFT_DETECTED or CONVERGENCE_CLAIM_UNVERIFIED blocker")

    for field in ("oos_status", "walk_forward_status", "bootstrap_status"):
        if report.get(field) != "PASS" and convergence_claim_after in {"ROBUSTLY_IMPROVING", "WRITER_INPUT_ELIGIBLE"}:
            errors.append(f"{field} must be PASS before robust or writer-input convergence claim")

    if convergence_claim_after == "WRITER_INPUT_ELIGIBLE":
        errors.append("model drift report cannot create LIVE_READY writer input eligibility in MVP-4")
    if drift_status == "NO_DRIFT" and blockers:
        errors.append("NO_DRIFT model drift report must not carry blockers")
    return errors


def model_drift_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "model_drift_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "model_drift_pass.json"
    live_flag_fail_path = fixture_dir / "model_drift_live_flag_fail.json"
    detected_claim_fail_path = fixture_dir / "model_drift_detected_claim_fail.json"
    suspected_unblocked_fail_path = fixture_dir / "model_drift_suspected_unblocked_fail.json"
    missing_baseline_fail_path = fixture_dir / "model_drift_missing_baseline_fail.json"
    stale_input_fail_path = fixture_dir / "model_drift_stale_input_fail.json"
    scale_up_fail_path = fixture_dir / "model_drift_scale_up_fail.json"
    paths = [
        schema_path,
        pass_path,
        live_flag_fail_path,
        detected_claim_fail_path,
        suspected_unblocked_fail_path,
        missing_baseline_fail_path,
        stale_input_fail_path,
        scale_up_fail_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "model_drift_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _model_drift_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "model_drift_validator",
            f"PASS fixture failed model drift validation: {pass_errors[0]}",
            paths,
            "MODEL_DRIFT_DETECTED",
        )

    negative_expectations = {
        live_flag_fail_path: "expected const False",
        detected_claim_fail_path: "DRIFT_DETECTED cannot keep convergence_claim_after=ROBUSTLY_IMPROVING",
        suspected_unblocked_fail_path: "DRIFT_SUSPECTED requires blocks_promotion=true",
        missing_baseline_fail_path: "NO_DRIFT requires baseline_sample_count >= min_required_sample_count",
        stale_input_fail_path: "stale or missing model drift input requires blockers",
        scale_up_fail_path: "expected const False",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _model_drift_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "model_drift_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "MODEL_DRIFT_DETECTED",
            )

    return pass_result(
        "model_drift_validator",
        "model drift report requires fresh scoped evidence, OOS/walk-forward/bootstrap PASS for strong claims, drift blocking, and false live/scale flags",
        paths,
    )


EXPLORATION_POLICY_DEPENDENCY_FIELDS = (
    "ranking_stability_validator_status",
    "optimizer_resource_budget_validator_status",
    "overfit_diagnostic_validator_status",
    "convergence_assessment_validator_status",
    "exploration_resource_validator_status",
    "model_drift_validator_status",
)
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
PARAMETER_NARROWING_DEPENDENCY_FIELDS = (
    "candidate_scorecard_validator_status",
    "optimizer_run_report_validator_status",
    "optimizer_recommendation_validator_status",
    "exploration_exploitation_policy_validator_status",
    "overfit_diagnostic_validator_status",
    "execution_feedback_loop_validator_status",
    "live_final_guard_validator_status",
)
PARAMETER_NARROWING_REQUIRED_SOURCE_ROLES = {
    "PAPER_SHADOW_EVIDENCE",
    "CANDIDATE_SCORECARD",
    "OPTIMIZER_RUN",
    "OPTIMIZER_RECOMMENDATION",
}


def _exploration_exploitation_policy_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    if schema is None:
        return ["exploration/exploitation policy schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "active_snapshot_mutation_allowed",
        "optimizer_winner_live_config_allowed",
        "paper_winner_live_config_allowed",
        "order_submission_allowed",
        "exchange_account_call_allowed",
        "scale_up_recommendation_allowed",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"exploration/exploitation policy has forbidden true field: {field}")

    if report.get("mode") == "LIVE":
        errors.append("exploration/exploitation policy mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("exploration/exploitation policy source_modes must not include LIVE")

    warning = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning or "live orders blocked" not in warning or (
        "scale-up blocked" not in warning and "scale up blocked" not in warning
    ):
        errors.append("exploration/exploitation policy warning must state not LIVE_READY, live orders blocked, and scale-up blocked")

    dependency_statuses = [report.get(field) for field in EXPLORATION_POLICY_DEPENDENCY_FIELDS]
    pass_count = sum(1 for status in dependency_statuses if status == "PASS")
    if report.get("dependency_pass_count") != pass_count:
        errors.append("dependency_pass_count must equal actual PASS dependency status count")
    if report.get("required_dependency_count") != len(EXPLORATION_POLICY_DEPENDENCY_FIELDS):
        errors.append("required_dependency_count must equal exploration policy dependency field count")

    dependency_summary_status = report.get("dependency_summary_status")
    non_pass_dependency = any(status != "PASS" for status in dependency_statuses)
    exploitation_allowed = report.get("exploitation_allowed_for_paper_ranking") is True
    transition_decision = report.get("transition_decision")
    policy_status = report.get("policy_status")
    recommendation_scope = report.get("recommendation_scope")
    blockers = report.get("blockers", [])

    if non_pass_dependency:
        if dependency_summary_status == "PASS":
            errors.append("dependency_summary_status cannot be PASS while a dependency is not PASS")
        if exploitation_allowed:
            errors.append("non-PASS dependency cannot allow exploitation for paper ranking")
        if transition_decision == "LIMITED_EXPLOITATION_REVIEW":
            errors.append("non-PASS dependency cannot allow LIMITED_EXPLOITATION_REVIEW")
        if policy_status == "PAPER_RANKING_REVIEW_ELIGIBLE":
            errors.append("non-PASS dependency cannot make policy PAPER_RANKING_REVIEW_ELIGIBLE")
        if report.get("blocks_promotion") is not True:
            errors.append("non-PASS dependency requires blocks_promotion=true")
        if not blockers:
            errors.append("non-PASS dependency requires blockers")

    candidate_count = int(report.get("candidate_count", 0))
    candidate_budget = int(report.get("exploration_candidate_budget", 0))
    if candidate_count > candidate_budget:
        if report.get("candidate_budget_status") != "BLOCKED":
            errors.append("candidate_count exceeds exploration_candidate_budget and must be BLOCKED")
        if transition_decision != "BLOCK_TRANSITION":
            errors.append("candidate budget breach must block transition")
        if report.get("blocks_promotion") is not True:
            errors.append("candidate budget breach requires blocks_promotion=true")
    elif report.get("candidate_budget_status") == "PASS" and candidate_count > candidate_budget:
        errors.append("candidate budget PASS is invalid when candidate_count exceeds budget")

    exploration_rate = float(report.get("exploration_rate_pct", 0))
    exploitation_rate = float(report.get("exploitation_rate_pct", 0))
    if abs((exploration_rate + exploitation_rate) - 100.0) > 0.0001:
        errors.append("exploration_rate_pct and exploitation_rate_pct must total 100")
    if exploration_rate < float(report.get("min_exploration_rate_pct", 0)):
        errors.append("exploration_rate_pct must not fall below min_exploration_rate_pct")
    if exploitation_rate > float(report.get("max_exploitation_rate_pct", 100)):
        errors.append("exploitation_rate_pct must not exceed max_exploitation_rate_pct")

    if exploitation_allowed:
        if policy_status != "PAPER_RANKING_REVIEW_ELIGIBLE":
            errors.append("paper ranking exploitation requires PAPER_RANKING_REVIEW_ELIGIBLE policy")
        if recommendation_scope != "PAPER_RANKING_REVIEW_ONLY":
            errors.append("paper ranking exploitation requires PAPER_RANKING_REVIEW_ONLY scope")
        if not report.get("exploitation_candidate_id"):
            errors.append("paper ranking exploitation requires exploitation_candidate_id")
        if report.get("blocks_promotion") is True:
            errors.append("paper ranking exploitation cannot be marked blocks_promotion=true")
    else:
        if recommendation_scope == "PAPER_RANKING_REVIEW_ONLY" or transition_decision == "LIMITED_EXPLOITATION_REVIEW":
            errors.append("paper ranking review scope cannot be shown when exploitation is not allowed")

    if report.get("objective_basis") == "BLOCKED_NO_VALID_OBJECTIVE":
        if not blockers:
            errors.append("blocked objective requires blockers")
        if transition_decision != "BLOCK_TRANSITION":
            errors.append("blocked objective must block transition")

    return errors


def _exploration_to_exploitation_errors(report: dict[str, Any]) -> list[str]:
    errors = _exploration_exploitation_policy_errors(report)
    transition_decision = report.get("transition_decision")
    exploitation_allowed = report.get("exploitation_allowed_for_paper_ranking") is True
    limited_transition = transition_decision == "LIMITED_EXPLOITATION_REVIEW" or exploitation_allowed

    if not limited_transition:
        return errors

    if report.get("controller_state") != "EXPLOITING_PAPER_ONLY":
        errors.append("limited exploitation transition requires controller_state=EXPLOITING_PAPER_ONLY")
    if report.get("policy_status") != "PAPER_RANKING_REVIEW_ELIGIBLE":
        errors.append("limited exploitation transition requires PAPER_RANKING_REVIEW_ELIGIBLE policy")
    if report.get("recommendation_scope") != "PAPER_RANKING_REVIEW_ONLY":
        errors.append("limited exploitation transition requires PAPER_RANKING_REVIEW_ONLY scope")
    if report.get("objective_basis") != "NET_EV_AFTER_COST":
        errors.append("limited exploitation transition requires NET_EV_AFTER_COST objective")

    source_modes = set(report.get("source_modes", []))
    if not {"PAPER", "SHADOW"}.issubset(source_modes):
        errors.append("limited exploitation transition requires both PAPER and SHADOW evidence source modes")

    dependency_statuses = [report.get(field) for field in EXPLORATION_POLICY_DEPENDENCY_FIELDS]
    if report.get("dependency_summary_status") != "PASS" or any(status != "PASS" for status in dependency_statuses):
        errors.append("limited exploitation transition requires all dependencies PASS")
    if report.get("candidate_budget_status") != "PASS":
        errors.append("limited exploitation transition requires candidate_budget_status=PASS")
    if int(report.get("cooldown_cycles_remaining", 0)) != 0:
        errors.append("limited exploitation transition requires cooldown_cycles_remaining=0")
    if float(report.get("min_exploration_rate_pct", 0)) <= 0:
        errors.append("limited exploitation transition requires positive min_exploration_rate_pct")
    if not report.get("exploitation_candidate_id"):
        errors.append("limited exploitation transition requires exploitation_candidate_id")

    if report.get("blockers"):
        errors.append("limited exploitation transition cannot carry blockers")
    if report.get("blocks_promotion") is True:
        errors.append("limited exploitation transition cannot claim paper ranking review while blocks_promotion=true")

    return errors


def _candidate_cooldown_errors(report: dict[str, Any]) -> list[str]:
    errors = _exploration_exploitation_policy_errors(report)
    cooldown = int(report.get("cooldown_cycles_remaining", 0))
    blocker_codes = {blocker.get("code") for blocker in report.get("blockers", [])}

    if cooldown <= 0:
        if "COOLDOWN" in blocker_codes:
            errors.append("cooldown_cycles_remaining=0 cannot carry COOLDOWN blocker")
        return errors

    if report.get("transition_decision") != "BLOCK_TRANSITION":
        errors.append("candidate cooldown requires transition_decision=BLOCK_TRANSITION")
    if report.get("recommendation_scope") != "BLOCKED":
        errors.append("candidate cooldown requires recommendation_scope=BLOCKED")
    if report.get("policy_status") != "BLOCKED":
        errors.append("candidate cooldown requires policy_status=BLOCKED")
    if report.get("controller_state") != "BLOCKED":
        errors.append("candidate cooldown requires controller_state=BLOCKED")
    if report.get("policy_scope") != "RESEARCH_BLOCKED":
        errors.append("candidate cooldown requires policy_scope=RESEARCH_BLOCKED")
    if report.get("exploitation_allowed_for_paper_ranking") is True:
        errors.append("candidate cooldown forbids exploitation_allowed_for_paper_ranking=true")
    if report.get("exploitation_candidate_id") is not None:
        errors.append("candidate cooldown requires exploitation_candidate_id=null")
    if report.get("blocks_promotion") is not True:
        errors.append("candidate cooldown requires blocks_promotion=true")
    if "COOLDOWN" not in blocker_codes:
        errors.append("candidate cooldown requires COOLDOWN blocker")
    if report.get("status") == "PASS":
        errors.append("candidate cooldown cannot expose status=PASS")

    return errors


def exploration_exploitation_policy_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "exploration_exploitation_policy.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "exploration_exploitation_policy_pass.json"
    dependency_untested_path = fixture_dir / "exploration_exploitation_policy_dependency_untested_fail.json"
    budget_exceeded_path = fixture_dir / "exploration_exploitation_policy_budget_exceeded_fail.json"
    live_flag_path = fixture_dir / "exploration_exploitation_policy_live_flag_fail.json"
    live_source_path = fixture_dir / "exploration_exploitation_policy_live_source_fail.json"
    warning_path = fixture_dir / "exploration_exploitation_policy_warning_fail.json"
    paths = [
        schema_path,
        pass_path,
        dependency_untested_path,
        budget_exceeded_path,
        live_flag_path,
        live_source_path,
        warning_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "exploration_exploitation_policy_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _exploration_exploitation_policy_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "exploration_exploitation_policy_validator",
            f"PASS fixture failed exploration/exploitation policy validation: {pass_errors[0]}",
            paths,
            "EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED",
        )

    negative_expectations = {
        dependency_untested_path: "non-PASS dependency cannot allow exploitation for paper ranking",
        budget_exceeded_path: "candidate_count exceeds exploration_candidate_budget",
        live_flag_path: "expected const False",
        live_source_path: "LIVE",
        warning_path: "warning must state not LIVE_READY",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _exploration_exploitation_policy_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "exploration_exploitation_policy_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED",
            )

    return pass_result(
        "exploration_exploitation_policy_validator",
        "exploration/exploitation policy is dependency-gated, budget-bounded, PAPER/SHADOW-only, and cannot create live, writer, order, or scale-up permission",
        paths,
    )


def exploration_to_exploitation_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "exploration_exploitation_policy.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "exploration_exploitation_policy_pass.json"
    cooldown_path = fixture_dir / "exploration_to_exploitation_cooldown_fail.json"
    missing_shadow_path = fixture_dir / "exploration_to_exploitation_missing_shadow_fail.json"
    zero_floor_path = fixture_dir / "exploration_to_exploitation_zero_exploration_floor_fail.json"
    blocker_path = fixture_dir / "exploration_to_exploitation_blocker_conflict_fail.json"
    controller_path = fixture_dir / "exploration_to_exploitation_controller_fail.json"
    paths = [
        schema_path,
        pass_path,
        cooldown_path,
        missing_shadow_path,
        zero_floor_path,
        blocker_path,
        controller_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "exploration_to_exploitation_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _exploration_to_exploitation_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "exploration_to_exploitation_validator",
            f"PASS fixture failed exploration-to-exploitation validation: {pass_errors[0]}",
            paths,
            "EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED",
        )

    negative_expectations = {
        cooldown_path: "cooldown_cycles_remaining=0",
        missing_shadow_path: "requires both PAPER and SHADOW evidence source modes",
        zero_floor_path: "positive min_exploration_rate_pct",
        blocker_path: "cannot carry blockers",
        controller_path: "controller_state=EXPLOITING_PAPER_ONLY",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _exploration_to_exploitation_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "exploration_to_exploitation_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED",
            )

    dependency = exploration_exploitation_policy_validator().as_dict()
    if dependency["status"] != "PASS":
        return blocked_result(
            "exploration_to_exploitation_validator",
            f"exploration/exploitation policy dependency did not pass: {dependency['status']}",
            paths,
            "EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED",
        )

    return pass_result(
        "exploration_to_exploitation_validator",
        "exploration-to-exploitation transition is cooldown-free, PAPER/SHADOW-evidenced, net-EV-only, keeps exploration floor, and cannot create live, order, or scale-up permission",
        paths,
    )


def candidate_cooldown_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "exploration_exploitation_policy.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "exploration_exploitation_policy_pass.json"
    blocked_pass_path = fixture_dir / "candidate_cooldown_blocked_pass.json"
    bypass_path = fixture_dir / "candidate_cooldown_bypass_fail.json"
    missing_blocker_path = fixture_dir / "candidate_cooldown_missing_blocker_fail.json"
    stale_blocker_path = fixture_dir / "candidate_cooldown_stale_blocker_fail.json"
    false_pass_status_path = fixture_dir / "candidate_cooldown_false_pass_status_fail.json"
    paths = [
        schema_path,
        pass_path,
        blocked_pass_path,
        bypass_path,
        missing_blocker_path,
        stale_blocker_path,
        false_pass_status_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "candidate_cooldown_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    for path in (pass_path, blocked_pass_path):
        pass_errors = _candidate_cooldown_errors(load_json(path))
        if pass_errors:
            return fail_result(
                "candidate_cooldown_validator",
                f"PASS fixture failed candidate cooldown validation: {pass_errors[0]}",
                paths,
                "COOLDOWN",
            )

    negative_expectations = {
        bypass_path: "candidate cooldown requires transition_decision=BLOCK_TRANSITION",
        missing_blocker_path: "candidate cooldown requires COOLDOWN blocker",
        stale_blocker_path: "cooldown_cycles_remaining=0 cannot carry COOLDOWN blocker",
        false_pass_status_path: "candidate cooldown cannot expose status=PASS",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _candidate_cooldown_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "candidate_cooldown_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "COOLDOWN",
            )

    dependency = exploration_exploitation_policy_validator().as_dict()
    if dependency["status"] != "PASS":
        return blocked_result(
            "candidate_cooldown_validator",
            f"exploration/exploitation policy dependency did not pass: {dependency['status']}",
            paths,
            "EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED",
        )

    return pass_result(
        "candidate_cooldown_validator",
        "candidate cooldown blocks PAPER ranking review until cooldown reaches zero, requires visible COOLDOWN blocker evidence, and cannot create live, order, or scale-up permission",
        paths,
    )


def _profit_convergence_cycle_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    if schema is None:
        return ["profit convergence cycle report schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "active_snapshot_mutation_allowed",
        "optimizer_winner_live_config_allowed",
        "paper_winner_live_config_allowed",
        "model_promotion_allowed",
        "scale_up_recommendation_allowed",
        "order_submission_allowed",
        "exchange_account_call_allowed",
        "profitability_guarantee_created",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"profit convergence cycle has forbidden true field: {field}")

    if report.get("mode") == "LIVE":
        errors.append("profit convergence cycle mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("profit convergence cycle source_modes must not include LIVE")

    warning = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning or "live orders blocked" not in warning or "no profit guarantee" not in warning:
        errors.append("profit convergence warning must state not LIVE_READY, live orders blocked, and no profit guarantee")

    dependency_statuses = [report.get(field) for field in PROFIT_CONVERGENCE_CYCLE_DEPENDENCY_FIELDS]
    pass_count = sum(1 for status in dependency_statuses if status == "PASS")
    if report.get("dependency_pass_count") != pass_count:
        errors.append("dependency_pass_count must equal actual PASS dependency status count")
    if report.get("required_dependency_count") != len(PROFIT_CONVERGENCE_CYCLE_DEPENDENCY_FIELDS):
        errors.append("required_dependency_count must equal profit convergence cycle dependency field count")

    blockers = report.get("blockers", [])
    blocker_codes = {item.get("code") for item in blockers if isinstance(item, dict)}
    non_pass_dependency = any(status != "PASS" for status in dependency_statuses)
    improvement_claim = report.get("convergence_claim") in {"LOCALLY_IMPROVING", "ROBUSTLY_IMPROVING"}
    local_review = report.get("cycle_status") == "LOCAL_IMPROVEMENT_REVIEW"
    ranking_allowed = report.get("candidate_ranking_allowed_for_paper") is True

    if non_pass_dependency:
        if local_review:
            errors.append("non-PASS dependency cannot allow LOCAL_IMPROVEMENT_REVIEW")
        if improvement_claim:
            errors.append("non-PASS dependency cannot keep profit convergence improvement claim")
        if ranking_allowed:
            errors.append("non-PASS dependency cannot allow paper candidate ranking")
        if report.get("blocks_promotion") is not True:
            errors.append("non-PASS dependency requires blocks_promotion=true")
        if not blockers:
            errors.append("non-PASS dependency requires blockers")

    data_status = report.get("data_freshness_status")
    data_age = float(report.get("data_age_seconds", 0))
    max_data_age = float(report.get("max_data_age_seconds", 0))
    if data_status != "FRESH" or data_age > max_data_age:
        if local_review or improvement_claim or ranking_allowed:
            errors.append("stale or missing profit convergence input cannot allow improvement review, claim, or ranking")
        if not blockers:
            errors.append("stale or missing profit convergence input requires blockers")

    if report.get("objective_basis") != "NET_EV_AFTER_COST":
        if local_review or improvement_claim or ranking_allowed:
            errors.append("profit convergence cannot claim improvement or rank without NET_EV_AFTER_COST objective")
        if not blockers:
            errors.append("blocked objective requires blockers")

    if report.get("raw_pnl_positive_net_ev_negative") is True or (
        report.get("raw_pnl_improved") is True and report.get("net_ev_after_cost_positive") is not True
    ):
        if local_review:
            errors.append("raw PnL improvement with negative net EV cannot allow LOCAL_IMPROVEMENT_REVIEW")
        if improvement_claim:
            errors.append("raw PnL improvement with negative net EV cannot keep convergence improvement claim")
        if ranking_allowed:
            errors.append("raw PnL improvement with negative net EV cannot allow paper candidate ranking")
        if "COST_AFTER_EDGE_UNVERIFIED" not in blocker_codes and "FEE_EXCEEDS_EDGE" not in blocker_codes:
            errors.append("raw PnL positive net EV negative cycle requires cost blocker")

    drift_status = report.get("model_drift_status")
    if drift_status in {"DRIFT_SUSPECTED", "DRIFT_DETECTED", "BLOCKED"}:
        if local_review or improvement_claim or ranking_allowed:
            errors.append(f"{drift_status} cannot allow profit convergence improvement review, claim, or ranking")
        if report.get("blocks_promotion") is not True:
            errors.append(f"{drift_status} requires blocks_promotion=true")
        if "MODEL_DRIFT_DETECTED" not in blocker_codes and "CONVERGENCE_CLAIM_UNVERIFIED" not in blocker_codes:
            errors.append(f"{drift_status} requires MODEL_DRIFT_DETECTED or CONVERGENCE_CLAIM_UNVERIFIED blocker")

    if local_review:
        if non_pass_dependency or data_status != "FRESH" or data_age > max_data_age or report.get("net_ev_after_cost_positive") is not True:
            errors.append("LOCAL_IMPROVEMENT_REVIEW requires all dependencies PASS, fresh input, and positive net EV after cost")
        if blockers:
            errors.append("LOCAL_IMPROVEMENT_REVIEW must not carry blockers")
    if ranking_allowed and report.get("cycle_status") not in {"LOCAL_IMPROVEMENT_REVIEW"}:
        errors.append("paper candidate ranking requires LOCAL_IMPROVEMENT_REVIEW cycle status")
    return errors


def profit_convergence_cycle_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "profit_convergence_cycle_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "profit_convergence_cycle_pass.json"
    dependency_untested_path = fixture_dir / "profit_convergence_cycle_dependency_untested_fail.json"
    raw_pnl_net_negative_path = fixture_dir / "profit_convergence_cycle_raw_pnl_net_negative_fail.json"
    drift_unblocked_path = fixture_dir / "profit_convergence_cycle_drift_unblocked_fail.json"
    live_flag_path = fixture_dir / "profit_convergence_cycle_live_flag_fail.json"
    paths = [
        schema_path,
        pass_path,
        dependency_untested_path,
        raw_pnl_net_negative_path,
        drift_unblocked_path,
        live_flag_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "profit_convergence_cycle_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _profit_convergence_cycle_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "profit_convergence_cycle_validator",
            f"PASS fixture failed profit convergence cycle validation: {pass_errors[0]}",
            paths,
            "CONVERGENCE_CLAIM_UNVERIFIED",
        )

    negative_expectations = {
        dependency_untested_path: "non-PASS dependency cannot allow LOCAL_IMPROVEMENT_REVIEW",
        raw_pnl_net_negative_path: "raw PnL improvement with negative net EV cannot allow LOCAL_IMPROVEMENT_REVIEW",
        drift_unblocked_path: "DRIFT_DETECTED cannot allow profit convergence improvement review",
        live_flag_path: "expected const False",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _profit_convergence_cycle_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "profit_convergence_cycle_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "CONVERGENCE_CLAIM_UNVERIFIED",
            )

    dependency = exploration_exploitation_policy_validator().as_dict()
    if dependency["status"] != "PASS":
        return blocked_result(
            "profit_convergence_cycle_validator",
            f"exploration/exploitation dependency did not pass: {dependency['status']}",
            paths,
            "EXPLORATION_EXPLOITATION_TRANSITION_UNTESTED",
        )

    return pass_result(
        "profit_convergence_cycle_validator",
        "profit convergence cycle is dependency-gated, net-EV-after-cost based, drift-blocked, PAPER/SHADOW-only, and cannot create live, writer, order, or scale-up permission",
        paths,
    )


def _parameter_narrowing_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    if schema is None:
        return ["parameter narrowing schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "active_snapshot_mutation_allowed",
        "active_config_mutation_allowed",
        "optimizer_winner_live_config_allowed",
        "paper_winner_live_config_allowed",
        "order_submission_allowed",
        "exchange_account_call_allowed",
        "scale_up_recommendation_allowed",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"parameter narrowing has forbidden true field: {field}")

    if report.get("mode") == "LIVE":
        errors.append("parameter narrowing mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("parameter narrowing source_modes must not include LIVE")

    source_evidence_ids_raw = report.get("source_evidence_ids", [])
    source_evidence_ids = [str(item) for item in source_evidence_ids_raw if isinstance(item, str)]
    bindings = report.get("source_evidence_identity_bindings", [])
    binding_by_id: dict[str, dict[str, Any]] = {}
    seen_binding_ids: set[str] = set()
    binding_mode_union: set[str] = set()
    binding_roles: set[str] = set()
    if isinstance(bindings, list):
        for index, binding in enumerate(bindings):
            if not isinstance(binding, dict):
                errors.append(f"source evidence identity binding {index} is not an object")
                continue
            evidence_id = str(binding.get("source_evidence_id", ""))
            if not evidence_id:
                errors.append(f"source evidence identity binding {index} missing source_evidence_id")
                continue
            if evidence_id in seen_binding_ids:
                errors.append(f"duplicate source evidence identity binding: {evidence_id}")
            seen_binding_ids.add(evidence_id)
            binding_by_id[evidence_id] = binding
            binding_roles.add(str(binding.get("source_role", "")))
            status = binding.get("identity_match_status")
            if status != "PASS":
                errors.append(f"source evidence identity binding cannot be {status}: {evidence_id}")
            binding_modes = set(binding.get("source_modes", []))
            binding_mode_union.update(str(mode) for mode in binding_modes)
            if "LIVE" in binding_modes:
                errors.append(f"source evidence identity binding cannot include LIVE mode: {evidence_id}")
            if not binding_modes.issubset(set(report.get("source_modes", []))):
                errors.append(f"source evidence identity binding mode not present in report source_modes: {evidence_id}")
            for field in (
                "exchange",
                "market_type",
                "session_id",
                "candidate_id",
                "strategy_id",
                "previous_parameter_hash",
                "proposed_parameter_hash",
                "timeframe_scope",
                "regime_scope",
            ):
                if binding.get(field) != report.get(field):
                    errors.append(f"source evidence identity binding mismatch for {field}: {evidence_id}")
    else:
        errors.append("source_evidence_identity_bindings must be a list")

    for evidence_id in source_evidence_ids:
        if evidence_id not in binding_by_id:
            errors.append(f"source_evidence_id missing identity binding: {evidence_id}")
    for evidence_id in binding_by_id:
        if evidence_id not in source_evidence_ids:
            errors.append(f"identity binding references unknown source_evidence_id: {evidence_id}")
    if source_evidence_ids and binding_mode_union != set(report.get("source_modes", [])):
        errors.append("source evidence identity binding modes must exactly cover report source_modes")

    warning = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning or "live orders blocked" not in warning or (
        "scale-up blocked" not in warning and "scale up blocked" not in warning
    ):
        errors.append("parameter narrowing warning must state not LIVE_READY, live orders blocked, and scale-up blocked")

    dependency_statuses = [report.get(field) for field in PARAMETER_NARROWING_DEPENDENCY_FIELDS]
    pass_count = sum(1 for status in dependency_statuses if status == "PASS")
    if report.get("dependency_pass_count") != pass_count:
        errors.append("dependency_pass_count must equal actual PASS dependency status count")
    if report.get("required_dependency_count") != len(PARAMETER_NARROWING_DEPENDENCY_FIELDS):
        errors.append("required_dependency_count must equal parameter narrowing dependency field count")

    non_pass_dependency = any(status != "PASS" for status in dependency_statuses)
    dependency_summary_status = report.get("dependency_summary_status")
    narrowing_allowed = report.get("narrowing_allowed_for_paper_ranking") is True
    narrowing_status = report.get("narrowing_status")
    recommendation_scope = report.get("recommendation_scope")
    parameter_write_scope = report.get("parameter_write_scope")
    blockers = report.get("blockers", [])

    if non_pass_dependency:
        if dependency_summary_status == "PASS":
            errors.append("dependency_summary_status cannot be PASS while a dependency is not PASS")
        if narrowing_allowed:
            errors.append("non-PASS dependency cannot allow parameter narrowing for paper ranking")
        if narrowing_status == "PAPER_PARAMETER_REVIEW_ELIGIBLE":
            errors.append("non-PASS dependency cannot make parameter narrowing PAPER_PARAMETER_REVIEW_ELIGIBLE")
        if recommendation_scope == "PAPER_PARAMETER_REVIEW_ONLY":
            errors.append("non-PASS dependency cannot use PAPER_PARAMETER_REVIEW_ONLY scope")
        if report.get("blocks_promotion") is not True:
            errors.append("non-PASS dependency requires blocks_promotion=true")
        if not blockers:
            errors.append("non-PASS dependency requires blockers")

    min_samples = int(report.get("min_required_sample_count", 0))
    paper_samples = int(report.get("paper_sample_count", 0))
    shadow_samples = int(report.get("shadow_sample_count", 0))
    sample_insufficient = paper_samples < min_samples or shadow_samples < min_samples
    if sample_insufficient:
        if narrowing_allowed:
            errors.append("insufficient PAPER/SHADOW samples cannot allow parameter narrowing")
        if report.get("blocks_promotion") is not True:
            errors.append("insufficient samples require blocks_promotion=true")
        if not blockers:
            errors.append("insufficient samples require blockers")

    max_narrowing = float(report.get("max_narrowing_pct", 0))
    narrowing_pct = float(report.get("narrowing_pct", 0))
    if narrowing_pct > max_narrowing:
        errors.append("narrowing_pct exceeds max_narrowing_pct")
        if narrowing_allowed:
            errors.append("over-narrowing cannot allow parameter narrowing for paper ranking")
        if report.get("blocks_promotion") is not True:
            errors.append("over-narrowing requires blocks_promotion=true")

    before = int(report.get("parameter_count_before", 0))
    after = int(report.get("parameter_count_after", 0))
    if after > before:
        errors.append("parameter narrowing cannot expand parameter_count_after beyond parameter_count_before")
    if narrowing_allowed and after >= before:
        errors.append("paper parameter review requires an actual narrowed parameter set")

    for index, change in enumerate(report.get("parameter_changes", [])):
        if not isinstance(change, dict):
            continue
        previous_min = float(change.get("previous_min", 0))
        previous_max = float(change.get("previous_max", 0))
        proposed_min = float(change.get("proposed_min", 0))
        proposed_max = float(change.get("proposed_max", 0))
        if previous_min > previous_max:
            errors.append(f"parameter change {index} has previous_min > previous_max")
        if proposed_min > proposed_max:
            errors.append(f"parameter change {index} has proposed_min > proposed_max")
        if change.get("direction") == "NARROW" and (proposed_min < previous_min or proposed_max > previous_max):
            errors.append(f"parameter change {index} expands bounds while marked NARROW")
        if change.get("direction") == "NARROW" and proposed_min == previous_min and proposed_max == previous_max:
            errors.append(f"parameter change {index} is marked NARROW but bounds are unchanged")

    if report.get("previous_parameter_hash") == report.get("proposed_parameter_hash") and narrowing_allowed:
        errors.append("paper parameter review requires proposed_parameter_hash to differ from previous_parameter_hash")
    if report.get("objective_basis") == "BLOCKED_NO_VALID_OBJECTIVE":
        if narrowing_allowed:
            errors.append("blocked objective cannot allow parameter narrowing")
        if not blockers:
            errors.append("blocked objective requires blockers")

    if narrowing_allowed:
        source_evidence_ids = [str(item).lower() for item in report.get("source_evidence_ids", [])]

        def has_source_evidence(*tokens: str) -> bool:
            return any(all(token in evidence_id for token in tokens) for evidence_id in source_evidence_ids)

        missing_roles = sorted(PARAMETER_NARROWING_REQUIRED_SOURCE_ROLES - binding_roles)
        if missing_roles:
            errors.append(f"paper parameter narrowing requires identity bindings for roles: {', '.join(missing_roles)}")
        if not has_source_evidence("paper", "shadow"):
            errors.append("paper parameter narrowing requires paper/shadow evidence source id")
        if not has_source_evidence("scorecard"):
            errors.append("paper parameter narrowing requires candidate scorecard source id")
        if not has_source_evidence("optimizer", "run"):
            errors.append("paper parameter narrowing requires optimizer run source id")
        if not has_source_evidence("optimizer", "recommendation"):
            errors.append("paper parameter narrowing requires optimizer recommendation source id")
        if narrowing_status != "PAPER_PARAMETER_REVIEW_ELIGIBLE":
            errors.append("paper parameter narrowing requires PAPER_PARAMETER_REVIEW_ELIGIBLE status")
        if recommendation_scope != "PAPER_PARAMETER_REVIEW_ONLY":
            errors.append("paper parameter narrowing requires PAPER_PARAMETER_REVIEW_ONLY scope")
        if parameter_write_scope != "PROPOSAL_ONLY":
            errors.append("paper parameter narrowing must remain PROPOSAL_ONLY")
        if report.get("blocks_promotion") is True:
            errors.append("paper parameter narrowing review cannot be marked blocks_promotion=true")
        if blockers:
            errors.append("paper parameter narrowing review must not carry blockers")
    else:
        if recommendation_scope == "PAPER_PARAMETER_REVIEW_ONLY" or parameter_write_scope == "PROPOSAL_ONLY":
            errors.append("paper parameter review scope cannot be shown when narrowing is not allowed")

    return errors


def parameter_narrowing_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "parameter_narrowing_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "parameter_narrowing_pass.json"
    dependency_untested_path = fixture_dir / "parameter_narrowing_dependency_untested_fail.json"
    over_narrow_path = fixture_dir / "parameter_narrowing_over_narrow_fail.json"
    live_flag_path = fixture_dir / "parameter_narrowing_live_flag_fail.json"
    live_source_path = fixture_dir / "parameter_narrowing_live_source_fail.json"
    warning_path = fixture_dir / "parameter_narrowing_warning_fail.json"
    missing_binding_path = fixture_dir / "parameter_narrowing_missing_binding_fail.json"
    identity_mismatch_path = fixture_dir / "parameter_narrowing_identity_mismatch_fail.json"
    identity_stale_path = fixture_dir / "parameter_narrowing_identity_stale_fail.json"
    paths = [
        schema_path,
        pass_path,
        dependency_untested_path,
        over_narrow_path,
        live_flag_path,
        live_source_path,
        warning_path,
        missing_binding_path,
        identity_mismatch_path,
        identity_stale_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "parameter_narrowing_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _parameter_narrowing_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "parameter_narrowing_validator",
            f"PASS fixture failed parameter narrowing validation: {pass_errors[0]}",
            paths,
            "PARAMETER_NARROWING_UNVERIFIED",
        )

    negative_expectations = {
        dependency_untested_path: "non-PASS dependency cannot allow parameter narrowing",
        over_narrow_path: "narrowing_pct exceeds max_narrowing_pct",
        live_flag_path: "expected const False",
        live_source_path: "LIVE",
        warning_path: "warning must state not LIVE_READY",
        missing_binding_path: "source_evidence_id missing identity binding",
        identity_mismatch_path: "source evidence identity binding mismatch for proposed_parameter_hash",
        identity_stale_path: "source evidence identity binding cannot be STALE",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _parameter_narrowing_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "parameter_narrowing_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "PARAMETER_NARROWING_UNVERIFIED",
            )

    return pass_result(
        "parameter_narrowing_validator",
        "parameter narrowing is dependency-gated, sample-bounded, exact evidence-identity-bound, proposal-only, PAPER/SHADOW scoped, and cannot mutate live or active config",
        paths,
    )


def _external_live_review_blockers() -> tuple[list[str], list[Path]]:
    manifest_path = ROOT / "system" / "evidence" / "MVP4_EXTERNAL_BLOCKER.evidence_manifest.json"
    paths = [manifest_path]
    if not manifest_path.exists():
        return ["LIVE_ENABLING_EVIDENCE_MISSING"], paths
    manifest = load_json(manifest_path)
    blockers = set(manifest.get("known_blockers", []))
    for item in manifest.get("external_review_input_statuses", []):
        code = item.get("primary_blocker_code")
        if code and not item.get("usable_for_live_enabling", False):
            blockers.add(code)
    return sorted(blockers), paths


def live_burn_in_feedback_validator() -> ValidatorResult:
    base = _schema_scaffold_validator(
        "live_burn_in_feedback_validator",
        "live_burn_in_feedback_report.schema.json",
        "trader1.live_burn_in_feedback_report.v1",
    )
    if base.status != "PASS":
        return base
    blockers, paths = _external_live_review_blockers()
    paths = [
        ROOT / "contracts" / "schema" / "live_burn_in_feedback_report.schema.json",
        ROOT / "contracts" / "generated" / "current_implementation_state.json",
    ] + paths
    if blockers:
        return blocked_result(
            "live_burn_in_feedback_validator",
            "live burn-in feedback is blocked until independent read-only burn-in evidence is available",
            paths,
            "LIVE_BURN_IN_FEEDBACK_MISSING",
        )
    return pass_result("live_burn_in_feedback_validator", "live burn-in feedback evidence is present and non-live", paths)


def paper_live_parity_validator() -> ValidatorResult:
    paths = [
        ROOT / "contracts" / "schema" / "paper_operation_gate_report.schema.json",
        ROOT / "contracts" / "schema" / "live_burn_in_feedback_report.schema.json",
        ROOT / "contracts" / "generated" / "current_implementation_state.json",
    ]
    for path in paths[:2]:
        schema = load_json(path)
        if schema.get("additionalProperties") is not False:
            return fail_result("paper_live_parity_validator", f"schema is not closed: {path.name}", paths, "SCHEMA_IDENTITY_MISMATCH")
    blockers, blocker_paths = _external_live_review_blockers()
    paths += blocker_paths
    if blockers:
        return blocked_result(
            "paper_live_parity_validator",
            "paper/live parity is blocked until verified live observation and burn-in evidence exist",
            paths,
            "READ_ONLY_BURN_IN_MISSING",
        )
    return pass_result("paper_live_parity_validator", "paper/live parity evidence is present for exact scope", paths)


def execution_quality_measurement_validator() -> ValidatorResult:
    base = _schema_scaffold_validator(
        "execution_quality_measurement_validator",
        "execution_quality_measurement_report.schema.json",
        "trader1.execution_quality_measurement_report.v1",
    )
    if base.status != "PASS":
        return base
    blockers, blocker_paths = _external_live_review_blockers()
    paths = [
        ROOT / "contracts" / "schema" / "execution_quality_measurement_report.schema.json",
        ROOT / "contracts" / "generated" / "current_implementation_state.json",
    ] + blocker_paths
    if blockers:
        return blocked_result(
            "execution_quality_measurement_validator",
            "execution quality measurement is blocked until realized execution evidence is available",
            paths,
            "EXECUTION_QUALITY_UNTESTED",
        )
    return pass_result("execution_quality_measurement_validator", "execution quality measurement evidence is present for exact scope", paths)


def survival_layer_validator() -> ValidatorResult:
    base = _schema_scaffold_validator(
        "survival_layer_validator",
        "survival_layer_report.schema.json",
        "trader1.survival_layer_report.v1",
    )
    if base.status != "PASS":
        return base
    paths = [
        ROOT / "contracts" / "schema" / "survival_layer_report.schema.json",
        ROOT / "contracts" / "generated" / "current_implementation_state.json",
        ROOT / "contracts" / "schema" / "emergency_flatten_report.schema.json",
        ROOT / "contracts" / "schema" / "safety_control_report.schema.json",
    ]
    dependency_failures = _dependency_failures(["emergency_flatten_validator", "safety_control_validator"])
    if dependency_failures:
        return blocked_result(
            "survival_layer_validator",
            "survival layer remains blocked until emergency protection dependencies pass: " + ", ".join(dependency_failures),
            paths,
            "SURVIVAL_LAYER_BLOCKED",
        )
    blockers, blocker_paths = _external_live_review_blockers()
    paths += blocker_paths
    if blockers:
        return blocked_result(
            "survival_layer_validator",
            "survival layer blocks scale-up until live review evidence and emergency protection are valid for exact scope",
            paths,
            "SURVIVAL_LAYER_BLOCKED",
        )
    return pass_result("survival_layer_validator", "survival layer evidence is present for exact scope", paths)


def risk_scaling_decision_validator() -> ValidatorResult:
    base = _schema_scaffold_validator(
        "risk_scaling_decision_validator",
        "risk_scaling_decision.schema.json",
        "trader1.risk_scaling_decision.v1",
    )
    if base.status != "PASS":
        return base
    paths = [
        ROOT / "contracts" / "schema" / "risk_scaling_decision.schema.json",
        ROOT / "contracts" / "generated" / "current_implementation_state.json",
        ROOT / "system" / "evidence" / "MVP4_EXTERNAL_BLOCKER.evidence_manifest.json",
    ]
    dependency_failures = _dependency_failures(
        [
            "live_burn_in_feedback_validator",
            "paper_live_parity_validator",
            "execution_quality_measurement_validator",
            "survival_layer_validator",
            "operator_control_validator",
        ]
    )
    if dependency_failures:
        return blocked_result(
            "risk_scaling_decision_validator",
            "risk scaling remains blocked until scale-up dependencies pass: " + ", ".join(dependency_failures),
            paths,
            "RISK_SCALING_UNTESTED",
        )
    return pass_result("risk_scaling_decision_validator", "risk scaling decision dependencies passed for exact scope", paths)


def live_final_guard_validator() -> ValidatorResult:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    matrix_path = ROOT / "tests" / "live_blocked" / "fixtures" / "live_blocked_matrix.json"
    paths = [
        state_path,
        ledger_path,
        matrix_path,
        ROOT / "trader1" / "safety" / "live_order_gate.py",
        ROOT / "trader1" / "execution" / "live_order_gateway.py",
    ] + _patch_result_paths()

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade"):
        if _live_flag_is_true(state.get(field)):
            return fail_result("live_final_guard_validator", f"current state has forbidden live flag: {field}", paths, "LIVE_FINAL_GUARD_FAILED")

    ledger = load_json(ledger_path)
    for patch in ledger.get("patches", []):
        for field in ("live_order_ready_after", "live_order_allowed_after", "can_live_trade_after"):
            if _live_flag_is_true(patch.get(field)):
                return fail_result("live_final_guard_validator", f"patch ledger has forbidden live flag: {patch.get('patch_id')}::{field}", paths, "LIVE_FINAL_GUARD_FAILED")

    forbidden_patch_fields = (
        "live_order_ready_after",
        "live_order_allowed_after",
        "can_live_trade_after",
        "optimizer_live_order_allowed_after",
        "convergence_live_order_allowed_after",
        "optimizer_live_mutation_detected",
        "convergence_live_mutation_detected",
        "scale_up_allowed_after",
    )
    for path in _patch_result_paths():
        patch_result = load_json(path)
        for field in forbidden_patch_fields:
            if _live_flag_is_true(patch_result.get(field)):
                return fail_result("live_final_guard_validator", f"patch result has forbidden live field: {rel(path)}::{field}", paths, "LIVE_FINAL_GUARD_FAILED")

    matrix = load_json(matrix_path)
    cases = matrix.get("cases", [])
    if not cases:
        return fail_result("live_final_guard_validator", "live-blocked matrix is empty", paths, "CONTRACT_GAP_HIGH")
    for case in cases:
        decision = evaluate_live_order_gate(
            {
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "blocker_code": case["blocker_code"],
            }
        )
        if decision.order_adapter_called or decision.live_order_allowed or decision.can_live_trade:
            return fail_result("live_final_guard_validator", f"live gate allowed blocked case: {case['case_id']}", paths, "LIVE_FINAL_GUARD_FAILED")
        if decision.primary_blocker_code != case["blocker_code"]:
            return fail_result("live_final_guard_validator", f"live gate blocker mismatch: {case['case_id']}", paths, "LIVE_FINAL_GUARD_FAILED")

    final_decision_attempt = evaluate_live_order_path(
        {
            "source_kind": "FinalDecision",
            "final_decision": "ENTER_LONG",
            "client_order_id": "live-final-guard-validator-client",
            "single_writer_available": True,
            "budget_reserved": True,
            "local_reservation_committed": True,
            "ledger_reconciled": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
        }
    )
    if final_decision_attempt.order_adapter_called or final_decision_attempt.external_submit_attempted:
        return fail_result("live_final_guard_validator", "FinalDecision path reached order adapter without live readiness", paths, "LIVE_FINAL_GUARD_FAILED")
    if final_decision_attempt.primary_blocker_code != "LIVE_READY_MISSING":
        return fail_result("live_final_guard_validator", "FinalDecision path did not expose LIVE_READY_MISSING", paths, "LIVE_READY_MISSING")

    missing_idempotency = evaluate_live_order_path(
        {
            "source_kind": "FinalDecision",
            "final_decision": "ENTER_LONG",
            "single_writer_available": True,
            "budget_reserved": True,
            "local_reservation_committed": True,
            "ledger_reconciled": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
        }
    )
    if "LIVE_FINAL_GUARD_FAILED" not in missing_idempotency.blockers or missing_idempotency.order_adapter_called:
        return fail_result("live_final_guard_validator", "missing idempotency key was not blocked by final guard", paths, "LIVE_FINAL_GUARD_FAILED")

    strategy_attempt = evaluate_live_order_path(
        {
            "source_kind": "StrategySignal",
            "final_decision": "ENTER_LONG",
            "strategy_attempted_exchange_call": True,
            "client_order_id": "live-final-guard-strategy-attempt",
            "single_writer_available": True,
            "budget_reserved": True,
            "local_reservation_committed": True,
            "ledger_reconciled": True,
        }
    )
    if strategy_attempt.order_adapter_called or strategy_attempt.primary_blocker_code != "CANDIDATE_DIRECT_LIVE_FORBIDDEN":
        return fail_result("live_final_guard_validator", "strategy-originated order attempt was not blocked before adapter", paths, "CANDIDATE_DIRECT_LIVE_FORBIDDEN")

    return pass_result("live_final_guard_validator", "live final guard blocks current state, patch ledger, live matrix, and order path before adapter submit", paths)


def optimizer_no_live_mutation_validator() -> ValidatorResult:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    paths = [state_path] + _patch_result_paths()
    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "optimizer_no_live_mutation_validator",
                f"current implementation state has forbidden live flag: {field}",
                [state_path],
                "LIVE_FINAL_GUARD_FAILED",
            )

    forbidden_fields = (
        "optimizer_live_mutation_detected",
        "convergence_live_mutation_detected",
        "optimizer_live_order_allowed_after",
        "convergence_live_order_allowed_after",
        "scale_up_allowed_after",
        "live_order_ready_after",
        "live_order_allowed_after",
        "can_live_trade_after",
    )
    for path in _patch_result_paths():
        patch = load_json(path)
        for field in forbidden_fields:
            if _live_flag_is_true(patch.get(field)):
                return fail_result(
                    "optimizer_no_live_mutation_validator",
                    f"patch result contains forbidden live-affecting field: {rel(path)}::{field}",
                    paths,
                    "LIVE_FINAL_GUARD_FAILED",
                )
    return pass_result(
        "optimizer_no_live_mutation_validator",
        "optimizer and convergence patch history contains no live config mutation or live order permission",
        paths,
    )


def _component_id_set(rows: Any) -> set[str]:
    component_ids: set[str] = set()
    if not isinstance(rows, list):
        return component_ids
    for row in rows:
        if isinstance(row, str):
            component_ids.add(row)
        elif isinstance(row, dict):
            value = row.get("component_id") or row.get("component")
            if isinstance(value, str):
                component_ids.add(value)
    return component_ids


def _profitability_evidence_audit_errors(audit: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if audit.get("project_id") != "TRADER_1":
        errors.append("audit project_id is not TRADER_1")

    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "profitability_guarantee_created",
        "optimizer_live_mutation_detected",
        "convergence_live_mutation_detected",
    ):
        if _live_flag_is_true(audit.get(field)):
            errors.append(f"audit has forbidden true field: {field}")

    text = json.dumps(audit, sort_keys=True).lower()
    for phrase in PROFITABILITY_EVIDENCE_FORBIDDEN_PHRASES:
        if phrase in text:
            errors.append(f"audit contains forbidden operator wording: {phrase}")

    inspected = _component_id_set(audit.get("inspected_components"))
    missing_inspected = sorted(PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS - inspected)
    if missing_inspected:
        errors.append(f"audit missing inspected components: {missing_inspected}")

    gaps = audit.get("gaps")
    if not isinstance(gaps, list) or not gaps:
        errors.append("audit has no explicit profitability evidence gaps")
        return errors

    gap_components = _component_id_set(gaps)
    missing_gap_components = sorted(PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS - gap_components)
    if missing_gap_components:
        errors.append(f"audit missing gap coverage for components: {missing_gap_components}")

    for index, gap in enumerate(gaps):
        if not isinstance(gap, dict):
            errors.append(f"gap #{index} is not an object")
            continue
        if gap.get("severity") not in {"MEDIUM", "HIGH", "CRITICAL"}:
            errors.append(f"gap #{index} does not carry a meaningful severity")
        if not gap.get("condition") or not gap.get("impact") or not gap.get("fix"):
            errors.append(f"gap #{index} is missing condition, impact, or fix")
        if gap.get("patch_status") not in {"RECORDED", "BLOCKED", "PARTIAL_PATCHED", "OPEN"}:
            errors.append(f"gap #{index} has unsupported patch_status")
        if gap.get("live_safety_impact") not in {"LIVE_BLOCKING", "LIVE_REVIEW_BLOCKING", "NO_LIVE_IMPACT"}:
            errors.append(f"gap #{index} does not state live safety impact")
        if _live_flag_is_true(gap.get("live_order_ready_after")) or _live_flag_is_true(gap.get("live_order_allowed_after")):
            errors.append(f"gap #{index} attempts live readiness or live permission")

    if not isinstance(audit.get("safe_patch_actions"), list) or len(audit.get("safe_patch_actions", [])) < 3:
        errors.append("audit must list at least three safe non-live patch actions")
    return errors


def _profitability_evidence_maturity_rollup_errors(rollup: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.profitability_evidence_maturity_rollup.v1")
    if schema is None:
        return ["profitability evidence maturity rollup schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(rollup, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    if rollup.get("project_id") != "TRADER_1":
        errors.append("rollup project_id is not TRADER_1")

    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "profitability_guarantee_created",
        "optimizer_live_mutation_detected",
        "convergence_live_mutation_detected",
        "live_review_eligible",
        "scale_up_eligible",
    ):
        if _live_flag_is_true(rollup.get(field)):
            errors.append(f"rollup has forbidden true field: {field}")

    if rollup.get("status") != "BLOCKED_FOR_PROFITABILITY_EVIDENCE_MATURITY":
        errors.append("rollup status must keep profitability evidence maturity blocked")

    text = json.dumps(rollup, sort_keys=True).lower()
    for phrase in PROFITABILITY_EVIDENCE_FORBIDDEN_PHRASES:
        if phrase in text:
            errors.append(f"rollup contains forbidden operator wording: {phrase}")

    components = rollup.get("components", [])
    component_ids = _component_id_set(components)
    missing_components = sorted(PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS - component_ids)
    unexpected_components = sorted(component_ids - PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS)
    if missing_components:
        errors.append(f"rollup missing required maturity components: {missing_components}")
    if unexpected_components:
        errors.append(f"rollup has unexpected maturity components: {unexpected_components}")

    if rollup.get("required_component_count") != len(PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS):
        errors.append("rollup required_component_count does not match required component set")
    if rollup.get("component_count") != len(PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS):
        errors.append("rollup component_count does not match required component set")
    if rollup.get("all_component_ids_present") is not True or rollup.get("coverage_complete") is not True:
        errors.append("rollup must explicitly mark component coverage complete")

    for index, component in enumerate(components):
        if not isinstance(component, dict):
            errors.append(f"rollup component #{index} is not an object")
            continue
        component_id = component.get("component_id", f"component#{index}")
        if component.get("validator_status") in {"FAIL", "UNTESTED", "STALE", "TIMEOUT"}:
            errors.append(f"rollup component {component_id} has unusable validator_status")
        if component.get("freshness_status") in {"STALE", "UNTESTED", "TIMEOUT"}:
            errors.append(f"rollup component {component_id} has unusable freshness_status")
        if component.get("dependency_status") in {"FAIL", "UNTESTED", "STALE", "TIMEOUT"}:
            errors.append(f"rollup component {component_id} has unusable dependency_status")
        if _live_flag_is_true(component.get("live_review_eligible")):
            errors.append(f"rollup component {component_id} attempted live review eligibility")
        if _live_flag_is_true(component.get("scale_up_allowed")):
            errors.append(f"rollup component {component_id} attempted scale-up permission")
        if component.get("evidence_status") == "PASS" and not component.get("source_evidence_ids"):
            errors.append(f"rollup component {component_id} claims PASS evidence without source_evidence_ids")
        if component.get("sample_count", 0) < component.get("min_required_sample_count", 0):
            if component.get("evidence_status") == "PASS":
                errors.append(f"rollup component {component_id} claims PASS evidence below required samples")
        paper_scorecard_input = component.get("paper_scorecard_input_eligible") is True
        long_run_eligible = component.get("long_run_evidence_eligible") is True
        long_run_blocker = component.get("long_run_blocker_code")
        if component.get("maturity_status") == "PAPER_SCORECARD_INPUT_ONLY" and not paper_scorecard_input:
            errors.append(f"rollup component {component_id} marks PAPER scorecard input without eligibility flag")
        if paper_scorecard_input and component.get("maturity_status") not in {
            "PAPER_SCORECARD_INPUT_ONLY",
            "BLOCKED_LONG_RUN_EVIDENCE",
        }:
            errors.append(f"rollup component {component_id} has scorecard eligibility/status mismatch")
        if component.get("maturity_status") == "BLOCKED_LONG_RUN_EVIDENCE" and long_run_eligible:
            errors.append(f"rollup component {component_id} claims long-run eligibility while long-run evidence is blocked")
        if long_run_eligible and long_run_blocker:
            errors.append(f"rollup component {component_id} has long-run blocker while long-run eligible")
        if not long_run_eligible and not long_run_blocker:
            errors.append(f"rollup component {component_id} lacks explicit long-run blocker")
        if not component.get("next_required_evidence") or not component.get("primary_blocker_code"):
            errors.append(f"rollup component {component_id} is missing next evidence or blocker code")

    if rollup.get("paper_scorecard_input_allowed") is True and not any(
        isinstance(component, dict) and component.get("paper_scorecard_input_eligible") is True
        for component in components
    ):
        errors.append("rollup allows PAPER scorecard input without any component-level eligibility")

    action = str(rollup.get("next_operator_action", "")).lower()
    if ("paper" not in action and "shadow" not in action) or "live" not in action or "blocked" not in action:
        errors.append("rollup next_operator_action must direct PAPER/SHADOW evidence collection and state live is blocked")

    return errors


def profitability_evidence_maturity_rollup_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "profitability_evidence_maturity_rollup.schema.json"
    rollup_path = (
        ROOT
        / "system"
        / "evidence"
        / "audit_reports"
        / "MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json"
    )
    fixture_path = ROOT / "tests" / "validators" / "fixtures" / "profitability_evidence_maturity_rollup_pass.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    paths = [schema_path, rollup_path, fixture_path, state_path]
    missing_paths = [path for path in paths if not path.exists()]
    if missing_paths:
        return blocked_result(
            "profitability_evidence_maturity_rollup_validator",
            f"profitability evidence maturity rollup inputs missing: {[rel(path) for path in missing_paths]}",
            paths,
            "CONTRACT_GAP_HIGH",
        )

    for path in (rollup_path, fixture_path):
        errors = _profitability_evidence_maturity_rollup_errors(load_json(path))
        if errors:
            return blocked_result(
                "profitability_evidence_maturity_rollup_validator",
                f"{rel(path)}: {errors[0]}",
                paths,
                "CONTRACT_GAP_HIGH",
            )

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "profitability_evidence_maturity_rollup_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    return pass_result(
        "profitability_evidence_maturity_rollup_validator",
        "profitability evidence maturity rollup covers all required components and remains live-blocked",
        paths,
    )


def _paper_exposure_quality_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.paper_exposure_quality_report.v1")
    if schema is None:
        return ["paper_exposure_quality_report schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "promotion_eligible",
        "order_adapter_called",
        "exchange_account_call_allowed",
        "live_config_mutation_allowed",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"paper exposure report has forbidden live, exchange, or scale field: {field}")

    if report.get("mode") != "PAPER":
        errors.append("paper exposure report mode must be PAPER and never LIVE before independent live-enabling evidence")

    warning = str(report.get("operator_warning", "")).lower()
    if "paper-only" not in warning or "scale-up blocked" not in warning:
        errors.append("operator_warning must say paper-only and scale-up blocked")

    if not report.get("source_evidence_ids"):
        errors.append("source_evidence_ids missing for paper exposure quality report")
    if report.get("portfolio_equity_source") == "UNVERIFIED":
        errors.append("portfolio_equity_source must be verified paper evidence")

    status = report.get("risk_quality_status")
    blockers = report.get("blockers", [])
    blocker_codes = {item.get("code") for item in blockers if isinstance(item, dict)}
    pass_status = status == "PASS_PAPER_ONLY"

    if pass_status:
        if blockers:
            errors.append("PASS_PAPER_ONLY paper exposure report must not carry blockers")
        if report.get("paper_sample_count", 0) < report.get("min_required_sample_count", 0):
            errors.append("paper_sample_count below min_required_sample_count")
        if report.get("gross_exposure_pct", 0) > report.get("max_allowed_gross_exposure_pct", 0):
            errors.append("gross_exposure_pct exceeds max_allowed_gross_exposure_pct")
        if report.get("max_symbol_exposure_pct", 0) > report.get("max_allowed_symbol_exposure_pct", 0):
            errors.append("max_symbol_exposure_pct exceeds max_allowed_symbol_exposure_pct")
        if report.get("symbol_concentration_pct", 0) > report.get("max_allowed_symbol_concentration_pct", 0):
            errors.append("symbol_concentration_pct exceeds max_allowed_symbol_concentration_pct")
        if report.get("drawdown_pct", 0) > report.get("max_allowed_drawdown_pct", 0):
            errors.append("drawdown_pct exceeds max_allowed_drawdown_pct")
        if report.get("exposure_breach_count", 0) > 0:
            errors.append("PASS_PAPER_ONLY cannot have exposure_breach_count > 0")
        if report.get("drawdown_breach_count", 0) > 0:
            errors.append("PASS_PAPER_ONLY cannot have drawdown_breach_count > 0")
        if report.get("idempotency_conflict_count", 0) > 0:
            errors.append("PASS_PAPER_ONLY cannot have idempotency_conflict_count > 0")
        if report.get("partial_write_recovery_status") != "PASS":
            errors.append("PASS_PAPER_ONLY requires partial_write_recovery_status=PASS")
    else:
        if not blockers:
            errors.append("non-PASS paper exposure report must carry explicit blockers")
        if status == "INSUFFICIENT_EVIDENCE" and "SAMPLE_INSUFFICIENT" not in blocker_codes:
            errors.append("INSUFFICIENT_EVIDENCE requires SAMPLE_INSUFFICIENT blocker")
        if status == "BLOCKED_EXPOSURE_BREACH" and "RISK_VETO" not in blocker_codes:
            errors.append("BLOCKED_EXPOSURE_BREACH requires RISK_VETO blocker")
        if status == "BLOCKED_DRAWDOWN_BREACH" and "DRAWDOWN_FREEZE_ACTIVE" not in blocker_codes:
            errors.append("BLOCKED_DRAWDOWN_BREACH requires DRAWDOWN_FREEZE_ACTIVE blocker")

    if report.get("recommendation") == "SCALE_DOWN_RECOMMENDED" and pass_status:
        errors.append("SCALE_DOWN_RECOMMENDED must be tied to a blocked or degraded exposure report")
    return errors


def paper_exposure_quality_report_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "paper_exposure_quality_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "paper_exposure_quality_pass.json"
    scale_up_path = fixture_dir / "paper_exposure_quality_scale_up_fail.json"
    missing_evidence_path = fixture_dir / "paper_exposure_quality_missing_evidence_fail.json"
    exposure_breach_path = fixture_dir / "paper_exposure_quality_exposure_breach_fail.json"
    live_mode_path = fixture_dir / "paper_exposure_quality_live_mode_fail.json"
    paths = [
        schema_path,
        pass_path,
        scale_up_path,
        missing_evidence_path,
        exposure_breach_path,
        live_mode_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "paper_exposure_quality_report_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _paper_exposure_quality_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "paper_exposure_quality_report_validator",
            f"PASS fixture failed paper exposure quality validation: {pass_errors[0]}",
            paths,
            "RISK_SCALING_UNTESTED",
        )

    negative_expectations = {
        scale_up_path: "expected const False",
        missing_evidence_path: "source_evidence_ids missing",
        exposure_breach_path: "gross_exposure_pct exceeds max_allowed_gross_exposure_pct",
        live_mode_path: "paper exposure report mode must be PAPER",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _paper_exposure_quality_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "paper_exposure_quality_report_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "RISK_SCALING_UNTESTED",
            )

    return pass_result(
        "paper_exposure_quality_report_validator",
        "paper exposure quality report is paper-only, evidence-bound, scale-up blocked, and fail-closed on exposure breaches",
        paths,
    )


CANDIDATE_SCORECARD_COST_FIELDS = (
    "expected_fee_bps",
    "expected_spread_bps",
    "expected_slippage_bps",
    "expected_impact_bps",
    "expected_latency_penalty_bps",
)
STRATEGY_CONDITION_REQUIRED_FAMILIES = {"VWAP_REVERSION", "TREND_PULLBACK", "BREAKOUT_RETEST"}
STRATEGY_CONDITION_REQUIRED_REGIMES = {"TRENDING", "RANGE", "RISK_OFF"}
STRATEGY_CONDITION_REQUIRED_GLOBAL_NO_TRADE = {"MIN_EDGE_FAIL", "EXPECTED_SLIPPAGE_EXCEEDED", "REGIME_MISMATCH"}
SYMBOL_STRATEGY_REQUIRED_FAMILIES = {"VWAP_REVERSION", "TREND_PULLBACK", "BREAKOUT_RETEST"}
OVERFIT_REQUIRED_PASS_STATUSES = {
    "oos_status": "PASS",
    "walk_forward_status": "PASS",
    "bootstrap_status": "PASS",
    "ranking_stability_status": "PASS",
    "survivorship_bias_check": "PASS",
    "data_snooping_check": "PASS",
}
ROLLING_WINDOW_DEFAULT_MIN_SAMPLE_COUNT = 300
ROLLING_WINDOW_DEFAULT_MIN_TRAIN_WINDOWS = 6
ROLLING_WINDOW_DEFAULT_MIN_OOS_WINDOWS = 3
ROLLING_WINDOW_DEFAULT_MIN_WALK_FORWARD_WINDOWS = 4
ROLLING_WINDOW_DEFAULT_MIN_BOOTSTRAP_ITERATIONS = 500
ROLLING_WINDOW_DEFAULT_MIN_SOURCE_EVIDENCE_IDS = 3
OPTIMIZER_FEEDBACK_COST_PAIRS = (
    ("fee_deviation_bps", "realized_fee_bps", "expected_fee_bps"),
    ("slippage_deviation_bps", "realized_slippage_bps", "expected_slippage_bps"),
    ("impact_deviation_bps", "realized_impact_bps", "expected_impact_bps"),
)
OPTIMIZER_FEEDBACK_RISK_REVIEW_BLOCKERS = {
    "EXECUTION_FEEDBACK_DIVERGENT",
    "EXECUTION_QUALITY_UNTESTED",
    "RISK_VETO",
    "SCALE_UP_NOT_ELIGIBLE",
    "HARD_TRUTH_MISSING",
}
ORDER_FAILURE_EXECUTION_ROOT_CAUSES = {
    "SLIPPAGE_DIVERGENCE",
    "EXECUTION_FEEDBACK_DIVERGENT",
    "FEE_MODEL_MISMATCH",
}
ORDER_FAILURE_EXECUTION_MARKERS = (
    "execution_feedback",
    "optimizer_feedback",
    "slippage",
    "fee",
    "impact",
    "latency",
)


def optimizer_feedback_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("feedback_hash", None)
    return sha256_json(payload)


def _paper_shadow_evidence_accumulation_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    errors: list[str] = []
    if schema is None:
        return ["paper/shadow evidence accumulation schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "promotion_eligible",
        "order_adapter_called",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"paper/shadow evidence report has forbidden true field: {field}")
    if report.get("dashboard_display_truth_only") is not True:
        errors.append("paper/shadow evidence report must be marked dashboard_display_truth_only=true")
    if report.get("paper_mode") != "PAPER" or report.get("shadow_mode") != "SHADOW":
        errors.append("paper/shadow evidence report must keep PAPER and SHADOW modes separated")
    if report.get("paper_session_id") == report.get("shadow_session_id"):
        errors.append("paper and shadow session ids must be distinct")
    if "/paper/" not in report.get("paper_artifact_path", "") or "/shadow/" not in report.get("shadow_artifact_path", ""):
        errors.append("paper/shadow evidence paths must include paper and shadow namespaces")
    if report.get("paper_artifact_hash") == report.get("shadow_artifact_hash") or report.get("session_hashes_distinct") is not True:
        errors.append("paper/shadow evidence artifact hashes must be distinct")
    if report.get("raw_join_attempted"):
        errors.append("raw paper/shadow evidence joins are forbidden")
    if report.get("evidence_hash") != paper_shadow_evidence_hash(report):
        errors.append("paper/shadow evidence hash mismatch")

    blockers = report.get("blockers", [])
    blocker_codes = {blocker.get("code") for blocker in blockers if isinstance(blocker, dict)}
    if int(report.get("paper_sample_count", 0)) < int(report.get("min_required_sample_count", 1)) or int(report.get("shadow_sample_count", 0)) < int(report.get("min_required_sample_count", 1)):
        errors.append("sample count below min_required_sample_count")
        if "SAMPLE_INSUFFICIENT" not in blocker_codes:
            errors.append("insufficient samples must carry SAMPLE_INSUFFICIENT blocker")
    long_run_coverage_requirements_met = (
        int(report.get("paper_sample_count", 0)) >= int(report.get("min_required_sample_count", 1))
        and int(report.get("shadow_sample_count", 0)) >= int(report.get("min_required_sample_count", 1))
        and int(report.get("evidence_window_count", 0)) >= int(report.get("min_required_evidence_window_count", 1))
        and int(report.get("evidence_span_hours", 0)) >= int(report.get("min_required_evidence_span_hours", 1))
    )
    supporting_source_ids = report.get("supporting_source_evidence_ids") or []
    supporting_window_count = paper_shadow_paired_supporting_window_count(supporting_source_ids)
    try:
        reported_supporting_window_count = int(report.get("supporting_source_window_count", -1))
    except (TypeError, ValueError):
        reported_supporting_window_count = -1
    if reported_supporting_window_count != supporting_window_count:
        errors.append("supporting_source_window_count must match paired supporting source ids")
    if report.get("evidence_span_source") == "NOT_PROVIDED" and int(report.get("evidence_span_hours", 0)) != 0:
        errors.append("evidence_span_hours must be zero when evidence_span_source is NOT_PROVIDED")
    if (
        report.get("evidence_span_source") != "NOT_PROVIDED"
        and int(report.get("evidence_span_hours", 0)) > 0
        and report.get("evidence_span_source_status") != "PASS"
    ):
        errors.append("evidence_span_source_status must be PASS when evidence_span_hours are supplied")
    if report.get("long_run_evidence_eligible") and report.get("evidence_span_source_status") != "PASS":
        errors.append("long-run evidence eligibility requires PASS evidence span source status")
    actual_runtime_source_ids = report.get("actual_runtime_source_evidence_ids") or []
    actual_runtime_source_status = report.get("actual_runtime_source_status") or "MISSING"
    actual_runtime_source_scope_errors = paper_shadow_actual_runtime_source_id_errors(report)
    actual_runtime_requirement_errors = paper_shadow_actual_runtime_requirement_status_errors(report)
    actual_runtime_source_validated = (
        actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and bool(actual_runtime_source_ids)
        and not actual_runtime_source_scope_errors
        and not actual_runtime_requirement_errors
    )
    long_run_requirements_met = (
        long_run_coverage_requirements_met
        and supporting_window_count >= int(report.get("min_required_evidence_window_count", 1))
        and actual_runtime_source_validated
    )
    if (
        int(report.get("evidence_window_count", 0)) >= int(report.get("min_required_evidence_window_count", 1))
        and supporting_window_count < int(report.get("min_required_evidence_window_count", 1))
    ):
        errors.append("long-run evidence requires per-window PAPER and SHADOW supporting source ids")
        if "MEASUREMENT_MISSING" not in blocker_codes:
            errors.append("missing per-window supporting source evidence must carry MEASUREMENT_MISSING blocker")
    if report.get("long_run_evidence_eligible") and int(report.get("evidence_window_count", 0)) > supporting_window_count:
        errors.append("long-run evidence window count exceeds supporting source coverage")
    if report.get("long_run_evidence_eligible") and not actual_runtime_source_validated:
        errors.append("long-run evidence eligibility requires validated non-live persistent runtime source evidence")
        if "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING" not in blocker_codes:
            errors.append("missing actual runtime source evidence must carry ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING blocker")
    if actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and not actual_runtime_source_ids:
        errors.append("validated actual runtime source status requires source evidence ids")
        if "MEASUREMENT_MISSING" not in blocker_codes:
            errors.append("missing actual runtime source evidence ids must carry MEASUREMENT_MISSING blocker")
    if actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and actual_runtime_source_scope_errors:
        errors.extend(actual_runtime_source_scope_errors)
        if "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING" not in blocker_codes:
            errors.append("invalid actual runtime source ids must carry ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING blocker")
    if actual_runtime_source_status == "VALIDATED_NON_LIVE_RUNTIME" and actual_runtime_requirement_errors:
        errors.extend(actual_runtime_requirement_errors)
        if "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING" not in blocker_codes:
            errors.append("invalid actual runtime requirement statuses must carry ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING blocker")
    if actual_runtime_source_status != "VALIDATED_NON_LIVE_RUNTIME" and actual_runtime_source_ids:
        errors.append("actual runtime source ids require validated non-live runtime status")
        if "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING" not in blocker_codes:
            errors.append("unvalidated actual runtime source ids must carry ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING blocker")
    if not report.get("long_run_evidence_eligible") and long_run_requirements_met:
        errors.append("long-run eligibility flag must match validated window, span, and actual runtime source evidence")
    if report.get("long_run_evidence_eligible") and not long_run_requirements_met:
        errors.append("long-run evidence eligibility claimed before minimum window/span coverage")
        if "SAMPLE_INSUFFICIENT" not in blocker_codes:
            errors.append("short long-run evidence claim must carry SAMPLE_INSUFFICIENT blocker")
    if report.get("long_run_evidence_eligible") and report.get("long_run_blocker_code") is not None:
        errors.append("long-run evidence eligible report must not carry long_run_blocker_code")
    if not report.get("long_run_evidence_eligible") and not report.get("long_run_blocker_code"):
        errors.append("long-run evidence blocker must remain visible when long_run_evidence_eligible=false")
    if int(report.get("paper_artifact_age_seconds", 0)) > int(report.get("max_artifact_age_seconds", 1)) or int(report.get("shadow_artifact_age_seconds", 0)) > int(report.get("max_artifact_age_seconds", 1)):
        errors.append("artifact age exceeds max_artifact_age_seconds")
        if "DATA_QUALITY_INSUFFICIENT" not in blocker_codes:
            errors.append("stale artifacts must carry DATA_QUALITY_INSUFFICIENT blocker")
    if int(report.get("entry_reason_count", 0)) <= 0 or int(report.get("no_trade_reason_count", 0)) <= 0:
        errors.append("entry and no-trade reason counts are required")
        if "MEASUREMENT_MISSING" not in blocker_codes:
            errors.append("missing reason evidence must carry MEASUREMENT_MISSING blocker")
    if int(report.get("cost_evidence_count", 0)) <= 0:
        errors.append("cost evidence count is required")
        if "EXECUTION_FEEDBACK_MISSING" not in blocker_codes:
            errors.append("missing cost evidence must carry EXECUTION_FEEDBACK_MISSING blocker")
    if not report.get("source_evidence_ids"):
        errors.append("source_evidence_ids are required")
    source_ids = report.get("source_evidence_ids") or []
    if len(source_ids) != len(set(source_ids)):
        errors.append("source_evidence_ids must be unique")
    if len(supporting_source_ids) != len(set(supporting_source_ids)):
        errors.append("supporting_source_evidence_ids must be unique")
    if set(source_ids) & set(supporting_source_ids):
        errors.append("bound source_evidence_ids must not be duplicated as supporting_source_evidence_ids")

    bindings = report.get("source_evidence_bindings") or []
    binding_by_id: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        if not isinstance(binding, dict):
            errors.append("source_evidence_bindings entries must be objects")
            continue
        source_id = binding.get("source_evidence_id")
        if source_id in binding_by_id:
            errors.append(f"duplicate source evidence binding: {source_id}")
        if source_id:
            binding_by_id[source_id] = binding
        if binding.get("identity_match_status") != "PASS":
            errors.append(f"source evidence binding status is not PASS: {source_id}")
        for field in ("exchange", "market_type", "candidate_id", "strategy_id", "strategy_build_id", "parameter_hash"):
            if binding.get(field) != report.get(field):
                errors.append(f"source evidence binding mismatch for {field}: {source_id}")
        role = binding.get("source_role")
        if role == "PAPER_OPERATION":
            expected = {
                "mode": "PAPER",
                "session_id": report.get("paper_session_id"),
                "artifact_path": report.get("paper_artifact_path"),
                "artifact_hash": report.get("paper_artifact_hash"),
                "sample_count": report.get("paper_sample_count"),
                "artifact_age_seconds": report.get("paper_artifact_age_seconds"),
            }
        elif role == "SHADOW_OBSERVATION":
            expected = {
                "mode": "SHADOW",
                "session_id": report.get("shadow_session_id"),
                "artifact_path": report.get("shadow_artifact_path"),
                "artifact_hash": report.get("shadow_artifact_hash"),
                "sample_count": report.get("shadow_sample_count"),
                "artifact_age_seconds": report.get("shadow_artifact_age_seconds"),
            }
        else:
            errors.append(f"unsupported source evidence binding role: {source_id}")
            continue
        for field, expected_value in expected.items():
            if binding.get(field) != expected_value:
                errors.append(f"source evidence binding mismatch for {field}: {source_id}")

    for source_id in binding_by_id:
        if source_id not in source_ids:
            errors.append(f"source evidence binding references unknown source id: {source_id}")
    for source_id in source_ids:
        if source_id not in binding_by_id:
            errors.append(f"source evidence id lacks binding: {source_id}")
    binding_roles = {binding.get("source_role") for binding in bindings if isinstance(binding, dict)}
    if not {"PAPER_OPERATION", "SHADOW_OBSERVATION"}.issubset(binding_roles):
        errors.append("source evidence bindings must include PAPER_OPERATION and SHADOW_OBSERVATION roles")

    eligible = report.get("scorecard_input_eligible") is True
    chain_complete = report.get("evidence_chain_complete") is True
    ranking_action = report.get("optimizer_ranking_action")
    if eligible:
        if blockers:
            errors.append("scorecard_input_eligible paper/shadow evidence must not carry blockers")
        if ranking_action != "ALLOW_RANKING":
            errors.append("scorecard_input_eligible paper/shadow evidence must use ALLOW_RANKING")
        if not chain_complete:
            errors.append("scorecard_input_eligible requires evidence_chain_complete=true")
    else:
        if not blockers:
            errors.append("non-eligible paper/shadow evidence must carry explicit blockers")
        if ranking_action == "ALLOW_RANKING":
            errors.append("non-eligible paper/shadow evidence cannot allow ranking")
    return errors


def _optimizer_feedback_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    errors: list[str] = []
    if schema is None:
        return ["optimizer feedback report schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "promotion_eligible"):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"optimizer feedback report has forbidden true field: {field}")
    if report.get("mode") == "LIVE":
        errors.append("optimizer feedback report mode LIVE is forbidden before independent live-enabling evidence")
    if report.get("dashboard_display_truth_only") is not True:
        errors.append("optimizer feedback report must be marked dashboard_display_truth_only=true")
    if report.get("feedback_hash") != optimizer_feedback_hash(report):
        errors.append("optimizer feedback hash mismatch")

    blockers = report.get("blockers", [])
    blocker_codes = {blocker.get("code") for blocker in blockers if isinstance(blocker, dict)}
    feedback_eligible = report.get("feedback_eligible") is True
    net_ev_deviation = abs(
        float(report["expected_net_ev_after_cost_bps"]) - float(report["realized_net_ev_after_cost_bps"])
    )
    if abs(float(report["net_ev_deviation_bps"]) - net_ev_deviation) > 0.000001:
        errors.append("net_ev_deviation_bps must equal absolute expected-vs-realized net EV difference")
    for deviation_field, realized_field, expected_field in OPTIMIZER_FEEDBACK_COST_PAIRS:
        expected_deviation = max(0.0, float(report[realized_field]) - float(report[expected_field]))
        if abs(float(report[deviation_field]) - expected_deviation) > 0.000001:
            errors.append(f"{deviation_field} must equal positive realized-minus-expected cost difference")

    if feedback_eligible:
        if report.get("feedback_status") != "VALIDATED_FOR_PAPER_RANKING":
            errors.append("feedback_eligible requires feedback_status=VALIDATED_FOR_PAPER_RANKING")
        if report.get("execution_quality_status") != "PASS":
            errors.append("execution_quality_status must be PASS before feedback eligibility")
        if report.get("risk_review_status") != "PASS":
            errors.append("feedback_eligible requires risk_review_status=PASS")
        if report.get("risk_review_action") != "ALLOW_PAPER_RANKING_REVIEW":
            errors.append("feedback_eligible requires risk_review_action=ALLOW_PAPER_RANKING_REVIEW")
        if report.get("exposure_review_status") != "PASS" or report.get("drawdown_review_status") != "PASS":
            errors.append("feedback_eligible requires exposure and drawdown review PASS")
        if report.get("risk_review_blocker_code") is not None:
            errors.append("feedback_eligible must not carry risk_review_blocker_code")
        if report.get("optimizer_ranking_action") != "ALLOW_RANKING":
            errors.append("optimizer_ranking_action must be ALLOW_RANKING before feedback eligibility")
        if blockers:
            errors.append("feedback_eligible optimizer feedback must not carry blockers")
        if float(report["net_ev_deviation_bps"]) > float(report["max_allowed_net_ev_deviation_bps"]):
            errors.append("net_ev_deviation_bps above max_allowed_net_ev_deviation_bps while feedback_eligible=true")
        if float(report["slippage_deviation_bps"]) > float(report["max_allowed_slippage_deviation_bps"]):
            errors.append("slippage_deviation_bps above max_allowed_slippage_deviation_bps while feedback_eligible=true")
        if float(report["fee_deviation_bps"]) > float(report["max_allowed_fee_deviation_bps"]):
            errors.append("fee_deviation_bps above max_allowed_fee_deviation_bps while feedback_eligible=true")
        if float(report["impact_deviation_bps"]) > float(report["max_allowed_impact_deviation_bps"]):
            errors.append("impact_deviation_bps above max_allowed_impact_deviation_bps while feedback_eligible=true")
        if float(report["latency_deviation_ms"]) > float(report["max_allowed_latency_deviation_ms"]):
            errors.append("latency_deviation_ms above max_allowed_latency_deviation_ms while feedback_eligible=true")
        if float(report["realized_net_ev_after_cost_bps"]) <= 0:
            errors.append("realized_net_ev_after_cost_bps must be positive before feedback eligibility")
    else:
        if report.get("feedback_status") == "VALIDATED_FOR_PAPER_RANKING":
            errors.append("feedback_status cannot be VALIDATED_FOR_PAPER_RANKING when feedback_eligible=false")
        if not blockers:
            errors.append("non-eligible optimizer feedback must carry explicit blocker evidence")
        if report.get("risk_review_status") == "PASS" and report.get("risk_review_action") == "ALLOW_PAPER_RANKING_REVIEW":
            errors.append("non-eligible optimizer feedback cannot pass risk review for paper ranking")

    if report.get("execution_quality_status") in {"FAIL", "BLOCKED", "UNTESTED", "STALE"} and not any(
        blocker.get("code") in {"EXECUTION_FEEDBACK_DIVERGENT", "EXECUTION_QUALITY_UNTESTED"}
        for blocker in blockers
    ):
        errors.append("non-PASS execution_quality_status must carry execution feedback blocker")
    if report.get("risk_review_status") in {"WARN", "BLOCKED", "UNTESTED", "STALE"}:
        risk_blocker = report.get("risk_review_blocker_code")
        if risk_blocker not in OPTIMIZER_FEEDBACK_RISK_REVIEW_BLOCKERS:
            errors.append("non-PASS risk_review_status must carry known risk_review_blocker_code")
        if risk_blocker not in blocker_codes:
            errors.append("risk_review_blocker_code must appear in blockers")
        if report.get("risk_review_action") == "ALLOW_PAPER_RANKING_REVIEW":
            errors.append("non-PASS risk_review_status cannot allow paper ranking review")
    if report.get("optimizer_ranking_action") == "BLOCK_RANKING" and not blockers:
        errors.append("BLOCK_RANKING optimizer feedback must carry blocker evidence")
    return errors


def _failure_analysis_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    errors: list[str] = []
    if schema is None:
        return ["failure analysis report schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "promotion_eligible"):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"failure analysis report has forbidden true field: {field}")
    if report.get("mode") == "LIVE":
        errors.append("failure analysis report mode LIVE is forbidden before independent live-enabling evidence")
    if report.get("dashboard_display_truth_only") is not True:
        errors.append("failure analysis report must be marked dashboard_display_truth_only=true")

    blockers = report.get("blockers", [])
    blocker_codes = {blocker.get("code") for blocker in blockers if isinstance(blocker, dict)}
    primary_root_cause = report.get("primary_root_cause_code")
    root_cause_status = report.get("root_cause_status")
    live_affecting = report.get("live_affecting") is True
    repeated_count = int(report.get("repeated_failure_count", 0))
    repeated_same_cause = report.get("repeated_failure_same_root_cause") is True
    blocks_promotion = report.get("blocks_promotion") is True
    blocks_live_order = report.get("blocks_live_order") is True
    ranking_action = report.get("optimizer_ranking_action")

    if primary_root_cause == "UNKNOWN_ROOT_CAUSE" and root_cause_status != "UNKNOWN":
        errors.append("UNKNOWN_ROOT_CAUSE requires root_cause_status=UNKNOWN")
    if root_cause_status == "UNKNOWN" and primary_root_cause != "UNKNOWN_ROOT_CAUSE":
        errors.append("root_cause_status=UNKNOWN requires primary_root_cause_code=UNKNOWN_ROOT_CAUSE")
    if root_cause_status in {"UNKNOWN", "PARTIAL"} and report.get("failure_status") == "ANALYZED":
        errors.append("unknown or partial root cause cannot use failure_status=ANALYZED")

    if live_affecting and primary_root_cause == "UNKNOWN_ROOT_CAUSE":
        if not blocks_live_order:
            errors.append("UNKNOWN_ROOT_CAUSE in live-affecting failure must block live order")
        if not blocks_promotion:
            errors.append("UNKNOWN_ROOT_CAUSE in live-affecting failure must block promotion")
        if ranking_action != "BLOCK_RANKING":
            errors.append("UNKNOWN_ROOT_CAUSE in live-affecting failure must block ranking")
        if "ROOT_CAUSE_UNKNOWN_LIVE_AFFECTING" not in blocker_codes:
            errors.append("UNKNOWN_ROOT_CAUSE in live-affecting failure must carry ROOT_CAUSE_UNKNOWN_LIVE_AFFECTING blocker")

    if repeated_same_cause and repeated_count >= 2:
        if not report.get("previous_failure_analysis_ids"):
            errors.append("repeated same-root-cause failure must link previous failure analysis ids")
        if not blocks_promotion:
            errors.append("repeated same-root-cause failure must block promotion")
        if ranking_action == "ALLOW_RANKING":
            errors.append("repeated same-root-cause failure must block ranking")
        if report.get("recommended_response") not in {"BLOCK_CANDIDATE", "PENALIZE_RANKING", "RETIRE_CANDIDATE"}:
            errors.append("repeated same-root-cause failure must recommend block, penalize, or retire")
        if not blockers:
            errors.append("repeated same-root-cause failure must carry explicit blocker evidence")

    if (blocks_promotion or blocks_live_order) and not blockers:
        errors.append("blocking failure analysis must carry explicit blocker evidence")
    if blocks_live_order and not live_affecting:
        errors.append("blocks_live_order=true requires live_affecting=true")
    if ranking_action == "ALLOW_RANKING" and (blocks_promotion or blocks_live_order or blockers):
        errors.append("optimizer_ranking_action=ALLOW_RANKING conflicts with blockers or promotion/live blocks")

    if report.get("memory_write_required") is True and report.get("memory_write_status") != "APPEND_ONLY_RECORDED":
        errors.append("memory_write_required requires memory_write_status=APPEND_ONLY_RECORDED")
    if report.get("memory_write_status") == "APPEND_ONLY_RECORDED" and not report.get("audit_hash"):
        errors.append("APPEND_ONLY_RECORDED requires audit_hash")

    return errors


def _order_failure_taxonomy_errors(report: dict[str, Any]) -> list[str]:
    errors = _failure_analysis_errors(report)
    if errors:
        return errors

    blockers = report.get("blockers", [])
    blocker_codes = {blocker.get("code") for blocker in blockers if isinstance(blocker, dict)}
    primary_root_cause = report.get("primary_root_cause_code")
    source_text = " ".join(
        str(value)
        for value in [
            report.get("failure_event_id"),
            report.get("notes"),
            *report.get("source_evidence_ids", []),
        ]
    ).lower()
    execution_marked = any(marker in source_text for marker in ORDER_FAILURE_EXECUTION_MARKERS)

    if execution_marked and primary_root_cause not in ORDER_FAILURE_EXECUTION_ROOT_CAUSES:
        errors.append("known execution failure evidence cannot remain outside execution failure taxonomy")
    if execution_marked and report.get("root_cause_status") != "KNOWN":
        errors.append("known execution failure evidence requires root_cause_status=KNOWN")
    if execution_marked and report.get("optimizer_ranking_action") == "ALLOW_RANKING":
        errors.append("known execution failure evidence must not allow ranking")
    if execution_marked and report.get("blocks_promotion") is not True:
        errors.append("known execution failure evidence must block promotion")
    if execution_marked and report.get("memory_write_status") != "APPEND_ONLY_RECORDED":
        errors.append("known execution failure evidence must be appended to failure memory")

    if primary_root_cause == "SLIPPAGE_DIVERGENCE":
        if "slippage" not in source_text:
            errors.append("SLIPPAGE_DIVERGENCE failure must link slippage evidence")
        if "EXECUTION_FEEDBACK_DIVERGENT" not in blocker_codes:
            errors.append("SLIPPAGE_DIVERGENCE failure must carry EXECUTION_FEEDBACK_DIVERGENT blocker")
        if report.get("recommended_response") not in {
            "PENALIZE_RANKING",
            "BLOCK_CANDIDATE",
            "RECHECK_COST_MODEL",
            "RETIRE_CANDIDATE",
        }:
            errors.append("SLIPPAGE_DIVERGENCE failure must recommend a ranking penalty, cost recheck, block, or retire action")

    if primary_root_cause in ORDER_FAILURE_EXECUTION_ROOT_CAUSES and not report.get("source_evidence_ids"):
        errors.append("execution failure taxonomy requires source_evidence_ids")
    return errors


def _overfit_diagnostic_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    errors: list[str] = []
    if schema is None:
        return ["overfit diagnostic report schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "promotion_eligible"):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"overfit diagnostic report has forbidden true field: {field}")
    if report.get("mode") == "LIVE":
        errors.append("overfit diagnostic report mode LIVE is forbidden before independent live-enabling evidence")
    if report.get("dashboard_display_truth_only") is not True:
        errors.append("overfit diagnostic report must be marked dashboard_display_truth_only=true")

    blockers = report.get("blockers", [])
    robustness_eligible = report.get("robustness_eligible") is True
    if robustness_eligible:
        if report.get("diagnostic_status") != "ROBUST_FOR_PAPER_REVIEW":
            errors.append("robustness_eligible requires diagnostic_status=ROBUST_FOR_PAPER_REVIEW")
        if blockers:
            errors.append("robustness_eligible diagnostic must not carry blockers")
        for field, expected in OVERFIT_REQUIRED_PASS_STATUSES.items():
            if report.get(field) != expected:
                errors.append(f"{field} must be {expected} before robustness eligibility")
        if report.get("overfit_status") != "LOW":
            errors.append("overfit_status must be LOW before robustness eligibility")
        if report.get("concentration_risk_status") != "LOW":
            errors.append("concentration_risk_status must be LOW before robustness eligibility")
        if int(report["sample_count"]) < int(report["min_required_sample_count"]):
            errors.append("sample_count below min_required_sample_count while robustness_eligible=true")
        if int(report["train_window_count"]) <= 0:
            errors.append("train_window_count must be positive while robustness_eligible=true")
        if int(report["oos_window_count"]) <= 0:
            errors.append("oos_window_count must be positive while robustness_eligible=true")
        if int(report["walk_forward_window_count"]) <= 0:
            errors.append("walk_forward_window_count must be positive while robustness_eligible=true")
        if int(report["bootstrap_iteration_count"]) < int(report["min_required_bootstrap_iterations"]):
            errors.append("bootstrap_iteration_count below min_required_bootstrap_iterations while robustness_eligible=true")
        if float(report["oos_net_ev_after_cost_bps"]) < float(report["min_required_oos_net_ev_bps"]):
            errors.append("oos_net_ev_after_cost_bps below min_required_oos_net_ev_bps while robustness_eligible=true")
        if float(report["oos_degradation_bps"]) > float(report["max_allowed_oos_degradation_bps"]):
            errors.append("oos_degradation_bps above max_allowed_oos_degradation_bps while robustness_eligible=true")
        if float(report["walk_forward_pass_rate"]) < float(report["min_required_walk_forward_pass_rate"]):
            errors.append("walk_forward_pass_rate below min_required_walk_forward_pass_rate while robustness_eligible=true")
        if float(report["bootstrap_confidence_lower_bps"]) < float(report["min_required_bootstrap_confidence_lower_bps"]):
            errors.append(
                "bootstrap_confidence_lower_bps below min_required_bootstrap_confidence_lower_bps while robustness_eligible=true"
            )
        if float(report["ranking_stability_score"]) < float(report["min_required_ranking_stability_score"]):
            errors.append("ranking_stability_score below min_required_ranking_stability_score while robustness_eligible=true")
    else:
        if report.get("diagnostic_status") == "ROBUST_FOR_PAPER_REVIEW":
            errors.append("diagnostic_status cannot be ROBUST_FOR_PAPER_REVIEW when robustness_eligible=false")
        if not blockers:
            errors.append("non-eligible overfit diagnostic must carry explicit blocker evidence")

    if report.get("overfit_status") == "HIGH" and not any(
        blocker.get("code") == "OVERFIT_RISK_HIGH" for blocker in blockers
    ):
        errors.append("HIGH overfit_status must carry OVERFIT_RISK_HIGH blocker")
    if report.get("bootstrap_status") in {"FAIL", "BLOCKED", "UNTESTED", "STALE"} and not any(
        blocker.get("code") == "BOOTSTRAP_UNSTABLE" for blocker in blockers
    ):
        errors.append("non-PASS bootstrap_status must carry BOOTSTRAP_UNSTABLE blocker")
    if report.get("oos_status") in {"FAIL", "BLOCKED", "UNTESTED", "STALE"} and not any(
        blocker.get("code") == "OOS_MISSING" for blocker in blockers
    ):
        errors.append("non-PASS oos_status must carry OOS_MISSING blocker")

    return errors


def _rolling_window_default_errors(report: dict[str, Any]) -> list[str]:
    errors = list(_overfit_diagnostic_errors(report))
    if report.get("robustness_eligible") is not True:
        return errors

    default_minimums = {
        "sample_count": ROLLING_WINDOW_DEFAULT_MIN_SAMPLE_COUNT,
        "min_required_sample_count": ROLLING_WINDOW_DEFAULT_MIN_SAMPLE_COUNT,
        "train_window_count": ROLLING_WINDOW_DEFAULT_MIN_TRAIN_WINDOWS,
        "oos_window_count": ROLLING_WINDOW_DEFAULT_MIN_OOS_WINDOWS,
        "walk_forward_window_count": ROLLING_WINDOW_DEFAULT_MIN_WALK_FORWARD_WINDOWS,
        "bootstrap_iteration_count": ROLLING_WINDOW_DEFAULT_MIN_BOOTSTRAP_ITERATIONS,
        "min_required_bootstrap_iterations": ROLLING_WINDOW_DEFAULT_MIN_BOOTSTRAP_ITERATIONS,
    }
    for field, minimum in default_minimums.items():
        try:
            value = int(report[field])
        except (KeyError, TypeError, ValueError):
            continue
        if value < minimum:
            errors.append(f"{field} below rolling default minimum {minimum}")

    source_evidence_ids = report.get("source_evidence_ids", [])
    if not isinstance(source_evidence_ids, list) or len(source_evidence_ids) < ROLLING_WINDOW_DEFAULT_MIN_SOURCE_EVIDENCE_IDS:
        errors.append(
            "rolling window default requires at least "
            f"{ROLLING_WINDOW_DEFAULT_MIN_SOURCE_EVIDENCE_IDS} source_evidence_ids"
        )

    unusable_statuses = {"UNTESTED", "STALE", "TIMEOUT"}
    for field in OVERFIT_REQUIRED_PASS_STATUSES:
        status = report.get(field)
        if status in unusable_statuses:
            errors.append(f"{field} cannot be {status} for rolling window default")

    return errors


def _candidate_scorecard_net_ev_errors(scorecard: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.candidate_scorecard.v1")
    if schema is None:
        return ["candidate_scorecard schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(scorecard, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(scorecard.get(field)):
            errors.append(f"candidate scorecard has forbidden live or scale flag: {field}")
    if scorecard.get("mode") == "LIVE":
        errors.append("candidate scorecard mode LIVE is forbidden before independent live-enabling evidence")

    gross = float(scorecard["gross_expected_edge_bps"])
    expected_cost = sum(float(scorecard[field]) for field in CANDIDATE_SCORECARD_COST_FIELDS)
    expected_net = gross - expected_cost
    actual_net = float(scorecard["net_ev_after_cost_bps"])
    if abs(actual_net - expected_net) > 0.000001:
        errors.append(
            "net_ev_after_cost_bps mismatch: "
            f"gross_expected_edge_bps - costs = {expected_net}, got {actual_net}"
        )

    blockers = scorecard.get("blockers", [])
    ranking_eligible = scorecard.get("ranking_eligible") is True
    warning_lower = str(scorecard.get("operator_warning", "")).lower()
    if "not live_ready" not in warning_lower or "live orders" not in warning_lower:
        errors.append("candidate scorecard warning must state not LIVE_READY and live orders blocked")
    if ranking_eligible and blockers:
        errors.append("ranking_eligible scorecard must not carry blockers")
    if not ranking_eligible and not blockers:
        errors.append("non-ranking scorecard must carry explicit blocker evidence")
    if ranking_eligible and scorecard.get("scorecard_scope") != "PAPER_SCORECARD_INPUT_ONLY":
        errors.append("ranking_eligible scorecard must remain PAPER_SCORECARD_INPUT_ONLY")
    if not ranking_eligible and scorecard.get("scorecard_scope") == "PAPER_SCORECARD_INPUT_ONLY":
        errors.append("PAPER_SCORECARD_INPUT_ONLY scorecard must be ranking_eligible")

    if ranking_eligible:
        min_required = float(scorecard["min_required_edge_bps"])
        if actual_net < min_required:
            errors.append("net_ev_after_cost_bps below min_required_edge_bps while ranking_eligible=true")
        source_ids = scorecard.get("source_evidence_ids", [])
        expected_runtime_source = runtime_cycle_source_evidence_id(
            str(scorecard.get("source_runtime_cycle_id", "")),
            str(scorecard.get("source_runtime_cycle_hash", "")),
        )
        if expected_runtime_source not in source_ids:
            errors.append("ranking_eligible scorecard requires source runtime cycle id and hash evidence")
        binding = runtime_cycle_binding_from_source_ids(source_ids)
        if binding != (scorecard.get("source_runtime_cycle_id"), scorecard.get("source_runtime_cycle_hash")):
            errors.append("ranking_eligible scorecard source evidence must match source_runtime_cycle_id and source_runtime_cycle_hash")
        if len(source_ids) < len(ROBUSTNESS_SOURCE_PREFIXES) + 1:
            errors.append("ranking_eligible scorecard requires runtime, OOS, walk-forward, and bootstrap source evidence ids")
        if not has_required_robustness_source_ids(
            source_ids,
            cycle_id=str(scorecard.get("source_runtime_cycle_id", "")),
            cycle_hash=str(scorecard.get("source_runtime_cycle_hash", "")),
        ):
            errors.append("ranking_eligible scorecard requires OOS, walk-forward, and bootstrap source evidence ids linked to the same runtime cycle hash")
        required_statuses = {
            "cost_model_status": "VALIDATED",
            "oos_status": "PASS",
            "walk_forward_status": "PASS",
            "bootstrap_status": "PASS",
            "overfit_status": "LOW",
        }
        for field, expected in required_statuses.items():
            if scorecard.get(field) != expected:
                errors.append(f"{field} must be {expected} before ranking eligibility")

    return errors


def candidate_scorecard_net_ev_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "candidate_scorecard.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "candidate_scorecard_net_ev_pass.json"
    raw_cost_fail_path = fixture_dir / "candidate_scorecard_net_ev_raw_cost_fail.json"
    live_flag_fail_path = fixture_dir / "candidate_scorecard_net_ev_live_flag_fail.json"
    oos_missing_fail_path = fixture_dir / "candidate_scorecard_net_ev_missing_oos_fail.json"
    live_ready_wording_fail_path = fixture_dir / "candidate_scorecard_net_ev_live_ready_wording_fail.json"
    missing_robustness_sources_path = fixture_dir / "candidate_scorecard_net_ev_missing_robustness_sources_fail.json"
    mismatched_robustness_sources_path = fixture_dir / "candidate_scorecard_net_ev_mismatched_robustness_sources_fail.json"
    paths = [
        schema_path,
        pass_path,
        raw_cost_fail_path,
        live_flag_fail_path,
        oos_missing_fail_path,
        live_ready_wording_fail_path,
        missing_robustness_sources_path,
        mismatched_robustness_sources_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "candidate_scorecard_net_ev_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _candidate_scorecard_net_ev_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "candidate_scorecard_net_ev_validator",
            f"PASS fixture failed net EV scorecard validation: {pass_errors[0]}",
            paths,
            "SCORECARD_SCHEMA_INVALID",
        )

    negative_expectations = {
        raw_cost_fail_path: "net_ev_after_cost_bps below min_required_edge_bps",
        live_flag_fail_path: "expected const False",
        oos_missing_fail_path: "oos_status must be PASS",
        live_ready_wording_fail_path: "candidate scorecard warning must state not LIVE_READY",
        missing_robustness_sources_path: "requires OOS, walk-forward, and bootstrap source evidence ids",
        mismatched_robustness_sources_path: "linked to the same runtime cycle hash",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _candidate_scorecard_net_ev_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "candidate_scorecard_net_ev_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "SCORECARD_SCHEMA_INVALID",
            )

    return pass_result(
        "candidate_scorecard_net_ev_validator",
        "candidate scorecards require cost-adjusted net EV, robustness status, explicit blockers, and false live flags",
        paths,
    )


def candidate_scorecard_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "candidate_scorecard.schema.json"
    builder_path = ROOT / "trader1" / "research" / "profitability" / "candidate_scorecard.py"
    builder_test_path = ROOT / "tests" / "research" / "test_candidate_scorecard_from_runtime.py"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    pass_path = fixture_dir / "candidate_scorecard_net_ev_pass.json"
    raw_cost_fail_path = fixture_dir / "candidate_scorecard_net_ev_raw_cost_fail.json"
    live_flag_fail_path = fixture_dir / "candidate_scorecard_net_ev_live_flag_fail.json"
    oos_missing_fail_path = fixture_dir / "candidate_scorecard_net_ev_missing_oos_fail.json"
    missing_robustness_sources_path = fixture_dir / "candidate_scorecard_net_ev_missing_robustness_sources_fail.json"
    mismatched_robustness_sources_path = fixture_dir / "candidate_scorecard_net_ev_mismatched_robustness_sources_fail.json"
    paths = [
        schema_path,
        builder_path,
        builder_test_path,
        pass_path,
        raw_cost_fail_path,
        live_flag_fail_path,
        oos_missing_fail_path,
        missing_robustness_sources_path,
        mismatched_robustness_sources_path,
    ]

    pass_scorecard = load_json(pass_path)
    pass_errors = _candidate_scorecard_net_ev_errors(pass_scorecard)
    if pass_errors:
        return fail_result(
            "candidate_scorecard_validator",
            f"PASS fixture failed candidate scorecard validation: {pass_errors[0]}",
            paths,
            "SCORECARD_SCHEMA_INVALID",
        )

    tampered_no_evidence = json.loads(json.dumps(pass_scorecard))
    tampered_no_evidence["source_evidence_ids"] = []
    if not any("source_evidence_ids" in error for error in _candidate_scorecard_net_ev_errors(tampered_no_evidence)):
        return fail_result(
            "candidate_scorecard_validator",
            "candidate scorecard without source evidence ids was not rejected",
            paths,
            "SCORECARD_MISSING",
        )

    tampered_scope = json.loads(json.dumps(pass_scorecard))
    tampered_scope["scorecard_scope"] = "BLOCKED_RESEARCH_ONLY"
    if "ranking_eligible scorecard must remain PAPER_SCORECARD_INPUT_ONLY" not in _candidate_scorecard_net_ev_errors(tampered_scope):
        return fail_result(
            "candidate_scorecard_validator",
            "ranking-eligible scorecard with non-paper scope was not rejected",
            paths,
            "SCORECARD_SCHEMA_INVALID",
        )

    runtime_report = build_upbit_paper_runtime_cycle_report(cycle_id="validator-candidate-scorecard-runtime-source")
    runtime_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime_report)
    runtime_errors = _candidate_scorecard_net_ev_errors(runtime_scorecard)
    if runtime_errors:
        return fail_result(
            "candidate_scorecard_validator",
            f"runtime-generated candidate scorecard failed validation: {runtime_errors[0]}",
            paths,
            "SCORECARD_SCHEMA_INVALID",
        )
    if runtime_scorecard.get("ranking_eligible") is True or runtime_scorecard.get("scorecard_scope") == "PAPER_SCORECARD_INPUT_ONLY":
        return fail_result(
            "candidate_scorecard_validator",
            "single runtime-generated scorecard attempted paper ranking eligibility before robustness evidence",
            paths,
            "SCORECARD_MISSING",
        )
    runtime_blocker_codes = {blocker.get("code") for blocker in runtime_scorecard.get("blockers", []) if isinstance(blocker, dict)}
    if not {"OOS_MISSING", "WALK_FORWARD_MISSING", "BOOTSTRAP_UNSTABLE", "OVERFIT_RISK_HIGH"}.issubset(runtime_blocker_codes):
        return fail_result(
            "candidate_scorecard_validator",
            "runtime-generated scorecard did not preserve robustness blockers",
            paths,
            "SCORECARD_MISSING",
        )
    if (
        runtime_scorecard.get("live_order_ready")
        or runtime_scorecard.get("live_order_allowed")
        or runtime_scorecard.get("can_live_trade")
        or runtime_scorecard.get("scale_up_allowed")
    ):
        return fail_result(
            "candidate_scorecard_validator",
            "runtime-generated candidate scorecard created forbidden live or scale permission",
            paths,
            "LIVE_FINAL_GUARD_FAILED",
        )

    negative_expectations = {
        raw_cost_fail_path: "net_ev_after_cost_bps below min_required_edge_bps",
        live_flag_fail_path: "expected const False",
        oos_missing_fail_path: "oos_status must be PASS",
        missing_robustness_sources_path: "requires OOS, walk-forward, and bootstrap source evidence ids",
        mismatched_robustness_sources_path: "linked to the same runtime cycle hash",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _candidate_scorecard_net_ev_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "candidate_scorecard_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "SCORECARD_SCHEMA_INVALID",
            )

    return pass_result(
        "candidate_scorecard_validator",
        "candidate scorecards are evidence-bound, paper-scorecard-input-only, cost-adjusted, robustness-gated, and non-live",
        paths,
    )


def ranking_stability_validator() -> ValidatorResult:
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    overfit_pass_path = fixture_dir / "overfit_diagnostic_pass.json"
    overfit_short_window_path = fixture_dir / "overfit_diagnostic_short_window_fail.json"
    optimizer_config_path = fixture_dir / "profit_optimizer_config_pass.json"
    paths = [
        ROOT / "contracts" / "schema" / "overfit_diagnostic_report.schema.json",
        ROOT / "contracts" / "schema" / "profit_optimizer_config.schema.json",
        overfit_pass_path,
        overfit_short_window_path,
        optimizer_config_path,
    ]

    overfit_pass = load_json(overfit_pass_path)
    pass_errors = _overfit_diagnostic_errors(overfit_pass)
    if pass_errors:
        return fail_result(
            "ranking_stability_validator",
            f"PASS fixture failed ranking stability validation: {pass_errors[0]}",
            paths,
            "RANKING_UNSTABLE",
        )
    config_errors = _profit_optimizer_config_errors(load_json(optimizer_config_path))
    if config_errors:
        return fail_result(
            "ranking_stability_validator",
            f"optimizer config failed ranking stability dependency validation: {config_errors[0]}",
            paths,
            "RANKING_UNSTABLE",
        )

    low_score = json.loads(json.dumps(overfit_pass))
    low_score["ranking_stability_score"] = float(low_score["min_required_ranking_stability_score"]) - 0.01
    if "ranking_stability_score below min_required_ranking_stability_score while robustness_eligible=true" not in _overfit_diagnostic_errors(low_score):
        return fail_result(
            "ranking_stability_validator",
            "low ranking_stability_score was not rejected",
            paths,
            "RANKING_UNSTABLE",
        )

    failed_status = json.loads(json.dumps(overfit_pass))
    failed_status["ranking_stability_status"] = "FAIL"
    if "ranking_stability_status must be PASS before robustness eligibility" not in _overfit_diagnostic_errors(failed_status):
        return fail_result(
            "ranking_stability_validator",
            "non-PASS ranking_stability_status was not rejected",
            paths,
            "RANKING_UNSTABLE",
        )

    short_window_errors = _overfit_diagnostic_errors(load_json(overfit_short_window_path))
    if not any("sample_count below min_required_sample_count" in error for error in short_window_errors):
        return fail_result(
            "ranking_stability_validator",
            "short-window ranking stability fixture was not rejected",
            paths,
            "SAMPLE_INSUFFICIENT",
        )

    config_without_required_stability = load_json(optimizer_config_path)
    config_without_required_stability["ranking_policy"]["ranking_stability_required"] = False
    config_without_stability_errors = _profit_optimizer_config_errors(config_without_required_stability)
    if not any(
        "profit optimizer config ranking policy must require ranking stability" in error
        or "ranking_stability_required" in error
        for error in config_without_stability_errors
    ):
        return fail_result(
            "ranking_stability_validator",
            "optimizer config without required ranking stability was not rejected",
            paths,
            "RANKING_UNSTABLE",
        )

    return pass_result(
        "ranking_stability_validator",
        "ranking stability requires optimizer policy enforcement plus PASS status, sufficient samples, and score above threshold before paper ranking review",
        paths,
    )


def rolling_window_default_validator() -> ValidatorResult:
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "rolling_window_default_pass.json"
    short_window_path = fixture_dir / "overfit_diagnostic_short_window_fail.json"
    train_window_path = fixture_dir / "rolling_window_default_train_window_fail.json"
    oos_window_path = fixture_dir / "rolling_window_default_oos_window_fail.json"
    walk_forward_path = fixture_dir / "rolling_window_default_walk_forward_fail.json"
    source_evidence_path = fixture_dir / "rolling_window_default_source_evidence_fail.json"
    stale_status_path = fixture_dir / "rolling_window_default_stale_status_fail.json"
    paths = [
        ROOT / "contracts" / "schema" / "overfit_diagnostic_report.schema.json",
        state_path,
        pass_path,
        short_window_path,
        train_window_path,
        oos_window_path,
        walk_forward_path,
        source_evidence_path,
        stale_status_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "rolling_window_default_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    dependency = ranking_stability_validator().as_dict()
    if dependency["status"] != "PASS":
        return fail_result(
            "rolling_window_default_validator",
            f"ranking stability dependency did not pass: {dependency['status']}",
            paths,
            "RANKING_UNSTABLE",
        )

    pass_errors = _rolling_window_default_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "rolling_window_default_validator",
            f"PASS fixture failed rolling window default validation: {pass_errors[0]}",
            paths,
            "SAMPLE_INSUFFICIENT",
        )

    negative_expectations = {
        short_window_path: "sample_count below rolling default minimum",
        train_window_path: "train_window_count below rolling default minimum",
        oos_window_path: "oos_window_count below rolling default minimum",
        walk_forward_path: "walk_forward_window_count below rolling default minimum",
        source_evidence_path: "rolling window default requires at least 3 source_evidence_ids",
        stale_status_path: "oos_status cannot be STALE for rolling window default",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _rolling_window_default_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "rolling_window_default_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "SAMPLE_INSUFFICIENT",
            )

    return pass_result(
        "rolling_window_default_validator",
        "rolling window defaults require minimum samples, train/OOS/walk-forward windows, bootstrap iterations, independent evidence ids, fresh PASS statuses, and false live flags before paper/shadow ranking review",
        paths,
    )


def parameter_bound_validator() -> ValidatorResult:
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    pass_path = fixture_dir / "parameter_narrowing_pass.json"
    over_narrow_path = fixture_dir / "parameter_narrowing_over_narrow_fail.json"
    live_source_path = fixture_dir / "parameter_narrowing_live_source_fail.json"
    paths = [
        ROOT / "contracts" / "schema" / "parameter_narrowing_report.schema.json",
        pass_path,
        over_narrow_path,
        live_source_path,
    ]

    report = load_json(pass_path)
    pass_errors = _parameter_narrowing_errors(report)
    if pass_errors:
        return fail_result(
            "parameter_bound_validator",
            f"PASS fixture failed parameter bound validation: {pass_errors[0]}",
            paths,
            "PARAMETER_NARROWING_UNVERIFIED",
        )

    expanded_bounds = json.loads(json.dumps(report))
    expanded_bounds["parameter_changes"][0]["proposed_min"] = expanded_bounds["parameter_changes"][0]["previous_min"] - 1
    if "parameter change 0 expands bounds while marked NARROW" not in _parameter_narrowing_errors(expanded_bounds):
        return fail_result(
            "parameter_bound_validator",
            "parameter bound expansion marked NARROW was not rejected",
            paths,
            "EXPANDED_BOUND_UNVERIFIED",
        )

    expanded_count = json.loads(json.dumps(report))
    expanded_count["parameter_count_after"] = int(expanded_count["parameter_count_before"]) + 1
    if "parameter narrowing cannot expand parameter_count_after beyond parameter_count_before" not in _parameter_narrowing_errors(expanded_count):
        return fail_result(
            "parameter_bound_validator",
            "parameter_count_after expansion was not rejected",
            paths,
            "EXPANDED_BOUND_UNVERIFIED",
        )

    over_narrow_errors = _parameter_narrowing_errors(load_json(over_narrow_path))
    if not any("narrowing_pct exceeds max_narrowing_pct" in error for error in over_narrow_errors):
        return fail_result(
            "parameter_bound_validator",
            "over-narrowing fixture was not rejected",
            paths,
            "PARAMETER_NARROWING_UNVERIFIED",
        )

    live_source_errors = _parameter_narrowing_errors(load_json(live_source_path))
    if not any("LIVE" in error for error in live_source_errors):
        return fail_result(
            "parameter_bound_validator",
            "LIVE source mode in parameter narrowing was not rejected",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    return pass_result(
        "parameter_bound_validator",
        "parameter bounds may narrow only within previous ranges, never expand candidate search, never over-narrow, and never use LIVE sources",
        paths,
    )


def promotion_threshold_validator() -> ValidatorResult:
    registry_path = ROOT / "contracts" / "registry.yaml"
    module_path = ROOT / "trader1" / "runtime" / "readiness" / "live_ready_snapshot.py"
    paths = [
        registry_path,
        ROOT / "contracts" / "schema" / "live_ready_candidate_writer_input.schema.json",
        module_path,
    ]
    writer_input = build_writer_input(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        strategy_id="mvp4_strategy",
        strategy_build_id="mvp4_strategy_build",
        parameter_hash="A" * 64,
        risk_profile="CONSERVATIVE",
        registry_hash=sha256_file(registry_path),
        schema_bundle_hash=sha256_file(ROOT / "contracts" / "schema" / "common.defs.schema.json"),
        source_tree_hash=sha256_file(module_path),
        writer_input_id="mvp4_promotion_threshold_validator_input",
    )

    not_pass = dict(writer_input)
    not_pass["promotion_threshold_status"] = "FAIL"
    not_pass["live_ready_snapshot_writer_status"] = "PASS"
    not_pass["blockers"] = []
    not_pass = attach_writer_input_hash(not_pass)
    not_pass_result = evaluate_live_ready_snapshot_writer(not_pass, evidence_manifest_present=True)
    if not_pass_result.blocker_code != "PROMOTION_INPUT_TYPE_INVALID" or not_pass_result.would_write_snapshot:
        return fail_result(
            "promotion_threshold_validator",
            "non-PASS promotion threshold did not block LIVE_READY writer input",
            paths,
            "PROMOTION_INPUT_TYPE_INVALID",
        )

    pass_but_not_enabled = dict(writer_input)
    pass_but_not_enabled["promotion_threshold_status"] = "PASS"
    pass_but_not_enabled["live_ready_snapshot_writer_status"] = "PASS"
    pass_but_not_enabled["blockers"] = []
    pass_but_not_enabled["evidence_manifest_hash"] = "E" * 64
    pass_but_not_enabled = attach_writer_input_hash(pass_but_not_enabled)
    pass_result_eval = evaluate_live_ready_snapshot_writer(pass_but_not_enabled, evidence_manifest_present=True)
    if pass_result_eval.would_write_snapshot or pass_result_eval.live_order_ready or pass_result_eval.live_order_allowed:
        return fail_result(
            "promotion_threshold_validator",
            "PASS promotion threshold created live readiness outside LIVE_ENABLING_PATCH",
            paths,
            "LIVE_FINAL_GUARD_FAILED",
        )
    if pass_result_eval.blocker_code != "LIVE_READY_SNAPSHOT_WRITER_UNTESTED":
        return fail_result(
            "promotion_threshold_validator",
            "promotion threshold PASS did not remain blocked outside LIVE_ENABLING_PATCH",
            paths,
            "LIVE_READY_SNAPSHOT_WRITER_UNTESTED",
        )

    missing_cost = dict(pass_but_not_enabled)
    missing_cost["cost_after_edge_status"] = "FAIL"
    missing_cost = attach_writer_input_hash(missing_cost)
    missing_cost_result = evaluate_live_ready_snapshot_writer(missing_cost, evidence_manifest_present=True)
    if missing_cost_result.blocker_code != "COST_AFTER_EDGE_UNVERIFIED":
        return fail_result(
            "promotion_threshold_validator",
            "cost-after-edge FAIL did not block promotion threshold writer input",
            paths,
            "COST_AFTER_EDGE_UNVERIFIED",
        )

    return pass_result(
        "promotion_threshold_validator",
        "promotion threshold rejects non-PASS thresholds and still cannot write LIVE_READY or enable live orders without independent LIVE_ENABLING evidence",
        paths,
    )


def _strategy_condition_matrix_errors(matrix: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(matrix, schema_bundle)
    errors: list[str] = []
    if schema is None:
        return ["strategy condition matrix schema not found"]
    instance_result = validate_instance_against_schema(matrix, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "promotion_eligible"):
        if _live_flag_is_true(matrix.get(field)):
            errors.append(f"strategy condition matrix has forbidden true field: {field}")
    if matrix.get("mode") == "LIVE":
        errors.append("strategy condition matrix mode LIVE is forbidden before independent live-enabling evidence")
    if matrix.get("dashboard_display_truth_only") is not True:
        errors.append("strategy condition matrix must be marked dashboard_display_truth_only=true")

    rows = matrix.get("condition_rows", [])
    families = {row.get("strategy_family") for row in rows}
    regimes = {row.get("regime_family") for row in rows}
    declared_families = set(matrix.get("required_strategy_families", []))
    declared_regimes = set(matrix.get("required_regime_families", []))
    missing_families = sorted(STRATEGY_CONDITION_REQUIRED_FAMILIES - families)
    missing_regimes = sorted(STRATEGY_CONDITION_REQUIRED_REGIMES - regimes)
    if missing_families:
        errors.append(f"condition matrix missing strategy families: {missing_families}")
    if missing_regimes:
        errors.append(f"condition matrix missing regime families: {missing_regimes}")
    if not STRATEGY_CONDITION_REQUIRED_FAMILIES.issubset(declared_families):
        errors.append("required_strategy_families must include VWAP_REVERSION, TREND_PULLBACK, and BREAKOUT_RETEST")
    if not STRATEGY_CONDITION_REQUIRED_REGIMES.issubset(declared_regimes):
        errors.append("required_regime_families must include TRENDING, RANGE, and RISK_OFF")

    global_no_trade = set(matrix.get("global_no_trade_reasons", []))
    missing_no_trade = sorted(STRATEGY_CONDITION_REQUIRED_GLOBAL_NO_TRADE - global_no_trade)
    if missing_no_trade:
        errors.append(f"global_no_trade_reasons missing required blockers: {missing_no_trade}")

    for row in rows:
        condition_id = row.get("condition_id", "<unknown>")
        entry_conditions = row.get("entry_conditions", [])
        exit_conditions = row.get("exit_conditions", [])
        no_trade_reasons = set(row.get("no_trade_reasons", []))
        if row.get("regime_family") == "RISK_OFF":
            if row.get("entry_allowed") is not False:
                errors.append(f"{condition_id}: RISK_OFF row must set entry_allowed=false")
            if row.get("risk_off_blocks_entry") is not True:
                errors.append(f"{condition_id}: RISK_OFF row must set risk_off_blocks_entry=true")
            if "REGIME_MISMATCH" not in no_trade_reasons and "RISK_VETO" not in no_trade_reasons:
                errors.append(f"{condition_id}: RISK_OFF row must carry REGIME_MISMATCH or RISK_VETO no-trade reason")
        else:
            if row.get("entry_allowed") is not True:
                errors.append(f"{condition_id}: non-risk-off row must set entry_allowed=true")
            if not entry_conditions:
                errors.append(f"{condition_id}: entry_allowed row must list entry_conditions")
            if not exit_conditions:
                errors.append(f"{condition_id}: entry_allowed row must list exit_conditions")
            if "MIN_EDGE_FAIL" not in no_trade_reasons:
                errors.append(f"{condition_id}: entry row must include MIN_EDGE_FAIL no-trade guard")
            if row.get("downtrend_avoidance_required") is not True:
                errors.append(f"{condition_id}: entry row must require downtrend avoidance")
            min_edge_bps = float(row.get("min_edge_bps", 0))
            expected_friction_bps = float(row.get("max_expected_slippage_bps", 0)) + float(
                row.get("max_spread_bps", 0)
            )
            if min_edge_bps <= expected_friction_bps:
                errors.append(
                    f"{condition_id}: min_edge_bps must exceed max_expected_slippage_bps plus max_spread_bps "
                    "for entry_allowed rows"
                )
        if not no_trade_reasons:
            errors.append(f"{condition_id}: no_trade_reasons must not be empty")

    if matrix.get("matrix_status") != "BLOCKED" and not matrix.get("source_evidence_ids"):
        errors.append("non-blocked condition matrix must carry source_evidence_ids")
    return errors


def strategy_condition_matrix_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "strategy_condition_matrix.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "strategy_condition_matrix_pass.json"
    missing_risk_off_path = fixture_dir / "strategy_condition_matrix_missing_risk_off_fail.json"
    live_flag_fail_path = fixture_dir / "strategy_condition_matrix_live_flag_fail.json"
    missing_no_trade_path = fixture_dir / "strategy_condition_matrix_missing_no_trade_fail.json"
    paths = [schema_path, pass_path, missing_risk_off_path, live_flag_fail_path, missing_no_trade_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "strategy_condition_matrix_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _strategy_condition_matrix_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "strategy_condition_matrix_validator",
            f"PASS fixture failed strategy condition validation: {pass_errors[0]}",
            paths,
            "STRATEGY_NOT_ELIGIBLE",
        )

    negative_expectations = {
        missing_risk_off_path: "condition matrix missing regime families",
        live_flag_fail_path: "expected const False",
        missing_no_trade_path: "global_no_trade_reasons missing required blockers",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _strategy_condition_matrix_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "strategy_condition_matrix_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "STRATEGY_NOT_ELIGIBLE",
            )

    return pass_result(
        "strategy_condition_matrix_validator",
        "strategy condition matrix requires entry, exit, no-trade, regime, risk-off, and false live flags",
        paths,
    )


def _symbol_strategy_regime_fit_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    errors: list[str] = []
    if schema is None:
        return ["symbol strategy regime fit schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "promotion_eligible"):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"symbol strategy regime fit report has forbidden true field: {field}")
    if report.get("mode") == "LIVE":
        errors.append("symbol strategy regime fit report mode LIVE is forbidden before independent live-enabling evidence")
    if report.get("dashboard_display_truth_only") is not True:
        errors.append("symbol strategy regime fit report must be marked dashboard_display_truth_only=true")

    supported = set(report.get("supported_strategy_families", []))
    rejected = set(report.get("rejected_strategy_families", []))
    overlap = sorted(supported & rejected)
    missing = sorted(SYMBOL_STRATEGY_REQUIRED_FAMILIES - (supported | rejected))
    if overlap:
        errors.append(f"strategy family cannot be both supported and rejected: {overlap}")
    if missing:
        errors.append(f"strategy family coverage missing: {missing}")

    blockers = report.get("blockers", [])
    blocker_codes = set(report.get("symbol_blocker_codes", []))
    paper_review_eligible = report.get("paper_review_eligible") is True
    fit_status = report.get("fit_status")
    if paper_review_eligible:
        if fit_status != "ELIGIBLE_FOR_PAPER_REVIEW":
            errors.append("paper_review_eligible requires fit_status=ELIGIBLE_FOR_PAPER_REVIEW")
        if blockers or blocker_codes:
            errors.append("paper_review_eligible report must not carry blockers")
        if report.get("regime_family") == "RISK_OFF":
            errors.append("RISK_OFF symbol-regime fit cannot be paper_review_eligible")
        if float(report["liquidity_score"]) < float(report["min_required_liquidity_score"]):
            errors.append("liquidity_score below min_required_liquidity_score while paper_review_eligible=true")
        if float(report["spread_bps"]) > float(report["max_allowed_spread_bps"]):
            errors.append("spread_bps above max_allowed_spread_bps while paper_review_eligible=true")
        if float(report["depth_score"]) < float(report["min_required_depth_score"]):
            errors.append("depth_score below min_required_depth_score while paper_review_eligible=true")
        if float(report["depth_notional_krw"]) <= 0:
            errors.append("depth_notional_krw must be positive while paper_review_eligible=true")
        if float(report["average_daily_value_krw"]) <= 0:
            errors.append("average_daily_value_krw must be positive while paper_review_eligible=true")
        if not supported:
            errors.append("paper_review_eligible report must support at least one strategy family")
    else:
        if fit_status == "ELIGIBLE_FOR_PAPER_REVIEW":
            errors.append("fit_status cannot be ELIGIBLE_FOR_PAPER_REVIEW when paper_review_eligible=false")
        if not blockers and not blocker_codes:
            errors.append("non-eligible symbol-regime report must carry explicit blocker evidence")

    if report.get("regime_family") == "RISK_OFF":
        if "REGIME_MISMATCH" not in blocker_codes and "RISK_VETO" not in blocker_codes:
            errors.append("RISK_OFF symbol-regime report must carry REGIME_MISMATCH or RISK_VETO blocker")
        if paper_review_eligible:
            errors.append("RISK_OFF symbol-regime report must remain not eligible for paper review")
    return errors


def symbol_strategy_regime_fit_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "symbol_strategy_regime_fit_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "symbol_strategy_regime_fit_pass.json"
    low_liquidity_path = fixture_dir / "symbol_strategy_regime_fit_low_liquidity_fail.json"
    high_spread_path = fixture_dir / "symbol_strategy_regime_fit_high_spread_fail.json"
    low_depth_path = fixture_dir / "symbol_strategy_regime_fit_low_depth_fail.json"
    live_flag_fail_path = fixture_dir / "symbol_strategy_regime_fit_live_flag_fail.json"
    missing_family_path = fixture_dir / "symbol_strategy_regime_fit_missing_family_fail.json"
    paths = [
        schema_path,
        pass_path,
        low_liquidity_path,
        high_spread_path,
        low_depth_path,
        live_flag_fail_path,
        missing_family_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "symbol_strategy_regime_fit_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _symbol_strategy_regime_fit_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "symbol_strategy_regime_fit_validator",
            f"PASS fixture failed symbol strategy regime fit validation: {pass_errors[0]}",
            paths,
            "REGIME_FIT_UNTESTED",
        )

    negative_expectations = {
        low_liquidity_path: "liquidity_score below min_required_liquidity_score",
        high_spread_path: "spread_bps above max_allowed_spread_bps",
        low_depth_path: "depth_score below min_required_depth_score",
        live_flag_fail_path: "expected const False",
        missing_family_path: "strategy family coverage missing",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _symbol_strategy_regime_fit_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "symbol_strategy_regime_fit_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "REGIME_FIT_UNTESTED",
            )

    return pass_result(
        "symbol_strategy_regime_fit_validator",
        "symbol strategy regime fit requires liquidity, volatility, spread, depth, regime, family coverage, and false live flags",
        paths,
    )


def _market_regime_adaptation_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    errors: list[str] = []
    if schema is None:
        return ["market regime adaptation schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    forbidden_true_fields = (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "active_snapshot_mutation_allowed",
        "optimizer_winner_live_config_allowed",
        "paper_winner_live_config_allowed",
        "execution_truth_created",
        "promotion_eligible",
    )
    for field in forbidden_true_fields:
        if _live_flag_is_true(report.get(field)):
            errors.append(f"market regime adaptation report has forbidden true field: {field}")
    if report.get("mode") == "LIVE":
        errors.append("market regime adaptation report mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("market regime adaptation report source_modes must not include LIVE")
    if report.get("live_observation_used") is True or report.get("read_only_live_observation_allowed") is True:
        errors.append("live observation is disabled for MVP-4 market regime adaptation")
    if report.get("official_api_verification_status") == "PASS":
        errors.append("official API PASS cannot be consumed by this non-live regime adaptation report")

    warning = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning or "live orders blocked" not in warning:
        errors.append("operator_warning must say not live_ready and live orders blocked")

    roles = {item.get("role") for item in report.get("source_artifact_roles", []) if isinstance(item, dict)}
    required_roles = {
        "MARKET_DATA_FRESHNESS",
        "SYMBOL_STRATEGY_REGIME_FIT",
        "STRATEGY_CONDITION_MATRIX",
        "STRATEGY_PERFORMANCE_MEMORY",
    }
    missing_roles = sorted(required_roles - roles)
    if missing_roles:
        errors.append(f"market regime adaptation missing source artifact roles: {missing_roles}")

    blockers = report.get("blockers", [])
    blocker_codes = {item.get("code") for item in blockers if isinstance(item, dict)}
    data_status = report.get("data_freshness_status")
    if data_status == "FRESH":
        if float(report.get("data_age_seconds", 0)) > float(report.get("max_data_age_seconds", 0)):
            errors.append("FRESH data_age_seconds must be <= max_data_age_seconds")
    else:
        if report.get("entry_allowed") is True:
            errors.append("entry_allowed must be false when regime data is not FRESH")
        if not blockers:
            errors.append("STALE or MISSING regime data requires blockers")

    if report.get("adaptation_signal") != "NO_SIGNAL" and report.get("adaptation_status") == "STABLE":
        errors.append("non-NO_SIGNAL adaptation cannot remain STABLE")

    dependency_fields = (
        "symbol_strategy_regime_fit_validator_status",
        "strategy_condition_matrix_validator_status",
        "strategy_performance_memory_validator_status",
    )
    if report.get("entry_allowed") is True:
        for field in dependency_fields:
            if report.get(field) != "PASS":
                errors.append(f"entry_allowed requires {field}=PASS")
        if blockers:
            errors.append("entry_allowed market regime adaptation must not carry blockers")
        if not report.get("recommended_strategy_families"):
            errors.append("entry_allowed market regime adaptation requires recommended_strategy_families")

    current_direction = report.get("current_trend_direction")
    if current_direction in {"DOWNTREND", "RISK_OFF"} or report.get("current_regime_family") == "RISK_OFF":
        if report.get("entry_allowed") is not False:
            errors.append(f"{current_direction} regime adaptation must set entry_allowed=false")
        if report.get("recommended_action") not in {"BLOCK_ENTRY", "SAFE_MODE"}:
            errors.append(f"{current_direction} regime adaptation must recommend BLOCK_ENTRY or SAFE_MODE")
        if report.get("primary_blocker_code") not in {"REGIME_MISMATCH", "RISK_VETO"}:
            errors.append(f"{current_direction} regime adaptation requires REGIME_MISMATCH or RISK_VETO primary blocker")
        if not {"REGIME_MISMATCH", "RISK_VETO"} & blocker_codes:
            errors.append(f"{current_direction} regime adaptation must carry REGIME_MISMATCH or RISK_VETO blocker")
        if not report.get("blocked_strategy_families"):
            errors.append(f"{current_direction} regime adaptation must list blocked_strategy_families")

    if report.get("adaptation_status") == "BLOCKED_SAFE_MODE" and not blockers:
        errors.append("BLOCKED_SAFE_MODE market regime adaptation requires blockers")
    return errors


def market_regime_adaptation_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "market_regime_adaptation_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "market_regime_adaptation_pass.json"
    live_flag_fail_path = fixture_dir / "market_regime_adaptation_live_flag_fail.json"
    stale_data_fail_path = fixture_dir / "market_regime_adaptation_stale_data_entry_fail.json"
    risk_off_fail_path = fixture_dir / "market_regime_adaptation_risk_off_entry_fail.json"
    live_observation_fail_path = fixture_dir / "market_regime_adaptation_live_observation_fail.json"
    missing_dependency_fail_path = fixture_dir / "market_regime_adaptation_missing_dependency_fail.json"
    missing_source_role_fail_path = fixture_dir / "market_regime_adaptation_missing_source_role_fail.json"
    paths = [
        schema_path,
        pass_path,
        live_flag_fail_path,
        stale_data_fail_path,
        risk_off_fail_path,
        live_observation_fail_path,
        missing_dependency_fail_path,
        missing_source_role_fail_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "market_regime_adaptation_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _market_regime_adaptation_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "market_regime_adaptation_validator",
            f"PASS fixture failed market regime adaptation validation: {pass_errors[0]}",
            paths,
            "REGIME_ADAPTATION_UNTESTED",
        )

    negative_expectations = {
        live_flag_fail_path: "expected const False",
        stale_data_fail_path: "entry_allowed must be false when regime data is not FRESH",
        risk_off_fail_path: "RISK_OFF regime adaptation must set entry_allowed=false",
        live_observation_fail_path: "expected const False",
        missing_dependency_fail_path: "entry_allowed requires symbol_strategy_regime_fit_validator_status=PASS",
        missing_source_role_fail_path: "market regime adaptation missing source artifact roles",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _market_regime_adaptation_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "market_regime_adaptation_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "REGIME_ADAPTATION_UNTESTED",
            )

    dependency_failures = _dependency_failures(
        [
            "symbol_strategy_regime_fit_validator",
            "strategy_condition_matrix_validator",
            "strategy_performance_memory_validator",
        ]
    )
    if dependency_failures:
        return blocked_result(
            "market_regime_adaptation_validator",
            "market regime adaptation remains blocked until dependencies pass: " + ", ".join(dependency_failures),
            paths,
            "REGIME_ADAPTATION_UNTESTED",
        )

    return pass_result(
        "market_regime_adaptation_validator",
        "market regime adaptation requires fresh scoped evidence, strategy/regime dependencies, downtrend and risk-off blocking, and false live flags",
        paths,
    )


def profitability_optimizer_evidence_gap_validator() -> ValidatorResult:
    audit_path = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json"
    maturity_rollup_path = (
        ROOT
        / "system"
        / "evidence"
        / "audit_reports"
        / "MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json"
    )
    contract_gap_path = (
        ROOT
        / "system"
        / "evidence"
        / "contract_gaps"
        / "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json"
    )
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    paths = [audit_path, maturity_rollup_path, contract_gap_path, state_path]
    if not audit_path.exists() or not maturity_rollup_path.exists() or not contract_gap_path.exists():
        return blocked_result(
            "profitability_optimizer_evidence_gap_validator",
            "profitability optimizer evidence maturity audit, rollup, or contract_gap is missing",
            paths,
            "CONTRACT_GAP_HIGH",
        )

    audit = load_json(audit_path)
    errors = _profitability_evidence_audit_errors(audit)
    if errors:
        return blocked_result(
            "profitability_optimizer_evidence_gap_validator",
            errors[0],
            paths,
            "CONTRACT_GAP_HIGH",
        )

    rollup_errors = _profitability_evidence_maturity_rollup_errors(load_json(maturity_rollup_path))
    if rollup_errors:
        return blocked_result(
            "profitability_optimizer_evidence_gap_validator",
            f"profitability evidence maturity rollup invalid: {rollup_errors[0]}",
            paths,
            "CONTRACT_GAP_HIGH",
        )

    contract_gap = load_json(contract_gap_path)
    if contract_gap.get("status") != "OPEN" or contract_gap.get("severity") not in {"HIGH", "CRITICAL"}:
        return blocked_result(
            "profitability_optimizer_evidence_gap_validator",
            "profitability evidence maturity contract_gap must remain open and high severity until evidence exists",
            paths,
            "CONTRACT_GAP_HIGH",
        )
    if contract_gap.get("live_affecting") is not True:
        return blocked_result(
            "profitability_optimizer_evidence_gap_validator",
            "profitability evidence maturity contract_gap must remain live-affecting",
            paths,
            "CONTRACT_GAP_HIGH",
        )

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "profitability_optimizer_evidence_gap_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    return pass_result(
        "profitability_optimizer_evidence_gap_validator",
        "profitability optimizer evidence gaps and maturity rollup are explicit, operator-visible, and live-blocking",
        paths,
    )


PROFIT_OPTIMIZER_REQUIRED_COST_COMPONENTS = {"FEE", "SPREAD", "SLIPPAGE", "IMPACT", "LATENCY"}
PROFIT_OPTIMIZER_REQUIRED_OBJECTIVE_COMPONENTS = {
    "NET_EV_AFTER_COST",
    "DRAWDOWN_PENALTY",
    "SLIPPAGE_PENALTY",
    "FEE_PENALTY",
    "SPREAD_PENALTY",
    "IMPACT_PENALTY",
    "LATENCY_PENALTY",
    "OVERFIT_PENALTY",
    "LIQUIDITY_DEPTH_SCORE",
    "REGIME_FIT_SCORE",
}


def _profit_optimizer_config_errors(config: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.profit_optimizer_config.v1")
    if schema is None:
        return ["profit_optimizer_config schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(config, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "order_submission_allowed",
        "exchange_account_call_allowed",
    ):
        if _live_flag_is_true(config.get(field)):
            errors.append(f"profit optimizer config has forbidden live, exchange, or scale field: {field}")
    if config.get("mode") == "LIVE":
        errors.append("profit optimizer config mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(config.get("allowed_source_modes", [])):
        errors.append("profit optimizer config allowed_source_modes must not include LIVE")

    if config.get("objective_basis") != "NET_EV_AFTER_COST":
        errors.append("profit optimizer config requires NET_EV_AFTER_COST objective basis")
    objective_components = {
        component.get("component_id")
        for component in config.get("objective_components", [])
        if isinstance(component, dict)
    }
    missing_objective_components = sorted(PROFIT_OPTIMIZER_REQUIRED_OBJECTIVE_COMPONENTS - objective_components)
    if missing_objective_components:
        errors.append(f"profit optimizer config missing required objective components: {missing_objective_components}")
    cost_components = set(config.get("cost_components", []))
    missing_cost_components = sorted(PROFIT_OPTIMIZER_REQUIRED_COST_COMPONENTS - cost_components)
    if missing_cost_components:
        errors.append(f"profit optimizer config missing required cost components: {missing_cost_components}")

    ranking_policy = config.get("ranking_policy", {})
    if ranking_policy.get("candidate_output_type") != "CANDIDATE_RANKING_INPUT":
        errors.append("profit optimizer config ranking policy must emit CANDIDATE_RANKING_INPUT")
    if ranking_policy.get("sort_key") != "NET_EV_AFTER_COST":
        errors.append("profit optimizer config ranking policy must sort by NET_EV_AFTER_COST")
    if ranking_policy.get("ranking_stability_required") is not True:
        errors.append("profit optimizer config ranking policy must require ranking stability")
    if int(ranking_policy.get("min_candidate_count", 0)) <= 0:
        errors.append("profit optimizer config ranking policy requires min_candidate_count > 0")

    promotion_policy = config.get("promotion_policy", {})
    for field in ("live_promotion_allowed", "live_ready_snapshot_write_allowed", "scale_up_allowed"):
        if _live_flag_is_true(promotion_policy.get(field)):
            errors.append(f"profit optimizer promotion policy has forbidden true field: {field}")
    for field in ("requires_oos_pass", "requires_walk_forward_pass", "requires_bootstrap_pass", "requires_operator_approval"):
        if promotion_policy.get(field) is not True:
            errors.append(f"profit optimizer promotion policy must require {field}")

    if config.get("dashboard_display_truth_only") is not True:
        errors.append("profit optimizer config must remain dashboard display truth only")
    warning_lower = str(config.get("operator_warning", "")).lower()
    if "not live_ready" not in warning_lower or "live orders" not in warning_lower:
        errors.append("profit optimizer config warning must state not LIVE_READY and live orders blocked")

    blockers = config.get("blockers", [])
    if config.get("status") == "PASS" and blockers:
        errors.append("PASS profit optimizer config must not carry blockers")
    if config.get("status") != "PASS" and not blockers:
        errors.append("non-PASS profit optimizer config must carry explicit blocker evidence")

    return errors


def profit_optimizer_config_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "profit_optimizer_config.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    pass_path = fixture_dir / "profit_optimizer_config_pass.json"
    live_flag_path = fixture_dir / "profit_optimizer_config_live_flag_fail.json"
    raw_pnl_path = fixture_dir / "profit_optimizer_config_raw_pnl_fail.json"
    live_source_path = fixture_dir / "profit_optimizer_config_live_source_fail.json"
    missing_cost_path = fixture_dir / "profit_optimizer_config_missing_cost_fail.json"
    live_writer_path = fixture_dir / "profit_optimizer_config_live_writer_fail.json"
    paths = [
        schema_path,
        pass_path,
        live_flag_path,
        raw_pnl_path,
        live_source_path,
        missing_cost_path,
        live_writer_path,
    ]

    pass_errors = _profit_optimizer_config_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "profit_optimizer_config_validator",
            f"PASS fixture failed profit optimizer config validation: {pass_errors[0]}",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    negative_expectations = {
        live_flag_path: "expected const False",
        raw_pnl_path: "RAW_PNL",
        live_source_path: "LIVE",
        missing_cost_path: "minItems 5",
        live_writer_path: "expected const False",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _profit_optimizer_config_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "profit_optimizer_config_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
            )

    return pass_result(
        "profit_optimizer_config_validator",
        "profit optimizer config is strict, non-live, net-EV-after-cost scoped, and cannot grant live readiness, order permission, or scale-up",
        paths,
    )


def objective_function_validator() -> ValidatorResult:
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    config_pass_path = fixture_dir / "profit_optimizer_config_pass.json"
    config_raw_pnl_path = fixture_dir / "profit_optimizer_config_raw_pnl_fail.json"
    config_missing_cost_path = fixture_dir / "profit_optimizer_config_missing_cost_fail.json"
    optimizer_run_pass_path = fixture_dir / "optimizer_run_pass.json"
    optimizer_run_raw_pnl_path = fixture_dir / "optimizer_run_raw_pnl_objective_fail.json"
    paths = [
        ROOT / "contracts" / "schema" / "profit_optimizer_config.schema.json",
        ROOT / "contracts" / "schema" / "optimizer_run_report.schema.json",
        config_pass_path,
        config_raw_pnl_path,
        config_missing_cost_path,
        optimizer_run_pass_path,
        optimizer_run_raw_pnl_path,
    ]

    config_pass_errors = _profit_optimizer_config_errors(load_json(config_pass_path))
    if config_pass_errors:
        return fail_result(
            "objective_function_validator",
            f"valid optimizer objective config failed: {config_pass_errors[0]}",
            paths,
            "COST_AFTER_EDGE_UNVERIFIED",
        )
    optimizer_run_pass_errors = _optimizer_run_errors(load_json(optimizer_run_pass_path))
    if optimizer_run_pass_errors:
        return fail_result(
            "objective_function_validator",
            f"valid optimizer run objective failed: {optimizer_run_pass_errors[0]}",
            paths,
            "COST_AFTER_EDGE_UNVERIFIED",
        )

    raw_config_errors = _profit_optimizer_config_errors(load_json(config_raw_pnl_path))
    if not any("RAW_PNL" in error or "NET_EV_AFTER_COST" in error for error in raw_config_errors):
        return fail_result(
            "objective_function_validator",
            "raw PnL optimizer config objective was not rejected",
            paths,
            "COST_AFTER_EDGE_UNVERIFIED",
        )
    raw_run_errors = _optimizer_run_errors(load_json(optimizer_run_raw_pnl_path))
    if not any("RAW_PNL" in error or "NET_EV_AFTER_COST" in error for error in raw_run_errors):
        return fail_result(
            "objective_function_validator",
            "raw PnL optimizer run objective was not rejected",
            paths,
            "COST_AFTER_EDGE_UNVERIFIED",
        )
    missing_cost_errors = _profit_optimizer_config_errors(load_json(config_missing_cost_path))
    if not any("cost components" in error or "minItems 5" in error for error in missing_cost_errors):
        return fail_result(
            "objective_function_validator",
            "optimizer objective missing fee/spread/slippage/impact/latency costs was not rejected",
            paths,
            "COST_AFTER_EDGE_UNVERIFIED",
        )

    return pass_result(
        "objective_function_validator",
        "objective functions require NET_EV_AFTER_COST with fee, spread, slippage, impact, latency, drawdown, overfit, liquidity, and regime components",
        paths,
    )


def candidate_ranking_validator() -> ValidatorResult:
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    config_pass_path = fixture_dir / "profit_optimizer_config_pass.json"
    optimizer_run_pass_path = fixture_dir / "optimizer_run_pass.json"
    paths = [
        ROOT / "contracts" / "schema" / "profit_optimizer_config.schema.json",
        ROOT / "contracts" / "schema" / "optimizer_run_report.schema.json",
        config_pass_path,
        optimizer_run_pass_path,
    ]

    config_errors = _profit_optimizer_config_errors(load_json(config_pass_path))
    if config_errors:
        return fail_result(
            "candidate_ranking_validator",
            f"valid candidate ranking config failed: {config_errors[0]}",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )
    run_report = load_json(optimizer_run_pass_path)
    run_errors = _optimizer_run_errors(run_report)
    if run_errors:
        return fail_result(
            "candidate_ranking_validator",
            f"valid candidate ranking run failed: {run_errors[0]}",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    tampered_no_output = json.loads(json.dumps(run_report))
    tampered_no_output["output_artifact_ids"] = []
    if "CANDIDATE_RANKING_INPUT requires output_artifact_ids" not in _optimizer_run_errors(tampered_no_output):
        return fail_result(
            "candidate_ranking_validator",
            "candidate ranking without output artifact ids was not rejected",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    tampered_zero_count = json.loads(json.dumps(run_report))
    tampered_zero_count["candidate_count"] = 0
    if "CANDIDATE_RANKING_INPUT requires candidate_count > 0" not in _optimizer_run_errors(tampered_zero_count):
        return fail_result(
            "candidate_ranking_validator",
            "candidate ranking with zero candidates was not rejected",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    tampered_live_scope = json.loads(json.dumps(run_report))
    tampered_live_scope["run_scope"] = "LIVE_WRITER_INPUT"
    live_scope_errors = _optimizer_run_errors(tampered_live_scope)
    if not any(
        "CANDIDATE_RANKING_INPUT requires replay/paper/shadow/read-only-only scope" in error
        or "run_scope" in error
        for error in live_scope_errors
    ):
        return fail_result(
            "candidate_ranking_validator",
            "candidate ranking with live-like scope was not rejected",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    return pass_result(
        "candidate_ranking_validator",
        "candidate ranking input requires non-live scope, NET_EV_AFTER_COST objective, candidate_count > 0, and output artifact ids",
        paths,
    )


def _optimizer_run_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.optimizer_run_report.v1")
    if schema is None:
        return ["optimizer_run_report schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "order_submission_allowed",
        "exchange_account_call_allowed",
        "scale_up_recommendation_allowed",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"optimizer run has forbidden live, exchange, or scale field: {field}")
    if report.get("mode") == "LIVE":
        errors.append("optimizer run mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("optimizer run source_modes must not include LIVE")

    warning_lower = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning_lower or "live orders" not in warning_lower:
        errors.append("optimizer run warning must state not LIVE_READY and live orders blocked")

    blockers = report.get("blockers", [])
    status = report.get("optimizer_run_status")
    scope = report.get("run_scope")
    output_type = report.get("optimizer_output_type")
    objective_basis = report.get("objective_basis")
    candidate_count = int(report.get("candidate_count", 0))
    output_artifact_ids = report.get("output_artifact_ids", [])
    if status == "COMPLETED_ANALYSIS_ONLY":
        if scope != "REPLAY_PAPER_SHADOW_READ_ONLY_ONLY":
            errors.append("COMPLETED_ANALYSIS_ONLY requires REPLAY_PAPER_SHADOW_READ_ONLY_ONLY scope")
        if blockers:
            errors.append("completed optimizer run must not carry blockers")
        if objective_basis != "NET_EV_AFTER_COST":
            errors.append("completed optimizer run requires NET_EV_AFTER_COST objective basis")
    elif not blockers:
        errors.append("non-completed optimizer run must carry explicit blocker evidence")
    if output_type == "CANDIDATE_RANKING_INPUT":
        if scope != "REPLAY_PAPER_SHADOW_READ_ONLY_ONLY":
            errors.append("CANDIDATE_RANKING_INPUT requires replay/paper/shadow/read-only-only scope")
        if objective_basis != "NET_EV_AFTER_COST":
            errors.append("CANDIDATE_RANKING_INPUT requires NET_EV_AFTER_COST objective basis")
        if candidate_count <= 0:
            errors.append("CANDIDATE_RANKING_INPUT requires candidate_count > 0")
        if not output_artifact_ids:
            errors.append("CANDIDATE_RANKING_INPUT requires output_artifact_ids")
    if scope in {"RESEARCH_ONLY_BLOCKED", "STALE_ANALYSIS_ONLY"} and not blockers:
        errors.append("blocked or stale optimizer run scope must carry blocker evidence")
    if report.get("resource_budget_status") == "BLOCKED" and not blockers:
        errors.append("resource_budget_status=BLOCKED requires blocker evidence")
    if report.get("partial_write_recovery_status") == "BLOCKED" and not blockers:
        errors.append("partial_write_recovery_status=BLOCKED requires blocker evidence")

    return errors


def optimizer_run_report_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "optimizer_run_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "optimizer_run_pass.json"
    live_flag_path = fixture_dir / "optimizer_run_live_flag_fail.json"
    live_mode_path = fixture_dir / "optimizer_run_live_mode_fail.json"
    wording_path = fixture_dir / "optimizer_run_live_ready_wording_fail.json"
    missing_blocker_path = fixture_dir / "optimizer_run_missing_blocker_fail.json"
    writer_path = fixture_dir / "optimizer_run_live_writer_fail.json"
    raw_pnl_path = fixture_dir / "optimizer_run_raw_pnl_objective_fail.json"
    paths = [
        schema_path,
        pass_path,
        live_flag_path,
        live_mode_path,
        wording_path,
        missing_blocker_path,
        writer_path,
        raw_pnl_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "optimizer_run_report_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _optimizer_run_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "optimizer_run_report_validator",
            f"PASS fixture failed optimizer run validation: {pass_errors[0]}",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    negative_expectations = {
        live_flag_path: "expected const False",
        live_mode_path: "optimizer run mode LIVE is forbidden",
        wording_path: "optimizer run warning must state not LIVE_READY",
        missing_blocker_path: "non-completed optimizer run must carry explicit blocker evidence",
        writer_path: "expected const False",
        raw_pnl_path: "RAW_PNL",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _optimizer_run_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "optimizer_run_report_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
            )

    return pass_result(
        "optimizer_run_report_validator",
        "optimizer run reports are analysis-only, net-EV-after-cost scoped, live-blocked, and cannot call exchange accounts, write LIVE_READY, or scale up",
        paths,
    )


def _optimizer_recommendation_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.optimizer_recommendation_report.v1")
    if schema is None:
        return ["optimizer_recommendation_report schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"optimizer recommendation has forbidden live or scale field: {field}")
    if report.get("mode") == "LIVE":
        errors.append("optimizer recommendation mode LIVE is forbidden before independent live-enabling evidence")

    warning_lower = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning_lower or "live orders" not in warning_lower:
        errors.append("optimizer recommendation warning must state not LIVE_READY and live orders blocked")

    action = report.get("recommendation_action")
    scope = report.get("recommendation_scope")
    output_type = report.get("optimizer_output_type")
    blockers = report.get("blockers", [])
    if action == "ALLOW_PAPER_RANKING":
        if scope != "PAPER_RANKING_RECOMMENDATION_ONLY":
            errors.append("ALLOW_PAPER_RANKING requires PAPER_RANKING_RECOMMENDATION_ONLY scope")
        if output_type != "RANKING_INPUT":
            errors.append("ALLOW_PAPER_RANKING requires optimizer_output_type=RANKING_INPUT")
        if blockers:
            errors.append("ALLOW_PAPER_RANKING recommendation must not carry blockers")
    elif not blockers:
        errors.append("non-ranking optimizer recommendation must carry explicit blocker evidence")
    if action == "RECOMMEND_SCALE_DOWN_ONLY" and output_type != "RISK_REDUCTION_ONLY":
        errors.append("RECOMMEND_SCALE_DOWN_ONLY requires optimizer_output_type=RISK_REDUCTION_ONLY")

    return errors


def optimizer_recommendation_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "optimizer_recommendation_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "optimizer_recommendation_pass.json"
    live_flag_path = fixture_dir / "optimizer_recommendation_live_flag_fail.json"
    wording_path = fixture_dir / "optimizer_recommendation_live_ready_wording_fail.json"
    scope_path = fixture_dir / "optimizer_recommendation_scope_mismatch_fail.json"
    writer_path = fixture_dir / "optimizer_recommendation_live_writer_fail.json"
    paths = [schema_path, pass_path, live_flag_path, wording_path, scope_path, writer_path, state_path]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "optimizer_recommendation_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _optimizer_recommendation_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "optimizer_recommendation_validator",
            f"PASS fixture failed optimizer recommendation validation: {pass_errors[0]}",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    negative_expectations = {
        live_flag_path: "expected const False",
        wording_path: "optimizer recommendation warning must state not LIVE_READY",
        scope_path: "ALLOW_PAPER_RANKING requires PAPER_RANKING_RECOMMENDATION_ONLY scope",
        writer_path: "expected const False",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _optimizer_recommendation_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "optimizer_recommendation_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
            )

    return pass_result(
        "optimizer_recommendation_validator",
        "optimizer recommendations are paper ranking inputs only, require explicit non-live wording, and cannot write live readiness or scale-up permission",
        paths,
    )


def _optimizer_guardrail_report_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.optimizer_guardrail_report.v1")
    if schema is None:
        return ["optimizer_guardrail_report schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "optimizer_live_mutation_detected",
        "order_submission_allowed",
        "exchange_account_call_allowed",
        "scale_up_recommendation_allowed",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"optimizer guardrail report has forbidden live, exchange, or scale field: {field}")
    if report.get("mode") == "LIVE":
        errors.append("optimizer guardrail report mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("optimizer guardrail report source_modes must not include LIVE")

    warning_lower = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning_lower or "live orders" not in warning_lower:
        errors.append("optimizer guardrail report warning must state not LIVE_READY and live orders blocked")

    dependency_statuses = [item.get("status") for item in report.get("dependency_results", []) if isinstance(item, dict)]
    dependency_non_pass = [status for status in dependency_statuses if status != "PASS"]
    blockers = report.get("blockers", [])
    guardrail_status = report.get("guardrail_status")
    summary_status = report.get("dependency_summary_status")
    decision = report.get("guardrail_decision")
    ranking_scope = report.get("output_ranking_scope")
    scope = report.get("guardrail_scope")

    if guardrail_status == "PASS_NO_LIVE_PERMISSION":
        if dependency_non_pass:
            errors.append("guardrail PASS cannot override dependency FAIL/BLOCKED/UNTESTED/STALE/TIMEOUT")
        if summary_status != "PASS":
            errors.append("guardrail PASS requires dependency_summary_status=PASS")
        if blockers:
            errors.append("guardrail PASS must not carry blockers")
        if decision not in {"ALLOW_ANALYSIS_OUTPUT", "ALLOW_SCALE_DOWN_ONLY"}:
            errors.append("guardrail PASS requires non-live analysis or scale-down-only decision")
    elif not blockers:
        errors.append("non-PASS optimizer guardrail report must carry explicit blocker evidence")

    if summary_status == "PASS" and dependency_non_pass:
        errors.append("dependency_summary_status=PASS cannot hide non-PASS dependency")
    if summary_status != "PASS" and not blockers:
        errors.append("non-PASS dependency summary must carry blocker evidence")
    if ranking_scope == "PAPER_RANKING_ONLY":
        if scope != "OPTIMIZER_PAPER_RANKING_ONLY":
            errors.append("PAPER_RANKING_ONLY output requires OPTIMIZER_PAPER_RANKING_ONLY scope")
        if guardrail_status != "PASS_NO_LIVE_PERMISSION":
            errors.append("PAPER_RANKING_ONLY output requires PASS_NO_LIVE_PERMISSION guardrail status")
    if decision == "ALLOW_SCALE_DOWN_ONLY" and ranking_scope != "NONE":
        errors.append("ALLOW_SCALE_DOWN_ONLY requires output_ranking_scope=NONE")

    return errors


def optimizer_guardrail_report_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "optimizer_guardrail_report.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "optimizer_guardrail_report_pass.json"
    live_flag_path = fixture_dir / "optimizer_guardrail_report_live_flag_fail.json"
    dependency_path = fixture_dir / "optimizer_guardrail_report_dependency_override_fail.json"
    wording_path = fixture_dir / "optimizer_guardrail_report_live_ready_wording_fail.json"
    missing_blocker_path = fixture_dir / "optimizer_guardrail_report_missing_blocker_fail.json"
    writer_path = fixture_dir / "optimizer_guardrail_report_live_writer_fail.json"
    scale_up_path = fixture_dir / "optimizer_guardrail_report_scale_up_fail.json"
    paths = [
        schema_path,
        pass_path,
        live_flag_path,
        dependency_path,
        wording_path,
        missing_blocker_path,
        writer_path,
        scale_up_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "optimizer_guardrail_report_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _optimizer_guardrail_report_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "optimizer_guardrail_report_validator",
            f"PASS fixture failed optimizer guardrail report validation: {pass_errors[0]}",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    negative_expectations = {
        live_flag_path: "expected const False",
        dependency_path: "guardrail PASS cannot override dependency",
        wording_path: "optimizer guardrail report warning must state not LIVE_READY",
        missing_blocker_path: "non-PASS optimizer guardrail report must carry explicit blocker evidence",
        writer_path: "expected const False",
        scale_up_path: "expected const False",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _optimizer_guardrail_report_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "optimizer_guardrail_report_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
            )

    return pass_result(
        "optimizer_guardrail_report_validator",
        "optimizer guardrail reports cannot convert dependency PASS into live readiness, live orders, exchange account calls, LIVE_READY writes, or scale-up",
        paths,
    )


def _optimization_state_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_bundle.get("trader1.optimization_state.v1")
    if schema is None:
        return ["optimization_state schema missing from schema bundle"]

    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "active_snapshot_mutation_allowed",
        "optimizer_winner_live_config_allowed",
        "paper_winner_live_config_allowed",
        "order_submission_allowed",
        "exchange_account_call_allowed",
        "scale_up_recommendation_allowed",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"optimization state has forbidden live, active, exchange, or scale field: {field}")
    if report.get("mode") == "LIVE":
        errors.append("optimization state mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("optimization state source_modes must not include LIVE")

    warning_lower = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning_lower or "live orders" not in warning_lower:
        errors.append("optimization state warning must state not LIVE_READY and live orders blocked")

    dependency_statuses = [item.get("status") for item in report.get("dependency_results", []) if isinstance(item, dict)]
    dependency_non_pass = [status for status in dependency_statuses if status != "PASS"]
    blockers = report.get("blockers", [])
    status = report.get("optimization_state_status")
    summary_status = report.get("dependency_summary_status")
    scope = report.get("state_scope")
    objective_basis = report.get("objective_basis")
    write_policy = report.get("state_write_policy")

    if status == "ACTIVE_ANALYSIS_ONLY":
        if dependency_non_pass:
            errors.append("ACTIVE_ANALYSIS_ONLY cannot override dependency FAIL/BLOCKED/UNTESTED/STALE/TIMEOUT")
        if summary_status != "PASS":
            errors.append("ACTIVE_ANALYSIS_ONLY requires dependency_summary_status=PASS")
        if blockers:
            errors.append("ACTIVE_ANALYSIS_ONLY state must not carry blockers")
        if objective_basis != "NET_EV_AFTER_COST":
            errors.append("ACTIVE_ANALYSIS_ONLY requires NET_EV_AFTER_COST objective basis")
        if write_policy != "APPEND_AUDIT_ONLY":
            errors.append("ACTIVE_ANALYSIS_ONLY requires APPEND_AUDIT_ONLY write policy")
    elif not blockers:
        errors.append("non-active optimization state must carry explicit blocker evidence")

    if summary_status == "PASS" and dependency_non_pass:
        errors.append("dependency_summary_status=PASS cannot hide non-PASS dependency")
    if summary_status != "PASS" and not blockers:
        errors.append("non-PASS dependency summary must carry blocker evidence")
    if scope == "PAPER_RANKING_STATE_ONLY":
        if report.get("latest_recommendation_id") is None:
            errors.append("PAPER_RANKING_STATE_ONLY requires latest_recommendation_id")
        if report.get("latest_guardrail_report_id") is None:
            errors.append("PAPER_RANKING_STATE_ONLY requires latest_guardrail_report_id")
        if status != "ACTIVE_ANALYSIS_ONLY":
            errors.append("PAPER_RANKING_STATE_ONLY requires ACTIVE_ANALYSIS_ONLY status")
    if scope == "RESEARCH_BLOCKED" and not blockers:
        errors.append("RESEARCH_BLOCKED optimization state must carry blocker evidence")

    return errors


def optimization_state_validator() -> ValidatorResult:
    schema_path = ROOT / "contracts" / "schema" / "optimization_state.schema.json"
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "optimization_state_pass.json"
    live_flag_path = fixture_dir / "optimization_state_live_flag_fail.json"
    dependency_path = fixture_dir / "optimization_state_dependency_override_fail.json"
    wording_path = fixture_dir / "optimization_state_live_ready_wording_fail.json"
    missing_blocker_path = fixture_dir / "optimization_state_missing_blocker_fail.json"
    active_mutation_path = fixture_dir / "optimization_state_active_snapshot_mutation_fail.json"
    raw_pnl_path = fixture_dir / "optimization_state_raw_pnl_objective_fail.json"
    paths = [
        schema_path,
        pass_path,
        live_flag_path,
        dependency_path,
        wording_path,
        missing_blocker_path,
        active_mutation_path,
        raw_pnl_path,
        state_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "optimization_state_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _optimization_state_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "optimization_state_validator",
            f"PASS fixture failed optimization state validation: {pass_errors[0]}",
            paths,
            "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
        )

    negative_expectations = {
        live_flag_path: "expected const False",
        dependency_path: "ACTIVE_ANALYSIS_ONLY cannot override dependency",
        wording_path: "optimization state warning must state not LIVE_READY",
        missing_blocker_path: "non-active optimization state must carry explicit blocker evidence",
        active_mutation_path: "expected const False",
        raw_pnl_path: "RAW_PNL",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _optimization_state_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "optimization_state_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
            )

    return pass_result(
        "optimization_state_validator",
        "optimization state remains append-audit-only, non-live, dependency-visible, and cannot mutate ACTIVE snapshots, live config, or scale-up permission",
        paths,
    )


def _dependency_failures(dependency_ids: list[str]) -> list[str]:
    failures: list[str] = []
    for dependency_id in dependency_ids:
        func = VALIDATOR_FUNCTIONS.get(dependency_id)
        if func is None:
            failures.append(f"{dependency_id}:UNTESTED")
            continue
        result = func().as_dict()
        if result["status"] != "PASS":
            failures.append(f"{dependency_id}:{result['status']}")
    return failures


def optimizer_guardrail_validator() -> ValidatorResult:
    paths = [
        ROOT / "contracts" / "registry.yaml",
        ROOT / "contracts" / "schema" / "common.defs.schema.json",
        ROOT / "contracts" / "generated" / "current_implementation_state.json",
    ] + _patch_result_paths()
    dependency_failures = _dependency_failures(
        [
            "optimizer_no_live_mutation_validator",
            "optimizer_run_report_validator",
            "optimizer_recommendation_validator",
            "optimizer_guardrail_report_validator",
            "optimization_state_validator",
            "exploration_exploitation_policy_validator",
            "parameter_narrowing_validator",
            "optimizer_memory_state_validator",
            "strategy_performance_memory_validator",
            "live_final_guard_validator",
            "registry_validator",
            "schema_validator",
            "closed_enum_validator",
        ]
    )
    if dependency_failures:
        return blocked_result(
            "optimizer_guardrail_validator",
            "optimizer guardrail remains blocked until dependencies pass: " + ", ".join(dependency_failures),
            paths,
            "OPTIMIZER_UNTESTED",
        )
    return pass_result("optimizer_guardrail_validator", "optimizer guardrail dependencies passed without live mutation", paths)


CONVERGENCE_ASSESSMENT_REQUIRED_STATUS_FIELDS = (
    "convergence_objective_profile_validator_status",
    "optimizer_memory_state_validator_status",
    "strategy_performance_memory_validator_status",
    "overfit_diagnostic_validator_status",
    "execution_feedback_loop_validator_status",
    "failure_analysis_validator_status",
    "paper_shadow_evidence_accumulation_validator_status",
    "market_regime_adaptation_validator_status",
    "model_drift_validator_status",
    "coverage_index_validator_status",
)


def _convergence_assessment_errors(report: dict[str, Any]) -> list[str]:
    schema_dir = ROOT / "contracts" / "schema"
    schema_bundle = load_schema_bundle(schema_dir)
    schema = schema_for_instance(report, schema_bundle)
    if schema is None:
        return ["convergence assessment report schema not found"]
    instance_result = validate_instance_against_schema(report, schema, schema_bundle)
    if instance_result.status != "PASS":
        return instance_result.errors

    errors: list[str] = []
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "live_config_mutation_allowed",
        "writes_live_ready_snapshot",
        "active_snapshot_mutation_allowed",
        "optimizer_winner_live_config_allowed",
        "paper_winner_live_config_allowed",
        "writer_input_eligible",
        "model_promotion_allowed",
        "scale_up_recommendation_allowed",
    ):
        if _live_flag_is_true(report.get(field)):
            errors.append(f"convergence assessment report has forbidden true field: {field}")

    if report.get("mode") == "LIVE":
        errors.append("convergence assessment mode LIVE is forbidden before independent live-enabling evidence")
    if "LIVE" in set(report.get("source_modes", [])):
        errors.append("convergence assessment source_modes must not include LIVE")

    warning = str(report.get("operator_warning", "")).lower()
    if "not live_ready" not in warning or "live orders blocked" not in warning:
        errors.append("convergence assessment operator_warning must say not live_ready and live orders blocked")

    dependency_statuses = [report.get(field) for field in CONVERGENCE_ASSESSMENT_REQUIRED_STATUS_FIELDS]
    pass_count = sum(1 for status in dependency_statuses if status == "PASS")
    if report.get("dependency_pass_count") != pass_count:
        errors.append("dependency_pass_count must equal actual PASS dependency status count")
    if report.get("required_dependency_count") != len(CONVERGENCE_ASSESSMENT_REQUIRED_STATUS_FIELDS):
        errors.append("required_dependency_count must equal convergence assessment dependency field count")

    blockers = report.get("blockers", [])
    blocker_codes = {item.get("code") for item in blockers if isinstance(item, dict)}
    claim = report.get("convergence_claim")
    status = report.get("assessment_status")
    score_band = report.get("objective_score_band")
    data_status = report.get("data_freshness_status")
    data_age = float(report.get("data_age_seconds", 0))
    max_data_age = float(report.get("max_data_age_seconds", 0))
    drift_status = report.get("model_drift_status")

    if any(item != "PASS" for item in dependency_statuses):
        if status in {"LOCALLY_IMPROVING", "ROBUSTLY_IMPROVING"}:
            errors.append("convergence assessment cannot claim improvement while dependency is not PASS")
        if claim in {"LOCALLY_IMPROVING", "ROBUSTLY_IMPROVING", "WRITER_INPUT_ELIGIBLE"}:
            errors.append("convergence assessment cannot keep improvement claim while dependency is not PASS")
        if report.get("blocks_promotion") is not True:
            errors.append("non-PASS dependency requires blocks_promotion=true")
        if not blockers:
            errors.append("non-PASS dependency requires blockers")

    if data_status != "FRESH" or data_age > max_data_age:
        if status in {"LOCALLY_IMPROVING", "ROBUSTLY_IMPROVING"}:
            errors.append("stale or missing convergence assessment input cannot claim improvement")
        if claim in {"LOCALLY_IMPROVING", "ROBUSTLY_IMPROVING", "WRITER_INPUT_ELIGIBLE"}:
            errors.append("stale or missing convergence assessment input cannot keep convergence claim")
        if not blockers:
            errors.append("stale or missing convergence assessment input requires blockers")

    if drift_status in {"DRIFT_SUSPECTED", "DRIFT_DETECTED", "BLOCKED"}:
        if report.get("blocks_promotion") is not True:
            errors.append(f"{drift_status} requires blocks_promotion=true")
        if claim not in {"BLOCKED", "NO_CLAIM"}:
            errors.append(f"{drift_status} cannot keep convergence_claim={claim}")
        if "MODEL_DRIFT_DETECTED" not in blocker_codes and "CONVERGENCE_CLAIM_UNVERIFIED" not in blocker_codes:
            errors.append(f"{drift_status} requires MODEL_DRIFT_DETECTED or CONVERGENCE_CLAIM_UNVERIFIED blocker")

    if claim == "WRITER_INPUT_ELIGIBLE":
        errors.append("convergence assessment cannot create LIVE_READY writer input eligibility in MVP-4")
    if score_band == "ROBUST_IMPROVING" and claim != "ROBUSTLY_IMPROVING":
        errors.append("ROBUST_IMPROVING objective_score_band requires ROBUSTLY_IMPROVING convergence_claim")
    if claim == "ROBUSTLY_IMPROVING" and (
        any(item != "PASS" for item in dependency_statuses)
        or drift_status != "NO_DRIFT"
        or data_status != "FRESH"
        or data_age > max_data_age
    ):
        errors.append("ROBUSTLY_IMPROVING convergence claim requires all dependencies PASS, fresh data, and NO_DRIFT")
    if claim in {"LOCALLY_IMPROVING", "ROBUSTLY_IMPROVING"} and blockers:
        errors.append("improving convergence assessment must not carry blockers")
    return errors


def convergence_assessment_validator() -> ValidatorResult:
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    pass_path = fixture_dir / "convergence_assessment_pass.json"
    live_flag_fail_path = fixture_dir / "convergence_assessment_live_flag_fail.json"
    missing_dependency_fail_path = fixture_dir / "convergence_assessment_missing_dependency_fail.json"
    untested_dependency_fail_path = fixture_dir / "convergence_assessment_untested_dependency_fail.json"
    drift_unblocked_fail_path = fixture_dir / "convergence_assessment_drift_unblocked_fail.json"
    writer_input_fail_path = fixture_dir / "convergence_assessment_writer_input_fail.json"
    scale_up_fail_path = fixture_dir / "convergence_assessment_scale_up_fail.json"
    paths = [
        ROOT / "contracts" / "generated" / "current_implementation_state.json",
        ROOT / "contracts" / "schema" / "convergence_assessment_report.schema.json",
        ROOT / "contracts" / "schema" / "optimizer_memory_state.schema.json",
        pass_path,
        live_flag_fail_path,
        missing_dependency_fail_path,
        untested_dependency_fail_path,
        drift_unblocked_fail_path,
        writer_input_fail_path,
        scale_up_fail_path,
    ] + _patch_result_paths()

    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "convergence_assessment_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _convergence_assessment_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "convergence_assessment_validator",
            f"PASS fixture failed convergence assessment validation: {pass_errors[0]}",
            paths,
            "CONVERGENCE_STATE_UNTESTED",
        )

    negative_expectations = {
        live_flag_fail_path: "expected const False",
        missing_dependency_fail_path: "convergence assessment cannot claim improvement while dependency is not PASS",
        untested_dependency_fail_path: "convergence assessment cannot keep improvement claim while dependency is not PASS",
        drift_unblocked_fail_path: "DRIFT_DETECTED requires blocks_promotion=true",
        writer_input_fail_path: "expected const False",
        scale_up_fail_path: "expected const False",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _convergence_assessment_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "convergence_assessment_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "CONVERGENCE_STATE_UNTESTED",
            )

    no_live_result = optimizer_no_live_mutation_validator().as_dict()
    if no_live_result["status"] != "PASS":
        return fail_result(
            "convergence_assessment_validator",
            "convergence assessment saw a live mutation guard failure",
            paths,
            "LIVE_FINAL_GUARD_FAILED",
        )
    dependency_failures = _dependency_failures(
        [
            "convergence_objective_profile_validator",
            "optimizer_memory_state_validator",
            "strategy_performance_memory_validator",
            "overfit_diagnostic_validator",
            "execution_feedback_loop_validator",
            "failure_analysis_validator",
            "paper_shadow_evidence_accumulation_validator",
            "market_regime_adaptation_validator",
            "model_drift_validator",
            "coverage_index_validator",
        ]
    )
    if dependency_failures:
        return blocked_result(
            "convergence_assessment_validator",
            "convergence assessment remains blocked until dependencies pass: " + ", ".join(dependency_failures),
            paths,
            "CONVERGENCE_STATE_UNTESTED",
        )
    return pass_result(
        "convergence_assessment_validator",
        "convergence assessment schema, fixtures, dependency chain, drift blocking, and false live/scale flags passed",
        paths,
    )


def _convergence_claim_errors(report: dict[str, Any]) -> list[str]:
    errors = _convergence_assessment_errors(report)

    claim = report.get("convergence_claim")
    status = report.get("assessment_status")
    score_band = report.get("objective_score_band")
    drift_status = report.get("model_drift_status")
    data_status = report.get("data_freshness_status")
    data_age = float(report.get("data_age_seconds", 0))
    max_data_age = float(report.get("max_data_age_seconds", 0))
    blockers = report.get("blockers", [])
    dependency_statuses = [report.get(field) for field in CONVERGENCE_ASSESSMENT_REQUIRED_STATUS_FIELDS]
    warning = str(report.get("operator_warning", "")).lower()
    next_action = str(report.get("next_operator_action", "")).lower()
    combined_text = f"{warning} {next_action}"

    for phrase in PROFITABILITY_EVIDENCE_FORBIDDEN_PHRASES:
        if phrase in combined_text:
            errors.append(f"convergence claim contains forbidden profitability wording: {phrase}")

    if "no profit guarantee" not in combined_text:
        errors.append("convergence claim operator text must state no profit guarantee")
    if "not live_ready" not in combined_text or "live orders blocked" not in combined_text:
        errors.append("convergence claim operator text must state not LIVE_READY and live orders blocked")
    if "scale" in combined_text and "blocked" not in combined_text:
        errors.append("convergence claim scale wording must remain blocked")

    if claim in {"LOCALLY_IMPROVING", "ROBUSTLY_IMPROVING"}:
        if any(status_value != "PASS" for status_value in dependency_statuses):
            errors.append("convergence claim cannot remain improving while dependency is not PASS")
        if data_status != "FRESH" or data_age > max_data_age:
            errors.append("convergence claim cannot remain improving with stale or missing data")
        if drift_status != "NO_DRIFT":
            errors.append(f"convergence claim cannot remain improving while model_drift_status={drift_status}")
        if blockers:
            errors.append("convergence claim cannot remain improving while blockers are present")
        if report.get("blocks_promotion") is not False:
            errors.append("improving convergence claim must not be represented as promotion-ready; blocks_promotion must remain false only for PAPER/SHADOW analysis")

    if claim == "ROBUSTLY_IMPROVING":
        if status != "ROBUSTLY_IMPROVING" or score_band != "ROBUST_IMPROVING":
            errors.append("ROBUSTLY_IMPROVING convergence claim requires matching robust assessment status and score band")
        if "shadow" not in combined_text:
            errors.append("ROBUSTLY_IMPROVING convergence claim must remain tied to PAPER/SHADOW evidence")

    if claim == "WRITER_INPUT_ELIGIBLE":
        errors.append("convergence claim validator blocks WRITER_INPUT_ELIGIBLE in MVP-4")
    return errors


def convergence_claim_validator() -> ValidatorResult:
    fixture_dir = ROOT / "tests" / "validators" / "fixtures"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    pass_path = fixture_dir / "convergence_claim_pass.json"
    dependency_fail_path = fixture_dir / "convergence_claim_dependency_fail.json"
    stale_fail_path = fixture_dir / "convergence_claim_stale_data_fail.json"
    drift_fail_path = fixture_dir / "convergence_claim_drift_fail.json"
    wording_fail_path = fixture_dir / "convergence_claim_forbidden_wording_fail.json"
    writer_input_fail_path = fixture_dir / "convergence_claim_writer_input_fail.json"
    paths = [
        state_path,
        ROOT / "contracts" / "schema" / "convergence_assessment_report.schema.json",
        pass_path,
        dependency_fail_path,
        stale_fail_path,
        drift_fail_path,
        wording_fail_path,
        writer_input_fail_path,
    ]

    state = load_json(state_path)
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if _live_flag_is_true(state.get(field)):
            return fail_result(
                "convergence_claim_validator",
                f"current implementation state has forbidden live or scale flag: {field}",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            )

    pass_errors = _convergence_claim_errors(load_json(pass_path))
    if pass_errors:
        return fail_result(
            "convergence_claim_validator",
            f"PASS fixture failed convergence claim validation: {pass_errors[0]}",
            paths,
            "CONVERGENCE_CLAIM_UNVERIFIED",
        )

    negative_expectations = {
        dependency_fail_path: "convergence claim cannot remain improving while dependency is not PASS",
        stale_fail_path: "convergence claim cannot remain improving with stale or missing data",
        drift_fail_path: "convergence claim cannot remain improving while model_drift_status=DRIFT_DETECTED",
        wording_fail_path: "forbidden profitability wording",
        writer_input_fail_path: "expected const False",
    }
    for path, expected_fragment in negative_expectations.items():
        errors = _convergence_claim_errors(load_json(path))
        if not any(expected_fragment in error for error in errors):
            return fail_result(
                "convergence_claim_validator",
                f"negative fixture did not fail closed as expected: {rel(path)}",
                paths,
                "CONVERGENCE_CLAIM_UNVERIFIED",
            )

    dependency = convergence_assessment_validator().as_dict()
    if dependency["status"] != "PASS":
        return blocked_result(
            "convergence_claim_validator",
            f"convergence assessment dependency did not pass: {dependency['status']}",
            paths,
            "CONVERGENCE_STATE_UNTESTED",
        )
    return pass_result(
        "convergence_claim_validator",
        "convergence claims are dependency-gated, fresh-data-only, drift-blocked, no-profit-guarantee, and cannot create writer input, live, order, or scale-up permission",
        paths,
    )


def scale_up_eligibility_validator() -> ValidatorResult:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    paths = [
        state_path,
        ROOT / "contracts" / "schema" / "risk_scaling_decision.schema.json",
        ROOT / "system" / "evidence" / "MVP4_EXTERNAL_BLOCKER.evidence_manifest.json",
    ] + _patch_result_paths()
    state = load_json(state_path)
    if not (state.get("live_order_ready") and state.get("live_order_allowed") and state.get("can_live_trade")):
        return blocked_result(
            "scale_up_eligibility_validator",
            "scale-up is blocked because live permission is false and external live-enabling evidence is missing",
            paths,
            "SCALE_UP_NOT_ELIGIBLE",
        )
    dependency_failures = _dependency_failures(
        [
            "risk_scaling_decision_validator",
            "live_burn_in_feedback_validator",
            "paper_live_parity_validator",
            "live_final_guard_validator",
            "emergency_flatten_validator",
            "ledger_reconciliation_validator",
        ]
    )
    if dependency_failures:
        return blocked_result(
            "scale_up_eligibility_validator",
            "scale-up remains blocked until dependencies pass: " + ", ".join(dependency_failures),
            paths,
            "RISK_SCALING_UNTESTED",
        )
    return pass_result("scale_up_eligibility_validator", "scale-up dependencies passed for exact scope", paths)


def review_plan_reflection_ledger_validator() -> ValidatorResult:
    validator_id = "review_plan_reflection_ledger_validator"
    paths = [
        ROOT / "검토안",
        ROOT / "system" / "evidence" / "audit_reports" / "REVIEW_PLAN_REFLECTION_LEDGER.json",
    ]
    from tools.review_plan_reflection_status import build_reflection_ledger, validate_reflection_ledger

    ledger = build_reflection_ledger()
    result = validate_reflection_ledger(ledger)
    if result["status"] != "PASS":
        return fail_result(
            validator_id,
            "review plan reflection ledger is unsafe or incomplete: " + ", ".join(result.get("blockers", [])),
            paths,
            "REVIEW_PLAN_REFLECTION_UNSAFE",
        )
    if ledger.get("delete_ready_count", 0) > 0:
        return blocked_result(
            validator_id,
            "review plan files are marked reflected and must be deleted one by one in a tracked patch",
            paths,
            "REVIEW_PLAN_DELETION_PENDING",
        )
    return pass_result(
        validator_id,
        "review plan files are cataloged, deleted-after-reflection entries remain ledgered, and new files can enter as pending input",
        paths,
    )


VALIDATOR_FUNCTIONS: dict[str, Callable[[], ValidatorResult]] = {
    "authority_integrity_validator": authority_integrity_validator,
    "external_authority_manifest_validator": external_authority_manifest_validator,
    "registry_validator": registry_validator,
    "schema_validator": schema_validator,
    "closed_enum_validator": closed_enum_validator,
    "common_defs_drift_validator": common_defs_drift_validator,
    "patch_result_schema_validator": patch_result_schema_validator,
    "patch_result_runtime_schema_instance_validator": patch_result_runtime_schema_instance_validator,
    "coverage_index_validator": coverage_index_validator,
    "active_schema_extraction_validator": active_schema_extraction_validator,
    "generated_artifact_dirty_validator": generated_artifact_dirty_validator,
    "live_blocked_scaffold_validator": live_blocked_scaffold_validator,
    "live_blocked_negative_matrix_validator": live_blocked_negative_matrix_validator,
    "source_bundle_hygiene_validator": source_bundle_hygiene_validator,
    "shipped_package_hygiene_validator": shipped_package_hygiene_validator,
    "secret_scan_validator": secret_scan_validator,
    "path_namespace_validator": path_namespace_validator,
    "truth_hierarchy_validator": truth_hierarchy_validator,
    "single_writer_order_path_validator": single_writer_order_path_validator,
    "strategy_direct_order_validator": strategy_direct_order_validator,
    "readiness_surface_validator": readiness_surface_validator,
    "root_launcher_guard_validator": root_launcher_guard_validator,
    "root_launcher_surface_validator": root_launcher_surface_validator,
    "binance_adapter_surface_validator": binance_adapter_surface_validator,
    "runtime_config_validator": runtime_config_validator,
    "live_ready_snapshot_validator": live_ready_snapshot_validator,
    "live_ready_snapshot_writer_validator": live_ready_snapshot_writer_validator,
    "official_api_verification_validator": official_api_verification_validator,
    "startup_probe_validator": startup_probe_validator,
    "heartbeat_validator": heartbeat_validator,
    "summary_shell_validator": summary_shell_validator,
    "read_only_dashboard_validator": read_only_dashboard_validator,
    "dashboard_visual_layout_validator": dashboard_visual_layout_validator,
    "runtime_schema_instance_validator": runtime_schema_instance_validator,
    "runtime_dashboard_artifact_hygiene_validator": runtime_dashboard_artifact_hygiene_validator,
    "runtime_stability_history_validator": runtime_stability_history_validator,
    "runtime_resource_pressure_validator": runtime_resource_pressure_validator,
    "bytecode_free_syntax_validator": bytecode_free_syntax_validator,
    "paper_portfolio_snapshot_validator": paper_portfolio_snapshot_validator,
    "safety_control_validator": safety_control_validator,
    "ledger_durability_validator": ledger_durability_validator,
    "paper_ledger_rollup_validator": paper_ledger_rollup_validator,
    "reconciliation_validator": reconciliation_validator,
    "ledger_reconciliation_validator": ledger_reconciliation_validator,
    "emergency_flatten_validator": emergency_flatten_validator,
    "operator_action_audit_validator": operator_action_audit_validator,
    "operator_control_validator": operator_control_validator,
    "upbit_paper_dry_run_validator": upbit_paper_dry_run_validator,
    "upbit_paper_runtime_cycle_validator": upbit_paper_runtime_cycle_validator,
    "upbit_public_market_data_collection_validator": upbit_public_market_data_collection_validator,
    "upbit_public_rest_sample_validator": upbit_public_rest_sample_validator,
    "upbit_public_rest_continuity_validator": upbit_public_rest_continuity_validator,
    "upbit_public_rest_continuity_history_validator": upbit_public_rest_continuity_history_validator,
    "upbit_paper_persistent_loop_validator": upbit_paper_persistent_loop_validator,
    "upbit_paper_runtime_sample_history_validator": upbit_paper_runtime_sample_history_validator,
    "upbit_paper_stale_loop_reconciliation_validator": upbit_paper_stale_loop_reconciliation_validator,
    "upbit_paper_stale_loop_regeneration_plan_validator": upbit_paper_stale_loop_regeneration_plan_validator,
    "upbit_paper_stale_loop_execution_guard_validator": upbit_paper_stale_loop_execution_guard_validator,
    "upbit_paper_stale_loop_safe_regeneration_executor_validator": upbit_paper_stale_loop_safe_regeneration_executor_validator,
    "upbit_paper_stale_loop_post_regeneration_reconciliation_validator": upbit_paper_stale_loop_post_regeneration_reconciliation_validator,
    "upbit_paper_blocked_repair_plan_validator": upbit_paper_blocked_repair_plan_validator,
    "upbit_paper_ledger_rollup_repair_validator": upbit_paper_ledger_rollup_repair_validator,
    "upbit_paper_post_repair_reconciliation_validator": upbit_paper_post_repair_reconciliation_validator,
    "upbit_paper_runtime_recovery_guard_validator": upbit_paper_runtime_recovery_guard_validator,
    "restart_recovery_validator": restart_recovery_validator,
    "upbit_operational_paper_gate_validator": upbit_operational_paper_gate_validator,
    "upbit_live_review_preflight_validator": upbit_live_review_preflight_validator,
    "convergence_objective_profile_validator": convergence_objective_profile_validator,
    "optimizer_memory_state_validator": optimizer_memory_state_validator,
    "strategy_performance_memory_validator": strategy_performance_memory_validator,
    "overfit_diagnostic_validator": overfit_diagnostic_validator,
    "execution_feedback_loop_validator": execution_feedback_loop_validator,
    "shadow_observation_runtime_validator": shadow_observation_runtime_validator,
    "shadow_observation_stream_validator": shadow_observation_stream_validator,
    "shadow_observation_scheduler_guard_validator": shadow_observation_scheduler_guard_validator,
    "shadow_observation_persistent_runtime_validator": shadow_observation_persistent_runtime_validator,
    "shadow_observation_actual_runtime_blocker_validator": shadow_observation_actual_runtime_blocker_validator,
    "shadow_observation_actual_runtime_harness_validator": shadow_observation_actual_runtime_harness_validator,
    "shadow_observation_artifact_writer_validator": shadow_observation_artifact_writer_validator,
    "shadow_observation_runtime_orchestration_validator": shadow_observation_runtime_orchestration_validator,
    "paper_shadow_evidence_accumulation_validator": paper_shadow_evidence_accumulation_validator,
    "failure_analysis_validator": failure_analysis_validator,
    "model_drift_validator": model_drift_validator,
    "risk_scaling_decision_validator": risk_scaling_decision_validator,
    "live_burn_in_feedback_validator": live_burn_in_feedback_validator,
    "paper_live_parity_validator": paper_live_parity_validator,
    "execution_quality_measurement_validator": execution_quality_measurement_validator,
    "survival_layer_validator": survival_layer_validator,
    "live_final_guard_validator": live_final_guard_validator,
    "optimizer_no_live_mutation_validator": optimizer_no_live_mutation_validator,
    "candidate_scorecard_validator": candidate_scorecard_validator,
    "candidate_scorecard_net_ev_validator": candidate_scorecard_net_ev_validator,
    "ranking_stability_validator": ranking_stability_validator,
    "rolling_window_default_validator": rolling_window_default_validator,
    "parameter_bound_validator": parameter_bound_validator,
    "promotion_threshold_validator": promotion_threshold_validator,
    "profit_optimizer_config_validator": profit_optimizer_config_validator,
    "objective_function_validator": objective_function_validator,
    "candidate_ranking_validator": candidate_ranking_validator,
    "optimizer_run_report_validator": optimizer_run_report_validator,
    "optimizer_recommendation_validator": optimizer_recommendation_validator,
    "optimizer_guardrail_report_validator": optimizer_guardrail_report_validator,
    "optimization_state_validator": optimization_state_validator,
    "exploration_exploitation_policy_validator": exploration_exploitation_policy_validator,
    "exploration_to_exploitation_validator": exploration_to_exploitation_validator,
    "candidate_cooldown_validator": candidate_cooldown_validator,
    "parameter_narrowing_validator": parameter_narrowing_validator,
    "strategy_condition_matrix_validator": strategy_condition_matrix_validator,
    "symbol_strategy_regime_fit_validator": symbol_strategy_regime_fit_validator,
    "market_regime_adaptation_validator": market_regime_adaptation_validator,
    "paper_exposure_quality_report_validator": paper_exposure_quality_report_validator,
    "realized_slippage_validator": realized_slippage_validator,
    "order_failure_taxonomy_validator": order_failure_taxonomy_validator,
    "profit_convergence_cycle_validator": profit_convergence_cycle_validator,
    "profitability_evidence_maturity_rollup_validator": profitability_evidence_maturity_rollup_validator,
    "profitability_optimizer_evidence_gap_validator": profitability_optimizer_evidence_gap_validator,
    "optimizer_guardrail_validator": optimizer_guardrail_validator,
    "convergence_assessment_validator": convergence_assessment_validator,
    "convergence_claim_validator": convergence_claim_validator,
    "scale_up_eligibility_validator": scale_up_eligibility_validator,
    "review_plan_reflection_ledger_validator": review_plan_reflection_ledger_validator,
}


def run_validators(validator_ids: list[str] | None = None) -> list[dict[str, Any]]:
    ids = validator_ids or MVP0_CORE_VALIDATORS
    results = []
    for validator_id in ids:
        func = VALIDATOR_FUNCTIONS[validator_id]
        try:
            results.append(func().as_dict())
        except Exception as exc:  # fail closed for validator runtime errors
            results.append(
                fail_result(validator_id, f"validator runtime exception: {exc}", [], "UNKNOWN_BLOCKED").as_dict()
            )
    return results


def evaluate_live_blocking_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    validator_id = fixture.get("validator_id", "live_blocked_scaffold_validator")
    paths: list[Path] = []
    if validator_id in CONVERGENCE_FOUNDATION_VALIDATORS + CONVERGENCE_ASSESSMENT_DEPENDENCY_VALIDATORS + CONVERGENCE_RISK_SCALE_VALIDATORS:
        if fixture.get("live_order_allowed") is True or fixture.get("can_live_trade") is True:
            return fail_result(
                validator_id,
                "convergence dependency fixture attempted live permission without evidence",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            ).as_dict()
        expected = fixture.get("expected_status", "PASS")
        if expected == "PASS":
            return pass_result(validator_id, "convergence dependency fixture preserved schema-only non-live state", paths).as_dict()
        return blocked_result(
            validator_id,
            "convergence dependency fixture remains blocked before dependency evidence",
            paths,
            fixture.get("expected_blocker_code", "CONVERGENCE_STATE_UNTESTED"),
        ).as_dict()
    if validator_id == "live_final_guard_validator":
        if fixture.get("live_order_allowed") is True or fixture.get("can_live_trade") is True:
            return fail_result(validator_id, "live final guard fixture attempted live permission without evidence", paths, "LIVE_FINAL_GUARD_FAILED").as_dict()
        expected = fixture.get("expected_status", "BLOCKED")
        if expected == "PASS":
            return pass_result(validator_id, "live final guard fixture preserved blocked non-live state", paths).as_dict()
        return blocked_result(
            validator_id,
            "live final guard fixture remains blocked before live evidence",
            paths,
            fixture.get("expected_blocker_code", "LIVE_FINAL_GUARD_FAILED"),
        ).as_dict()
    if validator_id in OPTIMIZER_CONVERGENCE_GUARDRAIL_VALIDATORS:
        if fixture.get("live_order_allowed") is True or fixture.get("can_live_trade") is True:
            return fail_result(
                validator_id,
                "optimizer/convergence fixture attempted live permission without evidence",
                paths,
                "LIVE_FINAL_GUARD_FAILED",
            ).as_dict()
        expected = fixture.get("expected_status", "BLOCKED")
        if expected == "PASS":
            return pass_result(validator_id, "optimizer/convergence guardrail fixture preserved live-blocked state", paths).as_dict()
        return blocked_result(
            validator_id,
            "optimizer/convergence guardrail fixture remains blocked without dependency evidence",
            paths,
            fixture.get("expected_blocker_code", "CONVERGENCE_STATE_UNTESTED"),
        ).as_dict()
    if fixture.get("live_order_allowed") is True or fixture.get("can_live_trade") is True:
        return fail_result(validator_id, "fixture attempted to allow live trading without live-enabling evidence", paths, "LIVE_FINAL_GUARD_FAILED").as_dict()
    if fixture.get("live_order_ready") is False and fixture.get("expected_order_adapter_called") is False:
        expected = fixture.get("expected_status", "BLOCKED")
        if expected == "PASS":
            return pass_result(validator_id, "safe blocked fixture preserved no-order behavior", paths).as_dict()
        return blocked_result(validator_id, "live readiness missing keeps order adapter blocked", paths, fixture.get("expected_blocker_code", "LIVE_READY_MISSING")).as_dict()
    return fail_result(validator_id, "fixture does not prove blocked live order behavior", paths, "UNKNOWN_BLOCKED").as_dict()


def run_fixture_file(path: Path) -> dict[str, Any]:
    return evaluate_live_blocking_fixture(load_json(path))
