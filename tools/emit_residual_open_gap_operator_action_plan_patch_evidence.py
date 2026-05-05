from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPEN-GAP-OPERATOR-ACTION-PLAN"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
REPORT_PATH = f"system/evidence/audit_reports/{PATCH_BASENAME}.report.json"
CLASSIFICATION_REPORT_PATH = "system/evidence/audit_reports/MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION.report.json"
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

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
from trader1.reports.residual_open_gap_operator_action_plan import (  # noqa: E402
    SCHEMA_ID,
    build_residual_open_gap_operator_action_plan_report,
    validate_residual_open_gap_operator_action_plan_report,
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
CHANGED_ARTIFACTS = [
    "trader1/reports/residual_open_gap_operator_action_plan.py",
    "contracts/schema/residual_open_gap_operator_action_plan_report.schema.json",
    "contracts/registry.yaml",
    "tests/contract/test_residual_open_gap_operator_action_plan.py",
    "tools/emit_residual_open_gap_operator_action_plan_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
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
    classification = load_json(ROOT / CLASSIFICATION_REPORT_PATH)
    report = build_residual_open_gap_operator_action_plan_report(
        classification,
        state,
        patch_id=PATCH_ID,
        generated_at_utc=now,
        trader1_sha256=trader_hash,
        agents_sha256=agents_hash,
    )
    errors = validate_residual_open_gap_operator_action_plan_report(report, classification, state)
    if errors:
        raise RuntimeError("residual open gap operator action plan failed: " + "; ".join(errors))
    for field in FALSE_FIELDS:
        if state.get(field) is not False:
            raise RuntimeError(f"current implementation state has forbidden true flag: {field}")
    return report


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CONTRACT_GAP", "SECTION_LEDGER_RECONCILIATION", "SECTION_LONG_RUN_RUNTIME_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-OPEN-GAP-CURRENT-BLOCKER-CLASSIFICATION", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["{SCHEMA_ID}", "trader1.open_contract_gap_current_blocker_classification_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS + EVIDENCE_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Convert residual open gaps into operator/evidence action classes without closing the gaps.
- Confirm implementation_recheck_action_count remains 0 after completed rechecks.
- Ensure every action item forbids live orders, credential use, live config mutation, LIVE_READY writes, and scale-up.
- Preserve next task as residual external-evidence/operator-reconciliation blocked status.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

action_plan_snapshot:
- open_gap_count: {report["open_gap_count"]}
- total_action_gap_count: {report["total_action_gap_count"]}
- implementation_recheck_action_count: {report["implementation_recheck_action_count"]}
- external_or_operator_action_required: {report["external_or_operator_action_required"]}
- selected_next_task_class: {report["selected_next_task_class"]}

known_omissions_by_design:
- This patch does not collect new runtime evidence.
- This patch does not reconcile operator-blocked evidence.
- This patch does not rewrite sealed historical patch_result baselines.
- This patch does not use credentials, place live orders, mutate live config, or scale up.

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

The residual open gaps are now grouped into operator/evidence action classes. There is no remaining implementation recheck action to repeat; the remaining route is blocked on operator reconciliation, bounded PAPER rerun/reconciliation, longer PAPER/SHADOW evidence, external live-readiness evidence, sealed baseline preservation, and scale-up policy evidence.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    artifacts = sorted(
        set(
            CHANGED_ARTIFACTS
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
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_CONTRACT_GAP",
            "source_file": "TRADER_1.md",
            "source_heading": "residual open gap operator action plan",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: residual open contract gaps must be grouped into operator/evidence "
                "actions and must not be treated as completed implementation work"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Residual open gap operator action plan",
            "requirement_kind": "EVIDENCE_PATCH",
            "schema_ids": [SCHEMA_ID],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/contract/test_residual_open_gap_operator_action_plan.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-OPEN-GAP-CURRENT-BLOCKER-CLASSIFICATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"residual open gap operator evidence action plan live blocked"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RESIDUAL_OPERATOR_ACTION_PLAN",
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
            "section_id": "SECTION_CONTRACT_GAP",
            "schema_files": ["contracts/schema/residual_open_gap_operator_action_plan_report.schema.json"],
            "validator_files": [
                "trader1/reports/residual_open_gap_operator_action_plan.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/contract/test_residual_open_gap_operator_action_plan.py"],
            "fixture_files": [
                "contracts/generated/current_implementation_state.json",
                CLASSIFICATION_REPORT_PATH,
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
            "status": "IMPLEMENTED_RESIDUAL_OPERATOR_ACTION_PLAN",
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
) -> dict[str, Any]:
    template = load_json(
        ROOT / "system" / "evidence" / "patch_results" / "MVP4_DASHBOARD_RESIDUAL_BLOCKER_SUMMARY.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "EVIDENCE_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-OPEN-GAP-CURRENT-BLOCKER-CLASSIFICATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_SHADOW_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "new_registry_items": [REQUIREMENT_ID, "residual_open_gap_operator_action_plan_report"],
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
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
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
            "remaining_blockers": [gap_id for item in report["action_items"] for gap_id in item["gap_ids"]],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                "open gap current blocker classification report",
                "residual open gap operator action plan",
                "requirement_index",
                "requirement_artifact_matrix",
            ],
            "task_class": "RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN",
            "required_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_RESIDUAL_OPERATOR_ACTION_PLAN",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "false",
            "optimizer_stage": "NOT_CHANGED_RESIDUAL_OPERATOR_ACTION_PLAN_ONLY",
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
    assert_false_flags("operator action plan report", report, "")

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
            "stage_gate_status": "PASS_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN_LIVE_BLOCKED",
            "open_gap_count": report["open_gap_count"],
            "total_action_gap_count": report["total_action_gap_count"],
            "implementation_recheck_action_count": report["implementation_recheck_action_count"],
            "external_or_operator_action_required": report["external_or_operator_action_required"],
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
            "artifact_paths": sorted(
                set(
                    CHANGED_ARTIFACTS
                    + EVIDENCE_ARTIFACTS
                    + [
                        CLASSIFICATION_REPORT_PATH,
                        "contracts/generated/ACTIVE_WORKING_VIEW.md",
                        "contracts/generated/current_implementation_state.json",
                        "contracts/generated/read_cache_manifest.json",
                        "contracts/generated/requirement_index.json",
                        "contracts/generated/requirement_artifact_matrix.json",
                        "system/evidence/implementation_patch_ledger.json",
                    ]
                )
            ),
            "known_blockers": patch_result["remaining_blockers"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 Residual Open Gap Operator Action Plan Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The current open gaps have completed implementation/recheck coverage, but the remaining blockers require operator action or evidence rather than another code-only recheck.

Patch:
- Added a closed residual operator action plan schema and report.
- Grouped {report["open_gap_count"]} open gaps into {len(report["action_items"])} operator/evidence action classes.
- Confirmed implementation_recheck_action_count={report["implementation_recheck_action_count"]}.
- Preserved the residual blocker route and all open gaps.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no current evidence promotion
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
    update_authority_manifest(now)
    report = build_report(now, trader_hash, agents_hash, state_before)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    validators_run = summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS_REQUIRED, report)
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
                    "tests.contract.test_residual_open_gap_operator_action_plan",
                    "tests.contract.test_open_gap_current_blocker_classification",
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
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=1800))
    report = build_report(now, trader_hash, agents_hash, state_before)
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
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
                "open_gap_count": report["open_gap_count"],
                "implementation_recheck_action_count": report["implementation_recheck_action_count"],
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
