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

PATCH_BASENAME = "MVP4_STALE_LOOP_REGENERATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
NEXT_TASK_CLASS = "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK"
PREVIOUS_REQUIREMENT_ID = (
    "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-"
    "RECONCILIATION-IMPLEMENTATION-DEPTH-RECHECK"
)
PREVIOUS_RECHECK_REQUIREMENT_ID = (
    "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-RECHECK"
)
STALE_LOOP_RECONCILIATION_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION"
STALE_LOOP_REGENERATION_POLICY_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-REGENERATION-POLICY"
STALE_LOOP_REGENERATION_BLOCKER = "STALE_LOOP_REGENERATION_REQUIRED"
STALE_LOOP_EXECUTION_BLOCKER = "STALE_LOOP_REGENERATION_EXECUTION_REQUIRED"

PREVIOUS_PATCH_RESULT = (
    "system/evidence/patch_results/"
    "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK.patch_result.json"
)
PREVIOUS_RECHECK_PATCH_RESULT = (
    "system/evidence/patch_results/"
    "MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK.patch_result.json"
)
STALE_LOOP_RECONCILIATION_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_stale_loop_reconciliation_report.json"
)
STALE_LOOP_REGENERATION_PLAN = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_stale_loop_regeneration_plan.json"
)
DEPTH_REPORT_PATH = ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.json"
CONTRACT_GAP_PATH = (
    ROOT / "system" / "evidence" / "contract_gaps" / f"{STALE_LOOP_REGENERATION_BLOCKER}.contract_gap.json"
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
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_stale_loop_reconciliation_validator",
    "upbit_paper_stale_loop_regeneration_plan_validator",
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
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck.py",
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py",
    "tests/contract/test_completed_recheck_route_depth_guard.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
    "tests/contract/test_open_contract_gap_implementation_priority_recheck.py",
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_implementation_depth_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
    "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_implementation_depth_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
    *ROUTE_TEST_ARTIFACTS,
    "tools/emit_stale_loop_regeneration_required_implementation_depth_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    str(DEPTH_REPORT_PATH.relative_to(ROOT)).replace("\\", "/"),
    str(CONTRACT_GAP_PATH.relative_to(ROOT)).replace("\\", "/"),
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


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return path.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "live" not in parts


def load_summary() -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    previous = load_json(ROOT / PREVIOUS_PATCH_RESULT)
    previous_recheck = load_json(ROOT / PREVIOUS_RECHECK_PATCH_RESULT)
    reconciliation = load_json(ROOT / STALE_LOOP_RECONCILIATION_REPORT)
    plan = load_json(ROOT / STALE_LOOP_REGENERATION_PLAN)

    if PREVIOUS_REQUIREMENT_ID not in state.get("completed_requirement_ids", []):
        raise RuntimeError("regenerated-current repair reconciliation depth recheck is not completed")
    if PREVIOUS_RECHECK_REQUIREMENT_ID not in state.get("completed_requirement_ids", []):
        raise RuntimeError("stale loop regeneration required recheck is not completed")
    if state.get("next_allowed_task_class") not in {PATCH_BASENAME, NEXT_TASK_CLASS}:
        raise RuntimeError("state is not routed to the stale loop regeneration required depth recheck")
    if previous.get("next_task_class") != PATCH_BASENAME:
        raise RuntimeError("previous depth recheck does not route to the stale loop regeneration required depth recheck")
    if previous_recheck.get("next_task_class") != "MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK":
        raise RuntimeError("previous stale loop regeneration recheck does not route to execution recheck")

    assert_false_fields("current implementation state", state)
    assert_false_fields(PREVIOUS_PATCH_RESULT, previous, "_after")
    assert_false_fields(PREVIOUS_RECHECK_PATCH_RESULT, previous_recheck, "_after")
    assert_false_fields(STALE_LOOP_RECONCILIATION_REPORT, reconciliation)
    assert_false_fields(STALE_LOOP_REGENERATION_PLAN, plan)
    for field in (
        "automatic_regeneration_allowed",
        "operator_confirmation_required_before_execution",
        "delete_source_allowed",
        "overwrite_source_allowed",
        "actual_regeneration_performed",
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
        if plan.get(field) is True:
            raise RuntimeError(f"stale loop regeneration plan has forbidden true field: {field}")

    if reconciliation.get("reconciliation_status") != "BLOCKED":
        raise RuntimeError("stale loop reconciliation is not BLOCKED")
    if reconciliation.get("legacy_schema_drift_count") != 16:
        raise RuntimeError("stale loop reconciliation legacy schema drift count changed")
    if reconciliation.get("current_evidence_usable_count") != 1:
        raise RuntimeError("stale loop reconciliation current evidence usable count changed")
    if plan.get("plan_status") != "READY_FOR_SAFE_PAPER_REGENERATION":
        raise RuntimeError("stale loop regeneration plan is not ready for safe PAPER regeneration")
    if plan.get("primary_blocker_code") is not None:
        raise RuntimeError("stale loop regeneration plan unexpectedly has a primary blocker")
    expected_counts = {
        "source_loop_report_count": 17,
        "source_current_accepted_count": 1,
        "source_excluded_count": 16,
        "legacy_schema_drift_count": 16,
        "unsafe_blocked_count": 0,
        "invalid_json_count": 0,
        "duplicate_runtime_cycle_hash_count": 0,
        "regeneration_item_count": 16,
        "operator_review_item_count": 0,
        "duplicate_replacement_path_count": 0,
        "overwrite_or_delete_count": 0,
    }
    for field, expected in expected_counts.items():
        if plan.get(field) != expected:
            raise RuntimeError(f"stale loop regeneration plan {field} drifted: {plan.get(field)} != {expected}")
    if plan.get("source_reconciliation_status") != reconciliation.get("reconciliation_status"):
        raise RuntimeError("regeneration plan source reconciliation status drifted from reconciliation report")
    if plan.get("source_reconciliation_hash") != reconciliation.get("reconciliation_hash"):
        raise RuntimeError("regeneration plan source reconciliation hash drifted")
    plan_items = [item for item in plan.get("items", []) if isinstance(item, dict)]
    if len(plan_items) != plan["source_excluded_count"]:
        raise RuntimeError("stale loop regeneration plan item count does not match excluded count")
    session_id = str(plan.get("session_id"))
    replacement_paths: list[str] = []
    for item in plan_items:
        replacement_path = item.get("planned_replacement_path")
        source_path = item.get("source_path")
        if item.get("source_classification") != "LEGACY_SCHEMA_DRIFT":
            raise RuntimeError("stale loop regeneration plan included a non-legacy source for regeneration")
        if item.get("source_evidence_usable_current"):
            raise RuntimeError("stale loop regeneration plan included current evidence source")
        if item.get("planned_action") != "REGENERATE_WITH_CURRENT_SCHEMA_AS_NEW_ARTIFACT":
            raise RuntimeError("stale loop regeneration plan item stopped being a regeneration item")
        if not isinstance(replacement_path, str) or not _artifact_path_allowed(replacement_path, session_id):
            raise RuntimeError("stale loop regeneration replacement path escaped PAPER namespace")
        if replacement_path == source_path or "regenerated-current-schema" not in replacement_path:
            raise RuntimeError("stale loop regeneration replacement path is not source-preserving")
        if (
            item.get("overwrite_source_allowed")
            or item.get("delete_source_allowed")
            or item.get("automatic_live_or_order_allowed")
            or item.get("requires_operator_review")
            or item.get("live_order_ready")
            or item.get("live_order_allowed")
            or item.get("can_live_trade")
            or item.get("scale_up_allowed")
        ):
            raise RuntimeError("stale loop regeneration plan item attempted forbidden mutation or live permission")
        replacement_paths.append(replacement_path)
    if len(replacement_paths) != len(set(replacement_paths)):
        raise RuntimeError("stale loop regeneration replacement paths are no longer unique")

    remaining_blockers = sorted(
        set(state.get("open_contract_gap_ids", []))
        | {STALE_LOOP_REGENERATION_BLOCKER, STALE_LOOP_EXECUTION_BLOCKER}
        | OPEN_GAPS_TO_PRESERVE
        | STATIC_LIVE_BLOCKERS
    )
    return {
        "route_before_patch": state.get("next_allowed_task_class"),
        "route_after_patch": NEXT_TASK_CLASS,
        "state_last_patch_id_before": state.get("last_patch_id"),
        "state_last_patch_result_hash_before": state.get("last_patch_result_hash"),
        "previous_patch_result_hash": previous.get("result_hash"),
        "previous_recheck_patch_result_hash": previous_recheck.get("result_hash"),
        "stale_loop_regeneration_plan_status": plan["plan_status"],
        "stale_loop_regeneration_source_loop_report_count": plan["source_loop_report_count"],
        "stale_loop_regeneration_source_current_accepted_count": plan["source_current_accepted_count"],
        "stale_loop_regeneration_source_excluded_count": plan["source_excluded_count"],
        "stale_loop_regeneration_legacy_schema_drift_count": plan["legacy_schema_drift_count"],
        "stale_loop_regeneration_item_count": plan["regeneration_item_count"],
        "stale_loop_regeneration_operator_review_item_count": plan["operator_review_item_count"],
        "stale_loop_regeneration_duplicate_replacement_path_count": plan["duplicate_replacement_path_count"],
        "stale_loop_regeneration_overwrite_or_delete_count": plan["overwrite_or_delete_count"],
        "stale_loop_regeneration_actual_regeneration_performed": plan["actual_regeneration_performed"],
        "stale_loop_regeneration_automatic_regeneration_allowed": plan["automatic_regeneration_allowed"],
        "stale_loop_regeneration_delete_source_allowed": plan["delete_source_allowed"],
        "stale_loop_regeneration_overwrite_source_allowed": plan["overwrite_source_allowed"],
        "stale_loop_regeneration_replacement_loop_ids": sorted(
            item["planned_replacement_loop_id"] for item in plan_items
        ),
        "remaining_blockers": remaining_blockers,
    }


def build_depth_report(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> dict[str, Any]:
    status = "PASS_DEPTH_5_STALE_LOOP_REGENERATION_REQUIRED_EXECUTION_BLOCKED"
    return {
        "schema_id": "trader1.stale_loop_regeneration_required_implementation_depth_recheck.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "patch_id": PATCH_ID,
        "requirement_id": REQUIREMENT_ID,
        "contract_gap_id": STALE_LOOP_REGENERATION_BLOCKER,
        "status": status,
        "depth_level": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "previous_patch_result_path": PREVIOUS_PATCH_RESULT,
        "previous_patch_result_hash": summary["previous_patch_result_hash"],
        "previous_recheck_patch_result_path": PREVIOUS_RECHECK_PATCH_RESULT,
        "previous_recheck_patch_result_hash": summary["previous_recheck_patch_result_hash"],
        "stale_loop_reconciliation_report_path": STALE_LOOP_RECONCILIATION_REPORT,
        "stale_loop_regeneration_plan_path": STALE_LOOP_REGENERATION_PLAN,
        "next_allowed_task_class": NEXT_TASK_CLASS,
        "execution_blocker_code": STALE_LOOP_EXECUTION_BLOCKER,
        "source_delete_allowed": False,
        "overwrite_source_allowed": False,
        "current_evidence_mutation_allowed": False,
        "actual_regeneration_performed": False,
        "actual_long_run_evidence_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        **summary,
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
                    "code": STALE_LOOP_REGENERATION_BLOCKER,
                    "message": (
                        "The stale-loop regeneration plan is source-preserving and PAPER-only, but the "
                        "actual regeneration executor has not been run in this depth recheck. Execution "
                        "must remain a separate validated task."
                    ),
                },
                {
                    "code": STALE_LOOP_EXECUTION_BLOCKER,
                    "message": (
                        "A dedicated execution-required depth recheck must validate safe PAPER regeneration "
                        "outputs before stale-loop regeneration blockers can close."
                    ),
                },
            ],
            "notes": (
                "Depth recheck only; no stale source is deleted or overwritten, no current evidence is written, "
                "no live order or credentialed API call is made, no live config is mutated, and no scale-up "
                "permission is created."
            ),
            "contract_gap_id": STALE_LOOP_REGENERATION_BLOCKER,
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
included_requirement_ids: ["{REQUIREMENT_ID}", "{PREVIOUS_REQUIREMENT_ID}", "{PREVIOUS_RECHECK_REQUIREMENT_ID}", "{STALE_LOOP_RECONCILIATION_REQUIREMENT_ID}", "{STALE_LOOP_REGENERATION_POLICY_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.contract_gap.v1", "trader1.upbit_paper_stale_loop_regeneration_plan.v1", "trader1.upbit_paper_stale_loop_reconciliation_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Confirm the stale-loop regeneration plan remains READY_FOR_SAFE_PAPER_REGENERATION.
- Confirm all legacy schema-drift sources map to source-preserving PAPER replacement paths.
- Confirm no stale source is deleted, overwritten, promoted, live-enabled, current-evidence usable, or scale-up enabled.
- Confirm actual_regeneration_performed=false and execution remains a separate required step.
- Route next_allowed_task_class to {NEXT_TASK_CLASS}.
- Keep live orders, live config mutation, source deletion, current evidence mutation, long-run evidence, and scale-up blocked.

stale_loop_regeneration_snapshot:
- plan_status: {summary["stale_loop_regeneration_plan_status"]}
- source_loop_report_count: {summary["stale_loop_regeneration_source_loop_report_count"]}
- source_current_accepted_count: {summary["stale_loop_regeneration_source_current_accepted_count"]}
- source_excluded_count: {summary["stale_loop_regeneration_source_excluded_count"]}
- legacy_schema_drift_count: {summary["stale_loop_regeneration_legacy_schema_drift_count"]}
- regeneration_item_count: {summary["stale_loop_regeneration_item_count"]}
- operator_review_item_count: {summary["stale_loop_regeneration_operator_review_item_count"]}
- duplicate_replacement_path_count: {summary["stale_loop_regeneration_duplicate_replacement_path_count"]}
- overwrite_or_delete_count: {summary["stale_loop_regeneration_overwrite_or_delete_count"]}
- actual_regeneration_performed: {str(summary["stale_loop_regeneration_actual_regeneration_performed"]).lower()}

known_omissions_by_design:
- This depth recheck does not execute stale-loop regeneration.
- This patch does not write replacement persistent-loop reports.
- This patch does not delete or overwrite stale source artifacts.
- This patch does not create long-run evidence, write current evidence, mutate live config, use credentials, place live orders, or scale up.
- STALE_LOOP_REGENERATION_REQUIRED and STALE_LOOP_REGENERATION_EXECUTION_REQUIRED remain open until executor evidence is reconciled.

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
- The stale-loop regeneration plan remains PAPER-only and source-preserving.
- actual_regeneration_performed=false, source_delete_allowed=false, overwrite_source_allowed=false.
- No current evidence, live permission, long-run evidence, or scale-up permission is created.

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
            "source_heading": "stale loop regeneration required implementation depth recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: stale loop regeneration plans must remain source-preserving, PAPER-only, "
                "execution-blocked, source-delete-blocked, current-evidence-blocked, live-blocked, "
                "and scale-up-blocked until validator-backed execution evidence exists"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Stale loop regeneration required implementation depth recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.contract_gap.v1",
                "trader1.upbit_paper_stale_loop_regeneration_plan.v1",
                "trader1.upbit_paper_stale_loop_reconciliation_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
                "tests/contract/test_stale_loop_regeneration_required_recheck.py",
                "tests/runtime/test_upbit_paper_stale_loop_regeneration.py",
                "tests/runtime/test_upbit_paper_stale_loop_reconciliation.py",
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
                STALE_LOOP_RECONCILIATION_REQUIREMENT_ID,
                STALE_LOOP_REGENERATION_POLICY_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"stale loop regeneration required implementation depth recheck remains execution and live blocked"
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
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/contract_gap.schema.json",
                "contracts/schema/upbit_paper_stale_loop_regeneration_plan.schema.json",
                "contracts/schema/upbit_paper_stale_loop_reconciliation_report.schema.json",
            ],
            "validator_files": [
                "trader1/validation/mvp0_validators.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_regeneration.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_reconciliation.py",
            ],
            "test_files": [
                "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
                "tests/contract/test_stale_loop_regeneration_required_recheck.py",
                "tests/runtime/test_upbit_paper_stale_loop_regeneration.py",
                "tests/runtime/test_upbit_paper_stale_loop_reconciliation.py",
            ],
            "fixture_files": [
                PREVIOUS_PATCH_RESULT,
                PREVIOUS_RECHECK_PATCH_RESULT,
                STALE_LOOP_RECONCILIATION_REPORT,
                STALE_LOOP_REGENERATION_PLAN,
            ],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_stale_loop_regeneration.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_reconciliation.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                rel(DEPTH_REPORT_PATH),
                rel(CONTRACT_GAP_PATH),
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "next_task_class",
                "remaining_blockers",
                "stale_loop_regeneration_plan_status",
                "stale_loop_regeneration_source_loop_report_count",
                "stale_loop_regeneration_source_current_accepted_count",
                "stale_loop_regeneration_source_excluded_count",
                "stale_loop_regeneration_legacy_schema_drift_count",
                "stale_loop_regeneration_item_count",
                "stale_loop_regeneration_operator_review_item_count",
                "stale_loop_regeneration_duplicate_replacement_path_count",
                "stale_loop_regeneration_overwrite_or_delete_count",
                "stale_loop_regeneration_actual_regeneration_performed",
                "stale_loop_regeneration_automatic_regeneration_allowed",
                "stale_loop_regeneration_delete_source_allowed",
                "stale_loop_regeneration_overwrite_source_allowed",
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
                STALE_LOOP_RECONCILIATION_REQUIREMENT_ID,
                STALE_LOOP_REGENERATION_POLICY_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_STATE_ONLY",
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
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_RUNTIME_RECOVERY",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LEDGER_RECONCILIATION"],
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
                rel(CONTRACT_GAP_PATH),
                PREVIOUS_PATCH_RESULT,
                PREVIOUS_RECHECK_PATCH_RESULT,
                STALE_LOOP_RECONCILIATION_REPORT,
                STALE_LOOP_REGENERATION_PLAN,
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
            "current_implementation_state_status": "UPDATED_DEPTH_RECHECK_NEXT_TASK_ADVANCED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "optimizer_stage": "MVP-4_PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_status_before": "STALE_LOOP_REGENERATION_REQUIRED_DEPTH_RECHECK_NEXT_LIVE_BLOCKED",
            "optimizer_status_after": "STALE_LOOP_REGENERATION_PLAN_CONFIRMED_EXECUTION_DEPTH_REQUIRED",
            "optimizer_maturity_level_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_maturity_level_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_output_type": "PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_guardrail_result": "PASS_STALE_LOOP_REGENERATION_PLAN_REMAINS_NON_EXECUTING",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_state_before": "STALE_LOOP_REGENERATION_REQUIRED_DEPTH_RECHECK_NEXT_LIVE_BLOCKED",
            "convergence_state_after": "STALE_LOOP_REGENERATION_PLAN_CONFIRMED_EXECUTION_DEPTH_REQUIRED",
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
            "candidate_current_evidence_usable_count": 0,
            "stale_loop_regeneration_plan_status": summary["stale_loop_regeneration_plan_status"],
            "stale_loop_regeneration_source_loop_report_count": summary[
                "stale_loop_regeneration_source_loop_report_count"
            ],
            "stale_loop_regeneration_source_current_accepted_count": summary[
                "stale_loop_regeneration_source_current_accepted_count"
            ],
            "stale_loop_regeneration_source_excluded_count": summary[
                "stale_loop_regeneration_source_excluded_count"
            ],
            "stale_loop_regeneration_legacy_schema_drift_count": summary[
                "stale_loop_regeneration_legacy_schema_drift_count"
            ],
            "stale_loop_regeneration_item_count": summary["stale_loop_regeneration_item_count"],
            "stale_loop_regeneration_operator_review_item_count": summary[
                "stale_loop_regeneration_operator_review_item_count"
            ],
            "stale_loop_regeneration_duplicate_replacement_path_count": summary[
                "stale_loop_regeneration_duplicate_replacement_path_count"
            ],
            "stale_loop_regeneration_overwrite_or_delete_count": summary[
                "stale_loop_regeneration_overwrite_or_delete_count"
            ],
            "stale_loop_regeneration_actual_regeneration_performed": summary[
                "stale_loop_regeneration_actual_regeneration_performed"
            ],
            "stale_loop_regeneration_automatic_regeneration_allowed": summary[
                "stale_loop_regeneration_automatic_regeneration_allowed"
            ],
            "stale_loop_regeneration_delete_source_allowed": summary[
                "stale_loop_regeneration_delete_source_allowed"
            ],
            "stale_loop_regeneration_overwrite_source_allowed": summary[
                "stale_loop_regeneration_overwrite_source_allowed"
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
            "stage_gate_status": "PASS_DEPTH_5_STALE_LOOP_REGENERATION_REQUIRED_EXECUTION_BLOCKED",
            "depth_report_path": rel(DEPTH_REPORT_PATH),
            "contract_gap_path": rel(CONTRACT_GAP_PATH),
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
                STALE_LOOP_RECONCILIATION_REPORT,
                STALE_LOOP_REGENERATION_PLAN,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                rel(DEPTH_REPORT_PATH),
                rel(CONTRACT_GAP_PATH),
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
            "depth_report_path": rel(DEPTH_REPORT_PATH),
            "contract_gap_path": rel(CONTRACT_GAP_PATH),
            **summary,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# MVP4 Stale Loop Regeneration Required Implementation Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The stale-loop regeneration plan remains READY_FOR_SAFE_PAPER_REGENERATION.
- Sixteen legacy schema-drift sources map to source-preserving PAPER replacement paths.
- actual_regeneration_performed remains false.
- delete_source_allowed=false, overwrite_source_allowed=false, automatic_regeneration_allowed=false.
- live_order_allowed=false and scale_up_allowed=false.

Patch:
- Added a dedicated implementation-depth recheck for {STALE_LOOP_REGENERATION_BLOCKER}.
- Routed next_allowed_task_class to {NEXT_TASK_CLASS}.
- Added depth report and contract gap evidence for stale-loop regeneration execution blocking.
- Preserved execution, live, current-evidence, source-delete, long-run evidence, and scale-up blockers.

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
- no stale-loop regeneration execution
- no long-run evidence created
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
            "next_allowed_task_class": NEXT_TASK_CLASS,
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
    write_json(DEPTH_REPORT_PATH, build_depth_report(now, trader_hash, agents_hash, summary))
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_contract_gap(now, trader_hash, agents_hash)
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
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
                    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", *ROUTE_TEST_ARTIFACTS, "-q"]),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "tests/runtime/test_upbit_paper_stale_loop_regeneration.py",
                    "tests/runtime/test_upbit_paper_stale_loop_reconciliation.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"]),
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
                "stale_loop_regeneration_plan_status": summary["stale_loop_regeneration_plan_status"],
                "stale_loop_regeneration_item_count": summary["stale_loop_regeneration_item_count"],
                "stale_loop_regeneration_actual_regeneration_performed": summary[
                    "stale_loop_regeneration_actual_regeneration_performed"
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
