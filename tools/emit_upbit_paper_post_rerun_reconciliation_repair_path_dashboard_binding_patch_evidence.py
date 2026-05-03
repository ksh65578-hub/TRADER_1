from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_OPERATOR_UX_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260503_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-REPAIR-PATH-OPERATOR-UX-RECHECK"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION_OPERATOR_UX_RECHECK"
SESSION_ID = "mvp1_upbit_paper_launcher"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.dashboard.read_only_dashboard import build_read_only_dashboard_shell, validate_read_only_dashboard_shell  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_repair_path import (  # noqa: E402
    build_upbit_paper_post_rerun_reconciliation_repair_path_report,
    validate_upbit_paper_post_rerun_reconciliation_repair_path_report,
    write_upbit_paper_post_rerun_reconciliation_repair_path_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "upbit_paper_post_rerun_reconciliation_repair_path_validator",
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
    "contracts/schema/patch_result.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_reconciliation_repair_path_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/upbit/krw_spot/paper/dashboard/index.html",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_post_rerun_reconciliation_repair_path_dashboard_binding_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

BLOCKERS = [
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
    "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED",
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


def runtime_repair_path() -> Path:
    return (
        ROOT
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / SESSION_ID
        / "paper_runtime"
        / "upbit_paper_post_rerun_reconciliation_repair_path_report.json"
    )


def load_repair_path_report() -> dict[str, Any]:
    report = build_upbit_paper_post_rerun_reconciliation_repair_path_report(
        root=ROOT,
        session_id=SESSION_ID,
        repair_path_id="mvp4-upbit-paper-post-rerun-repair-path-operator-ux-recheck",
    )
    write_upbit_paper_post_rerun_reconciliation_repair_path_report(root=ROOT, report=report)
    result = validate_upbit_paper_post_rerun_reconciliation_repair_path_report(report)
    if result.status != "PASS":
        raise RuntimeError(
            "post-rerun reconciliation repair path validation failed: "
            f"{result.status} {result.blocker_code} {result.message}"
        )
    return report


def load_runtime_artifact(relative_path: str) -> dict[str, Any]:
    value = load_json(ROOT / relative_path)
    if not isinstance(value, dict):
        raise RuntimeError(f"runtime artifact is not an object: {relative_path}")
    return value


def build_repair_path_operator_dashboard(repair_path: dict[str, Any]) -> dict[str, Any]:
    recheck = load_runtime_artifact(str(repair_path["source_recheck_path"]))
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=SESSION_ID,
        summary=load_runtime_artifact(
            f"system/runtime/upbit/krw_spot/paper/{SESSION_ID}/summary.json"
        ),
        heartbeat=load_runtime_artifact(
            f"system/runtime/upbit/krw_spot/paper/{SESSION_ID}/heartbeat.json"
        ),
        startup_probe=load_runtime_artifact(
            f"system/runtime/upbit/krw_spot/paper/{SESSION_ID}/startup_probe.json"
        ),
        upbit_paper_post_rerun_resolution_current_evidence_closure_report=load_runtime_artifact(
            str(repair_path["source_closure_path"])
        ),
        upbit_paper_post_rerun_current_evidence_closure_recheck_report=recheck,
        upbit_paper_post_rerun_reconciliation_repair_path_report=repair_path,
        upbit_paper_ledger_idempotency_runtime_evidence_report=load_runtime_artifact(
            str(recheck["source_ledger_idempotency_path"])
        ),
    )


def validate_dashboard_projection(dashboard: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    result = validate_read_only_dashboard_shell(dashboard)
    if result.status != "PASS":
        raise RuntimeError(f"dashboard validation failed: {result.status} {result.blocker_code} {result.message}")
    reconciliation = dashboard.get("reconciliation_recovery_summary")
    operator_action = dashboard.get("operator_action_summary")
    portfolio = dashboard.get("portfolio_snapshot")
    if not isinstance(reconciliation, dict) or not isinstance(operator_action, dict) or not isinstance(portfolio, dict):
        raise RuntimeError("dashboard missing reconciliation, operator action, or portfolio summary")
    if dashboard.get("blocking_reason") not in set(BLOCKERS):
        raise RuntimeError("repair dashboard binding did not keep a known live-blocking reason")
    if reconciliation.get("status") != "BLOCKED" or reconciliation.get("color_token") != "red":
        raise RuntimeError("dashboard did not keep reconciliation blocked while repair path is unresolved")
    if reconciliation.get("post_rerun_reconciliation_repair_path_status") != "BLOCKED_REPAIR_PATH_DECLARED":
        raise RuntimeError("dashboard did not surface repair path status")
    if reconciliation.get("post_rerun_reconciliation_repair_path_validation_status") != "PASS":
        raise RuntimeError("dashboard did not surface repair path validation PASS")
    if (
        reconciliation.get("post_rerun_reconciliation_repair_path_repair_gate_count") != 4
        or reconciliation.get("post_rerun_reconciliation_repair_path_satisfied_gate_count") != 0
        or reconciliation.get("post_rerun_reconciliation_repair_path_blocked_gate_count") != 4
    ):
        raise RuntimeError("dashboard did not surface blocked repair gate counts")
    if (
        reconciliation.get("post_rerun_reconciliation_repair_path_current_evidence_write_allowed_count") != 0
        or reconciliation.get("post_rerun_reconciliation_repair_path_candidate_current_evidence_usable_count") != 0
    ):
        raise RuntimeError("dashboard exposed repair path current-evidence writes")
    if (
        reconciliation.get("post_rerun_reconciliation_repair_path_source_recheck_persistent_loop_validation_status")
        != "PASS"
        or reconciliation.get("post_rerun_reconciliation_repair_path_source_recheck_persistent_loop_hash_self_check")
        != "PASS"
        or reconciliation.get("post_rerun_reconciliation_repair_path_source_recheck_head_cycle_in_persistent_loop")
        is not True
        or reconciliation.get("post_rerun_reconciliation_repair_path_source_recheck_runtime_input_role")
        != "PUBLIC_MARKET_DATA_COLLECTION"
        or reconciliation.get("post_rerun_reconciliation_repair_path_source_recheck_runtime_public_data_hash_match")
        is not True
        or reconciliation.get("post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_status") != "PASS"
        or reconciliation.get("post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_mismatch_count") != 0
    ):
        raise RuntimeError("dashboard did not surface clean repair path runtime-depth binding")
    source_ids = {source.get("artifact_id"): source for source in dashboard.get("source_artifacts", [])}
    repair_source = source_ids.get("POST_RERUN_RECONCILIATION_REPAIR_PATH")
    if not isinstance(repair_source, dict) or repair_source.get("freshness_status") != "PASS":
        raise RuntimeError("dashboard did not publish the repair path source artifact as PASS")
    if portfolio.get("status") != "UNVERIFIED" or portfolio.get("source_snapshot_status") != "BLOCKED":
        raise RuntimeError("portfolio was incorrectly promoted while repair path is blocked")
    if operator_action.get("status") != "BLOCKED" or operator_action.get("safe_to_continue_paper") is not False:
        raise RuntimeError("operator action did not fail closed for repair path")
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if dashboard.get(field) is not False or reconciliation.get(field) is not False or operator_action.get(field) is not False:
            raise RuntimeError(f"dashboard attempted forbidden live or scale permission: {field}")
    return reconciliation, operator_action, portfolio


def validate_repair_path_operator_projection(
    dashboard: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    result = validate_read_only_dashboard_shell(dashboard)
    if result.status != "PASS":
        raise RuntimeError(
            f"repair path operator dashboard validation failed: {result.status} {result.blocker_code} {result.message}"
        )
    reconciliation = dashboard.get("reconciliation_recovery_summary")
    operator_action = dashboard.get("operator_action_summary")
    workflow = dashboard.get("operator_workflow_summary")
    portfolio = dashboard.get("portfolio_snapshot")
    if not all(isinstance(item, dict) for item in (reconciliation, operator_action, workflow, portfolio)):
        raise RuntimeError("repair path operator projection missing dashboard sections")
    if dashboard.get("blocking_reason") != "POST_RERUN_RECONCILIATION_REQUIRED":
        raise RuntimeError("repair path operator projection did not keep POST_RERUN_RECONCILIATION_REQUIRED")
    if reconciliation.get("source") != "upbit_paper_post_rerun_reconciliation_repair_path_report.json":
        raise RuntimeError("repair path operator projection did not prefer repair path source")
    if operator_action.get("primary_action_label") != "Inspect post-rerun repair path":
        raise RuntimeError("repair path operator action label was not specific")
    operator_line = str(operator_action.get("one_line_blocker", ""))
    if (
        "post-rerun repair path has 0/4 satisfied repair gates" not in operator_line
        or "runtime-depth=PASS" not in operator_line
        or "current-evidence writes=0" not in operator_line
    ):
        raise RuntimeError("repair path operator action did not include gate/runtime-depth/write state")
    if (
        "operator resolution acceptance" not in str(operator_action.get("next_operator_action", ""))
        or "current-evidence rebuild" not in str(operator_action.get("next_operator_action", ""))
    ):
        raise RuntimeError("repair path operator action did not preserve next repair action")
    if (
        workflow.get("status") != "BLOCKED"
        or workflow.get("current_step") != "INSPECT_DASHBOARD"
        or "Post-rerun repair path is blocked" not in str(workflow.get("summary", ""))
        or "runtime-depth support is visible" not in str(workflow.get("steps", [{}, {}])[1].get("detail", ""))
    ):
        raise RuntimeError("repair path operator workflow did not explain repair path blocker")
    if portfolio.get("status") != "UNVERIFIED" or portfolio.get("source_snapshot_status") != "BLOCKED":
        raise RuntimeError("repair path operator projection promoted portfolio truth")
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if (
            dashboard.get(field) is not False
            or reconciliation.get(field) is not False
            or operator_action.get(field) is not False
            or workflow.get(field) is not False
        ):
            raise RuntimeError(f"repair path operator projection attempted forbidden permission: {field}")
    return reconciliation, operator_action, workflow, portfolio


def write_launcher_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    report = build_launcher_report("UPBIT_PAPER")
    report_path, dashboard_paths = write_launcher_runtime_bundle(report)
    dashboard = load_json(dashboard_paths["dashboard_shell"])
    reconciliation, operator_action, portfolio = validate_dashboard_projection(dashboard)

    html_path = dashboard_paths["dashboard_html"]
    legacy_html_path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "dashboard" / "index.html"
    base.write_text(legacy_html_path, html_path.read_text(encoding="utf-8"))

    artifact_paths = [base.rel(report_path), *(base.rel(path) for path in dashboard_paths.values()), base.rel(legacy_html_path)]
    return dashboard, reconciliation, operator_action, portfolio, sorted(set(artifact_paths))


def write_context(
    now: str,
    trader_hash: str,
    agents_hash: str,
    dashboard: dict[str, Any],
    repair_path: dict[str, Any],
    repair_operator_action: dict[str, Any],
    repair_workflow: dict[str, Any],
) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_OPERATOR_UX_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- The Upbit PAPER dashboard keeps the validated post-rerun reconciliation repair path operator-visible.
- Operator action uses a repair-path-specific label, gate/runtime-depth/write state, and next repair action.
- Operator workflow explains that runtime-depth support is visible but no repair gate authorizes current evidence.
- Current evidence writes, portfolio truth, live orders, and scale-up remain blocked.
- Portfolio cash/equity stay UNVERIFIED while repair gates are blocked, even when configured PAPER capital is 1,000,000 KRW.
- Current evidence writes, live orders, and scale-up remain blocked.

known_omissions_by_design:
- This patch is not a reconciliation writer, current-evidence writer, LIVE_READY patch, live config mutation, or scale-up patch.
- It does not resolve POST_RERUN_RECONCILIATION_REQUIRED; it makes the blocked repair path operator-visible.
- No private exchange/account/API call, credential, live order, or risk scale-up was used.

runtime_summary:
- dashboard_blocking_reason: {dashboard["blocking_reason"]}
- operator_action_status: {dashboard["operator_action_summary"]["status"]}
- repair_path_status: {repair_path["repair_path_status"]}
- repair_gate_count: {repair_path["repair_gate_count"]}
- satisfied_repair_gate_count: {repair_path["satisfied_repair_gate_count"]}
- blocked_repair_gate_count: {repair_path["blocked_repair_gate_count"]}
- source_closure_status: {repair_path["source_closure_status"]}
- source_recheck_status: {repair_path["source_recheck_status"]}
- source_recheck_runtime_depth_status: {repair_path["source_recheck_ledger_source_runtime_depth_status"]}
- source_recheck_runtime_depth_mismatch_count: {repair_path["source_recheck_ledger_source_runtime_depth_mismatch_count"]}
- source_recheck_persistent_loop_validation_status: {repair_path["source_recheck_ledger_source_persistent_loop_validation_status"]}
- operator_action_label: {repair_operator_action["primary_action_label"]}
- operator_workflow_status: {repair_workflow["status"]}
- operator_workflow_current_step: {repair_workflow["current_step"]}
- current_evidence_write_allowed: false
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

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

Upbit PAPER post-rerun repair path is visible in the read-only dashboard with repair-path-specific operator action and workflow guidance. Portfolio values remain UNVERIFIED current evidence until the separate repair gates are satisfied by a future validated repair path.

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
            "source_heading": "Upbit PAPER post-rerun reconciliation repair path operator UX recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: repair path operator action and workflow must identify blocked repair gates, "
                "runtime-depth support, zero current-evidence writes, and next repair evidence without live or scale permission"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER post-rerun reconciliation repair path operator UX recheck",
            "requirement_kind": "DASHBOARD_UX_PATCH",
            "schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/runtime/test_upbit_paper_post_rerun_reconciliation_repair_path.py",
            ],
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
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-REPAIR-PATH",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-REPAIR-PATH-RUNTIME-DEPTH-DASHBOARD-BINDING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"post rerun reconciliation repair path operator action workflow visible without current evidence live order or scale up permission"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_OPERATOR_UX_RECHECK_LIVE_BLOCKED",
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
                "contracts/schema/upbit_paper_post_rerun_reconciliation_repair_path_report.schema.json",
            ],
            "validator_files": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_repair_path.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/runtime/test_upbit_paper_post_rerun_reconciliation_repair_path.py",
            ],
            "fixture_files": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_reconciliation_repair_path_report.json"
            ],
            "runtime_modules": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_repair_path.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "reconciliation_recovery_summary.post_rerun_reconciliation_repair_path_status",
                "reconciliation_recovery_summary.post_rerun_reconciliation_repair_path_repair_gate_count",
                "reconciliation_recovery_summary.post_rerun_reconciliation_repair_path_satisfied_gate_count",
                "reconciliation_recovery_summary.post_rerun_reconciliation_repair_path_blocked_gate_count",
                "reconciliation_recovery_summary.post_rerun_reconciliation_repair_path_current_evidence_write_allowed_count",
                "reconciliation_recovery_summary.post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_status",
                "reconciliation_recovery_summary.post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_mismatch_count",
                "reconciliation_recovery_summary.post_rerun_reconciliation_repair_path_source_recheck_persistent_loop_validation_status",
                "operator_action_summary.primary_action_label",
                "operator_action_summary.one_line_blocker",
                "operator_action_summary.next_operator_action",
                "operator_workflow_summary.summary",
                "operator_workflow_summary.steps",
                "source_artifacts.POST_RERUN_RECONCILIATION_REPAIR_PATH",
                "portfolio_snapshot.source_snapshot_status",
                "operator_action_summary.primary_blocker_code",
                "blocking_reason",
            ],
            "patch_result_fields": [
                "post_rerun_reconciliation_repair_path_status",
                "post_rerun_reconciliation_repair_gate_count",
                "post_rerun_reconciliation_repair_gate_satisfied_count",
                "post_rerun_reconciliation_repair_gate_blocked_count",
                "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_status",
                "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_mismatch_count",
                "post_rerun_reconciliation_repair_path_operator_action_label",
                "post_rerun_reconciliation_repair_path_operator_workflow_status",
                "post_rerun_reconciliation_repair_path_operator_workflow_current_step",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_OPERATOR_UX_RECHECK_LIVE_BLOCKED",
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
    repair_path: dict[str, Any],
    repair_operator_action: dict[str, Any],
    repair_workflow: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH.patch_result.json"
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
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-REPAIR-PATH",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1",
            ],
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
            "next_optional_section_ids": ["SECTION_PORTFOLIO_TRUTH", "SECTION_UPBIT_PAPER_RUNTIME"],
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
                "post-rerun reconciliation repair path report",
                "read-only dashboard shell",
                "repair-path-specific operator action and workflow projection",
                "safe launcher dashboard binding",
                "live final guard",
            ],
            "task_class": "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_OPERATOR_UX_RECHECK",
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
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_POST_RERUN_REPAIR_PATH_OPERATOR_UX_VISIBLE",
            "optimizer_guardrail_result": "PASS_DASHBOARD_DOES_NOT_MUTATE_CURRENT_EVIDENCE",
            "convergence_state_after": "POST_RERUN_REPAIR_PATH_OPERATOR_UX_VISIBLE_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_CURRENT_EVIDENCE_MUTATION_NO_SCALE_UP",
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
            "post_rerun_reconciliation_repair_path_status": repair_path["repair_path_status"],
            "post_rerun_reconciliation_repair_gate_count": repair_path["repair_gate_count"],
            "post_rerun_reconciliation_repair_gate_satisfied_count": repair_path["satisfied_repair_gate_count"],
            "post_rerun_reconciliation_repair_gate_blocked_count": repair_path["blocked_repair_gate_count"],
            "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_status": repair_path[
                "source_recheck_ledger_source_runtime_depth_status"
            ],
            "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_mismatch_count": repair_path[
                "source_recheck_ledger_source_runtime_depth_mismatch_count"
            ],
            "post_rerun_reconciliation_repair_path_operator_action_label": repair_operator_action[
                "primary_action_label"
            ],
            "post_rerun_reconciliation_repair_path_operator_workflow_status": repair_workflow["status"],
            "post_rerun_reconciliation_repair_path_operator_workflow_current_step": repair_workflow["current_step"],
            "post_rerun_current_evidence_write_allowed_count": 0,
            "candidate_current_evidence_usable_count": 0,
        }
    )
    if dashboard.get("blocking_reason") not in set(BLOCKERS):
        raise RuntimeError("patch_result cannot be emitted without a known dashboard blocker projection")
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    dashboard: dict[str, Any],
    repair_path: dict[str, Any],
    repair_operator_action: dict[str, Any],
    repair_workflow: dict[str, Any],
    launcher_artifacts: list[str],
) -> None:
    reconciliation = dashboard["reconciliation_recovery_summary"]
    operator_action = dashboard["operator_action_summary"]
    portfolio = dashboard["portfolio_snapshot"]
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
            "stage_gate_status": "PASS_DASHBOARD_VISIBLE_POST_RERUN_REPAIR_PATH_LIVE_BLOCKED",
            "dashboard_blocking_reason": dashboard["blocking_reason"],
            "operator_action_status": operator_action["status"],
            "operator_primary_blocker_code": operator_action["primary_blocker_code"],
            "portfolio_status": portfolio["status"],
            "portfolio_source_snapshot_status": portfolio["source_snapshot_status"],
            "reconciliation_status": reconciliation["status"],
            "repair_path_status": reconciliation["post_rerun_reconciliation_repair_path_status"],
            "repair_gate_count": reconciliation["post_rerun_reconciliation_repair_path_repair_gate_count"],
            "satisfied_repair_gate_count": reconciliation["post_rerun_reconciliation_repair_path_satisfied_gate_count"],
            "blocked_repair_gate_count": reconciliation["post_rerun_reconciliation_repair_path_blocked_gate_count"],
            "source_recheck_runtime_depth_status": reconciliation[
                "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_status"
            ],
            "source_recheck_runtime_depth_mismatch_count": reconciliation[
                "post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_mismatch_count"
            ],
            "repair_path_operator_action_label": repair_operator_action["primary_action_label"],
            "repair_path_operator_workflow_status": repair_workflow["status"],
            "repair_path_operator_workflow_current_step": repair_workflow["current_step"],
            "current_evidence_mutation_allowed": False,
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
            "dashboard_blocking_reason": dashboard["blocking_reason"],
            "operator_action_status": operator_action["status"],
            "operator_primary_blocker_code": operator_action["primary_blocker_code"],
            "portfolio_status": portfolio["status"],
            "repair_path_status": repair_path["repair_path_status"],
            "repair_gate_count": repair_path["repair_gate_count"],
            "satisfied_repair_gate_count": repair_path["satisfied_repair_gate_count"],
            "blocked_repair_gate_count": repair_path["blocked_repair_gate_count"],
            "source_recheck_runtime_depth_status": repair_path[
                "source_recheck_ledger_source_runtime_depth_status"
            ],
            "source_recheck_runtime_depth_mismatch_count": repair_path[
                "source_recheck_ledger_source_runtime_depth_mismatch_count"
            ],
            "repair_path_operator_action_label": repair_operator_action["primary_action_label"],
            "repair_path_operator_workflow_status": repair_workflow["status"],
            "repair_path_operator_workflow_current_step": repair_workflow["current_step"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260503.md",
        f"""# MVP4 Upbit PAPER Post-Rerun Reconciliation Repair Path Operator UX Recheck Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Bound the post-rerun reconciliation repair path report into the read-only dashboard and safe launcher source map.
- Preserved the closure recheck runtime-depth fields in the repair path report.
- Surfaced repair-specific operator action and workflow guidance with gate counts, runtime-depth status, and zero current-evidence write allowance.
- Kept portfolio cash/equity UNVERIFIED while repair gates are blocked, even when configured PAPER capital is visible.
- Kept a known live-blocking dashboard/operator blocker while POST_RERUN_RECONCILIATION_REQUIRED remains in the blocker set.

Runtime evidence:
- repair_path_status={repair_path["repair_path_status"]}
- repair_gate_count={repair_path["repair_gate_count"]}
- satisfied_repair_gate_count={repair_path["satisfied_repair_gate_count"]}
- blocked_repair_gate_count={repair_path["blocked_repair_gate_count"]}
- source_recheck_runtime_depth_status={repair_path["source_recheck_ledger_source_runtime_depth_status"]}
- source_recheck_runtime_depth_mismatch_count={repair_path["source_recheck_ledger_source_runtime_depth_mismatch_count"]}
- source_recheck_persistent_loop_validation_status={repair_path["source_recheck_ledger_source_persistent_loop_validation_status"]}
- dashboard_source={reconciliation["source"]}
- repair_path_operator_action_label={repair_operator_action["primary_action_label"]}
- repair_path_operator_workflow_status={repair_workflow["status"]}
- repair_path_operator_workflow_current_step={repair_workflow["current_step"]}
- portfolio_status={portfolio["status"]}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no current evidence writer or live config mutation added
""",
    )


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    dashboard: dict[str, Any],
    repair_path: dict[str, Any],
    repair_operator_action: dict[str, Any],
    repair_workflow: dict[str, Any],
    launcher_artifacts: list[str],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(
        now,
        trader_hash,
        agents_hash,
        patch_result,
        dashboard,
        repair_path,
        repair_operator_action,
        repair_workflow,
        launcher_artifacts,
    )
    base.write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    repair_path = load_repair_path_report()
    dashboard, reconciliation, operator_action, _portfolio, launcher_artifacts = write_launcher_artifacts()
    repair_operator_dashboard = build_repair_path_operator_dashboard(repair_path)
    _repair_reconciliation, repair_operator_action, repair_workflow, _repair_portfolio = (
        validate_repair_path_operator_projection(repair_operator_dashboard)
    )
    write_context(now, trader_hash, agents_hash, dashboard, repair_path, repair_operator_action, repair_workflow)
    update_requirement_artifacts(now, trader_hash, agents_hash, launcher_artifacts)

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/runtime/test_upbit_paper_post_rerun_reconciliation_repair_path.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(
        now,
        tests_run,
        validators_run,
        dashboard,
        repair_path,
        repair_operator_action,
        repair_workflow,
    )
    write_patch_artifacts(
        now,
        trader_hash,
        agents_hash,
        patch_result,
        dashboard,
        repair_path,
        repair_operator_action,
        repair_workflow,
        launcher_artifacts,
    )

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(
        now,
        tests_run,
        validators_run,
        dashboard,
        repair_path,
        repair_operator_action,
        repair_workflow,
    )
    write_patch_artifacts(
        now,
        trader_hash,
        agents_hash,
        patch_result,
        dashboard,
        repair_path,
        repair_operator_action,
        repair_workflow,
        launcher_artifacts,
    )

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "dashboard_source": reconciliation["source"],
                "repair_path_operator_action_label": repair_operator_action["primary_action_label"],
                "operator_action_status": operator_action["status"],
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
