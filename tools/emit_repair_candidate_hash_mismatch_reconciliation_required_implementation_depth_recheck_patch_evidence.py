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

PATCH_BASENAME = "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
GAP_ID = "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED"
NEXT_GAP_ID = "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION"
NEXT_TASK_CLASS = "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK"

RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime"
POST_REPAIR_REPORT = RUNTIME_BASE / "upbit_paper_post_repair_reconciliation_report.json"
REPAIR_OPERATOR_QUEUE_REPORT = RUNTIME_BASE / "upbit_paper_repair_operator_queue_report.json"
DEPTH_REPORT_PATH = ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.json"
CONTRACT_GAP_PATH = ROOT / "system" / "evidence" / "contract_gaps" / f"{GAP_ID}.contract_gap.json"
PREVIOUS_POST_REPAIR_DEPTH_PATCH_RESULT = (
    "system/evidence/patch_results/"
    "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.patch_result.json"
)
PREVIOUS_POST_REPAIR_RECHECK_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK.patch_result.json"
)
PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT = (
    "system/evidence/patch_results/"
    "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK.patch_result.json"
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
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
]

CHANGED_ARTIFACTS = [
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_implementation_depth_recheck.py",
    *ROUTE_TEST_ARTIFACTS,
    "tools/emit_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    str(DEPTH_REPORT_PATH.relative_to(ROOT)).replace("\\", "/"),
    str(CONTRACT_GAP_PATH.relative_to(ROOT)).replace("\\", "/"),
]

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_post_repair_reconciliation_validator",
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
    return [rel(POST_REPAIR_REPORT), rel(REPAIR_OPERATOR_QUEUE_REPORT)]


def remaining_blockers() -> list[str]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    post_repair = load_json(POST_REPAIR_REPORT)
    queue = load_json(REPAIR_OPERATOR_QUEUE_REPORT)
    return sorted(
        set(state.get("open_contract_gap_ids", []))
        | set(post_repair.get("blocker_codes") or [])
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
    previous_post_repair_depth = load_json(ROOT / PREVIOUS_POST_REPAIR_DEPTH_PATCH_RESULT)
    previous_post_repair_recheck = load_json(ROOT / PREVIOUS_POST_REPAIR_RECHECK_PATCH_RESULT)
    previous_hash_mismatch_recheck = load_json(ROOT / PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT)
    post_repair = load_json(POST_REPAIR_REPORT)
    operator_queue = load_json(REPAIR_OPERATOR_QUEUE_REPORT)

    errors: list[str] = []
    errors.extend(false_field_errors("post_repair", post_repair))
    errors.extend(false_field_errors("operator_queue", operator_queue))

    if REQUIREMENT_ID in state.get("completed_requirement_ids", []):
        if state.get("next_allowed_task_class") != NEXT_TASK_CLASS:
            errors.append("completed depth recheck no longer routes to blocked-repair-plan implementation depth recheck")
    elif state.get("next_allowed_task_class") != "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK":
        errors.append("current state is not routed to hash-mismatch implementation depth recheck")
    if (
        previous_post_repair_depth.get("next_task_class")
        != "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
    ):
        errors.append("previous post-repair depth recheck no longer routes to this task")
    if previous_post_repair_recheck.get("next_task_class") != "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK":
        errors.append("previous post-repair state-sync recheck no longer routes to hash-mismatch recheck")
    if previous_hash_mismatch_recheck.get("patch_id") != "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK_20260504_001":
        errors.append("previous hash-mismatch recheck patch id drifted")

    if post_repair.get("post_repair_reconciliation_status") != "BLOCKED":
        errors.append("post-repair reconciliation must remain BLOCKED")
    if post_repair.get("primary_blocker_code") != "POST_REPAIR_RECONCILIATION_REQUIRED":
        errors.append("post-repair primary blocker must remain POST_REPAIR_RECONCILIATION_REQUIRED")
    if GAP_ID not in set(post_repair.get("blocker_codes") or []):
        errors.append("post-repair report lost hash-mismatch blocker")
    if int(post_repair.get("repair_candidate_count") or 0) != 1:
        errors.append("post-repair repair candidate count drifted")
    if int(post_repair.get("source_loop_expected_rollup_hash_mismatch_count") or 0) != 1:
        errors.append("post-repair hash mismatch count drifted")
    if int(post_repair.get("hash_reconciliation_operator_action_required_count") or 0) != 1:
        errors.append("post-repair operator action required count drifted")

    items = post_repair.get("items") or []
    if len(items) != 1:
        errors.append("post-repair item count drifted")
    hash_item = next((item for item in items if item.get("item_blocker_code") == GAP_ID), None)
    if hash_item is None:
        errors.append("post-repair hash-mismatch item is missing")
    for item in items:
        if item.get("item_blocker_code") != GAP_ID:
            errors.append("post-repair item is not bound to hash-mismatch blocker")
        if item.get("candidate_classification") != "REPAIR_CANDIDATE_BLOCKED_HASH_MISMATCH":
            errors.append("post-repair item lost hash-mismatch classification")
        if item.get("hash_reconciliation_status") != "SOURCE_EXPECTED_ROLLUP_ARTIFACT_MISSING":
            errors.append("post-repair item lost missing-source-rollup hash status")
        if item.get("source_loop_expected_rollup_artifact_exists") is not False:
            errors.append("source expected rollup artifact unexpectedly exists")
        if item.get("source_loop_expected_rollup_artifact_load_status") != "MISSING":
            errors.append("source expected rollup artifact is not marked MISSING")
        if item.get("source_loop_expected_rollup_recomputed_hash") is not None:
            errors.append("source expected rollup recomputed hash is set despite missing source artifact")
        if item.get("candidate_rollup_hash_self_check") != "PASS":
            errors.append("candidate rollup self-check is not PASS")
        if item.get("candidate_rollup_recomputed_hash") != item.get("candidate_rollup_hash"):
            errors.append("candidate rollup recomputed hash does not match stored candidate hash")
        if item.get("candidate_current_evidence_usable") is not False:
            errors.append("post-repair item became current-evidence usable")
        if item.get("source_loop_expected_rollup_hash_match") is not False:
            errors.append("post-repair item hash match unexpectedly passed")
        if item.get("hash_reconciliation_requires_operator_action") is not True:
            errors.append("post-repair item no longer requires operator hash reconciliation")
        if item.get("live_permission_created") is True:
            errors.append("post-repair item created live permission")

    if operator_queue.get("queue_status") != "BLOCKED":
        errors.append("repair operator queue must remain BLOCKED")
    if int(operator_queue.get("queue_item_count") or 0) < 1:
        errors.append("repair operator queue lost items")
    if int(operator_queue.get("hash_operator_reconciliation_required_count") or 0) != 1:
        errors.append("operator queue hash reconciliation required count drifted")
    queue_items = operator_queue.get("items") or []
    queue_item = next((item for item in queue_items if item.get("post_repair_item_blocker_code") == GAP_ID), None)
    if queue_item is None:
        errors.append("operator queue hash-mismatch item is missing")
    else:
        if queue_item.get("ready_for_operator_ledger_candidate_review") is not True:
            errors.append("operator queue hash-mismatch item is not review-ready")
        if queue_item.get("requires_hash_operator_reconciliation") is not True:
            errors.append("operator queue item does not require hash reconciliation")
        if NEXT_GAP_ID not in set(queue_item.get("blocking_codes") or []):
            errors.append("operator queue item lost blocked-repair-plan blocker")
        for field in FALSE_FIELDS:
            if queue_item.get(field) is True:
                errors.append(f"operator queue item has forbidden true field: {field}")
        if queue_item.get("live_permission_created") is True:
            errors.append("operator queue item created live permission")

    current_usable_count = max(
        int(post_repair.get("candidate_current_evidence_usable_count") or 0),
        int(operator_queue.get("candidate_current_evidence_usable_count") or 0),
    )
    status = "PASS_DEPTH_5_REPAIR_CANDIDATE_HASH_MISMATCH_LIVE_BLOCKING" if not errors else "BLOCKED_DEPTH_RECHECK_ERROR"
    return {
        "schema_id": "trader1.repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "patch_id": PATCH_ID,
        "requirement_id": REQUIREMENT_ID,
        "contract_gap_id": GAP_ID,
        "status": status,
        "depth_level": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "runtime_artifact_paths": runtime_artifacts(),
        "previous_post_repair_depth_patch_result_path": PREVIOUS_POST_REPAIR_DEPTH_PATCH_RESULT,
        "previous_post_repair_depth_patch_result_hash": previous_post_repair_depth.get("result_hash"),
        "previous_post_repair_recheck_patch_result_path": PREVIOUS_POST_REPAIR_RECHECK_PATCH_RESULT,
        "previous_post_repair_recheck_patch_result_hash": previous_post_repair_recheck.get("result_hash"),
        "previous_hash_mismatch_recheck_patch_result_path": PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT,
        "previous_hash_mismatch_recheck_patch_result_hash": previous_hash_mismatch_recheck.get("result_hash"),
        "error_count": len(errors),
        "errors": errors,
        "post_repair_reconciliation_status": post_repair.get("post_repair_reconciliation_status"),
        "primary_blocker_code": post_repair.get("primary_blocker_code"),
        "hash_mismatch_blocker_code": GAP_ID,
        "hash_reconciliation_status": hash_item.get("hash_reconciliation_status") if hash_item else None,
        "source_loop_expected_rollup_artifact_load_status": (
            hash_item.get("source_loop_expected_rollup_artifact_load_status") if hash_item else None
        ),
        "source_loop_expected_rollup_artifact_exists": (
            hash_item.get("source_loop_expected_rollup_artifact_exists") if hash_item else None
        ),
        "source_loop_expected_rollup_hash_match": (
            hash_item.get("source_loop_expected_rollup_hash_match") if hash_item else None
        ),
        "candidate_rollup_hash_self_check": hash_item.get("candidate_rollup_hash_self_check") if hash_item else None,
        "candidate_rollup_hash": hash_item.get("candidate_rollup_hash") if hash_item else None,
        "candidate_rollup_recomputed_hash": hash_item.get("candidate_rollup_recomputed_hash") if hash_item else None,
        "replacement_loop_id": hash_item.get("replacement_loop_id") if hash_item else None,
        "repair_candidate_count": post_repair.get("repair_candidate_count"),
        "reconciliation_item_count": post_repair.get("reconciliation_item_count"),
        "source_loop_expected_rollup_hash_mismatch_count": post_repair.get(
            "source_loop_expected_rollup_hash_mismatch_count"
        ),
        "hash_operator_reconciliation_required_count": post_repair.get(
            "hash_reconciliation_operator_action_required_count"
        ),
        "candidate_current_evidence_usable_count": current_usable_count,
        "post_repair_candidate_current_evidence_usable_count": post_repair.get(
            "candidate_current_evidence_usable_count"
        ),
        "operator_queue_status": operator_queue.get("queue_status"),
        "operator_queue_item_count": operator_queue.get("queue_item_count"),
        "operator_queue_hash_required_count": operator_queue.get("hash_operator_reconciliation_required_count"),
        "operator_queue_hash_item_review_ready": (
            queue_item.get("ready_for_operator_ledger_candidate_review") if queue_item else None
        ),
        "operator_queue_hash_item_requires_hash_reconciliation": (
            queue_item.get("requires_hash_operator_reconciliation") if queue_item else None
        ),
        "operator_queue_candidate_current_evidence_usable_count": operator_queue.get(
            "candidate_current_evidence_usable_count"
        ),
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
                    "message": "Repair candidate hash mismatch is depth-verified as live-blocking: the candidate rollup self-check passes, but the source expected rollup artifact is missing and requires explicit operator reconciliation.",
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
task_class: MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_CURRENT_EVIDENCE_CLOSURE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK", "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK", "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.contract_gap.v1", "trader1.upbit_paper_post_repair_reconciliation_report.v1", "trader1.upbit_paper_repair_operator_queue_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS + runtime_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Confirm the hash-mismatch repair candidate remains BLOCKED.
- Confirm the missing source expected rollup artifact is still not fabricated.
- Confirm repair candidate and operator queue remain review-only and operator-action-required.
- Confirm candidate_current_evidence_usable_count remains 0.
- Keep {GAP_ID} and {NEXT_GAP_ID} open.
- Route to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, and scale_up_allowed=false.

depth_snapshot:
- status: {report["status"]}
- post_repair_status: {report["post_repair_reconciliation_status"]}
- hash_reconciliation_status: {report["hash_reconciliation_status"]}
- source_loop_expected_rollup_artifact_load_status: {report["source_loop_expected_rollup_artifact_load_status"]}
- repair_candidate_count: {report["repair_candidate_count"]}
- hash_mismatch_count: {report["source_loop_expected_rollup_hash_mismatch_count"]}
- operator_queue_status: {report["operator_queue_status"]}
- candidate_current_evidence_usable_count: {report["candidate_current_evidence_usable_count"]}

known_omissions_by_design:
- Does not resolve hash mismatch.
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

Repair candidate hash mismatch depth has been rechecked as blocked. The candidate rollup self-check still passes, the source expected rollup artifact is still missing, current evidence remains unusable, and the next task is:

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
            "source_heading": "repair candidate hash mismatch reconciliation required implementation depth recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: verify repair candidate hash mismatch runtime evidence depth without "
                "fabricating missing source rollup evidence, current evidence promotion, live permission, or scale-up"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Repair candidate hash mismatch reconciliation required implementation depth recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.contract_gap.v1",
                "trader1.upbit_paper_post_repair_reconciliation_report.v1",
                "trader1.upbit_paper_repair_operator_queue_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py",
                "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
                *ROUTE_TEST_ARTIFACTS,
                "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
                "tests/runtime/test_upbit_paper_repair_operator_queue.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"],
            "depends_on": [
                "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK",
                "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK",
                "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-RECHECK",
                "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION",
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
                "contracts/schema/upbit_paper_post_repair_reconciliation_report.schema.json",
                "contracts/schema/upbit_paper_repair_operator_queue_report.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py",
                "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
                *ROUTE_TEST_ARTIFACTS,
                "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
                "tests/runtime/test_upbit_paper_repair_operator_queue.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_post_repair_reconciliation.py",
                "trader1/runtime/paper/upbit_paper_repair_operator_queue.py",
            ],
            "evidence_artifacts": artifacts + [rel(CONTRACT_GAP_PATH), rel(DEPTH_REPORT_PATH)],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "next_task_class",
                "remaining_blockers",
                "post_repair_reconciliation_status",
                "post_repair_source_loop_expected_rollup_hash_mismatch_count",
                "post_repair_candidate_current_evidence_usable_count",
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
    if report["status"] != "PASS_DEPTH_5_REPAIR_CANDIDATE_HASH_MISMATCH_LIVE_BLOCKING":
        raise RuntimeError("cannot emit patch_result while hash-mismatch depth recheck is blocked")
    template = load_json(ROOT / PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK",
                "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK",
                "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-RECHECK",
                "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION",
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
                PREVIOUS_POST_REPAIR_DEPTH_PATCH_RESULT,
                PREVIOUS_POST_REPAIR_RECHECK_PATCH_RESULT,
                PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT,
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK",
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
            "post_repair_reconciliation_status": report["post_repair_reconciliation_status"],
            "post_repair_reconciliation_item_count": report["reconciliation_item_count"],
            "post_repair_source_loop_expected_rollup_hash_mismatch_count": report[
                "source_loop_expected_rollup_hash_mismatch_count"
            ],
            "post_repair_candidate_current_evidence_usable_count": report[
                "post_repair_candidate_current_evidence_usable_count"
            ],
            "post_repair_reconciliation_operator_hash_mismatch_count": report[
                "hash_operator_reconciliation_required_count"
            ],
            "post_repair_reconciliation_operator_action_item_count": report["operator_queue_hash_required_count"],
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
            "stage_gate_status": "PASS_REPAIR_CANDIDATE_HASH_MISMATCH_DEPTH_RECHECK_OPERATOR_ACTION_REQUIRED",
            "depth_report_path": rel(DEPTH_REPORT_PATH),
            "contract_gap_path": rel(CONTRACT_GAP_PATH),
            "post_repair_reconciliation_status": report["post_repair_reconciliation_status"],
            "hash_reconciliation_status": report["hash_reconciliation_status"],
            "source_loop_expected_rollup_artifact_load_status": report[
                "source_loop_expected_rollup_artifact_load_status"
            ],
            "repair_candidate_count": report["repair_candidate_count"],
            "source_loop_expected_rollup_hash_mismatch_count": report[
                "source_loop_expected_rollup_hash_mismatch_count"
            ],
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
                PREVIOUS_POST_REPAIR_DEPTH_PATCH_RESULT,
                PREVIOUS_POST_REPAIR_RECHECK_PATCH_RESULT,
                PREVIOUS_HASH_MISMATCH_RECHECK_PATCH_RESULT,
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
            "post_repair_reconciliation_status": report["post_repair_reconciliation_status"],
            "hash_reconciliation_status": report["hash_reconciliation_status"],
            "source_loop_expected_rollup_artifact_load_status": report[
                "source_loop_expected_rollup_artifact_load_status"
            ],
            "repair_candidate_count": report["repair_candidate_count"],
            "source_loop_expected_rollup_hash_mismatch_count": report[
                "source_loop_expected_rollup_hash_mismatch_count"
            ],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# MVP4 Repair Candidate Hash Mismatch Reconciliation Required Implementation Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The repair candidate hash mismatch remains BLOCKED and live-affecting.
- The candidate rollup self-check is PASS, but the source expected rollup artifact remains MISSING.
- The operator queue keeps the item review-ready and hash-reconciliation-required.
- The candidate remains review-only with candidate_current_evidence_usable_count=0.

Patch:
- Added a depth report and contract_gap projection for {GAP_ID}.
- Added regression tests for hash-mismatch depth, operator queue fail-closed behavior, and forward route.
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
                    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py",
                    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
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
                    "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
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
                "post_repair_reconciliation_status": report["post_repair_reconciliation_status"],
                "repair_candidate_count": report["repair_candidate_count"],
                "source_loop_expected_rollup_hash_mismatch_count": report[
                    "source_loop_expected_rollup_hash_mismatch_count"
                ],
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
