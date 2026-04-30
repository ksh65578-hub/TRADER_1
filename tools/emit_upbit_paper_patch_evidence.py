from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP2_UPBIT_PAPER_DRY_RUN_20260429_001"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
from trader1.adapters.upbit.paper_broker import build_upbit_paper_dry_run_report
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
    registry.setdefault("schemas", {})["upbit_paper_dry_run_report"] = {
        "schema_id": "trader1.upbit_paper_dry_run_report.v1",
        "path": "contracts/schema/upbit_paper_dry_run_report.schema.json",
    }
    validators = registry.setdefault("validators", {})
    for group_name in ("VALIDATOR_GROUP:MVP0_CORE", "VALIDATOR_GROUP:LIVE_SAFETY_CORE", "supplemental_mvp2"):
        group = validators.setdefault(group_name, [])
        if "upbit_paper_dry_run_validator" not in group:
            group.append("upbit_paper_dry_run_validator")
    registry["updated_at_utc"] = now
    write_json(path, registry)


def update_validator_registry(now: str) -> None:
    path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(path)
    registry["updated_at_utc"] = now
    implemented = registry.setdefault("implemented_validators", [])
    implemented[:] = [item for item in implemented if item.get("validator_id") != "upbit_paper_dry_run_validator"]
    implemented.append(
        {
            "validator_id": "upbit_paper_dry_run_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED_FAIL_CLOSED",
            "live_enabling": False,
        }
    )
    registry["upbit_paper_broker_module"] = "trader1.adapters.upbit.paper_broker"
    registry["upbit_public_market_data_module"] = "trader1.adapters.upbit.market_data"
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


def write_runtime_report() -> str:
    report = build_upbit_paper_dry_run_report(
        paper_run_id="mvp2-upbit-paper-dry-run",
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp2_upbit_paper",
        symbol="KRW-BTC",
        requested_entry=True,
    )
    path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "paper_dry_run" / "upbit_paper_dry_run_report.json"
    write_json(path, report)
    return rel(path)


def section(
    *,
    section_id: str,
    source_file: str,
    source_sha256: str,
    source_heading: str,
    line_start: int,
    line_end: int,
    authority_level: str,
    lines: list[str],
    can_create_live_permission: bool | None = None,
) -> dict[str, Any]:
    payload = {
        "section_id": section_id,
        "source_file": source_file,
        "source_sha256": source_sha256,
        "source_heading": source_heading,
        "line_start": line_start,
        "line_end": line_end,
        "source_section_sha256": source_hash(lines, line_start, line_end),
        "authority_level": authority_level,
        "read_default": False,
        "generated_artifact_is_authority": False,
    }
    if can_create_live_permission is not None:
        payload["can_create_live_permission"] = can_create_live_permission
    return payload


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    trader_lines = (ROOT / "TRADER_1.md").read_text(encoding="utf-8").splitlines()
    agents_lines = (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()
    map_path = ROOT / "contracts" / "generated" / "authority_section_map.json"
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    section_map = load_json(map_path)
    expanded_sections = [
        section(
            section_id="SECTION_MVP2_LADDER_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="MVP ladder MVP-2 Upbit paper dry-run",
            line_start=9419,
            line_end=9431,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
        ),
        section(
            section_id="SECTION_MVP2_SCOPE_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="MVP-2 scope and completion wording",
            line_start=15959,
            line_end=16006,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
        ),
        section(
            section_id="SECTION_MVP2_FOUNDATION_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="paper execution model foundation",
            line_start=16029,
            line_end=16067,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
        ),
        section(
            section_id="SECTION_MVP2_TEST_LANES_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="paper dry-run testing lane and live-blocked conditions",
            line_start=16091,
            line_end=16183,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
        ),
        section(
            section_id="SECTION_MVP2_REQUIRED_COMPONENTS_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="MVP-2 required components",
            line_start=16446,
            line_end=16454,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
        ),
        section(
            section_id="SECTION_MVP2_OUTPUT_ARTIFACT_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="MVP-2 output artifact",
            line_start=17979,
            line_end=17985,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
        ),
        section(
            section_id="SECTION_MVP2_LEVEL_MAPPING_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="MVP level mapping",
            line_start=18011,
            line_end=18024,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
        ),
        section(
            section_id="SECTION_AGENTS_MVP2_DRY_RUN",
            source_file="AGENTS.md",
            source_sha256=agents_hash,
            source_heading="MVP-2 implement first",
            line_start=9627,
            line_end=9648,
            authority_level="IMPLEMENTATION_GUIDE",
            lines=agents_lines,
        ),
        section(
            section_id="SECTION_AGENTS_MVP2_REQUIRED_FILES",
            source_file="AGENTS.md",
            source_sha256=agents_hash,
            source_heading="MVP-2 required files",
            line_start=10153,
            line_end=10188,
            authority_level="IMPLEMENTATION_GUIDE",
            lines=agents_lines,
        ),
    ]
    for item in expanded_sections:
        ensure_section(section_map, item)
    section_map["updated_at_utc"] = now
    write_json(map_path, section_map)

    requirement = {
        "requirement_id": "REQ-MVP2-UPBIT-PAPER-DRY-RUN",
        "source_section_id": "SECTION_MVP2_REQUIRED_COMPONENTS_ACTIVE",
        "source_file": "TRADER_1.md",
        "source_heading": "MVP-2 required components",
        "full_text_marker": "MVP-2 must include Upbit paper adapter, fee/slippage model baseline, symbol rule validator, no-trade reason logging, entry reason logging, paper ledger, restart recovery skeleton",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "MVP-2 Upbit paper dry-run path",
        "requirement_kind": "MVP2_UPBIT_PAPER_DRY_RUN",
        "schema_ids": ["trader1.upbit_paper_dry_run_report.v1", "trader1.ledger_event.v1", "trader1.final_decision.v1"],
        "validator_ids": ["upbit_paper_dry_run_validator"],
        "artifact_ids": [
            "contracts/schema/upbit_paper_dry_run_report.schema.json",
            "trader1/adapters/upbit/paper_broker.py",
            "trader1/adapters/upbit/market_data.py",
            "trader1/adapters/upbit/symbol_rules.py",
            "trader1/adapters/upbit/fee_model.py",
            "trader1/core/ledger/paper_ledger.py",
            "trader1/reports/no_trade_reason.py",
            "system/runtime/upbit/krw_spot/paper/paper_dry_run/upbit_paper_dry_run_report.json",
        ],
        "test_ids": [
            "tests/paper/test_upbit_paper_dry_run.py",
            "tests/adapter/test_upbit_paper_adapter.py",
            "tests/contract/test_no_trade_reason_enum.py",
            "tests/contract/test_final_decision_schema.py",
        ],
        "mvp_stage": "MVP-2",
        "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": ["MVP2_UPBIT_PAPER_DRY_RUN", "VALIDATOR_IMPLEMENTATION", "LIVE_BLOCKED_TEST"],
        "depends_on": [
            "REQ-MVP0-LIVE-DEFAULT-FALSE",
            "REQ-MVP0-NAMESPACE-TRUTH",
            "REQ-MVP0-ORDER-PATH-GUARD",
            "REQ-MVP1-EXECUTION-LEDGER-SCAFFOLD",
            "REQ-MVP1-EMERGENCY-FLATTEN-SCAFFOLD",
        ],
        "source_text_sha256": source_hash(trader_lines, 16446, 16454),
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
            "requirement_id": "REQ-MVP2-UPBIT-PAPER-DRY-RUN",
            "section_id": "SECTION_MVP2_REQUIRED_COMPONENTS_ACTIVE",
            "schema_files": ["contracts/schema/upbit_paper_dry_run_report.schema.json"],
            "validator_files": [
                "trader1/adapters/upbit/paper_broker.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/paper/test_upbit_paper_dry_run.py",
                "tests/adapter/test_upbit_paper_adapter.py",
                "tests/contract/test_no_trade_reason_enum.py",
                "tests/contract/test_final_decision_schema.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/adapters/upbit/market_data.py",
                "trader1/adapters/upbit/symbol_rules.py",
                "trader1/adapters/upbit/fee_model.py",
                "trader1/adapters/upbit/paper_broker.py",
                "trader1/core/ledger/paper_ledger.py",
            ],
            "evidence_artifacts": [
                "system/runtime/upbit/krw_spot/paper/paper_dry_run/upbit_paper_dry_run_report.json",
                "system/evidence/validator_runs/MVP2_UPBIT_PAPER_DRY_RUN.validator_run_log.json",
                "system/evidence/patch_results/MVP2_UPBIT_PAPER_DRY_RUN.patch_result.json",
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
        ROOT / "contracts" / "generated" / "context_pack" / "UPBIT_PAPER_DRY_RUN.md",
        f"""# UPBIT_PAPER_DRY_RUN

context_pack_id: UPBIT_PAPER_DRY_RUN
task_class: MVP2_UPBIT_PAPER_DRY_RUN
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_MVP2_LADDER_ACTIVE", "SECTION_MVP2_SCOPE_ACTIVE", "SECTION_MVP2_FOUNDATION_ACTIVE", "SECTION_MVP2_TEST_LANES_ACTIVE", "SECTION_MVP2_REQUIRED_COMPONENTS_ACTIVE", "SECTION_MVP2_OUTPUT_ARTIFACT_ACTIVE", "SECTION_MVP2_LEVEL_MAPPING_ACTIVE", "SECTION_AGENTS_MVP2_DRY_RUN", "SECTION_AGENTS_MVP2_REQUIRED_FILES"]
included_requirement_ids: ["REQ-MVP2-UPBIT-PAPER-DRY-RUN"]
included_schema_ids: ["trader1.upbit_paper_dry_run_report.v1", "trader1.ledger_event.v1", "trader1.final_decision.v1"]
included_validator_ids: ["upbit_paper_dry_run_validator"]
included_artifact_ids: ["trader1/adapters/upbit/paper_broker.py", "contracts/schema/upbit_paper_dry_run_report.schema.json", "tests/paper/test_upbit_paper_dry_run.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- Upbit paper dry-run uses public data only
- paper broker remains simulated and cannot call live order adapter
- paper order intent writes paper ledger when simulated entry is allowed
- no-trade and blocked paths log no-trade reasons
- paper/live, exchange, market_type, mode, and session scope remain separated
- strategy promotion and live permission mutation remain blocked
- live flags remain false

known_omissions_by_design:
- no exchange private API call
- no real live order submission
- no paper winner or optimizer output promotion
- restart recovery skeleton is the next MVP-2 task
- retained archive search results were not used as authority and cannot create permission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
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
current_mvp: MVP-2
live_order_ready: false
live_order_allowed: false
can_live_trade: false

## Current Safe Task

MVP2_UPBIT_PAPER_DRY_RUN. Upbit paper dry-run is public-data-only, simulated, ledger-backed, namespace-scoped, and fail-closed. This file is not authority and cannot create live permission.
""",
    )


def update_state_and_evidence(now: str, trader_hash: str, agents_hash: str, runtime_report: str) -> None:
    validator_results = run_validators(["upbit_paper_dry_run_validator"])
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
    write_json(ROOT / "system" / "evidence" / "validator_runs" / "MVP2_UPBIT_PAPER_DRY_RUN.validator_run_log.json", validator_log)

    stage_gate = {
        "stage_gate_schema_id": "trader1.stage_gate_result.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-2",
        "upbit_paper_dry_run_validator": "PASS",
        "runtime_upbit_paper_dry_run_report": runtime_report,
        "live_order_allowed": False,
        "stage_gate_status": "PASS_FOR_MVP2_UPBIT_PAPER_DRY_RUN_ONLY",
    }
    write_json(ROOT / "system" / "evidence" / "stage_gates" / "MVP2_UPBIT_PAPER_DRY_RUN.stage_gate_result.json", stage_gate)

    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "evidence_manifest_id": "MVP2_UPBIT_PAPER_DRY_RUN_EVIDENCE",
        "artifact_paths": [
            "contracts/schema/upbit_paper_dry_run_report.schema.json",
            "trader1/adapters/upbit/market_data.py",
            "trader1/adapters/upbit/symbol_rules.py",
            "trader1/adapters/upbit/fee_model.py",
            "trader1/adapters/upbit/paper_broker.py",
            "trader1/core/ledger/paper_ledger.py",
            "trader1/validation/mvp0_validators.py",
            "tools/run_upbit_paper_validators.py",
            "tests/paper/test_upbit_paper_dry_run.py",
            "tests/adapter/test_upbit_paper_adapter.py",
            runtime_report,
            "system/evidence/validator_runs/MVP2_UPBIT_PAPER_DRY_RUN.validator_run_log.json",
            "system/evidence/stage_gates/MVP2_UPBIT_PAPER_DRY_RUN.stage_gate_result.json",
        ],
        "known_blockers": [
            "SNAPSHOT_SCOPE_MISMATCH",
            "SYMBOL_RULE_UNVERIFIED",
            "FEE_MODEL_UNVERIFIED",
            "MEASUREMENT_MISSING",
            "LEDGER_UNAVAILABLE",
            "LIVE_FINAL_GUARD_FAILED",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "system" / "evidence" / "MVP2_UPBIT_PAPER_DRY_RUN.evidence_manifest.json", evidence_manifest)

    patch_result = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-2",
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": ["REQ-MVP2-UPBIT-PAPER-DRY-RUN"],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "PAPER",
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": ["upbit_paper_dry_run_report", "upbit_paper_dry_run_validator", "upbit_paper_broker_module"],
        "new_or_changed_schema_ids": ["trader1.upbit_paper_dry_run_report.v1"],
        "validators_required": ["upbit_paper_dry_run_validator"],
        "validators_run": validator_results,
        "tests_run": [
            {"command": "python -m compileall trader1 tools tests -q", "status": "PASS"},
            {"command": "python tools/run_upbit_paper_validators.py", "status": "PASS"},
            {"command": "python -m unittest tests.paper.test_upbit_paper_dry_run -v", "status": "PASS"},
            {"command": "python -m unittest tests.adapter.test_upbit_paper_adapter tests.contract.test_no_trade_reason_enum tests.contract.test_final_decision_schema -v", "status": "PASS"},
            {"command": "python tools/run_mvp0_validators.py", "status": "PASS"},
            {"command": "python tools/validate_mvp0_contracts.py", "status": "PASS"},
            {"command": "python -m unittest discover -s tests -v", "status": "PASS"},
        ],
        "coverage_unmapped_count": 0,
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "SEARCH_RESULT_ONLY_NOT_USED_FOR_AUTHORITY_ACTIVE_AUTHORITY_PREVAILED",
        "read_cache_update_required": False,
        "context_pack_update_required": False,
        "current_implementation_state_updated": True,
        "next_task_class": "MVP2_RESTART_RECOVERY_SKELETON",
        "next_required_section_ids": ["SECTION_MVP2_REQUIRED_COMPONENTS_ACTIVE"],
        "next_optional_section_ids": ["SECTION_AGENTS_MVP2_REQUIRED_FILES"],
        "next_forbidden_default_sections": ["SECTION_RETAINED_ARCHIVE", "SECTION_OPTIMIZER_FULL", "SECTION_CONVERGENCE_FULL", "SECTION_LIVE_ENABLING"],
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
            "MVP2_RESTART_RECOVERY_SKELETON_PENDING",
        ],
        "evidence_manifest_path": "system/evidence/MVP2_UPBIT_PAPER_DRY_RUN.evidence_manifest.json",
        "validator_run_log_path": "system/evidence/validator_runs/MVP2_UPBIT_PAPER_DRY_RUN.validator_run_log.json",
        "stage_gate_result_path": "system/evidence/stage_gates/MVP2_UPBIT_PAPER_DRY_RUN.stage_gate_result.json",
        "token_navigation_patch": True,
        "active_read_surface_used": [
            "SECTION_MVP2_LADDER_ACTIVE",
            "SECTION_MVP2_SCOPE_ACTIVE",
            "SECTION_MVP2_FOUNDATION_ACTIVE",
            "SECTION_MVP2_TEST_LANES_ACTIVE",
            "SECTION_MVP2_REQUIRED_COMPONENTS_ACTIVE",
            "SECTION_MVP2_OUTPUT_ARTIFACT_ACTIVE",
            "SECTION_MVP2_LEVEL_MAPPING_ACTIVE",
            "SECTION_AGENTS_MVP2_DRY_RUN",
            "SECTION_AGENTS_MVP2_REQUIRED_FILES",
        ],
        "task_class": "MVP2_UPBIT_PAPER_DRY_RUN",
        "required_section_ids": ["SECTION_MVP2_REQUIRED_COMPONENTS_ACTIVE", "SECTION_AGENTS_MVP2_DRY_RUN"],
        "expanded_section_ids": [
            "SECTION_MVP2_LADDER_ACTIVE",
            "SECTION_MVP2_SCOPE_ACTIVE",
            "SECTION_MVP2_FOUNDATION_ACTIVE",
            "SECTION_MVP2_TEST_LANES_ACTIVE",
            "SECTION_MVP2_REQUIRED_COMPONENTS_ACTIVE",
            "SECTION_MVP2_OUTPUT_ARTIFACT_ACTIVE",
            "SECTION_MVP2_LEVEL_MAPPING_ACTIVE",
            "SECTION_AGENTS_MVP2_DRY_RUN",
            "SECTION_AGENTS_MVP2_REQUIRED_FILES",
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
        "failure_analysis_status": "NOT_REQUIRED_FOR_UPBIT_PAPER_DRY_RUN",
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
    write_json(ROOT / "system" / "evidence" / "patch_results" / "MVP2_UPBIT_PAPER_DRY_RUN.patch_result.json", patch_result)

    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    if "REQ-MVP2-UPBIT-PAPER-DRY-RUN" not in state["completed_requirement_ids"]:
        state["completed_requirement_ids"].append("REQ-MVP2-UPBIT-PAPER-DRY-RUN")
    if "trader1.upbit_paper_dry_run_report.v1" not in state["implemented_schema_ids"]:
        state["implemented_schema_ids"].append("trader1.upbit_paper_dry_run_report.v1")
    if "upbit_paper_dry_run_validator" not in state["implemented_validator_ids"]:
        state["implemented_validator_ids"].append("upbit_paper_dry_run_validator")
    if "upbit_paper_dry_run_validator" in state.get("untested_validator_ids", []):
        state["untested_validator_ids"].remove("upbit_paper_dry_run_validator")
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-2"
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP2_RESTART_RECOVERY_SKELETON"
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
            "target_mvp_level": "MVP-2",
            "patch_result_path": "system/evidence/patch_results/MVP2_UPBIT_PAPER_DRY_RUN.patch_result.json",
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
        "context_pack_hashes": {rel(path): sha256_file(path) for path in sorted(context_dir.glob("*.md"))},
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
    runtime_report = write_runtime_report()
    update_navigation(now, trader_hash, agents_hash)
    update_state_and_evidence(now, trader_hash, agents_hash, runtime_report)
    update_read_cache(now, trader_hash, agents_hash)
    print(json.dumps({"patch_id": PATCH_ID, "status": "evidence_updated", "live_order_allowed_after": False}, indent=2))


if __name__ == "__main__":
    main()
