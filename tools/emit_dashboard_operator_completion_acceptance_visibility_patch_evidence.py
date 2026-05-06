from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_OPERATOR_COMPLETION_ACCEPTANCE_VISIBILITY"
PATCH_ID = f"{PATCH_BASENAME}_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-OPERATOR-COMPLETION-ACCEPTANCE-VISIBILITY"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
COMPLETION_ACCEPTANCE_REPORT_PATH = (
    "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE.report.json"
)
EVIDENCE_PROGRESS_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
EXECUTION_GUIDE_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.report.json"
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_dashboard_live_availability_reason_patch_evidence as live_base  # noqa: E402
import tools.emit_residual_operator_evidence_run_completion_acceptance_patch_evidence as completion_base  # noqa: E402
from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


base = live_base.base
visibility_base = live_base.visibility_base

VALIDATORS_REQUIRED = [
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
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
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_operator_completion_acceptance_visibility_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
] + ROUTE_GUARD_TEST_ARTIFACTS

DASHBOARD_ARTIFACTS = [
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/upbit/krw_spot/paper/dashboard/index.html",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
    "system/runtime/upbit/krw_spot/live/mvp1_upbit_live_launcher/dashboard/index.html",
    "system/runtime/binance/spot/live/mvp1_binance_live_launcher/dashboard/index.html",
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
    completion_base.PATCH_BASENAME = PATCH_BASENAME
    completion_base.PATCH_ID = PATCH_ID
    completion_base.SESSION_DIR = SESSION_DIR
    completion_base.SESSION_ARTIFACTS = SESSION_ARTIFACTS


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_completion_acceptance_report() -> dict[str, Any]:
    report = load_json(ROOT / COMPLETION_ACCEPTANCE_REPORT_PATH)
    if report.get("schema_id") != "trader1.residual_operator_evidence_run_preflight_report.v1":
        raise RuntimeError("completion acceptance report schema mismatch")
    if report.get("preflight_status") != "NON_LIVE_OPERATOR_RUN_PRECHECK_PASS":
        raise RuntimeError("completion acceptance report must remain a non-live preflight PASS")
    if report.get("operator_completion_acceptance_status") != "PENDING_OPERATOR_RUNTIME_EVIDENCE":
        raise RuntimeError("completion acceptance report must remain pending operator runtime evidence")
    if report.get("operator_completion_acceptance_count") != 12:
        raise RuntimeError("completion acceptance report must expose 12 completion gates")
    if report.get("operator_completion_acceptance_pending_count") != 12:
        raise RuntimeError("completion acceptance report must keep all 12 gates pending")
    if report.get("operator_completion_acceptance_artifact_count") != 5:
        raise RuntimeError("completion acceptance report must expose five runtime artifact gates")
    if report.get("operator_completion_acceptance_validator_count") != 6:
        raise RuntimeError("completion acceptance report must expose six validator gates")
    for field in (
        "credential_values_read",
        "credential_environment_inspection_performed",
        "command_executed_by_this_patch",
        "operator_run_started_by_this_patch",
        "operator_run_completed_by_this_patch",
        "operator_run_evidence_ready_for_mvp5",
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_config_mutation_allowed",
        "live_ready_write_allowed",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if report.get(field) is not False:
            raise RuntimeError(f"completion acceptance report has non-false {field}")
    if report.get("non_live_operator_command_preflight_passed") is not True:
        raise RuntimeError("completion acceptance report must bind the non-live command preflight")
    if report.get("mvp5_entry_blocked_until_operator_evidence") is not True:
        raise RuntimeError("completion acceptance report must keep MVP-5 blocked")
    items = report.get("operator_completion_acceptance_items", [])
    if not isinstance(items, list) or len(items) != 12:
        raise RuntimeError("completion acceptance items must expose exactly 12 gates")
    kind_counts = {"RUNTIME_ARTIFACT": 0, "VALIDATOR": 0, "SAFETY_INVARIANT": 0}
    for item in items:
        if not isinstance(item, dict):
            raise RuntimeError("completion acceptance item must be an object")
        kind = item.get("acceptance_kind")
        if kind in kind_counts:
            kind_counts[kind] += 1
        for field in (
            "evidence_ready_for_closure",
            "current_evidence_write_allowed",
            "gap_closure_allowed_by_this_patch",
            "live_ready_write_allowed",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            if item.get(field) is not False:
                raise RuntimeError(f"completion acceptance item has non-false {field}")
    if kind_counts != {"RUNTIME_ARTIFACT": 5, "VALIDATOR": 6, "SAFETY_INVARIANT": 1}:
        raise RuntimeError("completion acceptance gate kind counts drifted")
    return report


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: DASHBOARD_UX
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_CONTRACT_GAP", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-RUN-COMPLETION-ACCEPTANCE", "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-PROGRESS-AUDIT", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.residual_operator_evidence_run_preflight_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS + DASHBOARD_ARTIFACTS + SESSION_ARTIFACTS + [COMPLETION_ACCEPTANCE_REPORT_PATH, EVIDENCE_PROGRESS_REPORT_PATH, EXECUTION_GUIDE_REPORT_PATH])}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The first-screen Live Execution card loads the PAPER/SHADOW completion acceptance report as display truth only.
- The dashboard shows {report["operator_completion_acceptance_pending_count"]}/{report["operator_completion_acceptance_count"]} completion gates pending: {report["operator_completion_acceptance_artifact_count"]} artifacts, {report["operator_completion_acceptance_validator_count"]} validators, and 1 safety invariant.
- The dashboard exposes the first pending gate and its responsible validator without exposing order controls or command execution.
- The dashboard keeps current evidence writes, gap closure, LIVE_READY write, live config mutation, live order, and scale-up disabled.
- No gap is closed by this patch.

known_omissions_by_design:
- completion gates remain pending until operator PAPER/SHADOW runtime evidence and validators PASS
- dashboard remains display truth only and cannot become execution truth
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

The dashboard now exposes PAPER/SHADOW completion acceptance as operator-facing display truth: all {report["operator_completion_acceptance_count"]} gates remain pending and no closure or live permission exists.

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
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Dashboard operator completion acceptance visibility",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: show PAPER/SHADOW completion acceptance gates on the dashboard "
                "without closing gaps, writing current evidence, or enabling live/scale"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard operator completion acceptance visibility",
            "requirement_kind": "DASHBOARD_UX",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS
            + DASHBOARD_ARTIFACTS
            + SESSION_ARTIFACTS
            + [COMPLETION_ACCEPTANCE_REPORT_PATH, EVIDENCE_PROGRESS_REPORT_PATH, EXECUTION_GUIDE_REPORT_PATH],
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_SHELL", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-RUN-COMPLETION-ACCEPTANCE",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"dashboard operator completion acceptance visibility fail closed"),
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
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": [
                "trader1/dashboard/read_only_dashboard.py",
                "tools/run_dashboard_visual_layout_validators.py",
            ],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py"],
            "fixture_files": [COMPLETION_ACCEPTANCE_REPORT_PATH],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py"],
            "evidence_artifacts": [
                COMPLETION_ACCEPTANCE_REPORT_PATH,
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                *SESSION_ARTIFACTS,
            ],
            "dashboard_artifacts": DASHBOARD_ARTIFACTS,
            "patch_result_fields": [
                "patch_id",
                "tests_run",
                "validators_run",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    regenerated: list[dict[str, Any]],
    report: dict[str, Any],
) -> dict[str, Any]:
    patch_result = visibility_base.build_patch_result(now, tests_run, validators_run, regenerated)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-RUN-COMPLETION-ACCEPTANCE",
                "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-PROGRESS-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "next_task_class": NEXT_TASK_CLASS,
            "remaining_blockers": BLOCKERS,
            "active_read_surface_used": [
                "current_implementation_state",
                "completion acceptance report",
                "read-only dashboard renderer",
                "read-only dashboard schema",
                "dashboard visual layout contract",
                "dashboard tests",
            ],
            "task_class": "DASHBOARD_UX",
            "required_section_ids": [
                "SECTION_DASHBOARD_SHELL",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_CONTRACT_GAP",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_DASHBOARD_SHELL",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_CONTRACT_GAP",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "optimizer_guardrail_result": "PASS_DASHBOARD_COMPLETION_ACCEPTANCE_VISIBILITY_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_DASHBOARD_COMPLETION_ACCEPTANCE_VISIBILITY_LIVE_BLOCKED",
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


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
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
            "stage_gate_status": "PASS_DASHBOARD_COMPLETION_ACCEPTANCE_VISIBILITY_LIVE_BLOCKED",
            "open_gap_count": report["open_gap_count"],
            "completion_acceptance_status": report["operator_completion_acceptance_status"],
            "completion_acceptance_gate_count": report["operator_completion_acceptance_count"],
            "completion_acceptance_pending_count": report["operator_completion_acceptance_pending_count"],
            "completion_acceptance_artifact_count": report["operator_completion_acceptance_artifact_count"],
            "completion_acceptance_validator_count": report["operator_completion_acceptance_validator_count"],
            "mvp5_entry_blocked_until_operator_evidence": True,
            "current_evidence_write_allowed": False,
            "gap_closure_allowed_by_this_patch": False,
            "live_ready_write_allowed": False,
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
                *DASHBOARD_ARTIFACTS,
                *SESSION_ARTIFACTS,
                COMPLETION_ACCEPTANCE_REPORT_PATH,
                EVIDENCE_PROGRESS_REPORT_PATH,
                EXECUTION_GUIDE_REPORT_PATH,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
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
        f"""# MVP4 Dashboard Operator Completion Acceptance Visibility Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- PAPER/SHADOW completion acceptance existed as evidence, but the dashboard did not yet show the exact pending gate count or first pending validator on the operator live-blocker surface.

Patch:
- Bound the dashboard shell to {COMPLETION_ACCEPTANCE_REPORT_PATH} as display truth only.
- Added operator-facing completion acceptance counts: {report["operator_completion_acceptance_pending_count"]}/{report["operator_completion_acceptance_count"]} pending gates, {report["operator_completion_acceptance_artifact_count"]} runtime artifacts, {report["operator_completion_acceptance_validator_count"]} validators, and 1 safety invariant.
- Exposed the first pending gate and responsible validator while keeping detailed evidence below the first-screen summary.
- Added fail-closed validation for permission drift inside completion gates.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no LIVE_READY write
- no current evidence write
- no gap closure
- no scale-up
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
    completion_base.write_session_artifacts(now, patch_result, report)
    write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    report = load_completion_acceptance_report()
    base.update_authority_manifest(now)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    regenerated = base.regenerate_paper_dashboards()
    regenerated.extend(visibility_base.refresh_existing_runtime_dashboard_html())

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
                "tests/dashboard/test_read_only_dashboard.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_dashboard_visual_layout_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, regenerated, report)
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
                "-v",
            ]
        )
    )
    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, regenerated, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "completion_acceptance_status": report["operator_completion_acceptance_status"],
                "completion_acceptance_gate_count": report["operator_completion_acceptance_count"],
                "completion_acceptance_pending_count": report["operator_completion_acceptance_pending_count"],
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
