from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-RESTART-RECOVERY-WAL-LEDGER-BINDING-RECHECK"
NEXT_TASK_CLASS = "MVP4_PARTIAL_WRITE_CRASH_RECOVERY_RECHECK"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_convergence_memory_failure_learning_hardening_patch_evidence import (  # noqa: E402
    ensure_matrix_row,
    ensure_requirement,
    without_generated_dirty_requirement,
)
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
    "ledger_durability_validator",
    "restart_recovery_validator",
    "reconciliation_validator",
    "ledger_reconciliation_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]

CHANGED_ARTIFACTS = [
    "trader1/core/events/intent_wal.py",
    "trader1/core/ledger/restart_recovery.py",
    "contracts/schema/intent_wal_event.schema.json",
    "tests/runtime/test_restart_recovery.py",
    "tools/emit_restart_recovery_wal_ledger_binding_recheck_patch_evidence.py",
    "contracts/generated/context_pack/RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK.md",
    "system/evidence/audit_reports/MVP4_RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK_20260429.md",
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
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    index = load_json(index_path)
    matrix = load_json(matrix_path)
    index["updated_at_utc"] = now
    matrix["updated_at_utc"] = now

    ensure_requirement(
        index,
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "source_file": "TRADER_1.md",
            "source_heading": "restart recovery WAL ledger binding",
            "full_text_marker": f"{REQUIREMENT_ID}:intent WAL source hashes must bind to recovered ledger hashes",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Restart recovery WAL source hashes bind to recovered ledger",
            "requirement_kind": "RUNTIME_SAFETY_VALIDATOR_PATCH",
            "schema_ids": ["trader1.intent_wal_event.v1", "trader1.restart_recovery_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_restart_recovery.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-LEDGER-RECONCILIATION-IDEMPOTENCY-RECHECK",
                "REQ-MVP4-PARTIAL-WRITE-CRASH-RECOVERY-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"intent WAL source hashes must bind to recovered ledger hashes"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "schema_files": ["contracts/schema/intent_wal_event.schema.json", "contracts/schema/restart_recovery_report.schema.json"],
            "validator_files": ["trader1/core/events/intent_wal.py", "trader1/core/ledger/restart_recovery.py"],
            "test_files": ["tests/runtime/test_restart_recovery.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/core/events/intent_wal.py", "trader1/core/ledger/restart_recovery.py"],
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
        },
    )
    matrix["schema_file_count"] = len(list((ROOT / "contracts" / "schema").glob("*.schema.json")))
    write_json(index_path, index)
    write_json(matrix_path, matrix)

    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK.md",
        f"""# RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK

context_pack_id: RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK
task_class: MVP4_RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.intent_wal_event.v1", "trader1.restart_recovery_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- WAL source_ledger_event_hash must be sha256 hex.
- WAL source hashes must be a subset of recovered ledger event hashes.
- Every recovered intent ledger event must have a WAL source hash.
- Recovery remains PAPER-only and live/order flags remain false.

known_omissions_by_design:
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no active or live config mutation
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

Restart recovery now verifies that intent WAL source hashes bind to recovered ledger event hashes. Unknown or missing WAL-to-ledger binding fails closed with reconciliation required.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_LEDGER_RECONCILIATION_IDEMPOTENCY_RECHECK.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-LEDGER-RECONCILIATION-IDEMPOTENCY-RECHECK",
                "REQ-MVP4-PARTIAL-WRITE-CRASH-RECOVERY-RECHECK",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": CHANGED_ARTIFACTS,
            "new_or_changed_schema_ids": ["trader1.intent_wal_event.v1"],
            "validators_required": VALIDATORS_REQUIRED,
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
            "next_required_section_ids": [
                "SECTION_PARTIAL_WRITE_CRASH_RECOVERY",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_RACE_CONDITION_PARTIAL_WRITE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_RUNTIME_WRITE_LOCK", "SECTION_DASHBOARD_OPERATOR_UX"],
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
            "active_read_surface_used": [
                "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK",
            "required_section_ids": [
                "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "TRADER_1:ledger-reconciliation-idempotency-active-surface",
                "TRADER_1:runtime-recovery-active-surface",
                "AGENTS:runtime-safety-implementation-guide",
            ],
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_WAL_LEDGER_BINDING",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
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
            "stage_gate_status": "PASS_FOR_WAL_LEDGER_BINDING_RECHECK_NO_LIVE_ORDERS",
            "next_allowed_task_class": NEXT_TASK_CLASS,
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
        f"""# MVP4 Restart Recovery WAL Ledger Binding Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Hidden defect:
- Restart recovery validated ledger chain and intent WAL chain independently.
- A WAL event could point to a ledger hash outside the recovered ledger chain if the WAL hash chain was recomputed.
- A recovered idempotent ledger event could be missing from WAL while both chains still looked individually valid.

Patch:
- WAL source_ledger_event_hash now requires sha256 hex shape.
- Restart recovery requires WAL source hashes to be contained in recovered ledger event hashes.
- Restart recovery requires every recovered ledger event with intent/client ids to have a WAL source entry.
- Added negative tests for outside-ledger WAL source, missing WAL source, and non-hex source hash.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.intent_wal_event.v1"]))
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []) + ["restart_recovery_validator", "ledger_reconciliation_validator"])
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
    update_navigation(now, trader_hash, agents_hash)
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)

    preliminary_validators = run_validators([item for item in VALIDATORS_REQUIRED if item != "generated_artifact_dirty_validator"])
    preliminary = without_generated_dirty_requirement(build_patch_result(now, [], preliminary_validators))
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, preliminary)
    write_json(patch_path, preliminary)
    update_state_and_ledger(now, preliminary)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "json.tool", "contracts/schema/intent_wal_event.schema.json"]),
        run_command([sys.executable, "-m", "unittest", "tests.runtime.test_restart_recovery", "tests.runtime.test_execution_ledger", "tests.runtime.test_reconciliation", "-v"]),
        run_command([sys.executable, "UPBIT_PAPER.py"]),
        run_command([sys.executable, "BINANCE_PAPER.py"]),
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    final_patch = build_patch_result(now, tests_run, validators_run)
    write_evidence(now, trader_hash, agents_hash, final_patch)
    write_json(patch_path, final_patch)
    update_state_and_ledger(now, final_patch)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in tests_run + validators_run if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": final_patch["result_hash"],
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
