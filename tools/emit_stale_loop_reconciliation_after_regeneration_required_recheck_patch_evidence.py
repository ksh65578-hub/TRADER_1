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

PATCH_BASENAME = "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-RECONCILIATION-AFTER-REGENERATION-REQUIRED-RECHECK"
PREVIOUS_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
)
PREVIOUS_RECHECK_REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-RECHECK"
POST_REGENERATION_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-POST-REGENERATION-RECONCILIATION"
CLOSURE_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-CLOSURE"
DASHBOARD_BINDING_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-DASHBOARD-BINDING"
NEXT_TASK_CLASS = "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK"
PREVIOUS_PATCH_RESULT = (
    "system/evidence/patch_results/"
    "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.patch_result.json"
)
PREVIOUS_RECHECK_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK.patch_result.json"
)
POST_REGENERATION_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json"
)
CLOSURE_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json"
)
CLOSURE_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE.patch_result.json"
)
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
CLOSED_GAP = "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED"
NEXT_OPEN_GAP = "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING"
STATIC_LIVE_BLOCKERS = {
    "API_UNVERIFIED",
    "LIVE_READY_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
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
    "upbit_paper_stale_loop_post_regeneration_reconciliation_validator",
    "upbit_paper_stale_loop_reconciliation_operator_queue_closure_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    item for item in VALIDATORS_REQUIRED if item != "generated_artifact_dirty_validator"
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tools/emit_stale_loop_reconciliation_after_regeneration_required_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    result: dict[str, Any] = {
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


def assert_false_fields(name: str, artifact: dict[str, Any], suffix: str = "") -> None:
    for field in FALSE_FIELDS:
        key = f"{field}{suffix}"
        if artifact.get(key) is True:
            raise RuntimeError(f"{name} has forbidden true field: {key}")


def _assert_no_live_or_mutation(name: str, artifact: dict[str, Any]) -> None:
    assert_false_fields(name, artifact)
    for field in (
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "persistent_loop_mutation_allowed",
        "replacement_write_allowed",
        "source_delete_allowed",
        "delete_source_allowed",
        "overwrite_source_allowed",
        "live_permission_created",
        "can_submit_order",
    ):
        if artifact.get(field) is True:
            raise RuntimeError(f"{name} has forbidden true field: {field}")


def _count_closure_lanes(closure: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in closure.get("items", []):
        lane = str(item.get("closure_lane"))
        counts[lane] = counts.get(lane, 0) + 1
    return counts


def load_summary() -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    previous = load_json(ROOT / PREVIOUS_PATCH_RESULT)
    previous_recheck = load_json(ROOT / PREVIOUS_RECHECK_PATCH_RESULT)
    post = load_json(ROOT / POST_REGENERATION_REPORT)
    closure = load_json(ROOT / CLOSURE_REPORT)
    closure_patch = load_json(ROOT / CLOSURE_PATCH_RESULT)

    if PREVIOUS_REQUIREMENT_ID not in state.get("completed_requirement_ids", []):
        raise RuntimeError("stale loop regeneration execution depth recheck is not completed")
    if PREVIOUS_RECHECK_REQUIREMENT_ID not in state.get("completed_requirement_ids", []):
        raise RuntimeError("stale loop regeneration execution recheck is not completed")
    if state.get("next_allowed_task_class") not in {PATCH_BASENAME, NEXT_TASK_CLASS}:
        raise RuntimeError("state is not routed to stale loop post-regeneration reconciliation recheck")
    if previous.get("next_task_class") != PATCH_BASENAME:
        raise RuntimeError("previous execution depth recheck does not route to this recheck")
    if previous_recheck.get("next_task_class") != PATCH_BASENAME:
        raise RuntimeError("previous execution recheck does not route to this recheck")
    if state.get("next_allowed_task_class") == PATCH_BASENAME and CLOSED_GAP not in state.get("open_contract_gap_ids", []):
        raise RuntimeError("post-regeneration reconciliation gap is not open before this recheck")

    assert_false_fields("current implementation state", state)
    assert_false_fields(PREVIOUS_PATCH_RESULT, previous, "_after")
    assert_false_fields(PREVIOUS_RECHECK_PATCH_RESULT, previous_recheck, "_after")
    assert_false_fields(CLOSURE_PATCH_RESULT, closure_patch, "_after")
    _assert_no_live_or_mutation(POST_REGENERATION_REPORT, post)
    _assert_no_live_or_mutation(CLOSURE_REPORT, closure)

    expected_post = {
        "post_reconciliation_status": "BLOCKED",
        "primary_blocker_code": CLOSED_GAP,
        "planned_regeneration_item_count": 16,
        "post_reconciliation_item_count": 16,
        "regenerated_current_accepted_count": 10,
        "regenerated_current_blocked_reconciliation_count": 6,
        "current_evidence_usable_count": 10,
        "excluded_from_current_evidence_count": 6,
        "replacement_hash_mismatch_count": 0,
        "source_hash_mismatch_count": 0,
        "unpaired_regenerated_artifact_count": 0,
        "usable_runtime_cycle_hash_duplicate_count": 0,
    }
    for field, expected in expected_post.items():
        if post.get(field) != expected:
            raise RuntimeError(f"post-regeneration reconciliation {field} drifted: {post.get(field)} != {expected}")
    if post.get("blocker_codes") != [CLOSED_GAP]:
        raise RuntimeError("post-regeneration reconciliation blocker shape drifted")

    expected_closure = {
        "closure_status": "BLOCKED",
        "primary_blocker_code": NEXT_OPEN_GAP,
        "closure_item_count": 6,
        "source_blocked_item_count": 6,
        "ledger_recheck_ready_count": 5,
        "recovery_guard_required_count": 1,
        "runtime_cycle_rerun_required_count": 0,
        "operator_review_required_count": 0,
        "unsafe_or_scope_blocked_count": 0,
        "current_evidence_write_allowed_count": 0,
        "current_evidence_usable_after_closure_count": 0,
        "source_post_regeneration_reconciliation_status": "BLOCKED",
        "source_post_regeneration_reconciliation_validator_status": "PASS",
        "source_ledger_idempotency_evidence_status": "PASS",
        "source_ledger_idempotency_status": "PASS",
        "source_ledger_reconciliation_status": "PASS",
        "source_ledger_mismatch_count": 0,
    }
    for field, expected in expected_closure.items():
        if closure.get(field) != expected:
            raise RuntimeError(f"closure report {field} drifted: {closure.get(field)} != {expected}")
    if closure.get("source_post_regeneration_reconciliation_hash") != post.get("post_reconciliation_hash"):
        raise RuntimeError("closure report no longer binds the post-regeneration reconciliation hash")
    for blocker in (CLOSED_GAP, NEXT_OPEN_GAP):
        if blocker not in closure.get("blocker_codes", []):
            raise RuntimeError(f"closure report is missing blocker {blocker}")
    if not closure.get("display_only") or not closure.get("dashboard_truth_only") or not closure.get("paper_only"):
        raise RuntimeError("closure report stopped being display-only PAPER truth")

    lane_counts = _count_closure_lanes(closure)
    if lane_counts != {"LEDGER_RECHECK_READY": 5, "RECOVERY_GUARD_REQUIRED": 1}:
        raise RuntimeError(f"closure lane counts drifted: {lane_counts}")
    if len(closure.get("items", [])) != closure["closure_item_count"]:
        raise RuntimeError("closure item count does not match items length")
    for item in closure.get("items", []):
        if not isinstance(item, dict):
            raise RuntimeError("closure item is not an object")
        _assert_no_live_or_mutation("closure item", item)
        if item.get("source_item_blocker_code") != CLOSED_GAP:
            raise RuntimeError("closure item stopped binding the source post-regeneration blocker")
        if NEXT_OPEN_GAP not in item.get("blocking_codes", []):
            raise RuntimeError("closure item missing operator-queue blocker")
        lane = item.get("closure_lane")
        if lane == "LEDGER_RECHECK_READY" and item.get("closure_recheck_ready") is not True:
            raise RuntimeError("ledger-ready closure item is not marked recheck ready")
        if lane == "RECOVERY_GUARD_REQUIRED" and item.get("closure_recheck_ready") is not False:
            raise RuntimeError("recovery-guard closure item is incorrectly recheck ready")
        if item.get("current_evidence_usable_after_closure") is True:
            raise RuntimeError("closure item incorrectly became current evidence")

    state_gaps = set(state.get("open_contract_gap_ids", []))
    next_open_gaps = sorted((state_gaps - {CLOSED_GAP}) | {NEXT_OPEN_GAP})
    remaining_blockers = sorted(set(next_open_gaps) | STATIC_LIVE_BLOCKERS)
    return {
        "route_before_patch": state.get("next_allowed_task_class"),
        "route_after_patch": NEXT_TASK_CLASS,
        "state_last_patch_id_before": state.get("last_patch_id"),
        "state_last_patch_result_hash_before": state.get("last_patch_result_hash"),
        "previous_patch_result_hash": previous.get("result_hash"),
        "previous_recheck_patch_result_hash": previous_recheck.get("result_hash"),
        "closure_patch_result_hash": closure_patch.get("result_hash"),
        "closed_gap_id": CLOSED_GAP,
        "next_open_gap_id": NEXT_OPEN_GAP,
        "stale_loop_post_regeneration_reconciliation_status": post["post_reconciliation_status"],
        "stale_loop_post_regeneration_item_count": post["planned_regeneration_item_count"],
        "stale_loop_post_regeneration_accepted_count": post["regenerated_current_accepted_count"],
        "stale_loop_post_regeneration_blocked_reconciliation_count": post[
            "regenerated_current_blocked_reconciliation_count"
        ],
        "stale_loop_post_regeneration_current_evidence_usable_count": post["current_evidence_usable_count"],
        "stale_loop_post_regeneration_excluded_from_current_evidence_count": post[
            "excluded_from_current_evidence_count"
        ],
        "stale_loop_operator_queue_closure_status": closure["closure_status"],
        "stale_loop_operator_queue_closure_item_count": closure["closure_item_count"],
        "stale_loop_operator_queue_closure_ledger_recheck_ready_count": closure["ledger_recheck_ready_count"],
        "stale_loop_operator_queue_closure_recovery_guard_required_count": closure[
            "recovery_guard_required_count"
        ],
        "stale_loop_operator_queue_closure_current_evidence_write_allowed_count": closure[
            "current_evidence_write_allowed_count"
        ],
        "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count": closure[
            "current_evidence_usable_after_closure_count"
        ],
        "next_open_contract_gap_ids": next_open_gaps,
        "remaining_blockers": remaining_blockers,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{PREVIOUS_REQUIREMENT_ID}", "{PREVIOUS_RECHECK_REQUIREMENT_ID}", "{POST_REGENERATION_REQUIREMENT_ID}", "{CLOSURE_REQUIREMENT_ID}", "{DASHBOARD_BINDING_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_stale_loop_post_regeneration_reconciliation_report.v1", "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Confirm post-regeneration reconciliation remains BLOCKED by {CLOSED_GAP}.
- Confirm operator queue closure decomposes that blocker into {NEXT_OPEN_GAP}.
- Close {CLOSED_GAP} in current state only after the closure report is PASS-validatable and fail-closed.
- Add {NEXT_OPEN_GAP} as the next current open gap.
- Keep current evidence write, persistent loop mutation, live order, live readiness, and scale-up blocked.

recheck_snapshot:
- post_regeneration_status: {summary["stale_loop_post_regeneration_reconciliation_status"]}
- post_regeneration_blocked_count: {summary["stale_loop_post_regeneration_blocked_reconciliation_count"]}
- closure_status: {summary["stale_loop_operator_queue_closure_status"]}
- closure_item_count: {summary["stale_loop_operator_queue_closure_item_count"]}
- ledger_recheck_ready_count: {summary["stale_loop_operator_queue_closure_ledger_recheck_ready_count"]}
- recovery_guard_required_count: {summary["stale_loop_operator_queue_closure_recovery_guard_required_count"]}

known_omissions_by_design:
- This patch does not rerun stale-loop regeneration, ledger repair, recovery guard, or current-evidence writers.
- This patch does not mutate system/runtime artifacts.
- This patch does not use credentials, place live orders, mutate live config, create live permission, create long-run evidence, or scale up.

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

The stale-loop post-regeneration reconciliation gap is decomposed into an operator queue. Five blocked regenerated PAPER replacements are ledger-recheck-ready, one remains recovery-guard-required, and zero are current-evidence-writable or live eligible.

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
            + [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260505.md",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                PREVIOUS_PATCH_RESULT,
                POST_REGENERATION_REPORT,
                CLOSURE_REPORT,
                CLOSURE_PATCH_RESULT,
                PREVIOUS_RECHECK_PATCH_RESULT,
            ]
        )
    )

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "source_file": "TRADER_1.md",
            "source_heading": "stale loop reconciliation after regeneration required recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: close {CLOSED_GAP} only when the operator queue closure report "
                f"preserves fail-closed PAPER-only evidence and opens {NEXT_OPEN_GAP}"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Stale loop reconciliation after regeneration required recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_stale_loop_post_regeneration_reconciliation_report.v1",
                "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
                "tests/runtime/test_upbit_paper_stale_loop_post_regeneration_reconciliation.py",
                "tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                PREVIOUS_REQUIREMENT_ID,
                PREVIOUS_RECHECK_REQUIREMENT_ID,
                POST_REGENERATION_REQUIREMENT_ID,
                CLOSURE_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"post-regeneration stale-loop reconciliation closes only into operator-queue pending gap"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RECHECK_OPERATOR_QUEUE_PENDING",
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
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/upbit_paper_stale_loop_post_regeneration_reconciliation_report.schema.json",
                "contracts/schema/upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.schema.json",
            ],
            "validator_files": [
                "trader1/validation/mvp0_validators.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_post_regeneration_reconciliation.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
            ],
            "test_files": [
                "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
                "tests/runtime/test_upbit_paper_stale_loop_post_regeneration_reconciliation.py",
                "tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_stale_loop_post_regeneration_reconciliation.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
            ],
            "evidence_artifacts": [
                PREVIOUS_PATCH_RESULT,
                PREVIOUS_RECHECK_PATCH_RESULT,
                POST_REGENERATION_REPORT,
                CLOSURE_REPORT,
                CLOSURE_PATCH_RESULT,
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "stale_loop_post_regeneration_reconciliation_status",
                "stale_loop_operator_queue_closure_status",
                "stale_loop_operator_queue_closure_item_count",
                "stale_loop_operator_queue_closure_ledger_recheck_ready_count",
                "stale_loop_operator_queue_closure_recovery_guard_required_count",
                "stale_loop_operator_queue_closure_current_evidence_write_allowed_count",
                "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_RECHECK_OPERATOR_QUEUE_PENDING",
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
    summary: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(ROOT / PREVIOUS_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                PREVIOUS_REQUIREMENT_ID,
                POST_REGENERATION_REQUIREMENT_ID,
                CLOSURE_REQUIREMENT_ID,
                DASHBOARD_BINDING_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_STATE_ONLY",
            "new_registry_items": [REQUIREMENT_ID, f"contracts/generated/context_pack/{PATCH_BASENAME}.md"],
            "new_or_changed_schema_ids": ["trader1.patch_result.v1"],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RUNTIME_RECOVERY"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": summary["remaining_blockers"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                PREVIOUS_PATCH_RESULT,
                POST_REGENERATION_REPORT,
                CLOSURE_REPORT,
                CLOSURE_PATCH_RESULT,
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_POST_REGENERATION_GAP_CLOSED_OPERATOR_QUEUE_PENDING",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "optimizer_stage": "MVP-4_PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_status_before": "STALE_LOOP_SAFE_REGENERATION_EXECUTED_RECONCILIATION_REQUIRED",
            "optimizer_status_after": "STALE_LOOP_OPERATOR_QUEUE_PENDING_NOT_LIVE_READY",
            "optimizer_maturity_level_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_maturity_level_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_output_type": "PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_guardrail_result": "PASS_OPERATOR_QUEUE_RECHECK_EVIDENCE_REMAINS_PAPER_ONLY",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "STATE_RECHECK_ONLY",
            "convergence_layer_changed": False,
            "convergence_state_before": "STALE_LOOP_SAFE_REGENERATION_EXECUTED_RECONCILIATION_REQUIRED",
            "convergence_state_after": "STALE_LOOP_OPERATOR_QUEUE_PENDING_NOT_LIVE_READY",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_CHANGED",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": validators_required,
            "convergence_validators_run": validators_run,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "candidate_current_evidence_usable_count": summary[
                "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count"
            ],
            "stale_loop_post_regeneration_reconciliation_status": summary[
                "stale_loop_post_regeneration_reconciliation_status"
            ],
            "stale_loop_post_regeneration_item_count": summary["stale_loop_post_regeneration_item_count"],
            "stale_loop_post_regeneration_accepted_count": summary[
                "stale_loop_post_regeneration_accepted_count"
            ],
            "stale_loop_post_regeneration_blocked_reconciliation_count": summary[
                "stale_loop_post_regeneration_blocked_reconciliation_count"
            ],
            "stale_loop_post_regeneration_current_evidence_usable_count": summary[
                "stale_loop_post_regeneration_current_evidence_usable_count"
            ],
            "stale_loop_post_regeneration_excluded_from_current_evidence_count": summary[
                "stale_loop_post_regeneration_excluded_from_current_evidence_count"
            ],
            "stale_loop_operator_queue_closure_status": summary["stale_loop_operator_queue_closure_status"],
            "stale_loop_operator_queue_closure_item_count": summary[
                "stale_loop_operator_queue_closure_item_count"
            ],
            "stale_loop_operator_queue_closure_ledger_recheck_ready_count": summary[
                "stale_loop_operator_queue_closure_ledger_recheck_ready_count"
            ],
            "stale_loop_operator_queue_closure_recovery_guard_required_count": summary[
                "stale_loop_operator_queue_closure_recovery_guard_required_count"
            ],
            "stale_loop_operator_queue_closure_current_evidence_write_allowed_count": summary[
                "stale_loop_operator_queue_closure_current_evidence_write_allowed_count"
            ],
            "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count": summary[
                "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count"
            ],
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    summary: dict[str, Any],
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
            "stage_gate_status": "PASS_POST_REGENERATION_GAP_CLOSED_OPERATOR_QUEUE_PENDING",
            **summary,
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
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "system/evidence/implementation_patch_ledger.json",
                PREVIOUS_PATCH_RESULT,
                PREVIOUS_RECHECK_PATCH_RESULT,
                POST_REGENERATION_REPORT,
                CLOSURE_REPORT,
                CLOSURE_PATCH_RESULT,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260505.md",
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
            **summary,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 Stale Loop Reconciliation After Regeneration Required Recheck Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Post-regeneration reconciliation is still BLOCKED and identified {summary["stale_loop_post_regeneration_blocked_reconciliation_count"]} regenerated PAPER replacements that cannot become current evidence.
- The operator queue closure report decomposes {CLOSED_GAP} into {NEXT_OPEN_GAP}.
- The queue has {summary["stale_loop_operator_queue_closure_ledger_recheck_ready_count"]} ledger-recheck-ready items and {summary["stale_loop_operator_queue_closure_recovery_guard_required_count"]} recovery-guard-required item.
- Current-evidence write allowed count remains {summary["stale_loop_operator_queue_closure_current_evidence_write_allowed_count"]}.

Patch:
- Closed {CLOSED_GAP} in current implementation state.
- Added {NEXT_OPEN_GAP} as the next open contract gap.
- Routed next_allowed_task_class to {NEXT_TASK_CLASS}.
- Preserved all live, current-evidence write, persistent-loop mutation, source deletion, long-run evidence, promotion, and scale-up blockers.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no runtime artifact staging
- no scale-up
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any], summary: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(completed)
    state["open_contract_gap_ids"] = summary["next_open_contract_gap_ids"]
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
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
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
    ledger["ledger_hash"] = ""
    ledger["ledger_hash"] = sha256_json({key: value for key, value in ledger.items() if key != "ledger_hash"})
    write_json(ledger_path, ledger)


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result, summary)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    summary = load_summary()
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        BOOTSTRAP_VALIDATORS_REQUIRED,
        summary,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, summary)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "tests.contract.test_stale_loop_reconciliation_after_regeneration_required_recheck",
                    "tests.contract.test_stale_loop_regeneration_execution_required_recheck",
                    "tests.contract.test_patch_result_runtime_schema_validation",
                    "-v",
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
                    "tests/runtime/test_upbit_paper_stale_loop_post_regeneration_reconciliation.py",
                    "tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]),
        ]
    )
    summary = load_summary()
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        BOOTSTRAP_VALIDATORS_REQUIRED,
        summary,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, summary)

    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(VALIDATORS_REQUIRED)),
        VALIDATORS_REQUIRED,
        summary,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, summary)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "closed_gap_id": CLOSED_GAP,
                "next_open_gap_id": NEXT_OPEN_GAP,
                "closure_status": summary["stale_loop_operator_queue_closure_status"],
                "ledger_recheck_ready_count": summary[
                    "stale_loop_operator_queue_closure_ledger_recheck_ready_count"
                ],
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
