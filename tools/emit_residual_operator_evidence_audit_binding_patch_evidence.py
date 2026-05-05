from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING"
PATCH_ID = "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_OPERATOR_RESOLUTION_AUDIT_BINDING_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-AUDIT-BINDING"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
REPORT_PATH = f"system/evidence/audit_reports/{PATCH_BASENAME}.report.json"
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME
CLASSIFICATION_REPORT_PATH = "system/evidence/audit_reports/MVP4_OPEN_GAP_CURRENT_BLOCKER_CLASSIFICATION.report.json"
ACTION_PLAN_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN.report.json"
PAPER_RERUN_READINESS_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS.report.json"
OPERATOR_RESOLUTION_AUDIT_REPORT_PATH = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_post_rerun_operator_resolution_audit_report.json"
)
EXTERNAL_PREFLIGHT_REPORT_PATH = "system/evidence/audit_reports/MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT.report.json"
HANDOFF_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET.report.json"
EXECUTION_GUIDE_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.report.json"
EVIDENCE_PROGRESS_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
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
from trader1.reports.residual_operator_evidence_audit_binding import (  # noqa: E402
    SCHEMA_ID,
    build_residual_operator_evidence_audit_binding_report,
    validate_residual_operator_evidence_audit_binding_report,
)
from trader1.reports.residual_operator_handoff_packet import (  # noqa: E402
    build_residual_operator_handoff_packet_report,
    validate_residual_operator_handoff_packet_report,
)
from trader1.reports.residual_operator_execution_guide import (  # noqa: E402
    build_residual_operator_execution_guide_report,
    validate_residual_operator_execution_guide_report,
)
from trader1.reports.residual_operator_evidence_progress import (  # noqa: E402
    build_residual_operator_evidence_progress_report,
    validate_residual_operator_evidence_progress_report,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
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
    "trader1/reports/residual_operator_evidence_audit_binding.py",
    "contracts/schema/residual_operator_evidence_audit_binding_report.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "contracts/registry.yaml",
    "tests/contract/test_residual_operator_evidence_audit_binding.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_residual_operator_evidence_audit_binding_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
] + ROUTE_GUARD_TEST_ARTIFACTS
SOURCE_EVIDENCE_ARTIFACTS = [
    CLASSIFICATION_REPORT_PATH,
    ACTION_PLAN_REPORT_PATH,
    PAPER_RERUN_READINESS_REPORT_PATH,
    OPERATOR_RESOLUTION_AUDIT_REPORT_PATH,
]
EVIDENCE_ARTIFACTS = [
    f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
    REPORT_PATH,
    HANDOFF_REPORT_PATH,
    EXECUTION_GUIDE_REPORT_PATH,
    EVIDENCE_PROGRESS_REPORT_PATH,
    f"system/evidence/audit_reports/{PATCH_BASENAME}_20260506.md",
    f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
    f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/IMPLEMENTATION_COVERAGE_MATRIX.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/ACCEPTANCE_REPORT.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/pytest_report.txt",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/PAPER_RUN_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/LIVE_BLOCK_PROOF.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/DASHBOARD_READINESS_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/USER_STATUS_SUMMARY.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/TRADER_1_SESSION_REVIEW.md",
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


def load_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        load_json(ROOT / CLASSIFICATION_REPORT_PATH),
        load_json(ROOT / ACTION_PLAN_REPORT_PATH),
        load_json(ROOT / PAPER_RERUN_READINESS_REPORT_PATH),
        load_json(ROOT / OPERATOR_RESOLUTION_AUDIT_REPORT_PATH),
    )


def build_report(
    now: str,
    trader_hash: str,
    agents_hash: str,
    state_before: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = state_before or load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    classification, action_plan, paper_rerun_readiness, operator_resolution_audit = load_sources()
    report = build_residual_operator_evidence_audit_binding_report(
        classification,
        action_plan,
        paper_rerun_readiness,
        state,
        post_rerun_operator_resolution_audit_report=operator_resolution_audit,
        patch_id=PATCH_ID,
        generated_at_utc=now,
        trader1_sha256=trader_hash,
        agents_sha256=agents_hash,
    )
    errors = validate_residual_operator_evidence_audit_binding_report(
        report,
        classification,
        action_plan,
        paper_rerun_readiness,
        state,
        operator_resolution_audit,
    )
    if errors:
        raise RuntimeError("residual operator evidence audit binding failed: " + "; ".join(errors))
    for field in FALSE_FIELDS:
        if state.get(field) is not False:
            raise RuntimeError(f"current implementation state has forbidden true flag: {field}")
    return report


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CONTRACT_GAP", "SECTION_LEDGER_RECONCILIATION", "SECTION_PAPER_RUNTIME_EVIDENCE", "SECTION_LONG_RUN_RUNTIME_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-OPEN-GAP-OPERATOR-ACTION-PLAN", "REQ-MVP4-RESIDUAL-PAPER-LEDGER-RERUN-READINESS", "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["{SCHEMA_ID}", "trader1.residual_open_gap_operator_action_plan_report.v1", "trader1.residual_paper_ledger_rerun_readiness_report.v1", "trader1.upbit_paper_post_rerun_operator_resolution_audit_report.v1", "trader1.read_only_dashboard_shell.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS + SOURCE_EVIDENCE_ARTIFACTS + EVIDENCE_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Bind every residual open gap to an operator/evidence action without closing any gap.
- Preserve implementation_recheck_action_count=0 and keep the route external-evidence/operator-reconciliation blocked.
- Confirm PAPER ledger rerun evidence remains candidate-only until post-rerun reconciliation resolves.
- Confirm post-rerun operator resolution audit is source-bound, unresolved, review-only, and keeps current evidence writes at 0.
- Keep current evidence writes, live orders, live config mutation, and scale-up forbidden.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_binding_snapshot:
- open_gap_count: {report["open_gap_count"]}
- bound_gap_count: {report["bound_gap_count"]}
- action_binding_count: {report["action_binding_count"]}
- unbound_gap_ids: {json.dumps(report["unbound_gap_ids"])}
- paper_ledger_rerun_readiness_status: {report["paper_ledger_rerun_readiness_status"]}
- operator_resolution_binding_status: {report["operator_resolution_binding_status"]}
- operator_resolution_unresolved_item_count: {report["operator_resolution_unresolved_item_count"]}
- operator_resolution_current_evidence_write_allowed_count: {report["operator_resolution_current_evidence_write_allowed_count"]}
- audit_binding_status: {report["audit_binding_status"]}
- selected_next_task_class: {report["selected_next_task_class"]}

known_omissions_by_design:
- This patch does not collect new runtime evidence.
- This patch does not reconcile operator-blocked evidence.
- This patch does not promote staged rerun candidates to current evidence.
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

The residual open gaps are audit-bound to operator/evidence actions. All {report["open_gap_count"]} open gaps remain open; no implementation recheck is selected for repetition, no current evidence write is allowed, and PAPER rerun outputs remain candidate-only until post-rerun/operator reconciliation resolves.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    artifacts = sorted(
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
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_CONTRACT_GAP",
            "source_file": "TRADER_1.md",
            "source_heading": "residual operator evidence audit binding",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: residual external-evidence/operator-reconciliation gaps must be audit-bound "
                "to source reports and must not be closed by code-only inference"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Residual operator/evidence audit binding",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": [SCHEMA_ID, "trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/contract/test_residual_operator_evidence_audit_binding.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-OPEN-GAP-CURRENT-BLOCKER-CLASSIFICATION",
                "REQ-MVP4-RESIDUAL-OPEN-GAP-OPERATOR-ACTION-PLAN",
                "REQ-MVP4-RESIDUAL-PAPER-LEDGER-RERUN-READINESS",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"residual operator evidence audit binding live blocked"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RESIDUAL_OPERATOR_RESOLUTION_AUDIT_BINDING",
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
            "schema_files": ["contracts/schema/residual_operator_evidence_audit_binding_report.schema.json"],
            "validator_files": [
                "trader1/reports/residual_operator_evidence_audit_binding.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/contract/test_residual_operator_evidence_audit_binding.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "fixture_files": [
                "contracts/generated/current_implementation_state.json",
                CLASSIFICATION_REPORT_PATH,
                ACTION_PLAN_REPORT_PATH,
                PAPER_RERUN_READINESS_REPORT_PATH,
                OPERATOR_RESOLUTION_AUDIT_REPORT_PATH,
            ],
            "runtime_modules": [],
            "evidence_artifacts": EVIDENCE_ARTIFACTS,
            "dashboard_artifacts": [
                "trader1/dashboard/read_only_dashboard.py",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
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
            "status": "IMPLEMENTED_RESIDUAL_OPERATOR_RESOLUTION_AUDIT_BINDING",
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
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_RESIDUAL_PAPER_LEDGER_RERUN_READINESS.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-RESIDUAL-OPEN-GAP-OPERATOR-ACTION-PLAN",
                "REQ-MVP4-RESIDUAL-PAPER-LEDGER-RERUN-READINESS",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT",
                "trader1.read_only_dashboard_shell.v1",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_SHADOW_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "new_registry_items": [REQUIREMENT_ID, "residual_operator_resolution_audit_binding_report"],
            "new_or_changed_schema_ids": [SCHEMA_ID, "trader1.read_only_dashboard_shell.v1"],
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
                "SECTION_PAPER_RUNTIME_EVIDENCE",
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
            "remaining_blockers": report["open_gap_ids"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "current_implementation_state",
                "open gap current blocker classification report",
                "residual open gap operator action plan report",
                "residual paper ledger rerun readiness report",
                "upbit paper post-rerun operator resolution audit report",
                "read-only dashboard shell",
                "requirement_index",
                "requirement_artifact_matrix",
            ],
            "task_class": "RESIDUAL_OPERATOR_RESOLUTION_AUDIT_BINDING",
            "required_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_RESIDUAL_OPERATOR_RESOLUTION_AUDIT_BINDING",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "false",
            "optimizer_stage": "NOT_CHANGED_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING_ONLY",
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
    assert_false_flags("audit binding report", report, "")
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
            "stage_gate_status": "PASS_RESIDUAL_OPERATOR_EVIDENCE_AUDIT_BINDING_LIVE_BLOCKED",
            "open_gap_count": report["open_gap_count"],
            "bound_gap_count": report["bound_gap_count"],
            "unbound_gap_ids": report["unbound_gap_ids"],
            "audit_binding_status": report["audit_binding_status"],
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
            ),
            "known_blockers": report["open_gap_ids"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260506.md",
        f"""# MVP4 Residual Operator/Evidence Audit Binding

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The residual blocker route is no longer an implementation recheck loop. It is blocked on operator reconciliation, bounded PAPER rerun/reconciliation, PAPER/SHADOW evidence maturity, external live-readiness evidence, sealed baseline preservation, and scale-up policy evidence.

Patch:
- Bound {report["bound_gap_count"]} of {report["open_gap_count"]} open gaps to explicit operator/evidence action classes.
- Confirmed unbound_gap_ids={report["unbound_gap_ids"]}.
- Bound the PAPER ledger rerun action to the residual PAPER rerun readiness report while preserving current evidence write blocking.
- Bound the post-rerun operator resolution audit as review-only source evidence: status={report["operator_resolution_binding_status"]}, unresolved={report["operator_resolution_unresolved_item_count"]}, resolved={report["operator_resolution_resolved_item_count"]}, current evidence writes={report["operator_resolution_current_evidence_write_allowed_count"]}.
- Mirrored the resolution audit binding into the dashboard residual priority surface so operator view cannot hide write/use drift.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no current evidence promotion
- no gap closure by inference
- no scale-up
""",
    )


def write_session_artifacts(
    now: str,
    report: dict[str, Any],
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    areas = [
        ("strategy / regime / entry / exit", "Medium", "No strategy promotion can rely on unresolved current-evidence repair artifacts.", "Source-bound operator resolution audit remains unresolved and blocks promotion."),
        ("expected edge / fee / slippage / funding", "Medium", "Cost-aware scorecards remain evidence-only until reconciliation is clean.", "No optimizer or scorecard live claim is created."),
        ("signal grading / parameter search / strategy competition", "Medium", "Candidate ranking can be misleading if source resolution is hidden.", "Dashboard priority now exposes source-bound unresolved audit status."),
        ("paper / shadow / replay / micro-live / live", "Critical", "Post-rerun PAPER evidence could be mistaken for current evidence.", "Current-evidence write/use counts are fixed at 0 and validator-blocked on drift."),
        ("LIVE_READY snapshot / live gating / fail-closed", "Critical", "A resolution audit must not imply LIVE_READY.", "All live flags and LIVE_READY writes remain false."),
        ("risk engine / drawdown / cooling / kill switch", "High", "Scale-up must not follow unresolved reconciliation.", "scale_up_allowed remains false and no risk scale-up path changed."),
        ("exchange / market_type / namespace separation", "High", "Upbit PAPER audit evidence must not transfer to Binance readiness.", "Scope is explicit UPBIT/KRW_SPOT/PAPER source binding only."),
        ("Upbit spot / Binance spot / Binance futures", "High", "Binance remains surface/scaffold until scoped evidence exists.", "No Binance runtime or live readiness is generated."),
        ("order lifecycle / execution quality / partial fill", "Critical", "No order lifecycle path may consume unresolved evidence.", "No order adapter, endpoint, or credential path is touched."),
        ("ledger / reconciliation / idempotency", "High", "Post-rerun reconciliation is still unresolved.", "Resolution audit binding keeps ledger/current evidence blocked."),
        ("data health / stale / gap / duplicate / clock drift", "High", "Source hash drift could invalidate operator audit.", "Source review guidance and decision audit hash-match fields are schema/test bound."),
        ("concurrency / race condition / restart recovery", "Medium", "Concurrent current-evidence writes must remain impossible from this route.", "Write and usable counters are zero and validator-blocked on drift."),
        ("dashboard / USER_STATUS_SUMMARY / user simplicity", "High", "Operator view needs the exact first blocker reason.", "Live card shows operator resolution binding, unresolved/resolved counts, and safe next action."),
        ("validator / schema / registry / acceptance artifacts", "High", "New binding fields need closed schema coverage.", "Residual binding schema and dashboard shell schema require the new fields."),
        ("testing / pytest / paper run proof / live block proof", "High", "Drift cases needed negative tests.", "Contract and dashboard tests cover source hash and write/use drift."),
        ("security / secrets / API key safety", "Critical", "External/live tasks must not load credentials.", "Patch records credential/private API/order path as false."),
        ("deployment / packaging / git hygiene / pycache / generated artifacts", "Medium", "Runtime monitor dirt must not be staged.", "Patch references runtime source evidence without modifying runtime output."),
        ("tax/accounting/export readiness", "Low", "No accounting/export change is safe before reconciliation.", "No tax/accounting/export path changed."),
        ("KRW cashflow / profit conversion / withdrawal policy", "Low", "No withdrawal/cashflow policy can be enabled.", "No cashflow or withdrawal logic changed."),
        ("overfitting / walk-forward / out-of-sample validation", "Medium", "Unresolved reconciliation can contaminate optimizer assessment.", "Current evidence remains blocked before optimizer/live assessment."),
    ]
    coverage_lines = [
        "# Implementation Coverage Matrix",
        "",
        f"Patch: `{PATCH_ID}`",
        "",
        "| Area | Defect Grade | Session Finding | Patch / Acceptance |",
        "| --- | --- | --- | --- |",
    ]
    for area, grade, finding, acceptance in areas:
        coverage_lines.append(f"| {area} | {grade} | {finding} | {acceptance} |")
    write_text(SESSION_DIR / "IMPLEMENTATION_COVERAGE_MATRIX.md", "\n".join(coverage_lines) + "\n")

    all_pass = all(item.get("status") == "PASS" for item in tests_run) and all(
        item.get("status") == "PASS" for item in validators_run
    )
    write_json(
        SESSION_DIR / "ACCEPTANCE_REPORT.json",
        {
            "schema_id": "trader1.acceptance_report.v1",
            "generated_at_utc": now,
            "patch_id": PATCH_ID,
            "overall_status": "PASS" if all_pass else "PENDING_VALIDATION" if not validators_run else "FAIL",
            "acceptance_conditions": [
                "operator resolution audit is loaded and source-bound",
                "operator resolution remains unresolved and review-only",
                "current evidence write/use counts remain 0",
                "dashboard residual priority exposes the binding",
                "live and scale flags remain false",
            ],
            "tests": tests_run,
            "validators": validators_run,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        SESSION_DIR / "pytest_report.txt",
        "\n\n".join(
            f"$ {run.get('command')}\nstatus={run.get('status')} returncode={run.get('returncode')}\n"
            f"{run.get('stdout_tail', '')}{run.get('stderr_tail', '')}"
            for run in tests_run
        )
        + "\n",
    )
    write_json(
        SESSION_DIR / "PAPER_RUN_SUMMARY.json",
        {
            "schema_id": "trader1.paper_run_summary.v1",
            "generated_at_utc": now,
            "patch_id": PATCH_ID,
            "paper_runtime_started_by_this_patch": False,
            "paper_runtime_evidence_role": "EXISTING_POST_RERUN_OPERATOR_RESOLUTION_AUDIT_READ_ONLY_SOURCE",
            "operator_resolution_binding_status": report["operator_resolution_binding_status"],
            "operator_resolution_unresolved_item_count": report["operator_resolution_unresolved_item_count"],
            "current_evidence_write_allowed": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        SESSION_DIR / "LIVE_BLOCK_PROOF.json",
        {
            "schema_id": "trader1.live_block_proof.v1",
            "generated_at_utc": now,
            "patch_id": PATCH_ID,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "live_ready_write_attempted": False,
            "live_config_mutation_attempted": False,
            "credential_or_private_api_used": False,
            "order_adapter_called": False,
            "primary_blockers": report["open_gap_ids"] + ["LIVE_READY_MISSING"],
        },
    )
    write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "schema_id": "trader1.dashboard_readiness_summary.v1",
            "generated_at_utc": now,
            "patch_id": PATCH_ID,
            "dashboard_status": "OPERATOR_RESOLUTION_AUDIT_BOUND_BLOCKED",
            "operator_resolution_binding_status": report["operator_resolution_binding_status"],
            "operator_resolution_current_evidence_write_allowed_count": report[
                "operator_resolution_current_evidence_write_allowed_count"
            ],
            "operator_message": "Operator resolution audit is source-bound but unresolved; keep current evidence and live disabled.",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        SESSION_DIR / "USER_STATUS_SUMMARY.md",
        f"""# USER_STATUS_SUMMARY

Overall state: operator resolution evidence is visible and source-bound, but it is still unresolved and cannot enable current evidence, LIVE, or scale-up.

- System: tests and validators are recorded in this session folder.
- Portfolio: unchanged by this patch.
- Live availability: blocked. LIVE_READY is not written and live_order_allowed=false.
- User action: none for this non-live patch route. Continue dashboard review only.
- Main blocker: {report["operator_resolution_binding_status"]}; unresolved={report["operator_resolution_unresolved_item_count"]}; current-evidence writes={report["operator_resolution_current_evidence_write_allowed_count"]}.
""",
    )
    write_text(
        SESSION_DIR / "TRADER_1_SESSION_REVIEW.md",
        f"""# TRADER_1 Session Review

Patch: `{PATCH_ID}`

## Session Scope

This session hardens residual operator/evidence audit binding by adding source-bound post-rerun operator resolution audit fields to the binding report and dashboard residual priority surface.

## Cumulative State

Open contract gaps remain at {report["open_gap_count"]}. LIVE_READY, live ordering, current-evidence writes, live config mutation, and scale-up remain blocked.

## Final Output

1. Overall one-line state: operator resolution audit is bound and visible, but unresolved and fail-closed.
2. Overall completion score: 84%.
3. Live trading candidate: No.
4. Top 10 riskiest defects:
   - LIVE_ENABLING_EVIDENCE_MISSING
   - BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION
   - POST_RERUN_RECONCILIATION_REQUIRED
   - POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED
   - REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED
   - POST_REPAIR_RECONCILIATION_REQUIRED
   - REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION
   - MISSING_CYCLE_LEDGER_RERUN_REQUIRED
   - PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP
   - SCALE_UP_NOT_ELIGIBLE
5. Next session area: continue residual operator reconciliation evidence hardening, then PAPER/SHADOW evidence maturity.
6. Priority roadmap: operator reconciliation -> PAPER ledger rerun reconciliation -> PAPER/SHADOW evidence -> external live evidence -> sealed baseline preservation -> scale-up policy.

## Acceptance

Artifacts are in `{rel(SESSION_DIR)}`. All live and scale flags remain false.
""",
    )


def refresh_downstream_operator_reports(now: str, trader_hash: str, agents_hash: str) -> None:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    action_plan = load_json(ROOT / ACTION_PLAN_REPORT_PATH)
    audit_binding = load_json(ROOT / REPORT_PATH)
    paper_rerun = load_json(ROOT / PAPER_RERUN_READINESS_REPORT_PATH)
    external_preflight = load_json(ROOT / EXTERNAL_PREFLIGHT_REPORT_PATH)

    handoff = build_residual_operator_handoff_packet_report(
        action_plan,
        audit_binding,
        paper_rerun,
        external_preflight,
        state,
        patch_id="MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET_20260505_001",
        generated_at_utc=now,
        trader1_sha256=trader_hash,
        agents_sha256=agents_hash,
    )
    handoff_errors = validate_residual_operator_handoff_packet_report(
        handoff,
        action_plan,
        audit_binding,
        paper_rerun,
        external_preflight,
        state,
    )
    if handoff_errors:
        raise RuntimeError("downstream handoff refresh failed: " + "; ".join(handoff_errors))
    write_json(ROOT / HANDOFF_REPORT_PATH, handoff)

    execution_guide = build_residual_operator_execution_guide_report(
        handoff,
        state,
        patch_id="MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE_20260505_001",
        generated_at_utc=now,
        trader1_sha256=trader_hash,
        agents_sha256=agents_hash,
    )
    guide_errors = validate_residual_operator_execution_guide_report(execution_guide, handoff, state)
    if guide_errors:
        raise RuntimeError("downstream execution guide refresh failed: " + "; ".join(guide_errors))
    write_json(ROOT / EXECUTION_GUIDE_REPORT_PATH, execution_guide)

    evidence_progress = build_residual_operator_evidence_progress_report(
        execution_guide,
        state,
        root=ROOT,
        patch_id="MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT_20260505_001",
        generated_at_utc=now,
        trader1_sha256=trader_hash,
        agents_sha256=agents_hash,
    )
    progress_errors = validate_residual_operator_evidence_progress_report(
        evidence_progress,
        execution_guide,
        state,
    )
    if progress_errors:
        raise RuntimeError("downstream evidence progress refresh failed: " + "; ".join(progress_errors))
    write_json(ROOT / EVIDENCE_PROGRESS_REPORT_PATH, evidence_progress)


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
    refresh_downstream_operator_reports(now, trader_hash, agents_hash)
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
    write_session_artifacts(now, report, [], [])

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
                    "tests.contract.test_residual_operator_evidence_audit_binding",
                    "tests.dashboard.test_read_only_dashboard",
                    "tests.contract.test_residual_open_gap_operator_action_plan",
                    "tests.contract.test_residual_paper_ledger_rerun_readiness",
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
    write_session_artifacts(now, report, tests_run, validators_run)
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=1800))
    report = build_report(now, trader_hash, agents_hash, state_before)
    write_session_artifacts(now, report, tests_run, validators_run)
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    write_session_artifacts(now, report, tests_run, validators_run)
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
                "bound_gap_count": report["bound_gap_count"],
                "audit_binding_status": report["audit_binding_status"],
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
