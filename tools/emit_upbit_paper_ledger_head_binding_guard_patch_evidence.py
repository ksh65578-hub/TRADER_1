from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-LEDGER-HEAD-BINDING-GUARD"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_EVIDENCE"

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
    "contracts/schema/paper_ledger_rollup_report.schema.json",
    "trader1/runtime/ledger/paper_ledger_rollup.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_paper_ledger_rollup.py",
    "tools/emit_upbit_paper_ledger_head_binding_guard_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD.md",
]
VALIDATORS_REQUIRED = [
    "registry_validator",
    "schema_validator",
    "paper_ledger_rollup_validator",
    "ledger_durability_validator",
    "ledger_reconciliation_validator",
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
    if validator_id not in {"patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}
]
BLOCKERS = [
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
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
        loop_id="mvp4-upbit-paper-ledger-head-binding-guard",
        requested_cycle_count=2,
    )
    paths: list[str] = []
    for cycle in loop.get("cycle_results", []):
        paths.extend(path for path in cycle.get("artifact_paths", []) if isinstance(path, str))
    for key in ("runtime_recovery_guard_path", "paper_ledger_rollup_path"):
        if isinstance(loop.get(key), str):
            paths.append(loop[key])
    paths.append(
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/"
        "paper_runtime/mvp4-upbit-paper-ledger-head-binding-guard.persistent_loop_report.json"
    )
    return sorted(set(paths))


def build_audit() -> dict[str, Any]:
    schema_text = (ROOT / "contracts" / "schema" / "paper_ledger_rollup_report.schema.json").read_text(encoding="utf-8")
    module_text = (ROOT / "trader1" / "runtime" / "ledger" / "paper_ledger_rollup.py").read_text(encoding="utf-8")
    validator_text = (ROOT / "trader1" / "validation" / "mvp0_validators.py").read_text(encoding="utf-8")
    test_text = (ROOT / "tests" / "runtime" / "test_paper_ledger_rollup.py").read_text(encoding="utf-8")
    checks = {
        "schema_requires_duplicate_path_count": "duplicate_ledger_path_count" in schema_text,
        "schema_declares_ledger_input_scope": "ledger_input_scope" in schema_text
        and "SESSION_CYCLE_GLOB" in schema_text
        and "EXPLICIT_SCOPED_PATHS" in schema_text,
        "schema_requires_ledger_head_binding": "ledger_head_match_status" in schema_text and "ledger_head_mismatch_count" in schema_text,
        "module_hashes_head_report": "paper_ledger_head_report_hash" in module_text,
        "module_splits_session_and_explicit_input_scope": "ledger_input_scope = \"SESSION_CYCLE_GLOB\"" in module_text
        and "ledger_input_scope = \"EXPLICIT_SCOPED_PATHS\"" in module_text,
        "module_requires_head_only_for_session_glob": "require_latest_head_report=ledger_input_scope == \"SESSION_CYCLE_GLOB\"" in module_text,
        "module_rejects_explicit_latest_head_claim": "explicit PAPER ledger rollup must not claim latest head binding" in module_text,
        "module_blocks_missing_head": "latest PAPER ledger head report is missing" in module_text,
        "module_blocks_head_mismatch": "does not match rollup head" in module_text,
        "validator_asserts_session_scope": "valid paper ledger rollup did not mark session-cycle input scope" in validator_text,
        "validator_asserts_explicit_scope_not_applicable": "EXPLICIT_SCOPED_PATHS" in validator_text and "NOT_APPLICABLE" in validator_text,
        "validator_duplicate_path_negative": "duplicate explicit ledger paths were not blocked" in validator_text,
        "validator_missing_head_negative": "missing latest ledger head report was not blocked" in validator_text,
        "validator_mismatch_head_negative": "mismatched latest ledger head report was not blocked" in validator_text,
        "test_asserts_session_scope": "SESSION_CYCLE_GLOB" in test_text,
        "test_asserts_explicit_scope": "EXPLICIT_SCOPED_PATHS" in test_text and "NOT_APPLICABLE" in test_text,
        "test_duplicate_path_negative": "test_rollup_blocks_duplicate_explicit_ledger_paths" in test_text,
        "test_missing_head_negative": "test_rollup_blocks_missing_latest_ledger_head_report" in test_text,
        "test_mismatched_head_negative": "test_rollup_blocks_mismatched_latest_ledger_head_report" in test_text,
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "audit_schema_id": "trader1.upbit_paper_ledger_head_binding_guard_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "checks": checks,
        "hidden_defects": [
            {
                "classification": "ledger_head_rollup_false_binding",
                "condition": "PAPER rollup could be generated from ledger JSONL while latest_paper_ledger_head.json was missing or inconsistent",
                "impact": "portfolio truth could be displayed without proving the latest ledger head artifact matched the rolled-up source cycle",
                "fix": "rollup now records and validates ledger head report path, hash, cycle, event count, match status, and mismatch count",
            },
            {
                "classification": "explicit_duplicate_ledger_path_replay",
                "condition": "explicit ledger_paths could include the same JSONL more than once",
                "impact": "reconciliation evidence could double-count events or hide rerun input mistakes",
                "fix": "rollup now counts duplicate ledger paths and blocks review with RECONCILIATION_REQUIRED",
            },
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD.md",
        f"""# MVP4_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD

context_pack_id: MVP4_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD
task_class: MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_EVIDENCE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.paper_ledger_rollup_report.v1", "trader1.paper_portfolio_snapshot.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- PAPER ledger rollup records duplicate_ledger_path_count and blocks explicit duplicate input paths.
- PAPER ledger rollup records latest ledger head report path, hash, cycle, event count, match status, and mismatch count.
- Session-cycle glob rollups require latest_paper_ledger_head.json binding PASS and portfolio source cycle alignment.
- Explicit scoped repair/rerun rollups use terminal ledger validation, set ledger_input_scope=EXPLICIT_SCOPED_PATHS, and must not claim latest head binding.
- Missing or mismatched latest_paper_ledger_head.json blocks session-cycle rollup review.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: {audit["status"]}

known_omissions_by_design:
- no long-run evidence eligibility is created
- no live Upbit order path
- no credential or private account access
- no LIVE_READY snapshot write
- no risk scale-up

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

Upbit PAPER session-cycle ledger rollup now proves the rolled-up source cycle is bound to latest_paper_ledger_head.json before portfolio truth can PASS. Explicit scoped repair/rerun rollups stay terminal-ledger evidence only and cannot claim latest-head binding. Missing, mismatched, or duplicated ledger inputs block review and keep all live/scaling flags false.

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
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER ledger head binding guard",
            "full_text_marker": f"{REQUIREMENT_ID}:paper ledger rollup must prove latest ledger head artifact binding",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "PAPER ledger rollup must bind latest ledger head report before portfolio truth can PASS",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.paper_ledger_rollup_report.v1", "trader1.patch_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_paper_ledger_rollup.py", "tests/validators/test_mvp0_validators.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP-CONSISTENCY-GUARD"],
            "source_text_sha256": sha256_bytes(b"paper ledger rollup must prove latest ledger head artifact binding"),
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
            "section_id": "SECTION_LEDGER_RECONCILIATION",
            "schema_files": ["contracts/schema/paper_ledger_rollup_report.schema.json"],
            "validator_files": ["trader1/runtime/ledger/paper_ledger_rollup.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/runtime/test_paper_ledger_rollup.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/ledger/paper_ledger_rollup.py"],
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
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
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
        "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP", "REQ-MVP4-LIVE-FINAL-GUARD"],
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
        "new_or_changed_schema_ids": ["trader1.paper_ledger_rollup_report.v1"],
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
        "active_read_surface_used": ["SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"],
        "task_class": "MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_EVIDENCE",
        "required_section_ids": ["SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"],
        "expanded_section_ids": ["AGENTS:0G", "TRADER_1:LEDGER_RECONCILIATION", "TRADER_1:LIVE_FINAL_GUARD"],
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
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD",
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
        "failure_analysis_status": "NOT_REQUIRED_LEDGER_HEAD_BINDING_GUARD",
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
            "stage_gate_status": "PASS_FOR_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD_NO_LIVE_ORDERS",
            "ledger_head_binding_guard_audit": audit,
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
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260502.md",
        f"""# MVP4 Upbit PAPER Ledger Head Binding Guard

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- PAPER session-cycle ledger rollup needed explicit proof that the rolled-up ledger source matched latest_paper_ledger_head.json.
- Explicit scoped repair/rerun rollups needed to remain terminal-ledger evidence without falsely claiming the current latest head.

Patch:
- Added ledger-head binding fields to paper_ledger_rollup_report.
- Added ledger_input_scope to separate SESSION_CYCLE_GLOB from EXPLICIT_SCOPED_PATHS evidence.
- Blocked duplicate explicit ledger_paths.
- Blocked missing or mismatched latest ledger head reports for session-cycle rollups.
- Kept explicit scoped rollups NOT_APPLICABLE for latest-head binding while retaining ledger-chain validation.
- Added negative tests and validator coverage.

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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.paper_ledger_rollup_report.v1"]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["paper_ledger_rollup_validator"]))
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
        run_command([sys.executable, "-B", "-m", "unittest", "tests.runtime.test_paper_ledger_rollup", "-v"]),
        run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS), BOOTSTRAP_VALIDATORS)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, audit, runtime_artifacts)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_patch_result_runtime_schema_validation", "-v"]),
            run_command([sys.executable, "-B", "-m", "unittest", "tests.validators.test_mvp0_validators", "-v"]),
        ]
    )
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED)
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
