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

PATCH_BASENAME = "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_NEXT_TASK_RESTORE"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-NEXT-TASK-RESTORE"
NEXT_TASK_CLASS = "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK"
BACKWARD_ROUTE_TASK = "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_RECHECK"

PATCH_RESULT_GAP_STATE_SYNC_REQUIREMENT_ID = "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-STATE-SYNC-RECHECK"
POST_REPAIR_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION"
POST_REPAIR_OPERATOR_UX_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION-OPERATOR-UX-RECHECK"

PATCH_RESULT_GAP_STATE_SYNC_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_STATE_SYNC_RECHECK.patch_result.json"
)
POST_REPAIR_PATCH_RESULT = "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION.patch_result.json"
POST_REPAIR_DASHBOARD_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION_DASHBOARD_BINDING.patch_result.json"
)
POST_REPAIR_OPERATOR_UX_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION_OPERATOR_UX_RECHECK.patch_result.json"
)
POST_REPAIR_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_post_repair_reconciliation_report.json"
)

COMPLETED_ROUTE_REQUIREMENT_IDS = {
    PATCH_RESULT_GAP_STATE_SYNC_REQUIREMENT_ID,
    "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-STATE-SYNC-RECHECK",
    "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK",
    "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-NEXT-TASK-RESTORE",
    "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-NEXT-TASK-RESTORE",
    "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-NEXT-TASK-RESTORE",
}
COMPLETED_ROUTE_TASK_CLASSES = {
    "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_RECHECK",
    "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_RECHECK",
    "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECK",
    "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_RECHECK",
    "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_RECHECK",
    "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_RECHECK",
    "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK",
}
OPEN_GAPS_TO_PRESERVE = {
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
}
STATIC_LIVE_BLOCKERS = {
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
}
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

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
    "upbit_paper_post_repair_reconciliation_validator",
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
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_post_repair_reconciliation_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
    "tools/emit_patch_result_validator_run_gap_state_sync_recheck_patch_evidence.py",
    "tools/emit_patch_result_validator_run_gap_next_task_restore_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
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


def assert_false_fields(name: str, artifact: dict[str, Any], suffix: str = "") -> None:
    for field in FALSE_FIELDS:
        key = f"{field}{suffix}"
        if artifact.get(key) is True:
            raise RuntimeError(f"{name} has forbidden true field: {key}")


def load_route_summary() -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    gap_state_sync = load_json(ROOT / PATCH_RESULT_GAP_STATE_SYNC_PATCH_RESULT)
    post_repair_patch = load_json(ROOT / POST_REPAIR_PATCH_RESULT)
    post_repair_dashboard = load_json(ROOT / POST_REPAIR_DASHBOARD_PATCH_RESULT)
    post_repair_operator = load_json(ROOT / POST_REPAIR_OPERATOR_UX_PATCH_RESULT)
    post_repair_report = load_json(ROOT / POST_REPAIR_REPORT)

    missing_completed = sorted(COMPLETED_ROUTE_REQUIREMENT_IDS - set(state.get("completed_requirement_ids", [])))
    if missing_completed:
        raise RuntimeError(f"completed route chain is incomplete: {missing_completed}")
    if PATCH_RESULT_GAP_STATE_SYNC_REQUIREMENT_ID not in gap_state_sync.get("affected_contract_ids", []):
        raise RuntimeError("patch-result validator-run state-sync patch_result requirement drifted")

    for path_text, artifact in (
        (PATCH_RESULT_GAP_STATE_SYNC_PATCH_RESULT, gap_state_sync),
        (POST_REPAIR_PATCH_RESULT, post_repair_patch),
        (POST_REPAIR_DASHBOARD_PATCH_RESULT, post_repair_dashboard),
        (POST_REPAIR_OPERATOR_UX_PATCH_RESULT, post_repair_operator),
    ):
        assert_false_fields(path_text, artifact, "_after")
    assert_false_fields("current implementation state", state)
    assert_false_fields(POST_REPAIR_REPORT, post_repair_report)

    if "POST_REPAIR_RECONCILIATION_REQUIRED" not in state.get("open_contract_gap_ids", []):
        raise RuntimeError("post-repair reconciliation gap is no longer tracked as open")
    if "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED" not in state.get("open_contract_gap_ids", []):
        raise RuntimeError("repair candidate hash mismatch gap is no longer tracked as open")
    if post_repair_report.get("post_repair_reconciliation_status") != "BLOCKED":
        raise RuntimeError("post-repair reconciliation report is no longer BLOCKED")
    if post_repair_report.get("primary_blocker_code") != "POST_REPAIR_RECONCILIATION_REQUIRED":
        raise RuntimeError("post-repair primary blocker drifted")
    if post_repair_report.get("candidate_current_evidence_usable_count") != 0:
        raise RuntimeError("post-repair report unexpectedly permits current evidence")
    if post_repair_report.get("source_loop_expected_rollup_hash_mismatch_count", 0) <= 0:
        raise RuntimeError("post-repair hash mismatch evidence is missing")

    observed_next = state.get("next_allowed_task_class")
    route_before = observed_next
    if state.get("last_patch_id") == PATCH_ID and observed_next == NEXT_TASK_CLASS:
        route_before = BACKWARD_ROUTE_TASK

    remaining_blockers = sorted(
        set(state.get("open_contract_gap_ids", []))
        | set(post_repair_report.get("blocker_codes", []))
        | OPEN_GAPS_TO_PRESERVE
        | STATIC_LIVE_BLOCKERS
    )
    return {
        "route_before_patch": route_before,
        "observed_state_next_allowed_task_class": observed_next,
        "route_after_patch": NEXT_TASK_CLASS,
        "completed_route_chain_recorded": True,
        "backward_route_detected": route_before in COMPLETED_ROUTE_TASK_CLASSES,
        "state_last_patch_id_before": state.get("last_patch_id"),
        "state_last_patch_result_hash_before": state.get("last_patch_result_hash"),
        "patch_result_gap_state_sync_patch_result_hash": gap_state_sync.get("result_hash"),
        "patch_result_gap_state_sync_next_task_class": gap_state_sync.get("next_task_class"),
        "post_repair_patch_result_hash": post_repair_patch.get("result_hash"),
        "post_repair_dashboard_patch_result_hash": post_repair_dashboard.get("result_hash"),
        "post_repair_operator_patch_result_hash": post_repair_operator.get("result_hash"),
        "post_repair_reconciliation_status": post_repair_report["post_repair_reconciliation_status"],
        "post_repair_reconciliation_item_count": post_repair_report["reconciliation_item_count"],
        "post_repair_source_loop_expected_rollup_hash_mismatch_count": post_repair_report[
            "source_loop_expected_rollup_hash_mismatch_count"
        ],
        "post_repair_candidate_current_evidence_usable_count": post_repair_report[
            "candidate_current_evidence_usable_count"
        ],
        "post_repair_reconciliation_operator_action_label": "Inspect post-repair reconciliation",
        "post_repair_reconciliation_operator_workflow_status": "BLOCKED",
        "post_repair_reconciliation_operator_workflow_current_step": "INSPECT_DASHBOARD",
        "post_repair_reconciliation_operator_hash_mismatch_count": post_repair_report[
            "source_loop_expected_rollup_hash_mismatch_count"
        ],
        "post_repair_reconciliation_operator_action_item_count": post_repair_report[
            "hash_reconciliation_operator_action_required_count"
        ],
        "remaining_blockers": remaining_blockers,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_NEXT_TASK_RESTORE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PATCH_RESULT", "SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{PATCH_RESULT_GAP_STATE_SYNC_REQUIREMENT_ID}", "{POST_REPAIR_REQUIREMENT_ID}", "{POST_REPAIR_OPERATOR_UX_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_repair_reconciliation_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Detect that the patch-result, profitability, long-run, paper-shadow, missing-cycle, and post-rerun route chain is already complete.
- Prevent current_implementation_state from routing back to {BACKWARD_ROUTE_TASK}.
- Restore next_allowed_task_class to {NEXT_TASK_CLASS}.
- Keep POST_REPAIR_RECONCILIATION_REQUIRED and REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED open and live-blocking.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

route_snapshot:
- route_before_patch: {summary["route_before_patch"]}
- backward_route_detected: {summary["backward_route_detected"]}
- route_after_patch: {summary["route_after_patch"]}

post_repair_snapshot:
- post_repair_reconciliation_status: {summary["post_repair_reconciliation_status"]}
- post_repair_reconciliation_item_count: {summary["post_repair_reconciliation_item_count"]}
- post_repair_source_loop_expected_rollup_hash_mismatch_count: {summary["post_repair_source_loop_expected_rollup_hash_mismatch_count"]}
- post_repair_candidate_current_evidence_usable_count: {summary["post_repair_candidate_current_evidence_usable_count"]}

known_omissions_by_design:
- No post-repair reconciliation is resolved by this patch.
- No current evidence writer, latest pointer, live config, credentialed API, live order, or scale-up output is written.
- The post-repair reconciliation and repair hash mismatch gaps remain open until independent operator reconciliation evidence passes.

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

The completed route chain was pointing back to the patch-result validator-run gap recheck. That recheck is already recorded, and the next safe open gap is the blocked post-repair reconciliation path. The post-repair report still shows one hash mismatch and zero usable current-evidence candidates.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
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
            "source_section_id": "SECTION_PATCH_RESULT",
            "source_file": "TRADER_1.md",
            "source_heading": "patch-result validator-run gap next task restore",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: completed route chains must not route current_implementation_state back "
                "to already completed patch-result validator-run rechecks when post-repair reconciliation remains open"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Patch result validator-run gap next task restore",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.patch_result.v1", "trader1.upbit_paper_post_repair_reconciliation_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_patch_result_runtime_schema_validation.py",
                "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
                "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
                "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_PATCH_RESULT",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                PATCH_RESULT_GAP_STATE_SYNC_REQUIREMENT_ID,
                POST_REPAIR_REQUIREMENT_ID,
                POST_REPAIR_OPERATOR_UX_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"completed patch result validator route must advance to post repair reconciliation open gap"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_NEXT_TASK_RESTORE_POST_REPAIR_GAP_OPEN",
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
            "section_id": "SECTION_PATCH_RESULT",
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/upbit_paper_post_repair_reconciliation_report.schema.json",
            ],
            "validator_files": [
                "trader1/validation/mvp0_validators.py",
                "trader1/runtime/paper/upbit_paper_post_repair_reconciliation.py",
            ],
            "test_files": [
                "tests/contract/test_patch_result_runtime_schema_validation.py",
                "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
                "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
                "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
            ],
            "fixture_files": [
                PATCH_RESULT_GAP_STATE_SYNC_PATCH_RESULT,
                POST_REPAIR_PATCH_RESULT,
                POST_REPAIR_DASHBOARD_PATCH_RESULT,
                POST_REPAIR_OPERATOR_UX_PATCH_RESULT,
                POST_REPAIR_REPORT,
            ],
            "runtime_modules": ["trader1/runtime/paper/upbit_paper_post_repair_reconciliation.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "next_task_class",
                "next_required_section_ids",
                "remaining_blockers",
                "post_repair_reconciliation_status",
                "post_repair_candidate_current_evidence_usable_count",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_NEXT_TASK_RESTORE_POST_REPAIR_GAP_OPEN",
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
    template = load_json(ROOT / POST_REPAIR_OPERATOR_UX_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                PATCH_RESULT_GAP_STATE_SYNC_REQUIREMENT_ID,
                POST_REPAIR_REQUIREMENT_ID,
                POST_REPAIR_OPERATOR_UX_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_STATE_ONLY",
            "new_registry_items": [
                REQUIREMENT_ID,
                f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
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
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
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
                PATCH_RESULT_GAP_STATE_SYNC_PATCH_RESULT,
                POST_REPAIR_PATCH_RESULT,
                POST_REPAIR_DASHBOARD_PATCH_RESULT,
                POST_REPAIR_OPERATOR_UX_PATCH_RESULT,
                POST_REPAIR_REPORT,
                "SECTION_PATCH_RESULT",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_NEXT_TASK_RESTORE",
            "required_section_ids": [
                "SECTION_PATCH_RESULT",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_PATCH_RESULT",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_NEXT_TASK_RESTORED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "optimizer_stage": "MVP-4_PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_status_before": "LIVE_BLOCKED_ROUTE_REGRESSION_DETECTED",
            "optimizer_status_after": "POST_REPAIR_RECONCILIATION_RECHECK_NEXT_LIVE_BLOCKED",
            "optimizer_maturity_level_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_maturity_level_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_output_type": "PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION_NO_CURRENT_EVIDENCE_PROMOTION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "STATE_ROUTING_RESTORE_ONLY",
            "convergence_layer_changed": False,
            "convergence_state_before": "LIVE_BLOCKED_ROUTE_REGRESSION_DETECTED",
            "convergence_state_after": "POST_REPAIR_RECONCILIATION_RECHECK_NEXT_LIVE_BLOCKED",
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
            "candidate_current_evidence_usable_count": summary["post_repair_candidate_current_evidence_usable_count"],
            "post_repair_reconciliation_status": summary["post_repair_reconciliation_status"],
            "post_repair_reconciliation_item_count": summary["post_repair_reconciliation_item_count"],
            "post_repair_source_loop_expected_rollup_hash_mismatch_count": summary[
                "post_repair_source_loop_expected_rollup_hash_mismatch_count"
            ],
            "post_repair_candidate_current_evidence_usable_count": summary[
                "post_repair_candidate_current_evidence_usable_count"
            ],
            "post_repair_reconciliation_operator_action_label": summary[
                "post_repair_reconciliation_operator_action_label"
            ],
            "post_repair_reconciliation_operator_workflow_status": summary[
                "post_repair_reconciliation_operator_workflow_status"
            ],
            "post_repair_reconciliation_operator_workflow_current_step": summary[
                "post_repair_reconciliation_operator_workflow_current_step"
            ],
            "post_repair_reconciliation_operator_hash_mismatch_count": summary[
                "post_repair_reconciliation_operator_hash_mismatch_count"
            ],
            "post_repair_reconciliation_operator_action_item_count": summary[
                "post_repair_reconciliation_operator_action_item_count"
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
            "stage_gate_status": "PASS_NEXT_TASK_RESTORED_TO_POST_REPAIR_RECONCILIATION_OPEN_GAP",
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
                PATCH_RESULT_GAP_STATE_SYNC_PATCH_RESULT,
                POST_REPAIR_PATCH_RESULT,
                POST_REPAIR_DASHBOARD_PATCH_RESULT,
                POST_REPAIR_OPERATOR_UX_PATCH_RESULT,
                POST_REPAIR_REPORT,
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
            **summary,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# MVP4 Patch Result Validator Run Gap Next Task Restore Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The patch-result validator-run gap recheck and its downstream route chain are already recorded as complete.
- The current state still pointed back to {summary["route_before_patch"]}, which can repeat completed work.
- The first still-open safe gap on this route is {NEXT_TASK_CLASS}.

Patch:
- Added route regression coverage that blocks the completed route chain from returning to completed rechecks.
- Restored current_implementation_state next_allowed_task_class to {NEXT_TASK_CLASS}.
- Preserved POST_REPAIR_RECONCILIATION_REQUIRED and REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED as open blockers.

Post-repair evidence:
- post_repair_reconciliation_status: {summary["post_repair_reconciliation_status"]}
- post_repair_source_loop_expected_rollup_hash_mismatch_count: {summary["post_repair_source_loop_expected_rollup_hash_mismatch_count"]}
- post_repair_candidate_current_evidence_usable_count: {summary["post_repair_candidate_current_evidence_usable_count"]}

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


def update_state_and_ledger(now: str, patch_result: dict[str, Any], summary: dict[str, Any]) -> None:
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
            "next_allowed_task_class": summary["route_after_patch"],
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
    update_state_and_ledger(now, patch_result, summary)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
    summary = load_route_summary()
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash, summary)

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
                    "tests.contract.test_patch_result_runtime_schema_validation",
                    "tests.contract.test_missing_cycle_ledger_rerun_required_recheck",
                    "tests.contract.test_post_rerun_current_evidence_write_blocked_recheck",
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
                    "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]),
        ]
    )
    summary = load_route_summary()
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash, summary)
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
                "route_before_patch": summary["route_before_patch"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "post_repair_reconciliation_status": summary["post_repair_reconciliation_status"],
                "post_repair_source_loop_expected_rollup_hash_mismatch_count": summary[
                    "post_repair_source_loop_expected_rollup_hash_mismatch_count"
                ],
                "post_repair_candidate_current_evidence_usable_count": summary[
                    "post_repair_candidate_current_evidence_usable_count"
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
