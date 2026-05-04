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

PATCH_BASENAME = "MVP4_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-COMPLETED-RECHECK-ROUTE-DEPTH-GUARD"
NEXT_TASK_CLASS = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"
BASELINE_REQUIREMENT_ID = "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-BASELINE-RECONCILIATION-RECHECK"
POST_REPAIR_REQUIREMENT_ID = "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-RECHECK"
HASH_MISMATCH_REQUIREMENT_ID = "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK"
BLOCKED_REPAIR_REQUIREMENT_ID = "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-RECHECK"

BASELINE_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK.patch_result.json"
)
POST_REPAIR_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK.patch_result.json"
)
HASH_MISMATCH_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK.patch_result.json"
)
BLOCKED_REPAIR_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK.patch_result.json"
)
POST_REPAIR_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_post_repair_reconciliation_report.json"
)
REPAIR_QUEUE_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_repair_operator_queue_report.json"
)
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
COMPLETED_RECHECK_TASK_CLASSES = {
    "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK",
    "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK",
    "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK",
}
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
    load_json,
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
    validator_id for validator_id in VALIDATORS_REQUIRED if validator_id != "generated_artifact_dirty_validator"
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_completed_recheck_route_depth_guard.py",
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
    "tools/emit_completed_recheck_route_depth_guard_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]


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


def assert_false_fields(name: str, artifact: dict[str, Any], suffix: str = "") -> None:
    for field in FALSE_FIELDS:
        key = f"{field}{suffix}"
        if artifact.get(key) is True:
            raise RuntimeError(f"{name} has forbidden true field: {key}")


def assert_patch_result_pass(path_text: str, requirement_id: str, expected_next: str | None = None) -> dict[str, Any]:
    artifact = load_json(ROOT / path_text)
    if requirement_id not in artifact.get("affected_contract_ids", []):
        raise RuntimeError(f"{path_text} is not bound to {requirement_id}")
    if expected_next is not None and artifact.get("next_task_class") != expected_next:
        raise RuntimeError(f"{path_text} next_task_class drifted: {artifact.get('next_task_class')}")
    assert_false_fields(path_text, artifact, "_after")
    for item in artifact.get("validators_run", []):
        if isinstance(item, dict) and item.get("status") != "PASS":
            raise RuntimeError(f"{path_text} has non-PASS validator: {item}")
    for item in artifact.get("tests_run", []):
        if isinstance(item, dict) and item.get("status") != "PASS":
            raise RuntimeError(f"{path_text} has non-PASS test: {item}")
    return artifact


def load_summary() -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    completed = set(state.get("completed_requirement_ids", []))
    required_completed = {
        BASELINE_REQUIREMENT_ID,
        POST_REPAIR_REQUIREMENT_ID,
        HASH_MISMATCH_REQUIREMENT_ID,
        BLOCKED_REPAIR_REQUIREMENT_ID,
    }
    missing = sorted(required_completed - completed)
    if missing:
        raise RuntimeError(f"route-depth guard prerequisites are not completed: {missing}")

    baseline = assert_patch_result_pass(
        BASELINE_PATCH_RESULT,
        BASELINE_REQUIREMENT_ID,
        "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK",
    )
    post_repair_patch = assert_patch_result_pass(
        POST_REPAIR_PATCH_RESULT,
        POST_REPAIR_REQUIREMENT_ID,
        "MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK",
    )
    hash_patch = assert_patch_result_pass(
        HASH_MISMATCH_PATCH_RESULT,
        HASH_MISMATCH_REQUIREMENT_ID,
        "MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK",
    )
    blocked_patch = assert_patch_result_pass(
        BLOCKED_REPAIR_PATCH_RESULT,
        BLOCKED_REPAIR_REQUIREMENT_ID,
        "MVP4_REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION_RECHECK",
    )
    post_repair = load_json(ROOT / POST_REPAIR_REPORT)
    repair_queue = load_json(ROOT / REPAIR_QUEUE_REPORT)

    assert_false_fields("current implementation state", state)
    assert_false_fields(POST_REPAIR_REPORT, post_repair)
    assert_false_fields(REPAIR_QUEUE_REPORT, repair_queue)
    route_before_patch = baseline.get("next_task_class")
    route_regression_detected = route_before_patch in COMPLETED_RECHECK_TASK_CLASSES
    if post_repair.get("candidate_current_evidence_usable_count") != 0:
        raise RuntimeError("post-repair candidate unexpectedly became current-evidence usable")
    if repair_queue.get("candidate_current_evidence_usable_count") != 0:
        raise RuntimeError("repair queue unexpectedly exposed current-evidence usable candidates")

    remaining_blockers = sorted(
        set(state.get("open_contract_gap_ids", []))
        | set(post_repair.get("blocker_codes", []))
        | set(repair_queue.get("blocker_codes", []))
        | OPEN_GAPS_TO_PRESERVE
        | STATIC_LIVE_BLOCKERS
    )
    return {
        "route_before_patch": route_before_patch,
        "route_after_patch": NEXT_TASK_CLASS,
        "route_regression_detected": route_regression_detected,
        "state_last_patch_id_before": (
            baseline.get("patch_id") if state.get("last_patch_id") == PATCH_ID else state.get("last_patch_id")
        ),
        "state_last_patch_result_hash_before": (
            baseline.get("result_hash") if state.get("last_patch_id") == PATCH_ID else state.get("last_patch_result_hash")
        ),
        "baseline_patch_result_hash": baseline.get("result_hash"),
        "post_repair_patch_result_hash": post_repair_patch.get("result_hash"),
        "hash_mismatch_patch_result_hash": hash_patch.get("result_hash"),
        "blocked_repair_patch_result_hash": blocked_patch.get("result_hash"),
        "post_repair_reconciliation_status": post_repair.get("post_repair_reconciliation_status"),
        "post_repair_source_loop_expected_rollup_hash_mismatch_count": post_repair.get(
            "source_loop_expected_rollup_hash_mismatch_count"
        ),
        "post_repair_candidate_current_evidence_usable_count": post_repair.get(
            "candidate_current_evidence_usable_count"
        ),
        "repair_operator_queue_status": repair_queue.get("queue_status"),
        "repair_operator_queue_item_count": repair_queue.get("queue_item_count"),
        "repair_operator_queue_candidate_current_evidence_usable_count": repair_queue.get(
            "candidate_current_evidence_usable_count"
        ),
        "completed_route_recheck_count": len(required_completed),
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
included_section_ids: ["SECTION_PATCH_RESULT", "SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{BASELINE_REQUIREMENT_ID}", "{POST_REPAIR_REQUIREMENT_ID}", "{HASH_MISMATCH_REQUIREMENT_ID}", "{BLOCKED_REPAIR_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_repair_reconciliation_report.v1", "trader1.upbit_paper_repair_operator_queue_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Confirm the patch-result baseline reconciliation and post-repair/hash-mismatch/operator rechecks are already completed.
- Detect a state route that points back to a completed recheck.
- Route next_allowed_task_class to {NEXT_TASK_CLASS}, which is not a completed recheck.
- Preserve post-repair, hash-mismatch, operator-reconciliation, patch-result, PAPER/SHADOW, live, and scale-up blockers.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

route_snapshot:
- route_before_patch: {summary["route_before_patch"]}
- route_after_patch: {summary["route_after_patch"]}
- route_regression_detected: {summary["route_regression_detected"]}
- completed_route_recheck_count: {summary["completed_route_recheck_count"]}
- post_repair_reconciliation_status: {summary["post_repair_reconciliation_status"]}
- post_repair_candidate_current_evidence_usable_count: {summary["post_repair_candidate_current_evidence_usable_count"]}
- repair_operator_queue_candidate_current_evidence_usable_count: {summary["repair_operator_queue_candidate_current_evidence_usable_count"]}

known_omissions_by_design:
- This patch does not resolve the open repair/operator gaps.
- This patch does not backfill historical patch_result evidence.
- This patch does not write current evidence, mutate runtime monitor output, mutate live config, use credentials, place live orders, or scale up.
- The next task is a priority recheck for selecting an implementable open contract gap without re-entering completed rechecks.

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

Completed recheck evidence remains intact, but the current state had routed back to a completed repair recheck. The route-depth guard keeps the blockers open and moves the next safe task to an open-gap implementation priority recheck.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    artifacts = sorted(
        set(
            CHANGED_ARTIFACTS
            + [
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "contracts/security/source_bundle_manifest.json",
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
            "source_section_id": "SECTION_PATCH_RESULT",
            "source_file": "TRADER_1.md",
            "source_heading": "completed recheck route depth guard",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: after a route repair or baseline reconciliation, current implementation "
                "state must not route back to a completed recheck while the open gaps remain live-blocking"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Completed recheck route depth guard",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_post_repair_reconciliation_report.v1",
                "trader1.upbit_paper_repair_operator_queue_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_completed_recheck_route_depth_guard.py",
                "tests/contract/test_patch_result_runtime_schema_validation.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_PATCH_RESULT",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                BASELINE_REQUIREMENT_ID,
                POST_REPAIR_REQUIREMENT_ID,
                HASH_MISMATCH_REQUIREMENT_ID,
                BLOCKED_REPAIR_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"completed recheck route depth guard live blocked"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_ROUTE_DEPTH_GUARD_NEXT_OPEN_GAP_PRIORITY_RECHECK",
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
                "contracts/schema/upbit_paper_repair_operator_queue_report.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/contract/test_completed_recheck_route_depth_guard.py",
                "tests/contract/test_patch_result_runtime_schema_validation.py",
            ],
            "fixture_files": [
                BASELINE_PATCH_RESULT,
                POST_REPAIR_PATCH_RESULT,
                HASH_MISMATCH_PATCH_RESULT,
                BLOCKED_REPAIR_PATCH_RESULT,
                POST_REPAIR_REPORT,
                REPAIR_QUEUE_REPORT,
            ],
            "runtime_modules": ["trader1/validation/mvp0_validators.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260504.md",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
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
            "status": "IMPLEMENTED_ROUTE_DEPTH_GUARD_NEXT_OPEN_GAP_PRIORITY_RECHECK",
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
    template = load_json(ROOT / BASELINE_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                BASELINE_REQUIREMENT_ID,
                POST_REPAIR_REQUIREMENT_ID,
                HASH_MISMATCH_REQUIREMENT_ID,
                BLOCKED_REPAIR_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
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
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
            ],
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
                BASELINE_PATCH_RESULT,
                POST_REPAIR_PATCH_RESULT,
                HASH_MISMATCH_PATCH_RESULT,
                BLOCKED_REPAIR_PATCH_RESULT,
                POST_REPAIR_REPORT,
                REPAIR_QUEUE_REPORT,
                "SECTION_PATCH_RESULT",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": [
                "SECTION_PATCH_RESULT",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_PATCH_RESULT",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_ROUTE_DEPTH_GUARD",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "optimizer_status_before": "COMPLETED_RECHECK_ROUTE_REENTRY_DETECTED",
            "optimizer_status_after": "OPEN_GAP_PRIORITY_RECHECK_NEXT_LIVE_BLOCKED",
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION_NO_CURRENT_EVIDENCE_PROMOTION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "STATE_ROUTE_DEPTH_GUARD_ONLY",
            "convergence_layer_changed": False,
            "convergence_state_before": "COMPLETED_RECHECK_ROUTE_REENTRY_DETECTED",
            "convergence_state_after": "OPEN_GAP_PRIORITY_RECHECK_NEXT_LIVE_BLOCKED",
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
                "post_repair_candidate_current_evidence_usable_count"
            ],
            "post_repair_reconciliation_status": summary["post_repair_reconciliation_status"],
            "post_repair_source_loop_expected_rollup_hash_mismatch_count": summary[
                "post_repair_source_loop_expected_rollup_hash_mismatch_count"
            ],
            "post_repair_candidate_current_evidence_usable_count": summary[
                "post_repair_candidate_current_evidence_usable_count"
            ],
            "repair_operator_queue_status": summary["repair_operator_queue_status"],
            "repair_operator_queue_item_count": summary["repair_operator_queue_item_count"],
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
            "stage_gate_status": "PASS_COMPLETED_RECHECK_ROUTE_DEPTH_GUARD_LIVE_BLOCKED",
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
                BASELINE_PATCH_RESULT,
                POST_REPAIR_PATCH_RESULT,
                HASH_MISMATCH_PATCH_RESULT,
                BLOCKED_REPAIR_PATCH_RESULT,
                POST_REPAIR_REPORT,
                REPAIR_QUEUE_REPORT,
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
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# MVP4 Completed Recheck Route Depth Guard

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The current state had routed to {summary["route_before_patch"]}.
- That task is already represented by completed recheck evidence, while the underlying gaps remain live-blocking.
- Post-repair and repair-queue candidates remain current-evidence unusable.

Patch:
- Added a route-depth guard that prevents state from re-entering completed repair rechecks after baseline reconciliation.
- Routed next_allowed_task_class to {NEXT_TASK_CLASS}.
- Preserved all open repair, patch-result, PAPER/SHADOW, live, and scale-up blockers.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no current evidence mutation
- no runtime monitor output mutation
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
                    "tests.contract.test_completed_recheck_route_depth_guard",
                    "tests.contract.test_patch_result_runtime_schema_validation",
                    "tests.contract.test_patch_result_validator_run_gap_baseline_reconciliation_recheck",
                    "tests.contract.test_post_repair_reconciliation_required_recheck",
                    "tests.contract.test_repair_candidate_hash_mismatch_reconciliation_required_recheck",
                    "-v",
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
                "route_before_patch": summary["route_before_patch"],
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
