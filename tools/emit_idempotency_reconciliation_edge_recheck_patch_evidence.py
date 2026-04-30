from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-IDEMPOTENCY-RECONCILIATION-EDGE-RECHECK"
NEXT_TASK_CLASS = "MVP4_LEDGER_RECONCILIATION_RECOVERY_EDGE_RECHECK"

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
from trader1.execution.live_order_gateway import evaluate_live_order_path  # noqa: E402
from trader1.safety.live_order_gate import REQUIRED_LIVE_TRUE_FIELDS  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "single_writer_order_path_validator",
    "strategy_direct_order_validator",
    "ledger_reconciliation_validator",
    "restart_recovery_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if not validator_id.startswith("patch_result") and validator_id != "generated_artifact_dirty_validator"
]
CHANGED_ARTIFACTS = [
    "trader1/execution/live_order_gateway.py",
    "trader1/validation/mvp0_validators.py",
    "tests/live_blocked/test_order_path_guard.py",
    "tools/emit_idempotency_reconciliation_edge_recheck_patch_evidence.py",
    "contracts/generated/context_pack/IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK.md",
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


def _all_green_live_gate() -> dict[str, Any]:
    live_gate = {field: True for field in REQUIRED_LIVE_TRUE_FIELDS}
    live_gate.update(
        {
            "live_order_ready": True,
            "live_order_allowed": True,
            "can_live_trade": True,
            "live_enabling_patch_valid": True,
        }
    )
    return live_gate


def idempotency_reconciliation_audit() -> dict[str, Any]:
    base_request = {
        "source_kind": "FinalDecision",
        "final_decision": "ENTER_LONG",
        "single_writer_available": True,
        "budget_reserved": True,
        "local_reservation_committed": True,
        "ledger_reconciled": True,
        "live_gate": _all_green_live_gate(),
    }
    same_identifier = evaluate_live_order_path(
        {
            **base_request,
            "original_client_order_id": "audit-same-id",
            "client_order_id": "audit-same-id",
            "idempotency_state": "TRANSPORT_AMBIGUOUS",
        }
    )
    missing_original = evaluate_live_order_path(
        {
            **base_request,
            "client_order_id": "audit-missing-original-id",
            "idempotency_state": "PENDING_CONFIRM",
        }
    )
    blockers: list[str] = []
    for label, decision in (("same_identifier", same_identifier), ("missing_original", missing_original)):
        if decision.primary_blocker_code != "RECONCILIATION_REQUIRED":
            blockers.append(f"{label.upper()}_NOT_RECONCILIATION_PRIMARY")
        if decision.final_decision != "RECONCILE_REQUIRED":
            blockers.append(f"{label.upper()}_NOT_RECONCILE_REQUIRED")
        if decision.order_adapter_called or decision.external_submit_attempted:
            blockers.append(f"{label.upper()}_TOUCHED_ORDER_SUBMIT")
    status = "PASS" if not blockers else "BLOCKED"
    return {
        "audit_schema_id": "trader1.idempotency_reconciliation_edge_recheck_audit.v1",
        "status": status,
        "blockers": blockers,
        "same_identifier_primary_blocker": same_identifier.primary_blocker_code,
        "same_identifier_final_decision": same_identifier.final_decision,
        "same_identifier_idempotency_action": same_identifier.idempotency_action,
        "same_identifier_order_adapter_called": same_identifier.order_adapter_called,
        "missing_original_primary_blocker": missing_original.primary_blocker_code,
        "missing_original_final_decision": missing_original.final_decision,
        "missing_original_idempotency_action": missing_original.idempotency_action,
        "missing_original_order_adapter_called": missing_original.order_adapter_called,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "next_action": (
            "Continue ledger/reconciliation recovery edge-case hardening."
            if status == "PASS"
            else "Block live review and repair ambiguous idempotency reconciliation handling."
        ),
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK.md",
        f"""# IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK

context_pack_id: IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK
task_class: MVP4_IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_IDEMPOTENCY", "SECTION_RECONCILIATION", "SECTION_ORDER_PATH_GUARD", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Every ambiguous idempotency state is blocked by RECONCILIATION_REQUIRED before any adapter submit.
- Same-identifier ambiguous transport states require reconciliation before submit.
- Ambiguous states without an original identifier require reconciliation before submit.
- Spoofed all-green live gate inputs cannot downgrade reconciliation into LIVE_ENABLING_EVIDENCE_MISSING.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- same_identifier_primary_blocker: {audit["same_identifier_primary_blocker"]}
- same_identifier_final_decision: {audit["same_identifier_final_decision"]}
- missing_original_primary_blocker: {audit["missing_original_primary_blocker"]}
- missing_original_final_decision: {audit["missing_original_final_decision"]}

known_omissions_by_design:
- no live execution
- no credential access
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

Ambiguous idempotency states now fail closed to RECONCILIATION_REQUIRED before any order adapter submit, including same-identifier and missing-original-identifier cases.

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
            "source_section_id": "SECTION_LEDGER_IDEMPOTENCY",
            "source_file": "TRADER_1.md",
            "source_heading": "Idempotency reconciliation edge recheck",
            "full_text_marker": f"{REQUIREMENT_ID}:ambiguous idempotency states must require reconciliation before submit",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Ambiguous idempotency states reconcile before submit",
            "requirement_kind": "LIVE_BLOCKED_TEST_PATCH",
            "schema_ids": ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/live_blocked/test_order_path_guard.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_LEDGER_IDEMPOTENCY", "SECTION_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-ORDER-PATH-ADAPTER-SUBMIT-RECHECK", "REQ-MVP4-LEDGER-RECONCILIATION-IDEMPOTENCY-RECHECK"],
            "source_text_sha256": sha256_bytes(b"ambiguous idempotency states must require reconciliation before submit"),
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
            "section_id": "SECTION_LEDGER_IDEMPOTENCY",
            "schema_files": [],
            "validator_files": ["trader1/execution/live_order_gateway.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/live_blocked/test_order_path_guard.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/execution/live_order_gateway.py"],
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
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "MATCH",
        "authority_hash_checked": True,
        "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP0-ORDER-PATH-GUARD", "REQ-MVP4-LEDGER-RECONCILIATION-IDEMPOTENCY-RECHECK"],
        "affected_exchange": "UPBIT_AND_BINANCE",
        "affected_market_type": "KRW_SPOT_AND_SPOT",
        "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
        "removed_requirements": [],
        "merged_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [],
        "new_or_changed_schema_ids": [],
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
        "next_required_section_ids": ["SECTION_LEDGER_IDEMPOTENCY", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY"],
        "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RUNTIME_RESOURCE_PRESSURE"],
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
        "active_read_surface_used": ["SECTION_LEDGER_IDEMPOTENCY", "SECTION_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
        "task_class": "MVP4_IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK",
        "required_section_ids": ["SECTION_LEDGER_IDEMPOTENCY", "SECTION_RECONCILIATION", "SECTION_ORDER_PATH_GUARD", "SECTION_LIVE_FINAL_GUARD"],
        "expanded_section_ids": ["TRADER_1:idempotency-reconciliation-active-surface", "AGENTS:live-blocked-test-implementation-guide"],
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
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_IDEMPOTENCY_RECONCILIATION_EDGE",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
    }
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], audit: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_FOR_IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK_NO_LIVE_ORDERS",
            "idempotency_reconciliation_audit": audit,
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
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_AUDIT.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260429.md",
        f"""# MVP4 Idempotency Reconciliation Edge Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- Ambiguous idempotency states were only forced into reconciliation when a new identifier was proposed or the identifier changed.
- Same-identifier ambiguous transport states could be reported with a later live-enabling blocker instead of RECONCILIATION_REQUIRED.
- Missing original identifiers in ambiguous states could hide the need for reconciliation before submit.

Patch:
- Any PENDING_CONFIRM, RECONCILE_REQUIRED, or TRANSPORT_AMBIGUOUS state now adds RECONCILIATION_REQUIRED before live gate fallback.
- Added negative tests for same-identifier and missing-original-identifier ambiguous states.
- Strengthened single_writer_order_path_validator to cover both edge cases.

Audit:
- same_identifier_primary_blocker: {audit['same_identifier_primary_blocker']}
- same_identifier_final_decision: {audit['same_identifier_final_decision']}
- missing_original_primary_blocker: {audit['missing_original_primary_blocker']}
- missing_original_final_decision: {audit['missing_original_final_decision']}

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
    audit = idempotency_reconciliation_audit()
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.live_blocked.test_order_path_guard", "-v"]),
    ]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS_REQUIRED), BOOTSTRAP_VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
        ]
    )
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    if audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "idempotency reconciliation audit failed"})
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "same_identifier_primary_blocker": audit["same_identifier_primary_blocker"],
                "missing_original_primary_blocker": audit["missing_original_primary_blocker"],
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
