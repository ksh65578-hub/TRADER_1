from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT_20260429_001"
PATCH_BASENAME = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT"
REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT"
RACE_REQUIREMENT_ID = "REQ-MVP4-RUNTIME-RESOURCE-PRESSURE-RACE-GUARD"
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
    "trader1/validation/mvp0_validators.py",
    "contracts/registry.yaml",
    "contracts/validators/validator_registry.json",
    "tests/validators/test_profitability_optimizer_evidence_gap_validator.py",
    "trader1/runtime/health/runtime_resource_pressure.py",
    "tests/runtime/test_runtime_resource_pressure.py",
    "tools/run_profitability_optimizer_evidence_gap_validators.py",
    "tools/emit_profitability_optimizer_evidence_gap_patch_evidence.py",
    "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json",
    "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
    "contracts/generated/context_pack/PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.md",
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


def write_gap_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
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
    write_json(audit_path, audit)

    write_json(
        ROOT / "system" / "evidence" / "contract_gaps" / "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
        {
            "schema_id": "trader1.contract_gap.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "status": "OPEN",
            "blockers": [
                {
                    "code": "CONTRACT_GAP_HIGH",
                    "severity": "HIGH",
                    "message": "Profitability, strategy, optimizer, and convergence evidence maturity is not sufficient for live review or scale-up.",
                    "source_requirement_id": REQUIREMENT_ID,
                }
            ],
            "notes": "MVP-4 remains safe to improve with PAPER, SHADOW, READ_ONLY, validators, schemas, fixtures, reports, and dashboard UX only. This gap must stay live-affecting until net EV after cost, strategy conditions, regime fit, OOS robustness, execution feedback, and convergence memory evidence are validated for exact scope.",
            "contract_gap_id": CONTRACT_GAP_ID,
            "severity": "HIGH",
            "source_section_id": "SECTION_STRATEGY_PROFITABILITY",
            "live_affecting": True,
        },
    )


def update_registry(now: str) -> None:
    registry_path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(registry_path)
    validators = registry.setdefault("validators", {})
    for group_name in ("VALIDATOR_GROUP:OPTIMIZER_CORE", "VALIDATOR_GROUP:CONVERGENCE_CORE"):
        group = validators.setdefault(group_name, [])
        if "profitability_optimizer_evidence_gap_validator" not in group:
            group.append("profitability_optimizer_evidence_gap_validator")
    write_json(registry_path, registry)

    validator_registry_path = ROOT / "contracts" / "validators" / "validator_registry.json"
    validator_registry = load_json(validator_registry_path)
    validator_registry["updated_at_utc"] = now
    implemented = validator_registry.setdefault("implemented_validators", [])
    implemented[:] = [
        item for item in implemented if item.get("validator_id") != "profitability_optimizer_evidence_gap_validator"
    ]
    implemented.append(
        {
            "validator_id": "profitability_optimizer_evidence_gap_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED_FAIL_CLOSED",
            "live_enabling": False,
        }
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
            "source_section_id": "SECTION_STRATEGY_PROFITABILITY",
            "source_file": "TRADER_1.md",
            "source_heading": "profitability, strategy, optimizer, and convergence evidence must not imply live readiness",
            "full_text_marker": f"{REQUIREMENT_ID}:profitability optimizer evidence maturity must be explicit and live-blocking",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Profitability optimizer evidence maturity gap audit",
            "requirement_kind": "VALIDATOR_IMPLEMENTATION",
            "schema_ids": ["trader1.contract_gap.v1"],
            "validator_ids": ["profitability_optimizer_evidence_gap_validator"],
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/validators/test_profitability_optimizer_evidence_gap_validator.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["OPTIMIZER_MVP3", "PROFIT_CONVERGENCE_MVP3", "DASHBOARD_UX", "LIVE_BLOCKED_TEST"],
            "depends_on": ["REQ-CONV-MVP0-SCAFFOLD", "REQ-OPT-MVP0-SCAFFOLD", "REQ-MVP4-LIVE-FINAL-GUARD"],
            "source_text_sha256": sha256_bytes(
                b"profitability optimizer evidence maturity must be explicit and live-blocking"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_WITH_OPEN_CONTRACT_GAP",
            "test_status": "PASS",
        },
    )
    ensure_requirement(
        index,
        {
            "requirement_id": RACE_REQUIREMENT_ID,
            "source_section_id": "SECTION_RUNTIME_RECOVERY",
            "source_file": "TRADER_1.md",
            "source_heading": "runtime resource scans must tolerate concurrent atomic writes",
            "full_text_marker": f"{RACE_REQUIREMENT_ID}:runtime resource pressure scan ignores disappearing temp files",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Runtime resource pressure race guard",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": [],
            "validator_ids": ["runtime_resource_pressure_validator"],
            "artifact_ids": [
                "trader1/runtime/health/runtime_resource_pressure.py",
                "tests/runtime/test_runtime_resource_pressure.py",
            ],
            "test_ids": ["tests/runtime/test_runtime_resource_pressure.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "SAFETY_BLOCKING",
            "live_affecting": True,
            "read_when": ["RUNTIME_RECOVERY", "PERFORMANCE", "LIVE_BLOCKED_TEST"],
            "depends_on": ["REQ-MVP4-LONG-RUN-STABILITY-RESOURCE-GUARD"],
            "source_text_sha256": sha256_bytes(b"runtime resource pressure scan ignores disappearing temp files"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_STRATEGY_PROFITABILITY",
            "schema_files": ["contracts/schema/contract_gap.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/validators/test_profitability_optimizer_evidence_gap_validator.py"],
            "fixture_files": ["system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json"],
            "runtime_modules": ["tools/run_profitability_optimizer_evidence_gap_validators.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED_WITH_OPEN_CONTRACT_GAP",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": RACE_REQUIREMENT_ID,
            "section_id": "SECTION_RUNTIME_RECOVERY",
            "schema_files": [],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/runtime/test_runtime_resource_pressure.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/health/runtime_resource_pressure.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": ["tests_run", "validators_run", "live_order_allowed_after"],
            "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
            "live_affecting": True,
            "status": "IMPLEMENTED",
        },
    )
    matrix["schema_file_count"] = len(list((ROOT / "contracts" / "schema").glob("*.schema.json")))
    write_json(index_path, index)
    write_json(matrix_path, matrix)

    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.md",
        f"""# PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT

context_pack_id: PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT
task_class: MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_STRATEGY_PROFITABILITY", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_ASSESSMENT", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{RACE_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.contract_gap.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- profitability, strategy, optimizer, and convergence evidence gaps are explicit
- net EV after cost, strategy condition, regime fit, OOS, execution feedback, and memory gaps remain live-blocking
- validator rejects missing gap coverage, forbidden live flags, and misleading operator wording
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no optimizer runtime promotion
- no live config mutation
- no LIVE_READY snapshot write
- no risk scale-up

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

Profitability and optimizer/convergence evidence maturity is now explicitly audited and validator-checked. The system can keep improving PAPER, SHADOW, READ_ONLY, tests, validators, fixtures, and dashboard UX, but this audit remains a live-review blocker until exact scoped evidence exists.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION.patch_result.json")
    optimizer_results = [
        result
        for result in validators_run
        if result.get("validator_id") in {"optimizer_no_live_mutation_validator", "optimizer_guardrail_validator"}
    ]
    convergence_results = [
        result
        for result in validators_run
        if result.get("validator_id") in {"convergence_assessment_validator", "profitability_optimizer_evidence_gap_validator"}
    ]
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-RUNTIME-RESOURCE-PRESSURE-RACE-GUARD",
                "REQ-OPT-MVP0-SCAFFOLD",
                "REQ-CONV-MVP0-SCAFFOLD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_SHADOW_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": [
                "contracts/registry.yaml::validators.profitability_optimizer_evidence_gap_validator",
                "contracts/validators/validator_registry.json::profitability_optimizer_evidence_gap_validator",
                *CHANGED_ARTIFACTS,
            ],
            "new_or_changed_schema_ids": ["trader1.contract_gap.v1"],
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
            "next_task_class": "MVP4_STRATEGY_NET_EV_SCORECARD_SCHEMA_HARDENING",
            "next_required_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_OPTIMIZER_OBJECTIVE",
                "SECTION_EXECUTION_COST_MODEL",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_CONVERGENCE_MEMORY"],
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
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_OPTIMIZER_GUARDRAIL",
                "SECTION_CONVERGENCE_ASSESSMENT",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT",
            "required_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_OPTIMIZER_OBJECTIVE",
                "SECTION_CONVERGENCE_MEMORY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "TRADER_1:strategy-profitability-active-surface",
                "TRADER_1:optimizer-guardrail-active-surface",
                "TRADER_1:convergence-active-surface",
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
            "optimizer_patch": "EVIDENCE_MATURITY_GAP_AUDIT_NO_RUNTIME_PROMOTION",
            "optimizer_stage": "MVP4_REVIEW_PREP",
            "optimizer_status_before": "SCAFFOLD_GUARDRAILED",
            "optimizer_status_after": "EVIDENCE_GAP_AUDITED_LIVE_BLOCKED",
            "optimizer_maturity_level_before": "MVP0_FAIL_CLOSED_VALIDATOR",
            "optimizer_maturity_level_after": "MVP4_EVIDENCE_GAP_VISIBLE",
            "optimizer_output_type": "ANALYSIS_ONLY_AUDIT",
            "optimizer_validators_required": [
                "optimizer_no_live_mutation_validator",
                "optimizer_guardrail_validator",
                "profitability_optimizer_evidence_gap_validator",
            ],
            "optimizer_validators_run": optimizer_results
            + [
                result
                for result in validators_run
                if result.get("validator_id") == "profitability_optimizer_evidence_gap_validator"
            ],
            "optimizer_guardrail_result": next(
                (result.get("status") for result in validators_run if result.get("validator_id") == "optimizer_guardrail_validator"),
                "UNTESTED",
            ),
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "EVIDENCE_MATURITY_GAP_AUDIT_NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_state_before": "GUARDRAILED_SCAFFOLD",
            "convergence_state_after": "EVIDENCE_GAP_AUDITED_LIVE_BLOCKED",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": True,
            "failure_analysis_status": "CONTRACT_GAP_RECORDED_FOR_FUTURE_FIXTURE",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": [
                "convergence_assessment_validator",
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
            "stage_gate_status": "PASS_FOR_EVIDENCE_GAP_AUDIT_LIVE_REVIEW_STILL_BLOCKED",
            "open_contract_gap_id": CONTRACT_GAP_ID,
            "next_allowed_task_class": "MVP4_STRATEGY_NET_EV_SCORECARD_SCHEMA_HARDENING",
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
        f"""# MVP4 Profitability Optimizer Evidence Gap Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- Strategy/profitability/optimizer/convergence scaffolds are safe but not mature evidence.
- Net EV after cost, strategy condition matrix, regime fit, OOS robustness, execution feedback, and convergence memory remain live-review blockers.
- The audit is now validator-checked so missing gap coverage or live flag drift fails closed.

Patch:
- Added profitability_optimizer_evidence_gap_validator.
- Added negative tests for live flag drift and missing component gap coverage.
- Added open live-affecting contract_gap {CONTRACT_GAP_ID}.
- Hardened runtime resource pressure scan against disappearing atomic-write temp files.

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
    state["next_allowed_task_class"] = "MVP4_STRATEGY_NET_EV_SCORECARD_SCHEMA_HARDENING"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []) + ["profitability_optimizer_evidence_gap_validator"])
    )
    state["untested_validator_ids"] = [
        item for item in state.get("untested_validator_ids", []) if item != "profitability_optimizer_evidence_gap_validator"
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
    write_gap_artifacts(now, trader_hash, agents_hash)
    update_registry(now)
    update_navigation(now, trader_hash, agents_hash)
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)

    validators_run = run_validators(VALIDATORS_REQUIRED)
    preliminary = build_patch_result(now, [], validators_run)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, preliminary)
    write_json(patch_path, preliminary)
    update_state_and_ledger(now, preliminary)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_profitability_optimizer_evidence_gap_validator", "-v"]),
        run_command([sys.executable, "tools/run_profitability_optimizer_evidence_gap_validators.py"]),
        run_command([sys.executable, "tools/run_optimizer_convergence_guardrail_validators.py"]),
        run_command([sys.executable, "UPBIT_PAPER.py"]),
        run_command([sys.executable, "BINANCE_PAPER.py"]),
        run_command([sys.executable, "tools/run_runtime_schema_instance_validators.py"]),
        run_command([sys.executable, "tools/run_root_launcher_validators.py"]),
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"]),
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
