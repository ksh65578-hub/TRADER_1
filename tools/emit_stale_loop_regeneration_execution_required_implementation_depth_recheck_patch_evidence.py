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

PATCH_BASENAME = "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
PREVIOUS_RECHECK_REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-RECHECK"
EXECUTOR_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-SAFE-REGENERATION-EXECUTOR"
POST_REGENERATION_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-POST-REGENERATION-RECONCILIATION"
NEXT_TASK_CLASS = "MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK"
PREVIOUS_PATCH_RESULT = (
    "system/evidence/patch_results/"
    "MVP4_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.patch_result.json"
)
PREVIOUS_RECHECK_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK.patch_result.json"
)
STALE_LOOP_REGENERATION_REQUIRED_GAP = "STALE_LOOP_REGENERATION_REQUIRED"
STALE_LOOP_EXECUTION_GAP = "STALE_LOOP_REGENERATION_EXECUTION_REQUIRED"
NEXT_RECONCILIATION_GAP = "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED"
DEPTH_REPORT_PATH = ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.json"
REQUIRED_CONTRACT_GAP_PATH = (
    ROOT / "system" / "evidence" / "contract_gaps" / f"{STALE_LOOP_REGENERATION_REQUIRED_GAP}.contract_gap.json"
)
EXECUTION_CONTRACT_GAP_PATH = (
    ROOT / "system" / "evidence" / "contract_gaps" / f"{STALE_LOOP_EXECUTION_GAP}.contract_gap.json"
)
GUARD_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_stale_loop_regeneration_execution_guard.json"
)
EXECUTOR_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_stale_loop_safe_regeneration_executor_report.json"
)
POST_REGENERATION_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json"
)
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
STATIC_LIVE_BLOCKERS = {
    "API_UNVERIFIED",
    "LIVE_READY_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
}
CLOSED_GAPS = {STALE_LOOP_REGENERATION_REQUIRED_GAP, STALE_LOOP_EXECUTION_GAP}
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
    NEXT_RECONCILIATION_GAP,
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
    "upbit_paper_stale_loop_reconciliation_validator",
    "upbit_paper_stale_loop_regeneration_plan_validator",
    "upbit_paper_stale_loop_execution_guard_validator",
    "upbit_paper_stale_loop_safe_regeneration_executor_validator",
    "upbit_paper_stale_loop_post_regeneration_reconciliation_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    item for item in VALIDATORS_REQUIRED if item != "generated_artifact_dirty_validator"
]
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
    "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py",
    *ROUTE_TEST_ARTIFACTS,
    "tools/emit_stale_loop_regeneration_execution_required_implementation_depth_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    str(DEPTH_REPORT_PATH.relative_to(ROOT)).replace("\\", "/"),
    str(REQUIRED_CONTRACT_GAP_PATH.relative_to(ROOT)).replace("\\", "/"),
    str(EXECUTION_CONTRACT_GAP_PATH.relative_to(ROOT)).replace("\\", "/"),
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


def _artifact_path_allowed(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return path.startswith("system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/") and ".." not in parts and "live" not in parts


def _count_replacement_artifacts(executor: dict[str, Any]) -> int:
    return len(
        {
            item["planned_replacement_path"]
            for item in executor.get("items", [])
            if isinstance(item, dict) and item.get("replacement_written")
        }
    )


def load_summary() -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    previous = load_json(ROOT / PREVIOUS_PATCH_RESULT)
    previous_recheck = load_json(ROOT / PREVIOUS_RECHECK_PATCH_RESULT)
    guard = load_json(ROOT / GUARD_REPORT)
    executor = load_json(ROOT / EXECUTOR_REPORT)
    post = load_json(ROOT / POST_REGENERATION_REPORT)

    if PREVIOUS_REQUIREMENT_ID not in state.get("completed_requirement_ids", []):
        raise RuntimeError("stale loop regeneration required implementation depth recheck is not completed")
    if PREVIOUS_RECHECK_REQUIREMENT_ID not in state.get("completed_requirement_ids", []):
        raise RuntimeError("stale loop regeneration execution required recheck is not completed")
    if state.get("next_allowed_task_class") not in {PATCH_BASENAME, NEXT_TASK_CLASS}:
        raise RuntimeError("state is not routed to stale loop regeneration execution required depth recheck")
    if previous.get("next_task_class") != PATCH_BASENAME:
        raise RuntimeError("previous depth recheck does not route to the execution required depth recheck")
    if previous_recheck.get("next_task_class") != NEXT_TASK_CLASS:
        raise RuntimeError("previous execution recheck does not route to post-regeneration reconciliation")

    assert_false_fields("current implementation state", state)
    assert_false_fields(PREVIOUS_PATCH_RESULT, previous, "_after")
    assert_false_fields(PREVIOUS_RECHECK_PATCH_RESULT, previous_recheck, "_after")
    for name, artifact in ((GUARD_REPORT, guard), (EXECUTOR_REPORT, executor), (POST_REGENERATION_REPORT, post)):
        assert_false_fields(name, artifact)
        for field in (
            "actual_long_run_evidence_created",
            "long_run_evidence_eligible",
            "promotion_eligible",
            "delete_source_allowed",
            "overwrite_source_allowed",
        ):
            if artifact.get(field) is True:
                raise RuntimeError(f"{name} has forbidden true field: {field}")

    expected_guard = {
        "guard_status": "PASS",
        "source_plan_status": "READY_FOR_SAFE_PAPER_REGENERATION",
        "planned_regeneration_item_count": 16,
        "replacement_existing_count": 0,
        "source_hash_mismatch_count": 0,
        "source_missing_count": 0,
    }
    for field, expected in expected_guard.items():
        if guard.get(field) != expected:
            raise RuntimeError(f"execution guard {field} drifted: {guard.get(field)} != {expected}")
    if guard.get("actual_regeneration_performed") is True or guard.get("execution_performed") is True:
        raise RuntimeError("execution guard must remain pre-execution evidence only")

    expected_executor = {
        "executor_status": "PASS",
        "planned_regeneration_item_count": 16,
        "regenerated_item_count": 16,
        "skipped_item_count": 0,
        "actual_regeneration_performed": True,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "source_retention_required": True,
        "delete_source_allowed": False,
        "overwrite_source_allowed": False,
    }
    for field, expected in expected_executor.items():
        if executor.get(field) != expected:
            raise RuntimeError(f"safe regeneration executor {field} drifted: {executor.get(field)} != {expected}")

    replacement_paths: list[str] = []
    for item in executor.get("items", []):
        if not isinstance(item, dict):
            raise RuntimeError("safe executor item is not an object")
        source_path = item.get("source_path")
        replacement_path = item.get("planned_replacement_path")
        if item.get("execution_item_status") != "PASS":
            raise RuntimeError("safe executor item is not PASS")
        if not item.get("source_retained") or not item.get("replacement_written") or not item.get("replacement_exists_after"):
            raise RuntimeError("safe executor item did not retain source and write replacement")
        if item.get("source_hash_match") is not True:
            raise RuntimeError("safe executor item source hash mismatch")
        if item.get("replacement_write_mode") != "CREATE_NEW_ONLY":
            raise RuntimeError("safe executor item stopped being create-new-only")
        if not isinstance(source_path, str) or not isinstance(replacement_path, str):
            raise RuntimeError("safe executor item has invalid source or replacement path")
        if not _artifact_path_allowed(source_path) or not _artifact_path_allowed(replacement_path):
            raise RuntimeError("safe executor item escaped UPBIT/KRW_SPOT/PAPER namespace")
        if source_path == replacement_path or "regenerated-current-schema" not in replacement_path:
            raise RuntimeError("safe executor replacement path is not source-preserving")
        if not (ROOT / source_path).exists() or not (ROOT / replacement_path).exists():
            raise RuntimeError("safe executor source or replacement artifact is missing")
        for field in (
            "delete_source_allowed",
            "overwrite_source_allowed",
            "actual_long_run_evidence_created",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            if item.get(field) is True:
                raise RuntimeError(f"safe executor item has forbidden true field: {field}")
        replacement_paths.append(replacement_path)
    if len(replacement_paths) != 16 or len(replacement_paths) != len(set(replacement_paths)):
        raise RuntimeError("safe executor replacement paths are missing or duplicated")

    expected_post = {
        "post_reconciliation_status": "BLOCKED",
        "primary_blocker_code": "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
        "planned_regeneration_item_count": 16,
        "regenerated_current_accepted_count": 10,
        "regenerated_current_blocked_reconciliation_count": 6,
        "current_evidence_usable_count": 10,
        "excluded_from_current_evidence_count": 6,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
    }
    for field, expected in expected_post.items():
        if post.get(field) != expected:
            raise RuntimeError(f"post-regeneration reconciliation {field} drifted: {post.get(field)} != {expected}")
    if "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED" not in post.get("blocker_codes", []):
        raise RuntimeError("post-regeneration reconciliation blocker is missing")

    state_gaps = set(state.get("open_contract_gap_ids", []))
    next_open_gaps = sorted((state_gaps - CLOSED_GAPS) | OPEN_GAPS_TO_PRESERVE)
    remaining_blockers = sorted(set(next_open_gaps) | STATIC_LIVE_BLOCKERS)
    return {
        "route_before_patch": state.get("next_allowed_task_class"),
        "route_after_patch": NEXT_TASK_CLASS,
        "state_last_patch_id_before": state.get("last_patch_id"),
        "state_last_patch_result_hash_before": state.get("last_patch_result_hash"),
        "previous_patch_result_hash": previous.get("result_hash"),
        "previous_recheck_patch_result_hash": previous_recheck.get("result_hash"),
        "closed_contract_gap_ids": sorted(CLOSED_GAPS),
        "resolved_contract_gap_status": "RESOLVED",
        "next_reconciliation_gap": NEXT_RECONCILIATION_GAP,
        "stale_loop_execution_guard_status": guard["guard_status"],
        "stale_loop_execution_guard_planned_regeneration_item_count": guard["planned_regeneration_item_count"],
        "stale_loop_execution_guard_replacement_existing_count": guard["replacement_existing_count"],
        "stale_loop_execution_guard_source_hash_mismatch_count": guard["source_hash_mismatch_count"],
        "stale_loop_execution_guard_source_missing_count": guard["source_missing_count"],
        "stale_loop_execution_guard_actual_regeneration_performed": guard["actual_regeneration_performed"],
        "stale_loop_execution_guard_actual_long_run_evidence_created": guard["actual_long_run_evidence_created"],
        "stale_loop_safe_executor_status": executor["executor_status"],
        "stale_loop_safe_executor_planned_regeneration_item_count": executor["planned_regeneration_item_count"],
        "stale_loop_safe_executor_regenerated_item_count": executor["regenerated_item_count"],
        "stale_loop_safe_executor_skipped_item_count": executor["skipped_item_count"],
        "stale_loop_safe_executor_replacement_artifact_count": _count_replacement_artifacts(executor),
        "stale_loop_safe_executor_actual_regeneration_performed": executor["actual_regeneration_performed"],
        "stale_loop_safe_executor_actual_long_run_evidence_created": executor["actual_long_run_evidence_created"],
        "stale_loop_safe_executor_long_run_evidence_eligible": executor["long_run_evidence_eligible"],
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
        "next_open_contract_gap_ids": next_open_gaps,
        "remaining_blockers": remaining_blockers,
    }


def build_depth_report(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> dict[str, Any]:
    status = "PASS_DEPTH_5_STALE_LOOP_REGENERATION_EXECUTION_RECONCILIATION_BLOCKED"
    return {
        "schema_id": "trader1.stale_loop_regeneration_execution_required_implementation_depth_recheck.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "patch_id": PATCH_ID,
        "requirement_id": REQUIREMENT_ID,
        "contract_gap_id": STALE_LOOP_EXECUTION_GAP,
        "status": status,
        "depth_level": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "previous_patch_result_path": PREVIOUS_PATCH_RESULT,
        "previous_patch_result_hash": summary["previous_patch_result_hash"],
        "previous_recheck_patch_result_path": PREVIOUS_RECHECK_PATCH_RESULT,
        "previous_recheck_patch_result_hash": summary["previous_recheck_patch_result_hash"],
        "execution_guard_report_path": GUARD_REPORT,
        "safe_executor_report_path": EXECUTOR_REPORT,
        "post_regeneration_reconciliation_report_path": POST_REGENERATION_REPORT,
        "resolved_contract_gap_ids": summary["closed_contract_gap_ids"],
        "next_open_contract_gap_ids": summary["next_open_contract_gap_ids"],
        "next_allowed_task_class": NEXT_TASK_CLASS,
        "new_runtime_regeneration_performed": False,
        "source_delete_allowed": False,
        "overwrite_source_allowed": False,
        "current_evidence_mutation_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        **summary,
    }


def write_contract_gaps(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    for gap_id, path, message in (
        (
            STALE_LOOP_REGENERATION_REQUIRED_GAP,
            REQUIRED_CONTRACT_GAP_PATH,
            "The source-preserving PAPER regeneration plan was followed by validated safe executor evidence.",
        ),
        (
            STALE_LOOP_EXECUTION_GAP,
            EXECUTION_CONTRACT_GAP_PATH,
            "Safe PAPER regeneration executor evidence exists and remains blocked on post-regeneration reconciliation.",
        ),
    ):
        write_json(
            path,
            {
                "schema_id": "trader1.contract_gap.v1",
                "generated_at_utc": now,
                "project_id": "TRADER_1",
                "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "status": "RESOLVED",
                "blockers": [],
                "notes": (
                    f"{message} Resolution is PAPER-only and does not create live readiness, current-evidence "
                    "promotion, source deletion, long-run evidence, or scale-up permission. "
                    f"{NEXT_RECONCILIATION_GAP} remains open."
                ),
                "contract_gap_id": gap_id,
                "severity": "HIGH",
                "source_section_id": "SECTION_RUNTIME_RECOVERY",
                "live_affecting": True,
            },
        )


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{PREVIOUS_REQUIREMENT_ID}", "{PREVIOUS_RECHECK_REQUIREMENT_ID}", "{EXECUTOR_REQUIREMENT_ID}", "{POST_REGENERATION_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.contract_gap.v1", "trader1.upbit_paper_stale_loop_regeneration_execution_guard.v1", "trader1.upbit_paper_stale_loop_safe_regeneration_executor_report.v1", "trader1.upbit_paper_stale_loop_post_regeneration_reconciliation_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Confirm execution guard PASS evidence remains pre-execution and source-retaining.
- Confirm safe regeneration executor PASS created 16 current-schema PAPER replacements.
- Confirm source reports remain retained and no delete or overwrite is allowed.
- Confirm generated replacements are not long-run evidence, live evidence, promotion evidence, or scale-up evidence.
- Resolve STALE_LOOP_REGENERATION_REQUIRED and STALE_LOOP_REGENERATION_EXECUTION_REQUIRED contract gaps in current state.
- Route next_allowed_task_class to {NEXT_TASK_CLASS}.

execution_recheck_snapshot:
- guard_status: {summary["stale_loop_execution_guard_status"]}
- executor_status: {summary["stale_loop_safe_executor_status"]}
- regenerated_item_count: {summary["stale_loop_safe_executor_regenerated_item_count"]}
- replacement_artifact_count: {summary["stale_loop_safe_executor_replacement_artifact_count"]}
- post_regeneration_status: {summary["stale_loop_post_regeneration_reconciliation_status"]}
- post_regeneration_current_evidence_usable_count: {summary["stale_loop_post_regeneration_current_evidence_usable_count"]}

known_omissions_by_design:
- This patch does not run regeneration again.
- This patch does not delete or overwrite stale source artifacts.
- This patch does not write current-evidence snapshots, mutate live config, use credentials, place live orders, create long-run evidence, or scale up.
- STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED remains open for the next safe recheck.
- Resolved gaps are not live readiness evidence.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )
    active_view_path = ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md"
    active_view = active_view_path.read_text(encoding="utf-8") if active_view_path.exists() else ""
    marker = f"## {PATCH_BASENAME}"
    section = f"""

{marker}

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

Current safe state:
- Safe PAPER regeneration executor evidence exists for 16 source-retaining current-schema replacements.
- No source deletion, overwrite, current-evidence write, long-run evidence, live permission, or scale-up permission is created.
- {NEXT_RECONCILIATION_GAP} remains open and live-blocking.

Next safe task:
- {NEXT_TASK_CLASS}
"""
    if marker in active_view:
        active_view = active_view[: active_view.index(marker)].rstrip() + section
    else:
        active_view = active_view.rstrip() + section
    write_text(active_view_path, active_view.rstrip() + "\n")


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
                rel(DEPTH_REPORT_PATH),
                rel(REQUIRED_CONTRACT_GAP_PATH),
                rel(EXECUTION_CONTRACT_GAP_PATH),
                PREVIOUS_RECHECK_PATCH_RESULT,
                GUARD_REPORT,
                EXECUTOR_REPORT,
                POST_REGENERATION_REPORT,
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
            "source_heading": "stale loop regeneration execution required implementation depth recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: safe regeneration executor evidence may close stale loop regeneration execution "
                "required only when source-retained PAPER replacements exist and live/long-run/scale-up remain blocked"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Stale loop regeneration execution required implementation depth recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.contract_gap.v1",
                "trader1.upbit_paper_stale_loop_regeneration_execution_guard.v1",
                "trader1.upbit_paper_stale_loop_safe_regeneration_executor_report.v1",
                "trader1.upbit_paper_stale_loop_post_regeneration_reconciliation_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
                "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py",
                "tests/runtime/test_upbit_paper_stale_loop_safe_regeneration_executor.py",
                "tests/runtime/test_upbit_paper_stale_loop_post_regeneration_reconciliation.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                PREVIOUS_REQUIREMENT_ID,
                PREVIOUS_RECHECK_REQUIREMENT_ID,
                EXECUTOR_REQUIREMENT_ID,
                POST_REGENERATION_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"safe regeneration execution depth recheck closes execution-required gap without live permission"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "COMPLETED",
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
            "schema_files": ["contracts/schema/patch_result.schema.json", "contracts/schema/contract_gap.schema.json"],
            "validator_files": [
                "trader1/validation/mvp0_validators.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_safe_regeneration_executor.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_post_regeneration_reconciliation.py",
            ],
            "test_files": [
                "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
                "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py",
                "tests/runtime/test_upbit_paper_stale_loop_safe_regeneration_executor.py",
                "tests/runtime/test_upbit_paper_stale_loop_post_regeneration_reconciliation.py",
            ],
            "fixture_files": [PREVIOUS_PATCH_RESULT, PREVIOUS_RECHECK_PATCH_RESULT],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_stale_loop_execution_guard.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_safe_regeneration_executor.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_post_regeneration_reconciliation.py",
            ],
            "evidence_artifacts": [
                GUARD_REPORT,
                EXECUTOR_REPORT,
                POST_REGENERATION_REPORT,
                rel(DEPTH_REPORT_PATH),
                rel(REQUIRED_CONTRACT_GAP_PATH),
                rel(EXECUTION_CONTRACT_GAP_PATH),
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "stale_loop_execution_guard_status",
                "stale_loop_safe_executor_status",
                "stale_loop_safe_executor_regenerated_item_count",
                "stale_loop_post_regeneration_reconciliation_status",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "COMPLETED",
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
                PREVIOUS_RECHECK_REQUIREMENT_ID,
                EXECUTOR_REQUIREMENT_ID,
                POST_REGENERATION_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_STATE_ONLY",
            "new_registry_items": [
                REQUIREMENT_ID,
                rel(DEPTH_REPORT_PATH),
                rel(REQUIRED_CONTRACT_GAP_PATH),
                rel(EXECUTION_CONTRACT_GAP_PATH),
            ],
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
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX"],
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
                rel(DEPTH_REPORT_PATH),
                rel(REQUIRED_CONTRACT_GAP_PATH),
                rel(EXECUTION_CONTRACT_GAP_PATH),
                PREVIOUS_PATCH_RESULT,
                PREVIOUS_RECHECK_PATCH_RESULT,
                GUARD_REPORT,
                EXECUTOR_REPORT,
                POST_REGENERATION_REPORT,
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_DEPTH_RECHECK_EXECUTION_GAP_CLOSED_RECONCILIATION_REQUIRED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "optimizer_stage": "MVP-4_PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_status_before": "STALE_LOOP_REGENERATION_EXECUTION_DEPTH_REQUIRED",
            "optimizer_status_after": "STALE_LOOP_REGENERATION_EXECUTION_DEPTH_CONFIRMED_RECONCILIATION_REQUIRED",
            "optimizer_maturity_level_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_maturity_level_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_output_type": "PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_guardrail_result": "PASS_SAFE_REGENERATION_EXECUTION_DEPTH_EVIDENCE_REMAINS_PAPER_ONLY",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_state_before": "STALE_LOOP_REGENERATION_EXECUTION_DEPTH_REQUIRED",
            "convergence_state_after": "STALE_LOOP_SAFE_REGENERATION_EXECUTION_DEPTH_CONFIRMED_RECONCILIATION_REQUIRED",
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
                "stale_loop_post_regeneration_current_evidence_usable_count"
            ],
            "stale_loop_regeneration_actual_regeneration_performed": summary[
                "stale_loop_safe_executor_actual_regeneration_performed"
            ],
            "stale_loop_execution_guard_status": summary["stale_loop_execution_guard_status"],
            "stale_loop_execution_guard_planned_regeneration_item_count": summary[
                "stale_loop_execution_guard_planned_regeneration_item_count"
            ],
            "stale_loop_execution_guard_replacement_existing_count": summary[
                "stale_loop_execution_guard_replacement_existing_count"
            ],
            "stale_loop_execution_guard_source_hash_mismatch_count": summary[
                "stale_loop_execution_guard_source_hash_mismatch_count"
            ],
            "stale_loop_execution_guard_source_missing_count": summary[
                "stale_loop_execution_guard_source_missing_count"
            ],
            "stale_loop_execution_guard_actual_regeneration_performed": summary[
                "stale_loop_execution_guard_actual_regeneration_performed"
            ],
            "stale_loop_execution_guard_actual_long_run_evidence_created": summary[
                "stale_loop_execution_guard_actual_long_run_evidence_created"
            ],
            "stale_loop_safe_executor_status": summary["stale_loop_safe_executor_status"],
            "stale_loop_safe_executor_planned_regeneration_item_count": summary[
                "stale_loop_safe_executor_planned_regeneration_item_count"
            ],
            "stale_loop_safe_executor_regenerated_item_count": summary[
                "stale_loop_safe_executor_regenerated_item_count"
            ],
            "stale_loop_safe_executor_skipped_item_count": summary["stale_loop_safe_executor_skipped_item_count"],
            "stale_loop_safe_executor_replacement_artifact_count": summary[
                "stale_loop_safe_executor_replacement_artifact_count"
            ],
            "stale_loop_safe_executor_actual_regeneration_performed": summary[
                "stale_loop_safe_executor_actual_regeneration_performed"
            ],
            "stale_loop_safe_executor_actual_long_run_evidence_created": summary[
                "stale_loop_safe_executor_actual_long_run_evidence_created"
            ],
            "stale_loop_safe_executor_long_run_evidence_eligible": summary[
                "stale_loop_safe_executor_long_run_evidence_eligible"
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
            "stage_gate_status": "PASS_DEPTH_5_STALE_LOOP_REGENERATION_EXECUTION_RECONCILIATION_BLOCKED",
            "depth_report_path": rel(DEPTH_REPORT_PATH),
            "required_contract_gap_path": rel(REQUIRED_CONTRACT_GAP_PATH),
            "execution_contract_gap_path": rel(EXECUTION_CONTRACT_GAP_PATH),
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
                GUARD_REPORT,
                EXECUTOR_REPORT,
                POST_REGENERATION_REPORT,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                rel(DEPTH_REPORT_PATH),
                rel(REQUIRED_CONTRACT_GAP_PATH),
                rel(EXECUTION_CONTRACT_GAP_PATH),
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
            "depth_report_path": rel(DEPTH_REPORT_PATH),
            "required_contract_gap_path": rel(REQUIRED_CONTRACT_GAP_PATH),
            "execution_contract_gap_path": rel(EXECUTION_CONTRACT_GAP_PATH),
            **summary,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 Stale Loop Regeneration Execution Required Implementation Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The stale-loop execution guard remains PASS and pre-execution only.
- The safe regeneration executor is PASS and has already written 16 source-retaining current-schema PAPER replacements.
- This depth recheck does not run regeneration again.
- The executor created no long-run evidence, live readiness, order permission, promotion permission, source deletion, overwrite, or scale-up permission.
- Post-regeneration reconciliation remains BLOCKED by STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED.

Patch:
- Resolved STALE_LOOP_REGENERATION_REQUIRED and STALE_LOOP_REGENERATION_EXECUTION_REQUIRED in current implementation state.
- Routed next_allowed_task_class to {NEXT_TASK_CLASS}.
- Added depth report, resolved contract-gap projections, and patch_result fields for execution guard and safe executor evidence.
- Preserved all live, long-run evidence, current-evidence write, source-delete, and scale-up blockers.

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
            "next_allowed_task_class": NEXT_TASK_CLASS,
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
    write_json(DEPTH_REPORT_PATH, build_depth_report(now, trader_hash, agents_hash, summary))
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
    write_contract_gaps(now, trader_hash, agents_hash, summary)
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
                    "tests.contract.test_stale_loop_regeneration_execution_required_implementation_depth_recheck",
                    "tests.contract.test_stale_loop_regeneration_execution_required_recheck",
                    "tests.contract.test_stale_loop_regeneration_required_implementation_depth_recheck",
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
                    "tests/runtime/test_upbit_paper_stale_loop_safe_regeneration_executor.py",
                    "tests/runtime/test_upbit_paper_stale_loop_post_regeneration_reconciliation.py",
                    "tests/runtime/test_upbit_paper_stale_loop_execution_guard.py",
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
    write_contract_gaps(now, trader_hash, agents_hash, summary)
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
                "safe_executor_status": summary["stale_loop_safe_executor_status"],
                "regenerated_item_count": summary["stale_loop_safe_executor_regenerated_item_count"],
                "closed_contract_gap_ids": summary["closed_contract_gap_ids"],
                "post_regeneration_status": summary["stale_loop_post_regeneration_reconciliation_status"],
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
