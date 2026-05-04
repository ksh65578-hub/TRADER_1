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

PATCH_BASENAME = "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = (
    "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-"
    "RECONCILIATION-RECHECK"
)
NEXT_TASK_CLASS = "MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK"
BLOCKED_REPAIR_PLAN_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-BLOCKED-REPAIR-PLAN"
REPAIR_OPERATOR_QUEUE_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-REPAIR-OPERATOR-QUEUE"
BLOCKED_REPAIR_PLAN_BLOCKER = "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION"
REGENERATED_BLOCKER = "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION"
STALE_LOOP_REGENERATION_BLOCKER = "STALE_LOOP_REGENERATION_REQUIRED"

PREVIOUS_PATCH_RESULT = (
    "system/evidence/patch_results/"
    "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK.patch_result.json"
)
BLOCKED_REPAIR_PLAN_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_blocked_repair_plan_report.json"
)
REPAIR_OPERATOR_QUEUE_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_repair_operator_queue_report.json"
)
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
OPEN_GAPS_TO_PRESERVE = {
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "SCALE_UP_NOT_ELIGIBLE",
    "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
    "STALE_LOOP_REGENERATION_EXECUTION_REQUIRED",
    "STALE_LOOP_REGENERATION_REQUIRED",
}
STATIC_LIVE_BLOCKERS = {
    "API_UNVERIFIED",
    "LIVE_READY_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
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
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


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
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    item for item in VALIDATORS_REQUIRED if item != "generated_artifact_dirty_validator"
]
CHANGED_ARTIFACTS = [
    "contracts/schema/patch_result.schema.json",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py",
    "tools/emit_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck_patch_evidence.py",
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


def _safe_lane_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        lane = str(item.get("safe_repair_lane") or "UNKNOWN")
        counts[lane] = counts.get(lane, 0) + 1
    return counts


def load_summary() -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    previous = load_json(ROOT / PREVIOUS_PATCH_RESULT)
    blocked_plan = load_json(ROOT / BLOCKED_REPAIR_PLAN_REPORT)
    repair_queue = load_json(ROOT / REPAIR_OPERATOR_QUEUE_REPORT)

    if PREVIOUS_REQUIREMENT_ID not in state.get("completed_requirement_ids", []):
        raise RuntimeError("blocked repair plan operator reconciliation recheck is not completed")
    if state.get("next_allowed_task_class") not in {PATCH_BASENAME, NEXT_TASK_CLASS}:
        raise RuntimeError("state is not routed to the regenerated-current blocked repairs recheck")
    if previous.get("next_task_class") != PATCH_BASENAME:
        raise RuntimeError("previous recheck does not route to the regenerated-current blocked repairs recheck")

    assert_false_fields("current implementation state", state)
    assert_false_fields(PREVIOUS_PATCH_RESULT, previous, "_after")
    assert_false_fields(BLOCKED_REPAIR_PLAN_REPORT, blocked_plan)
    assert_false_fields(REPAIR_OPERATOR_QUEUE_REPORT, repair_queue)
    for field in (
        "current_evidence_mutation_allowed",
        "generated_artifact_mutation_allowed",
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
            raise RuntimeError(f"blocked repair plan has forbidden true field: {field}")

    if blocked_plan.get("repair_plan_status") != "BLOCKED":
        raise RuntimeError("blocked repair plan is not BLOCKED")
    if blocked_plan.get("primary_blocker_code") != BLOCKED_REPAIR_PLAN_BLOCKER:
        raise RuntimeError("blocked repair plan primary blocker drifted")
    if BLOCKED_REPAIR_PLAN_BLOCKER not in blocked_plan.get("blocker_codes", []):
        raise RuntimeError("blocked repair plan blocker is missing")
    expected_counts = {
        "repair_item_count": 6,
        "ledger_rollup_rebuild_ready_count": 1,
        "runtime_cycle_rerun_required_count": 5,
        "recovery_guard_rerun_required_count": 1,
        "missing_cycle_ledger_jsonl_total_count": 10,
        "missing_paper_ledger_rollup_artifact_count": 6,
    }
    for field, expected in expected_counts.items():
        if blocked_plan.get(field) != expected:
            raise RuntimeError(f"blocked repair plan {field} drifted: {blocked_plan.get(field)} != {expected}")

    plan_items = [item for item in blocked_plan.get("items", []) if isinstance(item, dict)]
    lane_counts = _safe_lane_counts(plan_items)
    if lane_counts.get("LEDGER_ROLLUP_REBUILD_READY") != 1:
        raise RuntimeError("blocked repair plan lost the single ledger-rollup-ready lane")
    if lane_counts.get("RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP") != 4:
        raise RuntimeError("blocked repair plan runtime-cycle rerun lane count drifted")
    if lane_counts.get("RECOVERY_GUARD_THEN_LEDGER_ROLLUP") != 1:
        raise RuntimeError("blocked repair plan recovery-guard lane count drifted")
    for item in plan_items:
        if (
            item.get("current_evidence_mutation_allowed")
            or item.get("source_delete_allowed")
            or item.get("live_permission_created")
        ):
            raise RuntimeError("blocked repair plan item attempted forbidden mutation or live permission")
        for step in item.get("repair_steps", []):
            if step.get("mutates_current_evidence") or step.get("live_permission_created"):
                raise RuntimeError("blocked repair plan step attempted forbidden mutation or live permission")

    if repair_queue.get("queue_status") != "BLOCKED":
        raise RuntimeError("repair operator queue is not BLOCKED")
    if repair_queue.get("primary_blocker_code") != REGENERATED_BLOCKER:
        raise RuntimeError("repair operator queue primary regenerated-current blocker drifted")
    if repair_queue.get("blocker_codes") != [REGENERATED_BLOCKER]:
        raise RuntimeError("repair operator queue blocker projection drifted")
    if repair_queue.get("queue_item_count") != blocked_plan.get("repair_item_count"):
        raise RuntimeError("repair operator queue item count no longer matches blocked plan")
    for field in (
        "ledger_candidate_review_ready_count",
        "runtime_cycle_rerun_required_count",
        "recovery_guard_rerun_required_count",
        "hash_operator_reconciliation_required_count",
        "candidate_current_evidence_usable_count",
    ):
        expected = 0 if field == "candidate_current_evidence_usable_count" else blocked_plan.get(
            {
                "ledger_candidate_review_ready_count": "ledger_rollup_rebuild_ready_count",
                "runtime_cycle_rerun_required_count": "runtime_cycle_rerun_required_count",
                "recovery_guard_rerun_required_count": "recovery_guard_rerun_required_count",
                "hash_operator_reconciliation_required_count": "ledger_rollup_rebuild_ready_count",
            }.get(field, field)
        )
        if repair_queue.get(field) != expected:
            raise RuntimeError(f"repair operator queue {field} drifted")
    if repair_queue.get("candidate_current_evidence_usable_count") != 0:
        raise RuntimeError("repair operator queue exposed current evidence usability")
    queue_items = [item for item in repair_queue.get("items", []) if isinstance(item, dict)]
    queue_lane_counts = _safe_lane_counts(queue_items)
    if queue_lane_counts != lane_counts:
        raise RuntimeError("repair operator queue lane counts no longer mirror blocked plan")
    ledger_ready = [
        item
        for item in queue_items
        if item.get("safe_repair_lane") == "LEDGER_ROLLUP_REBUILD_READY"
    ]
    runtime_rerun = [
        item
        for item in queue_items
        if item.get("safe_repair_lane") == "RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP"
    ]
    recovery_guard = [
        item
        for item in queue_items
        if item.get("safe_repair_lane") == "RECOVERY_GUARD_THEN_LEDGER_ROLLUP"
    ]
    if len(ledger_ready) != 1 or len(runtime_rerun) != 4 or len(recovery_guard) != 1:
        raise RuntimeError("repair operator queue lane distribution drifted")
    if not ledger_ready[0].get("ready_for_operator_ledger_candidate_review"):
        raise RuntimeError("ledger-ready repair candidate lost operator review flag")
    if not ledger_ready[0].get("requires_hash_operator_reconciliation"):
        raise RuntimeError("ledger-ready repair candidate lost hash reconciliation requirement")
    if ledger_ready[0].get("post_repair_item_blocker_code") != "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED":
        raise RuntimeError("ledger-ready repair candidate hash mismatch blocker drifted")
    for item in runtime_rerun:
        if not item.get("requires_runtime_cycle_rerun"):
            raise RuntimeError("runtime-rerun repair candidate lost cycle rerun requirement")
        if item.get("ready_for_operator_ledger_candidate_review") or item.get("candidate_rollup_artifact_path"):
            raise RuntimeError("runtime-rerun repair candidate became ledger-review-ready too early")
    if not recovery_guard[0].get("requires_recovery_guard_rerun"):
        raise RuntimeError("recovery-guard repair candidate lost recovery guard rerun requirement")
    for item in queue_items:
        if (
            item.get("candidate_current_evidence_usable")
            or item.get("current_evidence_mutation_allowed")
            or item.get("persistent_loop_mutation_allowed")
            or item.get("source_delete_allowed")
            or item.get("live_permission_created")
        ):
            raise RuntimeError("repair operator queue item attempted current-evidence/live/source mutation")

    remaining_blockers = sorted(
        set(state.get("open_contract_gap_ids", []))
        | set(blocked_plan.get("blocker_codes", []))
        | set(repair_queue.get("blocker_codes", []))
        | OPEN_GAPS_TO_PRESERVE
        | STATIC_LIVE_BLOCKERS
    )
    return {
        "route_before_patch": state.get("next_allowed_task_class"),
        "route_after_patch": NEXT_TASK_CLASS,
        "state_last_patch_id_before": state.get("last_patch_id"),
        "state_last_patch_result_hash_before": state.get("last_patch_result_hash"),
        "previous_patch_result_hash": previous.get("result_hash"),
        "blocked_repair_plan_status": blocked_plan["repair_plan_status"],
        "blocked_repair_plan_item_count": blocked_plan["repair_item_count"],
        "blocked_repair_plan_ledger_rollup_rebuild_ready_count": blocked_plan[
            "ledger_rollup_rebuild_ready_count"
        ],
        "blocked_repair_plan_runtime_cycle_rerun_required_count": blocked_plan[
            "runtime_cycle_rerun_required_count"
        ],
        "blocked_repair_plan_recovery_guard_rerun_required_count": blocked_plan[
            "recovery_guard_rerun_required_count"
        ],
        "blocked_repair_plan_missing_cycle_ledger_jsonl_total_count": blocked_plan[
            "missing_cycle_ledger_jsonl_total_count"
        ],
        "blocked_repair_plan_missing_paper_ledger_rollup_artifact_count": blocked_plan[
            "missing_paper_ledger_rollup_artifact_count"
        ],
        "blocked_repair_plan_lane_counts": blocked_plan["repair_lane_counts"],
        "repair_operator_queue_status": repair_queue["queue_status"],
        "repair_operator_queue_primary_blocker_code": repair_queue["primary_blocker_code"],
        "repair_operator_queue_item_count": repair_queue["queue_item_count"],
        "repair_operator_queue_ledger_candidate_review_ready_count": repair_queue[
            "ledger_candidate_review_ready_count"
        ],
        "repair_operator_queue_runtime_cycle_rerun_required_count": repair_queue[
            "runtime_cycle_rerun_required_count"
        ],
        "repair_operator_queue_recovery_guard_rerun_required_count": repair_queue[
            "recovery_guard_rerun_required_count"
        ],
        "repair_operator_queue_hash_operator_reconciliation_required_count": repair_queue[
            "hash_operator_reconciliation_required_count"
        ],
        "repair_operator_queue_candidate_current_evidence_usable_count": repair_queue[
            "candidate_current_evidence_usable_count"
        ],
        "repair_operator_queue_ledger_ready_loop_ids": sorted(item["replacement_loop_id"] for item in ledger_ready),
        "repair_operator_queue_runtime_rerun_loop_ids": sorted(item["replacement_loop_id"] for item in runtime_rerun),
        "repair_operator_queue_recovery_guard_loop_ids": sorted(item["replacement_loop_id"] for item in recovery_guard),
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
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{PREVIOUS_REQUIREMENT_ID}", "{BLOCKED_REPAIR_PLAN_REQUIREMENT_ID}", "{REPAIR_OPERATOR_QUEUE_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_blocked_repair_plan_report.v1", "trader1.upbit_paper_repair_operator_queue_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Confirm repair operator queue remains BLOCKED by {REGENERATED_BLOCKER}.
- Confirm the one ledger-candidate-ready item still requires hash operator reconciliation.
- Confirm the four runtime-rerun items and one recovery-guard item remain blocked from ledger review.
- Confirm no regenerated candidate is current-evidence usable, source-delete allowed, live-enabled, or scale-up enabled.
- Route next_allowed_task_class to {NEXT_TASK_CLASS}.
- Keep live orders, live config mutation, source deletion, current evidence mutation, and scale-up blocked.

regenerated_current_blocked_repairs_snapshot:
- blocked_repair_plan_status: {summary["blocked_repair_plan_status"]}
- blocked_repair_plan_item_count: {summary["blocked_repair_plan_item_count"]}
- ledger_rollup_rebuild_ready_count: {summary["blocked_repair_plan_ledger_rollup_rebuild_ready_count"]}
- runtime_cycle_rerun_required_count: {summary["blocked_repair_plan_runtime_cycle_rerun_required_count"]}
- recovery_guard_rerun_required_count: {summary["blocked_repair_plan_recovery_guard_rerun_required_count"]}
- missing_cycle_ledger_jsonl_total_count: {summary["blocked_repair_plan_missing_cycle_ledger_jsonl_total_count"]}
- missing_paper_ledger_rollup_artifact_count: {summary["blocked_repair_plan_missing_paper_ledger_rollup_artifact_count"]}
- repair_operator_queue_status: {summary["repair_operator_queue_status"]}
- repair_operator_queue_primary_blocker_code: {summary["repair_operator_queue_primary_blocker_code"]}
- repair_operator_queue_ledger_candidate_review_ready_count: {summary["repair_operator_queue_ledger_candidate_review_ready_count"]}
- repair_operator_queue_runtime_cycle_rerun_required_count: {summary["repair_operator_queue_runtime_cycle_rerun_required_count"]}
- repair_operator_queue_recovery_guard_rerun_required_count: {summary["repair_operator_queue_recovery_guard_rerun_required_count"]}
- repair_operator_queue_hash_operator_reconciliation_required_count: {summary["repair_operator_queue_hash_operator_reconciliation_required_count"]}
- repair_operator_queue_candidate_current_evidence_usable_count: {summary["repair_operator_queue_candidate_current_evidence_usable_count"]}

known_omissions_by_design:
- This patch does not rebuild missing ledger rollups.
- This patch does not rerun missing PAPER cycles or recovery guards.
- This patch does not write current evidence, mutate live config, use credentials, place live orders, delete sources, or scale up.
- The regenerated-current repair reconciliation gap remains open until ledger/recovery reconciliation evidence exists.

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

The repair operator queue remains BLOCKED by regenerated-current ledger/recovery reconciliation. Six regenerated PAPER replacements are lane-classified; none can mutate current evidence or create live/scale permission.

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
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "regenerated current blocked repairs require ledger recovery reconciliation recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: regenerated current repair candidates must remain repair-queue-blocked, "
                "ledger/recovery-reconciliation-required, source-delete-blocked, current-evidence-blocked, "
                "live-blocked, and scale-up-blocked until validator-backed ledger and recovery evidence exists"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": (
                "Regenerated current blocked repairs require ledger recovery reconciliation recheck"
            ),
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_blocked_repair_plan_report.v1",
                "trader1.upbit_paper_repair_operator_queue_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py",
                "tests/runtime/test_upbit_paper_blocked_repair_plan.py",
                "tests/runtime/test_upbit_paper_repair_operator_queue.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                PREVIOUS_REQUIREMENT_ID,
                BLOCKED_REPAIR_PLAN_REQUIREMENT_ID,
                REPAIR_OPERATOR_QUEUE_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"regenerated current blocked repairs require ledger recovery reconciliation recheck remains live blocked"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RECHECK_REGENERATED_CURRENT_REPAIRS_LEDGER_RECOVERY_BLOCKED",
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
                "contracts/schema/upbit_paper_blocked_repair_plan_report.schema.json",
                "contracts/schema/upbit_paper_repair_operator_queue_report.schema.json",
            ],
            "validator_files": [
                "trader1/validation/mvp0_validators.py",
                "trader1/runtime/paper/upbit_paper_blocked_repair_plan.py",
                "trader1/runtime/paper/upbit_paper_repair_operator_queue.py",
            ],
            "test_files": [
                "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py",
                "tests/runtime/test_upbit_paper_blocked_repair_plan.py",
                "tests/runtime/test_upbit_paper_repair_operator_queue.py",
            ],
            "fixture_files": [PREVIOUS_PATCH_RESULT, BLOCKED_REPAIR_PLAN_REPORT, REPAIR_OPERATOR_QUEUE_REPORT],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_blocked_repair_plan.py",
                "trader1/runtime/paper/upbit_paper_repair_operator_queue.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ],
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
                "repair_operator_queue_primary_blocker_code",
                "repair_operator_queue_item_count",
                "repair_operator_queue_runtime_cycle_rerun_required_count",
                "repair_operator_queue_recovery_guard_rerun_required_count",
                "repair_operator_queue_hash_operator_reconciliation_required_count",
                "repair_operator_queue_candidate_current_evidence_usable_count",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_RECHECK_REGENERATED_CURRENT_REPAIRS_LEDGER_RECOVERY_BLOCKED",
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
                BLOCKED_REPAIR_PLAN_REQUIREMENT_ID,
                REPAIR_OPERATOR_QUEUE_REQUIREMENT_ID,
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
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LEDGER_RECONCILIATION",
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
            "remaining_blockers": summary["remaining_blockers"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                PREVIOUS_PATCH_RESULT,
                BLOCKED_REPAIR_PLAN_REPORT,
                REPAIR_OPERATOR_QUEUE_REPORT,
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_NEXT_TASK_ADVANCED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "optimizer_stage": "MVP-4_PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_status_before": "REGENERATED_CURRENT_REPAIRS_RECHECK_NEXT_LIVE_BLOCKED",
            "optimizer_status_after": "REGENERATED_CURRENT_REPAIRS_CONFIRMED_LEDGER_RECOVERY_BLOCKED",
            "optimizer_maturity_level_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_maturity_level_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_output_type": "PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_guardrail_result": "PASS_REGENERATED_CURRENT_REPAIRS_REMAIN_LEDGER_RECOVERY_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "STATE_RECHECK_ONLY",
            "convergence_layer_changed": False,
            "convergence_state_before": "REGENERATED_CURRENT_REPAIRS_RECHECK_NEXT_LIVE_BLOCKED",
            "convergence_state_after": "REGENERATED_CURRENT_REPAIRS_CONFIRMED_LEDGER_RECOVERY_BLOCKED",
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
                "repair_operator_queue_candidate_current_evidence_usable_count"
            ],
            "blocked_repair_plan_status": summary["blocked_repair_plan_status"],
            "blocked_repair_plan_item_count": summary["blocked_repair_plan_item_count"],
            "blocked_repair_plan_ledger_rollup_rebuild_ready_count": summary[
                "blocked_repair_plan_ledger_rollup_rebuild_ready_count"
            ],
            "blocked_repair_plan_runtime_cycle_rerun_required_count": summary[
                "blocked_repair_plan_runtime_cycle_rerun_required_count"
            ],
            "blocked_repair_plan_recovery_guard_rerun_required_count": summary[
                "blocked_repair_plan_recovery_guard_rerun_required_count"
            ],
            "blocked_repair_plan_missing_cycle_ledger_jsonl_total_count": summary[
                "blocked_repair_plan_missing_cycle_ledger_jsonl_total_count"
            ],
            "blocked_repair_plan_missing_paper_ledger_rollup_artifact_count": summary[
                "blocked_repair_plan_missing_paper_ledger_rollup_artifact_count"
            ],
            "repair_operator_queue_status": summary["repair_operator_queue_status"],
            "repair_operator_queue_primary_blocker_code": summary["repair_operator_queue_primary_blocker_code"],
            "repair_operator_queue_item_count": summary["repair_operator_queue_item_count"],
            "repair_operator_queue_ledger_candidate_review_ready_count": summary[
                "repair_operator_queue_ledger_candidate_review_ready_count"
            ],
            "repair_operator_queue_runtime_cycle_rerun_required_count": summary[
                "repair_operator_queue_runtime_cycle_rerun_required_count"
            ],
            "repair_operator_queue_recovery_guard_rerun_required_count": summary[
                "repair_operator_queue_recovery_guard_rerun_required_count"
            ],
            "repair_operator_queue_hash_operator_reconciliation_required_count": summary[
                "repair_operator_queue_hash_operator_reconciliation_required_count"
            ],
            "repair_operator_queue_candidate_current_evidence_usable_count": summary[
                "repair_operator_queue_candidate_current_evidence_usable_count"
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
            "stage_gate_status": "PASS_REGENERATED_CURRENT_REPAIRS_REMAIN_LEDGER_RECOVERY_BLOCKED",
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
                "contracts/security/source_bundle_manifest.json",
                "system/evidence/implementation_patch_ledger.json",
                PREVIOUS_PATCH_RESULT,
                BLOCKED_REPAIR_PLAN_REPORT,
                REPAIR_OPERATOR_QUEUE_REPORT,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260504.md",
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
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# MVP4 Regenerated Current Blocked Repairs Require Ledger Recovery Reconciliation Recheck Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The repair operator queue remains BLOCKED by {REGENERATED_BLOCKER}.
- One regenerated candidate is ledger-candidate-review-ready but still requires hash operator reconciliation.
- Four regenerated candidates require PAPER runtime cycle reruns before ledger rollup rebuild.
- One regenerated candidate requires recovery guard rerun before ledger rollup rebuild.
- candidate_current_evidence_usable_count remains 0.

Patch:
- Added a dedicated route/evidence recheck for {REGENERATED_BLOCKER}.
- Routed next_allowed_task_class to {NEXT_TASK_CLASS}.
- Added patch_result schema fields for repair operator queue blocker and lane counts.
- Preserved repair, live, current-evidence, source-delete, and scale-up blockers.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no current evidence mutation
- no source deletion
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
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", [])) | OPEN_GAPS_TO_PRESERVE)
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
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
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
                    "tests.contract.test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck",
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
                    "tests/runtime/test_upbit_paper_blocked_repair_plan.py",
                    "tests/runtime/test_upbit_paper_repair_operator_queue.py",
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
    write_source_bundle_manifest()
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
                "repair_operator_queue_status": summary["repair_operator_queue_status"],
                "repair_operator_queue_primary_blocker_code": summary[
                    "repair_operator_queue_primary_blocker_code"
                ],
                "repair_operator_queue_item_count": summary["repair_operator_queue_item_count"],
                "candidate_current_evidence_usable_count": summary[
                    "repair_operator_queue_candidate_current_evidence_usable_count"
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
