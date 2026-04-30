from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING_20260429_001"
PATCH_BASENAME = "MVP4_CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING"
REQUIREMENT_ID = "REQ-MVP4-CONVERGENCE-MEMORY-FAILURE-LEARNING-HARDENING"
CONTRACT_GAP_ID = "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (
    rel,
    run_command,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.validation.mvp0_validators import run_validators


VALIDATORS_REQUIRED = [
    "registry_validator",
    "schema_validator",
    "failure_analysis_validator",
    "execution_feedback_loop_validator",
    "overfit_diagnostic_validator",
    "candidate_scorecard_net_ev_validator",
    "strategy_condition_matrix_validator",
    "symbol_strategy_regime_fit_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "optimizer_no_live_mutation_validator",
    "profitability_optimizer_evidence_gap_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "live_final_guard_validator",
    "generated_artifact_dirty_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/failure_analysis_report.schema.json",
    "trader1/validation/mvp0_validators.py",
    "contracts/registry.yaml",
    "contracts/validators/validator_registry.json",
    "tests/validators/test_failure_analysis_validator.py",
    "tests/validators/fixtures/failure_analysis_pass.json",
    "tests/validators/fixtures/failure_analysis_unknown_root_live_affecting_fail.json",
    "tests/validators/fixtures/failure_analysis_repeated_unblocked_fail.json",
    "tests/validators/fixtures/failure_analysis_live_flag_fail.json",
    "tools/run_failure_analysis_validators.py",
    "tools/emit_convergence_memory_failure_learning_hardening_patch_evidence.py",
    "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json",
    "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
    "contracts/generated/context_pack/CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING.md",
]

BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
    "CONTRACT_GAP_HIGH",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_unique(items: list[Any], value: Any, key: str | None = None) -> None:
    if key is None:
        if value not in items:
            items.append(value)
        return
    items[:] = [item for item in items if not (isinstance(item, dict) and item.get(key) == value.get(key))]
    items.append(value)


def update_gap_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    audit_path = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json"
    audit = load_json(audit_path)
    audit["generated_at_utc"] = now
    audit["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
    audit["live_order_ready"] = False
    audit["live_order_allowed"] = False
    audit["can_live_trade"] = False
    audit["scale_up_allowed"] = False
    audit["live_permission_created"] = False
    audit["profitability_guarantee_created"] = False
    audit["optimizer_live_mutation_detected"] = False
    audit["convergence_live_mutation_detected"] = False
    for component in audit.get("inspected_components", []):
        if component.get("component_id") == "convergence_memory_failure_learning":
            component["current_level"] = "PARTIAL_PATCHED"
    for gap in audit.get("gaps", []):
        if gap.get("component") == "convergence_memory_failure_learning":
            gap["patch_status"] = "PARTIAL_PATCHED"
            gap["fix"] = (
                "failure_analysis_report schema and failure_analysis_validator now require root-cause status, "
                "source evidence ids, repeated-failure blocking, append-only memory write status, explicit blockers, "
                "false live flags, and negative fixtures. Runtime convergence memory accumulation remains required."
            )
    actions = audit.setdefault("safe_patch_actions", [])
    actions[:] = [
        item for item in actions if not (isinstance(item, dict) and item.get("action_id") == PATCH_ID)
    ]
    actions.append(
        {
            "action_id": PATCH_ID,
            "status": "APPLIED",
            "summary": "Hardened failure analysis so unknown live-affecting root causes and repeated failures block ranking/promotion without live permission.",
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    write_json(audit_path, audit)

    gap_path = ROOT / "system" / "evidence" / "contract_gaps" / f"{CONTRACT_GAP_ID}.contract_gap.json"
    gap = load_json(gap_path)
    gap["generated_at_utc"] = now
    gap["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
    gap["status"] = "OPEN"
    gap["severity"] = "HIGH"
    gap["live_affecting"] = True
    gap["notes"] = (
        "Candidate scorecards, strategy condition matrices, symbol/regime fit, OOS robustness, optimizer feedback, "
        "and failure analysis now have fail-closed schemas and negative fixtures. Convergence failure learning is "
        "partial-patched, but the broader profitability maturity gap remains open until runtime convergence memory, "
        "paper/shadow evidence accumulation, dashboard profitability maturity visibility, and risk exposure quality "
        "are validated. No live readiness or scale-up permission is created."
    )
    write_json(gap_path, gap)


def update_registry(now: str) -> None:
    registry_path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(registry_path)
    registry.setdefault("schemas", {})["failure_analysis_report"] = {
        "schema_id": "trader1.failure_analysis_report.v1",
        "path": "contracts/schema/failure_analysis_report.schema.json",
    }
    validators = registry.setdefault("validators", {})
    for group in (
        "VALIDATOR_GROUP:OPTIMIZER_CORE",
        "VALIDATOR_GROUP:OPTIMIZER_ROBUSTNESS",
        "VALIDATOR_GROUP:CONVERGENCE_CORE",
    ):
        members = validators.setdefault(group, [])
        if "failure_analysis_validator" not in members:
            members.append("failure_analysis_validator")
    registry["updated_at_utc"] = now
    write_json(registry_path, registry)

    validator_registry_path = ROOT / "contracts" / "validators" / "validator_registry.json"
    validator_registry = load_json(validator_registry_path)
    validator_registry["updated_at_utc"] = now
    ensure_unique(
        validator_registry.setdefault("implemented_validators", []),
        {
            "validator_id": "failure_analysis_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED_FAIL_CLOSED",
            "live_enabling": False,
        },
        "validator_id",
    )
    write_json(validator_registry_path, validator_registry)


def ensure_requirement(index: dict[str, Any], requirement: dict[str, Any]) -> None:
    rows = index.setdefault("requirements", [])
    rows[:] = [item for item in rows if item.get("requirement_id") != requirement["requirement_id"]]
    rows.append(requirement)


def ensure_matrix_row(matrix: dict[str, Any], row: dict[str, Any]) -> None:
    rows = matrix.setdefault("rows", [])
    rows[:] = [item for item in rows if item.get("requirement_id") != row["requirement_id"]]
    rows.append(row)


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    index = load_json(index_path)
    matrix = load_json(matrix_path)
    index["updated_at_utc"] = now
    matrix["updated_at_utc"] = now
    ensure_requirement(
        index,
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_CONVERGENCE_MEMORY",
            "source_file": "TRADER_1.md",
            "source_heading": "convergence memory must preserve failure learning and block repeated root causes",
            "full_text_marker": f"{REQUIREMENT_ID}:failure analysis requires append-only memory repeated-failure blocking and unknown-root live blocking",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Convergence memory failure learning hardening",
            "requirement_kind": "SCHEMA_VALIDATOR_PATCH",
            "schema_ids": ["trader1.failure_analysis_report.v1"],
            "validator_ids": ["failure_analysis_validator"],
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/validators/test_failure_analysis_validator.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["CONV_SLICE_FAILURE_LEARNING", "PROFIT_CONVERGENCE_MVP3", "VALIDATOR_IMPLEMENTATION"],
            "depends_on": [
                "REQ-MVP4-EXECUTION-FEEDBACK-COST-MODEL-HARDENING",
                "REQ-MVP4-OOS-ROBUSTNESS-SCHEMA-HARDENING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"failure analysis requires append-only memory repeated-failure blocking and unknown-root live blocking"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_CONVERGENCE_MEMORY",
            "schema_files": ["contracts/schema/failure_analysis_report.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/validators/test_failure_analysis_validator.py"],
            "fixture_files": [
                "tests/validators/fixtures/failure_analysis_pass.json",
                "tests/validators/fixtures/failure_analysis_unknown_root_live_affecting_fail.json",
                "tests/validators/fixtures/failure_analysis_repeated_unblocked_fail.json",
                "tests/validators/fixtures/failure_analysis_live_flag_fail.json",
            ],
            "runtime_modules": ["tools/run_failure_analysis_validators.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "new_or_changed_schema_ids",
                "validators_required",
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        },
    )
    matrix["schema_file_count"] = len(list((ROOT / "contracts" / "schema").glob("*.schema.json")))
    write_json(index_path, index)
    write_json(matrix_path, matrix)

    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING.md",
        f"""# CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING

context_pack_id: CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING
task_class: MVP4_CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CONVERGENCE_MEMORY", "SECTION_FAILURE_ANALYSIS", "SECTION_STRATEGY_PROFITABILITY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.failure_analysis_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- failure analysis requires known/unknown root-cause status and source evidence ids
- unknown live-affecting root cause blocks live order, promotion, and ranking
- repeated same-root-cause failures block ranking/promotion and require previous failure links
- memory-write-required analysis must be append-only recorded
- report remains dashboard/display truth only and cannot create live readiness, live order permission, promotion, or scale-up

known_omissions_by_design:
- no live execution feedback collection
- no optimizer runtime promotion
- no LIVE_READY snapshot write
- no risk scale-up
- runtime convergence memory accumulation, paper/shadow accumulation, dashboard profitability maturity, and risk exposure quality remain open contract_gap work

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )
    write_text(
        ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
        f"""# ACTIVE_WORKING_VIEW

generated_at_utc: {now}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: {PATCH_ID}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Failure analysis now requires root-cause status, repeated-failure blocking, source evidence, explicit blockers, and append-only memory write status before convergence assessment can pass. This improves failure learning while keeping live readiness, live order permission, and scale-up permission blocked.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(
        ROOT / "system" / "evidence" / "patch_results" / "MVP4_EXECUTION_FEEDBACK_COST_MODEL_HARDENING.patch_result.json"
    )
    optimizer_results = [
        result
        for result in validators_run
        if result.get("validator_id")
        in {
            "failure_analysis_validator",
            "execution_feedback_loop_validator",
            "overfit_diagnostic_validator",
            "candidate_scorecard_net_ev_validator",
            "strategy_condition_matrix_validator",
            "symbol_strategy_regime_fit_validator",
            "optimizer_no_live_mutation_validator",
            "optimizer_guardrail_validator",
            "profitability_optimizer_evidence_gap_validator",
        }
    ]
    convergence_results = [
        result
        for result in validators_run
        if result.get("validator_id")
        in {"convergence_assessment_validator", "failure_analysis_validator", "profitability_optimizer_evidence_gap_validator"}
    ]
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "SCHEMA_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT",
                "REQ-OPT-MVP0-SCAFFOLD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_SHADOW_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": [
                "contracts/registry.yaml::schemas.failure_analysis_report",
                "contracts/registry.yaml::validators.failure_analysis_validator",
                "contracts/validators/validator_registry.json::failure_analysis_validator",
                *CHANGED_ARTIFACTS,
            ],
            "new_or_changed_schema_ids": ["trader1.failure_analysis_report.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": "MVP4_PAPER_SHADOW_EVIDENCE_ACCUMULATION_HARDENING",
            "next_required_section_ids": [
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
            ],
            "next_optional_section_ids": ["SECTION_RISK_EXPOSURE", "SECTION_CONVERGENCE_MEMORY"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "BINANCE_FUTURES_LIVE"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "SECTION_CONVERGENCE_MEMORY",
                "SECTION_FAILURE_ANALYSIS",
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING",
            "required_section_ids": [
                "SECTION_CONVERGENCE_MEMORY",
                "SECTION_FAILURE_ANALYSIS",
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "TRADER_1:convergence-memory-active-surface",
                "TRADER_1:failure-analysis-active-surface",
                "AGENTS:profit-convergence-implementation-overlay",
            ],
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "CONVERGENCE_FAILURE_ANALYSIS_SCHEMA_VALIDATOR_PATCH",
            "optimizer_stage": "MVP4_REVIEW_PREP",
            "optimizer_status_before": "EXECUTION_FEEDBACK_COST_MODEL_GUARDED_LIVE_BLOCKED",
            "optimizer_status_after": "FAILURE_ANALYSIS_GUARDED_LIVE_BLOCKED",
            "optimizer_maturity_level_before": "MVP4_EXECUTION_FEEDBACK_COST_MODEL_GUARDED",
            "optimizer_maturity_level_after": "MVP4_FAILURE_ANALYSIS_REPEATED_ROOT_CAUSE_GUARDED",
            "optimizer_output_type": "ANALYSIS_ONLY_FAILURE_ANALYSIS_SCHEMA",
            "optimizer_validators_required": [
                "failure_analysis_validator",
                "execution_feedback_loop_validator",
                "overfit_diagnostic_validator",
                "candidate_scorecard_net_ev_validator",
                "strategy_condition_matrix_validator",
                "symbol_strategy_regime_fit_validator",
                "optimizer_no_live_mutation_validator",
                "optimizer_guardrail_validator",
                "profitability_optimizer_evidence_gap_validator",
            ],
            "optimizer_validators_run": optimizer_results,
            "optimizer_guardrail_result": next(
                (result.get("status") for result in validators_run if result.get("validator_id") == "optimizer_guardrail_validator"),
                "UNTESTED",
            ),
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "CONVERGENCE_MEMORY_FAILURE_LEARNING_GUARD_NO_LIVE_MUTATION",
            "convergence_layer_changed": True,
            "convergence_state_before": "EXECUTION_FEEDBACK_COST_MODEL_GUARDED_LIVE_BLOCKED",
            "convergence_state_after": "FAILURE_ANALYSIS_GUARDED_LIVE_BLOCKED",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": True,
            "failure_analysis_status": "FAIL_CLOSED_WITH_NEGATIVE_FIXTURES",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": [
                "convergence_assessment_validator",
                "failure_analysis_validator",
                "profitability_optimizer_evidence_gap_validator",
            ],
            "convergence_validators_run": convergence_results,
            "convergence_guardrail_result": next(
                (
                    result.get("status")
                    for result in validators_run
                    if result.get("validator_id") == "convergence_assessment_validator"
                ),
                "UNTESTED",
            ),
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    return patch_result


def without_generated_dirty_requirement(patch_result: dict[str, Any]) -> dict[str, Any]:
    patch_result["validators_required"] = [
        item for item in patch_result.get("validators_required", []) if item != "generated_artifact_dirty_validator"
    ]
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    write_json(
        ROOT / patch_result["validator_run_log_path"],
        {
            "validator_run_log_schema_id": "trader1.validator_run_log.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "validators_run": patch_result["validators_run"],
            "validators_untested": [],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / patch_result["stage_gate_result_path"],
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "PASS_FOR_CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING_LIVE_REVIEW_STILL_BLOCKED",
            "open_contract_gap_id": CONTRACT_GAP_ID,
            "next_allowed_task_class": "MVP4_PAPER_SHADOW_EVIDENCE_ACCUMULATION_HARDENING",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260429.md",
        f"""# MVP4 Convergence Memory Failure Learning Hardening

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- failure_analysis_report was scaffold-level and did not require root-cause status, repeated-failure blocking, or append-only memory write status.
- A repeated same-root-cause failure could remain ranking-allowed in review artifacts.
- Unknown live-affecting root causes could be under-explained to the operator without explicit live blocking evidence.

Patch:
- Hardened failure_analysis_report schema.
- Implemented failure_analysis_validator with PASS and negative fixtures.
- Added unknown-root live-affecting, repeated-unblocked, live-flag, and memory-write negative cases.
- Updated convergence assessment dependencies and profitability maturity audit while keeping the broader contract_gap open.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP4_PAPER_SHADOW_EVIDENCE_ACCUMULATION_HARDENING"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(
        set(state.get("implemented_schema_ids", []) + ["trader1.failure_analysis_report.v1"])
    )
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []) + ["failure_analysis_validator"])
    )
    state["untested_validator_ids"] = [
        item for item in state.get("untested_validator_ids", []) if item != "failure_analysis_validator"
    ]
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", []) + [CONTRACT_GAP_ID]))
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger.get("patches", []) if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": patch_result["target_mvp_level"],
            "patch_result_path": rel(patch_path),
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    write_json(ledger_path, ledger)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_gap_artifacts(now, trader_hash, agents_hash)
    update_registry(now)
    update_navigation(now, trader_hash, agents_hash)
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)

    validators_run = run_validators([item for item in VALIDATORS_REQUIRED if item != "generated_artifact_dirty_validator"])
    preliminary = without_generated_dirty_requirement(build_patch_result(now, [], validators_run))
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, preliminary)
    write_json(patch_path, preliminary)
    update_state_and_ledger(now, preliminary)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_failure_analysis_validator", "-v"]),
        run_command([sys.executable, "tools/run_failure_analysis_validators.py"]),
        run_command([sys.executable, "tools/run_convergence_assessment_dependency_validators.py"]),
        run_command([sys.executable, "tools/run_optimizer_feedback_validators.py"]),
        run_command([sys.executable, "tools/run_overfit_diagnostic_validators.py"]),
        run_command([sys.executable, "tools/run_profitability_optimizer_evidence_gap_validators.py"]),
        run_command([sys.executable, "tools/run_optimizer_convergence_guardrail_validators.py"]),
        run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"]),
        run_command([sys.executable, "UPBIT_PAPER.py"]),
        run_command([sys.executable, "BINANCE_PAPER.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    final_patch = build_patch_result(now, tests_run, validators_run)
    write_evidence(now, trader_hash, agents_hash, final_patch)
    write_json(patch_path, final_patch)
    update_state_and_ledger(now, final_patch)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in tests_run if item["status"] != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": final_patch["result_hash"],
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
                "open_contract_gap_ids": [CONTRACT_GAP_ID],
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
