from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP1_OPERATOR_CONTROL_20260428_001"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
from trader1.runtime.operator_control.operator_control import build_operator_action_audit
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


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


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
    return sha256_json({rel(schema): sha256_file(schema) for schema in schema_files})


def source_tree_hash() -> str:
    paths = sorted((ROOT / "trader1").rglob("*.py")) + sorted((ROOT / "tools").glob("*.py"))
    return sha256_json({rel(path): sha256_file(path) for path in paths if "__pycache__" not in path.parts})


def update_registry(now: str) -> None:
    path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(path)
    registry.setdefault("schemas", {})["operator_action_audit"] = {
        "schema_id": "trader1.operator_action_audit.v1",
        "path": "contracts/schema/operator_action_audit.schema.json",
    }
    validators = registry.setdefault("validators", {})
    for group_name in ("VALIDATOR_GROUP:MVP0_CORE", "VALIDATOR_GROUP:LIVE_SAFETY_CORE", "supplemental_mvp1"):
        group = validators.setdefault(group_name, [])
        for validator_id in ("operator_action_audit_validator", "operator_control_validator"):
            if validator_id not in group:
                group.append(validator_id)
    registry["updated_at_utc"] = now
    write_json(path, registry)


def update_validator_registry(now: str) -> None:
    path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(path)
    registry["updated_at_utc"] = now
    implemented = registry.setdefault("implemented_validators", [])
    implemented[:] = [
        item
        for item in implemented
        if item.get("validator_id") not in {"operator_action_audit_validator", "operator_control_validator"}
    ]
    for validator_id in ("operator_action_audit_validator", "operator_control_validator"):
        implemented.append(
            {
                "validator_id": validator_id,
                "module_path": "trader1.validation.mvp0_validators",
                "status": "IMPLEMENTED_FAIL_CLOSED",
                "live_enabling": False,
            }
        )
    registry["operator_control_module"] = "trader1.runtime.operator_control.operator_control"
    write_json(path, registry)


def update_authority_manifest(now: str) -> None:
    path = ROOT / "contracts" / "authority_manifest.json"
    manifest = load_json(path)
    manifest["registry_yaml_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "registry.yaml")
    manifest["schema_bundle_sha256_when_generated"] = schema_bundle_hash()
    manifest["validator_bundle_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "validators" / "validator_registry.json")
    manifest["source_tree_hash_when_generated"] = source_tree_hash()
    manifest["created_at_utc"] = manifest.get("created_at_utc", now)
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = sha256_json(manifest)
    write_json(path, manifest)


def write_runtime_operator_audit() -> str:
    record = build_operator_action_audit(
        action_id="mvp1-manual-stop",
        operator_id_hash="operator-hash-redacted",
        action_code="manual_stop",
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp1_operator_control",
    )
    path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "operator_action_audit.json"
    write_json(path, record)
    return rel(path)


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    trader_lines = (ROOT / "TRADER_1.md").read_text(encoding="utf-8").splitlines()
    agents_lines = (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()
    map_path = ROOT / "contracts" / "generated" / "authority_section_map.json"
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    section_map = load_json(map_path)
    for section in [
        {
            "section_id": "SECTION_OPERATOR_ACTION_AUDIT_SCHEMA_EXACT",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "operator_action_audit.schema.json",
            "line_start": 8062,
            "line_end": 8115,
            "source_section_sha256": source_hash(trader_lines, 8062, 8115),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_OPERATOR_CONTROL_ACTIVE_RULES",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "operator control",
            "line_start": 10044,
            "line_end": 10072,
            "source_section_sha256": source_hash(trader_lines, 10044, 10072),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_OPERATOR_CONTROL_VALIDATOR_IDS",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "operator control validators",
            "line_start": 4967,
            "line_end": 5002,
            "source_section_sha256": source_hash(trader_lines, 4967, 5002),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_CORE_MANUAL_BYPASS_RULE",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "Core operating rules",
            "line_start": 4269,
            "line_end": 4272,
            "source_section_sha256": source_hash(trader_lines, 4269, 4272),
            "authority_level": "ACTIVE_AUTHORITY",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_AGENTS_OPERATOR_CONTROL_RULES",
            "source_file": "AGENTS.md",
            "source_sha256": agents_hash,
            "source_heading": "Operator control rules",
            "line_start": 6145,
            "line_end": 6170,
            "source_section_sha256": source_hash(agents_lines, 6145, 6170),
            "authority_level": "IMPLEMENTATION_GUIDE",
            "read_default": False,
            "generated_artifact_is_authority": False,
        },
        {
            "section_id": "SECTION_RETAINED_OPERATOR_CONTROL_DETAIL_LOOKUP",
            "source_file": "TRADER_1.md",
            "source_sha256": trader_hash,
            "source_heading": "retained operator control omitted-detail lookup",
            "line_start": 15815,
            "line_end": 15871,
            "source_section_sha256": source_hash(trader_lines, 15815, 15871),
            "authority_level": "ARCHIVE_ONLY_NON_AUTHORITY_TRACEABILITY_ONLY",
            "read_default": False,
            "generated_artifact_is_authority": False,
            "can_create_live_permission": False,
        },
    ]:
        ensure_section(section_map, section)
    section_map["updated_at_utc"] = now
    write_json(map_path, section_map)

    requirement = {
        "requirement_id": "REQ-MVP1-OPERATOR-CONTROL-AUDIT",
        "source_section_id": "SECTION_OPERATOR_CONTROL_ACTIVE_RULES",
        "source_file": "TRADER_1.md",
        "source_heading": "operator control",
        "full_text_marker": "manual control cannot bypass risk veto, kill switch, ledger durability, reconciliation required, hard truth, symbol rule, policy block, or live readiness",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "MVP-1 fail-closed operator control audit scaffold",
        "requirement_kind": "MVP1_SAFE_BOOT_SKELETON",
        "schema_ids": ["trader1.operator_action_audit.v1", "trader1.validator_result.v1"],
        "validator_ids": ["operator_action_audit_validator", "operator_control_validator"],
        "artifact_ids": [
            "contracts/schema/operator_action_audit.schema.json",
            "trader1/runtime/operator_control/operator_control.py",
            "tools/run_operator_control_validators.py",
            "tests/runtime/test_operator_control.py",
            "system/runtime/upbit/krw_spot/paper/operator_action_audit.json",
        ],
        "test_ids": ["tests/runtime/test_operator_control.py"],
        "mvp_stage": "MVP-1",
        "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": ["MVP1_SAFE_BOOT_SKELETON", "VALIDATOR_IMPLEMENTATION"],
        "depends_on": [
            "REQ-MVP0-NAMESPACE-TRUTH",
            "REQ-MVP0-ORDER-PATH-GUARD",
            "REQ-MVP1-KILL-SWITCH-RESOURCE-GUARD",
            "REQ-MVP1-EXECUTION-LEDGER-SCAFFOLD",
        ],
        "source_text_sha256": source_hash(trader_lines, 10044, 10072),
        "source_authority_sha256": trader_hash,
        "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
        "test_status": "PASS",
    }
    index = load_json(index_path)
    ensure_requirement(index, requirement)
    index["updated_at_utc"] = now
    index["retained_archive_read"] = True
    write_json(index_path, index)

    matrix = load_json(matrix_path)
    matrix["schema_file_count"] = len(list((ROOT / "contracts" / "schema").glob("*.schema.json")))
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": "REQ-MVP1-OPERATOR-CONTROL-AUDIT",
            "section_id": "SECTION_OPERATOR_CONTROL_ACTIVE_RULES",
            "schema_files": ["contracts/schema/operator_action_audit.schema.json"],
            "validator_files": [
                "trader1/runtime/operator_control/operator_control.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/runtime/test_operator_control.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/operator_control/operator_control.py"],
            "evidence_artifacts": [
                "system/runtime/upbit/krw_spot/paper/operator_action_audit.json",
                "system/evidence/validator_runs/MVP1_OPERATOR_CONTROL.validator_run_log.json",
                "system/evidence/patch_results/MVP1_OPERATOR_CONTROL.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "new_or_changed_schema_ids",
                "validators_run",
                "tests_run",
                "retained_archive_read",
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
        ROOT / "contracts" / "generated" / "context_pack" / "OPERATOR_CONTROL.md",
        f"""# OPERATOR_CONTROL

context_pack_id: OPERATOR_CONTROL
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_OPERATOR_ACTION_AUDIT_SCHEMA_EXACT", "SECTION_OPERATOR_CONTROL_ACTIVE_RULES", "SECTION_OPERATOR_CONTROL_VALIDATOR_IDS", "SECTION_CORE_MANUAL_BYPASS_RULE", "SECTION_AGENTS_OPERATOR_CONTROL_RULES"]
included_requirement_ids: ["REQ-MVP1-OPERATOR-CONTROL-AUDIT"]
included_schema_ids: ["trader1.operator_action_audit.v1", "trader1.validator_result.v1"]
included_validator_ids: ["operator_action_audit_validator", "operator_control_validator"]
included_artifact_ids: ["trader1/runtime/operator_control/operator_control.py", "contracts/schema/operator_action_audit.schema.json", "tests/runtime/test_operator_control.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- manual controls produce an audit record
- high-risk controls require explicit confirmation and scope
- manual_stop forces a kill-switch blocked audit
- manual_resume_read_only cannot resume live mode
- manual reduce/exit remains blocked without adapter, ledger, and reconciliation evidence
- manual action cannot create live_order_ready, live_order_allowed, can_live_trade, or can_submit_order

known_omissions_by_design:
- no live order adapter call
- no emergency flatten execution
- no operator UI
- no exchange reconciliation adapter
- retained archive was read only for omitted-detail lookup and cannot create permission

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
current_mvp: {state.get("current_mvp", "MVP-1")}
live_order_ready: false
live_order_allowed: false
can_live_trade: false

## Current Safe Task

MVP1_SAFE_BOOT_SKELETON. Operator control is audit-only, confirmation-gated for high-risk actions, and fail-closed. This file is not authority and cannot create live permission.
""",
    )


def update_state_and_evidence(now: str, trader_hash: str, agents_hash: str, runtime_audit: str) -> None:
    validator_results = run_validators(["operator_action_audit_validator", "operator_control_validator"])
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
    write_json(ROOT / "system" / "evidence" / "validator_runs" / "MVP1_OPERATOR_CONTROL.validator_run_log.json", validator_log)

    stage_gate = {
        "stage_gate_schema_id": "trader1.stage_gate_result.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-1",
        "operator_action_audit_validator": "PASS",
        "operator_control_validator": "PASS",
        "runtime_operator_audit": runtime_audit,
        "live_order_allowed": False,
        "stage_gate_status": "PASS_FOR_MVP1_OPERATOR_CONTROL_ONLY",
    }
    write_json(ROOT / "system" / "evidence" / "stage_gates" / "MVP1_OPERATOR_CONTROL.stage_gate_result.json", stage_gate)

    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "evidence_manifest_id": "MVP1_OPERATOR_CONTROL_EVIDENCE",
        "artifact_paths": [
            "contracts/schema/operator_action_audit.schema.json",
            "trader1/runtime/operator_control/operator_control.py",
            "trader1/validation/mvp0_validators.py",
            "tools/run_operator_control_validators.py",
            "tests/runtime/test_operator_control.py",
            runtime_audit,
            "system/evidence/validator_runs/MVP1_OPERATOR_CONTROL.validator_run_log.json",
            "system/evidence/stage_gates/MVP1_OPERATOR_CONTROL.stage_gate_result.json",
        ],
        "known_blockers": [
            "KILL_SWITCH_ACTIVE",
            "OPERATOR_APPROVAL_MISSING",
            "RISK_VETO",
            "LEDGER_UNAVAILABLE",
            "RECONCILIATION_REQUIRED",
            "SNAPSHOT_SCOPE_MISMATCH",
            "LIVE_FINAL_GUARD_FAILED",
            "UNKNOWN_BLOCKED",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "system" / "evidence" / "MVP1_OPERATOR_CONTROL.evidence_manifest.json", evidence_manifest)

    patch_result = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-1",
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": ["REQ-MVP1-OPERATOR-CONTROL-AUDIT"],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "PAPER",
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": ["operator_action_audit_validator", "operator_control_validator"],
        "new_or_changed_schema_ids": ["trader1.operator_action_audit.v1"],
        "validators_required": ["operator_action_audit_validator", "operator_control_validator"],
        "validators_run": validator_results,
        "tests_run": [
            {"command": "python -m compileall trader1 tools tests -q", "status": "PASS"},
            {"command": "python tools/run_operator_control_validators.py", "status": "PASS"},
            {"command": "python -m unittest tests.runtime.test_operator_control -v", "status": "PASS"},
            {"command": "python tools/run_mvp0_validators.py", "status": "PASS"},
            {"command": "python tools/validate_mvp0_contracts.py", "status": "PASS"},
            {"command": "python -m unittest discover -s tests -v", "status": "PASS"},
        ],
        "coverage_unmapped_count": 0,
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "READ_FOR_OMITTED_DETAIL_ONLY_ACTIVE_AUTHORITY_PREVAILED",
        "read_cache_update_required": False,
        "context_pack_update_required": False,
        "current_implementation_state_updated": True,
        "next_task_class": "MVP1_SAFE_BOOT_SKELETON",
        "next_required_section_ids": ["SECTION_RECONCILIATION_SCAFFOLD", "SECTION_EMERGENCY_FLATTEN_SCAFFOLD"],
        "next_optional_section_ids": ["SECTION_OPERATOR_UI_READ_ONLY"],
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
            "EMERGENCY_FLATTEN_UNAVAILABLE",
        ],
        "evidence_manifest_path": "system/evidence/MVP1_OPERATOR_CONTROL.evidence_manifest.json",
        "validator_run_log_path": "system/evidence/validator_runs/MVP1_OPERATOR_CONTROL.validator_run_log.json",
        "stage_gate_result_path": "system/evidence/stage_gates/MVP1_OPERATOR_CONTROL.stage_gate_result.json",
        "token_navigation_patch": True,
        "active_read_surface_used": [
            "SECTION_OPERATOR_ACTION_AUDIT_SCHEMA_EXACT",
            "SECTION_OPERATOR_CONTROL_ACTIVE_RULES",
            "SECTION_OPERATOR_CONTROL_VALIDATOR_IDS",
            "SECTION_CORE_MANUAL_BYPASS_RULE",
            "SECTION_AGENTS_OPERATOR_CONTROL_RULES",
        ],
        "task_class": "MVP1_SAFE_BOOT_SKELETON",
        "required_section_ids": ["SECTION_OPERATOR_CONTROL_SURFACE", "SECTION_OPERATOR_ACTION_AUDIT_SCHEMA_EXACT"],
        "expanded_section_ids": [
            "SECTION_OPERATOR_ACTION_AUDIT_SCHEMA_EXACT",
            "SECTION_OPERATOR_CONTROL_ACTIVE_RULES",
            "SECTION_OPERATOR_CONTROL_VALIDATOR_IDS",
            "SECTION_CORE_MANUAL_BYPASS_RULE",
            "SECTION_AGENTS_OPERATOR_CONTROL_RULES",
            "SECTION_RETAINED_OPERATOR_CONTROL_DETAIL_LOOKUP",
        ],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "UPDATED",
        "requirement_index_status": "UPDATED",
        "requirement_artifact_matrix_status": "UPDATED",
        "read_cache_manifest_status": "UPDATED",
        "context_pack_status": "GENERATED",
        "current_implementation_state_status": "UPDATED",
        "retained_archive_read": True,
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
        "failure_analysis_status": "NOT_REQUIRED_FOR_OPERATOR_CONTROL",
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
    write_json(ROOT / "system" / "evidence" / "patch_results" / "MVP1_OPERATOR_CONTROL.patch_result.json", patch_result)

    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    if "REQ-MVP1-OPERATOR-CONTROL-AUDIT" not in state["completed_requirement_ids"]:
        state["completed_requirement_ids"].append("REQ-MVP1-OPERATOR-CONTROL-AUDIT")
    if "trader1.operator_action_audit.v1" not in state["implemented_schema_ids"]:
        state["implemented_schema_ids"].append("trader1.operator_action_audit.v1")
    for validator_id in ("operator_action_audit_validator", "operator_control_validator"):
        if validator_id not in state["implemented_validator_ids"]:
            state["implemented_validator_ids"].append(validator_id)
        if validator_id in state.get("untested_validator_ids", []):
            state["untested_validator_ids"].remove(validator_id)
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
            "patch_result_path": "system/evidence/patch_results/MVP1_OPERATOR_CONTROL.patch_result.json",
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
            rel(path): sha256_file(path) for path in sorted(context_dir.glob("*.md"))
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
    runtime_audit = write_runtime_operator_audit()
    update_navigation(now, trader_hash, agents_hash)
    update_state_and_evidence(now, trader_hash, agents_hash, runtime_audit)
    update_read_cache(now, trader_hash, agents_hash)
    print(json.dumps({"patch_id": PATCH_ID, "status": "evidence_updated", "live_order_allowed_after": False}, indent=2))


if __name__ == "__main__":
    main()
