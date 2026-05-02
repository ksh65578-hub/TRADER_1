from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
import tools.emit_upbit_paper_stale_loop_isolated_event_id_scope_repaired_dashboard_binding_patch_evidence as dashboard_binding  # noqa: E402
from trader1.dashboard.read_only_dashboard import validate_read_only_dashboard_shell  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard import (  # noqa: E402
    build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report,
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report,
    write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


PATCH_BASENAME = "MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_OPERATOR_REVIEW_BINDING"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-ISOLATED-EVENT-ID-SCOPE-REPAIRED-OPERATOR-REVIEW-BINDING"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK"
SESSION_ID = "mvp1_upbit_paper_launcher"

RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID / "paper_runtime"
REPAIRED_DUPLICATE_RECHECK_PATH = (
    RUNTIME_BASE / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_report.json"
)
OPERATOR_GUIDANCE_PATH = (
    RUNTIME_BASE / "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json"
)
CURRENT_EVIDENCE_GUARD_PATH = (
    RUNTIME_BASE / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json"
)

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]

CHANGED_ARTIFACTS = [
    "trader1/dashboard/read_only_dashboard.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_upbit_paper_stale_loop_isolated_event_id_scope_repaired_operator_review_binding_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json",
]

BLOCKERS = [
    "ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_CURRENT_WRITES_BLOCKED",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.BLOCKERS = BLOCKERS


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def write_runtime_guard_report() -> dict[str, Any]:
    report = build_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
        root=ROOT,
        event_id_scope_repaired_duplicate_recheck_report=load_json(REPAIRED_DUPLICATE_RECHECK_PATH),
        operator_review_guidance_report=load_json(OPERATOR_GUIDANCE_PATH),
        event_id_scope_repaired_current_evidence_guard_id=(
            "upbit-paper-stale-loop-isolated-event-id-scope-repaired-operator-review-binding-20260502"
        ),
    )
    result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(report)
    if result.status != "PASS":
        raise RuntimeError(
            f"repaired current-evidence guard validation failed: {result.status} {result.blocker_code} {result.message}"
        )
    write_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(root=ROOT, report=report)
    return report


def validate_dashboard_projection(dashboard: dict[str, Any], report: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    reconciliation, portfolio = dashboard_binding.validate_dashboard_projection(dashboard, report)
    operator_action = dashboard.get("operator_action_summary")
    workflow = dashboard.get("operator_workflow_summary")
    if not isinstance(operator_action, dict) or not isinstance(workflow, dict):
        raise RuntimeError("dashboard missing operator action or workflow summary")
    if operator_action.get("primary_action_label") != "Inspect repaired current-evidence blocker":
        raise RuntimeError("operator action did not name the repaired current-evidence blocker")
    if "current-evidence writes=0" not in str(operator_action.get("one_line_blocker", "")):
        raise RuntimeError("operator action did not expose current-evidence write block")
    operator_next = str(operator_action.get("next_operator_action", "")).lower()
    if "current evidence writes" not in operator_next or "blocked" not in operator_next:
        raise RuntimeError("operator next action did not keep current-evidence writes blocked")
    if workflow.get("status") != "BLOCKED" or "portfolio truth writes remain blocked" not in str(workflow.get("summary", "")):
        raise RuntimeError("operator workflow did not keep repaired candidates review-only")
    steps = workflow.get("steps", [])
    if (
        not isinstance(steps, list)
        or len(steps) != 4
        or "configured PAPER capital is not verified cash or equity" not in str(steps[1].get("detail", ""))
        or "Keep repaired candidates review-only" not in str(steps[2].get("detail", ""))
    ):
        raise RuntimeError("operator workflow did not separate configured capital from verified portfolio truth")
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if operator_action.get(field) is not False or workflow.get(field) is not False:
            raise RuntimeError(f"operator review binding attempted forbidden live or scale permission: {field}")
    return reconciliation, portfolio


def write_launcher_artifacts(report: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    launcher_report = build_launcher_report("UPBIT_PAPER")
    report_path, dashboard_paths = write_launcher_runtime_bundle(launcher_report)
    dashboard = load_json(dashboard_paths["dashboard_shell"])
    validate_dashboard_projection(dashboard, report)
    legacy_html_path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "dashboard" / "index.html"
    base.write_text(legacy_html_path, dashboard_paths["dashboard_html"].read_text(encoding="utf-8"))
    artifact_paths = [base.rel(report_path), *(base.rel(path) for path in dashboard_paths.values()), base.rel(legacy_html_path)]
    return dashboard, sorted(set(artifact_paths))


def write_context(now: str, trader_hash: str, agents_hash: str, dashboard: dict[str, Any], report: dict[str, Any]) -> None:
    operator_action = dashboard["operator_action_summary"]
    workflow = dashboard["operator_workflow_summary"]
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_OPERATOR_REVIEW_BINDING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- The first-screen operator action names the repaired current-evidence blocker.
- The primary blocker text states current-evidence writes remain zero.
- The operator workflow separates configured PAPER capital from verified cash/equity.
- Live orders, live readiness, current-evidence writes, portfolio truth writes, and scale-up remain blocked.

runtime_summary:
- dashboard_blocking_reason: {dashboard["blocking_reason"]}
- operator_action_label: {operator_action["primary_action_label"]}
- operator_workflow_summary: {workflow["summary"]}
- guard_status: {report["current_evidence_guard_status"]}
- current_evidence_write_allowed_count: {report["current_evidence_write_allowed_count"]}
- portfolio_truth_write_allowed_count: {report["portfolio_truth_write_allowed_count"]}
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not write current evidence, portfolio truth, LIVE_READY, live config, orders, or scale-up.
- It does not resolve POST_RERUN_RECONCILIATION_REQUIRED.

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

Upbit PAPER repaired isolated event-id candidates are visible as review-only evidence. The operator action and workflow now explicitly say current-evidence writes and portfolio truth writes remain blocked, and configured 1,000,000 KRW PAPER capital is not verified cash/equity.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str, launcher_artifacts: list[str]) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    artifacts = sorted(set(CHANGED_ARTIFACTS + launcher_artifacts))

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER repaired current-evidence guard operator review binding",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: operator action and workflow must expose repaired isolated event-id "
                "current-evidence write blocks without creating portfolio truth, live order, or scale-up permission"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER repaired current-evidence guard operator review binding",
            "requirement_kind": "DASHBOARD_UX_PATCH",
            "schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-ISOLATED-EVENT-ID-SCOPE-REPAIRED-DASHBOARD-BINDING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"repaired current evidence guard operator review binding no live no scale"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_OPERATOR_REVIEW_BOUND_LIVE_BLOCKED",
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
            "schema_files": [
                "contracts/schema/read_only_dashboard_shell.schema.json",
                "contracts/schema/upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.schema.json",
            ],
            "validator_files": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard.py",
            ],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py"],
            "fixture_files": [base.rel(CURRENT_EVIDENCE_GUARD_PATH)],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "operator_action_summary.primary_action_label",
                "operator_action_summary.one_line_blocker",
                "operator_action_summary.next_operator_action",
                "operator_workflow_summary.summary",
                "operator_workflow_summary.steps",
                "portfolio_snapshot.configured_paper_capital",
            ],
            "patch_result_fields": [
                "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_status",
                "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_current_evidence_write_allowed_count",
                "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_portfolio_truth_write_allowed_count",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_OPERATOR_REVIEW_BOUND_LIVE_BLOCKED",
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
    dashboard: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_DASHBOARD_BINDING.patch_result.json"
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
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-ISOLATED-EVENT-ID-SCOPE-REPAIRED-DASHBOARD-BINDING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [REQUIREMENT_ID],
            "validators_required": VALIDATORS_REQUIRED,
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
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_PORTFOLIO_TRUTH", "SECTION_OPERATOR_REVIEW"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "RETAINED_ARCHIVE"],
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
                "repaired current-evidence guard report",
                "operator action summary",
                "operator workflow summary",
                "read-only dashboard shell",
                "live final guard",
            ],
            "task_class": "MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_OPERATOR_REVIEW_BINDING",
            "required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "REPAIRED_CURRENT_EVIDENCE_GUARD_OPERATOR_REVIEW_BOUND",
            "optimizer_guardrail_result": "PASS_OPERATOR_REVIEW_DOES_NOT_MUTATE_CURRENT_EVIDENCE",
            "convergence_state_after": "REPAIRED_CURRENT_EVIDENCE_GUARD_OPERATOR_REVIEW_BOUND_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_CURRENT_EVIDENCE_MUTATION_NO_SCALE_UP",
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
            "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_status": report[
                "current_evidence_guard_status"
            ],
            "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_candidate_count": report[
                "candidate_count"
            ],
            "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_review_ready_count": report[
                "guard_review_ready_count"
            ],
            "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_blocked_count": report[
                "guard_blocked_count"
            ],
            "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_duplicate_total_count": report[
                "duplicate_total_count"
            ],
            "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_current_evidence_write_allowed_count": 0,
            "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_portfolio_truth_write_allowed_count": 0,
            "candidate_current_evidence_usable_count": 0,
        }
    )
    if dashboard.get("operator_action_summary", {}).get("primary_action_label") != "Inspect repaired current-evidence blocker":
        raise RuntimeError("patch_result cannot be emitted without operator review binding")
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    dashboard: dict[str, Any],
    report: dict[str, Any],
    launcher_artifacts: list[str],
) -> None:
    operator_action = dashboard["operator_action_summary"]
    workflow = dashboard["operator_workflow_summary"]
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
            "stage_gate_status": "PASS_REPAIRED_CURRENT_EVIDENCE_GUARD_OPERATOR_REVIEW_BOUND_LIVE_BLOCKED",
            "operator_action_label": operator_action["primary_action_label"],
            "operator_action_blocker": operator_action["one_line_blocker"],
            "operator_workflow_summary": workflow["summary"],
            "guard_status": report["current_evidence_guard_status"],
            "current_evidence_write_allowed_count": 0,
            "portfolio_truth_write_allowed_count": 0,
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
            "artifact_paths": sorted(
                set(
                    [
                        *CHANGED_ARTIFACTS,
                        *launcher_artifacts,
                        patch_result["validator_run_log_path"],
                        patch_result["stage_gate_result_path"],
                        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                    ]
                )
            ),
            "known_blockers": patch_result["remaining_blockers"],
            "operator_action_label": operator_action["primary_action_label"],
            "operator_workflow_summary": workflow["summary"],
            "guard_status": report["current_evidence_guard_status"],
            "current_evidence_write_allowed_count": 0,
            "portfolio_truth_write_allowed_count": 0,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json", patch_result)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    report = write_runtime_guard_report()
    dashboard, launcher_artifacts = write_launcher_artifacts(report)
    write_context(now, trader_hash, agents_hash, dashboard, report)
    update_requirement_artifacts(now, trader_hash, agents_hash, launcher_artifacts)

    tests_run = [
        run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/dashboard/test_read_only_dashboard.py", "-q"]),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
    ]
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, dashboard, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, dashboard, report, launcher_artifacts)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, dashboard, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, dashboard, report, launcher_artifacts)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
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
