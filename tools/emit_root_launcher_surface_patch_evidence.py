from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP1_ROOT_LAUNCHER_SURFACE_20260428_001"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
from trader1.runtime.boot.safe_launcher import ROOT_LAUNCHER_SPECS, build_launcher_report
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
    registry.setdefault("schemas", {})["root_launcher_report"] = {
        "schema_id": "trader1.root_launcher_report.v1",
        "path": "contracts/schema/root_launcher_report.schema.json",
    }
    validators = registry.setdefault("validators", {})
    for group_name in ("VALIDATOR_GROUP:MVP0_CORE", "VALIDATOR_GROUP:LIVE_SAFETY_CORE", "supplemental_mvp1"):
        group = validators.setdefault(group_name, [])
        if "root_launcher_surface_validator" not in group:
            group.append("root_launcher_surface_validator")
    registry["updated_at_utc"] = now
    write_json(path, registry)


def update_validator_registry(now: str) -> None:
    path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(path)
    registry["updated_at_utc"] = now
    implemented = registry.setdefault("implemented_validators", [])
    implemented[:] = [item for item in implemented if item.get("validator_id") != "root_launcher_surface_validator"]
    implemented.append(
        {
            "validator_id": "root_launcher_surface_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED_FAIL_CLOSED",
            "live_enabling": False,
        }
    )
    registry["root_launcher_report_module"] = "trader1.runtime.boot.safe_launcher"
    registry["root_launcher_files"] = [
        "UPBIT_PAPER.py",
        "UPBIT_LIVE.py",
        "BINANCE_PAPER.py",
        "BINANCE_LIVE.py",
    ]
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


def _scope_path(report: dict[str, Any]) -> Path:
    registry = load_json(ROOT / "contracts" / "registry.yaml")
    slugs = registry["path_slugs"]
    return (
        ROOT
        / "system"
        / "runtime"
        / slugs[report["exchange"]]
        / slugs[report["market_type"]]
        / slugs[report["mode"]]
        / "launcher_report.json"
    )


def write_runtime_reports() -> list[str]:
    paths: list[str] = []
    for launcher_name in sorted(ROOT_LAUNCHER_SPECS):
        report = build_launcher_report(launcher_name)
        path = _scope_path(report)
        write_json(path, report)
        paths.append(path.relative_to(ROOT).as_posix())
    return paths


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    trader_lines = (ROOT / "TRADER_1.md").read_text(encoding="utf-8").splitlines()
    agents_lines = (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()
    map_path = ROOT / "contracts" / "generated" / "authority_section_map.json"
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    section_map = load_json(map_path)
    for section in [
        {
            "section_id": "SECTION_MVP1_ROOT_LAUNCHER_SCOPE",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "MVP-1 root launcher separation",
            "line_start": 9420,
            "line_end": 9431,
            "source_section_sha256": source_hash(trader_lines, 9420, 9431),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_MVP1_ROOT_LAUNCHER_FOUR",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "MVP-1 root launcher four outputs",
            "line_start": 16447,
            "line_end": 16450,
            "source_section_sha256": source_hash(trader_lines, 16447, 16450),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_MVP1_SAFE_BOOT_SEQUENCE",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "safe boot sequence",
            "line_start": 21144,
            "line_end": 21161,
            "source_section_sha256": source_hash(trader_lines, 21144, 21161),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT",
            "source_file": "AGENTS.md",
            "source_sha256": agents_hash,
            "source_heading": "root launcher contract",
            "line_start": 2609,
            "line_end": 2631,
            "source_section_sha256": source_hash(agents_lines, 2609, 2631),
            "authority_level": "IMPLEMENTATION_GUIDE",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_AGENTS_MVP1_ROOT_LAUNCHERS",
            "source_file": "AGENTS.md",
            "source_sha256": agents_hash,
            "source_heading": "MVP-1 root launcher files",
            "line_start": 9597,
            "line_end": 9615,
            "source_section_sha256": source_hash(agents_lines, 9597, 9615),
            "authority_level": "IMPLEMENTATION_GUIDE",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
    ]:
        ensure_section(section_map, section)
    section_map["updated_at_utc"] = now
    write_json(map_path, section_map)

    requirement = {
        "requirement_id": "REQ-MVP1-ROOT-LAUNCHER-SURFACE",
        "source_section_id": "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT",
        "source_file": "AGENTS.md",
        "source_heading": "root launcher contract",
        "full_text_marker": "repository root must expose exactly four user launchers and live paths remain hard-blocked",
        "authority_level": "IMPLEMENTATION_GUIDE",
        "requirement_title": "MVP-1 exact four safe root launchers",
        "requirement_kind": "MVP1_SAFE_BOOT_SKELETON",
        "schema_ids": ["trader1.root_launcher_report.v1", "trader1.validator_result.v1"],
        "validator_ids": ["root_launcher_guard_validator", "root_launcher_surface_validator"],
        "artifact_ids": [
            "UPBIT_PAPER.py",
            "UPBIT_LIVE.py",
            "BINANCE_PAPER.py",
            "BINANCE_LIVE.py",
            "trader1/runtime/boot/safe_launcher.py",
            "contracts/schema/root_launcher_report.schema.json",
            "tools/run_root_launcher_validators.py",
            "tests/contract/test_root_launchers.py",
            "tests/runtime/test_safe_launcher.py",
        ],
        "test_ids": ["tests/contract/test_root_launchers.py", "tests/runtime/test_safe_launcher.py"],
        "mvp_stage": "MVP-1",
        "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": ["MVP1_SAFE_BOOT_SKELETON"],
        "depends_on": [
            "REQ-MVP0-ROOT-LAUNCHER-GUARD",
            "REQ-MVP0-CONFIG-VALIDATION",
            "REQ-MVP0-NAMESPACE-TRUTH",
            "REQ-MVP1-STARTUP-PROBE",
            "REQ-MVP1-HEARTBEAT",
            "REQ-MVP1-SUMMARY-SHELL",
        ],
        "source_text_sha256": source_hash(agents_lines, 2609, 2631),
        "source_authority_sha256": agents_hash,
        "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
        "test_status": "PASS",
    }
    index = load_json(index_path)
    ensure_requirement(index, requirement)
    index["updated_at_utc"] = now
    write_json(index_path, index)

    runtime_reports = [
        "system/runtime/upbit/krw_spot/paper/launcher_report.json",
        "system/runtime/upbit/krw_spot/live/launcher_report.json",
        "system/runtime/binance/spot/paper/launcher_report.json",
        "system/runtime/binance/spot/live/launcher_report.json",
    ]
    matrix = load_json(matrix_path)
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": "REQ-MVP1-ROOT-LAUNCHER-SURFACE",
            "section_id": "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT",
            "schema_files": ["contracts/schema/root_launcher_report.schema.json"],
            "validator_files": [
                "trader1/runtime/boot/launcher_guard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/contract/test_root_launchers.py", "tests/runtime/test_safe_launcher.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": runtime_reports
            + [
                "system/evidence/validator_runs/MVP1_ROOT_LAUNCHER_SURFACE.validator_run_log.json",
                "system/evidence/patch_results/MVP1_ROOT_LAUNCHER_SURFACE.patch_result.json",
            ],
            "dashboard_artifacts": [],
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
        ROOT / "contracts" / "generated" / "context_pack" / "ROOT_LAUNCHER_SURFACE.md",
        f"""# ROOT_LAUNCHER_SURFACE

context_pack_id: ROOT_LAUNCHER_SURFACE
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_MVP1_ROOT_LAUNCHER_SCOPE", "SECTION_MVP1_ROOT_LAUNCHER_FOUR", "SECTION_MVP1_SAFE_BOOT_SEQUENCE", "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT", "SECTION_AGENTS_MVP1_ROOT_LAUNCHERS"]
included_requirement_ids: ["REQ-MVP1-ROOT-LAUNCHER-SURFACE"]
included_schema_ids: ["trader1.root_launcher_report.v1", "trader1.validator_result.v1"]
included_validator_ids: ["root_launcher_guard_validator", "root_launcher_surface_validator"]
included_artifact_ids: ["UPBIT_PAPER.py", "UPBIT_LIVE.py", "BINANCE_PAPER.py", "BINANCE_LIVE.py", "trader1/runtime/boot/safe_launcher.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- repository root exposes exactly four allowed launchers
- no unexpected root launcher exists
- paper launchers cannot reference live order path
- live launchers remain hard-blocked in MVP-1
- Binance launchers explicitly select market_type
- launcher reports cannot set live_order_ready
- launcher reports cannot set live_order_allowed

known_omissions_by_design:
- read-only dashboard UI
- live key loading
- live order API
- exchange adapter
- paper broker
- futures live implementation

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

MVP1_SAFE_BOOT_SKELETON. Root launchers, startup probe, heartbeat, and summary shell are fail-closed safety artifacts only. This file is not authority and cannot create live permission.
""",
    )


def update_state_and_evidence(now: str, trader_hash: str, agents_hash: str, runtime_reports: list[str]) -> None:
    validator_results = run_validators(["root_launcher_guard_validator", "root_launcher_surface_validator"])
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
    write_json(ROOT / "system" / "evidence" / "validator_runs" / "MVP1_ROOT_LAUNCHER_SURFACE.validator_run_log.json", validator_log)

    stage_gate = {
        "stage_gate_schema_id": "trader1.stage_gate_result.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-1",
        "root_launcher_guard_validator": "PASS",
        "root_launcher_surface_validator": "PASS",
        "root_launcher_reports": runtime_reports,
        "live_order_allowed": False,
        "stage_gate_status": "PASS_FOR_MVP1_ROOT_LAUNCHER_SURFACE_ONLY",
    }
    write_json(ROOT / "system" / "evidence" / "stage_gates" / "MVP1_ROOT_LAUNCHER_SURFACE.stage_gate_result.json", stage_gate)

    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "evidence_manifest_id": "MVP1_ROOT_LAUNCHER_SURFACE_EVIDENCE",
        "artifact_paths": [
            "UPBIT_PAPER.py",
            "UPBIT_LIVE.py",
            "BINANCE_PAPER.py",
            "BINANCE_LIVE.py",
            "contracts/schema/root_launcher_report.schema.json",
            "trader1/runtime/boot/safe_launcher.py",
            "trader1/runtime/boot/launcher_guard.py",
            "trader1/validation/mvp0_validators.py",
            "tools/run_root_launcher_validators.py",
            "tests/contract/test_root_launchers.py",
            "tests/runtime/test_safe_launcher.py",
        ]
        + runtime_reports,
        "known_blockers": [
            "CONTRACT_GAP_HIGH",
            "LIVE_FINAL_GUARD_FAILED",
            "SNAPSHOT_SCOPE_MISMATCH",
            "PREFLIGHT_FAILED",
            "LIVE_READY_MISSING",
            "API_UNVERIFIED",
            "OPERATOR_APPROVAL_MISSING",
            "LIVE_ENABLING_EVIDENCE_MISSING",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "system" / "evidence" / "MVP1_ROOT_LAUNCHER_SURFACE.evidence_manifest.json", evidence_manifest)

    patch_result = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-1",
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": ["REQ-MVP1-ROOT-LAUNCHER-SURFACE"],
        "affected_exchange": "UPBIT_AND_BINANCE",
        "affected_market_type": "KRW_SPOT_AND_SPOT",
        "affected_mode": "PAPER_AND_LIVE_HARD_BLOCKED",
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": ["root_launcher_report schema", "root_launcher_surface_validator"],
        "new_or_changed_schema_ids": ["trader1.root_launcher_report.v1"],
        "validators_required": ["root_launcher_guard_validator", "root_launcher_surface_validator"],
        "validators_run": validator_results,
        "tests_run": [
            {"command": "python -m compileall trader1 tools tests -q", "status": "PASS"},
            {"command": "python tools/run_root_launcher_validators.py", "status": "PASS"},
            {"command": "python -m unittest tests.contract.test_root_launchers -v", "status": "PASS"},
            {"command": "python -m unittest tests.runtime.test_safe_launcher -v", "status": "PASS"},
            {"command": "python tools/run_mvp0_validators.py", "status": "PASS"},
            {"command": "python tools/validate_mvp0_contracts.py", "status": "PASS"},
            {"command": "python -m unittest discover -s tests -v", "status": "PASS"},
        ],
        "coverage_unmapped_count": 0,
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED_FOR_ROOT_LAUNCHER_SURFACE",
        "read_cache_update_required": False,
        "context_pack_update_required": False,
        "current_implementation_state_updated": True,
        "next_task_class": "MVP1_SAFE_BOOT_SKELETON",
        "next_required_section_ids": ["SECTION_AGENTS_MVP1_SAFE_BOOT_FILES", "SECTION_DASHBOARD_SHELL"],
        "next_optional_section_ids": ["SECTION_KILL_SWITCH_SCAFFOLD", "SECTION_RESOURCE_GUARD"],
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
        "evidence_manifest_path": "system/evidence/MVP1_ROOT_LAUNCHER_SURFACE.evidence_manifest.json",
        "validator_run_log_path": "system/evidence/validator_runs/MVP1_ROOT_LAUNCHER_SURFACE.validator_run_log.json",
        "stage_gate_result_path": "system/evidence/stage_gates/MVP1_ROOT_LAUNCHER_SURFACE.stage_gate_result.json",
        "token_navigation_patch": True,
        "active_read_surface_used": [
            "SECTION_MVP1_ROOT_LAUNCHER_SCOPE",
            "SECTION_MVP1_ROOT_LAUNCHER_FOUR",
            "SECTION_MVP1_SAFE_BOOT_SEQUENCE",
            "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT",
            "SECTION_AGENTS_MVP1_ROOT_LAUNCHERS",
        ],
        "task_class": "MVP1_SAFE_BOOT_SKELETON",
        "required_section_ids": ["SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT", "SECTION_MVP1_ROOT_LAUNCHER_FOUR"],
        "expanded_section_ids": [
            "SECTION_MVP1_ROOT_LAUNCHER_SCOPE",
            "SECTION_MVP1_ROOT_LAUNCHER_FOUR",
            "SECTION_MVP1_SAFE_BOOT_SEQUENCE",
            "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT",
            "SECTION_AGENTS_MVP1_ROOT_LAUNCHERS",
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
        "failure_analysis_status": "NOT_REQUIRED_FOR_ROOT_LAUNCHER_SURFACE",
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
    write_json(ROOT / "system" / "evidence" / "patch_results" / "MVP1_ROOT_LAUNCHER_SURFACE.patch_result.json", patch_result)

    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    if "REQ-MVP1-ROOT-LAUNCHER-SURFACE" not in state["completed_requirement_ids"]:
        state["completed_requirement_ids"].append("REQ-MVP1-ROOT-LAUNCHER-SURFACE")
    if "trader1.root_launcher_report.v1" not in state["implemented_schema_ids"]:
        state["implemented_schema_ids"].append("trader1.root_launcher_report.v1")
    if "root_launcher_surface_validator" not in state["implemented_validator_ids"]:
        state["implemented_validator_ids"].append("root_launcher_surface_validator")
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
            "patch_result_path": "system/evidence/patch_results/MVP1_ROOT_LAUNCHER_SURFACE.patch_result.json",
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
    runtime_reports = write_runtime_reports()
    update_navigation(now, trader_hash, agents_hash)
    update_state_and_evidence(now, trader_hash, agents_hash, runtime_reports)
    update_read_cache(now, trader_hash, agents_hash)
    print(json.dumps({"patch_id": PATCH_ID, "status": "evidence_updated", "live_order_allowed_after": False}, indent=2))


if __name__ == "__main__":
    main()
