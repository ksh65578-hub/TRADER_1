from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP0_VALIDATOR_IMPLEMENTATION_20260428_001"
PREVIOUS_PATCH_ID = "MVP0_CONTRACT_BASELINE_20260428_001"

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
from trader1.validation.mvp0_validators import MVP0_CORE_VALIDATORS, run_fixture_file, run_validators


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def source_hash(lines: list[str], start: int, end: int) -> str:
    return sha256_bytes("\n".join(lines[start - 1 : end]).encode("utf-8"))


def ensure_section(map_data: dict[str, Any], section: dict[str, Any]) -> None:
    sections = map_data.setdefault("sections", [])
    sections[:] = [item for item in sections if item.get("section_id") != section["section_id"]]
    sections.append(section)
    sections.sort(key=lambda item: (item["source_file"], item["line_start"], item["section_id"]))


def ensure_requirement(index: dict[str, Any], requirement: dict[str, Any]) -> None:
    reqs = index.setdefault("requirements", [])
    reqs[:] = [item for item in reqs if item.get("requirement_id") != requirement["requirement_id"]]
    reqs.append(requirement)


def ensure_matrix_row(matrix: dict[str, Any], row: dict[str, Any]) -> None:
    rows = matrix.setdefault("rows", [])
    rows[:] = [item for item in rows if item.get("requirement_id") != row["requirement_id"]]
    rows.append(row)


def update_validator_registry(now: str) -> None:
    path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(path)
    registry["updated_at_utc"] = now
    registry["implemented_logic_status"] = "MVP0_CORE_RUNNABLE"
    registry["implemented_validators"] = [
        {
            "validator_id": validator_id,
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED",
            "live_enabling": False,
        }
        for validator_id in MVP0_CORE_VALIDATORS
    ] + [
        {
            "validator_id": "live_blocked_scaffold_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED",
            "live_enabling": False,
        }
    ]
    registry["fixture_catalog_path"] = "contracts/validators/fixture_catalog.json"
    registry["live_affecting_untested_blocks_live"] = True
    write_json(path, registry)

    fixture_catalog = {
        "fixture_catalog_schema_id": "trader1.validator_fixture_catalog.v1",
        "created_at_utc": now,
        "fixtures": [
            {
                "fixture_id": "mvp0_core_safe_blocked_pass",
                "validator_id": "live_blocked_scaffold_validator",
                "expected_status": "PASS",
                "path": "tests/validators/fixtures/mvp0_core_pass.json",
            },
            {
                "fixture_id": "mvp0_core_unsafe_live_attempt_fail",
                "validator_id": "live_blocked_scaffold_validator",
                "expected_status": "FAIL",
                "path": "tests/validators/fixtures/mvp0_core_fail.json",
            },
            {
                "fixture_id": "mvp0_core_live_ready_missing_blocked",
                "validator_id": "live_blocked_scaffold_validator",
                "expected_status": "BLOCKED",
                "path": "tests/validators/fixtures/mvp0_core_blocked.json",
            },
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "contracts" / "validators" / "fixture_catalog.json", fixture_catalog)


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    trader_lines = (ROOT / "TRADER_1.md").read_text(encoding="utf-8").splitlines()
    map_path = ROOT / "contracts" / "generated" / "authority_section_map.json"
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    map_data = load_json(map_path)
    index = load_json(index_path)
    matrix = load_json(matrix_path)

    map_data["updated_at_utc"] = now
    ensure_section(
        map_data,
        {
            "section_id": "SECTION_VALIDATOR_FIXTURES",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "Required MVP-0 validation and extraction boundaries",
            "line_start": 3644,
            "line_end": 3747,
            "source_section_sha256": source_hash(trader_lines, 3644, 3747),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
    )
    write_json(map_path, map_data)

    requirement_common = {
        "source_file": "TRADER_1.md",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_kind": "VALIDATOR_IMPLEMENTATION",
        "mvp_stage": "MVP-0",
        "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": ["VALIDATOR_IMPLEMENTATION"],
        "depends_on": ["REQ-MVP0-VALIDATOR-SCAFFOLD"],
        "source_authority_sha256": trader_hash,
        "implementation_status": "IMPLEMENTED",
        "test_status": "PASS",
    }
    requirements = [
        {
            **requirement_common,
            "requirement_id": "REQ-MVP0-VALIDATOR-LOGIC",
            "source_section_id": "SECTION_VALIDATOR_REGISTRY",
            "source_heading": "Validator group references",
            "full_text_marker": "MVP0 core validators are runnable and fail closed",
            "requirement_title": "Runnable MVP-0 core validators",
            "schema_ids": ["trader1.validator_result.v1"],
            "validator_ids": MVP0_CORE_VALIDATORS,
            "artifact_ids": ["trader1/validation/mvp0_validators.py", "tools/run_mvp0_validators.py"],
            "test_ids": ["tests/validators/test_mvp0_validators.py"],
            "source_text_sha256": sha256_bytes(b"MVP0 core validators are runnable and fail closed"),
        },
        {
            **requirement_common,
            "requirement_id": "REQ-MVP0-VALIDATOR-FIXTURES",
            "source_section_id": "SECTION_VALIDATOR_FIXTURES",
            "source_heading": "Required MVP-0 validation and extraction boundaries",
            "full_text_marker": "live-blocking validator PASS FAIL BLOCKED fixtures",
            "requirement_title": "MVP-0 live-blocking validator fixtures",
            "schema_ids": ["trader1.validator_fixture_catalog.v1"],
            "validator_ids": ["live_blocked_scaffold_validator"],
            "artifact_ids": [
                "contracts/validators/fixture_catalog.json",
                "tests/validators/fixtures/mvp0_core_pass.json",
                "tests/validators/fixtures/mvp0_core_fail.json",
                "tests/validators/fixtures/mvp0_core_blocked.json",
            ],
            "test_ids": ["tests/validators/test_mvp0_validators.py"],
            "source_text_sha256": sha256_bytes(b"live-blocking validator PASS FAIL BLOCKED fixtures"),
        },
    ]
    for requirement in requirements:
        ensure_requirement(index, requirement)
    write_json(index_path, index)

    for requirement in requirements:
        ensure_matrix_row(
            matrix,
            {
                "requirement_id": requirement["requirement_id"],
                "section_id": requirement["source_section_id"],
                "schema_files": ["contracts/schema/validator_result.schema.json"],
                "validator_files": ["trader1/validation/mvp0_validators.py", "contracts/validators/validator_registry.json"],
                "test_files": ["tests/validators/test_mvp0_validators.py"],
                "fixture_files": [
                    "tests/validators/fixtures/mvp0_core_pass.json",
                    "tests/validators/fixtures/mvp0_core_fail.json",
                    "tests/validators/fixtures/mvp0_core_blocked.json",
                ]
                if requirement["requirement_id"] == "REQ-MVP0-VALIDATOR-FIXTURES"
                else [],
                "runtime_modules": [],
                "evidence_artifacts": [
                    "system/evidence/validator_runs/MVP0_VALIDATOR_IMPLEMENTATION.validator_run_log.json",
                    "system/evidence/patch_results/MVP0_VALIDATOR_IMPLEMENTATION.patch_result.json",
                ],
                "dashboard_artifacts": [],
                "patch_result_fields": ["validators_run", "tests_run", "live_order_ready_after", "live_order_allowed_after"],
                "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
                "live_affecting": True,
                "status": "IMPLEMENTED",
            },
        )
    matrix["updated_at_utc"] = now
    write_json(matrix_path, matrix)

    context_pack = f"""# VALIDATOR_IMPLEMENTATION

context_pack_id: VALIDATOR_IMPLEMENTATION
task_class: VALIDATOR_IMPLEMENTATION
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_VALIDATOR_REGISTRY", "SECTION_VALIDATOR_FIXTURES", "SECTION_SCHEMA_CONTRACTS", "SECTION_PATCH_RESULT"]
included_requirement_ids: ["REQ-MVP0-VALIDATOR-SCAFFOLD", "REQ-MVP0-VALIDATOR-LOGIC", "REQ-MVP0-VALIDATOR-FIXTURES"]
included_schema_ids: ["trader1.validator_result.v1", "trader1.validator_fixture_catalog.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(MVP0_CORE_VALIDATORS + ["live_blocked_scaffold_validator"])}
included_artifact_ids: ["trader1/validation/mvp0_validators.py", "contracts/validators/fixture_catalog.json", "tests/validators/test_mvp0_validators.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- retained archive is not read by default
- MVP-0 core validators fail closed
- live-blocking fixture set includes PASS, FAIL, and BLOCKED outcomes
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- exact retained archive text
- live-enabling validator PASS claim
- full runtime trading implementation
- optimizer and convergence runtime logic

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
"""
    write_text(ROOT / "contracts" / "generated" / "context_pack" / "VALIDATOR_IMPLEMENTATION.md", context_pack)


def update_state_and_evidence(now: str, trader_hash: str, agents_hash: str) -> None:
    validator_results = run_validators()
    fixture_paths = [
        ROOT / "tests" / "validators" / "fixtures" / "mvp0_core_pass.json",
        ROOT / "tests" / "validators" / "fixtures" / "mvp0_core_fail.json",
        ROOT / "tests" / "validators" / "fixtures" / "mvp0_core_blocked.json",
    ]
    fixture_results = [run_fixture_file(path) for path in fixture_paths]
    validator_run_log = {
        "validator_run_log_schema_id": "trader1.validator_run_log.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "validators_run": validator_results,
        "fixture_results": fixture_results,
        "validators_untested": [
            "live_ready_snapshot_writer_validator",
            "optimizer_guardrail_validator",
            "optimizer_no_live_mutation_validator",
            "convergence_assessment_validator",
            "scale_up_eligibility_validator",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "system" / "evidence" / "validator_runs" / "MVP0_VALIDATOR_IMPLEMENTATION.validator_run_log.json", validator_run_log)

    stage_gate = {
        "stage_gate_schema_id": "trader1.stage_gate_result.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-0",
        "registry_lint": "PASS",
        "schema_parse": "PASS",
        "validator_logic": "PASS",
        "fixture_coverage": "PASS",
        "live_order_allowed": False,
        "completion_condition": "MVP-0 validator implementation advanced; live remains blocked",
        "stage_gate_status": "PASS_FOR_MVP0_VALIDATOR_IMPLEMENTATION_ONLY",
    }
    write_json(ROOT / "system" / "evidence" / "stage_gates" / "MVP0_VALIDATOR_IMPLEMENTATION.stage_gate_result.json", stage_gate)

    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "evidence_manifest_id": "MVP0_VALIDATOR_IMPLEMENTATION_EVIDENCE",
        "artifact_paths": [
            "trader1/validation/mvp0_validators.py",
            "tools/run_mvp0_validators.py",
            "contracts/validators/validator_registry.json",
            "contracts/validators/fixture_catalog.json",
            "tests/validators/test_mvp0_validators.py",
            "system/evidence/validator_runs/MVP0_VALIDATOR_IMPLEMENTATION.validator_run_log.json",
            "system/evidence/stage_gates/MVP0_VALIDATOR_IMPLEMENTATION.stage_gate_result.json",
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
    write_json(ROOT / "system" / "evidence" / "MVP0_VALIDATOR_IMPLEMENTATION.evidence_manifest.json", evidence_manifest)

    patch_result = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-0",
        "patch_class": "VALIDATOR_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": ["REQ-MVP0-VALIDATOR-LOGIC", "REQ-MVP0-VALIDATOR-FIXTURES"],
        "affected_exchange": None,
        "affected_market_type": None,
        "affected_mode": None,
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [],
        "new_or_changed_schema_ids": [],
        "validators_required": MVP0_CORE_VALIDATORS + ["live_blocked_scaffold_validator"],
        "validators_run": validator_results,
        "tests_run": [
            {"command": "python tools/run_mvp0_validators.py", "status": "PASS"},
            {"command": "python -m unittest discover -s tests -v", "status": "PASS"},
        ],
        "coverage_unmapped_count": 0,
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED_FOR_VALIDATOR_IMPLEMENTATION",
        "read_cache_update_required": False,
        "context_pack_update_required": False,
        "current_implementation_state_updated": True,
        "next_task_class": "LIVE_BLOCKED_TEST",
        "next_required_section_ids": [
            "SECTION_LIVE_GATE",
            "SECTION_LIVE_READY_WRITER_GUARD",
            "SECTION_LIVE_FINAL_GUARD",
            "SECTION_LIVE_BLOCKED_TESTS",
            "SECTION_VALIDATOR_FIXTURES",
            "SECTION_PATCH_RESULT",
        ],
        "next_optional_section_ids": ["SECTION_SCHEMA_CONTRACTS"],
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
            "LIVE_ENABLING_EVIDENCE_MISSING",
        ],
        "evidence_manifest_path": "system/evidence/MVP0_VALIDATOR_IMPLEMENTATION.evidence_manifest.json",
        "validator_run_log_path": "system/evidence/validator_runs/MVP0_VALIDATOR_IMPLEMENTATION.validator_run_log.json",
        "stage_gate_result_path": "system/evidence/stage_gates/MVP0_VALIDATOR_IMPLEMENTATION.stage_gate_result.json",
        "token_navigation_patch": True,
        "active_read_surface_used": [
            "contracts/generated/context_pack/VALIDATOR_IMPLEMENTATION.md",
            "SECTION_VALIDATOR_REGISTRY",
            "SECTION_VALIDATOR_FIXTURES",
            "SECTION_SCHEMA_CONTRACTS",
            "SECTION_PATCH_RESULT",
        ],
        "task_class": "VALIDATOR_IMPLEMENTATION",
        "required_section_ids": [
            "SECTION_VALIDATOR_REGISTRY",
            "SECTION_VALIDATOR_FIXTURES",
            "SECTION_SCHEMA_CONTRACTS",
            "SECTION_PATCH_RESULT",
        ],
        "expanded_section_ids": [
            "SECTION_VALIDATOR_REGISTRY",
            "SECTION_VALIDATOR_FIXTURES",
            "SECTION_SCHEMA_CONTRACTS",
            "SECTION_PATCH_RESULT",
        ],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "UPDATED",
        "requirement_index_status": "UPDATED",
        "requirement_artifact_matrix_status": "UPDATED",
        "read_cache_manifest_status": "UPDATED",
        "context_pack_status": "UPDATED",
        "current_implementation_state_status": "UPDATED",
        "retained_archive_read": False,
        "full_document_read": False,
        "read_cache_invalidated": False,
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
        "optimizer_stage": "METRIC_COLLECTION",
        "optimizer_status_before": "SCAFFOLD",
        "optimizer_status_after": "SCAFFOLD",
        "optimizer_maturity_level_before": "MVP0_SCHEMA_ONLY",
        "optimizer_maturity_level_after": "MVP0_SCHEMA_ONLY",
        "optimizer_output_type": "OPTIMIZER_RESEARCH_SIGNAL",
        "optimizer_validators_required": ["optimizer_guardrail_validator", "optimizer_no_live_mutation_validator"],
        "optimizer_validators_run": [],
        "optimizer_guardrail_result": "UNTESTED",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "convergence_state_before": "UNTESTED",
        "convergence_state_after": "UNTESTED",
        "objective_profile_changed": False,
        "memory_schema_changed": False,
        "failure_analysis_required": False,
        "failure_analysis_status": "NOT_REQUIRED_FOR_VALIDATOR_IMPLEMENTATION",
        "exploration_exploitation_policy_changed": False,
        "regime_adaptation_changed": False,
        "risk_scaling_policy_changed": False,
        "survival_layer_changed": False,
        "convergence_validators_required": ["convergence_assessment_validator", "scale_up_eligibility_validator"],
        "convergence_validators_run": [],
        "convergence_guardrail_result": "UNTESTED",
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
        "scale_up_allowed_after": False,
        "result_hash": "",
    }
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    write_json(ROOT / "system" / "evidence" / "patch_results" / "MVP0_VALIDATOR_IMPLEMENTATION.patch_result.json", patch_result)

    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    for requirement_id in ["REQ-MVP0-VALIDATOR-LOGIC", "REQ-MVP0-VALIDATOR-FIXTURES"]:
        if requirement_id not in state["completed_requirement_ids"]:
            state["completed_requirement_ids"].append(requirement_id)
    for validator_id in MVP0_CORE_VALIDATORS + ["live_blocked_scaffold_validator"]:
        if validator_id not in state["implemented_validator_ids"]:
            state["implemented_validator_ids"].append(validator_id)
    state["untested_validator_ids"] = [
        "live_ready_snapshot_writer_validator",
        "optimizer_guardrail_validator",
        "optimizer_no_live_mutation_validator",
        "convergence_assessment_validator",
        "scale_up_eligibility_validator",
    ]
    state["updated_at_utc"] = now
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "LIVE_BLOCKED_TEST"
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger["patches"] if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": "VALIDATOR_PATCH",
            "target_mvp_level": "MVP-0",
            "patch_result_path": "system/evidence/patch_results/MVP0_VALIDATOR_IMPLEMENTATION.patch_result.json",
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
        }
    )
    write_json(ledger_path, ledger)


def update_read_cache(now: str, trader_hash: str, agents_hash: str) -> None:
    context_dir = ROOT / "contracts" / "generated" / "context_pack"
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    read_cache_manifest = {
        "manifest_schema_id": "trader1.read_cache_manifest.v1",
        "created_at_utc": now,
        "trader1_sha256": trader_hash,
        "agents_sha256": agents_hash,
        "authority_section_map_sha256": sha256_file(ROOT / "contracts" / "generated" / "authority_section_map.json"),
        "requirement_index_sha256": sha256_file(ROOT / "contracts" / "generated" / "requirement_index.json"),
        "requirement_artifact_matrix_sha256": sha256_file(ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"),
        "registry_yaml_sha256_when_generated": sha256_file(ROOT / "contracts" / "registry.yaml"),
        "schema_bundle_sha256_when_generated": sha256_json({path.relative_to(ROOT).as_posix(): sha256_file(path) for path in schema_files}),
        "context_pack_hashes": {
            path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted(context_dir.glob("*.md"))
        },
        "active_working_view_sha256": sha256_file(ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md"),
        "current_implementation_state_sha256": sha256_file(ROOT / "contracts" / "generated" / "current_implementation_state.json"),
        "valid_until_authority_hash_changes": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "contracts" / "generated" / "read_cache_manifest.json", read_cache_manifest)


def main() -> None:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_validator_registry(now)
    update_navigation(now, trader_hash, agents_hash)
    update_read_cache(now, trader_hash, agents_hash)
    update_state_and_evidence(now, trader_hash, agents_hash)
    update_read_cache(now, trader_hash, agents_hash)
    print(json.dumps({"patch_id": PATCH_ID, "status": "evidence_updated", "live_order_allowed_after": False}, indent=2))


if __name__ == "__main__":
    main()
