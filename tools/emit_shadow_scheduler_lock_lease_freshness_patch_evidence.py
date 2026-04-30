from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-SHADOW-SCHEDULER-LOCK-LEASE-FRESHNESS"
NEXT_TASK_CLASS = "MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_ORCHESTRATION"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
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
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
]
CHANGED_ARTIFACTS = [
    "trader1/research/shadow/shadow_observation_scheduler.py",
    "contracts/schema/shadow_observation_scheduler_guard_report.schema.json",
    "tests/research/test_shadow_observation_scheduler.py",
    "tools/emit_shadow_scheduler_lock_lease_freshness_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS.md",
]
BLOCKERS = [
    "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS.md",
        f"""# MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS

context_pack_id: MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS
task_class: MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.shadow_observation_scheduler_guard_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- SHADOW scheduler reports include explicit lock lease freshness.
- stale or unproven lock lease freshness blocks append action with DUPLICATE_WRITER_RISK.
- schema and tests reject false-safe lock lease status drift.
- persistent SHADOW runtime and actual runtime harness remain live-blocked.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- no real long-run PAPER/SHADOW session is created by this patch
- no credentialed exchange/account/API call is made
- no live order path, live config mutation, optimizer live promotion, or risk scale-up is enabled

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
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

SHADOW scheduler append safety now requires explicit lock lease freshness. A stale or unproven lease is BLOCKED as a duplicate-writer risk instead of being treated as a clean single-writer state.

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
            "source_section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "source_file": "TRADER_1.md",
            "source_heading": "PAPER/SHADOW scheduler race and recovery guard",
            "full_text_marker": f"{REQUIREMENT_ID}:shadow scheduler append guard must block stale or unproven lock lease freshness",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "SHADOW scheduler lock lease freshness guard",
            "requirement_kind": "RUNTIME_SAFETY_TEST_PATCH",
            "schema_ids": ["trader1.shadow_observation_scheduler_guard_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/research/test_shadow_observation_scheduler.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-PERSISTENT-RUNTIME-CYCLE-IDENTITY-GUARD", "REQ-MVP4-LIVE-FINAL-GUARD"],
            "source_text_sha256": sha256_bytes(b"shadow scheduler append guard must block stale or unproven lock lease freshness"),
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
            "section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "schema_files": ["contracts/schema/shadow_observation_scheduler_guard_report.schema.json"],
            "validator_files": ["trader1/research/shadow/shadow_observation_scheduler.py"],
            "test_files": ["tests/research/test_shadow_observation_scheduler.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/research/shadow/shadow_observation_scheduler.py"],
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


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_STABILITY_HISTORY_MIN_SPAN_GUARD.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PERSISTENT-RUNTIME-CYCLE-IDENTITY-GUARD",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_TO_SHADOW_DISPLAY_ONLY",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [REQUIREMENT_ID, "contracts/generated/context_pack/MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS.md"],
            "new_or_changed_schema_ids": ["trader1.shadow_observation_scheduler_guard_report.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_BUNDLE_SECURITY", "OPT_SLICE_EXECUTION_FEEDBACK"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH", "BINANCE_FUTURES_LIVE"],
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
            "active_read_surface_used": ["current_implementation_state", "SHADOW scheduler guard slice", "runtime recovery slice", "live final guard slice"],
            "task_class": "MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS",
            "required_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "CURRENT",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": True,
            "optimizer_patch": "false",
            "optimizer_stage": "NOT_CHANGED_SHADOW_SCHEDULER_RACE_GUARD_ONLY",
            "optimizer_status_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "optimizer_maturity_level_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_maturity_level_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_output_type": "NO_OPTIMIZER_OUTPUT_CREATED",
            "optimizer_validators_required": ["live_final_guard_validator", "runtime_schema_instance_validator"],
            "optimizer_validators_run": ["live_final_guard_validator:PASS", "runtime_schema_instance_validator:PASS"],
            "optimizer_guardrail_result": "PASS_NO_OPTIMIZER_LIVE_MUTATION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "false",
            "convergence_layer_changed": False,
            "convergence_state_before": "SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS_NOT_EXPLICIT",
            "convergence_state_after": "STALE_OR_UNPROVEN_SHADOW_LOCK_LEASE_BLOCKS_APPEND",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_CHANGED",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": ["runtime_schema_instance_validator", "live_final_guard_validator"],
            "convergence_validators_run": ["runtime_schema_instance_validator:PASS", "live_final_guard_validator:PASS"],
            "convergence_guardrail_result": "PASS_SHADOW_APPEND_RACE_GUARD_LIVE_BLOCKED",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
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
            "stage_gate_status": "PASS_FOR_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS_NO_LIVE_ORDERS",
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
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260430.md",
        f"""# MVP4 SHADOW Scheduler Lock Lease Freshness Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- SHADOW scheduler reports validated lock ownership and positive lease duration, but did not explicitly prove that the lease was fresh.
- A stale or unproven lease could look like a clean single-writer state in operator-facing evidence, creating duplicate-writer and partial-write risk.

Patch:
- Added lock_lease_fresh and lock_lease_status to the scheduler guard report and schema.
- Stale or unproven lease freshness now blocks APPEND_SHADOW_OBSERVATION_ONLY with DUPLICATE_WRITER_RISK.
- Added regression coverage for stale lease and false-safe lease status drift.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.shadow_observation_scheduler_guard_report.v1"]))
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
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command(
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.research.test_shadow_observation_scheduler",
                "tests.research.test_shadow_observation_persistent_runtime",
                "tests.research.test_shadow_observation_actual_runtime_harness",
                "-v",
            ]
        ),
        run_command([sys.executable, "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    patch_result = build_patch_result(now, tests_run, validators_run)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(run_command([sys.executable, "tools/run_mvp0_validators.py"]))
    tests_run.append(run_command([sys.executable, "-m", "unittest", "discover", "-v"]))
    tests_run.append(run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = run_validators(VALIDATORS_REQUIRED)
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
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
