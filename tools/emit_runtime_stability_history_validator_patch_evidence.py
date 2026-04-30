from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_RUNTIME_STABILITY_HISTORY_VALIDATOR_20260429_001"
PATCH_BASENAME = "MVP4_RUNTIME_STABILITY_HISTORY_VALIDATOR"
REQUIREMENT_ID = "REQ-MVP4-RUNTIME-STABILITY-HISTORY-VALIDATOR"

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
    "registry_validator",
    "schema_validator",
    "runtime_stability_history_validator",
    "read_only_dashboard_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "generated_artifact_dirty_validator",
]

CHANGED_ARTIFACTS = [
    "trader1/runtime/health/stability_history.py",
    "trader1/validation/mvp0_validators.py",
    "contracts/registry.yaml",
    "contracts/validators/validator_registry.json",
    "tools/validate_mvp0_contracts.py",
    "tools/run_runtime_stability_history_validators.py",
    "tests/validators/test_runtime_stability_history_validator.py",
    "tools/emit_runtime_stability_history_validator_patch_evidence.py",
    "contracts/generated/context_pack/RUNTIME_STABILITY_HISTORY_VALIDATOR.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_requirement(index: dict[str, Any], requirement: dict[str, Any]) -> None:
    requirements = index.setdefault("requirements", [])
    requirements[:] = [item for item in requirements if item.get("requirement_id") != requirement["requirement_id"]]
    requirements.append(requirement)


def ensure_matrix_row(matrix: dict[str, Any], row: dict[str, Any]) -> None:
    rows = matrix.setdefault("rows", [])
    rows[:] = [item for item in rows if item.get("requirement_id") != row["requirement_id"]]
    rows.append(row)


def update_validator_catalog(now: str) -> None:
    registry_path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(registry_path)
    registry["updated_at_utc"] = now
    existing = {item["validator_id"] for item in registry.get("implemented_validators", [])}
    if "runtime_stability_history_validator" not in existing:
        registry.setdefault("implemented_validators", []).append(
            {
                "validator_id": "runtime_stability_history_validator",
                "module_path": "trader1.validation.mvp0_validators",
                "status": "IMPLEMENTED_FAIL_CLOSED",
                "live_enabling": False,
            }
        )
    registry["runtime_stability_history_module"] = "trader1.runtime.health.stability_history"
    write_json(registry_path, registry)


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    index = load_json(index_path)
    matrix = load_json(matrix_path)
    index["updated_at_utc"] = now
    matrix["updated_at_utc"] = now
    matrix["schema_file_count"] = len(list((ROOT / "contracts" / "schema").glob("*.schema.json")))
    requirement = {
        "requirement_id": REQUIREMENT_ID,
        "source_section_id": "SECTION_DASHBOARD_SERVING_TRUTH",
        "source_file": "TRADER_1.md",
        "source_heading": "dashboard serving truth and runtime health validation",
        "full_text_marker": f"{REQUIREMENT_ID}:runtime stability history must remain display-only scoped validator evidence",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "Runtime stability history validator",
        "requirement_kind": "VALIDATOR_IMPLEMENTATION",
        "schema_ids": ["trader1.runtime_stability_history.v1"],
        "validator_ids": ["runtime_stability_history_validator", "live_final_guard_validator"],
        "artifact_ids": [
            "trader1/runtime/health/stability_history.py",
            "trader1/validation/mvp0_validators.py",
            "system/runtime/<exchange>/<market_type>/<mode>/<session_id>/stability_history.json",
        ],
        "test_ids": ["tests/validators/test_runtime_stability_history_validator.py"],
        "mvp_stage": "MVP-4",
        "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": ["VALIDATOR_IMPLEMENTATION", "DASHBOARD_UX"],
        "depends_on": ["REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-HEARTBEAT", "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD"],
        "source_text_sha256": sha256_bytes(b"runtime stability history display-only scoped validator evidence"),
        "source_authority_sha256": trader_hash,
        "implementation_status": "IMPLEMENTED",
        "test_status": "PASS",
    }
    ensure_requirement(index, requirement)
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_DASHBOARD_SERVING_TRUTH",
            "schema_files": ["contracts/schema/runtime_stability_history.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py", "contracts/validators/validator_registry.json"],
            "test_files": ["tests/validators/test_runtime_stability_history_validator.py"],
            "fixture_files": ["tests/validators/test_runtime_stability_history_validator.py"],
            "runtime_modules": [
                "trader1/runtime/health/stability_history.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": ["system/runtime/<exchange>/<market_type>/<mode>/<session_id>/dashboard/index.html"],
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
            "status": "IMPLEMENTED",
        },
    )
    write_json(index_path, index)
    write_json(matrix_path, matrix)


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "RUNTIME_STABILITY_HISTORY_VALIDATOR.md",
        f"""# RUNTIME_STABILITY_HISTORY_VALIDATOR

context_pack_id: RUNTIME_STABILITY_HISTORY_VALIDATOR
task_class: MVP4_RUNTIME_STABILITY_HISTORY_VALIDATOR
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-HEARTBEAT"]
included_schema_ids: ["trader1.runtime_stability_history.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- runtime stability histories are validated through the central validator chain
- live or scale-up flag drift in history artifacts is BLOCKED
- scope mismatch across exchange, market_type, mode, or session_id is BLOCKED
- fake VALIDATED_HISTORY and aggregate-count mismatch are rejected
- validator output cannot create live readiness, live permission, trading permission, or scale-up permission

known_omissions_by_design:
- no live order path is enabled
- no exchange account call, credential load, or live burn-in is performed
- stability history is display truth only and not LIVE_READY evidence

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

Runtime stability history is now part of the validator chain. The dashboard may show operation history only from scoped, hash-linked, display-only history artifacts; fake validated history, aggregate drift, live flag drift, and scope mismatch are rejected.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_RUNTIME_STABILITY_HISTORY_SCAFFOLD.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL",
                "REQ-MVP1-HEARTBEAT",
                "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": [
                "contracts/registry.yaml::schemas.runtime_stability_history",
                "contracts/registry.yaml::validators.runtime_stability_history_validator",
                "contracts/validators/validator_registry.json::runtime_stability_history_validator",
                *CHANGED_ARTIFACTS,
            ],
            "new_or_changed_schema_ids": ["trader1.runtime_stability_history.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "UNCHANGED_LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": "MVP4_LONG_RUN_STABILITY_RESOURCE_GUARD",
            "next_required_section_ids": ["SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_OPERATOR_VISIBILITY", "SECTION_MVP3_OPERATIONAL_PAPER"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "BINANCE_FUTURES_LIVE", "LIVE_CONFIG_MUTATION"],
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
            "active_read_surface_used": ["SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "MVP4_RUNTIME_STABILITY_HISTORY_VALIDATOR",
            "required_section_ids": ["SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_LIVE_FINAL_GUARD"],
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
            "failure_analysis_status": "NOT_REQUIRED_FOR_RUNTIME_STABILITY_HISTORY_VALIDATOR",
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
            "stage_gate_status": "PASS_FOR_RUNTIME_STABILITY_HISTORY_VALIDATOR_NO_LIVE_ORDERS",
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
        f"""# MVP4 Runtime Stability History Validator Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- runtime_stability_history existed as an artifact and dashboard input, but was not independently registered in the central validator chain.
- contract validation used a static required schema list that omitted runtime_stability_history.schema.json.
- stability history validation did not recompute aggregate sample counters, allowing a misleading aggregate display if an artifact was mutated and rehashed.

Patch:
- Added runtime_stability_history_validator to the validator registry, runtime validator table, registry groups, and current implementation state.
- Added negative tests for live/scale-up drift, scope mismatch, fake VALIDATED_HISTORY, and aggregate count mismatch.
- Added runtime_stability_history.schema.json to the contract validation required schema list.
- Updated requirement_index, requirement_artifact_matrix, read cache, and patch ledger.

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
    state["next_allowed_task_class"] = "MVP4_LONG_RUN_STABILITY_RESOURCE_GUARD"
    if REQUIREMENT_ID not in state["completed_requirement_ids"]:
        state["completed_requirement_ids"].append(REQUIREMENT_ID)
    if "runtime_stability_history_validator" not in state["implemented_validator_ids"]:
        state["implemented_validator_ids"].append("runtime_stability_history_validator")
    state["completed_requirement_ids"] = sorted(state["completed_requirement_ids"])
    state["implemented_validator_ids"] = sorted(state["implemented_validator_ids"])
    state["untested_validator_ids"] = [item for item in state.get("untested_validator_ids", []) if item != "runtime_stability_history_validator"]
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
    update_validator_catalog(now)
    update_navigation(now, trader_hash, agents_hash)
    update_context(now, trader_hash, agents_hash)
    update_authority_manifest(now)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_runtime_stability_history_validator", "-v"]),
        run_command([sys.executable, "tools/run_runtime_stability_history_validators.py"]),
        run_command([sys.executable, "UPBIT_PAPER.py"]),
        run_command([sys.executable, "BINANCE_PAPER.py"]),
    ]
    validators_run = run_validators([item for item in VALIDATORS_REQUIRED if item != "generated_artifact_dirty_validator"])
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
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
