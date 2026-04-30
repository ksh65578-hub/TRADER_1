from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_SCHEMA_FILES = [
    "common.defs.schema.json",
    "readiness_surface.schema.json",
    "runtime_config.schema.json",
    "safety_control_report.schema.json",
    "live_ready_snapshot.schema.json",
    "manual_order_test_evidence.schema.json",
    "final_decision.schema.json",
    "ledger_event.schema.json",
    "summary.schema.json",
    "read_only_dashboard_shell.schema.json",
    "runtime_stability_history.schema.json",
    "evidence_manifest.schema.json",
    "official_api_verification_report.schema.json",
    "validator_result.schema.json",
    "operator_action_audit.schema.json",
    "reconciliation_report.schema.json",
    "emergency_flatten_report.schema.json",
    "release_source_identity.schema.json",
    "contract_gap.schema.json",
    "patch_result.schema.json",
    "strategy_candidate.schema.json",
    "strategy_condition_matrix.schema.json",
    "candidate_generation_report.schema.json",
    "live_ready_candidate_writer_input.schema.json",
    "validator_fixture_catalog.schema.json",
    "profit_optimizer_config.schema.json",
    "candidate_scorecard.schema.json",
    "optimizer_run_report.schema.json",
    "optimization_state.schema.json",
    "search_space_snapshot.schema.json",
    "parameter_narrowing_report.schema.json",
    "symbol_strategy_regime_fit_report.schema.json",
    "optimizer_feedback_report.schema.json",
    "overfit_diagnostic_report.schema.json",
    "optimizer_recommendation_report.schema.json",
    "optimizer_guardrail_report.schema.json",
    "convergence_objective_profile.schema.json",
    "optimizer_memory_state.schema.json",
    "strategy_performance_memory.schema.json",
    "failure_analysis_report.schema.json",
    "market_regime_adaptation_report.schema.json",
    "exploration_exploitation_policy.schema.json",
    "risk_scaling_decision.schema.json",
    "convergence_assessment_report.schema.json",
    "model_drift_report.schema.json",
    "live_burn_in_feedback_report.schema.json",
    "profit_convergence_cycle_report.schema.json",
    "upbit_paper_dry_run_report.schema.json",
    "intent_wal_event.schema.json",
    "restart_recovery_report.schema.json",
    "strategy_unit.schema.json",
    "position_sizing_decision.schema.json",
    "replay_consistency_report.schema.json",
    "paper_shadow_separation_report.schema.json",
    "paper_shadow_evidence_accumulation_report.schema.json",
    "paper_operation_gate_report.schema.json",
    "read_only_account_snapshot.schema.json",
    "private_stream_health.schema.json",
    "upbit_read_only_reconciliation_path.schema.json",
    "api_key_permission_check_report.schema.json",
    "live_preflight_report.schema.json",
    "live_review_dashboard.schema.json",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fail(message: str) -> int:
    print(json.dumps({"status": "FAIL", "message": message}, indent=2))
    return 1


def main() -> int:
    if not (ROOT / "TRADER_1.md").exists() or not (ROOT / "AGENTS.md").exists():
        return fail("authority files missing")

    registry = load_json(ROOT / "contracts" / "registry.yaml")
    if registry["authority"]["authority_sha256"].startswith("__"):
        return fail("registry authority hash placeholder remains")
    if registry["live_defaults"] != {"live_order_ready": False, "live_order_allowed": False, "can_live_trade": False, "scale_up_allowed": False}:
        return fail("registry live defaults are not fail-closed")

    for name in REQUIRED_SCHEMA_FILES:
        path = ROOT / "contracts" / "schema" / name
        if not path.exists():
            return fail(f"missing schema: {name}")
        schema = load_json(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            return fail(f"schema draft mismatch: {name}")
        if schema.get("additionalProperties") is not False:
            return fail(f"schema does not default closed: {name}")

    generated = [
        "authority_section_map.json",
        "requirement_index.json",
        "requirement_artifact_matrix.json",
        "read_cache_manifest.json",
        "current_implementation_state.json",
    ]
    for name in generated:
        load_json(ROOT / "contracts" / "generated" / name)

    patch_result = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP0_CONTRACT_BASELINE.patch_result.json")
    invariants = {
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "live_order_ready_after": False,
        "live_order_allowed_after": False,
        "can_live_trade_after": False,
        "retained_archive_read": False,
        "full_document_read": False,
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_allowed_after": False,
    }
    for key, expected in invariants.items():
        if patch_result.get(key) != expected:
            return fail(f"patch_result invariant failed: {key}")

    print(json.dumps({"status": "PASS", "schemas_checked": len(REQUIRED_SCHEMA_FILES), "live_order_allowed_after": False}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
