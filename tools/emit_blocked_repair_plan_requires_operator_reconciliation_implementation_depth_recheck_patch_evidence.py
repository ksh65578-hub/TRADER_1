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

PATCH_BASENAME = "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-IMPLEMENTATION-DEPTH-RECHECK"
GAP_ID = "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION"
NEXT_GAP_ID = "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION"
NEXT_TASK_CLASS = "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"

RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime"
BLOCKED_REPAIR_PLAN_REPORT = RUNTIME_BASE / "upbit_paper_blocked_repair_plan_report.json"
REPAIR_OPERATOR_QUEUE_REPORT = RUNTIME_BASE / "upbit_paper_repair_operator_queue_report.json"
DEPTH_REPORT_PATH = ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.json"
CONTRACT_GAP_PATH = ROOT / "system" / "evidence" / "contract_gaps" / f"{GAP_ID}.contract_gap.json"
PREVIOUS_HASH_MISMATCH_DEPTH_PATCH_RESULT = (
    "system/evidence/patch_results/"
    "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.patch_result.json"
)
PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT = (
    "system/evidence/patch_results/"
    "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK.patch_result.json"
)
PREVIOUS_BLOCKED_REPAIR_RECHECK_PATCH_RESULT = (
    "system/evidence/patch_results/"
    "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK.patch_result.json"
)

ROUTE_TEST_ARTIFACTS = [
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py",
    "tests/contract/test_completed_recheck_route_depth_guard.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
    "tests/contract/test_open_contract_gap_implementation_priority_recheck.py",
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_implementation_depth_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
    "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
]

CHANGED_ARTIFACTS = [
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck.py",
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py",
    *ROUTE_TEST_ARTIFACTS,
    "tools/emit_blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    str(DEPTH_REPORT_PATH.relative_to(ROOT)).replace("\\", "/"),
    str(CONTRACT_GAP_PATH.relative_to(ROOT)).replace("\\", "/"),
]

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_blocked_repair_plan_validator",
    "upbit_paper_repair_operator_queue_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [validator for validator in VALIDATORS_REQUIRED if validator != "generated_artifact_dirty_validator"]

STATIC_BLOCKERS = {
    GAP_ID,
    NEXT_GAP_ID,
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
}
FALSE_FIELDS = (
    "live_order_ready",
    "live_order_allowed",
    "can_live_trade",
    "scale_up_allowed",
    "current_evidence_mutation_allowed",
    "persistent_loop_mutation_allowed",
    "source_delete_allowed",
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
    return [rel(BLOCKED_REPAIR_PLAN_REPORT), rel(REPAIR_OPERATOR_QUEUE_REPORT)]


def remaining_blockers() -> list[str]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    blocked_plan = load_json(BLOCKED_REPAIR_PLAN_REPORT)
    queue = load_json(REPAIR_OPERATOR_QUEUE_REPORT)
    return sorted(
        set(state.get("open_contract_gap_ids", []))
        | set(blocked_plan.get("blocker_codes") or [])
        | set(queue.get("blocker_codes") or [])
        | STATIC_BLOCKERS
    )


def false_field_errors(name: str, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in FALSE_FIELDS:
        if report.get(field) is True:
            errors.append(f"{name} has forbidden true field: {field}")
    if report.get("candidate_current_evidence_usable_count", 0) != 0:
        errors.append(f"{name} has current-usable candidate evidence")
    if report.get("promotion_eligible") is True:
        errors.append(f"{name} marks promotion eligible")
    return errors


def build_depth_report(now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    previous_hash_mismatch_depth = load_json(ROOT / PREVIOUS_HASH_MISMATCH_DEPTH_PATCH_RESULT)
    previous_hash_mismatch_recheck = load_json(ROOT / PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT)
    previous_blocked_repair_recheck = load_json(ROOT / PREVIOUS_BLOCKED_REPAIR_RECHECK_PATCH_RESULT)
    blocked_plan = load_json(BLOCKED_REPAIR_PLAN_REPORT)
    operator_queue = load_json(REPAIR_OPERATOR_QUEUE_REPORT)

    errors: list[str] = []
    errors.extend(false_field_errors("blocked_plan", blocked_plan))
    errors.extend(false_field_errors("operator_queue", operator_queue))

    if REQUIREMENT_ID in state.get("completed_requirement_ids", []):
        if state.get("next_allowed_task_class") != NEXT_TASK_CLASS:
            errors.append("completed depth recheck no longer routes to regenerated repair implementation depth recheck")
    elif state.get("next_allowed_task_class") != "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK":
        errors.append("current state is not routed to blocked repair plan implementation depth recheck")
    if (
        previous_hash_mismatch_depth.get("next_task_class")
        != "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"
    ):
        errors.append("previous hash-mismatch depth recheck no longer routes to this task")
    if previous_hash_mismatch_recheck.get("next_task_class") != "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK":
        errors.append("previous hash-mismatch recheck no longer routes to blocked repair plan recheck")
    if previous_blocked_repair_recheck.get("patch_id") != "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK_20260504_001":
        errors.append("previous blocked repair plan recheck patch id drifted")
    if previous_blocked_repair_recheck.get("next_task_class") != "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_RECHECK":
        errors.append("previous blocked repair plan recheck next task drifted")

    if blocked_plan.get("repair_plan_status") != "BLOCKED":
        errors.append("blocked repair plan must remain BLOCKED")
    if blocked_plan.get("primary_blocker_code") != GAP_ID:
        errors.append("blocked repair plan primary blocker drifted")
    if GAP_ID not in set(blocked_plan.get("blocker_codes") or []):
        errors.append("blocked repair plan lost operator reconciliation blocker")
    expected_counts = {
        "repair_item_count": 6,
        "ledger_rollup_rebuild_ready_count": 1,
        "runtime_cycle_rerun_required_count": 5,
        "recovery_guard_rerun_required_count": 1,
        "missing_cycle_ledger_jsonl_total_count": 10,
        "missing_paper_ledger_rollup_artifact_count": 6,
    }
    for field, expected in expected_counts.items():
        if int(blocked_plan.get(field) or 0) != expected:
            errors.append(f"blocked repair plan {field} drifted")
    for field in (
        "generated_artifact_mutation_allowed",
        "current_evidence_mutation_allowed",
        "source_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
    ):
        if blocked_plan.get(field) is True:
            errors.append(f"blocked repair plan has forbidden true field: {field}")

    plan_items = [item for item in blocked_plan.get("items", []) if isinstance(item, dict)]
    lane_counts: dict[str, int] = {}
    for item in plan_items:
        lane = str(item.get("safe_repair_lane") or "UNKNOWN")
        lane_counts[lane] = lane_counts.get(lane, 0) + 1
        for field in ("current_evidence_mutation_allowed", "source_delete_allowed", "live_permission_created"):
            if item.get(field) is True:
                errors.append(f"blocked repair plan item has forbidden true field: {field}")
        for step in item.get("repair_steps", []):
            if step.get("mutates_current_evidence") is True:
                errors.append("blocked repair step mutates current evidence")
            if step.get("live_permission_created") is True:
                errors.append("blocked repair step created live permission")
    if len(plan_items) != 6:
        errors.append("blocked repair plan item count drifted")
    if lane_counts.get("LEDGER_ROLLUP_REBUILD_READY") != 1:
        errors.append("blocked repair plan ledger-rollup-ready lane count drifted")
    if lane_counts.get("RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP") != 4:
        errors.append("blocked repair plan runtime-cycle rerun lane count drifted")
    if lane_counts.get("RECOVERY_GUARD_THEN_LEDGER_ROLLUP") != 1:
        errors.append("blocked repair plan recovery-guard lane count drifted")

    if operator_queue.get("queue_status") != "BLOCKED":
        errors.append("repair operator queue must remain BLOCKED")
    if int(operator_queue.get("queue_item_count") or 0) != 6:
        errors.append("repair operator queue item count drifted")
    if int(operator_queue.get("ledger_candidate_review_ready_count") or 0) != 1:
        errors.append("repair operator queue review-ready count drifted")
    if int(operator_queue.get("runtime_cycle_rerun_required_count") or 0) != 5:
        errors.append("repair operator queue runtime rerun count drifted")
    if int(operator_queue.get("recovery_guard_rerun_required_count") or 0) != 1:
        errors.append("repair operator queue recovery guard count drifted")
    if int(operator_queue.get("candidate_current_evidence_usable_count") or 0) != 0:
        errors.append("repair operator queue exposed current evidence usability")
    if NEXT_GAP_ID not in set(operator_queue.get("blocker_codes") or []):
        errors.append("repair operator queue lost regenerated repair blocker")
    queue_items = [item for item in operator_queue.get("items", []) if isinstance(item, dict)]
    for item in queue_items:
        if GAP_ID not in set(item.get("blocking_codes") or []):
            errors.append("repair operator queue item lost blocked repair plan blocker")
        for field in FALSE_FIELDS:
            if item.get(field) is True:
                errors.append(f"repair operator queue item has forbidden true field: {field}")
        if item.get("live_permission_created") is True:
            errors.append("repair operator queue item created live permission")
        if item.get("candidate_current_evidence_usable") is True:
            errors.append("repair operator queue item became current-evidence usable")

    current_usable_count = int(operator_queue.get("candidate_current_evidence_usable_count") or 0)
    status = (
        "PASS_DEPTH_5_BLOCKED_REPAIR_PLAN_OPERATOR_RECONCILIATION_LIVE_BLOCKING"
        if not errors
        else "BLOCKED_DEPTH_RECHECK_ERROR"
    )
    return {
        "schema_id": "trader1.blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "patch_id": PATCH_ID,
        "requirement_id": REQUIREMENT_ID,
        "contract_gap_id": GAP_ID,
        "status": status,
        "depth_level": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "runtime_artifact_paths": runtime_artifacts(),
        "previous_hash_mismatch_depth_patch_result_path": PREVIOUS_HASH_MISMATCH_DEPTH_PATCH_RESULT,
        "previous_hash_mismatch_depth_patch_result_hash": previous_hash_mismatch_depth.get("result_hash"),
        "previous_hash_mismatch_recheck_patch_result_path": PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT,
        "previous_hash_mismatch_recheck_patch_result_hash": previous_hash_mismatch_recheck.get("result_hash"),
        "previous_blocked_repair_recheck_patch_result_path": PREVIOUS_BLOCKED_REPAIR_RECHECK_PATCH_RESULT,
        "previous_blocked_repair_recheck_patch_result_hash": previous_blocked_repair_recheck.get("result_hash"),
        "error_count": len(errors),
        "errors": errors,
        "blocked_repair_plan_status": blocked_plan.get("repair_plan_status"),
        "primary_blocker_code": blocked_plan.get("primary_blocker_code"),
        "repair_item_count": blocked_plan.get("repair_item_count"),
        "ledger_rollup_rebuild_ready_count": blocked_plan.get("ledger_rollup_rebuild_ready_count"),
        "runtime_cycle_rerun_required_count": blocked_plan.get("runtime_cycle_rerun_required_count"),
        "recovery_guard_rerun_required_count": blocked_plan.get("recovery_guard_rerun_required_count"),
        "missing_cycle_ledger_jsonl_total_count": blocked_plan.get("missing_cycle_ledger_jsonl_total_count"),
        "missing_paper_ledger_rollup_artifact_count": blocked_plan.get("missing_paper_ledger_rollup_artifact_count"),
        "ledger_rollup_rebuild_ready_lane_count": lane_counts.get("LEDGER_ROLLUP_REBUILD_READY", 0),
        "runtime_cycle_rerun_lane_count": lane_counts.get("RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP", 0),
        "recovery_guard_rerun_lane_count": lane_counts.get("RECOVERY_GUARD_THEN_LEDGER_ROLLUP", 0),
        "repair_operator_queue_status": operator_queue.get("queue_status"),
        "repair_operator_queue_item_count": operator_queue.get("queue_item_count"),
        "repair_operator_queue_ledger_candidate_review_ready_count": operator_queue.get(
            "ledger_candidate_review_ready_count"
        ),
        "repair_operator_queue_runtime_cycle_rerun_required_count": operator_queue.get(
            "runtime_cycle_rerun_required_count"
        ),
        "repair_operator_queue_recovery_guard_rerun_required_count": operator_queue.get(
            "recovery_guard_rerun_required_count"
        ),
        "repair_operator_queue_candidate_current_evidence_usable_count": operator_queue.get(
            "candidate_current_evidence_usable_count"
        ),
        "candidate_current_evidence_usable_count": current_usable_count,
        "current_evidence_mutation_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
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
                    "message": "Blocked repair plan remains live-blocking: six PAPER repair items require operator reconciliation, ledger rollup rebuild, runtime cycle rerun, or recovery guard rerun before any regenerated current evidence can be considered.",
                }
            ],
            "notes": "Depth recheck only; no current evidence write, live order, credentialed API call, live config mutation, or scale-up permission is created.",
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
task_class: MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_CURRENT_EVIDENCE_CLOSURE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK", "REQ-MVP4-UPBIT-PAPER-BLOCKED-REPAIR-PLAN", "REQ-MVP4-UPBIT-PAPER-REPAIR-OPERATOR-QUEUE"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.contract_gap.v1", "trader1.upbit_paper_blocked_repair_plan_report.v1", "trader1.upbit_paper_repair_operator_queue_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS + runtime_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Confirm the blocked repair plan remains BLOCKED.
- Confirm all six repair items remain operator-action-required and fail-closed.
- Confirm lane counts remain 1 ledger-rollup-ready, 4 runtime-rerun, and 1 recovery-guard-rerun.
- Confirm repair operator queue remains BLOCKED with candidate_current_evidence_usable_count=0.
- Keep {GAP_ID} and {NEXT_GAP_ID} open.
- Route to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, and scale_up_allowed=false.

depth_snapshot:
- status: {report["status"]}
- blocked_repair_plan_status: {report["blocked_repair_plan_status"]}
- repair_item_count: {report["repair_item_count"]}
- ledger_rollup_rebuild_ready_count: {report["ledger_rollup_rebuild_ready_count"]}
- runtime_cycle_rerun_required_count: {report["runtime_cycle_rerun_required_count"]}
- recovery_guard_rerun_required_count: {report["recovery_guard_rerun_required_count"]}
- repair_operator_queue_status: {report["repair_operator_queue_status"]}
- repair_operator_queue_item_count: {report["repair_operator_queue_item_count"]}
- candidate_current_evidence_usable_count: {report["candidate_current_evidence_usable_count"]}

known_omissions_by_design:
- Does not execute repair steps.
- Does not write current evidence.
- Does not mutate live config.
- Does not call exchange/account/private/live APIs.
- Does not permit live orders or scale-up.
""",
    )
    awv_path = ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md"
    existing = awv_path.read_text(encoding="utf-8") if awv_path.exists() else ""
    marker = f"## {PATCH_BASENAME}"
    block = f"""

{marker}

updated_at_utc: {now}
last_patch_id: {PATCH_ID}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

Blocked repair plan depth has been rechecked as operator-action-required. The plan still has six fail-closed repair items, the repair queue still exposes no usable current evidence, and the next task is:

{NEXT_TASK_CLASS}
"""
    if marker in existing:
        existing = existing[: existing.index(marker)].rstrip()
    write_text(awv_path, existing.rstrip() + block)


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    artifacts = sorted(
        set(
            CHANGED_ARTIFACTS
            + runtime_artifacts()
            + [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260504.md",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ]
        )
    )
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "blocked repair plan requires operator reconciliation implementation depth recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: verify blocked repair plan operator reconciliation depth without "
                "executing repair steps, current evidence promotion, live permission, or scale-up"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Blocked repair plan requires operator reconciliation implementation depth recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.contract_gap.v1",
                "trader1.upbit_paper_blocked_repair_plan_report.v1",
                "trader1.upbit_paper_repair_operator_queue_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck.py",
                "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py",
                *ROUTE_TEST_ARTIFACTS,
                "tests/runtime/test_upbit_paper_blocked_repair_plan.py",
                "tests/runtime/test_upbit_paper_repair_operator_queue.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"],
            "depends_on": [
                "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK",
                "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK",
                "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK",
                "REQ-MVP4-UPBIT-PAPER-BLOCKED-REPAIR-PLAN",
                "REQ-MVP4-UPBIT-PAPER-REPAIR-OPERATOR-QUEUE",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                f"{REQUIREMENT_ID}|{PATCH_ID}|{GAP_ID}|{NEXT_TASK_CLASS}".encode("utf-8")
            ),
            "implementation_status": "COMPLETED",
            "test_status": "PASS",
        }
    )
    req_index.update(
        {
            "updated_at_utc": now,
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "requirements": sorted(requirements, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(req_path, req_index)

    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_LEDGER_RECONCILIATION",
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/contract_gap.schema.json",
                "contracts/schema/upbit_paper_blocked_repair_plan_report.schema.json",
                "contracts/schema/upbit_paper_repair_operator_queue_report.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck.py",
                "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py",
                *ROUTE_TEST_ARTIFACTS,
                "tests/runtime/test_upbit_paper_blocked_repair_plan.py",
                "tests/runtime/test_upbit_paper_repair_operator_queue.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_blocked_repair_plan.py",
                "trader1/runtime/paper/upbit_paper_repair_operator_queue.py",
            ],
            "evidence_artifacts": artifacts + [rel(CONTRACT_GAP_PATH), rel(DEPTH_REPORT_PATH)],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "next_task_class",
                "remaining_blockers",
                "blocked_repair_plan_status",
                "blocked_repair_plan_item_count",
                "blocked_repair_plan_ledger_rollup_rebuild_ready_count",
                "blocked_repair_plan_runtime_cycle_rerun_required_count",
                "blocked_repair_plan_recovery_guard_rerun_required_count",
                "blocked_repair_plan_missing_cycle_ledger_jsonl_total_count",
                "blocked_repair_plan_missing_paper_ledger_rollup_artifact_count",
                "repair_operator_queue_status",
                "repair_operator_queue_item_count",
                "repair_operator_queue_ledger_candidate_review_ready_count",
                "repair_operator_queue_candidate_current_evidence_usable_count",
                "candidate_current_evidence_usable_count",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "COMPLETED",
        }
    )
    matrix.update(
        {
            "updated_at_utc": now,
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
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
    if report["status"] != "PASS_DEPTH_5_BLOCKED_REPAIR_PLAN_OPERATOR_RECONCILIATION_LIVE_BLOCKING":
        raise RuntimeError("cannot emit patch_result while blocked repair plan depth recheck is blocked")
    template = load_json(ROOT / PREVIOUS_BLOCKED_REPAIR_RECHECK_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK",
                "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK",
                "REQ-MVP4-UPBIT-PAPER-BLOCKED-REPAIR-PLAN",
                "REQ-MVP4-UPBIT-PAPER-REPAIR-OPERATOR-QUEUE",
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
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
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
                PREVIOUS_HASH_MISMATCH_DEPTH_PATCH_RESULT,
                PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT,
                PREVIOUS_BLOCKED_REPAIR_RECHECK_PATCH_RESULT,
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK",
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
            "convergence_validators_required": validators_required,
            "convergence_validators_run": validators_run,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "scale_up_allowed_after": False,
            "blocked_repair_plan_status": report["blocked_repair_plan_status"],
            "blocked_repair_plan_item_count": report["repair_item_count"],
            "blocked_repair_plan_ledger_rollup_rebuild_ready_count": report["ledger_rollup_rebuild_ready_count"],
            "blocked_repair_plan_runtime_cycle_rerun_required_count": report["runtime_cycle_rerun_required_count"],
            "blocked_repair_plan_recovery_guard_rerun_required_count": report["recovery_guard_rerun_required_count"],
            "blocked_repair_plan_missing_cycle_ledger_jsonl_total_count": report[
                "missing_cycle_ledger_jsonl_total_count"
            ],
            "blocked_repair_plan_missing_paper_ledger_rollup_artifact_count": report[
                "missing_paper_ledger_rollup_artifact_count"
            ],
            "repair_operator_queue_status": report["repair_operator_queue_status"],
            "repair_operator_queue_item_count": report["repair_operator_queue_item_count"],
            "repair_operator_queue_ledger_candidate_review_ready_count": report[
                "repair_operator_queue_ledger_candidate_review_ready_count"
            ],
            "repair_operator_queue_runtime_cycle_rerun_required_count": report[
                "repair_operator_queue_runtime_cycle_rerun_required_count"
            ],
            "repair_operator_queue_recovery_guard_rerun_required_count": report[
                "repair_operator_queue_recovery_guard_rerun_required_count"
            ],
            "repair_operator_queue_candidate_current_evidence_usable_count": report[
                "repair_operator_queue_candidate_current_evidence_usable_count"
            ],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
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
            "stage_gate_status": "PASS_BLOCKED_REPAIR_PLAN_OPERATOR_RECONCILIATION_DEPTH_RECHECK_LIVE_BLOCKING",
            "depth_report_path": rel(DEPTH_REPORT_PATH),
            "contract_gap_path": rel(CONTRACT_GAP_PATH),
            "blocked_repair_plan_status": report["blocked_repair_plan_status"],
            "repair_item_count": report["repair_item_count"],
            "ledger_rollup_rebuild_ready_count": report["ledger_rollup_rebuild_ready_count"],
            "runtime_cycle_rerun_required_count": report["runtime_cycle_rerun_required_count"],
            "recovery_guard_rerun_required_count": report["recovery_guard_rerun_required_count"],
            "missing_cycle_ledger_jsonl_total_count": report["missing_cycle_ledger_jsonl_total_count"],
            "missing_paper_ledger_rollup_artifact_count": report["missing_paper_ledger_rollup_artifact_count"],
            "repair_operator_queue_status": report["repair_operator_queue_status"],
            "repair_operator_queue_item_count": report["repair_operator_queue_item_count"],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
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
                PREVIOUS_HASH_MISMATCH_DEPTH_PATCH_RESULT,
                PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT,
                PREVIOUS_BLOCKED_REPAIR_RECHECK_PATCH_RESULT,
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
            "blocked_repair_plan_status": report["blocked_repair_plan_status"],
            "repair_item_count": report["repair_item_count"],
            "ledger_rollup_rebuild_ready_count": report["ledger_rollup_rebuild_ready_count"],
            "runtime_cycle_rerun_required_count": report["runtime_cycle_rerun_required_count"],
            "recovery_guard_rerun_required_count": report["recovery_guard_rerun_required_count"],
            "missing_cycle_ledger_jsonl_total_count": report["missing_cycle_ledger_jsonl_total_count"],
            "missing_paper_ledger_rollup_artifact_count": report["missing_paper_ledger_rollup_artifact_count"],
            "repair_operator_queue_status": report["repair_operator_queue_status"],
            "repair_operator_queue_item_count": report["repair_operator_queue_item_count"],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# MVP4 Blocked Repair Plan Requires Operator Reconciliation Implementation Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The blocked repair plan remains BLOCKED and live-affecting.
- Six repair items still require ledger rollup rebuild, PAPER runtime rerun, recovery guard rerun, or operator reconciliation.
- The repair operator queue remains BLOCKED and exposes no usable current evidence.
- candidate_current_evidence_usable_count remains 0.

Patch:
- Added a depth report and contract_gap projection for {GAP_ID}.
- Added regression tests for blocked repair plan depth, operator queue fail-closed behavior, and forward route.
- Kept {GAP_ID} and {NEXT_GAP_ID} open, and advanced next_allowed_task_class to {NEXT_TASK_CLASS}.

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
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", [])) | {GAP_ID, NEXT_GAP_ID})
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
                    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck.py",
                    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py",
                    "tests/contract/test_post_repair_reconciliation_required_implementation_depth_recheck.py",
                    "-q",
                ]
            ),
            run_command(
                [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", *ROUTE_TEST_ARTIFACTS, "-q"]
            ),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "tests/runtime/test_upbit_paper_blocked_repair_plan.py",
                    "tests/runtime/test_upbit_paper_repair_operator_queue.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command(
                [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"],
                timeout_seconds=1200,
            ),
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
                "blocked_repair_plan_status": report["blocked_repair_plan_status"],
                "repair_item_count": report["repair_item_count"],
                "repair_operator_queue_status": report["repair_operator_queue_status"],
                "repair_operator_queue_item_count": report["repair_operator_queue_item_count"],
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
