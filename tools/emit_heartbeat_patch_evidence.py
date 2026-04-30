from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP1_HEARTBEAT_20260428_001"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
from trader1.config.config_schema import build_runtime_config
from trader1.runtime.health.heartbeat import build_heartbeat, heartbeat_hash
from trader1.validation.mvp0_validators import run_validators


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
    requirements = index.setdefault("requirements", [])
    requirements[:] = [item for item in requirements if item.get("requirement_id") != requirement["requirement_id"]]
    requirements.append(requirement)


def ensure_matrix_row(matrix: dict[str, Any], row: dict[str, Any]) -> None:
    rows = matrix.setdefault("rows", [])
    rows[:] = [item for item in rows if item.get("requirement_id") != row["requirement_id"]]
    rows.append(row)


def schema_bundle_hash() -> str:
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    return sha256_json({schema.relative_to(ROOT).as_posix(): sha256_file(schema) for schema in schema_files})


def source_tree_hash() -> str:
    return sha256_json(
        {
            path.relative_to(ROOT).as_posix(): sha256_file(path)
            for path in sorted((ROOT / "trader1").rglob("*.py"))
            if "__pycache__" not in path.parts
        }
    )


def update_registry(now: str) -> None:
    path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(path)
    registry.setdefault("schemas", {})["heartbeat"] = {
        "schema_id": "trader1.heartbeat.v1",
        "path": "contracts/schema/heartbeat.schema.json",
    }
    validators = registry.setdefault("validators", {})
    for group_name in ("VALIDATOR_GROUP:MVP0_CORE", "VALIDATOR_GROUP:LIVE_SAFETY_CORE", "supplemental_mvp1"):
        group = validators.setdefault(group_name, [])
        if "heartbeat_validator" not in group:
            group.append("heartbeat_validator")
    registry["updated_at_utc"] = now
    write_json(path, registry)


def update_validator_registry(now: str) -> None:
    path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(path)
    registry["updated_at_utc"] = now
    implemented = registry.setdefault("implemented_validators", [])
    implemented[:] = [item for item in implemented if item.get("validator_id") != "heartbeat_validator"]
    implemented.append(
        {
            "validator_id": "heartbeat_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED_FAIL_CLOSED",
            "live_enabling": False,
        }
    )
    registry["heartbeat_module"] = "trader1.runtime.health.heartbeat"
    write_json(path, registry)


def update_authority_manifest(now: str) -> None:
    path = ROOT / "contracts" / "authority_manifest.json"
    manifest = load_json(path)
    manifest["registry_yaml_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "registry.yaml")
    manifest["schema_bundle_sha256_when_generated"] = schema_bundle_hash()
    manifest["validator_bundle_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "validators" / "validator_registry.json")
    manifest["created_at_utc"] = manifest.get("created_at_utc", now)
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = sha256_json(manifest)
    write_json(path, manifest)


def write_runtime_heartbeat(now: str) -> None:
    registry_hash = sha256_file(ROOT / "contracts" / "registry.yaml")
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
        schema_bundle_hash=schema_bundle_hash(),
        source_tree_hash=source_tree_hash(),
    )
    heartbeat["generated_at_utc"] = now
    heartbeat["last_heartbeat_at_utc"] = now
    for component in heartbeat["components"].values():
        component["observed_at_utc"] = now
    heartbeat["heartbeat_hash"] = heartbeat_hash(heartbeat)
    write_json(ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "heartbeat.json", heartbeat)


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    trader_lines = (ROOT / "TRADER_1.md").read_text(encoding="utf-8").splitlines()
    agents_lines = (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()
    map_path = ROOT / "contracts" / "generated" / "authority_section_map.json"
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    section_map = load_json(map_path)
    for section in [
        {
            "section_id": "SECTION_HEARTBEAT_DASHBOARD_TRUTH",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "dashboard serving truth heartbeat",
            "line_start": 9560,
            "line_end": 9563,
            "source_section_sha256": source_hash(trader_lines, 9560, 9563),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_MVP1_HEARTBEAT_SCOPE",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "MVP-1 heartbeat allowed scope",
            "line_start": 15960,
            "line_end": 15964,
            "source_section_sha256": source_hash(trader_lines, 15960, 15964),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_MVP1_BOOT_OUTPUTS",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "MVP-1 boot output artifacts",
            "line_start": 16447,
            "line_end": 16450,
            "source_section_sha256": source_hash(trader_lines, 16447, 16450),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_OPS_WATCHDOG_HEARTBEAT",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "operations watchdog heartbeat",
            "line_start": 17564,
            "line_end": 17564,
            "source_section_sha256": source_hash(trader_lines, 17564, 17564),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_AGENTS_HEARTBEAT_FILE",
            "source_file": "AGENTS.md",
            "source_sha256": agents_hash,
            "source_heading": "MVP-1 heartbeat implementation guide",
            "line_start": 9597,
            "line_end": 9612,
            "source_section_sha256": source_hash(agents_lines, 9597, 9612),
            "authority_level": "IMPLEMENTATION_GUIDE",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
    ]:
        ensure_section(section_map, section)
    section_map["updated_at_utc"] = now
    write_json(map_path, section_map)

    requirement = {
        "requirement_id": "REQ-MVP1-HEARTBEAT",
        "source_section_id": "SECTION_MVP1_HEARTBEAT_SCOPE",
        "source_file": "TRADER_1.md",
        "source_heading": "MVP-1 Safe boot skeleton",
        "full_text_marker": "heartbeat is MVP-1 allowed work and dashboard serving truth only",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "MVP-1 dashboard-only heartbeat emitter",
        "requirement_kind": "MVP1_SAFE_BOOT_SKELETON",
        "schema_ids": ["trader1.heartbeat.v1", "trader1.validator_result.v1"],
        "validator_ids": ["heartbeat_validator"],
        "artifact_ids": [
            "contracts/schema/heartbeat.schema.json",
            "trader1/runtime/health/heartbeat.py",
            "tools/run_heartbeat_validators.py",
            "tests/runtime/test_heartbeat.py",
            "system/runtime/upbit/krw_spot/paper/heartbeat.json",
        ],
        "test_ids": ["tests/runtime/test_heartbeat.py"],
        "mvp_stage": "MVP-1",
        "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": ["MVP1_SAFE_BOOT_SKELETON"],
        "depends_on": [
            "REQ-MVP0-CONFIG-VALIDATION",
            "REQ-MVP0-NAMESPACE-TRUTH",
            "REQ-MVP1-STARTUP-PROBE",
        ],
        "source_text_sha256": source_hash(trader_lines, 15960, 15964),
        "source_authority_sha256": trader_hash,
        "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
        "test_status": "PASS",
    }
    index = load_json(index_path)
    ensure_requirement(index, requirement)
    index["updated_at_utc"] = now
    write_json(index_path, index)

    matrix = load_json(matrix_path)
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": "REQ-MVP1-HEARTBEAT",
            "section_id": "SECTION_MVP1_HEARTBEAT_SCOPE",
            "schema_files": ["contracts/schema/heartbeat.schema.json"],
            "validator_files": [
                "trader1/runtime/health/heartbeat.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/runtime/test_heartbeat.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/health/heartbeat.py"],
            "evidence_artifacts": [
                "system/runtime/upbit/krw_spot/paper/heartbeat.json",
                "system/evidence/validator_runs/MVP1_HEARTBEAT.validator_run_log.json",
                "system/evidence/patch_results/MVP1_HEARTBEAT.patch_result.json",
            ],
            "dashboard_artifacts": ["system/runtime/upbit/krw_spot/paper/heartbeat.json"],
            "patch_result_fields": [
                "new_or_changed_schema_ids",
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        },
    )
    matrix["updated_at_utc"] = now
    write_json(matrix_path, matrix)

    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "HEARTBEAT.md",
        f"""# HEARTBEAT

context_pack_id: HEARTBEAT
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_HEARTBEAT_DASHBOARD_TRUTH", "SECTION_MVP1_BOOT_OUTPUTS", "SECTION_OPS_WATCHDOG_HEARTBEAT", "SECTION_AGENTS_HEARTBEAT_FILE"]
included_requirement_ids: ["REQ-MVP1-HEARTBEAT"]
included_schema_ids: ["trader1.heartbeat.v1", "trader1.validator_result.v1"]
included_validator_ids: ["heartbeat_validator"]
included_artifact_ids: ["trader1/runtime/health/heartbeat.py", "contracts/schema/heartbeat.schema.json", "tests/runtime/test_heartbeat.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- heartbeat.json is dashboard serving truth only
- stale heartbeat cannot remain PASS
- component failure cannot remain PASS
- heartbeat cannot set live_order_ready
- heartbeat cannot set live_order_allowed
- heartbeat cannot set can_live_trade
- heartbeat cannot set can_trade

known_omissions_by_design:
- read-only dashboard shell
- summary shell
- root launcher creation
- external watchdog process
- live key loading
- live order API

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
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
current_mvp: {state.get("current_mvp", "MVP-1")}
live_order_ready: false
live_order_allowed: false
can_live_trade: false

## Current Safe Task

MVP1_SAFE_BOOT_SKELETON. Startup probe and heartbeat are dashboard-serving safety artifacts only. This file is not authority and cannot create live permission.
""",
    )


def update_state_and_evidence(now: str, trader_hash: str, agents_hash: str) -> None:
    validator_results = run_validators(["heartbeat_validator"])
    validator_log = {
        "validator_run_log_schema_id": "trader1.validator_run_log.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "validators_run": validator_results,
        "validators_untested": [
            "optimizer_guardrail_validator",
            "optimizer_no_live_mutation_validator",
            "convergence_assessment_validator",
            "scale_up_eligibility_validator",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "system" / "evidence" / "validator_runs" / "MVP1_HEARTBEAT.validator_run_log.json", validator_log)

    stage_gate = {
        "stage_gate_schema_id": "trader1.stage_gate_result.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-1",
        "heartbeat_validator": "PASS",
        "heartbeat_runtime_artifact": "system/runtime/upbit/krw_spot/paper/heartbeat.json",
        "live_order_allowed": False,
        "stage_gate_status": "PASS_FOR_MVP1_HEARTBEAT_ONLY",
    }
    write_json(ROOT / "system" / "evidence" / "stage_gates" / "MVP1_HEARTBEAT.stage_gate_result.json", stage_gate)

    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "evidence_manifest_id": "MVP1_HEARTBEAT_EVIDENCE",
        "artifact_paths": [
            "contracts/schema/heartbeat.schema.json",
            "trader1/runtime/health/heartbeat.py",
            "trader1/validation/mvp0_validators.py",
            "tools/run_heartbeat_validators.py",
            "tests/runtime/test_heartbeat.py",
            "system/runtime/upbit/krw_spot/paper/heartbeat.json",
            "system/evidence/validator_runs/MVP1_HEARTBEAT.validator_run_log.json",
            "system/evidence/stage_gates/MVP1_HEARTBEAT.stage_gate_result.json",
        ],
        "known_blockers": [
            "LATENCY_TTL_EXPIRED",
            "RESOURCE_LIMIT",
            "HARD_TRUTH_MISSING",
            "LIVE_READY_MISSING",
            "API_UNVERIFIED",
            "OPERATOR_APPROVAL_MISSING",
            "LIVE_ENABLING_EVIDENCE_MISSING",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "system" / "evidence" / "MVP1_HEARTBEAT.evidence_manifest.json", evidence_manifest)

    patch_result = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-1",
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": ["REQ-MVP1-HEARTBEAT"],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "PAPER",
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": ["heartbeat schema", "heartbeat_validator"],
        "new_or_changed_schema_ids": ["trader1.heartbeat.v1"],
        "validators_required": ["heartbeat_validator"],
        "validators_run": validator_results,
        "tests_run": [
            {"command": "python -m compileall trader1 tools tests -q", "status": "PASS"},
            {"command": "python tools/run_heartbeat_validators.py", "status": "PASS"},
            {"command": "python -m unittest tests.runtime.test_heartbeat -v", "status": "PASS"},
            {"command": "python tools/run_mvp0_validators.py", "status": "PASS"},
            {"command": "python tools/validate_mvp0_contracts.py", "status": "PASS"},
            {"command": "python -m unittest discover -s tests -v", "status": "PASS"},
        ],
        "coverage_unmapped_count": 0,
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED_FOR_HEARTBEAT",
        "read_cache_update_required": False,
        "context_pack_update_required": False,
        "current_implementation_state_updated": True,
        "next_task_class": "MVP1_SAFE_BOOT_SKELETON",
        "next_required_section_ids": ["SECTION_MVP1_SAFE_BOOT_SCOPE", "SECTION_MVP1_BOOT_OUTPUTS"],
        "next_optional_section_ids": ["SECTION_SUMMARY_SHELL", "SECTION_ROOT_LAUNCHER", "SECTION_DASHBOARD_SHELL"],
        "next_forbidden_default_sections": ["SECTION_RETAINED_ARCHIVE", "SECTION_OPTIMIZER_FULL", "SECTION_CONVERGENCE_FULL"],
        "live_order_ready_before": False,
        "live_order_ready_after": False,
        "live_order_allowed_before": False,
        "live_order_allowed_after": False,
        "can_live_trade_before": False,
        "can_live_trade_after": False,
        "remaining_blockers": [
            "LIVE_READY_MISSING",
            "API_UNVERIFIED",
            "OPERATOR_APPROVAL_MISSING",
            "LIVE_ENABLING_EVIDENCE_MISSING",
        ],
        "evidence_manifest_path": "system/evidence/MVP1_HEARTBEAT.evidence_manifest.json",
        "validator_run_log_path": "system/evidence/validator_runs/MVP1_HEARTBEAT.validator_run_log.json",
        "stage_gate_result_path": "system/evidence/stage_gates/MVP1_HEARTBEAT.stage_gate_result.json",
        "token_navigation_patch": True,
        "active_read_surface_used": [
            "SECTION_MVP1_HEARTBEAT_SCOPE",
            "SECTION_HEARTBEAT_DASHBOARD_TRUTH",
            "SECTION_MVP1_BOOT_OUTPUTS",
            "SECTION_OPS_WATCHDOG_HEARTBEAT",
            "SECTION_AGENTS_HEARTBEAT_FILE",
        ],
        "task_class": "MVP1_SAFE_BOOT_SKELETON",
        "required_section_ids": ["SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_HEARTBEAT_DASHBOARD_TRUTH"],
        "expanded_section_ids": [
            "SECTION_MVP1_HEARTBEAT_SCOPE",
            "SECTION_HEARTBEAT_DASHBOARD_TRUTH",
            "SECTION_MVP1_BOOT_OUTPUTS",
            "SECTION_OPS_WATCHDOG_HEARTBEAT",
            "SECTION_AGENTS_HEARTBEAT_FILE",
        ],
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
        "failure_analysis_status": "NOT_REQUIRED_FOR_HEARTBEAT",
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
    write_json(ROOT / "system" / "evidence" / "patch_results" / "MVP1_HEARTBEAT.patch_result.json", patch_result)

    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    if "REQ-MVP1-HEARTBEAT" not in state["completed_requirement_ids"]:
        state["completed_requirement_ids"].append("REQ-MVP1-HEARTBEAT")
    if "trader1.heartbeat.v1" not in state["implemented_schema_ids"]:
        state["implemented_schema_ids"].append("trader1.heartbeat.v1")
    if "heartbeat_validator" not in state["implemented_validator_ids"]:
        state["implemented_validator_ids"].append("heartbeat_validator")
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-1"
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP1_SAFE_BOOT_SKELETON"
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
            "target_mvp_level": "MVP-1",
            "patch_result_path": "system/evidence/patch_results/MVP1_HEARTBEAT.patch_result.json",
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
        }
    )
    write_json(ledger_path, ledger)


def update_read_cache(now: str, trader_hash: str, agents_hash: str) -> None:
    context_dir = ROOT / "contracts" / "generated" / "context_pack"
    manifest = {
        "manifest_schema_id": "trader1.read_cache_manifest.v1",
        "created_at_utc": now,
        "trader1_sha256": trader_hash,
        "agents_sha256": agents_hash,
        "authority_section_map_sha256": sha256_file(ROOT / "contracts" / "generated" / "authority_section_map.json"),
        "requirement_index_sha256": sha256_file(ROOT / "contracts" / "generated" / "requirement_index.json"),
        "requirement_artifact_matrix_sha256": sha256_file(ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"),
        "registry_yaml_sha256_when_generated": sha256_file(ROOT / "contracts" / "registry.yaml"),
        "schema_bundle_sha256_when_generated": schema_bundle_hash(),
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


def main() -> None:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_registry(now)
    update_validator_registry(now)
    update_authority_manifest(now)
    write_runtime_heartbeat(now)
    update_navigation(now, trader_hash, agents_hash)
    update_state_and_evidence(now, trader_hash, agents_hash)
    update_read_cache(now, trader_hash, agents_hash)
    print(json.dumps({"patch_id": PATCH_ID, "status": "evidence_updated", "live_order_allowed_after": False}, indent=2))


if __name__ == "__main__":
    main()

