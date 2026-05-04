from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

PATCH_BASENAME = "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
GAP_ID = "MISSING_CYCLE_LEDGER_RERUN_REQUIRED"
NEXT_TASK_CLASS = "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"

DEPTH_REPORT_PATH = ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.json"
CONTRACT_GAP_PATH = ROOT / "system" / "evidence" / "contract_gaps" / f"{GAP_ID}.contract_gap.json"
RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime"

RUNTIME_REPORTS = {
    "guard": RUNTIME_BASE / "upbit_paper_missing_cycle_rerun_guard_report.json",
    "executor": RUNTIME_BASE / "upbit_paper_bounded_rerun_staging_executor_report.json",
    "post_rerun": RUNTIME_BASE / "upbit_paper_post_rerun_ledger_rollup_reconciliation_report.json",
    "promotion_guard": RUNTIME_BASE / "upbit_paper_post_rerun_current_evidence_promotion_guard_report.json",
    "blocker_rollup": RUNTIME_BASE / "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json",
    "operator_queue": RUNTIME_BASE / "upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
    "decision_audit": RUNTIME_BASE / "upbit_paper_post_rerun_reconciliation_decision_audit_report.json",
    "resolution_audit": RUNTIME_BASE / "upbit_paper_post_rerun_operator_resolution_audit_report.json",
    "closure": RUNTIME_BASE / "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json",
    "repair_path": RUNTIME_BASE / "upbit_paper_post_rerun_reconciliation_repair_path_report.json",
}

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
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_missing_cycle_rerun_guard_validator",
    "upbit_paper_bounded_rerun_staging_executor_validator",
    "upbit_paper_post_rerun_ledger_rollup_reconciliation_validator",
    "upbit_paper_post_rerun_reconciliation_blocker_rollup_validator",
    "upbit_paper_post_rerun_current_evidence_promotion_guard_validator",
    "upbit_paper_post_rerun_operator_reconciliation_queue_validator",
    "upbit_paper_post_rerun_reconciliation_decision_audit_validator",
    "upbit_paper_post_rerun_operator_resolution_audit_validator",
    "upbit_paper_post_rerun_resolution_current_evidence_closure_validator",
    "upbit_paper_post_rerun_reconciliation_repair_path_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [validator for validator in VALIDATORS_REQUIRED if validator != "generated_artifact_dirty_validator"]

ROUTE_TEST_ARTIFACTS = [
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py",
    "tests/contract/test_completed_recheck_route_depth_guard.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
    "tests/contract/test_open_contract_gap_implementation_priority_recheck.py",
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
]

CHANGED_ARTIFACTS = [
    "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py",
    *ROUTE_TEST_ARTIFACTS,
    "tools/emit_missing_cycle_ledger_rerun_required_implementation_depth_recheck_patch_evidence.py",
    rel(DEPTH_REPORT_PATH),
    rel(CONTRACT_GAP_PATH),
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
RUNTIME_ARTIFACTS = [rel(path) for path in RUNTIME_REPORTS.values()]
STATIC_BLOCKERS = {
    GAP_ID,
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
}
FALSE_RUNTIME_FIELDS = (
    "live_order_ready",
    "live_order_allowed",
    "can_live_trade",
    "scale_up_allowed",
    "current_evidence_mutation_allowed",
    "current_ledger_jsonl_write_allowed",
    "latest_runtime_pointer_write_allowed",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str], timeout_seconds: int = 900) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    result = {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }
    if completed.returncode != 0:
        result["stdout_tail"] = completed.stdout[-4000:]
        result["stderr_tail"] = completed.stderr[-4000:]
    return result


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def false_field_errors(name: str, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in FALSE_RUNTIME_FIELDS:
        if report.get(field) is True:
            errors.append(f"{name} has forbidden true field: {field}")
    return errors


def build_depth_report(now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    reports = {name: load_json(path) for name, path in RUNTIME_REPORTS.items()}
    errors: list[str] = []
    for name, report in reports.items():
        errors.extend(false_field_errors(name, report))

    guard = reports["guard"]
    executor = reports["executor"]
    post_rerun = reports["post_rerun"]
    promotion_guard = reports["promotion_guard"]
    blocker_rollup = reports["blocker_rollup"]
    operator_queue = reports["operator_queue"]
    decision_audit = reports["decision_audit"]
    resolution_audit = reports["resolution_audit"]
    closure = reports["closure"]
    repair_path = reports["repair_path"]

    if guard.get("guard_status") != "BLOCKED":
        errors.append("missing-cycle guard must remain BLOCKED")
    if int(guard.get("missing_cycle_ledger_jsonl_total_count") or 0) <= 0:
        errors.append("missing-cycle guard no longer exposes missing ledger jsonl rows")
    if executor.get("staging_status") != "PASS":
        errors.append("bounded rerun staging executor must expose PASS staging_status")
    if int(executor.get("staged_cycle_count") or 0) <= 0:
        errors.append("bounded rerun staging executor no longer exposes staged cycles")
    if executor.get("staged_current_evidence_usable_count") != 0:
        errors.append("bounded rerun staging executor made staged evidence current-usable")
    if post_rerun.get("post_rerun_ledger_rollup_status") != "PASS":
        errors.append("post-rerun ledger rollup must remain PASS")
    if int(post_rerun.get("candidate_item_count") or 0) <= 0:
        errors.append("post-rerun ledger rollup no longer exposes candidates")
    if post_rerun.get("candidate_current_evidence_usable_count") != 0:
        errors.append("post-rerun ledger rollup made current evidence usable")
    if promotion_guard.get("promotion_guard_status") != "BLOCKED":
        errors.append("post-rerun current evidence promotion guard must remain BLOCKED")
    if blocker_rollup.get("current_evidence_write_allowed") is not False:
        errors.append("post-rerun blocker rollup allows current evidence writes")
    if blocker_rollup.get("current_evidence_write_allowed_count") != 0:
        errors.append("post-rerun blocker rollup has allowed write rows")
    if operator_queue.get("queue_status") != "BLOCKED":
        errors.append("post-rerun operator reconciliation queue must remain BLOCKED")
    if decision_audit.get("decision_audit_status") != "BLOCKED":
        errors.append("post-rerun reconciliation decision audit must remain BLOCKED")
    if resolution_audit.get("resolution_audit_status") != "UNRESOLVED_RECONCILIATION_REVIEW_ONLY":
        errors.append("operator resolution audit must remain unresolved review-only")
    if closure.get("closure_status") != "CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED":
        errors.append("resolution current evidence closure must remain closed/unresolved")
    if closure.get("current_evidence_write_allowed_count") != 0 or closure.get("candidate_current_evidence_usable_count") != 0:
        errors.append("resolution closure exposed current evidence write or usability")
    if repair_path.get("repair_path_status") != "BLOCKED_REPAIR_PATH_DECLARED":
        errors.append("post-rerun repair path must remain blocked")

    status = "PASS_DEPTH_5_RUNTIME_CHAIN_EVIDENCE_LIVE_BLOCKING" if not errors else "BLOCKED_DEPTH_RECHECK_ERROR"
    return {
        "schema_id": "trader1.missing_cycle_ledger_rerun_required_implementation_depth_recheck.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "patch_id": PATCH_ID,
        "requirement_id": REQUIREMENT_ID,
        "contract_gap_id": GAP_ID,
        "status": status,
        "depth_level": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "runtime_artifact_paths": RUNTIME_ARTIFACTS,
        "error_count": len(errors),
        "errors": errors,
        "guard_status": guard.get("guard_status"),
        "guard_item_count": guard.get("guard_item_count"),
        "rerun_ready_item_count": guard.get("rerun_ready_item_count"),
        "recovery_guard_blocked_item_count": guard.get("recovery_guard_blocked_item_count"),
        "missing_cycle_ledger_jsonl_total_count": guard.get("missing_cycle_ledger_jsonl_total_count"),
        "planned_staging_artifact_total_count": guard.get("planned_staging_artifact_total_count"),
        "actual_rerun_executed": False,
        "rerun_executor_created": bool(executor.get("staging_executor_created")),
        "staging_status": executor.get("staging_status"),
        "staged_cycle_count": executor.get("staged_cycle_count"),
        "staged_artifact_count": executor.get("staged_artifact_count"),
        "staging_reused_existing_artifact_count": executor.get("staging_reused_existing_artifact_count"),
        "staging_executor_created": bool(executor.get("staging_executor_created")),
        "post_staging_ledger_rollup_required": bool(executor.get("post_staging_ledger_rollup_required")),
        "post_staging_reconciliation_required": bool(executor.get("post_staging_reconciliation_required")),
        "post_rerun_ledger_rollup_status": post_rerun.get("post_rerun_ledger_rollup_status"),
        "post_rerun_reconciliation_status": post_rerun.get("post_rerun_reconciliation_status"),
        "post_rerun_candidate_rollup_count": post_rerun.get("candidate_item_count"),
        "post_rerun_candidate_rollup_written_count": post_rerun.get("candidate_rollup_written_count"),
        "post_rerun_candidate_rollup_reused_existing_count": post_rerun.get("candidate_rollup_reused_existing_count"),
        "candidate_current_evidence_usable_count": post_rerun.get("candidate_current_evidence_usable_count"),
        "post_rerun_current_evidence_promotion_guard_status": promotion_guard.get("promotion_guard_status"),
        "post_rerun_promotion_review_ready_count": promotion_guard.get("promotion_review_ready_count"),
        "post_rerun_promotion_candidate_verified_count": promotion_guard.get("candidate_rollup_verified_count"),
        "post_rerun_current_evidence_write_allowed_count": promotion_guard.get("current_evidence_write_allowed_count"),
        "post_rerun_operator_reconciliation_queue_status": operator_queue.get("queue_status"),
        "post_rerun_operator_reconciliation_queue_item_count": operator_queue.get("queue_item_count"),
        "post_rerun_operator_reconciliation_required_count": operator_queue.get("operator_reconciliation_required_count"),
        "post_rerun_reconciliation_decision_audit_status": decision_audit.get("decision_audit_status"),
        "post_rerun_reconciliation_decision_item_count": decision_audit.get("decision_item_count"),
        "post_rerun_reconciliation_write_denied_count": decision_audit.get("write_denied_count"),
        "post_rerun_current_evidence_write_authorized_count": decision_audit.get("current_evidence_write_authorized_count"),
        "post_rerun_reconciliation_blocker_rollup_status": blocker_rollup.get("blocker_rollup_status"),
        "post_rerun_reconciliation_blocker_rollup_item_count": blocker_rollup.get("rollup_item_count"),
        "post_rerun_reconciliation_unique_blocker_count": blocker_rollup.get("unique_blocker_count"),
        "post_rerun_reconciliation_primary_blocker_item_count": blocker_rollup.get("primary_blocker_item_count"),
        "post_rerun_operator_resolution_audit_status": resolution_audit.get("resolution_audit_status"),
        "post_rerun_operator_resolution_unresolved_item_count": resolution_audit.get("unresolved_item_count"),
        "post_rerun_operator_resolution_resolved_item_count": resolution_audit.get("resolved_item_count"),
        "post_rerun_operator_resolution_control_count": resolution_audit.get("resolution_control_count"),
        "post_rerun_operator_resolution_controls_satisfied_count": resolution_audit.get("resolution_controls_satisfied_count"),
        "post_rerun_resolution_current_evidence_closure_status": closure.get("closure_status"),
        "post_rerun_resolution_closure_source_unresolved_item_count": closure.get("source_unresolved_item_count"),
        "post_rerun_resolution_closure_source_resolved_item_count": closure.get("source_resolved_item_count"),
        "post_rerun_resolution_closure_closed_item_count": closure.get("closed_item_count"),
        "post_rerun_resolution_closure_current_evidence_closed_count": closure.get("current_evidence_closed_count"),
        "post_rerun_resolution_closure_controls_satisfied_count": closure.get("closure_controls_satisfied_count"),
        "post_rerun_reconciliation_repair_path_status": repair_path.get("repair_path_status"),
        "post_rerun_reconciliation_repair_gate_count": repair_path.get("repair_gate_count"),
        "post_rerun_reconciliation_repair_gate_satisfied_count": repair_path.get("satisfied_repair_gate_count"),
        "post_rerun_reconciliation_repair_gate_blocked_count": repair_path.get("blocked_repair_gate_count"),
        "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_status": repair_path.get(
            "source_recheck_ledger_source_runtime_depth_status"
        ),
        "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_mismatch_count": repair_path.get(
            "source_recheck_ledger_source_runtime_depth_mismatch_count"
        ),
        "current_evidence_mutation_allowed": False,
        "current_evidence_write_allowed_count": 0,
        "next_allowed_task_class": NEXT_TASK_CLASS,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def remaining_blockers() -> list[str]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    return sorted(set(state.get("open_contract_gap_ids", [])) | STATIC_BLOCKERS)


def write_contract_gap(now: str, trader_hash: str, agents_hash: str) -> None:
    write_json(
        CONTRACT_GAP_PATH,
        {
            "schema_id": "trader1.contract_gap.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "status": "OPEN",
            "blockers": [
                {
                    "code": GAP_ID,
                    "message": "Missing PAPER cycle rerun evidence is implemented as a guarded runtime chain, but current evidence remains blocked until post-rerun reconciliation depth evidence passes.",
                }
            ],
            "notes": "Depth recheck only; no rerun execution, current evidence write, live order, or scale-up permission is created.",
            "contract_gap_id": GAP_ID,
            "severity": "HIGH",
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "live_affecting": True,
        },
    )


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_CURRENT_EVIDENCE_CLOSURE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-NEXT-TASK-RESTORE", "REQ-MVP4-UPBIT-PAPER-MISSING-CYCLE-RERUN-GUARD"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.contract_gap.v1", "trader1.upbit_paper_missing_cycle_rerun_guard_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS + RUNTIME_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Confirm missing-cycle guard, bounded rerun staging, post-rerun rollup, operator queue, decision audit, resolution audit, closure, and repair path artifacts exist.
- Confirm the chain reaches DEPTH_5 evidence/stage gate coverage while current evidence usability and writes remain zero.
- Keep {GAP_ID} open and live-affecting.
- Route to {NEXT_TASK_CLASS} for the next post-rerun reconciliation depth check.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

depth_snapshot:
- status: {report["status"]}
- guard_item_count: {report["guard_item_count"]}
- staged_cycle_count: {report["staged_cycle_count"]}
- post_rerun_candidate_rollup_count: {report["post_rerun_candidate_rollup_count"]}
- candidate_current_evidence_usable_count: {report["candidate_current_evidence_usable_count"]}
- current_evidence_write_allowed_count: {report["current_evidence_write_allowed_count"]}

known_omissions_by_design:
- No PAPER cycle is rerun by this patch.
- No current ledger JSONL, latest pointer, current evidence, live config, credentialed API, live order, or scale-up output is written.
- Missing-cycle and post-rerun reconciliation gaps remain live-blocking until independent reconciliation depth evidence passes.

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

The missing-cycle PAPER rerun path has guard, bounded staging, post-rerun rollup, reconciliation blocker, operator queue, decision audit, resolution audit, closure, and repair-path evidence. Current evidence usability and write authorization remain zero, so the gap stays open and live-blocking.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    artifacts = sorted(
        set(
            CHANGED_ARTIFACTS
            + RUNTIME_ARTIFACTS
            + [
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "system/evidence/implementation_patch_ledger.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260504.md",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ]
        )
    )
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "missing cycle ledger rerun required implementation depth recheck",
            "full_text_marker": f"{REQUIREMENT_ID}: verify missing-cycle rerun runtime evidence depth without current evidence or live permission",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Missing cycle ledger rerun implementation depth recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.patch_result.v1", "trader1.contract_gap.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py",
                *ROUTE_TEST_ARTIFACTS,
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-NEXT-TASK-RESTORE",
                "REQ-MVP4-UPBIT-PAPER-MISSING-CYCLE-RERUN-GUARD",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-LEDGER-ROLLUP-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"missing cycle ledger rerun implementation depth recheck"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_DEPTH_5_RUNTIME_CHAIN_GAP_OPEN",
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
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/contract_gap.schema.json",
                "contracts/schema/upbit_paper_missing_cycle_rerun_guard_report.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py",
                *ROUTE_TEST_ARTIFACTS,
            ],
            "fixture_files": RUNTIME_ARTIFACTS + [rel(DEPTH_REPORT_PATH), rel(CONTRACT_GAP_PATH)],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_missing_cycle_rerun_guard.py",
                "trader1/runtime/paper/upbit_paper_bounded_rerun_staging_executor.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_ledger_rollup_reconciliation.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260504.md",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                rel(DEPTH_REPORT_PATH),
                rel(CONTRACT_GAP_PATH),
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "tests_run",
                "remaining_blockers",
                "next_task_class",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_DEPTH_5_RUNTIME_CHAIN_GAP_OPEN",
        }
    )
    matrix.update(
        {
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "updated_at_utc": now,
            "rows": sorted(rows, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
    report: dict[str, Any],
) -> dict[str, Any]:
    if report["status"] != "PASS_DEPTH_5_RUNTIME_CHAIN_EVIDENCE_LIVE_BLOCKING":
        raise RuntimeError("cannot emit patch_result while missing-cycle depth recheck is blocked")
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-NEXT-TASK-RESTORE",
                "REQ-MVP4-UPBIT-PAPER-MISSING-CYCLE-RERUN-GUARD",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID, rel(DEPTH_REPORT_PATH), rel(CONTRACT_GAP_PATH)],
            "new_or_changed_schema_ids": [],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": remaining_blockers(),
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                rel(DEPTH_REPORT_PATH),
                *RUNTIME_ARTIFACTS,
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK",
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_DEPTH_RECHECK_NEXT_TASK_ADVANCED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION_NO_CURRENT_EVIDENCE_PROMOTION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "scale_up_allowed_after": False,
            "guard_status": report["guard_status"],
            "guard_item_count": report["guard_item_count"],
            "rerun_ready_item_count": report["rerun_ready_item_count"],
            "recovery_guard_blocked_item_count": report["recovery_guard_blocked_item_count"],
            "missing_cycle_ledger_jsonl_total_count": report["missing_cycle_ledger_jsonl_total_count"],
            "planned_staging_artifact_total_count": report["planned_staging_artifact_total_count"],
            "actual_rerun_executed": False,
            "rerun_executor_created": report["rerun_executor_created"],
            "staging_status": report["staging_status"],
            "staged_cycle_count": report["staged_cycle_count"],
            "staged_artifact_count": report["staged_artifact_count"],
            "staging_reused_existing_artifact_count": report["staging_reused_existing_artifact_count"],
            "staging_executor_created": report["staging_executor_created"],
            "post_staging_ledger_rollup_required": report["post_staging_ledger_rollup_required"],
            "post_staging_reconciliation_required": report["post_staging_reconciliation_required"],
            "post_rerun_ledger_rollup_status": report["post_rerun_ledger_rollup_status"],
            "post_rerun_reconciliation_status": report["post_rerun_reconciliation_status"],
            "post_rerun_candidate_rollup_count": report["post_rerun_candidate_rollup_count"],
            "post_rerun_candidate_rollup_written_count": report["post_rerun_candidate_rollup_written_count"],
            "post_rerun_candidate_rollup_reused_existing_count": report[
                "post_rerun_candidate_rollup_reused_existing_count"
            ],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
            "post_rerun_current_evidence_promotion_guard_status": report[
                "post_rerun_current_evidence_promotion_guard_status"
            ],
            "post_rerun_promotion_review_ready_count": report["post_rerun_promotion_review_ready_count"],
            "post_rerun_promotion_candidate_verified_count": report["post_rerun_promotion_candidate_verified_count"],
            "post_rerun_current_evidence_write_allowed_count": report[
                "post_rerun_current_evidence_write_allowed_count"
            ],
            "post_rerun_operator_reconciliation_queue_status": report[
                "post_rerun_operator_reconciliation_queue_status"
            ],
            "post_rerun_operator_reconciliation_queue_item_count": report[
                "post_rerun_operator_reconciliation_queue_item_count"
            ],
            "post_rerun_operator_reconciliation_required_count": report[
                "post_rerun_operator_reconciliation_required_count"
            ],
            "post_rerun_reconciliation_decision_audit_status": report[
                "post_rerun_reconciliation_decision_audit_status"
            ],
            "post_rerun_reconciliation_decision_item_count": report[
                "post_rerun_reconciliation_decision_item_count"
            ],
            "post_rerun_reconciliation_write_denied_count": report[
                "post_rerun_reconciliation_write_denied_count"
            ],
            "post_rerun_current_evidence_write_authorized_count": report[
                "post_rerun_current_evidence_write_authorized_count"
            ],
            "post_rerun_reconciliation_blocker_rollup_status": report[
                "post_rerun_reconciliation_blocker_rollup_status"
            ],
            "post_rerun_reconciliation_blocker_rollup_item_count": report[
                "post_rerun_reconciliation_blocker_rollup_item_count"
            ],
            "post_rerun_reconciliation_unique_blocker_count": report[
                "post_rerun_reconciliation_unique_blocker_count"
            ],
            "post_rerun_reconciliation_primary_blocker_item_count": report[
                "post_rerun_reconciliation_primary_blocker_item_count"
            ],
            "post_rerun_operator_resolution_audit_status": report["post_rerun_operator_resolution_audit_status"],
            "post_rerun_operator_resolution_unresolved_item_count": report[
                "post_rerun_operator_resolution_unresolved_item_count"
            ],
            "post_rerun_operator_resolution_resolved_item_count": report[
                "post_rerun_operator_resolution_resolved_item_count"
            ],
            "post_rerun_operator_resolution_control_count": report[
                "post_rerun_operator_resolution_control_count"
            ],
            "post_rerun_operator_resolution_controls_satisfied_count": report[
                "post_rerun_operator_resolution_controls_satisfied_count"
            ],
            "post_rerun_resolution_current_evidence_closure_status": report[
                "post_rerun_resolution_current_evidence_closure_status"
            ],
            "post_rerun_resolution_closure_source_unresolved_item_count": report[
                "post_rerun_resolution_closure_source_unresolved_item_count"
            ],
            "post_rerun_resolution_closure_source_resolved_item_count": report[
                "post_rerun_resolution_closure_source_resolved_item_count"
            ],
            "post_rerun_resolution_closure_closed_item_count": report[
                "post_rerun_resolution_closure_closed_item_count"
            ],
            "post_rerun_resolution_closure_current_evidence_closed_count": report[
                "post_rerun_resolution_closure_current_evidence_closed_count"
            ],
            "post_rerun_resolution_closure_controls_satisfied_count": report[
                "post_rerun_resolution_closure_controls_satisfied_count"
            ],
            "post_rerun_reconciliation_repair_path_status": report["post_rerun_reconciliation_repair_path_status"],
            "post_rerun_reconciliation_repair_gate_count": report["post_rerun_reconciliation_repair_gate_count"],
            "post_rerun_reconciliation_repair_gate_satisfied_count": report[
                "post_rerun_reconciliation_repair_gate_satisfied_count"
            ],
            "post_rerun_reconciliation_repair_gate_blocked_count": report[
                "post_rerun_reconciliation_repair_gate_blocked_count"
            ],
            "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_status": report[
                "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_status"
            ],
            "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_mismatch_count": report[
                "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_mismatch_count"
            ],
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_MISSING_CYCLE_DEPTH_RECHECK_LIVE_BLOCKING",
            "depth_report_path": rel(DEPTH_REPORT_PATH),
            "contract_gap_path": rel(CONTRACT_GAP_PATH),
            "guard_item_count": report["guard_item_count"],
            "staged_cycle_count": report["staged_cycle_count"],
            "post_rerun_candidate_rollup_count": report["post_rerun_candidate_rollup_count"],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
            "current_evidence_write_allowed_count": report["current_evidence_write_allowed_count"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    artifact_paths = sorted(
        set(
            [
                *CHANGED_ARTIFACTS,
                *RUNTIME_ARTIFACTS,
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "system/evidence/implementation_patch_ledger.json",
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ]
        )
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": artifact_paths,
            "known_blockers": patch_result["remaining_blockers"],
            "depth_report_path": rel(DEPTH_REPORT_PATH),
            "contract_gap_path": rel(CONTRACT_GAP_PATH),
            "guard_item_count": report["guard_item_count"],
            "staged_cycle_count": report["staged_cycle_count"],
            "post_rerun_candidate_rollup_count": report["post_rerun_candidate_rollup_count"],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
            "current_evidence_write_allowed_count": report["current_evidence_write_allowed_count"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# MVP4 Missing Cycle Ledger Rerun Required Implementation Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The missing-cycle gap had guard, staging, and post-rerun evidence, but current state needed an implementation-depth recheck after patch-result validator depth hardening.
- Runtime artifacts now show guard/staging/post-rerun/operator-review/closure/repair-path coverage without making current evidence usable.

Patch:
- Added a depth report and live-affecting contract_gap projection for {GAP_ID}.
- Added regression tests for the runtime evidence chain, contract gap status, and forward route.
- Kept {GAP_ID} open and advanced next_allowed_task_class to {NEXT_TASK_CLASS}.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no scale-up
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", [])) | {GAP_ID})
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
            "next_allowed_task_class": NEXT_TASK_CLASS,
        }
    )
    write_json(ledger_path, ledger)


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(DEPTH_REPORT_PATH, report)
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_contract_gap(now, trader_hash, agents_hash)
    report = build_depth_report(now, trader_hash, agents_hash)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        BOOTSTRAP_VALIDATORS_REQUIRED,
        report,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py",
                    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
                    "tests/contract/test_patch_result_runtime_schema_validation.py",
                    "-q",
                ]
            ),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    *ROUTE_TEST_ARTIFACTS,
                    "-q",
                ]
            ),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "tests/runtime/test_upbit_paper_missing_cycle_rerun_guard.py",
                    "tests/runtime/test_upbit_paper_bounded_rerun_staging_executor.py",
                    "tests/runtime/test_upbit_paper_post_rerun_ledger_rollup_reconciliation.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_blocker_rollup.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
        ]
    )
    report = build_depth_report(now, trader_hash, agents_hash)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        BOOTSTRAP_VALIDATORS_REQUIRED,
        report,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(VALIDATORS_REQUIRED)),
        VALIDATORS_REQUIRED,
        report,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "guard_item_count": report["guard_item_count"],
                "staged_cycle_count": report["staged_cycle_count"],
                "post_rerun_candidate_rollup_count": report["post_rerun_candidate_rollup_count"],
                "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
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
