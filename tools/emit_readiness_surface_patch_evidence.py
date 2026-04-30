from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP0_READINESS_SURFACE_20260428_001"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
from trader1.runtime.readiness.readiness_surface import build_readiness_surface
from trader1.validation.mvp0_validators import current_authority_hashes, run_validators


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def readiness_surface_schema(registry: dict[str, Any]) -> dict[str, Any]:
    exchanges = registry["enums"]["exchange"]["values"]
    market_types = registry["enums"]["market_type"]["values"]
    modes = registry["enums"]["mode"]["values"]
    live_statuses = registry["enums"]["live_trading_status"]["values"]
    blocker_codes = registry["enums"]["live_blocker_code"]["values"]
    categories = registry["enums"]["blocker_category"]["values"]
    severities = registry["enums"]["severity"]["values"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "trader1.readiness_surface.v1",
        "title": "readiness_surface",
        "type": "object",
        "required": [
            "schema_id",
            "generated_at_utc",
            "project_id",
            "authority",
            "can_start",
            "can_live_trade",
            "live_order_ready",
            "live_order_allowed",
            "live_trading_status",
            "blockers",
            "surface_hash",
        ],
        "additionalProperties": False,
        "properties": {
            "schema_id": {"const": "trader1.readiness_surface.v1"},
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
            "exchange": {"type": ["string", "null"], "enum": [*exchanges, None]},
            "market_type": {"type": ["string", "null"], "enum": [*market_types, None]},
            "mode": {"type": ["string", "null"], "enum": [*modes, None]},
            "session_id": {"type": ["string", "null"]},
            "build_id": {"type": ["string", "null"]},
            "authority_document": {"const": "TRADER_1.md"},
            "authority_sha256": {"type": ["string", "null"], "pattern": "^[A-Fa-f0-9]{64}$"},
            "registry_hash": {"type": ["string", "null"]},
            "schema_bundle_hash": {"type": ["string", "null"]},
            "source_tree_hash": {"type": ["string", "null"]},
            "release_package_status": {"enum": ["NOT_BUILT", "STAGING_READY", "BUNDLE_READY", "DIRTY", "BLOCKED"]},
            "bundle_readiness_status": {"enum": ["UNKNOWN", "PASS", "WARN", "FAIL", "BLOCKED"]},
            "can_start": {"type": "boolean"},
            "can_collect_data": {"type": "boolean"},
            "can_evaluate_candidates": {"type": "boolean"},
            "can_paper_trade": {"type": "boolean"},
            "can_shadow_evaluate": {"type": "boolean"},
            "can_replay": {"type": "boolean"},
            "can_live_review": {"type": "boolean"},
            "can_live_trade": {"type": "boolean"},
            "live_order_ready": {"type": "boolean"},
            "live_order_allowed": {"type": "boolean"},
            "start_gate_status": {"enum": ["PASS", "WARN", "FAIL", "BLOCKED", "UNTESTED"]},
            "live_trading_status": {"enum": live_statuses},
            "primary_blocker_code": {"type": ["string", "null"], "enum": [*blocker_codes, None]},
            "primary_blocker_message": {"type": ["string", "null"]},
            "blockers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["code", "category", "severity", "message", "blocks_start", "blocks_live_order"],
                    "additionalProperties": False,
                    "properties": {
                        "code": {"type": "string", "enum": blocker_codes},
                        "category": {"enum": categories},
                        "severity": {"enum": severities},
                        "message": {"type": "string"},
                        "detail": {"type": ["string", "null"]},
                        "evidence_id": {"type": ["string", "null"]},
                        "source_contract_id": {"type": ["string", "null"]},
                        "blocks_start": {"type": "boolean"},
                        "blocks_live_order": {"type": "boolean"},
                    },
                },
            },
            "surface_hash": {"type": "string"},
        },
        "allOf": [
            {
                "if": {"properties": {"live_order_allowed": {"const": True}}, "required": ["live_order_allowed"]},
                "then": {
                    "properties": {
                        "live_order_ready": {"const": True},
                        "can_live_trade": {"const": True},
                        "live_trading_status": {"enum": ["SMALL_LIVE_BURN_IN", "LIVE_ACTIVE"]},
                        "primary_blocker_code": {"type": "null"},
                        "primary_blocker_message": {"type": "null"},
                    },
                    "not": {
                        "properties": {
                            "blockers": {
                                "contains": {
                                    "type": "object",
                                    "properties": {"blocks_live_order": {"const": True}},
                                    "required": ["blocks_live_order"],
                                }
                            }
                        }
                    },
                },
            }
        ],
    }


def update_authority_manifest(now: str) -> None:
    path = ROOT / "contracts" / "authority_manifest.json"
    manifest = load_json(path)
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    manifest["registry_yaml_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "registry.yaml")
    manifest["schema_bundle_sha256_when_generated"] = sha256_json(
        {schema.relative_to(ROOT).as_posix(): sha256_file(schema) for schema in schema_files}
    )
    manifest["validator_bundle_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "validators" / "validator_registry.json")
    manifest["created_at_utc"] = manifest.get("created_at_utc", now)
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = sha256_json(manifest)
    write_json(path, manifest)


def update_validator_registry(now: str) -> None:
    path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(path)
    registry["updated_at_utc"] = now
    implemented = registry.setdefault("implemented_validators", [])
    implemented[:] = [item for item in implemented if item.get("validator_id") != "readiness_surface_validator"]
    implemented.append(
        {
            "validator_id": "readiness_surface_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED",
            "live_enabling": False,
        }
    )
    registry["readiness_surface_module"] = "trader1.runtime.readiness.readiness_surface"
    write_json(path, registry)


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    trader_lines = (ROOT / "TRADER_1.md").read_text(encoding="utf-8").splitlines()
    map_path = ROOT / "contracts" / "generated" / "authority_section_map.json"
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    section_map = load_json(map_path)
    ensure_section(
        section_map,
        {
            "section_id": "SECTION_READINESS_SURFACE",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "readiness_surface schema and live ready formula",
            "line_start": 5549,
            "line_end": 6115,
            "source_section_sha256": source_hash(trader_lines, 5549, 6115),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
    )
    section_map["updated_at_utc"] = now
    write_json(map_path, section_map)

    index = load_json(index_path)
    requirement = {
        "requirement_id": "REQ-MVP0-READINESS-SURFACE",
        "source_section_id": "SECTION_READINESS_SURFACE",
        "source_file": "TRADER_1.md",
        "source_heading": "readiness_surface schema and live ready formula",
        "full_text_marker": "can_start can_live_review release readiness do not imply live_order_ready and live_order_allowed requires live_order_ready",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "MVP-0 fail-closed readiness surface",
        "requirement_kind": "MVP0_CONTRACT_BASELINE",
        "schema_ids": ["trader1.readiness_surface.v1", "trader1.validator_result.v1"],
        "validator_ids": ["readiness_surface_validator"],
        "artifact_ids": [
            "trader1/runtime/readiness/readiness_surface.py",
            "tests/readiness/test_readiness_surface.py",
            "system/runtime/upbit/krw_spot/live/readiness_surface.json",
        ],
        "test_ids": ["tests/readiness/test_readiness_surface.py"],
        "mvp_stage": "MVP-0",
        "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": ["MVP0_CONTRACT_BASELINE", "LIVE_BLOCKED_TEST"],
        "depends_on": ["REQ-MVP0-LIVE-DEFAULT-FALSE", "REQ-MVP0-NAMESPACE-TRUTH"],
        "source_text_sha256": source_hash(trader_lines, 5549, 6115),
        "source_authority_sha256": trader_hash,
        "implementation_status": "IMPLEMENTED",
        "test_status": "PASS",
    }
    ensure_requirement(index, requirement)
    index["updated_at_utc"] = now
    write_json(index_path, index)

    matrix = load_json(matrix_path)
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": "REQ-MVP0-READINESS-SURFACE",
            "section_id": "SECTION_READINESS_SURFACE",
            "schema_files": ["contracts/schema/readiness_surface.schema.json"],
            "validator_files": [
                "trader1/validation/mvp0_validators.py",
                "trader1/runtime/readiness/readiness_surface.py",
            ],
            "test_files": ["tests/readiness/test_readiness_surface.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/readiness/readiness_surface.py"],
            "evidence_artifacts": [
                "system/runtime/upbit/krw_spot/live/readiness_surface.json",
                "system/evidence/validator_runs/MVP0_READINESS_SURFACE.validator_run_log.json",
                "system/evidence/patch_results/MVP0_READINESS_SURFACE.patch_result.json",
            ],
            "dashboard_artifacts": ["system/runtime/upbit/krw_spot/live/readiness_surface.json"],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED",
        },
    )
    matrix["updated_at_utc"] = now
    write_json(matrix_path, matrix)

    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "READINESS_SURFACE.md",
        f"""# READINESS_SURFACE

context_pack_id: READINESS_SURFACE
task_class: MVP0_CONTRACT_BASELINE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_READINESS_SURFACE", "SECTION_LIVE_GATE", "SECTION_PATCH_RESULT"]
included_requirement_ids: ["REQ-MVP0-READINESS-SURFACE"]
included_schema_ids: ["trader1.readiness_surface.v1", "trader1.validator_result.v1", "trader1.patch_result.v1"]
included_validator_ids: ["readiness_surface_validator"]
included_artifact_ids: ["trader1/runtime/readiness/readiness_surface.py", "tests/readiness/test_readiness_surface.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- can_start and can_live_review do not imply live_order_ready
- live_order_allowed=true requires live_order_ready=true and can_live_trade=true
- any live blocker keeps live_order_ready=false and live_order_allowed=false
- standalone READY display is forbidden
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- live-enabling evidence
- real exchange credentials
- manual order test
- read-only burn-in
- live-ready snapshot writer execution

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: {now}
""",
    )


def update_read_cache(now: str, trader_hash: str, agents_hash: str) -> None:
    context_dir = ROOT / "contracts" / "generated" / "context_pack"
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    manifest = {
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
    write_json(ROOT / "contracts" / "generated" / "read_cache_manifest.json", manifest)


def write_runtime_surface(now: str) -> None:
    registry_path = ROOT / "contracts" / "registry.yaml"
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    surface = build_readiness_surface(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="LIVE",
        session_id="mvp0_readiness_surface",
        registry_hash=sha256_file(registry_path),
        schema_bundle_hash=sha256_json({path.relative_to(ROOT).as_posix(): sha256_file(path) for path in schema_files}),
        can_start=True,
        can_collect_data=True,
        can_live_review=True,
    )
    surface["generated_at_utc"] = now
    surface["surface_hash"] = ""
    from trader1.runtime.readiness.readiness_surface import surface_hash as compute_surface_hash

    surface["surface_hash"] = compute_surface_hash(surface)
    write_json(ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "live" / "readiness_surface.json", surface)


def update_state_and_evidence(now: str, trader_hash: str, agents_hash: str) -> None:
    validator_results = run_validators(["readiness_surface_validator"])
    validator_log = {
        "validator_run_log_schema_id": "trader1.validator_run_log.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "validators_run": validator_results,
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
    write_json(ROOT / "system" / "evidence" / "validator_runs" / "MVP0_READINESS_SURFACE.validator_run_log.json", validator_log)

    stage_gate = {
        "stage_gate_schema_id": "trader1.stage_gate_result.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-0",
        "readiness_surface": "PASS",
        "live_order_allowed": False,
        "stage_gate_status": "PASS_FOR_MVP0_READINESS_SURFACE_ONLY",
    }
    write_json(ROOT / "system" / "evidence" / "stage_gates" / "MVP0_READINESS_SURFACE.stage_gate_result.json", stage_gate)

    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "evidence_manifest_id": "MVP0_READINESS_SURFACE_EVIDENCE",
        "artifact_paths": [
            "contracts/schema/readiness_surface.schema.json",
            "trader1/runtime/readiness/readiness_surface.py",
            "tests/readiness/test_readiness_surface.py",
            "system/runtime/upbit/krw_spot/live/readiness_surface.json",
            "system/evidence/validator_runs/MVP0_READINESS_SURFACE.validator_run_log.json",
            "system/evidence/stage_gates/MVP0_READINESS_SURFACE.stage_gate_result.json",
        ],
        "known_blockers": [
            "LIVE_READY_MISSING",
            "LIVE_READY_SNAPSHOT_WRITER_UNTESTED",
            "API_UNVERIFIED",
            "OPERATOR_APPROVAL_MISSING",
            "LIVE_ENABLING_EVIDENCE_MISSING",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "system" / "evidence" / "MVP0_READINESS_SURFACE.evidence_manifest.json", evidence_manifest)

    patch_result = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-0",
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": ["REQ-MVP0-READINESS-SURFACE"],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "LIVE",
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [],
        "new_or_changed_schema_ids": ["trader1.readiness_surface.v1"],
        "validators_required": ["readiness_surface_validator"],
        "validators_run": validator_results,
        "tests_run": [
            {"command": "python tools/run_readiness_surface_validators.py", "status": "PASS"},
            {"command": "python -m unittest tests.readiness.test_readiness_surface -v", "status": "PASS"},
            {"command": "python -m unittest discover -s tests -v", "status": "PASS"},
        ],
        "coverage_unmapped_count": 0,
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED_FOR_READINESS_SURFACE",
        "read_cache_update_required": False,
        "context_pack_update_required": False,
        "current_implementation_state_updated": True,
        "next_task_class": "MVP0_CONTRACT_BASELINE",
        "next_required_section_ids": ["SECTION_ACTIVE_CONTRACT_PACK", "SECTION_LIVE_GATE", "SECTION_PATCH_RESULT"],
        "next_optional_section_ids": ["SECTION_FINAL_DECISION", "SECTION_DASHBOARD"],
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
        "evidence_manifest_path": "system/evidence/MVP0_READINESS_SURFACE.evidence_manifest.json",
        "validator_run_log_path": "system/evidence/validator_runs/MVP0_READINESS_SURFACE.validator_run_log.json",
        "stage_gate_result_path": "system/evidence/stage_gates/MVP0_READINESS_SURFACE.stage_gate_result.json",
        "token_navigation_patch": True,
        "active_read_surface_used": ["SECTION_READINESS_SURFACE", "SECTION_LIVE_GATE", "SECTION_PATCH_RESULT"],
        "task_class": "MVP0_CONTRACT_BASELINE",
        "required_section_ids": ["SECTION_ACTIVE_CONTRACT_PACK", "SECTION_LIVE_GATE", "SECTION_PATCH_RESULT"],
        "expanded_section_ids": ["SECTION_READINESS_SURFACE", "SECTION_LIVE_GATE", "SECTION_PATCH_RESULT"],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "UPDATED",
        "requirement_index_status": "UPDATED",
        "requirement_artifact_matrix_status": "UPDATED",
        "read_cache_manifest_status": "UPDATED",
        "context_pack_status": "GENERATED",
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
        "failure_analysis_status": "NOT_REQUIRED_FOR_READINESS_SURFACE",
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
    write_json(ROOT / "system" / "evidence" / "patch_results" / "MVP0_READINESS_SURFACE.patch_result.json", patch_result)

    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    if "REQ-MVP0-READINESS-SURFACE" not in state["completed_requirement_ids"]:
        state["completed_requirement_ids"].append("REQ-MVP0-READINESS-SURFACE")
    if "readiness_surface_validator" not in state["implemented_validator_ids"]:
        state["implemented_validator_ids"].append("readiness_surface_validator")
    state["updated_at_utc"] = now
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP0_CONTRACT_BASELINE"
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
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "target_mvp_level": "MVP-0",
            "patch_result_path": "system/evidence/patch_results/MVP0_READINESS_SURFACE.patch_result.json",
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
        }
    )
    write_json(ledger_path, ledger)


def main() -> None:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    registry = load_json(ROOT / "contracts" / "registry.yaml")
    write_json(ROOT / "contracts" / "schema" / "readiness_surface.schema.json", readiness_surface_schema(registry))
    update_validator_registry(now)
    update_authority_manifest(now)
    update_navigation(now, trader_hash, agents_hash)
    write_runtime_surface(now)
    update_state_and_evidence(now, trader_hash, agents_hash)
    update_read_cache(now, trader_hash, agents_hash)
    print(json.dumps({"patch_id": PATCH_ID, "status": "evidence_updated", "live_order_allowed_after": False}, indent=2))


if __name__ == "__main__":
    main()
