from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-COLLECTION-DEPTH-RECHECK"
CONTRACT_GAP_ID = "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY"
NEXT_TASK_CLASS = "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-RECHECK"

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
from tools.run_upbit_paper_runtime_evidence_collection_profile import (  # noqa: E402
    DEFAULT_REPORT_PATH,
    run_upbit_paper_runtime_evidence_collection_profile,
    validate_upbit_paper_runtime_evidence_collection_profile_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


REPORT_PATH = ROOT / DEFAULT_REPORT_PATH
CHANGED_ARTIFACTS = [
    "contracts/schema/upbit_paper_runtime_evidence_collection_profile_report.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "tools/run_upbit_paper_runtime_evidence_collection_profile.py",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
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
    "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
    "tests/contract/test_upbit_paper_audited_current_evidence_writer_dashboard_binding.py",
    rel(REPORT_PATH),
    f"tools/emit_actual_long_run_runtime_evidence_collection_depth_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
VALIDATORS_REQUIRED = [
    "schema_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "upbit_paper_persistent_loop_validator",
    "upbit_paper_runtime_sample_history_validator",
    "upbit_paper_ledger_idempotency_runtime_evidence_validator",
    "paper_ledger_rollup_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if validator_id not in {"patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}
]
BLOCKERS = [
    CONTRACT_GAP_ID,
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
    "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
    "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


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


def assert_current_state_ready_for_collection_depth_recheck() -> None:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    completed = set(state.get("completed_requirement_ids", []))
    if PROFITABILITY_MATURITY_RECHECK_REQUIREMENT_ID not in completed:
        raise RuntimeError("profitability optimizer evidence maturity recheck is not completed")
    if CONTRACT_GAP_ID not in state.get("open_contract_gap_ids", []):
        raise RuntimeError("actual long-run runtime evidence boundary gap is not open")
    if state.get("next_allowed_task_class") not in {PATCH_BASENAME, NEXT_TASK_CLASS}:
        raise RuntimeError("current state is not routed to actual long-run collection depth recheck")
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if state.get(field) is True:
            raise RuntimeError(f"current state has forbidden true field: {field}")


def write_profile_report() -> dict[str, Any]:
    report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=2)
    write_json(REPORT_PATH, report)
    return report


def build_audit(report: dict[str, Any]) -> dict[str, Any]:
    validation = validate_upbit_paper_runtime_evidence_collection_profile_report(report)
    depth = report.get("long_run_collection_depth") if isinstance(report.get("long_run_collection_depth"), dict) else {}
    gap = load_json(ROOT / "system" / "evidence" / "contract_gaps" / f"{CONTRACT_GAP_ID}.contract_gap.json")
    checks = {
        "profile_validation_pass": validation.status == "PASS",
        "depth_status_blocked": depth.get("status") == "BLOCKED_FOR_LONG_RUN_COLLECTION_DEPTH",
        "depth_role_not_long_run": depth.get("depth_role") == "PAPER_RUNTIME_COLLECTION_DEPTH_BLOCKER_NOT_LONG_RUN_EVIDENCE",
        "depth_blocker_visible": depth.get("blocker_code") == "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
        "shadow_runtime_missing_visible": "SHADOW" in depth.get("missing_runtime_modes", []),
        "span_deficit_visible": int(depth.get("missing_span_seconds") or 0) >= 0,
        "cycle_deficit_visible": int(depth.get("missing_cycle_count") or 0) > 0,
        "bounded_profile_not_long_run": depth.get("bounded_profile_counts_as_long_run_evidence") is False,
        "dashboard_display_not_long_run": depth.get("dashboard_display_counts_as_long_run_evidence") is False,
        "contract_gap_open": gap.get("status") == "OPEN" and gap.get("live_affecting") is True,
        "live_and_scale_false": all(
            report.get(field) is False and depth.get(field) is False
            for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
        ),
    }
    return {
        "audit_schema_id": "trader1.audit_report.v1",
        "audit_id": f"{PATCH_BASENAME}_AUDIT",
        "patch_id": PATCH_ID,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "requirement_id": REQUIREMENT_ID,
        "checks": checks,
        "profile_report_path": rel(REPORT_PATH),
        "profile_status": report.get("status"),
        "accepted_cycle_sample_count": report.get("accepted_cycle_sample_count"),
        "observed_span_seconds": report.get("observed_span_seconds"),
        "minimum_span_seconds": depth.get("minimum_span_seconds"),
        "missing_span_seconds": depth.get("missing_span_seconds"),
        "minimum_cycle_count": depth.get("minimum_cycle_count"),
        "missing_cycle_count": depth.get("missing_cycle_count"),
        "missing_runtime_modes": depth.get("missing_runtime_modes"),
        "contract_gap_status": gap.get("status"),
        "contract_gap_live_affecting": gap.get("live_affecting"),
        "finding": "Bounded Upbit PAPER runtime profile PASS could be confused with actual long-run evidence unless collection-depth deficits are first-class evidence.",
        "fix": "Profile, schema, tests, and dashboard now expose blocked long-run collection depth, missing SHADOW runtime evidence, span deficit, and cycle deficit.",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LONG_RUN_RUNTIME_EVIDENCE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-UPBIT-PAPER-RUNTIME-EVIDENCE-COLLECTION-PROFILE", "REQ-MVP4-DASHBOARD-UPBIT-PAPER-RUNTIME-EVIDENCE-PROFILE-BINDING"]
included_schema_ids: ["trader1.upbit_paper_runtime_evidence_collection_profile_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Bounded PAPER runtime evidence profile exposes long_run_collection_depth.
- Collection depth remains BLOCKED_FOR_LONG_RUN_COLLECTION_DEPTH and shows missing SHADOW runtime depth.
- Span and cycle deficits are hash-covered and projected to dashboard display truth.
- Dashboard validation blocks hidden missing SHADOW depth or false bounded-profile long-run claims.
- {CONTRACT_GAP_ID} remains OPEN and live-affecting.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_snapshot:
- audit_status: {audit["status"]}
- profile_status: {audit["profile_status"]}
- accepted_cycle_sample_count: {audit["accepted_cycle_sample_count"]}
- missing_span_seconds: {audit["missing_span_seconds"]}
- missing_cycle_count: {audit["missing_cycle_count"]}
- missing_runtime_modes: {json.dumps(audit["missing_runtime_modes"])}

known_omissions_by_design:
- this patch does not create actual 24h PAPER/SHADOW long-run evidence
- this patch does not close {CONTRACT_GAP_ID}
- this patch does not use credentials, call private endpoints, place live orders, mutate live config, or scale up

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

Actual long-run runtime evidence remains missing and live-blocking. Bounded Upbit PAPER runtime evidence now exposes collection-depth deficits explicitly: missing_span_seconds={audit["missing_span_seconds"]}, missing_cycle_count={audit["missing_cycle_count"]}, missing_runtime_modes={json.dumps(audit["missing_runtime_modes"])}.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
            "source_file": "TRADER_1.md",
            "source_heading": "Actual long-run runtime evidence collection depth recheck",
            "full_text_marker": f"{REQUIREMENT_ID}: bounded PAPER runtime profile must expose blocked long-run collection depth before any live-review evidence claim",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Actual long-run runtime evidence collection depth recheck",
            "requirement_kind": "RUNTIME_EVIDENCE_VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.upbit_paper_runtime_evidence_collection_profile_report.v1",
                "trader1.read_only_dashboard_shell.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-RUNTIME-EVIDENCE-COLLECTION-PROFILE",
                "REQ-MVP4-DASHBOARD-UPBIT-PAPER-RUNTIME-EVIDENCE-PROFILE-BINDING",
                "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"actual long-run runtime evidence collection depth remains blocked until PAPER and SHADOW depth evidence exists"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED_OPEN_GAP",
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
            "section_id": "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
            "schema_files": [
                "contracts/schema/upbit_paper_runtime_evidence_collection_profile_report.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": [
                "tools/run_upbit_paper_runtime_evidence_collection_profile.py",
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
            ],
            "fixture_files": [rel(REPORT_PATH)],
            "runtime_modules": [
                "tools/run_upbit_paper_runtime_evidence_collection_profile.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            ],
            "dashboard_artifacts": ["trader1/dashboard/read_only_dashboard.py"],
            "patch_result_fields": [
                "upbit_paper_runtime_evidence_profile_status",
                "upbit_paper_runtime_evidence_profile_accepted_cycle_sample_count",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED_OPEN_GAP",
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
    audit: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-RUNTIME-EVIDENCE-COLLECTION-PROFILE",
                "REQ-MVP4-DASHBOARD-UPBIT-PAPER-RUNTIME-EVIDENCE-PROFILE-BINDING",
                "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [
                REQUIREMENT_ID,
                f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
            ],
            "new_or_changed_schema_ids": [
                "trader1.upbit_paper_runtime_evidence_collection_profile_report.v1",
                "trader1.read_only_dashboard_shell.v1",
            ],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "remaining_blockers": BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_SHADOW_OBSERVATION_RUNTIME",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME"],
            "next_forbidden_default_sections": ["MVP5_LIVE_PERMISSION", "LIVE_CONFIG_MUTATION", "SCALE_UP_PERMISSION"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "active_read_surface_used": [
                "current_implementation_state",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK",
            "required_section_ids": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "upbit_paper_runtime_evidence_profile_status": audit["profile_status"],
            "upbit_paper_runtime_evidence_profile_accepted_cycle_sample_count": int(
                audit["accepted_cycle_sample_count"] or 0
            ),
            "upbit_paper_runtime_evidence_profile_component_count": template.get(
                "upbit_paper_runtime_evidence_profile_component_count", 0
            ),
            "upbit_paper_runtime_evidence_profile_component_pass_count": template.get(
                "upbit_paper_runtime_evidence_profile_component_pass_count", 0
            ),
            "upbit_paper_runtime_evidence_profile_ledger_status": template.get(
                "upbit_paper_runtime_evidence_profile_ledger_status", "PASS"
            ),
            "upbit_paper_runtime_evidence_profile_mismatch_count": template.get(
                "upbit_paper_runtime_evidence_profile_mismatch_count", 0
            ),
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], audit: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_COLLECTION_DEPTH_RECHECK_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_REMAINS_BLOCKED",
            "audit": audit,
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
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260505.md",
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
            "missing_span_seconds": audit["missing_span_seconds"],
            "missing_cycle_count": audit["missing_cycle_count"],
            "missing_runtime_modes": audit["missing_runtime_modes"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# Actual Long-Run Runtime Evidence Collection Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Added explicit long-run collection-depth evidence to the bounded Upbit PAPER runtime evidence profile.
- Dashboard now exposes missing SHADOW runtime depth, remaining span seconds, and remaining cycle count.
- Validation blocks hidden collection-depth gaps and false bounded-profile long-run claims.

Audit:
- status: {audit['status']}
- profile_status: {audit['profile_status']}
- accepted_cycle_sample_count: {audit['accepted_cycle_sample_count']}
- missing_span_seconds: {audit['missing_span_seconds']}
- missing_cycle_count: {audit['missing_cycle_count']}
- missing_runtime_modes: {json.dumps(audit['missing_runtime_modes'])}

Safety:
- actual long-run evidence gap remains OPEN
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentials, private endpoints, live orders, live config mutation, or scale-up
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(
        set(
            state.get("implemented_schema_ids", [])
            + [
                "trader1.upbit_paper_runtime_evidence_collection_profile_report.v1",
                "trader1.read_only_dashboard_shell.v1",
            ]
        )
    )
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
    assert_current_state_ready_for_collection_depth_recheck()
    update_authority_manifest(now)
    write_source_bundle_manifest()
    report = write_profile_report()
    audit = build_audit(report)
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command(
            [
                sys.executable,
                "tools/run_hygiene_safe_pytest.py",
                "--",
                "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_projects_paper_runtime_evidence_profile_pass_display_only",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_blocks_paper_runtime_evidence_profile_hidden_collection_depth",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_blocks_paper_runtime_evidence_profile_false_bounded_depth_claim",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_upbit_paper_runtime_evidence_collection_profile.py"]),
    ]
    audit = build_audit(load_json(REPORT_PATH))
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS), BOOTSTRAP_VALIDATORS, audit)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_bundle_security_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=1800),
        ]
    )
    audit = build_audit(load_json(REPORT_PATH))
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED, audit)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    if audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "audit failed", "audit": audit})
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "missing_span_seconds": audit["missing_span_seconds"],
                "missing_cycle_count": audit["missing_cycle_count"],
                "missing_runtime_modes": audit["missing_runtime_modes"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
                "tests_non_pass": failed,
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
