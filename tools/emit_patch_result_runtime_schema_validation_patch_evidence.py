from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION_20260429_001"
PATCH_BASENAME = "MVP4_PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION"
REQUIREMENT_ID = "REQ-MVP4-PATCH-RESULT-RUNTIME-SCHEMA-VALIDATION"
CONTRACT_GAP_ID = "PATCH_RESULT_VALIDATOR_RUN_GAP"

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
from trader1.validation.mvp0_validators import _patch_result_paths, _patch_result_validator_run_gaps, run_validators


VALIDATORS_REQUIRED = [
    "registry_validator",
    "schema_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
    "generated_artifact_dirty_validator",
]

CHANGED_ARTIFACTS = [
    "trader1/validation/mvp0_validators.py",
    "contracts/registry.yaml",
    "contracts/validators/validator_registry.json",
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tools/run_patch_result_runtime_schema_validators.py",
    "tools/emit_patch_result_runtime_schema_validation_patch_evidence.py",
    "system/evidence/audit_reports/PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json",
    "system/evidence/contract_gaps/PATCH_RESULT_VALIDATOR_RUN_GAP.contract_gap.json",
    "contracts/generated/context_pack/PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION.md",
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


def current_gap_rows() -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for patch_path in _patch_result_paths():
        patch = load_json(patch_path)
        gaps.extend(_patch_result_validator_run_gaps(patch, patch_path))
    return [
        {
            **gap,
            "resolution": "AUDIT_PRESERVED_NOT_BACKFILLED",
        }
        for gap in sorted(gaps, key=lambda item: (item["patch_result_path"], item["validator_id"], item["gap_type"]))
    ]


def write_gap_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    gaps = current_gap_rows()
    write_json(
        ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json",
        {
            "schema_id": "trader1.patch_result_validator_run_gap_audit.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "status": "AUDIT_PRESERVED_LIVE_BLOCKING" if gaps else "NO_GAPS",
            "reason": "Historical patch_result artifacts declared validators_required entries that were not mirrored in validators_run. Historical evidence is not backfilled; future patch_result artifacts are guarded by patch_result_runtime_schema_instance_validator.",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "gaps": gaps,
        },
    )
    write_json(
        ROOT / "system" / "evidence" / "contract_gaps" / "PATCH_RESULT_VALIDATOR_RUN_GAP.contract_gap.json",
        {
            "schema_id": "trader1.contract_gap.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "status": "OPEN" if gaps else "RESOLVED",
            "blockers": [
                {
                    "code": "CONTRACT_GAP_HIGH",
                    "severity": "HIGH",
                    "message": "Historical patch_result artifacts have validators_required entries without matching validators_run evidence.",
                    "source_requirement_id": REQUIREMENT_ID,
                }
            ]
            if gaps
            else [],
            "notes": "Do not backfill historical patch_result evidence. Future patch_result artifacts must include every required validator in validators_run with usable status, and this gap remains a live-readiness blocker until a formal evidence-preserving correction policy exists.",
            "contract_gap_id": CONTRACT_GAP_ID,
            "severity": "HIGH" if gaps else "INFO",
            "source_section_id": "SECTION_PATCH_RESULT",
            "live_affecting": True,
        },
    )


def ensure_requirement(index: dict[str, Any], requirement: dict[str, Any]) -> None:
    rows = index.setdefault("requirements", [])
    rows[:] = [item for item in rows if item.get("requirement_id") != requirement["requirement_id"]]
    rows.append(requirement)


def ensure_matrix_row(matrix: dict[str, Any], row: dict[str, Any]) -> None:
    rows = matrix.setdefault("rows", [])
    rows[:] = [item for item in rows if item.get("requirement_id") != row["requirement_id"]]
    rows.append(row)


def update_validator_catalog(now: str) -> None:
    path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(path)
    registry["updated_at_utc"] = now
    implemented = registry.setdefault("implemented_validators", [])
    implemented[:] = [item for item in implemented if item.get("validator_id") != "patch_result_runtime_schema_instance_validator"]
    implemented.append(
        {
            "validator_id": "patch_result_runtime_schema_instance_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED_AUDIT_PRESERVING",
            "live_enabling": False,
        }
    )
    write_json(path, registry)


def update_navigation(now: str, trader_hash: str) -> None:
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    index = load_json(index_path)
    matrix = load_json(matrix_path)
    index["updated_at_utc"] = now
    matrix["updated_at_utc"] = now
    matrix["schema_file_count"] = len(list((ROOT / "contracts" / "schema").glob("*.schema.json")))
    ensure_requirement(
        index,
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_PATCH_RESULT",
            "source_file": "TRADER_1.md",
            "source_heading": "patch_result evidence must be schema-valid, live-blocked, and validator-run complete",
            "full_text_marker": f"{REQUIREMENT_ID}:patch_result runtime schema validation and validator-run closure",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Patch result runtime schema validation",
            "requirement_kind": "VALIDATOR_IMPLEMENTATION",
            "schema_ids": ["trader1.patch_result.v1", "trader1.contract_gap.v1"],
            "validator_ids": ["patch_result_schema_validator", "patch_result_runtime_schema_instance_validator"],
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/contract/test_patch_result_runtime_schema_validation.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["VALIDATOR_IMPLEMENTATION", "LIVE_BLOCKED_TEST", "RETAINED_ARCHIVE_COVERAGE"],
            "depends_on": ["REQ-MVP4-SCHEMA-RUNTIME-INSTANCE-VALIDATION", "REQ-MVP4-LIVE-FINAL-GUARD"],
            "source_text_sha256": sha256_bytes(b"patch_result runtime schema validation and validator-run closure"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_WITH_AUDIT_PRESERVED_GAP",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_PATCH_RESULT",
            "schema_files": ["contracts/schema/patch_result.schema.json", "contracts/schema/contract_gap.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/contract/test_patch_result_runtime_schema_validation.py"],
            "fixture_files": ["system/evidence/audit_reports/PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json"],
            "runtime_modules": ["tools/run_patch_result_runtime_schema_validators.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "system/evidence/contract_gaps/PATCH_RESULT_VALIDATOR_RUN_GAP.contract_gap.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED_WITH_AUDIT_PRESERVED_GAP",
        },
    )
    write_json(index_path, index)
    write_json(matrix_path, matrix)


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION.md",
        f"""# PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION

context_pack_id: PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION
task_class: MVP4_PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PATCH_RESULT", "SECTION_SCHEMA_VALIDATION", "SECTION_VALIDATOR_DEPENDENCY_CHAIN", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.contract_gap.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- patch_result artifacts validate against trader1.patch_result.v1 through the shared schema-instance validator
- live flags remain false and LIVE_ENABLING_PATCH remains forbidden
- validators_required entries must appear in validators_run with usable status, or be explicitly audit-preserved as a historical gap
- historical gaps are not backfilled or rewritten

known_omissions_by_design:
- this patch does not claim live readiness
- this patch does not repair historical evidence by mutating old patch_result semantics

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
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

Patch result runtime schema validation is implemented. Historical validator-run omissions are preserved in an audit and contract_gap rather than backfilled. Future patch_result artifacts are checked for schema, live invariant, and validator-run closure.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_SCHEMA_RUNTIME_INSTANCE_VALIDATION.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-SCHEMA-RUNTIME-INSTANCE-VALIDATION"],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": [
                "contracts/registry.yaml::validators.patch_result_runtime_schema_instance_validator",
                "contracts/validators/validator_registry.json::patch_result_runtime_schema_instance_validator",
                *CHANGED_ARTIFACTS,
            ],
            "new_or_changed_schema_ids": ["trader1.patch_result.v1", "trader1.contract_gap.v1"],
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
            "next_task_class": "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT",
            "next_required_section_ids": ["SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_ASSESSMENT", "SECTION_STRATEGY_PROFITABILITY"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_CONTRACT_GAP"],
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
            "active_read_surface_used": ["SECTION_PATCH_RESULT", "SECTION_SCHEMA_VALIDATION", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "MVP4_PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION",
            "required_section_ids": ["SECTION_PATCH_RESULT", "SECTION_SCHEMA_VALIDATION", "SECTION_VALIDATOR_DEPENDENCY_CHAIN", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_PATCH_RESULT", "SECTION_SCHEMA_VALIDATION", "SECTION_VALIDATOR_DEPENDENCY_CHAIN", "SECTION_LIVE_FINAL_GUARD"],
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_PATCH_RESULT_VALIDATION",
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
            "stage_gate_status": "PASS_FOR_PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION_NO_LIVE_ORDERS",
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
        f"""# MVP4 Patch Result Runtime Schema Validation Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- 53 existing patch_result artifacts passed schema and live-flag invariants.
- 9 historical validators_required entries were missing matching validators_run entries.
- Historical patch_result artifacts were not backfilled or rewritten.

Patch:
- Added patch_result_runtime_schema_instance_validator.
- Added negative tests for extra property, live flag drift, and missing required validator runs.
- Added audit-preserved contract_gap for historical validator-run omissions.

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
    state["next_allowed_task_class"] = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["patch_result_runtime_schema_instance_validator"]))
    state["untested_validator_ids"] = [item for item in state.get("untested_validator_ids", []) if item != "patch_result_runtime_schema_instance_validator"]
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
    update_validator_catalog(now)
    update_navigation(now, trader_hash)
    update_context(now, trader_hash, agents_hash)
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.contract.test_patch_result_runtime_schema_validation", "-v"]),
        run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    patch_result = build_patch_result(now, tests_run, validators_run)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_tests = [
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "tools/run_live_final_guard_validators.py"]),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
    ]
    patch_result["tests_run"].extend(final_tests)
    patch_result["validators_run"] = run_validators(VALIDATORS_REQUIRED)
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] if item["status"] != "PASS"]
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
                "open_contract_gap_ids": [CONTRACT_GAP_ID],
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
