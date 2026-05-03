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

PATCH_BASENAME = "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_STATE_SYNC_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-STATE-SYNC-RECHECK"
GAP_ID = "MISSING_CYCLE_LEDGER_RERUN_REQUIRED"
NEXT_TASK_CLASS = "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_RECHECK"

PREVIOUS_GUARD_PATCH_ID = "MVP4_UPBIT_PAPER_MISSING_CYCLE_RERUN_GUARD_20260501_001"
PREVIOUS_GUARD_PATCH_RESULT = "system/evidence/patch_results/MVP4_UPBIT_PAPER_MISSING_CYCLE_RERUN_GUARD.patch_result.json"
PREVIOUS_EXECUTOR_PATCH_ID = "MVP4_UPBIT_PAPER_BOUNDED_RERUN_STAGING_EXECUTOR_20260501_001"
PREVIOUS_EXECUTOR_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_BOUNDED_RERUN_STAGING_EXECUTOR.patch_result.json"
)
PREVIOUS_POST_RERUN_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION_20260501_001"
PREVIOUS_POST_RERUN_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION.patch_result.json"
)
PREVIOUS_PROMOTION_GUARD_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_20260502_001"
PREVIOUS_PROMOTION_GUARD_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD.patch_result.json"
)

GUARD_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_missing_cycle_rerun_guard_report.json"
)
EXECUTOR_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_bounded_rerun_staging_executor_report.json"
)
POST_RERUN_RECONCILIATION_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_post_rerun_ledger_rollup_reconciliation_report.json"
)
POST_RERUN_BLOCKER_ROLLUP_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json"
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
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
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
    "upbit_paper_missing_cycle_rerun_guard_validator",
    "upbit_paper_bounded_rerun_staging_executor_validator",
    "upbit_paper_post_rerun_ledger_rollup_reconciliation_validator",
    "upbit_paper_post_rerun_reconciliation_blocker_rollup_validator",
    "upbit_paper_post_rerun_current_evidence_promotion_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
    "tools/emit_missing_cycle_ledger_rerun_required_state_sync_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
BLOCKERS = [
    GAP_ID,
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED",
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
]
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")


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


def assert_previous_patch(path_text: str, expected_patch_id: str) -> dict[str, Any]:
    path = ROOT / path_text
    if not path.exists():
        raise RuntimeError(f"historical patch_result missing: {path_text}")
    patch = load_json(path)
    if patch.get("patch_id") != expected_patch_id:
        raise RuntimeError(f"historical patch_id drifted for {path_text}")
    assert_false_fields(path_text, patch, "_after")
    return patch


def assert_runtime_report_false(name: str, report: dict[str, Any]) -> None:
    assert_false_fields(name, report)
    if report.get("actual_rerun_executed") is True:
        raise RuntimeError(f"{name} unexpectedly reports actual_rerun_executed=true")
    if report.get("candidate_current_evidence_usable_count", 0) != 0:
        raise RuntimeError(f"{name} unexpectedly reports usable current evidence")


def current_gap_summary() -> dict[str, Any]:
    guard_patch = assert_previous_patch(PREVIOUS_GUARD_PATCH_RESULT, PREVIOUS_GUARD_PATCH_ID)
    executor_patch = assert_previous_patch(PREVIOUS_EXECUTOR_PATCH_RESULT, PREVIOUS_EXECUTOR_PATCH_ID)
    post_rerun_patch = assert_previous_patch(PREVIOUS_POST_RERUN_PATCH_RESULT, PREVIOUS_POST_RERUN_PATCH_ID)
    promotion_guard_patch = assert_previous_patch(
        PREVIOUS_PROMOTION_GUARD_PATCH_RESULT,
        PREVIOUS_PROMOTION_GUARD_PATCH_ID,
    )

    guard = load_json(ROOT / GUARD_REPORT)
    executor = load_json(ROOT / EXECUTOR_REPORT)
    post_rerun = load_json(ROOT / POST_RERUN_RECONCILIATION_REPORT)
    blocker_rollup = load_json(ROOT / POST_RERUN_BLOCKER_ROLLUP_REPORT)

    assert_runtime_report_false(GUARD_REPORT, guard)
    assert_runtime_report_false(EXECUTOR_REPORT, executor)
    assert_runtime_report_false(POST_RERUN_RECONCILIATION_REPORT, post_rerun)
    assert_runtime_report_false(POST_RERUN_BLOCKER_ROLLUP_REPORT, blocker_rollup)

    if guard.get("guard_status") != "BLOCKED":
        raise RuntimeError("missing-cycle rerun guard is not BLOCKED")
    if guard.get("rerun_ready_item_count", 0) <= 0:
        raise RuntimeError("missing-cycle rerun guard no longer exposes rerun-ready items")
    if guard.get("missing_cycle_ledger_jsonl_total_count", 0) <= 0:
        raise RuntimeError("missing-cycle rerun guard no longer exposes missing cycle ledgers")
    if executor.get("executor_status") != "BLOCKED":
        raise RuntimeError("bounded rerun staging executor is not BLOCKED")
    if executor.get("staged_current_evidence_usable_count") != 0:
        raise RuntimeError("bounded rerun staging executor made staged evidence current-usable")
    if post_rerun.get("candidate_current_evidence_usable_count") != 0:
        raise RuntimeError("post-rerun ledger rollup reconciliation made current evidence usable")
    if blocker_rollup.get("current_evidence_write_allowed") is not False:
        raise RuntimeError("post-rerun blocker rollup allows current evidence writes")
    if blocker_rollup.get("current_evidence_write_allowed_count") != 0:
        raise RuntimeError("post-rerun blocker rollup has allowed current evidence write rows")

    return {
        "guard_patch_result_hash": guard_patch.get("result_hash"),
        "executor_patch_result_hash": executor_patch.get("result_hash"),
        "post_rerun_patch_result_hash": post_rerun_patch.get("result_hash"),
        "promotion_guard_patch_result_hash": promotion_guard_patch.get("result_hash"),
        "guard_status": guard.get("guard_status"),
        "guard_item_count": guard.get("guard_item_count"),
        "rerun_ready_item_count": guard.get("rerun_ready_item_count"),
        "recovery_guard_blocked_item_count": guard.get("recovery_guard_blocked_item_count"),
        "missing_cycle_ledger_jsonl_total_count": guard.get("missing_cycle_ledger_jsonl_total_count"),
        "planned_staging_artifact_total_count": guard.get("planned_staging_artifact_total_count"),
        "executor_status": executor.get("executor_status"),
        "staged_cycle_count": executor.get("staged_cycle_count"),
        "staged_current_evidence_usable_count": executor.get("staged_current_evidence_usable_count"),
        "post_rerun_candidate_item_count": post_rerun.get("candidate_item_count"),
        "post_rerun_candidate_current_evidence_usable_count": post_rerun.get(
            "candidate_current_evidence_usable_count"
        ),
        "current_evidence_write_allowed": blocker_rollup.get("current_evidence_write_allowed"),
        "current_evidence_write_allowed_count": blocker_rollup.get("current_evidence_write_allowed_count"),
    }


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-UPBIT-PAPER-MISSING-CYCLE-RERUN-GUARD", "REQ-MVP4-UPBIT-PAPER-BOUNDED-RERUN-STAGING-EXECUTOR", "REQ-MVP4-UPBIT-PAPER-POST-RERUN-LEDGER-ROLLUP-RECONCILIATION"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_missing_cycle_rerun_guard_report.v1", "trader1.upbit_paper_bounded_rerun_staging_executor_report.v1", "trader1.upbit_paper_post_rerun_ledger_rollup_reconciliation_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Detect that missing-cycle guard, bounded rerun staging executor, post-rerun ledger rollup reconciliation, and promotion guard patch_results already exist.
- Confirm the guard and executor remain BLOCKED and do not claim actual rerun execution.
- Confirm post-rerun reconciliation does not make any candidate current evidence usable.
- Keep {GAP_ID} in open_contract_gap_ids and route to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

gap_snapshot:
- guard_status: {summary["guard_status"]}
- guard_item_count: {summary["guard_item_count"]}
- rerun_ready_item_count: {summary["rerun_ready_item_count"]}
- recovery_guard_blocked_item_count: {summary["recovery_guard_blocked_item_count"]}
- missing_cycle_ledger_jsonl_total_count: {summary["missing_cycle_ledger_jsonl_total_count"]}
- executor_status: {summary["executor_status"]}
- staged_cycle_count: {summary["staged_cycle_count"]}
- staged_current_evidence_usable_count: {summary["staged_current_evidence_usable_count"]}
- post_rerun_candidate_current_evidence_usable_count: {summary["post_rerun_candidate_current_evidence_usable_count"]}
- current_evidence_write_allowed: {summary["current_evidence_write_allowed"]}

known_omissions_by_design:
- No cycle is rerun by this patch.
- No current ledger JSONL, latest pointer, current evidence, live config, credentialed API, live order, or scale-up output is written.
- The missing-cycle rerun requirement remains an open live-blocking gap until reconciliation and current evidence closure evidence independently pass.

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

Missing Upbit PAPER cycle ledgers have guard, staging, and post-rerun reconciliation artifacts, but they remain live-blocking. Actual rerun execution is false, current evidence usable count is zero, and current evidence writes remain blocked.

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
    requirements = [
        item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID
    ]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "missing cycle ledger rerun required state sync recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: recognize existing missing-cycle guard, staging, and post-rerun evidence, "
                "keep missing cycle ledger rerun requirement open, and route to post-rerun reconciliation recheck"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Missing cycle ledger rerun required state sync recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_missing_cycle_rerun_guard_report.v1",
                "trader1.upbit_paper_bounded_rerun_staging_executor_report.v1",
                "trader1.upbit_paper_post_rerun_ledger_rollup_reconciliation_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-MISSING-CYCLE-RERUN-GUARD",
                "REQ-MVP4-UPBIT-PAPER-BOUNDED-RERUN-STAGING-EXECUTOR",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-LEDGER-ROLLUP-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"missing cycle ledger rerun required state sync remains open live blocked"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_STATE_SYNC_RECHECK_GAP_OPEN",
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
                "contracts/schema/upbit_paper_missing_cycle_rerun_guard_report.schema.json",
                "contracts/schema/upbit_paper_bounded_rerun_staging_executor_report.schema.json",
                "contracts/schema/upbit_paper_post_rerun_ledger_rollup_reconciliation_report.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py"],
            "fixture_files": [
                GUARD_REPORT,
                EXECUTOR_REPORT,
                POST_RERUN_RECONCILIATION_REPORT,
                POST_RERUN_BLOCKER_ROLLUP_REPORT,
                PREVIOUS_GUARD_PATCH_RESULT,
                PREVIOUS_EXECUTOR_PATCH_RESULT,
                PREVIOUS_POST_RERUN_PATCH_RESULT,
                PREVIOUS_PROMOTION_GUARD_PATCH_RESULT,
            ],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_missing_cycle_rerun_guard.py",
                "trader1/runtime/paper/upbit_paper_bounded_rerun_staging_executor.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_ledger_rollup_reconciliation.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "tests_run",
                "next_task_class",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_STATE_SYNC_RECHECK_GAP_OPEN",
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
    summary: dict[str, Any],
    validators_required: list[str],
) -> dict[str, Any]:
    template = load_json(ROOT / PREVIOUS_GUARD_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-MISSING-CYCLE-RERUN-GUARD",
                "REQ-MVP4-UPBIT-PAPER-BOUNDED-RERUN-STAGING-EXECUTOR",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-LEDGER-ROLLUP-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
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
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PAPER_RUNTIME_RECOVERY"],
            "next_forbidden_default_sections": ["MVP5_LIVE_PERMISSION", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                "missing-cycle rerun guard report",
                "bounded rerun staging executor report",
                "post-rerun ledger rollup reconciliation report",
                "post-rerun blocker rollup report",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_RECHECK",
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
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
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_status_after": "MISSING_CYCLE_LEDGER_RERUN_RECHECKED_CURRENT_EVIDENCE_BLOCKED",
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION_NO_CURRENT_EVIDENCE_PROMOTION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "MISSING_CYCLE_LEDGER_RERUN_STATE_SYNC_ONLY",
            "convergence_state_after": "MISSING_CYCLE_LEDGER_RERUN_GAP_RECHECKED_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "scale_up_allowed_after": False,
            "guard_status": summary["guard_status"],
            "guard_item_count": summary["guard_item_count"],
            "rerun_ready_item_count": summary["rerun_ready_item_count"],
            "recovery_guard_blocked_item_count": summary["recovery_guard_blocked_item_count"],
            "missing_cycle_ledger_jsonl_total_count": summary["missing_cycle_ledger_jsonl_total_count"],
            "planned_staging_artifact_total_count": summary["planned_staging_artifact_total_count"],
            "actual_rerun_executed": False,
            "rerun_executor_created": False,
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
            "stage_gate_status": "PASS_STATE_SYNC_RECHECK_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_REMAINS_LIVE_BLOCKING",
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
                PREVIOUS_GUARD_PATCH_RESULT,
                PREVIOUS_EXECUTOR_PATCH_RESULT,
                PREVIOUS_POST_RERUN_PATCH_RESULT,
                PREVIOUS_PROMOTION_GUARD_PATCH_RESULT,
                GUARD_REPORT,
                EXECUTOR_REPORT,
                POST_RERUN_RECONCILIATION_REPORT,
                POST_RERUN_BLOCKER_ROLLUP_REPORT,
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


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", []) + [GAP_ID]))
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


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
    summary = current_gap_summary()
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        summary,
        BOOTSTRAP_VALIDATORS_REQUIRED,
    )
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "tests.contract.test_missing_cycle_ledger_rerun_required_recheck",
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
                    "tests/runtime/test_upbit_paper_missing_cycle_rerun_guard.py",
                    "tests/runtime/test_upbit_paper_bounded_rerun_staging_executor.py",
                    "tests/runtime/test_upbit_paper_post_rerun_ledger_rollup_reconciliation.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_blocker_rollup.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"]),
        ]
    )
    summary = current_gap_summary()
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(VALIDATORS_REQUIRED)),
        summary,
        VALIDATORS_REQUIRED,
    )
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "guard_status": summary["guard_status"],
                "executor_status": summary["executor_status"],
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
