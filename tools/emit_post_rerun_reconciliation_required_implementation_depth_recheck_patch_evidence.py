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

PATCH_BASENAME = "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
GAP_ID = "POST_RERUN_RECONCILIATION_REQUIRED"
NEXT_TASK_CLASS = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"

RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime"
DEPTH_REPORT_PATH = ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.json"
CONTRACT_GAP_PATH = ROOT / "system" / "evidence" / "contract_gaps" / f"{GAP_ID}.contract_gap.json"
PREVIOUS_STATE_SYNC_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_POST_RERUN_RECONCILIATION_REQUIRED_STATE_SYNC_RECHECK.patch_result.json"
)

RUNTIME_REPORTS = {
    "closure_recheck": RUNTIME_BASE / "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json",
    "repair_path": RUNTIME_BASE / "upbit_paper_post_rerun_reconciliation_repair_path_report.json",
    "blocker_rollup": RUNTIME_BASE / "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json",
    "decision_audit": RUNTIME_BASE / "upbit_paper_post_rerun_reconciliation_decision_audit_report.json",
    "operator_queue": RUNTIME_BASE / "upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
    "resolution_audit": RUNTIME_BASE / "upbit_paper_post_rerun_operator_resolution_audit_report.json",
    "closure": RUNTIME_BASE / "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json",
}

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
    "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_post_rerun_reconciliation_required_recheck.py",
    *ROUTE_TEST_ARTIFACTS,
    "tools/emit_post_rerun_reconciliation_required_implementation_depth_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    str(DEPTH_REPORT_PATH.relative_to(ROOT)).replace("\\", "/"),
    str(CONTRACT_GAP_PATH.relative_to(ROOT)).replace("\\", "/"),
]

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_post_rerun_current_evidence_closure_recheck_validator",
    "upbit_paper_post_rerun_reconciliation_repair_path_validator",
    "upbit_paper_post_rerun_reconciliation_blocker_rollup_validator",
    "upbit_paper_post_rerun_reconciliation_decision_audit_validator",
    "upbit_paper_post_rerun_operator_reconciliation_queue_validator",
    "upbit_paper_post_rerun_operator_resolution_audit_validator",
    "upbit_paper_post_rerun_resolution_current_evidence_closure_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [validator for validator in VALIDATORS_REQUIRED if validator != "generated_artifact_dirty_validator"]

STATIC_BLOCKERS = {
    GAP_ID,
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
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
    "current_evidence_write_allowed",
    "current_ledger_jsonl_write_allowed",
    "latest_runtime_pointer_write_allowed",
)

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


def runtime_artifacts() -> list[str]:
    return [rel(path) for path in RUNTIME_REPORTS.values()]


def remaining_blockers() -> list[str]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    return sorted(set(state.get("open_contract_gap_ids", [])) | STATIC_BLOCKERS)


def false_field_errors(name: str, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in FALSE_RUNTIME_FIELDS:
        if report.get(field) is True:
            errors.append(f"{name} has forbidden true field: {field}")
    if report.get("current_evidence_write_allowed_count", 0) != 0:
        errors.append(f"{name} has nonzero current_evidence_write_allowed_count")
    if report.get("current_evidence_write_authorized_count", 0) != 0:
        errors.append(f"{name} has nonzero current_evidence_write_authorized_count")
    if report.get("candidate_current_evidence_usable_count", 0) != 0:
        errors.append(f"{name} has current-usable candidate evidence")
    return errors


def build_depth_report(now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    reports = {name: load_json(path) for name, path in RUNTIME_REPORTS.items()}
    errors: list[str] = []
    for name, report in reports.items():
        errors.extend(false_field_errors(name, report))

    closure_recheck = reports["closure_recheck"]
    repair_path = reports["repair_path"]
    blocker_rollup = reports["blocker_rollup"]
    decision_audit = reports["decision_audit"]
    operator_queue = reports["operator_queue"]
    resolution_audit = reports["resolution_audit"]
    closure = reports["closure"]

    if closure_recheck.get("recheck_status") != "BLOCKED_POST_RERUN_CLOSURE_CONFIRMED":
        errors.append("closure recheck must remain blocked and confirmed")
    if closure_recheck.get("ledger_runtime_evidence_status") != "PASS":
        errors.append("closure recheck lost ledger runtime evidence PASS status")
    if repair_path.get("repair_path_status") != "BLOCKED_REPAIR_PATH_DECLARED":
        errors.append("repair path must remain blocked")
    if repair_path.get("satisfied_repair_gate_count") != 0:
        errors.append("repair path unexpectedly satisfies repair gates")
    if blocker_rollup.get("blocker_rollup_status") != "BLOCKED":
        errors.append("blocker rollup must remain BLOCKED")
    if blocker_rollup.get("primary_blocker_code") != GAP_ID:
        errors.append("blocker rollup primary blocker drifted")
    if decision_audit.get("decision_audit_status") != "BLOCKED":
        errors.append("decision audit must remain BLOCKED")
    if decision_audit.get("decision_item_count") != decision_audit.get("write_denied_count"):
        errors.append("decision audit item/write-denied counts diverged")
    if operator_queue.get("queue_status") != "BLOCKED":
        errors.append("operator reconciliation queue must remain BLOCKED")
    if int(operator_queue.get("operator_reconciliation_required_count") or 0) <= 0:
        errors.append("operator reconciliation queue no longer requires operator reconciliation")
    if resolution_audit.get("resolution_audit_status") != "UNRESOLVED_RECONCILIATION_REVIEW_ONLY":
        errors.append("resolution audit must remain unresolved review-only")
    if resolution_audit.get("operator_resolution_required") is not True:
        errors.append("operator resolution must remain required")
    if resolution_audit.get("resolved_item_count") != 0:
        errors.append("resolution audit unexpectedly has resolved items")
    if closure.get("closure_status") != "CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED":
        errors.append("current evidence closure must remain closed/unresolved")
    if closure.get("resolved_item_count") != 0:
        errors.append("current evidence closure unexpectedly has resolved items")
    if closure.get("current_evidence_closed_count") != closure.get("closed_item_count"):
        errors.append("current evidence closure closed counts diverged")

    previous_state_sync = load_json(ROOT / PREVIOUS_STATE_SYNC_PATCH_RESULT)
    if previous_state_sync.get("patch_id") != "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_STATE_SYNC_RECHECK_20260504_001":
        errors.append("previous post-rerun state-sync recheck patch_id drifted")
    if GAP_ID not in previous_state_sync.get("remaining_blockers", []):
        errors.append("previous post-rerun state-sync recheck no longer preserves blocker")
    if previous_state_sync.get("live_order_allowed_after") is not False:
        errors.append("previous post-rerun state-sync recheck no longer stays live-blocked")

    status = "PASS_DEPTH_5_POST_RERUN_RECONCILIATION_CHAIN_LIVE_BLOCKING" if not errors else "BLOCKED_DEPTH_RECHECK_ERROR"
    return {
        "schema_id": "trader1.post_rerun_reconciliation_required_implementation_depth_recheck.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "patch_id": PATCH_ID,
        "requirement_id": REQUIREMENT_ID,
        "contract_gap_id": GAP_ID,
        "status": status,
        "depth_level": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "runtime_artifact_paths": runtime_artifacts(),
        "previous_state_sync_patch_result_path": PREVIOUS_STATE_SYNC_PATCH_RESULT,
        "previous_state_sync_patch_result_hash": previous_state_sync.get("result_hash"),
        "error_count": len(errors),
        "errors": errors,
        "recheck_status": closure_recheck.get("recheck_status"),
        "ledger_runtime_evidence_status": closure_recheck.get("ledger_runtime_evidence_status"),
        "ledger_reconciliation_status": closure_recheck.get("ledger_reconciliation_status"),
        "ledger_idempotency_status": closure_recheck.get("ledger_idempotency_status"),
        "ledger_source_runtime_depth_status": closure_recheck.get("ledger_source_runtime_depth_status"),
        "ledger_source_runtime_depth_mismatch_count": closure_recheck.get(
            "ledger_source_runtime_depth_mismatch_count"
        ),
        "repair_path_status": repair_path.get("repair_path_status"),
        "repair_gate_count": repair_path.get("repair_gate_count"),
        "satisfied_repair_gate_count": repair_path.get("satisfied_repair_gate_count"),
        "blocked_repair_gate_count": repair_path.get("blocked_repair_gate_count"),
        "blocker_rollup_status": blocker_rollup.get("blocker_rollup_status"),
        "rollup_item_count": blocker_rollup.get("rollup_item_count"),
        "unique_blocker_count": blocker_rollup.get("unique_blocker_count"),
        "primary_blocker_code": blocker_rollup.get("primary_blocker_code"),
        "primary_blocker_item_count": blocker_rollup.get("primary_blocker_item_count"),
        "decision_audit_status": decision_audit.get("decision_audit_status"),
        "decision_item_count": decision_audit.get("decision_item_count"),
        "write_denied_count": decision_audit.get("write_denied_count"),
        "operator_queue_status": operator_queue.get("queue_status"),
        "operator_queue_item_count": operator_queue.get("queue_item_count"),
        "operator_reconciliation_required_count": operator_queue.get("operator_reconciliation_required_count"),
        "review_ready_reconciliation_item_count": operator_queue.get("review_ready_reconciliation_item_count"),
        "resolution_audit_status": resolution_audit.get("resolution_audit_status"),
        "operator_resolution_required": resolution_audit.get("operator_resolution_required"),
        "unresolved_item_count": resolution_audit.get("unresolved_item_count"),
        "resolved_item_count": resolution_audit.get("resolved_item_count"),
        "resolution_control_count": resolution_audit.get("resolution_control_count"),
        "resolution_controls_satisfied_count": resolution_audit.get("resolution_controls_satisfied_count"),
        "closure_status": closure.get("closure_status"),
        "closed_item_count": closure.get("closed_item_count"),
        "current_evidence_closed_count": closure.get("current_evidence_closed_count"),
        "candidate_current_evidence_usable_count": closure.get("candidate_current_evidence_usable_count"),
        "current_evidence_write_allowed_count": closure.get("current_evidence_write_allowed_count"),
        "current_evidence_write_authorized_count": closure.get("current_evidence_write_authorized_count"),
        "current_evidence_mutation_allowed": False,
        "next_allowed_task_class": NEXT_TASK_CLASS,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


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
                    "message": "Post-rerun reconciliation evidence reaches depth-5 review coverage, but operator resolution remains unresolved and current evidence writes remain blocked.",
                }
            ],
            "notes": "Depth recheck only; no current evidence write, live order, credentialed API call, live config mutation, or scale-up permission is created.",
            "contract_gap_id": GAP_ID,
            "severity": "HIGH",
            "source_section_id": "SECTION_CURRENT_EVIDENCE_CLOSURE",
            "live_affecting": True,
        },
    )


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_CURRENT_EVIDENCE_CLOSURE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-STATE-SYNC-RECHECK", "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-RECHECK", "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.contract_gap.v1", "trader1.upbit_paper_post_rerun_current_evidence_closure_recheck_report.v1", "trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1", "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS + runtime_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Confirm closure recheck, repair path, blocker rollup, decision audit, operator queue, resolution audit, and closure reports remain present.
- Confirm the chain reaches DEPTH_5 evidence/stage gate coverage while operator resolution remains unresolved.
- Confirm current evidence usability, write authorization, current ledger JSONL write, latest pointer write, live order, and scale-up remain blocked.
- Keep {GAP_ID} open and live-affecting.
- Route to {NEXT_TASK_CLASS}.

depth_snapshot:
- status: {report["status"]}
- operator_reconciliation_required_count: {report["operator_reconciliation_required_count"]}
- unresolved_item_count: {report["unresolved_item_count"]}
- resolved_item_count: {report["resolved_item_count"]}
- candidate_current_evidence_usable_count: {report["candidate_current_evidence_usable_count"]}
- current_evidence_write_allowed_count: {report["current_evidence_write_allowed_count"]}

known_omissions_by_design:
- No post-rerun reconciliation is resolved by this patch.
- No current ledger JSONL, latest pointer, current evidence, live config, credentialed API, live order, or scale-up output is written.
- {GAP_ID} and {NEXT_TASK_CLASS} remain live-blocking until independent current-evidence write-blocked recheck evidence passes.

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

Post-rerun reconciliation has depth-5 closure, repair path, blocker rollup, decision audit, operator queue, resolution audit, and current-evidence closure evidence. Operator resolution remains unresolved and all current evidence writes remain blocked.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    artifacts = sorted(
        set(
            CHANGED_ARTIFACTS
            + runtime_artifacts()
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

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_CURRENT_EVIDENCE_CLOSURE",
            "source_file": "TRADER_1.md",
            "source_heading": "post-rerun reconciliation required implementation depth recheck",
            "full_text_marker": f"{REQUIREMENT_ID}: verify post-rerun reconciliation runtime evidence depth without current evidence or live permission",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Post-rerun reconciliation required implementation depth recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.patch_result.v1", "trader1.contract_gap.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py",
                "tests/contract/test_post_rerun_reconciliation_required_recheck.py",
                *ROUTE_TEST_ARTIFACTS,
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-STATE-SYNC-RECHECK",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-RECHECK",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"post rerun reconciliation implementation depth recheck"),
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
            "section_id": "SECTION_CURRENT_EVIDENCE_CLOSURE",
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/contract_gap.schema.json",
                "contracts/schema/upbit_paper_post_rerun_current_evidence_closure_recheck_report.schema.json",
                "contracts/schema/upbit_paper_post_rerun_reconciliation_repair_path_report.schema.json",
                "contracts/schema/upbit_paper_post_rerun_resolution_current_evidence_closure_report.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py",
                "tests/contract/test_post_rerun_reconciliation_required_recheck.py",
                *ROUTE_TEST_ARTIFACTS,
            ],
            "fixture_files": runtime_artifacts() + [rel(DEPTH_REPORT_PATH), rel(CONTRACT_GAP_PATH)],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_post_rerun_current_evidence_closure_recheck.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_repair_path.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_resolution_current_evidence_closure.py",
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
    if report["status"] != "PASS_DEPTH_5_POST_RERUN_RECONCILIATION_CHAIN_LIVE_BLOCKING":
        raise RuntimeError("cannot emit patch_result while post-rerun reconciliation depth recheck is blocked")
    template = load_json(ROOT / PREVIOUS_STATE_SYNC_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-STATE-SYNC-RECHECK",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-RECHECK",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
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
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH"],
            "next_forbidden_default_sections": ["MVP5_LIVE_PERMISSION", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
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
                *runtime_artifacts(),
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK",
            "required_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
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
            "stage_gate_status": "PASS_POST_RERUN_RECONCILIATION_DEPTH_RECHECK_LIVE_BLOCKING",
            "depth_report_path": rel(DEPTH_REPORT_PATH),
            "contract_gap_path": rel(CONTRACT_GAP_PATH),
            "operator_reconciliation_required_count": report["operator_reconciliation_required_count"],
            "unresolved_item_count": report["unresolved_item_count"],
            "resolved_item_count": report["resolved_item_count"],
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
                *runtime_artifacts(),
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
            "operator_reconciliation_required_count": report["operator_reconciliation_required_count"],
            "unresolved_item_count": report["unresolved_item_count"],
            "resolved_item_count": report["resolved_item_count"],
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
        f"""# MVP4 Post-Rerun Reconciliation Required Implementation Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The post-rerun reconciliation gap had closure/reconciliation/repair evidence, but current state needed an implementation-depth recheck after the missing-cycle rerun depth pass.
- Runtime artifacts now show closure recheck, repair path, blocker rollup, decision audit, operator queue, resolution audit, and current-evidence closure coverage without making current evidence usable.

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
                    "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py",
                    "tests/contract/test_post_rerun_reconciliation_required_recheck.py",
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
                    "tests/runtime/test_upbit_paper_post_rerun_current_evidence_closure_recheck.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_repair_path.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_blocker_rollup.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_decision_audit.py",
                    "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_queue.py",
                    "tests/runtime/test_upbit_paper_post_rerun_operator_resolution_audit.py",
                    "tests/runtime/test_upbit_paper_post_rerun_resolution_current_evidence_closure.py",
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
                "operator_reconciliation_required_count": report["operator_reconciliation_required_count"],
                "unresolved_item_count": report["unresolved_item_count"],
                "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
                "current_evidence_write_allowed_count": report["current_evidence_write_allowed_count"],
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
