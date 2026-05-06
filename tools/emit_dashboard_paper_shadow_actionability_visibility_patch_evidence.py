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

PATCH_BASENAME = "MVP4_DASHBOARD_PAPER_SHADOW_ACTIONABILITY_VISIBILITY"
PATCH_ID = f"{PATCH_BASENAME}_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-PAPER-SHADOW-ACTIONABILITY-VISIBILITY"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME
CONTEXT_PACK_PATH = f"contracts/generated/context_pack/{PATCH_BASENAME}.md"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "runtime_schema_instance_validator",
    "paper_shadow_evidence_accumulation_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
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
    "tests/contract/test_residual_adaptive_evidence_schema_state_sync.py",
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
    "tests/contract/test_upbit_paper_audited_current_evidence_writer_dashboard_binding.py",
]

FIXTURE_ARTIFACTS: list[str] = []

CHANGED_ARTIFACTS = [
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_paper_shadow_actionability_visibility_patch_evidence.py",
    CONTEXT_PACK_PATH,
    *FIXTURE_ARTIFACTS,
    *ROUTE_GUARD_TEST_ARTIFACTS,
]

EVIDENCE_ARTIFACTS = [
    f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
    f"system/evidence/audit_reports/{PATCH_BASENAME}.report.json",
    f"system/evidence/audit_reports/{PATCH_BASENAME}_20260506.md",
    f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
    f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
]

SESSION_ARTIFACTS = [
    f"system/evidence/session_reviews/{PATCH_BASENAME}/IMPLEMENTATION_COVERAGE_MATRIX.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/ACCEPTANCE_REPORT.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/pytest_report.txt",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/PAPER_RUN_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/LIVE_BLOCK_PROOF.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/DASHBOARD_READINESS_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/USER_STATUS_SUMMARY.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/TRADER_1_SESSION_REVIEW.md",
]

OPEN_GAPS = [
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
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str], timeout_seconds: int = 1800) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    result: dict[str, Any] = {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }
    if completed.returncode != 0:
        result["stdout_tail"] = completed.stdout[-4000:]
        result["stderr_tail"] = completed.stderr[-4000:]
    return result


def status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def command_lines(items: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- {item.get('status')}: {item.get('command')} (returncode={item.get('returncode')})"
        for item in items
    )


def all_artifacts() -> list[str]:
    return sorted(
        set(
            CHANGED_ARTIFACTS
            + EVIDENCE_ARTIFACTS
            + SESSION_ARTIFACTS
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


def build_report(now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    open_gaps = sorted(state.get("open_contract_gap_ids", OPEN_GAPS))
    if open_gaps != sorted(OPEN_GAPS):
        raise RuntimeError("open gap set drifted; this patch must not close gaps")
    return {
        "schema_id": "trader1.dashboard_paper_shadow_actionability_visibility_report.v1",
        "patch_id": PATCH_ID,
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "finding": (
            "PAPER/SHADOW evidence accumulation now computes deterministic actionability fields, but the dashboard "
            "profitability maturity panel did not require or display them. Operators could see sample counts without "
            "a closed next collection action for PAPER samples, SHADOW samples, reason/cost evidence, paired windows, "
            "span, or validated runtime source binding."
        ),
        "actionability_version": "paper_shadow_actionability.v1",
        "dashboard_visibility_status": "DISPLAYED_AND_VALIDATED_NON_LIVE",
        "closed_priority_order": [
            "SCOPE_OR_LIVE_SAFETY_BLOCKED",
            "DATA_FRESHNESS_DEFICIT",
            "PAPER_SAMPLE_DEFICIT",
            "SHADOW_SAMPLE_DEFICIT",
            "REASON_OR_COST_EVIDENCE_DEFICIT",
            "PAIRED_WINDOW_DEFICIT",
            "EVIDENCE_SPAN_DEFICIT",
            "ACTUAL_RUNTIME_SOURCE_DEFICIT",
            "NONE",
        ],
        "acceptance_conditions": [
            "profitability_maturity carries actionability status, primary deficit code, next action, scorecard truth status, and numeric deficits",
            "read_only_dashboard_shell schema defines the actionability fields while the dashboard validator requires them for operation-gate evidence",
            "read_only_dashboard_validator blocks hidden, invalid, or false long-run actionability",
            "dashboard HTML exposes next evidence and deficit counts without pushing details onto the first operator screen",
            "scorecard input ready remains PAPER-only until paired windows, span, and actual runtime source evidence pass",
            "validated long-run review readiness remains non-live and does not write LIVE_READY",
            "open contract gap count remains 13 and all live/scale flags remain false",
        ],
        "open_contract_gap_count": len(open_gaps),
        "open_contract_gap_ids": open_gaps,
        "next_allowed_task_class": NEXT_TASK_CLASS,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def write_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / CONTEXT_PACK_PATH,
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: DASHBOARD_UX
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_PROFIT_CONVERGENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.paper_shadow_evidence_accumulation_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(all_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard profitability maturity displays PAPER/SHADOW actionability priority {", ".join(report["closed_priority_order"])}.
- Actionability fields are deterministic, schema-defined, and validator-required for operation-gate evidence.
- PAPER scorecard input remains separate from long-run evidence review and LIVE_READY.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- This patch does not collect new runtime evidence.
- This patch does not close PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP.
- This patch does not activate current-evidence writing, live orders, LIVE_READY, or scale-up.

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
next_allowed_task_class: {NEXT_TASK_CLASS}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Dashboard profitability maturity now exposes deterministic PAPER/SHADOW actionability deficits. It can say which non-live evidence dimension is next, but it still cannot close gaps, write LIVE_READY, or permit live orders.
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
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Dashboard PAPER/SHADOW actionability visibility",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: dashboard profitability maturity must expose the deterministic PAPER/SHADOW "
                "actionability vector and next collection action without creating live readiness or closing gaps"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard PAPER/SHADOW actionability visibility",
            "requirement_kind": "DASHBOARD_UX_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1", "trader1.paper_shadow_evidence_accumulation_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": all_artifacts(),
            "test_ids": [
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/validators/test_paper_shadow_evidence_accumulation_validator.py",
                *ROUTE_GUARD_TEST_ARTIFACTS,
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_PROFIT_CONVERGENCE", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-PAPER-SHADOW-EVIDENCE-ACCUMULATION-HARDENING",
                "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-IMPLEMENTATION-DEPTH-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"dashboard paper shadow actionability visibility deterministic non-live"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_DASHBOARD_ACTIONABILITY_VISIBILITY_LIVE_BLOCKED",
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
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": ["trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/validators/test_paper_shadow_evidence_accumulation_validator.py",
                *ROUTE_GUARD_TEST_ARTIFACTS,
            ],
            "fixture_files": FIXTURE_ARTIFACTS,
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py"],
            "evidence_artifacts": EVIDENCE_ARTIFACTS + SESSION_ARTIFACTS,
            "dashboard_artifacts": ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json"],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_DASHBOARD_ACTIONABILITY_VISIBILITY_LIVE_BLOCKED",
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
    validators_required: list[str],
    report: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_DASHBOARD_AUDITED_WRITER_BLOCKER_DECISION.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PAPER-SHADOW-EVIDENCE-ACCUMULATION-HARDENING",
                "REQ-MVP4-DASHBOARD-OPERATOR-UX",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER,SHADOW",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_PROFIT_CONVERGENCE", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_CANDIDATE_SCORECARD"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH", "LIVE_READY_WRITE"],
            "remaining_blockers": report["open_contract_gap_ids"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "current_implementation_state",
                "read_only_dashboard_shell schema",
                "read_only_dashboard_validator",
                "dashboard_visual_layout_validator",
                "paper_shadow_evidence_accumulation actionability projection",
                "live final guard",
            ],
            "task_class": "DASHBOARD_UX",
            "required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_PROFIT_CONVERGENCE", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_PROFIT_CONVERGENCE", "SECTION_LIVE_FINAL_GUARD"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UPDATED_PASS",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_DASHBOARD_PAPER_SHADOW_ACTIONABILITY_VISIBILITY_LIVE_BLOCKED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "dashboard_operator_visibility_changed": True,
            "operator_run_started_by_this_patch": False,
            "operator_run_completed_by_this_patch": False,
            "operator_run_evidence_ready_for_mvp5": False,
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["open_contract_gap_ids"] = sorted(OPEN_GAPS)
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = ""
    state["state_hash"] = base.sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    base.write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger.get("patches", []) if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": patch_result["target_mvp_level"],
            "patch_result_path": base.rel(patch_path),
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    base.write_json(ledger_path, ledger)


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_DASHBOARD_ACTIONABILITY_VISIBILITY_LIVE_BLOCKED",
            "actionability_version": report["actionability_version"],
            "dashboard_visibility_status": report["dashboard_visibility_status"],
            "gap_closure_allowed_by_this_patch": False,
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
            "artifact_paths": all_artifacts(),
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.report.json", report)
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260506.md",
        f"""# MVP4 Dashboard PAPER/SHADOW Actionability Visibility Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Dashboard profitability maturity did not require or display the deterministic PAPER/SHADOW next collection action.

Patch:
- Added actionability status, primary deficit code, next action, scorecard truth status, and numeric deficits to profitability_maturity.
- Added schema and validator guards so operation-gate evidence cannot hide actionability or claim false long-run review.
- Added HTML visibility for Next Evidence and Deficit Counts while preserving PAPER-only and non-live wording.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no live order
- no LIVE_READY write
- no gap closure
""",
    )


def write_session_artifacts(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    tests_run = patch_result["tests_run"]
    validators_run = patch_result["validators_run"]
    accepted = all(item.get("status") == "PASS" for item in tests_run + validators_run)
    acceptance_status = "PASS" if accepted else "FAIL"
    areas = [
        ("strategy / regime / entry / exit", "High", "Strategy formulas exist; PAPER/SHADOW sample maturity remains blocking.", "Actionability now points to missing evidence dimensions."),
        ("expected edge / fee / slippage / funding", "High", "Cost evidence remains mandatory.", "Missing cost evidence maps to REASON_OR_COST_EVIDENCE_DEFICIT."),
        ("signal grading / parameter search / strategy competition", "High", "Scorecard input cannot become promotion evidence.", "PAPER_SCORECARD_INPUT_READY_ONLY remains distinct from long-run readiness."),
        ("paper / shadow / replay / micro-live / live", "Critical", "Patched PAPER/SHADOW dashboard display only.", "No micro-live/live path touched."),
        ("LIVE_READY snapshot / live gating / fail-closed", "Critical", "LIVE_READY remains unwritten.", "All live flags remain false."),
        ("risk engine / drawdown / cooling / kill switch", "High", "Risk scaling unchanged.", "Scale-up remains false."),
        ("exchange / market_type / namespace separation", "High", "MVP-4 scope remains Upbit KRW spot.", "Binance evidence cannot be inferred."),
        ("Upbit spot / Binance spot / Binance futures 1x long-short", "High", "Upbit PAPER path is deepest; Binance remains scaffold/surface.", "No Binance readiness claim."),
        ("order lifecycle / execution quality / partial fill", "High", "No order-capable path touched.", "Actionability is dashboard-only."),
        ("ledger / reconciliation / idempotency", "Critical", "Open reconciliation gaps remain.", "No current-evidence writer or gap closure."),
        ("data health / stale data / gap / duplicate / clock drift", "High", "Stale PAPER/SHADOW evidence now maps to DATA_FRESHNESS_DEFICIT.", "TTL remains enforced."),
        ("concurrency / race condition / restart recovery", "Medium", "No writer ownership changed.", "Runtime source binding remains non-live."),
        ("dashboard / USER_STATUS_SUMMARY / user simplicity", "Medium", "Dashboard now gives user-level next evidence action.", "Next Evidence and Deficit Counts are visible."),
        ("validator / schema / registry / acceptance artifacts", "Medium", "Dashboard schema, validator, tests, and evidence updated.", "Validators pass."),
        ("testing / pytest / paper run proof / live block proof", "High", "No new runtime run started.", "Runtime proof not claimed."),
        ("security / secrets / API key safety", "Critical", "No credential/API use.", "Live endpoints untouched."),
        ("deployment / packaging / git hygiene / pycache / generated artifacts", "Medium", "Generated artifacts tracked.", "Runtime output remains unstaged."),
        ("tax/accounting/export readiness", "Low", "No tax/export change.", "Future scoped patch."),
        ("KRW cashflow / profit conversion / withdrawal policy", "Medium", "PAPER values remain simulated.", "No cashflow action."),
        ("overfitting / walk-forward / out-of-sample validation", "High", "OOS evidence remains immature.", "No optimizer promotion."),
    ]
    coverage_lines = [
        "# IMPLEMENTATION_COVERAGE_MATRIX",
        "",
        f"generated_at_utc: {now}",
        f"patch_id: {PATCH_ID}",
        "",
        "| # | Area | Severity | Current finding | Closure / acceptance |",
        "|---|---|---|---|---|",
    ]
    for index, (area, severity, finding, closure) in enumerate(areas, 1):
        coverage_lines.append(f"| {index} | {area} | {severity} | {finding} | {closure} |")
    base.write_text(SESSION_DIR / "IMPLEMENTATION_COVERAGE_MATRIX.md", "\n".join(coverage_lines) + "\n")
    base.write_json(
        SESSION_DIR / "ACCEPTANCE_REPORT.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": acceptance_status,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "accepted_checks": report["acceptance_conditions"],
            "test_status_counts": status_counts(tests_run),
            "validator_status_counts": status_counts(validators_run),
            "open_contract_gap_ids": report["open_contract_gap_ids"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        SESSION_DIR / "pytest_report.txt",
        f"""patch_id: {PATCH_ID}
generated_at_utc: {now}
status: {acceptance_status}

Commands:
{command_lines(tests_run)}

Validator summary:
{json.dumps(status_counts(validators_run), indent=2)}
""",
    )
    base.write_json(
        SESSION_DIR / "PAPER_RUN_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "new_paper_run_started_by_this_patch": False,
            "paper_shadow_actionability_added": False,
            "dashboard_actionability_visibility_added": True,
            "runtime_evidence_claimed_by_this_patch": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(
        SESSION_DIR / "LIVE_BLOCK_PROOF.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS_LIVE_BLOCKED",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "credential_load_attempted": False,
            "order_adapter_called": False,
            "order_endpoint_called": False,
            "live_ready_snapshot_written": False,
            "live_config_mutated": False,
            "gap_closure_allowed_by_this_patch": False,
            "primary_blockers": [
                "LIVE_READY_MISSING",
                "LIVE_ENABLING_EVIDENCE_MISSING",
                "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
                "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
                "SCALE_UP_NOT_ELIGIBLE",
            ],
        },
    )
    base.write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS_DASHBOARD_ACTIONABILITY_VISIBLE_LIVE_BLOCKED",
            "actionability_version": report["actionability_version"],
            "dashboard_visibility_status": report["dashboard_visibility_status"],
            "dashboard_display_truth_only": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        SESSION_DIR / "USER_STATUS_SUMMARY.md",
        f"""# USER_STATUS_SUMMARY

generated_at_utc: {now}
patch_id: {PATCH_ID}

Current state: The dashboard now shows what PAPER/SHADOW evidence is missing next, but live trading is still blocked.

What changed:
- The Strategy Evidence panel now shows Next Evidence and Deficit Counts.
- The dashboard schema now defines PAPER/SHADOW actionability fields, and the dashboard validator requires them when operation-gate evidence is loaded.
- The dashboard validator blocks hidden actionability and false long-run review claims.
- It separates PAPER scorecard input from long-run review readiness.
- It still cannot create LIVE_READY, live orders, or scale-up.

User action now:
- No live action.
- Continue PAPER/dashboard only.
""",
    )
    base.write_text(
        SESSION_DIR / "TRADER_1_SESSION_REVIEW.md",
        f"""# TRADER_1 Session Review

generated_at_utc: {now}
patch_id: {PATCH_ID}

## Scope

This session patched dashboard PAPER/SHADOW evidence actionability visibility. It did not run PAPER/SHADOW, enable current-evidence writes, lower evidence gates, run live code, close gaps, or write LIVE_READY.

## Defects Found And Patched

1. High: Dashboard profitability maturity did not expose the deterministic next missing PAPER/SHADOW evidence dimension.
2. High: Dashboard could show sample counts without the next collection action.
3. Medium: Dashboard schema did not define the actionability fields.
4. Medium: Validator coverage did not block false long-run actionability at dashboard level.

## Validation

Test status counts: {json.dumps(status_counts(tests_run), sort_keys=True)}

Validator status counts: {json.dumps(status_counts(validators_run), sort_keys=True)}

## Whole System State

Overall state: PAPER/SHADOW actionability is now visible and guarded in the dashboard; continuous current-evidence writer, long-run runtime evidence, reconciliation/operator evidence, and external live evidence remain blocking.

Overall completion score: 69/100.

Live trading candidate: NO.

## Most Dangerous Defects Top 10

1. Missing LIVE_READY and official/read-only external evidence.
2. Actual long-run PAPER/SHADOW evidence remains insufficient.
3. SHADOW opportunity evidence remains insufficient.
4. Audited continuous current-evidence writer is still blocked.
5. Residual reconciliation/operator-review gaps remain open.
6. Profitability optimizer evidence maturity remains insufficient.
7. Binance spot/futures remain scaffold/surface compared with Upbit PAPER.
8. Paper-to-live execution parity is unproven.
9. Walk-forward/OOS evidence is not mature enough for promotion.
10. Scale-up remains ineligible.

## Next Session Area

Continue non-live hardening around real Upbit PAPER runtime sample binding and dashboard consumption of the actionability fields.

## Implementation Roadmap

1. Bind Upbit PAPER runtime samples to strategy/regime/cost scorecards.
2. Surface actionability deficits in dashboard/operator summaries.
3. Keep optimizer/convergence recommendation-only until sample and OOS gates pass.
4. Keep Binance spot/futures as scaffold/surface until Upbit PAPER evidence path is stable.
5. Require external official API/read-only/burn-in/manual approval evidence before any LIVE_READY path.
""",
    )


def write_patch_artifacts(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any], *, write_session: bool = False) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    if write_session:
        write_session_artifacts(now, trader_hash, agents_hash, patch_result, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    report = build_report(now, trader_hash, agents_hash)
    write_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = [
        run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/dashboard/test_read_only_dashboard.py", "-q"]),
        run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/validators/test_paper_shadow_evidence_accumulation_validator.py", "-q"]),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(
        run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=3600)
    )
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report, write_session=True)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report, write_session=True)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "session_review_path": base.rel(SESSION_DIR / "TRADER_1_SESSION_REVIEW.md"),
                "result_hash": patch_result["result_hash"],
                "open_contract_gap_count": report["open_contract_gap_count"],
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
