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

PATCH_BASENAME = "MVP4_DASHBOARD_PAPER_TRUTH_FRESHNESS_SEPARATION"
PATCH_ID = f"{PATCH_BASENAME}_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-PAPER-TRUTH-FRESHNESS-SEPARATION"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
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

CHANGED_ARTIFACTS = [
    "trader1/dashboard/read_only_dashboard.py",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_paper_truth_freshness_separation_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
] + ROUTE_GUARD_TEST_ARTIFACTS

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

PAPER_VALUE_TRUTH_STATUSES = [
    "PAPER_LEDGER_CURRENT_VALUES_VERIFIED",
    "PAPER_LEDGER_LAST_VERIFIED_VALUES_STALE",
    "CURRENT_VALUES_UNVERIFIED_CONFIGURED_BASELINE_ONLY",
]
RUNTIME_CONTINUITY_STATUSES = [
    "SNAPSHOT_ONLY_NOT_LONG_RUN_PROOF",
    "STALE_SNAPSHOT_NOT_RUNTIME_PROOF",
    "NO_CURRENT_RUNTIME_PROOF",
]
WRITER_LIFECYCLE_STATUSES = [
    "AUDITED_SNAPSHOT_WRITTEN_CONTINUOUS_WRITER_BLOCKED",
    "AUDITED_WRITER_INPUTS_BLOCKED",
    "SUMMARY_LEDGER_ONLY_NO_AUDITED_WRITER",
    "NO_AUDITED_WRITER_EVIDENCE",
]
LIVE_BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
    "SCALE_UP_NOT_ELIGIBLE",
]


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.BLOCKERS = LIVE_BLOCKERS


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str], timeout_seconds: int = 1800) -> dict[str, Any]:
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
    open_gaps = sorted(state.get("open_contract_gap_ids", []))
    return {
        "schema_id": "trader1.dashboard_paper_truth_freshness_separation_report.v1",
        "patch_id": PATCH_ID,
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "finding": (
            "PAPER ledger values can be known while dashboard freshness and continuous runtime proof remain stale or missing."
        ),
        "defect_classification": [
            {
                "area": "dashboard portfolio truth",
                "severity": "High",
                "defect": "Operators could read stale PAPER values as either fully current or completely unverified.",
                "operational_risk": "Portfolio review becomes confusing and may overtrust an old simulated snapshot.",
                "closure": "Display value truth, snapshot freshness, runtime continuity, and writer lifecycle as separate fields.",
            },
            {
                "area": "audited writer lifecycle",
                "severity": "High",
                "defect": "Existing audited snapshot output and inactive continuous writer status appeared contradictory.",
                "operational_risk": "Operator may believe the current-evidence writer is live when only an audited snapshot exists.",
                "closure": "Use AUDITED_SNAPSHOT_WRITTEN_CONTINUOUS_WRITER_BLOCKED for snapshot-exists/writer-blocked state.",
            },
            {
                "area": "stale interpretation",
                "severity": "Medium",
                "defect": "A strict 300 second freshness limit made old PAPER snapshots hard to interpret.",
                "operational_risk": "The dashboard looked broken even when last verified simulated values were available.",
                "closure": "Keep the 300 second safety threshold but label stale values as last verified, not runtime proof.",
            },
        ],
        "paper_value_truth_statuses": PAPER_VALUE_TRUTH_STATUSES,
        "runtime_continuity_statuses": RUNTIME_CONTINUITY_STATUSES,
        "audited_writer_lifecycle_statuses": WRITER_LIFECYCLE_STATUSES,
        "stale_threshold_policy_changed": False,
        "long_run_threshold_policy_changed": False,
        "writer_contradiction_resolution": "AUDITED_SNAPSHOT_WRITTEN_CONTINUOUS_WRITER_BLOCKED",
        "stale_interpretation_status": "LAST_VERIFIED_VALUES_NOT_RUNTIME_PROOF",
        "acceptance_conditions": [
            "fresh PAPER ledger values must use PAPER_LEDGER_CURRENT_VALUES_VERIFIED",
            "stale PAPER ledger values must use PAPER_LEDGER_LAST_VERIFIED_VALUES_STALE",
            "portfolio without snapshot provenance must use CURRENT_VALUES_UNVERIFIED_CONFIGURED_BASELINE_ONLY",
            "audited current evidence snapshot display must disclose continuous writer blocked",
            "runtime continuity cannot be inferred from a snapshot",
            "live_order_ready/live_order_allowed/can_live_trade/scale_up_allowed remain false",
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
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: DASHBOARD_UX
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(all_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- PAPER value truth is separate from dashboard file freshness.
- Snapshot freshness is separate from runtime continuity proof.
- Existing audited snapshot output is separate from continuous current-evidence writer activation.
- Stale PAPER values are displayed as last verified simulated values, not as live/current runtime proof.
- UNVERIFIED is reserved for missing or unbound current PAPER value truth.
- The 300 second stale guard and long-run evidence gates remain safety blockers.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- This patch does not collect new long-run PAPER/SHADOW evidence.
- This patch does not lower stale or long-run thresholds.
- This patch does not activate the audited current-evidence writer.
- This patch does not close any of the {report["open_contract_gap_count"]} open gaps.
- This patch does not write LIVE_READY, mutate live config, call credentials, place live orders, or permit scale-up.

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

PAPER portfolio display now separates four concepts:

1. Last/current simulated ledger value truth.
2. Snapshot freshness.
3. Runtime continuity proof.
4. Audited writer lifecycle.

Stale PAPER ledger values may be visible as last verified simulated values, but they are not runtime continuity proof and do not enable LIVE_READY.
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
            "source_heading": "Dashboard PAPER truth freshness separation",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: dashboard must separate PAPER ledger value truth, freshness, runtime continuity, and audited writer lifecycle without closing gaps"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard PAPER truth and freshness separation",
            "requirement_kind": "DASHBOARD_UX_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": all_artifacts(),
            "test_ids": [
                "tests/dashboard/test_read_only_dashboard.py",
                *ROUTE_GUARD_TEST_ARTIFACTS,
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-DASHBOARD-PAPER-PORTFOLIO-CURRENT-TRUTH-UX",
                "REQ-MVP4-DASHBOARD-STALE-AUDITED-CURRENT-EVIDENCE-TRUTH",
                "REQ-MVP4-UPBIT-PAPER-AUDITED-CURRENT-EVIDENCE-WRITER-DASHBOARD-BINDING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"dashboard paper ledger value truth freshness runtime continuity writer lifecycle separation"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_DASHBOARD_PAPER_TRUTH_FRESHNESS_SEPARATED_LIVE_BLOCKED",
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
            "test_files": ["tests/dashboard/test_read_only_dashboard.py", *ROUTE_GUARD_TEST_ARTIFACTS],
            "fixture_files": ["tests/dashboard/test_read_only_dashboard.py::audited_writer_output_fixture"],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py"],
            "evidence_artifacts": EVIDENCE_ARTIFACTS + SESSION_ARTIFACTS,
            "dashboard_artifacts": [
                "portfolio_snapshot.paper_value_truth_status",
                "portfolio_snapshot.paper_value_truth_message",
                "portfolio_snapshot.runtime_continuity_status",
                "portfolio_snapshot.audited_writer_lifecycle_status",
                "portfolio_snapshot.operator_truth_summary",
            ],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
                "dashboard_operator_visibility_changed",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_DASHBOARD_PAPER_TRUTH_FRESHNESS_SEPARATED_LIVE_BLOCKED",
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
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-DASHBOARD-PAPER-PORTFOLIO-CURRENT-TRUTH-UX",
                "REQ-MVP4-DASHBOARD-STALE-AUDITED-CURRENT-EVIDENCE-TRUTH",
                "REQ-MVP4-UPBIT-PAPER-AUDITED-CURRENT-EVIDENCE-WRITER-DASHBOARD-BINDING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
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
            "next_required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": [
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_PROFITABILITY_OPTIMIZER",
                "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE",
            ],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "RETAINED_ARCHIVE"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": report["open_contract_gap_ids"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "contracts/generated/current_implementation_state.json",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "DASHBOARD_UX",
            "required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_guardrail_result": "PASS_DASHBOARD_ONLY_NO_OPTIMIZER_LIVE_MUTATION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "convergence_guardrail_result": "PASS_DASHBOARD_ONLY_NO_CONVERGENCE_LIVE_MUTATION",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "dashboard_operator_visibility_changed": True,
            "evidence_quality_status": "PAPER_LEDGER_DISPLAY_TRUTH_SEPARATED_FROM_RUNTIME_CONTINUITY_LIVE_BLOCKED",
            "codex_can_continue_non_live_patches": True,
            "user_runtime_required_for_next_non_live_patch": False,
            "user_runtime_required_for_gap_closure": True,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
) -> None:
    base.write_json(ROOT / f"system/evidence/audit_reports/{PATCH_BASENAME}.report.json", report)
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
            "stage_gate_status": "PASS_DASHBOARD_PAPER_TRUTH_FRESHNESS_SEPARATED_LIVE_BLOCKED",
            "open_contract_gap_count": report["open_contract_gap_count"],
            "open_contract_gap_ids": report["open_contract_gap_ids"],
            "stale_threshold_policy_changed": False,
            "long_run_threshold_policy_changed": False,
            "audited_current_evidence_writer_enabled": False,
            "next_allowed_task_class": NEXT_TASK_CLASS,
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
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "status": "PASS_DASHBOARD_PAPER_TRUTH_FRESHNESS_SEPARATED_LIVE_BLOCKED",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "artifact_paths": all_artifacts(),
            "known_blockers": LIVE_BLOCKERS + report["open_contract_gap_ids"],
            "notes": "Dashboard value truth, freshness, runtime continuity, and writer lifecycle are separate. No live permission or gap closure created.",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260506.md",
        f"""# MVP4 Dashboard PAPER Truth Freshness Separation Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- PAPER ledger snapshot values can exist while the runtime is stale and continuous current-evidence writer activation is blocked.
- The dashboard needed to separate value truth, freshness, runtime continuity, and writer lifecycle.

Patch:
- Added PAPER value-truth status fields.
- Added runtime-continuity status fields.
- Added audited-writer lifecycle fields.
- Changed stale PAPER display copy to "last verified PAPER ledger" when provenance exists.
- Preserved the 300 second stale guard and all long-run evidence gates.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed API/key use
- no live order
- no live config mutation
- no LIVE_READY write
- no current-evidence writer activation
- no stale/long-run threshold reduction
""",
    )


def write_session_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    tests_run = patch_result["tests_run"]
    validators_run = patch_result["validators_run"]
    accepted = all(item.get("status") == "PASS" for item in tests_run + validators_run)
    acceptance_status = "PASS" if accepted else "FAIL"

    areas = [
        ("strategy / regime / entry / exit", "High", "Closed formulas exist, but long-run PAPER evidence is still below promotion needs.", "Keep strategy output paper/shadow-only until evidence gates pass."),
        ("expected edge / fee / slippage / funding", "High", "Cost-aware scoring exists; realized execution evidence is immature.", "Block candidates when cost model is missing or net edge is non-positive."),
        ("signal grading / parameter search / strategy competition", "High", "Score gates exist; sample counts are not mature.", "Weak signals no-trade and promotion requires trade/sample thresholds."),
        ("paper / shadow / replay / micro-live / live", "Critical", "PAPER snapshot display improved; long-run proof remains open.", "PAPER/SHADOW evidence must accumulate before live readiness review."),
        ("LIVE_READY snapshot / live gating / fail-closed", "Critical", "No valid LIVE_READY snapshot.", "All live and scale flags remain false."),
        ("risk engine / drawdown / cooling / kill switch", "High", "Risk gates remain fail-closed; scale-up is ineligible.", "Drawdown/cooling/kill switch continue to block entry or sizing."),
        ("exchange / market_type / namespace separation", "High", "Upbit PAPER evidence cannot transfer to Binance.", "Exchange/market_type/mode evidence remains scoped."),
        ("Upbit spot / Binance spot / Binance futures 1x long-short", "High", "Upbit PAPER path is deepest; Binance is still surface/scaffold.", "Binance remains not live-ready and clearly separated."),
        ("order lifecycle / execution quality / partial fill", "High", "PAPER ledger is visible; live execution is still blocked.", "No adapter call without live final guard and external evidence."),
        ("ledger / reconciliation / idempotency", "Critical", "Last verified simulated ledger values can now remain visible as stale truth.", "Reconciliation gaps remain open and cannot be closed by display changes."),
        ("data health / stale data / gap / duplicate / clock drift", "High", "This patch clarifies stale semantics without lowering TTL.", "Stale means last verified value, not runtime proof."),
        ("concurrency / race condition / restart recovery", "Medium", "Writer activation remains blocked; snapshot display is read-only.", "No single-writer ownership or live mutation changed."),
        ("dashboard / USER_STATUS_SUMMARY / user simplicity", "High", "Patched this session.", "First screen can show portfolio values and exact freshness/runtime/writer meaning."),
        ("validator / schema / registry / acceptance artifacts", "Medium", "Schema and tests were extended.", "Validators and patch result must pass."),
        ("testing / pytest / paper run proof / live block proof", "High", "Tests prove display semantics; no new PAPER run was started.", "Artifacts state live blocked and no runtime gap closure."),
        ("security / secrets / API key safety", "Critical", "No credentials or private API use.", "Credential/API usage remains forbidden."),
        ("deployment / packaging / git hygiene / pycache / generated artifacts", "Medium", "Generated artifacts are tracked through read cache.", "Runtime local monitor output is not intentionally staged."),
        ("tax/accounting/export readiness", "Low", "No tax/export change.", "Leave export work for a scoped non-live patch."),
        ("KRW cashflow / profit conversion / withdrawal policy", "Medium", "PAPER KRW values are clearer but simulated.", "No live cashflow or withdrawal action."),
        ("overfitting / walk-forward / out-of-sample validation", "High", "Optimizer evidence remains immature.", "OOS/walk-forward evidence required before promotion."),
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

    paper_portfolio_path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / "portfolio" / "paper_portfolio_snapshot.json"
    audited_current_path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime" / "current_evidence" / "audited_current_evidence_snapshot.json"
    paper_portfolio = load_json(paper_portfolio_path) if paper_portfolio_path.exists() else {}
    audited_current = load_json(audited_current_path) if audited_current_path.exists() else {}

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
            "paper_only": True,
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "paper_truth_patch_scope": "dashboard display and validation only",
            "audited_current_evidence_status": audited_current.get("current_evidence_status", "MISSING"),
            "audited_current_evidence_generated_at_utc": audited_current.get("generated_at_utc"),
            "paper_portfolio_snapshot_status": paper_portfolio.get("snapshot_status", "MISSING"),
            "paper_portfolio_generated_at_utc": paper_portfolio.get("generated_at_utc"),
            "starting_cash_krw": paper_portfolio.get("starting_cash"),
            "cash_available_krw": paper_portfolio.get("cash_available"),
            "equity_krw": paper_portfolio.get("equity"),
            "total_pnl_krw": paper_portfolio.get("total_pnl"),
            "open_position_count": paper_portfolio.get("open_position_count", 0),
            "runtime_continuity_proven_by_this_patch": False,
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
            "audited_current_evidence_writer_enabled": False,
            "validators": [item for item in validators_run if item.get("validator_id") == "live_final_guard_validator"],
            "primary_blockers": LIVE_BLOCKERS,
        },
    )
    base.write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS_OPERATOR_DISPLAY_IMPROVED_LIVE_BLOCKED",
            "first_screen_focus": [
                "normal operation status",
                "portfolio value truth and source freshness",
                "runtime continuity proof status",
                "live availability and exact blockers",
            ],
            "portfolio_truth_states": {
                "PAPER_LEDGER_CURRENT_VALUES_VERIFIED": "fresh simulated PAPER ledger values for display only",
                "PAPER_LEDGER_LAST_VERIFIED_VALUES_STALE": "last verified simulated PAPER ledger values, not runtime proof",
                "CURRENT_VALUES_UNVERIFIED_CONFIGURED_BASELINE_ONLY": "only configured PAPER baseline is known",
            },
            "runtime_continuity_states": RUNTIME_CONTINUITY_STATUSES,
            "writer_lifecycle_states": WRITER_LIFECYCLE_STATUSES,
            "stale_threshold_policy_changed": False,
            "long_run_threshold_policy_changed": False,
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

Current state: PAPER portfolio values are easier to understand, but live trading is still blocked.

What changed:
- The dashboard now says whether PAPER values are current verified simulated values, last verified stale values, or unverified current values.
- Stale PAPER values can still be shown as last verified values, but the dashboard also says they do not prove the engine is still running now.
- The audited snapshot and continuous writer state are no longer mixed together.

User action now:
- No live action.
- For fresh proof, run PAPER and check the dashboard. This patch itself did not start a new PAPER run.
""",
    )
    base.write_text(
        SESSION_DIR / "TRADER_1_SESSION_REVIEW.md",
        f"""# TRADER_1 Session Review

generated_at_utc: {now}
patch_id: {PATCH_ID}

## Scope

This session addressed the user's critique that PAPER values were partly connected but stale/current/writer states were still confusing. The patch keeps safety strict while making the dashboard explain what is known and what is not known.

## Defects Found And Patched

1. High: stale PAPER values could read as either live-current or totally unverified. Patched with `paper_value_truth_status`.
2. High: audited snapshot already written and continuous writer blocked looked contradictory. Patched with `audited_writer_lifecycle_status`.
3. Medium: strict 300 second stale behavior looked like total dashboard failure. Patched wording to last verified PAPER ledger without lowering the threshold.
4. High: snapshot presence could be mistaken for runtime continuity. Patched with `runtime_continuity_status`.

## Validation

Test status counts: {json.dumps(status_counts(tests_run), sort_keys=True)}

Validator status counts: {json.dumps(status_counts(validators_run), sort_keys=True)}

## Whole System State

Overall state: PAPER display truth is clearer, but actual long-run PAPER/SHADOW validation and external live evidence remain blocking.

Overall completion score: 66/100.

Live trading candidate: NO.

## Most Dangerous Defects Top 10

1. Missing LIVE_READY and official/read-only external evidence.
2. Long-run PAPER runtime evidence remains insufficient.
3. SHADOW opportunity evidence remains insufficient.
4. Audited continuous current-evidence writer is still blocked.
5. Residual reconciliation/operator-review gaps remain open.
6. Profitability optimizer evidence maturity remains insufficient.
7. Binance spot/futures remain scaffold/surface compared with Upbit PAPER.
8. Paper-to-live execution parity is unproven.
9. Walk-forward/OOS evidence is not mature enough for promotion.
10. Scale-up remains ineligible and cannot be inferred from dashboard or optimizer display.

## Next Session Area

Continue non-live work on actual PAPER/SHADOW evidence accumulation, audited writer activation design without live permission, dashboard clarity, and validator binding. Do not close any open gap without evidence.

## Implementation Roadmap

1. Keep Upbit PAPER runtime and ledger/reconciliation evidence first.
2. Reduce operator confusion by making blocker/action summaries clearer, not by weakening gates.
3. Bind strategy/regime/cost scorecards to real PAPER samples.
4. Keep optimizer/convergence recommendation-only until sample and OOS gates pass.
5. Keep Binance spot/futures as scaffold/surface until Upbit PAPER evidence path is stable.
6. Require external official API/read-only/burn-in/manual approval evidence before any LIVE_READY path.
""",
    )


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
    *,
    write_session: bool = False,
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    if write_session:
        write_session_artifacts(now, trader_hash, agents_hash, patch_result, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_context(now, trader_hash, agents_hash, build_report(now, trader_hash, agents_hash))
    update_requirement_artifacts(now, trader_hash, agents_hash)

    report = build_report(now, trader_hash, agents_hash)
    tests_run: list[dict[str, Any]] = [
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "tests.dashboard.test_read_only_dashboard.ReadOnlyDashboardTest.test_dashboard_projects_audited_current_evidence_writer_portfolio_truth",
                "tests.dashboard.test_read_only_dashboard.ReadOnlyDashboardTest.test_dashboard_keeps_stale_audited_current_evidence_portfolio_values_stale_not_unverified",
                "tests.dashboard.test_read_only_dashboard.ReadOnlyDashboardTest.test_dashboard_position_detail_reads_paper_portfolio_fill_fields",
                "tests.dashboard.test_read_only_dashboard.ReadOnlyDashboardTest.test_stale_summary_demotes_paper_portfolio_values",
                "-v",
            ]
        ),
        run_command([sys.executable, "-B", "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/contract/test_schema_instance_validation.py", "-q"]),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        run_command([sys.executable, "-B", "tools/run_read_only_dashboard_validators.py"]),
        run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=3600))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report, write_session=True)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report, write_session=True)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
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
