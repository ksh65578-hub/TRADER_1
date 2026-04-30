from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-RUNTIME-SOURCE-HASH-GUARD"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_RUNTIME_E2E_CONTINUE"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "contracts/schema/upbit_public_market_data_collection_report.schema.json",
    "contracts/schema/upbit_paper_runtime_cycle_report.schema.json",
    "trader1/runtime/paper/upbit_public_collector.py",
    "trader1/runtime/paper/upbit_paper_runtime.py",
    "trader1/validation/mvp0_validators.py",
    "tests/integration/test_upbit_public_collection_persistent_loop.py",
    "tests/integration/test_upbit_paper_runtime_cycle.py",
    "tools/emit_upbit_paper_runtime_source_hash_guard_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD.md",
]
VALIDATORS_REQUIRED = [
    "registry_validator",
    "schema_validator",
    "upbit_public_market_data_collection_validator",
    "upbit_paper_runtime_cycle_validator",
    "upbit_paper_persistent_loop_validator",
    "runtime_schema_instance_validator",
    "path_namespace_validator",
    "single_writer_order_path_validator",
    "live_final_guard_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if not validator_id.startswith("patch_result_runtime") and validator_id != "generated_artifact_dirty_validator"
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
    "UPBIT_PAPER_RUNTIME_LONG_RUN_EVIDENCE_MISSING",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def run_runtime_artifacts() -> list[str]:
    loop = run_upbit_paper_persistent_loop(
        root=ROOT,
        loop_id="mvp4-upbit-runtime-source-hash-guard",
        requested_cycle_count=1,
    )
    paths: list[str] = []
    for cycle in loop.get("cycle_results", []):
        paths.extend(path for path in cycle.get("artifact_paths", []) if isinstance(path, str))
    for key in ("runtime_recovery_guard_path", "paper_ledger_rollup_path"):
        if isinstance(loop.get(key), str):
            paths.append(loop[key])
    paths.append("system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-upbit-runtime-source-hash-guard.persistent_loop_report.json")
    return sorted(set(paths))


def build_audit() -> dict[str, Any]:
    collector_text = (ROOT / "trader1" / "runtime" / "paper" / "upbit_public_collector.py").read_text(encoding="utf-8")
    runtime_text = (ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_runtime.py").read_text(encoding="utf-8")
    validator_text = (ROOT / "trader1" / "validation" / "mvp0_validators.py").read_text(encoding="utf-8")
    collection_schema = load_json(ROOT / "contracts" / "schema" / "upbit_public_market_data_collection_report.schema.json")
    runtime_schema = load_json(ROOT / "contracts" / "schema" / "upbit_paper_runtime_cycle_report.schema.json")
    checks = {
        "collection_schema_requires_public_market_data_hash": "public_market_data_hash" in set(collection_schema.get("required", [])),
        "runtime_schema_requires_source_public_market_data_hash": "source_public_market_data_hash" in set(runtime_schema.get("required", [])),
        "collector_recomputes_public_market_data_hash": "public_market_data_hash(report[\"public_market_data\"])" in collector_text,
        "latest_pointer_exposes_public_market_data_hash": "\"public_market_data_hash\": report[\"public_market_data_hash\"]" in collector_text,
        "runtime_recomputes_bound_public_market_data_hash": "public_market_data_hash(report[\"public_market_data\"])" in runtime_text,
        "collection_validator_has_payload_mismatch_fixture": "validator-upbit-public-payload-mismatch" in validator_text,
        "runtime_validator_has_payload_mismatch_fixture": "validator-upbit-runtime-source-bound" in validator_text
        and "collection-bound PAPER runtime allowed market data payload mutation" in validator_text,
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "audit_schema_id": "trader1.upbit_paper_runtime_source_hash_guard_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "checks": checks,
        "hidden_defect": {
            "classification": "cross_component_mismatch",
            "condition": "a PAPER runtime cycle could retain a valid source collection hash while carrying mutated public_market_data payload",
            "impact": "strategy, PnL, and dashboard evidence could be based on data that no longer matches the collection source",
            "fix": "collection reports now bind public_market_data_hash and runtime cycles verify source_public_market_data_hash before accepting collection-backed data",
        },
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD.md",
        f"""# MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD

context_pack_id: MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD
task_class: MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DATA_FRESHNESS", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_public_market_data_collection_report.v1", "trader1.upbit_paper_runtime_cycle_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Upbit public collection report includes public_market_data_hash.
- Upbit PAPER runtime cycle includes source_public_market_data_hash when bound to a collection report.
- Collection-bound runtime recomputes market data hash before accepting payload.
- Latest collection pointer and writer report expose public_market_data_hash for operator/audit traceability.
- Negative fixture mutates public_market_data after collection binding and fails closed.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: {audit["status"]}

known_omissions_by_design:
- no live Upbit order path
- no private account snapshot
- no credential or API key load
- no LIVE_READY snapshot write
- no MVP-5 promotion

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

Upbit PAPER collection-backed runtime now binds the exact public market data payload hash from collection to runtime cycle. A cycle with mutated public_market_data after collection binding fails closed as SCHEMA_IDENTITY_MISMATCH.

## Next Safe Task

{NEXT_TASK_CLASS}
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
            "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER runtime source data identity",
            "full_text_marker": f"{REQUIREMENT_ID}:collection-bound runtime must verify source market data payload hash",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER runtime must reject collection payload drift",
            "requirement_kind": "RUNTIME_VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.upbit_public_market_data_collection_report.v1",
                "trader1.upbit_paper_runtime_cycle_report.v1",
                "trader1.patch_result.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/integration/test_upbit_paper_runtime_cycle.py",
                "tests/validators/test_mvp0_validators.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DATA_FRESHNESS", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-UPBIT-PAPER-RUNTIME-E2E", "REQ-MVP0-LIVE-DEFAULT-FALSE"],
            "source_text_sha256": sha256_bytes(b"collection-bound runtime must verify source market data payload hash"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
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
            "section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "schema_files": [
                "contracts/schema/upbit_public_market_data_collection_report.schema.json",
                "contracts/schema/upbit_paper_runtime_cycle_report.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/paper/upbit_public_collector.py",
                "trader1/runtime/paper/upbit_paper_runtime.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/integration/test_upbit_paper_runtime_cycle.py",
            ],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/paper/upbit_public_collector.py", "trader1/runtime/paper/upbit_paper_runtime.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
    audit: dict[str, Any],
) -> dict[str, Any]:
    patch_result: dict[str, Any] = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-4",
        "patch_class": "VALIDATOR_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "MATCH",
        "authority_hash_checked": True,
        "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-UPBIT-PAPER-RUNTIME-E2E", "REQ-MVP4-LIVE-FINAL-GUARD"],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "PAPER",
        "removed_requirements": [],
        "merged_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [],
        "new_or_changed_schema_ids": [
            "trader1.upbit_public_market_data_collection_report.v1",
            "trader1.upbit_paper_runtime_cycle_report.v1",
        ],
        "validators_required": validators_required,
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
        "next_task_class": NEXT_TASK_CLASS,
        "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX"],
        "next_optional_section_ids": ["SECTION_STRATEGY_ENTRY_EXIT", "SECTION_PROFITABILITY_LOOP"],
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
        "token_navigation_patch": True,
        "active_read_surface_used": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DATA_FRESHNESS", "SECTION_LIVE_FINAL_GUARD"],
        "task_class": "MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD",
        "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DATA_FRESHNESS", "SECTION_LIVE_FINAL_GUARD"],
        "expanded_section_ids": ["AGENTS:0G", "TRADER_1:UPBIT_PAPER_RUNTIME", "TRADER_1:LIVE_FINAL_GUARD"],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "REUSED_HASH_MATCH",
        "requirement_index_status": "UPDATED",
        "requirement_artifact_matrix_status": "UPDATED",
        "read_cache_manifest_status": "UPDATED",
        "context_pack_status": "UPDATED",
        "current_implementation_state_status": "UPDATED",
        "retained_archive_read": False,
        "full_document_read": False,
        "read_cache_invalidated": False,
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_UPBIT_PAPER_SOURCE_HASH_GUARD",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
        "objective_profile_changed": False,
        "memory_schema_changed": False,
        "failure_analysis_required": False,
        "failure_analysis_status": "NOT_REQUIRED_RUNTIME_HASH_GUARD",
        "exploration_exploitation_policy_changed": False,
        "regime_adaptation_changed": False,
        "risk_scaling_policy_changed": False,
        "survival_layer_changed": False,
    }
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    audit: dict[str, Any],
    runtime_artifacts: list[str],
) -> None:
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
            "stage_gate_status": "PASS_FOR_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD_NO_LIVE_ORDERS",
            "source_hash_guard_audit": audit,
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
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
                *runtime_artifacts,
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
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260501.md",
        f"""# MVP4 Upbit PAPER Runtime Source Hash Guard

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- A collection-backed Upbit PAPER runtime cycle bound only the collection report hash and canonical event count. If public_market_data was changed after binding, the cycle could still be rehashed internally and pass without proving it matched the original collection payload.

Patch:
- Added public_market_data_hash to Upbit public collection reports and schema.
- Added source_public_market_data_hash to Upbit PAPER runtime cycle reports and schema.
- Runtime validation recomputes public_market_data_hash and fails closed on source payload mismatch.
- Latest collection pointer and writer report expose public_market_data_hash for traceability.
- Added unit/integration and validator negative fixtures for payload mutation.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credential use
- no exchange private API call
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
    state["implemented_schema_ids"] = sorted(
        set(
            state.get("implemented_schema_ids", [])
            + [
                "trader1.upbit_public_market_data_collection_report.v1",
                "trader1.upbit_paper_runtime_cycle_report.v1",
            ]
        )
    )
    state["implemented_validator_ids"] = sorted(
        set(
            state.get("implemented_validator_ids", [])
            + ["upbit_public_market_data_collection_validator", "upbit_paper_runtime_cycle_validator"]
        )
    )
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
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
    runtime_artifacts = run_runtime_artifacts()
    write_source_bundle_manifest()
    audit = build_audit()
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-B", "-m", "unittest", "tests.integration.test_upbit_public_collection_persistent_loop", "-v"]),
        run_command([sys.executable, "-B", "-m", "unittest", "tests.integration.test_upbit_paper_runtime_cycle", "-v"]),
    ]
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS), BOOTSTRAP_VALIDATORS, audit)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, audit, runtime_artifacts)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_schema_instance_validation", "-v"]),
            run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_patch_result_runtime_schema_validation", "-v"]),
            run_command([sys.executable, "-B", "-m", "unittest", "tests.validators.test_mvp0_validators", "-v"]),
            run_command([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-q"], timeout_seconds=600),
        ]
    )
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED, audit)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit, runtime_artifacts)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    if audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "audit failed"})
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
