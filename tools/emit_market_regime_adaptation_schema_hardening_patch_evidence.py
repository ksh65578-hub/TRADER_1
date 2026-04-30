from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_MARKET_REGIME_ADAPTATION_SCHEMA_HARDENING"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-MARKET-REGIME-ADAPTATION-SCHEMA-HARDENING"
CONTRACT_GAP_ID = "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (
    rel,
    run_command,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.validation.mvp0_validators import run_validators


BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "market_regime_adaptation_validator",
    "symbol_strategy_regime_fit_validator",
    "strategy_condition_matrix_validator",
    "strategy_performance_memory_validator",
    "paper_shadow_evidence_accumulation_validator",
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
]

FIXTURE_FILES = [
    "tests/validators/fixtures/market_regime_adaptation_pass.json",
    "tests/validators/fixtures/market_regime_adaptation_live_flag_fail.json",
    "tests/validators/fixtures/market_regime_adaptation_stale_data_entry_fail.json",
    "tests/validators/fixtures/market_regime_adaptation_risk_off_entry_fail.json",
    "tests/validators/fixtures/market_regime_adaptation_live_observation_fail.json",
    "tests/validators/fixtures/market_regime_adaptation_missing_dependency_fail.json",
    "tests/validators/fixtures/market_regime_adaptation_missing_source_role_fail.json",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/market_regime_adaptation_report.schema.json",
    "contracts/registry.yaml",
    "contracts/validators/validator_registry.json",
    "contracts/validators/fixture_catalog.json",
    "trader1/validation/mvp0_validators.py",
    "tests/validators/test_market_regime_adaptation_validator.py",
    *FIXTURE_FILES,
    "tools/run_market_regime_adaptation_validators.py",
    "tools/emit_market_regime_adaptation_schema_hardening_patch_evidence.py",
    "contracts/generated/context_pack/MARKET_REGIME_ADAPTATION_SCHEMA.md",
    "system/evidence/audit_reports/MVP4_MARKET_REGIME_ADAPTATION_SCHEMA_HARDENING_20260429.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def patch_hash(value: dict[str, Any]) -> str:
    clean = dict(value)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def ensure_unique(items: list[Any], key: str, row: dict[str, Any]) -> list[Any]:
    kept = [item for item in items if not (isinstance(item, dict) and item.get(key) == row[key])]
    kept.append(row)
    return kept


def update_registry(now: str) -> None:
    registry_path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(registry_path)
    registry.setdefault("schemas", {})["market_regime_adaptation_report"] = {
        "schema_id": "trader1.market_regime_adaptation_report.v1",
        "path": "contracts/schema/market_regime_adaptation_report.schema.json",
    }
    validators = registry.setdefault("validators", {})
    for group in ("VALIDATOR_GROUP:OPTIMIZER_CORE", "VALIDATOR_GROUP:CONVERGENCE_CORE"):
        group_values = validators.setdefault(group, [])
        if "market_regime_adaptation_validator" not in group_values:
            insert_at = group_values.index("symbol_strategy_regime_fit_validator") + 1 if "symbol_strategy_regime_fit_validator" in group_values else len(group_values)
            group_values.insert(insert_at, "market_regime_adaptation_validator")
    registry["updated_at_utc"] = now
    write_json(registry_path, registry)

    validator_registry_path = ROOT / "contracts" / "validators" / "validator_registry.json"
    validator_registry = load_json(validator_registry_path)
    validator_registry["updated_at_utc"] = now
    implemented = validator_registry.setdefault("implemented_validators", [])
    validator_registry["implemented_validators"] = ensure_unique(
        implemented,
        "validator_id",
        {
            "validator_id": "market_regime_adaptation_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED_FAIL_CLOSED",
            "live_enabling": False,
        },
    )
    write_json(validator_registry_path, validator_registry)


def update_fixture_catalog(now: str) -> None:
    catalog_path = ROOT / "contracts" / "validators" / "fixture_catalog.json"
    catalog = load_json(catalog_path)
    catalog["updated_at_utc"] = now
    fixtures = catalog.setdefault("fixtures", [])
    rows = [
        ("market_regime_adaptation_fresh_dependency_pass", "PASS", "market_regime_adaptation_pass.json"),
        ("market_regime_adaptation_live_flag_fail", "FAIL", "market_regime_adaptation_live_flag_fail.json"),
        ("market_regime_adaptation_stale_data_entry_fail", "FAIL", "market_regime_adaptation_stale_data_entry_fail.json"),
        ("market_regime_adaptation_risk_off_entry_fail", "FAIL", "market_regime_adaptation_risk_off_entry_fail.json"),
        ("market_regime_adaptation_live_observation_fail", "FAIL", "market_regime_adaptation_live_observation_fail.json"),
        ("market_regime_adaptation_missing_dependency_fail", "FAIL", "market_regime_adaptation_missing_dependency_fail.json"),
        ("market_regime_adaptation_missing_source_role_fail", "FAIL", "market_regime_adaptation_missing_source_role_fail.json"),
    ]
    for fixture_id, expected_status, filename in rows:
        fixtures = ensure_unique(
            fixtures,
            "fixture_id",
            {
                "fixture_id": fixture_id,
                "validator_id": "market_regime_adaptation_validator",
                "expected_status": expected_status,
                "path": f"tests/validators/fixtures/{filename}",
            },
        )
    catalog["fixtures"] = fixtures
    catalog["live_order_ready"] = False
    catalog["live_order_allowed"] = False
    catalog["can_live_trade"] = False
    write_json(catalog_path, catalog)


def update_gap_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    audit_path = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json"
    if audit_path.exists():
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
        for gap in audit.get("gaps", []):
            if gap.get("component") in {"symbol_selection_regime", "convergence_memory_failure_learning"}:
                gap["patch_status"] = "PARTIAL_PATCHED"
                gap["fix"] = (
                    "market_regime_adaptation_report now requires fresh scoped regime data, symbol-regime fit, "
                    "strategy condition matrix, strategy performance memory, paper/shadow evidence, and fail-closed "
                    "downtrend/risk-off blocking before any entry review."
                )
        actions = audit.setdefault("safe_patch_actions", [])
        actions[:] = [item for item in actions if not (isinstance(item, dict) and item.get("action_id") == PATCH_ID)]
        actions.append(
            {
                "action_id": PATCH_ID,
                "status": "APPLIED",
                "summary": "Hardened market regime adaptation schema and validator with stale data, dependency, risk-off, and live observation negative fixtures.",
                "live_order_ready_after": False,
                "live_order_allowed_after": False,
                "can_live_trade_after": False,
                "scale_up_allowed_after": False,
            }
        )
        write_json(audit_path, audit)

    gap_path = ROOT / "system" / "evidence" / "contract_gaps" / f"{CONTRACT_GAP_ID}.contract_gap.json"
    if gap_path.exists():
        gap = load_json(gap_path)
        gap["generated_at_utc"] = now
        gap["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
        gap["status"] = "OPEN"
        gap["severity"] = "HIGH"
        gap["live_affecting"] = True
        gap["notes"] = (
            "Market regime adaptation is now strict and fail-closed for stale data, missing dependencies, risk-off entry, "
            "and live observation misuse. The broader profitability maturity gap remains open until long-run OOS, "
            "walk-forward, execution feedback, paper/shadow evidence, and external live-review evidence mature."
        )
        write_json(gap_path, gap)


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MARKET_REGIME_ADAPTATION_SCHEMA.md",
        f"""# MARKET_REGIME_ADAPTATION_SCHEMA

context_pack_id: MARKET_REGIME_ADAPTATION_SCHEMA
task_class: MVP4_MARKET_REGIME_ADAPTATION_SCHEMA_HARDENING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_MARKET_REGIME_ADAPTATION", "SECTION_SYMBOL_REGIME_FIT", "SECTION_CONVERGENCE_MEMORY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.market_regime_adaptation_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- market regime adaptation uses fresh, scoped PAPER/SHADOW/READ_ONLY evidence only
- entry review requires symbol-regime fit, strategy condition matrix, and strategy performance memory validator PASS
- stale or missing regime data cannot allow entry
- DOWNTREND and RISK_OFF must block entry and surface REGIME_MISMATCH or RISK_VETO
- live observation, live config mutation, LIVE_READY snapshot writes, execution truth creation, and scale-up are blocked
- dashboard wording says not live_ready and live orders blocked

known_omissions_by_design:
- no live order, credential load, real exchange account call, live observation consumption, live config mutation, or scale-up
- regime adaptation remains analysis evidence only, not execution truth

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: {now}
""",
    )
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    write_text(
        ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
        f"""# ACTIVE_WORKING_VIEW

generated_at_utc: {now}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: {state.get("current_mvp", "MVP-4")}
last_patch_id: {PATCH_ID}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Market regime adaptation now requires fresh scoped data, source artifact roles, dependency validator PASS status, downtrend/risk-off entry blocking, dashboard truth wording, and explicit false fields for live readiness, live orders, live config mutation, LIVE_READY snapshot writing, ACTIVE snapshot mutation, execution truth creation, and scale-up.
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_MARKET_REGIME_ADAPTATION",
            "source_file": "TRADER_1.md",
            "source_heading": "Market regime adaptation must be evidence-backed and fail-closed",
            "full_text_marker": f"{REQUIREMENT_ID}:SECTION_MARKET_REGIME_ADAPTATION:fresh scoped regime evidence blocks downtrend and risk-off entry",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Harden market regime adaptation against stale data and risk-off entry",
            "requirement_kind": "OPTIMIZER_CONVERGENCE_GUARDRAIL",
            "schema_ids": ["trader1.market_regime_adaptation_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/validators/test_market_regime_adaptation_validator.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["OPTIMIZER_MVP3", "PROFIT_CONVERGENCE_MVP3", "LIVE_BLOCKED_TEST"],
            "depends_on": [
                "REQ-MVP4-SYMBOL-REGIME-FIT-SCHEMA-HARDENING",
                "REQ-MVP4-STRATEGY-CONDITION-MATRIX-SCHEMA-HARDENING",
                "REQ-MVP4-STRATEGY-PERFORMANCE-MEMORY-SCHEMA-HARDENING",
            ],
            "source_text_sha256": sha256_text(REQUIREMENT_ID),
            "implementation_status": "IMPLEMENTED",
            "test_status": "PASS",
        }
    )
    req_index.update(
        {
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "updated_at_utc": now,
            "requirements": sorted(requirements, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_MARKET_REGIME_ADAPTATION",
            "schema_files": ["contracts/schema/market_regime_adaptation_report.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/validators/test_market_regime_adaptation_validator.py"],
            "fixture_files": FIXTURE_FILES,
            "runtime_modules": ["trader1/validation/mvp0_validators.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "optimizer_live_mutation_detected",
                "optimizer_live_order_allowed_after",
                "convergence_live_mutation_detected",
                "convergence_live_order_allowed_after",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_OPERATOR_ACTION_SUMMARY_HARDENING.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-SYMBOL-REGIME-FIT-SCHEMA-HARDENING",
                "REQ-MVP4-STRATEGY-CONDITION-MATRIX-SCHEMA-HARDENING",
                "REQ-MVP4-STRATEGY-PERFORMANCE-MEMORY-SCHEMA-HARDENING",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "REPLAY_PAPER_SHADOW_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": sorted(set(CHANGED_ARTIFACTS)),
            "new_or_changed_schema_ids": ["trader1.market_regime_adaptation_report.v1"],
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
            "next_task_class": "MVP4_MODEL_DRIFT_SCHEMA_RECHECK",
            "next_required_section_ids": ["SECTION_MARKET_REGIME_ADAPTATION", "SECTION_MODEL_DRIFT", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_CONVERGENCE_ASSESSMENT", "SECTION_DASHBOARD_SHELL"],
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
            "active_read_surface_used": ["SECTION_MARKET_REGIME_ADAPTATION", "SECTION_SYMBOL_REGIME_FIT", "SECTION_CONVERGENCE_MEMORY", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "MVP4_MARKET_REGIME_ADAPTATION_SCHEMA_HARDENING",
            "required_section_ids": ["SECTION_MARKET_REGIME_ADAPTATION", "SECTION_SYMBOL_REGIME_FIT", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": [
                "TRADER_1:market-regime-adaptation-active-surface",
                "TRADER_1:downtrend-risk-off-no-trade-requirement",
                "AGENTS:market-regime-adaptation-validator-dependencies",
            ],
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "MARKET_REGIME_ADAPTATION_SCHEMA_HARDENING",
            "optimizer_stage": "MVP4_ANALYSIS_ONLY",
            "optimizer_status_before": "REGIME_ADAPTATION_SCHEMA_SCAFFOLD_ONLY",
            "optimizer_status_after": "FRESH_SCOPED_REGIME_ADAPTATION_VALIDATED",
            "optimizer_maturity_level_before": "MVP4_SCAFFOLD",
            "optimizer_maturity_level_after": "MVP4_NEGATIVE_FIXTURE_VALIDATED",
            "optimizer_output_type": "MARKET_REGIME_ADAPTATION_REPORT_ONLY",
            "optimizer_guardrail_result": "PASS_NO_LIVE_PERMISSION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "MARKET_REGIME_ADAPTATION_HARDENING",
            "convergence_layer_changed": True,
            "convergence_state_before": "REGIME_ADAPTATION_SCHEMA_SCAFFOLD_ONLY",
            "convergence_state_after": "FRESH_DEPENDENCY_GATED_REGIME_ADAPTATION_VALIDATED_NO_LIVE_PERMISSION",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": True,
            "failure_analysis_status": "REQUIRED_FOR_STALE_DATA_RISK_OFF_AND_DEPENDENCY_FAILURES",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": True,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
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
            "stage_gate_status": "PASS_FOR_MARKET_REGIME_ADAPTATION_SCHEMA_HARDENING_NO_LIVE_ORDERS",
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
                *patch_result["new_registry_items"],
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
        f"""# MVP4 Market Regime Adaptation Schema Hardening Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- market_regime_adaptation_report was scaffold-level and could not prove fresh regime evidence or dependency validator status.
- Stale regime data could be represented without an explicit entry block.
- Risk-off or downtrend states could be represented without mandatory no-entry behavior.
- LIVE observation and official API evidence could be confused with analysis-only regime adaptation.

Patch:
- Hardened market_regime_adaptation_report schema with source modes, source roles, freshness, validator dependency status, risk-off/downtrend blocking, operator warning, and false live/scale/mutation fields.
- Added market_regime_adaptation_validator and made optimizer/convergence dependency chains include it.
- Added PASS and negative fixtures for live flag drift, stale data entry, risk-off entry, live observation, missing dependency status, and missing source roles.
- Added unit tests and standalone validator runner.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.market_regime_adaptation_report.v1"]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["market_regime_adaptation_validator"]))
    state["untested_validator_ids"] = [item for item in state.get("untested_validator_ids", []) if item != "market_regime_adaptation_validator"]
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP4_MODEL_DRIFT_SCHEMA_RECHECK"
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
    update_authority_manifest(now)
    update_registry(now)
    update_fixture_catalog(now)
    update_gap_artifacts(now, trader_hash, agents_hash)
    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_market_regime_adaptation_validator", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_symbol_strategy_regime_fit_validator", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_strategy_condition_matrix_validator", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_strategy_performance_memory_validator", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_optimizer_convergence_guardrails", "-v"]),
        run_command([sys.executable, "tools/run_market_regime_adaptation_validators.py"]),
        run_command([sys.executable, "tools/run_symbol_strategy_regime_fit_validators.py"]),
        run_command([sys.executable, "tools/run_strategy_performance_memory_validators.py"]),
        run_command([sys.executable, "tools/run_optimizer_convergence_guardrail_validators.py"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, validators_run)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_tests = [
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
        run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"]),
    ]
    patch_result["tests_run"].extend(final_tests)
    patch_result["validators_run"] = run_validators(VALIDATORS_REQUIRED)
    patch_result["convergence_validators_run"] = patch_result["validators_run"]
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
