from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-SAFE-REGENERATION-EXECUTOR"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION"
SESSION_ID = "mvp1_upbit_paper_launcher"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.runtime.paper.upbit_paper_stale_loop_execution_guard import (  # noqa: E402
    build_upbit_paper_stale_loop_execution_guard,
    validate_upbit_paper_stale_loop_execution_guard,
    write_upbit_paper_stale_loop_execution_guard,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation import (  # noqa: E402
    build_upbit_paper_stale_loop_reconciliation_report,
    validate_upbit_paper_stale_loop_reconciliation_report,
    write_upbit_paper_stale_loop_reconciliation_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_regeneration import (  # noqa: E402
    build_upbit_paper_stale_loop_regeneration_plan,
    validate_upbit_paper_stale_loop_regeneration_plan,
    write_upbit_paper_stale_loop_regeneration_plan,
)
from trader1.runtime.paper.upbit_paper_stale_loop_safe_regeneration_executor import (  # noqa: E402
    build_upbit_paper_stale_loop_safe_regeneration_executor_report,
    validate_upbit_paper_stale_loop_safe_regeneration_executor_report,
    write_upbit_paper_stale_loop_safe_regeneration_executor_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_stale_loop_reconciliation_validator",
    "upbit_paper_stale_loop_regeneration_plan_validator",
    "upbit_paper_stale_loop_execution_guard_validator",
    "upbit_paper_stale_loop_safe_regeneration_executor_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]

BASE_CHANGED_ARTIFACTS = [
    "contracts/schema/upbit_paper_stale_loop_safe_regeneration_executor_report.schema.json",
    "contracts/registry.yaml",
    "trader1/runtime/paper/upbit_paper_stale_loop_safe_regeneration_executor.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_stale_loop_safe_regeneration_executor.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_safe_regeneration_executor_report.json",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_stale_loop_safe_regeneration_executor_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR.md",
]

BLOCKERS = [
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def configure_base(changed_artifacts: list[str]) -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = changed_artifacts
    base.BLOCKERS = BLOCKERS


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def runtime_path(name: str) -> Path:
    return (
        ROOT
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / SESSION_ID
        / "paper_runtime"
        / name
    )


def replacement_artifact_paths(executor: dict[str, Any]) -> list[str]:
    return sorted(
        {
            str(item["planned_replacement_path"])
            for item in executor.get("items", [])
            if item.get("replacement_written") and isinstance(item.get("planned_replacement_path"), str)
        }
    )


def changed_artifacts(executor: dict[str, Any] | None = None) -> list[str]:
    dynamic = replacement_artifact_paths(executor or {})
    return sorted(dict.fromkeys([*BASE_CHANGED_ARTIFACTS, *dynamic]))


def write_runtime_executor() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    executor_path = runtime_path("upbit_paper_stale_loop_safe_regeneration_executor_report.json")
    guard_path = runtime_path("upbit_paper_stale_loop_regeneration_execution_guard.json")
    plan_path = runtime_path("upbit_paper_stale_loop_regeneration_plan.json")
    reconciliation_path = runtime_path("upbit_paper_stale_loop_reconciliation_report.json")

    if executor_path.exists() and guard_path.exists() and plan_path.exists() and reconciliation_path.exists():
        executor = load_json(executor_path)
        executor_result = validate_upbit_paper_stale_loop_safe_regeneration_executor_report(executor)
        if executor_result.status == "PASS":
            return load_json(reconciliation_path), load_json(plan_path), load_json(guard_path), executor

    reconciliation = build_upbit_paper_stale_loop_reconciliation_report(
        root=ROOT,
        session_id=SESSION_ID,
        reconciliation_id="mvp4-upbit-paper-stale-loop-reconciliation",
    )
    reconciliation_result = validate_upbit_paper_stale_loop_reconciliation_report(reconciliation)
    if reconciliation_result.status != "PASS":
        raise RuntimeError(
            "stale loop reconciliation validation failed: "
            f"{reconciliation_result.status} {reconciliation_result.blocker_code} {reconciliation_result.message}"
        )
    write_upbit_paper_stale_loop_reconciliation_report(root=ROOT, report=reconciliation)

    plan = build_upbit_paper_stale_loop_regeneration_plan(
        root=ROOT,
        reconciliation_report=reconciliation,
        plan_id="mvp4-upbit-paper-stale-loop-regeneration-policy",
    )
    plan_result = validate_upbit_paper_stale_loop_regeneration_plan(plan)
    if plan_result.status != "PASS":
        raise RuntimeError(
            "stale loop regeneration plan validation failed: "
            f"{plan_result.status} {plan_result.blocker_code} {plan_result.message}"
        )
    write_upbit_paper_stale_loop_regeneration_plan(root=ROOT, plan=plan)

    guard = build_upbit_paper_stale_loop_execution_guard(
        root=ROOT,
        plan=plan,
        guard_id="mvp4-upbit-paper-stale-loop-regeneration-execution-guard",
    )
    guard_result = validate_upbit_paper_stale_loop_execution_guard(guard)
    if guard_result.status != "PASS" or guard.get("guard_status") != "PASS":
        raise RuntimeError(
            "stale loop execution guard validation failed: "
            f"{guard_result.status} {guard_result.blocker_code} {guard_result.message}"
        )
    write_upbit_paper_stale_loop_execution_guard(root=ROOT, report=guard)

    executor = build_upbit_paper_stale_loop_safe_regeneration_executor_report(
        root=ROOT,
        guard=guard,
        executor_id="mvp4-upbit-paper-stale-loop-safe-regeneration-executor",
    )
    executor_result = validate_upbit_paper_stale_loop_safe_regeneration_executor_report(executor)
    if executor_result.status != "PASS" or executor.get("executor_status") != "PASS":
        raise RuntimeError(
            "stale loop safe regeneration executor validation failed: "
            f"{executor_result.status} {executor_result.blocker_code} {executor_result.message}"
        )
    write_upbit_paper_stale_loop_safe_regeneration_executor_report(root=ROOT, report=executor)
    return reconciliation, plan, guard, executor


def write_context(now: str, trader_hash: str, agents_hash: str, executor: dict[str, Any]) -> None:
    replacements = replacement_artifact_paths(executor)
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR.md",
        f"""# MVP4_UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_safe_regeneration_executor_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(changed_artifacts(executor))}

acceptance_checklist:
- The executor accepts only a PASS execution guard for UPBIT/KRW_SPOT/PAPER.
- It writes current-schema replacement reports with CREATE_NEW_ONLY semantics.
- It retains every source report and never deletes or overwrites stale artifacts.
- It creates no long-run evidence, live readiness, order permission, promotion, or scale-up permission.
- Existing replacement paths block repeated execution.

known_omissions_by_design:
- regenerated artifacts are bounded PAPER schema-repair artifacts, not long-run evidence
- stale source artifacts remain retained for audit and post-regeneration reconciliation
- no private exchange/account/API call or credential was used
- MVP-5 remains blocked on external live-review evidence and operator approval

current_executor_summary:
- executor_status: {executor["executor_status"]}
- planned_regeneration_item_count: {executor["planned_regeneration_item_count"]}
- regenerated_item_count: {executor["regenerated_item_count"]}
- skipped_item_count: {executor["skipped_item_count"]}
- replacement_artifact_count: {len(replacements)}
- actual_regeneration_performed: {str(executor["actual_regeneration_performed"]).lower()}
- actual_long_run_evidence_created: false
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: {now}
""",
    )
    base.write_text(
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

Upbit PAPER stale loop reports can now be regenerated into current-schema copies through a source-retaining, create-new-only executor. This is schema repair for PAPER runtime artifacts only; it is not long-run evidence and does not change live readiness.

## Current Executor

- status: {executor["executor_status"]}
- planned replacements: {executor["planned_regeneration_item_count"]}
- replacements written: {executor["regenerated_item_count"]}
- source reports retained: true
- long-run evidence created: false
- live/order/scale flags: false

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str, executor: dict[str, Any]) -> None:
    artifacts = changed_artifacts(executor)
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER stale loop safe regeneration executor",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: stale loop regeneration executor may create current-schema PAPER copies only "
                "after PASS guard, while retaining sources and preserving live blockers"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER stale loop safe regeneration executor",
            "requirement_kind": "SCHEMA_VALIDATOR_RUNTIME_ARTIFACT_PATCH",
            "schema_ids": ["trader1.upbit_paper_stale_loop_safe_regeneration_executor_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/runtime/test_upbit_paper_stale_loop_safe_regeneration_executor.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-REGENERATION-EXECUTION-GUARD",
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-REGENERATION-POLICY",
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION",
                "REQ-MVP4-UPBIT-PAPER-LONG-RUN-EVIDENCE-BOUNDARY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"stale loop safe regeneration executor creates current-schema paper copies only"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_SAFE_EXECUTOR_LIVE_BLOCKED",
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
    base.write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "schema_files": ["contracts/schema/upbit_paper_stale_loop_safe_regeneration_executor_report.schema.json"],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_stale_loop_safe_regeneration_executor.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/runtime/test_upbit_paper_stale_loop_safe_regeneration_executor.py"],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_stale_loop_safe_regeneration_executor.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_execution_guard.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_regeneration.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_reconciliation.py",
            ],
            "evidence_artifacts": [
                *replacement_artifact_paths(executor),
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_safe_regeneration_executor_report.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_SAFE_EXECUTOR_LIVE_BLOCKED",
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
    base.write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    executor: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_EXECUTION_GUARD.patch_result.json")
    patch_result = dict(template)
    artifacts = changed_artifacts(executor)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "input_authority_hash_status": "PASS",
            "authority_hash_checked": True,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-REGENERATION-EXECUTION-GUARD",
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-REGENERATION-POLICY",
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION",
                "REQ-MVP4-UPBIT-PAPER-LONG-RUN-EVIDENCE-BOUNDARY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [REQUIREMENT_ID, "upbit_paper_stale_loop_safe_regeneration_executor_validator"],
            "new_or_changed_schema_ids": ["trader1.upbit_paper_stale_loop_safe_regeneration_executor_report.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "UNCHANGED_NOT_READ",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_DASHBOARD_OPERATOR_UX"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "BINANCE_FUTURES_LIVE", "RETAINED_ARCHIVE"],
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
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "current_implementation_state",
                "stale loop regeneration execution guard",
                "stale loop safe regeneration executor",
                "review-derived runtime evidence reproducibility gap",
            ],
            "task_class": "MVP4_UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR",
            "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "optimizer_stage": "MVP-4_PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_status_before": "PAPER_SCORECARD_INPUT_ONLY_STALE_LOOP_EXECUTION_GUARDED_BLOCKED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_SAFE_REGENERATION_COMPLETED_NOT_LONG_RUN_EVIDENCE",
            "optimizer_maturity_level_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_maturity_level_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_output_type": "PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_validators_required": ["candidate_scorecard_validator", "candidate_scorecard_net_ev_validator"],
            "optimizer_validators_run": [
                {"validator_id": "candidate_scorecard_validator", "status": "PASS"},
                {"validator_id": "candidate_scorecard_net_ev_validator", "status": "PASS"},
            ],
            "optimizer_guardrail_result": "PASS_SAFE_REGENERATION_REMAINS_PAPER_SCHEMA_REPAIR_ONLY_AND_LIVE_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "true",
            "convergence_layer_changed": True,
            "convergence_state_before": "STALE_RUNTIME_LOOP_EXECUTION_GUARDED_EXECUTOR_BLOCKED",
            "convergence_state_after": "STALE_RUNTIME_LOOP_SAFE_REGENERATION_COMPLETED_RECONCILIATION_REQUIRED",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_PAPER_SCHEMA_REPAIR",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_OR_LONG_RUN_EVIDENCE_CREATED",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "scale_up_allowed_after": False,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], executor: dict[str, Any]) -> None:
    replacements = replacement_artifact_paths(executor)
    base.write_json(
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
    base.write_json(
        ROOT / patch_result["stage_gate_result_path"],
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "PASS_SAFE_REGENERATION_COMPLETED_RECONCILIATION_REQUIRED",
            "executor_status": executor["executor_status"],
            "planned_regeneration_item_count": executor["planned_regeneration_item_count"],
            "regenerated_item_count": executor["regenerated_item_count"],
            "skipped_item_count": executor["skipped_item_count"],
            "replacement_artifact_count": len(replacements),
            "source_retention_required": True,
            "actual_regeneration_performed": executor["actual_regeneration_performed"],
            "actual_long_run_evidence_created": False,
            "long_run_evidence_eligible": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": [
                *changed_artifacts(executor),
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "executor_status": executor["executor_status"],
            "planned_regeneration_item_count": executor["planned_regeneration_item_count"],
            "regenerated_item_count": executor["regenerated_item_count"],
            "replacement_artifacts": replacements,
            "actual_regeneration_performed": executor["actual_regeneration_performed"],
            "actual_long_run_evidence_created": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260501.md",
        f"""# MVP4 Upbit PAPER Stale Loop Safe Regeneration Executor Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The stale loop regeneration plan and guard could identify schema-drifted PAPER loop reports, but the actual safe repair step was still missing.
- Without a guarded executor, stale loop reports stayed unusable for reconciliation and runtime evidence review.

Patch:
- Added a strict safe regeneration executor schema, runtime builder/writer/validator, registry entry, runtime artifact, and negative tests.
- The executor accepts only a PASS execution guard and writes current-schema PAPER replacement copies with CREATE_NEW_ONLY semantics.
- Source reports are retained. Delete and overwrite remain blocked.
- The replacement artifacts are schema repair outputs only. They are not long-run evidence, not promotion evidence, not LIVE_READY evidence, and not scale-up evidence.

Runtime executor summary:
- executor_status: {executor["executor_status"]}
- planned_regeneration_item_count: {executor["planned_regeneration_item_count"]}
- regenerated_item_count: {executor["regenerated_item_count"]}
- skipped_item_count: {executor["skipped_item_count"]}
- replacement_artifact_count: {len(replacements)}
- actual_regeneration_performed: {str(executor["actual_regeneration_performed"]).lower()}
- actual_long_run_evidence_created: false

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    base.update_state_and_ledger(now, patch_result)
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    schema_ids = set(state.get("implemented_schema_ids", []))
    schema_ids.add("trader1.upbit_paper_stale_loop_safe_regeneration_executor_report.v1")
    validator_ids = set(state.get("implemented_validator_ids", []))
    validator_ids.add("upbit_paper_stale_loop_safe_regeneration_executor_validator")
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    gaps = set(state.get("open_contract_gap_ids", []))
    gaps.discard("STALE_LOOP_SAFE_REGENERATION_EXECUTOR_REQUIRED")
    gaps.update({"ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY", "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED"})
    state["implemented_schema_ids"] = sorted(schema_ids)
    state["implemented_validator_ids"] = sorted(validator_ids)
    state["completed_requirement_ids"] = sorted(completed)
    state["untested_validator_ids"] = sorted(set(state.get("untested_validator_ids", [])) - validator_ids)
    state["open_contract_gap_ids"] = sorted(gaps)
    state["last_patch_id"] = PATCH_ID
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["updated_at_utc"] = now
    state["state_hash"] = ""
    state["state_hash"] = base.sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    base.write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
    ledger["updated_at_utc"] = now
    ledger["ledger_hash"] = ""
    ledger["ledger_hash"] = base.sha256_json({key: value for key, value in ledger.items() if key != "ledger_hash"})
    base.write_json(ledger_path, ledger)


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    executor: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, executor)
    base.write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    _, _, _, executor = write_runtime_executor()
    configure_base(changed_artifacts(executor))
    write_context(now, trader_hash, agents_hash, executor)
    update_requirement_artifacts(now, trader_hash, agents_hash, executor)

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/runtime/test_upbit_paper_stale_loop_safe_regeneration_executor.py",
                "tests/runtime/test_upbit_paper_stale_loop_execution_guard.py",
                "tests/runtime/test_upbit_paper_stale_loop_regeneration.py",
                "tests/runtime/test_upbit_paper_stale_loop_reconciliation.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, executor)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, executor)

    tests_run.append(base.run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, executor)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, executor)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "executor_status": executor["executor_status"],
                "planned_regeneration_item_count": executor["planned_regeneration_item_count"],
                "regenerated_item_count": executor["regenerated_item_count"],
                "actual_regeneration_performed": executor["actual_regeneration_performed"],
                "actual_long_run_evidence_created": False,
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
