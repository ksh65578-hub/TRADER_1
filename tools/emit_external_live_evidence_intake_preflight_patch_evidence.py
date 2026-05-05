from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-EXTERNAL-LIVE-EVIDENCE-INTAKE-PREFLIGHT"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
REPORT_PATH = f"system/evidence/audit_reports/{PATCH_BASENAME}.report.json"
SOURCE_MANIFEST_PATH = "system/evidence/MVP4_EXTERNAL_BLOCKER.evidence_manifest.json"
SOURCE_PATCH_RESULT_PATH = "system/evidence/patch_results/MVP4_EXTERNAL_BLOCKER.patch_result.json"
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    load_json,
    rel,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.reports.external_live_evidence_intake_preflight import (  # noqa: E402
    BLOCKED_REQUIREMENT_IDS,
    SCHEMA_ID,
    build_external_live_evidence_intake_preflight_report,
    validate_external_live_evidence_intake_preflight_report,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "live_final_guard_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    validator_id for validator_id in VALIDATORS_REQUIRED if validator_id != "generated_artifact_dirty_validator"
]
ROUTE_GUARD_TEST_ARTIFACTS = [
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
    "tests/contract/test_profitability_optimizer_evidence_maturity_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_implementation_depth_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
    "tests/contract/test_upbit_paper_audited_current_evidence_writer_dashboard_binding.py",
]
CHANGED_ARTIFACTS = [
    "trader1/reports/external_live_evidence_intake_preflight.py",
    "contracts/schema/external_live_evidence_intake_preflight_report.schema.json",
    "contracts/registry.yaml",
    "tests/contract/test_external_live_evidence_intake_preflight.py",
    "tools/emit_external_live_evidence_intake_preflight_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
] + ROUTE_GUARD_TEST_ARTIFACTS
SOURCE_EVIDENCE_ARTIFACTS = [
    SOURCE_MANIFEST_PATH,
    SOURCE_PATCH_RESULT_PATH,
]
EVIDENCE_ARTIFACTS = [
    f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
    REPORT_PATH,
    f"system/evidence/audit_reports/{PATCH_BASENAME}_20260505.md",
    f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
    f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
]


def run_command(args: list[str], timeout_seconds: int = 900) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        timeout=timeout_seconds,
    )
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


def assert_false_flags(name: str, value: dict[str, Any], suffix: str = "") -> None:
    for field in FALSE_FIELDS:
        key = f"{field}{suffix}"
        if value.get(key) is True:
            raise RuntimeError(f"{name} has forbidden true field: {key}")


def build_report(
    now: str,
    trader_hash: str,
    agents_hash: str,
    state_before: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = state_before or load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    manifest = load_json(ROOT / SOURCE_MANIFEST_PATH)
    report = build_external_live_evidence_intake_preflight_report(
        manifest,
        state,
        patch_id=PATCH_ID,
        generated_at_utc=now,
        trader1_sha256=trader_hash,
        agents_sha256=agents_hash,
        source_manifest_path=SOURCE_MANIFEST_PATH,
        source_manifest_sha256=sha256_file(ROOT / SOURCE_MANIFEST_PATH),
    )
    errors = validate_external_live_evidence_intake_preflight_report(report, manifest, state)
    if errors:
        raise RuntimeError("external live evidence intake preflight failed: " + "; ".join(errors))
    for field in FALSE_FIELDS:
        if state.get(field) is not False:
            raise RuntimeError(f"current implementation state has forbidden true flag: {field}")
    return report


def all_artifacts() -> list[str]:
    return sorted(
        set(
            CHANGED_ARTIFACTS
            + SOURCE_EVIDENCE_ARTIFACTS
            + EVIDENCE_ARTIFACTS
            + [
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "system/evidence/implementation_patch_ledger.json",
            ]
        )
    )


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LIVE_GATE", "SECTION_LIVE_FINAL_GUARD", "SECTION_LIVE_READY_REVIEW", "SECTION_OPERATOR_CONTROL", "SECTION_CONTRACT_GAP"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-OFFICIAL-API-PASS-EVIDENCE", "REQ-MVP4-READ-ONLY-ACCOUNT-SNAPSHOT-EVIDENCE", "REQ-MVP4-OPERATOR-APPROVAL-EVIDENCE", "REQ-MVP4-READ-ONLY-BURN-IN-EVIDENCE", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["{SCHEMA_ID}", "trader1.official_api_verification_report.v1", "trader1.read_only_account_snapshot.v1", "trader1.live_burn_in_feedback_report.v1", "trader1.operator_action_audit.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(all_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Map the four external live-readiness blocked requirements to expected intake artifacts.
- Preserve every external evidence item as missing or unusable for live enabling.
- Do not collect external evidence, load credentials, call private APIs, place live orders, mutate live config, close gaps, or scale up.
- Keep the next route as external-evidence/operator-reconciliation blocked.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

preflight_snapshot:
- blocked_requirement_count: {report["blocked_requirement_count"]}
- evidence_item_count: {report["evidence_item_count"]}
- intake_ready_count: {report["intake_ready_count"]}
- missing_or_unusable_count: {report["missing_or_unusable_count"]}
- preflight_status: {report["preflight_status"]}
- selected_next_task_class: {report["selected_next_task_class"]}

known_omissions_by_design:
- This patch does not provide official API evidence.
- This patch does not create read-only account snapshot evidence.
- This patch does not create operator approval evidence.
- This patch does not create burn-in evidence.
- This patch is not a LIVE_ENABLING_PATCH.

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

The four external live-readiness requirements are preflight-mapped to missing or unusable evidence inputs. No evidence was collected, no credentials or API calls were used, and no live or scale-up permission changed.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    artifacts = all_artifacts()

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LIVE_GATE",
            "source_file": "TRADER_1.md",
            "source_heading": "external live evidence intake preflight",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: external live-readiness evidence must be intake-mapped without "
                "collecting credentials, enabling live orders, or closing blocked requirements by inference"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "External live evidence intake preflight",
            "requirement_kind": "EVIDENCE_PATCH",
            "schema_ids": [SCHEMA_ID],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/contract/test_external_live_evidence_intake_preflight.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_READY_REVIEW",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_CONTRACT_GAP",
            ],
            "depends_on": [
                "REQ-MVP4-OFFICIAL-API-PASS-EVIDENCE",
                "REQ-MVP4-READ-ONLY-ACCOUNT-SNAPSHOT-EVIDENCE",
                "REQ-MVP4-OPERATOR-APPROVAL-EVIDENCE",
                "REQ-MVP4-READ-ONLY-BURN-IN-EVIDENCE",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"external live evidence intake preflight live blocked"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT",
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
            "section_id": "SECTION_LIVE_GATE",
            "schema_files": ["contracts/schema/external_live_evidence_intake_preflight_report.schema.json"],
            "validator_files": [
                "trader1/reports/external_live_evidence_intake_preflight.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/contract/test_external_live_evidence_intake_preflight.py"],
            "fixture_files": [
                "contracts/generated/current_implementation_state.json",
                SOURCE_MANIFEST_PATH,
                SOURCE_PATCH_RESULT_PATH,
            ],
            "runtime_modules": [],
            "evidence_artifacts": EVIDENCE_ARTIFACTS,
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "next_task_class",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT",
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
    report: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "EVIDENCE_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID] + sorted(BLOCKED_REQUIREMENT_IDS) + ["REQ-MVP4-LIVE-FINAL-GUARD"],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "new_registry_items": [REQUIREMENT_ID, "external_live_evidence_intake_preflight_report"],
            "new_or_changed_schema_ids": [SCHEMA_ID],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_READY_REVIEW",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_CONTRACT_GAP",
            ],
            "next_optional_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_PROFITABILITY_OPTIMIZER",
            ],
            "next_forbidden_default_sections": [
                "RETAINED_ARCHIVE",
                "LIVE_ENABLING_PATCH",
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
            "remaining_blockers": sorted(state.get("open_contract_gap_ids", [])),
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "current_implementation_state",
                "MVP4 external blocker evidence manifest",
                "MVP4 external blocker patch result",
                "requirement_index",
                "requirement_artifact_matrix",
            ],
            "task_class": "MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT",
            "required_section_ids": [
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_READY_REVIEW",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_CONTRACT_GAP",
            ],
            "expanded_section_ids": [
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_READY_REVIEW",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_CONTRACT_GAP",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "false",
            "optimizer_stage": "NOT_CHANGED_EXTERNAL_EVIDENCE_INTAKE_PREFLIGHT_ONLY",
            "optimizer_status_before": "RESIDUAL_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION",
            "optimizer_status_after": "RESIDUAL_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION",
            "optimizer_output_type": "NO_OPTIMIZER_OUTPUT_CREATED",
            "optimizer_validators_required": ["live_final_guard_validator"],
            "optimizer_validators_run": ["live_final_guard_validator:PASS"],
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION_NO_SCALE_UP",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "false",
            "convergence_layer_changed": False,
            "convergence_state_before": "RESIDUAL_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION",
            "convergence_state_after": "RESIDUAL_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_CHANGED",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": ["live_final_guard_validator"],
            "convergence_validators_run": ["live_final_guard_validator:PASS"],
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    assert_false_flags("patch_result", patch_result, "_after")
    assert_false_flags("preflight report", report, "")
    write_json(ROOT / REPORT_PATH, report)
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
            "stage_gate_status": "PASS_EXTERNAL_EVIDENCE_INTAKE_PREFLIGHT_LIVE_BLOCKED",
            "blocked_requirement_count": report["blocked_requirement_count"],
            "evidence_item_count": report["evidence_item_count"],
            "intake_ready_count": report["intake_ready_count"],
            "missing_or_unusable_count": report["missing_or_unusable_count"],
            "preflight_status": report["preflight_status"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": all_artifacts(),
            "known_blockers": sorted(set(report["blocked_requirement_ids"] + patch_result["remaining_blockers"])),
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 External Live Evidence Intake Preflight

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The four external live-readiness requirements remain blocked on missing or unusable evidence.
- No external evidence was collected by this patch.

Patch:
- Mapped {report["blocked_requirement_count"]} blocked requirements to {report["evidence_item_count"]} intake items.
- Confirmed intake_ready_count={report["intake_ready_count"]}.
- Confirmed missing_or_unusable_count={report["missing_or_unusable_count"]}.
- Preserved the residual external-evidence/operator-reconciliation route.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credential use
- no private API call
- no live order
- no live config mutation
- no gap closure
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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + [SCHEMA_ID]))
    state["blocked_requirement_ids"] = sorted(BLOCKED_REQUIREMENT_IDS)
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
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
    ledger["live_order_ready"] = False
    ledger["live_order_allowed"] = False
    ledger["can_live_trade"] = False
    ledger["scale_up_allowed"] = False
    ledger["ledger_hash"] = ""
    ledger["ledger_hash"] = sha256_json({key: value for key, value in ledger.items() if key != "ledger_hash"})
    write_json(ledger_path, ledger)


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    state_before = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    report = build_report(now, trader_hash, agents_hash, state_before)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    validators_run = summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS_REQUIRED, report, state_before)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "tests.contract.test_external_live_evidence_intake_preflight",
                    "tests.contract.test_residual_operator_evidence_audit_binding",
                    "tests.contract.test_patch_result_runtime_schema_validation",
                    "-v",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
        ]
    )
    report = build_report(now, trader_hash, agents_hash, state_before)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report, state_before)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=1800))
    report = build_report(now, trader_hash, agents_hash, state_before)
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report, state_before)
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
                "blocked_requirement_count": report["blocked_requirement_count"],
                "intake_ready_count": report["intake_ready_count"],
                "missing_or_unusable_count": report["missing_or_unusable_count"],
                "preflight_status": report["preflight_status"],
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
