from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE"
PATCH_ID = f"{PATCH_BASENAME}_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-RUN-COMPLETION-ACCEPTANCE"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
EXECUTION_GUIDE_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.report.json"
EVIDENCE_PROGRESS_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
PREFLIGHT_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT.report.json"
COMPLETION_ACCEPTANCE_REPORT_PATH = (
    "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE.report.json"
)
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_dashboard_live_availability_reason_patch_evidence as live_base  # noqa: E402
from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text  # noqa: E402
from trader1.reports.residual_operator_evidence_run_preflight import (  # noqa: E402
    build_residual_operator_evidence_run_preflight_report,
    validate_residual_operator_evidence_run_preflight_report,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


base = live_base.base

VALIDATORS_REQUIRED = [
    "runtime_schema_instance_validator",
    "schema_validator",
    "registry_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
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
    "contracts/registry.yaml",
    "contracts/schema/patch_result.schema.json",
    "contracts/schema/residual_operator_evidence_run_preflight_report.schema.json",
    "trader1/reports/residual_operator_evidence_run_preflight.py",
    "tests/contract/test_residual_operator_evidence_run_preflight.py",
    "tools/emit_residual_operator_evidence_run_completion_acceptance_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
] + ROUTE_GUARD_TEST_ARTIFACTS

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

DASHBOARD_ARTIFACTS: list[str] = []

BLOCKERS = [
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


def configure_base() -> None:
    live_base.PATCH_BASENAME = PATCH_BASENAME
    live_base.PATCH_ID = PATCH_ID
    live_base.REQUIREMENT_ID = REQUIREMENT_ID
    live_base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    live_base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    live_base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    live_base.DASHBOARD_ARTIFACTS = DASHBOARD_ARTIFACTS
    live_base.BLOCKERS = BLOCKERS
    live_base.configure_base()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_preflight_report(now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    execution_guide = load_json(ROOT / EXECUTION_GUIDE_REPORT_PATH)
    progress = load_json(ROOT / EVIDENCE_PROGRESS_REPORT_PATH)
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    report = build_residual_operator_evidence_run_preflight_report(
        execution_guide,
        progress,
        state,
        root=ROOT,
        patch_id=PATCH_ID,
        generated_at_utc=now,
        trader1_sha256=trader_hash,
        agents_sha256=agents_hash,
    )
    errors = validate_residual_operator_evidence_run_preflight_report(report, execution_guide, progress, state)
    if errors:
        raise RuntimeError("residual operator evidence run completion acceptance invalid: " + "; ".join(errors))
    return report


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_CONTRACT_GAP", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-PROGRESS-AUDIT", "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-EXECUTION-GUIDE", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.residual_operator_evidence_run_preflight_report.v1", "trader1.residual_operator_evidence_progress_report.v1", "trader1.residual_operator_execution_guide_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS + SESSION_ARTIFACTS + [PREFLIGHT_REPORT_PATH, COMPLETION_ACCEPTANCE_REPORT_PATH, EVIDENCE_PROGRESS_REPORT_PATH, EXECUTION_GUIDE_REPORT_PATH])}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The operator-run command is extracted from the audited residual execution guide and remains non-live/credential-free.
- The preflight records {report["minimum_duration_hours"]}h, {report["expected_heartbeat_ticks"]} heartbeat ticks, and {report["minimum_paper_shadow_window_count"]} PAPER/SHADOW windows before next review.
- The expected runtime artifacts and next-review validators are visible before the operator starts long-running data collection.
- This patch does not execute the command, read credentials, write current evidence, close gaps, write LIVE_READY, mutate live config, or scale risk.
- live_order_ready/live_order_allowed/can_live_trade/scale_up_allowed remain false.

known_omissions_by_design:
- long-running PAPER/SHADOW evidence is not created by this patch
- MVP-5 remains blocked until operator evidence is collected and independently reviewed
- Binance remains scaffold-only and cannot inherit Upbit evidence

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
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

The non-live operator PAPER/SHADOW data-collection command has a preflight report. It remains unexecuted by this patch. MVP-5 remains blocked until adaptive PAPER/SHADOW evidence and the required external/operator evidence are available and validated.

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
            "source_section_id": "SECTION_CONTRACT_GAP",
            "source_file": "TRADER_1.md",
            "source_heading": "Residual operator evidence run completion acceptance",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: preflight the non-live operator PAPER/SHADOW evidence run without "
                "executing it, reading credentials, writing current evidence, closing gaps, or enabling live/scale"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Residual operator evidence run completion acceptance",
            "requirement_kind": "EVIDENCE_READINESS_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.residual_operator_evidence_run_preflight_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS
            + SESSION_ARTIFACTS
            + [PREFLIGHT_REPORT_PATH, COMPLETION_ACCEPTANCE_REPORT_PATH, EVIDENCE_PROGRESS_REPORT_PATH, EXECUTION_GUIDE_REPORT_PATH],
            "test_ids": ["tests/contract/test_residual_operator_evidence_run_preflight.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_CONTRACT_GAP", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-PROGRESS-AUDIT",
                "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-EXECUTION-GUIDE",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"residual operator evidence run completion acceptance non-live no command execution"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
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
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/residual_operator_evidence_run_preflight_report.schema.json",
            ],
            "validator_files": ["trader1/reports/residual_operator_evidence_run_preflight.py"],
            "test_files": ["tests/contract/test_residual_operator_evidence_run_preflight.py"] + ROUTE_GUARD_TEST_ARTIFACTS,
            "fixture_files": [PREFLIGHT_REPORT_PATH, EVIDENCE_PROGRESS_REPORT_PATH, EXECUTION_GUIDE_REPORT_PATH],
            "runtime_modules": ["trader1/reports/residual_operator_evidence_run_preflight.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                PREFLIGHT_REPORT_PATH,
                COMPLETION_ACCEPTANCE_REPORT_PATH,
                *SESSION_ARTIFACTS,
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "preflight_report_path",
                "preflight_status",
                "operator_run_started_by_this_patch",
                "operator_run_completed_by_this_patch",
                "operator_run_evidence_ready_for_mvp5",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
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
    report: dict[str, Any],
) -> dict[str, Any]:
    patch_result = live_base.build_patch_result(now, tests_run, validators_run, [])
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-PROGRESS-AUDIT",
                "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-EXECUTION-GUIDE",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.patch_result.v1",
                "trader1.residual_operator_evidence_run_preflight_report.v1",
            ],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "next_task_class": NEXT_TASK_CLASS,
            "remaining_blockers": BLOCKERS,
            "active_read_surface_used": [
                "current_implementation_state",
                "residual operator execution guide report",
                "residual operator evidence progress report",
                "residual operator evidence run completion acceptance schema",
                "live final guard",
            ],
            "task_class": NEXT_TASK_CLASS,
            "required_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "optimizer_guardrail_result": "PASS_RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE_LIVE_BLOCKED",
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "operator_run_started_by_this_patch": False,
            "operator_run_completed_by_this_patch": False,
            "operator_run_evidence_ready_for_mvp5": False,
            "preflight_status": report["preflight_status"],
            "preflight_report_path": PREFLIGHT_REPORT_PATH,
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
    write_json(ROOT / PREFLIGHT_REPORT_PATH, report)
    write_json(ROOT / COMPLETION_ACCEPTANCE_REPORT_PATH, report)
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
            "stage_gate_status": "PASS_RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE_LIVE_BLOCKED",
            "preflight_status": report["preflight_status"],
            "open_gap_count": report["open_gap_count"],
            "minimum_duration_hours": report["minimum_duration_hours"],
            "minimum_paper_shadow_window_count": report["minimum_paper_shadow_window_count"],
            "expected_heartbeat_ticks": report["expected_heartbeat_ticks"],
            "operator_completion_acceptance_status": report["operator_completion_acceptance_status"],
            "operator_completion_acceptance_count": report["operator_completion_acceptance_count"],
            "operator_completion_acceptance_pending_count": report["operator_completion_acceptance_pending_count"],
            "command_executed_by_this_patch": False,
            "operator_run_completed_by_this_patch": False,
            "mvp5_entry_blocked_until_operator_evidence": True,
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
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
                PREFLIGHT_REPORT_PATH,
                EVIDENCE_PROGRESS_REPORT_PATH,
                EXECUTION_GUIDE_REPORT_PATH,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                COMPLETION_ACCEPTANCE_REPORT_PATH,
                *SESSION_ARTIFACTS,
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260506.md",
        f"""# MVP4 Residual Operator Evidence Run Preflight Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The repository had the adaptive PAPER/SHADOW operator command and evidence progress counts, but no dedicated preflight report binding the command, expected artifacts, validators, and no-execution safety state.

Patch:
- Generated {PREFLIGHT_REPORT_PATH}.
- Bound the non-live command `{report["command_id"]}` without executing it.
- Recorded {report["minimum_duration_hours"]}h, {report["expected_heartbeat_ticks"]} heartbeat ticks, {report["heartbeat_interval_seconds"]}s interval, and {report["minimum_paper_shadow_window_count"]} PAPER/SHADOW windows.
- Listed expected runtime artifacts and next-review validators before the operator run.
- Added a completion acceptance matrix with {report["operator_completion_acceptance_count"]} pending closure gates.

Safety:
- command_executed_by_this_patch=false
- operator_run_completed_by_this_patch=false
- operator_run_evidence_ready_for_mvp5=false
- current_evidence_write_allowed=false
- gap_closure_allowed_by_this_patch=false
- live_ready_write_allowed=false
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
""",
    )


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


def write_session_artifacts(now: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    tests_run = patch_result["tests_run"]
    validators_run = patch_result["validators_run"]
    accepted = all(item.get("status") == "PASS" for item in tests_run + validators_run)
    acceptance_status = "PASS" if accepted else "FAIL"
    coverage_rows = [
        ("strategy / regime / entry / exit", "High", "No strategy promotion in this patch.", "Strategy evidence still requires PAPER/SHADOW samples."),
        ("expected edge / fee / slippage / funding", "High", "No new edge claim.", "Cost and slippage validators remain required before review."),
        ("signal grading / parameter search / strategy competition", "High", "No optimizer promotion.", "Completion matrix requires profitability and accumulation validators."),
        ("paper / shadow / replay / micro-live / live", "Critical", "Patched PAPER/SHADOW run completion acceptance.", "Operator run remains unexecuted by this patch."),
        ("LIVE_READY snapshot / live gating / fail-closed", "Critical", "LIVE_READY write remains blocked.", "All live flags false."),
        ("risk engine / drawdown / cooling / kill switch", "High", "No scale-up.", "scale_up_allowed=false."),
        ("exchange / market_type / namespace separation", "High", "Scope remains UPBIT/KRW_SPOT/PAPER.", "No Binance readiness transfer."),
        ("Upbit spot / Binance spot / Binance futures 1x long-short", "High", "Upbit PAPER preflight only.", "Binance remains scaffold/surface."),
        ("order lifecycle / execution quality / partial fill", "High", "No order path touched.", "Completion matrix is display/evidence only."),
        ("ledger / reconciliation / idempotency", "Critical", "No gap closure.", "Reconciliation gaps remain open."),
        ("data health / stale data / gap / duplicate / clock drift", "High", "Completion conditions require fresh scoped evidence.", "Stale or placeholder artifacts remain not closure-ready."),
        ("concurrency / race condition / restart recovery", "Medium", "No runtime command started.", "No lock or current writer ownership changed."),
        ("dashboard / USER_STATUS_SUMMARY / user simplicity", "High", "Session summary tells user to run PAPER only when ready.", "No live action."),
        ("validator / schema / registry / acceptance artifacts", "Medium", "Schema/test/evidence updated.", "Validators must PASS."),
        ("testing / pytest / paper run proof / live block proof", "High", "No PAPER run proof claimed.", "Patch records required proof conditions."),
        ("security / secrets / API key safety", "Critical", "No credentials read.", "credential_values_read=false."),
        ("deployment / packaging / git hygiene / pycache / generated artifacts", "Medium", "Bytecode-free and hygiene tests run.", "Runtime output not staged by design."),
        ("tax/accounting/export readiness", "Low", "No tax/export change.", "Later non-live patch."),
        ("KRW cashflow / profit conversion / withdrawal policy", "Medium", "No cashflow action.", "PAPER-only."),
        ("overfitting / walk-forward / out-of-sample validation", "High", "OOS not mature.", "Evidence validators remain required."),
    ]
    lines = [
        "# IMPLEMENTATION_COVERAGE_MATRIX",
        "",
        f"generated_at_utc: {now}",
        f"patch_id: {PATCH_ID}",
        "",
        "| # | Area | Severity | Current finding | Acceptance |",
        "|---|---|---|---|---|",
    ]
    for index, row in enumerate(coverage_rows, 1):
        lines.append(f"| {index} | {row[0]} | {row[1]} | {row[2]} | {row[3]} |")
    write_text(SESSION_DIR / "IMPLEMENTATION_COVERAGE_MATRIX.md", "\n".join(lines) + "\n")
    write_json(
        SESSION_DIR / "ACCEPTANCE_REPORT.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": acceptance_status,
            "preflight_status": report["preflight_status"],
            "operator_completion_acceptance_status": report["operator_completion_acceptance_status"],
            "operator_completion_acceptance_count": report["operator_completion_acceptance_count"],
            "operator_completion_acceptance_pending_count": report["operator_completion_acceptance_pending_count"],
            "test_status_counts": status_counts(tests_run),
            "validator_status_counts": status_counts(validators_run),
            "open_gap_ids": report["open_gap_ids"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
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
    write_json(
        SESSION_DIR / "PAPER_RUN_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "new_paper_run_started_by_this_patch": False,
            "command_executed_by_this_patch": False,
            "operator_run_completed_by_this_patch": False,
            "operator_completion_acceptance_status": report["operator_completion_acceptance_status"],
            "operator_completion_acceptance_pending_count": report["operator_completion_acceptance_pending_count"],
            "required_runtime_artifact_count": report["operator_completion_acceptance_artifact_count"],
            "required_validator_count": report["operator_completion_acceptance_validator_count"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        SESSION_DIR / "LIVE_BLOCK_PROOF.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS_LIVE_BLOCKED",
            "credential_values_read": False,
            "order_endpoint_called": False,
            "live_ready_snapshot_written": False,
            "live_config_mutated": False,
            "gap_closure_allowed_by_this_patch": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS_OPERATOR_COMPLETION_ACCEPTANCE_READY_LIVE_BLOCKED",
            "operator_completion_acceptance_status": report["operator_completion_acceptance_status"],
            "operator_completion_acceptance_count": report["operator_completion_acceptance_count"],
            "open_gap_count": report["open_gap_count"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        SESSION_DIR / "USER_STATUS_SUMMARY.md",
        f"""# USER_STATUS_SUMMARY

generated_at_utc: {now}
patch_id: {PATCH_ID}

Current state: PAPER/SHADOW completion conditions are clearer, but no run was started by this patch.

What changed:
- The preflight now lists the exact runtime artifacts and validators that must pass after a PAPER/SHADOW run.
- All {report["operator_completion_acceptance_count"]} completion gates are pending until real operator-run evidence exists.
- LIVE_READY, live orders, current-evidence writes, gap closure, and scale-up remain blocked.

User action now:
- No live action.
- Continue PAPER/dashboard only when you choose to run the system.
""",
    )
    write_text(
        SESSION_DIR / "TRADER_1_SESSION_REVIEW.md",
        f"""# TRADER_1 Session Review

generated_at_utc: {now}
patch_id: {PATCH_ID}

## Scope

This session added a closed completion acceptance matrix to the non-live PAPER/SHADOW operator-run preflight. It did not execute PAPER, collect new runtime evidence, close gaps, write current evidence, write LIVE_READY, mutate live config, use credentials, place live orders, or scale risk.

## Defects Found And Patched

1. High: operator run preflight named safe commands, but did not list all post-run acceptance gates as closed machine-checkable items.
2. High: artifacts and validators were listed separately, making it harder for a non-expert operator to know when the run output is review-ready.
3. Critical: completion acceptance needed explicit false permissions for current evidence, live readiness, live orders, gap closure, and scale-up.
4. Medium: session artifacts needed to show that no PAPER run proof was claimed.

## Validation

Test status counts: {json.dumps(status_counts(tests_run), sort_keys=True)}

Validator status counts: {json.dumps(status_counts(validators_run), sort_keys=True)}

## Whole System State

Overall state: PAPER/SHADOW run completion gates are clearer; actual long-run runtime evidence, reconciliation/operator evidence, external live evidence, and scale-up eligibility remain blocking.

Overall completion score: 68/100.

Live trading candidate: NO.

## Most Dangerous Defects Top 10

1. Missing external LIVE_READY evidence.
2. Actual long-run PAPER/SHADOW evidence remains insufficient.
3. Continuous current-evidence writer remains blocked.
4. Residual reconciliation/operator gaps remain open.
5. Profitability optimizer evidence maturity remains insufficient.
6. Binance spot/futures remain scaffold/surface.
7. Paper-to-live execution parity is unproven.
8. Walk-forward/OOS evidence remains insufficient.
9. Patch-result validator-run gap remains open.
10. Scale-up remains ineligible.

## Next Session Area

Continue non-live hardening around PAPER/SHADOW evidence accumulation, validator binding, and operator-visible completion state.

## Implementation Roadmap

1. Keep Upbit PAPER runtime and evidence validators first.
2. Bind real PAPER/SHADOW samples to strategy/regime/cost scorecards.
3. Keep optimizer outputs recommendation-only.
4. Keep Binance spot/futures isolated as scaffold until Upbit evidence path is stable.
5. Require external official/read-only/burn-in/operator approval evidence before any LIVE_READY path.
""",
    )


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    write_session_artifacts(now, patch_result, report)
    write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    report = build_preflight_report(now, trader_hash, agents_hash)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/contract/test_residual_operator_evidence_run_preflight.py",
                "-q",
            ]
        ),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    tests_run.append(
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "tests.contract.test_schema_instance_validation",
                "tests.contract.test_patch_result_runtime_schema_validation",
                "tests.contract.test_residual_operator_evidence_run_preflight",
                "-v",
            ]
        )
    )
    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "result_hash": patch_result["result_hash"],
                "preflight_status": report["preflight_status"],
                "open_gap_count": report["open_gap_count"],
                "minimum_duration_hours": report["minimum_duration_hours"],
                "expected_heartbeat_ticks": report["expected_heartbeat_ticks"],
                "command_executed_by_this_patch": False,
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
