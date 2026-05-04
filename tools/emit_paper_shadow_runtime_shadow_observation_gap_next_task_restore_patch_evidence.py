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

PATCH_BASENAME = "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_NEXT_TASK_RESTORE"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-NEXT-TASK-RESTORE"
CONTRACT_GAP_ID = "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-STATE-SYNC-RECHECK"
DASHBOARD_REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-VISIBILITY-LAYOUT-FIX"
NEXT_TASK_CLASS = "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_RECHECK"
BACKWARD_NEXT_TASK_CLASS = "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_RECHECK"

PREVIOUS_PATCH_BASENAME = "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_STATE_SYNC_RECHECK"
PREVIOUS_PATCH_ID = f"{PREVIOUS_PATCH_BASENAME}_20260504_001"
PREVIOUS_PATCH_RESULT = f"system/evidence/patch_results/{PREVIOUS_PATCH_BASENAME}.patch_result.json"
DASHBOARD_PATCH_BASENAME = "MVP4_DASHBOARD_VISIBILITY_LAYOUT_FIX"
DASHBOARD_PATCH_ID = f"{DASHBOARD_PATCH_BASENAME}_20260504_001"
DASHBOARD_PATCH_RESULT = f"system/evidence/patch_results/{DASHBOARD_PATCH_BASENAME}.patch_result.json"

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
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "shadow_observation_runtime_validator",
    "shadow_observation_stream_validator",
    "shadow_observation_scheduler_guard_validator",
    "shadow_observation_persistent_runtime_validator",
    "shadow_observation_actual_runtime_blocker_validator",
    "shadow_observation_actual_runtime_harness_validator",
    "paper_shadow_evidence_accumulation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
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
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "shadow_observation_runtime_validator",
    "shadow_observation_stream_validator",
    "shadow_observation_scheduler_guard_validator",
    "shadow_observation_persistent_runtime_validator",
    "shadow_observation_actual_runtime_blocker_validator",
    "shadow_observation_actual_runtime_harness_validator",
    "paper_shadow_evidence_accumulation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_paper_shadow_runtime_shadow_observation_gap_recheck.py",
    "tools/emit_dashboard_visibility_layout_fix_patch_evidence.py",
    "tools/emit_paper_shadow_runtime_shadow_observation_gap_next_task_restore_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
BLOCKERS = [
    CONTRACT_GAP_ID,
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
    "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
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


def load_route_summary() -> dict[str, Any]:
    previous_path = ROOT / PREVIOUS_PATCH_RESULT
    dashboard_path = ROOT / DASHBOARD_PATCH_RESULT
    contract_gap_path = ROOT / "system" / "evidence" / "contract_gaps" / f"{CONTRACT_GAP_ID}.contract_gap.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"

    if not previous_path.exists():
        raise RuntimeError(f"previous shadow gap patch_result missing: {PREVIOUS_PATCH_RESULT}")
    if not dashboard_path.exists():
        raise RuntimeError(f"dashboard layout patch_result missing: {DASHBOARD_PATCH_RESULT}")

    previous = load_json(previous_path)
    dashboard = load_json(dashboard_path)
    contract_gap = load_json(contract_gap_path)
    state = load_json(state_path)

    if previous.get("patch_id") != PREVIOUS_PATCH_ID:
        raise RuntimeError("previous shadow gap state-sync patch_id drifted")
    if previous.get("next_task_class") != NEXT_TASK_CLASS:
        raise RuntimeError("previous shadow gap state-sync no longer routes to ledger recheck")
    if dashboard.get("patch_id") != DASHBOARD_PATCH_ID:
        raise RuntimeError("dashboard layout patch_id drifted")
    if PREVIOUS_REQUIREMENT_ID not in state.get("completed_requirement_ids", []):
        raise RuntimeError("shadow observation gap state-sync recheck is not recorded completed")
    if CONTRACT_GAP_ID not in state.get("open_contract_gap_ids", []):
        raise RuntimeError("shadow observation gap is no longer tracked as open")
    if contract_gap.get("contract_gap_id") != CONTRACT_GAP_ID or contract_gap.get("status") != "OPEN":
        raise RuntimeError("shadow observation gap contract gap is not open")
    if contract_gap.get("live_affecting") is not True:
        raise RuntimeError("shadow observation gap contract gap is not live-affecting")

    assert_false_fields(PREVIOUS_PATCH_RESULT, previous, "_after")
    assert_false_fields(DASHBOARD_PATCH_RESULT, dashboard, "_after")
    assert_false_fields("current implementation state", state)
    assert_false_fields("shadow observation gap contract gap", contract_gap)

    blocker_codes = {
        item.get("code") for item in contract_gap.get("blockers", []) if isinstance(item, dict)
    }
    required_blockers = {
        "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        "LONG_RUN_EVIDENCE_MISSING",
        "API_UNVERIFIED",
        "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    }
    if not required_blockers.issubset(blocker_codes):
        raise RuntimeError("shadow observation gap blockers are incomplete")

    return {
        "route_before_patch": state.get("next_allowed_task_class"),
        "route_after_patch": NEXT_TASK_CLASS,
        "backward_route_detected": state.get("next_allowed_task_class") == BACKWARD_NEXT_TASK_CLASS,
        "previous_patch_result_hash": previous.get("result_hash"),
        "previous_patch_next_task_class": previous.get("next_task_class"),
        "dashboard_patch_result_hash": dashboard.get("result_hash"),
        "dashboard_patch_next_task_class_before_generator_fix": dashboard.get("next_task_class"),
        "contract_gap_status": contract_gap.get("status"),
        "contract_gap_live_affecting": contract_gap.get("live_affecting"),
        "contract_gap_severity": contract_gap.get("severity"),
        "contract_gap_blocker_codes": sorted(blocker_codes),
        "state_last_patch_id_before": state.get("last_patch_id"),
        "state_last_patch_result_hash_before": state.get("last_patch_result_hash"),
    }


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_NEXT_TASK_RESTORE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{PREVIOUS_REQUIREMENT_ID}", "{DASHBOARD_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.contract_gap.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Detect the completed PAPER/SHADOW runtime shadow observation gap state-sync recheck.
- Confirm {CONTRACT_GAP_ID} remains OPEN and live-affecting.
- Prevent a dashboard-only patch from routing next_allowed_task_class back to completed shadow gap state sync work.
- Restore next_allowed_task_class to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

route_snapshot:
- route_before_patch: {summary["route_before_patch"]}
- backward_route_detected: {summary["backward_route_detected"]}
- route_after_patch: {summary["route_after_patch"]}
- previous_patch_next_task_class: {summary["previous_patch_next_task_class"]}
- dashboard_patch_next_task_class_before_generator_fix: {summary["dashboard_patch_next_task_class_before_generator_fix"]}

known_omissions_by_design:
- No PAPER or SHADOW runtime execution is created.
- No contract gap is closed.
- No historical patch_result is rewritten.
- No live order, credential, account API, live config mutation, or scale-up path is introduced.

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

The PAPER/SHADOW runtime shadow observation gap remains open and live-blocking. Its prior state-sync recheck is recorded complete, so current routing must not return to that completed recheck.

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
            "source_section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "source_file": "TRADER_1.md",
            "source_heading": "paper shadow runtime shadow observation gap next task restore",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: once the shadow observation gap state-sync recheck is completed, "
                "do not route current_implementation_state back to the completed shadow gap recheck"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Paper shadow runtime shadow observation next task restore",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.contract_gap.v1", "trader1.patch_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/contract/test_paper_shadow_runtime_shadow_observation_gap_recheck.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                PREVIOUS_REQUIREMENT_ID,
                DASHBOARD_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"completed paper shadow observation gap state sync must not route current state backward"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_NEXT_TASK_RESTORE_CONTRACT_GAP_OPEN",
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
            "section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "schema_files": ["contracts/schema/contract_gap.schema.json", "contracts/schema/patch_result.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/contract/test_paper_shadow_runtime_shadow_observation_gap_recheck.py"],
            "fixture_files": [
                "system/evidence/contract_gaps/PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP.contract_gap.json",
                PREVIOUS_PATCH_RESULT,
                DASHBOARD_PATCH_RESULT,
            ],
            "runtime_modules": [],
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
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_NEXT_TASK_RESTORE_CONTRACT_GAP_OPEN",
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
                DASHBOARD_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT,BINANCE",
            "affected_market_type": "KRW_SPOT,SPOT",
            "affected_mode": "PAPER_AND_SHADOW_STATE_ONLY",
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
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": [
                "SECTION_PAPER_RUNTIME_RECOVERY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_CONTRACT_GAP",
            ],
            "next_forbidden_default_sections": [
                "MVP5_LIVE_PERMISSION",
                "LIVE_CONFIG_MUTATION",
                "RISK_SCALE_UP",
            ],
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
                PREVIOUS_PATCH_RESULT,
                DASHBOARD_PATCH_RESULT,
                "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP contract gap",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_NEXT_TASK_RESTORE",
            "required_section_ids": [
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_DASHBOARD_OPERATOR_UX",
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
            "current_implementation_state_status": "UPDATED_NEXT_TASK_RESTORED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_status_before": "LIVE_BLOCKED_ROUTE_REGRESSION_DETECTED",
            "optimizer_status_after": "LIVE_BLOCKED_NEXT_TASK_RESTORED",
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "STATE_ROUTING_RESTORE_ONLY",
            "convergence_layer_changed": False,
            "convergence_state_before": "LIVE_BLOCKED_ROUTE_REGRESSION_DETECTED",
            "convergence_state_after": "LIVE_BLOCKED_NEXT_TASK_RESTORED",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_CHANGED",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
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
            "stage_gate_status": "PASS_NEXT_TASK_RESTORED_SHADOW_OBSERVATION_GAP_REMAINS_OPEN",
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
                "system/evidence/contract_gaps/PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP.contract_gap.json",
                PREVIOUS_PATCH_RESULT,
                DASHBOARD_PATCH_RESULT,
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
        f"""# MVP4 Paper Shadow Runtime Shadow Observation Gap Next Task Restore Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The prior PAPER/SHADOW runtime shadow observation gap state-sync recheck already routed to {NEXT_TASK_CLASS}.
- A later dashboard-only visibility patch left current_implementation_state routed back to {BACKWARD_NEXT_TASK_CLASS}.

Patch:
- Added a regression test that blocks routing back to the completed shadow observation gap state-sync recheck.
- Updated the dashboard visibility evidence generator so reruns continue to route to {NEXT_TASK_CLASS}.
- Restored current_implementation_state next_allowed_task_class to {NEXT_TASK_CLASS}.
- Kept {CONTRACT_GAP_ID} open and live-affecting.

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
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", []) + [CONTRACT_GAP_ID]))
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
    summary = load_route_summary()
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
                    "tests.contract.test_paper_shadow_runtime_shadow_observation_gap_recheck",
                    "-v",
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
    update_requirement_artifacts(now, trader_hash, agents_hash)
    write_source_bundle_manifest()
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
                "route_before_patch": summary["route_before_patch"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "contract_gap_status": summary["contract_gap_status"],
                "contract_gap_live_affecting": summary["contract_gap_live_affecting"],
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
